/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_context.hh"
#include "BKE_wm_runtime.hh"
#include "BLI_listbase.hh"
#include "DNA_windowmanager_types.h"
#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"
#include "WM_api.hh"
#include "WM_types.hh"

#include "view3d_axismeld.hh"
#include "view3d_axismeld_hotbox_internal.hh"
#include "wm_event_system.hh"

#include <memory>
#include <climits>
#include <string_view>

namespace blender {
namespace {
struct ReleaseCapture {
  int trigger, mouse;
  bool trigger_down, mouse_down, tool_session;
  wmWindow *source = nullptr, *receiver = nullptr;
  wmOperator *file_operator = nullptr;
  int file_token = 0;
};
struct ReleaseData {
  std::shared_ptr<ReleaseCapture> capture;
  wmWindow *window;
};

static bool window_is_live(const bContext *C, const wmWindow *window)
{
  const wmWindowManager *wm = CTX_wm_manager(C);
  if (wm && window) {
    for (const wmWindow &candidate : wm->windows) {
      if (&candidate == window) {
        return true;
      }
    }
  }
  return false;
}

static void cleanup(bContext *C, wmOperator *op)
{
  auto *data = static_cast<ReleaseData *>(op->customdata);
  if (!data) {
    return;
  }
  auto &capture = *data->capture;
  wmWindow *other = data->window == capture.source ? capture.receiver : capture.source;
  if (data->window == capture.source) {
    /* Source destruction invalidates the remaining receiver; never retain dead ownership. */
    capture.source = nullptr;
    capture.trigger_down = capture.mouse_down = false;
  }
  else if (data->window == capture.receiver) {
    capture.receiver = nullptr;
  }
  capture.file_operator = nullptr;
  capture.file_token = 0;
  delete data;
  op->customdata = nullptr;
  /* Let the surviving companion retire without waiting for another physical input. */
  if (window_is_live(C, other)) {
    WM_event_add_mousemove(other);
  }
}

static bool fileselect_handoff(wmOperator *owner,
                              wmOperator *receiver,
                              wmOperator *file_operator,
                              wmWindow *receiver_window)
{
  auto *data = static_cast<ReleaseData *>(owner->customdata);
  if (!data || data->capture->receiver ||
      (!data->capture->trigger_down && !data->capture->mouse_down))
  {
    return false;
  }
  const PropertyRNA *token_prop = RNA_struct_find_property(file_operator->ptr,
                                                          "axismeld_release_token");
  const bool token_matches = data->capture->file_token && token_prop &&
      RNA_int_get(file_operator->ptr, "axismeld_release_token") == data->capture->file_token;
  if (!token_matches && data->capture->file_operator != file_operator) {
    return false;
  }
  /* Single handoff only, including after the receiver is cancelled or closed. */
  data->capture->file_operator = nullptr;
  data->capture->file_token = 0;
  data->capture->receiver = receiver_window;
  receiver->customdata = new ReleaseData{data->capture, receiver_window};
  return true;
}

static wmOperatorStatus invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  const int trigger = RNA_enum_get(op->ptr, "trigger_type");
  const int mouse = RNA_enum_get(op->ptr, "mouse_type");
  if (!CTX_wm_window(C) ||
      (!ISKEYBOARD(trigger) && !ELEM(trigger, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)) ||
      (mouse != 0 && !ELEM(mouse, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)))
  {
    return OPERATOR_CANCELLED;
  }
  const bool trigger_down = RNA_boolean_get(op->ptr, "trigger_down");
  const bool mouse_down = mouse != 0 && RNA_boolean_get(op->ptr, "mouse_down");
  if (!trigger_down && !mouse_down) {
    return OPERATOR_FINISHED;
  }
  wmWindow *window = CTX_wm_window(C);
  auto capture = std::make_shared<ReleaseCapture>(ReleaseCapture{
      trigger, mouse, trigger_down, mouse_down, RNA_boolean_get(op->ptr, "tool_session")});
  capture->source = window;
  capture->file_token = RNA_int_get(op->ptr, "file_release_token");
  /* Dispatch registers its queued file selector before the hotbox adds this guard. */
  for (const wmEventHandler &base : window->runtime->modalhandlers) {
    if (base.type == WM_HANDLER_TYPE_OP) {
      const auto &handler = reinterpret_cast<const wmEventHandler_Op &>(base);
      if (handler.is_fileselect && handler.op) {
        capture->file_operator = handler.op;
        break;
      }
    }
  }
  op->customdata = new ReleaseData{capture, window};
  /* The command may have destroyed its initiating region. Retain only window ownership. */
  wmEventHandler_Op *handler = WM_event_add_modal_handler_ex(window, nullptr, nullptr, op);
  if (capture->file_operator || capture->file_token) {
    handler->fileselect_handoff = fileselect_handoff;
  }
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  auto &owner = *static_cast<ReleaseData *>(op->customdata);
  auto &data = *owner.capture;
  if (!data.trigger_down && !data.mouse_down) {
    cleanup(C, op);
    return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
  }
  if (event->type == WINDEACTIVATE) {
    wmWindow *other = owner.window == data.source ? data.receiver : data.source;
    if (window_is_live(C, other) && other->active) {
      /* Opening/focusing this exact file window is an internal handoff. */
      return OPERATOR_PASS_THROUGH;
    }
    data.trigger_down = data.mouse_down = false;
    cleanup(C, op);
    return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
  }
  if (event->type == EVT_ESCKEY && event->val == KM_PRESS) {
    /* Cancellation of a preceding confirmation must never bind a later selector. */
    data.file_operator = nullptr;
    data.file_token = 0;
  }
  bool *down = event->type == data.trigger ? &data.trigger_down :
               event->type == data.mouse   ? &data.mouse_down :
                                             nullptr;
  bool consume = false;
  if (down && *down) {
    if (event->val == KM_RELEASE) {
      *down = false;
      consume = true;
    }
    else if (event->val == KM_PRESS) {
      consume = (event->flag & WM_EVENT_IS_REPEAT) != 0;
      if (!consume) {
        /* A new physical press proves that the preceding release was lost. */
        *down = false;
      }
    }
  }
  const bool finished = !data.trigger_down && !data.mouse_down;
  if (finished) {
    cleanup(C, op);
  }
  const wmOperatorStatus status = finished ? OPERATOR_FINISHED : OPERATOR_RUNNING_MODAL;
  /* RUNNING_MODAL | PASS_THROUGH stops the remaining modal list in Blender. Plain
   * PASS_THROUGH retains this handler while allowing the child and queued file-open events. */
  return consume  ? status :
         finished ? OPERATOR_FINISHED | OPERATOR_PASS_THROUGH :
                    OPERATOR_PASS_THROUGH;
}
}  // namespace

bool axismeld_hotbox_guard_allows_tool_session(const wmOperator *op, const int trigger_type)
{
  if (!op || op->type != WM_operatortype_find("VIEW3D_OT_axismeld_hotbox_release_guard", true)) {
    return false;
  }
  const auto *data = static_cast<const ReleaseData *>(op->customdata);
  return data && data->capture->tool_session && !data->capture->mouse_down &&
         data->capture->trigger != trigger_type;
}

std::string axismeld_hotbox_refresh(bContext *C)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  if (!wm) {
    return {};
  }
  PointerRNA ptr = RNA_id_pointer_create(&wm->id);
  if (!RNA_struct_find_property(&ptr, "axismeld_hotbox_snapshot")) {
    return {};
  }
  RNA_string_set(&ptr, "axismeld_hotbox_snapshot", "");
  if (!WM_operatortype_find("AXISMELD_OT_hotbox_refresh", true) ||
      WM_operator_name_call(
          C, "AXISMELD_OT_hotbox_refresh", wm::OpCallContext::ExecDefault, nullptr, nullptr) !=
          OPERATOR_FINISHED)
  {
    return {};
  }
  return RNA_string_get(&ptr, "axismeld_hotbox_snapshot");
}

wmOperatorStatus axismeld_hotbox_dispatch(bContext *C, const char *command, int *r_file_token)
{
  if (!WM_operatortype_find("AXISMELD_OT_hotbox_dispatch", true)) {
    return OPERATOR_CANCELLED;
  }
  PointerRNA props = WM_operator_properties_create("AXISMELD_OT_hotbox_dispatch");
  RNA_string_set(&props, "command", command);
  if (r_file_token) {
    *r_file_token = 0;
    if (ELEM(std::string_view(command), "file.open", "file.save_as")) {
      static int next_file_token = 0;
      next_file_token = next_file_token == INT_MAX ? 1 : next_file_token + 1;
      *r_file_token = next_file_token;
      RNA_int_set(&props, "file_release_token", next_file_token);
    }
  }
  const wmOperatorStatus result = WM_operator_name_call(
      C, "AXISMELD_OT_hotbox_dispatch", wm::OpCallContext::ExecDefault, &props, nullptr);
  WM_operator_properties_free(&props);
  return result;
}

wmOperatorStatus axismeld_hotbox_setting(bContext *C, const char *setting, const char *value)
{
  if (!WM_operatortype_find("AXISMELD_OT_hotbox_setting", true)) {
    return OPERATOR_CANCELLED;
  }
  PointerRNA props = WM_operator_properties_create("AXISMELD_OT_hotbox_setting");
  RNA_string_set(&props, "setting", setting);
  RNA_string_set(&props, "value", value);
  const wmOperatorStatus result = WM_operator_name_call(
      C, "AXISMELD_OT_hotbox_setting", wm::OpCallContext::ExecDefault, &props, nullptr);
  WM_operator_properties_free(&props);
  return result;
}

wmOperatorStatus axismeld_hotbox_guard_begin(
    bContext *C, int trigger_type, int mouse_type, bool trigger_down, bool mouse_down,
    bool tool_session, int file_release_token)
{
  PointerRNA props = WM_operator_properties_create("VIEW3D_OT_axismeld_hotbox_release_guard");
  RNA_enum_set(&props, "trigger_type", trigger_type);
  RNA_enum_set(&props, "mouse_type", mouse_type);
  RNA_boolean_set(&props, "trigger_down", trigger_down);
  RNA_boolean_set(&props, "mouse_down", mouse_down);
  RNA_boolean_set(&props, "tool_session", tool_session);
  RNA_int_set(&props, "file_release_token", file_release_token);
  const wmOperatorStatus result = WM_operator_name_call(C,
                                                        "VIEW3D_OT_axismeld_hotbox_release_guard",
                                                        wm::OpCallContext::InvokeDefault,
                                                        &props,
                                                        nullptr);
  WM_operator_properties_free(&props);
  return result;
}

void VIEW3D_OT_axismeld_hotbox_release_guard(wmOperatorType *ot)
{
  ot->name = "AxisMeld Hotbox Release Guard";
  ot->idname = "VIEW3D_OT_axismeld_hotbox_release_guard";
  ot->description = "Consume only residual releases captured by a closed hotbox";
  ot->invoke = invoke;
  ot->modal = modal;
  ot->cancel = cleanup;
  /* Added after the child, this runs ahead of priority child tools in the same window. */
  ot->flag = OPTYPE_INTERNAL | OPTYPE_MODAL_PRIORITY;
  RNA_def_enum(ot->srna,
               "trigger_type",
               rna_enum_event_type_items,
               EVT_SPACEKEY,
               "Trigger",
               "Actual captured keyboard key");
  RNA_def_enum(ot->srna,
               "mouse_type",
               rna_enum_event_type_items,
               0,
               "Mouse",
               "Actual captured mouse button, or NONE");
  RNA_def_boolean(
      ot->srna, "trigger_down", false, "Trigger Down", "Captured trigger awaits release");
  RNA_def_boolean(
      ot->srna, "mouse_down", false, "Mouse Down", "Captured mouse button awaits release");
  RNA_def_boolean(
      ot->srna, "tool_session", false, "Tool Session", "Release ownership came from a tool gesture");
  PropertyRNA *prop = RNA_def_int(ot->srna, "file_release_token", 0, 0, INT_MAX,
                                 "File Release Token", "Transient file invoke chain", 0, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}
}  // namespace blender

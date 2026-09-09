/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_context.hh"
#include "DNA_windowmanager_types.h"
#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"
#include "WM_api.hh"
#include "WM_types.hh"

#include "view3d_axismeld.hh"
#include "view3d_axismeld_hotbox_internal.hh"

namespace blender {
namespace {
struct ReleaseData {
  int trigger, mouse;
  bool trigger_down, mouse_down;
};

static void cleanup(bContext * /*C*/, wmOperator *op)
{
  delete static_cast<ReleaseData *>(op->customdata);
  op->customdata = nullptr;
}

static wmOperatorStatus invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  const int trigger = RNA_enum_get(op->ptr, "trigger_type");
  const int mouse = RNA_enum_get(op->ptr, "mouse_type");
  if (!CTX_wm_window(C) || !ISKEYBOARD(trigger) ||
      (mouse != 0 && !ELEM(mouse, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)))
  {
    return OPERATOR_CANCELLED;
  }
  const bool trigger_down = RNA_boolean_get(op->ptr, "trigger_down");
  const bool mouse_down = mouse != 0 && RNA_boolean_get(op->ptr, "mouse_down");
  if (!trigger_down && !mouse_down) {
    return OPERATOR_FINISHED;
  }
  op->customdata = new ReleaseData{trigger, mouse, trigger_down, mouse_down};
  /* The command may have destroyed its initiating region. Retain only window ownership. */
  WM_event_add_modal_handler_ex(CTX_wm_window(C), nullptr, nullptr, op);
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  auto &data = *static_cast<ReleaseData *>(op->customdata);
  if (event->type == WINDEACTIVATE) {
    cleanup(C, op);
    return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
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

wmOperatorStatus axismeld_hotbox_dispatch(bContext *C, const char *command)
{
  if (!WM_operatortype_find("AXISMELD_OT_hotbox_dispatch", true)) {
    return OPERATOR_CANCELLED;
  }
  PointerRNA props = WM_operator_properties_create("AXISMELD_OT_hotbox_dispatch");
  RNA_string_set(&props, "command", command);
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
    bContext *C, int trigger_type, int mouse_type, bool trigger_down, bool mouse_down)
{
  PointerRNA props = WM_operator_properties_create("VIEW3D_OT_axismeld_hotbox_release_guard");
  RNA_enum_set(&props, "trigger_type", trigger_type);
  RNA_enum_set(&props, "mouse_type", mouse_type);
  RNA_boolean_set(&props, "trigger_down", trigger_down);
  RNA_boolean_set(&props, "mouse_down", mouse_down);
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
}
}  // namespace blender

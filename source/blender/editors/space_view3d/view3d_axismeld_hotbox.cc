/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <cmath>
#include <cstring>

#include "BKE_context.hh"
#include "BKE_screen.hh"
#include "BKE_wm_runtime.hh"
#include "BLF_api.hh"
#include "BLI_listbase.hh"
#include "BLI_time.hh"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"
#include "ED_screen.hh"
#include "ED_space_api.hh"
#include "GPU_immediate.hh"
#include "GPU_state.hh"
#include "RNA_access.hh"
#include "RNA_define.hh"
#include "UI_interface.hh"
#include "WM_api.hh"
#include "WM_types.hh"
#include "wm_event_system.hh"

#include "view3d_axismeld.hh"

namespace blender {
namespace {
using axismeld::HotboxAction;
using axismeld::HotboxPhase;

struct HotboxData {
  axismeld::HotboxState state;
  wmWindow *window;
  bScreen *screen;
  ScrArea *area;
  ARegion *region;
  View3D *space;
  ARegionType *region_type;
  wmTimer *timer = nullptr;
  void *draw_handle = nullptr;
  int trigger;
  eContextObjectMode mode;
  unsigned int scene_uid;
  float center[2], origin[2];
  float scale;
};

/* Validate each containing live list before inspecting the next captured pointer. */
static bool source_live(const bContext *C, const HotboxData &data)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  if (!wm || BLI_findindex(&wm->windows, data.window) < 0 ||
      WM_window_get_active_screen(data.window) != data.screen ||
      BLI_findindex(&data.screen->areabase, data.area) < 0 ||
      data.area->spacetype != SPACE_VIEW3D ||
      data.area->spacedata.first_as<View3D>() != data.space ||
      BLI_findindex(&data.area->regionbase, data.region) < 0)
  {
    return false;
  }
  return data.region->regiontype == RGN_TYPE_WINDOW && data.region->regiondata;
}

static void remove_visuals(bContext *C, HotboxData &data)
{
  if (data.draw_handle) {
    ED_region_draw_cb_exit(data.region_type, data.draw_handle);
    data.draw_handle = nullptr;
  }
  if (data.timer) {
    WM_event_timer_remove(CTX_wm_manager(C), nullptr, data.timer);
    data.timer = nullptr;
  }
  if (source_live(C, data)) {
    ED_region_tag_redraw(data.region);
  }
}

static void cleanup(bContext *C, wmOperator *op)
{
  if (auto *data = static_cast<HotboxData *>(op->customdata)) {
    remove_visuals(C, *data);
    delete data;
    op->customdata = nullptr;
  }
}

static void draw(const bContext *C, ARegion *region, void *customdata)
{
  const auto &data = *static_cast<HotboxData *>(customdata);
  if (!source_live(C, data) || region != data.region || CTX_wm_window(C) != data.window) {
    return;
  }
  const float scale = data.scale;
  const bool marking = data.state.phase() == HotboxPhase::Marking;
  const float cx = (marking ? data.origin[0] : data.center[0]) - region->winrct.xmin;
  const float cy = (marking ? data.origin[1] : data.center[1]) - region->winrct.ymin;
  struct Label {
    const char *text;
    float x, y;
    HotboxAction action;
  };
  const Label labels[] = {{"AxisMeld", 0, 0, HotboxAction::None},
                          {"Perspective", 0, 48, HotboxAction::Perspective},
                          {"Side", 95, 0, HotboxAction::Side},
                          {"Front", 0, -48, HotboxAction::Front},
                          {"Top", -95, 0, HotboxAction::Top}};
  const int font = BLF_default();
  BLF_size(font, 12.0f * scale);
  GPU_blend(GPU_BLEND_ALPHA);
  const uint pos = GPU_vertformat_attr_add(
      immVertexFormat(), "pos", gpu::VertAttrType::SFLOAT_32_32);
  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
  for (const Label &label : labels) {
    const float x = cx + label.x * scale;
    const float y = cy + label.y * scale;
    const bool selected = label.action != HotboxAction::None &&
                          data.state.candidate() == label.action;
    immUniformColor4f(selected ? 0.17f : 0.055f, selected ? 0.40f : 0.055f, 0.11f, 0.92f);
    immRectf(pos, x - 43 * scale, y - 15 * scale, x + 43 * scale, y + 15 * scale);
  }
  immUnbindProgram();
  for (const Label &label : labels) {
    BLF_color4f(font, 0.95f, 0.95f, 0.95f, 1.0f);
    const float width = BLF_width(font, label.text, std::strlen(label.text));
    BLF_position(font, cx + label.x * scale - width / 2, cy + (label.y - 4) * scale, 0);
    BLF_draw(font, label.text, std::strlen(label.text));
  }
  GPU_blend(GPU_BLEND_NONE);
}

static bool source_context(bContext *C, const HotboxData &data)
{
  if (!source_live(C, data)) {
    return false;
  }
  /* WM modal context is frozen to the initiating region, even while the pointer moves. */
  return CTX_wm_window(C) == data.window && CTX_wm_area(C) == data.area &&
         CTX_wm_region(C) == data.region && CTX_data_mode_enum(C) == data.mode &&
         CTX_data_scene(C)->id.session_uid == data.scene_uid && axismeld_view_context_poll(C);
}

static wmOperatorStatus invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  if (!ISKEYBOARD(event->type) || event->val != KM_PRESS || (event->flag & WM_EVENT_IS_REPEAT)) {
    return OPERATOR_PASS_THROUGH;
  }
  wmWindow *window = CTX_wm_window(C);
  /* Respect active tools even when their modal callback deliberately passes this key through. */
  for (const wmEventHandler &handler : window->runtime->modalhandlers) {
    if (ELEM(handler.type, WM_HANDLER_TYPE_OP, WM_HANDLER_TYPE_UI)) {
      return OPERATOR_PASS_THROUGH;
    }
  }
  auto *data = new HotboxData();
  data->window = window;
  data->screen = CTX_wm_screen(C);
  data->area = CTX_wm_area(C);
  data->region = CTX_wm_region(C);
  data->space = CTX_wm_view3d(C);
  data->region_type = data->region->runtime->type;
  data->trigger = event->type;
  data->mode = CTX_data_mode_enum(C);
  data->scene_uid = CTX_data_scene(C)->id.session_uid;
  data->scale = UI_SCALE_FAC;
  /* Preserve the press point at edges too: native region clipping trims labels, never the hit
   * origin. */
  data->center[0] = event->xy[0];
  data->center[1] = event->xy[1];
  data->state.begin(BLI_time_now_seconds(), RNA_float_get(op->ptr, "tap_seconds"));
  op->customdata = data;
  data->draw_handle = ED_region_draw_cb_activate(
      data->region_type, draw, data, REGION_DRAW_POST_PIXEL);
  data->timer = WM_event_timer_add(CTX_wm_manager(C), window, TIMER, 0.02);
  WM_event_add_modal_handler(C, op);
  ED_region_tag_redraw(data->region);
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  auto &data = *static_cast<HotboxData *>(op->customdata);
  if (data.state.phase() == HotboxPhase::Cancelled) {
    if (event->type == data.trigger) {
      if (event->val == KM_RELEASE) {
        cleanup(C, op);
        return OPERATOR_CANCELLED;
      }
      if (event->val == KM_PRESS && !(event->flag & WM_EVENT_IS_REPEAT)) {
        /* A fresh physical press also recovers after a lost release during window deactivation. */
        cleanup(C, op);
        return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
      }
      return OPERATOR_RUNNING_MODAL;
    }
    return OPERATOR_RUNNING_MODAL | OPERATOR_PASS_THROUGH;
  }
  if (event->type == WINDEACTIVATE || event->type == EVT_ESCKEY || !source_context(C, data)) {
    data.state.cancel();
    remove_visuals(C, data);
    return OPERATOR_RUNNING_MODAL;
  }
  data.state.advance(BLI_time_now_seconds());
  if (event->type == data.trigger) {
    if (event->val == KM_RELEASE) {
      const HotboxAction action = data.state.release_trigger(BLI_time_now_seconds());
      /* Remove the region draw callback before native quad-view can destroy any panes. */
      cleanup(C, op);
      if (action == HotboxAction::ToggleQuad) {
        axismeld_view_action(C, op, action);
      }
      return OPERATOR_FINISHED;
    }
    return OPERATOR_RUNNING_MODAL;
  }
  if (event->type == LEFTMOUSE && event->val == KM_PRESS &&
      ELEM(data.state.phase(), HotboxPhase::Pending, HotboxPhase::Held))
  {
    if (std::abs(event->xy[0] - data.center[0]) <= 43 * data.scale &&
        std::abs(event->xy[1] - data.center[1]) <= 15 * data.scale)
    {
      data.origin[0] = event->xy[0];
      data.origin[1] = event->xy[1];
      data.state.begin_marking();
    }
    else {
      /* Any menu mouse interaction irrevocably removes tap eligibility. */
      data.state.begin_marking();
      data.state.release_mouse();
    }
  }
  if (data.state.phase() == HotboxPhase::Marking &&
      (ISMOUSE_MOTION(event->type) || (event->type == LEFTMOUSE && event->val == KM_RELEASE)))
  {
    data.state.motion(
        event->xy[0] - data.origin[0], event->xy[1] - data.origin[1], 12 * data.scale);
    if (event->type == LEFTMOUSE) {
      const HotboxAction action = data.state.release_mouse();
      if (action != HotboxAction::None) {
        axismeld_view_action(C, op, action);
      }
    }
  }
  ED_region_tag_redraw(data.region);
  /* Active gestures own mouse, keyboard modifiers, and timers; nothing selects or navigates. */
  return OPERATOR_RUNNING_MODAL;
}
}  // namespace

void VIEW3D_OT_axismeld_hotbox(wmOperatorType *ot)
{
  ot->name = "AxisMeld Hotbox";
  ot->idname = "VIEW3D_OT_axismeld_hotbox";
  ot->description = "Hold for view marking gestures or tap to maximize and restore a pane";
  ot->poll = axismeld_view_context_poll;
  ot->invoke = invoke;
  ot->modal = modal;
  ot->cancel = cleanup;
  RNA_def_float(ot->srna,
                "tap_seconds",
                0.4f,
                0.1f,
                1.0f,
                "Tap Threshold",
                "Release before this time to toggle the layout",
                0.1f,
                1.0f);
}
}  // namespace blender

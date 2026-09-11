/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "BKE_context.hh"
#include "BKE_report.hh"
#include "BKE_screen.hh"
#include "BKE_wm_runtime.hh"
#include "BLI_listbase.hh"
#include "BLI_time.hh"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"
#include "ED_screen.hh"
#include "ED_space_api.hh"
#include "RNA_access.hh"
#include "RNA_define.hh"
#include "UI_interface.hh"
#include "WM_api.hh"
#include "WM_types.hh"
#include "view3d_axismeld.hh"
#include "view3d_axismeld_hotbox_internal.hh"
#include "wm_event_system.hh"
#include <algorithm>

namespace blender {
namespace {
using namespace axismeld;
struct HotboxData : HotboxVisual {
  HotboxState state;
  wmWindow *window;
  bScreen *screen;
  ScrArea *area;
  ARegion *region;
  View3D *space;
  ARegionType *region_type;
  rcti region_rect;
  wmTimer *timer = nullptr;
  void *draw_handle = nullptr;
  int trigger;
  eContextObjectMode mode;
  unsigned int scene_uid;
  bool navigation_consumed = false;
  bool menu_entered_on_press = false;
  bool mouse_moved_since_press = false;
  bool tool_shown = false;
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
  const rcti &rect = data.region->winrct;
  return data.region->regiontype == RGN_TYPE_WINDOW && data.region->regiondata &&
         data.scale == UI_SCALE_FAC && rect.xmin == data.region_rect.xmin &&
         rect.xmax == data.region_rect.xmax && rect.ymin == data.region_rect.ymin &&
         rect.ymax == data.region_rect.ymax;
}

static void cleanup(bContext *C, wmOperator *op)
{
  if (auto *data = static_cast<HotboxData *>(op->customdata)) {
    if (data->draw_handle) {
      ED_region_draw_cb_exit(data->region_type, data->draw_handle);
    }
    if (data->timer) {
      WM_event_timer_remove(CTX_wm_manager(C), nullptr, data->timer);
    }
    if (source_live(C, *data)) {
      ED_region_tag_redraw(data->region);
    }
    delete data;
    op->customdata = nullptr;
  }
}

static void draw(const bContext *C, ARegion *region, void *customdata)
{
  const auto &data = *static_cast<HotboxData *>(customdata);
  if (source_live(C, data) && region == data.region && CTX_wm_window(C) == data.window) {
    hotbox_draw(C, data);
  }
}

static bool source_context(bContext *C, const HotboxData &data)
{
  if (!source_live(C, data)) {
    return false;
  }
  return CTX_wm_window(C) == data.window && CTX_wm_area(C) == data.area &&
         CTX_wm_region(C) == data.region && CTX_data_mode_enum(C) == data.mode &&
         CTX_data_scene(C) && CTX_data_scene(C)->id.session_uid == data.scene_uid &&
         axismeld_view_context_poll(C);
}

static wmOperatorStatus close_guard(bContext *C, wmOperator *op, const bool trigger_down)
{
  const auto &data = *static_cast<HotboxData *>(op->customdata);
  const int trigger = data.trigger, mouse = data.active_mouse;
  const bool tool_session = !data.tool_root.empty();
  cleanup(C, op);
  if (trigger_down || mouse) {
    axismeld_hotbox_guard_begin(C, trigger, mouse, trigger_down, mouse != 0, tool_session);
  }
  return OPERATOR_FINISHED;
}

static bool refresh(bContext *C, HotboxData &data)
{
  MenuSnapshot next;
  std::string error;
  if (!parse_menu_snapshot(axismeld_hotbox_refresh(C), next, error)) {
    return false;
  }
  data.snapshot = std::move(next);
  hotbox_measure(data);
  hotbox_layout(data);
  return data.menu_layout.supported;
}

static wmOperatorStatus submit(bContext *C, wmOperator *op, const MenuNode &leaf)
{
  auto &data = *static_cast<HotboxData *>(op->customdata);
  // Strings must outlive cleanup and Python rebuilding its catalog/context.
  const std::string command = leaf.command, value = leaf.value;
  const bool setting = leaf.kind == MenuKind::Setting;
  if (!setting && hotbox_command_closes(command)) {
    const int trigger = data.trigger, mouse = data.active_mouse;
    const bool tool_session = !data.tool_root.empty();
    cleanup(C, op);
    axismeld_hotbox_dispatch(C, command.c_str());
    // No source-area/region access after dispatch: mode/quad commands can destroy them.
    axismeld_hotbox_guard_begin(C, trigger, mouse, true, mouse != 0, tool_session);
    return OPERATOR_FINISHED;
  }
  const wmOperatorStatus result = setting ?
                                      axismeld_hotbox_setting(C, command.c_str(), value.c_str()) :
                                      axismeld_hotbox_dispatch(C, command.c_str());
  if (result == OPERATOR_FINISHED) {
    data.open_path.clear();
  }
  if (!source_context(C, data) || (result == OPERATOR_FINISHED && !refresh(C, data))) {
    return close_guard(C, op, true);
  }
  return OPERATOR_RUNNING_MODAL;
}

static void open_menu(HotboxData &data, const MenuRect &rect)
{
  const size_t prefix = !data.open_path.empty() && data.open_path.front() == "center" ? 1 : 0;
  if (rect.depth == 0) {
    if (rect.id == "views") {
      return;
    }
    if (!prefix && !data.open_path.empty() && data.open_path.front() == rect.id) {
      return;  // Returning to a parent retains the deeper path.
    }
    data.open_path = {rect.id};
  }
  else {
    const size_t index = prefix + rect.depth;
    if (index < data.open_path.size() && data.open_path[index] == rect.id) {
      return;
    }
    data.open_path.resize(index);
    data.open_path.push_back(rect.id);
  }
  hotbox_layout(data);
}

static void scroll_owner(HotboxData &data, const std::string &owner, const int delta)
{
  const auto begin = data.open_path.begin() +
                     (!data.open_path.empty() && data.open_path.front() == "center" ? 1 : 0);
  const auto item = std::find(begin, data.open_path.end(), owner);
  if (item != data.open_path.end()) {
    data.open_path.erase(item + 1, data.open_path.end());
  }
  else {
    data.open_path.clear();
  }
  const MenuNode *node = hotbox_find_node(data.snapshot.menus, owner);
  if (node || owner == "@main") {
    const int item_count = int(node ? node->children.size() : data.snapshot.menus.size());
    data.scroll_offsets[owner] = menu_scroll_offset_transition(
        data.menu_layout, owner, data.scroll_offsets[owner], delta, item_count);
    hotbox_layout(data);
  }
}

static void back_to_parent(HotboxData &data, const std::string &owner)
{
  const auto begin = data.open_path.begin() +
                     (!data.open_path.empty() && data.open_path.front() == "center" ? 1 : 0);
  const auto item = std::find(begin, data.open_path.end(), owner);
  if (item != data.open_path.end()) {
    data.open_path.erase(item, data.open_path.end());
  }
  if (data.open_path.size() == 1 && data.open_path.front() == "center") {
    data.open_path.clear();
  }
  data.marking = false;
  hotbox_layout(data);
}

static void scroll_control(HotboxData &data, const std::string &id)
{
  const size_t end = id.rfind(':');
  scroll_owner(data, id.substr(8, end - 8), id.substr(end + 1) == "next" ? 1 : -1);
}

static std::string direction_id(const HotboxAction action)
{
  switch (action) {
    case HotboxAction::Perspective:
      return "views.perspective";
    case HotboxAction::Side:
      return "views.side";
    case HotboxAction::Front:
      return "views.front";
    case HotboxAction::Top:
      return "views.top";
    case HotboxAction::Left:
      return "views.left";
    case HotboxAction::Back:
      return "views.back";
    case HotboxAction::Bottom:
      return "views.bottom";
    default:
      return {};
  }
}

static wmOperatorStatus invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  if (!ISKEYBOARD(event->type) || event->val != KM_PRESS || (event->flag & WM_EVENT_IS_REPEAT)) {
    return OPERATOR_PASS_THROUGH;
  }
  wmWindow *window = CTX_wm_window(C);
  const std::string tool_root = RNA_string_get(op->ptr, "tool_menu");
  for (const wmEventHandler &handler : window->runtime->modalhandlers) {
    if (!tool_root.empty() && handler.type == WM_HANDLER_TYPE_OP &&
        axismeld_hotbox_guard_allows_tool_session(
            reinterpret_cast<const wmEventHandler_Op &>(handler).op, event->type))
    {
      // The priority guard retains its old key; it does not own this trigger or the mouse.
      continue;
    }
    if (ELEM(handler.type, WM_HANDLER_TYPE_OP, WM_HANDLER_TYPE_UI)) {
      return OPERATOR_PASS_THROUGH;
    }
  }
  MenuSnapshot snapshot;
  std::string error;
  if (!parse_menu_snapshot(RNA_string_get(op->ptr, "menu_json"), snapshot, error)) {
    BKE_report(op->reports, RPT_WARNING, error.c_str());
    return OPERATOR_CANCELLED;
  }
  if (!tool_root.empty()) {
    const MenuNode *root = hotbox_find_node(snapshot.menus, tool_root);
    if ((tool_root != "tools.select" && tool_root != "tools.move" &&
         tool_root != "tools.rotate" && tool_root != "tools.scale") ||
        !root || root->kind != MenuKind::Menu || !root->enabled || root->presentation != "radial")
    {
      return OPERATOR_CANCELLED;
    }
  }
  auto *data = new HotboxData();
  data->tool_root = tool_root;
  data->tap_eligible = tool_root.empty();
  data->snapshot = std::move(snapshot);
  data->window = window;
  data->screen = CTX_wm_screen(C);
  data->area = CTX_wm_area(C);
  data->region = CTX_wm_region(C);
  data->space = CTX_wm_view3d(C);
  data->region_type = data->region->runtime->type;
  data->region_rect = data->region->winrct;
  data->trigger = event->type;
  data->mode = CTX_data_mode_enum(C);
  data->scene_uid = CTX_data_scene(C)->id.session_uid;
  data->scale = UI_SCALE_FAC;
  data->width = data->region->winx / data->scale;
  data->height = data->region->winy / data->scale;
  data->center[0] = (event->xy[0] - data->region->winrct.xmin) / data->scale;
  data->center[1] = (event->xy[1] - data->region->winrct.ymin) / data->scale;
  hotbox_measure(*data);
  if (tool_root.empty()) {
    hotbox_layout(*data);
  }
  if (tool_root.empty() && !data->menu_layout.supported) {
    BKE_report(op->reports,
               RPT_WARNING,
               "Viewport cannot fit hotbox targets (minimum 340 x 200 logical pixels)");
  }
  data->state.begin(BLI_time_now_seconds(), RNA_float_get(op->ptr, "tap_seconds"));
  op->customdata = data;
  if (tool_root.empty() && data->menu_layout.supported) {
    data->draw_handle = ED_region_draw_cb_activate(
        data->region_type, draw, data, REGION_DRAW_POST_PIXEL);
  }
  data->timer = WM_event_timer_add(CTX_wm_manager(C), window, TIMER, .02);
  WM_event_add_modal_handler(C, op);
  ED_region_tag_redraw(data->region);
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus tool_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  auto &data = *static_cast<HotboxData *>(op->customdata);
  const float x = (event->xy[0] - data.region->winrct.xmin) / data.scale;
  const float y = (event->xy[1] - data.region->winrct.ymin) / data.scale;
  if (event->modifier ||
      (!ISTIMER(event->type) && !ISMOUSE_MOTION(event->type) && event->type != LEFTMOUSE))
  {
    close_guard(C, op, true);
    return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
  }
  if (!data.tool_shown) {
    if (event->type != LEFTMOUSE || event->val != KM_PRESS) {
      return OPERATOR_RUNNING_MODAL | OPERATOR_PASS_THROUGH;
    }
    data.tool_shown = true;
    data.active_mouse = LEFTMOUSE;
    data.center[0] = data.origin[0] = data.press_position[0] = x;
    data.center[1] = data.origin[1] = data.press_position[1] = y;
    data.pointer_position[0] = x;
    data.pointer_position[1] = y;
    data.open_path = {data.tool_root};
    hotbox_layout(data);
    if (!data.menu_layout.supported) {
      return close_guard(C, op, true);
    }
    data.draw_handle = ED_region_draw_cb_activate(
        data.region_type, draw, &data, REGION_DRAW_POST_PIXEL);
    ED_region_tag_redraw(data.region);
    return OPERATOR_RUNNING_MODAL;
  }
  if (ISMOUSE_MOTION(event->type) || event->type == LEFTMOUSE) {
    data.pointer_position[0] = x;
    data.pointer_position[1] = y;
    const bool at_origin = (x - data.origin[0]) * (x - data.origin[0]) +
                               (y - data.origin[1]) * (y - data.origin[1]) <= 12 * 12;
    if (at_origin && data.open_path.size() > 1)
    {
      data.open_path.resize(1);
      hotbox_layout(data);
    }
    // Edge clamping may move a button under the real press origin. The dead zone wins
    // over all menu hit testing, including reopening a child after returning to cancel it.
    const MenuRect *hover = at_origin ? nullptr : hit_menu_rect(data.menu_layout, x, y);
    const MenuRect rect = hover ? *hover : MenuRect{};
    data.hover_id = hover ? rect.id : "";
    data.hover_depth = hover ? rect.depth : -1;
    const MenuNode *node = hotbox_find_node(data.snapshot.menus, data.hover_id);
    if (ISMOUSE_MOTION(event->type) && node && node->enabled && node->kind == MenuKind::Menu) {
      open_menu(data, rect);
    }
    if (event->type == LEFTMOUSE && event->val == KM_RELEASE) {
      data.active_mouse = 0;
      if (node && node->enabled && ELEM(node->kind, MenuKind::Command, MenuKind::Setting)) {
        return submit(C, op, *node);
      }
      return close_guard(C, op, true);
    }
    ED_region_tag_redraw(data.region);
  }
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  auto &data = *static_cast<HotboxData *>(op->customdata);
  if (event->type == WINDEACTIVATE && !data.tool_root.empty()) {
    // Releases may occur outside this window. Do not create a guard after the focus-loss
    // event it would need in order to clear its own ownership.
    cleanup(C, op);
    return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
  }
  if (event->type == WINDEACTIVATE || event->type == EVT_ESCKEY || !source_context(C, data)) {
    if (event->type == data.active_mouse && event->val == KM_RELEASE) {
      data.active_mouse = 0;
    }
    return close_guard(C, op, !(event->type == data.trigger && event->val == KM_RELEASE));
  }
  data.state.advance(BLI_time_now_seconds());
  if (event->type == data.trigger) {
    if (event->val == KM_RELEASE) {
      const bool tap = data.tap_eligible && data.state.release_trigger(BLI_time_now_seconds()) ==
                                                HotboxAction::ToggleQuad;
      if (tap) {
        cleanup(C, op);
        axismeld_hotbox_dispatch(C, "view.toggle_quad");
        return OPERATOR_FINISHED;
      }
      return close_guard(C, op, false);
    }
    return OPERATOR_RUNNING_MODAL;
  }
  if (!data.tool_root.empty()) {
    return tool_modal(C, op, event);
  }
  const float x = (event->xy[0] - data.region->winrct.xmin) / data.scale;
  const float y = (event->xy[1] - data.region->winrct.ymin) / data.scale;
  const MenuRect *hover = hit_menu_rect(data.menu_layout, x, y);
  // Copy before open_menu/scroll can rebuild the owning rect vector.
  const MenuRect rect = hover ? *hover : MenuRect{};
  data.hover_id = hover ? rect.id : "";
  data.hover_depth = hover ? rect.depth : -1;
  const std::string item = hit_menu(data.menu_layout, x, y);
  const MenuNode *node = hotbox_find_node(data.snapshot.menus, item);
  const bool mouse = ELEM(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE);
  if (ISMOUSE_MOTION(event->type) || mouse) {
    data.pointer_position[0] = x;
    data.pointer_position[1] = y;
  }
  if (mouse && event->val == KM_PRESS && !data.active_mouse) {
    data.tap_eligible = false;
    data.active_mouse = event->type;
    data.navigation_consumed = false;
    data.menu_entered_on_press = false;
    data.mouse_moved_since_press = false;
    data.press_position[0] = x;
    data.press_position[1] = y;
    data.pending_leaf.clear();
    // Real menu rectangles (including disabled/separators) occlude the center-only fallback.
    const bool blank_center = data.menu_layout.supported && data.open_path.empty() &&
                              data.snapshot.style == "center" && !hover && x >= 0 &&
                              x < data.width && y >= 0 && y < data.height;
    if ((item == "views" && rect.depth == 0) || blank_center) {
      const int button = event->type == LEFTMOUSE ? 0 : event->type == MIDDLEMOUSE ? 1 : 2;
      const std::string &mapping = data.snapshot.center_buttons[button];
      data.open_path.clear();
      if (mapping == "views") {
        data.marking = true;
        data.open_path = {"center", "views"};
        data.origin[0] = x;
        data.origin[1] = y;
        data.candidate = HotboxAction::None;
      }
      else if (!mapping.empty()) {
        data.menu_entered_on_press = true;
        data.open_path = {"center", mapping};
      }
      hotbox_layout(data);
    }
    else if (item.starts_with("@scroll:")) {
      data.navigation_consumed = true;
      scroll_control(data, item);
    }
    else if (!rect.interactive && rect.native_menu && rect.id.starts_with("@scroll:")) {
      /* Disabled native navigation still owns its press/release without changing the page. */
      data.navigation_consumed = true;
    }
    else if (item.starts_with("@back:")) {
      data.navigation_consumed = true;
      back_to_parent(data, item.substr(6));
    }
    else if (node && node->kind == MenuKind::Menu) {
      data.menu_entered_on_press = true;
      open_menu(data, rect);
    }
  }
  if (data.active_mouse && ISMOUSE_MOTION(event->type) &&
      (x != data.press_position[0] || y != data.press_position[1]))
  {
    data.mouse_moved_since_press = true;
  }
  if (event->type == data.active_mouse && event->val == KM_RELEASE && data.menu_entered_on_press &&
      !data.mouse_moved_since_press)
  {
    // A click enters its directory. Inward layout may put another target under this same
    // coordinate, but only a subsequent press or actual held motion can select that target.
    data.active_mouse = 0;
    data.menu_entered_on_press = false;
    data.pending_leaf.clear();
    ED_region_tag_redraw(data.region);
    return OPERATOR_RUNNING_MODAL;
  }
  // These controls execute on press and rebuild the ring immediately. Their release still
  // belongs to that control, even when it becomes disabled or exposes a different parent item.
  // Ordinary menu-title presses intentionally retain held-drag-to-leaf behavior below.
  if (data.navigation_consumed) {
    if (event->type == data.active_mouse && event->val == KM_RELEASE) {
      data.active_mouse = 0;
      data.navigation_consumed = false;
    }
    ED_region_tag_redraw(data.region);
    return OPERATOR_RUNNING_MODAL;
  }
  if (ISMOUSE_MOTION(event->type) && data.active_mouse && !data.open_path.empty() && node &&
      node->kind == MenuKind::Menu)
  {
    open_menu(data, rect);
  }
  if (!data.marking && ELEM(event->type, WHEELUPMOUSE, WHEELDOWNMOUSE)) {
    data.tap_eligible = false;
    if (hover) {
      std::string owner;
      if (item.starts_with("@scroll:")) {
        owner = item.substr(8, item.rfind(':') - 8);
      }
      else if (rect.depth > 0) {
        const size_t index = rect.depth - 1 +
                             (!data.open_path.empty() && data.open_path.front() == "center" ? 1 :
                                                                                              0);
        if (index < data.open_path.size()) {
          owner = data.open_path[index];
        }
      }
      else {
        for (const MenuNode &root : data.snapshot.menus) {
          for (const MenuNode &child : root.children) {
            if (child.id == rect.id) {
              owner = root.id;
            }
          }
        }
      }
      scroll_owner(data, owner, event->type == WHEELUPMOUSE ? -1 : 1);
    }
  }
  if (data.active_mouse && (ISMOUSE_MOTION(event->type) ||
                            (event->type == data.active_mouse && event->val == KM_RELEASE)))
  {
    if (data.marking) {
      const float dx = x - data.origin[0], dy = y - data.origin[1];
      if (dx * dx + dy * dy <= 12 * 12 && data.open_path.size() > 2) {
        // Returning to the real gesture origin backs out of Style without releasing
        // the owner. A new outward stroke can select a view in the same gesture.
        data.open_path.resize(2);
        hotbox_layout(data);
      }
      // Real-origin dead zone wins first. Outside it, visible targets keep their semantics
      // even after inward placement; only untargeted space uses the original direction sectors.
      // Only untargeted space in the view ring uses sectors. Style and its submenu
      // own their real rectangles; the retained first level never participates in hits.
      data.candidate = hover || data.open_path.size() > 2 ? HotboxAction::None :
                                                            hotbox_direction(dx, dy, 12);
      data.pending_leaf = dx * dx + dy * dy <= 12 * 12 ? "" :
                          node && (rect.direction_label || node->kind == MenuKind::Setting) ?
                                                         item :
                                                         direction_id(data.candidate);
    }
    else {
      data.pending_leaf = node && ELEM(node->kind, MenuKind::Command, MenuKind::Setting) ? item :
                                                                                           "";
    }
    if (event->type == data.active_mouse && event->val == KM_RELEASE) {
      data.active_mouse = 0;
      if (data.marking || ((!node || node->kind != MenuKind::Menu) &&
                           !item.starts_with("@scroll:") && !item.starts_with("@back:")))
      {
        data.open_path.clear();
      }
      data.marking = false;
      data.candidate = HotboxAction::None;
      hotbox_layout(data);
      const MenuNode *leaf = hotbox_find_node(data.snapshot.menus, data.pending_leaf);
      data.pending_leaf.clear();
      if (leaf && leaf->enabled && ELEM(leaf->kind, MenuKind::Command, MenuKind::Setting)) {
        if (submit(C, op, *leaf) == OPERATOR_FINISHED) {
          return OPERATOR_FINISHED;
        }
      }
    }
  }
  ED_region_tag_redraw(data.region);
  return OPERATOR_RUNNING_MODAL;
}
}  // namespace

void VIEW3D_OT_axismeld_hotbox(wmOperatorType *ot)
{
  ot->name = "AxisMeld Hotbox";
  ot->idname = "VIEW3D_OT_axismeld_hotbox";
  ot->description = "Hold for Maya-style menus and central view gestures, tap to toggle a pane";
  ot->poll = axismeld_view_context_poll;
  ot->invoke = invoke;
  ot->modal = modal;
  ot->cancel = cleanup;
  RNA_def_float(ot->srna,
                "tap_seconds",
                .4f,
                .1f,
                1,
                "Tap Threshold",
                "Release before this time to toggle the layout",
                .1f,
                1);
  PropertyRNA *prop = RNA_def_string(
      ot->srna, "menu_json", nullptr, 0, "Menu Snapshot", "Validated declarative menu snapshot");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_string(ot->srna, "tool_menu", nullptr, 0, "Tool Menu",
                       "Registered tool root, armed until left mouse press");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}
}  // namespace blender

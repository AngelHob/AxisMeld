/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "BKE_context.hh"
#include "BKE_editmesh.hh"
#include "BKE_layer.hh"
#include "BKE_lib_id.hh"
#include "BKE_library.hh"
#include "DNA_object_types.h"
#include "DEG_depsgraph.hh"
#include "ED_object.hh"
#include "ED_outliner.hh"
#include "ED_view3d.hh"
#include "BKE_report.hh"
#include "BKE_screen.hh"
#include "BKE_wm_runtime.hh"
#include "BLI_listbase.hh"
#include "BLI_time.hh"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_userdef_types.h"
#include "BLI_string.hh"
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
#include "AXM_context_modeling.hh"
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
  bool component_session = false;
  bool creation_session = false;
  bool modeling_session = false;
  bool object_modeling_session = false;
  std::string companion_scroll_hover;
  double companion_scroll_next = 0;
  unsigned int object_target_uid = 0;
  unsigned int object_target_data_uid = 0;
  unsigned int object_active_uid = 0;
  std::vector<std::pair<unsigned int, unsigned int>> object_selection;
  wmEventModifierFlag required_modifiers = wmEventModifierFlag(0);
  unsigned int component_target_uid = 0;
  unsigned int component_data_uid = 0;
  unsigned int component_active_uid = 0;
  bool component_selected_target = false;
  std::vector<std::pair<unsigned int, unsigned int>> component_selection;
  ViewLayer *component_view_layer = nullptr;
  std::vector<std::string> return_path;
  bool center_return_armed = false;
};

/* Only live regions are read here; no sibling pointers survive this calculation. */
static MenuBounds hotbox_safe_bounds(const ScrArea &area, ARegion &region, const float scale)
{
  const rcti &visible = *ED_region_visible_rect(&region);
  const rcti &window = region.winrct;
  // Blender's pixel rectangles include xmax/ymax. Layout bounds are half-open.
  MenuBounds bounds{float(std::max(0, visible.xmin)),
                    float(std::max(0, visible.ymin)),
                    float(std::min(int(region.winx), visible.xmax + 1)),
                    float(std::min(int(region.winy), visible.ymax + 1))};
  for (const ARegion &sibling : area.regionbase) {
    if (&sibling == &region || !sibling.overlap || !sibling.runtime) {
      continue;
    }
    // Hidden/poll-failed/collapsed regions cease obstructing only after animation ends.
    if (!sibling.runtime->regiontimer &&
        (!sibling.runtime->visible ||
         (sibling.flag & (RGN_FLAG_HIDDEN | RGN_FLAG_TOO_SMALL | RGN_FLAG_POLL_FAILED))))
    {
      continue;
    }
    // Ordinary input routing still uses the full winrct during slide/fade animation.
    // Intersect the original WINDOW, not an already clipped bound: order must not matter.
    const rcti &obstacle = sibling.winrct;
    if (obstacle.xmax < window.xmin || obstacle.xmin > window.xmax ||
        obstacle.ymax < window.ymin || obstacle.ymin > window.ymax)
    {
      continue;
    }
    switch (RGN_ALIGN_ENUM_FROM_MASK(sibling.alignment)) {
      case RGN_ALIGN_TOP:
        bounds.ymax = std::min(bounds.ymax, float(obstacle.ymin - window.ymin));
        break;
      case RGN_ALIGN_BOTTOM:
        bounds.ymin = std::max(bounds.ymin, float(obstacle.ymax - window.ymin + 1));
        break;
      case RGN_ALIGN_LEFT:
        bounds.xmin = std::max(bounds.xmin, float(obstacle.xmax - window.xmin + 1));
        break;
      case RGN_ALIGN_RIGHT:
        bounds.xmax = std::min(bounds.xmax, float(obstacle.xmin - window.xmin));
        break;
      default:
        break;
    }
  }
  return {bounds.xmin / scale, bounds.ymin / scale,
           bounds.xmax / scale, bounds.ymax / scale};
}

/* Validate each containing live list before inspecting the next captured pointer. */
static bool source_containers_live(const bContext *C, const HotboxData &data)
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
  return true;
}

static bool source_live(const bContext *C, const HotboxData &data)
{
  if (!source_containers_live(C, data)) {
    return false;
  }
  const rcti &rect = data.region->winrct;
  return data.region->regiontype == RGN_TYPE_WINDOW && data.region->regiondata &&
         data.scale == UI_SCALE_FAC && rect.xmin == data.region_rect.xmin &&
         rect.xmax == data.region_rect.xmax && rect.ymin == data.region_rect.ymin &&
         rect.ymax == data.region_rect.ymax &&
         hotbox_safe_bounds(*data.area, *data.region, data.scale) == data.safe_bounds;
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
    // Geometry changes invalidate the session, but its surviving region still needs repainting.
    if (source_containers_live(C, *data)) {
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

/* Only the main modeling menu expands modes; QWER and component mouse sessions retain
 * their existing mesh boundary at invoke. View actions still use their own narrow poll. */
static bool modeling_menu_poll(bContext *C)
{
  return STREQ(U.keyconfigstr, "AxisMeld_Maya_2026") && CTX_wm_area(C) &&
         CTX_wm_area(C)->spacetype == SPACE_VIEW3D && CTX_wm_region(C) &&
         CTX_wm_region(C)->regiontype == RGN_TYPE_WINDOW && CTX_wm_region_view3d(C) &&
         ELEM(CTX_data_mode_enum(C), CTX_MODE_OBJECT, CTX_MODE_EDIT_MESH,
              CTX_MODE_EDIT_CURVE, CTX_MODE_EDIT_SURFACE, CTX_MODE_EDIT_LATTICE);
}

static bool selected_modeling_context(bContext *C, const std::string_view root)
{
  const int domain = modeling_root_domain(root);
  Scene *scene = CTX_data_scene(C);
  if (domain < 0 || CTX_data_mode_enum(C) != CTX_MODE_EDIT_MESH || !scene ||
      !ID_IS_EDITABLE(scene))
  {
    return false;
  }
  constexpr int select_modes[] = {SCE_SELECT_VERTEX, SCE_SELECT_EDGE, SCE_SELECT_FACE};
  if (scene->toolsettings->selectmode != select_modes[domain]) {
    return false;  // Mixed modes and selection flush never determine the root.
  }
  ViewLayer *view_layer = CTX_data_view_layer(C);
  BKE_view_layer_synced_ensure(*CTX_data_main(C), scene, view_layer);
  const auto eligible = [&](const Base *base) {
    return base && base->object->type == OB_MESH && (base->object->mode & OB_MODE_EDIT) &&
           BASE_VISIBLE(CTX_wm_view3d(C), base) && ID_IS_EDITABLE(base->object) &&
           base->object->data && ID_IS_EDITABLE(base->object->data);
  };
  if (!eligible(CTX_data_active_base(C))) {
    return false;
  }
  constexpr BMIterType domains[] = {BM_VERTS_OF_MESH, BM_EDGES_OF_MESH, BM_FACES_OF_MESH};
  // This is an existence query over the editing set, not a sum across Mesh data.
  // Repeated shared Mesh data has the same answer; do not mutate ID tags to deduplicate it.
  for (const Base &base : *BKE_view_layer_object_bases_get(view_layer)) {
    if (!eligible(&base)) {
      continue;
    }
    BMEditMesh *em = BKE_editmesh_from_object(base.object);
    if (!em || !em->bm) {
      continue;
    }
    BMIter iter;
    BMElem *element;
    BM_ITER_MESH (element, &iter, em->bm, domains[domain]) {
      if (BM_elem_flag_test(element, BM_ELEM_SELECT) && !BM_elem_flag_test(element, BM_ELEM_HIDDEN)) {
        return true;
      }
    }
  }
  return false;
}

static bool modeling_tree_allowed(const MenuNode &node, const std::string_view root)
{
  if (node.kind == MenuKind::Setting ||
      (node.kind == MenuKind::Command && !modeling_root_allows_command(root, node.command)))
  {
    return false;
  }
  return std::all_of(node.children.begin(), node.children.end(), [&](const MenuNode &child) {
    return modeling_tree_allowed(child, root);
  });
}

static bool object_companion_tree_allowed(const MenuNode &node)
{
  if (node.kind == MenuKind::Setting ||
      (node.kind == MenuKind::Command && !object_menu_allows_command(node.id, node.command))) {
    return false;
  }
  if (node.kind == MenuKind::Menu &&
      (node.presentation != "list" ||
       (node.id != object_modeling_menu && node.id != "context.modeling_object_menu.mapping" &&
        node.id != "context.modeling_object_menu.booleans" &&
        node.id != "context.modeling_object_menu.polygon_display"))) {
    return false;
  }
  return std::all_of(node.children.begin(), node.children.end(), object_companion_tree_allowed);
}

static bool component_companion_tree_allowed(const MenuNode &node)
{
  if (node.kind == MenuKind::Setting ||
      (node.kind == MenuKind::Command && !component_menu_allows_command(node.id, node.command))) {
    return false;
  }
  return std::all_of(node.children.begin(), node.children.end(), component_companion_tree_allowed);
}

static bool modeling_companion_tree_allowed(const MenuNode &node, const std::string_view root)
{
  if (node.kind == MenuKind::Setting ||
      (node.kind == MenuKind::Command && !modeling_menu_allows_command(root, node.id, node.command))) {
    return false;
  }
  return std::all_of(node.children.begin(), node.children.end(), [&](const MenuNode &child) {
    return modeling_companion_tree_allowed(child, root);
  });
}

static bool creation_tree_allowed(const MenuNode &node)
{
  if (node.kind == MenuKind::Setting ||
      (node.kind == MenuKind::Command && !creation_allows_command(node.id, node.command))) {
    return false;
  }
  if (node.kind == MenuKind::Menu && node.id != creation_root &&
      (node.presentation != "list" ||
       (node.id != creation_menu && node.id != "context.create_menu.polygon_display_all"))) {
    return false;
  }
  return std::all_of(node.children.begin(), node.children.end(), creation_tree_allowed);
}

static void enable_preselected_object_command(MenuNode &node)
{
  if (!node.enabled) {
    if (node.command == "tool.object_mesh_poly_build") {
      node.reason = "Blender Poly Build adaptation; not Maya Append or Quad Draw algorithms";
    }
    else if (node.command == "tool.object_mesh_knife") {
      node.reason = "Blender Knife adaptation; Maya Multi-Cut behavior differs";
    }
    else if (node.command == "tool.object_mesh_loopcut") {
      node.reason = "Blender persistent Loop Cut tool";
    }
    else if (node.command == "tool.object_mesh_offset_loop") {
      node.reason = "Blender persistent Offset Edge Loop Cut tool";
    }
    else if (node.command.starts_with("object.modeling_smooth")) {
      node.reason = "Subdivision Surface modifier on the captured Mesh; original mesh data remains";
    }
    else if (node.command.starts_with("object.modeling_mirror")) {
      node.reason = "Mirror modifier on the captured Mesh; default X bisect and merge";
    }
    else if (node.command.starts_with("object.modeling_reduce")) {
      node.reason = "Decimate modifier on the captured Mesh; default ratio 50 percent";
    }
    else if (node.command.starts_with("object.modeling_remesh")) {
      node.reason = "Voxel Remesh modifier on the captured Mesh; original mesh data remains";
    }
    if (node.command.ends_with("_options")) { node.reason += "; confirmation applies parameters"; }
  }
  node.enabled = true;
}

static bool object_modeling_context(bContext *C, const HotboxData &data);

static bool source_context(bContext *C, const HotboxData &data)
{
  if (!source_live(C, data)) {
    return false;
  }
  return CTX_wm_window(C) == data.window && CTX_wm_area(C) == data.area &&
         CTX_wm_region(C) == data.region && CTX_data_mode_enum(C) == data.mode &&
         CTX_data_scene(C) && CTX_data_scene(C)->id.session_uid == data.scene_uid &&
         modeling_menu_poll(C) &&
         (!data.component_session || CTX_data_view_layer(C) == data.component_view_layer) &&
         (!data.modeling_session ||
          (CTX_data_view_layer(C) == data.component_view_layer &&
            (data.object_modeling_session ? object_modeling_context(C, data) :
                                            selected_modeling_context(C, data.tool_root))));
}

static wmOperatorStatus close_guard(bContext *C, wmOperator *op, const bool trigger_down)
{
  const auto &data = *static_cast<HotboxData *>(op->customdata);
  const int trigger = data.trigger;
  const bool direct = data.component_session || data.creation_session || data.modeling_session;
  const int mouse = direct ? 0 : data.active_mouse;
  const bool tool_session = !data.tool_root.empty() && !direct;
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

/* A held tool key owns multiple mouse strokes, just as Space owns multiple view strokes. */
static void rearm_tool(bContext *C, HotboxData &data)
{
  if (data.draw_handle) {
    ED_region_draw_cb_exit(data.region_type, data.draw_handle);
    data.draw_handle = nullptr;
  }
  data.tool_shown = false;
  data.active_mouse = 0;
  data.open_path.clear();
  data.return_path.clear();
  data.scroll_offsets.clear();
  data.center_return_armed = false;
  data.hover_id.clear();
  data.hover_depth = -1;
  data.pending_leaf.clear();
  data.candidate = HotboxAction::None;
  data.navigation_consumed = false;
  data.menu_entered_on_press = false;
  data.mouse_moved_since_press = false;
  if (source_live(C, data)) {
    ED_region_tag_redraw(data.region);
  }
}

static bool tool_command_rearms(const std::string_view command)
{
  // These adapters execute synchronously without changing the mode or viewport topology.
  // Keep the default close-before-dispatch policy for all other and future commands.
  constexpr std::string_view commands[] = {
      "orientation.move.world", "orientation.move.object", "orientation.move.normal",
      "orientation.move.view", "orientation.rotate.world", "orientation.rotate.object",
      "orientation.rotate.normal", "orientation.rotate.view", "orientation.rotate.gimbal",
      "orientation.scale.world", "orientation.scale.object", "orientation.scale.normal",
      "orientation.scale.view", "selection.marquee", "selection.lasso", "selection.paint",
      "selection.clear", "selection.select_all"};
  return std::find(std::begin(commands), std::end(commands), command) != std::end(commands);
}

static bool component_target_valid(bContext *C, const Base *base)
{
  return base && base->object->type == OB_MESH &&
         base->object->mode == OB_MODE_OBJECT && BASE_SELECTABLE(CTX_wm_view3d(C), base) &&
         ID_IS_EDITABLE(base->object) && base->object->data &&
         ID_IS_EDITABLE(base->object->data) && !ID_IS_OVERRIDE_LIBRARY(base->object) &&
         !ID_IS_OVERRIDE_LIBRARY(base->object->data);
}

static bool empty_creation_context(bContext *C)
{
  if (CTX_data_mode_enum(C) != CTX_MODE_OBJECT) {
    return false;
  }
  ViewLayer *view_layer = CTX_data_view_layer(C);
  BKE_view_layer_synced_ensure(*CTX_data_main(C), CTX_data_scene(C), view_layer);
  for (const Base &base : *BKE_view_layer_object_bases_get(view_layer)) {
    if (base.flag & BASE_SELECTED) {
      return false;
    }
  }
  return true;
}

/* Full base selection, including hidden bases: never silently trim an editing set. */
static bool object_selection_signature(
    bContext *C,
    std::vector<std::pair<unsigned int, unsigned int>> &selection,
    unsigned int &active_uid)
{
  if (CTX_data_mode_enum(C) != CTX_MODE_OBJECT || !ID_IS_EDITABLE(CTX_data_scene(C))) {
    return false;
  }
  ViewLayer *view_layer = CTX_data_view_layer(C);
  BKE_view_layer_synced_ensure(*CTX_data_main(C), CTX_data_scene(C), view_layer);
  Base *active = CTX_data_active_base(C);
  active_uid = active ? active->object->id.session_uid : 0;
  for (const Base &base : *BKE_view_layer_object_bases_get(view_layer)) {
    if (!(base.flag & BASE_SELECTED)) {
      continue;
    }
    if (!component_target_valid(C, &base) ||
        !BASE_VISIBLE(CTX_wm_view3d(C), &base))
    {
      return false;
    }
    selection.emplace_back(base.object->id.session_uid,
                           static_cast<ID *>(base.object->data)->session_uid);
  }
  std::sort(selection.begin(), selection.end());
  return selection.empty() ||
         (active && (active->flag & BASE_SELECTED) && component_target_valid(C, active));
}

static bool object_modeling_context(bContext *C, const HotboxData &data)
{
  std::vector<std::pair<unsigned int, unsigned int>> selection;
  unsigned int active_uid = 0;
  if (!object_selection_signature(C, selection, active_uid) ||
      selection != data.object_selection || active_uid != data.object_active_uid)
  {
    return false;
  }
  if (!data.object_target_uid) {
    return !selection.empty();
  }
  for (Base &base : *BKE_view_layer_object_bases_get(CTX_data_view_layer(C))) {
    if (base.object->id.session_uid == data.object_target_uid) {
      return component_target_valid(C, &base) && BASE_VISIBLE(CTX_wm_view3d(C), &base) &&
             static_cast<ID *>(base.object->data)->session_uid == data.object_target_data_uid;
    }
  }
  return false;
}

/* Capture the complete selection without filtering other object types or changing flags. */
static void component_selection_signature(
    bContext *C,
    std::vector<std::pair<unsigned int, unsigned int>> &selection,
    unsigned int &active_uid)
{
  ViewLayer *layer = CTX_data_view_layer(C);
  BKE_view_layer_synced_ensure(*CTX_data_main(C), CTX_data_scene(C), layer);
  const Base *active = CTX_data_active_base(C);
  active_uid = active ? active->object->id.session_uid : 0;
  for (const Base &base : *BKE_view_layer_object_bases_get(layer)) {
    if (base.flag & BASE_SELECTED) {
      selection.emplace_back(base.object->id.session_uid,
          base.object->data ? static_cast<ID *>(base.object->data)->session_uid : 0);
    }
  }
  std::sort(selection.begin(), selection.end());
}

static bool component_selected_context(bContext *C, const HotboxData &data)
{
  if (!data.component_selected_target || CTX_data_mode_enum(C) != CTX_MODE_OBJECT ||
      CTX_data_view_layer(C) != data.component_view_layer) {
    return false;
  }
  std::vector<std::pair<unsigned int, unsigned int>> selection;
  unsigned int active_uid = 0;
  component_selection_signature(C, selection, active_uid);
  Base *active = CTX_data_active_base(C);
  return active_uid == data.component_target_uid && active_uid == data.component_active_uid &&
         selection == data.component_selection && component_target_valid(C, active) &&
         (active->flag & BASE_SELECTED) && BASE_VISIBLE(CTX_wm_view3d(C), active) &&
         static_cast<ID *>(active->object->data)->session_uid == data.component_data_uid;
}

static wmOperatorStatus dispatch_object_modeling(bContext *C,
                                                const std::string &command,
                                                const unsigned int target_uid)
{
  const bool action = command.starts_with("object.modeling_");
  const char *operator_id = action ? "AXISMELD_OT_object_modeling_action" :
                                    "AXISMELD_OT_object_modeling_tool";
  if (!WM_operatortype_find(operator_id, true)) {
    return OPERATOR_CANCELLED;
  }
  PointerRNA props = WM_operator_properties_create(operator_id);
  const std::string target_text = target_uid ? std::to_string(target_uid) : "";
  RNA_string_set(&props, "command", command.c_str());
  RNA_string_set(&props, "target_uid", target_text.c_str());
  /* Direct outer UNDO operator keeps captured preselection inside the undo boundary. */
  const wmOperatorStatus result = WM_operator_name_call(
      C, operator_id, action && command.ends_with("_options") ? wm::OpCallContext::InvokeDefault :
                                                               wm::OpCallContext::ExecDefault,
      &props, nullptr);
  WM_operator_properties_free(&props);
  // The child dialog owns its own handler after the hotbox has been cleaned up.
  return (result & OPERATOR_RUNNING_MODAL) ? OPERATOR_FINISHED : result;
}

static bool component_command(const std::string &command)
{
  return command == "selection.vertex_mode" || command == "selection.edge_mode" ||
         command == "selection.face_mode" || command == "mode.object";
}

static void enable_component_target_commands(std::vector<MenuNode> &nodes)
{
  for (MenuNode &node : nodes) {
    if (node.id == "context.components") {
      for (MenuNode &child : node.children) {
        if (child.kind == MenuKind::Command && component_command(child.command)) {
          child.enabled = true;
          child.reason.clear();
        }
      }
      return;
    }
    enable_component_target_commands(node.children);
  }
}

static bool commit_component_target(bContext *C, const HotboxData &data)
{
  if (!data.component_target_uid) {
    return true;  // Edit Mesh keeps its existing native editing set.
  }
  ViewLayer *view_layer = CTX_data_view_layer(C);
  if (view_layer != data.component_view_layer) {
    return false;
  }
  BKE_view_layer_synced_ensure(*CTX_data_main(C), CTX_data_scene(C), view_layer);
  Base *target = nullptr;
  for (Base &base : *BKE_view_layer_object_bases_get(view_layer)) {
    if (base.object->id.session_uid == data.component_target_uid) {
      target = &base;
      break;
    }
  }
  if (!component_target_valid(C, target)) {
    return false;
  }
  if (!(target->flag & BASE_SELECTED)) {
    for (Base &base : *BKE_view_layer_object_bases_get(view_layer)) {
      ed::object::base_select(&base, ed::object::BA_DESELECT);
    }
    ed::object::base_select(target, ed::object::BA_SELECT);
  }
  ed::object::base_activate(C, target);
  DEG_id_tag_update(&CTX_data_scene(C)->id, ID_RECALC_SELECT);
  WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, CTX_data_scene(C));
  ED_outliner_select_sync_from_object_tag(C);
  return true;
}

static wmOperatorStatus submit(bContext *C, wmOperator *op, const MenuNode &leaf)
{
  auto &data = *static_cast<HotboxData *>(op->customdata);
  // Strings must outlive cleanup and Python rebuilding its catalog/context.
  const std::string command = leaf.command, value = leaf.value;
  const bool setting = leaf.kind == MenuKind::Setting;
  if (data.modeling_session) {
    const bool companion = data.object_modeling_session ? object_menu_allows_command(leaf.id, command) :
        modeling_menu_allows_command(data.tool_root, leaf.id, command);
    if (setting || (!companion && !modeling_root_allows_command(data.tool_root, command)) ||
        !source_context(C, data))
    {
      cleanup(C, op);
      return OPERATOR_CANCELLED;
    }
    // Only the owned trigger release submits. Close before a native modal or persistent
    // tool starts, leaving its next stroke and its own undo transaction unguarded.
    if (data.object_modeling_session) {
      const unsigned int target_uid = data.object_target_uid;
      if (companion && !object_menu_target_aware(command)) {
        if (target_uid) {
          cleanup(C, op);
          return OPERATOR_CANCELLED;
        }
        cleanup(C, op);
        const auto result = axismeld_hotbox_dispatch(C, command.c_str());
        return (result & OPERATOR_RUNNING_MODAL) ? OPERATOR_FINISHED : result;
      }
      cleanup(C, op);
      return dispatch_object_modeling(C, command, target_uid);
    }
    cleanup(C, op);
    axismeld_hotbox_dispatch(C, command.c_str());
    return OPERATOR_FINISHED;
  }
  if (data.creation_session) {
    if (setting || !creation_allows_command(leaf.id, command) || !empty_creation_context(C)) {
      cleanup(C, op);
      return OPERATOR_CANCELLED;
    }
    // The owned trigger release already arrived. No release guard remains to create.
    cleanup(C, op);
    const auto result = axismeld_hotbox_dispatch(C, command.c_str());
    return (result & OPERATOR_RUNNING_MODAL) ? OPERATOR_FINISHED : result;
  }
  if (data.component_session) {
    if (component_menu_allows_command(leaf.id, command)) {
      if (setting || !source_context(C, data) ||
          (!component_menu_selection_wide(command) && !component_selected_context(C, data))) {
        cleanup(C, op);
        return OPERATOR_CANCELLED;
      }
      // Companion selection operations never preselect the captured pointer target.
      cleanup(C, op);
      const auto result = axismeld_hotbox_dispatch(C, command.c_str());
      return (result & OPERATOR_RUNNING_MODAL) ? OPERATOR_FINISHED : result;
    }
    if (!component_command(command) || !commit_component_target(C, data)) {
      cleanup(C, op);
      return OPERATOR_CANCELLED;
    }
    cleanup(C, op);
    axismeld_hotbox_dispatch(C, command.c_str());
    return OPERATOR_FINISHED;
  }
  if (!data.tool_root.empty() && !setting && tool_command_rearms(command)) {
    rearm_tool(C, data);
    const wmOperatorStatus result = axismeld_hotbox_dispatch(C, command.c_str());
    // An armed, hidden tool has no open path to lay out. The next mouse press
    // refreshes both its capabilities and geometry at the new gesture origin.
    if ((result != OPERATOR_FINISHED && result != OPERATOR_CANCELLED) ||
        !source_context(C, data))
    {
      return close_guard(C, op, true);
    }
    return OPERATOR_RUNNING_MODAL;
  }
  if (!setting && hotbox_command_closes(command)) {
    const int trigger = data.trigger, mouse = data.component_session ? 0 : data.active_mouse;
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
  if (rect.companion) {
    if (data.companion_path.empty()) { data.companion_path = {rect.owner}; }
    const auto owner = std::find(data.companion_path.begin(), data.companion_path.end(), rect.owner);
    if (owner == data.companion_path.end()) { return; }
    const size_t index = size_t(owner - data.companion_path.begin()) + 1;
    if (index < data.companion_path.size() && data.companion_path[index] == rect.id) { return; }
    data.companion_path.resize(index);
    data.companion_path.push_back(rect.id);
    hotbox_layout(data);
    return;
  }
  if (const auto companion = companion_root(rect.id); !companion.empty() &&
      (data.companion_path.empty() || data.companion_path.front() != companion)) {
    data.companion_path = {std::string(companion)};
  }
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
  if (const auto root = companion_owner(owner); !root.empty()) {
    if (data.companion_path.empty() || data.companion_path.front() != root) {
      data.companion_path = {std::string(root)};
    }
    const auto found = std::find(data.companion_path.begin(), data.companion_path.end(), owner);
    if (found != data.companion_path.end()) { data.companion_path.erase(found + 1, data.companion_path.end()); }
    if (const MenuNode *node = hotbox_find_node(data.snapshot.menus, owner)) {
      data.scroll_offsets[owner] = menu_scroll_offset_transition(
          data.menu_layout, owner, data.scroll_offsets[owner], delta, int(node->children.size()));
      hotbox_layout(data);
    }
    return;
  }
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

/* The companion shares the original held mouse; paging never creates another owner. */
static bool companion_navigation(HotboxData &data, const wmEvent *event)
{
  if ((data.modeling_session || data.creation_session || data.component_session) && event->modifier != data.required_modifiers) { return false; }
  const bool motion = ISMOUSE_MOTION(event->type);
  const bool wheel = ELEM(event->type, WHEELUPMOUSE, WHEELDOWNMOUSE);
  if (motion || wheel) {
    data.pointer_position[0] = (event->xy[0] - data.region->winrct.xmin) / data.scale;
    data.pointer_position[1] = (event->xy[1] - data.region->winrct.ymin) / data.scale;
  }
  const auto *hit = hit_menu_rect(data.menu_layout, data.pointer_position[0], data.pointer_position[1]);
  if (!hit || !hit->companion || hit->owner.empty()) {
    if (motion) { data.companion_scroll_hover.clear(); }
    return false;
  }
  const MenuRect rect = *hit;
  if (wheel) {
    data.tap_eligible = false;
    scroll_owner(data, rect.owner, event->type == WHEELUPMOUSE ? -1 : 1);
    data.companion_scroll_hover.clear();
    data.hover_id.clear();
    ED_region_tag_redraw(data.region);
    return true;
  }
  if ((motion || ISTIMER(event->type)) && rect.id.starts_with("@scroll:")) {
    data.tap_eligible = false;
    const double now = BLI_time_now_seconds();
    if (rect.interactive && (data.companion_scroll_hover != rect.id || now >= data.companion_scroll_next)) {
      scroll_control(data, rect.id);
      data.companion_scroll_next = now + 0.35;
    }
    data.companion_scroll_hover = rect.id;
    data.hover_id = rect.id;
    data.hover_depth = rect.depth;
    ED_region_tag_redraw(data.region);
    return true;
  }
  if (motion) {
    data.companion_scroll_hover.clear();
    const auto *node = hotbox_find_node(data.snapshot.menus, rect.id);
    const auto owner = std::find(data.companion_path.begin(), data.companion_path.end(), rect.owner);
    if (node && node->kind != MenuKind::Menu && owner != data.companion_path.end() &&
        owner + 1 != data.companion_path.end()) {
      data.companion_path.erase(owner + 1, data.companion_path.end());
      hotbox_layout(data);
    }
  }
  return false;
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
  const std::string tool_root = RNA_string_get(op->ptr, "tool_menu");
  if (!tool_root.empty() && !axismeld_view_context_poll(C)) {
    return OPERATOR_PASS_THROUGH;
  }
  const bool component = tool_root == "context.components";
  const bool creation = tool_root == "context.create";
  const bool object_modeling = tool_root == object_modeling_root;
  const bool modeling = object_modeling || modeling_root_domain(tool_root) >= 0;
  const bool direct = component || creation || modeling;
  if ((!ISKEYBOARD(event->type) &&
       !(direct && ELEM(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE))) ||
      event->val != KM_PRESS || (event->flag & WM_EVENT_IS_REPEAT) ||
      (component && event->modifier) ||
      ((creation || modeling) && (event->modifier & ~(KM_SHIFT | KM_CTRL)))) {
    return OPERATOR_PASS_THROUGH;
  }
  wmWindow *window = CTX_wm_window(C);
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
    if ((tool_root != "tools.select" && tool_root != "tools.move" && tool_root != "tools.rotate" &&
         tool_root != "tools.scale" && !direct) ||
        !root || root->kind != MenuKind::Menu || !root->enabled || root->presentation != "radial")
    {
      return OPERATOR_CANCELLED;
    }
    if (creation && (!creation_tree_allowed(*root) ||
        (hotbox_find_node(snapshot.menus, creation_menu) &&
         !creation_tree_allowed(*hotbox_find_node(snapshot.menus, creation_menu))))) {
      return OPERATOR_CANCELLED;
    }
    if (modeling && !modeling_tree_allowed(*root, tool_root)) {
      return OPERATOR_CANCELLED;
    }
  }
  if (component) {
    if (const auto *menu = hotbox_find_node(snapshot.menus, "context.component_menu")) {
      if (!component_companion_tree_allowed(*menu)) { return OPERATOR_CANCELLED; }
    }
  }
  if (modeling && !object_modeling) {
    if (const auto *menu = hotbox_find_node(snapshot.menus, companion_root(tool_root))) {
      if (!modeling_companion_tree_allowed(*menu, tool_root)) { return OPERATOR_CANCELLED; }
    }
  }
  if (modeling && !object_modeling && !selected_modeling_context(C, tool_root)) {
    return OPERATOR_PASS_THROUGH;
  }
  unsigned int target_uid = 0;
  unsigned int object_target_uid = 0, object_target_data_uid = 0, object_active_uid = 0;
  std::vector<std::pair<unsigned int, unsigned int>> object_selection;
  if (object_modeling) {
    if (const auto *companion = hotbox_find_node(snapshot.menus, object_modeling_menu)) {
      if (!object_companion_tree_allowed(*companion)) { return OPERATOR_CANCELLED; }
    }
    if (!object_selection_signature(C, object_selection, object_active_uid)) {
      return OPERATOR_PASS_THROUGH;
    }
    if (object_selection.empty()) {
      if (!ELEM(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)) {
        return OPERATOR_PASS_THROUGH;
      }
      const int mval[2] = {event->xy[0] - CTX_wm_region(C)->winrct.xmin,
                           event->xy[1] - CTX_wm_region(C)->winrct.ymin};
      Base *target = ED_view3d_give_nearest_selectable_base_under_cursor(C, mval);
      if (!component_target_valid(C, target) || !BASE_VISIBLE(CTX_wm_view3d(C), target)) {
        return OPERATOR_PASS_THROUGH;
      }
      object_target_uid = target->object->id.session_uid;
      object_target_data_uid = static_cast<ID *>(target->object->data)->session_uid;
    }
    /* Only these three leaves are enabled for a validated future target, never arbitrary mesh ops. */
    const auto enable = [&](auto &&self, std::vector<MenuNode> &nodes) -> void {
      for (MenuNode &node : nodes) {
        if (node.id == object_modeling_root) {
          for (MenuNode &child : node.children) {
            if (child.kind == MenuKind::Command &&
                modeling_root_allows_command(object_modeling_root, child.command))
            {
              if (object_target_uid) { enable_preselected_object_command(child); }
            }
          }
          return;
        }
        self(self, node.children);
      }
    };
    enable(enable, snapshot.menus);
    const auto enable_companion = [&](auto &&self, std::vector<MenuNode> &nodes) -> void {
      for (auto &node : nodes) {
        if (object_target_uid && node.kind == MenuKind::Command &&
            object_menu_allows_command(node.id, node.command)) {
          if (object_menu_target_aware(node.command)) {
            enable_preselected_object_command(node);
          }
          else {
            node.enabled = false;
            node.reason = "Requires an existing Mesh selection; pointer preselection is not supported for this action";
          }
        }
        self(self, node.children);
      }
    };
    enable_companion(enable_companion, snapshot.menus);
  }
  if (creation) {
    if (!empty_creation_context(C)) {
      return OPERATOR_PASS_THROUGH;
    }
    if (ELEM(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)) {
      const int mval[2] = {event->xy[0] - CTX_wm_region(C)->winrct.xmin,
                           event->xy[1] - CTX_wm_region(C)->winrct.ymin};
      if (ED_view3d_give_nearest_selectable_base_under_cursor(C, mval)) {
        return OPERATOR_PASS_THROUGH;
      }
    }
  }
  if (component && CTX_data_mode_enum(C) == CTX_MODE_OBJECT) {
    Base *target = nullptr;
    if (ELEM(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)) {
      const int mval[2] = {event->xy[0] - CTX_wm_region(C)->winrct.xmin,
                           event->xy[1] - CTX_wm_region(C)->winrct.ymin};
      target = ED_view3d_give_nearest_selectable_base_under_cursor(C, mval);
      if (target && !component_target_valid(C, target)) {
        return OPERATOR_PASS_THROUGH;
      }
    }
    if (!target) {
      target = CTX_data_active_base(C);
      if (!component_target_valid(C, target) || !(target->flag & BASE_SELECTED)) {
        return OPERATOR_PASS_THROUGH;
      }
    }
    target_uid = target->object->id.session_uid;
    enable_component_target_commands(snapshot.menus);
  }
  auto *data = new HotboxData();
  data->component_target_uid = target_uid;
  data->component_view_layer = CTX_data_view_layer(C);
  if (component) {
    Base *target = nullptr;
    BKE_view_layer_synced_ensure(*CTX_data_main(C), CTX_data_scene(C), data->component_view_layer);
    for (Base &base : *BKE_view_layer_object_bases_get(data->component_view_layer)) {
      if (base.object->id.session_uid == target_uid) { target = &base; break; }
    }
    if (!target && CTX_data_mode_enum(C) == CTX_MODE_EDIT_MESH) { target = CTX_data_active_base(C); }
    if (CTX_data_mode_enum(C) == CTX_MODE_OBJECT) {
      component_selection_signature(C, data->component_selection, data->component_active_uid);
      data->component_selected_target = target && target == CTX_data_active_base(C) &&
                                        (target->flag & BASE_SELECTED);
      data->component_data_uid = target && target->object->data ?
          static_cast<ID *>(target->object->data)->session_uid : 0;
    }
    const auto prepare = [&](auto &&self, std::vector<MenuNode> &nodes) -> void {
      for (MenuNode &node : nodes) {
        if (node.id == "context.component_menu.object" && target) {
          // ID names are already bounded UTF-8. Replace ASCII controls without
          // truncating or modifying any byte of a multibyte character.
          node.label = std::string(target->object->id.name + 2);
          for (char &byte : node.label) {
            if (static_cast<unsigned char>(byte) < 32 || byte == 127) { byte = ' '; }
          }
          node.label += "...";
        }
        if (node.kind == MenuKind::Command && component_menu_allows_command(node.id, node.command) &&
            !component_menu_selection_wide(node.command) && !data->component_selected_target) {
          node.enabled = false;
          node.reason = "Requires the captured target to be the selected active Object; selection is not changed on open";
        }
        self(self, node.children);
      }
    };
    prepare(prepare, snapshot.menus);
  }
  data->tool_root = tool_root;
  data->component_session = component;
  data->creation_session = creation;
  data->modeling_session = modeling;
  data->object_modeling_session = object_modeling;
  if (const auto companion = companion_root(tool_root); !companion.empty()) {
    data->companion_path = {std::string(companion)};
  }
  data->object_target_uid = object_target_uid;
  data->object_target_data_uid = object_target_data_uid;
  data->object_active_uid = object_active_uid;
  data->object_selection = std::move(object_selection);
  data->required_modifiers = creation || modeling ? event->modifier : wmEventModifierFlag(0);
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
  data->safe_bounds = hotbox_safe_bounds(*data->area, *data->region, data->scale);
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
  if (direct) {
    data->tool_shown = true;
    data->active_mouse = event->type;
    data->origin[0] = data->press_position[0] = data->pointer_position[0] = data->center[0];
    data->origin[1] = data->press_position[1] = data->pointer_position[1] = data->center[1];
    data->open_path = {tool_root};
    hotbox_layout(*data);
    if (!data->menu_layout.supported) {
      cleanup(C, op);
      return OPERATOR_PASS_THROUGH;
    }
    data->draw_handle = ED_region_draw_cb_activate(
        data->region_type, draw, data, REGION_DRAW_POST_PIXEL);
  }
  data->timer = WM_event_timer_add(CTX_wm_manager(C), window, TIMER, .02);
  WM_event_add_modal_handler(C, op);
  ED_region_tag_redraw(data->region);
  return OPERATOR_RUNNING_MODAL;
}

static bool retract_at_center(HotboxData &data, const float x, const float y, const bool motion)
{
  if (data.return_path != data.open_path) {
    data.return_path = data.open_path;
    data.center_return_armed = false;
  }
  std::string target = menu_return_target(data.menu_layout, x, y);
  const MenuNode *current_owner = data.open_path.empty() ? nullptr :
                                  hotbox_find_node(data.snapshot.menus, data.open_path.back());
  if (current_owner && current_owner->presentation == "radial" && target != current_owner->id) {
    // Hidden ancestor centers can lie in the current ring's extended direction regions.
    // Only returning to this ring's own center retracts it; the real origin cancels below.
    target.clear();
  }
  if (data.menu_layout.return_regions.size() > 1 && !data.open_path.empty()) {
    const MenuRect &current = data.menu_layout.return_regions.back();
    if (current.id == data.open_path.back() && data.open_path.size() > 1) {
      const bool inside = x >= current.x && x < current.x + current.width && y >= current.y &&
                          y < current.y + current.height;
      if (motion && !inside) {
        data.center_return_armed = true;
      }
      // The opening stroke arrives at the child's center. Only a subsequent
      // outward-and-back stroke may retract it. Visible child targets still win.
      if (target == current.id) {
        target = data.center_return_armed ? data.open_path[data.open_path.size() - 2] : "";
      }
    }
  }
  const float *stroke_origin = !data.tool_root.empty() || data.marking ? data.origin :
                                                                       data.press_position;
  const float dx = x - stroke_origin[0], dy = y - stroke_origin[1];
  if (dx * dx + dy * dy <= 12 * 12) {
    if (!data.tool_root.empty()) {
      target = data.tool_root;
    }
    else if (data.marking) {
      target = "views";
    }
  }
  const auto begin = data.open_path.begin() +
                     (!data.open_path.empty() && data.open_path.front() == "center" ? 1 : 0);
  const auto owner = std::find(begin, data.open_path.end(), target);
  if (owner == data.open_path.end() || owner + 1 == data.open_path.end()) {
    return false;
  }
  data.open_path.erase(owner + 1, data.open_path.end());
  data.return_path.clear();
  data.center_return_armed = false;
  data.hover_id.clear();
  data.hover_depth = -1;
  data.pending_leaf.clear();
  data.candidate = HotboxAction::None;
  hotbox_layout(data);
  return true;
}

static const MenuNode *active_radial_menu(const HotboxData &data)
{
  const MenuNode *owner = data.open_path.empty() ? nullptr :
                         hotbox_find_node(data.snapshot.menus, data.open_path.back());
  return owner && owner->presentation == "radial" ? owner : nullptr;
}

static const MenuRect *radial_hover(const HotboxData &data, const float x, const float y)
{
  const MenuNode *owner = active_radial_menu(data);
  return owner ? hit_marking_menu_rect(data.menu_layout, owner->id, x, y) : nullptr;
}

static wmOperatorStatus tool_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  auto &data = *static_cast<HotboxData *>(op->customdata);
  const float x = (event->xy[0] - data.region->winrct.xmin) / data.scale;
  const float y = (event->xy[1] - data.region->winrct.ymin) / data.scale;
  const bool direct = data.component_session || data.creation_session || data.modeling_session;
  const int owned = direct ? data.trigger : LEFTMOUSE;
  if (event->modifier != data.required_modifiers ||
      (!ISTIMER(event->type) && !ISMOUSE_MOTION(event->type) && event->type != owned))
  {
    // A modified release still relinquishes its owner; never wait for a second release.
    if (event->type == owned && event->val == KM_RELEASE) {
      data.active_mouse = 0;
    }
    close_guard(C, op, !(event->type == data.trigger && event->val == KM_RELEASE));
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
    if (!refresh(C, data)) {
      return close_guard(C, op, true);
    }
    data.draw_handle = ED_region_draw_cb_activate(
        data.region_type, draw, &data, REGION_DRAW_POST_PIXEL);
    ED_region_tag_redraw(data.region);
    return OPERATOR_RUNNING_MODAL;
  }
  if (ISMOUSE_MOTION(event->type) || event->type == owned) {
    data.pointer_position[0] = x;
    data.pointer_position[1] = y;
    const bool at_origin = (x - data.origin[0]) * (x - data.origin[0]) +
                               (y - data.origin[1]) * (y - data.origin[1]) <=
                           12 * 12;
    const bool returned = retract_at_center(data, x, y, ISMOUSE_MOTION(event->type));
    // Edge clamping may move a button under the real press origin. The dead zone wins
    // over all menu hit testing, including reopening a child after returning to cancel it.
    const MenuRect *hover = at_origin || returned ? nullptr :
                                                    hit_menu_rect(data.menu_layout, x, y);
    if (!hover && !at_origin && !returned) {
      hover = radial_hover(data, x, y);
    }
    const MenuRect rect = hover ? *hover : MenuRect{};
    data.hover_id = hover ? rect.id : "";
    data.hover_depth = hover ? rect.depth : -1;
    const MenuNode *node = hotbox_find_node(data.snapshot.menus, data.hover_id);
    if (ISMOUSE_MOTION(event->type) && node && node->enabled && node->kind == MenuKind::Menu) {
      open_menu(data, rect);
    }
    if (event->type == owned && event->val == KM_RELEASE) {
      data.active_mouse = 0;
      if (node && node->enabled && ELEM(node->kind, MenuKind::Command, MenuKind::Setting)) {
        return submit(C, op, *node);
      }
      if (!direct) {
        rearm_tool(C, data);
        return OPERATOR_RUNNING_MODAL;
      }
      return close_guard(C, op, false);
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
  if (event->type == WINDEACTIVATE || event->type == EVT_ESCKEY || !source_context(C, data) ||
      (data.creation_session && !empty_creation_context(C))) {
    if (event->type == data.active_mouse && event->val == KM_RELEASE) {
      data.active_mouse = 0;
    }
    return close_guard(C, op, !(event->type == data.trigger && event->val == KM_RELEASE));
  }
  data.state.advance(BLI_time_now_seconds());
  if (companion_navigation(data, event)) { return OPERATOR_RUNNING_MODAL; }
  if (event->type == data.trigger && !data.component_session && !data.creation_session &&
      !data.modeling_session) {
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
  const bool returned = data.active_mouse &&
                        (ISMOUSE_MOTION(event->type) ||
                         (event->type == data.active_mouse && event->val == KM_RELEASE)) &&
                        retract_at_center(data, x, y, ISMOUSE_MOTION(event->type));
  const bool radial_origin = data.active_mouse && active_radial_menu(data) &&
                             (x - data.press_position[0]) * (x - data.press_position[0]) +
                                     (y - data.press_position[1]) * (y - data.press_position[1]) <=
                                 12 * 12;
  const MenuRect *hover = returned || radial_origin ? nullptr :
                                                    hit_menu_rect(data.menu_layout, x, y);
  if (!hover && data.active_mouse && !returned && !radial_origin) {
    hover = radial_hover(data, x, y);
  }
  // Copy before open_menu/scroll can rebuild the owning rect vector.
  const MenuRect rect = hover ? *hover : MenuRect{};
  data.hover_id = hover ? rect.id : "";
  data.hover_depth = hover ? rect.depth : -1;
  const std::string item = hover && hover->interactive ? hover->id : "";
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
                              data.snapshot.style == "center" && !hover &&
                              x >= data.safe_bounds.xmin && x < data.safe_bounds.xmax &&
                              y >= data.safe_bounds.ymin && y < data.safe_bounds.ymax;
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
      // Short blind strokes retain cardinal gestures. Outside the central hole, use
      // displayed geometry instead of unrelated 45-degree sectors. Style still wins.
      const std::array<float, 2> gesture_origin = {data.origin[0], data.origin[1]};
      const MenuRect *nearest = !returned && !hover && data.open_path.size() == 2 ?
                                    nearest_marking_rect(data.menu_layout, x, y, &gesture_origin) :
                                    nullptr;
      data.candidate = returned || hover || data.open_path.size() > 2 ?
                           HotboxAction::None :
                           hotbox_direction(dx, dy, 12);
      data.pending_leaf = dx * dx + dy * dy <= 12 * 12 ? "" :
                          node && (rect.direction_label || node->kind == MenuKind::Setting) ?
                                                         item :
                          nearest ? (nearest->interactive ? nearest->id : "") :
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
  ot->poll = modeling_menu_poll;
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
  prop = RNA_def_string(ot->srna,
                        "tool_menu",
                        nullptr,
                        0,
                        "Tool Menu",
                        "Registered tool root, armed until left mouse press");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}
}  // namespace blender

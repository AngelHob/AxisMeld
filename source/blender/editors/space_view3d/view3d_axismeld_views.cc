/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <array>
#include <cstdint>
#include <cstring>
#include <vector>

#include "BKE_context.hh"
#include "BKE_report.hh"
#include "BLI_listbase.hh"
#include "BLI_math_rotation_c.hh"
#include "BLI_math_vector_c.hh"
#include "BLI_string.hh"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "ED_screen.hh"
#include "ED_view3d.hh"
#include "MEM_guardedalloc.h"
#include "RNA_access.hh"
#include "RNA_define.hh"
#include "WM_api.hh"
#include "WM_types.hh"

#include "view3d_axismeld.hh"
#include "view3d_intern.hh"
#include "view3d_navigate.hh"

namespace blender {
namespace {
using axismeld::HotboxAction;

/* Numeric clipping state only. RegionView3D owns clipbb; never retain its pointer. */
struct ViewClipping {
  bool enabled = false;
  bool has_bounds = false;
  float planes[6][4] = {};
  float local_planes[6][4] = {};
  float bounds[8][3] = {};

  void capture(const RegionView3D &rv)
  {
    enabled = (rv.rflag & RV3D_CLIPPING) != 0;
    has_bounds = rv.clipbb != nullptr;
    memcpy(planes, rv.clip, sizeof(planes));
    memcpy(local_planes, rv.clip_local, sizeof(local_planes));
    if (has_bounds) {
      memcpy(bounds, rv.clipbb->vec, sizeof(bounds));
    }
  }

  void apply(RegionView3D &rv) const
  {
    if (enabled) {
      rv.rflag |= RV3D_CLIPPING;
    }
    else {
      rv.rflag &= ~RV3D_CLIPPING;
    }
    memcpy(rv.clip, planes, sizeof(planes));
    memcpy(rv.clip_local, local_planes, sizeof(local_planes));
    if (has_bounds) {
      if (!rv.clipbb) {
        rv.clipbb = MEM_new<BoundBox>("AxisMeld view clipping");
      }
      memcpy(rv.clipbb->vec, bounds, sizeof(bounds));
    }
    else {
      MEM_SAFE_DELETE(rv.clipbb);
    }
  }
};

/* Deliberately not RegionView3D: that struct owns render, smooth-view and local-view pointers. */
struct ViewPose {
  ViewClipping clipping;
  float quat[4], ofs[3], dist;
  float last_quat[4], ofs_lock[2];
  eRegionView3D_Persp persp, last_persp;
  eRegionView3D_View view, last_view;
  eRegionView3D_ViewAxisRoll roll, last_roll;
  eRegionView3D_ViewLock lock, runtime_lock;
  eRegionView3D_ViewLockQuad quad_lock;

  void capture(const RegionView3D &rv)
  {
    clipping.capture(rv);
    copy_qt_qt(quat, rv.viewquat);
    copy_v3_v3(ofs, rv.ofs);
    dist = rv.dist;
    copy_qt_qt(last_quat, rv.lviewquat);
    copy_v2_v2(ofs_lock, rv.ofs_lock);
    persp = rv.persp;
    last_persp = rv.lpersp;
    view = rv.view;
    last_view = rv.lview;
    roll = rv.view_axis_roll;
    last_roll = rv.lview_axis_roll;
    lock = rv.viewlock;
    runtime_lock = rv.runtime_viewlock;
    quad_lock = rv.viewlock_quad;
  }
  void apply(RegionView3D &rv) const
  {
    clipping.apply(rv);
    copy_qt_qt(rv.viewquat, quat);
    copy_v3_v3(rv.ofs, ofs);
    rv.dist = dist;
    copy_qt_qt(rv.lviewquat, last_quat);
    copy_v2_v2(rv.ofs_lock, ofs_lock);
    rv.persp = persp;
    rv.lpersp = last_persp;
    rv.view = view;
    rv.lview = last_view;
    rv.view_axis_roll = roll;
    rv.lview_axis_roll = last_roll;
    rv.viewlock = lock;
    rv.runtime_viewlock = runtime_lock;
    rv.viewlock_quad = quad_lock;
    rv.rflag |= RV3D_GPULIGHT_UPDATE;
  }
  void axis(const eRegionView3D_View direction)
  {
    view = direction;
    roll = RV3D_VIEW_AXIS_ROLL_0;
    persp = RV3D_ORTHO;
    ED_view3d_quat_from_axis_view(view, roll, quat);
  }
};

struct ViewSlot {
  ViewPose pose{};
  ViewPose perspective{};
  /* A quad-derived clip is suspended in single view. User border clipping there is independent. */
  ViewClipping single_clipping;
  bool has_perspective = false;
  void capture(const RegionView3D &rv, const bool preserve_quad_locks)
  {
    const auto lock = pose.lock;
    const auto runtime_lock = pose.runtime_lock;
    const auto quad_lock = pose.quad_lock;
    const bool had_quad_clip = ((lock | runtime_lock) & RV3D_BOXCLIP) != 0;
    const ViewClipping quad_clipping = pose.clipping;
    pose.capture(rv);
    if (preserve_quad_locks && had_quad_clip) {
      single_clipping = pose.clipping;
      pose.clipping = quad_clipping;
    }
    else if ((RV3D_LOCK_FLAGS(&rv) & RV3D_BOXCLIP) == 0) {
      single_clipping = pose.clipping;
    }
    if (preserve_quad_locks) {
      pose.lock = lock;
      pose.runtime_lock = runtime_lock;
      pose.quad_lock = quad_lock;
    }
    if (rv.persp == RV3D_PERSP) {
      perspective.capture(rv);
      has_perspective = true;
    }
  }
};

struct ViewCache {
  /* Integer identities are compared only; no cached region or Scene is dereferenced. */
  unsigned int scene_uid = 0;
  std::vector<uintptr_t> topology;
  std::array<ViewSlot, 4> slots;
  int selected = 3;
  bool initialized = false;
};

static std::vector<ARegion *> window_regions(ScrArea *area)
{
  std::vector<ARegion *> regions;
  for (ARegion &region : area->regionbase) {
    if (region.regiontype == RGN_TYPE_WINDOW && region.regiondata) {
      regions.push_back(&region);
    }
  }
  return regions;
}

static std::vector<uintptr_t> topology(const ScrArea *area)
{
  std::vector<uintptr_t> signature;
  for (const ARegion &region : area->regionbase) {
    signature.push_back(uintptr_t(&region));
    signature.push_back(uintptr_t(region.regiondata));
    signature.push_back(uintptr_t(region.alignment));
    signature.push_back(uintptr_t(region.regiontype));
  }
  return signature;
}

static void refresh_quad_clipping(bContext *C, ViewCache &cache, const bool layout_changed)
{
  ScrArea *area = CTX_wm_area(C);
  const auto regions = window_regions(area);
  if (regions.size() != 4) {
    return;
  }
  if (layout_changed) {
    /* Fresh quad regions need default gizmo/tool handlers before editor keymaps.
     * The resize-only initializer installs editor handlers first, letting ordinary
     * selection/translation swallow axis clicks and drags in the new panes. Full
     * initialization also obtains the rectangles required by clipping below. */
    ED_area_init(C, CTX_wm_window(C), area);
  }
  /* Unlike quadview_update/boxview_sync, this does not overwrite other slots' poses.
   * Native clipping writes only BOXCLIP panes; independent border clipping is left intact. */
  view3d_boxview_clip(area);
  for (int i = 0; i < 4; i++) {
    cache.slots[i].pose.clipping.capture(*static_cast<RegionView3D *>(regions[i]->regiondata));
  }
}

static ViewCache &cache_ensure(bContext *C, View3D *v3d, ScrArea *area)
{
  auto *cache = static_cast<ViewCache *>(v3d->runtime.axismeld_view_cache);
  const auto signature = topology(area);
  const unsigned int scene_uid = CTX_data_scene(C)->id.session_uid;
  if (cache && (cache->scene_uid != scene_uid || cache->topology != signature)) {
    delete cache;
    cache = nullptr;
  }
  if (!cache) {
    cache = new ViewCache();
    cache->scene_uid = scene_uid;
    cache->topology = signature;
    v3d->runtime.axismeld_view_cache = cache;
    v3d->runtime.axismeld_view_cache_free = axismeld_view_cache_free;
  }
  return *cache;
}

static bool supported(bContext *C, wmOperator *op)
{
  View3D *v3d = CTX_wm_view3d(C);
  RegionView3D *rv = CTX_wm_region_view3d(C);
  if (v3d->localvd || rv->localvd || rv->persp == RV3D_CAMOB || (v3d->flag2 & V3D_LOCK_CAMERA) ||
      (v3d->flag & (V3D_XR_SESSION_MIRROR | V3D_XR_SESSION_SURFACE)) ||
      (v3d->runtime.flag & V3D_RUNTIME_XR_SESSION_ROOT))
  {
    BKE_report(op->reports,
               RPT_WARNING,
               "AxisMeld views do not support Local View, camera-locked views or XR");
    return false;
  }
  return true;
}

static bool toggle_quad(bContext *C, ViewCache &cache)
{
  ScrArea *area = CTX_wm_area(C);
  View3D *v3d = CTX_wm_view3d(C);
  ARegion *source = CTX_wm_region(C);
  auto regions = window_regions(area);
  if (regions.size() != 1 && regions.size() != 4) {
    return false;
  }
  for (ARegion *region : regions) {
    ED_view3d_smooth_view_force_finish(C, v3d, region);
  }
  if (regions.size() == 4) {
    for (int i = 0; i < 4; i++) {
      cache.slots[i].capture(*static_cast<RegionView3D *>(regions[i]->regiondata), false);
      if (regions[i] == source) {
        cache.selected = i;
      }
    }
    cache.initialized = true;
  }
  else if (cache.initialized) {
    cache.slots[cache.selected].capture(*static_cast<RegionView3D *>(source->regiondata), true);
  }
  else {
    const RegionView3D &rv = *static_cast<RegionView3D *>(source->regiondata);
    /* Native list/rectangle order: bottom-left, top-left, bottom-right, top-right. */
    for (ViewSlot &slot : cache.slots) {
      slot.capture(rv, false);
      slot.pose.runtime_lock = {};
      slot.pose.lock = RV3D_LOCK_ROTATION;
    }
    cache.slots[0].pose.axis(RV3D_VIEW_FRONT);
    cache.slots[1].pose.axis(RV3D_VIEW_TOP);
    cache.slots[2].pose.axis(RV3D_VIEW_RIGHT);
    cache.slots[3].pose.persp = RV3D_PERSP;
    cache.slots[3].pose.view = RV3D_VIEW_USER;
    cache.slots[3].pose.lock = {};
    cache.selected = rv.persp != RV3D_ORTHO                         ? 3 :
                     ELEM(rv.view, RV3D_VIEW_FRONT, RV3D_VIEW_BACK) ? 0 :
                     ELEM(rv.view, RV3D_VIEW_TOP, RV3D_VIEW_BOTTOM) ? 1 :
                     ELEM(rv.view, RV3D_VIEW_LEFT, RV3D_VIEW_RIGHT) ? 2 :
                                                                      3;
    cache.slots[cache.selected].capture(rv, true);
    cache.initialized = true;
  }
  PointerRNA props = WM_operator_properties_create("SCREEN_OT_region_quadview");
  RNA_boolean_set(&props, "preserve_active_view", true);
  const wmOperatorStatus result = WM_operator_name_call(
      C, "SCREEN_OT_region_quadview", wm::OpCallContext::ExecRegionWin, &props, nullptr);
  WM_operator_properties_free(&props);
  if (result != OPERATOR_FINISHED) {
    return false;
  }
  regions = window_regions(area);
  if (regions.size() == 1) {
    RegionView3D &rv = *static_cast<RegionView3D *>(regions[0]->regiondata);
    cache.slots[cache.selected].pose.apply(rv);
    cache.slots[cache.selected].single_clipping.apply(rv);
    rv.viewlock &= ~(RV3D_LOCK_ROTATION | RV3D_BOXVIEW | RV3D_BOXCLIP);
    rv.runtime_viewlock &= ~(RV3D_LOCK_ROTATION | RV3D_BOXVIEW | RV3D_BOXCLIP);
  }
  else if (regions.size() == 4) {
    for (int i = 0; i < 4; i++) {
      cache.slots[i].pose.apply(*static_cast<RegionView3D *>(regions[i]->regiondata));
    }
    cache.topology = topology(area);
    refresh_quad_clipping(C, cache, true);
  }
  cache.topology = topology(area);
  ED_area_tag_redraw(area);
  return true;
}
}  // namespace

void axismeld_view_cache_free(void *cache)
{
  delete static_cast<ViewCache *>(cache);
}

bool axismeld_boxview_clip_preserve(const ScrArea *area)
{
  if (!STREQ(U.keyconfigstr, "AxisMeld_Maya_2026") || area->spacetype != SPACE_VIEW3D) {
    return false;
  }
  const View3D *v3d = area->spacedata.first_as<View3D>();
  const auto *cache = static_cast<const ViewCache *>(v3d->runtime.axismeld_view_cache);
  if (!cache || cache->topology != topology(area)) {
    return false;
  }
  bool has_xy_bounds = false;
  bool has_z_bounds = false;
  for (const ARegion &region : area->regionbase) {
    if (region.regiontype != RGN_TYPE_WINDOW || !region.regiondata) {
      continue;
    }
    const auto *rv = static_cast<const RegionView3D *>(region.regiondata);
    if (RV3D_LOCK_FLAGS(rv) & RV3D_BOXCLIP) {
      has_xy_bounds |= ELEM(rv->view, RV3D_VIEW_TOP, RV3D_VIEW_BOTTOM);
      has_z_bounds |= ELEM(rv->view, RV3D_VIEW_FRONT, RV3D_VIEW_BACK);
    }
  }
  /* Axis actions may remove a boundary contributor while retaining quad locks.
   * Preserve the region-owned last valid volume, including during native navigation. */
  return !has_xy_bounds || !has_z_bounds;
}

bool axismeld_view_context_poll(bContext *C)
{
  return STREQ(U.keyconfigstr, "AxisMeld_Maya_2026") && CTX_wm_area(C) &&
         CTX_wm_area(C)->spacetype == SPACE_VIEW3D && CTX_wm_region(C) &&
         CTX_wm_region(C)->regiontype == RGN_TYPE_WINDOW && CTX_wm_region_view3d(C) &&
         ELEM(CTX_data_mode_enum(C), CTX_MODE_OBJECT, CTX_MODE_EDIT_MESH);
}

bool axismeld_view_action(bContext *C, wmOperator *op, const HotboxAction action)
{
  if (!axismeld_view_context_poll(C) || !supported(C, op)) {
    return false;
  }
  View3D *v3d = CTX_wm_view3d(C);
  ScrArea *area = CTX_wm_area(C);
  ARegion *region = CTX_wm_region(C);
  ViewCache &cache = cache_ensure(C, v3d, area);
  if (action == HotboxAction::ToggleQuad) {
    return toggle_quad(C, cache);
  }
  ED_view3d_smooth_view_force_finish(C, v3d, region);
  RegionView3D &rv = *CTX_wm_region_view3d(C);
  int index = cache.selected;
  const auto regions = window_regions(area);
  if (regions.size() == 4) {
    for (int i = 0; i < 4; i++) {
      if (regions[i] == region) {
        index = i;
      }
    }
  }
  ViewSlot &slot = cache.slots[index];
  slot.capture(rv, cache.initialized && regions.size() == 1);
  ViewPose next;
  next.capture(rv);
  copy_qt_qt(next.last_quat, rv.viewquat);
  next.last_view = rv.view;
  next.last_persp = rv.persp;
  next.last_roll = rv.view_axis_roll;
  if (action == HotboxAction::Perspective) {
    if (slot.has_perspective) {
      copy_qt_qt(next.quat, slot.perspective.quat);
      copy_v3_v3(next.ofs, slot.perspective.ofs);
      next.dist = slot.perspective.dist;
      next.roll = slot.perspective.roll;
    }
    next.persp = RV3D_PERSP;
    next.view = RV3D_VIEW_USER;
  }
  else if (ELEM(action, HotboxAction::Side, HotboxAction::Front, HotboxAction::Top)) {
    next.axis(action == HotboxAction::Side  ? RV3D_VIEW_RIGHT :
              action == HotboxAction::Front ? RV3D_VIEW_FRONT :
                                              RV3D_VIEW_TOP);
  }
  else if (ELEM(action, HotboxAction::Left, HotboxAction::Back, HotboxAction::Bottom)) {
    next.axis(action == HotboxAction::Left ? RV3D_VIEW_LEFT :
              action == HotboxAction::Back ? RV3D_VIEW_BACK :
                                             RV3D_VIEW_BOTTOM);
  }
  else {
    return false;
  }
  next.apply(rv);
  slot.capture(rv, cache.initialized && regions.size() == 1);
  refresh_quad_clipping(C, cache, false);
  ED_region_tag_redraw(region);
  return true;
}

static wmOperatorStatus axismeld_view_exec(bContext *C, wmOperator *op)
{
  return axismeld_view_action(C, op, HotboxAction(RNA_enum_get(op->ptr, "action"))) ?
             OPERATOR_FINISHED :
             OPERATOR_CANCELLED;
}

void VIEW3D_OT_axismeld_view(wmOperatorType *ot)
{
  static const EnumPropertyItem actions[] = {
      {int(HotboxAction::ToggleQuad),
       "TOGGLE_QUAD",
       0,
       "Toggle Quad",
       "Maximize or restore this pane"},
      {int(HotboxAction::Perspective),
       "PERSPECTIVE",
       0,
       "Perspective",
       "Restore perspective view"},
      {int(HotboxAction::Side), "SIDE", 0, "Side", "View from the right"},
      {int(HotboxAction::Front), "FRONT", 0, "Front", "View from the front"},
      {int(HotboxAction::Top), "TOP", 0, "Top", "View from above"},
      {int(HotboxAction::Left), "LEFT", 0, "Left", "View from the left"},
      {int(HotboxAction::Back), "BACK", 0, "Back", "View from behind"},
      {int(HotboxAction::Bottom), "BOTTOM", 0, "Bottom", "View from below"},
      {0, nullptr, 0, nullptr, nullptr},
  };
  ot->name = "AxisMeld View";
  ot->idname = "VIEW3D_OT_axismeld_view";
  ot->description = "Change the initiating AxisMeld view without changing scene geometry";
  ot->poll = axismeld_view_context_poll;
  ot->exec = axismeld_view_exec;
  RNA_def_enum(
      ot->srna, "action", actions, int(HotboxAction::ToggleQuad), "Action", "View action");
}
}  // namespace blender

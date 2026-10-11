/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_context.hh"
#include "BLI_string.hh"
#include "DNA_object_types.h"
#include "DNA_userdef_types.h"
#include "WM_api.hh"

#include "transform.hh"
#include "transform_snap.hh"

namespace blender::ed::transform {

static bool supported_mode(const TransInfo *t)
{
  return ELEM(t->mode, TFM_TRANSLATION, TFM_ROTATION, TFM_RESIZE);
}

static AxisMeldSnapKey snap_key(const wmEventType type)
{
  switch (type) {
    case EVT_XKEY:
      return AxisMeldSnapKey::Grid;
    case EVT_VKEY:
      return AxisMeldSnapKey::Vertex;
    case EVT_JKEY:
      return AxisMeldSnapKey::Increment;
    default:
      return AxisMeldSnapKey::None;
  }
}

static AxisMeldSnapSettings current_settings(const TransInfo *t)
{
  return {int(t->tsnap.mode), bool(t->modifiers & MOD_SNAP), bool(t->modifiers & MOD_SNAP_INVERT)};
}

static void apply_settings(TransInfo *t, const AxisMeldSnapSettings settings)
{
  t->tsnap.mode = eSnapMode(settings.mode);
  SET_FLAG_FROM_TEST(t->modifiers, settings.enabled, MOD_SNAP);
  SET_FLAG_FROM_TEST(t->modifiers, settings.invert, MOD_SNAP_INVERT);
  transform_snap_flag_from_modifiers_set(t);
  /* A target acquired with a different snap mode must not survive this switch. */
  t->tsnap.status &= ~(SNAP_TARGET_FOUND | SNAP_SOURCE_FOUND);
  t->tsnap.source_type = SCE_SNAP_TO_NONE;
  t->tsnap.target_type = SCE_SNAP_TO_NONE;
  t->tsnap.last = 0.0;
  t->redraw |= TREDRAW_HARD;
}

static void apply_temporary(TransInfo *t)
{
  apply_settings(t,
                 t->axismeld_snap.effective(
                     SCE_SNAP_TO_GRID, SCE_SNAP_TO_VERTEX, SCE_SNAP_TO_INCREMENT));
}

void axismeld_transform_snap_init(TransInfo *t, const wmEvent *event)
{
  const Object *object = CTX_data_active_object(t->context);
  t->axismeld_snap.enabled = event && STREQ(U.keyconfigstr, "AxisMeld_Maya_2026") &&
                            t->spacetype == SPACE_VIEW3D && t->region &&
                            t->region->regiontype == RGN_TYPE_WINDOW && supported_mode(t) &&
                            object &&
                            (object->mode == OB_MODE_OBJECT ||
                             (object->type == OB_MESH && object->mode == OB_MODE_EDIT)) &&
                            !(t->options & (CTX_CAMERA | CTX_CURSOR | CTX_TEXTURE_SPACE));
  if (!t->axismeld_snap.enabled || event->modifier & (KM_ALT | KM_OSKEY)) {
    return;
  }
  const AxisMeldSnapKey key = snap_key(event->keymodifier);
  /* Shift+J is Maya relative snapping, not Blender precision increments. */
  if (key == AxisMeldSnapKey::Increment && (event->modifier & KM_SHIFT)) {
    return;
  }
  if (t->axismeld_snap.press(key, current_settings(t))) {
    apply_temporary(t);
  }
}

bool axismeld_transform_snap_event(TransInfo *t, const wmEvent *event)
{
  AxisMeldSnapState &state = t->axismeld_snap;
  if (!state.enabled) {
    return false;
  }
  if (event->type == WINDEACTIVATE && state.active() != AxisMeldSnapKey::None) {
    axismeld_transform_snap_finish(t);
    t->state = TRANS_CANCEL;
    return true;
  }
  if (event->type == EVT_MODAL_MAP && state.active() != AxisMeldSnapKey::None) {
    switch (event->val) {
      case TFM_MODAL_TRANSLATE:
      case TFM_MODAL_ROTATE:
      case TFM_MODAL_RESIZE:
      case TFM_MODAL_TRACKBALL:
      case TFM_MODAL_ROTATE_NORMALS:
      case TFM_MODAL_VERT_EDGE_SLIDE:
        /* Native mode changes initialize snapping again. Capture that new baseline afterward. */
        apply_settings(t, state.base);
        state.mode_reset_pending = true;
        break;
      case TFM_MODAL_SNAP_INV_ON:
      case TFM_MODAL_SNAP_INV_OFF:
        state.base.invert = event->val == TFM_MODAL_SNAP_INV_ON;
        apply_temporary(t);
        return true;
      case TFM_MODAL_SNAP_TOGGLE:
        state.base.enabled = !state.base.enabled;
        apply_temporary(t);
        return true;
      default:
        break;
    }
  }

  const wmEventType type = event->type == EVT_MODAL_MAP ? event->prev_type : event->type;
  const short value = event->type == EVT_MODAL_MAP ? event->prev_val : event->val;
  const AxisMeldSnapKey key = snap_key(type);
  if (key == AxisMeldSnapKey::None) {
    return false;
  }
  if (value == KM_RELEASE && state.release(key)) {
    apply_temporary(t);
    return true;
  }
  if (value != KM_PRESS || !supported_mode(t) ||
      (event->modifier & (KM_CTRL | KM_ALT | KM_OSKEY)) ||
      (key == AxisMeldSnapKey::Increment && (event->modifier & KM_SHIFT)))
  {
    return false;
  }
  if (state.press(key, current_settings(t))) {
    apply_temporary(t);
  }
  /* Auto-repeat is owned, too: never let it become an X-axis constraint. */
  return true;
}

void axismeld_transform_snap_after_event(TransInfo *t)
{
  AxisMeldSnapState &state = t->axismeld_snap;
  if (state.mode_reset_pending) {
    state.mode_reset_pending = false;
    state.base = current_settings(t);
    if (supported_mode(t)) {
      apply_temporary(t);
    }
    else {
      state.clear();
    }
  }
}

void axismeld_transform_snap_finish(TransInfo *t)
{
  if (t->axismeld_snap.active() != AxisMeldSnapKey::None) {
    apply_settings(t, t->axismeld_snap.base);
    t->axismeld_snap.clear();
  }
}

}  // namespace blender::ed::transform

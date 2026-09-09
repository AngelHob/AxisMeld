/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "WM_api.hh"
#include "WM_types.hh"
#include "transform_gizmo.hh"

namespace blender::ed::transform {

static bool axis_select_poll(bContext *C)
{
  return axismeld_gizmo_highlight_axis(C) != -1;
}

static bool axis_selected_poll(bContext *C)
{
  return axismeld_gizmo_selected_axis(C) != -1;
}

static wmOperatorStatus axis_select_invoke(bContext *C, wmOperator *, const wmEvent *)
{
  return axismeld_gizmo_select_axis(C) ? OPERATOR_FINISHED : OPERATOR_PASS_THROUGH;
}

static wmOperatorStatus axis_clear_invoke(bContext *C, wmOperator *, const wmEvent *)
{
  axismeld_gizmo_clear_axis(C);
  return OPERATOR_FINISHED;
}

static wmOperatorStatus axis_drag_invoke(bContext *C, wmOperator *, const wmEvent *event)
{
  // The nested native transform owns modal events, cancel and undo, including MMB release.
  return axismeld_gizmo_drag_axis(C, event) ? OPERATOR_FINISHED : OPERATOR_PASS_THROUGH;
}

static void AXISMELD_OT_axis_select(wmOperatorType *ot)
{
  ot->name = "Select Transform Axis";
  ot->idname = "AXISMELD_OT_axis_select";
  ot->description = "Keep the clicked transform axis for subsequent middle-mouse drags";
  ot->poll = axis_select_poll;
  ot->invoke = axis_select_invoke;
  ot->flag = OPTYPE_INTERNAL;
}

static void AXISMELD_OT_axis_clear(wmOperatorType *ot)
{
  ot->name = "Clear Transform Axis";
  ot->idname = "AXISMELD_OT_axis_clear";
  ot->description = "Clear the persistent transform axis without changing geometry";
  ot->poll = axis_selected_poll;
  ot->invoke = axis_clear_invoke;
  ot->flag = OPTYPE_INTERNAL;
}

static void AXISMELD_OT_axis_drag(wmOperatorType *ot)
{
  ot->name = "Drag Selected Transform Axis";
  ot->idname = "AXISMELD_OT_axis_drag";
  ot->description = "Use the selected transform axis from anywhere in this viewport";
  ot->poll = axis_selected_poll;
  ot->invoke = axis_drag_invoke;
  ot->flag = OPTYPE_INTERNAL;
}

void axismeld_transform_operatortypes()
{
  WM_operatortype_append(AXISMELD_OT_axis_select);
  WM_operatortype_append(AXISMELD_OT_axis_clear);
  WM_operatortype_append(AXISMELD_OT_axis_drag);
}

}  // namespace blender::ed::transform

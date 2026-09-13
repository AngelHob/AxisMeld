# M2b pointer target implementer report

## Outcome
Implemented read-only Object-mode component PRESS target capture using native GPU picking. Only a submitted component command changes selection. Capture stores the Object session UID and view-layer identity, never a retained Base/Object pointer. Commit resolves the live UID in the current view layer and rechecks visible/selectable/editable Mesh plus Object mode. Missing, deleted, hidden, unselectable or non-editable targets cancel without falling back to the active object.

- Pointer hit Mesh: unselected target replaces selection, selected target preserves native multi-selection and becomes active.
- Empty space: retain the active selected editable Mesh context.
- Closest non-Mesh: native RMB pass-through. No Mesh-only filtering that would select geometry behind the non-Mesh.
- Keyboard trigger and Edit Mesh retain active/native editing context.
- Only this component root's four implemented command nodes are enabled after a native valid target capture; other commands and disabled slots remain governed by existing capability rules.
- PRESS and cancellation do not dispatch, select, activate, push undo or record Recent.
- Existing QWER/general hotbox release lifecycle code is unchanged.

## Native API choice
Added ED_view3d_give_nearest_selectable_base_under_cursor in ED_view3d.hh, backed by existing view3d_select.cc GPU buffers and native BASE_SELECTABLE filtering. The original generic cursor helper retains its default behavior. The dedicated helper forces nearest and disables the final bone-priority/X-Ray cycling evaluation. X-Ray therefore targets nearest rather than cycling through active objects; this is an explicit M2b behavior.

The helper is a generic read-only nearest-selectable API, so its public ED declaration was retained after discussion with main; the initial header dependency rebuild already completed. No Python ray cast, temporary selection probe, geometry modification or copied proprietary implementation was introduced.

## Review correction
Matched native editmode_enter_ex preflight by rejecting ID_IS_OVERRIDE_LIBRARY(object->data), in addition to Object override and editable checks. Attempting a Python Mesh.override_create fixture returned None on this build; that invalid fixture was removed, and this rare state has source-review evidence only, not claimed dynamic test coverage. No general dispatcher transaction/undo rewrite.

## Validation and evidence
- RED: original candidate failed the new unselected-pointer-target assertion: commit still edited the old active object. Cancellation assertions already preserved state.
- Final build: cmake --build D:\source\AxisMeld-build --config Release --target blender axismeld_hotbox_menu_test --parallel 2 succeeded.
- Python: 57 tests passed (unittest discover tests/python axismeld_*test.py).
- CTest: editor_hotbox_hotbox_model, axismeld_hotbox_menu, axismeld_hotbox_state, axismeld_identity, axismeld_transform_axis: 5/5 passed.
- Final components GUI suite: AXISMELD_COMPONENT_HOTBOX_EVENTS_PASS.
- git diff --check passed (only existing docs LF/CRLF warning).

Logs:
- D:\source\AxisMeld-build\m2b-build.log
- D:\source\AxisMeld-build\m2b-python.log
- D:\source\AxisMeld-build\m2b-native.log
- D:\source\AxisMeld-build\m2b-components.log

GUI coverage: unselected target commit; center/Esc/placeholder cancellation with original selection/active/Recent unchanged; already-selected target preserving multi-selection; no active object pointer target while global ordinary edge command stays unavailable; target made unselectable during session; target actually deleted during session; Edit Mode preserving a different editing object; actual filled Curve occluding the Mesh and native menu draw; hidden/empty fallback; keyboard F13 keeping a different active mesh; all previous direction/modifier/focus/release/normal-LMB cases.

Scene setup in the event fixture yields before PRESS so Blender has rendered new/removed objects into GPU selection state. This addresses test setup timing, not a production selection rollback.

Screenshot: D:\source\AxisMeld-build\m2b-artifacts\pointer-before-commit.png. Visually checked: component menu is over unselected Cube; Cube.001 remains active and selected in Outliner (its geometry lies outside the viewport). Also component-ring.png.

## Candidate handoff
After main confirmed backup, synced only candidate blender-opacity-check.exe and 5.3/scripts/startup/bl_operators/axismeld.py. Primary blender.exe was not overwritten; no commit/push. GUI ownership returned to main; no GUI process remains from implementer.

Candidate/bin SHA256: 3FCEBEBD3C141B01F9A0D091E37DE1DF0D97CCE15B2E7A6F3B3A0CB66BCBFEDF.

## Limits
Native GPU visibility/selectability semantics apply. Instances are not claimed as individual editable targets: native pick resolves a Base/owner, and collection/Geometry Nodes instance targeting has no additional support or acceptance coverage in this slice. Manual checks remain for physical gesture feel, viewport edges/quad regions, hidden/unselectable filtering nuance and X-Ray nearest behavior. Final installed QWER/hotbox/release regression is owned by main.

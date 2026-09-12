# M2a implementer report

Task 1 implemented; no commit, no primary installed blender.exe replacement, no portable config writes.

## Scope

- Added context.components radial menu under common.select: N Edge, W Vertex, S Face, NE idempotent Object Mode; E UV, SW Vertex Face, SE Multi Component remain disabled without command IDs and retain plan references.
- context.component_hotbox defaults to unmodified RMB PRESS. Object/mesh Edit selected visible editable mesh checks reuse the adapter. Unsupported contexts PASS_THROUGH to existing native RMB handlers.
- Profiles remain schema-1 PRESS-only; modified component bindings are rejected. Rebinds and disables retain native fallback; regenerated keymaps remove only old owned component items.
- Native component session immediately displays existing radial UI, commits on its own trigger release, clears owners before dispatch, cancels center/Esc/focus loss, and permits keyboard remapping. Mouse guards use one trigger owner, never a duplicate mouse owner.
- Same-event modified owned release relinquishes its mouse/trigger owner; QWER still retain their held keyboard trigger until released.
- Select directory replaces a non-action separator with the component submenu, retaining 8 items on one page rather than adding paging controls.
- The exact native Screen Editing/screen.area_options unmodified RMB item is exempted from global conflict detection; its edge-only handling remains unchanged. Other global RMB conflicts still fail.

## Files

New: scripts/modules/axismeld/context_hotbox.py; tests/python/axismeld_component_hotbox_test.py; tests/python/axismeld_component_hotbox_events.py.
Updated Python: adapter.py, commands.py, hotbox_catalog.py, hotbox_runtime.py, keymap.py, profiles.py under scripts/modules/axismeld; scripts/startup/bl_operators/axismeld.py; tests/python/axismeld_hotbox_ui_runner.py, axismeld_hotbox_catalog_test.py, axismeld_input_test.py.
Updated native: view3d_axismeld_hotbox.cc, view3d_axismeld_hotbox_release.cc, view3d_axismeld_hotbox_model.cc under source/blender/editors/space_view3d; its tests/hotbox_model_test.cc; source/blender/axismeld/tests/hotbox_menu_test.cc.

## Verification evidence

All logs below are in D:/source/AxisMeld-build/.

- Pure unit RED: component registry/menu missing, then GREEN. Additional modified-profile test RED then GREEN. Exact area-edge exception regression RED in m2a-area-edge-red.log.
- Real Blender RED mode.object unavailable: m2a-component-red.log.
- Native parser RED rejects mode.object: m2a-model-red.log; whitelist implemented afterward.
- Modified owned-release RED reproduced on old candidate in isolated sequential rerun: m2a-modified-release-red.log. Native fix rebuild: m2a-release-fix-build.log. Final new candidate real component suite GREEN: m2a-component-green.log.
- Python discovery: 57 tests PASS, m2a-python-green.log.
- Native CTest: editor_hotbox_hotbox_model, axismeld_hotbox_menu, axismeld_hotbox_state, axismeld_identity, axismeld_transform_axis all PASS, m2a-native-green.log.
- Final components suite: all four directions, repeated mode.object/gestures, center/Esc/disabled slots, actual native object-context-menu draw probe after RMB with unselected/non-mesh targets, actual user keymap F13 remapping and disable native fallback, modifier exclusion, modified owned-release cleanup, WINDOW_DEACTIVATE cancellation without old release then successful reopening, normal LMB selection afterward.
- Screenshot: m2a-artifacts/component-ring.png.
- Candidate updated: phase2b-ui-test-install/blender-opacity-check.exe plus axismeld Python modules/startup operator, after main-owned backup. Primary blender.exe unchanged by implementer.
- One earlier GUI edge RED accidentally overlapped main tools suite; it was discarded and reproduced in an exclusive sequential RED/GREEN run. Final components GREEN is exclusive.

## Limits / handoff

Active selected mesh only; under-pointer target picking is M2b. UV/Vertex Face/Multi Component not implemented. Human physical input, cross-application focus, DPI and feel remain manual checks. Space shares the registered submenu and native parser/layout validation, but the component event suite specifically exercises direct RMB/F13 entries. Main owns independent tools/Space/release regressions, screenshot inspection, final install and manual ledger.

The existing libpng iCCP warning appears in factory-scene runs; no Python traceback in final GREEN. No release-scale or other modeling algorithms changed.

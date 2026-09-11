# Task 1 implementation report

Archived implementer-stage record: statements about pending review/installation below preserve their original timing. Final controller delivery and manual boundaries are in [M1 acceptance](../../compatibility/2026-09-11-m1-tool-hotboxes.md); review outcomes and rulings are in [execution ledger](2026-09-11-m1-execution-ledger.md).

Status: DONE for the assigned implementation task. Primary installation and independent review remain controller-owned.

## Implementation

- Added four classic Maya Q/W/E/R root rings under Modify > Tool Settings, using exactly the controller-verified first-level directions. The default snapshot remains four roots, 200 catalog nodes, 31,673 UTF-8 bytes before live capability differences/history.
- Added optional, validated `direction` / `presentation` fields and appended native aggregate members. Old snapshots remain accepted. Lists use metadata; existing Space list identifiers retain their previous behavior.
- Added an explicit hidden, skip-save `tool_menu` native operator parameter restricted to the four registered roots. Keyboard Q/W/E/R switches the native tool synchronously, then arms an invisible modal. Unmodified LMB starts a standalone opaque native ring at the actual pointer. The native owner shares the existing source/context checks, renderer, command bridge and release guard.
- Owned LMB release submits once and closes. Trigger-first release cancels; trigger repeats are consumed; Q release does not reset Lasso/Circle. Settings lists retain the parent ring and block unrelated ring targets. Returning to the actual gesture origin backs out of a child.
- Native persistent Box/Lasso/Circle selection tools; native Object/Edit clear selection with child undo; per-tool orientation slots 1/2/3 with `use=True`, World=GLOBAL, Object=LOCAL, Normal=NORMAL, Rotate-only Gimbal, and View (Blender) in Axis lists.
- The same semantic commands are in COMMANDS, menu allowlist, policy and native parser; no new default binding. Tool roots invoked from menu/EXEC never arm a keyboard session. Existing profile schema remains unchanged.
- Deferred entries carry M1-P01..09 and specific capability/adapter reasons. UV state is never touched. No global wrapper UNDO was added.
- Fixture export now carries both optional metadata fields; CMake depends on the new tool_hotbox.py module so native tests cannot reuse an old catalog fixture.

## TDD evidence

1. Pure RED before catalog implementation:
   `C:/Python314/python.exe -m unittest discover -s tests/python -p axismeld_tool_hotbox_test.py`
   Result: 2 tests, 1 failure + 1 expected boundary error. `tools.select` absent; serializer rejected optional metadata as unknown fields. Not import-error-only proof.
2. Native parser RED:
   Build `editor_hotbox_hotbox_model_test`; run CTest `-R '^editor_hotbox_hotbox_model$' --output-on-failure`.
   Result: 8 passed, 1 failed, `DirectionMetadataIsOptionalStrictAndAtomic`: actual false, expected true for the optional direction/radial fixture.
3. Native layout RED:
   Build `axismeld_hotbox_menu_test`; run CTest `-R '^axismeld_hotbox_menu$' --output-on-failure`.
   Result: 41 passed, 1 failed, `StandaloneToolDirectionsAndNativeChildOwnership`: layout had 35 rectangles, expected 8. Saved output: `D:/source/AxisMeld-build/m1-tools-layout-red.log`.
4. Real GUI RED on old candidate with source Python:
   `axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe --suite tools`
   Result: the new orientation action raised `ValueError: No Blender adapter for this command` in the real native context.
5. First pure GREEN: the two initial focused tests passed; a subsequent full run passed 49 tests. Final expanded results are recorded below when complete.
6. Full native tree regression RED after adding real metadata: the new standalone test passed, but `RealDefaultTreeHasClickablePathsAtCornersAndCenter` could not fit new tool rings at 480 x 320. A fixed 24 px center hole independent of the opening directory width and compact placement resolved it. The final text-safe version retains the full native 60 px submenu padding and uses a 1.6 horizontal ellipse ratio only for explicit radial tool menus; legacy menus keep 1.7. No test expectation was weakened.
7. Unrelated mouse RED: `m1-tools-unrelated-red.log` shows `unrelated mouse action must leave armed tool menu` on BUTTON4MOUSE. Fixed tool sessions to leave on non-timer, non-motion, non-owned inputs and pass them through. The complete subsequent tools suite passed.
8. Strict focus-loss RED: `m1-tools-focus-red.log` shows `focus loss must clean tool ownership without old releases: ['VIEW3D_OT_axismeld_hotbox_release_guard']`. Tool sessions now directly clean up on WINDEACTIVATE without creating a new guard after the only focus-loss event. The Space branch and shared release-guard implementation are unchanged. Complete tools suite GREEN after rebuilding, including assertion before any old release is delivered.
9. Visual RED in the first compact version: Keep Spacing was visibly ellipsized because native `uiDefIconTextMenuBut` requires its text/arrow reserve. Restored native padding and changed only the tool-ring aspect ratio rather than narrowing labels. Final screenshot/native-fit verification is recorded below.

## Scope and limitations

- Targets classic Maya tool menus, not every Modeling Toolkit override.
- Circle is an adapted persistent Blender selection tool, not a complete Maya paint-selection implementation.
- Blender normal orientation and Euler gimbal semantics remain native. Same-tool tap does not reset Maya's active handle. Global object scaling differences are unchanged.
- No checked-state metadata was added: the menu does not show an active-orientation check mark; the underlying orientation slots are authoritative.
- Native settings lists contain a bounded adapted subset and consolidated placeholders; full Maya child option ordering/algorithms are not claimed.
- Event simulation does not expose the OS repeat-flag setter. Repeated physical key-down and modal deduplication are tested; the explicit WM_EVENT_IS_REPEAT and Python event.is_repeat guards are also present.
- Extreme narrow-view limitations from prior work remain; this task does not claim to repair all existing small-pane layouts.
- M2, M3, UV, primary installation and personal configuration updates are outside this implementer task.

## Verification, self-review and commits

- Python: `C:/Python314/python.exe -m unittest discover -s tests/python -p 'axismeld_*test.py'`: **50 tests, OK** (`m1-tools-python.log`).
- Native build: requested blender + editor_hotbox_hotbox_model_test + axismeld_hotbox_menu_test targets exited 0. Fixture regeneration is recorded in `m1-tools-build.log`; dependent-module CMake regeneration occurred and `Generating hotbox_menu_fixture.hh` was present.
- Native CTest: requested regex `^(axismeld_(hotbox_menu|hotbox_state|identity|transform_axis)|editor_hotbox_hotbox_model)$`: **5/5 targets passed**, 0 failures (`m1-tools-native.log`).
- GUI runners serially passed **tools, menus, native-style, release, selection, appearance**; logs are `D:/source/AxisMeld-build/m1-tools-<suite>-final.log`. The release suite explicitly covers its same-window scope. Expected invalid-setting/adapter-error probes were preserved.
- GUI environment noise with source resources: `Add-on not loaded: "cycles", cause: No module named 'cycles'` and `libpng warning: iCCP: cHRM chunk does not match sRGB`. These are not functional test passes or failures; controller will separately verify installed resources. The runner rejected unexpected tracebacks and required each suite's explicit PASS marker.

### Actual tools GUI coverage

- Q/W/E/R immediate persistent-tool identity; one armed modal; repeated key-down does not stack; tap closes without quad toggle.
- All World/Object/Normal ring directions on W/E/R; Rotate Gimbal; three independent orientation slots; actual Axis native list -> View (Blender).
- Q Marquee/Lasso/Paint native tool identities; Q release retains chosen Lasso/Circle.
- Trigger-first cancellation; owned LMB commit and cleanup; Esc while key/mouse held; no background World action while an unrelated native child is active; disabled targets do not execute.
- Object clear and Mesh Edit clear, each with an explicit fixture baseline and one native undo; Edit mode preserved by the action. The initial failed undo fixture had no Edit baseline and was corrected to match the existing selection suite's undo test contract.
- Invisible armed pointer motion preserves object matrices and selection; Alt navigation passes through; unrelated side mouse button exits armed ownership.
- Focus loss with subsequent releases; scene replacement while armed; actual area split changes the captured region bounds and cancels a shown session; single/quad tool gesture execution.
- W/E/R immediately after closing a shown gesture without moving the pointer.
- Actual native user-keymap remap to F13 and disabling the rebuilt binding. `keyconfigs.update` rebuilds the RNA item, so the test reacquires it before disabling; retaining the old item was a fixture issue, not a production bypass.
- Strict focus loss without any old releases is the final additional regression described above.

### Still manual or not claimed by this suite

- Maya hand-feel equivalence and every Modeling Toolkit override.
- Real OS auto-repeat bit injection (not exposed by event_simulate); repeated key-down handling is covered.
- Tools suite does not simulate direct gizmo or middle-button axis drags under each newly configured per-tool orientation. It asserts real native orientation slots, with shared gizmo/AxisMeld invoke-preparation code verified by the controller. Existing manipulator regression is a separate result, recorded below when run.
- Tools suite does not separately exercise every component mode, multi-object mesh edit, hidden/nonselectable object variant, or real multi-window OS focus switching. Existing selection regression separately covers its vertex/edge/face, multi-object and hidden-component cases; that is not relabeled as exhaustive Clear-specific testing.

Self-review found and fixed the new-ring narrow-layout issue, unrelated-input ownership gap and strict focus-loss ownership gap. No changes to primary installed blender.exe or personal settings were made. Controller owns Maya mapping and compatibility/acceptance documentation.

- Final focus fix build exited 0 (`m1-tools-focus-build.log`), and the complete tools suite including no-old-release focus loss passed (`m1-tools-tools-final.log`).
- Existing manipulator GUI regression passed (`m1-tools-manipulator-final.log`): direct axis drag, click + constrained/repeated MMB, cancel, undo, all four quad panes, edit mesh, Alt navigation, preset isolation, and the Tool Settings-extended Modify menu boundary. This retains the suite's actual context coverage; it is not a new per-tool custom-orientation drag matrix.

Final label/layout build exited 0 (`m1-tools-label-build.log`); the requested 5 CTest targets passed again, including all 42 layout tests and the unchanged 480 x 320 traversal. The complete tools GUI suite passed again after that build. Final visual inspection of both saved screenshots confirms full Keep Spacing text, equal-width tool buttons, no center button, and retained parent ring beside the native child. Screenshot paths:

- `D:/source/AxisMeld-build/m1-tools-artifacts/m1-tools-move-ring.png`
- `D:/source/AxisMeld-build/m1-tools-artifacts/m1-tools-native-child.png`

Final candidate: `D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe`

SHA-256: `DC2107F7BB39EA7EF38E05E9A53CC0050BDB9753FFBC515A6C55A8CD53F927CC`

Only the allowed candidate was overwritten, after checking it had no running process. The primary installed executable was never overwritten. Candidate uses the specified source-resources environment; installed-resource acceptance belongs to the controller.

Implementation commit: `0b27a59ba1a Add classic QWER tool marking menus with owned release handling`.

Final `git diff --cached --check` had no errors; git status was clean after committing. Git's normal LF/CRLF conversion notices are not test failures. No unresolved implementation defect was observed after the final targeted checks. Intentional adaptation differences and explicit manual gaps above remain.

## Files changed by this implementer

- `scripts/modules/axismeld/adapter.py`
- `scripts/modules/axismeld/commands.py`
- `scripts/modules/axismeld/hotbox_catalog.py`
- `scripts/modules/axismeld/hotbox_runtime.py`
- `scripts/modules/axismeld/tool_hotbox.py` (new)
- `scripts/startup/bl_operators/axismeld.py`
- `source/blender/axismeld/AXM_hotbox_menu.hh`
- `source/blender/axismeld/CMakeLists.txt`
- `source/blender/axismeld/intern/hotbox_menu.cc`
- `source/blender/axismeld/tests/hotbox_menu_fixture.py`
- `source/blender/axismeld/tests/hotbox_menu_test.cc`
- `source/blender/editors/space_view3d/tests/hotbox_model_test.cc`
- `source/blender/editors/space_view3d/view3d_axismeld_hotbox.cc`
- `source/blender/editors/space_view3d/view3d_axismeld_hotbox_draw.cc`
- `source/blender/editors/space_view3d/view3d_axismeld_hotbox_internal.hh`
- `source/blender/editors/space_view3d/view3d_axismeld_hotbox_model.cc`
- `tests/python/axismeld_hotbox_catalog_test.py`
- `tests/python/axismeld_hotbox_geometry_fixture.py`
- `tests/python/axismeld_hotbox_ui_runner.py`
- `tests/python/axismeld_input_test.py`
- `tests/python/axismeld_manipulator_events.py`
- `tests/python/axismeld_tool_hotbox_events.py` (new)
- `tests/python/axismeld_tool_hotbox_test.py` (new)

## Review fix round 1/5 — radial child direction contract

Status: DONE. Commit: `89b6bba727357f82fb57d894b7a0a5fd775db9d8 Require directions for every radial menu child`.

The Important review finding was reproduced before production edits: Python serialization accepted a missing `tools.move.symmetry.direction`, and native parsing accepted a radial child with no direction and replaced the old generation 99 with generation 7. Both parsers now enter their existing strict direction validation whenever the parent presentation is radial, even if the direction field is absent. All direct children must therefore supply a legal direction; ordinary legacy menus without metadata remain accepted. No layout, input ownership, command adapter, or feature changes were made.

Changed files: `scripts/modules/axismeld/hotbox_runtime.py`, `source/blender/editors/space_view3d/view3d_axismeld_hotbox_model.cc`, `tests/python/axismeld_tool_hotbox_test.py`, `source/blender/editors/space_view3d/tests/hotbox_model_test.cc`. The Python positive radial fixture now contains three command children, each with a distinct legal direction. Added Python missing-direction rejection and metadata-free legacy acceptance tests. Native missing-direction rejection also asserts generation remains 99; existing `ValidSnapshotOwnsDataAndNormalizesNull` continues to accept a legacy metadata-free snapshot.

### Exact RED / GREEN verification

All commands below ran in `D:/source/AxisMeld-phase0`; log paths are under `D:/source/AxisMeld-build`. `cmake.exe` and `ctest.exe` refer to `C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/`.

1. RED: `C:/Python314/python.exe -m unittest discover -s tests/python -p axismeld_tool_hotbox_test.py`
   - Exit 1; `Ran 5 tests`, `FAILED (failures=1)`; `test_radial_child_requires_direction`: `AssertionError: ValueError not raised`.
   - Log: `m1-tools-fix1-python-red.log`.
2. RED build: `cmake.exe --build D:/source/AxisMeld-build --config Release --target editor_hotbox_hotbox_model_test -- /m:4`
   - Exit 0; log `m1-tools-fix1-red-build.log`.
3. RED: `ctest.exe --test-dir D:/source/AxisMeld-build -C Release -R '^editor_hotbox_hotbox_model$' --output-on-failure`
   - Exit 8; 9 native cases passed, 1 failed (`RadialChildRequiresDirectionAtomically`). Actual parse result `true`, expected `false`; actual `out.generation` 7, expected 99.
   - Log: `m1-tools-fix1-native-red.log`.
4. GREEN: `C:/Python314/python.exe -m unittest discover -s tests/python -p 'axismeld_*test.py'`
   - Exit 0; `Ran 52 tests in 0.075s`, `OK`. Includes both new Python cases and the corrected valid radial fixture.
   - Log: `m1-tools-fix1-python-green.log`.
5. GREEN rebuild: `cmake.exe --build D:/source/AxisMeld-build --config Release --target blender editor_hotbox_hotbox_model_test -- /m:4`
   - Exit 0; log `m1-tools-fix1-green-build.log`.
6. GREEN: `ctest.exe --test-dir D:/source/AxisMeld-build -C Release -R '^(axismeld_(hotbox_menu|hotbox_state|identity|transform_axis)|editor_hotbox_hotbox_model)$' --output-on-failure`
   - Exit 0; `100% tests passed, 0 tests failed out of 5`. Parser target includes all 10 cases, including rejection with the unchanged-generation 99 assertion and legacy acceptance.
   - Log: `m1-tools-fix1-native-green.log`.
7. GREEN candidate GUI: `C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe --suite tools --artifacts D:/source/AxisMeld-build/m1-tools-artifacts`
   - Used the same three BLENDER_SYSTEM_RESOURCES / PYTHON / DATAFILES environment paths documented above. Candidate was copied from `bin/Release/blender.exe` only after a process-path check found no candidate process.
   - Exit 0; `AXISMELD_TOOL_HOTBOX_EVENTS_PASS`. All emitted groups passed: immediate Q/W/E/R taps/repeat ownership, real ring leaves/independent slots, trigger-first/disabled-menu/Escape, Object/Edit clear/native undo, invisible motion/Alt/focus/scene, live resize cancellation, quad/single gestures, remapped trigger/disabled binding. Both screenshots were refreshed.
   - Log: `m1-tools-fix1-tools-green.log`.
   - Existing source-resource warnings remain: `Add-on not loaded: "cycles", cause: No module named 'cycles'`; `libpng warning: iCCP: cHRM chunk does not match sRGB`. Installed-resource verification remains the controller's responsibility.

New candidate SHA-256: `8760100020BBFD92035C1450DD5FCA966A37648645A9BA0099A41211744D6D0D`.

`git diff --cached --check` passed; commit contains only the four files listed above, and git status was clean afterward. Primary installed executable and personal settings were not overwritten. This bounded parser fix did not rerun the other GUI suites or add per-tool gizmo/MMB drag coverage; the earlier coverage boundaries and controller-owned direction-chain verification remain unchanged. Implementation is frozen for the same independent reviewer to re-review.

## Final review concentrated fix — overlapping tool keys and edge-origin safety

Status: DONE. Commit: `c7909d81507a909f0af52f6807b4c0f297d8eadd Preserve tool handoff ownership and origin cancellation`.

Both Important findings were confirmed through the real GUI event queue before production changes. The initial regression test collected both failures in one disposable process rather than stopping after the first, and the final test retains strict individual assertions (no assertion relaxation).

### Minimal implementation and boundaries

- Tool-generated residual release guards now retain a `tool_session` source bit (default false). A new tool invoke may coexist only with an existing release guard from a tool, with a different actual captured trigger and no remaining mouse ownership. The old priority guard stays alive to consume its own old-key release. Non-tool/Space guards, conflicting mouse ownership, other operators and UI handlers retain the existing invoke barrier. No default Q/W/E/R key assumptions were added.
- Tool-modal hit testing now gives the real 12-logical-pixel origin dead zone priority over clamped menu rectangles. Returning to the origin collapses the child path and clears hover; no menu can open or command submit from inside that zone. Menu geometry/clamping itself is unchanged.
- Changed only `view3d_axismeld_hotbox.cc`, `view3d_axismeld_hotbox_internal.hh`, `view3d_axismeld_hotbox_release.cc` under `source/blender/editors/space_view3d`, and `tests/python/axismeld_tool_hotbox_events.py`. Shared release consumption/recovery modal logic was not refactored. No production Python adapter/default-key changes, new features, user configuration changes, or primary executable replacement.

### TDD RED evidence

Command (working directory `D:/source/AxisMeld-phase0`):

```powershell
$env:BLENDER_SYSTEM_RESOURCES='D:/source/AxisMeld-phase0'
$env:BLENDER_SYSTEM_PYTHON='D:/source/AxisMeld-build/phase2b-ui-test-install/5.3/python'
$env:BLENDER_SYSTEM_DATAFILES='D:/source/AxisMeld-build/phase2b-ui-test-install/5.3/datafiles'
& C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe --suite tools --artifacts D:/source/AxisMeld-build/m1-tools-artifacts
```

Exit 1, log `D:/source/AxisMeld-build/m1-tools-finalfix-red.log`. Relevant actual output:

```text
PASS immediate Q/W/E/R taps and repeat ownership
AssertionError: W-down E-down did not hand off one armed tool session: ['VIEW3D_OT_axismeld_hotbox_release_guard']
overlapping W-to-E gesture did not commit Rotate World: LOCAL
edge origin committed World (returned=False): GLOBAL
edge origin committed World (returned=True): GLOBAL
```

The overlap sequence was W-down, E-down, W-up, LMB-down, move to Rotate World, LMB-up, E-up. Rotate switched immediately but lacked its new armed session. Edge checks set Move orientation LOCAL, pressed W and LMB at viewport x+30 / vertical midpoint, then either released at the unchanged origin or entered the Axis submenu and returned to that origin before release. Both wrongly changed the slot to GLOBAL before the fix.

### GREEN build and tests

All commands ran serially in `D:/source/AxisMeld-phase0`; `cmake.exe` / `ctest.exe` below are from `C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/`.

1. `cmake.exe --build D:/source/AxisMeld-build --config Release --target blender editor_hotbox_hotbox_model_test -- /m:4`
   - Exit 0. Log `D:/source/AxisMeld-build/m1-tools-finalfix-build.log`.
2. `C:/Python314/python.exe -m unittest discover -s tests/python -p 'axismeld_*test.py'`
   - Exit 0; `Ran 52 tests in 0.076s`, `OK`. Log `m1-tools-finalfix-python.log`.
3. `ctest.exe --test-dir D:/source/AxisMeld-build -C Release -R '^(axismeld_(hotbox_menu|hotbox_state|identity|transform_axis)|editor_hotbox_hotbox_model)$' --output-on-failure`
   - Exit 0; `100% tests passed, 0 tests failed out of 5`. Log `m1-tools-finalfix-native.log`. This reruns existing ownership/state/layout/model targets, including the legacy/strict-parser coverage and compact layout cases; no unnecessary layout or standalone native test edits were made because the changed ownership paths are verified through actual window-manager events.
4. After confirming no process used the permitted candidate, copied `D:/source/AxisMeld-build/bin/Release/blender.exe` to `D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe`. Primary installed `blender.exe` was not touched.
5. With the same three environment variables used for RED, executed this exact runner command for each `$taskSuite` in `tools`, `hotbox`, `release`, `native-style`, serially:

   `C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe --suite $taskSuite --artifacts D:/source/AxisMeld-build/m1-tools-artifacts`

   All exited 0. Logs are `D:/source/AxisMeld-build/m1-tools-finalfix-{tools,hotbox,release,native-style}-green.log`. Final markers respectively:

   - `AXISMELD_TOOL_HOTBOX_EVENTS_PASS`
   - `AXISMELD_HOTBOX_EVENTS_PASS`
   - `AXISMELD_HOTBOX_RELEASE_EVENTS_PASS same-window scope only`
   - `AXISMELD_HOTBOX_NATIVE_STYLE_PASS`

### Actual added GUI coverage

- W-down → E-down switches Rotate immediately, with exactly one new hotbox and one old-key guard. W-up removes the old guard and leaves exactly the E hotbox; the subsequent World LMB gesture commits GLOBAL and all owners clear after E-up. This checks consumption/continuity, not just a permissive invoke result.
- W-down → E-down with E-up before LMB-up cancels the new gesture; W-up last clears residual ownership, and Rotate stays LOCAL.
- Both sequences repeat after the actual user-keymap remap of Move from W to F13, before the existing disabled-binding test.
- If the old W gesture still owns LMB, E still immediately selects Rotate but cannot start a conflicting new tool session; old mouse/key releases cleanly drain ownership.
- A Space-origin guard produced by Escape still blocks a W tool session until Space release; the new source flag is not a global modal bypass.
- Edge unchanged-origin release and Axis-submenu → origin-return release both preserve Move LOCAL and leave no stale modal.
- Existing tools coverage remains: same-key repeated press, Q selection persistence, independent orientations, unrelated mouse/Alt pass-through, trigger-first and Escape, focus loss without old releases, scene/region invalidation, quad/single, remap and disable. Existing Space hotbox and release suites separately confirm tap/hold/remap/cancel, modal-child release isolation, unrelated input, lost-release/focus recovery and settings/dispatch restrictions. Native-style suite covers the retained native-menu presentation at UI scales 1 and 2.

The new candidate SHA-256 is `97AEE90EF85872F9AF38EFD8C03576CB2DC44B5F3A8956553B8E5116C7876645` (rechecked after commit).

Self-review confirmed the four-file scope and no changed release-consumption modal algorithm, layout rules, or default keys. `git diff --check` and `git diff --cached --check` passed, and git status was clean after committing. Existing source-resource Cycles and PNG ICC warnings remain; Space/release negative probes also deliberately emit unsupported-context/unknown-setting/private-adapter-failure warnings. The GUI runner found no unexpected Python traceback in GREEN. This is not a pristine-output claim.

Not newly claimed: exhaustive per-tool gizmo/MMB direction drags, real OS auto-repeat-bit injection, separate cross-window release suite, every pixel of all four viewport edges, or installed-resource delivery acceptance. Earlier manual boundaries remain. No global/Evo files were edited. Implementation is frozen for the final reviewer's scope re-review and controller-owned installation.

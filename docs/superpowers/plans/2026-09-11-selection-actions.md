# Selection Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development task-by-task with independent review gates. Task1 and its fix1 scoped review are complete through ee4fcaf04ff; whole-batch final review passed over137c428cf0d..5b89b65311d. Candidate delivered; manual acceptance remains pending. Do not repeat implementation. This slice was activated only after the mapping final gate passed.

**Goal:** Expose three honest, synchronous Blender-native selection actions through AxisMeld's Select hotbox.

**Architecture:** Extend the existing semantic registries and small adapter, with exact per-command context gates. Keep native operators responsible for selection and undo. Use the existing menu bridge and private test runner, not new input handlers or geometry algorithms.

**Tech Stack:** Existing Python modules, Blender C++ snapshot validation, GTest, unittest and isolated Blender GUI event tests. No dependencies.

**Spec:** [Candidate design](../../design/2026-09-11-selection-actions-candidate.md) and [verified semantic boundaries](../../development/2026-09-11-modeling-adapter-preflight.md).

## Global Constraints

- Add exactly `selection.select_all`, `selection.grow`, `selection.shrink`; all status adapted, all default key=None. Preserve all existing default bindings and reserved keys.
- Select All uses object.select_all(SELECT) in Object and mesh.select_all(SELECT) in mesh Edit. Grow/Shrink only use mesh.select_more/select_less with use_face_step=True in mesh Edit. All EXEC_DEFAULT, no automatic mode switch.
- Keep the five existing Common → Select items including separator in their order, append three actions. Keep the existing Select hotbox container. Do not unlock other placeholders.
- Component-mode commands keep their visible editable selected mesh gate. New commands use exact context and native operator.poll(), not the existing broad selection prefix gate.
- Preserve native return status, Recent FINISHED policy and child-owned undo. No UNDO flag on generic wrappers, no full-geometry history comparison.
- No Select None, Invert, Duplicate, Linked Selection, UV, Global scale, keymap schema changes, new window/file commands, modal ownership changes or new dependencies.
- Work only in D:/source/AxisMeld-phase0 and the existing build. Reuse phase2b-ui-test-install; preserve portable settings and fallback, no new full install, no user process shutdown, no deletion, no push/merge/publish.
- GUI tests remain serial, hidden, factory-startup and private TEMP/config. Report manual differences in the single batch review, never claim Maya algorithm equivalence from native test success.

## Task 1: Registered selection actions with real operator and hotbox verification

This is one end-to-end task because a callable registry without its adapter/real context tests is not an independently usable deliverable.

**Files:**

- Modify `scripts/modules/axismeld/commands.py`: immutable metadata and differences.
- Modify `scripts/modules/axismeld/adapter.py`: exact gates and native execution.
- Modify `scripts/modules/axismeld/hotbox_catalog.py`: three leaves and close/replay policy.
- Modify `scripts/modules/axismeld/hotbox_runtime.py`: independent supported-command allowlist only.
- Modify `source/blender/editors/space_view3d/view3d_axismeld_hotbox_model.cc`: exact native allowlist only.
- Test `source/blender/editors/space_view3d/tests/hotbox_model_test.cc`.
- Test `source/blender/axismeld/tests/hotbox_menu_test.cc`: explicit new-ID close-before assertions, plus existing Select ellipse child-count5→8 to follow the new catalog; preserve all ellipse/back/spacing assertions.
- Test `tests/python/axismeld_hotbox_catalog_test.py`.
- Test `tests/python/axismeld_input_test.py`.
- Create `tests/python/axismeld_selection_events.py`: focused real scene/GUI result suite, not an expansion of the large generic menu suite.
- Modify `tests/python/axismeld_hotbox_ui_runner.py`: add `selection` suite with distinct marker.
- Modify `tests/python/axismeld_hotbox_menu_events.py`: update only Select-menu event geometry required by the three added leaves; preserve behavioral assertions.

**Interfaces:** Existing `available(context, command)` returns `(bool, reason)` and `run(context, command, *, invoke=True)` returns the native operator result. No signature changes. Private `_selection_operation(context, command)` returns `(bpy operator, properties dict)` or None. Runner `--suite selection` uses the new script and requires `AXISMELD_SELECTION_EVENTS_PASS`. New catalog IDs are `common.select.all`, `common.select.grow`, `common.select.shrink`.

- [x] Add registry/contract RED tests. Assert exact Select command order, complete unbound set, unchanged old baseline, adapted status, non-empty specific differences, replay/close policy and unknown-ID rejection. Example independent literals:

```python
expected = ('selection.select_all', 'selection.grow', 'selection.shrink')
self.assertEqual([node['command'] for node in node_by_id(default_catalog(), 'common.select')['children']
                  if node['kind'] == 'command'], [
    'selection.toggle_component', 'selection.vertex_mode', 'selection.edge_mode',
    'selection.face_mode', *expected])
for identifier in expected:
    self.assertIsNone(COMMANDS[identifier].key)
    self.assertEqual(COMMANDS[identifier].status, 'adapted')
    self.assertEqual(hotbox_catalog.command_policy(identifier), (True, True))
```

  Expand the existing full set assertion in `axismeld_input_test.py`, do not replace it with a subset assertion. Add native snapshot cases using existing snapshot(...) helper and literal command-node JSON for each new ID; assert parsed IDs and continued rejection of `selection.unknown` with atomic output preservation.

  Native `hotbox_command_closes()` already defaults all non-immediate-view commands to true
  (`hotbox_menu.cc:798-813`); no production policy edit is needed. Add the three new literal IDs to
  `RestrictedClosePolicyUsesLiteralCommandIdentities` so native close-before behavior is explicit.
  Preserve the unknown-ID close safety case and separate parser rejection checks. This existing-policy
  assertion is expected to pass before registration; the registration/parser tests provide RED.

- [x] Run pure Python tests and the targeted native parser test before production edits; save missing-ID RED. CMake target `editor_hotbox_hotbox_model_test` is verified from the generated `.vcxproj` and CTest file. Build that Release target and run `D:/source/AxisMeld-build/bin/tests/Release/editor_hotbox_hotbox_model_test.exe`. Record exact command and native RED output.

- [x] Create the isolated selection suite and runner route before production changes. Begin with installed native metadata/availability assertions so the old stage fails with a specific missing action assertion, not an import exception. Keep the no-source-module-injection rule; adding the tests directory solely for geometry fixture imports is allowed.

```python
from axismeld.commands import COMMANDS
check('selection.select_all' in COMMANDS, 'installed Select All action missing')
```

  Preserve existing runner timeout, private config, disabled preference save and failure detection. Run the stage's `--suite selection` once for installed RED. Factory test scenes only.

- [x] Add three metadata rows with explicit differences from the spec. Append the three catalog leaves after Face and add exact IDs to both independent allowlists and the close/replay set. Do not unify allowlists into a generic registry-derived acceptance path.

```python
_command('common.select.all', 'Select All', 'selection.select_all')
_command('common.select.grow', 'Grow Selection', 'selection.grow')
_command('common.select.shrink', 'Shrink Selection', 'selection.shrink')
```

- [x] Replace the prefix gate with an exact set of the existing mode commands. Route new commands through one small helper that resolves the operator/properties for current Object/EDIT_MESH, shared by available and run so the poll target cannot diverge. For Grow/Shrink outside EDIT_MESH return an unavailable reason; for Select All without active object allow object.select_all.poll() to decide. Run uses EXEC_DEFAULT regardless of invoke.

```python
SELECTION_ACTIONS = {'selection.select_all', 'selection.grow', 'selection.shrink'}
MODE_COMMANDS = {'selection.toggle_component', *COMPONENTS}

def _selection_operation(context, command):
    if command == 'selection.select_all':
        operation = bpy.ops.mesh.select_all if context.mode == 'EDIT_MESH' else bpy.ops.object.select_all
        return operation, {'action': 'SELECT'}
    if context.mode == 'EDIT_MESH' and command in {'selection.grow', 'selection.shrink'}:
        operation = bpy.ops.mesh.select_more if command == 'selection.grow' else bpy.ops.mesh.select_less
        return operation, {'use_face_step': True}
    return None
```

  `available()` checks the existing modeling context first, then exact MODE_COMMANDS gate. For new
  SELECTION_ACTIONS, None means `(False, 'Requires mesh Edit Mode')`; failed poll means
  `(False, 'Blender selection operator is unavailable in this context')`. The run branch obtains the
  same tuple after available succeeds and calls `operation('EXEC_DEFAULT', True, **properties)`.
  Actual dual-anchor GUI RED showed the omitted bool disables native child undo; Blender's Python
  call parser defaults it to false. Explicit True preserves child-owned undo without changing the
  generic wrapper flags. One undo must restore immediate pre-action B, not earlier sentinel A.

  Existing tools, views, hotbox and component-switch paths remain unchanged. Never catch a native failure and turn it into FINISHED.

- [x] Complete real scene assertions in the new suite. Use independent expected object names/mesh component sets, not a result-generated expectation. Cover:
  - Object no active selection: visible Mesh, Empty and Camera become selected; hidden and hide_select objects do not.
  - Object all selected and empty scene: dispatch returns the actual native no-op status and does not falsely create a success record. Mesh Edit no-op FINISHED follows existing Recent behavior.
  - Mesh Edit vertex/edge/face select-all, hidden components excluded, multi-object unique-data/shared-data cases, mode preserved.
  - A hand-built 5×5 quad patch with row-major face indices: grow center face12 to literal `{6,7,8,11,12,13,16,17,18}`, then shrink that region to literal `{12}`. Face Step=true includes vertex-connected diagonal faces (`bmo_utils.cc:280-410`), not just edge neighbors. Independently verify one undo restores each pre-action selection. Verify mesh counts/coordinates and UV coordinates equal the known initial fixture; native UV-selection sync invalidation is allowed and must not be mistaken for UV-coordinate mutation.
  - Object Grow/Shrink gray-disabled with reason and direct dispatch CANCELLED; wrong editor and unknown ID remain unavailable.
  - Each action via real held/clicked hotbox events, menu closes, correct result, Recent ID, W/E/R tools immediately correct; a canceled gesture changes neither scene nor Recent.
  - One new command mapped only in private user profile, saved/reloaded and effective; all default keys and no-key metadata remain unchanged.

  The face-grid fixture is independent of the operators under test:

```python
vertices = [(float(x), float(y), 0.0) for y in range(6) for x in range(6)]
faces = [(y*6+x, y*6+x+1, (y+1)*6+x+1, (y+1)*6+x)
         for y in range(5) for x in range(5)]
expected_grown_faces = {6, 7, 8, 11, 12, 13, 16, 17, 18}
expected_shrunk_faces = {12}
```

- [x] Update Select-menu coordinate fixtures in the existing menu suite to the exact new eight labels, including separator. Keep every prior mode-switch, close, non-owner release and context assertion. Do not change unrelated menu fixtures or native list geometry.

- [x] Run pure tests GREEN; build blender, native menu layout and parser test targets, then targeted CTest5. Generated menu fixture comes from `source/blender/axismeld/tests/hotbox_menu_fixture.py` through CMake; do not edit the generated header. Save logs before installation.

- [x] Verify no user Blender occupies the stage; verify portable relative paths/hashes against the batch backup; install only into existing stage. Run selection suite GREEN and inspect representative screenshots; run menus, hotbox, native-style, mappings standard/narrow/quad, release, profiles and manipulator serially, plus pure tests and targeted CTest. Report exact results and stage/build hash match. Do not run known deferred cross-window tests as a misleading completion gate.

- [x] Self-review, local commit only owned files, and report source identity, native/pure/installed RED/GREEN, exact operator results/undo evidence, logs, artifacts and adapted differences. The controller performs independent task/final review and adds H5-08 to the consolidated manual table only after completion.

## Controller activation and stop rules

Before activation, re-read mapping slice final review, current clock, git status and current stage SHA. The candidate requires enough time for implementation plus real undo and regression checks; the 04:23 consolidation boundary does not move. If insufficient, leave this plan unexecuted and report it as next work, not a partially delivered command set.

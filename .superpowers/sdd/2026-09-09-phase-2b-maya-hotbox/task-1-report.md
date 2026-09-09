# Phase 2B Task 1 report: catalog, config layers, snapshot

Date: 2026-09-09

Source review base: `4a6ea4c819c` (the linked worktree also contains later controller-owned documentation-only commits).

Scope: Task 1 pure Python catalog, fixed command policy, strict settings-layer merge, strict snapshot validation/serialization, and three unbound view command declarations.

## Result

- Added a copy-safe four-row declarative catalog with globally unique node IDs and only the approved first-batch leaves.
- Added fixed command close/replay policy. Unknown commands, `hotbox.open`, and settings are non-replayable.
- Added schema-1 hotbox settings with default `rows`, transparency 25, all three configurable rows enabled, and all center buttons mapped to `views`.
- Added strict per-layer schema validation and atomic default -> studio -> user -> session merge behavior. File I/O is intentionally not connected in this task.
- Added strict snapshot validation for fields/types, root order, menu/node structure, command/setting IDs, center references, cycles, depth 8, 256 nodes, 128-character IDs/labels, and 256 KiB serialized JSON.
- Added lazy runtime capability resolution. Importing `hotbox_runtime` does not import `bpy`; the adapter import occurs only inside live `snapshot(context)` construction.
- Declared `view.left`, `view.back`, and `view.bottom` without default key bindings. Their catalog leaves remain disabled with an adapter-not-implemented reason until Task 2 supplies the adapters.

Actual default snapshot size at review: 77 nodes, depth 4, 10,422 UTF-8 bytes.

## Files

- `scripts/modules/axismeld/commands.py`
- `scripts/modules/axismeld/hotbox_catalog.py`
- `scripts/modules/axismeld/hotbox_profiles.py`
- `scripts/modules/axismeld/hotbox_runtime.py`
- `tests/python/axismeld_hotbox_catalog_test.py`
- `tests/python/axismeld_input_test.py`
- `.superpowers/sdd/2026-09-09-phase-2b-maya-hotbox/task-1-report.md`

## TDD evidence

All complete command output is retained under `D:/source/AxisMeld-build/phase2b-validation-20260909/` with task1-prefixed unique names. Setup/import errors are separated from behavior failures below.

### Setup evidence (not claimed as behavior RED)

Command:

```powershell
& 'C:\Python314\python.exe' -m unittest discover -s tests/python -p axismeld_hotbox_catalog_test.py -v
```

Initial output ended with:

```text
ModuleNotFoundError: No module named 'axismeld.hotbox_catalog'
Ran 1 test in 0.000s
FAILED (errors=1)
```

Full output: `task1-red-initial-catalog.txt`. The later runtime-module import setup error is in `task1-red-runtime-module-setup.txt`.

### Behavior RED 1: unbound command metadata

Command:

```powershell
& 'C:\Python314\python.exe' -m unittest discover -s tests/python -p axismeld_hotbox_catalog_test.py -v
```

Observed output:

```text
test_new_view_commands_are_declared_without_default_keybindings (...) ... ERROR
KeyError: 'view.left'
Ran 1 test in 0.001s
FAILED (errors=1)
```

Full output: `task1-red-command-metadata.txt`.

GREEN output after adding metadata:

```text
test_new_view_commands_are_declared_without_default_keybindings (...) ... ok
Ran 1 test in 0.000s
OK
```

Full output: `task1-green-command-metadata.txt`.

### Behavior RED 2: complete catalog and strict layer behavior

Command:

```powershell
& 'C:\Python314\python.exe' -m unittest discover -s tests/python -p axismeld_hotbox_catalog_test.py -v
```

Observed behavior failures included the current implementation returning only `['common']` instead of all four rows, returning no approved Select leaves, preserving an unknown `extra` settings key, accepting non-canonical rows, and accepting invalid center mappings. Exact summary:

```text
Ran 9 tests in 0.006s
FAILED (failures=9, errors=23)
```

The errors were the missing `command_policy` API; the assertion failures were observable catalog/config results. Full output: `task1-red-catalog-profile-behaviors.txt`.

GREEN command was identical. Exact summary:

```text
Ran 9 tests in 0.003s
OK
```

Full output: `task1-green-catalog-profile-behaviors.txt`.

### Behavior RED 3: snapshot roundtrip and validation

Roundtrip command:

```powershell
& 'C:\Python314\python.exe' -m unittest axismeld_hotbox_catalog_test.HotboxCatalogTest.test_snapshot_roundtrip_is_strict_and_copy_safe -v
```

Observed assertion failure from the real minimal `{}` result:

```text
AssertionError: Items in the second set but not the first:
'schema_version'
'settings'
'menus'
'generation'
Ran 1 test in 0.000s
FAILED (failures=1)
```

Full output: `task1-red-snapshot-roundtrip-behavior.txt`. GREEN output was `Ran 1 test in 0.001s` / `OK` in `task1-green-snapshot-roundtrip-behavior.txt`.

Strict-boundary command:

```powershell
& 'C:\Python314\python.exe' -m unittest axismeld_hotbox_catalog_test.HotboxCatalogTest.test_snapshot_rejects_unknown_fields_types_ids_commands_and_values axismeld_hotbox_catalog_test.HotboxCatalogTest.test_snapshot_rejects_cycles_excess_depth_node_count_and_size -v
```

Observed no-op validator assertion failures:

```text
AssertionError: ValueError not raised
Ran 2 tests in 0.010s
FAILED (failures=15)
```

Full output: `task1-red-snapshot-validation-behaviors.txt`. After implementing validation, one test exposed an over-broad reason-length restriction; `task1-green-snapshot-validation-behaviors.txt` records that targeted failure. The restriction was narrowed to the contract's ID/label fields, and `task1-green-snapshot-limits.txt` records `Ran 1 test ... OK` for the corrected size gate.

### Existing input contract update

The first existing-suite run correctly exposed the old exact set expectation after adding three unbound commands:

```text
Ran 14 tests in 0.008s
FAILED (failures=1)
AssertionError: Items in the first set but not the second:
'view.bottom'
'view.left'
'view.back'
```

Full output: `task1-red-legacy-expectation-update.txt`. The expectation was updated without changing legacy schema-1 behavior.

## Verification

Focused catalog suite command:

```powershell
& 'C:\Python314\python.exe' -m unittest discover -s tests/python -p axismeld_hotbox_catalog_test.py -v
```

Output: `Ran 14 tests in 0.011s` / `OK`. Full output: `task1-green-full-catalog-suite.txt`.

Existing input suite command:

```powershell
& 'C:\Python314\python.exe' -m unittest discover -s tests/python -p axismeld_input_test.py -v
```

Output: `Ran 14 tests in 0.007s` / `OK`. Full output: `task1-green-input-regression.txt`.

Syntax command:

```powershell
& 'C:\Python314\python.exe' -m py_compile scripts/modules/axismeld/commands.py scripts/modules/axismeld/hotbox_catalog.py scripts/modules/axismeld/hotbox_profiles.py scripts/modules/axismeld/hotbox_runtime.py tests/python/axismeld_hotbox_catalog_test.py tests/python/axismeld_input_test.py
```

Output: no output, exit 0. Full output: `task1-green-pycompile.txt`.

Final fresh verification is recorded in `task1-final-verification.txt`.

No native build or GUI was required or run for this pure task.

## Self-review

- Catalog root and top-level menu order match the approved table. Planned-only UV/modeling entries are disabled and contain no fabricated commands.
- Repeated semantic commands use distinct node IDs. The two style submenus share a constructor but receive independent ID prefixes and independent dictionaries.
- Layer documents allow only schema version 1 plus settings; settings accept only the four approved keys. Candidate merge occurs on a deep copy and is committed only after full validation.
- Center button mappings accept null or any globally declared menu node ID, including ordinary dropdown menus.
- Snapshot validation checks Python `bool` separately from integer schema/generation/transparency fields and rejects non-finite numeric substitutions through strict type checks.
- Snapshot tree validation detects active recursion cycles before duplicate-ID checks, and independently enforces unique IDs, root order, node/depth/count limits, and known command/setting values.
- Runtime capability resolution only downgrades catalog-enabled command leaves. It never upgrades the three Task 2-owned view adapters, so the Task 1 snapshot cannot falsely report them operational.
- `hotbox_studio.json` / `hotbox_user.json` are declared separately from legacy `studio.json` / `user.json`; no read/write/persistence code was added.

## Handoff and concerns

- Public interfaces: `default_catalog() -> tuple`, `command_policy(command) -> tuple[bool, bool]`, `resolve_hotbox(layers) -> tuple[dict, list[str]]`, and `snapshot(context) -> str`.
- Additional pure helpers for later tasks: `apply_validated_layer`, `validate_settings`, `make_snapshot`, `validate_snapshot`, and `serialize_snapshot`.
- Task 2 must enable the `views.left/back/bottom` and `pane.panels.left/back/bottom` catalog leaves when its real adapters exist; they are deliberately disabled now.
- Task 3 owns in-memory settings, dispatch, apply/reload, and Recent implementation. Task 5 owns profile-directory file I/O and preferences persistence.
- Live adapter capability behavior and monotonically increasing `snapshot(context)` calls were not exercised in Blender because this task explicitly excluded native/GUI work. The pure serialized contract, bounds, default capability declarations, and lazy-import boundary were tested.

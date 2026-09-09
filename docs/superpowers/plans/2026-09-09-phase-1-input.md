# Phase 1 Input Foundation Implementation Plan

**Goal:** Build and ship the first usable Maya 2026 modeling key configuration.
**Architecture:** Immutable command catalog, pure layered profiles, Blender adapter and built-in preset.
**Tech Stack:** Python, Blender RNA/keyconfig API, existing CMake INSTALL and CTest.
**Spec:** `docs/design/2026-09-09-phase-1-input.md`

## Constraints

- Windows Maya 2026 baseline; all initial mappings adapted, not full parity.
- Personal overrides remain outside the distribution; no upstream keymap rewrite.
- Reuse the clean isolated worktree on `axismeld/phase-1` based on published integration.
- Continue implementation and verified integration under the existing development authorization.

## Task 1: Command and profile contracts

- [x] Create `tests/python/axismeld_input_test.py` with unittest cases importing
  `axismeld.commands`, `axismeld.profiles`, `axismeld.keymap` from source scripts/modules.
- [x] Run `python tests/python/axismeld_input_test.py` and observe missing module failure.
- [x] Implement `commands.py`: frozen catalog, `baseline_bindings()` returning copies.
  Implement `profiles.py`: `resolve_profiles(layers)` returns bindings, provenance,
  diagnostics; `load_profiles(config_dir, session=None)` reads studio/user in order.
- [x] Verify real precedence, disable, collision, malformed JSON and baseline immutability.

## Task 2: Built-in preset and semantic adapter

- [x] Implement `keymap.py: generate_keymaps(base, bindings)` and collision reporting
  without mutating caller data or addon keymaps; preserve other editors and modal maps.
- [x] Implement `adapter.py: available(context, command)` and
  `run(context, command, invoke=True)`, using native Blender tools, mode and view operations.
- [x] Add `scripts/startup/bl_operators/axismeld.py` and register in its package list.
- [x] Add `scripts/presets/keyconfig/AxisMeld_Maya_2026.py` with reload and baseline controls.
- [x] Add `tests/python/axismeld_input_blender.py`; test actual RNA, tool and mesh transitions,
  keyconfig registration, reload and switch-back using the built executable.

## Task 3: Integration and user-facing handoff

- [x] Register pure and Blender tests beside Phase 0 tests in `tests/python/CMakeLists.txt`.
- [x] Write `docs/maya-mapping/phase-1.md`: exact input catalog, adapted differences,
  activation path, override schema example and reserved/unimplemented gestures.
- [x] Run INSTALL through existing CMake tree; CTest `^axismeld_` and Windows verifier.
- [x] Review the complete diff, fix concrete findings, update README to actual capabilities.
- [ ] Commit, fast-forward integration and push; verify matching remote/local hashes.

## Verification commands

```powershell
python tests/python/axismeld_input_test.py
$cmake = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctest = Join-Path (Split-Path $cmake) 'ctest.exe'
& $cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
& $ctest --test-dir D:\source\AxisMeld-build -C Release -R '^axismeld_' --output-on-failure
pwsh -NoProfile -File tools/axismeld/verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
git diff --check
```

## Execution evidence (2026-09-09)

- Implementation: `82fc5257074`; saved-profile recovery fix: `03778ad6eb1`.
- Initial pure/import and installed-module tests failed before implementation.
- INSTALL Release build: exit 0 using the existing VS2026 / CMake build tree.
- Final `ctest -R '^axismeld_'`: 5/5 passed (8 pure cases and 8 Blender integration cases).
- Windows verifier: PASS; product identity and portable profile preserved.
- Independent review found one saved-preference opt-out defect; real-file recreation test
  failed with Move=T while preference=False, then passed with Move=W after correction.
- Scoped re-review: addressed, no remaining Critical/Important findings.
- Export/reimport preserves semantic properties; native user keymap edits survive reload.
- Physical keyboard/mouse, hotbox and splash visual acceptance remain outside this slice.

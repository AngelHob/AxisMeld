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

- [ ] Create `tests/python/axismeld_input_test.py` with unittest cases importing
  `axismeld.commands`, `axismeld.profiles`, `axismeld.keymap` from source scripts/modules.
- [ ] Run `python tests/python/axismeld_input_test.py` and observe missing module failure.
- [ ] Implement `commands.py`: frozen catalog, `baseline_bindings()` returning copies.
  Implement `profiles.py`: `resolve_profiles(layers)` returns bindings, provenance,
  diagnostics; `load_profiles(config_dir, session=None)` reads studio/user in order.
- [ ] Verify real precedence, disable, collision, malformed JSON and baseline immutability.

## Task 2: Built-in preset and semantic adapter

- [ ] Implement `keymap.py: generate_keymaps(base, bindings)` and collision reporting
  without mutating caller data or addon keymaps; preserve other editors and modal maps.
- [ ] Implement `adapter.py: available(context, command)` and
  `run(context, command, invoke=True)`, using native Blender tools, mode and view operations.
- [ ] Add `scripts/startup/bl_operators/axismeld.py` and register in its package list.
- [ ] Add `scripts/presets/keyconfig/AxisMeld_Maya_2026.py` with reload and baseline controls.
- [ ] Add `tests/python/axismeld_input_blender.py`; test actual RNA, tool and mesh transitions,
  keyconfig registration, reload and switch-back using the built executable.

## Task 3: Integration and user-facing handoff

- [ ] Register pure and Blender tests beside Phase 0 tests in `tests/python/CMakeLists.txt`.
- [ ] Write `docs/maya-mapping/phase-1.md`: exact input catalog, adapted differences,
  activation path, override schema example and reserved/unimplemented gestures.
- [ ] Run INSTALL through existing CMake tree; CTest `^axismeld_` and Windows verifier.
- [ ] Review the complete diff, fix concrete findings, update README to actual capabilities.
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

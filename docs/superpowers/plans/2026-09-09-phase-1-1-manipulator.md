# Phase 1.1 Manipulator Implementation Plan

> For agentic workers: execute this tightly coupled native/profile slice in the existing
> isolated workspace; use executing-plans and test-driven-development with review checkpoints.

**Goal:** Select a transform axis once and reuse it for empty-space middle drags.
**Architecture:** Region-local native axis state, narrow gizmo access, native operators,
profile-only event bindings; no replacement geometry engine or Python mouse-move loop.
**Tech Stack:** C++/GTest, Python/bpy event simulation, CMake/CTest, Windows Release.
**Spec:** `docs/design/2026-09-09-phase-1-1-manipulator.md`

## Global constraints

- Maya preset only, Object and mesh Edit Mode; other presets/editors retain upstream behavior.
- Native transform math, cancellation and undo remain authoritative.
- No user configuration changes or event injection into an existing user process.
- F8-F11 initial failure is unconfirmed and not a speculative fix target.
- Existing worktree `D:/source/AxisMeld-phase0`, branch `axismeld/phase-1-1`.

## Task 1: Native state and input routing

Files: `source/blender/axismeld/AXM_transform_axis.hh`, native state tests and CMake;
`scripts/modules/axismeld/keymap.py`, `tests/python/axismeld_input_test.py`.

- [ ] Write failing state tests: fresh state has no axis; selected X persists within a
  context; different object/mode/tool and disabled preset clear; invalid axis does not arm;
  two independent states never share selection.
  Example: `state.update_context(12, 0, 1); state.select(0); EXPECT_EQ(state.axis(), 0);`
  then `state.update_context(13, 0, 1); EXPECT_EQ(state.axis(), -1);`.
- [ ] Compile/run GTest and observe missing feature, then implement the header-only state
  contract `update_context(unsigned object, int mode, int tool)`, `select(int)`, `axis()`, `clear()`.
- [ ] Write a generated-keymap test proving `axismeld.axis_select` precedes click fallback
  and `axismeld.axis_drag` precedes bare MMB transform while preserving Alt bindings.
  Run `python tests/python/axismeld_input_test.py` RED, implement generator changes, run GREEN.

## Task 2: Native gizmo bridge and real event acceptance

Files: `source/blender/editors/transform/transform_gizmo_3d.cc`, `transform_gizmo.hh`,
`transform_axismeld.cc`, `transform_ops.cc`, `CMakeLists.txt`;
`tests/python/axismeld_manipulator_events.py`, `tests/python/CMakeLists.txt`.

- [ ] Create standalone GUI event test using `Window.event_simulate`, scheduled one event
  per timer tick, assertion failures exiting nonzero. With a cube selected and Move active,
  click X, move to empty space, MMB drag diagonally; assert X changed, Y/Z unchanged.
  Run against previous installed executable and record RED.
- [ ] Implement profile/context guards and region-local axis lookup, yellow persistent
  highlighting, click selection with no transform/undo, and explicit idle-axis clearing.
- [ ] Route MMB to the selected native gizmo's operator properties with release_confirm,
  passing the actual MMB event. Preserve native direct drag and Alt navigation.
- [ ] Extend event test with Rotate/Scale, mesh Edit Mode, repeat, cancel, undo, direct drag,
  mode/tool change and preset switch-back. Assert actual geometry/mode, not source text.
- [ ] Build INSTALL Release and run `ctest -R '^axismeld_' --output-on-failure`.
  Run GUI tests in a separate hidden process with `--factory-startup --enable-event-simulate`.

## Task 3: Timing, review and handoff

Files: `tests/python/axismeld_input_benchmark.py`, `docs/maya-mapping/phase-1-1.md`, README.

- [ ] Time 1 cold and 100 warm alternating W/E/R-equivalent native and adapter calls using
  `time.perf_counter_ns()`. Emit median/p95/max separately; label it dispatch-only evidence.
- [ ] Review changes and address concrete findings; re-run affected tests and INSTALL.
- [ ] Document activation, click-axis/MMB sequence, cancellation/undo and remaining differences.
- [ ] Commit verified changes, integrate under the existing route, verify remote/local hash;
  preserve the build worktree and user test executable/configuration.

## Progress

- Baseline: clean branch at `8aba7db983c`; 8 pure input tests passed.
- Implementation has not started when this plan is created.

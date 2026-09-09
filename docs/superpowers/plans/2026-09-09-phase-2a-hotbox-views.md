# Phase 2A Hotbox and View Switching Implementation Plan

> For agentic workers: use subagent-driven-development in this session, with task-scoped review gates.

**Goal:** Deliver the four approved Space/hotbox/view-restoration behaviors in the built AxisMeld Maya preset.

**Architecture:** A pure C++ input state model feeds a native modal overlay and native per-View3D numeric snapshots. A narrow option on the existing quad-view operator preserves the initiating pane. Built-in Python command metadata and profile generation expose the native operators without putting Python in mouse-motion dispatch.

**Tech stack:** Blender C++/RNA/GPU/BLF, bundled Python, CMake/MSVC, GTest, independent event-simulating Blender GUI fixtures.

**Spec:** `docs/superpowers/specs/2026-09-09-phase-2a-hotbox-views-design.md` (authority for detailed H1-H10 behavior).

## Global Constraints

- Only AxisMeld_Maya_2026, VIEW_3D WINDOW, OBJECT or EDIT_MESH; no selection requirement.
- Default tap threshold 0.4 seconds, adjustable 0.1–1.0; equality means hold. Gestures work immediately, without waiting for the threshold.
- N perspective, E side/right, S front, W top. Dead zone 12 logical pixels; exact diagonals select nothing. LMB release commits once, trigger-key release never commits an unfinished gesture.
- The actual keyboard invoke event is the release key; keyboard-only hotbox remapping, disabling, and schema_version=1 compatibility are required.
- Per-View3D runtime numeric snapshots only; no global last-view state, dangling region pointers, saved hidden-pane fields, geometry changes, or geometry undo steps.
- First quad layout: top-left top, top-right user/perspective, bottom-left front, bottom-right right. Preserve an original standard ortho in its matching slot, arbitrary user ortho in user slot.
- Preserve initiating pane on maximize, update only its slot on restore. Keep perspective history per slot and native shared lens/clipping/shading.
- Cancel safely on Esc, focus/context loss, mode/preset changes. No input leaks during hotbox; no automatic reopen from key repeat.
- Guard Local View, locked camera and XR before mutation. Ordinary quad-view orthographic locks are supported.
- Do not modify global Frames/Screen keymaps, transform math, GHOST, user scenes, user preferences, or the running user Blender process.
- GUI tests use a separate hidden factory process with private TEMP/TMP/TMPDIR and BLENDER_USER_CONFIG, with an explicit private-temp guard. Never run a GUI fixture in the user instance.
- Global scaling has no development plan. Phase 1.1 review status remains pending; no push, publish, or integration-branch merge in this plan.
- Build only affected targets, then `cmake --install`; never build the broad INSTALL target.

## Workspace and commands

Existing linked worktree: `D:/source/AxisMeld-phase0`; retain its source/build relationship. Use a local Phase 2A feature branch after the decision/plan commit. Existing build: `D:/source/AxisMeld-build`.

PowerShell variables for commands below (not persisted globally):

```powershell
$axmCmake = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$axmCtest = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
$axmBuild = 'D:\source\AxisMeld-build'
& $axmCtest -C Release --test-dir $axmBuild -R axismeld --output-on-failure
```

Baseline before implementation: seven existing AxisMeld tests must pass. Record task BASE before each task; workers commit only their task files. No concurrent implementation workers or concurrent builds. All new behavior follows failing-test → minimal implementation → passing-test.

## Task 1: Pure hotbox state and hit testing

**Files:** create `source/blender/axismeld/AXM_hotbox_state.hh`, create `source/blender/axismeld/tests/hotbox_state_test.cc`, update `source/blender/axismeld/CMakeLists.txt`.

**Responsibility:** UI-independent timing, interaction consumption, single-shot command selection and release/rearm protection. No Blender context/GPU/timer ownership in this header.

Use namespace `blender::axismeld`. Shared interface for Task 2:

```cpp
enum class HotboxPhase { Idle, Pending, Held, Marking, Cancelled };
enum class HotboxAction { None, ToggleQuad, Perspective, Side, Front, Top, Close };
HotboxAction hotbox_direction(float dx, float dy, float dead_zone);
class HotboxState {
 public:
  bool begin(double now, double tap_seconds, bool is_repeat = false);
  void advance(double now);
  void begin_marking();
  void motion(float dx, float dy, float dead_zone);
  HotboxAction release_mouse();
  HotboxAction release_trigger(double now);
  void cancel();
  HotboxPhase phase() const;
  HotboxAction candidate() const;
};
```

`begin` accepts Idle and a fresh non-repeat press after cancellation; it rejects auto-repeat and reopening an active sequence. Cancellation immediately hides UI at the native layer; pure Cancelled state consumes the matching release without toggling. A fresh non-repeat press represents physical re-press after a lost RELEASE on focus loss. Repeated commands in one hold are permitted, each separate LMB gesture commits at most once. `begin_marking` is called only after the native layer verifies a center hit. `advance` never creates an action. `release_trigger` returns ToggleQuad only from eligible Pending before threshold; all other active releases return Close; idle repeated releases return None. Candidate resets on commit/cancel/release. Validate non-finite inputs safely, never let malformed geometry pick a direction.

**Steps:**

1. Write tests first. Use real state objects and literal actions, no mock event dispatcher. Add a compilable minimal API stub only if needed to observe behavioral RED, then replace stub in GREEN.
2. First test catches missing short-tap transition:

```cpp
HotboxState state;
EXPECT_TRUE(state.begin(10.0, 0.4));
EXPECT_EQ(state.release_trigger(10.2), HotboxAction::ToggleQuad);
EXPECT_EQ(state.release_trigger(10.21), HotboxAction::None);
```

3. Add independent tests for 0.399/0.4/0.401 elapsed (start at zero for exact boundary), repeats not resetting start, immediate marking before timeout, no tap after dead-zone click, Space release before mouse release, Esc/cancel/rearm, repeated gestures, cardinal literal coordinates `(0,40),(40,0),(0,-40),(-40,0)`, dead zone `(3,4)`, diagonal `(40,40)`, DPI-equivalent `(0,30,24)` hit vs `(0,20,24)` miss, NaN/infinity safety.
4. Register the header in SRC and test in TEST_SRC, using existing test infrastructure. Build targeted `axismeld_hotbox_state_test` if generated as that target; inspect generated project names to resolve the actual test target, rather than building all tests.
5. Run `ctest -C Release --test-dir D:/source/AxisMeld-build -R axismeld_hotbox_state --output-on-failure`. Record RED command/output, GREEN command/output, and target name in the report.
6. Run existing native AxisMeld identity/transform-axis tests. Format with `lib/windows_x64/llvm/bin/clang-format.exe -i` on changed C++ only; `git diff --check`; commit task files.

**Acceptance:** H1-H3 pure-state portions and rearm portions pass. This task alone is not a usable hotbox and must not alter installed user behavior.

## Task 2: Native hotbox, view snapshots and narrow quad-view seam

**Files:** create `source/blender/editors/space_view3d/view3d_axismeld_hotbox.cc`, create `source/blender/editors/space_view3d/view3d_axismeld_views.cc`, create `source/blender/editors/space_view3d/view3d_axismeld.hh`; update that directory's `CMakeLists.txt`, `view3d_ops.cc`, `space_view3d.cc`; update `source/blender/makesdna/DNA_view3d_types.h`, `source/blender/editors/screen/screen_ops.cc`; create `tests/python/axismeld_hotbox_events.py`, create `tests/python/axismeld_hotbox_ui_runner.py`, update `tests/python/CMakeLists.txt`.

**Inputs:** Task 1's HotboxState API. Existing `transform_axismeld.cc` demonstrates preset/context checks. Existing manipulator GUI runner demonstrates private-temp safeguards. Do not change manipulator semantics.

**Interfaces:**

```cpp
// view3d_axismeld.hh; editor-private, no general-purpose framework.
void VIEW3D_OT_axismeld_hotbox(wmOperatorType *ot);
void VIEW3D_OT_axismeld_view(wmOperatorType *ot);
bool axismeld_view_context_poll(bContext *C);
bool axismeld_view_action(bContext *C, wmOperator *op,
                          blender::axismeld::HotboxAction action);
void axismeld_view_cache_free(void *cache);
```

Register `VIEW3D_OT_axismeld_hotbox` with float RNA `tap_seconds` (0.4, range 0.1–1.0), native invoke/modal/cancel; no UNDO or Python in motion. `VIEW3D_OT_axismeld_view` has enum `action` with `TOGGLE_QUAD`, `PERSPECTIVE`, `SIDE`, `FRONT`, `TOP`; native execute, no UNDO. Both guard the preset and context. Hotbox actual invoke event type is saved, so Task 3 can remap through the semantic adapter.

In `view3d_main_region_init`, ensure and attach empty `AxisMeld Hotbox` keymap (SPACE_VIEW3D, RGN_TYPE_WINDOW) immediately before the existing Frames handler. Its default map stays empty; Task 3 populates only this preset's instance. Ordinary 3D View is after Frames and cannot own Space reliably. Task 2 temporary native fixture binding must use this new map. Do not move existing handlers or modify global Frames data. Operator poll limits modes/presets.

Add dedicated `void *axismeld_view_cache` and free callback to View3D_Runtime (or equally narrow typed runtime ownership if compiler constraints favor it). Release in `view3d_free`; duplicate/read zero the runtime as native code already does. Cached snapshots own numeric view data only, including axis/history/lock fields, and four logical slots. No raw region pointer lives in cache. Active modal source pointers must be verified against live window/screen/area/region lists before dereference; draw callback checks it is drawing its captured live source.

Minimal seam: native `SCREEN_OT_region_quadview` boolean property `preserve_active_view`, default false, skips the existing locked-ortho-to-user-region swap when true. AxisMeld invokes it with true in the initiating region override; native default paths unchanged. Reuse native region duplication/removal. Resolve resulting physical pane order correctly from native quad region order/layout (verify actual rectangles in tests); do not assume the desired slot order already matches upstream.

**Steps:**

1. Add independent hidden GUI runner first. Copy only the minimal isolated-process harness pattern from the existing runner, not its test logic. Set all private temp/config environment variables before launch, check `bpy.app.tempdir` is under the private root before any scene operations, never touch the user process. Windows StartProcess helpers hidden if used. Tests must fail before implementation because native operator RNA is absent (`get_rna_type`, not `hasattr(bpy.types,...)`).
2. Initial literal behavioral fixture: create factory scene in private process, load AxisMeld preset without writing prefs, record original view and object matrices/vertex coordinates/selection. Invoke view action through native RNA. Assert four WINDOW regions; their rectangle-relative directions are TL top/TR user/BL front/BR right. Maximize each region including locked orthos, assert exactly one region and its original pose. Modify ofs/dist in single view, restore four and assert only that slot changed. Use explicit fixture values, not a helper derived from production logic.
3. Implement numeric snapshot helper and scene/topology invalidation. Cache stores a current Scene identity to detect scene changes without dereferencing a stale scene, a topology signature from live list and layout state, selected logical slot and per-slot perspective pose. New region topology outside AxisMeld invalidates safely. Do not retain hidden snapshots across file load. Finish any native smooth-view animation before capture/apply. Axis switching must target actual initiating region; native `view_axis` can retarget locked ortho panes, so do not use it blindly.
4. Implement view semantics from spec: preserve ofs/dist and native view history; restore perspective pose when available; clear only quad locks in single view and restore on quad. First layout uses all original center/dist with standardized unused directions. Unsupported Local View/camera-lock/XR rejects before topology change. No camera/geometry mutations.
5. Add TDD GUI cases for 20 round trips, two areas/two windows isolation, perspective round trip, arbitrary user ortho, empty selection, no geometry/undo changes, unsupported contexts, scene changes, manual quad topology, save/reopen and space duplication. Test independent-process cleanup and exit status, not source-text patterns.
6. Implement modal lifecycle using Task 1. Capture source and center on invoke. Install native region draw callback and timer; remove both on every exit, also `cancel`. No required hold delay before center or marking. A central LMB press starts marking with the press point as gesture origin, which remains fixed. Active gestures consume mouse/Alt input. Release matching trigger key closes; exact threshold long hold. Esc/context loss cleans immediately, retain minimal release suppression if needed; key repeats must not create a second operator. Other active tools must not be preempted.
7. Draw compact AxisMeld center and four labels with BLF/GPU native UI scaling. Same coordinate/origin/dead-zone function drives candidate highlight and selection. Clip drawing to source region, clamp initial center so readable labels fit where practical without moving the gesture origin after press. No external font/image/menu resources, no permanent panels.
8. Extend GUI event fixture for tap/hold/fast LMB cardinal gestures/dead zone/cancel/autorepeat/trigger remap through the temporary isolated `AxisMeld Hotbox` test keymap. Assert view changes and region counts, not only operator calls; verify viewport hotbox does not start animation while timeline Space still does. Clear temporary test bindings before exit. These tests must run before production keymap connection, so explicitly install the fixture's native bindings. Failed commands never become layout taps.
9. Build only `blender` and changed test targets, config Release parallel 8, with log in build directory. Windows raw bin/Release exe lacks the installed side-by-side dependencies. Stage with `cmake --install D:/source/AxisMeld-build --config Release --prefix D:/source/AxisMeld-build/phase2a-test-install`; run the native-state test and new GUI runner against that staged executable. Run existing Blender integration and manipulator runners against the same staged executable (CTest's configured install path otherwise tests the old build). Do not update the normal `install` directory until Task 3 connects and verifies the product.
10. Format changed C++ only, `git diff --check`, commit task files. Report exact tested behaviors and evidence limits (synthetic event tests do not prove subjective visual latency).

**Acceptance:** Native H1-H7/H9-H10 behavior verified in isolated GUI process; production preset still lacks SPACE until Task 3. Task 3 owns profile/UI wiring and end-to-end product-keymap proof.

## Task 3: Built-in command/profile connection and testable build handoff

**Files:** update `scripts/modules/axismeld/commands.py`, `adapter.py`, `profiles.py`, `keymap.py`, `runtime.py` only where necessary; update `scripts/startup/bl_operators/axismeld.py` and `scripts/modules/bl_keymap_utils/keymap_hierarchy.py`; update `tests/python/axismeld_input_test.py`, `axismeld_input_blender.py`, `axismeld_hotbox_events.py` and its runner's traceback check if needed; update command mapping and architecture docs at their existing paths, README and phase report only as warranted; create `docs/compatibility/phase-2a-manual-test.md`.

**Inputs:** Native operators from Task 2, with properties exactly as specified there. Existing module directory verified as `scripts/modules/axismeld`; change the existing files in place, never create a duplicate module tree.

**Interfaces:** Command.key becomes `str | None` (None default), unbound menu commands remain valid known semantic IDs. Add IDs `hotbox.open`, `view.toggle_quad`, `view.perspective`, `view.side`, `view.front`, `view.top`. Only hotbox.open has default SPACE. baseline_bindings returns only bound commands. Profile validation recognizes all COMMANDS, can assign bindings to initially unbound IDs, allows disabling by null, retains schema_version=1, rejects mouse-type hotbox.open before changing a layer. Preset FloatProperty `hotbox_tap_seconds` default0.4/min0.1/max1.0 is passed once by adapter to native `tap_seconds`.

**Steps:**

1. RED pure configuration tests for defaultSPACE hotbox, no phantom bindings for menu-only commands, remapping to a valid keyboard key, disabling, invalid mouse-trigger override rolling back only its config layer, old minimal schema1 payload unchanged, and duplicate/global conflict handling. Native Blender config tests verify the real new operators can be invoked through semantic adapter and real installed preset bindings.
2. Implement metadata/validation and adapters. Forward actual invoke event semantics via native INVOKE_DEFAULT; do not hardcode Space on release, and no Python modal. View actions call native enum actions. Keep old scene/modeling checks and existing tool behavior. Hotbox alone targets the new `AxisMeld Hotbox` map (SPACE_VIEW3D, WINDOW), not a duplicate in Object/Mesh or ordinary 3D View; other view actions retain 3D View target. Add the map to generated preset data and scoped conflict inspection.
3. The real upstream collision is unmodified PRESS Space in Frames/screen.animation_play, and the native 3D-region Frames handler precedes ordinary 3D View. Task 2's dedicated pre-Frames map resolves this without deleting global data. Permit only the exact hotbox.open Space-vs-original-Frames-play pair in validate_global_bindings; continue rejecting all other collisions. Test the native order with real events; global Frames/Screen data must remain identical. RESERVED_KEYS no longer owns Space separately once hotbox owns it.
4. Add preference field to existing preset preferences and show accurate supported/adapted status; replace only now-obsolete 'hotbox not implemented' descriptions. Fix the existing verified preferences-draw error by accepting `draw(self, layout)` directly, not `self.layout`; current caller rna_keymap_ui passes a UILayout, not a context. Add the new hotbox map to the 3D View keymap hierarchy, with a narrow dynamic entry only when the effective map has bindings to avoid empty AxisMeld rows in other presets. Preserve unrelated preferences, optional-file overrides and public-default/personal-config separation. Test actual KEYMAP preferences drawing in the private GUI and reject Python draw tracebacks even when Blender's process exits0. Include hotbox native-edit/reload/export roundtrip.
5. Change hotbox GUI tests to use actual product preset keymaps (remove Task 2's temporary test binding), including remap+disable with isolated settings. Assert default shortSpace toggles once, heldSpace directions, changing preset disables hotbox, other editors/active modal tools untouched and existing W/E/R remains covered by manipulator regression. Run native AxisMeld CTests; run the same CLI identity, portable paths, input profiles, installed-input Blender script, manipulator and hotbox GUI runners explicitly against phase2a-test-install/blender.exe. Record each command and result; configured whole CTest still targets the old install directory and cannot substitute for this new-build validation. Do not reconfigure CMake concurrently with another build or rewrite CTest files to mask executable selection.
6. Document exact implemented slice and remaining Maya differences. Add Chinese hand-test table: tap quad/maximize eachpane/restore navigation; four menu directions; fast gesture; hold without selection; remap/disable; Esc; unsupported modes. Explicitly say Global scaling unchanged/no development plan and hidden single-view slots not saved across restart. Preserve Phase 1.1 pending review status.
7. Re-stage updated scripts with `cmake --install D:/source/AxisMeld-build --config Release --prefix D:/source/AxisMeld-build/phase2a-test-install`; verify staged exe hash matches built exe and run isolated installed smoke using staged scripts, not source-script overrides. Deliver that separate runnable directory. The existing normal install/blender.exe was observed running in a user session; do not overwrite it, close it, or copy its preferences. The staged portable directory provides separate preferences. Do not claim visual smoothness or full Maya parity from synthetic tests.
8. `git diff --check`, commit task files; report RED/GREEN commands, installed smoke evidence, exact executable location and outstanding manual tests. Independent task review, then whole-branch review over this plan's implementation commits, no integration merge/push.

**Acceptance:** H1-H10 covered by explicit tests or honestly listed manual limits; no undocumented partial user-facing feature. A locally built hand-test deliverable is not approval to merge into integration.

## Final review closure: native navigation and small acceptance gaps

The final review reproduced BOXCLIP degeneration after an AxisMeld TOP-to-SIDE action followed by native `view3d.zoom`: native navigation reaches the shared clipping helper without passing the AxisMeld-only refresh guard. Extend the existing last-valid-volume contract to that real navigation entry point. Keep the guard local to AxisMeld-controlled view state and preserve unrelated presets' native behavior; reuse one contributor-completeness check rather than duplicating clipping mathematics. No global keymap, GHOST, geometry or transform changes.

Write a real native zoom regression before the correction, including missing TOP and missing FRONT contributors, last-valid planes through navigation, and recalculation after contributors return. Exercise native pan where it shares this path. Do not substitute direct RNA assignments for these navigation events. Preserve independent user clipping and native linked-navigation/lock semantics.

In the same single final fix wave, strengthen the pure cancellation test with a live marking candidate, and replace the preset's hardcoded Space wording with trigger-key-neutral text. Retain the disclosed edge-label cropping and baseline PNG warning; neither requires new feature work. Build affected targets, restage only the separate test installation, run covering native/installed/GUI tests, and record evidence before scoped re-review. Original install and integration branch remain untouched.

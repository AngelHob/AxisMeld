# M1 Q/W/E/R Tool Hotboxes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver usable Q/W/E/R + held LMB tool marking menus, sharing the existing native hotbox renderer and command bridge.

**Architecture:** Keep the schema-1 key binding PRESS event as the activation event; paired release ownership belongs to a native tool-menu session, not a second user binding. Extend the existing native hotbox with a validated tool-root mode and optional declarative menu layout metadata. Tool commands from menus/EXEC remain immediate and never arm a keyboard session.

**Tech Stack:** Blender C++ / Python / CMake / CTest / Windows hidden GUI event replay.

**Spec:** `docs/superpowers/specs/2026-09-11-modeling-interaction-alignment-design.md` (approved by user before this plan).

## Global Constraints

- UV 整体后置：编辑器、快捷键、热盒、选择、工具和算法都不提前改造。
- Global 物体缩放差异继续搁置，不因统一变换菜单而重新开发。
- 快捷键、Space 热盒目录、工具 marking 菜单和普通菜单引用同一稳定 command ID。
- 常用方向动作放紧凑、同组等宽的 marking 热盒；设置、选项和深目录用 Blender 原生菜单。
- 普通子菜单贴父入口，父级保持显示；子菜单活动时背景无关热盒不参与命中。
- 一级继续使用个人外观设置及默认 75% 不透明度；二级及以下原生样式且完全不透明。
- 不把 W/E/R 的单次选工具延迟到长按超时；不把键盘自动重复当作多次打开菜单。
- 更新现有测试入口，不新增整套 build；保留回退版和个人配置。
- This plan implements M1 only. M2 right-click and M3 complete modeling command coverage remain separate subsequent slices.

## Baseline and Maya source evidence

Baseline `ce3c318d188`, linked worktree `D:/source/AxisMeld-phase0`, branch `axismeld/phase-2a`; 47 Python tests pass.
Installed Maya source directory: `C:/Program Files/Autodesk/Maya2026/scripts/others`.
Read behavior/metadata only; never copy Autodesk implementation code into the repository.

- `buildSelectMM.mel`, `buildTranslateMM.mel`, `buildRotateMM.mel`, `buildScaleMM.mel`: switch tool on key press and install LMB marking popup.
- `buildToolOptionsMM.mel`: tool-specific content; Modeling Toolkit may supply its own variant. This first implementation targets the standard tool-menu definitions, not a claim of every toolkit variant.
- `selectMarkingMenuImpl.mel`: NW Marquee, NE Drag, W Paint, SW Lasso, E Camera Based, SE Clear; N Symmetry, S Select.
- `translateMarkingMenuImpl.mel`: W World, NW Object, NE Normal Average, SE Keep Spacing; N Symmetry, S Select, E Snap, SW Axis.
- `rotateMarkingMenuImpl.mel`: W World, NW Object, NE Normal Average, E Gimbal, SE Discrete Rotate; N Symmetry, S Select, SW Custom Axis.
- `scaleMarkingMenuImpl.mel`: W World, NW Object, NE Normal Average, E Discrete Scale, SE Relative; N Symmetry, S Select, SW Axis.
- `commonReflectionOptionsPopup.mel`, `commonSelectOptionsPopup.mel`: shared N/S option groups. They should open normal setting lists under the approved combination convention.
- `destroySTRSMarkingMenu.mel`: same-tool key tap can reset active handle; leave existing AxisMeld tap behavior unchanged in this slice and explicitly record this adaptation.

## Task 1: End-to-end tool marking menu integration

This is one coupled deliverable: Python capabilities, strict snapshot parser, native layout and input ownership cannot ship independently. The controller separately maintains Maya mapping and the acceptance report while the implementer owns code and tests.

**Files:**
- Modify: `scripts/modules/axismeld/commands.py`, `adapter.py`, `hotbox_catalog.py`, `hotbox_runtime.py`; modify `keymap.py` / `scripts/startup/bl_operators/axismeld.py` only for the keyboard-invoke distinction and safe repeat handling when needed.
- Create: `scripts/modules/axismeld/tool_hotbox.py` for narrowly scoped tool-menu metadata / native setting adaptation if needed to keep existing modules focused.
- Modify: `source/blender/axismeld/AXM_hotbox_menu.hh`, `intern/hotbox_menu.cc` for optional node direction/presentation and standalone root layout using the current ellipse/native-list builder.
- Modify: `source/blender/editors/space_view3d/view3d_axismeld_hotbox{,_model,_draw}.cc`, `view3d_axismeld_hotbox_internal.hh` for an explicit tool-root RNA parameter, invisible armed state, shared draw/hit ownership and strict decoding.
- Tests: new `tests/python/axismeld_tool_hotbox_test.py`, `tests/python/axismeld_tool_hotbox_events.py`; add runner suite `tools` in `axismeld_hotbox_ui_runner.py`; extend native `source/blender/axismeld/tests/hotbox_menu_test.cc` and `source/blender/editors/space_view3d/tests/hotbox_model_test.cc` (verify actual existing test path before editing).
- Keep build outputs and logs in existing `D:/source/AxisMeld-build`, prefix `m1-tools-`.

**Interfaces and behavior:**

1. New optional operator string `tool_menu` defaults empty (the unchanged Space behavior). Accept only registered Q/W/E/R tool roots. No arbitrary command evaluation.
2. Keyboard-invoked Q/W/E/R switches the native tool immediately, then arms its menu using the actual resolved event type. EXEC/menu command dispatch only switches the tool. A remapped key works; disabled binding does not arm; baseline and personal file schema do not change.
3. Armed but not shown: no draw, no scene mutation from pointer movement, no deferred tool switch. LMB press without Alt/other navigation modifiers opens at that mouse position and owns the drag. Modifier navigation and unrelated actions must leave the armed session safely and pass through; keyboard repeats never stack modals.
4. Shown: standalone compact ring with no extra center button, default Blender opaque style, drag guide and fixed Maya directions; normal setting lists retain the ring and isolate background hits. LMB release selects at most once, closes the tool overlay (or returns to invisible armed state only if proven safe), and release of the trigger never toggles quad or reselects Q over a chosen Lasso tool. Release trigger first cancels the pending gesture and drains only owned remaining release. Escape / lost context / focus loss do not leave stale state. Existing Space hotbox remains unchanged.
5. Menu roots are reachable from a normal Tool Settings submenu under Modify in the Space catalog, preserving existing immediate Move/Rotate/Scale entries. No fifth snapshot root. New root nodes stay within existing 256-node budget. Preserve existing mappings and old snapshot compatibility.
6. If adding metadata, accept only optional `direction` in N/NE/E/SE/S/SW/W/NW and optional menu `presentation` in radial/list; reject duplicates in one ring, invalid types/values and illegal placement. Append C++ aggregate fields so old tests remain compatible. Native list metadata replaces hardcoded ID reliance for the new menus; no broad refactor of unrelated menus.
7. Minimal real actions: Marquee -> native box select, Lasso -> native lasso tool, Paint -> native circle selection (explicitly adapted), Clear -> native deselect current Object/Mesh Edit set without automatic mode switch. World/Object/Normal/Gimbal use native orientations, with Gimbal only offered for Rotate. Use actual per-tool orientation slots if supported by both gizmo and AxisMeld axis drag; otherwise explicitly document shared Blender orientation rather than silently claiming independent Maya state.
8. Other first-level Maya entries have their verified labels/positions and disabled planned children where no mapping is implemented yet. Distinguish lack of equivalent capability from a native capability awaiting adaptation. Each placeholder reason includes stable plan code `M1-Pxx`; the controller records these in the mapping document. Preserve UV-related options only as deferred placeholders, never change UV state.
9. Settings/list menu children may initially contain a bounded subset plus explicit missing entries; do not invent new Maya directions. Blender-only orientation View may live in Axis/Custom Axis normal settings, clearly named View (Blender), never taking a Maya marking slot.
10. New commands are registered in COMMANDS, runtime allowlist, catalog policy and native parser together, initially without new default keys. `status='adapted'` with concrete differences. Selection actions preserve native child undo and FINISHED/CANCELLED/PASS_THROUGH. No global wrapper UNDO. Display active setting state if adding checked metadata; otherwise report missing check marks as a UI limitation rather than false state.

- [x] **Step 1: Write focused failing behavioral tests.**

Example pure test shape (use the actual exported catalog helper after choosing its stable name):
```python
menus = hotbox_catalog.default_catalog()
nodes = {n['id']: n for n in walk(menus)}  # walk is a test helper, no production call
self.assertIn('tools.move', nodes)
self.assertEqual({n['direction']: n['label'] for n in nodes['tools.move']['children']
                  if 'direction' in n},
                 {'W': 'World', 'NW': 'Object', 'NE': 'Normal Average',
                  'SE': 'Keep Spacing', 'N': 'Symmetry', 'S': 'Select',
                  'E': 'Snap', 'SW': 'Axis'})
```
Add serializer/parser rejection and behavior tests: invalid direction, duplicate direction, old snapshot accepted, malformed snapshot rejected without mutation. Layout tests use literal expected directional sides, equal dimensions, no center target, retained parent and blocked unrelated background hits for a native child.

- [x] **Step 2: Run tests and capture expected RED.**
```powershell
& C:/Python314/python.exe -m unittest discover -s tests/python -p axismeld_tool_hotbox_test.py
```
Expected missing tool roots / unsupported metadata assertion; avoid import-error-only proof.

- [x] **Step 3: Add minimal catalog and adapters, then native integration.**
Use the existing semantic dispatch:
```python
# keyboard invocation only; menu/EXEC never enters this branch
result = bpy.ops.wm.tool_set_by_id('EXEC_DEFAULT', name=TOOLS[command], cycle=False)
if result == {'FINISHED'} and keyboard_tool_session:
    return bpy.ops.view3d.axismeld_hotbox('INVOKE_DEFAULT',
        menu_json=hotbox_runtime.snapshot(context), tool_menu=tool_root)
return result
```
Determine `keyboard_tool_session` from the invoking event in the wrapper (not from `invoke=True` alone, because menu replay uses that). Register native property with hidden/skip-save flags. Before adding the modal, check existing modal/UI handlers. Keep invisible armed state out of layout/draw; initialize displayed root only on owned LMB. Share existing source-live checks, close guard, renderer and list hit isolation.

- [x] **Step 4: Run GREEN and real GUI event sequences.**
Use `win.event_simulate` following the isolated existing event suites:
```python
win.event_simulate(type='W', value='PRESS', x=cx, y=cy)
yield from settle()
check(current_tool() == 'builtin.move', 'W must select immediately')
win.event_simulate(type='LEFTMOUSE', value='PRESS', x=cx, y=cy)
yield from settle()
# Drag to a rendered World target, release LMB then W; assert orientation and no modal.
```
Test all four tools, tap/no popup, actual alternate tool selection, trigger-first cancel, Esc with held mouse/key, auto repeat, modifier navigation, remapped key, scene changes, Object/Edit, single/quad, disabled target no execution, Space regression and W/E/R after closing without moving mouse. Use private factory scenes and never user configuration. Save actual screenshots for root ring and native child for visual review.

- [x] **Step 5: Build, verify, self-review and commit.**
```powershell
& 'C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' --build D:/source/AxisMeld-build --config Release --target blender editor_hotbox_hotbox_model_test axismeld_hotbox_menu_test -- /m:4
& C:/Python314/python.exe -m unittest discover -s tests/python -p 'axismeld_*test.py'
& 'C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe' --test-dir D:/source/AxisMeld-build -C Release -R '^(axismeld_(hotbox_menu|hotbox_state|identity|transform_axis)|editor_hotbox_hotbox_model)$' --output-on-failure
```
Use candidate `phase2b-ui-test-install/blender-opacity-check.exe` with source resources, not a new install directory; coordinate candidate copy with controller. Run `tools`, `menus`, `native-style`, `release`, `selection`, `appearance` suites serially. Controller performs independent final delivery hashes and installed run. Do not overwrite primary installed blender.exe or personal configs in the implementation task.

## Controller delivery checkpoint

- [x] Inspect task report, task-scoped review and any fixes; then whole-slice review.
- [x] Update Maya mapping / placeholder backlog and concentrated manual acceptance table.
- [x] Verify no running user Blender before updating existing installed executable and only changed bundled modules; retain fallback and hash personal files before/after. If running, keep candidate and ask user to exit without killing it.
- [x] Report precisely which M1 features work, remaining adaptation differences, and that M2/M3/UV are not completed.

Delivery: see [M1 acceptance](../../compatibility/2026-09-11-m1-tool-hotboxes.md). Eight installed GUI suites passed; manual acceptance remains open. No merge or remote push was performed.

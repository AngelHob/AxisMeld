# Hotbox Mapping Lists Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development task-by-task with independent review gates. The user authorized a five-hour batch with deferred consolidated manual review. Do not start this plan's implementation until the short-settings plan's final review completes.

**Goal:** Browse the three center mouse-button mappings through continuous native menus, with all 13 existing choices reachable in narrow panes.

**Architecture:** Extend the existing pure layout and draw-only native adapter. Add an explicit standalone-entry flag to the C++ layout result so native submenu rows can share a background while hotbox entries stay separate. Reuse existing owner offsets, scroll IDs, input ownership and settings persistence; no popup input handlers.

**Tech Stack:** Blender C++, GTest, existing isolated Python GUI runners. No dependencies.

**Spec:** [Combination convention](../../design/hotbox-menu-composition.md), [batch scope](../../development/2026-09-10-five-hour-batch.md), and [mapping preflight](../../development/2026-09-11-mapping-list-preflight.md). This plan resolves the preflight's candidate choices below.

## Global Constraints

- Primary height 38, central side gaps 83.6, secondary height 24, secondary gap 4, popup separation 10 logical px unchanged.
- Preserve the parent hotbox and immediate owner entry. Retain the Views real-origin 12px exclusion and all existing short-list behavior.
- Add only `center.controls.buttons`, `center.controls.buttons.leftmouse`, `center.controls.buttons.middlemouse`, `center.controls.buttons.rightmouse` to explicit native-list classification.
- All 13 existing choices and default mappings remain unchanged. No JSON schema, configuration file format or keymap changes. Permitted modal edits are Task 1 scroll offset normalization and Task 2 disabled-native-scroll press classification through existing navigation_consumed; no new handlers or release mechanism.
- The three mouse-button submenu rows form one native block with submenu arrows. Their final setting leaves form one continuous native block.
- Full list when it fits. Only the 13-choice mapping lists can paginate; use 24px up/down navigation rows and at least one choice, with disabled boundary arrows. Scroll one item per existing offset action.
- Navigation uses existing `@scroll:<owner>:previous/next` IDs and never reaches the command/setting dispatcher. Existing wheel and release ownership remain the implementation.
- Reuse the existing UI-test stage, keep the fallback untouched, and preserve/check all portable files. No new full installation, no deleting builds, no push or merge.
- All actual GUI tests are serialized in private temporary configurations. No user session shutdown. Stop new implementation at the batch's consolidation boundary.

## Task 1: Explicit native blocks and bounded mapping pages

**Files:**

- Modify `source/blender/axismeld/AXM_hotbox_menu.hh`.
- Modify `source/blender/axismeld/intern/hotbox_menu.cc`.
- Modify `source/blender/editors/space_view3d/view3d_axismeld_hotbox_draw.cc`.
- Modify `source/blender/editors/include/UI_menu_overlay.hh`.
- Modify `source/blender/editors/interface/interface_menu_overlay.cc`.
- Test `source/blender/axismeld/tests/hotbox_menu_test.cc`.
- Review-fix only: `source/blender/editors/space_view3d/view3d_axismeld_hotbox.cc` scroll offset calculation.

**Interfaces:** Keep `layout_menu(...)` signature. Append defaulted fields, not serialized settings:

```cpp
// MenuRect, following native_menu:
bool native_menu_standalone = false;  // Native entry placed on a hotbox, not inside a list.
// ui::MenuOverlayItem, following submenu:
int icon_only = 0;  // ICON_NONE; nonzero requests a native icon-only navigation row.
```

- [x] Add geometry tests before production changes. Use `default_snapshot()`, existing `rect()` and `measured()` helpers. One large-pane example:

```cpp
auto snapshot = default_snapshot();
const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540,
    {"center.controls", "center.controls.buttons",
     "center.controls.buttons.rightmouse"}, {}, measured(snapshot));
ASSERT_TRUE(layout.supported);
const auto *entry = rect(layout, "center.controls.buttons");
ASSERT_NE(entry, nullptr);
EXPECT_TRUE(entry->native_menu);
EXPECT_TRUE(entry->native_menu_standalone);
const auto *button = rect(layout, "center.controls.buttons.rightmouse");
ASSERT_NE(button, nullptr);
EXPECT_TRUE(button->native_menu);
EXPECT_FALSE(button->native_menu_standalone);
EXPECT_EQ(rect(layout, "@scroll:center.controls.buttons.rightmouse:next"), nullptr);
```

  Repeat the mapping-page contract for all three mouse owners. Count all 13 leaves, equal x/width,
  contiguous 24px rows, native true and standalone false. Check the three parent submenu rows also
  share equal x/width and contiguous geometry with native true/standalone false.

- [x] Add narrow page traversal tests with real-ish label widths (`node.label.size() * 7.0f`) as well as the existing independent widths. Try 392×212.5 and 480×320, center and corner invocations. Traverse offsets from 0 through 12 and collect visible mapping IDs; require the union of all 13 IDs. Check every emitted rectangle stays within margins, choices remain 24px, and the immediate entry is separated by at least 10px. Use a central `center.controls` mapping to avoid depending on a hidden primary-row title.

- [x] Cover first/last disabled arrows, no arrows when all items fit, negative/oversized offsets, and an open mouse submenu after its ancestor offset changes. Do not use an unsupported layout as a successful reachability test. If a prescribed size is truly impossible with actual targets, report the concrete conflict before changing the contract.

- [x] Build/run only `axismeld_hotbox_menu_test` for RED. The initial new-field compilation failure is acceptable for that interface assertion; then retain a semantic RED proving the old mapping ellipses/non-contiguous rows before changing their layout. Save both evidence types distinctly.

- [x] Extend explicit classification and keep scrolling limited to the three mapping owners:

```cpp
bool mapping_list(const std::string &id)
{
  return id == "center.controls.buttons.leftmouse" ||
         id == "center.controls.buttons.middlemouse" ||
         id == "center.controls.buttons.rightmouse";
}
// native_list additionally accepts center.controls.buttons and mapping_list(id).
```

  Every native entry emitted by `ellipse(...)` gets standalone=true. Entries emitted inside
  `popup(...)` remain standalone=false, including child Menu nodes. Native popup widths use
  label+60 for Menu children and label+40 for Setting children.

- [x] Extract the existing native popup placement into a private `LayoutBuilder` helper returning success and x/y outputs. Preserve exact right/left/up/down order, clamping, margins and Views-only origin test. Its inputs are the immutable anchor, desired width/height, and whether to apply the origin exclusion. Do not move the owner entry or change short-list fallback.

- [x] For mapping owners, try content capacity from all children down to one. Compute height and attempt placement for each capacity; retain the first fit. Short lists try only their full count:

```cpp
const bool paged = capacity < count;
const float h = (capacity + (paged ? 2 : 0)) * secondary_height;
const int first = paged ? std::min(offset(owner.id, count), count - capacity) : 0;
// Open child menus must be visible: adjust first within [0, count - capacity] if next names one.
```

  A paged column is top previous row, `capacity` content rows, bottom next row. All share x/width,
  native=true, standalone=false and height24; arrows are interactive only when scrolling can move.
  Emit the existing navigation IDs, with no fake MenuNode or new dispatcher route. If no capacity
  fits safely, return unsupported with no partial active layout.

- [x] Change the renderer block split condition from node Menu-kind to `native_menu_standalone`.
  Keep `node.kind == MenuKind::Menu` solely for the native submenu-arrow appearance. Preserve
  depth ordering and continuous list backgrounds, including the scroll rows.

- [x] Display native navigation with Blender `ICON_TRIA_UP` / `ICON_TRIA_DOWN`, not textual angle brackets. Pass `icon_only` only for native `@scroll` rows; ordinary native mapping leaves must keep their labels even when `menu_icon()` would return an icon. All other menu overlays keep icon_only=0. In the draw-only adapter, nonzero `icon_only` selects `uiDefIconBut(... ButtonType::But, item.icon_only, ...)`; otherwise preserve the existing submenu/text constructors. Hover/disabled flags apply uniformly. No handlers or callbacks.

- [x] Run all native layout tests GREEN, format only changed C++, and build `blender` plus the native target. Do not install yet: Task 2 needs the old short-menu stage for a GUI RED. Self-review and local commit only owned files; report exact interface decisions, test logs and any unresolved placement limitations.

### Task 1 review correction: wheel-tail normalization

Independent review of `b93e8266e77` found a deterministic contract defect: displayed first index clamps
to `count-capacity`, but `scroll_owner()` stores up to `count-1`. For capacity5/count13, repeated down
can store12 while displaying8; a single up then still displays8. This is not a user preference.

- [x] Add RED tests for the offset transition that the real event path will call: capacity greater than1,
  repeated down at the tail, one up moving exactly one visible row; first-page reverse boundary; stale
  negative/oversized offsets; full-list wheel no drift; legacy ellipse behavior preserved.
- [x] Publish native mapping page scroll bounds/effective first through the pure layout result, or an
  equivalently small shared pure helper; use the same tested transition from `scroll_owner()`.
  Normalize against the displayed page before applying delta. Do not independently recompute capacity
  from viewport size in the event code, duplicate mapping ID classification there, or scan user geometry.
- [x] Limit extra public C++ layout state to this scroll calculation. No JSON or new input state, handlers,
  release/press ownership, global guards or persistence changes. Legacy ellipse offsets retain their
  existing behavior. Existing descendants-close behavior on owner scroll remains intact.
- [x] Re-run the covering native tests and build blender, still no install/GUI. Report exact event callsite
  integration and RED/GREEN; Task 2 must additionally verify the same contract with real mouse wheel
  events in actual paged panes before the whole slice is complete.

## Task 2: Actual nested menus, scrolling and persistence

**Files:**

- Modify `tests/python/axismeld_hotbox_geometry_fixture.py`.
- Modify `tests/python/axismeld_hotbox_native_style_events.py`.
- Modify `tests/python/axismeld_hotbox_menu_events.py`.
- Modify `tests/python/axismeld_hotbox_ui_runner.py`.
- Evidence-backed fix only: `source/blender/editors/space_view3d/view3d_axismeld_hotbox.cc` disabled native navigation press handling.

**Interfaces:** Use Task 1's 24px continuous list, submenu padding60/leaf padding40, optional up/down rows and one-item offsets. Geometry helpers only provide event coordinates; expected setting values remain independent test literals. No production changes in this task without demonstrated evidence and controller review.

- [x] Extend the label-driven native fixture to produce paged geometry (`items`, `previous`, `next`, `capacity`, `first`), preserving `native_list(...)` and `style_list(...)` compatibility for current short tests. Include immediate-owner avoidance and whole-column placement before choosing a page capacity.
- [x] Add `Center Mouse Buttons` to ellipse entry padding, use the native submenu column for Left/Middle/Right, and native pages for the 13 choices. Update existing menu inputs while preserving every existing setting/dispatch/release assertion.
- [x] Add runner suite `mappings` that uses `axismeld_hotbox_native_style_events.py` and requires its distinct `AXISMELD_HOTBOX_MAPPING_LISTS_PASS` marker. Reuse the existing narrow/quad layout setup, factoring a small shared setup helper only if needed. Keep native-style default and short-list probes intact. Existing hidden startup/private TEMP/timeout and failure checks stay unchanged.
- [x] Add actual mapping paths for all three mouse buttons. In standard view show all choices and verify continuous submenu-row backgrounds, three native arrows, list label completeness, hover and parent separation. The expected selectable values are the 13 immutable catalog literals, not a value copied from the item under test.
- [x] In narrow 1× and quad 2× verify every option becomes visible through real scroll controls, wheel scrolling affects only the intended owner, and disabled boundary arrows never apply settings. Prove actual choices for each button, including an option reached only after scrolling; verify runtime state plus delta-only user JSON, close/reopen and load persisted settings. Reset only private test configuration between cases.
- [x] Add release-focused actions: navigation press/release must not select the new item under the same pointer; held selection, non-owning release, Space-first release and Esc cancel; immediately use W/E/R after the nested menu exits. Assert observed command/setting counts and resulting state, not merely PASS text.
- [x] Actual GUI diagnosis amendment: every page counted as visited must first prove the native list background exists, before label-ink checks. Scene grid pixels must not count as menu-label coverage. Fresh disabled previous/next presses must neither scroll/apply settings nor dismiss the current native list. Capture a real RED on the current DE09 build before a production fix. In the existing mouse-press chain, classify a hovered native `@scroll` rectangle even when hit_menu excludes its disabled ID; consume the press/release using existing navigation_consumed, but never call scroll_control for a disabled rectangle. Do not change legacy ellipse-disabled clicks, other disabled items, blank-space cancellation, or any release handler. Verify non-owner release, later owner release, Space and Esc on these disabled controls.
- [ ] Run new actual mapping GUI on the old short-menu stage for RED. Save the exact failure and screenshot; do not accept a fixture exception alone as proof that native rendering was tested.
- [x] Verify idle stage and fresh portable-file hashes, then install the Task 1 build into the existing stage. Run mappings standard/narrow/quad GREEN, inspect representative normal screenshots, verify final stage/build hashes and portable integrity.
- [x] Run native-style default and short-list probes, menus, release, profiles, manipulator, hotbox, overlay, guide and quad serially; pure Python40 and targeted CTest5. If a GUI test needs only coordinate updates, keep its original behavioral assertions. Report actual dimensions and all log/artifact paths for H5-02/H5-03/H5-04/H5-07.
- [x] Self-review, commit only owned tests/runner, and write the report for independent review. The controller updates the consolidated review and batch status after review gates pass.

## Exit and deferred behavior

### Task 2 independent-review correction

The old-stage rendering RED attempt was a fixture-anchor failure and is explicitly not valid RED.
The exact old executable was replaced before this was discovered. Controller accepts this as an
unfulfilled historical process requirement, with native semantic RED and disabled-scroll real GUI
RED/GREEN separately retained; do not claim full original TDD compliance or manufacture a historical run.
Current correctness requirements are not waived. Before Task2 approval:

- Standard full13 pages must use the same native-background-before-label check as paged menus.
- A fresh disabled-boundary owner release must be followed by one enabled navigation click with an
  observed actual page change, not merely a fixture index update; prove the literal selected afterward.
- Wheel one mapping owner, open a sibling in the same hotbox session and prove its initial first row
  remains index0 and previous disabled, then return to the original and prove its independent offset.
  If the existing explicit path-reset contract makes the last retention assertion invalid, report the
  exact path/source evidence for controller judgment before changing production or weakening the test.
- Re-run mappings standard/narrow/quad and py_compile; retain private serialized GUI isolation.

This slice does not add Blender popup keyboard focus, auto-hover scrolling, new center mapping values,
new-window commands or global event guard changes. Directional Views remain a hotbox. The user reviews
the nested menu visual composition and physical scroll/drag comfort at the batch end, not during this plan.

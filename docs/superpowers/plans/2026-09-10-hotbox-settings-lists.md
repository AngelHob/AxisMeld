# Hotbox Short Settings Lists Implementation Plan

> **For agentic workers:** Use the applicable development workflow task-by-task with review checkpoints; the user explicitly requests deferred consolidated manual review during this five-hour batch. Do not reopen a routine visual-approval gate.

**Goal:** Render Menu Rows and Transparency choices with the same native continuous-menu composition as Style, without changing setting semantics or hotbox input ownership.

**Architecture:** Reuse pure C++ menu geometry and the draw-only native menu adapter. Extend explicit built-in list classification to two existing setting directories; no new schema, handler, operator or preference persistence path.

**Tech Stack:** Existing Blender C++, GTest, Python unittest and isolated GUI runners; no dependencies.

**Spec:** [Batch scope](../../development/2026-09-10-five-hour-batch.md) and [composition convention](../../design/hotbox-menu-composition.md).

## Constraints

- Primary height 38, central side gaps 83.6, secondary height 24, secondary gap 4 logical px unchanged.
- Short lists: `center.controls.rows` (3 items), `center.controls.transparency` (5 items), plus existing two Style paths.
- List entries use native submenu appearance; their children are continuous 24px rows with native list padding.
- Retain separate per-depth backgrounds, 10px popup separation, existing narrow-pane fallback and Views real-origin guard.
- Mapping directories remain unchanged in this slice; do not silently classify all descendants as lists without pagination design.
- All 5 transparency choices and 3 row choices must remain selectable; setting storage and session/file behavior unchanged.
- Keep old full GUI assertions, update only input geometry where the intended layout changed.

## Task 1: Geometry and native entry classification

Files: `source/blender/axismeld/intern/hotbox_menu.cc`, `source/blender/axismeld/tests/hotbox_menu_test.cc`.
Consumes `layout_menu(...)`, existing `MenuRect.native_menu` and built-in IDs. No exported API change.

- [ ] Add a GTest for each new path with `default_snapshot()` / `measured(snapshot)` and assert supported layout, native entry and children, 24px row height, common x and adjacent y. Assert original root rectangles remain depth 0/non-native. Example target contract:

```cpp
const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540,
                                {"center.controls", "center.controls.transparency"}, {}, widths);
ASSERT_TRUE(layout.supported);
EXPECT_TRUE(rect(layout, "center.controls.transparency")->native_menu);
const auto *first = rect(layout, "center.controls.transparency.0");
const auto *second = rect(layout, "center.controls.transparency.25");
ASSERT_NE(first, nullptr);
ASSERT_NE(second, nullptr);
EXPECT_TRUE(first->native_menu);
EXPECT_FLOAT_EQ(first->height, 24);
EXPECT_FLOAT_EQ(first->x, second->x);
EXPECT_FLOAT_EQ(first->y, second->y + 24);
```

- [ ] Build only `axismeld_hotbox_menu_test`, run new tests and save expected RED; failure must show old ellipse/non-native semantics, not a bad ID.
- [ ] Introduce one private explicit predicate used by entry width/classification and the continuous-popup branch:

```cpp
bool native_list(const std::string &id)
{
  return id == "views.style" || id == "center.controls.style" ||
         id == "center.controls.rows" || id == "center.controls.transparency";
}
```

  Use it in place of the current two-Style classification. Keep the Views-only origin guard specific to `views.style`.
- [ ] Add narrow/edge coverage for 3-row and 5-row lists, with either full in-bounds separated placement or explicit unsupported layout at true capacity limits; do not shrink targets or drop choices.
- [ ] Run the entire native target GREEN. Format only changed C++ files.

## Task 2: Actual settings interactions and visual verification

Files: `tests/python/axismeld_hotbox_geometry_fixture.py`, `tests/python/axismeld_hotbox_native_style_events.py`,
`tests/python/axismeld_hotbox_menu_events.py`; production renderer only if a concrete failing test requires it.

- [ ] Before edits inspect how each suite derives Controls geometry; expected label padding now includes the native entry icon/arrow reserve for the two new entries.
- [ ] Generalize the existing Style list fixture into a labels-parameterized native-list helper, leaving `style_list(...)` as a small backwards-compatible wrapper. Test input geometry must reflect declared labels and row count; do not hard-code expected selected setting results into the helper.
- [ ] Add GUI paths for Menu Rows and Transparency that move through the actual parent, verify native background/hover at 1×/2×, select a different value, then assert runtime/settings state. Demonstrate RED on the baseline stage before reinstalling. Use the current disposable configuration and reset settings between cases.
- [ ] Rebuild blender + native target, verify idle stage, preserve config, and install to the existing ui-test stage. Run new GUI cases GREEN and actual screenshots; labels must remain readable and all choices reachable.
- [ ] Run `menus`, `native-style`, `release`, `profiles`, manipulator and relevant quad/overlay/guide regressions serially. A changed click coordinate may be corrected; an expected command or release assertion may not be removed to pass.
- [ ] Read-only code review, resolve important findings with RED/GREEN; update batch progress and H5-01 with logs, screenshots and exact stage SHA; local checkpoint commit only.

## Exit

This slice completes only the short settings lists. Continue with a separately documented narrow design for mapping lists if sufficient time remains. Do not call the entire five-hour batch complete or demand immediate user review.

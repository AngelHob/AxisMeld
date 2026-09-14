# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent literal cases for visible WINDOW bounds used by GUI fixtures."""
import unittest

from axismeld_hotbox_geometry_fixture import ellipse_page, native_page, native_fixture_surface, visible_bounds


class VisibleBoundsTest(unittest.TestCase):
    def setUp(self):
        native_fixture_surface(None)

    def tearDown(self):
        native_fixture_surface(None)

    def test_label_prefix_candidates_preserve_full_text_after_two_icon_slots(self):
        from axismeld_hotbox_geometry_fixture import label_prefix_starts
        # Foreground columns of two 16px icons and a complete text run.
        columns = [*range(16), *range(20, 36), *range(40, 100)]
        self.assertEqual(label_prefix_starts(columns, 1), (0, 20, 40))
        self.assertEqual(label_prefix_starts([*range(16), *range(20, 80)], 1), (0, 20))
        self.assertEqual(label_prefix_starts(list(range(60)), 1), (0,))
        # A later word boundary cannot be used to discard part of the full label.
        self.assertEqual(label_prefix_starts([*range(60), *range(70, 100)], 1), (0,))
        columns_2x = [*range(32), *range(40, 72), *range(80, 200)]
        self.assertEqual(label_prefix_starts(columns_2x, 2), (0, 40, 80))

    def test_view_leaf_fixture_reserves_semantic_icon_in_full_and_compact_labels(self):
        from axismeld_hotbox_geometry_fixture import view_page
        full = view_page((550, 450, 100, 38), [], lambda _label: 80,
                         (0, 0, 1200, 900), 1)
        self.assertEqual(full['items'][0][2], 116)
        # Full text exceeds bounds; compact text must still retain the same 20px slot.
        compact = view_page((180, 200, 100, 38), [],
                            lambda label: 1000 if label.endswith('View') or label == 'New Camera' else 30,
                            (0, 0, 460, 460), 1)
        self.assertEqual(compact['items'][0][2], 66)

    def test_internal_tool_header_trims_top_of_offset_window(self):
        self.assertEqual(
            visible_bounds((2, 95, 392, 281), (
                ('top', (2, 324, 392, 26)),
            )),
            (2, 95, 392, 229),
        )

    def test_left_and_right_overlap_regions_trim_same_offset_window(self):
        self.assertEqual(
            visible_bounds((111, 73, 392, 281), (
                ('left', (111, 73, 48, 281)),
                ('right', (423, 73, 80, 281)),
                ('top', (111, 302, 392, 26)),
            )),
            (159, 73, 264, 229),
        )

    def test_hidden_and_non_intersecting_regions_do_not_change_bounds(self):
        # A hidden Blender overlap region is one pixel wide and is filtered by the
        # GUI caller.  This case independently protects the non-intersection rule.
        self.assertEqual(
            visible_bounds((40, 60, 400, 300), (
                ('left', (0, 60, 1, 300)),
                ('top', (40, 420, 400, 24)),
            )),
            (40, 60, 400, 300),
        )

    def test_perpendicular_obstacles_intersect_original_window_in_either_order(self):
        obstacles = (
            ('left', (0, 0, 100, 300)),
            ('top', (0, 250, 80, 24)),
        )
        self.assertEqual(visible_bounds((0, 0, 400, 300), obstacles),
                         (100, 0, 300, 250))
        self.assertEqual(visible_bounds((0, 0, 400, 300), tuple(reversed(obstacles))),
                         (100, 0, 300, 250))

    def test_obstacles_cannot_leave_an_empty_safe_rectangle(self):
        with self.assertRaisesRegex(AssertionError, 'consume WINDOW'):
            visible_bounds((10, 20, 100, 80), (
                ('left', (10, 20, 60, 80)),
                ('right', (70, 20, 40, 80)),
            ))

    def test_complete_rows_use_window_fallback_without_hiding_choices(self):
        args = ((350, 280, 80, 24), tuple(f'Choice {i}' for i in range(13)),
                lambda _label: 120, (159, 73, 264, 229))
        # This narrow region cannot fit two full columns; it must not silently page.
        with self.assertRaisesRegex(AssertionError, 'Complete native list cannot fit'):
            native_page(*args)
        native_fixture_surface((0, 0, 1024, 768))
        page = native_page(*args, first=999)
        self.assertEqual((page['capacity'], page['first']), (13, 0))
        self.assertEqual(page['bounds'], (0, 0, 1024, 768))
        self.assertEqual(page['items'][0], (430, 300, 160, 24))
        self.assertEqual(page['items'][-1], (430, 12, 160, 24))
        self.assertTrue(all(page['items']))
        self.assertIsNone(page['previous']); self.assertIsNone(page['next'])

    def test_edge_complete_native_items_keep_offset_bounds_and_no_fake_back(self):
        page = ellipse_page((390, 278, 48, 24), tuple(f'Entry {i}' for i in range(8)),
                            lambda _label: 72, (159, 73, 264, 229))
        self.assertEqual(page['items'][0], (278, 266, 112, 24))
        self.assertEqual(page['items'][-1], (278, 98, 112, 24))
        self.assertTrue(all(page['items']))
        for key in ('back', 'previous', 'next'): self.assertIsNone(page[key])
        for x,y,w,h in page['items']:
            self.assertGreaterEqual(x, 159); self.assertGreaterEqual(y, 73)
            self.assertLessEqual(x+w, 423); self.assertLessEqual(y+h, 302)
        # A complete oversized directory requires columns, never smaller targets.
        columns = native_page((460, 250, 100, 38), tuple(f'Item {i}' for i in range(56)),
                              lambda _label: 80, (0, 0, 960, 540))
        self.assertEqual(len(columns['columns']), 3)
        self.assertEqual(len(set(columns['items'])), 56)
        self.assertTrue(all(r[2:]==(120,24) for r in columns['items']))
        self.assertEqual(columns['items'][20][1], 12)
        self.assertEqual(columns['items'][21][0]-columns['items'][0][0], 124)


if __name__ == '__main__':
    unittest.main()

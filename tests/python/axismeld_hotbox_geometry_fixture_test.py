# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent literal cases for visible WINDOW bounds used by GUI fixtures."""
import unittest

from axismeld_hotbox_geometry_fixture import ellipse_page, native_page, visible_bounds


class VisibleBoundsTest(unittest.TestCase):
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

    def test_offset_safe_bounds_place_literal_paged_rows_below_internal_bar(self):
        page = native_page(
            (350, 280, 80, 24),
            tuple(f'Choice {index}' for index in range(13)),
            lambda _label: 120,
            (159, 73, 264, 229),
        )
        self.assertEqual((page['capacity'], page['first']), (6, 0))
        self.assertEqual(page['previous'], (190, 266, 160, 24))
        self.assertEqual(page['items'][:7], [
            (190, 242, 160, 24),
            (190, 218, 160, 24),
            (190, 194, 160, 24),
            (190, 170, 160, 24),
            (190, 146, 160, 24),
            (190, 122, 160, 24),
            None,
        ])
        self.assertEqual(page['next'], (190, 98, 160, 24))

    def test_edge_origin_moves_return_navigation_and_present_items_together(self):
        page = ellipse_page(
            (390, 278, 48, 24),
            tuple(f'Entry {index}' for index in range(8)),
            lambda _label: 72,
            (159, 73, 264, 229),
        )
        rectangles = [page['back'], page['previous'], page['next']]
        rectangles.extend(rect for rect in page['items'] if rect is not None)
        self.assertTrue(any(rect is None for rect in page['items']))
        self.assertIsNotNone(page['previous'])
        self.assertIsNotNone(page['next'])
        for rect in (rect for rect in rectangles if rect is not None):
            x, y, w, h = rect
            self.assertGreaterEqual(x, 159)
            self.assertGreaterEqual(y, 73)
            self.assertLessEqual(x+w, 423)
            self.assertLessEqual(y+h, 302)


if __name__ == '__main__':
    unittest.main()

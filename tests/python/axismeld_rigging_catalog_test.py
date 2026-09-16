# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Rigging projection preserves Maya source payload and explicit native chapters."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
from axismeld.menubar_catalog import build_menubar


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))
        if node.get('options'):
            yield node['options']


class RiggingCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.api = importlib.import_module('axismeld.rigging_workspace_catalog')
        except ModuleNotFoundError as error:
            if error.name != 'axismeld.rigging_workspace_catalog':
                raise
            cls.api = None

    def setUp(self):
        self.assertIsNotNone(self.api, 'Rigging workspace projection is missing')
        self.source = build_menubar()
        self.actual = self.api.integrate_rigging_groups(deepcopy(self.source))

    def test_only_two_domain_roots_are_exposed(self):
        self.assertEqual(self.actual['rigging_roots'], ('menubar.rigging.skeleton', 'menubar.rigging.skin'))
        self.assertEqual(self.actual['sets'], self.source['sets'])
        expected = [n for n in self.source['menus'] if n['id'] not in self.actual['rigging_roots']]
        actual = [n for n in self.actual['menus'] if n['id'] not in self.actual['rigging_roots']]
        self.assertEqual(actual, expected)

    def test_all_original_maya_rows_options_and_order_are_unchanged(self):
        for rid, body_count, options_count in (('menubar.rigging.skeleton', 54, 8),
                                               ('menubar.rigging.skin', 28, 25)):
            source = next(r for r in self.source['menus'] if r['id'] == rid)
            actual = next(r for r in self.actual['menus'] if r['id'] == rid)
            projected_source = deepcopy(actual)
            projected_source['children'] = [n for n in projected_source['children']
                                             if n.get('origin') != 'native_rigging']
            self.assertEqual(projected_source, source)
            rows = [n for n in walk((actual,)) if n['id'].startswith('maya.')]
            body = [n for n in rows if n['kind'] == 'disabled' and not n['id'].endswith('.options')]
            options = [n for n in rows if n['id'].endswith('.options')]
            self.assertEqual((len(body), len(options)), (body_count, options_count))
            self.assertTrue(all(n['kind'] == 'disabled' for n in body + options))

    def test_native_entries_land_in_reviewed_purpose_chapters(self):
        actual = {}
        for root in self.actual['menus']:
            chapter = None
            for node in root['children']:
                if node['kind'] == 'separator' and node.get('label'):
                    chapter = node['label']
                if node['kind'] == 'rigging_native':
                    actual[node['native_key']] = (root['id'], chapter)
                    self.assertTrue(node['icon'])
                    self.assertEqual(node['row_count_hint'], 1)
        self.assertEqual(actual, {
            'skeleton.create': ('menubar.rigging.skeleton', 'Joints'),
            'skeleton.edit_bones': ('menubar.rigging.skeleton', 'Joints'),
            'skeleton.ik': ('menubar.rigging.skeleton', 'IK'),
            'skeleton.pose': ('menubar.rigging.skeleton', 'IK'),
            'skin.bind': ('menubar.rigging.skin', 'Bind'),
            'skin.weight_paint': ('menubar.rigging.skin', 'Weight Maps'),
            'skin.weights': ('menubar.rigging.skin', 'Weight Maps'),
            'skin.vertex_groups': ('menubar.rigging.skin', 'Other'),
            'skin.group_specials': ('menubar.rigging.skin', 'Other'),
        })

    def test_repeated_integration_does_not_duplicate_entries(self):
        self.assertEqual(self.api.integrate_rigging_groups(deepcopy(self.actual)), self.actual)
        ids = [n['id'] for n in walk(self.actual['menus'])]
        self.assertEqual(len(ids), len(set(ids)))

    def test_missing_chapter_fails_before_mutating_another_root(self):
        broken = deepcopy(self.source)
        root = next(r for r in broken['menus'] if r['id'] == 'menubar.rigging.skin')
        root['children'] = [n for n in root['children'] if n.get('label') != 'Bind']
        before = deepcopy(broken)
        with self.assertRaises(ValueError):
            self.api.integrate_rigging_groups(broken)
        self.assertEqual(broken, before)


if __name__ == '__main__':
    unittest.main()

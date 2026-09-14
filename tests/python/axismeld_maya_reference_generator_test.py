# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keep the captured Maya reference generator deterministic and loss-audited."""
import copy
import json
from pathlib import Path
import re
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
GEN = runpy.run_path(str(ROOT / 'tools/axismeld/build_maya_menu_reference.py'))
SOURCE = json.loads(GEN['SOURCE'].read_text(encoding='utf-8'))
MENUS, AUDIT = GEN['normalize'](SOURCE)
NODES = tuple(GEN['walk'](MENUS))
PATHS = {n['path']: n for n in NODES if 'path' in n}


class ConversionTests(unittest.TestCase):
    def test_twenty_two_roots_and_conservation(self):
        self.assertEqual(len(MENUS), 22)
        raw = tuple(GEN['walk'](tuple(r for g in SOURCE['groups'].values() for r in g)))
        self.assertEqual(len(raw), len(NODES) + sum(a['action'] == 'remove' for a in AUDIT))

    def test_options_are_attached(self):
        self.assertEqual(sum('options' in n for n in NODES), 369)
        for n in NODES:
            if 'options' in n:
                self.assertEqual(n['options']['id'], n['id'] + '.options')
                self.assertEqual(n['options']['path'], n['path'] + ('Options',))
                self.assertNotIn(n['options'], n['children'])

    def test_no_snapshot_state_or_raw_bindings(self):
        for n in NODES:
            self.assertFalse({'checked', 'enabled', 'command', 'sourceType'} & n.keys())
            self.assertNotIn('menuItem', n['id'])
            if n.get('maya_command'):
                self.assertRegex(n['maya_command'], r'^[A-Za-z_][A-Za-z0-9_]*$')

    def test_precise_dynamic_removals_and_fixed_none(self):
        for p in [('File', 'Recent Files'), ('Select', 'Quick Select Sets'),
                  ('Mesh Display', 'Assign Existing Set')]:
            self.assertEqual(PATHS[p]['children'], ())
            self.assertTrue(PATHS[p]['dynamic'])
        self.assertIn(('Modify', 'Asset', 'Advanced Assets', 'Set Current Asset', 'None'), PATHS)
        self.assertNotIn(('Panels', 'Perspective', 'persp'), PATHS)
        self.assertIn(('Panels', 'Perspective', 'New'), PATHS)

    def test_bookmark_layouts_not_generic_filtered(self):
        self.assertEqual(len(PATHS['View', 'Predefined Bookmarks']['children']), 7)
        self.assertGreater(len(PATHS['Panels', 'Layouts']['children']), 5)
        n = PATHS['Show', 'Isolate Select', 'Bookmarks', 'Bookmark Current Objects']
        self.assertIn('options', n)
        self.assertIn('failed', PATHS['Show', 'Isolate Select', 'Bookmarks']['dynamic'])

    def test_workspace_template_and_audit(self):
        n = PATHS['Windows', 'Workspaces', 'Reset Current Workspace to Factory Default']
        self.assertEqual(n['maya_command'], 'ResetCurrentWorkspace')
        self.assertTrue(any(a['action'] == 'template' and 'General' in a['source_label'] for a in AUDIT))
        self.assertNotIn(('Windows', 'Workspaces', 'General*'), PATHS)

    def test_history_action_labels_are_templates_not_captured_operation_names(self):
        expected = {'Undo': 'Undo', 'Redo': 'Redo', 'RepeatLast': 'Repeat'}
        actual = {n['maya_command']: n for n in NODES
                  if n.get('maya_command') in expected}
        self.assertEqual(set(actual), set(expected))
        for identity, label in expected.items():
            with self.subTest(identity=identity):
                self.assertEqual(actual[identity]['label'], label)
                self.assertEqual(actual[identity]['path'], ('Edit', label))
        altered = copy.deepcopy(SOURCE)
        changed_labels = set()
        for n in GEN['walk'](tuple(r for g in altered['groups'].values() for r in g)):
            if n.get('command') in expected:
                n['label'] = expected[n['command']] + ' "differentSceneSpecificOperation..."'
                changed_labels.add(n['label'])
        normalized, audit = GEN['normalize'](altered)
        self.assertEqual(normalized, MENUS, 'History changes must not alter labels, IDs or paths')
        templates = {a['source_label'] for a in audit if a['action'] == 'template'}
        self.assertTrue(changed_labels <= templates, 'Every removed history suffix needs provenance')

    def test_history_templates_do_not_rewrite_distinct_view_or_tool_commands(self):
        expected = {'UndoViewChange': 'Undo View Change', 'RedoViewChange': 'Redo View Change',
                    'SetMeshRepeatTool': 'Repeat Tool'}
        actual = {n['maya_command']: n['label'] for n in NODES
                  if n.get('maya_command') in expected}
        self.assertEqual(actual, expected)
        self.assertTrue(any(n['label'] == 'Undoable Movement' for n in NODES))

    def test_ui_numbering_does_not_change_normalized_tree(self):
        altered = copy.deepcopy(SOURCE)
        for n in GEN['walk'](tuple(r for g in altered['groups'].values() for r in g)):
            n['path'] = 'unrelated|menuItem99999'
            n['parent'] = 'unrelated'
            if n.get('optionBox'):
                n['label'] = 'menuItem99999'
        self.assertEqual(GEN['normalize'](altered)[0], MENUS)

    def test_snapshot_values_do_not_change_normalized_tree(self):
        altered = copy.deepcopy(SOURCE)
        for n in GEN['walk'](tuple(r for g in altered['groups'].values() for r in g)):
            for key in ('enable', 'checkBox', 'radioButton'):
                n[key] = not n.get(key)
        self.assertEqual(GEN['normalize'](altered)[0], MENUS)

    def test_python_header_exact_indicator_parity(self):
        data = runpy.run_path(str(GEN['PYTHON']))
        pairs = dict(re.findall(r'\{"([^"]+)", "(checkbox|radio)"\}', GEN['HEADER'].read_text()))
        self.assertEqual(pairs, data['UNAVAILABLE_INDICATORS'])
        self.assertEqual(len(pairs), 197)

    def test_regeneration_is_exact(self):
        for path, text in GEN['render']().items():
            self.assertEqual(path.read_text(encoding='utf-8'), text)


if __name__ == '__main__':
    unittest.main(verbosity=2)

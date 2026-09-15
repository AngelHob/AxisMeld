# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Menu organization contracts independent of native drawing and scene state."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))


class MenubarCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.api = importlib.import_module('axismeld.menubar_catalog')
        except ModuleNotFoundError as error:
            if error.name != 'axismeld.menubar_catalog':
                raise
            cls.api = None

    def setUp(self):
        self.assertIsNotNone(self.api, 'Maya-organized application menubar is not implemented')
        self.catalog = self.api.build_menubar()
        self.menus = {item['id']: item for item in self.catalog['menus']}
        self.nodes = list(walk(self.catalog['menus']))

    def test_five_real_sets_and_topbar_order_are_preserved(self):
        from axismeld.menubar_reference import MENU_SETS
        self.assertEqual(set(self.catalog['sets']), {'MODELING', 'RIGGING', 'ANIMATION', 'FX', 'RENDERING'})
        for key, expected in MENU_SETS.items():
            self.assertEqual(tuple(self.catalog['sets'][key]), tuple(expected), key)
            self.assertTrue(all(identifier in self.menus for identifier in expected))
        self.assertFalse(any(identifier.startswith(('pane.', 'internal.')) for identifier in self.menus))

    def test_original_maya_rows_remain_at_their_original_parent_in_order(self):
        from axismeld.menubar_reference import REFERENCE_MENUS
        actual = {item['id']: item for item in self.nodes}

        def compare(reference):
            current = actual[reference['id']]
            self.assertEqual(current['label'], reference['label'])
            expected = reference.get('children', ())
            expected_ids = [item['id'] for item in expected]
            self.assertEqual([item['id'] for item in current['children']
                              if item['id'] in expected_ids], expected_ids)
            for child in expected:
                compare(child)
            if reference.get('options'):
                self.assertIn('options', current)
                self.assertFalse(current['options'].get('command'))
                self.assertFalse(current['options'].get('native_key'))

        for reference in REFERENCE_MENUS:
            compare(reference)

    def test_unavailable_maya_semantics_are_not_bound_to_different_native_actions(self):
        from axismeld.maya_menu_catalog import UNAVAILABLE_BINDINGS
        rows = [node for node in self.nodes if node.get('maya_command') in UNAVAILABLE_BINDINGS]
        self.assertEqual({node['maya_command'] for node in rows}, set(UNAVAILABLE_BINDINGS))
        for node in rows:
            self.assertEqual(node['kind'], 'disabled', node['label'])
            self.assertFalse(node.get('command'))
            self.assertFalse(node.get('native_key'))
            self.assertTrue(node['reason'])

    def test_all_existing_semantic_commands_are_reachable_in_their_purpose_menu(self):
        from axismeld.modeling_registry import SPECS
        commands = {node.get('command') for node in self.nodes}
        self.assertTrue(set(SPECS) <= commands, sorted(set(SPECS) - commands))
        self.assertFalse(any(node['label'] == 'Blender Extensions' for node in self.nodes))
        for root in self.catalog['menus']:
            for node in walk([root]):
                if node.get('origin') == 'blender_extension':
                    self.assertEqual(root['id'], self.api.CATEGORY_ROOTS[SPECS[node['command']].category])

    def test_native_entries_use_known_keys_and_preserve_original_capabilities(self):
        from axismeld.menubar_native import NATIVE_KEYS
        keys = {node['native_key'] for node in self.nodes if node.get('native_key')}
        self.assertEqual(keys, NATIVE_KEYS)
        for root_id, required in {
                'common.file': {'file.open', 'file.import', 'file.export', 'file.recent',
                                'file.save', 'file.save_as', 'file.save_copy', 'file.save_incremental',
                                'file.link', 'file.append', 'file.recover', 'file.external_data'},
                'common.edit': {'edit.undo', 'edit.redo', 'edit.undo_history', 'edit.repeat_history'},
                'common.modify': {'modify.rename', 'modify.batch_rename'},
                'common.windows': {'windows.preferences', 'windows.defaults', 'windows.install_template',
                                   'windows.new', 'windows.new_main', 'windows.workspace_next',
                                   'windows.workspace_previous', 'render.native'},
                'menubar.help': {'help.about', 'help.sysinfo', 'help.manual', 'help.system'},
                'menubar.rendering.render': {'render.image', 'render.animation', 'render.mixdown'},
        }.items():
            contained = {node.get('native_key') for node in walk([self.menus[root_id]])}
            self.assertTrue(required <= contained, (root_id, required - contained))

    def test_menu_ids_are_unique_and_mutating_a_result_does_not_change_the_next(self):
        identifiers = [node['id'] for node in self.nodes]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.catalog['menus'][0]['children'].clear()
        self.assertTrue(self.api.build_menubar()['menus'][0]['children'])

    def test_extension_sections_do_not_form_a_flat_unbounded_list(self):
        for node in self.nodes:
            if node.get('origin') == 'blender_section':
                self.assertLessEqual(len(node['children']), 24, node['id'])


if __name__ == '__main__':
    unittest.main()

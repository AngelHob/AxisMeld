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

    def test_extensions_belong_to_their_maya_chapter_not_the_last_heading(self):
        # Independent expectations from the actual Maya chapter captions.
        expected = {
            'common.select': {
                None: ('Object Relationships', 'Hierarchy', 'Grouped', 'Linked Objects', 'Pattern'),
                'Polygons': ('Mesh Components', 'Similarity Filters'),
                'NURBS Curves': ('Curve and Surface Points',)},
            'common.modify': {
                'Transform': ('Proportional Editing', 'Reset Transformations', 'Apply Transformations', 'Mirror', 'Transform Deltas'),
                'Pivot': ('Pivot', 'Object Origin'), 'Rotate Order': ('Rotation Order',), 'Naming': ('Naming Tools',)},
            'common.display': {'Viewport': ('Viewport Settings', 'Viewport'), 'Object': ('Component Display',)},
            'modeling.mesh': {'Combine': ('Combine Tools',), 'Remesh': ('Remesh',),
                'Transfer': ('Transfer', 'Element Order'), 'Optimize': ('Cleanup Tools',), 'Blender Modifiers': ('Modifiers',)},
            'modeling.edit_mesh': {'Components': ('Extrusion Tools', 'Components', 'Merge Tools', 'Topology', 'Interactive Topology'), 'Face': ('Face Boolean',)},
            'modeling.mesh_tools': {'Tools': ('Tools', 'Immediate Tools',)},
            'modeling.mesh_display': {'Normals': ('Normals', 'Average Normal Tools', 'Edit Normals', 'Face Strength', 'Shading', 'Normal Modifiers'),
                'Vertex Colors': ('Vertex Colors',), 'Display Attributes': ('Viewport Analysis', 'Data Marks',)},
            'modeling.curves': {'Modify': ('Geometry',), 'Edit': ('Control Points', 'Topology', 'Bezier Handles', 'Spline Type',)},
            'modeling.surfaces': {'Create': ('Construct',), 'Edit NURBS Surfaces': ('Topology', 'Control Points', 'Geometry',)},
            'modeling.deform': {'Create': ('Blender Deformers',), 'Edit': ('Binding', 'Hook Transforms',),
                'Weights': ('Vertex Groups',), 'Deformer Sets (legacy)': ('Blender Hook Membership',)},
        }
        for root_id, chapters in expected.items():
            actual, heading = {}, None
            for node in self.menus[root_id]['children']:
                if node['kind'] == 'separator' and node['label']:
                    heading = node['label']
                elif node.get('origin') == 'blender_section' and node['kind'] == 'menu':
                    self.assertNotIn(node['label'], actual)
                    actual[node['label']] = heading
            required = {label: chapter for chapter, labels in chapters.items() for label in labels}
            self.assertEqual(actual, required, root_id)

    def test_saving_and_nested_primitives_do_not_leak_into_unrelated_groups(self):
        file_rows = self.menus['common.file']['children']
        labels = [node['label'] for node in file_rows]
        self.assertEqual(labels[labels.index('Save Preferences')+1], 'Save and Recover')
        primitive = next(node for node in self.nodes if node['id'] == 'maya.common.create.polygon_primitives')
        labels = [node['label'] for node in primitive['children']]
        for label in ('Additional Primitives', 'Subdivision Primitives'):
            self.assertLess(labels.index(label), labels.index('Super Shapes'))
            self.assertGreater(labels.index(label), labels.index('Soccer Ball'))
        workspace = next(node for node in self.nodes if node['id'] == 'maya.common.windows.workspaces')
        labels = [node['label'] for node in workspace['children']]
        self.assertEqual(labels[labels.index('Switch Workspace')-1], 'Blender Workspaces')

    def test_naming_has_one_native_entry_for_each_equivalent_semantic_command(self):
        parent = next(node for node in self.menus['common.modify']['children'] if node['label'] == 'Naming Tools')
        for label, semantic, native in (('Rename Active Item...', 'object.rename', 'modify.rename'),
                                        ('Batch Rename...', 'object.batch_rename', 'modify.batch_rename')):
            rows = [node for node in parent['children'] if node['label'] == label]
            self.assertEqual(len(rows), 1, label)
            self.assertEqual(rows[0]['kind'], 'native')
            self.assertEqual(rows[0]['command'], semantic)
            self.assertEqual(rows[0]['native_key'], native)

    def test_blender_deformer_edits_reuse_the_actual_edit_submenus(self):
        root = self.menus['modeling.deform']
        for label, command in (('Blend Shape', 'deform.shape_key_mirror'), ('Lattice', 'deform.lattice_flip_x')):
            parent = next(node for node in root['children'] if node['kind'] == 'menu' and node['label'] == label)
            self.assertIn(command, {node.get('command') for node in walk([parent])})

    def test_unreviewed_extensions_cannot_silently_enter_the_last_chapter(self):
        root = self.menus['common.select']
        before = [node['id'] for node in root['children']]
        with self.assertRaisesRegex(ValueError, 'Missing Maya chapter placement'):
            self.api._section(root, ('Unreviewed Extension',))
        self.assertEqual([node['id'] for node in root['children']], before)


if __name__ == '__main__':
    unittest.main()

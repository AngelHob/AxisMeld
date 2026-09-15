# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Workspace reachability and source-preservation contracts independent of bpy."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))

from axismeld.menubar_catalog import build_menubar
from axismeld.menubar_reference import REFERENCE_MENUS


MODEL_SOURCE_ROOTS = tuple('modeling.' + suffix for suffix in
    ('mesh', 'edit_mesh', 'mesh_tools', 'mesh_display', 'curves', 'surfaces', 'deform', 'uv', 'generate'))
GROUP_ITEMS = {
    'Components': ('add_divisions', 'bevel', 'bridge', 'circularize', 'collapse', 'connect',
                   'detach', 'extrude', 'smart_extrude', 'merge', 'merge_to_center', 'transform',
                   'flip', 'symmetrize'),
    'Vertex': ('average_vertices', 'chamfer_vertices', 'reorder_vertices'),
    'Edge': ('delete_edge_vertex', 'edit_edge_flow', 'flip_triangle_edge',
             'spin_edge_backward', 'spin_edge_forward'),
    'Face': ('assign_invisible_faces', 'duplicate', 'extract', 'poke', 'wedge'),
    'Curve': ('project_curve_on_mesh', 'split_mesh_with_projected_curve'),
}
GROUP_OPTIONS = {'Components': 8, 'Vertex': 2, 'Edge': 1, 'Face': 5, 'Curve': 2}


def walk(nodes, *, options=False):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()), options=options)
        if options and node.get('options'):
            yield from walk((node['options'],), options=True)


def functions(nodes):
    return {node['id']: node for node in walk(nodes, options=True)
            if node.get('kind') not in {None, 'menu', 'separator'}}


class WorkspaceMenuCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.api = importlib.import_module('axismeld.workspace_menu_catalog')
        except ModuleNotFoundError as error:
            if error.name != 'axismeld.workspace_menu_catalog':
                raise
            cls.api = None

    def setUp(self):
        self.assertIsNotNone(self.api, 'The Modeling workspace menu projection is missing')
        self.source = build_menubar()
        self.actual = self.api.build_workspace_menubar()
        self.roots = {node['id']: node for node in self.actual['menus']}

    def test_edit_mesh_is_replaced_by_five_roots_in_both_inventory_and_modeling_set(self):
        group_ids = tuple('viewport.modeling.' + label.lower() for label in GROUP_ITEMS)
        expected = []
        for identifier in self.source['sets']['MODELING']:
            expected.extend(group_ids if identifier == 'modeling.edit_mesh' else (identifier,))
        self.assertEqual(self.actual['sets']['MODELING'], tuple(expected))
        self.assertNotIn('modeling.edit_mesh', self.roots)
        self.assertEqual(len(self.roots), 47)
        self.assertEqual(self.actual['edit_mesh_groups'], dict(zip(GROUP_ITEMS, group_ids)))
        for label, identifier in zip(GROUP_ITEMS, group_ids):
            self.assertEqual(self.roots[identifier]['label'], label)
            self.assertEqual(self.roots[identifier]['kind'], 'menu')

    def test_each_split_uses_exact_original_group_ids_order_and_option_counts(self):
        for label, suffixes in GROUP_ITEMS.items():
            root = self.roots['viewport.modeling.' + label.lower()]
            rows = [node for node in root['children']
                    if node.get('origin') == 'maya' and node['kind'] != 'separator']
            self.assertEqual(tuple(node['id'] for node in rows),
                             tuple('maya.modeling.edit_mesh.' + suffix for suffix in suffixes), label)
            self.assertEqual(sum(bool(node.get('options')) for node in rows), GROUP_OPTIONS[label])
        components = self.roots['viewport.modeling.components']['children']
        flip = next(i for i, n in enumerate(components) if n['label'] == 'Flip')
        self.assertEqual(components[flip - 1]['id'], 'maya.modeling.edit_mesh.separator_2744843f61')

    def test_all_source_function_payloads_and_options_are_unchanged_and_unique(self):
        expected = functions(self.source['menus'])
        self.assertEqual(functions(self.actual['menus']), expected)
        ids = [node['id'] for node in walk(self.actual['menus'], options=True)]
        self.assertEqual(len(ids), len(set(ids)))
        reference_nodes = list(walk(REFERENCE_MENUS))
        body_ids = {node['id'] for node in reference_nodes if node.get('kind') == 'item'}
        option_ids = {node['options']['id'] for node in reference_nodes if node.get('options')}
        self.assertEqual((len(body_ids), len(option_ids)), (1829, 639))
        self.assertTrue(body_ids | option_ids <= set(expected))
        exposed_roots = tuple(sorted(set().union(*self.actual['sets'].values())))
        self.assertEqual(set(exposed_roots), set(self.roots))
        self.assertTrue(body_ids | option_ids <= set(self.api.routes(self.actual, exposed_roots)))

    def test_modeling_reachability_covers_445_functions_and_237_options(self):
        expected_roots = ('modeling.mesh',) + tuple('viewport.modeling.' + label.lower()
            for label in GROUP_ITEMS) + tuple('modeling.' + suffix for suffix in
            ('mesh_tools', 'mesh_display', 'curves', 'surfaces', 'deform', 'uv', 'generate'))
        self.assertEqual(self.actual['modeling_roots'], expected_roots)
        reference_nodes = list(walk(root for root in REFERENCE_MENUS if root['id'] in MODEL_SOURCE_ROOTS))
        body_ids = {node['id'] for node in reference_nodes if node.get('kind') == 'item'}
        option_ids = {node['options']['id'] for node in reference_nodes if node.get('options')}
        self.assertEqual((len(body_ids), len(option_ids)), (445, 237))
        routes = self.api.routes(self.actual, self.actual['modeling_roots'])
        all_maya_ids = {node['id'] for node in walk(REFERENCE_MENUS, options=True)
                        if node.get('kind') == 'item'}
        self.assertEqual(set(routes) & all_maya_ids, body_ids | option_ids)

    def test_all_blender_extensions_follow_their_existing_chapters(self):
        components = self.roots['viewport.modeling.components']['children']
        self.assertEqual(tuple(n['label'] for n in components if n['kind'] == 'menu'),
            ('Extrusion Tools', 'Components', 'Merge Tools', 'Topology', 'Interactive Topology'))
        face = self.roots['viewport.modeling.face']['children']
        self.assertEqual(tuple(n['label'] for n in face if n['kind'] == 'menu'), ('Face Boolean',))
        original = next(root for root in self.source['menus'] if root['id'] == 'modeling.edit_mesh')
        extensions = {n['id']: n for n in walk((original,)) if n.get('origin') == 'blender_extension'}
        self.assertEqual(len(extensions), 34)
        actual = {n['id']: n for label in GROUP_ITEMS
                  for n in walk((self.roots['viewport.modeling.' + label.lower()],))
                  if n.get('origin') == 'blender_extension'}
        self.assertEqual(actual, extensions)

    def test_other_roots_and_other_four_sets_are_unchanged(self):
        for root in self.source['menus']:
            if root['id'] != 'modeling.edit_mesh':
                self.assertEqual(self.roots[root['id']], root, root['id'])
        for key in ('RIGGING', 'ANIMATION', 'FX', 'RENDERING'):
            self.assertEqual(self.actual['sets'][key], self.source['sets'][key])
        self.assertIn('modeling.deform', self.actual['sets']['RIGGING'])
        self.assertIn('modeling.deform', self.actual['sets']['ANIMATION'])

    def test_projection_cannot_mutate_its_input_or_subsequent_builds(self):
        before = deepcopy(self.source)
        with patch.object(self.api, 'build_menubar', return_value=self.source):
            result = self.api.build_workspace_menubar()
        self.assertEqual(self.source, before)
        first = next(root for root in result['menus'] if root['id'] == 'viewport.modeling.vertex')['children'][0]
        first['options']['reason'] = 'changed'
        self.assertEqual(self.source, before)
        self.assertEqual(self.api.build_workspace_menubar(), self.actual)
        self.assertEqual(build_menubar(), before)

    def test_routes_report_new_visible_paths_and_original_options_without_rewriting_provenance(self):
        routes = self.api.routes(self.actual, self.actual['modeling_roots'])
        self.assertEqual(routes['maya.modeling.edit_mesh.chamfer_vertices'], ('Vertex', 'Chamfer Vertices'))
        self.assertEqual(routes['maya.modeling.edit_mesh.chamfer_vertices.options'],
                         ('Vertex', 'Chamfer Vertices', 'Options'))
        self.assertEqual(routes['maya.modeling.edit_mesh.split_mesh_with_projected_curve'],
                         ('Curve', 'Split Mesh with Projected Curve'))
        node = functions(self.actual['menus'])['maya.modeling.edit_mesh.chamfer_vertices']
        self.assertEqual(node['path'], ('Edit Mesh', 'Chamfer Vertices'))
        self.assertNotIn('maya.common.file.save_scene', routes)

    def test_missing_or_unrecognized_maya_chapter_fails_instead_of_losing_functions(self):
        for replacement in (None, 'maya.modeling.edit_mesh.unreviewed'):
            changed = deepcopy(self.source)
            root = next(root for root in changed['menus'] if root['id'] == 'modeling.edit_mesh')
            index = next(i for i, node in enumerate(root['children']) if node['label'] == 'Edge')
            if replacement is None:
                del root['children'][index]
            else:
                root['children'][index]['id'] = replacement
            with patch.object(self.api, 'build_menubar', return_value=changed):
                with self.assertRaises(ValueError):
                    self.api.build_workspace_menubar()


if __name__ == '__main__':
    unittest.main()

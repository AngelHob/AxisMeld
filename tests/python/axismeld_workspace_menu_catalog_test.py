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
    ('mesh', 'edit_mesh', 'mesh_tools', 'mesh_display', 'curves', 'surfaces', 'uv'))
GROUP_IDS = {'Components': 'modeling.edit_mesh', 'Vertex': 'viewport.modeling.vertex',
             'Edge': 'viewport.modeling.edge', 'Face': 'viewport.modeling.face',
             'Curve': 'viewport.modeling.curve_projection'}
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
            if node.get('kind') not in {None, 'menu', 'separator', 'native_group'}}


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
        self.nodes = {node['id']: node for node in walk(self.actual['menus'])}

    def test_vertex_edge_face_are_nested_and_components_retain_edit_mesh(self):
        component_ids = tuple(GROUP_IDS[label] for label in ('Vertex', 'Edge', 'Face'))
        expected = [identifier for identifier in self.source['sets']['MODELING']
                    if identifier not in ('modeling.deform', 'modeling.generate')]
        self.assertEqual(self.actual['sets']['MODELING'], tuple(expected))
        self.assertFalse(set(component_ids) & set(self.roots))
        self.assertEqual(tuple(node['id'] for node in self.roots['modeling.edit_mesh']['children']
                               if node['id'] in component_ids), component_ids)
        self.assertNotIn('viewport.modeling.components', self.roots)
        self.assertNotIn('viewport.modeling.curve_projection', self.roots)
        self.assertNotIn('viewport.modeling.curve', self.roots)
        self.assertEqual(len(self.roots), 43)
        self.assertEqual(self.actual['edit_mesh_groups'], GROUP_IDS)
        for label, identifier in GROUP_IDS.items():
            caption = {'Components': 'Edit Mesh', 'Curve': 'Curve Projection'}.get(label, label)
            self.assertEqual(self.nodes[identifier]['label'], caption)
            self.assertEqual(self.nodes[identifier]['kind'], 'menu')

    def test_each_split_uses_exact_original_group_ids_order_and_option_counts(self):
        for label, suffixes in GROUP_ITEMS.items():
            root = self.nodes[GROUP_IDS[label]]
            rows = [node for node in root['children']
                    if node.get('origin') == 'maya' and node['kind'] != 'separator']
            self.assertEqual(tuple(node['id'] for node in rows),
                             tuple('maya.modeling.edit_mesh.' + suffix for suffix in suffixes), label)
            self.assertEqual(sum(bool(node.get('options')) for node in rows), GROUP_OPTIONS[label])
        components = self.roots['modeling.edit_mesh']['children']
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
        self.assertTrue(body_ids | option_ids <= set(self.api.routes(self.actual)))
        exposed_roots = set().union(*self.actual['sets'].values())
        self.assertEqual(set(self.roots) - exposed_roots, {'modeling.generate'})
        self.assertEqual(self.actual['archived_roots'], ('modeling.generate',))

    def test_modeling_reachability_covers_231_functions_and_161_options(self):
        expected_roots = ('modeling.mesh', 'modeling.edit_mesh', 'modeling.mesh_tools',
                         'modeling.mesh_display', 'modeling.curves', 'modeling.surfaces', 'modeling.uv')
        self.assertEqual(self.actual['modeling_roots'], expected_roots)
        reference_nodes = list(walk(root for root in REFERENCE_MENUS if root['id'] in MODEL_SOURCE_ROOTS))
        body_ids = {node['id'] for node in reference_nodes if node.get('kind') == 'item'}
        option_ids = {node['options']['id'] for node in reference_nodes if node.get('options')}
        self.assertEqual((len(body_ids), len(option_ids)), (231, 161))
        routes = self.api.routes(self.actual, self.actual['modeling_roots'])
        all_maya_ids = {node['id'] for node in walk(REFERENCE_MENUS, options=True)
                        if node.get('kind') == 'item'}
        self.assertEqual(set(routes) & all_maya_ids, body_ids | option_ids)

    def test_34_blender_extensions_follow_exact_component_and_purpose_routes(self):
        targets = {
            ('Vertex', 'Extrude'): ('extrude_vertices',),
            ('Vertex', 'Connect'): ('connect_pairs', 'make_edge_face'),
            ('Vertex', 'Smooth'): ('average_laplacian',),
            ('Vertex', 'Split'): ('rip', 'rip_fill', 'rip_extend'),
            ('Vertex', 'Delete'): ('dissolve_vertices',),
            ('Edge', 'Extrude'): ('extrude_edges', 'screw'),
            ('Edge', 'Split'): ('edge_split',),
            ('Edge', 'Loops'): ('space_loops',),
            ('Edge', 'Delete'): ('dissolve_edges', 'delete_edge_loop'),
            ('Face', 'Extrude'): ('extrude_faces_individual', 'extrude_along_normals'),
            ('Face', 'Fill'): ('fill', 'grid_fill', 'beautify_fill'),
            ('Face', 'Topology'): ('intersect_faces', 'split_by_edges'),
            ('Face', 'Delete'): ('dissolve_faces',),
            ('Face', 'Inset and Shell'): ('inset', 'solidify_faces', 'wireframe_faces'),
            ('Face', 'Face Boolean'): ('boolean_faces_union', 'boolean_faces_difference', 'boolean_faces_intersection'),
            ('Edit Mesh', 'Split'): ('detach_selection',),
            ('Edit Mesh', 'Merge'): ('merge_cursor', 'merge_first', 'merge_last', 'merge_collapse'),
            ('Edit Mesh', 'Transform'): ('flatten',),
        }
        original = next(root for root in self.source['menus'] if root['id'] == 'modeling.edit_mesh')
        extensions = {n['id']: n for n in walk((original,)) if n.get('origin') == 'blender_extension'}
        self.assertEqual(len(extensions), 34)
        expected_ids = {'menubar.command.mesh.' + suffix for items in targets.values() for suffix in items}
        self.assertEqual(expected_ids, set(extensions))
        actual = {n['id']: n for label in GROUP_ITEMS
                  for n in walk((self.nodes[GROUP_IDS[label]],))
                  if n.get('origin') == 'blender_extension'}
        self.assertEqual(actual, extensions)
        actual_routes = self.api.routes(self.actual, self.actual['modeling_roots'])
        for purpose, items in targets.items():
            for suffix in items:
                identifier = 'menubar.command.mesh.' + suffix
                prefix = () if purpose[0] == 'Edit Mesh' else ('Edit Mesh',)
                self.assertEqual(actual_routes[identifier], prefix + purpose + (extensions[identifier]['label'],), identifier)
        expected_counts = {'Vertex': 8, 'Edge': 6, 'Face': 14, 'Edit Mesh': 6}
        actual_counts = dict.fromkeys(expected_counts, 0)
        for identifier in extensions:
            child = actual_routes[identifier][1]
            owner = child if child in ('Vertex', 'Edge', 'Face') else 'Edit Mesh'
            actual_counts[owner] += 1
        self.assertEqual(actual_counts, expected_counts)

    def test_relocated_extensions_leave_no_empty_legacy_component_folders(self):
        old_root = next(root for root in self.source['menus'] if root['id'] == 'modeling.edit_mesh')
        legacy_ids = {n['id'] for n in old_root['children'] if n['kind'] == 'menu' and n['label'] in
                      ('Extrusion Tools', 'Components', 'Merge Tools', 'Topology', 'Interactive Topology')}
        self.assertEqual(len(legacy_ids), 5)
        self.assertFalse(legacy_ids & set(self.nodes))
        for label in ('Components', 'Vertex', 'Edge', 'Face'):
            for node in walk((self.nodes[GROUP_IDS[label]],)):
                if node.get('origin') in {'blender_section', 'workspace_section'}:
                    self.assertTrue(node['children'], node['id'])

    def test_other_modules_and_four_sets_are_unchanged_and_maya_child_order_is_preserved(self):
        for root in self.source['menus']:
            if root['id'] not in MODEL_SOURCE_ROOTS:
                self.assertEqual(self.roots[root['id']], root, root['id'])
        # The approved Edit Mesh split is checked explicitly above. Every
        # other source menu retains its Maya children in the same relative order,
        # even when native purpose groups are inserted between source chapters.
        for source_node in walk(self.source['menus']):
            if source_node.get('origin') != 'maya' or source_node['kind'] != 'menu' or source_node['id'] == 'modeling.edit_mesh':
                continue
            actual_node = self.nodes[source_node['id']]
            expected = [n['id'] for n in source_node['children'] if n.get('origin') == 'maya']
            actual = [n['id'] for n in actual_node['children'] if n['id'] in expected]
            self.assertEqual(actual, expected, source_node['id'])
            self.assertEqual({k: v for k, v in actual_node.items() if k != 'children'},
                             {k: v for k, v in source_node.items() if k != 'children'})
        self.assertIn(GROUP_IDS['Curve'], [n['id'] for n in self.roots['modeling.mesh_tools']['children']])
        for key in ('RIGGING', 'ANIMATION', 'FX', 'RENDERING'):
            self.assertEqual(self.actual['sets'][key], self.source['sets'][key])
        self.assertIn('modeling.deform', self.actual['sets']['RIGGING'])
        self.assertIn('modeling.deform', self.actual['sets']['ANIMATION'])

    def test_every_registered_native_group_item_is_drawn_or_has_a_precise_existing_alias(self):
        from axismeld.workspace_native_groups import GROUPS
        expected = {(key, item['id']) for key, group in GROUPS.items() for item in group['items']}
        added_modifier = {('object.modifiers', 'object.modifiers.provider')}
        self.assertTrue(added_modifier <= expected)
        self.assertEqual(len(expected - added_modifier), 161)
        self.assertEqual(len({item_id for _, item_id in expected - added_modifier}), 134)
        native_nodes = [n for n in self.nodes.values() if n['kind'] == 'native_group']
        self.assertTrue(native_nodes, 'Native groups are not integrated into the projected menu tree')
        included = [(n['group_key'], item_id) for n in native_nodes for item_id in n['include']]
        aliases = [(n['group_key'], n['native_item']) for n in self.actual['native_equivalences']]
        native_aliases = [(n['group_key'], n['native_item']) for n in self.actual['native_item_equivalences']]
        self.assertEqual(len(included), len(set(included)))
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertEqual(len(native_aliases), len(set(native_aliases)))
        self.assertFalse(set(included) & set(aliases))
        self.assertFalse((set(included) | set(aliases)) & set(native_aliases))
        self.assertEqual(set(included) | set(aliases) | set(native_aliases), expected)
        self.assertEqual((len(included), len(aliases), len(native_aliases)), (149, 11, 2))
        self.assertEqual({(n['group_key'], n['native_item'], n['target_group_key'], n['target_native_item'])
                          for n in self.actual['native_item_equivalences']}, {
            ('edge.seams', 'edge.seams.mesh_mark_seam', 'uv.seams', 'uv.seams.mesh_mark_seam'),
            ('edge.seams', 'edge.seams.mesh_mark_seam_2', 'uv.seams', 'uv.seams.mesh_mark_seam_2'),
        })
        for alias in self.actual['native_item_equivalences']:
            self.assertIn((alias['target_group_key'], alias['target_native_item']), included)
        self.assertNotIn('edge.seams', {n['group_key'] for n in native_nodes})
        expected_aliases = {
            'vertex.extrude.mesh_bevel': 'mesh.bevel_vertices',
            'vertex.rip.mesh_rip_move': 'mesh.rip',
            'vertex.rip.mesh_rip_move_2': 'mesh.rip_fill',
            'vertex.rip.mesh_rip_edge_move': 'mesh.rip_extend',
            'vertex.smooth_slide.mesh_vertices_smooth': 'mesh.average_vertices',
            'vertex.smooth_slide.mesh_vertices_smooth_laplacian': 'mesh.average_laplacian',
            'vertex.crease.transform_vert_crease': 'mesh.interactive_crease_vertices',
            'edge.construct.mesh_bevel': 'mesh.bevel_edges',
            'edge.slide.mesh_offset_edge_loops_slide': 'mesh.interactive_offset_loop',
            'edge.weight.transform_edge_crease': 'mesh.interactive_crease_edges',
            'face.construct.mesh_inset': 'mesh.inset',
        }
        self.assertEqual({row['native_item']: row['command'] for row in self.actual['native_equivalences']}, expected_aliases)
        active_commands = {n.get('command') for identifier in self.actual['modeling_roots']
                           for n in walk((self.roots[identifier],))}
        self.assertTrue(set(expected_aliases.values()) <= active_commands)
        for node in native_nodes:
            group = GROUPS[node['group_key']]
            placement = next(p for p in self.actual['native_group_placements'] if p['group_key'] == node['group_key'])
            self.assertEqual(tuple(node['include']), tuple(placement['included']))
            self.assertEqual(placement['root_id'], group['root_id'])
            self.assertEqual(placement['path'], group['path'])
            self.assertEqual(node['row_count_hint'], group['row_count_hint'])

    def test_native_purpose_groups_use_the_actual_maya_chapter(self):
        def chapter(root_id, label):
            heading = ''
            for node in self.roots[root_id]['children']:
                if node['kind'] == 'separator' and node['label']:
                    heading = node['label']
                elif node['kind'] == 'menu' and node['label'] == label:
                    return heading
            self.fail('Missing native purpose directory: ' + root_id + '/' + label)
        expected = {
            ('modeling.mesh', 'Modifiers'): 'Blender Modifiers',
            ('modeling.mesh_tools', 'Cut'): 'Tools',
            ('modeling.mesh_display', 'Face Data'): 'Display Attributes',
            ('modeling.curves', 'Transform'): 'Modify',
            ('modeling.surfaces', 'Transform'): 'Edit NURBS Surfaces',
            ('modeling.uv', 'Unwrap'): 'Create',
            ('modeling.uv', 'Seams'): 'Cut/Sew',
        }
        for (root_id, label), heading in expected.items():
            self.assertEqual(chapter(root_id, label), heading, root_id + '/' + label)

    def test_route_inventory_uses_nested_component_paths_for_maya_and_native_items(self):
        from axismeld.workspace_native_groups import GROUPS
        generator = Path(__file__).resolve().parents[2] / 'tools/utils/axismeld_workspace_menu_routes.py'
        spec = importlib.util.spec_from_file_location('workspace_routes_for_test', generator)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        inventory = module.build_inventory()
        self.assertEqual(inventory['counts']['modeling_projected_roots'], 7)
        self.assertEqual(inventory['counts']['total'], 392)
        rows = {row['id']: row for row in inventory['entries']}
        for label, suffixes in GROUP_ITEMS.items():
            if label not in ('Vertex', 'Edge', 'Face'):
                continue
            for suffix in suffixes:
                row = rows['maya.modeling.edit_mesh.' + suffix]
                self.assertEqual(row['primary_route'][:4], ('Modeling', '3D View', 'Edit Mesh', label))
                self.assertEqual(row['projected_root_id'], 'modeling.edit_mesh')
                self.assertTrue(all(route[:5] == ('Window', 'Maya Menu Sets', 'Modeling', 'Edit Mesh', label)
                                    for route in row['fallback_routes']))
        native = inventory['native_integration']['entries']
        self.assertEqual(len(native), 162)
        for row in native:
            group = GROUPS[row['group_key']]
            if group['root_id'].startswith('viewport.modeling.'):
                label = group['root_id'].rsplit('.', 1)[-1].title()
                self.assertEqual(row['destination_container'],
                                 ('Modeling', '3D View', 'Edit Mesh', label) + group['path'])
                if row['resolution'] == 'native_draw':
                    self.assertEqual(row['actual_routes'], [row['destination_container']])
                elif row['resolution'] == 'existing_command_alias':
                    visible = self.api.routes(self.actual, self.actual['modeling_roots'])
                    self.assertEqual(row['actual_routes'], [('Modeling', '3D View') + visible[target]
                                                           for target in row['equivalent_target_ids']])

    def test_projection_cannot_mutate_its_input_or_subsequent_builds(self):
        before = deepcopy(self.source)
        with patch.object(self.api, 'build_menubar', return_value=self.source):
            result = self.api.build_workspace_menubar()
        self.assertEqual(self.source, before)
        first = next(node for node in walk(result['menus']) if node['id'] == 'viewport.modeling.vertex')['children'][0]
        first['options']['reason'] = 'changed'
        self.assertEqual(self.source, before)
        self.assertEqual(self.api.build_workspace_menubar(), self.actual)
        self.assertEqual(build_menubar(), before)

    def test_routes_report_new_visible_paths_and_original_options_without_rewriting_provenance(self):
        routes = self.api.routes(self.actual, self.actual['modeling_roots'])
        self.assertEqual(routes['maya.modeling.edit_mesh.chamfer_vertices'], ('Edit Mesh', 'Vertex', 'Chamfer Vertices'))
        self.assertEqual(routes['maya.modeling.edit_mesh.chamfer_vertices.options'],
                         ('Edit Mesh', 'Vertex', 'Chamfer Vertices', 'Options'))
        self.assertEqual(routes['maya.modeling.edit_mesh.split_mesh_with_projected_curve'],
                         ('Mesh Tools', 'Curve Projection', 'Split Mesh with Projected Curve'))
        self.assertEqual(routes['maya.modeling.edit_mesh.add_divisions'], ('Edit Mesh', 'Add Divisions'))
        node = functions(self.actual['menus'])['maya.modeling.edit_mesh.chamfer_vertices']
        self.assertEqual(node['path'], ('Edit Mesh', 'Chamfer Vertices'))
        self.assertNotIn('maya.common.file.save_scene', routes)

    def test_deform_and_generate_are_excluded_from_modeling_without_deleting_the_reference(self):
        excluded = ('modeling.deform', 'modeling.generate')
        self.assertEqual(self.actual['excluded_modeling_roots'], excluded)
        self.assertFalse(set(excluded) & set(self.actual['modeling_roots']))
        self.assertFalse(set(excluded) & set(self.actual['sets']['MODELING']))
        references = [n for n in REFERENCE_MENUS if n['id'] in excluded]
        self.assertEqual(sum(n.get('kind') == 'item' for n in walk(references)), 214)
        self.assertEqual(sum(bool(n.get('options')) for n in walk(references)), 76)
        self.assertTrue(set(excluded) <= set(self.roots))

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

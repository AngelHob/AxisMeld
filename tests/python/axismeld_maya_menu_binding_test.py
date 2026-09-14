# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent binding decisions from the 18-ambiguity review, plus whole-tree contracts."""
from collections import defaultdict
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
from axismeld.maya_menu_catalog import _binding
from axismeld.modeling_registry import SPECS

# Deliberately independent of the binder's preferred/unavailable constants.
EXPECTED_PREFERRED = {
    'FillHole': 'mesh.fill_holes',
    'ReducePolygon': 'mesh.reduce_modifier',
    'SmoothPolygon': 'mesh.subdivision_modifier',
    'PolyExtrude': 'mesh.extrude_region',
    'PolyMerge': 'mesh.merge_distance',
    'ConnectComponents': 'mesh.connect_path',
    'AveragePolygonNormals': 'normals.average_custom',
    'PolygonNormalEditTool': 'normals.rotate',
}
EXPECTED_DISABLED = {
    'ReorderRotationDialog', 'SeparatePolygon', 'PolyRemesh', 'CleanupPolygon',
    'TransferAttributes', 'DetachComponent', 'DeletePolyElements', 'FlipTriangleEdge',
    'SetVertexNormal', 'OpenCloseSurfaces',
}
EXPECTED_UNAVAILABLE_SINGLETONS = {
    'PolygonSelectionConstraints', 'PrefixHierarchyNames', 'SearchAndReplaceNames',
    'EditMembershipTool', 'DuplicateCurve', 'SelectSimilar',
}
EXPECTED_CORE_SELECTION = {
    'SelectNone': 'selection.clear', 'SelectToggleMode': 'selection.toggle_component',
    'GrowPolygonSelectionRegion': 'selection.grow',
    'ShrinkPolygonSelectionRegion': 'selection.shrink',
}
EXPECTED_ROOTS = (
    'common.file', 'common.edit', 'common.create', 'common.select', 'common.modify',
    'common.display', 'common.windows', 'pane.view', 'pane.shading', 'pane.lighting',
    'pane.show', 'pane.renderer', 'pane.panels', 'modeling.mesh', 'modeling.edit_mesh',
    'modeling.mesh_tools', 'modeling.mesh_display', 'modeling.curves',
    'modeling.surfaces', 'modeling.deform', 'modeling.uv', 'modeling.generate',
)


def candidates():
    result = defaultdict(list)
    for spec in SPECS.values():
        for rtc in spec.maya:
            result[rtc].append(spec.id)
    return result


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class BindingDecisionTest(unittest.TestCase):
    def test_review_explicitly_covers_all_eighteen_current_ambiguities(self):
        ambiguous = {rtc for rtc, commands in candidates().items() if len(commands) > 1}
        self.assertEqual(len(EXPECTED_PREFERRED), 8)
        self.assertEqual(len(EXPECTED_DISABLED), 10)
        self.assertEqual(ambiguous, set(EXPECTED_PREFERRED) | EXPECTED_DISABLED)

    def test_preferred_binding_is_independent_of_candidate_order(self):
        original = candidates()
        reversed_candidates = {rtc: list(reversed(ids)) for rtc, ids in original.items()}
        for rtc, expected in EXPECTED_PREFERRED.items():
            for ordering in (original, reversed_candidates):
                with self.subTest(rtc=rtc, ordering=ordering[rtc]):
                    actual, reason = _binding({'maya_command': rtc}, 'modeling.mesh', ordering)
                    self.assertEqual(actual, expected)
                    self.assertTrue(reason, 'An adapted Maya label needs an honest difference')

    def test_disabled_identity_cannot_fall_back_even_to_one_available_candidate(self):
        original = candidates()
        for rtc in EXPECTED_DISABLED:
            for ids in (original[rtc], list(reversed(original[rtc])), original[rtc][:1], []):
                with self.subTest(rtc=rtc, ids=ids):
                    command, reason = _binding({'maya_command': rtc}, 'modeling.mesh', {rtc: ids})
                    self.assertEqual(command, '')
                    self.assertTrue(reason)

    def test_single_candidate_is_not_permission_to_replace_a_different_dialog(self):
        declared = candidates()
        for rtc in EXPECTED_UNAVAILABLE_SINGLETONS:
            with self.subTest(rtc=rtc):
                self.assertEqual(len(declared[rtc]), 1)
                command, reason = _binding({'maya_command': rtc}, 'common.modify', declared)
                self.assertEqual(command, '')
                self.assertTrue(reason)

    def test_existing_core_selection_actions_keep_their_exact_maya_entry(self):
        for rtc, expected in EXPECTED_CORE_SELECTION.items():
            with self.subTest(rtc=rtc):
                self.assertEqual(_binding({'maya_command': rtc}, 'common.select', candidates())[0],
                                 expected)

    def test_unknown_and_unreviewed_ambiguity_do_not_pick_first(self):
        for reference, declared in (
                ({'maya_command': 'UnknownMayaRTC'}, candidates()),
                ({'maya_command': ''}, candidates()),
                ({'maya_command': 'FutureAmbiguousRTC'},
                 {'FutureAmbiguousRTC': ['mesh.fill', 'mesh.fill_holes']}),
                ({'maya_command': 'FutureAmbiguousRTC'},
                 {'FutureAmbiguousRTC': ['mesh.fill_holes', 'mesh.fill']})):
            with self.subTest(reference=reference, declared=declared.get('FutureAmbiguousRTC')):
                command, reason = _binding(reference, 'modeling.mesh', declared)
                self.assertEqual(command, '')
                self.assertTrue(reason)

    def test_reference_command_text_is_inert_and_rtc_is_an_exact_identity(self):
        payload = "__import__('builtins').print('MUST_NOT_EXECUTE')"
        references = (
            {'maya_command': payload, 'command': payload, 'sourceType': 'python'},
            {'maya_command': 'FillHole; ' + payload, 'command': 'FillHole'},
            {'command': 'FillHole', 'runtimeCommand': 'FillHole', 'sourceType': 'mel'},
        )
        with patch('builtins.eval', side_effect=AssertionError('reference eval')), \
                patch('builtins.exec', side_effect=AssertionError('reference exec')):
            for reference in references:
                self.assertEqual(_binding(reference, 'modeling.mesh', candidates())[0], '')
            # Even an executable-looking source field cannot alter a trusted exact identity.
            self.assertEqual(_binding({'maya_command': 'FillHole', 'command': payload},
                                      'modeling.mesh', candidates())[0], 'mesh.fill_holes')


class FinalCatalogBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from axismeld.hotbox_catalog import default_catalog
        from axismeld.maya_menu_reference import REFERENCE_MENUS
        cls.roots = default_catalog()
        cls.entries = list(walk(cls.roots))
        cls.by_id = {entry['id']: entry for entry in cls.entries}
        cls.reference = REFERENCE_MENUS

    def test_all_564_existing_specs_remain_reachable_from_maya_or_blender_extensions(self):
        self.assertEqual(len(SPECS), 564, 'Re-audit a deliberate capability inventory change')
        self.assertIn('internal.blender', self.by_id, 'Maya hierarchy has not been wired yet')
        extension = self.by_id['internal.blender']
        self.assertEqual(extension['kind'], 'menu')
        self.assertTrue(extension['enabled'])
        allowed = [self.by_id[identifier] for identifier in EXPECTED_ROOTS] + [extension]
        reachable = {entry['command'] for entry in walk(allowed) if entry['kind'] == 'command'}
        self.assertEqual(set(SPECS) - reachable, set())
        for command in SPECS:
            self.assertIn('m3.' + command, self.by_id)
            self.assertEqual(self.by_id['m3.' + command]['command'], command)

    def test_blender_only_specs_keep_their_category_and_section_groups(self):
        extension = self.by_id['internal.blender']
        remaining = {entry['command'] for entry in walk((extension,)) if entry['kind'] == 'command'}
        for command in remaining & set(SPECS):
            spec = SPECS[command]
            parent = extension
            with self.subTest(command=command):
                for label in (spec.category, *spec.section):
                    matches = [child for child in parent['children']
                               if child['kind'] == 'menu' and child['label'] == label]
                    self.assertEqual(len(matches), 1, (command, label))
                    parent = matches[0]
                self.assertIn('m3.' + command, {child['id'] for child in parent['children']})

    def test_internal_extensions_do_not_recreate_large_flat_operation_lists(self):
        for entry in walk((self.by_id['internal.blender'],)):
            if entry['kind'] == 'menu':
                body = [child for child in entry['children'] if child['kind'] != 'separator']
                self.assertLessEqual(len(body), 40, entry['id'])

    def test_real_create_primitive_bodies_reuse_core_adapters_but_options_stay_unavailable(self):
        expected = {
            'CreatePolygonSphere': 'mesh.create_sphere',
            'CreatePolygonCube': 'mesh.create_cube',
            'CreatePolygonCylinder': 'mesh.create_cylinder',
            'CreatePolygonCone': 'mesh.create_cone',
            'CreatePolygonTorus': 'mesh.create_torus',
            'CreatePolygonPlane': 'mesh.create_plane',
            'CreatePolygonDisc': 'mesh.create_disc',
        }
        reference = next(root for root in self.reference if root['id'] == 'common.create')
        matched = {}
        for row in walk((reference,)):
            identity = row.get('maya_command')
            if identity not in expected:
                continue
            actual = self.by_id[row['id']]
            matched[identity] = actual['command']
            with self.subTest(identity=identity):
                self.assertEqual(actual['kind'], 'command')
                self.assertTrue(actual['enabled'])
                self.assertEqual(actual['command'], expected[identity])
                self.assertTrue(row.get('options'))
                self.assertEqual(len(actual['children']), 1)
                option = actual['children'][0]
                self.assertEqual(option['kind'], 'disabled')
                self.assertFalse(option['enabled'])
                self.assertEqual(option['command'], '')
        self.assertEqual(matched, expected)

    def test_existing_core_operations_remain_reachable_including_quad_view(self):
        expected = {
            'selection.select_all', 'selection.clear', 'selection.toggle_component',
            'selection.grow', 'selection.shrink', 'selection.vertex_mode',
            'selection.edge_mode', 'selection.face_mode', 'mode.object',
            'transform.move', 'transform.rotate', 'transform.scale', 'tool.select',
            'view.wireframe', 'view.shaded', 'view.frame_all', 'view.focus_selected',
            'view.toggle_quad', 'mesh.create_sphere', 'mesh.create_cube',
            'mesh.create_cylinder', 'mesh.create_cone', 'mesh.create_torus',
            'mesh.create_plane', 'mesh.create_disc',
        }
        reachable = {row['command'] for row in self.entries if row['kind'] == 'command'}
        self.assertEqual(expected - reachable, set())
        quad = self.by_id['pane.panels.toggle_quad']
        self.assertEqual(quad['command'], 'view.toggle_quad')
        self.assertIn(quad, list(walk((self.by_id['internal.blender'],))))

    def test_no_two_nodes_or_different_commands_share_an_id(self):
        identifiers = [entry['id'] for entry in self.entries]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        assigned = {}
        for entry in self.entries:
            if entry['command']:
                self.assertEqual(assigned.setdefault(entry['id'], entry['command']), entry['command'])

    def test_maya_main_trees_have_exact_reference_structure_without_blender_sections(self):
        self.assertEqual(tuple(node['id'] for node in self.reference), EXPECTED_ROOTS)
        seen_preferred = set()
        def compare(actual, expected):
            with self.subTest(path=expected.get('path', expected['id'])):
                self.assertEqual(actual['label'], expected['label'])
                self.assertFalse(actual['id'].startswith('internal.'))
                kind = expected.get('kind', 'menu')
                if kind == 'menu':
                    self.assertEqual(actual['kind'], 'menu')
                    self.assertEqual(len(actual['children']), len(expected.get('children', ())))
                    for child, reference in zip(actual['children'], expected.get('children', ())):
                        compare(child, reference)
                elif kind == 'separator':
                    self.assertEqual(actual['kind'], 'separator')
                    self.assertFalse(actual['enabled'])
                    self.assertEqual(actual['command'], '')
                    self.assertEqual(actual['children'], [])
                else:
                    self.assertIn(actual['kind'], ('command', 'disabled'))
                    self.assertEqual(len(actual['children']), int(bool(expected.get('options'))))
                    rtc = expected.get('maya_command')
                    if rtc in EXPECTED_CORE_SELECTION:
                        self.assertEqual(actual['command'], EXPECTED_CORE_SELECTION[rtc])
                    if rtc in EXPECTED_PREFERRED:
                        seen_preferred.add(rtc)
                        self.assertEqual(actual['command'], EXPECTED_PREFERRED[rtc])
                    if rtc in EXPECTED_DISABLED | EXPECTED_UNAVAILABLE_SINGLETONS:
                        self.assertEqual(actual['kind'], 'disabled')
                        self.assertEqual(actual['command'], '')
                        self.assertFalse(actual['enabled'])
        for expected in self.reference:
            compare(self.by_id[expected['id']], expected)
        self.assertEqual(seen_preferred, set(EXPECTED_PREFERRED))

    def test_real_options_are_disabled_independent_cells_never_reexecuting_main(self):
        found = 0
        def compare_options(actual, expected):
            nonlocal found
            if expected.get('options'):
                found += 1
                self.assertEqual(len(actual['children']), 1)
                option = actual['children'][0]
                self.assertEqual(option['id'], actual['id'] + '.options')
                self.assertEqual(option['label'], 'Options')
                self.assertEqual(option['kind'], 'disabled')
                self.assertFalse(option['enabled'])
                self.assertEqual(option['command'], '')
                self.assertEqual(option['children'], [])
            if expected.get('kind', 'menu') == 'menu':
                self.assertEqual(len(actual['children']), len(expected.get('children', ())))
                for child, reference in zip(actual['children'], expected.get('children', ())):
                    compare_options(child, reference)
        for expected in self.reference:
            compare_options(self.by_id[expected['id']], expected)
        # Independently counted from the captured Maya 2026 reference, not the binder.
        self.assertEqual(found, 369, 'Review a deliberate reference Options inventory change')


if __name__ == '__main__':
    unittest.main()

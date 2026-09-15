# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent Maya application-menubar reference contracts; no bpy or Maya execution."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
COMMON = tuple('common.' + name for name in ('file','edit','create','select','modify','display','windows'))
MODELING = tuple('modeling.' + name for name in ('mesh','edit_mesh','mesh_tools','mesh_display','curves','surfaces','deform','uv','generate'))
TAIL = ('menubar.cache','menubar.flow','menubar.arnold','menubar.help')
SPECIAL = {
    'MODELING': MODELING,
    'RIGGING': ('menubar.rigging.skeleton','menubar.rigging.skin','modeling.deform',
                'menubar.rigging.constrain','menubar.rigging.control','menubar.rigging.bifrost_rigging'),
    'ANIMATION': tuple('menubar.animation.' + name for name in ('key','playback','audio','visualize')) +
                 ('modeling.deform','menubar.rigging.constrain','menubar.mash'),
    'FX': tuple('menubar.fx.' + name for name in ('nparticles','fluids','ncloth','nhair','nconstraint','ncache','fields_solvers','effects')) + ('menubar.mash',),
    'RENDERING': tuple('menubar.rendering.' + name for name in ('lighting_shading','texturing','render','toon','stereo')),
}
EXPECTED = {key: COMMON + value + TAIL for key,value in SPECIAL.items()}


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))
        if node.get('options'):
            yield from walk((node['options'],))


class MenubarReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = runpy.run_path(str(ROOT / 'tools/axismeld/build_menubar_reference.py'))
        cls.source = json.loads(cls.generator['SOURCE'].read_text(encoding='utf-8'))
        cls.data = runpy.run_path(str(ROOT / 'scripts/modules/axismeld/menubar_reference.py'))

    def test_exact_five_visible_sequences_and_no_current_pane(self):
        self.assertEqual(self.data['MENU_SETS'], EXPECTED)
        nodes = self.data['REFERENCE_MENUS']
        self.assertEqual(len(nodes), 43)
        self.assertEqual({n['id'] for n in nodes}, set().union(*map(set, EXPECTED.values())))
        self.assertFalse(any(n['id'].startswith('pane.') for n in nodes))
        by_id = {n['id']: n for n in nodes}
        for raw in self.source['menu_sets']:
            actual = [by_id[i]['label'] for i in self.data['MENU_SETS'][raw['label'].upper()]]
            visible = [n['label'].strip() for n in raw['top_menu_array'] if n['visible']]
            self.assertEqual(actual, visible)

    def test_common_and_modeling_keep_canonical_identities_but_use_warmed_capture(self):
        old = runpy.run_path(str(ROOT / 'scripts/modules/axismeld/maya_menu_reference.py'))['REFERENCE_MENUS']
        by_id = {n['id']: n for n in self.data['REFERENCE_MENUS']}
        for n in old:
            if n['id'] in COMMON + MODELING:
                self.assertEqual(by_id[n['id']]['label'], n['label'])
        self.assertIn('Muscle', [n['label'] for n in by_id['modeling.deform']['children']])
        for key in ('MODELING','RIGGING','ANIMATION'):
            self.assertIn('modeling.deform', self.data['MENU_SETS'][key])
        self.assertFalse(any(n['id'] in ('menubar.rigging.deform','menubar.animation.deform') for n in by_id.values()))

    def test_missing_roots_or_wrong_visible_order_are_rejected(self):
        missing = copy.deepcopy(self.source)
        del missing['trees']['mainRigSkeletonsMenu']
        with self.assertRaises(ValueError):
            self.generator['normalize'](missing)
        wrong = copy.deepcopy(self.source)
        row = wrong['menu_sets'][0]['top_menu_array']
        row[0], row[1] = row[1], row[0]
        with self.assertRaises(ValueError):
            self.generator['normalize'](wrong)

    def test_options_are_distinct_and_all_ids_unique(self):
        nodes = tuple(walk(self.data['REFERENCE_MENUS']))
        self.assertEqual(len(nodes), len({n['id'] for n in nodes}))
        for n in nodes:
            if n.get('options'):
                option = n['options']
                self.assertEqual(option['id'], n['id'] + '.options')
                self.assertEqual(option['label'], 'Options')
                self.assertEqual(option['path'], n['path'] + ('Options',))
                self.assertNotIn(option, n.get('children', ()))

    def test_orphan_options_are_rejected_and_shared_menu_divergence_is_rejected(self):
        orphan = copy.deepcopy(self.source)
        orphan['trees']['mainRigSkeletonsMenu']['children'].insert(0, {
            'path':'orphan','label':'Options','optionBox':True})
        with self.assertRaises(ValueError):
            self.generator['normalize'](orphan)
        divergent = copy.deepcopy(self.source)
        divergent['trees']['mainConstraintsMenu']['children'][0]['label'] = 'Not the same menu'
        divergent['trees']['mainConstraintsMenu']['children'][0]['dividerLabel'] = 'Not the same menu'
        with self.assertRaises(ValueError):
            self.generator['normalize'](divergent)

    def test_capture_commands_are_inert_not_code_or_enable_state(self):
        changed = copy.deepcopy(self.source)
        pending = list(changed['trees'].values())
        while pending:
            n = pending.pop()
            n['command'] = '__import__("os").system("must_not_execute")'
            n['enable'] = not n.get('enable')
            pending.extend(n.get('children', ()))
        with patch('builtins.eval', side_effect=AssertionError('eval forbidden')):
            result = self.generator['normalize'](changed)
        self.assertEqual(result[0], self.data['MENU_SETS'])
        self.assertEqual(result[1], self.data['REFERENCE_MENUS'])
        for n in walk(result[1]):
            self.assertFalse({'command','enabled','checked','sourceType'} & n.keys())

    def test_plugins_are_explicit_dependencies_not_core_defaults(self):
        dependency = self.data['PLUGIN_DEPENDENCIES']
        self.assertTrue({'menubar.flow','menubar.rigging.bifrost_rigging'} <= set(dependency))
        for identifier, evidence in dependency.items():
            self.assertTrue(evidence['plugin'])
            self.assertTrue(evidence['source'])
            self.assertIn(identifier, {n['id'] for n in walk(self.data['REFERENCE_MENUS'])})

    def test_help_and_cache_keep_trees_and_help_label_is_stable(self):
        by_id = {n['id']: n for n in self.data['REFERENCE_MENUS']}
        self.assertEqual(by_id['menubar.help']['label'], 'Help')
        self.assertTrue(by_id['menubar.help']['children'])
        self.assertTrue(by_id['menubar.cache']['children'])
        self.assertEqual([n['label'] for n in by_id['menubar.cache']['children']],
                         ['Alembic Cache','Geometry Cache','GPU Cache'])

    def test_scene_material_and_camera_instances_are_not_static_commands(self):
        nodes = {n.get('path'): n for n in walk(self.data['REFERENCE_MENUS']) if n.get('path')}
        for path in (('Lighting/Shading','Assign Existing Material'), ('Toon','Set Camera Background Color')):
            node = nodes[path]
            self.assertTrue(node['dynamic'])
            self.assertTrue(all(child['kind'] == 'separator' for child in node['children']))
        self.assertEqual([n['label'] for n in nodes['Toon','Assign Outline']['children']],
                         ['Add New Toon Outline','Remove Current Toon Outlines'])
        favorites = nodes['Lighting/Shading','Assign Favorite Material']
        self.assertIn('Lambert', [n['label'] for n in favorites['children']])

    def test_regeneration_is_exact(self):
        for path, expected in self.generator['render']().items():
            self.assertEqual(path.read_text(encoding='utf-8'), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)

# SPDX-License-Identifier: GPL-2.0-or-later
"""Screenshot order and honest capability boundaries for Maya companion alignment."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
from axismeld import hotbox_catalog, hotbox_runtime


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class MayaCompanionAlignmentTest(unittest.TestCase):
    def test_full_json_preserves_unknown_reasons_at_exact_1mib_boundary(self):
        value = hotbox_runtime.make_snapshot(generation=1)
        node = next(n for n in walk(value['menus']) if n['id']=='common.file')
        node['reason'] = 'x'
        base = len(hotbox_runtime.serialize_snapshot(value).encode('utf-8'))
        node['reason'] = 'x' * (1 + hotbox_runtime.MAX_JSON_BYTES-base)
        payload = hotbox_runtime.serialize_snapshot(value)
        self.assertEqual(len(payload.encode('utf-8')), 1024*1024)
        self.assertEqual(json.loads(payload), value)
        node['reason'] += 'x'
        with self.assertRaisesRegex(ValueError,'1 MiB'):
            hotbox_runtime.serialize_snapshot(value)

    def test_creation_screenshot_order_grouping_and_honest_options(self):
        nodes = {node['id']: node for node in walk(hotbox_catalog.default_catalog())}
        menu = nodes['context.create_menu']
        self.assertEqual(menu['presentation'], 'list')
        self.assertEqual([n['label'] for n in menu['children'] if n['kind'] != 'separator'], [
            'Platonic Solid', 'Pyramid', 'Prism', 'Pipe', 'Helix', 'Gear', 'Soccer Ball',
            'Super Ellipse', 'Spherical Harmonics', 'Ultra Shape', 'Type', 'SVG', 'Quad Draw Tool',
            'Interactive Creation', 'Exit On Completion', 'Polygon Display All'])
        self.assertEqual([i for i,n in enumerate(menu['children']) if n['kind'] == 'separator'], [7, 14, 17])
        self.assertEqual(sum(bool(n['children']) and n['kind'] != 'menu' for n in menu['children']), 11)
        for n in menu['children']:
            if n['kind'] != 'menu':
                for option in n['children']:
                    self.assertEqual(option['id'], n['id']+'.options')
                    self.assertEqual((option['kind'], option['enabled'], option['command']), ('disabled', False, ''))
        for suffix, command in (('platonic','mesh.create_icosphere'), ('pyramid','mesh.create_pyramid'),
                                ('prism','mesh.create_prism'), ('type','object.create_text')):
            self.assertEqual(nodes['context.create_menu.'+suffix]['command'], command)
        for suffix in ('pipe','helix','gear','soccer_ball','super_ellipse','spherical_harmonics','ultra_shape','svg','quad_draw'):
            self.assertEqual(nodes['context.create_menu.'+suffix]['kind'], 'disabled')

    def test_radial_options_and_normals_directory_preserve_object_22_rows(self):
        nodes = {node['id']: node for node in walk(hotbox_catalog.default_catalog())}
        for leaf in nodes['context.create']['children']:
            self.assertEqual(len(leaf['children']), 1)
            self.assertEqual(leaf['children'][0]['id'], leaf['id']+'.options')
            self.assertFalse(leaf['children'][0]['enabled'])
        root = nodes['context.modeling_object']
        self.assertEqual({n['id'].split('.')[-1] for n in root['children'] if n['kind'] != 'menu' and n['children']},
                         {'weld','sculpt','knife','append','loopcut'})
        normals = nodes['context.modeling_object.normals']
        self.assertEqual((normals['kind'], normals['presentation']), ('menu','list'))
        self.assertEqual([n['label'] for n in normals['children']],
                         ['Toggle Soft Edge Display','Harden Edge','Soften/Harden Edges','Soften Edge'])
        self.assertTrue(all(n['kind']=='disabled' and not n['command'] for n in normals['children']))
        self.assertEqual(normals['children'][2]['children'][0]['id'], normals['id']+'.angle.options')
        self.assertFalse(normals['children'][2]['children'][0]['enabled'])
        self.assertEqual(sum(n['kind']!='separator' for n in nodes['context.modeling_object_menu']['children']),22)

    def test_only_fixed_disabled_workflow_indicators_are_accepted(self):
        value = hotbox_runtime.make_snapshot(generation=1)
        nodes = {n['id']:n for n in walk(value['menus'])}
        for suffix, checked in (('interactive_creation',False),('exit_on_completion',True)):
            node = nodes['context.create_menu.'+suffix]
            self.assertEqual((node['kind'],node['enabled'],node['command'],node['indicator'],node['checked']),
                             ('disabled',False,'','checkbox',checked))
        hotbox_runtime.serialize_snapshot(value)
        for field, bad in (('id','context.create_menu.unknown'),('indicator','radio'),('enabled',True)):
            copy = deepcopy(value)
            node = next(n for n in walk(copy['menus']) if n['id']=='context.create_menu.exit_on_completion')
            node[field] = bad
            with self.assertRaises(ValueError):
                hotbox_runtime.validate_snapshot(copy)


if __name__ == '__main__':
    unittest.main()

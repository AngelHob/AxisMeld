# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import copy
import json
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))

from axismeld.commands import COMMANDS
from axismeld import hotbox_catalog
from axismeld import hotbox_runtime
from axismeld.hotbox_catalog import default_catalog
from axismeld.hotbox_profiles import HOTBOX_PROFILE_FILENAMES, resolve_hotbox
from axismeld.profiles import resolve_profiles


def nodes(catalog):
    pending = list(catalog)
    while pending:
        node = pending.pop(0)
        yield node
        pending[0:0] = node['children']


def node_by_id(catalog, identifier):
    return next(node for node in nodes(catalog) if node['id'] == identifier)


def menu_node(identifier, children=()):
    return {'id': identifier, 'kind': 'menu', 'label': identifier, 'command': '',
            'enabled': True, 'reason': '', 'children': list(children)}


class HotboxCatalogTest(unittest.TestCase):
    def test_new_view_commands_are_declared_without_default_keybindings(self):
        self.assertTrue(all(COMMANDS[key].key is None
                            for key in ('view.left', 'view.back', 'view.bottom')))

    def test_defaults_and_atomic_layer(self):
        common = next(row for row in default_catalog() if row['id'] == 'common')
        self.assertEqual([node['label'] for node in common['children']], [
            'File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows'])
        good = {'schema_version': 1, 'settings': {'transparency': 50}}
        bad = {'schema_version': 1, 'settings': {'style': 'center', 'transparency': 101}}
        value, errors = resolve_hotbox([('studio', good), ('user', bad)])
        self.assertEqual(value['settings']['transparency'], 50)
        self.assertEqual(value['settings']['style'], 'rows')
        self.assertEqual(len(errors), 1)

    def test_catalog_has_canonical_rows_and_top_level_order(self):
        catalog = default_catalog()
        self.assertEqual([row['id'] for row in catalog], ['common', 'pane', 'center', 'modeling'])
        expected = {
            'common': ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows'],
            'pane': ['View', 'Shading', 'Lighting', 'Show', 'Renderer', 'Panels'],
            'center': ['Recent Commands', 'AxisMeld', 'Hotbox Controls'],
            'modeling': [
                'Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display', 'Curves', 'Surfaces',
                'Deform', 'UV', 'Generate'],
        }
        self.assertEqual({row['id']: [child['label'] for child in row['children']]
                          for row in catalog}, expected)

    def test_catalog_declares_actual_leaf_commands_without_inventing_uv_commands(self):
        catalog = default_catalog()
        self.assertEqual([node['command'] for node in node_by_id(catalog, 'common.select')['children']
                          if node['kind'] == 'command'], [
            'selection.toggle_component', 'selection.vertex_mode',
            'selection.edge_mode', 'selection.face_mode'])
        self.assertEqual([node['command'] for node in node_by_id(catalog, 'common.modify')['children']], [
            'transform.move', 'transform.rotate', 'transform.scale'])
        self.assertEqual([node['command'] for node in node_by_id(catalog, 'pane.view')['children']], [
            'view.focus_selected', 'view.frame_all'])
        self.assertEqual([node['command'] for node in node_by_id(catalog, 'pane.shading')['children']], [
            'view.wireframe', 'view.shaded'])
        self.assertFalse(node_by_id(catalog, 'modeling.uv')['enabled'])
        self.assertEqual(node_by_id(catalog, 'modeling.uv')['children'], [])
        for identifier in ('views.left', 'views.back', 'views.bottom',
                           'pane.panels.left', 'pane.panels.back', 'pane.panels.bottom'):
            self.assertFalse(node_by_id(catalog, identifier)['enabled'])

    def test_catalog_ids_are_unique_and_copies_do_not_share_mutable_nodes(self):
        first = default_catalog()
        identifiers = [node['id'] for node in nodes(first)]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        first[0]['children'][0]['label'] = 'Changed'
        self.assertEqual(default_catalog()[0]['children'][0]['label'], 'File')

    def test_views_and_controls_have_fixed_order_and_setting_values(self):
        catalog = default_catalog()
        expected_views = [
            'view.perspective', 'view.side', 'view.bottom', 'view.front',
            'view.back', 'view.top', 'view.left']
        for identifier in ('views', 'pane.panels.views'):
            menu = node_by_id(catalog, identifier)
            self.assertEqual([node['command'] for node in menu['children']
                              if node['kind'] == 'command'], expected_views)
        for identifier in ('views.style', 'center.controls.style'):
            menu = node_by_id(catalog, identifier)
            self.assertEqual([(node['label'], node['command'], node['value'])
                              for node in menu['children']], [
                ('Zones and Menu Rows', 'style', 'rows'),
                ('Zones Only', 'style', 'zones'),
                ('Center Zone Only', 'style', 'center'),
            ])
        rows = node_by_id(catalog, 'center.controls.rows')
        self.assertEqual([(node['label'], node['command'], node['value'])
                          for node in rows['children']], [
            ('Show Common Menus', 'row.common', 'toggle'),
            ('Show Pane Specific Menus', 'row.pane', 'toggle'),
            ('Show Modeling', 'row.modeling', 'toggle'),
        ])
        transparency = node_by_id(catalog, 'center.controls.transparency')
        self.assertEqual([node['value'] for node in transparency['children']],
                         ['0', '25', '50', '75', '100'])

    def test_hotbox_profile_names_are_separate_from_legacy_keybinding_files(self):
        self.assertEqual(HOTBOX_PROFILE_FILENAMES,
                         ('hotbox_studio.json', 'hotbox_user.json'))

    def test_command_policy_is_narrow_and_explicit(self):
        for command in ('view.perspective', 'view.side', 'view.bottom', 'view.front',
                        'view.back', 'view.top', 'view.left', 'view.focus_selected',
                        'view.frame_all', 'view.wireframe', 'view.shaded'):
            with self.subTest(command=command):
                self.assertEqual(hotbox_catalog.command_policy(command), (False, True))
        for command in ('view.toggle_quad', 'selection.toggle_component',
                        'selection.vertex_mode', 'selection.edge_mode', 'selection.face_mode',
                        'transform.move', 'transform.rotate', 'transform.scale'):
            with self.subTest(command=command):
                self.assertEqual(hotbox_catalog.command_policy(command), (True, True))
        for command in ('hotbox.open', 'style', 'uv.project_planar', 'unknown'):
            with self.subTest(command=command):
                self.assertEqual(hotbox_catalog.command_policy(command), (True, False))

    def test_settings_merge_rows_and_each_center_button(self):
        layers = [
            ('studio', {'schema_version': 1, 'settings': {
                'style': 'zones', 'rows': ['common', 'modeling'],
                'center_buttons': {'LEFTMOUSE': None, 'RIGHTMOUSE': 'pane.panels'},
            }}),
            ('user', {'schema_version': 1, 'settings': {
                'transparency': 75, 'center_buttons': {'MIDDLEMOUSE': 'common.select'},
            }}),
        ]
        original = copy.deepcopy(layers)
        value, errors = resolve_hotbox(layers)
        self.assertEqual(value['settings'], {
            'style': 'zones',
            'transparency': 75,
            'rows': ['common', 'modeling'],
            'center_buttons': {
                'LEFTMOUSE': None,
                'MIDDLEMOUSE': 'common.select',
                'RIGHTMOUSE': 'pane.panels',
            },
        })
        self.assertEqual(errors, [])
        self.assertEqual(layers, original)

    def test_strict_invalid_layers_each_roll_back_atomically(self):
        invalid_settings = [
            {'extra': 1},
            {'style': 'menuRows'},
            {'transparency': True},
            {'transparency': 24},
            {'rows': ['modeling', 'common']},
            {'rows': ['common', 'common']},
            {'rows': ['center']},
            {'center_buttons': {'BUTTON4MOUSE': 'views'}},
            {'center_buttons': {'LEFTMOUSE': 'missing.menu'}},
            {'center_buttons': {'LEFTMOUSE': 7}},
        ]
        for settings in invalid_settings:
            with self.subTest(settings=settings):
                value, errors = resolve_hotbox([
                    ('studio', {'schema_version': 1, 'settings': {'transparency': 50}}),
                    ('user', {'schema_version': 1, 'settings': settings}),
                ])
                self.assertEqual(value['settings']['transparency'], 50)
                self.assertNotIn('extra', value['settings'])
                self.assertEqual(len(errors), 1)
                self.assertIn('user:', errors[0])

    def test_hotbox_layers_do_not_change_legacy_keybinding_schema(self):
        legacy = {'schema_version': 1, 'bindings': {'transform.move': {'type': 'T'}}}
        result = resolve_profiles([('user', legacy)])
        self.assertEqual(result.bindings['transform.move']['type'], 'T')
        self.assertEqual(result.diagnostics, [])

    def test_snapshot_roundtrip_is_strict_and_copy_safe(self):
        self.assertNotIn('bpy', sys.modules)
        first = hotbox_runtime.make_snapshot(generation=7)
        payload = hotbox_runtime.serialize_snapshot(first)
        parsed = json.loads(payload)
        self.assertEqual(set(parsed), {'schema_version', 'generation', 'settings', 'menus'})
        self.assertEqual(parsed['schema_version'], 1)
        self.assertEqual(parsed['generation'], 7)
        self.assertEqual(parsed['settings']['transparency'], 25)
        self.assertEqual([row['id'] for row in parsed['menus']],
                         ['common', 'pane', 'center', 'modeling'])
        parsed['settings']['center_buttons']['RIGHTMOUSE'] = None
        parsed['menus'][0]['children'][0]['label'] = 'Changed'
        second = hotbox_runtime.make_snapshot(generation=8)
        self.assertEqual(second['settings']['center_buttons']['RIGHTMOUSE'], 'views')
        self.assertEqual(second['menus'][0]['children'][0]['label'], 'File')

    def test_snapshot_rejects_unknown_fields_types_ids_commands_and_values(self):
        cases = []

        def changed(mutator):
            value = hotbox_runtime.make_snapshot(generation=1)
            mutator(value)
            return value

        cases.extend((
            changed(lambda value: value.update(extra=True)),
            changed(lambda value: value.__setitem__('schema_version', True)),
            changed(lambda value: value.__setitem__('generation', True)),
            changed(lambda value: value.__setitem__('generation', 0)),
            changed(lambda value: value.__setitem__('generation', math.nan)),
            changed(lambda value: value['settings'].__setitem__('transparency', True)),
            changed(lambda value: value['menus'][0].__setitem__('extra', 'field')),
            changed(lambda value: value['menus'][0].__setitem__('id', '公共')),
            changed(lambda value: value['menus'][0].__setitem__('label', 'x' * 129)),
            changed(lambda value: node_by_id(value['menus'], 'pane.view.frame_all').__setitem__(
                'command', 'unknown.command')),
            changed(lambda value: node_by_id(value['menus'], 'pane.view.frame_all').__setitem__(
                'value', 'not-empty')),
            changed(lambda value: node_by_id(value['menus'], 'views.style.rows').__setitem__(
                'value', 'invalid-style')),
            changed(lambda value: value['settings']['center_buttons'].__setitem__(
                'RIGHTMOUSE', 'missing.menu')),
        ))
        duplicate = changed(lambda value: node_by_id(value['menus'], 'pane').__setitem__('id', 'common'))
        cases.append(duplicate)
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    hotbox_runtime.validate_snapshot(value)

    def test_snapshot_rejects_cycles_excess_depth_node_count_and_size(self):
        cycle = hotbox_runtime.make_snapshot(generation=1)
        cycle['menus'][0]['children'] = [cycle['menus'][0]]
        with self.assertRaisesRegex(ValueError, 'cycle'):
            hotbox_runtime.validate_snapshot(cycle)

        too_deep = hotbox_runtime.make_snapshot(generation=1)
        child = menu_node('depth.8')
        for depth in range(7, 0, -1):
            child = menu_node(f'depth.{depth}', [child])
        too_deep['menus'][0]['children'] = [child]
        with self.assertRaisesRegex(ValueError, 'depth'):
            hotbox_runtime.validate_snapshot(too_deep)

        too_many = hotbox_runtime.make_snapshot(generation=1)
        too_many['menus'][0]['children'] = [menu_node(f'many.{index}') for index in range(257)]
        with self.assertRaisesRegex(ValueError, '256'):
            hotbox_runtime.validate_snapshot(too_many)

        too_large = hotbox_runtime.make_snapshot(generation=1)
        node_by_id(too_large['menus'], 'common.file')['reason'] = 'x' * (256 * 1024)
        with self.assertRaisesRegex(ValueError, '256 KiB'):
            hotbox_runtime.serialize_snapshot(too_large)


if __name__ == '__main__':
    unittest.main()

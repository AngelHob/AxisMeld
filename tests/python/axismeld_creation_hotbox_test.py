# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Creation input/catalog contracts and the boundary to Blender's native operators."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'scripts' / 'modules'))
from axismeld import hotbox_catalog, hotbox_runtime
from axismeld.commands import COMMANDS, baseline_bindings
from axismeld.keymap import generate_keymaps, validate_global_bindings
from axismeld.profiles import resolve_profiles

CREATE_HOTBOX = 'context.create_hotbox'
EXPECTED = {
    'NE': ('disc', 'primitive_circle_add'), 'E': ('sphere', 'primitive_uv_sphere_add'),
    'SE': ('torus', 'primitive_torus_add'), 'S': ('cube', 'primitive_cube_add'),
    'SW': ('cone', 'primitive_cone_add'), 'W': ('cylinder', 'primitive_cylinder_add'),
    'NW': ('plane', 'primitive_plane_add'),
}


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


def profile(event):
    return {'schema_version': 1, 'bindings': {CREATE_HOTBOX: event}}


class CreationHotboxTest(unittest.TestCase):
    def test_default_creation_input_and_unbound_primitive_commands(self):
        bindings = baseline_bindings()
        self.assertIn(CREATE_HOTBOX, bindings)
        self.assertEqual(bindings[CREATE_HOTBOX], {
            'type': 'RIGHTMOUSE', 'value': 'PRESS', 'ctrl': False,
            'shift': True, 'alt': False, 'oskey': False})
        for name, _operator in EXPECTED.values():
            command = 'mesh.create_' + name
            self.assertIn(command, COMMANDS)
            self.assertNotIn(command, bindings)
            self.assertEqual(hotbox_catalog.command_policy(command), (True, True))

    def test_space_create_contains_the_same_radial_primitives(self):
        nodes = {node['id']: node for node in walk(hotbox_catalog.default_catalog())}
        self.assertEqual(nodes['common.create']['kind'], 'menu')
        self.assertEqual([child['id'] for child in nodes['common.create']['children']], ['context.create'])
        menu = nodes['context.create']
        self.assertEqual((menu['label'], menu['presentation']), ('Polygon Primitives', 'radial'))
        children = {child['direction']: child for child in menu['children']}
        self.assertEqual(set(children), {'N', *EXPECTED})
        self.assertFalse(children['N']['enabled'])
        self.assertEqual(children['N']['command'], '')
        self.assertIn('M2c-P01', children['N']['reason'])
        for direction, (name, _operator) in EXPECTED.items():
            self.assertEqual(children[direction]['command'], 'mesh.create_' + name)
            self.assertTrue(children[direction]['enabled'])
        hotbox_runtime.serialize_snapshot(hotbox_runtime.make_snapshot(generation=1))

    def test_creation_commands_cross_the_menu_allowlist_and_recent_policy(self):
        recent = hotbox_runtime.RecentCommands()
        for name, _operator in EXPECTED.values():
            command = 'mesh.create_' + name
            self.assertIn(command, hotbox_runtime.SUPPORTED_COMMANDS)
            recent.record(command)
            self.assertEqual(recent.items()[0], command)
        recent.record(CREATE_HOTBOX)
        self.assertNotIn(CREATE_HOTBOX, recent.items())

    def test_creation_profiles_accept_ctrl_shift_rebinds_and_reject_alt_oskey(self):
        for event in ({'type': 'F13'}, {'type': 'F13', 'ctrl': True},
                      {'type': 'MIDDLEMOUSE', 'shift': True, 'ctrl': True}):
            resolved = resolve_profiles([('user', profile(event))])
            self.assertFalse(resolved.diagnostics, event)
            self.assertEqual(resolved.bindings[CREATE_HOTBOX]['type'], event['type'])
            self.assertEqual(resolved.bindings[CREATE_HOTBOX]['ctrl'], event.get('ctrl', False))
        for event in ({'type': 'F13', 'alt': True}, {'type': 'F13', 'oskey': True},
                      {'type': 'F13', 'value': 'RELEASE'}, {'type': 'RIGHTMOUSE'}):
            resolved = resolve_profiles([('user', profile(event))])
            self.assertTrue(resolved.diagnostics, event)
            self.assertEqual(resolved.bindings, baseline_bindings())
        for modifier in ('ctrl', 'shift', 'alt', 'oskey'):
            resolved = resolve_profiles([('user', {'schema_version': 1, 'bindings': {
                'context.component_hotbox': {'type': 'F13', modifier: True}}})])
            self.assertTrue(resolved.diagnostics, modifier)

    def test_context_fallback_survives_regeneration_rebind_and_disable(self):
        cursor = ('view3d.cursor3d', {'type': 'RIGHTMOUSE', 'value': 'PRESS', 'shift': True}, None)
        drag = ('transform.translate', {'type': 'RIGHTMOUSE', 'value': 'CLICK_DRAG', 'shift': True},
                {'properties': [('cursor_transform', True)]})
        native = ('wm.call_menu', {'type': 'RIGHTMOUSE', 'value': 'PRESS'}, None)
        base = [('Object Mode', {}, {'items': [cursor, native]}),
                ('Mesh', {}, {'items': [cursor, native]}),
                ('3D View', {}, {'items': [cursor, drag]}),
                ('UV Editor', {}, {'items': [cursor, drag]})]
        bindings = baseline_bindings()
        self.assertIn(CREATE_HOTBOX, bindings)
        active = generate_keymaps(base, bindings)
        self.assertEqual(generate_keymaps(active, bindings), active)
        for name, _args, content in active[:2]:
            own = next(index for index, item in enumerate(content['items'])
                       if item[0] == 'axismeld.command' and
                       ('command', CREATE_HOTBOX) in item[2]['properties'])
            self.assertLess(own, content['items'].index(cursor), name)
        self.assertIn(cursor, active[2][2]['items'])
        self.assertIn(drag, active[2][2]['items'])
        self.assertEqual(active[3], base[3])
        for event in (None, {'type': 'F13', 'value': 'PRESS', 'ctrl': True}):
            changed = generate_keymaps(active, {**bindings, CREATE_HOTBOX: event})
            for _name, _args, content in changed[:2]:
                self.assertIn(cursor, content['items'])
                self.assertIn(native, content['items'])
                own = [item for item in content['items'] if item[0] == 'axismeld.command' and
                       ('command', CREATE_HOTBOX) in item[2]['properties']]
                self.assertEqual(len(own), int(event is not None))
                if event:
                    self.assertEqual(own[0][1], event)

    def test_global_modified_shortcuts_are_not_exempted(self):
        self.assertIn(CREATE_HOTBOX, baseline_bindings())
        base = [('Screen', {}, {'items': [('screen.other', {
            'type': 'RIGHTMOUSE', 'value': 'PRESS', 'shift': True}, None)]})]
        with self.assertRaisesRegex(ValueError, 'global input conflict'):
            validate_global_bindings(base, baseline_bindings())


class CreationAdapterTest(unittest.TestCase):
    def setUp(self):
        # bpy is a compiled host dependency; these doubles only capture the adapter's
        # native call boundary. Geometry and undo results require the real GUI suite.
        self.calls = []
        self.native_available = True
        def operation(name):
            def call(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {'FINISHED'}
            call.poll = lambda: self.native_available
            return call
        host = SimpleNamespace(ops=SimpleNamespace(
            mesh=SimpleNamespace(**{name: operation(name) for _suffix, name in EXPECTED.values()}),
            view3d=SimpleNamespace(axismeld_hotbox=operation('hotbox'))))
        spec = importlib.util.spec_from_file_location(
            'axismeld._creation_test_adapter', root / 'scripts/modules/axismeld/adapter.py')
        self.adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'bpy': host}):
            spec.loader.exec_module(self.adapter)
        self.context = SimpleNamespace(
            area=SimpleNamespace(type='VIEW_3D'), region=SimpleNamespace(type='WINDOW'),
            mode='OBJECT', selected_objects=[],
            scene=SimpleNamespace(is_editable=True, cursor=SimpleNamespace(location=(2, 3, 4))))

    def test_primitive_commands_allow_existing_object_selection_but_entry_requires_empty(self):
        self.assertTrue(self.adapter.available(self.context, 'mesh.create_cube')[0])
        self.assertTrue(self.adapter.available(self.context, CREATE_HOTBOX)[0])
        self.context.selected_objects = [object()]
        self.assertTrue(self.adapter.available(self.context, 'mesh.create_cube')[0])
        self.assertFalse(self.adapter.available(self.context, CREATE_HOTBOX)[0])
        self.context.mode = 'EDIT_MESH'
        self.assertFalse(self.adapter.available(self.context, 'mesh.create_cube')[0])
        with self.assertRaises(ValueError):
            self.adapter.run(self.context, 'mesh.create_cube')
        self.assertEqual(self.calls, [])

    def test_native_poll_is_rechecked_before_creation(self):
        self.assertTrue(self.adapter.available(self.context, 'mesh.create_cube')[0])
        self.native_available = False
        self.assertFalse(self.adapter.available(self.context, 'mesh.create_cube')[0])
        with self.assertRaises(ValueError):
            self.adapter.run(self.context, 'mesh.create_cube')
        self.assertEqual(self.calls, [])

    def test_uneditable_scene_rejects_creation_including_torus_without_native_poll(self):
        self.context.scene.is_editable = False
        for command in (CREATE_HOTBOX, *('mesh.create_' + name for name, _native in EXPECTED.values())):
            self.assertFalse(self.adapter.available(self.context, command)[0], command)
            with self.assertRaises(ValueError):
                self.adapter.run(self.context, command)
        self.assertEqual(self.calls, [])

    def test_all_primitives_use_exec_native_undo_and_live_cursor(self):
        self.assertIn('mesh.create_cube', COMMANDS)
        for index, (name, native) in enumerate(EXPECTED.values()):
            self.context.scene.cursor.location = (index, 3, -2)
            result = self.adapter.run(self.context, 'mesh.create_' + name)
            self.assertEqual(result, {'FINISHED'})
            operation, args, properties = self.calls[-1]
            self.assertEqual(operation, native)
            self.assertEqual(args, ('EXEC_DEFAULT', True))
            self.assertEqual(properties['location'], (index, 3, -2))
            self.assertEqual(properties['align'], 'WORLD')
            self.assertEqual(properties['rotation'], (0.0, 0.0, 0.0))
            if name == 'torus':
                # AddTorus has no enter_editmode RNA property; its native preference
                # behavior (Object or Edit Mesh) and undo are tested in the GUI host.
                self.assertNotIn('enter_editmode', properties)
                self.assertIn('Enter Edit Mode preference', COMMANDS['mesh.create_torus'].difference)
            else:
                self.assertIs(properties['enter_editmode'], False)
            if name == 'disc':
                self.assertEqual(properties['fill_type'], 'NGON')
        self.assertEqual(len(self.calls), 7)


if __name__ == '__main__':
    unittest.main()

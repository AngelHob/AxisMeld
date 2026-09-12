# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_catalog, hotbox_runtime
from axismeld.commands import COMMANDS, baseline_bindings
from axismeld.keymap import generate_keymaps, validate_global_bindings
from axismeld.profiles import resolve_profiles


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class ComponentHotboxTest(unittest.TestCase):
    def test_component_ring_and_disabled_slots(self):
        nodes = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}
        self.assertIn('context.components', nodes)
        ring = {n['direction']: n for n in nodes['context.components']['children']}
        self.assertEqual({d: ring[d]['command'] for d in ('N', 'W', 'S', 'NE')},
                         {'N': 'selection.edge_mode', 'W': 'selection.vertex_mode',
                          'S': 'selection.face_mode', 'NE': 'mode.object'})
        for direction, reason in [('E', 'deferred-uv'), ('SW', 'M2-vertex-face'), ('SE', 'M2-multi-component')]:
            self.assertFalse(ring[direction]['enabled'])
            self.assertEqual(ring[direction]['command'], '')
            self.assertIn(reason, ring[direction]['reason'])
        self.assertIn('mode.object', hotbox_runtime.SUPPORTED_COMMANDS)
        self.assertEqual(hotbox_catalog.command_policy('mode.object'), (True, True))
        hotbox_runtime.serialize_snapshot(hotbox_runtime.make_snapshot(generation=1))

    def test_component_profile_rejects_modifiers_and_release(self):
        for changes in ({'alt': True}, {'ctrl': True}, {'shift': True}, {'oskey': True}, {'value': 'RELEASE'}):
            profile = {'schema_version': 1, 'bindings': {'context.component_hotbox': {'type': 'F13', **changes}}}
            resolved = resolve_profiles([('user', profile)])
            self.assertTrue(resolved.diagnostics, changes)
            self.assertEqual(resolved.bindings['context.component_hotbox']['type'], 'RIGHTMOUSE')

    def test_native_area_edge_binding_is_preserved_but_real_global_conflicts_fail(self):
        args = {'space_type': 'EMPTY', 'region_type': 'WINDOW'}
        event = {'type': 'RIGHTMOUSE', 'value': 'PRESS'}
        base = [('Screen Editing', args, {'items': [('screen.area_options', event, None)]})]
        validate_global_bindings(base, baseline_bindings())
        self.assertEqual(generate_keymaps(base, baseline_bindings())[0], base[0])
        for name, operator in [('Screen', 'screen.area_options'), ('Screen Editing', 'wm.call_menu')]:
            with self.assertRaises(ValueError):
                validate_global_bindings([(name, args, {'items': [(operator, event, None)]})], baseline_bindings())

    def test_binding_preserves_native_fallback_and_reconfiguration(self):
        native = ('wm.call_menu', {'type': 'RIGHTMOUSE', 'value': 'PRESS'}, None)
        base = [('Object Mode', {}, {'items': [native]}), ('Mesh', {}, {'items': [native]})]
        bindings = baseline_bindings()
        self.assertIn('context.component_hotbox', bindings)
        active = generate_keymaps(base, bindings)
        for name, _, content in active:
            if name in {'Object Mode', 'Mesh'}:
                self.assertEqual(content['items'][0][2]['properties'], [('command', 'context.component_hotbox')])
                self.assertIn(native, content['items'])
        self.assertEqual(generate_keymaps(active, bindings), active)
        for event in (None, {'type': 'F13', 'value': 'PRESS'}):
            changed = generate_keymaps(active, {**bindings, 'context.component_hotbox': event})
            for name, _, content in changed:
                if name in {'Object Mode', 'Mesh'}:
                    self.assertIn(native, content['items'])
                    owned = [i for i in content['items'] if i[0] == 'axismeld.command' and i[2]['properties'] == [('command', 'context.component_hotbox')]]
                    self.assertEqual(len(owned), int(event is not None))
                    if owned:
                        self.assertEqual(owned[0][1]['type'], 'F13')

if __name__ == '__main__':
    unittest.main()

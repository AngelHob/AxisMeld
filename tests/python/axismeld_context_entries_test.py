# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_catalog, hotbox_runtime, tool_hotbox
from axismeld.commands import baseline_bindings
from axismeld.keymap import generate_keymaps


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class ContextEntriesTest(unittest.TestCase):
    def test_conversion_reference_directions_and_gaps(self):
        nodes = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}
        root = nodes['context.convert']
        self.assertEqual({n['direction']: n['label'] for n in root['children']}, {
            'N': 'To Edges', 'NW': 'Shrink Selection', 'E': 'To UVs',
            'SE': 'Edge Loop Utilities', 'SW': 'Edge Ring Utilities',
            'S': 'To Faces', 'W': 'To Vertices', 'NE': 'Grow Selection'})
        self.assertEqual(nodes['context.convert.vertices.vertices']['command'], 'selection.convert_vert')
        self.assertEqual(nodes['context.convert.edges.edges']['command'], 'selection.convert_edge')
        self.assertEqual(nodes['context.convert.faces.faces']['command'], 'selection.convert_face')
        self.assertEqual(nodes['context.convert_menu.face_path']['command'], 'selection.face_path')
        self.assertIn('two preselected Blender faces', nodes['context.convert_menu.face_path']['reason'])
        self.assertFalse(nodes['context.convert.uv.uv']['enabled'])
        self.assertEqual(nodes['context.convert.uv.uv']['command'], '')
        self.assertEqual(len([n for n in nodes['context.convert_menu']['children'] if n['kind'] != 'separator']), 7)
        hotbox_runtime.serialize_snapshot(hotbox_runtime.make_snapshot(generation=1))

    def test_current_tool_resolution_is_read_only_and_has_no_guess(self):
        for identifier, root in [('builtin.select_box', 'tools.select'), ('builtin.select_lasso', 'tools.select'),
                                 ('builtin.move', 'tools.move'), ('builtin.rotate', 'tools.rotate'),
                                 ('builtin.scale', 'tools.scale'), ('builtin.knife', None)]:
            calls = []
            def from_mode(mode, *, create):
                calls.append((mode, create))
                return SimpleNamespace(idname=identifier)
            context = SimpleNamespace(mode='EDIT_MESH', workspace=SimpleNamespace(
                tools=SimpleNamespace(from_space_view3d_mode=from_mode)))
            self.assertEqual(tool_hotbox.current_tool_root(context), root)
            self.assertEqual(calls, [('EDIT_MESH', False)])

    def test_bindings_and_native_fallback(self):
        bindings = baseline_bindings()
        for command, shift in [('context.conversion_hotbox', False), ('context.tool_hotbox', True)]:
            self.assertEqual(bindings[command], dict(type='RIGHTMOUSE', value='PRESS', ctrl=True,
                                                    shift=shift, alt=False, oskey=False))
        native = ('wm.call_menu', {'type': 'RIGHTMOUSE', 'value': 'PRESS', 'ctrl': True}, None)
        base = [(name, {}, {'items': [native]}) for name in ('Object Mode', 'Mesh', 'Curve')]
        generated = generate_keymaps(base, bindings)
        for name, _, content in generated:
            commands = [dict(item[2]['properties'])['command'] for item in content['items']
                        if item[0] == 'axismeld.command']
            self.assertEqual('context.conversion_hotbox' in commands, name in {'Object Mode', 'Mesh'})
            self.assertEqual('context.tool_hotbox' in commands, name in {'Object Mode', 'Mesh'})
            if name != 'AxisMeld Hotbox':
                self.assertIn(native, content['items'])
        self.assertEqual(generate_keymaps(generated, bindings), generated)

    def test_non_modeling_paint_maps_are_preserved(self):
        native = ('grease_pencil.brush_stroke', {'type': 'LEFTMOUSE', 'value': 'PRESS', 'alt': True}, None)
        base = [('3D View Tool: Paint Grease Pencil, Draw', {}, {'items': [native]})]
        self.assertEqual(generate_keymaps(base, baseline_bindings())[0], base[0])


if __name__ == '__main__':
    unittest.main()

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld.commands import baseline_bindings, COMMANDS
from axismeld.profiles import resolve_profiles, load_profiles
from axismeld.keymap import generate_keymaps
from axismeld.keymap import validate_global_bindings


def profile(**bindings):
    return {'schema_version': 1, 'bindings': bindings}


class ProfilesTest(unittest.TestCase):
    def test_maya_baseline(self):
        expected = {'tool.select': 'Q', 'transform.move': 'W', 'transform.rotate': 'E',
                    'transform.scale': 'R', 'selection.toggle_component': 'F8',
                    'selection.vertex_mode': 'F9', 'selection.edge_mode': 'F10',
                    'selection.face_mode': 'F11', 'view.focus_selected': 'F', 'view.frame_all': 'A'}
        self.assertEqual({key: baseline_bindings()[key]['type'] for key in expected}, expected)
        self.assertTrue(all(command.status == 'adapted' for command in COMMANDS.values()))

    def test_hotbox_is_bound_but_menu_view_commands_are_known_and_unbound(self):
        bindings = baseline_bindings()
        self.assertEqual(bindings['hotbox.open']['type'], 'SPACE')
        self.assertEqual(bindings['hotbox.open']['value'], 'PRESS')
        self.assertEqual(set(COMMANDS) - set(bindings), {
            'view.toggle_quad', 'view.perspective', 'view.side', 'view.front', 'view.top',
            'view.left', 'view.back', 'view.bottom', 'selection.select_all',
            'selection.grow', 'selection.shrink', 'selection.clear', 'selection.marquee',
            'selection.lasso', 'selection.paint', 'orientation.move.world',
            'orientation.move.object', 'orientation.move.normal', 'orientation.move.view',
            'orientation.rotate.world', 'orientation.rotate.object', 'orientation.rotate.normal',
            'orientation.rotate.view', 'orientation.rotate.gimbal', 'orientation.scale.world',
            'orientation.scale.object', 'orientation.scale.normal', 'orientation.scale.view'})

    def test_unbound_menu_command_can_be_remapped_and_hotbox_disabled(self):
        result = resolve_profiles([('user', profile(**{
            'view.front': {'type': 'K'},
            'hotbox.open': None,
        }))])
        self.assertEqual(result.bindings['view.front']['type'], 'K')
        self.assertIsNone(result.bindings['hotbox.open'])
        self.assertEqual(result.sources['view.front'], 'user')
        self.assertEqual(result.diagnostics, [])

    def test_mouse_hotbox_override_rolls_back_only_invalid_layer(self):
        result = resolve_profiles([
            ('studio', profile(**{'hotbox.open': {'type': 'F13'}})),
            ('user', profile(**{
                'hotbox.open': {'type': 'LEFTMOUSE'},
                'transform.move': {'type': 'T'},
            })),
        ])
        self.assertEqual(result.bindings['hotbox.open']['type'], 'F13')
        self.assertEqual(result.bindings['transform.move']['type'], 'W')
        self.assertEqual(result.sources['hotbox.open'], 'studio')
        self.assertEqual(len(result.diagnostics), 1)
        self.assertIn('keyboard', result.diagnostics[0])

    def test_precedence_disable_and_no_mutation(self):
        baseline = baseline_bindings()
        layers = [('studio', profile(**{'transform.move': {'type': 'T'}})),
                  ('user', profile(**{'transform.move': {'type': 'Y'}, 'transform.rotate': None})),
                  ('session', profile(**{'transform.move': {'type': 'U'}}))]
        original = copy.deepcopy(layers)
        result = resolve_profiles(layers)
        self.assertEqual(result.bindings['transform.move']['type'], 'U')
        self.assertIsNone(result.bindings['transform.rotate'])
        self.assertEqual(result.sources['transform.move'], 'session')
        self.assertEqual(layers, original)
        self.assertEqual(baseline_bindings(), baseline)

    def test_invalid_layer_rolls_back_atomically(self):
        result = resolve_profiles([
            ('studio', profile(**{'transform.move': {'type': 'T'}})),
            ('user', profile(**{'transform.move': {'type': 'R'}, 'tool.select': None})),
        ])
        self.assertEqual(result.bindings['transform.move']['type'], 'T')
        self.assertIsNotNone(result.bindings['tool.select'])
        self.assertIn('user', result.diagnostics[0])
        self.assertIn('conflict', result.diagnostics[0])

    def test_bad_schema_unknown_command_and_event(self):
        bad_profiles = [None, {'schema_version': 2, 'bindings': {}},
                        {'schema_version': True, 'bindings': {}},
                        profile(**{'uv.unknown': {'type': 'U'}}),
                        profile(**{'transform.move': {'type': 'TEXTINPUT'}}),
                        profile(**{'transform.move': {'type': 'T', 'ctrl': 'false'}}),
                        profile(**{'transform.move': {'type': 'T', 'value': 'RELEASE'}}),
                        profile(**{'transform.move': {'type': 'T', 'any': True}})]
        for value in bad_profiles:
            with self.subTest(value=value):
                result = resolve_profiles([('user', value)])
                self.assertEqual(result.bindings, baseline_bindings())
                self.assertEqual(len(result.diagnostics), 1)

    def test_file_recovery_and_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'studio.json').write_text(json.dumps(profile(**{'transform.move': {'type': 'T'}})))
            (root / 'user.json').write_text('{broken')
            result = load_profiles(root)
            self.assertEqual(result.bindings['transform.move']['type'], 'T')
            self.assertTrue(result.diagnostics)
            self.assertEqual((root / 'user.json').read_text(), '{broken')
            result = load_profiles(root, session=profile(**{'transform.move': {'type': 'U'}}))
            self.assertEqual(result.sources['transform.move'], 'session')
            (root / 'user.json').write_text(' ' * 65537)
            self.assertTrue(load_profiles(root).diagnostics)


class KeymapTest(unittest.TestCase):
    def test_axis_events_precede_fallback_without_touching_navigation(self):
        items = [('transform.translate', {'type': 'MIDDLEMOUSE', 'value': 'PRESS'}, None),
                 ('view3d.move', {'type': 'MIDDLEMOUSE', 'value': 'PRESS', 'alt': True}, None)]
        base = [('3D View Tool: Move', {'space_type': 'VIEW_3D'}, {'items': items}),
                ('Generic Gizmo Maybe Drag', {'space_type': 'EMPTY'}, {'items': [
                    ('gizmogroup.gizmo_tweak', {'type': 'LEFTMOUSE', 'value': 'CLICK_DRAG'}, None)]}),
                ('UV Editor', {'space_type': 'EMPTY'}, {'items': items}),
                ('3D View', {'space_type': 'VIEW_3D'}, {'items': []})]
        original = copy.deepcopy(base)
        result = generate_keymaps(base, baseline_bindings())
        self.assertEqual(result[0][2]['items'][0],
                         ('axismeld.axis_drag', {'type': 'MIDDLEMOUSE', 'value': 'PRESS'}, None))
        self.assertTrue(any(op == 'axismeld.command' and event['type'] == 'MIDDLEMOUSE'
                            and event.get('alt') and data['properties'] == [('command', 'view.pan')]
                            for op, event, data in result[3][2]['items']))
        self.assertEqual(result[1][2]['items'][0],
                         ('axismeld.axis_select', {'type': 'LEFTMOUSE', 'value': 'CLICK'}, None))
        self.assertIn(original[1][2]['items'][0], result[1][2]['items'])
        self.assertEqual(result[2], original[2])
        self.assertEqual(base, original)

    def test_global_shortcut_collision_rejects_only_bad_layer(self):
        base = [('Window', {'space_type': 'EMPTY'}, {'items': [
            ('wm.quit_blender', {'type': 'Q', 'value': 'PRESS', 'ctrl': True}, None)]})]
        result = resolve_profiles([
            ('studio', profile(**{'transform.move': {'type': 'T'}})),
            ('user', profile(**{'transform.move': {'type': 'Q', 'ctrl': True}})),
        ], validate=lambda candidate: validate_global_bindings(base, candidate))
        self.assertEqual(result.bindings['transform.move']['type'], 'T')
        self.assertIn('wm.quit_blender', result.diagnostics[0])

    def test_only_original_frames_space_play_may_overlap_hotbox(self):
        frames = [('Frames', {'space_type': 'EMPTY', 'region_type': 'WINDOW'}, {'items': [
            ('screen.animation_play', {'type': 'SPACE', 'value': 'PRESS'}, None)]})]
        validate_global_bindings(frames, baseline_bindings())
        for changed, shifted in (
                ([('Frames', {'space_type': 'EMPTY', 'region_type': 'WINDOW'}, {'items': [
                    ('screen.animation_cancel', {'type': 'SPACE', 'value': 'PRESS'}, None)]})], False),
                ([('Screen', {'space_type': 'EMPTY', 'region_type': 'WINDOW'}, {'items': [
                    ('screen.animation_play', {'type': 'SPACE', 'value': 'PRESS'}, None)]})], False),
                ([('Frames', {'space_type': 'EMPTY', 'region_type': 'WINDOW'}, {'items': [
                    ('screen.animation_play', {'type': 'SPACE', 'value': 'PRESS', 'shift': True}, None)]})], True),
        ):
            with self.subTest(changed=changed):
                bindings = baseline_bindings()
                bindings['hotbox.open'] = {
                    'type': 'SPACE', 'value': 'PRESS', 'ctrl': False,
                    'shift': shifted, 'alt': False, 'oskey': False}
                with self.assertRaisesRegex(ValueError, 'global input conflict'):
                    validate_global_bindings(changed, bindings)

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'user.json').write_text(
                '{"schema_version":1,"bindings":{"tool.select":null,"tool.select":{"type":"U"}}}')
            result = load_profiles(directory)
            self.assertEqual(result.bindings, baseline_bindings())
            self.assertIn('duplicate JSON key', result.diagnostics[0])

    def test_replaces_modeling_keys_but_preserves_other_editors_and_modal_maps(self):
        def km(name, space, items, **extra):
            return (name, {'space_type': space, 'region_type': 'WINDOW', **extra}, {'items': items})
        old = [('mesh.old', {'type': 'W', 'value': 'PRESS'}, None),
               ('mesh.wild', {'type': 'W', 'value': 'CLICK', 'any': True}, None),
               ('mesh.shift_w', {'type': 'W', 'value': 'PRESS', 'shift': True}, None),
               ('mesh.old_space', {'type': 'SPACE', 'value': 'PRESS'}, None)]
        base = [km('Mesh', 'EMPTY', old), km('Object Mode', 'EMPTY', []),
                km('3D View', 'VIEW_3D', []), km('Text', 'TEXT_EDITOR', old),
                km('Transform Modal Map', 'EMPTY', old, modal=True)]
        original = copy.deepcopy(base)
        bindings = resolve_profiles([('user', profile(**{'transform.move': {'type': 'T'}}))]).bindings
        generated = generate_keymaps(base, bindings)
        self.assertEqual(base, original)
        generated_by_name = {entry[0]: entry for entry in generated}
        self.assertEqual(generated_by_name['Text'], base[3])
        self.assertEqual(generated_by_name['Transform Modal Map'], base[4])
        hotbox = [entry for entry in generated if entry[0] == 'AxisMeld Hotbox']
        self.assertEqual(len(hotbox), 1)
        self.assertEqual(hotbox[0][1], {'space_type': 'VIEW_3D', 'region_type': 'WINDOW'})
        self.assertEqual(hotbox[0][2]['items'], [
            ('axismeld.command', baseline_bindings()['hotbox.open'],
             {'properties': [('command', 'hotbox.open')]})])
        items = generated[0][2]['items']
        self.assertNotIn('mesh.old', [item[0] for item in items])
        self.assertNotIn('mesh.wild', [item[0] for item in items])
        self.assertNotIn('mesh.old_space', [item[0] for item in items])
        self.assertIn('mesh.shift_w', [item[0] for item in items])
        events = [event for op, event, data in items if op == 'axismeld.command']
        self.assertTrue(any(event['type'] == 'T' for event in events))
        self.assertFalse(any(event['type'] == 'W' for event in events))

    def test_hotbox_map_is_not_duplicated_when_regenerating_generated_data(self):
        base = [('3D View', {'space_type': 'VIEW_3D', 'region_type': 'WINDOW'}, {'items': []})]
        once = generate_keymaps(base, baseline_bindings())
        twice = generate_keymaps(once, baseline_bindings())
        self.assertEqual(sum(name == 'AxisMeld Hotbox' for name, _args, _content in twice), 1)


if __name__ == '__main__':
    unittest.main()

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import copy
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_catalog, hotbox_runtime
from axismeld.commands import COMMANDS, baseline_bindings


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class ToolHotboxTest(unittest.TestCase):
    def test_tool_roots_are_reachable_with_verified_move_directions(self):
        menus = hotbox_catalog.default_catalog()
        nodes = {n['id']: n for n in walk(menus)}
        for tool in ('select', 'move', 'rotate', 'scale'):
            self.assertIn('tools.' + tool, tuple(nodes))
        self.assertEqual({n['direction']: n['label'] for n in nodes['tools.move']['children']},
                         {'W': 'World', 'NW': 'Object', 'NE': 'Component',
                          'SE': 'Keep Spacing', 'N': 'Symmetry', 'S': 'Select',
                          'E': 'Snap', 'SW': 'Axis'})
        self.assertLessEqual(len(nodes), hotbox_runtime.MAX_NODES)
        self.assertEqual(len(menus), 18)
        self.assertEqual(menus[4]['id'], 'context.modeling_object_menu')
        self.assertEqual(menus[5]['id'], 'context.create_menu')

    def test_other_tool_slots_are_classic_maya_and_placeholders_never_dispatch(self):
        nodes = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}
        for tool, expected in {
            'select': {'N': 'Symmetry', 'NE': 'Drag', 'E': 'Camera-Based Selection',
                       'SE': 'Clear Selection', 'S': 'Select', 'SW': 'Lasso',
                       'W': 'Paint Select', 'NW': 'Marquee'},
            'rotate': {'N': 'Symmetry', 'NE': 'Component', 'E': 'Gimbal',
                       'SE': 'Discrete Rotate', 'S': 'Select', 'SW': 'Custom',
                       'W': 'World', 'NW': 'Object'},
            'scale': {'N': 'Symmetry', 'NE': 'Component', 'E': 'Snap Scale',
                      'SE': 'Relative', 'S': 'Select', 'SW': 'Axis', 'W': 'World', 'NW': 'Object'},
        }.items():
            self.assertEqual({n['direction']: n['label'] for n in nodes['tools.' + tool]['children']}, expected)
        for node in nodes.values():
            if not node['id'].startswith('tools.'):
                continue
            if node['kind'] == 'disabled':
                self.assertFalse(node['enabled'])
                self.assertEqual(node['command'], '')
                self.assertRegex(node['reason'], r'^M1-P0[1-9]:')
            elif node['kind'] == 'command':
                command = node['command']
                self.assertIn(command, COMMANDS)
                self.assertIn(command, hotbox_runtime.SUPPORTED_COMMANDS)
                self.assertEqual(hotbox_catalog.command_policy(command), (True, True))
                if command.startswith(('orientation.', 'selection.marquee', 'selection.paint', 'selection.lasso')):
                    self.assertNotIn(command, baseline_bindings())
                elif command == 'selection.clear':
                    self.assertEqual(baseline_bindings()[command]['type'], 'D')
                    self.assertTrue(baseline_bindings()[command]['alt'])
        self.assertNotIn('orientation.move.gimbal', COMMANDS)
        self.assertNotIn('orientation.scale.gimbal', COMMANDS)

    def test_optional_metadata_round_trip_and_strict_placement(self):
        snap = hotbox_runtime.make_snapshot(generation=1)
        parent = snap['menus'][0]['children'][3]
        parent['presentation'] = 'radial'
        parent['children'] = [child for child in parent['children'] if child['kind'] == 'command'][:3]
        for child, direction in zip(parent['children'], ('N', 'E', 'S')):
            child['direction'] = direction
        hotbox_runtime.serialize_snapshot(snap)
        for change in ('invalid', 'duplicate', 'list', 'root', 'command'):
            bad = copy.deepcopy(snap)
            p = bad['menus'][0]['children'][3]
            if change == 'invalid':
                p['children'][0]['direction'] = 'UP'
            elif change == 'duplicate':
                p['children'][2]['direction'] = 'N'
            elif change == 'list':
                p['presentation'] = 'list'
            elif change == 'root':
                bad['menus'][0]['direction'] = 'N'
            else:
                p['children'][0]['presentation'] = 'list'
            with self.subTest(change=change), self.assertRaises(ValueError):
                hotbox_runtime.serialize_snapshot(bad)

    def test_nested_marking_choices_preserve_maya_slots_and_native_commands(self):
        nodes = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}
        for tool in ('select', 'move', 'rotate', 'scale'):
            p = 'tools.' + tool
            select = nodes[p + '.select']
            self.assertEqual(select['presentation'], 'radial')
            self.assertEqual({n['direction']: n['label'] for n in select['children']},
                             {'N': 'Preselection Highlight', 'NE': 'Highlight Nearest Component',
                              'E': 'Highlight Backfaces', 'SE': 'Asset Centric',
                              'S': 'Soft Select', 'SW': 'Clear Selection',
                              'W': 'Camera-Based Selection', 'NW': 'Marquee'})
            self.assertEqual(nodes[p + '.select.clear']['command'], 'selection.clear')
            self.assertEqual(nodes[p + '.select.soft']['presentation'], 'radial')
            self.assertEqual(nodes[p + '.symmetry']['presentation'], 'radial')
        for tool in ('move', 'rotate', 'scale'):
            p = 'tools.' + tool
            self.assertEqual(nodes[p + '.world']['command'], f'orientation.{tool}.world')
            self.assertEqual(nodes[p + '.object']['command'], f'orientation.{tool}.object')
            # Recent Commands and keymap labels consume command metadata, not menu labels.
            self.assertEqual(COMMANDS[f'orientation.{tool}.world'].label, 'Global')
            self.assertEqual(COMMANDS[f'orientation.{tool}.object'].label, 'Local')
            self.assertEqual(nodes[p + '.axis']['presentation'], 'radial')
        self.assertEqual(nodes['tools.move.axis.custom']['presentation'], 'radial')
        self.assertEqual(nodes['tools.move.snap']['presentation'], 'radial')
        # Whole expanded tree must survive the real serializer, not only its builder.
        hotbox_runtime.serialize_snapshot(hotbox_runtime.make_snapshot(generation=2))

    def test_radial_child_requires_direction(self):
        snap = hotbox_runtime.make_snapshot(generation=1)
        nodes = {n['id']: n for n in walk(snap['menus'])}
        del nodes['tools.move.symmetry']['direction']
        with self.assertRaises(ValueError):
            hotbox_runtime.serialize_snapshot(snap)

    def test_legacy_snapshot_without_metadata_is_accepted(self):
        snap = hotbox_runtime.make_snapshot(generation=1)
        for node in walk(snap['menus']):
            node.pop('direction', None)
            node.pop('presentation', None)
        hotbox_runtime.serialize_snapshot(snap)


if __name__ == '__main__':
    unittest.main()

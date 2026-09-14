# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent inventories from Maya 2026 MEL and resources/MayaStrings."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_catalog, tool_hotbox


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class ToolContentTest(unittest.TestCase):
    def setUp(self):
        self.nodes = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}

    def labels(self, identifier):
        return [n['label'] if n['kind'] != 'separator' else '|'
                for n in self.nodes[identifier]['children']]

    def test_native_lower_lists_in_exact_order(self):
        common = ['Selection Constraints', 'Transform Constraints', '|',
                  'Shift Extrude', 'Shift Duplicate', '|']
        expected = {
            'select': ['Automatic Camera-Based Selection'],
            'move': common + ['Preserve UVs', 'Preserve Children', 'Tweak Mode',
                              'Update Triad', '|', 'Move Options'],
            'rotate': common + ['Rotate Center', 'Free Rotate', 'Preserve UVs',
                                'Preserve Children', 'Tweak Mode', 'Relative', '|', 'Rotate Options'],
            'scale': common + ['Scale Center', 'Prevent Negative Scale', 'Preserve UVs',
                               'Preserve Children', 'Tweak Mode', '|', 'Scale Options'],
        }
        for tool, labels in expected.items():
            with self.subTest(tool=tool):
                self.assertEqual(self.labels('tools.' + tool + '_menu'), labels)
                self.assertEqual(self.labels('tools.' + tool + '.select_menu'),
                                 ['Automatic Camera-Based Selection'])

    def test_constraints_and_centers_are_complete(self):
        for tool in ('move', 'rotate', 'scale'):
            p = 'tools.' + tool + '_menu'
            self.assertEqual(self.labels(p + '.selection_constraints'),
                             ['Off', 'Angle', 'Border', 'Edge Loop', 'Edge Ring', 'Shell', 'UV Edge Loop'])
            self.assertEqual(self.labels(p + '.transform_constraints'),
                             ['Off', 'Edge Slide', 'Surface Slide', '|', 'Along Normals'])
        self.assertEqual(self.labels('tools.rotate_menu.center'), ['Default', 'Object', 'Manip', 'Selection'])
        self.assertEqual(self.labels('tools.scale_menu.center'), ['Default', 'Object', 'Manip'])

    def test_exact_labels_without_replacing_existing_direction_commands(self):
        expected = {
            'select': {'N': 'Symmetry', 'S': 'Select', 'NW': 'Marquee', 'W': 'Paint Select',
                       'SW': 'Lasso', 'SE': 'Clear Selection', 'NE': 'Drag', 'E': 'Camera-Based Selection'},
            'move': {'N': 'Symmetry', 'S': 'Select', 'W': 'World', 'NW': 'Object',
                     'NE': 'Component', 'SW': 'Axis', 'E': 'Snap', 'SE': 'Keep Spacing'},
            'rotate': {'N': 'Symmetry', 'S': 'Select', 'W': 'World', 'NW': 'Object',
                       'NE': 'Component', 'SW': 'Custom', 'E': 'Gimbal', 'SE': 'Discrete Rotate'},
            'scale': {'N': 'Symmetry', 'S': 'Select', 'W': 'World', 'NW': 'Object',
                      'NE': 'Component', 'SW': 'Axis', 'E': 'Snap Scale', 'SE': 'Relative'},
        }
        for tool, labels in expected.items():
            self.assertEqual({n['direction']: n['label'] for n in self.nodes['tools.' + tool]['children']}, labels)
            self.assertEqual({n['direction']: n['label']
                              for n in self.nodes['tools.' + tool + '.select']['children']},
                             {'N': 'Preselection Highlight', 'NE': 'Highlight Nearest Component',
                              'E': 'Highlight Backfaces', 'SE': 'Asset Centric', 'NW': 'Marquee',
                              'W': 'Camera-Based Selection', 'SW': 'Clear Selection', 'S': 'Soft Select'})
            self.assertEqual(self.labels('tools.' + tool + '.symmetry'),
                             ['Symmetry', 'World', 'Object', 'Topology', 'X Axis', 'Y Axis', 'Z Axis'])
            self.assertEqual(self.labels('tools.' + tool + '.select.soft'),
                             ['Object', 'Soft Select', 'Volume', 'Surface', 'Global', 'Color Feedback'])
        for tool in ('move', 'rotate', 'scale'):
            for name in ('world', 'object', 'normal'):
                self.assertEqual(self.nodes[f'tools.{tool}.{name}']['command'], f'orientation.{tool}.{name}')
        self.assertEqual(self.nodes['tools.select.drag']['kind'], 'disabled')
        self.assertEqual(self.nodes['tools.move.spacing']['kind'], 'disabled')
        self.assertEqual(self.nodes['tools.move.snap.relative']['direction'], 'S')
        for tool in ('move', 'rotate', 'scale'):
            self.assertEqual(self.nodes[f'common.modify.view_orientations.{tool}']['command'],
                             f'orientation.{tool}.view')

    def test_exact_companion_and_unavailable_state_contract(self):
        expected = {f'tools.{name}': f'tools.{name}_menu' for name in ('select', 'move', 'rotate', 'scale')}
        expected.update({f'tools.{name}.select': f'tools.{name}.select_menu'
                         for name in ('select', 'move', 'rotate', 'scale')})
        self.assertEqual(tool_hotbox.COMPANION_ROOTS, expected)
        for identifier in expected.values():
            self.assertEqual(self.nodes[identifier]['presentation'], 'list')
        actual = {n['id']: n['indicator'] for n in self.nodes.values()
                  if n['id'].startswith('tools.') and n.get('indicator')}
        self.assertEqual(actual, tool_hotbox.UNAVAILABLE_INDICATORS)
        self.assertTrue(actual)
        for identifier in actual:
            n = self.nodes[identifier]
            self.assertEqual((n['kind'], n['enabled'], n['command'], n['checked']),
                             ('disabled', False, '', False))
            self.assertIn('state not adapted', n['reason'])
        self.assertFalse(any(n['id'].endswith('.options') and n['children']
                             for n in self.nodes.values() if n['id'].startswith('tools.')))
        for tool in ('move', 'scale'):
            p = f'tools.{tool}.axis'
            self.assertEqual(self.labels(p), ['Normal', 'Parent', 'Along Rotation Axis', 'Live Object Axis', 'Custom'])
            self.assertNotIn(p + '.tool', self.nodes)
        for p in ('tools.move.axis.custom', 'tools.scale.axis.custom', 'tools.rotate.axis'):
            self.assertEqual(self.labels(p), ['Custom', 'Set to Component', 'Set To Point',
                                             'Set To Edge', 'Set To Face', 'Set To Object', 'Reset'])
            self.assertEqual(self.nodes[p + '.custom']['indicator'], 'checkbox')

    def test_controls_inventory_and_views_style_are_separate(self):
        self.assertEqual(self.labels('center.controls'),
                         ['Show Modeling', 'Show Rigging', 'Show Animation', 'Show FX',
                          'Show All', 'Hide All', 'Show Rendering', 'Show Common Menus',
                          'Show Pane Specific Menus', 'Show Custom Menu Set Menus',
                          'Set Transparency', 'Hotbox Style', '|', 'Window Options', '|',
                          'AxisMeld Center Mouse Buttons'])
        for domain in ('modeling', 'rigging', 'animation', 'fx', 'rendering'):
            title = 'FX' if domain == 'fx' else domain.title()
            self.assertEqual(self.labels('center.controls.' + domain),
                             [title + ' Only', 'Show/Hide ' + title])
        style = ['Zones and Menu Rows', 'Zones Only', 'Center Zone Only']
        self.assertEqual(self.labels('views.style'), style)
        self.assertEqual(self.labels('center.controls.style'), style + ['|', 'Center Zone RMB Popups'])
        self.assertEqual(self.labels('center.controls.window'), ['Show Main Menubar', 'Show Pane Menubars'])
        self.assertEqual(self.labels('center.controls.transparency'), ['0%', '25%', '50%', '75%', '100%'])
        self.assertEqual(self.nodes['views.side']['label'], 'Side View')
        self.assertNotIn('views.camera', self.nodes)
        actual = {n['id']: n['indicator'] for n in self.nodes.values()
                  if n['id'].startswith('center.controls.') and n.get('indicator')}
        self.assertEqual(actual, hotbox_catalog.CONTROL_UNAVAILABLE_INDICATORS)
        self.assertEqual(len(actual), 8)
        for identifier in actual:
            n = self.nodes[identifier]
            self.assertEqual((n['kind'], n['enabled'], n['command'], n['checked']),
                             ('disabled', False, '', False))


if __name__ == '__main__':
    unittest.main()

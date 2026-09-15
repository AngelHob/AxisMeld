# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya actions must not silently change geometry or data-sharing semantics."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))

from axismeld.hotbox_catalog import default_catalog
from axismeld.maya_menu_catalog import _binding
from axismeld.menubar_catalog import build_menubar
from axismeld.modeling_registry import SPECS


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))


class MayaSnapBindingTest(unittest.TestCase):
    def test_point_translation_rejects_even_a_single_component_snap_candidate(self):
        command, reason = _binding({'maya_command': 'SnapPointToPoint'}, 'common.modify',
                                   {'SnapPointToPoint': ['snap.selected_to_active']})
        self.assertEqual(command, '')
        self.assertTrue(reason)

    def test_native_capability_does_not_claim_maya_point_translation_identity(self):
        spec = SPECS['snap.selected_to_active']
        self.assertNotIn('SnapPointToPoint', spec.maya)
        self.assertEqual(spec.label, 'Selection to Active')
        self.assertEqual(spec.calls[0].operator, 'view3d.snap_selected_to_active')

    def test_duplicate_special_does_not_force_linked_data(self):
        command, reason = _binding({'maya_command': 'DuplicateSpecial'}, 'common.edit',
                                   {'DuplicateSpecial': ['edit.duplicate_linked']})
        self.assertEqual(command, '')
        self.assertTrue(reason)
        self.assertNotIn('DuplicateSpecial', SPECS['edit.duplicate_linked'].maya)
        for roots in (default_catalog(), build_menubar()['menus']):
            nodes = list(walk(roots))
            row = next(node for node in nodes if node['label'] == 'Duplicate Special')
            self.assertEqual(row['kind'], 'disabled')
            self.assertFalse(row.get('command'))
            self.assertTrue(row['reason'])
            for option in row['children']:
                self.assertEqual(option['kind'], 'disabled')
                self.assertFalse(option.get('command'))
            native = [node for node in nodes if node.get('command') == 'edit.duplicate_linked']
            self.assertTrue(native)
            self.assertTrue(all(node['label'] == 'Duplicate Linked' for node in native))

    def test_both_surfaces_preserve_placeholder_and_independent_native_action(self):
        for name, roots in (('hotbox', default_catalog()),
                            ('menubar', build_menubar()['menus'])):
            nodes = list(walk(roots))
            with self.subTest(surface=name):
                row = next(node for node in nodes if node['label'] == 'Point to Point')
                self.assertEqual(row['label'], 'Point to Point')
                self.assertEqual(row['kind'], 'disabled')
                self.assertFalse(row.get('command'))
                self.assertTrue(row['reason'])
                for option in row['children']:
                    self.assertEqual(option['kind'], 'disabled')
                    self.assertFalse(option.get('command'))
                native = [node for node in nodes
                          if node.get('command') == 'snap.selected_to_active']
                self.assertTrue(native)
                self.assertTrue(all(node['label'] == 'Selection to Active' for node in native))
                self.assertTrue(all(node['kind'] == 'command' for node in native))


if __name__ == '__main__':
    unittest.main()

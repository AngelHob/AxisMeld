# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Full catalog boundary and actual tool-state regressions."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_catalog, hotbox_runtime


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class ContentRuntimeTest(unittest.TestCase):
    def test_all_companions_survive_complete_bounded_snapshot(self):
        snap = hotbox_runtime.make_snapshot(generation=1)
        self.assertEqual(len(snap['menus']), 20)
        self.assertLessEqual(len(list(walk(snap['menus']))), 4096)
        self.assertLessEqual(len(hotbox_runtime.serialize_snapshot(snap).encode()), 1024 * 1024)
        for change in ('unknown', 'duplicate', 'reorder', 'missing'):
            bad = deepcopy(snap)
            if change == 'unknown':
                bad['menus'][-1]['id'] = 'untrusted.root'
            elif change == 'duplicate':
                bad['menus'].append(deepcopy(bad['menus'][-1]))
            elif change == 'reorder':
                bad['menus'][-1], bad['menus'][-2] = bad['menus'][-2], bad['menus'][-1]
            else:
                bad['menus'].pop(0)
            with self.subTest(change=change), self.assertRaises(ValueError):
                hotbox_runtime.serialize_snapshot(bad)

    def test_disabled_states_have_exact_ids_styles_and_false_values(self):
        snap = hotbox_runtime.make_snapshot(generation=1)
        nodes = {n['id']: n for n in walk(snap['menus'])}
        checkbox = nodes['tools.select.drag']
        radio = nodes['tools.move_menu.selection_constraints.off']
        self.assertEqual((checkbox['indicator'], checkbox['checked']), ('checkbox', False))
        self.assertEqual((radio['indicator'], radio['checked']), ('radio', False))
        self.assertTrue(nodes['context.create_menu.exit_on_completion']['checked'])
        for identifier, change in ((checkbox['id'], 'checked'), (radio['id'], 'style'),
                                   (checkbox['id'], 'id')):
            bad = deepcopy(snap)
            node = next(n for n in walk(bad['menus']) if n['id'] == identifier)
            if change == 'checked':
                node['checked'] = True
            elif change == 'style':
                node['indicator'] = 'checkbox'
            else:
                node['id'] = 'tools.select.unregistered_state'
            with self.subTest(change=change), self.assertRaises(ValueError):
                hotbox_runtime.serialize_snapshot(bad)

    def test_live_orientation_inheritance_and_marquee_checkbox(self):
        source = {n['id']: n for n in walk(hotbox_catalog.default_catalog())}
        ids = ('tools.move.world', 'tools.move.object', 'tools.select.marquee',
               'tools.move.select.marquee')
        context = NS(scene=NS(transform_orientation_slots=[NS(type='LOCAL', use=True),
                         NS(type='GLOBAL', use=False)]), mode='OBJECT',
                     workspace=NS(tools=NS(from_space_view3d_mode=lambda mode, create=False:
                                          NS(idname='builtin.select_box'))))
        adapter = NS(available=lambda *_: (True, ''))
        with patch.dict(sys.modules, {'axismeld.adapter': adapter}):
            nodes = hotbox_runtime._apply_runtime_capabilities(context, [deepcopy(source[i]) for i in ids])
        self.assertEqual([(n.get('indicator'), n.get('checked')) for n in nodes],
                         [('checkbox', False), ('checkbox', True),
                          ('checkbox', True), ('checkbox', True)])
        context.scene.transform_orientation_slots[1].use = True
        with patch.dict(sys.modules, {'axismeld.adapter': adapter}):
            nodes = hotbox_runtime._apply_runtime_capabilities(context, [deepcopy(source[i]) for i in ids[:2]])
        self.assertEqual([n['checked'] for n in nodes], [True, False])


if __name__ == '__main__':
    unittest.main()

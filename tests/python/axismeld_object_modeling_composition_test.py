# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya companion directory and independent option-cell contracts."""
from copy import deepcopy
from pathlib import Path
import sys
import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
from axismeld import hotbox_catalog, hotbox_runtime


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class CompositionTest(unittest.TestCase):
    def test_retopologize_and_options_are_honest_disabled_pinned_confirmation_gap(self):
        from axismeld.object_modeling_hotbox import OBJECT_MENU_COMMANDS, OBJECT_OPTION_COMMANDS
        row = next(n for n in walk(hotbox_catalog.default_catalog())
                   if n['id'] == 'context.modeling_object_menu.retopologize')
        for node in (row, row['children'][0]):
            self.assertEqual(node['kind'], 'disabled')
            self.assertFalse(node['enabled'])
            self.assertEqual(node['command'], '')
            self.assertIn('Target-pinned QuadriFlow confirmation not implemented', node['reason'])
            self.assertIn('native entry remains in Mesh menu', node['reason'])
            self.assertNotIn(node['id'], OBJECT_MENU_COMMANDS)
            self.assertNotIn(node['id'], OBJECT_OPTION_COMMANDS)
        native = [n for n in walk(hotbox_catalog.default_catalog()) if n['command'] == 'mesh.quad_remesh']
        self.assertTrue(native)
        self.assertTrue(all(not n['id'].startswith('context.modeling_object_menu.') for n in native))
    def test_snapshot_budget_with_runtime_disabled_reasons(self):
        value = hotbox_runtime.make_snapshot(generation=1)
        self.assertLess(len(hotbox_runtime.serialize_snapshot(value).encode('utf-8')), hotbox_runtime.MAX_JSON_BYTES)
        import axismeld
        recent = hotbox_runtime.RecentCommands()
        from axismeld.modeling_common import SETTINGS
        indicator_ids = set(SETTINGS) | {
            'display.xray', 'display.vertex_normals', 'display.split_normals', 'display.face_normals',
            'display.edge_length', 'display.edge_angle', 'display.face_area', 'display.face_angle',
            'display.crease_marks', 'display.sharp_edges', 'display.face_centers',
            'display.component_indices', 'color.display_active', 'display.modeling_toolbar',
            'display.distortion_analysis'}
        def command_state(context, command):
            return ('checkbox', False) if command in indicator_ids or command.startswith('tool.mesh_') else None
        def entry_size(command):
            entry = {'id': 'center.recent.9.' + command.replace('.', '_'), 'kind': 'command',
                     'label': hotbox_runtime.COMMANDS[command].label, 'command': command,
                     'enabled': False, 'reason': '', 'children': []}
            if command_state(None, command):
                entry.update(indicator='checkbox', checked=False)
            return len(json.dumps(entry, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        candidates = sorted((command for command in hotbox_runtime.SUPPORTED_COMMANDS
                             if hotbox_catalog.command_policy(command)[1]), key=entry_size, reverse=True)
        for command in candidates[:10]:
            recent.record(command)
        self.assertEqual(len(recent.items()), 10)
        # Runtime state now reads real tool orientation and Marquee state, while
        # component companion availability must observe an explicit Object context.
        context = NS(area=NS(type='VIEW_3D'), region=NS(type='WINDOW'), mode='OBJECT',
                     active_object=None,
                     scene=NS(is_editable=True, transform_orientation_slots=[
                         NS(use=False, type='GLOBAL') for _ in range(4)]),
                     workspace=NS(tools=NS(from_space_view3d_mode=lambda *args, **kw: None)))
        for reason in hotbox_runtime._CAPABILITY_REASONS:
            adapter = NS(available=lambda *args: (False, reason),
                         modeling_adapter=NS(available=lambda *args, **kw: (False, reason),
                                             command_state=command_state))
            with patch.object(axismeld, 'adapter', adapter, create=True), patch.object(hotbox_runtime, 'recent', recent), \
                 patch.object(hotbox_runtime, 'object_modeling_targets', return_value=()):
                menus = hotbox_runtime._catalog_with_recent()
                gaps = {n['id']: n['reason'] for n in walk(menus) if n['kind'] == 'disabled'}
                hotbox_runtime._apply_runtime_capabilities(context, menus)
                self.assertEqual({n['id']: n['reason'] for n in walk(menus) if n['kind'] == 'disabled'}, gaps)
                snapshot = hotbox_runtime.make_snapshot(generation=1, menus=menus)
                payload = hotbox_runtime.serialize_snapshot(snapshot)
                self.assertLess(len(payload.encode('utf-8')), hotbox_runtime.MAX_JSON_BYTES, reason)

    def test_unknown_capability_error_is_preserved_exactly(self):
        import axismeld
        reason = 'Specific plugin failure: preserve this full diagnostic exactly'
        adapter = NS(available=lambda *args: (False, reason))
        node = hotbox_catalog._node('probe', 'command', 'Probe', command='tool.select')
        with patch.object(axismeld, 'adapter', adapter, create=True):
            hotbox_runtime._apply_runtime_capabilities(NS(), [node])
        self.assertEqual(node['reason'], reason)

    def companion(self):
        matches = [n for n in walk(hotbox_catalog.default_catalog()) if n['id'] == 'context.modeling_object_menu']
        self.assertEqual(len(matches), 1, 'Missing simultaneous Object companion directory')
        return matches[0]

    def test_exact_maya_main_order_and_separators(self):
        companion = self.companion()
        self.assertEqual(companion['presentation'], 'list')
        self.assertEqual([n['label'] for n in companion['children'] if n['kind'] != 'separator'], [
            'Offset Edge Loop Tool', 'Smooth', 'Unsmooth', 'Subdiv Proxy', 'Crease Tool',
            'Project Curve on mesh', 'Split mesh with projected curve', 'Mirror', 'Mapping',
            'Triangulate', 'Quadrangulate', 'Reduce', 'Remesh', 'Retopologize',
            'Transfer Vertex Order', 'Separate', 'Combine', 'Booleans', 'Cleanup...',
            'Connect Tool', 'Quad Draw Tool', 'Polygon Display'])
        before = []
        last = None
        for row in companion['children']:
            if row['kind'] == 'separator':
                before.append(last)
            else:
                last = row['label']
        self.assertEqual(before, ['Crease Tool', 'Split mesh with projected curve', 'Mapping',
                                  'Retopologize', 'Transfer Vertex Order', 'Booleans', 'Quad Draw Tool'])
        # MayaStrings + contextPolyToolsObjectMM.mel:442 preserve punctuation.
        difference = next(n for n in walk([companion]) if n['id'].endswith('.booleans.difference'))
        self.assertEqual(difference['label'], 'Difference (A - B)')

    def test_options_are_independent_strict_leaves(self):
        companion = self.companion()
        rows = {n['id'].rsplit('.', 1)[-1]: n for n in companion['children']}
        for name in ('smooth', 'mirror', 'reduce', 'remesh'):
            row = rows[name]
            self.assertEqual(row['command'], 'object.modeling_' + name)
            self.assertEqual(len(row['children']), 1)
            option = row['children'][0]
            self.assertEqual(option['id'], row['id'] + '.options')
            self.assertEqual(option['command'], row['command'] + '_options')
        value = hotbox_runtime.make_snapshot(generation=1)
        hotbox_runtime.validate_snapshot(value)
        smooth = next(n for n in walk(value['menus']) if n['id'].endswith('object_menu.smooth'))
        smooth.update(kind='disabled', enabled=False, command='', reason='Main unavailable; options still available')
        hotbox_runtime.validate_snapshot(value)
        self.assertTrue(smooth['children'][0]['enabled'])
        for change in ({'id': 'bad.options'}, {'kind': 'menu'}, {'direction': 'N'}, {'presentation': 'list'},
                       {'children': [deepcopy(smooth['children'][0])]}):
            invalid = deepcopy(value)
            row = next(n for n in walk(invalid['menus']) if n['id'].endswith('object_menu.smooth'))
            row['children'][0].update(change)
            with self.assertRaises(ValueError):
                hotbox_runtime.validate_snapshot(invalid)


class ModifierActionTest(unittest.TestCase):
    def setUp(self):
        from axismeld_object_modeling_hotbox_test import ObjectToolTransactionTest
        fixture = ObjectToolTransactionTest()
        fixture.setUp()
        self.fixture = fixture
        self.context = context = fixture.ctx
        context.scene.session_uid = 100
        context.view_layer.as_pointer = lambda: 200
        context.view_layer.update = lambda: None
        context.window = NS(as_pointer=lambda: 300)
        context.area.as_pointer = lambda: 400
        context.region.as_pointer = lambda: 500
        self.dialogs = []
        context.window_manager = NS(invoke_props_dialog=lambda op: self.dialogs.append(op) or {'RUNNING_MODAL'})
        class Modifiers(list):
            def new(self, name, kind):
                item = NS(name=name, type=kind)
                self.append(item)
                return item
        for obj in fixture.objects:
            obj.modifiers = Modifiers()
            obj.name = 'Mesh' + str(obj.session_uid)
        self.action = fixture.module.AXISMELD_OT_object_modeling_action()
        self.action.command = 'object.modeling_smooth_options'
        self.action.target_uid = ''
        self.action.smooth_levels = 2
        self.action.mirror_axis = 'Y'
        self.action.mirror_bisect = False
        self.action.mirror_merge = True
        self.action.reduce_ratio = .25
        self.action.remesh_voxel_size = .2
        self.action.reports = []
        self.fail_evaluation = False
        def evaluate(context, target):
            if self.fail_evaluation:
                raise RuntimeError('Injected modifier evaluation failure')
        self.patch = patch.dict(sys.modules, {'axismeld.modeling_mesh_ops': NS(_evaluated_mesh=evaluate)})
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def state(self):
        return (self.context.mode, self.fixture.objects.active.session_uid,
                tuple(obj.selected for obj in self.fixture.objects),
                tuple(tuple(mod.__dict__.items()) for obj in self.fixture.objects for mod in obj.modifiers),
                tuple(self.context.tool_settings.mesh_select_mode))

    def preselection(self):
        self.fixture.a.selected = self.fixture.b.selected = False
        self.fixture.objects.active = self.fixture.b
        self.action.target_uid = '1'

    def test_options_invoke_is_read_only_and_confirmation_commits_preselection(self):
        self.preselection()
        before = self.state()
        self.assertEqual(self.action.invoke(self.context, None), {'RUNNING_MODAL'})
        self.assertEqual(self.state(), before)
        self.assertEqual(self.fixture.calls, [])
        # Until execute is called, dismissing the dialog has no mutation to roll back.
        self.assertEqual(self.action.execute(self.context), {'FINISHED'})
        self.assertTrue(self.fixture.a.selected)
        self.assertFalse(self.fixture.b.selected)
        self.assertIs(self.fixture.objects.active, self.fixture.a)
        self.assertEqual(self.fixture.a.modifiers[0].levels, 2)
        self.assertEqual(self.context.mode, 'OBJECT')
        self.assertIn('UNDO', self.action.bl_options)

    def test_all_four_actions_affect_only_active_and_preserve_shared_data_selection(self):
        for suffix, kind, field, expected in (('smooth', 'SUBSURF', 'levels', 2),
                                             ('mirror', 'MIRROR', 'use_axis', (False, True, False)),
                                             ('reduce', 'DECIMATE', 'ratio', .25),
                                             ('remesh', 'REMESH', 'voxel_size', .2)):
            self.action.command = 'object.modeling_' + suffix
            self.assertEqual(self.action.execute(self.context), {'FINISHED'})
            modifier = self.fixture.a.modifiers[-1]
            self.assertEqual(modifier.type, kind)
            self.assertEqual(getattr(modifier, field), expected)
            self.assertTrue(self.fixture.a.selected and self.fixture.b.selected)
            self.assertFalse(self.fixture.b.modifiers)
            self.assertIs(self.fixture.a.data, self.fixture.b.data)

    def test_option_source_selection_and_data_identity_changes_cancel_without_commit(self):
        for change in ('source', 'selection', 'data', 'active'):
            with self.subTest(change=change):
                self.preselection()
                self.assertEqual(self.action.invoke(self.context, None), {'RUNNING_MODAL'})
                if change == 'source':
                    self.context.scene.session_uid += 1
                elif change == 'selection':
                    self.fixture.b.selected = True
                elif change == 'data':
                    self.fixture.a.data.session_uid += 1
                else:
                    self.fixture.objects.active = self.fixture.a
                before = self.state()
                self.assertEqual(self.action.execute(self.context), {'CANCELLED'})
                self.assertEqual(self.state(), before)
                self.assertFalse(self.fixture.a.modifiers)

    def test_modifier_failure_removes_partial_modifier_and_restores_preselection(self):
        self.preselection()
        before = self.state()
        self.assertEqual(self.action.invoke(self.context, None), {'RUNNING_MODAL'})
        self.fail_evaluation = True
        self.assertEqual(self.action.execute(self.context), {'CANCELLED'})
        self.assertEqual(self.state(), before)
        self.assertFalse(self.fixture.a.modifiers)
        self.assertIn('original state restored', self.action.reports[-1][1])


if __name__ == '__main__':
    unittest.main()

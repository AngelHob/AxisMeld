# SPDX-License-Identifier: GPL-2.0-or-later
"""Object context menu and read-only complete selection contracts."""
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
from axismeld import hotbox_catalog
from axismeld import hotbox_runtime
from axismeld.commands import baseline_bindings
from axismeld.keymap import generate_keymaps
from axismeld.object_modeling_hotbox import OBJECT_TOOLS, OBJECT_BOUND_COMMANDS
from axismeld.profiles import resolve_profiles


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


class ObjectModelingTest(unittest.TestCase):
    def test_object_tool_bindings_are_unbound_by_default_and_object_scoped_when_remapped(self):
        for command in OBJECT_BOUND_COMMANDS:
            self.assertNotIn(command, baseline_bindings())
            for key in ('F13', 'F14'):
                resolved = resolve_profiles([('user', {'schema_version': 1, 'bindings': {command: {'type': key}}})])
                self.assertFalse(resolved.diagnostics)
                native = ('native.action', {'type': key, 'value': 'PRESS'}, None)
                base = [(name, {}, {'items': [native]}) for name in ('Object Mode', 'Mesh', '3D View')]
                generated = generate_keymaps(base, resolved.bindings)
                for name, _, content in generated:
                    items = [item for item in content['items'] if item[0] == 'axismeld.command' and
                             item[2] and ('command', command) in item[2].get('properties', ())]
                    if name == 'Object Mode':
                        self.assertEqual(len(items), 1)
                        self.assertEqual(items[0][1]['type'], key)
                        self.assertNotIn(native, content['items'])
                    elif name in ('Mesh', '3D View'):
                        self.assertFalse(items, name)
                        self.assertIn(native, content['items'], name)
                self.assertEqual(generate_keymaps(generated, resolved.bindings), generated)

    def test_object_tool_old_generated_bindings_migrate_by_id_for_remap_and_disable(self):
        for command in OBJECT_BOUND_COMMANDS:
            for event in ({'type': 'F14'}, None):
                resolved = resolve_profiles([('user', {'schema_version': 1, 'bindings': {command: event}})])
                self.assertFalse(resolved.diagnostics)
                legacy = ('axismeld.command', {'type': 'F13', 'value': 'PRESS'},
                          {'properties': [('command', command)]})
                native13 = ('native.f13', {'type': 'F13', 'value': 'PRESS'}, None)
                native14 = ('native.f14', {'type': 'F14', 'value': 'PRESS'}, None)
                base = [(name, {}, {'items': [legacy, native13, native14]})
                        for name in ('Object Mode', 'Mesh', '3D View')]
                generated = generate_keymaps(base, resolved.bindings)
                for name, _, content in generated:
                    self.assertNotIn(legacy, content['items'], name)
                    if name in ('Object Mode', 'Mesh', '3D View'):
                        self.assertIn(native13, content['items'], name)
                        if name != 'Object Mode' or event is None:
                            self.assertIn(native14, content['items'], name)
                    matches = [item for item in content['items'] if item[0] == 'axismeld.command' and
                               item[2] and ('command', command) in item[2].get('properties', ())]
                    self.assertEqual(len(matches), int(name == 'Object Mode' and event is not None), name)
                self.assertEqual(generate_keymaps(generated, resolved.bindings), generated)

    def test_space_dispatch_uses_adapter_without_recording_tool_start(self):
        calls = []
        adapter = NS(available=lambda context, command: (True, ''),
                     run=lambda context, command, **kwargs: calls.append(command) or {'FINISHED'})
        context = NS(window_manager=NS(keyconfigs=NS(active=NS(name='AxisMeld_Maya_2026'))))
        import axismeld
        before = hotbox_runtime.recent.items()
        with patch.object(axismeld, 'adapter', adapter, create=True):
            self.assertEqual(hotbox_runtime.dispatch(context, 'tool.object_mesh_knife'), {'FINISHED'})
        self.assertEqual(calls, ['tool.object_mesh_knife'])
        self.assertEqual(hotbox_runtime.recent.items(), before)

    def test_fixed_object_root(self):
        roots = [n for n in walk(hotbox_catalog.default_catalog()) if n['id'] == 'context.modeling_object']
        self.assertEqual(len(roots), 1, 'Object modeling root is missing')
        root = roots[0]
        self.assertEqual(root['presentation'], 'radial')
        self.assertEqual({n['direction']: n['command'] for n in root['children'] if n['kind'] == 'command'}, {
            'E': 'tool.object_mesh_poly_build', 'SW': 'tool.object_mesh_loopcut', 'W': 'tool.object_mesh_knife'})
        gaps = [n for n in root['children'] if n['kind'] == 'disabled']
        self.assertEqual({n['direction'] for n in gaps}, {'N', 'NE', 'SE', 'S', 'NW'})
        self.assertTrue(all(not n.get('command') and not n['enabled'] and 'M2d-' in n['reason'] for n in gaps))

    def test_generated_context_targets(self):
        maps = generate_keymaps([(n, {}, {'items': []}) for n in ('Object Mode', 'Mesh')], baseline_bindings())
        owners = {name: {dict(item[2]['properties'])['command'] for item in data['items']}
                  for name, _, data in maps if name in ('Object Mode', 'Mesh')}
        self.assertIn('context.modeling_hotbox', owners['Object Mode'])
        self.assertIn('context.modeling_hotbox', owners['Mesh'])
        self.assertIn('context.create_hotbox', owners['Object Mode'])
        self.assertNotIn('context.create_hotbox', owners['Mesh'])

    def test_strict_read_only_targets(self):
        module = importlib.import_module('axismeld.object_modeling_hotbox')
        def obj(uid, selected=True, **changes):
            result = NS(session_uid=uid, type='MESH', mode='OBJECT', is_editable=True,
                        override_library=None, hide_select=False,
                        data=NS(session_uid=uid + 10, is_editable=True, override_library=None),
                        select_get=lambda **kw: selected, visible_get=lambda **kw: True)
            result.__dict__.update(changes)
            return result
        a, b = obj(1), obj(2)
        ctx = NS(mode='OBJECT', scene=NS(is_editable=True), area=NS(type='VIEW_3D'),
                 region=NS(type='WINDOW'), view_layer=NS(objects=[a, b]), active_object=a,
                 selectable_objects=[a, b], space_data=NS(type='VIEW_3D'))
        self.assertEqual(module.object_modeling_targets(ctx), (a, b))
        self.assertEqual(module.object_modeling_targets(ctx, '1'), ())
        for changes in ({'type': 'CURVE'}, {'hide_select': True}, {'is_editable': False},
                        {'override_library': object()}, {'visible_get': lambda **kw: False}):
            old = dict(b.__dict__)
            b.__dict__.update(changes)
            self.assertEqual(module.object_modeling_targets(ctx), ())
            b.__dict__.clear()
            b.__dict__.update(old)
        ctx.active_object = None
        self.assertEqual(module.object_modeling_targets(ctx), ())
        a, b = obj(1, False), obj(2, False)
        ctx.view_layer.objects = [a, b]
        ctx.selectable_objects = [a, b]
        self.assertEqual(module.object_modeling_targets(ctx), ())
        self.assertEqual(module.object_modeling_targets(ctx, '2'), (b,))
        for uid in ('0', '-1', '4294967296', 'missing'):
            self.assertEqual(module.object_modeling_targets(ctx, uid), ())
        self.assertFalse(a.select_get())
        self.assertFalse(b.select_get())
        ctx.selectable_objects = [a]
        self.assertEqual(module.object_modeling_targets(ctx, '2'), ())


class ObjectToolTransactionTest(unittest.TestCase):
    def setUp(self):
        class Objects(list):
            active = None
        class Obj:
            type = 'MESH'
            mode = 'OBJECT'
            is_editable = True
            override_library = None
            hide_select = False
            def __init__(self, uid, mesh, selected):
                self.session_uid, self.data, self.selected = uid, mesh, selected
            def select_get(self, **kw):
                return self.selected
            def select_set(self, value, **kw):
                self.selected = value
            def visible_get(self, **kw):
                return True
        mesh = NS(session_uid=10, is_editable=True, override_library=None,
                  vertices=[NS(select=False, hide=True)], edges=[NS(select=True, hide=False)],
                  polygons=[NS(select=False, hide=False)], update=lambda: None)
        self.a, self.b = Obj(1, mesh, True), Obj(2, mesh, True)
        self.objects = Objects([self.a, self.b])
        self.objects.active = self.a
        self.tool_ids = {'OBJECT': 'builtin.move', 'EDIT_MESH': 'builtin.select_circle'}
        self.ctx = NS(mode='OBJECT', area=NS(type='VIEW_3D'), region=NS(type='WINDOW'),
                      scene=NS(is_editable=True), view_layer=NS(objects=self.objects),
                      selectable_objects=self.objects, space_data=NS(type='VIEW_3D'),
                      tool_settings=NS(mesh_select_mode=(False, True, False)),
                      objects_in_mode=[], active_object=self.a,
                      workspace=NS(tools=NS(from_space_view3d_mode=lambda mode, **kw:
                          NS(idname=self.tool_ids[mode]) if mode in self.tool_ids else None)))
        self.calls = []
        self.fail_tool = False
        self.raise_tool = False
        self.fail_mode = False
        self.fail_restore = ''
        def mode_set(*args, mode):
            self.calls.append(('mode', args, mode))
            self.ctx.mode = 'EDIT_MESH' if mode == 'EDIT' else 'OBJECT'
            self.a.mode = mode
            self.ctx.active_object = self.objects.active
            self.ctx.objects_in_mode = [self.a] if mode == 'EDIT' else []
            self.tool_ids.setdefault(self.ctx.mode, 'builtin.select_box')
            if mode == 'EDIT':
                mesh.vertices[0].select = True
                self.ctx.tool_settings.mesh_select_mode = (True, False, False)
                if self.fail_mode:
                    return {'CANCELLED'}
            return {'FINISHED'}
        def tool_set(*args, name):
            self.calls.append(('tool', args, name))
            if self.fail_restore and self.ctx.mode == 'EDIT_MESH' and name == 'builtin.select_circle':
                if self.fail_restore == 'exception':
                    raise RuntimeError('Injected Edit tool restore exception')
                return {'CANCELLED'}
            self.tool_ids[self.ctx.mode] = name
            if self.raise_tool and name == 'builtin.knife':
                raise RuntimeError('Injected tool exception')
            if self.fail_tool and name == 'builtin.knife':
                return {'CANCELLED'}
            return {'FINISHED'}
        class Operator:
            def report(self, level, message):
                self.reports.append((level, message))
        fake_bpy = NS(ops=NS(object=NS(mode_set=mode_set), wm=NS(tool_set_by_id=tool_set)))
        spec = importlib.util.spec_from_file_location('axismeld._object_transaction_test',
            Path(__file__).resolve().parents[2] / 'scripts/modules/axismeld/object_modeling_ops.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'bpy': fake_bpy, 'bpy.props': NS(**{name: lambda **kw: None for name in
                                      ('StringProperty', 'IntProperty', 'FloatProperty', 'BoolProperty', 'EnumProperty')}),
                                     'bpy.types': NS(Operator=Operator)}):
            spec.loader.exec_module(module)
        self.op = module.AXISMELD_OT_object_modeling_tool()
        self.module = module
        self.op.command = 'tool.object_mesh_knife'
        self.op.target_uid = ''
        self.op.reports = []

    def test_shared_mesh_enters_native_representative_with_child_undo_suppressed(self):
        self.assertEqual(self.op.execute(self.ctx), {'FINISHED'})
        self.assertEqual(self.ctx.mode, 'EDIT_MESH')
        self.assertTrue(self.a.selected and self.b.selected)
        self.assertEqual(self.tool_ids['EDIT_MESH'], 'builtin.knife')
        self.assertTrue(all(args == ('EXEC_DEFAULT', False) for _, args, _ in self.calls))

    def test_failure_restores_selection_components_domains_and_both_tools(self):
        for failure in ('fail_tool', 'fail_mode', 'raise_tool'):
            with self.subTest(failure=failure):
                self.setUp()
                self.a.selected = self.b.selected = False
                self.op.target_uid = '1'
                setattr(self, failure, True)
                self.assertEqual(self.op.execute(self.ctx), {'CANCELLED'})
                self.assertEqual(self.ctx.mode, 'OBJECT')
                self.assertFalse(self.a.selected or self.b.selected)
                self.assertIs(self.objects.active, self.a)
                self.assertEqual(self.ctx.tool_settings.mesh_select_mode, (False, True, False))
                self.assertFalse(self.a.data.vertices[0].select)
                self.assertTrue(self.a.data.vertices[0].hide)
                self.assertEqual(self.tool_ids, {'OBJECT': 'builtin.move', 'EDIT_MESH': 'builtin.select_circle'})
                self.assertTrue(self.op.reports)
                self.assertNotIn('rollback incomplete', self.op.reports[-1][1])

    def test_invalid_action_and_stale_target_are_mutation_free(self):
        for command, uid in (('mesh.extrude_region', ''), ('tool.object_mesh_knife', '999'),
                             ('tool.object_mesh_knife', '1')):
            self.op.command, self.op.target_uid = command, uid
            self.assertEqual(self.op.execute(self.ctx), {'CANCELLED'})
            self.assertEqual(self.calls, [])

    def test_edit_tool_restore_failure_reports_incomplete_and_continues_other_rollback(self):
        for failure in ('cancelled', 'exception'):
            with self.subTest(failure=failure):
                self.setUp()
                self.a.selected = self.b.selected = False
                self.objects.active = self.b
                self.ctx.active_object = self.b
                self.op.target_uid = '1'
                self.fail_tool = True
                self.fail_restore = failure
                components = tuple(tuple((e.select, e.hide) for e in elements) for elements in
                                   (self.a.data.vertices, self.a.data.edges, self.a.data.polygons))
                self.assertEqual(self.op.execute(self.ctx), {'CANCELLED'})
                self.assertEqual(self.ctx.mode, 'OBJECT')
                self.assertFalse(self.a.selected or self.b.selected)
                self.assertIs(self.objects.active, self.b)
                self.assertEqual(self.ctx.tool_settings.mesh_select_mode, (False, True, False))
                self.assertEqual(tuple(tuple((e.select, e.hide) for e in elements) for elements in
                                       (self.a.data.vertices, self.a.data.edges, self.a.data.polygons)), components)
                self.assertEqual(self.tool_ids['OBJECT'], 'builtin.move')
                self.assertEqual(self.tool_ids['EDIT_MESH'], 'builtin.knife')
                self.assertEqual(self.op.reports[-1][0], {'ERROR'})
                self.assertIn('rollback incomplete', self.op.reports[-1][1])
                self.assertIn(('tool', ('EXEC_DEFAULT', False), 'builtin.select_circle'), self.calls)
                self.assertIn(('mode', ('EXEC_DEFAULT', False), 'OBJECT'), self.calls)

    def test_absent_edit_slot_restores_native_initial_default_after_failure(self):
        del self.tool_ids['EDIT_MESH']
        self.a.selected = self.b.selected = False
        self.op.target_uid = '1'
        self.fail_tool = True
        self.assertIsNone(self.ctx.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False))
        self.assertEqual(self.op.execute(self.ctx), {'CANCELLED'})
        self.assertEqual(self.ctx.mode, 'OBJECT')
        self.assertFalse(self.a.selected or self.b.selected)
        self.assertIs(self.objects.active, self.a)
        self.assertEqual(self.tool_ids, {'OBJECT': 'builtin.move', 'EDIT_MESH': 'builtin.select_box'})
        self.assertEqual(self.ctx.tool_settings.mesh_select_mode, (False, True, False))
        self.assertFalse(self.a.data.vertices[0].select)
        self.assertTrue(self.a.data.vertices[0].hide)
        self.assertIn(('tool', ('EXEC_DEFAULT', False), 'builtin.select_box'), self.calls)
        self.assertNotIn('rollback incomplete', self.op.reports[-1][1])


if __name__ == '__main__':
    unittest.main()

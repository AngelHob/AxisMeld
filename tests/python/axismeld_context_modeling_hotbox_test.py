# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""M2d fixed menu, read-only selection and mutually exclusive input contracts."""
import ast
import importlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/modules'))
from axismeld import hotbox_catalog, hotbox_runtime
from axismeld.commands import COMMANDS, baseline_bindings
from axismeld.keymap import generate_keymaps, validate_global_bindings
from axismeld.profiles import resolve_profiles

CREATE = 'context.create_hotbox'
MODEL = 'context.modeling_hotbox'
COMPONENT = 'context.component_hotbox'
ROOTS = tuple('context.modeling_' + domain for domain in ('vertex', 'edge', 'face'))


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node['children'])


def layer(bindings):
    return ('user', {'schema_version': 1, 'bindings': bindings})


def items_for(maps, name, command):
    return [item for map_name, _args, content in maps if map_name == name
            for item in content['items'] if item[0] == 'axismeld.command' and item[2]
            and ('command', command) in item[2]['properties']]


class ModelingInputTest(unittest.TestCase):
    def test_actual_industry_keymap_retains_cursor_press_and_drag(self):
        spec = importlib.util.spec_from_file_location('industry_base', REPO /
            'scripts/presets/keyconfig/keymap_data/industry_compatible_data.py')
        industry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(industry)
        def execfile(path):
            module_spec = importlib.util.spec_from_file_location('blender_base', path)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            return module
        with patch.dict(sys.modules, {'bpy.utils': NS(execfile=execfile)}):
            base = industry.generate_keymaps(industry.Params())
        validate_global_bindings(base, baseline_bindings())
        current = generate_keymaps(base, baseline_bindings())
        for operator in ('view3d.cursor3d', 'transform.translate'):
            before = [item for name, _, content in base if name == '3D View'
                      for item in content['items'] if item[0] == operator and
                      item[1].get('type') == 'RIGHTMOUSE' and item[1].get('shift')]
            self.assertTrue(before, operator)
            after = next(content['items'] for name, _, content in current if name == '3D View')
            self.assertTrue(all(item in after for item in before))

    def test_default_pair_is_valid_and_context_targets_preserve_create_scope(self):
        defaults = baseline_bindings()
        self.assertIn(MODEL, defaults)
        self.assertEqual(defaults[CREATE], defaults[MODEL])
        self.assertFalse(resolve_profiles([layer({})]).diagnostics)
        maps = generate_keymaps([(name, {}, {'items': []}) for name in ('Mesh', 'Object Mode')], defaults)
        for name, expected in (('Mesh', MODEL), ('Object Mode', CREATE)):
            self.assertEqual(len(items_for(maps, name, expected)), 1)
        self.assertEqual(len(items_for(maps, 'Object Mode', MODEL)), 1)
        self.assertFalse(items_for(maps, 'Mesh', CREATE))

    def test_pair_rebinds_disable_and_invalid_layers_are_atomic(self):
        for event in ({'type': 'F13'}, {'type': 'F13', 'ctrl': True},
                      {'type': 'MIDDLEMOUSE', 'shift': True}):
            accepted = resolve_profiles([layer({CREATE: event, MODEL: event})])
            self.assertFalse(accepted.diagnostics)
            self.assertEqual(accepted.bindings[CREATE], accepted.bindings[MODEL])
        for command in (CREATE, MODEL):
            result = resolve_profiles([layer({command: None})])
            self.assertFalse(result.diagnostics)
            self.assertIsNone(result.bindings[command])
            self.assertIsNotNone(result.bindings[MODEL if command == CREATE else CREATE])
        for changes in ({MODEL: {'type': 'RIGHTMOUSE'}},
                        {CREATE: {'type': 'F13'}, MODEL: {'type': 'F13'}, 'tool.select': {'type': 'F13'}},
                        {MODEL: {'type': 'Y', 'ctrl': True}},
                        {MODEL: {'type': 'F', 'ctrl': True, 'shift': True}},
                        {MODEL: {'type': 'SPACE'}},
                        {MODEL: {'type': 'F13', 'alt': True}},
                        {MODEL: {'type': 'F13', 'oskey': True}}):
            result = resolve_profiles([layer(changes)])
            self.assertTrue(result.diagnostics, changes)
            self.assertEqual(result.bindings, baseline_bindings())

    def test_real_legacy_generated_entries_are_migrated_and_fallback_preserved(self):
        cursor = ('view3d.cursor3d', {'type': 'RIGHTMOUSE', 'value': 'PRESS', 'shift': True}, None)
        drag = ('transform.translate', {'type': 'RIGHTMOUSE', 'value': 'CLICK_DRAG', 'shift': True},
                {'properties': [('cursor_transform', True)]})
        legacy = ('axismeld.command', baseline_bindings()[CREATE], {'properties': [('command', CREATE)]})
        base = [(name, {}, {'items': [legacy, cursor, drag]}) for name in ('Object Mode', 'Mesh', '3D View')]
        current = generate_keymaps(base, baseline_bindings())
        self.assertEqual(generate_keymaps(current, baseline_bindings()), current)
        self.assertFalse(items_for(current, 'Mesh', CREATE))
        self.assertEqual(len(items_for(current, 'Mesh', MODEL)), 1)
        for name, _args, content in current[:3]:
            self.assertIn(cursor, content['items'], name)
            self.assertIn(drag, content['items'], name)
        for changed_command in (CREATE, MODEL):
            for event in (None, {'type': 'F13'}):
                resolved = resolve_profiles([layer({changed_command: event})])
                changed = generate_keymaps(current, resolved.bindings)
                self.assertEqual(generate_keymaps(changed, resolved.bindings), changed)
                for command, target in ((CREATE, 'Object Mode'), (MODEL, 'Mesh')):
                    own = items_for(changed, target, command)
                    self.assertEqual(len(own), int(resolved.bindings[command] is not None))
                    if own:
                        self.assertEqual(own[0][1], resolved.bindings[command])

    def test_global_interceptors_are_not_exempt(self):
        for name in ('Window', 'Screen', 'Frames'):
            base = [(name, {}, {'items': [('screen.other', baseline_bindings()[CREATE], None)]})]
            with self.assertRaisesRegex(ValueError, 'global input conflict'):
                validate_global_bindings(base, baseline_bindings())


class ModelingMenuTest(unittest.TestCase):
    def test_subrings_keep_source_directions_and_existing_requirements(self):
        nodes = {node['id']: node for node in walk(hotbox_catalog.default_catalog())}
        expected = {
            ROOTS[0] + '.merge': {'N': 'mesh.merge_center', 'NE': 'mesh.merge_distance'},
            ROOTS[1] + '.merge': {'N': 'mesh.merge_center', 'E': 'mesh.collapse'},
            ROOTS[1] + '.spin': {'E': 'mesh.edge_rotate_cw', 'W': 'mesh.edge_rotate_ccw'},
            ROOTS[0] + '.normals': {'S': 'display.vertex_normals', 'NE': 'normals.average_custom',
                                   'E': 'normals.rotate', 'SE': 'normals.set_from_faces'},
            ROOTS[1] + '.normals': {'NE': 'normals.soften_edges', 'E': 'normals.harden_by_angle',
                                   'SE': 'normals.harden_edges', 'S': 'display.sharp_edges'},
            ROOTS[2] + '.normals': {'S': 'display.face_normals', 'E': 'normals.reverse',
                                   'SE': 'normals.conform_outside'},
        }
        for root, commands in expected.items():
            actual = {child['direction']: child['command'] for child in nodes[root]['children']
                      if child['kind'] == 'command'}
            self.assertEqual(actual, commands)
        from axismeld.modeling_registry import SPECS
        self.assertEqual(SPECS['normals.set_from_faces'].requires, 'faces')

    def test_roots_directions_fixed_commands_and_honest_gaps(self):
        nodes = {node['id']: node for node in walk(hotbox_catalog.default_catalog())}
        expected = (
            {'NE': 'mesh.average_vertices', 'E': 'mesh.bevel_vertices', 'W': 'tool.mesh_knife', 'NW': 'selection.paint'},
            {'E': 'mesh.bevel_edges', 'S': 'mesh.extrude_edges', 'SW': 'mesh.dissolve_edges', 'W': 'tool.mesh_knife', 'NW': 'selection.paint'},
            {'N': 'mesh.merge_center', 'NE': 'mesh.poke_faces', 'S': 'mesh.extrude_region', 'W': 'tool.mesh_knife', 'NW': 'selection.paint'},
        )
        for root, expected_commands in zip(ROOTS, expected):
            self.assertIn(root, nodes)
            self.assertEqual(nodes[root]['presentation'], 'radial')
            children = {n['direction']: n for n in nodes[root]['children']}
            self.assertEqual(set(children), {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'})
            for direction, command in expected_commands.items():
                self.assertEqual(children[direction]['command'], command)
            for leaf in walk([nodes[root]]):
                if leaf['kind'] == 'command':
                    self.assertIn(leaf['command'], COMMANDS)
                    self.assertIn(leaf['command'], hotbox_runtime.SUPPORTED_COMMANDS)
                if leaf['kind'] == 'disabled':
                    self.assertFalse(leaf['enabled'])
                    self.assertFalse(leaf['command'])
                    self.assertIn('M2d-P', leaf['reason'])
        hotbox_runtime.serialize_snapshot(hotbox_runtime.make_snapshot(generation=1))
        self.assertNotIn(MODEL, hotbox_runtime.SUPPORTED_COMMANDS)


class ModelingSelectorTest(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module('axismeld.context_modeling_hotbox')
        self.bm = NS(**{domain: [NS(select=True, hide=False)] for domain in ('verts', 'edges', 'faces')})
        self.obj = NS(type='MESH', is_editable=True, data=NS(is_editable=True),
                      visible_get=lambda **kwargs: True)
        self.context = NS(area=NS(type='VIEW_3D'), region=NS(type='WINDOW'), mode='EDIT_MESH',
                          scene=NS(is_editable=True), tool_settings=NS(mesh_select_mode=(False, False, True)),
                          active_object=self.obj, objects_in_mode_unique_data=[self.obj], view_layer=object())
        self.host = patch.dict(sys.modules, {'bmesh': NS(from_edit_mesh=lambda data: self.bm)})
        self.host.start()
        self.addCleanup(self.host.stop)

    def test_explicit_domain_beats_selection_flush_and_does_not_mutate(self):
        before = repr(self.context), repr(self.bm)
        for index, root in enumerate(ROOTS):
            self.context.tool_settings.mesh_select_mode = tuple(i == index for i in range(3))
            self.assertEqual(self.module.modeling_root(self.context), root)
        self.assertEqual((repr(self.context), repr(self.bm)), before)

    def test_other_edit_mesh_selection_is_used_without_active_or_selection_change(self):
        other_data = NS(is_editable=True)
        other = NS(type='MESH', is_editable=True, data=other_data, visible_get=lambda **kwargs: True)
        self.context.objects_in_mode_unique_data.append(other)
        empty = NS(verts=[], edges=[], faces=[])
        with patch.dict(sys.modules, {'bmesh': NS(from_edit_mesh=lambda data: self.bm if data is other_data else empty)}):
            before = repr(self.context), repr(self.bm)
            self.assertEqual(self.module.modeling_root(self.context), ROOTS[2])
            self.assertEqual((repr(self.context), repr(self.bm)), before)


    def test_empty_mixed_hidden_uneditable_non_mesh_and_other_modes_fall_through(self):
        for flags in ((True, True, False), (False, False, False)):
            self.context.tool_settings.mesh_select_mode = flags
            self.assertIsNone(self.module.modeling_root(self.context))
        self.context.tool_settings.mesh_select_mode = (False, False, True)
        for obj, attr, bad in ((self.context, 'mode', 'OBJECT'), (self.obj, 'type', 'CURVE'),
                               (self.obj, 'is_editable', False), (self.obj.data, 'is_editable', False),
                               (self.context.scene, 'is_editable', False), (self.bm.faces[0], 'hide', True),
                               (self.bm.faces[0], 'select', False),
                               (self.obj, 'visible_get', lambda **kwargs: False)):
            old = getattr(obj, attr)
            setattr(obj, attr, bad)
            self.assertIsNone(self.module.modeling_root(self.context), attr)
            setattr(obj, attr, old)


class ModelingEntryTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def hotbox(*args, **kwargs):
            self.calls.append((args, kwargs))
            return {'RUNNING_MODAL'}
        hotbox.poll = lambda: True
        spec = importlib.util.spec_from_file_location('axismeld._modeling_test_adapter',
                                                     REPO / 'scripts/modules/axismeld/adapter.py')
        self.adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'bpy': NS(ops=NS(view3d=NS(axismeld_hotbox=hotbox)))}):
            spec.loader.exec_module(self.adapter)
        self.context = NS(area=NS(type='VIEW_3D'), region=NS(type='WINDOW'), mode='EDIT_MESH')
        source = ast.parse((REPO / 'scripts/startup/bl_operators/axismeld.py').read_text(encoding='utf-8'))
        cls = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == 'AXISMELD_OT_command')
        invoke = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'invoke')
        namespace = {'CREATE_HOTBOX': CREATE, 'MODEL_HOTBOX': MODEL, 'COMPONENT_HOTBOX': COMPONENT,
                     'adapter': self.adapter, 'TOOL_ROOTS': {}}
        exec(compile(ast.Module(body=[invoke], type_ignores=[]), '<real dispatcher invoke>', 'exec'), namespace)
        self.invoke = namespace['invoke']
        self.owner = NS(command=MODEL, _run=lambda *args, **kwargs: self.calls.append((args, kwargs)) or {'FINISHED'})

    def test_adapter_invokes_selected_root_and_execute_has_no_effect(self):
        for root in ROOTS:
            with patch.object(self.adapter, 'modeling_root', return_value=root), patch.object(hotbox_runtime, 'snapshot', return_value='snapshot'):
                self.assertTrue(self.adapter.available(self.context, MODEL)[0])
                self.assertEqual(self.adapter.run(self.context, MODEL), {'RUNNING_MODAL'})
                self.assertEqual(self.calls[-1], (('INVOKE_DEFAULT',), {'menu_json': 'snapshot', 'tool_menu': root}))
                count = len(self.calls)
                with self.assertRaisesRegex(ValueError, 'invoke event'):
                    self.adapter.run(self.context, MODEL, invoke=False)
                self.assertEqual(len(self.calls), count)

    def test_real_dispatcher_passes_invalid_context_and_events_to_native(self):
        event = NS(type='RIGHTMOUSE', value='PRESS', is_repeat=False, alt=False, oskey=False, ctrl=False, shift=True)
        with patch.object(self.adapter, 'modeling_root', return_value=None):
            self.assertEqual(self.invoke(self.owner, self.context, event), {'PASS_THROUGH'})
        with patch.object(self.adapter, 'modeling_root', return_value=ROOTS[2]):
            for attr, bad in (('value', 'RELEASE'), ('is_repeat', True), ('alt', True), ('oskey', True)):
                old = getattr(event, attr)
                setattr(event, attr, bad)
                self.assertEqual(self.invoke(self.owner, self.context, event), {'PASS_THROUGH'})
                setattr(event, attr, old)
            self.assertEqual(self.calls, [])
            for input_type, ctrl, shift in (('RIGHTMOUSE', False, True), ('MIDDLEMOUSE', False, True),
                                            ('F13', False, False), ('F13', True, False)):
                event.type, event.ctrl, event.shift = input_type, ctrl, shift
                self.assertEqual(self.invoke(self.owner, self.context, event), {'FINISHED'})



if __name__ == '__main__':
    unittest.main()

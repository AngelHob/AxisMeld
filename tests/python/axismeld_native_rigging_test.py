# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Native Rigging draw routing, mode guards and exact operator payloads without bpy."""
import ast
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))


class Layout:
    def __init__(self, events=None, enabled=True):
        self.events = events if events is not None else []
        self.enabled = enabled
        self.operator_context = 'INVOKE_REGION_WIN'

    def row(self, **_kwargs):
        return Layout(self.events, self.enabled)

    def menu(self, identifier, **kwargs):
        self.events.append(dict(api='menu', identifier=identifier, enabled=self.enabled, **kwargs))

    def label(self, **kwargs):
        self.events.append(dict(api='label', enabled=self.enabled, **kwargs))

    def operator(self, identifier, **kwargs):
        props = NS()
        self.events.append(dict(api='operator', identifier=identifier, enabled=self.enabled,
                                invocation=self.operator_context, properties=props, **kwargs))
        return props


class TraceLayout:
    """Capture native layout calls, properties and nested layout context."""
    def __init__(self, events=None):
        self.events = [] if events is None else events
        self.operator_context = 'INVOKE_REGION_WIN'

    def __getattr__(self, api):
        def call(*args, **kwargs):
            if api in {'row', 'column', 'split', 'box', 'column_flow', 'grid_flow'}:
                child = TraceLayout(self.events)
                child.operator_context = self.operator_context
                self.events.append((api, args, kwargs, self.operator_context, None))
                return child
            props = NS(constraint_axis=[False, False, False]) if api.startswith('operator') else None
            self.events.append((api, args, kwargs, self.operator_context, props))
            return props
        return call


ICON_DRAW_CLASSES = frozenset({
    'BoneOptions', 'ShowHideMenu', 'VIEW3D_MT_armature_add', 'VIEW3D_MT_bone_collections',
    'VIEW3D_MT_bone_options_toggle', 'VIEW3D_MT_edit_armature', 'VIEW3D_MT_edit_armature_delete',
    'VIEW3D_MT_edit_armature_names', 'VIEW3D_MT_edit_armature_parent', 'VIEW3D_MT_edit_armature_roll',
    'VIEW3D_MT_edit_mesh_weights', 'VIEW3D_MT_mirror', 'VIEW3D_MT_object_animation',
    'VIEW3D_MT_object_parent', 'VIEW3D_MT_paint_weight', 'VIEW3D_MT_paint_weight_lock',
    'VIEW3D_MT_pose', 'VIEW3D_MT_pose_apply', 'VIEW3D_MT_pose_constraints', 'VIEW3D_MT_pose_ik',
    'VIEW3D_MT_pose_motion', 'VIEW3D_MT_pose_names', 'VIEW3D_MT_pose_propagate',
    'VIEW3D_MT_pose_showhide', 'VIEW3D_MT_pose_slide', 'VIEW3D_MT_pose_transform',
    'VIEW3D_MT_snap', 'VIEW3D_MT_transform_armature', 'VIEW3D_MT_transform_base',
    'VIEW3D_MT_vertex_group',
})


def obj(kind='MESH', editable=True):
    return NS(type=kind, is_editable=editable, data=NS(is_editable=editable))


def context(mode='OBJECT', active=None, selected=None, area='VIEW_3D'):
    return NS(mode=mode, active_object=active, object=active,
              edit_object=active if mode.startswith('EDIT_') else None,
              selected_objects=selected if selected is not None else ([active] if active else []),
              area=NS(type=area), region=NS(type='HEADER'), scene=NS(is_editable=True))


class NativeRiggingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'scripts/startup/bl_ui/space_axismeld_native_rigging.py'
        if not path.exists():
            cls.api = None
            return
        cls.poll_value = True
        operation = NS(poll=lambda: cls.poll_value)
        fake = ModuleType('bpy')
        fake.types = ModuleType('bpy.types')
        fake.types.Menu = type('Menu', (), {})
        fake.ops = NS(object=NS(parent_set=operation, armature_add=operation),
                      paint=NS(weight_paint_toggle=operation))
        spec = importlib.util.spec_from_file_location('native_rigging_subject', path)
        cls.api = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'bpy': fake, 'bpy.types': fake.types}):
            spec.loader.exec_module(cls.api)

    def setUp(self):
        self.assertIsNotNone(self.api, 'Native Rigging renderer is missing')
        type(self).poll_value = True

    def draw(self, key, source):
        layout = Layout()
        self.api.draw_entry(layout, source, key)
        self.assertEqual(len(layout.events), 1, key)
        self.assertTrue(layout.events[0]['icon'])
        return layout.events[0]

    def test_real_menu_hosts_are_used_in_valid_modes(self):
        bone, mesh = obj('ARMATURE'), obj()
        for key, source, host in (
            ('skeleton.create', context(), 'VIEW3D_MT_armature_add'),
            ('skeleton.edit_bones', context('EDIT_ARMATURE', bone), 'VIEW3D_MT_edit_armature'),
            ('skeleton.pose', context('POSE', bone), 'VIEW3D_MT_pose'),
            ('skeleton.ik', context('POSE', bone), 'VIEW3D_MT_pose_ik'),
            ('skin.weights', context('PAINT_WEIGHT', mesh), 'VIEW3D_MT_paint_weight'),
            ('skin.weights', context('EDIT_MESH', mesh), 'VIEW3D_MT_edit_mesh_weights'),
            ('skin.vertex_groups', context('OBJECT', mesh), 'VIEW3D_MT_vertex_group'),
            ('skin.group_specials', context('PAINT_WEIGHT', mesh), 'MESH_MT_vertex_group_context_menu'),
        ):
            event = self.draw(key, source)
            self.assertEqual((event['api'], event['identifier'], event['enabled']), ('menu', host, True))

    def test_no_target_and_wrong_mode_are_disabled(self):
        for key in ('skeleton.edit_bones', 'skeleton.pose', 'skeleton.ik', 'skin.weights',
                    'skin.bind', 'skin.weight_paint', 'skin.vertex_groups', 'skin.group_specials'):
            self.assertFalse(self.draw(key, context())['enabled'], key)
        self.assertFalse(self.draw('skeleton.edit_bones', context('POSE', obj('ARMATURE')))['enabled'])
        self.assertFalse(self.draw('skin.weights', context('OBJECT', obj()))['enabled'])

    def test_unavailable_entries_are_labels_without_previewable_menu_hosts(self):
        cases = [('skeleton.create', context('POSE', obj('ARMATURE'))),
                 ('skeleton.edit_bones', context('POSE', obj('ARMATURE'))),
                 ('skin.weights', context('OBJECT', obj()))]
        cases.extend((key, context()) for key in self.api.ENTRIES if key != 'skeleton.create')
        cases.extend((key, context(area='OUTLINER')) for key in self.api.ENTRIES)
        for key, source in cases:
            with self.subTest(key=key, mode=source.mode, area=source.area.type):
                entry = self.api.ENTRIES[key]
                self.assertEqual(self.draw(key, source),
                                 dict(api='label', enabled=False, text=entry['label'], icon=entry['icon']))

    def test_other_editor_does_not_resolve_or_change_a_viewport_target(self):
        bone, mesh = obj('ARMATURE'), obj()
        for area in ('TOPBAR', 'OUTLINER', 'PROPERTIES'):
            source = context('OBJECT', bone, [mesh, bone], area=area)
            for key in self.api.ENTRIES:
                self.assertFalse(self.draw(key, source)['enabled'], (area, key))
            self.assertIs(source.active_object, bone)
            self.assertEqual(source.selected_objects, [mesh, bone])
            self.assertEqual(source.mode, 'OBJECT')

    def test_bind_requires_editable_active_armature_and_mesh_selection(self):
        bone, mesh = obj('ARMATURE'), obj()
        valid = context('OBJECT', bone, [mesh, bone])
        self.assertTrue(self.draw('skin.bind', valid)['enabled'])
        for invalid in (context('OBJECT', bone), context('OBJECT', mesh, [mesh, bone]),
                        context('POSE', bone, [mesh, bone]),
                        context('OBJECT', bone, [obj(editable=False), bone]),
                        context('OBJECT', obj('ARMATURE', editable=False), [mesh, bone]),
                        context('OBJECT', bone, [mesh, bone, obj('LIGHT')])):
            self.assertFalse(self.draw('skin.bind', invalid)['enabled'])

    def test_bind_preserves_all_four_native_parent_modes_and_defaults(self):
        bone, mesh = obj('ARMATURE'), obj()
        menu_type = next(c for c in self.api.classes if c.__name__ == 'AXISMELD_MT_rigging_armature_deform')
        menu = menu_type()
        menu.layout = Layout()
        menu.draw(context('OBJECT', bone, [mesh, bone]))
        events = menu.layout.events
        self.assertEqual([e['identifier'] for e in events], ['object.parent_set'] * 4)
        self.assertEqual([vars(e['properties']) for e in events],
                         [{'type': value} for value in
                          ('ARMATURE', 'ARMATURE_NAME', 'ARMATURE_AUTO', 'ARMATURE_ENVELOPE')])
        self.assertTrue(all(e['enabled'] and e['icon'] for e in events))

    def test_linked_armature_data_allows_pose_and_read_only_bind_target(self):
        bone, mesh = obj('ARMATURE'), obj()
        bone.data.is_editable = False
        for key in ('skeleton.pose', 'skeleton.ik'):
            self.assertTrue(self.draw(key, context('POSE', bone))['enabled'], key)
        self.assertTrue(self.draw('skin.bind', context('OBJECT', bone, [mesh, bone]))['enabled'])
        self.assertFalse(self.draw('skeleton.edit_bones', context('EDIT_ARMATURE', bone))['enabled'])
        mesh.data.is_editable = False
        self.assertFalse(self.draw('skin.bind', context('OBJECT', bone, [mesh, bone]))['enabled'])
        bone.is_editable = False
        for key in ('skeleton.pose', 'skeleton.ik'):
            self.assertFalse(self.draw(key, context('POSE', bone))['enabled'], key)

    def test_weight_paint_toggle_is_explicit_and_respects_native_poll(self):
        event = self.draw('skin.weight_paint', context('OBJECT', obj()))
        self.assertEqual((event['identifier'], vars(event['properties'])), ('paint.weight_paint_toggle', {}))
        self.assertTrue(event['enabled'])
        type(self).poll_value = False
        self.assertFalse(self.draw('skin.weight_paint', context('OBJECT', obj()))['enabled'])
        bone, mesh = obj('ARMATURE'), obj()
        self.assertFalse(self.draw('skin.bind', context('OBJECT', bone, [mesh, bone]))['enabled'])

    @contextmanager
    def icon_modules(self):
        ui = ModuleType('bl_ui')
        ui.space_axismeld_native_rigging = self.api
        ui.space_axismeld_menubar = NS(rigging_workspace=lambda source: getattr(source, 'rigging', False))
        with patch.dict(sys.modules, {'bl_ui': ui, 'bl_ui.space_axismeld_native_rigging': self.api}):
            yield

    def test_icon_proxy_preserves_explicit_icons_nested_layout_and_context(self):
        decorate = getattr(self.api, 'rigging_icon_layout', None)
        self.assertTrue(callable(decorate), 'Missing context-limited native icon decorator')
        with self.icon_modules():
            plain = TraceLayout()
            self.assertIs(decorate(plain, NS(rigging=False), 'BONE_DATA'), plain)
            icon = decorate(plain, NS(rigging=True), 'BONE_DATA')
            row = icon.row().column().split().box()
            row.operator_context = 'EXEC_REGION_WIN'
            row.operator('armature.extrude_move')
            row.operator('pose.copy', icon='COPYDOWN')
            row.menu('ExplicitNone', icon='NONE')
            row.menu('CustomPreview', icon_value=517)
            row.operator_enum('object.parent_set', 'type')
        entries = plain.events[4:]
        self.assertEqual(entries[0][2]['icon'], 'BONE_DATA')
        self.assertEqual(entries[0][3], 'EXEC_REGION_WIN')
        self.assertEqual(entries[1][2]['icon'], 'COPYDOWN')
        self.assertEqual(entries[2][2]['icon'], 'NONE')
        self.assertEqual(entries[3][2], {'icon_value': 517})
        self.assertEqual(entries[4][2], {})  # Native operator_enum has no icon argument.

    def test_native_subtrees_keep_original_calls_params_context_and_add_missing_icons(self):
        tree = ast.parse((ROOT / 'scripts/startup/bl_ui/space_view3d.py').read_text(encoding='utf-8'))
        declarations = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ICON_DRAW_CLASSES]
        self.assertEqual(len(declarations), len(ICON_DRAW_CLASSES))
        bone_props = {key: NS(name=key) for key in
                      ('show_wire', 'use_deform', 'use_envelope_multiply', 'use_inherit_rotation', 'lock')}
        self.api.bpy.types.Bone = NS(bl_rna=NS(properties=bone_props))
        self.api.bpy.types.EditBone = NS(bl_rna=NS(properties=bone_props))
        namespace = dict(Menu=type('Menu', (), {}), bpy=self.api.bpy, iface_=lambda text: text,
                         i18n_contexts=NS(default='default', operator_default='operator_default'))
        exec(compile(ast.Module(body=declarations, type_ignores=[]), 'native_rigging_draws', 'exec'), namespace)
        observed = set()
        with self.icon_modules():
            for name in sorted(ICON_DRAW_CLASSES):
                for mode, object_mode, display in (('EDIT_ARMATURE', 'EDIT', 'BBONE'),
                                                   ('POSE', 'POSE', 'ENVELOPE'),
                                                   ('PAINT_WEIGHT', 'WEIGHT_PAINT', 'BBONE')):
                    if name == 'VIEW3D_MT_edit_armature' and mode != 'EDIT_ARMATURE':
                        continue  # This host dereferences edit_object; its parent guards the mode.
                    active = obj('MESH' if mode == 'PAINT_WEIGHT' else 'ARMATURE')
                    active.mode = object_mode
                    active.vertex_groups = NS(active=True)
                    active.data.use_mirror_x = True
                    active.data.display_type = display
                    active.data.use_paint_mask_vertex = True
                    source = context(mode, active)
                    records = []
                    for is_rigging in (False, True):
                        source.rigging = is_rigging
                        menu = namespace[name]()
                        menu.type = 'TOGGLE'
                        menu.layout = TraceLayout()
                        menu.draw(source)
                        records.append(menu.layout.events)
                    before, after = records
                    self.assertEqual(len(before), len(after), name)
                    for old, new in zip(before, after):
                        api, args, kwargs, invoke, props = old
                        other_api, other_args, other_kwargs, other_invoke, other_props = new
                        normalized = dict(other_kwargs)
                        if api in {'operator', 'menu', 'operator_menu_enum'} and 'icon' not in kwargs:
                            self.assertTrue(normalized.pop('icon', None), (name, api, args))
                        self.assertEqual((other_api, other_args, normalized, other_invoke,
                                          vars(other_props) if other_props else None),
                                         (api, args, kwargs, invoke, vars(props) if props else None), name)
                        if api == 'operator':
                            observed.add(args[0])
        self.assertTrue({'armature.extrude_move', 'pose.transforms_clear', 'paint.weight_from_bones'} <= observed)

    def test_vertex_group_specials_and_rigify_parent_keep_native_payloads(self):
        for relative, name in (
                ('scripts/startup/bl_ui/properties_data_mesh.py', 'MESH_MT_vertex_group_context_menu'),
                ('scripts/modules/rigify/metarig_menu.py', '_menu_add_rigify_metarigs')):
            tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
            declaration = next(node for node in tree.body if getattr(node, 'name', None) == name)
            namespace = dict(Menu=type('Menu', (), {}))
            exec(compile(ast.Module(body=[declaration], type_ignores=[]), relative, 'exec'), namespace)
            records = []
            with self.icon_modules():
                for enabled in (False, True):
                    source = NS(rigging=enabled)
                    if isinstance(declaration, ast.ClassDef):
                        host = namespace[name]()
                        host.layout = TraceLayout()
                        host.draw(source)
                    else:
                        host = NS(layout=TraceLayout())
                        namespace[name](host, source)
                    records.append(host.layout.events)
            self.assertEqual(len(records[0]), len(records[1]))
            for before, after in zip(*records):
                old_api, old_args, old_kwargs, old_context, old_props = before
                api, args, kwargs, invocation, props = after
                normalized = dict(kwargs)
                if api in {'operator', 'menu'} and 'icon' not in old_kwargs:
                    self.assertTrue(normalized.pop('icon', None), (name, args))
                self.assertEqual((api, args, normalized, invocation, vars(props) if props else None),
                                 (old_api, old_args, old_kwargs, old_context,
                                  vars(old_props) if old_props else None))


if __name__ == '__main__':
    unittest.main()

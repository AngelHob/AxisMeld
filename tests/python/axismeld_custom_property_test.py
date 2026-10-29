# SPDX-License-Identifier: GPL-2.0-or-later
"""Focused native RNA tests; run with Blender --background --factory-startup.

This explicitly overlays source modules in this test-owned process. The dialog
host alone is replaced: ID properties, Operator RNA and enum updates are real.
"""
from pathlib import Path
from types import SimpleNamespace
import importlib
import json
import os
import sys
import unittest
import weakref

try:
    import bpy
except ImportError:
    raise unittest.SkipTest('Custom property RNA tests require Blender')

ROOT = Path(os.environ.get('AXISMELD_SOURCE_ROOT', Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / 'scripts/modules'))
import axismeld
axismeld.__path__.insert(0, str(ROOT / 'scripts/modules/axismeld'))
sys.modules.pop('axismeld.modeling_common_ops', None)
implementation = importlib.import_module('axismeld.modeling_common_ops')
Op = implementation.AXISMELD_OT_m3_custom_property
RUN = None
ERROR = None


class DialogContext:
    window_manager = SimpleNamespace(invoke_props_dialog=lambda operator: {'RUNNING_MODAL'})

    def __getattr__(self, name):
        return getattr(bpy.context, name)


class OperatorProxy:
    """Intercept reports only; all draft attributes still live in native RNA."""
    def __init__(self, operator):
        object.__setattr__(self, 'operator', operator)
        object.__setattr__(self, 'messages', [])

    def __getattr__(self, name):
        return getattr(self.operator, name)

    def __setattr__(self, name, value):
        setattr(self.operator, name, value)

    def report(self, levels, message):
        self.messages.append((levels, message))


class AXISMELD_OT_custom_property_test_bridge(bpy.types.Operator):
    bl_idname = 'axismeld.custom_property_test_bridge'
    bl_label = 'Test-owned native RNA bridge'
    __annotations__ = Op.__annotations__.copy()

    def execute(self, context):
        global ERROR
        try:
            RUN(OperatorProxy(self))
        except Exception as error:
            ERROR = error
        return {'FINISHED'}


def register():
    for cls in (Op, AXISMELD_OT_custom_property_test_bridge):
        existing = getattr(bpy.types, cls.__name__, None)
        if existing:
            bpy.utils.unregister_class(existing)
        bpy.utils.register_class(cls)


def snapshot(obj):
    return {key: (type(obj[key]).__name__, obj[key]) for key in obj.keys()}


def clear_properties(obj):
    for key in tuple(obj.keys()):
        del obj[key]


class CustomPropertyTests(unittest.TestCase):
    def setUp(self):
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        self.obj = bpy.data.objects.new('CP Source', bpy.data.meshes.new('CP Mesh'))
        bpy.context.scene.collection.objects.link(self.obj)
        bpy.context.view_layer.objects.active = self.obj
        self.obj.select_set(True)

    def bridge(self, callback, **kwargs):
        global RUN, ERROR
        RUN = callback
        ERROR = None
        self.assertEqual(bpy.ops.axismeld.custom_property_test_bridge('EXEC_DEFAULT', **kwargs), {'FINISHED'})
        if ERROR:
            raise ERROR

    def opened(self, op):
        self.assertEqual(Op.invoke(op, DialogContext(), None), {'RUNNING_MODAL'})

    def test_untouched_four_types(self):
        for key, value, kind in (('Count', 7, 'INTEGER'), ('Enabled', False, 'BOOLEAN'),
                                 ('Text', '007', 'STRING'), ('Weight', 1.5, 'FLOAT'),
                                 ('Empty', '', 'STRING'), ('Zero', 0, 'INTEGER')):
            with self.subTest(key=key):
                clear_properties(self.obj)
                self.obj[key] = value
                before = snapshot(self.obj)
                def check(op):
                    self.opened(op)
                    self.assertEqual((op.name, op.kind, op.value), (key, kind, str(value)))
                    self.assertEqual(snapshot(self.obj), before)
                    self.assertEqual(Op.execute(op, bpy.context), {'FINISHED'})
                self.bridge(check, action='EDIT')
                self.assertEqual(snapshot(self.obj), before)

    def test_selector_refreshes_all_draft_fields_without_writes(self):
        self.obj['First'] = 1.5
        self.obj['第二项'] = '007'
        before = snapshot(self.obj)
        def check(op):
            self.opened(op)
            op.name, op.kind, op.value = 'Discarded', 'BOOLEAN', 'true'
            op.property = '第二项'  # Native RNA update callback, not a helper call.
            self.assertEqual((op.name, op.kind, op.value), ('第二项', 'STRING', '007'))
            self.assertEqual(snapshot(self.obj), before)
            self.assertEqual(Op.execute(op, bpy.context), {'FINISHED'})
        self.bridge(check, action='EDIT')
        self.assertEqual(snapshot(self.obj), before)

    def test_active_source_swap_preserves_both_objects_for_each_action(self):
        self.obj['Value'] = 1.5
        other = bpy.data.objects.new('CP Other', None)
        bpy.context.scene.collection.objects.link(other)
        other['Value'] = 9.5
        for action in ('EDIT', 'DELETE', 'ADD'):
            with self.subTest(action=action):
                bpy.context.view_layer.objects.active = self.obj
                before = snapshot(self.obj), snapshot(other)
                def check(op):
                    self.opened(op)
                    bpy.context.view_layer.objects.active = other
                    self.assertEqual(Op.execute(op, bpy.context), {'CANCELLED'})
                    self.assertTrue(op.messages)
                self.bridge(check, action=action)
                self.assertEqual((snapshot(self.obj), snapshot(other)), before)

    def test_cancel_discards_draft(self):
        self.obj['Count'] = 7
        before = snapshot(self.obj)
        def check(op):
            self.opened(op)
            op.value = '22'
            getattr(Op, 'cancel', lambda *_: None)(op, bpy.context)
        self.bridge(check, action='EDIT')
        self.assertEqual(snapshot(self.obj), before)

    def test_native_operator_supports_transient_weak_owner(self):
        def check(op):
            self.assertIs(weakref.ref(op.operator)(), op.operator)
        self.bridge(check, action='ADD')

    def test_failed_confirmation_keeps_guard_but_does_not_contaminate_exec(self):
        self.obj['Count'] = 7
        def check(op):
            self.opened(op)
            op.value = 'invalid'
            self.assertEqual(Op.execute(op, bpy.context), {'CANCELLED'})
            other = bpy.data.objects.new('CP Retry Other', None)
            bpy.context.scene.collection.objects.link(other)
            other['Count'] = 99
            bpy.context.view_layer.objects.active = other
            op.value = '4'
            self.assertEqual(Op.execute(op, bpy.context), {'CANCELLED'})
            self.assertEqual(other['Count'], 99)
            # A fresh EXEC gets no stale callback draft even while this failed
            # operator remains alive. Native pointer reuse was observed in RED.
            self.assertEqual(bpy.ops.axismeld.m3_custom_property('EXEC_DEFAULT', action='EDIT',
                property='Count', name='Script', kind='STRING', value='009'), {'FINISHED'})
            self.assertEqual(other['Script'], '009')
        self.bridge(check, action='EDIT')

    def test_user_enum_names_are_untranslated_in_chinese(self):
        for module in ('axismeld.translations_reasons', 'axismeld.translations'):
            sys.modules.pop(module, None)
            importlib.import_module(module)
        from axismeld import translations
        translations.register()
        bpy.context.preferences.view.language = 'zh_HANS'
        context = bpy.ops.axismeld.m3_custom_property.get_rna_type().properties['property'].translation_context
        self.assertNotEqual(bpy.app.translations.pgettext('Name'), 'Name')
        self.assertEqual(bpy.app.translations.pgettext('Name', context), 'Name')
        for message in ('Custom property source context or object changed',
                        'No supported custom property on the active object',
                        'Selected custom property is missing or unsupported',
                        'Custom property value is invalid for the selected type',
                        'Choose a unique non-reserved property name'):
            self.assertNotEqual(bpy.app.translations.pgettext(message), message)
        bpy.context.preferences.view.language = 'en_US'

    def test_selected_delete_and_deliberate_rename_type_change(self):
        self.obj['First'] = 1
        self.obj['Second'] = 2
        def edit(op):
            self.opened(op)
            op.property = 'Second'
            op.name, op.kind, op.value = 'Renamed', 'STRING', '用户内容'
            self.assertEqual(Op.execute(op, bpy.context), {'FINISHED'})
        self.bridge(edit, action='EDIT')
        self.assertEqual(snapshot(self.obj), {'First': ('int', 1), 'Renamed': ('str', '用户内容')})
        def delete(op):
            self.opened(op)
            op.property = 'Renamed'
            self.assertEqual(Op.execute(op, bpy.context), {'FINISHED'})
        self.bridge(delete, action='DELETE')
        self.assertEqual(snapshot(self.obj), {'First': ('int', 1)})

    def test_explicit_exec_arguments_are_never_refreshed(self):
        self.obj['Original'] = 7
        self.assertEqual(bpy.ops.axismeld.m3_custom_property('EXEC_DEFAULT', action='EDIT',
            property='Original', name='Script Name', kind='STRING', value='008'), {'FINISHED'})
        self.assertEqual(snapshot(self.obj), {'Script Name': ('str', '008')})

    def test_invalid_conversion_and_collision_preserve_properties(self):
        self.obj['Count'] = 7
        self.obj['Other'] = 8
        before = snapshot(self.obj)
        for name, kind, value in (('Other', 'INTEGER', '4'), ('Count', 'INTEGER', '1.2'),
                                   ('Count', 'BOOLEAN', 'maybe'), ('_private', 'STRING', 'x')):
            def check(op):
                self.opened(op)
                op.name, op.kind, op.value = name, kind, value
                self.assertEqual(Op.execute(op, bpy.context), {'CANCELLED'})
                self.assertTrue(op.messages)
            self.bridge(check, action='EDIT')
            self.assertEqual(snapshot(self.obj), before)

    def test_removed_or_unsupported_property_cancels(self):
        for replacement in (None, [1, 2]):
            clear_properties(self.obj)
            self.obj['Value'] = 3
            def check(op):
                self.opened(op)
                del self.obj['Value']
                if replacement is not None:
                    self.obj['Value'] = replacement
                before = tuple(self.obj.keys())
                self.assertEqual(Op.execute(op, bpy.context), {'CANCELLED'})
                self.assertEqual(tuple(self.obj.keys()), before)
                self.assertTrue(op.messages)
            self.bridge(check, action='EDIT')

    def test_no_supported_properties_reports_reason(self):
        self.obj['Array'] = [1, 2]
        def check(op):
            self.assertEqual(Op.invoke(op, DialogContext(), None), {'CANCELLED'})
            self.assertTrue(op.messages)
        self.bridge(check, action='EDIT')

    def test_same_name_object_replacement_cancels(self):
        self.obj['Count'] = 7
        name = self.obj.name
        def check(op):
            self.opened(op)
            bpy.data.objects.remove(self.obj, do_unlink=True)
            other = bpy.data.objects.new(name, None)
            bpy.context.scene.collection.objects.link(other)
            other['Count'] = 99
            bpy.context.view_layer.objects.active = other
            self.assertEqual(Op.execute(op, bpy.context), {'CANCELLED'})
            self.assertEqual(other['Count'], 99)
        self.bridge(check, action='EDIT')

    def test_changed_scene_layer_window_and_mode_cancel(self):
        self.obj['Count'] = 7
        for field, replacement in (('scene', bpy.data.scenes.new('CP Other Scene')),
                                   ('view_layer', bpy.context.scene.view_layers.new('CP Other Layer')),
                                   ('window', SimpleNamespace(as_pointer=lambda: -1)),
                                   ('mode', 'EDIT_MESH')):
            def check(op):
                self.opened(op)
                changed = DialogContext()
                setattr(changed, field, replacement)
                before = snapshot(self.obj)
                self.assertEqual(Op.execute(op, changed), {'CANCELLED'})
                self.assertEqual(snapshot(self.obj), before)
            self.bridge(check, action='EDIT')

    def test_success_releases_first_confirm_guard_for_redo(self):
        self.obj['Count'] = 7
        def check(op):
            self.opened(op)
            self.assertEqual(Op.execute(op, bpy.context), {'FINISHED'})
            replacement = bpy.data.objects.new('Redo Rebuilt ID', None)
            bpy.context.scene.collection.objects.link(replacement)
            replacement['Count'] = 7
            bpy.context.view_layer.objects.active = replacement
            op.value = '9'
            self.assertEqual(Op.execute(op, bpy.context), {'FINISHED'})
            self.assertEqual(replacement['Count'], 9)
        self.bridge(check, action='EDIT')


if __name__ == '__main__':
    register()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CustomPropertyTests))
    payload = {'module': implementation.__file__, 'method': 'test-owned source overlay; native RNA; stub dialog host',
               'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors)}
    print('AXISMELD_CUSTOM_PROPERTY_RESULT', json.dumps(payload), flush=True)
    if not result.wasSuccessful():
        raise SystemExit(1)

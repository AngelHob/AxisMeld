# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
from bpy.types import Operator, KeyConfigPreferences, WindowManager
from bpy.props import StringProperty, BoolProperty, FloatProperty

from axismeld import adapter, runtime, hotbox_runtime
from axismeld.commands import PRESET_NAME


class AXISMELD_OT_command(Operator):
    bl_idname = 'axismeld.command'
    bl_label = 'AxisMeld Workflow Command'
    bl_description = 'Run a Maya-style modeling command through the AxisMeld adapter'
    # Native operators own undo; wrapping modal navigation must not add another undo entry.
    bl_options = {'INTERNAL'}

    command: StringProperty(name='Semantic command')

    @classmethod
    def poll(cls, context):
        return adapter.modeling_context(context)

    def _run(self, context, invoke):
        try:
            result = adapter.run(context, self.command, invoke=invoke)
        except (ValueError, RuntimeError) as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        # Nested native modal operators own their handlers and subsequent mouse events.
        return {'FINISHED'} if 'RUNNING_MODAL' in result else result

    def execute(self, context):
        return self._run(context, False)

    def invoke(self, context, event):
        return self._run(context, True)


class AXISMELD_OT_reload_profile(Operator):
    bl_idname = 'axismeld.reload_profile'
    bl_label = 'Reload AxisMeld Profiles'
    bl_description = 'Reload studio.json and user.json; native keymap edits remain managed by Blender'

    @classmethod
    def poll(cls, context):
        return context.window_manager.keyconfigs.active.name == PRESET_NAME

    def execute(self, context):
        runtime.load()
        self.report({'WARNING'} if runtime.diagnostics else {'INFO'},
                    '; '.join(runtime.diagnostics) or 'AxisMeld profiles loaded')
        return {'FINISHED'}


class AXISMELD_OT_hotbox_dispatch(Operator):
    bl_idname = 'axismeld.hotbox_dispatch'
    bl_label = 'AxisMeld Hotbox Command'
    bl_options = {'INTERNAL'}
    command: StringProperty(name='Semantic command')

    def execute(self, context):
        result = hotbox_runtime.dispatch(context, self.command)
        # Only the child owns a modal handler. A running child is not successful history yet.
        return {'FINISHED'} if 'RUNNING_MODAL' in result else result


class AXISMELD_OT_hotbox_setting(Operator):
    bl_idname = 'axismeld.hotbox_setting'
    bl_label = 'AxisMeld Hotbox Setting'
    bl_options = {'INTERNAL'}
    setting: StringProperty(name='Setting')
    value: StringProperty(name='Option')

    def execute(self, context):
        try:
            hotbox_runtime.apply_setting(context, self.setting, self.value)
        except ValueError as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class AXISMELD_OT_hotbox_refresh(Operator):
    bl_idname = 'axismeld.hotbox_refresh'
    bl_label = 'Refresh AxisMeld Hotbox'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        wm = context.window_manager
        wm.axismeld_hotbox_snapshot = ''
        try:
            wm.axismeld_hotbox_snapshot = hotbox_runtime.snapshot(context)
        except Exception as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


def _update_profile(self, context):
    runtime.load()


class AXISMELD_Preferences(KeyConfigPreferences):
    bl_idname = PRESET_NAME

    use_file_overrides: BoolProperty(
        name='Use Studio and User Profile Files', default=True, update=_update_profile,
        description='Disable to use the public Maya baseline; Blender native keymap edits remain separate')

    hotbox_tap_seconds: FloatProperty(
        name='Hotbox Tap Threshold', default=0.4, min=0.1, max=1.0,
        description='Maximum trigger-key tap duration for single/quad view switching')

    def draw(self, layout):
        layout.label(text='Maya 2026 - Modeling baseline (adapted)')
        layout.label(text='Click a transform axis, then middle-drag in empty viewport space')
        layout.prop(self, 'hotbox_tap_seconds')
        layout.prop(self, 'use_file_overrides')
        layout.operator('axismeld.reload_profile')
        layout.label(text=str(runtime.profile_directory() or 'No configuration directory'))
        layout.label(text='View hotbox is adapted; full Maya hotbox, snapping and UV are not implemented')
        for message in runtime.diagnostics:
            layout.label(text=message, icon='ERROR')


classes = (AXISMELD_OT_command, AXISMELD_OT_reload_profile, AXISMELD_OT_hotbox_dispatch,
           AXISMELD_OT_hotbox_setting, AXISMELD_OT_hotbox_refresh)


def register():
    from bpy.utils import register_class
    register_class(AXISMELD_Preferences)
    WindowManager.axismeld_hotbox_snapshot = StringProperty(
        name='AxisMeld Hotbox Snapshot', options={'HIDDEN', 'SKIP_SAVE'})


def unregister():
    from bpy.utils import unregister_class
    unregister_class(AXISMELD_Preferences)
    del WindowManager.axismeld_hotbox_snapshot

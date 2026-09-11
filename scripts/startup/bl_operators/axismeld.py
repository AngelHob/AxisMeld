# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
from bpy.types import Operator, KeyConfigPreferences, WindowManager
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty

from axismeld import adapter, runtime, hotbox_runtime
from axismeld.commands import PRESET_NAME
from axismeld.hotbox_catalog import registered_menu_choices
from axismeld.hotbox_profiles import DEFAULT_APPEARANCE
from axismeld.tool_hotbox import TOOL_ROOTS


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

    def _run(self, context, invoke, keyboard_tool_session=False):
        try:
            result = adapter.run(context, self.command, invoke=invoke,
                                 keyboard_tool_session=keyboard_tool_session)
        except (ValueError, RuntimeError) as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        # Nested native modal operators own their handlers and subsequent mouse events.
        return {'FINISHED'} if 'RUNNING_MODAL' in result else result

    def execute(self, context):
        return self._run(context, False)

    def invoke(self, context, event):
        keyboard = event.value == 'PRESS' and event.type not in {
            'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'BUTTON4MOUSE', 'BUTTON5MOUSE',
            'ACTIONZONE_AREA', 'ACTIONZONE_REGION', 'NONE'}
        if self.command in TOOL_ROOTS and event.is_repeat:
            return {'CANCELLED'}
        return self._run(context, True, keyboard_tool_session=keyboard)


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


class AXISMELD_OT_hotbox_reset_appearance(Operator):
    bl_idname = 'axismeld.hotbox_reset_appearance'
    bl_label = 'Restore Appearance Defaults'
    bl_description = 'Restore public hotbox colors and 75% opacity; keep keymaps, layout and mouse mappings'

    def execute(self, context):
        try:
            hotbox_runtime.reset_appearance(context)
        except ValueError as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


def _appearance_update(field):
    def update(self, context):
        if hotbox_runtime.preferences_are_syncing():
            return
        value = getattr(self, f'hotbox_{field}')
        if isinstance(DEFAULT_APPEARANCE[field], list):
            value = [round(channel*255) for channel in value]
        try:
            hotbox_runtime.apply_appearance(context, field, value)
        except ValueError as error:
            print('AxisMeld:', error)
            hotbox_runtime.reload_settings(context)
    return update


def _appearance_color(field, name):
    return FloatVectorProperty(
        name=name, size=3, subtype='COLOR_GAMMA', min=0, max=1,
        default=tuple(channel/255 for channel in DEFAULT_APPEARANCE[field]),
        options={'SKIP_SAVE'}, update=_appearance_update(field))


def _update_profile(self, context):
    runtime.load()


def _hotbox_update(setting, attribute=None):
    def update(self, context):
        if hotbox_runtime.preferences_are_syncing():
            return
        value = 'toggle' if attribute is None else getattr(self, attribute)
        try:
            hotbox_runtime.apply_setting(context, setting, value)
        except ValueError as error:
            print('AxisMeld:', error)
            hotbox_runtime.reload_settings(context)
    return update


class AXISMELD_Preferences(KeyConfigPreferences):
    bl_idname = PRESET_NAME

    use_file_overrides: BoolProperty(
        name='Use Studio and User Profile Files', default=True, update=_update_profile,
        description='Disable to use the public Maya baseline; Blender native keymap edits remain separate')

    hotbox_tap_seconds: FloatProperty(
        name='Hotbox Tap Threshold', default=0.4, min=0.1, max=1.0,
        description='Maximum trigger-key tap duration for single/quad view switching')

    hotbox_style: EnumProperty(
        name='Hotbox Style', items=(('rows', 'Zones and Menu Rows', ''),
                                    ('zones', 'Zones Only', ''),
                                    ('center', 'Center Zone Only', '')),
        default='rows', options={'SKIP_SAVE'}, update=_hotbox_update('style', 'hotbox_style'))
    hotbox_transparency: EnumProperty(
        name='Primary Hotbox Opacity', items=tuple((str(value), f'{100-value}%', '')
                                                for value in (100, 75, 50, 25, 0)),
        default='25', options={'SKIP_SAVE'},
        description='Opacity of primary backgrounds; Controls Transparency uses the inverse value; secondary stays opaque',
        update=_hotbox_update('transparency', 'hotbox_transparency'))
    hotbox_theme_background: BoolProperty(
        name='Use Theme Background', default=True, options={'SKIP_SAVE'},
        update=_appearance_update('theme_background'))
    hotbox_background: _appearance_color('background', 'Background Color')
    hotbox_brightness: IntProperty(
        name='Background Brightness', default=-13, min=-128, max=128, options={'SKIP_SAVE'},
        description='RGB offset for idle primary backgrounds; zero keeps the chosen color unchanged',
        update=_appearance_update('brightness'))
    hotbox_text: _appearance_color('text', 'Normal Text')
    hotbox_placeholder: _appearance_color('placeholder', 'Placeholder Text')
    hotbox_theme_hover_text: BoolProperty(
        name='Use Theme Hover Text', default=True, options={'SKIP_SAVE'},
        update=_appearance_update('theme_hover_text'))
    hotbox_hover_text: _appearance_color('hover_text', 'Hover Text')
    hotbox_row_common: BoolProperty(
        name='Show Common Menus', default=True, options={'SKIP_SAVE'},
        update=_hotbox_update('row.common'))
    hotbox_row_pane: BoolProperty(
        name='Show Pane Specific Menus', default=True, options={'SKIP_SAVE'},
        update=_hotbox_update('row.pane'))
    hotbox_row_modeling: BoolProperty(
        name='Show Modeling', default=True, options={'SKIP_SAVE'},
        update=_hotbox_update('row.modeling'))
    _center_items = tuple((value, label, '') for value, label in registered_menu_choices())
    hotbox_center_leftmouse: EnumProperty(
        name='Left Mouse Button', items=_center_items, default='views',
        options={'SKIP_SAVE'}, update=_hotbox_update('center.LEFTMOUSE',
                                                     'hotbox_center_leftmouse'))
    hotbox_center_middlemouse: EnumProperty(
        name='Middle Mouse Button', items=_center_items, default='views',
        options={'SKIP_SAVE'}, update=_hotbox_update('center.MIDDLEMOUSE',
                                                     'hotbox_center_middlemouse'))
    hotbox_center_rightmouse: EnumProperty(
        name='Right Mouse Button', items=_center_items, default='views',
        options={'SKIP_SAVE'}, update=_hotbox_update('center.RIGHTMOUSE',
                                                     'hotbox_center_rightmouse'))

    def draw(self, layout):
        layout.label(text='Maya 2026 - Modeling baseline (adapted)')
        layout.label(text='Click a transform axis, then middle-drag in empty viewport space')
        layout.prop(self, 'hotbox_tap_seconds')
        layout.prop(self, 'use_file_overrides')
        layout.operator('axismeld.reload_profile')
        layout.label(text=str(runtime.profile_directory() or 'No configuration directory'))
        layout.label(text=hotbox_runtime.settings_storage_note(bpy.context))
        layout.prop(self, 'hotbox_style')
        appearance = layout.box()
        appearance.label(text='Hotbox Appearance', icon='COLOR')
        appearance.use_property_split = True
        appearance.use_property_decorate = False
        appearance.prop(self, 'hotbox_transparency')
        appearance.prop(self, 'hotbox_theme_background')
        color = appearance.column()
        color.enabled = not self.hotbox_theme_background
        color.prop(self, 'hotbox_background')
        appearance.prop(self, 'hotbox_brightness', slider=True)
        appearance.prop(self, 'hotbox_text')
        appearance.prop(self, 'hotbox_placeholder')
        appearance.prop(self, 'hotbox_theme_hover_text')
        color = appearance.column()
        color.enabled = not self.hotbox_theme_hover_text
        color.prop(self, 'hotbox_hover_text')
        appearance.operator('axismeld.hotbox_reset_appearance', icon='LOOP_BACK')
        appearance.label(text='Next hotbox open applies changes; secondary menus use the opaque Blender theme')
        row = layout.row(align=True)
        row.prop(self, 'hotbox_row_common')
        row.prop(self, 'hotbox_row_pane')
        row.prop(self, 'hotbox_row_modeling')
        layout.prop(self, 'hotbox_center_leftmouse')
        layout.prop(self, 'hotbox_center_middlemouse')
        layout.prop(self, 'hotbox_center_rightmouse')
        layout.label(text='Hotbox menus and seven views are adapted; modeling/UV directories remain disabled')
        for message in runtime.diagnostics:
            layout.label(text=message, icon='ERROR')


classes = (AXISMELD_OT_command, AXISMELD_OT_reload_profile, AXISMELD_OT_hotbox_dispatch,
           AXISMELD_OT_hotbox_setting, AXISMELD_OT_hotbox_refresh, AXISMELD_OT_hotbox_reset_appearance)


def register():
    from bpy.utils import register_class
    register_class(AXISMELD_Preferences)
    WindowManager.axismeld_hotbox_snapshot = StringProperty(
        name='AxisMeld Hotbox Snapshot', options={'HIDDEN', 'SKIP_SAVE'})


def unregister():
    from bpy.utils import unregister_class
    unregister_class(AXISMELD_Preferences)
    del WindowManager.axismeld_hotbox_snapshot

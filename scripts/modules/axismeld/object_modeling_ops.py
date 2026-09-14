# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""One undo boundary for Object selection, Edit entry and persistent tool activation."""
import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from .object_modeling_hotbox import (OBJECT_TOOLS, OBJECT_ACTIONS, OBJECT_ACTION_COMMANDS,
                                    object_modeling_targets)


def _tool(context, mode):
    tool = context.workspace.tools.from_space_view3d_mode(mode, create=False)
    return tool.idname if tool else ''


def _set_tool(context, identifier):
    result = bpy.ops.wm.tool_set_by_id('EXEC_DEFAULT', False, name=identifier)
    if result != {'FINISHED'} or _tool(context, context.mode) != identifier:
        raise RuntimeError('Persistent tool activation did not complete')


def _restore_tool(context, identifier):
    # RNA exposes no removal for an absent mode slot; native mode entry initializes its default.
    identifier = identifier or 'builtin.select_box'
    if _tool(context, context.mode) != identifier:
        _set_tool(context, identifier)


class AXISMELD_OT_object_modeling_tool(Operator):
    bl_idname = 'axismeld.object_modeling_tool'
    bl_label = 'Object Modeling Tool'
    bl_options = {'INTERNAL', 'UNDO'}

    command: StringProperty(options={'HIDDEN'})
    target_uid: StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return bool(context.area and context.area.type == 'VIEW_3D' and context.region and
                    context.region.type == 'WINDOW' and context.mode == 'OBJECT')

    def execute(self, context):
        if self.command not in OBJECT_TOOLS:
            self.report({'WARNING'}, 'Unknown Object modeling tool')
            return {'CANCELLED'}
        targets = object_modeling_targets(context, self.target_uid)
        if not targets:
            self.report({'WARNING'}, 'Object modeling targets changed or are not eligible')
            return {'CANCELLED'}
        objects = tuple(context.view_layer.objects)
        selected = tuple(obj for obj in objects if obj.select_get(view_layer=context.view_layer))
        active = context.view_layer.objects.active
        select_mode = tuple(context.tool_settings.mesh_select_mode)
        old_tools = {mode: _tool(context, mode) for mode in ('OBJECT', 'EDIT_MESH')}
        meshes = {obj.data.session_uid: obj.data for obj in targets}
        components = {uid: tuple(tuple((element.select, element.hide) for element in elements)
                                 for elements in (mesh.vertices, mesh.edges, mesh.polygons))
                      for uid, mesh in meshes.items()}
        try:
            if self.target_uid:
                targets[0].select_set(True, view_layer=context.view_layer)
                context.view_layer.objects.active = targets[0]
            result = bpy.ops.object.mode_set('EXEC_DEFAULT', False, mode='EDIT')
            if result != {'FINISHED'} or context.mode != 'EDIT_MESH':
                raise RuntimeError('Mesh Edit Mode entry did not complete')
            editing = tuple(context.objects_in_mode)
            expected = {obj.session_uid for obj in targets}
            # Blender enters one representative per shared Mesh data, preserving other instances.
            if (not editing or context.active_object not in editing or
                    not {obj.session_uid for obj in editing} <= expected or
                    {obj.data.session_uid for obj in editing} != set(meshes)):
                raise RuntimeError('Native Edit Mode did not enter the complete target set')
            _set_tool(context, OBJECT_TOOLS[self.command])
        except Exception as error:
            rollback_errors = []
            # Restore both slots: leaving Edit alone does not reset its persistent tool.
            if context.mode == 'EDIT_MESH':
                try:
                    _restore_tool(context, old_tools['EDIT_MESH'])
                except Exception as rollback_error:
                    rollback_errors.append(str(rollback_error))
            if context.mode != 'OBJECT':
                try:
                    result = bpy.ops.object.mode_set('EXEC_DEFAULT', False, mode='OBJECT')
                    if result != {'FINISHED'} or context.mode != 'OBJECT':
                        raise RuntimeError('Could not restore Object Mode')
                except Exception as rollback_error:
                    rollback_errors.append(str(rollback_error))
            if context.mode == 'OBJECT':
                try:
                    for uid, mesh in meshes.items():
                        for elements, states in zip((mesh.vertices, mesh.edges, mesh.polygons), components[uid]):
                            if len(elements) != len(states):
                                raise RuntimeError('Tool activation unexpectedly changed mesh topology')
                            for element, (select, hide) in zip(elements, states):
                                element.select, element.hide = select, hide
                        mesh.update()
                    context.tool_settings.mesh_select_mode = select_mode
                    for obj in objects:
                        should_select = obj in selected
                        if obj.select_get(view_layer=context.view_layer) != should_select:
                            obj.select_set(should_select, view_layer=context.view_layer)
                    context.view_layer.objects.active = active
                    _restore_tool(context, old_tools['OBJECT'])
                except Exception as rollback_error:
                    rollback_errors.append(str(rollback_error))
            if rollback_errors:
                self.report({'ERROR'}, 'Object tool failed: ' + str(error) +
                            '; rollback incomplete: ' + '; '.join(rollback_errors))
            else:
                self.report({'WARNING'}, 'Object tool cancelled and restored: ' + str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


def _action_signature(context, target_uid):
    """Read-only identity token retained through the options dialog, never an executable payload."""
    targets = object_modeling_targets(context, target_uid)
    if not targets:
        return None
    selected = tuple(sorted((obj.session_uid, obj.data.session_uid) for obj in context.view_layer.objects
                            if obj.select_get(view_layer=context.view_layer)))
    active = context.view_layer.objects.active
    return (context.scene.session_uid, context.view_layer.as_pointer(), context.window.as_pointer(),
            context.area.as_pointer(), context.region.as_pointer(), context.mode,
            active.session_uid if active else 0, selected,
            tuple(sorted((obj.session_uid, obj.data.session_uid) for obj in targets)))


class AXISMELD_OT_object_modeling_action(Operator):
    bl_idname = 'axismeld.object_modeling_action'
    bl_label = 'Object Modeling Options'
    bl_options = {'INTERNAL', 'UNDO'}

    command: StringProperty(options={'HIDDEN'})
    target_uid: StringProperty(options={'HIDDEN'})
    smooth_levels: IntProperty(name='Subdivision Levels', default=1, min=1, max=6)
    mirror_axis: EnumProperty(name='Axis', items=[(axis, axis, '') for axis in ('X', 'Y', 'Z')], default='X')
    mirror_bisect: BoolProperty(name='Bisect', default=True)
    mirror_merge: BoolProperty(name='Merge', default=True)
    reduce_ratio: FloatProperty(name='Ratio', default=.5, min=.001, max=1.0, subtype='FACTOR')
    remesh_voxel_size: FloatProperty(name='Voxel Size', default=.1, min=.0001, soft_max=10, subtype='DISTANCE')

    @classmethod
    def poll(cls, context):
        return AXISMELD_OT_object_modeling_tool.poll(context)

    def invoke(self, context, _event):
        if self.command not in OBJECT_ACTION_COMMANDS:
            return {'CANCELLED'}
        self._target_signature = _action_signature(context, self.target_uid)
        if self._target_signature is None:
            self.report({'WARNING'}, 'Select an eligible Mesh or a valid pointer target')
            return {'CANCELLED'}
        # No selection, modifier or mode changes while the user reviews parameters.
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        targets = object_modeling_targets(context, self.target_uid)
        active = targets[0] if self.target_uid and targets else context.view_layer.objects.active
        self.layout.label(text='Active Mesh: ' + (active.name if active else 'Unavailable'))
        command = self.command.removesuffix('_options')
        fields = {
            'object.modeling_smooth': ('smooth_levels',),
            'object.modeling_mirror': ('mirror_axis', 'mirror_bisect', 'mirror_merge'),
            'object.modeling_reduce': ('reduce_ratio',),
            'object.modeling_remesh': ('remesh_voxel_size',),
        }.get(command, ())
        for field in fields:
            self.layout.prop(self, field)
        self.layout.label(text='Other selected objects remain unchanged')

    def execute(self, context):
        if self.command not in OBJECT_ACTION_COMMANDS:
            return {'CANCELLED'}
        signature = _action_signature(context, self.target_uid)
        if signature is None or signature != getattr(self, '_target_signature', signature):
            self.report({'WARNING'}, 'Object modeling context or target identity changed')
            return {'CANCELLED'}
        targets = object_modeling_targets(context, self.target_uid)
        target = targets[0] if self.target_uid else context.view_layer.objects.active
        if not target.data.polygons:
            self.report({'WARNING'}, 'Modifier requires Mesh faces')
            return {'CANCELLED'}
        command = self.command.removesuffix('_options')
        if command not in OBJECT_ACTIONS:
            return {'CANCELLED'}
        if command == 'object.modeling_smooth':
            properties = {'levels': self.smooth_levels, 'render_levels': self.smooth_levels}
        elif command == 'object.modeling_mirror':
            axes = tuple(axis == self.mirror_axis for axis in ('X', 'Y', 'Z'))
            properties = {'use_axis': axes, 'use_bisect_axis': tuple(self.mirror_bisect and axis for axis in axes),
                          'use_mirror_merge': self.mirror_merge, 'use_clip': self.mirror_merge}
        elif command == 'object.modeling_reduce':
            properties = {'ratio': self.reduce_ratio}
        else:
            properties = {'mode': 'VOXEL', 'voxel_size': self.remesh_voxel_size}
        selected = tuple(obj for obj in context.view_layer.objects if obj.select_get(view_layer=context.view_layer))
        old_active = context.view_layer.objects.active
        modifier = None
        try:
            if self.target_uid:
                target.select_set(True, view_layer=context.view_layer)
                context.view_layer.objects.active = target
            modifier = target.modifiers.new('AxisMeld ' + command.removeprefix('object.modeling_').title(),
                                            OBJECT_ACTIONS[command])
            for field, value in properties.items():
                setattr(modifier, field, value)
            from .modeling_mesh_ops import _evaluated_mesh
            _evaluated_mesh(context, target)
        except Exception as error:
            failures = []
            try:
                if modifier is not None:
                    target.modifiers.remove(modifier)
                context.view_layer.update()
            except Exception as rollback_error:
                failures.append(str(rollback_error))
            try:
                for obj in context.view_layer.objects:
                    state = obj in selected
                    if obj.select_get(view_layer=context.view_layer) != state:
                        obj.select_set(state, view_layer=context.view_layer)
                context.view_layer.objects.active = old_active
            except Exception as rollback_error:
                failures.append(str(rollback_error))
            self.report({'ERROR'} if failures else {'WARNING'}, str(error) +
                        ('; rollback incomplete: ' + '; '.join(failures) if failures else '; original state restored'))
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (AXISMELD_OT_object_modeling_tool, AXISMELD_OT_object_modeling_action)

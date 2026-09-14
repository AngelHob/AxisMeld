# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""One undo boundary for Object selection, Edit entry and persistent tool activation."""
import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from .object_modeling_hotbox import OBJECT_TOOLS, object_modeling_targets


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


classes = (AXISMELD_OT_object_modeling_tool,)

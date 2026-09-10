# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Blender operator adaptation; profile files cannot provide implementation code."""
import bpy

from .commands import COMMANDS

TOOLS = {'tool.select': 'builtin.select_box', 'transform.move': 'builtin.move',
         'transform.rotate': 'builtin.rotate', 'transform.scale': 'builtin.scale'}
COMPONENTS = {'selection.vertex_mode': 'VERT', 'selection.edge_mode': 'EDGE',
              'selection.face_mode': 'FACE'}
MODE_COMMANDS = {'selection.toggle_component', *COMPONENTS}
SELECTION_ACTIONS = {'selection.select_all', 'selection.grow', 'selection.shrink'}
VIEW_OPS = {'view.focus_selected': ('view_selected', {'use_all_regions': False}),
            'view.frame_all': ('view_all', {'center': False}),
            'view.orbit': ('rotate', {}), 'view.pan': ('move', {}),
            'view.dolly': ('zoom', {'use_axismeld_dolly': True})}
VIEW_ACTIONS = {'view.toggle_quad': 'TOGGLE_QUAD', 'view.perspective': 'PERSPECTIVE',
                'view.side': 'SIDE', 'view.front': 'FRONT', 'view.top': 'TOP',
                'view.left': 'LEFT', 'view.back': 'BACK', 'view.bottom': 'BOTTOM'}


def modeling_context(context):
    return bool(context.area and context.area.type == 'VIEW_3D' and
                context.region and context.region.type == 'WINDOW' and
                context.mode in {'OBJECT', 'EDIT_MESH'})


def _selection_operation(context, command):
    if command == 'selection.select_all':
        operation = bpy.ops.mesh.select_all if context.mode == 'EDIT_MESH' else bpy.ops.object.select_all
        return operation, {'action': 'SELECT'}
    if context.mode == 'EDIT_MESH' and command in {'selection.grow', 'selection.shrink'}:
        operation = bpy.ops.mesh.select_more if command == 'selection.grow' else bpy.ops.mesh.select_less
        return operation, {'use_face_step': True}
    return None


def available(context, command):
    if command not in COMMANDS:
        return False, 'Unknown AxisMeld command'
    if not modeling_context(context):
        return False, 'Requires a 3D View window in Object or mesh Edit Mode'
    if command in MODE_COMMANDS:
        obj = context.active_object
        if not (obj and obj.type == 'MESH' and obj.is_editable and obj.data.is_editable and
                obj.select_get() and obj.visible_get(view_layer=context.view_layer)):
            return False, 'Select a visible, editable mesh first'
    if command in SELECTION_ACTIONS:
        resolved = _selection_operation(context, command)
        if resolved is None:
            return False, 'Requires mesh Edit Mode'
        operation, _properties = resolved
        if not operation.poll():
            return False, 'Blender selection operator is unavailable in this context'
    if command in VIEW_OPS:
        operation = getattr(bpy.ops.view3d, VIEW_OPS[command][0], None)
        if operation is None or not operation.poll():
            return False, 'Blender view operator is unavailable in this context'
    if command in VIEW_ACTIONS and not bpy.ops.view3d.axismeld_view.poll():
        return False, 'AxisMeld view operator is unavailable in this context'
    if command == 'hotbox.open' and not bpy.ops.view3d.axismeld_hotbox.poll():
        return False, 'AxisMeld hotbox is unavailable in this context'
    return True, ''


def run(context, command, *, invoke=True):
    valid, reason = available(context, command)
    if not valid:
        raise ValueError(reason)
    if command in TOOLS:
        # Explicit selection is idempotent; repeated W must not cycle tools.
        return bpy.ops.wm.tool_set_by_id('EXEC_DEFAULT', name=TOOLS[command], cycle=False)
    if command == 'selection.toggle_component':
        mode = 'OBJECT' if context.mode == 'EDIT_MESH' else 'EDIT'
        return bpy.ops.object.mode_set('EXEC_DEFAULT', mode=mode)
    if command in COMPONENTS:
        if context.mode != 'EDIT_MESH':
            result = bpy.ops.object.mode_set('EXEC_DEFAULT', mode='EDIT')
            if result != {'FINISHED'}:
                return result
        expected = tuple(COMPONENTS[command] == value for value in ('VERT', 'EDGE', 'FACE'))
        if tuple(context.tool_settings.mesh_select_mode) == expected:
            return {'FINISHED'}
        return bpy.ops.mesh.select_mode('EXEC_DEFAULT', type=COMPONENTS[command],
                                        use_extend=False, use_expand=False)
    if command in SELECTION_ACTIONS:
        operation, properties = _selection_operation(context, command)
        # bpy.ops Python calls default their child-undo argument to false. Keep the generic
        # AxisMeld wrapper non-undoable while allowing the native selection operator to own it.
        return operation('EXEC_DEFAULT', True, **properties)
    if command in VIEW_OPS:
        name, properties = VIEW_OPS[command]
        return getattr(bpy.ops.view3d, name)('INVOKE_DEFAULT' if invoke else 'EXEC_DEFAULT', **properties)
    if command in VIEW_ACTIONS:
        return bpy.ops.view3d.axismeld_view('EXEC_DEFAULT', action=VIEW_ACTIONS[command])
    if command == 'hotbox.open':
        if not invoke:
            raise ValueError('hotbox.open requires a keyboard invoke event')
        preferences = context.window_manager.keyconfigs.active.preferences
        from . import hotbox_runtime
        return bpy.ops.view3d.axismeld_hotbox(
            'INVOKE_DEFAULT', tap_seconds=preferences.hotbox_tap_seconds,
            menu_json=hotbox_runtime.snapshot(context))
    if command in {'view.wireframe', 'view.shaded'}:
        context.space_data.shading.type = 'WIREFRAME' if command == 'view.wireframe' else 'SOLID'
        return {'FINISHED'}
    raise ValueError('No Blender adapter for this command')

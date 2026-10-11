# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Deferred, identity-bound Edit Mesh selection; menu previews never write BMesh."""
import bpy
import bmesh
from bpy.props import StringProperty, IntProperty, IntVectorProperty
from bpy.types import Operator
from .context_modeling_hotbox import MODEL_ROOTS, MODEL_MENU_COMMANDS


def resolve_target(context, object_uid, mesh_uid, domain, index, topology):
    if (context.mode != 'EDIT_MESH' or domain not in range(3) or index < 0 or
            tuple(context.tool_settings.mesh_select_mode) != tuple(i == domain for i in range(3))):
        return None
    target = None
    for obj in context.objects_in_mode_unique_data:
        if obj.type != 'MESH':
            continue
        bm = bmesh.from_edit_mesh(obj.data)
        # Preselection is exclusively the empty-selection workflow, across all editing meshes.
        if any(item.select for elements in (bm.verts, bm.edges, bm.faces) for item in elements):
            return None
        if str(obj.session_uid) != object_uid or str(obj.data.session_uid) != mesh_uid:
            continue
        if not (obj.is_editable and obj.data.is_editable and obj.visible_get(view_layer=context.view_layer)):
            return None
        if tuple(len(elements) for elements in (bm.verts, bm.edges, bm.faces)) != tuple(topology):
            return None
        elements = (bm.verts, bm.edges, bm.faces)[domain]
        elements.ensure_lookup_table()
        if index >= len(elements) or elements[index].hide:
            return None
        target = (obj, bm, elements[index], domain)
    return target


def preview(target):
    _obj, _bm, element, domain = target
    counts = ((1, 0, 0) if domain == 0 else (2, 1, 0) if domain == 1
              else (len(element.verts), len(element.edges), 1))
    return {'root': MODEL_ROOTS[domain], 'counts': counts}


def _geometry_signature(bm):
    for elements in (bm.verts, bm.edges, bm.faces):
        elements.index_update()
    return (tuple((tuple(v.co), v.hide) for v in bm.verts),
            tuple((tuple(v.index for v in e.verts), e.hide) for e in bm.edges),
            tuple((tuple(v.index for v in f.verts), f.hide) for f in bm.faces))


def execute_target(context, target, command):
    from . import adapter
    from .modeling_registry import SPECS
    obj, bm, element, domain = target
    geometry = _geometry_signature(bm)
    identity = (obj.session_uid, obj.data.session_uid)
    old_history = tuple((0 if isinstance(item, bmesh.types.BMVert) else
                         1 if isinstance(item, bmesh.types.BMEdge) else 2, item.index)
                        for item in bm.select_history)
    old_active = bm.faces.active.index if bm.faces.active else -1
    # Snapshot even hidden flags: rejecting a selection is cheaper than repairing one.
    selected = tuple(tuple(item.select for item in elements) for elements in (bm.verts, bm.edges, bm.faces))
    try:
        element.select_set(True)
        bm.select_flush_mode()
        bm.select_history.add(element)
        if domain == 2:
            bm.faces.active = element
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        result = adapter.run(context, command, invoke=True)
        if result in ({'FINISHED'}, {'RUNNING_MODAL'}):
            # The called native operator owns geometry undo, including captured selection.
            # Tool/state-only calls have no native undo; store their selection commit once.
            call = adapter.modeling_adapter.resolve(context, command) if command in SPECS else None
            if result == {'FINISHED'} and (call is None or not call.undo):
                bpy.ops.ed.undo_push(message='AxisMeld Component Target')
            return result
    except (RuntimeError, ValueError):
        result = {'CANCELLED'}
    # Native cancellation may replace BMesh even during invoke. Reacquire by persistent
    # identity and compare value-only geometry before restoring the original selection.
    # Running children use the native completion hook; no Python observer retains BMesh.
    if context.mode != 'EDIT_MESH':
        return result
    obj = next((item for item in context.objects_in_mode_unique_data
                if (item.session_uid, item.data.session_uid) == identity), None)
    if obj is None:
        return result
    bm = bmesh.from_edit_mesh(obj.data)
    if _geometry_signature(bm) == geometry:
        for items, flags in zip((bm.verts, bm.edges, bm.faces), selected):
            for item, flag in zip(items, flags):
                item.select = flag
        bm.select_history.clear()
        for elements in (bm.verts, bm.edges, bm.faces):
            elements.ensure_lookup_table()
        for domain, index in old_history:
            bm.select_history.add((bm.verts, bm.edges, bm.faces)[domain][index])
        bm.faces.active = bm.faces[old_active] if old_active >= 0 else None
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    return result


class AXISMELD_OT_edit_preselection(Operator):
    bl_idname = 'axismeld.edit_preselection'
    bl_label = 'Captured Component Action'
    bl_options = {'INTERNAL'}
    object_uid: StringProperty(options={'HIDDEN'})
    mesh_uid: StringProperty(options={'HIDDEN'})
    domain: IntProperty(options={'HIDDEN'}, min=0, max=2)
    index: IntProperty(options={'HIDDEN'}, min=0)
    topology: IntVectorProperty(options={'HIDDEN'}, size=3, min=0)
    command: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        from . import hotbox_runtime
        from .context_modeling_hotbox import modeling_menus
        from .hotbox_catalog import _node
        target = resolve_target(context, self.object_uid, self.mesh_uid, self.domain, self.index, self.topology)
        if target is None:
            return {'CANCELLED'}
        if not self.command:
            context.window_manager.axismeld_hotbox_snapshot = hotbox_runtime.snapshot(context, preselection=preview(target))
            return {'FINISHED'}
        allowed = set()
        pending = [modeling_menus(_node)[self.domain]]
        while pending:
            node = pending.pop()
            pending.extend(node['children'])
            if node['kind'] == 'command':
                allowed.add(node['command'])
        allowed.update(command for identifier, command in MODEL_MENU_COMMANDS.items()
                       if identifier.startswith(MODEL_ROOTS[self.domain] + '_menu.'))
        if self.command not in allowed:
            return {'CANCELLED'}
        result = execute_target(context, target, self.command)
        return {'FINISHED'} if 'RUNNING_MODAL' in result else result


classes = (AXISMELD_OT_edit_preselection,)

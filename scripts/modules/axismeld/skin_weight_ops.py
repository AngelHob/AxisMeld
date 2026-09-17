# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded Skin cleanup on native deform data, without mode/selection mutation."""
import bpy
import bmesh
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty

from .skin_weight_plan import plan_weights


def context_error(context):
    """Cheap, read-only menu guard. Per-vertex validation happens before writing."""
    if getattr(getattr(context, 'area', None), 'type', '') != 'VIEW_3D':
        return 'Use the source 3D View'
    if context.mode not in {'OBJECT', 'EDIT_MESH', 'PAINT_WEIGHT'}:
        return 'Use Object, Mesh Edit or Weight Paint mode'
    obj = context.active_object
    if obj is None or obj.type != 'MESH' or not obj.select_get():
        return 'Select an active mesh'
    if not context.scene.is_editable or not obj.is_editable or not obj.data.is_editable:
        return 'The mesh and object must be editable'
    if obj.library or obj.data.library or obj.override_library or obj.data.override_library:
        return 'Linked and overridden meshes are not supported by this adapter'
    if obj.data.users - int(obj.data.use_fake_user) != 1:
        return 'Shared mesh data is not supported; make it single-user explicitly'
    if context.mode == 'EDIT_MESH' and len(context.objects_in_mode) != 1:
        return 'Multi-object Edit mode is not supported by this adapter'
    modifiers = [m for m in obj.modifiers if m.type == 'ARMATURE']
    if len(modifiers) != 1:
        return 'Exactly one Armature modifier is required, including disabled modifiers'
    mod = modifiers[0]
    if not mod.object or mod.object.type != 'ARMATURE' or not mod.show_viewport or not mod.use_vertex_groups:
        return 'Enable a valid Armature modifier with vertex group deformation'
    names = {b.name for b in mod.object.data.bones if b.use_deform}
    if not any(g.name in names for g in obj.vertex_groups):
        return 'No vertex groups match this armature\'s deform bones'
    return ''


def scope_label(context):
    if context.mode == 'EDIT_MESH':
        return 'Selected visible vertices of the active mesh'
    mesh = context.active_object.data
    if context.mode == 'PAINT_WEIGHT':
        if mesh.use_paint_mask_vertex:
            return 'Vertex mask: selected visible vertices'
        if mesh.use_paint_mask:
            return 'Face mask: visible vertices of selected visible faces'
    return 'All visible vertices of the active mesh'


def _snapshot(context):
    obj = context.active_object
    if context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        layer = bm.verts.layers.deform.active
        vertices = {v.index: dict(v[layer]) if layer else {}
                    for v in bm.verts if v.select and not v.hide}
        return vertices, (bm, layer)
    mesh = obj.data
    selected = None
    if context.mode == 'PAINT_WEIGHT':
        if mesh.use_paint_mask_vertex:
            selected = {v.index for v in mesh.vertices if v.select}
        elif mesh.use_paint_mask:
            selected = {i for face in mesh.polygons if face.select and not face.hide for i in face.vertices}
    vertices = {v.index: {g.group: g.weight for g in v.groups} for v in mesh.vertices
                if not v.hide and (selected is None or v.index in selected)}
    return vertices, None


def _write(obj, edit_data, changes):
    if edit_data:
        bm, layer = edit_data
        # A nonempty plan requires existing memberships; never manufacture a layer.
        for vertex, groups in changes.items():
            weights = bm.verts[vertex][layer]
            for group, value in groups.items():
                if value is None:
                    if group in weights: del weights[group]
                else:
                    weights[group] = value
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    else:
        for vertex, groups in changes.items():
            for group, value in groups.items():
                target = obj.vertex_groups[group]
                if value is None:
                    target.remove([vertex])
                else:
                    target.add([vertex], value, 'REPLACE')
        obj.data.update()
    obj.update_tag(refresh={'DATA'})


class _SkinWeightOperation:
    bl_options = {'REGISTER', 'UNDO'}
    show_options: BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        reason = context_error(context)
        if reason:
            cls.poll_message_set(reason)
        return not reason

    def invoke(self, context, event):
        if self.show_options:
            self._dialog_target = context.active_object.as_pointer()
            return context.window_manager.invoke_props_dialog(self, width=460)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        reason = context_error(context)
        if reason:
            layout.label(text=reason, icon='ERROR')
            return
        layout.label(text='Active Mesh: ' + context.active_object.name, icon='MESH_DATA')
        mod = next(m for m in context.active_object.modifiers if m.type == 'ARMATURE')
        layout.label(text='Armature: ' + mod.object.name, icon='ARMATURE_DATA')
        layout.label(text=scope_label(context))
        layout.label(text='Deform bone groups only; group locks are always preserved')
        if self.operation == 'NORMALIZE':
            layout.prop(self, 'lock_active')
            layout.label(text='One-time operation; zero totals remain unassigned')
        else:
            layout.prop(self, 'threshold')
            layout.prop(self, 'keep_strongest')
            layout.prop(self, 'normalize_after')
            layout.label(text='Strictly below threshold; equal weights are retained')

    def execute(self, context):
        reason = context_error(context)
        if not reason and getattr(self, '_dialog_target', context.active_object.as_pointer()) != context.active_object.as_pointer():
            reason = 'The active mesh changed while Options was open'
        if reason:
            self.report({'WARNING'}, reason)
            return {'CANCELLED'}
        # F9 restores the undo state and can replace ID pointers. This guard is
        # only for the interval between opening Options and its first confirm.
        if hasattr(self, '_dialog_target'):
            del self._dialog_target
        obj = context.active_object
        mod = next(m for m in obj.modifiers if m.type == 'ARMATURE')
        names = {b.name for b in mod.object.data.bones if b.use_deform}
        groups = {g.index for g in obj.vertex_groups if g.name in names}
        locked = {g.index for g in obj.vertex_groups if g.lock_weight}
        if self.operation == 'NORMALIZE' and self.lock_active:
            locked.add(obj.vertex_groups.active_index)
        before, edit_data = _snapshot(context)
        if not before:
            self.report({'WARNING'}, 'No visible vertices in the current selection scope')
            return {'CANCELLED'}
        try:
            plan = plan_weights(before, groups, locked, operation=self.operation,
                **(dict(threshold=self.threshold, keep_strongest=self.keep_strongest,
                        normalize_after=self.normalize_after) if self.operation == 'PRUNE' else {}))
        except ValueError as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        if not plan['changes']:
            self.report({'INFO'}, 'No weights changed; zero-total vertices: ' + str(plan['zero_vertices']))
            # Adjust Last Operation has already restored the pre-operation
            # state. CANCELLED would make Blender replay the old changed state.
            if self.options.is_repeat and not self.options.is_repeat_last:
                return {'FINISHED'}
            return {'CANCELLED'}
        try:
            _write(obj, edit_data, plan['changes'])
        except (RuntimeError, ValueError) as error:
            rollback = {v: {g: before[v].get(g) for g in changed}
                        for v, changed in plan['changes'].items()}
            _write(obj, edit_data, rollback)
            self.report({'ERROR'}, 'Weight update rolled back: ' + str(error))
            return {'CANCELLED'}
        self.report({'INFO'}, 'Changed vertices: %d; zero-total vertices: %d' %
                    (plan['changed_vertices'], plan['zero_vertices']))
        return {'FINISHED'}


class AXISMELD_OT_skin_normalize_weights(_SkinWeightOperation, Operator):
    bl_idname = 'axismeld.skin_normalize_weights'
    bl_label = 'Normalize Weights'
    bl_description = ('Normalize active mesh deform weights once, preserving locked and non-bone groups; '
                      'does not enable a persistent Maya normalization mode')
    operation = 'NORMALIZE'
    lock_active: BoolProperty(name='Lock Active', default=False,
        description='Additionally preserve the active group for this operation only')


class AXISMELD_OT_skin_prune_weights(_SkinWeightOperation, Operator):
    bl_idname = 'axismeld.skin_prune_weights'
    bl_label = 'Prune Small Weights'
    bl_description = ('Remove active mesh unlocked deform weights strictly below the threshold; '
                      'preserve non-bone groups and the current vertex selection scope')
    operation = 'PRUNE'
    threshold: FloatProperty(name='Prune Below', default=.01, min=0, max=1, precision=4,
        description='Remove weights strictly below this value; equal weights remain')
    keep_strongest: BoolProperty(name='Keep Strongest', default=True,
        description='Keep the strongest positive deform influence if pruning would clear the vertex')
    normalize_after: BoolProperty(name='Normalize After', default=True,
        description='Normalize remaining weights once, preserving locked weights; zero totals stay zero')


classes = (AXISMELD_OT_skin_normalize_weights, AXISMELD_OT_skin_prune_weights)

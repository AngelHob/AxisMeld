# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Resolve fixed modeling calls, preserving native modal handlers and undo ownership."""
import bpy
from .modeling_registry import SPECS

MODES = frozenset({'OBJECT', 'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_LATTICE'})


def menu_context(context):
    return bool(context.area and context.area.type == 'VIEW_3D' and
                context.region and context.region.type == 'WINDOW' and context.mode in MODES)


def resolve(context, command):
    spec = SPECS.get(command)
    return next((call for call in spec.calls if context.mode in call.modes), None) if spec else None


def operation(call):
    namespace, name = call.operator.split('.')
    return getattr(getattr(bpy.ops, namespace), name)


def _eligible(context):
    return [obj for obj in context.selected_objects if obj.is_editable and
            (obj.data is None or obj.data.is_editable) and
            obj.visible_get(view_layer=context.view_layer)]


def _cached(cache, key, factory):
    if cache is None:
        return factory()
    if key not in cache:
        cache[key] = factory()
    return cache[key]


def _mesh_selection(context):
    import bmesh
    meshes = [bmesh.from_edit_mesh(obj.data) for obj in context.objects_in_mode_unique_data
              if obj.type == 'MESH' and obj.is_editable and obj.data.is_editable]
    per_mesh = [tuple(sum(item.select and not item.hide for item in getattr(bm, domain))
                      for domain in ('verts', 'edges', 'faces')) for bm in meshes]
    return per_mesh


def _requirement(context, requirement, cache=None):
    if not requirement:
        return True
    active = context.active_object
    selected = _cached(cache, 'eligible', lambda: _eligible(context))
    if requirement == 'object':
        return active in selected
    if requirement == 'mesh':
        return active in selected and active.type == 'MESH'
    if requirement == 'two_objects':
        return active in selected and len(selected) >= 2
    if requirement == 'two_mesh':
        return active in selected and active.type == 'MESH' and sum(o.type == 'MESH' for o in selected) >= 2
    if context.mode == 'EDIT_MESH':
        import bmesh
        per_mesh = _cached(cache, 'mesh_selection', lambda: _mesh_selection(context))
        counts = tuple(sum(values[index] for values in per_mesh) for index in range(3))
        if requirement == 'selection':
            return any(counts)
        if requirement in {'vertices', 'edges', 'faces', 'two_vertices', 'two_edges'}:
            domain = {'vertices': 0, 'edges': 1, 'faces': 2, 'two_vertices': 0, 'two_edges': 1}[requirement]
            minimum = 2 if requirement.startswith('two_') else 1
            return any(values[domain] >= minimum for values in per_mesh)
        if requirement == 'merge_history':
            bm = bmesh.from_edit_mesh(active.data)
            vertex = bm.select_history.active
            return (sum(v.select and not v.hide for v in bm.verts) >= 2 and
                    isinstance(vertex, bmesh.types.BMVert) and vertex.select and not vertex.hide)
        if requirement == 'face_projection':
            return counts[2] > 0 and any(obj.mode != 'EDIT' and obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}
                                        for obj in selected)
    if requirement == 'selection':
        return bool(selected)
    raise ValueError('Unknown modeling requirement: ' + requirement)


def available(context, command, *, cache=None):
    """Optional cache belongs to one read-only catalog construction, never dispatch."""
    if not menu_context(context):
        return False, 'Requires a supported modeling mode in a 3D View window'
    call = resolve(context, command)
    if call is None:
        return False, 'Unavailable in the current object or component mode'
    if not context.scene or not context.scene.is_editable:
        return False, 'Requires an editable scene'
    spec = SPECS[command]
    if not _requirement(context, spec.requires, cache):
        return False, 'Select eligible editable targets or components for this operation'
    for module in _modules():
        predicate = getattr(module, 'COMMAND_POLLS', {}).get(command)
        if predicate is not None and not _cached(cache, ('predicate', predicate), lambda: predicate(context)):
            return False, 'Select the required editable source and target objects'
    try:
        if not operation(call).poll():
            return False, 'Native operation requires a valid target or selection'
    except (AttributeError, RuntimeError):
        return False, 'Native operation is unavailable'
    return True, ''


def _modules():
    from . import modeling_common_ops, modeling_mesh_ops, modeling_shapes_ops
    return modeling_common_ops, modeling_mesh_ops, modeling_shapes_ops


def command_state(context, command):
    for module in _modules():
        reader = getattr(module, 'command_state', None)
        if reader is not None:
            state = reader(context, command)
            if state is not None:
                return state
    return None


def run(context, command, *, invoke=True):
    valid, reason = available(context, command)
    if not valid:
        raise ValueError(reason)
    call = resolve(context, command)
    # A running child owns its modal handler. Never turn its start into successful Recent history.
    return operation(call)('INVOKE_DEFAULT' if invoke and call.invoke else 'EXEC_DEFAULT',
                           call.undo, **dict(call.kwargs))

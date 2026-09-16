# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Original Blender Rigging menus, exposed through guarded native entry points."""
import bpy
from bpy.types import Menu
from axismeld.rigging_workspace_catalog import ENTRIES


class _RiggingIconLayout:
    """Fill only missing native row icons without replacing a menu's real host."""

    def __init__(self, layout, icon):
        object.__setattr__(self, '_layout', layout)
        object.__setattr__(self, '_icon', icon)

    def __getattr__(self, name):
        value = getattr(self._layout, name)
        if name in {'row', 'column', 'split', 'box', 'column_flow', 'grid_flow'}:
            def child(*args, **kwargs):
                return _RiggingIconLayout(value(*args, **kwargs), self._icon)
            return child
        if name in {'operator', 'menu', 'operator_menu_enum', 'prop_menu_enum'}:
            def with_icon(*args, **kwargs):
                if 'icon' not in kwargs and not kwargs.get('icon_value', 0):
                    kwargs['icon'] = self._icon
                return value(*args, **kwargs)
            return with_icon
        # operator_enum has no icon parameter; its generated rows retain RNA icons.
        return value

    def __setattr__(self, name, value):
        setattr(self._layout, name, value)


def rigging_icon_layout(layout, context, fallback):
    """Keep all other workspaces identical, including their original UILayout."""
    from bl_ui import space_axismeld_menubar
    if not space_axismeld_menubar.rigging_workspace(context):
        return layout
    return _RiggingIconLayout(layout, fallback)


def _viewport(context):
    return (getattr(getattr(context, 'area', None), 'type', '') == 'VIEW_3D' and
            bool(getattr(getattr(context, 'scene', None), 'is_editable', False)))


def _editable_object(obj, kinds):
    return (obj is not None and getattr(obj, 'type', '') in kinds and
            bool(getattr(obj, 'is_editable', False)))


def _editable(obj, kinds):
    return (_editable_object(obj, kinds) and
            bool(getattr(getattr(obj, 'data', None), 'is_editable', False)))


def _poll(identifier):
    namespace, name = identifier.split('.')
    try:
        return getattr(getattr(bpy.ops, namespace), name).poll()
    except (AttributeError, RuntimeError):
        return False


def _bind_context(context):
    if not _viewport(context) or getattr(context, 'mode', '') != 'OBJECT':
        return False
    active = getattr(context, 'active_object', None)
    selected = tuple(getattr(context, 'selected_objects', ()))
    if not _editable_object(active, {'ARMATURE'}) or active not in selected:
        return False
    targets = [obj for obj in selected if obj != active]
    # parent_set.poll only checks for an active object. Do not allow an unrelated
    # selected object to be silently reparented along with the intended meshes.
    return bool(targets) and all(_editable(obj, {'MESH'}) for obj in targets) and _poll('object.parent_set')


class AXISMELD_MT_rigging_armature_deform(Menu):
    bl_label = 'Armature Deform'

    @classmethod
    def poll(cls, context):
        return _bind_context(context)

    def draw(self, context):
        for kind, label, icon in (
            ('ARMATURE', 'Armature Deform', 'MOD_ARMATURE'),
            ('ARMATURE_NAME', 'With Empty Groups', 'GROUP_VERTEX'),
            ('ARMATURE_AUTO', 'With Automatic Weights', 'WPAINT_HLT'),
            ('ARMATURE_ENVELOPE', 'With Envelope Weights', 'BONE_DATA'),
        ):
            row = self.layout.row()
            row.enabled = _bind_context(context)
            row.operator_context = 'INVOKE_REGION_WIN'
            row.operator('object.parent_set', text=label, icon=icon).type = kind


def draw_entry(layout, context, key):
    """Draw one row; menus use their actual registered host, never copied draw code.

    Window menu navigation outside a 3D View remains disabled. Opening a menu
    never searches another editor or changes active objects, selection or mode.
    """
    entry = ENTRIES[key]
    active = getattr(context, 'active_object', None)
    mode = getattr(context, 'mode', '')
    available = _viewport(context)
    host = None
    if key == 'skeleton.create':
        host = 'VIEW3D_MT_armature_add'
        available = available and mode == 'OBJECT' and _poll('object.armature_add')
    elif key == 'skeleton.edit_bones':
        host = 'VIEW3D_MT_edit_armature'
        available = (available and mode == 'EDIT_ARMATURE' and _editable(active, {'ARMATURE'}) and
                     getattr(context, 'edit_object', None) == active)
    elif key in {'skeleton.pose', 'skeleton.ik'}:
        host = 'VIEW3D_MT_pose' if key == 'skeleton.pose' else 'VIEW3D_MT_pose_ik'
        available = available and mode == 'POSE' and _editable_object(active, {'ARMATURE'})
    elif key == 'skin.bind':
        host = AXISMELD_MT_rigging_armature_deform.__name__
        available = _bind_context(context)
    elif key == 'skin.weight_paint':
        available = (available and mode in {'OBJECT', 'PAINT_WEIGHT'} and _editable(active, {'MESH'}) and
                     _poll('paint.weight_paint_toggle'))
    elif key == 'skin.weights':
        host = 'VIEW3D_MT_edit_mesh_weights' if mode == 'EDIT_MESH' else 'VIEW3D_MT_paint_weight'
        available = available and mode in {'EDIT_MESH', 'PAINT_WEIGHT'} and _editable(active, {'MESH'})
    elif key in {'skin.vertex_groups', 'skin.group_specials'}:
        host = 'VIEW3D_MT_vertex_group' if key == 'skin.vertex_groups' else 'MESH_MT_vertex_group_context_menu'
        available = (available and mode in {'OBJECT', 'EDIT_MESH', 'EDIT_LATTICE', 'PAINT_WEIGHT'} and
                     _editable(active, {'MESH', 'LATTICE'}))
    else:
        raise ValueError('Unknown native Rigging entry: ' + key)

    row = layout.row()
    row.enabled = available
    if not available:
        # Disabled menu rows may still preview their subtree. Native menu draws
        # expect their mode/object context, so do not create an unavailable host.
        row.label(text=entry['label'], icon=entry['icon'])
    elif host:
        row.menu(host, text=entry['label'], icon=entry['icon'])
    else:
        row.operator_context = 'INVOKE_REGION_WIN'
        row.operator('paint.weight_paint_toggle', text=entry['label'], icon=entry['icon'])


classes = (AXISMELD_MT_rigging_armature_deform,)

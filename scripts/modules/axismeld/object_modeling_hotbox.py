# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed Object tool menu and read-only full view-layer selection eligibility."""
from types import MappingProxyType

OBJECT_ROOT = 'context.modeling_object'
OBJECT_TOOLS = MappingProxyType({
    'tool.object_mesh_poly_build': 'builtin.poly_build',
    'tool.object_mesh_loopcut': 'builtin.loop_cut',
    'tool.object_mesh_knife': 'builtin.knife',
})


def object_modeling_targets(context, target_uid=''):
    """Empty UID means existing selection; explicit UID requires completely empty selection."""
    if not (context.area and context.area.type == 'VIEW_3D' and context.region and
            context.region.type == 'WINDOW' and context.mode == 'OBJECT' and
            context.scene and context.scene.is_editable):
        return ()
    objects = tuple(context.view_layer.objects)
    selectable = tuple(context.selectable_objects)
    selected = tuple(obj for obj in objects if obj.select_get(view_layer=context.view_layer))
    if target_uid:
        if (not isinstance(target_uid, str) or not target_uid.isascii() or not target_uid.isdecimal() or
                not 0 < int(target_uid) <= 0xffffffff or selected):
            return ()
        targets = tuple(obj for obj in objects if obj.session_uid == int(target_uid))
        if len(targets) != 1:
            return ()
    else:
        if not selected or context.active_object not in selected:
            return ()
        targets = selected
    for obj in targets:
        if not (obj.type == 'MESH' and obj.mode == 'OBJECT' and obj.is_editable and
                obj.data and obj.data.is_editable and not obj.override_library and
                not obj.data.override_library and not obj.hide_select and obj in selectable and
                obj.visible_get(view_layer=context.view_layer, viewport=context.space_data)):
            return ()
    return targets


def object_modeling_menu(node):
    entries = (
        ('weld', 'N', 'Target Weld', '', 'M2d-P04.TargetWeld: Full target weld tool deferred'),
        ('fill', 'NE', 'Fill Holes', '', 'M2d-P02.ObjectFillHoles: Whole-mesh transaction deferred'),
        ('append', 'E', 'Poly Build (Append Adaptation)', 'tool.object_mesh_poly_build', ''),
        ('normals', 'SE', 'Soften / Harden', '', 'M2d-P05.ObjectNormals: Whole-mesh sharpness deferred'),
        ('extrude', 'S', 'Extrude', '', 'M2d-P02.ObjectExtrude: Whole-mesh extrusion deferred'),
        ('loopcut', 'SW', 'Loop Cut Tool', 'tool.object_mesh_loopcut', ''),
        ('knife', 'W', 'Knife (Multi-Cut Adaptation)', 'tool.object_mesh_knife', ''),
        ('sculpt', 'NW', 'Sculpt', '', 'M2d-P04.ObjectSculpt: Sculpt context transaction deferred'),
    )
    return node(OBJECT_ROOT, 'menu', 'Object Modeling', presentation='radial', children=tuple(
        node(OBJECT_ROOT + '.' + suffix, 'command' if command else 'disabled', label,
             command=command, direction=direction, enabled=bool(command), reason=reason)
        for suffix, direction, label, command, reason in entries))

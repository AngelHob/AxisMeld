# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed Object tool menu and read-only full view-layer selection eligibility."""
from types import MappingProxyType

OBJECT_ROOT = 'context.modeling_object'
OBJECT_MENU = 'context.modeling_object_menu'
OBJECT_TOOLS = MappingProxyType({
    'tool.object_mesh_poly_build': 'builtin.poly_build',
    'tool.object_mesh_loopcut': 'builtin.loop_cut',
    'tool.object_mesh_knife': 'builtin.knife',
    'tool.object_mesh_offset_loop': 'builtin.offset_edge_loop_cut',
})
OBJECT_ACTIONS = MappingProxyType({
    'object.modeling_smooth': 'SUBSURF',
    'object.modeling_mirror': 'MIRROR',
    'object.modeling_reduce': 'DECIMATE',
    'object.modeling_remesh': 'REMESH',
})
OBJECT_ACTION_COMMANDS = frozenset((*OBJECT_ACTIONS, *(command + '_options' for command in OBJECT_ACTIONS)))
OBJECT_BOUND_COMMANDS = frozenset((*OBJECT_TOOLS, *OBJECT_ACTION_COMMANDS))
OBJECT_MENU_COMMANDS = MappingProxyType({
    OBJECT_MENU + '.offset_loop': 'tool.object_mesh_offset_loop',
    **{OBJECT_MENU + '.' + suffix: 'object.modeling_' + suffix for suffix in ('smooth', 'mirror', 'reduce', 'remesh')},
    OBJECT_MENU + '.combine': 'mesh.combine_objects',
    OBJECT_MENU + '.quad_draw': 'tool.object_mesh_poly_build',
    **{OBJECT_MENU + '.booleans.' + suffix: 'mesh.boolean_' + suffix
       for suffix in ('union', 'difference', 'difference_reverse', 'intersection')},
    OBJECT_MENU + '.polygon_display.backface_culling': 'display.backface_culling',
})
OBJECT_OPTION_COMMANDS = MappingProxyType({
    **{OBJECT_MENU + '.' + suffix + '.options': 'object.modeling_' + suffix + '_options'
       for suffix in ('smooth', 'mirror', 'reduce', 'remesh')},
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
        ('weld', 'N', 'Target Weld Tool', '', 'M2d-P04.TargetWeld: Full target weld tool deferred'),
        ('fill', 'NE', 'Fill Holes', '', 'M2d-P02.ObjectFillHoles: Whole-mesh transaction deferred'),
        ('append', 'E', 'Append to Polygon Tool', 'tool.object_mesh_poly_build', 'Blender Poly Build; Maya Append behavior is not reproduced exactly'),
        ('normals', 'SE', 'Soften/Harden Edges', '', 'M2d-P05.ObjectNormals: Whole-mesh sharpness deferred'),
        ('extrude', 'S', 'Extrude', '', 'M2d-P02.ObjectExtrude: Whole-mesh extrusion deferred'),
        ('loopcut', 'SW', 'Insert Edge Loop Tool', 'tool.object_mesh_loopcut', 'Blender persistent Loop Cut tool'),
        ('knife', 'W', 'Multi-Cut', 'tool.object_mesh_knife', 'Blender persistent Knife tool; Maya Multi-Cut behavior differs'),
        ('sculpt', 'NW', 'Sculpt Tool', '', 'M2d-P04.ObjectSculpt: Sculpt context transaction deferred'),
    )
    return node(OBJECT_ROOT, 'menu', 'Object Modeling', presentation='radial', children=tuple(
        node(OBJECT_ROOT + '.' + suffix, 'command' if command else 'disabled', label,
             command=command, direction=direction, enabled=bool(command), reason=reason)
        for suffix, direction, label, command, reason in entries))


def object_modeling_companion(node):
    """Maya Object menu's 22 nonseparator rows, with independent option cells."""
    def row(suffix, label, *, options=False, reason=''):
        identifier = OBJECT_MENU + '.' + suffix
        command = OBJECT_MENU_COMMANDS.get(identifier, '')
        reason = reason or ('M2d-P02.' + suffix + ': Object adaptation not implemented')
        children = ()
        if options:
            option_id = identifier + '.options'
            option_command = OBJECT_OPTION_COMMANDS.get(option_id, '')
            children = (node(option_id, 'command' if option_command else 'disabled', 'Options',
                             command=option_command, enabled=bool(option_command),
                             reason=('Configure the active Mesh operation; confirmation creates one undo step' if option_command else
                                     'M2d-P02.Retopologize: Target-pinned QuadriFlow confirmation not implemented; native entry remains in Mesh menu' if suffix == 'retopologize' else
                                     'M2d-P02.' + suffix + '.Options: Dedicated parameters not implemented')),)
        return node(identifier, 'command' if command else 'disabled', label, command=command,
                    enabled=bool(command), reason=reason, children=children)

    def sep(suffix):
        return node(OBJECT_MENU + '.separator_' + suffix, 'separator', '', enabled=False)

    def directory(suffix, label, children):
        return node(OBJECT_MENU + '.' + suffix, 'menu', label, children=children, presentation='list')

    mapping = directory('mapping', 'Mapping', (
        *(row('mapping.planar_' + axis, 'Planar Map ' + axis.upper(), reason='M2d-UV.Planar' + axis.upper() + ': UV work is postponed') for axis in 'xyz'),
        row('mapping.planar', 'Planar Map', options=True), sep('mapping_planar'),
        row('mapping.cylindrical', 'Cylindrical Map', options=True),
        row('mapping.spherical', 'Spherical Map', options=True), sep('mapping_spherical'),
        row('mapping.automatic', 'Automatic Map', options=True),
        row('mapping.camera', 'Camera Based Map', options=True),
        row('mapping.normal', 'Normal Based Map', options=True),
    ))
    booleans = directory('booleans', 'Booleans', tuple(
        row('booleans.' + suffix, label, options=True,
            reason=('Exact Boolean modifier; requires exactly two selected Meshes; originals remain' if suffix in
                    ('union', 'difference', 'difference_reverse', 'intersection') else
                    'M3-P-MESH.' + suffix + ': Maya Boolean mode not implemented'))
        for suffix, label in (('union', 'Union'), ('difference', 'Difference A - B'),
                              ('difference_reverse', 'Difference B - A'), ('intersection', 'Intersection'),
                              ('slice', 'Slice'), ('hole_punch', 'Hole Punch'),
                              ('cut_out', 'Cut Out'), ('split_edges', 'Split Edges'))))
    display = directory('polygon_display', 'Polygon Display', (
        row('polygon_display.backface_culling', 'Backface Culling', reason='Current viewport shading; not Maya per-object polygon display'),
        sep('display_culling'), row('polygon_display.border_edges', 'Border Edges'),
        row('polygon_display.texture_border_edges', 'Texture Border Edges'), sep('display_borders'),
        row('polygon_display.face_normals', 'Face Normals'), row('polygon_display.vertex_normals', 'Vertex Normals'),
        sep('display_normals'), row('polygon_display.face_centers', 'Face Centers'),
        row('polygon_display.hidden_triangles', 'Hidden Triangles'), row('polygon_display.vertices', 'Vertices'),
        sep('display_vertices'), row('polygon_display.reset', 'Reset Polygon Display'),
    ))
    return node(
        OBJECT_MENU, 'menu', 'Object Modeling', presentation='list', children=(
            row('offset_loop', 'Offset Edge Loop Tool', options=True, reason='Blender persistent Offset Edge Loop Cut tool'),
            row('smooth', 'Smooth', options=True, reason='Add Subdivision Surface modifier to active Mesh; other selected objects are unchanged'),
            row('unsmooth', 'Unsmooth', options=True), row('subdiv_proxy', 'Subdiv Proxy', options=True),
            row('crease', 'Crease Tool', options=True), sep('crease'),
            row('project_curve', 'Project Curve on Mesh', options=True),
            row('split_projected', 'Split Mesh with Projected Curve', options=True), sep('projected'),
            row('mirror', 'Mirror', options=True, reason='Add Mirror modifier to active Mesh; default X bisect and merge'), mapping, sep('mapping'),
            row('triangulate', 'Triangulate'), row('quadrangulate', 'Quadrangulate', options=True),
            row('reduce', 'Reduce', options=True, reason='Add Decimate modifier to active Mesh; default ratio 50 percent'),
            row('remesh', 'Remesh', options=True, reason='Add Voxel Remesh modifier to active Mesh; original mesh remains'),
            row('retopologize', 'Retopologize', options=True, reason='M2d-P02.Retopologize: Target-pinned QuadriFlow confirmation not implemented; native entry remains in Mesh menu'),
            sep('retopologize'), row('transfer_order', 'Transfer Vertex Order'), sep('transfer'),
            row('separate', 'Separate'), row('combine', 'Combine', options=True, reason='Join selected editable Meshes into the active Mesh'), booleans,
            sep('booleans'), row('cleanup', 'Cleanup', reason='M2d-P02.Cleanup: Whole-object cleanup parameters are not implemented; individual Edit cleanup actions remain in Mesh menus'),
            row('connect', 'Connect Tool', options=True),
            row('quad_draw', 'Quad Draw Tool', options=True, reason='Blender Poly Build adaptation; not Maya Quad Draw algorithm'),
            sep('quad_draw'), display,
        ))

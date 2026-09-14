# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed single-domain Edit Mesh menus and a strictly read-only root selector."""
MODEL_HOTBOX = 'context.modeling_hotbox'
MODEL_ROOTS = ('context.modeling_vertex', 'context.modeling_edge', 'context.modeling_face')


def modeling_root(context):
    """Resolve the explicit selection domain, never pick or change the editing set."""
    if not (context.area and context.area.type == 'VIEW_3D' and context.region and
            context.region.type == 'WINDOW' and context.mode == 'EDIT_MESH' and
            context.scene and context.scene.is_editable):
        return None
    flags = tuple(context.tool_settings.mesh_select_mode)
    if len(flags) != 3 or sum(bool(flag) for flag in flags) != 1:
        return None
    active = context.active_object
    if not (active and active.type == 'MESH' and active.is_editable and active.data.is_editable and
            active.visible_get(view_layer=context.view_layer)):
        return None
    import bmesh
    domain = flags.index(True)
    for obj in context.objects_in_mode_unique_data:
        if not (obj.type == 'MESH' and obj.is_editable and obj.data.is_editable and
                obj.visible_get(view_layer=context.view_layer)):
            continue
        bm = bmesh.from_edit_mesh(obj.data)
        if any(item.select and not item.hide for item in getattr(bm, ('verts', 'edges', 'faces')[domain])):
            return MODEL_ROOTS[domain]
    return None


def modeling_menus(node):
    """Retain Maya directions; expose only existing semantic commands, with honest gaps."""
    def options(identifier):
        return (node(identifier + '.options', 'disabled', 'Options', enabled=False,
                     reason='M2d-P06.Options: Maya parameter adapter not implemented; main action is not invoked'),)

    def has_options(parent, suffix):
        root = next(root for root in MODEL_ROOTS if parent.startswith(root))
        relative = (parent + '.' + suffix)[len(root):]
        common = {'.extrude', '.bevel', '.knife', '.merge.target_weld'}
        extra = ({'.normals.average', '.normals.from_faces', '.merge.distance'} if root == MODEL_ROOTS[0]
                 else {'.normals.angle', '.merge.border'} if root == MODEL_ROOTS[1]
                 else {'.wedge', '.poke', '.normals.reverse'})
        return relative in common | extra

    def command(parent, suffix, direction, label, identifier):
        row_id = parent + '.' + suffix
        return node(row_id, 'command', label, command=identifier, direction=direction,
                    children=options(row_id) if has_options(parent, suffix) else ())

    def gap(parent, suffix, direction, label, reason):
        row_id = parent + '.' + suffix
        return node(row_id, 'disabled', label, enabled=False, direction=direction, reason=reason,
                    children=options(row_id) if has_options(parent, suffix) else ())

    def ring(identifier, label, children, direction=None):
        return node(identifier, 'menu', label, children=children, presentation='radial', direction=direction)

    roots = []
    for index, root in enumerate(MODEL_ROOTS):
        children = []
        if index < 2:
            merge = root + '.merge'
            children.append(ring(merge, 'Merge Vertices' if index == 0 else 'Merge/Collapse Edges', (
                command(merge, 'center', 'N', ('Merge Vertices To Center' if index == 0 else 'Merge Edges To Center'), 'mesh.merge_center'),
                command(merge, 'distance' if index == 0 else 'collapse', 'NE' if index == 0 else 'E',
                        'Merge Vertices' if index == 0 else 'Collapse Edge',
                        'mesh.merge_distance' if index == 0 else 'mesh.collapse'),
                gap(merge, 'target_weld', 'S', 'Target Weld Tool',
                    'M2d-P04.TargetWeld / M3-P-TOOLS.MergeVertexTool: Target Weld and boundary pairing adapter not implemented'),
            ), 'N'))
            if index == 1:
                children[-1]['children'] = list(children[-1]['children']) + [
                    gap(merge, 'border', 'NE', 'Merge Border Edges',
                        'M2d-P06.MergeBorderEdges: Maya boundary-edge pairing adapter not implemented; Merge by Distance is not equivalent')]
        else:
            children.append(command(root, 'merge', 'N', 'Merge Faces To Center', 'mesh.merge_center'))
        if index == 0:
            children.extend((command(root, 'average', 'NE', 'Average Vertices', 'mesh.average_vertices'),
                             command(root, 'bevel', 'E', 'Chamfer Vertex', 'mesh.bevel_vertices'),
                             gap(root, 'extrude', 'S', 'Extrude Vertex',
                                 'M2d-P03.VertexExtrude: Maya vertex width/length/divisions adapter not implemented'),
                             gap(root, 'delete', 'SW', 'Delete Vertex',
                                 'M2d-P03.DeleteVertex: Maya vertex topology cleanup adapter not implemented')))
        elif index == 1:
            spin = root + '.spin'
            children.extend((ring(spin, 'Flip/Spin Edge', (
                gap(spin, 'flip', 'N', 'Flip Triangle Edge',
                    'M2d-P03.FlipTriangleEdge: Dedicated triangle-edge eligibility adapter not implemented'),
                command(spin, 'cw', 'E', 'Spin Forward', 'mesh.edge_rotate_cw'),
                command(spin, 'ccw', 'W', 'Spin Backward', 'mesh.edge_rotate_ccw'),
            ), 'NE'), command(root, 'bevel', 'E', 'Bevel Edge', 'mesh.bevel_edges'),
                command(root, 'extrude', 'S', 'Extrude Edge', 'mesh.extrude_edges'),
                command(root, 'dissolve', 'SW', 'Delete Edge', 'mesh.dissolve_edges')))
        else:
            children.extend((command(root, 'poke', 'NE', 'Poke Face', 'mesh.poke_faces'),
                             gap(root, 'bevel', 'E', 'Bevel Face',
                                 'M2d-P03.FaceBoundaryBevel: Face boundary selection and native bevel transaction not implemented'),
                             command(root, 'extrude', 'S', 'Extrude Face', 'mesh.extrude_region'),
                             gap(root, 'wedge', 'SW', 'Wedge Face',
                                 'M2d-P03.WedgeFace: Selected-edge pivot wedge adapter not implemented')))
        normals = root + '.normals'
        specs = (
            (('display', 'S', 'Toggle Vertex Normal Display', 'display.vertex_normals'),
             ('average', 'NE', 'Average Normals', 'normals.average_custom'),
             ('rotate', 'E', 'Vertex Normal Edit Tool', 'normals.rotate'),
             ('from_faces', 'SE', 'Set Normals to Face', 'normals.set_from_faces')),
            (('soften', 'NE', 'Soften Edge', 'normals.soften_edges'),
             ('angle', 'E', 'Soften/Harden', 'normals.harden_by_angle'),
             ('harden', 'SE', 'Harden Edge', 'normals.harden_edges'),
             ('display', 'S', 'Toggle Soft Edge Display', 'display.sharp_edges')),
            (('display', 'S', 'Toggle Face Normal Display', 'display.face_normals'),
             ('reverse', 'E', 'Reverse Normals', 'normals.reverse'),
             ('conform', 'SE', 'Conform Normals', 'normals.conform_outside')),
        )[index]
        normal_children = [command(normals, *spec) for spec in specs]
        if index == 2:
            normal_children.append(gap(normals, 'propagate', 'NE', 'Reverse Propagate',
                                       'M2d-P05.ReversePropagate: Reverse and propagate transaction not implemented'))
        children.extend((ring(normals, ('Vertex Normals', 'Soften/Harden Edges', 'Face Normals')[index],
                              normal_children, 'SE'),
                         command(root, 'knife', 'W', 'Multi-Cut', 'tool.mesh_knife'),
                         command(root, 'paint', 'NW', ('Paint Select Vertices', 'Paint Select Edges', 'Paint Select Faces')[index], 'selection.paint')))
        roots.append(ring(root, ('Vertex Modeling', 'Edge Modeling', 'Face Modeling')[index], children))
    return tuple(roots)

# Fixed Maya2026 core inventory. Reorder Vertices is retained even without Maya's
# optional meshReorder plugin. Rows are content; selection-domain dispatch stays
# in the existing runtime/native owner.
MODEL_COMPANION_ROOTS = tuple(root + '_menu' for root in MODEL_ROOTS)
MODEL_COMPANION_MAP = dict(zip(MODEL_ROOTS, MODEL_COMPANION_ROOTS))
# suffix, actual MayaStrings label, Options, existing bounded command.
_COMPANION_ROWS = {
    'vertex': (
        ('crease', 'Crease Tool', True, 'mesh.interactive_crease_vertices'),
        ('connect_components', 'Connect Components', True, ''),
        ('detach', 'Detach Components', False, 'mesh.detach_selection'),
        ('transform', 'Transform Component', True, ''),
        ('connect_tool', 'Connect Tool', True, ''),
        ('sep_tools', '|', False, ''),
        ('circularize', 'Circularize Vertices', True, 'mesh.circularize'),
        ('reorder', 'Reorder Vertices', False, ''),
        ('sep_reorder', '|', False, ''),
        ('apply_color', 'Apply Color', True, 'color.set_value'),
        ('sep_color', '|', False, ''),
        ('polygon_display', 'Polygon Display', False, ''),
    ),
    'edge': (
        ('crease', 'Crease Tool', True, 'mesh.interactive_crease_edges'),
        ('offset_loop', 'Offset Edge Loop Tool', True, 'tool.mesh_offset_loop'),
        ('insert_loop', 'Insert Edge Loop Tool', True, 'tool.mesh_loopcut'),
        ('slide', 'Slide Edge Tool', True, 'tool.mesh_edge_slide'),
        ('circularize', 'Circularize Components', True, 'mesh.circularize'),
        ('edge_flow', 'Edit Edge Flow', True, 'mesh.edge_flow'),
        ('sep_flow', '|', False, ''),
        ('subdivide', 'Add Divisions To Edge', True, 'mesh.subdivide'),
        ('bridge', 'Bridge', True, 'mesh.bridge'),
        ('fill_hole', 'Fill Hole', False, 'mesh.fill_holes'),
        ('sep_fill', '|', False, ''),
        ('connect_components', 'Connect Components', True, ''),
        ('detach', 'Detach Components', False, 'mesh.edge_split'),
        ('transform', 'Transform Component', True, ''),
        ('connect_tool', 'Connect Tool', True, ''),
        ('sep_tools', '|', False, ''),
        ('polygon_display', 'Polygon Display', False, ''),
    ),
    'face': (
        ('sep_radial', '|', False, ''),
        ('smart_extrude', 'Smart Extrude', False, 'mesh.extrude_manifold'),
        ('smooth', 'Smooth Faces', True, 'mesh.smooth_subdivide'),
        ('invisible', 'Assign Invisible Faces', True, ''),
        ('subdivide', 'Add Divisions To Faces', True, 'mesh.subdivide'),
        ('circularize', 'Circularize Components', True, 'mesh.circularize'),
        ('connect_components', 'Connect Components', True, ''),
        ('detach', 'Detach Components', False, 'mesh.detach_selection'),
        ('triangulate', 'Triangulate Faces', False, 'mesh.triangulate'),
        ('quadrangulate', 'Quadrangulate Faces', True, 'mesh.quadrangulate'),
        ('reduce', 'Reduce Faces', True, 'mesh.reduce'),
        ('remesh', 'Remesh', True, ''),
        ('bridge', 'Bridge Faces', True, ''),
        ('sep_bridge', '|', False, ''),
        ('mirror', 'Mirror', True, ''),
        ('extract', 'Extract Faces', True, 'mesh.extract_faces'),
        ('duplicate', 'Duplicate Face', True, 'mesh.duplicate_faces'),
        ('transform', 'Transform Component', True, ''),
        ('connect_tool', 'Connect Tool', True, ''),
        ('target_weld', 'Target Weld Tool', True, ''),
        ('sep_tools', '|', False, ''),
        ('mapping', 'Mapping', False, ''),
        ('sep_mapping', '|', False, ''),
        ('polygon_display', 'Polygon Display', False, ''),
    ),
}
_DISPLAY_ROWS = {
    'vertex': (
        ('backface_culling', 'Toggle Backface Culling', False, 'display.backface_culling'),
        ('sep_culling', '|', False, ''),
        ('vertices', 'Toggle Vertices', False, ''),
        ('normals', 'Toggle Vertex Normals', False, 'display.vertex_normals'),
        ('numbers', 'Toggle Vertex Numbers', False, 'display.component_indices'),
        ('sep_numbers', '|', False, ''),
        ('reset', 'Reset Polygon Display', False, ''),
    ),
    'edge': (
        ('backface_culling', 'Toggle Backface Culling', False, 'display.backface_culling'),
        ('sep_culling', '|', False, ''),
        ('border', 'Toggle Border Edges', False, ''),
        ('texture_border', 'Toggle Texture Border Edges', False, ''),
        ('sep_borders', '|', False, ''),
        ('hidden_triangles', 'Toggle Hidden Triangle Edges', False, ''),
        ('soft_edges', 'Toggle Soft Edge Display', False, 'display.sharp_edges'),
        ('sep_edges', '|', False, ''),
        ('reset', 'Reset Polygon Display', False, ''),
    ),
    'face': (
        ('backface_culling', 'Toggle Backface Culling', False, 'display.backface_culling'),
        ('sep_culling', '|', False, ''),
        ('centers', 'Toggle Face Centers', False, 'display.face_centers'),
        ('normals', 'Toggle Face Normals', False, 'display.face_normals'),
        ('numbers', 'Toggle Face Numbers', False, 'display.component_indices'),
        ('hidden_triangles', 'Toggle Hidden Triangles', False, ''),
        ('sep_triangles', '|', False, ''),
        ('reset', 'Reset Polygon Display', False, ''),
    ),
}
MODEL_MENU_COMMANDS = {}
MODEL_MENU_DOMAINS = {}
for _domain, _root in zip(('vertex', 'edge', 'face'), MODEL_COMPANION_ROOTS):
    for _suffix, _label, _options, _command in _COMPANION_ROWS[_domain]:
        if _command:
            MODEL_MENU_COMMANDS[_root + '.' + _suffix] = _command
            MODEL_MENU_DOMAINS[_root + '.' + _suffix] = _domain
    for _suffix, _label, _options, _command in _DISPLAY_ROWS[_domain]:
        if _command:
            MODEL_MENU_COMMANDS[_root + '.polygon_display.' + _suffix] = _command
            MODEL_MENU_DOMAINS[_root + '.polygon_display.' + _suffix] = _domain


def modeling_companions(node):
    """Maya component lists; Options are independent disabled leaves, never actions."""
    def row(parent, spec):
        suffix, label, options, command = spec
        identifier = parent + '.' + suffix
        if label == '|':
            return node(identifier, 'separator', '', enabled=False)
        children = (node(identifier + '.options', 'disabled', 'Options', enabled=False,
                         reason='M2d-P06.Options: Maya parameter adapter not implemented; main action is not invoked'),) if options else ()
        reason = ('Maya menu requires optional meshReorder plugin; Blender vertex-order adapter not implemented'
                  if suffix == 'reorder' else
                  'Maya component semantics not safely adapted; retained placeholder' if not command else
                  'Existing Blender Edit Mesh adaptation; native requirements and component-domain scope apply')
        if command.startswith('display.'):
            reason = ('Current Blender viewport overlay; not Maya per-object display. '
                      'Component indices share one Edit Mesh switch; sharp-edge colors differ from Maya soft-edge display')
        return node(identifier, 'command' if command else 'disabled', label, command=command,
                    enabled=bool(command), children=children, reason=reason)

    def mapping(parent):
        # Reuse the pure Object declaration without changing its module or nodes.
        from .object_modeling_hotbox import OBJECT_MENU, object_modeling_companion
        source = next(child for child in object_modeling_companion(node)['children']
                      if child['id'] == OBJECT_MENU + '.mapping')
        def reidentify(item):
            result = dict(item)
            result['id'] = item['id'].replace(OBJECT_MENU, parent, 1)
            result['children'] = [reidentify(child) for child in item['children']]
            return result
        return reidentify(source)

    menus = []
    for domain, root in zip(('vertex', 'edge', 'face'), MODEL_COMPANION_ROOTS):
        children = []
        for spec in _COMPANION_ROWS[domain]:
            if spec[0] == 'polygon_display':
                children.append(node(root + '.polygon_display', 'menu', 'Polygon Display', presentation='list',
                                     children=tuple(row(root + '.polygon_display', child) for child in _DISPLAY_ROWS[domain])))
            elif spec[0] == 'mapping':
                children.append(mapping(root))
            else:
                children.append(row(root, spec))
        menus.append(node(root, 'menu', domain.title() + ' Modeling', presentation='list', children=children))
    return tuple(menus)

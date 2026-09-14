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
    def command(parent, suffix, direction, label, identifier):
        return node(parent + '.' + suffix, 'command', label, command=identifier, direction=direction)

    def gap(parent, suffix, direction, label, reason):
        return node(parent + '.' + suffix, 'disabled', label, enabled=False, direction=direction, reason=reason)

    def ring(identifier, label, children, direction=None):
        return node(identifier, 'menu', label, children=children, presentation='radial', direction=direction)

    roots = []
    for index, root in enumerate(MODEL_ROOTS):
        children = []
        if index < 2:
            merge = root + '.merge'
            children.append(ring(merge, 'Merge Vertices' if index == 0 else 'Merge / Collapse', (
                command(merge, 'center', 'N', 'Merge at Center', 'mesh.merge_center'),
                command(merge, 'distance' if index == 0 else 'collapse', 'NE' if index == 0 else 'E',
                        'Merge by Distance' if index == 0 else 'Collapse Edges',
                        'mesh.merge_distance' if index == 0 else 'mesh.collapse'),
                gap(merge, 'target_weld', 'S', 'Target Weld',
                    'M2d-P04.TargetWeld / M3-P-TOOLS.MergeVertexTool: Target Weld and boundary pairing adapter not implemented'),
            ), 'N'))
        else:
            children.append(command(root, 'merge', 'N', 'Merge at Center', 'mesh.merge_center'))
        if index == 0:
            children.extend((command(root, 'average', 'NE', 'Smooth Vertices', 'mesh.average_vertices'),
                             command(root, 'bevel', 'E', 'Bevel Vertices', 'mesh.bevel_vertices'),
                             gap(root, 'extrude', 'S', 'Extrude Vertex',
                                 'M2d-P03.VertexExtrude: Maya vertex width/length/divisions adapter not implemented'),
                             gap(root, 'delete', 'SW', 'Delete Vertex',
                                 'M2d-P03.DeleteVertex: Maya vertex topology cleanup adapter not implemented')))
        elif index == 1:
            spin = root + '.spin'
            children.extend((ring(spin, 'Rotate Edges', (
                gap(spin, 'flip', 'N', 'Flip Triangle Edge',
                    'M2d-P03.FlipTriangleEdge: Dedicated triangle-edge eligibility adapter not implemented'),
                command(spin, 'cw', 'E', 'Rotate Edge CW', 'mesh.edge_rotate_cw'),
                command(spin, 'ccw', 'W', 'Rotate Edge CCW', 'mesh.edge_rotate_ccw'),
            ), 'NE'), command(root, 'bevel', 'E', 'Bevel Edges', 'mesh.bevel_edges'),
                command(root, 'extrude', 'S', 'Extrude Edges', 'mesh.extrude_edges'),
                command(root, 'dissolve', 'SW', 'Dissolve Edges', 'mesh.dissolve_edges')))
        else:
            children.extend((command(root, 'poke', 'NE', 'Poke Faces', 'mesh.poke_faces'),
                             gap(root, 'bevel', 'E', 'Bevel Face Boundary',
                                 'M2d-P03.FaceBoundaryBevel: Face boundary selection and native bevel transaction not implemented'),
                             command(root, 'extrude', 'S', 'Extrude Region', 'mesh.extrude_region'),
                             gap(root, 'wedge', 'SW', 'Wedge Face',
                                 'M2d-P03.WedgeFace: Selected-edge pivot wedge adapter not implemented')))
        normals = root + '.normals'
        specs = (
            (('display', 'S', 'Show Vertex Normals', 'display.vertex_normals'),
             ('average', 'NE', 'Average Custom Normals', 'normals.average_custom'),
             ('rotate', 'E', 'Rotate Normals', 'normals.rotate'),
             ('from_faces', 'SE', 'Set Normals from Faces', 'normals.set_from_faces')),
            (('soften', 'NE', 'Clear Sharp Edges', 'normals.soften_edges'),
             ('angle', 'E', 'Set Sharpness by Angle', 'normals.harden_by_angle'),
             ('harden', 'SE', 'Mark Sharp Edges', 'normals.harden_edges'),
             ('display', 'S', 'Show Sharp Edge Colors', 'display.sharp_edges')),
            (('display', 'S', 'Show Face Normals', 'display.face_normals'),
             ('reverse', 'E', 'Reverse Normals', 'normals.reverse'),
             ('conform', 'SE', 'Recalculate Outside', 'normals.conform_outside')),
        )[index]
        normal_children = [command(normals, *spec) for spec in specs]
        if index == 2:
            normal_children.append(gap(normals, 'propagate', 'NE', 'Reverse and Propagate',
                                       'M2d-P05.ReversePropagate: Reverse and propagate transaction not implemented'))
        children.extend((ring(normals, ('Vertex Normals', 'Edge Sharpness', 'Face Normals')[index],
                              normal_children, 'SE'),
                         command(root, 'knife', 'W', 'Knife (Multi-Cut Adaptation)', 'tool.mesh_knife'),
                         command(root, 'paint', 'NW', 'Circle Select', 'selection.paint')))
        roots.append(ring(root, ('Vertex Modeling', 'Edge Modeling', 'Face Modeling')[index], children))
    return tuple(roots)

# SPDX-FileCopyrightText: 2009-2023 Blender Authors
# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Original native menu groups shared with the Modeling menu composition.

Functions preserve native operators, properties, enum providers and build/mode conditions.
"""
import bpy
from bpy.app.translations import pgettext_iface as iface_, contexts as i18n_contexts
from axismeld.workspace_native_groups import GROUPS


def _draw_mesh_transform(layout, context, include=None):
    with_bullet = bpy.app.build_options.bullet
    if include is None or 'mesh.transform.VIEW3D_MT_transform' in include:
        layout.menu('VIEW3D_MT_transform')
    if include is None or 'mesh.transform.VIEW3D_MT_mirror' in include:
        layout.menu('VIEW3D_MT_mirror')
    if include is None or 'mesh.transform.VIEW3D_MT_snap' in include:
        layout.menu('VIEW3D_MT_snap')


def _draw_mesh_duplicate_extrude(layout, context, include=None):
    if include is None or 'mesh.duplicate_extrude.mesh_duplicate_move' in include:
        layout.operator('mesh.duplicate_move', text='Duplicate', icon='DUPLICATE')
    if include is None or 'mesh.duplicate_extrude.VIEW3D_MT_edit_mesh_extrude' in include:
        layout.menu('VIEW3D_MT_edit_mesh_extrude')


def _draw_mesh_merge_split(layout, context, include=None):
    if include is None or 'mesh.merge_split.VIEW3D_MT_edit_mesh_merge' in include:
        layout.menu('VIEW3D_MT_edit_mesh_merge', text='Merge')
    if include is None or 'mesh.merge_split.VIEW3D_MT_edit_mesh_split' in include:
        layout.menu('VIEW3D_MT_edit_mesh_split', text='Split')
    if include is None or 'mesh.merge_split.mesh_separate' in include:
        layout.operator_menu_enum('mesh.separate', 'type')


def _draw_mesh_cut(layout, context, include=None):
    with_bullet = bpy.app.build_options.bullet
    if include is None or 'mesh.cut.mesh_bisect' in include:
        layout.operator('mesh.bisect')
    if include is None or 'mesh.cut.mesh_knife_project' in include:
        layout.operator('mesh.knife_project')
    if include is None or 'mesh.cut.mesh_knife_tool' in include:
        props = layout.operator('mesh.knife_tool')
        props.use_occlude_geometry = True
        props.only_selected = False
    if with_bullet:
        if include is None or 'mesh.cut.mesh_convex_hull' in include:
            layout.operator('mesh.convex_hull')


def _draw_mesh_symmetry(layout, context, include=None):
    if include is None or 'mesh.symmetry.mesh_symmetrize' in include:
        layout.operator('mesh.symmetrize')
    if include is None or 'mesh.symmetry.mesh_symmetry_snap' in include:
        layout.operator('mesh.symmetry_snap')


def _draw_mesh_attributes(layout, context, include=None):
    if include is None or 'mesh.attributes.VIEW3D_MT_edit_mesh_normals' in include:
        layout.menu('VIEW3D_MT_edit_mesh_normals')
    if include is None or 'mesh.attributes.VIEW3D_MT_edit_mesh_shading' in include:
        layout.menu('VIEW3D_MT_edit_mesh_shading')
    if include is None or 'mesh.attributes.VIEW3D_MT_edit_mesh_weights' in include:
        layout.menu('VIEW3D_MT_edit_mesh_weights')
    if include is None or 'mesh.attributes.mesh_attribute_set' in include:
        layout.operator('mesh.attribute_set')
    if include is None or 'mesh.attributes.mesh_sort_elements' in include:
        layout.operator_menu_enum('mesh.sort_elements', 'type', text='Sort Elements')


def _draw_mesh_cleanup(layout, context, include=None):
    if include is None or 'mesh.cleanup.VIEW3D_MT_edit_mesh_showhide' in include:
        layout.menu('VIEW3D_MT_edit_mesh_showhide')
    if include is None or 'mesh.cleanup.VIEW3D_MT_edit_mesh_clean' in include:
        layout.menu('VIEW3D_MT_edit_mesh_clean')


def _draw_mesh_delete(layout, context, include=None):
    if include is None or 'mesh.delete.VIEW3D_MT_edit_mesh_delete' in include:
        layout.menu('VIEW3D_MT_edit_mesh_delete')
    if include is None or 'mesh.delete.template_node_operator_asset_menu_items' in include:
        layout.template_node_operator_asset_menu_items(catalog_path='Mesh')


def _draw_vertex_extrude(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.extrude.mesh_extrude_vertices_move' in include:
        layout.operator('mesh.extrude_vertices_move', text='Extrude Vertices')
    if include is None or 'vertex.extrude.mesh_dupli_extrude_cursor' in include:
        layout.operator('mesh.dupli_extrude_cursor').rotate_source = True
    if include is None or 'vertex.extrude.mesh_bevel' in include:
        layout.operator('mesh.bevel', text='Bevel Vertices').affect = 'VERTICES'


def _draw_vertex_connect(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.connect.mesh_edge_face_add' in include:
        layout.operator('mesh.edge_face_add', text='New Edge/Face from Vertices')
    if include is None or 'vertex.connect.mesh_vert_connect_path' in include:
        layout.operator('mesh.vert_connect_path', text='Connect Vertex Path')
    if include is None or 'vertex.connect.mesh_vert_connect' in include:
        layout.operator('mesh.vert_connect', text='Connect Vertex Pairs')


def _draw_vertex_rip(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.rip.mesh_rip_move' in include:
        props = layout.operator('mesh.rip_move', text='Rip Vertices')
        props.MESH_OT_rip.use_fill = False
    if include is None or 'vertex.rip.mesh_rip_move_2' in include:
        props = layout.operator('mesh.rip_move', text='Rip Vertices and Fill')
        props.MESH_OT_rip.use_fill = True
    if include is None or 'vertex.rip.mesh_rip_edge_move' in include:
        layout.operator('mesh.rip_edge_move', text='Rip Vertices and Extend')


def _draw_vertex_smooth_slide(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.smooth_slide.transform_vert_slide' in include:
        layout.operator('transform.vert_slide', text='Slide Vertices')
    layout.operator_context = 'EXEC_REGION_WIN'
    if include is None or 'vertex.smooth_slide.mesh_vertices_smooth' in include:
        layout.operator('mesh.vertices_smooth', text='Smooth Vertices').factor = 0.5
    if include is None or 'vertex.smooth_slide.mesh_vertices_smooth_laplacian' in include:
        layout.operator('mesh.vertices_smooth_laplacian', text='Smooth Vertices (Laplacian)')
    layout.operator_context = 'INVOKE_REGION_WIN'


def _draw_vertex_crease(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.crease.transform_vert_crease' in include:
        layout.operator('transform.vert_crease', icon='VERTEX_CREASE')


def _draw_vertex_shape_keys(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.shape_keys.mesh_blend_from_shape' in include:
        layout.operator('mesh.blend_from_shape')
    if include is None or 'vertex.shape_keys.mesh_shape_propagate_to_all' in include:
        layout.operator('mesh.shape_propagate_to_all', text='Propagate to Shapes')


def _draw_vertex_groups_hooks(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.groups_hooks.VIEW3D_MT_vertex_group' in include:
        layout.menu('VIEW3D_MT_vertex_group')
    if include is None or 'vertex.groups_hooks.VIEW3D_MT_hook' in include:
        layout.menu('VIEW3D_MT_hook')


def _draw_vertex_parent(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'vertex.parent.object_vertex_parent_set' in include:
        layout.operator('object.vertex_parent_set')
    if include is None or 'vertex.parent.template_node_operator_asset_menu_items' in include:
        layout.template_node_operator_asset_menu_items(catalog_path='Vertex')


def _draw_edge_construct(layout, context, include=None):
    with_freestyle = bpy.app.build_options.freestyle
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'edge.construct.mesh_extrude_edges_move' in include:
        layout.operator('mesh.extrude_edges_move', text='Extrude Edges')
    if include is None or 'edge.construct.mesh_bevel' in include:
        layout.operator('mesh.bevel', text='Bevel Edges').affect = 'EDGES'
    if include is None or 'edge.construct.mesh_bridge_edge_loops' in include:
        layout.operator('mesh.bridge_edge_loops')
    if include is None or 'edge.construct.mesh_screw' in include:
        layout.operator('mesh.screw')


def _draw_edge_subdivide(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'edge.subdivide.mesh_subdivide' in include:
        layout.operator('mesh.subdivide')
    if include is None or 'edge.subdivide.mesh_subdivide_edgering' in include:
        layout.operator('mesh.subdivide_edgering')
    if include is None or 'edge.subdivide.mesh_unsubdivide' in include:
        layout.operator('mesh.unsubdivide')


def _draw_edge_rotate(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'edge.rotate.mesh_edge_rotate' in include:
        layout.operator('mesh.edge_rotate', text='Rotate Edge CW').use_ccw = False
    if include is None or 'edge.rotate.mesh_edge_rotate_2' in include:
        layout.operator('mesh.edge_rotate', text='Rotate Edge CCW').use_ccw = True


def _draw_edge_slide(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'edge.slide.transform_edge_slide' in include:
        layout.operator('transform.edge_slide')
    if include is None or 'edge.slide.mesh_loopcut_slide' in include:
        props = layout.operator('mesh.loopcut_slide')
        props.TRANSFORM_OT_edge_slide.release_confirm = False
    if include is None or 'edge.slide.mesh_offset_edge_loops_slide' in include:
        layout.operator('mesh.offset_edge_loops_slide')


def _draw_edge_weight(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'edge.weight.transform_edge_bevelweight' in include:
        layout.operator('transform.edge_bevelweight', icon='EDGE_BEVEL')
    if include is None or 'edge.weight.transform_edge_crease' in include:
        layout.operator('transform.edge_crease', icon='EDGE_CREASE')


def _draw_edge_seams(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'edge.seams.mesh_mark_seam' in include:
        layout.operator('mesh.mark_seam', icon='EDGE_SEAM').clear = False
    if include is None or 'edge.seams.mesh_mark_seam_2' in include:
        layout.operator('mesh.mark_seam', text='Clear Seam').clear = True


def _draw_edge_sharp(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    with_freestyle = bpy.app.build_options.freestyle
    if include is None or 'edge.sharp.mesh_mark_sharp' in include:
        layout.operator('mesh.mark_sharp', icon='EDGE_SHARP')
    if include is None or 'edge.sharp.mesh_mark_sharp_2' in include:
        layout.operator('mesh.mark_sharp', text='Clear Sharp').clear = True
    if include is None or 'edge.sharp.mesh_mark_sharp_3' in include:
        layout.operator('mesh.mark_sharp', text='Mark Sharp from Vertices').use_verts = True
    if include is None or 'edge.sharp.mesh_mark_sharp_4' in include:
        props = layout.operator('mesh.mark_sharp', text='Clear Sharp from Vertices')
        props.use_verts = True
        props.clear = True
    if include is None or 'edge.sharp.mesh_set_sharpness_by_angle' in include:
        layout.operator('mesh.set_sharpness_by_angle')
    if with_freestyle:
        layout.separator()
        if include is None or 'edge.sharp.mesh_mark_freestyle_edge' in include:
            layout.operator('mesh.mark_freestyle_edge').clear = False
        if include is None or 'edge.sharp.mesh_mark_freestyle_edge_2' in include:
            layout.operator('mesh.mark_freestyle_edge', text='Clear Freestyle Edge').clear = True
    if include is None or 'edge.sharp.template_node_operator_asset_menu_items' in include:
        layout.template_node_operator_asset_menu_items(catalog_path='Edge')


def _draw_face_extrude(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.extrude.view3d_edit_mesh_extrude_move_normal' in include:
        layout.operator('view3d.edit_mesh_extrude_move_normal', text='Extrude Faces')
    if include is None or 'face.extrude.view3d_edit_mesh_extrude_move_shrink_fatten' in include:
        layout.operator('view3d.edit_mesh_extrude_move_shrink_fatten', text='Extrude Faces Along Normals')
    if include is None or 'face.extrude.mesh_extrude_faces_move' in include:
        layout.operator('mesh.extrude_faces_move', text='Extrude Individual Faces')


def _draw_face_construct(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.construct.mesh_inset' in include:
        layout.operator('mesh.inset')
    if include is None or 'face.construct.mesh_poke' in include:
        layout.operator('mesh.poke')
    if include is None or 'face.construct.mesh_quads_convert_to_tris' in include:
        props = layout.operator('mesh.quads_convert_to_tris')
        props.quad_method = props.ngon_method = 'BEAUTY'
    if include is None or 'face.construct.mesh_tris_convert_to_quads' in include:
        layout.operator('mesh.tris_convert_to_quads')
    if include is None or 'face.construct.mesh_solidify' in include:
        layout.operator('mesh.solidify', text='Solidify Faces')
    if include is None or 'face.construct.mesh_wireframe' in include:
        layout.operator('mesh.wireframe')


def _draw_face_fill(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.fill.mesh_fill' in include:
        layout.operator('mesh.fill')
    if include is None or 'face.fill.mesh_fill_grid' in include:
        layout.operator('mesh.fill_grid')
    if include is None or 'face.fill.mesh_beautify_fill' in include:
        layout.operator('mesh.beautify_fill')


def _draw_face_boolean(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.boolean.mesh_intersect' in include:
        layout.operator('mesh.intersect')
    if include is None or 'face.boolean.mesh_intersect_boolean' in include:
        layout.operator('mesh.intersect_boolean')


def _draw_face_split(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.split.mesh_face_split_by_edges' in include:
        layout.operator('mesh.face_split_by_edges')


def _draw_face_shading(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.shading.mesh_faces_shade_smooth' in include:
        layout.operator('mesh.faces_shade_smooth')
    if include is None or 'face.shading.mesh_faces_shade_flat' in include:
        layout.operator('mesh.faces_shade_flat')


def _draw_face_data(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'face.data.VIEW3D_MT_edit_mesh_faces_data' in include:
        layout.menu('VIEW3D_MT_edit_mesh_faces_data')
    if include is None or 'face.data.template_node_operator_asset_menu_items' in include:
        layout.template_node_operator_asset_menu_items(catalog_path='Face')


def _draw_uv_unwrap(layout, context, include=None):
    if include is None or 'uv.unwrap.IMAGE_MT_uvs_unwrap' in include:
        layout.menu_contents('IMAGE_MT_uvs_unwrap')


def _draw_uv_projection(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'uv.projection.uv_project_from_view' in include:
        layout.operator('uv.project_from_view').scale_to_bounds = False
    if include is None or 'uv.projection.uv_project_from_view_2' in include:
        layout.operator('uv.project_from_view', text='Project from View (Bounds)').scale_to_bounds = True


def _draw_uv_seams(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'uv.seams.mesh_mark_seam' in include:
        layout.operator('mesh.mark_seam', icon='EDGE_SEAM').clear = False
    if include is None or 'uv.seams.mesh_mark_seam_2' in include:
        layout.operator('mesh.mark_seam', text='Clear Seam').clear = True


def _draw_uv_reset(layout, context, include=None):
    layout.operator_context = 'INVOKE_REGION_WIN'
    if include is None or 'uv.reset.uv_reset' in include:
        layout.operator('uv.reset')
    if include is None or 'uv.reset.template_node_operator_asset_menu_items' in include:
        layout.template_node_operator_asset_menu_items(catalog_path='UV')


def _draw_curve_transform(layout, context, include=None):
    if include is None or 'curve.transform.VIEW3D_MT_transform' in include:
        layout.menu('VIEW3D_MT_transform')
    if include is None or 'curve.transform.VIEW3D_MT_mirror' in include:
        layout.menu('VIEW3D_MT_mirror')
    if include is None or 'curve.transform.VIEW3D_MT_snap' in include:
        layout.menu('VIEW3D_MT_snap')


def _draw_curve_duplicate(layout, context, include=None):
    if include is None or 'curve.duplicate.curve_spin' in include:
        layout.operator('curve.spin')
    if include is None or 'curve.duplicate.curve_duplicate_move' in include:
        layout.operator('curve.duplicate_move', icon='DUPLICATE')


def _draw_curve_split(layout, context, include=None):
    if include is None or 'curve.split.curve_split' in include:
        layout.operator('curve.split')
    if include is None or 'curve.split.curve_separate' in include:
        layout.operator('curve.separate')


def _draw_curve_spline(layout, context, include=None):
    if include is None or 'curve.spline.curve_cyclic_toggle' in include:
        layout.operator('curve.cyclic_toggle')
    if include is None or 'curve.spline.curve_spline_type_set' in include:
        layout.operator_menu_enum('curve.spline_type_set', 'type')


def _draw_curve_cleanup(layout, context, include=None):
    if include is None or 'curve.cleanup.VIEW3D_MT_edit_curve_showhide' in include:
        layout.menu('VIEW3D_MT_edit_curve_showhide')
    if include is None or 'curve.cleanup.VIEW3D_MT_edit_curve_clean' in include:
        layout.menu('VIEW3D_MT_edit_curve_clean')
    if include is None or 'curve.cleanup.VIEW3D_MT_edit_curve_delete' in include:
        layout.menu('VIEW3D_MT_edit_curve_delete')


def _draw_curve_points_edit(layout, context, include=None):
    edit_object = context.edit_object
    if edit_object.type in {'CURVE', 'SURFACE'}:
        if include is None or 'curve_points.edit.curve_extrude_move' in include:
            layout.operator('curve.extrude_move')
        if include is None or 'curve_points.edit.curve_vertex_add' in include:
            layout.operator('curve.vertex_add')
        layout.separator()
        if include is None or 'curve_points.edit.curve_make_segment' in include:
            layout.operator('curve.make_segment')
        layout.separator()
        if edit_object.type == 'CURVE':
            if include is None or 'curve_points.edit.transform_tilt' in include:
                layout.operator('transform.tilt')
            if include is None or 'curve_points.edit.curve_tilt_clear' in include:
                layout.operator('curve.tilt_clear')
            layout.separator()
            if include is None or 'curve_points.edit.curve_handle_type_set' in include:
                layout.operator_menu_enum('curve.handle_type_set', 'type')
            if include is None or 'curve_points.edit.curve_normals_make_consistent' in include:
                layout.operator('curve.normals_make_consistent')
            layout.separator()
        if include is None or 'curve_points.edit.curve_smooth' in include:
            layout.operator('curve.smooth')
        if edit_object.type == 'CURVE':
            if include is None or 'curve_points.edit.curve_smooth_tilt' in include:
                layout.operator('curve.smooth_tilt')
            if include is None or 'curve_points.edit.curve_smooth_radius' in include:
                layout.operator('curve.smooth_radius')
            if include is None or 'curve_points.edit.curve_smooth_weight' in include:
                layout.operator('curve.smooth_weight')
        layout.separator()
    if include is None or 'curve_points.edit.VIEW3D_MT_hook' in include:
        layout.menu('VIEW3D_MT_hook')


def _draw_curve_points_parent(layout, context, include=None):
    if include is None or 'curve_points.parent.object_vertex_parent_set' in include:
        layout.operator('object.vertex_parent_set')


def _draw_curve_segments_edit(layout, context, include=None):
    if include is None or 'curve_segments.edit.curve_subdivide' in include:
        layout.operator('curve.subdivide')
    if include is None or 'curve_segments.edit.curve_switch_direction' in include:
        layout.operator('curve.switch_direction')


def _draw_curves_transform(layout, context, include=None):
    if include is None or 'curves.transform.VIEW3D_MT_transform' in include:
        layout.menu('VIEW3D_MT_transform')
    if include is None or 'curves.transform.VIEW3D_MT_mirror' in include:
        layout.menu('VIEW3D_MT_mirror')
    if include is None or 'curves.transform.VIEW3D_MT_snap' in include:
        layout.menu('VIEW3D_MT_snap')


def _draw_curves_construct(layout, context, include=None):
    if include is None or 'curves.construct.curves_duplicate_move' in include:
        layout.operator('curves.duplicate_move', icon='DUPLICATE')
    if include is None or 'curves.construct.curves_extrude_move' in include:
        layout.operator('curves.extrude_move')


def _draw_curves_attributes(layout, context, include=None):
    if include is None or 'curves.attributes.curves_attribute_set' in include:
        layout.operator('curves.attribute_set')
    if include is None or 'curves.attributes.curves_curve_type_set' in include:
        layout.operator_menu_enum('curves.curve_type_set', 'type')
    if include is None or 'curves.attributes.curves_cyclic_toggle' in include:
        layout.operator('curves.cyclic_toggle')
    if include is None or 'curves.attributes.template_node_operator_asset_menu_items' in include:
        layout.template_node_operator_asset_menu_items(catalog_path='Curves')


def _draw_curves_delete(layout, context, include=None):
    if include is None or 'curves.delete.curves_separate' in include:
        layout.operator('curves.separate')
    if include is None or 'curves.delete.curves_delete' in include:
        layout.operator('curves.delete', icon='X')


def _draw_curves_points_edit(layout, context, include=None):
    if include is None or 'curves_points.edit.curves_extrude_move' in include:
        layout.operator('curves.extrude_move')
    if include is None or 'curves_points.edit.curves_handle_type_set' in include:
        layout.operator_menu_enum('curves.handle_type_set', 'type')


def _draw_curves_segments_edit(layout, context, include=None):
    if include is None or 'curves_segments.edit.curves_subdivide' in include:
        layout.operator('curves.subdivide')
    if include is None or 'curves_segments.edit.curves_switch_direction' in include:
        layout.operator('curves.switch_direction')


def _draw_object_modifiers(layout, context, include=None):
    if include is None or 'object.modifiers.provider' in include:
        layout.menu_contents('VIEW3D_MT_object_modifiers')


_DRAW = {
    'mesh.transform': _draw_mesh_transform,
    'mesh.duplicate_extrude': _draw_mesh_duplicate_extrude,
    'mesh.merge_split': _draw_mesh_merge_split,
    'mesh.cut': _draw_mesh_cut,
    'mesh.symmetry': _draw_mesh_symmetry,
    'mesh.attributes': _draw_mesh_attributes,
    'mesh.cleanup': _draw_mesh_cleanup,
    'mesh.delete': _draw_mesh_delete,
    'vertex.extrude': _draw_vertex_extrude,
    'vertex.connect': _draw_vertex_connect,
    'vertex.rip': _draw_vertex_rip,
    'vertex.smooth_slide': _draw_vertex_smooth_slide,
    'vertex.crease': _draw_vertex_crease,
    'vertex.shape_keys': _draw_vertex_shape_keys,
    'vertex.groups_hooks': _draw_vertex_groups_hooks,
    'vertex.parent': _draw_vertex_parent,
    'edge.construct': _draw_edge_construct,
    'edge.subdivide': _draw_edge_subdivide,
    'edge.rotate': _draw_edge_rotate,
    'edge.slide': _draw_edge_slide,
    'edge.weight': _draw_edge_weight,
    'edge.seams': _draw_edge_seams,
    'edge.sharp': _draw_edge_sharp,
    'face.extrude': _draw_face_extrude,
    'face.construct': _draw_face_construct,
    'face.fill': _draw_face_fill,
    'face.boolean': _draw_face_boolean,
    'face.split': _draw_face_split,
    'face.shading': _draw_face_shading,
    'face.data': _draw_face_data,
    'uv.unwrap': _draw_uv_unwrap,
    'uv.projection': _draw_uv_projection,
    'uv.seams': _draw_uv_seams,
    'uv.reset': _draw_uv_reset,
    'curve.transform': _draw_curve_transform,
    'curve.duplicate': _draw_curve_duplicate,
    'curve.split': _draw_curve_split,
    'curve.spline': _draw_curve_spline,
    'curve.cleanup': _draw_curve_cleanup,
    'curve_points.edit': _draw_curve_points_edit,
    'curve_points.parent': _draw_curve_points_parent,
    'curve_segments.edit': _draw_curve_segments_edit,
    'curves.transform': _draw_curves_transform,
    'curves.construct': _draw_curves_construct,
    'curves.attributes': _draw_curves_attributes,
    'curves.delete': _draw_curves_delete,
    'curves_points.edit': _draw_curves_points_edit,
    'curves_segments.edit': _draw_curves_segments_edit,
    'object.modifiers': _draw_object_modifiers,
}

_ORIGINAL = {'VIEW3D_MT_edit_mesh': ('mesh.transform',
                         'mesh.duplicate_extrude',
                         'mesh.merge_split',
                         'mesh.cut',
                         'mesh.symmetry',
                         'mesh.attributes',
                         'mesh.cleanup',
                         'mesh.delete'),
 'VIEW3D_MT_edit_mesh_vertices': ('vertex.extrude',
                                  'vertex.connect',
                                  'vertex.rip',
                                  'vertex.smooth_slide',
                                  'vertex.crease',
                                  'vertex.shape_keys',
                                  'vertex.groups_hooks',
                                  'vertex.parent'),
 'VIEW3D_MT_edit_mesh_edges': ('edge.construct',
                               'edge.subdivide',
                               'edge.rotate',
                               'edge.slide',
                               'edge.weight',
                               'edge.seams',
                               'edge.sharp'),
 'VIEW3D_MT_edit_mesh_faces': ('face.extrude',
                               'face.construct',
                               'face.fill',
                               'face.boolean',
                               'face.split',
                               'face.shading',
                               'face.data'),
 'VIEW3D_MT_uv_map': ('uv.unwrap', 'uv.projection', 'uv.seams', 'uv.reset'),
 'VIEW3D_MT_edit_curve': ('curve.transform', 'curve.duplicate', 'curve.split', 'curve.spline', 'curve.cleanup'),
 'VIEW3D_MT_edit_surface': ('curve.transform', 'curve.duplicate', 'curve.split', 'curve.spline', 'curve.cleanup'),
 'VIEW3D_MT_edit_curve_ctrlpoints': ('curve_points.edit', 'curve_points.parent'),
 'VIEW3D_MT_edit_curve_segments': ('curve_segments.edit',),
 'VIEW3D_MT_edit_curves': ('curves.transform', 'curves.construct', 'curves.attributes', 'curves.delete'),
 'VIEW3D_MT_edit_curves_control_points': ('curves_points.edit',),
 'VIEW3D_MT_edit_curves_segments': ('curves_segments.edit',)}


def draw_original(layout, context, source_menu):
    """The native Menu class calls the same groups in its original order."""
    for index, key in enumerate(_ORIGINAL[source_menu]):
        if index:
            layout.separator()
        _DRAW[key](layout, context)


class _IconLayout:
    """Add a semantic icon only while composing native groups in Modeling."""
    def __init__(self, layout, icon):
        object.__setattr__(self, '_layout', layout)
        object.__setattr__(self, '_icon', icon)

    def __getattr__(self, name):
        return getattr(self._layout, name)

    def __setattr__(self, name, value):
        setattr(self._layout, name, value)

    def operator(self, *args, **kwargs):
        kwargs.setdefault('icon', self._icon)
        return self._layout.operator(*args, **kwargs)

    def menu(self, *args, **kwargs):
        kwargs.setdefault('icon', self._icon)
        return self._layout.menu(*args, **kwargs)

    def operator_menu_enum(self, *args, **kwargs):
        kwargs.setdefault('icon', self._icon)
        return self._layout.operator_menu_enum(*args, **kwargs)


def modeling_icon_layout(layout, context, icon):
    """Decorate inline native providers only in the Modeling 3D viewport."""
    from bl_ui import space_axismeld_menubar
    if space_axismeld_menubar.modeling_workspace(context):
        return _IconLayout(layout, icon)
    return layout


_HOSTED_SUBMENUS = frozenset({
    'VIEW3D_MT_edit_curve_ctrlpoints', 'VIEW3D_MT_edit_curve_segments',
    'VIEW3D_MT_edit_curves_control_points', 'VIEW3D_MT_edit_curves_segments',
})


def _selected_items(key, include):
    metadata = GROUPS[key]
    known = frozenset(item['id'] for item in metadata['items'])
    selected = known if include is None else frozenset(include)
    if not selected <= known:
        raise ValueError('Unknown native modeling item in group: ' + key)
    return selected


def _hosted_nodes(context, source_menu, root_id, path=None):
    """Read only the visible classified nodes; never reconstruct filtered items."""
    from bl_ui import space_axismeld_menubar
    if not space_axismeld_menubar.modeling_workspace(context):
        return ()
    root = next((node for node in space_axismeld_menubar._CATALOG['menus']
                 if node['id'] == root_id), None)
    if root is None:
        return ()
    found = []

    def visit(node):
        if node['kind'] == 'native_group':
            metadata = GROUPS[node['group_key']]
            if (metadata['source_menu'] == source_menu and metadata['root_id'] == root_id and
                    getattr(context, 'mode', '') in metadata['modes'] and
                    (path is None or metadata['path'] == path) and
                    _selected_items(node['group_key'], node.get('include'))):
                found.append(node)
        for child in node.get('children', ()):
            visit(child)

    visit(root)
    return tuple(found)


def draw_hosted_group(layout, context, key, *, include=None):
    """Use the real source Menu once per classified destination, preserving hooks."""
    metadata = GROUPS[key]
    source_menu = metadata['source_menu']
    if (source_menu not in _HOSTED_SUBMENUS or
            getattr(context, 'mode', '') not in metadata['modes'] or
            getattr(context, 'edit_object', None) is None):
        return False
    nodes = _hosted_nodes(context, source_menu, metadata['root_id'], metadata['path'])
    current = next((node for node in nodes if node['group_key'] == key), None)
    if current is None:
        return False
    # An explicit caller subset different from the visible catalog is an
    # ordinary group draw; it must never broaden into the complete host menu.
    if _selected_items(key, include) != _selected_items(key, current.get('include')):
        return False
    if nodes[0] is current:
        layout.menu_contents(source_menu)
    return True


def draw_hosted_menu(layout, context, source_menu):
    """Called by the original Menu.draw; native append/prepend owns its callbacks."""
    if source_menu not in _HOSTED_SUBMENUS or getattr(context, 'edit_object', None) is None:
        return False
    root_id = 'modeling.surfaces' if getattr(context, 'mode', '') == 'EDIT_SURFACE' else 'modeling.curves'
    nodes = _hosted_nodes(context, source_menu, root_id)
    if not nodes:
        return False
    # These four source menus each occupy a single purpose directory per mode.
    # A later repartition needs explicit hosting rules, not implicit global state.
    if len({GROUPS[node['group_key']]['path'] for node in nodes}) != 1:
        raise ValueError('Native submenu source spans multiple classified destinations: ' + source_menu)
    for index, node in enumerate(nodes):
        if index:
            layout.separator()
        _draw_group_content(layout, context, node['group_key'],
                            _selected_items(node['group_key'], node.get('include')))
    return True


def _draw_group_content(layout, context, key, selected):
    metadata = GROUPS[key]
    if not selected:
        return
    row = layout.column()
    matches = (getattr(getattr(context, 'area', None), 'type', '') == 'VIEW_3D' and
               getattr(context, 'mode', '') in metadata['modes'] and
               (not metadata.get('requires_object') or getattr(context, 'object', None) is not None))
    row.enabled = matches
    if metadata['dynamic_context'] and (not matches or getattr(context, 'edit_object', None) is None):
        row.enabled = False
        row.label(text=metadata['label'], icon=metadata['icon'])
        return
    _DRAW[metadata['draw_key']](_IconLayout(row, metadata['icon']), context, selected)


def draw_group(layout, context, key, *, include=None):
    """Draw an approved group, optionally keeping a reviewed subset of its items."""
    selected = _selected_items(key, include)
    if selected and not draw_hosted_group(layout, context, key, include=selected):
        _draw_group_content(layout, context, key, selected)

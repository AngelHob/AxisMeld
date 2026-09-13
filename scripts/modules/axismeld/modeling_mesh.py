# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed native mesh capabilities; labels retain Blender distinctions from Maya 2026."""
from math import pi
from .modeling_schema import CommandSpec, NativeCall, op

_M = ('EDIT_MESH',)
_SOURCE = {
    'Mesh': 'scripts/startup/bl_ui/space_view3d.py:4571-4628,5201-5222; '
            'scripts/startup/bl_ui/properties_data_modifier.py:143-198; '
            'Maya2026/scripts/startup/PolygonsMeshMenu.mel',
    'Edit Mesh': 'scripts/startup/bl_ui/space_view3d.py:4851-5280; '
                 'source/blender/editors/mesh/mesh_ops.cc:263-310; '
                 'Maya2026/scripts/startup/PolygonsBuildMenu.mel',
    'Mesh Tools': 'scripts/startup/bl_ui/space_toolsystem_toolbar.py:879-1243; '
                  'Maya2026/scripts/startup/PolygonsBuildToolsMenu.mel; '
                  'Maya2026/scripts/startup/hotkeySetup.mel:353-354',
    'Mesh Display': 'scripts/startup/bl_ui/space_view3d.py:5002-5190,7530-7555; '
                    'Maya2026/scripts/startup/ModelingMeshDisplayMenu.mel',
}
_specs = []


def _add(identifier, label, category, operator, *, section=(), maya=(), difference='', **kw):
    _specs.append(op(identifier, label, category, operator, section=section, maya=maya,
                     source=kw.pop('source', _SOURCE[category]),
                     classification='adapted' if maya else 'blender',
                     difference=difference or
                     f'Blender {label}; native topology and parameters, without Maya construction history.',
                     **kw))


def _edit(identifier, label, operator, *, category='Edit Mesh', requires='vertices', **kw):
    _add(identifier, label, category, operator, modes=_M, requires=requires, **kw)


# Whole meshes, targeted modifiers and non-UV data transfer.
_add('mesh.combine_objects', 'Combine Mesh Objects', 'Mesh', 'object.join', requires='two_mesh',
     section=('Combine',), maya=('CombinePolygons',),
     difference='Join selected editable meshes into the active object; uses its transform and material slots.')
for name, value, label in (('selection', 'SELECTED', 'Separate Selection'),
                           ('material', 'MATERIAL', 'Separate by Material'),
                           ('loose', 'LOOSE', 'Separate Loose Parts')):
    _edit('mesh.separate_' + name, label, 'mesh.separate', category='Mesh',
          section=('Combine',), kwargs={'type': value}, maya=('SeparatePolygon',),
          difference='Blender Edit Mesh separation; loose parts are connected shells, not Maya DAG history.')
for name, operation, label, identity, reverse in (
        ('union', 'UNION', 'Union (Active + Other)', 'PolygonBooleanUnion', False),
        ('difference', 'DIFFERENCE', 'Difference (Active - Other)', 'PolygonBooleanDifference', False),
        ('intersection', 'INTERSECT', 'Intersection', 'PolygonBooleanIntersection', False),
        ('difference_reverse', 'DIFFERENCE', 'Difference (Other - Active)', 'PolygonBooleanDifferenceBA', True)):
    _add('mesh.boolean_' + name, label, 'Mesh', 'axismeld.m3_mesh_boolean',
         requires='two_mesh', section=('Booleans',), maya=(identity,),
         kwargs={'operation': operation, 'reverse': reverse},
         difference='Exactly two selected meshes; add an Exact Boolean with an explicit operand. '
                    'Original objects and visibility remain; reverse modifies the other mesh. '
                    'Modifier evaluation is checked before committing one undo step.')
for name, operator, props, identity, requires in (
        ('fill_holes', 'mesh.fill_holes', {'sides': 0}, 'FillHole', 'edges'),
        ('reduce', 'mesh.decimate', {'ratio': .5}, 'ReducePolygon', 'faces'),
        ('smooth_subdivide', 'mesh.subdivide', {'number_cuts': 1, 'smoothness': 1.0}, 'SmoothPolygon', 'edges'),
        ('unsubdivide', 'mesh.unsubdivide', {'iterations': 2}, 'UnsmoothPolygon', 'edges'),
        ('triangulate', 'mesh.quads_convert_to_tris', {'quad_method': 'BEAUTY', 'ngon_method': 'BEAUTY'}, 'Triangulate', 'faces'),
        ('quadrangulate', 'mesh.tris_convert_to_quads', {}, 'Quadrangulate', 'faces'),
        ('symmetrize', 'mesh.symmetrize', {'direction': 'NEGATIVE_X'}, 'Symmetrize', 'vertices')):
    _edit('mesh.' + name, name.replace('_', ' ').title(), operator, category='Mesh',
          section=('Remesh',), kwargs=props, maya=(identity,), requires=requires)
_add('mesh.remesh_voxel', 'Voxel Remesh', 'Mesh', 'object.voxel_remesh', requires='mesh',
     section=('Remesh',), maya=('PolyRemesh',),
     difference='Destructive Blender voxel remeshing using the mesh voxel-size setting; attributes may be lost.')
_add('mesh.quad_remesh', 'QuadriFlow Remesh', 'Mesh', 'object.quadriflow_remesh', requires='mesh',
     section=('Remesh',), maya=('PolyRetopo',), invoke=True,
     kwargs={'mode': 'FACES', 'target_faces': 2000, 'use_preserve_sharp': True,
             'use_preserve_boundary': True},
     difference='Blender QuadriFlow, not Maya Retopologize. Opens native parameters and requires valid manifold input.')
for name, label, kind, identity in (
        ('reduce_modifier', 'Decimate Modifier (50%)', 'decimate', 'ReducePolygon'),
        ('remesh_modifier', 'Voxel Remesh Modifier', 'remesh', 'PolyRemesh'),
        ('subdivision_modifier', 'Subdivision Surface Modifier', 'subsurf', 'SmoothPolygon'),
        ('mirror_geometry', 'Mirror Geometry on X', 'mirror', 'MirrorPolygonGeometry'),
        ('modifier_array_legacy', 'Array Modifier (2 Copies)', 'array', ''),
        ('modifier_solidify', 'Solidify Modifier', 'solidify', ''),
        ('modifier_wireframe', 'Wireframe Modifier', 'wireframe', ''),
        ('modifier_weld', 'Weld Modifier', 'weld', ''),
        ('modifier_skin', 'Skin Modifier', 'skin', ''),
        ('modifier_build', 'Build Modifier', 'build', '')):
    _add('mesh.' + name, label, 'Mesh', 'axismeld.m3_mesh_modifier_' + kind,
         requires='mesh', section=('Modifiers',), maya=(identity,) if identity else (),
         difference='Add one configured Blender modifier to the active editable mesh; '
                    'geometry evaluation and input compatibility are checked. Parameters remain editable in Modifiers.')
for name, operator, props, requires in (
        ('cleanup_loose', 'mesh.delete_loose', {}, 'vertices'),
        ('cleanup_degenerate', 'mesh.dissolve_degenerate', {'threshold': .0001}, 'edges'),
        ('cleanup_limited_dissolve', 'mesh.dissolve_limited', {'angle_limit': pi / 36}, 'edges'),
        ('cleanup_planar', 'mesh.face_make_planar', {'factor': 1.0}, 'faces'),
        ('split_nonplanar', 'mesh.vert_connect_nonplanar', {}, 'faces'),
        ('split_concave', 'mesh.vert_connect_concave', {}, 'faces')):
    _edit('mesh.' + name, name.replace('_', ' ').title(), operator, category='Mesh',
          section=('Clean Up',), requires=requires, kwargs=props, maya=('CleanupPolygon',),
          difference='One explicit Blender cleanup operation; does not implement all Maya Cleanup checks.')
for suffix, label, data_type in (
        ('normals', 'Transfer Custom Normals', 'CUSTOM_NORMAL'),
        ('point_colors', 'Transfer Point Colors', 'COLOR_VERTEX'),
        ('corner_colors', 'Transfer Corner Colors', 'COLOR_CORNER'),
        ('sharp_edges', 'Transfer Sharp Edges', 'SHARP_EDGE'),
        ('crease', 'Transfer Edge Creases', 'CREASE')):
    _add('mesh.transfer_' + suffix, label, 'Mesh', 'object.data_transfer', requires='two_mesh',
         section=('Transfer',), maya=('TransferAttributes',),
         kwargs={'data_type': data_type, 'use_create': True, 'use_reverse_transfer': False},
         difference='Transfer from active source to selected mesh destinations using Blender nearest-element mappings; no UV transfer.')
_add('mesh.transfer_materials', 'Link Material Slots', 'Mesh', 'object.make_links_data',
     requires='two_mesh', section=('Transfer',), kwargs={'type': 'MATERIAL'},
     maya=('TransferShadingSets',),
     difference='Link active mesh material slots to other selected meshes; no spatial matching of Maya per-face shading sets.')
for name, value in (('selected', 'SELECTED'), ('reverse', 'REVERSE'), ('random', 'RANDOMIZE'),
                     ('cursor', 'CURSOR_DISTANCE'), ('material', 'MATERIAL')):
    _edit('mesh.sort_' + name, 'Sort Elements: ' + name.title(), 'mesh.sort_elements', category='Mesh',
          section=('Element Order',), kwargs={'type': value, 'elements': {'VERT', 'EDGE', 'FACE'}},
          difference='Blender index sorting; does not transfer vertex correspondence from another mesh.')

# Topology actions; native macros own modal completion and their own undo.
_modal_difference = ('Native Blender macro: Esc may cancel only movement while retaining new geometry; '
                     'one Undo removes the operation. Modal launch is not recorded in Recent.')
for name, label, operator, transform, requires, identity in (
        ('extrude_region', 'Extrude Region', 'mesh.extrude_region_move', 'TRANSFORM_OT_translate', 'vertices', 'PolyExtrude'),
        ('extrude_faces_individual', 'Extrude Individual Faces', 'mesh.extrude_faces_move', 'TRANSFORM_OT_shrink_fatten', 'faces', 'PolyExtrude'),
        ('extrude_along_normals', 'Extrude Along Normals', 'mesh.extrude_region_shrink_fatten', 'TRANSFORM_OT_shrink_fatten', 'faces', 'PolyExtrude'),
        ('extrude_edges', 'Extrude Edges', 'mesh.extrude_edges_move', 'TRANSFORM_OT_translate', 'edges', 'PolyExtrude'),
        ('extrude_vertices', 'Extrude Vertices', 'mesh.extrude_vertices_move', 'TRANSFORM_OT_translate', 'vertices', 'PolyExtrude'),
        ('extrude_manifold', 'Extrude Manifold', 'mesh.extrude_manifold', 'TRANSFORM_OT_translate', 'faces', 'SmartExtrude')):
    _edit('mesh.' + name, label, operator, section=('Extrude',), requires=requires,
          kwargs={transform: {'release_confirm': False}}, invoke=True, maya=(identity,),
          difference=_modal_difference, **({'key': 'E', 'ctrl': True} if name == 'extrude_region' else {}))
for name, affect, requires, identity in (('edges', 'EDGES', 'edges', 'BevelPolygon'),
                                         ('vertices', 'VERTICES', 'vertices', 'ChamferVertex')):
    _edit('mesh.bevel_' + name, 'Bevel ' + name.title(), 'mesh.bevel', requires=requires,
          section=('Components',), kwargs={'affect': affect}, invoke=True, maya=(identity,),
          difference='Blender bevel profile, overlap and miter behavior; interactive native operator.',
          **({'key': 'B', 'ctrl': True} if name == 'edges' else {}))
for name, label, operator, requires, props, identity in (
        ('bridge', 'Bridge Edge Loops', 'mesh.bridge_edge_loops', 'two_edges', {}, 'BridgeOrFill'),
        ('circularize', 'Circularize', 'mesh.circularize', 'two_vertices', {}, 'PolyCircularize'),
        ('subdivide', 'Subdivide', 'mesh.subdivide', 'edges', {'number_cuts': 1}, 'SubdividePolygon'),
        ('collapse', 'Collapse Edges', 'mesh.edge_collapse', 'edges', {}, 'PolygonCollapse'),
        ('connect_path', 'Connect Vertex Path', 'mesh.vert_connect_path', 'two_vertices', {}, 'ConnectComponents'),
        ('connect_pairs', 'Connect Vertex Pairs', 'mesh.vert_connect', 'two_vertices', {}, 'ConnectComponents'),
        ('detach_selection', 'Split Selection', 'mesh.split', 'vertices', {}, 'DetachComponent'),
        ('edge_split', 'Split Selected Edges', 'mesh.edge_split', 'edges', {'type': 'EDGE'}, 'DetachComponent'),
        ('merge_distance', 'Merge by Distance', 'mesh.remove_doubles', 'two_vertices', {'threshold': .0001}, 'PolyMerge')):
    _edit('mesh.' + name, label, operator, section=('Components',), requires=requires,
          kwargs=props, maya=(identity,))
for name, value in (('center', 'CENTER'), ('cursor', 'CURSOR'), ('first', 'FIRST'),
                     ('last', 'LAST'), ('collapse', 'COLLAPSE')):
    _edit('mesh.merge_' + name, 'Merge at ' + name.title(), 'mesh.merge', section=('Merge',),
          requires='merge_history' if name in ('first', 'last') else 'two_vertices',
          kwargs={'type': value}, maya=('MergeToCenter',) if name == 'center' else ('PolyMerge',),
          difference='Blender merge target; First/Last require visible selected vertex history.')
for name, label, operator, requires, props, identity in (
        ('average_vertices', 'Smooth Vertices', 'mesh.vertices_smooth', 'vertices', {'factor': .5}, 'AverageVertex'),
        ('average_laplacian', 'Laplacian Smooth Vertices', 'mesh.vertices_smooth_laplacian', 'vertices', {}, ''),
        ('edge_flow', 'Relax Edge Loops', 'mesh.relax_edge_loops', 'two_edges', {}, 'PolyEditEdgeFlow'),
        ('space_loops', 'Space Edge Loops Evenly', 'mesh.space_edge_loops_evenly', 'two_edges', {}, ''),
        ('flatten', 'Flatten', 'mesh.flatten', 'two_vertices', {}, ''),
        ('poke_faces', 'Poke Faces', 'mesh.poke', 'faces', {}, 'PokePolygon'),
        ('duplicate_faces', 'Duplicate Faces in Place', 'mesh.duplicate', 'faces', {}, 'DuplicateFace'),
        ('extract_faces', 'Extract Faces (Separate)', 'mesh.separate', 'faces', {'type': 'SELECTED'}, 'ExtractFace'),
        ('make_edge_face', 'Make Edge / Face', 'mesh.edge_face_add', 'two_vertices', {}, ''),
        ('fill', 'Fill', 'mesh.fill', 'edges', {}, 'FillHole'),
        ('grid_fill', 'Grid Fill', 'mesh.fill_grid', 'two_edges', {}, ''),
        ('beautify_fill', 'Beautify Faces', 'mesh.beautify_fill', 'faces', {}, ''),
        ('intersect_faces', 'Intersect Faces', 'mesh.intersect', 'faces', {}, ''),
        ('split_by_edges', 'Split Faces by Edges', 'mesh.face_split_by_edges', 'edges', {}, ''),
        ('dissolve_vertices', 'Dissolve Vertices', 'mesh.dissolve_verts', 'vertices', {}, ''),
        ('dissolve_edges', 'Dissolve Edges', 'mesh.dissolve_edges', 'edges', {}, 'DeletePolyElements'),
        ('dissolve_faces', 'Dissolve Faces', 'mesh.dissolve_faces', 'faces', {}, ''),
        ('delete_edge_loop', 'Delete Edge Loop', 'mesh.delete_edgeloop', 'edges', {}, 'DeletePolyElements')):
    _edit('mesh.' + name, label, operator, section=('Topology',), requires=requires,
          kwargs=props, maya=(identity,) if identity else ())
for name, ccw, identity, key in (('cw', False, 'PolySpinEdgeForward', 'RIGHT_ARROW'),
                                ('ccw', True, 'PolySpinEdgeBackward', 'LEFT_ARROW')):
    _edit('mesh.edge_rotate_' + name, 'Rotate Edge ' + name.upper(), 'mesh.edge_rotate',
          section=('Edges',), requires='edges', kwargs={'use_ccw': ccw}, maya=(identity, 'FlipTriangleEdge'),
          key=key, ctrl=True, alt=True,
          difference='Rotate selected manifold edges shared by exactly two faces; Blender edge-spin direction.')
for name, label, operator, requires, props in (
        ('inset', 'Inset Faces', 'mesh.inset', 'faces', {}),
        ('solidify_faces', 'Solidify Faces', 'mesh.solidify', 'faces', {'thickness': .1}),
        ('wireframe_faces', 'Wireframe Faces', 'mesh.wireframe', 'faces', {'thickness': .02}),
        ('spin', 'Spin / Wedge', 'mesh.spin', 'edges', {'angle': pi / 2, 'steps': 9}),
        ('screw', 'Screw', 'mesh.screw', 'edges', {'steps': 9, 'turns': 1}),
        ('rip', 'Rip Vertices', 'mesh.rip_move', 'vertices', {'MESH_OT_rip': {'use_fill': False}}),
        ('rip_fill', 'Rip Vertices and Fill', 'mesh.rip_move', 'vertices', {'MESH_OT_rip': {'use_fill': True}}),
        ('rip_extend', 'Rip Vertices and Extend', 'mesh.rip_edge_move', 'vertices', {})):
    _edit('mesh.' + name, label, operator, section=('Interactive Topology',), requires=requires,
          kwargs=props, invoke=True, maya=('WedgePolygon',) if name == 'spin' else (),
          difference=_modal_difference if name.startswith('rip') else
          'Native Blender interaction/parameters; Spin uses the current Cursor and axis, not a Maya selected-edge pivot.')
for name, operation in (('union', 'UNION'), ('difference', 'DIFFERENCE'), ('intersection', 'INTERSECT')):
    _edit('mesh.boolean_faces_' + name, 'Face Boolean: ' + name.title(), 'mesh.intersect_boolean',
          section=('Face Boolean',), requires='faces', kwargs={'operation': operation, 'solver': 'EXACT'},
          difference='Edit Mesh Boolean between selected and unselected face regions; not object operands.')
_edit('mesh.project_cut', 'Knife Project', 'mesh.knife_project', requires='face_projection',
      section=('Projected Cutting',), kwargs={'cut_through': False}, maya=('SplitMeshWithProjectedCurve',),
      difference='Project wire/boundary edges of selected non-Edit objects through the active view; '
                 'does not create Maya curve-on-mesh dependency data.')

# Registered persistent tools are distinct from immediately executing mesh operators.
for name, label, tool, identity in (
        ('poly_build', 'Poly Build (Quad Draw Adaptation)', 'poly_build', 'QuadDrawTool'),
        ('knife', 'Knife (Multi-Cut Adaptation)', 'knife', 'MultiCutTool'),
        ('loopcut', 'Loop Cut', 'loop_cut', 'SplitEdgeRingTool'),
        ('offset_loop', 'Offset Edge Loop', 'offset_edge_loop_cut', 'DuplicateEdges'),
        ('edge_slide', 'Edge Slide', 'edge_slide', 'SlideEdgeTool'),
        ('vertex_slide', 'Vertex Slide', 'vertex_slide', ''),
        ('spin', 'Spin Tool', 'spin', ''),
        ('inset', 'Inset Faces Tool', 'inset_faces', ''),
        ('bevel', 'Bevel Tool', 'bevel', ''),
        ('extrude', 'Extrude Region Tool', 'extrude_region', ''),
        ('extrude_manifold', 'Extrude Manifold Tool', 'extrude_manifold', ''),
        ('extrude_normals', 'Extrude Along Normals Tool', 'extrude_along_normals', ''),
        ('extrude_individual', 'Extrude Individual Faces Tool', 'extrude_individual', ''),
        ('bisect', 'Bisect Tool', 'bisect', '')):
    _add('tool.mesh_' + name, label, 'Mesh Tools', 'wm.tool_set_by_id', modes=_M,
         requires='mesh', section=('Tools',), kwargs={'name': 'builtin.' + tool}, undo=False,
         replayable=False, maya=(identity, 'AppendToPolygonTool') if name == 'poly_build' else
         (identity,) if identity else (),
         difference='Activate the registered Blender tool; subsequent viewport strokes perform edits. '
                    'Poly Build is not the complete Maya Quad Draw/Append/Target Weld workflow.',
         **({'key': 'Q' if name == 'poly_build' else 'X', 'ctrl': True, 'shift': True}
            if name in ('poly_build', 'knife') else {}))
for name, label, operator, requires, props in (
        ('knife', 'Knife Cut', 'mesh.knife_tool', 'mesh', {'use_occlude_geometry': True, 'only_selected': False}),
        ('loopcut', 'Insert Loop Cut and Slide', 'mesh.loopcut_slide', 'mesh', {'TRANSFORM_OT_edge_slide': {'release_confirm': False}}),
        ('offset_loop', 'Offset Edge Loops and Slide', 'mesh.offset_edge_loops_slide', 'edges', {}),
        ('edge_slide', 'Slide Edges', 'transform.edge_slide', 'edges', {'release_confirm': False}),
        ('vertex_slide', 'Slide Vertices', 'transform.vert_slide', 'vertices', {'release_confirm': False}),
        ('crease_edges', 'Edge Crease', 'transform.edge_crease', 'edges', {}),
        ('crease_vertices', 'Vertex Crease', 'transform.vert_crease', 'vertices', {}),
        ('bisect', 'Bisect', 'mesh.bisect', 'mesh', {})):
    _edit('mesh.interactive_' + name, label, operator, category='Mesh Tools',
          section=('Immediate Tools',), requires=requires, kwargs=props, invoke=True,
          maya=('PolyCreaseTool',) if name == 'crease_edges' else (),
          difference='Native Blender modal operation; input and cancellation belong to the child operator, not the opening menu.')
_add('display.modeling_toolbar', 'Show Modeling Toolbar', 'Mesh Tools', 'axismeld.m3_modeling_toolbar',
     modes=('OBJECT', 'EDIT_MESH'), section=('Tools',), undo=False, replayable=False,
     maya=('ToggleModelingToolkit',),
     difference='Toggle the current Blender 3D View toolbar; does not reproduce the Maya Modeling Toolkit panel.')

# Normals and colors use their own mesh data domains, not a generic Shade Smooth alias.
for name, label, operator, props, requires, identity in (
        ('conform_outside', 'Recalculate Outside', 'mesh.normals_make_consistent', {'inside': False}, 'faces', 'ConformPolygonNormals'),
        ('conform_inside', 'Recalculate Inside', 'mesh.normals_make_consistent', {'inside': True}, 'faces', ''),
        ('reverse', 'Reverse Normals', 'mesh.flip_normals', {}, 'faces', 'ReversePolygonNormals'),
        ('set_from_faces', 'Set Normals from Faces', 'mesh.set_normals_from_faces', {}, 'faces', 'SetToFaceNormals'),
        ('harden_edges', 'Mark Sharp Edges', 'mesh.mark_sharp', {'clear': False}, 'edges', 'PolygonHardenEdge'),
        ('soften_edges', 'Clear Sharp Edges', 'mesh.mark_sharp', {'clear': True}, 'edges', 'PolygonSoftenEdge'),
        ('harden_by_angle', 'Set Sharpness by Angle', 'mesh.set_sharpness_by_angle', {'angle': pi / 6}, 'edges', 'PolygonSoftenHarden'),
        ('merge', 'Merge Custom Normals', 'mesh.merge_normals', {}, 'vertices', ''),
        ('split', 'Split Custom Normals', 'mesh.split_normals', {}, 'vertices', ''),
        ('smooth_vectors', 'Smooth Normal Vectors', 'mesh.smooth_normals', {}, 'vertices', ''),
        ('copy_vector', 'Copy Normal Vector', 'mesh.normals_tools', {'mode': 'COPY'}, 'vertices', ''),
        ('paste_vector', 'Paste Normal Vector', 'mesh.normals_tools', {'mode': 'PASTE'}, 'vertices', ''),
        ('reset_vectors', 'Reset Normal Vectors', 'mesh.normals_tools', {'mode': 'RESET'}, 'vertices', '')):
    _edit('normals.' + name, label, operator, category='Mesh Display', section=('Normals',),
          kwargs=props, requires=requires, maya=(identity,) if identity else (),
          replayable=name != 'copy_vector', undo=name != 'copy_vector',
          difference='Blender split/custom normals and sharp-edge attributes; sharp flags do not override '
                     'all custom normals, and split/merge are not Maya persistent normal locks.')
for name, value in (('custom', 'CUSTOM_NORMAL'), ('area', 'FACE_AREA'), ('corner', 'CORNER_ANGLE')):
    _edit('normals.average_' + name, 'Average Normals: ' + name.title(), 'mesh.average_normals',
          category='Mesh Display', section=('Average Normals',), kwargs={'average_type': value},
          maya=('AveragePolygonNormals',), difference='Blender custom-normal, face-area or corner-angle weighting.')
for name, operator in (('rotate', 'transform.rotate_normal'), ('point_to_target', 'mesh.point_normals')):
    _edit('normals.' + name, name.replace('_', ' ').title(), operator, category='Mesh Display',
          section=('Edit Normals',), invoke=True, maya=('PolygonNormalEditTool', 'SetVertexNormal'),
          difference='Native Blender custom-normal interaction; not Maya per-vertex normal locking.')
for name, value in (('weak', 'WEAK'), ('medium', 'MEDIUM'), ('strong', 'STRONG')):
    _edit('normals.face_strength_' + name, 'Face Strength: ' + name.title(), 'mesh.mod_weighted_strength',
          category='Mesh Display', section=('Face Strength',), requires='faces',
          kwargs={'set': True, 'face_strength': value})
for name, object_op, mesh_op in (('smooth', 'object.shade_smooth', 'mesh.faces_shade_smooth'),
                                 ('flat', 'object.shade_flat', 'mesh.faces_shade_flat')):
    _specs.append(CommandSpec('normals.shade_' + name, 'Shade ' + name.title(), 'Mesh Display',
        (NativeCall(object_op), NativeCall(mesh_op, _M)), section=('Shading',), requires='mesh',
        classification='blender', source=_SOURCE['Mesh Display'],
        difference='Set object faces or selected Edit Mesh faces shading; does not subdivide geometry.'))
_add('normals.shade_by_angle', 'Shade Smooth by Angle', 'Mesh Display', 'object.shade_smooth_by_angle',
     section=('Shading',), requires='mesh', kwargs={'angle': pi / 6, 'keep_sharp_edges': True},
     difference='Native mesh smooth flags and angle-derived sharp edges; independent of Essentials assets.')
_add('normals.shade_auto_smooth', 'Auto Smooth Modifier', 'Mesh Display', 'object.shade_auto_smooth',
     section=('Shading',), requires='mesh', kwargs={'use_auto_smooth': True, 'angle': pi / 6},
     difference='Native Smooth by Angle geometry-node modifier; requires the bundled Essentials asset.')
for name, kind in (('weighted_modifier', 'weighted_normal'), ('edit_modifier', 'normal_edit')):
    _add('normals.' + name, name.replace('_', ' ').title(), 'Mesh Display',
         'axismeld.m3_mesh_modifier_' + kind, requires='mesh', section=('Normal Modifiers',),
         difference='One configured Blender normal modifier; does not provide Maya normal lock state.')
for name, label, attribute in (
        ('vertex_normals', 'Show Vertex Normals', 'show_vertex_normals'),
        ('split_normals', 'Show Split Normals', 'show_split_normals'),
        ('face_normals', 'Show Face Normals', 'show_face_normals'),
        ('edge_length', 'Show Edge Length', 'show_extra_edge_length'),
        ('edge_angle', 'Show Edge Angle', 'show_extra_edge_angle'),
        ('face_area', 'Show Face Area', 'show_extra_face_area'),
        ('face_angle', 'Show Face Corner Angles', 'show_extra_face_angle')):
    _add('display.' + name, label, 'Mesh Display', 'axismeld.m3_mesh_overlay',
         modes=('OBJECT', 'EDIT_MESH'), section=('Viewport Analysis',),
         kwargs={'attribute': attribute}, undo=False, replayable=False,
         maya={'vertex_normals': ('ToggleVertexNormalDisplay',),
               'face_normals': ('ToggleFaceNormalDisplay',)}.get(name, ()),
         difference='Toggle one current 3D View overlay; mesh measurements/normals are visible in Edit Mesh.')
_add('display.normal_length', 'Normal Display Length...', 'Mesh Display', 'axismeld.m3_normal_length',
     modes=('OBJECT', 'EDIT_MESH'), section=('Viewport Analysis',), invoke=True, undo=False,
     maya=('ChangeNormalSize',),
     difference='Change current 3D View normal overlay length only.')
for name, label, attribute, identities, difference in (
        ('crease_marks', 'Show Edge and Vertex Creases', 'show_edge_crease',
         ('ToggleCreaseEdges', 'ToggleCreaseVertices'),
         'Blender Edit Mesh crease overlay controls edge and vertex creases together; Maya has separate switches.'),
        ('sharp_edges', 'Show Sharp Edge Colors', 'show_edge_sharp',
         ('TogglePolyDisplayHardEdgesColor',),
         'Color Blender explicitly marked sharp edges in Edit Mesh; does not isolate hard/soft edges or alter normals.'),
        ('face_centers', 'Show Face Centers', 'show_face_center',
         ('TogglePolygonFaceCenters',),
         'Blender face dots are visible with face selection in non-X-Ray solid shading; no Maya Object-mode dots.'),
        ('component_indices', 'Show Selected Component Indices', 'show_extra_indices',
         ('ToggleVertIDs', 'ToggleEdgeIDs', 'ToggleFaceIDs'),
         'One Blender Edit Mesh switch shows selected vertex/edge/face indices together; indices are not persistent Maya component identities.')):
    _add('display.' + name, label, 'Mesh Display', 'axismeld.m3_mesh_overlay',
         modes=('EDIT_MESH',), requires='mesh', section=('Viewport Analysis',),
         kwargs={'attribute': attribute}, undo=False, replayable=False, maya=identities,
         source=_SOURCE['Mesh Display'] + '; native rna_space.cc:5495-5583; Maya buildDisplayMenu.mel:1786-1872',
         difference=difference)
_add('display.distortion_analysis', 'Show Face Distortion Analysis', 'Mesh Display',
     'axismeld.m3_mesh_distortion', modes=('EDIT_MESH',), requires='mesh',
     section=('Viewport Analysis',), undo=False, replayable=False,
     maya=('TogglePolyNonPlanarFaceDisplay',),
     source=_SOURCE['Mesh Display'] + '; native space_view3d.py:7453-7481; Maya buildDisplayMenu.mel:1878',
     difference='Blender face-distortion analysis colors non-planarity by its native angular thresholds; '
                'not Maya binary non-planar highlighting. Uses the current scene analysis thresholds and requires non-translucent X-Ray.')
for name, operator in (('rotate', 'mesh.colors_rotate'), ('reverse', 'mesh.colors_reverse')):
    _edit('mesh.colors_' + name, name.title() + ' Face Colors', operator, category='Mesh Display',
          section=('Vertex Colors',), requires='faces',
          difference='Rotate/reverse selected face-corner color data, not UV coordinates.')
for name, label, identity, invoke in (
        ('add', 'Create Color Attribute...', 'CreateEmptySet', True),
        ('remove', 'Delete Active Color Attribute', 'DeleteCurrentSet', False),
        ('rename', 'Rename Active Color Attribute...', 'RenameCurrentSet', True),
        ('active', 'Choose Active Color Attribute...', 'OpenColorSetEditor', True),
        ('set', 'Set Color Value...', 'PolygonApplyColor', True)):
    _add('color.attribute_' + name if name != 'set' else 'color.set_value', label, 'Mesh Display',
         'axismeld.m3_color_' + name, requires='mesh', section=('Color Attributes',),
         modes=('OBJECT', 'EDIT_MESH') if name == 'set' else ('OBJECT',),
         invoke=invoke, maya=(identity,),
         difference='Blender POINT/CORNER color attributes, not Maya per-instance color sets. '
                    'Management uses Object mode; Set Color affects the active object or selected Edit-domain elements.')
_add('color.display_active', 'Display Active Vertex Colors', 'Mesh Display', 'axismeld.m3_color_display',
     modes=('OBJECT', 'EDIT_MESH'), requires='mesh', section=('Vertex Colors',), undo=False,
     replayable=False, maya=('ToggleDisplayColorsAttr',),
     difference='Current solid viewport color source toggles VERTEX/MATERIAL; not Maya color-material blend modes.')
_add('color.attribute_convert', 'Convert Active Color Attribute...', 'Mesh Display',
     'geometry.color_attribute_convert', requires='mesh', section=('Color Attributes',),
     invoke=True, maya=('ModifyCurrentSet',),
     difference='Convert the active Blender color attribute between POINT/CORNER and FLOAT_COLOR/BYTE_COLOR; '
                'not Maya color-set representation/per-instance options.')
_add('color.paint_mode', 'Enter Vertex Paint (Blender)', 'Mesh Display', 'object.mode_set',
     requires='mesh', section=('Vertex Colors',), kwargs={'mode': 'VERTEX_PAINT'},
     undo=False, replayable=False, maya=('PaintVertexColorTool',),
     difference='Object-mode entry to Blender Vertex Paint. Leaves the supported modeling-hotbox context; '
                'paint tools/keymaps and the complete Maya painting workflow are not adapted.')
for domain in ('edge', 'face'):
    for clear in (False, True):
        _edit('display.freestyle_' + domain + ('_clear' if clear else '_mark'),
              ('Clear' if clear else 'Mark') + ' Freestyle ' + domain.title(),
              'mesh.mark_freestyle_' + domain, category='Mesh Display', section=('Data Marks',),
              requires='edges' if domain == 'edge' else 'faces', kwargs={'clear': clear})

SPECS = tuple(_specs)
del _specs

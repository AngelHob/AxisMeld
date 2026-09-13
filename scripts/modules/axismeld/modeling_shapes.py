# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed native curve, surface and deformation capabilities, with explicit differences."""
from .modeling_schema import op
from dataclasses import replace

_specs = []


def _curve(identifier, label, operator, *, surface=False, section='Control Points', maya=(),
           difference='', kwargs=None, invoke=False):
    category = 'Surfaces' if surface else 'Curves'
    prefix = 'surface.' if surface else 'curve.'
    _specs.append(op(prefix + identifier, label, category, operator,
                     modes=('EDIT_SURFACE',) if surface else ('EDIT_CURVE',),
                     kwargs=kwargs, invoke=invoke, section=(section,), maya=maya,
                     difference=difference or 'Native Blender control-point operation; NURBS parameterization follows Blender.',
                     source='scripts/startup/bl_ui/space_view3d.py:5317; source/blender/editors/curve/'))


for _surface in (False, True):
    _curve('duplicate', 'Duplicate Control Points', 'curve.duplicate_move', surface=_surface,
           invoke=True, maya=('DuplicateNURBSPatches',) if _surface else ('DuplicateCurve',))
    _curve('attach_segments', 'Connect Compatible Boundaries' if _surface else 'Connect Endpoints',
           'curve.make_segment', surface=_surface, section='Topology',
           maya=('AttachSurfaces', 'AttachSurfaceWithoutMoving') if _surface else ('AttachCurve',),
           difference='Connect selected compatible endpoints/control rows within the edit object; no Maya tangent-alignment or cross-object rebuild.')
    _curve('detach', 'Split Selected', 'curve.split', surface=_surface, section='Topology',
           maya=('DetachSurfaces',) if _surface else ('DetachCurve',))
    _curve('separate', 'Separate Selected to Object', 'curve.separate', surface=_surface, section='Topology')
    _curve('open_close', 'Toggle Cyclic U' if _surface else 'Toggle Cyclic', 'curve.cyclic_toggle',
           surface=_surface, kwargs={'direction': 'CYCLIC_U'}, section='Topology',
           maya=('OpenCloseSurfaces',) if _surface else ('OpenCloseCurve',))
    _curve('extrude', 'Extrude Control Row' if _surface else 'Extend Control Points',
           'curve.extrude_move', surface=_surface, invoke=True, section='Construct',
           maya=() if _surface else ('AddPointsTool', 'ExtendCurve'),
           difference='Interactive control-point extrusion; not a prescribed-length extension or a profile swept along a path.')
    _curve('subdivide', 'Subdivide Control Rows' if _surface else 'Subdivide Control Points',
           'curve.subdivide', surface=_surface, kwargs={'number_cuts': 1}, section='Topology',
           maya=('InsertIsoparms',) if _surface else ('InsertKnot',),
           difference='Blender control-net subdivision; not exact shape-preserving knot/isoparm insertion.')
    _curve('reverse', 'Reverse Direction', 'curve.switch_direction', surface=_surface,
           section='Topology', maya=('ReverseSurfaceDirection',) if _surface else ('ReverseCurve',),
           difference='Reverse native selected spline direction; surface U/V are not independent Maya direction modes.')
    _curve('smooth', 'Smooth Control Points', 'curve.smooth', surface=_surface,
           maya=() if _surface else ('SmoothCurve',))
    _curve('delete_points', 'Delete Selected Control Points', 'curve.delete', surface=_surface,
           kwargs={'type': 'VERT'}, section='Topology')

_curve('open_close_v', 'Toggle Cyclic V', 'curve.cyclic_toggle', surface=True,
       kwargs={'direction': 'CYCLIC_V'}, section='Topology', maya=('OpenCloseSurfaces',))
_curve('revolve', 'Spin Selected NURBS Row', 'curve.spin', surface=True, section='Construct',
       kwargs={'center': (0.0, 0.0, 0.0), 'axis': (0.0, 0.0, 1.0)}, maya=('Revolve',),
       difference='Native full rotation of a selected NURBS control row about world origin/Z; select a valid open row. Adjust Last Operation exposes axis/center.')
for _key, _label, _type, _maya in (
        ('auto', 'Automatic Handles', 'AUTOMATIC', ('BezierPresetBezier', 'BezierSetAnchorSmooth')),
        ('vector', 'Vector Corner Handles', 'VECTOR', ('BezierPresetCorner',)),
        ('aligned', 'Aligned Handles', 'ALIGNED', ()),
        ('free', 'Free Handles', 'FREE_ALIGN', ('BezierPresetBezierCorner', 'BezierSetAnchorBroken', 'BezierSetAnchorUneven'))):
    _curve('handle_' + _key, _label, 'curve.handle_type_set', kwargs={'type': _type},
           section='Bezier Handles', maya=_maya,
           difference='Bezier handle constraint; Blender aligned/free handles do not reproduce all Maya anchor-length and NURBS CV-hardness rules.')
for _type in ('BEZIER', 'NURBS', 'POLY'):
    _curve('spline_' + _type.lower(), 'Convert Spline to ' + _type.title(), 'curve.spline_type_set',
           kwargs={'type': _type}, section='Spline Type', difference='Spline-type conversion, not fitting or shape-preserving rebuilding.')
for _suffix in ('tilt', 'radius', 'weight'):
    _curve('smooth_' + _suffix, 'Smooth ' + _suffix.title(), 'curve.smooth_' + _suffix)
_curve('tilt', 'Tilt Selected', 'transform.tilt', invoke=True)
_curve('clear_tilt', 'Clear Tilt', 'curve.tilt_clear')
_curve('recalculate_handles', 'Recalculate Curve Normals', 'curve.normals_make_consistent')
_curve('radius', 'Set Point Radius', 'curve.radius_set', kwargs={'radius': 1.25})
_curve('weight', 'Set NURBS Weight', 'curve.spline_weight_set', kwargs={'weight': 0.75})
_curve('decimate', 'Decimate Bezier Points', 'curve.decimate', kwargs={'ratio': 0.5}, section='Topology')
_curve('dissolve_points', 'Dissolve Selected Points', 'curve.dissolve_verts', section='Topology')
_curve('delete_segments', 'Delete Selected Segments', 'curve.delete', kwargs={'type': 'SEGMENT'}, section='Topology')
_specs.append(op('curve.pen', 'Curve Pen Tool', 'Curves', 'wm.tool_set_by_id',
                 modes=('EDIT_CURVE',), kwargs={'name': 'builtin.pen'}, undo=False, replayable=False,
                 section=('Construct',), maya=('CurveEditTool', 'CVCurveTool', 'CreateBezierCurveTool'),
                 difference='First create a Curve and enter Edit; choose NURBS for BPoint CV extension or Bezier for anchor/handle editing. Native Pen extends selected spline endpoints; no automatic new-object lifecycle, EP interpolation or arc solver.',
                 source='scripts/startup/bl_ui/space_toolsystem_toolbar.py:1357; source/blender/editors/curve/editcurve_pen.cc:936'))
_specs.append(op('curve.draw', 'Draw Freehand Curve', 'Curves', 'wm.tool_set_by_id',
                 modes=('EDIT_CURVE',), kwargs={'name': 'builtin.draw'}, undo=False, replayable=False,
                 section=('Construct',), maya=('PencilCurveTool',),
                 difference='First create a Curve and enter Edit. Native Draw creates a freehand Bezier fit or Poly spline using native paint settings and error tolerance; it does not create a Maya EP-interpolated NURBS curve. Strokes own confirmation and undo.',
                 source='scripts/startup/bl_ui/space_toolsystem_toolbar.py:1317; source/blender/editors/curve/editcurve_paint.cc:810,1010,1211'))
_specs.append(op('surface.sweep_profile', 'Sweep Selected Curve Profile', 'Surfaces',
                 'axismeld.m3_curve_geometry', kwargs={'kind': 'PROFILE'}, requires='two_objects',
                 section=('Construct',), maya=('Extrude',),
                 difference='Active path curve uses the other selected curve as a bevel profile; creates evaluated curve geometry, not a Maya NURBS surface patch or its path parameterization.',
                 source='source/blender/makesrna/intern/rna_curve.cc'))
for _id, _label, _kind, _category, _maya in (
        ('curve.offset_geometry', '2D Curve Geometry Offset', 'OFFSET', 'Curves', ('OffsetCurve',)),
        ('curve.bevel_geometry', 'Curve Round Bevel Geometry', 'BEVEL', 'Curves', ()),
        ('curve.resolution', 'Curve Sampling Resolution', 'RESOLUTION', 'Curves', ()),
        ('surface.resolution', 'Surface Sampling Resolution', 'RESOLUTION', 'Surfaces', ())):
    _specs.append(op(_id, _label, _category, 'axismeld.m3_curve_geometry',
                     kwargs={'kind': _kind}, requires='object', section=('Geometry',), maya=_maya,
                     source='source/blender/makesrna/intern/rna_curve.cc',
                     difference='Edits native curve data. Offset affects 2D output geometry rather than creating an independent Maya offset curve; resolution only changes sampling.'))

for _id, _label, _kind, _maya, _difference in (
        ('bend', 'Bend', 'BEND', ('Bend',), 'Simple Deform uses the object local axis and bounding-box limits.'),
        ('twist', 'Twist', 'TWIST', ('Twist',), 'Simple Deform uses the object local axis and bounding-box limits.'),
        ('taper', 'Taper / Flare', 'TAPER', ('Flare',), 'Linear native taper; not independent Maya start/end flare factors.'),
        ('stretch', 'Stretch / Squash', 'STRETCH', ('Squash',), 'Native stretch and volume compensation; Maya squash bounds differ.'),
        ('wave', 'Static Wave', 'WAVE', ('Wave', 'Sine'), 'Static native XY wave with speed zero; not Maya axial Sine or animated Wave.'),
        ('lattice', 'Create Enclosing Lattice', 'LATTICE', ('CreateLattice',), 'Creates a 3 by 3 by 3 cage in object space and offsets its upper region; edit cage control points for further shaping.'),
        ('shrinkwrap', 'Shrinkwrap to Selected Mesh', 'SHRINKWRAP', ('CreateShrinkWrap',), 'Active source, one selected mesh target; nearest surface point with 0.05 offset.'),
        ('curve', 'Deform Along Selected Curve', 'CURVE', ('WireTool',), 'Active mesh and one selected curve; native local-axis curve deformation, not multi-wire/dropoff nodes.'),
        ('surface_bind', 'Bind to Selected Surface Mesh', 'SURFACE_DEFORM', ('CreateWrap',), 'Binds active mesh to one selected target mesh. Target deformation drives source after binding; topology must remain stable.'),
        ('mesh_bind', 'Bind to Selected Closed Mesh Cage', 'MESH_DEFORM', ('ProximityWrap',), 'Mesh Deform cage binding; one closed selected cage must enclose the active source. Not a proximity-distance wrap algorithm.'),
        ('corrective_smooth', 'Bind Corrective Smooth (Smooth Only)', 'CORRECTIVE_SMOOTH', ('DeltaMush',), 'Native bind with Smooth Only initially enabled for observable smoothing; disable it in modifier settings for corrective deformation.'),
        ('laplacian', 'Bind Laplacian / Offset Anchors', 'LAPLACIANDEFORM', (), 'Selected mesh vertices become anchors; at least one unselected vertex is required. Anchors move on local Z after binding.'),
        ('smooth', 'Smooth Modifier', 'SMOOTH', (), 'Native iterative vertex smoothing.'),
        ('laplacian_smooth', 'Laplacian Smooth Modifier', 'LAPLACIANSMOOTH', (), 'Native Laplacian smoothing, volume preservation disabled.'),
        ('cast', 'Cast to Sphere', 'CAST', (), 'Native spherical coordinate cast, radius 1.'),
        ('displace', 'Texture Displace', 'DISPLACE', ('CreateTextureDeformer',), 'Creates a linked Clouds texture in global coordinates; no UV dependency.'),
        ('warp', 'Warp Between Selected Empties', 'WARP', (), 'Two distinct empty transforms are ordered by object name: from, then to; no falloff.'),
        ('solidify', 'Add Shell Thickness', 'SOLIDIFY', (), 'Native surface shell thickness; not Maya Deform Solidify rigid-region preservation.')):
    _specs.append(op('deform.' + _id, _label, 'Deform', 'axismeld.m3_deform',
                     kwargs={'kind': _kind}, requires='mesh', maya=_maya,
                     section=('Targets and Binding',) if _kind in {'LATTICE', 'SHRINKWRAP', 'CURVE', 'SURFACE_DEFORM', 'MESH_DEFORM', 'WARP'} else ('Nonlinear and Smooth',),
                     difference=_difference + ' Parameters: Edit > Adjust Last Operation and native Modifier properties.',
                     source='source/blender/makesrna/intern/rna_modifier.cc; scripts/startup/bl_ui/properties_data_modifier.py'))
_specs.append(op('deform.shape_key_join', 'Selected Targets to Shape Keys', 'Deform',
                 'axismeld.m3_shape_targets', requires='two_mesh', section=('Shape Keys',),
                 maya=('CreateBlendShape', 'AddBlendShape', 'Morph'),
                 difference='Active mesh receives relative keys from equal indexed topology; first target influence is 1. Source targets remain. World-space target coordinates are converted to source local space.',
                 source='source/blender/editors/object/object_shapekey.cc'))
_specs.append(op('deform.hook_selected', 'Hook Selected Points / New Controller', 'Deform',
                 'axismeld.m3_hook', modes=('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE'),
                 section=('Membership and Hooks',), maya=('CreateCluster',),
                 difference='Native Hook with selected point membership, a new empty controller and 0.25 world Z offset; not the complete Maya Cluster node system.',
                 source='source/blender/editors/object/object_hook.cc'))
for _id, _label, _operator, _kwargs, _modes, _maya in (
        ('lattice_reset', 'Reset Lattice Grid', 'lattice.make_regular', {}, ('EDIT_LATTICE',), ('ResetLattice', 'RemoveLatticeTweaks')),
        ('lattice_flip_x', 'Flip Lattice X', 'lattice.flip', {'axis': 'U'}, ('EDIT_LATTICE',), ()),
        ('shape_key_remove', 'Remove Active Shape Key', 'object.shape_key_remove', {'all': False}, ('OBJECT',), ('RemoveBlendShape',)),
        ('shape_key_mirror', 'Mirror Active Shape Key', 'object.shape_key_mirror', {'use_topology': False}, ('OBJECT',), ()),
        ('vertex_group_assign', 'Assign Selected to Active Group', 'object.vertex_group_assign', {}, ('EDIT_MESH',), ('EditMembershipTool',)),
        ('vertex_group_remove', 'Remove Selected from Active Group', 'object.vertex_group_remove_from', {'use_all_groups': False}, ('EDIT_MESH',), ()),
        ('vertex_group_normalize', 'Normalize Active Group', 'object.vertex_group_normalize', {}, ('OBJECT', 'EDIT_MESH'), ()),
        ('vertex_group_mirror', 'Mirror Active Group Weights', 'object.vertex_group_mirror', {'mirror_weights': True, 'flip_group_names': False}, ('OBJECT', 'EDIT_MESH'), ('MirrorDeformerWeights',)),
        ('vertex_group_clean', 'Clean Active Group Weights', 'object.vertex_group_clean', {'limit': 0.01}, ('OBJECT', 'EDIT_MESH'), ('PruneCluster', 'PruneLattice', 'PruneWire'))):
    _specs.append(op('deform.' + _id, _label, 'Deform', _operator, kwargs=_kwargs, modes=_modes,
                     maya=_maya, section=('Shape Keys',) if _id.startswith('shape_key') else ('Membership and Hooks',),
                     difference='Native Blender active key / vertex group / lattice operation; indexed topology, group naming and weight semantics differ from Maya deformer nodes.',
                     source='scripts/startup/bl_ui/space_view3d.py; source/blender/editors/object/'))

for _id, _label, _kind, _action, _maya in (
        ('surface_bind_existing', 'Bind Existing Surface Deform', 'SURFACE_DEFORM', 'BIND', ()),
        ('surface_unbind_existing', 'Unbind Surface Deform', 'SURFACE_DEFORM', 'UNBIND', ()),
        ('mesh_bind_existing', 'Bind Existing Mesh Deform', 'MESH_DEFORM', 'BIND', ()),
        ('mesh_unbind_existing', 'Unbind Mesh Deform', 'MESH_DEFORM', 'UNBIND', ()),
        ('shrinkwrap_target', 'Set Shrinkwrap Target', 'SHRINKWRAP', 'SET_TARGET', ('SetShrinkWrapTarget', 'AddShrinkWrapSurfaces')),
        ('shrinkwrap_clear', 'Clear Shrinkwrap Target', 'SHRINKWRAP', 'CLEAR_TARGET', ('RemoveShrinkWrapTarget', 'RemoveShrinkWrapSurfaces')),
        ('curve_target', 'Set Curve Deform Target', 'CURVE', 'SET_TARGET', ('AddWire',)),
        ('hook_assign', 'Assign Selected to Hook', 'HOOK', 'ASSIGN', ()),
        ('hook_reset', 'Reset Hook Rest Transform', 'HOOK', 'RESET', ())):
    _specs.append(op('deform.' + _id, _label, 'Deform', 'axismeld.m3_deform_manage',
                     modes=('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE') if _kind == 'HOOK' else ('OBJECT',),
                     kwargs={'kind': _kind, 'action': _action}, maya=_maya,
                     section=('Targets and Binding',),
                     difference='Uses active modifier of this type, or the sole matching modifier. Native target and binding semantics; no Maya multi-influence arrays.',
                     source='source/blender/editors/object/object_modifier.cc; source/blender/editors/object/object_hook.cc'))
SPECS = tuple(replace(spec, classification='adapted' if spec.maya else 'blender') for spec in _specs)

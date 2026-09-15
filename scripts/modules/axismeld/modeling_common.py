# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed Common menu commands; executable names and RNA paths never come from profiles."""
from dataclasses import replace

from .modeling_schema import NativeCall, op

O = ('OBJECT',)
M = ('EDIT_MESH',)
C = ('EDIT_CURVE', 'EDIT_SURFACE')
EDIT = M + C + ('EDIT_LATTICE',)
ALL = O + EDIT


def _entry(identifier, label, category, operator, *, maya=(), line=None, **kwargs):
    kwargs.setdefault('difference', 'Uses Blender native selection, geometry and parameter semantics.')
    kwargs.setdefault('classification', 'adapted' if maya else 'blender')
    source = ('scripts/modules/axismeld/modeling_shapes_ops.py' if operator == 'axismeld.m3_curve_geometry' else
              'scripts/modules/axismeld/modeling_common_ops.py') if operator.startswith('axismeld.m3_') else (
              'scripts/startup/bl_ui/space_view3d.py' + (':' + str(line) if line else ''))
    return op(identifier, label, category, operator, maya=maya,
              source=(source + '; native ' + operator +
                      ('; Maya ' + ', '.join(maya) if maya else '; Blender extension')), **kwargs)


def _multi(identifier, label, category, calls, **kwargs):
    first = calls[0]
    item = _entry(identifier, label, category, first.operator, **kwargs)
    return replace(item, calls=tuple(calls))


def _call(operator, modes, **kwargs):
    return NativeCall(operator, modes, tuple(kwargs.items()))


_specs = [
    _multi('selection.invert', 'Invert', 'Select', (
        _call('object.select_all', O, action='INVERT'), _call('mesh.select_all', M, action='INVERT'),
        _call('curve.select_all', C, action='INVERT'),
        _call('lattice.select_all', ('EDIT_LATTICE',), action='INVERT')),
        maya=('InvertSelection',), key='I', ctrl=True, shift=True, section=('Selection',)),
    _entry('selection.hierarchy', 'Hierarchy', 'Select', 'axismeld.m3_select',
           kwargs={'action': 'HIERARCHY'}, maya=('SelectHierarchy',), requires='selection',
           section=('Hierarchy',), difference='Selects visible selectable Blender descendants; no Maya UFE/DAG nodes.'),
    _entry('selection.geometry', 'All Geometry', 'Select', 'axismeld.m3_select',
           kwargs={'action': 'GEOMETRY'}, maya=('SelectAllGeometry',), section=('All by Type',)),
    _entry('selection.transforms', 'All Objects', 'Select', 'object.select_all',
           kwargs={'action': 'SELECT'}, maya=('SelectAllTransforms',), section=('All by Type',),
           difference='Blender objects carry transforms; this excludes Maya transform-only DAG nodes.'),
    _entry('selection.image_planes', 'Image Empties', 'Select', 'axismeld.m3_select',
           kwargs={'action': 'IMAGE'}, maya=('SelectAllImagePlanes',), section=('All by Type',)),
    _entry('selection.assets', 'Asset Objects', 'Select', 'axismeld.m3_select',
           kwargs={'action': 'ASSETS'}, maya=('SelectAllAssets',), section=('All by Type',),
           difference='Selects Blender object datablocks marked as assets, not Maya asset containers.'),
    _entry('selection.by_name', 'By Name Pattern...', 'Select', 'object.select_pattern', invoke=True,
           section=('Object Relationships',), difference='Blender wildcard names in the current view layer.'),
    _entry('selection.active_camera', 'Active Camera', 'Select', 'object.select_camera',
           section=('Object Relationships',)),
]

for kind, label, maya in (
        ('MESH', 'Polygon Meshes', 'SelectAllPolygonGeometry'), ('CURVE', 'Curves', 'SelectAllNURBSCurves'),
        ('SURFACE', 'NURBS Surfaces', 'SelectAllNURBSSurfaces'), ('CAMERA', 'Cameras', 'SelectAllCameras'),
        ('LIGHT', 'Lights', 'SelectAllLights'), ('LATTICE', 'Lattices', 'SelectAllLattices'),
        ('EMPTY', 'Empties', ''), ('FONT', 'Text', '')):
    _specs.append(_entry('selection.type_' + kind.lower(), label, 'Select', 'object.select_by_type',
                        kwargs={'type': kind}, maya=(maya,) if maya else (), section=('All by Type',)))

for direction, extend, suffix, label in (
        ('PARENT', False, 'parent', 'Parent'), ('CHILD', False, 'child', 'Child'),
        ('PARENT', True, 'extend_parent', 'Extend to Parent'), ('CHILD', True, 'extend_child', 'Extend to Child')):
    _specs.append(_entry('selection.' + suffix, label, 'Select', 'object.select_hierarchy',
                        kwargs={'direction': direction, 'extend': extend}, requires='object', section=('Hierarchy',)))
for suffix, operator, label in (
        ('object_more', 'object.select_more', 'More'), ('object_less', 'object.select_less', 'Less')):
    _specs.append(_entry('selection.' + suffix, label, 'Select', operator,
                        requires='object', section=('Hierarchy',)))
for kind, label in (('CHILDREN_RECURSIVE', 'Children Recursive'), ('CHILDREN', 'Children'),
                    ('PARENT', 'Parent'), ('SIBLINGS', 'Siblings'), ('TYPE', 'Type'),
                    ('COLLECTION', 'Collection'), ('PASS', 'Object Pass'), ('COLOR', 'Color')):
    _specs.append(_entry('selection.grouped_' + kind.lower(), label, 'Select', 'object.select_grouped',
                        kwargs={'type': kind}, requires='object', section=('Grouped',)))
for kind, label in (('OBDATA', 'Object Data'), ('MATERIAL', 'Material'), ('DUPGROUP', 'Collection Instance')):
    _specs.append(_entry('selection.linked_' + kind.lower(), label, 'Select', 'object.select_linked',
                        kwargs={'type': kind}, requires='object', section=('Linked Objects',)))

for suffix, label, native, maya in (
        ('edge_loop', 'Edge Loop', 'select_edge_loop_multi', 'SelectEdgeLoopSp'),
        ('edge_ring', 'Edge Ring', 'select_edge_ring_multi', 'SelectEdgeRingSp'),
        ('boundary_loop', 'Boundary Loop', 'select_boundary_loop_multi', 'ConvertSelectionToShellBorder'),
        ('loop_region', 'Loop Interior', 'loop_to_region', ''),
        ('region_boundary', 'Selection Boundary', 'region_to_loop', 'ConvertSelectionToEdgePerimeter'),
        ('shortest_path', 'Shortest Edge Path', 'shortest_path_select', 'SelectShortestEdgePathTool'),
        ('linked_mesh', 'Connected Shell', 'select_linked', 'ConvertSelectionToShell'),
        ('linked_flat', 'Linked Flat Faces', 'faces_select_linked_flat', ''),
        ('similar_region', 'Similar Face Regions', 'select_similar_region', ''),
        ('non_manifold', 'Non-Manifold', 'select_non_manifold', 'PolygonSelectionConstraints'),
        ('loose', 'Loose Geometry', 'select_loose', ''),
        ('interior', 'Interior Faces', 'select_interior_faces', ''),
        ('sides', 'Faces by Sides', 'select_face_by_sides', ''),
        ('poles', 'Poles by Count', 'select_by_pole_count', ''),
        ('sharp', 'Sharp Edges', 'edges_select_sharp', ''),
        ('side', 'Side of Active', 'select_axis', ''),
        ('attribute', 'By Attribute', 'select_by_attribute', ''),
        ('next', 'Next Active', 'select_next_item', ''),
        ('previous', 'Previous Active', 'select_prev_item', ''),
        ('checker', 'Checker Deselect', 'select_nth', ''),
        ('ungrouped', 'Ungrouped Vertices', 'select_ungrouped', '')):
    _specs.append(_entry('selection.' + suffix, label, 'Select', 'mesh.' + native, modes=M,
                        maya=(maya,) if maya else (), requires='mesh', line=1906,
                        section=('Mesh Components',),
                        difference='Blender topology/threshold selection; use Adjust Last Operation for available parameters.'))
for mode, maya, key in (('VERT', 'ConvertSelectionToVertices', 'F9'),
                         ('EDGE', 'ConvertSelectionToEdges', 'F10'), ('FACE', 'ConvertSelectionToFaces', 'F11')):
    _specs.append(_entry('selection.convert_' + mode.lower(), 'Convert to ' + mode.title(), 'Select',
                        'mesh.select_mode', modes=M, kwargs={'type': mode, 'use_expand': True},
                        maya=(maya,), requires='mesh', key=key, ctrl=True, section=('Convert Selection',),
                        difference='Uses Blender selection expansion when changing domain; contained/perimeter rules differ.'))
for kind, label, maya in (
        ('VERT_NORMAL', 'Vertex Normal', 'SelectSimilar'), ('VERT_FACES', 'Adjacent Faces', ''),
        ('VERT_GROUPS', 'Vertex Groups', ''), ('VERT_EDGES', 'Connecting Edges', ''),
        ('EDGE_LENGTH', 'Edge Length', ''), ('EDGE_DIR', 'Edge Direction', ''), ('EDGE_FACES', 'Edge Face Count', ''),
        ('EDGE_FACE_ANGLE', 'Edge Face Angle', ''), ('EDGE_CREASE', 'Edge Crease', ''), ('EDGE_SHARP', 'Edge Sharpness', ''),
        ('FACE_AREA', 'Face Area', ''), ('FACE_SIDES', 'Polygon Sides', ''), ('FACE_PERIMETER', 'Face Perimeter', ''),
        ('FACE_NORMAL', 'Face Normal', ''), ('FACE_COPLANAR', 'Coplanar Faces', ''),
        ('FACE_SMOOTH', 'Smooth Faces', ''), ('FACE_MATERIAL', 'Face Material', '')):
    _specs.append(_entry('selection.similar_' + kind.lower(), label, 'Select', 'mesh.select_similar',
                        modes=M, kwargs={'type': kind}, requires='mesh', section=('Select Similar',), maya=(maya,) if maya else ()))
for suffix, label, operator in (('random', 'Random', 'select_random'), ('mirror', 'Mirror', 'select_mirror')):
    _specs.append(_multi('selection.' + suffix, label, 'Select', (
        _call('object.' + operator, O), _call('mesh.' + operator, M)), section=('Pattern',)))
for suffix, label, native, maya in (
        ('all', 'All Control Points', 'select_all', 'SelectCurveCVsAll'),
        ('first', 'First Control Points', 'de_select_first', 'SelectCurveCVsFirst'),
        ('last', 'Last Control Points', 'de_select_last', 'SelectCurveCVsLast'),
        ('next', 'Next Control Points', 'select_next', ''), ('previous', 'Previous Control Points', 'select_previous', ''),
        ('linked', 'Linked Spline', 'select_linked', ''), ('more', 'More Control Points', 'select_more', ''),
        ('less', 'Fewer Control Points', 'select_less', ''), ('random', 'Random Control Points', 'select_random', ''),
        ('checker', 'Checker Control Points', 'select_nth', '')):
    _specs.append(_entry('selection.curve_' + suffix, label, 'Select', 'curve.' + native, modes=C,
                        kwargs={'action': 'SELECT'} if suffix == 'all' else {},
                        maya=(maya,) if maya else (), section=('Curve and Surface Points',), line=2026))

# Settings are a fixed, trusted enum. UI state reads these same values.
# owner, attribute, value (None toggles), UI kind. No arbitrary property path is executable.
SETTINGS = {
    'pivot.median': ('TOOLS', 'transform_pivot_point', 'MEDIAN_POINT', 'radio'),
    'pivot.active': ('TOOLS', 'transform_pivot_point', 'ACTIVE_ELEMENT', 'radio'),
    'pivot.cursor': ('TOOLS', 'transform_pivot_point', 'CURSOR', 'radio'),
    'pivot.individual': ('TOOLS', 'transform_pivot_point', 'INDIVIDUAL_ORIGINS', 'radio'),
    'pivot.bounds': ('TOOLS', 'transform_pivot_point', 'BOUNDING_BOX_CENTER', 'radio'),
    'snap.enabled': ('TOOLS', 'use_snap', None, 'checkbox'),
    'snap.vertex': ('TOOLS', 'snap_elements', ('VERTEX',), 'radio'),
    'snap.edge': ('TOOLS', 'snap_elements', ('EDGE',), 'radio'),
    'snap.face': ('TOOLS', 'snap_elements', ('FACE',), 'radio'),
    'snap.increment': ('TOOLS', 'snap_elements', ('INCREMENT',), 'radio'),
    'snap.closest': ('TOOLS', 'snap_target', 'CLOSEST', 'radio'),
    'snap.center': ('TOOLS', 'snap_target', 'CENTER', 'radio'),
    'snap.median': ('TOOLS', 'snap_target', 'MEDIAN', 'radio'),
    'snap.active': ('TOOLS', 'snap_target', 'ACTIVE', 'radio'),
    'transform.proportional': ('TOOLS', 'use_proportional_edit', None, 'checkbox'),
    'transform.proportional_objects': ('TOOLS', 'use_proportional_edit_objects', None, 'checkbox'),
    'transform.proportional_connected': ('TOOLS', 'use_proportional_connected', None, 'checkbox'),
    'transform.proportional_projected': ('TOOLS', 'use_proportional_projected', None, 'checkbox'),
    'display.grid': ('OVERLAY', 'show_floor', None, 'checkbox'),
    'display.axis_x': ('OVERLAY', 'show_axis_x', None, 'checkbox'),
    'display.axis_y': ('OVERLAY', 'show_axis_y', None, 'checkbox'),
    'display.axis_z': ('OVERLAY', 'show_axis_z', None, 'checkbox'),
    'display.overlays': ('OVERLAY', 'show_overlays', None, 'checkbox'),
    'display.wire_overlay': ('OVERLAY', 'show_wireframes', None, 'checkbox'),
    'display.face_orientation': ('OVERLAY', 'show_face_orientation', None, 'checkbox'),
    'display.origins': ('OVERLAY', 'show_object_origins', None, 'checkbox'),
    'display.relationships': ('OVERLAY', 'show_relationship_lines', None, 'checkbox'),
    'display.curve_normals': ('OVERLAY', 'show_curve_normals', None, 'checkbox'),
    'display.statistics': ('OVERLAY', 'show_stats', None, 'checkbox'),
    'display.backface_culling': ('SHADING', 'show_backface_culling', None, 'checkbox'),
    'display.backface_culling_on': ('SHADING', 'show_backface_culling', True, None),
    'display.backface_culling_off': ('SHADING', 'show_backface_culling', False, None),
    'display.color_object': ('SHADING', 'color_type', 'OBJECT', 'radio'),
    'display.color_material': ('SHADING', 'color_type', 'MATERIAL', 'radio'),
    'display.color_random': ('SHADING', 'color_type', 'RANDOM', 'radio'),
}
for kind in ('SMOOTH', 'SPHERE', 'ROOT', 'INVERSE_SQUARE', 'SHARP', 'LINEAR', 'CONSTANT', 'RANDOM'):
    SETTINGS['transform.falloff_' + kind.lower()] = ('TOOLS', 'proportional_edit_falloff', kind, 'radio')
for kind in ('mesh', 'curve', 'surf', 'meta', 'font', 'volume', 'lattice', 'empty', 'light', 'camera'):
    SETTINGS['display.type_' + kind] = ('SPACE', 'show_object_viewport_' + kind, None, 'checkbox')
for kind in ('mesh', 'curve', 'surf', 'lattice', 'light', 'camera'):
    del SETTINGS['display.type_' + kind]
    for verb, value in (('hide', False), ('show', True)):
        SETTINGS['display.' + verb + '_type_' + kind] = ('SPACE', 'show_object_viewport_' + kind, value, 'radio')
_setting_labels = {'display.backface_culling_on': 'Backface Culling on for All Polys',
                   'display.backface_culling_off': 'Backface Culling off for All Polys',
                   'pivot.median': 'Median Point', 'pivot.active': 'Active Element', 'pivot.cursor': '3D Cursor',
                   'pivot.individual': 'Individual Origins', 'pivot.bounds': 'Bounding Box Center',
                   'snap.enabled': 'Enable Snapping', 'transform.proportional': 'Proportional Editing',
                   'transform.proportional_objects': 'Object Proportional Editing',
                   'transform.proportional_connected': 'Connected Only',
                   'transform.proportional_projected': 'Projected from View'}
_setting_maya = {'display.grid': ('ToggleGrid',), 'display.backface_culling': ('ToggleBackfaceGeometry',),
                 'display.curve_normals': ('ToggleNormals',),
                 'display.wire_overlay': ('TogglePolyDisplayEdges',),
                 'transform.proportional': ('ProportionalModificationTool',)}
for kind, maya in (('mesh', 'PolygonSurfaces'), ('curve', 'NURBSCurves'), ('surf', 'NURBSSurfaces'),
                   ('lattice', 'Lattices'), ('light', 'Lights'), ('camera', 'Cameras')):
    for verb in ('hide', 'show'):
        _setting_maya['display.' + verb + '_type_' + kind] = (verb.title() + maya,)
for identifier in SETTINGS:
    category = 'Display' if identifier.startswith('display.') else 'Modify'
    section = ('Pivot',) if identifier.startswith('pivot.') else (('Snapping',) if identifier.startswith('snap.') else (
        ('Proportional Editing',) if identifier.startswith('transform.') else ('Viewport Settings',)))
    _specs.append(_entry(identifier, _setting_labels.get(identifier, identifier.split('.', 1)[1].replace('_', ' ').title()),
                        category, 'axismeld.m3_setting', modes=ALL,
                        kwargs={'action': identifier}, undo=False, replayable=False, section=section,
                        maya=_setting_maya.get(identifier, ()), line=1473,
                        difference='Edits only the named Blender viewport/tool setting; no geometry or temporary hold-key emulation.'))
_specs.append(_entry('display.xray', 'X-Ray', 'Display', 'axismeld.m3_setting', modes=ALL,
                    kwargs={'action': 'display.xray'}, undo=False, replayable=False, section=('Viewport Settings',),
                    difference='Uses the separate Blender solid/wireframe X-Ray setting in the current viewport.'))

for suffix, label, native in (('translate', 'Move Components / Objects', 'translate'),
                             ('rotate_interactive', 'Rotate Components / Objects', 'rotate'),
                             ('resize_interactive', 'Scale Components / Objects', 'resize'),
                             ('shear', 'Shear', 'shear'), ('to_sphere', 'To Sphere', 'tosphere'),
                             ('bend', 'Bend Transform', 'bend'), ('push_pull', 'Push / Pull', 'push_pull')):
    _specs.append(_entry('transform.' + suffix, label, 'Modify', 'transform.' + native, modes=ALL,
                        invoke=True, requires='selection', section=('Transform Actions',), line=1317))
_specs.append(_entry('transform.shrink_fatten', 'Move Along Normals', 'Modify', 'transform.shrink_fatten',
                    modes=M, invoke=True, requires='mesh', section=('Transform Actions',), maya=('MoveNormalTool',)))
for suffix, native, label, values in (
        ('location', 'location_clear', 'Reset Location', {'clear_delta': False}),
        ('rotation', 'rotation_clear', 'Reset Rotation', {'clear_delta': False}),
        ('scale', 'scale_clear', 'Reset Scale', {'clear_delta': False})):
    _specs.append(_entry('transform.reset_' + suffix, label, 'Modify', 'object.' + native,
                        kwargs=values, requires='selection', section=('Reset Transformations',), line=3026))
_specs.append(_entry('transform.reset_all', 'Reset Transformations', 'Modify', 'axismeld.m3_match',
                    kwargs={'action': 'RESET'}, requires='selection', section=('Reset Transformations',),
                    maya=('ResetTransformations',), difference='Clears Blender local location/rotation/scale, retaining deltas and parenting.'))
for suffix, label, flags in (('location', 'Apply Location', (True, False, False)),
                             ('rotation', 'Apply Rotation', (False, True, False)),
                             ('scale', 'Apply Scale', (False, False, True)),
                             ('rotation_scale', 'Apply Rotation and Scale', (False, True, True)),
                             ('all', 'Apply All Transforms', (True, True, True))):
    _specs.append(_entry('transform.apply_' + suffix, label, 'Modify', 'object.transform_apply', invoke=True,
                        kwargs=dict(zip(('location', 'rotation', 'scale'), flags)), requires='selection',
                        maya=('FreezeTransformations',) if suffix == 'all' else (), section=('Apply Transformations',), line=3291,
                        difference='Blender Apply bakes transforms into data; not exact Maya Freeze. Native multi-user confirmation is retained.'))
for kind, label, maya in (('ALL', 'Match All Transforms', 'MatchTransform'), ('LOCATION', 'Match Translation', 'MatchTranslation'),
                         ('ROTATION', 'Match Rotation', 'MatchRotation'), ('SCALE', 'Match Scale', 'MatchScaling')):
    _specs.append(_entry('transform.match_' + ('all' if kind == 'ALL' else kind.lower()), label, 'Modify',
                        'axismeld.m3_match', kwargs={'action': kind}, requires='two_objects',
                        section=('Match Transformations',), maya=(maya,),
                        difference='Matches selected editable objects to the active object in world space; partial matches decompose shear.'))
for kind, label, maya in (('ORIGIN_GEOMETRY', 'Center Origin to Geometry', 'CenterPivot'),
                         ('ORIGIN_CURSOR', 'Origin to 3D Cursor', ''), ('GEOMETRY_ORIGIN', 'Geometry to Origin', ''),
                         ('ORIGIN_CENTER_OF_MASS', 'Origin to Surface Center of Mass', ''),
                         ('ORIGIN_CENTER_OF_VOLUME', 'Origin to Volume Center of Mass', '')):
    _specs.append(_entry('pivot.' + kind.lower(), label, 'Modify', 'object.origin_set', kwargs={'type': kind},
                        requires='selection', section=('Object Origin',), maya=(maya,) if maya else (), line=2908,
                        difference='Uses one Blender origin; independent Maya rotate and scale pivots are not reproduced.'))
for native, label, kwargs in (
        ('snap_selected_to_grid', 'Selection to Grid', {}),
        ('snap_selected_to_cursor', 'Selection to Cursor', {'use_offset': False}),
        ('snap_selected_to_active', 'Selection to Active', {}),
        ('snap_cursor_to_selected', 'Cursor to Selected', {}), ('snap_cursor_to_center', 'Cursor to Origin', {}),
        ('snap_cursor_to_grid', 'Cursor to Grid', {}), ('snap_cursor_to_active', 'Cursor to Active', {})):
    _specs.append(_entry('snap.' + native.removeprefix('snap_'), label, 'Modify', 'view3d.' + native, modes=ALL,
                        kwargs=kwargs, section=('Snap Actions',), line=1473,
                        requires='object' if native.endswith('_active') else ''))
for axis, vector in (('x', (True, False, False)), ('y', (False, True, False)), ('z', (False, False, True))):
    _specs.append(_entry('transform.mirror_' + axis, 'Mirror ' + axis.upper(), 'Modify', 'transform.mirror',
                        modes=ALL, kwargs={'constraint_axis': vector, 'orient_type': 'GLOBAL'},
                        requires='selection', section=('Mirror',), line=1446))
for suffix, label, operator, kwargs in (
        ('align', 'Align Objects...', 'object.align', {}),
        ('randomize', 'Randomize Transform...', 'object.randomize_transform', {}),
        ('align_orientation', 'Align to Transform Orientation', 'transform.transform', {'mode': 'ALIGN'}),
        ('visual_apply', 'Apply Visual Transform', 'object.visual_transform_apply', {})):
    _specs.append(_entry('transform.' + suffix, label, 'Modify', operator, kwargs=kwargs,
                        requires='selection', section=('Transform Actions',), line=1374,
                        maya=('AlignObjects',) if suffix == 'align' else ()))
for mode, label in (('LOC', 'Location to Deltas'), ('ROT', 'Rotation to Deltas'),
                    ('SCALE', 'Scale to Deltas'), ('ALL', 'All Transforms to Deltas')):
    _specs.append(_entry('transform.delta_' + mode.lower(), label, 'Modify', 'object.transforms_to_deltas',
                        kwargs={'mode': mode}, requires='selection', section=('Transform Deltas',), line=3317))
_specs.extend((
    _entry('object.rename', 'Rename Active Item...', 'Modify', 'wm.call_panel', invoke=True, undo=False,
           kwargs={'name': 'TOPBAR_PT_name', 'keep_open': False}, requires='object', section=('Names',), line=2900,
           difference='Opens the native active-item naming panel (space_topbar.py:559).'),
    _entry('object.batch_rename', 'Batch Rename...', 'Modify', 'wm.batch_rename', invoke=True,
           requires='selection', section=('Names',), maya=('PrefixHierarchyNames', 'SearchAndReplaceNames'),
           difference='Blender Batch Rename patterns and current selected-object targets; hierarchy is not implicitly selected.'),
    _entry('object.make_single_user', 'Make Object and Data Single User', 'Modify', 'object.make_single_user',
           requires='selection', section=('Convert',), kwargs={'object': True, 'obdata': True, 'material': False,
           'animation': False, 'obdata_animation': False}, maya=('ConvertInstanceToObject',), line=3510),
    _entry('object.instances_real', 'Make Instances Real', 'Modify', 'object.duplicates_make_real',
           requires='selection', section=('Convert',), line=3350),
))
for target, label, maya in (('MESH', 'Convert to Mesh', ('NURBSToPolygons', 'CreatePolyFromPreview')),
                            ('CURVE', 'Convert to Curve', ('CreateCurveFromPoly',))):
    _specs.append(_entry('object.convert_' + target.lower(), label, 'Modify', 'object.convert',
                        kwargs={'target': target}, requires='selection', section=('Convert',), maya=maya, line=3546,
                        difference='Converts evaluated Blender data; modifiers and original data may be replaced.'))

_specs.extend((
    _entry('edit.undo', 'Undo', 'Edit', 'ed.undo', modes=ALL, undo=False, replayable=False,
           maya=('Undo',), key='Z', section=('History',), line=2895),
    _entry('edit.redo', 'Redo', 'Edit', 'ed.redo', modes=ALL, undo=False, replayable=False,
           maya=('Redo',), key='Z', shift=True, section=('History',), line=2895),
    _entry('edit.adjust_last_operation', 'Adjust Last Operation...', 'Edit', 'screen.redo_last',
           modes=ALL, invoke=True, undo=False, replayable=False, section=('History',),
           difference='Native parameter popup returns CANCELLED even when opened; UI-only, not Recent. F9 remains Vertex.'),
    _entry('edit.repeat_native', 'Repeat Last Blender Operation', 'Edit', 'screen.repeat_last',
           modes=ALL, invoke=True, undo=False, replayable=False, section=('History',),
           difference='Repeats native operator history, separate from AxisMeld Recent. Maya G already uses the identical native Screen repeat_last binding, which remains in place.'),
    _entry('edit.copy_objects', 'Copy Objects', 'Edit', 'view3d.copybuffer', undo=False, replayable=False,
           requires='selection', key='C', ctrl=True, maya=('CopySelected',), section=('Clipboard',), line=2920),
    _entry('edit.paste_objects', 'Paste Objects', 'Edit', 'view3d.pastebuffer', key='V', ctrl=True,
           maya=('PasteSelected',), section=('Clipboard',), line=2920,
           difference='Pastes Blender object-buffer data; not component or animation clipboard.'),
    _entry('edit.cut_objects', 'Cut Objects', 'Edit', 'axismeld.m3_cut', requires='selection',
           key='X', ctrl=True, maya=('CutSelected',), section=('Clipboard',),
           difference='Copies selected editable objects successfully before native deletion; one geometry undo.'),
    _entry('edit.group', 'Group', 'Edit', 'axismeld.m3_group', requires='selection', key='G', ctrl=True,
           maya=('Group',), section=('Hierarchy',),
           difference='Creates a Blender Empty parent and preserves world transforms; Collections are not used as DAG groups.'),
    _entry('edit.ungroup', 'Ungroup', 'Edit', 'axismeld.m3_ungroup', requires='selection',
           maya=('Ungroup',), section=('Hierarchy',),
           difference='Removes selected Empty parents, preserving child world transforms and the surviving parent chain.'),
    _entry('edit.parent', 'Parent', 'Edit', 'object.parent_set', requires='two_objects',
           kwargs={'type': 'OBJECT', 'keep_transform': True}, maya=('Parent',), key='P', section=('Hierarchy',), line=3359),
    _entry('edit.unparent', 'Unparent (Keep Transform)', 'Edit', 'object.parent_clear', requires='selection',
           kwargs={'type': 'CLEAR_KEEP_TRANSFORM'}, maya=('Unparent',), key='P', shift=True, section=('Hierarchy',), line=3359),
    _multi('edit.duplicate', 'Duplicate', 'Edit', (
        _call('object.duplicate', O, linked=False), _call('mesh.duplicate', M), _call('curve.duplicate', C)),
        requires='selection', maya=('Duplicate',), key='D', ctrl=True, section=('Duplicate',), line=2914),
    _entry('edit.duplicate_linked', 'Duplicate Linked', 'Edit', 'object.duplicate', kwargs={'linked': True},
           requires='selection', key='D', ctrl=True, shift=True, section=('Duplicate',),
           difference='Blender linked object data instance; arbitrary Maya Duplicate Special arrays/history are not implied.'),
    _multi('edit.duplicate_move', 'Duplicate and Move', 'Edit', (
        NativeCall('object.duplicate_move', O, (), True, True),
        NativeCall('mesh.duplicate_move', M, (), True, True), NativeCall('curve.duplicate_move', C, (), True, True)),
        requires='selection', replayable=False, section=('Duplicate',),
        difference='Native modal duplicate/move. Cancel may retain the duplicate while cancelling movement; one undo removes it.'),
    _entry('edit.duplicate_repeat_transform', 'Repeat Duplicate Transform', 'Edit', 'axismeld.m3_duplicate_repeat',
           invoke=True, undo=False, replayable=False, requires='selection', key='D', shift=True,
           maya=('DuplicateWithTransform',), section=('Duplicate',),
           difference='Repeats a confirmed native Duplicate and Move as the last redoable operation; unavailable after other operations.'),
    _multi('edit.delete', 'Delete Selected', 'Edit', (
        _call('object.delete', O, use_global=False),
        _call('axismeld.m3_delete_components', M + C)),
        requires='selection', maya=('Delete',), key='DEL', section=('Delete',), line=2945),
))

for suffix, label, native, values, maya in (
        ('icosphere', 'Icosphere', 'mesh.primitive_ico_sphere_add', {}, ('CreatePolygonPlatonic',)),
        ('grid', 'Grid', 'mesh.primitive_grid_add', {}, ()),
        ('circle', 'Circle (Unfilled)', 'mesh.primitive_circle_add', {'fill_type': 'NOTHING'}, ()),
        ('monkey', 'Suzanne', 'mesh.primitive_monkey_add', {}, ()),
        ('pyramid', 'Polygon Pyramid', 'mesh.primitive_cone_add', {'vertices': 4, 'radius2': 0.0}, ('CreatePolygonPyramid',)),
        ('prism', 'Polygon Prism', 'mesh.primitive_cone_add', {'vertices': 3, 'radius1': 1.0, 'radius2': 1.0}, ('CreatePolygonPrism',))):
    _specs.append(_entry('mesh.create_' + suffix, label, 'Create', 'axismeld.m3_create',
                        kwargs={'kind': suffix.upper()}, maya=maya, section=('Additional Primitives',), line=2506,
                        difference='Creates a native Blender primitive at the 3D Cursor with native dimensions, Z-up and topology.'))
for suffix, label, native, maya in (
        ('bezier', 'Bezier Curve', 'primitive_bezier_curve_add', ''),
        ('bezier_circle', 'Bezier Circle', 'primitive_bezier_circle_add', ''),
        ('nurbs', 'NURBS Curve', 'primitive_nurbs_curve_add', ''),
        ('nurbs_circle', 'NURBS Circle', 'primitive_nurbs_circle_add', 'CreateNURBSCircle'),
        ('path', 'NURBS Path', 'primitive_nurbs_path_add', '')):
    _specs.append(_entry('curve.create_' + suffix, label, 'Create', 'axismeld.m3_create',
                        kwargs={'kind': 'CURVE_' + suffix.upper()}, maya=(maya,) if maya else (),
                        section=('Curve Primitives',), line=2534,
                        difference='Adds a native spline at the 3D Cursor; this is primitive creation, not the complete Maya interactive CV/EP tool.'))
for suffix, label, maya in (('curve', 'NURBS Curve Surface', ''), ('circle', 'NURBS Circle Surface', ''),
                          ('surface', 'NURBS Plane', 'CreateNURBSPlane'), ('cylinder', 'NURBS Cylinder', 'CreateNURBSCylinder'),
                          ('sphere', 'NURBS Sphere', 'CreateNURBSSphere'), ('torus', 'NURBS Torus', 'CreateNURBSTorus')):
    _specs.append(_entry('surface.create_' + suffix, label, 'Create', 'axismeld.m3_create',
                        kwargs={'kind': 'SURFACE_' + suffix.upper()}, maya=(maya,) if maya else (), section=('NURBS Primitives',), line=2563,
                        difference='Uses Blender native NURBS control points, dimensions and tessellation at the 3D Cursor.'))
for suffix, label, maya in (('locator', 'Locator (Empty)', 'CreateLocator'), ('empty_group', 'Empty Group', 'CreateEmptyGroup'),
                          ('text', 'Text', 'CreatePolygonType'), ('lattice', 'Lattice Object', '')):
    _specs.append(_entry('object.create_' + suffix, label, 'Create', 'axismeld.m3_create',
                        kwargs={'kind': suffix.upper()}, maya=(maya,) if maya else (), section=('Objects',), line=2768,
                        difference='Creates the named native Blender object at the 3D Cursor; no Maya construction-node network.'))
_specs.extend((
    _entry('object.create_collection', 'Collection from Selection...', 'Create', 'collection.create',
           invoke=True, section=('Object Collections',), line=3396, maya=('CreateSet',),
           difference='Blender Collections are organization/linking sets, not Maya transform groups or exclusive partitions.'),
    _entry('object.create_collection_instance', 'Collection Instance...', 'Create', 'object.collection_instance_add',
           invoke=True, section=('Object Collections',), line=2840),
    _entry('object.create_reference_image', 'Reference Image...', 'Create', 'object.empty_image_add',
           kwargs={'background': False}, invoke=True, maya=('CreateImagePlane',), section=('Objects',), line=2853),
    _entry('tool.measure', 'Measure Tool', 'Create', 'wm.tool_set_by_id', modes=ALL,
           kwargs={'name': 'builtin.measure'}, undo=False, replayable=False,
           maya=('DistanceTool',), section=('Measure',), difference='Uses the Blender viewport measurement tool; no persistent Maya measurement node.'),
))

for suffix, label, action, maya, event in (
        ('hide_selected', 'Hide Selected', 'HIDE_SELECTED', 'HideSelectedObjects', {'key': 'H', 'ctrl': True}),
        ('hide_unselected', 'Hide Unselected', 'HIDE_UNSELECTED', 'HideUnselectedObjects', {'key': 'H', 'alt': True}),
        ('show_selected', 'Show Selected', 'SHOW_SELECTED', 'ShowSelectedObjects', {'key': 'H', 'shift': True}),
        ('show_all', 'Show All', 'SHOW_ALL', 'ShowAll', {}),
        ('show_last_hidden', 'Show Last Hidden', 'SHOW_LAST', 'ShowLastHidden', {'key': 'H', 'ctrl': True, 'shift': True}),
        ('toggle_visibility', 'Toggle Visibility (Keep Selection)', 'TOGGLE', 'ToggleVisibilityAndKeepSelection', {'key': 'H'}),
        ('template', 'Template Objects', 'TEMPLATE', 'TemplateObject', {}),
        ('untemplate', 'Untemplate Objects', 'UNTEMPLATE', 'UntemplateObject', {}),
        ('bounds', 'Bounding Boxes', 'BOUNDS', 'ShowBoundingBox', {}),
        ('solid', 'Object Geometry', 'SOLID', 'ShowObjectGeometry', {}),
        ('wire', 'Object Wire Display', 'WIRE', '', {}),
        ('hide_bounds', 'No Bounding Box', 'TEXTURED', 'HideBoundingBox', {}),
        ('local_axes', 'Local Rotation Axes', 'AXES', 'ToggleLocalRotationAxes', {}),
        ('in_front', 'Draw In Front', 'IN_FRONT', '', {})):
    _specs.append(_entry('display.' + suffix, label, 'Display', 'axismeld.m3_object_display',
                        kwargs={'action': action}, modes=O, maya=(maya,) if maya else (),
                        section=('Object Display',), line=3474, **event,
                        difference='Blender per-view-layer display. Show Last Hidden tracks AxisMeld hides; Untemplate restores selected or the last templated batch and its saved flags.'))
for suffix, label, native, kwargs, maya in (
        ('hide_components', 'Hide Selected Components', 'hide', {'unselected': False}, ''),
        ('hide_other_components', 'Hide Unselected Components', 'hide', {'unselected': True}, 'HideUnselectedCVs'),
        ('show_components', 'Show All Components', 'reveal', {'select': False}, 'ShowAllPolyComponents')):
    _specs.append(_multi('display.' + suffix, label, 'Display', (
        _call('mesh.' + native, M, **kwargs), _call('curve.' + native, C, **kwargs)),
        maya=(maya,) if maya else (), section=('Component Display',), line=5282,
        key='H' if suffix == 'show_components' else None,
        ctrl=suffix == 'show_components', alt=suffix == 'show_components'))
_specs.extend((
    _entry('display.isolate', 'Toggle Local View', 'Display', 'view3d.localview', modes=ALL,
           invoke=True, undo=False, section=('Viewport',),
           difference='Blender Local View isolation, not a saved Maya isolate-set network.'),
    _entry('display.isolate_remove', 'Remove from Local View', 'Display', 'view3d.localview_remove_from',
           undo=False, requires='selection', section=('Viewport',)),
    _entry('display.frame_selected_all', 'Frame Selected in All Panes', 'Display', 'view3d.view_selected',
           modes=ALL, kwargs={'use_all_regions': True}, undo=False, key='F', shift=True,
           maya=('FrameSelectedWithoutChildrenInAllViews', 'FrameSelectedInAllViews'), section=('Frame',),
           difference='Frames selected Blender elements across quad regions; child handling follows native selection.'),
    _entry('display.frame_all_panes', 'Frame All in All Panes', 'Display', 'axismeld.m3_frame_all',
           modes=ALL, undo=False, key='A', shift=True, maya=('FrameAllInAllViews',), section=('Frame',)),
))

for action, label, maya in (
        ('CONTAINED_EDGES', 'Contained Edges', 'ConvertSelectionToContainedEdges'),
        ('CONTAINED_FACES', 'Contained Faces', 'ConvertSelectionToContainedFaces'),
        ('VERTEX_PERIMETER', 'Vertex Perimeter', 'ConvertSelectionToVertexPerimeter'),
        ('FACE_PERIMETER', 'Face Perimeter', 'ConvertSelectionToFacePerimeter')):
    _specs.append(_entry('selection.' + action.lower(), label, 'Select', 'axismeld.m3_selection_convert',
                        modes=M, kwargs={'action': action}, requires='mesh', maya=(maya,),
                        section=('Convert Selection',),
                        difference='Converts selected Blender mesh elements by containment or selected-region boundary.'))
_specs.append(_entry('selection.multi_component', 'Multi-Component', 'Select', 'axismeld.m3_selection_convert',
                    modes=M, kwargs={'action': 'MULTI'}, requires='mesh', maya=('SelectMultiComponentMask',),
                    key='F7', section=('Convert Selection',), difference='Enables Blender vertex, edge and face domains together; face-corner selection is separate data, not an interactive domain.'))
_specs.append(_entry('selection.surface_cv_boundary', 'Selected Surface CV Boundary', 'Select',
                    'axismeld.m3_selection_convert', modes=('EDIT_SURFACE',),
                    kwargs={'action': 'SURFACE_CV_BOUNDARY'}, maya=('SelectCVSelectionBoundary',),
                    section=('Curve and Surface Points',),
                    difference='Selects the U/V control-grid boundary of selected NURBS points; this is not a surface isoparm domain.'))
_specs.append(_entry('selection.face_path', 'Face Path', 'Select', 'mesh.shortest_path_select',
                    modes=M, requires='mesh', maya=('SelectFacePath',), section=('Mesh Components',),
                    difference='Uses two preselected Blender faces, not an interactive Maya path-picking context.'))
_specs.append(_entry('selection.control_points', 'Edit Control Points', 'Select', 'object.mode_set',
                    kwargs={'mode': 'EDIT'}, requires='object', maya=('SelectCVsMask',),
                    section=('Curve and Surface Points',), difference='Enters Blender Curve, Surface or Lattice Edit Mode.'))
for order in ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'):
    _specs.append(_entry('transform.rotation_order_' + order.lower(), order, 'Modify', 'axismeld.m3_rotation_order',
                        kwargs={'order': order}, requires='selection', maya=('ReorderRotationDialog',),
                        section=('Rotation Order',), difference='Changes Euler order while preserving the current local transform; animation curves are not resampled.'))
for action, label, maya in (('ADD', 'Add Custom Property...', 'AddAttribute'),
                          ('EDIT', 'Edit Custom Property...', 'RenameAttribute'),
                          ('DELETE', 'Delete Custom Property...', 'DeleteAttribute')):
    _specs.append(_entry('object.property_' + action.lower(), label, 'Modify', 'axismeld.m3_custom_property',
                        kwargs={'action': action}, invoke=True, requires='object', maya=(maya,),
                        section=('Custom Properties',), difference='Edits scalar custom properties on the active Blender object, not Maya attribute connections or compound attributes.'))
_specs.append(_entry('object.geometry_to_bounds', 'Geometry to Bounding Box', 'Modify', 'axismeld.m3_bounds',
                    requires='selection', maya=('GeometryToBoundingBox',), section=('Convert',),
                    difference='Replaces each modifier-free editable mesh with its local bounding box, preserving object transforms. Modifier stacks must be applied first.'))
for kind in ('SPHERE', 'CUBE', 'CYLINDER', 'CONE', 'PLANE', 'TORUS'):
    _specs.append(_entry('mesh.create_subdiv_' + kind.lower(), 'Subdivision ' + kind.title(), 'Create',
                        'axismeld.m3_create', kwargs={'kind': 'SUBDIV_' + kind},
                        maya=('CreateSubdiv' + kind.title(),), section=('Subdivision Primitives',),
                        difference='Creates a Blender polygon primitive with a level-2 Catmull-Clark modifier; Maya hierarchical subdivision components are not reproduced.'))
for action, label, maya in (('HIDE_ALL', 'Hide All Objects', 'HideAll'),
                          ('HIDE_GEOMETRY', 'Hide All Geometry', 'HideGeometry'),
                          ('SHOW_GEOMETRY', 'Show All Geometry', 'ShowGeometry'),
                          ('HIDE_DEFORMED', 'Hide Deforming Geometry', 'HideDeformingGeometry'),
                          ('SHOW_DEFORMED', 'Show Deforming Geometry', 'ShowDeformingGeometry')):
    _specs.append(_entry('display.' + action.lower(), label, 'Display', 'axismeld.m3_object_display',
                        kwargs={'action': action}, maya=(maya,), section=('Object Visibility',),
                        difference='Changes current-view-layer visibility; deforming geometry means mesh/curve/surface with enabled deformation modifiers.'))
_specs.append(_entry('transform.universal_tool', 'Universal Transform Tool', 'Modify', 'wm.tool_set_by_id',
                    modes=ALL, kwargs={'name': 'builtin.transform'}, undo=False, replayable=False,
                    key='T', ctrl=True, maya=('UniversalManip', 'MoveRotateScaleTool'), section=('Transform Actions',),
                    difference='Activates the native combined move/rotate/scale gizmo; Maya tool-specific manipulator options differ.'))
_specs.append(_entry('display.wire_color', 'Wireframe Color...', 'Display', 'axismeld.m3_wire_color',
                    invoke=True, requires='selection', maya=('SetWireframeColor',), section=('Object Display',),
                    difference='Sets selected Blender object colors and the current viewport wireframe-color source to Object; the same color is shared by solid Object color mode.'))
for action, label, maya in (
        ('SELECTED', 'Bake Selected Mesh History', 'DeleteHistory'),
        ('ALL', 'Bake All Mesh History', 'DeleteAllHistory'),
        ('SELECTED_NON_DEFORM', 'Bake Selected Mesh Non-Deformer History', 'BakeNonDefHistory'),
        ('ALL_NON_DEFORM', 'Bake All Mesh Non-Deformer History', 'BakeAllNonDefHistory')):
    _specs.append(_entry('edit.bake_' + action.lower(), label, 'Edit', 'axismeld.m3_bake_history',
                        kwargs={'action': action}, maya=(maya,), section=('Delete by Type',),
                        requires='selection' if action.startswith('SELECTED') else '',
                        key='D' if action == 'SELECTED' else None,
                        alt=action == 'SELECTED', shift=action == 'SELECTED',
                        difference='Bakes local single-user static mesh modifier stacks with native Apply. Non-deformer baking preserves OnlyDeform modifiers and requires topology modifiers to precede them; shared data, shape keys, animation/drivers/NLA, overrides, Collision application, disabled modifiers and interleaved stacks are unavailable. No Maya DG nodes are deleted.'))
for name, resolution in (('hull', 1), ('rough', 4), ('medium', 12), ('fine', 24)):
    _specs.append(_entry('display.nurbs_' + name, 'NURBS Sampling ' + name.title(), 'Display',
                        'axismeld.m3_curve_geometry', kwargs={'kind': 'RESOLUTION', 'resolution': resolution},
                        requires='object', maya=('NURBSSmoothness' + name.title(),), section=('NURBS Sampling',),
                        difference='Uses native curve/surface U/V sampling ' + str(resolution) +
                        '; Hull is minimum sampling, not Maya control-hull-only display. No rebuild or topology conversion.'))
for identifier, label, category, action, maya, difference in (
        ('transform.follow_curve', 'Place Along Active Curve', 'Modify', 'PATH', 'PositionAlongCurve',
         'Distributes selected static unparented unconstrained objects with zero delta location along one non-degenerate static standalone curve. Uses persistent native Follow Path constraints; resets base locations and preserves scales. Parent/constraint/modifier/bevel/taper/animation networks are unavailable. Closed splines use non-overlapping parameter fractions.'),
        ('object.replace_data', 'Replace with Active Object Data', 'Modify', 'REPLACE', 'ReplaceObjects',
         'Native Link Object Data replaces compatible selected targets with the active source datablock. Targets become linked instances; object transforms and existing modifiers remain.'),
        ('object.transfer_scalar_properties', 'Copy Active Scalar Custom Properties', 'Edit', 'TRANSFER', 'TransferAttributeValues',
         'Copies named string/number/boolean custom properties from active source to selected editable objects, creating missing keys. Any target non-scalar name collision or override disables the whole action; arrays, connections and Maya typed attributes are excluded.'),
        ('edit.delete_hook_modifiers', 'Delete All Hook Modifiers', 'Edit', 'DELETE_HOOK', 'DeleteAllClusters',
         'Removes native Hook modifiers scene-wide as the bounded Blender cluster-like influence adaptation. Influence objects and vertex groups remain; arbitrary Maya cluster nodes are not deleted.'),
        ('edit.delete_lattice_modifiers', 'Delete All Lattice Modifiers', 'Edit', 'DELETE_LATTICE', 'DeleteAllLattices',
         'Removes native Lattice modifiers scene-wide. Cage objects remain to preserve other references and shared ownership.'),
        ('edit.delete_nonlinear_modifiers', 'Delete All Nonlinear Modifiers', 'Edit', 'DELETE_NONLINEAR', 'DeleteAllNonLinearDeformers',
         'Removes native Simple Deform and Wave modifiers used by the adapted Maya nonlinear actions. Unrelated modifiers and influence objects remain.'),
        ('edit.delete_curve_modifiers', 'Delete All Curve Deform Modifiers', 'Edit', 'DELETE_CURVE', 'DeleteAllWires',
         'Removes native Curve modifiers scene-wide as the adapted wire family. Curve objects remain, including ordinary geometry and shared deform targets.')):
    _specs.append(_entry(identifier, label, category, 'axismeld.m3_relationship', kwargs={'action': action},
                        requires='' if action.startswith('DELETE_') else 'two_objects', maya=(maya,),
                        section=('Delete by Type',) if action.startswith('DELETE_') else ('Object Relationships',),
                        difference=difference + (' Animated/driven/NLA or override objects are unavailable; surviving modifiers retain their original instances during rollback.' if action.startswith('DELETE_') else '')))

SPECS = tuple(_specs)
del _specs

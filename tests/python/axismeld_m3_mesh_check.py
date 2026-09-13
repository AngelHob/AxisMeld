# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Factory-startup background checks for the trusted M3 mesh declarations and geometry."""
import math
from pathlib import Path
import sys

import bpy
import bmesh

SOURCE = Path(__file__).resolve().parents[2] / 'scripts' / 'modules'
sys.path.insert(0, str(SOURCE))
import axismeld
axismeld.__path__.insert(0, str(SOURCE / 'axismeld'))
from axismeld.modeling_mesh import SPECS
from axismeld import modeling_mesh_ops


def check(value, message):
    if not value:
        raise AssertionError(message)


def native(identifier):
    group, name = identifier.split('.')
    return getattr(getattr(bpy.ops, group), name)


def validate_properties(rna, kwargs):
    for key, value in kwargs.items():
        prop = rna.properties.get(key)
        check(prop is not None, (rna.identifier, key))
        if prop.type == 'ENUM':
            choices = {item.identifier for item in prop.enum_items}
            check(set(value) <= choices if prop.is_enum_flag else value in choices,
                  (rna.identifier, key, value, choices))
        elif prop.type == 'POINTER':
            validate_properties(prop.fixed_type, value)


def reset():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def cube(location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location)
    return bpy.context.object


def volume(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        return abs(bm.calc_volume(signed=True))
    finally:
        bm.free()
        evaluated.to_mesh_clear()


def run():
    for cls in modeling_mesh_ops.classes:
        if not getattr(cls, 'is_registered', False):
            bpy.utils.register_class(cls)
    check(len(SPECS) >= 100, ('coverage', len(SPECS)))
    check(len({spec.id for spec in SPECS}) == len(SPECS), 'duplicate mesh semantic IDs')
    check({spec.category for spec in SPECS} == {'Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display'},
          'four complete mesh categories')
    specs = {spec.id: spec for spec in SPECS}
    for spec in SPECS:
        check(spec.source and spec.difference, ('provenance', spec.id))
        for call in spec.calls:
            validate_properties(native(call.operator).get_rna_type(), dict(call.kwargs))
            if call.invoke:
                check(not spec.replayable, ('modal/UI Recent', spec.id))
    check(specs['mesh.extrude_region'].calls[0].operator == 'mesh.extrude_region_move',
          'extrude must preserve native macro completion')
    check(specs['mesh.extrude_region'].key == 'E' and specs['mesh.extrude_region'].ctrl,
          'Maya Ctrl E')
    check(specs['mesh.bevel_edges'].key == 'B' and specs['mesh.bevel_edges'].ctrl, 'Maya Ctrl B')
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    definitions = VIEW3D_PT_tools_active.tools_from_context(bpy.context, mode='EDIT_MESH')
    tool_ids = {tool.idname for tool in VIEW3D_PT_tools_active._tools_flatten_with_dynamic(
        definitions, context=bpy.context) if tool is not None}
    for spec in SPECS:
        if spec.id.startswith('tool.mesh_'):
            check(dict(spec.calls[0].kwargs)['name'] in tool_ids, ('registered tool', spec.id))
    for operation, expected in [('UNION', 12), ('DIFFERENCE', 4), ('INTERSECT', 4)]:
        reset()
        target = cube()
        operand = cube((1, 0, 0))
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        before = len(target.modifiers)
        bpy.ops.ed.undo_push(message='Boolean before')
        result = bpy.ops.axismeld.m3_mesh_boolean('EXEC_DEFAULT', True, operation=operation)
        check(result == {'FINISHED'}, ('boolean', operation, result))
        check(len(target.modifiers) == before + 1, 'one targeted modifier')
        modifier = target.modifiers[-1]
        check(modifier.object == operand and modifier.operation == operation, 'operand/operation')
        check(math.isclose(volume(target), expected, abs_tol=.001), ('evaluated volume', operation))
        target_name, operand_name = target.name, operand.name
        check(bpy.ops.ed.undo() == {'FINISHED'}, 'boolean single undo')
        check(len(bpy.data.objects[target_name].modifiers) == before and operand_name in bpy.data.objects,
              'undo restores both original meshes')
        check(bpy.ops.ed.redo() == {'FINISHED'}, 'boolean redo')
        check(math.isclose(volume(bpy.data.objects[target_name]), expected, abs_tol=.001), 'redo evaluation')
    reset()
    target = cube()
    check(not bpy.ops.axismeld.m3_mesh_boolean.poll(), 'boolean rejects missing operand')
    other = cube((1, 0, 0))
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    check(bpy.ops.axismeld.m3_mesh_boolean(operation='DIFFERENCE', reverse=True) == {'FINISHED'},
          'reverse boolean')
    check(len(target.modifiers) == 0 and other.modifiers[-1].object == target, 'B minus A target')
    check(math.isclose(volume(other), 4, abs_tol=.001), 'reverse evaluated volume')
    check(not modeling_mesh_ops.COMMAND_POLLS['mesh.boolean_union'](bpy.context),
          'boolean dependency cycle unavailable')
    other.modifiers.remove(other.modifiers[-1])
    # Evaluation failure is a true transaction rollback; inputs/previous modifiers stay intact.
    saved_evaluator = modeling_mesh_ops._evaluated_mesh
    evaluations = []
    def reject_evaluation(*args, **kwargs):
        evaluations.append(True)
        raise ValueError('test evaluation rejection')
    modeling_mesh_ops._evaluated_mesh = reject_evaluation
    before = (len(target.modifiers), len(other.modifiers), len(bpy.data.objects))
    try:
        check(bpy.ops.axismeld.m3_mesh_boolean(operation='UNION') == {'CANCELLED'}, 'failed boolean cancels')
        check(before == (len(target.modifiers), len(other.modifiers), len(bpy.data.objects)),
              'failed boolean leaves no new modifier or object')
        check(len(evaluations) == 1, 'failure injected after modifier creation and before commit')
    finally:
        modeling_mesh_ops._evaluated_mesh = saved_evaluator
    other.hide_set(True)
    check(not bpy.ops.axismeld.m3_mesh_boolean.poll(), 'hidden operand cannot execute')
    other.hide_set(False)
    for kind in modeling_mesh_ops._MODIFIERS:
        reset()
        if kind == 'skin':
            data = bpy.data.meshes.new('Wire')
            data.from_pydata([(0, 0, 0), (0, 0, 1), (1, 0, 2)], [(0, 1), (1, 2)], [])
            obj = bpy.data.objects.new('Wire', data)
            bpy.context.collection.objects.link(obj)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        else:
            obj = cube()
        bpy.ops.ed.undo_push(message='Modifier before')
        check(native('axismeld.m3_mesh_modifier_' + kind)('EXEC_DEFAULT', True) == {'FINISHED'},
              ('configured modifier', kind))
        check(len(obj.modifiers) == 1, ('one modifier', kind))
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        check(len(evaluated.data.vertices) > 0, ('actual evaluated mesh', kind))
        name = obj.name
        check(bpy.ops.ed.undo() == {'FINISHED'}, ('modifier undo', kind))
        check(len(bpy.data.objects[name].modifiers) == 0, ('modifier single undo', kind))
    reset()
    obj = cube()
    check(bpy.ops.axismeld.m3_mesh_modifier_subsurf() == {'FINISHED'}, 'subdivision modifier')
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    check(len(evaluated.data.polygons) > len(obj.data.polygons), 'subdivision actually evaluated')
    bpy.ops.ed.undo_push(message='Color before')
    check(bpy.ops.axismeld.m3_color_add('EXEC_DEFAULT', True, name='Test Colors') == {'FINISHED'}, 'color add')
    check(obj.data.color_attributes.active_color.name == 'Test Colors', 'active color attribute')
    check(bpy.ops.ed.undo() == {'FINISHED'} and not bpy.context.object.data.color_attributes, 'color add one undo')
    bpy.ops.ed.redo()
    obj = bpy.context.object
    check(bpy.ops.axismeld.m3_color_set('EXEC_DEFAULT', True, color=(.2, .4, .6, 1)) == {'FINISHED'}, 'color value')
    check(all(abs(value.color[1] - .4) < .001 for value in obj.data.color_attributes.active_color.data),
          'actual color data')
    bpy.ops.ed.undo()
    check(all(value.color[0] == 1 for value in bpy.context.object.data.color_attributes.active_color.data),
          'color set one undo')
    bpy.ops.ed.redo()
    obj = bpy.context.object
    # Edit color application is restricted to the selected face-corner domain.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    check(not bpy.ops.axismeld.m3_color_set.poll(), 'CORNER zero selection disabled')
    bm.edges.ensure_lookup_table()
    bm.edges[0].select_set(True)
    check(not bpy.ops.axismeld.m3_color_set.poll(), 'CORNER selected edge without face disabled')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.faces.ensure_lookup_table()
    bm.faces[0].select_set(True)
    check(bpy.ops.axismeld.m3_color_set(color=(1, 0, 0, 1)) == {'FINISHED'}, 'selected edit colors')
    layer = bm.loops.layers.float_color['Test Colors']
    check(all(loop[layer][0] == 1 for loop in bm.faces[0].loops), 'selected face colors changed')
    check(all(abs(loop[layer][0] - .2) < .001 for face in list(bm.faces)[1:] for loop in face.loops),
          'unselected colors unchanged')
    bpy.ops.object.mode_set(mode='OBJECT')
    check(bpy.ops.axismeld.m3_color_rename('EXEC_DEFAULT', True, name='Renamed') == {'FINISHED'}, 'color rename')
    check(obj.data.color_attributes.active_color.name == 'Renamed', 'renamed attribute')
    bpy.ops.ed.undo()
    check(bpy.context.object.data.color_attributes.active_color.name == 'Test Colors', 'rename one undo')
    bpy.ops.ed.redo()
    obj = bpy.context.object
    check(bpy.ops.geometry.color_attribute_convert(domain='POINT', data_type='BYTE_COLOR') == {'FINISHED'},
          'native color storage/domain conversion')
    check(obj.data.color_attributes.active_color.domain == 'POINT' and
          obj.data.color_attributes.active_color.data_type == 'BYTE_COLOR', 'converted attribute')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    check(not bpy.ops.axismeld.m3_color_set.poll(), 'POINT zero selection disabled')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.verts[0].select_set(True)
    check(bpy.ops.axismeld.m3_color_set.poll(), 'POINT selected vertex enabled')
    bm.verts[0].hide_set(True)
    check(not bpy.ops.axismeld.m3_color_set.poll(), 'POINT hidden vertex disabled')
    bm.verts[0].hide_set(False)
    bm.verts[0].select_set(True)
    check(bpy.ops.axismeld.m3_color_set(color=(.1, .3, .5, .7)) == {'FINISHED'}, 'BYTE edit color set')
    bpy.ops.object.mode_set(mode='OBJECT')
    actual = obj.data.color_attributes.active_color.data[0].color
    check(all(abs(a - b) < .005 for a, b in zip(actual, (.1, .3, .5, .7))),
          ('BYTE Edit/Object linear color agreement', tuple(actual)))
    check(bpy.ops.axismeld.m3_color_remove('EXEC_DEFAULT', True) == {'FINISHED'}, 'color remove')
    check(len(obj.data.color_attributes) == 0, 'removed only active attribute')
    bpy.ops.ed.undo()
    check(len(bpy.context.object.data.color_attributes) == 1, 'remove one undo')
    reset()
    cube()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    before = len(bmesh.from_edit_mesh(bpy.context.object.data).faces)
    call = specs['mesh.triangulate'].calls[0]
    check(native(call.operator)(**dict(call.kwargs)) == {'FINISHED'}, 'triangulate')
    check(len(bmesh.from_edit_mesh(bpy.context.object.data).faces) == before * 2, 'triangle topology')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    outward = bm.calc_volume(signed=True)
    bpy.ops.mesh.flip_normals()
    check(math.isclose(bm.calc_volume(signed=True), -outward, abs_tol=.001), 'normal reversal')
    reset()
    target = cube()
    cutter = cube((0, 0, 3))
    cutter.select_set(False)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode='EDIT')
    cutter.select_set(True)
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    region = next(region for region in area.regions if region.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        check(not modeling_mesh_ops.COMMAND_POLLS['mesh.project_cut'](bpy.context),
              'closed shell has no projection boundary')
        wire = bpy.data.meshes.new('Projection Wire')
        wire.from_pydata([(-1, 0, 0), (1, 0, 0)], [(0, 1)], [])
        cutter.data = wire
        check(modeling_mesh_ops.COMMAND_POLLS['mesh.project_cut'](bpy.context),
              'selected non-Edit wire projects')
        cutter.hide_set(True)
        check(not modeling_mesh_ops.COMMAND_POLLS['mesh.project_cut'](bpy.context),
              'hidden projection operand disabled')
    reset()
    cube()
    paint = specs['color.paint_mode']
    check(not paint.replayable and not paint.calls[0].undo, 'paint mode has no edit/replay claim')
    check(native(paint.calls[0].operator)(**dict(paint.calls[0].kwargs)) == {'FINISHED'}, 'native paint mode entry')
    check(bpy.context.mode == 'PAINT_VERTEX', 'actual Vertex Paint context')
    check(not modeling_mesh_ops.COMMAND_POLLS['color.paint_mode'](bpy.context), 'paint entry only Object mode')
    reset()
    one = cube()
    two = cube((4, 0, 0))
    one.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    for obj in (one, two):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.verts[0].select_set(True)
    check(not modeling_mesh_ops.COMMAND_POLLS['mesh.connect_path'](bpy.context),
          'connect path cannot add vertex counts across separate meshes')
    check(not modeling_mesh_ops.COMMAND_POLLS['mesh.connect_pairs'](bpy.context),
          'connect pairs requires a common face')
    bm = bmesh.from_edit_mesh(one.data)
    bm.faces.ensure_lookup_table()
    bpy.ops.mesh.select_all(action='DESELECT')
    vertices = list(bm.faces[0].verts)
    vertices[0].select_set(True)
    vertices[2].select_set(True)
    check(modeling_mesh_ops.COMMAND_POLLS['mesh.connect_path'](bpy.context),
          'two nonadjacent vertices in the same mesh enabled')
    check(bpy.ops.mesh.vert_connect_path() == {'FINISHED'}, 'valid native connect path')
    reset()
    cube()
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    region = next(region for region in area.regions if region.type == 'WINDOW')
    additions = {
        'display.crease_marks': 'show_edge_crease',
        'display.sharp_edges': 'show_edge_sharp',
        'display.face_centers': 'show_face_center',
        'display.component_indices': 'show_extra_indices',
    }
    check(set(additions) | {'display.distortion_analysis'} <= set(specs), 'native Display overlay coverage')
    with bpy.context.temp_override(area=area, region=region):
        for identifier in (*additions, 'display.distortion_analysis'):
            check(not modeling_mesh_ops.COMMAND_POLLS[identifier](bpy.context),
                  ('Edit-only overlay disabled in Object', identifier))
        bpy.ops.object.mode_set(mode='EDIT')
        overlay = bpy.context.space_data.overlay
        shading = bpy.context.space_data.shading
        shading.type = 'SOLID'
        shading.show_xray = False
        for identifier, attribute in additions.items():
            check(modeling_mesh_ops.COMMAND_POLLS[identifier](bpy.context), ('valid overlay', identifier))
            prior = {prop: getattr(overlay, prop) for prop in additions.values()}
            call = specs[identifier].calls[0]
            check(not call.undo and not specs[identifier].replayable, ('display no geometry undo', identifier))
            check(native(call.operator)(**dict(call.kwargs)) == {'FINISHED'}, ('overlay toggle', identifier))
            check(getattr(overlay, attribute) != prior[attribute], ('actual overlay property', identifier))
            check(modeling_mesh_ops.command_state(bpy.context, identifier) ==
                  ('checkbox', getattr(overlay, attribute)), ('live checkbox', identifier))
            check(all(getattr(overlay, prop) == value for prop, value in prior.items() if prop != attribute),
                  ('unrelated overlays preserved', identifier))
            native(call.operator)(**dict(call.kwargs))
            check(getattr(overlay, attribute) == prior[attribute], ('reversible toggle', identifier))
        statvis = bpy.context.scene.tool_settings.statvis
        statvis.type = 'SHARP'
        overlay.show_statvis = False
        call = specs['display.distortion_analysis'].calls[0]
        check(native(call.operator)() == {'FINISHED'}, 'distortion analysis enabled')
        check(statvis.type == 'DISTORT' and overlay.show_statvis, 'native distortion analysis state')
        check(modeling_mesh_ops.command_state(bpy.context, 'display.distortion_analysis') ==
              ('checkbox', True), 'distortion live checkbox')
        check(native(call.operator)() == {'FINISHED'} and not overlay.show_statvis,
              'distortion analysis toggles off')
        shading.show_xray = True
        shading.xray_alpha = .5
        check(not modeling_mesh_ops.COMMAND_POLLS['display.face_centers'](bpy.context),
              'native face centers unavailable with X-Ray')
        check(not modeling_mesh_ops.COMMAND_POLLS['display.distortion_analysis'](bpy.context),
              'native mesh analysis unavailable with translucent X-Ray')
        shading.show_xray = False
    print('M3_MESH_CHECK_PASS', len(SPECS), 'declarations, RNA, boolean volumes, modifiers, colors, topology')


run()

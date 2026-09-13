# SPDX-License-Identifier: GPL-2.0-or-later
"""Run with Blender --background --factory-startup --python (no installation writes)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'modules'))
import axismeld
axismeld.__path__.insert(0, str(ROOT / 'scripts' / 'modules' / 'axismeld'))
# A candidate installation can pre-load older M3 modules during startup. This
# isolated process must validate the owned source files, not that cached copy.
for module_name in ('axismeld.modeling_common_ops', 'axismeld.modeling_common'):
    sys.modules.pop(module_name, None)
from axismeld.modeling_common import SPECS


def declarations():
    ids = [item.id for item in SPECS]
    assert len(ids) == len(set(ids)), 'duplicate semantic IDs'
    assert {'edit.group', 'edit.ungroup', 'transform.match_all', 'edit.cut_objects',
            'selection.invert', 'edit.adjust_last_operation', 'display.show_last_hidden'} <= set(ids)
    assert all(item.category in {'Select', 'Modify', 'Edit', 'Create', 'Display'} for item in SPECS)
    assert all(item.source and item.difference for item in SPECS)
    assert not set(ids).intersection('mesh.create_' + kind for kind in (
        'disc', 'sphere', 'torus', 'cube', 'cone', 'cylinder', 'plane'))
    adjust = next(item for item in SPECS if item.id == 'edit.adjust_last_operation')
    assert not adjust.replayable and adjust.calls[0].invoke and not adjust.calls[0].undo
    assert not any(item.key == 'F9' and not item.ctrl for item in SPECS)


declarations()
print('AXISMELD_M3_COMMON_DECLARATIONS_PASS', len(SPECS), flush=True)

try:
    import bpy
except ImportError:
    bpy = None

if bpy is not None:
    import importlib
    implementation = importlib.import_module('axismeld.modeling_common_ops')
    from mathutils import Matrix
    from unittest.mock import patch

    for cls in implementation.classes:
        existing = getattr(bpy.types, cls.__name__, None)
        if existing is not None:
            bpy.utils.unregister_class(existing)
        bpy.utils.register_class(cls)
    from axismeld.modeling_shapes_ops import AXISMELD_OT_m3_curve_geometry
    if not hasattr(bpy.types, AXISMELD_OT_m3_curve_geometry.__name__):
        bpy.utils.register_class(AXISMELD_OT_m3_curve_geometry)

    failures = []
    for spec in SPECS:
        for call in spec.calls:
            native = implementation._operator(call.operator)
            try:
                properties = native.get_rna_type().properties
            except KeyError:
                failures.append((spec.id, call.operator, 'operator missing'))
                continue
            for key, value in call.kwargs:
                if key not in properties:
                    failures.append((spec.id, key, 'property missing'))
                elif properties[key].type == 'ENUM':
                    enum = {entry.identifier for entry in properties[key].enum_items_static}
                    if enum and value not in enum:
                        failures.append((spec.id, key, value, sorted(enum)))
    assert not failures, failures
    print('AXISMELD_M3_COMMON_RNA_PASS', flush=True)

    window = bpy.context.window_manager.windows[0]
    area = next(area for area in window.screen.areas if area.type == 'VIEW_3D')
    region = next(region for region in area.regions if region.type == 'WINDOW')
    print('COMMON_CHECK_ENTER_CONTEXT', flush=True)
    with bpy.context.temp_override(window=window, area=area, region=region):
        print('COMMON_CHECK_SETTINGS', flush=True)
        for identifier in (*implementation.SETTINGS, 'display.xray'):
            assert implementation._setting_available(bpy.context, identifier), identifier
            assert implementation.command_state(bpy.context, identifier)[0] in {'radio', 'checkbox'}
        print('COMMON_CHECK_SCENE_SETUP', flush=True)
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

        def cube(name, location):
            bpy.ops.mesh.primitive_cube_add(location=location)
            obj = bpy.context.active_object
            obj.name = name
            return obj

        def select(objects, active):
            implementation._restore_selection(bpy.context, set(objects), active)
            bpy.context.view_layer.update()

        def matrix_close(left, right):
            return all(abs(left[row][col] - right[row][col]) < 1e-5 for row in range(4) for col in range(4))

        a = cube('Common A', (1, 2, 3))
        b = cube('Common B', (-2, 4, 1))
        select((a, b), b)
        before = {obj.name: obj.matrix_world.copy() for obj in (a, b)}
        bpy.context.preferences.edit.use_global_undo = True
        host_undo = not bpy.app.background
        print('COMMON_CHECK_UNDO_PUSH', flush=True)
        if host_undo:
            bpy.ops.ed.undo_push(message='Before Common Group')
        print('COMMON_CHECK_GROUP', flush=True)
        assert bpy.ops.axismeld.m3_group('EXEC_DEFAULT', host_undo) == {'FINISHED'}
        bpy.context.view_layer.update()
        group = bpy.context.active_object
        assert group.type == 'EMPTY' and set(group.children) == {a, b}
        assert all(matrix_close(obj.matrix_world, before[obj.name]) for obj in (a, b))
        assert bpy.ops.axismeld.m3_ungroup('EXEC_DEFAULT', host_undo) == {'FINISHED'}
        bpy.context.view_layer.update()
        assert all(obj.parent is None and matrix_close(obj.matrix_world, before[obj.name]) for obj in (a, b))

        parent = bpy.data.objects.new('Shear Parent', None)
        bpy.context.scene.collection.objects.link(parent)
        parent.scale = (2.0, 0.7, 1.5)
        parent.rotation_euler = (0.3, 0.2, 0.4)
        a.parent = parent
        a.rotation_euler = (0.4, 0.5, 0.2)
        select((a,), a)
        original_world = a.matrix_world.copy()
        original_basis = a.matrix_basis.copy()
        assert bpy.ops.axismeld.m3_group('EXEC_DEFAULT', host_undo) == {'FINISHED'}
        bpy.context.view_layer.update()
        assert matrix_close(a.matrix_world, original_world), 'group discarded world shear'
        assert matrix_close(a.matrix_basis, original_basis), 'group changed local channels'
        assert bpy.ops.axismeld.m3_ungroup('EXEC_DEFAULT', host_undo) == {'FINISHED'}
        bpy.context.view_layer.update()
        assert a.parent == parent and matrix_close(a.matrix_world, original_world), 'ungroup discarded world shear'
        select((a, b), b)
        assert bpy.ops.axismeld.m3_match('EXEC_DEFAULT', host_undo, action='LOCATION') == {'FINISHED'}
        bpy.context.view_layer.update()
        expected = original_world.copy()
        expected.translation = b.matrix_world.translation
        assert matrix_close(a.matrix_world, expected), 'match location changed linear transform'
        print('AXISMELD_M3_COMMON_SHEAR_MATRICES_PASS', flush=True)
        a.parent = None
        a.matrix_world = Matrix.Translation((1, 2, 3))

        select((a, b), b)
        assert bpy.ops.axismeld.m3_match('EXEC_DEFAULT', host_undo, action='ALL') == {'FINISHED'}
        bpy.context.view_layer.update()
        assert matrix_close(a.matrix_world, b.matrix_world)
        before_objects = set(bpy.data.objects)
        with patch.object(implementation, '_copy_objects', return_value={'CANCELLED'}):
            assert bpy.ops.axismeld.m3_cut('EXEC_DEFAULT', host_undo) == {'CANCELLED'}
        assert set(bpy.data.objects) == before_objects, 'failed copy deleted objects'

        select((a,), a)
        assert bpy.ops.axismeld.m3_object_display('EXEC_DEFAULT', host_undo, action='HIDE_SELECTED') == {'FINISHED'}
        assert a.hide_get()
        assert implementation.COMMAND_POLLS['display.show_last_hidden'](bpy.context)
        assert bpy.ops.axismeld.m3_object_display('EXEC_DEFAULT', host_undo, action='SHOW_LAST') == {'FINISHED'}
        assert not a.hide_get()
        a.hide_select = False
        for identifier in ('display.hide_type_mesh', 'display.show_type_mesh'):
            assert bpy.ops.axismeld.m3_setting('EXEC_DEFAULT', False, action=identifier) == {'FINISHED'}
            assert bpy.context.space_data.show_object_viewport_mesh == identifier.startswith('display.show_')
        select((a,), a)
        axes = a.show_axis
        assert bpy.ops.axismeld.m3_object_display('EXEC_DEFAULT', host_undo, action='AXES') == {'FINISHED'}
        assert a.show_axis != axes
        assert bpy.ops.axismeld.m3_wire_color('EXEC_DEFAULT', host_undo, color=(0.2, 0.4, 0.6, 1.0)) == {'FINISHED'}
        assert abs(a.color[1] - 0.4) < 1e-5 and bpy.context.space_data.shading.wireframe_color_type == 'OBJECT'
        matrix = a.matrix_basis.copy()
        for order in ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'):
            assert bpy.ops.axismeld.m3_rotation_order('EXEC_DEFAULT', host_undo, order=order) == {'FINISHED'}
            assert a.rotation_mode == order and matrix_close(a.matrix_basis, matrix)
        assert bpy.ops.axismeld.m3_custom_property('EXEC_DEFAULT', host_undo, action='ADD', name='AuditValue',
            kind='INTEGER', value='5') == {'FINISHED'}
        assert a['AuditValue'] == 5
        assert bpy.ops.axismeld.m3_custom_property('EXEC_DEFAULT', host_undo, action='EDIT', property='AuditValue',
            name='AuditRenamed', kind='FLOAT', value='2.5') == {'FINISHED'}
        assert 'AuditValue' not in a and a['AuditRenamed'] == 2.5
        assert bpy.ops.axismeld.m3_custom_property('EXEC_DEFAULT', host_undo, action='DELETE',
            property='AuditRenamed') == {'FINISHED'}
        assert 'AuditRenamed' not in a
        old_data = a.data
        assert bpy.ops.axismeld.m3_bounds('EXEC_DEFAULT', host_undo) == {'FINISHED'}
        assert a.data != old_data and len(a.data.vertices) == 8 and len(a.data.polygons) == 6
        bpy.context.scene.cursor.location = (3.25, -1.75, 2.5)
        bpy.context.preferences.edit.use_enter_edit_mode = False
        for kind in implementation.CREATORS:
            before_count = len(bpy.data.objects)
            assert bpy.ops.axismeld.m3_create('EXEC_DEFAULT', host_undo, kind=kind) == {'FINISHED'}, kind
            obj = bpy.context.active_object
            assert len(bpy.data.objects) == before_count + 1 and bpy.context.mode == 'OBJECT', kind
            assert (obj.location - bpy.context.scene.cursor.location).length < 1e-5, kind
            if kind.startswith('SUBDIV_'):
                assert len(obj.modifiers) == 1 and obj.modifiers[0].type == 'SUBSURF', kind
            if obj.type == 'MESH':
                assert len(obj.data.vertices) > 0, kind
            elif obj.type in {'CURVE', 'SURFACE'}:
                assert len(obj.data.splines) > 0, kind
        print('AXISMELD_M3_COMMON_CREATORS_PASS', len(implementation.CREATORS), flush=True)
        data = bpy.data.meshes.new('Conversion Grid')
        data.from_pydata([(x, y, 0) for y in range(4) for x in range(4)], [],
                         [(y*4+x, y*4+x+1, (y+1)*4+x+1, (y+1)*4+x) for y in range(3) for x in range(3)])
        grid = bpy.data.objects.new('Conversion Grid', data)
        bpy.context.scene.collection.objects.link(grid)
        select((grid,), grid)
        bpy.ops.object.mode_set(mode='EDIT')
        import bmesh
        bm = bmesh.from_edit_mesh(data)
        for vert in bm.verts:
            vert.select_set(vert.index in {0, 1, 4, 5})
        bmesh.update_edit_mesh(data)
        assert bpy.ops.axismeld.m3_selection_convert('EXEC_DEFAULT', host_undo, action='CONTAINED_EDGES') == {'FINISHED'}
        assert sum(edge.select for edge in bm.edges) == 4
        assert bpy.ops.axismeld.m3_selection_convert('EXEC_DEFAULT', host_undo, action='CONTAINED_FACES') == {'FINISHED'}
        assert sum(face.select for face in bm.faces) == 1
        bpy.ops.mesh.select_all(action='SELECT')
        assert bpy.ops.axismeld.m3_selection_convert('EXEC_DEFAULT', host_undo, action='FACE_PERIMETER') == {'FINISHED'}
        assert sum(face.select for face in bm.faces) == 8
        bpy.ops.mesh.select_all(action='SELECT')
        assert bpy.ops.axismeld.m3_selection_convert('EXEC_DEFAULT', host_undo, action='VERTEX_PERIMETER') == {'FINISHED'}
        assert sum(vert.select for vert in bm.verts) == 12
        assert bpy.ops.axismeld.m3_selection_convert('EXEC_DEFAULT', host_undo, action='MULTI') == {'FINISHED'}
        assert tuple(bpy.context.tool_settings.mesh_select_mode) == (True, True, True)
        bpy.ops.object.mode_set(mode='OBJECT')
        assert bpy.ops.axismeld.m3_create('EXEC_DEFAULT', host_undo, kind='SURFACE_SURFACE') == {'FINISHED'}
        bpy.ops.object.mode_set(mode='EDIT')
        assert bpy.ops.axismeld.m3_selection_convert('EXEC_DEFAULT', host_undo, action='SURFACE_CV_BOUNDARY') == {'FINISHED'}
        for spline in bpy.context.active_object.data.splines:
            assert sum(point.select for point in spline.points) == 2 * spline.point_count_u + 2 * spline.point_count_v - 4
        bpy.ops.object.mode_set(mode='OBJECT')
        print('AXISMELD_M3_COMMON_SELECTION_CONVERSION_PASS', flush=True)
        surface = bpy.context.active_object
        for resolution in (1, 4, 12, 24):
            assert bpy.ops.axismeld.m3_curve_geometry('EXEC_DEFAULT', host_undo, kind='RESOLUTION',
                                                     resolution=resolution) == {'FINISHED'}
            assert surface.data.resolution_u == resolution and surface.data.resolution_v == resolution
        assert bpy.ops.axismeld.m3_setting('EXEC_DEFAULT', False, action='display.curve_normals') == {'FINISHED'}
        print('AXISMELD_M3_COMMON_NURBS_DISPLAY_PASS', flush=True)
        baked = cube('History Bake', (0, 0, 0))
        topology = baked.modifiers.new('Topology', 'SUBSURF')
        topology.levels = 1
        deform = baked.modifiers.new('Preserved Deform', 'SIMPLE_DEFORM')
        deform.deform_method = 'TWIST'
        deform.angle = 0.4
        select((baked,), baked)
        linked = bpy.data.objects.new('Shared Bake Data', baked.data)
        bpy.context.scene.collection.objects.link(linked)
        assert not implementation.COMMAND_POLLS['edit.bake_selected_non_deform'](bpy.context)
        bpy.data.objects.remove(linked, do_unlink=True)
        assert implementation.COMMAND_POLLS['edit.bake_selected_non_deform'](bpy.context)
        assert bpy.ops.axismeld.m3_bake_history('EXEC_DEFAULT', host_undo, action='SELECTED_NON_DEFORM') == {'FINISHED'}
        assert len(baked.data.vertices) == 26 and len(baked.modifiers) == 1
        assert baked.modifiers[0].name == 'Preserved Deform' and baked.modifiers[0].angle == deform.angle
        backup = baked.copy()
        bpy.context.scene.collection.objects.link(backup)
        original_angle = baked.modifiers[0].angle
        baked.modifiers.clear()
        implementation._restore_modifier_stack(bpy.context, baked, backup)
        assert len(baked.modifiers) == 1 and baked.modifiers[0].type == 'SIMPLE_DEFORM'
        assert baked.modifiers[0].name == 'Preserved Deform' and baked.modifiers[0].angle == original_angle
        bpy.data.objects.remove(backup, do_unlink=True)
        failed_data = baked.data
        failed_objects = set(bpy.data.objects)
        try:
            with patch.object(implementation, '_apply_modifier', return_value={'CANCELLED'}):
                bpy.ops.axismeld.m3_bake_history('EXEC_DEFAULT', host_undo, action='SELECTED')
        except RuntimeError:
            pass
        assert baked.data == failed_data and len(baked.modifiers) == 1
        assert set(bpy.data.objects) == failed_objects, 'failed bake leaked temporary object'
        assert bpy.ops.axismeld.m3_bake_history('EXEC_DEFAULT', host_undo, action='SELECTED') == {'FINISHED'}
        assert not baked.modifiers
        first = cube('History All First', (0, 0, 0))
        first.modifiers.new('All First', 'SUBSURF').levels = 1
        second = cube('History All Second', (3, 0, 0))
        second.modifiers.new('All Second', 'SUBSURF').levels = 1
        select((second,), second)
        assert bpy.ops.axismeld.m3_bake_history('EXEC_DEFAULT', host_undo, action='ALL_NON_DEFORM') == {'FINISHED'}
        assert not first.modifiers and not second.modifiers
        assert len(first.data.vertices) == 26 and len(second.data.vertices) == 26
        print('AXISMELD_M3_COMMON_HISTORY_BAKE_PASS', flush=True)
        select((first, second), second)
        first_matrix = first.matrix_world.copy()
        assert bpy.ops.axismeld.m3_relationship('EXEC_DEFAULT', host_undo, action='REPLACE') == {'FINISHED'}
        assert first.data == second.data and matrix_close(first.matrix_world, first_matrix)
        second['TransferScalar'] = 9.25
        second['TransferString'] = 'source'
        second['ExcludedArray'] = [1, 2, 3]
        first['TransferScalar'] = -1.0
        first['TransferString'] = [1, 2, 3]
        assert not implementation.COMMAND_POLLS['object.transfer_scalar_properties'](bpy.context)
        assert list(first['TransferString']) == [1, 2, 3]
        del first['TransferString']
        assert bpy.ops.axismeld.m3_relationship('EXEC_DEFAULT', host_undo, action='TRANSFER') == {'FINISHED'}
        assert first['TransferScalar'] == 9.25 and first['TransferString'] == 'source' and 'ExcludedArray' not in first
        for action, native in (('DELETE_HOOK', 'HOOK'), ('DELETE_LATTICE', 'LATTICE'),
                               ('DELETE_NONLINEAR', 'SIMPLE_DEFORM'), ('DELETE_CURVE', 'CURVE')):
            first.modifiers.new('Family Remove', native)
            second.modifiers.new('Family Remove Other', native)
            retained = first.modifiers.new('Family Retained', 'BEVEL')
            select((second,), second)
            assert bpy.ops.axismeld.m3_relationship('EXEC_DEFAULT', host_undo, action=action) == {'FINISHED'}
            assert all(mod.type != native for obj in (first, second) for mod in obj.modifiers)
            assert retained in list(first.modifiers)
            first.modifiers.remove(retained)
        hook_target = bpy.data.objects.new('Hook Target', None)
        bpy.context.scene.collection.objects.link(hook_target)
        expected_hooks = {}
        for obj in (first, second):
            hook = obj.modifiers.new('Rollback Hook', 'HOOK')
            hook.object = hook_target
            hook.vertex_indices_set((0, 2, 4))
            hook.matrix_inverse = Matrix.Translation((1, 2, 3))
            hook.strength = 0.35
            obj.modifiers.new('Surviving Bevel', 'BEVEL')
            expected_hooks[obj] = tuple(mod.name for mod in obj.modifiers)
        real_remove = implementation._remove_modifier
        removal_count = [0]
        def fail_second_remove(obj, modifier):
            real_remove(obj, modifier)
            removal_count[0] += 1
            if removal_count[0] == 2:
                raise RuntimeError('Injected second Hook removal failure')
        try:
            with patch.object(implementation, '_remove_modifier', side_effect=fail_second_remove):
                bpy.ops.axismeld.m3_relationship('EXEC_DEFAULT', host_undo, action='DELETE_HOOK')
        except RuntimeError:
            pass
        for obj in (first, second):
            assert tuple(mod.name for mod in obj.modifiers) == expected_hooks[obj]
            hook = obj.modifiers['Rollback Hook']
            assert hook.object == hook_target and tuple(hook.vertex_indices) == (0, 2, 4)
            assert abs(hook.strength - 0.35) < 1e-6 and matrix_close(hook.matrix_inverse, Matrix.Translation((1, 2, 3)))
        print('AXISMELD_M3_COMMON_HOOK_ROLLBACK_PASS', flush=True)
        first.driver_add('location', 0)
        assert not implementation.COMMAND_POLLS['edit.delete_hook_modifiers'](bpy.context)
        first.driver_remove('location', 0)
        assert bpy.ops.axismeld.m3_create('EXEC_DEFAULT', host_undo, kind='CURVE_PATH') == {'FINISHED'}
        path = bpy.context.active_object
        select((first, second, path), path)
        path.parent = first
        bpy.context.view_layer.update()
        assert not implementation.COMMAND_POLLS['transform.follow_curve'](bpy.context), 'path parent cycle was enabled'
        path.parent = None
        bpy.context.view_layer.update()
        first.delta_location.x = 1.0
        assert not implementation.COMMAND_POLLS['transform.follow_curve'](bpy.context)
        first.delta_location.x = 0.0
        path.data.driver_add('bevel_depth')
        assert not implementation.COMMAND_POLLS['transform.follow_curve'](bpy.context)
        path.data.driver_remove('bevel_depth')
        saved_points = [tuple(point.co) for point in path.data.splines[0].points]
        for point in path.data.splines[0].points:
            point.co = (0, 0, 0, 1)
        assert not implementation.COMMAND_POLLS['transform.follow_curve'](bpy.context)
        for point, co in zip(path.data.splines[0].points, saved_points):
            point.co = co
        assert bpy.ops.axismeld.m3_relationship('EXEC_DEFAULT', host_undo, action='PATH') == {'FINISHED'}
        bpy.context.view_layer.update()
        assert all(obj.constraints[0].type == 'FOLLOW_PATH' and obj.constraints[0].target == path
                   for obj in (first, second))
        assert {first.constraints[0].offset_factor, second.constraints[0].offset_factor} == {0.0, 1.0}
        assert (first.matrix_world.translation - second.matrix_world.translation).length > 1.0
        first.constraints.clear()
        second.constraints.clear()
        path.data.splines[0].use_cyclic_u = True
        assert bpy.ops.axismeld.m3_relationship('EXEC_DEFAULT', host_undo, action='PATH') == {'FINISHED'}
        assert {first.constraints[0].offset_factor, second.constraints[0].offset_factor} == {0.0, 0.5}
        print('AXISMELD_M3_COMMON_RELATIONSHIPS_PASS', flush=True)
        a.display_type = 'BOUNDS'
        select((a,), a)
        assert bpy.ops.axismeld.m3_object_display('EXEC_DEFAULT', host_undo, action='TEMPLATE') == {'FINISHED'}
        assert bpy.ops.axismeld.m3_object_display('EXEC_DEFAULT', host_undo, action='UNTEMPLATE') == {'FINISHED'}
        assert not a.hide_select and a.display_type == 'BOUNDS', 'untemplate lost original display flags'
        a.hide_select = False
        print('AXISMELD_M3_COMMON_COMPOUND_RESULTS_PASS', flush=True)

        # Background Blender may not own an initialized window undo history. Report
        # that limitation explicitly; the GUI integration suite must verify one step.
        if host_undo and bpy.ops.ed.undo.poll():
            assert bpy.ops.ed.undo() == {'FINISHED'}
            print('AXISMELD_M3_COMMON_BACKGROUND_UNDO_AVAILABLE', flush=True)
        else:
            print('AXISMELD_M3_COMMON_UNDO_REQUIRES_GUI_HISTORY', flush=True)
    print('AXISMELD_M3_COMMON_CHECK_PASS', flush=True)

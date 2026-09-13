# SPDX-License-Identifier: GPL-2.0-or-later
"""Background RNA, actual curve/surface/deformer geometry and rollback contracts."""
import sys
from pathlib import Path
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
import axismeld
axismeld.__path__.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules/axismeld'))
from axismeld.modeling_shapes import SPECS
from axismeld.modeling_shapes_ops import classes

for cls in classes:
    if not cls.is_registered:
        bpy.utils.register_class(cls)
assert len({s.id for s in SPECS}) == len(SPECS)
assert {s.category for s in SPECS} == {'Curves', 'Surfaces', 'Deform'}
for spec in SPECS:
    for call in spec.calls:
        group, name = call.operator.split('.')
        operator = getattr(getattr(bpy.ops, group), name)
        rna = operator.get_rna_type()
        for key, value in call.kwargs:
            assert key in rna.properties, (spec.id, key)
            prop = rna.properties[key]
            if prop.type == 'ENUM':
                assert value in prop.enum_items, (spec.id, key, value)
assert any(s.id == 'deform.lattice' for s in SPECS)
assert any(s.id == 'deform.mesh_bind' for s in SPECS)
print('M3_SHAPES_RNA_PASS', len(SPECS), flush=True)


def clean():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def mesh_fixture():
    clean()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=8, y_subdivisions=8, size=2)
    obj = bpy.context.object
    for vertex in obj.data.vertices:
        vertex.co.z = 0.3 * vertex.co.x * vertex.co.y + 0.1 * vertex.co.x
    obj.data.update()
    return obj


def evaluated(obj):
    bpy.context.view_layer.update()
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    result = tuple(tuple(vertex.co) for vertex in mesh.vertices)
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    return result


def changed(first, second):
    return len(first) != len(second) or any(abs(a - b) > 1e-5
        for v1, v2 in zip(first, second) for a, b in zip(v1, v2))


for kind in ('BEND', 'TWIST', 'TAPER', 'STRETCH', 'WAVE', 'LATTICE',
             'CORRECTIVE_SMOOTH', 'SMOOTH', 'LAPLACIANSMOOTH', 'CAST', 'DISPLACE', 'SOLIDIFY'):
    obj = mesh_fixture()
    before = evaluated(obj)
    assert bpy.ops.axismeld.m3_deform(kind=kind) == {'FINISHED'}, kind
    assert changed(before, evaluated(obj)), ('no evaluated effect', kind)
    print('M3_SHAPES_GEOMETRY', kind, flush=True)

obj = mesh_fixture()
original = evaluated(obj)
for kind in ('SHRINKWRAP', 'SURFACE_DEFORM', 'MESH_DEFORM', 'CURVE', 'WARP', 'LAPLACIANDEFORM'):
    assert bpy.ops.axismeld.m3_deform(kind=kind) == {'CANCELLED'}, kind
    assert len(obj.modifiers) == 0 and evaluated(obj) == original

for kind in ('SHRINKWRAP', 'SURFACE_DEFORM', 'MESH_DEFORM'):
    obj = mesh_fixture()
    bpy.ops.mesh.primitive_cube_add(size=6)
    target = bpy.context.object
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    before = evaluated(obj)
    assert bpy.ops.axismeld.m3_deform(kind=kind) == {'FINISHED'}, kind
    if kind != 'SHRINKWRAP':
        assert not changed(before, evaluated(obj)), (kind, 'binding should keep rest shape')
        for vertex in target.data.vertices:
            vertex.co.z += 0.75
        target.data.update()
    assert changed(before, evaluated(obj)), ('target has no effect', kind)
    print('M3_SHAPES_TARGET', kind, flush=True)

obj = mesh_fixture()
before = evaluated(obj)
bpy.ops.curve.primitive_bezier_curve_add()
target = bpy.context.object
target.data.splines[0].bezier_points[1].co.z += 2
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
assert bpy.ops.axismeld.m3_deform(kind='CURVE', axis='X') == {'FINISHED'}
assert changed(before, evaluated(obj))

obj = mesh_fixture()
before = evaluated(obj)
for i in range(2):
    bpy.ops.object.empty_add(location=(0, 0, i + 1))
    bpy.context.object.name = 'Warp' + str(i)
for empty in bpy.data.objects:
    if empty.type == 'EMPTY':
        empty.select_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
assert bpy.ops.axismeld.m3_deform(kind='WARP') == {'FINISHED'}
assert changed(before, evaluated(obj))

obj = mesh_fixture()
before = evaluated(obj)
for vertex in obj.data.vertices:
    vertex.select = vertex.index < 8
assert bpy.ops.axismeld.m3_deform(kind='LAPLACIANDEFORM') == {'FINISHED'}
assert changed(before, evaluated(obj))

obj = mesh_fixture()
before = evaluated(obj)
target = obj.copy()
target.data = obj.data.copy()
bpy.context.collection.objects.link(target)
target.location.z += 0.4
target.select_set(True)
assert bpy.ops.axismeld.m3_shape_targets() == {'FINISHED'}
assert len(obj.data.shape_keys.key_blocks) == 2
assert changed(before, evaluated(obj))

obj = mesh_fixture()
bpy.ops.object.mode_set(mode='EDIT')
assert bpy.ops.axismeld.m3_hook() == {'FINISHED'}
bpy.ops.object.mode_set(mode='OBJECT')
assert any(m.type == 'HOOK' and m.object for m in obj.modifiers)
assert changed(tuple(tuple(v.co) for v in obj.data.vertices), evaluated(obj))

clean()
bpy.ops.curve.primitive_bezier_curve_add()
curve = bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
before = len(curve.data.splines[0].bezier_points)
assert bpy.ops.curve.subdivide(number_cuts=1) == {'FINISHED'}
assert len(curve.data.splines[0].bezier_points) > before
clean()
bpy.ops.surface.primitive_nurbs_surface_curve_add()
surface = bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
assert bpy.ops.curve.spin(center=(0, 0, 0), axis=(0, 0, 1)) == {'FINISHED'}
assert surface.data.splines[0].point_count_v > 1
print('M3_SHAPES_ALL_PASS', flush=True)

from mathutils import Matrix, Vector
from axismeld.modeling_shapes_ops import COMMAND_POLLS
obj = mesh_fixture()
bpy.ops.object.empty_add()
parent = bpy.context.object
parent.scale = (2.0, 0.75, 1.5)
parent.rotation_euler = (0.2, 0.3, 0.4)
obj.parent = parent
obj.rotation_euler = (0.3, 0.5, 0.2)
obj.scale = (0.6, 1.2, 0.8)
bpy.context.view_layer.objects.active = obj
bpy.context.view_layer.update()
low = Vector(tuple(min(v[i] for v in obj.bound_box) for i in range(3)))
high = Vector(tuple(max(v[i] for v in obj.bound_box) for i in range(3)))
expected = obj.matrix_world @ Matrix.Translation((low + high) * .5) @ Matrix.Diagonal(
    tuple(max(high[i] - low[i], .01) * 1.05 for i in range(3)) + (1.,))
assert bpy.ops.axismeld.m3_deform(kind='LATTICE') == {'FINISHED'}
cage = obj.modifiers[-1].object
assert all(abs(cage.matrix_world[i][j] - expected[i][j]) < 1e-5 for i in range(4) for j in range(4)), 'parent shear cage placement'
clean()
bpy.ops.curve.primitive_bezier_curve_add()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.curve.select_all(action='DESELECT')
assert not COMMAND_POLLS['curve.subdivide'](bpy.context)
assert not COMMAND_POLLS['curve.handle_auto'](bpy.context)
print('M3_SHAPES_CONTEXT_PASS', flush=True)

for kind in ('SURFACE_DEFORM', 'MESH_DEFORM'):
    obj = mesh_fixture()
    bpy.ops.mesh.primitive_cube_add(size=6)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.axismeld.m3_deform(kind=kind) == {'FINISHED'}
    assert bpy.ops.axismeld.m3_deform_manage(kind=kind, action='UNBIND') == {'FINISHED'}
    assert not obj.modifiers[-1].is_bound
    assert bpy.ops.axismeld.m3_deform_manage(kind=kind, action='BIND') == {'FINISHED'}
    assert obj.modifiers[-1].is_bound
obj = mesh_fixture()
bpy.ops.mesh.primitive_plane_add(size=6)
target = bpy.context.object
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
assert bpy.ops.axismeld.m3_deform(kind='MESH_DEFORM') == {'CANCELLED'}
assert not obj.modifiers
assert bpy.ops.axismeld.m3_deform(kind='SHRINKWRAP') == {'FINISHED'}
assert bpy.ops.axismeld.m3_deform_manage(kind='SHRINKWRAP', action='CLEAR_TARGET') == {'FINISHED'}
assert obj.modifiers[-1].target is None
assert bpy.ops.axismeld.m3_deform_manage(kind='SHRINKWRAP', action='SET_TARGET') == {'FINISHED'}
assert obj.modifiers[-1].target == target
clean()
bpy.ops.curve.primitive_bezier_curve_add()
path = bpy.context.object
bpy.ops.curve.primitive_bezier_circle_add(radius=.15)
profile = bpy.context.object
path.select_set(True)
bpy.context.view_layer.objects.active = path
assert bpy.ops.axismeld.m3_curve_geometry(kind='PROFILE') == {'FINISHED'}
assert path.data.bevel_object == profile
assert len(evaluated(path)) > 0
print('M3_SHAPES_BIND_MANAGEMENT_PASS', flush=True)
for fixture in ('MESH', 'CURVE', 'EMPTY'):
    clean()
    if fixture == 'MESH':
        bpy.ops.mesh.primitive_cube_add()
    elif fixture == 'CURVE':
        bpy.ops.curve.primitive_bezier_curve_add()
    else:
        bpy.ops.object.empty_add()
    for command, poll in COMMAND_POLLS.items():
        assert isinstance(bool(poll(bpy.context)), bool), command
clean()
for poll in COMMAND_POLLS.values():
    assert not poll(bpy.context)
print('M3_SHAPES_CROSS_CONTEXT_PASS', flush=True)
clean()
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=3)
bpy.ops.object.mode_set(mode='OBJECT')
before = evaluated(obj)
assert bpy.ops.axismeld.m3_deform(kind='DISPLACE') == {'FINISHED'}
assert changed(before, evaluated(obj)), 'regular .5-unit Cube grid must not sample only neutral noise'
assert obj.modifiers[-1].texture_coords == 'GLOBAL'
assert abs(obj.modifiers[-1].texture.noise_scale - .37) < 1e-6
print('M3_SHAPES_REGULAR_CUBE_DISPLACE_PASS', flush=True)

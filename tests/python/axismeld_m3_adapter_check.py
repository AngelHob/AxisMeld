# SPDX-License-Identifier: GPL-2.0-or-later
"""M3 selection-domain regression and read-only availability across modeling contexts."""
from pathlib import Path
import sys
import bpy
import bmesh

SOURCE = Path(__file__).resolve().parents[2] / 'scripts' / 'modules'
sys.path.insert(0, str(SOURCE))
import axismeld
axismeld.__path__.insert(0, str(SOURCE / 'axismeld'))
from axismeld import modeling_adapter as adapter
from axismeld.modeling_registry import SPECS

REQUIREMENTS = {'', 'object', 'mesh', 'selection', 'two_objects', 'two_mesh',
                'vertices', 'edges', 'faces', 'two_vertices', 'two_edges',
                'merge_history', 'face_projection'}
assert {spec.requires for spec in SPECS.values()} <= REQUIREMENTS
assert {spec.classification for spec in SPECS.values()} <= {'adapted', 'blender'}
for module in adapter._modules():
    for cls in module.classes:
        if not cls.is_registered:
            bpy.utils.register_class(cls)


def clean():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def mesh(points, edges=()):
    data = bpy.data.meshes.new('Adapter Fixture')
    data.from_pydata(points, edges, [])
    obj = bpy.data.objects.new('Adapter Fixture', data)
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    return obj


clean()
objects = [mesh([(0, 0, 0)]), mesh([(1, 0, 0)])]
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
assert not adapter._requirement(bpy.context, 'two_vertices'), 'never combine counts across independent meshes'
assert not adapter._requirement(bpy.context, 'merge_history')
clean()
objects = [mesh([(0, 0, 0), (1, 0, 0)], [(0, 1)]), mesh([(0, 1, 0), (1, 1, 0)], [(0, 1)])]
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
assert not adapter._requirement(bpy.context, 'two_edges'), 'one edge per independent mesh is not two edges'
assert adapter._requirement(bpy.context, 'two_vertices')
bm = bmesh.from_edit_mesh(objects[0].data)
bm.verts.ensure_lookup_table()
bm.select_history.clear()
bm.select_history.add(bm.verts[0])
assert adapter._requirement(bpy.context, 'merge_history')
bm.verts[0].select = False
assert not adapter._requirement(bpy.context, 'merge_history'), 'history vertex must remain selected'
bm.verts[0].select = True
bm.verts[0].hide = True
assert not adapter._requirement(bpy.context, 'merge_history'), 'hidden history must not enable merge'
print('M3_ADAPTER_PER_MESH_SELECTION_PASS', flush=True)

area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
region = next(region for region in area.regions if region.type == 'WINDOW')


def check_available(tag):
    with bpy.context.temp_override(area=area, region=region):
        for command in SPECS:
            available, reason = adapter.available(bpy.context, command)
            assert isinstance(available, bool) and isinstance(reason, str), (tag, command)
            adapter.command_state(bpy.context, command)
    print('M3_ADAPTER_CONTEXT_PASS', tag, flush=True)


for kind in ('EMPTY_SCENE', 'EMPTY', 'MESH', 'CURVE', 'SURFACE', 'LATTICE'):
    clean()
    if kind == 'EMPTY':
        bpy.ops.object.empty_add()
    elif kind == 'MESH':
        bpy.ops.mesh.primitive_cube_add()
    elif kind == 'CURVE':
        bpy.ops.curve.primitive_bezier_curve_add()
    elif kind == 'SURFACE':
        bpy.ops.surface.primitive_nurbs_surface_surface_add()
    elif kind == 'LATTICE':
        bpy.ops.object.add(type='LATTICE')
    check_available(kind + '_OBJECT')
    if kind in {'MESH', 'CURVE', 'SURFACE', 'LATTICE'}:
        bpy.ops.object.mode_set(mode='EDIT')
        check_available(kind + '_EDIT_SELECTED')
        select = bpy.ops.mesh.select_all if kind == 'MESH' else bpy.ops.lattice.select_all if kind == 'LATTICE' else bpy.ops.curve.select_all
        select(action='DESELECT')
        check_available(kind + '_EDIT_EMPTY')
        if kind in {'CURVE', 'SURFACE'}:
            with bpy.context.temp_override(area=area, region=region):
                prefix = 'curve.' if kind == 'CURVE' else 'surface.'
                assert not adapter.available(bpy.context, prefix + 'subdivide')[0]
                assert not adapter.available(bpy.context, prefix + 'duplicate')[0]
print('M3_ADAPTER_CHECK_PASS', len(SPECS), flush=True)

# Independent regressions for matrix preservation and failure-state restoration.
from axismeld import modeling_common_ops as common


def close_matrix(a, b):
    return all(abs(a[i][j] - b[i][j]) < 1e-5 for i in range(4) for j in range(4))


clean()
bpy.ops.object.empty_add()
parent = bpy.context.object
parent.scale = (2, .7, 1.5)
parent.rotation_euler = (.3, .2, .4)
bpy.ops.mesh.primitive_cube_add()
source = bpy.context.object
source.parent = parent
source.rotation_euler = (.4, .5, .2)
bpy.context.view_layer.update()
original = source.matrix_world.copy()
assert bpy.ops.axismeld.m3_group() == {'FINISHED'}
group = bpy.context.object
bpy.context.view_layer.update()
assert close_matrix(source.matrix_world, original), 'Group must preserve inherited shear'
assert bpy.ops.axismeld.m3_ungroup() == {'FINISHED'}
bpy.context.view_layer.update()
assert close_matrix(source.matrix_world, original), 'Ungroup must preserve inherited shear'
assert source.select_get() and bpy.context.object == source
assert source.parent == parent
bpy.ops.mesh.primitive_cube_add(location=(5, 3, 2))
target = bpy.context.object
source.select_set(True)
bpy.context.view_layer.update()
expected = source.matrix_world.copy()
expected.translation = target.matrix_world.translation
assert bpy.ops.axismeld.m3_match(action='LOCATION') == {'FINISHED'}
bpy.context.view_layer.update()
assert close_matrix(source.matrix_world, expected), 'Match Location must preserve linear transform'
print('M3_COMMON_INDEPENDENT_MATRICES_PASS', flush=True)

clean()
bpy.ops.mesh.primitive_cube_add()
first = bpy.context.object
bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0))
second = bpy.context.object
first.select_set(True)
bpy.context.view_layer.objects.active = first
selected_before = set(bpy.context.selected_objects)


class FailHideOnce:
    """Inject a failure after the second real native hide operation has changed selection."""
    def __init__(self, obj):
        self.obj = obj
        self.failed = False

    def __getattr__(self, name):
        return getattr(self.obj, name)

    def __contains__(self, name):
        return name in self.obj

    def hide_set(self, value):
        self.obj.hide_set(value)
        if value and not self.failed:
            self.failed = True
            raise RuntimeError('Independent test: fail after hiding second object')


original_batch = common._display_batch
proxy = FailHideOnce(second)
common._display_batch = lambda context, action: (first, proxy)
try:
    try:
        result = bpy.ops.axismeld.m3_object_display(action='HIDE_ALL')
    except RuntimeError as error:
        # Blender raises the operator's ERROR report even when execute returns CANCELLED.
        assert 'Independent test:' in str(error)
        result = {'CANCELLED'}
    assert result == {'CANCELLED'} and proxy.failed
finally:
    common._display_batch = original_batch
assert not first.hide_get() and not second.hide_get()
assert set(bpy.context.selected_objects) == selected_before
assert bpy.context.view_layer.objects.active == first
print('M3_COMMON_INDEPENDENT_HIDE_ROLLBACK_PASS', flush=True)

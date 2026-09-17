# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Blender Mesh/BMesh results; run inside Blender with --python-exit-code 1."""
import math
from pathlib import Path
import tempfile
import unittest

import bpy
import bmesh


def snapshot(obj):
    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        layer = bm.verts.layers.deform.active
        return [dict(v[layer]) if layer else {} for v in bm.verts]
    return [{g.group: g.weight for g in v.groups} for v in obj.data.vertices]


def fixture():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    arm = bpy.data.armatures.new('A1 armature')
    rig = bpy.data.objects.new('A1 rig', arm)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name in ('A', 'B', 'Locked', 'Control'):
        bone = arm.edit_bones.new(name)
        bone.tail.z = 1
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.bones['Control'].use_deform = False
    rig.select_set(False)
    mesh = bpy.data.meshes.new('A1 mesh')
    mesh.from_pydata([(0,0,0), (1,0,0), (0,1,0), (1,1,0), (2,1,0), (2,2,0)], [], [(0,1,2),(3,4,5)])
    obj = bpy.data.objects.new('A1 weights', mesh)
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('Skin', 'ARMATURE')
    mod.object = rig
    for name in ('A', 'B', 'Locked', 'Control', 'Mask'):
        obj.vertex_groups.new(name=name)
    for vertex in range(6):
        for group, value in enumerate((.2, .6, .2, .7, .8)):
            obj.vertex_groups[group].add([vertex], value, 'REPLACE')
    obj.vertex_groups['Locked'].lock_weight = True
    obj.vertex_groups.active_index = 0
    return obj, rig


class SkinWeightTests(unittest.TestCase):
    def setUp(self):
        self.obj, self.rig = fixture()
        self.area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
        self.override = bpy.context.temp_override(area=self.area,
            region=next(r for r in self.area.regions if r.type == 'WINDOW'))
        self.override.__enter__()

    def tearDown(self):
        self.override.__exit__(None, None, None)

    def operation(self, kind='normalize', **kwargs):
        name = 'skin_' + kind + '_weights'
        self.assertTrue(hasattr(bpy.types, 'AXISMELD_OT_' + name), 'Skin weight adapter is missing')
        return getattr(bpy.ops.axismeld, name)(**kwargs)

    def assert_close(self, actual, expected):
        self.assertTrue(math.isclose(actual, expected, abs_tol=1e-6), (actual, expected))

    def test_normalize_actual_result_locks_nonbone_and_other_object(self):
        other = self.obj.copy(); other.data = self.obj.data.copy()
        bpy.context.collection.objects.link(other); other.select_set(True)
        other_before = snapshot(other)
        self.obj.vertex_groups[0].add([0], .1, 'REPLACE')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'FINISHED'})
        after = snapshot(self.obj)
        self.assert_close(after[0][0], .8/7)
        self.assert_close(after[0][1], .8*6/7)
        for v in range(6):
            for g in (2,3,4): self.assertEqual(after[v][g], before[v][g])
        self.assertEqual(snapshot(other), other_before)
        self.assertEqual(bpy.context.mode, 'OBJECT')
        self.assertEqual(set(bpy.context.selected_objects), {self.obj, other})

    def test_prune_strict_equal_boundary_lock_and_renormalize(self):
        # Use exactly representable float32 values to test strict comparison.
        self.obj.vertex_groups[0].add([0], .125, 'REPLACE')
        self.obj.vertex_groups[1].add([0], .0625, 'REPLACE')
        self.obj.vertex_groups[2].add([0], .0625, 'REPLACE')
        self.assertEqual(self.operation('prune', threshold=.125), {'FINISHED'})
        row = snapshot(self.obj)[0]
        self.assertNotIn(1, row)
        self.assert_close(row[0], .9375)
        self.assertEqual(row[2], .0625)
        self.assert_close(row[3], .7); self.assert_close(row[4], .8)

    def test_prune_keeps_strongest_bone_even_with_mask_group(self):
        self.obj.vertex_groups[2].lock_weight = False
        self.assertEqual(self.operation('prune', threshold=.9), {'FINISHED'})
        row = snapshot(self.obj)[0]
        self.assertEqual({g:w for g,w in row.items() if g<3}, {1:1.0})
        self.assert_close(row[4], .8)

    def test_prune_can_explicitly_clear_and_skip_normalize(self):
        self.obj.vertex_groups[2].lock_weight = False
        self.assertEqual(self.operation('prune', threshold=.9, keep_strongest=False,
                                        normalize_after=False), {'FINISHED'})
        self.assertEqual(set(snapshot(self.obj)[0]), {3,4})

    def test_zero_does_not_create_weight_or_normalize_single_zero(self):
        for group in self.obj.vertex_groups:
            if group.index < 3: group.remove([0])
        self.obj.vertex_groups[0].add([0], 0, 'REPLACE')
        self.obj.vertex_groups[0].add([1], .05, 'REPLACE')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'FINISHED'})
        self.assertEqual(snapshot(self.obj)[0], before[0])

    def test_impossible_locked_sum_is_atomic(self):
        self.obj.vertex_groups[0].add([0], .05, 'REPLACE')
        self.obj.vertex_groups[1].lock_weight = True
        self.obj.vertex_groups[1].add([5], .9, 'REPLACE')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'CANCELLED'})
        self.assertEqual(snapshot(self.obj), before)

    def test_extra_active_lock_is_not_a_permanent_group_lock(self):
        self.obj.vertex_groups[1].add([0], .1, 'REPLACE')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(lock_active=True), {'FINISHED'})
        after = snapshot(self.obj)
        self.assertEqual(after[0][0], before[0][0]); self.assert_close(after[0][1], .6)
        self.assertFalse(self.obj.vertex_groups[0].lock_weight)

    def test_hidden_object_vertices_are_untouched(self):
        self.obj.data.vertices[0].hide = True
        for v in (0,1): self.obj.vertex_groups[0].add([v], .05, 'REPLACE')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'FINISHED'})
        self.assertEqual(snapshot(self.obj)[0], before[0])
        self.assertNotEqual(snapshot(self.obj)[1], before[1])

    def test_weight_paint_vertex_mask_and_mirror_do_not_expand_selection(self):
        for v in self.obj.data.vertices: v.select = v.index == 0
        self.obj.data.use_paint_mask_vertex = True
        self.obj.data.use_mirror_x = True
        self.obj.vertex_groups[0].add([0,1], .05, 'REPLACE')
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'FINISHED'})
        self.assertNotEqual(snapshot(self.obj)[0], before[0])
        self.assertEqual(snapshot(self.obj)[1:], before[1:])
        self.assertEqual(bpy.context.mode, 'PAINT_WEIGHT')
        self.assertEqual([v.index for v in self.obj.data.vertices if v.select], [0])

    def test_weight_paint_face_mask_uses_only_selected_face_vertices(self):
        for p in self.obj.data.polygons: p.select = p.index == 0
        self.obj.data.use_paint_mask = True
        for v in range(6): self.obj.vertex_groups[0].add([v], .05, 'REPLACE')
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'FINISHED'})
        after = snapshot(self.obj)
        self.assertTrue(all(after[v] != before[v] for v in (0,1,2)))
        self.assertEqual(after[3:], before[3:])

    def test_edit_bmesh_only_selected_unhidden_and_no_mode_change(self):
        for v in range(6): self.obj.vertex_groups[0].add([v], .05, 'REPLACE')
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(self.obj.data); bm.verts.ensure_lookup_table()
        for v in bm.verts: v.select_set(False)
        bm.verts[0].select_set(True)
        bmesh.update_edit_mesh(self.obj.data)
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'FINISHED'})
        after = snapshot(self.obj)
        self.assertNotEqual(after[0], before[0]); self.assertEqual(after[1:], before[1:])
        self.assertEqual(bpy.context.mode, 'EDIT_MESH')
        self.assertEqual([v.index for v in bm.verts if v.select], [0])

    def test_invalid_contexts_refuse_without_writing(self):
        from axismeld.skin_weight_ops import context_error
        before = snapshot(self.obj)
        extra = self.obj.modifiers.new('Ambiguous', 'ARMATURE'); extra.object=self.rig
        self.assertTrue(context_error(bpy.context)); self.obj.modifiers.remove(extra)
        shared = self.obj.copy(); bpy.context.collection.objects.link(shared)
        self.assertTrue(context_error(bpy.context)); bpy.data.objects.remove(shared, do_unlink=True)
        self.obj.modifiers[0].show_viewport=False
        self.assertTrue(context_error(bpy.context)); self.obj.modifiers[0].show_viewport=True
        self.obj.modifiers[0].use_vertex_groups=False
        self.assertTrue(context_error(bpy.context)); self.obj.modifiers[0].use_vertex_groups=True
        self.assertFalse(context_error(bpy.context))
        self.assertEqual(snapshot(self.obj), before)

    def test_catalog_only_two_body_and_options_are_adapted(self):
        from axismeld.workspace_menu_catalog import build_workspace_menubar
        def walk(nodes):
            for n in nodes:
                yield n
                yield from walk(n.get('children', ()))
        nodes=list(walk(build_workspace_menubar()['menus']))
        adapted=[n for n in nodes if n['kind']=='skin_weight']
        self.assertEqual({n['maya_command'] for n in adapted}, {'NormalizeWeights','PruneSmallWeights'})
        self.assertTrue(all(n['options']['kind']=='skin_weight_options' for n in adapted))
        for n in nodes:
            if n.get('maya_command') in {'EnableWeightNormalization','DisableWeightNormalization','EnableWeightPostNormalization'}:
                self.assertEqual(n['kind'],'disabled')

    def test_already_normalized_rna_weights_cancel_without_empty_change(self):
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'CANCELLED'})
        self.assertEqual(snapshot(self.obj), before)

    def test_fake_user_is_not_a_second_mesh_object(self):
        self.obj.data.use_fake_user = True
        self.assertTrue(bpy.ops.axismeld.skin_normalize_weights.poll())
        self.obj.vertex_groups[0].add([0], .05, 'REPLACE')
        self.assertEqual(self.operation(), {'FINISHED'})

    def test_multi_object_edit_is_rejected_without_selection_change(self):
        other = self.obj.copy(); other.data = self.obj.data.copy()
        bpy.context.collection.objects.link(other); other.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        self.assertEqual(len(bpy.context.objects_in_mode), 2)
        before, other_before = snapshot(self.obj), snapshot(other)
        self.assertFalse(bpy.ops.axismeld.skin_normalize_weights.poll())
        self.assertFalse(bpy.ops.axismeld.skin_prune_weights.poll())
        self.assertEqual(snapshot(self.obj), before); self.assertEqual(snapshot(other), other_before)
        self.assertEqual(bpy.context.mode, 'EDIT_MESH')

    def test_linked_armature_is_readonly_reference_but_linked_mesh_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='axismeld-skin-fixture-') as folder:
            path = str(Path(folder) / 'synthetic.blend')
            bpy.data.libraries.write(path, {self.rig.data, self.obj.data})
            with bpy.data.libraries.load(path, link=True) as (source, target):
                target.armatures = source.armatures
                target.meshes = source.meshes
            self.rig.data = target.armatures[0]
            self.obj.vertex_groups[0].add([0], .05, 'REPLACE')
            self.assertTrue(bpy.ops.axismeld.skin_normalize_weights.poll())
            self.assertEqual(self.operation(), {'FINISHED'})
            linked = bpy.data.objects.new('Linked Mesh', target.meshes[0])
            bpy.context.collection.objects.link(linked)
            self.obj.select_set(False); linked.select_set(True)
            bpy.context.view_layer.objects.active=linked
            self.assertFalse(bpy.ops.axismeld.skin_normalize_weights.poll())
            self.assertFalse(bpy.ops.axismeld.skin_prune_weights.poll())

    def test_empty_edit_selection_cancel_has_no_writes(self):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        before = snapshot(self.obj)
        self.assertEqual(self.operation(), {'CANCELLED'})
        self.assertEqual(snapshot(self.obj), before)

    def test_serialized_result_loads_same_weights(self):
        # Read actual saved datablocks back through Blender's library loader.
        self.obj.vertex_groups[0].add([0], .05, 'REPLACE')
        self.assertEqual(self.operation(), {'FINISHED'})
        before = snapshot(self.obj)
        with tempfile.TemporaryDirectory(prefix='axismeld-skin-save-') as folder:
            path = str(Path(folder) / 'weights.blend')
            bpy.data.libraries.write(path, {self.obj})
            with bpy.data.libraries.load(path) as (source, target):
                target.objects = [self.obj.name]
            self.assertEqual(snapshot(target.objects[0]), before)


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SkinWeightTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise RuntimeError('Skin weight result tests failed')
    print('AXISMELD_SKIN_WEIGHT_RESULTS_PASS', result.testsRun)

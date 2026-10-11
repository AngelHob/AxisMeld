# SPDX-License-Identifier: GPL-2.0-or-later
"""Run with Blender --background --factory-startup --python-exit-code 1."""
from pathlib import Path
import sys
import unittest
import types
import importlib
from unittest.mock import patch
import bpy
import bmesh
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/modules'))
package = types.ModuleType('_axismeld_preselection_test')
package.__path__ = [str(Path(__file__).resolve().parents[2] / 'scripts/modules/axismeld')]
sys.modules[package.__name__] = package
edit_preselection = importlib.import_module(package.__name__ + '.edit_preselection')
adapter = importlib.import_module(package.__name__ + '.adapter')


class PreselectionTest(unittest.TestCase):
    def setUp(self):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.context.object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.mesh.select_all(action='DESELECT')
        self.bm = bmesh.from_edit_mesh(self.obj.data)
        self.bm.faces.ensure_lookup_table()
        self.args = (str(self.obj.session_uid), str(self.obj.data.session_uid), 2, 0, (8, 12, 6))
        self.area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        self.region = next(region for region in self.area.regions if region.type == 'WINDOW')

    def test_read_only_capture_counts(self):
        with bpy.context.temp_override(area=self.area, region=self.region):
            target = edit_preselection.resolve_target(bpy.context, *self.args)
        self.assertEqual(edit_preselection.preview(target), {'root': 'context.modeling_face', 'counts': (4, 4, 1)})
        self.assertFalse(any(v.select for v in self.bm.verts))

    def test_preview_snapshot_enables_target_action_without_selecting_mesh(self):
        runtime = importlib.import_module(package.__name__ + '.hotbox_runtime')
        catalog = importlib.import_module(package.__name__ + '.hotbox_catalog')
        pending = list(catalog.default_catalog())
        requested = {'context.modeling_face.poke', 'context.modeling_edge_menu.crease',
                     'context.convert_menu.face_path'}
        nodes = {}
        while pending:
            node = pending.pop()
            pending.extend(node['children'])
            if node['id'] in requested:
                nodes[node['id']] = node
        with bpy.context.temp_override(area=self.area, region=self.region):
            target = edit_preselection.resolve_target(bpy.context, *self.args)
            runtime._apply_runtime_capabilities(bpy.context, list(nodes.values()),
                                                preselection=edit_preselection.preview(target))
        self.assertTrue(nodes['context.modeling_face.poke']['enabled'])
        self.assertFalse(nodes['context.modeling_edge_menu.crease']['enabled'])
        self.assertFalse(nodes['context.convert_menu.face_path']['enabled'])
        self.assertFalse(any(item.select for domain in (self.bm.verts, self.bm.edges, self.bm.faces) for item in domain))

    def test_stale_or_nonempty_target_is_rejected(self):
        with bpy.context.temp_override(area=self.area, region=self.region):
            for args in ((*self.args[:4], (8, 12, 7)), ('0', *self.args[1:])):
                self.assertIsNone(edit_preselection.resolve_target(bpy.context, *args))
            self.bm.faces[0].select_set(True)
            self.assertIsNone(edit_preselection.resolve_target(bpy.context, *self.args))

    def test_face_path_requires_two_faces_in_one_mesh_and_single_face_mode(self):
        with bpy.context.temp_override(area=self.area, region=self.region):
            self.bm.faces[0].select_set(True)
            self.bm.select_flush_mode()
            self.assertFalse(adapter.modeling_adapter.available(bpy.context, 'selection.face_path')[0])
            self.bm.faces[1].select_set(True)
            self.bm.select_flush_mode()
            self.assertTrue(adapter.modeling_adapter.available(bpy.context, 'selection.face_path')[0])
            bpy.context.tool_settings.mesh_select_mode = (True, False, True)
            self.assertFalse(adapter.modeling_adapter.available(bpy.context, 'selection.face_path')[0])

    def test_failure_restores_selection_history_and_active_face(self):
        self.bm.faces.active = self.bm.faces[2]
        with bpy.context.temp_override(area=self.area, region=self.region):
            target = edit_preselection.resolve_target(bpy.context, *self.args)
            def fail(*args, **kwargs):
                self.assertEqual(sum(face.select for face in self.bm.faces), 1)
                return {'CANCELLED'}
            with patch.object(adapter, 'run', fail):
                self.assertEqual(edit_preselection.execute_target(bpy.context, target, 'mesh.poke_faces'), {'CANCELLED'})
        self.assertFalse(any(v.select for v in self.bm.verts))
        self.assertEqual(len(self.bm.select_history), 0)
        self.assertEqual(self.bm.faces.active, self.bm.faces[2])

    def test_success_uses_one_face_and_preserves_active_object(self):
        active = bpy.context.object
        with bpy.context.temp_override(area=self.area, region=self.region):
            target = edit_preselection.resolve_target(bpy.context, *self.args)
            # Background screens have no initialized HUD region type. Exercise the real
            # geometry operator without its GUI undo/HUD registration; GUI tests own undo.
            with patch.object(adapter, 'run', lambda *args, **kwargs: bpy.ops.mesh.poke('EXEC_DEFAULT', False)):
                result = edit_preselection.execute_target(bpy.context, target, 'mesh.poke_faces')
        self.assertEqual(result, {'FINISHED'})
        self.assertEqual((len(self.bm.verts), len(self.bm.faces)), (9, 9))
        self.assertEqual(bpy.context.object, active)

    def test_conversion_routes_expand_by_domain_with_native_results(self):
        cases = [('FACE', 'VERT', False, 4), ('FACE', 'EDGE', False, 4),
                 ('EDGE', 'VERT', False, 2), ('EDGE', 'FACE', True, 2),
                 ('VERT', 'EDGE', True, 3), ('VERT', 'FACE', True, 2)]
        for source, destination, expansion, count in cases:
            with self.subTest(source=source, destination=destination):
                with bpy.context.temp_override(area=self.area, region=self.region):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='SELECT')
                    bpy.ops.object.delete()
                    mesh = bpy.data.meshes.new('ConversionFixture')
                    mesh.from_pydata([(-2,-2,0),(0,-2,0),(0,2,0),(-2,2,0),(2,-2,0),(2,2,0)], [],
                                     [(0,1,2,3),(1,4,5,2)])
                    obj = bpy.data.objects.new('ConversionFixture', mesh)
                    bpy.context.collection.objects.link(obj)
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type=source)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bm = bmesh.from_edit_mesh(mesh)
                    bm.verts.ensure_lookup_table()
                    bm.faces.ensure_lookup_table()
                    element = (bm.faces[0] if source == 'FACE' else bm.verts[1] if source == 'VERT' else
                               next(e for e in bm.edges if all(v.co.x == 0 for v in e.verts)))
                    element.select_set(True)
                    bm.select_flush_mode()
                    observed = []
                    class NativeWithoutBackgroundHud:
                        def poll(self):
                            return bpy.ops.mesh.select_mode.poll()
                        def __call__(self, invocation, undo, **kwargs):
                            observed.append((invocation, undo, kwargs))
                            return bpy.ops.mesh.select_mode(invocation, False, **kwargs)
                    with patch.object(adapter.modeling_adapter, 'operation', lambda call: NativeWithoutBackgroundHud()):
                        result = adapter.modeling_adapter.run(bpy.context, 'selection.convert_' + destination.lower())
                    self.assertEqual(result, {'FINISHED'})
                    self.assertEqual(observed, [('EXEC_DEFAULT', True, {'type': destination, 'use_expand': expansion})])
                    self.assertEqual(tuple(bpy.context.tool_settings.mesh_select_mode),
                                     tuple(destination == mode for mode in ('VERT', 'EDGE', 'FACE')))
                    elements = {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[destination]
                    self.assertEqual(sum(item.select for item in elements), count)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(PreselectionTest)
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
    raise RuntimeError('Preselection transaction tests failed')
print('AXISMELD_PRESELECTION_RNA_PASS')

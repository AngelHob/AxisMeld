# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure Python checks: per-construction selection aggregation, never stale dispatch."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
import axismeld
from axismeld import hotbox_runtime


class ModelingCacheTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('axismeld._cache_test_adapter',
            ROOT / 'scripts/modules/axismeld/modeling_adapter.py')
        self.adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'bpy': NS()}):
            spec.loader.exec_module(self.adapter)

    def test_counts_once_per_snapshot_and_live_without_cache(self):
        visits = []
        class Domain(list):
            def __iter__(self):
                visits.append(True)
                return super().__iter__()
        vertices = Domain([NS(select=True, hide=False), NS(select=True, hide=False)])
        bm = NS(verts=vertices, edges=Domain([NS(select=True, hide=False)]), faces=Domain([]))
        obj = NS(type='MESH', data=NS(is_editable=True), is_editable=True,
                 visible_get=lambda **kwargs: True)
        context = NS(mode='EDIT_MESH', active_object=obj, selected_objects=[obj],
                     objects_in_mode_unique_data=[obj], view_layer=object())
        with patch.dict(sys.modules, {'bmesh': NS(from_edit_mesh=lambda data: bm)}):
            cache = {}
            for _ in range(100):
                for requirement in ('vertices', 'edges', 'faces', 'two_vertices', 'two_edges', 'selection'):
                    self.adapter._requirement(context, requirement, cache)
            self.assertEqual(len(visits), 3, 'each mesh domain is traversed once for 600 checks')
            vertices[1].select = False
            self.assertFalse(self.adapter._requirement(context, 'two_vertices'))
            self.assertEqual(len(visits), 6, 'dispatch performs a fresh native selection traversal')
            self.assertFalse(self.adapter._requirement(context, 'two_vertices', {}))
            self.assertEqual(len(visits), 9, 'new construction starts with fresh counts')

    def test_runtime_cache_lifetime_and_unknown_command_routing(self):
        caches, ordinary = [], []
        def available(context, command, *, cache):
            caches.append(cache)
            return True, ''
        fake = NS(modeling_adapter=NS(available=available, command_state=lambda c, k: None),
                  available=lambda c, command: (ordinary.append(command) or False, 'Unknown'))
        def nodes():
            return [{'kind': 'command', 'enabled': True, 'command': command, 'children': []}
                    for command in ('curve.subdivide', 'curve.subdivide', 'unknown.not_registered')]
        with patch.dict(sys.modules, {'axismeld.adapter': fake}), patch.object(axismeld, 'adapter', fake, create=True):
            hotbox_runtime._apply_runtime_capabilities(NS(), nodes())
            hotbox_runtime._apply_runtime_capabilities(NS(), nodes())
        self.assertIs(caches[0], caches[1])
        self.assertIs(caches[2], caches[3])
        self.assertIsNot(caches[0], caches[2])
        self.assertEqual(ordinary, ['unknown.not_registered', 'unknown.not_registered'])

    def test_shared_curve_predicate_is_read_once_but_dispatch_is_live(self):
        visits, selection = [], [True]
        def predicate(context):
            visits.append(True)
            return selection[0]
        module = NS(COMMAND_POLLS={command: predicate for command in ('curve.subdivide', 'curve.duplicate')})
        context = NS(area=NS(type='VIEW_3D'), region=NS(type='WINDOW'), mode='EDIT_CURVE',
                     scene=NS(is_editable=True))
        with patch.object(self.adapter, '_modules', lambda: (module,)), patch.object(
                self.adapter, 'operation', lambda call: NS(poll=lambda: True)):
            cache = {}
            for _ in range(50):
                for command in module.COMMAND_POLLS:
                    self.assertTrue(self.adapter.available(context, command, cache=cache)[0])
            self.assertEqual(len(visits), 1)
            selection[0] = False
            self.assertFalse(self.adapter.available(context, 'curve.subdivide')[0])
            self.assertEqual(len(visits), 2)


if __name__ == '__main__':
    unittest.main()

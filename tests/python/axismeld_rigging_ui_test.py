"""Header routing must keep native menus reachable without changing keymaps."""
from pathlib import Path
import types
import unittest
from unittest.mock import patch

from axismeld_menubar_ui_test import Layout, load_ui


class Workspace(dict):
    def __init__(self, name, role=None):
        super().__init__()
        self.name = name
        if role:
            self['axismeld_workspace_role'] = role


class RiggingHeaderTests(unittest.TestCase):
    def setUp(self):
        self.ui = load_ui()
        self.context = types.SimpleNamespace(
            workspace=Workspace('Rigging'), area=types.SimpleNamespace(type='VIEW_3D'),
            window_manager=types.SimpleNamespace(keyconfigs=types.SimpleNamespace(
                active=types.SimpleNamespace(name='Blender'))))

    def api(self, name):
        result = getattr(self.ui, name, None)
        self.assertIsNotNone(result, 'Rigging workspace header is not implemented: ' + name)
        return result

    def test_rigging_is_available_with_both_native_and_maya_keymaps(self):
        predicate = self.api('rigging_workspace')
        for keymap in ('Blender', 'AxisMeld_Maya_2026'):
            self.context.window_manager.keyconfigs.active.name = keymap
            self.assertTrue(predicate(self.context))

    def test_role_survives_rename_and_copy_but_other_editors_do_not_gain_menus(self):
        predicate = self.api('rigging_workspace')
        for workspace in (Workspace('Rigging.001'), Workspace('My Character', 'RIGGING')):
            self.context.workspace = workspace
            self.assertTrue(predicate(self.context))
        self.context.area.type = 'IMAGE_EDITOR'
        self.assertFalse(predicate(self.context))
        self.context.area.type = 'VIEW_3D'
        self.context.workspace = Workspace('Animation')
        self.assertFalse(predicate(self.context))

    def test_header_only_rehomes_armature_pose_weights(self):
        self.api('rigging_workspace')
        layout = Layout()
        proxy = self.ui.viewport_menu_layout(layout, self.context)
        menu_ids = ('VIEW3D_MT_view', 'VIEW3D_MT_select_pose', 'VIEW3D_MT_add',
                    'VIEW3D_MT_object', 'VIEW3D_MT_edit_armature', 'VIEW3D_MT_pose',
                    'VIEW3D_MT_paint_weight', 'VIEW3D_MT_edit_mesh', 'VIEW3D_MT_uv_map')
        for name in menu_ids:
            proxy.menu(name)
        self.assertEqual([r[1] for r in layout.log], [n for n in menu_ids if n not in
                         {'VIEW3D_MT_edit_armature', 'VIEW3D_MT_pose', 'VIEW3D_MT_paint_weight'}])
        self.context.workspace = Workspace('Layout')
        self.assertIs(self.ui.viewport_menu_layout(layout, self.context), layout)

    def test_exact_skeleton_skin_order_and_no_global_or_other_rigging_roots(self):
        draw = self.api('draw_rigging_menus')
        roots = ('menubar.rigging.skeleton', 'menubar.rigging.skin')
        names = dict(zip(roots, ('AXISMELD_MT_skeleton_test', 'AXISMELD_MT_skin_test')))
        nodes = dict(zip(roots, ({'label': 'Skeleton'}, {'label': 'Skin'})))
        with patch.object(self.ui, '_CATALOG', {'rigging_roots': roots}), \
             patch.object(self.ui, '_MENU_NAMES', names), patch.object(self.ui, '_NODES', nodes):
            layout = Layout()
            draw(layout, self.context)
            self.assertEqual([r[2]['text'] for r in layout.log], ['Skeleton', 'Skin'])
            self.context.workspace = Workspace('Layout')
            other = Layout()
            draw(other, self.context)
            self.assertFalse(other.log)

    def test_renamed_rigging_never_also_draws_modeling(self):
        self.api('rigging_workspace')
        self.context.window_manager.keyconfigs.active.name = 'AxisMeld_Maya_2026'
        self.context.workspace = Workspace('Modeling', 'RIGGING')
        self.assertFalse(self.ui.modeling_workspace(self.context))

    def test_native_dispatch_keeps_original_context_and_menu_host(self):
        self.api('rigging_workspace')
        calls = []
        renderer = types.SimpleNamespace(draw_entry=lambda *args: calls.append(args))
        node = dict(id='native.skin.weights', kind='rigging_native', label='Weights',
                    native_key='skin.weights')
        with patch.dict('sys.modules', {'bl_ui': types.SimpleNamespace(
                space_axismeld_native_rigging=renderer)}):
            layout = Layout()
            self.ui._draw_item(layout, self.context, node)
        self.assertEqual(calls, [(layout, self.context, 'skin.weights')])

    def test_registered_provider_and_real_viewport_draw_include_rigging(self):
        self.api('draw_rigging_menus')
        root = Path(__file__).resolve().parents[2]
        self.assertIn('"space_axismeld_native_rigging"',
                      (root / 'scripts/startup/bl_ui/__init__.py').read_text())
        self.assertIn('space_axismeld_menubar.draw_rigging_menus(self.layout, context)',
                      (root / 'scripts/startup/bl_ui/space_view3d.py').read_text())


if __name__ == '__main__':
    unittest.main()

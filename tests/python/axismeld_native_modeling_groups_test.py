# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Native modeling parameters, source providers and invalid-context regression."""
import ast
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
SOURCE = ROOT / 'scripts/startup/bl_ui/space_axismeld_native_modeling.py'


class Props(dict):
    def __getattr__(self, key):
        return self.setdefault(key, Props())

    def __setattr__(self, key, value):
        self[key] = value


class Layout:
    def __init__(self, log=None):
        self.log = [] if log is None else log
        self.operator_context = 'INVOKE_REGION_WIN'
        self.enabled = True

    def row(self, **_kwargs):
        row = Layout(self.log)
        row.operator_context, row.enabled = self.operator_context, self.enabled
        return row

    def column(self, **kwargs):
        self.log.append(('column', kwargs))
        return self.row()

    def operator(self, identifier, **kwargs):
        props = Props()
        self.log.append(('operator', identifier, kwargs, props, self.operator_context, self.enabled))
        return props

    def operator_enum(self, identifier, prop, **kwargs):
        self.log.append(('enum', identifier, prop, kwargs, self.operator_context, self.enabled))

    def operator_menu_enum(self, identifier, prop=None, **kwargs):
        self.log.append(('enum_menu', identifier, prop, kwargs, self.operator_context, self.enabled))

    def menu(self, identifier, **kwargs):
        self.log.append(('menu', identifier, kwargs, self.enabled))

    def menu_contents(self, identifier):
        self.log.append(('menu_contents', identifier, self.enabled))

    def separator(self, **kwargs):
        self.log.append(('separator', kwargs))

    def label(self, **kwargs):
        self.log.append(('label', kwargs, self.enabled))

    def template_node_operator_asset_menu_items(self, **kwargs):
        self.log.append(('asset', kwargs, self.enabled))


def load():
    bpy = ModuleType('bpy')
    bpy.app = SimpleNamespace(build_options=SimpleNamespace(bullet=True, freestyle=True))
    translations = ModuleType('bpy.app.translations')
    translations.pgettext_iface = lambda text: text
    translations.contexts = SimpleNamespace(id_mesh='Mesh', operator_default='Operator', default='Default')
    spec = importlib.util.spec_from_file_location('native_modeling_under_test', SOURCE)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'bpy': bpy, 'bpy.app.translations': translations}):
        spec.loader.exec_module(module)
    return module


def host_package(api, catalog):
    ui = ModuleType('bl_ui.space_axismeld_menubar')
    ui._CATALOG = catalog
    ui.modeling_workspace = lambda ctx: (getattr(getattr(ctx, 'workspace', None), 'name', '') == 'Modeling'
        and getattr(getattr(ctx, 'area', None), 'type', '') == 'VIEW_3D')
    package = ModuleType('bl_ui')
    package.space_axismeld_menubar = ui
    package.space_axismeld_native_modeling = api
    return package


def native_source_draw(class_name, api):
    path = ROOT / 'scripts/startup/bl_ui/space_view3d.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    draw = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'draw')
    namespace = {'bpy': api.bpy}
    exec(compile(ast.Module(body=[draw], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['draw']


class NativeModelingGroupsTests(unittest.TestCase):
    def api(self):
        self.assertTrue(SOURCE.exists(), 'Native reusable modeling groups are not implemented')
        return load()

    def test_original_vertex_actions_keep_variants_and_invocation_modes(self):
        api, layout = self.api(), Layout()
        api.draw_original(layout, SimpleNamespace(mode='EDIT_MESH'), 'VIEW3D_MT_edit_mesh_vertices')
        ops = [row for row in layout.log if row[0] == 'operator']
        self.assertEqual(len(ops), 16)
        rip = [row for row in ops if row[1] == 'mesh.rip_move']
        self.assertEqual([row[3] for row in rip], [{'MESH_OT_rip': {'use_fill': False}}, {'MESH_OT_rip': {'use_fill': True}}])
        self.assertEqual(next(row[3] for row in ops if row[1] == 'mesh.bevel'), {'affect': 'VERTICES'})
        smooth = next(row for row in ops if row[1] == 'mesh.vertices_smooth')
        self.assertEqual(smooth[3], {'factor': .5})
        self.assertEqual(smooth[4], 'EXEC_REGION_WIN')
        self.assertEqual([row[1] for row in layout.log if row[0] == 'menu'], ['VIEW3D_MT_vertex_group', 'VIEW3D_MT_hook'])
        self.assertIn(('asset', {'catalog_path': 'Vertex'}, True), layout.log)

    def test_original_edge_dynamic_build_and_loopcut_parameters_survive(self):
        api, layout = self.api(), Layout()
        api.bpy.app.build_options.freestyle = False
        api.draw_original(layout, SimpleNamespace(mode='EDIT_MESH'), 'VIEW3D_MT_edit_mesh_edges')
        ops = [row for row in layout.log if row[0] == 'operator']
        self.assertEqual(len(ops), 21)
        self.assertFalse(any(row[1] == 'mesh.mark_freestyle_edge' for row in ops))
        loop = next(row for row in ops if row[1] == 'mesh.loopcut_slide')
        self.assertEqual(loop[3], {'TRANSFORM_OT_edge_slide': {'release_confirm': False}})
        self.assertEqual([row[3] for row in ops if row[1] == 'mesh.edge_rotate'], [{'use_ccw': False}, {'use_ccw': True}])

    def test_uv_uses_original_unwrap_provider_and_both_projection_variants(self):
        api, layout = self.api(), Layout()
        api.draw_original(layout, SimpleNamespace(mode='EDIT_MESH'), 'VIEW3D_MT_uv_map')
        self.assertEqual(layout.log[0], ('menu_contents', 'IMAGE_MT_uvs_unwrap', True))
        ops = [row for row in layout.log if row[0] == 'operator']
        self.assertEqual([row[3] for row in ops if row[1] == 'uv.project_from_view'],
                         [{'scale_to_bounds': False}, {'scale_to_bounds': True}])
        self.assertEqual(ops[-1][1], 'uv.reset')
        self.assertIn(('asset', {'catalog_path': 'UV'}, True), layout.log)

    def test_group_filter_keeps_one_actual_button_and_rejects_unknown_item_ids(self):
        api, layout = self.api(), Layout()
        from axismeld.workspace_native_groups import GROUPS
        key = next(key for key, data in GROUPS.items() if data['source_menu'] == 'VIEW3D_MT_uv_map'
                   and any(item['operator'] == 'uv.project_from_view' for item in data['items']))
        target = next(item['id'] for item in GROUPS[key]['items'] if item['operator'] == 'uv.project_from_view')
        api.draw_group(layout, SimpleNamespace(mode='EDIT_MESH', area=SimpleNamespace(type='VIEW_3D')), key, include=(target,))
        self.assertEqual(layout.log[0][0], 'column', 'A native menu group must stack its buttons vertically')
        rows = [row for row in layout.log if row[0] == 'operator']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2]['icon'], 'UV')
        with self.assertRaises(ValueError):
            api.draw_group(layout, SimpleNamespace(), key, include=('arbitrary.operator',))

    def test_no_selection_or_wrong_mode_is_gray_without_fake_context_or_mutation(self):
        api = self.api()
        from axismeld.workspace_native_groups import GROUPS
        context = SimpleNamespace(mode='OBJECT', area=SimpleNamespace(type='VIEW_3D'),
                                  active_object=None, object=None, edit_object=None)
        for key in GROUPS:
            layout = Layout()
            with self.subTest(group=key):
                api.draw_group(layout, context, key)
                self.assertTrue(all(not row[-1] for row in layout.log if row[0] in
                    {'operator', 'enum', 'enum_menu', 'menu', 'menu_contents', 'asset', 'label'}))
        self.assertIsNone(context.active_object)
        self.assertEqual(context.mode, 'OBJECT')

    def test_inline_unwrap_icons_are_scoped_and_all_nine_native_actions_are_preserved(self):
        api = self.api()
        ui_path = ROOT / 'scripts/startup/bl_ui/space_axismeld_menubar.py'
        ui_tree = ast.parse(ui_path.read_text(encoding='utf-8'))
        scope = [node for node in ui_tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {'enabled', 'modeling_workspace'}]
        ui = ModuleType('bl_ui.space_axismeld_menubar')
        ui.PRESET_NAME = 'AxisMeld_Maya_2026'
        exec(compile(ast.Module(body=scope, type_ignores=[]), str(ui_path), 'exec'), ui.__dict__)
        package = ModuleType('bl_ui')
        package.space_axismeld_menubar = ui
        package.space_axismeld_native_modeling = api
        image_path = ROOT / 'scripts/startup/bl_ui/space_image.py'
        image_tree = ast.parse(image_path.read_text(encoding='utf-8'))
        cls = next(node for node in image_tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'IMAGE_MT_uvs_unwrap')
        draw = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'draw')
        namespace = {}
        exec(compile(ast.Module(body=[draw], type_ignores=[]), str(image_path), 'exec'), namespace)
        baseline = None
        for workspace, area, preset, decorated in (
                ('Modeling', 'VIEW_3D', 'AxisMeld_Maya_2026', True),
                ('Modeling', 'IMAGE_EDITOR', 'AxisMeld_Maya_2026', False),
                ('Layout', 'VIEW_3D', 'AxisMeld_Maya_2026', False),
                ('Modeling', 'VIEW_3D', 'Blender', False)):
            context = SimpleNamespace(workspace=SimpleNamespace(name=workspace),
                area=SimpleNamespace(type=area), window_manager=SimpleNamespace(
                    keyconfigs=SimpleNamespace(active=SimpleNamespace(name=preset))))
            layout = Layout()
            with self.subTest(workspace=workspace, area=area, preset=preset), patch.dict(sys.modules, {'bl_ui': package}):
                namespace['draw'](SimpleNamespace(layout=layout), context)
                ops = [row for row in layout.log if row[0] == 'operator']
                self.assertEqual([row[1] for row in ops], ['uv.unwrap'] * 3 + [
                    'uv.smart_project', 'uv.lightmap_pack', 'uv.follow_active_quads',
                    'uv.cube_project', 'uv.cylinder_project', 'uv.sphere_project'])
                self.assertEqual([row[3] for row in ops[:3]], [
                    {'method': 'ANGLE_BASED'}, {'method': 'CONFORMAL'}, {'method': 'MINIMUM_STRETCH'}])
                self.assertEqual([row[4] for row in ops], ['INVOKE_REGION_WIN'] * 3 +
                                 ['INVOKE_DEFAULT'] * 3 + ['EXEC_REGION_WIN'] * 3)
                self.assertEqual([row[2].get('icon') for row in ops], ['UV' if decorated else None] * 9)
                normalized = [(kind, *values) if kind != 'operator' else
                    (kind, values[0], {k: v for k, v in values[1].items() if k != 'icon'}, *values[2:])
                    for kind, *values in layout.log]
                if baseline is None:
                    baseline = normalized
                else:
                    self.assertEqual(normalized, baseline)

    def test_classified_curve_submenus_dispatch_the_original_host_once_and_keep_item_filter(self):
        api = self.api()
        from axismeld.workspace_native_groups import GROUPS
        cases = (
            ('VIEW3D_MT_edit_curve_ctrlpoints', 'EDIT_CURVE', 'modeling.curves'),
            ('VIEW3D_MT_edit_curve_ctrlpoints', 'EDIT_SURFACE', 'modeling.surfaces'),
            ('VIEW3D_MT_edit_curve_segments', 'EDIT_CURVE', 'modeling.curves'),
            ('VIEW3D_MT_edit_curves_control_points', 'EDIT_CURVES', 'modeling.curves'),
            ('VIEW3D_MT_edit_curves_segments', 'EDIT_CURVES', 'modeling.curves'),
        )
        for source_menu, mode, root_id in cases:
            groups = [(key, data) for key, data in GROUPS.items()
                      if data['source_menu'] == source_menu and data['root_id'] == root_id]
            # Retain just one fixed item per source group. A native fallback
            # would incorrectly reintroduce the filtered actions here.
            nodes = [dict(kind='native_group', group_key=key, include=(data['items'][0]['id'],))
                     for key, data in groups]
            catalog = {'menus': [dict(id=root_id, kind='menu', children=nodes)]}
            context = SimpleNamespace(mode=mode, workspace=SimpleNamespace(name='Modeling'),
                area=SimpleNamespace(type='VIEW_3D'), edit_object=SimpleNamespace(
                    type='SURFACE' if mode == 'EDIT_SURFACE' else 'CURVES' if mode == 'EDIT_CURVES' else 'CURVE'))
            draw = native_source_draw(source_menu, api)
            class HostLayout(Layout):
                def menu_contents(self, identifier):
                    super().menu_contents(identifier)
                    self_case.assertEqual(identifier, source_menu)
                    self_case.assertEqual(sum(row[0] == 'menu_contents' for row in self.log), 1,
                                          'Native submenu host must not recurse or draw twice')
                    draw(SimpleNamespace(layout=self), context)
            self_case = self
            layout = HostLayout()
            with self.subTest(menu=source_menu, mode=mode), patch.dict(sys.modules, {'bl_ui': host_package(api, catalog)}):
                for node in nodes:
                    api.draw_group(layout, context, node['group_key'], include=node['include'])
                self.assertEqual([row[1] for row in layout.log if row[0] == 'menu_contents'], [source_menu])
                self.assertEqual(len([row for row in layout.log if row[0] in {'operator', 'enum_menu'}]), len(nodes))

    def test_original_curve_submenu_fallback_outside_modeling_keeps_all_native_actions(self):
        api = self.api()
        source_menu = 'VIEW3D_MT_edit_curve_ctrlpoints'
        context = SimpleNamespace(mode='EDIT_CURVE', workspace=SimpleNamespace(name='Layout'),
            area=SimpleNamespace(type='VIEW_3D'), edit_object=SimpleNamespace(type='CURVE'))
        expected, actual = Layout(), Layout()
        api.draw_original(expected, context, source_menu)
        with patch.dict(sys.modules, {'bl_ui': host_package(api, {'menus': []})}):
            native_source_draw(source_menu, api)(SimpleNamespace(layout=actual), context)
        self.assertEqual(actual.log, expected.log)

    def test_modifier_provider_icons_only_decorate_modeling_and_keep_add_copy_clear(self):
        api = self.api()
        api.bpy.context = SimpleNamespace(active_object=SimpleNamespace(type='MESH'))
        draw = native_source_draw('VIEW3D_MT_object_modifiers', api)
        for workspace, area, decorated in (('Modeling','VIEW_3D',True), ('Layout','VIEW_3D',False),
                                           ('Modeling','PROPERTIES',False)):
            layout = Layout()
            context = SimpleNamespace(workspace=SimpleNamespace(name=workspace), area=SimpleNamespace(type=area))
            with self.subTest(workspace=workspace, area=area), patch.dict(sys.modules, {'bl_ui': host_package(api, {'menus': []})}):
                draw(SimpleNamespace(layout=layout), context)
                rows = [row for row in layout.log if row[0] in {'menu','operator'}]
                self.assertEqual([row[1] for row in rows], ['OBJECT_MT_modifier_add',
                    'object.modifiers_copy_to_selected','object.modifiers_clear'])
                self.assertEqual([row[2].get('icon') for row in rows], ['MODIFIER' if decorated else None] * 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)

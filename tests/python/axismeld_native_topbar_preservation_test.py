# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Execute source draw functions to verify native host dispatch and retained controls.

The layout recorder observes calls only; actual Menu append/remove callbacks are
verified separately in the isolated Blender UI regression.
"""
import ast
from contextlib import contextmanager
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[2] / 'scripts/startup/bl_ui/space_topbar.py'


class Layout:
    def __init__(self):
        self.events = []

    def row(self, **_kwargs):
        return self

    def operator(self, identifier, **kwargs):
        props = SimpleNamespace()
        self.events.append(('operator', identifier, kwargs, props))
        return props

    def menu(self, identifier, **kwargs):
        self.events.append(('menu', identifier, kwargs))

    def separator(self, **kwargs):
        self.events.append(('separator', kwargs))

    def prop(self, owner, name, **kwargs):
        self.events.append(('prop', owner, name, kwargs))

    def template_ID_tabs(self, owner, name, **kwargs):
        self.events.append(('workspace', owner, name, kwargs))

    def template_ID(self, owner, name, **kwargs):
        self.events.append(('id', owner, name, kwargs))

    def template_search(self, owner, name, search_owner, search_name, **kwargs):
        self.events.append(('search', owner, name, search_owner, search_name, kwargs))

    def template_reports_banner(self):
        self.events.append(('reports',))

    def template_running_jobs(self):
        self.events.append(('jobs',))


def source_draw(class_name, method='draw', **namespace):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    function = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method)
    module = ast.Module(body=[function], type_ignores=[])
    namespace.setdefault('i18n_contexts', SimpleNamespace(id_windowmanager='WindowManager'))
    exec(compile(module, str(SOURCE), 'exec'), namespace)
    return namespace[method]


def context():
    scene = SimpleNamespace(render=SimpleNamespace(use_multiview=False))
    return SimpleNamespace(
        area=SimpleNamespace(show_menus=True),
        window=SimpleNamespace(scene=scene),
        screen=SimpleNamespace(show_fullscreen=False, show_statusbar=False),
        scene=scene, blend_data=SimpleNamespace(is_saved=True),
        preferences=SimpleNamespace(view=SimpleNamespace(show_developer_ui=False)),
        tool_settings=SimpleNamespace(lock_object_mode=True),
    )


@contextmanager
def extensions(enabled=True):
    ui = ModuleType('bl_ui')
    helper = ModuleType('bl_ui.space_axismeld_menubar')
    helper.enabled = lambda _context: enabled
    helper.draw_supplement = lambda layout, _context, identifier: layout.events.append(('supplement', identifier))
    helper.draw_menu_sets_entry = lambda layout, _context: layout.events.append(('menu_sets',))
    ui.space_axismeld_menubar = helper
    utility = ModuleType('_bl_ui_utils.layout')

    @contextmanager
    def operator_context(_layout, _context):
        yield

    utility.operator_context = operator_context
    with patch.dict(sys.modules, {'bl_ui': ui, 'bl_ui.space_axismeld_menubar': helper,
                                 '_bl_ui_utils.layout': utility}):
        yield


class NativeTopbarPreservationTests(unittest.TestCase):
    def test_maya_configuration_keeps_native_menu_class_dispatch_and_workspace_tabs(self):
        native = source_draw('TOPBAR_MT_editor_menus')
        def dispatch(ctx, layout):
            native(SimpleNamespace(layout=layout), ctx)
        draw = source_draw('TOPBAR_HT_upper_bar', 'draw_left',
                           TOPBAR_MT_editor_menus=SimpleNamespace(draw_collapsible=dispatch))
        for maya_enabled in (False, True):
            with self.subTest(maya_enabled=maya_enabled), extensions(maya_enabled):
                layout, ctx = Layout(), context()
                draw(SimpleNamespace(layout=layout), ctx)
                self.assertEqual([event[1] for event in layout.events if event[0] == 'menu'], [
                    'TOPBAR_MT_blender', 'TOPBAR_MT_file', 'TOPBAR_MT_edit',
                    'TOPBAR_MT_render', 'TOPBAR_MT_window', 'TOPBAR_MT_help',
                ])
                self.assertEqual(layout.events[-2], ('separator', {'type': 'LINE'}))
                self.assertEqual(layout.events[-1], ('workspace', ctx.window, 'workspace',
                    {'new': 'workspace.add', 'menu': 'TOPBAR_MT_workspace_menu'}))

    def test_fullscreen_return_and_scene_view_layer_controls_remain_native(self):
        left = source_draw('TOPBAR_HT_upper_bar', 'draw_left',
                          TOPBAR_MT_editor_menus=SimpleNamespace(draw_collapsible=lambda *_args: None))
        right = source_draw('TOPBAR_HT_upper_bar', 'draw_right')
        layout, ctx = Layout(), context()
        ctx.screen.show_fullscreen = True
        with extensions():
            left(SimpleNamespace(layout=layout), ctx)
            right(SimpleNamespace(layout=layout), ctx)
        self.assertFalse(any(event[0] == 'workspace' for event in layout.events))
        self.assertIn('screen.back_to_previous', [event[1] for event in layout.events if event[0] == 'operator'])
        self.assertEqual([event[0] for event in layout.events[-4:]], ['reports', 'jobs', 'id', 'search'])
        self.assertEqual(layout.events[-2][1:3], (ctx.window, 'scene'))
        self.assertEqual(layout.events[-1][1:5], (ctx.window, 'view_layer', ctx.scene, 'view_layers'))

    def test_common_supplements_follow_original_native_content_and_dynamic_menu_dispatch(self):
        cases = (
            ('TOPBAR_MT_file', 'common.file', 'wm.quit_blender'),
            ('TOPBAR_MT_edit', 'common.edit', 'screen.userpref_show'),
            ('TOPBAR_MT_window', 'common.windows', 'screen.screenshot_area'),
            ('TOPBAR_MT_help', 'menubar.help', 'wm.sysinfo'),
        )
        for class_name, identifier, native_operation in cases:
            with self.subTest(menu=class_name), extensions():
                layout = Layout()
                source_draw(class_name)(SimpleNamespace(layout=layout), context())
                self.assertIn(native_operation, [event[1] for event in layout.events if event[0] == 'operator'])
                expected_tail = [('supplement', identifier)]
                if class_name == 'TOPBAR_MT_window':
                    expected_tail.append(('menu_sets',))
                self.assertEqual(layout.events[-len(expected_tail):], expected_tail)
                if class_name == 'TOPBAR_MT_file':
                    menus = [event[1] for event in layout.events if event[0] == 'menu']
                    for original_id in ('TOPBAR_MT_file_import', 'TOPBAR_MT_file_export',
                                        'TOPBAR_MT_file_open_recent', 'TOPBAR_MT_file_defaults'):
                        self.assertIn(original_id, menus)

    def test_no_second_global_menu_header_is_registered(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        self.assertNotIn('TOPBAR_HT_menubar', {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)})
        registration = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                            and any(isinstance(target, ast.Name) and target.id == 'classes'
                                    for target in node.targets))
        self.assertNotIn('TOPBAR_HT_menubar', {node.id for node in ast.walk(registration)
                                            if isinstance(node, ast.Name)})


if __name__ == '__main__':
    unittest.main(verbosity=2)

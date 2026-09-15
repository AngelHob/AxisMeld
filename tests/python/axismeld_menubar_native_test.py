import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[2] / 'scripts/modules/axismeld/menubar_native.py'

class Layout:
    def __init__(self, records=None, parent=None, direction=None, align=False):
        self.align = align
        self.direction = direction
        self.records = records if records is not None else []
        self.operator_context = parent.operator_context if parent else 'INVOKE_DEFAULT'
        self.enabled = parent.enabled if parent else True
    def separator(self):
        self.records.append(('separator',))
    def row(self, *, align=False):
        return Layout(self.records, self, 'row', align)
    def column(self):
        return Layout(self.records, self, 'column')
    def operator(self, name, **kwargs):
        props = types.SimpleNamespace()
        self.records.append(('operator', name, kwargs, props, self.operator_context, self.enabled))
        return props
    def menu(self, name, **kwargs):
        self.records.append(('menu', name, kwargs, None, self.operator_context, self.enabled))
    def prop(self, owner, name, **kwargs):
        self.records.append(('prop', name, kwargs, owner, self.operator_context, self.enabled))

def context(saved=False, developer=False, multiview=False):
    ns = types.SimpleNamespace
    return ns(blend_data=ns(is_saved=saved), preferences=ns(view=ns(show_developer_ui=developer)),
              tool_settings=ns(lock_object_mode=False), screen=ns(show_statusbar=True),
              scene=ns(render=ns(use_multiview=multiview)))

class NativeMenuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('native_under_test', MODULE)
        cls.native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.native)
    def draw(self, key, ctx=None):
        layout = Layout()
        self.native.draw_native(layout, ctx or context(), key, text='Caption', icon='FILE')
        self.assertEqual(layout.operator_context, 'INVOKE_DEFAULT')
        return layout.records
    def test_native_body_preserves_parent_options_alignment_group(self):
        class Parent(Layout):
            def row(self, *, align=False):
                self.child=super().row(align=align)
                return self.child
        for key in ('file.new_scene','file.open','file.save_as','file.import','file.export'):
            layout=Parent(align=True)
            self.native.draw_native(layout,context(),key,text='Body',icon='NONE')
            self.assertTrue(layout.child.align,key+' breaks item_align traversal to body')
            self.assertEqual(layout.child.direction,'row')

    def test_save_preferences_keeps_native_exec_area_context(self):
        record=self.draw('file.save_preferences')[0]
        self.assertEqual(record[1],'wm.save_userpref')
        self.assertEqual(record[4],'EXEC_AREA')
        self.assertEqual(vars(record[3]),{})

    def test_unknown_key_is_atomic_rejection(self):
        layout = Layout()
        with self.assertRaises(ValueError):
            self.native.draw_native(layout, context(), 'wm.quit_blender', text='', icon='NONE')
        self.assertEqual(layout.records, [])
        self.assertIsInstance(self.native.NATIVE_KEYS, frozenset)
    def test_save_modes_and_modified_images(self):
        for saved, mode in ((False, 'INVOKE_AREA'), (True, 'EXEC_AREA')):
            record = self.draw('file.save', context(saved))[0]
            self.assertEqual(record[1], 'wm.save_mainfile')
            self.assertEqual(record[4], mode)
            self.assertTrue(record[3].show_save_modified_images_dialog)
    def test_copy_increment_and_save_as_stay_distinct(self):
        record = self.draw('file.save_copy')[0]
        self.assertEqual(record[1], 'wm.save_as_mainfile')
        self.assertTrue(record[3].copy)
        self.assertTrue(record[3].show_save_modified_images_dialog)
        for saved in (False, True):
            record = self.draw('file.save_incremental', context(saved))[0]
            self.assertEqual(record[4:6], ('EXEC_AREA', saved))
            self.assertTrue(record[3].incremental)
            self.assertTrue(record[3].show_save_modified_images_dialog)
        record = self.draw('file.save_as')[0]
        self.assertEqual(record[4], 'INVOKE_AREA')
        self.assertTrue(record[3].show_save_modified_images_dialog)
        self.assertFalse(hasattr(record[3], 'copy'))
    def test_dynamic_original_menu_ids(self):
        for key, menu in [('file.import','TOPBAR_MT_file_import'), ('file.export','TOPBAR_MT_file_export'),
                          ('file.recent','TOPBAR_MT_file_open_recent'), ('edit.undo_history','TOPBAR_MT_undo_history'),
                          ('file.new','TOPBAR_MT_file_new'), ('file.external_data','TOPBAR_MT_file_external_data'),
                          ('windows.defaults','TOPBAR_MT_file_defaults')]:
            record = self.draw(key)[0]
            self.assertEqual(record[:2], ('menu', menu))
    def test_file_selectors_invoke_area(self):
        for key, op in [('open','wm.open_mainfile'),('link','wm.link'),('append','wm.append')]:
            record = self.draw('file.'+key)[0]
            self.assertEqual((record[1],record[4]),(op,'INVOKE_AREA'))
    def test_native_properties_keep_actual_context_owner(self):
        ctx=context()
        for key, owner, prop in [('windows.lock_object_mode',ctx.tool_settings,'lock_object_mode'),
                                 ('windows.statusbar',ctx.screen,'show_statusbar')]:
            record=self.draw(key,ctx)[0]
            self.assertEqual(record[:2],('prop',prop))
            self.assertIs(record[3],owner)
    def test_platform_developer_multiview_conditions(self):
        for key in ('edit.operator_search','help.developer_docs','help.developer_community','help.api','help.cheat_sheet'):
            self.assertEqual(self.draw(key),[])
            self.assertEqual(len(self.draw(key,context(developer=True))),1)
        with patch.object(self.native.sys,'platform','linux'):
            self.assertEqual(self.draw('windows.console'),[])
        with patch.object(self.native.sys,'platform','win32'):
            self.assertEqual(self.draw('windows.console')[0][1],'wm.console_toggle')
        self.assertEqual(self.draw('windows.stereo'),[])
        self.assertEqual(self.draw('windows.stereo',context(multiview=True))[0][1],'wm.set_stereo_3d')
    def test_editor_screenshot_and_rename_parameters(self):
        self.assertEqual(self.draw('windows.screenshot_editor')[0][4],'INVOKE_SCREEN')
        props=self.draw('modify.rename')[0][3]
        self.assertEqual(props.name,'TOPBAR_PT_name')
        self.assertFalse(props.keep_open)
        for key,direction in [('windows.workspace_next','NEXT'),('windows.workspace_previous','PREV')]:
            self.assertEqual(self.draw(key)[0][3].direction,direction)
    def test_help_presets_are_not_generic_links(self):
        for key,value in [('manual','MANUAL'),('release_notes','RELEASE_NOTES'),('report_bug','BUG'),('api','API')]:
            record=self.draw('help.'+key,context(developer=True))[0]
            self.assertEqual(record[1],'wm.url_open_preset')
            self.assertEqual(record[3].type,value)
    def test_render_leaves_keep_props_and_sequence_visibility(self):
        ctx=context()
        ctx.sequencer_scene=None
        self.assertEqual(self.draw('render.sequence_image',ctx),[])
        self.assertEqual(self.draw('render.sequence_animation',ctx),[])
        ctx.sequencer_scene=types.SimpleNamespace(render=types.SimpleNamespace(use_sequencer=True))
        ctx.strips=[object()]
        for key, animation, sequence in [('image',False,False),('animation',True,False),
                                          ('sequence_image',False,True),('sequence_animation',True,True)]:
            record=self.draw('render.'+key,ctx)[0]
            self.assertEqual(record[1],'render.render')
            self.assertTrue(record[3].use_viewport)
            self.assertEqual(getattr(record[3],'animation',False),animation)
            self.assertEqual(getattr(record[3],'use_sequencer_scene',False),sequence)
        ctx.sequencer_scene=ctx.scene
        ctx.scene.render.use_sequencer=True
        self.assertEqual(self.draw('render.sequence_image',ctx),[])
        record=self.draw('render.lock_interface',ctx)[0]
        self.assertIs(record[3],ctx.scene.render)
        self.assertEqual(record[1],'use_lock_interface')

    def test_every_fixed_key_draws_without_dispatching_operators(self):
        source=MODULE.parents[2] / 'startup/bl_ui/space_topbar.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        render_class=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='TOPBAR_MT_render')
        namespace={'Menu':object}
        exec(compile(ast.Module(body=[render_class],type_ignores=[]),str(source),'exec'),namespace)
        module=types.SimpleNamespace(TOPBAR_MT_render=namespace['TOPBAR_MT_render'])
        ctx=context(saved=True,developer=True,multiview=True)
        ctx.sequencer_scene=types.SimpleNamespace(render=types.SimpleNamespace(use_sequencer=True))
        ctx.strips=[object()]
        with patch.dict(sys.modules,{'bl_ui.space_topbar':module,'bl_ui':types.ModuleType('bl_ui')}), patch.object(self.native.sys,'platform','win32'):
            for key in sorted(self.native.NATIVE_KEYS):
                with self.subTest(key=key):
                    self.assertTrue(self.draw(key,ctx))
            records=self.draw('render.native',ctx)
        renders=[r for r in records if r[:2]==('operator','render.render')]
        self.assertEqual(len(renders),4)
        self.assertEqual([getattr(r[3],'animation',False) for r in renders],[False,True,False,True])
        self.assertEqual([getattr(r[3],'use_sequencer_scene',False) for r in renders],[False,False,True,True])
        self.assertTrue(all(r[3].use_viewport for r in renders))
        self.assertIn(('prop','use_lock_interface'),[r[:2] for r in records])

    def test_render_delegates_exact_context_to_native_draw(self):
        ctx=context()
        seen=[]
        def draw(instance, received):
            self.assertEqual(instance.layout.direction, 'column')
            seen.append(received)
            instance.layout.operator('native.render.sentinel')
        module=types.SimpleNamespace(TOPBAR_MT_render=types.SimpleNamespace(draw=draw))
        with patch.dict(sys.modules,{'bl_ui.space_topbar':module,'bl_ui':types.ModuleType('bl_ui')}):
            record=self.draw('render.native',ctx)[0]
        self.assertIs(seen[0],ctx)
        self.assertEqual(record[1],'native.render.sentinel')

if __name__ == '__main__':
    unittest.main()

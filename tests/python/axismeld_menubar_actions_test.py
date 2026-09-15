# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[2]/'scripts/modules/axismeld/menubar_actions.py'

class Override:
    def __enter__(self): return self
    def __exit__(self,*args): pass
class Op:
    def __init__(self,callback=None): self.calls=[]; self.callback=callback; self.allowed=True
    def poll(self): return self.allowed
    def __call__(self,*args,**kwargs):
        self.calls.append((args,kwargs))
        return self.callback() if self.callback else {'FINISHED'}

def fixture():
    area=NS(type='VIEW_3D',regions=[],spaces=NS(active=NS()))
    region=NS(type='WINDOW');area.regions=[region]
    screen=NS(areas=[area]);window=NS(screen=screen)
    ctx=NS(window=window,screen=screen,area=area,region=region,mode='OBJECT',scene=NS(is_editable=True),
           window_manager=NS(windows=[window]),temp_override=lambda **kw:Override())
    object_ops=NS(**{name:Op() for name in ['camera_add','light_add','armature_add','metaball_add',
                     'volume_add','grease_pencil_add','speaker_add','effector_add']})
    wm=NS(window_new=Op(),window_close=Op())
    bpy=NS(ops=NS(object=object_ops,wm=wm),context=ctx,app=NS(background=False))
    spec=importlib.util.spec_from_file_location('actions_test_target',PATH)
    module=importlib.util.module_from_spec(spec)
    sys.modules['bpy']=bpy
    spec.loader.exec_module(module)
    return module,bpy,ctx

class MenubarActionsTest(unittest.TestCase):
    def setUp(self):
        self.old_bpy=sys.modules.get('bpy')
    def tearDown(self):
        if self.old_bpy is None:
            sys.modules.pop('bpy',None)
        else:
            sys.modules['bpy']=self.old_bpy
    def test_metadata_import_does_not_require_bpy(self):
        spec=importlib.util.spec_from_file_location('actions_without_bpy',PATH)
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'bpy':None}):
            spec.loader.exec_module(module)
        self.assertTrue(all(item['category'] in {'Create','Windows'} and
                            isinstance(item['section'],tuple) for item in module.ACTIONS.values()))

    def test_closed_keys_and_semantic_rtcs(self):
        mod,bpy,ctx=fixture()
        self.assertEqual(len(mod.ACTIONS),21)
        self.assertEqual(mod.ACTIONS['create.camera']['maya_command'],'CreateCameraOnly')
        self.assertNotIn('maya_command',mod.ACTIONS['create.armature'])
        self.assertFalse(mod.available(ctx,'object.delete')[0])
        self.assertEqual(mod.run(ctx,'object.delete'),{'CANCELLED'})
    def test_creation_once_native_undo_and_no_mode_change(self):
        mod,bpy,ctx=fixture()
        self.assertEqual(mod.run(ctx,'create.light_sun'),{'FINISHED'})
        self.assertEqual(bpy.ops.object.light_add.calls,[(('EXEC_DEFAULT',True),{'type':'SUN'})])
        self.assertEqual(ctx.mode,'OBJECT')
    def test_no_implicit_edit_mode_or_context_switch(self):
        mod,bpy,ctx=fixture()
        for field,value in [('mode','EDIT_MESH'),('area',NS(type='TEXT_EDITOR')),('region',None)]:
            old=getattr(ctx,field);setattr(ctx,field,value)
            self.assertFalse(mod.available(ctx,'create.camera')[0])
            self.assertEqual(mod.run(ctx,'create.camera'),{'CANCELLED'})
            setattr(ctx,field,old)
        self.assertEqual(bpy.ops.object.camera_add.calls,[])
    def test_stale_source_window_and_native_poll_reject(self):
        mod,bpy,ctx=fixture();ctx.window_manager.windows=[]
        self.assertFalse(mod.available(ctx,'create.camera')[0])
        ctx.window_manager.windows=[ctx.window];bpy.ops.object.camera_add.allowed=False
        self.assertFalse(mod.available(ctx,'create.camera')[0])
    def test_editor_changes_only_unique_new_window(self):
        mod,bpy,ctx=fixture();source=ctx.window
        extra=NS(screen=NS(areas=[NS(type='TEXT_EDITOR')]))
        ctx.window_manager.windows.append(extra)
        target=NS(screen=NS(areas=[NS(type='VIEW_3D',spaces=NS(active=NS()))]))
        def create():ctx.window_manager.windows.append(target);return {'FINISHED'}
        bpy.ops.wm.window_new.callback=create
        self.assertEqual(mod.run(ctx,'editor.geometry_nodes'),{'FINISHED'})
        self.assertEqual(target.screen.areas[0].type,'NODE_EDITOR')
        self.assertEqual(target.screen.areas[0].spaces.active.tree_type,'GeometryNodeTree')
        self.assertEqual(source.screen.areas[0].type,'VIEW_3D')
        self.assertEqual(extra.screen.areas[0].type,'TEXT_EDITOR')
        self.assertEqual(bpy.ops.wm.window_new.calls,[(('EXEC_DEFAULT',False),{})])
    def test_editor_refuses_reused_window(self):
        mod,bpy,ctx=fixture()
        self.assertEqual(mod.run(ctx,'editor.outliner'),{'CANCELLED'})
        self.assertEqual(ctx.area.type,'VIEW_3D')
        self.assertEqual(bpy.ops.wm.window_close.calls,[])
    def test_editor_invalid_new_layout_closes_only_new_window(self):
        mod,bpy,ctx=fixture()
        target=NS(screen=NS(areas=[]))
        def create():ctx.window_manager.windows.append(target);return {'FINISHED'}
        bpy.ops.wm.window_new.callback=create
        self.assertEqual(mod.run(ctx,'editor.outliner'),{'CANCELLED'})
        self.assertEqual(len(bpy.ops.wm.window_close.calls),1)
        self.assertEqual(ctx.area.type,'VIEW_3D')
    def test_editor_rejects_screen_shared_with_any_existing_window(self):
        mod,bpy,ctx=fixture()
        other=NS(screen=NS(areas=[NS(type='TEXT_EDITOR',spaces=NS(active=NS()))]))
        ctx.window_manager.windows.append(other)
        target=NS(screen=other.screen)
        def create():ctx.window_manager.windows.append(target);return {'FINISHED'}
        bpy.ops.wm.window_new.callback=create
        self.assertEqual(mod.run(ctx,'editor.outliner'),{'CANCELLED'})
        self.assertEqual(other.screen.areas[0].type,'TEXT_EDITOR')
        self.assertEqual(len(bpy.ops.wm.window_close.calls),1)

    def test_background_editor_is_honestly_unavailable(self):
        mod,bpy,ctx=fixture();bpy.app.background=True
        self.assertFalse(mod.available(ctx,'editor.outliner')[0])
        self.assertEqual(mod.run(ctx,'editor.outliner'),{'CANCELLED'})
        self.assertEqual(bpy.ops.wm.window_new.calls,[])

if __name__=='__main__':unittest.main()

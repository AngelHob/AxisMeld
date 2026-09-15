# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/modules'))
import axismeld
PATH=Path(__file__).resolve().parents[2]/'scripts/modules/axismeld/menubar_runtime.py'

class Item(NS):
    def as_pointer(self):return id(self)

def region(x=0,y=0,width=400,height=300,kind='WINDOW'):
    return Item(type=kind,x=x,y=y,width=width,height=height)
def area(width=800,height=600,x=0,y=0,kind='VIEW_3D',regions=None):
    return Item(type=kind,width=width,height=height,x=x,y=y,regions=regions or [region(width=width,height=height)])

class Override:
    def __init__(self,ctx,kwargs):self.ctx=ctx;self.kwargs=kwargs;self.old={}
    def __enter__(self):
        for key,value in self.kwargs.items():
            self.old[key]=getattr(self.ctx,key,None);setattr(self.ctx,key,value)
        return self
    def __exit__(self,*args):
        for key,value in self.old.items():setattr(self.ctx,key,value)

class RuntimeTest(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('axismeld.menubar_runtime',PATH)
        self.runtime=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=self.runtime
        spec.loader.exec_module(self.runtime)
        self.viewport=area();self.topbar=area(kind='TOPBAR',height=30)
        self.scene=Item();self.screen=Item(areas=[self.topbar,self.viewport]);self.layer=Item()
        self.window=Item(screen=self.screen,scene=self.scene,view_layer=self.layer)
        self.ctx=Item(window=self.window,screen=self.screen,scene=self.scene,view_layer=self.layer,
                      area=self.topbar,region=region(kind='HEADER'),mode='OBJECT',
                      window_manager=Item(windows=[self.window]))
        self.ctx.temp_override=lambda **kwargs:Override(self.ctx,kwargs)
        self.runs=[];self.polls=[];self.allowed=True
        def available(ctx,key):
            self.polls.append((key,ctx.window,ctx.area,ctx.region,ctx.scene))
            return (self.allowed,'' if self.allowed else 'Selection changed')
        def run(ctx,key):
            self.runs.append((key,ctx.window,ctx.area,ctx.region,ctx.scene))
            return {'RUNNING_MODAL'}
        adapter=NS(SPECS={'mesh.test':object()},available=available,run=run)
        actions=NS(ACTIONS={'create.camera':{},'editor.outliner':{}},available=available,run=run)
        self.patches=[patch.dict(sys.modules,{'bpy':NS(context=self.ctx)}),
                      patch.object(axismeld,'modeling_adapter',adapter,create=True),
                      patch.object(axismeld,'menubar_actions',actions,create=True)]
        for item in self.patches:item.start();self.addCleanup(item.stop)
    def token(self):return self.runtime.source_token(self.ctx)
    def test_current_window_only_and_largest_fallback(self):
        huge=area(width=2000,height=2000)
        self.ctx.window_manager.windows.append(Item(screen=Item(areas=[huge]),scene=self.scene))
        self.assertIs(self.runtime.resolve_source(self.ctx).area,self.viewport)
        self.screen.areas=[self.topbar]
        self.assertIsNone(self.runtime.resolve_source(self.ctx))
        self.assertFalse(self.runtime.available(self.ctx,'command','mesh.test')[0])
    def test_current_viewport_and_exact_quad_region_take_priority(self):
        quad=[region(x=x,y=y) for x,y in [(400,300),(0,300),(400,0),(0,0)]]
        small=area(width=800,height=600,regions=quad)
        self.screen.areas.append(area(width=1800,height=1000))
        self.screen.areas.append(small);self.ctx.area=small;self.ctx.region=quad[0]
        self.assertIs(self.runtime.resolve_source(self.ctx).region,quad[0])
        self.ctx.region=region(kind='HEADER')
        self.assertIs(self.runtime.resolve_source(self.ctx).region,quad[3])
    def test_hidden_or_zero_size_regions_not_selected(self):
        self.viewport.regions=[region(width=0),region(height=1)]
        self.assertIsNone(self.runtime.resolve_source(self.ctx))
    def test_execution_reuses_capture_and_restores_popup_context(self):
        token=self.token();old_region=self.ctx.region
        self.screen.areas.append(area(width=2000,height=1000))
        self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'RUNNING_MODAL'})
        self.assertEqual(len(self.runs),1)
        self.assertIs(self.runs[0][2],self.viewport)
        self.assertIs(self.ctx.area,self.topbar)
        self.assertIs(self.ctx.region,old_region)
        self.assertEqual(self.ctx.mode,'OBJECT')
    def test_empty_malformed_unknown_tokens_and_kind_reject_atomically(self):
        for token in ['', 'not json','{}',json.dumps([1,True,2,3,4,5,6]),'x'*3000]:
            self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'CANCELLED'})
        for kind,key in [('native','file.save'),('command','wm.delete'),('action','object.delete')]:
            self.assertFalse(self.runtime.available(self.ctx,kind,key,self.token())[0])
            self.assertEqual(self.runtime.run(self.ctx,kind,key,self.token()),{'CANCELLED'})
        self.assertEqual(self.runs,[])
    def test_removed_area_or_region_never_retargets(self):
        token=self.token();self.screen.areas.remove(self.viewport)
        self.screen.areas.append(area())
        self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'CANCELLED'})
        self.screen.areas.append(self.viewport);self.viewport.regions=[]
        self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'CANCELLED'})
        self.assertEqual(self.runs,[])
    def test_scene_screen_layer_and_window_switch_reject(self):
        for key in ('scene','screen','view_layer'):
            original=getattr(self.window,key);token=self.token()
            setattr(self.window,key,Item())
            self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'CANCELLED'})
            setattr(self.window,key,original)
        token=self.token();self.ctx.window=Item(screen=self.screen,scene=self.scene,view_layer=self.layer)
        self.ctx.window_manager.windows.append(self.ctx.window)
        self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'CANCELLED'})
        self.assertEqual(self.runs,[])
    def test_adapter_poll_is_rechecked_at_submission(self):
        token=self.token()
        self.assertTrue(self.runtime.available(self.ctx,'command','mesh.test',token)[0])
        self.allowed=False
        self.assertEqual(self.runtime.run(self.ctx,'command','mesh.test',token),{'CANCELLED'})
        self.assertEqual(self.runs,[])
    def test_editor_without_3d_keeps_current_window_context(self):
        self.screen.areas=[self.topbar];token=self.token()
        self.assertTrue(token)
        self.assertEqual(self.runtime.run(self.ctx,'action','editor.outliner',token),{'RUNNING_MODAL'})
        self.assertIs(self.runs[0][2],self.topbar)
        self.assertFalse(self.runtime.available(self.ctx,'action','create.camera',token)[0])
    def test_state_reads_live_source_and_never_uses_stale_capture(self):
        axismeld.modeling_adapter.command_state=lambda ctx,key: ('checkbox',ctx.area is self.viewport)
        token=self.token()
        self.assertEqual(self.runtime.state(self.ctx,'command','mesh.test',token),('checkbox',True))
        self.assertIs(self.ctx.area,self.topbar)
        self.assertIsNone(self.runtime.state(self.ctx,'action','create.camera',token))
        self.screen.areas.remove(self.viewport)
        self.assertIsNone(self.runtime.state(self.ctx,'command','mesh.test',token))
        self.assertEqual(self.runs,[])

    def test_fifteen_core_commands_use_only_fixed_adapter_routes(self):
        expected=frozenset({
            'mesh.create_cone','mesh.create_cube','mesh.create_cylinder','mesh.create_disc',
            'mesh.create_plane','mesh.create_sphere','mesh.create_torus','selection.clear',
            'selection.grow','selection.select_all','selection.shrink','selection.toggle_component',
            'transform.move','transform.rotate','transform.scale'})
        calls=[]
        def available(ctx,key):return True,''
        def run(ctx,key):
            calls.append((key,ctx.area,ctx.region));return {'FINISHED'}
        core=NS(available=available,run=run)
        with patch.object(axismeld,'adapter',core,create=True):
            token=self.token()
            for key in sorted(expected):
                self.assertTrue(self.runtime.available(self.ctx,'command',key,token)[0],key)
                self.assertEqual(self.runtime.run(self.ctx,'command',key,token),{'FINISHED'})
            self.assertEqual(self.runtime.run(self.ctx,'command','hotbox.open',token),{'CANCELLED'})
            self.assertEqual(self.runtime.run(self.ctx,'command','mode.object',token),{'CANCELLED'})
        self.assertEqual(self.runtime.CORE_COMMANDS,expected)
        self.assertIsInstance(self.runtime.CORE_COMMANDS,frozenset)
        self.assertEqual({item[0] for item in calls},expected)
        self.assertTrue(all(item[1] is self.viewport for item in calls))
        self.assertEqual(self.runs,[])
        self.assertEqual(self.ctx.mode,'OBJECT')

    def test_capture_is_stable_and_read_only(self):
        before=(self.ctx.area,self.ctx.region,self.ctx.mode,list(self.screen.areas))
        self.assertEqual(self.token(),self.token())
        self.assertEqual(before,(self.ctx.area,self.ctx.region,self.ctx.mode,list(self.screen.areas)))

if __name__=='__main__':unittest.main()

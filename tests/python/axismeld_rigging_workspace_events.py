# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise default Rigging workspace through native GUI in a disposable factory process.

Run with ordinary Python: --blender PATH --artifacts DIR --verification JSON.
No add-on enable call or user preferences write is performed by this test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender',required=True)
    parser.add_argument('--artifacts',required=True)
    parser.add_argument('--verification',required=True)
    args=parser.parse_args()
    art=Path(args.artifacts).resolve();art.mkdir(parents=True,exist_ok=True)
    isolated=Path(tempfile.mkdtemp(prefix='isolated-',dir=art))
    env=os.environ.copy()
    for name in ('config','scripts','tmp'):(isolated/name).mkdir()
    env.update(BLENDER_USER_CONFIG=str(isolated/'config'),BLENDER_USER_SCRIPTS=str(isolated/'scripts'),
               TEMP=str(isolated/'tmp'),TMP=str(isolated/'tmp'),TMPDIR=str(isolated/'tmp'),
               AXISMELD_TEST_ARTIFACTS=str(art),AXISMELD_TEST_ROOT=str(isolated),
               AXISMELD_RIGGING_WORKSPACE_VERIFICATION=str(Path(args.verification).resolve()))
    startup=None
    if sys.platform=='win32':
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    command=[str(Path(args.blender).resolve()),'--factory-startup','--enable-event-simulate','--python-exit-code','1','--python',str(Path(__file__).resolve())]
    result=subprocess.run(command,env=env,startupinfo=startup,capture_output=True,timeout=240)
    (art/'stdout.log').write_bytes(result.stdout);(art/'stderr.log').write_bytes(result.stderr)
    sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    passed=(result.returncode==0 and b'AXISMELD_RIGGING_WORKSPACE_GUI_PASS' in result.stdout and
            b'Traceback (most recent call last):' not in result.stdout+result.stderr and
            b'ID user decrement error' not in result.stdout+result.stderr)
    receipt=dict(status='PASS' if passed else 'FAIL',exit_code=result.returncode or (0 if passed else 1),command=command,artifacts=str(art),isolation=str(isolated),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    evidence=art/'capture-evidence.json'
    if evidence.exists():receipt.update(json.loads(evidence.read_text()))
    if passed:
        reopen_command=[str(Path(args.blender).resolve()),'--background','--factory-startup',
                        '--python-exit-code','1','--python',
                        str(Path(__file__).with_name('axismeld_rigging_workspace_test.py').resolve()),
                        '--','--case','gui-reopen','--artifacts',str(art)]
        reopened=subprocess.run(reopen_command,env=env,startupinfo=startup,capture_output=True,timeout=90)
        (art/'reopen.stdout.log').write_bytes(reopened.stdout)
        (art/'reopen.stderr.log').write_bytes(reopened.stderr)
        receipt['reopen_command']=reopen_command
        receipt['reopen_exit_code']=reopened.returncode
        if reopened.returncode or b'AXISMELD_RIGGING_WORKSPACE_PASS gui-reopen' not in reopened.stdout:
            receipt['status']='FAIL';receipt['exit_code']=reopened.returncode or 1
    (art/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    raise SystemExit(receipt['exit_code'])

try:
    import bpy
except ImportError:
    if __name__=='__main__':run()
else:
    import blf
    import imbuf
    import numpy as np
    sys.path.insert(0,str(Path(__file__).parent))
    from axismeld_hotbox_image_fixture import observed_menu_rectangles
    ART=Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
    ROOT=Path(os.environ['AXISMELD_TEST_ROOT'])
    bpy.context.preferences.use_preferences_save=False
    bpy.context.preferences.view.show_splash=False
    bpy.context.preferences.view.show_tooltips=False


def settle(count=8):
    for _ in range(count):yield


def suite():
    win=bpy.context.window
    expected=json.loads(Path(os.environ['AXISMELD_RIGGING_WORKSPACE_VERIFICATION']).read_text(encoding='utf-8-sig'))
    scriptroot=Path(bpy.utils.system_resource('SCRIPTS'))
    resources={}
    for item in expected['resources']:
        path=scriptroot.parent/item['path']
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual==item['sha256'],('Candidate resource drift',str(path),actual,item['sha256'])
        resources[item['path']]=actual
    evidence=dict(exe=bpy.app.binary_path,exe_sha256=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),pid=os.getpid(),
                  resources=resources,resource_fingerprint=hashlib.sha256(json.dumps(resources,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    assert evidence['exe_sha256']==expected['binary_sha256']
    (ART/'capture-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    (ART/'test-source.py').write_bytes(Path(__file__).read_bytes())
    print('RIGGING_GUI_EVIDENCE',json.dumps({k:v for k,v in evidence.items() if k!='resources'}),flush=True)
    from bl_ui import space_topbar
    captured={}
    original_draw=space_topbar.TOPBAR_HT_upper_bar.draw
    def capture_draw(self,context):
        if context.window == win:
            captured['area']=(context.area.x,context.area.y,context.area.width,context.area.height)
            captured['regions']=[(r.type,r.alignment,r.x,r.y,r.width,r.height) for r in context.area.regions]
        return original_draw(self,context)
    space_topbar.TOPBAR_HT_upper_bar.draw=capture_draw
    def shot(name):
        path=ART/(name+'.png')
        with bpy.context.temp_override(window=win):
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT',path,flush=True)
        picture=bpy.data.images.load(str(path),check_existing=False)
        try:
            width,height=picture.size
            return np.asarray(picture.pixels[:],dtype=np.float32).reshape(height,width,4).copy()
        finally: bpy.data.images.remove(picture)
    def event(kind,value='PRESS',x=400,y=500):
        win.event_simulate(type=kind,value=value,x=int(x),y=int(y))
    templates={}
    def locate(pixels,label,rect,allowed_rectangles=None,prefer_left=False,ink_levels=None):
        scale=bpy.context.preferences.system.ui_scale
        key=(scale,label)
        if key not in templates:
            blf.size(0,bpy.context.preferences.ui_styles[0].widget.points*scale)
            blf.color(0,1,1,1,1);blf.position(0,4,10*scale,0)
            canvas=imbuf.new((int(600*scale),int(40*scale)))
            with blf.bind_imbuf(0,canvas): blf.draw_buffer(0,label)
            path=ROOT/('glyph-'+str(len(templates))+'.png')
            imbuf.write(canvas,filepath=str(path));canvas.free()
            picture=bpy.data.images.load(str(path),check_existing=False)
            try:
                w,h=picture.size
                alpha=np.asarray(picture.pixels[:],dtype=np.float32).reshape(h,w,4)[:,:,3]>.35
                yy,xx=np.nonzero(alpha)
                templates[key]=alpha[yy.min():yy.max()+1,xx.min():xx.max()+1].copy()
            finally: bpy.data.images.remove(picture)
        glyph=templates[key];gh,gw=glyph.shape
        x0,y0,x1,y1=map(int,rect)
        if isinstance(ink_levels,tuple):
            # Native workspace tabs use their own text theme color. Compare the
            # same full glyph at different foreground cuts; keep the unchanged
            # > .75 agreement requirement instead of accepting a weaker match.
            scores=[]
            for level in ink_levels:
                try:
                    scores.append(locate(pixels,label,rect,allowed_rectangles,prefer_left,level))
                except AssertionError:
                    pass
            assert scores,('No complete themed workspace caption',label,rect)
            return scores[0]
        ink=np.min(pixels[y0:y1,x0:x1,:3],axis=2)>(.18 if ink_levels is None else ink_levels)
        if allowed_rectangles is not None:
            allowed=np.zeros(ink.shape,dtype=bool)
            for ax0,ay0,ax1,ay1 in allowed_rectangles:
                allowed[max(0,ay0-y0):min(y1-y0,ay1-y0),max(0,ax0-x0):min(x1-x0,ax1-x0)]=True
            ink &= allowed
        assert ink.shape[0]>=gh and ink.shape[1]>=gw,(label,rect,glyph.shape)
        shape=(ink.shape[0]+gh-1,ink.shape[1]+gw-1)
        hits=np.fft.irfft2(np.fft.rfft2(ink,s=shape)*np.fft.rfft2(glyph[::-1,::-1],s=shape),s=shape)[gh-1:ink.shape[0],gw-1:ink.shape[1]]
        total=np.pad(ink.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
        counts=total[gh:,gw:]-total[:-gh,gw:]-total[gh:,:-gw]+total[:-gh,:-gw]
        score=2*hits/(counts+np.count_nonzero(glyph))
        # Match a complete native row caption, not Camera inside Camera, Aim
        # and Up. Actual icon/shortcut cells have a wider gap than word spaces.
        if allowed_rectangles is not None:
            margin=max(5,round(9*scale))
            for cy,cx in zip(*np.nonzero(score>.75)):
                if (np.any(ink[cy:cy+gh,max(0,cx-round(6*scale)):max(0,cx-round(2*scale))]) or
                        np.any(ink[cy:cy+gh,cx+gw+round(2*scale):min(ink.shape[1],cx+gw+margin)])):
                    score[cy,cx]=0
        y,x=np.unravel_index(np.argmax(score),score.shape)
        if prefer_left and np.any(score>.75):
            x=int(np.nonzero(score>.75)[1].min())
            y=int(np.argmax(score[:,x]))
        assert score[y,x]>.75,(label,float(score[y,x]),rect)
        print('ACTUAL_LABEL',label,float(score[y,x]),(x+x0,y+y0,gw,gh),flush=True)
        return (x+x0+gw/2,y+y0+gh/2)
    def click(point):
        event('MOUSEMOVE','NOTHING',*point);yield from settle(2)
        event('LEFTMOUSE','PRESS',*point);yield from settle(2)
        event('LEFTMOUSE','RELEASE',*point);yield from settle(2)
    def rect(r):
        return (r.x,r.y,r.x+r.width,r.y+r.height)
    def view():
        return max((a for a in win.screen.areas if a.type=='VIEW_3D'),key=lambda a:a.width*a.height)
    def header():return next(r for r in view().regions if r.type=='HEADER')
    def view_menu_rect(pixels):
        bounds=rect(header())
        point=locate(pixels,'View',bounds,prefer_left=True,ink_levels=(.08,.12,.18,.25))
        width=templates[(bpy.context.preferences.system.ui_scale,'View')].shape[1]
        # Editor/mode selectors precede View. Their similar short captions (for
        # example Edit Mode versus Edit Mesh) are not viewport menu roots.
        return (int(point[0]-width/2-1),bounds[1],bounds[2],bounds[3])
    def top_rect():
        r=next(r for r in captured['regions'] if r[0]=='HEADER' and r[1]=='TOP')
        return (r[2],r[3],r[2]+r[4],r[3]+r[5])
    def verify_topbar(tag):
        pixels=shot(tag)
        main=next(r for r in captured['regions'] if r[0]=='WINDOW')
        assert main[5]<=1,('Original Blender topbar must remain one row',captured)
        positions=[locate(pixels,label,top_rect(),prefer_left=True) for label in ('File','Edit','Render','Window','Help')]
        assert all(positions[i][0]<positions[i+1][0] for i in range(len(positions)-1))
        workspace=locate(pixels,win.workspace.name,top_rect(),ink_levels=(.08,.12,.18,.25))
        assert all(abs(point[1]-workspace[1])<4*bpy.context.preferences.system.ui_scale for point in positions)
        return pixels
    def set_config(name):
        preset=next(Path(p)/(name+'.py') for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/(name+'.py')).exists())
        assert bpy.utils.keyconfig_set(str(preset))
        yield from settle(14)
    def close():
        for _ in range(4):event('ESC');yield from settle(2)
    def popup(pixels,baseline,tag):
        scale=bpy.context.preferences.system.ui_scale
        changed=np.max(np.abs(pixels[:,:,:3]-baseline[:,:,:3]),axis=2)>.004
        boxes=observed_menu_rectangles((np.max(pixels[:,:,:3],axis=2)<.15)&changed,100*scale,25*scale)
        assert boxes,('No actual native popup',tag)
        return boxes
    def open_path(labels,tag,top=False):
        baseline=shot(tag+'-before')
        source=top_rect() if top else view_menu_rect(baseline)
        point=locate(baseline,labels[0],source,prefer_left=True,ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(10)
        pixels=shot(tag+'-root');boxes=popup(pixels,baseline,tag)
        print('ACTUAL_MENU_POPUPS',tag,0,boxes,flush=True)
        for i,label in enumerate(labels[1:]):
            point=locate(pixels,label,(0,0,win.width,win.height),boxes)
            event('MOUSEMOVE','NOTHING',*point);yield from settle(14)
            previous=pixels
            pixels=shot(tag+'-child-'+str(i));boxes=popup(pixels,previous,tag)
            # Match the next level only in its newly displayed popup. Parent
            # chapter labels can share a caption, e.g. Curves' Edit heading and
            # Hair Curves > Edit, without representing the same destination.
            print('ACTUAL_MENU_POPUPS',tag,i+1,boxes,flush=True)
        return pixels,boxes
    def activate_path(labels,tag,top=False):
        pixels,boxes=yield from open_path(labels[:-1],tag,top)
        point=locate(pixels,labels[-1],(0,0,win.width,win.height),boxes)
        yield from click(point);yield from settle(12)
    def switch_workspace(name):
        pixels=shot('workspace-before-'+name.lower())
        point=locate(pixels,name,top_rect(),ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(16)
        assert win.workspace.name==name,('Actual workspace click failed',name,win.workspace.name)
    from bl_ui import space_axismeld_menubar as ui
    def context():
        area=view();return bpy.context.temp_override(window=win,area=area,region=next(r for r in area.regions if r.type=='WINDOW'))
    def mode(value):
        with context():
            if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
            if value!='OBJECT':bpy.ops.object.mode_set(mode=value)
    def header_check(tag,rigging):
        pixels=shot(tag);bounds=view_menu_rect(pixels)
        for label in ('Skeleton','Skin'):
            if rigging:locate(pixels,label,bounds,ink_levels=(.08,.12,.18,.25))
            else:
                try:locate(pixels,label,bounds,ink_levels=(.08,.12,.18,.25))
                except AssertionError:pass
                else:raise AssertionError(('Rigging menu leaked outside its workspace',label))
        if rigging:
            with context():assert ui.rigging_workspace(bpy.context)
            assert sorted(a.type for a in win.screen.areas)==['OUTLINER','PROPERTIES','VIEW_3D']
        return pixels
    def weights():
        cube=bpy.data.objects['Cube']
        return tuple(tuple((g.group,g.weight) for g in v.groups) for v in cube.data.vertices)
    callbacks=[];draw_calls=[]
    sentinels=(('VIEW3D_MT_edit_armature','Garnet Cedar Dawn'),
               ('VIEW3D_MT_pose','Velvet Solar Crest'),
               ('VIEW3D_MT_paint_weight','Onyx Copper Vale'))
    for identifier,label in sentinels:
        def draw(self,context,identifier=identifier,label=label):
            draw_calls.append((identifier,context.mode));self.layout.label(text=label)
        getattr(bpy.types,identifier).append(draw);callbacks.append((identifier,draw))
    try:
        # The factory topbar may already have drawn before this timer installs
        # its observer. A real keyconfig refresh requests its next redraw.
        yield from set_config('Blender')
        assert win.workspace.name=='Layout'
        assert len(bpy.data.workspaces)==12 and bpy.data.workspaces['Rigging'].get('axismeld_workspace_role')=='RIGGING'
        verify_topbar('factory-native-topbar')
        header_check('factory-layout',False)
        yield from switch_workspace('Modeling')
        pixels=header_check('modeling-unchanged',False)
        # Modeling follows its existing keyconfig-dependent projection; under
        # native Blender keys this is the original Mesh/Vertex/Edge/Face row.
        locate(pixels,'Vertex',view_menu_rect(pixels),ink_levels=(.08,.12,.18,.25))
        yield from switch_workspace('Rigging')
        assert bpy.context.mode=='OBJECT'
        verify_topbar('rigging-native-topbar')
        header_check('rigging-blender-keys',True)
        yield from set_config('AxisMeld_Maya_2026')
        header_check('rigging-maya-keys',True)
        print('FACTORY_RIGGING_LAYOUT_HEADER_AND_KEYCONFIG_PASS',flush=True)
        with context():
            bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
        yield from settle(10)
        before=set(bpy.data.objects.keys())
        pixels,boxes=yield from open_path(('Skeleton',),'no-object-skeleton')
        point=locate(pixels,'Edit Bones',(0,0,win.width,win.height),boxes,ink_levels=(.04,.08,.12,.18))
        yield from click(point);yield from settle(8)
        assert set(bpy.data.objects.keys())==before and bpy.context.view_layer.objects.active is None
        yield from close()
        print('NO_SELECTION_DISABLED_EDIT_BONES_PASS',flush=True)
        yield from activate_path(('Skeleton','Add Armature','Rigify Meta-Rigs','Basic','Basic Human'),'skeleton-basic-human')
        arm=bpy.context.active_object
        assert arm.type=='ARMATURE' and len(arm.data.bones)>10 and any(b.rigify_type for b in arm.pose.bones)
        arm_name=arm.name
        shot('rigging-basic-human-created')
        print('SKELETON_NATIVE_METARIG_CREATION_PASS',len(arm.data.bones),flush=True)
        for value,path,identifier,label,tag in (
                ('EDIT',('Skeleton','Edit Bones'),*sentinels[0],'native-armature-plugin'),
                ('POSE',('Skeleton','Pose'),*sentinels[1],'native-pose-plugin')):
            mode(value);yield from settle(12)
            pixels,boxes=yield from open_path(path,tag)
            locate(pixels,label,(0,0,win.width,win.height),boxes)
            assert any(call[0]==identifier for call in draw_calls)
            yield from close()
        print('ARMATURE_POSE_NATIVE_PLUGIN_HOSTS_PASS',flush=True)
        mode('OBJECT');yield from settle(10)
        def bind_fixture():
            with context():
                bpy.ops.object.select_all(action='DESELECT')
                cube=bpy.data.objects['Cube'];arm=bpy.data.objects[arm_name]
                cube.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
                bpy.ops.ed.undo_push(message='Rigging before native bind')
        bind_fixture();yield from settle(8)
        yield from activate_path(('Skin','Armature Deform','With Empty Groups'),'native-bind')
        cube=bpy.data.objects['Cube'];arm=bpy.data.objects[arm_name]
        assert cube.parent==arm and any(m.type=='ARMATURE' and m.object==arm for m in cube.modifiers)
        assert len(cube.vertex_groups)>10
        shot('native-armature-deform-created')
        yield from activate_path(('Edit','Undo'),'native-bind-undo',True)
        cube=bpy.data.objects['Cube']
        assert cube.parent is None and not cube.modifiers and not cube.vertex_groups
        print('SKIN_NATIVE_BIND_AND_UNDO_PASS',flush=True)
        bind_fixture();yield from settle(8)
        yield from activate_path(('Skin','Armature Deform','With Empty Groups'),'native-rebind')
        with context():
            bpy.ops.object.select_all(action='DESELECT')
            cube=bpy.data.objects['Cube'];cube.select_set(True);bpy.context.view_layer.objects.active=cube
            group=cube.vertex_groups[0];cube.vertex_groups.active_index=0
            for i in range(8):group.add([i],(i+1)/10,'REPLACE')
        yield from settle(8)
        yield from activate_path(('Skin','Weight Paint Mode'),'skin-enter-weight-paint')
        assert bpy.context.mode=='PAINT_WEIGHT'
        pixels,boxes=yield from open_path(('Skin','Weights'),'native-weight-plugin')
        locate(pixels,sentinels[2][1],(0,0,win.width,win.height),boxes)
        assert any(call[0]==sentinels[2][0] for call in draw_calls)
        yield from close()
        before=weights()
        with context():bpy.ops.ed.undo_push(message='Rigging before weight normalize')
        yield from activate_path(('Skin','Weights','Normalize'),'native-normalize')
        after=weights()
        assert after!=before and abs(max(g[0][1] for g in after)-1.0)<1e-6,(before,after)
        shot('native-weights-normalized')
        yield from activate_path(('Edit','Undo'),'native-weight-undo',True)
        assert weights()==before
        print('SKIN_NATIVE_WEIGHT_NORMALIZE_AND_UNDO_PASS',flush=True)
        mode('OBJECT');yield from settle(8)
        # Invoke exactly the native + operator; inspect its real General popup.
        original_workspaces=set(bpy.data.workspaces.keys())
        original_screens=set(bpy.data.screens.keys())
        baseline=shot('native-add-workspace-before')
        event('MOUSEMOVE','NOTHING',1100,win.height-15);yield from settle(4)
        with context():assert bpy.ops.workspace.add('INVOKE_DEFAULT')=={'INTERFACE'}
        yield from settle(10)
        pixels=shot('native-add-workspace-root');boxes=popup(pixels,baseline,'workspace-add')
        point=locate(pixels,'General',(0,0,win.width,win.height),boxes)
        event('MOUSEMOVE','NOTHING',*point);yield from settle(14)
        previous=pixels;pixels=shot('native-add-workspace-general');boxes=popup(pixels,previous,'workspace-general')
        point=locate(pixels,'Rigging',(0,0,win.width,win.height),boxes)
        yield from click(point);yield from settle(16)
        assert win.workspace.name=='Rigging.001' and win.workspace.get('axismeld_workspace_role')=='RIGGING'
        added_screens={screen.name for screen in win.workspace.screens}
        assert bpy.context.mode=='OBJECT'
        win.workspace.name='Character Setup'
        yield from settle(8);header_check('renamed-rigging-native-header',True)
        with context():assert bpy.ops.workspace.delete()=={'FINISHED'}
        yield from settle(14)
        assert 'Character Setup' not in bpy.data.workspaces
        assert added_screens.isdisjoint(bpy.data.screens.keys())
        assert set(bpy.data.workspaces.keys())==original_workspaces
        assert set(bpy.data.screens.keys())==original_screens
        win.workspace=bpy.data.workspaces['Rigging'];yield from settle(14)
        # The native deletion regression is triggered by custom properties,
        # including the role marker. Check the inactive path and an unmarked
        # factory Layout control without manufacturing unsupported shared IDs.
        for template,inactive in (('Rigging',True),('Layout',False)):
            with context():
                assert bpy.ops.workspace.append_activate(idname=template,filepath='<startup.blend>')=={'FINISHED'}
            yield from settle(14)
            added=win.workspace
            assert added.name==template+'.001'
            if inactive:
                added['acceptance_string']='unrelated custom property'
                win.workspace=bpy.data.workspaces['Rigging'];yield from settle(14)
            else:
                assert not added.keys()
            added_name=added.name
            added_screens={screen.name for screen in added.screens}
            event('MOUSEMOVE','NOTHING',600,500);yield from settle(4)
            # Window/area overrides rebuild their workspace context. Override
            # only workspace here, as the operator explicitly supports an
            # inactive workspace through CTX_wm_workspace's Python member.
            with bpy.context.temp_override(workspace=added):
                assert bpy.context.workspace==added
                assert bpy.ops.workspace.delete()=={'FINISHED'}
            yield from settle(14)
            assert added_name not in bpy.data.workspaces,(template,inactive,added_name,list(bpy.data.workspaces.keys()))
            assert added_screens.isdisjoint(bpy.data.screens.keys())
            assert set(bpy.data.workspaces.keys())==original_workspaces
            assert set(bpy.data.screens.keys())==original_screens
        win.workspace=bpy.data.workspaces['Rigging'];yield from settle(14)
        header_check('rigging-final',True)
        print('NATIVE_GENERAL_APPEND_RENAME_DELETE_PASS',flush=True)
        import axismeld_rigging_workspace_test as checks
        saved=ART/'gui-rigging.blend'
        with context():assert bpy.ops.wm.save_as_mainfile(filepath=str(saved),check_existing=False)=={'FINISHED'}
        (ART/'gui-saved-state.json').write_text(json.dumps(checks.state(),indent=2))
        (ART/'gui-saved-weights.json').write_text(json.dumps(weights(),indent=2))
        evidence['plugin_draw_calls']=draw_calls
        evidence['saved_file']=str(saved)
        (ART/'capture-evidence.json').write_text(json.dumps(evidence,indent=2))
        print('AXISMELD_RIGGING_WORKSPACE_GUI_PASS',flush=True)
    finally:
        for identifier,callback in callbacks:getattr(bpy.types,identifier).remove(callback)


if __name__=='__main__' and 'bpy' in globals():
    steps=suite()
    def tick():
        try:
            next(steps);return .04
        except StopIteration:bpy.ops.wm.quit_blender()
        except BaseException:
            traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
    bpy.app.timers.register(tick,first_interval=1)

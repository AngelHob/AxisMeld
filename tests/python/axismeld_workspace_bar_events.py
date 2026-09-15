# SPDX-License-Identifier: GPL-2.0-or-later
"""Real workspace/menu row acceptance in a disposable factory scene."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import bpy
import blf
import imbuf
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_menu_rectangles

ART = Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
ROOT = Path(os.environ['AXISMELD_TEST_ROOT'])
PHASE = 'workspace-bar'
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
# Avoid transient tooltip overlays while measuring actual row captions.
bpy.context.preferences.view.show_tooltips = False

def settle(count=8):
    for _ in range(count): yield

def suite():
    from bl_ui import space_axismeld_menubar as ui
    executed=[]
    original_run=ui.menubar_runtime.run
    def traced_run(*args):
        executed.append(args[1:3])
        print('ACTUAL_COMMAND_RUN',args[1:],flush=True)
        result=original_run(*args)
        print('ACTUAL_COMMAND_RESULT',result,flush=True)
        return result
    ui.menubar_runtime.run=traced_run
    win=bpy.context.window
    from bl_ui import space_topbar
    captured={}
    original_draw=space_topbar.TOPBAR_HT_upper_bar.draw
    def capture_draw(self,context):
        if context.window == win:
            captured['area']=(context.area.x,context.area.y,context.area.width,context.area.height)
            captured['regions']=[(r.type,r.alignment,r.x,r.y,r.width,r.height) for r in context.area.regions]
        return original_draw(self,context)
    space_topbar.TOPBAR_HT_upper_bar.draw=capture_draw
    resources={}
    scriptroot=Path(bpy.utils.system_resource('SCRIPTS'))
    paths=list((scriptroot/'modules/axismeld').glob('*.py'))
    paths += [scriptroot/'startup/bl_ui'/n for n in ('space_axismeld_menubar.py','space_topbar.py','__init__.py')]
    for path in paths:
        resources[path.relative_to(scriptroot).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    evidence={'phase':PHASE,'exe':bpy.app.binary_path,'exe_sha256':hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),'resources':resources,'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    evidence['resource_fingerprint']=hashlib.sha256(json.dumps(resources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (ART/'capture-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print('MENUBAR_EVIDENCE',json.dumps(evidence),flush=True)
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
    def region(kind,alignment=None):
        return next(r for r in captured['regions'] if r[0]==kind and (alignment is None or r[1]==alignment))
    def rect(r):
        return (r[2],r[3],r[2]+r[4],r[3]+r[5])
    def viewport_geometry():
        return [(a.type,a.x,a.y,a.width,a.height) for a in win.screen.areas]
    records=[]
    def verify_rows(tag,maya):
        pixels=shot(tag)
        if os.environ.get('AXISMELD_TEST_WINDOW_SIZE'):
            expected=tuple(map(int,os.environ['AXISMELD_TEST_WINDOW_SIZE'].split('x')))
            assert (win.width,win.height)==expected,('Requested window geometry changed during test',tag,expected,(win.width,win.height))
        scale=bpy.context.preferences.system.ui_scale
        print('ACTUAL_TOPBAR_REGIONS',tag,captured,flush=True)
        upper=region('HEADER','TOP');main=region('WINDOW')
        record={'tag':tag,'maya':maya,'ui_scale':scale,'window':[win.width,win.height],
                'area':captured['area'],'regions':captured['regions'],'workspace':win.workspace.name,
                'viewports':viewport_geometry()}
        records.append(record)
        if maya:
            assert main[5]>=18*scale,('Maya menus require a separate visible row',main,captured)
            assert abs(main[3]+main[5]-upper[3])<=1,('Two rows must be adjacent without overlap',main,upper)
            assert main[4]==win.width,('Maya menu row must span window',main,win.width)
            file_menu=locate(pixels,'File',rect(main),prefer_left=True)
            create_menu=locate(pixels,'Create',rect(main),prefer_left=True)
            assert abs(file_menu[1]-create_menu[1])<=2*scale
            workspace=locate(pixels,win.workspace.name,rect(upper),ink_levels=(.08,.12,.18,.25))
            assert workspace[1]-file_menu[1]>=18*scale
            assert captured['area'][3]>=upper[5]+main[5]
        else:
            assert main[5]<=1,('Blender fallback left a second blank row',main)
            assert abs(captured['area'][3]-upper[5])<=2
            locate(pixels,'File',rect(upper),prefer_left=True)
            locate(pixels,win.workspace.name,rect(upper),ink_levels=(.08,.12,.18,.25))
        return pixels
    def close():
        for _ in range(3):
            event('ESC');yield from settle(2)
    def menu_path(labels,tag):
        baseline=shot(tag+'-before')
        point=locate(baseline,labels[0],rect(region('WINDOW')),prefer_left=True)
        yield from click(point);yield from settle(10)
        for i,label in enumerate(labels[1:]):
            pixels=shot(tag+'-'+str(i))
            scale=bpy.context.preferences.system.ui_scale
            changed=np.max(np.abs(pixels[:,:,:3]-baseline[:,:,:3]),axis=2)>.004
            boxes=observed_menu_rectangles((np.max(pixels[:,:,:3],axis=2)<.15)&changed,100*scale,30*scale)
            assert boxes,('No actual menu popup',labels,i)
            point=locate(pixels,label,(0,0,win.width,region('WINDOW')[3]),boxes)
            if i==len(labels)-2:yield from click(point)
            else:event('MOUSEMOVE','NOTHING',*point)
            yield from settle(12)
    def set_config(name):
        preset=next(Path(p)/(name+'.py') for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/(name+'.py')).exists())
        assert bpy.utils.keyconfig_set(str(preset))
        yield from settle(14)
        assert ui.enabled(bpy.context)==(name=='AxisMeld_Maya_2026')

    yield from settle(12)
    yield from set_config('Blender')
    assert not ui.enabled(bpy.context)
    native_geometry=viewport_geometry()
    verify_rows('native-blender-initial',False)
    native_height=captured['area'][3]
    yield from set_config('AxisMeld_Maya_2026')
    verify_rows('maya-workspace-rows',True)
    maya_height=captured['area'][3]
    assert maya_height>native_height
    original=win.workspace.name
    before=tuple(sorted(o.name for o in bpy.data.objects))
    for name in ('Modeling',original):
        pixels=shot('workspace-before-'+name.lower())
        point=locate(pixels,name,rect(region('HEADER','TOP')),ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(16)
        shot('workspace-click-result-'+name.lower())
        assert win.workspace.name==name,('Actual workspace tab click did not switch',name,win.workspace.name)
        assert tuple(sorted(o.name for o in bpy.data.objects))==before
        verify_rows('workspace-after-'+name.lower(),True)
    print('WORKSPACE_TAB_ROUNDTRIP_PASS',flush=True)
    if os.environ.get('AXISMELD_TEST_WINDOW_SIZE'):
        # A separate narrow-window acceptance checks row geometry and workspace
        # interaction. The full normal-window run owns the five-set action audit.
        yield from set_config('Blender')
        verify_rows('narrow-native-restored',False)
        assert viewport_geometry()==native_geometry
        yield from set_config('AxisMeld_Maya_2026')
        verify_rows('narrow-maya-restored',True)
        bpy.context.preferences.view.ui_scale=1.5
        yield from settle(16)
        verify_rows('narrow-maya-scale-1-5',True)
        yield from set_config('Blender')
        verify_rows('narrow-native-scale-1-5',False)
        yield from set_config('AxisMeld_Maya_2026')
        verify_rows('narrow-maya-scale-1-5-restored',True)
        (ART/'workspace-row-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        print('NARROW_ROW_GEOMETRY_ROUNDTRIP_PASS',flush=True)
        print('AXISMELD_WORKSPACE_BAR_PASS',flush=True)
        return
    # The lower row must own all menu-set interaction and leave workspaces alone.
    for mode in ('MODELING','RIGGING','ANIMATION','FX','RENDERING','MODELING'):
        menu=region('WINDOW');scale=bpy.context.preferences.system.ui_scale
        yield from click((menu[2]+45*scale,menu[3]+menu[5]/2));yield from settle(8)
        event('HOME');yield from settle(2)
        for _ in range(('MODELING','RIGGING','ANIMATION','FX','RENDERING').index(mode)):
            event('DOWN_ARROW');yield from settle(2)
        event('RET');yield from settle(10)
        assert win.workspace.name==original
        assert bpy.context.window_manager.axismeld_menubar_set==mode
        pixels=verify_rows('menu-set-'+mode.lower(),True)
        point=locate(pixels,'Create',rect(region('WINDOW')),prefer_left=True)
        yield from click(point);yield from settle(10)
        popup=shot('menu-set-popup-'+mode.lower())
        changed=np.max(np.abs(popup[:,:,:3]-pixels[:,:,:3]),axis=2)>.004
        boxes=observed_menu_rectangles((np.max(popup[:,:,:3],axis=2)<.15)&changed,100*scale,30*scale)
        # Native popup padding can overlap a few pixels of its source button.
        # Its observed top must stay below that lower-row caption and below
        # the entire workspace row.
        assert boxes and all(b[3]<point[1] and b[3]<region('HEADER','TOP')[3] for b in boxes),('Popup must open from lower row',boxes,point)
        locate(popup,'Polygon Primitives',(0,0,win.width,region('WINDOW')[3]),boxes)
        yield from close()
    print('LOWER_ROW_MENU_SETS_POPUPS_PASS',flush=True)
    view=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    view_region=next(r for r in view.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=win,area=view,region=view_region):bpy.ops.ed.undo_push(message='Workspace row GUI baseline')
    yield from menu_path(('Create','Polygon Primitives','Cube'),'create-cube')
    assert len(bpy.data.objects)==len(before)+1
    assert executed[-1]==('command','mesh.create_cube')
    mesh=bpy.context.view_layer.objects.active.data
    assert (len(mesh.vertices),len(mesh.polygons))==(8,6)
    yield from menu_path(('Edit','Undo'),'cube-undo')
    assert tuple(sorted(o.name for o in bpy.data.objects))==before
    print('LOWER_ROW_CREATE_CUBE_UNDO_PASS',flush=True)
    yield from set_config('Blender')
    verify_rows('native-blender-restored',False)
    assert captured['area'][3]==native_height
    assert viewport_geometry()==native_geometry,('Single-row fallback did not restore editor geometry immediately',native_geometry,viewport_geometry())
    yield from set_config('AxisMeld_Maya_2026')
    verify_rows('maya-restored',True)
    assert captured['area'][3]==maya_height
    print('KEYCONFIG_ROW_GEOMETRY_ROUNDTRIP_PASS',flush=True)
    # Startup window geometry is passed by the runner. 1.5 UI scale also exercises
    # the independent row heights when there is less horizontal room per widget.
    bpy.context.preferences.view.ui_scale=1.5
    yield from settle(16)
    verify_rows('maya-scale-1-5',True)
    yield from menu_path(('Create','Polygon Primitives','Cube'),'scale-1-5-create')
    assert len(bpy.data.objects)==len(before)+1 and executed[-1]==('command','mesh.create_cube')
    yield from menu_path(('Edit','Undo'),'scale-1-5-undo')
    assert tuple(sorted(o.name for o in bpy.data.objects))==before
    yield from set_config('Blender')
    verify_rows('native-scale-1-5',False)
    yield from set_config('AxisMeld_Maya_2026')
    verify_rows('maya-scale-1-5-restored',True)
    print('SCALED_ROW_GEOMETRY_AND_ACTIONS_PASS',flush=True)
    (ART/'workspace-row-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('AXISMELD_WORKSPACE_BAR_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps);return .04
    except StopIteration: bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

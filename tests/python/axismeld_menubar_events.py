# SPDX-License-Identifier: GPL-2.0-or-later
"""Real native topbar input acceptance in a disposable factory scene."""
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
PHASE = os.environ.get('AXISMELD_TEST_SUITE','').removeprefix('menubar-')
if PHASE not in {'actions','sets','layout'}: PHASE=os.environ.get('AXISMELD_MENUBAR_PHASE','all')
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False

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
    def locate(pixels,label,rect,allowed_rectangles=None,prefer_left=False):
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
        ink=np.min(pixels[y0:y1,x0:x1,:3],axis=2)>(.55 if label=='Save As' else .18)
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
        event('MOUSEMOVE','NOTHING',*point)
        event('LEFTMOUSE','PRESS',*point);event('LEFTMOUSE','RELEASE',*point)
    def menu_path(labels,tag):
        pixels=shot(tag+'-before')
        background=pixels.copy()
        scale=bpy.context.preferences.system.ui_scale
        point=locate(pixels,labels[0],(95*scale,win.height-26*scale,win.width,win.height),prefer_left=True)
        click(point);yield from settle(10)
        for index,label in enumerate(labels[1:]):
            pixels=shot(tag+'-'+str(index))
            dark=np.max(pixels[:,:,:3],axis=2)<.15
            changed=np.max(np.abs(pixels[:,:,:3]-background[:,:,:3]),axis=2)>.004
            boxes=observed_menu_rectangles(dark & changed,100*scale,30*scale)
            assert boxes,('No actual changed menu background',tag,label)
            print('ACTUAL_POPUP_BACKGROUNDS',tag,label,boxes,flush=True)
            point=locate(pixels,label,(0,0,win.width,win.height-26*scale),boxes)
            assert any(x0<point[0]<x1 and y0<point[1]<y1 for x0,y0,x1,y1 in boxes)
            if index==len(labels)-2:
                if tag=='create-cube':
                    rgb=pixels[:,:,:3]
                    gear_mask=(np.min(rgb,axis=2)>.18)&(np.max(rgb,axis=2)<.5)
                    region_mask=np.zeros(gear_mask.shape,dtype=bool)
                    region_mask[max(0,int(point[1]-10*scale)):int(point[1]+10*scale),int(point[0]+60*scale):max(b[2] for b in boxes)]=True
                    gears=observed_menu_rectangles(gear_mask&region_mask,5*scale,5*scale)
                    gears=[b for b in gears if b[2]-b[0]<20*scale and b[3]-b[1]<20*scale]
                    assert len(gears)==1,('Independent Cube Options glyph not unique',gears)
                    gx0,gy0,gx1,gy1=gears[0]
                    snapshot=tuple(sorted(o.name for o in bpy.data.objects));calls=len(executed)
                    click(((gx0+gx1)/2,(gy0+gy1)/2));yield from settle(6)
                    assert tuple(sorted(o.name for o in bpy.data.objects))==snapshot and len(executed)==calls
                    print('ACTUAL_DISABLED_OPTIONS_PASS',gears[0],flush=True)
                    shot('cube-disabled-options-click')
                event('MOUSEMOVE','NOTHING',*point);yield from settle(5)
                event('LEFTMOUSE','PRESS',*point);yield from settle(2)
                event('LEFTMOUSE','RELEASE',*point)
            else: event('MOUSEMOVE','NOTHING',*point)
            yield from settle(12)
    yield from settle(12)
    assert not ui.enabled(bpy.context)
    shot('native-blender-fallback')
    preset=next(Path(p)/'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    yield from settle(12)
    assert ui.enabled(bpy.context)
    print('WINDOW',win.width,win.height,[(a.type,a.x,a.y,a.width,a.height) for a in win.screen.areas],flush=True)
    if PHASE not in {'actions','layout'}:
        raw=json.loads((Path(__file__).resolve().parents[2]/'docs/reference/maya2026-menubar-tree.json').read_text(encoding='utf-8'))
        initial_scene=tuple(sorted(o.name for o in bpy.data.objects))
        initial_workspace=win.workspace.as_pointer()
        for mode,label in (('MODELING','Modeling'),('RIGGING','Rigging'),('ANIMATION','Animation'),('FX','FX'),('RENDERING','Rendering'),('MODELING','Modeling')):
            click((45,win.height-13));yield from settle(8)
            pixels=shot('selector-'+mode.lower())
            event('HOME');yield from settle(2)
            for _ in range(('MODELING','RIGGING','ANIMATION','FX','RENDERING').index(mode)):
                event('DOWN_ARROW');yield from settle(2)
            event('RET');yield from settle(8)
            assert bpy.context.window_manager.axismeld_menubar_set==mode,'actual enum click did not switch menu set'
            pixels=shot('topbar-'+mode.lower())
            record=next(r for r in raw['menu_sets'] if r['label']==label)
            previous=95
            for title in record['visible_top_labels']:
                point=locate(pixels,title.strip(),(previous,win.height-25,win.width,win.height),prefer_left=True)
                assert point[0]>previous
                previous=point[0]+2
            assert win.workspace.as_pointer()==initial_workspace
            assert tuple(sorted(o.name for o in bpy.data.objects))==initial_scene
        yield from settle(8)
    if PHASE=='sets':
        print('AXISMELD_MENUBAR_SETS_PASS',flush=True)
        return
    print('ACTUAL_SCALE_COLUMNS',bpy.context.preferences.system.ui_scale,[[n['label'] for n in col] for col in ui.menu_columns(ui._NODES['common.edit']['children'],bpy.context)],flush=True)
    if PHASE=='layout':
        for requested in (1.0,2.0):
            bpy.context.preferences.view.ui_scale=requested
            yield from settle(14)
            scale=bpy.context.preferences.system.ui_scale
            for label in ('Create','Edit','File'):
                pixels=shot('layout-'+str(requested)+'-'+label+'-header')
                point=locate(pixels,label,(95*scale,win.height-26*scale,win.width,win.height),prefer_left=True)
                click(point);yield from settle(12)
                popup=shot('layout-'+str(requested)+'-'+label+'-popup')
                changed=np.max(np.abs(popup[:,:,:3]-pixels[:,:,:3]),axis=2)>.004
                boxes=observed_menu_rectangles((np.max(popup[:,:,:3],axis=2)<.15)&changed,100*scale,30*scale)
                assert boxes,('No actual popup',label,requested)
                assert all(0<=x0<x1<=win.width and 0<=y0<y1<=win.height for x0,y0,x1,y1 in boxes)
                if label=='Create':
                    locate(popup,'Adobe(R) Illustrator(R) Object...',(0,0,win.width,win.height-26*scale),boxes)
                    locate(popup,'Collections',(0,0,win.width,win.height-26*scale),boxes)
                elif label=='File':
                    locate(popup,'New Scene',(0,0,win.width,win.height-26*scale),boxes)
                    locate(popup,'Exit',(0,0,win.width,win.height-26*scale),boxes)
                else:
                    locate(popup,'Unparent',(0,0,win.width,win.height-26*scale),boxes)
                print('ACTUAL_LAYOUT_BOUNDS',label,requested,boxes,flush=True)
                event('ESC');yield from settle(6)
        print('AXISMELD_MENUBAR_LAYOUT_PASS',flush=True)
        return
    # Real popup traversal; observations come from full rendered labels.
    view=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in view.regions if r.type=='WINDOW')
    before=tuple(sorted(o.name for o in bpy.data.objects))
    with bpy.context.temp_override(window=win,area=view,region=region):
        bpy.ops.ed.undo_push(message='Menubar GUI baseline')
    yield from menu_path(('Create','Polygon Primitives','Cube'),'create-cube')
    shot('cube-after-click')
    assert len(bpy.data.objects)==len(before)+1,('Cube did not create',list(bpy.data.objects))
    assert bpy.context.view_layer.objects.active.type=='MESH'
    assert executed[-1]==('command','mesh.create_cube')
    mesh=bpy.context.view_layer.objects.active.data
    assert (len(mesh.vertices),len(mesh.polygons))==(8,6)
    yield from menu_path(('Edit','Undo'),'cube-one-undo')
    assert tuple(sorted(o.name for o in bpy.data.objects))==before,'one Undo did not restore scene'
    for submenu,label,kind in [('Cameras','Camera','CAMERA'),('Lights','Point Light','LIGHT')]:
        yield from menu_path(('Create',submenu,label),'create-'+kind.lower())
        assert bpy.context.view_layer.objects.active.type==kind
        assert executed[-1]==('action','create.camera' if kind=='CAMERA' else 'create.light_point')
        if kind=='LIGHT': assert bpy.context.view_layer.objects.active.data.type=='POINT'
        assert len(bpy.data.objects)==len(before)+1
        yield from menu_path(('Edit','Undo'),kind.lower()+'-one-undo')
        assert tuple(sorted(o.name for o in bpy.data.objects))==before
    print('MENUBAR_ACTIONS_CREATE_UNDO_PASS',flush=True)
    # Removing every 3D source must gray semantic actions, not reroute them.
    views=[a for a in win.screen.areas if a.type=='VIEW_3D']
    previous_calls=len(executed)
    try:
        for source_area in views: source_area.type='CONSOLE'
        yield from settle(8)
        yield from menu_path(('Create','Polygon Primitives','Cube'),'no-3d-disabled-cube')
        assert len(executed)==previous_calls
        assert tuple(sorted(o.name for o in bpy.data.objects))==before
        shot('no-3d-disabled-after-click')
        event('ESC');yield from settle(4)
        event('ESC');yield from settle(4)
    finally:
        for source_area in views: source_area.type='VIEW_3D'
    yield from settle(8)
    print('MENUBAR_NO_3D_DISABLED_PASS',flush=True)
    original_areas=tuple((a.as_pointer(),a.type) for a in win.screen.areas)
    original_windows=set(w.as_pointer() for w in bpy.context.window_manager.windows)
    yield from menu_path(('Windows','Outliner'),'new-outliner-window')
    added=[w for w in bpy.context.window_manager.windows if w.as_pointer() not in original_windows]
    assert len(added)==1,'Outliner did not open exactly one independent window'
    assert any(a.type=='OUTLINER' for a in added[0].screen.areas)
    assert tuple((a.as_pointer(),a.type) for a in win.screen.areas)==original_areas
    assert tuple(sorted(o.name for o in bpy.data.objects))==before
    with bpy.context.temp_override(window=added[0]): bpy.ops.wm.window_close()
    yield from settle(12)
    print('MENUBAR_EDITOR_INDEPENDENT_WINDOW_PASS',flush=True)
    yield from menu_path(('File','Save Scene As...'),'native-save-as')
    browsers=[(w,a) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type=='FILE_BROWSER']
    assert len(browsers)==1,'native Save As file browser did not open'
    browser_win,browser_area=browsers[0]
    target=ART/'native-menu-save.blend'
    browser_area.spaces.active.params.directory=str(ART).encode()
    browser_area.spaces.active.params.filename=target.name
    browser_area.tag_redraw();yield from settle(10)
    oldwin=win;win=browser_win
    pixels=shot('native-save-file-browser')
    point=locate(pixels,'Save As',(win.width*.5,0,win.width,win.height*.25))
    click(point);yield from settle(20)
    win=oldwin
    assert target.is_file() and target.stat().st_size>1000,'native Save As did not save requested temporary file'
    assert Path(bpy.data.filepath).resolve()==target.resolve()
    assert tuple(sorted(o.name for o in bpy.data.objects))==before
    print('MENUBAR_NATIVE_SAVE_PASS',target,flush=True)
    print('AXISMELD_MENUBAR_ACTIONS_PASS' if PHASE=='actions' else 'AXISMELD_MENUBAR_EVENTS_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps);return .04
    except StopIteration: bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

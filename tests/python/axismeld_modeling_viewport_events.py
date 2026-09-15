# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Modeling viewport-menu acceptance in a disposable factory scene."""
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
PHASE = 'modeling-viewport'
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
    paths += [scriptroot/'startup/bl_ui'/n for n in ('space_axismeld_menubar.py','space_topbar.py','space_view3d.py','__init__.py')]
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
    def rect(r):
        return (r.x,r.y,r.x+r.width,r.y+r.height)
    def view():
        return max((a for a in win.screen.areas if a.type=='VIEW_3D'),key=lambda a:a.width*a.height)
    def header():return next(r for r in view().regions if r.type=='HEADER')
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
        source=top_rect() if top else rect(header())
        point=locate(baseline,labels[0],source,prefer_left=True,ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(10)
        pixels=shot(tag+'-root');boxes=popup(pixels,baseline,tag)
        for i,label in enumerate(labels[1:]):
            point=locate(pixels,label,(0,0,win.width,win.height),boxes)
            event('MOUSEMOVE','NOTHING',*point);yield from settle(14)
            pixels=shot(tag+'-child-'+str(i));boxes=popup(pixels,baseline,tag)
        return pixels,boxes
    def activate_path(labels,tag,top=False):
        pixels,boxes=yield from open_path(labels[:-1],tag,top)
        point=locate(pixels,labels[-1],(0,0,win.width,win.height),boxes)
        yield from click(point);yield from settle(12)
    def scene_state():
        import bmesh
        state=[]
        for obj in bpy.context.scene.objects:
            data=None
            if obj.type=='MESH':
                if obj.mode=='EDIT':
                    bm=bmesh.from_edit_mesh(obj.data)
                    data=(tuple((tuple(v.co),v.select,v.hide) for v in bm.verts),len(bm.edges),len(bm.faces))
                else:data=(tuple((tuple(v.co),v.select,v.hide) for v in obj.data.vertices),len(obj.data.edges),len(obj.data.polygons))
            state.append((obj.name,obj.type,obj.mode,obj.select_get(),tuple(tuple(r) for r in obj.matrix_world),data))
        active=bpy.context.view_layer.objects.active
        return tuple(state),active.name if active else None
    def set_mode(mode):
        area=view();window_region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(window=win,area=area,region=window_region):
            if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
            if mode=='NONE':
                bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
            else:
                cube=bpy.data.objects['Cube'];cube.select_set(True);bpy.context.view_layer.objects.active=cube
                if mode=='EDIT':
                    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        yield from settle(12)
    def verify_header(tag,modeling,mode):
        pixels=shot(tag)
        row=header();bounds=rect(row)
        assert row.type=='HEADER' and row.y<top_rect()[1],('Modeling menus belong to the 3D viewport header',bounds,top_rect())
        native=('View','Select','Add')+(('Object',) if mode!='EDIT' else ())
        points=[locate(pixels,label,bounds,prefer_left=True,ink_levels=(.08,.12,.18,.25)) for label in native]
        if modeling:
            for label in ('Mesh','Components','Vertex','Edge','Face','Mesh Projection'):
                point=locate(pixels,label,bounds,(bounds,),prefer_left=True,ink_levels=(.08,.12,.18,.25))
                points.append(point)
                width=templates[(bpy.context.preferences.system.ui_scale,label)].shape[1]
                remaining=(int(point[0]+width/2+2),bounds[1],bounds[2],bounds[3])
                if remaining[2]-remaining[0]>width:
                    try:locate(pixels,label,remaining,(bounds,),prefer_left=True,ink_levels=(.08,.12,.18,.25))
                    except AssertionError:pass
                    else:raise AssertionError(('Duplicate visible viewport menu root',label))

        else:
            try:locate(pixels,'Components',bounds,ink_levels=(.08,.12,.18,.25))
            except AssertionError:pass
            else:raise AssertionError('Maya Components root leaked into Layout')
        assert max(p[1] for p in points)-min(p[1] for p in points)<5*bpy.context.preferences.system.ui_scale
        print('ACTUAL_VIEWPORT_HEADER',tag,mode,(row.x,row.y,row.width,row.height),points,flush=True)
        return pixels
    def switch_workspace(name):
        pixels=shot('workspace-before-'+name.lower())
        point=locate(pixels,name,top_rect(),ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(16)
        assert win.workspace.name==name,('Actual workspace click failed',name,win.workspace.name)
    sentinels=(('TOPBAR_MT_file','AxisMeld File Plugin Sentinel'),('TOPBAR_MT_file_import','AxisMeld Import Plugin Sentinel'),('VIEW3D_MT_edit_mesh_vertices','AxisMeld Vertex Plugin Sentinel'))
    callbacks=[]
    def add_sentinels():
        for identifier,label in sentinels:
            def draw(self,context,label=label):self.layout.label(text=label)
            getattr(bpy.types,identifier).append(draw);callbacks.append((identifier,draw))
    def remove_sentinels():
        for identifier,callback in callbacks:getattr(bpy.types,identifier).remove(callback)
        callbacks.clear()
    yield from set_config('Blender')
    verify_topbar('native-layout')
    verify_header('native-layout-viewport',False,'OBJECT')
    yield from set_config('AxisMeld_Maya_2026')
    verify_topbar('maya-profile-native-topbar')
    verify_header('maya-profile-layout-viewport',False,'OBJECT')
    print('ORIGINAL_TOPBAR_AND_LAYOUT_PASS',flush=True)
    add_sentinels()
    try:
        for path,label,tag in ((('File',),sentinels[0][1],'native-file-plugin'),(('File','Import'),sentinels[1][1],'native-import-plugin')):
            pixels,boxes=yield from open_path(path,tag,True)
            locate(pixels,label,(0,0,win.width,win.height),boxes)
            yield from close()
        print('NATIVE_TOPBAR_PLUGIN_APPEND_PASS',flush=True)
        yield from switch_workspace('Modeling')
        verify_topbar('modeling-native-topbar')
        for mode in ('OBJECT','NONE','EDIT'):
            yield from set_mode(mode)
            verify_header('modeling-header-'+mode.lower(),True,mode)
            before=scene_state();calls=len(executed)
            pixels,boxes=yield from open_path(('Components',),'components-'+mode.lower())
            point=locate(pixels,'Add Divisions',(0,0,win.width,win.height),boxes,ink_levels=(.08,.12,.18,.25))
            if mode!='EDIT':
                yield from click(point);yield from settle(8)
                assert scene_state()==before and len(executed)==calls,('Unavailable component command mutated context',mode)
            else:
                # The Maya option box is a distinct disabled button. Locate its
                # actual gear glyph on the Add Divisions row and click that cell.
                scale=bpy.context.preferences.system.ui_scale
                rgb=pixels[:,:,:3]
                mask=(np.min(rgb,axis=2)>.18)&(np.max(rgb,axis=2)<.5)
                allowed=np.zeros(mask.shape,dtype=bool)
                containing=next(b for b in boxes if b[0]<point[0]<b[2] and b[1]<point[1]<b[3])
                allowed[max(0,int(point[1]-10*scale)):int(point[1]+10*scale),int(point[0]+65*scale):containing[2]]=True
                gears=observed_menu_rectangles(mask&allowed,5*scale,5*scale)
                gears=[b for b in gears if b[2]-b[0]<20*scale and b[3]-b[1]<20*scale]
                assert len(gears)==1,('Maya Options gear not independently identified',gears)
                x0,y0,x1,y1=gears[0]
                yield from click(((x0+x1)/2,(y0+y1)/2));yield from settle(8)
                assert scene_state()==before and len(executed)==calls,'Maya Options click executed body'
                shot('maya-options-click-no-action')
            yield from close()
        print('MODE_CONTEXT_AND_DISABLED_OPTIONS_PASS',flush=True)
        pixels,boxes=yield from open_path(('Vertex','Blender Tools'),'native-vertex-plugin')
        locate(pixels,sentinels[2][1],(0,0,win.width,win.height),boxes)
        yield from close()
        area=view();window_region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(window=win,area=area,region=window_region):bpy.ops.ed.undo_push(message='Modeling viewport GUI baseline')
        before=scene_state()
        yield from activate_path(('Components','Add Divisions'),'subdivide')
        assert executed[-1]==('command','mesh.subdivide')
        import bmesh
        bm=bmesh.from_edit_mesh(bpy.context.active_object.data)
        assert (len(bm.verts),len(bm.faces))==(26,24),('Subdivision did not affect selected Cube',len(bm.verts),len(bm.faces))
        shot('subdivide-result')
        yield from activate_path(('Edit','Undo'),'subdivide-undo',True)
        assert scene_state()==before,'One Undo did not restore original edit mesh and selection'
        print('VIEWPORT_SUBDIVIDE_ONE_UNDO_PASS',flush=True)
        for menu_set,root_menu in (('Rigging','Skeleton'),('Animation','Key'),('FX','Fields/Solvers'),('Rendering','Lighting/Shading')):
            # First inspect the actual navigation and set submenu. Leaf captions
            # can be module-specific, so the native set root is the acceptance.
            pixels,boxes=yield from open_path(('Window','Maya Menu Sets',menu_set),'other-set-'+menu_set.lower(),True)
            locate(pixels,root_menu,(0,0,win.width,win.height),boxes)
            yield from close()
        print('OTHER_MAYA_MENU_SETS_REACHABLE_PASS',flush=True)
        yield from set_mode('OBJECT')
        yield from switch_workspace('Layout')
        verify_header('layout-restored-native-viewport',False,'OBJECT')
        verify_topbar('layout-restored-native-topbar')
        print('LAYOUT_NATIVE_ROUNDTRIP_PASS',flush=True)
    finally:remove_sentinels()
    for path,label,tag in ((('File',),sentinels[0][1],'native-file-plugin-removed'),(('File','Import'),sentinels[1][1],'native-import-plugin-removed')):
        pixels,boxes=yield from open_path(path,tag,True)
        try:locate(pixels,label,(0,0,win.width,win.height),boxes)
        except AssertionError:pass
        else:raise AssertionError(('Removed plugin sentinel still rendered',label))
        yield from close()
    print('NATIVE_PLUGIN_SENTINELS_REMOVED_PASS',flush=True)
    print('AXISMELD_MODELING_VIEWPORT_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps);return .04
    except StopIteration: bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

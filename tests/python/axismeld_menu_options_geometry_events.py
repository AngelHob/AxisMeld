# SPDX-License-Identifier: GPL-2.0-or-later
"""Native final-column Options geometry and hit-region acceptance."""
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
PHASE = 'menu-options-geometry'
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
    paths += [scriptroot/'startup/bl_ui'/n for n in ('space_axismeld_menubar.py','space_axismeld_native_modeling.py','space_topbar.py','space_view3d.py','space_image.py','__init__.py')]
    for path in paths:
        resources[path.relative_to(scriptroot).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    evidence={'phase':PHASE,'exe':bpy.app.binary_path,'exe_sha256':hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),'resources':resources,'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    evidence['resource_fingerprint']=hashlib.sha256(json.dumps(resources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (ART/'capture-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    (ART/'test-source.py').write_bytes(Path(__file__).read_bytes())
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
    labels=('Short','A moderate modeling label','An intentionally much longer modeling command','With Checkbox')
    class AXISMELD_MT_options_geometry(bpy.types.Menu):
        bl_label='Options Geometry Regression'
        def draw(self,context):
            column=self.layout.column();column.ui_units_x=28
            for i,label in enumerate(labels):
                ui._draw_item(column,context,{'id':'geometry.'+str(i),'kind':'command','command':'mesh.create_cube','origin':'maya','label':label,'icon':'MESH_CUBE','indicator':'checkbox' if i==3 else '', 'options':{'reason':'Independent disabled Maya Options'}})
            # These native rows are intentionally outside the Options pattern.
            row=column.row(align=True)
            for icon in ('PLAY','PLAY','PREFERENCES'):
                cell=row.row(align=True);cell.enabled=False
                op=cell.operator('axismeld.menubar_execute',text='',icon=icon)
                op.kind='disabled'
            row=column.row(align=True)
            body=row.row(align=True);body.enabled=False
            op=body.operator('axismeld.menubar_execute',text='Ordinary trailing control',icon='MESH_CUBE');op.kind='disabled'
            cell=row.row(align=True);cell.enabled=False
            op=cell.operator('axismeld.menubar_execute',text='',icon='PLAY');op.kind='disabled'
    bpy.utils.register_class(AXISMELD_MT_options_geometry)
    yield from settle(12)
    preset=next(Path(p)/'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset));yield from settle(12)
    area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=win,area=area,region=region):bpy.ops.ed.undo_push(message='Options geometry acceptance')
    records=[]
    def icon_boxes(pixels,rectangle,scale):
        rgb=pixels[:,:,:3]
        mask=(np.min(rgb,axis=2)>.18)&(np.max(rgb,axis=2)<.5)
        allowed=np.zeros(mask.shape,dtype=bool)
        x0,y0,x1,y1=map(int,rectangle);allowed[y0:y1,x0:x1]=True
        boxes=observed_menu_rectangles(mask&allowed,5*scale,5*scale)
        return [b for b in boxes if b[2]-b[0]<20*scale and b[3]-b[1]<20*scale]
    for requested in (1.0,1.5):
        bpy.context.preferences.view.ui_scale=requested;yield from settle(14)
        scale=bpy.context.preferences.system.ui_scale
        tag='options-'+str(requested)
        event('MOUSEMOVE','NOTHING',600,700);yield from settle(3)
        baseline=shot(tag+'-before')
        with bpy.context.temp_override(window=win,area=area,region=region):bpy.ops.wm.call_menu(name=AXISMELD_MT_options_geometry.__name__)
        yield from settle(12)
        pixels=shot(tag)
        changed=np.max(np.abs(pixels[:,:,:3]-baseline[:,:,:3]),axis=2)>.004
        boxes=observed_menu_rectangles((np.max(pixels[:,:,:3],axis=2)<.15)&changed,100*scale,30*scale)
        assert len(boxes)==1,(tag,boxes)
        popup=boxes[0];rows=[];positions={}
        for label in labels:
            point=locate(pixels,label,(0,0,win.width,win.height),boxes,ink_levels=(.08,.12,.18,.25));positions[label]=point
            glyph=templates[(scale,label)]
            gears=icon_boxes(pixels,(point[0]+glyph.shape[1]/2+5*scale,point[1]-10*scale,popup[2],point[1]+10*scale),scale)
            assert len(gears)==1,(tag,label,gears)
            g=gears[0]
            rows.append({'label':label,'glyph_rect':g,'center_x':(g[0]+g[2])/2,'right_margin':popup[2]-g[2]})
        # Isolate the first native icon slot geometrically. At fractional scale,
        # antialiasing can put parts of the adjacent enabled body icon into the
        # disabled color range, so color alone cannot distinguish the two slots.
        point=positions['With Checkbox'];label_left=point[0]-templates[(scale,'With Checkbox')].shape[1]/2
        prefix=sorted(icon_boxes(pixels,(popup[0],point[1]-10*scale,min(label_left-2*scale,popup[0]+24*scale),point[1]+10*scale),scale))
        assert len(prefix)==1,('Disabled leading checkbox was not distinct from the enabled body',prefix)
        checkbox=prefix[0]
        control_point=locate(pixels,'Ordinary trailing control',(0,0,win.width,win.height),boxes,ink_levels=(.08,.12,.18,.25))
        control_left=control_point[0]+templates[(scale,'Ordinary trailing control')].shape[1]/2+5*scale
        controls=icon_boxes(pixels,(control_left,control_point[1]-10*scale,popup[2],control_point[1]+10*scale),scale)
        assert len(controls)==1,('Ordinary trailing play control was not identified',controls)
        pure_y=(point[1]+control_point[1])/2
        pure=icon_boxes(pixels,(popup[0],pure_y-10*scale,popup[2],pure_y+10*scale),scale)
        assert len(pure)==3,('Pure icon row changed',pure)
        record={'requested_ui_scale':requested,'actual_ui_scale':scale,'popup':popup,'rows':rows,'center_spread':max(r['center_x'] for r in rows)-min(r['center_x'] for r in rows),'leading_checkbox_glyph':checkbox,'non_options_control_glyph':controls[0],'pure_icon_glyphs':pure}
        records.append(record)
        (ART/'option-geometry.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        print('ACTUAL_OPTIONS_GEOMETRY',json.dumps(record),flush=True)
        assert record['center_spread']<=1,('Options centers differ within one column',record)
        assert all(0<=r['right_margin']<=12*scale for r in rows),('Options were not aligned with the final popup right edge',record)
        assert popup[2]-controls[0][2]>=30*scale,'Unrelated trailing play control was stretched to the right edge'
        assert popup[2]-max(b[2] for b in pure)>=30*scale,'Pure icon row was stretched to the right edge'
        before=tuple(sorted(o.name for o in bpy.data.objects));calls=len(executed)
        gear=rows[0]['glyph_rect']
        yield from click(((gear[0]+gear[2])/2,(gear[1]+gear[3])/2));yield from settle(8)
        assert tuple(sorted(o.name for o in bpy.data.objects))==before and len(executed)==calls,'Options hit ran the main command'
        yield from click(((checkbox[0]+checkbox[2])/2,(checkbox[1]+checkbox[3])/2));yield from settle(8)
        assert tuple(sorted(o.name for o in bpy.data.objects))==before and len(executed)==calls,'Disabled leading checkbox hit ran the main command'
        # This point is in the newly absorbed blank width immediately before
        # the Options slot; it must belong to the body, not a visual-only stretch.
        yield from click((gear[0]-12*scale,positions['Short'][1]));yield from settle(12)
        assert len(bpy.data.objects)==len(before)+1 and executed[-1]==('command','mesh.create_cube'),'Expanded body hit region did not run the body command'
        with bpy.context.temp_override(window=win,area=area,region=region):bpy.ops.ed.undo()
        yield from settle(12)
        assert tuple(sorted(o.name for o in bpy.data.objects))==before
        print('OPTIONS_GEOMETRY_AND_HIT_REGIONS_PASS',requested,flush=True)
    print('AXISMELD_MENU_OPTIONS_GEOMETRY_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps);return .04
    except StopIteration:bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

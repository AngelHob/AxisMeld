# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real-input acceptance of fully expanded menus without paging."""
import os
from pathlib import Path
import sys
import traceback
import numpy as np
import imbuf
import blf
import bpy

root=Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
artifacts=Path(os.environ.get('AXISMELD_TEST_ARTIFACTS',root))
bpy.context.preferences.use_preferences_save=False
bpy.context.preferences.view.show_splash=False

def check(value,message):
    if not value:
        raise AssertionError(message)

def settle(count=6):
    for _ in range(count):
        yield

def suite():
    win=bpy.context.window
    area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    def override():
        return bpy.context.temp_override(window=win,area=area,region=region)
    preset=next(Path(p)/'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                if (Path(p)/'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)),'preset activation failed')
    yield from settle(8)
    with override():
        bpy.ops.screen.screen_full_area()
    yield from settle(8)
    area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    area.spaces.active.show_region_ui=False
    area.spaces.active.show_region_toolbar=False
    scale=bpy.context.preferences.system.ui_scale
    origin=[region.x+region.width/2,region.y+region.height/2]
    position=origin.copy()
    def event(kind,value='PRESS',point=None,**modifiers):
        if point is not None:
            position[:]=point
        win.event_simulate(type=kind,value=value,x=int(position[0]),y=int(position[1]),**modifiers)
    def capture(label):
        path = artifacts / (label + '.png')
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        picture = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = picture.size
            values = np.asarray(picture.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(picture)
        print('SCREENSHOT', path, flush=True)
        return values

    def foreground(pixels):
        rgb = pixels[:, :, :3]
        return (rgb[:, :, 1] > .24) & (rgb[:, :, 1] > np.maximum(rgb[:, :, 0], rgb[:, :, 2])*.45)

    templates={}
    template_baselines={}
    def template(label):
        key=(scale,label)
        if key not in templates:
            blf.size(0,bpy.context.preferences.ui_styles[0].widget.points*scale)
            blf.color(0,1,1,1,1)
            blf.position(0,4,10*scale,0)
            canvas=imbuf.new((int(420*scale),int(40*scale)))
            with blf.bind_imbuf(0,canvas):
                blf.draw_buffer(0,label)
            path=root/('label-'+str(len(templates))+'.png')
            imbuf.write(canvas,filepath=str(path))
            canvas.free()
            picture=bpy.data.images.load(str(path),check_existing=False)
            try:
                w,h=picture.size
                alpha=np.asarray(picture.pixels[:],dtype=np.float32).reshape(h,w,4)[:,:,3]>.35
                yy,xx=np.nonzero(alpha)
                templates[key]=alpha[yy.min():yy.max()+1,xx.min():xx.max()+1].copy()
                template_baselines[key]=float(yy.min())-10*scale
            finally:
                bpy.data.images.remove(picture)
        return templates[key]

    def locate(pixels,rect,label,required=True,native=False):
        # Font-only template matching locates actual rendered text, including
        # complete long labels. FFT correlation keeps many menu rows bounded.
        x0,y0,x1,y1=map(int,rect)
        x0=max(0,x0+2); y0=max(0,y0+2)
        ink=(np.min(pixels[y0:y1-1,x0:x1-1,:3],axis=2)>.55 if native
             else foreground(pixels[y0:y1-1,x0:x1-1]))
        glyph=template(label)
        gh,gw=glyph.shape
        check(ink.shape[0]>=gh and ink.shape[1]>=gw,'observed box cannot contain '+label)
        shape=(ink.shape[0]+gh-1,ink.shape[1]+gw-1)
        product=np.fft.rfft2(ink,s=shape)*np.fft.rfft2(glyph[::-1,::-1],s=shape)
        hits=np.fft.irfft2(product,s=shape)[gh-1:ink.shape[0],gw-1:ink.shape[1]]
        summed=np.pad(ink.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
        counts=summed[gh:,gw:]-summed[:-gh,gw:]-summed[gh:,:-gw]+summed[:-gh,:-gw]
        scores=2*hits/(counts+np.count_nonzero(glyph))
        y,x=np.unravel_index(np.argmax(scores),scores.shape)
        score=float(scores[y,x])
        if not required and score<=.75:
            return None
        check(score>.75,'actual full label not independently identified: '+repr((label,score,rect)))
        return (x+x0,y+y0,x+x0+gw,y+y0+gh),score

    bpy.context.preferences.view.ui_scale=2
    yield from settle(12)
    scale=bpy.context.preferences.system.ui_scale
    from axismeld import hotbox_runtime
    with override():
        hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
            'style':'rows','rows':['common'],'transparency':0}})
    import json
    original_snapshot=hotbox_runtime.snapshot
    def enabled_display_snapshot(context):
        value=json.loads(original_snapshot(context))
        pending=list(value['menus'])
        while pending:
            node=pending.pop()
            if node['id']=='common.display':
                node['label']='Layout Pressure'
                node['children']=[{'id':'test.entry.pressure.%02d'%i,'kind':'command',
                    'label':'Pressure item %02d for full menu layout'%i,
                    'enabled':True,'command':'view.wireframe','reason':'Synthetic owned-release pressure fixture',
                    'children':[]} for i in range(1,57)]
            pending.extend(node.get('children',[]))
        return json.dumps(value)
    hotbox_runtime.snapshot=enabled_display_snapshot
    origin[:]=[region.x+region.width/2,region.y+region.height/2]
    event('MOUSEMOVE','NOTHING',origin);event('SPACE');yield from settle(12)
    def probe_state():
        return (bpy.context.mode,tuple((o.name,o.select_get(),tuple(o.location)) for o in bpy.context.scene.objects),str(hotbox_runtime.recent.items()),area.spaces.active.shading.type,area.spaces.active.overlay.show_overlays,tuple(region.data.view_rotation),region.data.view_distance)
    initial=probe_state()
    pixels=capture('synthetic-pressure-entry')
    label=locate(pixels,(region.x,region.y,region.x+region.width,region.y+region.height),'Layout Pressure')[0]
    event('MOUSEMOVE','NOTHING',((label[0]+label[2])/2,(label[1]+label[3])/2));event('LEFTMOUSE')
    yield from settle(10)
    destination=artifacts/'synthetic-pressure-2x-enabled-entry.png'
    destination.parent.mkdir(parents=True,exist_ok=True)
    with override():bpy.ops.screen.screenshot(filepath=str(destination))
    print('SYNTHETIC_PRESSURE_SCREENSHOT',destination,flush=True)
    event('LEFTMOUSE','RELEASE')
    yield from settle(8)
    print('SYNTHETIC_STATIONARY_RELEASE',initial,probe_state(),flush=True)
    check(probe_state()==initial,'stationary synthetic entry release dispatched a newly exposed item')
    event('LEFTMOUSE')
    yield from settle(3)
    event('LEFTMOUSE','RELEASE')
    yield from settle(6)
    print('SYNTHETIC_FRESH_CLICK',probe_state(),flush=True)
    check(area.spaces.active.shading.type=='WIREFRAME','positive control enabled covered leaf did not execute')
    event('SPACE','RELEASE')
    event('ESC');event('ESC','RELEASE')
    yield from settle(7)
    check(not list(win.modal_operators),'display capture retained owner')
    hotbox_runtime.snapshot=original_snapshot
    print('AXISMELD_FULL_MENU_ENTRY_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps);return .025
    except StopIteration:bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

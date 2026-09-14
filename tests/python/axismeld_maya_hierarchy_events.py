# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real-input Maya hierarchy acceptance, using captured Maya UI metadata as oracle."""
import os
from pathlib import Path
import sys
import traceback
import numpy as np
import imbuf
import blf
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from axismeld_hotbox_geometry_fixture import label_prefix_starts
from axismeld_maya_hierarchy_test import normalized_reference_roots, visual_rows, ROOT_LABELS
import json

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
    for colors in (bpy.context.preferences.themes[0].user_interface.wcol_menu,
                   bpy.context.preferences.themes[0].user_interface.wcol_menu_back,
                   bpy.context.preferences.themes[0].user_interface.wcol_menu_item):
        colors.inner=(.8,.04,.65,1)
        colors.inner_sel=(.8,.04,.65,1)
    yield from settle(8)
    templates={}
    template_baselines={}
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
            # Magenta backdrop has low green; native disabled text/heading ink
            # is also valid text. Keep the full-label F1 gate unchanged.
            return rgb[:, :, 1] > .18

    def template(label, raster_alpha=.35):
            key=(scale,label) if raster_alpha==.35 else (scale,label,raster_alpha)
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
                    alpha=np.asarray(picture.pixels[:],dtype=np.float32).reshape(h,w,4)[:,:,3]>raster_alpha
                    yy,xx=np.nonzero(alpha)
                    templates[key]=alpha[yy.min():yy.max()+1,xx.min():xx.max()+1].copy()
                    template_baselines[key]=float(yy.min())-10*scale
                finally:
                    bpy.data.images.remove(picture)
            return templates[key]

    def locate(pixels,rect,label,required=True,native=False,raster_alpha=.35):
            # Font-only template matching locates actual rendered text, including
            # complete long labels. FFT correlation keeps many menu rows bounded.
            x0,y0,x1,y1=map(int,rect)
            x0=max(0,x0+2); y0=max(0,y0+2)
            ink=(np.min(pixels[y0:y1-1,x0:x1-1,:3],axis=2)>.55 if native
                 else foreground(pixels[y0:y1-1,x0:x1-1]))
            glyph=template(label,raster_alpha)
            gh,gw=glyph.shape
            if not required and (ink.shape[0]<gh or ink.shape[1]<gw):
                return None
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

    glyph_template=template

    def rendered_rows(pixels, rect, labels):
        x0,y0,x1,y1=map(int,rect)
        ink=foreground(pixels[y0:y1,x0+4:x1-int(26*scale)])
        occupied=np.flatnonzero(np.sum(ink,axis=1)>=scale)
        bands=np.split(occupied,np.flatnonzero(np.diff(occupied)>2*scale)+1)
        matches=[]
        for band in bands:
            if len(band)<3*scale:continue
            band_rect=(x0,max(y0,y0+int(band[0])-3*scale),x1,min(y1,y0+int(band[-1])+4*scale))
            sample=ink[band[0]:band[-1]+1]
            yy,xx=np.nonzero(sample)
            if not len(xx):continue
            sample_origin=x0+4+int(xx.min())
            sample=sample[:,xx.min():xx.max()+1]
            occupied_columns=np.flatnonzero(np.any(sample,axis=0))
            widths=[(start,sample.shape[1]-start) for start in label_prefix_starts(occupied_columns,scale)]
            candidates=[]
            for label in set(labels):
                valid_starts=[start for start,width in widths if abs(width-template(label).shape[1])<=3*scale]
                if not valid_starts:continue
                found=locate(pixels,band_rect,label,required=False)
                if found is not None:
                    glyph,score=found
                    valid_starts=[start for start in valid_starts if abs(glyph[0]-(sample_origin+start))<=3*scale]
                    if not valid_starts:continue
                    candidates.append((-min(valid_starts),score,label,glyph))
            if not candidates:continue
            # Actual full ink width rejects substring matches independently of
            # expected ordering; the full-label F1>.75 gate remains unchanged.
            _,score,label,glyph=max(candidates)
            cy=glyph[1]-template_baselines[(scale,label)]+4*scale
            matches.append((label,(x0+x1)/2,cy,score))
        return sorted(matches,key=lambda item:-item[2])

    def columns(pixels,minimum_width=150,minimum_height=60):
            # Four-neighbour connected backgrounds separate even a 4px column gap.
            # Glyph holes do not split a menu because its background surrounds them.
            rgb=pixels[:,:,:3]
            mask=(rgb[:,:,0]>.3)&(rgb[:,:,2]>.25)&(np.minimum(rgb[:,:,0],rgb[:,:,2])>2.2*rgb[:,:,1])
            parents=[];boxes=[];previous=[]
            def find(i):
                while parents[i]!=i:
                    parents[i]=parents[parents[i]];i=parents[i]
                return i
            def join(a,b):
                a,b=find(a),find(b)
                if a==b:return
                parents[b]=a
                boxes[a]=[min(boxes[a][0],boxes[b][0]),min(boxes[a][1],boxes[b][1]),
                          max(boxes[a][2],boxes[b][2]),max(boxes[a][3],boxes[b][3])]
            for y in range(win.height):
                xs=np.flatnonzero(mask[y]);current=[]
                for span in np.split(xs,np.flatnonzero(np.diff(xs)>1)+1):
                    if not len(span):continue
                    x0,x1=int(span[0]),int(span[-1])+1
                    i=len(parents);parents.append(i);boxes.append([x0,y,x1,y+1]);current.append((x0,x1,i))
                start=0
                for x0,x1,i in current:
                    while start<len(previous) and previous[start][1]<=x0:start+=1
                    j=start
                    while j<len(previous) and previous[j][0]<x1:
                        join(i,previous[j][2]);j+=1
                previous=current
            result=[tuple(boxes[i]) for i in range(len(parents)) if find(i)==i
                    and boxes[i][2]-boxes[i][0]>minimum_width*scale and boxes[i][3]-boxes[i][1]>minimum_height*scale]
            trimmed=[]
            for x0,y0,x1,y1 in result:
                spans=[np.flatnonzero(mask[y,x0:x1]) for y in range(y0,y1)]
                spans=[xs for xs in spans if len(xs)>20*scale]
                if spans:
                    # Most physical scanlines expose the real column edges.
                    # A touching primary button may extend only a few top rows.
                    left=x0+int(np.median([xs[0] for xs in spans]));right=x0+int(np.median([xs[-1]+1 for xs in spans]))
                    trimmed.append((left,y0,right,y1))
            return sorted(trimmed,key=lambda r:r[0])

    from axismeld import hotbox_runtime
    references=normalized_reference_roots()
    reports=[]
    failures=[]

    def state():
        return (bpy.context.mode, tuple((o.name,o.select_get(),tuple(tuple(v) for v in o.matrix_world))
                    for o in bpy.context.scene.objects), tuple(hotbox_runtime.recent.items()),
                region.data.view_distance, tuple(region.data.view_rotation), tuple(region.data.view_location))

    def inspect_level(pixels, expected, tag, parent_boxes=()):
        rows=visual_rows(expected)
        wanted=[r['label'] for r in rows if r['kind']!='separator']
        expected_height=sum(6 if r['kind']=='separator' else 24 for r in rows)*scale
        all_columns=columns(pixels,minimum_width=80,minimum_height=42 if expected_height>40*scale else 18)
        if expected_height<=40*scale:
            all_columns=[r for r in all_columns if abs(r[3]-r[1]-expected_height)<=2*scale]
        observed=[]
        observed_columns=[]
        for rect in all_columns:
            if any(all(abs(a-b)<3*scale for a,b in zip(rect,p)) for p in parent_boxes):
                continue
            found=rendered_rows(pixels,rect,wanted)
            if found:
                observed_columns.append(rect)
                observed.extend((label,x,y,score,rect) for label,x,y,score in found)
        check(tuple(n[0] for n in observed)==tuple(wanted),
              tag+' rendered sequence mismatch '+repr([n[0] for n in observed]))
        # Measure all physical column heights. Named divider is a full 24px
        # non-action heading; plain separator is 6px. Options never add a row.
        expected_height=sum(6 if r['kind']=='separator' else 24 for r in rows)*scale
        actual_height=sum(r[3]-r[1] for r in observed_columns)
        check(abs(actual_height-expected_height)<=2*scale*len(observed_columns),
              tag+' separator/title/no-paging height '+repr((actual_height,expected_height,observed_columns)))
        visible_rows=[r for r in rows if r['kind']!='separator']
        for row,hit in zip(visible_rows,observed):
            if not row['options']:
                continue
            _,_,cy,_,rect=hit
            # Independently observed column edge bounds the right 24px Options
            # cell. Require real two-dimensional gear ink separate from label.
            x0,y0,x1,y1=rect
            ink=pixels[max(0,int(cy-9*scale)):int(cy+9*scale),
                                  int(x1-21*scale):int(x1-3*scale),1]>.18
            yy,xx=np.nonzero(ink)
            if len(visible_rows)==1 and len(xx)<12*scale*scale:
                # A one-row menu renders its independently backed Options cell
                # just outside the measured main button, unlike a tall list.
                ink=pixels[max(0,int(cy-9*scale)):int(cy+9*scale),int(x1+3*scale):int(x1+21*scale),1]>.18
                yy,xx=np.nonzero(ink)
            check(len(xx)>=12*scale*scale and np.ptp(xx)>=6*scale and np.ptp(yy)>=6*scale,
                  tag+' missing independent Options gear for '+row['label'])
        reports.append({'tag':tag,'sequence':[n[0] for n in observed],
                        'columns':observed_columns,'actual_height':actual_height,
                        'expected_height':expected_height,'option_owners':[r['label'] for r in rows if r['options']]})
        print('MAYA_HIERARCHY_LEVEL',tag,reports[-1],flush=True)
        return observed,observed_columns

    def cancel():
        event('ESC');event('ESC','RELEASE');event('LEFTMOUSE','RELEASE');event('SPACE','RELEASE')
        yield from settle(6)
        check(not list(win.modal_operators),'hierarchy cancel retained modal ownership')

    # Display first is an independent negative oracle against the retired flat
    # layout. The other 21 roots are opened through their real Space row titles.
    order=[('common',references['common'][5])]
    order += [(group,node) for group,items in references.items() for node in items
              if not(group=='common' and node['label']=='Display')]
    for group,expected in order:
        row_group='pane' if group=='current_pane' else group
        with override():
            hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
                'style':'rows','rows':[row_group],'transparency':0,
                'appearance':{'theme_background':True,'brightness':0,'text':[255,255,255],
                              'placeholder':[160,160,160]}}})
        before=state()
        origin[:]=[region.x+region.width/2,region.y+region.height/2]
        event('MOUSEMOVE','NOTHING',origin);event('SPACE');yield from settle(9)
        tag='hierarchy-'+group+'-'+expected['label'].replace(' ','-').lower()
        try:
            primary=capture(tag+'-title')
            label=locate(primary,(0,int(origin[1]-180*scale),win.width,int(origin[1]+180*scale)),expected['label'])[0]
            event('MOUSEMOVE','NOTHING',((label[0]+label[2])/2,(label[1]+label[3])/2))
            event('LEFTMOUSE');yield from settle(8)
            pixels=capture(tag+'-level')
            observed,boxes=inspect_level(pixels,expected,tag)
            check(state()==before,tag+' open mutated scene/Recent/view')
            if group=='common' and expected['label']=='Display':
                hit=next(n for n in observed if n[0]=='Polygons')
                event('MOUSEMOVE','NOTHING',(hit[1],hit[2]));yield from settle(10)
                child=next(n for n in expected['children'] if n.get('label')=='Polygons')
                inspect_level(capture(tag+'-polygons'),child,tag+'-polygons',boxes)
                check(state()==before,'nested Polygons open executed a leaf')
        except AssertionError as error:
            failures.append({'tag':tag,'error':str(error)})
            print('MAYA_HIERARCHY_FAILURE',failures[-1],flush=True)
        finally:
            yield from cancel()
        check(state()==before,tag+' cancel mutated scene/Recent/view')
    (artifacts/'maya-hierarchy-observations.json').write_text(
        json.dumps({'observations':reports,'failures':failures},indent=2),encoding='utf-8')
    check(not failures,'Maya hierarchy acceptance failed: '+repr(failures))
    print('AXISMELD_MAYA_HIERARCHY_EVENTS_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps)
        return .025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

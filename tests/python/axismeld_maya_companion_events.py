# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real-input acceptance of Maya companion inventory, grouping and options."""
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

    def companion_rect(pixels, exclude=None):
            # Actual long colored row spans establish bounds; no list-layout constants
            # or expected coordinates enter this measurement. Text-sized holes close,
            # while the established radial inner gaps keep radial buttons separate.
            rgb = pixels[:, :, :3]
            colored = ((rgb[:, :, 0] > .3) & (rgb[:, :, 2] > .25)
                       & (np.minimum(rgb[:, :, 0], rgb[:, :, 2]) > 2.2*rgb[:, :, 1]))
            if exclude is not None:
                xa,ya,xb,yb = map(int,exclude)
                colored[max(0,ya-3):yb+3,max(0,xa-3):xb+3] = False
            minimum_width = (100 if exclude is not None else 150)*scale
            groups = {}
            for y in range(region.y+3, region.y+region.height-3):
                xs = np.flatnonzero(colored[y, region.x+2:region.x+region.width-2])+region.x+2
                if len(xs) < minimum_width-10*scale:
                    continue
                cuts = np.flatnonzero(np.diff(xs) > 28*scale)+1
                for span in np.split(xs, cuts):
                    if len(span) and span[-1]-span[0] > minimum_width:
                        key = (round(int(span[0])/(4*scale)), round(int(span[-1])/(4*scale)))
                        groups.setdefault(key, []).append((int(span[0]), int(span[-1]), y))
            candidates = []
            for rows in groups.values():
                ys = [row[2] for row in rows]
                if max(ys)-min(ys) > 58*scale and len(ys) > 25*scale:
                    candidates.append((min(row[0] for row in rows), min(ys),
                                       max(row[1] for row in rows)+1, max(ys)+1))
            check(candidates, 'no independently observed companion rectangle')
            return max(candidates, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))

    templates={}
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

    def radial_rectangles(pixels, expected=None):
        rgb=pixels[:,:,:3]
        colored=((rgb[:,:,0]>.3)&(rgb[:,:,2]>.25)&(np.minimum(rgb[:,:,0],rgb[:,:,2])>2.2*rgb[:,:,1]))
        groups={}
        for yy in range(max(region.y,int(origin[1]-86*scale)),min(region.y+region.height,int(origin[1]+86*scale))):
            xs=np.flatnonzero(colored[yy,region.x:region.x+region.width])+region.x
            for span in np.split(xs,np.flatnonzero(np.diff(xs)>3*scale)+1):
                if len(span) and span[-1]-span[0]>=60*scale:
                    key=(round(int(span[0])/(4*scale)),round(int(span[-1])/(4*scale)))
                    groups.setdefault(key,[]).append((int(span[0]),int(span[-1]),yy))
        found={}
        # Views deliberately has equal-width buttons in multiple rows. Equal
        # x-bounds do not make them one tall rectangle: separate actual y runs.
        clusters=[]
        for same_x_rows in groups.values():
            current=[]
            for row in same_x_rows:
                if current and row[2]-current[-1][2]>16*scale:
                    clusters.append(current)
                    current=[]
                current.append(row)
            if current:
                clusters.append(current)
        for rows in clusters:
            y0,y1=min(r[2] for r in rows),max(r[2] for r in rows)
            if not 13*scale<=y1-y0<=27*scale:
                continue
            x0,x1=min(r[0] for r in rows),max(r[1] for r in rows)
            dx,dy=(x0+x1)/2-origin[0],(y0+y1)/2-origin[1]
            direction=('N' if dy>16*scale else 'S' if dy < -16*scale else '')
            direction+=('E' if dx>20*scale else 'W' if dx < -20*scale else '')
            if direction:
                rect=(x0,y0,x1,y1)
                if direction not in found or (x1-x0)*(y1-y0)>(found[direction][2]-found[direction][0])*(found[direction][3]-found[direction][1]):
                    found[direction]=rect
        check(set(found)==(set(expected) if expected is not None else {'N','NE','E','SE','S','SW','W','NW'}),
              'actual screenshot did not expose all eight radial button rectangles: '+repr(found))
        return found

    glyph_template=template

    def rendered_rows(pixels, rect, labels):
        x0, y0, x1, y1 = map(int, rect)
        # Exclude independent Options/arrow cell. Left margin is only for
        # discarding the native backdrop border, not prescribing text origin.
        ink = foreground(pixels[y0:y1, x0+4:x1-int(26*scale)])
        # Keep thin descender rows (e.g. 2x Pipe's p). Three-pixel occupancy
        # cut away five real glyph rows and falsely resembled Prism.
        occupied = np.flatnonzero(np.sum(ink, axis=1) >= scale)
        bands = np.split(occupied, np.flatnonzero(np.diff(occupied)>2*scale)+1)
        matches = []
        for band in bands:
            if len(band) < 3*scale:
                continue
            low, high = int(band[0]), int(band[-1])+1
            sample = ink[low:high]
            ys, xs = np.nonzero(sample)
            if not len(xs):
                continue
            sample = sample[:, xs.min():xs.max()+1]
            samples = [sample]
            # Independently match the full BLF label after zero/one/two observed
            # icon slots. Semantic icons are 16px in a 20px slot; checkbox/radio
            # adds another slot. Neither icon is part of the label template.
            columns = np.flatnonzero(np.any(sample, axis=0))
            for text_start in label_prefix_starts(columns, scale)[1:]:
                suffix = sample[:,text_start:]
                sy,sx = np.nonzero(suffix)
                if len(sx):
                    samples.append(suffix[sy.min():sy.max()+1,sx.min():sx.max()+1])
            scores = []
            for label in labels:
                target = glyph_template(label)
                best = 0
                for candidate in samples:
                    if abs(target.shape[1]-candidate.shape[1]) > 6*scale:
                        continue
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            yy0, xx0 = max(0,dy), max(0,dx)
                            ty0, tx0 = max(0,-dy), max(0,-dx)
                            hh = min(candidate.shape[0]-yy0, target.shape[0]-ty0)
                            ww = min(candidate.shape[1]-xx0, target.shape[1]-tx0)
                            if hh <= 0 or ww <= 0:
                                continue
                            overlap = np.count_nonzero(candidate[yy0:yy0+hh,xx0:xx0+ww]
                                                       & target[ty0:ty0+hh,tx0:tx0+ww])
                            best = max(best, 2*overlap/(np.count_nonzero(candidate)+np.count_nonzero(target)))
                scores.append((best,label))
            if scores:
                score,label = max(scores)
                if score >= .58:
                    matches.append((label, (x0+x1)/2, y0+(low+high)/2, score))
        return sorted(matches, key=lambda item: -item[2])

    def start(shift=True,point=None):
        if point is not None:
            origin[:]=point
        event('MOUSEMOVE','NOTHING',origin)
        yield from settle(4)
        if shift:
            event('LEFT_SHIFT',shift=True)
        event('RIGHTMOUSE',shift=shift)
        yield from settle(9)
        check([op.bl_idname for op in win.modal_operators].count('VIEW3D_OT_axismeld_hotbox')==1,
              'public Shift+RMB must open exactly one native hotbox')

    def cancel():
        event('MOUSEMOVE','NOTHING',origin,shift=True)
        yield from settle(3)
        event('RIGHTMOUSE','RELEASE',shift=True)
        event('LEFT_SHIFT','RELEASE')
        yield from settle(6)
        check(not list(win.modal_operators),'original press cancellation retained modal ownership')

    # Capture the existing Object companion before asserting new CREATE behavior.
    # Both gestures use the old public API, before importing any new data module.
    yield from start()
    capture('object-old-separator-baseline')
    yield from cancel()
    with override():
        for obj in tuple(bpy.context.scene.objects):
            bpy.data.objects.remove(obj,do_unlink=True)
    yield from settle(7)
    yield from start()
    pixels=capture('create-companion-first')
    try:
        rect=companion_rect(pixels)
    except AssertionError:
        raise AssertionError('CREATE Shift+RMB lacks the required simultaneous Maya 16-row companion list') from None
    print('CREATE_COMPANION_RECT',rect,flush=True)
    yield from cancel()
    from axismeld import hotbox_runtime
    object_labels=('Offset Edge Loop Tool','Smooth','Unsmooth','Subdiv Proxy','Crease Tool',
                   'Project Curve on mesh','Split mesh with projected curve','Mirror','Mapping',
                   'Triangulate','Quadrangulate','Reduce','Remesh','Retopologize','Transfer Vertex Order',
                   'Separate','Combine','Booleans','Cleanup...','Connect Tool','Quad Draw Tool','Polygon Display')
    create_labels=('Platonic Solid','Pyramid','Prism','Pipe','Helix','Gear','Soccer Ball',
                   'Super Ellipse','Spherical Harmonics','Ultra Shape','Type','SVG','Quad Draw Tool',
                   'Interactive Creation','Exit On Completion','Polygon Display All')
    separators={
        'object':{'Crease Tool','Split mesh with projected curve','Mapping','Retopologize',
                  'Transfer Vertex Order','Booleans','Quad Draw Tool'},
        'create':{'Soccer Ball','Quad Draw Tool','Exit On Completion'}}
    create_options=set(create_labels[:10])|{'Quad Draw Tool'}

    def state():
        return (bpy.context.mode,bpy.context.active_object.name if bpy.context.active_object else None,
                tuple(sorted((o.name,o.type,o.select_get(),len(o.modifiers),
                              len(o.data.vertices) if o.type=='MESH' else 0,
                              len(o.data.polygons) if o.type=='MESH' else 0)
                             for o in bpy.context.scene.objects)),
                tuple(hotbox_runtime.recent.items()))

    def seed(domain):
        with override():
            if bpy.context.mode!='OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for obj in tuple(bpy.context.scene.objects):
                bpy.data.objects.remove(obj,do_unlink=True)
            if domain=='object':
                bpy.ops.mesh.primitive_cube_add()
        return state()

    def inventory(domain,tag):
        labels=object_labels if domain=='object' else create_labels
        seen=set();edges=set();separator_points=[];last=None;stalls=0
        arrow_samples={}
        for page in range(40):
            picture=capture(tag+'-'+str(page))
            rect=companion_rect(picture)
            rows=rendered_rows(picture,rect,labels)
            check(rows,'no complete expected labels recognized in actual '+domain+' list')
            order=[labels.index(row[0]) for row in rows]
            check(order==sorted(set(order)),domain+' rendered rows duplicate or out of Maya order')
            seen.update(row[0] for row in rows)
            for previous,current in zip(rows,rows[1:]):
                if labels.index(current[0])!=labels.index(previous[0])+1:
                    continue
                delta=(previous[2]-current[2])/scale
                expected=30 if previous[0] in separators[domain] else 24
                check(abs(delta-expected)<=2,
                      domain+' actual row/separator pitch incorrect: '+repr((previous[0],current[0],delta,expected)))
                edges.add(previous[0])
                if expected==30:
                    separator_points.append(((rect[0]+rect[2])/2,(previous[2]+current[2])/2))
            if domain=='object':
                for row in rows:
                    if row[0] in {'Mapping','Booleans','Polygon Display'}:
                        cy=row[2]
                        # Actual right-edge glyph pixels, independent of catalog
                        # fields. These rows interrupt an adjacent Options column;
                        # a union background used to paint over the first two.
                        slot=foreground(picture[int(cy-8*scale):int(cy+8*scale),
                                                int(rect[2]-22*scale):int(rect[2]-2*scale)])
                        arrow_samples[row[0]]=int(np.count_nonzero(slot))
                        print('MAYA_SUBMENU_ARROW_PIXELS',tag,row[0],arrow_samples[row[0]],flush=True)
            if domain=='create':
                for row in rows:
                    cy=row[2]
                    slot=picture[int(cy-9*scale):int(cy+9*scale),
                                 int(rect[2]-24*scale):int(rect[2]-2*scale),1]>.18
                    yy,xx=np.nonzero(slot)
                    gear=bool(len(xx)>8*scale*scale and xx.max()-xx.min()>=8*scale)
                    if row[0] in create_options:
                        check(gear,'missing independent Options gear in '+row[0])
                    elif row[0] in {'Type','SVG','Interactive Creation','Exit On Completion'}:
                        check(not gear,'unexpected Options gear in '+row[0])
            if domain=='create':
                verify_workflow(picture,rect,rows)
            print('MAYA_ROWS',tag,page,[(r[0],round(r[2],2)) for r in rows],flush=True)
            if seen==set(labels) and separators[domain]<=edges:
                if domain=='object':
                    check(set(arrow_samples)=={'Mapping','Booleans','Polygon Display'},
                          'not every actual submenu arrow row was observed')
                    check(all(amount>=5*scale*scale for amount in arrow_samples.values()),
                          'actual submenu arrow overwritten beside Options column: '+repr(arrow_samples))
                return rect,rows,separator_points
            signature=tuple((r[0],round(r[2])) for r in rows)
            stalls=stalls+1 if signature==last else 0;last=signature
            check(stalls<3,'bounded real paging stalled before all Maya entries were observed')
            event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),shift=True)
            event('WHEELDOWNMOUSE',shift=True)
            yield from settle(5)
        raise AssertionError('not all Maya '+domain+' rows/separators reached')

    def find_row(domain,label,tag):
        labels=object_labels if domain=='object' else create_labels
        for page in range(40):
            picture=capture(tag+'-'+str(page));rect=companion_rect(picture)
            for row in rendered_rows(picture,rect,labels):
                if row[0]==label:
                    return picture,rect,(row[1],row[2])
            event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),shift=True)
            event('WHEELDOWNMOUSE',shift=True)
            yield from settle(4)
        raise AssertionError('actual menu label unreachable: '+label)

    def verify_workflow(picture,rect,rows):
        indexed={row[0]:row for row in rows}
        if not {'Interactive Creation','Exit On Completion'}<=indexed.keys():
            return
        masks=[]
        for label in ('Interactive Creation','Exit On Completion'):
            text,_=locate(picture,rect,label)
            x,y,x1,y1=text;cy=(y+y1)/2
            mask=picture[int(cy-8*scale):int(cy+8*scale),int(x-44*scale):int(x-23*scale),1]>.18
            check(np.count_nonzero(mask)>8*scale*scale,'disabled workflow checkbox missing: '+label)
            masks.append(mask)
        check(masks[0].shape==masks[1].shape and not np.array_equal(masks[0],masks[1]),
              'Interactive Creation and Exit On Completion must display different unchecked/checked states')
        check(np.count_nonzero(masks[1])>np.count_nonzero(masks[0]),
              'Exit On Completion must show the checked glyph, not reversed workflow states')
        print('WORKFLOW_CHECKBOX_PIXELS',scale,[int(np.count_nonzero(m)) for m in masks],flush=True)

    def geometry_reference(tag):
        with override():
            hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
                'style':'center','rows':[],'transparency':0,
                'appearance':{'theme_background':True,'brightness':0}}})
        event('MOUSEMOVE','NOTHING',origin)
        event('SPACE');yield from settle(12)
        event('LEFTMOUSE');yield from settle(7)
        reference=radial_rectangles(capture(tag+'-views'),{'N','E','SE','S','SW','W','NW'})
        event('LEFTMOUSE','RELEASE');event('SPACE','RELEASE')
        yield from settle(6)
        check(not list(win.modal_operators),'Views reference retained ownership')
        return reference

    def compare_edges(actual,reference,tag):
        observed=[]
        for left,right in (('NW','NE'),('W','E'),('SW','SE')):
            a=actual[right][0]-actual[left][2]-1
            rl,rr=(left,right) if right in reference else ('SW','SE')
            r=reference[rr][0]-reference[rl][2]-1
            check(abs(a-r)<=3*scale,'Options changed actual Views inner clearance: '+repr((tag,left,a,r)))
            observed.append((a,r))
        print('MAYA_ACTUAL_INNER_EDGES',tag,scale,observed,flush=True)

    for requested_scale in (1.0,2.0):
        bpy.context.preferences.view.ui_scale=requested_scale
        yield from settle(9)
        scale=bpy.context.preferences.system.ui_scale
        region=next(r for r in area.regions if r.type=='WINDOW')
        midpoint=(region.x+region.width/2,region.y+region.height/2)
        origin[:]=midpoint
        reference=yield from geometry_reference('maya-'+str(requested_scale))
        for domain in ('create','object'):
            before=seed(domain)
            yield from settle(7)
            yield from start(point=midpoint)
            actual=radial_rectangles(capture('maya-'+domain+'-ring-'+str(requested_scale)))
            compare_edges(actual,reference,domain)
            rect,rows,points=yield from inventory(domain,'maya-'+domain+'-'+str(requested_scale))
            check(len(points)>=len(separators[domain]),'not all fine separator groups were visually sampled')
            yield from cancel()
            check(state()==before,'inventory/paging changed scene/Recent')

        # New radial Options are all explicit disabled placeholders. Observe
        # their actual gear pixels and release a representative tool's gear,
        # proving it does not fall through to the live main action.
        before=seed('object')
        yield from settle(6);yield from start(point=midpoint)
        picture=capture('maya-object-radial-options-'+str(requested_scale))
        text,_=locate(picture,(region.x,origin[1]-90*scale,region.x+region.width,origin[1]+90*scale),'Multi-Cut')
        # Solid background just above glyphs exposes the actual button right edge.
        row_y=int(text[3]+3*scale)
        rgb=picture[row_y,:,:3]
        colored=(rgb[:,0]>.3)&(rgb[:,2]>.25)&(np.minimum(rgb[:,0],rgb[:,2])>2.2*rgb[:,1])
        xs=np.flatnonzero(colored)
        spans=np.split(xs,np.flatnonzero(np.diff(xs)>3*scale)+1)
        candidates=[span for span in spans if len(span) and span[0]<=(text[0]+text[2])/2<=span[-1]]
        check(candidates,'cannot observe Multi-Cut button background edge')
        right=int(max(candidates,key=len)[-1])+1
        cy=(text[1]+text[3])/2
        gear=picture[int(cy-9*scale):int(cy+9*scale),int(right-23*scale):int(right-2*scale),1]>.18
        check(np.count_nonzero(gear)>8*scale*scale,'Multi-Cut radial Options gear not visible')
        event('MOUSEMOVE','NOTHING',(right-12*scale,cy),shift=True)
        yield from settle(4)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        yield from settle(7)
        check(state()==before and not list(win.modal_operators),'disabled radial Options executed main Knife tool')

        before=seed('create')
        yield from settle(6);yield from start(point=midpoint)
        picture,rect,point=yield from find_row('create','Platonic Solid','maya-create-disabled-options-'+str(requested_scale))
        event('MOUSEMOVE','NOTHING',(rect[2]-12*scale,point[1]),shift=True)
        yield from settle(4)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        yield from settle(7)
        check(state()==before and not list(win.modal_operators),'disabled creation Options created main primitive')

        # A separator is actual noninteractive list area, not a radial fallthrough.
        before=seed('create')
        yield from settle(6);yield from start(point=midpoint)
        _,rect,upper=yield from find_row('create','Soccer Ball','maya-separator-hit-'+str(requested_scale))
        # The visible Soccer/Super Ellipse pair is required before selecting their
        # independently measured midpoint, six logical pixels of separator.
        for pair_page in range(5):
            picture=capture('maya-separator-hit-pair-'+str(requested_scale)+'-'+str(pair_page))
            rect=companion_rect(picture)
            rows={r[0]:r for r in rendered_rows(picture,rect,create_labels)}
            if {'Soccer Ball','Super Ellipse'}<=rows.keys():
                break
            event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),shift=True)
            event('WHEELDOWNMOUSE',shift=True);yield from settle(5)
        check({'Soccer Ball','Super Ellipse'}<=rows.keys(),'separator hit fixture must expose both neighboring labels')
        point=((rect[0]+rect[2])/2,(rows['Soccer Ball'][2]+rows['Super Ellipse'][2])/2)
        event('MOUSEMOVE','NOTHING',point,shift=True);yield from settle(4)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        yield from settle(7)
        check(state()==before and not list(win.modal_operators),'separator release passed through to creation/radial')

        # Four corners exercise native clamping rather than synthesized layout.
        for domain in ('object','create'):
            before=seed(domain);yield from settle(5)
            # WINDOW overlaps real Header/Tool Header surfaces at the top.
            # A press there belongs to that editor region, not viewport input.
            # Establish visible viewport corners from actual UI region edges.
            x0,y0,x1,y1=region.x,region.y,region.x+region.width,region.y+region.height
            for overlay in area.regions:
                if overlay.type in {'HEADER','TOOL_HEADER'} and overlay.width>1 and overlay.height>1:
                    if y0<overlay.y<y1 and overlay.y>region.y+region.height/2:
                        y1=min(y1,overlay.y)
                    elif y0<overlay.y+overlay.height<y1 and overlay.y<region.y+region.height/2:
                        y0=max(y0,overlay.y+overlay.height)
            print('MAYA_VISIBLE_CORNERS',scale,(x0,y0,x1,y1),
                  [(r.type,r.x,r.y,r.width,r.height) for r in area.regions if r.type in {'HEADER','TOOL_HEADER'}],flush=True)
            for xside,yside in ((0,0),(0,1),(1,0),(1,1)):
                point=(x1-4 if xside else x0+4,y1-4 if yside else y0+4)
                yield from start(point=point)
                rect=companion_rect(capture('maya-corner-'+domain+'-'+str(requested_scale)+'-'+str(xside)+str(yside)))
                check(region.x<=rect[0]<rect[2]<=region.x+region.width and
                      region.y<=rect[1]<rect[3]<=region.y+region.height,'actual companion escapes viewport')
                yield from cancel()
                check(state()==before,'clamped original-press cancel changed scene')
        origin[:]=midpoint

    bpy.context.preferences.view.ui_scale=1.0
    yield from settle(8)
    scale=bpy.context.preferences.system.ui_scale
    region=next(r for r in area.regions if r.type=='WINDOW')
    midpoint=(region.x+region.width/2,region.y+region.height/2);origin[:]=midpoint

    # Real new primitive/text main commands, each with one actual Undo boundary.
    for label,kind in (('Platonic Solid','MESH'),('Pyramid','MESH'),('Prism','MESH'),('Type','FONT')):
        before=seed('create');yield from settle(5)
        with override():bpy.ops.ed.undo_push(message='Maya creation baseline '+label)
        yield from start(point=midpoint)
        picture,rect,point=yield from find_row('create',label,'maya-create-main-'+label.replace(' ','-'))
        event('MOUSEMOVE','NOTHING',point,shift=True);yield from settle(3)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        yield from settle(7)
        obj=bpy.context.active_object
        check(len(bpy.context.scene.objects)==1 and obj and obj.type==kind,
              label+' did not create exactly one corresponding native object')
        if label=='Pyramid':
            check((len(obj.data.vertices),len(obj.data.polygons))==(5,5),'Pyramid must be square-base 5-vertex mesh')
        elif label=='Prism':
            check((len(obj.data.vertices),len(obj.data.polygons))==(6,5),'Prism must be triangular 6-vertex prism')
        elif label=='Platonic Solid':
            check(len(obj.data.vertices)>=12 and all(len(face.vertices)==3 for face in obj.data.polygons),
                  'Platonic Solid adaptation must be a real triangulated native Icosphere')
        else:
            check(obj.data.body=='Text','Type must create native editable Text content')
        with override():bpy.ops.ed.undo()
        yield from settle(7)
        check(state()[:3]==before[:3],label+' single Undo did not restore empty Object scene')
        print('PASS actual Maya creation main action and single Undo',label,flush=True)

    # All four Maya Soft/Hard entries stay in their real ordinary submenu.
    before=seed('object');yield from settle(5);yield from start(point=midpoint)
    picture=capture('maya-normals-parent')
    text,_=locate(picture,(region.x,origin[1]-90*scale,region.x+region.width,origin[1]+90*scale),'Soften/Harden Edges')
    event('MOUSEMOVE','NOTHING',((text[0]+text[2])/2,(text[1]+text[3])/2),shift=True)
    yield from settle(8)
    picture=capture('maya-normals-child')
    parent=companion_rect(picture)
    child=companion_rect(picture,exclude=parent)
    # The first child row touches its radial parent. Its background can merge
    # at that y, so identify all four texts within the independently observed
    # child x-column rather than dropping the touching first row.
    child=(child[0],region.y,child[2],region.y+region.height)
    for label in ('Toggle Soft Edge Display','Harden Edge','Soften/Harden Edges','Soften Edge'):
        locate(picture,child,label)
    event('ESC',shift=True);event('ESC','RELEASE',shift=True)
    event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
    yield from settle(7)
    check(state()==before and not list(win.modal_operators),'Soften/Harden grey directory cancelled with mutation')

    # Workflow placeholder release is never a global-preference toggle.
    for label in ('Interactive Creation','Exit On Completion'):
        before=seed('create');yield from settle(5);yield from start(point=midpoint)
        preference=bpy.context.preferences.edit.use_enter_edit_mode
        picture,rect,point=yield from find_row('create',label,'maya-workflow-'+label.replace(' ','-'))
        event('MOUSEMOVE','NOTHING',point,shift=True);yield from settle(4)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        yield from settle(7)
        check(state()==before and bpy.context.preferences.edit.use_enter_edit_mode==preference,
              'disabled workflow mutated scene or global creation preference')

    # Only the current viewport's existing Backface Culling action is live.
    before=seed('create');yield from settle(5);yield from start(point=midpoint)
    picture,rect,point=yield from find_row('create','Polygon Display All','maya-display-parent')
    event('MOUSEMOVE','NOTHING',point,shift=True);yield from settle(7)
    picture=capture('maya-display-child');child=companion_rect(picture,exclude=rect)
    prior_culling=area.spaces.active.shading.show_backface_culling
    text,_=locate(picture,child,'Backface Culling off for All Polys' if prior_culling else 'Backface Culling on for All Polys')
    prior_culling=area.spaces.active.shading.show_backface_culling
    event('MOUSEMOVE','NOTHING',((text[0]+text[2])/2,(text[1]+text[3])/2),shift=True)
    yield from settle(3);event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
    yield from settle(7)
    check(area.spaces.active.shading.show_backface_culling!=prior_culling and state()[:3]==before[:3],
          'Polygon Display All Backface Culling did not toggle only viewport shading')
    area.spaces.active.shading.show_backface_culling=prior_culling

    # Repeated owned gestures and every cancellation path remain scene read-only.
    for domain in ('create','object'):
        before=seed(domain);yield from settle(5)
        for index,reason in enumerate(('center','center','center','escape','shift-first','focus')):
            point=(midpoint[0]+(index%3-1)*60,midpoint[1]+(index%2)*30)
            yield from start(point=point)
            if reason=='center':
                yield from cancel()
            else:
                if reason=='escape':
                    event('ESC',shift=True);event('ESC','RELEASE',shift=True)
                elif reason=='shift-first':
                    event('LEFT_SHIFT','RELEASE')
                else:
                    event('WINDOW_DEACTIVATE','NOTHING')
                event('RIGHTMOUSE','RELEASE',shift=reason!='shift-first')
                if reason!='shift-first':event('LEFT_SHIFT','RELEASE')
                yield from settle(7)
            check(state()==before and not list(win.modal_operators),domain+' '+reason+' changed state or retained ownership')
        print('PASS repeated Maya companion gestures and cancellation',domain,flush=True)

    # Single/quad evidence uses the same real rendered Views inner edges.
    for requested_scale in (1.0,2.0):
        bpy.context.preferences.view.ui_scale=requested_scale;yield from settle(8)
        scale=bpy.context.preferences.system.ui_scale
        region=next(r for r in area.regions if r.type=='WINDOW')
        with override():bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        region=min((r for r in area.regions if r.type=='WINDOW'),key=lambda r:(r.y,r.x))
        origin[:]=[region.x+region.width/2,region.y+region.height/2]
        reference=yield from geometry_reference('maya-quad-'+str(requested_scale))
        for domain in ('create','object'):
            before=seed(domain);yield from settle(5)
            if requested_scale==1.0:
                yield from start()
                picture=capture('maya-quad-'+domain+'-'+str(requested_scale))
                compare_edges(radial_rectangles(picture),reference,'quad '+domain)
                rect=companion_rect(picture)
                check(region.x<=rect[0]<rect[2]<=region.x+region.width and
                      region.y<=rect[1]<rect[3]<=region.y+region.height,'quad companion escaped actual viewport')
                yield from cancel()
            else:
                check(region.height/scale<250,'short-quad unsupported fixture dimensions changed')
                event('MOUSEMOVE','NOTHING',origin)
                event('LEFT_SHIFT',shift=True);event('RIGHTMOUSE',shift=True)
                yield from settle(8)
                capture('maya-short-quad-'+domain)
                check(not list(win.modal_operators),'short quad must safely reject a ring plus minimum companion that cannot fit')
                event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
                yield from settle(6)
            check(state()==before,'quad open/cancel changed scene or Recent')
        yield from geometry_reference('maya-quad-next-input-'+str(requested_scale))
        with override():bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        region=next(r for r in area.regions if r.type=='WINDOW')

    print('AXISMELD_MAYA_COMPANION_UI_TEST_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps)
        return .025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
    return None
bpy.app.timers.register(tick,first_interval=1)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real-input acceptance of Maya companion inventory, grouping and options."""
import os
import json
from pathlib import Path
import sys
import traceback
import numpy as np
import imbuf
import blf
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles,observed_menu_rectangles,menu_background_mask
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
            for y in range(3,pixels.shape[0]-3):
                xs = np.flatnonzero(colored[y,2:pixels.shape[1]-2])+2
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

    def labelled_radial_rectangles(pixels, scale, expected_directions, matches):
        """Locate a direct Object/Create/component ring after its actual translation.

        Uses the diagnostic magenta theme shared by content GUI observers. It does
        not infer motion from companion count, height, column count or source press.
        """
        boxes=[r for r in observed_menu_rectangles(menu_background_mask(pixels),35*scale,13*scale)
               if r[3]-r[1]<=27*scale]
        if not boxes: raise AssertionError('No actual radial button backgrounds')
        # Native toolbar controls can share the diagnostic theme. Identify a full
        # directional constellation, rather than treating the highest colored box
        # in the entire window as its North button.
        candidates=[]
        for north in boxes:
            for south in boxes:
                ny=(north[1]+north[3])/2;sy=(south[1]+south[3])/2
                nx=(north[0]+north[2])/2;sx=(south[0]+south[2])/2
                if not 70*scale<ny-sy<180*scale or abs(nx-sx)>20*scale: continue
                cx=(nx+sx)/2;cy=(ny+sy)/2;found={};duplicate=False
                for rect in boxes:
                    rx=(rect[0]+rect[2])/2;ry=(rect[1]+rect[3])/2
                    if not sy<=ry<=ny or abs(rx-cx)>400*scale: continue
                    dx=rx-cx;dy=ry-cy
                    direction=('N' if dy>16*scale else 'S' if dy < -16*scale else '')
                    direction+=('E' if dx>20*scale else 'W' if dx < -20*scale else '')
                    if not direction or direction not in expected_directions or not matches(direction,rect): continue
                    if direction in found: duplicate=True;break
                    found[direction]=rect
                if not duplicate and set(found)==set(expected_directions):
                    candidates.append({'rects':found,'center':(cx,cy)})
        if len(candidates)!=1:
            raise AssertionError(f'Expected one complete observed radial constellation, got {candidates!r}; boxes={boxes!r}')
        return candidates[0]

    object_ring_labels={'N':'Target Weld Tool','NE':'Fill Holes','E':'Append to Polygon Tool',
                        'SE':'Soften/Harden Edges','S':'Extrude','SW':'Insert Edge Loop Tool',
                        'W':'Multi-Cut','NW':'Sculpt Tool'}
    create_ring_labels={'N':'Create Polygon Tool','NE':'Disc','E':'Sphere','SE':'Torus',
                        'S':'Cube','SW':'Cone','W':'Cylinder','NW':'Plane'}
    move_ring_labels={'N':'Symmetry','NE':'Component','E':'Snap','SE':'Keep Spacing',
                      'S':'Select','SW':'Axis','W':'World','NW':'Object'}

    def radial_rectangles(pixels, expected=None):
        if isinstance(expected,dict):
            def matches(direction,rect):
                glyph=template(expected[direction]);gh,gw=glyph.shape
                if rect[2]-rect[0]-4<gw or rect[3]-rect[1]-4<gh:return False
                return locate(pixels,rect,expected[direction],required=False) is not None
            observed=labelled_radial_rectangles(pixels,scale,set(expected),matches)['rects']
            cells=observed_menu_rectangles(menu_background_mask(pixels),10*scale,13*scale)
            for direction,rect in tuple(observed.items()):
                adjacent=[cell for cell in cells if 18*scale<=cell[2]-cell[0]<=27*scale
                          and 0<=cell[0]-rect[2]<=3*scale
                          and abs(cell[1]-rect[1])<=2*scale and abs(cell[3]-rect[3])<=2*scale]
                check(len(adjacent)<=1,'ambiguous observed Options cell '+repr(adjacent))
                if adjacent:observed[direction]=(rect[0],rect[1],adjacent[0][2],rect[3])
            return {direction:(r[0],r[1],r[2]-1,r[3]-1) for direction,r in observed.items()}

        center=origin
        if expected is None:
            center=observed_radial_rectangles(pixels,scale,{'N','NW','NE','W','E','SW','SE','S'})['center']
        rgb=pixels[:,:,:3]
        colored=((rgb[:,:,0]>.3)&(rgb[:,:,2]>.25)&(np.minimum(rgb[:,:,0],rgb[:,:,2])>2.2*rgb[:,:,1]))
        groups={}
        for yy in range(max(0,int(center[1]-86*scale)),min(pixels.shape[0],int(center[1]+86*scale))):
            xs=np.flatnonzero(colored[yy,:])
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
            dx,dy=(x0+x1)/2-center[0],(y0+y1)/2-center[1]
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

    def actual_columns(picture,labels):
        # A complete menu may end in a single 24px row in its own column.
        # Admit short background components only when a complete companion
        # caption is actually rendered there; toolbar/radial boxes are not
        # columns merely because they share the diagnostic background color.
        candidates=observed_menu_rectangles(menu_background_mask(picture),150*scale,13*scale)
        full_columns=[rect for rect in candidates if rect[3]-rect[1]>=58*scale]
        columns=[]
        for rect in candidates:
            if rect[3]-rect[1]>=58*scale:
                columns.append(rect)
                continue
            # A short final column belongs to the same complete popup: its
            # observed top and width must agree with a full sibling column.
            # Caption correlation alone can match a substring of a radial row.
            if not any(abs(rect[3]-other[3])<=2*scale and
                       abs((rect[2]-rect[0])-(other[2]-other[0]))<=2*scale
                       for other in full_columns):
                continue
            if not rendered_rows(picture,rect,labels):
                continue
            for label in labels:
                gh,gw=template(label).shape
                if rect[3]-rect[1]-3<gh or rect[2]-rect[0]-3<gw:
                    continue
                if locate(picture,rect,label,required=False) is not None:
                    columns.append(rect)
                    break
        return columns

    def inventory(domain,tag):
        labels=object_labels if domain=='object' else create_labels
        yield from settle(0)
        picture=capture(tag+'-full')
        columns=actual_columns(picture,labels)
        check(columns,'no actual complete columns')
        all_rows=[];separator_points=[];arrows={}
        for rect in columns:
            rows=rendered_rows(picture,rect,labels)
            check(rows,'empty actual Maya column')
            all_rows.extend(rows)
            for previous,current in zip(rows,rows[1:]):
                check(labels.index(current[0])==labels.index(previous[0])+1,'Maya column skipped/duplicated a row')
                delta=(previous[2]-current[2])/scale
                expected=30 if previous[0] in separators[domain] else 24
                check(abs(delta-expected)<=2,'actual24/6 row/separator pitch changed '+repr((previous[0],delta,expected)))
                if expected==30:separator_points.append(((rect[0]+rect[2])/2,(previous[2]+current[2])/2))
            for row in rows:
                cy=row[2]
                if domain=='object' and row[0] in {'Mapping','Booleans','Polygon Display'}:
                    slot=foreground(picture[int(cy-8*scale):int(cy+8*scale),int(rect[2]-22*scale):int(rect[2]-2*scale)])
                    arrows[row[0]]=int(np.count_nonzero(slot))
                    check(arrows[row[0]]>=5*scale*scale,'actual submenu arrow overwritten beside Options')
                if domain=='create':
                    slot=picture[int(cy-9*scale):int(cy+9*scale),int(rect[2]-24*scale):int(rect[2]-2*scale),1]>.18
                    yy,xx=np.nonzero(slot)
                    gear=bool(len(xx)>8*scale*scale and xx.max()-xx.min()>=8*scale)
                    if row[0] in create_options:check(gear,'missing independent Options gear '+row[0])
                    elif row[0] in {'Type','SVG','Interactive Creation','Exit On Completion'}:check(not gear,'unexpected Options gear '+row[0])
            if rows[-1][0] in separators[domain]:
                # A column break can follow the actual trailing6px separator.
                # Measure its retained band instead of demanding a next-row
                # baseline in a different column.
                tail=(rows[-1][2]-rect[1])/scale
                check(abs(tail-17)<=2,'column-boundary6px separator band missing '+repr(tail))
                separator_points.append(((rect[0]+rect[2])/2,rect[1]+3*scale))
            if domain=='create':verify_workflow(picture,rect,rows)
        check(tuple(row[0] for row in all_rows)==labels,'complete Maya order/multiplicity mismatch '+repr(all_rows))
        height=sum(rect[3]-rect[1] for rect in columns)/scale
        expected=len(labels)*24+len(separators[domain])*6
        check(abs(height-expected)<=2*len(columns),'actual complete columns lost6px separators '+repr((height,expected)))
        if domain=='object':check(set(arrows)=={'Mapping','Booleans','Polygon Display'},'missing actual submenu arrow')
        print('MAYA_FULL_ROWS',tag,columns,[row[0] for row in all_rows],arrows,flush=True)
        return columns[0],all_rows,separator_points

    def find_row(domain,label,tag):
        yield from settle(0)
        labels=object_labels if domain=='object' else create_labels
        picture=capture(tag+'-full')
        for rect in actual_columns(picture,labels):
            for row in rendered_rows(picture,rect,labels):
                if row[0]==label:return picture,rect,(row[1],row[2])
        raise AssertionError('actual full menu label missing: '+label)

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
            actual=radial_rectangles(capture('maya-'+domain+'-ring-'+str(requested_scale)),
                                     object_ring_labels if domain=='object' else create_ring_labels)
            compare_edges(actual,reference,domain)
            rect,rows,points=yield from inventory(domain,'maya-'+domain+'-'+str(requested_scale))
            check(len(points)>=len(separators[domain]),'not all fine separator groups were visually sampled')
            yield from cancel()
            check(state()==before,'complete inventory changed scene/Recent')

        # New radial Options are all explicit disabled placeholders. Observe
        # their actual gear pixels and release a representative tool's gear,
        # proving it does not fall through to the live main action.
        before=seed('object')
        yield from settle(6);yield from start(point=midpoint)
        picture=capture('maya-object-radial-options-'+str(requested_scale))
        text,_=locate(picture,(0,0,picture.shape[1],picture.shape[0]),'Multi-Cut')
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
        picture=capture('maya-separator-hit-'+str(requested_scale))
        observed_separators=[]
        for rect in actual_columns(picture,create_labels):
            rows=rendered_rows(picture,rect,create_labels)
            for upper,lower in zip(rows,rows[1:]):
                if upper[0] not in separators['create']:
                    continue
                check(create_labels.index(lower[0])==create_labels.index(upper[0])+1,
                      'separator neighbors must be consecutive complete labels')
                check(abs((upper[2]-lower[2])/scale-30)<=2,
                      'actual separator neighbors must preserve 24+6 pitch')
                observed_separators.append(((rect[0]+rect[2])/2,(upper[2]+lower[2])/2))
        check(observed_separators,'separator hit fixture must expose same-column neighboring labels')
        point=observed_separators[0]
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
                check(0<=rect[0]<rect[2]<=win.width and
                      0<=rect[1]<rect[3]<=win.height,'actual companion escapes whole-window surface')
                yield from cancel()
                check(state()==before,'clamped original-press cancel changed scene')
        origin[:]=midpoint

        # Snap's Relative Mode is one native companion row, never a fourth/S radial leaf.
        for cancel_target in ('relative-row','missing-south'):
            before=seed('object');yield from settle(5)
            event('MOUSEMOVE','NOTHING',origin);event('W');yield from settle(9)
            event('LEFTMOUSE');yield from settle(8)
            parent=radial_rectangles(capture('maya-snap-parent-'+str(scale)+'-'+cancel_target),move_ring_labels)
            snap=parent['E']
            event('MOUSEMOVE','NOTHING',((snap[0]+snap[2])/2,(snap[1]+snap[3])/2))
            yield from settle(9)
            picture=capture('maya-snap-child-'+str(scale)+'-'+cancel_target)
            boxes=[r for r in observed_menu_rectangles(menu_background_mask(picture),35*scale,13*scale)
                   if r[3]-r[1]<=27*scale]
            observed={}
            texts={}
            for label in ('Discrete Move','Vertex','Face Center','Relative Mode'):
                glyph=template(label);gh,gw=glyph.shape
                choices=[]
                for box in boxes:
                    if box[2]-box[0]-4<gw or box[3]-box[1]-4<gh:continue
                    match=locate(picture,box,label,required=False)
                    if match is not None:choices.append((box,match[0]))
                check(len(choices)==1,'Snap must expose one complete actual label '+repr((label,choices)))
                observed[label],texts[label]=choices[0]
            east=observed['Discrete Move'];sw=observed['Face Center'];se=observed['Vertex']
            relative=observed['Relative Mode']
            check(sw[2]<se[0] and abs(sw[1]-se[1])<=3*scale,'Snap SW/SE actual order or row changed')
            check(relative[3]<min(sw[1],se[1],east[1]),'Relative Mode must be below all three actual radial leaves')
            check(abs((relative[3]-relative[1])/scale-24)<=2,'Snap companion must be one complete24px row')
            text=texts['Relative Mode'];x,y,x1,y1=text;cy=(y+y1)/2
            checkbox=picture[int(cy-8*scale):int(cy+8*scale),int(x-44*scale):int(x-23*scale),1]>.18
            check(np.count_nonzero(checkbox)>8*scale*scale,'Relative Mode disabled checkbox is not visible')
            yy,xx=np.nonzero(checkbox);inset=int(3*scale)
            inside=checkbox[yy.min()+inset:yy.max()+1-inset,xx.min()+inset:xx.max()+1-inset]
            check(inside.size and np.mean(inside)<.15,'Relative Mode must render an empty checkbox interior')
            with override():resolved=json.loads(hotbox_runtime.snapshot(bpy.context))
            pending=list(resolved['menus']);nodes={}
            while pending:
                item=pending.pop();nodes[item['id']]=item;pending.extend(item['children'])
            row=nodes['tools.move.snap_menu.relative'];ring=nodes['tools.move.snap']
            check(row['kind']=='disabled' and not row['enabled'] and not row['command']
                  and row.get('indicator')=='checkbox' and row.get('checked') is False
                  and not row.get('direction'),'Relative Mode must be a readonly unchecked non-directional row')
            check({item.get('direction') for item in ring['children']}=={'E','SE','SW'},'Snap gained an incorrect S action')
            gap=((sw[2]+se[0])/2,(sw[1]+sw[3]+se[1]+se[3])/4)
            check(not any(r[0]<=gap[0]<r[2] and r[1]<=gap[1]<r[3] for r in boxes),
                  'Absent S sector contains an actual menu rectangle')
            settings=bpy.context.scene.tool_settings
            snap_state=(settings.use_snap,tuple(sorted(settings.snap_elements)))
            active_tool=bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode,create=False)
            tool_id=active_tool.idname if active_tool else None
            point=((relative[0]+relative[2])/2,(relative[1]+relative[3])/2) if cancel_target=='relative-row' else gap
            event('MOUSEMOVE','NOTHING',point);yield from settle(3)
            event('LEFTMOUSE','RELEASE');event('W','RELEASE');yield from settle(7)
            active_tool=bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode,create=False)
            check(state()==before and not list(win.modal_operators),'Snap cancellation changed scene/Recent or retained owner')
            check((settings.use_snap,tuple(sorted(settings.snap_elements)))==snap_state
                  and (active_tool.idname if active_tool else None)==tool_id,'Snap placeholder changed snapping/tool state')
            print('MAYA_SNAP_COMPANION',scale,cancel_target,observed,'checkbox_pixels',int(np.count_nonzero(checkbox)),flush=True)

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
    text,_=locate(picture,(0,0,picture.shape[1],picture.shape[0]),'Soften/Harden Edges')
    event('MOUSEMOVE','NOTHING',((text[0]+text[2])/2,(text[1]+text[3])/2),shift=True)
    yield from settle(8)
    picture=capture('maya-normals-child')
    parent=companion_rect(picture)
    child=companion_rect(picture,exclude=parent)
    # The first child row touches its radial parent. Its background can merge
    # at that y, so identify all four texts within the independently observed
    # child x-column rather than dropping the touching first row.
    child=(child[0],0,child[2],picture.shape[0])
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
            if requested_scale==2.0:
                check(region.height/scale<250,'short-quad fixture dimensions changed')
            yield from start()
            picture=capture('maya-quad-'+domain+'-'+str(requested_scale))
            compare_edges(radial_rectangles(picture,object_ring_labels if domain=='object' else create_ring_labels),reference,'quad '+domain)
            labels=object_labels if domain=='object' else create_labels
            columns=actual_columns(picture,labels)
            check(columns,'quad full menu must expose actual complete columns')
            check(all(0<=r[0]<r[2]<=win.width and 0<=r[1]<r[3]<=win.height for r in columns),
                  'quad companion escapes whole-window surface')
            if requested_scale==2.0:
                check(any(r[0]<region.x or r[2]>region.x+region.width or r[1]<region.y
                          or r[3]>region.y+region.height for r in columns),
                      'short quad must actually use the whole-window fallback')
            labels=object_labels if domain=='object' else create_labels
            check(tuple(row[0] for r in columns for row in rendered_rows(picture,r,labels))==labels,
                  'quad companion lost a complete row or changed order')
            yield from cancel()
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

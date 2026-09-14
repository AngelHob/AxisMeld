# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent real-input and screenshot acceptance for semantic icons."""
import os
from pathlib import Path
import sys
import traceback
import numpy as np
import imbuf
import blf
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles, observed_menu_rectangles, menu_background_mask

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
                    # A diagonal belongs between the observed N/S button edges.
                    # Native header controls can share both this theme and a similar
                    # glyph, but sit alongside N rather than inside the actual ring.
                    if len(direction)==2 and not south[3]<ry<north[1]: continue
                    if not direction or direction not in expected_directions or not matches(direction,rect): continue
                    if direction in found: duplicate=True;break
                    found[direction]=rect
                if not duplicate and set(found)==set(expected_directions):
                    candidates.append({'rects':found,'center':(cx,cy)})
        if len(candidates)!=1:
            raise AssertionError(f'Expected one complete observed radial constellation, got {candidates!r}; boxes={boxes!r}')
        return candidates[0]

    def radial_rectangles(pixels, expected=None):
        if isinstance(expected,dict) and 'NE' in expected:
            def matches(direction,rect):
                glyph=template(expected[direction]);gh,gw=glyph.shape
                if rect[2]-rect[0]-4<gw or rect[3]-rect[1]-4<gh:return False
                return locate(pixels,rect,expected[direction],required=False) is not None
            observed=labelled_radial_rectangles(pixels,scale,set(expected),matches)['rects']
            cells=observed_menu_rectangles(menu_background_mask(pixels),10*scale,13*scale)
            for d,r in tuple(observed.items()):
                adjacent=[c for c in cells if 18*scale<=c[2]-c[0]<=27*scale and 0<=c[0]-r[2]<=3*scale
                          and abs(c[1]-r[1])<=2*scale and abs(c[3]-r[3])<=2*scale]
                check(len(adjacent)<=1,'ambiguous actual Options cell '+repr(adjacent))
                if adjacent:observed[d]=(r[0],r[1],adjacent[0][2],r[3])
            return {d:(r[0],r[1],r[2]-1,r[3]-1) for d,r in observed.items()}
        center=origin
        if expected is None or len(expected)==8 or 'NE' in expected:
            directions=set(expected) if expected is not None else {'N','NW','NE','W','E','SW','SE','S'}
            center=observed_radial_rectangles(pixels,scale,directions)['center']
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
              'actual screenshot did not expose the expected visible radial button rectangles: '+repr(found))
        return found

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
        if ink.shape[0]<gh or ink.shape[1]<gw:
            if not required:
                return None
            check(False,'observed box cannot contain '+label)
        shape=(ink.shape[0]+gh-1,ink.shape[1]+gw-1)
        product=np.fft.rfft2(ink,s=shape)*np.fft.rfft2(glyph[::-1,::-1],s=shape)
        hits=np.fft.irfft2(product,s=shape)[gh-1:ink.shape[0],gw-1:ink.shape[1]]
        summed=np.pad(ink.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
        counts=summed[gh:,gw:]-summed[:-gh,gw:]-summed[gh:,:-gw]+summed[:-gh,:-gw]
        scores=2*hits/(counts+np.count_nonzero(glyph))
        # Border Edges is also a suffix of Texture Border Edges. Exclude the
        # independently matched longer label's actual glyph band, so the
        # full-label observer cannot report that suffix as a sibling row.
        if label == 'Border Edges':
            longer = locate(pixels, rect, 'Texture Border Edges', required=False)
            if longer:
                band = longer[0]
                low = max(0, band[1]-y0-gh+1)
                high = min(scores.shape[0], band[3]-y0)
                scores[low:high, :] = -1
        y,x=np.unravel_index(np.argmax(scores),scores.shape)
        score=float(scores[y,x])
        if not required and score<=.75:
            return None
        check(score>.75,'actual full label not independently identified: '+repr((label,score,rect)))
        return (x+x0,y+y0,x+x0+gw,y+y0+gh),score

    def semantic_icon(pixels,rect,label,state=False,disabled_state=False):
        # Semantic and state cells are independently observed on the left of
        # actual text, not inferred from catalog icon data or C++ layout math.
        text,score=locate(pixels,rect,label)
        x,y,xend,yend=text
        low=max(int(rect[1])+2,int((y+yend)/2-9*scale))
        high=min(int(rect[3])-1,int((y+yend)/2+9*scale))
        # Equal-width Views buttons keep the icon at their left edge while
        # centering unequal labels in the remaining content. Observe the whole
        # actual left-of-text interior for a button, not an assumed text gap.
        is_button=(rect[3]-rect[1])<30*scale
        ix=int(rect[0])+2 if is_button else max(int(rect[0])+2,int(x-22*scale))
        end=int(x-3*scale)
        # Disabled native icon alpha blends white with magenta (observed
        # green ~.34 versus background .07); do not require near-gray text.
        icon=pixels[low:high,ix:end,1]>.18
        amount=int(np.count_nonzero(icon))
        print('ICON_OBSERVER',label,'rect',rect,'label_score',score,'label_x',x,
              'left_glyph_pixels',amount,flush=True)
        check(amount>=10*scale*scale,'visible '+label+' button lacks a separate semantic icon left of its rendered label')
        check(xend<int(rect[2])-2,'full label is clipped against right button edge: '+label)
        if state:
            state_pixels=pixels[low:high,max(int(rect[0])+2,int(x-44*scale)):int(x-23*scale)]
            state_ink=foreground(state_pixels)
            if disabled_state:
                # Native disabled checkbox alpha produces green .22-.26 on this
                # magenta fixture, below the enabled near-neutral-color predicate.
                # Use the existing disabled semantic-icon contrast contract only
                # for this authored unavailable checkbox, and require its outline.
                state_ink=state_pixels[:,:,1]>.18
                sy,sx=np.nonzero(state_ink)
                check(len(sx)>=8*scale*scale,
                      'disabled checkbox outline is missing: '+label)
                left,right,top,bottom=int(sx.min()),int(sx.max()),int(sy.min()),int(sy.max())
                check(8*scale<=right-left+1<=14*scale and
                      8*scale<=bottom-top+1<=14*scale,
                      'disabled checkbox has the wrong measured shape: '+label)
                outline=state_ink[top:bottom+1,left:right+1]
                edge=max(1,int(scale))
                check(all(np.count_nonzero(side)>=6*scale for side in
                          (outline[:edge,:],outline[-edge:,:],
                           outline[:,:edge],outline[:,-edge:])),
                      'disabled checkbox must expose all four outline sides: '+label)
                cy,cx=(top+bottom)//2,(left+right)//2
                check(not np.any(state_ink[cy:cy+edge,cx:cx+edge]),
                      'unavailable checkbox must remain visibly unchecked: '+label)
                check(float(np.quantile(state_pixels[:,:,1][state_ink],.8))<.4,
                      'disabled checkbox lost its reduced native alpha: '+label)
            check(np.count_nonzero(state_ink)>=8*scale*scale,
                  'state indicator and semantic icon must both appear separately: '+label)
            print('STATE_AND_SEMANTIC',label,int(np.count_nonzero(state_ink)),amount,flush=True)
        colors=pixels[low:high,ix:end,1][icon]
        return {'point':((x+xend)/2,(y+yend)/2),'text':text,
                'brightness':float(np.quantile(colors,.8)),'mask':icon}

    # This first public gesture works on the old candidate, before importing any
    # new production module or accessing semantic icon mappings.
    event('MOUSEMOVE','NOTHING',origin)
    yield from settle()
    event('LEFT_SHIFT',shift=True)
    event('RIGHTMOUSE',shift=True)
    yield from settle(8)
    check([op.bl_idname for op in win.modal_operators].count('VIEW3D_OT_axismeld_hotbox')==1,
          'public selected Object Shift+RMB did not open exactly one hotbox')
    pixels=capture('icons-first-object-multicut')
    rectangles=radial_rectangles(pixels)
    semantic_icon(pixels,rectangles['W'],'Multi-Cut')
    event('RIGHTMOUSE','RELEASE',origin,shift=True)
    event('LEFT_SHIFT','RELEASE')
    yield from settle()
    check(not list(win.modal_operators),'center cancel left modal ownership')
    from axismeld import hotbox_runtime

    object_labels={'N':'Target Weld Tool','NW':'Sculpt Tool','NE':'Fill Holes',
                   'W':'Multi-Cut','E':'Append to Polygon Tool',
                   'SW':'Insert Edge Loop Tool','SE':'Soften/Harden Edges','S':'Extrude'}
    views_labels={'N':'Perspective View','NW':'Left View',
                  'W':'Top View','E':'Right View','SW':'Back View','SE':'Bottom View','S':'Front View'}
    component_labels={'N':'Edge','W':'Vertex','S':'Face','NE':'Object Mode',
                      'E':'UV','SW':'Vertex Face','SE':'Multi'}
    create_labels={'N':'Create Polygon Tool','NW':'Plane','NE':'Disc','W':'Cylinder',
                   'E':'Sphere','SW':'Cone','SE':'Torus','S':'Cube'}
    q_labels={'N':'Symmetry','NW':'Marquee','NE':'Drag','W':'Paint Select',
              'E':'Camera-Based Selection','SW':'Lasso','SE':'Clear Selection','S':'Select'}
    transform_labels={'N':'Symmetry','NW':'Object','NE':'Component','W':'World',
                      'E':'Snap','SW':'Axis','SE':'Keep Spacing','S':'Select'}

    def settings(center='views',primary=False):
        with override():
            hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
                'style':'rows' if primary else 'center','transparency':0,
                'rows':['common','pane','modeling'] if primary else [],
                'center_buttons':{'LEFTMOUSE':center},
                'appearance':{'theme_background':True,'brightness':0,'text':[255,255,255],
                              'placeholder':[160,160,160]}}})

    def begin(key='SPACE',mouse='LEFTMOUSE',shift=False):
        origin[:]=[region.x+region.width/2,region.y+region.height/2]
        event('MOUSEMOVE','NOTHING',origin)
        yield from settle(3)
        if shift:
            event('LEFT_SHIFT',shift=True)
        if key:
            event(key,shift=shift)
            yield from settle(12)
        event(mouse,shift=shift)
        yield from settle(7)
        check([op.bl_idname for op in win.modal_operators].count('VIEW3D_OT_axismeld_hotbox')==1,
              'entry must have one native hotbox owner: '+repr((key,mouse)))

    def cancel(key='SPACE',mouse='LEFTMOUSE',shift=False):
        # Release at the physical press origin; do not guess diagonal blanks.
        event('MOUSEMOVE','NOTHING',origin,shift=shift)
        yield from settle(3)
        event(mouse,'RELEASE',shift=shift)
        if key:
            event(key,'RELEASE')
        if shift:
            event('LEFT_SHIFT','RELEASE')
        yield from settle(6)
        check(not list(win.modal_operators),'center cancellation retained modal ownership')

    def observe_ring(label,labels):
        pixels=capture(label)
        rectangles=radial_rectangles(pixels,labels)
        observed={}
        compact={'Perspective View':'Persp','Right View':'Side','Front View':'Front',
                 'Top View':'Top','Left View':'Left','Back View':'Back','Bottom View':'Bottom'}
        for direction,text in labels.items():
            if text in compact and locate(pixels,rectangles[direction],text,required=False) is None:
                text=compact[text]
            observed[direction]=semantic_icon(pixels,rectangles[direction],text)
        return rectangles,observed

    def gaps(rectangles,reference,label):
        values=[]
        for left,right in (('NW','NE'),('W','E'),('SW','SE')):
            if left not in rectangles or right not in rectangles:
                continue
            actual=rectangles[right][0]-rectangles[left][2]-1
            # Views has no visible NE command. Its measured lower diagonal pair
            # supplies the symmetric upper-row clearance; no synthetic button width.
            ref_left,ref_right=('SW','SE') if right not in reference else (left,right)
            expected=reference[ref_right][0]-reference[ref_left][2]-1
            check(abs(actual-expected)<=3*scale,
                  label+' actual inner-edge clearance differs from Views: '+repr((left,actual,expected)))
            values.append((left,actual,expected))
        print('ACTUAL_INNER_EDGES',label,scale,values,flush=True)

    def whole_region():
        return (region.x+2,region.y+2,region.x+region.width-2,region.y+region.height-2)

    def labelled_column(pixels, label):
        # Connected backgrounds preserve real inter-column gaps. The old span
        # closing joined adjacent columns and placed a left-column Options hit
        # at the right edge of a different column.
        glyph=template(label);gh,gw=glyph.shape
        matches=[]
        backgrounds=observed_menu_rectangles(menu_background_mask(pixels),100*scale,13*scale)
        columns=[rect for rect in backgrounds if rect[3]-rect[1]>27*scale]
        # A one-row final column (e.g. Polygon Display at 2x) is still native:
        # it shares observed width/top and an adjacent column gap with a tall
        # sibling. Isolated radial buttons cannot establish this context.
        for rect in backgrounds:
            if rect in columns:
                continue
            if any(abs((rect[2]-rect[0])-(other[2]-other[0]))<=2*scale and
                   abs(rect[3]-other[3])<=2*scale and
                   0<=rect[0]-other[2]<=10*scale for other in columns):
                columns.append(rect)
        for rect in columns:
            if rect[2]-rect[0]-4<gw or rect[3]-rect[1]-4<gh:
                continue
            if locate(pixels,rect,label,required=False) is not None:
                matches.append(rect)
        check(len(matches)==1,'expected one actual native column containing '+label+': '+repr(matches))
        return matches[0]

    def find_row(label,tag):
        yield from settle(1)
        pixels=capture(tag+'-0')
        rect=labelled_column(pixels,label)
        observed=semantic_icon(pixels,rect,label)
        return pixels,rect,observed

    for requested_scale in (1.0,2.0):
        bpy.context.preferences.view.ui_scale=requested_scale
        yield from settle(10)
        region=next(r for r in area.regions if r.type=='WINDOW')
        scale=bpy.context.preferences.system.ui_scale
        tag='icons-'+str(requested_scale)
        settings(primary=True)
        origin[:]=[region.x+region.width/2,region.y+region.height/2]
        event('MOUSEMOVE','NOTHING',origin)
        event('SPACE')
        yield from settle(14)
        pixels=capture(tag+'-space-primary')
        central=(region.x+2,int(origin[1]-180*scale),region.x+region.width-2,int(origin[1]+180*scale))
        for label in ('File','Edit','Create','Select','Modify','Display','Windows'):
            semantic_icon(pixels,central,label)
        event('ESC');event('ESC','RELEASE');event('SPACE','RELEASE')
        yield from settle(7)
        check(not list(win.modal_operators),'primary Escape left ownership')

        settings()
        yield from settle(7)
        yield from begin()
        reference,_=observe_ring(tag+'-views',views_labels)
        yield from cancel()

        for key in ('Q','W','E','R'):
            labels=dict(q_labels if key=='Q' else transform_labels)
            if key=='E':
                labels.update(E='Gimbal',SW='Custom',SE='Discrete Rotate')
            elif key=='R':
                labels.update(E='Snap Scale',SE='Relative')
            yield from begin(key)
            actual,_=observe_ring(tag+'-'+key,labels)
            gaps(actual,reference,key)
            # Enter a real child ring by hovering its observed parent label.
            if key=='W':
                point=((actual['SW'][0]+actual['SW'][2])/2,(actual['SW'][1]+actual['SW'][3])/2)
                event('MOUSEMOVE','NOTHING',point)
                yield from settle(7)
                child=capture(tag+'-W-axis-child')
                for label in ('Parent','Normal','Live Object Axis','Along Rotation Axis','Custom'):
                    semantic_icon(child,whole_region(),label)
                event('ESC');event('ESC','RELEASE')
                event('LEFTMOUSE','RELEASE');event(key,'RELEASE')
                yield from settle(6)
            else:
                yield from cancel(key)

        with override():
            bpy.ops.object.mode_set(mode='EDIT')
        yield from settle(7)
        yield from begin(None,'RIGHTMOUSE')
        actual,_=observe_ring(tag+'-components',component_labels)
        gaps(actual,reference,'components')
        yield from cancel(None,'RIGHTMOUSE')
        with override():
            bpy.ops.object.mode_set(mode='OBJECT')
        yield from settle(7)
        yield from begin(None,'RIGHTMOUSE',True)
        actual,observed=observe_ring(tag+'-object',object_labels)
        gaps(actual,reference,'Object')
        check(observed['NW']['brightness']<observed['W']['brightness']-.08,
              'disabled Object icon must use visibly reduced native alpha')

        pixels,rect,smooth=yield from find_row('Smooth',tag+'-ordinary')
        semantic_icon(pixels,rect,'Unsmooth')
        text=smooth['text'];cy=int((text[1]+text[3])/2)
        gear=foreground(pixels[int(cy-10*scale):int(cy+10*scale),int(rect[2]-24*scale):int(rect[2]-2*scale)])
        gy,gx=np.nonzero(gear)
        check(len(gx)>10*scale*scale and gx.max()-gx.min()<=18*scale,
              'Options must have one gear confined to its independent cell')
        # Actual Options hit area remains separate from the semantic icon/label.
        before=tuple((obj.name,len(obj.modifiers)) for obj in bpy.context.scene.objects)
        event('MOUSEMOVE','NOTHING',(rect[2]-12*scale,cy),shift=True)
        yield from settle(4)
        event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
        yield from settle(8)
        check(tuple((obj.name,len(obj.modifiers)) for obj in bpy.context.scene.objects)==before,
              'opening Options mutated modifiers')
        dialog=capture(tag+'-options-dialog')
        locate(dialog,whole_region(),'Subdivision Levels',native=True)
        event('ESC');event('ESC','RELEASE')
        yield from settle(6)

        for parent,children in (('Mapping',('Planar Map X','Planar Map Y','Planar Map Z')),
                                ('Polygon Display',('Backface Culling','Border Edges'))):
            yield from begin(None,'RIGHTMOUSE',True)
            pixels,rect,observed=yield from find_row(parent,tag+'-'+parent.replace(' ','-'))
            event('MOUSEMOVE','NOTHING',observed['point'],shift=True)
            yield from settle(8)
            child=capture(tag+'-'+parent.replace(' ','-')+'-cascade')
            child_labels=[semantic_icon(child,labelled_column(child,label),label,state=label=='Backface Culling')
                          for label in children]
            check(len({item['text'][0] for item in child_labels})==1,
                  'semantic/state columns misalign sibling labels: '+parent)
            event('ESC',shift=True);event('ESC','RELEASE',shift=True)
            event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
            yield from settle(7)
            check(not list(win.modal_operators),'cascade Escape retained ownership')

        with override():
            selected=tuple(obj.name for obj in bpy.context.selected_objects)
            active=bpy.context.active_object.name
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            bpy.context.view_layer.objects.active=None
        # Put the pointer over an observed blank corner to avoid preselect.
        # A temporary hidden mesh makes the entire viewport a native blank pick.
        for obj in bpy.context.scene.objects:
            obj.hide_set(True)
        yield from settle(6)
        yield from begin(None,'RIGHTMOUSE',True)
        actual,_=observe_ring(tag+'-create',create_labels)
        gaps(actual,reference,'Create')
        yield from cancel(None,'RIGHTMOUSE',True)
        for obj in bpy.context.scene.objects:
            obj.hide_set(False)
        for name in selected:
            bpy.data.objects[name].select_set(True)
        bpy.context.view_layer.objects.active=bpy.data.objects[active]
        yield from settle(6)

        # Native radio and checkbox state get their own glyph, in addition to
        # the semantic icon. Enter through Space's actual configured center.
        for menu,labels in (('center.controls.style',('Zones and Menu Rows','Zones Only','Center Zone Only',
                                                     'Center Zone RMB Popups')),
                            ('center.controls.transparency',('0%','25%','50%','75%','100%')),
                            ('center.controls.modeling',('Show/Hide Modeling',)),
                            ('context.create_menu.polygon_display_all',
                             ('Backface Culling on for All Polys','Backface Culling off for All Polys'))):
            settings(menu)
            yield from settle(6)
            yield from begin()
            pixels=capture(tag+'-'+menu)
            # These short lists touch the center button; label matching avoids
            # treating their contiguous backdrops as one tall rectangle.
            rect=whole_region()
            for label in labels:
                semantic_icon(pixels,rect,label,state=(menu in ('center.controls.transparency','center.controls.modeling') or label=='Center Zone RMB Popups'),
                              disabled_state=label=='Center Zone RMB Popups')
            yield from cancel()
        settings()

        # The same rendered inner edges must survive an actual quad viewport.
        with override():
            bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        region=min((r for r in area.regions if r.type=='WINDOW'),key=lambda r:(r.y,r.x))
        yield from begin()
        quad_reference,_=observe_ring(tag+'-quad-views',views_labels)
        yield from cancel()
        if requested_scale==2.0:
            # The old short-quad rejection now expands onto the whole window.
            # Preserve full scene/tool/input observers around that same boundary.
            print('QUAD_W_FULL_SURFACE_BOUNDS','physical',region.width,region.height,
                  'logical',region.width/scale,region.height/scale,'scale',scale,flush=True)
            check(region.height/scale<250,'2x boundary fixture is no longer a short quad region')
            def scene_tool_state():
                with override():
                    active=bpy.context.view_layer.objects.active
                    objects=[]
                    for obj in sorted(bpy.context.scene.objects,key=lambda item:item.name):
                        mesh=() if obj.type!='MESH' else (
                            tuple((tuple(v.co),v.select,v.hide) for v in obj.data.vertices),
                            tuple((tuple(e.vertices),e.select,e.hide) for e in obj.data.edges),
                            tuple((tuple(f.vertices),f.select,f.hide) for f in obj.data.polygons))
                        objects.append((obj.as_pointer(),obj.name,obj.mode,obj.select_get(),
                                        obj.hide_get(),obj.hide_viewport,
                                        tuple(tuple(row) for row in obj.matrix_world),
                                        obj.parent.as_pointer() if obj.parent else None,
                                        tuple((m.name,m.type) for m in obj.modifiers),mesh))
                    tools=[]
                    for mode in ('OBJECT','EDIT_MESH'):
                        tool=bpy.context.workspace.tools.from_space_view3d_mode(mode,create=False)
                        tools.append(None if tool is None else tool.idname)
                    return (bpy.context.mode,active.as_pointer() if active else None,
                            tuple(objects),tuple(tools),hotbox_runtime.recent.items())
            before=scene_tool_state()
            event('MOUSEMOVE','NOTHING',origin)
            event('W')
            yield from settle(12)
            check([op.bl_idname for op in win.modal_operators]==['VIEW3D_OT_axismeld_hotbox'],
                  'W press must own its ordinary invisible hold phase')
            held=scene_tool_state()
            print('QUAD_W_STATE_BEFORE',repr(before),flush=True)
            print('QUAD_W_STATE_HELD',repr(held),flush=True)
            check(held[:3]==before[:3] and held[4]==before[4],
                  'W hold phase changed scene/selection/Recent before display')
            check(held[3][0]=='builtin.move','ordinary W press did not activate Move')
            before=held
            event('LEFTMOUSE')
            yield from settle(9)
            actual,_=observe_ring(tag+'-quad-W-expanded',transform_labels)
            gaps(actual,quad_reference,'quad W2x whole-window complete composition')
            pixels=capture(tag+'-quad-W-expanded-companion')
            companion=companion_rect(pixels)
            semantic_icon(pixels,companion,'Selection Constraints')
            check([op.bl_idname for op in win.modal_operators]==['VIEW3D_OT_axismeld_hotbox'],
                  'whole-window W must retain one visible owner')
            check(scene_tool_state()==before,'expanded W display changed normal held scene/tool/Recent')
            event('MOUSEMOVE','NOTHING',origin)
            event('LEFTMOUSE','RELEASE');event('W','RELEASE')
            yield from settle(6)
            check(not list(win.modal_operators) and scene_tool_state()==before,
                  'expanded W original-source return changed scene or retained input')
            yield from begin()
            observe_ring(tag+'-quad-views-after-W-expanded',views_labels)
            yield from cancel()
            check(scene_tool_state()==before,'next Views cancellation changed scene/tool/Recent')
            print('PASS2x short quad W expands across panes; original return and Views recover',flush=True)

            # Keep the same real quad, increase logical room through the public
            # UI scale preference, and measure both rings afresh at that scale.
            bpy.context.preferences.view.ui_scale=1.5
            yield from settle(10)
            region=min((r for r in area.regions if r.type=='WINDOW'),key=lambda r:(r.y,r.x))
            scale=bpy.context.preferences.system.ui_scale
            check(abs(scale-1.5)<.01,'bounded W supplement did not apply actual 1.5x scale')
            print('QUAD_W_SUPPORTED_BOUNDS','physical',region.width,region.height,
                  'logical',region.width/scale,region.height/scale,'scale',scale,flush=True)
            yield from begin()
            roomy_reference,_=observe_ring(tag+'-quad-1.5-views',views_labels)
            yield from cancel()
            yield from begin('W')
            actual,_=observe_ring(tag+'-quad-1.5-W',transform_labels)
            gaps(actual,roomy_reference,'quad W 1.5x complete composition')
            pixels=capture(tag+'-quad-1.5-W-companion')
            companion=companion_rect(pixels)
            semantic_icon(pixels,companion,'Selection Constraints')
            yield from cancel('W')
            bpy.context.preferences.view.ui_scale=2.0
            yield from settle(10)
            region=min((r for r in area.regions if r.type=='WINDOW'),key=lambda r:(r.y,r.x))
            scale=bpy.context.preferences.system.ui_scale
            check(abs(scale-2.0)<.01,'quad Object boundary did not restore actual 2x scale')
            origin[:]=[region.x+region.width/2,region.y+region.height/2]
        else:
            yield from begin('W')
            actual,_=observe_ring(tag+'-quad-W',transform_labels)
            gaps(actual,quad_reference,'quad W')
            yield from cancel('W')
        before=(bpy.context.mode,bpy.context.active_object.name,
                tuple((o.name,o.select_get(),len(o.modifiers)) for o in bpy.context.view_layer.objects))
        yield from begin(None,'RIGHTMOUSE',True)
        actual,_=observe_ring(tag+'-quad-object-expanded',object_labels)
        gaps(actual,quad_reference,'quad Object whole-window complete composition')
        yield from cancel(None,'RIGHTMOUSE',True)
        check((bpy.context.mode,bpy.context.active_object.name,
               tuple((o.name,o.select_get(),len(o.modifiers)) for o in bpy.context.view_layer.objects))==before,
              'expanded Object cancellation changed mode/selection/modifiers')
        yield from begin()
        observe_ring(tag+'-quad-views-after-object',views_labels)
        yield from cancel()
        with override():
            bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        region=next(r for r in area.regions if r.type=='WINDOW')
        print('PASS semantic icons, state slots, Options and actual geometry scale',scale,flush=True)

    print('AXISMELD_HOTBOX_ICONS_EVENTS_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps)
        return .025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None
bpy.app.timers.register(tick,first_interval=1)

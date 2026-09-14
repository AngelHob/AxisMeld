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

    def semantic_icon(pixels,rect,label,state=False):
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
            state_ink=foreground(pixels[low:high,max(int(rect[0])+2,int(x-44*scale)):int(x-23*scale)])
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
    views_labels={'N':'Perspective View','NW':'Left View','NE':'New Camera',
                  'W':'Top View','E':'Right View','SW':'Back View','SE':'Bottom View','S':'Front View'}
    component_labels={'N':'Edge','W':'Vertex','S':'Face','NE':'Object Mode',
                      'E':'UV','SW':'Vertex Face','SE':'Multi Component'}
    create_labels={'N':'Create Polygon Tool','NW':'Plane','NE':'Disc','W':'Cylinder',
                   'E':'Sphere','SW':'Cone','SE':'Torus','S':'Cube'}
    q_labels={'N':'Symmetry','NW':'Marquee Select','NE':'Drag Select','W':'Paint Selection',
              'E':'Camera Based Selection','SW':'Lasso Select','SE':'Clear Selection','S':'Select'}
    transform_labels={'N':'Symmetry','NW':'Local','NE':'Normal Average','W':'Global',
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
            expected=reference[right][0]-reference[left][2]-1
            check(abs(actual-expected)<=3*scale,
                  label+' actual inner-edge clearance differs from Views: '+repr((left,actual,expected)))
            values.append((left,actual,expected))
        print('ACTUAL_INNER_EDGES',label,scale,values,flush=True)

    def whole_region():
        return (region.x+2,region.y+2,region.x+region.width-2,region.y+region.height-2)

    def find_row(label,tag):
        for page in range(32):
            pixels=capture(tag+'-'+str(page))
            rect=companion_rect(pixels)
            located=locate(pixels,rect,label,required=False)
            if located:
                observed=semantic_icon(pixels,rect,label)
                return pixels,rect,observed
            event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),shift=True)
            event('WHEELDOWNMOUSE',shift=True)
            yield from settle(4)
        raise AssertionError('bounded real wheel paging did not expose '+label)

    # Keep icon and clipping coverage at both effective UI scales. All settings
    # and geometry live only in this disposable factory process.
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
                labels.update(E='Gimbal',SW='Custom Axis',SE='Discrete Rotate')
            elif key=='R':
                labels.update(E='Discrete Scale',SE='Relative')
            yield from begin(key)
            actual,_=observe_ring(tag+'-'+key,labels)
            gaps(actual,reference,key)
            # Enter a real child ring by hovering its observed parent label.
            if key=='W':
                point=((actual['SW'][0]+actual['SW'][2])/2,(actual['SW'][1]+actual['SW'][3])/2)
                event('MOUSEMOVE','NOTHING',point)
                yield from settle(7)
                child=capture(tag+'-W-axis-child')
                for label in ('Parent Axis','Component Axis','Live Object Axis','Rotation Axis',
                              'Custom Axis','View (Blender)','Tool Options'):
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
            childrect=companion_rect(child,exclude=rect)
            child_labels=[semantic_icon(child,childrect,label,state=label=='Backface Culling')
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
        for menu,labels in (('center.controls.style',('Zones and Menu Rows','Zones Only','Center Zone Only')),
                            ('center.controls.rows',('Show Common Menus','Show Pane Specific Menus','Show Modeling'))):
            settings(menu)
            yield from settle(6)
            yield from begin()
            pixels=capture(tag+'-'+menu)
            # These short lists touch the center button; label matching avoids
            # treating their contiguous backdrops as one tall rectangle.
            rect=whole_region()
            for label in labels:
                semantic_icon(pixels,rect,label,state=menu.endswith('.style'))
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
        yield from begin('W')
        actual,_=observe_ring(tag+'-quad-W',transform_labels)
        gaps(actual,quad_reference,'quad W')
        yield from cancel('W')
        if requested_scale==1.0:
            yield from begin(None,'RIGHTMOUSE',True)
            actual,_=observe_ring(tag+'-quad-object',object_labels)
            gaps(actual,quad_reference,'quad Object')
            yield from cancel(None,'RIGHTMOUSE',True)
        else:
            # Actual old/new disposable probes both reject this 480x231 logical
            # region: complete Object ring plus minimum paged companion cannot
            # fit. Preserve this existing safe narrow-window boundary.
            check(region.height/scale<250,'unsupported fixture is no longer a short quad region')
            before=(bpy.context.mode,bpy.context.active_object.name,
                    tuple((o.name,o.select_get(),len(o.modifiers)) for o in bpy.context.view_layer.objects))
            event('MOUSEMOVE','NOTHING',origin)
            event('LEFT_SHIFT',shift=True);event('RIGHTMOUSE',shift=True)
            yield from settle(9)
            capture(tag+'-quad-object-unsupported')
            check(not list(win.modal_operators),'unsupported short Object region started a competing handler')
            event('RIGHTMOUSE','RELEASE',shift=True);event('LEFT_SHIFT','RELEASE')
            yield from settle(5)
            check((bpy.context.mode,bpy.context.active_object.name,
                   tuple((o.name,o.select_get(),len(o.modifiers)) for o in bpy.context.view_layer.objects))==before,
                  'unsupported short Object region changed mode/selection/modifiers')
            yield from begin()
            capture(tag+'-quad-views-after-unsupported')
            yield from cancel()
            print('PASS existing 2x short quad Object unsupported guard and next Views input',flush=True)
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

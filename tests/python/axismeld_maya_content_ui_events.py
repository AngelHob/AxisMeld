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

    def companion_rect(pixels, exclude=None, minimum_height=58, min_width=None):
            # Actual long colored row spans establish bounds; no list-layout constants
            # or expected coordinates enter this measurement. Text-sized holes close,
            # while the established radial inner gaps keep radial buttons separate.
            rgb = pixels[:, :, :3]
            colored = ((rgb[:, :, 0] > .3) & (rgb[:, :, 2] > .25)
                       & (np.minimum(rgb[:, :, 0], rgb[:, :, 2]) > 2.2*rgb[:, :, 1]))
            if exclude is not None:
                xa,ya,xb,yb = map(int,exclude)
                colored[max(0,ya-3):yb+3,max(0,xa-3):xb+3] = False
            minimum_width = (min_width if min_width is not None else (100 if exclude is not None else 150))*scale
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
                if max(ys)-min(ys) > minimum_height*scale and len(ys) > min(25, minimum_height*.4)*scale:
                    candidates.append((min(row[0] for row in rows), min(ys),
                                       max(row[1] for row in rows)+1, max(ys)+1))
            check(candidates, 'no independently observed companion rectangle')
            rect=max(candidates, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
            # A touching parent button can merge the top row's horizontal
            # span. Follow the observed list's solid right interior vertically
            # to retain those rows, independently of labels and row counts.
            xa,ya,xb,yb=rect
            column=np.any(colored[:,int(xb-4*scale):int(xb-2*scale)],axis=1)
            while ya>region.y and column[ya-1]:ya-=1
            while yb<region.y+region.height and column[yb]:yb+=1
            return xa,ya,xb,yb

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
                    # Measure the font baseline, not the union of icon and text
                    # ink: descenders and gear glyphs have different heights.
                    glyph_match=locate(pixels,(x0,max(y0,y0+low-8*scale),x1,min(y1,y0+high+8*scale)),label,required=False)
                    if glyph_match is not None:
                        bounds,score=glyph_match
                        cy=bounds[1]-template_baselines[(scale,label)]+4*scale
                        matches.append((label,(x0+x1)/2,cy,score))
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

    # Independent public input RED, before importing new menu/catalog modules.
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode=(True,False,False)
        bpy.ops.mesh.select_all(action='SELECT')
    yield from settle(7)
    yield from start()
    picture=capture('content-first-vertex-companion')
    try:
        initial=companion_rect(picture)
    except AssertionError:
        raise AssertionError('Vertex Shift+RMB lacks the required simultaneous Maya9-row companion')
    check(locate(picture,initial,'Crease Tool',required=False),
          'Vertex companion lacks independently rendered Crease Tool')
    yield from cancel()
    from axismeld import hotbox_runtime
    import bmesh
    from mathutils import Vector
    from bpy_extras.view3d_utils import location_3d_to_region_2d

    MODEL = {
        'vertex': ('Crease Tool +O','Connect Components +O','Detach Components','Transform Component +O','Connect Tool +O',
                   '|','Circularize Vertices +O','Reorder Vertices','|','Apply Color +O','|','Polygon Display'),
        'edge': ('Crease Tool +O','Offset Edge Loop Tool +O','Insert Edge Loop Tool +O','Slide Edge Tool +O',
                 'Circularize Components +O','Edit Edge Flow +O','|','Add Divisions To Edge +O','Bridge +O','Fill Hole',
                 '|','Connect Components +O','Detach Components','Transform Component +O','Connect Tool +O','|','Polygon Display'),
        'face': ('|','Smart Extrude','Smooth Faces +O','Assign Invisible Faces +O','Add Divisions To Faces +O',
                 'Circularize Components +O','Connect Components +O','Detach Components','Triangulate Faces',
                 'Quadrangulate Faces +O','Reduce Faces +O','Remesh +O','Bridge Faces +O','|','Mirror +O','Extract Faces +O',
                 'Duplicate Face +O','Transform Component +O','Connect Tool +O','Target Weld Tool +O','|','Mapping','|','Polygon Display'),
    }
    COMPONENT=('AuditMesh...','|','Select','Select All','Deselect All','Select Hierarchy','Invert Selection','|',
               'Select Similar +O','|','Make Live','|','DG Traversal','Inputs','Outputs','Paint','Metadata','Actions',
               'UV Sets','Color Sets','Time Editor','|','Scene Assembly','|','Material Attributes...','|',
               'Assign New Material','Assign Favorite Material','Assign Existing Material')
    TOOLS={
        'Q':('Automatic Camera-Based Selection',),
        'W':('Selection Constraints','Transform Constraints','|','Shift Extrude','Shift Duplicate','|',
             'Preserve UVs','Preserve Children','Tweak Mode','Update Triad','|','Move Options'),
        'E':('Selection Constraints','Transform Constraints','|','Shift Extrude','Shift Duplicate','|',
             'Rotate Center','Free Rotate','Preserve UVs','Preserve Children','Tweak Mode','Relative','|','Rotate Options'),
        'R':('Selection Constraints','Transform Constraints','|','Shift Extrude','Shift Duplicate','|',
             'Scale Center','Prevent Negative Scale','Preserve UVs','Preserve Children','Tweak Mode','|','Scale Options'),
    }
    def state():
        selected=[]
        if bpy.context.mode=='EDIT_MESH':
            for ob in bpy.context.objects_in_mode_unique_data:
                bm=bmesh.from_edit_mesh(ob.data)
                selected.append((ob.name,tuple(tuple(e.select for e in getattr(bm,key)) for key in ('verts','edges','faces'))))
        return (bpy.context.mode,tuple(bpy.context.tool_settings.mesh_select_mode),
                bpy.context.active_object.name if bpy.context.active_object else None,
                tuple(sorted((o.name,o.type,o.select_get(),len(o.modifiers)) for o in bpy.context.scene.objects)),
                tuple(selected),tuple(hotbox_runtime.recent.items()))

    def setup(domain='vertex'):
        with override():
            if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
            for obj in tuple(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
            bpy.ops.mesh.primitive_cube_add()
            bpy.context.active_object.name='AuditMesh'
            if domain!='object':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode=tuple(domain==d for d in ('vertex','edge','face'))
                bpy.ops.mesh.select_all(action='SELECT')
        region.data.view_location=Vector((0,0,0));region.data.view_distance=8

    def configure(center='views'):
        with override():
            hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
                'style':'center','rows':[],'transparency':0,'center_buttons':{'LEFTMOUSE':center},
                'appearance':{'theme_background':True,'brightness':0,'text':[255,255,255],'placeholder':[160,160,160]}}})

    def begin(kind,point=None):
        if point is None:point=(region.x+region.width/2,region.y+region.height/2)
        origin[:]=point
        event('MOUSEMOVE','NOTHING',origin);yield from settle(3)
        if kind in MODEL or kind=='create':
            event('LEFT_SHIFT',shift=True);event('RIGHTMOUSE',shift=True)
        elif kind=='component':event('RIGHTMOUSE')
        else:
            event(kind);yield from settle(12);event('LEFTMOUSE')
        yield from settle(8)
        check(sum(op.bl_idname=='VIEW3D_OT_axismeld_hotbox' for op in win.modal_operators)==1,
              'one owner required for '+kind)

    def finish(kind,at_origin=True):
        shift=(kind in MODEL or kind=='create')
        if at_origin:event('MOUSEMOVE','NOTHING',origin,shift=shift);yield from settle(3)
        event('RIGHTMOUSE' if kind in MODEL or kind in ('create','component') else 'LEFTMOUSE','RELEASE',shift=shift)
        if shift:event('LEFT_SHIFT','RELEASE')
        elif kind!='component':event(kind,'RELEASE')
        yield from settle(6)
        check(not list(win.modal_operators),'release retained ownership: '+kind)

    def all_labels(expected):return [name.removesuffix(' +O') for name in expected if name!='|']

    def browse(kind,expected,tag,stop=None):
        labels=all_labels(expected);seen=set();boundaries=set()
        separator_after={expected[i-1].removesuffix(' +O') for i,x in enumerate(expected) if x=='|' and i>0}
        options={x.removesuffix(' +O') for x in expected if x.endswith(' +O')}
        last=None;stalls=0
        for page in range(45):
            picture=capture(tag+'-'+str(page));rect=companion_rect(picture)
            rows=rendered_rows(picture,rect,labels)
            check(rows,'no full labels recognized in '+tag)
            indices=[labels.index(r[0]) for r in rows]
            check(indices==sorted(set(indices)),'actual menu order/duplicate mismatch '+tag+repr(rows))
            seen.update(r[0] for r in rows)
            for a,b in zip(rows,rows[1:]):
                if labels.index(b[0])==labels.index(a[0])+1:
                    wanted=30 if a[0] in separator_after else 24
                    check(abs((a[2]-b[2])/scale-wanted)<=2,'actual24/6 menu pitch changed '+repr((tag,a,b)))
                    boundaries.add(a[0])
            for row in rows:
                if row[0] in options:
                    cy=row[2];mask=picture[int(cy-9*scale):int(cy+9*scale),int(rect[2]-24*scale):int(rect[2]-2*scale),1]>.18
                    yy,xx=np.nonzero(mask)
                    check(len(xx)>8*scale*scale and xx.max()-xx.min()>=8*scale,'missing Options glyph '+row[0])
                if row[0]==stop:return picture,rect,row
            print('CONTENT_ROWS',tag,page,[(r[0],round(r[2],1)) for r in rows],flush=True)
            if stop is None and seen==set(labels) and separator_after<=boundaries:return picture,rect,rows
            signature=tuple((r[0],round(r[2])) for r in rows)
            stalls=stalls+1 if signature==last else 0;last=signature
            check(stalls<3,'real paging stalled '+tag)
            event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),shift=(kind in MODEL or kind=='create'))
            event('WHEELDOWNMOUSE',shift=(kind in MODEL or kind=='create'));yield from settle(4)
        raise AssertionError('bounded content paging did not expose complete '+tag)

    def check_edges(actual,reference,tag):
        comparisons=[]
        for left,right in (('NW','NE'),('W','E'),('SW','SE')):
            if left not in actual or right not in actual:continue
            got=actual[right][0]-actual[left][2]-1
            # The historical disabled NE New Camera was removed. Compare
            # this upper pair against the observed symmetric lower pair.
            ref_left,ref_right=(left,right) if right in reference else ('SW','SE')
            wanted=reference[ref_right][0]-reference[ref_left][2]-1
            check(abs(got-wanted)<=2*scale,'actual Views inner edges differ '+repr((tag,left,got,wanted)))
            comparisons.append((got,wanted))
        check(comparisons,'no actual horizontal pair compared '+tag)
        print('CONTENT_ACTUAL_VIEWS_EDGES',tag,scale,comparisons,flush=True)

    def reference(tag):
        configure();yield from begin('SPACE')
        result=radial_rectangles(capture(tag+'-views'),{'N','E','SE','S','SW','W','NW'})
        yield from finish('SPACE');return result

    def hover_row(kind,expected,label,tag):
        picture,rect,row=yield from browse(kind,expected,tag,stop=label)
        event('MOUSEMOVE','NOTHING',(row[1],row[2]),shift=kind in MODEL or kind=='create')
        yield from settle(8)
        return rect

    def child_labels(parent,labels,tag):
        picture=capture(tag)
        rect=companion_rect(picture,exclude=parent,minimum_height=30,min_width=55)
        texts=[locate(picture,rect,label)[0] for label in labels]
        check([t[1] for t in texts]==sorted([t[1] for t in texts],reverse=True),
              'actual child labels are not in specified order '+tag)
        return picture,rect,texts

    def checkbox_pixels(picture,text,tag):
        x,y,x1,y1=text;cy=(y+y1)/2
        mask=picture[int(cy-8*scale):int(cy+8*scale),int(x-44*scale):int(x-23*scale),1]>.18
        check(np.count_nonzero(mask)>=8*scale*scale,'missing actual separate state glyph '+tag)
        return mask

    def escape(kind):
        event('ESC',shift=kind in MODEL or kind=='create');event('ESC','RELEASE')
        event('RIGHTMOUSE' if kind in MODEL or kind in ('create','component') else 'LEFTMOUSE','RELEASE')
        if kind in MODEL or kind=='create':event('LEFT_SHIFT','RELEASE')
        elif kind!='component':event(kind,'RELEASE')
        yield from settle(7)
        check(not list(win.modal_operators),'Escape retained owner '+kind)

    def state_cases():
        nonlocal scale,region
        controls=('Show Modeling','Show Rigging','Show Animation','Show FX','Show All','Hide All','Show Rendering',
                  'Show Common Menus','Show Pane Specific Menus','Show Custom Menu Set Menus','Set Transparency',
                  'Hotbox Style','|','Window Options','|','AxisMeld Center Mouse Buttons')
        for requested_scale in (1.0,2.0):
            bpy.context.preferences.view.ui_scale=requested_scale;yield from settle(8)
            scale=bpy.context.preferences.system.ui_scale;region=next(r for r in area.regions if r.type=='WINDOW')
            setup();configure();yield from settle(5)
            before=state()
            # All ordinary constraint children; actual state slots remain separate from semantic icons.
            for key,parent,labels in (
                ('W','Selection Constraints',('Off','Angle','Border','Edge Loop','Edge Ring','Shell','UV Edge Loop')),
                ('W','Transform Constraints',('Off','Edge Slide','Surface Slide','Along Normals')),
                ('E','Rotate Center',('Default','Object','Manip','Selection')),
                ('R','Scale Center',('Default','Object','Manip'))):
                yield from begin(key)
                rect=yield from hover_row(key,TOOLS[key],parent,'state-'+str(scale)+'-'+parent)
                picture,child,texts=child_labels(rect,labels,'state-'+str(scale)+'-'+parent+'-child')
                for label,text in zip(labels,texts):checkbox_pixels(picture,text,parent+' '+label)
                yield from escape(key)
                check(state()==before,'disabled constraint hover mutated scene')
            # Component UV directory is an ordinary two-item list, not a new radial.
            yield from begin('component');picture=capture('state-uv-parent-'+str(scale))
            ring=radial_rectangles(picture,{'N','NE','E','SE','S','SW','W'})
            r=ring['E'];event('MOUSEMOVE','NOTHING',((r[0]+r[2])/2,(r[1]+r[3])/2));yield from settle(8)
            picture=capture('state-uv-child-'+str(scale))
            whole=(region.x,region.y,region.x+region.width,region.y+region.height)
            shell,_=locate(picture,whole,'UV Shell')
            # Search the same actual child x-column above its second row, avoiding the parent UV label.
            locate(picture,(shell[0]-2,shell[3],shell[2]+8*scale,shell[3]+30*scale),'UV')
            yield from escape('component');check(state()==before,'UV hover changed selection')
            # A held W Select child must bring its own automatic-selection companion.
            yield from begin('W');picture=capture('state-shared-select-parent-'+str(scale))
            r=radial_rectangles(picture)['S']
            event('MOUSEMOVE','NOTHING',((r[0]+r[2])/2,(r[1]+r[3])/2));yield from settle(9)
            picture=capture('state-shared-select-child-'+str(scale))
            text,_=locate(picture,whole,'Automatic Camera-Based Selection')
            checkbox_pixels(picture,text,'shared Select automatic')
            locate(picture,whole,'Preselection Highlight');locate(picture,whole,'Highlight Nearest Component')
            yield from escape('W');check(state()==before,'shared Select hover changed scene')
            configure('center.controls');yield from begin('SPACE')
            if requested_scale==1.0:yield from browse('SPACE',controls,'state-controls-full')
            yield from escape('SPACE')
            for parent,labels in (('Show Modeling',('Modeling Only','Show/Hide Modeling')),
                                  ('Hotbox Style',('Zones and Menu Rows','Zones Only','Center Zone Only','Center Zone RMB Popups')),
                                  ('Window Options',('Show Main Menubar','Show Pane Menubars'))):
                yield from begin('SPACE')
                rect=yield from hover_row('SPACE',controls,parent,'state-control-'+str(scale)+'-'+parent)
                picture,child,texts=child_labels(rect,labels,'state-control-'+str(scale)+'-'+parent+'-child')
                for label,text in zip(labels,texts):
                    if label!='Modeling Only':checkbox_pixels(picture,text,label)
                yield from escape('SPACE')
            configure();check(state()==before,'Controls content mutated scene')
        bpy.context.preferences.view.ui_scale=1.0;yield from settle(8)
        scale=bpy.context.preferences.system.ui_scale;region=next(r for r in area.regions if r.type=='WINDOW')
        # Options release cannot launch its main Crease action or change selection.
        setup();configure();yield from settle(5);before=state();yield from begin('vertex')
        picture,rect,row=yield from browse('vertex',MODEL['vertex'],'state-disabled-options',stop='Crease Tool')
        event('MOUSEMOVE','NOTHING',(rect[2]-12*scale,row[2]),shift=True);yield from settle(3)
        yield from finish('vertex',False);check(state()==before,'disabled Options executed main action')
        # Actual component operation and one Undo, independent mesh observer.
        setup('face');yield from settle(5)
        with override():bpy.ops.ed.undo_push(message='Before companion face triangulate')
        before=state();yield from begin('face')
        picture,rect,row=yield from browse('face',MODEL['face'],'state-face-triangulate',stop='Triangulate Faces')
        event('MOUSEMOVE','NOTHING',(row[1],row[2]),shift=True);yield from finish('face',False)
        check(len(bmesh.from_edit_mesh(bpy.context.active_object.data).faces)==12,'Face companion did not triangulate cube')
        with override():check(bpy.ops.ed.undo()=={'FINISHED'},'one Undo unavailable')
        yield from settle(6)
        after=state()
        print('TRIANGULATE_UNDO_OBSERVED',repr(before),repr(after),flush=True)
        check(after[:-1]==before[:-1],'one Undo did not restore component scene')
        check('mesh.triangulate' in repr(after[-1]),'successful triangulate missing from Recent')
        # Target title comes from the pointer object while live selection commands retain their own selection scope.
        setup('object')
        active=bpy.context.active_object;active.name='ActiveA';active.location.x=-2
        with override():bpy.ops.mesh.primitive_cube_add(location=(2,0,0))
        target=bpy.context.active_object;target.name='PointerB';target.select_set(False)
        active.select_set(True);bpy.context.view_layer.objects.active=active
        yield from settle(7)
        uv=location_3d_to_region_2d(region,region.data,Vector((2,0,1)))
        point=(region.x+uv.x,region.y+uv.y)
        expected=tuple('PointerB...' if x=='AuditMesh...' else x for x in COMPONENT)
        before=state();yield from begin('component',point)
        picture=capture('state-pointer-title');rect=companion_rect(picture)
        locate(picture,rect,'PointerB...');yield from finish('component')
        check(state()==before,'pointer title/open/cancel selected the target')
        yield from begin('component',point)
        picture,rect,row=yield from browse('component',expected,'state-pointer-invert',stop='Invert Selection')
        event('MOUSEMOVE','NOTHING',(row[1],row[2]));yield from finish('component',False)
        check(not active.select_get() and target.select_get(),'Invert Selection preselected pointer before executing')
        target.select_set(False);bpy.context.view_layer.objects.active=active
        yield from settle(4);before=state();yield from begin('component',point)
        picture,rect,row=yield from browse('component',expected,'state-pointer-deselect',stop='Deselect All')
        event('MOUSEMOVE','NOTHING',(row[1],row[2]));yield from finish('component',False)
        check(state()==before,'Deselect All committed pointer selection')
        # Explicit On/Off must remain idempotent across two actual clicks each.
        setup('object')
        with override():
            for obj in tuple(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
        yield from settle(5)
        create=('Platonic Solid +O','Pyramid +O','Prism +O','Pipe +O','Helix +O','Gear +O','Soccer Ball +O','|',
                'Super Ellipse +O','Spherical Harmonics +O','Ultra Shape +O','Type','SVG','Quad Draw Tool +O','|',
                'Interactive Creation','Exit On Completion','|','Polygon Display All')
        initial_culling=area.spaces.active.shading.show_backface_culling
        for value in (True,True,False,False):
            yield from begin('create')
            rect=yield from hover_row('create',create,'Polygon Display All','state-create-culling-'+str(value))
            picture,child,texts=child_labels(rect,('Backface Culling on for All Polys','Backface Culling off for All Polys'),
                                            'state-create-culling-child-'+str(value))
            text=texts[0 if value else 1]
            event('MOUSEMOVE','NOTHING',((text[0]+text[2])/2,(text[1]+text[3])/2),shift=True)
            yield from finish('create',False)
            check(area.spaces.active.shading.show_backface_culling==value,'explicit culling action is not idempotent')
            check(not bpy.context.scene.objects,'display action created an object')
        area.spaces.active.shading.show_backface_culling=initial_culling
        print('AXISMELD_MAYA_CONTENT_STATE_EVENTS_PASS',flush=True)

    if os.environ.get('AXISMELD_TEST_SUITE')=='maya-content-state':
        yield from state_cases()
        return

    setup();yield from settle(6)
    for requested_scale in (1.0,2.0):
        bpy.context.preferences.view.ui_scale=requested_scale;yield from settle(9)
        scale=bpy.context.preferences.system.ui_scale
        region=next(r for r in area.regions if r.type=='WINDOW')
        base=yield from reference('content-'+str(requested_scale))
        # Full inventory at1x;2x repeats every ring and the longest companion.
        for kind in ('vertex','edge','face','component','Q','W','E','R'):
            setup(kind if kind in MODEL else 'vertex');yield from settle(5)
            before=state();yield from begin(kind)
            picture=capture('content-'+str(requested_scale)+'-'+kind+'-root')
            actual=radial_rectangles(picture, {'N','NE','E','SE','S','SW','W'} if kind=='component' else None)
            check_edges(actual,base,kind)
            if kind=='Q':
                label,_=locate(picture,(region.x,region.y,region.x+region.width,region.y+region.height),'Automatic Camera-Based Selection')
                check(label[3]<min(r[1] for r in actual.values()),'Q companion must be below actual ring')
            elif requested_scale==1.0 or kind=='face':
                yield from browse(kind,MODEL.get(kind,COMPONENT if kind=='component' else TOOLS.get(kind)),
                                  'content-'+str(requested_scale)+'-'+kind)
            yield from finish(kind)
            check(state()==before,'opening/paging/cancel changed scene or Recent '+kind)
        print('PASS full content and actual Views geometry',requested_scale,flush=True)
    print('AXISMELD_MAYA_CONTENT_UI_EVENTS_PASS',flush=True)

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

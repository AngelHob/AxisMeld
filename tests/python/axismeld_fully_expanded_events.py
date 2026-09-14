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
        # Disabled narrow caps SVG/CVs lose low-alpha antialias pixels under
        # the observed RGB threshold. Their .60 alpha template retains the same
        # full-label F1>.75 gate (SVG .93069 on preserved screenshot).
        # Narrow labels can be disconnected from their semantic icon by the
        # band classifier. Recover only a complete >=.75 font-template match
        # on an otherwise unclaimed baseline; never synthesize missing text.
        for label in labels:
            if any(row[0]==label for row in matches):
                continue
            raster_alpha=.6 if label in {'SVG','CVs'} else .35
            match=locate(pixels,rect,label,required=False,raster_alpha=raster_alpha)
            if match is not None:
                bounds,score=match
                key=(scale,label) if raster_alpha==.35 else (scale,label,raster_alpha)
                cy=bounds[1]-template_baselines[key]+4*scale
                if not any(abs(row[2]-cy)<6*scale for row in matches):
                    print('FULL_LABEL_RECOVERED',label,bounds,score,flush=True)
                    matches.append((label,(x0+x1)/2,cy,score))
        return sorted(matches, key=lambda item: -item[2])

    object_labels=('Offset Edge Loop Tool','Smooth','Unsmooth','Subdiv Proxy','Crease Tool',
                   'Project Curve on mesh','Split mesh with projected curve','Mirror','Mapping',
                   'Triangulate','Quadrangulate','Reduce','Remesh','Retopologize','Transfer Vertex Order',
                   'Separate','Combine','Booleans','Cleanup...','Connect Tool','Quad Draw Tool','Polygon Display')
    create_labels=('Platonic Solid','Pyramid','Prism','Pipe','Helix','Gear','Soccer Ball',
                   'Super Ellipse','Spherical Harmonics','Ultra Shape','Type','SVG','Quad Draw Tool',
                   'Interactive Creation','Exit On Completion','Polygon Display All')
    component_labels=('AuditMesh...','Select','Select All','Deselect All','Select Hierarchy','Invert Selection',
                      'Select Similar','Make Live','DG Traversal','Inputs','Outputs','Paint','Metadata','Actions',
                      'UV Sets','Color Sets','Time Editor','Scene Assembly','Material Attributes...',
                      'Assign New Material','Assign Favorite Material','Assign Existing Material')
    face_labels=('Smart Extrude','Smooth Faces','Assign Invisible Faces','Add Divisions To Faces',
                 'Circularize Components','Connect Components','Detach Components','Triangulate Faces',
                 'Quadrangulate Faces','Reduce Faces','Remesh','Bridge Faces','Mirror','Extract Faces',
                 'Duplicate Face','Transform Component','Connect Tool','Target Weld Tool','Mapping','Polygon Display')
    w_labels=('Selection Constraints','Transform Constraints','Shift Extrude','Shift Duplicate',
              'Preserve UVs','Preserve Children','Tweak Mode','Update Triad','Move Options')
    from axismeld import hotbox_runtime
    import bmesh
    def scene_state():
        meshes=[]
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH':continue
            if obj.mode=='EDIT':
                bm=bmesh.from_edit_mesh(obj.data)
                mesh=(tuple((tuple(v.co),v.select,v.hide) for v in bm.verts),
                      tuple((e.select,e.hide) for e in bm.edges),
                      tuple((f.select,f.hide,len(f.verts)) for f in bm.faces))
            else:
                mesh=(tuple((tuple(v.co),v.select,v.hide) for v in obj.data.vertices),
                      tuple((tuple(e.vertices),e.select,e.hide) for e in obj.data.edges),
                      tuple((tuple(f.vertices),f.select,f.hide) for f in obj.data.polygons))
            meshes.append((obj.name,mesh))
        return (bpy.context.mode,tuple(bpy.context.tool_settings.mesh_select_mode),
                bpy.context.active_object.name if bpy.context.active_object else None,
                tuple((o.name,o.select_get(),tuple(tuple(r) for r in o.matrix_world),len(o.modifiers))
                      for o in bpy.context.scene.objects),tuple(meshes),hotbox_runtime.recent.items())
    def view_state():
        return tuple((r.as_pointer(),r.data.view_distance,tuple(r.data.view_location),tuple(r.data.view_rotation))
                     for r in area.regions if r.type=='WINDOW' and r.data)
    failures=[]
    observations=[]
    for kind,labels,low_y in ((k,l,y) for y in (100,300)
                             for k,l in (('object',object_labels),('create',create_labels),
                                         ('component',component_labels),('face',face_labels),('W',w_labels))):
        with override():
            if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
            for obj in tuple(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
            if kind!='create':
                bpy.ops.mesh.primitive_cube_add()
                bpy.context.active_object.name='AuditMesh'
            if kind=='face':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='SELECT')
        yield from settle(7)
        origin[:]=[region.x+region.width/2,region.y+low_y*scale]
        event('MOUSEMOVE','NOTHING',origin)
        shift=kind in ('object','create','face')
        if shift:event('LEFT_SHIFT',shift=True)
        elif kind=='W':event('W');yield from settle(12)
        event('LEFTMOUSE' if kind=='W' else 'RIGHTMOUSE',shift=shift)
        yield from settle(9)
        check([op.bl_idname for op in win.modal_operators].count('VIEW3D_OT_axismeld_hotbox')==1,
              'one native session required '+kind)
        before=scene_state()
        picture=capture('fully-expanded-low-'+str(low_y)+'-'+kind)
        rect=companion_rect(picture,minimum_height=30,min_width=80)
        rows=rendered_rows(picture,rect,labels)
        visible=tuple(row[0] for row in rows)
        missing=tuple(label for label in labels if label not in visible)
        duplicates=tuple(label for label in labels if visible.count(label)>1)
        isolated=picture.copy()
        xa,ya,xb,yb=map(int,rect);isolated[ya:yb,xa:xb,:]=0
        south_label={'object':'Extrude','create':'Cube','component':'Face','face':'Extrude Face','W':'Select'}[kind]
        south=tuple(map(int,locate(isolated,(region.x+region.width/2-400*scale,region.y,region.x+region.width/2+400*scale,region.y+region.height-80*scale),south_label)[0]))
        below_ring=bool(rect[3]<south[1])
        bottom_clearance=(rect[1]-region.y)/scale
        bottom_aligned=0<=bottom_clearance<=16
        # Unlabelled leading/trailing bands expose visible page controls from
        # screenshot geometry; no runtime layout/readback fields are consulted.
        head_gap=(rect[3]-rows[0][2])/scale if rows else None
        tail_gap=(rows[-1][2]-rect[1])/scale if rows else None
        paging_bands=bool(rows and (head_gap>26 or tail_gap>26))
        record={'source':kind,'origin':tuple(origin),'region':(region.x,region.y,region.width,region.height),
                'window':(win.width,win.height),'scale':scale,'actual_list_bounds':rect,
                'bottom_clearance':bottom_clearance,'bottom_aligned':bottom_aligned,
                'south_label_bounds':south,'list_below_ring':below_ring,'visible':visible,'missing':missing,'duplicates':duplicates,
                'top_unlabelled_band':head_gap,'bottom_unlabelled_band':tail_gap,'paging_bands':paging_bands}
        observations.append(record)
        print('FULLY_EXPANDED_OBSERVED',repr(record),flush=True)
        if missing or duplicates or paging_bands or not below_ring or not bottom_aligned:
            failures.append((kind,missing,duplicates,paging_bands,below_ring,bottom_clearance))
        complete=not (missing or duplicates or paging_bands or not below_ring or not bottom_aligned)
        if complete:
            # Wheel must neither scroll the complete menu nor zoom the source view.
            before_view=view_state()
            wheel_row=rows[4] if kind=='W' else rows[0]
            event('MOUSEMOVE','NOTHING',(wheel_row[1],wheel_row[2]),shift=shift)
            event('WHEELDOWNMOUSE',shift=shift);event('WHEELUPMOUSE',shift=shift)
            yield from settle(7)
            after_picture=capture('fully-expanded-wheel-'+str(low_y)+'-'+kind)
            after_rect=companion_rect(after_picture,minimum_height=30,min_width=80)
            check(tuple(r[0] for r in rendered_rows(after_picture,after_rect,labels))==visible and after_rect==rect,
                  'wheel changed complete menu contents or placement '+kind)
            check(view_state()==before_view and scene_state()==before,'wheel leaked to original viewport '+kind)
            # Physical press position remains a cancellation return target even
            # if the complete translated menu now covers that coordinate.
            event('MOUSEMOVE','NOTHING',origin,shift=shift)
            yield from settle(4)
        else:
            event('ESC',shift=shift);event('ESC','RELEASE',shift=shift)
        event('LEFTMOUSE' if kind=='W' else 'RIGHTMOUSE','RELEASE',shift=shift)
        if shift:event('LEFT_SHIFT','RELEASE')
        elif kind=='W':event('W','RELEASE')
        yield from settle(7)
        check(not list(win.modal_operators),'cancel/release left handler '+kind)
        check(scene_state()==before,'physical origin cancel changed scene/selection/Recent '+kind)
    import json
    (artifacts/'observations.json').write_text(json.dumps(observations,indent=2))
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
        return sorted(result,key=lambda r:r[0])

    # Explicit synthetic overflow pressure: this is not the Maya Display tree.
    display_labels=tuple('Pressure item %02d for full menu layout' % i for i in range(1,57))
    original_snapshot=hotbox_runtime.snapshot
    import json
    def pressure_snapshot(context):
        document=json.loads(original_snapshot(context))
        pending=list(document['menus'])
        while pending:
            node=pending.pop()
            if node['id']=='common.display':
                node['label']='Layout Pressure'
                node['children']=[{'id':'test.pressure.%02d'%i,'kind':'disabled','label':label,
                    'enabled':False,'reason':'Synthetic layout pressure fixture','command':'','children':[]}
                    for i,label in enumerate(display_labels)]
            pending.extend(node.get('children',[]))
        return json.dumps(document)
    hotbox_runtime.snapshot=pressure_snapshot
    with override():
        hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
            'style':'rows','rows':['common'],'transparency':0}})
    origin[:]=[region.x+region.width/2,region.y+region.height/2]
    event('MOUSEMOVE','NOTHING',origin);event('SPACE');yield from settle(12)
    primary=capture('fully-expanded-synthetic-pressure-parent')
    label=locate(primary,(region.x,region.y,region.x+region.width,region.y+region.height),'Layout Pressure')[0]
    event('MOUSEMOVE','NOTHING',((label[0]+label[2])/2,(label[1]+label[3])/2));event('LEFTMOUSE')
    yield from settle(9)
    picture=capture('fully-expanded-synthetic-pressure-columns')
    actual_columns=columns(picture)
    check(len(actual_columns)>=2,'Synthetic56 must visibly use multiple complete columns')
    actual_sequence=[]
    for rect in actual_columns:
        rows=rendered_rows(picture,rect,display_labels)
        check(rows,'empty/unreadable actual synthetic pressure column')
        check((rect[3]-rows[0][2])/scale<=26 and (rows[-1][2]-rect[1])/scale<=26,
              'Display column has a paging or artificial Back band')
        actual_sequence.extend(row[0] for row in rows)
    check(tuple(actual_sequence)==display_labels,'Synthetic56 row order/multiplicity differs: '+repr(actual_sequence))
    print('FULL_DISPLAY_COLUMNS',actual_columns,'count',len(actual_sequence),flush=True)
    before_view=view_state();before=scene_state()
    event('MOUSEMOVE','NOTHING',((actual_columns[0][0]+actual_columns[0][2])/2,
                               (actual_columns[0][1]+actual_columns[0][3])/2))
    event('WHEELDOWNMOUSE');event('WHEELUPMOUSE');yield from settle(6)
    after=capture('fully-expanded-synthetic-pressure-wheel')
    after_columns=columns(after)
    check(after_columns==actual_columns and tuple(row[0] for rect in after_columns
          for row in rendered_rows(after,rect,display_labels))==display_labels,'Display wheel paged its contents')
    check(view_state()==before_view and scene_state()==before,'Display wheel leaked to scene/source view')
    event('ESC');event('ESC','RELEASE');event('LEFTMOUSE','RELEASE');event('SPACE','RELEASE')
    yield from settle(7);check(not list(win.modal_operators),'Synthetic pressure cancellation retained ownership')
    hotbox_runtime.snapshot=original_snapshot

    def actual_buttons(pixels,labels):
        from axismeld_hotbox_image_fixture import observed_radial_rectangles
        if labels is views_labels:
            candidates=observed_radial_rectangles(pixels,scale,{'N','NW','W','E','SW','SE','S'})['rects']
        else:
            from itertools import product
            from axismeld_hotbox_image_fixture import observed_menu_rectangles,menu_background_mask
            boxes=[r for r in observed_menu_rectangles(menu_background_mask(pixels),35*scale,13*scale)
                   if r[3]-r[1]<=27*scale]
            # Match complete glyphs inside actual short backgrounds, then require
            # a unique three-row side constellation. The unrelated viewport
            # title may touch North; it is not one of the six measured edges.
            choices={d:[r for r in boxes if locate(pixels,r,label,required=False) is not None]
                     for d,label in labels.items()}
            constellations=[]
            directions=tuple(labels)
            for values in product(*(choices[d] for d in directions)):
                c=dict(zip(directions,values))
                if len(set(values))!=6:continue
                cy=lambda d:(c[d][1]+c[d][3])/2
                if any(abs(cy(l)-cy(r))>3*scale or c[l][2]>=c[r][0]
                       for l,r in (('NW','NE'),('W','E'),('SW','SE'))):continue
                upper=cy('NW')-cy('W');lower=cy('W')-cy('SW')
                if not (20*scale<upper<45*scale and abs(upper-lower)<=3*scale):continue
                if abs(c['NW'][2]-c['SW'][2])>3*scale:continue
                if abs(c['NE'][0]-c['SE'][0])>3*scale:continue
                constellations.append(c)
            check(len(constellations)==1,'Expected unique labelled side constellation '+repr(constellations))
            candidates=constellations[0]
        found={}
        for direction,names in labels.items():
            rect=candidates[direction]
            names=names if isinstance(names,tuple) else (names,)
            matches=[locate(pixels,rect,name,required=False) for name in names]
            check(any(match is not None for match in matches),
                  'actual constellation button lacks full label '+repr((direction,names,rect)))
            found[direction]=rect
        return found
    views_labels={'NW':('Left View','Left'),'W':('Top View','Top'),'E':('Right View','Side'),
                  'SW':('Back View','Back'),'SE':('Bottom View','Bottom')}
    tool_labels={'Q':{'NW':'Marquee','NE':'Drag','W':'Paint Select','E':'Camera-Based Selection',
                      'SW':'Lasso','SE':'Clear Selection'},
                 'W':{'NW':'Object','NE':'Component','W':'World','E':'Snap','SW':'Axis','SE':'Keep Spacing'},
                 'E':{'NW':'Object','NE':'Component','W':'World','E':'Gimbal','SW':'Custom','SE':'Discrete Rotate'},
                 'R':{'NW':'Object','NE':'Component','W':'World','E':'Snap Scale','SW':'Axis','SE':'Relative'}}
    with override():
        hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
            'style':'center','rows':[],'center_buttons':{'LEFTMOUSE':'views'},'transparency':0}})
        bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
    yield from settle(8)
    bpy.context.preferences.view.ui_scale=2.0;yield from settle(10)
    scale=bpy.context.preferences.system.ui_scale
    region=min((r for r in area.regions if r.type=='WINDOW'),key=lambda r:(r.y,r.x))
    origin[:]=[region.x+region.width/2,region.y+region.height/2]
    source_bounds=(region.x,region.y,region.x+region.width,region.y+region.height)
    print('FULL_QUAD_SOURCE',source_bounds,'window',(win.width,win.height),'scale',scale,flush=True)
    event('MOUSEMOVE','NOTHING',origin);event('SPACE');yield from settle(12)
    event('LEFTMOUSE');yield from settle(9)
    reference=actual_buttons(capture('fully-expanded-quad2-views'),views_labels)
    event('MOUSEMOVE','NOTHING',origin);event('LEFTMOUSE','RELEASE');event('SPACE','RELEASE')
    yield from settle(7);check(not list(win.modal_operators),'quad Views cancellation retained owner')
    for key in ('Q','W','E','R'):
        event('MOUSEMOVE','NOTHING',origin);event(key);yield from settle(12)
        before=scene_state()
        for repeat in range(2):
            event('LEFTMOUSE');yield from settle(9)
            picture=capture('fully-expanded-quad2-'+key+'-'+str(repeat))
            ring=actual_buttons(picture,tool_labels[key])
            gaps=[]
            for left,right in (('NW','NE'),('W','E'),('SW','SE')):
                a=ring[right][0]-ring[left][2]-1
                rl,rr=(left,right) if right in reference else ('SW','SE')
                b=reference[rr][0]-reference[rl][2]-1
                check(abs(a-b)<=3*scale,'actual quad tool inner edges differ from Views '+repr((key,left,a,b)))
                gaps.append((a,b))
            if key=='W':
                menu_columns=columns(picture)
                sequence=tuple(row[0] for rect in menu_columns for row in rendered_rows(picture,rect,w_labels))
                check(sequence==w_labels,'quad W must show all9 direct entries at once')
                all_rects=(*ring.values(),*menu_columns)
                check(any(r[0]<source_bounds[0] or r[1]<source_bounds[1] or
                          r[2]>source_bounds[2] or r[3]>source_bounds[3] for r in all_rects),
                      'quad W did not actually cross its source pane')
                before_views=view_state()
                rect=menu_columns[0]
                event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2))
                event('WHEELDOWNMOUSE');event('WHEELUPMOUSE');yield from settle(5)
                check(view_state()==before_views,'cross-pane wheel reached an underlying view')
            print('FULL_QUAD_ACTUAL_EDGES',key,repeat,gaps,flush=True)
            event('MOUSEMOVE','NOTHING',origin);yield from settle(3)
            event('LEFTMOUSE','RELEASE');yield from settle(6)
            check(scene_state()==before,'translated source-origin return dispatched an item '+key)
        event(key,'RELEASE');yield from settle(7)
        check(not list(win.modal_operators),'repeated QWER release retained owner '+key)
    # Dispatch through actual displayed Views text; the captured source pane's
    # rotation changes while all three other pane rotations remain unchanged.
    before_rotations={r.as_pointer():tuple(r.data.view_rotation) for r in area.regions if r.type=='WINDOW'}
    source_pointer=region.as_pointer()
    event('MOUSEMOVE','NOTHING',origin);event('SPACE');yield from settle(12)
    event('LEFTMOUSE');yield from settle(8)
    target=actual_buttons(capture('fully-expanded-quad-source-command'),views_labels)['W']
    event('MOUSEMOVE','NOTHING',((target[0]+target[2])/2,(target[1]+target[3])/2))
    yield from settle(3);event('LEFTMOUSE','RELEASE');event('SPACE','RELEASE');yield from settle(8)
    after_rotations={r.as_pointer():tuple(r.data.view_rotation) for r in area.regions if r.type=='WINDOW'}
    check(after_rotations[source_pointer]!=before_rotations[source_pointer],'Top command did not affect captured source pane')
    check(all(after_rotations[p]==q for p,q in before_rotations.items() if p!=source_pointer),
          'captured Views command affected another pane')
    check(not list(win.modal_operators),'source command retained modal owner')
    print('FULL_QUAD_SOURCE_DISPATCH_PASS',source_pointer,flush=True)
    check(not failures,'menus must show every main row without pagination: '+repr(failures))
    print('AXISMELD_FULLY_EXPANDED_UI_EVENTS_PASS',flush=True)

steps=suite()
def tick():
    try:
        next(steps)
        return .025
    except StopIteration:bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

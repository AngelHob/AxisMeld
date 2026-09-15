# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded real-input acceptance of Maya menubar chapter corrections."""
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
PHASE = 'alignment'
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False

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
    resources={}
    scriptroot=Path(bpy.utils.system_resource('SCRIPTS'))
    paths=list((scriptroot/'modules/axismeld').glob('*.py'))
    paths += [scriptroot/'startup/bl_ui'/n for n in ('space_axismeld_menubar.py','space_topbar.py','__init__.py')]
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
    def locate(pixels,label,rect,allowed_rectangles=None,prefer_left=False):
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
        ink=np.min(pixels[y0:y1,x0:x1,:3],axis=2)>(.55 if label=='Save As' else .18)
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
        event('MOUSEMOVE','NOTHING',*point)
        event('LEFTMOUSE','PRESS',*point);event('LEFTMOUSE','RELEASE',*point)

    def popup_after(before, tag):
        pixels=shot(tag)
        scale=bpy.context.preferences.system.ui_scale
        changed=np.max(np.abs(pixels[:,:,:3]-before[:,:,:3]),axis=2)>.004
        boxes=observed_menu_rectangles((np.max(pixels[:,:,:3],axis=2)<.15)&changed,100*scale,30*scale)
        assert boxes,('No actual changed popup',tag)
        print('ACTUAL_POPUP_BOUNDS',tag,boxes,flush=True)
        return pixels,boxes
    def open_path(labels,tag):
        before=shot(tag+'-before')
        scale=bpy.context.preferences.system.ui_scale
        click(locate(before,labels[0],(95*scale,win.height-26*scale,win.width,win.height),prefer_left=True))
        yield from settle(10)
        pixels,boxes=popup_after(before,tag+'-root')
        for index,label in enumerate(labels[1:]):
            point=locate(pixels,label,(0,0,win.width,win.height-26*scale),boxes)
            # Keep the pre-menu baseline: child popups can overlap the parent
            # with identical background color, so parent-vs-child diff clips labels.
            event('MOUSEMOVE','NOTHING',*point)
            yield from settle(14)
            pixels,boxes=popup_after(before,tag+'-child-'+str(index))
        return pixels,boxes
    def ordered(pixels,boxes,labels):
        positions={}
        lefts={}
        scale=bpy.context.preferences.system.ui_scale
        for label in labels:
            point=locate(pixels,label,(0,0,win.width,win.height-26),boxes)
            assert any(b[0]<point[0]<b[2] and b[1]<point[1]<b[3] for b in boxes)
            positions[label]=point
            lefts[label]=point[0]-templates[(scale,label)].shape[1]/2
        # Native popup columns share a continuous background. Observe caption
        # start bands instead of treating the entire connected popup as one col.
        # Semantic/state slots may indent a caption by up to 20 physical pixels.
        starts=[]
        for x in sorted(lefts.values()):
            if not starts or x-starts[-1]>40*scale:starts.append(x)
        previous=None
        for label in labels:
            column=min(range(len(starts)),key=lambda i:abs(lefts[label]-starts[i]))
            order=(column,-positions[label][1])
            assert previous is None or order>previous,('Wrong visible chapter order',labels,label,previous,order)
            previous=order
        print('ACTUAL_CHAPTER_SEQUENCE',labels,positions,flush=True)
        return positions
    def close():
        for _ in range(4):
            event('ESC');yield from settle(2)
    def node_path(labels):
        candidates=[n for n in ui._CATALOG['menus'] if n['label']==labels[0]]
        assert len(candidates)==1,labels
        current=candidates[0]
        for label in labels[1:]:
            matches=[n for n in current.get('children',()) if n['label']==label]
            assert len(matches)==1,(labels,label,len(matches))
            current=matches[0]
        return current
    def scene_state():
        import bmesh
        result=[]
        for obj in bpy.context.scene.objects:
            mesh=None
            if obj.type=='MESH':
                if obj.mode=='EDIT':
                    bm=bmesh.from_edit_mesh(obj.data)
                    mesh=(tuple((tuple(v.co),v.select,v.hide) for v in bm.verts),tuple((len(e.verts),e.select,e.hide) for e in bm.edges),tuple((len(f.verts),f.select,f.hide) for f in bm.faces))
                else:mesh=(tuple((tuple(v.co),v.select,v.hide) for v in obj.data.vertices),tuple((tuple(e.vertices),e.select,e.hide) for e in obj.data.edges),tuple((tuple(f.vertices),f.select,f.hide) for f in obj.data.polygons))
            result.append((obj.name,obj.type,obj.mode,obj.select_get(),tuple(tuple(r) for r in obj.matrix_world),mesh))
        active=bpy.context.view_layer.objects.active
        return (tuple(result),active.name if active else None)
    yield from settle(12)
    preset=next(Path(p)/'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    yield from settle(12)
    assert ui.enabled(bpy.context)
    # Explicit chapter expectations are filled from the approved correction,
    # never inferred from the product's SECTION_ANCHORS or registry.
    for title,sequence in CHAPTERS:
        pixels,boxes=yield from open_path((title,),'chapter-'+title.replace(' ','-'))
        ordered(pixels,boxes,sequence)
        yield from close()
    for path,sequence,tag in (
        (('File',),('Save Preferences','Save and Recover','References'),'save-adjacency'),
        (('Create','Polygon Primitives'),('Soccer Ball','Additional Primitives','Subdivision Primitives','Super Shapes'),'primitive-adjacency'),
    ):
        pixels,boxes=yield from open_path(path,tag)
        ordered(pixels,boxes,sequence)
        yield from close()
    naming=('Modify','Naming Tools')
    names=('Rename Active Item...','Batch Rename...')
    assert tuple(n['label'] for n in node_path(naming)['children'])==names
    pixels,boxes=yield from open_path(naming,'naming-unique')
    ordered(pixels,boxes,names)
    yield from close()
    print('ACTUAL_NAMING_UNIQUE_PASS',flush=True)
    # Both Object and Edit modes expose the historical semantic mismatch.
    view=next(a for a in win.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in view.regions if r.type=='WINDOW')
    for mode in ('OBJECT','EDIT'):
        with bpy.context.temp_override(window=win,area=view,region=region):
            bpy.ops.object.mode_set(mode=mode)
        yield from settle(6)
        for path in (('Edit','Duplicate Special'),('Modify','Snap Align Objects','Point to Point')):
            node=node_path(path)
            assert node['kind']=='disabled' and not node.get('command'),(path,node)
            before=scene_state();calls=len(executed)
            pixels,boxes=yield from open_path(path[:-1],'disabled-'+mode+'-'+path[-1].replace(' ','-'))
            point=locate(pixels,path[-1],(0,0,win.width,win.height-26),boxes)
            click(point);yield from settle(8)
            assert scene_state()==before and len(executed)==calls,(mode,path,'disabled click mutated scene or executed')
            shot('disabled-after-'+mode+'-'+path[-1].replace(' ','-'))
            yield from close()
    with bpy.context.temp_override(window=win,area=view,region=region):bpy.ops.object.mode_set(mode='OBJECT')
    print('ACTUAL_DISABLED_SEMANTICS_PASS',flush=True)
    workspace_path=('Windows','Workspaces')
    tree=node_path(workspace_path)
    placeholders=[n for n in tree['children'] if n['label'] in WORKSPACES]
    assert tuple(n['label'] for n in placeholders)==WORKSPACES and all(n['kind']=='disabled' for n in placeholders)
    pixels,boxes=yield from open_path(workspace_path,'workspace-placeholders')
    positions=ordered(pixels,boxes,('Factory Workspaces',)+WORKSPACES+('Blender Workspaces','Switch Workspace'))
    original=win.workspace.as_pointer();before=scene_state();calls=len(executed)
    for name in ('General','Bifrost Fluids'):
        click(positions[name]);yield from settle(6)
        assert win.workspace.as_pointer()==original and scene_state()==before and len(executed)==calls
    yield from close()
    pixels,boxes=yield from open_path(workspace_path+('Switch Workspace',),'workspace-native-switch')
    point=locate(pixels,'Next Workspace',(0,0,win.width,win.height-26),boxes)
    click(point);yield from settle(14)
    assert win.workspace.as_pointer()!=original,'Real native Next Workspace did not switch'
    yield from close()
    pixels,boxes=yield from open_path(workspace_path+('Switch Workspace',),'workspace-native-return')
    point=locate(pixels,'Previous Workspace',(0,0,win.width,win.height-26),boxes)
    click(point);yield from settle(14)
    assert win.workspace.as_pointer()==original,'Native Previous Workspace did not restore source workspace'
    print('ACTUAL_WORKSPACE_PLACEHOLDERS_SWITCH_PASS',flush=True)
    print('AXISMELD_MENUBAR_ALIGNMENT_PASS',flush=True)

# Approved independent UI expectations (not product-generated).
CHAPTERS = (
    ('Select', ('Object Relationships','Linked Objects','Pattern','Type','Polygons','Mesh Components','Similarity Filters','NURBS Curves','Curve and Surface Points','NURBS Surfaces','Universal Scene Description')),
    ('Modify', ('Transform','Proportional Editing','Apply Transformations','Transform Deltas','Object Origin','Align','Rotate Order','Rotation Order','Nodes','Naming','Naming Tools','Attributes','Assets')),
    ('Display', ('Viewport Settings','Object','Component Display')),
    ('Mesh', ('Combine Tools','Element Order','Cleanup Tools','Blender Modifiers','Modifiers')),
    ('Edit Mesh', ('Extrusion Tools','Merge Tools','Interactive Topology','Vertex','Edge','Face','Face Boolean','Curve')),
    ('Mesh Tools', ('Immediate Tools',)),
    ('Mesh Display', ('Average Normal Tools','Edit Normals','Face Strength','Shading','Normal Modifiers','Vertex Color Sets','Display Attributes','Viewport Analysis','Data Marks')),
    ('Curves', ('Modify','Geometry','Edit','Bezier Handles','Spline Type','Control Points','Topology')),
    ('Surfaces', ('Create','Construct','Edit NURBS Surfaces','Geometry','Topology','Control Points')),
    ('Deform', ('Create','Blender Deformers','Edit','Binding','Hook Transforms','Intermediate Objects','Weights','Vertex Groups','Deformer Sets (legacy)','Blender Hook Membership')),
)
WORKSPACES = ('General','Modeling - Standard','Modeling - Expert','Sculpting','Pose Sculpting','UV Editing','XGen','XGen - Interactive Groom','Rigging','Animation','Rendering - Standard','Rendering - Expert','MASH','Motion Graphics','Bifrost Fluids')
steps=suite()
def tick():
    try:
        next(steps);return .04
    except StopIteration:bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
bpy.app.timers.register(tick,first_interval=1)

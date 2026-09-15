# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise built-in Rigify through native GUI in a disposable factory process.

Run with ordinary Python: --blender PATH --artifacts DIR --verification JSON.
No add-on enable call or user preferences write is performed by this test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender',required=True)
    parser.add_argument('--artifacts',required=True)
    parser.add_argument('--verification',required=True)
    args=parser.parse_args()
    art=Path(args.artifacts).resolve();art.mkdir(parents=True,exist_ok=True)
    isolated=Path(tempfile.mkdtemp(prefix='isolated-',dir=art))
    env=os.environ.copy()
    for name in ('config','scripts','tmp'):(isolated/name).mkdir()
    env.update(BLENDER_USER_CONFIG=str(isolated/'config'),BLENDER_USER_SCRIPTS=str(isolated/'scripts'),
               TEMP=str(isolated/'tmp'),TMP=str(isolated/'tmp'),TMPDIR=str(isolated/'tmp'),
               AXISMELD_TEST_ARTIFACTS=str(art),AXISMELD_TEST_ROOT=str(isolated),
               AXISMELD_RIGIFY_VERIFICATION=str(Path(args.verification).resolve()))
    startup=None
    if sys.platform=='win32':
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    command=[str(Path(args.blender).resolve()),'--factory-startup','--enable-event-simulate','--python-exit-code','1','--python',str(Path(__file__).resolve())]
    result=subprocess.run(command,env=env,startupinfo=startup,capture_output=True,timeout=180)
    (art/'stdout.log').write_bytes(result.stdout);(art/'stderr.log').write_bytes(result.stderr)
    sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    passed=result.returncode==0 and b'AXISMELD_RIGIFY_BUILTIN_GUI_PASS' in result.stdout and b'Traceback (most recent call last):' not in result.stdout+result.stderr
    receipt=dict(status='PASS' if passed else 'FAIL',exit_code=result.returncode or (0 if passed else 1),command=command,artifacts=str(art),isolation=str(isolated),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    evidence=art/'capture-evidence.json'
    if evidence.exists():receipt.update(json.loads(evidence.read_text()))
    (art/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    raise SystemExit(receipt['exit_code'])

try:
    import bpy
except ImportError:
    if __name__=='__main__':run()
else:
    import blf
    import imbuf
    import numpy as np
    sys.path.insert(0,str(Path(__file__).parent))
    from axismeld_hotbox_image_fixture import observed_menu_rectangles
    ART=Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
    ROOT=Path(os.environ['AXISMELD_TEST_ROOT'])
    bpy.context.preferences.use_preferences_save=False
    bpy.context.preferences.view.show_splash=False
    bpy.context.preferences.view.show_tooltips=False


def settle(count=8):
    for _ in range(count):yield


def suite():
    win=bpy.context.window
    expected=json.loads(Path(os.environ['AXISMELD_RIGIFY_VERIFICATION']).read_text(encoding='utf-8-sig'))
    scriptroot=Path(bpy.utils.system_resource('SCRIPTS'))
    resources={}
    for item in expected['resources']:
        path=scriptroot.parent/item['path']
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual==item['sha256'],('Candidate resource drift',str(path),actual,item['sha256'])
        resources[item['path']]=actual
    evidence=dict(exe=bpy.app.binary_path,exe_sha256=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),pid=os.getpid(),
                  resources=resources,resource_fingerprint=hashlib.sha256(json.dumps(resources,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    assert evidence['exe_sha256']==expected['binary_sha256']
    (ART/'capture-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    (ART/'test-source.py').write_bytes(Path(__file__).read_bytes())
    print('RIGIFY_GUI_EVIDENCE',json.dumps({k:v for k,v in evidence.items() if k!='resources'}),flush=True)
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
    def rect(r):
        return (r.x,r.y,r.x+r.width,r.y+r.height)
    def view():
        return max((a for a in win.screen.areas if a.type=='VIEW_3D'),key=lambda a:a.width*a.height)
    def header():return next(r for r in view().regions if r.type=='HEADER')
    def view_menu_rect(pixels):
        bounds=rect(header())
        point=locate(pixels,'View',bounds,prefer_left=True,ink_levels=(.08,.12,.18,.25))
        width=templates[(bpy.context.preferences.system.ui_scale,'View')].shape[1]
        # Editor/mode selectors precede View. Their similar short captions (for
        # example Edit Mode versus Edit Mesh) are not viewport menu roots.
        return (int(point[0]-width/2-1),bounds[1],bounds[2],bounds[3])
    def close():
        for _ in range(4):event('ESC');yield from settle(2)
    def popup(pixels,baseline,tag):
        scale=bpy.context.preferences.system.ui_scale
        changed=np.max(np.abs(pixels[:,:,:3]-baseline[:,:,:3]),axis=2)>.004
        boxes=observed_menu_rectangles((np.max(pixels[:,:,:3],axis=2)<.15)&changed,100*scale,25*scale)
        assert boxes,('No actual native popup',tag)
        return boxes
    def open_path(labels,tag,top=False):
        baseline=shot(tag+'-before')
        source=view_menu_rect(baseline)
        point=locate(baseline,labels[0],source,prefer_left=True,ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(10)
        pixels=shot(tag+'-root');boxes=popup(pixels,baseline,tag)
        print('ACTUAL_MENU_POPUPS',tag,0,boxes,flush=True)
        for i,label in enumerate(labels[1:]):
            point=locate(pixels,label,(0,0,win.width,win.height),boxes)
            event('MOUSEMOVE','NOTHING',*point);yield from settle(14)
            previous=pixels
            pixels=shot(tag+'-child-'+str(i));boxes=popup(pixels,previous,tag)
            # Match the next level only in its newly displayed popup. Parent
            # chapter labels can share a caption, e.g. Curves' Edit heading and
            # Hair Curves > Edit, without representing the same destination.
            print('ACTUAL_MENU_POPUPS',tag,i+1,boxes,flush=True)
        return pixels,boxes
    def activate_path(labels,tag,top=False):
        pixels,boxes=yield from open_path(labels[:-1],tag,top)
        point=locate(pixels,labels[-1],(0,0,win.width,win.height),boxes)
        yield from click(point);yield from settle(12)
    yield from settle(18)
    area=view();region=next(r for r in area.regions if r.type=='WINDOW')
    assert bpy.ops.pose.rigify_generate.get_rna_type()
    assert hasattr(bpy.types.PoseBone,'rigify_type')
    pixels,boxes=yield from open_path(('Add','Armature','Rigify Meta-Rigs','Basic'),'native-add-armature')
    point=locate(pixels,'Basic Human',(0,0,win.width,win.height),boxes)
    yield from click(point);yield from settle(14)
    metarig=bpy.context.active_object
    assert metarig and metarig.type=='ARMATURE' and len(metarig.data.bones)>10
    assert any(b.rigify_type for b in metarig.pose.bones)
    print('NATIVE_ADD_BASIC_HUMAN_PASS',metarig.name,len(metarig.data.bones),flush=True)
    shot('native-basic-human-created')
    # Invoke the existing native Rigify viewport menu, in the same context as
    # creating the metarig. Properties editor zoom has its own font transform.
    yield from activate_path(('Rigify','Generate Rig'),'native-generate-rig')
    yield from settle(20)
    rig=metarig.data.rigify_target_rig
    assert rig is not None and rig!=metarig and len(rig.data.bones)>100
    assert sum(not b.name.startswith(('ORG-','DEF-','MCH-')) for b in rig.data.bones)>10
    shot('native-generated-rig')
    print('NATIVE_GENERATE_RIG_PASS',rig.name,len(rig.data.bones),flush=True)
    # Use the owned factory window's large editor for native Preferences. This
    # avoids resizing/focusing any desktop/user windows and shows whole panels.
    area.type='PREFERENCES'
    bpy.context.preferences.active_section='ANIMATION'
    yield from settle(18)
    pixels=shot('preferences-animation-rigify')
    locate(pixels,'Rigify',rect(area),ink_levels=(.08,.12,.18,.25))
    locate(pixels,'Automatic Rigging',rect(area),ink_levels=(.08,.12,.18,.25))
    locate(pixels,'Feature Sets:',rect(area),ink_levels=(.08,.12,.18,.25))
    locate(pixels,'Install Feature Set from File...',rect(area),ink_levels=(.08,.12,.18,.25,.35,.5))
    print('NATIVE_ANIMATION_RIGIFY_PREFERENCES_PASS',flush=True)
    bpy.context.preferences.active_section='ADDONS'
    bpy.context.preferences.view.show_addons_enabled_only=False
    bpy.context.window_manager.addon_search=''
    yield from settle(18)
    pixels=shot('preferences-addons-all')
    # Positive control: the actual native add-on list is displayed before
    # testing its empty Rigify search result.
    locate(pixels,'Cycles Render Engine',rect(area),ink_levels=(.08,.12,.18,.25))
    bpy.context.window_manager.addon_search='Rigify'
    yield from settle(18)
    pixels=shot('preferences-addons-rigify-search')
    window_region=next(r for r in area.regions if r.type=='WINDOW')
    search=locate(pixels,'Rigify',(area.x+155,area.y+area.height-90,area.x+900,area.y+area.height),ink_levels=(.08,.12,.18,.25))
    content=(window_region.x,window_region.y,window_region.x+window_region.width,int(search[1]-18))
    for label in ('Rigify','Missing Add-ons','Missing Built-in Add-ons','Missing script files'):
        try:locate(pixels,label,content,ink_levels=(.08,.12,.18,.25))
        except AssertionError:pass
        else:raise AssertionError(('Native module incorrectly shown as optional/missing add-on',label))
    import addon_utils
    assert 'rigify' not in [mod.__name__ for mod in addon_utils.modules(refresh=False)]
    assert bpy.context.preferences.addons.get('rigify') is not None,'Compatibility settings storage should remain'
    assert bpy.ops.pose.rigify_generate.get_rna_type()
    print('NATIVE_ADDONS_RIGIFY_HIDDEN_NO_MISSING_PASS',flush=True)
    print('AXISMELD_RIGIFY_BUILTIN_GUI_PASS',flush=True)


if __name__=='__main__' and 'bpy' in globals():
    steps=suite()
    def tick():
        try:
            next(steps);return .04
        except StopIteration:bpy.ops.wm.quit_blender()
        except BaseException:
            traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
    bpy.app.timers.register(tick,first_interval=1)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Skin menu, independent Options, cancellation and single-Undo GUI checks.

Run with ordinary Python: --blender PATH --artifacts DIR [--verification JSON].
The child uses disposable factory preferences. No production operator is called
directly by these acceptance cases; fixture creation and undo checkpoints are
the only scripted scene operations. Automated evidence is not manual acceptance.
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


PASS_MARKER = 'AXISMELD_SKIN_WEIGHT_GUI_PASS'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', required=True)
    parser.add_argument('--artifacts', required=True)
    parser.add_argument('--verification', help='Optional existing candidate resource manifest')
    args = parser.parse_args()
    art = Path(args.artifacts).resolve()
    art.mkdir(parents=True, exist_ok=True)
    isolated = Path(tempfile.mkdtemp(prefix='isolated-', dir=art))
    env = os.environ.copy()
    # Personal resource redirections must not leak into this factory process.
    for key in tuple(env):
        if key.startswith(('BLENDER_USER_', 'AXISMELD_TEST_', 'AXISMELD_SKIN_')):
            env.pop(key)
    for name in ('config', 'scripts', 'tmp'):
        (isolated / name).mkdir()
    env.update(BLENDER_USER_CONFIG=str(isolated / 'config'),
               BLENDER_USER_SCRIPTS=str(isolated / 'scripts'),
               TEMP=str(isolated / 'tmp'), TMP=str(isolated / 'tmp'),
               TMPDIR=str(isolated / 'tmp'),
               AXISMELD_TEST_ARTIFACTS=str(art), AXISMELD_TEST_ROOT=str(isolated))
    if args.verification:
        env['AXISMELD_SKIN_VERIFICATION'] = str(Path(args.verification).resolve())
    startup = None
    if sys.platform == 'win32':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    command = [str(Path(args.blender).resolve()), '--factory-startup',
               '--enable-event-simulate', '--python-exit-code', '1',
               '--python', str(Path(__file__).resolve())]
    try:
        result = subprocess.run(command, env=env, startupinfo=startup,
                                capture_output=True, timeout=240)
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, exit_code = error.stdout or b'', error.stderr or b'', 124
        stderr += b'\nGUI event test timed out after 240 seconds.\n'
    (art / 'stdout.log').write_bytes(stdout)
    (art / 'stderr.log').write_bytes(stderr)
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    passed = (exit_code == 0 and PASS_MARKER.encode() in stdout and
              b'Traceback (most recent call last):' not in stdout + stderr and
              b'ID user decrement error' not in stdout + stderr)
    receipt = dict(status='PASS' if passed else 'FAIL',
                   exit_code=exit_code or (0 if passed else 1),
                   command=command, artifacts=str(art), isolation=str(isolated),
                   test_sha256=sha256(__file__), automated=True,
                   manual_acceptance='not performed')
    evidence = art / 'capture-evidence.json'
    if evidence.exists():
        receipt.update(json.loads(evidence.read_text(encoding='utf-8')))
    receipt['screenshots'] = {p.name: sha256(p) for p in sorted(art.glob('*.png'))}
    (art / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    raise SystemExit(receipt['exit_code'])


try:
    import bpy
except ImportError:
    if __name__ == '__main__':
        run()
else:
    import blf
    import imbuf
    import numpy as np
    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_image_fixture import observed_menu_rectangles
    ART = Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
    ROOT = Path(os.environ['AXISMELD_TEST_ROOT'])
    bpy.context.preferences.use_preferences_save = False
    bpy.context.preferences.view.show_splash = False
    bpy.context.preferences.view.show_tooltips = False


def settle(count=8):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    scriptroot = Path(bpy.utils.system_resource('SCRIPTS'))
    paths = list((scriptroot / 'modules/axismeld').glob('*.py'))
    paths += [scriptroot / 'startup/bl_ui' / name for name in (
        'space_axismeld_menubar.py', 'space_axismeld_native_rigging.py',
        'space_topbar.py', 'space_view3d.py', '__init__.py')]
    resources = {p.relative_to(scriptroot).as_posix(): sha256(p) for p in paths}
    evidence = dict(exe=bpy.app.binary_path, exe_sha256=sha256(bpy.app.binary_path),
                    version=bpy.app.version_string,
                    build_hash=bpy.app.build_hash.decode(errors='replace'),
                    test_sha256=sha256(__file__), pid=os.getpid(), resources=resources,
                    cases=[], automated=True, manual_acceptance='not performed')
    evidence['resource_fingerprint'] = hashlib.sha256(json.dumps(
        resources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if os.environ.get('AXISMELD_SKIN_VERIFICATION'):
        expected = json.loads(Path(os.environ['AXISMELD_SKIN_VERIFICATION']).read_text(
            encoding='utf-8-sig'))
        assert evidence['exe_sha256'] == expected['binary_sha256'], 'Candidate binary drift'
        for item in expected['resources']:
            path = scriptroot.parent / item['path']
            assert sha256(path) == item['sha256'], ('Candidate resource drift', str(path))

    def save_evidence():
        (ART / 'capture-evidence.json').write_text(json.dumps(evidence, indent=2),
                                                 encoding='utf-8')

    save_evidence()
    (ART / 'test-source.py').write_bytes(Path(__file__).read_bytes())
    from bl_ui import space_topbar
    captured = {}
    original_draw = space_topbar.TOPBAR_HT_upper_bar.draw

    def capture_draw(self, context):
        if context.window == win:
            captured['regions'] = [(r.type, r.alignment, r.x, r.y, r.width, r.height)
                                   for r in context.area.regions]
        return original_draw(self, context)

    space_topbar.TOPBAR_HT_upper_bar.draw = capture_draw

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
    cursor = [400, 500]
    def event(kind, value='PRESS', x=None, y=None, **modifiers):
        if x is not None:
            cursor[:] = [int(x), int(y)]
        win.event_simulate(type=kind, value=value, x=cursor[0], y=cursor[1], **modifiers)
    templates={}
    def locate(pixels,label,rect,allowed_rectangles=None,prefer_left=False,ink_levels=None,
               allow_neighbors=False):
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
                    scores.append(locate(pixels,label,rect,allowed_rectangles,prefer_left,level,
                                         allow_neighbors=allow_neighbors))
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
        if allowed_rectangles is not None and not allow_neighbors:
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
    def top_rect():
        r=next(r for r in captured['regions'] if r[0]=='HEADER' and r[1]=='TOP')
        return (r[2],r[3],r[2]+r[4],r[3]+r[5])
    def verify_topbar(tag):
        pixels=shot(tag)
        main=next(r for r in captured['regions'] if r[0]=='WINDOW')
        assert main[5]<=1,('Original Blender topbar must remain one row',captured)
        positions=[locate(pixels,label,top_rect(),prefer_left=True) for label in ('File','Edit','Render','Window','Help')]
        assert all(positions[i][0]<positions[i+1][0] for i in range(len(positions)-1))
        workspace=locate(pixels,win.workspace.name,top_rect(),ink_levels=(.08,.12,.18,.25))
        assert all(abs(point[1]-workspace[1])<4*bpy.context.preferences.system.ui_scale for point in positions)
        return pixels
    def set_config(name):
        preset=next(Path(p)/(name+'.py') for p in bpy.utils.preset_paths('keyconfig') if (Path(p)/(name+'.py')).exists())
        assert bpy.utils.keyconfig_set(str(preset))
        yield from settle(14)
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
        source=top_rect() if top else view_menu_rect(baseline)
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
    def switch_workspace(name):
        pixels=shot('workspace-before-'+name.lower())
        point=locate(pixels,name,top_rect(),ink_levels=(.08,.12,.18,.25))
        yield from click(point);yield from settle(16)
        assert win.workspace.name==name,('Actual workspace click failed',name,win.workspace.name)

    def context():
        area = view()
        return bpy.context.temp_override(window=win, area=area,
                                         region=next(r for r in area.regions if r.type == 'WINDOW'))

    def key(kind, unicode=None, **modifiers):
        kwargs = dict(modifiers)
        if unicode is not None:
            kwargs['unicode'] = unicode
        event(kind, **kwargs)
        yield from settle(2)
        event(kind, 'RELEASE', **modifiers)
        yield from settle(2)

    def snapshot():
        objects = {}
        for name in ('SkinSubject', 'OtherSelected'):
            ob = bpy.data.objects[name]
            objects[name] = {
                'weights': [{ob.vertex_groups[g.group].name: float(g.weight) for g in v.groups}
                            for v in ob.data.vertices],
                'vertex_selection': [v.select for v in ob.data.vertices],
                'vertex_hidden': [v.hide for v in ob.data.vertices],
                'groups': [(g.name, g.lock_weight) for g in ob.vertex_groups],
                'active_group': ob.vertex_groups.active_index,
                'modifiers': [(m.name, m.type, m.object.name if m.type == 'ARMATURE' and m.object
                               else None) for m in ob.modifiers],
                'parent': ob.parent.name if ob.parent else None,
                'matrix': [list(row) for row in ob.matrix_world],
            }
        return dict(objects=objects, selected=sorted(o.name for o in bpy.context.selected_objects),
                    active=bpy.context.view_layer.objects.active.name,
                    mode=bpy.context.mode, workspace=win.workspace.name)

    def assert_expected(before, operation, threshold=0.01, normalize_after=True):
        import copy
        expected = copy.deepcopy(before)
        rows = expected['objects']['SkinSubject']['weights']
        for row in rows[:3]:
            if operation == 'prune':
                for name in ('BoneA', 'BoneB'):
                    if row[name] < threshold:
                        del row[name]
            if operation == 'normalize' or normalize_after:
                total = sum(row.get(name, 0.0) for name in ('BoneA', 'BoneB'))
                for name in ('BoneA', 'BoneB'):
                    if name in row:
                        row[name] = row[name] * (1.0 - row['LockedBone']) / total
        actual = snapshot()
        actual_rows = actual['objects']['SkinSubject'].pop('weights')
        expected_rows = expected['objects']['SkinSubject'].pop('weights')
        assert actual == expected, ('Selection or protected data changed', actual, expected)
        for index, (found, wanted) in enumerate(zip(actual_rows, expected_rows)):
            assert found.keys() == wanted.keys(), (operation, index, found, wanted)
            assert all(abs(found[name] - value) < 2e-6 for name, value in wanted.items()), (
                operation, index, found, wanted)
        assert snapshot() != before, 'A real operation must change fixture weights'

    def checkpoint():
        with context():
            bpy.ops.ed.undo_push(message='Skin GUI acceptance checkpoint')

    def record(name, before, after):
        evidence['cases'].append(dict(name=name, status='PASS', before=before, after=after))
        save_evidence()
        print('SKIN_GUI_CASE_PASS', name, flush=True)

    def undo_once(before, tag):
        yield from activate_path(('Edit', 'Undo'), tag, top=True)
        assert snapshot() == before, ('One native Undo did not restore exact state', tag,
                                      snapshot(), before)
        shot(tag + '-restored')

    def gear(pixels, boxes, label):
        point = locate(pixels, label, (0, 0, win.width, win.height), boxes)
        scale = bpy.context.preferences.system.ui_scale
        box = next(b for b in boxes if b[0] <= point[0] < b[2] and b[1] <= point[1] < b[3])
        label_width = templates[(scale, label)].shape[1]
        rgb = pixels[:, :, :3]
        mask = (np.min(rgb, axis=2) > .18) & (np.max(rgb, axis=2) < .95)
        allowed = np.zeros(mask.shape, dtype=bool)
        x0, x1 = int(point[0] + label_width / 2 + 5 * scale), int(box[2])
        y0, y1 = int(point[1] - 10 * scale), int(point[1] + 10 * scale)
        allowed[y0:y1, x0:x1] = True
        icons = [r for r in observed_menu_rectangles(mask & allowed, 5 * scale, 5 * scale)
                 if r[2] - r[0] < 20 * scale and r[3] - r[1] < 20 * scale]
        assert len(icons) == 1, ('Expected independent Options glyph', label, icons)
        icon = icons[0]
        print('ACTUAL_OPTIONS_GLYPH', label, icon, flush=True)
        return ((icon[0] + icon[2]) / 2, (icon[1] + icon[3]) / 2)

    def open_options(path, tag):
        pixels, boxes = yield from open_path(path[:-1], tag)
        point = gear(pixels, boxes, path[-1])
        yield from click(point)
        yield from settle(12)
        dialog = shot(tag + '-dialog')
        dialog_boxes = popup(dialog, pixels, tag + '-dialog')
        # An independent parameter caption proves the gear did not run the body.
        caption = 'Lock Active' if path[-1] == 'Normalize Weights' else 'Prune Below'
        locate(dialog, caption, (0, 0, win.width, win.height), dialog_boxes,
               ink_levels=(.08, .12, .18, .25, .4, .5), allow_neighbors=True)
        return dialog, dialog_boxes

    def set_threshold(pixels, boxes, value, tag):
        point = locate(pixels, 'Prune Below', (0, 0, win.width, win.height), boxes,
                       ink_levels=(.08, .12, .18, .25, .4, .5), allow_neighbors=True)
        box = next(b for b in boxes if b[0] <= point[0] < b[2] and b[1] <= point[1] < b[3])
        target = (box[2] - 65 * bpy.context.preferences.system.ui_scale, point[1])
        event('MOUSEMOVE', 'NOTHING', *target)
        yield from settle(2)
        event('LEFTMOUSE', 'PRESS', *target, ctrl=True)
        event('LEFTMOUSE', 'RELEASE', *target, ctrl=True)
        yield from settle(3)
        yield from key('A', ctrl=True)
        digit_keys = ('ZERO', 'ONE', 'TWO', 'THREE', 'FOUR',
                      'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE')
        for character in value:
            yield from key('PERIOD' if character == '.' else digit_keys[int(character)],
                           unicode=character)
        yield from key('RET')
        yield from settle(5)
        edited = shot(tag + '-edited')
        # Numeric widgets have a lighter background than menu rows. Keep the
        # same > .75 full-glyph match while trying foreground cuts above it.
        locate(edited, format(float(value), '.4f'),
               (box[0], point[1] - 12, box[2], point[1] + 12),
               ink_levels=(.4, .5, .6), allow_neighbors=True)
        return edited

    try:
        yield from set_config('Blender')
        yield from switch_workspace('Rigging')
        with context():
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            arm_data = bpy.data.armatures.new('SkinFixtureArmature')
            arm = bpy.data.objects.new('SkinFixtureArmature', arm_data)
            bpy.context.collection.objects.link(arm)
            arm.select_set(True)
            bpy.context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
            for i, name in enumerate(('BoneA', 'BoneB', 'LockedBone', 'NonDeformBone')):
                bone = arm_data.edit_bones.new(name)
                bone.head = (i, 0, 0)
                bone.tail = (i, 0, 1)
            bpy.ops.object.mode_set(mode='OBJECT')
            arm_data.bones['NonDeformBone'].use_deform = False
            arm.select_set(False)
            mesh = bpy.data.meshes.new('SkinFixtureMesh')
            mesh.from_pydata(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
                             (), ((0, 1, 2, 3),))
            mesh.update()
            subject = bpy.data.objects.new('SkinSubject', mesh)
            bpy.context.collection.objects.link(subject)
            modifier = subject.modifiers.new('FixtureSkin', 'ARMATURE')
            modifier.object = arm
            groups = {name: subject.vertex_groups.new(name=name) for name in (
                'BoneA', 'BoneB', 'LockedBone', 'NonDeformBone', 'UnrelatedMask')}
            for i, (a, b) in enumerate(((.2, .3), (.005, .5), (.05, .5), (.001, .2))):
                for name, value in dict(BoneA=a, BoneB=b, LockedBone=.25,
                                        NonDeformBone=.6, UnrelatedMask=.4).items():
                    groups[name].add([i], value, 'REPLACE')
                mesh.vertices[i].select = i % 2 == 0
            mesh.vertices[3].hide = True
            groups['LockedBone'].lock_weight = True
            subject.vertex_groups.active_index = groups['BoneA'].index
            other_mesh = bpy.data.meshes.new('OtherMesh')
            other_mesh.from_pydata(((2, 0, 0),), (), ())
            other = bpy.data.objects.new('OtherSelected', other_mesh)
            bpy.context.collection.objects.link(other)
            other.vertex_groups.new(name='Unrelated').add([0], .125, 'REPLACE')
            subject.select_set(True)
            other.select_set(True)
            bpy.context.view_layer.objects.active = subject
            bpy.context.view_layer.update()
        yield from settle(12)
        normalize_path = ('Skin', 'Normalize Weights', 'Normalize Weights')
        prune_path = ('Skin', 'Prune Small Weights')
        initial = snapshot()
        shot('fixture')

        for operation, path in (('normalize', normalize_path), ('prune', prune_path)):
            checkpoint()
            before = snapshot()
            yield from activate_path(path, operation + '-body')
            assert_expected(before, operation)
            after = snapshot()
            shot(operation + '-body-result')
            yield from undo_once(before, operation + '-body-undo')
            record(operation + '-body-single-undo', before, after)

        before = snapshot()
        pixels, boxes = yield from open_options(normalize_path, 'normalize-options-cancel')
        assert snapshot() == before, 'Opening Normalize Options changed data'
        point = locate(pixels, 'Lock Active', (0, 0, win.width, win.height), boxes,
                       ink_levels=(.08, .12, .18, .25), allow_neighbors=True)
        yield from click(point)
        assert snapshot() == before, 'Editing Normalize Options changed data before confirmation'
        shot('normalize-options-edited')
        yield from key('ESC')
        yield from settle(8)
        assert snapshot() == before, 'Cancelling Normalize Options changed data'
        record('normalize-options-open-edit-cancel', before, snapshot())

        before = snapshot()
        pixels, boxes = yield from open_options(prune_path, 'prune-options-cancel')
        assert snapshot() == before, 'Opening Prune Options changed data'
        yield from set_threshold(pixels, boxes, '0.1', 'prune-options-cancel')
        assert snapshot() == before, 'Editing Prune Options changed data before confirmation'
        yield from key('ESC')
        yield from settle(8)
        assert snapshot() == before, 'Cancelling changed Prune Options changed data'
        record('prune-options-open-edit-cancel', before, snapshot())

        checkpoint()
        before = snapshot()
        pixels, boxes = yield from open_options(prune_path, 'prune-options-confirm')
        assert snapshot() == before
        edited = yield from set_threshold(pixels, boxes, '0.1', 'prune-options-confirm')
        assert snapshot() == before
        point = locate(edited, 'OK', (0, 0, win.width, win.height), boxes,
                       ink_levels=(.18, .25, .4, .5))
        yield from click(point)
        yield from settle(12)
        assert_expected(before, 'prune', threshold=.1)
        after = snapshot()
        shot('prune-options-confirm-result')
        record('prune-options-custom-threshold', before, after)

        # F9 must recompute from the original weights. BoneA=.05 was removed by
        # .1, but must reappear when the same operation is adjusted down to .02.
        region = next(r for r in view().regions if r.type == 'WINDOW')
        event('MOUSEMOVE', 'NOTHING', region.x + region.width / 2,
              region.y + region.height / 2)
        yield from settle(3)
        baseline = shot('prune-redo-before')
        yield from key('F9')
        yield from settle(12)
        pixels = shot('prune-redo-popup')
        boxes = popup(pixels, baseline, 'prune-redo')
        yield from set_threshold(pixels, boxes, '0.02', 'prune-redo')
        yield from settle(12)
        assert_expected(before, 'prune', threshold=.02)
        redone = snapshot()
        assert redone != after, 'F9 must use the newly entered threshold'
        yield from key('ESC')
        yield from settle(8)
        assert snapshot() == redone, 'Closing the redo popup reverted an applied adjustment'
        shot('prune-redo-result')
        yield from undo_once(before, 'prune-options-redo-undo')
        record('prune-options-f9-original-state-single-undo', before, redone)

        # Redo to a no-change plan is a distinct regression: returning CANCELLED
        # can make native redo replay the previous threshold after restoring the
        # original snapshot. With normalization off, threshold zero must retain
        # all original memberships and values.
        checkpoint()
        before = snapshot()
        pixels, boxes = yield from open_options(prune_path, 'prune-noop-options')
        edited = yield from set_threshold(pixels, boxes, '0.1', 'prune-noop-options')
        point = locate(edited, 'Normalize After', (0, 0, win.width, win.height), boxes,
                       ink_levels=(.18, .25, .4, .5), allow_neighbors=True)
        yield from click(point)
        assert snapshot() == before
        edited = shot('prune-noop-options-normalize-off')
        point = locate(edited, 'OK', (0, 0, win.width, win.height), boxes,
                       ink_levels=(.18, .25, .4, .5))
        yield from click(point)
        yield from settle(12)
        assert_expected(before, 'prune', threshold=.1, normalize_after=False)
        event('MOUSEMOVE', 'NOTHING', region.x + region.width / 2,
              region.y + region.height / 2)
        yield from settle(3)
        baseline = shot('prune-noop-redo-before')
        yield from key('F9')
        yield from settle(12)
        pixels = shot('prune-noop-redo-popup')
        boxes = popup(pixels, baseline, 'prune-noop-redo')
        yield from set_threshold(pixels, boxes, '0', 'prune-noop-redo')
        yield from settle(12)
        assert snapshot() == before, ('F9 no-change plan replayed the prior deletion',
                                      snapshot(), before)
        yield from key('ESC')
        yield from settle(8)
        assert snapshot() == before
        yield from undo_once(before, 'prune-noop-redo-undo')
        record('prune-options-f9-no-change-original-state', before, snapshot())
        assert snapshot() == initial, 'The GUI suite must leave its original fixture state'
        shot('final-restored')
        save_evidence()
        print(PASS_MARKER, flush=True)
    finally:
        space_topbar.TOPBAR_HT_upper_bar.draw = original_draw


if __name__ == '__main__' and 'bpy' in globals():
    steps = suite()

    def tick():
        try:
            next(steps)
            return .04
        except StopIteration:
            bpy.ops.wm.quit_blender()
        except BaseException:
            traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(1)

    bpy.app.timers.register(tick, first_interval=1)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Space/File invokes and native confirmation chains; never confirm file I/O.

All menu/confirmation clicks locate complete rendered captions. The screenshots
and receipt probes complement the separate cross-window lifecycle suite, which
tests split releases, lost input, focus loss, and either window's destruction.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import blf
import bpy
import imbuf
import numpy as np

ROOT = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
ART = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', ROOT)).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(ROOT)
ART.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False
bpy.context.preferences.filepaths.save_modified_images = 'ASK'
bpy.context.preferences.view.use_save_prompt = True
RECEIPTS = []
FILE_IO = []
GUARD = 'VIEW3D_OT_axismeld_hotbox_release_guard'


class AXISMELD_OT_file_receipt_probe(bpy.types.Operator):
    bl_idname = 'axismeld.file_receipt_probe'
    bl_label = 'Private file-window input receipt'
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        RECEIPTS.append((event.type, event.value))
        return {'FINISHED', 'PASS_THROUGH'} if event.type == 'ESC' else {'PASS_THROUGH'}


bpy.utils.register_class(AXISMELD_OT_file_receipt_probe)
bpy.app.handlers.load_pre.append(lambda *_: FILE_IO.append('load'))
bpy.app.handlers.save_pre.append(lambda *_: FILE_IO.append('save'))


def settle(count=8):
    for _ in range(count):
        yield


def suite():
    from axismeld import adapter, hotbox_runtime
    source = bpy.context.window
    area = next(a for a in source.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    origin = (region.x + region.width / 2, region.y + region.height / 2)
    calls = []
    real_run = adapter.run

    def observed_run(context, command, **kwargs):
        result = real_run(context, command, **kwargs)
        calls.append((command, dict(kwargs), sorted(result)))
        print('ACTUAL_FILE_DISPATCH', calls[-1], flush=True)
        return result

    adapter.run = observed_run
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    yield from settle(12)

    def override(target=source):
        target_area = area if target == source else next(a for a in target.screen.areas if a.type == 'FILE_BROWSER')
        target_region = next(r for r in target_area.regions if r.type == 'WINDOW')
        return bpy.context.temp_override(window=target, area=target_area, region=target_region)

    def ids(target):
        return [op.bl_idname for op in target.modal_operators]

    def event(kind, value='PRESS', point=origin, target=source, **modifiers):
        target.event_simulate(type=kind, value=value, x=round(point[0]), y=round(point[1]), **modifiers)

    def click(point, target=source):
        event('MOUSEMOVE', 'NOTHING', point, target)
        yield from settle(2)
        event('LEFTMOUSE', 'PRESS', point, target)
        yield from settle(2)
        event('LEFTMOUSE', 'RELEASE', point, target)
        yield from settle(10)

    def shot(name, target=source):
        path = ART / (name + '.png')
        with override(target):
            bpy.ops.screen.screenshot(filepath=str(path))
        picture = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = picture.size
            pixels = np.asarray(picture.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(picture)
        print('SCREENSHOT', path, flush=True)
        return pixels

    # Same full-caption glyph correlation used by modeling-viewport acceptance.
    # It reads the rendered UI, never the product's menu rectangles or row math.
    templates = {}

    def locate(pixels, label, bounds=None):
        scale = bpy.context.preferences.system.ui_scale
        if label not in templates:
            blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10 * scale, 0)
            canvas = imbuf.new((int(650 * scale), int(40 * scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, label)
            path = ROOT / ('file-glyph-' + str(len(templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            picture = bpy.data.images.load(str(path), check_existing=False)
            try:
                w, h = picture.size
                alpha = np.asarray(picture.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, 3] > .35
                yy, xx = np.nonzero(alpha)
                templates[label] = alpha[yy.min():yy.max()+1, xx.min():xx.max()+1].copy()
            finally:
                bpy.data.images.remove(picture)
        glyph = templates[label]
        gh, gw = glyph.shape
        x0, y0, x1, y1 = map(int, bounds or (0, 0, pixels.shape[1], pixels.shape[0]))
        best = None
        for level in (.18, .3, .5):
            ink = np.min(pixels[y0:y1, x0:x1, :3], axis=2) > level
            shape = (ink.shape[0] + gh - 1, ink.shape[1] + gw - 1)
            hits = np.fft.irfft2(np.fft.rfft2(ink, s=shape) *
                                np.fft.rfft2(glyph[::-1, ::-1], s=shape), s=shape)[gh-1:ink.shape[0], gw-1:ink.shape[1]]
            total = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
            counts = total[gh:, gw:] - total[:-gh, gw:] - total[gh:, :-gw] + total[:-gh, :-gw]
            scores = 2 * hits / (counts + np.count_nonzero(glyph))
            for cy, cx in zip(*np.nonzero(scores > .75)):
                # Reject Save in Save As / Don't Save / Save modified image(s).
                if (np.any(ink[cy:cy+gh, max(0, cx-round(6*scale)):max(0, cx-round(2*scale))]) or
                    np.any(ink[cy:cy+gh, cx+gw+round(2*scale):min(ink.shape[1], cx+gw+round(9*scale))])):
                    scores[cy, cx] = 0
            y, x = np.unravel_index(np.argmax(scores), scores.shape)
            candidate = (float(scores[y, x]), x+x0+gw/2, y+y0+gh/2)
            if best is None or candidate[0] > best[0]:
                best = candidate
        assert best[0] > .75, ('No complete rendered caption', label, best, bounds)
        print('ACTUAL_LABEL', label, best, flush=True)
        return best[1:]

    def state():
        return (bpy.data.filepath, bpy.context.scene.as_pointer(),
                tuple((o.name, o.type, o.select_get(), tuple(tuple(r) for r in o.matrix_world))
                      for o in bpy.context.scene.objects))

    def no_io():
        assert not FILE_IO, FILE_IO
        assert not list(ROOT.rglob('*.blend')), 'A cancelled entry wrote a blend file'
        assert not (ROOT / 'must-not-write.png').exists(), 'The dirty image was saved'

    def no_owners():
        assert len(bpy.context.window_manager.windows) == 1, 'File receiver remained open'
        assert GUARD not in ids(source), ids(source)
        assert 'VIEW3D_OT_axismeld_hotbox' not in ids(source), ids(source)

    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'style': 'rows', 'rows': ['common'], 'transparency': 0}})
        snapshot = json.loads(hotbox_runtime.snapshot(bpy.context))
    pending = list(snapshot['menus'])
    leaves = {}
    while pending:
        node = pending.pop()
        if node.get('command') in {'file.open', 'file.save_as'}:
            leaves[node['command']] = node
        pending.extend(node.get('children', []))
    assert set(leaves) == {'file.open', 'file.save_as'}, leaves
    for node in leaves.values():
        options = [n for n in node['children'] if n['label'] == 'Options']
        assert options and all(not n['enabled'] and not n['command'] for n in options), node
    for op in (bpy.ops.wm.open_mainfile, bpy.ops.wm.save_as_mainfile):
        prop = op.get_rna_type().properties['axismeld_release_token']
        assert prop.is_hidden and prop.is_skip_save and prop.default == 0
    print('PASS FILE_OPTIONS_AND_TRANSIENT_PROPERTIES', flush=True)

    def open_hotbox(command, tag):
        no_owners()
        event('MOUSEMOVE', 'NOTHING')
        event('SPACE')
        yield from settle(12)
        assert 'VIEW3D_OT_axismeld_hotbox' in ids(source), ids(source)
        pixels = shot(tag + '-space')
        bounds = (region.x, region.y, region.x+region.width, region.y+region.height)
        yield from click(locate(pixels, 'File', bounds))
        pixels = shot(tag + '-file')
        before_calls = len(calls)
        yield from click(locate(pixels, leaves[command]['label'], bounds))
        assert len(calls) == before_calls + 1 and calls[-1][0] == command, calls
        token = calls[-1][1]['file_release_token']
        assert token > 0 and GUARD in ids(source), (token, ids(source))
        assert 'VIEW3D_OT_axismeld_hotbox' not in ids(source), ids(source)
        return token

    def receiver_cancel(tag, token, before):
        for _ in range(60):
            receivers = [w for w in bpy.context.window_manager.windows if w != source]
            if receivers:
                break
            yield
        assert len(receivers) == 1, ('No unique native File Browser', tag)
        receiver = receivers[0]
        file_area = next(a for a in receiver.screen.areas if a.type == 'FILE_BROWSER')
        op = file_area.spaces.active.active_operator
        properties = op.properties
        actual_token = getattr(properties, 'axismeld_release_token', 0)
        assert actual_token == token, (tag, op.bl_idname, actual_token, token)
        assert (GUARD in ids(receiver)) == bool(token), (tag, ids(receiver))
        yield from settle(12)
        shot(tag + '-receiver', receiver)
        file_region = next(r for r in file_area.regions if r.type == 'WINDOW')
        point = (file_region.x+file_region.width/2, file_region.y+file_region.height/2)
        if token:
            with override(receiver):
                bpy.ops.axismeld.file_receipt_probe('INVOKE_DEFAULT')
            RECEIPTS.clear()
            event('SPACE', 'RELEASE', point, receiver)
            yield from settle(10)
            assert ('SPACE', 'RELEASE') not in RECEIPTS, (tag, RECEIPTS)
            assert receiver in bpy.context.window_manager.windows[:], tag
            assert state() == before and not FILE_IO, (tag, state(), before, FILE_IO)
            assert GUARD not in ids(receiver) and GUARD not in ids(source), (tag, ids(receiver), ids(source))
        event('ESC', 'PRESS', point, receiver)
        yield from settle(16)
        no_owners()
        assert state() == before, (tag, 'Cancellation changed the scene')
        no_io()
        print('PASS ACTUAL_FILE_WINDOW', tag, 'token', token, flush=True)

    assert not bpy.data.is_dirty, 'Clean File entry fixture unexpectedly dirty'
    for command, tag in (('file.open', 'clean-open'), ('file.save_as', 'clean-save-as')):
        before = state()
        token = yield from open_hotbox(command, tag)
        yield from receiver_cancel(tag, token, before)

    # Native inherited shortcuts are actual key events and remain outside the
    # transient hotbox ownership chain, including Save of an untitled scene.
    for key, tag in (('O', 'native-ctrl-o'), ('S', 'native-ctrl-s')):
        before, count = state(), len(calls)
        event(key, ctrl=True)
        event(key, 'RELEASE', ctrl=True)
        yield from settle(14)
        assert len(calls) == count and GUARD not in ids(source), calls
        yield from receiver_cancel(tag, 0, before)

    with override():
        bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(.125, 0, 0))
    yield from settle(8)
    assert bpy.data.is_dirty, 'Dirty scene fixture was not marked modified'
    for choice, tag in (("Don't Save", 'dirty-open-discard'), ('Cancel', 'dirty-open-cancel')):
        before = state()
        token = yield from open_hotbox('file.open', tag)
        assert len(bpy.context.window_manager.windows) == 1, 'Dirty confirmation was bypassed'
        pixels = shot(tag + '-confirmation')
        yield from click(locate(pixels, choice))
        if choice == "Don't Save":
            yield from receiver_cancel(tag, token, before)
        else:
            event('SPACE', 'RELEASE')
            yield from settle(12)
            no_owners()
            assert state() == before
            no_io()
            print('PASS ACTUAL_FILE_CONFIRM_CANCEL', tag, flush=True)

    image = bpy.data.images.new('Private dirty-image fixture', width=8, height=8)
    image.filepath_raw = str(ROOT / 'must-not-write.png')
    image.file_format = 'PNG'
    image.pixels[0:4] = (1, 0, 0, 1)
    image.update()
    assert image.is_dirty and not image.packed_file
    before = state()
    token = yield from open_hotbox('file.save_as', 'dirty-image-save-as')
    assert len(bpy.context.window_manager.windows) == 1, 'Modified-image dialog was bypassed'
    pixels = shot('dirty-image-confirmation')
    # Native Save continuation writes an image when checked. Uncheck the actual
    # rendered caption, then assert that continuation neither saves nor packs it.
    yield from click(locate(pixels, 'Save 1 modified image(s)'))
    pixels = shot('dirty-image-unchecked')
    yield from click(locate(pixels, 'Save'))
    no_io()
    assert image.is_dirty and not image.packed_file, 'Image continuation saved or packed the fixture'
    yield from receiver_cancel('dirty-image-save-as', token, before)
    assert image.is_dirty and not image.packed_file
    bpy.data.images.remove(image)
    adapter.run = real_run
    print('AXISMELD_FILE_WINDOW_EVENTS_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return .035
    except StopIteration:
        bpy.ops.wm.quit_blender()
        return None
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


(ART / 'capture-evidence.json').write_text(json.dumps({
    'binary': bpy.app.binary_path,
    'binary_sha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
    'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}, indent=2), encoding='utf-8')
bpy.app.timers.register(tick, first_interval=1)

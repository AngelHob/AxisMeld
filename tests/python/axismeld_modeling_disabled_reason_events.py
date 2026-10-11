# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual Modeling gray-row tooltips and guarded native-menu regression.

Run in an isolated GUI with --enable-event-simulate; the normal event harness
provides AXISMELD_TEST_ARTIFACTS and AXISMELD_TEST_ROOT. No preferences are saved.
The observer matches rendered captions and tooltip words, not only properties.
"""
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
    from bl_ui import space_axismeld_menubar as ui

    win = bpy.context.window
    script_root = Path(bpy.utils.system_resource('SCRIPTS'))
    paths = [script_root / 'startup/bl_ui' / name for name in (
        'space_axismeld_menubar.py', 'space_axismeld_native_modeling.py', 'space_view3d.py')]
    evidence = dict(phase='modeling-disabled-reason', exe=bpy.app.binary_path,
                    exe_sha256=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                    test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    resources={p.relative_to(script_root).as_posix():
                               hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, cases=[])
    (ART / 'test-source.py').write_bytes(Path(__file__).read_bytes())

    def save():
        (ART / 'capture-evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')

    save()
    cursor = [600, 650]
    templates = {}
    failures = []

    def view():
        return max((a for a in win.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)

    def context():
        area = view()
        return bpy.context.temp_override(window=win, area=area,
                                         region=next(r for r in area.regions if r.type == 'WINDOW'))

    def event(kind, value='PRESS', point=None):
        if point is not None:
            cursor[:] = [int(v) for v in point]
        win.event_simulate(type=kind, value=value, x=cursor[0], y=cursor[1])

    def key(kind):
        event(kind)
        yield from settle(2)
        event(kind, 'RELEASE')
        yield from settle(2)

    def close():
        bpy.context.preferences.view.show_tooltips = False
        for _ in range(5):
            yield from key('ESC')
        event('MOUSEMOVE', 'NOTHING', (win.width // 2, win.height // 2))
        yield from settle(4)

    def shot(tag):
        path = ART / (tag + '.png')
        with context():
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            return np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(image)

    def locate(pixels, label, boxes=None, style='widget', levels=(.08, .12, .18, .25),
               full=True, prefer_bottom=False):
        scale = bpy.context.preferences.system.ui_scale
        cache_key = (scale, style, label)
        if cache_key not in templates:
            blf.size(0, getattr(bpy.context.preferences.ui_styles[0], style).points * scale)
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10 * scale, 0)
            canvas = imbuf.new((int(900 * scale), int(45 * scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, label)
            path = ROOT / ('disabled-reason-glyph-' + str(len(templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            image = bpy.data.images.load(str(path), check_existing=False)
            try:
                width, height = image.size
                alpha = np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4)[:, :, 3] > .35
                yy, xx = np.nonzero(alpha)
                templates[cache_key] = alpha[yy.min():yy.max()+1, xx.min():xx.max()+1].copy()
            finally:
                bpy.data.images.remove(image)
        glyph = templates[cache_key]
        gh, gw = glyph.shape
        best = None
        boxes = boxes or [(0, 0, win.width, win.height)]
        for x0, y0, x1, y1 in boxes:
            x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
            if y1-y0 < gh or x1-x0 < gw:
                continue
            for level in levels:
                ink = np.min(pixels[y0:y1, x0:x1, :3], axis=2) > level
                shape = (ink.shape[0]+gh-1, ink.shape[1]+gw-1)
                hits = np.fft.irfft2(np.fft.rfft2(ink, s=shape) *
                                    np.fft.rfft2(glyph[::-1, ::-1], s=shape), s=shape)[gh-1:ink.shape[0], gw-1:ink.shape[1]]
                total = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
                counts = total[gh:, gw:]-total[:-gh, gw:]-total[gh:, :-gw]+total[:-gh, :-gw]
                scores = 2 * hits / (counts + np.count_nonzero(glyph))
                if full:
                    for cy, cx in zip(*np.nonzero(scores > .75)):
                        if (np.any(ink[cy:cy+gh, max(0, cx-round(6*scale)):max(0, cx-round(2*scale))]) or
                                np.any(ink[cy:cy+gh, cx+gw+round(2*scale):min(ink.shape[1], cx+gw+round(9*scale))])):
                            scores[cy, cx] = 0
                y, x = np.unravel_index(np.argmax(scores), scores.shape)
                if prefer_bottom and np.any(scores > .75):
                    y = int(np.nonzero(scores > .75)[0].min())
                    x = int(np.argmax(scores[y]))
                match = (float(scores[y, x]), x+x0+gw/2, y+y0+gh/2)
                if (best is None or
                        (prefer_bottom and match[0] > .75 and
                         (best[0] <= .75 or match[2] < best[2])) or
                        (not prefer_bottom and match[0] > best[0])):
                    best = match
        assert best and best[0] > .75, ('Rendered caption missing', label, style, best, boxes)
        print('ACTUAL_GLYPH', label, style, best, flush=True)
        return best[1:]

    def click(point):
        event('MOUSEMOVE', 'NOTHING', point)
        yield from settle(2)
        event('LEFTMOUSE', 'PRESS')
        yield from settle(2)
        event('LEFTMOUSE', 'RELEASE')
        yield from settle(3)

    def popup(pixels, baseline, tag):
        scale = bpy.context.preferences.system.ui_scale
        changed = np.max(np.abs(pixels[:, :, :3]-baseline[:, :, :3]), axis=2) > .004
        boxes = observed_menu_rectangles((np.max(pixels[:, :, :3], axis=2) < .15) & changed,
                                        100 * scale, 20 * scale)
        assert boxes, ('No actual native popup', tag)
        # A new child overlaps its parent, so screenshot subtraction can split
        # its background into overlapping components. Captions may span that
        # split; merge only observed overlaps, without inventing menu bounds.
        merged = []
        for box in boxes:
            while True:
                overlap = next((other for other in merged
                                if min(box[2], other[2]) > max(box[0], other[0]) and
                                min(box[3], other[3]) > max(box[1], other[1])), None)
                if overlap is None:
                    break
                merged.remove(overlap)
                box = (min(box[0], overlap[0]), min(box[1], overlap[1]),
                       max(box[2], overlap[2]), max(box[3], overlap[3]))
            merged.append(box)
        return merged

    def open_path(labels, tag):
        yield from close()
        baseline = shot(tag + '-before')
        region = next(r for r in view().regions if r.type == 'HEADER')
        bounds = [(region.x, region.y, region.x+region.width, region.y+region.height)]
        view_point = locate(baseline, 'View', bounds)
        bounds[0] = (int(view_point[0]), region.y, region.x+region.width, region.y+region.height)
        yield from click(locate(baseline, labels[0], bounds))
        yield from settle(10)
        pixels = shot(tag + '-root')
        boxes = popup(pixels, baseline, tag)
        for index, label in enumerate(labels[1:]):
            # Extrude appears both as a Maya command and as a lower native
            # directory. Choose the lower complete rendered caption, not a
            # catalog row index or an assumed menu coordinate.
            event('MOUSEMOVE', 'NOTHING', locate(pixels, label, boxes, prefer_bottom=True))
            yield from settle(16)
            previous = pixels
            pixels = shot(tag + '-child-' + str(index))
            boxes = popup(pixels, previous, tag)
        return pixels, boxes

    def snapshot():
        import bmesh
        objects = []
        for obj in bpy.context.scene.objects:
            geometry = None
            if obj.type == 'MESH':
                mesh = bmesh.from_edit_mesh(obj.data) if obj.mode == 'EDIT' else obj.data
                vertices = mesh.verts if obj.mode == 'EDIT' else mesh.vertices
                geometry = [(tuple(v.co), v.select, v.hide) for v in vertices]
            elif obj.type in {'CURVE', 'SURFACE'}:
                geometry = [[(tuple(p.co), p.select_control_point) for p in spline.bezier_points]
                            for spline in obj.data.splines]
            objects.append((obj.name, obj.type, obj.mode, obj.select_get(), geometry))
        active = bpy.context.view_layer.objects.active
        return (objects, active.name if active else None, bpy.context.mode)

    descriptions = []
    original_description = ui.AXISMELD_OT_menubar_execute.description

    @classmethod
    def traced_description(cls, context, properties):
        text = original_description(context, properties)
        descriptions.append(text)
        return text

    ui.AXISMELD_OT_menubar_execute.description = traced_description
    host_calls = []
    callbacks = []
    executed = []

    class AXISMELD_OT_disabled_reason_poll_probe(bpy.types.Operator):
        bl_idname = 'axismeld.disabled_reason_poll_probe'
        bl_label = 'Native Poll Guard'

        @classmethod
        def poll(cls, context):
            cls.poll_message_set('The native sentinel poll deliberately rejects execution')
            return False

        def execute(self, context):
            executed.append(context.mode)
            return {'FINISHED'}

    bpy.utils.register_class(AXISMELD_OT_disabled_reason_poll_probe)
    for identifier, label in (
            ('VIEW3D_MT_edit_curve_ctrlpoints', 'Quasar Copper Alpha'),
            ('VIEW3D_MT_edit_mesh_extrude', 'Velvet Indigo Omega')):
        def observe_host(self, context, identifier=identifier):
            # Observe before the original draw: an invalid native draw may
            # raise before appended plug-in callbacks get a chance to run.
            host_calls.append((identifier, context.mode))

        def callback(self, context, identifier=identifier, label=label):
            self.layout.label(text=label)
            self.layout.operator(AXISMELD_OT_disabled_reason_poll_probe.bl_idname)
        getattr(bpy.types, identifier).prepend(observe_host)
        getattr(bpy.types, identifier).append(callback)
        callbacks.append((identifier, observe_host))
        callbacks.append((identifier, callback))

    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    win.workspace = bpy.data.workspaces['Modeling']
    bpy.context.preferences.view.ui_scale = 1.0
    yield from settle(16)

    def check_case(record, condition, message):
        if not condition:
            record.setdefault('failures', []).append(message)
            failures.append(record['case'] + ': ' + message)

    def disabled_case(path, label, tag, forbidden_host):
        before = snapshot()
        start = len(host_calls)
        pixels, boxes = yield from open_path(path, tag)
        point = locate(pixels, label, boxes, prefer_bottom=True)
        record = dict(case=tag, path=path, row=label, popup=boxes)
        baseline_descriptions = len(descriptions)
        bpy.context.preferences.view.show_tooltips = True
        tooltip = pixels
        matched = False
        for attempt in range(2):
            event('MOUSEMOVE', 'NOTHING', (point[0]-35, point[1]))
            yield from settle(4)
            event('MOUSEMOVE', 'NOTHING', (point[0]-2, point[1]))
            yield from settle(4)
            event('MOUSEMOVE', 'NOTHING', (point[0]+2, point[1]))
            yield from settle(45)
            tooltip = shot(tag + '-tooltip-' + str(attempt+1))
            # Only pixels outside the source menu can prove a visible tooltip.
            outside = tooltip.copy()
            changed = np.max(np.abs(tooltip[:, :, :3]-pixels[:, :, :3]), axis=2) > .004
            outside[~changed, :3] = 0
            for x0, y0, x1, y1 in boxes:
                outside[max(0, y0-5):y1+5, max(0, x0-5):x1+5, :3] = 0
            try:
                record['reason_glyph'] = locate(outside, 'Edit Mode', style='tooltip', full=False)
                matched = True
                break
            except AssertionError:
                pass
        record['descriptions'] = descriptions[baseline_descriptions:]
        record['host_calls'] = host_calls[start:]
        check_case(record, matched, 'Hover did not render the required Edit Mode reason')
        check_case(record, not any(call[0] == forbidden_host for call in host_calls[start:]),
                   'Unavailable native submenu was previewed')
        check_case(record, snapshot() == before, 'Hover changed selection, mode or geometry')
        yield from click(point)
        yield from close()
        check_case(record, snapshot() == before and not executed, 'Disabled row click executed an action')
        evidence['cases'].append(record)
        save()
        print('ACTUAL_DISABLED_REASON_CASE', json.dumps(record), flush=True)

    try:
        with context():
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None
        yield from settle(8)
        # Collect both failures on the old candidate before reporting RED.
        yield from disabled_case(('Curves', 'Control Points'), 'Control Points', 'no-object-control-points',
                                 'VIEW3D_MT_edit_curve_ctrlpoints')
        yield from disabled_case(('Edit Mesh', 'Extrude'), 'Extrude', 'no-object-extrude',
                                 'VIEW3D_MT_edit_mesh_extrude')

        with context():
            bpy.ops.curve.primitive_bezier_curve_add()
            curve = bpy.context.active_object
            bpy.ops.object.mode_set(mode='EDIT')
        yield from settle(10)
        for object_type, path, label, sentinel, host, poll_id in (
                ('CURVE', ('Curves', 'Control Points'), None, 'Quasar Copper Alpha',
                 'VIEW3D_MT_edit_curve_ctrlpoints', 'curve.extrude_move'),
                ('MESH', ('Edit Mesh', 'Extrude', 'Extrude'), 'Extrude Faces', 'Velvet Indigo Omega',
                 'VIEW3D_MT_edit_mesh_extrude', 'mesh.extrude_repeat')):
            if object_type == 'MESH':
                with context():
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    cube = bpy.data.objects['Cube']
                    cube.select_set(True)
                    bpy.context.view_layer.objects.active = cube
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                yield from settle(10)
            namespace, operator_name = poll_id.split('.')
            native_op = getattr(getattr(bpy.ops, namespace), operator_name)
            with context():
                before_poll = native_op.poll()
            assert before_poll, ('Invalid native positive-control fixture', poll_id)
            before = snapshot()
            calls_before = len(host_calls)
            pixels, boxes = yield from open_path(path, 'valid-' + object_type.lower())
            locate(pixels, sentinel, boxes)
            locate(pixels, label or native_op.get_rna_type().name, boxes)
            point = locate(pixels, 'Native Poll Guard', boxes)
            with context():
                assert native_op.poll() == before_poll
                assert not bpy.ops.axismeld.disabled_reason_poll_probe.poll()
            assert any(call[0] == host for call in host_calls[calls_before:]), 'Native callback was not invoked'
            yield from click(point)
            yield from close()
            assert not executed and snapshot() == before, 'Native rejected poll was bypassed or menu changed state'
            evidence['cases'].append(dict(case='valid-' + object_type.lower(), native_poll=before_poll,
                                          callback=sentinel, host_calls=host_calls[calls_before:],
                                          rejected_poll_preserved=True, scene_unchanged=True))
            save()
    finally:
        for identifier, callback in callbacks:
            getattr(bpy.types, identifier).remove(callback)
        ui.AXISMELD_OT_menubar_execute.description = original_description
        bpy.utils.unregister_class(AXISMELD_OT_disabled_reason_poll_probe)
    evidence['failures'] = failures
    save()
    assert not failures, failures
    print('AXISMELD_MODELING_DISABLED_REASON_PASS', flush=True)


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

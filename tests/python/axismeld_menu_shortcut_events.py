# SPDX-License-Identifier: GPL-2.0-or-later
"""Observe live shortcut captions in the real viewport Maya Modify menu."""
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
    from axismeld import adapter
    win = bpy.context.window
    executed = []
    adapted = []
    original_run = ui.menubar_runtime.run
    original_adapter_run = adapter.run

    def traced_adapter_run(context, command, **kwargs):
        # Observe the actual execution context after the menu's override has
        # been entered, then delegate without replacing the adapter behavior.
        area_pointer = context.area.as_pointer() if context.area else None
        region_pointer = context.region.as_pointer() if context.region else None
        result = original_adapter_run(context, command, **kwargs)
        adapted.append((command, area_pointer, region_pointer, frozenset(result)))
        return result

    def traced_run(context, kind, key, token):
        source = ui.menubar_runtime._from_token(context, token, True)
        result = original_run(context, kind, key, token)
        executed.append((kind, key, source.area.as_pointer() if source else None,
                         source.region.as_pointer() if source else None, frozenset(result)))
        return result

    adapter.run = traced_adapter_run
    ui.menubar_runtime.run = traced_run
    scriptroot = Path(bpy.utils.system_resource('SCRIPTS'))
    paths = [scriptroot / 'startup/bl_ui/space_axismeld_menubar.py',
             scriptroot / 'modules/axismeld/menubar_runtime.py']
    evidence = {
        'exe': bpy.app.binary_path,
        'exe_sha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
        'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'resources': {p.relative_to(scriptroot).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in paths},
    }
    (ART / 'capture-evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    (ART / 'test-source.py').write_bytes(Path(__file__).read_bytes())
    print('MENU_SHORTCUT_EVIDENCE', json.dumps(evidence), flush=True)

    def shot(name):
        path = ART / (name + '.png')
        with bpy.context.temp_override(window=win):
            bpy.ops.screen.screenshot(filepath=str(path))
        picture = bpy.data.images.load(str(path), check_existing=False)
        try:
            w, h = picture.size
            return np.asarray(picture.pixels[:], dtype=np.float32).reshape(h, w, 4).copy()
        finally:
            bpy.data.images.remove(picture)

    def event(kind, value='PRESS', x=400, y=500):
        win.event_simulate(type=kind, value=value, x=int(x), y=int(y))

    def click(point):
        event('MOUSEMOVE', 'NOTHING', *point)
        yield from settle(2)
        event('LEFTMOUSE', 'PRESS', *point)
        yield from settle(2)
        event('LEFTMOUSE', 'RELEASE', *point)
        yield from settle(8)

    def close():
        for _ in range(4):
            event('ESC')
            yield from settle(2)

    templates = {}

    def locate(pixels, label, bounds, boxes=None, threshold=(.18, .25, .35, .5)):
        if isinstance(threshold, tuple):
            # Hovered and idle native menu rows use different foreground
            # colors. Keep the same complete-glyph agreement requirement while
            # measuring the same caption at each foreground cutoff.
            errors = []
            for level in threshold:
                try:
                    return locate(pixels, label, bounds, boxes, level)
                except AssertionError as error:
                    errors.append(str(error))
            raise AssertionError(('Missing complete themed caption', label, errors))
        scale = bpy.context.preferences.system.ui_scale
        key = (scale, label)
        if key not in templates:
            blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10 * scale, 0)
            canvas = imbuf.new((int(600 * scale), int(40 * scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, label)
            path = ROOT / ('shortcut-glyph-' + str(len(templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            picture = bpy.data.images.load(str(path), check_existing=False)
            try:
                w, h = picture.size
                alpha = np.asarray(picture.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, 3] > .35
                yy, xx = np.nonzero(alpha)
                templates[key] = alpha[yy.min():yy.max() + 1, xx.min():xx.max() + 1].copy()
            finally:
                bpy.data.images.remove(picture)
        glyph = templates[key]
        gh, gw = glyph.shape
        x0, y0, x1, y1 = map(int, bounds)
        ink = np.min(pixels[y0:y1, x0:x1, :3], axis=2) > threshold
        if boxes is not None:
            allowed = np.zeros(ink.shape, dtype=bool)
            for ax0, ay0, ax1, ay1 in boxes:
                allowed[max(0, ay0-y0):min(y1-y0, ay1-y0),
                        max(0, ax0-x0):min(x1-x0, ax1-x0)] = True
            ink &= allowed
        assert ink.shape[0] >= gh and ink.shape[1] >= gw, (label, bounds, glyph.shape)
        shape = (ink.shape[0]+gh-1, ink.shape[1]+gw-1)
        hits = np.fft.irfft2(np.fft.rfft2(ink, s=shape) *
                            np.fft.rfft2(glyph[::-1, ::-1], s=shape), s=shape)[gh-1:ink.shape[0], gw-1:ink.shape[1]]
        total = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        counts = total[gh:, gw:] - total[:-gh, gw:] - total[gh:, :-gw] + total[:-gh, :-gw]
        score = 2 * hits / (counts + np.count_nonzero(glyph))
        if boxes is not None:
            # Require a complete caption. "Scale Tool" inside
            # "Move/Rotate/Scale Tool" must not pass as the separate command.
            margin = max(5, round(9 * scale))
            for cy, cx in zip(*np.nonzero(score > .75)):
                if (np.any(ink[cy:cy+gh, max(0, cx-round(6*scale)):max(0, cx-round(2*scale))]) or
                        np.any(ink[cy:cy+gh, cx+gw+round(2*scale):min(ink.shape[1], cx+gw+margin)])):
                    score[cy, cx] = 0
        y, x = np.unravel_index(np.argmax(score), score.shape)
        assert score[y, x] > .75, ('Missing full rendered caption', label, float(score[y, x]), bounds)
        rect = tuple(map(int, (x+x0, y+y0, x+x0+gw, y+y0+gh)))
        print('ACTUAL_MENU_CAPTION', label, float(score[y, x]), rect, flush=True)
        return rect

    def center(rect):
        return ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)

    def popup(pixels, baseline):
        scale = bpy.context.preferences.system.ui_scale
        changed = np.max(np.abs(pixels[:, :, :3] - baseline[:, :, :3]), axis=2) > .004
        boxes = observed_menu_rectangles((np.max(pixels[:, :, :3], axis=2) < .15) & changed,
                                         100 * scale, 25 * scale)
        assert boxes, 'No newly rendered native popup'
        return boxes

    def open_tools(tag, foreign_host=False):
        view = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in view.regions if r.type == 'WINDOW')
        node = next(node for node in ui._NODES.values()
                    if node['kind'] == 'menu' and node.get('path') == ('Modify', 'Transformation Tools'))
        event('MOUSEMOVE', 'NOTHING', view.x+view.width//2, view.y+view.height//2)
        yield from settle(3)
        baseline = shot(tag + '-before')
        # This is the actual registered submenu used by Object > Maya Modify,
        # drawn with its source View3D; no test menu or replacement draw function.
        host = next(a for a in win.screen.areas if a.type == 'OUTLINER') if foreign_host else view
        host_region = next(r for r in host.regions if r.type == 'WINDOW') if foreign_host else region
        with bpy.context.temp_override(window=win, area=host, region=host_region):
            bpy.ops.wm.call_menu(name=ui._MENU_NAMES[node['id']])
        yield from settle(16)
        pixels = shot(tag + '-transformation-tools')
        return pixels, popup(pixels, baseline)

    yield from settle(12)
    win.workspace = bpy.data.workspaces['Modeling']
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    yield from settle(14)
    view = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in view.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win, area=view, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        assert bpy.context.mode == 'OBJECT'
    yield from settle(8)
    commands = ('transform.move', 'transform.rotate', 'transform.scale')
    labels = ('Move Tool', 'Rotate Tool', 'Scale Tool')

    def bindings(command):
        return [item for km in bpy.context.window_manager.keyconfigs.user.keymaps
                for item in km.keymap_items
                if item.idname == 'axismeld.command' and item.properties.command == command]

    map_names = [km.name for km in bpy.context.window_manager.keyconfigs.user.keymaps
                 if any(item.idname == 'axismeld.command' and item.properties.command in commands
                        for item in km.keymap_items)]
    records, execution_records = [], []
    for requested in (1.0, 1.5):
        bpy.context.preferences.view.ui_scale = requested
        yield from settle(14)
        for mode in ('default', 'rebound', 'disabled', 'removed'):
            if mode == 'default':
                # Reloading a preset deliberately retains user edits. Reset the
                # affected maps explicitly, then reacquire RNA items after update.
                for name in map_names:
                    bpy.context.window_manager.keyconfigs.user.keymaps[name].restore_to_default()
            elif mode == 'rebound':
                for command, key in zip(commands, ('F6', 'F7', 'F8')):
                    for item in bindings(command):
                        item.type, item.ctrl, item.shift = key, True, True
            elif mode == 'disabled':
                for command in commands:
                    for item in bindings(command):
                        item.active = False
            else:
                for km in bpy.context.window_manager.keyconfigs.user.keymaps:
                    for item in list(km.keymap_items):
                        if item.idname == 'axismeld.command' and item.properties.command in commands:
                            km.keymap_items.remove(item)
            yield from settle(12)
            current = {command: [item.to_string() for item in bindings(command) if item.active]
                       for command in commands}
            assert all(bool(current[c]) == (mode in {'default', 'rebound'}) for c in commands), current
            tag = 'shortcut-' + str(requested) + '-' + mode
            # Each case must demonstrate a real tool transition. A cancelled
            # menu action must not pass because Move was selected by a prior case.
            with bpy.context.temp_override(window=win, area=view, region=region):
                result = bpy.ops.wm.tool_set_by_id('EXEC_DEFAULT', name='builtin.select_box', cycle=False)
            assert result == {'FINISHED'}, ('Could not establish tool baseline', tag, result)
            yield from settle(6)
            tool_before = win.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
            assert tool_before and tool_before.idname == 'builtin.select_box', \
                ('Tool baseline was not Select Box', tag)
            # An Outliner host has no matching 3D handler. The submenu must use
            # its captured View3D when resolving customized bindings there.
            foreign_host = mode == 'rebound'
            pixels, boxes = yield from open_tools(tag, foreign_host)
            scale = bpy.context.preferences.system.ui_scale
            row_records = []
            for command, label in zip(commands, labels):
                body = locate(pixels, label, (0, 0, win.width, win.height), boxes)
                row = tuple(map(int, next(box for box in boxes if box[0] <= body[0] < box[2] and
                           box[1] <= body[1] < box[3])))
                # Exclude the independent rightmost Options cell from caption evidence.
                hint_bounds = (body[2]+8*scale, body[1]-3*scale, row[2]-24*scale, body[3]+3*scale)
                record = {'scale': requested, 'mode': mode, 'command': command,
                          'host': 'OUTLINER' if foreign_host else 'VIEW_3D',
                          'expected': current[command], 'body': body, 'popup': row,
                          'hint_bounds': hint_bounds}
                try:
                    if current[command]:
                        record['hint'] = locate(pixels, current[command][0], hint_bounds)
                    else:
                        x0, y0, x1, y1 = map(int, hint_bounds)
                        ink = np.min(pixels[y0:y1, x0:x1, :3], axis=2)
                        # A hovered empty row is brighter than idle shortcut
                        # text. Measure glyph contrast against this row's local
                        # background instead of counting its highlight as ink.
                        background = np.median(ink, axis=1, keepdims=True)
                        contrast = ink - background
                        record['hint_max_contrast'] = float(np.max(contrast))
                        record['hint_foreground_pixels'] = int(np.count_nonzero(contrast > .02))
                        assert record['hint_foreground_pixels'] == 0, \
                            ('Unbound command kept shortcut ink', command, hint_bounds,
                             record['hint_max_contrast'], record['hint_foreground_pixels'])
                    record['pass'] = True
                except AssertionError as error:
                    record['pass'], record['error'] = False, str(error)
                records.append(record)
                row_records.append(record)
                (ART / 'menu-shortcuts.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
                assert record['pass'], ('Menu shortcut rendering failed', record)
            (ART / 'menu-shortcuts.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
            print('ACTUAL_SHORTCUT_STATE', tag, current, flush=True)
            # Gray Options remain a distinct hit target; clicking the same
            # row's body still runs its wrapper in the exact captured source.
            move = row_records[0]
            body, row = move['body'], move['popup']
            ink = ((np.min(pixels[:, :, :3], axis=2) > .18) &
                   (np.max(pixels[:, :, :3], axis=2) < .5))
            allowed = np.zeros(ink.shape, dtype=bool)
            allowed[int(body[1]-6*scale):int(body[3]+6*scale),
                    int(row[2]-24*scale):int(row[2])] = True
            gears = observed_menu_rectangles(ink & allowed, 5*scale, 5*scale)
            gears = [box for box in gears if box[2]-box[0] < 20*scale and box[3]-box[1] < 20*scale]
            assert len(gears) == 1, ('Independent Options gear not found', gears)
            before_calls = len(executed)
            before_adapter_calls = len(adapted)
            before_scene = [(o.name, o.select_get(), tuple(tuple(r) for r in o.matrix_world))
                            for o in bpy.context.scene.objects]
            yield from click(center(gears[0]))
            assert len(executed) == before_calls and len(adapted) == before_adapter_calls, \
                'Options gear executed the row body'
            tool_after_gear = win.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
            assert tool_after_gear and tool_after_gear.idname == 'builtin.select_box', \
                'Options gear changed the active tool'
            yield from click(center(body))
            assert len(executed) == before_calls+1 and executed[-1] == (
                'command', 'transform.move', view.as_pointer(), region.as_pointer(),
                frozenset({'FINISHED'})), ('Menu wrapper did not finish in its captured source', executed)
            assert len(adapted) == before_adapter_calls+1 and adapted[-1] == (
                'transform.move', view.as_pointer(), region.as_pointer(), frozenset({'FINISHED'})), \
                ('Adapter did not execute in the captured source', adapted)
            tool = win.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
            assert tool and tool.idname == 'builtin.move', 'Menu wrapper did not activate Move Tool'
            assert before_scene == [(o.name, o.select_get(), tuple(tuple(r) for r in o.matrix_world))
                                    for o in bpy.context.scene.objects], 'Menu clicks changed scene geometry or selection'
            execution = {'case': tag, 'host': 'OUTLINER' if foreign_host else 'VIEW_3D',
                         'wrapper_result': sorted(executed[-1][-1]),
                         'adapter_command': adapted[-1][0],
                         'adapter_area': adapted[-1][1], 'adapter_region': adapted[-1][2],
                         'adapter_result': sorted(adapted[-1][-1]),
                         'tool_before': 'builtin.select_box', 'tool_after': tool.idname,
                         'options_executed': False}
            execution_records.append(execution)
            (ART / 'menu-shortcut-execution.json').write_text(json.dumps(execution_records, indent=2), encoding='utf-8')
            print('ACTUAL_SHORTCUT_WRAPPER_AND_OPTIONS_PASS', json.dumps(execution), flush=True)
            yield from close()
    print('AXISMELD_MENU_SHORTCUT_EVENTS_PASS', flush=True)


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

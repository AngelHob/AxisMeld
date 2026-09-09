# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise installed binding and native navigation with real private GUI events.

Catches missing horizontal input, inverted vertical input, incremental drift,
origin dependence, unclamped results, and leakage into native keymaps/preferences.
Run with axismeld_navigation_ui_runner.py, never in an existing user process.
"""
import math
import os
from pathlib import Path
import sys
import traceback

import bpy
from mathutils import Quaternion

bpy.context.preferences.view.show_splash = False
bpy.context.preferences.use_preferences_save = False
test_root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(test_root):
    raise RuntimeError('Navigation events require an isolated Blender temporary directory')


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    rv3d = space.region_3d
    inputs = bpy.context.preferences.inputs
    saved_prefs = (inputs.view_zoom_method, inputs.view_zoom_axis, inputs.invert_mouse_zoom)
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    failures = []
    pos = [region.x + region.width // 2, region.y + region.height // 2]

    def check(condition, message):
        print(('PASS ' if condition else 'FAIL ') + message, flush=True)
        if not condition:
            failures.append(message)

    def event(kind, value='PRESS', *, point=None, alt=True):
        if point is not None:
            pos[:] = [int(point[0]), int(point[1])]
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], alt=alt)

    def settle(count=3):
        for _ in range(count):
            yield

    def drag(points, *, origin=(0.5, 0.5), cancel=False):
        samples = []
        start = (region.x + int(region.width * origin[0]), region.y + int(region.height * origin[1]))
        event('MOUSEMOVE', 'NOTHING', point=start)
        yield from settle()
        event('RIGHTMOUSE')
        yield from settle(2)
        for dx, dy in points:
            event('MOUSEMOVE', 'NOTHING', point=(start[0] + dx, start[1] + dy))
            yield from settle(2)
            samples.append(rv3d.view_distance)
        if cancel:
            event('ESC', alt=False)
            yield
            event('ESC', 'RELEASE', alt=False)
            yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        return samples

    def fixture(perspective='PERSP'):
        rv3d.view_perspective = perspective
        rv3d.view_distance = 10.0
        rv3d.view_location = (0, 0, 0)
        rv3d.view_rotation = Quaternion((1, 0, 0, 0))

    yield from settle(12)
    event('ESC', alt=False)
    yield
    event('ESC', 'RELEASE', alt=False)
    yield from settle()
    for perspective in ('PERSP', 'ORTHO'):
        for name, delta, near in [('right', (60, 0), True), ('left', (-60, 0), False),
                                  ('up', (0, 60), False), ('down', (0, -60), True)]:
            fixture(perspective)
            yield from settle()
            yield from drag([delta])
            distance = rv3d.view_distance
            print('MEASURE', perspective, name, distance, flush=True)
            check(distance < 9.99 if near else distance > 10.01,
                  f'{perspective} {name} {"near" if near else "far"}: {distance}')
            check(rv3d.view_perspective == perspective, f'{perspective} projection retained')
    fixture()
    yield from drag([(60, 0)])
    single = rv3d.view_distance
    fixture()
    yield from drag([(60, -60)])
    check(0 < rv3d.view_distance < single < 10, 'right-down adds both axes')
    fixture()
    yield from drag([(60, 60)])
    check(abs(rv3d.view_distance - 10) < 1e-4, 'equal right-up cancels')
    fixture()
    yield from drag([(60, 0), (60, -60), (0, 0)])
    check(abs(rv3d.view_distance - 10) < 1e-4, 'return to origin restores initial distance')
    fixture()
    yield from drag([(20, 0), (40, 0), (60, 0)])
    check(abs(rv3d.view_distance - single) < 1e-4, 'event subdivision does not accumulate drift')
    fixture()
    yield from drag([(60, 0)], origin=(0.3, 0.35))
    check(abs(rv3d.view_distance - single) < 1e-4, 'equal delta at different origin is equal')
    fixture()
    yield from drag([(60, -60)], cancel=True)
    check(abs(rv3d.view_distance - 10) < 1e-4, 'Escape restores initial distance')
    for delta in [(100000, -100000), (-100000, 100000)]:
        fixture()
        samples = yield from drag([delta, (delta[0] * 2, delta[1] * 2), (0, 0)])
        check(all(math.isfinite(value) and value > 0 for value in samples) and
              samples[0] == samples[1] and
              (samples[0] < 0.01 if delta[0] > 0 else samples[0] >= 10000),
              f'extreme {delta} saturates at positive finite native bound: {samples}')
        check(abs(rv3d.view_distance - 10) < 1e-4,
              f'extreme {delta} stays finite and returns from clamp')

    for method in ('CONTINUE', 'SCALE', 'DOLLY'):
        inputs.view_zoom_method = method
        inputs.view_zoom_axis = 'HORIZONTAL'
        inputs.invert_mouse_zoom = True
        fixture()
        yield from drag([(60, 0)])
        check(abs(rv3d.view_distance - single) < 1e-4,
              f'AxisMeld direction and gain independent of native {method}/horizontal/invert')
    # Even a native continuous preference must not keep moving while the mouse is held still.
    inputs.view_zoom_method = 'CONTINUE'
    fixture()
    start = (region.x + region.width // 2, region.y + region.height // 2)
    event('MOUSEMOVE', 'NOTHING', point=start)
    yield from settle()
    event('RIGHTMOUSE')
    yield
    event('MOUSEMOVE', 'NOTHING', point=(start[0] + 60, start[1]))
    yield from settle()
    stationary = rv3d.view_distance
    yield from settle(12)
    check(abs(rv3d.view_distance - stationary) < 1e-5, 'held stationary mouse has no timer drift')
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    inputs.view_zoom_method, inputs.view_zoom_axis, inputs.invert_mouse_zoom = saved_prefs

    # Camera framing must run through the native inverse factor and camera limits.
    fixture('CAMERA')
    space.camera = bpy.data.objects['Camera']
    rv3d.view_camera_zoom = 0
    lens = space.camera.data.lens
    yield from settle()
    yield from drag([(60, 0)])
    check(rv3d.view_camera_zoom > 0, 'camera right drag enlarges frame')
    check(space.camera.data.lens == lens, 'camera focal length unchanged')
    camera_zoom = rv3d.view_camera_zoom
    yield from drag([(0, 60)])
    check(rv3d.view_camera_zoom < camera_zoom, 'camera up drag reduces frame')
    rv3d.view_camera_zoom = 0
    yield from drag([(100000, 0)])
    check(math.isfinite(rv3d.view_camera_zoom) and rv3d.view_camera_zoom == 600,
          'camera frame uses native maximum clamp')
    rv3d.view_camera_zoom = 0
    yield from drag([(-100000, 0)])
    check(math.isfinite(rv3d.view_camera_zoom) and abs(rv3d.view_camera_zoom + 30) < 1e-4,
          f'camera frame uses native minimum clamp: {rv3d.view_camera_zoom}')
    space.lock_camera = True
    yield from settle()
    camera_position = space.camera.location.copy()
    yield from drag([(60, 0)])
    check((space.camera.location - camera_position).length > 0.01 and
          space.camera.data.lens == lens, 'locked camera retains native movement and focal length')
    space.lock_camera = False

    fixture()
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.screen.region_quadview()
    yield from settle(8)
    # Native region order matches region_quadviews; choose an orthographic pane.
    region = next(r for r in area.regions if r.type == 'WINDOW' and
                  r.data and r.data.view_perspective == 'ORTHO')
    rv3d = region.data
    # RNA exposes per-region bits: initialize all three linked orthographic panes,
    # including both TOP and FRONT required to form the native clipping volume.
    for pane in (r for r in area.regions if r.type == 'WINDOW' and r.data.lock_rotation):
        with bpy.context.temp_override(window=win, area=area, region=pane):
            pane.data.view_distance = 10
            pane.data.show_sync_view = True
            pane.data.use_box_clip = True
    yield from drag([(60, 0)])
    check(rv3d.view_distance < 9.99 and rv3d.view_perspective == 'ORTHO',
          'quad orthographic binding invokes dual-axis navigation')
    check(rv3d.show_sync_view and rv3d.use_box_clip, 'quad sync and BOXCLIP flags retained')
    synced = [r.data for r in area.regions if r.type == 'WINDOW' and r.data.show_sync_view]
    check(len(synced) >= 2 and all(abs(v.view_distance - rv3d.view_distance) < 1e-4 for v in synced),
          'quad linked pane distances synchronize')
    check(all(sum(abs(value) for value in plane[:3]) > 0.9 for plane in rv3d.clip_planes),
          'quad BOXCLIP planes remain valid after drag')
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.screen.region_quadview()
    yield from settle(8)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    rv3d = space.region_3d

    check(saved_prefs == (inputs.view_zoom_method, inputs.view_zoom_axis, inputs.invert_mouse_zoom),
          'AxisMeld does not mutate zoom preferences')
    # Factory default native behavior is intentionally vertical-only and up=near.
    bpy.utils.keyconfig_set(str(preset.with_name('Industry_Compatible.py')))
    yield from settle()
    fixture()
    yield from drag([(60, 0)])
    check(abs(rv3d.view_distance - 10) < 1e-4, 'Industry native horizontal remains unchanged')
    fixture()
    yield from drag([(0, 60)])
    check(rv3d.view_distance < 9.99, 'Industry native up remains near')
    if failures:
        raise AssertionError(f'{len(failures)} navigation failures: ' + '; '.join(failures))
    print('AXISMELD_NAVIGATION_EVENTS_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return 0.035
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1.0)

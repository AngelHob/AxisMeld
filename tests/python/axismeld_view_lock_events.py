# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real isolated navigation: fixed-axis views cannot tumble, including maximized panes.

Run via axismeld_navigation_ui_runner.py --suite view-lock, never a user session.
"""
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
    raise RuntimeError('View lock events require an isolated temporary directory')


def check(value, message):
    if not value:
        raise AssertionError(message)


def same_rotation(a, b):
    return abs(abs(a.dot(b)) - 1.0) < 1e-6


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    camera = bpy.data.objects['Camera']
    camera_before = camera.matrix_world.copy()
    pos = [0, 0]

    def panes():
        return [r for r in area.regions if r.type == 'WINDOW']

    def settle(count=4):
        for _ in range(count):
            yield

    def event(kind, value='PRESS', *, alt=False, point=None):
        if point is not None:
            pos[:] = point
        win.event_simulate(type=kind, value=value, x=int(pos[0]), y=int(pos[1]), alt=alt)

    def focus():
        event('MOUSEMOVE', 'NOTHING',
              point=(region.x + region.width // 2, region.y + region.height // 2))
        yield from settle()

    def tap_space():
        yield from focus()
        event('SPACE')
        yield
        event('SPACE', 'RELEASE')
        yield from settle(8)

    def action(value):
        with bpy.context.temp_override(window=win, area=area, region=region):
            check(bpy.ops.view3d.axismeld_view(action=value) == {'FINISHED'},
                  f'native view action failed: {value}')

    def drag(button):
        yield from focus()
        start = tuple(pos)
        event(button, alt=True)
        yield
        for step in range(1, 7):
            event('MOUSEMOVE', 'NOTHING', alt=True,
                  point=(start[0] + 10 * step, start[1] + 6 * step))
            yield
        event(button, 'RELEASE', alt=True)
        yield from settle(6)

    def locked_navigation(label):
        view = region.data
        before = view.view_rotation.copy()
        other_before = [p.data.view_rotation.copy() for p in panes()]
        yield from drag('LEFTMOUSE')
        check(same_rotation(before, view.view_rotation) and view.view_perspective == 'ORTHO',
              f'{label}: Alt+LMB changed the fixed view')
        check(all(same_rotation(saved, p.data.view_rotation) for saved, p in zip(other_before, panes())),
              f'{label}: blocked tumble was rerouted into another pane')
        with bpy.context.temp_override(window=win, area=area, region=region):
            check(not bpy.ops.view3d.rotate.poll(), f'{label}: native rotate entry remains available')
        before_location = view.view_location.copy()
        yield from drag('MIDDLEMOUSE')
        check((view.view_location - before_location).length > 1e-4,
              f'{label}: rotation lock also blocked pan')
        before_distance = view.view_distance
        yield from drag('RIGHTMOUSE')
        check(abs(view.view_distance - before_distance) > 1e-4,
              f'{label}: rotation lock also blocked dolly')
        check(same_rotation(before, view.view_rotation), f'{label}: pan/dolly changed rotation')
        print(f'PASS {label}: tumble blocked, pan/dolly retained', flush=True)

    def free_tumble(label):
        before = region.data.view_rotation.copy()
        yield from drag('LEFTMOUSE')
        check(not same_rotation(before, region.data.view_rotation), f'{label}: free tumble blocked')
        print(f'PASS {label}: free tumble', flush=True)

    yield from settle(12)
    # A loaded/native axis view may not yet carry AxisMeld's rotation policy.
    # Entering its first AxisMeld quad must still initialize a fixed pane.
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.view3d.view_axis(type='TOP')
    yield from settle(12)
    yield from tap_space()
    region = panes()[1]
    yield from locked_navigation('first quad from an unlocked native Top')
    yield from tap_space()
    region = panes()[0]
    yield from locked_navigation('maximized first native Top')
    yield from tap_space()
    check(len(panes()) == 4, 'Space did not enter quad view')
    for index in range(3):
        region = panes()[index]
        yield from locked_navigation(f'quad fixed pane {index}')
        yield from tap_space()
        check(len(panes()) == 1, 'Space did not maximize fixed pane')
        region = panes()[0]
        yield from locked_navigation(f'maximized fixed pane {index}')
        yield from tap_space()
        check(len(panes()) == 4, 'Space did not restore quad view')
    region = panes()[3]
    yield from free_tumble('quad Perspective')
    region = panes()[1]
    action('PERSPECTIVE')
    yield from free_tumble('explicit Perspective in formerly locked quad pane')
    action('TOP')
    yield from locked_navigation('quad Top restored after Perspective')
    yield from tap_space()
    region = panes()[0]
    action('PERSPECTIVE')
    yield from free_tumble('Perspective in maximized fixed pane')
    yield from tap_space()
    region = panes()[1]
    check(region.data.view_perspective == 'PERSP', 'quad restore lost explicit Perspective')
    yield from free_tumble('Perspective stays unlocked after quad restore')
    yield from tap_space()
    region = panes()[0]
    for name in ('FRONT', 'TOP', 'SIDE', 'BACK', 'LEFT', 'BOTTOM'):
        action(name)
        yield from locked_navigation(f'single {name}')
        action('PERSPECTIVE')
        yield from free_tumble(f'{name} to Perspective')
    # User orthographic projection is not a fixed named camera.
    region.data.view_perspective = 'ORTHO'
    region.data.view_rotation = Quaternion((0.2, 0.3, 0.4), 0.7)
    yield from free_tumble('arbitrary user orthographic')
    action('PERSPECTIVE')
    bpy.utils.keyconfig_set(str(preset.with_name('Industry_Compatible.py')))
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.view3d.view_axis(type='TOP')
    yield from settle(12)
    yield from free_tumble('Industry native axis view')
    check(camera.matrix_world == camera_before, 'viewport navigation moved scene Camera object')
    print('AXISMELD_VIEW_LOCK_EVENTS_PASS', flush=True)


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

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Separate factory-startup GUI event acceptance; never attach to a user session.

Use axismeld_manipulator_ui_runner.py --blender /path/to/blender to isolate temp/config.
No preference or scene files are retained. Failure exits nonzero.
"""
import math
import os
from pathlib import Path
import sys
import traceback

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

bpy.context.preferences.view.show_splash = False
bpy.context.preferences.use_preferences_save = False
# WM_exit_ex always writes quit.blend for GUI exits in this Blender version. Require
# a private temp root rather than guessing a preference or altering user recovery files.
test_root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(test_root):
    raise RuntimeError('GUI test requires an isolated Blender temporary directory')


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def suite():
    win = bpy.context.window
    bpy.context.preferences.use_preferences_save = False
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    rv3d = space.region_3d
    rv3d.view_rotation = Quaternion((1, 0, 0, 0))
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 10
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py'
                  for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    # Fail clearly on the previous build, before attempting any mouse input.
    check(bpy.ops.axismeld.axis_select.get_rna_type().identifier == 'AXISMELD_OT_axis_select',
          'missing native axis-selection operator')
    obj = bpy.data.objects.get('Cube')
    check(obj is not None, 'factory cube missing')
    pos = [region.x + region.width // 2, region.y + region.height // 2]

    def event(kind, value='PRESS', *, x=None, y=None, **mods):
        if x is not None:
            pos[:] = [int(x), int(y)]
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], **mods)

    def settle(count=3):
        for _ in range(count):
            yield

    def click(kind='LEFTMOUSE', **mods):
        event(kind, **mods)
        yield
        event(kind, 'RELEASE', **mods)
        yield from settle()

    def key(kind, **mods):
        yield from click(kind, **mods)

    def drag(kind, cancel=False):
        event(kind)
        yield
        start = tuple(pos)
        for step in range(1, 9):
            event('MOUSEMOVE', 'NOTHING', x=start[0] + step * 9, y=start[1] + step * 5)
            yield
        if cancel:
            yield from key(cancel if isinstance(cancel, str) else 'ESC')
        event(kind, 'RELEASE')
        yield from settle(4)

    def find_handle(tool, center):
        for radius in range(20, 155, 3):
            factor = math.sqrt(0.5) if tool == 'rotate' else 1.0
            dx, dy = radius * factor, radius * factor if tool == 'rotate' else 0
            event('MOUSEMOVE', 'NOTHING', x=region.x + center.x + dx,
                  y=region.y + center.y + dy)
            yield from settle(2)
            with bpy.context.temp_override(window=win, area=area, region=region):
                if bpy.ops.axismeld.axis_select.poll():
                    return
        raise AssertionError(f'{tool}: no selectable native handle found')

    yield from settle(10)
    event('MOUSEMOVE', 'NOTHING')
    yield from settle()
    yield from key('ESC')
    for tool, hotkey in [('move', 'W'), ('rotate', 'E'), ('scale', 'R')]:
        with bpy.context.temp_override(window=win, area=area, region=region):
            obj.location = (0, 0, 0)
            obj.rotation_euler = (0, 0, 0)
            obj.scale = (1, 1, 1)
            bpy.context.view_layer.update()
            bpy.ops.ed.undo_push(message='AxisMeld test fixture')
        yield from key(hotkey)
        yield from settle(5)
        with bpy.context.temp_override(window=win, area=area, region=region):
            active_tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname
            print('TEST_CONTEXT', tool, active_tool, bpy.context.mode,
                  bpy.context.window_manager.keyconfigs.active.name, region.width, region.height, flush=True)
            check(active_tool == f'builtin.{tool}', f'{hotkey}: real key event did not select {tool}')
        center = location_3d_to_region_2d(region, rv3d, Vector((0, 0, 0)))
        # Find a real highlighted native handle. X arrow/box lies right of origin;
        # Z rotation ring is diagonal in this top view, away from edge-on X/Y rings.
        yield from find_handle(tool, center)
        before = (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale))
        yield from click()
        check(before == (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale)),
              f'{tool}: axis click changed geometry')
        event('MOUSEMOVE', 'NOTHING', x=region.x + center.x + 250, y=region.y + center.y - 160)
        yield from settle()
        with bpy.context.temp_override(window=win, area=area, region=region):
            check(bpy.ops.axismeld.axis_drag.poll(), f'{tool}: clicked axis did not persist')
        yield from drag('MIDDLEMOUSE')
        if tool == 'move':
            check(abs(obj.location.x) > 0.01 and abs(obj.location.y) < 1e-5 and abs(obj.location.z) < 1e-5,
                  f'move: wrong constraint {tuple(obj.location)}')
        elif tool == 'rotate':
            check(abs(obj.rotation_euler.z) > 0.01 and abs(obj.rotation_euler.x) < 1e-5 and
                  abs(obj.rotation_euler.y) < 1e-5, f'rotate: wrong constraint {tuple(obj.rotation_euler)}')
        else:
            check(abs(obj.scale.x - 1) > 0.01 and abs(obj.scale.y - 1) < 1e-5 and
                  abs(obj.scale.z - 1) < 1e-5, f'scale: wrong constraint {tuple(obj.scale)}')
        after = (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale))
        yield from drag('MIDDLEMOUSE')
        repeated = (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale))
        check(repeated != after, f'{tool}: repeated drag lost its axis')
        yield from drag('MIDDLEMOUSE', cancel=True)
        check(repeated == (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale)),
              f'{tool}: cancellation did not restore geometry')
        yield from drag('MIDDLEMOUSE', cancel='RIGHTMOUSE')
        check(repeated == (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale)),
              f'{tool}: RMB cancellation did not restore geometry')
        yield from key('Z', ctrl=True)
        obj = bpy.data.objects.get('Cube')  # Undo may replace datablocks.
        check(all(abs(a - b) < 1e-5 for group, expected in zip(
            (obj.location, obj.rotation_euler, obj.scale), after) for a, b in zip(group, expected)),
            f'{tool}: one undo did not reverse only the repeated drag')
        yield from key('Z', ctrl=True)
        obj = bpy.data.objects.get('Cube')
        check(all(abs(a - b) < 1e-5 for group, expected in zip(
            (obj.location, obj.rotation_euler, obj.scale), before) for a, b in zip(group, expected)),
            f'{tool}: one undo did not restore pre-drag state')
        print(f'PASS {tool}: click-only, constrained/repeated MMB, cancel, undo', flush=True)

    # A plain click and a drag share native hit-testing but must remain different actions.
    yield from find_handle('scale', center)
    yield from click()
    yield from key('ESC')
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(not bpy.ops.axismeld.axis_drag.poll(), 'idle Escape did not clear the axis')
    yield from find_handle('scale', center)
    yield from drag('LEFTMOUSE')
    check(abs(obj.scale.x - 1) > 0.01 and abs(obj.scale.y - 1) < 1e-5,
          f'direct native handle drag broken: {tuple(obj.scale)}')
    yield from key('W')
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(not bpy.ops.axismeld.axis_drag.poll(), 'tool change retained a stale axis')
    yield from find_handle('move', center)
    yield from click()
    yield from key('F9')
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(bpy.context.mode == 'EDIT_MESH', 'physical F9 did not enter edit mode')
        check(not bpy.ops.axismeld.axis_drag.poll(), 'mode change retained a stale axis')
        bpy.ops.mesh.select_all(action='SELECT')
    yield from key('W')  # Blender stores active tools independently for Object and Edit modes.
    yield from settle()
    yield from find_handle('move', center)
    yield from click()
    event('MOUSEMOVE', 'NOTHING', x=region.x + center.x + 250, y=region.y + center.y - 160)
    yield from settle()
    import bmesh
    before_vertices = [v.co.copy() for v in bmesh.from_edit_mesh(obj.data).verts]
    yield from drag('MIDDLEMOUSE')
    after_vertices = [v.co.copy() for v in bmesh.from_edit_mesh(obj.data).verts]
    check(any(abs(a.x - b.x) > 0.01 for a, b in zip(after_vertices, before_vertices)) and
          all(abs(a.y - b.y) < 1e-5 and abs(a.z - b.z) < 1e-5
              for a, b in zip(after_vertices, before_vertices)), 'mesh edit axis constraint failed')
    view_before = rv3d.view_location.copy()
    event('MIDDLEMOUSE', alt=True)
    yield
    event('MOUSEMOVE', 'NOTHING', x=pos[0] + 55, y=pos[1] + 40, alt=True)
    yield
    event('MIDDLEMOUSE', 'RELEASE', alt=True)
    yield from settle()
    check((rv3d.view_location - view_before).length > 0.001, 'Alt MMB did not navigate')
    check(all((v.co - saved).length < 1e-5 for v, saved in
              zip(bmesh.from_edit_mesh(obj.data).verts, after_vertices)), 'Alt MMB changed geometry')
    industry = preset.with_name('Industry_Compatible.py')
    bpy.utils.keyconfig_set(str(industry))
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(not bpy.ops.axismeld.axis_drag.poll() and not bpy.ops.axismeld.axis_select.poll(),
              'native axis commands leaked into original preset')
    print('PASS direct drag, idle clear, tool/mode invalidation, edit mesh, Alt navigation, preset isolation',
          flush=True)
    print('AXISMELD_MANIPULATOR_EVENTS_PASS', flush=True)


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
        # Immediate test-process failure; no open user files exist in factory startup.
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1.0)

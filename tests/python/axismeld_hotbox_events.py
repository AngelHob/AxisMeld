# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Behavioral native view/event acceptance; only run through the isolated runner.

Catches swapped locked panes, discarded hidden poses, retargeted axis commands,
and accidental geometry edits. Expected quaternions are literal Blender Z-up poses.
"""
import os
from pathlib import Path
import sys
import traceback

import bpy
from mathutils import Quaternion

test_root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(test_root):
    raise RuntimeError('GUI test requires an isolated Blender temporary directory')
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def pose(rv):
    return (tuple(rv.view_rotation), tuple(rv.view_location), rv.view_distance, rv.view_perspective)


def same(actual, expected, label):
    check(actual[3] == expected[3], label + ': projection')
    check(abs(abs(sum(a * b for a, b in zip(actual[0], expected[0]))) - 1) < 1e-5,
          label + ': orientation')
    check(max(abs(a - b) for a, b in zip(actual[1], expected[1])) < 1e-5, label + ': center')
    check(abs(actual[2] - expected[2]) < 1e-5, label + ': distance')


def clipping(rv):
    return rv.use_clip_planes, tuple(tuple(plane) for plane in rv.clip_planes)


def same_clipping(actual, expected, label):
    check(actual[0] == expected[0], label + ': enabled clipping')
    check(max(abs(a - b) for p, q in zip(actual[1], expected[1]) for a, b in zip(p, q)) < 1e-5,
          label + f': clipping planes: actual={actual[1]!r}, expected={expected[1]!r}')


def settle(count=3):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    space = area.spaces.active
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    check(bpy.ops.view3d.axismeld_view.get_rna_type().identifier == 'VIEW3D_OT_axismeld_view',
          'missing native view action')
    check(bpy.ops.view3d.axismeld_hotbox.get_rna_type().identifier == 'VIEW3D_OT_axismeld_hotbox',
          'missing native hotbox')

    def regions():
        return [r for r in area.regions if r.type == 'WINDOW']

    def rv(region):
        with bpy.context.temp_override(window=win, area=area, region=region):
            return bpy.context.region_data

    def action(kind, region=None):
        region = region or regions()[0]
        with bpy.context.temp_override(window=win, area=area, region=region):
            check(bpy.ops.view3d.axismeld_view(action=kind) == {'FINISHED'}, kind + ': failed')

    cube = bpy.data.objects['Cube']
    geometry = (tuple(tuple(row) for row in cube.matrix_world),
                tuple(tuple(v.co) for v in cube.data.vertices), tuple(o.name for o in bpy.context.selected_objects))
    original = ((0.820473, 0.424708, -0.175920, -0.339851), (2.25, -3.5, 1.75), 17.0, 'PERSP')
    view = rv(regions()[0])
    view.view_rotation = Quaternion(original[0]).normalized()
    view.view_location = original[1]
    view.view_distance = original[2]
    view.view_perspective = original[3]
    original = pose(view)
    yield from settle(5)
    action('TOGGLE_QUAD')
    yield from settle(5)
    check(len(regions()) == 4, 'initial quad missing')
    # Physical rectangle order, not native list-order assumptions.
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    expected = [((1, 0, 0, 0), original[1], 17.0, 'ORTHO'), original,
                ((0.70710678, 0.70710678, 0, 0), original[1], 17.0, 'ORTHO'),
                ((0.5, 0.5, 0.5, 0.5), original[1], 17.0, 'ORTHO')]
    for i, pane in enumerate(panes):
        same(pose(rv(pane)), expected[i], f'physical pane {i}')
    for cycle in range(20):
        for index in range(4):
            panes = sorted(regions(), key=lambda r: (-r.y, r.x))
            action('TOGGLE_QUAD', panes[index])
            yield from settle(2)
            check(len(regions()) == 1, 'maximize did not produce one pane')
            view = rv(regions()[0])
            same(pose(view), expected[index], f'maximized {cycle}/{index}')
            if cycle == 0:
                view.view_location = (index + 5.25, index - 7.5, index + 9.75)
                view.view_distance = index + 23.0
                expected[index] = pose(view)
            action('TOGGLE_QUAD')
            yield from settle(2)
            for j, pane in enumerate(sorted(regions(), key=lambda r: (-r.y, r.x))):
                same(pose(rv(pane)), expected[j], f'restored {cycle}/{index}/{j}')
    print('PASS physical quad mapping, locked-pane maximize, independent poses, 20 round trips', flush=True)
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    linked = rv(panes[0])
    linked.show_sync_view = True
    linked.use_box_clip = True
    yield from settle()
    check([rv(p).use_clip_planes for p in panes] == [True, False, True, False],
          'fixture must have quad clipping only in top/front, with unclipped user/right panes')
    # An independent native border clip in the right pane must not be mistaken for
    # quad-derived clipping; the top-right user pane remains deliberately unclipped.
    with bpy.context.temp_override(window=win, area=area, region=panes[3]):
        bpy.ops.view3d.clip_border('EXEC_DEFAULT', xmin=20, ymin=30, xmax=160, ymax=150)
    yield from settle()
    check(rv(panes[3]).use_clip_planes and not rv(panes[3]).use_box_clip,
          'independent native clipping fixture was not created')
    clip_states = [clipping(rv(p)) for p in panes]
    locks = [(rv(p).lock_rotation, rv(p).show_sync_view, rv(p).use_box_clip) for p in panes]
    expected = [pose(rv(p)) for p in panes]
    action('TOGGLE_QUAD', panes[0])
    yield from settle()
    single = rv(regions()[0])
    check(not single.lock_rotation and not single.show_sync_view and not single.use_box_clip,
          'quad-specific locks survived maximize')
    check(not single.use_clip_planes, 'quad-derived clipping survived maximize')
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    check([(rv(p).lock_rotation, rv(p).show_sync_view, rv(p).use_box_clip) for p in panes] == locks,
          'quad linkage locks were not restored')
    for i, pane in enumerate(panes):
        same(pose(rv(pane)), expected[i], 'linked quad pose restore')
        same_clipping(clipping(rv(pane)), clip_states[i], f'quad clipping restore {i}')
    action('TOGGLE_QUAD', panes[0])
    yield from settle()
    rv(regions()[0]).view_location = (41, 43, 47)
    rv(regions()[0]).view_distance = 53
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    check(panes[0].width > panes[0].height, 'clip geometry fixture expects a landscape top pane')
    # A top view centered at (41,43) with distance 53 spans X [-12,94].
    # Vertical extent follows its actual quad rectangle; front/Z extent did not change.
    half_y = 53 * panes[0].height / panes[0].width
    # Native face order is ymin, xmax, ymax, xmin, with inward-facing normals.
    refreshed_planes = ((0, 1, 0, half_y - 43), (-1, 0, 0, 94),
                        (0, -1, 0, 43 + half_y), (1, 0, 0, 12),
                        clip_states[0][1][4], clip_states[0][1][5])
    for i in (0, 2):
        same_clipping(clipping(rv(panes[i])), (True, refreshed_planes), f'navigated quad clip {i}')
    for i in (1, 2, 3):
        same(pose(rv(panes[i])), expected[i], f'clip recompute must not synchronize pane {i}')
    for i in (1, 3):
        same_clipping(clipping(rv(panes[i])), clip_states[i], f'clip recompute touched independent pane {i}')
    action('TOGGLE_QUAD', panes[0])
    yield from settle()
    rv(regions()[0]).view_location = expected[0][1]
    rv(regions()[0]).view_distance = expected[0][2]
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    for i, pane in enumerate(panes):
        same_clipping(clipping(rv(pane)), clip_states[i], f'quad clip geometry restored {i}')
    # A user can create an independent clip while a former quad-clipped pane is
    # maximized. Keep it separately from the temporarily hidden quad clip volume.
    action('TOGGLE_QUAD', panes[0])
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.view3d.clip_border('EXEC_DEFAULT', xmin=90, ymin=80, xmax=240, ymax=210)
    single_user_clip = clipping(rv(regions()[0]))
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    for i, pane in enumerate(panes):
        same_clipping(clipping(rv(pane)), clip_states[i], f'quad clip after single-user clip {i}')
    action('TOGGLE_QUAD', panes[0])
    yield from settle()
    same_clipping(clipping(rv(regions()[0])), single_user_clip, 'single-user clip restored')
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='EDIT')
    yield from settle()
    # Edit-mode drawing consumes clipbb through native local-clipping calculation.
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.view3d.clip_border('INVOKE_DEFAULT')
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    action('TOGGLE_QUAD', panes[3])
    yield from settle()
    same_clipping(clipping(rv(regions()[0])), clip_states[3], 'independent clip while maximized')
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    for i, pane in enumerate(panes):
        same_clipping(clipping(rv(pane)), clip_states[i], f'independent clipping restore {i}')
    # Remove only the native independent fixture before later navigation cases.
    with bpy.context.temp_override(window=win, area=area, region=panes[3]):
        bpy.ops.view3d.clip_border('INVOKE_DEFAULT')
    rv(panes[0]).show_sync_view = False
    rv(panes[0]).use_box_clip = False
    yield from settle()
    print('PASS quad clip clearing, per-pane planes, unclipped user pane, independent user clip ownership', flush=True)
    # A menu action must affect the initiating locked pane, never the user pane.
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    action('SIDE', panes[0])
    same(pose(rv(panes[0])), ((0.5, 0.5, 0.5, 0.5), expected[0][1], expected[0][2], 'ORTHO'), 'locked side')
    same(pose(rv(panes[1])), expected[1], 'untouched user pane')
    action('TOGGLE_QUAD', panes[1])
    yield from settle()
    perspective = pose(rv(regions()[0]))
    action('FRONT')
    action('PERSPECTIVE')
    same(pose(rv(regions()[0])), perspective, 'perspective history')
    yield from settle()

    # Temporary isolated fixture binding: production configuration is Task 3.
    km = bpy.context.window_manager.keyconfigs.active.keymaps.new(
        'AxisMeld Hotbox', space_type='VIEW_3D', region_type='WINDOW')
    binding = km.keymap_items.new('view3d.axismeld_hotbox', 'SPACE', 'PRESS')
    binding.properties.tap_seconds = 0.4
    pos = [0, 0]

    def event(kind, value='PRESS', *, x=None, y=None, **mods):
        if x is not None:
            pos[:] = [int(x), int(y)]
        return win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], **mods)

    def locate(region=None, edge=False):
        region = region or regions()[0]
        event('MOUSEMOVE', 'NOTHING', x=region.x + (5 if edge else region.width // 2),
              y=region.y + (5 if edge else region.height // 2))
        yield from settle()

    def key(kind='SPACE', hold=1):
        event(kind)
        yield from settle(hold)
        event(kind, 'RELEASE')
        yield from settle()

    def gesture(dx, dy, *, trigger='SPACE', cancel=False):
        event(trigger)
        yield
        event('LEFTMOUSE')
        yield
        event('MOUSEMOVE', 'NOTHING', x=pos[0] + dx, y=pos[1] + dy)
        yield
        if cancel:
            event('ESC')
            yield
        event('LEFTMOUSE', 'RELEASE')
        yield
        event(trigger, 'RELEASE')
        yield from settle()

    yield from locate()
    yield from key()
    check(len(regions()) == 4 and not win.screen.is_animation_playing,
          'viewport Space must toggle once before Frames playback')
    target = sorted(regions(), key=lambda r: (-r.y, r.x))[0]
    before = pose(rv(target))
    yield from locate(target)
    yield from key()
    check(len(regions()) == 1, 'event maximize failed')
    same(pose(rv(regions()[0])), before, 'event initiating locked pane')
    yield from locate()
    yield from key(hold=25)
    check(len(regions()) == 1, 'long hold toggled layout')
    for dx, dy, quat, projection in [
            (90, 0, (0.5, 0.5, 0.5, 0.5), 'ORTHO'),
            (0, -90, (0.70710678, 0.70710678, 0, 0), 'ORTHO'),
            (-90, 0, (1, 0, 0, 0), 'ORTHO')]:
        yield from locate()
        view = pose(rv(regions()[0]))
        yield from gesture(dx, dy)
        check(len(regions()) == 1, 'marking release became layout tap')
        same(pose(rv(regions()[0])), (quat, view[1], view[2], projection), 'cardinal event')
    yield from locate()
    yield from gesture(0, 90)
    check(rv(regions()[0]).view_perspective == 'PERSP', 'up gesture did not restore perspective')
    for dx, dy in [(0, 0), (6, 0), (40, 40)]:
        yield from locate()
        before = pose(rv(regions()[0]))
        yield from gesture(dx, dy)
        same(pose(rv(regions()[0])), before, 'dead zone or diagonal committed')
        check(len(regions()) == 1, 'dead zone or diagonal toggled')
    yield from locate()
    before = pose(rv(regions()[0]))
    yield from gesture(90, 0, cancel=True)
    same(pose(rv(regions()[0])), before, 'Esc committed candidate')
    yield from locate()
    event('SPACE')
    yield
    event('LEFTMOUSE')
    yield
    event('MOUSEMOVE', 'NOTHING', x=pos[0] + 90, y=pos[1])
    yield from settle()
    if os.environ.get('AXISMELD_TEST_ARTIFACTS'):
        with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
            bpy.ops.screen.screenshot(filepath=str(
                Path(os.environ['AXISMELD_TEST_ARTIFACTS']) / 'hotbox-side-candidate.png'))
    event('SPACE', 'RELEASE')
    yield
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    same(pose(rv(regions()[0])), before, 'trigger release implicitly committed mouse candidate')
    # Mode and preset loss cancel immediately; the next released/repressed trigger works.
    yield from locate()
    event('SPACE')
    yield
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='SCULPT')
    yield from settle()
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'mode change left a pending tap')
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='OBJECT')
    yield from settle()
    yield from locate()
    event('SPACE')
    yield
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='EDIT')
    yield
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'Object to supported mesh Edit Mode retained pending tap')
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='OBJECT')
    yield from settle()
    original_scene = win.scene
    cancel_scene = bpy.data.scenes.new('hotbox pending scene change')
    yield from locate()
    event('SPACE')
    yield
    win.scene = cancel_scene
    yield
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'scene change retained pending tap')
    win.scene = original_scene
    yield from settle()
    yield from locate()
    event('SPACE')
    yield
    event('WINDOW_DEACTIVATE', 'NOTHING')
    yield from settle()
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'window deactivation left a pending tap')
    yield from locate()
    event('SPACE')
    yield
    area.type = 'CONSOLE'
    yield from settle()
    event('SPACE', 'RELEASE')
    yield from settle()
    area.type = 'VIEW_3D'
    yield from settle()
    space = area.spaces.active
    check(len(regions()) == 1, 'source editor loss toggled layout')
    yield from locate()
    yield from key()
    check(len(regions()) == 4, 'hotbox did not recover after source editor loss')
    yield from locate()
    yield from key()
    check(len(regions()) == 1, 'hotbox recovery did not maximize')
    # A pre-existing transform may pass Space through, but must retain its modal ownership.
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.transform.translate('INVOKE_DEFAULT')
    yield
    yield from key()
    check(len(regions()) == 1, 'hotbox preempted active transform')
    event('ESC')
    yield from settle()
    # Mesh Edit Mode is supported without selected vertices; mouse/Alt does not leak through.
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
    yield from settle()
    yield from locate()
    yield from gesture(0, -90)
    check(rv(regions()[0]).view_perspective == 'ORTHO' and len(regions()) == 1,
          'mesh Edit Mode gesture failed')
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.object.mode_set(mode='OBJECT')
    yield from settle()
    yield from locate(edge=True)
    yield from gesture(90, 0)
    check(rv(regions()[0]).view_perspective == 'ORTHO', 'edge-center fast gesture failed')
    old_scale = bpy.context.preferences.view.ui_scale
    bpy.context.preferences.view.ui_scale = 2.0
    yield from settle(8)
    check(abs(bpy.context.preferences.system.ui_scale - 2.0) < 0.05, 'fixture UI scale did not apply')
    action('TOP')
    yield from locate()
    before = pose(rv(regions()[0]))
    yield from gesture(18, 0)
    same(pose(rv(regions()[0])), before, '2x UI scale dead zone was not scaled')
    yield from locate()
    yield from gesture(30, 0)
    same(pose(rv(regions()[0])), ((0.5, 0.5, 0.5, 0.5), before[1], before[2], 'ORTHO'),
         '2x UI scale direction outside dead zone')
    bpy.context.preferences.view.ui_scale = old_scale
    yield from settle(8)
    binding.type = 'F13'
    yield from settle()
    yield from locate()
    yield from key('F13')
    check(len(regions()) == 4, 'remapped trigger did not open/close')
    yield from locate()
    yield from key('F13')
    check(len(regions()) == 1, 'remapped release did not maximize')
    binding.type = 'SPACE'
    yield from settle()
    # Repeated PRESS events must not create another modal or restart the timer. The
    # RNA simulator cannot set WM_EVENT_IS_REPEAT; true flag boundaries are in the core test.
    yield from locate()
    event('SPACE')
    yield from settle(18)
    event('SPACE')
    yield
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'repeated press restarted tap timing')
    # Geometry undo is anchored by an explicit scene edit; view operations must not
    # insert intervening undo steps. This also exercises native undo cache invalidation.
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.ed.undo_push(message='hotbox before object move')
        cube.location.x = 4.0
        bpy.ops.ed.undo_push(message='hotbox moved object')
        action('TOP')
        action('TOGGLE_QUAD')
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.ed.undo()
    yield from settle()
    cube = bpy.data.objects['Cube']
    check(abs(cube.location.x) < 1e-5, 'view operation inserted a geometry undo step')
    if len(regions()) == 4:
        action('TOGGLE_QUAD')
        yield from settle()

    # Rejected contexts must leave topology and scene camera untouched.
    scene_camera = win.scene.camera
    space.lock_camera = True
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        check(bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD') == {'CANCELLED'}, 'camera lock accepted')
    yield from locate()
    before = pose(rv(regions()[0]))
    yield from gesture(0, -90)
    same(pose(rv(regions()[0])), before, 'rejected command changed camera-locked view')
    check(len(regions()) == 1, 'rejected marking command became a layout tap')
    space.lock_camera = False
    check(len(regions()) == 1 and win.scene.camera == scene_camera, 'camera rejection mutated scene')
    space.mirror_xr_session = True
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        check(bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD') == {'CANCELLED'}, 'XR mirror accepted')
    space.mirror_xr_session = False
    check(len(regions()) == 1 and win.scene.camera == scene_camera, 'XR rejection mutated scene')
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.view3d.localview(frame_selected=False)
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        check(bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD') == {'CANCELLED'}, 'Local View accepted')
        bpy.ops.view3d.localview(frame_selected=False)
    yield from settle()
    check(len(regions()) == 1, 'Local View rejection changed topology')
    for obj in win.scene.objects:
        obj.select_set(False)
    action('TOGGLE_QUAD')
    yield from settle()
    action('TOGGLE_QUAD')
    yield from settle()
    check(len(regions()) == 1 and not bpy.context.selected_objects, 'empty selection rejected or changed')
    # Fresh arbitrary user orthographic view belongs in top-right, preserving projection.
    original_scene = win.scene
    fresh_scene = bpy.data.scenes.new('hotbox empty scene')
    win.scene = fresh_scene
    yield from settle()
    view = rv(regions()[0])
    view.view_rotation = Quaternion((0.8, 0.3, 0.2, 0.1)).normalized()
    view.view_perspective = 'ORTHO'
    view.view_location = (31, 32, 33)
    view.view_distance = 34
    arbitrary = pose(view)
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    same(pose(rv(panes[1])), arbitrary, 'arbitrary user ortho after scene invalidation')
    for pane in panes:
        check(tuple(rv(pane).view_location) == (31, 32, 33), 'old scene hidden pose survived')
    action('TOGGLE_QUAD', panes[1])
    yield from settle()
    standard_scene = bpy.data.scenes.new('hotbox standard scene')
    win.scene = standard_scene
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.view3d.view_axis(type='RIGHT')
    # No settle: AxisMeld must finish the native smooth view before snapshotting it.
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    same(pose(rv(panes[3])), ((0.5, 0.5, 0.5, 0.5), (31, 32, 33), 34, 'ORTHO'),
         'standard right source slot and pending smooth view')
    check(rv(panes[1]).view_perspective == 'PERSP', 'standard ortho source stole user slot projection')
    action('TOGGLE_QUAD', panes[3])
    yield from settle()
    win.scene = original_scene
    yield from settle()
    # External native topology changes must discard old hidden AxisMeld slots.
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.screen.region_quadview()
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    for index, pane in enumerate(panes):
        rv(pane).view_distance = 61 + index
    action('TOGGLE_QUAD', panes[0])
    yield from settle()
    action('TOGGLE_QUAD')
    yield from settle()
    for index, pane in enumerate(sorted(regions(), key=lambda r: (-r.y, r.x))):
        check(abs(rv(pane).view_distance - (61 + index)) < 1e-5, 'manual quad reused stale hidden pose')
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    native_user = pose(rv(panes[1]))
    with bpy.context.temp_override(window=win, area=area, region=panes[0]):
        bpy.ops.screen.region_quadview()
    yield from settle()
    same(pose(rv(regions()[0])), native_user, 'upstream default quad exit changed')
    # Delete the captured region while modal: validation must precede any cached pointer access.
    action('TOGGLE_QUAD')
    yield from settle()
    panes = sorted(regions(), key=lambda r: (-r.y, r.x))
    yield from locate(panes[0])
    event('SPACE')
    yield
    with bpy.context.temp_override(window=win, area=area, region=panes[1]):
        bpy.ops.screen.region_quadview()
    yield from settle()
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'destroyed modal source triggered another layout change')
    yield from locate()
    yield from key()
    check(len(regions()) == 4, 'hotbox did not recover after source region destruction')
    action('TOGGLE_QUAD')
    yield from settle()
    # Another real area has independent runtime ownership.
    second = next(a for a in win.screen.areas if a != area and a.type == 'PROPERTIES')
    second.type = 'VIEW_3D'
    yield from settle()
    second_region = next(r for r in second.regions if r.type == 'WINDOW')
    first_pose = pose(rv(regions()[0]))
    with bpy.context.temp_override(window=win, area=second, region=second_region):
        bpy.context.region_data.view_location = (101, 102, 103)
        bpy.context.region_data.view_distance = 104
        bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
    yield from settle()
    same(pose(rv(regions()[0])), first_pose, 'second area changed first')
    check(len([r for r in second.regions if r.type == 'WINDOW']) == 4, 'second area quad failed')
    second.type = 'PROPERTIES'
    yield from settle()
    # Native space duplication creates an independent runtime, including in a second window.
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        bpy.ops.wm.window_new()
    # Hide only this private test process's windows; never inspect/control a user process.
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @callback_type
        def hide_private_window(hwnd, _):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == os.getpid():
                user32.ShowWindow(hwnd, 0)
            return True

        user32.EnumWindows(hide_private_window, 0)
    yield from settle()
    second_window = next(w for w in bpy.context.window_manager.windows if w != win)
    second_area = next(a for a in second_window.screen.areas if a.type == 'VIEW_3D')
    second_region = next(r for r in second_area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=second_window, area=second_area, region=second_region):
        bpy.context.region_data.view_location = (201, 202, 203)
        bpy.context.region_data.view_distance = 204
        bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
    yield from settle()
    check(len([r for r in second_area.regions if r.type == 'WINDOW']) == 4, 'second window quad failed')
    same(pose(rv(regions()[0])), first_pose, 'duplicated window changed source view')
    second_region = next(r for r in second_area.regions if r.type == 'WINDOW')
    second_window.event_simulate(type='MOUSEMOVE', value='NOTHING',
                                x=second_region.x + second_region.width // 2,
                                y=second_region.y + second_region.height // 2)
    yield from settle()
    second_window.event_simulate(type='SPACE', value='PRESS',
                                x=second_region.x + second_region.width // 2,
                                y=second_region.y + second_region.height // 2)
    yield
    with bpy.context.temp_override(window=second_window):
        bpy.ops.wm.window_close()
    yield from settle()
    # Timeline Space retains native playback, and disabling the fixture restores viewport playback.
    timeline = next(a for a in win.screen.areas if a.type == 'DOPESHEET_EDITOR')
    timeline_region = next(r for r in timeline.regions if r.type == 'WINDOW')
    event('MOUSEMOVE', 'NOTHING', x=timeline_region.x + timeline_region.width // 2,
          y=timeline_region.y + timeline_region.height // 2)
    yield from settle()
    yield from key()
    check(win.screen.is_animation_playing, 'timeline Space was stolen')
    yield from key()
    check(not win.screen.is_animation_playing, 'timeline did not stop')
    binding.active = False
    yield from settle()
    yield from locate()
    yield from key()
    check(win.screen.is_animation_playing, 'disabled viewport binding did not fall through')
    yield from key()
    check(not win.screen.is_animation_playing, 'viewport playback did not stop')
    km.keymap_items.remove(binding)
    yield from locate()
    # Context guard, including a real preset change while the operator is pending.
    binding = km.keymap_items.new('view3d.axismeld_hotbox', 'SPACE', 'PRESS')
    yield from settle()
    event('SPACE')
    yield
    bpy.utils.keyconfig_set(str(preset.with_name('Industry_Compatible.py')))
    yield from settle()
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(regions()) == 1, 'preset loss committed a tap')
    with bpy.context.temp_override(window=win, area=area, region=regions()[0]):
        check(not bpy.ops.view3d.axismeld_hotbox.poll() and not bpy.ops.view3d.axismeld_view.poll(),
              'native hotbox/view leaked into another preset')
    km.keymap_items.remove(binding)
    bpy.utils.keyconfig_set(str(preset))
    yield from settle()
    print('PASS native marking/tap/hold/remap/cancel, contexts, scene/topology invalidation, areas/windows, undo', flush=True)
    # Selection was deliberately cleared above, and the object edit was undone.
    for name in geometry[2]:
        bpy.data.objects[name].select_set(True)
    check(geometry == (tuple(tuple(row) for row in cube.matrix_world),
                       tuple(tuple(v.co) for v in cube.data.vertices), tuple(o.name for o in bpy.context.selected_objects)),
          'view operations changed geometry or selection')
    # Save only the currently visible single pane. Hidden runtime slots must not cross reload.
    view = rv(regions()[0])
    view.view_location = (301, 302, 303)
    view.view_distance = 304
    saved = pose(view)
    path = test_root / 'hotbox-current-view.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path), relative_remap=False)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    yield from settle(5)
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    space = area.spaces.active
    check(len(regions()) == 1, 'save/reopen layout changed')
    same(pose(rv(regions()[0])), saved, 'save/reopen pose')
    action('TOGGLE_QUAD')
    yield from settle()
    for pane in regions():
        check(tuple(rv(pane).view_location) == (301, 302, 303), 'hidden runtime cache persisted in file')
        check(abs(rv(pane).view_distance - 304) < 1e-5, 'hidden runtime distance persisted in file')
    print('PASS save/reopen current view and discarded hidden runtime slots', flush=True)
    print('AXISMELD_HOTBOX_EVENTS_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return 0.025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1.0, persistent=True)

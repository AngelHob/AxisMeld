# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real transform modal input in an isolated --enable-event-simulate instance."""
import os
from pathlib import Path
import sys
import traceback

import bpy
import bmesh
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=5):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    view = space.region_3d
    view.view_rotation = Quaternion((1, 0, 0, 0))
    view.view_perspective = 'ORTHO'
    view.view_location = (0, 0, 0)
    view.view_distance = 12
    space.overlay.grid_scale = 1
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    cube = bpy.context.active_object
    mesh_object = cube
    settings = bpy.context.scene.tool_settings
    settings.snap_elements = {'EDGE'}
    settings.snap_target = 'CENTER'
    settings.use_snap = False
    settings.use_snap_translate = True
    settings.use_snap_rotate = False
    settings.use_snap_scale = False
    position = [region.x + region.width // 2, region.y + region.height // 2]

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    # A disposable trigger enters the actual native transform. It bypasses only gizmo picking,
    # not the native transform input path, snap solver, cancel, or saveTransform/Redo.
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    trigger = km.keymap_items.new('transform.translate', 'F20', 'PRESS', any=True)

    def event(kind, value='PRESS', world=None, **modifiers):
        if world is not None:
            xy = location_3d_to_region_2d(region, view, Vector(world))
            position[:] = int(region.x + xy.x), int(region.y + xy.y)
        win.event_simulate(type=kind, value=value, x=position[0], y=position[1], **modifiers)

    def snapshot():
        return (settings.use_snap, frozenset(settings.snap_elements), settings.snap_target,
                settings.use_snap_translate, settings.use_snap_rotate, settings.use_snap_scale)

    def modals():
        return [op.bl_idname for op in win.modal_operators if op.bl_idname.startswith('TRANSFORM_OT_')]

    def redo():
        return next(op for op in reversed(bpy.context.window_manager.operators)
                    if op.bl_idname.startswith('TRANSFORM_OT_'))

    def start(preheld=None, snap=False, inspect_modal=True, ctrl=False):
        settings.use_snap = snap
        cube.location = (.13, .27, 0)
        cube.rotation_euler = (0, 0, 0)
        cube.scale = (1, 1, 1)
        event('MOUSEMOVE', 'NOTHING', world=cube.location)
        yield from settle()
        if preheld:
            event(preheld)
            yield from settle()
        if ctrl:
            event('LEFT_CTRL', ctrl=True)
            yield from settle()
        # GHOST normally supplies the held letter. event_simulate bypasses that
        # tracking, so explicitly supply the real invocation's key modifier.
        event('F20', ctrl=ctrl, key_modifier=preheld or 'NONE')
        event('F20', 'RELEASE', ctrl=ctrl, key_modifier=preheld or 'NONE')
        yield from settle()
        if inspect_modal:
            check(modals(), 'Native transform did not start')

    def cancel():
        event('ESC')
        event('ESC', 'RELEASE')
        yield from settle()
        check(not modals(), 'Transform did not cancel')

    def unchanged(before, label):
        check(snapshot() == before, label + ': temporary input changed ToolSettings')

    yield from settle(10)
    baseline = snapshot()
    for key in ('X', 'V', 'J'):
        event(key)
        event(key, 'RELEASE')
        yield from settle()
        unchanged(baseline, key + ' outside transform')
    check(not modals(), 'Snap key alone started a transform')

    # Holding X before the native invocation must not become the modal X-axis lock.
    yield from start(preheld='X')
    before = snapshot()
    event('MOUSEMOVE', 'NOTHING', world=(3.24, 2.21, 0))
    yield from settle()
    check(abs(cube.location.x - 3) < .08 and abs(cube.location.y - 2) < .08,
          'Pre-held X did not produce two-axis grid snapping: ' + str(tuple(cube.location)))
    unchanged(before, 'X active')
    event('X', 'RELEASE')
    event('X')
    event('MOUSEMOVE', 'NOTHING', world=(3, 2, 0))
    yield from settle()
    check(abs(cube.location.y - 2) < .08, 'X during transform became an axis lock')
    event('X', 'RELEASE')
    event('MOUSEMOVE', 'NOTHING', world=(2.63, 1.37, 0))
    yield from settle()
    check(abs(cube.location.y - 1.37) < .08, 'X release did not restore free motion')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle()
    check(not modals(), 'X release then confirm did not finish')
    unchanged(before, 'X release then confirm')
    check(set(redo().properties.snap_elements) == {'EDGE'} and not redo().properties.snap,
          'Temporary GRID leaked into Redo')

    # Ctrl held before invocation must be captured in the underlying baseline,
    # just as Ctrl pressed after invocation is. Start off-grid to distinguish
    # actual grid snapping from unconstrained native mouse motion.
    yield from start(preheld='X', ctrl=True)
    before = snapshot()
    event('MOUSEMOVE', 'NOTHING', world=(3.24, 2.21, 0), ctrl=True)
    yield from settle()
    check(abs(cube.location.x - 3) < .08 and abs(cube.location.y - 2) < .08,
          'Pre-held X+Ctrl lost temporary grid snapping: ' + str(tuple(cube.location)))
    event('X', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    event('MOUSEMOVE', 'NOTHING', world=(2.63, 1.37, 0))
    yield from settle()
    check(abs(cube.location.y - 1.37) < .08, 'Pre-held Ctrl remained inverted after release')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle()
    unchanged(before, 'Pre-held X+Ctrl restore')
    check(set(redo().properties.snap_elements) == {'EDGE'} and not redo().properties.snap,
          'Pre-held X+Ctrl leaked into Redo')

    # A real target with one vertex makes vertex snapping distinguishable from grid snapping.
    mesh = bpy.data.meshes.new('AxisMeld snap target')
    mesh.from_pydata([(2.43, 1.67, 0)], [], [])
    target = bpy.data.objects.new('AxisMeld snap target', mesh)
    bpy.context.scene.collection.objects.link(target)
    # Establish that the exact visible fixture is a valid native target before
    # judging the temporary V mode switch. This uses no AxisMeld held letter.
    settings.snap_elements = {'VERTEX'}
    yield from start(snap=True)
    event('MOUSEMOVE', 'NOTHING', world=(2.48, 1.71, 0))
    yield from settle()
    print('NATIVE_VERTEX_BASELINE', tuple(cube.location), 'target', tuple(target.matrix_world @ mesh.vertices[0].co), flush=True)
    check((cube.location - Vector((2.43, 1.67, 0))).length < .025,
          'Native Vertex baseline cannot snap to the fixture: ' + str(tuple(cube.location)))
    yield from cancel()
    settings.snap_elements = {'EDGE'}
    yield from start()
    before = snapshot()
    event('V')
    # Native target solving has a 10ms throttle. Let the key's redraw complete
    # before the next input frame, instead of reusing its old-position result.
    yield from settle(2)
    event('MOUSEMOVE', 'NOTHING', world=(2.48, 1.71, 0))
    yield from settle()
    print('TEMP_VERTEX_RESULT', tuple(cube.location), flush=True)
    check((cube.location - Vector((2.43, 1.67, 0))).length < .025,
          'V did not use the native vertex target: ' + str(tuple(cube.location)))
    event('RET')
    event('RET', 'RELEASE')
    yield from settle()
    check(not modals(), 'Confirm while V held failed')
    unchanged(before, 'V held at confirm')
    check(set(redo().properties.snap_elements) == {'EDGE'} and not redo().properties.snap,
          'Temporary VERTEX leaked into Redo')
    event('V', 'RELEASE')
    yield from settle()
    unchanged(before, 'V release after confirm')

    # Repeat and overlapping letters are temporary. Ctrl must restore to its current state.
    for initial_snap in (False, True):
        yield from start(snap=initial_snap)
        before = snapshot()
        event('J')
        event('J')
        event('X')
        event('V')
        event('V', 'RELEASE')
        event('LEFT_CTRL', ctrl=True)
        event('LEFT_CTRL', 'RELEASE')
        event('X', 'RELEASE')
        event('MOUSEMOVE', 'NOTHING', world=(2.63, 1.37, 0))
        yield from settle()
        unchanged(before, 'Nested temporary snap')
        event('J', 'RELEASE')
        yield from settle()
        unchanged(before, 'Restore original snap on/off')
        yield from cancel()
        unchanged(before, 'Cancel')
        check((cube.location - Vector((.13, .27, 0))).length < .0001, 'Cancel changed geometry')

    # Switch translation to rotation using a disposable native modal mapping while J is held.
    modal = bpy.context.window_manager.keyconfigs.active.keymaps.get('Transform Modal Map')
    switch = modal.keymap_items.new_modal('ROTATE', 'F19', 'PRESS')
    # Native mode changes may intentionally normalize incompatible snap modes.
    # Compare with the same native transition without a temporary letter held.
    yield from start(inspect_modal=False)
    event('F19')
    event('F19', 'RELEASE')
    yield from settle()
    event('RET')
    event('RET', 'RELEASE')
    yield from settle()
    rotation_baseline = set(redo().properties.snap_elements)
    # Inspecting modal_operators creates a Python instance; native mode replacement forbids that.
    yield from start(inspect_modal=False)
    before = snapshot()
    event('J')
    event('F19')
    event('F19', 'RELEASE')
    yield from settle()
    check('TRANSFORM_OT_rotate' in modals(), 'Native transform mode switch failed')
    event('J', 'RELEASE')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle()
    unchanged(before, 'Mode switch restore')
    check(set(redo().properties.snap_elements) == rotation_baseline,
          'Mode switch did not restore its native snap baseline')
    modal.keymap_items.remove(switch)

    # Focus loss cancels the native transform before any temporary state can persist.
    yield from start()
    before = snapshot()
    event('X')
    event('MOUSEMOVE', 'NOTHING', world=(3, 2, 0))
    yield from settle()
    event('WINDOW_DEACTIVATE', 'NOTHING')
    yield from settle()
    check(not modals(), 'Focus loss left a temporary transform running')
    unchanged(before, 'Focus loss')
    check((cube.location - Vector((.13, .27, 0))).length < .0001, 'Focus loss did not cancel geometry')
    event('X', 'RELEASE')

    # Object Mode owns native transforms for Empty/Curve/etc. as well as mesh objects.
    empty = bpy.data.objects.new('AxisMeld temporary snap Empty', None)
    bpy.context.scene.collection.objects.link(empty)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    empty.select_set(True)
    bpy.context.view_layer.objects.active = empty
    cube = empty
    yield from start()
    before = snapshot()
    event('X')
    yield from settle(2)
    event('MOUSEMOVE', 'NOTHING', world=(3, 2, 0))
    yield from settle()
    print('EMPTY_X_RESULT', tuple(cube.location), flush=True)
    check(abs(cube.location.y - 2) < .08, 'Object Empty was incorrectly excluded from held X')
    yield from cancel()
    event('X', 'RELEASE')
    unchanged(before, 'Empty cancel')

    # Other keyconfigs keep their native X-axis constraint and settings.
    industry = next(Path(p) / 'industry_compatible.py' for p in bpy.utils.preset_paths('keyconfig')
                    if (Path(p) / 'industry_compatible.py').exists())
    bpy.utils.keyconfig_set(str(industry))
    yield from start()
    before = snapshot()
    event('X')
    event('MOUSEMOVE', 'NOTHING', world=(3, 2, 0))
    yield from settle()
    check(abs(cube.location.y - .27) < .001, 'Non-AxisMeld X axis constraint was changed')
    yield from cancel()
    event('X', 'RELEASE')
    unchanged(before, 'Industry Compatible')

    bpy.utils.keyconfig_set(str(preset))
    cube.select_set(False)
    bpy.context.view_layer.objects.active = None
    before = snapshot()
    for key in ('X', 'V', 'J'):
        event(key)
        event(key, 'RELEASE')
    yield from settle()
    check(not modals(), 'No-active-object input started a transform')
    unchanged(before, 'No active object')

    # The same mesh in the UV editor must keep native X axis constraints.
    mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_object
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    area.ui_type = 'UV'
    yield from settle()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    position[:] = (region.x + region.width // 2, region.y + region.height // 2)
    with override():
        bpy.ops.uv.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(mesh_object.data)
    uv = bm.loops.layers.uv.active
    uv_before = [loop[uv].uv.copy() for face in bm.faces for loop in face.loops]
    event('MOUSEMOVE', 'NOTHING')
    yield from settle()
    with override():
        check(bpy.ops.transform.translate('INVOKE_DEFAULT') == {'RUNNING_MODAL'},
              'UV native transform did not start')
    event('X')
    position[0] += 90
    position[1] += 60
    event('MOUSEMOVE', 'NOTHING')
    yield from settle()
    uv_after = [loop[uv].uv.copy() for face in bm.faces for loop in face.loops]
    check(all(abs(a.y - b.y) < .00001 for a, b in zip(uv_before, uv_after)),
          'AxisMeld held X leaked into the UV editor')
    check(any(abs(a.x - b.x) > .0001 for a, b in zip(uv_before, uv_after)),
          'UV scope check did not actually move UVs')
    yield from cancel()
    event('X', 'RELEASE')
    unchanged(before, 'UV editor')
    km.keymap_items.remove(trigger)
    print('AXISMELD_TEMPORARY_SNAP_EVENTS_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return .025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1)

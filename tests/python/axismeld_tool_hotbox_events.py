# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real keyboard/owned mouse tool gestures in a disposable factory scene."""
import os
from pathlib import Path
import sys
import traceback
import math
import blf
import bpy

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
    from axismeld import adapter, hotbox_runtime
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    pos = [cx, cy]

    def event(kind, value='PRESS', point=None, **kwargs):
        if point is not None:
            pos[:] = map(int, point)
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], **kwargs)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def tool():
        return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def screenshot(name):
        path = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root)) / name
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)

    def ring(tool_name, origin=None):
        # Coordinates only; independent native tests assert direction, spacing and hit ownership.
        from axismeld.hotbox_catalog import default_catalog
        def walk(nodes):
            for n in nodes:
                yield n
                yield from walk(n['children'])
        nodes = next(n for n in walk(default_catalog()) if n['id'] == 'tools.' + tool_name)['children']
        scale = bpy.context.preferences.system.ui_scale
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        w = max(blf.dimensions(0, n['label'])[0] / scale +
                (60 if n.get('presentation') == 'list' else 16) for n in nodes)
        d = math.sqrt(.5)
        directions = {'N': (0, 1), 'NE': (d, d), 'E': (1, 0), 'SE': (d, -d),
                      'S': (0, -1), 'SW': (-d, -d), 'W': (-1, 0), 'NW': (-d, d)}
        for ry in range(24, int(region.height / scale)):
            rects = [(-12, -19, 24, 38)]
            clear = True
            for n in nodes:
                nx, ny = directions[n['direction']]
                x, y = nx * 1.6 * ry - w / 2, ny * ry - 12
                clear &= all(x+w+3.999 <= ox or ox+ow+3.999 <= x or
                             y+24+3.999 <= oy or oy+oh+3.999 <= y
                             for ox, oy, ow, oh in rects)
                rects.append((x, y, w, 24))
            if clear:
                left = min(r[0] for r in rects)
                right = max(r[0]+r[2] for r in rects)
                bottom = min(r[1] for r in rects)
                top = max(r[1]+r[3] for r in rects)
                px, py = origin if origin is not None else (cx, cy)
                ox = max(region.x+scale*(12-left), min(px, region.x+region.width-scale*(12+right)))
                oy = max(region.y+scale*(12-bottom), min(py, region.y+region.height-scale*(12+top)))
                return {n['direction']: (ox + r[0]*scale, oy + r[1]*scale, r[2]*scale, r[3]*scale)
                        for n, r in zip(nodes, rects[1:])}
        raise AssertionError('tool ring fixture does not fit')

    def middle(rect):
        return rect[0] + rect[2]/2, rect[1] + rect[3]/2

    def open_ring(key):
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event(key)
        yield from settle()
        event('LEFTMOUSE')
        yield from settle()

    def gesture(key, name, direction, *, trigger_first=False):
        yield from open_ring(key)
        event('MOUSEMOVE', 'NOTHING', middle(ring(name)[direction]))
        yield from settle()
        if trigger_first:
            event(key, 'RELEASE')
            yield from settle()
            event('LEFTMOUSE', 'RELEASE')
        else:
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            event(key, 'RELEASE')
        yield from settle()
        check(not modals(), 'gesture left stale modal: ' + str(modals()))

    def overlap(old_key, *, old_release_first):
        slot = bpy.context.scene.transform_orientation_slots[2]
        slot.type = 'LOCAL'
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event(old_key)
        yield from settle()
        event('E')
        yield from settle()
        check(tool() == 'builtin.rotate', 'overlap must switch to Rotate immediately')
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
              old_key + '-down E-down must hand off one armed tool session: ' + str(modals()))
        check(modals().count('VIEW3D_OT_axismeld_hotbox_release_guard') == 1,
              'old trigger must retain independent release ownership')
        if old_release_first:
            event(old_key, 'RELEASE')
            yield from settle()
            check(modals() == ['VIEW3D_OT_axismeld_hotbox'],
                  'old release must be swallowed without cancelling E: ' + str(modals()))
        event('LEFTMOUSE')
        yield from settle()
        event('MOUSEMOVE', 'NOTHING', middle(ring('rotate')['W']))
        yield from settle()
        if not old_release_first:
            event('E', 'RELEASE')
            yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        event('E' if old_release_first else old_key, 'RELEASE')
        yield from settle()
        check(slot.type == ('GLOBAL' if old_release_first else 'LOCAL'),
              'overlap must commit only when mouse releases before the new trigger: ' + slot.type)
        check(not modals(), 'overlap left stale modal: ' + str(modals()))

    event('MOUSEMOVE', 'NOTHING')
    yield from settle()
    with override():
        ok, reason = adapter.available(bpy.context, 'orientation.move.object')
        check(ok, 'per-tool orientation adapter unavailable: ' + reason)
        check(adapter.run(bpy.context, 'orientation.move.object', invoke=False) == {'FINISHED'}, 'orientation failed')
    check(bpy.context.scene.transform_orientation_slots[1].type == 'LOCAL', 'Move slot not updated')
    check(bpy.context.scene.transform_orientation_slots[1].use, 'Move must use its own orientation slot')
    for key, expected in (('Q', 'builtin.select_box'), ('W', 'builtin.move'),
                           ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
        event(key)
        yield from settle()
        check(tool() == expected, key + ' must switch immediately')
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'one armed handler required')
        event(key, 'PRESS')  # Repeated key-down; simulate API has no repeat-flag setter.
        yield from settle()
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'repeat stacked modal')
        event(key, 'RELEASE')
        yield from settle()
        check(not modals(), 'tap left stale modal: ' + str(modals()))
    print('PASS immediate Q/W/E/R taps and repeat ownership', flush=True)

    yield from overlap('W', old_release_first=True)
    yield from overlap('W', old_release_first=False)

    # Handoff must not bypass mouse ownership or the existing Space release barrier.
    yield from open_ring('W')
    event('E')
    yield from settle()
    check(tool() == 'builtin.rotate', 'mouse-owned overlap must still switch the tool immediately')
    check(modals() == ['VIEW3D_OT_axismeld_hotbox_release_guard'],
          'an old owned mouse must block the new tool session: ' + str(modals()))
    event('W', 'RELEASE')
    event('LEFTMOUSE', 'RELEASE')
    event('E', 'RELEASE')
    yield from settle()
    check(not modals(), 'mouse-conflicting overlap left ownership')
    event('SPACE')
    yield from settle()
    event('ESC')
    event('ESC', 'RELEASE')
    yield from settle()
    event('W')
    yield from settle()
    check(modals() == ['VIEW3D_OT_axismeld_hotbox_release_guard'],
          'a Space-origin release guard must still block tool sessions: ' + str(modals()))
    event('SPACE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(not modals(), 'Space release barrier left ownership')

    edge = (region.x + 30, cy)
    slot = bpy.context.scene.transform_orientation_slots[1]
    for return_to_origin in (False, True):
        slot.type = 'LOCAL'
        event('MOUSEMOVE', 'NOTHING', edge)
        event('W')
        yield from settle()
        event('LEFTMOUSE')
        yield from settle()
        if return_to_origin:
            event('MOUSEMOVE', 'NOTHING', middle(ring('move', edge)['SW']))
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', edge)
            yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        event('W', 'RELEASE')
        yield from settle()
        check(slot.type == 'LOCAL',
              'edge origin committed World (returned=%s): %s' % (return_to_origin, slot.type))
        check(not modals(), 'edge origin left stale modal: ' + str(modals()))
    print('PASS overlapping tool-key handoff and edge-origin cancellation', flush=True)

    for key, name, index in (('W', 'move', 1), ('E', 'rotate', 2), ('R', 'scale', 3)):
        yield from gesture(key, name, 'NW')
        check(bpy.context.scene.transform_orientation_slots[index].type == 'LOCAL', name + ' Object failed')
        yield from gesture(key, name, 'W')
        check(bpy.context.scene.transform_orientation_slots[index].type == 'GLOBAL', name + ' World failed')
        yield from gesture(key, name, 'NE')
        check(bpy.context.scene.transform_orientation_slots[index].type == 'NORMAL', name + ' Normal failed')
    yield from gesture('E', 'rotate', 'E')
    check(bpy.context.scene.transform_orientation_slots[2].type == 'GIMBAL', 'Rotate Gimbal failed')
    check(bpy.context.scene.transform_orientation_slots[1].type == 'NORMAL' and
          bpy.context.scene.transform_orientation_slots[3].type == 'NORMAL', 'tool slots leaked')
    yield from gesture('Q', 'select', 'SW')
    check(tool() == 'builtin.select_lasso', 'Q release reset chosen Lasso')
    yield from gesture('Q', 'select', 'W')
    check(tool() == 'builtin.select_circle', 'Paint must adapt to persistent circle tool')
    yield from gesture('Q', 'select', 'NW')
    check(tool() == 'builtin.select_box', 'Marquee failed')
    for key, expected in (('W', 'builtin.move'), ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
        event(key)
        yield from settle()
        check(tool() == expected, 'tool switch at unchanged post-gesture pointer failed')
        event(key, 'RELEASE')
        yield from settle()
        check(not modals(), 'post-gesture tool tap left modal')
    print('PASS all real ring leaves and independent orientation slots', flush=True)
    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_geometry_fixture import native_list
    yield from open_ring('W')
    axis_rect = ring('move')['SW']
    event('MOUSEMOVE', 'NOTHING', middle(axis_rect))
    yield from settle()
    scale = bpy.context.preferences.system.ui_scale
    rows = native_list(axis_rect, ['View (Blender)', 'Custom Axis / Alignment', 'Tool Options', 'Preserve UV'],
                       lambda label: blf.dimensions(0, label)[0] / scale,
                       (region.x, region.y, region.width, region.height), scale)
    event('MOUSEMOVE', 'NOTHING', middle(rows[0]))
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(bpy.context.scene.transform_orientation_slots[1].type == 'VIEW', 'native Axis list View action failed')
    check(not modals(), 'native Axis list left modal')
    before = bpy.context.scene.transform_orientation_slots[1].type
    yield from gesture('W', 'move', 'W', trigger_first=True)
    check(bpy.context.scene.transform_orientation_slots[1].type == before, 'trigger-first committed')
    yield from open_ring('W')
    screenshot('m1-tools-move-ring.png')
    event('MOUSEMOVE', 'NOTHING', middle(ring('move')['N']))
    yield from settle()
    screenshot('m1-tools-native-child.png')
    event('MOUSEMOVE', 'NOTHING', middle(ring('move')['W']))
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(bpy.context.scene.transform_orientation_slots[1].type == before, 'native child leaked to background World')
    check(not modals(), 'disabled target left modal')
    yield from open_ring('W')
    event('ESC')
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    event('ESC', 'RELEASE')
    yield from settle()
    check(not modals(), 'Escape left modal')
    print('PASS trigger-first, disabled menu isolation and Escape', flush=True)

    # Clear is a native selection operation in both modes and owns its single undo entry.
    with override():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.ed.undo_push(message='Tool clear Object pre-action')
        check(adapter.run(bpy.context, 'selection.clear', invoke=False) == {'FINISHED'}, 'Object clear failed')
    check(not bpy.context.selected_objects, 'Object clear left selection')
    with override():
        bpy.ops.ed.undo()
    yield from settle()
    check(bool(bpy.context.selected_objects), 'Object clear undo failed')
    with override():
        cube = bpy.data.objects.get('Cube')
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.ed.undo_push(message='Tool clear Edit pre-action')
    yield from settle()
    yield from gesture('Q', 'select', 'SE')
    import bmesh
    check(not any(v.select for v in bmesh.from_edit_mesh(cube.data).verts), 'Edit clear failed')
    with override():
        bpy.ops.ed.undo()
    yield from settle()
    cube = bpy.context.edit_object
    check(any(v.select for v in bmesh.from_edit_mesh(cube.data).verts), 'Edit clear undo failed')
    yield from gesture('W', 'move', 'NW')
    check(bpy.context.scene.transform_orientation_slots[1].type == 'LOCAL', 'Edit Object direction failed')
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    yield from settle()
    print('PASS Object/Edit clear and native undo', flush=True)

    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    event('W')
    yield from settle()
    matrices = {o.name: tuple(tuple(row) for row in o.matrix_world) for o in bpy.context.scene.objects}
    selected = {o.name for o in bpy.context.selected_objects}
    event('MOUSEMOVE', 'NOTHING', (cx+70, cy+30))
    yield from settle()
    check(matrices == {o.name: tuple(tuple(row) for row in o.matrix_world) for o in bpy.context.scene.objects},
          'armed pointer motion transformed scene')
    check(selected == {o.name for o in bpy.context.selected_objects}, 'armed pointer motion selected')
    event('LEFTMOUSE', 'PRESS', alt=True)
    yield from settle()
    event('LEFTMOUSE', 'RELEASE', alt=True)
    event('W', 'RELEASE')
    yield from settle()
    check(not modals(), 'Alt navigation left tool modal: ' + str(modals()))
    event('W')
    yield from settle()
    event('BUTTON4MOUSE')
    yield from settle()
    check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'unrelated mouse action must leave armed tool menu')
    event('BUTTON4MOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    yield from open_ring('W')
    event('WINDOW_DEACTIVATE', 'NOTHING')
    yield from settle()
    check(not modals(), 'focus loss must clean tool ownership without old releases: ' + str(modals()))
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(not modals(), 'focus loss left modal')
    original_scene = win.scene
    event('W')
    yield from settle()
    win.scene = bpy.data.scenes.new('ToolContextChange')
    event('MOUSEMOVE', 'NOTHING')
    event('W', 'RELEASE')
    yield from settle()
    check(not modals(), 'scene change left modal')
    win.scene = original_scene
    yield from settle()
    print('PASS invisible motion, Alt navigation, focus loss and scene change', flush=True)

    yield from open_ring('W')
    with override():
        bpy.ops.screen.area_split(direction='VERTICAL', factor=.85)
    yield from settle(8)
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(not modals(), 'area resize left modal')
    area = max((a for a in win.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    print('PASS live region resize cancellation', flush=True)

    with override():
        bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
    yield from settle()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    yield from gesture('W', 'move', 'NW')
    check(bpy.context.scene.transform_orientation_slots[1].type == 'LOCAL', 'quad tool ring failed')
    with override():
        bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
    yield from settle()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    print('PASS quad and single tool gestures', flush=True)

    # Native user keymap edit: original W must stop arming; remapped F13 owns the release.
    binding = next(kmi for km in bpy.context.window_manager.keyconfigs.user.keymaps
                   for kmi in km.keymap_items if kmi.idname == 'axismeld.command' and
                   kmi.properties.command == 'transform.move')
    binding.type = 'F13'
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    yield from overlap('F13', old_release_first=True)
    yield from overlap('F13', old_release_first=False)
    yield from gesture('F13', 'move', 'W')
    check(bpy.context.scene.transform_orientation_slots[1].type == 'GLOBAL', 'remapped trigger failed')
    # keyconfigs.update rebuilds the resolved map; reacquire its current RNA item.
    binding = next(kmi for km in bpy.context.window_manager.keyconfigs.user.keymaps
                   for kmi in km.keymap_items if kmi.idname == 'axismeld.command' and
                   kmi.properties.command == 'transform.move' and kmi.type == 'F13')
    binding.active = False
    bpy.context.window_manager.keyconfigs.update()
    event('F13')
    yield from settle()
    check(not modals(), 'disabled binding armed tool menu')
    event('F13', 'RELEASE')
    yield from settle()
    print('PASS remapped trigger and disabled binding', flush=True)
    print('AXISMELD_TOOL_HOTBOX_EVENTS_PASS', flush=True)


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

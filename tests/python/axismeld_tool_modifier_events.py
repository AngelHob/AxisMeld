# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Profile-rebound keyboard tool modifiers and owned releases in a private GUI."""
import json
import os
from pathlib import Path
import sys
import traceback

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=6):
    for _ in range(count):
        yield


def suite():
    from axismeld import runtime

    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'AxisMeld preset did not load')
    scale = bpy.context.preferences.system.ui_scale
    center = (region.x + region.width // 2, region.y + region.height // 2)
    position = list(center)
    theme = bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu, theme.wcol_menu_back, theme.wcol_menu_item):
        colors.inner = (.8, .04, .65, 1)
        colors.inner_sel = (.8, .04, .65, 1)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def event(kind, value='PRESS', point=None, **mods):
        if point is not None:
            position[:] = map(int, point)
        win.event_simulate(type=kind, value=value, x=position[0], y=position[1], **mods)

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def armed(message):
        check(modals() == ['VIEW3D_OT_axismeld_hotbox'], message + ': ' + repr(modals()))

    def scene_state():
        return (tuple(sorted(o.name for o in bpy.context.selected_objects)),
                tuple((o.name, tuple(tuple(row) for row in o.matrix_world))
                      for o in bpy.context.scene.objects))

    def target(direction, name):
        path = artifacts / (name + '.png')
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
        finally:
            bpy.data.images.remove(image)
        rect = observed_radial_rectangles(
            pixels, scale, {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'})['rects'][direction]
        print('SCREENSHOT', path, flush=True)
        return ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)

    def begin(key, ctrl=False):
        event('MOUSEMOVE', 'NOTHING', center)
        if ctrl:
            event('LEFT_CTRL', ctrl=True)
        event(key, ctrl=ctrl)
        yield from settle()
        armed(('Ctrl+' if ctrl else '') + key + ' must survive the first timer/motion')
        event('MOUSEMOVE', 'NOTHING', center, ctrl=ctrl)
        yield from settle()
        armed('held trigger motion must retain the tool session')

    def stroke(direction, name, ctrl=False, point=None):
        event('MOUSEMOVE', 'NOTHING', point or center, ctrl=ctrl)
        event('LEFTMOUSE', ctrl=ctrl)
        yield from settle()
        event('MOUSEMOVE', 'NOTHING', target(direction, name), ctrl=ctrl)
        yield from settle()
        event('LEFTMOUSE', 'RELEASE', ctrl=ctrl)
        yield from settle()
        armed(name + ' mouse release must allow another stroke under the same held key')

    # Keep ordinary QWER sessions and their trigger ownership as a control.
    for key, tool in (('Q', 'builtin.select_box'), ('W', 'builtin.move'),
                      ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
        yield from begin(key)
        check(bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname == tool,
              key + ' did not select its normal tool')
        event(key, 'RELEASE')
        yield from settle()
        check(not modals(), key + ' release left ownership')
    slot = bpy.context.scene.transform_orientation_slots[1]
    slot.type = 'NORMAL'
    yield from begin('W')
    yield from stroke('NW', 'default-w-local')
    check(slot.type == 'LOCAL', 'default W first stroke did not set Local')
    yield from stroke('W', 'default-w-world')
    check(slot.type == 'GLOBAL', 'default W repeat stroke did not set World')
    event('W', 'RELEASE')
    yield from settle()
    check(not modals(), 'default W repeat strokes left ownership')
    print('PASS default QWER and repeated W strokes', flush=True)

    directory = runtime.profile_directory()
    check(directory.resolve().is_relative_to(root), 'profile directory escaped private root')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'user.json').write_text(json.dumps({
        'schema_version': 1, 'bindings': {'transform.move': {'type': 'F20', 'ctrl': True}}}),
        encoding='utf-8')
    config = runtime.load()
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    for name in ('Object Mode', 'Mesh'):
        bindings = [item for item in config.keymaps[name].keymap_items
                    if item.idname == 'axismeld.command' and
                    item.properties.command == 'transform.move']
        check(len(bindings) == 1 and bindings[0].type == 'F20' and bindings[0].ctrl,
              name + ' did not install the Ctrl+F20 profile binding')

    before_scene = scene_state()
    slot.type = 'NORMAL'
    yield from begin('F20', ctrl=True)
    yield from stroke('NW', 'ctrl-f20-local', ctrl=True)
    check(slot.type == 'LOCAL', 'Ctrl+F20 first stroke did not set Local')
    shifted = (center[0] + 80 * scale, center[1] + 50 * scale)
    yield from stroke('W', 'ctrl-f20-world', ctrl=True, point=shifted)
    check(slot.type == 'GLOBAL', 'Ctrl+F20 repeat stroke did not set World')
    event('F20', 'RELEASE', ctrl=True)
    yield from settle()
    check(not modals(), 'Ctrl+F20 trigger release left ownership')
    event('LEFT_CTRL', 'RELEASE')
    yield from settle()
    check(scene_state() == before_scene, 'orientation strokes changed scene or selection')
    print('PASS profile Ctrl+F20 and repeated LMB strokes at a new origin', flush=True)

    # Cancel while hovering a real command. Neither release order may dispatch it.
    for cancel in ('trigger', 'modifier', 'modified-mouse-release', 'focus'):
        slot.type = 'GLOBAL'
        yield from begin('F20', ctrl=True)
        event('LEFTMOUSE', ctrl=True)
        yield from settle()
        event('MOUSEMOVE', 'NOTHING', target('NW', 'cancel-' + cancel), ctrl=True)
        yield from settle()
        if cancel == 'trigger':
            event('F20', 'RELEASE', ctrl=True)
        elif cancel == 'modifier':
            event('LEFT_CTRL', 'RELEASE')
        elif cancel == 'modified-mouse-release':
            event('LEFTMOUSE', 'RELEASE')
        else:
            event('WINDOW_DEACTIVATE', 'NOTHING', ctrl=True)
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' not in modals(), cancel + ' did not close the tool')
        check(slot.type == 'GLOBAL', cancel + ' committed the hovered Local command')
        if cancel != 'modified-mouse-release':
            event('LEFTMOUSE', 'RELEASE', ctrl=cancel == 'trigger')
        if cancel != 'trigger':
            event('F20', 'RELEASE')
        event('LEFT_CTRL', 'RELEASE')
        yield from settle()
        check(not modals(), cancel + ' left release ownership: ' + repr(modals()))
        check(slot.type == 'GLOBAL' and scene_state() == before_scene,
              cancel + ' releases changed command, scene or selection')
    print('PASS trigger/modifier/modified mouse release and focus cancellation', flush=True)

    yield from begin('F20', ctrl=True)
    yield from stroke('NW', 'ctrl-f20-before-rearm-cancel', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle()
    check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'modifier release did not cancel rearmed wait')
    event('F20', 'RELEASE')
    yield from settle()
    check(not modals() and slot.type == 'LOCAL', 'rearmed modifier cancellation changed prior result')
    print('PASS modifier release during rearmed wait', flush=True)

    # Primary Space has no tool root and retains its independent modifier handling.
    event('MOUSEMOVE', 'NOTHING', center)
    event('SPACE')
    yield from settle(12)
    armed('primary Space did not open')
    event('LEFT_CTRL', ctrl=True)
    yield from settle()
    armed('primary Space must retain its existing modifier behavior')
    event('LEFT_CTRL', 'RELEASE')
    event('SPACE', 'RELEASE')
    yield from settle()
    check(not modals(), 'primary Space release left ownership')
    print('PASS primary Space retains its separate input lifecycle', flush=True)
    print('AXISMELD_TOOL_MODIFIER_EVENTS_PASS', flush=True)


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

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Private real preferences callbacks, persisted appearance, rendering and reset isolation."""
import json
import os
from pathlib import Path
import traceback

import bpy
import blf

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
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    from axismeld import hotbox_runtime, runtime
    prefs = bpy.context.window_manager.keyconfigs.active.preferences
    check(hasattr(prefs, 'hotbox_background'), 'missing appearance preferences')
    check(prefs.hotbox_brightness == -13 and prefs.hotbox_transparency == '25',
          'fresh appearance defaults are not dark / 75 percent opaque')
    opacity = prefs.bl_rna.properties['hotbox_transparency']
    check(opacity.name == 'Primary Hotbox Opacity' and opacity.enum_items['25'].name == '75%',
          'opacity UI must not invert the existing transparency model')
    directory = runtime.profile_directory()
    check(directory.resolve().is_relative_to(root), 'profile directory escaped test root')
    prefs.hotbox_style = 'zones'
    prefs.hotbox_center_rightmouse = 'pane.shading'
    prefs.hotbox_theme_background = False
    prefs.hotbox_background = (51/255, 102/255, 153/255)
    prefs.hotbox_brightness = -13
    prefs.hotbox_text = (204/255, 230/255, 51/255)
    prefs.hotbox_placeholder = (230/255, 51/255, 77/255)
    prefs.hotbox_theme_hover_text = False
    prefs.hotbox_hover_text = (51/255, 230/255, 230/255)
    saved = (directory / 'hotbox_user.json').read_bytes()
    hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {}})
    appearance = hotbox_runtime.current_settings()['appearance']
    check(appearance['background'] == [51, 102, 153] and appearance['text'] == [204, 230, 51]
          and appearance['placeholder'] == [230, 51, 77] and appearance['hover_text'] == [51, 230, 230],
          'color picker values did not persist as RGB bytes')
    check((directory / 'hotbox_user.json').read_bytes() == saved, 'reload unexpectedly rewrote profile')
    check(bpy.ops.axismeld.hotbox_reset_appearance() == {'FINISHED'}, 'appearance reset failed')
    check(prefs.hotbox_style == 'zones' and prefs.hotbox_center_rightmouse == 'pane.shading',
          'appearance reset changed layout or mouse bindings')
    check(prefs.hotbox_theme_background and prefs.hotbox_theme_hover_text and
          prefs.hotbox_brightness == -13 and prefs.hotbox_transparency == '25', 'reset default mismatch')
    check(json.loads((directory / 'hotbox_user.json').read_text()) == {
        'schema_version': 1, 'settings': {'style': 'zones', 'center_buttons': {'RIGHTMOUSE': 'pane.shading'}}},
        'reset left appearance overrides or removed unrelated settings')

    # Session-only mode must still display and render edits but never write personal files.
    prefs.use_file_overrides = False
    before = (directory / 'hotbox_user.json').read_bytes()
    prefs.hotbox_theme_background = False
    prefs.hotbox_background = (51/255, 102/255, 153/255)
    prefs.hotbox_text = (204/255, 230/255, 51/255)
    prefs.hotbox_placeholder = (230/255, 51/255, 77/255)
    prefs.hotbox_theme_hover_text = False
    prefs.hotbox_hover_text = (51/255, 230/255, 230/255)
    prefs.hotbox_transparency = '0'
    check((directory / 'hotbox_user.json').read_bytes() == before, 'session-only edit wrote file')
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    cx, cy = region.x + region.width//2, region.y + region.height//2
    scale = bpy.context.preferences.system.ui_scale
    pos = [cx, cy]

    def event(kind, value='PRESS', point=None):
        if point:
            pos[:] = [int(v) for v in point]
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1])

    def capture(name):
        path = artifacts / name
        bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        img = bpy.data.images.load(str(path), check_existing=False)
        result = list(img.pixels), img.size[0]
        bpy.data.images.remove(img)
        return result

    yield from settle()
    event('MOUSEMOVE', 'NOTHING')
    event('SPACE')
    yield from settle(8)
    pixels, width = capture('appearance-custom.png')
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    labels = ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
    widths = [blf.dimensions(0, label)[0] + 40*scale for label in labels]
    left = cx - (sum(widths) + 60*scale)/2

    def center(index):
        return left + sum(widths[:index]) + 10*scale*index + widths[index]/2

    def sample(x, y):
        start = (int(y)*width+int(x))*4
        return pixels[start:start+3]

    def has_ink(index, rgb):
        half = blf.dimensions(0, labels[index])[0]/2
        return any(max(abs(a-b/255) for a, b in zip(sample(x, y), rgb)) < .06
                   for y in range(int(cy+90*scale), int(cy+102*scale))
                   for x in range(int(center(index)-half), int(center(index)+half)))

    color = sample(center(0), cy+86*scale)
    check(max(abs(a-b/255) for a, b in zip(color, [38, 89, 140])) < .025,
          f'custom background/brightness not rendered: {color}')
    check(has_ink(0, [230, 51, 77]), 'placeholder RGB not rendered')
    check(has_ink(3, [204, 230, 51]), 'normal text RGB not rendered')
    event('MOUSEMOVE', 'NOTHING', (center(3), cy+96*scale))
    yield from settle()
    pixels, width = capture('appearance-hover.png')
    check(has_ink(3, [51, 230, 230]), 'custom hover text RGB not rendered')
    event('SPACE', 'RELEASE')
    yield from settle()

    for channel, brightness, name in ((0, -128, 'black'), (1, 128, 'white')):
        prefs.hotbox_background = (channel, channel, channel)
        prefs.hotbox_brightness = brightness
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event('SPACE')
        yield from settle(8)
        pixels, width = capture(f'appearance-clamp-{name}.png')
        check(max(abs(v-channel) for v in sample(center(0), cy+86*scale)) < .02,
              f'brightness must clamp RGB at {name}, not wrap around')
        event('SPACE', 'RELEASE')
        yield from settle()

    check(bpy.ops.axismeld.hotbox_reset_appearance() == {'FINISHED'}, 'session reset failed')
    check((directory / 'hotbox_user.json').read_bytes() == before, 'session reset wrote personal file')
    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    event('SPACE')
    yield from settle(8)
    capture('appearance-default.png')
    event('SPACE', 'RELEASE')
    yield from settle()

    # Redraw the real KEYMAP preference editor, including registered color controls and reset.
    area.type = 'PREFERENCES'
    bpy.context.preferences.active_section = 'KEYMAP'
    event('MOUSEMOVE', 'NOTHING', (80, 120))
    yield from settle(12)
    capture('appearance-preferences.png')
    print('AXISMELD_HOTBOX_APPEARANCE_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
    except StopIteration:
        bpy.ops.wm.quit_blender()
        return None
    except BaseException:
        traceback.print_exc()
        bpy.ops.wm.quit_blender()
        return None
    return .1


bpy.app.timers.register(tick, first_interval=.5)

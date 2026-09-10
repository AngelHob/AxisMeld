# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual opt-in preset Space entry: visible menu and native RMB seven-view acceptance."""
import os
from pathlib import Path
import sys
import traceback
import json
import bpy
import blf

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(root):
    raise RuntimeError('Only the isolated GUI runner may run this test')
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
region_receipts = []


class AXISMELD_OT_menu_region_probe(bpy.types.Operator):
    bl_idname = 'axismeld.menu_region_probe'
    bl_label = 'Private region receipt'
    def invoke(self, context, event):
        region_receipts.append((context.area.type, context.region.type, event.mouse_x, event.mouse_y))
        return {'FINISHED'}


def check(value, label):
    if not value:
        raise AssertionError(label)


def settle(count=4):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    if os.environ.get('AXISMELD_TEST_FONT_POINTS'):
        bpy.context.preferences.ui_styles[0].widget.points = float(os.environ['AXISMELD_TEST_FONT_POINTS'])
    icon_probe = bool(os.environ.get('AXISMELD_TEST_ICON_SCALE_PROBE'))
    if icon_probe:
        bpy.context.preferences.view.ui_scale = 2.0
    yield from settle(8)
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    position = [cx, cy]
    theme_probe = bool(os.environ.get('AXISMELD_TEST_THEME_PROBE'))
    alpha_probe = bool(os.environ.get('AXISMELD_TEST_ICON_ALPHA_PROBE'))
    if alpha_probe:
        colors = bpy.context.preferences.themes[0].user_interface.wcol_menu
        colors.inner = colors.inner_sel = (0, 0, 0, 1)
        colors.text = colors.text_sel = (1, 1, 1)
        from axismeld import hotbox_runtime
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': 1, 'settings': {'transparency': 0}})
    if theme_probe:
        # Deliberately distinctive native theme, scoped to this disposable process.
        bpy.context.preferences.themes[0].user_interface.wcol_menu.inner = (.8, .12, .04, 1)
        bpy.context.preferences.themes[0].user_interface.wcol_menu.inner_sel = (.8, .12, .04, 1)
    native_style_probe = bool(os.environ.get('AXISMELD_TEST_NATIVE_STYLE'))
    if native_style_probe:
        bpy.context.preferences.themes[0].user_interface.wcol_menu_back.inner = (.8, .12, .04, 1)

    def event(kind, value='PRESS', x=None, y=None):
        if x is not None:
            position[:] = [int(x), int(y)]
        win.event_simulate(type=kind, value=value, x=position[0], y=position[1])

    def screenshot(name):
        path = artifacts / name
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        return path

    event('MOUSEMOVE', 'NOTHING', cx, cy)
    yield from settle()
    before_path = screenshot('menus-before.png')
    event('SPACE')
    yield from settle(8)
    path = screenshot('menus-main.png')
    # Common row is at center + 96 logical pixels. A broad strip must visibly change;
    # the old fixed four labels never draw there. Compare real rendered pixels.
    before = bpy.data.images.load(str(before_path), check_existing=False)
    after = bpy.data.images.load(str(path), check_existing=False)
    scale = bpy.context.preferences.system.ui_scale
    a, b = list(before.pixels), list(after.pixels)
    width = after.size[0]
    if alpha_probe:
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        common_labels = ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
        span = (sum(blf.dimensions(0, text)[0]/scale + 40 for text in common_labels) + 60) / .72
        center_width = blf.dimensions(0, 'AxisMeld')[0]/scale + 60
        side_width = blf.dimensions(0, 'Recent Commands')[0]/scale + 60
        recent_center = cx - (center_width/2 + 83.6 + side_width/2)*scale
        text_width = blf.dimensions(0, 'Recent Commands')[0]
        left = recent_center - (text_width + 20*scale)/2
        def foreground_peak(x0, x1):
            return max(min(b[(y*width+x)*4:(y*width+x)*4+3])
                       for y in range(int(cy-6*scale), int(cy+6*scale))
                       for x in range(int(x0), int(x1)))
        icon_peak = foreground_peak(left, left + 16*scale)
        text_peak = foreground_peak(left + 20*scale, left + 20*scale + text_width)
        check(icon_peak >= text_peak*.8,
              f'disabled icon alpha applied twice: icon={icon_peak}, text={text_peak}')
        event('SPACE', 'RELEASE')
        yield from settle()
        print('PASS disabled icon and text use the same single theme-alpha attenuation', flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    if icon_probe:
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        left = cx - (blf.dimensions(0, 'AxisMeld')[0] + 20 * scale) / 2
        # At 2x the upper half of the center icon must contain rendered foreground.
        # An unscaled 16px icon sits entirely below this band in its reserved 32px slot.
        icon_pixels = 0
        for y in range(int(cy + 2 * scale), int(cy + 7 * scale)):
            for x in range(int(left), int(left + 16 * scale)):
                i = (y * width + x) * 4
                icon_pixels += min(b[i:i+3]) > .65 and sum(abs(a[i+k] - b[i+k]) for k in range(3)) > .3
        check(icon_pixels > 5, f'2x native icon did not scale into its slot: {icon_pixels}')
        event('SPACE', 'RELEASE')
        yield from settle()
        print('PASS 2x native semantic icon occupies the scaled slot', flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    if theme_probe:
        themed_pixels = 0
        for y in range(int(cy - 80 * scale), int(cy + 80 * scale)):
            for x in range(int(cx - 100 * scale), int(cx + 100 * scale)):
                i = (y * width + x) * 4
                red, green, blue = b[i:i+3]
                themed_pixels += (red > green * 3 and red > blue * 3 and
                                  sum(abs(a[i+k] - b[i+k]) for k in range(3)) > .2)
        check(themed_pixels > 1500 * scale * scale,
              f'menu must use native theme background, changed red pixels={themed_pixels}')
        print('PASS hotbox uses native theme menu background', flush=True)
        event('SPACE', 'RELEASE')
        yield from settle()
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    changed = 0
    for y in range(int(cy + 87 * scale), int(cy + 105 * scale)):
        for x in range(int(cx - 170 * scale), int(cx + 170 * scale)):
            i = (y * width + x) * 4
            changed += sum(abs(a[i + k] - b[i + k]) for k in range(3)) > .08
    failures = []
    if changed < 1000 * scale * scale:
        failures.append(f'Space main Common directory missing: changed pixels={changed}')
    bpy.data.images.remove(before)
    bpy.data.images.remove(after)
    if os.environ.get('AXISMELD_TEST_OVERLAY'):
        event('SPACE', 'RELEASE')
        yield from settle()
        for requested_scale in (1.0, 2.0):
            bpy.context.preferences.view.ui_scale = requested_scale
            yield from settle(8)
            scale = bpy.context.preferences.system.ui_scale
            region = next(r for r in area.regions if r.type == 'WINDOW')
            cx, cy = region.x + region.width // 2, region.y + region.height // 2
            event('MOUSEMOVE', 'NOTHING', cx, cy)
            yield from settle()
            event('SPACE')
            yield from settle(8)
            main = screenshot(f'overlay-{requested_scale}-main.png')
            blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
            span = sum(blf.dimensions(0, label)[0]/scale + 40 for label in
                       ('File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows')) + 60
            def difference(first, second, bounds):
                images = [bpy.data.images.load(str(p), check_existing=False) for p in (first, second)]
                pixels = [list(im.pixels) for im in images]
                w = images[0].size[0]
                x0, y0, x1, y1 = (int(v) for v in bounds)
                changed = sum(sum(abs(pixels[0][(y*w+x)*4+k]-pixels[1][(y*w+x)*4+k])
                                  for k in range(3)) > .08
                              for y in range(y0, y1) for x in range(x0, x1))
                for im in images:
                    bpy.data.images.remove(im)
                return changed
            # A known, unoccluded portion of the first-level File title must not disappear
            # or move with an off-center RMB origin.
            sample = (cx-span*scale/2+8*scale, cy+90*scale,
                      cx-span*scale/2+24*scale, cy+102*scale)
            event('MOUSEMOVE', 'NOTHING', cx+12*scale, cy)
            event('RIGHTMOUSE')
            yield from settle()
            held = screenshot(f'overlay-{requested_scale}-held.png')
            check(difference(main, held, sample) == 0,
                  f'{requested_scale}x first-level File disappeared or shifted behind secondary')
            edit_left = cx-span*scale/2 + blf.dimensions(0, 'File')[0] + 50*scale
            check(difference(main, held, (edit_left+15*scale, cy+91*scale,
                                          edit_left+35*scale, cy+101*scale)) == 0,
                  'partial button overlap erased unoccluded first-level Edit text')
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            other = screenshot(f'overlay-{requested_scale}-other-release.png')
            check(difference(held, other, (cx-220*scale, cy-170*scale,
                                           cx+220*scale, cy+170*scale)) == 0,
                  'non-owning release changed the overlay')
            event('RIGHTMOUSE', 'RELEASE')
            event('MOUSEMOVE', 'NOTHING', cx, cy)
            yield from settle()
            returned = screenshot(f'overlay-{requested_scale}-returned.png')
            check(difference(main, returned, (region.x, region.y, region.x+region.width,
                                              region.y+region.height)) == 0,
                  'neutral owner release did not restore the same live first-level hotbox')
            # Re-entry without releasing Space proves that the original modal survives.
            event('RIGHTMOUSE')
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', cx+90*scale, cy)
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            with bpy.context.temp_override(window=win, area=area, region=region):
                rv = bpy.context.region_data
                check(rv.view_perspective == 'ORTHO' and
                      abs(abs(sum(a*b for a,b in zip(rv.view_rotation, (.5,.5,.5,.5))))-1) < 1e-5,
                      'repeat entry failed to dispatch Right View')
            event('SPACE', 'RELEASE')
            yield from settle()
        print('PASS retained parent, fixed root, owned neutral release and repeat view entry at 1x/2x', flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    if os.environ.get('AXISMELD_TEST_DRAG_GUIDE'):
        event('SPACE', 'RELEASE')
        yield from settle()
        for requested_scale in (1.0, 2.0):
            bpy.context.preferences.view.ui_scale = requested_scale
            yield from settle(8)
            region = next(r for r in area.regions if r.type == 'WINDOW')
            scale = bpy.context.preferences.system.ui_scale
            cx, cy = region.x + region.width // 2, region.y + region.height // 2
            # Off-center press distinguishes the real gesture origin from the menu anchor.
            ox, oy = cx + 12 * scale, cy
            event('MOUSEMOVE', 'NOTHING', cx, cy)
            yield from settle()
            event('SPACE')
            yield from settle(8)
            event('MOUSEMOVE', 'NOTHING', ox, oy)
            event('RIGHTMOUSE')
            yield from settle()
            stationary = screenshot(f'guide-{requested_scale}-stationary.png')
            # Empty NE sector: no label/command changes along this short stroke.
            event('MOUSEMOVE', 'NOTHING', ox + 40 * scale, oy + 40 * scale)
            yield from settle()
            dragged = screenshot(f'guide-{requested_scale}-dragged.png')
            def line_pixels(first, second):
                images = [bpy.data.images.load(str(p), check_existing=False) for p in (first, second)]
                w = images[0].size[0]
                pixels = [list(im.pixels) for im in images]
                count = 0
                for offset in range(int(24 * scale), int(37 * scale)):
                    for across in range(-2, 3):
                        i = (int(oy + offset) * w + int(ox + offset) + across) * 4
                        count += sum(abs(pixels[0][i+k] - pixels[1][i+k]) for k in range(3)) > .2
                for im in images:
                    bpy.data.images.remove(im)
                return count
            check(line_pixels(stationary, dragged) > 8 * scale,
                  f'{requested_scale}x missing press-origin drag guide in empty NE corridor')
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            other_release = screenshot(f'guide-{requested_scale}-other-release.png')
            check(line_pixels(dragged, other_release) == 0, 'non-owner release removed guide')
            event('MOUSEMOVE', 'NOTHING', ox, oy)
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            # Move again without a held button: zero-length geometry alone must not mask
            # a missing owner-release state transition.
            event('MOUSEMOVE', 'NOTHING', ox + 40 * scale, oy + 40 * scale)
            yield from settle()
            released = screenshot(f'guide-{requested_scale}-released.png')
            check(line_pixels(stationary, released) == 0, 'guide remained after neutral release')
            event('SPACE', 'RELEASE')
            yield from settle()
        from axismeld import hotbox_runtime
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': 1, 'settings': {'center_buttons': {'RIGHTMOUSE': 'common.select'}}})
        for cancellation in ('ESC', 'SPACE'):
            event('MOUSEMOVE', 'NOTHING', cx, cy)
            yield from settle()
            clean = screenshot(f'guide-menu-{cancellation}-clean.png')
            event('SPACE')
            yield from settle(8)
            event('MOUSEMOVE', 'NOTHING', ox, oy)
            event('RIGHTMOUSE')
            yield from settle()
            stationary = screenshot(f'guide-menu-{cancellation}-stationary.png')
            event('MOUSEMOVE', 'NOTHING', ox + 40 * scale, oy + 40 * scale)
            yield from settle()
            dragged = screenshot(f'guide-menu-{cancellation}-dragged.png')
            check(line_pixels(stationary, dragged) > 8 * scale,
                  'ordinary mapped menu missing held-drag guide')
            event(cancellation, 'PRESS' if cancellation == 'ESC' else 'RELEASE')
            yield from settle()
            event('RIGHTMOUSE', 'RELEASE')
            if cancellation == 'ESC':
                event('ESC', 'RELEASE')
                event('SPACE', 'RELEASE')
            yield from settle()
            cancelled = screenshot(f'guide-menu-{cancellation}-cancelled.png')
            check(line_pixels(clean, cancelled) == 0, f'{cancellation} left a ghost guide')
        print('PASS drag guide at 1x/2x, real press origin, owner release, ordinary menus and Esc/Space cleanup',
              flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    event('RIGHTMOUSE')
    yield
    event('MOUSEMOVE', 'NOTHING', cx - 90 * scale, cy + 90 * scale)
    yield from settle()
    screenshot('menus-rmb-left-candidate.png')
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        rv = bpy.context.region_data
        left = (.5, .5, -.5, -.5)
        if rv.view_perspective != 'ORTHO' or abs(abs(sum(a*b for a,b in zip(rv.view_rotation, left)))-1) > 1e-5:
            failures.append(f'Space+RMB NW must select Left; actual={tuple(rv.view_rotation)}, {rv.view_perspective}')
    event('SPACE', 'RELEASE')
    yield from settle()
    check(not failures, '\n'.join(failures))
    print('PASS actual Space main directory screenshot and RMB NW native Left view', flush=True)
    if os.environ.get('AXISMELD_TEST_VISUAL_ONLY'):
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return

    from axismeld import hotbox_runtime, runtime
    from axismeld.commands import COMMANDS
    hotbox_user = runtime.profile_directory() / 'hotbox_user.json'
    def reset_hotbox_settings():
        hotbox_user.unlink(missing_ok=True)
        hotbox_runtime.reload_settings(
            bpy.context, session={'schema_version': 1, 'settings': {}})
    observed = []
    real_dispatch = hotbox_runtime.dispatch
    def observed_dispatch(context, command):
        result = real_dispatch(context, command)
        observed.append((command, result))
        return result
    hotbox_runtime.dispatch = observed_dispatch
    settings_observed = []
    real_apply_setting = hotbox_runtime.apply_setting
    def observed_setting(context, setting, value):
        result = real_apply_setting(context, setting, value)
        settings_observed.append((setting, value, result))
        return result
    hotbox_runtime.apply_setting = observed_setting

    def locate(x=None, y=None):
        x, y = (cx, cy) if x is None else (x, y)
        event('MOUSEMOVE', 'NOTHING', x, y)
        yield from settle()

    def open_box():
        yield from locate()
        event('SPACE')
        yield

    def close_box():
        event('SPACE', 'RELEASE')
        yield from settle()

    def move(point):
        event('MOUSEMOVE', 'NOTHING', *point)
        yield from settle()

    def click(point, button='LEFTMOUSE'):
        yield from move(point)
        event(button)
        yield
        event(button, 'RELEASE')
        yield from settle()

    def current_pose():
        with bpy.context.temp_override(window=win, area=area, region=region):
            rv = bpy.context.region_data
            return tuple(rv.view_rotation), rv.view_perspective

    directions = (
        (-90, 90, 'view.left', (.5, .5, -.5, -.5)),
        (90, 0, 'view.side', (.5, .5, .5, .5)),
        (0, -90, 'view.front', (.70710678, .70710678, 0, 0)),
        (-90, 0, 'view.top', (1, 0, 0, 0)),
        (-90, -90, 'view.back', (0, 0, .70710678, .70710678)),
        (90, -90, 'view.bottom', (0, 1, 0, 0)),
        (0, 90, 'view.perspective', None),
    )
    # Continuous motion crosses the retained first-level center before reaching a sector.
    # A single large synthetic jump cannot catch an underlying hover stealing the gesture.
    for requested_scale in (1.0, 2.0):
        bpy.context.preferences.view.ui_scale = requested_scale
        yield from settle(8)
        scale = bpy.context.preferences.system.ui_scale
        for dx, dy, command, rotation in directions:
            yield from open_box()
            count, setting_count = len(observed), len(settings_observed)
            event('RIGHTMOUSE')
            yield
            for distance in (1, 3, 6, 10, 15, 30, 50, 70, 90):
                event('MOUSEMOVE', 'NOTHING', cx+dx/90*distance*scale, cy+dy/90*distance*scale)
                yield
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count+1 and observed[-1] == (command, {'FINISHED'}) and
                  len(settings_observed) == setting_count,
                  f'segmented 1/3/6/10/15/30/50/70/90 motion at {scale}x stole {command}')
            yield from close_box()
        yield from open_box()
        count, setting_count = len(observed), len(settings_observed)
        event('RIGHTMOUSE')
        yield
        for distance in (1, 3, 6, 10, 15):
            event('MOUSEMOVE', 'NOTHING', cx+distance*scale, cy)
            yield
        screenshot(f'menus-segmented-near-side-{scale}.png')
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count+1 and observed[-1] == ('view.side', {'FINISHED'}) and
              len(settings_observed) == setting_count,
              f'15 logical pixels at {scale}x must select Side outside the 12px dead zone')
        yield from close_box()
    bpy.context.preferences.view.ui_scale = 1.0
    yield from settle(8)
    scale = bpy.context.preferences.system.ui_scale
    print('PASS segmented seven-direction motion and near 15px Side at 1x/2x', flush=True)
    if os.environ.get('AXISMELD_TEST_SEGMENTED_PROBE'):
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    for button in ('RIGHTMOUSE', 'LEFTMOUSE', 'MIDDLEMOUSE'):
        for dx, dy, command, rotation in directions:
            yield from open_box()
            event(button)
            yield
            event('MOUSEMOVE', 'NOTHING', cx + dx * scale, cy + dy * scale)
            yield
            count = len(observed)
            event(button, 'RELEASE')
            yield from settle()
            check(len(observed) == count + 1 and observed[-1] == (command, {'FINISHED'}),
                  f'{button} {command} must execute exactly once')
            q, projection = current_pose()
            check(projection == ('PERSP' if rotation is None else 'ORTHO'), command + ' projection')
            if rotation:
                check(abs(abs(sum(a*b for a,b in zip(q, rotation))) - 1) < 1e-5,
                      command + ' literal Z-up orientation')
            yield from close_box()
            check(len(observed) == count + 1, 'mouse action followed by Space became tap')
    print('PASS B1/B2 all default mouse buttons: seven actual directions exactly once', flush=True)

    for dx, dy in ((0, 0), (6, 0), (40, 40)):
        yield from open_box()
        original = current_pose()
        count = len(observed)
        setting_count = len(settings_observed)
        event('RIGHTMOUSE')
        yield
        event('MOUSEMOVE', 'NOTHING', cx + dx * scale, cy + dy * scale)
        yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from close_box()
        check(len(observed) == count and current_pose() == original, 'NE/deadzone executed')
        check(len(settings_observed) == setting_count, 'NE/deadzone submitted a setting')
    if os.environ.get('AXISMELD_TEST_DEADZONE_PROBE'):
        print('PASS deadzone/NE dispatched neither commands nor settings; 21 direction positive controls',
              flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    for cancel in ('SPACE', 'ESC'):
        yield from open_box()
        count = len(observed)
        original = current_pose()
        event('RIGHTMOUSE')
        yield
        event('MOUSEMOVE', 'NOTHING', cx + 90, cy)
        yield
        event(cancel, 'RELEASE' if cancel == 'SPACE' else 'PRESS')
        yield
        event('RIGHTMOUSE', 'RELEASE')
        if cancel == 'ESC':
            event('SPACE', 'RELEASE')
        yield from settle()
        check(len(observed) == count and current_pose() == original, 'reverse release/Esc committed')
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    event('MOUSEMOVE', 'NOTHING', cx - 90, cy + 90)
    yield
    count = len(observed)
    event('LEFTMOUSE')
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    check(len(observed) == count, 'second mouse committed RMB candidate')
    event('RIGHTMOUSE', 'RELEASE')
    yield from close_box()
    check(len(observed) == count + 1 and observed[-1][0] == 'view.left', 'owning mouse lost candidate')

    # Measured public labels provide input positions only; all effects below are literal.
    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_geometry_fixture import ellipse_page, native_list, style_list
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    icon_labels = {'AxisMeld', 'AxisMeld Views', 'Recent Commands', 'Hotbox Controls',
                   'Wireframe', 'Solid', 'Perspective View', 'Right View', 'Bottom View',
                   'Front View', 'Back View', 'Top View', 'Left View', 'Vertex', 'Edge', 'Face'}
    def label_width(label):
        native_icon = label in icon_labels or label.startswith(('Entry ', 'Parent ', 'Child '))
        return blf.dimensions(0, label)[0] / scale + (20 if native_icon else 0)
    common_labels = ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
    common_span = sum(label_width(label) + 40 for label in common_labels) + 60
    center_span = common_span / .72
    def row_title(labels, index, dy):
        widths = [label_width(label) + 40 for label in labels]
        if dy == 48:
            extra = (common_span * (.92 / .72) - sum(widths) - 10*(len(widths)-1)) / len(widths)
            widths = [width + extra for width in widths]
        start = cx / scale - (sum(widths) + 10 * (len(widths)-1)) / 2
        x = start + sum(widths[:index]) + 10 * index
        return (x * scale, cy + (dy-19) * scale, widths[index] * scale, 38 * scale)
    def midpoint(rect):
        check(rect is not None, 'input attempted an off-page item')
        x, y, w, h = rect
        return x+w/2, y+h/2
    def page(anchor, labels, first=0):
        native_labels = (
            ['Zones and Menu Rows', 'Zones Only', 'Center Zone Only'],
            ['Show Common Menus', 'Show Pane Specific Menus', 'Show Modeling'],
            ['0%', '25%', '50%', '75%', '100%'],
        )
        if labels in native_labels:
            return {'items': native_list(anchor, labels, label_width,
                                        (region.x, region.y, region.width, region.height), scale)}
        views = bool(labels and labels[0] == 'Perspective View')
        measure = (lambda label: blf.dimensions(0, label)[0] / scale) if views else label_width
        return ellipse_page(anchor, labels, measure,
                            (region.x, region.y, region.width, region.height), scale, first,
                            views=views)
    def popup(anchor, labels, first=0):
        return page(anchor, labels, first)['items']
    if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') == 'quad':
        bpy.context.preferences.view.ui_scale = 2.0
        yield from settle(8)
        scale = bpy.context.preferences.system.ui_scale
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        area.spaces.active.show_region_toolbar = False
        area.spaces.active.show_region_header = False
        area.spaces.active.show_region_tool_header = False
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        region = next(r for r in area.regions if r.type == 'WINDOW')
        cx, cy = region.x+region.width//2, region.y+region.height//2
        print('ROOMY_QUAD_2X', region.width/scale, region.height/scale, flush=True)
        check(340 <= region.width/scale < 480 and 200 <= region.height/scale < 320,
              'actual quad must exercise compact logical geometry at 2x')
        anchor = (cx-(label_width('AxisMeld')+40)*scale/2, cy-19*scale,
                  (label_width('AxisMeld')+40)*scale, 38*scale)
        labels = ['Perspective View', 'Right View', 'Bottom View', 'Front View',
                  'Back View', 'Top View', 'Left View', '', 'Hotbox Style']
        for index, command in enumerate(('view.perspective', 'view.side', 'view.bottom',
                                          'view.front', 'view.back', 'view.top', 'view.left')):
            yield from open_box()
            if index == 0:
                screenshot('menus-quad-2x-compact-main.png')
            event('RIGHTMOUSE')
            yield
            positions = popup(anchor, labels)
            yield from move(midpoint(positions[index]))
            if index == 0:
                screenshot('menus-quad-2x-seven-views.png')
            count = len(observed)
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count+1 and observed[-1] == (command, {'FINISHED'}),
                  '2x quad visible button ' + command)
            yield from close_box()
        original_snapshot = hotbox_runtime.snapshot
        def quad_snapshot(context):
            value = json.loads(original_snapshot(context))
            value['settings']['center_buttons']['RIGHTMOUSE'] = 'common.select'
            value['menus'][0]['children'][3]['children'] = [
                dict(id=f'quad.{i}', kind='command', label=f'Entry {i:02}',
                     command='view.top' if i == 17 else 'view.front', enabled=True,
                     reason='', children=[]) for i in range(18)]
            return json.dumps(value)
        hotbox_runtime.snapshot = quad_snapshot
        yield from open_box()
        event('RIGHTMOUSE')
        yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        labels = [f'Entry {i:02}' for i in range(18)]
        current = page(anchor, labels)
        check(current['capacity'] < 8, 'quad overflow must reduce capacity, never target size')
        screenshot('menus-quad-2x-page-first.png')
        while current['first'] + current['capacity'] < 18:
            yield from click(midpoint(current['next']))
            current = page(anchor, labels, current['first']+1)
        screenshot('menus-quad-2x-page-last.png')
        count = len(observed)
        yield from click(midpoint(current['items'][17]))
        check(len(observed) == count+1 and observed[-1] == ('view.top', {'FINISHED'}),
              '2x quad long ellipse final page leaf')
        yield from close_box()
        print('PASS actual 2x quad: all seven visible views and final long-menu page', flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') in {'corner', 'latch'}:
        area.spaces.active.show_region_toolbar = False
        area.spaces.active.show_region_header = False
        area.spaces.active.show_region_tool_header = False
        yield from settle(8)
        cx, cy = region.x+2, region.y+2
        anchor = (region.x, region.y, (label_width('AxisMeld')+40)*scale, 38*scale)
        labels = ['Perspective View', 'Right View', 'Bottom View', 'Front View',
                  'Back View', 'Top View', 'Left View', '', 'Hotbox Style']
        if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') == 'latch':
            hotbox_runtime.reload_settings(bpy.context, session={
                'schema_version': 1, 'settings': {'center_buttons': {'RIGHTMOUSE': 'pane.shading'}}})
            yield from open_box()
            event('RIGHTMOUSE')
            yield
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            choices = popup(anchor, ['Wireframe', 'Solid'])
            count = len(observed)
            yield from click(midpoint(choices[1]))
            check(len(observed) == count+1 and observed[-1] == ('view.shaded', {'FINISHED'}),
                  'stationary mapped-menu release at the corner reclassified the rebuilt ring')
            yield from close_box()
            print('PASS stationary corner menu entry latches, next fresh leaf click executes', flush=True)
            print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
            return
        yield from open_box()
        event('RIGHTMOUSE')
        yield
        positions = popup(anchor, labels)
        yield from move(midpoint(positions[5]))
        screenshot('menus-corner-visible-top.png')
        count = len(observed)
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count+1 and observed[-1] == ('view.top', {'FINISHED'}),
              'visible corner Top button dispatched its displaced origin sector instead of Top')
        yield from close_box()
        print('PASS inward-clamped visible Top button dispatches Top', flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE'):
        original_snapshot = hotbox_runtime.snapshot
        def navigation_snapshot(context):
            value = json.loads(original_snapshot(context))
            value['settings']['center_buttons']['RIGHTMOUSE'] = 'common.select'
            if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') == 'title':
                value['settings']['center_buttons']['RIGHTMOUSE'] = 'center.controls'
            if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') == 'gap':
                value['settings']['style'] = 'center'
            value['menus'][0]['children'][3]['children'] = [
                dict(id=f'nav.{i}', kind='command', label=f'Entry {i:02}',
                     command='view.top' if i == 17 else 'view.front', enabled=True,
                     reason='', children=[]) for i in range(18)]
            return json.dumps(value)
        hotbox_runtime.snapshot = navigation_snapshot
        anchor = (cx-(label_width('AxisMeld')+40)*scale/2, cy-19*scale,
                  (label_width('AxisMeld')+40)*scale, 38*scale)
        labels = [f'Entry {i:02}' for i in range(18)]
        yield from open_box()
        event('RIGHTMOUSE')
        yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') == 'title':
            controls = popup(anchor, ['Menu Rows', 'Hotbox Style', 'Transparency',
                                       'Center Mouse Buttons'])
            yield from click(midpoint(controls[1]))
            choices = popup(controls[1], ['Zones and Menu Rows', 'Zones Only', 'Center Zone Only'])
            yield from click(midpoint(choices[2]))
            check(hotbox_runtime.current_settings()['style'] == 'center',
                  'latched child-directory click bounced immediately through its new Back control')
            yield from close_box()
            print('PASS latched child directory click enters and its setting leaf executes', flush=True)
            print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
            return
        current = page(anchor, labels)
        if os.environ.get('AXISMELD_TEST_NAVIGATION_PROBE') == 'gap':
            gap_point = (cx, cy+25*scale)
            count = len(observed)
            yield from move(gap_point)
            event('LEFTMOUSE')
            yield
            yield from move((gap_point[0]+350*scale, gap_point[1]))
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count, 'active ellipse gap incorrectly restarted center marking')
            yield from close_box()
            print('PASS active-ring gap cannot restart center-only marking', flush=True)
            print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
            return
        while current['first'] + current['capacity'] < 18:
            yield from click(midpoint(current['next']))
            current = page(anchor, labels, current['first']+1)
        screenshot('menus-next-terminal-page.png')
        count = len(observed)
        yield from click(midpoint(current['items'][17]))
        check(len(observed) == count+1 and observed[-1] == ('view.top', {'FINISHED'}),
              'Next becoming disabled on press discarded the menu before its final leaf')
        yield from close_box()
        print('PASS terminal Next press/release retains the final page and dispatches its leaf', flush=True)
        print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)
        return
    pane_labels = ['View', 'Shading', 'Lighting', 'Show', 'Renderer', 'Panels']
    shading = row_title(pane_labels, 1, 48)
    shading_items = popup(shading, ['Wireframe', 'Solid'])
    review_failures = []
    # Releasing anywhere except a title/parent must discard the old executable popup.
    common_labels = ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
    with bpy.context.temp_override(window=win, area=area, region=region):
        common = json.loads(hotbox_runtime.snapshot(bpy.context))['menus'][0]['children']
    check([node['label'] for node in common] == common_labels and
          common[0]['id'] == 'common.file' and not common[0]['enabled'],
          'disabled cancellation fixture must address the actual seven-item public File row')
    for target, point in (('blank', (cx-300*scale, cy-180*scale)),
                          ('disabled', midpoint(row_title(common_labels, 0, 96)))):
        yield from open_box()
        yield from move(midpoint(shading))
        event('LEFTMOUSE')
        yield
        yield from move(point)
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        screenshot(f'menus-cancel-{target}.png')
        count = len(observed)
        yield from click(midpoint(shading_items[0]))
        if len(observed) != count:
            review_failures.append(f'ordinary dropdown {target} release left an executable child')
        yield from close_box()
    yield from open_box()
    count = len(observed)
    yield from click(midpoint(shading))
    yield from move(midpoint(shading_items[0]))
    check(len(observed) == count, 'title release or leaf hover executed without fresh press')
    screenshot('menus-click-shading.png')
    yield from click(midpoint(shading_items[0]))
    check(len(observed) == count+1 and observed[-1][0] == 'view.wireframe' and
          area.spaces.active.shading.type == 'WIREFRAME', 'click browse wireframe failed')
    yield from close_box()
    yield from open_box()
    yield from move(midpoint(shading))
    event('LEFTMOUSE')
    yield
    yield from move(midpoint(shading_items[1]))
    count = len(observed)
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    check(len(observed) == count+1 and observed[-1][0] == 'view.shaded' and
          area.spaces.active.shading.type == 'SOLID', 'held drag did not dispatch Solid exactly once')
    yield from close_box()
    print('PASS B4 click browse and held drag dispatch actual shading commands', flush=True)

    # A disabled File title must neither dispatch nor turn the gesture into a tap.
    yield from open_box()
    count = len(observed)
    yield from click(midpoint(row_title(common_labels, 0, 96)))
    screenshot('menus-disabled-file-reason.png')
    yield from close_box()
    check(len(observed) == count and len([r for r in area.regions if r.type == 'WINDOW']) == 1,
          'disabled title executed or became tap')

    # Close-before mode command: no stale draw pointer and no residual Space playback.
    select = row_title(common_labels, 3, 96)
    select_items = popup(select, ['Object / Component', '', 'Vertex', 'Edge', 'Face'])
    yield from open_box()
    yield from move(midpoint(select))
    event('LEFTMOUSE')
    yield
    yield from move(midpoint(select_items[0]))
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    check(bpy.context.object.mode == 'EDIT', 'mode command did not run before Space release')
    screenshot('menus-mode-change-closed.png')
    yield from close_box()
    check(not win.screen.is_animation_playing, 'residual Space played animation after mode change')
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    yield from settle()

    panels = row_title(pane_labels, 5, 48)
    panel_items = popup(panels, ['Views', '', 'Single / Quad View'])
    yield from open_box()
    yield from click(midpoint(panels))
    count = len(observed)
    yield from click(midpoint(panel_items[2]))
    region = next(r for r in area.regions if r.type == 'WINDOW')
    check(len([r for r in area.regions if r.type == 'WINDOW']) == 4 and
          len(observed) == count+1 and observed[-1][0] == 'view.toggle_quad',
          'actual Panels leaf failed to close before destroying its source region')
    yield from close_box()
    check(not win.screen.is_animation_playing, 'quad handoff leaked captured Space')
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
    yield from settle()
    region = next(r for r in area.regions if r.type == 'WINDOW')

    # Map center to an ordinary menu and to the root center; null cancels a tap only.
    def settings(mapping):
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': 1, 'settings': {'center_buttons': {'RIGHTMOUSE': mapping}}})
    center = (cx-(label_width('AxisMeld')+40)*scale/2, cy-19*scale,
              (label_width('AxisMeld')+40)*scale, 38*scale)
    settings('pane.shading')
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    mapped_items = popup(center, ['Wireframe', 'Solid'])
    yield from move(midpoint(mapped_items[0]))
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    check(area.spaces.active.shading.type == 'WIREFRAME', 'center ordinary mapping became marking')
    yield from close_box()
    settings('center')
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    root_items = popup(center, ['Recent Commands', 'AxisMeld', 'Hotbox Controls'])
    yield from click(midpoint(root_items[1]))
    yield from settle()
    screenshot('menus-center-root-duplicate-views.png')
    view_items = popup(root_items[1], ['Perspective View', 'Right View', 'Bottom View', 'Front View',
                                     'Back View', 'Top View', 'Left View', '', 'Hotbox Style'])
    yield from click(midpoint(view_items[5]))
    check(observed[-1][0] == 'view.top' and current_pose()[1] == 'ORTHO',
          'root-center duplicate views node did not open its own deeper popup')
    yield from close_box()
    settings(None)
    yield from open_box()
    count = len(observed)
    event('RIGHTMOUSE')
    yield
    event('MOUSEMOVE', 'NOTHING', cx+90, cy)
    yield
    event('RIGHTMOUSE', 'RELEASE')
    yield from close_box()
    check(len(observed) == count, 'null center mapping executed or became short tap')
    reset_hotbox_settings()

    # Center-only applies to blank WINDOW content, retaining actual mouse-press origin.
    # B is far from Space's A origin and all visible center/popup rectangles.
    blank = (cx-230*scale, cy-130*scale)
    hotbox_runtime.reload_settings(bpy.context, session={
        'schema_version': 1, 'settings': {'style': 'center'}})
    for dx, dy, command, rotation in directions:
        yield from open_box()
        yield from move(blank)
        event('RIGHTMOUSE')
        yield
        yield from move((blank[0]+dx*scale, blank[1]+dy*scale))
        count = len(observed)
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count+1 and observed[-1] == (command, {'FINISHED'}),
              f'center blank RMB {command} must use actual press origin and execute exactly once')
        q, projection = current_pose()
        check(projection == ('PERSP' if rotation is None else 'ORTHO'), 'blank ' + command)
        if rotation:
            check(abs(abs(sum(a*b for a,b in zip(q, rotation))) - 1) < 1e-5,
                  'blank ' + command + ' orientation')
        yield from close_box()
        check(len(observed) == count+1, 'center blank release became tap')
    print('PASS center blank RMB seven views use actual press origin', flush=True)

    hotbox_runtime.reload_settings(bpy.context, session={
        'schema_version': 1, 'settings': {'style': 'center', 'center_buttons': {
            'LEFTMOUSE': 'views', 'MIDDLEMOUSE': 'pane.shading', 'RIGHTMOUSE': None}}})
    yield from open_box()
    yield from move(blank)
    count = len(observed)
    event('RIGHTMOUSE')
    yield
    yield from move((blank[0]+90*scale, blank[1]))
    event('RIGHTMOUSE', 'RELEASE')
    yield from close_box()
    check(len(observed) == count, 'center blank null mapping executed or became tap')
    yield from open_box()
    yield from move(blank)
    event('MIDDLEMOUSE')
    yield
    yield from move(midpoint(center))
    event('MIDDLEMOUSE', 'RELEASE')
    yield from settle()
    screenshot('menus-center-blank-mapped-shading.png')
    # Fresh LMB has views mapping, but an existing actual leaf must win over fallback.
    count = len(observed)
    yield from click(midpoint(mapped_items[1]))
    check(len(observed) == count+1 and observed[-1] == ('view.shaded', {'FINISHED'}) and
          area.spaces.active.shading.type == 'SOLID',
          'center blank ordinary mapping or existing leaf priority failed')
    yield from close_box()
    yield from open_box()
    yield from move(blank)
    count = len(observed)
    event('LEFTMOUSE')
    yield
    yield from move((blank[0], blank[1]-90*scale))
    event('LEFTMOUSE', 'RELEASE')
    yield from close_box()
    check(len(observed) == count+1 and observed[-1][0] == 'view.front',
          'center blank independent LMB views mapping failed')
    for style in ('rows', 'zones'):
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': 1, 'settings': {'style': style}})
        yield from open_box()
        yield from move(blank)
        count = len(observed)
        event('RIGHTMOUSE')
        yield
        yield from move((blank[0]+90*scale, blank[1]))
        event('RIGHTMOUSE', 'RELEASE')
        yield from close_box()
        check(len(observed) == count, style + ' blank unexpectedly became central mapping')
    print('PASS center blank independent views/menu/null mappings, leaf priority and rows/zones isolation',
          flush=True)
    reset_hotbox_settings()

    # Style is a tail of the held overlay. Do not release the owning RMB to enter it.
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    central_list = popup(center, ['Perspective View', 'Right View', 'Bottom View', 'Front View',
                                  'Back View', 'Top View', 'Left View', '', 'Hotbox Style'])
    yield from move(midpoint(central_list[8]))
    central_styles = style_list(central_list[8], label_width,
                               (region.x, region.y, region.width, region.height), scale)
    if native_style_probe:
        path = screenshot('menus-native-style-background.png')
        image = bpy.data.images.load(str(path), check_existing=False)
        pixels, image_width = list(image.pixels), image.size[0]
        x, y, w, h = central_styles[0]
        # Ordinary menus have one uninterrupted background between rows, including
        # outside the text. Old floating cards expose the viewport in this strip.
        samples = [pixels[(yy*image_width+xx)*4:(yy*image_width+xx)*4+3]
                   for yy in range(int(y-3*scale), int(y-scale))
                   for xx in range(int(x+6*scale), int(x+12*scale))]
        check(samples and all(r > .7 and g < .2 and b < .1 for r, g, b in samples),
              'Style must render a continuous opaque native menu background between rows')
        bpy.data.images.remove(image)
    yield from move(midpoint(central_styles[1]))
    screenshot('menus-fresh-style-drag-candidate.png')
    count = len(observed)
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['style'] == 'zones' and
              len(observed) == count, 'held Style tail/list must select its setting')
    yield from close_box()
    reset_hotbox_settings()

    yield from open_box()
    event('RIGHTMOUSE')
    yield
    count = len(observed)
    yield from move(midpoint(central_list[8]))
    yield from move(midpoint(central_styles[1]))
    yield from move((cx, cy))
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['style'] == 'rows' and
              len(observed) == count, 'return from Style to neutral center must cancel without latching')
    yield from close_box()
    reset_hotbox_settings()

    # Backtracking must restore view sectors without needing a fresh mouse press.
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    count = len(observed)
    yield from move(midpoint(central_list[8]))
    yield from move((cx, cy))
    yield from move((cx+15*scale, cy))
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    check(len(observed) == count+1 and observed[-1] == ('view.side', {'FINISHED'}),
          'Style -> center -> short Right gesture did not restore view sectors')
    yield from close_box()

    yield from open_box()
    event('RIGHTMOUSE')
    yield
    count, settings_count = len(observed), len(settings_observed)
    yield from move(midpoint(central_list[9]))
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    check(len(observed) == count and len(settings_observed) == settings_count,
          'disabled New Camera must neither dispatch nor fall back to a direction')
    yield from close_box()

    yield from open_box()
    event('RIGHTMOUSE')
    yield
    yield from move(midpoint(central_list[8]))
    yield from move(midpoint(central_styles[1]))
    event('SPACE', 'RELEASE')
    yield from settle()
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    check(len(observed) == count and len(settings_observed) == settings_count and
          not win.screen.is_animation_playing,
          'Space release in Style must cancel without applying a setting or leaking playback')
    print('PASS held Style selection, center backtracking, disabled New Camera and Space cleanup', flush=True)

    # Ordinary Controls settings still rebuild the same live hotbox through the native bridge.
    control_width = (label_width('Hotbox Controls') + 40)*scale
    controls = (center[0]+center[2]+83.6*scale, cy-19*scale, control_width, 38*scale)
    control_items = popup(controls, ['Menu Rows', 'Hotbox Style', 'Transparency',
                                     'Center Mouse Buttons'])
    yield from open_box()
    yield from click(midpoint(controls))
    yield from click(midpoint(control_items[1]))
    style_items = popup(control_items[1], ['Zones and Menu Rows', 'Zones Only', 'Center Zone Only'])
    yield from click(midpoint(style_items[2]))
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['style'] == 'center',
              'actual style leaf did not update settings')
    screenshot('menus-style-center-live.png')
    count = len(observed)
    yield from click(midpoint(shading))
    yield from click(midpoint(shading_items[0]))
    check(len(observed) == count, 'hidden row still dispatched after immediate style rebuild')
    yield from close_box()
    reset_hotbox_settings()
    # The two other short settings lists use their actual Controls parents and setting leaves.
    yield from open_box()
    yield from click(midpoint(controls))
    yield from click(midpoint(control_items[0]))
    row_items = popup(control_items[0],
                      ['Show Common Menus', 'Show Pane Specific Menus', 'Show Modeling'])
    screenshot('menus-rows-open.png')
    yield from click(midpoint(row_items[2]))
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['rows'] ==
              ['common', 'pane'], 'actual Menu Rows leaf did not update settings')
    check(settings_observed[-1][:2] == ('row.modeling', 'toggle'),
          'actual Menu Rows leaf bypassed shared settings dispatch')
    yield from close_box()
    reset_hotbox_settings()

    yield from open_box()
    yield from click(midpoint(controls))
    yield from click(midpoint(control_items[2]))
    transparency_items = popup(control_items[2], ['0%', '25%', '50%', '75%', '100%'])
    screenshot('menus-transparency-open.png')
    yield from click(midpoint(transparency_items[3]))
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['transparency'] == 75,
              'actual Transparency leaf did not update settings')
    check(settings_observed[-1][:2] == ('transparency', '75'),
          'actual Transparency leaf bypassed shared settings dispatch')
    yield from close_box()
    reset_hotbox_settings()
    print('PASS visible Menu Rows and Transparency lists changed shared runtime settings', flush=True)

    # Configure the same center-button model through the visible Controls tree.
    yield from open_box()
    yield from click(midpoint(controls))
    yield from click(midpoint(control_items[3]))
    button_items = popup(control_items[3], ['Left Mouse Button', 'Middle Mouse Button',
                                            'Right Mouse Button'])
    yield from click(midpoint(button_items[2]))
    mapping_labels = ['Disabled', 'AxisMeld Views', 'Recent Commands', 'Hotbox Controls',
                      'Common', 'Select', 'Modify', 'Current Pane', 'Pane View',
                      'Pane Shading', 'Panels', 'Panel Views', 'Modeling']
    mapping_page = page(button_items[2], mapping_labels)
    while mapping_page['items'][9] is None:
        yield from click(midpoint(mapping_page['next']))
        mapping_page = page(button_items[2], mapping_labels, mapping_page['first'] + 1)
    mapping_items = mapping_page['items']
    screenshot('menus-controls-center-button-open.png')
    yield from click(midpoint(mapping_items[9]))
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['center_buttons']
              ['RIGHTMOUSE'] == 'pane.shading',
              'visible center-button Controls did not persist another registered menu')
    check(json.loads(hotbox_user.read_text(encoding='utf-8')) == {
        'schema_version': 1,
        'settings': {'center_buttons': {'RIGHTMOUSE': 'pane.shading'}},
    }, 'visible center-button Controls did not write a delta-only user layer')
    yield from close_box()
    print('PASS visible Controls center-button click persisted one delta setting', flush=True)

    # A successful leaf is visible and replayable through the session-only Recent menu.
    recent_command = hotbox_runtime.recent.items()[0]
    recent_width = (label_width('Recent Commands') + 40)*scale
    recent_rect = (center[0]-83.6*scale-recent_width, cy-19*scale, recent_width, 38*scale)
    yield from open_box()
    yield from click(midpoint(recent_rect))
    recent_labels = [COMMANDS[command].label for command in hotbox_runtime.recent.items()]
    recent_items = popup(recent_rect, recent_labels)
    screenshot('menus-recent-open.png')
    count = len(observed)
    yield from click(midpoint(recent_items[0]))
    check(len(observed) == count+1 and observed[-1] == (recent_command, {'FINISHED'}),
          'visible Recent did not replay the newest available command')
    yield from close_box()
    print('PASS visible Recent opened and replayed newest currently available command', flush=True)
    reset_hotbox_settings()

    # Changing the live viewport geometry/scale invalidates the captured drawing context.
    preferences = bpy.context.window_manager.keyconfigs.active.preferences
    preferences.hotbox_tap_seconds = 1.0
    yield from open_box()
    count = len(observed)
    bpy.context.preferences.view.ui_scale = 1.25
    yield from settle(8)
    yield from close_box()
    check(len(observed) == count, 'live viewport scale change kept stale drawing/tap context')
    preferences.hotbox_tap_seconds = .4
    bpy.context.preferences.view.ui_scale = 1.0
    yield from settle(8)

    for requested_scale in (1.0, 1.25, 1.5, 2.0):
        content_corners = {}
        bpy.context.preferences.view.ui_scale = requested_scale
        yield from settle(8)
        scale = bpy.context.preferences.system.ui_scale
        check(abs(scale-requested_scale) < .05, 'UI scaling fixture did not apply')
        print('SCALE_RECT', requested_scale, 'area', area.x, area.y, area.width, area.height,
              'region', region.x, region.y, region.width, region.height, flush=True)
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        yield from open_box()
        yield from settle(20)
        screenshot(f'menus-scale-{requested_scale}-center-main.png')
        yield from close_box()
        if requested_scale == 2.0:
            # A receipt-only F14 diagnostic identifies the native visual region. Product
            # acceptance below still uses untouched actual Space preset bindings.
            bpy.utils.register_class(AXISMELD_OT_menu_region_probe)
            km = bpy.context.window_manager.keyconfigs.active.keymaps['3D View Generic']
            probe = km.keymap_items.new('axismeld.menu_region_probe', 'F14', 'PRESS')
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', region.x, region.y)
            yield from settle()
            event('F14')
            yield
            event('F14', 'RELEASE')
            yield from settle()
            print('OVERLAP_RECEIPT', region_receipts, flush=True)
            check(region_receipts and region_receipts[-1][1] == 'TOOLS',
                  '2x corner diagnostic expected actual overlapping toolbar receipt')
            count = len(observed)
            event('SPACE')
            yield
            event('SPACE', 'RELEASE')
            yield from settle()
            check(len(observed) == count, 'Space hotbox must not expand into TOOLS')
            if win.screen.is_animation_playing:
                with bpy.context.temp_override(window=win):
                    bpy.ops.screen.animation_cancel(restore_frame=False)
            area.spaces.active.show_region_toolbar = False
            area.spaces.active.show_region_ui = False
            area.spaces.active.show_region_header = False
            area.spaces.active.show_region_tool_header = False
            yield from settle(8)
            for corner, x, y, sx, sy in (
                    ('sw', region.x, region.y, 1, 1),
                    ('se', region.x+region.width-1, region.y, -1, 1),
                    ('nw', region.x, region.y+region.height-1, 1, -1),
                    ('ne', region.x+region.width-1, region.y+region.height-1, -1, -1)):
                for ax, ay in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    px, py = x+ax*sx, y+ay*sy
                    event('MOUSEMOVE', 'NOTHING', px, py)
                    yield from settle()
                    received = len(region_receipts)
                    event('F14')
                    yield
                    event('F14', 'RELEASE')
                    yield from settle()
                    receipt = region_receipts[-1] if len(region_receipts) > received else None
                    print('CONTENT_BOUNDARY_RECEIPT', corner, px, py, receipt, flush=True)
                    if receipt and receipt[1] == 'WINDOW':
                        content_corners[corner] = (px, py)
                        break
                check(corner in content_corners, 'No WINDOW content within adjacent native boundary pixel')
            km.keymap_items.remove(probe)
            bpy.utils.unregister_class(AXISMELD_OT_menu_region_probe)
            print('2x GUI matrix uses measured first WINDOW content pixels; pure layout retains literal0/0', flush=True)
        # Use actual viewport boundary coordinates, never a safe inset center substitute.
        for corner, x, y, dx, dy, command in (
                ('sw', region.x, region.y, 90, 0, 'view.side'),
                ('se', region.x+region.width-1, region.y, -90, 0, 'view.top'),
                ('nw', region.x, region.y+region.height-1, 90, -90, 'view.bottom'),
                ('ne', region.x+region.width-1, region.y+region.height-1, -90, -90, 'view.back')):
            x, y = content_corners.get(corner, (x, y))
            event('MOUSEMOVE', 'NOTHING', x, y)
            yield from settle()
            print('GUI_CORNER', corner, x, y, flush=True)
            event('SPACE')
            yield from settle()
            check(not win.screen.is_animation_playing, 'actual WINDOW content Space started playback')
            if corner == 'sw':
                screenshot(f'menus-scale-{requested_scale}-corner-main.png')
            event('RIGHTMOUSE')
            yield
            event('MOUSEMOVE', 'NOTHING', x+dx*scale, y+dy*scale)
            yield
            if corner == 'sw':
                yield from settle()
                screenshot(f'menus-scale-{requested_scale}-corner-marking.png')
            count = len(observed)
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count+1 and observed[-1][0] == command,
                  f'scale={scale} true {corner} corner changed captured gesture origin')
            yield from close_box()
            check(not win.screen.is_animation_playing, 'actual content gesture leaked Space playback')
    bpy.context.preferences.view.ui_scale = 1.0
    yield from settle(8)
    scale = bpy.context.preferences.system.ui_scale
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    print('PASS B9 all four corners: scales1/1.25/1.5 literal; scale2 measured content boundary', flush=True)

    # Native malformed snapshot must cancel without leaving a handler that steals the next Space.
    real_snapshot = hotbox_runtime.snapshot
    hotbox_runtime.snapshot = lambda _context: '{'
    yield from open_box()
    yield from close_box()
    hotbox_runtime.snapshot = real_snapshot
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    event('MOUSEMOVE', 'NOTHING', cx-90, cy+90)
    yield
    count = len(observed)
    event('RIGHTMOUSE', 'RELEASE')
    yield from close_box()
    check(len(observed) == count+1 and observed[-1][0] == 'view.left',
          'malformed invoke leaked a modal handler')

    # Split only this disposable window to exercise an actual small viewport and row overflow.
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.screen.area_split(direction='VERTICAL', factor=.34)
    yield from settle(8)
    area = min((a for a in win.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.screen.area_split(direction='HORIZONTAL', factor=.42)
    yield from settle(8)
    area = min((a for a in win.screen.areas if a.type == 'VIEW_3D' and a.width < 600),
               key=lambda a: a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    cx, cy = region.x+region.width//2, region.y+region.height//2
    check(480 <= region.width/scale < 600 and 320 <= region.height/scale < 420,
          f'small viewport fixture not within supported bounds: {region.width}x{region.height}')
    print('SMALL_VIEWPORT', region.x, region.y, region.width, region.height, flush=True)
    area.spaces.active.show_region_toolbar = False
    yield from open_box()
    screenshot('menus-small-row-first.png')
    # First Modeling page is hand calculated from measured public labels, with two 38px controls.
    modeling_labels = ['Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display', 'Curves', 'Surfaces',
                       'Deform', 'UV', 'Generate']
    room = region.width/scale - 24 - 96
    used = 0
    for label in modeling_labels:
        width = label_width(label)+40
        if used+width > room:
            break
        used += width+10
    total = used-10+96
    next_point = (cx+(total/2-19)*scale, cy-48*scale)
    count = len(observed)
    yield from click(next_point)
    screenshot('menus-small-row-scrolled.png')
    check(len(observed) == count, 'layout-only row scroll control reached command dispatcher')
    yield from close_box()

    # A bounded native-parser fixture provides real overflow at two independent popup owners.
    # No replacement key binding: actual Space still invokes the installed adapter and parser.
    real_snapshot = hotbox_runtime.snapshot
    def long_snapshot(context):
        value = json.loads(real_snapshot(context))
        value['settings']['center_buttons']['RIGHTMOUSE'] = 'common.select'
        parent = value['menus'][0]['children'][3]
        def leaf(identifier, label, command):
            return dict(id=identifier, kind='command', label=label, command=command,
                        enabled=True, reason='', children=[])
        child = dict(id='fixture.child', kind='menu', label='Nested Entries', command='',
                     enabled=True, reason='', children=[
                         leaf(f'fixture.child.{i}', f'Child {i:02}', 'view.top' if i == 17 else 'view.front')
                         for i in range(18)])
        parent['children'] = [child] + [leaf(f'fixture.parent.{i}', f'Parent {i:02}', 'view.side')
                                            for i in range(17)]
        return json.dumps(value)
    hotbox_runtime.snapshot = long_snapshot
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    center = (cx-(label_width('AxisMeld')+40)*scale/2, cy-19*scale,
              (label_width('AxisMeld')+40)*scale, 38*scale)
    parent_labels = ['Nested Entries']+[f'Parent {i:02}' for i in range(17)]
    parent_page = page(center, parent_labels)
    child_anchor = parent_page['items'][0]
    yield from click(midpoint(child_anchor))
    child_labels = [f'Child {i:02}' for i in range(18)]
    child_page = page(child_anchor, child_labels)
    screenshot('menus-small-parent-child-first.png')
    while child_page['first'] + child_page['capacity'] < 18:
        yield from click(midpoint(child_page['next']))
        child_page = page(child_anchor, child_labels, child_page['first']+1)
    screenshot('menus-small-child-scrolled.png')
    count = len(observed)
    yield from click(midpoint(child_page['back']))
    check(len(observed) == count, 'Back release dispatched a newly exposed parent leaf')
    screenshot('menus-small-return-parent.png')
    yield from click(midpoint(parent_page['next']))
    parent_page = page(center, parent_labels, 1)
    screenshot('menus-small-ancestor-scrolled.png')
    yield from click(midpoint(parent_page['items'][1]))
    check(len(observed) == count+1 and observed[-1] == ('view.side', {'FINISHED'}),
          'parent page did not own its real leaf after returning from nested ellipse')
    yield from click((cx, cy), 'RIGHTMOUSE')
    yield from click(midpoint(parent_page['previous']))
    parent_page = page(center, parent_labels)
    child_anchor = parent_page['items'][0]
    yield from click(midpoint(child_anchor))
    count = len(observed)
    yield from click(midpoint(child_page['items'][17]))
    check(len(observed) == count+1 and observed[-1] == ('view.top', {'FINISHED'}),
          'independent child page did not survive parent back/forward navigation')
    yield from close_box()
    hotbox_runtime.snapshot = real_snapshot
    print('PASS B9 actual small viewport, row controls and nested per-owner scrolling', flush=True)
    # Unsupported menu dimensions still own the trigger lifecycle; no menu layout is permitted.
    for dimension in ('width', 'height'):
        if dimension == 'height':
            area = max((a for a in win.screen.areas if a.type == 'VIEW_3D'),
                       key=lambda a: a.width*a.height)
            region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.screen.area_split(direction='VERTICAL' if dimension == 'width' else 'HORIZONTAL',
                                      factor=.5 if dimension == 'width' else .18)
        yield from settle(8)
        candidates = [a for a in win.screen.areas if a.type == 'VIEW_3D']
        area = min(candidates, key=lambda a: a.width if dimension == 'width' else a.height)
        region = next(r for r in area.regions if r.type == 'WINDOW')
        check((region.width/scale < 340 and region.height/scale >= 200) if dimension == 'width'
              else (region.height/scale < 200 and region.width/scale >= 340),
              f'unsupported {dimension} fixture must isolate one limit: {region.width}x{region.height}')
        print('UNSUPPORTED_VIEWPORT', dimension, region.x, region.y, region.width, region.height, flush=True)
        cx, cy = region.x+region.width//2, region.y+region.height//2
        count = len(observed)
        yield from open_box()
        yield from close_box()
        if (len(observed) != count+1 or observed[-1] != ('view.toggle_quad', {'FINISHED'})
                or not area.spaces.active.region_quadviews):
            review_failures.append(f'unsupported {dimension} short tap did not toggle quad')
        if area.spaces.active.region_quadviews:
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                real_dispatch(bpy.context, 'view.toggle_quad')
            yield from settle(8)
        region = next(r for r in area.regions if r.type == 'WINDOW')
        cx, cy = region.x+region.width//2, region.y+region.height//2
        count = len(observed)
        yield from open_box()
        yield from settle(20)
        screenshot(f'menus-unsupported-{dimension}-hold.png')
        yield from close_box()
        check(len(observed) == count and not area.spaces.active.region_quadviews,
              f'unsupported {dimension} hold toggled layout')
        yield from open_box()
        event('RIGHTMOUSE')
        yield
        event('SPACE', 'RELEASE')
        yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count, f'unsupported {dimension} mouse gesture became tap')
        check(not win.screen.is_animation_playing, f'unsupported {dimension} leaked Space playback')
    check(not review_failures, '\n'.join(review_failures))
    print('PASS review regression: ordinary cancellation and unsupported width/height tap/hold', flush=True)
    hotbox_runtime.dispatch = real_dispatch
    hotbox_runtime.apply_setting = real_apply_setting
    print('PASS B2/B3/B4/B8 cancel, two buttons, disabled, mode cleanup, center remaps', flush=True)
    print('AXISMELD_HOTBOX_MENU_EVENTS_PASS', flush=True)


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

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Native Style menu rendering and dispatch through both hotbox entries at 1x/2x."""
import json
import os
from pathlib import Path
import sys
import traceback

import blf
import bpy

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(root):
    raise RuntimeError('Only the isolated GUI runner may run this test')
sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_geometry_fixture import ellipse_page, native_list
from axismeld import hotbox_runtime

bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
STYLE_LABELS = ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only')
ROW_LABELS = ('Show Common Menus', 'Show Pane Specific Menus', 'Show Modeling')
TRANSPARENCY_LABELS = ('0%', '25%', '50%', '75%', '100%')


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=4):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    position = [0, 0]

    def event(kind, value='PRESS', point=None):
        if point is not None:
            position[:] = [int(v) for v in point]
        win.event_simulate(type=kind, value=value, x=position[0], y=position[1])

    def move(rect):
        event('MOUSEMOVE', 'NOTHING', (rect[0]+rect[2]/2, rect[1]+rect[3]/2))
        yield from settle()

    def click(rect):
        yield from move(rect)
        event('LEFTMOUSE')
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()

    def screenshot(name):
        path = artifacts / name
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        return path

    theme = bpy.context.preferences.themes[0].user_interface
    normal_background = tuple(theme.wcol_menu_back.inner)
    # Native hover derives from inner/text, not the pressed-selection color used
    # by the old custom hotbox entry. Make the latter unmistakably different.
    theme.wcol_menu_item.inner_sel = (1, 0, 1, 1)
    layout_probe = os.environ.get('AXISMELD_TEST_NATIVE_LIST_LAYOUT')
    if layout_probe:
        if layout_probe == 'narrow':
            bpy.context.preferences.view.ui_scale = 1.0
            yield from settle(8)
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.screen.area_split(direction='VERTICAL', factor=.25)
            yield from settle(8)
            area = min((a for a in win.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width)
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.screen.area_split(direction='HORIZONTAL', factor=.42)
            yield from settle(8)
            area = min((a for a in win.screen.areas if a.type == 'VIEW_3D' and a.width < 500),
                       key=lambda a: a.height)
            region = next(r for r in area.regions if r.type == 'WINDOW')
        elif layout_probe == 'quad':
            bpy.context.preferences.view.ui_scale = 2.0
            yield from settle(8)
            area.spaces.active.show_region_toolbar = False
            area.spaces.active.show_region_ui = False
            area.spaces.active.show_region_header = False
            area.spaces.active.show_region_tool_header = False
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
            yield from settle(8)
            region = min((r for r in area.regions if r.type == 'WINDOW'), key=lambda r: (r.y, r.x))
        else:
            raise AssertionError(f'Unknown native list layout probe {layout_probe!r}')

        scale = bpy.context.preferences.system.ui_scale
        logical_width, logical_height = region.width/scale, region.height/scale
        if layout_probe == 'narrow':
            check(360 <= logical_width < 430 and 320 <= logical_height < 420,
                  f'narrow probe outside bounded dimensions: {logical_width}x{logical_height}')
        else:
            check(360 <= logical_width < 430 and 200 <= logical_height < 260,
                  f'2x quad probe outside bounded dimensions: {logical_width}x{logical_height}')
        print('NATIVE_LIST_LAYOUT', layout_probe, 'scale', scale, 'logical', logical_width,
              logical_height, 'physical', region.width, region.height, 'origin', region.x, region.y,
              flush=True)
        print('NATIVE_LIST_INPUT', layout_probe,
              'SPACE press -> center RIGHTMOUSE center.controls -> LEFTMOUSE parent/leaf',
              flush=True)
        cx, cy = region.x+region.width/2, region.y+region.height/2
        bounds = (region.x, region.y, region.width, region.height)
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        def measure(label):
            return blf.dimensions(0, label)[0] / scale
        center_width = (measure('AxisMeld') + 60)*scale
        center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)
        control_labels = ['Menu Rows', 'Hotbox Style', 'Transparency', 'Center Mouse Buttons']

        def open_list(index, labels):
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('SPACE')
            yield from settle(8)
            event('RIGHTMOUSE')
            yield from settle()
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            controls = ellipse_page(center, control_labels, measure, bounds, scale)['items']
            yield from click(controls[index])
            return controls[index], native_list(controls[index], labels, measure, bounds, scale)

        cases = (
            ('rows', 0, ROW_LABELS,
             (('common', ['pane', 'modeling']),
              ('pane', ['common', 'modeling']),
              ('modeling', ['common', 'pane']))),
            ('transparency', 2, TRANSPARENCY_LABELS,
             ((0, 0), (25, 25), (50, 50), (75, 75), (100, 100))),
        )
        for name, controls_index, labels, options in cases:
            for selected_index, (selected, expected) in enumerate(options):
                initial_transparency = 50 if name == 'transparency' and selected == 25 else 25
                hotbox_runtime.reload_settings(bpy.context, session={
                    'schema_version': 1, 'settings': {
                        'style': 'rows', 'transparency': initial_transparency,
                        'rows': ['common', 'pane', 'modeling'],
                        'center_buttons': {'RIGHTMOUSE': 'center.controls'},
                    }})
                with bpy.context.temp_override(window=win, area=area, region=region):
                    before = json.loads(hotbox_runtime.snapshot(bpy.context))['settings']
                check(before['center_buttons']['RIGHTMOUSE'] == 'center.controls',
                      f'{layout_probe} {name} input mapping was not applied')
                owner, choices = yield from open_list(controls_index, labels)
                check(len(choices) == len(labels) and all(
                    x >= region.x and y >= region.y and x+w <= region.x+region.width and
                    y+h <= region.y+region.height for x, y, w, h in choices),
                    f'{layout_probe} {name} did not expose every list row inside the real pane')
                ox, oy, ow, oh = owner
                list_left = min(r[0] for r in choices)
                list_right = max(r[0]+r[2] for r in choices)
                list_bottom = min(r[1] for r in choices)
                list_top = max(r[1]+r[3] for r in choices)
                check(list_left >= ox+ow+9.99*scale or ox >= list_right+9.99*scale or
                      list_bottom >= oy+oh+9.99*scale or oy >= list_top+9.99*scale,
                      f'{layout_probe} {name} owner/list separation is below 10 logical pixels')
                open_path = screenshot(
                    f'native-list-{layout_probe}-{name}-{selected_index}-open.png')
                image = bpy.data.images.load(str(open_path), check_existing=False)
                pixels, width = list(image.pixels), image.size[0]
                for label, (x, y, w, h) in zip(labels, choices):
                    ink = sum(min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]) > .55
                              for yy in range(int(y+3*scale), int(y+h-3*scale))
                              for xx in range(int(x+3*scale), int(x+w-3*scale)))
                    check(ink > 2*scale*scale,
                          f'{layout_probe} {name} missing readable label {label!r}')
                bpy.data.images.remove(image)
                yield from move(choices[selected_index])
                screenshot(f'native-list-{layout_probe}-{name}-{selected_index}-hover.png')
                event('LEFTMOUSE')
                event('LEFTMOUSE', 'RELEASE')
                yield from settle()
                with bpy.context.temp_override(window=win, area=area, region=region):
                    after = json.loads(hotbox_runtime.snapshot(bpy.context))['settings']
                if name == 'rows':
                    check(after['rows'] == expected,
                          f'{layout_probe} Rows choice {selected!r} was not reachable')
                else:
                    check(after['transparency'] == expected,
                          f'{layout_probe} Transparency choice {selected!r} was not reachable')
                event('SPACE', 'RELEASE')
                yield from settle()
                check(not win.screen.is_animation_playing,
                      f'{layout_probe} {name} leaked Space release')
                print('NATIVE_LIST_SETTING', layout_probe, name, selected, 'expected', expected,
                      flush=True)
        print('AXISMELD_HOTBOX_NATIVE_LIST_LAYOUT_PASS', layout_probe, flush=True)
        print('AXISMELD_HOTBOX_NATIVE_STYLE_PASS', flush=True)
        return

    for requested_scale in (1.0, 2.0):
        bpy.context.preferences.view.ui_scale = requested_scale
        yield from settle(8)
        scale = bpy.context.preferences.system.ui_scale
        region = next(r for r in area.regions if r.type == 'WINDOW')
        cx, cy = region.x+region.width/2, region.y+region.height/2
        bounds = (region.x, region.y, region.width, region.height)
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        def measure(label):
            return blf.dimensions(0, label)[0] / scale
        center_width = (measure('AxisMeld') + 60)*scale
        center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)
        cases = (
            ('style-views', None, STYLE_LABELS, 1),
            ('style-controls', 1, STYLE_LABELS, 1),
            ('rows-controls', 0, ROW_LABELS, 2),
            ('transparency-controls', 2, TRANSPARENCY_LABELS, 3),
        )
        for entry, controls_index, labels, selected_index in cases:
            theme.wcol_menu_back.inner = normal_background
            hotbox_runtime.reload_settings(bpy.context, session={
                'schema_version': 1, 'settings': {
                    'style': 'rows', 'transparency': 25,
                    'rows': ['common', 'pane', 'modeling'],
                }})
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('SPACE')
            yield from settle(8)
            native_siblings = ()
            if controls_index is None:
                event('RIGHTMOUSE')
                yield from settle()
                ring = ellipse_page(center, [], measure, bounds, scale, views=True)
                list_anchor = ring['items'][8]
                yield from move(list_anchor)
            else:
                control_width = (measure('Hotbox Controls') + 60)*scale
                control = (center[0]+center[2]+83.6*scale, cy-19*scale,
                           control_width, 38*scale)
                yield from click(control)
                ring = ellipse_page(control, ['Menu Rows', 'Hotbox Style', 'Transparency',
                                               'Center Mouse Buttons'], measure, bounds, scale)
                native_siblings = tuple(ring['items'][:3])
                list_anchor = ring['items'][controls_index]
                yield from click(list_anchor)
            choices = native_list(list_anchor, labels, measure, bounds, scale,
                                  marking_origin=(cx, cy) if controls_index is None else None)
            screenshot(f'native-style-{entry}-{requested_scale}-normal.png')
            theme.wcol_menu_back.inner = (.8, .12, .04, 1)
            area.tag_redraw()
            yield from settle()
            path = screenshot(f'native-style-{entry}-{requested_scale}-theme.png')
            image = bpy.data.images.load(str(path), check_existing=False)
            pixels, width = list(image.pixels), image.size[0]
            x, y, w, h = choices[0]
            samples = [pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                       for yy in range(int(y-3*scale), int(y-scale))
                       for xx in range(int(x+6*scale), int(x+12*scale))]
            check(samples and all(r > .7 and g < .2 and b < .1 for r, g, b in samples),
                   f'{entry} {requested_scale}x native menu background missing or discontinuous')
            for label, (lx, ly, lw, lh) in zip(labels, choices):
                ink = sum(min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]) > .55
                          for yy in range(int(ly+3*scale), int(ly+lh-3*scale))
                          for xx in range(int(lx+3*scale), int(lx+lw-3*scale)))
                check(ink > 2*scale*scale,
                      f'{entry} {requested_scale}x missing readable label {label!r}')
            ex, ey, ew, eh = list_anchor
            entry_background = [pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                                for yy in range(int(ey+4*scale), int(ey+6*scale))
                                for xx in range(int(ex+5*scale), int(ex+8*scale))]
            check(entry_background and all(max(rgb)-min(rgb) < .08 and max(rgb) < .6
                                          for rgb in entry_background),
                  f'{entry} {requested_scale}x entry still uses a hotbox selection background')
            # In the menu-sized entry, the slot beyond the text contains a submenu arrow.
            arrow_ink = sum(min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]) > .65
                            for yy in range(int(ey+eh/2-5*scale), int(ey+eh/2+5*scale))
                            for xx in range(int(ex+ew-18*scale), int(ex+ew-4*scale)))
            check(arrow_ink > 3*scale*scale,
                  f'{entry} {requested_scale}x native submenu arrow missing')
            between_x = ex+ew+5*scale if choices[0][0] > ex else ex-5*scale
            between_y = ey+eh/2
            gap_rgb = pixels[(int(between_y)*width+int(between_x))*4:][:3]
            check(not (gap_rgb[0] > .7 and gap_rgb[1] < .2 and gap_rgb[2] < .1),
                  'entry and submenu incorrectly share a background spanning their gap')
            if native_siblings:
                left = int(min(r[0] for r in native_siblings))
                right = int(max(r[0]+r[2] for r in native_siblings))
                bottom = int(min(r[1] for r in native_siblings))
                top = int(max(r[1]+r[3] for r in native_siblings))
                excluded = (*ring['items'], *choices)
                gap_samples = []
                for yy in range(bottom, top):
                    for xx in range(left, right):
                        if any(rx-2*scale <= xx <= rx+rw+2*scale and
                               ry-2*scale <= yy <= ry+rh+2*scale
                               for rx, ry, rw, rh in excluded):
                            continue
                        gap_samples.append(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3])
                red_gap = sum(r > .7 and g < .2 and b < .1 for r, g, b in gap_samples)
                check(gap_samples and red_gap < max(3, len(gap_samples)//100),
                      f'{entry} {requested_scale}x sibling native entries share one background')
            bpy.data.images.remove(image)
            yield from move(choices[selected_index])
            hover_path = screenshot(f'native-style-{entry}-{requested_scale}-hover.png')
            hover_image = bpy.data.images.load(str(hover_path), check_existing=False)
            hover_pixels, hover_width = list(hover_image.pixels), hover_image.size[0]
            hx, hy, hw, hh = choices[selected_index]
            hover_changed = sum(
                sum(abs(a-b) for a, b in zip(
                    pixels[(yy*width+xx)*4:(yy*width+xx)*4+3],
                    hover_pixels[(yy*hover_width+xx)*4:(yy*hover_width+xx)*4+3])) > .12
                for yy in range(int(hy+3*scale), int(hy+hh-3*scale))
                for xx in range(int(hx+3*scale), int(hx+hw-3*scale)))
            check(hover_changed > 8*scale*scale,
                  f'{entry} {requested_scale}x native hover did not render')
            bpy.data.images.remove(hover_image)
            event('RIGHTMOUSE' if controls_index is None else 'LEFTMOUSE',
                  'RELEASE' if controls_index is None else 'PRESS')
            if controls_index is not None:
                event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            with bpy.context.temp_override(window=win, area=area, region=region):
                settings = json.loads(hotbox_runtime.snapshot(bpy.context))['settings']
            if entry.startswith('style'):
                check(settings['style'] == 'zones',
                      f'{entry} {requested_scale}x style setting not applied')
            elif entry.startswith('rows'):
                check(settings['rows'] == ['common', 'pane'] and
                      hotbox_runtime.current_settings()['rows'] == ['common', 'pane'],
                      f'{entry} {requested_scale}x row toggle not applied')
            else:
                check(settings['transparency'] == 75 and
                      hotbox_runtime.current_settings()['transparency'] == 75,
                      f'{entry} {requested_scale}x transparency setting not applied')
            event('SPACE', 'RELEASE')
            yield from settle()
            check(not win.screen.is_animation_playing, 'native menu leaked Space release')
    print('AXISMELD_HOTBOX_NATIVE_STYLE_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return .03
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


bpy.app.timers.register(tick, first_interval=1)

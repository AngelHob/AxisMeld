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
from axismeld_hotbox_geometry_fixture import ellipse_page, native_list, native_page
from axismeld import hotbox_runtime, runtime

bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
STYLE_LABELS = ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only')
ROW_LABELS = ('Show Common Menus', 'Show Pane Specific Menus', 'Show Modeling')
TRANSPARENCY_LABELS = ('0%', '25%', '50%', '75%', '100%')
CONTROL_LABELS = ('Menu Rows', 'Hotbox Style', 'Transparency', 'Center Mouse Buttons')
BUTTON_LABELS = ('Left Mouse Button', 'Middle Mouse Button', 'Right Mouse Button')
MAPPING_LABELS = ('Disabled', 'AxisMeld Views', 'Recent Commands', 'Hotbox Controls',
                  'Common', 'Select', 'Modify', 'Current Pane', 'Pane View', 'Pane Shading',
                  'Panels', 'Panel Views', 'Modeling')
MAPPING_VALUES = (None, 'views', 'center.recent', 'center.controls', 'common',
                  'common.select', 'common.modify', 'pane', 'pane.view', 'pane.shading',
                  'pane.panels', 'pane.panels.views', 'modeling')
MOUSE_BUTTONS = ('LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE')


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=4):
    for _ in range(count):
        yield


def mapping_suite():
    """Actual Center Mouse Buttons lists, pagination, release ownership and persistence."""
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    position = [0, 0]

    def event(kind, value='PRESS', point=None):
        if point is not None:
            position[:] = [int(v) for v in point]
        win.event_simulate(type=kind, value=value, x=position[0], y=position[1])

    def midpoint(rect):
        check(rect is not None, 'mapping input attempted an off-page row')
        return rect[0]+rect[2]/2, rect[1]+rect[3]/2

    def move(rect):
        event('MOUSEMOVE', 'NOTHING', midpoint(rect))
        yield from settle()

    def click(rect):
        yield from move(rect)
        event('LEFTMOUSE')
        yield
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()

    def screenshot(name):
        path = artifacts / name
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        return path

    layout_probe = os.environ.get('AXISMELD_TEST_NATIVE_LIST_LAYOUT', 'standard')
    if layout_probe == 'narrow':
        bpy.context.preferences.view.ui_scale = 1.0
        yield from settle(8)
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
        # The shared short-list narrow pane is tall enough for thirteen 24px rows.
        # Split only this disposable pane once more so the mapping list must paginate.
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=.75)
        yield from settle(8)
        area = max((a for a in win.screen.areas
                    if a.type == 'VIEW_3D' and a.width < 500 and 240 <= a.height < 320),
                   key=lambda a: a.height)
        region = next(r for r in area.regions if r.type == 'WINDOW')
        area.spaces.active.show_region_toolbar = False
        yield from settle(8)
    elif layout_probe == 'quad':
        bpy.context.preferences.view.ui_scale = 2.0
        yield from settle(8)
        area.spaces.active.show_region_toolbar = False
        area.spaces.active.show_region_ui = False
        area.spaces.active.show_region_header = False
        area.spaces.active.show_region_tool_header = False
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        region = min((r for r in area.regions if r.type == 'WINDOW'), key=lambda r: (r.y, r.x))
    elif layout_probe != 'standard':
        raise AssertionError(f'Unknown mapping list layout probe {layout_probe!r}')
    else:
        bpy.context.preferences.view.ui_scale = 1.0
        yield from settle(8)
        region = next(r for r in area.regions if r.type == 'WINDOW')

    scale = bpy.context.preferences.system.ui_scale
    logical_width, logical_height = region.width/scale, region.height/scale
    if layout_probe == 'narrow':
        check(360 <= logical_width < 430 and 240 <= logical_height < 320,
              f'narrow mapping probe outside bounded dimensions: {logical_width}x{logical_height}')
    elif layout_probe == 'quad':
        check(360 <= logical_width < 430 and 200 <= logical_height < 260,
              f'2x quad mapping probe outside bounded dimensions: {logical_width}x{logical_height}')
    print('MAPPING_LIST_LAYOUT', layout_probe, 'scale', scale, 'logical', logical_width,
          logical_height, 'physical', region.width, region.height, 'origin', region.x, region.y,
          flush=True)
    cx, cy = region.x+region.width/2, region.y+region.height/2
    bounds = (region.x, region.y, region.width, region.height)
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    icon_labels = {'AxisMeld', 'AxisMeld Views', 'Recent Commands', 'Hotbox Controls'}

    def measure(label):
        return blf.dimensions(0, label)[0] / scale + (20 if label in icon_labels else 0)

    center_width = (measure('AxisMeld')+40)*scale
    center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)
    control_width = (measure('Hotbox Controls')+40)*scale
    control = (center[0]+center[2]+83.6*scale, cy-19*scale, control_width, 38*scale)
    hotbox_user = runtime.profile_directory() / 'hotbox_user.json'
    observed = []
    settings_observed = []
    real_dispatch = hotbox_runtime.dispatch
    real_apply_setting = hotbox_runtime.apply_setting

    def observed_dispatch(context, command):
        result = real_dispatch(context, command)
        observed.append((command, result))
        return result

    def observed_setting(context, setting, value):
        result = real_apply_setting(context, setting, value)
        settings_observed.append((setting, value, result))
        return result

    hotbox_runtime.dispatch = observed_dispatch
    hotbox_runtime.apply_setting = observed_setting

    opener_button = [None]
    controls_first = [0]

    def reset_settings(opener=None):
        hotbox_user.unlink(missing_ok=True)
        opener_button[0] = opener
        session_settings = ({'center_buttons': {opener: 'center.controls'}} if opener else {})
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': 1, 'settings': session_settings})

    def enter_buttons():
        if layout_probe == 'standard':
            yield from click(control)
            controls_anchor = control
        else:
            check(opener_button[0] in MOUSE_BUTTONS,
                  f'{layout_probe} mapping suite requires a center Controls opener')
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            yield from settle()
            event(opener_button[0])
            yield
            event(opener_button[0], 'RELEASE')
            yield from settle()
            controls_anchor = center
        controls_page = ellipse_page(controls_anchor, CONTROL_LABELS, measure, bounds, scale,
                                     first=controls_first[0])
        while controls_page['items'][3] is None:
            count, setting_count = len(observed), len(settings_observed)
            yield from click(controls_page['next'])
            check(len(observed) == count and len(settings_observed) == setting_count,
                  'Controls navigation reached a command or setting dispatcher')
            controls_page = ellipse_page(controls_anchor, CONTROL_LABELS, measure, bounds, scale,
                                         first=controls_page['first']+1)
        controls_first[0] = controls_page['first']
        controls = controls_page['items']
        yield from click(controls[3])
        buttons = native_page(controls[3], BUTTON_LABELS, measure, bounds, scale,
                              submenu_indices=range(3))
        return controls[3], buttons

    def open_buttons():
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event('SPACE')
        yield from settle(8)
        controls_first[0] = 0
        return (yield from enter_buttons())

    def open_mapping(button_index, first=0):
        owner, buttons = yield from open_buttons()
        yield from click(buttons['items'][button_index])
        page = native_page(buttons['items'][button_index], MAPPING_LABELS, measure, bounds, scale,
                           first=first)
        return owner, buttons, page

    def close_box():
        event('SPACE', 'RELEASE')
        yield from settle()

    def settings():
        with bpy.context.temp_override(window=win, area=area, region=region):
            return json.loads(hotbox_runtime.snapshot(bpy.context))['settings']

    def image_pixels(path):
        image = bpy.data.images.load(str(path), check_existing=False)
        return image, list(image.pixels), image.size[0]

    def check_labels(path, page, labels, receipt):
        image, pixels, width = image_pixels(path)
        try:
            for index, rect in enumerate(page['items']):
                if rect is None:
                    continue
                x, y, w, h = rect
                ink = sum(min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]) > .55
                          for yy in range(int(y+3*scale), int(y+h-3*scale))
                          for xx in range(int(x+3*scale), int(x+w-3*scale)))
                check(ink > 2*scale*scale, f'{receipt} missing readable label {labels[index]!r}')
        finally:
            bpy.data.images.remove(image)

    def native_page_red_ratio(path, page):
        rows = ([page['previous']] if page['previous'] else [])
        rows += [rect for rect in page['items'] if rect is not None]
        rows += ([page['next']] if page['next'] else [])
        rows.sort(key=lambda rect: rect[1], reverse=True)
        check(rows, 'native page has no rows')
        for upper, lower in zip(rows, rows[1:]):
            check(abs(upper[1]-(lower[1]+lower[3])) < .1,
                  'native page rows are not a continuous 24px column')
        image, pixels, width = image_pixels(path)
        try:
            samples = []
            for x, y, w, h in rows:
                samples.extend(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                               for yy in range(int(y+4*scale), int(y+h-4*scale))
                               for xx in range(int(x+5*scale), int(x+9*scale)))
            return sum(r > .7 and g < .2 and b < .1 for r, g, b in samples) / len(samples)
        finally:
            bpy.data.images.remove(image)

    def check_native_page(path, page, receipt):
        check(native_page_red_ratio(path, page) > .6,
              f'{receipt} did not render the expected continuous native page')
        check_labels(path, page, MAPPING_LABELS, receipt)

    def prove_enabled_step(button_index, buttons, page, direction, receipt):
        delta = 1 if direction == 'next' else -1
        control_rect = page[direction]
        target = native_page(buttons['items'][button_index], MAPPING_LABELS, measure, bounds,
                             scale, first=page['first']+delta)
        exposed_index = (target['first']+target['capacity']-1 if delta > 0 else target['first'])
        expected = MAPPING_VALUES[exposed_index]
        expected_event_value = 'none' if expected is None else expected
        count, setting_count = len(observed), len(settings_observed)
        yield from click(control_rect)
        path = screenshot(
            f'mapping-{layout_probe}-{MOUSE_BUTTONS[button_index].lower()}-{receipt}.png')
        check_native_page(path, target, f'{layout_probe} {receipt}')
        check(len(observed) == count and len(settings_observed) == setting_count,
              f'{layout_probe} {receipt} navigation reached a dispatcher')
        yield from click(target['items'][exposed_index])
        check(len(observed) == count and len(settings_observed) == setting_count+1 and
              settings_observed[-1][:2] == (
                  f'center.{MOUSE_BUTTONS[button_index]}', expected_event_value) and
              settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected,
              f'{layout_probe} {receipt} did not expose literal {expected!r}')
        print('MAPPING_ENABLED_AFTER_DISABLED', layout_probe, BUTTON_LABELS[button_index],
              direction, 'first', target['first'], 'literal', expected, flush=True)

    def press_tool(key, expected):
        event(key)
        event(key, 'RELEASE')
        yield from settle()
        with bpy.context.temp_override(window=win, area=area, region=region):
            actual = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT').idname
        check(actual == expected, f'{key} was stolen after nested mapping exit: {actual}')

    menu_back = bpy.context.preferences.themes[0].user_interface.wcol_menu_back
    normal_menu_background = tuple(menu_back.inner)
    menu_back.inner = (.8, .12, .04, 1)
    reset_settings()
    if layout_probe == 'standard':
        owner, buttons = yield from open_buttons()
        button_path = screenshot('mapping-standard-button-block.png')
        image, pixels, width = image_pixels(button_path)
        try:
            rows = [buttons['items'][i] for i in range(3)]
            check(all(rect is not None for rect in rows), 'standard mapping submenu dropped a mouse row')
            for upper, lower in zip(rows, rows[1:]):
                check(abs(upper[1]-(lower[1]+lower[3])) < .1,
                      'mouse submenu rows are not one continuous 24px block')
                samples = [pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                           for yy in range(int(lower[1]+lower[3]-2*scale),
                                           int(lower[1]+lower[3]+2*scale))
                           for xx in range(int(lower[0]+5*scale), int(lower[0]+9*scale))]
                check(samples and sum(r > .7 and g < .2 and b < .1
                                      for r, g, b in samples) > len(samples)*.6,
                      'mouse submenu background is not continuous across rows')
            for index, (x, y, w, h) in enumerate(rows):
                arrow_ink = sum(min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]) > .65
                                for yy in range(int(y+h/2-5*scale), int(y+h/2+5*scale))
                                for xx in range(int(x+w-18*scale), int(x+w-4*scale)))
                check(arrow_ink > 3*scale*scale,
                      f'{BUTTON_LABELS[index]} native submenu arrow missing')
            ox, oy, ow, oh = owner
            bx, by, bw, bh = rows[0]
            separated = (bx >= ox+ow+9.99*scale or ox >= bx+bw+9.99*scale or
                         by >= oy+oh+9.99*scale or oy >= by+bh+9.99*scale)
            check(separated, 'Center Mouse Buttons owner and submenu are below 10px separation')
        finally:
            bpy.data.images.remove(image)
        yield from click(buttons['items'][0])
        page = native_page(buttons['items'][0], MAPPING_LABELS, measure, bounds, scale)
        check(page['capacity'] == 13 and page['previous'] is None and page['next'] is None,
              'standard mapping list must show all 13 choices without pagination')
        normal_path = screenshot('mapping-standard-left-full.png')
        check_native_page(normal_path, page, 'standard full mapping list')
        yield from move(page['items'][9])
        hover_path = screenshot('mapping-standard-left-hover.png')
        normal_image, normal_pixels, normal_width = image_pixels(normal_path)
        hover_image, hover_pixels, hover_width = image_pixels(hover_path)
        try:
            x, y, w, h = page['items'][9]
            changed = sum(sum(abs(a-b) for a, b in zip(
                              normal_pixels[(yy*normal_width+xx)*4:(yy*normal_width+xx)*4+3],
                              hover_pixels[(yy*hover_width+xx)*4:(yy*hover_width+xx)*4+3])) > .12
                          for yy in range(int(y+3*scale), int(y+h-3*scale))
                          for xx in range(int(x+3*scale), int(x+w-3*scale)))
            check(changed > 8*scale*scale, 'standard mapping row did not render native hover')
        finally:
            bpy.data.images.remove(normal_image)
            bpy.data.images.remove(hover_image)
        for _ in range(5):
            event('WHEELDOWNMOUSE')
        for _ in range(3):
            event('WHEELUPMOUSE')
        yield from settle()
        count, setting_count = len(observed), len(settings_observed)
        yield from click(page['items'][0])
        check(len(observed) == count and len(settings_observed) == setting_count+1 and
              settings_observed[-1][:2] == ('center.LEFTMOUSE', 'none') and
              settings()['center_buttons']['LEFTMOUSE'] is None,
              'full mapping list drifted under wheel or selected a non-literal first row')
        yield from close_box()

        for button_index, selected_index, expected in ((1, 4, 'common'), (2, 9, 'pane.shading')):
            _owner, _buttons, page = yield from open_mapping(button_index)
            count, setting_count = len(observed), len(settings_observed)
            yield from click(page['items'][selected_index])
            check(len(observed) == count and len(settings_observed) == setting_count+1 and
                  settings_observed[-1][:2] == (f'center.{MOUSE_BUTTONS[button_index]}', expected) and
                  settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected,
                  f'{BUTTON_LABELS[button_index]} did not apply literal {expected!r}')
            yield from close_box()
        expected_user = {'schema_version': 1, 'settings': {'center_buttons': {
            'LEFTMOUSE': None, 'MIDDLEMOUSE': 'common', 'RIGHTMOUSE': 'pane.shading'}}}
        check(json.loads(hotbox_user.read_text(encoding='utf-8')) == expected_user,
              'standard mappings did not write the exact delta-only user JSON')
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {}})
        check(settings()['center_buttons'] == {
            'LEFTMOUSE': None, 'MIDDLEMOUSE': 'common', 'RIGHTMOUSE': 'pane.shading'},
            'standard mappings did not reload from the persisted user layer')
        _owner, _buttons, _page = yield from open_mapping(2)
        check(settings()['center_buttons']['RIGHTMOUSE'] == 'pane.shading',
              'reopened nested mapping lost persisted Right Mouse setting')
        yield from close_box()

        # Held leaf selection owns its release; another mouse release cannot commit it.
        reset_settings()
        _owner, _buttons, page = yield from open_mapping(0)
        yield from move(page['items'][6])
        count, setting_count = len(observed), len(settings_observed)
        event('LEFTMOUSE')
        yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count and len(settings_observed) == setting_count,
              'non-owning release committed held mapping selection')
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count and len(settings_observed) == setting_count+1 and
              settings_observed[-1][:2] == ('center.LEFTMOUSE', 'common.modify'),
              'owning release did not commit held mapping selection')
        yield from close_box()
        yield from press_tool('W', 'builtin.move')

        reset_settings()
        _owner, _buttons, page = yield from open_mapping(1)
        yield from move(page['items'][10])
        count, setting_count = len(observed), len(settings_observed)
        event('LEFTMOUSE')
        yield
        event('SPACE', 'RELEASE')
        yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        check(len(observed) == count and len(settings_observed) == setting_count and
              settings()['center_buttons']['MIDDLEMOUSE'] == 'views',
              'Space-first release committed a held mapping')
        yield from press_tool('E', 'builtin.rotate')

        reset_settings()
        _owner, _buttons, page = yield from open_mapping(2)
        yield from move(page['items'][12])
        count, setting_count = len(observed), len(settings_observed)
        event('LEFTMOUSE')
        yield
        event('ESC')
        event('ESC', 'RELEASE')
        event('LEFTMOUSE', 'RELEASE')
        event('SPACE', 'RELEASE')
        yield from settle()
        check(len(observed) == count and len(settings_observed) == setting_count and
              settings()['center_buttons']['RIGHTMOUSE'] == 'views',
              'Esc committed a held mapping')
        yield from press_tool('R', 'builtin.scale')
        check(not observed, 'mapping-only suite reached the command dispatcher')
        print('PASS standard mappings: native blocks, all labels, hover, no drift, releases and W/E/R',
              flush=True)
    else:
        selected_indices = (11, 12, 9)
        for button_index, selected_index in enumerate(selected_indices):
            opener = MOUSE_BUTTONS[(button_index+1) % len(MOUSE_BUTTONS)]
            reset_settings(opener)
            _owner, _buttons, page = yield from open_mapping(button_index)
            check(1 < page['capacity'] < 13 and page['previous'] is not None and page['next'] is not None,
                  f'{layout_probe} mapping page did not expose bounded navigation')
            initial = settings()['center_buttons'][MOUSE_BUTTONS[button_index]]
            count, setting_count = len(observed), len(settings_observed)
            yield from move(page['previous'])
            event('LEFTMOUSE')
            yield from settle()
            if button_index == 0:
                pressed = screenshot(f'mapping-{layout_probe}-disabled-previous-press.png')
                check(native_page_red_ratio(pressed, page) > .6,
                      f'{layout_probe} disabled previous press prematurely left its page')
            check(len(observed) == count and len(settings_observed) == setting_count,
                  f'{layout_probe} disabled previous press applied a setting')
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count and len(settings_observed) == setting_count,
                  f'{layout_probe} non-owner release changed disabled previous ownership')
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            if button_index == 0:
                released = screenshot(f'mapping-{layout_probe}-disabled-previous-release.png')
                check(native_page_red_ratio(released, page) > .6,
                      f'{layout_probe} disabled previous owner release lost the leaf page')
            check(len(observed) == count and len(settings_observed) == setting_count and
                  settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == initial,
                  f'{layout_probe} disabled previous arrow applied a setting')
            print('MAPPING_DISABLED_BOUNDARY', layout_probe, 'previous',
                  'press=page non-owner=page owner-release=page no-setting', flush=True)
            yield from prove_enabled_step(button_index, _buttons, page, 'next',
                                          'enabled-next-after-disabled-previous')
            yield from close_box()
            reset_settings(opener)
            _owner, _buttons, page = yield from open_mapping(button_index)
            visible = set()
            while True:
                path = screenshot(
                    f'mapping-{layout_probe}-{MOUSE_BUTTONS[button_index].lower()}-page-{page["first"]}.png')
                check_native_page(
                    path, page,
                    f'{layout_probe} {BUTTON_LABELS[button_index]} page {page["first"]}')
                visible.update(i for i, rect in enumerate(page['items']) if rect is not None)
                if page['first'] + page['capacity'] == 13:
                    break
                before_settings = settings()['center_buttons'][MOUSE_BUTTONS[button_index]]
                count, setting_count = len(observed), len(settings_observed)
                yield from click(page['next'])
                check(len(observed) == count and len(settings_observed) == setting_count and
                      settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == before_settings,
                      f'{layout_probe} navigation release selected the newly exposed row')
                page = native_page(_buttons['items'][button_index], MAPPING_LABELS, measure, bounds,
                                   scale, first=page['first']+1)
            check(visible == set(range(13)),
                  f'{layout_probe} {BUTTON_LABELS[button_index]} did not expose all 13 choices')
            count, setting_count = len(observed), len(settings_observed)
            yield from move(page['next'])
            event('LEFTMOUSE')
            yield from settle()
            if button_index == 0:
                pressed = screenshot(f'mapping-{layout_probe}-disabled-next-press.png')
                check(native_page_red_ratio(pressed, page) > .6,
                      f'{layout_probe} disabled next press prematurely left its page')
            check(len(observed) == count and len(settings_observed) == setting_count,
                  f'{layout_probe} disabled next press applied a setting')
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count and len(settings_observed) == setting_count,
                  f'{layout_probe} non-owner release changed disabled next ownership')
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            if button_index == 0:
                released = screenshot(f'mapping-{layout_probe}-disabled-next-release.png')
                check(native_page_red_ratio(released, page) > .6,
                      f'{layout_probe} disabled next owner release lost the leaf page')
            check(len(observed) == count and len(settings_observed) == setting_count,
                  f'{layout_probe} disabled next arrow applied a setting')
            print('MAPPING_DISABLED_BOUNDARY', layout_probe, 'next',
                  'press=page non-owner=page owner-release=page no-setting', flush=True)
            yield from prove_enabled_step(button_index, _buttons, page, 'previous',
                                          'enabled-previous-after-disabled-next')
            yield from close_box()
            reset_settings(opener)
            if button_index == 0:
                # Keep an unaffected Controls route in the private user layer before this
                # hotbox starts, so sibling literal submission can refresh and re-enter it.
                real_apply_setting(bpy.context, f'center.{opener}', 'center.controls')
                check(opener == 'MIDDLEMOUSE' and
                      settings()['center_buttons'][opener] == 'center.controls',
                      f'{layout_probe} could not prepare persistent Controls opener')
            _owner, _buttons, page = yield from open_mapping(button_index)
            while page['first']+page['capacity'] < 13:
                yield from click(page['next'])
                page = native_page(_buttons['items'][button_index], MAPPING_LABELS, measure,
                                   bounds, scale, first=page['first']+1)

            if button_index == 0:
                last_first = page['first']
                yield from move(page['items'][selected_index])
                for _ in range(20):
                    event('WHEELDOWNMOUSE')
                yield from settle()
                screenshot(f'mapping-{layout_probe}-wheel-last-excess.png')
                event('WHEELUPMOUSE')
                yield from settle()
                reversed_page = native_page(_buttons['items'][button_index], MAPPING_LABELS,
                                            measure, bounds, scale, first=last_first-1)
                check(reversed_page['first'] == last_first-1,
                      f'{layout_probe} fixture did not define a one-item tail reversal')
                reversed_path = screenshot(f'mapping-{layout_probe}-wheel-last-reversed.png')
                check_native_page(reversed_path, reversed_page,
                                  f'{layout_probe} tail-wheel reversed owner page')

                # Per-owner offsets must remain independent inside this exact hotbox session.
                # Switch to an untouched sibling without releasing Space, prove its disabled
                # previous boundary and first literal, then re-enter through the unaffected
                # middle-button opener and prove the original owner's retained page.
                sibling_index = 2
                yield from click(_buttons['items'][sibling_index])
                sibling_page = native_page(_buttons['items'][sibling_index], MAPPING_LABELS,
                                           measure, bounds, scale)
                sibling_path = screenshot(f'mapping-{layout_probe}-wheel-sibling-first.png')
                check_native_page(sibling_path, sibling_page,
                                  f'{layout_probe} untouched sibling first page')
                count, setting_count = len(observed), len(settings_observed)
                yield from click(sibling_page['previous'])
                sibling_boundary = screenshot(
                    f'mapping-{layout_probe}-wheel-sibling-disabled-previous.png')
                check_native_page(sibling_boundary, sibling_page,
                                  f'{layout_probe} sibling disabled previous page')
                check(len(observed) == count and len(settings_observed) == setting_count,
                      f'{layout_probe} sibling disabled previous changed a setting')
                yield from click(sibling_page['items'][0])
                check(len(observed) == count and len(settings_observed) == setting_count+1 and
                      settings_observed[-1][:2] == ('center.RIGHTMOUSE', 'none') and
                      settings()['center_buttons']['RIGHTMOUSE'] is None,
                      f'{layout_probe} sibling first row was not literal None')
                check(settings()['center_buttons'][opener] == 'center.controls',
                      f'{layout_probe} sibling setting changed the unaffected opener')

                _owner, retained_buttons = yield from enter_buttons()
                yield from click(retained_buttons['items'][button_index])
                reversed_page = native_page(retained_buttons['items'][button_index],
                                            MAPPING_LABELS, measure, bounds, scale,
                                            first=last_first-1)
                retained_path = screenshot(f'mapping-{layout_probe}-wheel-owner-retained.png')
                check_native_page(retained_path, reversed_page,
                                  f'{layout_probe} original owner retained wheel page')
                first_index = reversed_page['first']
                expected = MAPPING_VALUES[first_index]
                expected_event_value = 'none' if expected is None else expected
                count, setting_count = len(observed), len(settings_observed)
                yield from click(reversed_page['items'][first_index])
                check(len(observed) == count and len(settings_observed) == setting_count+1 and
                      settings_observed[-1][:2] == ('center.LEFTMOUSE', expected_event_value) and
                      settings()['center_buttons']['LEFTMOUSE'] == expected,
                      f'{layout_probe} tail wheel reversal did not move visible first row by one')
                real_apply_setting(bpy.context, 'center.RIGHTMOUSE', 'views')
                real_apply_setting(bpy.context, f'center.{opener}', 'views')
                check(settings()['center_buttons']['RIGHTMOUSE'] == 'views' and
                      settings()['center_buttons'][opener] == 'views',
                      f'{layout_probe} could not remove private sibling/opener setup')
                print('MAPPING_TAIL_WHEEL', layout_probe, 'capacity', page['capacity'],
                      'excess_down', 20, 'last_first', last_first,
                      'reversed_first', first_index, 'literal', expected,
                      'sibling_first', 0, 'owner_retained', first_index, flush=True)
                print('MAPPING_SIBLING_OFFSET', layout_probe,
                      'same-session first=0 previous=disabled literal=None owner=retained',
                      first_index, flush=True)
            else:
                expected = MAPPING_VALUES[selected_index]
                expected_event_value = 'none' if expected is None else expected
                count, setting_count = len(observed), len(settings_observed)
                yield from click(page['items'][selected_index])
                check(len(observed) == count and len(settings_observed) == setting_count+1 and
                      settings_observed[-1][:2] == (
                          f'center.{MOUSE_BUTTONS[button_index]}', expected_event_value) and
                      settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected,
                      f'{layout_probe} {BUTTON_LABELS[button_index]} scrolled literal not applied')
            yield from close_box()
            expected_value = settings()['center_buttons'][MOUSE_BUTTONS[button_index]]
            expected_user = {'schema_version': 1, 'settings': {'center_buttons': {
                MOUSE_BUTTONS[button_index]: expected_value}}}
            check(json.loads(hotbox_user.read_text(encoding='utf-8')) == expected_user,
                  f'{layout_probe} mapping did not write one-button delta JSON')
            hotbox_runtime.reload_settings(bpy.context,
                                           session={'schema_version': 1, 'settings': {}})
            check(settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected_value,
                  f'{layout_probe} mapping did not reload persisted value')
            opener_button[0] = opener
            hotbox_runtime.reload_settings(bpy.context, session={
                'schema_version': 1, 'settings': {
                    'center_buttons': {opener: 'center.controls'}}})
            _owner, _buttons, _page = yield from open_mapping(button_index)
            check(settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected_value,
                  f'{layout_probe} reopened mapping lost persisted value')
            yield from close_box()

        # First-page excess upward wheel, then one downward event must expose literal `views`.
        reset_settings('LEFTMOUSE')
        _owner, _buttons, page = yield from open_mapping(2)
        yield from move(page['items'][0])
        for _ in range(20):
            event('WHEELUPMOUSE')
        yield from settle()
        event('WHEELDOWNMOUSE')
        yield from settle()
        first_reversed = native_page(_buttons['items'][2], MAPPING_LABELS, measure, bounds,
                                     scale, first=1)
        count, setting_count = len(observed), len(settings_observed)
        yield from click(first_reversed['items'][1])
        check(len(observed) == count and len(settings_observed) == setting_count+1 and
              settings_observed[-1][:2] == ('center.RIGHTMOUSE', 'views') and
              settings()['center_buttons']['RIGHTMOUSE'] == 'views',
              f'{layout_probe} first-page wheel reversal was not exactly one item')
        yield from close_box()
        check(not observed, f'{layout_probe} mapping navigation reached command dispatcher')
        print('PASS', layout_probe,
              'all mapping literals visible; real controls, wheel bounds, persistence and owner settings',
              flush=True)

    menu_back.inner = normal_menu_background
    area.tag_redraw()
    yield from settle()
    if layout_probe == 'standard':
        reset_settings()
    else:
        reset_settings('LEFTMOUSE')
    _owner, _buttons, _page = yield from open_mapping(2)
    screenshot(f'mapping-{layout_probe}-normal-theme.png')
    yield from close_box()
    hotbox_runtime.dispatch = real_dispatch
    hotbox_runtime.apply_setting = real_apply_setting
    print('AXISMELD_HOTBOX_MAPPING_LISTS_PASS', flush=True)


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
            controls_page = ellipse_page(center, control_labels, measure, bounds, scale)
            while controls_page['items'][index] is None:
                yield from click(controls_page['next'])
                controls_page = ellipse_page(center, control_labels, measure, bounds, scale,
                                             first=controls_page['first']+1)
            owner = controls_page['items'][index]
            yield from click(owner)
            return owner, native_list(owner, labels, measure, bounds, scale)

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


steps = (mapping_suite() if os.environ.get('AXISMELD_TEST_SUITE') == 'mappings' else suite())


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

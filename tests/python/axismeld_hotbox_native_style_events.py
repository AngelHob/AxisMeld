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
from axismeld_hotbox_geometry_fixture import ellipse_page, native_list, native_page, native_fixture_surface, visible_bounds
from axismeld import hotbox_runtime, runtime

bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
STYLE_LABELS = ('Zones and Menu Rows', 'Zones Only', 'Center Zone Only')
MODELING_LABELS = ('Modeling Only', 'Show/Hide Modeling')
CONTROL_STYLE_LABELS = STYLE_LABELS + ('', 'Center Zone RMB Popups')
TRANSPARENCY_LABELS = ('0%', '25%', '50%', '75%', '100%')
CONTROL_LABELS = ('Show Modeling', 'Show Rigging', 'Show Animation', 'Show FX',
                  'Show All', 'Hide All', 'Show Rendering', 'Show Common Menus',
                  'Show Pane Specific Menus', 'Show Custom Menu Set Menus',
                  'Set Transparency', 'Hotbox Style', '', 'Window Options')
CONTROL_SUBMENUS = (0, 1, 2, 3, 6, 10, 11, 13)

def catalog_layout(anchor, identifier, bounds, scale):
    """Read public text/state only; never import production layout or hit rectangles."""
    pending = list(json.loads(hotbox_runtime.snapshot(bpy.context))['menus'])
    while pending:
        node = pending.pop()
        if node['id'] == identifier:
            break
        pending.extend(node['children'])
    else:
        raise AssertionError('Missing public menu: ' + identifier)
    children = node['children']
    has_state = any(child.get('indicator') for child in children)
    widths = {}
    for child in children:
        extra = 0 if child['kind'] == 'separator' else 20 + 20*has_state
        if child['kind'] != 'menu' and child['children']:
            extra += 24
        widths[child['label']] = max(widths.get(child['label'], 0),
            blf.dimensions(0, child['label'])[0]/scale + extra)
    result = native_page(anchor, [child['label'] for child in children], widths.__getitem__, bounds, scale,
                        submenu_indices=[i for i, child in enumerate(children) if child['kind'] == 'menu'])
    result['by_id'] = {child['id']: rect for child, rect in zip(children, result['items'])}
    result['nodes'] = children
    return result

def controls_layout(anchor, measure, bounds, scale, first=0):
    # Complete native sibling group owns both the semantic and state columns.
    page = native_page(anchor, CONTROL_LABELS,
                       lambda label: blf.dimensions(0, label)[0]/scale + (40 if label else 0),
                       bounds, scale, first=first, submenu_indices=CONTROL_SUBMENUS)
    page['back'] = None
    return page
BUTTON_LABELS = ('Left Mouse Button', 'Middle Mouse Button', 'Right Mouse Button')
MAPPING_LABELS = ('Disabled', 'AxisMeld Views', 'Recent Commands', 'Hotbox Controls',
                  'Common', 'Select', 'Modify', 'Current Pane', 'Pane View', 'Pane Shading',
                  'Panels', 'Panel Views', 'Modeling')
MAPPING_VALUES = (None, 'views', 'center.recent', 'center.controls', 'common',
                  'common.select', 'common.modify', 'pane', 'pane.view', 'pane.shading',
                  'pane.panels', 'pane.panels.views', 'modeling')
MOUSE_BUTTONS = ('LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE')
VISIBLE_REGION_SIDES = {'TOOLS': 'left', 'UI': 'right', 'TOOL_HEADER': 'top'}


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=4):
    for _ in range(count):
        yield


def observed_visible_bounds(area, window_region):
    """Return fixture bounds from real, currently visible overlap-region edges."""
    window = (window_region.x, window_region.y, window_region.width, window_region.height)
    wx, wy, ww, wh = window
    obstacles = []
    for candidate in area.regions:
        side = VISIBLE_REGION_SIDES.get(candidate.type)
        if side is None or candidate.width <= 1 or candidate.height <= 1:
            continue
        rect = (candidate.x, candidate.y, candidate.width, candidate.height)
        x, y, w, h = rect
        if x >= wx+ww or x+w <= wx or y >= wy+wh or y+h <= wy:
            continue
        obstacles.append((side, rect, candidate.type))
    safe = visible_bounds(window, tuple((side, rect) for side, rect, _kind in obstacles))
    return window, safe, obstacles


def check_radio_image(path, choices, selected_index, scale):
    """Inspect native circle pixels independently of the C++ state helper and hover flag."""
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        pixels, width = list(image.pixels), image.size[0]
        states = []
        for rect in choices:
            if rect is None:
                states.append(None)
                continue
            x, y, w, h = rect
            # Actual 1x Style capture places the independent radio center at row x+11;
            # the semantic icon occupies the next column and must not count as state.
            ink = sum(min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]) > .55
                      for yy in range(int(y+h/2-6*scale), int(y+h/2+6*scale))
                      for xx in range(int(x+5*scale), int(x+17*scale)))
            check(ink > 8*scale*scale, f'{path.name}: missing circle at {rect}')
            center = [min(pixels[(yy*width+xx)*4:(yy*width+xx)*4+3])
                      for yy in range(int(y+h/2-scale), int(y+h/2+scale))
                      for xx in range(int(x+10*scale), int(x+12*scale))]
            states.append(sum(center)/len(center) > .55)
        check(states == [None if rect is None else i == selected_index
                         for i, rect in enumerate(choices)],
              f'{path.name}: rendered radio state {states}, expected index {selected_index}')
        print('RADIO_PIXELS_PASS', path.name, states, flush=True)
    finally:
        bpy.data.images.remove(image)


def mapping_suite():
    """Actual complete Center Mouse Buttons lists, release ownership and persistence."""
    win = bpy.context.window
    native_fixture_surface((0, 0, win.width, win.height))
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
        # Split only this disposable pane once more so the mapping list must require a larger drawing surface.
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
        with bpy.context.temp_override(window=win, area=area, region=region):
            check(bpy.ops.screen.screen_full_area() == {'FINISHED'},
                  '2x quad mapping probe could not maximize its disposable VIEW_3D')
        yield from settle(8)
        area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in area.regions if r.type == 'WINDOW')
        area.spaces.active.show_region_toolbar = True
        area.spaces.active.show_region_ui = True
        area.spaces.active.show_region_header = False
        area.spaces.active.show_region_tool_header = True
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
        yield from settle(8)
        quad_windows = [r for r in area.regions if r.type == 'WINDOW' and
                        r.width > 1 and r.height > 1]
        check(len(quad_windows) == 4,
              f'2x quad probe expected four independent WINDOW regions, got '
              f'{[(r.x, r.y, r.width, r.height) for r in quad_windows]!r}')
        region = min(quad_windows, key=lambda r: (r.y, r.x))
        print('MAPPING_QUAD_WINDOWS',
              [(r.x, r.y, r.width, r.height) for r in quad_windows], flush=True)
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
        check(430 <= logical_width < 500 and 200 <= logical_height < 260,
              f'2x quad mapping probe outside bounded dimensions: {logical_width}x{logical_height}')
    print('MAPPING_LIST_LAYOUT', layout_probe, 'scale', scale, 'logical', logical_width,
          logical_height, 'physical', region.width, region.height, 'origin', region.x, region.y,
          flush=True)
    cx, cy = region.x+region.width/2, region.y+region.height/2
    window_bounds, bounds, visible_obstacles = observed_visible_bounds(area, region)
    print('MAPPING_VISIBLE_BOUNDS', layout_probe, 'window', window_bounds, 'safe', bounds,
          'obstacles', visible_obstacles, flush=True)
    if layout_probe == 'narrow':
        check(any(kind == 'TOOL_HEADER' for _side, _rect, kind in visible_obstacles),
              'narrow mapping probe requires its real visible Tool Header obstacle')
        check(bounds[3] < window_bounds[3],
              'narrow mapping safe bounds did not exclude the real Tool Header')
    elif layout_probe == 'quad':
        obstacle_kinds = {kind for _side, _rect, kind in visible_obstacles}
        check(obstacle_kinds == {'TOOLS'} and bounds[0] > window_bounds[0],
              f'2x lower-left WINDOW did not isolate its intersecting toolbar: '
              f'{visible_obstacles!r}')
        check('TOOL_HEADER' not in obstacle_kinds and 'UI' not in obstacle_kinds,
              f'2x lower-left WINDOW was clipped by a non-intersecting sibling: '
              f'{visible_obstacles!r}')
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    def measure(label):
        return blf.dimensions(0, label)[0] / scale + 20

    def mapping_measure(label):
        # Button mappings have a separate radio column; their menu titles do not.
        return measure(label) + 20

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
        session_settings = ({'center_buttons': {opener: 'internal.blender'}} if opener else {})
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': 1, 'settings': session_settings})

    extension_page = [None]
    requested_mapping = [0]
    route_button = [None]

    def prepare_extension_opener():
        # Use a different button from the setting under test. This session-only
        # route never writes the user layer or changes that row's expected radio.
        opener = opener_button[0]
        if opener is None or opener == MOUSE_BUTTONS[requested_mapping[0]]:
            opener = MOUSE_BUTTONS[(requested_mapping[0]+1) % 3]
        route_button[0] = opener
        current = hotbox_runtime.current_settings()
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {}})
        current['center_buttons'] = hotbox_runtime.current_settings()['center_buttons']
        current['center_buttons'][opener] = 'internal.blender'
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': current})
        return opener

    def enter_buttons():
        opener = route_button[0]
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        yield from settle()
        event(opener)
        yield
        event(opener, 'RELEASE')
        yield from settle()
        extension_page[0] = catalog_layout(center, 'internal.blender', bounds, scale)
        owner = extension_page[0]['by_id']['center.controls.buttons']
        yield from click(owner)
        buttons = native_page(owner, BUTTON_LABELS, measure, bounds, scale,
                              submenu_indices=range(3))
        return owner, buttons

    def open_buttons():
        prepare_extension_opener()
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event('SPACE')
        yield from settle(8)
        controls_first[0] = 0
        return (yield from enter_buttons())

    def open_mapping(button_index, first=0):
        requested_mapping[0] = button_index
        owner, buttons = yield from open_buttons()
        yield from click(buttons['items'][button_index])
        page = native_page(buttons['items'][button_index], MAPPING_LABELS, mapping_measure, bounds, scale,
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
        rows.sort(key=lambda rect: (rect[0], -rect[1]))
        check(rows, 'native page has no rows')
        for upper, lower in zip(rows, rows[1:]):
            if abs(upper[0]-lower[0]) > .1: continue
            check(abs(upper[1]-(lower[1]+lower[3])) < .1,
                  'native complete rows are not continuous within their column')
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
        rows = ([page['previous']] if page['previous'] else [])
        rows += [rect for rect in page['items'] if rect is not None]
        rows += ([page['next']] if page['next'] else [])
        surface = page.get('bounds', bounds)
        bx, by, bw, bh = surface
        obstacles = visible_obstacles if tuple(surface) == tuple(bounds) else []
        for rect in rows:
            x, y, w, h = rect
            check(x >= bx and y >= by and x+w <= bx+bw and y+h <= by+bh,
                  f'{receipt} row {rect!r} escaped visible bounds {bounds!r}')
            for _side, obstacle, kind in obstacles:
                ox, oy, ow, oh = obstacle
                check(x+w <= ox or ox+ow <= x or y+h <= oy or oy+oh <= y,
                      f'{receipt} row {rect!r} overlaps visible {kind} {obstacle!r}')
        check(native_page_red_ratio(path, page) > .6,
              f'{receipt} did not render the expected continuous native page')
        check_labels(path, page, MAPPING_LABELS, receipt)
        image, pixels, width = image_pixels(path)
        try:
            for _side, (x, y, w, h), kind in obstacles:
                samples = [pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                           for yy in range(int(y+2), int(y+h-2))
                           for xx in range(int(x+2), int(x+w-2))]
                menu_red = sum(r > .7 and g < .2 and b < .1 for r, g, b in samples)
                check(samples and menu_red < max(8, len(samples)//50),
                      f'{receipt} rendered {menu_red} menu-background pixels across visible '
                      f'{kind} {(x, y, w, h)!r}')
        finally:
            bpy.data.images.remove(image)

    def press_tool(key, expected):
        event(key)
        yield
        event(key, 'RELEASE')
        yield from settle()
        with bpy.context.temp_override(window=win, area=area, region=region):
            actual = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT').idname
        check(actual == expected, f'{key} was stolen after nested mapping exit: {actual}')

    def held_leaf_cancel(boundary, cancel_kind, selected_index):
        opener = 'MIDDLEMOUSE'
        reset_settings(opener)
        _owner, buttons, page = yield from open_mapping(0)
        held_rect = page['items'][-1 if boundary == 'next' else 0]
        before = settings()['center_buttons']
        count, setting_count = len(observed), len(settings_observed)
        ready_path = screenshot(
            f'mapping-{layout_probe}-held-leaf-{boundary}-{cancel_kind}-ready.png')
        check_native_page(ready_path, page,
                          f'{layout_probe} held leaf {boundary} before {cancel_kind}')
        # The removed navigation arrows are replaced by an actual leaf press;
        # cancelling before its owner release must still produce no setting.
        yield from move(held_rect)
        event('LEFTMOUSE')
        yield from settle()
        check(len(observed) == count and len(settings_observed) == setting_count and
              settings()['center_buttons'] == before,
              f'{layout_probe} held leaf {boundary} changed state before cancellation')
        if cancel_kind == 'space-first':
            event('SPACE', 'RELEASE')
            yield from settle()
            event('LEFTMOUSE', 'RELEASE')
        else:
            check(cancel_kind == 'esc', f'unknown held cancellation {cancel_kind!r}')
            event('ESC')
            event('ESC', 'RELEASE')
            yield from settle()
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            event('SPACE', 'RELEASE')
        yield from settle()
        check(len(observed) == count and len(settings_observed) == setting_count and
              settings()['center_buttons'] == before,
              f'{layout_probe} held leaf {boundary} cancellation leaked an outcome')
        modal_ids = [op.bl_idname for op in win.modal_operators]
        check(not modal_ids,
              f'{layout_probe} held {boundary} {cancel_kind} left modal guards {modal_ids!r}')
        print('MAPPING_HELD_LEAF_POST_RELEASE', layout_probe, boundary, cancel_kind,
              'modal=[]', flush=True)
        for key, expected_tool in (
                ('W', 'builtin.move'), ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
            yield from press_tool(key, expected_tool)

        _owner, buttons, fresh = yield from open_mapping(0)
        fresh_path = screenshot(
            f'mapping-{layout_probe}-held-leaf-{boundary}-{cancel_kind}-reopened.png')
        check_native_page(fresh_path, fresh,
                          f'{layout_probe} reopened after held {boundary} {cancel_kind}')
        expected = MAPPING_VALUES[selected_index]
        expected_event_value = 'none' if expected is None else expected
        yield from click(fresh['items'][selected_index])
        check(len(observed) == count and len(settings_observed) == setting_count+1 and
              settings_observed[-1][:2] == ('center.LEFTMOUSE', expected_event_value) and
              settings()['center_buttons']['LEFTMOUSE'] == expected,
              f'{layout_probe} held {boundary} {cancel_kind} left residual ownership')
        yield from close_box()
        print('MAPPING_HELD_LEAF_CANCEL', layout_probe, boundary, cancel_kind,
              'trailing-owner-release no-dispatch no-setting WER reopened-literal', expected,
              flush=True)

    def visible_region_change_cancel(property_name, region_type):
        check(layout_probe == 'standard', 'visible-region change probe requires standard layout')
        space = area.spaces.active
        initial_visibility = getattr(space, property_name)
        bpy.context.preferences.view.use_reduce_motion = False
        with bpy.context.temp_override(window=win, area=area, region=region):
            setattr(space, property_name, False)
        area.tag_redraw()
        yield from settle(16)

        def region_rects():
            return [
                (candidate.x, candidate.y, candidate.width, candidate.height)
                for candidate in area.regions if candidate.type == region_type
            ]

        def start_session():
            reset_settings()
            before = settings()['center_buttons']
            counts = len(observed), len(settings_observed)
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('SPACE')
            yield from settle(8)
            modal_ids = [op.bl_idname for op in win.modal_operators]
            check('VIEW3D_OT_axismeld_hotbox' in modal_ids,
                  f'{region_type} change probe did not start a hotbox session: {modal_ids!r}')
            return before, counts, tuple(position)

        def finish_cancel(before, counts, unchanged_point, direction):
            check(tuple(position) == unchanged_point,
                  f'{region_type} {direction} cancellation probe moved the pointer')
            modal_ids = [op.bl_idname for op in win.modal_operators]
            check('VIEW3D_OT_axismeld_hotbox' not in modal_ids,
                  f'{region_type} {direction} change left the hotbox session active '
                  f'{modal_ids!r}')
            event('SPACE', 'RELEASE')
            yield from settle()
            modal_ids = [op.bl_idname for op in win.modal_operators]
            check(not modal_ids,
                  f'{region_type} {direction} Space release left modal guards {modal_ids!r}')
            count, setting_count = counts
            check(len(observed) == count and len(settings_observed) == setting_count and
                  settings()['center_buttons'] == before,
                  f'{region_type} {direction} change committed a hotbox outcome')
            for key, expected_tool in (
                    ('W', 'builtin.move'), ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
                yield from press_tool(key, expected_tool)

        # Hidden -> visible changes the full safe rectangle as soon as the native
        # overlap animation starts, so the old session must cancel at the same point.
        before, counts, unchanged_point = yield from start_session()
        with bpy.context.temp_override(window=win, area=area, region=region):
            setattr(space, property_name, True)
        area.tag_redraw()
        yield
        first_visible = tuple(region_rects())
        check(any(w > 1 and h > 1 for _x, _y, w, h in first_visible),
              f'{property_name} did not expose a real {region_type} region')
        event('MOUSEMOVE', 'NOTHING', unchanged_point)
        yield from settle()
        yield from finish_cancel(before, counts, unchanged_point, 'hidden-to-visible')

        # Visible -> hidden keeps the full original winrct while Blender's native
        # overlap fade is active.  It must remain a live session during that fade,
        # then cancel once the region has actually disappeared.
        yield from settle(16)
        before, counts, unchanged_point = yield from start_session()
        with bpy.context.temp_override(window=win, area=area, region=region):
            setattr(space, property_name, False)
        area.tag_redraw()
        yield
        in_flight = tuple(region_rects())
        check(any(w > 1 and h > 1 for _x, _y, w, h in in_flight),
              f'{region_type} did not retain its full rect during native hide animation: '
              f'{in_flight!r}')
        event('MOUSEMOVE', 'NOTHING', unchanged_point)
        yield from settle()
        modal_ids = [op.bl_idname for op in win.modal_operators]
        check('VIEW3D_OT_axismeld_hotbox' in modal_ids,
              f'{region_type} hide animation discarded its full bounds early: {modal_ids!r}')
        hidden = tuple(region_rects())
        for _attempt in range(40):
            if all(w <= 1 or h <= 1 for _x, _y, w, h in hidden):
                break
            yield
            hidden = tuple(region_rects())
        check(all(w <= 1 or h <= 1 for _x, _y, w, h in hidden),
              f'{region_type} native hide animation did not finish: {hidden!r}')
        event('MOUSEMOVE', 'NOTHING', unchanged_point)
        yield from settle()
        yield from finish_cancel(before, counts, unchanged_point, 'visible-to-hidden')

        with bpy.context.temp_override(window=win, area=area, region=region):
            setattr(space, property_name, initial_visibility)
        area.tag_redraw()
        yield from settle(16)
        print('MAPPING_VISIBLE_REGION_CHANGE_CANCEL', property_name, region_type,
              'point', unchanged_point, 'first-visible', first_visible,
              'hide-in-flight', in_flight, 'hidden-final', hidden,
              'both-directions release-modal=[] WER', flush=True)

    def quad_upper_overlap_probe():
        check(layout_probe == 'quad', 'upper overlap probe requires four-view layout')
        upper = min(quad_windows, key=lambda candidate: (-candidate.y, candidate.x))
        upper_window, upper_bounds, upper_obstacles = observed_visible_bounds(area, upper)
        kinds = {kind for _side, _rect, kind in upper_obstacles}
        check(kinds == {'TOOLS', 'TOOL_HEADER'} and upper_bounds[0] > upper_window[0] and
              upper_bounds[3] < upper_window[3],
              f'2x upper-left WINDOW did not include its intersecting toolbar/header: '
              f'{upper_obstacles!r}')
        check('UI' not in kinds,
              f'2x upper-left WINDOW was clipped by non-intersecting UI: '
              f'{upper_obstacles!r}')
        reset_settings('LEFTMOUSE')
        count, setting_count = len(observed), len(settings_observed)
        point = (upper.x+upper.width//2, upper.y+upper.height//2)
        event('MOUSEMOVE', 'NOTHING', point)
        yield from settle()
        baseline_path = artifacts / 'mapping-quad-upper-before.png'
        with bpy.context.temp_override(window=win, area=area, region=upper):
            bpy.ops.screen.screenshot(filepath=str(baseline_path))
        print('SCREENSHOT', baseline_path, flush=True)
        event('SPACE')
        yield from settle(8)
        modal_ids = [op.bl_idname for op in win.modal_operators]
        check('VIEW3D_OT_axismeld_hotbox' in modal_ids,
              f'2x upper-left safe area rejected its hotbox: {modal_ids!r}')
        path = artifacts / 'mapping-quad-upper-intersecting-overlaps.png'
        with bpy.context.temp_override(window=win, area=area, region=upper):
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        baseline, baseline_pixels, baseline_width = image_pixels(baseline_path)
        image, pixels, width = image_pixels(path)
        try:
            check(width == baseline_width, '2x upper-left screenshot dimensions changed')
            bx, by, bw, bh = upper_bounds
            safe_changed = sum(
                sum(abs(a-b) for a, b in zip(
                    pixels[(yy*width+xx)*4:(yy*width+xx)*4+3],
                    baseline_pixels[(yy*width+xx)*4:(yy*width+xx)*4+3])) > .12
                for yy in range(int(by), int(by+bh))
                for xx in range(int(bx), int(bx+bw)))
            check(safe_changed > 200,
                  f'2x upper-left hotbox did not render in safe bounds: '
                  f'{safe_changed} changed pixels')
            for _side, (x, y, w, h), kind in upper_obstacles:
                obstacle_changed = sum(
                    sum(abs(a-b) for a, b in zip(
                        pixels[(yy*width+xx)*4:(yy*width+xx)*4+3],
                        baseline_pixels[(yy*width+xx)*4:(yy*width+xx)*4+3])) > .12
                    for yy in range(int(y+2), int(y+h-2))
                    for xx in range(int(x+2), int(x+w-2)))
                check(obstacle_changed < max(20, int(w*h)//50),
                      f'2x upper-left hotbox changed {obstacle_changed} pixels over {kind}')
        finally:
            bpy.data.images.remove(baseline)
            bpy.data.images.remove(image)
        event('LEFTMOUSE')
        yield
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' in
              [op.bl_idname for op in win.modal_operators],
              '2x upper-left center mapping was not reachable by real input')
        event('SPACE', 'RELEASE')
        yield from settle()
        check(not win.modal_operators and len(observed) == count and
              len(settings_observed) == setting_count,
              '2x upper-left overlap probe leaked modal or dispatch state')
        print('MAPPING_QUAD_UPPER_OVERLAP', 'window', upper_window, 'safe', upper_bounds,
              'obstacles', upper_obstacles, 'real-center-input modal=[]', flush=True)

    def visible_dpi_change_cancel():
        check(layout_probe == 'standard', 'DPI change probe requires standard layout')
        space = area.spaces.active
        initial_visibility = space.show_region_ui
        initial_scale = bpy.context.preferences.view.ui_scale
        with bpy.context.temp_override(window=win, area=area, region=region):
            space.show_region_ui = True
        area.tag_redraw()
        yield from settle(16)
        ui_region = next(candidate for candidate in area.regions
                         if candidate.type == 'UI' and candidate.width > 1)
        before_rect = (ui_region.x, ui_region.y, ui_region.width, ui_region.height)
        reset_settings()
        before = settings()['center_buttons']
        count, setting_count = len(observed), len(settings_observed)
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event('SPACE')
        yield from settle(8)
        check('VIEW3D_OT_axismeld_hotbox' in
              [op.bl_idname for op in win.modal_operators],
              'DPI change probe did not start a hotbox session')
        unchanged_point = tuple(position)
        bpy.context.preferences.view.ui_scale = 1.2
        area.tag_redraw()
        yield from settle(16)
        ui_region = next(candidate for candidate in area.regions
                         if candidate.type == 'UI' and candidate.width > 1)
        after_rect = (ui_region.x, ui_region.y, ui_region.width, ui_region.height)
        check(after_rect != before_rect and after_rect[2] != before_rect[2],
              f'UI scale input did not resize the visible sidebar: '
              f'{before_rect!r} -> {after_rect!r}')
        event('MOUSEMOVE', 'NOTHING', unchanged_point)
        yield from settle()
        check(tuple(position) == unchanged_point and
              'VIEW3D_OT_axismeld_hotbox' not in
              [op.bl_idname for op in win.modal_operators],
              'DPI change did not cancel at the original pointer')
        event('SPACE', 'RELEASE')
        yield from settle()
        check(not win.modal_operators and len(observed) == count and
              len(settings_observed) == setting_count and
              settings()['center_buttons'] == before,
              'DPI change leaked modal or outcome state')
        for key, expected_tool in (
                ('W', 'builtin.move'), ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
            yield from press_tool(key, expected_tool)
        bpy.context.preferences.view.ui_scale = initial_scale
        with bpy.context.temp_override(window=win, area=area, region=region):
            space.show_region_ui = initial_visibility
        area.tag_redraw()
        yield from settle(16)
        print('MAPPING_DPI_CHANGE_CANCEL', 'point', unchanged_point,
              'before', before_rect, 'after', after_rect, 'release-modal=[] WER', flush=True)

    feedback_probe = os.environ.get('AXISMELD_TEST_CASCADE_FEEDBACK')
    if feedback_probe:
        check(layout_probe == 'standard', 'feedback probe requires its standard-view fixture')
        reset_settings()
        if feedback_probe in {'opacity', 'separator'}:
            theme = bpy.context.preferences.themes[0].user_interface
            theme.wcol_menu.inner = (.20, .20, .20, 1)
            theme.wcol_menu_back.inner = (.8, .12, .04, .2)
            theme.wcol_menu_item.inner = (.1, .1, .1, 0)
            theme.wcol_menu_item.text = (.9, .9, .9)
            theme.wcol_menu_item.inner_sel = (.05, .2, .9, 1)
            hotbox_runtime.reload_settings(bpy.context, session={
                'schema_version': 1, 'settings': {'transparency': 0}})
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('SPACE')
            yield from settle(8)
            primary_path = screenshot('feedback-primary.png')
            event('RIGHTMOUSE')
            yield from settle(8)
            views = ellipse_page(center, ['Perspective View', 'Right View', 'Bottom View',
                                         'Front View', 'Back View', 'Top View', 'Left View'],
                                 lambda label: blf.dimensions(0, label)[0] / scale,
                                 bounds, scale, views=True)
            secondary_path = screenshot('feedback-secondary-grey.png')

            def background_sample(path, rect):
                image, pixels, width = image_pixels(path)
                try:
                    x, y, w, _h = rect
                    samples = [pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                               for yy in range(int(y+4*scale), int(y+7*scale))
                               for xx in range(int(x+w/2-2*scale), int(x+w/2+2*scale))]
                    return tuple(sum(s[c] for s in samples)/len(samples) for c in range(3))
                finally:
                    bpy.data.images.remove(image)

            opaque_primary = background_sample(primary_path, control)
            event('RIGHTMOUSE', 'RELEASE')
            yield from close_box()
            # Reference the actual native widget at full theme alpha (same display transform).
            theme.wcol_menu_back.inner = (.8, .12, .04, 1)
            owner, buttons, page = yield from open_mapping(0)
            yield from move(page['items'][0])
            reference = background_sample(screenshot('opacity-native-reference.png'), page['items'][1])
            yield from move(page['items'][1])
            hover_reference = background_sample(screenshot('opacity-native-hover-reference.png'),
                                                page['items'][1])
            yield from close_box()
            theme.wcol_menu_back.inner = (.8, .12, .04, .2)
            translucent_primaries = {}
            for transparency in (() if feedback_probe == 'separator' else (0, 25, 75, 100)):
                hotbox_runtime.reload_settings(bpy.context, session={
                    'schema_version': 1, 'settings': {'transparency': transparency}})
                event('MOUSEMOVE', 'NOTHING', (cx, cy))
                event('SPACE')
                yield from settle(8)
                primary_path = screenshot(f'opacity-primary-{transparency}.png')
                check_labels(primary_path, {'items': [control]}, ['Hotbox Controls'],
                             f'root transparency {transparency}')
                primary = background_sample(primary_path, control)
                if transparency in {25, 75}:
                    translucent_primaries[transparency] = primary
                if transparency == 100:
                    # Alpha blending is independently checked from opaque and clear captures.
                    for amount, rendered in translucent_primaries.items():
                        alpha = amount/100
                        expected = tuple(a*(1-alpha) + b*alpha for a, b in zip(opaque_primary, primary))
                        check(max(abs(a-b) for a, b in zip(rendered, expected)) < .025,
                              f'primary transparency is not {amount} percent while foreground remains visible')
                event('RIGHTMOUSE')
                yield from settle(8)
                path = screenshot(f'opacity-secondary-{transparency}.png')
                for label, rect in (('view', views['items'][0]), ('entry', views['items'][8])):
                    color = background_sample(path, rect)
                    print('OPAQUE_THEME_SAMPLE', transparency, label, color, flush=True)
                    check(max(abs(a-b) for a, b in zip(color, reference)) < .025,
                          f'{label} must use opaque native theme, independent of root transparency')
                yield from move(views['items'][0])
                color = background_sample(screenshot(f'opacity-hover-{transparency}.png'),
                                          views['items'][0])
                # Compare native hover, not the deliberately different blue selected color.
                check(max(abs(a-b) for a, b in zip(color, hover_reference)) < .025,
                      f'marking hover must match native menu hover, got {color!r}')
                event('MOUSEMOVE', 'NOTHING', (cx, cy))
                yield from settle()
                event('RIGHTMOUSE', 'RELEASE')
                yield from close_box()
                owner, buttons, page = yield from open_mapping(0)
                event('MOUSEMOVE', 'NOTHING', midpoint(page['items'][0]))
                yield from settle()
                path = screenshot(f'opacity-cascade-{transparency}.png')
                # Retained ancestors may be geometrically covered; use visible leaf background.
                color = background_sample(path, page['items'][1])
                check(max(abs(a-b) for a, b in zip(color, reference)) < .025,
                      'deep native menu must be opaque even when theme alpha is low')
                yield from close_box()
            check(tuple(theme.wcol_menu_back.inner)[3] < .21,
                  'opaque overlay mutated the global menu theme alpha')
            hotbox_runtime.reload_settings(bpy.context, session={
                'schema_version': 1, 'settings': {'center_buttons': {'LEFTMOUSE': 'pane.panels'}}})
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('SPACE')
            yield from settle()
            event('LEFTMOUSE')
            yield from settle()
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            panels = catalog_layout(center, 'pane.panels', bounds, scale)
            path = screenshot('opacity-native-separator.png')
            image, pixels, width = image_pixels(path)
            try:
                x, y, w, h = next(rect for node, rect in zip(panels['nodes'], panels['items'])
                                    if node['kind'] == 'separator' and not node['label'])
                line_green = max(pixels[(yy*width+xx)*4+1]
                                 for yy in range(int(y+h/2-2*scale), int(y+h/2+2*scale))
                                 for xx in range(int(x+w/2-10*scale), int(x+w/2+10*scale)))
                check(line_green > reference[1]+.05,
                      'native separator lost its visible line and became an empty button')
            finally:
                bpy.data.images.remove(image)
            yield from close_box()
        else:
            check(feedback_probe == 'drag', 'unknown feedback probe')
            owner, buttons = yield from open_buttons()
            controls = extension_page[0]['items']
            yield from move(owner)
            event('LEFTMOUSE')
            yield from settle()
            # Continuous held motion deliberately crosses a retained, unrelated hotbox title.
            # Do not teleport straight to the child: that hid the original input-stealing bug.
            start = midpoint(owner)
            for target in (midpoint(next(item for index,item in enumerate(controls)
                                             if item is not None and item != owner)), midpoint(buttons['items'][0])):
                for step in range(1, 17):
                    point = tuple(a+(b-a)*step/16 for a, b in zip(start, target))
                    event('MOUSEMOVE', 'NOTHING', point)
                    yield
                start = target
            yield from settle()
            page = native_page(buttons['items'][0], MAPPING_LABELS, mapping_measure, bounds, scale)
            target = midpoint(page['items'][0])
            for step in range(1, 17):
                event('MOUSEMOVE', 'NOTHING', tuple(a+(b-a)*step/16 for a, b in zip(start, target)))
                yield
            screenshot('feedback-cascade-held.png')
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            check(settings()['center_buttons']['LEFTMOUSE'] is None and
                  len(settings_observed) == 1 and
                  settings_observed[0][:2] == ('center.LEFTMOUSE', 'none') and not observed,
                  f'crossing retained hotbox stole held cascade selection: {settings_observed!r}')
            yield from close_box()
            for key, tool in (('W', 'builtin.move'), ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
                yield from press_tool(key, tool)
        print('AXISMELD_CASCADE_FEEDBACK_PASS', feedback_probe, flush=True)
        print('AXISMELD_HOTBOX_MAPPING_LISTS_PASS', flush=True)
        return

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
            separated = (bx >= ox+ow-.1*scale or ox >= bx+bw-.1*scale or
                         by >= oy+oh-.1*scale or oy >= by+bh-.1*scale)
            check(separated, 'Center Mouse Buttons owner and submenu overlap')
        finally:
            bpy.data.images.remove(image)
        yield from click(buttons['items'][0])
        page = native_page(buttons['items'][0], MAPPING_LABELS, mapping_measure, bounds, scale)
        check(page['capacity'] == 13 and page['previous'] is None and page['next'] is None,
              'standard mapping list must show all 13 choices without pagination')
        normal_path = screenshot('mapping-standard-left-full.png')
        check_native_page(normal_path, page, 'standard full mapping list')
        check_radio_image(normal_path, page['items'], 1, scale)
        yield from move(page['items'][9])
        hover_path = screenshot('mapping-standard-left-hover.png')
        check_radio_image(hover_path, page['items'], 1, scale)
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
        check_radio_image(screenshot('radio-mapping-right-reloaded.png'), _page['items'], 9, scale)
        check(settings()['center_buttons']['RIGHTMOUSE'] == 'pane.shading',
              'reopened nested mapping lost persisted Right Mouse setting')
        yield from close_box()

        for button_index, selected_index in ((0, 0), (1, 4)):
            _owner, _buttons, _page = yield from open_mapping(button_index)
            check_radio_image(screenshot(f'radio-mapping-{button_index}-reloaded.png'),
                              _page['items'], selected_index, scale)
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
        yield from visible_region_change_cancel('show_region_toolbar', 'TOOLS')
        yield from visible_region_change_cancel('show_region_ui', 'UI')
        yield from visible_dpi_change_cancel()
        check(not observed, 'mapping-only suite reached the command dispatcher')
        print('PASS standard mappings: native blocks, all labels, hover, no drift, releases and W/E/R',
              flush=True)
    else:
        if layout_probe == 'quad':
            yield from quad_upper_overlap_probe()
        held_reopen_indices = (1, 1) if layout_probe == 'quad' else (2, 3)
        yield from held_leaf_cancel('previous', 'space-first', held_reopen_indices[0])
        yield from held_leaf_cancel('next', 'esc', held_reopen_indices[1])

        selected_indices = (11, 12, 9)
        for button_index, selected_index in enumerate(selected_indices):
            opener = MOUSE_BUTTONS[(button_index+1) % len(MOUSE_BUTTONS)]
            reset_settings(opener)
            _owner, buttons, page = yield from open_mapping(button_index)
            check(page['capacity'] == 13 and all(page['items']) and
                  page['previous'] is None and page['next'] is None,
                  f'{layout_probe} mapping must expose all 13 choices without navigation')
            path = screenshot(f'mapping-{layout_probe}-{button_index}-complete.png')
            check_native_page(path, page, f'{layout_probe} all 13 mapping choices')
            before = settings()['center_buttons']
            count, setting_count = len(observed), len(settings_observed)
            distance = region.data.view_distance
            yield from move(page['items'][selected_index])
            for kind in ('WHEELDOWNMOUSE', 'WHEELUPMOUSE'):
                for _ in range(20): event(kind)
                yield from settle()
                check_native_page(screenshot(f'mapping-{layout_probe}-{button_index}-{kind}.png'),
                                  page, f'{layout_probe} wheel preserves complete rows')
            check(settings()['center_buttons'] == before and len(observed) == count and
                  len(settings_observed) == setting_count and region.data.view_distance == distance,
                  'wheel changed mapping, dispatched a command or zoomed the source view')
            # A real leaf press waits for its owning release, even after another
            # mouse button releases over the same complete list.
            event('LEFTMOUSE')
            yield from settle()
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count and len(settings_observed) == setting_count,
                  'non-owner release prematurely submitted a mapping leaf')
            expected = MAPPING_VALUES[selected_index]
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            check(len(observed) == count and len(settings_observed) == setting_count+1 and
                  settings_observed[-1][:2] == (f'center.{MOUSE_BUTTONS[button_index]}', expected) and
                  settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected,
                  'owned release did not submit exactly the selected literal')
            yield from close_box()
            expected_user = {'schema_version': 1, 'settings': {'center_buttons': {
                MOUSE_BUTTONS[button_index]: expected}}}
            check(json.loads(hotbox_user.read_text(encoding='utf-8')) == expected_user,
                  f'{layout_probe} mapping did not write one-button delta JSON')
            hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {}})
            check(settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected,
                  f'{layout_probe} mapping did not reload persisted value')
            hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
                'center_buttons': {opener: 'internal.blender'}}})
            opener_button[0] = opener
            _owner, buttons, reopened = yield from open_mapping(button_index)
            check_native_page(screenshot(f'mapping-{layout_probe}-{button_index}-reopened.png'),
                              reopened, 'reopened complete mapping')
            check(settings()['center_buttons'][MOUSE_BUTTONS[button_index]] == expected,
                  'reopened mapping lost persisted value')
            # Same-session sibling selection still belongs to that sibling, never
            # to the menu that was previously open.
            sibling = (button_index+2) % 3
            yield from click(buttons['items'][sibling])
            sibling_page = native_page(buttons['items'][sibling], MAPPING_LABELS,
                                       mapping_measure, bounds, scale)
            count, setting_count = len(observed), len(settings_observed)
            yield from click(sibling_page['items'][0])
            check(len(observed) == count and len(settings_observed) == setting_count+1 and
                  settings_observed[-1][:2] == (f'center.{MOUSE_BUTTONS[sibling]}', 'none') and
                  settings()['center_buttons'][MOUSE_BUTTONS[sibling]] is None,
                  'sibling menu submitted to the previous owner')
            yield from close_box()
        check(not observed, f'{layout_probe} mapping navigation reached command dispatcher')
        print('PASS', layout_probe,
              'all 13 mapping literals, wheel consumption, owner releases, persistence and siblings',
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
    native_fixture_surface((0, 0, win.width, win.height))
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
            area.spaces.active.show_region_toolbar = False
            yield from settle(8)
        elif layout_probe == 'quad':
            bpy.context.preferences.view.ui_scale = 2.0
            yield from settle(8)
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                check(bpy.ops.screen.screen_full_area() == {'FINISHED'},
                      '2x quad native-list probe could not maximize its disposable VIEW_3D')
            yield from settle(8)
            area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
            area.spaces.active.show_region_toolbar = True
            area.spaces.active.show_region_ui = True
            area.spaces.active.show_region_header = False
            area.spaces.active.show_region_tool_header = True
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
            check(430 <= logical_width < 500 and 200 <= logical_height < 260,
                  f'2x quad probe outside bounded dimensions: {logical_width}x{logical_height}')
        print('NATIVE_LIST_LAYOUT', layout_probe, 'scale', scale, 'logical', logical_width,
              logical_height, 'physical', region.width, region.height, 'origin', region.x, region.y,
              flush=True)
        print('NATIVE_LIST_INPUT', layout_probe,
              'SPACE press -> center RIGHTMOUSE center.controls -> LEFTMOUSE parent/leaf',
              flush=True)
        cx, cy = region.x+region.width/2, region.y+region.height/2
        window_bounds, bounds, visible_obstacles = observed_visible_bounds(area, region)
        print('NATIVE_LIST_VISIBLE_BOUNDS', layout_probe, 'window', window_bounds, 'safe', bounds,
              'obstacles', visible_obstacles, flush=True)
        if layout_probe == 'narrow':
            check(any(kind == 'TOOL_HEADER' for _side, _rect, kind in visible_obstacles),
                  'narrow native-list probe requires its real visible Tool Header obstacle')
        else:
            obstacle_kinds = {kind for _side, _rect, kind in visible_obstacles}
            check(obstacle_kinds == {'TOOLS'} and bounds[0] > window_bounds[0],
                  f'2x lower-left native-list WINDOW did not isolate its toolbar: '
                  f'{visible_obstacles!r}')
            check('TOOL_HEADER' not in obstacle_kinds and 'UI' not in obstacle_kinds,
                  f'2x lower-left native-list WINDOW was clipped by a non-intersecting sibling: '
                  f'{visible_obstacles!r}')
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        def measure(label):
            return blf.dimensions(0, label)[0] / scale + 20 + (
                20 if label in CONTROL_STYLE_LABELS + TRANSPARENCY_LABELS else 0)
        center_width = (measure('AxisMeld') + 40)*scale
        center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)
        control_labels = CONTROL_LABELS

        def open_list(index, labels):
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('SPACE')
            yield from settle(8)
            event('RIGHTMOUSE')
            yield from settle()
            event('RIGHTMOUSE', 'RELEASE')
            yield from settle()
            controls_page = controls_layout(center, measure, bounds, scale)
            check(all(controls_page['items']), 'Controls omitted a fixed row')
            owner = controls_page['items'][index]
            if index in (7, 8):
                # These active checkboxes now live directly in Controls.
                return center, [owner]
            yield from click(owner)
            choices = native_list(owner, labels, measure, bounds, scale)
            return owner, choices[1:] if index == 0 else choices

        cases = (
            ('rows-common', 7, ('Show Common Menus',), (('common', ['pane', 'modeling']),)),
            ('rows-pane', 8, ('Show Pane Specific Menus',), (('pane', ['common', 'modeling']),)),
            ('rows-modeling', 0, MODELING_LABELS, (('modeling', ['common', 'pane']),)),
            ('transparency', 10, TRANSPARENCY_LABELS,
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
                if controls_index == 0:
                    labels = MODELING_LABELS[1:]
                bx, by, bw, bh = bounds
                check(len(choices) == len(labels) and all(
                    x >= bx and y >= by and x+w <= bx+bw and y+h <= by+bh
                    for x, y, w, h in choices),
                    f'{layout_probe} {name} did not expose every list row inside visible bounds')
                for choice in choices:
                    x, y, w, h = choice
                    for _side, obstacle, kind in visible_obstacles:
                        ox, oy, ow, oh = obstacle
                        check(x+w <= ox or ox+ow <= x or y+h <= oy or oy+oh <= y,
                              f'{layout_probe} {name} row {choice!r} overlaps visible '
                              f'{kind} {obstacle!r}')
                ox, oy, ow, oh = owner
                list_left = min(r[0] for r in choices)
                list_right = max(r[0]+r[2] for r in choices)
                list_bottom = min(r[1] for r in choices)
                list_top = max(r[1]+r[3] for r in choices)
                check(list_left >= ox+ow-.1*scale or ox >= list_right-.1*scale or
                      list_bottom >= oy+oh-.1*scale or oy >= list_top-.1*scale,
                      f'{layout_probe} {name} owner and list overlap')
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
                if name.startswith('rows'):
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
        window_bounds, bounds, visible_obstacles = observed_visible_bounds(area, region)
        print('NATIVE_STYLE_VISIBLE_BOUNDS', requested_scale, 'window', window_bounds,
              'safe', bounds, 'obstacles', visible_obstacles, flush=True)
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        def measure(label):
            return blf.dimensions(0, label)[0] / scale + 20 + (
                20 if label in CONTROL_STYLE_LABELS + TRANSPARENCY_LABELS else 0)
        center_width = (measure('AxisMeld') + 40)*scale
        center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)
        cases = (
            ('style-views', None, STYLE_LABELS, 1),
            ('style-controls', 11, CONTROL_STYLE_LABELS, 1),
            ('rows-controls', 0, MODELING_LABELS, 1),
            ('transparency-controls', 10, TRANSPARENCY_LABELS, 3),
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
                ring = ellipse_page(center, [],
                                    lambda label: blf.dimensions(0, label)[0] / scale,
                                    bounds, scale, views=True)
                list_anchor = ring['items'][8]
                yield from move(list_anchor)
            else:
                control_width = (measure('Hotbox Controls') + 40)*scale
                control = (center[0]+center[2]+83.6*scale, cy-19*scale,
                           control_width, 38*scale)
                yield from click(control)
                ring = controls_layout(control, measure, bounds, scale)
                check(all(ring['items']), 'Controls omitted a fixed row')
                native_siblings = tuple(item for item in ring['items'] if item is not None)
                list_anchor = ring['items'][controls_index]
                yield from click(list_anchor)
            choices = native_list(list_anchor, labels,
                                  lambda label: blf.dimensions(0, label)[0]/scale + (20 if label else 0) +
                                  (20 if label and entry in {'style-controls', 'transparency-controls'} else 0),
                                  bounds, scale,
                                  marking_origin=(cx, cy) if controls_index is None else None)
            visible_rects = [rect for rect in (*ring['items'], ring['back'], *choices)
                             if rect is not None]
            surface = ring.get('bounds', bounds)
            if any(x < bounds[0] or y < bounds[1] or x+w > bounds[0]+bounds[2] or
                   y+h > bounds[1]+bounds[3] for x,y,w,h in visible_rects):
                surface = (0, 0, win.width, win.height)
            bx, by, bw, bh = surface
            obstacles = visible_obstacles if tuple(surface) == tuple(bounds) else []
            for rect in visible_rects:
                x, y, w, h = rect
                check(x >= bx and y >= by and x+w <= bx+bw and y+h <= by+bh,
                      f'{entry} {requested_scale}x rect {rect!r} escaped visible bounds '
                      f'{bounds!r}')
                for _side, obstacle, kind in obstacles:
                    ox, oy, ow, oh = obstacle
                    check(x+w <= ox or ox+ow <= x or y+h <= oy or oy+oh <= y,
                          f'{entry} {requested_scale}x rect {rect!r} overlaps visible '
                          f'{kind} {obstacle!r}')
            normal_path = screenshot(f'native-style-{entry}-{requested_scale}-normal.png')
            initial_radio = 0 if entry.startswith('style') else 1
            if entry == 'transparency-controls':
                check_radio_image(normal_path, choices[:3] if entry.startswith('style') else choices, initial_radio, scale)
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
                if not label:
                    check(abs(lh-6*scale)<.1*scale, 'Controls Style separator height changed')
                    continue
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
            left = min(r[0] for r in choices)
            right = max(r[0]+r[2] for r in choices)
            bottom = min(r[1] for r in choices)
            top = max(r[1]+r[3] for r in choices)
            anchors = ring.get('columns', ()) if native_siblings else ()
            anchors = anchors or [list_anchor]
            al = min(r[0] for r in anchors); ar = max(r[0]+r[2] for r in anchors)
            ab = min(r[1] for r in anchors); at = max(r[1]+r[3] for r in anchors)
            check(min(abs(left-ar), abs(al-right), abs(bottom-at), abs(ab-top)) < .1*scale,
                  'native cascade does not touch its parent list block')
            if native_siblings:
                check(ring['back'] is None, 'Native Controls must not invent a ring Back item')
                # The parent is now one native list. Verify actual visible row bounds
                # stay aligned and contiguous, including its 6px separators.
                ordered = sorted(native_siblings, key=lambda item: (item[0], -item[1]))
                for upper, lower in zip(ordered, ordered[1:]):
                    if abs(upper[0]-lower[0]) > .1*scale: continue
                    check(abs(upper[0]-lower[0])<.1*scale and
                          abs(upper[1]-lower[1]-lower[3])<.1*scale,
                          f'{entry} native Controls parent rows have a gap or misalignment')
                # Sample the quiet right gutter of a visible unrelated parent row.
                candidates = [r for r in ordered if r != list_anchor and r[3] >= 24*scale]
                check(candidates, 'Retained native parent has no visible unrelated row')
                px, py, pw, ph = candidates[0]
                parent_background = [pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                                     for yy in range(int(py+2*scale), int(py+4*scale))
                                     for xx in range(int(px+pw-3*scale), int(px+pw-scale))]
                check(parent_background and all(r>.7 and g<.2 and b<.1
                                                for r,g,b in parent_background),
                      f'{entry} retained Controls list lost its continuous native theme')
            bpy.data.images.remove(image)
            yield from move(choices[selected_index])
            hover_path = screenshot(f'native-style-{entry}-{requested_scale}-hover.png')
            if entry == 'transparency-controls':
                check_radio_image(hover_path, choices[:3] if entry.startswith('style') else choices, initial_radio, scale)
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
            if entry == 'transparency-controls':
                # Settings refresh clears the submenu path but retains the parent hotbox.
                # Reopen without another Space press and verify the newly selected glyph.
                yield from click(control)
                yield from click(list_anchor)
                check_radio_image(screenshot(f'radio-{entry}-{requested_scale}-after-click.png'),
                                  choices[:3] if entry.startswith('style') else choices, selected_index, scale)
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

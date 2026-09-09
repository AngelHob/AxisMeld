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
    yield from settle(8)
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    position = [cx, cy]

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
    # Common row is at center + 64 logical pixels. A broad strip must visibly change;
    # the old fixed four labels never draw there. Compare real rendered pixels.
    before = bpy.data.images.load(str(before_path), check_existing=False)
    after = bpy.data.images.load(str(path), check_existing=False)
    scale = bpy.context.preferences.system.ui_scale
    a, b = list(before.pixels), list(after.pixels)
    width = after.size[0]
    changed = 0
    for y in range(int(cy + 55 * scale), int(cy + 73 * scale)):
        for x in range(int(cx - 170 * scale), int(cx + 170 * scale)):
            i = (y * width + x) * 4
            changed += sum(abs(a[i + k] - b[i + k]) for k in range(3)) > .08
    failures = []
    if changed < 1000 * scale * scale:
        failures.append(f'Space main Common directory missing: changed pixels={changed}')
    bpy.data.images.remove(before)
    bpy.data.images.remove(after)
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
        event('RIGHTMOUSE')
        yield
        event('MOUSEMOVE', 'NOTHING', cx + dx * scale, cy + dy * scale)
        yield
        event('RIGHTMOUSE', 'RELEASE')
        yield from close_box()
        check(len(observed) == count and current_pose() == original, 'NE/deadzone executed')
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

    # Independent measured coordinates for the normal centered row and right-hand popup.
    # This does not import/reimplement the production layout or query test-only native state.
    blf.size(0, 12 * scale)
    def label_width(label):
        return blf.dimensions(0, label)[0] / scale
    def row_title(labels, index, dy):
        widths = [label_width(label) + 24 for label in labels]
        start = cx / scale - (sum(widths) + 4 * (len(widths)-1)) / 2
        x = start + sum(widths[:index]) + 4 * index
        return (x * scale, cy + (dy-14) * scale, widths[index] * scale, 28 * scale)
    def midpoint(rect):
        x, y, w, h = rect
        return x+w/2, y+h/2
    def popup(anchor, labels):
        x, y, w, h = anchor
        width = (max(label_width(label) for label in labels) + 24) * scale
        px = x+w+4*scale
        if px+width > region.x+region.width-8*scale:
            px = x-4*scale-width
        px = max(region.x+8*scale, min(px, region.x+region.width-8*scale-width))
        height = len(labels)*28*scale
        bottom = max(region.y+8*scale, min(y+h-height, region.y+region.height-8*scale-height))
        return [(px, bottom+height-(i+1)*28*scale, width, 28*scale) for i in range(len(labels))]
    pane_labels = ['View', 'Shading', 'Lighting', 'Show', 'Renderer', 'Panels']
    shading = row_title(pane_labels, 1, 32)
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
                          ('disabled', midpoint(row_title(common_labels, 0, 64)))):
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
    yield from click(midpoint(row_title(common_labels, 0, 64)))
    screenshot('menus-disabled-file-reason.png')
    yield from close_box()
    check(len(observed) == count and len([r for r in area.regions if r.type == 'WINDOW']) == 1,
          'disabled title executed or became tap')

    # Close-before mode command: no stale draw pointer and no residual Space playback.
    select = row_title(common_labels, 3, 64)
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

    panels = row_title(pane_labels, 5, 32)
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
    center = (cx-(label_width('AxisMeld')+24)*scale/2, cy-14*scale,
              (label_width('AxisMeld')+24)*scale, 28*scale)
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
    yield from move(midpoint(root_items[1]))
    yield from settle()
    screenshot('menus-center-root-duplicate-views.png')
    view_items = popup(root_items[1], ['Perspective View', 'Side View', 'Bottom View', 'Front View',
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

    # The central marking menu's appended Style list wins over the directional sector.
    yield from open_box()
    event('RIGHTMOUSE')
    yield
    central_list = popup(center, ['Perspective View', 'Side View', 'Bottom View', 'Front View',
                                  'Back View', 'Top View', 'Left View', '', 'Hotbox Style'])
    yield from move(midpoint(central_list[8]))
    central_styles = popup(central_list[8], ['Zones and Menu Rows', 'Zones Only', 'Center Zone Only'])
    yield from move(midpoint(central_styles[1]))
    screenshot('menus-marking-style-candidate.png')
    count = len(observed)
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['style'] == 'zones' and
              len(observed) == count, 'marking Style list must win over direction inference')
    yield from close_box()
    reset_hotbox_settings()

    yield from open_box()
    event('RIGHTMOUSE')
    yield
    yield from move(midpoint(central_list[8]))
    count = len(observed)
    event('RIGHTMOUSE', 'RELEASE')
    yield from settle()
    check(len(observed) == count, 'Style parent release executed a directional command')
    yield from click(midpoint(central_styles[1]))
    with bpy.context.temp_override(window=win, area=area, region=region):
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['style'] == 'zones' and
              len(observed) == count, 'marking Style parent must support click browsing')
    yield from close_box()
    reset_hotbox_settings()

    # Actual settings leaves use the native bridge and rebuild the same live hotbox.
    control_width = (label_width('Hotbox Controls')+24)*scale
    controls = (center[0]+center[2]+4*scale, cy-14*scale, control_width, 28*scale)
    control_items = popup(controls, ['Menu Rows', 'Hotbox Style', 'Transparency',
                                     'Center Mouse Buttons'])
    yield from open_box()
    yield from click(midpoint(controls))
    yield from move(midpoint(control_items[1]))
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
    mapping_items = popup(button_items[2], mapping_labels)
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
    recent_width = (label_width('Recent Commands')+24)*scale
    recent_rect = (center[0]-4*scale-recent_width, cy-14*scale, recent_width, 28*scale)
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
        blf.size(0, 12*scale)
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
    blf.size(0, 12*scale)
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
    # First Modeling page is hand calculated from measured public labels, with two 24px controls.
    modeling_labels = ['Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display', 'Curves', 'Surfaces',
                       'Deform', 'UV', 'Generate']
    room = region.width/scale - 16 - 56
    used = 0
    for label in modeling_labels:
        width = label_width(label)+24
        if used+width > room:
            break
        used += width+4
    total = used-4+56
    next_point = (cx+(total/2-12)*scale, cy-32*scale)
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
    center = (cx-(label_width('AxisMeld')+24)*scale/2, cy-14*scale,
              (label_width('AxisMeld')+24)*scale, 28*scale)
    capacity = int((region.height/scale-16)/28)-2
    def overflow_page(anchor, labels, first=0):
        labels = ['<']+labels[first:first+capacity]+['>']
        return popup(anchor, labels)
    parent_labels = ['Nested Entries']+[f'Parent {i:02}' for i in range(17)]
    parent_rects = overflow_page(center, parent_labels)
    child_anchor = parent_rects[1]
    yield from move(midpoint(child_anchor))
    child_labels = [f'Child {i:02}' for i in range(18)]
    child_rects = overflow_page(child_anchor, child_labels)
    screenshot('menus-small-parent-child-first.png')
    # Wheel over only the child owner; parent position must still accept its same title.
    for _ in range(18-capacity):
        yield from move(midpoint(child_rects[-1]))
        event('WHEELDOWNMOUSE')
        yield
        event('WHEELDOWNMOUSE', 'RELEASE')
        yield
    yield from settle()
    screenshot('menus-small-child-scrolled.png')
    yield from move(midpoint(child_anchor))
    screenshot('menus-small-return-parent.png')
    # Scroll ancestor: deeper popup closes before its anchor moves.
    yield from move(midpoint(parent_rects[-1]))
    event('WHEELDOWNMOUSE')
    yield
    event('WHEELDOWNMOUSE', 'RELEASE')
    yield from settle()
    screenshot('menus-small-ancestor-scrolled.png')
    count = len(observed)
    yield from click(midpoint(child_rects[-2]))
    check(len(observed) == count, 'scrolling ancestor left executable deeper child rectangles')
    # The blank release above cancels browsing; explicitly reopen the same owner.
    yield from click((cx, cy), 'RIGHTMOUSE')
    yield from move(midpoint(parent_rects[-1]))
    event('WHEELUPMOUSE')
    yield
    event('WHEELUPMOUSE', 'RELEASE')
    yield from settle()
    yield from move(midpoint(child_anchor))
    yield from click(midpoint(child_rects[-2]))
    check(len(observed) == count+1 and observed[-1][0] == 'view.top',
          'independent child scroll offset did not survive ancestor navigation')
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
                                      factor=.5 if dimension == 'width' else .25)
        yield from settle(8)
        candidates = [a for a in win.screen.areas if a.type == 'VIEW_3D']
        area = min(candidates, key=lambda a: a.width if dimension == 'width' else a.height)
        region = next(r for r in area.regions if r.type == 'WINDOW')
        check((region.width/scale < 480 and region.height/scale >= 320) if dimension == 'width'
              else (region.height/scale < 320 and region.width/scale >= 480),
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

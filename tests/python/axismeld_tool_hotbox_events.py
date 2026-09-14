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
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles

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
    showing=False
    display_generation=0
    observed_roots={}
    theme=bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu,theme.wcol_menu_back,theme.wcol_menu_item):
        colors.inner=(.8,.04,.65,1)
        colors.inner_sel=(.8,.04,.65,1)

    def event(kind, value='PRESS', point=None, **kwargs):
        nonlocal showing,display_generation
        if kind=='LEFTMOUSE':
            showing=value=='PRESS'
            if showing:display_generation+=1
        elif kind=='ESC':showing=False
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
        if showing and tool_name in {'select','move','rotate','scale'}:
            key=(display_generation,tool_name)
            if key in observed_roots:
                return observed_roots[key]
            path=root/'actual-tool-input-targets.png'
            with override():bpy.ops.screen.screenshot(filepath=str(path))
            picture=bpy.data.images.load(str(path),check_existing=False)
            try:
                width,height=picture.size
                pixels=np.asarray(picture.pixels[:],dtype=np.float32).reshape(height,width,4).copy()
            finally:bpy.data.images.remove(picture)
            observed=observed_radial_rectangles(pixels,bpy.context.preferences.system.ui_scale,
                {'N','NW','NE','W','E','SW','SE','S'})
            observed_roots[key]={d:(r[0],r[1],r[2]-r[0],r[3]-r[1]) for d,r in observed['rects'].items()}
            return observed_roots[key]
        # Coordinates only; independent native tests assert direction, spacing and hit ownership.
        from axismeld.hotbox_catalog import default_catalog
        def walk(nodes):
            for n in nodes:
                yield n
                yield from walk(n['children'])
        nodes = next(n for n in walk(default_catalog()) if n['id'] == 'tools.' + tool_name)['children']
        scale = bpy.context.preferences.system.ui_scale
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        widths = {n['id']: max(84, blf.dimensions(0, n['label'])[0] / scale + 20 +
                  (60 if n['kind'] == 'menu' else 16)) for n in nodes}
        # Views owns the spacing reference: title, icon, then primary-button padding.
        # Native tests compare inner edges against actual Views layouts independently.
        center_width = blf.dimensions(0, 'AxisMeld')[0] / scale + 20 + 40
        d = math.sqrt(.5)
        directions = {'N': (0, 1), 'NE': (d, d), 'E': (1, 0), 'SE': (d, -d),
                      'S': (0, -1), 'SW': (-d, -d), 'W': (-1, 0), 'NW': (-d, d)}
        for ry in (0,):
            rects = [(-center_width/2, -12, center_width, 24)]
            clear = True
            for n in nodes:
                w = widths[n['id']]
                nx, ny = directions[n['direction']]
                side = (w + center_width)/2 + 8
                x = (0 if nx == 0 else math.copysign(side - (0 if ny == 0 else 16), nx)) - w/2
                y = (0 if ny == 0 else math.copysign(32 * (2 if nx == 0 else 1), ny)) - 12
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

    def stroke(name, direction=None, *, origin=None, disabled=False, capture=None, beyond=0):
        """One owned mouse stroke; deliberately never send another tool-key press."""
        point = (cx, cy) if origin is None else origin
        event('MOUSEMOVE', 'NOTHING', point)
        event('LEFTMOUSE')
        yield from settle()
        if capture:
            screenshot(capture)
        if disabled:
            entry = middle(ring(name, point)['N'])
            event('MOUSEMOVE', 'NOTHING', entry)
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', middle(ring(name + '.symmetry', entry)['W']))
        elif direction is not None:
            rect = ring(name, point)[direction]
            target = middle(rect)
            if beyond:
                # Follow the displayed row past its horizontal edge. Diagonal rays do
                # not preserve a row when tool labels have unequal widths.
                event('MOUSEMOVE', 'NOTHING', target)
                yield from settle()
                target = (rect[0] - beyond if 'W' in direction else rect[0] + rect[2] + beyond,
                          target[1])
            event('MOUSEMOVE', 'NOTHING', target)
        yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()

    def check_armed(message):
        check(modals() == ['VIEW3D_OT_axismeld_hotbox'], message + ': ' + str(modals()))

    def repeat_strokes(key, name, slot_index=None, *, capture=False):
        # Observe real tool/orientation changes, in addition to modal ownership. A second
        # keyboard PRESS would hide the reported bug and is forbidden within this sequence.
        scale = bpy.context.preferences.system.ui_scale
        offset = min(90 * scale, region.width * .12, region.height * .12)
        first = (cx - offset, cy - offset)
        second = (cx + offset, cy + offset)
        third = (cx + offset, cy - offset)
        selected = slot_index is None

        def current():
            return tool() if selected else bpy.context.scene.transform_orientation_slots[slot_index].type

        event('MOUSEMOVE', 'NOTHING', first)
        event(key)
        yield from settle()
        yield from stroke(name, 'SW' if selected else 'NW', origin=first)
        check(current() == ('builtin.select_lasso' if selected else 'LOCAL'),
              key + ' first held-key stroke did not commit')
        yield from stroke(name, 'W', origin=second,
                          capture='rearm-' + name + '-second-stroke.png' if capture else None)
        check(current() == ('builtin.select_circle' if selected else 'GLOBAL'),
              key + ' second LMB stroke under one held key did not reopen at the new origin')
        check_armed(key + ' second mouse release must keep exactly one armed session')
        if capture:
            screenshot('rearm-' + name + '-waiting.png')

        before = current()
        event('MOUSEMOVE', 'NOTHING', middle(ring(name, second)['NW']))
        yield from settle()
        check(current() == before, key + ' unpressed motion after commit dispatched a command')
        yield from stroke(name, origin=third)
        check(current() == before, key + ' empty-center stroke committed a command')
        check_armed(key + ' empty-center release must allow another mouse stroke')
        yield from stroke(name, origin=first, disabled=True)
        check(current() == before, key + ' disabled Symmetry leaf changed state')
        check_armed(key + ' disabled leaf release must allow another mouse stroke')
        yield from stroke(name, 'NW' if selected else 'NE', origin=third)
        expected = 'builtin.select_box' if selected else 'NORMAL'
        check(current() == expected, key + ' stroke after empty/disabled releases did not reopen')
        check_armed(key + ' final mouse release must retain the held trigger')
        event(key, 'RELEASE')
        yield from settle()
        check(current() == expected, key + ' final trigger release changed the committed result')
        check(not modals(), key + ' final trigger release left ownership: ' + str(modals()))

    def repeat_cancel_paths():
        slot = bpy.context.scene.transform_orientation_slots[1]

        def arm_after_commit():
            slot.type = 'GLOBAL'
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('W')
            yield from settle()
            yield from stroke('move', 'NW')
            check(slot.type == 'LOCAL', 'pre-cancel first stroke did not commit')
            check_armed('pre-cancel first stroke must retain its held key')
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            yield from settle()

        yield from arm_after_commit()
        event('ESC')
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'Escape must end the rearmed session')
        event('ESC', 'RELEASE')
        event('W', 'RELEASE')
        yield from settle()
        check(not modals(), 'Escape in the rearmed wait left ownership: ' + str(modals()))

        for cancel in ('trigger', 'escape'):
            yield from arm_after_commit()
            event('LEFTMOUSE')
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', middle(ring('move')['W']))
            yield from settle()
            event('W' if cancel == 'trigger' else 'ESC', 'RELEASE' if cancel == 'trigger' else 'PRESS')
            yield from settle()
            event('LEFTMOUSE', 'RELEASE')
            if cancel == 'escape':
                event('W', 'RELEASE')
                event('ESC', 'RELEASE')
            yield from settle()
            check(slot.type == 'LOCAL', cancel + ' submitted the second stroke')
            check(not modals(), cancel + ' during a reopened stroke left ownership: ' + str(modals()))

        for shown in (False, True):
            yield from arm_after_commit()
            if shown:
                event('LEFTMOUSE')
                yield from settle()
                event('MOUSEMOVE', 'NOTHING', middle(ring('move')['W']))
                yield from settle()
            event('WINDOW_DEACTIVATE', 'NOTHING')
            yield from settle()
            check(slot.type == 'LOCAL', 'focus loss submitted the reopened stroke')
            check(not modals(), 'focus loss after rearming must clear without old releases')
            # The old releases may be lost outside this window. A fresh key must work
            # before we send any of them to reset the event simulator for later cases.
            event('E')
            yield from settle()
            check(tool() == 'builtin.rotate', 'fresh key after rearmed focus loss did not select tool')
            check_armed('fresh key after rearmed focus loss did not start a clean session')
            event('E', 'RELEASE')
            yield from settle()
            check(not modals(), 'fresh post-focus trigger left ownership')
            if shown:
                event('LEFTMOUSE', 'RELEASE')
            event('W', 'RELEASE')
            yield from settle()
            check(not modals(), 'late post-focus releases left ownership')

    def extended_strokes():
        scale = bpy.context.preferences.system.ui_scale
        for key, name, slot_index in (('Q', 'select', None), ('W', 'move', 1),
                                      ('E', 'rotate', 2), ('R', 'scale', 3)):
            selected = slot_index is None
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event(key)
            yield from settle()
            directions = ('SW', 'W', 'NW') if selected else ('NW', 'W', 'NE')
            expected = ('builtin.select_lasso', 'builtin.select_circle', 'builtin.select_box') if selected else (
                'LOCAL', 'GLOBAL', 'NORMAL')
            for direction, result in zip(directions, expected):
                yield from stroke(name, direction, beyond=64 * scale)
                current = tool() if selected else bpy.context.scene.transform_orientation_slots[slot_index].type
                check(current == result, key + ' outer extension of ' + direction + ' did not commit ' + result)
                check_armed(key + ' outer release must keep the held-key session')
            event('LEFTMOUSE', 'PRESS', (cx, cy))
            yield from settle()
            rect = ring(name)['W']
            target = middle(rect)
            event('MOUSEMOVE', 'NOTHING', target)
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', (rect[0] - 64 * scale, target[1]))
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            current = tool() if selected else bpy.context.scene.transform_orientation_slots[slot_index].type
            check(current == expected[-1], key + ' outer stroke returned to center still committed')
            check_armed(key + ' outer-center cancel must leave the session rearmed')
            event(key, 'RELEASE')
            yield from settle()
            check(not modals(), key + ' outer extension sequence left ownership')

    def overlap(old_key, *, old_release_first, after_stroke=False):
        slot = bpy.context.scene.transform_orientation_slots[2]
        slot.type = 'LOCAL'
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        event(old_key)
        yield from settle()
        if after_stroke:
            yield from stroke('move', 'NW')
            check_armed('completed W stroke must permit the existing E handoff')
            event('MOUSEMOVE', 'NOTHING', (cx, cy))
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

    for key, name, slot_index in (('Q', 'select', None), ('W', 'move', 1),
                                  ('E', 'rotate', 2), ('R', 'scale', 3)):
        yield from repeat_strokes(key, name, slot_index, capture=True)
    print('PASS held Q/W/E/R repeat strokes, relocated origins and empty/disabled rearming', flush=True)
    yield from repeat_cancel_paths()
    print('PASS rearmed trigger-first, Escape and lost-release focus cancellation', flush=True)
    yield from extended_strokes()
    print('PASS Q/W/E/R visible-row outer commits and return-to-origin cancellation', flush=True)

    yield from overlap('W', old_release_first=True)
    yield from overlap('W', old_release_first=False)
    yield from overlap('W', old_release_first=True, after_stroke=True)
    yield from overlap('W', old_release_first=False, after_stroke=True)

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
    # Returning through the visible blank center must retract the native submenu
    # immediately, before a new outward stroke. This is outside the old 12px circle.
    bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
    yield from open_ring('W')
    event('MOUSEMOVE', 'NOTHING', middle(ring('move')['SE']))
    yield from settle()
    scale = bpy.context.preferences.system.ui_scale
    event('MOUSEMOVE', 'NOTHING', (cx + 14*scale, cy + 14*scale))
    yield from settle(1)
    event('MOUSEMOVE', 'NOTHING', middle(ring('move')['W']))
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(bpy.context.scene.transform_orientation_slots[1].type == 'GLOBAL',
          'visual-center return failed to retract native child immediately')
    bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
    yield from open_ring('W')
    axis_rect = ring('move')['SW']
    event('MOUSEMOVE', 'NOTHING', middle(axis_rect))
    yield from settle()
    scale = bpy.context.preferences.system.ui_scale
    child = ring('move.axis', middle(axis_rect))
    screenshot('compact-tool-axis.png')
    # Maya Axis has no Blender View leaf. Exercise its existing Parent row,
    # return one level, then prove the root command really runs.
    event('MOUSEMOVE', 'NOTHING', middle(child['W']))
    yield from settle()
    north = middle(child['N'])
    event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
    yield from settle(1)
    event('MOUSEMOVE', 'NOTHING', middle(ring('move')['W']))
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(bpy.context.scene.transform_orientation_slots[1].type == 'GLOBAL',
          'child Axis return did not restore the actual root World command')
    check(not modals(), 'child Axis ring left modal')
    for key, name, slot_index in (('W', 'move', 1), ('R', 'scale', 3)):
        bpy.context.scene.transform_orientation_slots[slot_index].type = 'LOCAL'
        yield from open_ring(key)
        axis_entry = middle(ring(name)['SW'])
        event('MOUSEMOVE', 'NOTHING', axis_entry)
        yield from settle()
        axis_ring = ring(name + '.axis', axis_entry)
        custom_entry = middle(axis_ring['SW'])
        event('MOUSEMOVE', 'NOTHING', custom_entry)
        yield from settle()
        custom_ring = ring(name + '.axis.custom', custom_entry)
        event('MOUSEMOVE', 'NOTHING', middle(custom_ring['W']))
        yield from settle()
        # Return to the current visible child's blank center after an outward stroke.
        north = middle(custom_ring['N'])
        event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
        yield from settle(1)
        # Axis itself is now Maya-only and all its leaves are unavailable.
        # A second one-level return must expose the real root World command.
        event('MOUSEMOVE', 'NOTHING', middle(axis_ring['W']))
        yield from settle()
        north = middle(axis_ring['N'])
        event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
        yield from settle(1)
        event('MOUSEMOVE', 'NOTHING', middle(ring(name)['W']))
        event('LEFTMOUSE', 'RELEASE')
        event(key, 'RELEASE')
        yield from settle()
        check(bpy.context.scene.transform_orientation_slots[slot_index].type == 'GLOBAL',
              name + ' third-level then Axis center return did not restore root World')
        check(not modals(), 'third-level return left modal')
        # A hidden root return square has corners outside the real 12 px cancel disc.
        # Crossing one must keep the current Custom ring. Two subsequent visible
        # center returns must reach the root Object command; an early ancestor
        # return changes this navigation chain. Validate the geometric premise
        # against the displayed child targets before choosing the point.
        bpy.context.scene.transform_orientation_slots[slot_index].type = 'GLOBAL'
        yield from open_ring(key)
        axis_entry = middle(ring(name)['SW'])
        event('MOUSEMOVE', 'NOTHING', axis_entry)
        yield from settle()
        axis_ring = ring(name + '.axis', axis_entry)
        custom_entry = middle(axis_ring['SW'])
        event('MOUSEMOVE', 'NOTHING', custom_entry)
        yield from settle()
        custom_ring = ring(name + '.axis.custom', custom_entry)
        hidden_corners = [(cx + dx * scale, cy + dy * scale)
                          for dx, dy in ((10, 10), (-10, 10), (10, -10), (-10, -10))]
        hidden_corners = [point for point in hidden_corners
                          if math.dist(point, (cx, cy)) > 12 * scale and
                          not any(rect[0] <= point[0] < rect[0] + rect[2] and
                                  rect[1] <= point[1] < rect[1] + rect[3]
                                  for rect in custom_ring.values())]
        check(bool(hidden_corners), name + ' hidden-root corner fixture is covered by child targets')
        event('MOUSEMOVE', 'NOTHING', hidden_corners[0])
        yield from settle()
        screenshot('hidden-root-corner-' + name + '.png')
        event('MOUSEMOVE', 'NOTHING', middle(custom_ring['W']))
        yield from settle()
        north = middle(custom_ring['N'])
        event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
        yield from settle(1)
        event('MOUSEMOVE', 'NOTHING', middle(axis_ring['W']))
        yield from settle()
        north = middle(axis_ring['N'])
        event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
        yield from settle(1)
        event('MOUSEMOVE', 'NOTHING', middle(ring(name)['NW']))
        event('LEFTMOUSE', 'RELEASE')
        event(key, 'RELEASE')
        yield from settle()
        check(bpy.context.scene.transform_orientation_slots[slot_index].type == 'LOCAL',
              name + ' hidden ancestor center swallowed the active third-level ring')
        check(not modals(), 'hidden ancestor corner left modal')
    print('PASS hidden ancestor corners keep current third-level W/R ring', flush=True)
    # Child/root centers can coincide when both rings clamp inward at the corner.
    edge_origin = (region.x + 10, region.y + 10)
    bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
    event('MOUSEMOVE', 'NOTHING', edge_origin)
    event('W')
    yield from settle()
    event('LEFTMOUSE')
    yield from settle()
    edge_ring = ring('move', edge_origin)
    edge_axis_entry = middle(edge_ring['SW'])
    event('MOUSEMOVE', 'NOTHING', edge_axis_entry)
    yield from settle()
    edge_axis = ring('move.axis', edge_axis_entry)
    event('MOUSEMOVE', 'NOTHING', middle(edge_axis['W']))
    yield from settle()
    north = middle(edge_axis['N'])
    event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
    yield from settle(1)
    event('MOUSEMOVE', 'NOTHING', middle(edge_ring['W']))
    event('LEFTMOUSE', 'RELEASE')
    event('W', 'RELEASE')
    yield from settle()
    check(bpy.context.scene.transform_orientation_slots[1].type == 'GLOBAL',
          'edge-clamped child center did not return to root')
    check(not modals(), 'edge-clamped return left ownership')

    # Internal menus retain non-Maya tool settings without inserting fake rows
    # in Maya Modify. Use a real off-center LMB press so origin-return remains
    # distinct from the Space opening position.
    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_geometry_fixture import native_page, native_fixture_surface
    native_fixture_surface((0,0,win.width,win.height))

    def open_space_modify(identifier='internal.blender'):
        from axismeld.hotbox_catalog import default_catalog
        pending=list(default_catalog());nodes={}
        while pending:
            item=pending.pop();nodes[item['id']]=item;pending.extend(item['children'])
        entries=nodes[identifier]['children']
        measure=lambda label: blf.dimensions(0,label)[0]/scale+20
        center_width=(measure('AxisMeld')+40)*scale
        anchor=(cx-center_width/2,cy-19*scale,center_width,38*scale)
        bounds=(region.x,region.y,region.width,region.height)
        with override():
            hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
                'center_buttons':{'LEFTMOUSE':identifier}}})
        event('MOUSEMOVE','NOTHING',(cx,cy));event('SPACE');yield from settle()
        event('MOUSEMOVE','NOTHING',(cx+24*scale,cy));event('LEFTMOUSE');yield from settle()
        page=native_page(anchor,[n['label'] for n in entries],measure,bounds,scale,
            submenu_indices=[i for i,n in enumerate(entries) if n['kind']=='menu'])
        return anchor,entries,page,measure,bounds

    def open_space_move():
        anchor,entries,page,measure,bounds=yield from open_space_modify('internal.marking')
        move_index=next(i for i,n in enumerate(entries) if n['id']=='tools.move')
        move_entry=page['items'][move_index]
        event('MOUSEMOVE','NOTHING',middle(move_entry));yield from settle()
        return ring('move',middle(move_entry)),(cx+24*scale,cy)

    # Relocated Blender View actions remain reachable through real Space input.
    # Every tool is checked both for successful dispatch and original-press cancel.
    for name, slot_index in (('move', 1), ('rotate', 2), ('scale', 3)):
        for cancel in (False, True):
            bpy.context.scene.transform_orientation_slots[slot_index].type = 'LOCAL'
            recent_before = hotbox_runtime.recent.items()
            modify, entries, page, measure, bounds = yield from open_space_modify()
            index = next(i for i,n in enumerate(entries) if n['id']=='common.modify.view_orientations')
            parent = page['items'][index]
            event('MOUSEMOVE', 'NOTHING', middle(parent))
            yield from settle()
            children = entries[index]['children']
            # These three live orientations expose a separate native state column.
            child_page = native_page(parent, [n['label'] for n in children],
                                     lambda label: measure(label) + 20, bounds, scale)
            child_index = next(i for i,n in enumerate(children)
                               if n['command']=='orientation.' + name + '.view')
            event('MOUSEMOVE', 'NOTHING', middle(child_page['items'][child_index]))
            yield from settle()
            if cancel:
                event('MOUSEMOVE', 'NOTHING', (cx+24*scale,cy))
                yield from settle()
            event('LEFTMOUSE', 'RELEASE')
            event('SPACE', 'RELEASE')
            yield from settle()
            check(bpy.context.scene.transform_orientation_slots[slot_index].type == ('LOCAL' if cancel else 'VIEW'),
                  name + ' relocated Space View action/cancel failed')
            check(not modals(), name + ' relocated View left modal ownership')
            if cancel:
                check(hotbox_runtime.recent.items()==recent_before, 'cancelled View changed Recent')
            else:
                check(hotbox_runtime.recent.items()[0]=='orientation.' + name + '.view',
                      'successful relocated View did not enter Recent')
    print('PASS Space Blender View Orientations for Move/Rotate/Scale and original-press cancellation', flush=True)

    space_ring, _mouse_origin = yield from open_space_move()
    space_axis_entry = middle(space_ring['SW'])
    event('MOUSEMOVE', 'NOTHING', space_axis_entry)
    yield from settle()
    space_axis = ring('move.axis', space_axis_entry)
    screenshot('compact-space-tool-child.png')
    event('MOUSEMOVE', 'NOTHING', middle(space_axis['W']))
    yield from settle()
    north = middle(space_axis['N'])
    event('MOUSEMOVE', 'NOTHING', (north[0], north[1] - 64*scale))
    yield from settle(1)
    event('MOUSEMOVE', 'NOTHING', middle(space_ring['NW']))
    event('LEFTMOUSE', 'RELEASE')
    event('SPACE', 'RELEASE')
    yield from settle()
    check(bpy.context.scene.transform_orientation_slots[1].type == 'LOCAL',
          'Space tool child return did not restore root orientation command')
    check(not modals(), 'Space tool child left ownership')
    print('PASS compact child, third-level, edge-center and Space tool return', flush=True)
    for return_to_press in (False, True):
        bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
        space_ring, mouse_origin = yield from open_space_move()
        rect = space_ring['NE']
        target = middle(rect)
        event('MOUSEMOVE', 'NOTHING', target)
        yield from settle()
        event('MOUSEMOVE', 'NOTHING', (rect[0] + rect[2] + 64 * scale, target[1]))
        yield from settle()
        if return_to_press:
            # The real LMB-down was off-center within the mapped Internal button.
            check(math.dist(mouse_origin, (cx, cy)) > 12 * scale,
                  'Space origin-cancel fixture must use a distinct LMB press position')
            event('MOUSEMOVE', 'NOTHING', mouse_origin)
            yield from settle()
        screenshot('space-tool-origin-cancel.png' if return_to_press else 'space-tool-outer.png')
        event('LEFTMOUSE', 'RELEASE')
        event('SPACE', 'RELEASE')
        yield from settle()
        check(bpy.context.scene.transform_orientation_slots[1].type == ('LOCAL' if return_to_press else 'NORMAL'),
              'Space tool outer stroke failed real LMB-origin cancel' if return_to_press else
              'Space tool radial outer release did not commit Normal')
        check(not modals(), 'Space tool outer/origin release left ownership')
    print('PASS Space tool outer release and actual mouse-press-origin cancellation', flush=True)
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

    for key, name in (('Q', 'select'), ('E', 'rotate'), ('R', 'scale')):
        yield from open_ring(key)
        screenshot('reference-tool-' + name + '.png')
        event('ESC')
        event('LEFTMOUSE', 'RELEASE')
        event(key, 'RELEASE')
        event('ESC', 'RELEASE')
        yield from settle()
        check(not modals(), 'reference screenshot left ownership')

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
    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    event('Q')
    yield from settle()
    yield from stroke('select', 'SE')
    import bmesh
    check(not any(v.select for v in bmesh.from_edit_mesh(cube.data).verts), 'Edit clear failed')
    check_armed('Clear Selection must retain its held Q session')
    yield from stroke('select', 'SW')
    check(tool() == 'builtin.select_lasso', 'Q stroke after Clear Selection did not reopen')
    event('Q', 'RELEASE')
    yield from settle()
    check(not modals(), 'Clear Selection/reopen left ownership')
    with override():
        bpy.ops.ed.undo()
    yield from settle()
    cube = bpy.context.edit_object
    check(any(v.select for v in bmesh.from_edit_mesh(cube.data).verts), 'Edit clear undo failed')
    yield from repeat_strokes('Q', 'select')
    yield from repeat_strokes('W', 'move', 1)
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
    yield from repeat_strokes('W', 'move', 1)
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
    yield from repeat_strokes('F13', 'move', 1)
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

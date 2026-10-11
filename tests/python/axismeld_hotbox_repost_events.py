# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Observe fresh QWER mouse strokes after a companion submenu was visited.

Run in an isolated factory GUI with --enable-event-simulate. All menu targets
come from rendered glyphs/backgrounds. No native layout or modal data is read.
The default assertions intentionally fail when a previous companion cascade is
reposted by another LMB stroke under the same held W/E/R key.
"""
import json
import os
from pathlib import Path
import sys
import traceback

import blf
import bpy
import imbuf
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import (
    menu_background_mask,
    observed_menu_rectangles,
    observed_radial_rectangles,
)

ROOT = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
ART = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', ROOT)).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(ROOT)
ART.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False
RECORDS = []


def settle(count=8):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    yield from settle()
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    scale = bpy.context.preferences.system.ui_scale
    center = (region.x + region.width / 2, region.y + region.height / 2)
    position = list(center)
    theme = bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu, theme.wcol_menu_back, theme.wcol_menu_item):
        colors.inner = (.8, .04, .65, 1)
        colors.inner_sel = (.8, .04, .65, 1)
        colors.text = (1, 1, 1)
        colors.text_sel = (1, 1, 1)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def event(kind, value='PRESS', point=None):
        if point is not None:
            position[:] = point
        win.event_simulate(type=kind, value=value, x=round(position[0]), y=round(position[1]))

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def scene_signature():
        return (tuple(sorted(o.name for o in bpy.context.selected_objects)),
                tuple((o.name, tuple(tuple(row) for row in o.matrix_world))
                      for o in bpy.context.scene.objects))

    def shot(name):
        path = ART / (name + '.png')
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        picture = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = picture.size
            pixels = np.asarray(picture.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(picture)
        print('SCREENSHOT', path, flush=True)
        return pixels

    templates = {}

    def glyph(text):
        if text not in templates:
            blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
            blf.disable(0, blf.WORD_WRAP)
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10 * scale, 0)
            canvas = imbuf.new((int(blf.dimensions(0, text)[0]) + 16, int(40 * scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, text)
            path = ROOT / ('repost-glyph-' + str(len(templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            picture = bpy.data.images.load(str(path), check_existing=False)
            try:
                w, h = picture.size
                alpha = np.asarray(picture.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, 3] > .35
                yy, xx = np.nonzero(alpha)
                templates[text] = alpha[yy.min():yy.max()+1, xx.min():xx.max()+1].copy()
            finally:
                bpy.data.images.remove(picture)
        return templates[text]

    def caption(pixels, text):
        reference = glyph(text)
        gh, gw = reference.shape
        # Use the full rendered window: companion menus can legitimately overflow
        # the originating viewport. The distinctive full caption avoids toolbar text.
        best = (0.0, (0, 0))
        for level in (.18, .3, .5):
            ink = np.min(pixels[:, :, :3], axis=2) > level
            shape = (ink.shape[0] + gh - 1, ink.shape[1] + gw - 1)
            hits = np.fft.irfft2(np.fft.rfft2(ink, s=shape) *
                                np.fft.rfft2(reference[::-1, ::-1], s=shape), s=shape)
            hits = hits[gh-1:ink.shape[0], gw-1:ink.shape[1]]
            total = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
            counts = total[gh:, gw:] - total[:-gh, gw:] - total[gh:, :-gw] + total[:-gh, :-gw]
            scores = 2 * hits / (counts + np.count_nonzero(reference))
            y, x = np.unravel_index(np.argmax(scores), scores.shape)
            found = (float(scores[y, x]), (float(x + gw / 2), float(y + gh / 2)))
            if found[0] > best[0]:
                best = found
        return best

    def locate(pixels, text):
        score, point = caption(pixels, text)
        assert score > .75, ('Rendered caption missing', text, score)
        print('ACTUAL_LABEL', text, score, point, flush=True)
        return point

    def native_boxes(pixels):
        return observed_menu_rectangles(menu_background_mask(pixels), 35 * scale, 28 * scale)

    def save_record(record):
        RECORDS.append(record)
        (ART / 'hotbox-repost-events.json').write_text(json.dumps(RECORDS, indent=2), encoding='utf-8')

    before_scene = scene_signature()
    offsets = ((-65, 35), (65, 70), (0, 20), (-75, 55))
    for key, name, slot_index in (('W', 'move', 1), ('E', 'rotate', 2), ('R', 'scale', 3)):
        slot = bpy.context.scene.transform_orientation_slots[slot_index]
        slot.type = 'LOCAL'
        event('MOUSEMOVE', 'NOTHING', center)
        event(key)
        yield from settle()
        assert modals() == ['VIEW3D_OT_axismeld_hotbox'], (key, 'not armed', modals())
        # One key press owns all six mouse strokes: disabled cancel, center
        # cancel, execution, and the fresh root after each preceding stroke.
        for index, ending in enumerate(('disabled', 'center', 'execute')):
            origin = (center[0] + offsets[index][0] * scale,
                      center[1] + offsets[index][1] * scale)
            event('MOUSEMOVE', 'NOTHING', origin)
            event('LEFTMOUSE')
            yield from settle()
            prefix = name + '-' + ending
            root_pixels = shot(prefix + '-root')
            root_columns = native_boxes(root_pixels)
            assert caption(root_pixels, 'UV Edge Loop')[0] < .7, (prefix, 'initial root has stale cascade')
            ring = observed_radial_rectangles(root_pixels, scale, {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'})
            world = ring['rects']['W']
            world_point = ((world[0] + world[2]) / 2, (world[1] + world[3]) / 2)
            event('MOUSEMOVE', 'NOTHING', locate(root_pixels, 'Selection Constraints'))
            yield from settle()
            branch_pixels = shot(prefix + '-cascade')
            leaf_point = locate(branch_pixels, 'UV Edge Loop')
            assert len(native_boxes(branch_pixels)) > len(root_columns), (prefix, 'cascade not visibly opened')
            if ending == 'disabled':
                event('MOUSEMOVE', 'NOTHING', leaf_point)
            elif ending == 'center':
                event('MOUSEMOVE', 'NOTHING', origin)
            else:
                event('MOUSEMOVE', 'NOTHING', world_point)
            yield from settle()
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            expected = 'GLOBAL' if ending == 'execute' else 'LOCAL'
            assert slot.type == expected, (prefix, 'wrong command effect', slot.type, expected)
            assert scene_signature() == before_scene, (prefix, 'selection or geometry changed')
            assert modals() == ['VIEW3D_OT_axismeld_hotbox'], (prefix, 'not rearmed', modals())

            next_origin = (center[0] + offsets[index + 1][0] * scale,
                           center[1] + offsets[index + 1][1] * scale)
            event('MOUSEMOVE', 'NOTHING', next_origin)
            event('LEFTMOUSE')
            yield from settle()
            repost = shot(prefix + '-reposted')
            root_score = caption(repost, 'Selection Constraints')[0]
            old_score = caption(repost, 'UV Edge Loop')[0]
            repost_columns = native_boxes(repost)
            record = {'key': key, 'ending': ending, 'old_leaf_score': old_score,
                      'root_caption_score': root_score, 'root_columns': root_columns,
                      'repost_columns': repost_columns, 'orientation': slot.type,
                      'modals': modals(), 'scale': scale,
                      'window': [repost.shape[1], repost.shape[0]]}
            save_record(record)
            assert root_score > .75, (prefix, 'fresh root missing', record)
            assert old_score < .7 and len(repost_columns) == len(root_columns), (
                prefix, 'fresh LMB stroke reopened the previous companion cascade', record)
            # A successful fresh stroke can cancel at its own new origin without
            # committing a hidden leaf, and must keep the same held trigger alive.
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            assert slot.type == expected and scene_signature() == before_scene, (prefix, 'fresh-origin cancel mutated scene')
            assert modals() == ['VIEW3D_OT_axismeld_hotbox'], (prefix, 'fresh-origin cancel lost ownership')
            print('PASS REPOST', key, ending, flush=True)

        event(key, 'RELEASE')
        yield from settle()
        assert not modals(), (key, 'trigger release left stale modal', modals())

    print('AXISMELD_HOTBOX_REPOST_EVENTS_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return .025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1)

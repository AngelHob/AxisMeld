# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real hotbox reasons: complete rendered sentences at narrow widths and high DPI.

Run in a disposable GUI through the hotbox runner. Input targets and reason lines
are located from rendered glyphs, never the native layout model. AXISMELD_REASON_SCALE
selects the UI scale (default 1.5); the runner controls the actual window geometry.
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
    from axismeld import hotbox_runtime
    win = bpy.context.window
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    bpy.context.preferences.view.ui_scale = float(os.environ.get('AXISMELD_REASON_SCALE', '1.5'))
    yield from settle(12)
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    scale = bpy.context.preferences.system.ui_scale
    origin = (region.x + region.width / 2, region.y + region.height / 2)
    position = list(origin)
    theme = bpy.context.preferences.themes[0].user_interface
    original_reason_text = tuple(theme.wcol_menu_back.text)
    original_reason_background = tuple(theme.wcol_menu_back.inner)
    # Isolate reason ink from the grid and native menu labels, without changing
    # font metrics, reason content, or menu geometry.
    theme.wcol_menu_back.text = (0, 1, 0)
    theme.wcol_menu_back.inner = (.08, .08, .08, 1)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'style': 'rows', 'rows': ['common'], 'transparency': 0}})
        snapshot = json.loads(hotbox_runtime.snapshot(bpy.context))
    nodes = {}
    pending = list(snapshot['menus'])
    while pending:
        node = pending.pop()
        nodes[node['id']] = node
        pending.extend(node.get('children', []))

    def event(kind, value='PRESS', point=None):
        if point is not None:
            position[:] = point
        win.event_simulate(type=kind, value=value, x=round(position[0]), y=round(position[1]))

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
            width = int(blf.dimensions(0, text)[0]) + 16
            canvas = imbuf.new((width, int(40 * scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, text)
            path = ROOT / ('reason-glyph-' + str(len(templates)) + '.png')
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

    def match(ink, text):
        reference = glyph(text)
        gh, gw = reference.shape
        if ink.shape[0] < gh or ink.shape[1] < gw:
            return 0.0, (0, 0)
        shape = (ink.shape[0] + gh - 1, ink.shape[1] + gw - 1)
        hits = np.fft.irfft2(np.fft.rfft2(ink, s=shape) *
                            np.fft.rfft2(reference[::-1, ::-1], s=shape), s=shape)
        hits = hits[gh-1:ink.shape[0], gw-1:ink.shape[1]]
        total = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        counts = total[gh:, gw:] - total[:-gh, gw:] - total[gh:, :-gw] + total[:-gh, :-gw]
        scores = 2 * hits / (counts + np.count_nonzero(reference))
        y, x = np.unravel_index(np.argmax(scores), scores.shape)
        return float(scores[y, x]), (x + gw / 2, y + gh / 2)

    def locate(pixels, label, bounds=None):
        x0, y0, x1, y1 = map(int, bounds or (0, 80 * scale, pixels.shape[1], pixels.shape[0]))
        best = (0, (0, 0))
        for level in (.18, .3, .5):
            ink = np.min(pixels[y0:y1, x0:x1, :3], axis=2) > level
            candidate = match(ink, label)
            if candidate[0] > best[0]:
                best = candidate
        assert best[0] > .75, ('Complete menu caption not found', label, best, bounds)
        print('ACTUAL_LABEL', label, best, flush=True)
        return best[1][0] + x0, best[1][1] + y0

    def verify_reason(pixels, reason, case):
        # Read observed line bands, then match a complete consecutive word span
        # against each. This accepts any valid wrap points while rejecting an
        # omitted word, clipped suffix, or replacement ellipsis.
        rgb = pixels[:, :, :3]
        ink = (rgb[:, :, 1] > .35) & (rgb[:, :, 1] > 2 * np.maximum(rgb[:, :, 0], rgb[:, :, 2]))
        occupied = np.flatnonzero(np.any(ink, axis=1))
        bands = list(reversed([b for b in np.split(occupied, np.flatnonzero(np.diff(occupied) > 2 * scale) + 1) if len(b)]))
        words = reason.split(' ')
        complete = None
        # Native section headings share the theme color. A candidate must decode
        # the whole reason in consecutive observed lines, wherever it can avoid
        # menu targets, rather than mistaking those headings for explanation ink.
        for start in range(len(bands)):
            consumed = 0
            lines = []
            for band in bands[start:]:
                row = ink[max(0, int(band[0])-2):int(band[-1])+3]
                columns = np.flatnonzero(np.any(row, axis=0))
                actual_width = int(columns[-1] - columns[0] + 1)
                candidates = []
                for end in range(consumed + 1, len(words) + 1):
                    text = ' '.join(words[consumed:end])
                    if abs(glyph(text).shape[1] - actual_width) > 3:
                        continue
                    score, _ = match(row, text)
                    candidates.append((score, end, text))
                if not candidates or max(candidates)[0] <= .75:
                    break
                score, consumed, text = max(candidates)
                lines.append({'text': text, 'score': score, 'ymin': int(band[0]), 'ymax': int(band[-1])+1,
                              'xmin': int(columns[0]), 'xmax': int(columns[-1])+1})
                if consumed == len(words):
                    complete = lines
                    break
            if complete:
                break
        assert complete, ('Complete reason could not be read from rendered lines', case, reason)
        lines = complete
        bounds = [min(l['xmin'] for l in lines), min(l['ymin'] for l in lines),
                  max(l['xmax'] for l in lines), max(l['ymax'] for l in lines)]
        assert bounds[0] >= 8 * scale and bounds[2] <= pixels.shape[1] - 8 * scale, (
            'Reason text crossed horizontal safe margin', case, bounds, pixels.shape[1])
        assert bounds[1] >= 8 * scale and bounds[3] <= pixels.shape[0] - 8 * scale, (
            'Reason text crossed vertical safe margin', case, bounds, pixels.shape[0])
        full_width = glyph(reason).shape[1]
        if full_width > pixels.shape[1] - 24 * scale:
            assert len(lines) > 1, ('Long reason was not wrapped', case, lines)
        RECORDS.append({'case': case, 'reason': reason, 'scale': scale,
                        'window': [pixels.shape[1], pixels.shape[0]], 'lines': lines,
                        'ink_bounds': bounds})
        (ART / 'hotbox-reason-events.json').write_text(json.dumps(RECORDS, indent=2), encoding='utf-8')
        print('PASS COMPLETE_REASON', case, len(lines), reason, flush=True)

    def close(key, mouse=False):
        event('MOUSEMOVE', 'NOTHING', origin)
        if mouse:
            event('LEFTMOUSE', 'RELEASE')
        event(key, 'RELEASE')
        yield from settle()
        assert not list(win.modal_operators), [op.bl_idname for op in win.modal_operators]

    yield from settle()
    event('MOUSEMOVE', 'NOTHING', origin)
    event('SPACE')
    yield from settle()
    pixels = shot('reason-space')
    # The global Blender Edit caption remains visible and is intentionally
    # excluded; only a caption inside the source viewport is a hotbox target.
    viewport = (region.x, region.y, region.x + region.width, region.y + region.height - 30 * scale)
    event('MOUSEMOVE', 'NOTHING', locate(pixels, 'Edit', viewport))
    yield from settle()
    event('LEFTMOUSE')
    yield from settle()
    pixels = shot('reason-edit')
    node = next(n for n in nodes.values() if n['label'] == 'Duplicate Special')
    event('MOUSEMOVE', 'NOTHING', locate(pixels, node['label']))
    yield from settle()
    verify_reason(shot('reason-duplicate-special'), node['reason'], 'duplicate-special')
    theme.wcol_menu_back.text = original_reason_text
    theme.wcol_menu_back.inner = original_reason_background
    event('MOUSEMOVE', 'NOTHING', position)
    yield from settle()
    shot('reason-duplicate-special-theme')
    theme.wcol_menu_back.text = (0, 1, 0)
    theme.wcol_menu_back.inner = (.08, .08, .08, 1)
    yield from close('SPACE', mouse=True)

    for suffix in ('delete', 'delete_non_deformer', 'inputs'):
        node = nodes['context.history.' + suffix]
        event('MOUSEMOVE', 'NOTHING', origin)
        event('A')
        yield from settle()
        event('LEFTMOUSE')
        yield from settle()
        pixels = shot('reason-history-' + suffix + '-menu')
        event('MOUSEMOVE', 'NOTHING', locate(pixels, node['label']))
        yield from settle()
        verify_reason(shot('reason-history-' + suffix), node['reason'], 'history-' + suffix)
        yield from close('A', mouse=True)

    print('AXISMELD_HOTBOX_REASON_EVENTS_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
    except StopIteration:
        bpy.ops.wm.quit_blender()
        return None
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return .1


bpy.app.timers.register(tick, first_interval=.5)

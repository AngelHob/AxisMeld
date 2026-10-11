# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real hotbox reasons: complete sentences without covering the open menus.

Run in a disposable GUI through the hotbox runner. Input targets and reason lines
are located from rendered glyphs, never the native layout model. AXISMELD_REASON_SCALE
selects the UI scale (default 1.5); the runner controls the actual window geometry.
AXISMELD_REASON_CASES selects comma-separated case names. Explicitly selecting
cases with AXISMELD_REASON_NO_FIT=1 asserts suppression instead of accepting a
missing explanation in the normal complete-reason tests.
AXISMELD_REASON_QUAD=1 enters native quad view before capturing the source pane.
AXISMELD_REASON_RESTORE=1 requires one no-fit case, then enlarges the real window
with the native fullscreen toggle and requires that same reason to reappear.
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
ALL_CASES = ('duplicate-special', 'history-delete', 'history-delete_non_deformer', 'history-inputs')
CASE_FILTER = os.environ.get('AXISMELD_REASON_CASES')
CASES = tuple(s.strip() for s in CASE_FILTER.split(',')) if CASE_FILTER else ALL_CASES
NO_FIT = os.environ.get('AXISMELD_REASON_NO_FIT') == '1'
QUAD = os.environ.get('AXISMELD_REASON_QUAD') == '1'
RESTORE = os.environ.get('AXISMELD_REASON_RESTORE') == '1'
assert CASES and set(CASES).issubset(ALL_CASES), ('Unknown reason cases', CASES)
assert not NO_FIT or CASE_FILTER, 'No-fit tests must explicitly select their cases'
assert not RESTORE or (NO_FIT and len(CASES) == 1), 'Restore requires exactly one explicit no-fit case'
sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import menu_background_mask, observed_menu_rectangles


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
    if QUAD:
        with bpy.context.temp_override(window=win, area=area, region=region):
            assert bpy.ops.screen.region_quadview() == {'FINISHED'}
        yield from settle(12)
        area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
        panes = sorted((r for r in area.regions if r.type == 'WINDOW'), key=lambda r: (-r.y, r.x))
        assert len(panes) == 4 and len(area.spaces.active.region_quadviews) == 4
        region = panes[0]
    scale = bpy.context.preferences.system.ui_scale
    assert region.width / scale >= 340 and region.height / scale >= 200, (
        'Reason fixture needs a supported source pane', region.width, region.height, scale, QUAD)
    origin = (region.x + region.width / 2, region.y + region.height / 2)
    position = list(origin)
    theme = bpy.context.preferences.themes[0].user_interface
    original_colors = {(name, field): tuple(getattr(getattr(theme, name), field))
                       for name in ('wcol_menu', 'wcol_menu_back', 'wcol_menu_item')
                       for field in ('text', 'inner', 'inner_sel')}

    def diagnostic_theme(enabled=True):
        for (name, field), color in original_colors.items():
            setattr(getattr(theme, name), field, color)
        if enabled:
            # Backdrops and reason panels share blue. Record the original menu
            # components before hover so shared colors cannot hide an overlap.
            for name in ('wcol_menu', 'wcol_menu_item', 'wcol_menu_back'):
                color = (.08, .08, .65, 1) if name == 'wcol_menu_back' else (.8, .04, .65, 1)
                getattr(theme, name).inner = color
                getattr(theme, name).inner_sel = color
            theme.wcol_menu_back.text = (0, 1, 0)

    diagnostic_theme()

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'style': 'rows', 'rows': ['common'], 'transparency': 0}})

    def current_nodes():
        with override():
            snapshot = json.loads(hotbox_runtime.snapshot(bpy.context))
        nodes, parents = {}, {}
        pending = [(node, None) for node in snapshot['menus']]
        while pending:
            node, parent = pending.pop()
            nodes[node['id']] = node
            parents[node['id']] = parent
            pending.extend((child, node['id']) for child in node.get('children', []))
        return nodes, parents

    def scene_state():
        with override():
            return {'mode': bpy.context.mode,
                    'active': getattr(bpy.context.view_layer.objects.active, 'name', None),
                    'objects': sorted((obj.name, obj.type, obj.select_get(),
                                       tuple(value for row in obj.matrix_world for value in row),
                                       getattr(obj.data, 'name', None))
                                      for obj in bpy.context.scene.objects)}

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

    def caption_match(pixels, label, bounds=None):
        # Bottom-aligned native menus can place valid captions below the old
        # toolbar exclusion band. Callers restrict ambiguous root labels.
        x0, y0, x1, y1 = map(int, bounds or (0, 0, pixels.shape[1], pixels.shape[0]))
        best = (0, (0, 0))
        for level in (.18, .3, .5):
            ink = np.min(pixels[y0:y1, x0:x1, :3], axis=2) > level
            candidate = match(ink, label)
            if candidate[0] > best[0]:
                best = candidate
        return best[0], (best[1][0] + x0, best[1][1] + y0)

    def locate(pixels, label, bounds=None):
        best = caption_match(pixels, label, bounds)
        assert best[0] > .75, ('Complete menu caption not found', label, best, bounds)
        print('ACTUAL_LABEL', label, best, flush=True)
        return best[1]

    def green_ink(pixels):
        rgb = pixels[:, :, :3]
        return (rgb[:, :, 1] > .35) & (rgb[:, :, 1] > 2 * np.maximum(rgb[:, :, 0], rgb[:, :, 2]))

    def blue_background(pixels):
        rgb = pixels[:, :, :3]
        return (rgb[:, :, 2] > .25) & (rgb[:, :, 2] > 2.2 * np.maximum(rgb[:, :, 0], rgb[:, :, 1]))

    def intersects(a, b):
        return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

    def neutral_menu(pixels, case, nodes, name):
        # A clamped popup can place a disabled command under the opening press,
        # displaying its reason before the intended hover. Clear that reason
        # through real pointer motion before observing protected menu pixels.
        if case.startswith('duplicate-special'):
            title = 'Hierarchy'
            assert any(node['kind'] == 'separator' and node['label'] == title
                       and not node.get('reason') for node in nodes.values())
            score, point = match(green_ink(pixels), title)
            assert score > .75, ('Noninteractive menu heading not found', title, score)
            print('NEUTRAL_MENU_TITLE', title, score, point, flush=True)
        else:
            # This radial menu has no central title. Its observed North/South
            # captions identify the actual clear center after window clamping.
            north = locate(pixels, 'Enable All Outputs')
            south = locate(pixels, 'Disable All Outputs')
            point = ((north[0] + south[0]) / 2, (north[1] + south[1]) / 2)
            x, y = map(round, point)
            assert not (menu_background_mask(pixels) | blue_background(pixels))[y, x], (
                'Observed radial center is occupied', point)
            print('NEUTRAL_RADIAL_CENTER', point, flush=True)
        event('MOUSEMOVE', 'NOTHING', point)
        yield from settle()
        return shot(name)

    def protect_menu(pixels, idle, node, nodes, parents):
        rectangles = []
        # Keep colors separate: a root button can touch two native backdrops.
        # Unioning their pixels first would bridge columns and incorrectly mark
        # the empty space inside their joint bounding box as an occupied menu.
        for mask in (menu_background_mask, blue_background):
            colored, previous = mask(pixels), mask(idle)
            rectangles.extend(rect for rect in observed_menu_rectangles(colored, 4 * scale, 4 * scale)
                              if np.any((colored & ~previous)[rect[1]:rect[3], rect[0]:rect[2]]))
        rectangles = sorted(set(rectangles))
        assert rectangles, 'No actual pre-hover menu backgrounds were observed'
        # Only labels found in the pre-hover rendered menus are protected. The
        # snapshot supplies expected strings, never their position or dimensions.
        parent = parents[node['id']]
        labels = {n['label'] for n in nodes.values() if parents[n['id']] in (None, parent) and n.get('label')}
        labels.add(node['label'])
        captions = []
        for label in sorted(labels):
            for rect in rectangles:
                height, width = glyph(label).shape
                if width > rect[2] - rect[0] or height > rect[3] - rect[1]:
                    continue
                score, center = caption_match(pixels, label, rect)
                # Reject FFT rounding around the exact threshold while choosing
                # baseline captions; later preservation still requires > .75.
                if score <= .75 + 1e-6:
                    continue
                x, y = center
                pad = int(2 * scale)
                crop = (max(0, int(x - width / 2) - pad), max(0, int(y - height / 2) - pad),
                        min(pixels.shape[1], int(x + width / 2) + pad),
                        min(pixels.shape[0], int(y + height / 2) + pad))
                captions.append({'label': label, 'bounds': crop, 'before_score': score})
        assert any(c['label'] == node['label'] for c in captions), ('Target caption was not protected', node['label'])
        return {'rectangles': rectangles, 'captions': captions, 'pixels': pixels}

    def verify_captions(pixels, protected, case):
        for caption in protected['captions']:
            score, _ = caption_match(pixels, caption['label'], caption['bounds'])
            caption['after_score'] = score
            assert score > .75, ('Protected menu caption was covered', case, caption)

    def write_record(record):
        RECORDS.append(record)
        (ART / 'hotbox-reason-events.json').write_text(json.dumps(RECORDS, indent=2), encoding='utf-8')

    def read_reason(ink, reason, x_offset, y_offset):
        # Continuous character spans also cover BLF HardLimit breaks inside a
        # word in a narrow side strip. Every non-space character must be consumed
        # in order; the existing full-glyph Dice threshold remains unchanged.
        # UI redraws can change font 0 after templates are cached. Reset the
        # measurement size before the cheap advance filter, even on cache hits.
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        blf.disable(0, blf.WORD_WRAP)
        occupied = np.flatnonzero(np.any(ink, axis=1))
        bands = list(reversed([b for b in np.split(occupied, np.flatnonzero(np.diff(occupied) > 2 * scale) + 1) if len(b)]))
        for start in range(len(bands)):
            consumed, lines = 0, []
            for band in bands[start:]:
                row = ink[max(0, int(band[0])-2):int(band[-1])+3]
                columns = np.flatnonzero(np.any(row, axis=0))
                actual_width = int(columns[-1] - columns[0] + 1)
                candidates = []
                for end in range(consumed + 1, len(reason) + 1):
                    text = reason[consumed:end]
                    if text[-1].isspace():
                        continue
                    # Font advances cheaply discard impossible spans before a
                    # raster template is created; actual ink widths decide fit.
                    if abs(blf.dimensions(0, text)[0] - actual_width) > 8 * scale:
                        continue
                    if abs(glyph(text).shape[1] - actual_width) > 3:
                        continue
                    score, _ = match(row, text)
                    candidates.append((score, end, text))
                if not candidates or max(candidates)[0] <= .75:
                    break
                score, consumed, text = max(candidates)
                lines.append({'text': text, 'score': score,
                              'ymin': int(band[0]) + y_offset, 'ymax': int(band[-1]) + 1 + y_offset,
                              'xmin': int(columns[0]) + x_offset, 'xmax': int(columns[-1]) + 1 + x_offset})
                while consumed < len(reason) and reason[consumed].isspace():
                    consumed += 1
                if consumed == len(reason):
                    return lines
        return None

    def verify_reason(pixels, reason, case, protected, expect_no_fit=NO_FIT):
        ink = green_ink(pixels)
        record = {'case': case, 'reason': reason, 'scale': scale, 'expect_no_fit': expect_no_fit,
                  'quad': QUAD, 'source_region': [region.x, region.y, region.width, region.height],
                  'window': [pixels.shape[1], pixels.shape[0]],
                  'protected_menu_rectangles': protected['rectangles'],
                  'protected_captions': protected['captions']}
        if expect_no_fit:
            new_ink = ink & ~green_ink(protected['pixels'])
            record['new_reason_ink_pixels'] = int(np.count_nonzero(new_ink))
            write_record(record)
            assert not np.any(new_ink), ('No-fit reason must be absent', case, record['new_reason_ink_pixels'])
            verify_captions(pixels, protected, case)
            print('PASS NO_FIT_MENU_PRESERVED', case, flush=True)
            return

        complete = None
        panel = None
        # Work within observed blue components so unrelated section headings at
        # the same height cannot corrupt a reason shown beside the menus.
        for rect in observed_menu_rectangles(blue_background(pixels), 3 * scale, 3 * scale):
            x0, y0, x1, y1 = rect
            complete = read_reason(ink[y0:y1, x0:x1], reason, x0, y0)
            if complete:
                panel = rect
                break
        assert complete, ('Complete reason could not be read from rendered lines', case, reason)
        lines = complete
        bounds = [min(l['xmin'] for l in lines), min(l['ymin'] for l in lines),
                  max(l['xmax'] for l in lines), max(l['ymax'] for l in lines)]
        overlaps = [rect for rect in protected['rectangles'] if intersects(panel, rect)]
        record.update({'lines': lines, 'ink_bounds': bounds, 'panel_bounds': panel,
                       'overlapping_menu_rectangles': overlaps})
        write_record(record)
        assert not overlaps, ('Reason backdrop covered an existing menu', case, panel, overlaps)
        assert not any(intersects(bounds, rect) for rect in protected['rectangles']), (
            'Reason text covered an existing menu', case, bounds)
        verify_captions(pixels, protected, case)
        assert bounds[0] >= 8 * scale and bounds[2] <= pixels.shape[1] - 8 * scale, (
            'Reason text crossed horizontal safe margin', case, bounds, pixels.shape[1])
        assert bounds[1] >= 8 * scale and bounds[3] <= pixels.shape[0] - 8 * scale, (
            'Reason text crossed vertical safe margin', case, bounds, pixels.shape[0])
        full_width = glyph(reason).shape[1]
        if full_width > pixels.shape[1] - 24 * scale:
            assert len(lines) > 1, ('Long reason was not wrapped', case, lines)
        print('PASS COMPLETE_REASON_NO_OVERLAP', case, len(lines), reason, flush=True)

    def close(key, mouse=False):
        # Clamping can place a command under the original press position in a
        # short window. Cancel while the input is held, before any release.
        event('ESC')
        yield from settle()
        event('ESC', 'RELEASE')
        if mouse:
            event('LEFTMOUSE', 'RELEASE')
        event(key, 'RELEASE')
        yield from settle()
        assert not list(win.modal_operators), [op.bl_idname for op in win.modal_operators]

    initial_scene = scene_state()
    if 'duplicate-special' in CASES:
        yield from settle()
        nodes, parents = current_nodes()
        node = next(n for n in nodes.values() if n['label'] == 'Duplicate Special')
        assert node.get('reason'), node
        event('MOUSEMOVE', 'NOTHING', origin)
        yield from settle()
        idle = shot('reason-duplicate-special-idle')
        event('SPACE')
        yield from settle()
        pixels = shot('reason-space')
        # Exclude the global Blender Edit caption above the source viewport.
        viewport = (region.x, region.y, region.x + region.width, region.y + region.height - 30 * scale)
        event('MOUSEMOVE', 'NOTHING', locate(pixels, 'Edit', viewport))
        yield from settle()
        event('LEFTMOUSE')
        yield from settle()
        pixels = shot('reason-edit')
        pixels = yield from neutral_menu(pixels, 'duplicate-special', nodes, 'reason-edit-neutral')
        protected = protect_menu(pixels, idle, node, nodes, parents)
        event('MOUSEMOVE', 'NOTHING', locate(pixels, node['label']))
        yield from settle()
        pixels = shot('reason-duplicate-special')
        diagnostic_theme(False)
        event('MOUSEMOVE', 'NOTHING', position)
        yield from settle()
        shot('reason-duplicate-special-theme')
        diagnostic_theme()
        yield from close('SPACE', mouse=True)
        assert scene_state() == initial_scene, ('Reason hover/cancel changed scene or selection', 'duplicate-special')
        verify_reason(pixels, node['reason'], 'duplicate-special', protected)

    for suffix in ('delete', 'delete_non_deformer', 'inputs'):
        case = 'history-' + suffix
        if case not in CASES:
            continue
        nodes, parents = current_nodes()
        node = nodes['context.history.' + suffix]
        assert node.get('reason'), node
        event('MOUSEMOVE', 'NOTHING', origin)
        yield from settle()
        idle = shot('reason-' + case + '-idle')
        event('A')
        yield from settle()
        event('LEFTMOUSE')
        yield from settle()
        pixels = shot('reason-history-' + suffix + '-menu')
        pixels = yield from neutral_menu(pixels, case, nodes, 'reason-' + case + '-neutral')
        protected = protect_menu(pixels, idle, node, nodes, parents)
        event('MOUSEMOVE', 'NOTHING', locate(pixels, node['label']))
        yield from settle()
        pixels = shot('reason-history-' + suffix)
        yield from close('A', mouse=True)
        assert scene_state() == initial_scene, ('Reason hover/cancel changed scene or selection', case)
        verify_reason(pixels, node['reason'], case, protected)

    if RESTORE:
        # The no-fit branch above has already verified zero new reason ink,
        # preserved captions, cancellation, and unchanged scene/selection.
        # Resize the actual window; changing only UI scale would invalidate the
        # scale captured by a hotbox invocation and would not prove recovery.
        case = CASES[0]
        original_node = node
        small_window = RECORDS[-1]['window']
        assert RECORDS[-1]['expect_no_fit'] and RECORDS[-1]['new_reason_ink_pixels'] == 0
        assert not list(win.modal_operators)
        with override():
            assert bpy.ops.wm.window_fullscreen_toggle() == {'FINISHED'}
        yield from settle(16)
        area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
        panes = sorted((r for r in area.regions if r.type == 'WINDOW'), key=lambda r: (-r.y, r.x))
        assert len(panes) == (4 if QUAD else 1), ('Resize changed source pane layout', len(panes), QUAD)
        region = panes[0]
        origin = (region.x + region.width / 2, region.y + region.height / 2)
        assert bpy.context.preferences.system.ui_scale == scale, 'Window resize changed UI scale'
        assert scene_state() == initial_scene, 'Window resize changed scene or selection'
        nodes, parents = current_nodes()
        node = nodes[original_node['id']]
        assert (node['label'], node['reason']) == (original_node['label'], original_node['reason']), (
            'Restore must reopen the same node and real reason', original_node, node)
        event('MOUSEMOVE', 'NOTHING', origin)
        yield from settle()
        idle = shot('reason-' + case + '-restored-idle')
        large_window = [idle.shape[1], idle.shape[0]]
        assert all(after >= before for after, before in zip(large_window, small_window)) and any(
            after > before for after, before in zip(large_window, small_window)), (
                'Native fullscreen toggle did not enlarge the actual window', small_window, large_window)
        key = 'SPACE' if case == 'duplicate-special' else 'A'
        event(key)
        yield from settle()
        if key == 'SPACE':
            pixels = shot('reason-space-restored')
            viewport = (region.x, region.y, region.x + region.width, region.y + region.height - 30 * scale)
            event('MOUSEMOVE', 'NOTHING', locate(pixels, 'Edit', viewport))
            yield from settle()
        event('LEFTMOUSE')
        yield from settle()
        pixels = shot('reason-' + case + '-restored-menu')
        pixels = yield from neutral_menu(pixels, case, nodes, 'reason-' + case + '-restored-neutral')
        protected = protect_menu(pixels, idle, node, nodes, parents)
        event('MOUSEMOVE', 'NOTHING', locate(pixels, node['label']))
        yield from settle()
        pixels = shot('reason-' + case + '-restored')
        diagnostic_theme(False)
        event('MOUSEMOVE', 'NOTHING', position)
        yield from settle()
        shot('reason-' + case + '-restored-theme')
        diagnostic_theme()
        yield from close(key, mouse=True)
        assert scene_state() == initial_scene, 'Restored reason hover/cancel changed scene or selection'
        verify_reason(pixels, node['reason'], case + '-restored', protected, expect_no_fit=False)
        RECORDS[-1]['restoration_of'] = {'case': case, 'node_id': node['id'], 'small_window': small_window}
        print('PASS REASON_RESTORED_AFTER_WINDOW_ENLARGED', case, small_window, large_window, flush=True)

    diagnostic_theme(False)
    assert len(RECORDS) == len(CASES) + int(RESTORE), (len(RECORDS), CASES, RESTORE)
    (ART / 'hotbox-reason-events.json').write_text(json.dumps(RECORDS, indent=2), encoding='utf-8')
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

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare actual companion pixels with an independently recorded released build.

AXISMELD_COMPACT_MODE=record writes AXISMELD_COMPACT_BASELINE; compare (default)
requires it. Both modes use real public gestures and screenshot-derived geometry.
No native layout coordinates, command snapshots or OS input APIs are consumed.
The released baseline has 16 logical-pixel rows; the current target is 18.
"""
import hashlib
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
from axismeld_hotbox_image_fixture import menu_background_mask, observed_menu_rectangles

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
mode = os.environ.get('AXISMELD_COMPACT_MODE', 'compare')
assert mode in {'record', 'compare'}
baseline_path = Path(os.environ['AXISMELD_COMPACT_BASELINE']).resolve()
baseline = json.loads(baseline_path.read_text(encoding='utf-8')) if mode == 'compare' else None
ROW_HEIGHT_CONTRACT = {'baseline': 16.0, 'current': 18.0, 'native': 24.0}
BASELINE_FONT_FACTOR = ROW_HEIGHT_CONTRACT['baseline'] / ROW_HEIGHT_CONTRACT['native']
CURRENT_FONT_FACTOR = ROW_HEIGHT_CONTRACT['current'] / ROW_HEIGHT_CONTRACT['native']
RELATIVE_SCALE = ROW_HEIGHT_CONTRACT['current'] / ROW_HEIGHT_CONTRACT['baseline']
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False

RINGS = {
    'views': {'N': 'Perspective View', 'NW': 'Left View', 'W': 'Top View',
              'E': 'Side View', 'SW': 'Back View', 'SE': 'Bottom View', 'S': 'Front View'},
    'create': {'N': 'Create Polygon Tool', 'NW': 'Plane', 'NE': 'Disc', 'W': 'Cylinder',
               'E': 'Sphere', 'SW': 'Cone', 'SE': 'Torus', 'S': 'Cube'},
    'object': {'N': 'Target Weld Tool', 'NW': 'Sculpt Tool', 'NE': 'Fill Holes',
               'W': 'Multi-Cut', 'E': 'Append to Polygon Tool', 'SW': 'Insert Edge Loop Tool',
               'SE': 'Soften/Harden Edges', 'S': 'Extrude'},
    'move': {'N': 'Symmetry', 'NW': 'Object', 'NE': 'Component', 'W': 'World',
             'E': 'Snap', 'SW': 'Axis', 'SE': 'Keep Spacing', 'S': 'Select'},
}
LABELS = {
    'create': ('Platonic Solid', 'Pyramid', 'Prism', 'Pipe', 'Helix', 'Gear', 'Soccer Ball',
               'Super Ellipse', 'Spherical Harmonics', 'Ultra Shape', 'Type', 'SVG',
               'Quad Draw Tool', 'Interactive Creation', 'Exit On Completion', 'Polygon Display All'),
    'object': ('Offset Edge Loop Tool', 'Smooth', 'Unsmooth', 'Subdiv Proxy', 'Crease Tool',
               'Project Curve on mesh', 'Split mesh with projected curve', 'Mirror', 'Mapping',
               'Triangulate', 'Quadrangulate', 'Reduce', 'Remesh', 'Retopologize',
               'Transfer Vertex Order', 'Separate', 'Combine', 'Booleans', 'Cleanup...',
               'Connect Tool', 'Quad Draw Tool', 'Polygon Display'),
    'move': ('Selection Constraints', 'Transform Constraints', 'Shift Extrude', 'Shift Duplicate',
             'Preserve UVs', 'Preserve Children', 'Tweak Mode', 'Update Triad', 'Move Options'),
    'mapping': ('Planar Map X', 'Planar Map Y', 'Planar Map Z'),
}


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=7):
    for _ in range(count):
        yield


def foreground(pixels):
    rgb = pixels[:, :, :3]
    return (rgb[:, :, 1] > .24) & (rgb[:, :, 1] > np.maximum(rgb[:, :, 0], rgb[:, :, 2]) * .45)


def suite():
    win = bpy.context.window
    def refresh():
        nonlocal area, region
        area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in area.regions if r.type == 'WINDOW')
    area = region = None
    refresh()
    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'Maya preset activation failed')
    yield from settle()
    with override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.screen.screen_full_area()
    yield from settle()
    refresh()
    area.spaces.active.show_region_ui = False
    area.spaces.active.show_region_toolbar = False
    from axismeld import hotbox_runtime
    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'style': 'center', 'transparency': 0, 'rows': [], 'center_buttons': {'LEFTMOUSE': 'views'},
            'appearance': {'theme_background': False, 'background': [204, 10, 166],
                           'brightness': 0, 'text': [255, 255, 255],
                           'placeholder': [160, 160, 160]}}})
    colors = bpy.context.preferences.themes[0].user_interface
    # Keep toolbar menu buttons at their original color: a translated ring can
    # touch them, and equal diagnostic backgrounds would merge pixel components.
    for item in (colors.wcol_menu_back, colors.wcol_menu_item):
        item.inner = item.inner_sel = (.8, .04, .65, 1)
    position = [0, 0]
    origin = [0, 0]
    scale = 1.0
    templates = {}
    template_bottoms = {}

    def event(kind, value='PRESS', point=None, **modifiers):
        if point is not None:
            position[:] = point
        win.event_simulate(type=kind, value=value, x=int(position[0]), y=int(position[1]), **modifiers)

    def capture(label):
        path = artifacts / (label + '.png')
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

    def template(label, factor):
        # Screenshot/UI redraws share font 0. Reestablish state even on cache hits.
        blf.disable(0, blf.WORD_WRAP)
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale * factor)
        key = (scale, factor, label)
        if key not in templates:
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10 * scale, 0)
            canvas = imbuf.new((int(440 * scale), int(45 * scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, label)
            path = root / ('compact-glyph-' + str(len(templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            picture = bpy.data.images.load(str(path), check_existing=False)
            try:
                width, height = picture.size
                alpha = np.asarray(picture.pixels[:], dtype=np.float32).reshape(height, width, 4)[:, :, 3] > .35
                yy, xx = np.nonzero(alpha)
                templates[key] = alpha[yy.min():yy.max()+1, xx.min():xx.max()+1].copy()
                template_bottoms[key] = int(yy.min())
            finally:
                bpy.data.images.remove(picture)
        return templates[key]

    def locate(pixels, rect, label, factor, required=True):
        x0, y0, x1, y1 = map(int, rect)
        x0 += 2
        y0 += 2
        ink = foreground(pixels[y0:y1-1, x0:x1-1])
        glyph = template(label, factor)
        gh, gw = glyph.shape
        if ink.shape[0] < gh or ink.shape[1] < gw:
            check(not required, 'Observed box cannot contain full label: ' + label)
            return None
        shape = (ink.shape[0]+gh-1, ink.shape[1]+gw-1)
        product = np.fft.rfft2(ink, s=shape) * np.fft.rfft2(glyph[::-1, ::-1], s=shape)
        hits = np.fft.irfft2(product, s=shape)[gh-1:ink.shape[0], gw-1:ink.shape[1]]
        summed = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        counts = summed[gh:, gw:]-summed[:-gh, gw:]-summed[gh:, :-gw]+summed[:-gh, :-gw]
        scores = 2*hits/(counts+np.count_nonzero(glyph))
        if label == 'Smooth':
            # At small sizes Smooth also correlates strongly with the suffix of
            # Unsmooth. Exclude the independently matched longer caption's row.
            longer = locate(pixels, rect, 'Unsmooth', factor, False)
            if longer:
                band = longer['text']
                scores[max(0, band[1]-y0-gh+1):min(scores.shape[0], band[3]-y0), :] = -1
        y, x = np.unravel_index(np.argmax(scores), scores.shape)
        score = float(scores[y, x])
        if score <= .750001 and not required:
            return None
        check(score > .75, 'Full caption missing/clipped: ' + repr((label, factor, score, rect)))
        return {'text': [int(x+x0), int(y+y0), int(x+x0+gw), int(y+y0+gh)], 'score': score,
                'baseline_y': int(y+y0)-template_bottoms[(scale, factor, label)]}

    def state():
        return (bpy.context.mode, bpy.context.active_object.name if bpy.context.active_object else None,
                tuple((o.name, o.select_get(), o.hide_get(), len(o.modifiers), tuple(o.location))
                      for o in bpy.context.view_layer.objects))

    def begin(name):
        origin[:] = [region.x + region.width/2, region.y + region.height/2]
        event('MOUSEMOVE', 'NOTHING', origin)
        yield from settle(3)
        if name in {'create', 'object'}:
            event('LEFT_SHIFT', shift=True)
            event('RIGHTMOUSE', shift=True)
        else:
            event('SPACE' if name == 'views' else 'W')
            yield from settle(13)
            event('LEFTMOUSE')
        yield from settle(9)
        check([op.bl_idname for op in win.modal_operators].count('VIEW3D_OT_axismeld_hotbox') == 1,
              'Expected exactly one native hotbox owner: ' + name)

    def cancel(name, before):
        # Clamped lower lists can cover the original press; release there could
        # execute a command. Escape explicitly cancels before any trigger release.
        event('ESC')
        event('ESC', 'RELEASE')
        yield from settle(3)
        if name in {'create', 'object'}:
            event('RIGHTMOUSE', 'RELEASE', shift=True)
            event('LEFT_SHIFT', 'RELEASE')
        else:
            event('LEFTMOUSE', 'RELEASE')
            event('SPACE' if name == 'views' else 'W', 'RELEASE')
        yield from settle()
        check(not list(win.modal_operators), 'Cancellation retained modal ownership')
        check(state() == before, 'Drawing/cancellation changed scene or selection')

    def backgrounds(pixels):
        return observed_menu_rectangles(menu_background_mask(pixels), 10*scale, 10*scale)

    def ring(pixels, name):
        boxes = [r for r in backgrounds(pixels) if 13*scale < r[3]-r[1] <= 27*scale and r[2]-r[0] > 35*scale]
        result = {}
        compact = dict(zip(('Perspective View', 'Side View', 'Front View', 'Top View', 'Left View',
                            'Back View', 'Bottom View'), ('Persp', 'Side', 'Front', 'Top', 'Left', 'Back', 'Bottom')))
        def matched_boxes(label, candidates):
            matches = [(r, locate(pixels, r, label, 1, False)) for r in candidates]
            matches = [(r, m) for r, m in matches if m]
            if not matches and name == 'views':
                matches = [(r, locate(pixels, r, compact[label], 1, False)) for r in candidates]
                matches = [(r, m) for r, m in matches if m]
            return matches
        north_matches = matched_boxes(RINGS[name]['N'], boxes)
        check(north_matches, 'No actual North caption for ' + name)
        north, _ = max(north_matches, key=lambda entry: entry[1]['score'])
        nx, ny = (north[0]+north[2])/2, (north[1]+north[3])/2
        south_boxes = [r for r in boxes if abs((r[0]+r[2])/2-nx) <= 20*scale
                       and 70*scale < ny-(r[1]+r[3])/2 < 180*scale]
        south_matches = matched_boxes(RINGS[name]['S'], south_boxes)
        check(south_matches, 'No actual South caption for ' + name)
        south, _ = max(south_matches, key=lambda entry: entry[1]['score'])
        cx = (north[0]+north[2]+south[0]+south[2])/4
        cy = (north[1]+north[3]+south[1]+south[3])/4
        for direction, label in RINGS[name].items():
            # Header labels such as Object Mode and Select Box share words with
            # this menu. Restrict caption searches to the observed N/S ring band.
            directional = []
            for rect in boxes:
                rx, ry = (rect[0]+rect[2])/2, (rect[1]+rect[3])/2
                if not (south[1]+south[3])/2 <= ry <= ny:
                    continue
                observed = ('N' if ry-cy > 16*scale else 'S' if ry-cy < -16*scale else '')
                observed += ('E' if rx-cx > 20*scale else 'W' if rx-cx < -20*scale else '')
                if observed == direction:
                    directional.append(rect)
            matches = matched_boxes(label, directional)
            check(matches, 'Actual radial caption missing: ' + repr((name, label)))
            # Similar View suffixes can give weaker partial correlations. The
            # complete caption's strongest match must still pass the same gate.
            rect, matched = max(matches, key=lambda entry: entry[1]['score'])
            options = [r for r in backgrounds(pixels) if 18*scale <= r[2]-r[0] <= 27*scale
                       and 0 <= r[0]-rect[2] <= 3*scale and abs(r[1]-rect[1]) <= 2*scale
                       and abs(r[3]-rect[3]) <= 2*scale]
            check(len(options) <= 1, 'Ambiguous independent radial Options')
            if options:
                rect = (rect[0], rect[1], options[0][2], rect[3])
            result[direction] = list(rect)
        check(len({tuple(r) for r in result.values()}) == len(result),
              'Different radial captions resolved to the same actual button')
        center = [(result['N'][0]+result['N'][2]+result['S'][0]+result['S'][2])/4,
                  (result['N'][1]+result['N'][3]+result['S'][1]+result['S'][3])/4]
        return {key: [r[0]-center[0], r[1]-center[1], r[2]-center[0], r[3]-center[1]]
                for key, r in result.items()}

    def observe_list(pixels, name, exclude=()):
        boxes = [r for r in backgrounds(pixels) if r[2]-r[0] > 100*scale
                 and r not in exclude and r[3]-r[1] > 27*scale]
        # A reflowed final column may contain one row; use observed sibling
        # width/top and adjacency to classify it, never a native column formula.
        for r in backgrounds(pixels):
            if r in boxes or r in exclude:
                continue
            if any(abs((r[2]-r[0])-(b[2]-b[0])) <= 2*scale and abs(r[3]-b[3]) <= 2*scale
                   and 0 <= r[0]-b[2] <= 10*scale for b in boxes):
                boxes.append(r)
        # Both known sizes are observed so the released build reaches the explicit
        # 16-to-18 geometry RED. A successful comparison requires the 18px font.
        candidates = []
        for factor in ((BASELINE_FONT_FACTOR,) if mode == 'record'
                       else (CURRENT_FONT_FACTOR, BASELINE_FONT_FACTOR)):
            rows = {}
            for label in LABELS[name]:
                matches = [(r, locate(pixels, r, label, factor, False)) for r in boxes]
                matches = [(r, m) for r, m in matches if m]
                if not matches:
                    print('CAPTION_CANDIDATES', name, factor, label, matches, flush=True)
                    break
                r, match = max(matches, key=lambda entry: entry[1]['score'])
                rows[label] = {'rect': list(r), **match}
            if len(rows) == len(LABELS[name]):
                # Weak matches of similar short labels must never reuse a row.
                bands = [(row['rect'][0], round((row['text'][1]+row['text'][3])/2))
                         for row in rows.values()]
                if len(set(bands)) != len(bands):
                    print('REJECT_DUPLICATE_ROWS', name, factor, rows, flush=True)
                    continue
                candidates.append((sum(r['score'] for r in rows.values()), factor, rows))
        check(candidates, 'Full companion captions missing/clipped: ' + repr((name, boxes)))
        _, factor, rows = max(candidates, key=lambda entry: entry[0])
        units = scale*factor
        for label, row in rows.items():
            x, y, xe, ye = row['text']
            rect = row['rect']
            cy = (y+ye)/2
            low, high = max(int(rect[1])+2, int(cy-9*units)), min(int(rect[3])-1, int(cy+9*units))
            left = max(int(rect[0])+2, int(x-22*units))
            icon = pixels[low:high, left:int(x-3*units), 1] > .18
            check(np.count_nonzero(icon) >= 8*units*units, 'Missing separate semantic icon: ' + label)
            check(xe < rect[2]-2, 'Caption touches/clips right menu edge: ' + label)
            if label in {'Interactive Creation', 'Exit On Completion', 'Shift Extrude', 'Shift Duplicate'}:
                state_ink = pixels[low:high, max(int(rect[0])+2, int(x-44*units)):int(x-23*units), 1] > .18
                check(np.count_nonzero(state_ink) >= 8*units*units,
                      'State glyph overlaps/missing beside semantic icon: ' + label)
            if label in {'Platonic Solid', 'Spherical Harmonics', 'Quad Draw Tool', 'Smooth'}:
                # Disabled native gear icons use the same reduced alpha as
                # semantic icons; the glyph score gate above is unchanged.
                right_ink = pixels[low:high, int(rect[2]-24*units):int(rect[2]-2*units), 1] > .18
                iy, ix = np.nonzero(right_ink)
                check(len(ix) > 8*units*units and ix.max()-ix.min() <= 18*units,
                      'Options gear clipped/missing: ' + label)
                check(xe+2 < rect[2]-24*units+int(ix.min()),
                      'Full caption overlaps independent Options gear: ' + label)
        grouped = {}
        for row in rows.values():
            grouped.setdefault(tuple(row['rect']), []).append(row['baseline_y'])
        pitches = [a-b for centers in grouped.values() for a, b in zip(sorted(centers, reverse=True),
                   sorted(centers, reverse=True)[1:])]
        check(pitches, 'No observed adjacent companion rows')
        # Measure actual rendered baselines, correcting only the independently
        # drawn glyph's crop offset. Descenders must not shorten apparent rows.
        # Separators increase the gap, so the minimum is ordinary row spacing.
        pitch = float(min(pitches))
        if mode == 'record':
            check(abs(pitch-ROW_HEIGHT_CONTRACT['baseline']*scale) <= 1.5,
                  'Released baseline is not the 16px build: ' + repr((name, scale, pitch)))
        result = {'font_factor': factor, 'pitch': pitch,
                  'widths': {label: row['rect'][2]-row['rect'][0] for label, row in rows.items()},
                  'rows': rows, 'columns': [list(r) for r in grouped]}
        print('COMPACT_MEASURE', name, scale, json.dumps(result), flush=True)
        return result

    with open(bpy.app.binary_path, 'rb') as stream:
        binary_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    result = {'schema': 1, 'mode': mode, 'status': 'RUNNING', 'binary': bpy.app.binary_path,
              'sha256': binary_hash, 'source': bpy.app.build_hash.decode(),
              'rowHeightContract': ROW_HEIGHT_CONTRACT,
              'scriptPath': str(Path(__file__).resolve()),
              'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': {}}
    if baseline:
        check(baseline['schema'] == 1, 'Unsupported baseline schema')
        check(baseline.get('rowHeightContract') == ROW_HEIGHT_CONTRACT,
              'Baseline must be recorded from the released 16px build for this 18px contract')
        check(baseline.get('mode') == 'record' and baseline.get('status') == 'BASELINE_RECORDED',
              'Baseline is not a completed record')
        result['baseline'] = {'path': str(baseline_path),
                              'sha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                              'binary': baseline['binary'], 'binarySha256': baseline['sha256']}
    for requested in (1.0, 1.5):
        bpy.context.preferences.view.ui_scale = requested
        yield from settle(12)
        refresh()
        scale = bpy.context.preferences.system.ui_scale
        check(abs(scale-requested) < .01, 'Requested UI scale not established')
        tag = 'scale-' + str(requested)
        result['cases'][tag] = current = {}
        for name in ('views', 'object', 'create', 'move'):
            hidden = None
            if name == 'create':
                hidden = [(o, o.hide_get(), o.select_get()) for o in bpy.context.view_layer.objects]
                active = bpy.context.view_layer.objects.active
                for obj, _, _ in hidden:
                    obj.select_set(False)
                    obj.hide_set(True)
                bpy.context.view_layer.objects.active = None
                yield from settle()
            before = state()
            yield from begin(name)
            pixels = capture(tag + '-' + name)
            current[name] = {'ring': ring(pixels, name), 'window': list(pixels.shape[1::-1]), 'ui_scale': scale}
            if name != 'views':
                current[name]['list'] = observe_list(pixels, name)
            if name == 'object':
                row = current[name]['list']['rows']['Mapping']['text']
                event('MOUSEMOVE', 'NOTHING', ((row[0]+row[2])/2, (row[1]+row[3])/2), shift=True)
                yield from settle(10)
                child = capture(tag + '-mapping-cascade')
                current['mapping'] = {'list': observe_list(child, 'mapping',
                    tuple(tuple(r) for r in current[name]['list']['columns']))}
            yield from cancel(name, before)
            if hidden:
                for obj, hide, selected in hidden:
                    obj.hide_set(hide)
                    obj.select_set(selected)
                bpy.context.view_layer.objects.active = active
                yield from settle()
        (artifacts / 'observed.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        if baseline:
            previous = baseline['cases'][tag]
            for name, case in current.items():
                old = previous[name]
                if 'ring' in case:
                    check(case['window'] == old['window'], 'Baseline and candidate window sizes differ')
                    for direction, rect in case['ring'].items():
                        check(all(abs(a-b) <= 2 for a, b in zip(rect, old['ring'][direction])),
                              'Radial/Views geometry changed: ' + repr((tag, name, direction, rect, old['ring'][direction])))
                if 'list' in case:
                    new_list, old_list = case['list'], old['list']
                    new_list['ratios'] = {label: width/old_list['widths'][label]
                                          for label, width in new_list['widths'].items()}
                    for label, width in new_list['widths'].items():
                        check(abs(width-old_list['widths'][label]*RELATIVE_SCALE) <= 2,
                              'Companion width did not scale from 16px to 18px: ' + repr((tag, name, label, width, old_list['widths'][label])))
                    check(abs(new_list['pitch']-old_list['pitch']*RELATIVE_SCALE) <= 1.5,
                          'Companion row spacing did not scale to 18px: ' + repr((tag, name, new_list['pitch'], old_list['pitch'])))
                    check(abs(new_list['pitch']-ROW_HEIGHT_CONTRACT['current']*scale) <= 1.5,
                          'Companion absolute row height is not 18px times UI scale: ' + repr((tag, name, new_list['pitch'])))
                    check(new_list['font_factor'] == CURRENT_FONT_FACTOR,
                          'Companion font does not match 18px rows: ' + name)
    if mode == 'record':
        result['status'] = 'BASELINE_RECORDED'
        baseline_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
        (artifacts / 'observed.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print('AXISMELD_COMPACT_COMPANION_BASELINE_RECORDED', flush=True)
    else:
        result['status'] = 'PASS'
        (artifacts / 'observed.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print('AXISMELD_COMPACT_COMPANION_EVENTS_PASS', flush=True)


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

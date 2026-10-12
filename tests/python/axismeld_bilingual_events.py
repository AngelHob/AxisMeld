# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bilingual representative GUI acceptance in a disposable event-simulated process.

AXISMELD_BILINGUAL_MODE=main (default) checks 100%/150%, English -> Chinese ->
English, public hotbox gestures and three representative native menus.
AXISMELD_BILINGUAL_MODE=reason checks the actual Chinese history explanation;
AXISMELD_REASON_NO_FIT=1 requires zero new explanation ink in the runner's small
window. AXISMELD_REASON_RESTORE=1 then enlarges the real window and requires the
same complete explanation to reappear. No native layout coordinates are read.

Expected captions come from stable IDs and Blender's translation API. Geometry,
input targets, line pitch, Options cells and clipping come from rendered pixels.
This is representative GUI evidence, not screenshots of every menu or button.
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
from mathutils import Quaternion

sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import menu_background_mask, observed_menu_rectangles, observed_radial_rectangles
from axismeld import hotbox_runtime
from axismeld.translations import iface, tip

ROOT = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
ART = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', ROOT)).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(ROOT), 'Requires disposable runner isolation'
ART.mkdir(parents=True, exist_ok=True)
MODE = os.environ.get('AXISMELD_BILINGUAL_MODE', 'main')
assert MODE in {'main', 'reason'}
NO_FIT = os.environ.get('AXISMELD_REASON_NO_FIT') == '1'
RESTORE = os.environ.get('AXISMELD_REASON_RESTORE') == '1'
assert not RESTORE or NO_FIT
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False
bpy.context.preferences.view.smooth_view = 0

RECORD = {'schema': 1, 'mode': MODE, 'status': 'RUNNING', 'cases': [],
          'coverageBoundary': 'Representative public gestures and menus; not every menu or operator',
          'geometrySource': 'Screenshot background components and independently rasterized BLF glyphs',
          'nativeLayoutCoordinatesRead': False, 'manualResultsChanged': False}


def write_record():
    (ART / 'bilingual-events.json').write_text(json.dumps(RECORD, ensure_ascii=False, indent=2), encoding='utf-8')


def settle(count=8):
    for _ in range(count):
        yield


def intersects(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


class Observer:
    def __init__(self, window):
        self.win = window
        self.position = [0, 0]
        self.templates = {}
        self.offsets = {}
        self.refresh()

    def refresh(self):
        self.area = max((a for a in self.win.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width*a.height)
        self.region = next(r for r in self.area.regions if r.type == 'WINDOW')
        self.scale = bpy.context.preferences.system.ui_scale

    def override(self):
        return bpy.context.temp_override(window=self.win, area=self.area, region=self.region)

    def rect(self):
        r = self.region
        return (r.x, r.y, r.x+r.width, r.y+r.height)

    def origin(self):
        r = self.region
        return (r.x+r.width/2, r.y+r.height/2)

    def event(self, kind, value='PRESS', point=None, **kwargs):
        if point is not None:
            self.position[:] = map(round, point)
        self.win.event_simulate(type=kind, value=value, x=self.position[0], y=self.position[1], **kwargs)

    def shot(self, name):
        path = ART / (name + '.png')
        with self.override():
            bpy.ops.screen.screenshot(filepath=str(path))
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            w, h = image.size
            pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(h, w, 4).copy()
        finally:
            bpy.data.images.remove(image)
        print('SCREENSHOT', path, flush=True)
        return pixels

    def glyph(self, label, factor=1):
        blf.disable(0, blf.WORD_WRAP)
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * self.scale * factor)
        key = (self.scale, factor, label)
        if key not in self.templates:
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10*self.scale, 0)
            canvas = imbuf.new((int(blf.dimensions(0, label)[0])+16, int(45*self.scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, label)
            path = ROOT / ('bilingual-glyph-' + str(len(self.templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            image = bpy.data.images.load(str(path), check_existing=False)
            try:
                w, h = image.size
                alpha = np.asarray(image.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, 3] > .35
                yy, xx = np.nonzero(alpha)
                assert len(xx), ('BLF could not rasterize actual caption', label)
                self.templates[key] = alpha[yy.min():yy.max()+1, xx.min():xx.max()+1].copy()
                self.offsets[key] = int(yy.min())
            finally:
                bpy.data.images.remove(image)
        return self.templates[key]

    def match(self, ink, label, factor=1):
        reference = self.glyph(label, factor)
        gh, gw = reference.shape
        if ink.shape[0] < gh or ink.shape[1] < gw:
            return 0.0, (0, 0, gw, gh)
        shape = (ink.shape[0]+gh-1, ink.shape[1]+gw-1)
        hits = np.fft.irfft2(np.fft.rfft2(ink, s=shape)*np.fft.rfft2(reference[::-1, ::-1], s=shape), s=shape)
        hits = hits[gh-1:ink.shape[0], gw-1:ink.shape[1]]
        summed = np.pad(ink.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        counts = summed[gh:, gw:]-summed[:-gh, gw:]-summed[gh:, :-gw]+summed[:-gh, :-gw]
        scores = 2*hits/(counts+np.count_nonzero(reference))
        y, x = np.unravel_index(np.argmax(scores), scores.shape)
        return float(scores[y, x]), (int(x), int(y), int(x+gw), int(y+gh))

    def locate(self, pixels, label, rect=None, factor=1, required=True, green=False, excluded=()):
        x0, y0, x1, y1 = map(int, rect or (0, 0, pixels.shape[1], pixels.shape[0]))
        rgb = pixels[y0:y1, x0:x1, :3]
        best = (0, (0, 0, 0, 0))
        for level in (.18, .3, .5):
            ink = ((rgb[:, :, 1] > .35) & (rgb[:, :, 1] > 2*np.maximum(rgb[:, :, 0], rgb[:, :, 2]))
                   if green else np.min(rgb, axis=2) > level)
            for ex0, ey0, ex1, ey1 in excluded:
                ink[max(0, ey0-y0):min(y1-y0, ey1-y0), max(0, ex0-x0):min(x1-x0, ex1-x0)] = False
            candidate = self.match(ink, label, factor)
            if candidate[0] > best[0]:
                best = candidate
        if best[0] <= .75 and not required:
            return None
        assert best[0] > .75, ('Full rendered caption missing or clipped', label, factor, best[0], rect)
        a, b, c, d = best[1]
        box = [a+x0, b+y0, c+x0, d+y0]
        baseline = box[1]-self.offsets[(self.scale, factor, label)]
        return {'label': label, 'text': box, 'baseline_y': baseline, 'score': best[0],
                'blf_advance_width': float(blf.dimensions(0, label)[0]), 'font_factor': factor}

    def boxes(self, pixels, minimum_width=10, minimum_height=10):
        return observed_menu_rectangles(menu_background_mask(pixels), minimum_width*self.scale, minimum_height*self.scale)

    def nodes(self):
        with self.override():
            document = json.loads(hotbox_runtime.snapshot(bpy.context))
        pending = list(document['menus'])
        result = {}
        while pending:
            node = pending.pop()
            result[node['id']] = node
            pending.extend(node['children'])
        return result

    def ring(self, pixels, root_id, nodes, *, whole_window=False):
        # Expected strings/IDs are public snapshot content. No positions or native
        # widths are available in that document or used by this observation.
        children = [n for n in nodes[root_id]['children'] if n.get('direction')]
        if root_id == 'views':
            # Views has implicit directions in its published layout contract.
            # These identify labels, not expected coordinates or native widths.
            directions = {'view.perspective': 'N', 'view.side': 'E', 'view.bottom': 'SE',
                          'view.front': 'S', 'view.back': 'SW', 'view.top': 'W', 'view.left': 'NW'}
            children = [dict(n, direction=directions[n['command']]) for n in nodes[root_id]['children']
                        if n.get('command') in directions]
        x0, y0, x1, y1 = (0, 0, pixels.shape[1], pixels.shape[0]) if whole_window else map(int, self.rect())
        observed = observed_radial_rectangles(pixels[y0:y1, x0:x1], self.scale, [n['direction'] for n in children])
        rectangles = {direction: [r[0]+x0, r[1]+y0, r[2]+x0, r[3]+y0]
                      for direction, r in observed['rects'].items()}
        captions = {}
        for node in children:
            rect = rectangles[node['direction']]
            caption = self.locate(pixels, iface(node['label']), rect)
            captions[node['id']] = caption
        # Same independently observed minimum-clearance contract used by the
        # roomy/Views acceptance. Include visibly separate radial Options cells.
        expanded = dict(rectangles)
        for direction, rect in rectangles.items():
            option = [r for r in self.boxes(pixels) if 18*self.scale <= r[2]-r[0] <= 27*self.scale
                      and 0 <= r[0]-rect[2] <= 3*self.scale
                      and abs(r[1]-rect[1]) <= 2*self.scale and abs(r[3]-rect[3]) <= 2*self.scale]
            assert len(option) <= 1, ('Ambiguous radial Options', root_id, direction)
            if option:
                expanded[direction] = [rect[0], rect[1], option[0][2], rect[3]]
        gaps = {}
        for left, right in (('NW', 'NE'), ('W', 'E'), ('SW', 'SE')):
            if left in expanded and right in expanded:
                gap = (expanded[right][0]-expanded[left][2])/self.scale
                assert gap >= 4, ('Observed radial buttons overlap or violate clear space', root_id, left, right, gap)
                gaps[left+'-'+right] = gap
        for a, first in expanded.items():
            for b, second in expanded.items():
                if a < b:
                    assert not intersects(first, second), ('Observed radial buttons overlap', root_id, a, b)
        return {'root_id': root_id, 'rectangles': expanded, 'horizontalClearances': gaps, 'captions': captions}

    def companion(self, pixels, nodes, root_id, sources, options_source=None, raw_names=()):
        candidates = [r for r in self.boxes(pixels) if r[2]-r[0] > 100*self.scale and r[3]-r[1] > 27*self.scale]
        rows = {}
        for source in sources:
            label = source if source in raw_names else iface(source)
            matches = []
            for rect in candidates:
                excluded = []
                for other in sources:
                    longer = other if other in raw_names else iface(other)
                    if longer != label and label in longer:
                        match = self.locate(pixels, longer, rect, .75, False)
                        if match:
                            a, b, c, d = match['text']
                            excluded.append((rect[0], b-1, rect[2], d+1))
                matches.append((rect, self.locate(pixels, label, rect, .75, False, excluded=excluded)))
            matches = [(r, m) for r, m in matches if m]
            assert matches, ('Full 18px companion caption missing', root_id, source, label, candidates)
            rect, match = max(matches, key=lambda value: value[1]['score'])
            rows[source] = {'rect': list(rect), **match}
            assert match['text'][2] < rect[2]-2, ('Full caption clips right column edge', source, rect, match)
        grouped = {}
        bands = [(row['rect'][0], round((row['text'][1]+row['text'][3])/2)) for row in rows.values()]
        assert len(set(bands)) == len(bands), ('Distinct companion captions resolved to one row', root_id, rows)
        for row in rows.values():
            grouped.setdefault(tuple(row['rect']), []).append(row['baseline_y'])
        pitches = [a-b for values in grouped.values() for a, b in zip(sorted(values, reverse=True), sorted(values, reverse=True)[1:])]
        assert pitches and abs(min(pitches)-18*self.scale) <= 1.5, ('Actual 18px row pitch changed', root_id, self.scale, pitches)
        options = None
        if options_source:
            row = rows[options_source]
            rect = row['rect']; x, y, xe, ye = row['text']; units = .75*self.scale
            low, high = max(int(rect[1])+2, int((y+ye)/2-9*units)), min(int(rect[3])-1, int((y+ye)/2+9*units))
            start = int(rect[2]-24*units)
            ink = pixels[low:high, start:int(rect[2]-2*units), 1] > .18
            iy, ix = np.nonzero(ink)
            assert len(ix) > 8*units*units and ix.max()-ix.min() <= 18*units, ('Independent Options gear clipped or missing', options_source)
            assert xe+2 < start+int(ix.min()), ('Full caption overlaps Options gear', options_source)
            options = {'source': options_source, 'ink_bounds': [start+int(ix.min()), low+int(iy.min()), start+int(ix.max())+1, low+int(iy.max())+1],
                       'column_right': rect[2]}
        return {'root_id': root_id, 'rows': rows, 'pitch': min(pitches), 'options': options,
                'stable_ids': [n['id'] for n in nodes[root_id]['children']]}


def state():
    active = bpy.context.view_layer.objects.active
    return {'active': active.name if active else None, 'mode': bpy.context.mode,
            'objects': sorted((o.name, o.type, o.select_get(), o.hide_get(), tuple(o.location), len(o.modifiers)) for o in bpy.context.scene.objects)}


def profile(observer, rows=False):
    with observer.override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'style': 'rows' if rows else 'center', 'rows': ['common', 'pane', 'modeling'] if rows else [],
            'transparency': 0, 'center_buttons': {'LEFTMOUSE': 'views'},
            'appearance': {'theme_background': False, 'background': [204, 10, 166], 'brightness': 0,
                           'text': [255, 255, 255], 'placeholder': [160, 160, 160]}}})


def cancel(observer, key=None, mouse=None, shift=False):
    observer.event('ESC'); yield from settle(3)
    observer.event('ESC', 'RELEASE')
    if mouse: observer.event(mouse, 'RELEASE', shift=shift)
    if key: observer.event(key, 'RELEASE')
    if shift: observer.event('LEFT_SHIFT', 'RELEASE')
    yield from settle()
    assert not list(observer.win.modal_operators), 'Cancel retained modal ownership'


def open_hotbox(observer, key=None, mouse='LEFTMOUSE', shift=False):
    observer.event('MOUSEMOVE', 'NOTHING', observer.origin()); yield from settle(3)
    if key:
        observer.event(key); yield from settle(13)
    if shift:
        observer.event('LEFT_SHIFT', shift=True)
    if mouse:
        observer.event(mouse, shift=shift)
    yield from settle(10)
    assert [o.bl_idname for o in observer.win.modal_operators].count('VIEW3D_OT_axismeld_hotbox') == 1


def activate_language(observer, language):
    view = bpy.context.preferences.view
    view.language = language
    view.use_translate_interface = True
    view.use_translate_tooltips = True
    for area in observer.win.screen.areas:
        area.tag_redraw()
    yield from settle(16)
    observer.refresh()
    assert view.language == language and bpy.app.translations.locale == language, (view.language, bpy.app.translations.locale)
    assert (iface('Edit Mesh') == 'Edit Mesh') == (language == 'en_US')
    RECORD.setdefault('languageSequence', []).append(language)


def main_suite(observer):
    win = observer.win
    win.workspace = bpy.data.workspaces['Modeling']; yield from settle(14); observer.refresh()
    with observer.override():
        bpy.ops.screen.screen_full_area()
    yield from settle(12); observer.refresh()
    observer.area.spaces.active.show_region_ui = False
    observer.area.spaces.active.show_region_toolbar = False
    observer.region.data.view_rotation = Quaternion((1, 0, 0, 0))
    observer.region.data.view_location = (0, 0, 0)
    observer.region.data.view_distance = 10
    observer.region.data.view_perspective = 'ORTHO'
    cube = bpy.data.objects['Cube']
    for requested in (1.0, 1.5):
        bpy.context.preferences.view.ui_scale = requested; yield from settle(14); observer.refresh()
        assert abs(observer.scale-requested) < .01
        for language in ('en_US', 'zh_HANS'):
            yield from activate_language(observer, language)
            tag = language+'-'+str(requested)
            with observer.override():
                if cube.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
                for obj in bpy.context.scene.objects:
                    obj.hide_set(False); obj.select_set(obj == cube)
                bpy.context.view_layer.objects.active = cube
            yield from settle()
            profile(observer, rows=True)
            before = state(); yield from open_hotbox(observer, 'SPACE', mouse=None)
            pixels = observer.shot(tag+'-space')
            roots = ('File', 'Edit', 'Create', 'Select', 'Modify', 'Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display', 'Curves', 'Surfaces')
            captions = [observer.locate(pixels, iface(s), observer.rect()) for s in roots]
            RECORD['cases'].append({'case': 'Space', 'language': language, 'scale': observer.scale, 'captions': captions})
            yield from cancel(observer, 'SPACE'); assert state() == before
            profile(observer)
            for case, key, mouse, shift, root_id in (
                    ('Views', 'SPACE', 'LEFTMOUSE', False, 'views'),
                    ('Q', 'Q', 'LEFTMOUSE', False, 'tools.select'),
                    ('W', 'W', 'LEFTMOUSE', False, 'tools.move'),
                    ('E', 'E', 'LEFTMOUSE', False, 'tools.rotate'),
                    ('R', 'R', 'LEFTMOUSE', False, 'tools.scale'),
                    ('Object', None, 'RIGHTMOUSE', True, 'context.modeling_object')):
                before = state(); nodes = observer.nodes()
                yield from open_hotbox(observer, key, mouse, shift)
                pixels = observer.shot(tag+'-'+case)
                record = {'case': case, 'language': language, 'scale': observer.scale,
                          'ring': observer.ring(pixels, root_id, nodes)}
                if case == 'Object':
                    record['list'] = observer.companion(pixels, nodes, 'context.modeling_object_menu',
                        ('Offset Edge Loop Tool', 'Smooth', 'Unsmooth', 'Subdiv Proxy', 'Crease Tool'), 'Smooth')
                elif case in {'W', 'E', 'R'}:
                    companion = 'tools.'+{'W':'move','E':'rotate','R':'scale'}[case]+'_menu'
                    record['list'] = observer.companion(pixels, nodes, companion,
                        ('Selection Constraints', 'Transform Constraints', 'Shift Extrude', 'Shift Duplicate'))
                RECORD['cases'].append(record); write_record()
                yield from cancel(observer, key, mouse, shift); assert state() == before
            with observer.override():
                for obj in bpy.context.scene.objects:
                    obj.select_set(False); obj.hide_set(True)
                bpy.context.view_layer.objects.active = None
            yield from settle(); before = state(); nodes = observer.nodes()
            yield from open_hotbox(observer, mouse='RIGHTMOUSE', shift=True)
            pixels = observer.shot(tag+'-Create')
            RECORD['cases'].append({'case': 'Create', 'language': language, 'scale': observer.scale,
                'ring': observer.ring(pixels, 'context.create', nodes),
                'list': observer.companion(pixels, nodes, 'context.create_menu',
                    ('Platonic Solid', 'Pyramid', 'Prism', 'Pipe', 'Helix', 'Gear'), 'Platonic Solid')})
            yield from cancel(observer, mouse='RIGHTMOUSE', shift=True); assert state() == before
            with observer.override():
                for obj in bpy.context.scene.objects: obj.hide_set(False)
                cube.select_set(True); bpy.context.view_layer.objects.active = cube
            yield from settle(); before = state(); nodes = observer.nodes()
            yield from open_hotbox(observer, mouse='RIGHTMOUSE')
            pixels = observer.shot(tag+'-RMB-Components')
            record = {'case': 'RMB Components', 'language': language, 'scale': observer.scale,
                      'ring': observer.ring(pixels, 'context.components', nodes)}
            record['list'] = observer.companion(pixels, nodes, 'context.component_menu',
                ('Cube...', 'Select', 'Select All', 'Deselect All', 'Select Hierarchy', 'Invert Selection'), raw_names=('Cube...',))
            assert cube.name == 'Cube', 'Language switched a user data name'
            record['userName'] = cube.name; RECORD['cases'].append(record)
            yield from cancel(observer, mouse='RIGHTMOUSE'); assert state() == before
            write_record()
        yield from activate_language(observer, 'en_US')
        pixels = observer.shot('en_US-'+str(requested)+'-restored')
        header = next(r for r in observer.area.regions if r.type == 'HEADER')
        restored = observer.locate(pixels, 'Edit Mesh',
            (header.x, header.y, header.x+header.width, header.y+header.height))
        RECORD['cases'].append({'case': 'English restored Modeling header', 'scale': observer.scale, 'caption': restored})
    # Restore the real workspace screen; representative menu roots then use
    # their actual VIEW_3D header, preserving normal native menu invocation.
    with observer.override(): bpy.ops.screen.screen_full_area()
    yield from settle(12); observer.refresh()
    for requested in (1.0, 1.5):
        bpy.context.preferences.view.ui_scale = requested; yield from settle(14); observer.refresh()
        for language in ('en_US', 'zh_HANS'):
            yield from activate_language(observer, language)
            for workspace, root, labels in (
                    ('Modeling', 'Edit Mesh', ('Vertex', 'Edge', 'Face')),
                    ('Rigging', 'Skeleton', ('Joints', 'IK', 'Edit Bones')),
                    ('Rigging', 'Skin', ('Bind', 'Weight Maps', 'Weights'))):
                win.workspace = bpy.data.workspaces[workspace]; yield from settle(14); observer.refresh()
                header = next(r for r in observer.area.regions if r.type == 'HEADER')
                before = state(); pixels = observer.shot(language+'-'+str(requested)+'-'+root+'-before')
                target = observer.locate(pixels, iface(root), (header.x, header.y, header.x+header.width, header.y+header.height))['text']
                point = ((target[0]+target[2])/2, (target[1]+target[3])/2)
                observer.event('MOUSEMOVE', 'NOTHING', point); yield from settle(2)
                observer.event('LEFTMOUSE'); yield from settle(2)
                observer.event('LEFTMOUSE', 'RELEASE'); yield from settle(12)
                pixels = observer.shot(language+'-'+str(requested)+'-'+root)
                boxes = observer.boxes(pixels, 35, 27)
                assert boxes, ('Native menu popup not observed', root)
                observed = []
                for label in labels:
                    matches = [observer.locate(pixels, iface(label), rect, required=False) for rect in boxes]
                    matches = [m for m in matches if m]
                    assert matches, ('Representative native menu caption missing', root, label)
                    observed.append(max(matches, key=lambda m: m['score']))
                RECORD['cases'].append({'case': 'Native '+root, 'language': language, 'scale': observer.scale,
                                        'captions': observed, 'observedPopupRectangles': boxes})
                yield from cancel(observer); assert state() == before
                write_record()
        yield from activate_language(observer, 'en_US')
        pixels = observer.shot('en_US-'+str(requested)+'-native-restored')
        header = next(r for r in observer.area.regions if r.type == 'HEADER')
        bounds = (header.x, header.y, header.x+header.width, header.y+header.height)
        restored = [observer.locate(pixels, label, bounds) for label in ('Skeleton', 'Skin')]
        RECORD['cases'].append({'case': 'English restored Rigging header', 'scale': observer.scale, 'captions': restored})


def reason_suite(observer):
    bpy.context.preferences.view.ui_scale = float(os.environ.get('AXISMELD_REASON_SCALE', '1.5'))
    yield from settle(14); observer.refresh()
    yield from activate_language(observer, 'zh_HANS')
    profile(observer)
    # Use an actual eligible history target. A plain factory cube has no stack
    # to bake, so its short prerequisite message cannot exercise long-text fit.
    # This modifier is fixture data in the isolated scene and is never applied.
    with observer.override():
        target = bpy.context.active_object
        assert target is not None and target.type == 'MESH'
        target.modifiers.new('Bilingual explanation fixture', 'TRIANGULATE')
    theme = bpy.context.preferences.themes[0].user_interface
    theme.wcol_menu_back.inner = (.08, .08, .65, 1)
    theme.wcol_menu_back.inner_sel = (.08, .08, .65, 1)
    theme.wcol_menu_back.text = (0, 1, 0)
    node_id = 'context.history.delete_non_deformer'

    def green(pixels):
        rgb = pixels[:, :, :3]
        return (rgb[:, :, 1] > .35) & (rgb[:, :, 1] > 2*np.maximum(rgb[:, :, 0], rgb[:, :, 2]))

    def blue(pixels):
        rgb = pixels[:, :, :3]
        return (rgb[:, :, 2] > .25) & (rgb[:, :, 2] > 2.2*np.maximum(rgb[:, :, 0], rgb[:, :, 1]))

    def read_reason(ink, reason, x_offset, y_offset):
        # Consume every non-space Unicode character across observed BLF lines;
        # retain the established >.75 full-glyph threshold and crop tolerances.
        observer.glyph(reason)
        occupied = np.flatnonzero(np.any(ink, axis=1))
        # CJK glyphs occupy more of the line cell than Latin glyphs. Split at
        # observed empty raster rows; a DPI-scaled gap merges distinct CJK lines.
        bands = list(reversed([b for b in np.split(occupied, np.flatnonzero(np.diff(occupied)>1)+1) if len(b)]))
        for start in range(len(bands)):
            consumed, lines = 0, []
            for band in bands[start:]:
                row = ink[max(0, int(band[0])-2):int(band[-1])+3]
                columns = np.flatnonzero(np.any(row, axis=0))
                actual_width = int(columns[-1]-columns[0]+1)
                candidates = []
                for end in range(consumed+1, len(reason)+1):
                    text = reason[consumed:end]
                    if text[-1].isspace(): continue
                    observer.glyph(text)
                    if abs(blf.dimensions(0, text)[0]-actual_width)>8*observer.scale: continue
                    if abs(observer.glyph(text).shape[1]-actual_width)>3: continue
                    score, _ = observer.match(row, text)
                    candidates.append((score, end, text))
                if not candidates or max(candidates)[0] <= .75: break
                score, consumed, text = max(candidates)
                lines.append({'text': text, 'score': score, 'bounds': [int(columns[0])+x_offset, int(band[0])+y_offset,
                    int(columns[-1])+1+x_offset, int(band[-1])+1+y_offset]})
                while consumed<len(reason) and reason[consumed].isspace(): consumed += 1
                if consumed == len(reason): return lines
        return None

    def one_case(tag, expect_no_fit):
        before = state(); nodes = observer.nodes(); node = nodes[node_id]
        assert node['enabled'], 'Long-history fixture must pass the real capability check'
        reason = tip(node['reason'])
        assert len(reason) >= 80, 'Long explanation fixture unexpectedly resolved to a prerequisite'
        assert any('\u3400'<=c<='\u9fff' for c in reason), ('Expected actual Chinese explanation', reason)
        yield from open_hotbox(observer, 'A')
        pixels = observer.shot(tag+'-open')
        ring = observer.ring(pixels, 'context.history', nodes, whole_window=True)
        north, south = ring['rectangles']['N'], ring['rectangles']['S']
        neutral = ((north[0]+north[2]+south[0]+south[2])/4, (north[1]+north[3]+south[1]+south[3])/4)
        observer.event('MOUSEMOVE', 'NOTHING', neutral); yield from settle()
        protected = observer.shot(tag+'-neutral')
        rectangles = observer.boxes(protected)
        captions = list(ring['captions'].values())
        # Confirm actual pre-hover captions before relying on their pixel bounds.
        for caption in captions:
            observer.locate(protected, caption['label'], caption['text'])
        target = ring['captions'][node_id]['text']
        observer.event('MOUSEMOVE', 'NOTHING', ((target[0]+target[2])/2, (target[1]+target[3])/2)); yield from settle()
        pixels = observer.shot(tag+'-hover')
        record = {'case': 'Chinese history explanation', 'node_id': node_id, 'reason': reason,
                  'scale': observer.scale, 'window': [pixels.shape[1], pixels.shape[0]],
                  'expectNoFit': expect_no_fit, 'protectedMenuRectangles': rectangles}
        if expect_no_fit:
            new_ink = green(pixels) & ~green(protected)
            record['newExplanationInkPixels'] = int(np.count_nonzero(new_ink))
            assert not np.any(new_ink), ('No-fit explanation must be hidden', record)
        else:
            complete = panel = None
            for rect in observed_menu_rectangles(blue(pixels), 3*observer.scale, 3*observer.scale):
                x0, y0, x1, y1 = rect
                complete = read_reason(green(pixels)[y0:y1, x0:x1], reason, x0, y0)
                if complete:
                    panel = rect; break
            assert complete, ('Complete actual Chinese explanation not readable', reason)
            assert not any(intersects(panel, rect) for rect in rectangles), ('Explanation covered menu backdrop', panel, rectangles)
            for line in complete:
                bounds = line['bounds']
                assert not any(intersects(bounds, rect) for rect in rectangles), ('Explanation ink covered menu', bounds)
                assert (bounds[0]>=8*observer.scale and bounds[2]<=pixels.shape[1]-8*observer.scale and
                        bounds[1]>=8*observer.scale and bounds[3]<=pixels.shape[0]-8*observer.scale), ('Explanation crossed safe margin', bounds)
            record.update({'lines': complete, 'panel': panel})
        for caption in captions:
            observer.locate(pixels, caption['label'], caption['text'])
        RECORD['cases'].append(record); write_record()
        yield from cancel(observer, 'A', 'LEFTMOUSE'); assert state() == before
        return record

    small = yield from one_case('zh-reason', NO_FIT)
    if RESTORE:
        with observer.override(): assert bpy.ops.wm.window_fullscreen_toggle() == {'FINISHED'}
        yield from settle(16); observer.refresh()
        large = yield from one_case('zh-reason-restored', False)
        assert any(a>b for a, b in zip(large['window'], small['window'])) and all(a>=b for a, b in zip(large['window'], small['window']))
        assert large['reason'] == small['reason'] and large['node_id'] == small['node_id']
        RECORD['restoredAfterRealWindowResize'] = True


def suite():
    observer = Observer(bpy.context.window)
    preset = next(Path(p)/'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p)/'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    theme = bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu_back, theme.wcol_menu_item):
        colors.inner = colors.inner_sel = (.8, .04, .65, 1)
    scripts = Path(bpy.utils.system_resource('SCRIPTS'))
    resources = {p.relative_to(scripts).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (scripts/'modules/axismeld').glob('*.py')}
    RECORD.update({'binary': bpy.app.binary_path, 'binarySha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                   'buildHash': bpy.app.build_hash.decode(), 'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'resources': resources})
    write_record(); yield from settle()
    if MODE == 'main': yield from main_suite(observer)
    else: yield from reason_suite(observer)
    RECORD['status'] = 'PASS'; write_record()
    print('AXISMELD_BILINGUAL_EVENTS_PASS', MODE, flush=True)


steps = suite()

def tick():
    try:
        next(steps)
        return .025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        RECORD['status'] = 'FAIL'; write_record()
        traceback.print_exc(); sys.stdout.flush(); sys.stderr.flush()
        os._exit(1)
    return None

bpy.app.timers.register(tick, first_interval=1)

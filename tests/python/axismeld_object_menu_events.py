# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Object/preselect input, persistent strokes, undo and rendered clearance.

Run only through the disposable GUI runner. The first assertion intentionally uses
the old public input API, so an older installation fails on missing behavior before
any newly introduced module or selector could cause an import error.
"""
import json
import os
from pathlib import Path
import sys
import traceback

import numpy as np
import imbuf

import blf
import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.edit.use_global_undo = True
bpy.context.preferences.edit.use_enter_edit_mode = False

MODEL = 'context.modeling_hotbox'
CREATE = 'context.create_hotbox'
OBJECT = 'context.modeling_object'
COMPANION = 'context.modeling_object_menu'
MAIN_LABELS = (
    'Offset Edge Loop Tool', 'Smooth', 'Unsmooth', 'Subdiv Proxy', 'Crease Tool',
    'Project Curve on Mesh', 'Split Mesh with Projected Curve', 'Mirror', 'Mapping',
    'Triangulate', 'Quadrangulate', 'Reduce', 'Remesh', 'Retopologize',
    'Transfer Vertex Order', 'Separate', 'Combine', 'Booleans', 'Cleanup',
    'Connect Tool', 'Quad Draw Tool', 'Polygon Display')
PLANE = [(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)]


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=5):
    for _ in range(count):
        yield


def rounded(co):
    return tuple(round(float(value), 5) for value in co)


def mesh_state(obj):
    """Geometry and selected domains survive undo even if BMesh indices reorder."""
    owned = obj.mode != 'EDIT'
    bm = bmesh.new() if owned else bmesh.from_edit_mesh(obj.data)
    if owned:
        bm.from_mesh(obj.data)
    try:
        return (
            tuple(sorted((rounded(v.co), v.select, v.hide) for v in bm.verts)),
            tuple(sorted((tuple(sorted(rounded(v.co) for v in e.verts)), e.select, e.hide)
                         for e in bm.edges)),
            tuple(sorted((tuple(sorted(rounded(v.co) for v in f.verts)), f.select, f.hide)
                         for f in bm.faces)))
    finally:
        if owned:
            bm.free()


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    position = [region.x + region.width / 2, region.y + region.height / 2]
    origin = position.copy()
    scale = bpy.context.preferences.system.ui_scale
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'Maya preset activation failed')
    yield from settle(8)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def event(kind, value='PRESS', point=None, **modifiers):
        if point is not None:
            position[:] = point
        if value == 'PRESS' and kind in {'ZERO', 'ONE', 'TWO', 'PERIOD'}:
            # Numeric operators consume UTF-8 input, not just the key enum.
            modifiers.setdefault('unicode', {'ZERO': '0', 'ONE': '1', 'TWO': '2', 'PERIOD': '.'}[kind])
        win.event_simulate(type=kind, value=value, x=int(position[0]), y=int(position[1]), **modifiers)

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def idle(label):
        check(not modals(), label + ' left modal ownership: ' + repr(modals()))

    def midpoint():
        return [region.x + region.width / 2, region.y + region.height / 2]

    def state():
        return (bpy.context.mode, tuple(bpy.context.tool_settings.mesh_select_mode),
                bpy.context.active_object.name if bpy.context.active_object else None,
                tuple(sorted((obj.name, obj.type, obj.mode, obj.select_get(),
                              rounded(v for row in obj.matrix_world for v in row),
                              mesh_state(obj) if obj.type == 'MESH' else (),
                              tuple((m.name,m.type,tuple((key,str(getattr(m,key))) for key in
                                    ('levels','render_levels','ratio','mode','voxel_size','operation','solver')
                                    if hasattr(m,key))) for m in obj.modifiers))
                             for obj in bpy.context.scene.objects)))

    def clear():
        with override():
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for obj in tuple(bpy.context.scene.objects):
                bpy.data.objects.remove(obj, do_unlink=True)

    def seed(domain='FACE', coordinates=PLANE, faces=((0, 1, 2, 3),), edges=(),
             selection=None, name='M2d Mesh'):
        clear()
        with override():
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(coordinates, edges, faces)
            mesh.update()
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.collection.objects.link(obj)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            for vert in mesh.vertices:
                vert.select = True
            bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        return obj.name

    def topology(name):
        bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
        return len(bm.verts), len(bm.edges), len(bm.faces)

    def face_area(name):
        return sum(face.calc_area() for face in bmesh.from_edit_mesh(bpy.data.objects[name].data).faces)

    def begin(trigger='RIGHTMOUSE', shift=True, ctrl=False, point=None):
        origin[:] = midpoint() if point is None else point
        event('MOUSEMOVE', 'NOTHING', origin)
        yield from settle()
        if ctrl:
            event('LEFT_CTRL', ctrl=True)
        if shift:
            event('LEFT_SHIFT', ctrl=ctrl, shift=True)
        event(trigger, ctrl=ctrl, shift=shift)
        yield from settle(7)
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
              'selected Object Mesh Shift+RMB must immediately open one modeling session: ' + repr(modals()))

    def release(trigger='RIGHTMOUSE', shift=True, ctrl=False):
        # Let the owning release reach the menu before releasing its modifiers.
        event(trigger, 'RELEASE', shift=shift, ctrl=ctrl)
        yield from settle(3)
        if shift:
            event('LEFT_SHIFT', 'RELEASE', ctrl=ctrl)
        if ctrl:
            event('LEFT_CTRL', 'RELEASE')
        yield from settle()

    # Missing-companion RED uses old public events and native screenshot pixels,
    # before importing any newly introduced AxisMeld module or snapshot schema.
    with override():
        bpy.ops.screen.screen_full_area()
    yield from settle(8)
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    area.spaces.active.show_region_ui = False
    area.spaces.active.show_region_toolbar = False
    theme = bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu, theme.wcol_menu_back, theme.wcol_menu_item):
        colors.inner = (.8, .04, .65, 1)
        colors.inner_sel = (.8, .04, .65, 1)
    name = seed()
    yield from settle(8)
    before = state()
    yield from begin()
    first_path = artifacts / 'object-companion-first.png'
    with override():
        bpy.ops.screen.screenshot(filepath=str(first_path))
    print('SCREENSHOT', first_path, flush=True)
    image = bpy.data.images.load(str(first_path), check_existing=False)
    try:
        width, height = image.size
        pixels = list(image.pixels)
        cx, cy = origin
        # Inspect a wide region beneath the lowest radial button. A list must
        # contribute a solid wide body across multiple native row heights.
        # No production layout builder or label/catalog introspection is used.
        visible_rows = []
        for yy in range(max(0, int(cy-390*scale)), max(0, int(cy-92*scale))):
            longest = run = 0
            for xx in range(max(0, int(cx-420*scale)), min(width, int(cx+420*scale))):
                r, g, b = pixels[(yy*width+xx)*4:(yy*width+xx)*4+3]
                run = run+1 if r > .3 and b > .25 and min(r,b) > 2.2*g else 0
                longest = max(longest, run)
            if longest > 150*scale:
                visible_rows.append(yy)
        check(len(visible_rows) >= 60*scale,
              'Object Shift+RMB missing simultaneously visible lower companion list: '
              + repr(len(visible_rows)) + ' wide body rows')
    finally:
        bpy.data.images.remove(image)
    check(state() == before, 'opening Object composition mutated the scene')
    yield from release()
    idle('initial Object composition center cancel')
    check(state() == before, 'initial Object composition center cancel changed scene')
    print('PASS real Object radial and lower companion are simultaneously visible', flush=True)
    from axismeld import hotbox_runtime, runtime
    check(not runtime.diagnostics, 'runtime diagnostics: ' + repr(runtime.diagnostics))

    def ortho():
        region.data.view_rotation = Quaternion((1, 0, 0, 0))
        region.data.view_location = Vector((0, 0, 0))
        region.data.view_distance = 10
        region.data.view_perspective = 'ORTHO'

    def capture(label):
        path = artifacts / (label + '.png')
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        picture = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = picture.size
            values = np.asarray(picture.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(picture)
        print('SCREENSHOT', path, flush=True)
        return values

    def foreground(pixels):
        rgb = pixels[:, :, :3]
        return (rgb[:, :, 1] > .24) & (rgb[:, :, 1] > np.maximum(rgb[:, :, 0], rgb[:, :, 2])*.45)

    def companion_rect(pixels, exclude=None):
        # Actual long colored row spans establish bounds; no list-layout constants
        # or expected coordinates enter this measurement. Text-sized holes close,
        # while the established radial inner gaps keep radial buttons separate.
        rgb = pixels[:, :, :3]
        colored = ((rgb[:, :, 0] > .3) & (rgb[:, :, 2] > .25)
                   & (np.minimum(rgb[:, :, 0], rgb[:, :, 2]) > 2.2*rgb[:, :, 1]))
        if exclude is not None:
            xa,ya,xb,yb = map(int,exclude)
            colored[max(0,ya-3):yb+3,max(0,xa-3):xb+3] = False
        minimum_width = (100 if exclude is not None else 150)*scale
        groups = {}
        for y in range(region.y+3, region.y+region.height-3):
            xs = np.flatnonzero(colored[y, region.x+2:region.x+region.width-2])+region.x+2
            if len(xs) < minimum_width-10*scale:
                continue
            cuts = np.flatnonzero(np.diff(xs) > 28*scale)+1
            for span in np.split(xs, cuts):
                if len(span) and span[-1]-span[0] > minimum_width:
                    key = (round(int(span[0])/(4*scale)), round(int(span[-1])/(4*scale)))
                    groups.setdefault(key, []).append((int(span[0]), int(span[-1]), y))
        candidates = []
        for rows in groups.values():
            ys = [row[2] for row in rows]
            if max(ys)-min(ys) > 58*scale and len(ys) > 25*scale:
                candidates.append((min(row[0] for row in rows), min(ys),
                                   max(row[1] for row in rows)+1, max(ys)+1))
        check(candidates, 'no independently observed companion rectangle')
        return max(candidates, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))

    templates = {}

    def glyph_template(label):
        if label not in templates:
            blf.size(0, bpy.context.preferences.ui_styles[0].widget.points*scale)
            blf.color(0, 1, 1, 1, 1)
            blf.position(0, 4, 10*scale, 0)
            canvas = imbuf.new((int(420*scale), int(40*scale)))
            with blf.bind_imbuf(0, canvas):
                blf.draw_buffer(0, label)
            path = root / ('glyph-' + str(len(templates)) + '.png')
            imbuf.write(canvas, filepath=str(path))
            canvas.free()
            picture = bpy.data.images.load(str(path), check_existing=False)
            try:
                width, height = picture.size
                values = np.asarray(picture.pixels[:], dtype=np.float32).reshape(height,width,4)
                mask = values[:, :, 3] > .35
                ys, xs = np.nonzero(mask)
                check(len(xs), 'empty independent label glyph template: ' + label)
                templates[label] = mask[ys.min():ys.max()+1, xs.min():xs.max()+1].copy()
            finally:
                bpy.data.images.remove(picture)
        return templates[label]

    def rendered_rows(pixels, rect, labels):
        x0, y0, x1, y1 = map(int, rect)
        # Exclude independent Options/arrow cell. Left margin is only for
        # discarding the native backdrop border, not prescribing text origin.
        ink = foreground(pixels[y0:y1, x0+4:x1-int(26*scale)])
        occupied = np.flatnonzero(np.sum(ink, axis=1) >= 3*scale)
        bands = np.split(occupied, np.flatnonzero(np.diff(occupied)>2*scale)+1)
        matches = []
        for band in bands:
            if len(band) < 3*scale:
                continue
            low, high = int(band[0]), int(band[-1])+1
            sample = ink[low:high]
            ys, xs = np.nonzero(sample)
            if not len(xs):
                continue
            sample = sample[:, xs.min():xs.max()+1]
            samples = [sample]
            # A native check indicator is an independent small glyph before the
            # label. Recognize its isolated <=14px column cluster and following
            # whitespace; do not treat its width as part of the label template.
            columns = np.flatnonzero(np.any(sample, axis=0))
            gaps = np.flatnonzero(np.diff(columns) >= 5*scale)
            if len(gaps):
                split = int(gaps[0])
                prefix_width = int(columns[split]-columns[0]+1)
                text_start = int(columns[split+1])
                if prefix_width <= 14*scale and text_start <= 26*scale:
                    suffix = sample[:,text_start:]
                    sy,sx = np.nonzero(suffix)
                    if len(sx):
                        samples.append(suffix[sy.min():sy.max()+1,sx.min():sx.max()+1])
            scores = []
            for label in labels:
                target = glyph_template(label)
                best = 0
                for candidate in samples:
                    if abs(target.shape[1]-candidate.shape[1]) > 6*scale:
                        continue
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            yy0, xx0 = max(0,dy), max(0,dx)
                            ty0, tx0 = max(0,-dy), max(0,-dx)
                            hh = min(candidate.shape[0]-yy0, target.shape[0]-ty0)
                            ww = min(candidate.shape[1]-xx0, target.shape[1]-tx0)
                            if hh <= 0 or ww <= 0:
                                continue
                            overlap = np.count_nonzero(candidate[yy0:yy0+hh,xx0:xx0+ww]
                                                       & target[ty0:ty0+hh,tx0:tx0+ww])
                            best = max(best, 2*overlap/(np.count_nonzero(candidate)+np.count_nonzero(target)))
                scores.append((best,label))
            if scores:
                score,label = max(scores)
                if score >= .58:
                    matches.append((label, (x0+x1)/2, y0+(low+high)/2, score))
        return sorted(matches, key=lambda item: -item[2])

    def inspect_page(tag, labels=MAIN_LABELS):
        picture = capture(tag)
        rect = companion_rect(picture)
        rows = rendered_rows(picture, rect, labels)
        check(rows, 'no actual rendered expected labels recognized: ' + tag)
        print('RENDERED_ROWS', tag, rect, [(r[0], round(r[3],3)) for r in rows], flush=True)
        return rect, rows

    def move(point, shift=True):
        event('MOUSEMOVE', 'NOTHING', point, shift=shift)
        yield from settle(3)

    def find_main(label, tag='find'):
        # Scroll the actual list under a held trigger until the rendered target
        # appears. Catalog IDs determine neither coordinates nor visibility.
        for page in range(30):
            rect, rows = inspect_page(tag+'-'+str(page))
            for text, x, y, _score in rows:
                if text == label:
                    yield from move((x,y))
                    return rect, (x,y)
            event('MOUSEMOVE', 'NOTHING', ((rect[0]+rect[2])/2,(rect[1]+rect[3])/2), shift=True)
            event('WHEELDOWNMOUSE', shift=True)
            yield from settle(4)
        raise AssertionError('rendered main row unreachable through paging: ' + label)

    def baseline(label):
        with override():
            bpy.ops.ed.undo_push(message=label)
        return state()

    def undo(expected,label):
        idle(label+' before Undo')
        with override():
            check(bpy.ops.ed.undo() == {'FINISHED'}, label+' Undo unavailable')
        yield from settle(8)
        check(state() == expected, label+' one Undo did not restore scene')

    def run_main(label):
        yield from begin()
        yield from find_main(label,label.replace(' ','-'))
        yield from release()
        idle(label)

    # All 22 independently specified Maya rows must be rendered and accessible
    # in their original order, across actual native pages.
    yield from begin()
    seen = []
    separator_pairs=set()
    expected_separators={'Crease Tool','Split Mesh with Projected Curve','Mapping',
                         'Retopologize','Transfer Vertex Order','Booleans','Quad Draw Tool'}
    last_page = None
    unchanged_pages = 0
    for page in range(35):
        rect, rows = inspect_page('inventory-'+str(page))
        labels = tuple(row[0] for row in rows)
        check([MAIN_LABELS.index(label) for label in labels] == sorted(MAIN_LABELS.index(label) for label in labels),
              'rendered main rows violate Maya order: '+repr(labels))
        ordinary_gaps=[a[2]-b[2] for a,b in zip(rows,rows[1:])
                       if a[0] not in expected_separators and MAIN_LABELS.index(b[0])==MAIN_LABELS.index(a[0])+1]
        if ordinary_gaps:
            row_gap=float(np.median(ordinary_gaps))
            for a,b in zip(rows,rows[1:]):
                if a[0] in expected_separators and MAIN_LABELS.index(b[0])==MAIN_LABELS.index(a[0])+1:
                    check(a[2]-b[2]>row_gap+3*scale,'rendered separator missing after '+a[0])
                    separator_pairs.add(a[0])
        for label in labels:
            if label not in seen:
                seen.append(label)
        if len(seen) == len(MAIN_LABELS):
            break
        # Wheel offsets count actual separator rows too. Advancing past a
        # separator may retain every label while moving their real pixel y
        # positions (inventory5/6 is such a legitimate transition). Compare
        # observed geometry, and allow a short bounded identical-page grace
        # for a clipped leading separator; exact22row reachability remains.
        page_signature = tuple((row[0], round(row[2], 1)) for row in rows)
        unchanged_pages = unchanged_pages + 1 if page_signature == last_page else 0
        check(unchanged_pages < 3, 'paging made no rendered progress for three advances before every Maya row became visible')
        last_page = page_signature
        event('MOUSEMOVE','NOTHING',((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),shift=True)
        event('WHEELDOWNMOUSE',shift=True)
        yield from settle(5)
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'paging lost single owner')
    check(separator_pairs==expected_separators,'not every Maya separator was observed between rendered rows: '+repr(separator_pairs))
    check(tuple(seen) == MAIN_LABELS, 'rendered inventory is not exactly the22Maya rows: '+repr(seen))
    yield from move(origin)
    yield from release()
    idle('inventory center cancel')
    check(state() == before, 'inventory paging/center cancel mutated scene')
    print('PASS all22mainrows rendered in source order through real paging',flush=True)


    def evaluated(name):
        obj = bpy.data.objects[name]
        obj = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            volume = abs(bm.calc_volume(signed=True))
            bm.free()
            points = [obj.matrix_world @ vert.co for vert in mesh.vertices]
            bounds = tuple((min(v[i] for v in points),max(v[i] for v in points)) for i in range(3))
            return (len(mesh.vertices),len(mesh.edges),len(mesh.polygons),volume,bounds)
        finally:
            obj.to_mesh_clear()

    def cube_scene(pair=False, x=0):
        clear()
        with override():
            bpy.ops.mesh.primitive_cube_add(size=2, location=(x,0,0))
            first = bpy.context.active_object
            first.name = 'Composition A'
            if pair:
                bpy.ops.mesh.primitive_cube_add(size=2, location=(x+1,0,0))
                second = bpy.context.active_object
                second.name = 'Composition B'
                first.select_set(True)
                bpy.context.view_layer.objects.active = first
            bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        ortho()
        return first.name

    for label, expected_type in (('Smooth','SUBSURF'), ('Mirror','MIRROR'),
                                 ('Reduce','DECIMATE'), ('Remesh','REMESH')):
        name = cube_scene()
        if label == 'Mirror':
            for vert in bpy.data.objects[name].data.vertices:
                vert.co.x += .5
            bpy.data.objects[name].data.update()
        if label == 'Reduce':
            with override():
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.subdivide(number_cuts=3)
                bpy.ops.object.mode_set(mode='OBJECT')
        yield from settle(8)
        original_eval = evaluated(name)
        expected = baseline('composition '+label)
        yield from run_main(label)
        yield from settle(8)
        check(bpy.context.mode == 'OBJECT', label+' changed Object Mode')
        obj = bpy.data.objects[name]
        check(any(m.type == expected_type for m in obj.modifiers), label+' did not add its promised native modifier')
        result = evaluated(name)
        if label == 'Smooth':
            check(result[0] > original_eval[0] and 0 < result[3] < original_eval[3],
                  'Smooth evaluated result did not subdivide/round cube')
        elif label == 'Mirror':
            lo,hi = result[4][0]
            check(abs(lo+hi)<1e-5 and lo<0<hi and result[4][0] != original_eval[4][0],
                  'Mirror evaluated result did not make the asymmetric mesh symmetric across local X')
        elif label == 'Reduce':
            check(0 < result[2] < original_eval[2], 'Reduce evaluated result did not reduce actual polygon count')
        else:
            check(result[0] > 8 and result[3] > 0, 'Remesh did not produce a nonempty evaluated voxel surface')
        yield from undo(expected,label)
    print('PASS real Smooth/Mirror/Reduce/Remesh evaluated geometry and one Undo',flush=True)

    # Independent Options cell opens a read-only native parameter window; release
    # must not also execute the main row. Confirmation is a new real input event.
    for outcome in ('cancel','confirm','target-change','cancel-preselect','confirm-preselect'):
        name = cube_scene()
        yield from settle(8)
        if outcome.endswith('-preselect'):
            for obj in bpy.context.view_layer.objects:
                obj.select_set(False)
            bpy.context.view_layer.objects.active=None
            yield from settle(5)
        expected = baseline('Smooth Options '+outcome)
        recent = hotbox_runtime.recent.items()
        yield from begin()
        rect, point = yield from find_main('Smooth','options-'+outcome)
        yield from move((rect[2]-12*scale,point[1]))
        yield from release()
        yield from settle(5)
        check(state() == expected and hotbox_runtime.recent.items() == recent,
              'opening Options committed main row or mutated targets')
        capture('options-'+outcome+'-open')
        if outcome == 'target-change':
            bpy.data.objects[name].data = bpy.data.objects[name].data.copy()
            expected = state()
        event('ESC' if outcome.startswith('cancel') else 'RET')
        event('ESC' if outcome.startswith('cancel') else 'RET','RELEASE')
        yield from settle(8)
        idle('Options '+outcome)
        if outcome.startswith('confirm'):
            check(any(m.type=='SUBSURF' for m in bpy.data.objects[name].modifiers)
                  and evaluated(name)[0] > 8, 'Options confirmation did not execute one Smooth result')
            yield from undo(expected,'Smooth Options confirm')
        else:
            check(state() == expected and hotbox_runtime.recent.items() == recent,
                  'Options '+outcome+' changed scene/Recent')
    print('PASS Options independent hit, read-only window, cancel/confirm/stale identity and Undo',flush=True)

    CHILD_LABELS = {
        'Mapping': ('Planar Map X','Planar Map Y','Planar Map Z','Planar Map',
                    'Cylindrical Map','Spherical Map','Automatic Map','Camera Based Map','Normal Based Map'),
        'Booleans': ('Union','Difference A - B','Difference B - A','Intersection',
                     'Slice','Hole Punch','Cut Out','Split Edges'),
        'Polygon Display': ('Backface Culling','Border Edges','Texture Border Edges','Face Normals',
                            'Vertex Normals','Face Centers','Hidden Triangles','Vertices','Reset Polygon Display'),
    }

    def find_child(parent,label,tag):
        main_rect,_point = yield from find_main(parent,tag+'-parent')
        yield from settle(5)
        for page in range(20):
            picture = capture(tag+'-child-'+str(page))
            child_rect = companion_rect(picture,exclude=main_rect)
            rows = rendered_rows(picture,child_rect,CHILD_LABELS[parent])
            check(rows, parent+' cascade has no expected rendered child labels')
            # A child must coexist with the original main list and radial root.
            check(rendered_rows(picture,main_rect,MAIN_LABELS), parent+' cascade erased its main list')
            check(modals().count('VIEW3D_OT_axismeld_hotbox')==1, parent+' cascade created competing owner')
            print('RENDERED_CHILD',parent,[r[0] for r in rows],flush=True)
            for text,x,y,_score in rows:
                if text==label:
                    yield from move((x,y))
                    return child_rect,(x,y)
            event('MOUSEMOVE','NOTHING',((child_rect[0]+child_rect[2])/2,(child_rect[1]+child_rect[3])/2),shift=True)
            event('WHEELDOWNMOUSE',shift=True)
            yield from settle(4)
        raise AssertionError('unreachable rendered cascade leaf: '+parent+'/'+label)

    name = cube_scene()
    yield from settle(8)
    expected = state()
    recent = hotbox_runtime.recent.items()
    yield from begin()
    yield from find_child('Mapping','Planar Map X','mapping')
    yield from release()
    idle('disabled Mapping leaf')
    check(state()==expected and hotbox_runtime.recent.items()==recent,
          'disabled Mapping cascade leaf changed geometry/selection or Recent')

    old_culling = area.spaces.active.shading.show_backface_culling
    yield from begin()
    yield from find_child('Polygon Display','Backface Culling','polygon-display')
    yield from release()
    idle('Polygon Display leaf')
    check(area.spaces.active.shading.show_backface_culling != old_culling and state()==expected,
          'Polygon Display cascade failed actual viewport culling toggle')
    area.spaces.active.shading.show_backface_culling = old_culling

    for label,volume,target_name in (('Union',12,'Composition A'),('Difference A - B',4,'Composition A'),
                                    ('Difference B - A',4,'Composition B'),('Intersection',4,'Composition A')):
        cube_scene(pair=True)
        yield from settle(8)
        expected = baseline('Boolean '+label)
        yield from begin()
        yield from find_child('Booleans',label,'boolean-'+label.replace(' ','-'))
        yield from release()
        idle('Boolean '+label)
        check(len(bpy.context.scene.objects)==2, 'Boolean must preserve both original objects')
        target=bpy.data.objects[target_name]
        check(len(target.modifiers)==1 and target.modifiers[0].type=='BOOLEAN'
              and target.modifiers[0].solver=='EXACT', label+' added wrong native Boolean target/solver')
        check(abs(evaluated(target_name)[3]-volume)<1e-4, label+' produced wrong evaluated overlap volume')
        yield from undo(expected,'Boolean '+label)
    print('PASS three visible cascades, disabled Mapping, native culling and four exact Boolean results/Undo',flush=True)

    name = cube_scene(pair=True)
    yield from settle(8)
    expected = baseline('Combine pair')
    yield from run_main('Combine')
    meshes = [o for o in bpy.context.scene.objects if o.type=='MESH']
    check(len(meshes)==1 and len(meshes[0].data.vertices)==16,
          'Combine did not join both selected cubes into one16vertexmesh')
    yield from undo(expected,'Combine pair')
    print('PASS real selected-pair Combine and one Undo',flush=True)

    # Shared data/target policy lives in production; these observers inspect the
    # native tool and subsequent mesh result rather than adapter dispatch return.
    for label, tool in (('Offset Edge Loop Tool','builtin.offset_edge_loop_cut'),('Quad Draw Tool','builtin.poly_build')):
        name = seed()
        ortho()
        yield from settle(8)
        expected = baseline(label+' entry')
        yield from run_main(label)
        check(bpy.context.mode == 'EDIT_MESH'
              and bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == tool,
              label+' failed to activate native persistent tool in Edit')
        if label=='Quad Draw Tool':
            entered=state()
            def project(point):
                local=location_3d_to_region_2d(region,region.data,Vector(point))
                check(local is not None,'PolyBuild stroke point not projectable')
                return region.x+local.x,region.y+local.y
            start,end=project((0,-2,0)),project((0,-3,0))
            event('MOUSEMOVE','NOTHING',start)
            yield from settle(8)
            event('LEFTMOUSE',point=start)
            yield from settle(3)
            event('MOUSEMOVE','NOTHING',end)
            yield from settle(5)
            event('LEFTMOUSE','RELEASE',end)
            yield from settle(8)
            idle('lower Quad Draw real stroke')
            check(topology(name)[0]>4 and topology(name)[2]>1,
                  'lower Quad Draw tool did not receive actual edge extrusion stroke')
            yield from undo(entered,'lower Quad Draw separate stroke')
        yield from undo(expected,label+' entry')
    print('PASS lower-list Offset Edge Loop and Quad Draw startup and one Undo',flush=True)


    def radial_rectangles(pixels):
        rgb=pixels[:,:,:3]
        colored=((rgb[:,:,0]>.3)&(rgb[:,:,2]>.25)&(np.minimum(rgb[:,:,0],rgb[:,:,2])>2.2*rgb[:,:,1]))
        groups={}
        for yy in range(max(region.y,int(origin[1]-86*scale)),min(region.y+region.height,int(origin[1]+86*scale))):
            xs=np.flatnonzero(colored[yy,region.x:region.x+region.width])+region.x
            for span in np.split(xs,np.flatnonzero(np.diff(xs)>3*scale)+1):
                if len(span) and span[-1]-span[0]>=60*scale:
                    key=(round(int(span[0])/(4*scale)),round(int(span[-1])/(4*scale)))
                    groups.setdefault(key,[]).append((int(span[0]),int(span[-1]),yy))
        found={}
        # Views deliberately has equal-width buttons in multiple rows. Equal
        # x-bounds do not make them one tall rectangle: separate actual y runs.
        clusters=[]
        for same_x_rows in groups.values():
            current=[]
            for row in same_x_rows:
                if current and row[2]-current[-1][2]>16*scale:
                    clusters.append(current)
                    current=[]
                current.append(row)
            if current:
                clusters.append(current)
        for rows in clusters:
            y0,y1=min(r[2] for r in rows),max(r[2] for r in rows)
            if not 13*scale<=y1-y0<=27*scale:
                continue
            x0,x1=min(r[0] for r in rows),max(r[1] for r in rows)
            dx,dy=(x0+x1)/2-origin[0],(y0+y1)/2-origin[1]
            direction=('N' if dy>16*scale else 'S' if dy < -16*scale else '')
            direction+=('E' if dx>20*scale else 'W' if dx < -20*scale else '')
            if direction:
                rect=(x0,y0,x1,y1)
                if direction not in found or (x1-x0)*(y1-y0)>(found[direction][2]-found[direction][0])*(found[direction][3]-found[direction][1]):
                    found[direction]=rect
        check(set(found)=={'N','NE','E','SE','S','SW','W','NW'},
              'actual screenshot did not expose all eight radial button rectangles: '+repr(found))
        return found

    for cancel in ('disabled-row','disabled-options','center','shift-first','escape','focus','data-change'):
        name=cube_scene()
        yield from settle(5)
        yield from begin()
        label='Unsmooth' if cancel=='disabled-row' else 'Offset Edge Loop Tool' if cancel=='disabled-options' else 'Smooth'
        rect,point=yield from find_main(label,'cancel-'+cancel)
        if cancel=='disabled-options':
            yield from move((rect[2]-12*scale,point[1]))
        if cancel=='center':
            yield from move(origin)
        elif cancel=='shift-first':
            event('LEFT_SHIFT','RELEASE')
        elif cancel=='escape':
            event('ESC',shift=True)
            event('ESC','RELEASE',shift=True)
        elif cancel=='focus':
            event('WINDOW_DEACTIVATE','NOTHING')
        elif cancel=='data-change':
            bpy.data.objects[name].data=bpy.data.objects[name].data.copy()
            event('MOUSEMOVE','NOTHING',position,shift=True)
        expected=state()
        recent=hotbox_runtime.recent.items()
        yield from settle(3)
        event('RIGHTMOUSE','RELEASE',shift=cancel!='shift-first')
        event('LEFT_SHIFT','RELEASE')
        yield from settle(5)
        idle('composition '+cancel)
        check(state()==expected and hotbox_runtime.recent.items()==recent,
              'composition '+cancel+' dispatched through list occlusion or invalid source')
    print('PASS real list/Options occlusion, center/Esc/modifier/focus and stale-source cancellation',flush=True)

    name=seed()
    yield from settle(5)
    expected=baseline('composition radial outward Knife')
    yield from begin()
    rectangles=radial_rectangles(capture('composition-all-eight-radial'))
    x0,y0,x1,y1=rectangles['W']
    yield from move(((x0+x1)/2,(y0+y1)/2))
    yield from move((region.x+20*scale,(y0+y1)/2))
    yield from release()
    check(bpy.context.mode=='EDIT_MESH'
          and bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname=='builtin.knife',
          'companion incorrectly disabled radial outward Knife outside actual list bounds')
    yield from undo(expected,'composition radial outward Knife')

    # Remapped owning keyboard input retains the same combined menu and closes
    # on its own release; no second popup owns the lower list.
    with override():
        config=runtime.load(session={'schema_version':1,'bindings':{MODEL:{'type':'F13','ctrl':True}}})
        bpy.context.window_manager.keyconfigs.active=config
        bpy.context.window_manager.keyconfigs.update()
    yield from settle(8)
    expected=state()
    yield from begin('F13',False,True)
    picture=capture('composition-remapped-F13')
    companion_rect(picture)
    radial_rectangles(picture)
    yield from release('F13',False,True)
    idle('composition remap center cancel')
    check(state()==expected,'remapped composition center cancel edited scene')
    with override():
        config=runtime.load(session={'schema_version':1,'bindings':{}})
        bpy.context.window_manager.keyconfigs.active=config
        bpy.context.window_manager.keyconfigs.update()
    yield from settle(8)
    print('PASS radial outside-list extension and remapped combined owner',flush=True)

    # Match the established isolated Views reference fixture: hide primary
    # Space rows so their semitransparent backdrops cannot merge with the eight
    # solid secondary buttons in the screenshot observer. Font and radial
    # spacing remain native and unchanged, with the same settings for Object.
    with override():
        hotbox_runtime.reload_settings(bpy.context,session={'schema_version':1,'settings':{
            'style':'center','transparency':0,'rows':[],
            'appearance':{'theme_background':True,'brightness':0}}})
    yield from settle(8)

    for layout in ('single','quad'):
        name=seed()
        if layout=='quad':
            with override():
                bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
            yield from settle(8)
            region=min((r for r in area.regions if r.type=='WINDOW'),key=lambda r:(r.y,r.x))
        ortho()
        yield from settle(8)
        origin[:]=midpoint()
        event('MOUSEMOVE','NOTHING',origin)
        event('SPACE')
        yield from settle(16)
        event('LEFTMOUSE')
        yield from settle(8)
        reference=radial_rectangles(capture('composition-'+layout+'-views'))
        event('LEFTMOUSE','RELEASE')
        event('SPACE','RELEASE')
        yield from settle(8)
        idle('Views reference '+layout)
        expected=state()
        yield from begin()
        picture=capture('composition-'+layout+'-object')
        actual=radial_rectangles(picture)
        companion=companion_rect(picture)
        for left,right in (('NW','NE'),('W','E'),('SW','SE')):
            reference_gap=reference[right][0]-reference[left][2]-1
            actual_gap=actual[right][0]-actual[left][2]-1
            check(abs(reference_gap-actual_gap)<=3*scale,
                  layout+' actual radial inner edges do not match same-instance Views: '+repr((left,actual_gap,reference_gap)))
        for rect in actual.values():
            check(rect[2]<companion[0] or rect[0]>companion[2] or rect[3]<companion[1] or rect[1]>companion[3],
                  layout+' actual companion overlaps radial button pixels')
        yield from release()
        idle(layout+' composition center cancel')
        check(state()==expected,layout+' combined display/center cancel edited scene')
        print('PASS combined menu and actual Views inner edges',layout,flush=True)

    # Edge clamping must keep the actual companion body visible while retaining
    # the original physical press point as cancellation dead zone.
    name=seed()
    yield from settle(5)
    expected=state()
    for xside,yside in ((0,0),(1,0),(0,1),(1,1)):
        point=(region.x+(region.width-4 if xside else 4),
               region.y+(region.height-4 if yside else 4))
        yield from begin(point=point)
        rect=companion_rect(capture('composition-corner-'+str(xside)+str(yside)))
        check(region.x<=rect[0]<rect[2]<=region.x+region.width
              and region.y<=rect[1]<rect[3]<=region.y+region.height,
              'corner companion body escaped originating viewport')
        yield from release()
        idle('corner original-press cancel')
        check(state()==expected,'corner clamping consumed original-press cancellation')
    print('PASS four corner companion visibility and physical press cancellation',flush=True)

    print('AXISMELD_OBJECT_MENU_EVENTS_PASS', flush=True)


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

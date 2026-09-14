# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real M2d input, mesh results, child tools, native fallback and rendered clearance.

Run only through the disposable GUI runner. The first assertion intentionally uses
the old public input API, so an older installation fails on missing behavior before
any newly introduced module or selector could cause an import error.
"""
import json
import os
from pathlib import Path
import sys
import traceback

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
ROOTS = {'VERT': 'context.modeling_vertex', 'EDGE': 'context.modeling_edge',
         'FACE': 'context.modeling_face'}
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
                              mesh_state(obj) if obj.type == 'MESH' else ())
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
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type=domain, use_extend=False, use_expand=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(mesh)
            elements = getattr(bm, {'VERT': 'verts', 'EDGE': 'edges', 'FACE': 'faces'}[domain])
            elements.ensure_lookup_table()
            for index in (range(len(elements)) if selection is None else selection):
                elements[index].select_set(True)
            bm.select_flush_mode()
            bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
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
              'selected single-domain Mesh Shift+RMB must immediately open one modeling session: ' + repr(modals()))

    def release(trigger='RIGHTMOUSE', shift=True, ctrl=False):
        # Let the owning release reach the menu before releasing its modifiers.
        event(trigger, 'RELEASE', shift=shift, ctrl=ctrl)
        yield from settle(3)
        if shift:
            event('LEFT_SHIFT', 'RELEASE', ctrl=ctrl)
        if ctrl:
            event('LEFT_CTRL', 'RELEASE')
        yield from settle()

    # Missing functionality RED: real input in an old installed binary, no new imports.
    first = seed()
    before = state()
    cursor = tuple(bpy.context.scene.cursor.location)
    yield from begin()
    check(state() == before and tuple(bpy.context.scene.cursor.location) == cursor,
          'opening the modeling root changed geometry, selection, mode or cursor')
    yield from release()
    idle('initial center cancellation')
    check(state() == before, 'initial center cancellation edited geometry')
    print('PASS M2d real Shift+RMB opens on selected Edit Mesh without mutating context', flush=True)

    from axismeld import hotbox_runtime, runtime
    check(not runtime.diagnostics, 'runtime diagnostics: ' + repr(runtime.diagnostics))

    with override():
        bpy.ops.screen.screen_full_area()
    yield from settle(8)
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    origin[:] = midpoint()
    area.spaces.active.show_region_ui = False
    area.spaces.active.show_region_toolbar = False

    def ortho():
        region.data.view_rotation = Quaternion((1, 0, 0, 0))
        region.data.view_location = Vector((0, 0, 0))
        region.data.view_distance = 10
        region.data.view_perspective = 'ORTHO'

    ortho()
    yield from settle(8)

    def nodes():
        with override():
            pending = list(json.loads(hotbox_runtime.snapshot(bpy.context))['menus'])
        result = {}
        while pending:
            item = pending.pop()
            result[item['id']] = item
            pending.extend(item['children'])
        return result

    def rectangle_targets(root_id, anchor=None):
        """Input fixture only. Geometry outcomes and screenshot edges are independent."""
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        center_width = blf.dimensions(0, 'AxisMeld')[0] / scale + 60
        origin_x, origin_y = origin if anchor is None else anchor
        vectors = {'N': (0, 1), 'NE': (1, 1), 'E': (1, 0), 'SE': (1, -1),
                   'S': (0, -1), 'SW': (-1, -1), 'W': (-1, 0), 'NW': (-1, 1)}
        result = {}
        for item in nodes()[root_id]['children']:
            if 'direction' not in item:
                continue
            sx, sy = vectors[item['direction']]
            width = max(84, blf.dimensions(0, item['label'])[0] / scale +
                        (60 if item['kind'] == 'menu' else 16))
            x = sx * ((width + center_width) / 2 + 8 - (16 if sy else 0)) if sx else 0
            y = sy * (32 if sx else 64)
            result[item['direction']] = (origin_x + x * scale, origin_y + y * scale)
        return result

    def move_to(root_id, direction, anchor=None, shift=True, ctrl=False, outer=False):
        point = rectangle_targets(root_id, anchor)[direction]
        event('MOUSEMOVE', 'NOTHING', point, shift=shift, ctrl=ctrl)
        yield from settle()
        if outer:
            sx = 0 if direction in {'N', 'S'} else (-1 if 'W' in direction else 1)
            sy = (1 if direction == 'N' else -1) if sx == 0 else 0
            extended = (point[0] + sx * 90 * scale, point[1] + sy * 90 * scale)
            for fraction in (.25, .5, .75, 1):
                event('MOUSEMOVE', 'NOTHING', tuple(a + (b-a)*fraction for a, b in zip(point, extended)),
                      shift=shift, ctrl=ctrl)
                yield from settle(1)
        return point

    def action(domain, direction, outer=False, trigger='RIGHTMOUSE', shift=True, ctrl=False, point=None):
        yield from begin(trigger, shift, ctrl, point)
        yield from move_to(ROOTS[domain], direction, shift=shift, ctrl=ctrl, outer=outer)
        yield from release(trigger, shift, ctrl)

    def baseline(label):
        with override():
            bpy.ops.ed.undo_push(message=label)
        return state()

    def undo_to(expected, label):
        idle(label + ' before Undo')
        with override():
            check(bpy.ops.ed.undo() == {'FINISHED'}, label + ' Undo unavailable')
        yield from settle(8)
        check(state() == expected, label + ' one Undo failed to restore geometry and selection')

    # Incorrect NE/S/E dispatch, swallowed mouse release or a wrapper Undo each fail here.
    name = seed()
    yield from settle()
    expected = baseline('M2d Poke baseline')
    yield from action('FACE', 'NE', outer=True)
    idle('Face NE Poke')
    check(topology(name) == (5, 8, 4), 'Face NE must make one center and four triangles')
    check(abs(face_area(name) - 16) < 1e-5, 'Poke changed the planar surface area')
    check(all(len(f.verts) == 3 for f in bmesh.from_edit_mesh(bpy.data.objects[name].data).faces),
          'Poke did not create triangular faces')
    yield from undo_to(expected, 'Face Poke')

    # Maya Merge Faces to Center is vertex collapse, not dissolve into an n-gon.
    name = seed(coordinates=[(-3, -1, 0), (-1, -1, 0), (-1, 1, 0), (-3, 1, 0),
                             (1, -1, 0), (3, -1, 0), (3, 1, 0), (1, 1, 0)],
                faces=((0, 1, 2, 3), (4, 5, 6, 7)))
    yield from settle()
    expected = baseline('M2d Face Center baseline')
    yield from action('FACE', 'N')
    idle('Face N center')
    check(topology(name) == (1, 0, 0), 'Face N must collapse the selected face vertices to one point')
    bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
    check(next(iter(bm.verts)).co.length < 1e-5, 'Face N used the wrong center')
    check(tuple(bpy.context.tool_settings.mesh_select_mode) == (False, False, True)
          and not any(v.select for v in bm.verts), 'Face N changed the native post-collapse selection policy')
    yield from undo_to(expected, 'Face Center')

    # The active object is not the whole native editing set. Two real BMeshes
    # distinguish an active-only selector from the supported multi-object path.
    clear()
    names = []
    with override():
        for offset, label in ((-4, 'M2d Active Unselected'), (4, 'M2d Other Selected')):
            mesh = bpy.data.meshes.new(label)
            mesh.from_pydata(PLANE, [], [(0, 1, 2, 3)])
            obj = bpy.data.objects.new(label, mesh)
            bpy.context.collection.objects.link(obj)
            obj.location.x = offset
            obj.select_set(True)
            names.append(obj.name)
        bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        other_bm = bmesh.from_edit_mesh(bpy.data.objects[names[1]].data)
        next(iter(other_bm.faces)).select_set(True)
        other_bm.select_flush_mode()
        bmesh.update_edit_mesh(bpy.data.objects[names[1]].data, loop_triangles=False, destructive=False)
    yield from settle()
    expected = baseline('M2d other editing mesh selection baseline')
    check(not any(v.select for v in bmesh.from_edit_mesh(bpy.data.objects[names[0]].data).verts),
          'multi-Edit fixture accidentally selected the active mesh')
    yield from action('FACE', 'NE')
    idle('non-active editing mesh selection')
    check(topology(names[0]) == (4, 4, 1) and topology(names[1]) == (5, 8, 4),
          'active-empty multi-Edit did not Poke only the other selected mesh')
    check(bpy.context.active_object.name == names[0], 'multi-Edit Poke changed the active object')
    yield from undo_to(expected, 'non-active editing mesh Poke')
    with override():
        bpy.ops.mesh.select_all(action='SELECT')
    yield from settle()
    expected = baseline('M2d two meshes independent centers baseline')
    yield from action('FACE', 'N')
    idle('two editing mesh centers')
    for name, expected_x in zip(names, (-4, 4)):
        obj = bpy.data.objects[name]
        bm = bmesh.from_edit_mesh(obj.data)
        check(topology(name) == (1, 0, 0), name + ' did not merge its face vertices independently')
        point = obj.matrix_world @ next(iter(bm.verts)).co
        check((point - Vector((expected_x, 0, 0))).length < 1e-5,
              name + ' merged toward another editing mesh instead of its own center')
        check(not any(v.select for v in bm.verts), 'multi-Mesh Face Center changed native post-merge selection')
    check(tuple(bpy.context.tool_settings.mesh_select_mode) == (False, False, True),
          'multi-Mesh Face Center changed component domain')
    yield from undo_to(expected, 'two editing meshes Center')
    print('PASS real multi-Edit active-empty routing, per-mesh centers and one Undo of both meshes', flush=True)

    name = seed('VERT', selection=(0,))
    yield from settle()
    expected = baseline('M2d vertex bevel baseline')
    yield from action('VERT', 'E')
    check(any('bevel' in value.lower() for value in modals()), 'Vertex E failed to launch native bevel')
    for key in ('ZERO', 'PERIOD', 'TWO'):
        event(key)
        event(key, 'RELEASE')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle(8)
    idle('vertex bevel confirmation')
    check(topology(name)[0] > 4 and face_area(name) < 16, 'Vertex E did not chamfer a corner')
    yield from undo_to(expected, 'Vertex Bevel')

    name = seed('EDGE', coordinates=[(-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1),
                                    (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1)],
                faces=((0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4),
                       (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)))
    yield from settle()
    expected = baseline('M2d edge bevel baseline')
    yield from action('EDGE', 'E')
    check(any('bevel' in value.lower() for value in modals()), 'Edge E failed to launch bevel')
    for key in ('ZERO', 'PERIOD', 'TWO'):
        event(key)
        event(key, 'RELEASE')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle(8)
    idle('edge bevel confirmation')
    check(topology(name) == (24, 48, 26), 'Edge E did not bevel all twelve cube edges with one segment')
    yield from undo_to(expected, 'Edge Bevel')

    # Open mesh edge (two faces not required) keeps the extrusion fixture unambiguous.
    name = seed('EDGE', coordinates=[(-1, 0, 0), (1, 0, 0)], faces=(), edges=((0, 1),))
    yield from settle()
    expected = baseline('M2d edge extrusion baseline')
    yield from action('EDGE', 'S')
    check(any('extrude' in value.lower() or 'transform' in value.lower() for value in modals()),
          'Edge S did not start the native extrusion macro')
    event('Y')
    event('Y', 'RELEASE')
    event('ONE')
    event('ONE', 'RELEASE')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle(8)
    idle('edge extrusion confirmation')
    check(topology(name) == (4, 4, 1) and abs(face_area(name) - 2) < 1e-5,
          'Edge S did not create the expected translated quad')
    check(sorted(round(v.co.y, 5) for v in bmesh.from_edit_mesh(bpy.data.objects[name].data).verts)
          == [0, 0, 1, 1], 'Edge extrusion retained a stale Shift or wrong axis')
    yield from undo_to(expected, 'Edge Extrude')

    name = seed()
    yield from settle()
    expected = baseline('M2d face extrusion baseline')
    yield from action('FACE', 'S')
    check(any('extrude' in value.lower() or 'transform' in value.lower() for value in modals()),
          'Face S did not start the shared Ctrl+E extrusion macro')
    event('Z')
    event('Z', 'RELEASE')
    event('ONE')
    event('ONE', 'RELEASE')
    event('RET')
    event('RET', 'RELEASE')
    yield from settle(8)
    idle('face extrusion confirmation')
    # The shared native extrude_region_move retains this isolated source face;
    # direct native characterization produces a closed six-face prism.
    check(topology(name) == (8, 12, 6), 'Face S created the wrong region topology: ' + repr(topology(name)))
    check(sorted(round(v.co.z, 5) for v in bmesh.from_edit_mesh(bpy.data.objects[name].data).verts)
          == [0, 0, 0, 0, 1, 1, 1, 1], 'Face extrusion macro did not accept native numeric translation')
    yield from undo_to(expected, 'Face Extrude')
    print('PASS real Poke, Face Center, Vertex Bevel, Edge/Face Extrude and one Undo', flush=True)

    # A root-only test misses child ownership and wrong parent-return targets.
    # Enter Merge, leave its center toward a leaf, return one level, and invoke
    # the parent's Circle direction. Remaining in Merge cannot select this tool.
    name = seed('VERT')
    yield from settle()
    before = state()
    yield from begin()
    child_anchor = yield from move_to(ROOTS['VERT'], 'N')
    yield from move_to(ROOTS['VERT'] + '.merge', 'NE', anchor=child_anchor)
    event('MOUSEMOVE', 'NOTHING', child_anchor, shift=True)
    yield from settle()
    check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'Merge center return closed its parent session')
    yield from move_to(ROOTS['VERT'], 'NW')
    yield from release()
    idle('Merge one-level return to parent Circle')
    check(state() == before and bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname
          == 'builtin.select_circle', 'Merge center did not return one level to the parent direction')
    expected = baseline('M2d child Merge baseline')
    yield from begin()
    child_anchor = yield from move_to(ROOTS['VERT'], 'N')
    yield from move_to(ROOTS['VERT'] + '.merge', 'N', anchor=child_anchor, outer=True)
    yield from release()
    idle('Merge child outward action')
    check(topology(name) == (1, 0, 0)
          and next(iter(bmesh.from_edit_mesh(bpy.data.objects[name].data).verts)).co.length < 1e-5,
          'Merge child N outward release did not execute center geometry')
    yield from undo_to(expected, 'Merge child center')

    name = seed()
    yield from settle()
    expected = baseline('M2d Normals child return baseline')
    yield from begin()
    child_anchor = yield from move_to(ROOTS['FACE'], 'SE')
    yield from move_to(ROOTS['FACE'] + '.normals', 'E', anchor=child_anchor)
    event('MOUSEMOVE', 'NOTHING', child_anchor, shift=True)
    yield from settle()
    check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'Normals center return closed its parent session')
    yield from move_to(ROOTS['FACE'], 'NE')
    yield from release()
    idle('Normals one-level return to Poke')
    check(topology(name) == (5, 8, 4), 'Normals center failed to return one level to parent Poke')
    yield from undo_to(expected, 'Normals child return then parent Poke')

    area.spaces.active.overlay.show_face_normals = False
    yield from begin()
    child_anchor = yield from move_to(ROOTS['FACE'], 'SE')
    yield from move_to(ROOTS['FACE'] + '.normals', 'S', anchor=child_anchor)
    yield from release()
    idle('Normals child display action')
    check(area.spaces.active.overlay.show_face_normals and state() == expected,
          'Normals child S did not change the actual native overlay without geometry changes')
    normals_before = tuple(tuple(face.normal) for face in bmesh.from_edit_mesh(bpy.data.objects[name].data).faces)
    recent = hotbox_runtime.recent.items()
    yield from begin()
    child_anchor = yield from move_to(ROOTS['FACE'], 'SE')
    yield from move_to(ROOTS['FACE'] + '.normals', 'E', anchor=child_anchor)
    # Returning to the real original press point cancels the entire child path.
    event('MOUSEMOVE', 'NOTHING', origin, shift=True)
    yield from settle()
    yield from release()
    idle('Normals child return to original press cancellation')
    check(state() == expected and tuple(tuple(face.normal) for face in
          bmesh.from_edit_mesh(bpy.data.objects[name].data).faces) == normals_before
          and hotbox_runtime.recent.items() == recent, 'Normals child cancellation executed Reverse or polluted Recent')
    print('PASS Merge/Normals child entry, one-level return, outward action and original-press cancel', flush=True)

    # A canceled native bevel restores topology; opening a modal never records a result.
    name = seed('EDGE')
    yield from settle()
    expected = state()
    hotbox_runtime.recent._items = []
    yield from action('EDGE', 'E')
    check(any('bevel' in value.lower() for value in modals()), 'Edge E failed to launch bevel')
    event('MOUSEMOVE', 'NOTHING', (position[0] + 70, position[1] + 20))
    yield from settle()
    event('ESC')
    event('ESC', 'RELEASE')
    yield from settle()
    idle('bevel Esc')
    check(state() == expected and not hotbox_runtime.recent.items(), 'bevel Esc changed geometry or Recent')

    # Each cancellation begins with an actual actionable candidate, then reopens.
    for cancellation in ('center', 'disabled', 'shift-first', 'escape', 'focus',
                         'extra-ctrl', 'other-release', 'domain-change'):
        name = seed()
        yield from settle()
        expected = state()
        recent = hotbox_runtime.recent.items()
        yield from begin()
        yield from move_to(ROOTS['FACE'], 'E' if cancellation == 'disabled' else 'NE')
        if cancellation == 'center':
            event('MOUSEMOVE', 'NOTHING', origin, shift=True)
        elif cancellation == 'shift-first':
            event('LEFT_SHIFT', 'RELEASE')
            yield from settle()
            event('RIGHTMOUSE', 'RELEASE')
        elif cancellation == 'escape':
            event('ESC', shift=True)
            event('ESC', 'RELEASE', shift=True)
        elif cancellation == 'focus':
            event('WINDOW_DEACTIVATE', 'NOTHING')
            yield from settle()
            idle('focus loss before impossible release')
        elif cancellation == 'extra-ctrl':
            event('LEFT_CTRL', ctrl=True, shift=True)
        elif cancellation == 'other-release':
            event('LEFTMOUSE', 'RELEASE', shift=True)
        elif cancellation == 'domain-change':
            bpy.context.tool_settings.mesh_select_mode = (False, True, False)
            expected = state()
            event('MOUSEMOVE', 'NOTHING', position, shift=True)
        yield from settle()
        event('RIGHTMOUSE', 'RELEASE', shift=cancellation != 'shift-first', ctrl=cancellation == 'extra-ctrl')
        event('LEFT_CTRL', 'RELEASE', shift=cancellation != 'shift-first')
        event('LEFT_SHIFT', 'RELEASE')
        yield from settle()
        idle(cancellation)
        check(state() == expected, cancellation + ' committed a stale modeling candidate')
        check(hotbox_runtime.recent.items() == recent, cancellation + ' entered Recent')
        seed()
        yield from settle()
        yield from begin()
        yield from release()
        idle(cancellation + ' repeated opening')
    print('PASS candidate cancellation, owner release, focus, live domain and repeated opening', flush=True)

    def project(point):
        local = location_3d_to_region_2d(region, region.data, Vector(point))
        check(local is not None, 'world point is not projectable')
        return region.x + local.x, region.y + local.y

    def click(point, **modifiers):
        event('MOUSEMOVE', 'NOTHING', point, **modifiers)
        yield from settle(2)
        event('LEFTMOUSE', point=point, **modifiers)
        yield from settle(2)
        event('LEFTMOUSE', 'RELEASE', point, **modifiers)
        yield from settle(3)

    # Activating a persistent tool is not enough: actual subsequent strokes must edit.
    name = seed()
    ortho()
    yield from settle(8)
    expected = baseline('M2d Knife stroke baseline')
    yield from action('FACE', 'W')
    idle('Knife activation')
    check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == 'builtin.knife',
          'Face W did not activate persistent Knife')
    yield from click(project((-2, 0, 0)))
    check(any('knife' in value.lower() for value in modals()), 'Knife did not receive a subsequent LMB')
    yield from click(project((2, 0, 0)))
    event('RET')
    event('RET', 'RELEASE')
    yield from settle(8)
    idle('Knife stroke confirmation')
    check(topology(name) == (6, 7, 2) and abs(face_area(name) - 16) < 1e-5,
          'Knife stroke did not split the quad without losing surface area')
    yield from undo_to(expected, 'Knife subsequent stroke')

    name = seed('VERT', selection=(0,))
    ortho()
    yield from settle(8)
    expected = baseline('M2d Circle selection baseline')
    yield from action('VERT', 'NW')
    idle('Circle activation')
    check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == 'builtin.select_circle',
          'Vertex NW did not activate Circle Selection')
    yield from click(project((2, 2, 0)))
    idle('Circle subsequent stroke')
    bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
    check(any(v.select and (v.co - Vector((2, 2, 0))).length < 1e-5 for v in bm.verts),
          'Circle did not select the subsequent viewport target')
    check(topology(name) == (4, 4, 1) and abs(face_area(name) - 16) < 1e-5,
          'Circle selection changed topology')
    yield from undo_to(expected, 'Circle subsequent selection')
    event('W')
    event('W', 'RELEASE')
    yield from settle()
    idle('QWER after persistent tools')
    check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == 'builtin.move',
          'QWER failed to regain tool control after Circle')
    print('PASS persistent Knife/Circle receive real strokes, undo and release to QWER', flush=True)

    # The selected editing set must win even with unrelated geometry under the cursor.
    clear()
    with override():
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2))
        foreground = bpy.context.active_object
        foreground.name = 'M2d Unselected Foreground'
        foreground.select_set(False)
        mesh = bpy.data.meshes.new('M2d selected plane')
        mesh.from_pydata(PLANE, [], [(0, 1, 2, 3)])
        selected = bpy.data.objects.new('M2d Selected Edit Set', mesh)
        bpy.context.collection.objects.link(selected)
        selected.select_set(True)
        bpy.context.view_layer.objects.active = selected
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
    foreground_before = mesh_state(foreground)
    selected_name, foreground_name = selected.name, foreground.name
    ortho()
    yield from settle()
    yield from action('FACE', 'NE', point=project((0, 0, 2)))
    idle('selected editing set priority')
    check(topology(selected_name) == (5, 8, 4), 'pointer target replaced the selected editing set')
    check(mesh_state(bpy.data.objects[foreground_name]) == foreground_before
          and not bpy.data.objects[foreground_name].select_get()
          and bpy.context.active_object.name == selected_name, 'modeling gesture changed pointer-object selection or geometry')

    def fallback(label):
        expected = state()
        bpy.context.scene.cursor.location = (40, 40, 40)
        event('MOUSEMOVE', 'NOTHING', midpoint())
        yield from settle()
        event('LEFT_SHIFT', shift=True)
        event('RIGHTMOUSE', shift=True)
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' not in modals(), label + ' wrongly opened a context ring')
        event('RIGHTMOUSE', 'RELEASE', shift=True)
        event('LEFT_SHIFT', 'RELEASE')
        yield from settle()
        idle(label + ' fallback')
        check((bpy.context.scene.cursor.location - Vector((40, 40, 40))).length > 1,
              label + ' swallowed the native 3D Cursor fallback')
        check(state() == expected, label + ' fallback changed scene context')

    seed('FACE', selection=())
    yield from settle()
    yield from fallback('empty Edit selection')
    seed('FACE')
    bpy.context.tool_settings.mesh_select_mode = (True, True, True)
    yield from settle()
    yield from fallback('mixed component domains')
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    yield from settle()
    yield from fallback('selected Object')
    clear()
    with override():
        bpy.ops.curve.primitive_bezier_curve_add()
        bpy.ops.object.mode_set(mode='EDIT')
    yield from settle()
    yield from fallback('Curve Edit')
    print('PASS current selection priority and actual native fallback for unsupported contexts', flush=True)

    def configure(event_value):
        with override():
            config = runtime.load(session={'schema_version': 1, 'bindings': {MODEL: event_value}})
            bpy.context.window_manager.keyconfigs.active = config
            bpy.context.window_manager.keyconfigs.update()
        yield from settle(8)
        check(not runtime.diagnostics, 'profile reload diagnostics: ' + repr(runtime.diagnostics))

    seed()
    for binding, trigger, shift, ctrl in (({'type': 'F13', 'ctrl': True}, 'F13', False, True),
                                           ({'type': 'MIDDLEMOUSE', 'shift': True, 'ctrl': True},
                                            'MIDDLEMOUSE', True, True)):
        yield from configure(binding)
        yield from fallback('MODEL rebind preserves old Shift+RMB')
        name = seed()
        yield from settle()
        expected = baseline('M2d remapped owner baseline')
        yield from action('FACE', 'NE', trigger=trigger, shift=shift, ctrl=ctrl)
        idle('remapped modeling trigger')
        check(topology(name) == (5, 8, 4), 'remapped owning release failed to execute Poke once')
        yield from undo_to(expected, 'remapped Poke')
    yield from configure(None)
    yield from fallback('disabled MODEL')
    # Disabling MODEL must not disable the independent CREATE entry in Object Mode.
    clear()
    yield from settle()
    yield from begin()
    yield from release()
    idle('CREATE remains after MODEL disable')
    check(not bpy.context.scene.objects, 'CREATE center cancellation created geometry')
    with override():
        config = runtime.load(session={'schema_version': 1, 'bindings': {}})
        bpy.context.window_manager.keyconfigs.active = config
        bpy.context.window_manager.keyconfigs.update()
    yield from settle(8)
    print('PASS profile rebind/disable and independent CREATE/MODEL mouse ownership', flush=True)

    # Rendered inner edges, not a shared gap formula, establish the Views benchmark.
    theme = bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu, theme.wcol_menu_back, theme.wcol_menu_item):
        # Magenta distinguishes button pixels from viewport RGB axes and orange
        # selection outlines, including an axis running through the middle row.
        colors.inner = (.8, .04, .65, 1)
        colors.inner_sel = (.8, .04, .65, 1)
    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'style': 'center', 'transparency': 0, 'rows': [],
            'appearance': {'theme_background': True, 'brightness': 0}}})

    def screenshot(name):
        path = artifacts / name
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        print('SCREENSHOT', path, flush=True)
        return path

    def rendered_gaps(path):
        """Find colored button spans from pixels, without calling the layout builder."""
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            pixels = list(image.pixels)
            cx, cy = origin
            results = []
            # Views and component roots may have different vertical row spacing.
            # Search a band around each row; inner x edges remain independently observed.
            for row in (1, 0, -1):
                colored = set()
                previous_y = {}
                runs = {}
                # Require a continuous vertical background run, then a continuous
                # horizontal span. Single cursor/axis antialiasing pixels cannot
                # masquerade as a button edge, while glyph holes do not shift it.
                offsets = (-10, 10) if row == 0 else sorted((row*26, row*39))
                for yy in range(int(cy + offsets[0]*scale), int(cy + offsets[1]*scale)+1):
                    if not 0 <= yy < height:
                        continue
                    for xx in range(max(region.x + 2, int(cx - 470 * scale)),
                                    min(region.x + region.width - 2, int(cx + 470 * scale))):
                        r, g, b = pixels[(yy*width + xx)*4:(yy*width + xx)*4+3]
                        if r > .3 and b > .25 and min(r, b) > 2.2*g:
                            runs[xx] = runs.get(xx, 0)+1 if previous_y.get(xx) == yy-1 else 1
                            previous_y[xx] = yy
                            if runs[xx] >= max(4, int(4*scale)):
                                colored.add(xx)
                spans = []
                for xx in sorted(colored):
                    if not spans or xx - spans[-1][1] > 3:
                        spans.append([xx, xx])
                    else:
                        spans[-1][1] = xx
                spans = [span for span in spans if span[1] - span[0] >= 18*scale]
                left = [span for span in spans if span[1] < cx - 6*scale]
                right = [span for span in spans if span[0] > cx + 6*scale]
                check(left and right, f'{path.name}: no independent left/right rendered spans for row {row}: {spans}')
                results.append((min(span[0] for span in right) - max(span[1] for span in left) - 1) / scale)
            return tuple(results)
        finally:
            bpy.data.images.remove(image)

    def views_reference(label):
        origin[:] = midpoint()
        event('MOUSEMOVE', 'NOTHING', origin)
        event('SPACE')
        yield from settle(16)
        event('LEFTMOUSE')
        yield from settle(8)
        check('VIEW3D_OT_axismeld_hotbox' in modals(), 'Views reference failed to open')
        measured = rendered_gaps(screenshot(label + '-views.png'))
        # The diagonal visual gap is outside the center return rectangle. Views
        # selects its nearest direction there: prove NW with real view rotation,
        # so visual spacing is not mistaken for a larger cancellation contract.
        rotations = lambda: tuple(tuple(r.data.view_rotation) for r in area.regions
                                  if r.type == 'WINDOW' and r.data is not None)
        before_views = rotations()
        event('MOUSEMOVE', 'NOTHING', (origin[0] - (measured[0]/2-10)*scale,
                                     origin[1] + 32*scale))
        yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        yield from settle(3)
        event('SPACE', 'RELEASE')
        yield from settle()
        idle('Views reference')
        check(rotations() != before_views, label + ' NW diagonal gap failed to select a real Views orientation')
        print('PASS Views diagonal visual gap selects NW, outside center cancellation', label, flush=True)
        ortho()
        yield from settle()
        return measured

    for layout in ('single', 'quad'):
        seed()
        if layout == 'quad':
            with override():
                bpy.ops.view3d.axismeld_view(action='TOGGLE_QUAD')
            yield from settle(8)
            windows = [r for r in area.regions if r.type == 'WINDOW' and r.width > 1 and r.height > 1]
            check(len(windows) == 4, 'quad layout did not create four independent WINDOW regions')
            region = min(windows, key=lambda value: (value.y, value.x))
        ortho()
        yield from settle(8)
        reference = yield from views_reference('m2d-' + layout)
        check(reference[0] > 50 and reference[1] > reference[0] + 20,
              'Views reference unexpectedly collapsed its established horizontal clearance: ' + repr(reference))
        for domain in ('VERT', 'EDGE', 'FACE'):
            name = seed(domain)
            yield from settle()
            before = state()
            yield from begin()
            measured = rendered_gaps(screenshot('m2d-' + layout + '-' + domain.lower() + '.png'))
            check(all(abs(a-b) <= 3 for a, b in zip(measured, reference)),
                  f'{layout} {domain} actual inner gaps {measured} do not match Views {reference}')
            yield from release()
            idle('rendered gap cancellation')
            check(state() == before, 'screenshot/center cancellation changed mesh')
            # The return rectangle cancels on both sides at y=0. The diagonal
            # visual gap above is a valid nearest-direction gesture in Views.
            for side in (-1, 1):
                yield from begin()
                event('MOUSEMOVE', 'NOTHING', (origin[0] + side*(reference[1]/2-10)*scale,
                                             origin[1]), shift=True)
                yield from settle()
                yield from release()
                idle('center return edge release')
                check(state() == before, f'{layout} {domain} center return edge dispatched an adjacent action')
        # A real action in quad verifies ownership is in that specific WINDOW.
        name = seed()
        yield from settle()
        before = baseline('M2d ' + layout + ' real Poke baseline')
        yield from action('FACE', 'NE')
        idle(layout + ' Poke')
        check(topology(name) == (5, 8, 4), layout + ' directional release failed to reach Poke')
        yield from undo_to(before, layout + ' Poke')
        print('PASS rendered Views clearance and actual center-return edge cancellation', layout, reference, flush=True)
    print('AXISMELD_CONTEXT_MODELING_EVENTS_PASS', flush=True)


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

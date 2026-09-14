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

import blf
import bmesh
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles
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

    theme=bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu,theme.wcol_menu_back,theme.wcol_menu_item):
        colors.inner=(.8,.04,.65,1)
        colors.inner_sel=(.8,.04,.65,1)

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

    # First assertion uses only the old public gesture and native observers.
    name = seed()
    before = state()
    yield from begin()
    check(state() == before, 'opening Object root mutated mode/selection/mesh')
    yield from release()
    idle('first center cancellation')
    check(state() == before, 'canceling Object root mutated mode/selection/mesh')
    print('PASS Object Shift+RMB opens exactly one non-mutating hotbox', flush=True)
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
        if anchor is None and root_id in {OBJECT,CREATE,MODEL,'context.create'}:
            path=root/'actual-input-targets.png'
            with override():bpy.ops.screen.screenshot(filepath=str(path))
            picture=bpy.data.images.load(str(path),check_existing=False)
            try:
                width,height=picture.size
                pixels=np.asarray(picture.pixels[:],dtype=np.float32).reshape(height,width,4).copy()
            finally:bpy.data.images.remove(picture)
            expected={item['direction'] for item in nodes()[root_id]['children'] if 'direction' in item}
            observed=observed_radial_rectangles(pixels,scale,expected)
            return {direction:((rect[0]+rect[2])/2,(rect[1]+rect[3])/2)
                    for direction,rect in observed['rects'].items()}

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


    def action(direction, trigger='RIGHTMOUSE', shift=True, ctrl=False, point=None):
        yield from begin(trigger, shift, ctrl, point)
        yield from move_to(OBJECT, direction, shift=shift, ctrl=ctrl)
        yield from release(trigger, shift, ctrl)

    def activated(tool, names, shared=False):
        idle('tool activation')
        check(bpy.context.mode == 'EDIT_MESH', 'Object action did not enter Mesh Edit')
        check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == tool,
              'incorrect persistent native tool: ' + tool)
        if shared:
            # Native mode_set exposes only the representative for shared Mesh data.
            # Observe unique edit data coverage, preserving the full selection set.
            targets = [bpy.data.objects[name] for name in names]
            check({o.data.as_pointer() for o in bpy.context.objects_in_mode}
                  == {o.data.as_pointer() for o in targets},
                  'tool entered Edit on incorrect unique Mesh data set')
            check(bpy.context.active_object.mode == 'EDIT'
                  and all(o.select_get() for o in targets),
                  'shared-data entry lost active Edit representative or selected instances')
        else:
            check(set(o.name for o in bpy.context.objects_in_mode) == set(names),
                  'tool entered Edit on incorrect object set')

    def deselect():
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        bpy.context.view_layer.objects.active = None

    # Each tool is a mode/selection transaction before any native stroke occurs.
    for direction, tool in (('E', 'builtin.poly_build'), ('SW', 'builtin.loop_cut'), ('W', 'builtin.knife')):
        for preselect in (False, True):
            name = seed()
            ortho()
            if preselect:
                deselect()
            yield from settle(8)
            expected = baseline('Object ' + tool + ' entry')
            recent = hotbox_runtime.recent.items()
            yield from action(direction, point=project((0, 0, 0)))
            activated(tool, [name])
            check(topology(name) == (4, 4, 1), 'activating tool edited geometry')
            check(hotbox_runtime.recent.items() == recent, 'persistent tool entry polluted Recent')
            yield from undo_to(expected, 'Object ' + tool + ' entry')
    print('PASS three tools selected/preselected entry and one Undo mode/selection transaction', flush=True)

    # A genuine partial native activation is followed by an injected exception.
    # Only the boundary is replaced; target capture, event dispatch, mode entry,
    # actual tool change, rollback and all observers run through the real system.
    from axismeld import object_modeling_ops

    def tool_slots():
        values = []
        for mode in ('OBJECT', 'EDIT_MESH'):
            tool = bpy.context.workspace.tools.from_space_view3d_mode(mode, create=False)
            values.append(tool.idname if tool else '')
        return tuple(values)

    def raw_component_flags():
        return tuple(sorted((obj.name, tuple(tuple((element.select, element.hide) for element in domain)
                                 for domain in (obj.data.vertices, obj.data.edges, obj.data.polygons)))
                            for obj in bpy.context.scene.objects if obj.type == 'MESH'))

    for preselect in (False, True):
        name = seed()
        with override():
            bpy.ops.object.mode_set('EXEC_DEFAULT', False, mode='EDIT')
            bpy.ops.wm.tool_set_by_id('EXEC_DEFAULT', False, name='builtin.select_circle')
            bpy.ops.object.mode_set('EXEC_DEFAULT', False, mode='OBJECT')
            bpy.ops.wm.tool_set_by_id('EXEC_DEFAULT', False, name='builtin.move')
        obj = bpy.data.objects[name]
        for index, domain in enumerate((obj.data.vertices, obj.data.edges, obj.data.polygons)):
            for number, element in enumerate(domain):
                element.select = (number + index) % 2 == 0
                element.hide = number == index
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        obj.data.update()
        if preselect:
            deselect()
        ortho()
        obj.location.x = .15
        yield from settle(8)
        sentinel = baseline('failed entry Undo sentinel A')
        sentinel_flags = raw_component_flags()
        obj.location.x = .3
        yield from settle()
        expected = baseline('failed entry Undo sentinel B')
        expected_flags = raw_component_flags()
        expected_slots = tool_slots()
        expected_recent = hotbox_runtime.recent.items()
        original_set_tool = object_modeling_ops._set_tool
        injection = {'fired': False, 'changed': False}

        def partial_activation_then_fail(context, identifier):
            if not injection['fired']:
                injection['fired'] = True
                original_set_tool(context, 'builtin.select_box')
                current = context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname
                injection['changed'] = current == 'builtin.select_box' and current != expected_slots[1]
                raise RuntimeError('intentional GUI acceptance partial tool activation failure')
            return original_set_tool(context, identifier)

        object_modeling_ops._set_tool = partial_activation_then_fail
        try:
            yield from action('W', point=project((.3, 0, 0)))
        finally:
            object_modeling_ops._set_tool = original_set_tool
        idle('injected activation failure')
        check(injection['fired'] and injection['changed'], 'failure fixture never changed actual Edit tool')
        check(state() == expected and raw_component_flags() == expected_flags,
              'failed partial activation did not restore full scene and raw component select/hide flags')
        check(tool_slots() == expected_slots, 'failed partial activation did not restore both mode tool slots')
        check(hotbox_runtime.recent.items() == expected_recent, 'failed partial activation entered Recent')
        # A failed entry must not push a wrapper step: next Undo crosses B to A.
        yield from undo_to(sentinel, 'failed entry creates no Undo step')
        check(raw_component_flags() == sentinel_flags, 'failure Undo sentinel changed raw component flags')
    print('PASS selected/preselected partial activation rollback, both tool slots and no Undo step', flush=True)

    # Selection wins over a different foreground object beneath the actual pointer.
    name = seed()
    selected = bpy.data.objects[name]
    with override():
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2))
    foreground = bpy.context.active_object
    foreground.select_set(False)
    selected.select_set(True)
    bpy.context.view_layer.objects.active = selected
    foreground_name = foreground.name
    foreground_before = mesh_state(foreground)
    ortho()
    yield from settle(8)
    expected = baseline('selected priority')
    yield from action('W', point=project((0, 0, 2)))
    activated('builtin.knife', [name])
    check(not bpy.data.objects[foreground_name].select_get()
          and mesh_state(bpy.data.objects[foreground_name]) == foreground_before,
          'pointer foreground overrode current selection')
    yield from undo_to(expected, 'selected priority')

    # Entire selected set is captured; shared data remains shared without copies.
    for shared in (False, True):
        name = seed()
        first = bpy.data.objects[name]
        other = bpy.data.objects.new('Other Mesh', first.data if shared else first.data.copy())
        bpy.context.collection.objects.link(other)
        other.location.x = 5
        other.select_set(True)
        other_name = other.name
        yield from settle()
        expected = baseline('multi object entry')
        yield from action('W')
        activated('builtin.knife', [name, other_name], shared=shared)
        check(bpy.context.active_object.name == name, 'multi entry changed active')
        check((bpy.data.objects[name].data == bpy.data.objects[other_name].data) == shared,
              'tool entry changed shared mesh data identity')
        yield from undo_to(expected, 'multi object entry')
    print('PASS selected priority, independent multi object and shared mesh data', flush=True)

    # Cancellation/stale sessions must retain externally changed state, never retarget.
    for cancel in ('center', 'disabled', 'escape', 'shift-first', 'selection', 'active', 'data', 'delete', 'collection-lock'):
        name = seed()
        other = bpy.data.objects.new('Other', bpy.data.objects[name].data.copy())
        bpy.context.collection.objects.link(other)
        other.location.x = 5
        yield from settle()
        yield from begin()
        yield from move_to(OBJECT, 'N' if cancel == 'disabled' else 'W')
        if cancel == 'center':
            event('MOUSEMOVE', 'NOTHING', origin, shift=True)
        elif cancel == 'escape':
            event('ESC', shift=True)
            event('ESC', 'RELEASE', shift=True)
        elif cancel == 'shift-first':
            event('LEFT_SHIFT', 'RELEASE')
        elif cancel == 'selection':
            other.select_set(True)
        elif cancel == 'active':
            bpy.context.view_layer.objects.active = other
        elif cancel == 'data':
            bpy.data.objects[name].data = bpy.data.objects[name].data.copy()
        elif cancel == 'collection-lock':
            bpy.context.collection.hide_select = True
        elif cancel == 'delete':
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        expected = state()
        recent = hotbox_runtime.recent.items()
        event('MOUSEMOVE', 'NOTHING', position, shift=cancel != 'shift-first')
        yield from settle()
        event('RIGHTMOUSE', 'RELEASE', shift=cancel != 'shift-first')
        event('LEFT_SHIFT', 'RELEASE')
        yield from settle()
        idle(cancel)
        check(state() == expected and hotbox_runtime.recent.items() == recent,
              cancel + ' committed or mutated a canceled/stale Object session')
        if cancel == 'collection-lock':
            bpy.context.collection.hide_select = False
    print('PASS cancellation, selection/active/data identity changes and deleted targets', flush=True)

    # Nearest native GPU candidate cannot pass through a non-Mesh foreground.
    name = seed()
    with override():
        bpy.ops.curve.primitive_bezier_circle_add(radius=1, location=(0, 0, 2))
    blocker = bpy.context.active_object
    blocker.data.dimensions = '2D'
    blocker.data.fill_mode = 'BOTH'
    deselect()
    ortho()
    yield from settle(10)
    expected = state()
    event('MOUSEMOVE', 'NOTHING', project((0, 0, 2)))
    event('LEFT_SHIFT', shift=True)
    event('RIGHTMOUSE', shift=True)
    yield from settle(8)
    check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'non-Mesh foreground was penetrated')
    yield from release()
    check(state() == expected, 'non-Mesh fallback changed object state')
    clear()
    yield from settle()
    yield from begin()
    yield from move_to('context.create', 'S')
    yield from release()
    idle('blank CREATE')
    check(bpy.context.mode == 'OBJECT' and len(bpy.context.scene.objects) == 1
          and len(bpy.context.active_object.data.vertices) == 8, 'true blank failed to CREATE cube')
    print('PASS non-Mesh foreground blocking and blank CREATE', flush=True)

    # Invalid complete selection sets must not silently narrow to the active Mesh.
    for invalid in ('mixed-type', 'locked', 'missing-active', 'collection-lock', 'hidden', 'outside-local-view'):
        name = seed()
        fixture_collection = None
        local_view = False
        if invalid == 'mixed-type':
            other = bpy.data.objects.new('Selected Empty', None)
            bpy.context.collection.objects.link(other)
            other.select_set(True)
        elif invalid == 'locked':
            bpy.data.objects[name].hide_select = True
        elif invalid == 'collection-lock':
            fixture_collection = bpy.data.collections.new('Object GUI locked collection')
            bpy.context.scene.collection.children.link(fixture_collection)
            obj = bpy.data.objects[name]
            fixture_collection.objects.link(obj)
            for old in tuple(obj.users_collection):
                if old != fixture_collection:
                    old.objects.unlink(obj)
            fixture_collection.hide_select = True
        elif invalid == 'hidden':
            bpy.data.objects[name].hide_set(True)
            # Native hidden bases may lose selection during depsgraph refresh.
        elif invalid == 'outside-local-view':
            other = bpy.data.objects.new('Selected Outside Local View', bpy.data.objects[name].data.copy())
            bpy.context.collection.objects.link(other)
            other.location.x = 5
            with override():
                bpy.ops.view3d.localview(frame_selected=False)
            local_view = True
            other.select_set(True)
            check(other.select_get() and not other.local_view_get(area.spaces.active)
                  and bpy.data.objects[name].local_view_get(area.spaces.active),
                  'local-view fixture did not retain selected excluded base')
        else:
            bpy.context.view_layer.objects.active = None
        yield from settle()
        expected = state()
        auto_deselected = invalid in {'locked', 'collection-lock', 'hidden'}
        if auto_deselected:
            check(not any(o.select_get() for o in bpy.context.view_layer.objects),
                  invalid + ' native fixture did not clear selected base')
        try:
            origin[:] = midpoint()
            event('MOUSEMOVE', 'NOTHING', origin)
            event('LEFT_SHIFT', shift=True)
            event('RIGHTMOUSE', shift=True)
            yield from settle()
            if auto_deselected:
                check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
                      invalid + ' native auto-deselection did not permit CREATE root')
            else:
                check('VIEW3D_OT_axismeld_hotbox' not in modals(), invalid + ' selected set incorrectly accepted')
            yield from release()
            idle(invalid + ' fallback')
            check(state() == expected, invalid + ' fallback changed selection or mode')
        finally:
            if local_view:
                with override():
                    bpy.ops.view3d.localview(frame_selected=False)
            if fixture_collection:
                fixture_collection.hide_select = False
                for obj in tuple(fixture_collection.objects):
                    bpy.context.scene.collection.objects.link(obj)
                    fixture_collection.objects.unlink(obj)
                bpy.data.collections.remove(fixture_collection)
            if invalid == 'hidden':
                bpy.data.objects[name].hide_set(False)

    for mutation in ('selection', 'data'):
        name = seed()
        deselect()
        ortho()
        yield from settle(8)
        yield from begin(point=project((0, 0, 0)))
        yield from move_to(OBJECT, 'W')
        if mutation == 'selection':
            bpy.data.objects[name].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
        else:
            bpy.data.objects[name].data = bpy.data.objects[name].data.copy()
        expected = state()
        event('MOUSEMOVE', 'NOTHING', position, shift=True)
        yield from settle()
        yield from release()
        idle('stale preselect ' + mutation)
        check(state() == expected, 'stale preselect ' + mutation + ' was committed')
    print('PASS invalid selected-set fallback, native lock/hide auto-deselection CREATE cancellation and stale preselect', flush=True)

    # Actual native strokes after activation: no direct mesh operator dispatch.
    for direction, tool in (('W', 'builtin.knife'), ('SW', 'builtin.loop_cut'), ('E', 'builtin.poly_build')):
        name = seed()
        ortho()
        yield from settle(8)
        yield from action(direction)
        activated(tool, [name])
        entered = state()
        if tool == 'builtin.knife':
            yield from click(project((-2, 0, 0)))
            check(any('knife' in m.lower() for m in modals()), 'Knife did not receive subsequent LMB')
            yield from click(project((2, 0, 0)))
            event('RET')
            event('RET', 'RELEASE')
        elif tool == 'builtin.loop_cut':
            yield from click(project((0, -2, 0)))
            event('ESC')
            event('ESC', 'RELEASE')
        else:
            # Drag boundary edge outward using Poly Build's native extrude gesture.
            start, end = project((0, -2, 0)), project((0, -3, 0))
            event('MOUSEMOVE', 'NOTHING', start)
            yield from settle(8)
            event('LEFTMOUSE', point=start)
            yield from settle(3)
            event('MOUSEMOVE', 'NOTHING', end)
            yield from settle(5)
            event('LEFTMOUSE', 'RELEASE', end)
        yield from settle(10)
        idle(tool + ' stroke')
        check(topology(name)[0] > 4 and topology(name)[2] > 1, tool + ' real stroke failed to edit mesh')
        yield from undo_to(entered, tool + ' separate native stroke Undo')
    event('W')
    event('W', 'RELEASE')
    yield from settle()
    check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == 'builtin.move',
          'QWER did not regain tool ownership')
    print('PASS real Knife, Loop Cut, Poly Build strokes and independent stroke Undo', flush=True)

    def configure(bindings):
        with override():
            config = runtime.load(session={'schema_version': 1, 'bindings': bindings})
            bpy.context.window_manager.keyconfigs.active = config
            bpy.context.window_manager.keyconfigs.update()
        yield from settle(8)
        check(not runtime.diagnostics, 'binding diagnostics: ' + repr(runtime.diagnostics))

    for bindings, trigger, shift, ctrl in (({MODEL: {'type': 'F13', 'ctrl': True}}, 'F13', False, True),
            ({MODEL: {'type': 'MIDDLEMOUSE', 'shift': True, 'ctrl': True}}, 'MIDDLEMOUSE', True, True),
            ({CREATE: None}, 'RIGHTMOUSE', True, False)):
        name = seed()
        yield from configure(bindings)
        expected = baseline('remapped Object')
        yield from action('W', trigger, shift, ctrl)
        activated('builtin.knife', [name])
        yield from undo_to(expected, 'remapped Object')
    yield from configure({MODEL: {'type': 'F13', 'ctrl': True}})
    seed()
    deselect()
    ortho()
    yield from settle()
    event('MOUSEMOVE', 'NOTHING', project((0, 0, 0)))
    event('LEFT_CTRL', ctrl=True)
    event('F13', ctrl=True)
    yield from settle()
    check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'keyboard MODEL preselected pointer target')
    event('F13', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from configure({MODEL: None})
    clear()
    yield from settle()
    yield from begin()
    yield from release()
    idle('disabled MODEL leaves CREATE')
    yield from configure({})
    print('PASS mouse/keyboard remap, keyboard no-preselect and independent disable', flush=True)

    # A direct leaf binding belongs to Object Mode and owns the same Undo
    # transaction; generated entries must migrate rather than accumulate.
    direct_leaf = 'tool.object_mesh_knife'

    def direct_leaf_entries():
        return [(km.name, item.type, item.value) for km in bpy.context.window_manager.keyconfigs.user.keymaps
                for item in km.keymap_items if item.idname == 'axismeld.command'
                and item.properties.command == direct_leaf]

    name = seed()
    yield from configure({direct_leaf: {'type': 'F13'}})
    check(direct_leaf_entries() == [('Object Mode', 'F13', 'PRESS')],
          'direct Object leaf keymap leaked outside Object Mode: ' + repr(direct_leaf_entries()))
    expected = baseline('direct Object Knife F13')
    event('MOUSEMOVE', 'NOTHING', midpoint())
    event('F13')
    event('F13', 'RELEASE')
    yield from settle(8)
    activated('builtin.knife', [name])
    yield from undo_to(expected, 'direct Object Knife F13')
    yield from configure({direct_leaf: {'type': 'F14'}})
    check(direct_leaf_entries() == [('Object Mode', 'F14', 'PRESS')],
          'direct Object leaf remap retained an old/generated wrong-map entry: ' + repr(direct_leaf_entries()))
    yield from configure({direct_leaf: None})
    check(not direct_leaf_entries(), 'disabled Object leaf retained generated keymap entries')
    yield from configure({})
    print('PASS direct Object leaf real F13 and Undo, Object-only keymap, remap/disable cleanup', flush=True)

    # Reverse the actual active Object keymap pair; eligibility must determine
    # which root owns Shift+RMB independently of insertion order.
    keymap = bpy.context.window_manager.keyconfigs.active.keymaps['Object Mode']
    pair = [item for item in keymap.keymap_items if item.idname == 'axismeld.command'
            and item.properties.command in {CREATE, MODEL}]
    check(len(pair) == 2, 'expected exactly CREATE/MODEL Object keymap pair')
    original_order = [item.properties.command for item in pair]
    saved = [(item.properties.command, item.type, item.value, item.shift, item.ctrl, item.alt, item.oskey)
             for item in pair]
    for item in pair:
        keymap.keymap_items.remove(item)
    for command, key, value, shift, ctrl, alt, oskey in reversed(saved):
        item = keymap.keymap_items.new('axismeld.command', key, value,
                                      shift=shift, ctrl=ctrl, alt=alt, oskey=oskey)
        item.properties.command = command
    bpy.context.window_manager.keyconfigs.update()
    yield from settle(8)
    reversed_order = [item.properties.command for item in keymap.keymap_items
                      if item.idname == 'axismeld.command' and item.properties.command in {CREATE, MODEL}]
    check(reversed_order == original_order[::-1], 'Object keymap pair did not actually reverse')
    name = seed()
    yield from settle()
    expected = baseline('reversed keymap MODEL')
    yield from action('W')
    activated('builtin.knife', [name])
    yield from undo_to(expected, 'reversed keymap MODEL')
    clear()
    yield from settle()
    yield from begin()
    yield from move_to('context.create', 'S')
    yield from release()
    idle('reversed keymap CREATE')
    check(bpy.context.mode == 'OBJECT' and len(bpy.context.scene.objects) == 1
          and len(bpy.context.active_object.data.vertices) == 8,
          'reversed keymap blank CREATE did not create one cube')
    yield from configure({})
    print('PASS reversed active Object keymap order preserves MODEL and CREATE ownership', flush=True)
    # Explicit Space center entry uses the live selected set through actual input.
    # Its generic directory dispatch must not expose enabled but inert Object leaves.
    name = seed()
    ortho()
    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'center_buttons': {'LEFTMOUSE': OBJECT}}})
    yield from settle(8)
    expected = baseline('Space custom center Object entry')
    recent = hotbox_runtime.recent.items()
    origin[:] = midpoint()
    event('MOUSEMOVE', 'NOTHING', origin)
    event('SPACE')
    yield from settle(16)
    event('LEFTMOUSE')
    yield from settle(8)
    check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
          'Space custom center Object root did not own exactly one session')
    check(state() == expected, 'Space custom center opening changed scene context')
    yield from move_to(OBJECT, 'W', shift=False)
    event('LEFTMOUSE', 'RELEASE')
    yield from settle(3)
    event('SPACE', 'RELEASE')
    yield from settle(8)
    activated('builtin.knife', [name])
    check(topology(name) == (4, 4, 1) and hotbox_runtime.recent.items() == recent,
          'Space Object persistent tool entry edited geometry or entered Recent')
    yield from undo_to(expected, 'Space custom center Object entry')
    # Space is an explicit directory and intentionally uses live valid selection.
    # This differs from the captured pointer session tested above.
    name = seed()
    other = bpy.data.objects.new('Space Live Selection', bpy.data.objects[name].data.copy())
    bpy.context.collection.objects.link(other)
    other.location.x = 5
    other_name = other.name
    yield from settle()
    origin[:] = midpoint()
    event('MOUSEMOVE', 'NOTHING', origin)
    event('SPACE')
    yield from settle(16)
    event('LEFTMOUSE')
    yield from settle(8)
    bpy.data.objects[name].select_set(False)
    other.select_set(True)
    bpy.context.view_layer.objects.active = other
    yield from move_to(OBJECT, 'W', shift=False)
    event('LEFTMOUSE', 'RELEASE')
    yield from settle(3)
    event('SPACE', 'RELEASE')
    yield from settle(8)
    activated('builtin.knife', [other_name])
    check(bpy.data.objects[name].mode == 'OBJECT' and not bpy.data.objects[name].select_get(),
          'explicit Space committed the old selection rather than the live valid selection')
    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {}})
    yield from settle(8)
    print('PASS explicit Space custom center Object Knife and one Undo', flush=True)

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

    def rendered_gaps(path, reference=False):
        """Find colored button spans from pixels, without calling the layout builder."""
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            pixels = list(image.pixels)
            cx, cy = origin
            if not reference:
                rgba=np.asarray(pixels,dtype=np.float32).reshape(height,width,4)
                cx,cy=observed_radial_rectangles(rgba,scale,{'N','NW','NE','W','E','SW','SE','S'})['center']
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
                # Include solid strips above/below label glyphs. Cropping to
                # the middle 13px can split a short inner-edge strip from the
                # rest of a disabled label and wrongly discard its true edge.
                offsets = (-12, 12) if row == 0 else sorted((row*20, row*44))
                for yy in range(int(cy + offsets[0]*scale), int(cy + offsets[1]*scale)+1):
                    if not 0 <= yy < height:
                        continue
                    for xx in range(max(2,int(cx-470*scale)),
                                    min(width-2,int(cx+470*scale))):
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
                if reference and row==1 and left and not right:
                    results.append(None)
                    continue
                check(left and right, f'{path.name}: no independent left/right rendered spans for row {row}: {spans}')
                print('PIXEL_EDGES', path.name, 'row', row, 'origin', tuple(origin), 'size', (width, height), 'spans', spans, flush=True)
                results.append((min(span[0] for span in right) - max(span[1] for span in left) - 1) / scale)
            if reference and results[0] is None:results[0]=results[2]
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
        measured = rendered_gaps(screenshot(label + '-views.png'),reference=True)
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
        for domain in ('OBJECT',):
            name = seed()
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
                actual_targets=rectangle_targets(OBJECT)
                center_x=(actual_targets['N'][0]+actual_targets['S'][0])/2
                center_y=(actual_targets['N'][1]+actual_targets['S'][1])/2
                event('MOUSEMOVE', 'NOTHING', (center_x+side*(reference[1]/2-10)*scale,center_y),shift=True)
                yield from settle()
                yield from release()
                idle('center return edge release')
                check(state() == before, f'{layout} {domain} center return edge dispatched an adjacent action')
        print('PASS Object rendered Views clearance', layout, reference, flush=True)
    print('AXISMELD_OBJECT_MODELING_EVENTS_PASS', flush=True)


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

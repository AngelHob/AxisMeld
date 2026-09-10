# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Focused real-scene and native-event acceptance for AxisMeld selection actions."""
import json
import os
from pathlib import Path
import sys
import traceback

import blf
import bmesh
import bpy

from axismeld.commands import COMMANDS, baseline_bindings


root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(root):
    raise RuntimeError('Only the isolated GUI runner may run this test')
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.edit.use_global_undo = True
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def settle(count=4):
    for _ in range(count):
        yield


def suite():
    expected_actions = ('selection.select_all', 'selection.grow', 'selection.shrink')
    for command in expected_actions:
        check(command in COMMANDS, f'installed {command} action missing')
        check(COMMANDS[command].key is None and COMMANDS[command].status == 'adapted',
              f'installed {command} metadata changed')

    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'failed to activate installed AxisMeld preset')
    yield from settle(8)
    from axismeld import adapter, hotbox_runtime, runtime

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def object_mode():
        if bpy.context.mode != 'OBJECT':
            with override():
                bpy.ops.object.mode_set(mode='OBJECT')

    def clear_scene():
        object_mode()
        for obj in tuple(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.view_layer.objects.active = None

    def mesh_object(name, vertices, faces, data=None):
        mesh = data or bpy.data.meshes.new(name + 'Mesh')
        if data is None:
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj

    def select_objects(objects, active):
        object_mode()
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active

    clear_scene()
    visible_mesh = mesh_object('VisibleMesh', [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
    visible_empty = bpy.data.objects.new('VisibleEmpty', None)
    bpy.context.collection.objects.link(visible_empty)
    camera_data = bpy.data.cameras.new('VisibleCameraData')
    visible_camera = bpy.data.objects.new('VisibleCamera', camera_data)
    bpy.context.collection.objects.link(visible_camera)
    hidden = mesh_object('HiddenMesh', [(0, 0, 0)], [])
    hidden.hide_set(True)
    locked = mesh_object('LockedMesh', [(0, 0, 0)], [])
    locked.hide_select = True
    bpy.context.view_layer.objects.active = None
    with override():
        check(adapter.available(bpy.context, 'selection.select_all') == (True, ''),
              'Object Select All incorrectly requires an active mesh')
        check(hotbox_runtime.dispatch(bpy.context, 'selection.select_all') == {'FINISHED'},
              'Object Select All did not preserve native FINISHED')
    check({obj.name for obj in bpy.context.selected_objects} ==
          {'VisibleMesh', 'VisibleEmpty', 'VisibleCamera'},
          f'Object Select All eligibility mismatch: {[obj.name for obj in bpy.context.selected_objects]!r}')
    with override():
        for command in ('selection.grow', 'selection.shrink'):
            check(adapter.available(bpy.context, command) == (False, 'Requires mesh Edit Mode'),
                  command + ' Object availability reason changed')
            check(hotbox_runtime.dispatch(bpy.context, command) == {'CANCELLED'},
                  command + ' dispatched outside mesh Edit Mode')
        wrong_area = next(a for a in win.screen.areas if a.type != 'VIEW_3D')
    wrong_region = next((r for r in wrong_area.regions if r.type == 'WINDOW'), wrong_area.regions[-1])
    with bpy.context.temp_override(window=win, area=wrong_area, region=wrong_region):
        check(not adapter.available(bpy.context, 'selection.select_all')[0],
              'selection action accepted a non-3D editor')
    with override():
        check(adapter.available(bpy.context, 'selection.unknown') ==
              (False, 'Unknown AxisMeld command'), 'unknown selection ID was accepted')
        check(hotbox_runtime.dispatch(bpy.context, 'selection.unknown') == {'CANCELLED'},
              'unknown selection ID dispatched')
    print('PASS Object eligibility, exact context gates and unknown rejection', flush=True)

    object_selection = {obj.name for obj in bpy.context.selected_objects}
    hotbox_runtime.recent._items = []
    hotbox_runtime.recent.record('transform.move')
    before_recent = hotbox_runtime.recent.items()
    with override():
        native_noop = bpy.ops.object.select_all('EXEC_DEFAULT', action='SELECT')
    check({obj.name for obj in bpy.context.selected_objects} == object_selection and
          bpy.context.mode == 'OBJECT' and hotbox_runtime.recent.items() == before_recent,
          'native already-selected Object Select All changed selection, mode or AxisMeld Recent')
    with override():
        result = hotbox_runtime.dispatch(bpy.context, 'selection.select_all')
    check(native_noop == {'FINISHED'} and result == native_noop,
          f'visible locked-object status changed: native={native_noop}, adapter={result}')
    check({obj.name for obj in bpy.context.selected_objects} == object_selection and
          bpy.context.mode == 'OBJECT',
          'visible locked-object Select All changed selection or mode')
    check(hotbox_runtime.recent.items() == ('selection.select_all', *before_recent),
          f'visible locked-object Select All Recent policy changed: {hotbox_runtime.recent.items()!r}')
    print('PASS selectable Object set already selected plus visible locked object returns FINISHED '
          'and records Recent', flush=True)

    locked.hide_set(True)
    object_selection = {obj.name for obj in bpy.context.selected_objects}
    hotbox_runtime.recent._items = []
    hotbox_runtime.recent.record('transform.rotate')
    before_recent = hotbox_runtime.recent.items()
    with override():
        native_noop = bpy.ops.object.select_all('EXEC_DEFAULT', action='SELECT')
    check({obj.name for obj in bpy.context.selected_objects} == object_selection and
          bpy.context.mode == 'OBJECT' and hotbox_runtime.recent.items() == before_recent,
          'native all-visible-selected Object Select All changed selection, mode or Recent')
    with override():
        result = hotbox_runtime.dispatch(bpy.context, 'selection.select_all')
    check(native_noop == {'CANCELLED'} and result == native_noop,
          f'all-visible-selected Object status changed: native={native_noop}, adapter={result}')
    check({obj.name for obj in bpy.context.selected_objects} == object_selection and
          bpy.context.mode == 'OBJECT' and hotbox_runtime.recent.items() == before_recent,
          'all-visible-selected Object Select All changed selection, mode or Recent')
    print('PASS all-visible-selected Object native CANCELLED and unchanged selection/mode/Recent',
          flush=True)

    clear_scene()
    with override():
        native_noop = bpy.ops.object.select_all('EXEC_DEFAULT', action='SELECT')
        before_recent = hotbox_runtime.recent.items()
        result = hotbox_runtime.dispatch(bpy.context, 'selection.select_all')
    check(result == native_noop, f'empty-scene status changed: native={native_noop}, adapter={result}')
    if result == {'FINISHED'}:
        check(hotbox_runtime.recent.items()[0] == 'selection.select_all',
              'FINISHED empty-scene result was not recorded')
    else:
        check(hotbox_runtime.recent.items() == before_recent,
              'non-FINISHED empty-scene result created a Recent record')
    print(f'PASS empty-scene native status and Recent policy: {result}', flush=True)

    component = mesh_object('ComponentMesh',
                            [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
                            [(0, 1, 2, 3)])
    select_objects([component], component)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
    for mode, collection_name in (((True, False, False), 'verts'),
                                  ((False, True, False), 'edges'),
                                  ((False, False, True), 'faces')):
        bpy.context.tool_settings.mesh_select_mode = mode
        with override():
            bpy.ops.mesh.reveal(select=False)
            bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(component.data)
        elements = getattr(bm, collection_name)
        elements.ensure_lookup_table()
        elements[0].hide_set(True)
        bmesh.update_edit_mesh(component.data)
        with override():
            check(hotbox_runtime.dispatch(bpy.context, 'selection.select_all') == {'FINISHED'},
                  f'{collection_name} Select All failed')
        bm = bmesh.from_edit_mesh(component.data)
        elements = getattr(bm, collection_name)
        elements.ensure_lookup_table()
        check(not elements[0].select and all(element.select for element in elements[1:] if not element.hide),
              f'{collection_name} hidden component was selected or visible component omitted')

    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    with override():
        bpy.ops.mesh.reveal(select=False)
        bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(component.data)
    bm.faces.ensure_lookup_table()
    edit_selection = {face.index for face in bm.faces if face.select}
    check(edit_selection == set(range(len(bm.faces))), 'failed to establish all-selected Edit fixture')
    hotbox_runtime.recent._items = []
    hotbox_runtime.recent.record('transform.scale')
    before_recent = hotbox_runtime.recent.items()
    with override():
        native_noop = bpy.ops.mesh.select_all('EXEC_DEFAULT', action='SELECT')
    bm = bmesh.from_edit_mesh(component.data)
    bm.faces.ensure_lookup_table()
    check({face.index for face in bm.faces if face.select} == edit_selection and
          bpy.context.mode == 'EDIT_MESH' and hotbox_runtime.recent.items() == before_recent,
          'native already-selected Edit Select All changed selection, mode or AxisMeld Recent')
    with override():
        result = hotbox_runtime.dispatch(bpy.context, 'selection.select_all')
    bm = bmesh.from_edit_mesh(component.data)
    bm.faces.ensure_lookup_table()
    check(native_noop == {'FINISHED'} and result == native_noop,
          f'already-selected Edit status changed: native={native_noop}, adapter={result}')
    check({face.index for face in bm.faces if face.select} == edit_selection and
          bpy.context.mode == 'EDIT_MESH',
          'already-selected Edit Select All changed selection or mode')
    check(hotbox_runtime.recent.items() == ('selection.select_all', *before_recent),
          f'already-selected Edit Select All Recent policy changed: {hotbox_runtime.recent.items()!r}')
    print('PASS already-selected Edit native FINISHED and observable Recent policy', flush=True)
    with override():
        bpy.ops.mesh.reveal(select=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    print('PASS vertex/edge/face Select All excludes hidden components', flush=True)

    clear_scene()
    tri = ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
    unique_a = mesh_object('UniqueA', *tri)
    unique_b = mesh_object('UniqueB', *tri)
    shared_a = mesh_object('SharedA', *tri)
    shared_b = mesh_object('SharedB', [], [], data=shared_a.data)
    select_objects([unique_a, unique_b, shared_a, shared_b], unique_a)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.mesh.select_all(action='DESELECT')
        check(hotbox_runtime.dispatch(bpy.context, 'selection.select_all') == {'FINISHED'},
              'multi-object Select All failed')
    for data in {unique_a.data, unique_b.data, shared_a.data}:
        bm = bmesh.from_edit_mesh(data)
        check(all(face.select for face in bm.faces), f'multi-object data {data.name} not selected')
    check(bpy.context.mode == 'EDIT_MESH', 'multi-object Select All changed mode')
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    print('PASS multi-object unique/shared-data Select All preserves Edit Mode', flush=True)

    clear_scene()
    vertices = [(float(x), float(y), 0.0) for y in range(6) for x in range(6)]
    faces = [(y*6+x, y*6+x+1, (y+1)*6+x+1, (y+1)*6+x)
             for y in range(5) for x in range(5)]
    grid = mesh_object('SelectionGrid', vertices, faces)
    uv_layer = grid.data.uv_layers.new(name='UVMap')
    for loop in grid.data.loops:
        co = grid.data.vertices[loop.vertex_index].co
        uv_layer.data[loop.index].uv = (co.x / 5.0, co.y / 5.0)
    initial_vertices = tuple(tuple(vertex.co) for vertex in grid.data.vertices)
    initial_faces = tuple(tuple(vertex for vertex in polygon.vertices) for polygon in grid.data.polygons)
    initial_uvs = tuple(tuple(loop.uv) for loop in uv_layer.data)
    select_objects([grid], grid)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

    def set_faces(indices):
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            face.select_set(face.index in indices)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)

    def selected_faces():
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        bm.faces.ensure_lookup_table()
        return {face.index for face in bm.faces if face.select}

    expected_grown_faces = {6, 7, 8, 11, 12, 13, 16, 17, 18}
    expected_shrunk_faces = {12}
    set_faces({12})
    with override():
        check(hotbox_runtime.dispatch(bpy.context, 'selection.grow') == {'FINISHED'}, 'grid grow failed')
    check(selected_faces() == expected_grown_faces,
          f'Face Step grow mismatch: {selected_faces()!r}')
    set_faces(expected_grown_faces)
    with override():
        check(hotbox_runtime.dispatch(bpy.context, 'selection.shrink') == {'FINISHED'}, 'grid shrink failed')
    check(selected_faces() == expected_shrunk_faces,
          f'Face Step shrink mismatch: {selected_faces()!r}')
    check(bpy.context.mode == 'EDIT_MESH', 'Grow/Shrink changed Edit Mode')
    bm = bmesh.from_edit_mesh(grid.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    live_uv_layer = bm.loops.layers.uv['UVMap']
    live_vertices = tuple(tuple(vertex.co) for vertex in bm.verts)
    live_faces = tuple(tuple(loop.vert.index for loop in face.loops) for face in bm.faces)
    live_uvs = tuple(tuple(loop[live_uv_layer].uv) for face in bm.faces for loop in face.loops)
    check(live_vertices == initial_vertices and live_faces == initial_faces and live_uvs == initial_uvs,
          'selection actions changed mesh counts/coordinates or UV coordinates')
    print('PASS 5x5 Face Step grow/shrink literals and geometry/UV invariants', flush=True)

    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_geometry_fixture import ellipse_page
    scale = bpy.context.preferences.system.ui_scale
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    position = [cx, cy]

    def event(kind, value='PRESS', point=None):
        if point is not None:
            position[:] = [int(point[0]), int(point[1])]
        win.event_simulate(type=kind, value=value, x=position[0], y=position[1])

    def midpoint(rect):
        check(rect is not None, 'event fixture selected an off-page item')
        x, y, width, height = rect
        return x + width / 2, y + height / 2

    def label_width(label):
        blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
        icons = {'Object / Component', 'Vertex', 'Edge', 'Face', 'Select All',
                 'Grow Selection', 'Shrink Selection'}
        return blf.dimensions(0, label)[0] / scale + (20 if label in icons else 0)

    labels = ['Object / Component', '', 'Vertex', 'Edge', 'Face',
              'Select All', 'Grow Selection', 'Shrink Selection']
    center_width = (label_width('AxisMeld') + 40) * scale
    center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)

    def positions(anchor):
        return ellipse_page(anchor, labels, label_width,
                            (region.x, region.y, region.width, region.height), scale)['items']

    def modal_open():
        return any(operator.bl_idname == 'VIEW3D_OT_axismeld_hotbox'
                   for operator in win.modal_operators)

    def open_box():
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        yield from settle()
        event('SPACE')
        yield from settle()

    def release_space():
        event('SPACE', 'RELEASE')
        yield from settle()
        check(not win.screen.is_animation_playing, 'selection leaf leaked Space playback')

    def anchor_undo(before, sentinel):
        set_faces(sentinel)
        with override():
            bpy.ops.ed.undo_push(message='AxisMeld selection sentinel')
        yield from settle()
        set_faces(before)
        with override():
            bpy.ops.ed.undo_push(message='AxisMeld selection pre-action')
        yield from settle()

    def verify_tools(command):
        for key, tool in (('W', 'builtin.move'), ('E', 'builtin.rotate'), ('R', 'builtin.scale')):
            event(key); event(key, 'RELEASE')
            yield from settle()
            check(bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname == tool,
                  f'{command}: {key} tool unavailable immediately after hotbox close')

    yield from anchor_undo({12}, {0})
    common_labels = ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
    widths = [label_width(label) + 40 for label in common_labels]
    common_span = sum(widths) + 10 * (len(widths)-1)
    start = cx/scale - common_span/2
    select_x = start + sum(widths[:3]) + 30
    select_rect = (select_x*scale, (cy+96*scale)-19*scale, widths[3]*scale, 38*scale)
    yield from open_box()
    event('LEFTMOUSE', point=midpoint(select_rect)); event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    menu_items = positions(select_rect)
    screenshot = artifacts / 'selection-select-menu.png'
    with override():
        bpy.ops.screen.screenshot(filepath=str(screenshot))
    event('LEFTMOUSE', point=midpoint(menu_items[5])); event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    check(selected_faces() == set(range(25)), 'clicked Select All leaf did not select all faces')
    check(not modal_open() and hotbox_runtime.recent.items()[0] == 'selection.select_all',
          'clicked Select All did not close-before and record Recent')
    yield from release_space()
    yield from verify_tools('selection.select_all')
    with override():
        check(bpy.ops.ed.undo() == {'FINISHED'}, 'Select All event undo failed')
    yield from settle()
    grid = bpy.data.objects['SelectionGrid']
    check(bpy.context.mode == 'EDIT_MESH' and selected_faces() == {12},
          f'one undo did not restore pre-Select All selection: {selected_faces()!r}')

    hotbox_runtime.reload_settings(bpy.context, session={
        'schema_version': 1, 'settings': {'center_buttons': {'RIGHTMOUSE': 'common.select'}}})
    for command, index, before, expected in (
            ('selection.grow', 6, {12}, expected_grown_faces),
            ('selection.shrink', 7, expected_grown_faces, expected_shrunk_faces)):
        yield from anchor_undo(before, {0} if before != {0} else {24})
        yield from open_box()
        event('RIGHTMOUSE')
        yield from settle()
        event('MOUSEMOVE', 'NOTHING', midpoint(positions(center)[index]))
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check(selected_faces() == expected, command + ' held hotbox result mismatch')
        check(not modal_open() and hotbox_runtime.recent.items()[0] == command,
              command + ' did not close-before and record Recent')
        yield from release_space()
        yield from verify_tools(command)
        with override():
            check(bpy.ops.ed.undo() == {'FINISHED'}, command + ' event undo failed')
        yield from settle()
        grid = bpy.data.objects['SelectionGrid']
        check(bpy.context.mode == 'EDIT_MESH' and selected_faces() == before,
              f'{command}: one undo did not restore pre-action selection: {selected_faces()!r}')
        set_faces(expected)
    before_selection = selected_faces()
    before_recent = hotbox_runtime.recent.items()
    yield from open_box()
    event('RIGHTMOUSE')
    yield from settle()
    event('MOUSEMOVE', 'NOTHING', midpoint(positions(center)[6]))
    event('ESC'); event('ESC', 'RELEASE')
    yield from settle()
    event('RIGHTMOUSE', 'RELEASE')
    yield from release_space()
    check(selected_faces() == before_selection and hotbox_runtime.recent.items() == before_recent,
          'canceled selection gesture changed scene or Recent')
    print('PASS real clicked/held selection leaves close, Recent, W/E/R and cancellation', flush=True)

    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    clear_scene()
    mesh_object('BoundA', [(0, 0, 0)], [])
    mesh_object('BoundB', [(1, 0, 0)], [])
    directory = runtime.profile_directory()
    check(directory.resolve().is_relative_to(root), 'private profile directory escaped test root')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'user.json').write_text(json.dumps({
        'schema_version': 1, 'bindings': {'selection.select_all': {'type': 'F13'}}}),
        encoding='utf-8')
    config = bpy.context.window_manager.keyconfigs.active
    config.preferences.use_file_overrides = True
    config = runtime.load()
    bpy.context.window_manager.keyconfigs.update()
    binding = next(item for keymap in config.keymaps for item in keymap.keymap_items
                   if item.idname == 'axismeld.command' and
                   item.properties.command == 'selection.select_all')
    check(binding.type == 'F13', 'private Select All binding did not reload')
    check(all(COMMANDS[command].key is None for command in expected_actions) and
          baseline_bindings()['view.frame_all']['type'] == 'A',
          'default no-key metadata or existing A binding changed')
    bpy.context.view_layer.objects.active = None
    event('MOUSEMOVE', 'NOTHING', (cx, cy)); yield from settle()
    event('F13'); event('F13', 'RELEASE'); yield from settle()
    check({obj.name for obj in bpy.context.selected_objects} == {'BoundA', 'BoundB'},
          'reloaded private Select All binding was ineffective')
    print('PASS private user binding save/reload and unchanged defaults', flush=True)
    print('AXISMELD_SELECTION_EVENTS_PASS', flush=True)


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

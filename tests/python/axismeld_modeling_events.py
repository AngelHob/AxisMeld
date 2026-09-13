# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Installed M3 menus, actual input, native modal lifetime and one-step undo."""
import json
import os
from pathlib import Path
import sys
import traceback

import blf
import bmesh
import bpy

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_geometry_fixture import native_page
from axismeld import adapter, hotbox_runtime
from axismeld.modeling_registry import CATEGORIES, SPECS

bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.edit.use_global_undo = True
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=6):
    for _ in range(count):
        yield


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'preset activation failed')
    yield from settle(8)
    from axismeld import runtime
    check(not runtime.diagnostics, 'runtime diagnostics: ' + repr(runtime.diagnostics))
    scale = bpy.context.preferences.system.ui_scale
    cx, cy = region.x + region.width/2, region.y + region.height/2
    position = [cx, cy]

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def event(kind, value='PRESS', xy=None, **mods):
        if xy is not None:
            position[:] = xy
        win.event_simulate(type=kind, value=value, x=int(position[0]), y=int(position[1]), **mods)

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def image(name):
        with override():
            bpy.ops.screen.screenshot(filepath=str(artifacts / name))

    def clear():
        with override():
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for obj in tuple(bpy.data.objects):
                bpy.data.objects.remove(obj, do_unlink=True)

    def snapshot_nodes():
        with override():
            document = json.loads(hotbox_runtime.snapshot(bpy.context))
        pending, nodes = list(document['menus']), {}
        while pending:
            node = pending.pop()
            nodes[node['id']] = node
            pending.extend(node['children'])
        return nodes

    def open_menu(identifier):
        with override():
            hotbox_runtime.reload_settings(bpy.context, session={
                'schema_version': 1, 'settings': {'center_buttons': {'LEFTMOUSE': identifier}}})
        event('MOUSEMOVE', 'NOTHING', (cx, cy))
        yield from settle()
        event('SPACE')
        yield from settle(16)
        event('LEFTMOUSE')
        yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
              'native menu failed to open: ' + identifier + repr(modals()))

    def close_menu():
        event('ESC')
        event('ESC', 'RELEASE')
        event('SPACE', 'RELEASE')
        yield from settle()
        check(not modals(), 'menu cancellation retained handlers: ' + repr(modals()))

    clear()
    with override():
        bpy.ops.mesh.primitive_cube_add()
    yield from settle()
    for category, identifier in CATEGORIES.items():
        nodes = snapshot_nodes()
        check(nodes[identifier]['kind'] == 'menu' and nodes[identifier]['enabled'], category)
        yield from open_menu(identifier)
        image('m3-menu-' + category.lower().replace(' ', '-') + '.png')
        yield from close_menu()
    print('PASS twelve actual Space native menu entries and cancellation', flush=True)

    # A real native list click changes a mutually exclusive setting; hover is not state.
    pivot_menu = 'common.modify.m3_pivot'
    yield from open_menu(pivot_menu)
    entries = snapshot_nodes()[pivot_menu]['children']
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    center_width = (blf.dimensions(0, 'AxisMeld')[0]/scale + 20 + 40)*scale
    center = (cx-center_width/2, cy-19*scale, center_width, 38*scale)
    def measure(label):
        return blf.dimensions(0, label)[0]/scale + 20
    page = native_page(center, [n['label'] for n in entries], measure,
                       (region.x, region.y, region.width, region.height), scale)
    index = next(i for i, n in enumerate(entries) if n['command'] == 'pivot.active')
    x, y, width, height = page['items'][index]
    event('MOUSEMOVE', 'NOTHING', (x+width/2, y+height/2))
    yield from settle()
    event('LEFTMOUSE')
    event('LEFTMOUSE', 'RELEASE')
    event('SPACE', 'RELEASE')
    yield from settle()
    check(not modals(), 'radio selection retained a handler')
    check(bpy.context.scene.tool_settings.transform_pivot_point == 'ACTIVE_ELEMENT',
          'actual menu radio click did not change the native pivot')
    states = snapshot_nodes()[pivot_menu]['children']
    check([n['command'] for n in states if n.get('checked')] == ['pivot.active'], 'radio state is not exclusive')
    yield from open_menu(pivot_menu)
    image('m3-pivot-radio.png')
    yield from close_menu()
    print('PASS actual radio list click and exclusive native state', flush=True)

    # Keymap routes the verified Maya Duplicate shortcut to the shared native action.
    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    with override():
        bpy.ops.ed.undo_push(message='M3 duplicate baseline')
    before = len(bpy.context.scene.objects)
    event('LEFT_CTRL', ctrl=True)
    event('D', ctrl=True)
    event('D', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle(10)
    check(len(bpy.context.scene.objects) == before + 1, 'Ctrl+D did not duplicate once')
    check(not modals(), 'Ctrl+D should duplicate in place without moving')
    event('Z')
    event('Z', 'RELEASE')
    yield from settle(10)
    check(len(bpy.context.scene.objects) == before, 'one Z failed to undo duplication')
    event('LEFT_CTRL', ctrl=True)
    event('Y', ctrl=True)
    event('Y', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle(10)
    check(len(bpy.context.scene.objects) == before + 1, 'Maya Ctrl+Y redo alias failed')
    event('Z')
    event('Z', 'RELEASE')
    yield from settle(10)
    check(len(bpy.context.scene.objects) == before, 'redo alias did not share the native undo stack')
    print('PASS Ctrl+D native geometry and one Z undo', flush=True)

    # A compound grouping operation must own precisely one undo entry.
    with override():
        bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0))
        for obj in bpy.context.scene.objects:
            obj.select_set(True)
        bpy.ops.ed.undo_push(message='M3 grouping baseline')
        check(hotbox_runtime.dispatch(bpy.context, 'edit.group') == {'FINISHED'}, 'Group failed')
    yield from settle()
    check(any(obj.type == 'EMPTY' for obj in bpy.context.scene.objects), 'Group did not create DAG parent')
    with override():
        bpy.ops.ed.undo()
    yield from settle()
    check(len(bpy.context.scene.objects) == 2 and not any(o.parent for o in bpy.context.scene.objects),
          'compound Group did not undo in one step')
    print('PASS compound Group parent structure and one-step undo', flush=True)

    clear()
    with override():
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        name = obj.name
        obj.modifiers.new('Bake Topology', 'SUBSURF').levels = 1
        obj.modifiers.new('Keep Deformation', 'SIMPLE_DEFORM').angle = .4
        bpy.ops.ed.undo_push(message='M3 non-deformer bake baseline')
        check(hotbox_runtime.dispatch(bpy.context, 'edit.bake_selected_non_deform') == {'FINISHED'},
              'non-deformer history bake failed')
        check(len(obj.data.polygons) > 6 and [m.type for m in obj.modifiers] == ['SIMPLE_DEFORM'],
              'history bake lost the retained deformer or did not bake topology')
    yield from settle()
    with override():
        bpy.ops.ed.undo()
    yield from settle()
    obj = bpy.data.objects[name]
    check(len(obj.data.polygons) == 6 and [m.type for m in obj.modifiers] == ['SUBSURF', 'SIMPLE_DEFORM'],
          'one undo failed to restore the mesh and complete modifier stack')
    print('PASS mesh history bake preserves deformer and restores stack in one undo', flush=True)

    # Native modifier wrappers alter evaluated geometry and undo all owned resources.
    for identifier in ('deform.bend', 'deform.lattice', 'deform.displace'):
        clear()
        with override():
            bpy.ops.mesh.primitive_cube_add()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.subdivide(number_cuts=3)
            bpy.ops.object.mode_set(mode='OBJECT')
            obj = bpy.context.active_object
            name = obj.name
            bpy.ops.ed.undo_push(message='M3 deformation baseline')
            before = [tuple(v.co) for v in obj.data.vertices]
            resources = (len(bpy.data.objects), len(bpy.data.lattices), len(bpy.data.textures))
            check(hotbox_runtime.dispatch(bpy.context, identifier) == {'FINISHED'}, identifier)
            bpy.context.view_layer.update()
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            after = [tuple(v.co) for v in evaluated.data.vertices]
            check(any(sum(abs(a-b) for a, b in zip(p, q)) > 1e-5 for p, q in zip(before, after)),
                  identifier + ' produced no evaluated deformation')
        yield from settle()
        with override():
            bpy.ops.ed.undo()
        yield from settle()
        restored = bpy.data.objects.get(name)
        check(restored is not None and not restored.modifiers, identifier + ' modifier survived one undo')
        check((len(bpy.data.objects), len(bpy.data.lattices), len(bpy.data.textures)) == resources,
              identifier + ' owned resources survived one undo')
    print('PASS real deformation and one-step undo of modifier/cage/texture', flush=True)

    clear()
    with override():
        check(hotbox_runtime.dispatch(bpy.context, 'mesh.create_cube') == {'FINISHED'}, 'parameter cube')
    yield from settle()
    before_recent = hotbox_runtime.recent.items()
    with override():
        check(adapter.available(bpy.context, 'edit.adjust_last_operation')[0], 'parameter entry unavailable')
        # Blender opens the redo popup and deliberately returns CANCELLED.
        check(hotbox_runtime.dispatch(bpy.context, 'edit.adjust_last_operation') == {'CANCELLED'},
              'unexpected native redo popup result')
    yield from settle(10)
    image('m3-adjust-last-operation.png')
    event('ESC')
    event('ESC', 'RELEASE')
    yield from settle()
    check(hotbox_runtime.recent.items() == before_recent, 'parameter UI entered Recent')
    print('PASS native parameter popup preserves UI-only cancellation and Recent', flush=True)

    # Actual modal bevel cancellation must preserve topology and not add successful Recent.
    clear()
    with override():
        bpy.ops.mesh.primitive_cube_add()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    yield from settle()
    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    event('F7')
    event('F7', 'RELEASE')
    yield from settle()
    check(tuple(bpy.context.tool_settings.mesh_select_mode) == (True, True, True), 'F7 multi-component failed')
    event('LEFT_CTRL', ctrl=True)
    event('T', ctrl=True)
    event('T', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle()
    check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == 'builtin.transform',
          'Ctrl+T did not activate the native universal tool')
    event('F10')
    event('F10', 'RELEASE')
    yield from settle()
    with override():
        bpy.ops.mesh.hide(unselected=False)
    event('LEFT_CTRL', ctrl=True)
    event('LEFT_ALT', ctrl=True, alt=True)
    event('H', ctrl=True, alt=True)
    event('H', 'RELEASE', ctrl=True, alt=True)
    event('LEFT_ALT', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle()
    check(not any(v.hide for v in bmesh.from_edit_mesh(bpy.context.active_object.data).verts),
          'Ctrl+Alt+H did not reveal mesh components')
    with override():
        bpy.ops.mesh.select_all(action='SELECT')
    print('PASS F7 multi-component, Ctrl+T tool and Ctrl+Alt+H visibility', flush=True)
    before_mesh = tuple(len(getattr(bmesh.from_edit_mesh(bpy.context.active_object.data), domain))
                        for domain in ('verts', 'edges', 'faces'))
    hotbox_runtime.recent._items = []
    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    event('LEFT_CTRL', ctrl=True)
    event('B', ctrl=True)
    event('B', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle(8)
    check(any('bevel' in name.lower() for name in modals()), 'Ctrl+B failed to invoke native bevel')
    event('MOUSEMOVE', 'NOTHING', (cx + 60, cy))
    yield from settle()
    event('ESC')
    event('ESC', 'RELEASE')
    yield from settle()
    after_mesh = tuple(len(getattr(bmesh.from_edit_mesh(bpy.context.active_object.data), domain))
                       for domain in ('verts', 'edges', 'faces'))
    check(before_mesh == after_mesh and not modals(), 'native bevel Esc did not restore geometry/lifetime')
    check(not hotbox_runtime.recent.items(), 'modal start entered successful Recent')
    print('PASS native Ctrl+B modal cancel, geometry and Recent', flush=True)
    with override():
        bpy.ops.ed.undo_push(message='M3 bevel confirmation baseline')
    event('MOUSEMOVE', 'NOTHING', (cx, cy))
    event('LEFT_CTRL', ctrl=True)
    event('B', ctrl=True)
    event('B', 'RELEASE', ctrl=True)
    event('LEFT_CTRL', 'RELEASE')
    yield from settle(8)
    event('MOUSEMOVE', 'NOTHING', (cx + 80, cy + 30))
    yield from settle()
    event('LEFTMOUSE')
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    committed = tuple(len(getattr(bmesh.from_edit_mesh(bpy.context.active_object.data), domain))
                      for domain in ('verts', 'edges', 'faces'))
    check(committed != before_mesh and not modals(), 'native bevel confirmation did not commit topology')
    event('Z')
    event('Z', 'RELEASE')
    yield from settle(10)
    restored = tuple(len(getattr(bmesh.from_edit_mesh(bpy.context.active_object.data), domain))
                     for domain in ('verts', 'edges', 'faces'))
    check(restored == before_mesh, 'one Z failed to undo confirmed native bevel')
    print('PASS native Ctrl+B confirmation and one-step topology undo', flush=True)

    # Curve and Surface get only their native modeling command families.
    for operator_name, mode, category in (
            ('primitive_bezier_curve_add', 'EDIT_CURVE', 'Curves'),
            ('primitive_nurbs_surface_surface_add', 'EDIT_SURFACE', 'Surfaces')):
        clear()
        with override():
            namespace = bpy.ops.curve if mode == 'EDIT_CURVE' else bpy.ops.surface
            getattr(namespace, operator_name)()
            bpy.ops.object.mode_set(mode='EDIT')
        yield from settle()
        check(bpy.context.mode == mode, 'wrong shape Edit mode')
        with override():
            check(adapter.available(bpy.context, 'hotbox.open')[0], 'main menu mode gate')
            check(not adapter.available(bpy.context, 'context.component_hotbox')[0], 'mesh RMB leaked to shape mode')
            check(not adapter.available(bpy.context, 'transform.move')[0], 'QWER hotbox leaked to shape mode')
        nodes = snapshot_nodes()
        enabled = [n for n in nodes.values() if n['kind'] == 'command' and n['enabled'] and
                   n['command'] in SPECS and SPECS[n['command']].category == category]
        check(enabled, category + ' has no native available operations')
        yield from open_menu(CATEGORIES[category])
        image('m3-' + mode.lower() + '.png')
        yield from close_menu()
    print('PASS Curve/Surface Space entries and mesh-only context exclusion', flush=True)
    print('AXISMELD_MODELING_EVENTS_PASS', flush=True)


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

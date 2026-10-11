# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual Ctrl mouse entries and deferred Edit preselection in a disposable GUI."""
import json
import os
from pathlib import Path
import sys
import traceback
import numpy as np
import bpy
import bmesh
from mathutils import Quaternion, Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.edit.use_global_undo = True
sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles, observed_menu_rectangles, menu_background_mask


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
    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'Preset failed')
    with override():
        bpy.ops.screen.screen_full_area()
    yield from settle(10)
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    area.spaces.active.show_region_ui = False
    area.spaces.active.show_region_toolbar = False
    region.data.view_rotation = Quaternion((1, 0, 0, 0))
    region.data.view_location = Vector((0, 0, 0))
    region.data.view_distance = 10
    region.data.view_perspective = 'ORTHO'
    scale = bpy.context.preferences.system.ui_scale
    pos = [region.x + region.width // 2, region.y + region.height // 2]
    def event(kind, value='PRESS', point=None, **mods):
        if point is not None:
            pos[:] = point
        win.event_simulate(type=kind, value=value, x=int(pos[0]), y=int(pos[1]), **mods)
    def modals():
        return [op.bl_idname for op in win.modal_operators]
    def state():
        obj = bpy.data.objects['ContextTarget']
        bm = bmesh.from_edit_mesh(obj.data)
        return (bpy.context.mode, bpy.context.active_object.name,
                tuple(bpy.context.tool_settings.mesh_select_mode),
                tuple((tuple(v.co), v.select, v.hide) for v in bm.verts),
                tuple((e.select, e.hide) for e in bm.edges),
                tuple((f.select, f.hide) for f in bm.faces))
    def selected(domain):
        bm = bmesh.from_edit_mesh(bpy.data.objects['ContextTarget'].data)
        return sum(item.select for item in getattr(bm, domain))
    def begin(ctrl=False, shift=False, point=None):
        event('MOUSEMOVE', 'NOTHING', point)
        yield from settle()
        if ctrl:
            event('LEFT_CTRL', ctrl=True)
        if shift:
            event('LEFT_SHIFT', ctrl=ctrl, shift=True)
        event('RIGHTMOUSE', ctrl=ctrl, shift=shift)
        yield from settle()
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'Context entry did not open: ' + repr(modals()))
    def release(ctrl=False, shift=False):
        event('RIGHTMOUSE', 'RELEASE', ctrl=ctrl, shift=shift)
        yield from settle(3)
        if shift:
            event('LEFT_SHIFT', 'RELEASE', ctrl=ctrl)
        if ctrl:
            event('LEFT_CTRL', 'RELEASE')
        yield from settle()
    def pixels(name='context-entry'):
        path = artifacts / (name + '.png')
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            return np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
        finally:
            bpy.data.images.remove(image)
    def target(direction, directions=('N','NE','E','SE','S','SW','W','NW')):
        rect = observed_radial_rectangles(pixels(), scale, directions)['rects'][direction]
        return ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
    with override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        mesh = bpy.data.meshes.new('ContextTarget')
        mesh.from_pydata([(-2,-2,0),(0,-2,0),(0,2,0),(-2,2,0),(2,-2,0),(2,2,0)], [],
                         [(0,1,2,3),(1,4,5,2)])
        obj = bpy.data.objects.new('ContextTarget', mesh)
        bpy.context.collection.objects.link(obj)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
    yield from settle(10)
    point = location_3d_to_region_2d(region, region.data, Vector((-1,0,0)))
    point = (region.x + point.x, region.y + point.y)
    before = state()
    # RED against the old runtime: this must open despite no existing selected face.
    yield from begin(shift=True, point=point)
    check(state() == before, 'Open mutated the empty selection')
    event('ESC', shift=True)
    yield from settle()
    yield from release(shift=True)
    check(state() == before and not modals(), 'Esc cancellation leaked selection or ownership')
    from axismeld import hotbox_runtime
    for colors in (bpy.context.preferences.themes[0].user_interface.wcol_menu,
                   bpy.context.preferences.themes[0].user_interface.wcol_menu_back,
                   bpy.context.preferences.themes[0].user_interface.wcol_menu_item):
        colors.inner = colors.inner_sel = (.8, .04, .65, 1)
    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'transparency': 0, 'appearance': {'theme_background': True, 'brightness': 0}}})
        bpy.ops.ed.undo_push(message='Empty Edit preselection baseline')
    yield from begin(shift=True, point=point)
    event('MOUSEMOVE', 'NOTHING', target('NE'), shift=True)
    yield from settle()
    check(state() == before, 'Hover mutated the empty selection')
    yield from release(shift=True)
    bm = bmesh.from_edit_mesh(bpy.data.objects['ContextTarget'].data)
    check((len(bm.verts), len(bm.edges), len(bm.faces)) == (7,11,5), 'Poke did not affect exactly the pointer face')
    check(not modals(), 'Submitted action left modal ownership')
    with override():
        bpy.ops.ed.undo()
    yield from settle(10)
    check(state() == before, 'One Undo did not restore geometry and empty selection')
    print('PASS Edit empty pointer face: open/hover/Esc read-only; actual Poke; one Undo', flush=True)

    # Native Bevel replaces its BMesh backup on cancel; Crease cancels in place.
    # Both must restore the empty input selection without undoing a later operation.
    with override():
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
    yield from settle()
    edge_point = location_3d_to_region_2d(region, region.data, Vector((0,0,0)))
    edge_point = (region.x + edge_point.x, region.y + edge_point.y)
    empty_edge = state()
    for command in ('Bevel', 'Crease'):
        yield from begin(shift=True, point=edge_point)
        check(state() == empty_edge, command + ' menu open selected the pointer edge')
        if command == 'Bevel':
            action_point = target('E')
        else:
            columns = observed_menu_rectangles(menu_background_mask(pixels()), 120*scale, 100*scale)
            check(len(columns) == 1, 'Expected one visible Edge companion menu: ' + repr(columns))
            x0, y0, x1, y1 = columns[0]
            # First visible companion row is Crease Tool; stay away from its options cell.
            action_point = (x0 + (x1-x0)*.35, y1 - 11*scale)
        event('MOUSEMOVE', 'NOTHING', action_point, shift=True)
        yield from settle()
        check(state() == empty_edge, command + ' hover selected the pointer edge')
        yield from release(shift=True)
        expected = 'MESH_OT_bevel' if command == 'Bevel' else 'TRANSFORM_OT_edge_crease'
        check(expected in modals(), command + ' row did not invoke its native modal: ' + repr(modals()))
        check(selected('edges') == 1, command + ' did not target exactly the pointer edge')
        # Move within the native modal before Esc, so cancellation restores real tentative changes.
        event('MOUSEMOVE', 'NOTHING', (action_point[0] + 34*scale, action_point[1] + 12*scale))
        yield from settle()
        event('ESC')
        yield from settle(10)
        check(not modals() and state() == empty_edge,
              command + ' native Esc left selection, geometry, domain or modal ownership behind')
        print('PASS empty pointer edge -> ' + command + ' native modal -> movement -> Esc restores input', flush=True)

    # A confirmed modal still owns one Undo transaction, including preselection.
    with override():
        bpy.ops.ed.undo_push(message='Empty edge before confirmed Crease')
    yield from begin(shift=True, point=edge_point)
    columns = observed_menu_rectangles(menu_background_mask(pixels()), 120*scale, 100*scale)
    x0, y0, x1, y1 = columns[0]
    action_point = (x0 + (x1-x0)*.35, y1 - 11*scale)
    event('MOUSEMOVE', 'NOTHING', action_point, shift=True)
    yield from settle()
    yield from release(shift=True)
    check('TRANSFORM_OT_edge_crease' in modals(), 'Crease confirm test did not start native modal')
    event('MOUSEMOVE', 'NOTHING', (action_point[0]+34*scale, action_point[1]))
    yield from settle()
    event('RET')
    yield from settle(10)
    check(not modals(), 'Crease confirmation did not finish')
    with override():
        bpy.ops.ed.undo()
    yield from settle(10)
    check(state() == empty_edge, 'One Crease Undo did not restore empty edge input')
    print('PASS confirmed pointer-edge Crease: one Undo restores empty input', flush=True)

    # Conversion is a distinct held-RMB session; select a face explicitly as input.
    with override():
        bpy.ops.mesh.select_mode(type='FACE')
        bm = bmesh.from_edit_mesh(bpy.data.objects['ContextTarget'].data)
        bm.faces.ensure_lookup_table()
        bm.faces[0].select_set(True)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(bpy.data.objects['ContextTarget'].data)
    yield from settle()
    yield from begin(ctrl=True, point=(region.x + region.width/2, region.y + region.height*.65))
    parent = target('W')
    event('MOUSEMOVE', 'NOTHING', parent, ctrl=True)
    yield from settle()
    boxes = observed_menu_rectangles(menu_background_mask(pixels()), 60*scale, 13*scale)
    candidates = [((x0+x1)/2, (y0+y1)/2) for x0,y0,x1,y1 in boxes
                  if abs((y0+y1)/2-parent[1]) < 10*scale and (x0+x1)/2 < parent[0]-25*scale]
    check(candidates, 'No visible To Vertices child button')
    print('CONVERSION_TARGET', {'parent': parent, 'candidates': candidates,
          'mode': tuple(bpy.context.tool_settings.mesh_select_mode),
          'selected': [selected(domain) for domain in ('verts','edges','faces')]}, flush=True)
    event('MOUSEMOVE', 'NOTHING', min(candidates), ctrl=True)
    yield from settle()
    pixels('conversion-before-release')
    yield from release(ctrl=True)
    pixels('conversion-after-release')
    print('CONVERSION_RESULT', {'mode': tuple(bpy.context.tool_settings.mesh_select_mode),
          'selected': [selected(domain) for domain in ('verts','edges','faces')],
          'modals': modals()}, flush=True)
    check(tuple(bpy.context.tool_settings.mesh_select_mode) == (True,False,False) and selected('verts') == 4,
          'Ctrl+RMB child did not convert the selected face to its four vertices')
    check(not modals(), 'Conversion left a modal handler')
    print('PASS Ctrl+RMB: visible parent and child, actual selected-face to vertices', flush=True)

    with override():
        bpy.ops.wm.tool_set_by_id(name='builtin.move')
        bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
        bpy.context.scene.transform_orientation_slots[1].use = True
    before = state()
    for _ in range(2):
        yield from begin(ctrl=True, shift=True, point=(region.x+region.width/2, region.y+region.height*.65))
        check(bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == 'builtin.move',
              'Current-tool entry switched tools')
        event('MOUSEMOVE', 'NOTHING', target('W'), ctrl=True, shift=True)
        yield from settle()
        yield from release(ctrl=True, shift=True)
        check(not modals(), 'Current-tool direct entry incorrectly remained armed')
    check(state() == before and bpy.context.scene.transform_orientation_slots[1].type == 'GLOBAL',
          'Current-tool World direction failed or modified mesh selection')
    print('PASS Ctrl+Shift+RMB: current Move World action, no tool switch, repeated direct opening', flush=True)
    print('AXISMELD_CONTEXT_ENTRIES_EVENTS_PASS', flush=True)


steps = suite()
def tick():
    try:
        next(steps)
        return .04
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None
bpy.app.timers.register(tick, first_interval=1)

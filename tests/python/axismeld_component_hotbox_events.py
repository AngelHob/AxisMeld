# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual RMB ownership, component state, cancellation and native fallback."""
import os
import json
import numpy as np
from pathlib import Path
import sys
import traceback
import bpy
root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle():
    for _ in range(6):
        yield


def suite():
    from axismeld import adapter
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    pos = [cx, cy]
    scale = bpy.context.preferences.system.ui_scale
    def event(kind, value='PRESS', delta=None, **kwargs):
        if delta is not None:
            pos[:] = (int(cx + delta[0]*scale), int(cy + delta[1]*scale))
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], **kwargs)
    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)
    def modals():
        return [op.bl_idname for op in win.modal_operators]
    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_image_fixture import (observed_radial_rectangles,
        observed_menu_rectangles, menu_background_mask)
    from axismeld import hotbox_runtime
    for colors in (bpy.context.preferences.themes[0].user_interface.wcol_menu,
                   bpy.context.preferences.themes[0].user_interface.wcol_menu_back,
                   bpy.context.preferences.themes[0].user_interface.wcol_menu_item):
        colors.inner = colors.inner_sel = (.8, .04, .65, 1)
    with override():
        hotbox_runtime.reload_settings(bpy.context, session={'schema_version': 1, 'settings': {
            'transparency': 0, 'appearance': {'theme_background': True, 'brightness': 0}}})
    def observe():
        path = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root)) / 'component-input.png'
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
            ring = observed_radial_rectangles(pixels, scale, ('N','NE','E','SE','S','SW','W'))
            columns = observed_menu_rectangles(menu_background_mask(pixels), 80*scale, 100*scale)
            return ring, columns
        finally:
            bpy.data.images.remove(image)
    captured = False
    def gesture(delta, cancel=False, trigger='RIGHTMOUSE', during=None, companion_row=None):
        nonlocal captured
        event('MOUSEMOVE', 'NOTHING', (0, 0))
        yield from settle()  # Scene setup must reach the GPU before the PRESS pick.
        event(trigger)
        yield from settle()
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'RMB must immediately open one component session: ' + str((bpy.context.mode, [(o.name,o.mode,o.select_get()) for o in bpy.context.scene.objects], modals())))
        if not captured:
            with override():
                bpy.ops.screen.screenshot(filepath=str(Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root)) / 'component-ring.png'))
            captured = True
        ring, columns = observe()
        if during is not None:
            during()
        # PRESS/GPU pick and physical-origin cancellation stay at (cx, cy).
        # Only visible target coordinates follow the actually rendered composition.
        if companion_row is not None:
            with override():
                pending = list(json.loads(hotbox_runtime.snapshot(bpy.context))['menus'])
            while pending:
                node = pending.pop()
                if node['id'] == 'context.component_menu':
                    rows = node['children']; break
                pending.extend(node['children'])
            column = min(columns, key=lambda r: abs((r[0]+r[2])/2-ring['center'][0]))
            check(abs((column[3]-column[1])/scale-570) <= 6,
                  'component input fixture requires its complete 570px single column')
            used = 0
            for item in rows:
                height = 6 if item['kind'] == 'separator' else 24
                if item['id'] == 'context.component_menu.' + companion_row:
                    # Stay away from the physical press cancel disk and Options column.
                    pos[:] = (int(column[0]+55*scale), int(column[3]-(2+used+height/2)*scale))
                    break
                used += height
            else:
                raise AssertionError('Missing companion row ' + companion_row)
        elif delta == (0, 0):
            pos[:] = (cx, cy)
        else:
            pos[:] = (int(ring['center'][0]+delta[0]*scale),
                      min(win.height-2, int(ring['center'][1]+delta[1]*scale)))
        event('MOUSEMOVE', 'NOTHING')
        yield from settle()
        if cancel:
            event('ESC')
            yield from settle()
            event('ESC', 'RELEASE')
        event(trigger, 'RELEASE')
        yield from settle()
        check(not modals(), 'component release left handlers: ' + str(modals()))
    with override():
        check(adapter.available(bpy.context, 'mode.object')[0], 'idempotent Object Mode must be available')
        check(adapter.run(bpy.context, 'mode.object', invoke=False) == {'FINISHED'}, 'Object Mode failed')
        check(adapter.run(bpy.context, 'mode.object', invoke=False) == {'FINISHED'}, 'Object Mode second call failed')
    event('MOUSEMOVE', 'NOTHING', (0, 0))
    yield from settle()
    for delta, mask in [((0,64), (False,True,False)), ((-86,0), (True,False,False)),
                        ((0,-64), (False,False,True)), ((0,64), (False,True,False))]:
        yield from gesture(delta)
        check(bpy.context.mode == 'EDIT_MESH' and tuple(bpy.context.tool_settings.mesh_select_mode) == mask,
              'RMB direction must select the specified component mode')
    yield from gesture((85,32))
    check(bpy.context.mode == 'OBJECT', 'NE must enter Object Mode')
    yield from gesture((85,32))
    check(bpy.context.mode == 'OBJECT', 'NE must remain Object Mode on repeated gesture')
    for delta, cancel in [((0,0),False), ((0,64),True), ((86,0),False), ((-86,-32),False), ((86,-32),False)]:
        yield from gesture(delta,cancel)
        check(bpy.context.mode == 'OBJECT', 'center/Esc/disabled directions must not execute')
    print('PASS RMB component directions, consecutive gestures, Object Mode idempotence, center/Esc/placeholders', flush=True)
    for delta, mask in [((-280,0), (True,False,False)), ((0,260), (False,True,False)),
                        ((0,-64), (False,False,True))]:
        def capture_outer():
            with override():bpy.ops.screen.screenshot(filepath=str(Path(os.environ.get('AXISMELD_TEST_ARTIFACTS',root))/('component-outer-'+str(delta)+'.png')))
        yield from gesture(delta,during=capture_outer)
        check(bpy.context.mode == 'EDIT_MESH' and tuple(bpy.context.tool_settings.mesh_select_mode) == mask,
              'RMB outer stroke must retain its component direction: '+repr((delta,bpy.context.mode,tuple(bpy.context.tool_settings.mesh_select_mode))))
    # Full companion owns these observed rows; fixed old S offsets no longer
    # identify them after the complete composition is bottom-aligned.
    import bmesh
    def occluded_state():
        bm=bmesh.from_edit_mesh(bpy.context.active_object.data)
        return (bpy.context.mode,tuple(bpy.context.tool_settings.mesh_select_mode),
                tuple(tuple(e.select for e in getattr(bm,key)) for key in ('verts','edges','faces')))
    before_occluded=occluded_state()
    yield from gesture((0,-260), companion_row='invert_selection')
    after_occluded=occluded_state()
    print('COMPANION_OCCLUDED_S',repr(before_occluded),repr(after_occluded),flush=True)
    check(after_occluded[:2]==before_occluded[:2] and
          after_occluded[2]==tuple(tuple(not flag for flag in flags) for flags in before_occluded[2]),
          'covered S extension must execute actual Invert Selection instead of Face')
    before_occluded=occluded_state()
    yield from gesture((0,-265), companion_row='separator_selection')
    check(occluded_state()==before_occluded,
          'companion separator must cancel instead of falling through to S')
    yield from gesture((280,32))
    check(bpy.context.mode == 'OBJECT', 'RMB outer NE stroke must enter Object Mode')
    for delta in [(-280,32), (280,0), (-280,-32), (280,-32)]:
        yield from gesture(delta)
        check(bpy.context.mode == 'OBJECT', 'RMB missing/disabled outer direction must not select neighbour')
    print('PASS RMB unobstructed extended directions, S main-row release, companion separator cancellation and missing NW occlusion', flush=True)
    cube = bpy.context.active_object
    # M2b: the factory cube is under the pointer, while another mesh is active.
    with override():
        bpy.ops.mesh.primitive_cube_add(location=(20, 0, 0))
        other = bpy.context.active_object
    def capture_pointer():
        with override():
            bpy.ops.screen.screenshot(filepath=str(Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root)) / 'pointer-before-commit.png'))
    yield from gesture((0,0), during=capture_pointer)
    before = (tuple(o.name for o in bpy.context.selected_objects), other.name)
    from axismeld import hotbox_runtime
    recent_before = hotbox_runtime.recent.items()
    for delta, cancel in [((0,0),False), ((0,64),True), ((86,0),False)]:
        yield from gesture(delta, cancel)
        check((tuple(o.name for o in bpy.context.selected_objects), bpy.context.active_object.name) == before,
              'pointer cancellation must preserve selection and active object')
        check(hotbox_runtime.recent.items() == recent_before, 'pointer cancellation polluted Recent')
    yield from gesture((0,64))
    check(bpy.context.active_object == cube and bpy.context.mode == 'EDIT_MESH',
          'pointer commit must target the unselected mesh under RMB, not the active mesh')
    check(not other.select_get(), 'unselected pointer target must replace previous selection')
    with override():
        adapter.run(bpy.context, 'mode.object', invoke=False)
        other.select_set(True)
        bpy.context.view_layer.objects.active = other
    yield from settle()
    yield from gesture((85,32))
    check(bpy.context.active_object == cube and other.select_get() and cube.select_get(),
          'selected pointer target must activate while preserving native selection set')
    with override():
        other.select_set(False)
        bpy.data.objects.remove(other, do_unlink=True)
    # No active object still permits a pointer target, but ordinary commands stay unavailable.
    with override():
        cube.select_set(False)
        bpy.context.view_layer.objects.active = None
        check(not adapter.available(bpy.context, 'selection.edge_mode')[0], 'global capability weakened')
    yield from gesture((0,64))
    check(bpy.context.mode == 'EDIT_MESH' and bpy.context.active_object == cube,
          'pointer target must work without an active object')
    with override():
        adapter.run(bpy.context, 'mode.object', invoke=False)
    # A captured target becoming unavailable must cancel, never execute on a replacement active mesh.
    with override():
        bpy.ops.mesh.primitive_cube_add(location=(20, 0, 0))
        other = bpy.context.active_object
    def invalidate_target():
        cube.hide_select = True
    recent_before = hotbox_runtime.recent.items()
    yield from gesture((0,64), during=invalidate_target)
    check(bpy.context.mode == 'OBJECT' and bpy.context.active_object == other and not cube.select_get(),
          'invalid target fell back to another mesh or changed selection')
    check(hotbox_runtime.recent.items() == recent_before, 'invalid target polluted Recent')
    with override():
        cube.hide_select = False
        bpy.data.objects.remove(other, do_unlink=True)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
    with override():
        bpy.ops.mesh.primitive_cube_add(location=(20, 0, 0))
        other = bpy.context.active_object
    def delete_target():
        bpy.data.objects.remove(cube, do_unlink=True)
    recent_before = hotbox_runtime.recent.items()
    yield from gesture((0,64), during=delete_target)
    check(bpy.context.mode == 'OBJECT' and bpy.context.active_object == other and other.select_get(),
          'deleted target fell back to the active mesh')
    check(hotbox_runtime.recent.items() == recent_before, 'deleted target polluted Recent')
    with override():
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        bpy.data.objects.remove(other, do_unlink=True)
    # Edit-mode pointer remains bound to the current native editing set.
    with override():
        bpy.ops.mesh.primitive_cube_add(location=(20, 0, 0))
        other = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
    yield from gesture((0,64))
    check(bpy.context.mode == 'EDIT_MESH' and bpy.context.active_object == other and cube.mode == 'OBJECT',
          'Edit Mesh pointer crossed to another object')
    with override():
        adapter.run(bpy.context, 'mode.object', invoke=False)
        bpy.data.objects.remove(other, do_unlink=True)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
    native_draws = []
    def native_menu_probe(self, context):
        native_draws.append(context.mode)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(native_menu_probe)
    def native_rmb():
        before = len(native_draws)
        event('MOUSEMOVE', 'NOTHING', (0,0))
        event('RIGHTMOUSE')
        yield from settle()
        event('RIGHTMOUSE', 'RELEASE')
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'unsupported context armed component menu')
        check(len(native_draws) > before, 'native object context menu must actually draw on RMB')
        event('ESC')
        event('ESC', 'RELEASE')
        yield from settle()
    # Real foreground non-mesh geometry must pass to Blender, not edit the mesh behind it.
    from mathutils import Quaternion, Vector
    rv3d = region.data
    saved_view = (rv3d.view_rotation.copy(), rv3d.view_location.copy(), rv3d.view_distance, rv3d.view_perspective)
    rv3d.view_rotation = Quaternion((1, 0, 0, 0))
    rv3d.view_location = Vector((0, 0, 0))
    rv3d.view_distance = 10
    rv3d.view_perspective = 'ORTHO'
    with override():
        bpy.ops.curve.primitive_bezier_circle_add(radius=3, location=(0, 0, 3))
        foreground = bpy.context.active_object
        foreground.data.dimensions = '2D'
        foreground.data.fill_mode = 'BOTH'
        foreground.select_set(False)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
    yield from settle()
    yield from native_rmb()
    check(bpy.context.mode == 'OBJECT' and bpy.context.active_object == cube,
          'foreground non-mesh changed mesh context')
    with override():
        bpy.data.objects.remove(foreground, do_unlink=True)
    rv3d.view_rotation, rv3d.view_location, rv3d.view_distance, rv3d.view_perspective = saved_view
    yield from settle()
    with override():
        cube.select_set(False)
        cube.hide_set(True)
        check(not adapter.available(bpy.context, 'context.component_hotbox')[0], 'unselected mesh available')
    yield from native_rmb()
    with override():
        bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
        bpy.context.active_object.select_set(True)
        check(not adapter.available(bpy.context, 'context.component_hotbox')[0], 'non-mesh available')
    yield from native_rmb()
    with override():
        bpy.context.active_object.select_set(False)
        cube.hide_set(False)
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
    # Real keymap edits preserve native RMB, and the new trigger owns its own release.
    def binding():
        return next(kmi for km in bpy.context.window_manager.keyconfigs.user.keymaps
                    if km.name == 'Object Mode' for kmi in km.keymap_items
                    if kmi.idname == 'axismeld.command' and kmi.properties.command == 'context.component_hotbox')
    binding().map_type = 'KEYBOARD'
    binding().type = 'F13'
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    yield from native_rmb()
    with override():
        bpy.ops.mesh.primitive_cube_add(location=(20, 0, 0))
        keyboard_target = bpy.context.active_object
    yield from gesture((0,64), trigger='F13')
    check(bpy.context.mode == 'EDIT_MESH' and bpy.context.active_object == keyboard_target,
          'remapped keyboard trigger must keep the active target rather than pick the pointer cube')
    with override():
        adapter.run(bpy.context, 'mode.object', invoke=False)
    with override():
        bpy.data.objects.remove(keyboard_target, do_unlink=True)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
    binding().active = False
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    event('F13')
    yield from settle()
    check(not modals(), 'disabled remapped binding opened component menu')
    event('F13', 'RELEASE')
    yield from native_rmb()
    binding().active = True
    binding().map_type = 'MOUSE'
    binding().type = 'RIGHTMOUSE'
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    bpy.types.VIEW3D_MT_object_context_menu.remove(native_menu_probe)
    event('RIGHTMOUSE')
    yield from settle()
    event('RIGHTMOUSE', 'RELEASE', ctrl=True)
    yield from settle()
    check(not modals(), 'modified owned release left a stale component guard')
    # Focus loss clears both owners immediately, even if the old release never arrives.
    event('RIGHTMOUSE')
    yield from settle()
    event('WINDOW_DEACTIVATE', 'NOTHING')
    yield from settle()
    check(not modals(), 'focus loss left an owner waiting for an impossible release')
    yield from gesture((0,0))
    for modifier in ('alt', 'ctrl', 'shift', 'oskey'):
        before_modified = (bpy.context.mode, bpy.context.active_object.name,
                           tuple(sorted(o.name for o in bpy.context.selected_objects)))
        event('RIGHTMOUSE', **{modifier:True})
        yield from settle()
        if modifier == 'shift':
            # M2d owns Shift+RMB on selected Object Mesh independently of the
            # unmodified component entry. Other modifiers still fall through.
            check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
                  'Shift+RMB must open one Object modeling session')
        else:
            check('VIEW3D_OT_axismeld_hotbox' not in modals(),
                  modifier + '+RMB must retain native handling')
        event('RIGHTMOUSE', 'RELEASE', **{modifier:True})
        event('ESC')
        event('ESC', 'RELEASE')
        yield from settle()
        if modifier == 'shift':
            check(not modals() and before_modified == (
                bpy.context.mode, bpy.context.active_object.name,
                tuple(sorted(o.name for o in bpy.context.selected_objects))),
                'Object modeling center cancellation changed context or left ownership')
    with override():
        bpy.ops.object.select_all(action='DESELECT')
    event('LEFTMOUSE', delta=(0,0))
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    check(cube.select_get(), 'normal LMB selection after component sessions must work')
    check(not modals(), 'normal selection left handlers')
    print('PASS unsupported contexts, modifiers and normal selection after release', flush=True)
    print('AXISMELD_COMPONENT_HOTBOX_EVENTS_PASS', flush=True)

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

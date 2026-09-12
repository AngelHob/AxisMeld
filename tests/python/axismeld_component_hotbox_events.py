# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual RMB ownership, component state, cancellation and native fallback."""
import os
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
    captured = False
    def gesture(delta, cancel=False, trigger='RIGHTMOUSE'):
        nonlocal captured
        event('MOUSEMOVE', 'NOTHING', (0, 0))
        event(trigger)
        yield from settle()
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1, 'RMB must immediately open one component session')
        if not captured:
            with override():
                bpy.ops.screen.screenshot(filepath=str(Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root)) / 'component-ring.png'))
            captured = True
        event('MOUSEMOVE', 'NOTHING', delta)
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
    cube = bpy.context.active_object
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
    with override():
        cube.select_set(False)
        check(not adapter.available(bpy.context, 'context.component_hotbox')[0], 'unselected mesh available')
    yield from native_rmb()
    with override():
        bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
        bpy.context.active_object.select_set(True)
        check(not adapter.available(bpy.context, 'context.component_hotbox')[0], 'non-mesh available')
    yield from native_rmb()
    with override():
        bpy.context.active_object.select_set(False)
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
    yield from gesture((0,64), trigger='F13')
    check(bpy.context.mode == 'EDIT_MESH', 'remapped keyboard trigger must execute once')
    with override():
        adapter.run(bpy.context, 'mode.object', invoke=False)
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
        event('RIGHTMOUSE', **{modifier:True})
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' not in modals(), 'modified RMB must retain native handling')
        event('RIGHTMOUSE', 'RELEASE')
        event('ESC')
        event('ESC', 'RELEASE')
        yield from settle()
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

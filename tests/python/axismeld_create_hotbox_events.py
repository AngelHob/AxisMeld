# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual Shift+RMB creation, geometry, undo and scoped native fallback."""
import os
import json
from pathlib import Path
import sys
import traceback

import bpy
import blf
from mathutils import Quaternion, Vector

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.edit.use_global_undo = True


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
    bpy.utils.keyconfig_set(str(preset))
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    pos = [cx, cy]
    scale = bpy.context.preferences.system.ui_scale

    def event(kind, value='PRESS', delta=None, **kwargs):
        if delta is not None:
            pos[:] = (int(cx + delta[0] * scale), int(cy + delta[1] * scale))
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], **kwargs)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def screenshot(name):
        with override():
            bpy.ops.screen.screenshot(filepath=str(
                Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root)) / name))

    # This assertion intentionally precedes imports of newly installed modules so
    # an old installation fails on the missing real input behavior, not an import.
    with override():
        for obj in list(bpy.context.scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    event('MOUSEMOVE', 'NOTHING', (0, 0))
    yield from settle()
    event('LEFT_SHIFT', shift=True)
    event('RIGHTMOUSE', shift=True)
    yield from settle()
    check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
          'empty Object scene Shift+RMB must immediately open one create session: ' + str(modals()))
    event('RIGHTMOUSE', 'RELEASE', shift=True)
    event('LEFT_SHIFT', 'RELEASE')
    yield from settle()
    check(not modals(), 'initial center cancellation left handlers: ' + str(modals()))
    check(not bpy.context.scene.objects, 'initial center cancellation created an object')

    from axismeld import hotbox_runtime

    def scene_state():
        return (bpy.context.mode,
                tuple(sorted((o.name, o.type, o.select_get()) for o in bpy.context.scene.objects)),
                tuple(bpy.context.scene.cursor.location))

    # Public direction contract; these coordinates are comfortably inside the
    # minimum-size buttons. Outcomes are asserted from actual scene geometry.
    targets = {'N': (0, 64), 'NE': (46, 32), 'E': (62, 0), 'SE': (46, -32),
               'S': (0, -64), 'SW': (-46, -32), 'W': (-62, 0), 'NW': (-46, 32)}
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    reference_expansion = (blf.dimensions(0, 'AxisMeld')[0]/scale + 20 + 40 - 24)/2
    targets = {direction: (x + (reference_expansion if x > 0 else -reference_expansion if x < 0 else 0), y)
               for direction, (x, y) in targets.items()}
    outer = {'N': (0, 260), 'NE': (280, 32), 'E': (280, 0), 'SE': (280, -32),
             'S': (0, -260), 'SW': (-280, -32), 'W': (-280, 0), 'NW': (-280, 32)}

    def begin(trigger='RIGHTMOUSE', required_shift=True, required_ctrl=False):
        event('MOUSEMOVE', 'NOTHING', (0, 0))
        yield from settle()
        if required_ctrl:
            event('LEFT_CTRL', ctrl=True)
        if required_shift:
            event('LEFT_SHIFT', shift=True, ctrl=required_ctrl)
        event(trigger, shift=required_shift, ctrl=required_ctrl)
        yield from settle()
        check(modals().count('VIEW3D_OT_axismeld_hotbox') == 1,
              'create gesture failed to open: ' + str(modals()))

    def finish(trigger='RIGHTMOUSE', required_shift=True, required_ctrl=False):
        event(trigger, 'RELEASE', shift=required_shift, ctrl=required_ctrl)
        if required_shift:
            event('LEFT_SHIFT', 'RELEASE', ctrl=required_ctrl)
        if required_ctrl:
            event('LEFT_CTRL', 'RELEASE')
        yield from settle()
        check(not modals(), 'create release left handlers: ' + str(modals()))

    def stroke(direction, trigger='RIGHTMOUSE', required_shift=True, extend=True, required_ctrl=False):
        yield from begin(trigger, required_shift, required_ctrl)
        event('MOUSEMOVE', 'NOTHING', targets[direction], shift=required_shift, ctrl=required_ctrl)
        yield from settle()
        if extend:
            start, end = targets[direction], outer[direction]
            for t in (.25, .5, .75, 1):
                event('MOUSEMOVE', 'NOTHING', tuple(a + (b-a)*t for a, b in zip(start, end)),
                      shift=required_shift, ctrl=required_ctrl)
                yield from settle(1)
        yield from finish(trigger, required_shift, required_ctrl)

    def geometry(kind, obj):
        check(obj.type == 'MESH', kind + ' did not create a Mesh object')
        mesh = obj.data
        counts = (len(mesh.vertices), len(mesh.edges), len(mesh.polygons))
        print('CREATE_GEOMETRY', kind, counts, flush=True)
        check(all(counts), kind + ' produced empty geometry')
        sizes = [len(p.vertices) for p in mesh.polygons]
        zs = [v.co.z for v in mesh.vertices]
        if kind == 'cube':
            check(counts == (8, 12, 6) and all(s == 4 for s in sizes), 'Cube topology wrong')
        elif kind == 'plane':
            check(counts == (4, 4, 1) and sizes == [4], 'Plane topology wrong')
            check(max(zs)-min(zs) < 1e-6, 'Plane is not planar')
        elif kind == 'disc':
            check(counts[0] >= 16 and sizes == [counts[0]], 'Disc must be one filled NGON')
            check(max(zs)-min(zs) < 1e-6, 'Disc is not planar')
        elif kind == 'sphere':
            check(counts[2] > 100 and 3 in sizes and 4 in sizes, 'Sphere topology wrong')
            check(max(zs)-min(zs) > 1.9, 'Sphere has no height')
        elif kind == 'torus':
            check(counts[2] > 100 and all(s == 4 for s in sizes), 'Torus topology wrong')
            check(max(zs)-min(zs) > .1, 'Torus has no tube thickness')
        elif kind == 'cone':
            check(sum(s > 4 for s in sizes) == 1 and 3 in sizes, 'Cone must have one cap and triangular sides')
        elif kind == 'cylinder':
            check(sum(s > 4 for s in sizes) == 2 and 4 in sizes, 'Cylinder must have two caps and quad sides')

    cursor = Vector((2.25, -3.5, 1.75))
    bpy.context.preferences.edit.use_enter_edit_mode = False
    for direction, kind in [('NE', 'disc'), ('E', 'sphere'), ('SE', 'torus'), ('S', 'cube'),
                            ('SW', 'cone'), ('W', 'cylinder'), ('NW', 'plane')]:
        with override():
            bpy.context.scene.cursor.location = cursor
            bpy.ops.ed.undo_push(message='Before create ' + kind)
        before = scene_state()
        yield from stroke(direction)
        objects = list(bpy.context.scene.objects)
        check(len(objects) == 1, kind + ' must create exactly one object')
        obj = objects[0]
        check(bpy.context.mode == 'OBJECT' and obj == bpy.context.active_object and obj.select_get(),
              kind + ' must remain Object with the new mesh active and selected')
        check((obj.location - cursor).length < 1e-5, kind + ' must use the 3D Cursor position')
        check((bpy.context.scene.cursor.location - cursor).length < 1e-5, 'create moved the 3D Cursor')
        geometry(kind, obj)
        check(hotbox_runtime.recent.items()[0] == 'mesh.create_' + kind,
              kind + ' successful creation did not enter Recent')
        with override():
            check(bpy.ops.ed.undo() == {'FINISHED'}, kind + ' undo was not available')
        yield from settle()
        check(scene_state() == before, kind + ' one undo must restore the pre-action scene')
    print('PASS seven directions, outward strokes, actual primitive geometry, cursor and one undo', flush=True)

    # Torus is the documented native exception: its Python operator has no
    # enter_editmode RNA property. Preserve the user's preference and one undo.
    bpy.context.preferences.edit.use_enter_edit_mode = True
    for direction, kind, expected_mode in [('S', 'cube', 'OBJECT'), ('SE', 'torus', 'EDIT_MESH')]:
        with override():
            bpy.context.scene.cursor.location = cursor
            bpy.ops.ed.undo_push(message='Before creation preference ' + kind)
        yield from stroke(direction)
        check(len(bpy.context.scene.objects) == 1 and bpy.context.mode == expected_mode,
              kind + ' did not follow its documented creation-mode policy')
        check(bpy.context.preferences.edit.use_enter_edit_mode,
              kind + ' changed the user creation preference')
        with override():
            check(bpy.ops.ed.undo() == {'FINISHED'}, kind + ' preference-case undo unavailable')
        yield from settle()
        check(not bpy.context.scene.objects and bpy.context.mode == 'OBJECT',
              kind + ' preference-case one undo did not restore the empty Object scene')
    bpy.context.preferences.edit.use_enter_edit_mode = False
    print('PASS explicit Cube Object mode and native Torus Edit preference with one undo', flush=True)

    # Every cancellation happens after a real candidate is visible where possible.
    for cancellation in ('center', 'disabled', 'shift-first', 'escape', 'focus', 'extra-modifier'):
        before = scene_state()
        recent = hotbox_runtime.recent.items()
        yield from begin()
        if cancellation == 'center':
            event('MOUSEMOVE', 'NOTHING', targets['S'], shift=True)
            yield from settle()
            event('MOUSEMOVE', 'NOTHING', (0, 0), shift=True)
        elif cancellation == 'disabled':
            event('MOUSEMOVE', 'NOTHING', outer['N'], shift=True)
            screenshot('create-disabled-n.png')
        else:
            event('MOUSEMOVE', 'NOTHING', targets['S'], shift=True)
        yield from settle()
        if cancellation == 'shift-first':
            event('LEFT_SHIFT', 'RELEASE')
            yield from settle()
            event('RIGHTMOUSE', 'RELEASE')
        elif cancellation == 'escape':
            event('ESC', shift=True)
            event('ESC', 'RELEASE', shift=True)
            yield from finish()
        elif cancellation == 'focus':
            event('WINDOW_DEACTIVATE', 'NOTHING')
            yield from settle()
            check(not modals(), 'focus loss retained an owner waiting for a lost release')
            event('RIGHTMOUSE', 'RELEASE')
            event('LEFT_SHIFT', 'RELEASE')
        elif cancellation == 'extra-modifier':
            event('LEFT_CTRL', ctrl=True, shift=True)
            event('RIGHTMOUSE', 'RELEASE', ctrl=True, shift=True)
            event('LEFT_CTRL', 'RELEASE', shift=True)
            event('LEFT_SHIFT', 'RELEASE')
        else:
            yield from finish()
        yield from settle()
        check(not modals(), cancellation + ' left stale handlers: ' + str(modals()))
        check(scene_state() == before, cancellation + ' changed scene, selection or cursor')
        check(hotbox_runtime.recent.items() == recent, cancellation + ' changed Recent')
        # Missing modifiers on the trigger release must not leave a future guard.
        yield from begin()
        yield from finish()
    print('PASS center, disabled, Shift-first, Esc, focus and modifier cancellation with reopen', flush=True)

    bpy.context.preferences.edit.use_enter_edit_mode = False
    rv3d = region.data
    rv3d.view_rotation = Quaternion((1, 0, 0, 0))
    rv3d.view_location = Vector((0, 0, 0))
    rv3d.view_distance = 10
    rv3d.view_perspective = 'ORTHO'

    def native_fallback(label, delta=(0, 0)):
        before_objects = tuple(sorted((o.name, o.select_get(), o.type) for o in bpy.context.scene.objects))
        before_mode = bpy.context.mode
        bpy.context.scene.cursor.location = (40, 40, 40)
        event('MOUSEMOVE', 'NOTHING', delta)
        yield from settle()
        event('LEFT_SHIFT', shift=True)
        event('RIGHTMOUSE', shift=True)
        yield from settle()
        check('VIEW3D_OT_axismeld_hotbox' not in modals(), label + ' incorrectly opened creation')
        event('RIGHTMOUSE', 'RELEASE', shift=True)
        event('LEFT_SHIFT', 'RELEASE')
        yield from settle()
        check((bpy.context.scene.cursor.location - Vector((40, 40, 40))).length > 1,
              label + ' did not execute the native 3D Cursor fallback')
        check(tuple(sorted((o.name, o.select_get(), o.type) for o in bpy.context.scene.objects)) == before_objects
              and bpy.context.mode == before_mode, label + ' changed geometry or selection context')
        check(not modals(), label + ' left native/AxisMeld modal handlers: ' + str(modals()))

    # Test CREATE's own fallback with the independent Object MODEL entry disabled.
    # Default selected/preselected Object routing is covered by object-modeling.
    from axismeld import runtime
    with override():
        config = runtime.load(session={'schema_version': 1, 'bindings': {
            'context.modeling_hotbox': None}})
        bpy.context.window_manager.keyconfigs.active = config
        bpy.context.window_manager.keyconfigs.update()
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        existing_name = bpy.context.active_object.name
    yield from native_fallback('selected Object', (200, 100))
    with override():
        bpy.context.active_object.select_set(False)
        bpy.context.view_layer.objects.active = None
    yield from native_fallback('unselected mesh under pointer')
    with override():
        obj = bpy.data.objects[existing_name]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        # Selected single-domain Edit now belongs to the independent MODEL hotbox.
        # Keep proving native Cursor fallback here for an empty Edit selection.
        bpy.ops.mesh.select_all(action='DESELECT')
    yield from native_fallback('Mesh Edit empty selection')
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    print('PASS CREATE independent selected Object, empty Edit and pointer-target fallback', flush=True)
    with override():
        config = runtime.load(session={'schema_version': 1, 'bindings': {}})
        bpy.context.window_manager.keyconfigs.active = config
        bpy.context.window_manager.keyconfigs.update()
    yield from settle()

    # Real Space -> Create -> native list -> shared radial. Retain an existing
    # selected object to prove this explicit entry has a different scope to RMB.
    sys.path.insert(0, str(Path(__file__).parent))
    from axismeld_hotbox_geometry_fixture import native_page
    blf.size(0, bpy.context.preferences.ui_styles[0].widget.points * scale)
    # Every Space title and the native Polygon Primitives entry now has one
    # semantic icon. The central AxisMeld reference above already counted its icon.
    measure = lambda label: blf.dimensions(0, label)[0] / scale + 20
    labels = ['File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
    widths = [measure(label) + 40 for label in labels]
    left = cx - (sum(widths) + 60)*scale/2
    create_rect = (left + (sum(widths[:2]) + 20)*scale, cy + 77*scale, widths[2]*scale, 38*scale)
    bounds = (region.x, region.y, region.width, region.height)

    def absolute_middle(rect):
        pos[:] = (int(rect[0] + rect[2]/2), int(rect[1] + rect[3]/2))

    bpy.context.scene.cursor.location = cursor
    with override():
        bpy.ops.ed.undo_push(message='Before Space create with selection')
    before_space = scene_state()
    event('MOUSEMOVE', 'NOTHING', (0, 0))
    yield from settle()
    event('SPACE')
    yield from settle()
    screenshot('create-space-open.png')
    check('VIEW3D_OT_axismeld_hotbox' in modals(), 'Space press did not open its hotbox: ' + str(modals()))
    absolute_middle(create_rect)
    event('MOUSEMOVE', 'NOTHING')
    event('LEFTMOUSE')
    yield from settle()
    primitive_rect = native_page(create_rect, ['Polygon Primitives'], measure, bounds, scale,
                                 submenu_indices=(0,))['items'][0]
    absolute_middle(primitive_rect)
    event('MOUSEMOVE', 'NOTHING')
    yield from settle()
    screenshot('create-space-existing-selection.png')
    # The tool ring is anchored at this entry; straight down remains Cube even
    # after clamping/outer extension, and release must create once before Space up.
    pos[1] -= int(160*scale)
    event('MOUSEMOVE', 'NOTHING')
    yield from settle()
    event('LEFTMOUSE', 'RELEASE')
    yield from settle()
    event('SPACE', 'RELEASE')
    yield from settle()
    check(len(bpy.context.scene.objects) == 2, 'Space Create with selected mesh did not create exactly one object')
    check(bpy.context.active_object.name != existing_name, 'Space Create did not activate new object')
    geometry('cube', bpy.context.active_object)
    check((bpy.context.active_object.location-cursor).length < 1e-5, 'Space Create ignored cursor location')
    check(not modals(), 'Space Create left release ownership: ' + str(modals()))
    with override():
        check(bpy.ops.ed.undo() == {'FINISHED'}, 'Space Create undo unavailable')
    yield from settle()
    check(scene_state() == before_space, 'Space Create one undo failed to restore the original selection')
    print('PASS Space Create native-list path with existing selection and one undo restoration', flush=True)

    def recent_creation(snapshot):
        pending = list(snapshot['menus'])
        while pending:
            node = pending.pop()
            pending.extend(node['children'])
            if node['id'].startswith('center.recent.') and node['command'] == 'mesh.create_cube':
                return node
        raise AssertionError('Successful Cube is missing from the live Recent menu')

    with override():
        item = recent_creation(json.loads(hotbox_runtime.snapshot(bpy.context)))
        check(item['enabled'], 'Object Recent creation must be enabled')
        bpy.ops.ed.undo_push(message='Before Recent create replay')
        check(hotbox_runtime.dispatch(bpy.context, item['command']) == {'FINISHED'}, 'Recent replay failed')
    yield from settle()
    check(len(bpy.context.scene.objects) == 2, 'Recent replay did not create a new mesh')
    geometry('cube', bpy.context.active_object)
    with override():
        bpy.ops.ed.undo()
    yield from settle()
    check(scene_state() == before_space, 'Recent replay undo did not restore prior state')
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        item = recent_creation(json.loads(hotbox_runtime.snapshot(bpy.context)))
        check(not item['enabled'], 'Recent creation must be disabled in Edit Mesh')
        before_edit = scene_state()
        recent = hotbox_runtime.recent.items()
        check(hotbox_runtime.dispatch(bpy.context, item['command']) == {'CANCELLED'},
              'Edit Mesh creation replay must be rejected at dispatch')
        check(scene_state() == before_edit and hotbox_runtime.recent.items() == recent,
              'Rejected Edit Recent command changed state')
        bpy.ops.object.mode_set(mode='OBJECT')
    print('PASS Recent success identity, native replay, undo and Edit Mesh rejection', flush=True)

    with override():
        for obj in list(bpy.context.scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

    def binding():
        return next(kmi for km in bpy.context.window_manager.keyconfigs.user.keymaps
                    if km.name == 'Object Mode' for kmi in km.keymap_items
                    if kmi.idname == 'axismeld.command' and kmi.properties.command == 'context.create_hotbox')

    binding().map_type = 'KEYBOARD'
    binding().type = 'F13'
    binding().shift = False
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    yield from native_fallback('original Shift+RMB after remap')
    bpy.context.scene.cursor.location = cursor
    yield from stroke('S', trigger='F13', required_shift=False)
    check(len(bpy.context.scene.objects) == 1, 'remapped keyboard creation did not create one object')
    geometry('cube', bpy.context.active_object)
    with override():
        bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
    binding().active = False
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    event('F13')
    event('F13', 'RELEASE')
    yield from settle()
    check(not modals() and not bpy.context.scene.objects, 'disabled creation keymap still acted')
    binding().active = True
    binding().type = 'F14'
    binding().ctrl = True
    binding().shift = True
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    yield from stroke('S', trigger='F14', required_shift=True, required_ctrl=True)
    check(len(bpy.context.scene.objects) == 1, 'Ctrl+Shift remapped keyboard creation failed')
    geometry('cube', bpy.context.active_object)
    with override():
        bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
    yield from begin('F14', True, True)
    event('MOUSEMOVE', 'NOTHING', targets['S'], shift=True, ctrl=True)
    event('LEFT_CTRL', 'RELEASE', shift=True)
    yield from settle()
    event('F14', 'RELEASE', shift=True)
    event('LEFT_SHIFT', 'RELEASE')
    yield from settle()
    check(not modals() and not bpy.context.scene.objects,
          'required Ctrl released before remapped owner must cancel without residue')
    binding().map_type = 'MOUSE'
    binding().type = 'RIGHTMOUSE'
    binding().ctrl = False
    binding().shift = True
    bpy.context.window_manager.keyconfigs.update()
    yield from settle()
    print('PASS native user remap, Ctrl+Shift ownership, original fallback and disable', flush=True)

    with override():
        check(bpy.ops.view3d.axismeld_view('EXEC_DEFAULT', action='TOGGLE_QUAD') == {'FINISHED'},
              'quad setup failed')
    yield from settle(10)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    cx, cy = region.x + region.width//2, region.y + region.height//2
    bpy.context.scene.cursor.location = cursor
    yield from stroke('S', extend=False)
    check(len(bpy.context.scene.objects) == 1, 'quad viewport creation failed')
    geometry('cube', bpy.context.active_object)
    check(not modals(), 'quad creation left ownership')
    screenshot('create-quad-cube.png')
    print('PASS quad viewport representative creation', flush=True)
    print('AXISMELD_CREATE_HOTBOX_EVENTS_PASS', flush=True)


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

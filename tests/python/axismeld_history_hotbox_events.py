# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Actual A/LMB History gestures, deferred scene changes and one-step Undo.

Targets come from rendered button backgrounds, not the native menu model. Run
only through the disposable GUI runner with event simulation enabled.
"""
import json
import os
from pathlib import Path
import sys
import traceback

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_radial_rectangles

root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(root)
artifacts = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', root))
artifacts.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.smooth_view = 0
records = []


def check(value, message):
    if not value:
        raise AssertionError(message)


def settle(count=5):
    for _ in range(count):
        yield


def evidence(case, phase, state, **extra):
    records.append({'case': case, 'phase': phase, 'state': state, **extra})
    (artifacts / 'history-hotbox-events.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py'
                  for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    center = (region.x + region.width // 2, region.y + region.height // 2)
    pos = list(center)
    theme = bpy.context.preferences.themes[0].user_interface
    for colors in (theme.wcol_menu, theme.wcol_menu_back, theme.wcol_menu_item):
        colors.inner = (.8, .04, .65, 1)
        colors.inner_sel = (.8, .04, .65, 1)

    def override():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def event(kind, value='PRESS', point=None, **kwargs):
        if point is not None:
            pos[:] = map(int, point)
        win.event_simulate(type=kind, value=value, x=pos[0], y=pos[1], **kwargs)

    def modals():
        return [op.bl_idname for op in win.modal_operators]

    def vector(values):
        return tuple(round(float(v), 6) for v in values)

    def state(name='History GUI Fixture'):
        obj = bpy.data.objects[name]
        return {
            'objects': tuple(sorted(o.name for o in bpy.context.scene.objects)),
            'selected': tuple(sorted(o.name for o in bpy.context.selected_objects)),
            'active': bpy.context.view_layer.objects.active.name,
            'location': vector(obj.location),
            'rotation': vector(obj.rotation_euler),
            'scale': vector(obj.scale),
            'object_uid': obj.session_uid,
            'data_uid': obj.data.session_uid,
            'shape_keys': tuple(k.name for k in obj.data.shape_keys.key_blocks)
                          if obj.data.shape_keys else (),
            'vertices': tuple(vector(v.co) for v in obj.data.vertices),
            'faces': tuple(tuple(p.vertices) for p in obj.data.polygons),
            'modifiers': tuple((m.name, m.type,
                                m.levels if m.type == 'SUBSURF' else None,
                                round(m.angle, 6) if m.type == 'SIMPLE_DEFORM' else None)
                               for m in obj.modifiers),
        }

    def view():
        rv3d = area.spaces.active.region_3d
        return (round(rv3d.view_distance, 6), vector(rv3d.view_location),
                vector(rv3d.view_rotation))

    def fixture(kind='reset'):
        check(not modals(), 'fixture started with live handlers: ' + str(modals()))
        with override():
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            bpy.ops.mesh.primitive_cube_add(location=(3, 2, 1))
            obj = bpy.context.active_object
            obj.name = 'History GUI Fixture'
            obj.rotation_euler = (.1, .2, .3)
            obj.scale = (2, 1.5, .5)
            if kind == 'history':
                obj.modifiers.new('Bake Triangles', 'TRIANGULATE')
            elif kind == 'non_deformer':
                obj.modifiers.new('Bake Subdivision', 'SUBSURF').levels = 1
                obj.modifiers.new('Keep Deformation', 'SIMPLE_DEFORM').angle = .4
            bpy.context.view_layer.update()
            bpy.ops.ed.undo_push(message='History GUI baseline ' + kind)
            area.spaces.active.region_3d.view_distance = 73
            area.spaces.active.region_3d.view_location = (0, 0, 0)
            area.tag_redraw()

    def observed(case):
        path = artifacts / ('history-' + case + '.png')
        with override():
            bpy.ops.screen.screenshot(filepath=str(path))
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(image)
        ring = observed_radial_rectangles(pixels, bpy.context.preferences.system.ui_scale,
                                         {'N', 'NW', 'NE', 'W', 'E', 'SW', 'SE', 'S'})
        evidence(case, 'observed_eight_directions', state(), rectangles=ring['rects'],
                 screenshot=str(path))
        return ring

    def target(ring, direction):
        x0, y0, x1, y1 = ring['rects'][direction]
        # Body center-left avoids the independent right-aligned Options cell.
        return (x0 + (x1 - x0) * .35, (y0 + y1) / 2)

    def arm():
        event('MOUSEMOVE', 'NOTHING', center)
        event('A')
        yield from settle()
        check(modals() == ['VIEW3D_OT_axismeld_hotbox'],
              'A did not arm exactly one History session: ' + str(modals()))

    def post(case, point=center):
        event('MOUSEMOVE', 'NOTHING', point)
        event('LEFTMOUSE')
        yield from settle()
        return observed(case)

    def choose(ring, direction):
        event('MOUSEMOVE', 'NOTHING', target(ring, direction))
        yield from settle()
        event('LEFTMOUSE', 'RELEASE')
        yield from settle()
        check(modals() == ['VIEW3D_OT_axismeld_hotbox'],
              'LMB release must leave one armed History session: ' + str(modals()))

    def release():
        event('A', 'RELEASE')
        yield from settle(8)
        check(not modals(), 'A release left handlers: ' + str(modals()))

    fixture()
    yield from settle()
    # A is a release command. Long unposted holds also frame; no QWER tap timeout.
    for case, delay in (('unposted_short', 1), ('unposted_long', 30)):
        area.spaces.active.region_3d.view_distance = 73
        yield from settle()
        before, before_view = state(), view()
        yield from arm()
        yield from settle(delay)
        check(state() == before and view() == before_view, 'A press executed Frame All early')
        evidence(case, 'before_A_release', state(), view=view())
        yield from release()
        check(state() == before and view() != before_view, 'Unposted A release did not Frame All')
        evidence(case, 'after_A_release', state(), view=view())
        print('PASS History ' + case + ': Frame All only on A release', flush=True)

    for case, direction in (('posted_center_cancel', None), ('posted_disabled_cancel', 'W')):
        before, before_view = state(), view()
        yield from arm()
        ring = yield from post(case)
        if direction:
            yield from choose(ring, direction)
        else:
            event('LEFTMOUSE', 'RELEASE', ring['center'])
            yield from settle()
        yield from release()
        check(state() == before and view() == before_view,
              case + ': posted cancellation changed scene or framed view')
        evidence(case, 'after_A_release', state(), view=view())
        print('PASS History ' + case, flush=True)

    # All four existing actions must wait for A release, then own exactly one Undo.
    for kind, direction in (('reset', 'SW'), ('freeze', 'SE'),
                            ('history', 'NW'), ('non_deformer', 'NE')):
        fixture(kind)
        yield from settle()
        before, before_view = state(), view()
        evidence(kind, 'before_gesture', before, view=before_view)
        yield from arm()
        ring = yield from post(kind)
        yield from choose(ring, direction)
        evidence(kind, 'after_LMB_release', state(), view=view())
        check(state() == before and view() == before_view,
              kind + ': LMB release changed the scene before A release')
        yield from release()
        after = state()
        evidence(kind, 'after_A_release', after, view=view())
        check(view() == before_view and after != before, kind + ': deferred action did not execute')
        if kind in {'reset', 'freeze'}:
            check(after['location'] == (0, 0, 0) and after['rotation'] == (0, 0, 0)
                  and after['scale'] == (1, 1, 1), kind + ': local transforms did not clear')
            check((after['vertices'] == before['vertices']) == (kind == 'reset'),
                  kind + ': wrong mesh-data semantics')
        elif kind == 'history':
            check(len(after['faces']) == 12 and not after['modifiers'],
                  'Delete History did not bake the actual Triangulate stack')
        else:
            check(len(after['faces']) > 6 and
                  tuple(m[1] for m in after['modifiers']) == ('SIMPLE_DEFORM',),
                  'Delete Non-Deformer History lost deformation or did not bake topology')
        event('Z')
        event('Z', 'RELEASE')
        yield from settle(10)
        evidence(kind, 'after_one_Undo', state(), view=view())
        # Undo can reconstruct IDs with new session UIDs; geometry, transforms,
        # selection and stack must still restore in exactly one step.
        comparable = lambda s: {k: v for k, v in s.items() if k not in {'object_uid', 'data_uid'}}
        check(comparable(state()) == comparable(before),
              kind + ': one native Undo did not restore the complete fixture')
        print('PASS History ' + kind + ': LMB deferred, A committed, one Undo restored', flush=True)

    fixture()
    yield from settle()
    before, before_view = state(), view()
    yield from arm()
    ring = yield from post('repeat_first')
    yield from choose(ring, 'SW')
    check(state() == before, 'First repeated LMB prematurely committed Reset')
    shifted = (center[0] + 30, center[1] + 25)
    ring = yield from post('repeat_second_cancel', shifted)
    event('LEFTMOUSE', 'RELEASE', ring['center'])
    yield from settle()
    yield from release()
    check(state() == before and view() == before_view,
          'Second LMB post did not clear first selection or incorrectly framed the view')
    evidence('repeat_LMB_cancel', 'after_A_release', state(), view=view())
    print('PASS History repeated LMB under one held A clears the previous candidate', flush=True)

    for case in ('early_A_release', 'escape_cancel', 'focus_loss_cancel'):
        before, before_view = state(), view()
        yield from arm()
        ring = yield from post(case)
        event('MOUSEMOVE', 'NOTHING', target(ring, 'SW'))
        yield from settle()
        if case == 'early_A_release':
            event('A', 'RELEASE')
            yield from settle()
            check(state() == before and view() == before_view,
                  'Early A release committed the currently hovered action')
            event('LEFTMOUSE', 'RELEASE')
        else:
            # Cancel a valid recorded candidate, not only an empty visible menu.
            event('LEFTMOUSE', 'RELEASE')
            yield from settle()
            if case == 'escape_cancel':
                event('ESC')
                event('ESC', 'RELEASE')
            else:
                event('WINDOW_DEACTIVATE', 'NOTHING')
            yield from settle()
            event('A', 'RELEASE')
        yield from settle(8)
        check(state() == before and view() == before_view and not modals(),
              case + ': scene/view changed or a stale modal remains: ' + str(modals()))
        evidence(case, 'after_release_drain', state(), view=view())
        print('PASS History ' + case + ': no scene/view change, no handler leak', flush=True)

    # A timer/another editor can change the scene between LMB and A releases.
    # Read both objects: checking only the old target would miss retargeting B.
    for case, direction in (('selection_swap_reset', 'SW'), ('selection_swap_history', 'NW'),
                            ('selection_added', 'SW'), ('active_only_changed', 'SW'),
                            ('selected_data_replaced', 'NW'), ('other_selected_data_replaced', 'NW'),
                            ('selection_changed_then_restored', 'SW'),
                            ('selection_changed_before_queue', 'SW'),
                            ('geometry_poll_changed', 'NW')):
        fixture('history')
        original = bpy.data.objects['History GUI Fixture']
        peer = original.copy()
        peer.data = original.data.copy()
        peer.name = 'History GUI Peer'
        bpy.context.scene.collection.objects.link(peer)
        peer.location = (8, 4, 2)
        peer.select_set(case in {'active_only_changed', 'other_selected_data_replaced'})
        bpy.context.view_layer.objects.active = original
        yield from settle()
        yield from arm()
        ring = yield from post(case)
        if case == 'selection_changed_before_queue':
            original.select_set(False)
            peer.select_set(True)
            bpy.context.view_layer.objects.active = peer
            yield from settle()
        yield from choose(ring, direction)
        if case.startswith('selection_swap') or case == 'selection_changed_then_restored':
            original.select_set(False)
            peer.select_set(True)
            bpy.context.view_layer.objects.active = peer
        elif case == 'selection_added':
            peer.select_set(True)
        elif case == 'active_only_changed':
            bpy.context.view_layer.objects.active = peer
        elif case == 'selected_data_replaced':
            original.data = original.data.copy()
        elif case == 'other_selected_data_replaced':
            peer.data = peer.data.copy()
        elif case == 'geometry_poll_changed':
            original.shape_key_add(name='Basis')
        yield from settle()
        if case == 'selection_changed_then_restored':
            peer.select_set(False)
            original.select_set(True)
            bpy.context.view_layer.objects.active = original
            yield from settle()
        before_both = {name: state(name) for name in ('History GUI Fixture', 'History GUI Peer')}
        before_view = view()
        evidence(case, 'after_external_change_before_A_release', before_both, view=before_view)
        yield from release()
        after_both = {name: state(name) for name in before_both}
        evidence(case, 'after_A_release', after_both, view=view())
        check(after_both == before_both and view() == before_view,
              case + ': deferred command retargeted/mutated scene, restored selection, or framed view')
        print('PASS History ' + case + ': stale candidate discarded without retargeting', flush=True)

    print('AXISMELD_HISTORY_HOTBOX_EVENTS_PASS', flush=True)


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

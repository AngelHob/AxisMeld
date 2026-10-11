# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Residual-release receipt gate. Run only through the disposable GUI runner."""
import os
import json
from pathlib import Path
import sys
import traceback
import unittest

import bpy

test_root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
if not Path(bpy.app.tempdir).resolve().is_relative_to(test_root):
    raise RuntimeError('Release test requires an isolated temporary directory')
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
events = []
window_events = {}
file_results = []
popup_results = []


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class AXISMELD_OT_release_probe(bpy.types.Operator):
    bl_idname = 'axismeld.release_probe'
    bl_label = 'Private release probe'
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        events.append((event.type, event.value))
        window_events.setdefault(context.window.as_pointer(), []).append((event.type, event.value))
        return {'FINISHED', 'PASS_THROUGH'} if event.type == 'ESC' else {'PASS_THROUGH'}


class AXISMELD_OT_release_priority_probe(bpy.types.Operator):
    bl_idname = 'axismeld.release_priority_probe'
    bl_label = 'Private priority release probe'
    bl_options = {'INTERNAL', 'MODAL_PRIORITY'}
    invoke = AXISMELD_OT_release_probe.invoke
    modal = AXISMELD_OT_release_probe.modal


class AXISMELD_OT_release_file_probe(bpy.types.Operator):
    bl_idname = 'axismeld.release_file_probe'
    bl_label = 'Private no-write file probe'
    directory: bpy.props.StringProperty(subtype='DIR_PATH', default=str(test_root))
    filename: bpy.props.StringProperty(subtype='FILE_NAME', default='')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        file_results.append('EXECUTE')
        return {'FINISHED'}

    def cancel(self, context):
        file_results.append('CANCEL')


class AXISMELD_OT_release_popup_probe(bpy.types.Operator):
    bl_idname = 'axismeld.release_popup_probe'
    bl_label = 'Private same-window confirmation'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=220)

    def draw(self, context):
        self.layout.label(text='Private no-write popup')

    def execute(self, context):
        popup_results.append('EXECUTE')
        return {'FINISHED'}

    def cancel(self, context):
        popup_results.append('CANCEL')


for cls in (AXISMELD_OT_release_probe, AXISMELD_OT_release_priority_probe,
            AXISMELD_OT_release_file_probe, AXISMELD_OT_release_popup_probe):
    bpy.utils.register_class(cls)


def settle(count=4):
    for _ in range(count):
        yield


def external_focus_probe():
    """A real OS focus change; event_simulate does not maintain GHOST win.active."""
    if sys.platform != 'win32':
        raise RuntimeError('This isolated external-focus fixture currently requires Windows')
    import ctypes
    from ctypes import wintypes
    api = ctypes.windll.user32
    api.CreateWindowExW.restype = wintypes.HWND
    api.CreateWindowExW.argtypes = (wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                   wintypes.HINSTANCE, ctypes.c_void_p)
    api.SetForegroundWindow.argtypes = (wintypes.HWND,)
    api.GetForegroundWindow.restype = wintypes.HWND
    api.DestroyWindow.argtypes = (wintypes.HWND,)
    hwnd = api.CreateWindowExW(0, 'STATIC', 'AxisMeld isolated focus probe',
                               0x10000000 | 0x80000000 | 0x00C00000,
                               20, 20, 280, 80, None, None, None, None)
    check(hwnd, 'private OS focus probe window could not be created')
    api.SetForegroundWindow(hwnd)
    return api, hwnd


def suite():
    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    failures = []
    cross_window = os.environ.get('AXISMELD_TEST_SUITE') == 'release-cross-window'
    try:
        bpy.ops.view3d.axismeld_hotbox_release_guard.get_rna_type()
        has_guard = True
    except KeyError:
        has_guard = False

    def event(target, kind, value='PRESS', target_region=None):
        target_region = target_region or next(r for r in area.regions if r.type == 'WINDOW')
        target.event_simulate(type=kind, value=value,
                              x=target_region.x + target_region.width // 2,
                              y=target_region.y + target_region.height // 2)

    def guard():
        if has_guard:
            result = bpy.ops.view3d.axismeld_hotbox_release_guard(
                'INVOKE_DEFAULT', trigger_type='SPACE', mouse_type='RIGHTMOUSE',
                trigger_down=True, mouse_down=True)
            check(result == {'RUNNING_MODAL'}, 'guard did not attach')

    for priority in (False, True):
        event(win, 'MOUSEMOVE', 'NOTHING')
        event(win, 'SPACE')
        event(win, 'RIGHTMOUSE')
        yield from settle()
        # Clear any default context menu before establishing the command handoff.
        event(win, 'ESC')
        yield from settle()
        with bpy.context.temp_override(window=win, area=area, region=region):
            probe = bpy.ops.axismeld.release_priority_probe if priority else bpy.ops.axismeld.release_probe
            probe('INVOKE_DEFAULT')
            guard()
        events.clear()
        event(win, 'MOUSEMOVE', 'NOTHING')
        event(win, 'A')
        event(win, 'A', 'RELEASE')
        yield from settle()
        before_release = list(events)
        print(f'WAITING priority={priority} guard={has_guard} receipt={before_release!r}', flush=True)
        if ('A', 'PRESS') not in before_release:
            failures.append(f'priority={priority}: unrelated key blocked while waiting')
        events.clear()
        event(win, 'RIGHTMOUSE', 'RELEASE')
        event(win, 'SPACE', 'RELEASE')
        yield from settle()
        receipt = list(events)
        event(win, 'MOUSEMOVE', 'NOTHING')
        event(win, 'LEFTMOUSE')
        event(win, 'LEFTMOUSE', 'RELEASE')
        event(win, 'ESC')
        yield from settle()
        print(f'RECEIPT priority={priority} guard={has_guard} residual={receipt!r} all={events!r}', flush=True)
        if any(item in receipt for item in [('RIGHTMOUSE', 'RELEASE'), ('SPACE', 'RELEASE')]):
            failures.append(f'priority={priority}: captured residual release reached child')
        for item in [('MOUSEMOVE', 'NOTHING'), ('LEFTMOUSE', 'PRESS'), ('ESC', 'PRESS')]:
            check(item in events, f'normal input blocked: {item}')

    if has_guard:
        # No preset/area poll is permitted: residual ownership survives either change.
        for recovery in ('fresh_press', 'fresh_last_press', 'focus_loss', 'source_area_loss', 'empty'):
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.axismeld.release_probe('INVOKE_DEFAULT')
                if recovery == 'empty':
                    check(bpy.ops.view3d.axismeld_hotbox_release_guard(
                        'INVOKE_DEFAULT', trigger_type='F13', mouse_type='NONE',
                        trigger_down=False, mouse_down=False) == {'FINISHED'},
                        'empty capture must not create a handler')
                else:
                    bpy.ops.view3d.axismeld_hotbox_release_guard(
                        'INVOKE_DEFAULT', trigger_type='F13', mouse_type='RIGHTMOUSE',
                        trigger_down=True, mouse_down=recovery != 'fresh_last_press')
            events.clear()
            if recovery in {'fresh_press', 'fresh_last_press'}:
                event(win, 'F13')
                event(win, 'F13', 'RELEASE')
                event(win, 'RIGHTMOUSE', 'RELEASE')
            elif recovery == 'focus_loss':
                event(win, 'WINDOW_DEACTIVATE', 'NOTHING')
                event(win, 'F13', 'RELEASE')
                event(win, 'RIGHTMOUSE', 'RELEASE')
            elif recovery == 'source_area_loss':
                area.type = 'CONSOLE'
                event(win, 'F13', 'RELEASE')
                event(win, 'RIGHTMOUSE', 'RELEASE')
            else:
                event(win, 'F13', 'RELEASE')
            yield from settle()
            receipt = list(events)
            event(win, 'ESC')
            yield from settle()
            print(f'RECOVERY {recovery} receipt={receipt!r}', flush=True)
            if recovery in {'fresh_press', 'fresh_last_press', 'focus_loss', 'empty'}:
                check(('F13', 'RELEASE') in receipt, f'{recovery}: new input swallowed')
            if recovery in {'fresh_press', 'fresh_last_press'}:
                check(('F13', 'PRESS') in receipt, 'fresh non-repeat press swallowed')
            if recovery == 'fresh_press':
                check(('RIGHTMOUSE', 'RELEASE') not in receipt, 'other capture lost on fresh trigger')
            if recovery == 'source_area_loss':
                # Frozen child probe can be removed with its area. Fresh normal input after restore
                # is covered by later tests; this path specifically guards against stale region use.
                area.type = 'VIEW_3D'
                yield from settle()
                region = next(r for r in area.regions if r.type == 'WINDOW')
        print('PASS empty capture, actual F13, lost-release recovery, focus loss, source editor loss', flush=True)

    if not cross_window:
        check(not failures, '; '.join(failures))
        # UI popup is created before the priority guard; its own UI handler must remain usable.
        for confirm in (True, False):
            with bpy.context.temp_override(window=win, area=area, region=region):
                check(bpy.ops.axismeld.release_popup_probe('INVOKE_DEFAULT') == {'RUNNING_MODAL'},
                      'same-window popup did not open')
                guard()
            yield from settle()
            event(win, 'RIGHTMOUSE', 'RELEASE')
            event(win, 'SPACE', 'RELEASE')
            yield from settle()
            check(len(popup_results) == (0 if confirm else 1), 'residual release acted on popup')
            event(win, 'MOUSEMOVE', 'NOTHING')
            event(win, 'RET' if confirm else 'ESC')
            yield from settle()
            check(popup_results == (['EXECUTE'] if confirm else ['EXECUTE', 'CANCEL']),
                  f'popup normal confirm/cancel blocked: {popup_results!r}')
        print('PASS same-window popup residual isolation and subsequent confirm/Esc', flush=True)
        # Guard remains valid after leaving AxisMeld preset; no active-preset dependency.
        preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                      if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
        bpy.utils.keyconfig_set(str(preset))
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.axismeld.release_probe('INVOKE_DEFAULT')
            guard()
        bpy.utils.keyconfig_set(str(preset.with_name('Industry_Compatible.py')))
        events.clear()
        event(win, 'RIGHTMOUSE', 'RELEASE')
        event(win, 'SPACE', 'RELEASE')
        yield from settle()
        check(('RIGHTMOUSE', 'RELEASE') not in events and ('SPACE', 'RELEASE') not in events,
              'preset change caused residual release leakage')
        event(win, 'ESC')
        yield from settle()
        print('PASS captured releases remain isolated after preset change', flush=True)
        yield from bridge_suite(win, area, region)
        print('AXISMELD_HOTBOX_RELEASE_EVENTS_PASS same-window scope only', flush=True)
        return

    check(bpy.context.preferences.view.filebrowser_display_type == 'WINDOW',
          'fixture must exercise default new-window file browser')
    guard_id = 'VIEW3D_OT_axismeld_hotbox_release_guard'
    for case in ('receiver_only', 'mouse_in_source', 'key_in_source', 'fresh_press',
                 'external_focus', 'receiver_close', 'source_close'):
        source, source_area, source_region = win, area, region
        if case == 'source_close':
            with bpy.context.temp_override(window=win, area=area, region=region):
                bpy.ops.wm.window_new()
            yield from settle(10)
            source = next(w for w in bpy.context.window_manager.windows if w != win)
            source_area = next(a for a in source.screen.areas if a.type == 'VIEW_3D')
            source_region = next(r for r in source_area.regions if r.type == 'WINDOW')
        source_id = source.as_pointer()
        initial_windows = {w.as_pointer() for w in bpy.context.window_manager.windows}
        event(source, 'SPACE', target_region=source_region)
        event(source, 'RIGHTMOUSE', target_region=source_region)
        yield from settle()
        event(source, 'ESC', target_region=source_region)
        yield from settle()
        file_results.clear()
        with bpy.context.temp_override(window=source, area=source_area, region=source_region):
            bpy.ops.axismeld.release_probe('INVOKE_DEFAULT')
            file_invoke = bpy.ops.axismeld.release_file_probe('INVOKE_DEFAULT')
            guard()
        print('FILE_INVOKE', case, file_invoke,
              [op.bl_idname for op in source.modal_operators], flush=True)
        # FULL_OPEN creates the receiver later. Hiding it here would cause a real
        # external focus-loss event and invalidate the capture being measured.
        for _ in range(40):
            if any(w.as_pointer() not in initial_windows for w in bpy.context.window_manager.windows):
                break
            yield
        receiver = next((w for w in bpy.context.window_manager.windows
                         if w.as_pointer() not in initial_windows), None)
        check(receiver is not None, 'queued file FULL_OPEN did not reach file-select handler')
        receiver_id = receiver.as_pointer()
        file_area = next(a for a in receiver.screen.areas if a.type == 'FILE_BROWSER')
        file_region = next(r for r in file_area.regions if r.type == 'WINDOW')
        yield from settle(10)
        print('FILE_HANDLERS', case, [op.bl_idname for op in source.modal_operators],
              [op.bl_idname for op in receiver.modal_operators], flush=True)
        check(guard_id in [op.bl_idname for op in receiver.modal_operators],
              case + ': exact receiver did not inherit release ownership')
        with bpy.context.temp_override(window=receiver, area=file_area, region=file_region):
            bpy.ops.axismeld.release_probe('INVOKE_DEFAULT')
        events.clear()
        window_events.clear()
        focus_probe = None
        if case == 'source_close':
            with bpy.context.temp_override(window=source, area=source_area, region=source_region):
                bpy.ops.wm.window_close()
            yield from settle(12)
            live_ids = {w.as_pointer() for w in bpy.context.window_manager.windows}
            check(source_id not in live_ids, 'disposable source did not close')
            for current in bpy.context.window_manager.windows:
                check(guard_id not in [op.bl_idname for op in current.modal_operators],
                      'source destruction left release ownership alive')
            if receiver_id in live_ids:
                event(receiver, 'ESC', target_region=file_region)
                yield from settle(12)
            check(len(bpy.context.window_manager.windows) == 1, 'source close left an orphan window')
            print('PASS FILE_LIFECYCLE source_close', file_results, flush=True)
            continue
        if case == 'receiver_close':
            with bpy.context.temp_override(window=receiver, area=file_area, region=file_region):
                bpy.ops.wm.window_close()
            yield from settle(12)
            check(len(bpy.context.window_manager.windows) == 1, 'receiver did not close')
            event(source, 'RIGHTMOUSE', 'RELEASE', source_region)
            event(source, 'SPACE', 'RELEASE', source_region)
        else:
            if case == 'external_focus':
                focus_probe = external_focus_probe()
                yield from settle(8)
                api, hwnd = focus_probe
                check(api.GetForegroundWindow() == hwnd,
                      'OS did not activate the private external-focus window')
                # --enable-event-simulate still updates GHOST window activation,
                # but wm_event_add_ghostevent deliberately drops OS queue input.
                # Supply its WM event only after the real activation has changed.
                event(receiver, 'WINDOW_DEACTIVATE', 'NOTHING', file_region)
                yield from settle(4)
                check(all(guard_id not in [op.bl_idname for op in w.modal_operators]
                          for w in (source, receiver)),
                      'real external focus loss did not retire paired release guards')
            elif case == 'fresh_press':
                event(receiver, 'SPACE', 'PRESS', file_region)
            mouse_target = source if case == 'mouse_in_source' else receiver
            key_target = source if case == 'key_in_source' else receiver
            event(mouse_target, 'RIGHTMOUSE', 'RELEASE',
                  source_region if mouse_target == source else file_region)
            event(key_target, 'SPACE', 'RELEASE',
                  source_region if key_target == source else file_region)
        yield from settle(8)
        receipt = list(events)
        print('FILE_RECEIPT', case, window_events, 'results=', file_results, flush=True)
        if case not in {'external_focus', 'fresh_press'}:
            if any(item in receipt for item in [('RIGHTMOUSE', 'RELEASE'), ('SPACE', 'RELEASE')]):
                failures.append(case + ': captured residual release reached child')
        elif case == 'fresh_press':
            check(('SPACE', 'PRESS') in receipt and ('SPACE', 'RELEASE') in receipt,
                  'new press/release after lost release was swallowed')
            check(('RIGHTMOUSE', 'RELEASE') not in receipt, 'fresh key lost other capture')
        else:
            check(('SPACE', 'RELEASE') in receipt and ('RIGHTMOUSE', 'RELEASE') in receipt,
                  'external focus loss swallowed future releases')
        if focus_probe:
            api, hwnd = focus_probe
            api.DestroyWindow(hwnd)
            yield from settle(4)
        if case != 'receiver_close':
            check(not file_results, 'residual release confirmed/cancelled file browser')
            event(receiver, 'MOUSEMOVE', 'NOTHING', file_region)
            event(receiver, 'LEFTMOUSE', 'PRESS', file_region)
            event(receiver, 'LEFTMOUSE', 'RELEASE', file_region)
            event(receiver, 'ESC', 'PRESS', file_region)
            yield from settle(14)
        check(file_results == ['CANCEL'], f'file cancel failed: {file_results!r}')
        check(len(bpy.context.window_manager.windows) == 1, 'file browser window remained open')
        check(guard_id not in [op.bl_idname for op in source.modal_operators],
              'completed source guard remained attached')
        event(source, 'ESC', target_region=source_region)
        yield from settle()
        print('PASS FILE_LIFECYCLE', case, flush=True)
    check(not failures, '; '.join(failures))
    print('AXISMELD_HOTBOX_CROSS_WINDOW_PASS', flush=True)


def bridge_suite(win, area, region):
    from axismeld import hotbox_runtime, adapter
    check(hasattr(hotbox_runtime, 'dispatch'), 'semantic dispatch is missing')
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    bpy.utils.keyconfig_set(str(preset))
    yield from settle()
    bpy.context.window_manager.keyconfigs.active.preferences.use_file_overrides = False
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        wm = bpy.context.window_manager
        check(bpy.ops.axismeld.hotbox_refresh() == {'FINISHED'}, 'snapshot refresh failed')
        first = json.loads(wm.axismeld_hotbox_snapshot)
        check(first['settings']['style'] == 'rows', 'initial settings differ')
        common = first['menus'][0]['children']
        directories=[node for node in common if node['id'] in {'common.file','common.windows'}]
        check(len(directories)==2 and all(n['kind']=='menu' and n['children'] for n in directories),
              'real Maya File/Windows hierarchy is missing')
        pending=[child for menu in directories for child in menu['children']]
        leaves=[]
        while pending:
            child=pending.pop();pending.extend(child['children'])
            if child['kind'] not in {'menu','separator'}:leaves.append(child)
        reviewed = {'maya.common.file.open_scene': 'file.open',
                    'maya.common.file.save_scene_as': 'file.save_as'}
        check({node['id']: node.get('command') for node in leaves if node['enabled']} == reviewed,
              'File selector admission differs from the two reviewed bodies')
        check(leaves and all(not node['enabled'] and not node.get('command')
                             for node in leaves if node['id'] not in reviewed),
              'unadapted file/window action became operational')
        check(bpy.ops.axismeld.hotbox_setting(setting='style', value='center') == {'FINISHED'},
              'style setting failed')
        bpy.ops.axismeld.hotbox_setting(setting='transparency', value='75')
        bpy.ops.axismeld.hotbox_setting(setting='row.common', value='toggle')
        bpy.ops.axismeld.hotbox_setting(setting='row.common', value='toggle')
        bpy.ops.axismeld.hotbox_setting(setting='row.pane', value='toggle')
        bpy.ops.axismeld.hotbox_refresh()
        changed = json.loads(wm.axismeld_hotbox_snapshot)
        check(changed['settings'] == {'style': 'center', 'transparency': 75,
              'appearance': {'theme_background': True, 'background': [64, 64, 64], 'brightness': -13,
                             'text': [160, 160, 160], 'placeholder': [0, 0, 0],
                             'theme_hover_text': True, 'hover_text': [255, 255, 255]},
              'rows': ['common', 'modeling'], 'center_buttons': {
                  'LEFTMOUSE': 'views', 'MIDDLEMOUSE': 'views', 'RIGHTMOUSE': 'views'}},
              'settings mutation or canonical row ordering failed')
        check(changed['generation'] > first['generation'], 'generation did not advance')
        for setting, value in [('style', 'bad'), ('transparency', 'True'), ('row.center', 'toggle')]:
            check(bpy.ops.axismeld.hotbox_setting(setting=setting, value=value) == {'CANCELLED'},
                  'invalid setting accepted')
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings'] == changed['settings'],
              'invalid setting partly mutated state')
        session = {'schema_version': 1, 'settings': {'style': 'zones', 'rows': ['pane']}}
        hotbox_runtime.reload_settings(bpy.context, session=session)
        session['settings']['rows'].append('modeling')
        check(json.loads(hotbox_runtime.snapshot(bpy.context))['settings']['rows'] == ['pane'],
              'reload retained caller mutable state')
        hotbox_runtime.reload_settings(bpy.context, session={
            'schema_version': True, 'settings': {'style': 'center'}})
        check(hotbox_runtime.diagnostics, 'invalid reload omitted diagnostics')
        preserved = json.loads(hotbox_runtime.snapshot(bpy.context))['settings']
        check(preserved['style'] == 'zones' and preserved['rows'] == ['pane'],
              'invalid layer replaced the previous valid session')
        hotbox_runtime.reload_settings(
            bpy.context, session={'schema_version': 1, 'settings': {}})
        for command in ('view.front', 'view.wireframe', 'view.shaded'):
            check(bpy.ops.axismeld.hotbox_dispatch(command=command) == {'FINISHED'}, command)
        check(area.spaces.active.shading.type == 'SOLID', 'dispatch did not change real shading')
        check(hotbox_runtime.recent.items()[:3] == ('view.shaded', 'view.wireframe', 'view.front'),
              'real completed commands were not recorded')
        before = hotbox_runtime.recent.items()
        for command in ('hotbox.open', 'view.orbit', 'wm.open_mainfile', 'wm.window_new', 'unknown'):
            check(bpy.ops.axismeld.hotbox_dispatch(command=command) == {'CANCELLED'},
                  'dispatch allowlist failed: ' + command)
        check(hotbox_runtime.recent.items() == before, 'rejected command entered Recent')
        # Capture a currently-enabled entry, then invalidate real context before dispatch.
        check(adapter.available(bpy.context, 'selection.vertex_mode')[0], 'selection fixture unavailable')
        cube = bpy.context.active_object
        cube.hide_set(True)
        check(bpy.ops.axismeld.hotbox_dispatch(command='selection.vertex_mode') == {'CANCELLED'},
              'dispatch failed to recheck live availability')
        check(hotbox_runtime.recent.items() == before, 'unavailable command entered Recent')
        cube.hide_set(False)
        # Force adapter failure at its unavoidable boundary; all history/wrapper behavior is real.
        original = adapter.run
        try:
            adapter.run = lambda *a, **k: {'FINISHED'}
            cube.hide_set(True)
            check(bpy.ops.axismeld.hotbox_dispatch(command='selection.vertex_mode') == {'CANCELLED'},
                  'dispatch delegated availability checking solely to the adapter run')
            cube.hide_set(False)
            adapter.run = lambda *a, **k: {'CANCELLED'}
            with unittest.TestCase().assertNoLogs('axismeld.hotbox_runtime', level='ERROR'):
                check(bpy.ops.axismeld.hotbox_dispatch(command='view.top') == {'CANCELLED'}, 'cancel lost')
            def raise_error(*args, **kwargs):
                raise RuntimeError('private expected adapter failure')
            adapter.run = raise_error
            with unittest.TestCase().assertLogs('axismeld.hotbox_runtime', level='ERROR') as diagnostic:
                check(bpy.ops.axismeld.hotbox_dispatch(command='view.top') == {'CANCELLED'}, 'exception lost')
            message = diagnostic.records[0].getMessage()
            check(all(detail in message for detail in
                      ('view.top', 'RuntimeError', 'private expected adapter failure')),
                  'dispatch exception diagnostic lacks command/type/message')
            print('PASS dispatch exception diagnostic:', message, flush=True)
            adapter.run = lambda *a, **k: bpy.ops.axismeld.release_priority_probe('INVOKE_DEFAULT')
            check(bpy.ops.axismeld.hotbox_dispatch(command='view.top') == {'FINISHED'}, 'modal wrapper')
            check([op.bl_idname for op in win.modal_operators] == ['AXISMELD_OT_release_priority_probe'],
                  'wrapper claimed child modal handler')
            bpy.ops.view3d.axismeld_hotbox_release_guard(
                'INVOKE_DEFAULT', trigger_type='SPACE', mouse_type='RIGHTMOUSE',
                trigger_down=True, mouse_down=True)
        finally:
            adapter.run = original
        check(hotbox_runtime.recent.items() == before, 'cancel/error/running-modal entered Recent')
        original_snapshot = hotbox_runtime.snapshot
        try:
            hotbox_runtime.snapshot = raise_error
            check(bpy.ops.axismeld.hotbox_refresh() == {'CANCELLED'}, 'refresh failure not propagated')
            check(wm.axismeld_hotbox_snapshot == '', 'failed refresh reused stale payload')
        finally:
            hotbox_runtime.snapshot = original_snapshot
        # RNA response is transient and registration cleans it up.
        prop = wm.bl_rna.properties['axismeld_hotbox_snapshot']
        check(prop.is_hidden and prop.is_skip_save, 'snapshot property is not transient/hidden')
    events.clear()
    for event_type in ('RIGHTMOUSE', 'SPACE'):
        win.event_simulate(type=event_type, value='RELEASE', x=region.x + 20, y=region.y + 20)
    yield from settle()
    check(('RIGHTMOUSE', 'RELEASE') not in events and ('SPACE', 'RELEASE') not in events,
          'dispatch wrapper child received captured releases')
    win.event_simulate(type='ESC', value='PRESS', x=region.x + 20, y=region.y + 20)
    yield from settle()
    with bpy.context.temp_override(window=win, area=area, region=region):
        # Actual successful context-changing commands; no stubbed adapter during these assertions.
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
        for command, expected in (('selection.vertex_mode', (True, False, False)),
                                  ('selection.edge_mode', (False, True, False)),
                                  ('selection.face_mode', (False, False, True))):
            check(bpy.ops.axismeld.hotbox_dispatch(command=command) == {'FINISHED'}, command)
            check(bpy.context.mode == 'EDIT_MESH' and
                  tuple(bpy.context.tool_settings.mesh_select_mode) == expected,
                  'semantic selection did not update actual mode')
        check(bpy.ops.axismeld.hotbox_dispatch(command='selection.toggle_component') == {'FINISHED'},
              'object/component dispatch failed')
        check(bpy.context.mode == 'OBJECT', 'object mode not restored')
        for command, tool_id in (('transform.move', 'builtin.move'),
                                  ('transform.rotate', 'builtin.rotate'),
                                  ('transform.scale', 'builtin.scale')):
            check(bpy.ops.axismeld.hotbox_dispatch(command=command) == {'FINISHED'}, command)
            check(bpy.context.workspace.tools.from_space_view3d_mode('OBJECT').idname == tool_id,
                  'dispatch did not activate expected tool')
        for command in ('view.perspective', 'view.side', 'view.bottom', 'view.front', 'view.back',
                        'view.top', 'view.left', 'view.focus_selected', 'view.frame_all'):
            check(bpy.ops.axismeld.hotbox_dispatch(command=command) == {'FINISHED'}, command)
    for expected_count in (4, 1):
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=win, area=area, region=region):
            check(bpy.ops.axismeld.hotbox_dispatch(command='view.toggle_quad') == {'FINISHED'},
                  'quad dispatch failed')
        yield from settle()
        check(len([r for r in area.regions if r.type == 'WINDOW']) == expected_count,
              'dispatch did not change actual region topology')
    from bl_operators import axismeld as operator_module
    operator_module.unregister()
    check(not hasattr(bpy.types.WindowManager, 'axismeld_hotbox_snapshot'), 'RNA property leaked on unregister')
    operator_module.register()
    check(bpy.context.window_manager.axismeld_hotbox_snapshot == '', 'RNA response persisted on re-register')
    print('PASS live settings/refresh, restricted dispatch, actual child ownership, Recent success-only', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return 0.025
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1.0)

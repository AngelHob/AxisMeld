# SPDX-License-Identifier: GPL-2.0-or-later
"""Installed-code GUI acceptance, in an isolated unsaved factory process only.

Requires AXISMELD_TEST_ROOT, AXISMELD_TEST_ARTIFACTS, BLENDER_USER_CONFIG and
TEMP isolation. Launch with --factory-startup --enable-event-simulate --python.
Uses real props dialogs; RNA selection, simulated RET/ESC and F9 field editing.
No source overlay, no installation writes, no physical mouse acceptance claim.
"""
import json
import os
from pathlib import Path
import sys
import traceback

import bpy
import numpy as np
from axismeld import modeling_common_ops as implementation, translations

sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import menu_background_mask, observed_menu_rectangles

ROOT = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
ART = Path(os.environ['AXISMELD_TEST_ARTIFACTS']).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(ROOT), 'Disposable TEMP required'
assert Path(os.environ['BLENDER_USER_CONFIG']).resolve().is_relative_to(ROOT), 'Isolated config required'
assert not bpy.app.background and not bpy.data.filepath, 'Unsaved factory GUI required'
ART.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False
RECORD = {'schema': 1, 'status': 'RUNNING', 'cases': [], 'module': implementation.__file__,
          'binary': bpy.app.binary_path, 'version': bpy.app.version_string,
          'interactionMethod': 'Actual invoke_props_dialog host; RNA selector changes; event_simulate RET/ESC and F9 mouse/text input; native ed.undo/redo',
          'manualAcceptanceChanged': False,
          'boundary': 'Test-owned instrumentation calls original invoke/draw/execute/cancel. No physical input, complete public-menu route or high-DPI readability acceptance.'}
OP = implementation.AXISMELD_OT_m3_custom_property
CURRENT = None
POPUP = None
TRACE = []
TAG = ''
ORIGINAL = {name: getattr(OP, name) for name in ('invoke', 'draw', 'execute', 'cancel')}


def fields(op):
    return {key: getattr(op, key) for key in ('action', 'property', 'name', 'kind', 'value')}


def tracked_invoke(op, context, event):
    global CURRENT, POPUP
    CURRENT = op
    POPUP = None
    result = ORIGINAL['invoke'](op, context, event)
    TRACE.append({'method': 'invoke', 'tag': TAG, 'result': sorted(result), 'fields': fields(op)})
    return result


def tracked_draw(op, context):
    global POPUP
    POPUP = context.region_popup
    TRACE.append({'method': 'draw', 'tag': TAG, 'fields': fields(op)})
    ORIGINAL['draw'](op, context)


def tracked_execute(op, context):
    global POPUP
    entry = {'method': 'execute', 'tag': TAG, 'fields': fields(op)}
    result = ORIGINAL['execute'](op, context)
    POPUP = None
    entry['result'] = sorted(result)
    TRACE.append(entry)
    return result


def tracked_cancel(op, context):
    global POPUP
    POPUP = None
    TRACE.append({'method': 'cancel', 'tag': TAG})
    return ORIGINAL['cancel'](op, context)


for name, function in (('invoke', tracked_invoke), ('draw', tracked_draw),
                       ('execute', tracked_execute), ('cancel', tracked_cancel)):
    setattr(OP, name, function)


def record(case, **details):
    RECORD['cases'].append({'case': case, **details})
    RECORD['trace'] = TRACE
    (ART / 'custom-property-gui.json').write_text(json.dumps(RECORD, ensure_ascii=False, indent=2), encoding='utf-8')


def settle(count=5):
    for _ in range(count):
        yield


def values(obj):
    return {key: [type(obj[key]).__name__, obj[key]] for key in obj.keys()}


def suite():
    global TAG, CURRENT
    prefs = bpy.context.preferences
    prefs.edit.use_global_undo = True
    window = bpy.context.window
    area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    point = [round(region.x + region.width / 2), round(region.y + region.height / 2)]

    def context():
        return bpy.context.temp_override(window=window, area=area, region=region)

    def event(kind, value='PRESS', **kwargs):
        window.event_simulate(type=kind, value=value, x=point[0], y=point[1], **kwargs)

    def key(kind, unicode=None, **modifiers):
        kwargs = dict(modifiers)
        if unicode is not None:
            kwargs['unicode'] = unicode
        event(kind, **kwargs)
        yield from settle(2)
        # Native event_simulate accepts unicode on PRESS only.
        event(kind, 'RELEASE', **modifiers)
        yield from settle(2)

    def screenshot(name):
        path = ART / (name + '.png')
        with context():
            bpy.ops.screen.screenshot(filepath=str(path))
        return path

    def source():
        return bpy.data.objects['CP GUI Source']

    def open_edit(tag):
        global TAG
        TAG = tag
        event('MOUSEMOVE', 'NOTHING')
        yield from settle(2)
        with context():
            assert bpy.ops.axismeld.m3_custom_property('INVOKE_DEFAULT', action='EDIT') == {'RUNNING_MODAL'}
        yield from settle()
        assert any(item['method'] == 'draw' and item['tag'] == tag for item in TRACE), 'Native dialog never drew'
        assert POPUP is not None and POPUP.type == 'TEMPORARY', 'Missing native popup refresh context'
        assert CURRENT.kind == 'INTEGER' and CURRENT.name == 'Count' and CURRENT.value == str(source()['Count'])

    with context():
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects.new('CP GUI Source', None)
        bpy.context.scene.collection.objects.link(obj)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for name, value in (('Count', 7), ('Enabled', False), ('Text', '007'), ('Weight', 1.5), ('Name', '用户字符串')):
            obj[name] = value
        bpy.ops.ed.undo_push(message='CP GUI fixture baseline')
    yield from settle()

    for locale in ('en_US', 'zh_HANS'):
        prefs.view.language = locale
        prefs.view.use_translate_interface = True
        prefs.view.use_translate_tooltips = True
        prefs.view.use_translate_reports = True
        translations.register()
        yield from settle()
        before = values(source())
        yield from open_edit(locale + '-cancel')
        for name, kind, value in (('Enabled', 'BOOLEAN', 'False'), ('Text', 'STRING', '007'),
                                  ('Weight', 'FLOAT', '1.5'), ('Name', 'STRING', '用户字符串')):
            trace_start = len(TRACE)
            with context():
                CURRENT.property = name
            # Scripted RNA assignment has no native button event to refresh the
            # cached popup layout. Use the public temporary-region refresh API,
            # then require a real draw with the changed fields before capturing.
            POPUP.tag_refresh_ui()
            event('MOUSEMOVE', 'NOTHING')
            yield from settle()
            assert (CURRENT.name, CURRENT.kind, CURRENT.value) == (name, kind, value)
            draws = [item for item in TRACE[trace_start:] if item['method'] == 'draw' and item['tag'] == TAG]
            assert draws and all(draws[-1]['fields'][key] == expected for key, expected in
                                 (('property', name), ('name', name), ('kind', kind), ('value', value))), draws
            assert values(source()) == before
            record('selector-native-draw', locale=locale, fields=draws[-1]['fields'],
                   method='RNA selector; native Region.tag_refresh_ui; MOUSEMOVE event; actual operator draw')
        screenshot(locale + '-dialog-user-data')
        yield from key('ESC')
        yield from settle()
        assert values(source()) == before
        assert any(item['method'] == 'cancel' and item['tag'] == TAG for item in TRACE)
        record('selector-and-cancel-preserve-data', locale=locale, before=before, after=values(source()), method='RNA selection; ESC event')
        CURRENT = None

        yield from open_edit(locale + '-confirm')
        with context():
            CURRENT.value = '9'
        yield from key('RET')
        yield from settle()
        assert source()['Count'] == 9 and type(source()['Count']) is int
        assert any(item['method'] == 'execute' and item['tag'] == TAG and item['result'] == ['FINISHED'] for item in TRACE)
        record('native-dialog-confirm', locale=locale, value=source()['Count'], method='RNA value; RET event')
        CURRENT = None
        with context():
            assert bpy.ops.ed.undo() == {'FINISHED'}
        yield from settle()
        assert values(source()) == before
        with context():
            assert bpy.ops.ed.redo() == {'FINISHED'}
        yield from settle()
        assert source()['Count'] == 9 and type(source()['Count']) is int
        with context():
            f9_after_undo_redo = bpy.ops.screen.redo_last.poll()
        record('native-one-undo-and-redo', locale=locale, value=source()['Count'],
               operatorStackCount=len(bpy.context.window_manager.operators), f9Available=f9_after_undo_redo)

        # Native ed_undo_refresh_for_op clears the last-operator stack. F9 must
        # follow a fresh confirmed operation, rather than the independent
        # Undo/Redo check above (screen.redo_last polls that stack).
        yield from open_edit(locale + '-fresh-confirm-for-F9')
        with context():
            CURRENT.value = '11'
        yield from key('RET')
        yield from settle()
        assert source()['Count'] == 11 and type(source()['Count']) is int
        with context():
            assert bpy.ops.screen.redo_last.poll(), 'Fresh confirmed operator missing from native F9 stack'
        record('fresh-native-confirm-for-F9', locale=locale, value=source()['Count'],
               operatorStackCount=len(bpy.context.window_manager.operators), method='RNA value; RET event')
        CURRENT = None

        # Native F9 popup is measured from its rendered background only. The
        # bottom field is Value in this four-field operator's existing draw.
        # No private button coordinates or implementation state are written.
        colors = prefs.themes[0].user_interface.wcol_menu_back
        previous_color = tuple(colors.inner)
        colors.inner = (0.65, 0.04, 0.55, 1.0)  # Disposable diagnostic theme.
        TAG = locale + '-F9'
        trace_start = len(TRACE)
        with context():
            bpy.ops.screen.redo_last('INVOKE_DEFAULT')
        yield from settle(8)
        draws = [item for item in TRACE[trace_start:] if item['method'] == 'draw']
        assert draws and draws[-1]['fields']['value'] == '11' and draws[-1]['fields']['kind'] == 'INTEGER', draws
        path = screenshot(locale + '-F9-before')
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
            scale = prefs.system.ui_scale
            boxes = observed_menu_rectangles(menu_background_mask(pixels), 180 * scale, 70 * scale)
        finally:
            bpy.data.images.remove(image)
        assert len(boxes) == 1, ('Expected one rendered F9 popup', boxes)
        left, bottom, right, top = boxes[0]
        point[:] = [round(right - 70 * scale), round(bottom + 17 * scale)]
        # Native UI needs a hover event to activate the new button before text
        # entry. Match the proven Skin options field-edit event sequence.
        event('MOUSEMOVE', 'NOTHING')
        yield from settle(3)
        yield from key('LEFTMOUSE', ctrl=True)
        focus_path = screenshot(locale + '-F9-field-focus')
        focus_fields = fields(bpy.context.window_manager.operators[-1])
        yield from key('A', ctrl=True)
        yield from key('FOUR', unicode='4')
        text_path = screenshot(locale + '-F9-field-pending-text')
        record('native-F9-input-stages', locale=locale, focusScreenshot=str(focus_path),
               pendingTextScreenshot=str(text_path), focusOperator=focus_fields,
               pendingOperator=fields(bpy.context.window_manager.operators[-1]),
               method='MOUSEMOVE; Ctrl+click; Ctrl+A; text PRESS-only Unicode; RNA commits on RET')
        yield from key('RET')
        yield from settle(8)
        assert source()['Count'] == 4 and type(source()['Count']) is int, ('F9 did not recompute', TRACE[trace_start:])
        executions = [item for item in TRACE[trace_start:] if item['method'] == 'execute']
        assert executions and executions[-1]['fields']['value'] == '4' and executions[-1]['result'] == ['FINISHED'], executions
        screenshot(locale + '-F9-after')
        yield from key('ESC')
        colors.inner = previous_color
        record('native-F9-field-recompute', locale=locale, popup=list(boxes[0]), click=list(point), executions=executions,
               method='screen.redo_last popup; rendered bottom-field position; simulated hover/Ctrl+click/Ctrl+A/4/RET')
        # Restore this fixture through RNA for the next locale, then push a new
        # explicit baseline; these pushes are harness setup, never product work.
        source()['Count'] = 7
        with context():
            bpy.ops.ed.undo_push(message='CP next locale baseline')

    RECORD['status'] = 'PASS'
    record('complete')


STEPS = suite()


def tick():
    try:
        next(STEPS)
        return 0.15
    except StopIteration:
        print('AXISMELD_CUSTOM_PROPERTY_GUI_PASS', json.dumps(RECORD), flush=True)
    except Exception:
        RECORD['status'] = 'FAIL'
        RECORD['error'] = traceback.format_exc()
        record('failure')
        print(RECORD['error'], flush=True)
    for name, method in ORIGINAL.items():
        setattr(OP, name, method)
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(tick, first_interval=1.0)

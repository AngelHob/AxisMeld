# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Properties RNA navigation in a disposable GUI, driven by an app timer.

Set BLENDER_USER_CONFIG and TEMP to directories under AXISMELD_TEST_ROOT, then
run: blender --factory-startup --python axismeld_property_navigation_gui.py
Writes property-navigation-gui.json under AXISMELD_TEST_ARTIFACTS (or ROOT).
This creates test objects/windows and exits. Never run against a working file.
Native field mouse editing/Undo remains a separate manual acceptance item;
this script verifies the native transform operator and its actual Undo stack.
"""
import json
import os
from pathlib import Path
import traceback

import bpy
from axismeld import hotbox_runtime, menubar_runtime, property_navigation, translations

ROOT = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
ART = Path(os.environ.get('AXISMELD_TEST_ARTIFACTS', ROOT)).resolve()
assert Path(bpy.app.tempdir).resolve().is_relative_to(ROOT), 'Requires disposable TEMP isolation'
assert Path(os.environ['BLENDER_USER_CONFIG']).resolve().is_relative_to(ROOT), 'Requires isolated config'
assert not bpy.app.background, 'Real GUI required'
assert not bpy.data.filepath, 'Requires unsaved factory startup'
ART.mkdir(parents=True, exist_ok=True)
RECORD = {'schema': 1, 'status': 'RUNNING', 'cases': [], 'binary': bpy.app.binary_path,
          'version': bpy.app.version_string, 'manualAcceptanceChanged': False,
          'navigationModule': property_navigation.__file__,
          'boundary': 'Real Properties RNA and native operator Undo; physical field editing remains manual'}


def record(name, **details):
    RECORD['cases'].append({'case': name, **details})
    (ART / 'property-navigation-gui.json').write_text(
        json.dumps(RECORD, ensure_ascii=False, indent=2), encoding='utf-8')


def settle():
    for _ in range(4):
        yield


def override(window, area):
    return bpy.context.temp_override(window=window, area=area,
                                     region=next(r for r in area.regions if r.type == 'WINDOW'))


def state(window):
    return {'scene': window.scene.name, 'layer': window.view_layer.name,
            'workspace': window.workspace.name, 'mode': window.view_layer.objects.active.mode,
            'active': window.view_layer.objects.active.name,
            'objects': [(o.name, o.type, tuple(o.location), tuple(o.rotation_euler), tuple(o.scale),
                         o.select_get(view_layer=window.view_layer),
                         [(m.name, m.type) for m in o.modifiers]) for o in window.scene.objects]}


def identities():
    """Record actual source boundaries so fixture synchronization is visible."""
    result = []
    for window in bpy.context.window_manager.windows:
        item = {'window': window.as_pointer(), 'screen': window.screen.as_pointer(),
                'scene': window.scene.name, 'layer': window.view_layer.name,
                'active': getattr(window.view_layer.objects.active, 'name', None), 'properties': []}
        for area in window.screen.areas:
            if area.type != 'PROPERTIES':
                continue
            space = area.spaces.active
            with override(window, area):
                item['properties'].append({'area': area.as_pointer(), 'tab': space.context,
                                           'pin': getattr(space.pin_id, 'name', None),
                                           'pinFlag': space.use_pin_id,
                                           'contextObject': getattr(bpy.context.object, 'name', None)})
        result.append(item)
    return result


def main():
    prefs = bpy.context.preferences
    prefs.use_preferences_save = False
    prefs.view.show_splash = False
    source_window = bpy.context.window
    source_scene = source_window.scene
    viewport = next(a for a in source_window.screen.areas if a.type == 'VIEW_3D')
    props = next(a for a in source_window.screen.areas if a.type == 'PROPERTIES')
    pinned = next(a for a in source_window.screen.areas if a.type == 'OUTLINER')
    pinned.type = 'PROPERTIES'  # Test fixture only; navigation never converts areas.
    with override(source_window, viewport):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.name = 'PN Source'
        obj.modifiers.new('PN Native Bevel', 'BEVEL')
    pin_obj = bpy.data.objects.new('PN Unrelated Pin', None)
    source_window.scene.collection.objects.link(pin_obj)
    pinned.spaces.active.pin_id = pin_obj
    pinned.spaces.active.use_pin_id = True
    yield from settle()
    pinned.spaces.active.context = 'OBJECT'
    pinned.spaces.active.search_filter = 'pinned search'
    pin_state = (pinned.spaces.active.context, pinned.spaces.active.search_filter,
                 pinned.spaces.active.pin_id.as_pointer(), pinned.spaces.active.use_pin_id)

    before_windows = {w.as_pointer() for w in bpy.context.window_manager.windows}
    with override(source_window, viewport):
        # A child wm.window_new synchronizes scene changes with its parent.
        # Independent main windows are required to test different source scenes.
        bpy.ops.wm.window_new_main()
    other_window = next(w for w in bpy.context.window_manager.windows if w.as_pointer() not in before_windows)
    other_scene = bpy.data.scenes.new('PN Other Scene')
    other_window.scene = other_scene
    other_obj = bpy.data.objects.new('PN Other Active', None)
    other_scene.collection.objects.link(other_obj)
    other_window.view_layer.objects.active = other_obj
    other_obj.select_set(True, view_layer=other_window.view_layer)
    other_area = next(a for a in other_window.screen.areas if a.type == 'PROPERTIES')
    yield from settle()
    other_area.spaces.active.context = 'OBJECT'
    other_area.spaces.active.search_filter = 'other window search'
    other_state = state(other_window)
    assert source_window.scene == source_scene and source_window.scene != other_scene, identities()
    assert source_window.view_layer.objects.active == obj, identities()
    baseline = state(source_window)
    record('independent-window-source-fixture', windows=identities(), expectedObject=obj.name)
    recent_before = hotbox_runtime.recent.items()
    from bl_operators import axismeld as operators
    for cls in (operators.AXISMELD_OT_object_transform_properties, operators.AXISMELD_OT_modifier_properties):
        assert not ({'UNDO', 'REGISTER', 'INTERNAL'} & cls.bl_options), cls.bl_options

    with override(source_window, viewport):
        token = menubar_runtime.source_token(bpy.context)
    labels = ('Blender Object Properties', 'Object Transform Properties', 'Modifier Properties')
    for locale, scale in (('en_US', 1.0), ('zh_HANS', 1.5)):
        prefs.view.language = locale
        prefs.view.use_translate_interface = True
        prefs.view.use_translate_tooltips = True
        prefs.view.ui_scale = scale
        yield from settle()
        for target, key, op in (
                ('OBJECT', 'properties.object_transform', bpy.ops.axismeld.object_transform_properties),
                ('MODIFIER', 'properties.modifier', bpy.ops.axismeld.modifier_properties)):
            props.spaces.active.search_filter = 'filter to clear'
            with override(source_window, viewport):
                assert op.poll(), (locale, target, property_navigation.available(bpy.context, target))
                assert op('EXEC_DEFAULT') == {'FINISHED'}
                assert menubar_runtime.run(bpy.context, 'action', key, token) == {'FINISHED'}
            yield from settle()
            assert props.spaces.active.context == target
            assert props.spaces.active.search_filter == ''
            with override(source_window, props):
                assert bpy.context.object == obj, (target, bpy.context.object)
            assert state(source_window) == baseline
            assert state(other_window) == other_state
            assert hotbox_runtime.recent.items() == recent_before
            assert (pinned.spaces.active.context, pinned.spaces.active.search_filter,
                    pinned.spaces.active.pin_id.as_pointer(), pinned.spaces.active.use_pin_id) == pin_state
            assert other_area.spaces.active.search_filter == 'other window search'
            captions = [translations.iface(label) for label in labels]
            assert all(any('\u3400' <= c <= '\u9fff' for c in label) for label in captions) if locale == 'zh_HANS' else captions == list(labels)
            with override(source_window, props):
                bpy.ops.screen.screenshot(filepath=str(ART / f'properties-{locale}-{target}.png'))
            record('native-tab-object-and-isolation', target=target, locale=locale,
                   requestedScale=scale, actualScale=prefs.system.ui_scale, captions=captions)

    # Same-object pin survives. All other compatible targets unavailable cancels.
    props.spaces.active.pin_id = obj
    props.spaces.active.use_pin_id = True
    yield from settle()
    with override(source_window, viewport):
        assert bpy.ops.axismeld.object_transform_properties() == {'FINISHED'}
    assert props.spaces.active.pin_id == obj and props.spaces.active.use_pin_id
    props.spaces.active.pin_id = pin_obj
    yield from settle()
    with override(source_window, viewport):
        assert not property_navigation.available(bpy.context, 'OBJECT')[0]
        assert property_navigation.run(bpy.context, 'OBJECT') == {'CANCELLED'}
    record('same-object-pin-and-foreign-pin-cancellation')
    props.spaces.active.use_pin_id = False
    yield from settle()
    with override(source_window, props):
        assert bpy.context.object == pin_obj, identities()
    with override(source_window, viewport):
        assert property_navigation.run(bpy.context, 'OBJECT') == {'CANCELLED'}
    record('native-foreign-pin-root-with-flag-off', windows=identities())
    # Clear the native root, not just the UI flag, for later success cases.
    props.spaces.active.pin_id = None
    assert props.spaces.active.pin_id is None and not props.spaces.active.use_pin_id
    obj.select_set(False, view_layer=source_window.view_layer)
    with override(source_window, viewport):
        assert property_navigation.run(bpy.context, 'OBJECT') == {'CANCELLED'}
    obj.select_set(True, view_layer=source_window.view_layer)
    with override(source_window, viewport):
        # Removed source type must cancel even when another VIEW_3D exists.
        old_type = viewport.type
        viewport.type = 'TEXT_EDITOR'
        assert menubar_runtime.run(bpy.context, 'action', 'properties.modifier', token) == {'CANCELLED'}
        viewport.type = old_type
    yield from settle()
    record('empty-selection-and-stale-source-cancellation')

    for kind, data in (('EMPTY', None), ('CAMERA', bpy.data.cameras.new('PN Camera')),
                       ('LIGHT', bpy.data.lights.new('PN Light', 'POINT')),
                       ('ARMATURE', bpy.data.armatures.new('PN Armature'))):
        probe = bpy.data.objects.new('PN ' + kind, data)
        source_window.scene.collection.objects.link(probe)
        obj.select_set(False, view_layer=source_window.view_layer)
        probe.select_set(True, view_layer=source_window.view_layer)
        source_window.view_layer.objects.active = probe
        yield from settle()
        with override(source_window, viewport):
            assert property_navigation.available(bpy.context, 'MODIFIER')[0] == (kind == 'EMPTY'), kind
            if kind == 'EMPTY':
                assert property_navigation.run(bpy.context, 'MODIFIER') == {'FINISHED'}
        if kind == 'EMPTY':
            yield from settle()
            with override(source_window, props):
                assert bpy.context.object == probe, identities()
        record('native-type-eligibility', objectType=kind, modifierAvailable=(kind == 'EMPTY'))
        probe.select_set(False, view_layer=source_window.view_layer)
    obj.select_set(True, view_layer=source_window.view_layer)
    source_window.view_layer.objects.active = obj
    yield from settle()

    # Native editing/Undo, with no navigation undo entry between transform and Undo.
    # Push only the test fixture baseline: production navigation never pushes Undo.
    with override(source_window, viewport):
        bpy.ops.ed.undo_push(message='PN test baseline')
        initial_location = tuple(obj.location)
        assert bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(2.0, 0.0, 0.0)) == {'FINISHED'}
        assert tuple(obj.location) != initial_location
        assert bpy.ops.axismeld.modifier_properties() == {'FINISHED'}
        with override(source_window, props):
            assert bpy.context.object == obj, identities()
        assert bpy.ops.ed.undo() == {'FINISHED'}
    yield from settle()
    restored = bpy.data.objects['PN Source']
    assert tuple(restored.location) == initial_location
    assert state(other_window) == other_state
    assert pinned.spaces.active.pin_id.name == 'PN Unrelated Pin'
    record('native-transform-and-undo-after-navigation', restoredLocation=list(restored.location))
    RECORD['status'] = 'PASS'
    record('complete')


STEPS = main()


def tick():
    try:
        next(STEPS)
        return 0.15
    except StopIteration:
        print('AXISMELD_PROPERTY_NAVIGATION_GUI_PASS', json.dumps(RECORD), flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        RECORD['status'] = 'FAIL'
        RECORD['error'] = traceback.format_exc()
        RECORD['failureWindows'] = identities()
        record('failure')
        print(RECORD['error'], flush=True)
        bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(tick, first_interval=1.0)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real Skin Options keyboard access and unavailable Options mouse tooltip."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from axismeld_hotbox_image_fixture import observed_menu_rectangles

ART = Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False


def settle(count=6):
    for _ in range(count):
        yield


def suite():
    from axismeld import skin_weight_ops
    from bl_ui import space_axismeld_menubar as ui

    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    script_root = Path(bpy.utils.system_resource('SCRIPTS'))
    resources = [script_root / 'modules/axismeld/skin_weight_ops.py',
                 script_root / 'startup/bl_ui/space_axismeld_menubar.py']
    evidence = dict(phase='menu-options-access', exe=bpy.app.binary_path,
                    exe_sha256=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                    test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    resources={p.relative_to(script_root).as_posix():
                               hashlib.sha256(p.read_bytes()).hexdigest() for p in resources})
    (ART / 'test-source.py').write_bytes(Path(__file__).read_bytes())

    def save_evidence():
        (ART / 'capture-evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')

    save_evidence()

    def context():
        return bpy.context.temp_override(window=win, area=area, region=region)

    cursor = [600, 650]

    def event(kind, value='PRESS', point=None):
        if point is not None:
            cursor[:] = [int(v) for v in point]
        win.event_simulate(type=kind, value=value, x=cursor[0], y=cursor[1])

    def key(kind):
        event(kind)
        yield from settle(2)
        event(kind, 'RELEASE')
        yield from settle(2)

    def shot(tag):
        path = ART / (tag + '.png')
        with context():
            bpy.ops.screen.screenshot(filepath=str(path))
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            width, height = image.size
            return np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(image)

    class AXISMELD_MT_access_skin(bpy.types.Menu):
        bl_label = 'Skin Options Access'

        def draw(self, context):
            ui._draw_item(self.layout, context, dict(
                id='access.normalize', kind='skin_weight', label='Normalize Weights',
                icon='MOD_VERTEX_WEIGHT', skin_operation='NORMALIZE'))

    reason = 'Maya option parameters are not implemented'

    class AXISMELD_MT_access_unavailable(bpy.types.Menu):
        bl_label = 'Unavailable Options Access'

        def draw(self, context):
            self.layout.ui_units_x = 24
            ui._draw_item(self.layout, context, dict(
                id='access.cube', kind='command', command='mesh.create_cube', origin='maya',
                label='Create Cube', icon='MESH_CUBE', options={'reason': reason}))

    for cls in (AXISMELD_MT_access_skin, AXISMELD_MT_access_unavailable):
        bpy.utils.register_class(cls)
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    bpy.context.preferences.view.ui_scale = 1.0
    yield from settle(12)

    with context():
        bpy.ops.object.select_all(action='DESELECT')
        arm_data = bpy.data.armatures.new('OptionsAccessArmature')
        arm = bpy.data.objects.new('OptionsAccessArmature', arm_data)
        bpy.context.collection.objects.link(arm)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        for index, name in enumerate(('BoneA', 'BoneB')):
            bone = arm_data.edit_bones.new(name)
            bone.head, bone.tail = (index, 0, 0), (index, 0, 1)
        bpy.ops.object.mode_set(mode='OBJECT')
        arm.select_set(False)
        mesh = bpy.data.meshes.new('OptionsAccessMesh')
        mesh.from_pydata(((0, 0, 0), (1, 0, 0), (0, 1, 0)), (), ((0, 1, 2),))
        subject = bpy.data.objects.new('OptionsAccessSubject', mesh)
        bpy.context.collection.objects.link(subject)
        subject.modifiers.new('OptionsAccessSkin', 'ARMATURE').object = arm
        for name, weight in (('BoneA', .2), ('BoneB', .3)):
            subject.vertex_groups.new(name=name).add([0, 1, 2], weight, 'REPLACE')
        subject.select_set(True)
        bpy.context.view_layer.objects.active = subject
        bpy.context.view_layer.update()
        assert not skin_weight_ops.context_error(bpy.context)
        bpy.ops.ed.undo_push(message='Options access fixture')
    yield from settle(10)

    def snapshot():
        return dict(weights=[[(g.group, g.weight) for g in vertex.groups] for vertex in mesh.vertices],
                    selected=sorted(o.name for o in bpy.context.selected_objects),
                    active=bpy.context.view_layer.objects.active.name, mode=bpy.context.mode,
                    objects=sorted(o.name for o in bpy.data.objects))

    invoked = []
    original_invoke = skin_weight_ops.AXISMELD_OT_skin_normalize_weights.invoke

    def traced_invoke(self, context, event):
        options = self.show_options
        result = original_invoke(self, context, event)
        invoked.append(dict(show_options=options, result=sorted(result)))
        print('ACTUAL_SKIN_OPTIONS_INVOKE', json.dumps(invoked[-1]), flush=True)
        return result

    skin_weight_ops.AXISMELD_OT_skin_normalize_weights.invoke = traced_invoke
    initial = snapshot()
    shot('skin-before')
    event('MOUSEMOVE', 'NOTHING')
    with context():
        bpy.ops.wm.call_menu(name=AXISMELD_MT_access_skin.__name__)
    yield from settle(8)
    for name in ('HOME', 'DOWN_ARROW', 'RET'):
        yield from key(name)
    yield from settle(10)
    shot('skin-enabled-options-dialog')
    assert invoked == [dict(show_options=True, result=['RUNNING_MODAL'])], invoked
    assert snapshot() == initial, 'Opening the Options dialog executed Normalize Weights'
    yield from key('ESC')
    yield from settle(8)
    shot('skin-after-cancel')
    assert snapshot() == initial, 'Cancelling Options changed weights, selection or scene'
    evidence['skin_options'] = dict(invoked=invoked, before=initial, after_cancel=snapshot())
    save_evidence()

    described = []
    original_description = ui.AXISMELD_OT_menubar_execute.description

    @classmethod
    def traced_description(cls, context, properties):
        text = original_description(context, properties)
        described.append(text)
        return text

    ui.AXISMELD_OT_menubar_execute.description = traced_description
    event('MOUSEMOVE', 'NOTHING', (600, 650))
    yield from settle(4)
    baseline = shot('gray-before-menu')
    with context():
        bpy.ops.wm.call_menu(name=AXISMELD_MT_access_unavailable.__name__)
    yield from settle(10)
    menu_pixels = shot('gray-menu')
    scale = bpy.context.preferences.system.ui_scale
    changed = np.max(np.abs(menu_pixels[:, :, :3] - baseline[:, :, :3]), axis=2) > .004
    boxes = observed_menu_rectangles((np.max(menu_pixels[:, :, :3], axis=2) < .15) & changed,
                                    100 * scale, 10 * scale)
    assert len(boxes) == 1, ('Expected one actual one-row popup', boxes)
    popup = boxes[0]
    rgb = menu_pixels[:, :, :3]
    icon_mask = (np.min(rgb, axis=2) > .18) & (np.max(rgb, axis=2) < .5)
    allowed = np.zeros(icon_mask.shape, dtype=bool)
    x0, y0, x1, y1 = popup
    allowed[y0:y1, max(x0, int(x1 - 28 * scale)):x1] = True
    icons = [b for b in observed_menu_rectangles(icon_mask & allowed, 5 * scale, 5 * scale)
             if b[2] - b[0] < 20 * scale and b[3] - b[1] < 20 * scale]
    assert len(icons) == 1, ('Expected the actual trailing unavailable gear', popup, icons)
    gear = icons[0]
    center = ((gear[0] + gear[2]) / 2, (gear[1] + gear[3]) / 2)
    bpy.context.preferences.view.show_tooltips = True
    hover_descriptions = len(described)
    tooltip_pixels = None
    for attempt in range(2):
        # Native tooltip timing needs real motion, including a second movement
        # within 30 px. Re-enter from the body rather than assuming a stationary
        # cursor on a newly-created popup is sufficient to start its timer.
        event('MOUSEMOVE', 'NOTHING', (center[0] - 40 * scale, center[1]))
        yield from settle(4)
        event('MOUSEMOVE', 'NOTHING', (center[0] - 2 * scale, center[1]))
        yield from settle(4)
        event('MOUSEMOVE', 'NOTHING', (center[0] + 2 * scale, center[1]))
        yield from settle(45)
        tooltip_pixels = shot('gray-gear-tooltip-' + str(attempt + 1))
        if reason in described[hover_descriptions:]:
            break
    assert reason in described[hover_descriptions:], ('Gray gear did not request its reason tooltip', described)
    tooltip_changed = np.max(np.abs(tooltip_pixels[:, :, :3] - menu_pixels[:, :, :3]), axis=2) > .004
    # Exclude the original popup and its hover highlight. The screenshot must
    # contain newly-drawn pixels outside it, for visual confirmation by root.
    tooltip_changed[max(0, y0 - 5):y1 + 5, max(0, x0 - 5):x1 + 5] = False
    assert np.count_nonzero(tooltip_changed) > 100, 'Reason callback ran without a visible tooltip overlay'
    assert snapshot() == initial, 'Hovering the unavailable gear changed the scene'
    evidence['gray_options'] = dict(popup=popup, gear=gear, reason=reason,
                                    tooltip_descriptions=described[hover_descriptions:],
                                    overlay_pixels=int(np.count_nonzero(tooltip_changed)))
    save_evidence()
    yield from key('ESC')
    print('AXISMELD_MENU_OPTIONS_ACCESS_PASS', flush=True)


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


bpy.app.timers.register(tick, first_interval=1)

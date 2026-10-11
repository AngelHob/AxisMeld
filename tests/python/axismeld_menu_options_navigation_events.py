# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real menu key events: skip unavailable AxisMeld Options, retain native stops."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import bpy


ART = Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False


def settle(count=6):
    for _ in range(count):
        yield


def suite():
    from bl_ui import space_axismeld_menubar as ui

    win = bpy.context.window
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    script = Path(bpy.utils.system_resource('SCRIPTS')) / 'startup/bl_ui/space_axismeld_menubar.py'
    evidence = {
        'phase': 'menu-options-navigation',
        'exe': bpy.app.binary_path,
        'exe_sha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
        'menubar_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
        'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ART / 'capture-evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    (ART / 'test-source.py').write_bytes(Path(__file__).read_bytes())
    print('MENU_NAVIGATION_EVIDENCE', json.dumps(evidence), flush=True)

    executed = []
    original_run = ui.menubar_runtime.run

    def traced_run(*args):
        result = original_run(*args)
        executed.append((args[1], args[2], sorted(result)))
        print('ACTUAL_COMMAND_RUN', executed[-1], flush=True)
        return result

    ui.menubar_runtime.run = traced_run

    def context():
        return bpy.context.temp_override(window=win, area=area, region=region)

    def event(kind, value='PRESS'):
        win.event_simulate(type=kind, value=value, x=600, y=650)

    def key(kind):
        event(kind)
        yield from settle(2)
        event(kind, 'RELEASE')
        yield from settle(2)

    def shot(name):
        with context():
            bpy.ops.screen.screenshot(filepath=str(ART / (name + '.png')))

    def node(label, command, indicator=''):
        return dict(id='navigation.' + command, kind='command', command='mesh.create_' + command,
                    origin='maya', label=label, icon='MESH_CUBE', indicator=indicator,
                    options={'reason': 'Independent unavailable Options remain inspectable'})

    class AXISMELD_MT_navigation_rows(bpy.types.Menu):
        bl_label = 'Options Keyboard Navigation'

        def draw(self, context):
            column = self.layout.column()
            column.ui_units_x = 24
            ui._draw_item(column, context, node('First body', 'cube'))
            ui._draw_item(column, context, node('Second body with indicator', 'sphere', 'checkbox'))
            ui._draw_item(column, context, node('Last body', 'cylinder'))

    class AXISMELD_MT_navigation_disabled_body(bpy.types.Menu):
        bl_label = 'Unavailable Body Navigation'

        def draw(self, context):
            ui._draw_item(self.layout, context, node('First body', 'cube'))
            ui._draw_item(self.layout, context, dict(
                id='navigation.unavailable', kind='disabled', label='Unavailable body explanation',
                icon='ERROR', reason='This ordinary unavailable body must remain keyboard reachable'))
            ui._draw_item(self.layout, context, node('Last body', 'sphere'))

    skin_operation = ['NORMALIZE']

    class AXISMELD_MT_navigation_disabled_skin(bpy.types.Menu):
        bl_label = 'Unavailable Skin Options Navigation'

        def draw(self, context):
            ui._draw_item(self.layout, context, node('First body', 'cube'))
            ui._draw_item(self.layout, context, dict(
                id='navigation.skin', kind='skin_weight', label='Unavailable Skin body',
                icon='MOD_VERTEX_WEIGHT', skin_operation=skin_operation[0]))
            ui._draw_item(self.layout, context, node('Last body', 'sphere'))

    def wrapper(layout, context, command, text='', icon='PREFERENCES', enabled=True):
        cell = layout.row(align=True)
        cell.enabled = enabled
        op = cell.operator('axismeld.menubar_execute', text=text, icon=icon)
        op.kind = 'command'
        op.key = 'mesh.create_' + command
        op.token = ui.menubar_runtime.source_token(context)

    class AXISMELD_MT_navigation_enabled_options(bpy.types.Menu):
        bl_label = 'Enabled Options Navigation'

        def draw(self, context):
            row = self.layout.row(align=True)
            wrapper(row, context, 'cube', text='Body before enabled Options', icon='MESH_CUBE')
            wrapper(row, context, 'sphere')
            wrapper(self.layout, context, 'cylinder', text='Last body', icon='MESH_CUBE')

    class AXISMELD_MT_navigation_pure_icons(bpy.types.Menu):
        bl_label = 'Pure Icon Navigation'

        def draw(self, context):
            row = self.layout.row(align=True)
            wrapper(row, context, 'cube', icon='PLAY')
            wrapper(row, context, 'plane', enabled=False)
            wrapper(row, context, 'sphere', icon='PLAY')

    class AXISMELD_MT_navigation_native(bpy.types.Menu):
        bl_label = 'Native Blender Navigation Control'

        def draw(self, context):
            row = self.layout.row(align=True)
            for text, icon, enabled, value in (
                    ('Native body', 'MESH_CUBE', True, 101), ('', 'PREFERENCES', False, 102)):
                cell = row.row(align=True)
                cell.enabled = enabled
                op = cell.operator('wm.context_set_int', text=text, icon=icon)
                op.data_path, op.value = 'scene.frame_current', value
            op = self.layout.operator('wm.context_set_int', text='Native last body')
            op.data_path, op.value = 'scene.frame_current', 103

    class AXISMELD_MT_navigation_trailing_icon(bpy.types.Menu):
        bl_label = 'Pure Icon Trailing Gear'

        def draw(self, context):
            row = self.layout.row(align=True)
            wrapper(row, context, 'cube', icon='PLAY')
            wrapper(row, context, 'plane', enabled=False)
            wrapper(self.layout, context, 'sphere', text='Following row', icon='MESH_UVSPHERE')

    classes = (AXISMELD_MT_navigation_rows, AXISMELD_MT_navigation_disabled_body,
               AXISMELD_MT_navigation_disabled_skin,
               AXISMELD_MT_navigation_enabled_options, AXISMELD_MT_navigation_pure_icons,
               AXISMELD_MT_navigation_native, AXISMELD_MT_navigation_trailing_icon)
    for cls in classes:
        bpy.utils.register_class(cls)
    preset = next(Path(p) / 'AxisMeld_Maya_2026.py' for p in bpy.utils.preset_paths('keyconfig')
                  if (Path(p) / 'AxisMeld_Maya_2026.py').exists())
    assert bpy.utils.keyconfig_set(str(preset))
    yield from settle(12)
    with context():
        bpy.ops.ed.undo_push(message='Options keyboard navigation fixture')

    records = []

    def open_menu(cls):
        # Opening and all navigation use the real menu event path. No active
        # button or native layout internals are written by this regression.
        yield from key('ESC')
        event('MOUSEMOVE', 'NOTHING')
        yield from settle(2)
        with context():
            bpy.ops.wm.call_menu(name=cls.__name__)
        yield from settle(8)

    def run_case(cls, tag, keys, expected):
        yield from open_menu(cls)
        before = tuple(sorted(o.name for o in bpy.data.objects))
        first_call = len(executed)
        for name in keys:
            yield from key(name)
        shot(tag + '-selected')
        yield from key('RET')
        yield from settle(8)
        calls = executed[first_call:]
        record = dict(case=tag, keys=keys, expected=expected, calls=calls)
        records.append(record)
        (ART / 'navigation-results.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        print('ACTUAL_MENU_NAVIGATION', json.dumps(record), flush=True)
        if expected is None:
            assert not calls and tuple(sorted(o.name for o in bpy.data.objects)) == before, record
        else:
            assert calls == [('command', 'mesh.create_' + expected, ['FINISHED'])], record
            assert len(bpy.data.objects) == len(before) + 1, ('Command did not create its object', record)
            with context():
                bpy.ops.ed.undo()
            yield from settle(8)
            assert tuple(sorted(o.name for o in bpy.data.objects)) == before, ('Undo changed the fixture', tag)
        yield from key('ESC')

    # The first case is RED on the old binary: Down selects its unavailable
    # gear, so Enter runs no command instead of creating the second row sphere.
    for scale in (1.0, 1.5):
        bpy.context.preferences.view.ui_scale = scale
        yield from settle(10)
        for tag, keys, expected in (
                ('down', ('HOME', 'DOWN_ARROW'), 'sphere'),
                ('up', ('END', 'UP_ARROW'), 'sphere'),
                ('first', ('HOME',), 'cube'),
                ('last', ('END',), 'cylinder'),
                ('wrap-up', ('HOME', 'UP_ARROW'), 'cylinder'),
                ('wrap-down', ('END', 'DOWN_ARROW'), 'cube')):
            yield from run_case(AXISMELD_MT_navigation_rows, str(scale) + '-' + tag, keys, expected)
    for cls, tag, keys, expected in (
            (AXISMELD_MT_navigation_disabled_body, 'disabled-body-stop', ('HOME', 'DOWN_ARROW'), None),
            (AXISMELD_MT_navigation_disabled_body, 'after-disabled-body', ('HOME', 'DOWN_ARROW', 'DOWN_ARROW'), 'sphere'),
            (AXISMELD_MT_navigation_disabled_body, 'disabled-body-up-stop', ('END', 'UP_ARROW'), None),
            (AXISMELD_MT_navigation_enabled_options, 'enabled-options-down', ('HOME', 'DOWN_ARROW'), 'sphere'),
            (AXISMELD_MT_navigation_enabled_options, 'enabled-options-up', ('END', 'UP_ARROW'), 'sphere'),
            (AXISMELD_MT_navigation_pure_icons, 'pure-icon-stop', ('HOME', 'DOWN_ARROW'), None),
            (AXISMELD_MT_navigation_trailing_icon, 'pure-icon-trailing-stop', ('HOME', 'DOWN_ARROW'), None),
            (AXISMELD_MT_navigation_trailing_icon, 'after-pure-icon-trailing', ('HOME', 'DOWN_ARROW', 'DOWN_ARROW'), 'sphere'),
            (AXISMELD_MT_navigation_pure_icons, 'after-pure-icon', ('HOME', 'DOWN_ARROW', 'DOWN_ARROW'), 'sphere')):
        yield from run_case(cls, tag, keys, expected)

    from axismeld.skin_weight_ops import context_error
    with context():
        assert context_error(bpy.context), 'Skin fixture must be unavailable without an armature'
    for operation in ('NORMALIZE', 'PRUNE'):
        skin_operation[0] = operation
        for suffix, keys, expected in (
                ('body-stop', ('HOME', 'DOWN_ARROW'), None),
                ('after-body', ('HOME', 'DOWN_ARROW', 'DOWN_ARROW'), 'sphere'),
                ('body-up-stop', ('END', 'UP_ARROW'), None),
                ('before-body', ('END', 'UP_ARROW', 'UP_ARROW'), 'cube')):
            yield from run_case(AXISMELD_MT_navigation_disabled_skin,
                                'skin-' + operation.lower() + '-' + suffix, keys, expected)

    # Exact native operator control: its unavailable trailing gear retains the
    # original keyboard stop, and the following native row remains executable.
    for tag, keys, expected in (
            ('native-down-stop', ('HOME', 'DOWN_ARROW'), 1),
            ('native-up-stop', ('END', 'UP_ARROW'), 1),
            ('native-after-stop', ('HOME', 'DOWN_ARROW', 'DOWN_ARROW'), 103),
            ('native-first', ('HOME',), 101),
            ('native-last', ('END',), 103)):
        bpy.context.scene.frame_current = 1
        yield from open_menu(AXISMELD_MT_navigation_native)
        for name in keys:
            yield from key(name)
        shot(tag + '-selected')
        yield from key('RET')
        yield from settle(6)
        assert bpy.context.scene.frame_current == expected, (tag, keys, bpy.context.scene.frame_current)
        records.append(dict(case=tag, keys=keys, expected_frame=expected,
                            actual_frame=bpy.context.scene.frame_current))
    (ART / 'navigation-results.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    yield from key('ESC')
    print('AXISMELD_MENU_OPTIONS_NAVIGATION_PASS', flush=True)


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

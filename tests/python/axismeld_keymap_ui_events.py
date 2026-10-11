# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Installed-only Preferences keymap draw smoke; run in a disposable GUI process.

Set AXISMELD_TEST_ARTIFACTS and BLENDER_USER_CONFIG to disposable directories.
This forwards every observed layout call to the actual native Preferences UI.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import bpy
import rna_keymap_ui
from axismeld.commands import COMMANDS, PRESET_NAME
from axismeld.tool_hotbox import CURRENT_TOOL_HOTBOX


ARTIFACTS = Path(os.environ['AXISMELD_TEST_ARTIFACTS'])
ARTIFACTS.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
bpy.context.preferences.view.show_tooltips = False
bpy.context.preferences.view.language = 'en_US'
bpy.context.preferences.view.use_translate_interface = False


class NativeLayoutTrace:
    """Observe label text without replacing any production/native drawing."""

    def __init__(self, layout, labels):
        object.__setattr__(self, '_layout', layout)
        object.__setattr__(self, '_labels', labels)

    def __setattr__(self, name, value):
        setattr(self._layout, name, value)

    def __getattr__(self, name):
        value = getattr(self._layout, name)
        if name in {'row', 'column', 'split', 'box'}:
            return lambda *args, **kwargs: NativeLayoutTrace(value(*args, **kwargs), self._labels)
        if name == 'label':
            def label(*args, **kwargs):
                self._labels.append(kwargs.get('text', ''))
                return value(*args, **kwargs)
            return label
        return value


def settle(count=12):
    for _ in range(count):
        yield


def suite():
    bpy.utils.keyconfig_init()
    preset = next(Path(directory) / (PRESET_NAME + '.py')
                  for directory in bpy.utils.preset_paths('keyconfig')
                  if (Path(directory) / (PRESET_NAME + '.py')).is_file())
    assert bpy.utils.keyconfig_set(str(preset)), 'AxisMeld preset did not load'
    # The expanded event editor calls _wm_capabilities(), which needs a native
    # window; exercise it here instead of in the background RNA regression.
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps:
        for item in keymap.keymap_items:
            if item.idname == 'axismeld.command' and item.properties.command == 'transform.move':
                item.show_expanded = True
    window = bpy.context.window
    area = next(area for area in window.screen.areas if area.type == 'VIEW_3D')
    area.type = 'PREFERENCES'
    space = area.spaces.active
    bpy.context.preferences.active_section = 'KEYMAP'
    observed = {}
    original_draw = rna_keymap_ui.draw_kmi

    def traced_draw(display_keymaps, kc, km, kmi, layout, level):
        labels = []
        result = original_draw(display_keymaps, kc, km, kmi, NativeLayoutTrace(layout, labels), level)
        if bpy.context.area == area:
            observed.setdefault((space.filter_type, space.filter_text), []).append({
                'operator': kmi.idname,
                'command': getattr(kmi.properties, 'command', None),
                'expanded': kmi.show_expanded,
                'labels': labels,
            })
        return result

    rna_keymap_ui.draw_kmi = traced_draw
    cases = []
    try:
        for filter_type, query, required_command, screenshot in (
                ('NAME', 'Move Tool', 'transform.move', 'move-tool'),
                ('NAME', 'Rotate Tool', 'transform.rotate', 'rotate-tool'),
                ('NAME', 'axismeld.command', 'transform.move', 'operator-identifier'),
                ('KEY', 'ctrl shift rmb', CURRENT_TOOL_HOTBOX, 'key-binding')):
            space.filter_type = filter_type
            space.filter_text = query
            area.tag_redraw()
            yield from settle()
            rows = observed.get((filter_type, query), [])
            assert rows, f'No production Preferences keymap rows drawn for {filter_type}: {query}'
            matching = [row for row in rows if row['command'] == required_command]
            assert matching, f'Missing semantic binding {required_command}: {rows}'
            expected_label = COMMANDS[required_command].label
            assert all(expected_label in row['labels'] for row in matching), matching
            if query == 'Move Tool':
                assert all(row['expanded'] for row in matching), 'Expanded binding was not drawn'
            if filter_type == 'NAME' and query != 'axismeld.command':
                assert all(query in row['labels'] for row in rows), rows
            if query == 'axismeld.command':
                assert all('AxisMeld Workflow Command' not in row['labels'] for row in rows), rows
            path = ARTIFACTS / (screenshot + '.png')
            with bpy.context.temp_override(window=window):
                bpy.ops.screen.screenshot(filepath=str(path))
            cases.append({'type': filter_type, 'query': query, 'rows': rows, 'screenshot': str(path)})
            print('AXISMELD_KEYMAP_UI_GUI_CASE', filter_type, query, 'rows', len(rows), flush=True)
    finally:
        rna_keymap_ui.draw_kmi = original_draw

    module = Path(rna_keymap_ui.__file__).resolve()
    scripts = Path(bpy.utils.system_resource('SCRIPTS')).resolve()
    assert module.is_relative_to(scripts), f'Source-injected UI module is not allowed: {module}'
    evidence = {
        'binary': bpy.app.binary_path,
        'binary_sha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
        'module': str(module),
        'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
        'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'cases': cases,
        'verification': 'Production draw_kmi forwarded to native Preferences UILayout; screenshots saved',
    }
    (ARTIFACTS / 'keymap-ui-gui.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print('AXISMELD_KEYMAP_UI_GUI_PASS', flush=True)


steps = suite()


def tick():
    try:
        next(steps)
        return 0.05
    except StopIteration:
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    return None


bpy.app.timers.register(tick, first_interval=1.0)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Installed profile/preferences integration in a private Blender configuration."""
from pathlib import Path
import json
import os
import traceback

import bpy


def check(value, label):
    if not value:
        raise AssertionError(label)


def run():
    root = Path(os.environ['AXISMELD_TEST_ROOT']).resolve()
    check(Path(bpy.app.tempdir).resolve().is_relative_to(root), 'Blender temp escaped private root')
    bpy.context.preferences.use_preferences_save = False
    preset = next(Path(path) / 'AxisMeld_Maya_2026.py'
                  for path in bpy.utils.preset_paths('keyconfig')
                  if (Path(path) / 'AxisMeld_Maya_2026.py').exists())
    check(bpy.utils.keyconfig_set(str(preset)), 'failed to activate installed AxisMeld preset')

    from axismeld import hotbox_runtime, runtime
    baseline = json.loads(hotbox_runtime.snapshot(bpy.context))
    check(baseline['settings']['transparency'] == 75 and
          bpy.context.window_manager.keyconfigs.active.preferences.hotbox_transparency == '75',
          'fresh installed profile and preferences must start at 75 percent transparency')
    directory = runtime.profile_directory()
    check(directory.resolve().is_relative_to(root), 'profile directory escaped private root')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'user.json').write_text(json.dumps({
        'schema_version': 1, 'bindings': {'transform.move': {'type': 'T'}}}), encoding='utf-8')
    (directory / 'hotbox_studio.json').write_text(json.dumps({
        'schema_version': 1, 'settings': {'style': 'zones', 'transparency': 50}}), encoding='utf-8')
    (directory / 'hotbox_user.json').write_text(json.dumps({
        'schema_version': 1, 'settings': {'transparency': 25}}), encoding='utf-8')
    config = runtime.load()
    move = next(item.type for item in config.keymaps['Mesh'].keymap_items
                if item.idname == 'axismeld.command' and item.properties.command == 'transform.move')
    first = json.loads(hotbox_runtime.snapshot(bpy.context))
    check(move == 'T', 'schema-1 keybinding edit was not preserved')
    check(first['settings']['style'] == 'zones' and first['settings']['transparency'] == 25,
          'installed hotbox layers did not resolve')
    check(config.preferences.hotbox_style == 'zones' and
          config.preferences.hotbox_transparency == '25', 'preferences did not show effective settings')

    # The native Controls operator and preference callback share one persisted mutation path.
    hotbox_runtime.reload_settings(bpy.context, session={
        'schema_version': 1, 'settings': {'style': 'center'}})
    check(bpy.ops.axismeld.hotbox_setting(setting='center.RIGHTMOUSE', value='pane.shading') ==
          {'FINISHED'}, 'Controls setting failed')
    user = json.loads((directory / 'hotbox_user.json').read_text(encoding='utf-8'))
    check(user == {'schema_version': 1, 'settings': {
        'center_buttons': {'RIGHTMOUSE': 'pane.shading'}, 'transparency': 25}},
        f'one persisted setting leaked another session field: {user!r}')
    config.preferences.hotbox_style = 'center'
    user = json.loads((directory / 'hotbox_user.json').read_text(encoding='utf-8'))
    check(user['settings']['style'] == 'center', 'preference did not use Controls mutation path')

    # Invalid reload rolls back that whole layer. A later Controls write must preserve it byte-for-byte.
    invalid = '{"schema_version":1,"settings":{"style":"bad"}}'
    (directory / 'hotbox_user.json').write_text(invalid, encoding='utf-8')
    runtime.load()
    rolled = json.loads(hotbox_runtime.snapshot(bpy.context))
    check(rolled['settings']['style'] == 'zones' and rolled['settings']['transparency'] == 50,
          'invalid user layer did not roll back atomically')
    check(any('hotbox user:' in message for message in runtime.diagnostics),
          'invalid hotbox layer diagnostic missing')
    check(bpy.ops.axismeld.hotbox_setting(setting='style', value='rows') == {'CANCELLED'},
          'malformed user layer was overwritten')
    check((directory / 'hotbox_user.json').read_text(encoding='utf-8') == invalid,
          'malformed user layer changed')

    # Disabled files are ignored; Controls remains a session-only override and explains that state.
    config = bpy.context.window_manager.keyconfigs.active
    config.preferences.use_file_overrides = False
    before = (directory / 'hotbox_user.json').read_text(encoding='utf-8')
    check(bpy.ops.axismeld.hotbox_setting(setting='transparency', value='100') == {'FINISHED'},
          'session-only Controls mutation failed')
    current = json.loads(hotbox_runtime.snapshot(bpy.context))
    check(current['settings']['transparency'] == 100, 'session-only override not applied')
    check((directory / 'hotbox_user.json').read_text(encoding='utf-8') == before,
          'disabled file overrides still wrote disk')
    check(hotbox_runtime.settings_storage_note(bpy.context).startswith('Session only'),
          'disabled-file UI explanation missing')

    # Session validation is independent of current scene and generations advance after reload.
    generation = current['generation']
    hotbox_runtime.reload_settings(bpy.context, session={
        'schema_version': 1, 'settings': {'style': 'rows',
                                         'center_buttons': {'LEFTMOUSE': None}}})
    second = json.loads(hotbox_runtime.snapshot(bpy.context))
    check(second['generation'] > generation and second['settings']['style'] == 'rows' and
          second['settings']['center_buttons']['LEFTMOUSE'] is None,
          'next snapshot did not use reloaded generation/settings')
    print('AXISMELD_HOTBOX_PROFILES_PASS', flush=True)
    bpy.ops.wm.quit_blender()


try:
    run()
except BaseException:
    traceback.print_exc()
    raise

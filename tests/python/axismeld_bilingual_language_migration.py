# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify real saved language preferences with isolated background Blender runs.

The audit runner seeds old preferences with the published 18px package, then
starts the new candidate normally. This test refuses non-isolated config paths.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

import bpy


WORKSPACES = {
    'Layout', 'Modeling', 'Sculpting', 'UV Editing', 'Texture Paint', 'Shading',
    'Animation', 'Rendering', 'Compositing', 'Geometry Nodes', 'Scripting', 'Rigging',
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def isolated_config(profile):
    profile = Path(profile).resolve()
    assert (profile / '.migration-test-profile').is_file(), 'Missing isolation marker'
    configured = os.environ.get('BLENDER_USER_CONFIG')
    assert configured, 'BLENDER_USER_CONFIG must be explicit'
    config = Path(configured).resolve()
    assert config == profile / 'config', (config, profile)
    actual = Path(bpy.utils.user_resource('CONFIG')).resolve()
    assert actual == config, ('Blender config isolation failed', actual, config)
    return config


def language_state():
    view = bpy.context.preferences.view
    return {
        'preference': view.language,
        'locale': bpy.app.translations.locale,
        'locales': list(bpy.app.translations.locales),
        'interface': view.use_translate_interface,
        'tooltips': view.use_translate_tooltips,
        'newDataNames': view.use_translate_new_dataname,
        'workspaces': sorted(bpy.data.workspaces.keys()),
    }


def check_language(expected):
    state = language_state()
    assert set(state['locales']) == {'en_US', 'zh_HANS'} and len(state['locales']) == 2, state
    assert state['preference'] == expected, ('Saved preference migration failed', expected, state)
    assert state['locale'] == expected, ('Effective locale differs from preference', expected, state)
    assert state['interface'] and state['tooltips'], state
    return state


def check_workspaces_and_modeling():
    from bl_ui import space_axismeld_menubar
    from axismeld.workspace_menu_catalog import build_workspace_menubar

    names = set(bpy.data.workspaces.keys())
    assert names == WORKSPACES, ('Workspace datablock names were changed', sorted(names))
    window = bpy.context.window
    assert window is not None, 'Background startup window is needed for real context checks'
    original = window.workspace
    keyconfigs = bpy.context.window_manager.keyconfigs
    original_keyconfig = keyconfigs.active
    modeling = bpy.data.workspaces['Modeling']
    try:
        # The normal factory default remains Blender. Opt into the installed
        # preset exactly as a user would, then restore it before saving any prefs.
        if original_keyconfig.name != 'AxisMeld_Maya_2026':
            preset = next(Path(path) / 'AxisMeld_Maya_2026.py'
                          for path in bpy.utils.preset_paths('keyconfig')
                          if (Path(path) / 'AxisMeld_Maya_2026.py').is_file())
            assert bpy.utils.keyconfig_set(str(preset))
        # Window.workspace posts a notifier: background execution does not run
        # the GUI event loop that commits it. Exercise the production predicate
        # with the real Modeling datablock and a valid current viewport instead
        # of claiming that an asynchronous GUI workspace switch completed.
        area = next(area for area in window.screen.areas if area.type == 'VIEW_3D')
        region = next(region for region in area.regions if region.type == 'WINDOW')
        # Keep the existing window implicit. Explicitly setting it would clear
        # the Python workspace override (CTX_wm_window_set clears nested keys).
        with bpy.context.temp_override(workspace=modeling, area=area, region=region):
            assert bpy.context.workspace == modeling, 'Real Modeling context override was lost'
            assert space_axismeld_menubar.enabled(bpy.context), 'AxisMeld keyconfig must be active'
            assert space_axismeld_menubar.modeling_workspace(bpy.context), 'Modeling routing was lost'
            assert not space_axismeld_menubar.rigging_workspace(bpy.context)
            context_check = {
                'executionMode': 'background' if bpy.app.background else 'gui',
                'observation': 'real-workspace-datablock-context-override',
                'contextWorkspace': bpy.context.workspace.name,
                'windowWorkspace': window.workspace.name,
                'screen': window.screen.name,
                'areaType': bpy.context.area.type,
                'regionType': bpy.context.region.type,
                'mode': bpy.context.mode,
                'guiWorkspaceSwitchVerified': False,
            }
        catalog = build_workspace_menubar()
        roots = tuple(catalog['modeling_roots'])
        assert len(roots) == 7 and len(set(roots)) == 7, roots
        observed_keyconfig = keyconfigs.active.name
    finally:
        keyconfigs.active = original_keyconfig
    assert window.workspace == original, 'Background predicate check changed the active workspace'
    assert bpy.context.workspace == original, 'Workspace context override was not restored'
    assert keyconfigs.active == original_keyconfig, 'Opt-in keyconfig was not restored'
    assert set(bpy.data.workspaces.keys()) == names, 'Predicate check renamed workspace data'
    return {'names': sorted(names), 'modelingDetected': True,
            'modelingRoots': list(roots), 'keyconfig': observed_keyconfig,
            'originalKeyconfig': original_keyconfig.name, 'optInRestored': True,
            'contextCheck': context_check}


def main(args, report):
    config = isolated_config(args.profile)
    prefs = bpy.context.preferences
    prefs.use_preferences_save = False
    report['initial'] = language_state()
    if args.mode == 'seed':
        assert args.requested in bpy.app.translations.locales or args.requested == 'DEFAULT'
        prefs.view.language = args.requested
        prefs.view.use_translate_interface = True
        prefs.view.use_translate_tooltips = True
        prefs.view.use_translate_new_dataname = True
        assert prefs.view.language == args.requested
        assert bpy.ops.wm.save_userpref() == {'FINISHED'}
        preference_file = config / 'userpref.blend'
        assert preference_file.is_file()
        report.update(status='BASELINE_SEEDED', observed=language_state(),
                      preferenceFile=str(preference_file), preferenceSha256=sha256(preference_file))
        return

    report['migrated'] = check_language(args.expected)
    report['workspaceCheck'] = check_workspaces_and_modeling()
    if args.mode == 'save_zh':
        prefs.view.language = 'zh_HANS'
        prefs.view.use_translate_new_dataname = True
        assert bpy.ops.wm.save_userpref() == {'FINISHED'}
        report['saved'] = check_language('zh_HANS')
        preference_file = config / 'userpref.blend'
        report['preferenceSha256'] = sha256(preference_file)
    if args.factory_reset:
        before = language_state()
        # Load the real factory startup while retaining the saved preferences.
        # read_factory_settings resets preferences and has no use_userpref flag
        # in Blender 5.4; the retained-language API is read_homefile instead.
        assert bpy.ops.wm.read_homefile(use_factory_startup=True) == {'FINISHED'}
        after = check_language(args.expected)
        assert before['newDataNames'] and after['newDataNames'], 'Factory test needs data-name translation enabled'
        report['factoryReset'] = {
            'before': before, 'after': after, 'workspaceCheck': check_workspaces_and_modeling(),
            'retainedLanguage': True, 'datablockNamesPreserved': True,
            'operator': 'wm.read_homefile', 'parameters': {'use_factory_startup': True},
            'factoryStartupReloaded': True, 'preferencesReset': False,
        }
    report['status'] = 'PASS'


def entrypoint():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('seed', 'verify', 'save_zh'), required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--requested', default='en_US')
    parser.add_argument('--expected', choices=('en_US', 'zh_HANS'), default='en_US')
    parser.add_argument('--factory-reset', action='store_true',
                        help='Reload factory startup with saved preferences retained; does not reset preferences')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    report = {'schemaVersion': 1, 'status': 'RUNNING', 'mode': args.mode,
              'requested': args.requested, 'expected': args.expected,
              'binary': bpy.app.binary_path, 'version': bpy.app.version_string,
              'startedAt': datetime.now(timezone.utc).isoformat()}
    try:
        main(args, report)
    except Exception as error:
        report.update(status='FAIL', errorType=type(error).__name__, error=str(error))
        raise
    finally:
        report['finishedAt'] = datetime.now(timezone.utc).isoformat()
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('AXISMELD_LANGUAGE_MIGRATION', json.dumps(report, ensure_ascii=False), flush=True)


entrypoint()

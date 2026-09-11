# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure session-history behavior; live dispatch/settings are covered by release suite."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_runtime


class RecentCommandsTest(unittest.TestCase):
    def test_empty_recent_is_disabled_then_populated_menu_is_enabled_and_mappable(self):
        old_recent = hotbox_runtime.recent
        try:
            hotbox_runtime.recent = hotbox_runtime.RecentCommands()
            settings = hotbox_runtime.make_snapshot(generation=1)['settings']
            settings['center_buttons']['RIGHTMOUSE'] = 'center.recent'
            empty = hotbox_runtime.make_snapshot(generation=2, settings=settings)
            hotbox_runtime.serialize_snapshot(empty)  # Strict validation retains menu identity.
            menu = next(child for child in empty['menus'][2]['children']
                        if child['id'] == 'center.recent')
            self.assertEqual(menu['kind'], 'menu')
            self.assertFalse(menu['enabled'])
            self.assertTrue(menu['reason'])
            self.assertEqual(menu['children'], [])
            hotbox_runtime.recent.record('view.front')
            populated = hotbox_runtime.make_snapshot(generation=3, settings=settings)
            hotbox_runtime.serialize_snapshot(populated)
            menu = next(child for child in populated['menus'][2]['children']
                        if child['id'] == 'center.recent')
            self.assertTrue(menu['enabled'])
            self.assertEqual(menu['reason'], '')
            self.assertEqual([(child['command'], child['label']) for child in menu['children']],
                             [('view.front', 'Front View')])
            self.assertFalse(empty['menus'][2]['children'][0]['enabled'])
        finally:
            hotbox_runtime.recent = old_recent

    def test_session_history_is_newest_first_unique_and_copy_safe(self):
        self.assertTrue(hasattr(hotbox_runtime, 'RecentCommands'), 'session history is missing')
        recent = hotbox_runtime.RecentCommands()
        recent.record('view.front')
        recent.record('view.top')
        recent.record('view.front')
        self.assertEqual(recent.items(), ('view.front', 'view.top'))
        self.assertEqual(hotbox_runtime.RecentCommands().items(), ())

    def test_only_supported_replayable_semantics_can_enter_history(self):
        self.assertTrue(hasattr(hotbox_runtime, 'RecentCommands'), 'session history is missing')
        recent = hotbox_runtime.RecentCommands()
        for command in ('hotbox.open', 'style', 'wm.open_mainfile', 'view.orbit',
                        'view.pan', 'tool.select', '', '../private/file.blend', None):
            recent.record(command)
        self.assertEqual(recent.items(), ())
        recent.record('transform.move')
        self.assertEqual(recent.items(), ('transform.move',))

    def test_ten_item_limit_discards_oldest_and_replaying_promotes(self):
        self.assertTrue(hasattr(hotbox_runtime, 'RecentCommands'), 'session history is missing')
        recent = hotbox_runtime.RecentCommands()
        commands = ('view.perspective', 'view.side', 'view.bottom', 'view.front',
                    'view.back', 'view.top', 'view.left', 'view.focus_selected',
                    'view.frame_all', 'view.wireframe', 'view.shaded')
        for command in commands:
            recent.record(command)
        self.assertEqual(recent.items(), tuple(reversed(commands[1:])))
        recent.record('view.front')
        self.assertEqual(recent.items()[0], 'view.front')
        self.assertEqual(len(recent.items()), 10)

    def test_snapshot_exposes_only_session_history_as_replayable_leaf_commands(self):
        old_recent = hotbox_runtime.recent
        try:
            hotbox_runtime.recent = hotbox_runtime.RecentCommands()
            hotbox_runtime.recent.record('view.front')
            hotbox_runtime.recent.record('transform.move')
            value = hotbox_runtime.make_snapshot(generation=1)
            recent = next(child for child in value['menus'][2]['children']
                          if child['id'] == 'center.recent')
            self.assertEqual(recent['kind'], 'menu')
            self.assertEqual([(node['command'], node['label']) for node in recent['children']], [
                ('transform.move', 'Move Tool'), ('view.front', 'Front View')])
            self.assertEqual(len({node['id'] for node in recent['children']}), 2)
        finally:
            hotbox_runtime.recent = old_recent


class SessionSettingsTest(unittest.TestCase):
    @staticmethod
    def context(use_file_overrides=False):
        preferences = SimpleNamespace(use_file_overrides=use_file_overrides)
        config = SimpleNamespace(preferences=preferences)
        keyconfigs = SimpleNamespace(get=lambda name: config)
        return SimpleNamespace(window_manager=SimpleNamespace(keyconfigs=keyconfigs))

    def tearDown(self):
        hotbox_runtime.reload_settings(self.context(), session={
            'schema_version': 1, 'settings': {}})

    def test_normal_reload_preserves_session_controls_and_explicit_empty_clears(self):
        context = self.context()
        hotbox_runtime.reload_settings(context, session={
            'schema_version': 1, 'settings': {'style': 'zones'}})
        hotbox_runtime.apply_setting(context, 'transparency', '25')
        hotbox_runtime.reload_settings(context)
        self.assertEqual(hotbox_runtime.current_settings()['style'], 'zones')
        self.assertEqual(hotbox_runtime.current_settings()['transparency'], 25)
        hotbox_runtime.reload_settings(context, session={
            'schema_version': 1, 'settings': {}})
        self.assertEqual(hotbox_runtime.current_settings()['style'], 'rows')
        self.assertEqual(hotbox_runtime.current_settings()['transparency'], 75)

    def test_invalid_explicit_session_keeps_previous_valid_layer(self):
        context = self.context()
        hotbox_runtime.reload_settings(context, session={
            'schema_version': 1, 'settings': {'center_buttons': {'RIGHTMOUSE': 'pane.shading'}}})
        hotbox_runtime.reload_settings(context, session={
            'schema_version': 1, 'settings': {'center_buttons': {'RIGHTMOUSE': 'missing.menu'}}})
        self.assertEqual(hotbox_runtime.current_settings()['center_buttons']['RIGHTMOUSE'],
                         'pane.shading')
        self.assertTrue(any('session:' in message for message in hotbox_runtime.diagnostics))


if __name__ == '__main__':
    unittest.main()

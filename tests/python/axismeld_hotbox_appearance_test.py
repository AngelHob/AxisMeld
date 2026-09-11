# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Appearance is a partial, strictly validated, independently resettable profile layer."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_profiles as profiles, hotbox_runtime as runtime
import axismeld_hotbox_runtime_test as session_tests


def layer(**settings):
    return {'schema_version': 1, 'settings': settings}


def context(use_file_overrides=False):
    return session_tests.SessionSettingsTest.context(use_file_overrides)


class AppearanceTest(unittest.TestCase):
    def tearDown(self):
        runtime.reload_settings(context(), session=layer())

    def test_legacy_files_gain_defaults_without_rewrite(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'hotbox_user.json'
            original = '{"schema_version":1,"settings":{"transparency":50}}'
            path.write_text(original, encoding='utf-8')
            value, errors = profiles.load_hotbox_profiles(root)
            self.assertEqual(errors, [])
            self.assertEqual(value['settings']['appearance'], {
                'theme_background': True, 'background': [64, 64, 64], 'brightness': -13,
                'text': [160, 160, 160], 'placeholder': [0, 0, 0],
                'theme_hover_text': True, 'hover_text': [255, 255, 255]})
            self.assertEqual(value['settings']['transparency'], 50)
            self.assertEqual(path.read_text(encoding='utf-8'), original)

    def test_nested_layers_merge_and_persist_only_changed_appearance_fields(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / 'hotbox_studio.json').write_text(json.dumps(layer(
                appearance={'text': [90, 100, 110]}, style='zones')), encoding='utf-8')
            value, errors = profiles.load_hotbox_profiles(root, session=layer(
                appearance={'brightness': -30}))
            self.assertEqual(errors, [])
            self.assertEqual(value['settings']['appearance']['text'], [90, 100, 110])
            saved = profiles.save_hotbox_user(root, value['settings'])
            self.assertEqual(saved, layer(appearance={'brightness': -30}))
            self.assertEqual(profiles.load_hotbox_profiles(root)[0], value)

    def test_bad_appearance_rolls_back_entire_layer(self):
        base, _ = profiles.resolve_hotbox([('studio', layer(appearance={'brightness': -20}))])
        for bad in ({'text': [0, 0]}, {'text': [True, 0, 0]}, {'text': [256, 0, 0]},
                    {'text': [0.5, 0, 0]}, {'text': 'red'}, {'brightness': True},
                    {'brightness': -129}, {'brightness': float('nan')},
                    {'theme_background': 1}, {'unknown': 1}):
            with self.subTest(bad=bad):
                value, errors = profiles.resolve_hotbox([
                    ('studio', layer(appearance={'brightness': -20})),
                    ('user', layer(style='center', appearance=bad))])
                self.assertTrue(errors)
                self.assertEqual(value, base)

    def test_session_changes_survive_reload_and_reset_does_not_touch_behavior(self):
        ctx = context()
        runtime.reload_settings(ctx, session=layer(style='zones', transparency=75,
            center_buttons={'RIGHTMOUSE': 'pane.shading'}))
        runtime.apply_appearance(ctx, 'text', [20, 40, 60])
        runtime.apply_appearance(ctx, 'brightness', -40)
        runtime.reload_settings(ctx)
        self.assertEqual(runtime.current_settings()['appearance']['text'], [20, 40, 60])
        runtime.reset_appearance(ctx)
        value = runtime.current_settings()
        self.assertEqual(value['style'], 'zones')
        self.assertEqual(value['center_buttons']['RIGHTMOUSE'], 'pane.shading')
        self.assertEqual(value['transparency'], 25)
        self.assertEqual(value['appearance']['brightness'], -13)
        self.assertEqual(value['appearance']['text'], [160, 160, 160])
        before = deepcopy(value)
        with self.assertRaises(ValueError):
            runtime.apply_appearance(ctx, 'text', [999, 0, 0])
        self.assertEqual(runtime.current_settings(), before)

    def test_file_save_does_not_leak_other_session_appearance_and_reset_preserves_files(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(sys.modules, {
                'axismeld.runtime': SimpleNamespace(profile_directory=lambda: Path(root))}):
            path = Path(root) / 'hotbox_user.json'
            path.write_text(json.dumps(layer(style='zones', transparency=75,
                center_buttons={'RIGHTMOUSE': 'pane.shading'})), encoding='utf-8')
            ctx = context(True)
            runtime.reload_settings(ctx, session=layer(appearance={'brightness': 50}))
            runtime.apply_appearance(ctx, 'text', [20, 40, 60])
            self.assertEqual(json.loads(path.read_text())['settings']['appearance'],
                             {'text': [20, 40, 60]})
            self.assertEqual(runtime.current_settings()['appearance']['brightness'], 50)
            runtime.reset_appearance(ctx)
            saved = json.loads(path.read_text())
            self.assertEqual(saved, layer(style='zones', center_buttons={'RIGHTMOUSE': 'pane.shading'}))
            self.assertEqual(runtime.current_settings()['appearance']['brightness'], -13)

    def test_invalid_file_prevents_reset_or_edit_without_partial_session_changes(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(sys.modules, {
                'axismeld.runtime': SimpleNamespace(profile_directory=lambda: Path(root))}):
            path = Path(root) / 'hotbox_user.json'
            original = '{"schema_version":1,"settings":{"appearance":{"text":"red"}}}'
            path.write_text(original, encoding='utf-8')
            ctx = context(True)
            runtime.reload_settings(ctx, session=layer(appearance={'brightness': 50}))
            before = runtime.current_settings()
            for change in (lambda: runtime.reset_appearance(ctx),
                           lambda: runtime.apply_appearance(ctx, 'brightness', -25)):
                with self.assertRaises(ValueError):
                    change()
                self.assertEqual(runtime.current_settings(), before)
                self.assertEqual(path.read_text(encoding='utf-8'), original)


if __name__ == '__main__':
    unittest.main()

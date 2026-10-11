# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Real-RNA keymap naming/filter regression, run with Blender --background.

By default this tests the installed modules. AXISMELD_KEYMAP_UI_SOURCE may point
at a source rna_keymap_ui.py for a focused pre-install RED/GREEN probe.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bpy
import rna_keymap_ui as keymap_ui
from axismeld.commands import COMMANDS


if source := os.environ.get('AXISMELD_KEYMAP_UI_SOURCE'):
    spec = importlib.util.spec_from_file_location('axismeld_keymap_ui_subject', source)
    keymap_ui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(keymap_ui)


class RecordingLayout:
    """Record drawing calls while keeping the real KeyMap/KeyMapItem RNA."""

    def __init__(self, calls=None):
        self.calls = [] if calls is None else calls

    def __getattr__(self, method):
        def call(*args, **kwargs):
            self.calls.append((method, args, kwargs))
            if method in {'row', 'column', 'split', 'box'}:
                return RecordingLayout(self.calls)
            if method == 'operator':
                return SimpleNamespace()
        return call

    def labels(self):
        return [kwargs.get('text', '') for method, _args, kwargs in self.calls if method == 'label']


class UnreadableProperties:
    """Simulate an invalidated RNA properties pointer on an otherwise live item."""

    def __init__(self, item, error):
        self.item = item
        self.error = error

    def __getattr__(self, name):
        if name == 'properties':
            raise self.error('RNA properties unavailable')
        return getattr(self.item, name)


class KeymapUILabelTests(unittest.TestCase):
    def setUp(self):
        bpy.context.preferences.use_preferences_save = False
        self.keyconfigs = bpy.context.window_manager.keyconfigs
        self.config = self.keyconfigs.new('AxisMeld Keymap UI Test')
        self.keymap = self.config.keymaps.new('AxisMeld Keymap UI Test', space_type='VIEW_3D')
        area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        region = next(region for region in area.regions if region.type == 'WINDOW')
        self.override = bpy.context.temp_override(area=area, region=region)
        self.override.__enter__()

    def tearDown(self):
        self.override.__exit__(None, None, None)
        self.keyconfigs.remove(self.config)

    def item(self, command=None, operator='axismeld.command', key='W', **kwargs):
        item = self.keymap.keymap_items.new(operator, key, 'PRESS', **kwargs)
        if command is not None:
            item.properties.command = command
        return item

    def draw(self, item):
        layout = RecordingLayout()
        keymap_ui.draw_kmi([(self.keymap, self.config)], self.config, self.keymap, item, layout, 0)
        return layout

    def filtered(self, text, filter_type='NAME'):
        layout = RecordingLayout()
        result = keymap_ui.draw_filtered([(self.keymap, self.config)], filter_type, text.lower(), layout)
        # Production draw_kmi emits an 'active' property for each selected item.
        selected = [args[0] for method, args, _kwargs in layout.calls
                    if method == 'prop' and args[1] == 'active']
        return result, selected, layout

    def test_semantic_commands_draw_the_central_label(self):
        item = self.item()
        self.assertEqual(item.name, 'AxisMeld Workflow Command')
        for command in COMMANDS.values():
            with self.subTest(command=command.id):
                item.properties.command = command.id
                self.assertIn(command.label, self.draw(item).labels())

    def test_name_filter_selects_only_the_matching_action(self):
        move = self.item('transform.move')
        self.item('transform.rotate', key='E')
        result, selected, layout = self.filtered('move tool')
        self.assertTrue(result)
        self.assertEqual(selected, [move])
        self.assertIn('Move Tool', layout.labels())

    def test_name_filter_keeps_operator_identifier_and_generic_name(self):
        move = self.item('transform.move')
        rotate = self.item('transform.rotate', key='E')
        for query in ('axismeld.command', 'axismeld workflow command'):
            with self.subTest(query=query):
                self.assertEqual(self.filtered(query)[1], [move, rotate])

    def test_translated_semantic_label_is_searchable(self):
        move = self.item('transform.move')
        original_iface = keymap_ui.iface_
        with patch.object(keymap_ui, 'iface_', side_effect=lambda label, *args:
                          '移动工具' if label == 'Move Tool' else original_iface(label, *args)):
            self.assertEqual(self.filtered('移动工具')[1], [move])
            self.assertEqual(self.filtered('move tool')[1], [move])

    def test_native_name_and_search_remain_available(self):
        native = self.item(operator='wm.search_menu')
        self.assertIn(native.name, self.draw(native).labels())
        self.assertEqual(self.filtered(native.name)[1], [native])
        self.assertEqual(self.filtered('wm.search_menu')[1], [native])

    def test_unknown_and_unset_semantics_keep_operator_name(self):
        for command in (None, '', 'removed.command'):
            with self.subTest(command=command):
                item = self.item(command)
                self.assertIn(item.name, self.draw(item).labels())
                self.assertIn(item, self.filtered(item.name)[1])

    def test_missing_or_invalidated_properties_keep_operator_name(self):
        item = self.item('transform.move')
        for error in (AttributeError, ReferenceError):
            with self.subTest(error=error):
                self.assertIn(item.name, self.draw(UnreadableProperties(item, error)).labels())

    def test_unknown_operator_keeps_existing_name_fallback(self):
        item = self.item(operator='axismeld.deleted_operator')
        expected = (item.name if keymap_ui._is_operator_available(item.idname) else
                    'axismeld.deleted_operator (unavailable)')
        self.assertIn(expected, self.draw(item).labels())
        self.assertEqual(self.filtered('axismeld.deleted_operator')[1], [item])

    def test_key_filter_keeps_modifier_event_and_alias_behavior(self):
        move = self.item('transform.move', ctrl=True)
        self.item('transform.rotate', key='E')
        mouse = self.item('transform.scale', key='RIGHTMOUSE', shift=True)
        for query, expected in (('ctrl w', [move]), ('press w', [move]),
                                ('shift rmb', [mouse]), ('release w', [])):
            with self.subTest(query=query):
                self.assertEqual(self.filtered(query, 'KEY')[1], expected)
        self.assertFalse(self.filtered('nonexistent_key_event', 'KEY')[0])


if __name__ == '__main__':
    print('AXISMELD_KEYMAP_UI_MODULE', keymap_ui.__file__, flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(KeymapUILabelTests))
    output = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  module=keymap_ui.__file__, binary=bpy.app.binary_path,
                  module_sha256=hashlib.sha256(Path(keymap_ui.__file__).read_bytes()).hexdigest(),
                  binary_sha256=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                  semantic_commands=len(COMMANDS),
                  layout='recorded production draw calls', rna='real Blender KeyMapItem')
    if artifacts := os.environ.get('AXISMELD_TEST_ARTIFACTS'):
        directory = Path(artifacts)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'keymap-ui-rna.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print('AXISMELD_KEYMAP_UI_RNA', json.dumps(output), flush=True)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('AXISMELD_KEYMAP_UI_RNA_PASS', flush=True)

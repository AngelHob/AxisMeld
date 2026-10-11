# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Source diagnostics on real RNA keymaps; use a separate factory-startup process."""
import importlib.util
import json
from pathlib import Path
import unittest

import bpy

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('input_audit', ROOT / 'tools/utils/axismeld_input_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class InputDiagnosticsRNA(unittest.TestCase):
    def setUp(self):
        self.config = bpy.context.window_manager.keyconfigs.new('AxisMeldInputDiagnosticsTest')

    def tearDown(self):
        bpy.context.window_manager.keyconfigs.remove(self.config)

    def add(self, name, key, **modifiers):
        km = self.config.keymaps.new(name, space_type='VIEW_3D' if name == '3D View' else 'EMPTY')
        return km.keymap_items.new('wm.search_menu', key, 'PRESS', **modifiers)

    def test_object_conversion_key_is_not_a_mesh_conflict(self):
        item = self.add('Object Mode', 'F9', ctrl=True)
        before = (item.idname, item.type, item.value, item.ctrl, item.active)
        self.assertEqual(audit.addon_conflicts(self.config, audit.baseline_bindings()), [])
        self.assertEqual(before, (item.idname, item.type, item.value, item.ctrl, item.active))
        self.add('Mesh', 'F9', ctrl=True)
        self.assertEqual(len(audit.addon_conflicts(self.config, audit.baseline_bindings())), 1)

    def test_mesh_parent_key_is_not_an_object_conflict(self):
        self.add('Mesh', 'P')
        self.assertEqual(audit.addon_conflicts(self.config, audit.baseline_bindings()), [])
        self.add('Object Mode', 'P')
        self.assertEqual(len(audit.addon_conflicts(self.config, audit.baseline_bindings())), 1)

    def test_shared_view_still_reports(self):
        self.add('3D View', 'F9', ctrl=True)
        rows = audit.addon_conflicts(self.config, audit.baseline_bindings())
        self.assertEqual(len(rows), 1)
        self.assertIn('selection.convert_vert', rows[0])

    def test_real_file_loader_matches_python_artifact(self):
        report = audit.build_report()
        expected = json.loads(audit.OUTPUT.with_suffix('.json').read_text(encoding='utf-8'))
        self.assertEqual(report, expected)
        self.assertEqual(report['errors'], [])


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(InputDiagnosticsRNA))
if not result.wasSuccessful():
    raise RuntimeError('Input diagnostics RNA verification failed')
print('AXISMELD_INPUT_DIAGNOSTICS_RNA_PASS')

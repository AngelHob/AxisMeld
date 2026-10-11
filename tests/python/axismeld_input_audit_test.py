# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Test audit failures against the real bundled keymap, not a miniature fixture."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tools/utils/axismeld_input_audit.py'


class InputAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not TOOL.exists():
            return
        spec = importlib.util.spec_from_file_location('axismeld_input_audit', TOOL)
        cls.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.audit)

    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'The current-input audit tool must exist')
        self.base = self.audit.load_base()
        self.generated = self.audit.generate_keymaps(self.base, self.audit.baseline_bindings())

    def report(self):
        return self.audit.build_report(base=self.base, generated=self.generated)

    def test_real_generation_preserves_source_and_has_all_aliases(self):
        before = copy.deepcopy(self.base)
        report = self.report()
        self.assertEqual(report['errors'], [])
        self.assertEqual(self.base, before)
        rows = report['bindings']
        self.assertEqual(len(rows), len(list(self.audit.binding_events(self.audit.baseline_bindings()))))
        redo = [r for r in rows if r['command'] == 'edit.redo']
        self.assertEqual({r['input'] for r in redo}, {'Shift+Z', 'Ctrl+Y'})
        self.assertTrue(all(r['placements'] and r['references'] for r in rows))
        self.assertEqual(report['verification']['manual'], 'not_reassessed')

    def test_missing_binding_is_an_error(self):
        mesh = next(c for n, a, c in self.generated if n == 'Mesh')
        mesh['items'] = [i for i in mesh['items'] if self.audit.command_id(i) != 'transform.move']
        self.assertTrue(any('transform.move' in e and 'Mesh' in e for e in self.report()['errors']))

    def test_duplicate_binding_is_an_error(self):
        mesh = next(c for n, a, c in self.generated if n == 'Mesh')
        mesh['items'].append(copy.deepcopy(next(i for i in mesh['items']
                                             if self.audit.command_id(i) == 'transform.move')))
        self.assertTrue(any('transform.move' in e and 'duplicate' in e for e in self.report()['errors']))

    def test_wrong_editor_is_not_reported_as_success(self):
        mesh = next(c for n, a, c in self.generated if n == 'Mesh')
        item = copy.deepcopy(next(i for i in mesh['items'] if self.audit.command_id(i) == 'transform.move'))
        text = next(c for n, a, c in self.generated if n == 'Text')
        text['items'].append(item)
        errors = self.report()['errors']
        self.assertTrue(any('unexpected' in e and 'Text' in e for e in errors))
        self.assertTrue(any('protected' in e and 'Text' in e for e in errors))

    def test_reserved_keys_and_inherited_items_remain_separate(self):
        report = self.report()
        self.assertEqual({r['key'] for r in report['reserved']}, set(self.audit.RESERVED_KEYS))
        self.assertTrue(all(r['status'] == 'reserved_not_implemented' for r in report['reserved']))
        self.assertTrue(report['inherited'])
        self.assertTrue(all(r['status'] == 'native_inherited_not_maya_verified'
                            for r in report['inherited']))

    def test_manipulator_inputs_are_owned_not_native_inheritance(self):
        report = self.report()
        self.assertFalse(any(r['operator'].startswith('axismeld.') for r in report['inherited']))
        self.assertIn('owned_auxiliary', report)
        items = report['owned_auxiliary']
        self.assertEqual(len(items), 7)
        self.assertEqual({r['operator'] for r in items},
                         {'axismeld.axis_select', 'axismeld.axis_drag', 'axismeld.axis_clear'})
        self.assertTrue(any(r['map'] == 'Generic Gizmo Maybe Drag' for r in items))

    def test_wrong_region_changes_report_and_is_an_error(self):
        before = self.report()
        _name, args, _content = next(km for km in self.generated if km[0] == 'AxisMeld Hotbox')
        args['region_type'] = 'HEADER'
        report = self.report()
        self.assertTrue(before != report, 'Region changes must alter the audit snapshot')
        self.assertTrue(any('context' in e and 'AxisMeld Hotbox' in e for e in report['errors']))

    def test_execution_property_change_is_not_invisible(self):
        before = self.report()
        mesh = next(c for n, a, c in self.generated if n == 'Mesh')
        item = next(i for i in mesh['items'] if self.audit.command_id(i) == 'transform.move')
        item[2]['properties'].append(('unexpected', True))
        report = self.report()
        self.assertTrue(before != report, 'Operator property changes must alter the audit snapshot')
        self.assertTrue(any('properties' in e for e in report['errors']))

    def test_reference_default_change_remains_visible(self):
        references = copy.deepcopy(self.audit.load_reference())
        item = next(r for r in references['maya_actions'] if 'selection.invert' in r.get('commands', ()))
        item['maya_default_inputs'] = [{'input': 'Ctrl+Shift+F12', 'source': 'test-reference'}]
        report = self.audit.build_report(base=self.base, generated=self.generated, reference=references)
        row = next(r for r in report['bindings'] if r['command'] == 'selection.invert')
        self.assertIn('Ctrl+Shift+F12', str(row['references']))
        self.assertNotEqual(row['reference_comparison'], 'same_notation')

    def test_deterministic_output_and_no_fake_human_result(self):
        first, second = self.report(), self.report()
        self.assertEqual(first, second)
        md = self.audit.render_markdown(first)
        self.assertIn('not_reassessed', md)
        self.assertIn('Ctrl+Y', md)
        self.assertNotIn(str(ROOT), md)
        self.assertNotIn('C:/Program Files', str(first))

    def test_full_native_properties_are_json_serializable(self):
        report = self.report()
        encoded = json.dumps(report, ensure_ascii=False, sort_keys=True)
        self.assertEqual(json.loads(encoded), report)
        # Native enum-flag properties must keep their values, not stringify a set.
        item = ('mesh.test_enum_flags', {'type': 'F20', 'value': 'PRESS'},
                {'properties': [('flags', {'FACE', 'EDGE'})]})
        mesh = next(c for n, a, c in self.generated if n == 'Mesh')
        mesh['items'].append(item)
        record = next(r for r in self.report()['inherited'] if r['operator'] == item[0])
        self.assertEqual(record['properties'], {'properties': [['flags', ['EDGE', 'FACE']]]})

    def test_python_loader_does_not_leave_fake_bpy_modules(self):
        before = {k: v for k, v in sys.modules.items() if k in {'bpy', 'bpy.utils'}}
        self.audit.load_base()
        after = {k: v for k, v in sys.modules.items() if k in {'bpy', 'bpy.utils'}}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()

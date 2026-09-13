# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""M3 boundary tests: complete menu registry, bounded JSON and isolated keymaps."""
from pathlib import Path
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
from axismeld.commands import COMMANDS, baseline_bindings
from axismeld import hotbox_runtime
from axismeld.hotbox_catalog import command_policy, default_catalog
from axismeld.modeling_registry import SPECS, CATEGORIES, keymap_targets
from axismeld.keymap import generate_keymaps


def nodes():
    pending = list(default_catalog())
    while pending:
        entry = pending.pop()
        yield entry
        pending.extend(entry['children'])


class ModelingRegistryTest(unittest.TestCase):
    def test_all_twelve_categories_are_real_native_lists(self):
        catalog = {node['id']: node for node in nodes()}
        for identifier in CATEGORIES.values():
            entry = catalog[identifier]
            self.assertEqual(entry['kind'], 'menu')
            self.assertEqual(entry['presentation'], 'list')
            self.assertTrue(entry['enabled'])
            self.assertTrue(entry['children'])

    def test_every_command_has_fixed_metadata_and_reachable_menu(self):
        reachable = {node['command'] for node in nodes() if node['kind'] == 'command'}
        self.assertEqual(set(SPECS) - reachable, set())
        for identifier, spec in SPECS.items():
            self.assertIn(identifier, COMMANDS)
            self.assertIn(identifier, hotbox_runtime.SUPPORTED_COMMANDS)
            self.assertTrue(spec.source, identifier)
            self.assertTrue(spec.difference, identifier)
            self.assertIn(spec.classification, {'adapted', 'blender'})
            self.assertEqual(command_policy(identifier), (True, spec.replayable))
            for call in spec.calls:
                self.assertRegex(call.operator, r'^[a-z_][a-z_0-9]*\.[a-z_][a-z_0-9]*$')
                self.assertTrue(call.modes)

    def test_native_allowlist_exactly_matches_registry(self):
        text = (ROOT / 'source/blender/editors/space_view3d/view3d_axismeld_modeling_commands.inc').read_text()
        self.assertEqual(set(re.findall(r'"([a-z0-9_.]+)"', text)), set(SPECS))

    def test_full_snapshot_is_bounded_and_round_trips(self):
        snapshot = hotbox_runtime.make_snapshot(generation=1)
        payload = hotbox_runtime.serialize_snapshot(snapshot)
        self.assertLessEqual(len(payload.encode()), hotbox_runtime.MAX_JSON_BYTES)
        self.assertLess(len(list(nodes())), hotbox_runtime.MAX_NODES)

    def test_display_state_cannot_become_executable_parameters(self):
        snapshot = hotbox_runtime.make_snapshot(generation=1)
        command = next(node for node in snapshot['menus'][0]['children'] if node['id'] == 'common.select')
        leaf = {'id': 'm3.test.state', 'kind': 'command', 'command': 'selection.select_all',
                'label': 'State', 'enabled': True, 'reason': '', 'children': [],
                'indicator': 'radio', 'checked': False}
        command['children'].append(leaf)
        hotbox_runtime.serialize_snapshot(snapshot)
        leaf['checked'] = 'True'
        with self.assertRaisesRegex(ValueError, 'indicator'):
            hotbox_runtime.serialize_snapshot(snapshot)
        leaf['checked'] = True
        leaf['indicator'] = 'operator_path'
        with self.assertRaisesRegex(ValueError, 'indicator'):
            hotbox_runtime.serialize_snapshot(snapshot)

    def test_placeholder_never_dispatches_and_has_unique_plan(self):
        from axismeld.modeling_gaps import GAPS
        self.assertEqual(len({item['plan'] for item in GAPS}), len(GAPS))
        for node in nodes():
            if node['id'].startswith('gap.'):
                self.assertFalse(node['enabled'])
                self.assertEqual(node['command'], '')
                self.assertIn('M3-P-', node['reason'])

    def test_coverage_has_no_unreviewed_or_unimplemented_native_adapters(self):
        from axismeld.modeling_gaps import GAPS
        coverage = json.loads((ROOT / 'docs/maya-mapping/2026-09-14-m3-modeling-coverage.json').read_text(encoding='utf8'))
        self.assertEqual({entry['id'] for entry in coverage['native_commands']}, set(SPECS))
        rows = coverage['maya_actions']
        self.assertEqual(len({row['identity'] for row in rows}), len(rows))
        plans = set()
        for row in rows:
            self.assertNotEqual(row.get('availability'), 'native_adapter_pending', row['identity'])
            if row['scope'] == 'in_scope':
                self.assertIn(row['classification'], {'adapted', 'planned'})
                if row['classification'] == 'adapted':
                    self.assertTrue(row['commands'])
                else:
                    for field in ('plan', 'reason', 'dependency', 'acceptance'):
                        self.assertTrue(row[field], (row['identity'], field))
                    self.assertNotIn(row['plan'], plans)
                    plans.add(row['plan'])
        self.assertEqual(plans, {gap['plan'] for gap in GAPS})

    def test_modal_and_history_policy(self):
        for identifier, spec in SPECS.items():
            if any(call.invoke for call in spec.calls):
                self.assertFalse(spec.replayable, identifier)
        self.assertEqual(COMMANDS['selection.vertex_mode'].key, 'F9')
        self.assertFalse(command_policy('edit.adjust_last_operation')[1])

    def test_curve_keymaps_preserve_native_qwer_and_uv(self):
        base = [(name, {'space_type': space, 'region_type': 'WINDOW'},
                 {'items': [('native.test', {'type': 'Q', 'value': 'PRESS'}, None)]})
                for name, space in [('Curve', 'EMPTY'), ('Lattice', 'EMPTY'), ('UV Editor', 'EMPTY')]]
        result = generate_keymaps(base, baseline_bindings())
        self.assertEqual(result[2], base[2])
        for name, _args, content in result[:2]:
            self.assertIn(base[0][2]['items'][0], content['items'])
            for operator, _event, data in content['items']:
                if operator == 'axismeld.command':
                    command = dict(data['properties'])['command']
                    self.assertIn(command, SPECS)
                    self.assertIn(name, keymap_targets(command))

    def test_default_aliases_follow_remap_disable_and_global_conflict_checks(self):
        from axismeld.keymap import binding_events, validate_global_bindings
        bindings = baseline_bindings()
        aliases = [event for command, event in binding_events(bindings) if command == 'edit.redo']
        self.assertEqual([event['type'] for event in aliases], ['Z', 'Y'])
        conflict = [('Screen', {'space_type': 'EMPTY', 'region_type': 'WINDOW'},
                     {'items': [('native.conflict', {'type': 'Y', 'value': 'PRESS', 'ctrl': True}, None)]})]
        with self.assertRaisesRegex(ValueError, 'global input conflict: edit.redo'):
            validate_global_bindings(conflict, bindings)
        for value in (None, {'type': 'F13', 'value': 'PRESS'}):
            bindings['edit.redo'] = value
            self.assertEqual([event for command, event in binding_events(bindings) if command == 'edit.redo'], [value])
        from axismeld.profiles import resolve_profiles
        for owner, alias in (('edit.redo', {'type': 'Y', 'ctrl': True}),
                             ('display.frame_selected_all', {'type': 'F', 'ctrl': True, 'shift': True})):
            document = {'schema_version': 1, 'bindings': {'selection.grow': alias}}
            rejected = resolve_profiles([('user', document)])
            self.assertTrue(rejected.diagnostics)
            self.assertIn('input conflict', rejected.diagnostics[0])
            document['bindings'][owner] = None
            accepted = resolve_profiles([('user', document)])
            self.assertFalse(accepted.diagnostics)
            self.assertEqual(accepted.bindings['selection.grow']['type'], alias['type'])
        from types import SimpleNamespace
        from axismeld.keymap import addon_conflicts
        item = SimpleNamespace(active=True, type='Y', any=False, ctrl=True, shift=False,
                               alt=False, oskey=False, idname='addon.action')
        maps = [SimpleNamespace(name=name, is_modal=False, keymap_items=[item])
                for name in ('Curve', 'Lattice', 'UV Editor')]
        conflicts = addon_conflicts(SimpleNamespace(keymaps=maps), baseline_bindings())
        self.assertEqual(len(conflicts), 2)
        self.assertTrue(all('edit.redo' in conflict and 'UV Editor' not in conflict for conflict in conflicts))


if __name__ == '__main__':
    unittest.main()

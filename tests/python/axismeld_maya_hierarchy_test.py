# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent Maya UI-reference expectations; never derive them from AxisMeld catalog."""
import json
from pathlib import Path
import unittest
import sys
import hashlib
from copy import deepcopy

REFERENCE = Path(__file__).resolve().parents[2] / 'docs/reference/maya2026-menu-tree.json'
ROOT_LABELS = {
    'common': ('File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows'),
    'current_pane': ('View', 'Shading', 'Lighting', 'Show', 'Renderer', 'Panels'),
    'modeling': ('Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display', 'Curves', 'Surfaces', 'Deform', 'UV', 'Generate'),
}
ROOT_IDS = {
    'common': ('file', 'edit', 'create', 'select', 'modify', 'display', 'windows'),
    'current_pane': ('view', 'shading', 'lighting', 'show', 'renderer', 'panels'),
    'modeling': ('mesh', 'edit_mesh', 'mesh_tools', 'mesh_display', 'curves', 'surfaces', 'deform', 'uv', 'generate'),
}


def reference_roots():
    return json.loads(REFERENCE.read_text(encoding='utf-8'))['groups']


def normalized_reference_roots():
    """Apply the reviewed change ledger to raw capture, without generator imports."""
    ledger = json.loads(REFERENCE.with_name('maya2026-menu-normalization.json').read_text(encoding='utf-8'))
    if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != ledger['source_sha256']:
        raise AssertionError('normalization ledger does not match captured reference')
    changes = {}
    for change in ledger['changes']:
        changes.setdefault(change['source_ui_path'], []).append(change)
    seen = set()
    def convert(source):
        updates = changes.get(source['path'], ())
        seen.add(source['path'])
        if any(c['action'] == 'remove' for c in updates):
            return None
        node = deepcopy(source)
        for update in updates:
            if update['action'] == 'template':
                node['label'] = update['replacement']
            elif update['action'] == 'dynamic_provider':
                node['_dynamic_provider'] = update['reason']
        if 'children' in node:
            node['children'] = [item for child in source['children'] if (item := convert(child)) is not None]
        return node
    result = {group: [convert(n) for n in roots] for group, roots in reference_roots().items()}
    if set(changes) - seen:
        raise AssertionError('normalization references absent UI paths: ' + repr(set(changes) - seen))
    return result


def visual_rows(node):
    """Fold only adjacent Maya optionBox metadata into its actual owner row."""
    rows = []
    for source in node.get('children', ()):
        if source.get('optionBox'):
            if not rows or rows[-1]['kind'] != 'item' or rows[-1]['options']:
                raise AssertionError('unpaired or repeated optionBox: ' + source['path'])
            rows[-1]['options'] = source
            continue
        divider = bool(source.get('divider'))
        label = (source.get('dividerLabel') or source.get('label') or '') if divider else source.get('label', '')
        rows.append({'kind': 'heading' if divider and label else 'separator' if divider else 'item',
                     'label': label, 'options': None, 'source': source})
    return rows


class MayaReferenceShapeTests(unittest.TestCase):
    def test_exact_twenty_two_root_names_and_order(self):
        for group, labels in ROOT_LABELS.items():
            self.assertEqual(tuple(n['label'] for n in reference_roots()[group]), labels)

    def test_display_slots_are_not_twenty_three_action_rows(self):
        display = reference_roots()['common'][5]
        rows = visual_rows(display)
        self.assertEqual(len(display['children']), 23)
        self.assertEqual(sum(r['kind'] == 'item' for r in rows), 16)
        self.assertEqual(sum(r['kind'] != 'item' for r in rows), 5)
        self.assertEqual(sum(bool(r['options']) for r in rows), 2)
        self.assertEqual([r['label'] for r in rows if r['kind'] == 'heading'], ['Viewport', 'Object'])
        self.assertEqual([r['label'] for r in rows if r['options']], ['Grid', 'Toggle Show/Hide'])

    def test_polygons_is_a_real_nested_submenu(self):
        display = reference_roots()['common'][5]
        polygons = next(n for n in display['children'] if n.get('label') == 'Polygons')
        self.assertTrue(polygons['subMenu'])
        self.assertEqual(len(polygons['children']), 37)
        self.assertNotIn('Vertices', [r['label'] for r in visual_rows(display)])
        self.assertIn('Vertices', [r['label'] for r in visual_rows(polygons)])

    def test_every_captured_options_cell_has_one_adjacent_owner(self):
        def visit(node):
            visual_rows(node)
            for child in node.get('children', ()):
                if child.get('subMenu'):
                    visit(child)
        for roots in reference_roots().values():
            for node in roots:
                visit(node)


class MayaCatalogHierarchyTests(unittest.TestCase):
    def test_twenty_two_fixed_root_levels_against_maya(self):
        sys.path.insert(0, str(REFERENCE.parents[2] / 'scripts/modules'))
        from axismeld.hotbox_catalog import default_catalog
        catalog = default_catalog()
        by_id = {}
        def collect(node):
            by_id[node['id']] = node
            for child in node.get('children', ()):
                collect(child)
        if isinstance(catalog, dict):
            roots = catalog.get('roots', ())
        else:
            roots = catalog
        for node in roots:
            collect(node)
        def assert_level(actual, expected):
            rows = visual_rows(expected)
            self.assertEqual([n['label'] for n in actual['children']], [r['label'] for r in rows], actual['id'])
            for observed, row in zip(actual['children'], rows):
                self.assertEqual(observed['kind'] == 'separator', row['kind'] != 'item', observed['id'])
                options = [c for c in observed.get('children', ()) if c['id'].endswith('.options')]
                self.assertEqual(len(options), int(bool(row['options'])), observed['id'])
                if row['source'].get('subMenu'):
                    self.assertEqual(observed['kind'], 'menu', observed['id'])
        for group, roots in normalized_reference_roots().items():
            prefix = 'pane' if group == 'current_pane' else group
            for suffix, expected in zip(ROOT_IDS[group], roots):
                assert_level(by_id[prefix + '.' + suffix], expected)
        display = by_id['common.display']
        actual = next(n for n in display['children'] if n['label'] == 'Polygons')
        expected = next(n for n in reference_roots()['common'][5]['children'] if n.get('label') == 'Polygons')
        assert_level(actual, expected)

    def test_complete_recursive_normalized_hierarchy(self):
        sys.path.insert(0, str(REFERENCE.parents[2] / 'scripts/modules'))
        from axismeld.hotbox_catalog import default_catalog
        by_id = {}
        def collect(node):
            by_id[node['id']] = node
            for child in node.get('children', ()):
                collect(child)
        for node in default_catalog():
            collect(node)
        visited = 0
        def compare(actual, expected, path):
            nonlocal visited
            visited += 1
            rows = visual_rows(expected)
            self.assertEqual(actual['label'], expected['label'], path)
            self.assertEqual(len(actual['children']), len(rows), path)
            for child, row in zip(actual['children'], rows):
                source = row['source']
                here = path + ' > ' + row['label']
                self.assertEqual(child['label'], row['label'], here)
                if row['kind'] != 'item':
                    visited += 1
                    self.assertEqual(child['kind'], 'separator', here)
                    self.assertFalse(child['enabled'], here)
                    self.assertFalse(child.get('command'), here)
                    self.assertFalse(child['children'], here)
                elif source.get('subMenu'):
                    self.assertEqual(child['kind'], 'menu', here)
                    compare(child, source, here)
                else:
                    visited += 1
                    self.assertIn(child['kind'], ('command', 'disabled'), here)
                    indicator = 'checkbox' if source.get('isCheckBox') else 'radio' if source.get('isRadioButton') else ''
                    self.assertEqual(child.get('indicator', ''), indicator, here)
                options = [n for n in child['children'] if n['id'].endswith('.options')]
                self.assertEqual(len(options), int(bool(row['options'])), here)
                if row['options']:
                    visited += 1
                    self.assertEqual(options[0]['id'], child['id'] + '.options', here)
                    self.assertEqual(options[0]['label'], 'Options', here)
                    self.assertFalse(options[0]['enabled'], here)
                    self.assertFalse(options[0].get('command'), here)
                if not source.get('subMenu'):
                    self.assertEqual(len(child['children']), len(options), here)
        for group, roots in normalized_reference_roots().items():
            prefix = 'pane' if group == 'current_pane' else group
            for suffix, expected in zip(ROOT_IDS[group], roots):
                compare(by_id[prefix + '.' + suffix], expected, expected['label'])
        self.assertEqual(visited, 1949)


if __name__ == '__main__':
    unittest.main()

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Cross-boundary contracts: new application menus cannot widen the old hotbox."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))
        if isinstance(node.get('options'), dict):
            yield from walk((node['options'],))


class MenubarIsolationTests(unittest.TestCase):
    def test_new_catalog_keeps_the_verified_hotbox_tree_and_command_boundary(self):
        from axismeld.commands import COMMANDS
        from axismeld.hotbox_catalog import default_catalog
        from axismeld.menubar_catalog import build_menubar
        # Independently recorded before topbar integration at bff4cd9448a.
        expected_tree = '0627b66398ea3f455b2e2296690eacda7f2f327a53838a8427b712878f8f2e71'
        expected_commands = '40dc0b53a83508d66d7c31f628e5dd53a47982e7273bfec241c93f2ad3a08b72'
        for _ in range(2):
            build_menubar()
            serialized = json.dumps(default_catalog(), sort_keys=True, separators=(',', ':')).encode()
            self.assertEqual(hashlib.sha256(serialized).hexdigest(), expected_tree)
            self.assertEqual(hashlib.sha256('\n'.join(sorted(COMMANDS)).encode()).hexdigest(), expected_commands)

    def test_native_application_actions_cannot_be_smuggled_into_hotbox_json(self):
        from axismeld.menubar_catalog import build_menubar
        from axismeld.hotbox_runtime import make_snapshot, validate_snapshot
        build_menubar()
        for command in ('file.save', 'file.import', 'wm.open_mainfile', 'wm.quit_blender'):
            snapshot = make_snapshot(generation=1)
            leaf = next(node for node in walk(snapshot['menus']) if node['kind'] == 'command')
            leaf['command'] = command
            with self.subTest(command=command), self.assertRaises(ValueError):
                validate_snapshot(snapshot)

    def test_assembled_native_dynamic_entries_retain_original_menu_dispatch(self):
        from axismeld.menubar_catalog import build_menubar
        from axismeld.menubar_native import draw_native
        keys = {node.get('native_key') for node in walk(build_menubar()['menus'])}
        expected = {
            'file.import': 'TOPBAR_MT_file_import',
            'file.export': 'TOPBAR_MT_file_export',
            'file.recent': 'TOPBAR_MT_file_open_recent',
            'edit.undo_history': 'TOPBAR_MT_undo_history',
        }
        class NativeRegistryProbe:
            def __init__(self):
                self.calls = []
                self.append_events = []
            def row(self, *, align=False):
                return self
            def menu(self, identifier, **kwargs):
                self.calls.append(identifier)
                # Represents a live registration appended to an existing class.
                # The new assembly must dispatch that class, not copy its rows.
                if identifier in expected.values():
                    self.append_events.append(identifier)
        context = SimpleNamespace()
        for key, identifier in expected.items():
            with self.subTest(key=key):
                self.assertIn(key, keys)
                layout = NativeRegistryProbe()
                draw_native(layout, context, key, text='Native provider', icon='NONE')
                self.assertEqual(layout.calls, [identifier])
                self.assertEqual(layout.append_events, [identifier])

    def test_blender_additions_live_under_actual_editor_and_display_purposes(self):
        from axismeld.menubar_catalog import build_menubar
        paths = {}
        def collect(nodes, parent=()):
            for node in nodes:
                path = parent + (node['label'],)
                for field in ('command', 'native_key', 'action_key'):
                    if node.get(field):
                        paths.setdefault(node[field], []).append(path)
                collect(node.get('children', ()), path)
        collect(build_menubar()['menus'])
        # These are user-facing purposes, not registry section names or hashes.
        expected = {
            'editor.geometry_nodes': ('Windows', 'Modeling Editors'),
            'editor.shader': ('Windows', 'Rendering Editors'),
            'editor.compositor': ('Windows', 'Rendering Editors'),
            'editor.nla': ('Windows', 'Animation Editors'),
            'windows.workspace_next': ('Windows', 'Workspaces'),
            'windows.defaults': ('Windows', 'Settings/Preferences'),
            'display.type_meta': ('Display', 'Viewport Settings', 'Object Types'),
            'display.xray': ('Display', 'Viewport Settings', 'Shading'),
        }
        for capability, prefix in expected.items():
            with self.subTest(capability=capability):
                self.assertTrue(any(path[:len(prefix)] == prefix for path in paths[capability]))

    def test_plugin_trees_and_unadapted_dynamic_directories_are_retained(self):
        from axismeld.menubar_catalog import build_menubar
        from axismeld.menubar_reference import REFERENCE_MENUS, PLUGIN_DEPENDENCIES
        actual = {node['id']: node for node in walk(build_menubar()['menus'])}
        reference = {node['id']: node for node in walk(REFERENCE_MENUS)}
        for identifier in PLUGIN_DEPENDENCIES:
            with self.subTest(plugin_node=identifier):
                self.assertIn(identifier, actual)
                expected_descendants = {node['id'] for node in walk((reference[identifier],))}
                self.assertTrue(expected_descendants <= {node['id'] for node in walk((actual[identifier],))})
        for path in (('File', 'Recent Projects'), ('Select', 'Quick Select Sets'),
                     ('Lighting/Shading', 'Assign Existing Material')):
            node = next(node for node in actual.values() if tuple(node.get('path', ())) == path)
            self.assertEqual(node['kind'], 'menu', path)
            self.assertTrue(node.get('dynamic'), path)
            self.assertFalse(node.get('native_key'), path)
            self.assertFalse(node.get('command'), path)

    def test_core_topbar_source_retains_original_classes_for_external_callers(self):
        import ast
        tree = ast.parse((ROOT / 'scripts/startup/bl_ui/space_topbar.py').read_text(encoding='utf-8'))
        classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
        self.assertTrue({'TOPBAR_MT_file','TOPBAR_MT_edit','TOPBAR_MT_render','TOPBAR_MT_window',
                         'TOPBAR_MT_help','TOPBAR_MT_file_import','TOPBAR_MT_file_export'} <= classes)


if __name__ == '__main__':
    unittest.main(verbosity=2)

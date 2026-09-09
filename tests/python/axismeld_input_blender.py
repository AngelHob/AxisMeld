# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Installed Blender integration tests; intentionally no source module path injection."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest

import bpy
from axismeld import adapter, runtime
from axismeld.commands import COMMANDS, PRESET_NAME, baseline_bindings


class InstalledInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.utils.keyconfig_init()
        cls.area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        cls.region = next(region for region in cls.area.regions if region.type == 'WINDOW')
        cls.preset = next(Path(directory) / (PRESET_NAME + '.py')
                          for directory in bpy.utils.preset_paths('keyconfig')
                          if (Path(directory) / (PRESET_NAME + '.py')).is_file())

    def setUp(self):
        self.override = bpy.context.temp_override(area=self.area, region=self.region)
        self.override.__enter__()
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.context.object

    def tearDown(self):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(self.obj, do_unlink=True)
        self.override.__exit__(None, None, None)

    def test_component_transitions_and_tools(self):
        self.assertTrue(bpy.ops.axismeld.command.poll())
        for command, mode in [('selection.vertex_mode', (True, False, False)),
                              ('selection.edge_mode', (False, True, False)),
                              ('selection.face_mode', (False, False, True))]:
            self.assertEqual(bpy.ops.axismeld.command(command=command), {'FINISHED'})
            self.assertEqual(bpy.context.mode, 'EDIT_MESH')
            self.assertEqual(tuple(bpy.context.tool_settings.mesh_select_mode), mode)
        bpy.ops.axismeld.command(command='selection.toggle_component')
        self.assertEqual(bpy.context.mode, 'OBJECT')
        bpy.ops.axismeld.command(command='selection.toggle_component')
        self.assertEqual(tuple(bpy.context.tool_settings.mesh_select_mode), (False, False, True))
        for mode in ('EDIT', 'OBJECT'):
            bpy.ops.object.mode_set(mode=mode)
            for command, tool in adapter.TOOLS.items():
                for repeat in range(2):
                    self.assertEqual(bpy.ops.axismeld.command(command=command), {'FINISHED'})
                    self.assertEqual(bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname, tool)

    def test_real_generator_preserves_unrelated_maps(self):
        data_file = self.preset.parent / 'keymap_data/industry_compatible_data.py'
        industry = bpy.utils.execfile(str(data_file))
        base = industry.generate_keymaps(industry.Params())
        original = copy.deepcopy(base)
        bindings = baseline_bindings()
        from axismeld.keymap import modeling_keymap, overlaps, generate_keymaps, validate_global_bindings
        from axismeld.commands import RESERVED_KEYS
        validate_global_bindings(base, bindings)
        result = generate_keymaps(base, bindings)
        self.assertEqual(original, base)
        self.assertEqual(len(base), len(result))
        for before, after in zip(base, result):
            if before[0] == 'Generic Gizmo Maybe Drag':
                self.assertEqual(after[2]['items'][1:], before[2]['items'])
                self.assertEqual(after[2]['items'][0][0], 'axismeld.axis_select')
            elif not modeling_keymap(before[0], before[1]):
                self.assertEqual(before, after, before[0])
            else:
                for op, event, props in after[2]['items']:
                    self.assertFalse(any(overlaps(event, {'type': key}) for key in RESERVED_KEYS))
                    if op != 'axismeld.command':
                        self.assertFalse(any(overlaps(event, value) for value in bindings.values()), before[0])

    def test_view_adapter_and_wrong_context(self):
        for command, expected in [('view.wireframe', 'WIREFRAME'), ('view.shaded', 'SOLID')]:
            self.assertEqual(bpy.ops.axismeld.command(command=command), {'FINISHED'})
            self.assertEqual(self.area.spaces.active.shading.type, expected)
        for command in ('view.focus_selected', 'view.frame_all'):
            self.assertEqual(bpy.ops.axismeld.command(command=command), {'FINISHED'})
        self.assertFalse(adapter.available(bpy.context, 'uv.cut')[0])
        self.obj.select_set(False)
        self.assertFalse(adapter.available(bpy.context, 'selection.vertex_mode')[0])
        other = next(area for area in bpy.context.screen.areas if area.type == 'PROPERTIES')
        region = next(region for region in other.regions if region.type == 'WINDOW')
        with bpy.context.temp_override(area=other, region=region):
            self.assertFalse(bpy.ops.axismeld.command.poll())

    def test_preset_load_reload_addon_conflict_and_switch_back(self):
        keyconfigs = bpy.context.window_manager.keyconfigs
        old = keyconfigs.active
        addon = keyconfigs.addon or keyconfigs.new('AxisMeldTestAddon')
        keymap = addon.keymaps.new('Mesh', space_type='EMPTY', region_type='WINDOW')
        item = keymap.keymap_items.new('mesh.select_all', 'W', 'PRESS')
        item.properties.action = 'SELECT'
        original = (item.idname, item.type, item.active, item.properties.action)
        try:
            self.assertTrue(bpy.utils.keyconfig_set(str(self.preset)))
            config = keyconfigs.active
            self.assertEqual(config.name, PRESET_NAME)
            first_count = sum(len(km.keymap_items) for km in config.keymaps)
            for repeat in range(2):
                self.assertEqual(bpy.ops.axismeld.reload_profile(), {'FINISHED'})
                self.assertEqual(sum(len(km.keymap_items) for km in config.keymaps), first_count)
            for command, event in baseline_bindings().items():
                target = '3D View' if command.startswith('view.') else 'Mesh'
                matches = [item for item in config.keymaps[target].keymap_items
                           if item.idname == 'axismeld.command' and item.properties.command == command]
                self.assertEqual(len(matches), 1, command)
                self.assertEqual(matches[0].type, event['type'])
            self.assertEqual(original, (item.idname, item.type, item.active, item.properties.action))
            # Background mode may not provide an addon keyconfig; directly test that case too.
            from axismeld.keymap import addon_conflicts
            self.assertTrue(any('transform.move' in row for row in addon_conflicts(addon, baseline_bindings())))
            keyconfigs.active = old
            self.assertEqual(keyconfigs.active.name, old.name)
        finally:
            keymap.keymap_items.remove(item)
            keyconfigs.active = old

    def test_profile_file_loading_and_baseline_toggle(self):
        old_directory = runtime.profile_directory
        try:
            with tempfile.TemporaryDirectory() as directory:
                runtime.profile_directory = lambda: Path(directory)
                path = Path(directory) / 'user.json'
                content = json.dumps({'schema_version': 1, 'bindings': {'transform.move': {'type': 'T'}}})
                path.write_text(content, encoding='utf-8')
                self.assertTrue(bpy.utils.keyconfig_set(str(self.preset)))
                config = bpy.context.window_manager.keyconfigs.active
                def move_key():
                    return next(item.type for item in config.keymaps['Mesh'].keymap_items
                                if item.idname == 'axismeld.command' and item.properties.command == 'transform.move')
                self.assertEqual(move_key(), 'T')
                config.preferences.use_file_overrides = False
                self.assertEqual(move_key(), 'W')
                config.preferences.use_file_overrides = True
                self.assertEqual(move_key(), 'T')
                self.assertEqual(path.read_text(encoding='utf-8'), content)
        finally:
            runtime.profile_directory = old_directory
            runtime.load()

    def test_export_preserves_semantic_command_properties(self):
        from bl_keymap_utils.io import keyconfig_export_as_data
        keyconfigs = bpy.context.window_manager.keyconfigs
        previous = keyconfigs.active
        try:
            self.assertTrue(bpy.utils.keyconfig_set(str(self.preset)))
            keyconfigs.update()
            with tempfile.TemporaryDirectory() as directory:
                export = Path(directory) / 'AxisMeld_Export_Test.py'
                keyconfig_export_as_data(bpy.context.window_manager, keyconfigs.active, str(export), all_keymaps=True)
                self.assertTrue(bpy.utils.keyconfig_set(str(export)))
                saved = {item.properties.command for keymap in keyconfigs.active.keymaps
                         for item in keymap.keymap_items if item.idname == 'axismeld.command'}
                self.assertEqual(saved, set(COMMANDS))
        finally:
            keyconfigs.active = previous
            exported = keyconfigs.get('AxisMeld_Export_Test')
            if exported:
                keyconfigs.remove(exported)

    def test_native_user_keymap_edit_survives_profile_reload(self):
        keyconfigs = bpy.context.window_manager.keyconfigs
        self.assertTrue(bpy.utils.keyconfig_set(str(self.preset)))
        keyconfigs.update()
        def user_move():
            return next(item for item in keyconfigs.user.keymaps['Mesh'].keymap_items
                        if item.idname == 'axismeld.command' and item.properties.command == 'transform.move')
        item = user_move()
        original = item.type
        try:
            item.type = 'U'
            keyconfigs.update()
            runtime.load()
            keyconfigs.update()
            self.assertEqual(user_move().type, 'U')
        finally:
            user_move().type = original
            keyconfigs.update()

    def test_disabled_file_overrides_survive_keyconfig_recreation(self):
        old_directory = runtime.profile_directory
        keyconfigs = bpy.context.window_manager.keyconfigs
        try:
            with tempfile.TemporaryDirectory() as directory:
                runtime.profile_directory = lambda: Path(directory)
                (Path(directory) / 'user.json').write_text(json.dumps({
                    'schema_version': 1, 'bindings': {'transform.move': {'type': 'T'}}}))
                config = runtime.load()
                config.preferences.use_file_overrides = False
                keyconfigs.remove(config)
                recreated = runtime.load()
                self.assertFalse(recreated.preferences.use_file_overrides)
                move = next(item.type for item in recreated.keymaps['Mesh'].keymap_items
                            if item.idname == 'axismeld.command' and item.properties.command == 'transform.move')
                self.assertEqual(move, 'W')
        finally:
            runtime.profile_directory = old_directory
            config = keyconfigs.get(PRESET_NAME)
            if config:
                config.preferences.use_file_overrides = True
            runtime.load()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(InstalledInputTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

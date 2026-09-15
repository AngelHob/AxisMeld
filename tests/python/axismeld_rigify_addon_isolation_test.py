# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later

"""Regression checks for native modules excluded from add-on management.

Run in an isolated Blender process with disposable BLENDER_USER_CONFIG and
BLENDER_USER_SCRIPTS directories, --background --factory-startup
--python-exit-code 1 --python tests/python/axismeld_rigify_addon_isolation_test.py.
The test loads this checkout's add-on manager while using real Blender RNA and
filesystem discovery. Initialization and extension refresh side effects are
replaced only where the test targets routing, not their upstream internals.
Append -- NativeBootstrapRollback.test_late_parameter_failure_rolls_back for a
single rollback case in its own process; the bootstrap cases need a candidate
with native Rigify installed.
"""
import ast
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import bpy

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('addon_isolation_subject', ROOT / 'scripts/modules/addon_utils.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class NativeIsolation(unittest.TestCase):
    def setUp(self):
        bpy.context.preferences.use_preferences_save = False
        for name in ('rigify', 'ordinary_probe'):
            if name not in bpy.context.preferences.addons:
                bpy.context.preferences.addons.new().module = name
        self.record = bpy.context.preferences.addons['rigify']
        self.pointer = self.record.as_pointer()
        self.root = Path(tempfile.mkdtemp(prefix='native-addon-discovery-', dir=tempfile.gettempdir()))
        for name in ('rigify', 'ordinary_probe'):
            folder = self.root / name
            folder.mkdir()
            (folder / '__init__.py').write_text("bl_info = {'name': %r, 'blender': (4, 0, 0)}\n" % name)

    def test_check_does_not_treat_preference_storage_as_enabled_addon(self):
        mod = types.ModuleType('rigify')
        with patch.dict(sys.modules, {'rigify': mod}), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(subject.check('rigify'), (False, False))
            self.assertEqual(out.getvalue(), '')

    def test_enable_leaves_native_module_and_preferences_untouched(self):
        calls = []
        mod = types.ModuleType('rigify')
        mod.__file__ = str(self.root / 'rigify/__init__.py')
        mod.__time__ = os.path.getmtime(mod.__file__)
        mod.register = lambda: calls.append('register')
        with patch.dict(sys.modules, {'rigify': mod}):
            subject.enable('rigify', default_set=True, persistent=True, refresh_handled=True)
            self.assertEqual(calls, [], 'Native registration belongs only to startup')
            self.assertNotIn('__addon_enabled__', vars(mod))
            self.assertEqual(bpy.context.preferences.addons['rigify'].as_pointer(), self.pointer)

    def test_disable_does_not_unregister_or_delete_native_preferences(self):
        calls = []
        mod = types.ModuleType('rigify')
        mod.__addon_enabled__ = True
        mod.unregister = lambda: calls.append('unregister')
        with patch.dict(sys.modules, {'rigify': mod}):
            subject.disable('rigify', default_set=True, refresh_handled=True)
            self.assertEqual(calls, [], 'Native unregistration belongs only to startup')
            self.assertEqual(bpy.context.preferences.addons['rigify'].as_pointer(), self.pointer)

    def test_discovery_excludes_old_user_copy_and_stale_cache(self):
        old = types.SimpleNamespace(
            __file__=str(self.root / 'rigify/__init__.py'),
            __time__=os.path.getmtime(self.root / 'rigify/__init__.py'),
            bl_info={'name': 'Rigify'},
        )
        cache = {'rigify': old}
        with patch.object(subject, '_paths_with_extension_repos', return_value=[(str(self.root), '')]):
            subject.modules_refresh(module_cache=cache)
        self.assertEqual(set(cache), {'ordinary_probe'})
        self.assertEqual(subject.error_duplicates, [])

    def test_cached_discovery_hides_native_without_refresh(self):
        cache = {'rigify': types.SimpleNamespace(__name__='rigify'),
                 'ordinary_probe': types.SimpleNamespace(__name__='ordinary_probe')}
        result = subject.modules(module_cache=cache, refresh=False)
        self.assertEqual([m.__name__ for m in result], ['ordinary_probe'])

    def test_reset_does_not_reload_old_rigify_copy(self):
        native = types.ModuleType('rigify')
        ordinary = types.ModuleType('ordinary_probe')
        with patch.object(subject, '_paths_with_extension_repos', return_value=[(str(self.root), '')]), \
             patch.object(subject, 'extensions_refresh'), \
             patch.object(subject, 'check', return_value=(False, False)) as state, \
             patch('importlib.reload') as reload_module, \
             patch.dict(sys.modules, {'rigify': native, 'ordinary_probe': ordinary}):
            subject.reset_all(reload_scripts=True)
            self.assertEqual([c.args[0] for c in state.call_args_list], ['ordinary_probe'])
            self.assertEqual([c.args[0] for c in reload_module.call_args_list], [ordinary])

    def test_startup_does_not_enable_preference_storage(self):
        with patch.object(subject, 'paths', return_value=[]), \
             patch.object(subject, '_stale_pending_check_and_remove_once'), \
             patch.object(subject, '_initialize_extensions_repos_once'), \
             patch.object(subject, 'enable') as enable:
            subject._initialize_once()
            self.assertNotIn('rigify', [call.args[0] for call in enable.call_args_list])
            self.assertIn('ordinary_probe', [call.args[0] for call in enable.call_args_list])

    def test_both_preference_lists_exclude_native_storage_but_keep_real_addons(self):
        for relative in ('scripts/startup/bl_ui/space_userpref.py',
                         'scripts/addons_core/bl_pkg/bl_extension_ui.py'):
            tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
            assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == 'used_addon_module_name_map'
                                   for t in node.targets)]
            self.assertEqual(len(assignments), 1)
            expression = ast.Expression(assignments[0].value)
            result = eval(compile(expression, relative, 'eval'),
                          {'prefs': bpy.context.preferences, 'addon_utils': subject})
            self.assertNotIn('rigify', result, relative)
            self.assertIn('ordinary_probe', result)


class NativeBootstrapRollback(unittest.TestCase):
    def assert_unregistered(self, builtin):
        self.assertFalse(hasattr(bpy.types.PoseBone, 'rigify_type'))
        self.assertFalse(hasattr(bpy.types.PoseBone, 'rigify_parameters'))
        self.assertFalse(hasattr(bpy.types.Armature, 'rigify_target_rig'))
        self.assertNotIn(builtin._preferences_update_pre, bpy.app.handlers._extension_repos_update_pre)
        self.assertNotIn(builtin._preferences_update_post, bpy.app.handlers._extension_repos_update_post)
        self.assertNotIn(builtin.rigify.utils.action_layers.versioning_5_0, bpy.app.handlers.load_post)
        self.assertIsNone(bpy.types.Panel.bl_rna_get_subclass_py('USERPREF_PT_animation_rigify'))

    def assert_registered_once(self, builtin):
        self.assertTrue(hasattr(bpy.types.PoseBone, 'rigify_type'))
        self.assertTrue(hasattr(bpy.types.PoseBone, 'rigify_parameters'))
        self.assertTrue(hasattr(bpy.types.Armature, 'rigify_target_rig'))
        self.assertEqual(bpy.app.handlers._extension_repos_update_pre.count(builtin._preferences_update_pre), 1)
        self.assertEqual(bpy.app.handlers._extension_repos_update_post.count(builtin._preferences_update_post), 1)
        self.assertEqual(bpy.app.handlers.load_post.count(builtin.rigify.utils.action_layers.versioning_5_0), 1)
        self.assertIs(bpy.types.Panel.bl_rna_get_subclass_py('USERPREF_PT_animation_rigify'),
                      builtin.USERPREF_PT_animation_rigify)

    def test_late_parameter_failure_rolls_back(self):
        import rigify_builtin as builtin
        bpy.context.preferences.use_preferences_save = False
        self.assert_registered_once(builtin)
        builtin.unregister()

        def fail_after_core_registration():
            self.assertTrue(hasattr(bpy.types.PoseBone, 'rigify_type'))
            self.assertTrue(hasattr(bpy.types.Armature, 'rigify_target_rig'))
            raise RuntimeError('Injected late parameter failure')

        with patch.object(builtin.rigify, 'register_rig_parameters', side_effect=fail_after_core_registration):
            with self.assertRaisesRegex(RuntimeError, 'Injected late parameter failure'):
                builtin.register()
        self.assert_unregistered(builtin)
        builtin.register()
        self.assert_registered_once(builtin)

    def test_preferences_panel_failure_rolls_back(self):
        import rigify_builtin as builtin
        bpy.context.preferences.use_preferences_save = False
        self.assert_registered_once(builtin)
        builtin.unregister()
        real_register_class = bpy.utils.register_class

        def register_except_preferences_panel(cls):
            if cls is builtin.USERPREF_PT_animation_rigify:
                self.assertTrue(hasattr(bpy.types.PoseBone, 'rigify_type'))
                raise RuntimeError('Injected preferences panel failure')
            return real_register_class(cls)

        with patch.object(bpy.utils, 'register_class', side_effect=register_except_preferences_panel):
            with self.assertRaisesRegex(RuntimeError, 'Injected preferences panel failure'):
                builtin.register()
        self.assert_unregistered(builtin)
        builtin.register()
        self.assert_registered_once(builtin)


test_names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
suite = (unittest.defaultTestLoader.loadTestsFromNames(test_names, module=sys.modules[__name__])
         if test_names else unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise RuntimeError('Native addon isolation probe failed')
print('NATIVE_ADDON_ISOLATION_PASS', flush=True)

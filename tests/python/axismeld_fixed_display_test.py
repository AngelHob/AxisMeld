# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the production setting methods without loading Blender RNA classes."""
import ast
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
from axismeld.modeling_common import SETTINGS


def production_functions():
    tree = ast.parse((ROOT / 'scripts/modules/axismeld/modeling_common_ops.py').read_text(encoding='utf-8'))
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {
        '_setting_owner', '_setting_available', 'command_state'}]
    operator = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AXISMELD_OT_m3_setting')
    definitions += [n for n in operator.body if isinstance(n, ast.FunctionDef) and n.name == 'execute']
    scope = {'SETTINGS': SETTINGS}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), '<production setting methods>', 'exec'), scope)
    return scope


class FixedDisplayTest(unittest.TestCase):
    def test_on_and_off_are_idempotent_and_keep_legacy_toggle(self):
        methods = production_functions()
        shading = SimpleNamespace(show_backface_culling=False)
        context = SimpleNamespace(space_data=SimpleNamespace(type='VIEW_3D', shading=shading, overlay=object()), area=None)
        for action, expected in [('on', True), ('on', True), ('off', False), ('off', False)]:
            command = 'display.backface_culling_' + action
            self.assertEqual(methods['execute'](SimpleNamespace(action=command), context), {'FINISHED'})
            self.assertIs(shading.show_backface_culling, expected)
            self.assertIsNone(methods['command_state'](context, command))
        for expected in (True, False):
            self.assertEqual(methods['execute'](SimpleNamespace(action='display.backface_culling'), context), {'FINISHED'})
            self.assertIs(shading.show_backface_culling, expected)
            self.assertEqual(methods['command_state'](context, 'display.backface_culling'), ('checkbox', expected))

    def test_explicit_actions_reject_non_viewport_context(self):
        methods = production_functions()
        for space in (None, SimpleNamespace(type='IMAGE_EDITOR')):
            context = SimpleNamespace(space_data=space, area=None)
            for command in ('display.backface_culling_on', 'display.backface_culling_off'):
                self.assertEqual(methods['execute'](SimpleNamespace(action=command), context), {'CANCELLED'})


if __name__ == '__main__':
    unittest.main()

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run in isolated Blender; verify optional feature-set preference lifecycles."""
import json
import os
from pathlib import Path

import bpy
import rigify
from rigify import feature_set_list

artifacts = Path(os.environ['AXISMELD_RIGIFY_ARTIFACTS']).resolve()
scripts = Path(os.environ['BLENDER_USER_SCRIPTS']).resolve()
install = Path(feature_set_list.get_install_path(create=True)).resolve()
assert install.is_relative_to(scripts)
trace = artifacts / 'enabled-feature-trace.txt'
assert not trace.exists()
for module in ('enabled_feature_probe', 'unrecorded_feature_probe'):
    root = install / module
    root.mkdir()
    for subdir in ('rigs', 'metarigs'):
        (root / subdir).mkdir()
        (root / subdir / '__init__.py').write_text('', encoding='utf-8')
    (root / '__init__.py').write_text(
        "import os\nfrom pathlib import Path\n"
        "rigify_info = {'name': 'Isolated feature probe'}\n"
        "def emit(event):\n"
        "    with (Path(os.environ['AXISMELD_RIGIFY_ARTIFACTS']) / 'enabled-feature-trace.txt').open('a') as f:\n"
        f"        f.write('{module}:' + event + '\\n')\n"
        "def register(): emit('register')\n"
        "def unregister(): emit('unregister')\n", encoding='utf-8')


def prefs():
    return rigify.RigifyPreferences.get_instance()


def entry(module):
    return next(fs for fs in prefs().rigify_feature_sets if fs.module_name == module)


def events():
    return trace.read_text().splitlines() if trace.exists() else []


prefs().refresh_installed_feature_sets()
assert not entry('enabled_feature_probe').enabled
assert not entry('unrecorded_feature_probe').enabled
assert events() == [], 'Discovery activated optional code'
entry('enabled_feature_probe').enabled = True
expected = ['enabled_feature_probe:register']
assert events() == expected
assert bpy.ops.wm.save_userpref() == {'FINISHED'}
entry('enabled_feature_probe').enabled = False
expected += ['enabled_feature_probe:unregister']
assert bpy.ops.wm.read_userpref() == {'FINISHED'}
expected += ['enabled_feature_probe:register']
assert entry('enabled_feature_probe').enabled and not entry('unrecorded_feature_probe').enabled
assert events() == expected, ('Preferences did not restore exactly one registration', events())

for _ in range(2):
    bpy.utils.load_scripts(reload_scripts=True)
    expected += ['enabled_feature_probe:unregister', 'enabled_feature_probe:register']
    assert events() == expected, ('Reload left duplicate or unbalanced external callbacks', events())
    assert entry('enabled_feature_probe').enabled and not entry('unrecorded_feature_probe').enabled

assert bpy.ops.wm.read_factory_userpref() == {'FINISHED'}
expected += ['enabled_feature_probe:unregister']
assert events() == expected
assert not entry('enabled_feature_probe').enabled and not entry('unrecorded_feature_probe').enabled
assert bpy.ops.pose.rigify_generate.get_rna_type()
(artifacts / 'feature-lifecycle.json').write_text(json.dumps(dict(status='PASS', events=events(),
    saved_enabled_restored=True, two_reloads_balanced=True, factory_keeps_optional_features_disabled=True), indent=2), encoding='utf-8')
print('RIGIFY_FEATURE_LIFECYCLE_PASS')

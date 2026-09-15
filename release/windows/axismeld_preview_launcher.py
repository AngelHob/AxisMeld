# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Start the portable preview in the tested Maya Modeling workspace."""
from pathlib import Path
import os
import bpy

bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.view.show_splash = False
preset = Path(bpy.utils.system_resource('SCRIPTS')) / 'presets/keyconfig/AxisMeld_Maya_2026.py'
assert preset.is_file(), 'The bundled Maya key configuration is missing'
assert bpy.utils.keyconfig_set(str(preset)), 'Maya key configuration activation failed'

if bpy.app.background:
    print('AXISMELD_PREVIEW_CONFIG_READY_GUI_REQUIRED', flush=True)
else:
    window = bpy.context.window
    workspace = bpy.data.workspaces.get('Modeling')
    assert window is not None and workspace is not None
    window.workspace = workspace

    def verify_workspace():
        from bl_ui.space_axismeld_menubar import modeling_workspace
        assert window.workspace == workspace
        area = next(area for area in window.screen.areas if area.type == 'VIEW_3D')
        region = next(region for region in area.regions if region.type == 'WINDOW')
        with bpy.context.temp_override(window=window, area=area, region=region):
            assert modeling_workspace(bpy.context)
        print('AXISMELD_PORTABLE_PREVIEW_LAUNCH_PASS', flush=True)
        if os.environ.get('AXISMELD_PREVIEW_LAUNCH_TEST') == '1':
            bpy.ops.wm.quit_blender()
        return None

    bpy.app.timers.register(verify_workspace, first_interval=0.5)

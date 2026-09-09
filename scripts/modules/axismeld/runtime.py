# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Preset loading; files and addon keymaps are read-only inputs."""
from pathlib import Path
import bpy
from bl_keymap_utils.io import keyconfig_init_from_data

from .commands import PRESET_NAME
from .profiles import load_profiles, resolve_profiles
from .keymap import generate_keymaps, addon_conflicts, validate_global_bindings

diagnostics = []
sources = {}


def profile_directory():
    directory = bpy.utils.user_resource('CONFIG')
    return Path(directory) / 'axismeld' if directory else None


def load(*, session=None):
    global diagnostics, sources
    keyconfigs = bpy.context.window_manager.keyconfigs
    existing = keyconfigs.get(PRESET_NAME)
    use_overrides = existing.preferences.use_file_overrides if existing and existing.preferences else True
    directory = profile_directory()
    # Both files are shipped in the standard scripts tree and installed by upstream CMake.
    data_file = Path(__file__).resolve().parents[2] / 'presets/keyconfig/keymap_data/industry_compatible_data.py'
    industry = bpy.utils.execfile(str(data_file))
    base = industry.generate_keymaps(industry.Params(
        use_mouse_emulate_3_button=bpy.context.preferences.inputs.use_mouse_emulate_3_button))
    validate = lambda candidate: validate_global_bindings(base, candidate)
    resolved = (load_profiles(directory, session=session, validate=validate) if use_overrides and directory else
                resolve_profiles([('session', session)] if session is not None else [], validate=validate))
    data = generate_keymaps(base, resolved.bindings)
    diagnostics = resolved.diagnostics + addon_conflicts(keyconfigs.addon, resolved.bindings)
    if bpy.context.preferences.inputs.use_mouse_emulate_3_button:
        diagnostics.append('Emulate 3 Button Mouse uses Alt+LMB; disable it for Maya tumble navigation')
    sources = resolved.sources
    for message in diagnostics:
        print('AxisMeld:', message)
    config = keyconfigs.new(PRESET_NAME)
    keyconfig_init_from_data(config, data)
    return config

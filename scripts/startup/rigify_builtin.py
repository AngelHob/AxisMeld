# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later

"""Native startup lifecycle and preferences UI for the bundled Rigify module."""

import bpy
from bpy.app.handlers import persistent

# bpy.utils reloads startup modules after unregistering them; the implementation
# package lives in modules and must be reloaded here as well.
if "rigify" in locals():
    import importlib
    rigify = importlib.reload(rigify)
else:
    import rigify

_registered = False
_preferences_suspended = False


class USERPREF_PT_animation_rigify(bpy.types.Panel):
    bl_label = "Rigify"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "animation"

    def draw(self, context):
        self.layout.label(text="Automatic Rigging", icon='ARMATURE_DATA')
        rigify.RigifyPreferences.get_instance(context).draw_settings(self.layout, context)


@persistent
def _preferences_update_pre(*_args):
    global _preferences_suspended
    if _registered and not _preferences_suspended:
        rigify.feature_set_list.unregister_feature_sets()
        _preferences_suspended = True


@persistent
def _preferences_update_post(*_args):
    global _preferences_suspended
    if not _registered:
        return
    prefs = rigify.RigifyPreferences.get_instance()
    prefs.register_feature_sets(True)
    prefs.update_external_rigs()
    _preferences_suspended = False


def register():
    global _registered, _preferences_suspended
    if _registered:
        return
    try:
        rigify.register()
        bpy.utils.register_class(USERPREF_PT_animation_rigify)
        bpy.app.handlers._extension_repos_update_pre.append(_preferences_update_pre)
        bpy.app.handlers._extension_repos_update_post.append(_preferences_update_post)
    except Exception:
        # External rig parameters can fail after Rigify's core classes/RNA have
        # registered. Roll them back so a corrected package can load on reload.
        # Preserve the original exception if cleanup itself reports a problem.
        import traceback
        try:
            _unregister_preferences_ui()
            rigify.unregister()
        except Exception:
            traceback.print_exc()
        _preferences_suspended = False
        raise
    _registered = True


def _unregister_preferences_ui():
    for handlers, callback in (
        (bpy.app.handlers._extension_repos_update_pre, _preferences_update_pre),
        (bpy.app.handlers._extension_repos_update_post, _preferences_update_post),
    ):
        if callback in handlers:
            handlers.remove(callback)
    if USERPREF_PT_animation_rigify.is_registered:
        bpy.utils.unregister_class(USERPREF_PT_animation_rigify)


def unregister():
    global _registered, _preferences_suspended
    if not _registered:
        return
    _unregister_preferences_ui()
    rigify.unregister()
    _registered = False
    _preferences_suspended = False

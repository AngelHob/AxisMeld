# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Trusted native menu drawing. No configuration-supplied operators or context overrides."""
import sys
from types import SimpleNamespace

_MENUS = {
    'file.new': 'TOPBAR_MT_file_new',
    'file.recent': 'TOPBAR_MT_file_open_recent',
    'file.recover': 'TOPBAR_MT_file_recover',
    'file.previews': 'TOPBAR_MT_file_previews',
    'file.project': 'TOPBAR_MT_file_project',
    'file.import': 'TOPBAR_MT_file_import',
    'file.export': 'TOPBAR_MT_file_export',
    'file.external_data': 'TOPBAR_MT_file_external_data',
    'file.cleanup': 'TOPBAR_MT_file_cleanup',
    'edit.undo_history': 'TOPBAR_MT_undo_history',
    'windows.defaults': 'TOPBAR_MT_file_defaults',
    'help.system': 'TOPBAR_MT_blender_system',
}
_OPERATORS = {
    'file.new_scene': 'wm.read_homefile',
    'file.save_preferences': 'wm.save_userpref',
    'file.open': 'wm.open_mainfile',
    'file.revert': 'wm.revert_mainfile',
    'file.link': 'wm.link',
    'file.append': 'wm.append',
    'file.quit': 'wm.quit_blender',
    'edit.undo': 'ed.undo',
    'edit.redo': 'ed.redo',
    'edit.adjust_last': 'screen.redo_last',
    'edit.repeat_last': 'screen.repeat_last',
    'edit.repeat_history': 'screen.repeat_history',
    'edit.search': 'wm.search_menu',
    'edit.operator_search': 'wm.search_operator',
    'modify.rename': 'wm.call_panel',
    'modify.batch_rename': 'wm.batch_rename',
    'windows.preferences': 'screen.userpref_show',
    'windows.install_template': 'preferences.app_template_install',
    'windows.new': 'wm.window_new',
    'windows.new_main': 'wm.window_new_main',
    'windows.fullscreen': 'wm.window_fullscreen_toggle',
    'windows.workspace_next': 'screen.workspace_cycle',
    'windows.workspace_previous': 'screen.workspace_cycle',
    'windows.screenshot': 'screen.screenshot',
    'windows.screenshot_editor': 'screen.screenshot_area',
    'windows.console': 'wm.console_toggle',
    'windows.stereo': 'wm.set_stereo_3d',
    'render.mixdown': 'sound.mixdown',
    'render.view_render': 'render.view_show',
    'render.play_animation': 'render.play_rendered_anim',
    'help.splash': 'wm.splash',
    'help.about': 'wm.splash_about',
    'help.cheat_sheet': 'wm.operator_cheat_sheet',
    'help.sysinfo': 'wm.sysinfo',
}
_PRESETS = {'help.manual': 'MANUAL', 'help.release_notes': 'RELEASE_NOTES',
            'help.api': 'API', 'help.report_bug': 'BUG'}
_URLS = {
    'help.support': 'https://www.blender.org/support',
    'help.community': 'https://www.blender.org/community/',
    'help.get_involved': 'https://www.blender.org/get-involved/',
    'help.developer_docs': 'https://developer.blender.org/docs/',
    'help.developer_community': 'https://devtalk.blender.org',
}
_DEVELOPER = frozenset({'edit.operator_search', 'help.developer_docs',
                        'help.developer_community', 'help.api', 'help.cheat_sheet'})
_SAVES = frozenset({'file.save', 'file.save_as', 'file.save_copy', 'file.save_incremental'})
_RENDERS = frozenset({'render.image', 'render.animation', 'render.sequence_image',
                      'render.sequence_animation'})
NATIVE_KEYS = frozenset(_MENUS) | frozenset(_OPERATORS) | frozenset(_PRESETS) | frozenset(_URLS) | _SAVES | _RENDERS | frozenset({
    'windows.lock_object_mode', 'windows.statusbar', 'render.lock_interface', 'render.native',
})


def draw_native(layout, context, key, *, text, icon):
    """Draw one fixed native entry, preserving the caller's source context.

    Child layouts isolate per-entry invocation modes and enabled flags. Original
    dynamic Menu classes retain add-on append hooks and their own live conditions.
    """
    if key not in NATIVE_KEYS:
        raise ValueError('Unknown native menubar key: ' + str(key))
    if key in _DEVELOPER and not context.preferences.view.show_developer_ui:
        return
    if key == 'windows.console' and sys.platform[:3] != 'win':
        return
    if key == 'windows.stereo' and not context.scene.render.use_multiview:
        return
    if key in {'render.sequence_image', 'render.sequence_animation'}:
        seq_scene = context.sequencer_scene
        if not (seq_scene and seq_scene.render.use_sequencer and
                getattr(context, 'strips', ()) and seq_scene != context.scene):
            return

    # item_align() only descends into aligned children. Keep a native body in
    # its parent's alignment group with the independent Options cell.
    row = layout.column() if key == 'render.native' else layout.row(align=True)
    kwargs = {'text': text, 'icon': icon}
    if key == 'render.native':
        from bl_ui.space_topbar import TOPBAR_MT_render
        TOPBAR_MT_render.draw(SimpleNamespace(layout=row), context)
    elif key in _MENUS:
        if key.startswith('file.') or key == 'windows.defaults':
            row.operator_context = 'INVOKE_AREA'
        row.menu(_MENUS[key], **kwargs)
    elif key in _SAVES:
        row.operator_context = 'INVOKE_AREA'
        if key == 'file.save' and context.blend_data.is_saved:
            row.operator_context = 'EXEC_AREA'
        elif key == 'file.save_incremental':
            row.operator_context = 'EXEC_AREA'
            row.enabled = context.blend_data.is_saved
        props = row.operator('wm.save_as_mainfile' if key in {'file.save_as', 'file.save_copy'}
                             else 'wm.save_mainfile', **kwargs)
        props.show_save_modified_images_dialog = True
        if key == 'file.save_copy':
            props.copy = True
        elif key == 'file.save_incremental':
            props.incremental = True
    elif key in _RENDERS:
        props = row.operator('render.render', **kwargs)
        props.use_viewport = True
        if key in {'render.animation', 'render.sequence_animation'}:
            props.animation = True
        if key in {'render.sequence_image', 'render.sequence_animation'}:
            props.use_sequencer_scene = True
    elif key == 'windows.lock_object_mode':
        row.prop(context.tool_settings, 'lock_object_mode', **kwargs)
    elif key == 'windows.statusbar':
        row.prop(context.screen, 'show_statusbar', **kwargs)
    elif key == 'render.lock_interface':
        row.prop(context.scene.render, 'use_lock_interface', **kwargs)
    elif key in _PRESETS:
        row.operator('wm.url_open_preset', **kwargs).type = _PRESETS[key]
    elif key in _URLS:
        row.operator('wm.url_open', **kwargs).url = _URLS[key]
    else:
        if key == 'file.save_preferences':
            row.operator_context = 'EXEC_AREA'
        elif key.startswith('file.') and key != 'file.new_scene':
            row.operator_context = 'INVOKE_AREA'
        elif key == 'file.new_scene':
            row.operator_context = 'INVOKE_DEFAULT'
        elif key == 'windows.screenshot_editor':
            row.operator_context = 'INVOKE_SCREEN'
        props = row.operator(_OPERATORS[key], **kwargs)
        if key == 'modify.rename':
            props.name = 'TOPBAR_PT_name'
            props.keep_open = False
        elif key == 'windows.workspace_next':
            props.direction = 'NEXT'
        elif key == 'windows.workspace_previous':
            props.direction = 'PREV'

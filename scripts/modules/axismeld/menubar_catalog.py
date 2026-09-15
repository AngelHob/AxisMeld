# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Application menus organized by the captured Maya hierarchy.

Only fixed semantic IDs and native keys are executable. Captured Maya command
text is provenance, never code. This tree is separate from the hotbox protocol.
"""
from copy import deepcopy
from hashlib import sha256

from .maya_menu_catalog import _binding, UNAVAILABLE_BINDINGS
from .menubar_actions import ACTIONS
from .menubar_native import NATIVE_KEYS
from .menubar_reference import MENU_SETS, REFERENCE_MENUS
from .modeling_registry import SPECS

CATEGORY_ROOTS = {
    'Select': 'common.select', 'Modify': 'common.modify', 'Display': 'common.display',
    'Edit': 'common.edit', 'Create': 'common.create', 'Mesh': 'modeling.mesh',
    'Edit Mesh': 'modeling.edit_mesh', 'Mesh Tools': 'modeling.mesh_tools',
    'Mesh Display': 'modeling.mesh_display', 'Curves': 'modeling.curves',
    'Surfaces': 'modeling.surfaces', 'Deform': 'modeling.deform',
    'Windows': 'common.windows',
}

# Exact reviewed runtime-command identities. Similar Maya tools remain disabled.
NATIVE_BINDINGS = {
    'NewScene': 'file.new_scene', 'OpenScene': 'file.open', 'SaveScene': 'file.save',
    'SaveSceneAs': 'file.save_as', 'IncrementAndSave': 'file.save_incremental',
    'SavePreferences': 'file.save_preferences', 'Import': 'file.import',
    'Export': 'file.export', 'Quit': 'file.quit', 'Undo': 'edit.undo',
    'Redo': 'edit.redo', 'RepeatLast': 'edit.repeat_last',
    'PreferencesWindow': 'windows.preferences', 'OutputWindow': 'windows.console',
    'RenderIntoNewWindow': 'render.image', 'RenderViewWindow': 'render.view_render',
}
ACTION_BINDINGS = {
    value['maya_command']: key for key, value in ACTIONS.items() if value.get('maya_command')
}
ACTION_BINDINGS.update({
    'OutlinerWindow': 'editor.outliner', 'GraphEditor': 'editor.graph',
    'DopeSheetEditor': 'editor.dopesheet', 'TextureViewWindow': 'editor.uv',
})

# Reuse real parent menus where the registry's section names describe that purpose.
SECTION_PATHS = {
    ('Create', 'Additional Primitives'): ('Polygon Primitives', 'Additional Primitives'),
    ('Create', 'Subdivision Primitives'): ('Polygon Primitives', 'Subdivision Primitives'),
    ('Create', 'Curve Primitives'): ('Curve Tools', 'Curve Primitives'),
    ('Create', 'Measure'): ('Measure Tools',),
    ('Create', 'Object Collections'): ('Collections',),
    ('Modify', 'Snapping'): ('Snap Align Objects', 'Snapping Settings'),
    ('Modify', 'Snap Actions'): ('Snap Align Objects', 'Snap Actions'),
    ('Modify', 'Transform Actions'): ('Transformation Tools', 'Transform Actions'),
    ('Modify', 'Names'): ('Naming Tools',),
    ('Select', 'Selection'): ('Selection Tools',),
    ('Select', 'Select Similar'): ('Similarity Filters',),
    ('Edit', 'Hierarchy'): ('Hierarchy Tools',),
    ('Edit', 'Duplicate'): ('Duplicate Tools',),
    ('Mesh', 'Clean Up'): ('Cleanup Tools',),
    ('Mesh', 'Combine'): ('Combine Tools',),
    ('Edit Mesh', 'Extrude'): ('Extrusion Tools',),
    ('Edit Mesh', 'Merge'): ('Merge Tools',),
    ('Mesh Display', 'Average Normals'): ('Average Normal Tools',),
}

# Named Maya headings are separators, not fabricated submenus. Supplemental
# purpose directories are inserted within the appropriate heading's section.
SECTION_ANCHORS = {
    ('common.file', 'Scene Templates'): '',
    ('common.file', 'Save and Recover'): '',
    ('common.file', 'References and Data'): 'References',
    ('common.file', 'Project Tools'): 'Project',
    ('common.file', 'View Previews'): 'View',
    ('common.create', 'Objects'): 'Objects',
    ('common.create', 'Rigging'): 'Objects',
    ('common.create', 'Metaballs'): 'Objects',
    ('common.create', 'Volumes'): 'Objects',
    ('common.create', 'Grease Pencil'): 'Objects',
    ('common.create', 'Audio'): 'Objects',
    ('common.create', 'Force Fields'): 'Objects',
    ('common.create', 'Collections'): 'Scene Management',
    ('common.edit', 'History'): '',
    ('common.edit', 'Search'): '',
    ('common.edit', 'Duplicate Tools'): 'Duplicate',
    ('common.modify', 'Naming Tools'): 'Naming',
    ('menubar.rendering.render', 'Render Output'): 'Rendering',
    ('menubar.help', 'Blender Help'): 'Learn',
    ('menubar.help', 'Diagnostics'): 'Support',
}

# Each tuple is (root, real or purpose parent path, fixed native entries).
# Original native dynamic menu IDs are drawn by menubar_native, preserving hooks.
NATIVE_GROUPS = (
    ('common.file', ('Scene Templates',), (('file.new', 'New from Template'),)),
    ('common.file', ('Save and Recover',), (
        ('file.save_copy', 'Save Copy...'), ('file.revert', 'Revert'),
        ('file.recover', 'Recover'))),
    ('common.file', ('References and Data',), (
        ('file.link', 'Link...'), ('file.append', 'Append...'),
        ('file.external_data', 'External Data'), ('file.cleanup', 'Clean Up'))),
    ('common.file', ('Project Tools',), (('file.project', 'Blender Project'),)),
    ('common.file', ('View Previews',), (('file.previews', 'Data Previews'),)),
    ('common.edit', ('History',), (
        ('edit.undo_history', 'Undo History'), ('edit.adjust_last', 'Adjust Last Operation...'),
        ('edit.repeat_history', 'Repeat History...'))),
    ('common.edit', ('Search',), (
        ('edit.search', 'Menu Search...'), ('edit.operator_search', 'Operator Search...'))),
    ('common.modify', ('Naming Tools',), (
        ('modify.rename', 'Rename Active Item...'), ('modify.batch_rename', 'Batch Rename...'))),
    ('common.windows', ('Settings/Preferences', 'Startup and Defaults'), (
        ('windows.defaults', 'Defaults'), ('windows.install_template', 'Install Application Template...'),
        ('windows.lock_object_mode', 'Lock Object Modes'))),
    ('common.windows', ('Workspaces', 'Switch Workspace'), (
        ('windows.workspace_next', 'Next Workspace'), ('windows.workspace_previous', 'Previous Workspace'))),
    ('common.windows', ('UI Elements', 'Window Display'), (
        ('windows.fullscreen', 'Toggle Window Fullscreen'), ('windows.statusbar', 'Status Bar'),
        ('windows.stereo', 'Set Stereo 3D'))),
    ('common.windows', ('Window Management',), (
        ('windows.new', 'New Window'), ('windows.new_main', 'New Main Window'),
        ('windows.screenshot', 'Save Screenshot...'),
        ('windows.screenshot_editor', 'Save Screenshot (Editor)...'))),
    ('common.windows', ('Rendering Editors', 'Render'), (('render.native', 'Render'),)),
    ('menubar.rendering.render', ('Render Output',), (
        ('render.image', 'Render Image'), ('render.animation', 'Render Animation'),
        ('render.sequence_image', 'Render Sequence Image'),
        ('render.sequence_animation', 'Render Sequence Animation'),
        ('render.mixdown', 'Render Audio...'), ('render.view_render', 'View Render'),
        ('render.play_animation', 'View Animation'), ('render.lock_interface', 'Lock Interface'))),
    ('menubar.help', ('Blender Help',), (
        ('help.splash', 'Splash Screen'), ('help.about', 'About Blender'),
        ('help.manual', 'Blender Manual'), ('help.support', 'Blender Support'),
        ('help.community', 'Blender Community'), ('help.get_involved', 'Get Involved'),
        ('help.release_notes', 'Blender Release Notes'))),
    ('menubar.help', ('Scripting Reference', 'Blender Development'), (
        ('help.developer_docs', 'Developer Documentation'),
        ('help.developer_community', 'Developer Community'), ('help.api', 'Python API Reference'),
        ('help.cheat_sheet', 'Operator Cheat Sheet'))),
    ('menubar.help', ('Diagnostics',), (
        ('help.report_bug', 'Report a Blender Bug'), ('help.sysinfo', 'Save System Info'),
        ('help.system', 'System'))),
)

EDITOR_PATHS = {
    'editor.outliner': ('General Editors',), 'editor.text': ('General Editors', 'Scripting'),
    'editor.console': ('General Editors', 'Scripting'),
    'editor.geometry_nodes': ('Modeling Editors',), 'editor.uv': ('Modeling Editors',),
    'editor.graph': ('Animation Editors',), 'editor.dopesheet': ('Animation Editors',),
    'editor.nla': ('Animation Editors',), 'editor.shader': ('Rendering Editors',),
    'editor.compositor': ('Rendering Editors',),
}

ROOT_ICONS = {
    'common.file': 'FILE_BLEND', 'common.edit': 'EDITMODE_HLT',
    'common.create': 'ADD', 'common.select': 'RESTRICT_SELECT_OFF',
    'common.modify': 'OBJECT_DATA', 'common.display': 'HIDE_OFF',
    'common.windows': 'WINDOW', 'modeling.mesh': 'MESH_DATA',
    'modeling.edit_mesh': 'EDITMODE_HLT', 'modeling.mesh_tools': 'TOOL_SETTINGS',
    'modeling.mesh_display': 'MESH_DATA', 'modeling.curves': 'CURVE_DATA',
    'modeling.surfaces': 'SURFACE_DATA', 'modeling.deform': 'MODIFIER',
    'modeling.uv': 'UV', 'modeling.generate': 'PARTICLES',
    'menubar.cache': 'FILE_CACHE', 'menubar.help': 'HELP',
}
KEY_ICONS = {
    'file.new': 'FILE_NEW', 'file.new_scene': 'FILE_NEW', 'file.open': 'FILE_FOLDER',
    'file.save': 'FILE_TICK', 'file.save_as': 'FILE_TICK', 'file.save_copy': 'DUPLICATE',
    'file.import': 'IMPORT', 'file.export': 'EXPORT', 'file.quit': 'QUIT',
    'edit.undo': 'LOOP_BACK', 'edit.redo': 'LOOP_FORWARDS', 'edit.undo_history': 'LOOP_BACK',
    'edit.repeat_last': 'FILE_REFRESH', 'edit.search': 'VIEWZOOM',
    'windows.preferences': 'PREFERENCES', 'windows.console': 'CONSOLE',
    'render.image': 'RENDER_STILL', 'render.animation': 'RENDER_ANIMATION',
    'render.mixdown': 'SOUND', 'help.about': 'INFO', 'help.sysinfo': 'INFO',
    'transform.move': 'EMPTY_ARROWS', 'transform.rotate': 'ORIENTATION_GIMBAL',
    'transform.scale': 'FULLSCREEN_ENTER',
    **{'mesh.create_' + name: 'MESH_' + icon for name, icon in (
        ('cube', 'CUBE'), ('sphere', 'UVSPHERE'), ('cylinder', 'CYLINDER'),
        ('cone', 'CONE'), ('plane', 'PLANE'), ('disc', 'CIRCLE'), ('torus', 'TORUS'))},
}


def _apply_icons(root):
    fallback = ROOT_ICONS.get(root['id'], 'TOOL_SETTINGS')
    if root['id'].startswith('menubar.rigging.'):
        fallback = 'OUTLINER_OB_ARMATURE'
    elif root['id'].startswith('menubar.animation.'):
        fallback = 'ACTION'
    elif root['id'].startswith('menubar.fx.'):
        fallback = 'PARTICLES'
    elif root['id'].startswith('menubar.rendering.'):
        fallback = 'RENDER_STILL'
    for node in _walk((root,)):
        key = node.get('native_key') or node.get('command') or ''
        node.setdefault('icon', KEY_ICONS.get(key, fallback))


def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.get('children', ()))


def _node(identifier, label, kind, **values):
    return dict(id=identifier, label=label, kind=kind, children=[], **values)


def _section(root, path):
    """Find real directories; create only named purpose directories, never pages."""
    current = root
    for label in path:
        child = next((item for item in current['children']
                      if item['kind'] == 'menu' and item['label'] == label), None)
        if child is None:
            suffix = sha256((current['id'] + '\0' + label).encode()).hexdigest()[:16]
            child = _node('menubar.section.' + suffix, label, 'menu', origin='blender_section')
            anchor = SECTION_ANCHORS.get((current['id'], label))
            items = current['children']
            if anchor is None:
                items.append(child)
            else:
                start = next((index + 1 for index, item in enumerate(items)
                              if anchor and item['kind'] == 'separator' and item['label'] == anchor), 0)
                end = next((index for index in range(start, len(items))
                            if items[index]['kind'] == 'separator'), len(items))
                items.insert(end, child)
        current = child
    return current


def _extension_path(spec):
    path = SECTION_PATHS.get((spec.category, spec.section[0]), spec.section) if spec.section else ()
    if spec.category == 'Display' and spec.section == ('Viewport Settings',):
        # This registry section exceeds one compact menu. These are functional
        # partitions, independent of item count, window height or source order.
        if any(marker in spec.id for marker in ('.type_', '.show_type_', '.hide_type_')):
            return ('Viewport Settings', 'Object Types')
        if any(word in spec.id for word in ('xray', 'shading', 'backface', 'cavity', 'color', 'studio', 'matcap')):
            return ('Viewport Settings', 'Shading')
        return ('Viewport Settings', 'Overlays')
    return path


def build_menubar():
    candidates = {}
    for spec in SPECS.values():
        for identity in spec.maya:
            candidates.setdefault(identity, []).append(spec.id)

    def convert(reference, root_id):
        result = deepcopy(reference)
        result['children'] = [convert(child, root_id) for child in reference.get('children', ())]
        result['origin'] = 'maya'
        result['reason'] = reference.get('dynamic', '') or ''
        if reference.get('options'):
            result['options'] = dict(reference['options'], kind='disabled',
                                     reason='Maya option parameters are not adapted; this does not execute the main action')
        identity = reference.get('maya_command', '')
        if reference['kind'] not in {'menu', 'separator'}:
            command, reason = _binding(reference, root_id, candidates)
            result.update(kind='command' if command else 'disabled', command=command, reason=reason)
            if identity in NATIVE_BINDINGS:
                result.update(kind='native', native_key=NATIVE_BINDINGS[identity],
                              reason='Uses the corresponding native Blender operation and file format')
            elif identity in ACTION_BINDINGS:
                key = ACTION_BINDINGS[identity]
                result.update(kind='action', action_key=key, icon=ACTIONS[key]['icon'],
                              reason=ACTIONS[key]['reason'])
            if identity == 'ExportSelection':
                result['reason'] = 'Selection export flags are format-specific; use Export All and the native format selection settings'
        elif root_id == 'common.file' and tuple(reference.get('path', ())) == ('File', 'Recent Files'):
            result.update(kind='native', native_key='file.recent',
                          reason='Current Blender recent-file history')
        return result

    menus = [convert(dict(reference, kind='menu'), reference['id']) for reference in REFERENCE_MENUS]
    roots = {root['id']: root for root in menus}
    used_commands = {item.get('command') for item in _walk(menus)}
    for spec in SPECS.values():
        if spec.id in used_commands:
            continue
        parent = _section(roots[CATEGORY_ROOTS[spec.category]], _extension_path(spec))
        parent['children'].append(_node('menubar.command.' + spec.id, spec.label, 'command',
                                        command=spec.id, reason=spec.difference,
                                        origin='blender_extension'))

    for root_id, path, entries in NATIVE_GROUPS:
        root = roots[root_id]
        present = {item.get('native_key') for item in _walk((root,))}
        missing = [(key, label) for key, label in entries if key not in present]
        if not missing:
            continue
        parent = _section(root, path)
        for key, label in missing:
            suffix = sha256((root_id + '\0' + key).encode()).hexdigest()[:16]
            parent['children'].append(_node('menubar.native.' + suffix, label, 'native',
                                            native_key=key, origin='native',
                                            reason='Native Blender operation'))

    used_actions = {item.get('action_key') for item in _walk(menus)}
    for key, metadata in ACTIONS.items():
        if key in used_actions:
            continue
        root = roots[CATEGORY_ROOTS[metadata['category']]]
        path = EDITOR_PATHS[key] if key.startswith('editor.') else metadata['section']
        parent = _section(root, path)
        parent['children'].append(_node('menubar.action.' + key, metadata['label'], 'action',
                                        action_key=key, icon=metadata['icon'],
                                        reason=metadata['reason'], origin='native'))

    # These are construction invariants, independent of UI availability/poll.
    nodes = list(_walk(menus))
    identifiers = [item['id'] for item in nodes]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate menubar node ID')
    if {item.get('native_key') for item in nodes if item.get('native_key')} != NATIVE_KEYS:
        raise ValueError('Native menubar capability inventory is incomplete')
    for item in nodes:
        if item.get('maya_command') in UNAVAILABLE_BINDINGS and item['kind'] != 'disabled':
            raise ValueError('Unadapted Maya semantics became executable')
    for root in menus:
        _apply_icons(root)
    return {'sets': dict(MENU_SETS), 'menus': tuple(menus)}

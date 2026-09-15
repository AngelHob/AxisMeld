# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fixed native object additions and editor windows; metadata imports without bpy."""

_CREATES = {
    'camera': ('Camera', 'camera_add', {}, 'Cameras', 'OUTLINER_OB_CAMERA', 'CreateCameraOnly'),
    'light_sun': ('Sun Light', 'light_add', {'type': 'SUN'}, 'Lights', 'LIGHT_SUN', 'CreateDirectionalLight'),
    'light_point': ('Point Light', 'light_add', {'type': 'POINT'}, 'Lights', 'LIGHT_POINT', 'CreatePointLight'),
    'light_spot': ('Spot Light', 'light_add', {'type': 'SPOT'}, 'Lights', 'LIGHT_SPOT', 'CreateSpotLight'),
    'light_area': ('Area Light', 'light_add', {'type': 'AREA'}, 'Lights', 'LIGHT_AREA', 'CreateAreaLight'),
    'armature': ('Armature', 'armature_add', {}, 'Rigging', 'OUTLINER_OB_ARMATURE', ''),
    'metaball': ('Metaball', 'metaball_add', {'type': 'BALL'}, 'Metaballs', 'OUTLINER_OB_META', ''),
    'volume': ('Empty Volume', 'volume_add', {}, 'Volumes', 'OUTLINER_OB_VOLUME', ''),
    'grease_pencil': ('Empty Grease Pencil', 'grease_pencil_add', {'type': 'EMPTY'}, 'Grease Pencil', 'OUTLINER_OB_GREASEPENCIL', ''),
    'speaker': ('Speaker', 'speaker_add', {}, 'Audio', 'OUTLINER_OB_SPEAKER', ''),
    'force_field': ('Force Field (Force)', 'effector_add', {'type': 'FORCE'}, 'Force Fields', 'OUTLINER_OB_FORCE_FIELD', ''),
}
_EDITORS = {
    'outliner': ('Outliner', 'OUTLINER', None, 'OUTLINER'),
    'shader': ('Shader Editor', 'NODE_EDITOR', 'ShaderNodeTree', 'NODE_MATERIAL'),
    'geometry_nodes': ('Geometry Node Editor', 'NODE_EDITOR', 'GeometryNodeTree', 'GEOMETRY_NODES'),
    'compositor': ('Compositor', 'NODE_EDITOR', 'CompositorNodeTree', 'NODE_COMPOSITING'),
    'graph': ('Graph Editor', 'GRAPH_EDITOR', None, 'GRAPH'),
    'dopesheet': ('Dope Sheet', 'DOPESHEET_EDITOR', None, 'ACTION'),
    'nla': ('Nonlinear Animation', 'NLA_EDITOR', None, 'NLA'),
    'text': ('Text Editor', 'TEXT_EDITOR', None, 'TEXT'),
    'console': ('Python Console', 'CONSOLE', None, 'CONSOLE'),
    'uv': ('UV Editor', 'IMAGE_EDITOR', 'UV', 'UV'),
}
ACTIONS = {}
for _key, (_label, _operator, _props, _section, _icon, _rtc) in _CREATES.items():
    ACTIONS['create.' + _key] = {
        'label': _label, 'category': 'Create', 'section': (_section,), 'icon': _icon,
        'reason': 'Native Blender object and defaults; Maya option parameters are not shared',
    }
    if _rtc:
        ACTIONS['create.' + _key]['maya_command'] = _rtc
for _key, (_label, _type, _subtype, _icon) in _EDITORS.items():
    ACTIONS['editor.' + _key] = {
        'label': _label + ' (New Window)', 'category': 'Windows', 'section': ('Editors',),
        'icon': _icon, 'reason': 'Open a new Blender editor window; existing layouts stay unchanged',
    }


def _identity(value):
    return value.as_pointer() if hasattr(value, 'as_pointer') else id(value)


def _live_window(context):
    window = getattr(context, 'window', None)
    manager = getattr(context, 'window_manager', None)
    return bool(window and manager and
                any(_identity(item) == _identity(window) for item in manager.windows))


def available(context, key):
    import bpy
    if key not in ACTIONS:
        return False, 'Unknown menubar action'
    try:
        if not _live_window(context):
            return False, 'Source window is unavailable'
        if key.startswith('editor.'):
            if bpy.app.background:
                return False, 'Editor windows require the graphical application'
            with bpy.context.temp_override(window=context.window):
                return (True, '') if bpy.ops.wm.window_new.poll() else (False, 'Cannot create a new window')
        if context.mode != 'OBJECT':
            return False, 'Requires Object mode'
        area, region = context.area, context.region
        if not (area and area.type == 'VIEW_3D' and region and region.type == 'WINDOW' and
                any(_identity(item) == _identity(area) for item in context.window.screen.areas) and
                any(_identity(item) == _identity(region) for item in area.regions)):
            return False, 'Requires a live 3D viewport source'
        if not context.scene.is_editable:
            return False, 'Scene is not editable'
        operator = getattr(bpy.ops.object, _CREATES[key[7:]][1])
        with bpy.context.temp_override(window=context.window, area=area, region=region):
            return (True, '') if operator.poll() else (False, 'Native operation is unavailable')
    except (AttributeError, ReferenceError, RuntimeError):
        return False, 'Source context or native operation is unavailable'


def _open_editor(context, key):
    import bpy
    manager = context.window_manager
    before = {_identity(window) for window in manager.windows}
    existing_screens = {_identity(window.screen) for window in manager.windows}
    with bpy.context.temp_override(window=context.window):
        result = bpy.ops.wm.window_new('EXEC_DEFAULT', False)
    created = [window for window in manager.windows if _identity(window) not in before]
    # wm.window_new uses WM_window_open(temp=false): it cannot reuse a window.
    # Still require the exact one-new-window postcondition before modifying UI.
    if len(created) != 1:
        return {'CANCELLED'}
    target = created[0]
    try:
        if result != {'FINISHED'} or _identity(target.screen) in existing_screens or len(target.screen.areas) != 1:
            raise RuntimeError('New editor window did not own an independent single-area screen')
        area = target.screen.areas[0]
        _, area_type, subtype, _ = _EDITORS[key[7:]]
        with bpy.context.temp_override(window=target, area=area):
            area.type = area_type
            if area_type == 'NODE_EDITOR':
                area.spaces.active.tree_type = subtype
                if area.spaces.active.tree_type != subtype:
                    raise RuntimeError('Node editor subtype did not change')
            elif subtype == 'UV':
                area.ui_type = 'UV'
                if area.ui_type != 'UV':
                    raise RuntimeError('UV editor subtype did not change')
            if area.type != area_type:
                raise RuntimeError('Editor type did not change')
        return {'FINISHED'}
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        # Only the uniquely identified window created by this call is closed.
        with bpy.context.temp_override(window=target):
            bpy.ops.wm.window_close('EXEC_DEFAULT', False)
        return {'CANCELLED'}


def run(context, key):
    import bpy
    if not available(context, key)[0]:
        return {'CANCELLED'}
    if key.startswith('editor.'):
        return _open_editor(context, key)
    _, name, props, _, _, _ = _CREATES[key[7:]]
    with bpy.context.temp_override(window=context.window, area=context.area, region=context.region):
        # This is the only undo-owning call: no mode changes or manual undo push.
        return getattr(bpy.ops.object, name)('EXEC_DEFAULT', True, **props)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pinned, read-only source resolution for menubar semantic commands/actions.

Native File/Window/Render draw entries deliberately do not use this module.
"""
from dataclasses import dataclass, replace
import json

# Exact non-SPECS CORE_BINDINGS used by the reviewed Maya menu catalog.
# Do not replace this with all commands.COMMANDS: hotbox triggers and other
# context-specific routes are intentionally outside the menubar executor.
CORE_COMMANDS = frozenset({
    'mesh.create_cone', 'mesh.create_cube', 'mesh.create_cylinder', 'mesh.create_disc',
    'mesh.create_plane', 'mesh.create_sphere', 'mesh.create_torus', 'selection.clear',
    'selection.grow', 'selection.select_all', 'selection.shrink', 'selection.toggle_component',
    'transform.move', 'transform.rotate', 'transform.scale',
})


@dataclass(frozen=True)
class Source:
    window: object
    screen: object
    scene: object
    view_layer: object
    area: object = None
    region: object = None


def _id(value):
    if value is None:
        return 0
    return value.as_pointer()


def _same(left, right):
    return _id(left) == _id(right)


def _base(context):
    window = getattr(context, 'window', None)
    manager = getattr(context, 'window_manager', None)
    if not window or not manager or not any(_same(window, item) for item in manager.windows):
        return None
    screen, scene = window.screen, window.scene
    layer = window.view_layer
    if not screen or not scene or not layer or not _same(scene, context.scene):
        return None
    return Source(window, screen, scene, layer)


def _visible(value):
    return value.width > 1 and value.height > 1


def _order(value):
    # Equal-area quad panes are deterministic: leftmost, then bottommost.
    return (-value.width * value.height, value.x, value.y, _id(value))


def _regions(area):
    return [item for item in area.regions if item.type == 'WINDOW' and _visible(item)]


def resolve_source(context):
    """Current 3D WINDOW first; otherwise largest visible area in this window.

    In a quad area a directly supplied WINDOW region wins. Without one, choose
    the largest visible pane, resolving ties left-to-right then bottom-to-top.
    Never inspect or change another window, mode, selection, or workspace.
    """
    try:
        base = _base(context)
        if base is None:
            return None
        areas = [item for item in base.screen.areas
                 if item.type == 'VIEW_3D' and _visible(item) and _regions(item)]
        current = getattr(context, 'area', None)
        area = next((item for item in areas if _same(item, current)), None)
        if area is None:
            area = min(areas, key=_order) if areas else None
        if area is None:
            return None
        regions = _regions(area)
        current_region = getattr(context, 'region', None)
        region = next((item for item in regions if _same(item, current_region)), None)
        if region is None:
            region = min(regions, key=_order)
        return replace(base, area=area, region=region)
    except (AttributeError, ReferenceError, RuntimeError):
        return None


def source_token(context):
    """Capture source identities, including window-only tokens without a 3D view.

    Tokens are session-local pointer identities, not durable configuration. UI
    operators store this exact string at draw time and pass it back at execute.
    """
    try:
        source = resolve_source(context) or _base(context)
        if source is None:
            return ''
        return json.dumps([1, _id(source.window), _id(source.screen), _id(source.scene),
                           _id(source.view_layer), _id(source.area), _id(source.region)],
                          separators=(',', ':'))
    except (AttributeError, ReferenceError, RuntimeError):
        return ''


def _from_token(context, token, needs_viewport):
    if not isinstance(token, str) or not token or len(token) > 512:
        return None
    try:
        ids = json.loads(token)
        if (not isinstance(ids, list) or len(ids) != 7 or
                any(type(value) is not int or value < 0 for value in ids) or
                ids[0] != 1 or not all(ids[1:5]) or bool(ids[5]) != bool(ids[6])):
            return None
        base = _base(context)
        if base is None or ids[1:5] != [_id(base.window), _id(base.screen),
                                      _id(base.scene), _id(base.view_layer)]:
            return None
        if not needs_viewport:
            return base
        area = next((item for item in base.screen.areas if _id(item) == ids[5]), None)
        if area is None or area.type != 'VIEW_3D' or not _visible(area):
            return None
        region = next((item for item in _regions(area) if _id(item) == ids[6]), None)
        return replace(base, area=area, region=region) if region is not None else None
    except (AttributeError, ReferenceError, RuntimeError, ValueError, TypeError):
        return None


def _backend(kind, key):
    if kind == 'command':
        if key in CORE_COMMANDS:
            from . import adapter
            return adapter
        from . import modeling_adapter
        return modeling_adapter if key in modeling_adapter.SPECS else None
    if kind == 'action':
        from . import menubar_actions
        return menubar_actions if key in menubar_actions.ACTIONS else None
    return None


def _prepare(context, kind, key, token):
    if not isinstance(kind, str) or not isinstance(key, str):
        return None, None
    backend = _backend(kind, key)
    if backend is None:
        return None, None
    needs_viewport = not (kind == 'action' and key.startswith('editor.'))
    captured = token if token else source_token(context)
    return backend, _from_token(context, captured, needs_viewport)


def _override(source):
    import bpy
    kwargs = {'window': source.window, 'scene': source.scene, 'view_layer': source.view_layer}
    if source.area is not None:
        kwargs.update(area=source.area, region=source.region)
    return bpy.context.temp_override(**kwargs)


def available(context, kind, key, token=''):
    """Read current eligibility under the captured source; native keys reject."""
    import bpy
    try:
        backend, source = _prepare(context, kind, key, token)
        if backend is None:
            return False, 'Unknown menubar command or action'
        if source is None:
            return False, 'Captured source is unavailable; a live 3D viewport is required for modeling'
        with _override(source):
            return backend.available(bpy.context, key)
    except (AttributeError, ReferenceError, RuntimeError, ValueError):
        return False, 'Source context or native operation is unavailable'


def run(context, kind, key, token=''):
    """Submit only with a valid draw-time token; never fall back after capture.

    The backend owns native undo/modal behavior. No wrapper undo push, mode
    change, selection mutation, or Recent insertion occurs here.
    """
    import bpy
    if not token:
        return {'CANCELLED'}
    backend, source = _prepare(context, kind, key, token)
    if backend is None or source is None:
        return {'CANCELLED'}
    with _override(source):
        if not backend.available(bpy.context, key)[0]:
            return {'CANCELLED'}
        return backend.run(bpy.context, key)


def state(context, kind, key, token=''):
    """Return actual source state as (indicator, bool), or None when unknown."""
    import bpy
    if kind != 'command':
        return None
    try:
        backend, source = _prepare(context, kind, key, token)
        if backend is None or source is None:
            return None
        with _override(source):
            value = backend.command_state(bpy.context, key)
        if (isinstance(value, tuple) and len(value) == 2 and
                value[0] in {'checkbox', 'radio'} and type(value[1]) is bool):
            return value
    except (AttributeError, ReferenceError, RuntimeError, ValueError):
        pass
    return None

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Runtime construction of validated hotbox JSON snapshots."""
from copy import deepcopy
import json
from threading import Lock

from .commands import COMMANDS, PRESET_NAME
from .hotbox_catalog import default_catalog, command_policy
from .hotbox_profiles import CANONICAL_ROWS, DEFAULT_SETTINGS, resolve_hotbox, validate_settings


MAX_NODES = 256
MAX_DEPTH = 8
MAX_JSON_BYTES = 256 * 1024
MAX_TEXT = 128
NODE_KINDS = frozenset({'menu', 'command', 'separator', 'disabled', 'setting'})
NODE_FIELDS = frozenset({'id', 'kind', 'label', 'command', 'enabled', 'reason', 'children'})
SETTING_VALUES = {
    'style': frozenset({'rows', 'zones', 'center'}),
    'transparency': frozenset({'0', '25', '50', '75', '100'}),
    'row.common': frozenset({'toggle'}),
    'row.pane': frozenset({'toggle'}),
    'row.modeling': frozenset({'toggle'}),
}

_generation = 0
_generation_lock = Lock()
_settings = deepcopy(DEFAULT_SETTINGS)
diagnostics = []

# Deliberately independent of the general adapter registry: new-window/file and interactive
# navigation actions must not become callable through this batch's menu bridge.
SUPPORTED_COMMANDS = frozenset({
    'view.perspective', 'view.side', 'view.bottom', 'view.front', 'view.back',
    'view.top', 'view.left', 'view.focus_selected', 'view.frame_all', 'view.wireframe',
    'view.shaded', 'view.toggle_quad', 'selection.toggle_component', 'selection.vertex_mode',
    'selection.edge_mode', 'selection.face_mode', 'transform.move', 'transform.rotate',
    'transform.scale',
})


class RecentCommands:
    """Session-only semantic IDs; never retains object references or file paths."""
    def __init__(self):
        self._items = []

    def record(self, command):
        if not isinstance(command, str) or command not in SUPPORTED_COMMANDS or not command_policy(command)[1]:
            return
        self._items = [command] + [item for item in self._items if item != command]
        del self._items[10:]

    def items(self):
        return tuple(self._items)


recent = RecentCommands()


def dispatch(context, command):
    """Recheck live availability and record only synchronous successful menu commands."""
    if not isinstance(command, str) or command not in SUPPORTED_COMMANDS:
        return {'CANCELLED'}
    from . import adapter
    config = context.window_manager.keyconfigs.active
    if config is None or config.name != PRESET_NAME:
        return {'CANCELLED'}
    try:
        available, _reason = adapter.available(context, command)
        if not available:
            return {'CANCELLED'}
        result = adapter.run(context, command, invoke=True)
    except Exception:
        return {'CANCELLED'}
    if result == {'FINISHED'}:
        recent.record(command)
    return result


def apply_setting(context, setting, value):
    """Apply a single validated menu setting to this session, without disk writes."""
    global _settings
    if (not isinstance(setting, str) or setting not in SETTING_VALUES or
            not isinstance(value, str) or value not in SETTING_VALUES[setting]):
        raise ValueError('Unknown hotbox setting or option')
    candidate = deepcopy(_settings)
    if setting.startswith('row.'):
        row = setting.removeprefix('row.')
        rows = set(candidate['rows'])
        rows.symmetric_difference_update({row})
        candidate['rows'] = [item for item in CANONICAL_ROWS if item in rows]
    else:
        candidate[setting] = int(value) if setting == 'transparency' else value
    validate_settings(candidate)
    _settings = candidate


def reload_settings(context, *, session=None):
    """Resolve baseline plus optional session layer; file/prefs loading belongs to Task5."""
    global _settings, diagnostics
    value, errors = resolve_hotbox([] if session is None else [('session', session)])
    _settings = value['settings']
    diagnostics = errors


def _next_generation():
    global _generation
    with _generation_lock:
        _generation += 1
        return _generation


def _validate_text(value, name, *, ascii_only=False, nonempty=False, max_length=None):
    if not isinstance(value, str):
        raise ValueError(f'{name} must be a string')
    if nonempty and not value:
        raise ValueError(f'{name} must not be empty')
    if max_length is not None and len(value) > max_length:
        raise ValueError(f'{name} exceeds {max_length} characters')
    if ascii_only and not value.isascii():
        raise ValueError(f'{name} must contain ASCII characters only')


def validate_snapshot(value):
    """Strictly validate the complete Python-to-native snapshot contract."""
    if not isinstance(value, dict) or set(value) != {
            'schema_version', 'generation', 'settings', 'menus'}:
        raise ValueError('snapshot contains unknown or missing fields')
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValueError('schema_version must be integer 1')
    if type(value['generation']) is not int or value['generation'] <= 0:
        raise ValueError('generation must be a positive integer')
    validate_settings(value['settings'])
    menus = value['menus']
    if not isinstance(menus, list):
        raise ValueError('menus must be an array')
    if not all(isinstance(node, dict) for node in menus):
        raise ValueError('root menu groups must be objects')
    if [node.get('id') for node in menus] != [
            'common', 'pane', 'center', 'modeling']:
        raise ValueError('root menus must be common, pane, center and modeling in order')
    if not all(node.get('kind') == 'menu' for node in menus):
        raise ValueError('root menu groups must have menu kind')

    identifiers = set()
    menu_ids = set()
    active = set()
    count = 0

    def visit(node, depth):
        nonlocal count
        if depth > MAX_DEPTH:
            raise ValueError(f'menu depth exceeds {MAX_DEPTH}')
        identity = id(node)
        if identity in active:
            raise ValueError('menu tree contains a cycle')
        if not isinstance(node, dict):
            raise ValueError('menu node must be an object')
        fields = set(node)
        if not NODE_FIELDS <= fields or fields - (NODE_FIELDS | {'value'}):
            raise ValueError('menu node contains unknown or missing fields')

        identifier = node['id']
        _validate_text(identifier, 'node id', ascii_only=True, nonempty=True, max_length=MAX_TEXT)
        if identifier.startswith('@scroll:'):
            raise ValueError('node id uses reserved layout control prefix')
        if identifier in identifiers:
            raise ValueError(f'duplicate menu node id: {identifier}')
        identifiers.add(identifier)
        count += 1
        if count > MAX_NODES:
            raise ValueError(f'menu tree exceeds {MAX_NODES} nodes')

        kind = node['kind']
        if not isinstance(kind, str) or kind not in NODE_KINDS:
            raise ValueError('unknown menu node kind')
        _validate_text(node['label'], 'node label', max_length=MAX_TEXT)
        _validate_text(node['command'], 'node command')
        _validate_text(node['reason'], 'node reason')
        if type(node['enabled']) is not bool:
            raise ValueError('node enabled must be boolean')
        children = node['children']
        if not isinstance(children, list):
            raise ValueError('node children must be an array')
        item_value = node.get('value', '')
        if not isinstance(item_value, str):
            raise ValueError('node value must be a string')

        if kind == 'menu':
            if node['command'] or item_value:
                raise ValueError('menu nodes cannot carry command or value')
            menu_ids.add(identifier)
        elif children:
            raise ValueError('only menu nodes can have children')
        elif kind == 'command':
            if node['command'] not in COMMANDS:
                raise ValueError(f'unknown command ID: {node["command"]}')
            if item_value:
                raise ValueError('non-setting value must be empty')
        elif kind == 'setting':
            if node['command'] not in SETTING_VALUES or item_value not in SETTING_VALUES[node['command']]:
                raise ValueError('unknown setting ID or option')
        else:
            if node['command'] or item_value:
                raise ValueError('non-setting value and command must be empty')
            if kind in {'separator', 'disabled'} and node['enabled']:
                raise ValueError(f'{kind} nodes cannot be enabled')
            if kind == 'disabled' and not node['reason']:
                raise ValueError('disabled nodes require a reason')

        active.add(identity)
        try:
            for child in children:
                visit(child, depth + 1)
        finally:
            active.remove(identity)

    for root in menus:
        visit(root, 1)
    for button, menu_id in value['settings']['center_buttons'].items():
        if menu_id is not None and menu_id not in menu_ids:
            raise ValueError(f'{button} references an unresolved menu ID')
    return value


def make_snapshot(*, generation, settings=None, menus=None):
    """Build and validate an independent snapshot document."""
    value = {
        'schema_version': 1,
        'generation': generation,
        'settings': deepcopy(DEFAULT_SETTINGS if settings is None else settings),
        'menus': list(deepcopy(default_catalog() if menus is None else menus)),
    }
    validate_snapshot(value)
    return value


def serialize_snapshot(value):
    """Validate and serialize a snapshot within the native boundary limit."""
    validate_snapshot(value)
    try:
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False,
                             separators=(',', ':'), sort_keys=True)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError(f'snapshot is not JSON serializable: {error}') from error
    if len(payload.encode('utf-8')) > MAX_JSON_BYTES:
        raise ValueError('snapshot exceeds 256 KiB')
    return payload


def _apply_runtime_capabilities(context, menus):
    # Importing adapter imports bpy, so keep it out of module initialization and pure tests.
    from . import adapter

    pending = list(menus)
    while pending:
        node = pending.pop()
        pending.extend(node['children'])
        if node['kind'] != 'command' or not node['enabled']:
            continue
        enabled, reason = adapter.available(context, node['command'])
        node['enabled'] = bool(enabled)
        node['reason'] = '' if enabled else str(reason)
    return menus


def snapshot(context):
    """Return a capability-resolved snapshot for a live Blender context."""
    menus = _apply_runtime_capabilities(context, default_catalog())
    return serialize_snapshot(make_snapshot(generation=_next_generation(), settings=_settings, menus=menus))

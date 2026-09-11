# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Runtime construction of validated hotbox JSON snapshots."""
from copy import deepcopy
import json
import logging
from threading import Lock

from .commands import COMMANDS, PRESET_NAME
from .tool_hotbox import DIRECTIONS, MENU_COMMANDS
from .hotbox_catalog import default_catalog, command_policy
from .hotbox_profiles import (CANONICAL_ROWS, DEFAULT_APPEARANCE, DEFAULT_SETTINGS, MENU_IDS, MOUSE_BUTTONS,
                              load_hotbox_profiles, resolve_hotbox, save_hotbox_user,
                              validate_settings)


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
    **{f'center.{button}': frozenset({'none', *MENU_IDS}) for button in MOUSE_BUTTONS},
}

_generation = 0
_generation_lock = Lock()
_settings = deepcopy(DEFAULT_SETTINGS)
diagnostics = []
_syncing_preferences = False
_session_document = {'schema_version': 1, 'settings': {}}

# Deliberately independent of the general adapter registry: new-window/file and interactive
# navigation actions must not become callable through this batch's menu bridge.
SUPPORTED_COMMANDS = frozenset({
    *MENU_COMMANDS,
    'view.perspective', 'view.side', 'view.bottom', 'view.front', 'view.back',
    'view.top', 'view.left', 'view.focus_selected', 'view.frame_all', 'view.wireframe',
    'view.shaded', 'view.toggle_quad', 'selection.toggle_component', 'selection.vertex_mode',
    'selection.edge_mode', 'selection.face_mode', 'selection.select_all', 'selection.grow',
    'selection.shrink', 'transform.move', 'transform.rotate', 'transform.scale',
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
    except Exception as error:
        logging.getLogger(__name__).error(
            'Hotbox command %s failed: %s: %s', command, type(error).__name__, error)
        return {'CANCELLED'}
    if result == {'FINISHED'}:
        recent.record(command)
    return result


def apply_setting(context, setting, value):
    """Apply one setting through the shared Controls/Preferences persistence path."""
    if (not isinstance(setting, str) or setting not in SETTING_VALUES or
            not isinstance(value, str) or value not in SETTING_VALUES[setting]):
        raise ValueError('Unknown hotbox setting or option')
    candidate = _settings_with_change(_settings, setting, value)
    _commit_settings(context, candidate, [setting])


def apply_appearance(context, field, value):
    """Typed preferences boundary, separate from executable menu setting commands."""
    if not isinstance(field, str) or field not in DEFAULT_APPEARANCE:
        raise ValueError('Unknown appearance field')
    candidate = deepcopy(_settings)
    candidate['appearance'][field] = deepcopy(value)
    validate_settings(candidate)
    _commit_settings(context, candidate, [f'appearance.{field}'])


def reset_appearance(context):
    candidate = deepcopy(_settings)
    candidate['appearance'] = deepcopy(DEFAULT_APPEARANCE)
    candidate['transparency'] = DEFAULT_SETTINGS['transparency']
    _commit_settings(context, candidate,
                     ['transparency', *(f'appearance.{key}' for key in DEFAULT_APPEARANCE)])


def _commit_settings(context, candidate, changed):
    global _settings
    if _file_overrides_enabled(context):
        from . import runtime
        directory = runtime.profile_directory()
        if directory is None:
            raise ValueError('No configuration directory for hotbox_user.json')
        persisted, _errors = load_hotbox_profiles(directory)
        persisted_settings = deepcopy(persisted['settings'])
        for setting in changed:
            if setting.startswith(('center.', 'appearance.')):
                group, key = setting.split('.', 1)
                model_key = 'center_buttons' if group == 'center' else group
                persisted_settings[model_key][key] = deepcopy(candidate[model_key][key])
            else:
                model_key = 'rows' if setting.startswith('row.') else setting
                persisted_settings[model_key] = deepcopy(candidate[model_key])
        try:
            save_hotbox_user(directory, persisted_settings)
        except (OSError, ValueError) as error:
            raise ValueError(str(error)) from error
        for setting in changed:
            _remove_session_setting(setting)
        reload_settings(context)
    else:
        for setting in changed:
            _store_session_setting(setting, candidate)
        _settings = candidate
        _sync_preferences(context)


def _settings_with_change(base, setting, value):
    candidate = deepcopy(base)
    if setting.startswith('row.'):
        row = setting.removeprefix('row.')
        rows = set(candidate['rows'])
        rows.symmetric_difference_update({row})
        candidate['rows'] = [item for item in CANONICAL_ROWS if item in rows]
    elif setting.startswith('center.'):
        candidate['center_buttons'][setting.removeprefix('center.')] = (
            None if value == 'none' else value)
    else:
        candidate[setting] = int(value) if setting == 'transparency' else value
    validate_settings(candidate)
    return candidate


def _store_session_setting(setting, settings):
    patch = _session_document['settings']
    if setting.startswith('row.'):
        patch['rows'] = deepcopy(settings['rows'])
    elif setting.startswith('appearance.'):
        key = setting.removeprefix('appearance.')
        patch.setdefault('appearance', {})[key] = deepcopy(settings['appearance'][key])
    elif setting.startswith('center.'):
        button = setting.removeprefix('center.')
        patch.setdefault('center_buttons', {})[button] = settings['center_buttons'][button]
    else:
        patch[setting] = deepcopy(settings[setting])


def _remove_session_setting(setting):
    patch = _session_document['settings']
    if setting.startswith('row.'):
        patch.pop('rows', None)
    elif setting.startswith('appearance.'):
        appearance = patch.get('appearance', {})
        appearance.pop(setting.removeprefix('appearance.'), None)
        if not appearance:
            patch.pop('appearance', None)
    elif setting.startswith('center.'):
        buttons = patch.get('center_buttons', {})
        buttons.pop(setting.removeprefix('center.'), None)
        if not buttons:
            patch.pop('center_buttons', None)
    else:
        patch.pop(setting, None)


def reload_settings(context, *, session=None):
    """Resolve baseline/file/session layers and update non-owning Preferences controls."""
    global _settings, diagnostics, _session_document
    session_errors = []
    if session is not None:
        _candidate, session_errors = resolve_hotbox([('session', session)])
        if not session_errors:
            _session_document = deepcopy(session)
    active_session = _session_document
    if _file_overrides_enabled(context):
        from . import runtime
        directory = runtime.profile_directory()
        if directory is not None:
            value, errors = load_hotbox_profiles(directory, session=active_session)
        else:
            value, errors = resolve_hotbox([('session', active_session)])
    else:
        value, errors = resolve_hotbox([('session', active_session)])
    _settings = value['settings']
    diagnostics = session_errors + errors
    _sync_preferences(context)


def current_settings():
    return deepcopy(_settings)


def preferences_are_syncing():
    return _syncing_preferences


def settings_storage_note(context):
    if not _file_overrides_enabled(context):
        return 'Session only: file overrides are disabled; Controls changes are not saved'
    from . import runtime
    directory = runtime.profile_directory()
    return f'User settings: {directory / "hotbox_user.json"}' if directory else 'No configuration directory'


def _preferences(context):
    try:
        configs = context.window_manager.keyconfigs
        config = configs.get(PRESET_NAME)
        return config.preferences if config is not None else None
    except (AttributeError, RuntimeError):
        return None


def _file_overrides_enabled(context):
    preferences = _preferences(context)
    return True if preferences is None else bool(preferences.use_file_overrides)


def _sync_preferences(context):
    global _syncing_preferences
    preferences = _preferences(context)
    if preferences is None or not hasattr(preferences, 'hotbox_style'):
        return
    _syncing_preferences = True
    try:
        preferences.hotbox_style = _settings['style']
        preferences.hotbox_transparency = str(_settings['transparency'])
        for key, value in _settings['appearance'].items():
            if isinstance(value, list):
                value = tuple(channel/255 for channel in value)
            setattr(preferences, f'hotbox_{key}', value)
        for row in CANONICAL_ROWS:
            setattr(preferences, f'hotbox_row_{row}', row in _settings['rows'])
        for button in MOUSE_BUTTONS:
            setattr(preferences, f'hotbox_center_{button.lower()}',
                    _settings['center_buttons'][button] or 'none')
    finally:
        _syncing_preferences = False


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
    center_setting_menu_ids = set()
    active = set()
    count = 0

    def visit(node, depth, parent_presentation=''):
        nonlocal count
        if depth > MAX_DEPTH:
            raise ValueError(f'menu depth exceeds {MAX_DEPTH}')
        identity = id(node)
        if identity in active:
            raise ValueError('menu tree contains a cycle')
        if not isinstance(node, dict):
            raise ValueError('menu node must be an object')
        fields = set(node)
        if not NODE_FIELDS <= fields or fields - (NODE_FIELDS | {'value', 'direction', 'presentation'}):
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
        if 'direction' in node:
            if (not isinstance(node['direction'], str) or node['direction'] not in DIRECTIONS or
                    parent_presentation != 'radial' or kind == 'separator'):
                raise ValueError('invalid direction or placement')
        if 'presentation' in node:
            if kind != 'menu' or node['presentation'] not in ('radial', 'list'):
                raise ValueError('invalid menu presentation')
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
            if node['command'].startswith('center.') and item_value != 'none':
                center_setting_menu_ids.add(item_value)
        else:
            if node['command'] or item_value:
                raise ValueError('non-setting value and command must be empty')
            if kind in {'separator', 'disabled'} and node['enabled']:
                raise ValueError(f'{kind} nodes cannot be enabled')
            if kind == 'disabled' and not node['reason']:
                raise ValueError('disabled nodes require a reason')

        active.add(identity)
        try:
            directions = [child.get('direction') for child in children
                          if isinstance(child, dict) and 'direction' in child]
            if any(directions.count(direction) > 1 for direction in directions):
                raise ValueError('duplicate direction in ring')
            for child in children:
                visit(child, depth + 1, node.get('presentation', ''))
        finally:
            active.remove(identity)

    for root in menus:
        visit(root, 1)
    if not center_setting_menu_ids <= menu_ids:
        raise ValueError('center setting references an unresolved menu ID')
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
        'menus': list(deepcopy(_catalog_with_recent() if menus is None else menus)),
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


def _catalog_with_recent():
    menus = default_catalog()
    center = next(node for node in menus if node['id'] == 'center')
    recent_menu = next(node for node in center['children'] if node['id'] == 'center.recent')
    recent_menu['children'] = [{
        'id': f'center.recent.{index}.{command.replace(".", "_")}',
        'kind': 'command',
        'label': COMMANDS[command].label,
        'command': command,
        'enabled': True,
        'reason': '',
        'children': [],
    } for index, command in enumerate(recent.items())]
    recent_menu['enabled'] = bool(recent_menu['children'])
    recent_menu['reason'] = '' if recent_menu['enabled'] else 'No recent commands in this session'
    return menus


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
    menus = _apply_runtime_capabilities(context, _catalog_with_recent())
    return serialize_snapshot(make_snapshot(generation=_next_generation(), settings=_settings, menus=menus))

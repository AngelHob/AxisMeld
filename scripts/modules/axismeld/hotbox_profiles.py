# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Strict, atomic layering for non-executable hotbox settings."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile

from .hotbox_catalog import default_catalog


HOTBOX_PROFILE_FILENAMES = ('hotbox_studio.json', 'hotbox_user.json')
CANONICAL_ROWS = ('common', 'pane', 'modeling')
MOUSE_BUTTONS = ('LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE')
SETTING_KEYS = frozenset({'style', 'transparency', 'rows', 'center_buttons'})
DEFAULT_SETTINGS = {
    'style': 'rows',
    'transparency': 75,
    'rows': list(CANONICAL_ROWS),
    'center_buttons': {button: 'views' for button in MOUSE_BUTTONS},
}


def _menu_ids():
    result = set()
    pending = list(default_catalog())
    while pending:
        node = pending.pop()
        if node['kind'] == 'menu':
            result.add(node['id'])
        pending.extend(node['children'])
    return frozenset(result)


MENU_IDS = _menu_ids()


def _validate_rows(rows):
    if not isinstance(rows, list) or any(not isinstance(row, str) for row in rows):
        raise ValueError('rows must be a list of row IDs')
    expected = [row for row in CANONICAL_ROWS if row in rows]
    if rows != expected:
        raise ValueError('rows must be a unique canonical-order subset')


def _validate_center_buttons(center_buttons, *, partial):
    if not isinstance(center_buttons, dict):
        raise ValueError('center_buttons must be an object')
    keys = set(center_buttons)
    expected = set(MOUSE_BUTTONS)
    if (not partial and keys != expected) or (partial and not keys <= expected):
        raise ValueError('center_buttons contains an unknown or missing mouse button')
    for button, menu_id in center_buttons.items():
        if menu_id is not None and (not isinstance(menu_id, str) or menu_id not in MENU_IDS):
            raise ValueError(f'{button} must reference a menu ID or null')


def validate_settings(settings):
    """Validate a fully resolved settings object and return it unchanged."""
    if not isinstance(settings, dict) or set(settings) != SETTING_KEYS:
        raise ValueError('settings contains unknown or missing fields')
    if not isinstance(settings['style'], str) or settings['style'] not in {'rows', 'zones', 'center'}:
        raise ValueError('style must be rows, zones or center')
    transparency = settings['transparency']
    if type(transparency) is not int or transparency not in {0, 25, 50, 75, 100}:
        raise ValueError('transparency must be 0, 25, 50, 75 or 100')
    _validate_rows(settings['rows'])
    _validate_center_buttons(settings['center_buttons'], partial=False)
    return settings


def _validate_layer_document(document):
    if not isinstance(document, dict) or set(document) != {'schema_version', 'settings'}:
        raise ValueError('expected schema_version and settings')
    if type(document['schema_version']) is not int or document['schema_version'] != 1:
        raise ValueError('unsupported schema_version; expected 1')
    settings = document['settings']
    if not isinstance(settings, dict) or set(settings) - SETTING_KEYS:
        raise ValueError('settings must be an object containing only known fields')
    if 'style' in settings and (not isinstance(settings['style'], str) or
                                settings['style'] not in {'rows', 'zones', 'center'}):
        raise ValueError('style must be rows, zones or center')
    if 'transparency' in settings:
        transparency = settings['transparency']
        if type(transparency) is not int or transparency not in {0, 25, 50, 75, 100}:
            raise ValueError('transparency must be 0, 25, 50, 75 or 100')
    if 'rows' in settings:
        _validate_rows(settings['rows'])
    if 'center_buttons' in settings:
        _validate_center_buttons(settings['center_buttons'], partial=True)


def apply_validated_layer(base, patch, validate=validate_settings):
    """Apply one already-schema-checked layer to a copy, then validate it."""
    candidate = deepcopy(base)
    for key, value in patch.get('settings', {}).items():
        if key == 'center_buttons':
            candidate['settings'][key].update(value)
        else:
            candidate['settings'][key] = deepcopy(value)
    validate(candidate['settings'])
    return candidate


def resolve_hotbox(layers=()):
    """Resolve default→studio→user→session layers with per-layer rollback."""
    value = {'schema_version': 1, 'settings': deepcopy(DEFAULT_SETTINGS)}
    diagnostics = []
    for name, document in layers:
        try:
            _validate_layer_document(document)
            candidate = apply_validated_layer(value, document)
        except (KeyError, RecursionError, TypeError, ValueError) as error:
            diagnostics.append(f'{name}: {error}; using the previous valid layer')
            continue
        value = candidate
    return deepcopy(value), diagnostics


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _read_document(path):
    with Path(path).open('rb') as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError('profile exceeds 64 KiB')
    document = json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique_object)
    _validate_layer_document(document)
    return document


def load_hotbox_profiles(config_dir, session=None):
    """Load strict studio/user settings with per-file diagnostics and optional session layer."""
    layers, diagnostics = [], []
    for name, filename in zip(('studio', 'user'), HOTBOX_PROFILE_FILENAMES):
        path = Path(config_dir) / filename
        try:
            layers.append((name, _read_document(path)))
        except FileNotFoundError:
            pass
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            diagnostics.append(f'hotbox {name}: {error}; file left unchanged')
    if session is not None:
        layers.append(('session', session))
    value, layer_errors = resolve_hotbox(layers)
    return value, diagnostics + layer_errors


def _settings_delta(base, settings):
    delta = {}
    for key in ('style', 'transparency', 'rows'):
        if settings[key] != base[key]:
            delta[key] = deepcopy(settings[key])
    buttons = {button: settings['center_buttons'][button]
               for button in MOUSE_BUTTONS
               if settings['center_buttons'][button] != base['center_buttons'][button]}
    if buttons:
        delta['center_buttons'] = buttons
    return delta


def save_hotbox_user(config_dir, settings):
    """Atomically replace only the validated user settings delta; never repair bad input."""
    validate_settings(settings)
    root = Path(config_dir)
    studio_path = root / HOTBOX_PROFILE_FILENAMES[0]
    user_path = root / HOTBOX_PROFILE_FILENAMES[1]
    try:
        studio = _read_document(studio_path)
    except FileNotFoundError:
        studio = None
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise ValueError(f'existing hotbox_studio.json is invalid: {error}') from error
    try:
        _read_document(user_path)
    except FileNotFoundError:
        pass
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise ValueError(f'existing hotbox_user.json is invalid: {error}') from error

    base_layers = [] if studio is None else [('studio', studio)]
    base, errors = resolve_hotbox(base_layers)
    if errors:
        raise ValueError(errors[0])
    document = {'schema_version': 1,
                'settings': _settings_delta(base['settings'], settings)}
    _validate_layer_document(document)
    resolved, errors = resolve_hotbox([*base_layers, ('user', document)])
    if errors or resolved['settings'] != settings:
        raise ValueError('user hotbox settings failed round-trip validation')

    root.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(document, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=root, prefix='.hotbox_user.json.',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _read_document(temporary)
        os.replace(temporary, user_path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    return deepcopy(document)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Strict, atomic layering for non-executable hotbox settings."""
from copy import deepcopy

from .hotbox_catalog import default_catalog


HOTBOX_PROFILE_FILENAMES = ('hotbox_studio.json', 'hotbox_user.json')
CANONICAL_ROWS = ('common', 'pane', 'modeling')
MOUSE_BUTTONS = ('LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE')
SETTING_KEYS = frozenset({'style', 'transparency', 'rows', 'center_buttons'})
DEFAULT_SETTINGS = {
    'style': 'rows',
    'transparency': 25,
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

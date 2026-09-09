# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Validate and resolve non-executable, delta-only profile layers without bpy."""
from dataclasses import dataclass
import json
from pathlib import Path

from .commands import baseline_bindings

MODIFIERS = ('ctrl', 'shift', 'alt', 'oskey')
KEY_TYPES = frozenset((*'ABCDEFGHIJKLMNOPQRSTUVWXYZ', *(f'F{i}' for i in range(1, 25)),
                       'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
                       'SPACE', 'TAB', 'RET', 'BACK_SPACE', 'DEL', 'INSERT', 'HOME', 'END',
                       'PAGE_UP', 'PAGE_DOWN', 'LEFT_ARROW', 'RIGHT_ARROW', 'UP_ARROW', 'DOWN_ARROW',
                       'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'COMMA', 'PERIOD', 'SLASH',
                       'SEMI_COLON', 'QUOTE', 'LEFT_BRACKET', 'RIGHT_BRACKET', 'MINUS', 'EQUAL'))


@dataclass
class ResolvedProfile:
    bindings: dict
    sources: dict
    diagnostics: list


def normalize_event(event):
    if not isinstance(event, dict) or set(event) - {'type', 'value', *MODIFIERS}:
        raise ValueError('event must contain only type, value and boolean modifiers')
    if not isinstance(event.get('type'), str) or event['type'] not in KEY_TYPES:
        raise ValueError('unsupported event type')
    if event.get('value', 'PRESS') != 'PRESS':
        raise ValueError('this profile version supports PRESS only')
    if any(type(event.get(key, False)) is not bool for key in MODIFIERS):
        raise ValueError('modifiers must be boolean')
    return {'type': event['type'], 'value': 'PRESS', **{key: event.get(key, False) for key in MODIFIERS}}


def event_signature(event):
    return (event['type'], *(event.get(key, False) for key in MODIFIERS))


def _apply(bindings, document):
    if not isinstance(document, dict) or set(document) != {'schema_version', 'bindings'}:
        raise ValueError('expected schema_version and bindings')
    if type(document['schema_version']) is not int or document['schema_version'] != 1:
        raise ValueError('unsupported schema_version; expected 1')
    changes = document['bindings']
    if not isinstance(changes, dict) or changes.keys() - bindings.keys():
        raise ValueError('unknown command or invalid bindings object')
    candidate = {key: (dict(value) if value else None) for key, value in bindings.items()}
    for command, event in changes.items():
        candidate[command] = normalize_event(event) if event is not None else None
    seen = {}
    for command, event in candidate.items():
        if event is None:
            continue
        signature = event_signature(event)
        if signature in seen:
            raise ValueError(f'input conflict: {seen[signature]} and {command}')
        seen[signature] = command
    return candidate


def resolve_profiles(layers=(), *, validate=None):
    result = ResolvedProfile(baseline_bindings(), {key: 'maya2026-default' for key in baseline_bindings()}, [])
    for name, document in layers:
        try:
            candidate = _apply(result.bindings, document)
            if validate is not None:
                validate(candidate)
        except (ValueError, TypeError) as error:
            result.diagnostics.append(f'{name}: {error}; using the previous valid layer')
            continue
        result.bindings = candidate
        result.sources.update({key: name for key in document['bindings']})
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load_profiles(config_dir, session=None, *, validate=None):
    layers, diagnostics = [], []
    for name in ('studio', 'user'):
        path = Path(config_dir) / f'{name}.json'
        try:
            with path.open('rb') as stream:
                data = stream.read(65537)
            if len(data) > 65536:
                raise ValueError('profile exceeds 64 KiB')
            layers.append((name, json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique_object)))
        except FileNotFoundError:
            pass
        except (OSError, ValueError, RecursionError) as error:
            diagnostics.append(f'{name}: {error}; file left unchanged')
    if session is not None:
        layers.append(('session', session))
    result = resolve_profiles(layers, validate=validate)
    result.diagnostics[:0] = diagnostics
    return result

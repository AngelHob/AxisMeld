# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Transform generated keymap data. No mutation of Blender/addon user state."""
from copy import deepcopy

from .commands import baseline_bindings, RESERVED_KEYS
from .profiles import MODIFIERS


def overlaps(event, owned):
    if event.get('type') != owned['type']:
        return False
    return bool(event.get('any')) or all(
        event.get(key, False) == -1 or event.get(key, False) == owned.get(key, False)
        for key in MODIFIERS)


def modeling_keymap(name, args):
    return not args.get('modal', False) and (
        name in {'Object Mode', 'Mesh', 'Object Non-modal', '3D View', '3D View Generic'} or
        name.startswith('3D View Tool:'))


def validate_global_bindings(base, bindings):
    """Reject profile inputs intercepted by shared window/screen shortcuts."""
    for name, args, content in base:
        if args.get('modal') or name not in {'Window', 'Screen', 'Screen Editing', 'Frames'}:
            continue
        for operator, event, data in content['items']:
            for command, owned in bindings.items():
                if owned is not None and overlaps(event, owned):
                    raise ValueError(f'global input conflict: {command} with {name}/{operator}')


def generate_keymaps(base, bindings):
    result = deepcopy(base)
    owned = [*baseline_bindings().values(), *(value for value in bindings.values() if value),
             *({'type': key} for key in RESERVED_KEYS)]
    for name, args, content in result:
        if not modeling_keymap(name, args):
            continue
        content['items'] = [item for item in content['items']
                            if not any(overlaps(item[1], event) for event in owned)]
        for command, event in bindings.items():
            target = ('3D View',) if command.startswith('view.') else ('Object Mode', 'Mesh')
            if name in target and event is not None:
                content['items'].append(('axismeld.command', dict(event),
                                         {'properties': [('command', command)]}))
    return result


def addon_conflicts(keyconfig, bindings):
    """Report possible overlaps, never disable a third-party item."""
    conflicts = []
    if keyconfig is None:
        return conflicts
    for keymap in keyconfig.keymaps:
        if not modeling_keymap(keymap.name, {'modal': keymap.is_modal}):
            continue
        for item in keymap.keymap_items:
            if not item.active:
                continue
            event = {'type': item.type, 'any': item.any,
                     **{key: getattr(item, key) for key in MODIFIERS}}
            for command, owned in bindings.items():
                if owned is not None and overlaps(event, owned):
                    conflicts.append(f'Addon {keymap.name}: {item.idname} overlaps {command}')
    return conflicts

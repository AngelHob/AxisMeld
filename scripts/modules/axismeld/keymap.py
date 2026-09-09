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
        name in {'Object Mode', 'Mesh', 'Object Non-modal', '3D View', '3D View Generic',
                 'AxisMeld Hotbox'} or
        name.startswith('3D View Tool:'))


def _original_frames_space_play(name, args, operator, event, data, command, owned):
    return (command == 'hotbox.open' and name == 'Frames' and
            args == {'space_type': 'EMPTY', 'region_type': 'WINDOW'} and
            operator == 'screen.animation_play' and
            event == {'type': 'SPACE', 'value': 'PRESS'} and data is None and
            owned == {'type': 'SPACE', 'value': 'PRESS', 'alt': False,
                      'ctrl': False, 'shift': False, 'oskey': False})


def validate_global_bindings(base, bindings):
    """Reject profile inputs intercepted by shared window/screen shortcuts."""
    for name, args, content in base:
        if args.get('modal') or name not in {'Window', 'Screen', 'Screen Editing', 'Frames'}:
            continue
        for operator, event, data in content['items']:
            for command, owned in bindings.items():
                if owned is not None and overlaps(event, owned):
                    if _original_frames_space_play(
                            name, args, operator, event, data, command, owned):
                        continue
                    raise ValueError(f'global input conflict: {command} with {name}/{operator}')


def generate_keymaps(base, bindings):
    result = deepcopy(base)
    owned = [*baseline_bindings().values(), *(value for value in bindings.values() if value),
             *({'type': key} for key in RESERVED_KEYS)]
    for name, args, content in result:
        # Native operators poll the Maya preset, modeling context and highlighted/armed
        # transform gizmo. Other gizmos and unconstrained drags fall through unchanged.
        if name == 'Generic Gizmo Maybe Drag':
            content['items'].insert(0, ('axismeld.axis_select',
                                       {'type': 'LEFTMOUSE', 'value': 'CLICK'}, None))
        if not modeling_keymap(name, args):
            continue
        content['items'] = [item for item in content['items']
                            if not any(overlaps(item[1], event) for event in owned)]
        for command, event in bindings.items():
            if command == 'hotbox.open':
                continue
            target = ('3D View',) if command.startswith('view.') else ('Object Mode', 'Mesh')
            if name in target and event is not None:
                content['items'].append(('axismeld.command', dict(event),
                                         {'properties': [('command', command)]}))
        if name in {'3D View Tool: Move', '3D View Tool: Rotate', '3D View Tool: Scale'}:
            content['items'][0:0] = [
                ('axismeld.axis_drag', {'type': 'MIDDLEMOUSE', 'value': 'PRESS'}, None),
                ('axismeld.axis_clear', {'type': 'ESC', 'value': 'PRESS'}, None),
            ]
    hotbox_items = []
    hotbox_event = bindings.get('hotbox.open')
    if hotbox_event is not None:
        hotbox_items.append(('axismeld.command', dict(hotbox_event),
                             {'properties': [('command', 'hotbox.open')]}))
    hotbox_maps = [entry for entry in result if entry[0] == 'AxisMeld Hotbox']
    if hotbox_maps:
        hotbox_maps[0][2]['items'] = hotbox_items
        result[:] = [entry for entry in result
                     if entry[0] != 'AxisMeld Hotbox' or entry is hotbox_maps[0]]
    elif hotbox_items:
        result.append(('AxisMeld Hotbox', {'space_type': 'VIEW_3D', 'region_type': 'WINDOW'},
                       {'items': hotbox_items}))
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

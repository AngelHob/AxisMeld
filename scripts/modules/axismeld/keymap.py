# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Transform generated keymap data. No mutation of Blender/addon user state."""
from copy import deepcopy

from .context_hotbox import COMPONENT_HOTBOX
from .creation_hotbox import CREATE_HOTBOX
from .context_modeling_hotbox import MODEL_HOTBOX
from .object_modeling_hotbox import OBJECT_TOOLS
from .commands import baseline_bindings, binding_events, RESERVED_KEYS
from .profiles import MODIFIERS
from .modeling_registry import SPECS as MODELING_SPECS, keymap_targets

CONTEXT_TARGETS = {COMPONENT_HOTBOX: ('Object Mode', 'Mesh'),
                   CREATE_HOTBOX: ('Object Mode',), MODEL_HOTBOX: ('Object Mode', 'Mesh')}
CONTEXT_HOTBOXES = frozenset(CONTEXT_TARGETS)

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
            for command, owned in binding_events(bindings):
                if owned is not None and overlaps(event, owned):
                    # Screen Editing is activated on area edges; keep its exact native RMB
                    # item. It does not intercept the 3D View WINDOW component gesture.
                    if (command == COMPONENT_HOTBOX and name == 'Screen Editing' and
                            args == {'space_type': 'EMPTY', 'region_type': 'WINDOW'} and
                            operator == 'screen.area_options' and data is None and
                            event == {'type': 'RIGHTMOUSE', 'value': 'PRESS'} and
                            owned == baseline_bindings()[COMPONENT_HOTBOX]):
                        continue
                    if _original_frames_space_play(
                            name, args, operator, event, data, command, owned):
                        continue
                    raise ValueError(f'global input conflict: {command} with {name}/{operator}')


def generate_keymaps(base, bindings):
    result = deepcopy(base)
    # Context sessions must retain the native fallback for rejected contexts and rebinds.
    owned = [*(value for key, value in baseline_bindings().items()
               if key not in CONTEXT_HOTBOXES and key not in MODELING_SPECS and key not in OBJECT_TOOLS),
             *(value for key, value in bindings.items()
               if value and key not in CONTEXT_HOTBOXES and key not in MODELING_SPECS and key not in OBJECT_TOOLS),
             *({'type': key} for key in RESERVED_KEYS)]
    for name, args, content in result:
        # Native operators poll the Maya preset, modeling context and highlighted/armed
        # transform gizmo. Other gizmos and unconstrained drags fall through unchanged.
        if name == 'Generic Gizmo Maybe Drag':
            content['items'].insert(0, ('axismeld.axis_select',
                                       {'type': 'LEFTMOUSE', 'value': 'CLICK'}, None))
        legacy_map = modeling_keymap(name, args)
        extra_map = name in {'Curve', 'Lattice'} and not args.get('modal', False)
        if not legacy_map and not extra_map:
            continue
        local_owned = list(owned) if legacy_map else []
        # Curve/Lattice only gain explicitly declared M3 shortcuts; native QWER and
        # non-modeling editor maps remain intact. View-wide fallback bindings are retained.
        local_owned.extend(event for layer in (baseline_bindings(), bindings)
                           for identifier, event in binding_events(layer)
                           if event and identifier in MODELING_SPECS and
                           name in keymap_targets(identifier))
        if name == 'Object Mode':
            local_owned.extend(event for identifier, event in binding_events(bindings)
                               if event and identifier in OBJECT_TOOLS)
        content['items'] = [item for item in content['items']
                             if not (item[0] == 'axismeld.command' and item[2] and
                                     any(('command', command) in item[2].get('properties', ())
                                         for command in (*CONTEXT_HOTBOXES, *OBJECT_TOOLS)))
                            and not any(overlaps(item[1], event) for event in local_owned)]
        for command, event in binding_events(bindings):
            if command == 'hotbox.open':
                continue
            target = (keymap_targets(command) if command in MODELING_SPECS else
                      ('Object Mode',) if command in OBJECT_TOOLS else
                      CONTEXT_TARGETS[command] if command in CONTEXT_TARGETS else
                      ('3D View',) if command.startswith('view.') else ('Object Mode', 'Mesh'))
            if name in target and event is not None:
                item = ('axismeld.command', dict(event),
                        {'properties': [('command', command)]})
                if command in CONTEXT_HOTBOXES:
                    content['items'].insert(0, item)
                else:
                    content['items'].append(item)
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
        extra_map = keymap.name in {'Curve', 'Lattice'} and not keymap.is_modal
        if not modeling_keymap(keymap.name, {'modal': keymap.is_modal}) and not extra_map:
            continue
        for item in keymap.keymap_items:
            if not item.active:
                continue
            event = {'type': item.type, 'any': item.any,
                     **{key: getattr(item, key) for key in MODIFIERS}}
            for command, owned in binding_events(bindings):
                if extra_map and (command not in MODELING_SPECS or keymap.name not in keymap_targets(command)):
                    continue
                if owned is not None and overlaps(event, owned):
                    conflicts.append(f'Addon {keymap.name}: {item.idname} overlaps {command}')
    return conflicts

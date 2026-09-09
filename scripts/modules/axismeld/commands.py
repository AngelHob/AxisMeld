# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Immutable Maya command metadata; Blender implementation lives in adapter.py."""
from dataclasses import dataclass
from types import MappingProxyType

PRESET_NAME = 'AxisMeld_Maya_2026'
SOURCE_URL = ('https://help.autodesk.com/cloudhelp/2026/ENU/Maya-KeyboardShortcuts/files/'
              'GUID-30CACC9D-8FBE-4B85-8A8F-C5ADF32DDD4E.htm')


@dataclass(frozen=True)
class Command:
    id: str
    label: str
    key: str
    alt: bool = False
    status: str = 'adapted'
    difference: str = 'Uses Blender semantics; Maya hold menus are not implemented.'


COMMANDS = MappingProxyType({command.id: command for command in (
    Command('tool.select', 'Select Tool', 'Q'),
    Command('transform.move', 'Move Tool', 'W'),
    Command('transform.rotate', 'Rotate Tool', 'E'),
    Command('transform.scale', 'Scale Tool', 'R'),
    Command('selection.toggle_component', 'Object / Component', 'F8'),
    Command('selection.vertex_mode', 'Vertex', 'F9'),
    Command('selection.edge_mode', 'Edge', 'F10'),
    Command('selection.face_mode', 'Face', 'F11'),
    Command('view.focus_selected', 'Frame Selected', 'F'),
    Command('view.frame_all', 'Frame All', 'A'),
    Command('view.orbit', 'Tumble', 'LEFTMOUSE', alt=True),
    Command('view.pan', 'Track', 'MIDDLEMOUSE', alt=True),
    Command('view.dolly', 'Dolly', 'RIGHTMOUSE', alt=True),
    Command('view.wireframe', 'Wireframe', 'FOUR'),
    Command('view.shaded', 'Shaded', 'FIVE'),
)})

# No approximate stand-in for hold/release behavior or UV/smoothing semantics.
RESERVED_KEYS = ('SPACE', 'D', 'X', 'C', 'V', 'J', 'F12', 'ONE', 'TWO', 'THREE')


def baseline_bindings():
    return {key: {'type': command.key, 'value': 'PRESS', 'alt': command.alt,
                  'ctrl': False, 'shift': False, 'oskey': False}
            for key, command in COMMANDS.items()}

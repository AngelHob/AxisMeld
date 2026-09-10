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
    key: str | None = None
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
    Command('selection.select_all', 'Select All',
            difference=('Selects eligible objects or mesh components using Blender context; '
                        'Maya DAG/UFE rules are not reproduced.')),
    Command('selection.grow', 'Grow Selection',
            difference=('Uses Blender native topology traversal; Maya '
                        'GrowPolygonSelectionRegion equivalence is not claimed.')),
    Command('selection.shrink', 'Shrink Selection',
            difference=('Uses Blender native topology traversal; Maya '
                        'ShrinkPolygonSelectionRegion equivalence is not claimed.')),
    Command('view.focus_selected', 'Frame Selected', 'F'),
    Command('view.frame_all', 'Frame All', 'A'),
    Command('view.orbit', 'Tumble', 'LEFTMOUSE', alt=True),
    Command('view.pan', 'Track', 'MIDDLEMOUSE', alt=True),
    Command('view.dolly', 'Dolly', 'RIGHTMOUSE', alt=True),
    Command('view.wireframe', 'Wireframe', 'FOUR'),
    Command('view.shaded', 'Shaded', 'FIVE'),
    Command('hotbox.open', 'View Hotbox', 'SPACE',
            difference='Adapted four-direction view menu and tap quad toggle; not the full Maya hotbox.'),
    Command('view.toggle_quad', 'Toggle Single / Quad View',
            difference='Uses AxisMeld session view slots; hidden slots are not saved across restart.'),
    Command('view.perspective', 'Perspective View',
            difference='Restores the current pane perspective history with Blender navigation semantics.'),
    Command('view.side', 'Side View',
            difference='Uses the AxisMeld right-side orthographic view.'),
    Command('view.front', 'Front View',
            difference='Uses the AxisMeld front orthographic view.'),
    Command('view.top', 'Top View',
            difference='Uses the AxisMeld top orthographic view.'),
    Command('view.left', 'Left View',
            difference='Uses the AxisMeld left orthographic view.'),
    Command('view.back', 'Back View',
            difference='Uses the AxisMeld back orthographic view.'),
    Command('view.bottom', 'Bottom View',
            difference='Uses the AxisMeld bottom orthographic view.'),
)})

# No approximate stand-in for hold/release behavior or UV/smoothing semantics.
RESERVED_KEYS = ('D', 'X', 'C', 'V', 'J', 'F12', 'ONE', 'TWO', 'THREE')


def baseline_bindings():
    return {key: {'type': command.key, 'value': 'PRESS', 'alt': command.alt,
                  'ctrl': False, 'shift': False, 'oskey': False}
            for key, command in COMMANDS.items() if command.key is not None}

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Immutable Maya command metadata; Blender implementation lives in adapter.py."""
from dataclasses import dataclass
from types import MappingProxyType
from .tool_hotbox import ORIENTATIONS
from .creation_hotbox import CREATE_HOTBOX, PRIMITIVES
from .modeling_registry import SPECS as MODELING_SPECS

PRESET_NAME = 'AxisMeld_Maya_2026'
SOURCE_URL = ('https://help.autodesk.com/cloudhelp/2026/ENU/Maya-KeyboardShortcuts/files/'
              'GUID-30CACC9D-8FBE-4B85-8A8F-C5ADF32DDD4E.htm')


@dataclass(frozen=True)
class Command:
    id: str
    label: str
    key: str | None = None
    alt: bool = False
    ctrl: bool = False
    shift: bool = False
    oskey: bool = False
    status: str = 'adapted'
    difference: str = 'Uses Blender semantics; Maya hold menus are not implemented.'


COMMANDS = MappingProxyType({command.id: command for command in (
    *(Command(spec.id, spec.label, spec.key, alt=spec.alt, ctrl=spec.ctrl, shift=spec.shift,
              status=spec.classification, difference=spec.difference)
      for spec in MODELING_SPECS.values()),
    *(Command('mesh.create_' + name, label,
              difference=('Creates a native Blender primitive at the 3D Cursor with Blender dimensions, '
                          'Z-up and topology; Maya interactive placement is not reproduced.' +
                          (' Disc is a filled NGON circle.' if name == 'disc' else '') +
                          (' Torus follows Blender\'s Enter Edit Mode preference.' if name == 'torus' else '')))
      for name, label, _direction, _operator, _properties in PRIMITIVES),
    Command(CREATE_HOTBOX, 'Empty Context Create Hotbox', 'RIGHTMOUSE', shift=True,
            difference='Object-only empty-selection creation menu; direct mouse entry requires empty pointer space.'),
    *(Command(identifier, label,
              difference='Uses a persistent Blender selection tool; Paint is circle selection, not Maya brush semantics.')
      for identifier, label in (('selection.marquee', 'Marquee Select'),
                                 ('selection.lasso', 'Lasso Select'),
                                 ('selection.paint', 'Paint Selection'))),
    Command('selection.clear', 'Clear Selection', 'D', alt=True,
            difference='Native deselect in the current Object or Mesh Edit set; no mode switching.'),
    *(Command(identifier, orientation.title(),
              difference='Blender per-tool transform orientation; Normal uses Blender selection normals and Gimbal uses Euler semantics.')
      for identifier, (_, orientation) in ORIENTATIONS.items()),
    Command('tool.select', 'Select Tool', 'Q', difference='Native box select; hold Q + LMB opens classic tool options; toolkit variants deferred.'),
    Command('transform.move', 'Move Tool', 'W', difference='Native Move tool with classic held-LMB menu; same-tool tap does not reset the active axis.'),
    Command('transform.rotate', 'Rotate Tool', 'E', difference='Native Rotate tool with classic held-LMB menu; same-tool tap does not reset the active axis.'),
    Command('transform.scale', 'Scale Tool', 'R', difference='Native Scale tool with classic held-LMB menu; global object-scale difference remains deferred.'),
    Command('context.component_hotbox', 'Active Mesh Component Hotbox', 'RIGHTMOUSE',
            difference='Hold and release on the active selected editable mesh; target-under-pointer picking deferred to M2b.'),
    Command('mode.object', 'Object Mode',
            difference='Idempotently exits mesh Edit Mode on the active selected editable mesh.'),
    Command('selection.toggle_component', 'Object / Component', 'F8'),
    Command('selection.vertex_mode', 'Vertex', 'F9'),
    Command('selection.edge_mode', 'Edge', 'F10'),
    Command('selection.face_mode', 'Face', 'F11'),
    Command('selection.select_all', 'Select All', 'A', ctrl=True, shift=True,
            difference=('Selects eligible objects or mesh components using Blender context; '
                        'Maya DAG/UFE rules are not reproduced.')),
    Command('selection.grow', 'Grow Selection', 'PERIOD', shift=True,
            difference=('Uses Blender native topology traversal; Maya '
                        'GrowPolygonSelectionRegion equivalence is not claimed.')),
    Command('selection.shrink', 'Shrink Selection', 'COMMA', shift=True,
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
                  'ctrl': command.ctrl, 'shift': command.shift, 'oskey': command.oskey}
            for key, command in COMMANDS.items() if command.key is not None}


# Verified default Maya aliases: hotkeySetup.mel:257 and :267. Remapping or
# disabling the primary also removes these aliases. Native Screen Ctrl+Z/G stay native.
DEFAULT_ALIASES = {
    'edit.redo': ({'type': 'Y', 'value': 'PRESS', 'ctrl': True},),
    'display.frame_selected_all': ({'type': 'F', 'value': 'PRESS', 'ctrl': True, 'shift': True},),
}


def binding_events(bindings):
    """One input source for profile collision checks, keymaps and diagnostics."""
    defaults = baseline_bindings()
    for command, event in bindings.items():
        yield command, event
        if event is not None and event == defaults.get(command):
            for alias in DEFAULT_ALIASES.get(command, ()):
                yield command, {'ctrl': False, 'shift': False, 'alt': False, 'oskey': False} | alias

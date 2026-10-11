# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya 2026 polyConvertMM menu facts; existing adapters retain their semantics."""
from .modeling_registry import SPECS

CONVERSION_HOTBOX = 'context.conversion_hotbox'
CONVERSION_ROOT = 'context.convert'
CONVERSION_MENU = 'context.convert_menu'

# suffix, label, direction, existing command; empty commands are honest gaps.
GROUPS = (
    ('edges', 'To Edges', 'N', (
        ('edges', 'To Edges', 'N', 'selection.convert_edge'),
        ('contained', 'To Contained Edges', 'S', 'selection.contained_edges'),
        ('contiguous', 'To Contiguous Edges', 'NW', ''),
        ('perimeter', 'To Edge Perimeter', 'NE', 'selection.region_boundary'))),
    ('shrink', 'Shrink Selection', 'NW', (
        ('shrink', 'Shrink', 'NW', 'selection.shrink'), ('loop', 'Shrink Loop', 'N', ''))),
    ('uv', 'To UVs', 'E', (
        ('uv', 'To UVs', 'E', ''), ('perimeter', 'To UV Perimeter', 'NE', ''))),
    ('loop', 'Edge Loop Utilities', 'SE', (
        ('loop', 'To Edge Loop', 'SE', 'selection.edge_loop'),
        ('delete', 'To Edge Loop and Delete', 'NE', ''),
        ('duplicate', 'To Edge Loop and Duplicate', 'SW', ''))),
    ('ring', 'Edge Ring Utilities', 'SW', (
        ('ring', 'To Edge Ring', 'SW', 'selection.edge_ring'),
        ('split', 'To Edge Ring and Split', 'SE', ''),
        ('collapse', 'To Edge Ring and Collapse', 'NW', ''))),
    ('faces', 'To Faces', 'S', (
        ('faces', 'To Faces', 'S', 'selection.convert_face'),
        ('contained', 'To Contained Faces', 'N', 'selection.contained_faces'),
        ('perimeter', 'To Face Perimeter', 'SE', 'selection.face_perimeter'))),
    ('vertices', 'To Vertices', 'W', (
        ('vertices', 'To Vertices', 'W', 'selection.convert_vert'),
        ('perimeter', 'To Vertex Perimeter', 'NW', 'selection.vertex_perimeter'))),
    ('grow', 'Grow Selection', 'NE', (
        ('grow', 'Grow', 'NE', 'selection.grow'), ('loop', 'Grow Loop', 'N', ''))),
)
ROWS = (
    ('face_path', 'To Face Path', 'selection.face_path'), ('uv_shell', 'To UV Shell', ''),
    ('shell', 'To Shell', 'selection.linked_mesh'),
    ('shell_border', 'To Shell Border', 'selection.boundary_loop'),
    ('separator_border', '|', ''), ('border_tool', 'Select Border Edge Tool', ''),
    ('separator_boundary', '|', ''), ('boundary', 'Selection Boundary', ''),
    ('constraints', 'Selection Constraints', ''),
)
COMMAND_ROWS = {f'{CONVERSION_ROOT}.{group}.{suffix}': command
                for group, _, _, children in GROUPS for suffix, _, _, command in children if command}
COMMAND_ROWS.update({f'{CONVERSION_MENU}.{suffix}': command for suffix, _, command in ROWS if command})


def conversion_menus(node):
    def row(identifier, label, command, direction=None):
        children = ()
        if identifier.endswith('.edges.contiguous'):
            children = (node(identifier + '.options', 'disabled', 'Options', enabled=False,
                             reason='Maya contiguous-edge options are not adapted'),)
        difference = SPECS[command].difference if command in SPECS else ''
        return node(identifier, 'command' if command else 'disabled', label,
                    command=command, direction=direction, enabled=bool(command), children=children,
                    reason=difference[:128] if command else 'Maya selection operation is not adapted')
    groups = [node(CONVERSION_ROOT + '.' + name, 'menu', label, direction=direction,
                   presentation='radial', children=[
                       row(f'{CONVERSION_ROOT}.{name}.{suffix}', title, command, child_direction)
                       for suffix, title, child_direction, command in children])
              for name, label, direction, children in GROUPS]
    companion = [node(CONVERSION_MENU + '.' + suffix, 'separator', '', enabled=False)
                 if label == '|' else row(CONVERSION_MENU + '.' + suffix, label, command)
                 for suffix, label, command in ROWS]
    return (node(CONVERSION_ROOT, 'menu', 'Convert Selection', presentation='radial', children=groups),
            node(CONVERSION_MENU, 'menu', 'Convert Selection Menu', presentation='list', children=companion))

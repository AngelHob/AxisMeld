# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded active-mesh component menu; target-under-pointer picking belongs to M2b."""
COMPONENT_ROOT = 'context.components'
COMPONENT_HOTBOX = 'context.component_hotbox'


def component_menu(node):
    children = [node(COMPONENT_ROOT + '.' + name, 'command', label,
                     command=command, direction=direction)
                for name, label, command, direction in (
                    ('edge', 'Edge', 'selection.edge_mode', 'N'),
                    ('vertex', 'Vertex', 'selection.vertex_mode', 'W'),
                    ('face', 'Face', 'selection.face_mode', 'S'),
                    ('object', 'Object Mode', 'mode.object', 'NE'))]
    children += [node(COMPONENT_ROOT + '.' + name, 'disabled', label, enabled=False,
                      reason=reason + ': Not implemented', direction=direction)
                 for name, label, direction, reason in (
                     ('uv', 'UV', 'E', 'deferred-uv'),
                     ('vertex_face', 'Vertex Face', 'SW', 'M2-vertex-face'),
                     ('multi', 'Multi Component', 'SE', 'M2-multi-component'))]
    return node(COMPONENT_ROOT, 'menu', 'Active Mesh Components', children=children,
                presentation='radial')

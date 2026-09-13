# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya empty-context primitive directions and bounded native creation adapters."""
CREATE_ROOT = 'context.create'
CREATE_HOTBOX = 'context.create_hotbox'

# Keep native dimensions and tessellation; only Disc needs an explicit filled topology.
# Torus has no enter_editmode RNA property and retains Blender's preference behavior.
PRIMITIVES = (
    ('disc', 'Disc', 'NE', 'primitive_circle_add', {'fill_type': 'NGON', 'enter_editmode': False}),
    ('sphere', 'Sphere', 'E', 'primitive_uv_sphere_add', {'enter_editmode': False}),
    ('torus', 'Torus', 'SE', 'primitive_torus_add', {}),
    ('cube', 'Cube', 'S', 'primitive_cube_add', {'enter_editmode': False}),
    ('cone', 'Cone', 'SW', 'primitive_cone_add', {'enter_editmode': False}),
    ('cylinder', 'Cylinder', 'W', 'primitive_cylinder_add', {'enter_editmode': False}),
    ('plane', 'Plane', 'NW', 'primitive_plane_add', {'enter_editmode': False}),
)
CREATE_OPERATORS = {'mesh.create_' + name: (operator, properties)
                    for name, _label, _direction, operator, properties in PRIMITIVES}
CREATE_COMMANDS = frozenset(CREATE_OPERATORS)


def creation_menu(node):
    children = [node(CREATE_ROOT + '.polygon', 'disabled', 'Create Polygon Tool', enabled=False,
                     reason='M2c-P01: Maya interactive polygon creation adapter not implemented',
                     direction='N')]
    children.extend(node(CREATE_ROOT + '.' + name, 'command', label,
                         command='mesh.create_' + name, direction=direction)
                    for name, label, direction, _operator, _properties in PRIMITIVES)
    return node(CREATE_ROOT, 'menu', 'Polygon Primitives', children=children, presentation='radial')

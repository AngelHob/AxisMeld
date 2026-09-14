# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya empty-context primitive directions and bounded native creation adapters."""
CREATE_ROOT = 'context.create'
CREATE_HOTBOX = 'context.create_hotbox'
CREATE_MENU = 'context.create_menu'
CREATE_MENU_COMMANDS = {
    CREATE_MENU + '.platonic': 'mesh.create_icosphere',
    CREATE_MENU + '.pyramid': 'mesh.create_pyramid',
    CREATE_MENU + '.prism': 'mesh.create_prism',
    CREATE_MENU + '.type': 'object.create_text',
    CREATE_MENU + '.polygon_display_all.backface_culling_on': 'display.backface_culling_on',
    CREATE_MENU + '.polygon_display_all.backface_culling_off': 'display.backface_culling_off',
}
CREATE_WORKFLOW_INDICATORS = frozenset({CREATE_MENU + '.interactive_creation',
                                       CREATE_MENU + '.exit_on_completion'})

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
    def options(suffix):
        return (node(CREATE_ROOT + '.' + suffix + '.options', 'disabled', 'Options', enabled=False,
                     reason='M2c-P02.' + suffix + ': Read-only creation parameters not implemented'),)
    children = [node(CREATE_ROOT + '.polygon', 'disabled', 'Create Polygon Tool', enabled=False,
                     reason='M2c-P01: Maya interactive polygon creation adapter not implemented',
                     direction='N', children=options('polygon'))]
    children.extend(node(CREATE_ROOT + '.' + name, 'command', label,
                         command='mesh.create_' + name, direction=direction, children=options(name))
                    for name, label, direction, _operator, _properties in PRIMITIVES)
    return node(CREATE_ROOT, 'menu', 'Polygon Primitives', children=children, presentation='radial')


def creation_companion(node):
    """The screenshot's 16 rows; absent Maya algorithms stay visible and disabled."""
    def row(suffix, label, *, options=False, reason=''):
        identifier = CREATE_MENU + '.' + suffix
        command = CREATE_MENU_COMMANDS.get(identifier, '')
        children = ()
        if options:
            children = (node(identifier + '.options', 'disabled', 'Options', enabled=False,
                             reason='M2c-P02.' + suffix + ': Read-only parameters not implemented'),)
        return node(identifier, 'command' if command else 'disabled', label,
                    command=command, enabled=bool(command), children=children,
                    reason=reason or 'M2c-P03.' + suffix + ': Maya creation workflow not implemented')

    def sep(suffix):
        return node(CREATE_MENU + '.separator_' + suffix, 'separator', '', enabled=False)

    def workflow(suffix, label, checked):
        result = row(suffix, label, reason='M2c-P04.' + suffix + ': Interactive creation workflow not implemented; preferences unchanged')
        result.update(indicator='checkbox', checked=checked)
        return result

    display = node(CREATE_MENU + '.polygon_display_all', 'menu', 'Polygon Display All',
                   presentation='list', children=(
        row('polygon_display_all.backface_culling_on', 'Backface Culling on for All Polys',
            reason='Set current viewport backface culling on; not Maya global polygon display'),
        row('polygon_display_all.backface_culling_off', 'Backface Culling off for All Polys',
            reason='Set current viewport backface culling off; not Maya global polygon display'),
        sep('display_culling'),
        row('polygon_display_all.border_edges', 'Toggle All Geometry Border Edges'),
        row('polygon_display_all.texture_border_edges', 'Toggle All Texture Border Edges'),
        sep('display_borders'),
        row('polygon_display_all.face_normals', 'Toggle All Face Normals'),
        row('polygon_display_all.vertex_normals', 'Toggle All Vertex Normals'),
        sep('display_normals'),
        row('polygon_display_all.face_centers', 'Toggle All Face Centers'),
        row('polygon_display_all.hidden_triangles', 'Toggle All Hidden Triangles'),
        row('polygon_display_all.vertices', 'Toggle All Vertices'),
        sep('display_vertices'),
        row('polygon_display_all.reset', 'Reset Display for All Polys'),
    ))
    return node(CREATE_MENU, 'menu', 'Polygon Primitives', presentation='list', children=(
        row('platonic', 'Platonic Solid', options=True,
            reason='Blender Icosphere adaptation only; not the full Maya Platonic Solid family'),
        row('pyramid', 'Pyramid', options=True,
            reason='Native four-sided cone at the 3D Cursor; Blender dimensions and topology'),
        row('prism', 'Prism', options=True,
            reason='Native triangular prism at the 3D Cursor; Blender dimensions and topology'),
        row('pipe', 'Pipe', options=True), row('helix', 'Helix', options=True),
        row('gear', 'Gear', options=True), row('soccer_ball', 'Soccer Ball', options=True), sep('solids'),
        row('super_ellipse', 'Super Ellipse', options=True),
        row('spherical_harmonics', 'Spherical Harmonics', options=True),
        row('ultra_shape', 'Ultra Shape', options=True),
        row('type', 'Type', reason='Native Blender Text at the 3D Cursor; no Maya Type construction network'),
        row('svg', 'SVG'), row('quad_draw', 'Quad Draw Tool', options=True,
            reason='M2c-P03.QuadDraw: Empty-selection Poly Build startup transaction not implemented'),
        sep('tools'), workflow('interactive_creation', 'Interactive Creation', False),
        workflow('exit_on_completion', 'Exit On Completion', True), sep('workflow'), display,
    ))

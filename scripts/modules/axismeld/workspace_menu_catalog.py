# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure placement projection of the reviewed Maya application menu catalog.

The source catalog owns command bindings and Maya provenance. This projection
places the reviewed modeling chapters in their viewport menu containers.
"""
from copy import deepcopy
from hashlib import sha256

from .menubar_catalog import build_menubar
from .workspace_native_catalog import integrate_native_groups


MODELING_SOURCE_ROOTS = tuple('modeling.' + suffix for suffix in (
    'mesh', 'edit_mesh', 'mesh_tools', 'mesh_display', 'curves', 'surfaces',
    'uv',
))
EXCLUDED_MODELING_ROOTS = ('modeling.deform', 'modeling.generate')

# Maya 2026 PolygonsBuildMenu.mel creates these chapters at lines
# 76, 201, 231, 264 and 322. Shared operations stay in Edit Mesh; its
# Vertex, Edge and Face chapters use stable nested menu IDs.
EDIT_MESH_CHAPTERS = (
    ('maya.modeling.edit_mesh.components', 'Components', 'modeling.edit_mesh', 'EDITMODE_HLT'),
    ('maya.modeling.edit_mesh.vertex', 'Vertex', 'viewport.modeling.vertex', 'VERTEXSEL'),
    ('maya.modeling.edit_mesh.edge', 'Edge', 'viewport.modeling.edge', 'EDGESEL'),
    ('maya.modeling.edit_mesh.face', 'Face', 'viewport.modeling.face', 'FACESEL'),
    ('maya.modeling.edit_mesh.curve', 'Curve', 'viewport.modeling.curve_projection', 'CURVE_DATA'),
)

# Reviewed component ownership for Blender-only Edit Mesh entries. Maya's
# shared component commands keep their original chapter and source payload.
_EDIT_EXTENSION_GROUPS = {
    'viewport.modeling.vertex': {
        'Extrude': ('extrude_vertices',),
        'Connect': ('connect_pairs', 'make_edge_face'),
        'Smooth': ('average_laplacian',),
        'Split': ('rip', 'rip_fill', 'rip_extend'),
        'Delete': ('dissolve_vertices',),
    },
    'viewport.modeling.edge': {
        'Extrude': ('extrude_edges', 'screw'),
        'Split': ('edge_split',),
        'Loops': ('space_loops',),
        'Delete': ('dissolve_edges', 'delete_edge_loop'),
    },
    'viewport.modeling.face': {
        'Extrude': ('extrude_faces_individual', 'extrude_along_normals'),
        'Fill': ('fill', 'grid_fill', 'beautify_fill'),
        'Topology': ('intersect_faces', 'split_by_edges'),
        'Delete': ('dissolve_faces',),
        'Inset and Shell': ('inset', 'solidify_faces', 'wireframe_faces'),
        'Face Boolean': ('boolean_faces_union', 'boolean_faces_difference', 'boolean_faces_intersection'),
    },
    'modeling.edit_mesh': {
        'Split': ('detach_selection',),
        'Merge': ('merge_cursor', 'merge_first', 'merge_last', 'merge_collapse'),
        'Transform': ('flatten',),
    },
}
EDIT_MESH_EXTENSION_ROUTES = {
    'menubar.command.mesh.' + suffix: (root_id, (purpose,))
    for root_id, groups in _EDIT_EXTENSION_GROUPS.items()
    for purpose, suffixes in groups.items() for suffix in suffixes
}


def _walk_nodes(nodes):
    for node in nodes:
        yield node
        yield from _walk_nodes(node.get('children', ()))


def _purpose_section(root, path):
    current = root
    for label in path:
        child = next((node for node in current['children']
                      if node['kind'] == 'menu' and node['label'] == label), None)
        if child is None:
            if any(node['kind'] == 'separator' and node['label'] for node in current['children']):
                raise ValueError('Explicit chapter placement required: ' + current['id'] + ' / ' + label)
            suffix = sha256((current['id'] + '\0' + label).encode()).hexdigest()[:16]
            child = dict(id='workspace.section.' + suffix, label=label, kind='menu', children=[],
                         origin='workspace_section', icon=root.get('icon', 'TOOL_SETTINGS'))
            current['children'].append(child)
        current = child
    return current


def _place_edit_mesh_extensions(roots):
    owners = [roots[identifier] for identifier in _EDIT_EXTENSION_GROUPS]
    extensions = {node['id']: node for node in _walk_nodes(owners)
                  if node.get('origin') == 'blender_extension'}
    if set(extensions) != set(EDIT_MESH_EXTENSION_ROUTES):
        raise ValueError('Blender Edit Mesh extensions need an updated component placement audit')
    for node in _walk_nodes(owners):
        node['children'] = [child for child in node.get('children', ()) if child['id'] not in extensions]
    for identifier, (root_id, path) in EDIT_MESH_EXTENSION_ROUTES.items():
        _purpose_section(roots[root_id], path)['children'].append(extensions[identifier])

    def prune(node):
        for child in node.get('children', ()):
            prune(child)
        node['children'] = [child for child in node.get('children', ())
                            if not (child.get('origin') in {'blender_section', 'workspace_section'}
                                    and child['kind'] == 'menu' and not child['children'])]

    for root in owners:
        prune(root)


def _split_edit_mesh(root):
    groups, seen = [], []
    chapters = {identifier: (label, destination, icon)
                for identifier, label, destination, icon in EDIT_MESH_CHAPTERS}
    for node in root['children']:
        if node['kind'] == 'separator' and node['label']:
            chapter = chapters.get(node['id'])
            if chapter is None or node['label'] != chapter[0]:
                raise ValueError('Unreviewed Edit Mesh chapter: ' + node['id'])
            label, destination, icon = chapter
            seen.append(node['id'])
            caption = {'Components': 'Edit Mesh', 'Curve': 'Curve Projection'}.get(label, label)
            groups.append(dict(id=destination, label=caption, kind='menu', children=[],
                               icon=icon, origin='workspace_projection',
                               source_menu_id=root['id'], source_heading_id=node['id']))
        elif not groups:
            raise ValueError('Edit Mesh item has no reviewed chapter: ' + node['id'])
        else:
            groups[-1]['children'].append(node)
    if tuple(seen) != tuple(chapter[0] for chapter in EDIT_MESH_CHAPTERS):
        raise ValueError('Edit Mesh chapters are missing, duplicated or out of order')
    return groups


def build_workspace_menubar():
    """Return an independent catalog with seven Modeling viewport root menus.

Every functional node, including its separate Options object, retains its
complete source payload. Deform and Generate leave the Modeling menu set;
their reference data and all other menu sets stay unchanged.
    """
    catalog = deepcopy(build_menubar())
    source = next((root for root in catalog['menus'] if root['id'] == 'modeling.edit_mesh'), None)
    if source is None:
        raise ValueError('The reviewed Edit Mesh source menu is missing')
    groups = _split_edit_mesh(source)
    shared, component_groups, curve_projection = groups[0], groups[1:4], groups[4]
    tools = next((root for root in catalog['menus'] if root['id'] == 'modeling.mesh_tools'), None)
    if tools is None:
        raise ValueError('The reviewed Mesh Tools destination is missing')
    tools['children'].append(curve_projection)

    catalog['menus'] = tuple(shared if root['id'] == source['id'] else root for root in catalog['menus'])
    # Move extensions before nesting so the reviewed ownership containers do
    # not overlap while their children are relocated.
    _place_edit_mesh_extensions({node['id']: node for node in (*catalog['menus'], *component_groups)})
    shared['children'].extend(component_groups)
    catalog['sets']['MODELING'] = tuple(identifier for identifier in catalog['sets']['MODELING']
                                        if identifier not in EXCLUDED_MODELING_ROOTS)
    catalog['modeling_roots'] = MODELING_SOURCE_ROOTS
    catalog['edit_mesh_groups'] = {chapter[1]: group['id'] for chapter, group in zip(EDIT_MESH_CHAPTERS, groups)}
    catalog['excluded_modeling_roots'] = EXCLUDED_MODELING_ROOTS
    exposed_roots = set().union(*catalog['sets'].values())
    catalog['archived_roots'] = tuple(root['id'] for root in catalog['menus'] if root['id'] not in exposed_roots)
    # Actual Blender menu hosts belong to the UI integration, not this source
    # projection. Callers can record that independent entrypoint map here.
    catalog['host_roots'] = {}
    return integrate_native_groups(catalog)


def routes(catalog=None, root_ids=None):
    """Map functional IDs, including Options, to their projected label paths.

Pass actual UI entrypoint root IDs to audit reachability. The default traverses
the complete projected catalog; source node ``path`` provenance is never edited.
    """
    if catalog is None:
        catalog = build_workspace_menubar()
    roots = {root['id']: root for root in catalog['menus']}
    if root_ids is None:
        root_ids = tuple(roots)
    result = {}

    def visit(node, parent_path):
        path = parent_path + (node['label'],)
        if node['kind'] not in {'menu', 'separator'}:
            if node['id'] in result:
                raise ValueError('A functional menu ID has multiple routes: ' + node['id'])
            result[node['id']] = path
        for child in node.get('children', ()):
            visit(child, path)
        if node.get('options'):
            visit(node['options'], path)

    for identifier in root_ids:
        if identifier not in roots:
            raise ValueError('Unknown workspace menu root: ' + identifier)
        visit(roots[identifier], ())
    return result

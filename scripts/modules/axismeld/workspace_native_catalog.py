# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Place fixed native draw groups into the reviewed Modeling purpose chapters."""
from .workspace_native_groups import GROUPS
from .modeling_registry import SPECS


# Reviewed equal invocation modes AND full parameter payloads. Similar operator
# names with different defaults/macros remain separate native capabilities.
EQUIVALENT_ITEMS = {
    'vertex.extrude.mesh_bevel': 'mesh.bevel_vertices',
    'vertex.rip.mesh_rip_move': 'mesh.rip',
    'vertex.rip.mesh_rip_move_2': 'mesh.rip_fill',
    'vertex.rip.mesh_rip_edge_move': 'mesh.rip_extend',
    'vertex.smooth_slide.mesh_vertices_smooth': 'mesh.average_vertices',
    'vertex.smooth_slide.mesh_vertices_smooth_laplacian': 'mesh.average_laplacian',
    'vertex.crease.transform_vert_crease': 'mesh.interactive_crease_vertices',
    'edge.construct.mesh_bevel': 'mesh.bevel_edges',
    'edge.slide.mesh_offset_edge_loops_slide': 'mesh.interactive_offset_loop',
    'edge.weight.transform_edge_crease': 'mesh.interactive_crease_edges',
    'face.construct.mesh_inset': 'mesh.inset',
}

EQUIVALENT_NATIVE_ITEMS = (
    ('edge.seams', 'edge.seams.mesh_mark_seam', 'uv.seams', 'uv.seams.mesh_mark_seam'),
    ('edge.seams', 'edge.seams.mesh_mark_seam_2', 'uv.seams', 'uv.seams.mesh_mark_seam_2'),
)


def deduplicate_native_items(selections):
    aliases = []
    for source_group, source_id, target_group, target_id in EQUIVALENT_NATIVE_ITEMS:
        source = GROUPS[source_group]
        target = GROUPS[target_group]
        source_item = next(item for item in source['items'] if item['id'] == source_id)
        target_item = next(item for item in target['items'] if item['id'] == target_id)
        group_fields = ('modes', 'root_id', 'path', 'dynamic_context')
        item_fields = ('api', 'operator', 'provider', 'properties', 'invoke_context',
                       'keywords', 'conditions', 'enum_property')
        if (any(source[field] != target[field] for field in group_fields) or
                any(source_item[field] != target_item[field] for field in item_fields) or
                target_id not in selections[target_group]):
            raise ValueError('Native item equivalence changed; review before deduplicating: ' + source_id)
        selections[source_group] = tuple(item for item in selections[source_group] if item != source_id)
        aliases.append(dict(group_key=source_group, native_item=source_id,
                            target_group_key=target_group, target_native_item=target_id))
    return tuple(aliases)


def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.get('children', ()))


def _flatten(values, prefix=''):
    result = {}
    for key, value in dict(values).items():
        key = prefix + key
        if isinstance(value, dict):
            result.update(_flatten(value, key + '.'))
        else:
            result[key] = value
    return result


def native_selections(catalog):
    active = [root for root in catalog['menus'] if root['id'] in catalog['modeling_roots']]
    commands = {node.get('command') for node in _walk(active)}
    selections, aliases = {}, []
    for key, group in GROUPS.items():
        selected = []
        for item in group['items']:
            command = EQUIVALENT_ITEMS.get(item['id'])
            if not command or command not in commands:
                selected.append(item['id'])
                continue
            calls = SPECS[command].calls
            if len(calls) != 1:
                raise ValueError('Native equivalence is no longer a single call: ' + command)
            call = calls[0]
            expected_context = 'INVOKE_REGION_WIN' if call.invoke else 'EXEC_REGION_WIN'
            if not (item['api'] == 'operator' and item['operator'] == call.operator and
                    _flatten(item['properties']) == _flatten(call.kwargs) and
                    item['invoke_context'] == expected_context and not item['conditions'] and
                    tuple(group['modes']) == tuple(call.modes)):
                raise ValueError('Native equivalence changed; review before deduplicating: ' + item['id'])
            aliases.append(dict(native_item=item['id'], command=command, group_key=key))
        selections[key] = tuple(selected)
    return selections, tuple(aliases)


def _chapter(root_id, path):
    first = path[0]
    if root_id == 'modeling.mesh':
        return {'Mirror': 'Mirror', 'Clean Up': 'Optimize', 'Cleanup Tools': 'Optimize',
                'Modifiers': 'Blender Modifiers', 'Attributes': 'Transfer',
                'Asset Tools': 'Optimize'}.get(first)
    if root_id == 'modeling.mesh_tools':
        return 'Tools'
    if root_id == 'modeling.mesh_display':
        return 'Display Attributes' if first in {'Face Data', 'Visibility', 'Attributes', 'Asset Tools'} else 'Normals'
    if root_id == 'modeling.curves':
        return 'Modify' if first in {'Transform', 'Duplicate', 'Spline'} else 'Edit'
    if root_id == 'modeling.surfaces':
        return 'Edit NURBS Surfaces'
    if root_id == 'modeling.uv':
        return 'Create' if first in {'Unwrap', 'Projection'} else 'Cut/Sew' if first == 'Seams' else 'Tools'
    return None


def _parent(root, path, icon):
    parent = root
    for depth, label in enumerate(path):
        children = parent['children']
        matching = [child for child in children if child['kind'] == 'menu' and child['label'] == label]
        if len(matching) > 1:
            raise ValueError('Ambiguous purpose directory: ' + str((root['id'], path)))
        if matching:
            parent = matching[0]
            continue
        index = len(children)
        headings = [(i, child['label']) for i, child in enumerate(children)
                    if child['kind'] == 'separator' and child.get('label')]
        if headings:
            chapter = _chapter(root['id'], path) if depth == 0 else None
            found = [i for i, title in headings if title == chapter]
            if len(found) != 1:
                raise ValueError('Native group needs an explicit chapter: ' + str((root['id'], path)))
            index = next((i for i, _ in headings if i > found[0]), len(children))
        node = dict(id=parent['id'] + '.native.' + label.lower().replace(' ', '_'),
                    label=label, kind='menu', icon=icon, origin='native_modeling', children=[])
        children.insert(index, node)
        parent = node
    return parent


def integrate_native_groups(catalog, selections=None):
    """Add approved native items; an explicit empty selection omits a duplicate group."""
    active_roots = [root for root in catalog['menus'] if root['id'] in catalog['modeling_roots']]
    # Component menus may live inside Edit Mesh while retaining their stable IDs.
    # Resolve only containers reachable from the active Modeling headers.
    roots = {node['id']: node for node in _walk(active_roots) if node['kind'] == 'menu'}
    if selections is None:
        selections, aliases = native_selections(catalog)
        catalog['native_equivalences'] = aliases
        catalog['native_item_equivalences'] = deduplicate_native_items(selections)
    placements = []
    for key, group in GROUPS.items():
        if group['root_id'] not in roots:
            raise ValueError('Native group is outside current Modeling scope: ' + key)
        known = tuple(item['id'] for item in group['items'])
        included = known if selections is None or key not in selections else tuple(selections[key])
        if not set(included) <= set(known):
            raise ValueError('Unknown native group item: ' + key)
        if not included:
            continue
        parent = _parent(roots[group['root_id']], group['path'], group['icon'])
        parent['children'].append(dict(id='workspace.native.' + key, kind='native_group',
            label=group['label'], icon=group['icon'], origin='native_modeling', group_key=key,
            include=included, row_count_hint=group['row_count_hint']))
        placements.append(dict(group_key=key, root_id=group['root_id'], path=group['path'],
                               source_menu=group['source_menu'], included=included))
    catalog['native_group_placements'] = tuple(placements)
    return catalog

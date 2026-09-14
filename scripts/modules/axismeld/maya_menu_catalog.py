# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bind trusted Blender commands to an independently captured Maya menu tree.

The operation registry describes capabilities, not Maya's visible hierarchy.
No command text from Maya or from a user profile is evaluated here.
"""
from hashlib import sha256

from .context_hotbox import COMPONENT_ROOT
from .context_modeling_hotbox import MODEL_ROOTS
from .creation_hotbox import CREATE_ROOT
from .object_modeling_hotbox import OBJECT_ROOT
from .tool_hotbox import TOOL_ROOTS
from .modeling_registry import SPECS


# Reviewed explicitly; dictionary order is never a choice among different actions.
PREFERRED_BINDINGS = {
    'FillHole': 'mesh.fill_holes',
    'ReducePolygon': 'mesh.reduce_modifier',
    'SmoothPolygon': 'mesh.subdivision_modifier',
    'PolyExtrude': 'mesh.extrude_region',
    'PolyMerge': 'mesh.merge_distance',
    'ConnectComponents': 'mesh.connect_path',
    'AveragePolygonNormals': 'normals.average_custom',
    'PolygonNormalEditTool': 'normals.rotate',
}
UNAVAILABLE_BINDINGS = {
    'ReorderRotationDialog': 'Rotation-order dialog adaptation not implemented',
    'SeparatePolygon': 'Selected-shell separation transaction not implemented',
    'PolyRemesh': 'Maya surface remesh is not equivalent to voxel-volume reconstruction',
    'CleanupPolygon': 'Complete cleanup selection and options not implemented',
    'TransferAttributes': 'Attribute-set and source/target transfer adaptation not implemented',
    'DetachComponent': 'Component-domain detach dispatch not implemented',
    'DeletePolyElements': 'Maya edge and vertex deletion semantics not implemented',
    'FlipTriangleEdge': 'Triangle-only edge flip eligibility not implemented',
    'SetVertexNormal': 'Absolute vertex-normal vector settings not implemented',
    'OpenCloseSurfaces': 'Surface direction and selected-boundary adaptation not implemented',
    'PolygonSelectionConstraints': 'Selection-constraint dialog not implemented; non-manifold selection is only one filter',
    'PrefixHierarchyNames': 'Hierarchy prefix naming and target scope adaptation not implemented',
    'SearchAndReplaceNames': 'Maya search/replace naming operation and target scope adaptation not implemented',
    'EditMembershipTool': 'Interactive deformer membership tool not implemented; assigning vertex weights is a different action',
    'DuplicateCurve': 'Extracting curves from surface boundaries and isoparms is not implemented',
    'SelectSimilar': 'Object/component similarity dispatch not implemented; vertex-normal filtering is only one criterion',
}
CORE_BINDINGS = {
    'SelectAll': ('selection.select_all', ''),
    'SelectNone': ('selection.clear', 'Deselect eligible Blender objects or mesh components in the source context'),
    'SelectToggleMode': ('selection.toggle_component', 'Toggle Blender Object and Mesh Edit modes on the active mesh'),
    'GrowPolygonSelectionRegion': ('selection.grow', 'Grow with Blender mesh topology traversal'),
    'ShrinkPolygonSelectionRegion': ('selection.shrink', 'Shrink with Blender mesh topology traversal'),
    'MoveTool': ('transform.move', ''),
    'RotateTool': ('transform.rotate', ''),
    'ScaleTool': ('transform.scale', ''),
    'SelectTool': ('tool.select', ''),
    'DisplayWireframe': ('view.wireframe', 'Blender Wireframe viewport'),
    'FrameAll': ('view.frame_all', 'Frame the source Blender viewport'),
    'FrameSelectedWithoutChildren': ('view.focus_selected', 'Frame selected items in the source viewport'),
    **{'CreatePolygon' + name.title(): (
        'mesh.create_' + name,
        'Create a Blender primitive at the 3D Cursor with Blender dimensions, topology and mode rules')
       for name in ('sphere', 'cube', 'cylinder', 'cone', 'torus', 'plane', 'disc')},
}
PATH_BINDINGS = {
    ('pane.shading', ('Shading', 'Smooth Shade All')):
        ('view.shaded', 'Blender Solid viewport; uses Blender object shading'),
}

# Filled from the trusted reference during construction. The runtime uses these
# to show only real Maya state affordances and to keep adaptation reasons visible.
MAYA_ROW_INDICATORS = {}
MAYA_ADAPTATION_REASONS = {}
MAYA_ROW_IDS = set()


def _walk(nodes):
    for entry in nodes:
        yield entry
        yield from _walk(entry['children'])


def _binding(reference, root_id, candidates):
    identity = reference.get('maya_command', '')
    if identity in UNAVAILABLE_BINDINGS:
        return '', UNAVAILABLE_BINDINGS[identity]
    if identity in PREFERRED_BINDINGS:
        command = PREFERRED_BINDINGS[identity]
    elif identity in CORE_BINDINGS:
        return CORE_BINDINGS[identity]
    elif (root_id, tuple(reference.get('path', ()))) in PATH_BINDINGS:
        return PATH_BINDINGS[root_id, tuple(reference['path'])]
    elif len(candidates.get(identity, ())) == 1:
        command = candidates[identity][0]
    elif identity and candidates.get(identity):
        return '', 'Maya command has multiple Blender adaptations; no implicit default'
    else:
        return '', 'Maya command adapter not implemented'
    spec = SPECS[command]
    return command, spec.difference or 'Uses Blender operation semantics'


def rebuild_maya_menus(roots, node):
    """Replace 22 visible menus; retain marking and Blender-only access separately."""
    from .maya_menu_reference import REFERENCE_MENUS

    roots = list(roots)
    old = {entry['id']: entry for entry in _walk(roots)}
    candidates = {}
    for spec in SPECS.values():
        for identity in spec.maya:
            candidates.setdefault(identity, []).append(spec.id)
    used_ids = set()
    used_commands = set()
    MAYA_ROW_INDICATORS.clear()
    MAYA_ADAPTATION_REASONS.clear()
    MAYA_ROW_IDS.clear()

    def convert(reference, root_id):
        kind = reference['kind']
        identifier = reference['id']
        label = reference['label']
        reason = reference.get('dynamic', '')
        if not isinstance(reason, str):
            reason = 'Dynamic Maya members are not connected to Blender'
        if kind == 'menu':
            children = [convert(child, root_id) for child in reference.get('children', ())]
            result = node(identifier, 'menu', label, children=children, presentation='list',
                          enabled=bool(children), reason=reason if reason else (
                              '' if children else 'Maya dynamic menu adapter not implemented'))
        elif kind == 'separator':
            result = node(identifier, 'separator', label, enabled=False)
        else:
            command, unavailable = _binding(reference, root_id, candidates)
            if command in SPECS:
                stable = 'm3.' + command
                if stable not in used_ids:
                    identifier = stable
                used_commands.add(command)
            result = node(identifier, 'command' if command else 'disabled', label,
                          command=command, enabled=bool(command),
                          reason=unavailable)
            if command:
                MAYA_ADAPTATION_REASONS[identifier] = unavailable
            indicator = reference.get('indicator', '')
            if indicator:
                result.update(indicator=indicator, checked=False)
                MAYA_ROW_INDICATORS[identifier] = indicator
            options = reference.get('options')
            if options:
                # A real options affordance is never the main action a second time.
                result['children'] = [node(identifier + '.options', 'disabled', 'Options',
                                           enabled=False,
                                           reason='Maya parameter adapter not implemented; main action is not invoked')]
        if result['id'] in used_ids:
            raise ValueError('Duplicate normalized Maya node ID: ' + result['id'])
        used_ids.add(result['id'])
        MAYA_ROW_IDS.add(result['id'])
        return result

    for reference in REFERENCE_MENUS:
        root_id = reference['id']
        target = old[root_id]
        replacement = convert(dict(reference, kind='menu'), root_id)
        target.clear()
        target.update(replacement)

    # Marking roots are internal invocation targets, not entries in Maya's Select,
    # Create or Modify menus. Keep their IDs and gestures without invented parents.
    marking_ids = (COMPONENT_ROOT, CREATE_ROOT, *MODEL_ROOTS, OBJECT_ROOT, *TOOL_ROOTS.values())
    marking = node('internal.marking', 'menu', 'Marking Menus', presentation='list',
                   children=tuple(old[identifier] for identifier in marking_ids))
    extensions = []
    categories = {}
    sections = {}
    for spec in SPECS.values():
        if spec.id in used_commands:
            continue
        if spec.category not in categories:
            category_id = 'internal.blender.' + spec.category.lower().replace(' ', '_')
            categories[spec.category] = node(category_id, 'menu', spec.category,
                                             presentation='list')
            extensions.append(categories[spec.category])
        parent = categories[spec.category]
        for depth, label in enumerate(spec.section):
            path = tuple(spec.section[:depth + 1])
            key = (spec.category, path)
            if key not in sections:
                # Labels are trusted registry data; hash the complete path to keep
                # IDs bounded and stable without ambiguity from punctuation.
                suffix = sha256('\0'.join((spec.category, *path)).encode('utf-8')).hexdigest()[:16]
                section = node(categories[spec.category]['id'] + '.section.' + suffix,
                               'menu', label, presentation='list')
                parent['children'].append(section)
                sections[key] = section
            parent = sections[key]
        parent['children'].append(
            node('m3.' + spec.id, 'command', spec.label, command=spec.id,
                 reason=spec.difference))
    if 'common.modify.view_orientations' in old:
        extensions.append(old['common.modify.view_orientations'])
    if 'pane.panels.views' in old:
        extensions.append(old['pane.panels.views'])
    if 'pane.panels.toggle_quad' in old:
        extensions.append(old['pane.panels.toggle_quad'])
    extensions.append(node('internal.blender.select_tool', 'command', 'Blender Select Tool',
                           command='tool.select', reason='Activate the Blender Box Select tool'))
    if 'center.controls.buttons' in old:
        extensions.append(old['center.controls.buttons'])
        controls = old['center.controls']
        controls['children'] = [child for child in controls['children']
                                if child['id'] not in {'center.controls.buttons',
                                                       'center.controls.separator.axismeld'}]
    blender = node('internal.blender', 'menu', 'Blender Extensions', presentation='list',
                   children=extensions)
    roots.append(node('internal', 'menu', 'AxisMeld Internal Menus', presentation='list',
                      children=(marking, blender)))
    identifiers = [entry['id'] for entry in _walk(roots)]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate catalog node IDs after Maya hierarchy conversion')
    return tuple(roots)

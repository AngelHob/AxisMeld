# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya component content; target identity and dispatch stay runtime-owned."""
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
                     ('vertex_face', 'Vertex Face', 'SW', 'M2-vertex-face'),
                     ('multi', 'Multi', 'SE', 'M2-multi-component'))]
    children.insert(4, node(COMPONENT_ROOT + '.uv', 'menu', 'UV', direction='E',
                            presentation='list', children=[
        node(COMPONENT_ROOT + '.uv.' + suffix, 'disabled', label, enabled=False,
             reason='Target-bound UV selection adapter not implemented')
        for suffix, label in (('uv', 'UV'), ('shell', 'UV Shell'))]))
    return node(COMPONENT_ROOT, 'menu', 'Active Mesh Components', children=children,
                presentation='radial')


# Maya 2026 dagMenuProc.mel:2618-2806; buildShaderMenus.mel:501-557.
# Only these fixed rows can dispatch. Source/target eligibility remains runtime-owned.
COMPONENT_MENU = 'context.component_menu'
COMPONENT_MENU_COMMANDS = {COMPONENT_MENU + '.' + suffix: command for suffix, command in (
    ('select_all', 'selection.select_all'), ('deselect_all', 'selection.clear'),
    ('select_hierarchy', 'selection.hierarchy'), ('invert_selection', 'selection.invert'),
    ('actions.template', 'display.template'), ('actions.untemplate', 'display.untemplate'),
    ('actions.unparent', 'edit.unparent'),
)}
UNAVAILABLE_INDICATORS = {COMPONENT_MENU + '.metadata.visualize': 'checkbox'}


def component_companion(node):
    """Screenshot's 22 main rows and seven visible group separators.

    Dynamic DG, material, UV/color and plugin entries require a target-bound data
    bridge; placeholders describe that boundary instead of inventing scene nodes.
    """
    def row(suffix, label, reason='', *, options=False, checked=None):
        identifier = COMPONENT_MENU + '.' + suffix
        command = COMPONENT_MENU_COMMANDS.get(identifier, '')
        children = ()
        if options:
            children = (node(identifier + '.options', 'disabled', 'Options', enabled=False,
                             reason='Target-bound parameter editor not implemented'),)
        item = node(identifier, 'command' if command else 'disabled', label,
                    command=command, enabled=bool(command), children=children,
                    reason=reason or 'Target-bound Maya operation not implemented')
        if checked is not None:
            item.update(indicator='checkbox', checked=checked)
        return item

    def menu(suffix, label, children):
        return node(COMPONENT_MENU + '.' + suffix, 'menu', label,
                    presentation='list', children=children)

    def sep(suffix):
        return node(COMPONENT_MENU + '.separator_' + suffix, 'separator', '', enabled=False)

    def dynamic(suffix, label='Target data unavailable'):
        return row(suffix, label, 'Captured-target data bridge not implemented; active-object data is not substituted')

    # historyPopupFill.mel:248-262,367-377; dynamic node options need real node IDs.
    def history(suffix, label):
        return menu(suffix, label, (
            row(suffix+'.select_all', 'Select All '+label),
            row(suffix+'.enable_all', 'Enable All '+label),
            row(suffix+'.disable_all', 'Disable All '+label), sep(suffix),
            dynamic(suffix+'.nodes', 'History nodes unavailable'),
            row(suffix+'.all', 'All '+label+'...'),
        ))

    # dagMenuProc.mel:2153-2177. English labels checked in resources/MayaStrings.
    clips = menu('time_editor.select_clip', 'Select Clip', tuple(
        menu('time_editor.select_clip.'+parent, label, tuple(
            row('time_editor.select_clip.'+parent+'.'+match, 'Match '+word)
            for match, word in (('exact', 'Exact'), ('all', 'All'), ('any', 'Any'), ('none', 'None'))))
        for parent, label in (('exclude_parent', 'Exclude Parent'), ('include_parent', 'Include Parent'))))
    return node(
        COMPONENT_MENU, 'menu', 'Object Context', presentation='list', children=(
            row('object', 'Object...', 'Captured object attribute editor not implemented'), sep('object'),
            row('select', 'Select', 'Captured-target selection transaction not implemented'),
            row('select_all', 'Select All', 'Select all in the current Blender selection domain'),
            row('deselect_all', 'Deselect All', 'Clear the current Blender selection domain'),
            row('select_hierarchy', 'Select Hierarchy', 'Selected Object hierarchy only; no preselection commit'),
            row('invert_selection', 'Invert Selection', 'Invert the current Blender selection domain'), sep('selection'),
            row('select_similar', 'Select Similar', options=True), sep('similar'),
            row('make_live', 'Make Live', 'Maya live-surface selection and snapping workflow not implemented'), sep('live'),
            menu('dg_traversal', 'DG Traversal', (dynamic('dg_traversal.nodes', 'DG nodes unavailable'),)),
            history('inputs', 'Inputs'), history('outputs', 'Outputs'),
            menu('paint', 'Paint', (row('paint.select', 'Paint Select'), row('paint.3d', '3D Paint'),
                                  dynamic('paint.attributes', 'Paintable attributes unavailable'))),
            menu('metadata', 'Metadata', (
                row('metadata.edit', 'Edit Metadata...'),
                row('metadata.visualize', 'Visualize Metadata', options=True, checked=False),
                menu('metadata.stream', 'Select Stream', (dynamic('metadata.stream.data', 'Metadata streams unavailable'),)),
            )),
            menu('actions', 'Actions', (
                row('actions.template', 'Template', 'Selected Object display only; no preselection commit'),
                row('actions.untemplate', 'Untemplate', 'Existing Object selection required; target identity checked before dispatch'),
                row('actions.unparent', 'Unparent', 'Blender Keep Transform on current Object selection only'),
                row('actions.bounds', 'Bounding Box', 'Maya toggle not implemented; existing Blender bounds commands are one-way'),
            )),
            menu('uv_sets', 'UV Sets', (row('uv_sets.linking', 'UV Linking...'),
                row('uv_sets.editor', 'UV Set Editor'), sep('uv_sets'), dynamic('uv_sets.data', 'UV sets unavailable'))),
            menu('color_sets', 'Color Sets', (row('color_sets.editor', 'Color Set Editor'),
                sep('color_sets'), dynamic('color_sets.data', 'Color sets unavailable'))),
            menu('time_editor', 'Time Editor', (clips,)), sep('time_editor'),
            menu('scene_assembly', 'Scene Assembly', (dynamic('scene_assembly.data', 'Scene Assembly unavailable'),)),
            sep('assembly'), row('material_attributes', 'Material Attributes...', 'Captured-target material editor not implemented'),
            sep('material'),
            menu('assign_new_material', 'Assign New Material', (row('assign_new_material.new', 'New Material...'),
                dynamic('assign_new_material.plugins', 'Material provider entries unavailable'))),
            menu('assign_favorite_material', 'Assign Favorite Material',
                 (dynamic('assign_favorite_material.data', 'Material favorites unavailable'),)),
            menu('assign_existing_material', 'Assign Existing Material',
                 (dynamic('assign_existing_material.data', 'Scene materials unavailable'),)),
        ))

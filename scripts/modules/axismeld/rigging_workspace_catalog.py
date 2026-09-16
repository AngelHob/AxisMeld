# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Add native Rigging entry points without changing captured Maya menu payloads."""

RIGGING_ROOTS = ('menubar.rigging.skeleton', 'menubar.rigging.skin')

# Entries are one visible menu/operator row each. Full native submenus retain
# their own hierarchy, context and extension callbacks in the UI renderer.
ENTRIES = {
    'skeleton.create': dict(root=RIGGING_ROOTS[0], chapter='Joints', label='Add Armature', icon='ARMATURE_DATA'),
    'skeleton.edit_bones': dict(root=RIGGING_ROOTS[0], chapter='Joints', label='Edit Bones', icon='EDITMODE_HLT'),
    'skeleton.ik': dict(root=RIGGING_ROOTS[0], chapter='IK', label='Inverse Kinematics', icon='CON_KINEMATIC'),
    'skeleton.pose': dict(root=RIGGING_ROOTS[0], chapter='IK', label='Pose', icon='POSE_HLT'),
    'skin.bind': dict(root=RIGGING_ROOTS[1], chapter='Bind', label='Armature Deform', icon='MOD_ARMATURE'),
    'skin.weight_paint': dict(root=RIGGING_ROOTS[1], chapter='Weight Maps',
                              label='Weight Paint Mode', icon='WPAINT_HLT'),
    'skin.weights': dict(root=RIGGING_ROOTS[1], chapter='Weight Maps', label='Weights', icon='WPAINT_HLT'),
    'skin.vertex_groups': dict(root=RIGGING_ROOTS[1], chapter='Other', label='Vertex Groups', icon='GROUP_VERTEX'),
    'skin.group_specials': dict(root=RIGGING_ROOTS[1], chapter='Other',
                                label='Vertex Group Specials', icon='GROUP_VERTEX'),
}


def _chapter_end(children, label):
    headings = [(i, node['label']) for i, node in enumerate(children)
                if node['kind'] == 'separator' and node.get('label')]
    starts = [i for i, title in headings if title == label]
    if len(starts) != 1:
        raise ValueError('Rigging native entry needs one exact Maya chapter: ' + label)
    return next((i for i, _title in headings if i > starts[0]), len(children))


def integrate_rigging_groups(catalog):
    """Insert native rows in-place and return the catalog; no bpy or mode changes.

    Validate both source roots before writing, preserve every original node and
    option unchanged, and permit repeated integration without duplicated rows.
    """
    roots = {}
    for identifier in RIGGING_ROOTS:
        matching = [root for root in catalog['menus'] if root['id'] == identifier]
        if len(matching) != 1:
            raise ValueError('Rigging needs one original domain root: ' + identifier)
        roots[identifier] = matching[0]
    pending = {identifier: list(root['children']) for identifier, root in roots.items()}
    for key, entry in ENTRIES.items():
        children = pending[entry['root']]
        index = _chapter_end(children, entry['chapter'])
        node = dict(id='workspace.rigging_native.' + key, kind='rigging_native',
                    label=entry['label'], icon=entry['icon'], origin='native_rigging',
                    native_key=key, row_count_hint=1)
        existing = [child for child in children if child['id'] == node['id']]
        if existing:
            if existing != [node]:
                raise ValueError('Rigging native entry payload was changed: ' + key)
            continue
        children.insert(index, node)
    for identifier, children in pending.items():
        roots[identifier]['children'] = children
    catalog['rigging_roots'] = RIGGING_ROOTS
    return catalog

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya 2026 tool menu content; unavailable Maya state is never inferred."""

TOOL_ROOTS = {'tool.select': 'tools.select', 'transform.move': 'tools.move',
              'transform.rotate': 'tools.rotate', 'transform.scale': 'tools.scale'}
DIRECTIONS = frozenset({'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'})
ORIENTATIONS = {f'orientation.{tool}.{name}': (slot, value)
                for tool, slot in (('move', 1), ('rotate', 2), ('scale', 3))
                for name, value in (('world', 'GLOBAL'), ('object', 'LOCAL'),
                                     ('normal', 'NORMAL'), ('view', 'VIEW'),
                                     *((('gimbal', 'GIMBAL'),) if tool == 'rotate' else ()))}
SELECTION_TOOLS = {'selection.marquee': 'builtin.select_box',
                   'selection.lasso': 'builtin.select_lasso',
                   'selection.paint': 'builtin.select_circle'}
MENU_COMMANDS = frozenset({*TOOL_ROOTS, *ORIENTATIONS, *SELECTION_TOOLS, 'selection.clear'})
_TOOLS = ('select', 'move', 'rotate', 'scale')
COMPANION_ROOTS = {f'tools.{tool}': f'tools.{tool}_menu' for tool in _TOOLS}
COMPANION_ROOTS.update({f'tools.{tool}.select': f'tools.{tool}.select_menu' for tool in _TOOLS})

# Exact fixed IDs only. Empty checkbox/radio means unavailable, not Maya's current state.
UNAVAILABLE_INDICATORS = {}
for _tool in _TOOLS:
    _p = 'tools.' + _tool
    for _suffix in ('symmetry.options', 'symmetry.world', 'symmetry.object', 'symmetry.topology',
                    'symmetry.x', 'symmetry.y', 'symmetry.z', 'select.options', 'select.closest',
                    'select.backfaces', 'select.container', 'select.camera', 'select.soft.object',
                    'select.soft.toggle', 'select.soft.volume', 'select.soft.surface',
                    'select.soft.global', 'select.soft.color', 'select_menu.automatic'):
        UNAVAILABLE_INDICATORS[_p + '.' + _suffix] = 'checkbox'
    if _tool == 'select':
        for _suffix in ('drag', 'camera'):
            UNAVAILABLE_INDICATORS[_p + '.' + _suffix] = 'checkbox'
        UNAVAILABLE_INDICATORS[_p + '_menu.automatic'] = 'checkbox'
    else:
        for _suffix in (('axis.custom',) if _tool == 'rotate' else
                        ('axis.normal', 'axis.parent', 'axis.rotation', 'axis.live', 'axis.custom.custom')):
            UNAVAILABLE_INDICATORS[_p + '.' + _suffix] = 'checkbox'
        for _suffix in (('spacing', 'snap.options', 'snap.vertex', 'snap.relative', 'snap.face')
                        if _tool == 'move' else ('discrete',) if _tool == 'rotate'
                        else ('discrete', 'relative')):
            UNAVAILABLE_INDICATORS[_p + '.' + _suffix] = 'checkbox'
        _menu = _p + '_menu'
        for _suffix in ('extrude', 'duplicate', 'preserve_uv', 'preserve_children', 'tweak',
                        'transform_constraints.normals',
                        *({'move': ('update_triad',), 'rotate': ('free_rotate', 'relative'),
                           'scale': ('negative',)}[_tool])):
            UNAVAILABLE_INDICATORS[_menu + '.' + _suffix] = 'checkbox'
        for _suffix in ('off', 'angle', 'border', 'loop', 'ring', 'shell', 'uv_loop'):
            UNAVAILABLE_INDICATORS[_menu + '.selection_constraints.' + _suffix] = 'radio'
        for _suffix in ('off', 'edge', 'surface'):
            UNAVAILABLE_INDICATORS[_menu + '.transform_constraints.' + _suffix] = 'radio'
        if _tool != 'move':
            for _suffix in ('default', 'object', 'manip', *(('selection',) if _tool == 'rotate' else ())):
                UNAVAILABLE_INDICATORS[_menu + '.center.' + _suffix] = 'radio'


def _disabled(node, identifier, label, direction=None):
    indicator = UNAVAILABLE_INDICATORS.get(identifier)
    result = node(identifier, 'disabled', label, enabled=False, direction=direction,
                  reason='M1-P08: Maya state not adapted' if indicator else 'M1-P08: Maya tool adapter pending')
    if indicator:
        result.update(indicator=indicator, checked=False)
    return result


def tool_menus(node):
    def action(p, name, label, command, direction):
        return node(p + '.' + name, 'command', label, command=command, direction=direction)

    def pending(p, entries):
        return [_disabled(node, p + '.' + name, label, direction) for name, label, direction in entries]

    def radial(p, name, label, direction, children):
        return node(p + '.' + name, 'menu', label, children=children,
                    direction=direction, presentation='radial')

    def custom(p):
        return pending(p, (('custom', 'Custom', 'E'), ('component', 'Set to Component', 'W'),
                           ('point', 'Set To Point', 'SW'), ('edge', 'Set To Edge', 'S'),
                           ('face', 'Set To Face', 'SE'), ('object', 'Set To Object', 'N'),
                           ('reset', 'Reset', 'NW')))

    roots = []
    for tool in _TOOLS:
        p = 'tools.' + tool
        children = [
            radial(p, 'symmetry', 'Symmetry', 'N', pending(p + '.symmetry', (
                ('options', 'Symmetry', 'N'), ('world', 'World', 'W'), ('object', 'Object', 'E'),
                ('topology', 'Topology', 'NE'), ('x', 'X Axis', 'SW'),
                ('y', 'Y Axis', 'S'), ('z', 'Z Axis', 'SE')))),
            radial(p, 'select', 'Select', 'S', [
                *pending(p + '.select', (('options', 'Preselection Highlight', 'N'),
                    ('closest', 'Highlight Nearest Component', 'NE'),
                    ('backfaces', 'Highlight Backfaces', 'E'), ('container', 'Asset Centric', 'SE'))),
                action(p + '.select', 'marquee', 'Marquee', 'selection.marquee', 'NW'),
                _disabled(node, p + '.select.camera', 'Camera-Based Selection', 'W'),
                action(p + '.select', 'clear', 'Clear Selection', 'selection.clear', 'SW'),
                radial(p + '.select', 'soft', 'Soft Select', 'S', pending(p + '.select.soft', (
                    ('object', 'Object', 'N'), ('toggle', 'Soft Select', 'S'), ('volume', 'Volume', 'SW'),
                    ('surface', 'Surface', 'W'), ('global', 'Global', 'NW'), ('color', 'Color Feedback', 'E'))))]),
        ]
        if tool == 'select':
            children += [action(p, name, title, 'selection.' + name, direction)
                         for name, title, direction in (('marquee', 'Marquee', 'NW'),
                             ('paint', 'Paint Select', 'W'), ('lasso', 'Lasso', 'SW'),
                             ('clear', 'Clear Selection', 'SE'))]
            children += pending(p, (('drag', 'Drag', 'NE'), ('camera', 'Camera-Based Selection', 'E')))
        else:
            children += [action(p, name, title, f'orientation.{tool}.{name}', direction)
                         for name, title, direction in (('world', 'World', 'W'),
                             ('object', 'Object', 'NW'), ('normal', 'Component', 'NE'))]
            axis = p + '.axis'
            axis_children = custom(axis) if tool == 'rotate' else [
                *pending(axis, (('normal', 'Normal', 'NW'), ('parent', 'Parent', 'W'),
                    ('rotation', 'Along Rotation Axis', 'NE'), ('live', 'Live Object Axis', 'N'))),
                radial(axis, 'custom', 'Custom', 'SW', custom(axis + '.custom'))]
            children.append(radial(p, 'axis', 'Custom' if tool == 'rotate' else 'Axis', 'SW', axis_children))
            if tool == 'rotate':
                children.append(action(p, 'gimbal', 'Gimbal', 'orientation.rotate.gimbal', 'E'))
                children += pending(p, (('discrete', 'Discrete Rotate', 'SE'),))
            elif tool == 'move':
                children.append(radial(p, 'snap', 'Snap', 'E', pending(p + '.snap', (
                    ('options', 'Discrete Move', 'E'), ('vertex', 'Vertex', 'SE'),
                    ('relative', 'Relative Mode', 'S'), ('face', 'Face Center', 'SW')))))
                children += pending(p, (('spacing', 'Keep Spacing', 'SE'),))
            else:
                children += pending(p, (('discrete', 'Snap Scale', 'E'), ('relative', 'Relative', 'SE')))
        roots.append(node(p, 'menu', tool.title() + ' Tool', children=children, presentation='radial'))
    return roots


def tool_companions(node):
    """Native lower lists from the four *MarkingMenuImpl and shared Select MELs."""
    def disabled(p, name, label):
        return _disabled(node, p + '.' + name, label)

    def sep(p, name):
        return node(p + '.separator.' + name, 'separator', '', enabled=False)

    def menu(p, name, label, children):
        return node(p + '.' + name, 'menu', label, children=children, presentation='list')

    def constraints(p):
        selection = p + '.selection_constraints'
        transform = p + '.transform_constraints'
        return [menu(p, 'selection_constraints', 'Selection Constraints', [
            disabled(selection, name, label) for name, label in (
                ('off', 'Off'), ('angle', 'Angle'), ('border', 'Border'), ('loop', 'Edge Loop'),
                ('ring', 'Edge Ring'), ('shell', 'Shell'), ('uv_loop', 'UV Edge Loop'))]),
            menu(p, 'transform_constraints', 'Transform Constraints', [
                disabled(transform, 'off', 'Off'), disabled(transform, 'edge', 'Edge Slide'),
                disabled(transform, 'surface', 'Surface Slide'), sep(transform, 'normals'),
                disabled(transform, 'normals', 'Along Normals')])]

    roots = []
    for tool in _TOOLS:
        p = 'tools.' + tool + '_menu'
        if tool == 'select':
            children = [disabled(p, 'automatic', 'Automatic Camera-Based Selection')]
        else:
            children = constraints(p) + [sep(p, 'shift'), disabled(p, 'extrude', 'Shift Extrude'),
                disabled(p, 'duplicate', 'Shift Duplicate'), sep(p, 'settings')]
            if tool != 'move':
                choices = [('default', 'Default'), ('object', 'Object'), ('manip', 'Manip')]
                if tool == 'rotate':
                    choices.append(('selection', 'Selection'))
                children.append(menu(p, 'center', tool.title() + ' Center', [
                    disabled(p + '.center', name, label) for name, label in choices]))
                name, label = ('free_rotate', 'Free Rotate') if tool == 'rotate' else ('negative', 'Prevent Negative Scale')
                children.append(disabled(p, name, label))
            children += [disabled(p, 'preserve_uv', 'Preserve UVs'),
                         disabled(p, 'preserve_children', 'Preserve Children'), disabled(p, 'tweak', 'Tweak Mode')]
            if tool == 'move':
                children.append(disabled(p, 'update_triad', 'Update Triad'))
            elif tool == 'rotate':
                children.append(disabled(p, 'relative', 'Relative'))
            children += [sep(p, 'options'), disabled(p, 'options', tool.title() + ' Options')]
        roots.append(node(p, 'menu', tool.title() + ' Tool Menu', children=children, presentation='list'))
    for tool in _TOOLS:
        p = 'tools.' + tool + '.select_menu'
        roots.append(node(p, 'menu', 'Select Menu', presentation='list',
                          children=[disabled(p, 'automatic', 'Automatic Camera-Based Selection')]))
    return roots

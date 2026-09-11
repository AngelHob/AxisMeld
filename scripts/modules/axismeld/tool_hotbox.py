# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Classic Maya tool-menu positions and bounded Blender adaptations."""

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


def tool_menus(node):
    """Build owned trees using the catalog's single node constructor."""
    def action(prefix, name, label, command, direction=None):
        return node(prefix + '.' + name, 'command', label, command=command, direction=direction)

    def planned(prefix, name, label, code, difference):
        return node(prefix + '.' + name, 'disabled', label, enabled=False,
                    reason=f'M1-P{code:02}: {difference}')

    def options(prefix, name, label, direction, children):
        return node(prefix + '.' + name, 'menu', label, children=children,
                    direction=direction, presentation='list')

    roots = []
    for tool, label in (('select', 'Select Tool'), ('move', 'Move Tool'),
                         ('rotate', 'Rotate Tool'), ('scale', 'Scale Tool')):
        p = 'tools.' + tool
        children = [
            options(p, 'symmetry', 'Symmetry', 'N', (
                planned(p + '.symmetry', 'options', 'Symmetry Options', 1,
                        'Blender symmetry capabilities exist; tool adapter pending'),)),
            options(p, 'select', 'Select', 'S', (
                action(p + '.select', 'all', 'Select All', 'selection.select_all'),
                action(p + '.select', 'clear', 'Clear Selection', 'selection.clear'),
                planned(p + '.select', 'soft', 'Soft Selection', 7,
                        'Proportional editing exists; Maya soft-selection adapter pending'),
                planned(p + '.select', 'options', 'Selection Options', 7,
                        'Advanced selection options adapter pending'),)),
        ]
        if tool == 'select':
            children += [action(p, name, title, 'selection.' + name, direction)
                         for name, title, direction in (
                             ('marquee', 'Marquee Select', 'NW'),
                             ('paint', 'Paint Selection', 'W'),
                             ('lasso', 'Lasso Select', 'SW'),
                             ('clear', 'Clear Selection', 'SE'))]
            children += [options(p, name, title, direction, (
                planned(p + '.' + name, 'options', title, code, reason),))
                for name, title, direction, code, reason in (
                    ('drag', 'Drag Select', 'NE', 2, 'Blender drag-selection behavior exists; adapter pending'),
                    ('camera', 'Camera Based Selection', 'E', 3,
                     'Blender occlusion selection exists; automatic camera-based policy adapter pending'))]
        else:
            children += [action(p, name, title, f'orientation.{tool}.{name}', direction)
                         for name, title, direction in (('world', 'World', 'W'),
                             ('object', 'Object', 'NW'), ('normal', 'Normal Average', 'NE'))]
            axis_label = 'Custom Axis' if tool == 'rotate' else 'Axis'
            children.append(options(p, 'axis', axis_label, 'SW', (
                action(p + '.axis', 'view', 'View (Blender)', f'orientation.{tool}.view'),
                planned(p + '.axis', 'custom', 'Custom Axis / Alignment', 6,
                        'Custom orientations exist; Maya axis alignment adapter pending'),
                planned(p + '.axis', 'tool', 'Tool Options', 8,
                        'Smart extrude/duplicate and pivot variants await individual capability mapping'),
                planned(p + '.axis', 'uv', 'Preserve UV', 9, 'UV workflow deferred; no UV state changes'),)))
            if tool == 'rotate':
                children.append(action(p, 'gimbal', 'Gimbal', 'orientation.rotate.gimbal', 'E'))
                entries = (('discrete', 'Discrete Rotate', 'SE', 5),)
            elif tool == 'move':
                entries = (('snap', 'Snap', 'E', 5), ('spacing', 'Keep Spacing', 'SE', 4))
            else:
                entries = (('discrete', 'Discrete Scale', 'E', 5), ('relative', 'Relative', 'SE', 5))
            children += [options(p, name, title, direction, (
                planned(p + '.' + name, 'options', title, code,
                        'Native transform/snapping capabilities exist; Maya option adapter pending'),))
                         for name, title, direction, code in entries]
        roots.append(node(p, 'menu', label, children=children, presentation='radial'))
    return roots

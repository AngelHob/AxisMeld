# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Maya buildSelectAllMM history menu; reuse bounded existing adaptations."""
from .modeling_registry import SPECS

HISTORY_ROOT = 'context.history'
HISTORY_TRIGGER = 'view.frame_all'
HISTORY_COMMANDS = {
    'delete': 'edit.bake_selected',
    'delete_non_deformer': 'edit.bake_selected_non_deform',
    'freeze': 'transform.apply_all',
    'reset': 'transform.reset_all',
}


def history_menu(node):
    rows = []
    for suffix, label, direction in (
            ('inputs', 'Select All Inputs', 'W'), ('outputs', 'Select All Outputs', 'E'),
            ('enable', 'Enable All Outputs', 'N'), ('disable', 'Disable All Outputs', 'S'),
            ('delete', 'Delete History', 'NW'), ('delete_non_deformer', 'Delete Non-Deformer History', 'NE'),
            ('freeze', 'Freeze Transformations', 'SE'), ('reset', 'Reset Transformations', 'SW')):
        identifier = HISTORY_ROOT + '.' + suffix
        command = HISTORY_COMMANDS.get(suffix, '')
        item = node(identifier, 'command' if command else 'disabled', label,
                    command=command, enabled=bool(command), direction=direction,
                    reason=SPECS[command].difference if command else
                    'Maya dependency-graph input/output operations are not adapted')
        if suffix in {'freeze', 'reset'}:
            item['children'] = [node(identifier + '.options', 'disabled', 'Options', enabled=False,
                                     reason='Maya transformation options are not adapted; main action is not invoked')]
        rows.append(item)
    return node(HISTORY_ROOT, 'menu', 'History Operations', children=rows, presentation='radial')

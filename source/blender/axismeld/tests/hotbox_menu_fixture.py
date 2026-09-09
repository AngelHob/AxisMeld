# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export the real default catalog as a value fixture for the pure native layout test."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts' / 'modules'))
from axismeld.hotbox_catalog import default_catalog


def node(value):
    fields = ', '.join(json.dumps(value.get(key, ''), ensure_ascii=True)
                       for key in ('id', 'label', 'command', 'reason', 'value'))
    children = ',\n'.join(node(child) for child in value['children'])
    return ('{' + fields + ', MenuKind::' + value['kind'].title() + ', ' +
            str(value['enabled']).lower() + ', {' + children + '}}')


Path(sys.argv[1]).write_text(
    '// Generated from the production catalog. Do not edit.\n'
    'static MenuSnapshot default_snapshot() { return {1, "rows", 25, '
    '{"common", "pane", "modeling"}, {"views", "views", "views"}, {' +
    ',\n'.join(node(root) for root in default_catalog()) + '}}; }\n', encoding='utf-8')

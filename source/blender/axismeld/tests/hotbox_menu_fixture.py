# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export the real default catalog as a value fixture for the pure native layout test."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts' / 'modules'))
from axismeld.hotbox_catalog import default_catalog
from axismeld.hotbox_runtime import make_snapshot, serialize_snapshot


definitions = []


def node(value):
    fields = ', '.join(json.dumps(value.get(key, ''), ensure_ascii=True)
                       for key in ('id', 'label', 'command', 'reason', 'value'))
    children = ',\n'.join(node(child) for child in value['children'])
    name = f'fixture_node_{len(definitions)}'
    initializer = ('{' + fields + ', MenuKind::' + value['kind'].title() + ', ' +
            str(value['enabled']).lower() + ', {' + children + '}, ' +
            json.dumps(value.get('direction', '')) + ', ' +
            json.dumps(value.get('presentation', '')) + ', ' +
            json.dumps(value.get('indicator', '')) + ', ' +
            str(value.get('checked', False)).lower() + '}')
    # Bound each initializer's expression tree; one deeply nested default tree can
    # exhaust MSVC commit memory while compiling exception cleanup code.
    definitions.append(f'static MenuNode {name}() {{ return {initializer}; }}\n')
    return name + '()'


roots = ',\n'.join(node(root) for root in default_catalog())
serialized = serialize_snapshot(make_snapshot(generation=73))
json_chunks = ',\n'.join(json.dumps(serialized[index:index + 4096], ensure_ascii=True)
                         for index in range(0, len(serialized), 4096))
Path(sys.argv[1]).write_text(
    '// Generated from the production catalog. Do not edit.\n'
    '#ifndef AXISMELD_JSON_FIXTURE_ONLY\n'
    + ''.join(definitions) + 'static MenuSnapshot default_snapshot() { return {1, "rows", 25, '
    '{"common", "pane", "modeling"}, {"views", "views", "views"}, {' +
    roots + '}}; }\n#endif\n'
    'static std::string default_snapshot_json() {\n'
    '  static const char *chunks[] = {\n' + json_chunks + '\n};\n'
    '  std::string result;\n'
    f'  result.reserve({len(serialized.encode("utf-8"))});\n'
    '  for (const char *chunk : chunks) { result += chunk; }\n'
    '  return result;\n}\n', encoding='utf-8')

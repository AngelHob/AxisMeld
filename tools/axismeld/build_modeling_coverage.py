# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Join independently audited Maya identities to the actual trusted M3 registry."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from pprint import pformat
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
from axismeld.commands import COMMANDS, baseline_bindings
from axismeld.keymap import binding_events
from axismeld.modeling_registry import SPECS, CATEGORIES
from axismeld.hotbox_catalog import default_catalog

parser = argparse.ArgumentParser()
parser.add_argument('--source-dir', type=Path, required=True)
args = parser.parse_args()
actions = json.loads((args.source_dir / 'm3-maya-actions.json').read_text(encoding='utf8'))
catalog = {}
pending = list(default_catalog())
while pending:
    entry = pending.pop()
    catalog[entry['id']] = entry
    pending.extend(entry['children'])
menu_ids = {identifier for identifier, entry in catalog.items() if entry['kind'] == 'menu'}
# Parse the independently verified official Windows default-input table. A miss is
# recorded as unverified, never invented from the Blender binding or personal overlay.
maya_inputs = {}
for line in (args.source_dir / 'm3-maya-inventory.md').read_text(encoding='utf8').splitlines():
    cells = [cell.strip() for cell in line.strip('|').split('|')]
    if len(cells) == 4 and cells[3].startswith('hotkeySetup.mel:'):
        maya_inputs.setdefault(cells[1], []).append({
            'input': cells[0], 'release': cells[2], 'source': cells[3]})
audits = {}
for family in ('common', 'mesh', 'shapes'):
    records = json.loads((args.source_dir / f'm3-{family}-coverage.json').read_text(encoding='utf8'))
    if isinstance(records, dict):
        records = records['records']
    audits[family] = {record['identity']: record for record in records}
    if len(audits[family]) != len(records):
        raise ValueError('Duplicate audited identity in ' + family)


def safe_identity(identity):
    clean = re.sub('[^A-Za-z0-9_.-]', '_', identity)
    if clean != identity or len(clean) > 85:
        clean = clean[:70] + '_' + hashlib.sha256(identity.encode()).hexdigest()[:10]
    return clean


rows, gaps, aliases, unresolved = [], [], [], []
alias_keys = set()
for action in actions:
    if action['scope'] == 'non_action':
        continue
    identity = action['identity']
    family = ('common' if action['menu'] in {'Select', 'Modify', 'Edit', 'Create', 'Display'} else
              'mesh' if action['menu'] in {'Mesh', 'Edit Mesh', 'Mesh Tools', 'Mesh Display'} else 'shapes')
    audit = audits[family].get(identity)
    if audit is None:
        audit = next((records[identity] for records in audits.values() if identity in records), None)
    row = dict(action)
    row['maya_default_inputs'] = maya_inputs.get(identity, [])
    row['maya_input_status'] = 'verified' if row['maya_default_inputs'] else '未核得默认'
    scope = (audit or {}).get('scope_override', action['scope'])
    if scope != action['scope']:
        row['inventory_scope'] = action['scope']
        row['scope'] = scope
        row['scope_reason'] = audit['scope_reason']
    row['manual_status'] = '待人工测试' if scope == 'in_scope' else '本轮范围外或动态依赖'
    if scope != 'in_scope':
        row.update({key: value for key, value in (audit or {}).items()
                    if key in {'plan', 'reason', 'dependency', 'acceptance', 'availability'}})
        row['classification'] = 'deferred' if scope == 'out_of_scope' else 'dynamic_dependency'
        row['commands'] = (audit or {}).get('commands', [])
    elif audit is None:
        unresolved.append(identity)
        continue
    else:
        if audit.get('availability') == 'native_adapter_pending':
            raise ValueError(f'{identity}: available native capability still needs its adapter')
        row.update(audit)
        commands = row.get('commands', [])
        if commands:
            unknown = set(commands) - (menu_ids if row.get('kind') == 'menu' else COMMANDS.keys())
            if unknown:
                raise ValueError(f'{identity}: unknown commands {sorted(unknown)}')
            row['classification'] = 'adapted'
            row.pop('plan', None)
            row['actual_menu_paths'] = []
            for command in commands:
                if command in menu_ids and row.get('kind') == 'menu':
                    row['actual_menu_paths'].append(command)
                    continue
                spec = SPECS.get(command)
                if spec:
                    row['actual_menu_paths'].append(' > '.join((spec.category, *spec.section, spec.label)))
                # Keep cross-category Maya paths usable without duplicating the
                # command implementation, binding, or trusted native allowlist.
                if spec and spec.category != action['menu']:
                    section = action.get('suggested_group', [action['menu']])[1:]
                    alias_key = (action['menu'], tuple(section), command)
                    if alias_key not in alias_keys:
                        alias_keys.add(alias_key)
                        aliases.append({'identity': safe_identity(identity + '.' + command),
                                        'category': action['menu'], 'section': section,
                                        'label': spec.label, 'command': command})
                    row['actual_menu_paths'].append(' > '.join((action['menu'], *section, spec.label)))
        else:
            for field in ('plan', 'reason', 'dependency', 'acceptance'):
                if not row.get(field):
                    raise ValueError(f'{identity}: missing audited {field}')
            row['classification'] = 'planned'
            category = action['menu']
            section = action.get('suggested_group', [category])[1:]
            plan = row['plan']
            if not plan.startswith('M3-P-'):
                # Preserve references to earlier context work in the detailed plan;
                # use one M3 tracking identity for this menu's unimplemented entry.
                row['prior_plan'] = plan
                plan = 'M3-P-CONTEXT.' + safe_identity(identity)
                row['plan'] = plan
            short_reason = 'Not implemented; see the capability plan'
            gaps.append({'identity': safe_identity(identity), 'category': category,
                         'section': section, 'label': action['label'], 'plan': plan,
                         'reason': short_reason[:max(0, 128-len(plan)-2)]})
            for placement in action.get('placements', []):
                if placement['menu'] != category:
                    aliases.append({'identity': safe_identity(identity + '.' + placement['menu']),
                                    'category': placement['menu'],
                                    'section': placement['suggested_group'][1:],
                                    'label': action['label'], 'plan': plan,
                                    'reason': short_reason[:max(0, 128-len(plan)-2)]})
    rows.append(row)

if unresolved:
    raise ValueError('Unresolved in-scope Maya identities: ' + ', '.join(unresolved))
if len({gap['plan'] for gap in gaps}) != len(gaps):
    raise ValueError('Each missing capability requires a unique leaf plan')

counts = Counter(row['classification'] for row in rows)
document = {
    'schema_version': 1, 'date': '2026-09-14',
    'scope': 'M3 modeling menus; UV and independent animation/rigging/painting workflows deferred',
    'verification': 'Developer tests are recorded separately; every new manual scenario remains pending.',
    'counts': dict(counts), 'command_count': len(SPECS),
    'category_commands': dict(Counter(spec.category for spec in SPECS.values())),
    'native_commands': [{**asdict(spec), 'manual_status': '待人工测试',
                         'default_bindings': [event for command, event in binding_events(baseline_bindings())
                                              if command == spec.id and event is not None],
                         'parameter_entry': 'Edit > Adjust Last Operation / native tool or modifier properties'}
                        for spec in SPECS.values()],
    'cross_category_entries': aliases,
    'maya_actions': rows,
}
out = ROOT / 'docs/maya-mapping/2026-09-14-m3-modeling-coverage.json'
out.write_text(json.dumps(document, ensure_ascii=False, indent=2,
                          default=lambda value: sorted(value) if isinstance(value, (set, frozenset)) else str(value))
               + '\n', encoding='utf8')
runtime = ROOT / 'scripts/modules/axismeld/modeling_gaps.py'
runtime.write_text('# SPDX-FileCopyrightText: 2026 AxisMeld Authors\n'
                   '# SPDX-License-Identifier: GPL-2.0-or-later\n'
                   '"""Audited, non-executable Maya capability plans. Generated by build_modeling_coverage.py."""\n'
                   'GAPS = ' + pformat(tuple(gaps), width=110, sort_dicts=False) + '\n\n'
                   'ALIASES = ' + pformat(tuple(aliases), width=110, sort_dicts=False) + '\n', encoding='utf8')

def cell(value):
    return str(value).replace('|', '/').replace('\n', ' ')

lines = [
    '# M3 建模功能逐项对照与能力计划', '',
    '日期：2026-09-14。来源为本机 Maya 2026 官方菜单、运行时命令身份与默认键位文件，以及本机 Blender 源码。只整理功能身份和差异，没有复制 Autodesk 实现。', '',
    f'新增 {len(SPECS)} 个语义命令。Maya 去重动作分类：' + '；'.join(f'{key} {value}' for key, value in counts.items()) + '。', '',
    'M3 的交付边界是原生能力接入、默认键位核实、逐项映射和确实缺失能力的独立计划；不是 Maya 所有算法完全等价。完整绘制/动画/绑定及 UV 后置。', '',
    '所有本轮人工验证状态仍为待测，集中见 `../compatibility/2026-09-14-manual-test-ledger.md`。下表包含菜单路径、作用模式、原生调用、默认输入、参数与差异；完整机器记录见同名 JSON。', '',
    '## 已接入命令', '',
    '| ID / 菜单 | 标签 / 类型 | 模式 / 原生入口 | 默认输入 / 参数 | 差异 |',
    '|---|---|---|---|---|',
]
bindings = baseline_bindings()
for identifier, spec in SPECS.items():
    events = [event for command, event in binding_events(bindings) if command == identifier and event is not None]
    key = ' / '.join('+'.join([*(name for name in ('ctrl', 'shift', 'alt') if event.get(name)), event['type']])
                     for event in events) or '无AxisMeld专用绑定'
    if identifier == 'edit.repeat_native':
        key += '；G沿用原生Screen绑定'
    calls = '; '.join(','.join(call.modes) + ' / ' + call.operator +
                      (' INVOKE' if call.invoke else ' EXEC') for call in spec.calls)
    lines.append('| ' + ' | '.join(map(cell, (identifier + ' / ' + ' > '.join((spec.category, *spec.section)),
                    spec.label + ' / ' + spec.classification, calls, key + ' / Edit > Adjust Last Operation 或原生属性',
                    spec.difference))) + ' |')
lines.extend(['', '## Maya 身份覆盖', '', '| 菜单路径 | Maya 动作 | 默认输入 / 释放 | 分类 / 命令或计划 | 差异或边界 | 来源 |', '|---|---|---|---|---|---|'])
for row in rows:
    target = ', '.join(row.get('commands', [])) or row.get('plan', row.get('scope_reason', ''))
    inputs = '; '.join(item['input'] + ' / ' + item['release'] + ' (' + item['source'] + ')'
                       for item in row['maya_default_inputs']) or row['maya_input_status']
    lines.append('| ' + ' | '.join(map(cell, (' > '.join(row['suggested_group']), row['label'] + ' / ' + row['identity'], inputs,
                                             row['classification'] + ' / ' + target,
                                             row.get('reason', row.get('difference', row.get('scope_reason', ''))),
                                             '; '.join(row['source'])))) + ' |')
lines.extend(['', '## 尚未交付能力的逐项计划', '', '| 计划 / 动作 | 缺失边界 | 依赖 | 验收目标 |', '|---|---|---|---|'])
for row in rows:
    if row['classification'] == 'planned':
        lines.append('| ' + ' | '.join(map(cell, (row['plan'] + ' / ' + row['label'], row['reason'], row['dependency'], row['acceptance']))) + ' |')
out.with_suffix('.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
print(json.dumps({'commands': len(SPECS), 'classification': dict(counts), 'gaps': len(gaps)}, ensure_ascii=False))

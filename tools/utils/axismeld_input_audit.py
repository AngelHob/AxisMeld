# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generate/check the current default input inventory without loading user profiles."""
import argparse
from collections import Counter
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
# A running Blender may already have another installation's axismeld cached.
# Load this checkout in an isolated package, without unregistering or replacing it.
_API = '_axismeld_input_audit_api'
_package_path = ROOT / 'scripts/modules/axismeld/__init__.py'
if _API not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_API, _package_path,
                                                 submodule_search_locations=[str(_package_path.parent)])
    _package = importlib.util.module_from_spec(_spec)
    sys.modules[_API] = _package
    _spec.loader.exec_module(_package)
elif Path(sys.modules[_API].__file__).resolve() != _package_path:
    raise RuntimeError('An input audit from another checkout is already loaded')
from _axismeld_input_audit_api.commands import COMMANDS, RESERVED_KEYS, baseline_bindings, binding_events
from _axismeld_input_audit_api.keymap import (
    CONTEXT_TARGETS, addon_conflicts, generate_keymaps, modeling_keymap, validate_global_bindings,
)
from _axismeld_input_audit_api.modeling_registry import SPECS
from _axismeld_input_audit_api.object_modeling_hotbox import OBJECT_BOUND_COMMANDS

OUTPUT = ROOT / 'docs/compatibility/current-input-audit'
REFERENCE = 'docs/maya-mapping/2026-09-14-m3-modeling-coverage.json'
MODE_MAPS = {'OBJECT': 'Object Mode', 'EDIT_MESH': 'Mesh', 'EDIT_CURVE': 'Curve',
             'EDIT_SURFACE': 'Curve', 'EDIT_LATTICE': 'Lattice'}
AUDIT_MAPS = {'Object Mode', 'Mesh', 'Curve', 'Lattice', 'Object Non-modal',
              '3D View', '3D View Generic', 'AxisMeld Hotbox', 'Window', 'Screen', 'Frames'}
KEY_LABELS = {'SPACE': 'Space', 'LEFTMOUSE': 'LMB', 'MIDDLEMOUSE': 'MMB', 'RIGHTMOUSE': 'RMB',
              'DEL': 'Delete', 'PERIOD': '.', 'COMMA': ',', 'ONE': '1', 'TWO': '2', 'THREE': '3',
              'FOUR': '4', 'FIVE': '5', 'LEFT_ARROW': 'Left', 'RIGHT_ARROW': 'Right'}


def exec_file(path):
    """Only the file-loader bridge; keymap generation stays in upstream source."""
    spec = importlib.util.spec_from_file_location('_axismeld_keymap_data', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def file_loader():
    # Industry Compatible has one bpy dependency: execfile(blender_default.py).
    # Use the real API in Blender and restore every temporary module in Python.
    if 'bpy' in sys.modules:
        yield
        return
    previous = {name: sys.modules.get(name) for name in ('bpy', 'bpy.utils')}
    bpy, utils = ModuleType('bpy'), ModuleType('bpy.utils')
    utils.execfile = exec_file
    bpy.utils = utils
    sys.modules.update({'bpy': bpy, 'bpy.utils': utils})
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def load_base():
    with file_loader():
        industry = exec_file(ROOT / 'scripts/presets/keyconfig/keymap_data/industry_compatible_data.py')
        return industry.generate_keymaps(industry.Params(use_mouse_emulate_3_button=False))


def load_reference():
    return json.loads((ROOT / REFERENCE).read_text(encoding='utf-8'))


def command_id(item):
    operator, _event, properties = item
    return dict((properties or {}).get('properties', ())).get('command') if operator == 'axismeld.command' else None


def event_signature(event):
    return (event['type'], event.get('value', 'PRESS'),
            *(event.get(key, False) for key in ('ctrl', 'shift', 'alt', 'oskey')),
            event.get('key_modifier', 'NONE'), event.get('any', False))


def input_label(event):
    return '+'.join([label for key, label in (('ctrl', 'Ctrl'), ('alt', 'Alt'),
                                            ('shift', 'Shift'), ('oskey', 'OSKey')) if event.get(key)] +
                    [KEY_LABELS.get(event['type'], event['type'])])


def targets(command):
    if command == 'hotbox.open':
        return ['AxisMeld Hotbox']
    if command in SPECS:
        return sorted({MODE_MAPS[mode] for call in SPECS[command].calls
                       for mode in call.modes if mode in MODE_MAPS})
    if command in OBJECT_BOUND_COMMANDS:
        return ['Object Mode']
    if command in CONTEXT_TARGETS:
        return sorted(CONTEXT_TARGETS[command])
    return ['3D View'] if command.startswith('view.') else ['Mesh', 'Object Mode']


def references_for(command, reference):
    found = []
    for item in reference['maya_actions']:
        if command in item.get('commands', ()) and item.get('maya_default_inputs'):
            found.append({'document': REFERENCE, 'identity': item['identity'],
                          'inputs': [{'input': entry.get('input', ''),
                                      'release': entry.get('release', ''),
                                      'source': Path(entry.get('source', '').replace('\\', '/')).name}
                                     for entry in item['maya_default_inputs']]})
    if found:
        return found
    document = ('docs/maya-mapping/2026-09-11-tool-marking-menus.md'
                if command in {'tool.select', 'transform.move', 'transform.rotate', 'transform.scale'} else
                'docs/maya-mapping/hotbox-maya2026.md' if command == 'hotbox.open' else
                'docs/maya-mapping/2026-09-13-component-pointer-target.md' if command == 'context.component_hotbox' else
                'docs/maya-mapping/2026-09-14-empty-create-hotbox.md' if command in CONTEXT_TARGETS else
                'docs/maya-mapping/phase-1.md')
    return [{'document': document, 'identity': 'review_prose_and_current_source', 'inputs': []}]


def interaction(command):
    if command in {'tool.select', 'transform.move', 'transform.rotate', 'transform.scale'}:
        return 'QWER press selects tool; held key + repeated LMB opens marking menu; owned release/cancel: G-03/G-04/G-07.'
    if command == 'hotbox.open':
        return 'Tap toggles quad; hold opens main menu; center mouse dispatches Views; Space/owned release/cancel: G/MT groups.'
    if command in CONTEXT_TARGETS:
        return 'RMB context session; pointer target/selection/domain choose branch; commit or cancel on release: P/C/K/D/O groups.'
    if command in {'view.orbit', 'view.pan', 'view.dolly'}:
        return 'Alt + mouse press starts native navigation; drag/release handled by native modal operator.'
    return 'PRESS dispatches declared command; result/poll/Undo remain native or adapted; see M3 and input acceptance.'


def json_snapshot(value):
    """Copy keymap data to JSON types, keeping enum flags in deterministic order."""
    if isinstance(value, dict):
        return {key: json_snapshot(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted((json_snapshot(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, (tuple, list)):
        return [json_snapshot(item) for item in value]
    return value


def build_report(*, base=None, generated=None, reference=None):
    base = load_base() if base is None else base
    bindings = baseline_bindings()
    validate_global_bindings(base, bindings)
    generated = generate_keymaps(base, bindings) if generated is None else generated
    reference = load_reference() if reference is None else reference
    rows, errors, inherited, removed, observed, details, auxiliary = [], [], [], [], [], [], []
    expected_contexts = {name: args for name, args, _content in base}
    expected_contexts['AxisMeld Hotbox'] = {'space_type': 'VIEW_3D', 'region_type': 'WINDOW'}
    for name, args, content in generated:
        for index, item in enumerate(content['items']):
            identifier = command_id(item)
            record = {'map': name, 'context': args, 'index': index, 'operator': item[0],
                      'event': item[1], 'properties': item[2]}
            if identifier:
                observed.append((identifier, event_signature(item[1]), name))
                details.append((identifier, event_signature(item[1]), record))
                if args != expected_contexts.get(name):
                    errors.append(f'context mismatch: {identifier} / {name}')
                if item[2] != {'properties': [('command', identifier)]}:
                    errors.append(f'properties mismatch: {identifier} / {name}')
            elif item[0].startswith('axismeld.'):
                auxiliary.append(record | {'status': 'axismeld_owned_auxiliary'})
                if item[0] == 'axismeld.command':
                    errors.append(f'missing command property: {name}')
            elif name in AUDIT_MAPS or name.startswith('3D View Tool:'):
                inherited.append(record | {'status': 'native_inherited_not_maya_verified'})
    counts = Counter(observed)
    expected = set()
    for command, event in binding_events(bindings):
        actual = sorted(name for owner, sig, name in observed
                        if owner == command and sig == event_signature(event))
        expected_maps = targets(command)
        for name in expected_maps:
            key = (command, event_signature(event), name)
            expected.add(key)
            if counts[key] == 0:
                errors.append(f'missing: {command} / {input_label(event)} / {name}')
            elif counts[key] > 1:
                errors.append(f'duplicate: {command} / {input_label(event)} / {name}')
        refs = references_for(command, reference)
        reference_inputs = {entry['input'] for ref in refs for entry in ref['inputs']}
        comparison = ('same_notation' if input_label(event) in reference_inputs else
                      'review_notation_or_difference' if reference_inputs else 'prose_reference_review')
        rows.append({'command': command, 'label': COMMANDS[command].label, 'input': input_label(event),
                     'event': event, 'alias': event != bindings[command], 'expected_maps': expected_maps,
                     'placements': actual, 'placement_details': [record for owner, sig, record in details
                                                                 if owner == command and sig == event_signature(event)],
                     'references': refs, 'reference_comparison': comparison,
                     'interaction': interaction(command), 'difference': COMMANDS[command].difference,
                     'manual_ledger': 'docs/compatibility/2026-09-14-manual-test-ledger.md'})
    for identifier, sig, name in sorted(counts):
        if (identifier, sig, name) not in expected:
            errors.append(f'unexpected: {identifier} / {sig} / {name}')
    generated_maps = {(name, tuple(sorted(args.items()))): content for name, args, content in generated}
    protected = 0
    for name, args, content in base:
        current = generated_maps.get((name, tuple(sorted(args.items()))))
        allowed = (modeling_keymap(name, args) or
                   (name in {'Curve', 'Lattice', 'Generic Gizmo Maybe Drag'} and not args.get('modal')))
        if not allowed:
            protected += 1
            if current != content:
                errors.append(f'protected map changed: {name}')
        if current is not None and (name in AUDIT_MAPS or name.startswith('3D View Tool:')):
            for item in content['items']:
                if item not in current['items']:
                    removed.append({'map': name, 'context': args, 'operator': item[0], 'event': item[1],
                                    'properties': item[2],
                                    'status': 'removed_by_current_preset_review_if_needed'})
    return json_snapshot({'schema_version': 1,
            'scope': 'Current public AxisMeld preset; no personal overrides or live addon enumeration',
            'verification': {'configuration': 'generated_source_only', 'gui': 'not_run_by_generator',
                             'manual': 'not_reassessed', 'reference': 'stored_reference_not_new_maya_runtime_audit'},
            'counts': {'commands_with_default': len(bindings), 'bindings_including_aliases': len(rows),
                       'base_maps': len(base), 'generated_maps': len(generated),
                       'protected_maps_checked': protected, 'inherited_items': len(inherited),
                       'removed_items': len(removed), 'owned_auxiliary_items': len(auxiliary)},
            'bindings': rows,
            'reserved': [{'key': key, 'status': 'reserved_not_implemented'} for key in RESERVED_KEYS],
            'inherited': inherited, 'owned_auxiliary': auxiliary, 'removed': removed, 'errors': errors,
            'review_notes': [
                'Same-map RMB native fallback and Shift+RMB create/model dispatch are intentional; verify runtime predicates.',
                'Shared Frames Space and mode/3D View overlaps need handler order and poll; equality is not proof of a bug.',
                'Alt+LMB DOUBLE_CLICK edgering_select is removed by current PRESS ownership; requires modal event verification.',
                'Measure X ruler_remove is removed by reserved-X ownership; DEL remains. Classify before changing.',
                'Reference same_notation compares only stored input text, not operation equivalence or release behavior.',
            ]})


def render_markdown(report):
    lines = ['# 当前默认键位与交互对照（自动生成）', '',
             '由 `tools/utils/axismeld_input_audit.py` 从当前源码生成；运行 `--check` 检查漂移。', '',
             '这是静态生成配置与已存 Maya 参考的对照，不是完整 Maya 等价性或 GUI 验收。人工状态：**not_reassessed**；既有人工记录不变。', '',
             'JSON 同名文件保留事件值、实际 keymap/区域/顺序/操作属性、来源、差异以及原生继承/移除项完整清单。个人配置不读取。', '',
             f"默认命令 {report['counts']['commands_with_default']}；含别名输入 {report['counts']['bindings_including_aliases']}；"
             f"生成 keymap {report['counts']['generated_maps']}；检查未改动的受保护 keymap {report['counts']['protected_maps_checked']}。", '',
             '| 输入 | 命令 | 生成到的 keymap | 已存参考身份/输入 | 参考比较 |',
             '|---|---|---|---|---|']
    def cell(text):
        return str(text).replace('|', '\\|').replace('\n', ' ')
    for row in report['bindings']:
        refs = '; '.join(ref['identity'] + ': ' + ', '.join(e['input'] for e in ref['inputs'])
                         if ref['inputs'] else ref['document'] for ref in row['references'])
        lines.append('| ' + ' | '.join(map(cell, (row['input'] + ('（别名）' if row['alias'] else ''),
                     row['command'], ', '.join(row['placements']), refs, row['reference_comparison']))) + ' |')
    lines += ['', '`same_notation` 仅表示与已存输入文本相同；`review_notation_or_difference` 需要核对写法或差异；'
              '`prose_reference_review` 需要读取所指文档。均不等于功能通过。', '',
              '## 直接注入的操纵器输入', '',
              '这些输入由 AxisMeld 注入，不属于原生继承：', '',
              '| 输入 | 操作 | keymap |', '|---|---|---|']
    lines += ['| ' + ' | '.join(map(cell, (input_label(row['event']) + ' / ' + row['event']['value'],
                                         row['operator'], row['map']))) + ' |'
              for row in report['owned_auxiliary']]
    lines += ['', '## 按住、松开与人工入口', '']
    lines += ['- ' + text for text in dict.fromkeys(r['interaction'] for r in report['bindings'])]
    lines += ['', '[统一人工清单](2026-09-14-manual-test-ledger.md) · '
              '[当前 UI/输入阶段](../development/2026-09-29-ui-interaction-shortcuts.md)', '',
              '## 预留、继承与待核实', '',
              '预留裸键：' + '、'.join(row['key'] for row in report['reserved']) + '。缺失能力暂缓，不解除灰显。', '',
              '原生继承项标为 `native_inherited_not_maya_verified`；移除项保留原事件值，便于发现 PRESS/双击等差异。', '']
    lines += ['- ' + text for text in report['review_notes']]
    lines += ['', '## 生成一致性错误', ''] + (report['errors'] or ['无。仅表示当前绑定位置及受保护 keymap 检查通过。'])
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    report = build_report()
    outputs = {OUTPUT.with_suffix('.json'): json.dumps(report, ensure_ascii=False, indent=2) + '\n',
               OUTPUT.with_suffix('.md'): render_markdown(report)}
    if report['errors']:
        raise SystemExit('\n'.join(report['errors']))
    for path, text in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != text:
                raise SystemExit(f'Input audit is outdated: {path.relative_to(ROOT)}')
        else:
            path.write_text(text, encoding='utf-8')
    print(json.dumps({'checked': args.check, **report['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    # Blender passes its own flags before --; ordinary Python passes only ours.
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)

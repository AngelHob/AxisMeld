#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generate the audited Maya-to-Blender menu route inventory and local browser.

Run from any directory with Python; Blender and network access are unnecessary.
Use --check in validation and --html PATH to export the self-contained viewer.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON = ROOT / 'docs/compatibility/maya2026-workspace-menu-routes.json'
sys.path.insert(0, str(ROOT / 'scripts/modules'))

from axismeld.menubar_catalog import build_menubar
from axismeld.menubar_reference import REFERENCE_MENUS
from axismeld.workspace_menu_catalog import MODELING_SOURCE_ROOTS, build_workspace_menubar, routes
from axismeld.workspace_native_groups import GROUPS


SET_LABELS = {'MODELING': 'Modeling', 'RIGGING': 'Rigging', 'ANIMATION': 'Animation',
              'FX': 'FX', 'RENDERING': 'Rendering'}
GLOBAL_HOSTS = {'common.file': 'File', 'common.edit': 'Edit',
                'common.windows': 'Window', 'menubar.help': 'Help'}
VIEWPORT_HOSTS = {'common.display': 'View', 'common.select': 'Select',
                  'common.create': 'Add', 'common.modify': 'Object'}
SOURCE_FILES = (
    'scripts/modules/axismeld/menubar_reference.py',
    'scripts/modules/axismeld/menubar_catalog.py',
    'scripts/modules/axismeld/workspace_menu_catalog.py',
    'scripts/modules/axismeld/workspace_native_catalog.py',
    'scripts/modules/axismeld/workspace_native_groups.py',
    'scripts/startup/bl_ui/space_axismeld_native_modeling.py',
    'scripts/startup/bl_ui/space_axismeld_menubar.py',
    'scripts/startup/bl_ui/space_topbar.py',
    'scripts/startup/bl_ui/space_view3d.py',
)


def walk(nodes):
    for node in nodes:
        yield node, False
        yield from walk(node.get('children', ()))
        if node.get('options'):
            yield node['options'], True


def native_inventory(catalog):
    """Audit each original draw declaration in each required mode placement.

Curve providers reused in Surface modes share source IDs, so a declaration ID
alone is not the placement key. Composite menu/enum providers remain intact.
    """
    roots = {root['id']: root for root in catalog['menus']}
    expected = {(key, item['id']): (group, item)
                for key, group in GROUPS.items() for item in group['items']}
    included = [(node['group_key'], item_id) for node, _ in walk(catalog['menus'])
                if node['kind'] == 'native_group' for item_id in node['include']]
    aliases = {(row['group_key'], row['native_item']): row['command']
               for row in catalog['native_equivalences']}
    native_aliases = {(row['group_key'], row['native_item']):
                      (row['target_group_key'], row['target_native_item'])
                      for row in catalog['native_item_equivalences']}
    if (len(included) != len(set(included)) or set(included) & set(aliases) or
            (set(included) | set(aliases)) & set(native_aliases)):
        raise ValueError('Native draw references are duplicated or both drawn and aliased')
    if set(included) | set(aliases) | set(native_aliases) != set(expected):
        raise ValueError('Native draw declarations are missing from the current integration')
    if not set(native_aliases.values()) <= set(included):
        raise ValueError('Native-to-native aliases must target a surviving draw reference')
    added = {('object.modifiers', 'object.modifiers.provider')}
    if not added <= set(expected) or len(set(expected) - added) != 161:
        raise ValueError('The original 161 native placement declarations changed; review coverage')
    if len({item_id for _, item_id in set(expected) - added}) != 134:
        raise ValueError('The original 134 unique native declarations changed; review coverage')
    active_roots = [root for root in catalog['menus'] if root['id'] in catalog['modeling_roots']]
    active_routes = routes(catalog, catalog['modeling_roots'])
    command_targets = {}
    for node, _ in walk(active_roots):
        if node.get('command'):
            command_targets.setdefault(node['command'], []).append(node['id'])
    entries = []
    for (group_key, item_id), (group, item) in expected.items():
        root = roots[group['root_id']]
        command = aliases.get((group_key, item_id), '')
        native_target = native_aliases.get((group_key, item_id))
        targets = command_targets.get(command, ()) if command else ()
        if command and not targets:
            raise ValueError('Native alias target is not reachable: ' + command)
        actual_paths = [('Modeling', '3D View') + active_routes[target] for target in targets]
        container = ('Modeling', '3D View', root['label']) + tuple(group['path'])
        if native_target:
            target_group = GROUPS[native_target[0]]
            actual_paths = [('Modeling', '3D View', roots[target_group['root_id']]['label']) +
                            tuple(target_group['path'])]
        entries.append({
            'id': group_key + '::' + item_id,
            'group_key': group_key, 'source_item_id': item_id,
            'source_menu': group['source_menu'], 'source_group': group['source_group'],
            'entry_locator': item['keywords'].get('text') or item['operator'] or item['provider'] or item['api'],
            'caption_is_dynamic': 'text' not in item['keywords'],
            'api': item['api'], 'operator': item['operator'], 'provider': item['provider'],
            'properties': item['properties'], 'invoke_context': item['invoke_context'],
            'conditions': item['conditions'], 'modes': group['modes'],
            'enum_property': item['enum_property'], 'keywords': item['keywords'],
            'source_statement': item['source'],
            'resolution': 'existing_command_alias' if command else 'native_item_alias' if native_target else 'native_draw',
            'destination_container': container,
            'equivalent_command': command, 'equivalent_target_ids': targets,
            'equivalent_native_group': native_target[0] if native_target else '',
            'equivalent_native_item': native_target[1] if native_target else '',
            'actual_routes': actual_paths or [container],
            'added_entry': (group_key, item_id) in added,
        })
    return {
        'counts': {'placement_groups': len(GROUPS), 'placement_references': len(expected),
                   'unique_source_items': len({item_id for _, item_id in expected}),
                   'original_placement_references': 161, 'original_unique_source_items': 134,
                   'added_provider_entries': len(added), 'native_draw_references': len(included),
                   'existing_command_aliases': len(aliases), 'native_item_aliases': len(native_aliases)},
        'coverage': {'missing_references': [], 'duplicate_references': [],
                     'all_original_draw_statements_preserved_or_precisely_aliased': True},
        'note': '原生融合单独核对绘制声明和模式放置引用；Curve声明复用于Surface模式。菜单、参数枚举和节点资产入口保留原提供器，不将内部功能摊平。已有按钮别名仅在完整参数及调用方式一致时合并。这些数字不是展开后的全部Blender功能总数。',
        'entries': entries,
    }


def build_inventory():
    catalog = build_workspace_menubar()
    roots = {node['id']: node for node in catalog['menus']}
    actual_nodes = {node['id']: node for node, _ in walk(catalog['menus'])}
    source_nodes = {node['id']: node for node, _ in walk(build_menubar()['menus'])}
    node_routes, route_roots = {}, {}
    for identifier in roots:
        for item_id, path in routes(catalog, (identifier,)).items():
            if item_id in node_routes:
                raise ValueError('Duplicate projected function ID: ' + item_id)
            node_routes[item_id], route_roots[item_id] = path, identifier

    exposed_roots = set().union(*catalog['sets'].values())
    if set(roots) - exposed_roots != set(catalog['archived_roots']):
        raise ValueError('Unexposed roots differ from the explicit archive inventory')
    fallback_paths = {}
    for menu_set, identifiers in catalog['sets'].items():
        for identifier in identifiers:
            for item_id, path in routes(catalog, (identifier,)).items():
                fallback_paths.setdefault(item_id, []).append(
                    ('Window', 'Maya Menu Sets', SET_LABELS[menu_set]) + path)

    entries, seen = [], set()
    for source_root in REFERENCE_MENUS:
        if source_root['id'] not in MODELING_SOURCE_ROOTS:
            continue
        for reference, is_option in walk((source_root,)):
            if reference.get('kind') != 'item':
                continue
            identifier = reference['id']
            if identifier in seen:
                raise ValueError('Duplicate Maya reference ID: ' + identifier)
            seen.add(identifier)
            if identifier not in node_routes or identifier not in fallback_paths:
                raise ValueError('Maya function has no actual navigation route: ' + identifier)
            actual = actual_nodes[identifier]
            if actual != source_nodes[identifier]:
                raise ValueError('Projection changed a function payload: ' + identifier)
            if is_option and actual['kind'] != 'disabled':
                raise ValueError('Options rendering needs a reviewed availability update: ' + identifier)
            projected_root = route_roots[identifier]
            local_path = node_routes[identifier]
            aliases = []
            if projected_root in catalog['modeling_roots']:
                primary = ('Modeling', '3D View') + local_path
                condition = 'AxisMeld Maya 键位；Modeling 工作区的 3D 视窗。无需选中对象即可找到菜单。'
            elif projected_root in GLOBAL_HOSTS:
                primary = (GLOBAL_HOSTS[projected_root], 'Maya ' + local_path[0]) + local_path[1:]
                condition = 'AxisMeld Maya 键位；Blender 全局菜单，任意工作区。'
            elif projected_root in VIEWPORT_HOSTS:
                primary = ('Modeling', '3D View', VIEWPORT_HOSTS[projected_root],
                           'Maya ' + local_path[0]) + local_path[1:]
                condition = 'AxisMeld Maya 键位；Modeling 工作区的 3D 视窗，Object 模式。'
                if projected_root == 'common.modify':
                    aliases.append(('Modeling', '3D View', 'Edit Mesh', 'Maya Modify') + local_path[1:])
            else:
                primary = fallback_paths[identifier][0]
                condition = 'AxisMeld Maya 键位；Window 全局导航，任意工作区。'
            kind = actual['kind']
            if kind not in {'command', 'action', 'native', 'disabled'}:
                raise ValueError('Maya row has no supported button/placeholder kind: ' + identifier)
            entries.append({
                'id': identifier,
                'entry_type': 'options' if is_option else 'body',
                'label': reference['label'],
                'maya_root_id': source_root['id'],
                'maya_root_label': source_root['label'],
                'maya_path': reference['path'],
                'maya_command': reference.get('maya_command', ''),
                'projected_root_id': projected_root,
                'primary_route': primary,
                'primary_condition': condition,
                'additional_routes': aliases,
                'additional_route_condition': 'Edit Mesh 模式。' if aliases else '',
                'fallback_routes': fallback_paths[identifier],
                'fallback_condition': 'AxisMeld Maya 键位；任意工作区的 Window → Maya Menu Sets。',
                'presentation': 'gray_placeholder' if kind == 'disabled' else 'button',
                'availability': 'not_adapted' if kind == 'disabled' else 'runtime_context',
                'binding_kind': kind,
                'binding_key': actual.get('native_key') or actual.get('command') or actual.get('action_key') or '',
                'reason': actual.get('reason', ''),
            })

    entry_counts = Counter(row['entry_type'] for row in entries)
    if (entry_counts['body'], entry_counts['options']) != (231, 161):
        raise ValueError('The retained Maya modeling scope changed; review the new counts before regenerating')
    all_maya_ids = {node['id'] for node, _ in walk(REFERENCE_MENUS) if node.get('kind') == 'item'}
    modeling_entry_ids = set(routes(catalog, catalog['modeling_roots'])) & all_maya_ids
    if modeling_entry_ids != seen:
        raise ValueError('Actual Modeling entrypoints differ from the independently scoped Maya function IDs')
    presentation_counts = Counter(row['presentation'] for row in entries)
    model_rows = [row for row in entries if row['projected_root_id'] in catalog['modeling_roots']]
    model_counts = Counter(row['entry_type'] for row in model_rows)
    edit_rows = [row for row in entries if row['maya_root_id'] == 'modeling.edit_mesh']
    edit_counts = Counter(row['entry_type'] for row in edit_rows)
    excluded = []
    for root in REFERENCE_MENUS:
        if root['id'] in catalog['excluded_modeling_roots']:
            original_rows = [(node, is_option) for node, is_option in walk((root,)) if node.get('kind') == 'item']
            excluded.append({'root_id': root['id'], 'label': root['label'],
                             'body': sum(not is_option for _, is_option in original_rows),
                             'options': sum(is_option for _, is_option in original_rows),
                             'removed_from_modeling': True, 'reference_preserved': True})
    excluded_body = sum(row['body'] for row in excluded)
    excluded_options = sum(row['options'] for row in excluded)
    if (excluded_body, excluded_options) != (214, 76):
        raise ValueError('The excluded Deform/Generate scope changed; review the reference')
    return {
        'schema_version': 3,
        'title': 'AxisMeld · Maya 建模菜单去向',
        'source_baseline': 'Local audited Maya 2026 menubar reference',
        'scope': '仅列本轮七个保留建模源菜单的231个正文和161个独立Options。Deform、Generate共214个正文和76个Options移出Modeling；原始Maya参考留档。其他模块不在本轮开发范围。表格不含分隔线、目录本身和额外Blender专属功能。',
        'availability_note': '按钮表示已绑定现有操作；是否可用取决于当前模式、选区、编辑器及操作条件。灰色占位不执行动作。Options 独立保留，当前均未适配。',
        'route_note': '主入口按本轮实际 UI 宿主生成。窗口导航路径始终保留；仍需启用 AxisMeld Maya 键位。当前模式可能使正文按钮灰显。路径末尾的 Options 是正文右侧的独立齿轮按钮，不是下一级子菜单。',
        'counts': {
            'total': len(entries), 'body': entry_counts['body'], 'options': entry_counts['options'],
            'button': presentation_counts['button'], 'gray_placeholder': presentation_counts['gray_placeholder'],
            'modeling_body': model_counts['body'], 'modeling_options': model_counts['options'],
            'edit_mesh_body': edit_counts['body'], 'edit_mesh_options': edit_counts['options'],
            'source_roots': len(MODELING_SOURCE_ROOTS), 'reference_source_roots': len(REFERENCE_MENUS),
            'projected_roots': len(roots), 'excluded_modeling_body': excluded_body,
            'excluded_modeling_options': excluded_options,
            'modeling_projected_roots': len(catalog['modeling_roots']),
        },
        'excluded_from_modeling': excluded,
        'native_integration': native_inventory(catalog),
        'coverage': {'missing_ids': [], 'duplicate_ids': [], 'changed_payload_ids': [],
                     'every_entry_has_fallback': True,
                     'scope': 'Seven retained Maya modeling source roots; other modules are outside this development scope.',
                     'method': 'Independent retained-modeling reference IDs compared against projected payloads and current Modeling menu-set entrypoints.'},
        'source_files': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE_FILES},
        'entries': entries,
    }


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AxisMeld · Maya 建模菜单去向</title><style>
:root{color-scheme:dark;--bg:#15191e;--panel:#20262d;--line:#38414d;--text:#edf2f7;--muted:#b0bdca;--blue:#8ac8ff;--gray:#aeb8c4;--orange:#ffbb78}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 system-ui,"Microsoft YaHei",sans-serif}
main{max-width:1580px;margin:auto;padding:36px 28px}header{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}
h1{font-size:29px;line-height:1.25;margin:0 0 12px}p{margin:6px 0;color:var(--muted)}.eyebrow{color:var(--blue);font-size:12px;letter-spacing:.14em;margin-bottom:10px}.small{font-size:12px}
.counts{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:25px 0 18px}.stat{padding:16px 18px;background:var(--panel);border:1px solid var(--line);border-radius:9px}.stat strong{display:block;font-size:28px;line-height:1.2}.stat span{color:var(--muted);font-size:12px}
.notice{padding:13px 16px;border-left:3px solid var(--orange);background:#28282a;margin:18px 0;color:#d8dde4}.controls{display:grid;grid-template-columns:2fr 1.15fr 1fr 1fr;gap:10px;margin:22px 0 12px}label{display:grid;gap:5px;color:var(--muted);font-size:12px}input,select,button{font:inherit;color:var(--text);background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:10px 12px;min-width:0}input:focus,select:focus,button:focus{outline:2px solid var(--blue);outline-offset:2px}button{cursor:pointer}button:hover{border-color:var(--blue)}button:disabled{opacity:.4;cursor:default}
.toolbar{display:flex;justify-content:space-between;align-items:center;margin:14px 0;gap:15px;min-height:40px}.pager{display:flex;align-items:center;gap:10px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:9px}table{width:100%;border-collapse:collapse;table-layout:fixed;min-width:900px}th{text-align:left;background:#28313a;padding:13px 15px;font-weight:600;position:sticky;top:0}td{padding:16px 15px;border-top:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}tr:nth-child(even){background:#1a2026}th:nth-child(1){width:28%}th:nth-child(2){width:47%}th:nth-child(3){width:25%}.label{font-weight:600;margin:0 0 6px;font-size:15px}.path{color:#e0eaf5;margin:0 0 7px}.source{color:var(--muted)}.id{font:11px/1.5 ui-monospace,Consolas,monospace;color:#8d9cab;margin-top:10px}.tag{display:inline-block;border:1px solid #496374;border-radius:4px;padding:2px 6px;font-size:11px;font-weight:400;vertical-align:2px;margin-left:6px}.status{display:inline-block;border-radius:5px;padding:4px 8px;background:#203649;color:#a7d8ff;font-weight:600}.status.gray{background:#313842;color:#c7d0db}.muted{color:var(--muted)}.secondary{margin-top:12px;border-top:1px dashed #394550;padding-top:9px}.secondary strong{display:block;color:#acbbc9;font-size:11px;margin-bottom:3px}.secondary p{margin:0 0 6px;font-size:12px}.reason{font-size:12px;margin-top:9px}.empty{padding:60px;text-align:center;color:var(--muted)}footer{margin:24px 0 5px;font-size:12px;color:var(--muted)}
@media(max-width:760px){main{padding:22px 15px}header{display:block}.counts{grid-template-columns:repeat(2,1fr)}.controls{grid-template-columns:1fr 1fr}.controls label:first-child{grid-column:1/-1}.toolbar{align-items:flex-start;flex-direction:column}h1{font-size:25px}.stat strong{font-size:24px}}
</style></head><body><main>
<header><div><div class="eyebrow">AXISMELD / MODELING MENU DIRECTORY</div><h1>建模菜单，去哪里找？</h1><p>搜索功能名、Maya 原路径或源 ID，查看 Blender 中的实际入口。</p><p class="small">本地文件 · 无需联网 · 仅本轮建模范围；Deform、Generate 已移出 Modeling，变形使用 Modifier。</p></div><button id="download" type="button">下载本轮 JSON</button></header>
<section class="counts" aria-label="覆盖统计"><div class="stat"><strong id="count-all"></strong><span>本轮逐项记录 · 无缺失、无重复</span></div><div class="stat"><strong id="count-body"></strong><span>保留的 Maya 建模正文功能</span></div><div class="stat"><strong id="count-options"></strong><span>独立 Options 占位</span></div><div class="stat"><strong id="count-buttons"></strong><span>已有操作绑定 · 仍需运行时上下文</span></div></section>
<div class="notice" id="availability"></div>
<section class="controls" aria-label="筛选菜单"><label>搜索<input id="search" type="search" placeholder="例如 Chamfer Vertices、Edit Mesh、Curve Projection" autocomplete="off"></label><label>Maya 原菜单<select id="root"><option value="">全部建模源菜单</option></select></label><label>入口类型<select id="kind"><option value="">正文 + Options</option><option value="body">仅正文功能</option><option value="options">仅 Options</option></select></label><label>按钮状态<select id="status"><option value="">全部状态</option><option value="button">已有操作绑定</option><option value="gray_placeholder">灰色占位</option></select></label></section>
<div class="toolbar"><div id="result" role="status" aria-live="polite"></div><div class="pager"><button id="prev" type="button">上一页</button><span id="page" class="small"></span><button id="next" type="button">下一页</button></div></div>
<div class="table-wrap"><table><thead><tr><th>Maya 功能 / 原路径</th><th>Blender 实际入口</th><th>状态 / 适配说明</th></tr></thead><tbody id="rows"></tbody></table></div>
<footer><p>主入口对应本轮的实际菜单位置；Window → Maya Menu Sets 提供所有工作区可找到的备用入口。启用 AxisMeld Maya 键位后可见。</p><p>原 Edit Mesh 的 Curve 组已放入 Mesh Tools → Curve Projection。Options 是正文右侧的独立齿轮按钮，不是下一级子菜单。</p><p>Deform、Generate 共214个正文和76个Options已移出本轮Modeling范围；原始参考仍留档。其他模块未在本轮开发；目录覆盖核验不等于所有操作的人工验收。</p><p id="coverage"></p></footer>
<section aria-labelledby="native-heading" style="margin-top:36px"><h2 id="native-heading">Blender 原生融合核验</h2><p id="native-counts"></p><p class="small" id="native-note"></p><div class="controls"><label>搜索原生来源或入口<input id="native-search" type="search" placeholder="例如 modifiers、mesh.mark_seam、Vertex" autocomplete="off"></label><label>处理方式<select id="native-resolution"><option value="">全部处理方式</option><option value="native_draw">原生绘制</option><option value="existing_command_alias">合并到已有按钮</option><option value="native_item_alias">合并到另一原生入口</option></select></label></div><p id="native-result" role="status" aria-live="polite"></p><div class="table-wrap"><table><thead><tr><th>原生来源声明</th><th>实际目录 / 合并后入口</th><th>参数与上下文</th></tr></thead><tbody id="native-rows"></tbody></table></div></section>
</main><script id="inventory" type="application/json">__DATA__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('inventory').textContent),$=id=>document.getElementById(id),size=75;
const norm=s=>String(s).normalize('NFKC').toLocaleLowerCase();
const sourceRoots=new Map(data.entries.map(r=>[r.maya_root_id,r.maya_root_label]));
for(const [value,text]of sourceRoots){const o=document.createElement('option');o.value=value;o.textContent=text;$('root').append(o)}
$('count-all').textContent=data.counts.total.toLocaleString();$('count-body').textContent=data.counts.body.toLocaleString();$('count-options').textContent=data.counts.options.toLocaleString();$('count-buttons').textContent=data.counts.button.toLocaleString();$('availability').textContent=data.availability_note;
$('coverage').textContent=`本轮覆盖：Modeling ${data.counts.modeling_body} 个正文 + ${data.counts.modeling_options} 个 Options；其中原 Edit Mesh ${data.counts.edit_mesh_body} + ${data.counts.edit_mesh_options}。本轮源 ID 缺失 ${data.coverage.missing_ids.length}，重复 ${data.coverage.duplicate_ids.length}，绑定 payload 变化 ${data.coverage.changed_payload_ids.length}。`;
const indexed=data.entries.map(row=>({row,search:norm([row.id,row.maya_path.join(' '),row.primary_route.join(' '),row.fallback_routes.flat().join(' '),row.additional_routes.flat().join(' '),row.maya_command,row.binding_key,row.reason].join(' '))}));
let page=0,filtered=indexed;
function el(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n}
function path(value){return value.join(' → ')}
function draw(){const total=filtered.length,pages=Math.max(1,Math.ceil(total/size));page=Math.min(page,pages-1);const start=page*size,fragment=document.createDocumentFragment();
 for(const {row:r}of filtered.slice(start,start+size)){const tr=el('tr'),a=el('td'),b=el('td'),c=el('td');
  const label=el('div',r.entry_type==='options'?r.maya_path.at(-2)+' · Options':r.label,'label');if(r.entry_type==='options')label.append(el('span','Options','tag'));a.append(label,el('div',path(r.maya_path),'path source'),el('div',r.id,'id'));
  b.append(el('div',path(r.primary_route),'path'),el('div',r.primary_condition,'small muted'));const other=el('div',undefined,'secondary');other.append(el('strong','任意工作区备用入口'));for(const route of r.fallback_routes)other.append(el('p',path(route)));for(const route of r.additional_routes){other.append(el('strong','Edit Mesh 模式附加入口'),el('p',path(route)))}b.append(other);
  c.append(el('span',r.presentation==='button'?'已有操作绑定':'灰色占位','status'+(r.presentation==='button'?'':' gray')),el('p',r.presentation==='button'?'模式、选区与上下文决定是否可用。':'未适配；菜单中保留位置，点击不会执行动作。','small muted'));if(r.reason)c.append(el('div',r.reason,'reason muted'));if(r.binding_key)c.append(el('div',r.binding_key,'id'));tr.append(a,b,c);fragment.append(tr)}
 if(!total){const tr=el('tr'),td=el('td','没有匹配项；可以缩短关键词或清除筛选。','empty');td.colSpan=3;tr.append(td);fragment.append(tr)}
 $('rows').replaceChildren(fragment);$('result').textContent=total?`共 ${total.toLocaleString()} 项 · 当前 ${start+1}–${Math.min(start+size,total)} 项`:'共 0 项';$('page').textContent=`${page+1} / ${pages}`;$('prev').disabled=page===0;$('next').disabled=page>=pages-1;
}
function filter(){const terms=norm($('search').value).trim().split(/\s+/).filter(Boolean),root=$('root').value,kind=$('kind').value,status=$('status').value;filtered=indexed.filter(({row:r,search})=>(!root||r.maya_root_id===root)&&(!kind||r.entry_type===kind)&&(!status||r.presentation===status)&&terms.every(t=>search.includes(t)));page=0;draw()}
for(const id of ['search','root','kind','status'])$(id).addEventListener(id==='search'?'input':'change',filter);
$('prev').addEventListener('click',()=>{page--;draw()});$('next').addEventListener('click',()=>{page++;draw()});
$('download').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='maya2026-workspace-menu-routes.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});draw();
const native=data.native_integration,nc=native.counts;
$('native-counts').textContent=`${nc.unique_source_items} 个源声明 · ${nc.placement_references} 个模式放置引用；${nc.native_draw_references} 个保留原生绘制，${nc.existing_command_aliases} 个合并到已有按钮，${nc.native_item_aliases} 个合并到另一原生入口。新增完整 Modifier 菜单入口 ${nc.added_provider_entries} 个。`;
$('native-note').textContent=native.note;
const nativeIndex=native.entries.map(row=>({row,search:norm([row.id,row.entry_locator,row.source_menu,row.operator,row.provider,row.destination_container.join(' '),row.actual_routes.flat().join(' '),row.equivalent_command].join(' '))}));
function drawNative(){const terms=norm($('native-search').value).trim().split(/\s+/).filter(Boolean),resolution=$('native-resolution').value,items=nativeIndex.filter(({row,search})=>(!resolution||row.resolution===resolution)&&terms.every(t=>search.includes(t))),fragment=document.createDocumentFragment();
 for(const{row:r}of items){const tr=el('tr'),a=el('td'),b=el('td'),c=el('td');a.append(el('div',r.entry_locator,'label'),el('div',r.source_menu+' / '+r.source_group,'small muted'),el('div',r.id,'id'));if(r.caption_is_dynamic)a.append(el('p','此处以来源标识定位；菜单标题由 Blender 提供。','small muted'));if(r.added_entry)a.append(el('span','本轮新增入口','tag'));
  const label={native_draw:'原生绘制',existing_command_alias:'合并到已有按钮',native_item_alias:'合并到另一原生入口'}[r.resolution]||r.resolution;b.append(el('span',label,'status'));for(const route of r.actual_routes)b.append(el('div',path(route),'path'));if(r.resolution!=='native_draw')b.append(el('div',r.equivalent_command||r.equivalent_native_item||'','id'));
  c.append(el('div',r.modes.join(' / '),'small'),el('div',r.api+' · '+r.invoke_context,'id'));if(Object.keys(r.properties).length)c.append(el('div',JSON.stringify(r.properties),'id'));if(r.enum_property)c.append(el('div','保留参数枚举：'+r.enum_property,'small muted'));if(r.conditions.length)c.append(el('div','原条件：'+r.conditions.join('；'),'small muted'));tr.append(a,b,c);fragment.append(tr)}
 if(!items.length){const tr=el('tr'),td=el('td','没有匹配的原生来源。','empty');td.colSpan=3;tr.append(td);fragment.append(tr)}$('native-rows').replaceChildren(fragment);$('native-result').textContent=`共 ${items.length} 个放置引用 · 缺失 ${native.coverage.missing_references.length}，重复 ${native.coverage.duplicate_references.length}`;
}
$('native-search').addEventListener('input',drawNative);$('native-resolution').addEventListener('change',drawNative);drawNative();
</script></body></html>
'''


def render_html(inventory):
    payload = json.dumps(inventory, ensure_ascii=False, separators=(',', ':'))
    payload = payload.replace('&', r'\u0026').replace('<', r'\u003c').replace('>', r'\u003e')
    return HTML_TEMPLATE.replace('__DATA__', payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path, default=DEFAULT_JSON)
    parser.add_argument('--html', type=Path, help='Optional self-contained HTML output path')
    parser.add_argument('--check', action='store_true', help='Verify existing outputs instead of writing')
    args = parser.parse_args()
    inventory = build_inventory()
    outputs = [(args.json, json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')]
    if args.html:
        outputs.append((args.html, render_html(inventory)))
    for destination, content in outputs:
        if args.check:
            if not destination.is_file() or destination.read_text(encoding='utf-8') != content:
                raise SystemExit('Outdated menu route artifact: ' + str(destination))
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'verified' if args.check else 'generated',
                      'counts': inventory['counts'], 'coverage': inventory['coverage'],
                      'outputs': [str(path) for path, _ in outputs]}, ensure_ascii=False))


if __name__ == '__main__':
    main()

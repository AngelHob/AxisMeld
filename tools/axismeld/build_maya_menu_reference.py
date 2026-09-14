#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Normalize the audited Maya snapshot into inert, deterministic reference data.

No Maya command is evaluated. runtimeCommand names are provenance, never bindings.
Dynamic policies below match complete display paths, not substrings or enabled state.
Run with --check to verify all three generated artifacts without writing them.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import pprint
import re


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/reference/maya2026-menu-tree.json'
BOUNDARIES = ROOT / 'docs/development/2026-09-14-maya-dynamic-menu-boundaries.md'
PYTHON = ROOT / 'scripts/modules/axismeld/maya_menu_reference.py'
HEADER = ROOT / 'source/blender/axismeld/AXM_maya_menu_reference.hh'
AUDIT = ROOT / 'docs/reference/maya2026-menu-normalization.json'

ROOTS = {
    'common': ('file', 'edit', 'create', 'select', 'modify', 'display', 'windows'),
    'current_pane': ('view', 'shading', 'lighting', 'show', 'renderer', 'panels'),
    'modeling': ('mesh', 'edit_mesh', 'mesh_tools', 'mesh_display', 'curves',
                 'surfaces', 'deform', 'uv', 'generate'),
}

# These are dynamic providers, even when the captured scene happened to be empty.
DYNAMIC = {
    ('File', 'Recent Files'): 'Recent files require current user history',
    ('File', 'Recent Increments'): 'Recent increments require current file history',
    ('File', 'Recent Projects'): 'Recent projects require current user history',
    ('Edit', 'Recent Commands List'): 'Command history belongs to the current session',
    ('Edit', 'Delete by Type', 'Sounds'): 'Sound members require current scene audio nodes',
    ('Select', 'Quick Select Sets'): 'Quick select sets require current scene sets',
    ('Modify', 'Asset', 'Advanced Assets', 'Set Current Asset'):
        'Asset members require current scene containers; None remains a fixed action',
    ('Windows', 'Workspaces'):
        'Factory, user and module workspace registrations require a workspace provider',
    ('View', 'Bookmarks'): 'Named bookmarks require the source camera',
    ('View', 'Image Plane'): 'Image plane actions require the live source camera',
    ('View', 'Image Plane', 'Image Plane Attributes'):
        'Image plane members require the live source camera',
    ('Show', 'Isolate Select', 'Bookmarks'):
        'Dynamic Maya bookmark enumeration failed in the audited capture; fixed actions retained',
    ('Panels', 'Perspective'): 'Perspective camera members require the current scene',
    ('Panels', 'Orthographic'): 'Orthographic camera members require the current scene',
    ('Panels', 'Stereo'): 'Stereo rigs and camera sets require scene and plugin providers',
    ('Panels', 'Saved Layouts'): 'Saved layouts are registered configuration instances',
    ('Panels', 'Panel'): 'Panel types and instances require the current panel registry',
    ('Panels', 'Hypergraph Panel'): 'Existing Hypergraph panels require the current panel registry',
    ('Renderer',): 'Renderer entries require the current renderer registry',
    ('Mesh Display', 'Assign Existing Set'): 'Bake set members require current scene sets',
    ('Create', 'Lights'): 'Additional light types depend on plugin registration',
    ('Create', 'Cameras'): 'Additional camera types depend on plugin registration',
    ('Create', 'Scene Assembly'): 'Assembly types require registered capabilities',
}

EMPTY_MEMBERS = {
    ('File', 'Recent Files'), ('File', 'Recent Increments'), ('File', 'Recent Projects'),
    ('Edit', 'Delete by Type', 'Sounds'), ('Select', 'Quick Select Sets'),
    ('View', 'Image Plane', 'Image Plane Attributes'),
    ('Mesh Display', 'Assign Existing Set'),
}
FIXED_MEMBERS = {
    ('Modify', 'Asset', 'Advanced Assets', 'Set Current Asset'): {'None'},
    ('View', 'Bookmarks'): {'Edit Bookmarks...'},
    ('Show', 'Isolate Select', 'Bookmarks'): {'Bookmark Current Objects'},
    ('Panels', 'Perspective'): {'New'},
    ('Panels', 'Orthographic'): {'New'},
    ('Panels', 'Stereo'): {'Create Stereo Camera', 'Create Stereo Layer'},
    ('Panels', 'Saved Layouts'): {'Edit Layouts...'},
    ('Panels', 'Hypergraph Panel'): {'New Scene Hierarchy', 'New Input and Output Connections'},
}
WORKSPACE_ACTIONS = {
    'ResetCurrentWorkspace', 'SaveCurrentWorkspace', 'ImportWorkspaceFiles',
    'DeleteCurrentWorkspace',
}

# buildEditMenu.mel:79-124 appends current repeat/undo/redo history names.
# Match the exact parent and RTC, never labels such as Undo View Change or Repeat Tool.
HISTORY_LABELS = {'Undo': 'Undo', 'Redo': 'Redo', 'RepeatLast': 'Repeat'}


def slug(label):
    return re.sub(r'[^a-z0-9]+', '_', label.casefold()).strip('_') or 'separator'


def normalize(source):
    audit = []
    ids = set()

    def record(action, raw, path, reason, **extra):
        audit.append({'action': action, 'path': path, 'source_ui_path': raw.get('path'),
                      'source_label': raw.get('label', ''), 'reason': reason,
                      'source_evidence': {key: raw.get(key) for key in
                                          ('command', 'runtimeCommand', 'dividerLabel', 'optionBox')},
                      **extra})

    def removal(raw, parent):
        # Separators are structure, including empty ones around dynamic providers.
        if raw.get('divider'):
            return None
        if parent in EMPTY_MEMBERS:
            return DYNAMIC[parent]
        if parent in FIXED_MEMBERS and raw.get('label') not in FIXED_MEMBERS[parent]:
            return DYNAMIC[parent]
        if parent == ('Windows', 'Workspaces'):
            if (raw.get('runtimeCommand') not in WORKSPACE_ACTIONS and
                    raw.get('label') != 'Disable Docking/Undocking'):
                return DYNAMIC[parent]
        return None

    def register(identifier):
        if identifier in ids:
            raise ValueError('Duplicate normalized identity: ' + identifier)
        ids.add(identifier)
        return identifier

    def children(raw_nodes, parent, root_id, parent_id):
        result = []
        prior = None
        prior_removed_reason = None
        prior_source_label = ''
        # Semantic sibling signatures avoid dependence on numbered Maya UI controls.
        signatures = Counter()
        def stable_neighbor(raw):
            if raw.get('optionBox') or raw.get('divider') or removal(raw, parent):
                return None
            if raw.get('runtimeCommand') == 'ResetCurrentWorkspace':
                return 'Reset Current Workspace to Factory Default'
            if parent == ('Edit',) and raw.get('runtimeCommand') in HISTORY_LABELS:
                return HISTORY_LABELS[raw['runtimeCommand']]
            return raw.get('label', '')

        for index, raw in enumerate(raw_nodes):
            if raw.get('optionBox'):
                if prior_removed_reason:
                    record('remove', raw, parent + (prior_source_label, 'Options'), prior_removed_reason)
                    continue
                if prior is None or prior['kind'] == 'separator' or 'options' in prior:
                    raise ValueError('Orphan or duplicate OptionBox: ' + str(raw.get('path')))
                prior['options'] = {
                    'id': register(prior['id'] + '.options'), 'kind': 'item', 'label': 'Options',
                    'path': prior['path'] + ('Options',),
                    'maya_command': raw.get('runtimeCommand') or '', 'indicator': '', 'children': (),
                }
                continue
            label = raw.get('dividerLabel') or raw.get('label') or ''
            prior_source_label = label
            path = parent + (label,)
            reason = removal(raw, parent)
            prior = None
            prior_removed_reason = reason
            if reason:
                record('remove', raw, path, reason)
                continue
            if parent == ('Windows', 'Workspaces') and raw.get('runtimeCommand') == 'ResetCurrentWorkspace':
                label = 'Reset Current Workspace to Factory Default'
                record('template', raw, path, 'Current workspace name is contextual', replacement=label)
                path = parent + (label,)
            if (parent == ('Edit',) and not raw.get('divider') and
                    raw.get('runtimeCommand') in HISTORY_LABELS):
                fixed_label = HISTORY_LABELS[raw['runtimeCommand']]
                if label != fixed_label:
                    record('template', raw, path,
                           'Edit action label appends current session history; '
                           'Maya startup/buildEditMenu.mel:79-124', replacement=fixed_label)
                label = fixed_label
                path = parent + (label,)
            kind = ('separator' if raw.get('divider') else
                    'menu' if raw.get('subMenu') or raw.get('kind') == 'menu' else 'item')
            key = slug(label)
            if kind == 'separator' and not label:
                # Anonymous separators are anchored to neighboring labels, not menuItem numbers.
                before = next((stable_neighbor(x) for x in reversed(raw_nodes[:index])
                               if stable_neighbor(x) is not None), 'start')
                after = next((stable_neighbor(x) for x in raw_nodes[index + 1:]
                              if stable_neighbor(x) is not None), 'end')
                key = 'separator_' + hashlib.sha256((before + '\0' + after).encode()).hexdigest()[:10]
            signature = (key, raw.get('runtimeCommand') or '', kind)
            signatures[signature] += 1
            identifier = parent_id + '.' + key
            if identifier in ids:
                suffix = hashlib.sha256(repr(signature).encode()).hexdigest()[:10]
                identifier += '_' + suffix + '_' + str(signatures[signature])
            node = {
                'id': register(identifier), 'kind': kind, 'label': label, 'path': path,
                'maya_command': '' if kind == 'separator' else raw.get('runtimeCommand') or '',
                'indicator': ('checkbox' if raw.get('isCheckBox') else
                              'radio' if raw.get('isRadioButton') else ''),
                'children': (),
            }
            if path in DYNAMIC:
                node['dynamic'] = DYNAMIC[path]
                record('dynamic_provider', raw, path, DYNAMIC[path])
            elif parent == ('Panels', 'Panel') or parent == ('Renderer',):
                node['dynamic'] = DYNAMIC[parent]
                record('dynamic_binding', raw, path, DYNAMIC[parent])
            if raw.get('runtimeCommand') == 'ResetCurrentWorkspace':
                node['dynamic'] = 'Workspace name and reset target require the current workspace'
            if raw.get('children'):
                node['children'] = children(raw['children'], path, root_id, identifier)
            result.append(node)
            prior = node
        return tuple(result)

    roots = []
    for group, names in ROOTS.items():
        raw_roots = source['groups'][group]
        if len(raw_roots) != len(names):
            raise ValueError('Unexpected root count: ' + group)
        for name, raw in zip(names, raw_roots):
            if slug(raw['label']) != name:
                raise ValueError('Unexpected root order or label: ' + raw['label'])
            root_id = ('pane' if group == 'current_pane' else group) + '.' + name
            root = {'id': register(root_id), 'label': raw['label'],
                    'children': children(raw.get('children', ()), (raw['label'],),
                                         root_id, 'maya.' + root_id)}
            if (raw['label'],) in DYNAMIC:
                root['dynamic'] = DYNAMIC[(raw['label'],)]
                record('dynamic_provider', raw, (raw['label'],), root['dynamic'])
            roots.append(root)
    return tuple(roots), audit


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))
        if 'options' in node:
            yield node['options']


def render():
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    menus, changes = normalize(source)
    nodes = tuple(walk(menus))
    indicators = {node['id']: node['indicator'] for node in nodes if node.get('indicator')}
    assert len(menus) == 22
    assert all('menuItem' not in node['id'] for node in nodes)
    assert all('checked' not in node and 'enabled' not in node for node in nodes)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    raw_nodes = tuple(walk(tuple(root for group in source['groups'].values() for root in group)))
    removed = sum(change['action'] == 'remove' for change in changes)
    if len(raw_nodes) != len(nodes) + removed:
        raise ValueError('Every raw node must be preserved, attached as Options, or audited as removed')
    python = (
        '# SPDX-FileCopyrightText: 2026 AxisMeld Authors\n'
        '# SPDX-License-Identifier: GPL-2.0-or-later\n'
        '"""Generated inert Maya reference; RTC names are evidence, not executable bindings.\n'
        'Regenerate with tools/axismeld/build_maya_menu_reference.py.\n"""\n\n'
        f'SOURCE_SHA256 = {source_hash!r}\n\n'
        'REFERENCE_MENUS = ' + pprint.pformat(menus, width=110, sort_dicts=False) + '\n\n'
        'UNAVAILABLE_INDICATORS = ' + pprint.pformat(indicators, width=110, sort_dicts=False) + '\n'
    )
    header = (
        '/* SPDX-FileCopyrightText: 2026 AxisMeld Authors\n'
        ' * SPDX-License-Identifier: GPL-2.0-or-later */\n'
        '#pragma once\n\n#include <array>\n#include <string_view>\n#include <utility>\n\n'
        'namespace blender::axismeld {\n\n'
        '/* Generated exact identities; never replace this with a prefix allowlist. */\n'
        f'inline constexpr std::array<std::pair<std::string_view, std::string_view>, {len(indicators)}>\n'
        '    maya_menu_unavailable_indicators = {{\n' +
        ''.join(f'        {{"{identifier}", "{style}"}},\n' for identifier, style in indicators.items()) +
        '    }};\n\n}  // namespace blender::axismeld\n'
    )
    audit = {'schema': 1, 'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
             'source_sha256': source_hash,
             'policy': str(BOUNDARIES.relative_to(ROOT)).replace('\\', '/'),
             'root_count': len(menus), 'node_count_including_options': len(nodes),
             'indicator_count': len(indicators), 'action_counts': dict(Counter(x['action'] for x in changes)),
             'identity_policy': 'Display-label ancestry; anonymous separators use neighboring label hashes. '
                                'Identical sibling semantic signatures use a local occurrence suffix. '
                                'Maya numbered UI paths never form identities.',
             'changes': changes}
    return {PYTHON: python, HEADER: header, AUDIT: json.dumps(audit, ensure_ascii=False, indent=2) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, text in render().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                raise SystemExit('Generated reference differs: ' + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8', newline='\n')
        print(('Checked ' if args.check else 'Wrote ') + str(path.relative_to(ROOT)))


if __name__ == '__main__':
    main()

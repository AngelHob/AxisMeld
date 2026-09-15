#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Convert trusted menubar captures into inert reference data, without Maya execution."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pprint
import runpy
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/reference/maya2026-menubar-tree.json'
PYTHON = ROOT / 'scripts/modules/axismeld/menubar_reference.py'
AUDIT = ROOT / 'docs/reference/maya2026-menubar-normalization.json'
LEGACY = runpy.run_path(str(ROOT / 'tools/axismeld/build_maya_menu_reference.py'))
OLD = runpy.run_path(str(ROOT / 'scripts/modules/axismeld/maya_menu_reference.py'))['REFERENCE_MENUS']
COMMON_UI = ('mainFileMenu','mainEditMenu','mainCreateMenu','mainSelectMenu','mainModifyMenu','mainDisplayMenu','mainWindowMenu')
COMMON_IDS = tuple('common.' + name for name in ('file','edit','create','select','modify','display','windows'))
MODEL_UI = ('mainMeshMenu','mainEditMeshMenu','mainMeshToolsMenu','mainMeshDisplayMenu','mainCurvesMenu','mainSurfacesMenu','mainDeformMenu','mainUVMenu','mainGenerateMenu')
MODEL_IDS = tuple('modeling.' + name for name in ('mesh','edit_mesh','mesh_tools','mesh_display','curves','surfaces','deform','uv','generate'))
SET_UI = {
    'MODELING': MODEL_UI,
    'RIGGING': ('mainRigSkeletonsMenu','mainRigSkinningMenu','mainRigDeformationsMenu','mainRigConstraintsMenu','mainRigControlMenu','mainBifrostRiggingMenu'),
    'ANIMATION': ('mainKeysMenu','mainPlaybackMenu','mainAudioMenu','mainVisualizeMenu','mainDeformationMenu','mainConstraintsMenu','mainMashMenu'),
    'FX': ('mainParticlesMenu','mainFluidsMenu','mainNClothMenu','mainHairMenu','mainNConstraintMenu','mainNCacheMenu','mainFieldsSolverMenu','mainDynEffectsMenu','mainMashMenu'),
    'RENDERING': ('mainShadingMenu','mainRenTexturingMenu','mainRenderMenu','mainCartoonMenu','mainStereoMenu'),
}
SET_NAMES = {'MODELING':'modelingMenuSet','RIGGING':'riggingMenuSet','ANIMATION':'animationMenuSet','FX':'dynamicsMenuSet','RENDERING':'renderingMenuSet'}
TAIL_UI = ('mainPipelineCacheMenu','Flow','ArnoldMenu','MainHelpMenu')
ROOT_IDS = dict(zip(COMMON_UI + MODEL_UI, COMMON_IDS + MODEL_IDS))
for key, paths in SET_UI.items():
    if key == 'MODELING':
        continue
    labels = {
        'RIGGING': ('skeleton','skin','deform','constrain','control','bifrost_rigging'),
        'ANIMATION': ('key','playback','audio','visualize','deform','constrain','mash'),
        'FX': ('nparticles','fluids','ncloth','nhair','nconstraint','ncache','fields_solvers','effects','mash'),
        'RENDERING': ('lighting_shading','texturing','render','toon','stereo'),
    }[key]
    ROOT_IDS.update(zip(paths, ('menubar.' + key.lower() + '.' + name for name in labels)))
ROOT_IDS.update(zip(TAIL_UI, ('menubar.cache','menubar.flow','menubar.arnold','menubar.help')))
ROOT_IDS['mainMashMenu'] = 'menubar.mash'
# These UI roots are distinct, but their normalized semantic trees were audited
# equal. Recheck that fact every generation; do not merge conditional differences.
ALIASES = {'mainRigDeformationsMenu':'mainDeformMenu', 'mainDeformationMenu':'mainDeformMenu',
           'mainConstraintsMenu':'mainRigConstraintsMenu'}
for alias, canonical in ALIASES.items():
    ROOT_IDS[alias] = ROOT_IDS[canonical]


def _without_ids(node):
    return {key: tuple(_without_ids(child) for child in value) if key == 'children' else
            _without_ids(value) if key == 'options' else value
            for key,value in node.items() if key != 'id'}


BUNDLED_WORKSPACES = frozenset({
    'General', 'Modeling - Standard', 'Modeling - Expert', 'Sculpting', 'Pose Sculpting',
    'UV Editing', 'XGen', 'XGen - Interactive Groom', 'Rigging', 'Animation',
    'Rendering - Standard', 'Rendering - Expert', 'MASH', 'Motion Graphics', 'Bifrost Fluids',
})


def _restore_bundled_workspaces(raw, root, audit, environment):
    """Normalize this version's bundled layouts separately from user instances.

    Factory names: Maya startup/buildViewMenu.mel:29-48 and resources/workspaces.
    Bifrost Fluids: Bifrost 2.14.1.0 resources/workspaces/Bifrost_Fluids.json.
    The standalone conversion reuses Options/ID rules without changing the older
    hotbox normalizer's intentionally different workspace-provider policy.
    """
    workspace_raw = next(n for n in raw['children'] if n.get('label') == 'Workspaces')
    workspace = next(n for n in root['children'] if n['label'] == 'Workspaces')
    kept = []
    keep_options = False
    for item in workspace_raw['children']:
        label = item.get('label', '').removesuffix('*')
        if item.get('optionBox'):
            if keep_options:
                kept.append(deepcopy(item))
            continue
        keep_options = bool(item.get('divider') or label in BUNDLED_WORKSPACES or
                            item.get('runtimeCommand') in LEGACY['WORKSPACE_ACTIONS'] or
                            label == 'Disable Docking/Undocking')
        if not keep_options:
            continue
        child = deepcopy(item)
        child['label'] = label
        if item.get('runtimeCommand') == 'ResetCurrentWorkspace':
            child['label'] = 'Reset Current Workspace to Factory Default'
        kept.append(child)
    local = dict(environment, ROOTS={'common.windows': ('workspaces',)})
    converter = types.FunctionType(LEGACY['normalize'].__code__, local)
    converted, _ = converter({'groups': {'common.windows': [dict(workspace_raw, children=kept)]}})
    def prefix(node):
        if 'path' in node:
            node['path'] = ('Windows',) + node['path']
        for child in node.get('children', ()):
            prefix(child)
        if node.get('options'):
            prefix(node['options'])
    for node in converted[0]['children']:
        prefix(node)
    workspace['children'] = converted[0]['children']
    restored_paths = {item['path'] for item in kept}
    audit[:] = [entry for entry in audit if not
                (entry['action'] == 'remove' and entry['source_ui_path'] in restored_paths)]
    for item in workspace_raw['children']:
        if item.get('label', '').endswith('*') and item['label'][:-1] in BUNDLED_WORKSPACES:
            audit.append({'action': 'template', 'source_ui_path': item['path'],
                          'source_label': item['label'], 'path': ('Windows', 'Workspaces', item['label']),
                          'replacement': item['label'][:-1],
                          'reason': 'Bundled workspace name retained; current-layout marker is session state'})


def _convert(raw, identifier):
    # Reuse audited Options/separator/history normalization in a private globals
    # dictionary. No old source/reference or live module globals are changed.
    raw = deepcopy(raw)
    raw['label'] = raw['label'].strip()
    group, name = identifier.rsplit('.', 1)
    environment = dict(LEGACY['normalize'].__globals__)
    environment['ROOTS'] = {group: (name,)}
    dynamic = {
        ('Lighting/Shading','Assign Existing Material'): 'Scene material instances; startup/buildShaderMenus.mel:342,546-549',
        ('Toon','Set Camera Background Color'): 'Live camera instances; paintEffects/buildCartoonMenu.mel:68-88',
        ('Toon','Assign Outline'): 'Live pfxToon nodes after two fixed actions; paintEffects/buildCartoonMenu.mel:47-64',
    }
    environment['DYNAMIC'] = dict(environment['DYNAMIC']) | dynamic
    environment['EMPTY_MEMBERS'] = set(environment['EMPTY_MEMBERS']) | set(tuple(dynamic)[:2])
    environment['FIXED_MEMBERS'] = dict(environment['FIXED_MEMBERS']) | {
        ('Toon','Assign Outline'): {'Add New Toon Outline','Remove Current Toon Outlines'}}
    converter = types.FunctionType(LEGACY['normalize'].__code__, environment)
    roots, audit = converter({'groups': {group: [raw]}})
    if identifier == 'common.windows':
        _restore_bundled_workspaces(raw, roots[0], audit, environment)
    return roots[0], audit


def normalize(source):
    if source.get('errors'):
        raise ValueError('Menubar capture has unresolved builder errors')
    rows = source.get('menu_sets', ())
    if len(rows) != 5 or tuple(row.get('label','').upper() for row in rows) != tuple(SET_UI):
        raise ValueError('Expected five canonical menu sets')
    trees = source.get('trees', {})
    required = set(COMMON_UI + TAIL_UI).union(*(set(value) for value in SET_UI.values()))
    if set(trees) != required:
        raise ValueError('Unexpected or missing captured root: ' + repr(set(trees) ^ required))
    converted = {}
    audit = []
    for path, raw in trees.items():
        if raw.get('path') != path:
            raise ValueError('Root UI identity does not match captured tree: ' + path)
        converted[path], entries = _convert(raw, ROOT_IDS[path])
        audit.extend(entries)
    for alias, canonical in ALIASES.items():
        if _without_ids(converted[alias]) != _without_ids(converted[canonical]):
            raise ValueError('Shared menu content diverged: ' + alias)
        audit.append({'action':'shared_root','source_ui_path':alias,'canonical_ui_path':canonical,
                      'root_id':ROOT_IDS[canonical], 'reason':'Normalized content is identical; reuse one tree and its capabilities'})
    menus = {}
    for path, root in converted.items():
        if path not in ALIASES:
            menus[root['id']] = root
    sets = {}
    for row in rows:
        key = row['label'].upper()
        if row.get('current_menu_set') != SET_NAMES[key] or row.get('menu_set') != SET_NAMES[key]:
            raise ValueError('Capture did not switch to requested menu set: ' + key)
        if tuple(row.get('members', ())) != SET_UI[key]:
            raise ValueError('Unexpected menu-set member order: ' + key)
        visible = [n for n in row['top_menu_array'] if n.get('visible')]
        expected = COMMON_UI + SET_UI[key] + TAIL_UI
        if tuple(n['path'] for n in visible) != expected:
            raise ValueError('Unexpected visible application-menubar order: ' + key)
        for n in visible:
            if n['label'].strip() != menus[ROOT_IDS[n['path']]]['label']:
                raise ValueError('Visible label differs from tree: ' + n['path'])
        sets[key] = tuple(ROOT_IDS[n['path']] for n in visible)
    result = tuple(menus.values())
    identifiers = [n['id'] for n in LEGACY['walk'](result)]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate normalized menubar node IDs')
    return sets, result, audit


def render():
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    sets, menus, audit = normalize(source)
    dependencies = deepcopy(source.get('plugin_dependencies', {}))
    dependencies['maya.common.windows.workspaces.bifrost_fluids'] = {
        'plugin': 'Bifrost 2.14.1.0',
        'source': 'Bifrost/Maya2026/2.14.1.0/bifrost/resources/workspaces/Bifrost_Fluids.json',
        'scope': 'Bundled module workspace preset; no Blender layout adaptation',
    }
    if not {'menubar.flow','menubar.rigging.bifrost_rigging'} <= dependencies.keys():
        raise ValueError('Plugin roots need source-audited dependencies')
    all_ids = {n['id'] for n in LEGACY['walk'](menus)}
    if not set(dependencies) <= all_ids:
        raise ValueError('Dependency refers to an absent node')
    prefix = '# SPDX-FileCopyrightText: 2026 AxisMeld Authors\n# SPDX-License-Identifier: GPL-2.0-or-later\n'
    text = prefix + '\n"""Generated inert Maya menubar reference; edit its audited generator/source."""\n\n'
    for key,value in (('MENU_SETS',sets),('REFERENCE_MENUS',menus),('PLUGIN_DEPENDENCIES',dependencies)):
        text += key + ' = ' + pprint.pformat(value, width=110, sort_dicts=False) + '\n\n'
    notes = {'schema_version':1,'source':str(SOURCE.relative_to(ROOT)),
             'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'reused_normalizer':'tools/axismeld/build_maya_menu_reference.py',
             'stable_root_identity_reference':'scripts/modules/axismeld/maya_menu_reference.py',
             'menu_sets':sets,'unique_roots':len(menus),'nodes':len(all_ids),
             'plugin_dependencies':dependencies,'actions':audit}
    return {PYTHON:text, AUDIT:json.dumps(notes,ensure_ascii=False,indent=2)+'\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    for path,text in render().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                raise SystemExit('Stale generated artifact: ' + str(path))
            print('Checked',path.relative_to(ROOT))
        else:
            path.write_text(text,encoding='utf-8')
            print('Wrote',path.relative_to(ROOT))


if __name__ == '__main__':
    main()

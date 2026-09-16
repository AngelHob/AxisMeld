# SPDX-License-Identifier: GPL-2.0-or-later
"""Add the reviewed Rigging workspace to a clean, explicitly supplied startup.

Run with Python 3.14 (or Python plus zstandard):
  THIS_FILE --blender EXE --input ORIGINAL.blend --output NEW.blend --manifest JSON

Input and output must differ. Existing Rigging workspaces are rejected.
An isolated background process records the uninitialized input; a separate GUI
process performs the native workspace switch; a third process checks the saved
file. The saved DNA must have a layout relation for every window/workspace.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

try:
    import bpy
    from mathutils import Color, Euler, Matrix, Quaternion, Vector
except ImportError:
    bpy = None


EXPECTED_WORKSPACES = {
    'Layout', 'Modeling', 'Sculpting', 'UV Editing', 'Texture Paint', 'Shading',
    'Animation', 'Rendering', 'Compositing', 'Geometry Nodes', 'Scripting',
}


def _plain(value):
    if hasattr(value, 'to_dict'):
        return _plain(value.to_dict())
    if hasattr(value, 'to_list'):
        return _plain(value.to_list())
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, Color, Euler, Matrix, Quaternion, Vector)):
        return [_plain(item) for item in value]
    if not isinstance(value, (str, bytes)) and hasattr(value, '__iter__'):
        return [_plain(item) for item in value]
    return value


def _scalars(value):
    """Writable RNA values, excluding runtime pointers and derived values."""
    result = {}
    for prop in value.bl_rna.properties:
        if prop.is_readonly or prop.type not in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
            continue
        item = getattr(value, prop.identifier)
        if getattr(prop, 'is_array', False):
            item = list(item)
        elif isinstance(item, set):
            item = sorted(item)
        result[prop.identifier] = _plain(item)
    return result


def _custom(value):
    return {key: _plain(item) for key, item in value.items()}


def _space(space):
    state = {'type': space.type, 'properties': _scalars(space)}
    if space.type == 'VIEW_3D':
        state.update(shading=_scalars(space.shading), overlay=_scalars(space.overlay))
        if space.region_3d:
            state['region_3d'] = _scalars(space.region_3d)
    return state


def semantic_manifest():
    """Reviewable defaults inventory; intentionally excludes runtime ID users."""
    inventory = {}
    for prop in bpy.data.bl_rna.properties:
        if prop.type == 'COLLECTION':
            inventory[prop.identifier] = sorted(item.name for item in getattr(bpy.data, prop.identifier))
    workspaces = {}
    for workspace in bpy.data.workspaces:
        workspaces[workspace.name] = dict(
            properties=_scalars(workspace), custom=_custom(workspace),
            tools=[dict(idname=tool.idname, mode=tool.mode, space_type=tool.space_type)
                   for tool in workspace.tools],
            screens=[dict(name=screen.name, properties=_scalars(screen),
                          areas=[dict(type=area.type,
                                      geometry=[area.x, area.y, area.width, area.height],
                                      active=area.spaces.active.type,
                                      spaces=[_space(space) for space in area.spaces])
                                 for area in screen.areas]) for screen in workspace.screens])
    objects = {}
    for obj in bpy.data.objects:
        objects[obj.name] = dict(properties=_scalars(obj), custom=_custom(obj),
                                data=obj.data.name if obj.data else None,
                                parent=obj.parent.name if obj.parent else None,
                                modifiers=[(m.type, _scalars(m)) for m in obj.modifiers],
                                constraints=[(c.type, _scalars(c)) for c in obj.constraints],
                                selected=obj.select_get())
    meshes = {mesh.name: dict(properties=_scalars(mesh), custom=_custom(mesh),
                             vertices=[list(v.co) for v in mesh.vertices],
                             edges=[list(e.vertices) for e in mesh.edges],
                             faces=[list(p.vertices) for p in mesh.polygons],
                             uv_layers={uv.name: [list(v.uv) for v in uv.data] for uv in mesh.uv_layers},
                             materials=[m.name if m else None for m in mesh.materials])
              for mesh in bpy.data.meshes}
    scenes = {scene.name: dict(properties=_scalars(scene), custom=_custom(scene),
                              render=_scalars(scene.render), units=_scalars(scene.unit_settings),
                              tool_settings=_scalars(scene.tool_settings),
                              camera=scene.camera.name if scene.camera else None,
                              world=scene.world.name if scene.world else None,
                              objects=sorted(scene.objects.keys()),
                              view_layers={layer.name: dict(properties=_scalars(layer),
                                                           active=layer.objects.active.name if layer.objects.active else None)
                                           for layer in scene.view_layers})
              for scene in bpy.data.scenes}
    state = dict(inventory=inventory, workspaces=workspaces, objects=objects,
                 meshes=meshes, scenes=scenes,
                 other_data={kind: {item.name: dict(properties=_scalars(item), custom=_custom(item))
                                    for item in getattr(bpy.data, kind)}
                             for kind in ('cameras', 'lights', 'materials', 'worlds')},
                 windows=[dict(workspace=w.workspace.name, screen=w.screen.name, scene=w.scene.name)
                          for w in bpy.context.window_manager.windows])
    # JSON-normalize tuples before comparing against a later process/reload.
    return json.loads(json.dumps(state, sort_keys=True))


def assert_only_rigging_added(before, after):
    assert set(after['workspaces']) == set(before['workspaces']) | {'Rigging'}
    projected = json.loads(json.dumps(after))
    rigging = projected['workspaces'].pop('Rigging')
    projected['inventory']['workspaces'].remove('Rigging')
    projected['inventory']['all_ids'].remove('Rigging')
    for screen in rigging['screens']:
        projected['inventory']['screens'].remove(screen['name'])
        projected['inventory']['all_ids'].remove(screen['name'])
    assert projected == before, 'Original default scene/workspace/data semantics changed; inspect manifest'
    assert rigging['properties']['object_mode'] == 'OBJECT'
    assert rigging['custom']['axismeld_workspace_role'] == 'RIGGING'
    assert len(rigging['screens']) == 1
    actual = rigging['screens'][0]['areas']
    expected = before['workspaces']['Modeling']['screens'][0]['areas']
    assert actual == expected, 'Rigging must copy Modeling geometry and editor settings'


def raw_layout_relations(path):
    """Inspect persisted IDs, not pointers fabricated by an ordinary file load."""
    try:
        import zstandard  # noqa: F401
    except ImportError:
        from compression import zstd
        sys.modules['zstandard'] = zstd
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'modules'))
    import blendfile
    with blendfile.open_blend(str(path)) as blend:
        windows = [block for block in blend.blocks
                   if blend.structs[block.sdna_index].dna_type_id == b'wmWindow']
        winids = [window.get(b'winid') for window in windows]
        assert winids and len(winids) == len(set(winids))
        relations = {}
        for workspace in blend.find_blocks_from_code(b'WS'):
            name = workspace.get((b'id', b'name'))[2:]
            layouts = []
            layout = workspace.get_pointer((b'layouts', b'first'))
            while layout:
                assert layout.get_pointer(b'screen') is not None, (name, 'Missing screen')
                layouts.append(layout.addr_old)
                layout = layout.get_pointer(b'next')
            parents = []
            relation = workspace.get_pointer((b'hook_layout_relations', b'first'))
            while relation:
                assert relation.get(b'value') in layouts, (name, 'Foreign layout relation')
                parents.append(relation.get(b'parentid'))
                relation = relation.get_pointer(b'next')
            assert sorted(parents) == sorted(winids), (name, 'Missing/duplicate window relation', parents, winids)
            relations[name] = parents
        assert relations
        return dict(window_ids=winids, workspace_relations=relations,
                    windows=[{key: window.get(key.encode()) for key in
                              ('winid', 'sizex', 'sizey', 'windowstate', 'posx', 'posy')}
                             for window in windows])


def _duplicate():
    template = bpy.data.workspaces['Modeling']
    assert len(template.screens) == 1
    assert sorted(a.type for a in template.screens[0].areas) == ['OUTLINER', 'PROPERTIES', 'VIEW_3D']
    # Generic ID.copy() decrements this NEVER_UNUSED ID's real users to zero.
    # The native duplicate operator also schedules its necessary GUI switch.
    old_ids = {workspace.as_pointer() for workspace in bpy.data.workspaces}
    with bpy.context.temp_override(workspace=template):
        assert bpy.ops.workspace.duplicate() == {'FINISHED'}
    created = [workspace for workspace in bpy.data.workspaces if workspace.as_pointer() not in old_ids]
    assert len(created) == 1
    rigging = created[0]
    assert rigging.users > 0
    rigging.name = 'Rigging'
    rigging.object_mode = 'OBJECT'
    rigging['axismeld_workspace_role'] = 'RIGGING'
    rigging.screens[0].name = 'Rigging'
    with bpy.context.temp_override(workspace=rigging):
        assert bpy.ops.workspace.reorder_to_back() == {'INTERFACE'}
    return rigging


def blender_stage(args):
    source, target, manifest = map(Path, (args.input, args.output, args.manifest))
    bpy.context.preferences.use_preferences_save = False
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.preferences.view.show_splash = False
    def open_regular(path):
        assert bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=True, use_scripts=False) == {'FINISHED'}
    if args.stage == 'baseline':
        open_regular(source)
        assert set(bpy.data.workspaces.keys()) == EXPECTED_WORKSPACES, 'Unexpected input workspace set'
        assert not any(w.get('axismeld_workspace_role') == 'RIGGING' for w in bpy.data.workspaces)
        assert bpy.context.window.workspace.name == 'Layout'
        assert set(bpy.data.objects.keys()) == {'Camera', 'Cube', 'Light'}
        manifest.write_text(json.dumps({'before': semantic_manifest()}, indent=2), encoding='utf-8')
        return
    evidence = json.loads(manifest.read_text(encoding='utf-8'))
    if args.stage == 'verify':
        open_regular(target)
        evidence['after_reopen'] = semantic_manifest()
        assert_only_rigging_added(evidence['before'], evidence['after_reopen'])
        manifest.write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        return
    assert args.stage == 'create' and not bpy.app.background
    phase = 0
    def tick():
        nonlocal phase
        try:
            if phase == 0:
                open_regular(source)
                evidence['gui_before'] = semantic_manifest()
                assert evidence['gui_before'] == evidence['before'], (
                    'GUI normalized the original layout; use a display matching input dimensions')
            elif phase == 1:
                _duplicate()
            elif phase == 2:
                # ED_workspace_change creates the hook_layout_relation. Merely
                # assigning window.workspace in background never processes it.
                assert bpy.context.window.workspace.name == 'Rigging'
                evidence['activated_workspace'] = 'Rigging'
                bpy.context.window.workspace = bpy.data.workspaces['Layout']
            elif phase == 3:
                assert bpy.context.window.workspace.name == 'Layout'
                evidence['after_in_memory'] = semantic_manifest()
                assert_only_rigging_added(evidence['before'], evidence['after_in_memory'])
                assert bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=False,
                                                 copy=True, compress=True, relative_remap=False) == {'FINISHED'}
            else:
                manifest.write_text(json.dumps(evidence, indent=2), encoding='utf-8')
                print('AXISMELD_RIGGING_GUI_ASSET_PASS', flush=True)
                bpy.ops.wm.quit_blender()
                return None
            phase += 1
            return 0.5
        except BaseException:
            evidence['error'] = traceback.format_exc()
            manifest.write_text(json.dumps(evidence, indent=2), encoding='utf-8')
            traceback.print_exc()
            # Timer exceptions do not propagate to --python-exit-code.
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(1)
    bpy.app.timers.register(tick, first_interval=1, persistent=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', help='Known-good Blender with the original startup')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--stage', choices=('baseline', 'create', 'verify'), help=argparse.SUPPRESS)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if bpy else None)
    for field in ('input', 'output', 'manifest'):
        setattr(args, field, str(Path(getattr(args, field)).resolve()))
    if bpy:
        blender_stage(args)
        return
    assert args.blender, '--blender is required'
    source, target, manifest = map(Path, (args.input, args.output, args.manifest))
    assert source != target, 'Never overwrite the input startup while generating'
    assert not target.exists(), 'Output already exists; select a fresh output file'
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    work = manifest.parent / (manifest.stem + '-processes')
    work.mkdir(exist_ok=False)
    env = os.environ.copy()
    for name in ('config', 'scripts', 'tmp'):
        (work / name).mkdir()
    env.update(BLENDER_USER_CONFIG=str(work / 'config'), BLENDER_USER_SCRIPTS=str(work / 'scripts'),
               TEMP=str(work / 'tmp'), TMP=str(work / 'tmp'), TMPDIR=str(work / 'tmp'))
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    evidence = dict(input=args.input, input_sha256=source_sha, output=args.output,
                    binary=str(Path(args.blender).resolve()),
                    binary_sha256=hashlib.sha256(Path(args.blender).read_bytes()).hexdigest(),
                    generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    input_layout_relations=raw_layout_relations(source), stages=[])
    try:
        startup = None
        if sys.platform == 'win32':
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = subprocess.SW_HIDE
        for stage in ('baseline', 'create', 'verify'):
            # Match the original startup's 1920x1080 drawable area. Window
            # borders would rescale Layout/Rigging while leaving other tabs raw.
            flags = ['--window-fullscreen'] if stage == 'create' else ['--background']
            command = [args.blender, '--factory-startup', *flags, '--python-exit-code', '1',
                       '--python', str(Path(__file__).resolve()), '--', '--stage', stage,
                       '--input', args.input, '--output', args.output, '--manifest', args.manifest]
            result = subprocess.run(command, env=env, startupinfo=startup, capture_output=True, timeout=90)
            (work / (stage + '.stdout.log')).write_bytes(result.stdout)
            (work / (stage + '.stderr.log')).write_bytes(result.stderr)
            evidence['stages'].append(dict(stage=stage, command=command, exit_code=result.returncode))
            assert result.returncode == 0, (stage, result.returncode, 'See process logs')
            assert b'Traceback (most recent call last):' not in result.stdout + result.stderr
        evidence.update(json.loads(manifest.read_text(encoding='utf-8')))
        evidence['output_layout_relations'] = raw_layout_relations(target)
        assert evidence['output_layout_relations']['windows'] == evidence['input_layout_relations']['windows']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha, 'Input was modified'
        evidence['output_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        evidence['status'] = 'PASS'
        print('AXISMELD_RIGGING_STARTUP_ASSET_PASS', target, evidence['output_sha256'])
    except BaseException:
        evidence['status'] = 'FAIL'
        evidence['error'] = traceback.format_exc()
        raise
    finally:
        manifest.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()

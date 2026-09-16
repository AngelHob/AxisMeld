# SPDX-License-Identifier: GPL-2.0-or-later
"""Real default Rigging workspace acceptance; run with Blender --background.

Example: blender --background --factory-startup --python-exit-code 1 --python
axismeld_rigging_workspace_test.py -- --case factory --artifacts DIR
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    import bpy
except ImportError:
    bpy = None


ORIGINAL_NAMES = {
    'Layout', 'Modeling', 'Sculpting', 'UV Editing', 'Texture Paint', 'Shading',
    'Animation', 'Rendering', 'Compositing', 'Geometry Nodes', 'Scripting',
}


def geometry(workspace):
    return [sorted((area.type, area.x, area.y, area.width, area.height)
                   for area in screen.areas) for screen in workspace.screens]


def scene_state():
    return {'scenes': sorted(bpy.data.scenes.keys()),
            'objects': {obj.name: {'type': obj.type, 'mode': obj.mode,
                                    'matrix': [list(row) for row in obj.matrix_world],
                                    'selected': obj.select_get(),
                                    'mesh': [list(v.co) for v in obj.data.vertices] if obj.type == 'MESH' else None}
                        for obj in bpy.data.objects},
            'active': bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None}


def workspace_state():
    return {workspace.name: {'mode': workspace.object_mode,
                            'role': workspace.get('axismeld_workspace_role'),
                            'geometry': geometry(workspace),
                            'screens': [screen.name for screen in workspace.screens],
                            'view_gizmos': [area.spaces.active.show_gizmo for screen in workspace.screens
                                            for area in screen.areas if area.type == 'VIEW_3D']}
            for workspace in bpy.data.workspaces}


def state():
    return json.loads(json.dumps(dict(scene=scene_state(), workspaces=workspace_state(),
                                     active=bpy.context.window.workspace.name)))


def open_file(path, *, load_ui=True):
    assert bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()), load_ui=load_ui, use_scripts=False) == {'FINISHED'}


def assert_original_workspaces():
    assert set(bpy.data.workspaces.keys()) == ORIGINAL_NAMES
    assert not any(w.get('axismeld_workspace_role') == 'RIGGING' for w in bpy.data.workspaces)
    assert bpy.context.window.workspace.name == 'Layout'


def assert_rigging():
    names = set(bpy.data.workspaces.keys())
    assert 'Rigging' in names, ('Factory workspace is missing Rigging', sorted(names))
    assert names == ORIGINAL_NAMES | {'Rigging'}, ('Unexpected workspace set', sorted(names))
    rigging = bpy.data.workspaces['Rigging']
    assert rigging.get('axismeld_workspace_role') == 'RIGGING'
    assert rigging.object_mode == 'OBJECT', 'Entering Rigging must not force Edit/Pose mode'
    assert len(rigging.screens) == 1
    assert sorted(area.type for area in rigging.screens[0].areas) == ['OUTLINER', 'PROPERTIES', 'VIEW_3D']
    assert geometry(rigging) == geometry(bpy.data.workspaces['Modeling'])
    assert rigging.screens[0] != bpy.data.workspaces['Modeling'].screens[0], 'Layouts must be independent'
    assert bpy.context.window.workspace.name == 'Layout', 'Factory active workspace changed'
    assert set(bpy.data.objects.keys()) == {'Camera', 'Cube', 'Light'}
    cube = bpy.data.objects['Cube']
    assert cube.mode == 'OBJECT' and len(cube.data.vertices) == 8 and len(cube.data.polygons) == 6
    assert bpy.context.view_layer.objects.active == cube
    assert len(bpy.data.scenes) == 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('raw-asset', 'factory', 'asset', 'append-save', 'embedded-append', 'reopen', 'gui-reopen',
                                          'old-file', 'no-ui', 'user-startup', 'factory-reset'), default='factory')
    parser.add_argument('--asset')
    parser.add_argument('--original', help='Unmodified old startup, used as an existing user file fixture')
    parser.add_argument('--artifacts', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if bpy else None)
    art = Path(args.artifacts).resolve()
    art.mkdir(parents=True, exist_ok=True)
    if args.case == 'raw-asset':
        # Ordinary file loading can repair missing layout relationships. Inspect
        # the saved DNA before that repair, since factory versioning needs it.
        import importlib.util
        path = Path(__file__).resolve().parents[2] / 'tools/utils/axismeld_rigging_workspace_asset.py'
        spec = importlib.util.spec_from_file_location('workspace_asset', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert args.asset
        evidence = dict(case=args.case, asset_sha256=hashlib.sha256(Path(args.asset).read_bytes()).hexdigest(),
                        test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        try:
            evidence.update(module.raw_layout_relations(args.asset))
            assert set(evidence['workspace_relations']) == ORIGINAL_NAMES | {'Rigging'}
        except BaseException:
            evidence['status'] = 'FAIL'
            raise
        else:
            evidence['status'] = 'PASS'
            print('AXISMELD_RIGGING_WORKSPACE_PASS', args.case, flush=True)
        finally:
            (art / 'raw-asset-receipt.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        return
    assert bpy is not None, 'Run behavior cases inside Blender'
    bpy.context.preferences.use_preferences_save = False
    evidence = dict(case=args.case, exe=bpy.app.binary_path,
                    exe_sha256=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
                    test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    startup_names=sorted(bpy.data.workspaces.keys()))
    (art / 'test-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        if args.case == 'asset':
            assert args.asset, '--case asset requires --asset'
            evidence['asset_sha256'] = hashlib.sha256(Path(args.asset).read_bytes()).hexdigest()
            open_file(args.asset)
            assert_rigging()
        elif args.case == 'factory':
            assert_rigging()
        elif args.case == 'factory-reset':
            assert_rigging()
            for _ in range(2):
                assert bpy.ops.wm.read_factory_settings(use_empty=False) == {'FINISHED'}
                assert_rigging()
        elif args.case in {'append-save', 'embedded-append'}:
            assert args.original
            if args.case == 'append-save':
                assert args.asset
            open_file(args.original)
            assert_original_workspaces()
            original = state()
            # This is the exact native filepath sentinel used by + > General.
            source = '<startup.blend>' if args.case == 'embedded-append' else str(Path(args.asset).resolve())
            assert bpy.ops.workspace.append_activate(idname='Rigging', filepath=source) == {'FINISHED'}
            added = bpy.data.workspaces['Rigging']
            assert added.users > 0 and added.get('axismeld_workspace_role') == 'RIGGING'
            assert added.object_mode == 'OBJECT'
            assert geometry(added) == geometry(bpy.data.workspaces['Modeling'])
            assert scene_state() == original['scene'], 'Adding a workspace imported or changed scene data'
            assert bpy.context.window.workspace.name == 'Layout', 'Background append must defer GUI switching'
            added.name = 'Custom Rigging'
            ids = {workspace.as_pointer() for workspace in bpy.data.workspaces}
            with bpy.context.temp_override(workspace=added):
                assert bpy.ops.workspace.duplicate() == {'FINISHED'}
            duplicates = [workspace for workspace in bpy.data.workspaces if workspace.as_pointer() not in ids]
            assert len(duplicates) == 1
            duplicate = duplicates[0]
            assert duplicate.users > 0 and duplicate.get('axismeld_workspace_role') == 'RIGGING'
            assert duplicate.object_mode == 'OBJECT' and geometry(duplicate) == geometry(added)
            assert duplicate.screens[0] != added.screens[0]
            original_view = next(a.spaces.active for a in added.screens[0].areas if a.type == 'VIEW_3D')
            copied_view = next(a.spaces.active for a in duplicate.screens[0].areas if a.type == 'VIEW_3D')
            original_gizmo = original_view.show_gizmo
            copied_view.show_gizmo = not original_gizmo
            assert original_view.show_gizmo == original_gizmo, 'Duplicated workspace mutated original editor state'
            after = state()
            assert after['scene'] == original['scene']
            assert all(after['workspaces'][name] == original['workspaces'][name] for name in ORIGINAL_NAMES)
            path = art / 'renamed-and-duplicated.blend'
            assert bpy.ops.wm.save_as_mainfile(filepath=str(path), check_existing=False) == {'FINISHED'}
            (art / 'saved-state.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
            evidence['saved_file'] = str(path)
        elif args.case in {'reopen', 'gui-reopen'}:
            gui = args.case == 'gui-reopen'
            open_file(art / ('gui-rigging.blend' if gui else 'renamed-and-duplicated.blend'))
            expected = json.loads((art / ('gui-saved-state.json' if gui else 'saved-state.json')).read_text(encoding='utf-8'))
            assert state() == expected, 'Saved names/role/editor settings/scene changed in a new process'
            assert all(w.users > 0 for w in bpy.data.workspaces)
            if gui:
                cube = bpy.data.objects['Cube']
                assert cube.parent and cube.parent.type == 'ARMATURE'
                assert len(cube.vertex_groups) > 10
                assert any(m.type == 'ARMATURE' and m.object == cube.parent for m in cube.modifiers)
                expected_weights = json.loads((art / 'gui-saved-weights.json').read_text())
                assert [[[g.group, g.weight] for g in v.groups] for v in cube.data.vertices] == expected_weights
        elif args.case in {'old-file', 'no-ui'}:
            assert args.original
            assert_rigging()
            before = workspace_state()
            open_file(args.original, load_ui=args.case == 'old-file')
            if args.case == 'old-file':
                assert_original_workspaces()
            else:
                assert workspace_state() == before, 'Load UI disabled must retain current workspaces'
        else:
            assert args.case == 'user-startup'
            # This case is launched without --factory-startup using an isolated
            # config containing the old startup, not by opening it afterwards.
            assert_original_workspaces()
        evidence['final_state'] = state()
    except BaseException:
        evidence['status'] = 'FAIL'
        raise
    else:
        evidence['status'] = 'PASS'
        print('AXISMELD_RIGGING_WORKSPACE_PASS', args.case, flush=True)
    finally:
        (art / (args.case + '-receipt.json')).write_text(json.dumps(evidence, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

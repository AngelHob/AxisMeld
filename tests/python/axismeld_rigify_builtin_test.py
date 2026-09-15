# SPDX-License-Identifier: GPL-2.0-or-later
"""Behavioral acceptance for factory-available Rigify, in isolated processes.

Run with ordinary Python and --blender/--artifacts. The same file is the Blender
worker; no test depends on the eventual built-in module installation directory.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

REQUIRED_OPERATORS = (
    'object.armature_basic_human_metarig_add',
    'pose.rigify_generate',
)
FEATURE_MODULE = 'axismeld_disabled_feature_fixture'


def _operator(bpy, identifier):
    module, name = identifier.split('.')
    return getattr(getattr(bpy.ops, module), name)


def _availability(bpy):
    available = {}
    for identifier in REQUIRED_OPERATORS:
        try:
            _operator(bpy, identifier).get_rna_type()
        except (AttributeError, KeyError, RuntimeError):
            available[identifier] = False
        else:
            available[identifier] = True
    return available


def _require_available(bpy):
    available = _availability(bpy)
    assert all(available.values()), ('Factory startup must expose Rigify without enabling an add-on', available)
    assert hasattr(bpy.types.PoseBone, 'rigify_type'), 'Rigify pose-bone RNA is absent'
    assert hasattr(bpy.types.PoseBone, 'rigify_parameters'), 'Rigify parameter RNA is absent'
    assert hasattr(bpy.types.Armature, 'rigify_target_rig'), 'Rigify target RNA is absent'


def _rig_state(bpy, metarig_name, rig_name):
    meta = bpy.data.objects[metarig_name]
    rig = bpy.data.objects[rig_name]
    assert meta.type == rig.type == 'ARMATURE' and meta != rig
    assert meta.data.rigify_target_rig == rig, 'Saved metarig lost its generated rig pointer'
    bones = sorted(rig.data.bones, key=lambda bone: bone.name)
    controls = [bone.name for bone in bones if not bone.name.startswith(('ORG-', 'DEF-', 'MCH-'))]
    assert 'root' in controls and len(controls) > 10, ('Control rig was not generated', controls)
    assert any(b.name.startswith('DEF-') for b in bones), 'Generated rig has no deformation bones'
    assert rig.data.get('rig_id'), 'Generated rig has no Rigify identity'
    constraints = [(p.name, c.name, c.type) for p in rig.pose.bones for c in p.constraints]
    assert constraints, 'Generated rig has no pose constraints'
    widgets = sorted({p.custom_shape.name for p in rig.pose.bones if p.custom_shape})
    assert widgets, 'Generated controls have no custom shape widgets'
    return dict(metarig=meta.name, rig=rig.name, rig_id=rig.data['rig_id'],
                metarig_types=sorted((p.name, p.rigify_type) for p in meta.pose.bones),
                bones=[(b.name, b.parent.name if b.parent else '', tuple(b.head_local), tuple(b.tail_local), b.use_deform) for b in bones],
                controls=controls, constraints=constraints, widgets=widgets,
                bone_collections=sorted((c.name, c.rigify_ui_row, c.rigify_ui_title) for c in rig.data.collections_all))


def _generate_and_save(bpy, art, prefix):
    _require_available(bpy)
    assert bpy.ops.object.armature_basic_human_metarig_add() == {'FINISHED'}
    meta = bpy.context.active_object
    assert meta and meta.type == 'ARMATURE' and len(meta.data.bones) > 10
    assert any(p.rigify_type for p in meta.pose.bones), 'Metarig contains no rig component types'
    name = meta.name
    # Generate catches internal exceptions and can still return FINISHED. The
    # actual target rig, bones, constraints and widgets below are the acceptance.
    assert bpy.ops.pose.rigify_generate() == {'FINISHED'}
    meta = bpy.data.objects[name]
    rig = meta.data.rigify_target_rig
    assert rig is not None, 'Generate returned but created no target rig'
    state = _rig_state(bpy, name, rig.name)
    path = art / (prefix + '-generated.blend')
    assert bpy.ops.wm.save_as_mainfile(filepath=str(path), check_existing=False) == {'FINISHED'}
    (art / (prefix + '-rig-data.json')).write_text(json.dumps(state, indent=2), encoding='utf-8')
    print('RIGIFY_GENERATED_DATA', prefix, len(state['bones']), len(state['controls']), len(state['constraints']), flush=True)


def _reopen_and_compare(bpy, art, prefix):
    expected = json.loads((art / (prefix + '-rig-data.json')).read_text())
    path = art / (prefix + '-generated.blend')
    assert bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False) == {'FINISHED'}
    _require_available(bpy)
    observed = _rig_state(bpy, expected['metarig'], expected['rig'])
    assert json.loads(json.dumps(observed)) == expected, 'New process did not preserve rig bones, controls, constraints, widgets and metarig pointer'
    print('RIGIFY_REOPEN_EXACT_DATA', prefix, len(observed['bones']), len(observed['controls']), flush=True)


def _assert_no_duplicate_handlers(bpy):
    handlers = [(getattr(fn, '__module__', ''), getattr(fn, '__name__', ''))
                for fn in bpy.app.handlers.load_post
                if getattr(fn, '__module__', '').startswith('rigify')]
    assert len(handlers) == len(set(handlers)), ('Duplicate Rigify load handlers', handlers)
    assert sum(module.endswith('.utils.action_layers') and name == 'versioning_5_0'
               for module, name in handlers) == 1, ('Expected exactly one Rigify versioning_5_0 load handler', handlers)
    return handlers


def _seed_legacy_preferences(bpy, art):
    # This explicit enable is ONLY for manufacturing a legacy user fixture with
    # the old binary. New factory/lifecycle/reopen workers never call it.
    import addon_utils
    assert addon_utils.enable('rigify', default_set=True, persistent=True) is not None
    import rigify
    from rigify import feature_set_list
    feature_path = Path(feature_set_list.get_install_path(create=True)) / FEATURE_MODULE
    assert feature_path.resolve().is_relative_to(Path(os.environ['BLENDER_USER_SCRIPTS']).resolve())
    feature_path.mkdir(parents=True)
    module_source = '''import os
from pathlib import Path
rigify_info = {"name": "AxisMeld Disabled Fixture", "author": "AxisMeld Tests", "version": (1, 0, 0)}
def _trace(event):
    with Path(os.environ["AXISMELD_RIGIFY_FEATURE_TRACE"]).open("a", encoding="utf-8") as stream:
        stream.write(event + "\\n")
def register(): _trace("register")
def unregister(): _trace("unregister")
'''
    (feature_path / '__init__.py').write_text(module_source, encoding='utf-8')
    for name in ('rigs', 'metarigs'):
        (feature_path / name).mkdir()
        (feature_path / name / '__init__.py').write_text('', encoding='utf-8')
    importlib.invalidate_caches()
    prefs = rigify.RigifyPreferences.get_instance()
    prefs.refresh_installed_feature_sets()
    entry = next(fs for fs in prefs.rigify_feature_sets if fs.module_name == FEATURE_MODULE)
    entry.enabled = False
    assert FEATURE_MODULE not in feature_set_list.get_enabled_modules_names()
    assert bpy.ops.wm.save_userpref() == {'FINISHED'}
    userpref = Path(bpy.utils.user_resource('CONFIG')) / 'userpref.blend'
    assert userpref.is_file()
    data = dict(module=FEATURE_MODULE, enabled=False, userpref=str(userpref),
                userpref_sha256=hashlib.sha256(userpref.read_bytes()).hexdigest())
    (art / 'legacy-preferences.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    _generate_and_save(bpy, art, 'legacy')


def _assert_disabled_feature(bpy):
    import rigify
    from rigify import feature_set_list
    prefs = rigify.RigifyPreferences.get_instance()
    matches = [fs for fs in prefs.rigify_feature_sets if fs.module_name == FEATURE_MODULE]
    assert len(matches) == 1 and not matches[0].enabled, 'Legacy disabled Feature Set state was lost'
    assert FEATURE_MODULE not in feature_set_list.get_enabled_modules_names()
    trace = Path(os.environ['AXISMELD_RIGIFY_FEATURE_TRACE'])
    events = trace.read_text().splitlines() if trace.exists() else []
    assert 'register' not in events, ('Disabled Feature Set executed register', events)
    print('RIGIFY_DISABLED_FEATURE_STATE', json.dumps(events), flush=True)


def worker(bpy):
    art = Path(os.environ['AXISMELD_RIGIFY_ARTIFACTS'])
    case = os.environ['AXISMELD_RIGIFY_CASE']
    bpy.context.preferences.use_preferences_save = False
    snapshot = {
        'case': case,
        'pid': os.getpid(),
        'exe': bpy.app.binary_path,
        'exe_sha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest(),
        'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'operators': _availability(bpy),
        'rigify_pose_rna': hasattr(bpy.types.PoseBone, 'rigify_type'),
        'enabled_addons': sorted(bpy.context.preferences.addons.keys()),
        'config_path': bpy.utils.user_resource('CONFIG'),
        'scripts_path': bpy.utils.script_path_user(),
        'background': bpy.app.background,
    }
    loaded = sys.modules.get('rigify')
    if loaded is not None and getattr(loaded, '__file__', None):
        package = Path(loaded.__file__).resolve().parent
        resources = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(package.rglob('*.py'))}
        snapshot['loaded_package_path'] = str(package)
        snapshot['rigify_resources'] = resources
        snapshot['rigify_resource_fingerprint'] = hashlib.sha256(json.dumps(resources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (art / (case + '-startup.json')).write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
    print('RIGIFY_FACTORY_API', json.dumps(snapshot), flush=True)
    if case == 'legacy-seed':
        _seed_legacy_preferences(bpy, art)
    else:
        _require_available(bpy)
        _assert_no_duplicate_handlers(bpy)
        if case == 'generate':
            _generate_and_save(bpy, art, 'factory')
        elif case == 'reopen':
            _reopen_and_compare(bpy, art, 'factory')
        elif case == 'lifecycle':
            for iteration in range(2):
                bpy.utils.load_scripts(reload_scripts=True)
                _require_available(bpy)
                _assert_no_duplicate_handlers(bpy)
                assert bpy.ops.wm.read_factory_settings(use_empty=True) == {'FINISHED'}
                _require_available(bpy)
                _assert_no_duplicate_handlers(bpy)
                print('RIGIFY_PUBLIC_RELOAD_FACTORY_PASS', iteration, flush=True)
            assert bpy.ops.wm.read_factory_userpref() == {'FINISHED'}
            _require_available(bpy)
            _generate_and_save(bpy, art, 'lifecycle')
        elif case == 'legacy-load':
            _assert_disabled_feature(bpy)
            assert bpy.ops.wm.read_userpref() == {'FINISHED'}
            _require_available(bpy)
            _assert_disabled_feature(bpy)
            _reopen_and_compare(bpy, art, 'legacy')
            _assert_disabled_feature(bpy)
            expected = json.loads((art / 'legacy-preferences.json').read_text())
            assert hashlib.sha256(Path(expected['userpref']).read_bytes()).hexdigest() == expected['userpref_sha256'], 'Candidate silently rewrote the saved legacy preferences'
        else:
            assert case == 'factory', ('Unimplemented test case', case)
    print('AXISMELD_RIGIFY_' + case.upper().replace('-', '_') + '_PASS', flush=True)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', required=True)
    parser.add_argument('--artifacts', required=True)
    parser.add_argument('--case', choices=('factory', 'generate', 'reopen', 'lifecycle', 'legacy-seed', 'legacy-baseline', 'all'), default='all')
    parser.add_argument('--legacy-blender', help='Old candidate, only used to manufacture enabled legacy preferences')
    args = parser.parse_args()
    art = Path(args.artifacts).resolve()
    art.mkdir(parents=True, exist_ok=True)
    isolation = Path(tempfile.mkdtemp(prefix='isolated-', dir=art))
    startup = None
    if sys.platform == 'win32':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    (art / 'test-source.py').write_bytes(Path(__file__).read_bytes())
    if args.case == 'all':
        assert args.legacy_blender, '--all requires --legacy-blender to verify real legacy preferences'
        cases = [('factory', args.blender, 'clean'), ('generate', args.blender, 'clean'),
                 ('reopen', args.blender, 'clean'), ('lifecycle', args.blender, 'clean'),
                 ('legacy-seed', args.legacy_blender, 'legacy'), ('legacy-load', args.blender, 'legacy')]
    elif args.case == 'legacy-baseline':
        cases = [('legacy-seed', args.blender, 'legacy'), ('legacy-load', args.blender, 'legacy')]
    else:
        cases = [(args.case, args.blender, 'legacy' if args.case == 'legacy-seed' else 'clean')]
    results = []
    for case, binary, profile in cases:
        config, scripts, temporary = (isolation / profile / name for name in ('config', 'scripts', 'tmp'))
        for path in (config, scripts, temporary):
            path.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(BLENDER_USER_CONFIG=str(config), BLENDER_USER_SCRIPTS=str(scripts),
                   TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary),
                   AXISMELD_RIGIFY_ARTIFACTS=str(art), AXISMELD_RIGIFY_CASE=case,
                   AXISMELD_RIGIFY_FEATURE_TRACE=str(art / 'feature-register-trace.log'))
        command = [str(Path(binary).resolve()), '--background']
        if case != 'legacy-load':
            command.append('--factory-startup')
        command += ['--python-exit-code', '1', '--python', str(Path(__file__).resolve())]
        result = subprocess.run(command, env=env, startupinfo=startup, capture_output=True, timeout=180)
        (art / (case + '.stdout.log')).write_bytes(result.stdout)
        (art / (case + '.stderr.log')).write_bytes(result.stderr)
        marker = ('AXISMELD_RIGIFY_' + case.upper().replace('-', '_') + '_PASS').encode()
        passed = result.returncode == 0 and marker in result.stdout and b'Traceback (most recent call last):' not in result.stdout + result.stderr
        results.append(dict(case=case, status='PASS' if passed else 'FAIL', exit_code=result.returncode, command=command))
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        if not passed:
            break
    receipt = dict(status='PASS' if all(r['status'] == 'PASS' for r in results) else 'FAIL',
                   exit_code=0 if all(r['status'] == 'PASS' for r in results) else results[-1]['exit_code'] or 1,
                   processes=results, isolation=str(isolation), artifacts=str(art),
                   test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (art / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    raise SystemExit(receipt['exit_code'])


if __name__ == '__main__':
    try:
        import bpy
    except ImportError:
        run()
    else:
        try:
            worker(bpy)
        except BaseException:
            traceback.print_exc()
            raise

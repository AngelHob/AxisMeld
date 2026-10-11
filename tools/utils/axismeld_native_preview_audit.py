# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only full native AxisMeld install audit; only --report is written.

candidate: compare live checkout, report packaging cleanup, no manifest required.
staging/extract: require a complete manifest, compare committed source, reject
personal/build files. Does not launch Blender, package files, or prove a rebuild.
Python 3.11+; standard library only. Do not write the report into the installation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

INTEGRATION = '''scripts/addons_core/bl_pkg/bl_extension_ui.py
scripts/modules/addon_utils.py
scripts/presets/keyconfig/AxisMeld_Maya_2026.py
scripts/startup/bl_operators/axismeld.py
scripts/startup/bl_ui/__init__.py
scripts/startup/bl_ui/properties_data_mesh.py
scripts/startup/bl_ui/space_axismeld_menubar.py
scripts/startup/bl_ui/space_axismeld_native_modeling.py
scripts/startup/bl_ui/space_axismeld_native_rigging.py
scripts/startup/bl_ui/space_image.py
scripts/startup/bl_ui/space_topbar.py
scripts/startup/bl_ui/space_userpref.py
scripts/startup/bl_ui/space_view3d.py
scripts/startup/rigify_builtin.py'''.splitlines()
MODULES = ('scripts/modules/axismeld/', 'scripts/modules/rigify/')
# Exact upstream bytes already reviewed by the fixed 2026.09.17 release audit.
EXAMPLES = {
    '5.3/python/lib/site-packages/Cython/Debugger/libpython.py': 'b5747b0de5dac5d15c12af53365db5269cae7393b3bff0c91ee4a020ae737263',
    '5.3/python/lib/site-packages/mesonbuild/dependencies/pkgconfig.py': '6af545b0dd5619cf0994af6d83ac6e1986556a09eafa707d0ce9d0207e13f2b6',
    '5.3/python/lib/site-packages/numpy/lib/_datasource.py': '72c15f3952f4d15efa28cfbecfdc113802261c33c1e65e5bfbc875009962e777',
    '5.3/python/lib/site-packages/pip/_internal/utils/urls.py': '8d46659f0ca5d0ba7db3b60cc98e8be97e0dc55a4cd079f49fe3236ab2d497e8',
    '5.3/python/lib/site-packages/setuptools/_distutils/tests/test_dir_util.py': '618e30600c36f444a1255e9d17a9065ee86f23dc229f14f8a9ac77245e4aaa18',
    '5.3/python/lib/site-packages/setuptools/_distutils/tests/test_util.py': 'a91b897ef3eaa97274c29eb60968ef623ac30a55e4728cbab00fbef85869d760',
}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe(path):
    value = PurePosixPath(path)
    return (bool(path) and not value.is_absolute() and '..' not in value.parts and
            not any(c in path for c in ('\\', ':', '\n', '\r')) and str(value) == path)


def git(repo, *args, data=None):
    return subprocess.run(['git', '-C', str(repo), *args], input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def blobs(repo, revision, paths):
    ordered = sorted(paths)
    requests = ''.join(revision + ':' + p + '\n' for p in ordered).encode()
    output = git(repo, 'cat-file', '--batch', data=requests)
    result, offset = {}, 0
    for path in ordered:
        end = output.index(b'\n', offset)
        header = output[offset:end].split()
        need(len(header) == 3 and header[1] == b'blob', 'Missing source blob: ' + path)
        size = int(header[2])
        start = end + 1
        need(output[start + size:start + size + 1] == b'\n', 'Truncated source blob: ' + path)
        result[path] = output[start:start + size]
        offset = start + size + 1
    need(offset == len(output), 'Unexpected trailing Git output')
    return result


def file_map(value, label):
    if isinstance(value, dict):
        rows = [{'path': p, 'sha256': d} if isinstance(d, str) else dict(d, path=p)
                for p, d in value.items()]
    else:
        need(isinstance(value, list), label + ' must be an array or mapping')
        rows = value
    result = {}
    for row in rows:
        path = row['path']
        need(safe(path) and path not in result, label + ' invalid/duplicate path')
        need(re.fullmatch('[a-f0-9]{64}', row['sha256']) is not None,
             label + ' invalid digest: ' + path)
        result[path] = row
    need(len(result) == len({p.casefold() for p in result}), label + ' case collision')
    return result


def audit(args):
    root, repo = args.install.resolve(), args.repo.resolve()
    need(root.is_dir(), 'Install directory missing')
    need(not args.report.resolve().is_relative_to(root), 'Report must be outside install')
    strict = args.phase != 'candidate'
    files = {}
    for path in root.rglob('*'):
        info = path.lstat()
        need(not path.is_symlink() and not (getattr(info, 'st_file_attributes', 0) & 0x400),
             'Symlink or reparse point: ' + path.relative_to(root).as_posix())
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            need(safe(rel), 'Unsafe relative path')
            files[rel] = path
    need(len(files) == len({p.casefold() for p in files}), 'Case-colliding files')
    versions = [p for p in root.iterdir() if (p / 'scripts/modules').is_dir()]
    need(len(versions) == 1, 'Require exactly one versioned runtime')
    version = versions[0]
    for rel in ('blender.exe', 'blender-launcher.exe', 'ucrtbase.dll',
                'portable/README.txt', version.name + '/python/bin/python.exe'):
        need(rel in files and files[rel].stat().st_size > 0, 'Missing runtime: ' + rel)
    for rel in ('blender.exe', 'blender-launcher.exe', 'ucrtbase.dll'):
        with files[rel].open('rb') as stream:
            need(stream.read(2) == b'MZ', 'Not a PE executable: ' + rel)
    need(not (version / 'scripts/addons_core/rigify').exists(), 'Old Rigify addon present')
    cleanup, personal = [], []
    for rel in files:
        low = rel.lower()
        parts, name = PurePosixPath(low).parts, PurePosixPath(low).name
        if not strict and low == 'portable/.gitignore':
            need(files[rel].read_bytes() == (repo / 'release/datafiles/axismeld/portable/.gitignore').read_bytes(),
                 'Unexpected portable/.gitignore contents')
            cleanup.append(rel)
            continue
        if '__pycache__' in parts or low.endswith(('.pyc', '.pyo', '.pdb', '.lib', '.exp')):
            cleanup.append(rel)
        if (set(parts) & {'.git', '.codex', '.cache', '.ssh', '.aws', 'appdata'} or
                name in {'userpref.blend', 'bookmarks.txt', 'recent-files.txt', '.git-credentials',
                         '.env', 'id_rsa', 'id_ed25519', 'credentials.json'} or
                low.endswith(('.log', '.crash.txt', '-receipt.json', '-acceptance.json', '-probe.json')) or
                (low.startswith('portable/') and low != 'portable/readme.txt') or
                (name == 'startup.blend' and not low.startswith(
                    version.name + '/scripts/startup/bl_app_templates_system/'))):
            personal.append(rel)
    need(not personal, 'Personal/test files present: ' + ', '.join(personal))
    if strict:
        need(not cleanup, 'Build/cache files present: ' + ', '.join(cleanup))
    assemblies = {}
    for assembly in ('blender.crt', 'blender.shared'):
        rel = assembly + '/' + assembly + '.manifest'
        need(rel in files, 'Missing assembly manifest: ' + rel)
        tree = ET.parse(files[rel]).getroot()
        identities = tree.findall('{*}assemblyIdentity')
        need(len(identities) == 1 and identities[0].get('name') == assembly,
             'Wrong assembly identity: ' + rel)
        names = [entry.get('name', '') for entry in tree.findall('{*}file')]
        need(names and len(names) == len(set(names)), 'Missing/duplicate assembly files: ' + rel)
        members = {}
        for name in names:
            need(safe(name), 'Unsafe assembly member')
            member = assembly + '/' + name
            need(member in files and files[member].stat().st_size > 0,
                 'Missing assembly DLL: ' + member)
            with files[member].open('rb') as stream:
                need(stream.read(2) == b'MZ', 'Invalid assembly DLL: ' + member)
            members[name] = digest(files[member])
        assemblies[assembly] = {'manifest_sha256': digest(files[rel]), 'members': members}

    manifest_path = root / 'AxisMeld-build.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig')) if manifest_path.exists() else None
    need(not strict or manifest is not None, 'Formal package requires AxisMeld-build.json')
    revision = manifest.get('sourceCommit') if manifest else None
    if strict:
        for key in ('sourceCommit', 'nativeSourceCommit'):
            value = manifest.get(key, '')
            need(re.fullmatch('[a-f0-9]{40}', value) is not None, 'Invalid ' + key)
            git(repo, 'cat-file', '-e', value + '^{commit}')
        need(manifest['sourceCommit'] == manifest['nativeSourceCommit'],
             'This full-native audit requires sourceCommit == nativeSourceCommit')
        need(manifest.get('source') == 'https://github.com/AngelHob/AxisMeld/tree/' + revision,
             'Source URL/revision mismatch')
    source_paths = set(INTEGRATION) | set(args.extra_resource)
    if strict:
        tracked = git(repo, 'ls-tree', '-r', '--name-only', revision, '--',
                      'scripts/modules/axismeld', 'scripts/modules/rigify', 'release/license').decode().splitlines()
        module_paths = {p for p in tracked if p.startswith(MODULES)}
        license_paths = {p for p in tracked if p.startswith('release/license/')}
    else:
        module_paths = {p.relative_to(repo).as_posix() for folder in MODULES
                        for p in (repo / folder).rglob('*') if p.is_file()
                        and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
        license_paths = {p.relative_to(repo).as_posix() for p in (repo / 'release/license').rglob('*') if p.is_file()}
    installed_modules = {rel.removeprefix(version.name + '/') for rel in files
                         if rel.startswith(tuple(version.name + '/' + p for p in MODULES))
                         and rel not in cleanup}
    need(installed_modules == module_paths, 'Managed module file set differs from source: ' +
         json.dumps({'missing': sorted(module_paths - installed_modules),
                     'extra': sorted(installed_modules - module_paths)}))
    source_paths.update(p for p in module_paths if p.endswith('.py'))
    module_assets = module_paths - source_paths
    declared = file_map(manifest['resources'], 'resources') if manifest else {}
    if strict:
        need(source_paths <= declared.keys(), 'Manifest omits selected source resources')
    source_paths.update(declared)
    need(all(safe(p) and p.startswith('scripts/') and p.endswith('.py') for p in source_paths),
         'Invalid selected resource')
    asset = 'release/datafiles/startup.blend'
    marker = 'release/datafiles/axismeld/portable/README.txt'
    wanted = source_paths | module_assets | license_paths | {'COPYING', asset, marker}
    sources = blobs(repo, revision, wanted) if strict else {p: (repo / p).read_bytes() for p in wanted}
    for path in sorted(module_assets):
        need((version / path).read_bytes() == sources[path], 'Module asset source mismatch: ' + path)
    rows, newline_only = [], []
    for path in sorted(source_paths):
        installed = version / path
        need(installed.is_file(), 'Missing selected resource: ' + path)
        actual, source = installed.read_bytes(), sources[path]
        need(not source.startswith(b'version https://git-lfs.github.com/spec/v1'), 'Source LFS pointer: ' + path)
        need(actual.replace(b'\r\n', b'\n') == source.replace(b'\r\n', b'\n'),
             'Source mismatch: ' + path)
        if actual != source:
            newline_only.append(path)
        value = sha(actual)
        if path in declared:
            need(value == declared[path]['sha256'], 'Manifest resource mismatch: ' + path)
        rows.append({'path': path, 'sha256': value})
    resource_hashes = {r['path']: r['sha256'] for r in rows}
    fingerprint = sha(json.dumps(resource_hashes, sort_keys=True, separators=(',', ':')).encode())
    if manifest:
        need(manifest.get('resourceFingerprint') == fingerprint, 'Resource fingerprint mismatch')
    licenses = {}
    for path in sorted(license_paths | {'COPYING'}):
        rel = 'copying.txt' if path == 'COPYING' else path.removeprefix('release/')
        if not strict and rel == 'copying.txt' and rel not in files:
            cleanup.append('ADD copying.txt FROM source COPYING')
            continue
        need(rel in files, 'Missing license: ' + rel)
        actual = files[rel].read_bytes()
        need(actual.replace(b'\r\n', b'\n') == sources[path].replace(b'\r\n', b'\n'),
             'License source mismatch: ' + rel)
        licenses[rel] = sha(actual)
    need(files['portable/README.txt'].read_bytes().replace(b'\r\n', b'\n') ==
         sources[marker].replace(b'\r\n', b'\n'), 'Portable marker mismatch')
    need(not sources[asset].startswith(b'version https://git-lfs.github.com/spec/v1'),
         'Expected actual ordinary Git startup asset, not an LFS pointer')
    binary_sha = digest(files['blender.exe'])
    if manifest:
        need(manifest.get('binarySha256') == binary_sha, 'Manifest binary mismatch')
        embedded = file_map(manifest.get('embeddedSourceAssets', []), 'embeddedSourceAssets')
        need(asset in embedded and embedded[asset]['sha256'] == sha(sources[asset]),
             'Embedded source asset manifest mismatch')
    file_hashes = {}
    if strict:
        declared_files = file_map(manifest.get('files', []), 'files')
        need(set(declared_files) == set(files) - {'AxisMeld-build.json'},
             'Full manifest file set differs from installation')
        for rel, row in declared_files.items():
            file_hashes[rel] = digest(files[rel])
            need(file_hashes[rel] == row['sha256'], 'File digest mismatch: ' + rel)
            if 'size' in row:
                need(row['size'] == files[rel].stat().st_size, 'File size mismatch: ' + rel)

    profile = re.compile(r'(?<![A-Za-z0-9_./])(?:[A-Za-z]:[/\\]+Users[/\\]+|/home/|/Users/)([^/\\\s\"<>]+)', re.I)
    private_site = re.compile(r'https?://[^/\s]+\.chatgpt\.site', re.I)
    placeholders = {'user', 'username', 'yourname', 'your_username', 'example', 'public', 'default', '...'}
    matches, examples, scanned = [], [], 0
    for rel, path in files.items():
        if path.suffix.lower() not in {'.py', '.txt', '.md', '.json', '.cmd', '.bat', '.toml', '.ini', '.html'}:
            continue
        raw = path.read_bytes()
        encoding = ('utf-32' if raw.startswith((b'\xff\xfe\x00\x00', b'\x00\x00\xfe\xff')) else
                    'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
        try:
            content = raw.decode(encoding)
        except UnicodeDecodeError:
            raise ValueError('Unscannable text file: ' + rel) from None
        scanned += 1
        found = [m for m in profile.finditer(content) if m[1].lower() not in placeholders
                 and not m[1].startswith(('$', '{', '%'))]
        if found and EXAMPLES.get(rel) == sha(raw):
            examples.append(rel)
            found = []
        sites = len(private_site.findall(content))
        if found or sites:
            matches.append({'path': rel, 'profile_path_count': len(found), 'private_site_count': sites})
    need(not matches, 'Private text patterns (contents suppressed): ' + json.dumps(matches))
    archive = None
    if args.archive:
        need(strict, '--archive requires staging/extract mode')
        archive_sha = digest(args.archive)
        sidecar = Path(str(args.archive) + '.sha256').read_text(encoding='utf-8-sig').strip().split()
        need(sidecar == [archive_sha, args.archive.name], 'Archive sidecar mismatch')
        with zipfile.ZipFile(args.archive) as z:
            entries = z.infolist()
            # A file and a directory with its name cannot coexist on extraction.
            names = [i.filename[:-1] if i.is_dir() else i.filename for i in entries]
            need(len(names) == len(set(names)) == len({n.casefold() for n in names}), 'ZIP path collision')
            file_names = {name.casefold() for name, entry in zip(names, entries) if not entry.is_dir()}
            for name in names:
                need(not any(str(parent).casefold() in file_names for parent in PurePosixPath(name).parents),
                     'ZIP file is an ancestor of another entry')
            prefix = args.archive_prefix.rstrip('/') + '/'
            archive_files = {}
            for name, entry in zip(names, entries):
                need(safe(name) and (name == prefix[:-1] or name.startswith(prefix)), 'Unsafe ZIP path')
                need(not stat.S_ISLNK(entry.external_attr >> 16), 'ZIP symlink')
                if entry.is_dir():
                    continue
                rel = entry.filename[len(prefix):]
                need(rel in files, 'Unexpected ZIP file: ' + rel)
                with z.open(entry) as stream:
                    archive_files[rel] = hashlib.file_digest(stream, 'sha256').hexdigest()
                expected = file_hashes[rel] if rel in file_hashes else digest(files[rel])
                need(archive_files[rel] == expected, 'ZIP/install mismatch: ' + rel)
            need(set(archive_files) == set(files), 'ZIP/install file set mismatch')
        archive = {'name': args.archive.name, 'sha256': archive_sha, 'files': len(archive_files)}
    return {'schema_version': 1, 'status': 'PASS', 'phase': args.phase,
            'audit_utc': datetime.now(timezone.utc).isoformat(), 'source_commit': revision,
            'binary_sha256': binary_sha, 'version_directory': version.name, 'files_count': len(files),
            'assemblies': assemblies, 'licenses': licenses, 'resources': rows,
            'resource_fingerprint': fingerprint, 'newline_only_resources': newline_only,
            'startup_source_sha256': sha(sources[asset]), 'staging_todo': cleanup,
            'manifest_sha256': digest(manifest_path) if manifest else None,
            'privacy': {'text_files_scanned': scanned, 'reviewed_exact_examples': examples},
            'archive': archive,
            'scope': 'Static integrity only. No binary/source reproducibility, embedded manifest extraction, '
                     'factory startup, actual portable behavior, GUI, GPU or other-machine validation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--phase', choices=('candidate', 'staging', 'extract'), required=True)
    parser.add_argument('--extra-resource', action='append', default=[])
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--archive-prefix', default='AxisMeld-Preview')
    args = parser.parse_args()
    try:
        result = audit(args)
    except Exception as exc:
        # Only print explicitly constructed validation messages, not subprocess
        # stderr or file contents which can contain private paths or credentials.
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(json.dumps({'status': 'FAIL', 'reason': reason}, ensure_ascii=False))
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'phase': args.phase, 'binary_sha256': result['binary_sha256'],
                      'resources': len(result['resources']), 'files': result['files_count'],
                      'staging_todo_count': len(result['staging_todo']),
                      'report': str(args.report)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

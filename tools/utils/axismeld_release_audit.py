# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify only the published 2026-09-17 Rigging preview, without launching Blender.

Requires its ZIP plus the adjacent .sha256 sidecar and the source checkout.
The public handoff snapshot pins the release; this is not a validator for a new
custom build. Reports contain checks and hashes, without copying runtime user data.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = 'docs/compatibility/2026-09-17-handoff-snapshot.json'
RELEASE_TAG = 'axismeld-2026.09.17-rigging-preview'
PREFIX = 'AxisMeld-Preview/'

# Reviewed upstream examples/tests contain literal sample home paths. Exempt only
# these exact vendored bytes, never a user's name or a whole dependency directory.
PROFILE_EXAMPLE_FILES = {
    '5.3/python/lib/site-packages/Cython/Debugger/libpython.py':
        'b5747b0de5dac5d15c12af53365db5269cae7393b3bff0c91ee4a020ae737263',
    '5.3/python/lib/site-packages/mesonbuild/dependencies/pkgconfig.py':
        '6af545b0dd5619cf0994af6d83ac6e1986556a09eafa707d0ce9d0207e13f2b6',
    '5.3/python/lib/site-packages/numpy/lib/_datasource.py':
        '72c15f3952f4d15efa28cfbecfdc113802261c33c1e65e5bfbc875009962e777',
    '5.3/python/lib/site-packages/pip/_internal/utils/urls.py':
        '8d46659f0ca5d0ba7db3b60cc98e8be97e0dc55a4cd079f49fe3236ab2d497e8',
    '5.3/python/lib/site-packages/setuptools/_distutils/tests/test_dir_util.py':
        '618e30600c36f444a1255e9d17a9065ee86f23dc229f14f8a9ac77245e4aaa18',
    '5.3/python/lib/site-packages/setuptools/_distutils/tests/test_util.py':
        'a91b897ef3eaa97274c29eb60968ef623ac30a55e4728cbab00fbef85869d760',
}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(value, message):
    if not value:
        raise AssertionError(message)


def safe_names(z):
    names = z.namelist()
    check(len(names) == len(set(names)), 'Duplicate ZIP entries')
    check(len(names) == len({name.casefold() for name in names}), 'Case-insensitive ZIP path collision')
    for item in z.infolist():
        name = item.filename
        parts = PurePosixPath(name).parts
        check(name.startswith(PREFIX) and '\\' not in name and ':' not in name and
              '..' not in parts and not PurePosixPath(name).is_absolute() and
              str(PurePosixPath(name)) == name.rstrip('/'), 'Unsafe ZIP path: ' + name)
        check(not stat.S_ISLNK(item.external_attr >> 16), 'ZIP symlink: ' + name)
    return names


def audit(archive, repo=REPO):
    archive, repo = Path(archive), Path(repo)
    snapshot = json.loads((repo / SNAPSHOT).read_text(encoding='utf-8'))
    expected = snapshot['release']
    check(expected['tag'] == RELEASE_TAG, 'Snapshot is not the supported fixed release')
    check(archive.name == expected['archive_name'], 'Use the canonical published archive filename')
    check(archive.stat().st_size == expected['archive_bytes'], 'Archive byte size differs from published snapshot')
    archive_sha = sha_file(archive)
    check(archive_sha == expected['archive_sha256'], 'Archive SHA256 differs from published snapshot')
    sidecar = Path(str(archive) + '.sha256').read_text(encoding='ascii').strip().split()
    check(sidecar == [archive_sha, archive.name], 'Archive SHA256 sidecar mismatch')
    with zipfile.ZipFile(archive) as z:
        names = safe_names(z)
        check(z.testzip() is None, 'ZIP CRC failure')
        check(len(names) == expected['archive_entries'], 'Archive entry count differs from published snapshot')
        def read(path):
            try:
                return z.read(PREFIX + path)
            except KeyError as error:
                raise AssertionError('Missing required archive member: ' + path) from error
        manifest_bytes = read('AxisMeld-build.json')
        check(sha_bytes(manifest_bytes) == expected['manifest_sha256'], 'Published manifest digest mismatch')
        manifest = json.loads(manifest_bytes)
        commit = manifest['sourceCommit']
        check(re.fullmatch('[a-f0-9]{40}', commit), 'Invalid source commit')
        check(commit == snapshot['pins']['release_source_commit'], 'Manifest source commit differs from fixed release')
        check(manifest['buildId'] == RELEASE_TAG, 'Wrong release build ID')
        check(manifest['source'] == 'https://github.com/AngelHob/AxisMeld/tree/' + commit,
              'Source URL/commit mismatch')

        def git(*args):
            return subprocess.check_output(['git', '-C', str(repo), *args])

        git('cat-file', '-e', commit + '^{commit}')
        resources = manifest['resources']
        resource_map = {item['path']: item['sha256'] for item in resources}
        check(len(resources) == len(resource_map) == expected['resource_count'] == 139, 'Expected exactly 139 unique resources')
        check(all(path.startswith('scripts/') and '..' not in PurePosixPath(path).parts
                  for path in resource_map), 'Invalid resource source path')
        fingerprint = sha_bytes(json.dumps(resource_map, sort_keys=True, separators=(',', ':')).encode())
        check(fingerprint == manifest['resourceFingerprint'] == expected['resource_fingerprint'], 'Resource fingerprint mismatch')
        source_comparison = {'byte_identical': 0, 'newline_only': 0, 'resources_verified': 0}
        for path, expected_digest in resource_map.items():
            data = read('5.3/' + path)
            check(sha_bytes(data) == expected_digest, 'Resource digest mismatch: ' + path)
            source = git('show', commit + ':' + path)
            if data == source:
                source_comparison['byte_identical'] += 1
            else:
                check(data.decode('utf-8').replace('\r\n', '\n') ==
                      source.decode('utf-8').replace('\r\n', '\n'), 'Committed source mismatch: ' + path)
                source_comparison['newline_only'] += 1
            source_comparison['resources_verified'] += 1

        binary_sha = sha_bytes(read('blender.exe'))
        check(binary_sha == manifest['binarySha256'] == expected['binary_sha256'], 'Executable fingerprint mismatch')
        assets = manifest['embeddedSourceAssets']
        check(len(assets) == 1 and assets[0]['path'] == 'release/datafiles/startup.blend',
              'Expected one embedded startup source asset')
        asset = assets[0]
        asset_blob = git('show', commit + ':' + asset['path'])
        if asset_blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            pointer = asset_blob.decode('ascii')
            oid = re.search(r'^oid sha256:([a-f0-9]{64})$', pointer, re.M)
            size = re.search(r'^size ([0-9]+)$', pointer, re.M)
            check(oid and size and oid[1] == asset['sha256'], 'Startup LFS OID/manifest mismatch')
            common = Path(git('rev-parse', '--git-common-dir').decode().strip())
            if not common.is_absolute():
                common = repo / common
            object_path = common / 'lfs/objects' / oid[1][:2] / oid[1][2:4] / oid[1]
            asset_content = object_path.read_bytes()
            check(len(asset_content) == int(size[1]) and sha_bytes(asset_content) == oid[1],
                  'Startup LFS object content/size mismatch')
            asset_storage = 'git_lfs'
        else:
            asset_content = asset_blob
            check(sha_bytes(asset_content) == asset['sha256'], 'Startup Git binary blob/manifest mismatch')
            asset_storage = 'git_blob'
        # The runtime check separately proves the executable actually loads the new embedded workspace.
        check(asset['sha256'] == expected['embedded_startup']['sha256'] and
              len(asset_content) == expected['embedded_startup']['byte_size'] and
              asset_storage == expected['embedded_startup']['storage_kind'],
              'Startup content/storage differs from published snapshot')

        rigify_prefix = 'scripts/modules/rigify/'
        source_rigify = set(git('ls-tree', '-r', '--name-only', commit, 'scripts/modules/rigify').decode().splitlines())
        packaged_rigify = {name[len(PREFIX + '5.3/'):] for name in names
                          if name.startswith(PREFIX + '5.3/' + rigify_prefix) and not name.endswith('/')}
        check(len(source_rigify) == expected['rigify_file_count'] == 88 and packaged_rigify == source_rigify, 'Rigify source/package file set mismatch')
        check(source_rigify <= resource_map.keys(), 'Rigify files missing from manifest')
        check(not any('/addons_core/rigify/' in name or '/addons/rigify/' in name for name in names),
              'Old Rigify addon package is present')

        licenses = {}
        for packaged, source_path in (
                ('copying.txt', 'COPYING'), ('license/license.md', 'release/license/license.md'),
                ('license/spdx/GPL-2.0-or-later.txt', 'release/license/spdx/GPL-2.0-or-later.txt'),
                ('license/spdx/GPL-3.0-or-later.txt', 'release/license/spdx/GPL-3.0-or-later.txt')):
            data, source = read(packaged), git('show', commit + ':' + source_path)
            check(data.replace(b'\r\n', b'\n') == source.replace(b'\r\n', b'\n'), 'License mismatch: ' + packaged)
            licenses[packaged] = sha_bytes(data)

        unexpected, text_matches, reviewed_examples = [], [], []
        text_count = 0
        profile_path = re.compile(r'(?<![A-Za-z0-9_./])(?:[A-Za-z]:[/\\]+Users[/\\]+|/home/|/Users/)([^/\\\s\"<>]+)', re.I)
        private_site = re.compile(r'https?://[^/\s]+\.chatgpt\.site', re.I)
        template_users = {'user', 'username', 'yourname', 'your_username', 'example', 'public', 'default', '...'}
        for name in names:
            rel = name[len(PREFIX):]
            lower = rel.lower()
            parts = PurePosixPath(lower).parts
            if ('__pycache__' in parts or '.git' in parts or '.codex' in parts or '.cache' in parts or
                    'appdata' in parts or '.ssh' in parts or '.aws' in parts or
                    lower.endswith(('.pyc', '.pdb', '.lib', '.exp', '.log', '.crash.txt')) or
                    PurePosixPath(lower).name in {'userpref.blend', 'bookmarks.txt', 'recent-files.txt', '.git-credentials', '.env',
                                                   'id_rsa', 'id_ed25519', 'credentials.json'} or
                    (lower.startswith('portable/') and lower != 'portable/readme.txt') or
                    ('startup.blend' in lower and not lower.startswith('5.3/scripts/startup/bl_app_templates_system/')) or
                    lower.endswith(('-receipt.json', '-acceptance.json', '-probe.json'))):
                unexpected.append(rel)
            if PurePosixPath(lower).suffix in {'.py', '.txt', '.md', '.json', '.cmd', '.bat', '.toml', '.ini'}:
                data = read(rel)
                try:
                    content = data.decode('utf-8-sig')
                except UnicodeDecodeError:
                    continue
                text_count += 1
                found = [match for match in profile_path.finditer(content)
                         if match[1].lower() not in template_users and not match[1].startswith(('$', '{', '%'))]
                if found and PROFILE_EXAMPLE_FILES.get(rel) == sha_bytes(data):
                    reviewed_examples.append({'path': rel, 'profile_path_count': len(found), 'sha256': sha_bytes(data)})
                    found = []
                private_site_count = len(private_site.findall(content))
                if found or private_site_count:
                    text_matches.append({'path': rel, 'profile_path_count': len(found),
                                         'private_site_count': private_site_count})
        check(not unexpected, 'Unexpected personal/test paths: ' + repr(unexpected))
        check(not text_matches, 'Private local/site strings detected: ' + repr(text_matches))
        return dict(schema_version=1, status='PASS', audit_utc=datetime.now(timezone.utc).isoformat(),
                    snapshot=SNAPSHOT, source_commit=commit, archive=dict(path=str(archive), bytes=archive.stat().st_size,
                    entries=len(names), sha256=archive_sha), manifest=dict(sha256=sha_bytes(manifest_bytes),
                    resources=len(resources), resource_fingerprint=fingerprint), binary_sha256=binary_sha,
                    startup_asset=dict(path=asset['path'], sha256=sha_bytes(asset_content),
                                       storage_kind=asset_storage, byte_size=len(asset_content)),
                    source_comparison=source_comparison, rigify_files=len(source_rigify), licenses=licenses,
                    privacy=dict(text_files_scanned=text_count, unexpected_paths=unexpected, text_matches=text_matches,
                                 reviewed_upstream_examples=reviewed_examples),
                    scope='Read-only ZIP, committed source and startup content (Git blob or verified LFS object), '
                    'final build fingerprints and license checks. '
                    'Embedded startup execution is verified separately; binary hash is not reproducible-build proof.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.archive, args.repo)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()

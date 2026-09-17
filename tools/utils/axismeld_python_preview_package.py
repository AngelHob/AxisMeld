# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Assemble a Python-only preview from the fixed 2026-09-17 Rigging release.

Requires Python 3.11+, Git history, the canonical base ZIP and its .sha256 sidecar.
Commit the desired source first: only HEAD blobs, never working-tree files, are
packaged. The caller must verify a clean source tree and test the extracted new
package before publishing. This tool neither builds native code nor publishes.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import zipfile


NATIVE_SOURCE_COMMIT = '617986ac184125fe2169456bdb525965530ea736'
BASE_ARCHIVE_SHA256 = '869c54a60c6a7ef68831389acef2ec34a56467e7aeaa8236d5dee354d57e4a73'
PREFIX = 'AxisMeld-Preview/'
VERSION = '5.3/'
MANIFEST = PREFIX + 'AxisMeld-build.json'
NOTES = PREFIX + 'AxisMeld-Skin-Weights.txt'
START_HERE = PREFIX + 'AxisMeld-START-HERE.txt'
SKIN_USAGE = '''Skin 权重整理 / Skin Weights

1. Rigging 工作区的 Skin > Normalize Weights 和 Skin > Prune Small Weights
   提供一次性权重整理；正文按默认参数执行，右侧 Options 齿轮打开独立参数对话框。
2. 仅处理活动且已选择的可编辑、非共享网格，需恰好一个有效 Armature Modifier。
   仅处理该骨架的变形骨同名顶点组；其他对象、非骨骼组及永久锁定组保持不变。
   对象模式处理未隐藏顶点；编辑模式和权重绘制遮罩遵循当前选择，不隐式全选。
3. Normalize Weights 保留锁定权重，可额外 Lock Active；全零顶点不自动补权。
   Prune Small Weights 默认阈值 0.01，仅删除严格小于阈值的未锁权重，等于阈值保留。
   Keep Strongest 和 Normalize After 默认开启，可在 Options 中调整。
4. 打开或取消 Options 不改权重，确认才执行；每次有效操作可一次 Undo。
   F9 调整上次操作仅适用于 Blender 默认键位；Maya 键位仍用
   Edit > Adjust Last Operation，F9 保留原 Vertex 映射。
5. 这是有明确范围的 Blender 数据适配，不代表 Maya 的全部 Skin 算法或持续归一化模式。
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(repo, *args, input_bytes=None):
    return subprocess.run(['git', '-C', str(repo), *args], input=input_bytes,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def script_path(path):
    parts = PurePosixPath(path).parts
    return (path.startswith('scripts/') and path.endswith('.py') and
            '\\' not in path and ':' not in path and '\n' not in path and '\r' not in path and
            '..' not in parts and str(PurePosixPath(path)) == path and '__pycache__' not in parts)


def committed_resources(repo, head, base_paths):
    """Read only explicitly listed scripts plus committed AxisMeld Python files."""
    tree = {}
    for record in git(repo, 'ls-tree', '-r', '-z', head, '--', 'scripts').split(b'\0'):
        if record:
            metadata, path = record.split(b'\t', 1)
            tree[path.decode('utf-8')] = metadata.split()
    paths = set(base_paths)
    if len(paths) != len(base_paths) or not all(script_path(path) for path in paths):
        raise ValueError('Invalid or duplicate baseline resource paths')
    paths.update(path for path in tree if path.startswith('scripts/modules/axismeld/') and script_path(path))
    for path in sorted(paths):
        if path not in tree:
            raise ValueError('Missing committed resource: ' + path)
        mode, kind, _oid = tree[path]
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise ValueError('Resource must be a committed regular file: ' + path)
    ordered = sorted(paths)
    requests = ''.join(head + ':' + path + '\n' for path in ordered).encode('utf-8')
    content = git(repo, 'cat-file', '--batch', input_bytes=requests)
    resources = {}
    offset = 0
    for path in ordered:
        end = content.index(b'\n', offset)
        _oid, kind, raw_size = content[offset:end].split()
        if kind != b'blob':
            raise ValueError('Expected committed blob: ' + path)
        size = int(raw_size)
        start = end + 1
        data = content[start:start + size]
        if len(data) != size or content[start + size:start + size + 1] != b'\n':
            raise ValueError('Incomplete Git blob: ' + path)
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise ValueError('LFS pointer is not an installed Python resource: ' + path)
        resources[path] = data
        offset = start + size + 1
    if offset != len(content):
        raise ValueError('Unexpected extra Git blob response')
    return resources


def validate_source_changes(repo, base_commit, head, resource_paths):
    git(repo, 'merge-base', '--is-ancestor', base_commit, head)
    paths = [p.decode('utf-8') for p in git(
        repo, 'diff', '--no-renames', '--ignore-submodules=none', '--name-only', '-z',
        base_commit, head, '--').split(b'\0') if p]
    documents = {'README', 'README.md', 'AGENTS.md', '.github/README.md'}
    rejected = [path for path in paths if not (
        path in resource_paths or path in documents or
        path.startswith(('docs/', 'tests/', 'tools/')))]
    if rejected:
        raise ValueError('Unsupported source changes require a new native/full installation: ' + ', '.join(rejected))
    return paths


def check_archive_entries(source):
    names = source.namelist()
    if len(names) != len(set(names)) or len(names) != len({name.casefold() for name in names}):
        raise ValueError('Duplicate or case-colliding base ZIP entries')
    for item in source.infolist():
        name = item.filename
        parts = PurePosixPath(name).parts
        if (not name.startswith(PREFIX) or '\\' in name or ':' in name or '..' in parts or
                str(PurePosixPath(name)) != name.rstrip('/') or stat.S_ISLNK(item.external_attr >> 16)):
            raise ValueError('Unsafe base ZIP path: ' + name)
        lower = name.lower()
        if ('__pycache__' in parts or lower.endswith('.pyc') or
                (lower.startswith(PREFIX.lower() + 'portable/') and
                 lower != PREFIX.lower() + 'portable/readme.txt' and not item.is_dir())):
            raise ValueError('Runtime cache or personal portable data in base ZIP: ' + name)


def refresh_start_here(data):
    text = data.decode('utf-8-sig')
    replacements = {
        'AxisMeld Windows x64 开发预览版 / Rigging Workspace Preview':
            'AxisMeld Windows x64 开发预览版 / Skin Weights Preview',
        '新增 RG-07 至 RG-14': '新增 RG-15 至 RG-20；RG-07 至 RG-14 仍待测',
    }
    for original, updated in replacements.items():
        if text.count(original) != 1:
            raise ValueError('Unexpected fixed-baseline START-HERE content: ' + original)
        text = text.replace(original, updated, 1)
    return (text.rstrip() + '\n\n' + SKIN_USAGE).encode('utf-8')


def assemble_python_overlay(repo, base_archive, output, build_id, native_commit, base_sha):
    """Overlay Git blobs after admission; kept separate for tiny Git/ZIP tests.

    The CLI always uses package(), which admits only the one pinned public ZIP.
    This function still checks its supplied archive hash and unchanged native
    inputs; it does not turn a different native build into a supported baseline.
    """
    repo, base_archive, output = map(Path, (repo, base_archive, output))
    sidecar = Path(str(output) + '.sha256')
    for path in (output, sidecar):
        if path.exists() or path.is_symlink():
            raise FileExistsError('Refuse to overwrite existing output: ' + str(path))
    if output.suffix.lower() != '.zip':
        raise ValueError('Output must have a .zip extension')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', build_id):
        raise ValueError('Build ID must use letters, digits, dots, underscores or hyphens')
    if sha_file(base_archive) != base_sha:
        raise ValueError('Base archive SHA256 mismatch')
    head = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
    with zipfile.ZipFile(base_archive) as source:
        check_archive_entries(source)
        manifest = json.loads(source.read(MANIFEST))
        if manifest['sourceCommit'] != native_commit:
            raise ValueError('Base manifest native source commit mismatch')
        if manifest['buildId'] == build_id:
            raise ValueError('New preview requires a distinct build ID')
        binary_sha = sha(source.read(PREFIX + 'blender.exe'))
        if manifest['binarySha256'] != binary_sha:
            raise ValueError('Base manifest executable SHA256 mismatch')
        resources = committed_resources(repo, head, [item['path'] for item in manifest['resources']])
        changed_paths = validate_source_changes(repo, native_commit, head, resources.keys())
        resource_map = {path: sha(data) for path, data in sorted(resources.items())}
        manifest.update(buildId=build_id, sourceCommit=head,
                        source='https://github.com/AngelHob/AxisMeld/tree/' + head,
                        sourceURL='https://github.com/AngelHob/AxisMeld/tree/' + head,
                        resources=[{'path': path, 'sha256': digest} for path, digest in resource_map.items()],
                        resourceFingerprint=sha(json.dumps(resource_map, sort_keys=True, separators=(',', ':')).encode()),
                        binaryProvenance={
                            'method': 'reused-native-binary-with-committed-python-overlay',
                            'nativeSourceCommit': native_commit,
                            'binarySha256': binary_sha,
                            'baseReleaseTag': manifest['buildId'],
                            'baseArchiveName': base_archive.name,
                            'baseArchiveSha256': base_sha,
                            'scope': 'No native rebuild. Native and embedded startup inputs must remain unchanged.'})
        notes = (
            'AxisMeld Skin Weights 开发预览版\n\n'
            f'版本：{build_id}\nPython 源码：{head}\n原生源码：{native_commit}\n\n'
            + SKIN_USAGE + '\n'
            '本包复用已审计 Rigging 预览包的原生程序、内嵌启动资产、DLL 和运行库，未重新编译。\n'
            '新增 RG-15 至 RG-20；RG-07 至 RG-14 仍待测。生产角色变形、第三方扩展和高 DPI\n'
            '仍需人工验收；精确 Python/原生源码与文件指纹见 AxisMeld-build.json。\n'
        )
        replacements = {PREFIX + VERSION + path: data for path, data in resources.items()}
        replacements[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        replacements[NOTES] = notes.encode('utf-8')
        replacements[START_HERE] = refresh_start_here(source.read(START_HERE))
        names = set(source.namelist())
        all_names = names | replacements.keys()
        if len(all_names) != len({name.casefold() for name in all_names}):
            raise ValueError('New resource causes a case-insensitive ZIP path collision')
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
            for item in source.infolist():
                info = copy.copy(item)
                if item.filename in replacements:
                    target.writestr(info, replacements[item.filename])
                else:
                    with source.open(item) as reader, target.open(info, 'w') as writer:
                        shutil.copyfileobj(reader, writer, length=1024 * 1024)
            timestamp = source.getinfo(MANIFEST).date_time
            for name in sorted(replacements.keys() - names):
                info = zipfile.ZipInfo(name, timestamp)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(info, replacements[name])
    with zipfile.ZipFile(output) as result:
        if result.testzip() is not None:
            raise ValueError('New package CRC verification failed')
        for path, expected in resource_map.items():
            if sha(result.read(PREFIX + VERSION + path)) != expected:
                raise ValueError('New package resource verification failed: ' + path)
        if sha(result.read(PREFIX + 'blender.exe')) != binary_sha:
            raise ValueError('New package executable verification failed')
    output_sha = sha_file(output)
    with sidecar.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(output_sha + '  ' + output.name + '\n')
    return dict(status='PASS', source_commit=head, native_source_commit=native_commit,
                binary_sha256=binary_sha, resource_count=len(resources), changed_paths=changed_paths,
                archive=str(output.resolve()), archive_sha256=output_sha,
                archive_bytes=output.stat().st_size, sidecar=str(sidecar.resolve()))


def package(repo, base_archive, output, build_id):
    """Public entry point: only the fixed, independently audited release is accepted."""
    if sha_file(base_archive) != BASE_ARCHIVE_SHA256:
        raise ValueError('Only the fixed Rigging release ZIP is accepted (SHA256 mismatch)')
    # Import after pin validation so small failure tests do not need a full release.
    from axismeld_release_audit import audit
    report = audit(base_archive, repo)
    if report['source_commit'] != NATIVE_SOURCE_COMMIT:
        raise ValueError('Audited release has the wrong fixed native source')
    return assemble_python_overlay(repo, base_archive, output, build_id,
                                   NATIVE_SOURCE_COMMIT, BASE_ARCHIVE_SHA256)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--base-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build-id', required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.repo, args.base_archive, args.output, args.build_id), indent=2))


if __name__ == '__main__':
    main()

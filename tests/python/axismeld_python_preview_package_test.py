# SPDX-License-Identifier: GPL-2.0-or-later
"""Small real Git/ZIP fixtures for the fixed-baseline Python preview packager."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


TOOL = Path(__file__).resolve().parents[2] / 'tools/utils/axismeld_python_preview_package.py'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class PythonPreviewPackageTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'The Python-only preview packager has not been implemented')
        spec = importlib.util.spec_from_file_location('preview_package', TOOL)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.temporary = tempfile.TemporaryDirectory(prefix='axismeld-package-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Package Test')
        self.git('config', 'user.email', 'package-test@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.resource = 'scripts/modules/axismeld/existing.py'
        self.write(self.resource, b'VALUE = "baseline"\n')
        self.write('source/creator/creator.cc', b'/* native baseline */\n')
        self.write('release/datafiles/startup.blend', b'fixture startup\x00')
        self.write('.gitattributes', b'*.blend -text\n')
        self.write('docs/README.md', b'Baseline docs\n')
        self.base_commit = self.commit()
        self.base = self.root / 'baseline.zip'
        self.native = b'MZ fixture executable\x00\xff'
        self.runtime = b'DLL runtime bytes\x00\x80'
        self.license = b'Fixture license retained exactly\r\n'
        self.start_here = (
            'AxisMeld Windows x64 开发预览版 / Rigging Workspace Preview\r\n'
            'Rigging 原有说明保留。\r\nRigify 默认内置，无需安装或启用。\r\n'
            '新增 RG-07 至 RG-14。\r\n'
        ).encode('utf-8')
        self.manifest = {
            'buildId': 'baseline-preview',
            'channel': 'development-preview',
            'sourceCommit': self.base_commit,
            'source': 'https://example.invalid/baseline',
            'binarySha256': sha(self.native),
            'embeddedSourceAssets': [{'path': 'release/datafiles/startup.blend', 'sha256': sha(b'fixture startup\x00')}],
            'resources': [{'path': self.resource, 'sha256': sha(b'VALUE = "baseline"\n')}],
        }
        with zipfile.ZipFile(self.base, 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in {
                'AxisMeld-Preview/blender.exe': self.native,
                'AxisMeld-Preview/runtime.dll': self.runtime,
                'AxisMeld-Preview/copying.txt': self.license,
                'AxisMeld-Preview/portable/README.txt': b'Portable marker\n',
                'AxisMeld-Preview/AxisMeld-START-HERE.txt': self.start_here,
                'AxisMeld-Preview/5.3/' + self.resource: b'VALUE = "baseline"\n',
                'AxisMeld-Preview/AxisMeld-build.json': json.dumps(self.manifest).encode(),
            }.items():
                z.writestr(name, data)
        self.base_sha = sha(self.base.read_bytes())
        self.output = self.root / 'preview.zip'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def write(self, path, data):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture change')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def assemble(self):
        # Admission against the one real release is tested separately. This
        # exercises its subsequent Git/ZIP pipeline with real, tiny fixtures.
        return self.tool.assemble_python_overlay(
            self.repo, self.base, self.output, 'skin-preview-test',
            self.base_commit, self.base_sha)

    def test_packages_committed_scripts_and_preserves_native_runtime(self):
        committed = b'VALUE = "committed"\n'
        added = b'def normalize_weights():\n    return "fixture"\n'
        self.write(self.resource, committed)
        self.write('scripts/modules/axismeld/skin_weights.py', added)
        self.write('docs/README.md', b'Updated public docs\n')
        head = self.commit()
        # Neither a dirty working-tree script nor local runtime cache may leak.
        self.write(self.resource, b'VALUE = "uncommitted"\n')
        self.write('scripts/modules/axismeld/private_untracked.py', b'UNTRACKED = True\n')
        self.write('portable/config/userpref.blend', b'private fixture')
        self.write('scripts/modules/axismeld/__pycache__/existing.pyc', b'cache')
        result = self.assemble()
        with zipfile.ZipFile(self.output) as z:
            self.assertEqual(z.read('AxisMeld-Preview/blender.exe'), self.native)
            self.assertEqual(z.read('AxisMeld-Preview/runtime.dll'), self.runtime)
            self.assertEqual(z.read('AxisMeld-Preview/copying.txt'), self.license)
            self.assertEqual(z.read('AxisMeld-Preview/5.3/' + self.resource), committed)
            self.assertEqual(z.read('AxisMeld-Preview/5.3/scripts/modules/axismeld/skin_weights.py'), added)
            names = z.namelist()
            self.assertFalse(any('__pycache__' in p or 'userpref' in p or 'private_untracked' in p for p in names))
            manifest = json.loads(z.read('AxisMeld-Preview/AxisMeld-build.json'))
            self.assertEqual(manifest['sourceCommit'], head)
            self.assertEqual(manifest['channel'], 'development-preview')
            self.assertEqual(manifest['embeddedSourceAssets'], self.manifest['embeddedSourceAssets'])
            self.assertEqual(manifest['binaryProvenance']['nativeSourceCommit'], self.base_commit)
            self.assertEqual(manifest['binaryProvenance']['baseArchiveSha256'], self.base_sha)
            resource_map = {p['path']: p['sha256'] for p in manifest['resources']}
            self.assertEqual(resource_map, {self.resource: sha(committed), 'scripts/modules/axismeld/skin_weights.py': sha(added)})
            expected_fingerprint = sha(json.dumps(resource_map, sort_keys=True, separators=(',', ':')).encode())
            self.assertEqual(manifest['resourceFingerprint'], expected_fingerprint)
            self.assertIn(b'Normalize Weights', z.read('AxisMeld-Preview/AxisMeld-Skin-Weights.txt'))
        self.assertEqual(result['source_commit'], head)
        self.assertEqual(Path(str(self.output) + '.sha256').read_text().split(), [sha(self.output.read_bytes()), self.output.name])

    def test_rejects_native_startup_and_attributes_changes(self):
        for path in ('source/creator/creator.cc', 'release/datafiles/startup.blend', '.gitattributes', 'CMakeLists.txt'):
            with self.subTest(path=path):
                target = self.repo / path
                original = target.read_bytes() if target.exists() else None
                self.write(path, b'changed native build input\n')
                self.commit()
                with self.assertRaisesRegex(ValueError, 'Unsupported source changes'):
                    self.assemble()
                self.assertFalse(self.output.exists())
                if original is None:
                    target.unlink()
                else:
                    target.write_bytes(original)
                self.commit()

    def test_refreshes_start_here_and_preserves_original_instructions(self):
        self.assemble()
        with zipfile.ZipFile(self.output) as z:
            text = z.read('AxisMeld-Preview/AxisMeld-START-HERE.txt').decode('utf-8')
        self.assertIn('Skin Weights Preview', text)
        self.assertIn('新增 RG-15 至 RG-20；RG-07 至 RG-14 仍待测', text)
        self.assertIn('Rigging 原有说明保留。', text)
        self.assertIn('Rigify 默认内置，无需安装或启用。', text)
        self.assertIn('Edit > Adjust Last Operation', text)
        self.assertIn('Prune Small Weights', text)

    def test_rejects_changed_script_that_would_not_be_packaged(self):
        self.write('scripts/modules/unlisted.py', b'RUNTIME_CHANGE = True\n')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'Unsupported source changes'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_rejects_native_gitlink_even_when_git_config_ignores_submodules(self):
        self.git('update-index', '--add', '--cacheinfo',
                 '160000,' + self.base_commit + ',lib/windows_x64')
        self.git('commit', '-qm', 'change native dependency')
        self.git('config', 'diff.ignoreSubmodules', 'all')
        with self.assertRaisesRegex(ValueError, 'Unsupported source changes'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_rejects_deleted_manifest_resource(self):
        self.git('rm', '--', self.resource)
        self.git('commit', '-qm', 'remove required runtime script')
        with self.assertRaisesRegex(ValueError, 'Missing committed resource'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_rejects_changed_base_archive_before_writing(self):
        with self.base.open('ab') as stream:
            stream.write(b'changed archive')
        with self.assertRaisesRegex(ValueError, 'Base archive SHA256'):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_public_entry_rejects_nonpublished_archive(self):
        with self.assertRaisesRegex(ValueError, 'fixed Rigging release'):
            self.tool.package(self.repo, self.base, self.output, 'skin-preview-test')
        self.assertFalse(self.output.exists())

    def test_writes_checksum_for_unicode_output_filename(self):
        self.output = self.root / '中文预览.zip'
        self.assemble()
        text = Path(str(self.output) + '.sha256').read_text(encoding='utf-8')
        self.assertEqual(text, sha(self.output.read_bytes()) + '  中文预览.zip\n')

    def test_refuses_existing_zip_or_sidecar_without_overwrite(self):
        for occupied in (self.output, Path(str(self.output) + '.sha256')):
            with self.subTest(occupied=occupied.name):
                occupied.write_bytes(b'KEEP EXISTING OUTPUT')
                with self.assertRaises(FileExistsError):
                    self.assemble()
                self.assertEqual(occupied.read_bytes(), b'KEEP EXISTING OUTPUT')
                occupied.unlink()


if __name__ == '__main__':
    unittest.main()

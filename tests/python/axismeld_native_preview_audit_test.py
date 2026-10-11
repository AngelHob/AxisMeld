# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Static package gates exercised with an isolated minimal Git/install/ZIP fixture."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'native_preview_audit', ROOT / 'tools/utils/axismeld_native_preview_audit.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def write(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


class NativePreviewAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory(prefix='axismeld-native-audit-')
        cls.root = Path(cls.base.name)
        cls.repo = cls.root / 'source'
        cls.template = cls.root / 'template'
        cls.repo.mkdir()
        cls.template.mkdir()
        cls.resources = set(AUDIT.INTEGRATION) | {
            'scripts/modules/axismeld/__init__.py',
            'scripts/modules/rigify/__init__.py',
        }
        for path in cls.resources:
            write(cls.repo, path, b'# fixture\n')
            write(cls.template, '5.3/' + path, b'# fixture\n')
        sources = {
            'COPYING': b'fixture copying\n',
            'release/license/license.md': b'fixture license\n',
            'release/datafiles/startup.blend': b'fixture startup asset',
            'release/datafiles/axismeld/portable/README.txt': b'fixture portable\n',
            'scripts/modules/axismeld/data.txt': b'fixture module asset\n',
        }
        for path, content in sources.items():
            write(cls.repo, path, content)
        for packaged, source in (
                ('copying.txt', 'COPYING'),
                ('license/license.md', 'release/license/license.md'),
                ('portable/README.txt', 'release/datafiles/axismeld/portable/README.txt'),
                ('5.3/scripts/modules/axismeld/data.txt', 'scripts/modules/axismeld/data.txt')):
            write(cls.template, packaged, sources[source])
        for path in ('blender.exe', 'blender-launcher.exe', 'ucrtbase.dll',
                     '5.3/python/bin/python.exe'):
            write(cls.template, path, b'MZ fixture executable')
        for assembly in ('blender.crt', 'blender.shared'):
            content = ('<assembly><assemblyIdentity name="' + assembly +
                       '"/><file name="fixture.dll"/></assembly>').encode()
            write(cls.template, assembly + '/' + assembly + '.manifest', content)
            write(cls.template, assembly + '/fixture.dll', b'MZ fixture dll')
        def git(*args):
            return subprocess.check_output(
                ['git', '-C', str(cls.repo), '-c', 'core.autocrlf=false', *args],
                stderr=subprocess.STDOUT).decode().strip()
        git('init', '-q', '--template=')
        git('add', '.')
        git('-c', 'user.name=Audit Fixture', '-c', 'user.email=fixture@example.invalid',
            '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Static audit fixture')
        cls.commit = git('rev-parse', 'HEAD')

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(dir=self.root, prefix='case-')
        self.folder = Path(self.case.name)
        self.install = self.folder / 'install'
        shutil.copytree(self.template, self.install)
        self.args = SimpleNamespace(
            install=self.install, repo=self.repo, report=self.folder / 'report.json',
            phase='staging', extra_resource=[], archive=None, archive_prefix='AxisMeld-Preview')

    def tearDown(self):
        self.case.cleanup()

    def manifest(self):
        resources = {p: AUDIT.digest(self.install / '5.3' / p) for p in self.resources}
        value = {
            'sourceCommit': self.commit, 'nativeSourceCommit': self.commit,
            'source': 'https://github.com/AngelHob/AxisMeld/tree/' + self.commit,
            'binarySha256': AUDIT.digest(self.install / 'blender.exe'),
            'resources': resources,
            'resourceFingerprint': AUDIT.sha(json.dumps(
                resources, sort_keys=True, separators=(',', ':')).encode()),
            'embeddedSourceAssets': [{'path': 'release/datafiles/startup.blend',
                                     'sha256': AUDIT.digest(self.repo / 'release/datafiles/startup.blend')}],
            'files': {p.relative_to(self.install).as_posix(): AUDIT.digest(p)
                      for p in self.install.rglob('*')
                      if p.is_file() and p.name != 'AxisMeld-build.json'},
        }
        write(self.install, 'AxisMeld-build.json', json.dumps(value).encode())

    def archive(self, extra=()):
        self.args.archive = self.folder / 'fixture.zip'
        with zipfile.ZipFile(self.args.archive, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in self.install.rglob('*'):
                if path.is_file():
                    archive.write(path, 'AxisMeld-Preview/' + path.relative_to(self.install).as_posix())
            for name, content in extra:
                archive.writestr(name, content)
        Path(str(self.args.archive) + '.sha256').write_text(
            AUDIT.digest(self.args.archive) + '  ' + self.args.archive.name, encoding='ascii')

    def test_valid_committed_install_and_zip_are_read_only(self):
        self.manifest()
        self.archive([('AxisMeld-Preview/empty/', '')])
        before = {p: AUDIT.digest(p) for directory in (self.repo, self.install)
                  for p in directory.rglob('*') if p.is_file()}
        result = AUDIT.audit(self.args)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['archive']['files'], result['files_count'])
        self.assertFalse(self.args.report.exists())
        self.assertEqual(before, {p: AUDIT.digest(p) for p in before})

    def test_self_manifest_cannot_admit_uncommitted_managed_module_files(self):
        for module, filename in (('rigify', 'stale.py'), ('axismeld', 'stale.txt')):
            with self.subTest(module=module, filename=filename):
                path = self.install / '5.3/scripts/modules' / module / filename
                path.write_bytes(b'# source does not contain this file\n')
                self.manifest()
                with self.assertRaisesRegex(ValueError, 'Managed module file set'):
                    AUDIT.audit(self.args)
                path.unlink()

    def test_managed_non_python_asset_must_match_source(self):
        write(self.install, '5.3/scripts/modules/axismeld/data.txt', b'altered asset\n')
        self.manifest()
        with self.assertRaisesRegex(ValueError, 'Module asset source mismatch'):
            AUDIT.audit(self.args)

    def test_private_text_is_checked_in_utf8_utf16_and_utf32(self):
        for encoding in ('utf-8', 'utf-16', 'utf-32'):
            with self.subTest(encoding=encoding):
                content = 'C:\\Users\\FixturePrivate\\Documents https://fixture-private.chatgpt.site/'
                write(self.install, 'notes.txt', content.encode(encoding))
                self.manifest()
                with self.assertRaisesRegex(ValueError, 'Private text patterns'):
                    AUDIT.audit(self.args)

    def test_unscannable_selected_text_fails_closed(self):
        write(self.install, 'notes.txt', b'\xffinvalid text')
        self.manifest()
        with self.assertRaisesRegex(ValueError, 'Unscannable text file'):
            AUDIT.audit(self.args)

    def test_zip_file_directory_identity_collision_is_rejected(self):
        self.manifest()
        self.archive([('AxisMeld-Preview/BLENDER.EXE/', '')])
        with self.assertRaisesRegex(ValueError, 'ZIP path collision'):
            AUDIT.audit(self.args)

    def test_zip_file_cannot_be_another_entry_ancestor(self):
        self.manifest()
        self.archive([('AxisMeld-Preview/blender.exe/subdirectory/', '')])
        with self.assertRaisesRegex(ValueError, 'ZIP file is an ancestor'):
            AUDIT.audit(self.args)

    def test_report_cannot_be_inside_install(self):
        self.manifest()
        self.args.report = self.install / 'audit.json'
        with self.assertRaisesRegex(ValueError, 'Report must be outside install'):
            AUDIT.audit(self.args)
        self.assertFalse(self.args.report.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)

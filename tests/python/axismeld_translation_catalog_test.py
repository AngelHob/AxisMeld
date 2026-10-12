# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Complete first-party catalog coverage without changing canonical identifiers."""
from copy import deepcopy
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/modules'))
from axismeld import translations
from axismeld.commands import COMMANDS
from axismeld.hotbox_catalog import default_catalog
from axismeld.workspace_menu_catalog import build_workspace_menubar


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))


class TranslationCatalogTests(unittest.TestCase):
    def test_every_fixed_hotbox_menu_recent_caption_and_explanation_has_a_translation(self):
        catalogs = [default_catalog(), build_workspace_menubar()['menus']]
        before = deepcopy(catalogs)
        sources = {command.label for command in COMMANDS.values()}
        for catalog in catalogs:
            for node in walk(catalog):
                sources.update(node[field] for field in ('label', 'reason') if node.get(field))
                if node.get('options', {}).get('reason'):
                    sources.add(node['options']['reason'])
        self.assertEqual(sorted(sources - translations.ZH_HANS.keys()), [])
        self.assertEqual(catalogs, before)

    def test_source_fallbacks_are_explicit_and_templates_keep_their_arguments(self):
        for source, target in translations.ZH_HANS.items():
            with self.subTest(source=source):
                self.assertTrue(source and target)
                self.assertNotIn('TODO', target)
                self.assertEqual(re.findall(r'%(?:\([^)]+\))?[sdif]', source),
                                 re.findall(r'%(?:\([^)]+\))?[sdif]', target))
                if source in translations.TECHNICAL_TERMS:
                    self.assertEqual(target, translations.TECHNICAL_TERMS[source])
                elif source in translations.UNCHANGED:
                    self.assertEqual(source, target)
                else:
                    self.assertRegex(target, r'[\u3400-\u9fff]')

    def test_two_language_install_list_retains_saved_preference_ids(self):
        entries = [line.split(':')[:3] for line in
                   (ROOT / 'release/datafiles/axismeld/languages').read_text(encoding='utf-8').splitlines()
                   if line and not line.startswith('#')]
        self.assertEqual([(entry[0], entry[2]) for entry in entries], [('1', 'en_US'), ('13', 'zh_HANS')])

    def test_chinese_dictionary_is_registered_in_native_label_and_operator_contexts(self):
        self.assertEqual(set(translations.TRANSLATIONS), {'zh_HANS'})
        for source, target in translations.ZH_HANS.items():
            for context in ('*', 'Operator', 'AxisMeld'):
                self.assertEqual(translations.TRANSLATIONS['zh_HANS'][context, source], target)


if __name__ == '__main__':
    unittest.main()

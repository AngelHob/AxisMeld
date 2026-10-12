# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise real language switching and every fixed first-party UI caption.

Run with an isolated BLENDER_USER_CONFIG and --factory-startup. Does not save
preferences, modify scene data, or mark any manual acceptance item complete.
"""
import json
import os
from pathlib import Path
import re

import bpy

from axismeld.commands import COMMANDS
from axismeld.hotbox_catalog import default_catalog
from axismeld.workspace_menu_catalog import build_workspace_menubar


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('children', ()))


def main():
    prefs = bpy.context.preferences
    prefs.use_preferences_save = False
    labels = {node['label'] for node in walk(default_catalog()) if node.get('label')}
    labels.update(node['label'] for node in walk(build_workspace_menubar()['menus']) if node.get('label'))
    labels.update(command.label for command in COMMANDS.values())
    locales = tuple(bpy.app.translations.locales)
    assert set(locales) == {'en_US', 'zh_HANS'} and len(locales) == 2, locales
    from axismeld import translations
    labels.update(translations.ZH_HANS)
    before = [(node['id'], node.get('command')) for node in walk(default_catalog())]
    prefs.view.use_translate_interface = True
    prefs.view.use_translate_tooltips = True
    prefs.view.language = 'zh_HANS'
    missing = [label for label in sorted(labels)
               if label not in translations.UNCHANGED
               and translations.iface(label) != translations.TECHNICAL_TERMS.get(label)
               and not re.search(r'[\u3400-\u9fff]', translations.iface(label))]
    assert not missing, missing
    for (context, source), expected in translations.translations_blender.CONTEXTUAL_ZH_HANS.items():
        assert bpy.app.translations.pgettext_iface(source, context) == expected, (context, source)
    for source, expected in {'Cavity': '腔体', 'Xform Ops': '变换操作'}.items():
        assert bpy.app.translations.pgettext_iface(source) == expected, source
    for source, expected in {'Edit Mesh': '编辑网格', 'Mesh Tools': '网格工具',
                             'Skeleton': '骨架', 'Skin': '蒙皮',
                             'Target Weld Tool': '目标焊接工具', 'Options': '选项'}.items():
        assert translations.iface(source) == expected, (source, translations.iface(source))
    prefs.view.use_translate_interface = False
    assert translations.iface('Edit Mesh') == 'Edit Mesh'
    prefs.view.use_translate_interface = True
    prefs.view.use_translate_tooltips = False
    assert translations.tip('Options') == 'Options'
    prefs.view.use_translate_tooltips = True
    prefs.view.language = 'en_US'
    assert all(translations.iface(label) == label for label in labels)
    assert all(translations.tip(label) == label for label in labels)
    assert before == [(node['id'], node.get('command')) for node in walk(default_catalog())]
    # User data is never replaced by a localized catalog caption.
    obj = bpy.context.active_object
    if obj is not None:
        old_name = obj.name
        obj.name = 'Target Weld Tool'
        prefs.view.language = 'zh_HANS'
        from axismeld import hotbox_runtime
        snapshot = json.loads(hotbox_runtime.snapshot(bpy.context))
        title = next(node['label'] for node in walk(snapshot['menus'])
                     if node['id'] == 'context.component_menu.object')
        assert title == 'Target Weld Tool...', title
        obj.name = old_name
        bpy.context.view_layer.objects.active = None
        snapshot = json.loads(hotbox_runtime.snapshot(bpy.context))
        title = next(node['label'] for node in walk(snapshot['menus'])
                     if node['id'] == 'context.component_menu.object')
        assert title == translations.iface('Object...'), title
        bpy.context.view_layer.objects.active = obj
    prefs.view.language = 'en_US'
    translations.unregister()
    translations.register()
    prefs.view.language = 'zh_HANS'
    assert translations.iface('Target Weld Tool') == '目标焊接工具'
    prefs.view.language = 'en_US'
    report = {'status': 'PASS', 'locales': locales, 'captions': len(labels),
              'unchangedTerms': len(translations.UNCHANGED),
              'normalizedTechnicalTerms': translations.TECHNICAL_TERMS, 'missing': missing,
              'englishRoundTrip': True, 'userDataProtected': True,
              'interfaceAndTooltipFlags': True, 'registrationReload': True}
    output = os.environ.get('AXISMELD_BILINGUAL_REPORT')
    if output:
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('AXISMELD_BILINGUAL_UI_PASS', json.dumps(report, ensure_ascii=False))


main()

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""First-party display translations; canonical catalogs and data names stay English.

Blender's MO catalogs retain precedence. These dictionaries fill first-party
messages absent from the upstream catalog and use Blender's translation flags.
"""
from . import (translations_native_labels, translations_labels_a,
               translations_labels_b, translations_labels_c, translations_ui,
               translations_reasons, translations_blender)

_MODULES = (translations_native_labels, translations_labels_a,
            translations_labels_b, translations_labels_c, translations_ui,
            translations_reasons, translations_blender)
ZH_HANS = {}
UNCHANGED = set()
for _module in _MODULES:
    ZH_HANS.update(_module.ZH_HANS)
    UNCHANGED.update(_module.UNCHANGED)
UNCHANGED = frozenset(source for source in UNCHANGED if ZH_HANS.get(source) == source)
# Native terminology normalizes these spellings while retaining their standard
# abbreviations. Keep the exact accepted display explicit instead of accepting
# arbitrary English fallbacks as completed Chinese translations.
TECHNICAL_TERMS = {'UVs': 'UV', 'Nurbs': 'NURBS'}
_REGISTRATION_KEY = 'axismeld.ui'
TRANSLATIONS = {'zh_HANS': {(context, source): target
                            for source, target in ZH_HANS.items()
                            for context in ('*', 'Operator', 'AxisMeld')}}
TRANSLATIONS['zh_HANS'].update(translations_blender.CONTEXTUAL_ZH_HANS)


def iface(message, context='*'):
    """Translate an interface caption, honoring the native interface flag."""
    import bpy
    result = bpy.app.translations.pgettext_iface(message, context)
    if result == message and context != '*':
        result = bpy.app.translations.pgettext_iface(message)
    return result


def tip(message, context='*'):
    """Translate an explanation, honoring the independent native tooltip flag."""
    import bpy
    result = bpy.app.translations.pgettext_tip(message, context)
    if result == message and context != '*':
        result = bpy.app.translations.pgettext_tip(message)
    return result


def register():
    import bpy
    # The same first-party owner is reused during Reload Scripts; no add-on state
    # or user configuration is needed to install the bundled vocabulary.
    bpy.app.translations.unregister(_REGISTRATION_KEY)
    bpy.app.translations.register(_REGISTRATION_KEY, TRANSLATIONS)


def unregister():
    import bpy
    bpy.app.translations.unregister(_REGISTRATION_KEY)

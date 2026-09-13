# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compose modeled operations into native lists without changing marking directions."""
import re
from .modeling_registry import CATEGORIES, SPECS


def extend_catalog(roots, node):
    pending = list(roots)
    lookup = {}
    while pending:
        entry = pending.pop()
        lookup[entry['id']] = entry
        pending.extend(entry['children'])
    for identifier in CATEGORIES.values():
        entry = lookup[identifier]
        entry.update(kind='menu', enabled=True, reason='', presentation='list')

    def destination(category, section):
        current = lookup[CATEGORIES[category]]
        for label in section:
            identifier = current['id'] + '.m3_' + re.sub('[^a-z0-9]+', '_', label.lower()).strip('_')
            if identifier not in lookup:
                child = node(identifier, 'menu', label, presentation='list')
                current['children'].append(child)
                lookup[identifier] = child
            current = lookup[identifier]
        return current

    for spec in SPECS.values():
        destination(spec.category, spec.section)['children'].append(
            node('m3.' + spec.id, 'command', spec.label, command=spec.id))
    # Only independently audited missing capabilities belong here. No operator is attached.
    from .modeling_gaps import GAPS, ALIASES
    for alias in ALIASES:
        child = (node('m3.alias.' + alias['identity'], 'command', alias['label'], command=alias['command'])
                 if 'command' in alias else
                 node('gap.alias.' + alias['identity'], 'disabled', alias['label'], enabled=False,
                      reason=alias['plan'] + ': ' + alias['reason']))
        destination(alias['category'], tuple(alias['section']))['children'].append(child)
    for gap in GAPS:
        destination(gap['category'], tuple(gap['section']))['children'].append(
            node('gap.' + gap['identity'], 'disabled', gap['label'], enabled=False,
                 reason=gap['plan'] + ': ' + gap['reason']))
    return roots

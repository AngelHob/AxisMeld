# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Trusted, immutable declarations for modeling menu commands (no bpy dependency)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class NativeCall:
    operator: str
    modes: tuple = ('OBJECT',)
    kwargs: tuple = ()
    invoke: bool = False
    undo: bool = True


@dataclass(frozen=True)
class CommandSpec:
    id: str
    label: str
    category: str
    calls: tuple
    section: tuple = ()
    requires: str = ''
    replayable: bool = True
    classification: str = 'adapted'
    difference: str = ''
    source: str = ''
    maya: tuple = ()
    key: str | None = None
    ctrl: bool = False
    shift: bool = False
    alt: bool = False


def op(identifier, label, category, operator, *, modes=('OBJECT',), kwargs=None,
       invoke=False, undo=True, section=(), requires='', replayable=None,
       classification='adapted', difference='', source='', maya=(), key=None,
       ctrl=False, shift=False, alt=False):
    """Declare one fixed native entry; modal/UI entries default to no Recent replay."""
    return CommandSpec(identifier, label, category,
                       (NativeCall(operator, tuple(modes), tuple((kwargs or {}).items()), invoke, undo),),
                       tuple(section), requires, not invoke if replayable is None else replayable,
                       classification, difference, source, tuple(maya), key, ctrl, shift, alt)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Plan bounded skin weight changes without importing Blender or writing data."""

from collections.abc import Mapping
from math import fsum, isfinite
from numbers import Real
from struct import pack, unpack


# Blender stores weights as float32. Keep locked values unchanged when their
# sum differs from one only by float32 accumulation error.
_LOCK_SUM_TOLERANCE = 1e-6


def _float32(value):
    return unpack('f', pack('f', value))[0]


def _index(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f'{label} must be a non-negative integer')
    return value


def _group_indices(groups, label):
    try:
        indices = frozenset(groups)
    except TypeError as error:
        raise ValueError(f'{label} must contain group indices') from error
    for group in indices:
        _index(group, label)
    return indices


def _unit_value(value, label):
    if (isinstance(value, bool) or not isinstance(value, Real) or
            not 0.0 <= value <= 1.0 or not isfinite(value)):
        raise ValueError(f'{label} must be finite and between 0 and 1')
    return float(value)


def _snapshot(vertices):
    if not isinstance(vertices, Mapping):
        raise ValueError('Vertices must map vertex indices to group weights')
    snapshot = {}
    for vertex, weights in vertices.items():
        _index(vertex, 'Vertex index')
        if not isinstance(weights, Mapping):
            raise ValueError(f'Vertex {vertex} weights must map group indices to weights')
        snapshot[vertex] = {
            _index(group, f'Vertex {vertex} group index'):
            _unit_value(weight, f'Vertex {vertex}, group {group} weight')
            for group, weight in weights.items()
        }
    return snapshot


def _normalize(weights, locked_groups, vertex):
    """Normalize the positive members in a local, deform-only weight copy."""
    locked_sum = fsum(weight for group, weight in weights.items() if group in locked_groups)
    if locked_sum > 1.0 + _LOCK_SUM_TOLERANCE:
        raise ValueError(f'Vertex {vertex}: locked deform weights exceed 1')

    unlocked = {group: weight for group, weight in weights.items()
                if group not in locked_groups and weight > 0.0}
    if not unlocked:
        if abs(locked_sum - 1.0) > _LOCK_SUM_TOLERANCE:
            raise ValueError(f'Vertex {vertex}: no unlocked positive weight can fill the remaining total')
        return

    remaining = max(0.0, 1.0 - locked_sum)
    unlocked_sum = fsum(unlocked.values())
    for group, weight in unlocked.items():
        # Divide before multiplying to avoid underflow for tiny positive input.
        weights[group] = (weight / unlocked_sum) * remaining


def plan_weights(vertices, deform_groups, locked_groups, *, operation='NORMALIZE',
                 threshold=0.01, keep_strongest=True, normalize_after=True):
    """Return an atomic plan for one skin cleanup operation.

    ``vertices`` maps target vertex indices to snapshots of all their group
    weights. ``deform_groups`` identifies the only groups allowed to change;
    ``locked_groups`` contains permanent locks plus any caller-selected active
    lock. Unknown or non-deform lock indices are harmless.

    The returned ``changes`` maps only changed vertices and changed deform
    members to replacement float32 values, or ``None`` for member removal. A
    replacement that stores the same float32 value is omitted, avoiding empty
    Blender Undo operations. No input is mutated. ``changed_vertices`` counts
    these vertices; ``zero_vertices``
    counts targets with no positive deform weight after the operation.

    Originally zero-sum vertices retain their membership. Pruning is strictly
    below ``threshold``. Unless disabled, its last positive deform influence
    survives (largest weight, then smallest group index) and remaining weights
    are normalized. No operation creates a previously absent influence.

    Invalid snapshots/options and impossible normalization raise ``ValueError``
    before any plan is returned. Locked sums within 1e-6 of one are accepted
    without altering the locked weights, accommodating float32 roundoff.
    """
    if operation not in ('NORMALIZE', 'PRUNE'):
        raise ValueError('Operation must be NORMALIZE or PRUNE')
    threshold = _unit_value(threshold, 'Threshold')
    if not isinstance(keep_strongest, bool) or not isinstance(normalize_after, bool):
        raise ValueError('Keep Strongest and Normalize After must be booleans')
    deform_groups = _group_indices(deform_groups, 'Deform groups')
    locked_groups = _group_indices(locked_groups, 'Locked groups')
    snapshot = _snapshot(vertices)

    changes = {}
    zero_vertices = 0
    for vertex, original in snapshot.items():
        weights = {group: weight for group, weight in original.items() if group in deform_groups}
        positive = {group: weight for group, weight in weights.items() if weight > 0.0}
        if not positive:
            zero_vertices += 1
            continue

        if operation == 'PRUNE':
            removed = {group for group, weight in weights.items()
                       if group not in locked_groups and weight < threshold}
            if keep_strongest and not any(group not in removed for group in positive):
                strongest = min(positive, key=lambda group: (-positive[group], group))
                removed.discard(strongest)
            weights = {group: weight for group, weight in weights.items() if group not in removed}

        if not any(weight > 0.0 for weight in weights.values()):
            zero_vertices += 1
        elif operation == 'NORMALIZE' or normalize_after:
            _normalize(weights, locked_groups, vertex)

        vertex_changes = {}
        for group, weight in original.items():
            if group not in deform_groups:
                continue
            if group not in weights:
                vertex_changes[group] = None
            elif group not in locked_groups:
                stored_weight = _float32(weights[group])
                if stored_weight != _float32(weight):
                    vertex_changes[group] = stored_weight
        if vertex_changes:
            changes[vertex] = vertex_changes

    return {'changes': changes, 'zero_vertices': zero_vertices, 'changed_vertices': len(changes)}

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The complete trusted M3 registry, independent of Blender and user profiles."""
from types import MappingProxyType
from .modeling_common import SPECS as COMMON
from .modeling_mesh import SPECS as MESH
from .modeling_shapes import SPECS as SHAPES

CATEGORIES = MappingProxyType({
    'Select': 'common.select', 'Modify': 'common.modify', 'Edit': 'common.edit',
    'Create': 'common.create', 'Display': 'common.display', 'Mesh': 'modeling.mesh',
    'Edit Mesh': 'modeling.edit_mesh', 'Mesh Tools': 'modeling.mesh_tools',
    'Mesh Display': 'modeling.mesh_display', 'Curves': 'modeling.curves',
    'Surfaces': 'modeling.surfaces', 'Deform': 'modeling.deform',
})

_specs = (*COMMON, *MESH, *SHAPES)
if len({item.id for item in _specs}) != len(_specs):
    raise ValueError('Duplicate M3 command ID')
if any(item.category not in CATEGORIES or not item.calls for item in _specs):
    raise ValueError('Invalid M3 command declaration')
SPECS = MappingProxyType({item.id: item for item in _specs})


def keymap_targets(identifier):
    modes = {mode for call in SPECS[identifier].calls for mode in call.modes}
    return tuple(name for mode, name in (
        ('OBJECT', 'Object Mode'), ('EDIT_MESH', 'Mesh'), ('EDIT_CURVE', 'Curve'),
        ('EDIT_SURFACE', 'Curve'), ('EDIT_LATTICE', 'Lattice')) if mode in modes)

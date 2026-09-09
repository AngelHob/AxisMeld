# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Declarative AxisMeld hotbox menu catalog without Blender dependencies."""
from copy import deepcopy


_VIEW_REPLAYABLE = frozenset({
    'view.perspective', 'view.side', 'view.bottom', 'view.front', 'view.back',
    'view.top', 'view.left', 'view.focus_selected', 'view.frame_all',
    'view.wireframe', 'view.shaded',
})
_CLOSE_REPLAYABLE = frozenset({
    'view.toggle_quad', 'selection.toggle_component', 'selection.vertex_mode',
    'selection.edge_mode', 'selection.face_mode', 'transform.move',
    'transform.rotate', 'transform.scale',
})


def command_policy(command):
    """Return the fixed ``(close_before, replayable)`` command policy."""
    if command in _VIEW_REPLAYABLE:
        return False, True
    if command in _CLOSE_REPLAYABLE:
        return True, True
    return True, False


def _node(identifier, kind, label, *, command='', enabled=True, reason='', children=(), value=None):
    node = {
        'id': identifier,
        'kind': kind,
        'label': label,
        'command': command,
        'enabled': enabled,
        'reason': reason,
        'children': list(children),
    }
    if value is not None:
        node['value'] = value
    return node


def _menu(identifier, label, children):
    return _node(identifier, 'menu', label, children=children)


def _command(identifier, label, command, *, enabled=True, reason=''):
    return _node(identifier, 'command', label, command=command, enabled=enabled, reason=reason)


def _disabled(identifier, label, reason='Not implemented'):
    return _node(identifier, 'disabled', label, enabled=False, reason=reason)


def _separator(identifier):
    return _node(identifier, 'separator', '', enabled=False)


def _setting(identifier, label, setting, value):
    return _node(identifier, 'setting', label, command=setting, value=value)


def _view_items(prefix):
    items = (
        ('perspective', 'Perspective View', 'view.perspective', True),
        ('side', 'Side View', 'view.side', True),
        ('bottom', 'Bottom View', 'view.bottom', False),
        ('front', 'Front View', 'view.front', True),
        ('back', 'Back View', 'view.back', False),
        ('top', 'Top View', 'view.top', True),
        ('left', 'Left View', 'view.left', False),
    )
    return [_command(f'{prefix}.{suffix}', label, command, enabled=operational,
                     reason='' if operational else 'Adapter not implemented')
            for suffix, label, command, operational in items]


def _style_menu(prefix):
    return _menu(prefix, 'Hotbox Style', (
        _setting(f'{prefix}.rows', 'Zones and Menu Rows', 'style', 'rows'),
        _setting(f'{prefix}.zones', 'Zones Only', 'style', 'zones'),
        _setting(f'{prefix}.center', 'Center Zone Only', 'style', 'center'),
    ))


def _catalog():
    common = _menu('common', 'Common', (
        _disabled('common.file', 'File'),
        _disabled('common.edit', 'Edit'),
        _disabled('common.create', 'Create'),
        _menu('common.select', 'Select', (
            _command('common.select.object_component', 'Object / Component',
                     'selection.toggle_component'),
            _separator('common.select.separator.modes'),
            _command('common.select.vertex', 'Vertex', 'selection.vertex_mode'),
            _command('common.select.edge', 'Edge', 'selection.edge_mode'),
            _command('common.select.face', 'Face', 'selection.face_mode'),
        )),
        _menu('common.modify', 'Modify', (
            _command('common.modify.move', 'Move Tool', 'transform.move'),
            _command('common.modify.rotate', 'Rotate Tool', 'transform.rotate'),
            _command('common.modify.scale', 'Scale Tool', 'transform.scale'),
        )),
        _disabled('common.display', 'Display'),
        _disabled('common.windows', 'Windows'),
    ))

    pane_views = _menu('pane.panels.views', 'Views', _view_items('pane.panels'))
    pane = _menu('pane', 'Current Pane', (
        _menu('pane.view', 'View', (
            _command('pane.view.frame_selected', 'Frame Selected', 'view.focus_selected'),
            _command('pane.view.frame_all', 'Frame All', 'view.frame_all'),
        )),
        _menu('pane.shading', 'Shading', (
            _command('pane.shading.wireframe', 'Wireframe', 'view.wireframe'),
            _command('pane.shading.solid', 'Solid', 'view.shaded'),
        )),
        _disabled('pane.lighting', 'Lighting'),
        _disabled('pane.show', 'Show'),
        _disabled('pane.renderer', 'Renderer'),
        _menu('pane.panels', 'Panels', (
            pane_views,
            _separator('pane.panels.separator.layout'),
            _command('pane.panels.toggle_quad', 'Single / Quad View', 'view.toggle_quad'),
        )),
    ))

    views_children = _view_items('views')
    views_children.extend((_separator('views.separator.style'), _style_menu('views.style')))
    controls = _menu('center.controls', 'Hotbox Controls', (
        _menu('center.controls.rows', 'Menu Rows', (
            _setting('center.controls.rows.common', 'Show Common Menus', 'row.common', 'toggle'),
            _setting('center.controls.rows.pane', 'Show Pane Specific Menus', 'row.pane', 'toggle'),
            _setting('center.controls.rows.modeling', 'Show Modeling', 'row.modeling', 'toggle'),
        )),
        _style_menu('center.controls.style'),
        _menu('center.controls.transparency', 'Transparency', tuple(
            _setting(f'center.controls.transparency.{value}', f'{value}%', 'transparency', str(value))
            for value in (0, 25, 50, 75, 100)
        )),
    ))
    center = _menu('center', 'Center', (
        _disabled('center.recent', 'Recent Commands', 'Session history is not connected yet'),
        _menu('views', 'AxisMeld', views_children),
        controls,
    ))

    modeling = _menu('modeling', 'Modeling', tuple(
        _disabled(identifier, label) for identifier, label in (
            ('modeling.mesh', 'Mesh'),
            ('modeling.edit_mesh', 'Edit Mesh'),
            ('modeling.mesh_tools', 'Mesh Tools'),
            ('modeling.mesh_display', 'Mesh Display'),
            ('modeling.curves', 'Curves'),
            ('modeling.surfaces', 'Surfaces'),
            ('modeling.deform', 'Deform'),
            ('modeling.uv', 'UV'),
            ('modeling.generate', 'Generate'),
        )
    ))
    return common, pane, center, modeling


_DEFAULT_CATALOG = _catalog()


def default_catalog():
    """Return an independent copy of the built-in menu tree."""
    return tuple(deepcopy(_DEFAULT_CATALOG))

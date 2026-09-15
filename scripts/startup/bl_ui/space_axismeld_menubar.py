# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Native application menus for the AxisMeld Maya key configuration."""
from hashlib import sha256
import bpy
import blf
from bpy.types import Menu, Operator
from bpy.props import EnumProperty, StringProperty
from axismeld.commands import PRESET_NAME
from axismeld.workspace_menu_catalog import build_workspace_menubar
from axismeld import menubar_native, menubar_runtime

_CATALOG = build_workspace_menubar()
_NODES = {}

def _index(nodes):
    for node in nodes:
        _NODES[node['id']] = node
        _index(node.get('children', ()))

_index(_CATALOG['menus'])
_MENU_NAMES = {key: 'AXISMELD_MT_' + sha256(key.encode()).hexdigest()[:24]
               for key, node in _NODES.items() if node['kind'] == 'menu'}
_SET_LABELS = {'MODELING': 'Modeling', 'RIGGING': 'Rigging', 'ANIMATION': 'Animation',
               'FX': 'FX', 'RENDERING': 'Rendering'}
_COMPONENT_MENU_HOSTS = {
    'viewport.modeling.vertex': 'VIEW3D_MT_edit_mesh_vertices',
    'viewport.modeling.edge': 'VIEW3D_MT_edit_mesh_edges',
    'viewport.modeling.face': 'VIEW3D_MT_edit_mesh_faces',
}
_BLENDER_MODELING_MENUS = {
    'modeling.mesh': 'VIEW3D_MT_edit_mesh',
    **_COMPONENT_MENU_HOSTS,
    'modeling.uv': 'VIEW3D_MT_uv_map',
    'modeling.curves': 'VIEW3D_MT_edit_curve',
    'modeling.surfaces': 'VIEW3D_MT_edit_surface',
}
_REPLACED_HEADER_MENUS = frozenset(_BLENDER_MODELING_MENUS.values()) | {
    'VIEW3D_MT_edit_curve_ctrlpoints', 'VIEW3D_MT_edit_curve_segments',
    'VIEW3D_MT_edit_curves', 'VIEW3D_MT_edit_curves_control_points',
    'VIEW3D_MT_edit_curves_segments',
}
_VIEWPORT_SUPPLEMENTS = {
    'VIEW3D_MT_view': 'common.display',
    'VIEW3D_MT_select_object': 'common.select',
    'VIEW3D_MT_select_edit_mesh': 'common.select',
    'VIEW3D_MT_select_edit_curve': 'common.select',
    'VIEW3D_MT_select_edit_surface': 'common.select',
    'VIEW3D_MT_add': 'common.create',
    'VIEW3D_MT_mesh_add': 'common.create',
    'VIEW3D_MT_curve_add': 'common.create',
    'VIEW3D_MT_surface_add': 'common.create',
    'VIEW3D_MT_object': 'common.modify',
}
_HOST_CALLBACKS = []


def _icon(node):
    return node.get('icon') or ('FILE_FOLDER' if node['kind'] == 'menu' else 'TOOL_SETTINGS')


def enabled(context):
    configs = getattr(context.window_manager, 'keyconfigs', None)
    return getattr(getattr(configs, 'active', None), 'name', '') == PRESET_NAME


def modeling_workspace(context):
    workspace = getattr(context, 'workspace', None)
    area = getattr(context, 'area', None)
    return (enabled(context) and getattr(area, 'type', '') == 'VIEW_3D' and
            getattr(workspace, 'name', '').partition('.')[0] == 'Modeling')


class _ViewportMenuLayout:
    """Keep the native draw flow while the same Menu IDs host the new groups."""
    def __init__(self, layout):
        self._layout = layout

    def __getattr__(self, name):
        return getattr(self._layout, name)

    def menu(self, identifier, *args, **kwargs):
        if identifier not in _REPLACED_HEADER_MENUS:
            return self._layout.menu(identifier, *args, **kwargs)


def viewport_menu_layout(layout, context):
    return _ViewportMenuLayout(layout) if modeling_workspace(context) else layout


def draw_modeling_menus(layout, context):
    if not modeling_workspace(context):
        return
    for identifier in _CATALOG.get('modeling_roots', ()):
        # Keep real native Menu hosts so their append/prepend hooks still run.
        menu = _BLENDER_MODELING_MENUS.get(identifier, _MENU_NAMES[identifier])
        if identifier == 'modeling.curves' and getattr(context, 'mode', '') == 'EDIT_CURVES':
            menu = 'VIEW3D_MT_edit_curves'
        layout.menu(menu, text=_NODES[identifier]['label'])


def draw_native_modeling_menu(layout, context, identifier):
    if not modeling_workspace(context):
        return False
    draw_menu(layout, context, identifier)
    return True


def draw_supplement(layout, context, identifier):
    if enabled(context):
        layout.separator()
        layout.menu(_MENU_NAMES[identifier], text='Maya ' + _NODES[identifier]['label'], icon='FILE_FOLDER')


def draw_menu_sets_entry(layout, context):
    if enabled(context):
        layout.menu('AXISMELD_MT_workspace_menu_sets', text='Maya Menu Sets', icon='FILE_FOLDER')


def menu_columns(nodes, context):
    """Preserve every item and divider; divide only this menu's current level."""
    scale = max(.5, context.preferences.system.ui_scale)
    available = max(3, (context.window.height / scale - 100) / 22)
    columns, column, height = [], [], 0
    for index, node in enumerate(nodes):
        cost = (max(1, node.get('row_count_hint', 1)) if node['kind'] == 'native_group' else
                .3 if node['kind'] == 'separator' and not node.get('label') else 1)
        reserve = cost
        if node['kind'] == 'separator' and node.get('label'):
            # A named divider is a group heading, not an orphanable last row.
            for following in nodes[index + 1:]:
                reserve += .3 if following['kind'] == 'separator' and not following.get('label') else 1
                if following['kind'] != 'separator':
                    break
        if column and height + reserve > available:
            columns.append(column)
            column, height = [], 0
        column.append(node)
        height += cost
    if column:
        columns.append(column)
    return columns


class AXISMELD_OT_menubar_execute(Operator):
    bl_idname = 'axismeld.menubar_execute'
    bl_label = 'AxisMeld Menu Command'
    # The trusted child operator owns Undo, exactly as the existing command dispatcher.
    bl_options = {'INTERNAL'}
    kind: StringProperty(options={'SKIP_SAVE'})
    key: StringProperty(options={'SKIP_SAVE'})
    token: StringProperty(options={'SKIP_SAVE'})
    reason: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return properties.reason or 'Run this menu command in its captured source viewport'

    def execute(self, context):
        try:
            result = menubar_runtime.run(context, self.kind, self.key, self.token)
        except (RuntimeError, ValueError) as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        # The child owns its modal handler. This dispatcher has no modal method.
        return {'FINISHED'} if 'RUNNING_MODAL' in result else result


def _draw_item(layout, context, node):
    kind = node['kind']
    if kind == 'native_group':
        from bl_ui import space_axismeld_native_modeling
        space_axismeld_native_modeling.draw_group(layout, context, node['group_key'],
                                                include=node.get('include'))
        return
    if kind == 'separator':
        if node.get('label'):
            row = layout.row()
            row.enabled = False
            row.label(text=node['label'])
        else:
            layout.separator(factor=.3)
        return
    row = layout.row(align=True)
    if kind == 'menu':
        menu = _MENU_NAMES[node['id']]
        if modeling_workspace(context):
            menu = _COMPONENT_MENU_HOSTS.get(node['id'], menu)
        row.menu(menu, text=node['label'], icon=_icon(node))
    elif kind == 'native':
        menubar_native.draw_native(row, context, node['native_key'], text=node['label'], icon=_icon(node))
    else:
        token = menubar_runtime.source_token(context) if kind in {'command', 'action'} else ''
        key = node.get('command', '') if kind == 'command' else node.get('action_key', '')
        available, reason = menubar_runtime.available(context, kind, key, token) if token else (False, node.get('reason', 'Unavailable in Blender'))
        state = menubar_runtime.state(context, kind, key, token) if token else None
        authored_indicator = node.get('indicator', '')
        if node.get('origin') == 'maya' and not authored_indicator:
            state = None
        if state or authored_indicator in {'checkbox', 'radio'}:
            indicator, checked = state or (authored_indicator, False)
            state_cell = row.row(align=True)
            state_cell.enabled = bool(state) and available
            state_cell.label(text='', icon=('RADIOBUT_ON' if checked else 'RADIOBUT_OFF') if indicator == 'radio' else ('CHECKBOX_HLT' if checked else 'CHECKBOX_DEHLT'))
        body = row.row(align=True)
        body.enabled = available
        op = body.operator(AXISMELD_OT_menubar_execute.bl_idname, text=node['label'], icon=_icon(node))
        op.kind, op.key, op.token, op.reason = kind, key, token, reason or node.get('reason', '')
    # Options are distinct UI cells, never aliases of the main action.
    option = node.get('options')
    if option:
        cell = row.row(align=True)
        cell.enabled = False
        op = cell.operator(AXISMELD_OT_menubar_execute.bl_idname, text='', icon='PREFERENCES')
        op.kind, op.key, op.token = 'disabled', '', ''
        op.reason = option.get('reason') or 'Maya option parameters are not implemented'


def draw_menu(layout, context, identifier):
    nodes = list(_NODES[identifier].get('children', ()))
    columns = menu_columns(nodes, context)
    container = layout.row() if len(columns) > 1 else layout
    scale = max(.5, context.preferences.system.ui_scale)
    blf.size(0, context.preferences.ui_styles[0].widget.points * scale)
    for nodes in columns:
        column = container.column()
        # Measure the widget font, including separate semantic/state/option cells;
        # character counts do not predict a proportional caption's width.
        widths = [blf.dimensions(0, node.get('label', ''))[0] / scale + 48 +
                  (24 if node.get('options') else 0) +
                  (20 if node.get('indicator') else 0) for node in nodes]
        # Native rows also contain live shortcut text and dynamic menus. Their
        # native width estimate includes those cells; a caption-only override
        # would shrink them (for example Save As + Shift Ctrl S).
        if not any(node['kind'] in {'native', 'native_group'} for node in nodes):
            column.ui_units_x = max(widths, default=100) / 20
        for node in nodes:
            _draw_item(column, context, node)


def draw_bar(layout, context):
    if not enabled(context):
        return False
    layout.prop(context.window_manager, 'axismeld_menubar_set', text='')
    menu_set = getattr(context.window_manager, 'axismeld_menubar_set', 'MODELING')
    for identifier in _CATALOG['sets'].get(menu_set, _CATALOG['sets']['MODELING']):
        node = _NODES[identifier]
        # Category captions follow a native application menu bar. Semantic icons
        # remain on every submenu and function inside the popup.
        layout.menu(_MENU_NAMES[identifier], text=node['label'])
    return True


def _menu_class(identifier):
    def draw(self, context):
        draw_menu(self.layout, context, identifier)
    return type(_MENU_NAMES[identifier], (Menu,), {
        '__module__': __name__, 'bl_idname': _MENU_NAMES[identifier],
        'bl_label': _NODES[identifier]['label'], 'draw': draw,
    })


def _redraw(_self, context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {'TOPBAR', 'VIEW_3D'}:
                area.tag_redraw()


class AXISMELD_MT_workspace_menu_sets(Menu):
    bl_label = 'Maya Menu Sets'

    def draw(self, _context):
        for key, label in _SET_LABELS.items():
            self.layout.menu('AXISMELD_MT_workspace_set_' + key, text=label, icon='FILE_FOLDER')


def _set_menu_class(key):
    def draw(self, _context):
        for identifier in _CATALOG['sets'][key]:
            self.layout.menu(_MENU_NAMES[identifier], text=_NODES[identifier]['label'], icon='FILE_FOLDER')
    return type('AXISMELD_MT_workspace_set_' + key, (Menu,), {
        '__module__': __name__, 'bl_label': _SET_LABELS[key], 'draw': draw,
    })


def register_props():
    bpy.types.WindowManager.axismeld_menubar_set = EnumProperty(
        name='Menu Set', items=tuple((key, _SET_LABELS[key], '') for key in _CATALOG['sets']),
        default='MODELING', options={'SKIP_SAVE'}, update=_redraw,
    )
    # Append to actual native providers, preserving their mode branches and
    # add-on callbacks. The header continues using these same Menu IDs.
    for identifier, root in _VIEWPORT_SUPPLEMENTS.items():
        menu = getattr(bpy.types, identifier, None)
        if menu is not None:
            def draw(self, context, root=root):
                if modeling_workspace(context):
                    draw_supplement(self.layout, context, root)
            menu.append(draw)
            _HOST_CALLBACKS.append((menu, draw))


def unregister_props():
    for menu, draw in reversed(_HOST_CALLBACKS):
        menu.remove(draw)
    _HOST_CALLBACKS.clear()
    if hasattr(bpy.types.WindowManager, 'axismeld_menubar_set'):
        del bpy.types.WindowManager.axismeld_menubar_set


classes = ((AXISMELD_OT_menubar_execute, AXISMELD_MT_workspace_menu_sets) +
           tuple(_menu_class(key) for key in _MENU_NAMES) +
           tuple(_set_menu_class(key) for key in _SET_LABELS))

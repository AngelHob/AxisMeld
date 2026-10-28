# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Navigate native Properties without changing scene data, pins or layouts."""
from . import menubar_runtime

# Matches buttons_context_path_modifier in space_buttons/buttons_context.cc.
# In particular EMPTY has a native Modifier context; ARMATURE and META do not.
_MODIFIER_TYPES = frozenset({'EMPTY', 'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE',
                             'GREASEPENCIL', 'CURVES', 'POINTCLOUD', 'VOLUME'})
REASONS = {
    'target': 'Unknown property navigation target',
    'background': 'Property navigation requires the graphical application',
    'source': 'Property navigation requires a live 3D viewport in the source window',
    'selection': 'Requires an active selected object in the source view layer',
    'modifier': 'The active object has no native Modifier Properties context',
    'editor': 'No visible unpinned or same-object-pinned Properties editor in this window',
    'unavailable': 'Property navigation source or editor is unavailable',
}
_ERRORS = (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError)


def _plan(context, target):
    import bpy
    if target not in {'OBJECT', 'MODIFIER'}:
        return None, REASONS['target']
    if bpy.app.background:
        return None, REASONS['background']
    source = menubar_runtime.resolve_source(context)
    if source is None or not menubar_runtime._same(source.view_layer, context.view_layer):
        return None, REASONS['source']
    obj = source.view_layer.objects.active
    if obj is None or not obj.select_get(view_layer=source.view_layer):
        return None, REASONS['selection']
    if target == 'MODIFIER' and obj.type not in _MODIFIER_TYPES:
        return None, REASONS['modifier']
    candidates = []
    for area in source.screen.areas:
        if (area.type != 'PROPERTIES' or not menubar_runtime._visible(area) or
                not menubar_runtime._regions(area)):
            continue
        space = area.spaces.active
        # Native buttons_context_path uses pinid as its root even if the UI
        # SB_PIN_CONTEXT flag is off. A flag-only "unpin" is not unpinned RNA.
        if ((space.pin_id is None and not space.use_pin_id) or
                menubar_runtime._same(space.pin_id, obj)):
            candidates.append(area)
    current = getattr(context, 'area', None)
    area = next((item for item in candidates if menubar_runtime._same(item, current)), None)
    if area is None and candidates:
        area = min(candidates, key=menubar_runtime._order)
    if area is None:
        return None, REASONS['editor']
    return (source, area), ''


def available(context, target):
    """Read eligibility only; selection, mode and pin state are never repaired."""
    try:
        plan, reason = _plan(context, target)
        return plan is not None, reason
    except _ERRORS:
        return False, REASONS['unavailable']


def run(context, target):
    """Change only a compatible editor's tab/search, restoring both on failure."""
    import bpy
    try:
        plan, _reason = _plan(context, target)
        if plan is None:
            return {'CANCELLED'}
        source, area = plan
        space = area.spaces.active
        previous_context, previous_search = space.context, space.search_filter
    except _ERRORS:
        return {'CANCELLED'}
    try:
        with bpy.context.temp_override(window=source.window, area=area,
                                       region=menubar_runtime._regions(area)[0],
                                       scene=source.scene, view_layer=source.view_layer):
            space.context = target
            space.search_filter = ''
            if space.context != target or space.search_filter:
                raise RuntimeError('Properties navigation did not apply')
        return {'FINISHED'}
    except _ERRORS:
        # RNA may reject a write after applying an earlier field. Restore each
        # independently so one unavailable field cannot prevent the other.
        for field, value in (('context', previous_context), ('search_filter', previous_search)):
            try:
                setattr(space, field, value)
            except _ERRORS:
                pass
        return {'CANCELLED'}

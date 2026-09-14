# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded Common adapters. Each compound geometry operation owns exactly one undo."""
import bpy
from bpy.props import EnumProperty, StringProperty, FloatVectorProperty
from bpy.types import Operator
from mathutils import Matrix, Vector

from .modeling_common import ALL, SETTINGS, SPECS


def _object_mode(context):
    return bool(context.mode == 'OBJECT' and context.scene and context.scene.is_editable)


def _selected(context):
    return tuple(context.selected_objects)


def _editable(objects):
    return bool(objects) and all(obj.is_editable for obj in objects)


def _has_animation(obj):
    data = obj.animation_data
    return bool(data and (data.drivers or data.action or data.nla_tracks))


def _object_selection(context):
    return _object_mode(context) and _editable(_selected(context))


def _restore_selection(context, selected, active):
    context.view_layer.update()
    for obj in context.view_layer.objects:
        if obj is not None:
            obj.select_set(obj in selected)
    context.view_layer.objects.active = active


def _parent_state(objects):
    return {obj: (obj.parent, obj.parent_type, obj.parent_bone, obj.matrix_parent_inverse.copy(),
                  obj.matrix_basis.copy()) for obj in objects}


def _restore_parents(states):
    for obj, (parent, kind, bone, inverse, basis) in states.items():
        obj.parent = parent
        obj.parent_type = kind
        obj.parent_bone = bone
        obj.matrix_parent_inverse = inverse
        obj.matrix_basis = basis


def _plain_parentable(objects):
    return all(not obj.constraints and (obj.parent is None or
               (obj.parent_type == 'OBJECT' and abs(obj.parent.matrix_world.determinant()) > 1e-10))
               for obj in objects)


class AXISMELD_OT_m3_group(Operator):
    bl_idname = 'axismeld.m3_group'
    bl_label = 'Group Objects'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (_object_selection(context) and context.scene.collection.is_editable and
                _plain_parentable(_selected(context)))

    def execute(self, context):
        selected = _selected(context)
        active = context.view_layer.objects.active
        selected_set = set(selected)
        roots = []
        for obj in selected:
            parent = obj.parent
            while parent is not None and parent not in selected_set:
                parent = parent.parent
            if parent is None:
                roots.append(obj)
        states = _parent_state(roots)
        parent = roots[0].parent
        if any(obj.parent != parent for obj in roots):
            parent = None
        group = None
        try:
            group = bpy.data.objects.new('Group', None)
            group.empty_display_type = 'PLAIN_AXES'
            context.scene.collection.objects.link(group)
            group.parent = parent
            center = sum((obj.matrix_world.translation for obj in roots), Vector()) / len(roots)
            group_world = Matrix.Translation(center)
            group.matrix_parent_inverse = parent.matrix_world.inverted_safe() if parent else Matrix.Identity(4)
            group.matrix_basis = group_world
            for obj in roots:
                parent_transform = obj.parent.matrix_world @ obj.matrix_parent_inverse if obj.parent else Matrix.Identity(4)
                obj.parent = group
                obj.parent_type = 'OBJECT'
                obj.matrix_parent_inverse = group_world.inverted() @ parent_transform
            _restore_selection(context, {group}, group)
        except Exception as error:
            _restore_parents(states)
            if group is not None:
                bpy.data.objects.remove(group, do_unlink=True)
            _restore_selection(context, set(selected), active)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


def _ungroupable(context):
    selected = _selected(context)
    return (_object_mode(context) and _editable(selected) and
            all(obj.type == 'EMPTY' and obj.instance_type == 'NONE' and obj.children for obj in selected) and
            all(child.is_editable for group in selected for child in group.children) and
            _plain_parentable(child for group in selected for child in group.children) and
            _ungroup_matrices_supported(selected))


def _matrix_has_shear(matrix):
    location, rotation, scale = matrix.decompose()
    restored = Matrix.LocRotScale(location, rotation, scale)
    return any(abs(matrix[row][column] - restored[row][column]) > 1e-5
               for row in range(3) for column in range(3))


def _ungroup_matrices_supported(groups):
    # Blender unparented objects can store only TRS. Refuse an operation that
    # would require discarding existing shear when no surviving parent remains.
    groups = set(groups)
    for group in groups:
        for child in group.children:
            if child in groups:
                continue
            parent = child.parent
            while parent in groups:
                parent = parent.parent
            if parent is not None and abs(parent.matrix_world.determinant()) <= 1e-10:
                return False
            if parent is None and _matrix_has_shear(child.matrix_world):
                return False
    return True


class AXISMELD_OT_m3_ungroup(Operator):
    bl_idname = 'axismeld.m3_ungroup'
    bl_label = 'Ungroup Empty Parents'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _ungroupable(context)

    def execute(self, context):
        groups = set(_selected(context))
        children = {child for group in groups for child in group.children if child not in groups}
        states = _parent_state(children)
        try:
            # All targets were validated before edits; detach before deleting any parent.
            for child in children:
                parent = child.parent
                while parent in groups:
                    parent = parent.parent
                world = child.matrix_world.copy()
                parent_transform = child.parent.matrix_world @ child.matrix_parent_inverse
                child.parent = parent
                child.parent_type = 'OBJECT'
                if parent:
                    child.matrix_parent_inverse = parent.matrix_world.inverted() @ parent_transform
                else:
                    # Parent inverse is ignored without a parent. Exact shear is not
                    # representable as object TRS; such targets are rejected by poll.
                    child.matrix_parent_inverse = Matrix.Identity(4)
                    child.matrix_world = world
        except Exception as error:
            _restore_parents(states)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        for group in groups:
            bpy.data.objects.remove(group, do_unlink=True)
        active = sorted(children, key=lambda obj: obj.name)[0] if children else None
        _restore_selection(context, children, active)
        return {'FINISHED'}


class AXISMELD_OT_m3_match(Operator):
    bl_idname = 'axismeld.m3_match'
    bl_label = 'Match or Reset Transforms'
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=[(key, label, '') for key, label in (
        ('ALL', 'All'), ('LOCATION', 'Location'), ('ROTATION', 'Rotation'), ('SCALE', 'Scale'), ('RESET', 'Reset'))])

    @classmethod
    def poll(cls, context):
        return _object_selection(context)

    def execute(self, context):
        if not _match_poll(context, self.action):
            return {'CANCELLED'}
        objects = _selected(context)
        target = context.view_layer.objects.active
        if self.action != 'RESET' and (target not in objects or len(objects) < 2):
            return {'CANCELLED'}
        before = {obj: obj.matrix_basis.copy() for obj in objects}
        try:
            if self.action == 'RESET':
                for obj in objects:
                    obj.location = (0.0, 0.0, 0.0)
                    if obj.rotation_mode == 'QUATERNION':
                        obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
                    elif obj.rotation_mode == 'AXIS_ANGLE':
                        obj.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
                    else:
                        obj.rotation_euler = (0.0, 0.0, 0.0)
                    obj.scale = (1.0, 1.0, 1.0)
            else:
                target_world = target.matrix_world.copy()
                target_loc, target_rot, target_scale = target_world.decompose()
                for obj in objects:
                    if obj == target:
                        continue
                    if self.action == 'ALL':
                        obj.matrix_world = target_world
                    elif self.action == 'LOCATION':
                        world = obj.matrix_world.copy()
                        world.translation = target_loc
                        obj.matrix_world = world
                    else:
                        loc, rot, scale = obj.matrix_world.decompose()
                        obj.matrix_world = Matrix.LocRotScale(
                            target_loc if self.action == 'LOCATION' else loc,
                            target_rot if self.action == 'ROTATION' else rot,
                            target_scale if self.action == 'SCALE' else scale)
        except Exception as error:
            for obj, matrix in before.items():
                obj.matrix_basis = matrix
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


def _match_poll(context, action):
    if not _object_selection(context):
        return False
    objects = _selected(context)
    if any(obj.constraints or (obj.animation_data and obj.animation_data.drivers) for obj in objects):
        return False
    if action == 'RESET':
        return True
    target = context.active_object
    if target not in objects or len(objects) < 2:
        return False
    target_world = target.matrix_world
    target_location, target_rotation, target_scale = target_world.decompose()
    for obj in objects:
        if obj == target:
            continue
        if obj.parent and (obj.parent_type != 'OBJECT' or abs(obj.parent.matrix_world.determinant()) <= 1e-10):
            return False
        if action == 'LOCATION':
            continue
        if action == 'ALL':
            desired = target_world
        else:
            location, rotation, scale = obj.matrix_world.decompose()
            desired = Matrix.LocRotScale(location, target_rotation if action == 'ROTATION' else rotation,
                                        target_scale if action == 'SCALE' else scale)
        parent_transform = obj.parent.matrix_world @ obj.matrix_parent_inverse if obj.parent else Matrix.Identity(4)
        if abs(parent_transform.determinant()) <= 1e-10 or _matrix_has_shear(parent_transform.inverted() @ desired):
            return False
    return True


def _copy_objects():
    return bpy.ops.view3d.copybuffer('EXEC_DEFAULT', False)


class AXISMELD_OT_m3_cut(Operator):
    bl_idname = 'axismeld.m3_cut'
    bl_label = 'Cut Objects'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _object_selection(context) and bpy.ops.view3d.copybuffer.poll() and bpy.ops.object.delete.poll()

    def execute(self, _context):
        # No delete is attempted if the clipboard operation failed or was cancelled.
        if _copy_objects() != {'FINISHED'}:
            return {'CANCELLED'}
        return bpy.ops.object.delete('EXEC_DEFAULT', False, use_global=False)


def _last_duplicate(context):
    operators = context.window_manager.operators
    return bool(operators and operators[-1].bl_idname in {
        'OBJECT_OT_duplicate_move', 'MESH_OT_duplicate_move', 'CURVE_OT_duplicate_move'})


class AXISMELD_OT_m3_duplicate_repeat(Operator):
    bl_idname = 'axismeld.m3_duplicate_repeat'
    bl_label = 'Repeat Duplicate Transform'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return _last_duplicate(context) and bpy.ops.screen.repeat_last.poll()

    def invoke(self, _context, _event):
        return bpy.ops.screen.repeat_last('INVOKE_DEFAULT', False)


class AXISMELD_OT_m3_delete_components(Operator):
    bl_idname = 'axismeld.m3_delete_components'
    bl_label = 'Delete Components'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode in {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE'}

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            mode = context.tool_settings.mesh_select_mode
            kind = 'FACE' if mode[2] else ('EDGE' if mode[1] else 'VERT')
            return bpy.ops.mesh.delete('EXEC_DEFAULT', False, type=kind)
        return bpy.ops.curve.delete('EXEC_DEFAULT', False, type='VERT')


class AXISMELD_OT_m3_select(Operator):
    bl_idname = 'axismeld.m3_select'
    bl_label = 'Select Object Collection'
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=[(key, key.title(), '') for key in ('HIERARCHY', 'GEOMETRY', 'IMAGE', 'ASSETS')])

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.view_layer is not None

    def execute(self, context):
        if self.action == 'HIERARCHY':
            targets = set(_selected(context))
            stack = list(targets)
            while stack:
                for child in stack.pop().children:
                    if child not in targets:
                        targets.add(child)
                        stack.append(child)
        else:
            predicates = {
                'GEOMETRY': lambda obj: obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'},
                'IMAGE': lambda obj: obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE',
                'ASSETS': lambda obj: obj.asset_data is not None,
            }
            targets = {obj for obj in context.view_layer.objects if predicates[self.action](obj)}
        for obj in context.view_layer.objects:
            if obj.visible_get(view_layer=context.view_layer) and not obj.hide_select:
                obj.select_set(obj in targets)
        return {'FINISHED'}


def _setting_owner(context, owner):
    if owner == 'TOOLS':
        return context.tool_settings
    space = context.space_data
    if not space or space.type != 'VIEW_3D':
        return None
    return {'SPACE': space, 'OVERLAY': space.overlay, 'SHADING': space.shading}[owner]


def _setting_available(context, identifier):
    if identifier == 'display.xray':
        return bool(context.space_data and context.space_data.type == 'VIEW_3D')
    owner, attribute, _value, _kind = SETTINGS[identifier]
    target = _setting_owner(context, owner)
    return target is not None and hasattr(target, attribute)


def command_state(context, identifier):
    if identifier == 'display.xray' and _setting_available(context, identifier):
        shading = context.space_data.shading
        return ('checkbox', shading.show_xray_wireframe if shading.type == 'WIREFRAME' else shading.show_xray)
    if identifier not in SETTINGS or not _setting_available(context, identifier):
        return None
    owner, attribute, value, kind = SETTINGS[identifier]
    if kind is None:
        return None  # Explicit On/Off actions are ordinary rows, not toggle indicators.
    current = getattr(_setting_owner(context, owner), attribute)
    expected = set(value) if isinstance(value, tuple) else value
    return (kind, bool(current) if value is None else current == expected)


class AXISMELD_OT_m3_setting(Operator):
    bl_idname = 'axismeld.m3_setting'
    bl_label = 'Modeling Viewport Setting'
    bl_options = {'INTERNAL'}

    action: EnumProperty(items=[(key, key, '') for key in (*SETTINGS, 'display.xray')])

    @classmethod
    def poll(cls, context):
        return context.mode in ALL and context.tool_settings is not None

    def execute(self, context):
        if not _setting_available(context, self.action):
            return {'CANCELLED'}
        if self.action == 'display.xray':
            target = context.space_data.shading
            attribute = 'show_xray_wireframe' if target.type == 'WIREFRAME' else 'show_xray'
            setattr(target, attribute, not getattr(target, attribute))
        else:
            owner, attribute, value, _kind = SETTINGS[self.action]
            target = _setting_owner(context, owner)
            setattr(target, attribute, not getattr(target, attribute) if value is None else (
                set(value) if isinstance(value, tuple) else value))
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


CREATORS = {
    'ICOSPHERE': ('mesh.primitive_ico_sphere_add', {}),
    'GRID': ('mesh.primitive_grid_add', {}),
    'CIRCLE': ('mesh.primitive_circle_add', {'fill_type': 'NOTHING'}),
    'MONKEY': ('mesh.primitive_monkey_add', {}),
    'PYRAMID': ('mesh.primitive_cone_add', {'vertices': 4, 'radius2': 0.0}),
    'PRISM': ('mesh.primitive_cone_add', {'vertices': 3, 'radius1': 1.0, 'radius2': 1.0}),
    'CURVE_BEZIER': ('curve.primitive_bezier_curve_add', {}),
    'CURVE_BEZIER_CIRCLE': ('curve.primitive_bezier_circle_add', {}),
    'CURVE_NURBS': ('curve.primitive_nurbs_curve_add', {}),
    'CURVE_NURBS_CIRCLE': ('curve.primitive_nurbs_circle_add', {}),
    'CURVE_PATH': ('curve.primitive_nurbs_path_add', {}),
    **{'SURFACE_' + name.upper(): ('surface.primitive_nurbs_surface_' + name + '_add', {})
       for name in ('curve', 'circle', 'surface', 'cylinder', 'sphere', 'torus')},
    'LOCATOR': ('object.empty_add', {'type': 'PLAIN_AXES'}),
    'EMPTY_GROUP': ('object.empty_add', {'type': 'PLAIN_AXES'}),
    'TEXT': ('object.text_add', {}),
    'LATTICE': ('object.add', {'type': 'LATTICE'}),
}
for _kind, _native in (('SPHERE', 'mesh.primitive_uv_sphere_add'), ('CUBE', 'mesh.primitive_cube_add'),
                       ('CYLINDER', 'mesh.primitive_cylinder_add'), ('CONE', 'mesh.primitive_cone_add'),
                       ('PLANE', 'mesh.primitive_plane_add'), ('TORUS', 'mesh.primitive_torus_add')):
    CREATORS['SUBDIV_' + _kind] = (_native, {})


def _operator(identifier):
    namespace, name = identifier.split('.')
    return getattr(getattr(bpy.ops, namespace), name)


def _creation_poll(context, kind):
    return _object_mode(context) and _operator(CREATORS[kind][0]).poll()


class AXISMELD_OT_m3_create(Operator):
    bl_idname = 'axismeld.m3_create'
    bl_label = 'Create Blender Primitive'
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=[(key, key.replace('_', ' ').title(), '') for key in CREATORS])

    @classmethod
    def poll(cls, context):
        return _object_mode(context)

    def execute(self, context):
        if not _creation_poll(context, self.kind):
            return {'CANCELLED'}
        identifier, values = CREATORS[self.kind]
        properties = dict(values, align='WORLD', location=tuple(context.scene.cursor.location),
                          rotation=(0.0, 0.0, 0.0))
        operation = _operator(identifier)
        if 'enter_editmode' in operation.get_rna_type().properties:
            properties['enter_editmode'] = False
        result = operation('EXEC_DEFAULT', False, **properties)
        if result == {'FINISHED'} and self.kind == 'EMPTY_GROUP':
            context.active_object.name = 'Group'
        if result == {'FINISHED'} and self.kind.startswith('SUBDIV_'):
            modifier = context.active_object.modifiers.new('Subdivision', 'SUBSURF')
            modifier.levels = 2
            modifier.render_levels = 2
        return result


_hidden_batches = []
_template_batch = frozenset()
_TEMPLATE = '_axismeld_m3_template'


def _selected_flags(context):
    return tuple(obj for obj in context.view_layer.objects if obj.select_get(view_layer=context.view_layer))


def _last_hidden(context):
    if not _hidden_batches:
        return ()
    uids = _hidden_batches[-1]
    return tuple(obj for obj in context.view_layer.objects if obj.session_uid in uids and obj.hide_get())


def _template_targets(context):
    selected = _selected_flags(context)
    if selected:
        return tuple(obj for obj in selected if _TEMPLATE in obj)
    # hide_select removes viewport selection. Retain the exact last batch so the
    # inverse command is available immediately without selecting restricted objects.
    return tuple(obj for obj in context.view_layer.objects if obj.session_uid in _template_batch and _TEMPLATE in obj)


def _display_poll(context, action):
    if not _object_mode(context):
        return False
    if action == 'SHOW_LAST':
        return _editable(_last_hidden(context))
    if action == 'SHOW_ALL':
        return any(obj.hide_get() and obj.is_editable for obj in context.view_layer.objects)
    if action in {'HIDE_ALL', 'HIDE_GEOMETRY', 'SHOW_GEOMETRY', 'HIDE_DEFORMED', 'SHOW_DEFORMED'}:
        return _editable(_display_batch(context, action))
    objects = _selected_flags(context)
    if action == 'HIDE_UNSELECTED':
        return bool(objects) and all(obj.is_editable for obj in context.view_layer.objects if obj not in objects)
    if action == 'UNTEMPLATE':
        return _editable(_template_targets(context))
    return _editable(objects)


def _display_batch(context, action):
    objects = tuple(context.view_layer.objects)
    if action == 'HIDE_ALL':
        return objects
    geometry = tuple(obj for obj in objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'})
    if action.endswith('GEOMETRY'):
        return geometry
    deformers = {'ARMATURE', 'CAST', 'CORRECTIVE_SMOOTH', 'CURVE', 'DISPLACE', 'HOOK', 'LAPLACIANDEFORM',
                 'LATTICE', 'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'SURFACE_DEFORM', 'WARP', 'WAVE'}
    return tuple(obj for obj in geometry if any(mod.type in deformers and mod.show_viewport for mod in obj.modifiers))


class AXISMELD_OT_m3_object_display(Operator):
    bl_idname = 'axismeld.m3_object_display'
    bl_label = 'Object Display'
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=[(key, key.replace('_', ' ').title(), '') for key in (
        'HIDE_SELECTED', 'HIDE_UNSELECTED', 'SHOW_SELECTED', 'SHOW_ALL', 'SHOW_LAST', 'TOGGLE',
        'TEMPLATE', 'UNTEMPLATE', 'BOUNDS', 'SOLID', 'WIRE', 'TEXTURED', 'IN_FRONT', 'AXES',
        'HIDE_ALL', 'HIDE_GEOMETRY', 'SHOW_GEOMETRY', 'HIDE_DEFORMED', 'SHOW_DEFORMED')])

    @classmethod
    def poll(cls, context):
        return _object_mode(context)

    def execute(self, context):
        global _template_batch
        if not _display_poll(context, self.action):
            return {'CANCELLED'}
        selected = _selected_flags(context)
        active = context.view_layer.objects.active
        objects = selected
        if self.action == 'HIDE_UNSELECTED':
            objects = tuple(obj for obj in context.view_layer.objects if obj not in selected)
        elif self.action == 'SHOW_ALL':
            objects = tuple(obj for obj in context.view_layer.objects if obj.is_editable and obj.hide_get())
        elif self.action == 'SHOW_LAST':
            objects = _last_hidden(context)
        elif self.action == 'UNTEMPLATE':
            objects = _template_targets(context)
        elif self.action in {'HIDE_ALL', 'HIDE_GEOMETRY', 'SHOW_GEOMETRY', 'HIDE_DEFORMED', 'SHOW_DEFORMED'}:
            objects = _display_batch(context, self.action)
        before = {obj: (obj.hide_get(), obj.hide_select, obj.display_type, obj.show_in_front, obj.show_axis,
                        dict(obj[_TEMPLATE]) if _TEMPLATE in obj else None) for obj in objects}
        hide = self.action.startswith('HIDE_') or (self.action == 'TOGGLE' and not all(obj.hide_get() for obj in objects))
        try:
            for obj in objects:
                if self.action.startswith(('HIDE_', 'SHOW_')) or self.action == 'TOGGLE':
                    obj.hide_set(hide)
                elif self.action == 'TEMPLATE':
                    if _TEMPLATE not in obj:
                        obj[_TEMPLATE] = {'hide_select': int(obj.hide_select), 'display_type': obj.display_type}
                    obj.hide_select = True
                    obj.display_type = 'WIRE'
                elif self.action == 'UNTEMPLATE' and _TEMPLATE in obj:
                    saved = obj[_TEMPLATE]
                    obj.hide_select = bool(saved['hide_select'])
                    obj.display_type = saved['display_type']
                    del obj[_TEMPLATE]
                elif self.action == 'IN_FRONT':
                    obj.show_in_front = not obj.show_in_front
                elif self.action == 'AXES':
                    obj.show_axis = not obj.show_axis
                elif self.action in {'BOUNDS', 'SOLID', 'WIRE', 'TEXTURED'}:
                    obj.display_type = self.action
        except Exception as error:
            for obj, (hidden, selectable, display, front, axes, saved) in before.items():
                obj.hide_set(hidden)
                obj.hide_select = selectable
                obj.display_type = display
                obj.show_in_front = front
                obj.show_axis = axes
                if saved is None:
                    if _TEMPLATE in obj:
                        del obj[_TEMPLATE]
                else:
                    obj[_TEMPLATE] = saved
            _restore_selection(context, set(selected), active)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        if hide:
            _hidden_batches.append(frozenset(obj.session_uid for obj in objects if not before[obj][0]))
            del _hidden_batches[:-20]
        elif self.action == 'SHOW_LAST':
            _hidden_batches.pop()
        elif self.action == 'TEMPLATE':
            _template_batch = frozenset(obj.session_uid for obj in objects)
        return {'FINISHED'}


class AXISMELD_OT_m3_selection_convert(Operator):
    bl_idname = 'axismeld.m3_selection_convert'
    bl_label = 'Convert Mesh Selection'
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(items=[(key, key.replace('_', ' ').title(), '') for key in (
        'CONTAINED_EDGES', 'CONTAINED_FACES', 'VERTEX_PERIMETER', 'FACE_PERIMETER', 'MULTI', 'SURFACE_CV_BOUNDARY')])

    @classmethod
    def poll(cls, context):
        return context.mode in {'EDIT_MESH', 'EDIT_SURFACE'} and context.edit_object.data.is_editable

    def execute(self, context):
        if self.action == 'SURFACE_CV_BOUNDARY':
            if context.mode != 'EDIT_SURFACE':
                return {'CANCELLED'}
            for obj in context.objects_in_mode_unique_data:
                for spline in obj.data.splines:
                    width, height = spline.point_count_u, spline.point_count_v
                    selected = {index for index, point in enumerate(spline.points) if point.select and not point.hide}
                    for index, point in enumerate(spline.points):
                        u, v = index % width, index // width
                        neighbors = []
                        for du, dv in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nu, nv = u + du, v + dv
                            if spline.use_cyclic_u:
                                nu %= width
                            if spline.use_cyclic_v:
                                nv %= height
                            neighbors.append(nv * width + nu if 0 <= nu < width and 0 <= nv < height else -1)
                        point.select = index in selected and any(neighbor not in selected for neighbor in neighbors)
            return {'FINISHED'}
        if context.mode != 'EDIT_MESH':
            return {'CANCELLED'}
        if self.action == 'MULTI':
            context.tool_settings.mesh_select_mode = (True, True, True)
            return {'FINISHED'}
        import bmesh
        for obj in context.objects_in_mode_unique_data:
            bm = bmesh.from_edit_mesh(obj.data)
            verts = {vert for vert in bm.verts if vert.select and not vert.hide}
            edges = {edge for edge in bm.edges if edge.select and not edge.hide}
            faces = {face for face in bm.faces if face.select and not face.hide}
            if self.action == 'CONTAINED_EDGES':
                chosen = {edge for edge in bm.edges if not edge.hide and all(vert in verts for vert in edge.verts)}
                domain = 'EDGE'
            elif self.action == 'CONTAINED_FACES':
                chosen = {face for face in bm.faces if not face.hide and all(vert in verts for vert in face.verts)}
                domain = 'FACE'
            else:
                boundary = {edge for edge in bm.edges if not edge.hide and
                            any(face in faces for face in edge.link_faces) and
                            (len(edge.link_faces) == 1 or any(face not in faces for face in edge.link_faces))}
                if self.action == 'FACE_PERIMETER':
                    chosen = {face for edge in boundary for face in edge.link_faces if face in faces}
                    domain = 'FACE'
                else:
                    chosen = {vert for edge in boundary for vert in edge.verts}
                    if not faces:
                        chosen = {vert for vert in verts if vert.is_boundary or
                                  any(edge.other_vert(vert) not in verts for edge in vert.link_edges)}
                    domain = 'VERT'
            for elements in (bm.faces, bm.edges, bm.verts):
                for element in elements:
                    element.select_set(False)
            bm.select_mode = {domain}
            for element in chosen:
                element.select_set(True)
            bm.select_flush_mode()
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        context.tool_settings.mesh_select_mode = tuple(domain == key for key in ('VERT', 'EDGE', 'FACE'))
        return {'FINISHED'}


class AXISMELD_OT_m3_rotation_order(Operator):
    bl_idname = 'axismeld.m3_rotation_order'
    bl_label = 'Set Rotation Order'
    bl_options = {'REGISTER', 'UNDO'}
    order: EnumProperty(items=[(key, key, '') for key in ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX')])

    @classmethod
    def poll(cls, context):
        return _object_selection(context)

    def execute(self, context):
        before = {obj: (obj.rotation_mode, obj.matrix_basis.copy()) for obj in _selected(context)}
        try:
            for obj, (_order, matrix) in before.items():
                obj.rotation_mode = self.order
                obj.matrix_basis = matrix
        except Exception as error:
            for obj, (order, matrix) in before.items():
                obj.rotation_mode = order
                obj.matrix_basis = matrix
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class AXISMELD_OT_m3_wire_color(Operator):
    bl_idname = 'axismeld.m3_wire_color'
    bl_label = 'Set Object Wireframe Color'
    bl_options = {'REGISTER', 'UNDO'}
    color: FloatVectorProperty(name='Color', subtype='COLOR', size=4, min=0.0, max=1.0,
                               default=(0.8, 0.8, 0.8, 1.0))

    @classmethod
    def poll(cls, context):
        return _object_selection(context) and context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def invoke(self, context, _event):
        self.color = context.active_object.color if context.active_object else _selected(context)[0].color
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        before = {obj: tuple(obj.color) for obj in _selected(context)}
        shading = context.space_data.shading
        old_source = shading.wireframe_color_type
        try:
            for obj in before:
                obj.color = self.color
            shading.wireframe_color_type = 'OBJECT'
        except Exception as error:
            for obj, color in before.items():
                obj.color = color
            shading.wireframe_color_type = old_source
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


def _custom_keys(context):
    obj = context.active_object
    return tuple(key for key in obj.keys() if not key.startswith('_') and
                 isinstance(obj[key], (str, float, int, bool))) if obj else ()


def _property_items(_self, context):
    return [(key, key, '') for key in _custom_keys(context)]


class AXISMELD_OT_m3_custom_property(Operator):
    bl_idname = 'axismeld.m3_custom_property'
    bl_label = 'Object Custom Property'
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(items=[(key, key.title(), '') for key in ('ADD', 'EDIT', 'DELETE')])
    property: EnumProperty(name='Property', items=_property_items)
    name: StringProperty(name='Name', default='Property')
    value: StringProperty(name='Value', default='0')
    kind: EnumProperty(name='Type', items=[(key, key.title(), '') for key in ('FLOAT', 'INTEGER', 'BOOLEAN', 'STRING')])

    @classmethod
    def poll(cls, context):
        return _object_mode(context) and context.active_object is not None and context.active_object.is_editable

    def invoke(self, context, _event):
        keys = _custom_keys(context)
        if self.action != 'ADD':
            if not keys:
                return {'CANCELLED'}
            self.property = keys[0]
            self.name = keys[0]
            self.value = str(context.active_object[keys[0]])
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context):
        if self.action != 'ADD':
            self.layout.prop(self, 'property')
        if self.action != 'DELETE':
            self.layout.prop(self, 'name')
            self.layout.prop(self, 'kind')
            self.layout.prop(self, 'value')

    def execute(self, context):
        obj = context.active_object
        if self.action != 'ADD' and self.property not in _custom_keys(context):
            return {'CANCELLED'}
        if self.action == 'DELETE':
            del obj[self.property]
            return {'FINISHED'}
        if not self.name.strip() or self.name.startswith('_') or (self.name in obj and
                (self.action == 'ADD' or self.name != self.property)):
            self.report({'ERROR'}, 'Choose a unique non-reserved property name')
            return {'CANCELLED'}
        try:
            if self.kind == 'BOOLEAN' and self.value.lower() not in {'true', 'false', '1', '0'}:
                raise ValueError('Boolean value must be true, false, 1 or 0')
            value = {'FLOAT': float, 'INTEGER': int, 'STRING': str,
                     'BOOLEAN': lambda item: item.lower() in {'true', '1'}}[self.kind](self.value)
        except ValueError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        obj[self.name] = value
        if self.action == 'EDIT' and self.name != self.property:
            del obj[self.property]
        return {'FINISHED'}


def _bounds_poll(context):
    return _object_selection(context) and all(obj.type == 'MESH' and not obj.modifiers and obj.data.is_editable
                                               for obj in _selected(context))


class AXISMELD_OT_m3_bounds(Operator):
    bl_idname = 'axismeld.m3_bounds'
    bl_label = 'Geometry to Bounding Box'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _bounds_poll(context)

    def execute(self, context):
        before = {obj: obj.data for obj in _selected(context)}
        created = []
        try:
            # Construct every replacement before mutating any object.
            for obj in before:
                mesh = bpy.data.meshes.new(obj.data.name + ' Bounds')
                created.append((obj, mesh))
                mesh.from_pydata(list(obj.bound_box), [], ((0, 1, 2, 3), (4, 7, 6, 5),
                    (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)))
                mesh.update()
            for obj, mesh in created:
                obj.data = mesh
        except Exception as error:
            for obj, data in before.items():
                obj.data = data
            for _obj, mesh in created:
                bpy.data.meshes.remove(mesh)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


# Source: source/blender/modifiers/intern/MOD_*.cc ModifierTypeType::OnlyDeform.
# Mesh-compatible entries only. Shape keys are rejected separately, because
# applying topology before them cannot preserve indexed key coordinates.
ONLY_DEFORM = frozenset({'ARMATURE', 'CAST', 'CLOTH', 'COLLISION', 'CORRECTIVE_SMOOTH', 'CURVE',
    'DISPLACE', 'HOOK', 'LAPLACIANDEFORM', 'LAPLACIANSMOOTH', 'LATTICE', 'MESH_CACHE', 'MESH_DEFORM',
    'PARTICLE_SYSTEM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'SOFT_BODY', 'SURFACE', 'SURFACE_DEFORM',
    'WARP', 'WAVE'})


def _bake_targets(context, action):
    objects = context.scene.objects if action.startswith('ALL') else _selected(context)
    return tuple(obj for obj in objects if obj.type == 'MESH' and obj.modifiers)


def _bake_names(obj, action):
    return tuple(modifier.name for modifier in obj.modifiers
                 if not action.endswith('NON_DEFORM') or modifier.type not in ONLY_DEFORM)


def _bake_poll(context, action):
    if not _object_mode(context) or not context.scene.collection.is_editable:
        return False
    objects = _bake_targets(context, action)
    if not _editable(objects):
        return False
    has_target = False
    for obj in objects:
        if (not obj.data.is_editable or obj.data.users > 1 or obj.data.shape_keys or obj.override_library or
                _has_animation(obj)):
            return False
        deform_seen = False
        for modifier in obj.modifiers:
            is_deform = modifier.type in ONLY_DEFORM
            if action.endswith('NON_DEFORM') and is_deform:
                deform_seen = True
                continue
            if deform_seen or not modifier.show_viewport or modifier.type == 'COLLISION':
                return False
            has_target = True
    return has_target


def _apply_modifier(context, obj, name):
    with context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj]):
        return bpy.ops.object.modifier_apply('EXEC_DEFAULT', False, modifier=name)


def _restore_modifier_stack(context, obj, backup):
    with context.temp_override(object=backup, active_object=backup,
            selected_objects=[backup, obj], selected_editable_objects=[backup, obj]):
        for modifier in backup.modifiers:
            # Commit only removes modifiers. Preserve every surviving instance,
            # including bound deformer caches and unsupported native-copy types.
            if obj.modifiers.get(modifier.name) is not None:
                continue
            if modifier.type == 'HOOK':
                restored = obj.modifiers.new(modifier.name, 'HOOK')
                _restore_hook(modifier, restored)
            else:
                result = bpy.ops.object.modifier_copy_to_selected('EXEC_DEFAULT', False, modifier=modifier.name)
                if result != {'FINISHED'} or obj.modifiers.get(modifier.name) is None:
                    raise RuntimeError('Could not restore modifier: ' + modifier.name)
    with context.temp_override(object=obj, active_object=obj,
            selected_objects=[obj], selected_editable_objects=[obj]):
        for index, modifier in enumerate(backup.modifiers):
            if obj.modifiers.find(modifier.name) != index:
                result = bpy.ops.object.modifier_move_to_index('EXEC_DEFAULT', False,
                    modifier=modifier.name, index=index)
                if result != {'FINISHED'}:
                    raise RuntimeError('Could not restore modifier order: ' + modifier.name)


def _restore_hook(source, target):
    # Fixed Hook RNA only; native copy-to-selected explicitly excludes Hook.
    # Set target/bone before inverse, because their setters recalculate inverse.
    for name in ('object', 'subtarget', 'strength', 'falloff_type', 'falloff_radius',
                 'use_falloff_uniform', 'vertex_group', 'invert_vertex_group',
                 'show_viewport', 'show_render', 'show_in_editmode', 'show_on_cage', 'show_expanded'):
        setattr(target, name, getattr(source, name))
    target.center = source.center.copy()
    target.matrix_inverse = source.matrix_inverse.copy()
    target.vertex_indices_set(tuple(source.vertex_indices))
    source_mapping, target_mapping = source.falloff_curve, target.falloff_curve
    for name in ('use_clip', 'clip_min_x', 'clip_min_y', 'clip_max_x', 'clip_max_y', 'extend'):
        setattr(target_mapping, name, getattr(source_mapping, name))
    target_mapping.initialize()
    for old_curve, new_curve in zip(source_mapping.curves, target_mapping.curves):
        while len(new_curve.points) > 2:
            new_curve.points.remove(new_curve.points[-2])
        new_curve.points[0].location = old_curve.points[0].location
        new_curve.points[-1].location = old_curve.points[-1].location
        for point in list(old_curve.points)[1:-1]:
            new_curve.points.new(*point.location)
        for old_point, new_point in zip(old_curve.points, new_curve.points):
            new_point.handle_type = old_point.handle_type
    target_mapping.update()


def _remove_modifier(obj, modifier):
    obj.modifiers.remove(modifier)


class AXISMELD_OT_m3_bake_history(Operator):
    bl_idname = 'axismeld.m3_bake_history'
    bl_label = 'Bake Mesh Modifier History'
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(items=[(key, key.replace('_', ' ').title(), '') for key in (
        'SELECTED', 'ALL', 'SELECTED_NON_DEFORM', 'ALL_NON_DEFORM')])

    @classmethod
    def poll(cls, context):
        return _object_mode(context)

    def execute(self, context):
        if not _bake_poll(context, self.action):
            return {'CANCELLED'}
        selected = set(_selected_flags(context))
        active = context.view_layer.objects.active
        prepared = []
        backups = []
        committed = []
        try:
            # Every native application happens on an isolated copy first. A
            # cancelled/failed Apply leaves all original objects and stacks intact.
            for obj in _bake_targets(context, self.action):
                names = _bake_names(obj, self.action)
                if not names:
                    continue
                duplicate = obj.copy()
                duplicate.data = obj.data.copy()
                prepared.append((obj, duplicate, names, obj.data))
                backup = obj.copy()
                backups.append((obj, backup))
                context.scene.collection.objects.link(duplicate)
                context.scene.collection.objects.link(backup)
                context.view_layer.update()
                for name in names:
                    if _apply_modifier(context, duplicate, name) != {'FINISHED'}:
                        raise RuntimeError('Native modifier Apply cancelled: ' + name)
                    if duplicate.modifiers.get(name) is not None:
                        raise RuntimeError('Native modifier Apply did not bake: ' + name)
            # All linked/read-only/shape-key and operator checks have succeeded.
            for obj, duplicate, names, _original_data in prepared:
                committed.append(obj)
                obj.data = duplicate.data
                for name in names:
                    _remove_modifier(obj, obj.modifiers[name])
        except Exception as error:
            # Preparation failure occurs before originals are changed. The commit
            # consists only of assignments/removals on prevalidated local IDs.
            for obj, _duplicate, _names, original_data in prepared:
                if obj.data != original_data:
                    obj.data = original_data
            for obj, backup in backups:
                if obj not in committed:
                    continue
                _restore_modifier_stack(context, obj, backup)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        finally:
            for _obj, backup in backups:
                bpy.data.objects.remove(backup, do_unlink=True)
            for _obj, duplicate, _names, _original_data in prepared:
                data = duplicate.data
                bpy.data.objects.remove(duplicate, do_unlink=True)
                if data.users == 0:
                    bpy.data.meshes.remove(data)
            _restore_selection(context, selected, active)
        return {'FINISHED'}


DELETE_FAMILIES = {'DELETE_HOOK': frozenset({'HOOK'}), 'DELETE_LATTICE': frozenset({'LATTICE'}),
                   'DELETE_NONLINEAR': frozenset({'SIMPLE_DEFORM', 'WAVE'}), 'DELETE_CURVE': frozenset({'CURVE'})}


def _family_targets(context, action):
    kinds = DELETE_FAMILIES[action]
    return tuple(obj for obj in context.scene.objects if any(modifier.type in kinds for modifier in obj.modifiers))


def _path_source_supported(source):
    # A static standalone curve has no dependency back into a future follower.
    # Reject parent/constraint/modifier, bevel/taper-object and animation networks
    # instead of trying to infer arbitrary dependency-graph paths in Python.
    data = source.data
    return (source.parent is None and not source.constraints and not source.modifiers and
            not _has_animation(source) and not _has_animation(data) and
            data.bevel_object is None and data.taper_object is None)


def _relationship_poll(context, action):
    if not _object_mode(context):
        return False
    if action in DELETE_FAMILIES:
        objects = _family_targets(context, action)
        return (context.scene.collection.is_editable and _editable(objects) and
                all(not obj.override_library and not _has_animation(obj)
                    for obj in objects))
    source = context.active_object
    selected = _selected(context)
    if not source or source not in selected or len(selected) < 2 or not _editable(selected):
        return False
    targets = tuple(obj for obj in selected if obj != source)
    if action == 'PATH':
        return (source.type == 'CURVE' and source.data.is_editable and len(source.data.splines) == 1 and
                _path_source_supported(source) and _path_has_length(source) and
                all(not obj.parent and not obj.constraints and
                    not any(abs(value) > 1e-8 for value in obj.delta_location) and
                    not _has_animation(obj) for obj in targets))
    if action == 'REPLACE':
        return source.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'LATTICE'} and all(
            obj.type == source.type and not obj.override_library for obj in targets)
    keys = _custom_keys(context)
    return bool(keys) and all(not obj.override_library and all(key not in obj or
        isinstance(obj[key], (str, float, int, bool)) for key in keys) for obj in targets)


def _path_has_length(source):
    spline = source.data.splines[0]
    points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
    positions = [Vector(point.co[:3]) for point in points]
    return len(positions) > 1 and any((point - positions[0]).length > 1e-8 for point in positions[1:])


class AXISMELD_OT_m3_relationship(Operator):
    bl_idname = 'axismeld.m3_relationship'
    bl_label = 'Modeling Object Relationship'
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(items=[(key, key.replace('_', ' ').title(), '')
                               for key in ('PATH', 'REPLACE', 'TRANSFER', *DELETE_FAMILIES)])

    @classmethod
    def poll(cls, context):
        return _object_mode(context)

    def execute(self, context):
        if not _relationship_poll(context, self.action):
            return {'CANCELLED'}
        if self.action in DELETE_FAMILIES:
            return self._delete_family(context)
        source = context.active_object
        targets = tuple(sorted((obj for obj in _selected(context) if obj != source), key=lambda obj: obj.name))
        if self.action == 'REPLACE':
            original = {obj: obj.data for obj in targets}
            try:
                result = bpy.ops.object.make_links_data('EXEC_DEFAULT', False, type='OBDATA')
                if result != {'FINISHED'}:
                    raise RuntimeError('Native Link Object Data cancelled')
                return result
            except Exception as error:
                for obj, data in original.items():
                    obj.data = data
                self.report({'ERROR'}, str(error))
                return {'CANCELLED'}
        if self.action == 'TRANSFER':
            keys = _custom_keys(context)
            values = {key: source[key] for key in keys}
            original = {obj: {key: (key in obj, obj.get(key)) for key in keys} for obj in targets}
            try:
                for obj in targets:
                    for key, value in values.items():
                        obj[key] = value
            except Exception as error:
                for obj, properties in original.items():
                    for key, (existed, value) in properties.items():
                        if existed:
                            obj[key] = value
                        elif key in obj:
                            del obj[key]
                self.report({'ERROR'}, str(error))
                return {'CANCELLED'}
            return {'FINISHED'}
        original = {obj: obj.matrix_basis.copy() for obj in targets}
        original_path = source.data.use_path
        created = []
        try:
            source.data.use_path = True
            for index, obj in enumerate(targets):
                constraint = obj.constraints.new('FOLLOW_PATH')
                created.append((obj, constraint))
                constraint.name = 'AxisMeld Curve Placement'
                constraint.target = source
                constraint.use_fixed_location = True
                denominator = len(targets) if source.data.splines[0].use_cyclic_u else max(1, len(targets) - 1)
                constraint.offset_factor = index / denominator
                constraint.use_curve_follow = True
                constraint.forward_axis = 'FORWARD_X'
                constraint.up_axis = 'UP_Z'
                obj.location = (0.0, 0.0, 0.0)
            context.view_layer.update()
        except Exception as error:
            for obj, constraint in created:
                obj.constraints.remove(constraint)
            for obj, matrix in original.items():
                obj.matrix_basis = matrix
            source.data.use_path = original_path
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}

    def _delete_family(self, context):
        selected, active = set(_selected_flags(context)), context.active_object
        backups = []
        try:
            for obj in _family_targets(context, self.action):
                backup = obj.copy()
                backups.append((obj, backup))
                context.scene.collection.objects.link(backup)
            for obj, _backup in backups:
                for modifier in tuple(obj.modifiers):
                    if modifier.type in DELETE_FAMILIES[self.action]:
                        _remove_modifier(obj, modifier)
        except Exception as error:
            for obj, backup in backups:
                _restore_modifier_stack(context, obj, backup)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        finally:
            for _obj, backup in backups:
                bpy.data.objects.remove(backup, do_unlink=True)
            _restore_selection(context, selected, active)
        return {'FINISHED'}


class AXISMELD_OT_m3_frame_all(Operator):
    bl_idname = 'axismeld.m3_frame_all'
    bl_label = 'Frame All in All Panes'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.area and context.area.type == 'VIEW_3D')

    def execute(self, context):
        regions = [region for region in context.area.regions if region.type == 'WINDOW']
        for region in regions:
            with context.temp_override(region=region):
                result = bpy.ops.view3d.view_all('EXEC_DEFAULT', False, center=False)
                if result != {'FINISHED'}:
                    return result
        return {'FINISHED'}


COMMAND_POLLS = {
    'edit.group': lambda context: AXISMELD_OT_m3_group.poll(context),
    'edit.ungroup': _ungroupable,
    'edit.cut_objects': lambda context: AXISMELD_OT_m3_cut.poll(context),
    'edit.duplicate_repeat_transform': _last_duplicate,
    'selection.hierarchy': lambda context: bool(_selected(context)),
    'selection.control_points': lambda context: context.active_object is not None and
        context.active_object.type in {'CURVE', 'SURFACE', 'LATTICE'} and context.active_object.data.is_editable,
    'selection.face_path': lambda context: context.mode == 'EDIT_MESH' and context.tool_settings.mesh_select_mode[2],
    'object.geometry_to_bounds': _bounds_poll,
    'object.property_edit': lambda context: bool(_custom_keys(context)),
    'object.property_delete': lambda context: bool(_custom_keys(context)),
    'transform.reset_all': lambda context: _match_poll(context, 'RESET'),
}
for identifier in (*SETTINGS, 'display.xray'):
    COMMAND_POLLS[identifier] = lambda context, identifier=identifier: _setting_available(context, identifier)
for identifier in ('display.nurbs_hull', 'display.nurbs_rough', 'display.nurbs_medium', 'display.nurbs_fine'):
    COMMAND_POLLS[identifier] = lambda context: (context.mode == 'OBJECT' and context.active_object is not None
        and context.active_object.type in {'CURVE', 'SURFACE'} and context.active_object.data.is_editable)
for spec in SPECS:
    call = spec.calls[0]
    values = dict(call.kwargs)
    if call.operator == 'axismeld.m3_create':
        COMMAND_POLLS[spec.id] = lambda context, kind=values['kind']: _creation_poll(context, kind)
    elif call.operator == 'axismeld.m3_object_display':
        COMMAND_POLLS[spec.id] = lambda context, action=values['action']: _display_poll(context, action)
    elif call.operator == 'axismeld.m3_match' and values['action'] != 'RESET':
        COMMAND_POLLS[spec.id] = lambda context, action=values['action']: _match_poll(context, action)
    elif call.operator == 'axismeld.m3_bake_history':
        COMMAND_POLLS[spec.id] = lambda context, action=values['action']: _bake_poll(context, action)
    elif call.operator == 'axismeld.m3_relationship':
        COMMAND_POLLS[spec.id] = lambda context, action=values['action']: _relationship_poll(context, action)
    elif call.operator == 'mesh.select_similar':
        kind = values['type']
        domain = 0 if kind.startswith('VERT_') else (1 if kind.startswith('EDGE_') else 2)
        COMMAND_POLLS[spec.id] = lambda context, domain=domain: (context.mode == 'EDIT_MESH' and
                                                                context.tool_settings.mesh_select_mode[domain])


classes = (AXISMELD_OT_m3_group, AXISMELD_OT_m3_ungroup, AXISMELD_OT_m3_match, AXISMELD_OT_m3_cut,
           AXISMELD_OT_m3_duplicate_repeat, AXISMELD_OT_m3_delete_components, AXISMELD_OT_m3_select,
           AXISMELD_OT_m3_setting, AXISMELD_OT_m3_create, AXISMELD_OT_m3_object_display, AXISMELD_OT_m3_frame_all,
           AXISMELD_OT_m3_selection_convert, AXISMELD_OT_m3_rotation_order, AXISMELD_OT_m3_custom_property,
           AXISMELD_OT_m3_bounds, AXISMELD_OT_m3_wire_color, AXISMELD_OT_m3_bake_history,
           AXISMELD_OT_m3_relationship)

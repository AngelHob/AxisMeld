# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded curve and deformation operations; each composite owns one undo."""
import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from mathutils import Matrix, Vector


def _source(context):
    obj = context.active_object
    return obj if obj and obj.type == 'MESH' and obj.mode == 'OBJECT' and obj.is_editable and obj.data.is_editable else None


def _targets(context, kind):
    return [obj for obj in context.selected_objects
            if obj != context.active_object and obj.type == kind]


def _closed_mesh(obj):
    counts = {}
    for face in obj.data.polygons:
        for edge in face.edge_keys:
            edge = tuple(sorted(edge))
            counts[edge] = counts.get(edge, 0) + 1
    return bool(counts) and all(count == 2 for count in counts.values())


def _can_deform(context, kind):
    obj = _source(context)
    if not obj or not obj.data.vertices:
        return False
    if kind == 'CURVE':
        return len(_targets(context, 'CURVE')) == 1 and bool(_targets(context, 'CURVE')[0].data.splines)
    if kind in {'SHRINKWRAP', 'SURFACE_DEFORM', 'MESH_DEFORM'}:
        targets = _targets(context, 'MESH')
        if len(targets) != 1 or not targets[0].data.polygons:
            return False
        if kind == 'MESH_DEFORM':
            if not _closed_mesh(targets[0]) or abs(targets[0].matrix_world.determinant()) < 1e-10:
                return False
            # Reject obviously invalid cages before allocating/binding. Native binding
            # remains authoritative for non-convex geometry inside these bounds.
            matrix = targets[0].matrix_world.inverted() @ obj.matrix_world
            bounds = [Vector(v) for v in targets[0].bound_box]
            return all(min(v[i] for v in bounds) <= (matrix @ vertex.co)[i] <= max(v[i] for v in bounds)
                       for vertex in obj.data.vertices for i in range(3))
        return True
    if kind == 'WARP':
        targets = _targets(context, 'EMPTY')
        return len(targets) == 2 and targets[0].matrix_world != targets[1].matrix_world
    if kind == 'LAPLACIANDEFORM':
        selected = sum(v.select for v in obj.data.vertices)
        return bool(obj.data.polygons) and 0 < selected < len(obj.data.vertices)
    return True


KINDS = ('BEND', 'TWIST', 'TAPER', 'STRETCH', 'WAVE', 'LATTICE', 'SHRINKWRAP',
         'CURVE', 'SURFACE_DEFORM', 'MESH_DEFORM', 'CORRECTIVE_SMOOTH',
         'LAPLACIANDEFORM', 'SMOOTH', 'LAPLACIANSMOOTH', 'CAST', 'DISPLACE', 'WARP', 'SOLIDIFY')


class AXISMELD_OT_m3_deform(bpy.types.Operator):
    bl_idname = 'axismeld.m3_deform'
    bl_label = 'Configure Deformation'
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=[(item, item.replace('_', ' ').title(), '') for item in KINDS])
    strength: FloatProperty(name='Strength / Angle', default=0.5, min=-10.0, max=10.0)
    iterations: IntProperty(name='Iterations', default=3, min=1, max=100)
    axis: EnumProperty(items=[(axis, axis, '') for axis in 'XYZ'], default='Z')

    @classmethod
    def poll(cls, context):
        return bool(_source(context))

    def execute(self, context):
        if not _can_deform(context, self.kind):
            self.report({'WARNING'}, 'Select an editable mesh and the required valid target(s)')
            return {'CANCELLED'}
        obj = context.active_object
        modifier = None
        cage = cage_data = texture = group = None
        coordinates = None
        try:
            modifier = obj.modifiers.new('AxisMeld ' + self.kind.replace('_', ' ').title(),
                                         'SIMPLE_DEFORM' if self.kind in {'BEND', 'TWIST', 'TAPER', 'STRETCH'} else self.kind)
            if self.kind in {'BEND', 'TWIST', 'TAPER', 'STRETCH'}:
                modifier.deform_method = self.kind
                modifier.deform_axis = self.axis
                modifier.factor = self.strength
            elif self.kind == 'WAVE':
                modifier.height = self.strength
                modifier.width = 1.5
                modifier.speed = 0.0
                modifier.narrowness = 1.0
            elif self.kind == 'LATTICE':
                cage_data = bpy.data.lattices.new('AxisMeld Lattice')
                cage_data.points_u = cage_data.points_v = cage_data.points_w = 3
                cage = bpy.data.objects.new('AxisMeld Lattice', cage_data)
                context.collection.objects.link(cage)
                bounds = [Vector(v) for v in obj.bound_box]
                low = Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
                high = Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
                # Parenting preserves inherited shear, which assigning matrix_world
                # to a parentless object would lose during TRS decomposition.
                cage.parent = obj
                cage.matrix_parent_inverse = Matrix.Identity(4)
                cage.matrix_basis = (Matrix.Translation((low + high) * 0.5) @
                                     Matrix.Diagonal(tuple(max(high[i] - low[i], 0.01) * 1.05
                                                           for i in range(3)) + (1.0,)))
                modifier.object = cage
                for point in cage_data.points:
                    point.co_deform.x += self.strength * (point.co_deform.z + 0.5) ** 2
            elif self.kind in {'SHRINKWRAP', 'SURFACE_DEFORM', 'MESH_DEFORM'}:
                target = _targets(context, 'MESH')[0]
                if self.kind == 'SHRINKWRAP':
                    modifier.target = target
                    modifier.wrap_method = 'NEAREST_SURFACEPOINT'
                    modifier.offset = 0.05
                else:
                    if self.kind == 'MESH_DEFORM':
                        modifier.object = target
                        modifier.precision = 4
                        bind = bpy.ops.object.meshdeform_bind
                    else:
                        modifier.target = target
                        bind = bpy.ops.object.surfacedeform_bind
                    context.view_layer.update()
                    result = bind('EXEC_DEFAULT', False, modifier=modifier.name)
                    if result != {'FINISHED'} or not modifier.is_bound:
                        raise ValueError('Native binding failed; check target topology and enclosure')
            elif self.kind == 'CURVE':
                modifier.object = _targets(context, 'CURVE')[0]
                modifier.deform_axis = 'POS_' + self.axis
            elif self.kind == 'CORRECTIVE_SMOOTH':
                modifier.factor = self.strength
                modifier.iterations = self.iterations
                modifier.rest_source = 'BIND'
                modifier.use_only_smooth = True
                context.view_layer.update()
                result = bpy.ops.object.correctivesmooth_bind('EXEC_DEFAULT', False, modifier=modifier.name)
                if result != {'FINISHED'} or not modifier.is_bind:
                    raise ValueError('Corrective Smooth binding failed')
            elif self.kind == 'LAPLACIANDEFORM':
                group = obj.vertex_groups.new(name='AxisMeld Anchors')
                indices = [v.index for v in obj.data.vertices if v.select]
                group.add(indices, 1.0, 'REPLACE')
                modifier.vertex_group = group.name
                modifier.iterations = self.iterations
                context.view_layer.update()
                result = bpy.ops.object.laplaciandeform_bind('EXEC_DEFAULT', False, modifier=modifier.name)
                if result != {'FINISHED'} or not modifier.is_bind:
                    raise ValueError('Laplacian binding failed')
                coordinates = [v.co.copy() for v in obj.data.vertices]
                for index in indices:
                    obj.data.vertices[index].co.z += self.strength
                obj.data.update()
            elif self.kind in {'SMOOTH', 'LAPLACIANSMOOTH'}:
                if self.kind == 'SMOOTH':
                    modifier.factor = self.strength
                else:
                    modifier.lambda_factor = self.strength
                    modifier.use_volume_preserve = False
                modifier.iterations = self.iterations
            elif self.kind == 'CAST':
                modifier.factor = self.strength
                modifier.cast_type = 'SPHERE'
                modifier.radius = 1.0
            elif self.kind == 'DISPLACE':
                texture = bpy.data.textures.new('AxisMeld Deformation Noise', type='CLOUDS')
                # Default .25 samples the regular .5-unit Cube grid at noise lattice
                # points, all exactly midlevel .5. Avoid a neutral default result.
                texture.noise_scale = 0.37
                modifier.texture = texture
                modifier.texture_coords = 'GLOBAL'
                modifier.strength = self.strength
            elif self.kind == 'WARP':
                targets = sorted(_targets(context, 'EMPTY'), key=lambda item: item.name)
                modifier.object_from, modifier.object_to = targets
                modifier.strength = self.strength
                modifier.falloff_type = 'NONE'
            elif self.kind == 'SOLIDIFY':
                modifier.thickness = self.strength * 0.2
            context.view_layer.update()
            return {'FINISHED'}
        except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
            if coordinates:
                for vertex, co in zip(obj.data.vertices, coordinates):
                    vertex.co = co
            if modifier:
                obj.modifiers.remove(modifier)
            if group:
                obj.vertex_groups.remove(group)
            if cage:
                bpy.data.objects.remove(cage, do_unlink=True)
            if cage_data:
                bpy.data.lattices.remove(cage_data)
            if texture:
                bpy.data.textures.remove(texture)
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}


class AXISMELD_OT_m3_curve_geometry(bpy.types.Operator):
    bl_idname = 'axismeld.m3_curve_geometry'
    bl_label = 'Curve Geometry'
    bl_options = {'REGISTER', 'UNDO'}
    kind: EnumProperty(items=[('OFFSET', '2D Offset', ''), ('BEVEL', 'Round Bevel', ''), ('PROFILE', 'Selected Curve Profile', ''),
                              ('RESOLUTION', 'Sampling Resolution', '')])
    amount: FloatProperty(default=0.15, min=0.0, max=100.0)
    resolution: IntProperty(default=24, min=1, max=1024)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bool(obj and obj.is_editable and obj.type in {'CURVE', 'SURFACE'} and obj.data.is_editable)

    def execute(self, context):
        data = context.active_object.data
        if self.kind == 'OFFSET':
            if context.active_object.type != 'CURVE' or data.dimensions != '2D':
                return {'CANCELLED'}
            data.offset = self.amount
        elif self.kind == 'BEVEL':
            data.bevel_mode = 'ROUND'
            data.bevel_depth = self.amount
            data.bevel_resolution = 3
        elif self.kind == 'PROFILE':
            if not _can_profile(context):
                return {'CANCELLED'}
            data.bevel_mode = 'OBJECT'
            data.bevel_object = _targets(context, 'CURVE')[0]
        else:
            data.resolution_u = data.resolution_v = self.resolution
            for spline in data.splines:
                spline.resolution_u = spline.resolution_v = self.resolution
        return {'FINISHED'}


def _shape_targets(context):
    obj = _source(context)
    targets = _targets(context, 'MESH') if obj else []
    if not targets or abs(obj.matrix_world.determinant()) < 1e-10 or (obj.data.shape_keys and not obj.data.shape_keys.use_relative):
        return False
    topology = tuple(tuple(face.vertices) for face in obj.data.polygons)
    edges = tuple(tuple(edge.vertices) for edge in obj.data.edges)
    return all(len(target.data.vertices) == len(obj.data.vertices) and
               tuple(tuple(face.vertices) for face in target.data.polygons) == topology and
               tuple(tuple(edge.vertices) for edge in target.data.edges) == edges for target in targets)


def _can_profile(context):
    obj = context.active_object
    targets = _targets(context, 'CURVE')
    return bool(obj and obj.type == 'CURVE' and obj.data.is_editable and len(targets) == 1
                and targets[0].data.splines and targets[0].data.bevel_object != obj)


class AXISMELD_OT_m3_shape_targets(bpy.types.Operator):
    bl_idname = 'axismeld.m3_shape_targets'
    bl_label = 'Selected Meshes to Shape Keys'
    bl_options = {'REGISTER', 'UNDO'}
    value: FloatProperty(name='First Target Influence', default=1.0, min=0.0, max=1.0)

    @classmethod
    def poll(cls, context):
        return bool(_shape_targets(context))

    def execute(self, context):
        if not self.poll(context):
            return {'CANCELLED'}
        obj = context.active_object
        created = []
        try:
            if not obj.data.shape_keys:
                created.append(obj.shape_key_add(name='Basis', from_mix=False))
            for index, target in enumerate(_targets(context, 'MESH')):
                key = obj.shape_key_add(name=target.name, from_mix=False)
                created.append(key)
                matrix = obj.matrix_world.inverted() @ target.matrix_world
                for point, vertex in zip(key.data, target.data.vertices):
                    point.co = matrix @ vertex.co
                key.value = self.value if index == 0 else 0.0
            obj.active_shape_key_index = len(obj.data.shape_keys.key_blocks) - len(_targets(context, 'MESH'))
            return {'FINISHED'}
        except (RuntimeError, ValueError) as exc:
            for key in reversed(created):
                obj.shape_key_remove(key)
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}


def _selected_points(context):
    obj = context.active_object
    if not obj or not obj.is_editable or obj.mode != 'EDIT' or not obj.data or not obj.data.is_editable:
        return False
    if obj.type == 'MESH':
        import bmesh
        return any(v.select for v in bmesh.from_edit_mesh(obj.data).verts)
    if obj.type in {'CURVE', 'SURFACE'}:
        return any(p.select_control_point for s in obj.data.splines for p in s.bezier_points) or any(
            p.select for s in obj.data.splines for p in s.points)
    return False


class AXISMELD_OT_m3_hook(bpy.types.Operator):
    bl_idname = 'axismeld.m3_hook'
    bl_label = 'Hook Selected Points'
    bl_options = {'REGISTER', 'UNDO'}
    offset: FloatProperty(name='Controller Z Offset', default=0.25, min=-100.0, max=100.0)

    @classmethod
    def poll(cls, context):
        return _selected_points(context)

    def execute(self, context):
        obj = context.active_object
        if not self.poll(context):
            return {'CANCELLED'}
        before = {modifier.as_pointer() for modifier in obj.modifiers}
        objects_before = {item.as_pointer() for item in bpy.data.objects}
        try:
            result = bpy.ops.object.hook_add_newob('EXEC_DEFAULT', False)
            hook = next((m for m in obj.modifiers if m.as_pointer() not in before and m.type == 'HOOK'), None)
            if result != {'FINISHED'} or not hook or not hook.object:
                raise ValueError('Native Hook did not create a valid controller')
            hook.object.location.z += self.offset
            return {'FINISHED'}
        except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
            for modifier in tuple(obj.modifiers):
                if modifier.as_pointer() not in before:
                    obj.modifiers.remove(modifier)
            for item in tuple(bpy.data.objects):
                if item.as_pointer() not in objects_before:
                    bpy.data.objects.remove(item, do_unlink=True)
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}


def _modifier(context, kind):
    obj = context.active_object
    if not obj or not obj.is_editable:
        return None
    active = obj.modifiers.active
    if active and active.type == kind:
        return active
    modifiers = [m for m in obj.modifiers if m.type == kind]
    return modifiers[0] if len(modifiers) == 1 else None


def _can_manage(context, kind, action):
    allowed = {'HOOK': {'ASSIGN', 'RESET'}, 'SHRINKWRAP': {'SET_TARGET', 'CLEAR_TARGET'},
               'CURVE': {'SET_TARGET'}, 'SURFACE_DEFORM': {'BIND', 'UNBIND'},
               'MESH_DEFORM': {'BIND', 'UNBIND'}}
    if action not in allowed.get(kind, set()):
        return False
    modifier = _modifier(context, kind)
    if not modifier:
        return False
    if kind == 'HOOK':
        return _selected_points(context) and bool(modifier.object)
    if not _source(context):
        return False
    if action == 'SET_TARGET':
        return _can_deform(context, kind)
    if action == 'CLEAR_TARGET':
        return bool(modifier.target) if kind == 'SHRINKWRAP' else False
    if action == 'UNBIND':
        return bool(modifier.is_bound)
    target = modifier.object if kind == 'MESH_DEFORM' else modifier.target
    return bool(target and target.type == 'MESH' and target.data.polygons and not modifier.is_bound)


class AXISMELD_OT_m3_deform_manage(bpy.types.Operator):
    bl_idname = 'axismeld.m3_deform_manage'
    bl_label = 'Deformation Target / Binding'
    bl_options = {'REGISTER', 'UNDO'}
    kind: EnumProperty(items=[(kind, kind.replace('_', ' ').title(), '')
                             for kind in ('SHRINKWRAP', 'SURFACE_DEFORM', 'MESH_DEFORM', 'CURVE', 'HOOK')])
    action: EnumProperty(items=[(action, action.replace('_', ' ').title(), '')
                               for action in ('SET_TARGET', 'CLEAR_TARGET', 'BIND', 'UNBIND', 'ASSIGN', 'RESET')])

    @classmethod
    def poll(cls, context):
        return bool(context.active_object and context.active_object.is_editable)

    def execute(self, context):
        if not _can_manage(context, self.kind, self.action):
            return {'CANCELLED'}
        modifier = _modifier(context, self.kind)
        if self.kind == 'HOOK':
            operator = bpy.ops.object.hook_assign if self.action == 'ASSIGN' else bpy.ops.object.hook_reset
            return operator('EXEC_DEFAULT', False, modifier=modifier.name)
        if self.action == 'CLEAR_TARGET':
            modifier.target = None
        elif self.action == 'SET_TARGET':
            target = _targets(context, 'CURVE' if self.kind == 'CURVE' else 'MESH')[0]
            if self.kind == 'CURVE':
                modifier.object = target
            elif self.kind == 'SHRINKWRAP':
                modifier.target = target
            else:
                return {'CANCELLED'}
        else:
            bind = bpy.ops.object.meshdeform_bind if self.kind == 'MESH_DEFORM' else bpy.ops.object.surfacedeform_bind
            result = bind('EXEC_DEFAULT', False, modifier=modifier.name)
            if result != {'FINISHED'}:
                return {'CANCELLED'}
        return {'FINISHED'}


DEFORM_IDS = {'bend': 'BEND', 'twist': 'TWIST', 'taper': 'TAPER', 'stretch': 'STRETCH',
              'wave': 'WAVE', 'lattice': 'LATTICE', 'shrinkwrap': 'SHRINKWRAP', 'curve': 'CURVE',
              'surface_bind': 'SURFACE_DEFORM', 'mesh_bind': 'MESH_DEFORM',
              'corrective_smooth': 'CORRECTIVE_SMOOTH', 'laplacian': 'LAPLACIANDEFORM',
              'smooth': 'SMOOTH', 'laplacian_smooth': 'LAPLACIANSMOOTH', 'cast': 'CAST',
              'displace': 'DISPLACE', 'warp': 'WARP', 'solidify': 'SOLIDIFY'}
COMMAND_POLLS = {'deform.' + key: (lambda context, kind=kind: _can_deform(context, kind))
                 for key, kind in DEFORM_IDS.items()}
COMMAND_POLLS.update({
    'curve.pen': lambda c: bool(c.active_object and c.active_object.type == 'CURVE' and
                               c.active_object.is_editable and c.active_object.data.is_editable),
    'curve.draw': lambda c: bool(c.active_object and c.active_object.type == 'CURVE' and
                                c.active_object.is_editable and c.active_object.data.is_editable),
    'deform.shape_key_join': _shape_targets,
    'deform.hook_selected': _selected_points,
    'surface.sweep_profile': _can_profile,
    'curve.offset_geometry': lambda c: bool(c.active_object and c.active_object.type == 'CURVE'
                                            and c.active_object.data.is_editable and c.active_object.data.dimensions == '2D'),
})
for _id in ('auto', 'vector', 'aligned', 'free'):
    COMMAND_POLLS['curve.handle_' + _id] = lambda c: bool(c.active_object and c.active_object.type == 'CURVE' and
        _selected_points(c) and
        any(p.select_control_point or p.select_left_handle or p.select_right_handle
            for s in c.active_object.data.splines for p in s.bezier_points))
_selected_curve_ids = ('duplicate', 'attach_segments', 'detach', 'separate', 'open_close', 'extrude',
                       'subdivide', 'reverse', 'smooth', 'delete_points')
for _prefix in ('curve.', 'surface.'):
    for _id in _selected_curve_ids:
        COMMAND_POLLS[_prefix + _id] = _selected_points
for _id in ('spline_bezier', 'spline_nurbs', 'spline_poly', 'smooth_tilt', 'smooth_radius',
            'smooth_weight', 'tilt', 'clear_tilt', 'recalculate_handles', 'radius', 'weight',
            'decimate', 'dissolve_points', 'delete_segments'):
    COMMAND_POLLS['curve.' + _id] = _selected_points
COMMAND_POLLS['surface.open_close_v'] = _selected_points
COMMAND_POLLS['surface.revolve'] = lambda c: bool(c.active_object and c.active_object.type == 'SURFACE') and _selected_points(c) and any(
    s.type == 'NURBS' and s.point_count_v == 1 and any(p.select for p in s.points)
    for s in c.active_object.data.splines)
for _kind in ('surface', 'mesh'):
    for _action in ('bind', 'unbind'):
        COMMAND_POLLS['deform.' + _kind + '_' + _action + '_existing'] = (
            lambda c, kind=_kind.upper() + '_DEFORM', action=_action.upper(): _can_manage(c, kind, action))
for _id, _kind, _action in (
        ('shrinkwrap_target', 'SHRINKWRAP', 'SET_TARGET'),
        ('shrinkwrap_clear', 'SHRINKWRAP', 'CLEAR_TARGET'),
        ('curve_target', 'CURVE', 'SET_TARGET'), ('hook_assign', 'HOOK', 'ASSIGN'), ('hook_reset', 'HOOK', 'RESET')):
    COMMAND_POLLS['deform.' + _id] = lambda c, kind=_kind, action=_action: _can_manage(c, kind, action)
for _id in ('curve.bevel_geometry', 'curve.resolution', 'surface.resolution'):
    COMMAND_POLLS[_id] = lambda c, kind='SURFACE' if _id.startswith('surface') else 'CURVE': bool(
        c.active_object and c.active_object.type == kind and c.active_object.data.is_editable)
classes = (AXISMELD_OT_m3_deform, AXISMELD_OT_m3_curve_geometry,
           AXISMELD_OT_m3_shape_targets, AXISMELD_OT_m3_hook, AXISMELD_OT_m3_deform_manage)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded mesh operations. Only these fixed properties/targets can be changed."""
import math

import bpy
import bmesh
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, StringProperty
from bpy.types import Operator
from mathutils import Color


def _editable_mesh(context, modes=('OBJECT',)):
    obj = context.object
    return bool(context.mode in modes and context.scene and context.scene.is_editable and obj and
                obj.type == 'MESH' and obj.is_editable and obj.data.is_editable and
                obj.select_get() and obj.visible_get(view_layer=context.view_layer))


def _boolean_targets(context):
    if not _editable_mesh(context):
        return None
    selected = tuple(context.selected_objects)
    if len(selected) != 2 or context.object not in selected:
        return None
    if not all(obj.type == 'MESH' and obj.is_editable and obj.data.is_editable and
               obj.visible_get(view_layer=context.view_layer) and len(obj.data.polygons) and
               abs(obj.matrix_world.determinant()) > 1e-12 for obj in selected):
        return None
    return context.object, next(obj for obj in selected if obj != context.object)


def _depends_on(obj, target, visited=None):
    visited = set() if visited is None else visited
    if obj == target:
        return True
    if obj in visited:
        return False
    visited.add(obj)
    dependencies = [obj.parent] if obj.parent else []
    for owner in (*obj.modifiers, *obj.constraints):
        for prop in owner.bl_rna.properties:
            if prop.type == 'POINTER' and prop.fixed_type.identifier == 'Object':
                dependency = getattr(owner, prop.identifier, None)
                if dependency is not None:
                    dependencies.append(dependency)
        if owner.type == 'BOOLEAN' and getattr(owner, 'operand_type', '') == 'COLLECTION' and owner.collection:
            dependencies.extend(owner.collection.all_objects)
    return any(_depends_on(dependency, target, visited) for dependency in dependencies)


def _evaluated_mesh(context, obj, *, allow_empty=False):
    context.view_layer.update()
    evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        if mesh is None or (not allow_empty and not mesh.vertices):
            raise ValueError('The configured modifier produced no mesh geometry')
        if any(not math.isfinite(coordinate) for vertex in mesh.vertices for coordinate in vertex.co):
            raise ValueError('The configured modifier produced non-finite geometry')
    finally:
        evaluated.to_mesh_clear()


class AXISMELD_OT_m3_mesh_boolean(Operator):
    bl_idname = 'axismeld.m3_mesh_boolean'
    bl_label = 'Mesh Boolean'
    bl_options = {'REGISTER', 'UNDO'}

    operation: EnumProperty(items=[(value, label, '') for value, label in
                                  (('UNION', 'Union'), ('DIFFERENCE', 'Difference'),
                                   ('INTERSECT', 'Intersection'))], default='DIFFERENCE')
    reverse: BoolProperty(name='Other Minus Active', default=False)

    @classmethod
    def poll(cls, context):
        return _boolean_targets(context) is not None

    def execute(self, context):
        targets = _boolean_targets(context)
        if targets is None:
            self.report({'WARNING'}, 'Select exactly two visible editable meshes with faces')
            return {'CANCELLED'}
        target, operand = targets[::-1] if self.reverse else targets
        if _depends_on(operand, target):
            self.report({'WARNING'}, 'Boolean operand already depends on its result object')
            return {'CANCELLED'}
        modifier = None
        try:
            modifier = target.modifiers.new('AxisMeld Boolean', 'BOOLEAN')
            modifier.operation = self.operation
            modifier.object = operand
            modifier.solver = 'EXACT'
            _evaluated_mesh(context, target, allow_empty=True)
        except Exception as error:
            if modifier is not None:
                target.modifiers.remove(modifier)
            context.view_layer.update()
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


# Fixed modifier presets, not an arbitrary modifier/RNA path supplied by a profile.
_MODIFIERS = {
    'decimate': ('DECIMATE', {'ratio': .5}),
    'remesh': ('REMESH', {'mode': 'VOXEL', 'voxel_size': .1}),
    'subsurf': ('SUBSURF', {'levels': 1, 'render_levels': 1}),
    'mirror': ('MIRROR', {'use_axis': (True, False, False), 'use_bisect_axis': (True, False, False),
                          'use_clip': True, 'use_mirror_merge': True}),
    'array': ('ARRAY', {'count': 2, 'relative_offset_displace': (1.0, 0.0, 0.0)}),
    'solidify': ('SOLIDIFY', {'thickness': .1}),
    'wireframe': ('WIREFRAME', {'thickness': .02}),
    'weld': ('WELD', {'merge_threshold': .0001}),
    'skin': ('SKIN', {}),
    'build': ('BUILD', {'frame_duration': 1.0}),
    'weighted_normal': ('WEIGHTED_NORMAL', {'keep_sharp': True, 'weight': 50}),
    'normal_edit': ('NORMAL_EDIT', {'mode': 'DIRECTIONAL', 'offset': (0.0, 0.0, 1.0)}),
}


class _MeshModifier(Operator):
    bl_options = {'REGISTER', 'UNDO'}
    modifier_key = ''

    @classmethod
    def poll(cls, context):
        if not _editable_mesh(context) or not context.object.data.vertices:
            return False
        mesh = context.object.data
        if cls.modifier_key == 'skin':
            return bool(mesh.edges) and not mesh.polygons and mesh.users == 1
        return bool(mesh.polygons)

    def execute(self, context):
        if not type(self).poll(context):
            self.report({'WARNING'}, 'Active mesh does not meet this modifier input requirements')
            return {'CANCELLED'}
        obj = context.object
        kind, properties = _MODIFIERS[self.modifier_key]
        modifier = None
        had_skin = bool(obj.data.skin_vertices)
        try:
            modifier = obj.modifiers.new('AxisMeld ' + self.modifier_key.replace('_', ' ').title(), kind)
            for attribute, value in properties.items():
                setattr(modifier, attribute, value)
            if kind == 'BUILD':
                modifier.frame_start = context.scene.frame_current - .5
            if kind == 'SKIN' and not obj.data.skin_vertices:
                # Native modifier creation owns the required skin-vertex layer.
                obj.modifiers.remove(modifier)
                modifier = None
                with context.temp_override(object=obj, active_object=obj,
                                           selected_objects=[obj], selected_editable_objects=[obj]):
                    result = bpy.ops.object.modifier_add('EXEC_DEFAULT', False, type='SKIN')
                if result != {'FINISHED'}:
                    raise ValueError('Native Skin modifier setup failed')
                modifier = obj.modifiers[-1]
            _evaluated_mesh(context, obj)
        except Exception as error:
            if modifier is not None:
                obj.modifiers.remove(modifier)
            if kind == 'SKIN' and not had_skin and obj.data.skin_vertices:
                with context.temp_override(object=obj, active_object=obj):
                    bpy.ops.mesh.customdata_skin_clear('EXEC_DEFAULT', False)
            context.view_layer.update()
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


_modifier_classes = tuple(type('AXISMELD_OT_m3_mesh_modifier_' + name, (_MeshModifier,), {
    'bl_idname': 'axismeld.m3_mesh_modifier_' + name,
    'bl_label': 'Mesh ' + name.replace('_', ' ').title() + ' Modifier',
    'modifier_key': name,
}) for name in _MODIFIERS)


_OVERLAYS = {
    'display.vertex_normals': 'show_vertex_normals',
    'display.split_normals': 'show_split_normals',
    'display.face_normals': 'show_face_normals',
    'display.edge_length': 'show_extra_edge_length',
    'display.edge_angle': 'show_extra_edge_angle',
    'display.face_area': 'show_extra_face_area',
    'display.face_angle': 'show_extra_face_angle',
    'display.crease_marks': 'show_edge_crease',
    'display.sharp_edges': 'show_edge_sharp',
    'display.face_centers': 'show_face_center',
    'display.component_indices': 'show_extra_indices',
}


def _view(context):
    return bool(context.area and context.area.type == 'VIEW_3D' and context.space_data and
                context.space_data.type == 'VIEW_3D')


class AXISMELD_OT_m3_mesh_overlay(Operator):
    bl_idname = 'axismeld.m3_mesh_overlay'
    bl_label = 'Mesh Viewport Overlay'
    bl_options = {'INTERNAL'}
    attribute: EnumProperty(items=[(name, name.replace('show_', '').replace('_', ' ').title(), '')
                                   for name in _OVERLAYS.values()])

    @classmethod
    def poll(cls, context):
        return _view(context)

    def execute(self, context):
        overlay = context.space_data.overlay
        setattr(overlay, self.attribute, not getattr(overlay, self.attribute))
        return {'FINISHED'}


class AXISMELD_OT_m3_normal_length(Operator):
    bl_idname = 'axismeld.m3_normal_length'
    bl_label = 'Normal Display Length'
    bl_options = {'INTERNAL'}
    length: FloatProperty(name='Length', default=.1, min=.00001, max=100000)

    @classmethod
    def poll(cls, context):
        return _view(context)

    def invoke(self, context, _event):
        self.length = context.space_data.overlay.normals_length
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        context.space_data.overlay.normals_length = self.length
        return {'FINISHED'}


def _edit_overlay(context):
    return _view(context) and _editable_mesh(context, ('EDIT_MESH',))


def _face_centers(context):
    return (_edit_overlay(context) and context.space_data.shading.type != 'WIREFRAME' and
            not context.space_data.shading.show_xray)


def _distortion(context):
    if not _edit_overlay(context):
        return False
    shading = context.space_data.shading
    xray = (shading.show_xray_wireframe and shading.xray_alpha_wireframe < 1.0
            if shading.type == 'WIREFRAME' else
            shading.show_xray and shading.xray_alpha < 1.0 if shading.type == 'SOLID' else False)
    return not xray


class AXISMELD_OT_m3_mesh_distortion(Operator):
    bl_idname = 'axismeld.m3_mesh_distortion'
    bl_label = 'Face Distortion Analysis'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return _distortion(context)

    def execute(self, context):
        overlay = context.space_data.overlay
        statvis = context.scene.tool_settings.statvis
        previous = overlay.show_statvis, statvis.type
        try:
            enabled = previous == (True, 'DISTORT')
            statvis.type = 'DISTORT'
            overlay.show_statvis = not enabled
        except (AttributeError, TypeError, ValueError, RuntimeError) as error:
            overlay.show_statvis, statvis.type = previous
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class AXISMELD_OT_m3_modeling_toolbar(Operator):
    bl_idname = 'axismeld.m3_modeling_toolbar'
    bl_label = 'Show Modeling Toolbar'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return _view(context)

    def execute(self, context):
        context.space_data.show_region_toolbar = not context.space_data.show_region_toolbar
        return {'FINISHED'}


def _active_color(context):
    return context.object.data.color_attributes.active_color


class _ColorAction(Operator):
    bl_options = {'REGISTER', 'UNDO'}
    action = ''
    name: StringProperty(name='Name', default='Color')
    domain: EnumProperty(name='Domain', items=[('POINT', 'Vertex', ''), ('CORNER', 'Face Corner', '')],
                         default='CORNER')
    data_type: EnumProperty(name='Storage', items=[('FLOAT_COLOR', 'Float Color', ''),
                                                  ('BYTE_COLOR', 'Byte Color', '')], default='FLOAT_COLOR')
    color: FloatVectorProperty(name='Color', subtype='COLOR', size=4, min=0, max=1,
                               default=(1, 1, 1, 1))

    @classmethod
    def poll(cls, context):
        if not _editable_mesh(context, ('OBJECT', 'EDIT_MESH') if cls.action == 'set' else ('OBJECT',)):
            return False
        active = _active_color(context)
        if cls.action == 'add':
            return True
        if active is None:
            return False
        if cls.action == 'set' and context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.object.data)
            elements = bm.verts if active.domain == 'POINT' else bm.faces
            return any(element.select and not element.hide for element in elements)
        return True

    def draw(self, context):
        if self.action == 'active':
            self.layout.prop_search(self, 'name', context.object.data, 'color_attributes')
        elif self.action in ('add', 'rename'):
            self.layout.prop(self, 'name')
        if self.action == 'add':
            self.layout.prop(self, 'domain')
            self.layout.prop(self, 'data_type')
        if self.action in ('add', 'set'):
            self.layout.prop(self, 'color')

    def invoke(self, context, _event):
        if self.action in ('rename', 'active'):
            self.name = _active_color(context).name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not type(self).poll(context):
            return {'CANCELLED'}
        mesh = context.object.data
        attributes = mesh.color_attributes
        active = attributes.active_color
        # Layer collection access can rebuild CustomData storage; keep identities,
        # not a borrowed layer pointer, across BMesh access or attribute creation.
        active_name = active.name if active is not None else None
        active_domain = active.domain if active is not None else None
        active_type = active.data_type if active is not None else None
        if self.action in ('add', 'rename') and not self.name.strip():
            self.report({'WARNING'}, 'A nonempty color attribute name is required')
            return {'CANCELLED'}
        if self.action == 'active':
            attribute = attributes.get(self.name)
            if attribute is None:
                return {'CANCELLED'}
            attributes.active_color = attribute
            return {'FINISHED'}
        if self.action == 'rename':
            active.name = self.name.strip()
            return {'FINISHED'}
        if self.action == 'remove':
            attributes.remove(active)
            return {'FINISHED'}
        created = None
        old_values = []
        try:
            if self.action == 'add':
                created = attributes.new(name=self.name.strip(), type=self.data_type, domain=self.domain)
                attributes.active_color = created
                values = created.data
                for value in values:
                    value.color = self.color
            elif context.mode == 'OBJECT':
                values = active.data
                old_values = [(value, tuple(value.color)) for value in values]
                for value in values:
                    value.color = self.color
            else:
                bm = bmesh.from_edit_mesh(mesh)
                layers = bm.verts.layers if active_domain == 'POINT' else bm.loops.layers
                layer = (layers.float_color if active_type == 'FLOAT_COLOR' else layers.color).get(active_name)
                if layer is None:
                    raise ValueError('Active edit color layer is unavailable')
                elements = ([v for v in bm.verts if v.select and not v.hide] if active_domain == 'POINT' else
                            [loop for face in bm.faces if face.select and not face.hide for loop in face.loops])
                if not elements:
                    raise ValueError('Select vertices or faces in the active color attribute domain')
                old_values = [(element, tuple(element[layer])) for element in elements]
                # RNA .color is scene-linear; BMesh byte-color layers expose stored
                # sRGB bytes. Float-color layers already use scene-linear values.
                color = ((*Color(self.color[:3]).from_scene_linear_to_srgb(), self.color[3])
                         if active_type == 'BYTE_COLOR' else self.color)
                for element in elements:
                    element[layer] = color
                bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
            mesh.update()
        except Exception as error:
            if created is not None:
                attributes.remove(created)
                if active_name is not None:
                    attributes.active_color = attributes.get(active_name)
            else:
                for element, value in old_values:
                    if context.mode == 'OBJECT':
                        element.color = value
                    else:
                        element[layer] = value
                if context.mode == 'EDIT_MESH':
                    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


_color_classes = tuple(type('AXISMELD_OT_m3_color_' + action, (_ColorAction,), {
    'bl_idname': 'axismeld.m3_color_' + action,
    'bl_label': {'add': 'Create Color Attribute', 'remove': 'Delete Active Color Attribute',
                 'rename': 'Rename Active Color Attribute', 'active': 'Choose Active Color Attribute',
                 'set': 'Set Color Value'}[action],
    'action': action,
    '__annotations__': dict(_ColorAction.__annotations__),
}) for action in ('add', 'remove', 'rename', 'active', 'set'))


class AXISMELD_OT_m3_color_display(Operator):
    bl_idname = 'axismeld.m3_color_display'
    bl_label = 'Display Active Vertex Colors'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return _view(context) and _editable_mesh(context, ('OBJECT', 'EDIT_MESH')) and bool(_active_color(context))

    def execute(self, context):
        shading = context.space_data.shading
        shading.color_type = 'MATERIAL' if shading.color_type == 'VERTEX' else 'VERTEX'
        return {'FINISHED'}


def command_state(context, command):
    if command in _OVERLAYS and _view(context):
        return 'checkbox', bool(getattr(context.space_data.overlay, _OVERLAYS[command]))
    if command == 'color.display_active' and _view(context):
        return 'checkbox', context.space_data.shading.color_type == 'VERTEX'
    if command == 'display.modeling_toolbar' and _view(context):
        return 'checkbox', context.space_data.show_region_toolbar
    if command == 'display.distortion_analysis' and _view(context):
        return 'checkbox', (context.space_data.overlay.show_statvis and
                            context.scene.tool_settings.statvis.type == 'DISTORT')
    if command.startswith('tool.mesh_') and context.workspace and context.mode == 'EDIT_MESH':
        from .modeling_mesh import SPECS
        spec = next((item for item in SPECS if item.id == command), None)
        tool = context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
        if spec and tool:
            return 'radio', tool.idname == dict(spec.calls[0].kwargs)['name']
    return None


def _edit_meshes(context):
    if context.mode != 'EDIT_MESH':
        return ()
    return tuple(bmesh.from_edit_mesh(obj.data) for obj in context.objects_in_mode_unique_data
                 if obj.type == 'MESH' and obj.is_editable and obj.data.is_editable and
                 obj.visible_get(view_layer=context.view_layer))


def _bridge(context):
    for bm in _edit_meshes(context):
        edges = {edge for edge in bm.edges if edge.select and not edge.hide}
        groups = 0
        while edges:
            groups += 1
            pending = [edges.pop()]
            while pending:
                edge = pending.pop()
                for vertex in edge.verts:
                    linked = edges.intersection(vertex.link_edges)
                    edges.difference_update(linked)
                    pending.extend(linked)
        if groups >= 2:
            return True
    return False


def _edge_rotate(context):
    return any(edge.select and not edge.hide and len(edge.link_faces) == 2
               for bm in _edit_meshes(context) for edge in bm.edges)


def _connect_path(context):
    for bm in _edit_meshes(context):
        selected = [vertex for vertex in bm.verts if vertex.select and not vertex.hide]
        if len(selected) == 2:
            start, end = selected
            if any(end in edge.verts for edge in start.link_edges):
                continue  # Existing edge; no path split can be created.
            reached, pending = {start}, [start]
            while pending:
                vertex = pending.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if edge.link_faces and not edge.hide and not other.hide and other not in reached:
                        reached.add(other)
                        pending.append(other)
            if end in reached:
                return True
        elif len(selected) > 2:
            history = [element for element in bm.select_history if element.select and not element.hide]
            if len(history) >= 2 and len({type(element) for element in history}) == 1 and not isinstance(history[0], bmesh.types.BMFace):
                return True
    return False


def _connect_pairs(context):
    for bm in _edit_meshes(context):
        for face in bm.faces:
            if face.hide:
                continue
            selected = [vertex for vertex in face.verts if vertex.select and not vertex.hide]
            if any(not any(second in edge.verts for edge in first.link_edges)
                   for i, first in enumerate(selected) for second in selected[i + 1:]):
                return True
    return False


def _face_boolean(context):
    return any(any(face.select and not face.hide for face in bm.faces) and
               any(not face.select and not face.hide for face in bm.faces) for bm in _edit_meshes(context))


def _voxel(context):
    return (_editable_mesh(context) and bool(context.object.data.polygons) and
            context.object.data.shape_keys is None and context.object.data.users == 1)


def _quadriflow(context):
    if not _voxel(context):
        return False
    bm = bmesh.new()
    try:
        bm.from_mesh(context.object.data)
        return bool(bm.faces) and all(edge.is_manifold for edge in bm.edges)
    finally:
        bm.free()


def _projection(context):
    if not _view(context) or not any(bm.faces for bm in _edit_meshes(context)):
        return False
    for obj in context.selected_objects:
        if obj.mode == 'EDIT' or obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT'} or not obj.visible_get():
            continue
        evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        if mesh is None:
            continue
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            if any(edge.is_wire or edge.is_boundary for edge in bm.edges):
                return True
        finally:
            bm.free()
            evaluated.to_mesh_clear()
    return False


def _boolean_poll(context, reverse=False):
    pair = _boolean_targets(context)
    if pair is None:
        return False
    target, operand = pair[::-1] if reverse else pair
    return not _depends_on(operand, target)


COMMAND_POLLS = {
    **{identifier: _edit_overlay for identifier in
       ('display.crease_marks', 'display.sharp_edges', 'display.component_indices')},
    'display.face_centers': _face_centers,
    'display.distortion_analysis': _distortion,
    **{'mesh.boolean_' + suffix: _boolean_poll
       for suffix in ('union', 'difference', 'intersection', 'difference_reverse')},
    'mesh.boolean_difference_reverse': lambda c: _boolean_poll(c, True),
    'mesh.bridge': _bridge,
    'mesh.edge_rotate_cw': _edge_rotate,
    'mesh.edge_rotate_ccw': _edge_rotate,
    'mesh.connect_path': _connect_path,
    'mesh.connect_pairs': _connect_pairs,
    **{'mesh.boolean_faces_' + name: _face_boolean for name in ('union', 'difference', 'intersection')},
    'mesh.remesh_voxel': _voxel,
    'mesh.quad_remesh': _quadriflow,
    'mesh.project_cut': _projection,
    **{('color.set_value' if cls.action == 'set' else 'color.attribute_' + cls.action): cls.poll
       for cls in _color_classes},
    'color.display_active': AXISMELD_OT_m3_color_display.poll,
    'color.attribute_convert': lambda c: _editable_mesh(c) and _active_color(c) is not None,
    'color.paint_mode': lambda c: _editable_mesh(c) and bool(c.object.data.polygons),
    'mesh.colors_rotate': lambda c: bool(_edit_meshes(c)) and _active_color(c) is not None,
    'mesh.colors_reverse': lambda c: bool(_edit_meshes(c)) and _active_color(c) is not None,
}

classes = (AXISMELD_OT_m3_mesh_boolean, *_modifier_classes, AXISMELD_OT_m3_mesh_overlay,
           AXISMELD_OT_m3_normal_length, AXISMELD_OT_m3_modeling_toolbar, AXISMELD_OT_m3_mesh_distortion,
           *_color_classes, AXISMELD_OT_m3_color_display)

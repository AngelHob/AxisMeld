/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <string_view>
#include <utility>
#include <string>
#include <vector>

namespace blender::axismeld {

/* Keep this bounded direct-session contract in sync with the Python catalog fixture. */
inline constexpr std::string_view modeling_roots[] = {
    "context.modeling_vertex", "context.modeling_edge", "context.modeling_face"};
inline constexpr std::string_view object_modeling_root = "context.modeling_object";
inline constexpr std::string_view object_modeling_commands[] = {
    "tool.object_mesh_poly_build", "tool.object_mesh_loopcut", "tool.object_mesh_knife"};
inline constexpr std::string_view object_modeling_menu = "context.modeling_object_menu";

inline constexpr std::string_view creation_root = "context.create";
inline constexpr std::string_view creation_menu = "context.create_menu";

inline constexpr std::pair<std::string_view, std::string_view> companion_roots[] = {
    {"context.modeling_object", "context.modeling_object_menu"},
    {"context.create", "context.create_menu"},
    {"context.components", "context.component_menu"},
    {"context.modeling_vertex", "context.modeling_vertex_menu"},
    {"context.modeling_edge", "context.modeling_edge_menu"},
    {"context.modeling_face", "context.modeling_face_menu"},
    {"tools.select", "tools.select_menu"},
    {"tools.move", "tools.move_menu"},
    {"tools.rotate", "tools.rotate_menu"},
    {"tools.scale", "tools.scale_menu"},
    {"tools.select.select", "tools.select.select_menu"},
    {"tools.move.select", "tools.move.select_menu"},
    {"tools.rotate.select", "tools.rotate.select_menu"},
    {"tools.scale.select", "tools.scale.select_menu"},
};

inline std::string_view companion_root(const std::string_view root)
{
  for (const auto &[owner, menu] : companion_roots) {
    if (root == owner) { return menu; }
  }
  return {};
}

inline std::string_view companion_owner(const std::string_view id)
{
  for (const auto &[owner, menu] : companion_roots) {
    if (id == menu || (id.starts_with(menu) && id.size() > menu.size() && id[menu.size()] == '.')) {
      return menu;
    }
  }
  return {};
}

inline std::string_view active_companion_root(const std::vector<std::string> &path)
{
  for (auto item = path.rbegin(); item != path.rend(); ++item) {
    if (const auto menu = companion_root(*item); !menu.empty()) { return menu; }
  }
  return {};
}

inline bool creation_workflow_indicator(const std::string_view id)
{
  return id == "context.create_menu.interactive_creation" ||
         id == "context.create_menu.exit_on_completion";
}

inline bool creation_allows_command(const std::string_view id, const std::string_view command)
{
  constexpr std::pair<std::string_view, std::string_view> entries[] = {
      {"context.create.disc", "mesh.create_disc"},
      {"context.create.sphere", "mesh.create_sphere"},
      {"context.create.torus", "mesh.create_torus"},
      {"context.create.cube", "mesh.create_cube"},
      {"context.create.cone", "mesh.create_cone"},
      {"context.create.cylinder", "mesh.create_cylinder"},
      {"context.create.plane", "mesh.create_plane"},
      {"context.create_menu.platonic", "mesh.create_icosphere"},
      {"context.create_menu.pyramid", "mesh.create_pyramid"},
      {"context.create_menu.prism", "mesh.create_prism"},
      {"context.create_menu.type", "object.create_text"},
      { "context.create_menu.polygon_display_all.backface_culling_on", "display.backface_culling_on"},
      {"context.create_menu.polygon_display_all.backface_culling_off", "display.backface_culling_off"},
  };
  for (const auto &[row, allowed] : entries) {
    if (id == row && command == allowed) { return true; }
  }
  return false;
}

struct ObjectMenuCommand {
  std::string_view row, command, options;
};
inline constexpr ObjectMenuCommand object_menu_commands[] = {
    {"context.modeling_object_menu.offset_loop", "tool.object_mesh_offset_loop", ""},
    {"context.modeling_object_menu.smooth", "object.modeling_smooth", "object.modeling_smooth_options"},
    {"context.modeling_object_menu.mirror", "object.modeling_mirror", "object.modeling_mirror_options"},
    {"context.modeling_object_menu.reduce", "object.modeling_reduce", "object.modeling_reduce_options"},
    {"context.modeling_object_menu.remesh", "object.modeling_remesh", "object.modeling_remesh_options"},
    {"context.modeling_object_menu.combine", "mesh.combine_objects", ""},
    {"context.modeling_object_menu.quad_draw", "tool.object_mesh_poly_build", ""},
    {"context.modeling_object_menu.booleans.union", "mesh.boolean_union", ""},
    {"context.modeling_object_menu.booleans.difference", "mesh.boolean_difference", ""},
    {"context.modeling_object_menu.booleans.difference_reverse", "mesh.boolean_difference_reverse", ""},
    {"context.modeling_object_menu.booleans.intersection", "mesh.boolean_intersection", ""},
    {"context.modeling_object_menu.polygon_display.backface_culling", "display.backface_culling", ""},
};

inline bool object_menu_allows_command(const std::string_view id, const std::string_view command)
{
  if (command.empty()) {
    return false;
  }
  const bool option = id.ends_with(".options");
  const auto row = option ? id.substr(0, id.size() - 8) : id;
  for (const auto &entry : object_menu_commands) {
    if (row == entry.row && command == (option ? entry.options : entry.command)) {
      return true;
    }
  }
  return false;
}

inline bool object_menu_command_registered(const std::string_view command)
{
  if (command.empty()) {
    return false;
  }
  for (const auto &entry : object_menu_commands) {
    if (command == entry.command || command == entry.options) {
      return true;
    }
  }
  return false;
}

inline bool object_menu_target_aware(const std::string_view command)
{
  return command == "tool.object_mesh_offset_loop" || command == "tool.object_mesh_poly_build" ||
         command == "object.modeling_smooth" || command == "object.modeling_smooth_options" ||
         command == "object.modeling_mirror" || command == "object.modeling_mirror_options" ||
         command == "object.modeling_reduce" || command == "object.modeling_reduce_options" ||
         command == "object.modeling_remesh" || command == "object.modeling_remesh_options";
}

inline int modeling_root_domain(const std::string_view root)
{
  for (int domain = 0; domain < 3; domain++) {
    if (root == modeling_roots[domain]) {
      return domain;
    }
  }
  return -1;
}

struct ModelingCommand {
  std::string_view command;
  int domains;  /* Vertex = 1, Edge = 2, Face = 4; independent of Blender enum values. */
};
inline constexpr ModelingCommand modeling_commands[] = {
    {"mesh.merge_center", 7},
    {"mesh.merge_distance", 1},
    {"mesh.average_vertices", 1},
    {"mesh.bevel_vertices", 1},
    {"tool.mesh_knife", 7},
    {"selection.paint", 7},
    {"display.vertex_normals", 1},
    {"normals.average_custom", 1},
    {"normals.rotate", 1},
    {"normals.set_from_faces", 1},
    {"mesh.collapse", 2},
    {"mesh.edge_rotate_cw", 2},
    {"mesh.edge_rotate_ccw", 2},
    {"mesh.bevel_edges", 2},
    {"mesh.extrude_edges", 2},
    {"mesh.dissolve_edges", 2},
    {"normals.soften_edges", 2},
    {"normals.harden_by_angle", 2},
    {"normals.harden_edges", 2},
    {"display.sharp_edges", 2},
    {"mesh.poke_faces", 4},
    {"mesh.extrude_region", 4},
    {"display.face_normals", 4},
    {"normals.reverse", 4},
    {"normals.conform_outside", 4},
};

inline bool modeling_root_allows_command(const std::string_view root,
                                         const std::string_view command)
{
  if (root == object_modeling_root) {
    for (const auto allowed : object_modeling_commands) {
      if (command == allowed) {
        return true;
      }
    }
    return false;
  }
  const int domain = modeling_root_domain(root);
  if (domain < 0) {
    return false;
  }
  for (const ModelingCommand &entry : modeling_commands) {
    if (entry.command == command && (entry.domains & (1 << domain))) {
      return true;
    }
  }
  return false;
}


/* Fixed authored state IDs: no arbitrary disabled controls or active values. */
inline std::string_view unavailable_indicator(const std::string_view id)
{
  constexpr std::pair<std::string_view, std::string_view> entries[] = {
      {"tools.select.symmetry.options", "checkbox"},
      {"tools.select.symmetry.world", "checkbox"},
      {"tools.select.symmetry.object", "checkbox"},
      {"tools.select.symmetry.topology", "checkbox"},
      {"tools.select.symmetry.x", "checkbox"},
      {"tools.select.symmetry.y", "checkbox"},
      {"tools.select.symmetry.z", "checkbox"},
      {"tools.select.select.options", "checkbox"},
      {"tools.select.select.closest", "checkbox"},
      {"tools.select.select.backfaces", "checkbox"},
      {"tools.select.select.container", "checkbox"},
      {"tools.select.select.camera", "checkbox"},
      {"tools.select.select.soft.object", "checkbox"},
      {"tools.select.select.soft.toggle", "checkbox"},
      {"tools.select.select.soft.volume", "checkbox"},
      {"tools.select.select.soft.surface", "checkbox"},
      {"tools.select.select.soft.global", "checkbox"},
      {"tools.select.select.soft.color", "checkbox"},
      {"tools.select.select_menu.automatic", "checkbox"},
      {"tools.select.drag", "checkbox"},
      {"tools.select.camera", "checkbox"},
      {"tools.select_menu.automatic", "checkbox"},
      {"tools.move.symmetry.options", "checkbox"},
      {"tools.move.symmetry.world", "checkbox"},
      {"tools.move.symmetry.object", "checkbox"},
      {"tools.move.symmetry.topology", "checkbox"},
      {"tools.move.symmetry.x", "checkbox"},
      {"tools.move.symmetry.y", "checkbox"},
      {"tools.move.symmetry.z", "checkbox"},
      {"tools.move.select.options", "checkbox"},
      {"tools.move.select.closest", "checkbox"},
      {"tools.move.select.backfaces", "checkbox"},
      {"tools.move.select.container", "checkbox"},
      {"tools.move.select.camera", "checkbox"},
      {"tools.move.select.soft.object", "checkbox"},
      {"tools.move.select.soft.toggle", "checkbox"},
      {"tools.move.select.soft.volume", "checkbox"},
      {"tools.move.select.soft.surface", "checkbox"},
      {"tools.move.select.soft.global", "checkbox"},
      {"tools.move.select.soft.color", "checkbox"},
      {"tools.move.select_menu.automatic", "checkbox"},
      {"tools.move.axis.normal", "checkbox"},
      {"tools.move.axis.parent", "checkbox"},
      {"tools.move.axis.rotation", "checkbox"},
      {"tools.move.axis.live", "checkbox"},
      {"tools.move.axis.custom.custom", "checkbox"},
      {"tools.move.spacing", "checkbox"},
      {"tools.move.snap.options", "checkbox"},
      {"tools.move.snap.vertex", "checkbox"},
      {"tools.move.snap.relative", "checkbox"},
      {"tools.move.snap.face", "checkbox"},
      {"tools.move_menu.extrude", "checkbox"},
      {"tools.move_menu.duplicate", "checkbox"},
      {"tools.move_menu.preserve_uv", "checkbox"},
      {"tools.move_menu.preserve_children", "checkbox"},
      {"tools.move_menu.tweak", "checkbox"},
      {"tools.move_menu.transform_constraints.normals", "checkbox"},
      {"tools.move_menu.update_triad", "checkbox"},
      {"tools.move_menu.selection_constraints.off", "radio"},
      {"tools.move_menu.selection_constraints.angle", "radio"},
      {"tools.move_menu.selection_constraints.border", "radio"},
      {"tools.move_menu.selection_constraints.loop", "radio"},
      {"tools.move_menu.selection_constraints.ring", "radio"},
      {"tools.move_menu.selection_constraints.shell", "radio"},
      {"tools.move_menu.selection_constraints.uv_loop", "radio"},
      {"tools.move_menu.transform_constraints.off", "radio"},
      {"tools.move_menu.transform_constraints.edge", "radio"},
      {"tools.move_menu.transform_constraints.surface", "radio"},
      {"tools.rotate.symmetry.options", "checkbox"},
      {"tools.rotate.symmetry.world", "checkbox"},
      {"tools.rotate.symmetry.object", "checkbox"},
      {"tools.rotate.symmetry.topology", "checkbox"},
      {"tools.rotate.symmetry.x", "checkbox"},
      {"tools.rotate.symmetry.y", "checkbox"},
      {"tools.rotate.symmetry.z", "checkbox"},
      {"tools.rotate.select.options", "checkbox"},
      {"tools.rotate.select.closest", "checkbox"},
      {"tools.rotate.select.backfaces", "checkbox"},
      {"tools.rotate.select.container", "checkbox"},
      {"tools.rotate.select.camera", "checkbox"},
      {"tools.rotate.select.soft.object", "checkbox"},
      {"tools.rotate.select.soft.toggle", "checkbox"},
      {"tools.rotate.select.soft.volume", "checkbox"},
      {"tools.rotate.select.soft.surface", "checkbox"},
      {"tools.rotate.select.soft.global", "checkbox"},
      {"tools.rotate.select.soft.color", "checkbox"},
      {"tools.rotate.select_menu.automatic", "checkbox"},
      {"tools.rotate.axis.custom", "checkbox"},
      {"tools.rotate.discrete", "checkbox"},
      {"tools.rotate_menu.extrude", "checkbox"},
      {"tools.rotate_menu.duplicate", "checkbox"},
      {"tools.rotate_menu.preserve_uv", "checkbox"},
      {"tools.rotate_menu.preserve_children", "checkbox"},
      {"tools.rotate_menu.tweak", "checkbox"},
      {"tools.rotate_menu.transform_constraints.normals", "checkbox"},
      {"tools.rotate_menu.free_rotate", "checkbox"},
      {"tools.rotate_menu.relative", "checkbox"},
      {"tools.rotate_menu.selection_constraints.off", "radio"},
      {"tools.rotate_menu.selection_constraints.angle", "radio"},
      {"tools.rotate_menu.selection_constraints.border", "radio"},
      {"tools.rotate_menu.selection_constraints.loop", "radio"},
      {"tools.rotate_menu.selection_constraints.ring", "radio"},
      {"tools.rotate_menu.selection_constraints.shell", "radio"},
      {"tools.rotate_menu.selection_constraints.uv_loop", "radio"},
      {"tools.rotate_menu.transform_constraints.off", "radio"},
      {"tools.rotate_menu.transform_constraints.edge", "radio"},
      {"tools.rotate_menu.transform_constraints.surface", "radio"},
      {"tools.rotate_menu.center.default", "radio"},
      {"tools.rotate_menu.center.object", "radio"},
      {"tools.rotate_menu.center.manip", "radio"},
      {"tools.rotate_menu.center.selection", "radio"},
      {"tools.scale.symmetry.options", "checkbox"},
      {"tools.scale.symmetry.world", "checkbox"},
      {"tools.scale.symmetry.object", "checkbox"},
      {"tools.scale.symmetry.topology", "checkbox"},
      {"tools.scale.symmetry.x", "checkbox"},
      {"tools.scale.symmetry.y", "checkbox"},
      {"tools.scale.symmetry.z", "checkbox"},
      {"tools.scale.select.options", "checkbox"},
      {"tools.scale.select.closest", "checkbox"},
      {"tools.scale.select.backfaces", "checkbox"},
      {"tools.scale.select.container", "checkbox"},
      {"tools.scale.select.camera", "checkbox"},
      {"tools.scale.select.soft.object", "checkbox"},
      {"tools.scale.select.soft.toggle", "checkbox"},
      {"tools.scale.select.soft.volume", "checkbox"},
      {"tools.scale.select.soft.surface", "checkbox"},
      {"tools.scale.select.soft.global", "checkbox"},
      {"tools.scale.select.soft.color", "checkbox"},
      {"tools.scale.select_menu.automatic", "checkbox"},
      {"tools.scale.axis.normal", "checkbox"},
      {"tools.scale.axis.parent", "checkbox"},
      {"tools.scale.axis.rotation", "checkbox"},
      {"tools.scale.axis.live", "checkbox"},
      {"tools.scale.axis.custom.custom", "checkbox"},
      {"tools.scale.discrete", "checkbox"},
      {"tools.scale.relative", "checkbox"},
      {"tools.scale_menu.extrude", "checkbox"},
      {"tools.scale_menu.duplicate", "checkbox"},
      {"tools.scale_menu.preserve_uv", "checkbox"},
      {"tools.scale_menu.preserve_children", "checkbox"},
      {"tools.scale_menu.tweak", "checkbox"},
      {"tools.scale_menu.transform_constraints.normals", "checkbox"},
      {"tools.scale_menu.negative", "checkbox"},
      {"tools.scale_menu.selection_constraints.off", "radio"},
      {"tools.scale_menu.selection_constraints.angle", "radio"},
      {"tools.scale_menu.selection_constraints.border", "radio"},
      {"tools.scale_menu.selection_constraints.loop", "radio"},
      {"tools.scale_menu.selection_constraints.ring", "radio"},
      {"tools.scale_menu.selection_constraints.shell", "radio"},
      {"tools.scale_menu.selection_constraints.uv_loop", "radio"},
      {"tools.scale_menu.transform_constraints.off", "radio"},
      {"tools.scale_menu.transform_constraints.edge", "radio"},
      {"tools.scale_menu.transform_constraints.surface", "radio"},
      {"tools.scale_menu.center.default", "radio"},
      {"tools.scale_menu.center.object", "radio"},
      {"tools.scale_menu.center.manip", "radio"},
      {"center.controls.rigging.toggle", "checkbox"},
      {"center.controls.animation.toggle", "checkbox"},
      {"center.controls.fx.toggle", "checkbox"},
      {"center.controls.rendering.toggle", "checkbox"},
      {"center.controls.custom", "checkbox"},
      {"center.controls.style.rmb_popups", "checkbox"},
      {"center.controls.window.main", "checkbox"},
      {"center.controls.window.pane", "checkbox"},
      {"context.component_menu.metadata.visualize", "checkbox"},
      {"context.create_menu.interactive_creation", "checkbox"},
      {"context.create_menu.exit_on_completion", "checkbox"},
  };
  for (const auto &[row, style] : entries) {
    if (id == row) { return style; }
  }
  return {};
}

inline bool component_menu_allows_command(const std::string_view id, const std::string_view command)
{
  constexpr std::pair<std::string_view, std::string_view> entries[] = {
      {"context.component_menu.select_all", "selection.select_all"},
      {"context.component_menu.deselect_all", "selection.clear"},
      {"context.component_menu.select_hierarchy", "selection.hierarchy"},
      {"context.component_menu.invert_selection", "selection.invert"},
      {"context.component_menu.actions.template", "display.template"},
      {"context.component_menu.actions.untemplate", "display.untemplate"},
      {"context.component_menu.actions.unparent", "edit.unparent"},
  };
  for (const auto &[row, allowed] : entries) {
    if (id == row && command == allowed) { return true; }
  }
  return false;
}

inline bool component_menu_selection_wide(const std::string_view command)
{
  return command == "selection.select_all" || command == "selection.clear" ||
         command == "selection.invert";
}

inline bool modeling_menu_allows_command(const std::string_view root,
                                         const std::string_view id,
                                         const std::string_view command)
{
  struct Entry { std::string_view root, row, command; };
  constexpr Entry entries[] = {
      {"context.modeling_vertex", "context.modeling_vertex_menu.crease", "mesh.interactive_crease_vertices"},
      {"context.modeling_vertex", "context.modeling_vertex_menu.detach", "mesh.detach_selection"},
      {"context.modeling_vertex", "context.modeling_vertex_menu.circularize", "mesh.circularize"},
      {"context.modeling_vertex", "context.modeling_vertex_menu.apply_color", "color.set_value"},
      {"context.modeling_vertex", "context.modeling_vertex_menu.polygon_display.backface_culling", "display.backface_culling"},
      {"context.modeling_vertex", "context.modeling_vertex_menu.polygon_display.normals", "display.vertex_normals"},
      {"context.modeling_vertex", "context.modeling_vertex_menu.polygon_display.numbers", "display.component_indices"},
      {"context.modeling_edge", "context.modeling_edge_menu.crease", "mesh.interactive_crease_edges"},
      {"context.modeling_edge", "context.modeling_edge_menu.offset_loop", "tool.mesh_offset_loop"},
      {"context.modeling_edge", "context.modeling_edge_menu.insert_loop", "tool.mesh_loopcut"},
      {"context.modeling_edge", "context.modeling_edge_menu.slide", "tool.mesh_edge_slide"},
      {"context.modeling_edge", "context.modeling_edge_menu.circularize", "mesh.circularize"},
      {"context.modeling_edge", "context.modeling_edge_menu.edge_flow", "mesh.edge_flow"},
      {"context.modeling_edge", "context.modeling_edge_menu.subdivide", "mesh.subdivide"},
      {"context.modeling_edge", "context.modeling_edge_menu.bridge", "mesh.bridge"},
      {"context.modeling_edge", "context.modeling_edge_menu.fill_hole", "mesh.fill_holes"},
      {"context.modeling_edge", "context.modeling_edge_menu.detach", "mesh.edge_split"},
      {"context.modeling_edge", "context.modeling_edge_menu.polygon_display.backface_culling", "display.backface_culling"},
      {"context.modeling_edge", "context.modeling_edge_menu.polygon_display.soft_edges", "display.sharp_edges"},
      {"context.modeling_face", "context.modeling_face_menu.smart_extrude", "mesh.extrude_manifold"},
      {"context.modeling_face", "context.modeling_face_menu.smooth", "mesh.smooth_subdivide"},
      {"context.modeling_face", "context.modeling_face_menu.subdivide", "mesh.subdivide"},
      {"context.modeling_face", "context.modeling_face_menu.circularize", "mesh.circularize"},
      {"context.modeling_face", "context.modeling_face_menu.detach", "mesh.detach_selection"},
      {"context.modeling_face", "context.modeling_face_menu.triangulate", "mesh.triangulate"},
      {"context.modeling_face", "context.modeling_face_menu.quadrangulate", "mesh.quadrangulate"},
      {"context.modeling_face", "context.modeling_face_menu.reduce", "mesh.reduce"},
      {"context.modeling_face", "context.modeling_face_menu.extract", "mesh.extract_faces"},
      {"context.modeling_face", "context.modeling_face_menu.duplicate", "mesh.duplicate_faces"},
      {"context.modeling_face", "context.modeling_face_menu.polygon_display.backface_culling", "display.backface_culling"},
      {"context.modeling_face", "context.modeling_face_menu.polygon_display.centers", "display.face_centers"},
      {"context.modeling_face", "context.modeling_face_menu.polygon_display.normals", "display.face_normals"},
      {"context.modeling_face", "context.modeling_face_menu.polygon_display.numbers", "display.component_indices"},
  };
  for (const auto &entry : entries) {
    if (root == entry.root && id == entry.row && command == entry.command) { return true; }
  }
  return false;
}

}  // namespace blender::axismeld

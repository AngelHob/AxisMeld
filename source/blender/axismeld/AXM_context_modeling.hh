/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <string_view>

namespace blender::axismeld {

/* Keep this bounded direct-session contract in sync with the Python catalog fixture. */
inline constexpr std::string_view modeling_roots[] = {
    "context.modeling_vertex", "context.modeling_edge", "context.modeling_face"};
inline constexpr std::string_view object_modeling_root = "context.modeling_object";
inline constexpr std::string_view object_modeling_commands[] = {
    "tool.object_mesh_poly_build", "tool.object_mesh_loopcut", "tool.object_mesh_knife"};
inline constexpr std::string_view object_modeling_menu = "context.modeling_object_menu";

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

}  // namespace blender::axismeld

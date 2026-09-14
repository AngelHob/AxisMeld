/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <string_view>

namespace blender::axismeld {

/* Keep this bounded direct-session contract in sync with the Python catalog fixture. */
inline constexpr std::string_view modeling_roots[] = {
    "context.modeling_vertex", "context.modeling_edge", "context.modeling_face"};

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

/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "view3d_axismeld_hotbox_icons.hh"
#include <string>
#include <string_view>

#include "AXM_hotbox_menu.hh"
#include "UI_resources.hh"

namespace blender::axismeld {
namespace {
struct IconMatch {
  std::string_view key;
  int icon;
};

/* Stable semantic IDs, not translated labels or arbitrary Blender operator lookups.
 * Exact mappings take precedence over the category vocabulary below. */
constexpr IconMatch exact_icons[] = {
    {"views", ICON_ORIENTATION_GLOBAL},
    {"center.recent", ICON_RECOVER_LAST},
    {"center.controls", ICON_PREFERENCES},
    {"common.file", ICON_FILEBROWSER},
    {"common.edit", ICON_EDITMODE_HLT},
    {"common.create", ICON_ADD},
    {"common.modify", ICON_MODIFIER},
    {"pane", ICON_WINDOW},
    {"pane.panels", ICON_WINDOW},
    {"center", ICON_PIVOT_MEDIAN},
    {"modeling", ICON_MESH_DATA},
    {"common", ICON_MENU_PANEL},
    {"style", ICON_MENU_PANEL},
    {"transparency", ICON_SHADING_RENDERED},
    {"file.new", ICON_FILE_NEW},
    {"file.open", ICON_FILE_FOLDER},
    {"file.save", ICON_FILE_TICK},
    {"file.save_as", ICON_FILE_TICK},
    {"file.import", ICON_IMPORT},
    {"file.export", ICON_EXPORT},
    {"edit.copy_objects", ICON_COPYDOWN},
    {"edit.paste_objects", ICON_PASTEDOWN},
    {"edit.cut_objects", ICON_X},
    {"edit.adjust_last_operation", ICON_PREFERENCES},
    {"object.rename", ICON_FONT_DATA},
    {"object.batch_rename", ICON_FONT_DATA},
    {"view.wireframe", ICON_SHADING_WIRE},
    {"view.shaded", ICON_SHADING_SOLID},
    {"view.perspective", ICON_VIEW_PERSPECTIVE},
    {"view.side", ICON_VIEW_ORTHO},
    {"view.bottom", ICON_VIEW_ORTHO},
    {"view.front", ICON_VIEW_ORTHO},
    {"view.back", ICON_VIEW_ORTHO},
    {"view.top", ICON_VIEW_ORTHO},
    {"view.left", ICON_VIEW_ORTHO},
    {"view.toggle_quad", ICON_SPLIT_VERTICAL},
    {"view.focus_selected", ICON_ZOOM_SELECTED},
    {"view.frame_all", ICON_ZOOM_ALL},
    {"mode.object", ICON_OBJECT_DATA},
    {"selection.vertex_mode", ICON_VERTEXSEL},
    {"selection.edge_mode", ICON_EDGESEL},
    {"selection.face_mode", ICON_FACESEL},
    {"selection.convert_vert", ICON_VERTEXSEL},
    {"selection.convert_edge", ICON_EDGESEL},
    {"selection.convert_face", ICON_FACESEL},
    {"selection.select_all", ICON_SELECT_SET},
    {"selection.clear", ICON_SELECT_SUBTRACT},
    {"selection.grow", ICON_SELECT_EXTEND},
    {"selection.shrink", ICON_SELECT_SUBTRACT},
    {"selection.marquee", ICON_SELECT_SET},
    {"selection.lasso", ICON_GP_SELECT_STROKES},
    {"selection.paint", ICON_BRUSH_DATA},
    {"selection.toggle_component", ICON_EDITMODE_HLT},
    {"tool.select", ICON_RESTRICT_SELECT_OFF},
    {"transform.move", ICON_EMPTY_ARROWS},
    {"transform.rotate", ICON_GESTURE_ROTATE},
    {"transform.scale", ICON_FULLSCREEN_ENTER},
    {"object.modeling_smooth", ICON_MOD_SUBSURF},
    {"object.modeling_mirror", ICON_MOD_MIRROR},
    {"object.modeling_reduce", ICON_MOD_DECIM},
    {"object.modeling_remesh", ICON_MOD_REMESH},
    {"mesh.smooth_subdivide", ICON_MOD_SUBSURF},
    {"mesh.subdivision_modifier", ICON_MOD_SUBSURF},
    {"mesh.combine_objects", ICON_AUTOMERGE_ON},
    {"mesh.create_subdiv_sphere", ICON_MESH_UVSPHERE},
    {"mesh.create_subdiv_cube", ICON_MESH_CUBE},
    {"mesh.create_subdiv_cylinder", ICON_MESH_CYLINDER},
    {"mesh.create_subdiv_cone", ICON_MESH_CONE},
    {"mesh.create_subdiv_plane", ICON_MESH_PLANE},
    {"mesh.create_subdiv_torus", ICON_MESH_TORUS},
    {"pivot.median", ICON_PIVOT_MEDIAN},
    {"pivot.active", ICON_PIVOT_ACTIVE},
    {"pivot.cursor", ICON_PIVOT_CURSOR},
    {"pivot.individual", ICON_PIVOT_INDIVIDUAL},
    {"pivot.bounds", ICON_PIVOT_BOUNDBOX},
    {"snap.vertex", ICON_SNAP_VERTEX},
    {"snap.edge", ICON_SNAP_EDGE},
    {"snap.face", ICON_SNAP_FACE},
    {"snap.increment", ICON_SNAP_INCREMENT},
    {"snap.enabled", ICON_SNAP_ON},
};

/* Vocabulary is bounded by identifier token boundaries: e.g. 'plane' must not
 * classify 'planesomething'. Order resolves deliberately related operations. */
bool token(const std::string_view id, const std::string_view word)
{
  size_t position = 0;
  while ((position = id.find(word, position)) != std::string_view::npos) {
    const size_t end = position + word.size();
    if ((position == 0 || id[position - 1] == '.' || id[position - 1] == '_') &&
        (end == id.size() || id[end] == '.' || id[end] == '_'))
    {
      return true;
    }
    position++;
  }
  return false;
}

constexpr IconMatch operation_icons[] = {
    {"export", ICON_EXPORT},
    {"import", ICON_IMPORT},
    {"boolean", ICON_MOD_BOOLEAN},
    {"booleans", ICON_MOD_BOOLEAN},
    {"mirror", ICON_MOD_MIRROR},
    {"symmetrize", ICON_MOD_MIRROR},
    {"symmetry", ICON_MOD_MIRROR},
    {"reduce", ICON_MOD_DECIM},
    {"decimate", ICON_MOD_DECIM},
    {"remesh", ICON_MOD_REMESH},
    {"retopologize", ICON_MOD_REMESH},
    {"triangulate", ICON_MOD_TRIANGULATE},
    {"knife", ICON_MOD_TRIANGULATE},
    {"multi_cut", ICON_MOD_TRIANGULATE},
    {"bisect", ICON_MOD_TRIANGULATE},
    {"subdivide", ICON_MOD_SUBSURF},
    {"subdivision", ICON_MOD_SUBSURF},
    {"unsubdivide", ICON_MOD_SUBSURF},
    {"subdiv", ICON_MOD_SUBSURF},
    {"bevel", ICON_MOD_BEVEL},
    {"solidify", ICON_MOD_SOLIDIFY},
    {"extrude", ICON_MOD_SOLIDIFY},
    {"wireframe", ICON_SHADING_WIRE},
    {"smooth", ICON_MOD_SMOOTH},
    {"unsmooth", ICON_MOD_SUBSURF},
    {"soften", ICON_MOD_SMOOTH},
    {"harden", ICON_MOD_NORMALEDIT},
    {"normals", ICON_NORMALS_VERTEX},
    {"normal", ICON_NORMALS_VERTEX},
    {"array", ICON_MOD_ARRAY},
    {"weld", ICON_AUTOMERGE_ON},
    {"merge", ICON_AUTOMERGE_ON},
    {"combine", ICON_AUTOMERGE_ON},
    {"join", ICON_AUTOMERGE_ON},
    {"separate", ICON_AUTOMERGE_OFF},
    {"detach", ICON_AUTOMERGE_OFF},
    {"split", ICON_MOD_EDGESPLIT},
    {"extract", ICON_AUTOMERGE_OFF},
    {"duplicate", ICON_DUPLICATE},
    {"transfer", ICON_MOD_DATA_TRANSFER},
    {"cleanup", ICON_BRUSH_DATA},
    {"dissolve", ICON_X},
    {"delete", ICON_X},
    {"remove", ICON_REMOVE},
    {"clear", ICON_X},
    {"undo", ICON_LOOP_BACK},
    {"redo", ICON_LOOP_FORWARDS},
    {"history", ICON_RECOVER_LAST},
    {"repeat", ICON_RECOVER_LAST},
    {"mapping", ICON_UV_DATA},
    {"uv", ICON_UV_DATA},
    {"texture", ICON_TEXTURE},
    {"material", ICON_MATERIAL},
    {"materials", ICON_MATERIAL},
    {"color", ICON_COLOR},
    {"colors", ICON_COLOR},
    {"paint", ICON_BRUSH_DATA},
    {"sculpt", ICON_SCULPTMODE_HLT},
    {"cube", ICON_MESH_CUBE},
    {"sphere", ICON_MESH_UVSPHERE},
    {"icosphere", ICON_MESH_ICOSPHERE},
    {"torus", ICON_MESH_TORUS},
    {"cone", ICON_MESH_CONE},
    {"pyramid", ICON_MESH_CONE},
    {"cylinder", ICON_MESH_CYLINDER},
    {"prism", ICON_MESH_CYLINDER},
    {"plane", ICON_MESH_PLANE},
    {"grid", ICON_MESH_GRID},
    {"circle", ICON_MESH_CIRCLE},
    {"disc", ICON_MESH_CIRCLE},
    {"monkey", ICON_MESH_MONKEY},
    {"bezier", ICON_CURVE_BEZCURVE},
    {"nurbs", ICON_CURVE_NCURVE},
    {"collection", ICON_OUTLINER_COLLECTION},
    {"group", ICON_OUTLINER_COLLECTION},
    {"ungroup", ICON_OUTLINER_COLLECTION},
    {"lod", ICON_OUTLINER_COLLECTION},
    {"hierarchy", ICON_OUTLINER_COLLECTION},
    {"parent", ICON_ORIENTATION_PARENT},
    {"child", ICON_ORIENTATION_PARENT},
    {"camera", ICON_CAMERA_DATA},
    {"light", ICON_LIGHT_DATA},
    {"image", ICON_IMAGE_DATA},
    {"font", ICON_FONT_DATA},
    {"text", ICON_FONT_DATA},
    {"lattice", ICON_MOD_LATTICE},
    {"empty", ICON_EMPTY_DATA},
    {"locator", ICON_EMPTY_AXIS},
    {"cursor", ICON_CURSOR},
    {"world", ICON_ORIENTATION_GLOBAL},
    {"global", ICON_ORIENTATION_GLOBAL},
    {"gimbal", ICON_ORIENTATION_GIMBAL},
    {"local", ICON_ORIENTATION_LOCAL},
    {"rotate", ICON_GESTURE_ROTATE},
    {"rotation", ICON_GESTURE_ROTATE},
    {"spin", ICON_GESTURE_ROTATE},
    {"scale", ICON_FULLSCREEN_ENTER},
    {"resize", ICON_FULLSCREEN_ENTER},
    {"move", ICON_EMPTY_ARROWS},
    {"translate", ICON_EMPTY_ARROWS},
    {"location", ICON_EMPTY_ARROWS},
    {"falloff", ICON_PROP_ON},
    {"proportional", ICON_PROP_ON},
    {"pivot", ICON_PIVOT_MEDIAN},
    {"origin", ICON_OBJECT_ORIGIN},
    {"snap", ICON_SNAP_ON},
    {"measure", ICON_DRIVER_DISTANCE},
    {"distance", ICON_DRIVER_DISTANCE},
    {"angle", ICON_DRIVER_ROTATIONAL_DIFFERENCE},
    {"length", ICON_DRIVER_DISTANCE},
    {"vertex", ICON_VERTEXSEL},
    {"vertices", ICON_VERTEXSEL},
    {"vert", ICON_VERTEXSEL},
    {"edge", ICON_EDGESEL},
    {"edges", ICON_EDGESEL},
    {"loopcut", ICON_EDGESEL},
    {"loop", ICON_EDGESEL},
    {"face", ICON_FACESEL},
    {"faces", ICON_FACESEL},
    {"fill", ICON_FACESEL},
    {"quadrangulate", ICON_FACESEL},
    {"poly_build", ICON_MESH_DATA},
    {"quad_draw", ICON_MESH_DATA},
    {"inset", ICON_FACESEL},
    {"crease", ICON_MOD_SUBSURF},
    {"connect", ICON_EDGESEL},
    {"bridge", ICON_EDGESEL},
    {"bend", ICON_MOD_SIMPLEDEFORM},
    {"twist", ICON_MOD_SIMPLEDEFORM},
    {"taper", ICON_MOD_SIMPLEDEFORM},
    {"hide", ICON_HIDE_ON},
    {"show", ICON_HIDE_OFF},
    {"isolate", ICON_RESTRICT_VIEW_OFF},
    {"xray", ICON_XRAY},
    {"shading", ICON_SHADING_SOLID},
    {"display", ICON_HIDE_OFF},
    {"view", ICON_VIEW_ORTHO},
    {"views", ICON_ORIENTATION_GLOBAL},
    {"controls", ICON_PREFERENCES},
    {"settings", ICON_PREFERENCES},
    {"toolkit", ICON_TOOL_SETTINGS},
    {"toolbox", ICON_TOOL_SETTINGS},
    {"mesh", ICON_MESH_DATA},
    {"curve", ICON_CURVE_DATA},
    {"curves", ICON_CURVE_DATA},
    {"surface", ICON_SURFACE_DATA},
    {"surfaces", ICON_SURFACE_DATA},
    {"deform", ICON_MOD_SIMPLEDEFORM},
    {"select", ICON_RESTRICT_SELECT_OFF},
    {"selection", ICON_RESTRICT_SELECT_OFF},
    {"object", ICON_OBJECT_DATA},
    {"objects", ICON_OBJECT_DATA},
    {"transform", ICON_EMPTY_ARROWS},
    {"edit", ICON_EDITMODE_HLT},
    {"create", ICON_ADD},
    {"modeling", ICON_MESH_DATA},
    {"tools", ICON_TOOL_SETTINGS},
    {"tool", ICON_TOOL_SETTINGS},
};

/* Maya's fixed gap IDs use CamelCase/acronyms; normalize identifiers only,
 * never visible labels. CreateNURBSCube becomes create_nurbs_cube. */
std::string identifier_words(const std::string_view identity)
{
  std::string result;
  result.reserve(identity.size() + 8);
  const auto upper = [](const char c) { return c >= 'A' && c <= 'Z'; };
  const auto lower = [](const char c) { return c >= 'a' && c <= 'z'; };
  for (size_t index = 0; index < identity.size(); index++) {
    const char c = identity[index];
    if (upper(c)) {
      if (index > 0 && (lower(identity[index - 1]) ||
                        (upper(identity[index - 1]) && index + 1 < identity.size() &&
                         lower(identity[index + 1]))))
      {
        result += '_';
      }
      result += char(c - 'A' + 'a');
    }
    else {
      result += c;
    }
  }
  return result;
}

int identity_icon(std::string_view identity)
{
  if (identity.ends_with(".options")) {
    identity.remove_suffix(std::string_view(".options").size());
  }
  if (identity.starts_with("object.modeling_") && identity.ends_with("_options")) {
    identity.remove_suffix(std::string_view("_options").size());
  }
  for (const auto &entry : exact_icons) {
    if (identity == entry.key) {
      return entry.icon;
    }
  }
  /* Orientation describes the frame, not the move/rotate/scale tool namespace. */
  if (identity.starts_with("orientation.")) {
    if (identity.ends_with(".world")) {
      return ICON_ORIENTATION_GLOBAL;
    }
    if (identity.ends_with(".object")) {
      return ICON_ORIENTATION_LOCAL;
    }
    if (identity.ends_with(".normal")) {
      return ICON_ORIENTATION_NORMAL;
    }
    if (identity.ends_with(".view")) {
      return ICON_ORIENTATION_VIEW;
    }
    if (identity.ends_with(".gimbal")) {
      return ICON_ORIENTATION_GIMBAL;
    }
  }
  const std::string words = identifier_words(identity);
  for (const auto &entry : operation_icons) {
    if (token(words, entry.key)) {
      return entry.icon;
    }
  }
  return ICON_NONE;
}
}  // namespace

int hotbox_semantic_icon(const MenuNode &node)
{
  if (node.kind == MenuKind::Separator) {
    return ICON_NONE;
  }
  /* Controls have their own icon-only rendering and never receive another slot. */
  if (node.id.starts_with("@back:")) {
    return ICON_BACK;
  }
  if (node.id.starts_with("@scroll:")) {
    return node.id.ends_with(":previous") ? ICON_TRIA_UP : ICON_TRIA_DOWN;
  }
  if (node.kind == MenuKind::Setting && node.command.starts_with("center.")) {
    if (const int icon = identity_icon(node.value)) {
      return icon;
    }
    return ICON_MENU_PANEL;
  }
  if (!node.command.empty()) {
    /* No ID fallback here: aliases/Recent of the same command must stay identical. */
    const int icon = identity_icon(node.command);
    return icon != ICON_NONE ? icon : ICON_TOOL_SETTINGS;
  }
  if (const int icon = identity_icon(node.id)) {
    return icon;
  }
  return node.kind == MenuKind::Menu ? ICON_FILE_FOLDER : ICON_TOOL_SETTINGS;
}
}  // namespace blender::axismeld

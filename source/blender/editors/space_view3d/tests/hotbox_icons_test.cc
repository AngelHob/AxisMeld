/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <functional>
#include <map>
#include <set>

#include "AXM_hotbox_menu.hh"
#include "UI_resources.hh"
#include "testing/testing.h"
#include "view3d_axismeld_hotbox_icons.hh"

namespace blender::axismeld::tests {
#include "hotbox_menu_fixture.hh"

static MenuNode item(const std::string &command, const std::string &id = "test.entry")
{
  return {id, "Translated label", command, "", "", MenuKind::Command, true};
}

TEST(hotbox_icons, RealCatalogHasStaticIconsWithoutChangingAliasesOrTranslatedLabels)
{
  const auto snapshot = default_snapshot();
  int total = 0, functions = 0, generic = 0;
  std::set<int> icons;
  std::map<std::string, int> commands;
  std::function<void(const std::vector<MenuNode> &)> visit = [&](const auto &nodes) {
    for (const auto &node : nodes) {
      total++;
      const int icon = hotbox_semantic_icon(node);
      if (node.kind == MenuKind::Separator) {
        EXPECT_EQ(icon, ICON_NONE) << node.id;
      }
      else {
        functions++;
        EXPECT_GT(icon, ICON_NONE) << node.id;
        EXPECT_LT(icon, BIFICONID_LAST_STATIC) << node.id;
        icons.insert(icon);
        generic += icon == ICON_TOOL_SETTINGS;
        auto translated = node;
        translated.label = "A completely unrelated translated caption";
        translated.enabled = !node.enabled;
        EXPECT_EQ(hotbox_semantic_icon(translated), icon) << node.id;
        if (node.kind == MenuKind::Command) {
          const auto [previous, inserted] = commands.emplace(node.command, icon);
          if (!inserted) {
            EXPECT_EQ(previous->second, icon) << node.command;
          }
          EXPECT_EQ(hotbox_semantic_icon(item(node.command, "center.recent.9.alias")), icon);
        }
      }
      visit(node.children);
    }
  };
  visit(snapshot.menus);
  EXPECT_GE(total, 1403);
  EXPECT_GE(functions, 1388);
  EXPECT_GE(icons.size(), 30);
  EXPECT_LT(generic, functions / 5);
  RecordProperty("catalog_nodes", total);
  RecordProperty("functional_nodes", functions);
  RecordProperty("distinct_icons", int(icons.size()));
  RecordProperty("generic_tool_icons", generic);
  RecordProperty("unique_command_icons", int(commands.size()));
}

TEST(hotbox_icons, RepresentativeOperationsAndModifierOptionsUseNativeSemantics)
{
  const std::pair<const char *, int> expected[] = {
      {"object.modeling_smooth", ICON_MOD_SUBSURF},
      {"object.modeling_mirror", ICON_MOD_MIRROR},
      {"object.modeling_reduce", ICON_MOD_DECIM},
      {"object.modeling_remesh", ICON_MOD_REMESH},
      {"mesh.boolean_difference", ICON_MOD_BOOLEAN},
      {"mesh.create_cube", ICON_MESH_CUBE},
      {"mesh.create_torus", ICON_MESH_TORUS},
      {"selection.vertex_mode", ICON_VERTEXSEL},
      {"selection.edge_mode", ICON_EDGESEL},
      {"selection.face_mode", ICON_FACESEL},
      {"view.wireframe", ICON_SHADING_WIRE},
      {"view.perspective", ICON_VIEW_PERSPECTIVE},
      {"tool.object_mesh_knife", ICON_MOD_TRIANGULATE},
  };
  for (const auto &[command, icon] : expected) {
    EXPECT_EQ(hotbox_semantic_icon(item(command)), icon) << command;
    if (std::string_view(command).starts_with("object.modeling_")) {
      EXPECT_EQ(hotbox_semantic_icon(item(std::string(command) + "_options")), icon);
    }
  }
}

TEST(hotbox_icons, DirectoriesSettingsGapsAndControlBoundaries)
{
  MenuNode node{
      "context.modeling_object_menu.mapping", "Anything", "", "", "", MenuKind::Menu, true};
  EXPECT_EQ(hotbox_semantic_icon(node), ICON_UV_DATA);
  node.id = "context.modeling_object_menu.mirror";
  node.kind = MenuKind::Disabled;
  EXPECT_EQ(hotbox_semantic_icon(node), ICON_MOD_MIRROR);
  node.id = "context.modeling_object_menu.mirror.options";
  EXPECT_EQ(hotbox_semantic_icon(node), ICON_MOD_MIRROR);
  node.kind = MenuKind::Setting;
  node.command = "center.LEFTMOUSE";
  node.value = "views";
  EXPECT_EQ(hotbox_semantic_icon(node), ICON_ORIENTATION_GLOBAL);
  node.value = "center.recent";
  EXPECT_EQ(hotbox_semantic_icon(node), ICON_RECOVER_LAST);
  node.kind = MenuKind::Separator;
  EXPECT_EQ(hotbox_semantic_icon(node), ICON_NONE);
  EXPECT_EQ(hotbox_semantic_icon(item("", "@back:any")), ICON_BACK);
  EXPECT_EQ(hotbox_semantic_icon(item("", "@scroll:any:next")), ICON_TRIA_DOWN);
  EXPECT_EQ(hotbox_semantic_icon(item("", "@scroll:any:previous")), ICON_TRIA_UP);
}

TEST(hotbox_icons, OperationScopeAndMayaGapIdentifiersDoNotInheritUnrelatedNamespaces)
{
  const std::pair<const char *, int> commands[] = {
      {"orientation.move.normal", ICON_ORIENTATION_NORMAL},
      {"orientation.rotate.object", ICON_ORIENTATION_LOCAL},
      {"orientation.scale.view", ICON_ORIENTATION_VIEW},
      {"mesh.extrude_vertices", ICON_MOD_SOLIDIFY},
      {"selection.type_surface", ICON_SURFACE_DATA},
      {"curve.open_close", ICON_CURVE_DATA},
      {"edit.copy_objects", ICON_COPYDOWN},
      {"edit.paste_objects", ICON_PASTEDOWN},
      {"file.open", ICON_FILE_FOLDER},
      {"file.save", ICON_FILE_TICK},
      {"file.export", ICON_EXPORT},
  };
  for (const auto &[command, icon] : commands) {
    EXPECT_EQ(hotbox_semantic_icon(item(command)), icon) << command;
  }
  const std::pair<const char *, int> gaps[] = {
      {"gap.ExportDeformerWeights", ICON_EXPORT},
      {"gap.ImportDeformerWeights", ICON_IMPORT},
      {"gap.CreateNURBSCube", ICON_MESH_CUBE},
      {"gap.SelectSurfacePointsMask", ICON_SURFACE_DATA},
      {"tools.move.symmetry", ICON_MOD_MIRROR},
  };
  for (const auto &[id, icon] : gaps) {
    auto node = item("", id);
    node.kind = MenuKind::Disabled;
    EXPECT_EQ(hotbox_semantic_icon(node), icon) << id;
  }
}
}  // namespace blender::axismeld::tests

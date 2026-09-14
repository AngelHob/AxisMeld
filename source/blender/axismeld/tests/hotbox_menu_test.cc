/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <map>
#include <set>

#include "AXM_hotbox_menu.hh"
#include "AXM_context_modeling.hh"
#include "testing/testing.h"

namespace blender::axismeld::tests {
#include "hotbox_menu_fixture.hh"

TEST(axismeld_hotbox_menu, MayaContentCompanionMappingsAreExact)
{
  for (const std::string root : {"context.modeling_vertex", "context.modeling_edge",
                                  "context.modeling_face", "tools.select", "tools.move",
                                  "tools.rotate", "tools.scale", "tools.move.select",
                                  "tools.rotate.select", "tools.scale.select", "tools.select.select"}) {
    EXPECT_EQ(companion_root(root), root + "_menu") << root;
  }
  EXPECT_EQ(companion_root("context.components"), "context.component_menu");
  EXPECT_TRUE(companion_root("tools.move.fake").empty());
  EXPECT_EQ(active_companion_root({"tools.move", "tools.move.select"}), "tools.move.select_menu");
  EXPECT_EQ(active_companion_root({"tools.move"}), "tools.move_menu");
  EXPECT_TRUE(active_companion_root({"views"}).empty());
  EXPECT_EQ(companion_owner("tools.move.select_menu.automatic_camera"), "tools.move.select_menu");
  EXPECT_TRUE(companion_owner("tools.move_menu_typo").empty());
}

TEST(axismeld_hotbox_menu, MayaCompanionCommandsCannotCrossTargetsOrDomains)
{
  EXPECT_TRUE(component_menu_allows_command("context.component_menu.select_all", "selection.select_all"));
  EXPECT_FALSE(component_menu_allows_command("context.component_menu.select", "selection.select_all"));
  EXPECT_FALSE(component_menu_allows_command("context.component_menu.select_all.options", "selection.select_all"));
  EXPECT_TRUE(component_menu_selection_wide("selection.invert"));
  EXPECT_FALSE(component_menu_selection_wide("edit.unparent"));
  EXPECT_TRUE(modeling_menu_allows_command("context.modeling_face", "context.modeling_face_menu.triangulate", "mesh.triangulate"));
  EXPECT_FALSE(modeling_menu_allows_command("context.modeling_edge", "context.modeling_face_menu.triangulate", "mesh.triangulate"));
  EXPECT_FALSE(modeling_menu_allows_command("context.modeling_face", "context.modeling_face_menu.triangulate.options", "mesh.triangulate"));
  EXPECT_TRUE(creation_allows_command("context.create_menu.polygon_display_all.backface_culling_on", "display.backface_culling_on"));
  EXPECT_FALSE(creation_allows_command("context.create_menu.polygon_display_all.backface_culling_on", "display.backface_culling_off"));
}

/* A fixed eight-row fixture isolates generic native-list padding from catalog growth. */
static MenuSnapshot legacy_select_snapshot()
{
  auto snapshot = default_snapshot();
  auto &selection = snapshot.menus[0].children[3];
  selection.presentation = "list";
  selection.children.clear();
  for (int index = 0; index < 8; index++) {
    selection.children.push_back({"fixture.select." + std::to_string(index), "Select Item",
                                   "selection.select_all", "", "", MenuKind::Command, true});
  }
  selection.children[0].kind = MenuKind::Menu;
  selection.children[0].command.clear();
  selection.children[0].children = {{"fixture.select.child", "Child", "selection.clear",
                                     "", "", MenuKind::Command, true}};
  return snapshot;
}

static MenuSnapshot overflow_snapshot()
{
  auto snapshot = default_snapshot();
  MenuNode list{"fixture.overflow", "Overflow", "", "", "", MenuKind::Menu, true};
  list.presentation = "list";
  for (int index = 0; index < 56; index++) {
    list.children.push_back({"fixture.overflow." + std::to_string(index), "Visible row",
                             "selection.clear", "", "", MenuKind::Command, true});
  }
  snapshot.menus[0].children.push_back(std::move(list));
  snapshot.style = "center";
  snapshot.center_buttons[0] = "fixture.overflow";
  return snapshot;
}

static void visit(const std::vector<MenuNode> &nodes,
                  const std::function<void(const MenuNode &)> &fn)
{
  for (const MenuNode &node : nodes) {
    fn(node);
    visit(node.children, fn);
  }
}

static std::unordered_map<std::string, float> measured(const MenuSnapshot &snapshot)
{
  std::unordered_map<std::string, float> result;
  // Independent logical measurements; default main rows still overflow a small viewport.
  const auto has_state = [&](const MenuNode &node) {
    return !node.indicator.empty() || menu_radio_state(snapshot, node) != MenuRadioState::None ||
           (node.kind == MenuKind::Setting && node.command.starts_with("row."));
  };
  std::function<void(const std::vector<MenuNode> &, bool)> measure;
  measure = [&](const std::vector<MenuNode> &nodes, const bool state_column) {
    for (const auto &node : nodes) {
      const bool view_command = node.id.starts_with("views.") && node.kind == MenuKind::Command;
      result[node.id] = view_command ? 38.0f :
                                      80.0f + (state_column || has_state(node) ? 20.0f : 0.0f);
      const bool reserve_children = node.presentation != "radial" && node.id != "views" &&
          std::any_of(node.children.begin(), node.children.end(), has_state);
      measure(node.children, reserve_children);
    }
  };
  measure(snapshot.menus, false);
  return result;
}

static const MenuRect *rect(const MenuLayout &layout, const std::string &id)
{
  for (const MenuRect &item : layout.rects) {
    if (item.id == id) {
      return &item;
    }
  }
  return nullptr;
}

// The absent Maya NE view remains a non-painted cancellation gap.
static const MenuRect *view_reference_rect(const MenuLayout &layout, const std::string &id)
{
  if (const auto *item = rect(layout, id)) { return item; }
  for (const auto &item : layout.marking_gaps) {
    if (item.id == id) { return &item; }
  }
  return nullptr;
}

static void expect_complete_native(MenuSnapshot snapshot, const std::string &id,
                                   const float width = 1920, const float height = 1080,
                                   const float x = 960, const float y = 540)
{
  snapshot.style = "center";
  snapshot.center_buttons[0] = id;
  const auto widths = measured(snapshot);
  const auto layout = layout_menu(snapshot, width, height, x, y, {"center", id}, {}, widths);
  const auto stale = layout_menu(snapshot, width, height, x, y, {"center", id}, {{id, 999}}, widths);
  ASSERT_TRUE(layout.supported) << id;
  ASSERT_TRUE(stale.supported);
  EXPECT_TRUE(layout.native_scroll_bounds.empty());
  const MenuNode *owner = nullptr;
  visit(snapshot.menus, [&](const MenuNode &node) { if (node.id == id) { owner = &node; } });
  ASSERT_NE(owner, nullptr);
  int prior_column = -1;
  float prior_y = height;
  for (const auto &node : owner->children) {
    const auto *item = rect(layout, node.id), *unchanged = rect(stale, node.id);
    ASSERT_NE(item, nullptr) << node.id;
    ASSERT_NE(unchanged, nullptr);
    EXPECT_EQ(std::count_if(layout.rects.begin(), layout.rects.end(), [&](const auto &r) {
      return r.id == node.id;
    }), 1) << node.id;
    EXPECT_FLOAT_EQ(item->x, unchanged->x);
    EXPECT_FLOAT_EQ(item->y, unchanged->y);
    EXPECT_TRUE(item->native_menu);
    EXPECT_FLOAT_EQ(item->height, node.kind == MenuKind::Separator && node.label.empty() ? 6 : 24);
    EXPECT_GE(item->x, 12); EXPECT_GE(item->y, 12);
    EXPECT_LE(item->x + item->width, width - 12);
    EXPECT_LE(item->y + item->height, height - 12);
    EXPECT_GE(item->column, prior_column);
    if (item->column == prior_column) { EXPECT_FLOAT_EQ(item->y + item->height, prior_y); }
    prior_column = item->column; prior_y = item->y;
    const bool enabled = node.enabled && node.kind != MenuKind::Disabled && node.kind != MenuKind::Separator;
    EXPECT_EQ(hit_menu(layout, item->x + item->width / 2, item->y + item->height / 2),
              enabled ? item->id : "") << node.id;
    if (!node.children.empty() && node.kind != MenuKind::Menu) {
      const auto *options = rect(layout, node.children.front().id);
      ASSERT_NE(options, nullptr);
      EXPECT_FLOAT_EQ(options->width, 24);
      EXPECT_FLOAT_EQ(options->x, item->x + item->width);
      EXPECT_EQ(options->column, item->column);
    }
  }
  for (const auto &item : layout.rects) {
    EXPECT_FALSE(item.id.starts_with("@scroll:") || item.id.starts_with("@back:"));
  }
}

TEST(axismeld_hotbox_menu, DeepestSelectCompanionReplacesParentAndDropsStaleCascade)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto child = layout_menu(snapshot, 2400, 1600, 1200, 900,
      {"tools.move", "tools.move.select"}, {}, widths, nullptr, "tools.move",
      {"tools.move_menu", "tools.move_menu.transform_constraints"});
  ASSERT_TRUE(child.supported);
  EXPECT_NE(rect(child, "tools.move.select_menu.automatic"), nullptr);
  EXPECT_EQ(rect(child, "tools.move_menu.options"), nullptr);
  const auto parent = layout_menu(snapshot, 2400, 1600, 1200, 900,
      {"tools.move"}, {}, widths, nullptr, "tools.move", {"tools.move.select_menu"});
  ASSERT_TRUE(parent.supported);
  EXPECT_NE(rect(parent, "tools.move_menu.options"), nullptr);
  EXPECT_EQ(rect(parent, "tools.move.select_menu.automatic"), nullptr);
}

static const std::array<const char *, 13> mapping_suffixes = {
    "none",
    "views",
    "center_recent",
    "center_controls",
    "common",
    "common_select",
    "common_modify",
    "pane",
    "pane_view",
    "pane_shading",
    "pane_panels",
    "pane_panels_views",
    "modeling",
};

static bool separated_by(const MenuRect &a, const MenuRect &b, const float distance)
{
  return a.x >= b.x + b.width + distance || b.x >= a.x + a.width + distance ||
         a.y >= b.y + b.height + distance || b.y >= a.y + a.height + distance;
}

TEST(axismeld_hotbox_menu, NativeSeparatorsUseSixPixelGeometryAndKeepAllRowsReachable)
{
  auto snapshot = default_snapshot();
  MenuNode list{"fixture.thin", "Thin list", "", "", "", MenuKind::Menu, true};
  list.presentation = "list";
  for (int i = 0; i < 20; i++) {
    list.children.push_back({"fixture.row" + std::to_string(i), "Action", "view.front", "", "", MenuKind::Command, true});
    list.children.push_back({"fixture.sep" + std::to_string(i), "", "", "", "", MenuKind::Separator, false});
  }
  snapshot.menus[0].children.push_back(list);
  snapshot.center_buttons[0] = list.id;
  const auto widths = measured(snapshot);
  std::set<std::string> reached;
  for (int offset = 0; offset < 40; offset++) {
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540,
                                    {"center", list.id}, {{list.id, offset}}, widths);
    ASSERT_TRUE(layout.supported);
    for (const auto &item : layout.rects) {
      if (!item.id.starts_with("fixture.") || item.depth == 0) { continue; }
      const bool separator = item.id.starts_with("fixture.sep");
      EXPECT_EQ(item.height, separator ? 6 : 24) << item.id;
      EXPECT_GE(item.y, 12); EXPECT_LE(item.y + item.height, 1068);
      EXPECT_EQ(hit_menu(layout, item.x + item.width / 2, item.y + item.height / 2),
                separator ? "" : item.id);
      reached.insert(item.id);
    }
  }
  for (const auto &child : list.children) { EXPECT_TRUE(reached.contains(child.id)) << child.id; }
}

TEST(axismeld_hotbox_menu, NativeLabeledSeparatorsAreReadableNoninteractiveHeadings)
{
  auto snapshot = default_snapshot();
  MenuNode list{"fixture.heading", "Headings", "", "", "", MenuKind::Menu, true};
  list.presentation = "list";
  list.children = {{"fixture.heading.title", "Viewport display attributes", "", "", "", MenuKind::Separator, false},
                   {"fixture.heading.action", "Action", "view.front", "", "", MenuKind::Command, true},
                   {"fixture.heading.line", "", "", "", "", MenuKind::Separator, false},
                   {"fixture.heading.title2", "Object", "", "", "", MenuKind::Separator, false},
                   {"fixture.heading.action2", "Action", "view.back", "", "", MenuKind::Command, true}};
  snapshot.menus[0].children.push_back(list);
  snapshot.center_buttons[0] = list.id;
  const auto widths = measured(snapshot);
  const auto layout = layout_menu(snapshot, 960, 540, 480, 270, {"center", list.id}, {}, widths);
  ASSERT_TRUE(layout.supported);
  const MenuRect *previous = nullptr;
  for (const auto &node : list.children) {
    const auto *item = rect(layout, node.id);
    ASSERT_NE(item, nullptr) << node.id;
    EXPECT_EQ(item->height, node.label.empty() ? 6 : 24);
    EXPECT_GE(item->width, widths.at(list.children.front().id) + 40);
    if (previous) { EXPECT_EQ(previous->y, item->y + item->height); }
    EXPECT_EQ(hit_menu(layout, item->x + item->width / 2, item->y + item->height / 2),
              node.kind == MenuKind::Separator ? "" : node.id);
    if (node.kind == MenuKind::Separator) { EXPECT_FALSE(item->interactive); }
    previous = item;
  }
}

TEST(axismeld_hotbox_menu, NativeHeadingStaysWithItsFirstActionAcrossColumns)
{
  auto snapshot = default_snapshot();
  snapshot.style = "center";
  MenuNode list{"fixture.heading_columns", "Heading columns", "", "", "", MenuKind::Menu, true};
  list.presentation = "list";
  for (int i = 0; i < 8; i++) {
    list.children.push_back({"fixture.hrow" + std::to_string(i), "Action", "view.front", "", "", MenuKind::Command, true});
  }
  list.children.push_back({"fixture.hsection", "Next section", "", "", "", MenuKind::Separator, false});
  list.children.push_back({"fixture.hlast", "Last action", "view.back", "", "", MenuKind::Command, true});
  snapshot.menus[0].children.push_back(list);
  snapshot.center_buttons[0] = list.id;
  const auto layout = layout_menu(snapshot, 960, 240, 480, 120, {"center", list.id}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *heading = rect(layout, "fixture.hsection");
  const auto *last = rect(layout, "fixture.hlast");
  const auto *first = rect(layout, "fixture.hrow0");
  ASSERT_NE(heading, nullptr); ASSERT_NE(last, nullptr); ASSERT_NE(first, nullptr);
  EXPECT_NE(first->column, heading->column);
  EXPECT_EQ(heading->column, last->column);
  EXPECT_EQ(heading->height, 24);
  EXPECT_EQ(heading->y, last->y + last->height);
  EXPECT_EQ(hit_menu(layout, heading->x + 5, heading->y + 12), "");
  EXPECT_EQ(hit_menu(layout, last->x + 5, last->y + 12), last->id);
  for (const auto &node : list.children) { EXPECT_NE(rect(layout, node.id), nullptr); }
}

TEST(axismeld_hotbox_menu, CreationCompanionUsesThinSeparatorsAndIndependentPath)
{
  auto snapshot = default_snapshot();
  MenuNode list{"context.create_menu", "Create menu", "", "", "", MenuKind::Menu, true};
  list.presentation = "list";
  list.children = {{"fixture.create.a", "Create A", "mesh.create_cube", "", "", MenuKind::Command, true},
                   {"fixture.create.sep", "", "", "", "", MenuKind::Separator, false},
                   {"fixture.create.b", "Create B", "mesh.create_plane", "", "", MenuKind::Command, true}};
  std::erase_if(snapshot.menus, [&](const MenuNode &node) { return node.id == list.id; });
  snapshot.menus.push_back(list);
  const auto layout = layout_menu(snapshot, 1200, 900, 600, 550, {"context.create"}, {},
                                  measured(snapshot), nullptr, "context.create");
  ASSERT_TRUE(layout.supported);
  const auto *a = rect(layout, "fixture.create.a"), *separator = rect(layout, "fixture.create.sep"),
             *b = rect(layout, "fixture.create.b");
  ASSERT_NE(a, nullptr); ASSERT_NE(separator, nullptr); ASSERT_NE(b, nullptr);
  EXPECT_TRUE(a->companion); EXPECT_EQ(separator->height, 6);
  EXPECT_EQ(a->y, separator->y + separator->height);
  EXPECT_EQ(separator->y, b->y + b->height);
  EXPECT_EQ(hit_marking_menu_rect(layout, "context.create", separator->x + 5, separator->y + 3), nullptr);
  EXPECT_NE(hit_marking_menu_rect(layout, "context.create", 1190, 550), nullptr);
}

TEST(axismeld_hotbox_menu, ObjectCompanionIsVisibleWithoutStealingRadialAndOptionsAreSeparate)
{
  auto snapshot = default_snapshot();
  MenuNode option{"composition.action.options", "Options", "mesh.quad_remesh", "", "", MenuKind::Command, true};
  MenuNode action{"composition.action", "Action", "", "Unavailable", "", MenuKind::Disabled, false, {option}};
  MenuNode list{"context.modeling_object_menu", "Object menu", "", "", "", MenuKind::Menu, true, {action}};
  list.presentation = "list";
  // Independent fixture, not the production catalog's composition metadata.
  std::function<void(std::vector<MenuNode> &)> remove = [&](auto &nodes) {
    std::erase_if(nodes, [](const MenuNode &node) { return node.id == "context.modeling_object_menu"; });
    for (auto &node : nodes) { remove(node.children); }
  };
  remove(snapshot.menus);
  snapshot.menus[0].children.push_back(list);
  const auto widths = measured(snapshot);
  auto layout = layout_menu(snapshot, 1200, 900, 600, 550,
                            {"context.modeling_object"}, {}, widths, nullptr, "context.modeling_object");
  ASSERT_TRUE(layout.supported);
  const MenuRect *main = rect(layout, action.id), *cell = rect(layout, option.id);
  ASSERT_NE(main, nullptr);
  ASSERT_NE(cell, nullptr);
  EXPECT_EQ(cell->width, 24);
  EXPECT_FALSE(main->interactive);
  EXPECT_TRUE(cell->interactive);
  EXPECT_EQ(main->x + main->width, cell->x);
  EXPECT_EQ(hit_menu(layout, cell->x + 12, cell->y + 12), option.id);
  EXPECT_NE(hit_marking_menu_rect(layout, "context.modeling_object", 1100, 550), nullptr);
  EXPECT_EQ(hit_marking_menu_rect(layout, "context.modeling_object", cell->x + 12, cell->y + 12), nullptr);
}

TEST(axismeld_hotbox_menu, CreationCompanionAndRadialCommandAdmissionStayExact)
{
  EXPECT_TRUE(creation_allows_command("context.create_menu.type", "object.create_text"));
  EXPECT_TRUE(creation_allows_command("context.create_menu.pyramid", "mesh.create_pyramid"));
  EXPECT_TRUE(creation_allows_command("context.create_menu.polygon_display_all.backface_culling_on", "display.backface_culling_on"));
  EXPECT_FALSE(creation_allows_command("context.create_menu.pyramid.options", "mesh.create_pyramid"));
  EXPECT_FALSE(creation_allows_command("context.create_menu.pyramid", "mesh.create_cube"));
  EXPECT_FALSE(creation_allows_command("context.create.fake", "mesh.create_fake"));
  EXPECT_FALSE(creation_allows_command("context.create_menu.type", "wm.open_mainfile"));
  const auto snapshot = default_snapshot();
  visit(snapshot.menus, [&](const MenuNode &node) {
    if ((node.id.starts_with("context.create.") || node.id.starts_with("context.create_menu.")) &&
        node.kind == MenuKind::Command) {
      EXPECT_TRUE(creation_allows_command(node.id, node.command)) << node.id;
    }
  });
}

TEST(axismeld_hotbox_menu, RadialOptionsPreserveCombinedInnerEdgesAndCannotRunTheirMainAction)
{
  auto snapshot = default_snapshot();
  const auto find_mutable = [&](auto &&self, std::vector<MenuNode> &nodes, const std::string &id) -> MenuNode * {
    for (auto &node : nodes) {
      if (node.id == id) { return &node; }
      if (auto *found = self(self, node.children, id)) { return found; }
    }
    return nullptr;
  };
  for (const auto root : {creation_root, object_modeling_root}) {
    auto *node = find_mutable(find_mutable, snapshot.menus, std::string(root));
    ASSERT_NE(node, nullptr);
    for (const std::string direction : {"N", "E", "S", "W"}) {
      SCOPED_TRACE(std::string(root) + " " + direction);
      auto found = std::find_if(node->children.begin(), node->children.end(), [&](const MenuNode &item) {
        return item.direction == direction;
      });
      ASSERT_NE(found, node->children.end());
      auto &leaf = *found;
      leaf.children.clear();
      const auto before = layout_menu(snapshot, 1800, 1600, 900, 950, {std::string(root)}, {}, measured(snapshot), nullptr, root);
      leaf.children = {{leaf.id + ".options", "Options", "", "Unavailable", "", MenuKind::Disabled, false}};
      const auto after = layout_menu(snapshot, 1800, 1600, 900, 950, {std::string(root)}, {}, measured(snapshot), nullptr, root);
      ASSERT_TRUE(before.supported); ASSERT_TRUE(after.supported);
      const auto *old = rect(before, leaf.id), *main = rect(after, leaf.id), *option = rect(after, leaf.id + ".options");
      ASSERT_NE(old, nullptr); ASSERT_NE(main, nullptr); ASSERT_NE(option, nullptr);
      EXPECT_EQ(option->width, 24); EXPECT_EQ(option->height, 24);
      EXPECT_EQ(main->width, old->width);
      EXPECT_EQ(main->x + main->width, option->x);
      EXPECT_EQ(main->y, option->y);
      if (direction == "W") {
        EXPECT_EQ(old->x + old->width, option->x + option->width);
      }
      else if (direction == "E") {
        EXPECT_EQ(old->x, main->x);
      }
      else {
        EXPECT_EQ(old->x + old->width / 2, (main->x + option->x + option->width) / 2);
      }
      // Check interior pixels across the entire independent cell, not only its center.
      for (const float x : {0.5f, 12.0f, 23.5f}) {
        const auto *hit = hit_menu_rect(after, option->x + x, option->y + 12);
        ASSERT_NE(hit, nullptr);
        EXPECT_EQ(hit->id, option->id);
        EXPECT_TRUE(hit->option_box);
        EXPECT_EQ(hit_menu(after, option->x + x, option->y + 12), "");
      }
      const auto *main_hit = hit_menu_rect(after, main->x + main->width / 2, main->y + 12);
      ASSERT_NE(main_hit, nullptr);
      EXPECT_EQ(main_hit->id, leaf.id);
    }
  }
}

TEST(axismeld_hotbox_menu, ObjectCompanionCatalogUsesExactMainAndOptionPairs)
{
  const auto snapshot = default_snapshot();
  const MenuNode *companion = nullptr;
  visit(snapshot.menus, [&](const MenuNode &node) { if (node.id == object_modeling_menu) { companion = &node; } });
  ASSERT_NE(companion, nullptr);
  EXPECT_EQ(companion->presentation, "list");
  std::set<std::string> actual;
  visit(companion->children, [&](const MenuNode &node) {
    EXPECT_NE(node.kind, MenuKind::Setting);
    if (node.kind == MenuKind::Command) {
      EXPECT_TRUE(object_menu_allows_command(node.id, node.command)) << node.id << ": " << node.command;
      actual.insert(node.id);
    }
  });
  for (const auto &entry : object_menu_commands) {
    EXPECT_TRUE(actual.contains(std::string(entry.row))) << entry.row;
    if (!entry.options.empty()) { EXPECT_TRUE(actual.contains(std::string(entry.row) + ".options")); }
  }
  EXPECT_FALSE(object_menu_allows_command("context.modeling_object_menu.smooth.options", "object.modeling_reduce_options"));
  EXPECT_FALSE(object_menu_allows_command("context.modeling_object_menu.smooth", "object.modeling_smooth_options"));
  EXPECT_FALSE(modeling_root_allows_command(object_modeling_root, "tool.object_mesh_offset_loop"));
  EXPECT_FALSE(object_menu_command_registered("object.modeling_smooth_options.extra"));
}

TEST(axismeld_hotbox_menu, FullObjectCompanionAndCascadeKeepRadialGeometryAndSpatialOcclusion)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const std::string root(object_modeling_root), list(object_modeling_menu);
  const auto initial = layout_menu(snapshot, 1200, 700, 600, 450, {root}, {}, widths, nullptr, root);
  ASSERT_TRUE(initial.supported);
  EXPECT_TRUE(initial.native_scroll_bounds.empty());
  const auto paged = layout_menu(snapshot, 1200, 700, 600, 450, {root}, {{list, 999}}, widths, nullptr, root);
  ASSERT_TRUE(paged.supported);
  EXPECT_TRUE(paged.native_scroll_bounds.empty());
  EXPECT_EQ(initial.rects.size(), paged.rects.size());
  const auto cascade = layout_menu(snapshot, 1200, 700, 600, 450, {root}, {}, widths, nullptr, root,
                                  {list, list + ".booleans"});
  ASSERT_TRUE(cascade.supported);
  const auto *child = rect(cascade, list + ".booleans.union");
  ASSERT_NE(child, nullptr);
  EXPECT_EQ(hit_marking_menu_rect(cascade, root, child->x + 5, child->y + 12), nullptr);
  EXPECT_NE(hit_marking_menu_rect(cascade, root, 1190, 450), nullptr);
  for (const auto &item : initial.rects) {
    if (!item.direction_label) { continue; }
    const auto *same = rect(cascade, item.id);
    ASSERT_NE(same, nullptr);
    EXPECT_EQ(same->x, item.x); EXPECT_EQ(same->y, item.y); EXPECT_EQ(same->width, item.width);
  }
  for (const auto &item : cascade.rects) {
    EXPECT_GE(item.x, 0); EXPECT_GE(item.y, 0);
    EXPECT_LE(item.x + item.width, 1200); EXPECT_LE(item.y + item.height, 700);
  }
}

TEST(axismeld_hotbox_menu, ModelingDirectRootsAndLeavesMatchTheRealCatalog)
{
  const auto snapshot = default_snapshot();
  for (int domain = 0; domain < 3; domain++) {
    const std::string_view root = modeling_roots[domain];
    EXPECT_EQ(modeling_root_domain(root), domain);
    const MenuNode *ring = nullptr;
    visit(snapshot.menus, [&](const MenuNode &node) {
      if (node.id == root) {
        ring = &node;
      }
    });
    ASSERT_NE(ring, nullptr);
    EXPECT_EQ(ring->presentation, "radial");
    std::set<std::string_view> actual;
    visit(ring->children, [&](const MenuNode &node) {
      if (node.kind == MenuKind::Command) {
        EXPECT_TRUE(modeling_root_allows_command(root, node.command)) << node.command;
        actual.insert(node.command);
      }
      EXPECT_NE(node.kind, MenuKind::Setting);
    });
    for (const auto &entry : modeling_commands) {
      EXPECT_EQ(actual.contains(entry.command), (entry.domains & (1 << domain)) != 0)
          << entry.command;
    }
  }
  EXPECT_EQ(modeling_root_domain("context.modeling_fake"), -1);
  EXPECT_EQ(modeling_root_domain("context.modeling_vertex.extra"), -1);
  EXPECT_FALSE(modeling_root_allows_command("context.modeling_face", "mesh.create_cube"));
  EXPECT_FALSE(modeling_root_allows_command("context.modeling_face", "context.modeling_hotbox"));
  EXPECT_FALSE(modeling_root_allows_command("context.modeling_vertex", "mesh.poke_faces"));
  EXPECT_FALSE(modeling_root_allows_command("context.modeling_fake", "mesh.merge_center"));
}

TEST(axismeld_hotbox_menu, ObjectDirectRootHasOnlyFixedToolsAndDisabledMayaDirections)
{
  const auto snapshot = default_snapshot();
  const MenuNode *root = nullptr;
  visit(snapshot.menus, [&](const MenuNode &node) {
    if (node.id == object_modeling_root) {
      root = &node;
    }
  });
  ASSERT_NE(root, nullptr);
  EXPECT_EQ(root->presentation, "radial");
  EXPECT_EQ(root->children.size(), 8);
  EXPECT_EQ(modeling_root_domain(root->id), -1);
  std::set<std::string_view> actual;
  for (const MenuNode &child : root->children) {
    EXPECT_NE(child.kind, MenuKind::Setting);
    if (child.kind == MenuKind::Command) {
      EXPECT_TRUE(modeling_root_allows_command(root->id, child.command));
      actual.insert(child.command);
    }
    else if (child.direction == "SE") {
      EXPECT_EQ(child.kind, MenuKind::Menu);
      EXPECT_EQ(child.presentation, "list");
      ASSERT_EQ(child.children.size(), 4);
      const std::array<std::string, 4> suffixes = {"display", "harden", "angle", "soften"};
      for (size_t i = 0; i < suffixes.size(); i++) {
        EXPECT_EQ(child.children[i].id, child.id + "." + suffixes[i]);
        EXPECT_EQ(child.children[i].kind, MenuKind::Disabled);
        EXPECT_FALSE(child.children[i].enabled);
        EXPECT_TRUE(child.children[i].command.empty());
      }
      ASSERT_EQ(child.children[2].children.size(), 1);
      EXPECT_EQ(child.children[2].children[0].id, child.id + ".angle.options");
      EXPECT_FALSE(child.children[2].children[0].enabled);
    }
    else {
      EXPECT_EQ(child.kind, MenuKind::Disabled);
      EXPECT_FALSE(child.enabled);
      EXPECT_TRUE(child.command.empty());
    }
  }
  for (const auto command : object_modeling_commands) {
    EXPECT_TRUE(actual.contains(command));
    for (const auto edit_root : modeling_roots) {
      EXPECT_FALSE(modeling_root_allows_command(edit_root, command));
    }
  }
  EXPECT_EQ(actual.size(), 3);
  EXPECT_FALSE(modeling_root_allows_command(root->id, "mesh.extrude_region"));
  EXPECT_FALSE(modeling_root_allows_command(root->id, "mesh.create_cube"));
}

TEST(axismeld_hotbox_menu, MayaStyleItemsArePlainWhileOtherStateGroupsFollowSnapshot)
{
  auto snapshot = default_snapshot();
  auto check = [&]() {
    std::map<std::string, int> selected;
    visit(snapshot.menus, [&](const MenuNode &node) {
      const auto state = menu_radio_state(snapshot, node);
      if (state == MenuRadioState::Selected) {
        selected[node.command]++;
      }
      if ((node.kind == MenuKind::Command || node.kind == MenuKind::Disabled) &&
          node.indicator == "radio") {
        EXPECT_EQ(state, node.checked ? MenuRadioState::Selected : MenuRadioState::Unselected)
            << node.id;
      }
      else if (node.kind != MenuKind::Setting || node.command.starts_with("row.")) {
        EXPECT_EQ(state, MenuRadioState::None) << node.id;
      }
      if (node.kind == MenuKind::Setting && node.command == "style") {
        // HotboxCenterMenu:170-175 / HotboxControlsMenu:129-134 contain no radio flag.
        EXPECT_EQ(state, MenuRadioState::None) << node.id;
        EXPECT_TRUE(node.enabled);
        EXPECT_TRUE(node.value == "rows" || node.value == "zones" || node.value == "center");
      }
      if (node.kind == MenuKind::Setting && node.command == "transparency") {
        EXPECT_EQ(state, node.value == std::to_string(snapshot.transparency) ?
                             MenuRadioState::Selected : MenuRadioState::Unselected) << node.id;
      }
      const std::array<std::string, 3> commands = {
          "center.LEFTMOUSE", "center.MIDDLEMOUSE", "center.RIGHTMOUSE"};
      for (int i = 0; i < 3; i++) {
        if (node.kind == MenuKind::Setting && node.command == commands[i]) {
          const std::string current = snapshot.center_buttons[i].empty() ? "none" :
                                                                          snapshot.center_buttons[i];
          EXPECT_EQ(state, node.value == current ? MenuRadioState::Selected :
                                                                     MenuRadioState::Unselected)
              << node.id;
        }
      }
    });
    EXPECT_EQ(selected["style"], 0);  // Both menus keep executable, plain Style settings.
    for (const auto command : {"center.LEFTMOUSE", "center.MIDDLEMOUSE", "center.RIGHTMOUSE"}) {
      EXPECT_EQ(selected[command], 1);
    }
    EXPECT_EQ(selected["transparency"], snapshot.transparency == 37 ? 0 : 1);
  };
  check();
  snapshot.style = "zones";
  snapshot.transparency = 37;
  snapshot.center_buttons = {"", "center.recent", "center.controls"};
  check();
  snapshot.style = "center";
  snapshot.transparency = 100;
  check();
  const MenuNode unsupported{"test", "Test", "unknown", "", "value", MenuKind::Setting, true, {}};
  EXPECT_EQ(menu_radio_state(snapshot, unsupported), MenuRadioState::None);
}

TEST(axismeld_hotbox_menu, RoomierMainTargetsKeepTenPixelGaps)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  ASSERT_TRUE(layout.supported);
  for (const auto &item : layout.rects) {
    EXPECT_GE(item.height, 38.0f) << item.id;
    if (!item.id.starts_with("@")) {
      EXPECT_GE(item.width - widths.at(item.id), 40.0f) << item.id;
    }
    for (const auto &other : layout.rects) {
      if (&item == &other || item.depth != other.depth) {
        continue;
      }
      EXPECT_TRUE(
          item.x + item.width + 9.99f <= other.x || other.x + other.width + 9.99f <= item.x ||
          item.y + item.height + 9.99f <= other.y || other.y + other.height + 9.99f <= item.y)
          << item.id << " too close to " << other.id;
    }
  }
}

TEST(axismeld_hotbox_menu, StandaloneToolDirectionsAndNativeChildOwnership)
{
  auto snapshot = default_snapshot();
  MenuNode tool{"tools.test", "Move", "", "", "", MenuKind::Menu, true, {}};
  tool.presentation = "radial";
  const std::array<const char *, 8> directions = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
  for (const auto direction : directions) {
    MenuNode child{
        std::string("tool.") + direction, direction, "", "", "", MenuKind::Menu, true, {}};
    child.direction = direction;
    child.presentation = "list";
    child.children.push_back(
        {child.id + ".leaf", "Option", "selection.clear", "", "", MenuKind::Command, true, {}});
    tool.children.push_back(child);
  }
  snapshot.menus[0].children.push_back(tool);
  const auto widths = measured(snapshot);
  const auto layout = layout_menu(
      snapshot, 1200, 800, 600, 400, {"tools.test"}, {}, widths, nullptr, "tools.test");
  ASSERT_TRUE(layout.supported);
  ASSERT_EQ(layout.rects.size(), 8);
  EXPECT_EQ(hit_menu(layout, 600, 400), "");
  for (const auto &item : layout.rects) {
    EXPECT_EQ(item.width, layout.rects.front().width);
    EXPECT_EQ(item.height, 24);
    EXPECT_GT(item.depth, 0);
  }
  ASSERT_NE(rect(layout, "tool.N"), nullptr);
  EXPECT_GT(rect(layout, "tool.N")->y, 400);
  EXPECT_LT(rect(layout, "tool.S")->y + 24, 400);
  EXPECT_LT(rect(layout, "tool.W")->x + rect(layout, "tool.W")->width, 600);
  EXPECT_GT(rect(layout, "tool.E")->x, 600);
  const auto child = layout_menu(
      snapshot, 1200, 800, 600, 400, {"tools.test", "tool.N"}, {}, widths, nullptr, "tools.test");
  ASSERT_TRUE(child.supported);
  ASSERT_NE(rect(child, "tool.W"), nullptr);
  EXPECT_TRUE(rect(child, "tool.W")->retained_only);
  ASSERT_NE(rect(child, "tool.N.leaf"), nullptr);
  EXPECT_TRUE(rect(child, "tool.N.leaf")->native_menu);
  const MenuRect &west = *rect(child, "tool.W");
  EXPECT_EQ(hit_menu(child, west.x + west.width / 2, west.y + 12), "");
}

TEST(axismeld_hotbox_menu, VisibleDirectionEdgesKeepNearestButtonAndDisabledOcclusion)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  for (const std::array<float, 2> origin :
       {std::array<float, 2>{960, 540}, {20, 20}, {1900, 1060}}) {
    const auto layout = layout_menu(snapshot, 1920, 1080, origin[0], origin[1],
                                    {"center", "views"}, {}, widths, &origin);
    ASSERT_TRUE(layout.supported);
    for (const std::string id : {"views.left", "views.back", "views.bottom", "views.camera"}) {
      const auto *item = view_reference_rect(layout, id);
      ASSERT_NE(item, nullptr);
      const bool left = id == "views.left" || id == "views.back";
      for (const float extension : {0.5f, 4.0f, 8.0f, 64.0f, 256.0f}) {
        const float x = left ? item->x - extension : item->x + item->width + extension;
        const auto *nearest = nearest_marking_rect(layout, x, item->y + item->height / 2);
        ASSERT_NE(nearest, nullptr);
        EXPECT_EQ(nearest->id, id);
        EXPECT_EQ(nearest->interactive, item->interactive);
      }
      const bool upper = id == "views.left" || id == "views.camera";
      const auto *vertical = nearest_marking_rect(
          layout, item->x + item->width / 2, item->y + (upper ? 150 : -150));
      ASSERT_NE(vertical, nullptr);
      EXPECT_EQ(vertical->id, id);
    }
    EXPECT_EQ(nearest_marking_rect(layout, NAN, 0), nullptr);
    for (const auto &center : layout.return_regions) {
      if (center.id == "views") {
        for (const float distance : {23.0f, 24.0f, 25.0f}) {
          EXPECT_EQ(nearest_marking_rect(layout, center.x + center.width / 2 + distance,
                                        center.y + center.height / 2), nullptr);
        }
      }
    }
  }
  for (const std::array<float, 2> origin :
       {std::array<float, 2>{0, 0}, {1919, 0}, {0, 1079}, {1919, 1079}}) {
    const auto layout = layout_menu(snapshot, 1920, 1080, origin[0], origin[1],
                                    {"center", "views"}, {}, widths, &origin);
    ASSERT_TRUE(layout.supported);
    const float x = origin[0] + (origin[0] == 0 ? 90 : -90);
    EXPECT_EQ(nearest_marking_rect(layout, x, origin[1], &origin), nullptr);
    EXPECT_EQ(nearest_marking_rect(layout, origin[0] + (origin[0] == 0 ? 15 : -15),
                                  origin[1] + (origin[1] == 0 ? 15 : -15), &origin), nullptr);
  }
}

TEST(axismeld_hotbox_menu, ToolReferenceUsesContentWidthsAndInsetDiagonalRows)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  for (const std::string tool : {"select", "move", "rotate", "scale"}) {
    const std::string root = "tools." + tool;
    const auto layout = layout_menu(
        snapshot, 1920, 1080, 960, 540, {root}, {}, widths, nullptr, root);
    ASSERT_TRUE(layout.supported);
    std::set<float> sizes;
    for (const auto &item : layout.rects) {
      if (item.companion) { continue; }
      sizes.insert(item.width);
      EXPECT_GE(item.width, 84);
      EXPECT_GE(item.width, widths.at(item.id) + 16);
      EXPECT_EQ(item.height, 24);
      for (const auto &other : layout.rects) {
        if (&item != &other && !other.companion) {
          EXPECT_TRUE(separated_by(item, other, 4));
        }
      }
    }
    EXPECT_GT(sizes.size(), 1) << root;
    if (tool != "select") {
      const auto &west = *rect(layout, root + ".world");
      const auto &northwest = *rect(layout, root + ".object");
      EXPECT_FLOAT_EQ(northwest.x + northwest.width - west.x - west.width, 16);
      EXPECT_FLOAT_EQ(northwest.y - west.y, 32);
    }
  }
}

TEST(axismeld_hotbox_menu, EveryRadialMatchesViewsHorizontalClearanceAndCenterCancellation)
{
  const auto snapshot = default_snapshot();
  std::vector<const MenuNode *> owners;
  visit(snapshot.menus, [&](const MenuNode &node) {
    if (node.presentation == "radial") {
      owners.push_back(&node);
    }
  });
  ASSERT_GE(owners.size(), 24);
  const std::unordered_map<std::string, std::string> reference_ids = {
      {"N", "views.perspective"}, {"NE", "views.camera"}, {"E", "views.side"},
      {"SE", "views.bottom"}, {"S", "views.front"}, {"SW", "views.back"},
      {"W", "views.top"}, {"NW", "views.left"}};
  for (const float title_width : {40.0f, 80.0f}) {
    auto widths = measured(snapshot);
    widths["views"] = title_width;
    for (const auto size : {std::array<float, 2>{1920, 1080}, {960, 540}}) {
      for (const auto origin : {std::array<float, 2>{size[0] / 2, size[1] / 2},
                                {0, 0}, {size[0], 0}, {0, size[1]}, {size[0], size[1]}}) {
        const auto views = layout_menu(snapshot, size[0], size[1], origin[0], origin[1],
                                       {"center", "views"}, {}, widths);
        ASSERT_TRUE(views.supported);
        const auto &reference_center = views.return_regions.back();
        const float reference_cx = reference_center.x + reference_center.width / 2;
        for (const MenuNode *owner : owners) {
          SCOPED_TRACE(testing::Message() << owner->id << " title=" << title_width << " size="
                                         << size[0] << "x" << size[1] << " origin="
                                         << origin[0] << "," << origin[1]);
          const auto layout = layout_menu(snapshot, size[0], size[1], origin[0], origin[1],
                                          {owner->id}, {}, widths, nullptr, owner->id);
          ASSERT_TRUE(layout.supported);
          const auto &center = layout.return_regions.back();
          const float cx = center.x + center.width / 2, cy = center.y + center.height / 2;
          EXPECT_FLOAT_EQ(center.width, reference_center.width);
          EXPECT_FLOAT_EQ(center.height, 40);
          auto compare_inner_edge = [&](const MenuRect &item, const std::string &direction) {
            const auto *reference = view_reference_rect(views, reference_ids.at(direction));
            ASSERT_NE(reference, nullptr);
            if (direction == "N" || direction == "S") {
              EXPECT_FLOAT_EQ(item.x + item.width / 2, cx);
            }
            else {
              const bool west = direction.find('W') != std::string::npos;
              const float actual_edge = item.x + (west ? item.width : 0) - cx;
              const float reference_edge = reference->x + (west ? reference->width : 0) -
                                           reference_cx;
              EXPECT_FLOAT_EQ(actual_edge, reference_edge) << direction;
            }
          };
          for (const MenuNode &node : owner->children) {
            const auto *item = rect(layout, node.id);
            ASSERT_NE(item, nullptr);
            MenuRect combined = *item;
            if (node.kind != MenuKind::Menu && !node.children.empty()) {
              const auto *option = rect(layout, node.id + ".options");
              ASSERT_NE(option, nullptr);
              EXPECT_TRUE(option->option_box);
              EXPECT_EQ(option->width, 24); EXPECT_EQ(option->height, 24);
              EXPECT_EQ(option->x, item->x + item->width);
              EXPECT_EQ(option->y, item->y);
              EXPECT_EQ(hit_menu(layout, option->x + 12, option->y + 12), "");
              combined.width += option->width;
            }
            // Maya centers the complete label+parameter-box group, not the label cell.
            // This checks the actual closest painted/hittable edge without relaxing it.
            compare_inner_edge(combined, node.direction);
            EXPECT_FLOAT_EQ(item->width, std::max(84.0f, widths.at(node.id) +
                                           (node.kind == MenuKind::Menu ? 60 : 16)));
            EXPECT_FLOAT_EQ(item->height, 24);
            EXPECT_GE(item->x, 12);
            EXPECT_LE(combined.x + combined.width, size[0] - 12);
            EXPECT_GE(item->y, 12);
            EXPECT_LE(item->y + item->height, size[1] - 12);
            const auto *hit = hit_marking_menu_rect(layout, owner->id,
                                                    item->x + item->width / 2, item->y + 12);
            ASSERT_NE(hit, nullptr);
            EXPECT_EQ(hit->id, node.id);
          }
          for (const auto &empty : layout.marking_gaps) {
            compare_inner_edge(empty, empty.id.substr(empty.id.rfind(':') + 1));
            EXPECT_FALSE(empty.interactive);
            EXPECT_EQ(rect(layout, empty.id), nullptr);
          }
          // These points lie inside the actual Views central-row clearance. A larger
          // painted hole must also cancel, rather than selecting a nearby diagonal.
          for (const float dx : {-reference_center.width / 2 + .5f, -24.0f, 24.0f,
                                  reference_center.width / 2 - .5f}) {
            EXPECT_EQ(hit_menu_rect(layout, cx + dx, cy), nullptr);
            EXPECT_EQ(hit_marking_menu_rect(layout, owner->id, cx + dx, cy), nullptr);
            EXPECT_EQ(menu_return_target(layout, cx + dx, cy), owner->id);
          }
        }
      }
    }
  }
}

TEST(axismeld_hotbox_menu, NarrowRadialsRejectAtomicallyInsteadOfReducingViewsClearance)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  for (const std::string owner : {"tools.select", "tools.move", "tools.rotate", "tools.scale"}) {
    for (const auto origin : {std::array<float, 2>{0, 0}, {196, 105}, {392, 210}}) {
      const auto narrow = layout_menu(snapshot, 392, 210, origin[0], origin[1],
                                      {owner}, {}, widths, nullptr, owner);
      EXPECT_FALSE(narrow.supported) << owner;
      EXPECT_TRUE(narrow.rects.empty());
      EXPECT_TRUE(narrow.return_regions.empty());
      EXPECT_TRUE(narrow.marking_gaps.empty());
    }
    const auto roomy = layout_menu(snapshot, 960, 540, 480, 270,
                                   {owner}, {}, widths, nullptr, owner);
    ASSERT_TRUE(roomy.supported) << owner;
  }
  for (const std::string owner : {"tools.move.axis"}) {
    const auto narrow = layout_menu(snapshot, 392, 210, 196, 105,
                                    {owner}, {}, widths, nullptr, owner);
    // Radials reserve state space on each actual state item, not the entire sibling group.
    // The original compact boundary therefore remains supported with faithful measurements.
    EXPECT_TRUE(narrow.supported) << owner;
    EXPECT_EQ(widths.at(owner + ".normal"), 100);
    EXPECT_EQ(widths.at(owner + ".custom"), 80);
    const auto roomy = layout_menu(snapshot, 960, 540, 480, 270,
                                   {owner}, {}, widths, nullptr, owner);
    ASSERT_TRUE(roomy.supported) << owner;
  }
  const auto component = layout_menu(snapshot, 392, 210, 196, 105,
                                      {"context.components"}, {}, widths, nullptr, "context.components");
  EXPECT_FALSE(component.supported);
  EXPECT_TRUE(component.rects.empty());
  EXPECT_TRUE(component.occlusion_regions.empty());
  // Eight creation parameter cells increase the complete ring width beyond 392px.
  // Preserve the same Views clearances and reject the whole composition atomically.
  const auto creation = layout_menu(snapshot, 392, 210, 196, 105,
                                    {"context.create"}, {}, widths, nullptr, "context.create");
  EXPECT_FALSE(creation.supported);
  EXPECT_TRUE(creation.rects.empty());
  EXPECT_TRUE(creation.return_regions.empty());
  EXPECT_TRUE(creation.marking_gaps.empty());
  EXPECT_TRUE(creation.occlusion_regions.empty());
  const auto roomy = layout_menu(snapshot, 960, 540, 480, 270,
                                 {"context.create"}, {}, widths, nullptr, "context.create");
  EXPECT_TRUE(roomy.supported);
  EXPECT_NE(rect(roomy, "context.create_menu.platonic"), nullptr);
}

TEST(axismeld_hotbox_menu, WideRadialChildCenterAndOutwardHitsIgnoreHiddenAncestors)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[0] = "tools.move";
  const auto widths = measured(snapshot);
  for (const bool space_entry : {false, true}) {
    const std::vector<std::string> path = space_entry ?
        std::vector<std::string>{"center", "tools.move",
                                 "tools.move.axis", "tools.move.axis.custom"} :
        std::vector<std::string>{"tools.move", "tools.move.axis", "tools.move.axis.custom"};
    auto child = layout_menu(snapshot, 1920, 1080, 960, 540, path, {}, widths, nullptr,
                              space_entry ? "" : "tools.move");
    ASSERT_TRUE(child.supported);
    ASSERT_GE(child.return_regions.size(), 3);
    const std::string owner = "tools.move.axis.custom";
    const auto &center = child.return_regions.back();
    const float cx = center.x + center.width / 2, cy = center.y + center.height / 2;
    EXPECT_EQ(center.id, owner);
    EXPECT_EQ(menu_return_target(child, cx, cy), owner);
    EXPECT_EQ(hit_marking_menu_rect(child, owner, cx, cy), nullptr);
    const auto *east = rect(child, owner + ".custom");
    ASSERT_NE(east, nullptr);
    EXPECT_TRUE(menu_return_target(child, east->x + east->width / 2, east->y + 12).empty());
    const float x = east->x + east->width + 100, y = east->y + 12;
    child.return_regions.front() = {"tools.move", x - 50, y - 20, 100, 40, 1};
    const auto *outward = hit_marking_menu_rect(child, owner, x, y);
    ASSERT_NE(outward, nullptr);
    EXPECT_EQ(outward->id, east->id);
    EXPECT_EQ(hit_marking_menu_rect(child, "tools.move", x, y), nullptr);
    // Returning after the outer stroke still identifies only the current child;
    // the operator uses this owner to retract exactly one path level.
    EXPECT_EQ(menu_return_target(child, cx, cy), owner);
  }
}

TEST(axismeld_hotbox_menu, RadialOutwardHitsRetainDisplayedRowsAndDisabledTargets)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  for (const std::string owner : {"tools.select", "tools.move", "tools.rotate", "tools.scale",
                                   "context.components"}) {
    for (const std::array<float, 2> origin :
         {std::array<float, 2>{600, 400}, {10, 10}, {1190, 790}}) {
      const auto layout = layout_menu(
          snapshot, 1200, 800, origin[0], origin[1], {owner}, {}, widths, nullptr, owner);
      ASSERT_TRUE(layout.supported) << owner;
      const auto &center = layout.return_regions.back();
      const float cx = center.x + center.width / 2;
      for (const auto &item : layout.rects) {
        if (item.companion) { continue; }
        const float middle = item.x + item.width / 2;
        if (std::abs(middle - cx) < 1) {
          continue;
        }
        for (const float extension : {0.5f, 8.0f, 64.0f, 256.0f}) {
          const float x = middle < cx ? item.x - extension : item.x + item.width + extension;
          const auto *hit = hit_marking_menu_rect(layout, owner, x, item.y + 12);
          const bool covered = std::any_of(layout.occlusion_regions.begin(), layout.occlusion_regions.end(),
              [&](const MenuRect &region) {
                return x >= region.x && x <= region.x + region.width &&
                       item.y + 12 >= region.y && item.y + 12 <= region.y + region.height;
              });
          if (covered) {
            EXPECT_EQ(hit, nullptr) << item.id;
            continue;
          }
          ASSERT_NE(hit, nullptr) << item.id;
          EXPECT_EQ(hit->id, item.id);
          EXPECT_EQ(hit->interactive, item.interactive);
        }
      }
      EXPECT_EQ(hit_marking_menu_rect(layout, owner, cx, center.y + center.height / 2), nullptr);
      EXPECT_EQ(hit_marking_menu_rect(layout, "unrelated", cx - 500, 400), nullptr);
      EXPECT_EQ(hit_marking_menu_rect(layout, owner, NAN, 400), nullptr);
    }
  }
}

TEST(axismeld_hotbox_menu, MissingRadialDirectionsBlockInsteadOfStealingNeighbours)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto layout = layout_menu(snapshot, 1200, 800, 600, 400,
                                  {"context.components"}, {}, widths, nullptr,
                                  "context.components");
  ASSERT_TRUE(layout.supported);
  ASSERT_EQ(std::count_if(layout.rects.begin(), layout.rects.end(),
                          [](const MenuRect &item) { return !item.companion; }), 7);
  ASSERT_EQ(layout.marking_gaps.size(), 1);
  const auto &missing = layout.marking_gaps.front();
  const auto *gap = hit_marking_menu_rect(layout, "context.components",
                                         missing.x+missing.width/2, missing.y+missing.height/2);
  ASSERT_NE(gap, nullptr);
  EXPECT_FALSE(gap->interactive);
  EXPECT_EQ(gap, &layout.marking_gaps.front());
  EXPECT_EQ(rect(layout, gap->id), nullptr);
  // A missing slot is gesture metadata, never an extra drawn/hittable button.
  EXPECT_EQ(hit_menu_rect(layout, gap->x + gap->width / 2, gap->y + 12), nullptr);
}

// This unit exercises native-child ownership independently of Maya's Keep Spacing checkbox.
static MenuSnapshot native_child_snapshot()
{
  auto snapshot = default_snapshot();
  const auto adapt = [&](auto &&self, std::vector<MenuNode> &nodes) -> void {
    for (auto &node : nodes) {
      if (node.id == "tools.move.spacing") {
        node.kind = MenuKind::Menu;
        node.enabled = true;
        node.presentation = "list";
        node.indicator.clear();
        node.children = {{"fixture.native_child", "Fixture action", "", "", "", MenuKind::Disabled, false}};
      }
      self(self, node.children);
    }
  };
  adapt(adapt, snapshot.menus);
  return snapshot;
}

TEST(axismeld_hotbox_menu, RadialHitUsesCurrentCenterAndNeverAnOpenNativeList)
{
  const auto snapshot = native_child_snapshot();
  const auto widths = measured(snapshot);
  auto child = layout_menu(snapshot, 1200, 800, 600, 400,
                            {"tools.move", "tools.move.axis"}, {}, widths, nullptr, "tools.move");
  ASSERT_TRUE(child.supported);
  ASSERT_EQ(child.return_regions.size(), 2);
  const auto &center = child.return_regions.back();
  EXPECT_EQ(hit_marking_menu_rect(child, "tools.move.axis", center.x + 21, center.y + 21),
            nullptr);
  const auto *east = rect(child, "tools.move.axis.rotation");
  ASSERT_NE(east, nullptr);
  const float x = east->x + east->width + 100, y = east->y + 12;
  // A hidden ancestor center may overlap a child's outward region. It is not
  // the active dead zone (including when an ancestor happened to be Views).
  child.return_regions.front() = {"views", x - 10, y - 10, 20, 20, 1};
  const auto *outward = hit_marking_menu_rect(child, "tools.move.axis", x, y);
  ASSERT_NE(outward, nullptr);
  EXPECT_EQ(outward->id, east->id);
  EXPECT_EQ(hit_marking_menu_rect(child, "tools.move", x, y), nullptr);

  const auto native = layout_menu(snapshot, 1200, 800, 600, 400,
                                   {"tools.move", "tools.move.spacing"}, {}, widths, nullptr,
                                   "tools.move");
  ASSERT_TRUE(native.supported);
  const auto *anchor = rect(native, "tools.move.spacing");
  ASSERT_NE(anchor, nullptr);
  EXPECT_EQ(hit_marking_menu_rect(native, "tools.move", 1100, anchor->y + 12), nullptr);
  const auto *leaf = rect(native, "fixture.native_child");
  ASSERT_NE(leaf, nullptr);
  EXPECT_EQ(hit_marking_menu_rect(native, "tools.move", leaf->x + 10, leaf->y + 12), nullptr);
  EXPECT_EQ(hit_menu_rect(native, leaf->x + 10, leaf->y + 12), leaf);
}

TEST(axismeld_hotbox_menu, MarkingRowsStayCompactWithLongLabels)
{
  const auto snapshot = default_snapshot();
  for (const float label_width : {80.0f, 160.0f}) {
    auto widths = measured(snapshot);
    visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = label_width; });
    for (const bool views : {false, true}) {
      const auto layout = layout_menu(snapshot,
                                      1920,
                                      1080,
                                      960,
                                      540,
                                      views ? std::vector<std::string>{"center", "views"} :
                                              std::vector<std::string>{"tools.move"},
                                      {},
                                      widths,
                                      nullptr,
                                      views ? "" : "tools.move");
      ASSERT_TRUE(layout.supported);
      const auto *middle = rect(layout, views ? "views.top" : "tools.move.world");
      const auto *upper = rect(layout, views ? "views.left" : "tools.move.object");
      const auto *lower = rect(layout, views ? "views.back" : "tools.move.axis");
      ASSERT_NE(middle, nullptr);
      ASSERT_NE(upper, nullptr);
      ASSERT_NE(lower, nullptr);
      EXPECT_GE(upper->y - middle->y - middle->height, 4);
      EXPECT_LE(upper->y - middle->y - middle->height, 11);
      EXPECT_LE(middle->y - lower->y - lower->height, 11);
    }
  }
}

TEST(axismeld_hotbox_menu, ToolChildRingReplacesParentButSpaceDirectoryRemains)
{
  auto snapshot = default_snapshot();
  // Independent tree avoids coupling the visibility test to catalog changes.
  MenuNode leaf{"nested.leaf", "Clear", "selection.clear", "", "", MenuKind::Command, true, {}};
  leaf.direction = "SW";
  MenuNode child{"nested.child", "Select", "", "", "", MenuKind::Menu, true, {leaf}};
  child.presentation = "radial";
  child.direction = "S";
  MenuNode root{"nested", "Tool", "", "", "", MenuKind::Menu, true, {child}};
  root.presentation = "radial";
  snapshot.menus[0].children.push_back(root);
  const auto widths = measured(snapshot);
  const auto tool = layout_menu(
      snapshot, 1200, 800, 600, 400, {"nested", "nested.child"}, {}, widths, nullptr, "nested");
  ASSERT_TRUE(tool.supported);
  EXPECT_EQ(rect(tool, "nested.child"), nullptr);
  ASSERT_NE(rect(tool, "nested.leaf"), nullptr);
  const auto space = layout_menu(
      snapshot, 1200, 800, 600, 400, {"nested", "nested.child"}, {}, widths);
  ASSERT_TRUE(space.supported);
  EXPECT_NE(rect(space, "views"), nullptr);
  EXPECT_NE(rect(space, "nested.leaf"), nullptr);
}

TEST(axismeld_hotbox_menu, VisualCenterReturnIsImmediateWithoutStealingVisibleLeaves)
{
  const auto snapshot = native_child_snapshot();
  const auto widths = measured(snapshot);
  const auto layout = layout_menu(snapshot,
                                  1200,
                                  800,
                                  600,
                                  400,
                                  {"tools.move", "tools.move.spacing"},
                                  {},
                                  widths,
                                  nullptr,
                                  "tools.move");
  ASSERT_TRUE(layout.supported);
  EXPECT_EQ(menu_return_target(layout, 614, 414), "tools.move");
  const auto *leaf = rect(layout, "fixture.native_child");
  ASSERT_NE(leaf, nullptr);
  EXPECT_TRUE(menu_return_target(layout, leaf->x + leaf->width / 2, leaf->y + 12).empty());
  const auto edge = layout_menu(
      snapshot, 1200, 800, 0, 0, {"tools.move"}, {}, widths, nullptr, "tools.move");
  ASSERT_TRUE(edge.supported);
  ASSERT_EQ(edge.return_regions.size(), 1);
  const auto &center = edge.return_regions.front();
  EXPECT_EQ(menu_return_target(edge, center.x + center.width / 2, center.y + center.height / 2),
            "tools.move");
  EXPECT_TRUE(menu_return_target(edge, -10, -10).empty());
}

TEST(axismeld_hotbox_menu, ReferenceCentralSpacingDoesNotStretchSideHitTargets)
{
  auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  for (const bool full : {true, false}) {
    snapshot.rows = full ? std::vector<std::string>{"common", "pane", "modeling"} :
                           std::vector<std::string>{"pane"};
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
    ASSERT_TRUE(layout.supported);
    const auto *center = rect(layout, "views"), *left = rect(layout, "center.recent"),
               *right = rect(layout, "center.controls");
    ASSERT_NE(center, nullptr);
    ASSERT_NE(left, nullptr);
    ASSERT_NE(right, nullptr);
    EXPECT_FLOAT_EQ(left->width, 120);
    EXPECT_FLOAT_EQ(right->width, 120);
    EXPECT_NEAR(center->x - left->x - left->width, 83.6f, 0.01f);
    EXPECT_NEAR(right->x - center->x - center->width, 83.6f, 0.01f);
    // Small incomplete reaches must not acquire either side entry's hit rectangle.
    for (float distance : {1.0f, 30.0f, 80.0f}) {
      EXPECT_EQ(hit_menu_rect(layout, center->x - distance, 540), nullptr);
      EXPECT_EQ(hit_menu_rect(layout, center->x + center->width + distance, 540), nullptr);
    }
    EXPECT_EQ(hit_menu_rect(layout, left->x + left->width / 2, 540)->id, "center.recent");
    EXPECT_EQ(hit_menu_rect(layout, right->x + right->width / 2, 540)->id, "center.controls");
  }
}

TEST(axismeld_hotbox_menu, OrdinarySecondaryCommandsUseCompleteNativeColumns)
{
  const auto snapshot = legacy_select_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {"common.select"}, {}, widths);
  ASSERT_TRUE(layout.supported);
  std::set<float> centers_x, centers_y;
  int children = 0;
  for (const auto &item : layout.rects) {
    if (item.depth != 1 || item.id.starts_with("@back:")) {
      continue;
    }
    EXPECT_FLOAT_EQ(item.height, 24.0f);
    centers_x.insert(item.x + item.width / 2);
    centers_y.insert(item.y + item.height / 2);
    children++;
  }
  EXPECT_EQ(children, 8);
  // The synthetic directory proves all eight entries share one continuous native block.
  EXPECT_NE(rect(layout, "fixture.select.0"), nullptr);
  EXPECT_EQ(rect(layout, "@scroll:common.select:next"), nullptr);
  EXPECT_EQ(rect(layout, "@back:common.select"), nullptr);
  EXPECT_EQ(centers_x.size(), 1);
  EXPECT_GE(centers_y.size(), 3);
}

TEST(axismeld_hotbox_menu, EqualWidthRingExposesExtendedEdgesWithoutOverlap)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  widths["views.perspective"] = 104;
  widths["views.front"] = 25;
  widths["center.controls.buttons"] = 151;
  for (const std::vector<std::string> path :
       {std::vector<std::string>{"center", "views"}})
  {
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, path, {}, widths);
    ASSERT_TRUE(layout.supported);
    const float want = path.back() == "views" ? 120 : 211;
    for (const auto &item : layout.rects) {
      if (item.depth != 1 || item.id.starts_with("@") || item.id == "views.style") {
        continue;
      }
      EXPECT_FLOAT_EQ(item.width, want) << item.id;
      for (const float dx : {2.0f, want - 2.0f}) {
        const auto *hit = hit_menu_rect(layout, item.x + dx, item.y + 12);
        ASSERT_NE(hit, nullptr) << item.id;
        EXPECT_EQ(hit->id, item.id);
      }
      for (const auto &other : layout.rects) {
        if (other.depth == item.depth && &other != &item) {
          EXPECT_TRUE(separated_by(item, other, 3.99f)) << item.id << ":" << other.id;
        }
      }
    }
  }
}

TEST(axismeld_hotbox_menu, CompactSecondaryHitTargetsDoNotInheritPrimaryPadding)
{
  const auto snapshot = legacy_select_snapshot();
  const auto widths = measured(snapshot);
  for (const std::vector<std::string> path :
       {std::vector<std::string>{"center", "views"}, std::vector<std::string>{"common.select"}})
  {
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, path, {}, widths);
    ASSERT_TRUE(layout.supported);
    for (const auto &item : layout.rects) {
      if (item.depth == 0) {
        EXPECT_FLOAT_EQ(item.height, 38);
        continue;
      }
      EXPECT_FLOAT_EQ(item.height, 24);
      if (!item.id.starts_with("@")) {
        EXPECT_FLOAT_EQ(item.width, item.id == "views.style" ? 140 : item.id.starts_with("views.") ? 54 : 140) << item.id;
        EXPECT_GE(item.width, widths.at(item.id) + (item.native_menu ? 60 : 16)) << item.id;
      }
      const float x = item.x + item.width / 2, y = item.y + item.height / 2;
      const auto *hit = hit_menu_rect(layout, x, y);
      ASSERT_NE(hit, nullptr);
      EXPECT_EQ(hit->id, item.id);
      const auto *outside = hit_menu_rect(layout, x, item.y + 25);
      EXPECT_TRUE(!outside || outside->id != item.id);
    }
  }
}

TEST(axismeld_hotbox_menu, BothStyleDirectoriesUseContiguousMenuRows)
{
  const auto snapshot = default_snapshot();
  for (const std::vector<std::string> path :
       {std::vector<std::string>{"center", "views", "views.style"},
        std::vector<std::string>{"center.controls", "center.controls.style"}})
  {
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, path, {}, measured(snapshot));
    ASSERT_TRUE(layout.supported);
    const auto *rows = rect(layout, path.back() + ".rows"),
               *zones = rect(layout, path.back() + ".zones"),
               *center = rect(layout, path.back() + ".center");
    ASSERT_NE(rows, nullptr);
    ASSERT_NE(zones, nullptr);
    ASSERT_NE(center, nullptr);
    for (const MenuRect *item : {rows, zones, center}) {
      EXPECT_TRUE(item->native_menu);
      EXPECT_FLOAT_EQ(item->height, 24);
    }
    EXPECT_FLOAT_EQ(rows->x, zones->x);
    EXPECT_FLOAT_EQ(rows->y, zones->y + zones->height);
    EXPECT_FLOAT_EQ(zones->y, center->y + center->height);
    EXPECT_EQ(rect(layout, "@back:" + path.back()), nullptr);
  }
}

TEST(axismeld_hotbox_menu, ControlsRowsRemainInTheirMayaDirectories)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540,
                                  {"center.controls", "center.controls.modeling"}, {}, widths);
  ASSERT_TRUE(layout.supported);
  const auto *common = rect(layout, "center.controls.rows.common");
  const auto *pane = rect(layout, "center.controls.rows.pane");
  const auto *modeling = rect(layout, "center.controls.rows.modeling");
  ASSERT_NE(common, nullptr); ASSERT_NE(pane, nullptr); ASSERT_NE(modeling, nullptr);
  EXPECT_EQ(common->x, pane->x);
  EXPECT_EQ(common->y, pane->y + 24);
  EXPECT_EQ(common->depth, pane->depth);
  EXPECT_EQ(modeling->depth, common->depth + 1);
  for (const auto *item : {common, pane, modeling}) {
    EXPECT_TRUE(item->native_menu); EXPECT_EQ(item->height, 24);
    EXPECT_EQ(hit_menu(layout, item->x + item->width / 2, item->y + 12), item->id);
  }
  EXPECT_EQ(rect(layout, "center.controls.rows"), nullptr);
}

TEST(axismeld_hotbox_menu, ControlsTransparencyUsesAContiguousNativeMenu)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto root = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  const auto layout = layout_menu(snapshot,
                                  1920,
                                  1080,
                                  960,
                                  540,
                                  {"center.controls", "center.controls.transparency"},
                                  {},
                                  widths);
  ASSERT_TRUE(root.supported);
  ASSERT_TRUE(layout.supported);
  const auto *entry = rect(layout, "center.controls.transparency");
  ASSERT_NE(entry, nullptr);
  EXPECT_TRUE(entry->native_menu);
  EXPECT_FLOAT_EQ(entry->height, 24);
  EXPECT_FLOAT_EQ(entry->width, widths.at("center.controls.transparency") + 60);
  const std::array<const char *, 5> ids = {"center.controls.transparency.0",
                                           "center.controls.transparency.25",
                                           "center.controls.transparency.50",
                                           "center.controls.transparency.75",
                                           "center.controls.transparency.100"};
  const auto *first = rect(layout, ids.front());
  ASSERT_NE(first, nullptr);
  const MenuRect *previous = nullptr;
  for (const char *id : ids) {
    const auto *item = rect(layout, id);
    ASSERT_NE(item, nullptr) << id;
    EXPECT_TRUE(item->native_menu);
    EXPECT_FLOAT_EQ(item->height, 24);
    EXPECT_FLOAT_EQ(item->x, first->x);
    if (previous) {
      EXPECT_FLOAT_EQ(previous->y, item->y + 24);
    }
    previous = item;
  }
  EXPECT_EQ(rect(layout, "@back:center.controls.transparency"), nullptr);
  for (const MenuRect &original : root.rects) {
    const auto *preserved = rect(layout, original.id);
    ASSERT_NE(preserved, nullptr) << original.id;
    EXPECT_EQ(preserved->depth, 0) << original.id;
    EXPECT_FALSE(preserved->native_menu) << original.id;
  }
}

TEST(axismeld_hotbox_menu, MappingMenusUseContinuousNativeBlocksAtDesktopSize)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[0] = "internal.blender";
  const auto widths = measured(snapshot);
  const std::array<const char *, 3> owners = {"center.controls.buttons.leftmouse",
                                              "center.controls.buttons.middlemouse",
                                              "center.controls.buttons.rightmouse"};
  const auto parent = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "internal.blender", "center.controls.buttons"}, {}, widths);
  ASSERT_TRUE(parent.supported);
  const MenuRect *previous = nullptr;
  for (const char *owner : owners) {
    const auto *item = rect(parent, owner);
    ASSERT_NE(item, nullptr) << owner;
    EXPECT_TRUE(item->native_menu);
    EXPECT_FALSE(item->native_menu_standalone);
    EXPECT_FLOAT_EQ(item->height, 24);
    EXPECT_FLOAT_EQ(item->width, widths.at(owner) + 60);
    if (previous) {
      EXPECT_FLOAT_EQ(item->x, previous->x);
      EXPECT_FLOAT_EQ(item->width, previous->width);
      EXPECT_FLOAT_EQ(previous->y, item->y + 24);
    }
    previous = item;
  }

  for (const char *owner : owners) {
    SCOPED_TRACE(owner);
    const auto layout = layout_menu(snapshot,
                                    1920,
                                    1080,
                                    960,
                                    540,
                                    {"center", "internal.blender", "center.controls.buttons", owner},
                                    {},
                                    widths);
    ASSERT_TRUE(layout.supported);
    const auto *entry = rect(layout, "center.controls.buttons");
    ASSERT_NE(entry, nullptr);
    EXPECT_TRUE(entry->native_menu);
    EXPECT_FALSE(entry->native_menu_standalone);
    const auto *button = rect(layout, owner);
    ASSERT_NE(button, nullptr);
    EXPECT_TRUE(button->native_menu);
    EXPECT_FALSE(button->native_menu_standalone);
    EXPECT_EQ(rect(layout, std::string("@scroll:") + owner + ":previous"), nullptr);
    EXPECT_EQ(rect(layout, std::string("@scroll:") + owner + ":next"), nullptr);

    const MenuRect *last = nullptr;
    for (const char *suffix : mapping_suffixes) {
      const std::string id = std::string(owner) + "." + suffix;
      const auto *item = rect(layout, id);
      ASSERT_NE(item, nullptr) << id;
      EXPECT_TRUE(item->native_menu);
      EXPECT_FALSE(item->native_menu_standalone);
      EXPECT_FLOAT_EQ(item->height, 24);
      EXPECT_FLOAT_EQ(item->width, widths.at(id) + 40);
      if (last) {
        EXPECT_FLOAT_EQ(item->x, last->x);
        EXPECT_FLOAT_EQ(item->width, last->width);
        EXPECT_FLOAT_EQ(last->y, item->y + 24);
      }
      last = item;
    }
  }
}

TEST(axismeld_hotbox_menu, FullMappingListsReachAllChoicesWithoutPages)
{
  for (const std::string id : {"center.controls.buttons.leftmouse", "center.controls.buttons.middlemouse",
                              "center.controls.buttons.rightmouse"}) {
    for (const auto point : {std::array<float, 2>{0, 0}, {960, 0}, {0, 540}, {960, 540}, {480, 270}}) {
      expect_complete_native(default_snapshot(), id, 960, 540, point[0], point[1]);
    }
  }
}


TEST(axismeld_hotbox_menu, MappingStaleOffsetsNeverHideAnyRow)
{
  expect_complete_native(default_snapshot(), "center.controls.buttons.rightmouse", 960, 540, 480, 270);
}


TEST(axismeld_hotbox_menu, CompleteNativeColumnsStayInsideOffsetSurfaceBounds)
{
  auto snapshot = overflow_snapshot(); snapshot.style = "center";
  snapshot.center_buttons[0] = "fixture.overflow";
  const MenuBounds bounds{37, 81, 997, 621};
  const auto layout = layout_menu_in_bounds(snapshot, bounds, 500, 300,
                  {"center", "fixture.overflow"}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  ASSERT_GT(layout.native_columns.size(), 1);
  for (const auto *rects : {&layout.rects, &layout.native_columns, &layout.occlusion_regions}) {
    for (const auto &item : *rects) {
      EXPECT_GE(item.x, bounds.xmin); EXPECT_GE(item.y, bounds.ymin);
      EXPECT_LE(item.x+item.width, bounds.xmax); EXPECT_LE(item.y+item.height, bounds.ymax);
    }
  }
}


TEST(axismeld_hotbox_menu, VisibleBoundsTranslateAllGeometryAndPreserveViewsClearance)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  // Non-zero left/bottom clipping, with room also reserved for top/right overlap regions.
  const MenuBounds bounds{51.5f, 32.5f, 851.5f, 632.5f};
  int compared_gaps = 0;
  for (const std::string owner : {"views", "tools.select", "tools.move", "tools.rotate",
                                  "tools.scale", "context.components", "context.create", "context.modeling_object",
                                  "tools.move.axis"}) {
    const bool views = owner == "views";
    for (const auto center : {std::array<float, 2>{0, 0}, {400, 300}, {800, 600}}) {
      const std::array<float, 2> popup{center[0], center[1]};
      const std::array<float, 2> shifted_popup{popup[0] + bounds.xmin,
                                              popup[1] + bounds.ymin};
      const auto local = layout_menu(snapshot, 800, 600, center[0], center[1],
                                      {owner}, {}, widths, views ? &popup : nullptr,
                                      views ? "" : owner);
      const auto shifted = layout_menu_in_bounds(
          snapshot, bounds, center[0] + bounds.xmin, center[1] + bounds.ymin,
          {owner}, {}, widths, views ? &shifted_popup : nullptr, views ? "" : owner);
      ASSERT_TRUE(local.supported) << owner;
      ASSERT_TRUE(shifted.supported) << owner;
      auto compare = [&](const auto &before, const auto &after) {
        ASSERT_EQ(before.size(), after.size());
        for (int i = 0; i < int(before.size()); i++) {
          const auto &a = before[i], &b = after[i];
          EXPECT_EQ(a.id, b.id);
          EXPECT_FLOAT_EQ(a.x + bounds.xmin, b.x) << a.id;
          EXPECT_FLOAT_EQ(a.y + bounds.ymin, b.y) << a.id;
          EXPECT_FLOAT_EQ(a.width, b.width) << a.id;
          EXPECT_FLOAT_EQ(a.height, b.height) << a.id;
          EXPECT_EQ(a.depth, b.depth);
        }
      };
      compare(local.rects, shifted.rects);
      compare(local.return_regions, shifted.return_regions);
      compare(local.marking_gaps, shifted.marking_gaps);
      ASSERT_FALSE(local.return_regions.empty());
      compared_gaps += int(local.marking_gaps.size());
      for (const auto &item : shifted.rects) {
        EXPECT_GE(item.x, bounds.xmin) << item.id;
        EXPECT_GE(item.y, bounds.ymin) << item.id;
        EXPECT_LE(item.x + item.width, bounds.xmax) << item.id;
        EXPECT_LE(item.y + item.height, bounds.ymax) << item.id;
      }
      // Compare actual hit/return/outward cancellation, including absent directions and edges.
      for (float y = -50; y <= 650; y += 10) {
        for (float x = -50; x <= 850; x += 10) {
          const float sx = x + bounds.xmin, sy = y + bounds.ymin;
          EXPECT_EQ(hit_menu(local, x, y), hit_menu(shifted, sx, sy));
          EXPECT_EQ(menu_return_target(local, x, y), menu_return_target(shifted, sx, sy));
          const auto *a = hit_marking_menu_rect(local, owner, x, y);
          const auto *b = hit_marking_menu_rect(shifted, owner, sx, sy);
          EXPECT_EQ(a ? a->id : "", b ? b->id : "");
        }
      }
    }
  }
  EXPECT_GT(compared_gaps, 0);
}

TEST(axismeld_hotbox_menu, VisibleBoundsClampOnlyLayoutAnchorsAndRejectInsufficientSpace)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const MenuBounds bounds{100, 50, 900, 650};
  const std::array<float, 2> origin{990, 700};
  const auto layout = layout_menu_in_bounds(snapshot, bounds, 10, 20, {"views"}, {},
                                            widths, &origin);
  ASSERT_TRUE(layout.supported);
  EXPECT_FLOAT_EQ(origin[0], 990);
  EXPECT_FLOAT_EQ(origin[1], 700);
  for (const auto &item : layout.rects) {
    EXPECT_GE(item.x, bounds.xmin);
    EXPECT_GE(item.y, bounds.ymin);
    EXPECT_LE(item.x + item.width, bounds.xmax);
    EXPECT_LE(item.y + item.height, bounds.ymax);
  }
  const float nan = std::numeric_limits<float>::quiet_NaN();
  for (const MenuBounds small : {MenuBounds{100, 50, 100, 650}, {100, 50, 900, 50},
                                  {100, 50, 99, 650}, {100, 50, 439, 650},
                                  {100, 50, 900, 249}, {nan, 50, 900, 650}}) {
    const auto rejected = layout_menu_in_bounds(snapshot, small, 200, 100,
                                                  {"views"}, {}, widths);
    EXPECT_FALSE(rejected.supported);
    EXPECT_TRUE(rejected.rects.empty());
    EXPECT_TRUE(rejected.return_regions.empty());
    EXPECT_TRUE(rejected.marking_gaps.empty());
    EXPECT_TRUE(rejected.native_scroll_bounds.empty());
  }
}

TEST(axismeld_hotbox_menu, NoMenuScrollTransitionCanChangeCompleteContents)
{
  MenuLayout layout{{}, true};
  for (const int stored : {-3, 0, 1, 999}) {
    for (const int delta : {-1, 1}) {
      EXPECT_EQ(menu_scroll_offset_transition(layout, "common.display", stored, delta, 56), 0);
    }
  }
  expect_complete_native(default_snapshot(), "common.display");
}


TEST(axismeld_hotbox_menu, CompleteMappingAndOrdinaryDirectoriesDoNotDrift)
{
  expect_complete_native(default_snapshot(), "center.controls.buttons.leftmouse");
  expect_complete_native(legacy_select_snapshot(), "common.select");
}


TEST(axismeld_hotbox_menu, CompleteShortSettingsUseActualNarrowSurfaceCorners)
{
  for (const std::string id : {"views.style", "center.controls.style", "center.controls.modeling",
                              "center.controls.transparency"}) {
    for (const auto point : {std::array<float, 2>{0, 0}, {392, 0}, {0, 260}, {392, 260}}) {
      expect_complete_native(default_snapshot(), id, 392, 260, point[0], point[1]);
    }
  }
}


TEST(axismeld_hotbox_menu, FullStylePopupDoesNotCoverItsDirectEntry)
{
  auto snapshot = default_snapshot(); snapshot.style = "center";
  const auto widths = measured(snapshot);
  for (const auto point : {std::array<float, 2>{0, 0}, {960, 540}, {480, 270}}) {
    const auto layout = layout_menu(snapshot, 960, 540, point[0], point[1],
                                    {"center", "views", "views.style"}, {}, widths);
    ASSERT_TRUE(layout.supported);
    const auto *entry = rect(layout, "views.style"); ASSERT_NE(entry, nullptr);
    for (const auto &column : layout.native_columns) {
      if (column.owner != "views.style") { continue; }
      EXPECT_TRUE(column.x >= entry->x+entry->width || column.x+column.width <= entry->x ||
                  column.y >= entry->y+entry->height || column.y+column.height <= entry->y);
    }
  }
}


TEST(axismeld_hotbox_menu, UniformViewRingKeepsCompactSpacingWithoutOverlap)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "views"}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *side = rect(layout, "views.side");
  ASSERT_NE(side, nullptr);
  EXPECT_EQ(hit_menu(layout, side->x + 2, side->y + 12), "views.side");
  const auto *style = rect(layout, "views.style"), *front = rect(layout, "views.front");
  ASSERT_NE(style, nullptr);
  ASSERT_NE(front, nullptr);
  EXPECT_NEAR(front->y - style->y - style->height, 4.0f, .01f);
  for (const auto &item : layout.rects) {
    if (item.depth != 1) {
      continue;
    }
    for (const auto &other : layout.rects) {
      if (&item == &other || other.depth != 1) {
        continue;
      }
      EXPECT_TRUE(
          item.x + item.width + 3.99f <= other.x || other.x + other.width + 3.99f <= item.x ||
          item.y + item.height + 3.99f <= other.y || other.y + other.height + 3.99f <= item.y)
          << item.id << " / " << other.id;
    }
  }
}

TEST(axismeld_hotbox_menu, StyleEntriesUseNativeMenuTargetsWhileViewActionsStayHotbox)
{
  const auto snapshot = default_snapshot();
  for (const std::vector<std::string> path :
       {std::vector<std::string>{"center", "views", "views.style"},
        std::vector<std::string>{"center.controls", "center.controls.style"}})
  {
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, path, {}, measured(snapshot));
    ASSERT_TRUE(layout.supported);
    const auto *entry = rect(layout, path.back());
    ASSERT_NE(entry, nullptr);
    EXPECT_TRUE(entry->native_menu);
    EXPECT_FLOAT_EQ(entry->height, 24);
    for (const auto &item : layout.rects) {
      if (item.direction_label || item.depth == 0) {
        EXPECT_FALSE(item.native_menu);
      }
    }
  }
}

TEST(axismeld_hotbox_menu, ViewOverlayRetainsParentWithoutSecondaryCenterOrRootHits)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto main = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  const auto views = layout_menu(snapshot, 1920, 1080, 960, 540, {"center", "views"}, {}, widths);
  ASSERT_TRUE(views.supported);
  const auto *parent = rect(views, "views");
  ASSERT_NE(parent, nullptr);
  EXPECT_EQ(parent->depth, 0);
  EXPECT_FLOAT_EQ(parent->x, rect(main, "views")->x);
  EXPECT_FLOAT_EQ(parent->y, rect(main, "views")->y);
  EXPECT_EQ(hit_menu_rect(views, 960, 540), nullptr);
  for (const auto &item : main.rects) {
    ASSERT_NE(rect(views, item.id), nullptr) << item.id;
    EXPECT_FLOAT_EQ(rect(views, item.id)->x, item.x);
    EXPECT_FLOAT_EQ(rect(views, item.id)->y, item.y);
  }
  const auto *style = rect(views, "views.style"), *front = rect(views, "views.front");
  ASSERT_NE(style, nullptr);
  ASSERT_NE(front, nullptr);
  EXPECT_LE(style->y + style->height + 3.99f, front->y);
  EXPECT_EQ(rect(views, "@back:views"), nullptr);
}

TEST(axismeld_hotbox_menu, ViewStyleOpensAParentRetainingVerticalList)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "views", "views.style"}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *style = rect(layout, "views.style"), *rows = rect(layout, "views.style.rows"),
             *zones = rect(layout, "views.style.zones"),
             *center = rect(layout, "views.style.center");
  ASSERT_NE(style, nullptr);
  ASSERT_NE(rows, nullptr);
  ASSERT_NE(zones, nullptr);
  ASSERT_NE(center, nullptr);
  EXPECT_GE(rows->x, style->x + style->width);
  EXPECT_FLOAT_EQ(rows->x, zones->x);
  EXPECT_FLOAT_EQ(rows->x, center->x);
  EXPECT_GT(rows->y, zones->y);
  EXPECT_GT(zones->y, center->y);
  EXPECT_NE(rect(layout, "views.front"), nullptr);
  EXPECT_EQ(rect(layout, "@back:views.style"), nullptr);
}

TEST(axismeld_hotbox_menu, ViewOverlayUsesFullLabelsAndAbsentNorthEastCamera)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  const std::array<float, 2> origin = {972, 544};
  const auto layout = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "views"}, {}, widths, &origin);
  ASSERT_TRUE(layout.supported);
  const auto *root = rect(layout, "views"), *camera = view_reference_rect(layout, "views.camera");
  ASSERT_NE(root, nullptr);
  ASSERT_NE(camera, nullptr);
  EXPECT_FLOAT_EQ(root->x + root->width / 2, 960);
  EXPECT_FLOAT_EQ(root->y + root->height / 2, 540);
  EXPECT_GT(camera->x + camera->width / 2, origin[0]);
  EXPECT_GT(camera->y + camera->height / 2, origin[1]);
  EXPECT_FALSE(camera->interactive);
  EXPECT_EQ(rect(layout, "views.camera"), nullptr);
  EXPECT_TRUE(
      hit_menu(layout, camera->x + camera->width / 2, camera->y + camera->height / 2).empty());
  for (const auto &item : layout.rects) {
    EXPECT_FALSE(item.compact_label);
  }
  const auto *perspective = rect(layout, "views.perspective");
  ASSERT_NE(perspective, nullptr);
  EXPECT_FLOAT_EQ(perspective->width, widths.at("views.perspective") + 16);
}

TEST(axismeld_hotbox_menu, NativeCascadeKeepsVisibleParentNativeSiblingsReachable)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[0] = "internal.blender";
  for (const std::vector<std::string> path :
       {std::vector<std::string>{"center", "internal.blender", "center.controls.buttons"},
        std::vector<std::string>{
            "center", "internal.blender", "center.controls.buttons", "center.controls.buttons.leftmouse"}})
  {
    const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, path, {}, measured(snapshot));
    ASSERT_TRUE(layout.supported);
    const auto *other = rect(layout, "internal.blender.select");
    ASSERT_NE(other, nullptr);
    const auto *hit = hit_menu_rect(
        layout, other->x + other->width / 2, other->y + other->height / 2);
    ASSERT_NE(hit, nullptr);
    EXPECT_EQ(hit->id, other->id);
    const auto *entry = rect(layout, "center.controls.buttons");
    ASSERT_NE(entry, nullptr);
    hit = hit_menu_rect(layout, entry->x + entry->width / 2, entry->y + entry->height / 2);
    ASSERT_NE(hit, nullptr);
    EXPECT_EQ(hit->id, entry->id);
    const auto *sibling = rect(layout, "center.controls.buttons.rightmouse");
    ASSERT_NE(sibling, nullptr);
    hit = hit_menu_rect(layout, sibling->x + sibling->width / 2, sibling->y + sibling->height / 2);
    ASSERT_NE(hit, nullptr);
    EXPECT_EQ(hit->id, sibling->id);
  }
}

TEST(axismeld_hotbox_menu, NativeCascadeTouchesItsDirectAnchor)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[0] = "internal.blender";
  for (const float cx : {200.0f, 960.0f, 1700.0f}) {
    const auto layout = layout_menu(
        snapshot,
        1920,
        1080,
        cx,
        540,
        {"center", "internal.blender", "center.controls.buttons", "center.controls.buttons.leftmouse"},
        {},
        measured(snapshot));
    ASSERT_TRUE(layout.supported);
    for (const auto &pair :
         {std::pair{"center.controls.buttons", "center.controls.buttons.leftmouse"},
          std::pair{"center.controls.buttons.leftmouse",
                    "center.controls.buttons.leftmouse.none"}})
    {
      const auto *anchor = rect(layout, pair.first), *child = rect(layout, pair.second);
      ASSERT_NE(anchor, nullptr);
      ASSERT_NE(child, nullptr);
      EXPECT_TRUE(std::abs(child->x - anchor->x - anchor->width) < .01f ||
                  std::abs(anchor->x - child->x - child->width) < .01f);
    }
  }
}

TEST(axismeld_hotbox_menu, ActiveNativeListDoesNotExposeUnderlyingRootHitTargets)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[0] = "internal.blender";
  const auto layout = layout_menu(snapshot,
                                  1920,
                                  1080,
                                  960,
                                  540,
                                  {"center", "internal.blender", "center.controls.buttons"},
                                  {},
                                  measured(snapshot));
  ASSERT_TRUE(layout.supported);
  for (const auto &item : layout.rects) {
    if (item.depth == 0) {
      const auto *hit = hit_menu_rect(layout, item.x + item.width / 2, item.y + item.height / 2);
      EXPECT_TRUE(!hit || hit->depth > 0) << item.id;
    }
    else {
      EXPECT_TRUE(item.depth == 1 || item.depth == 2 || item.depth == 3) << item.id;
    }
  }
  EXPECT_EQ(rect(layout, "@back:center.controls.buttons"), nullptr);
  const auto *entry = rect(layout, "center.controls.buttons");
  const auto *button = rect(layout, "center.controls.buttons.leftmouse");
  ASSERT_NE(entry, nullptr);
  ASSERT_NE(button, nullptr);
  EXPECT_FALSE(entry->native_menu_standalone);
  EXPECT_FALSE(button->native_menu_standalone);
}

TEST(axismeld_hotbox_menu, SevenViewsKeepTaperedRowsAndOriginalDirections)
{
  auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  for (const char *id : {"views.perspective",
                         "views.side",
                         "views.front",
                         "views.top",
                         "views.left",
                         "views.back",
                         "views.bottom"})
  {
    widths[id] = 38;
  }
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {"center", "views"}, {}, widths);
  ASSERT_TRUE(layout.supported);
  const auto *n = rect(layout, "views.perspective"), *e = rect(layout, "views.side"),
             *s = rect(layout, "views.front"), *w = rect(layout, "views.top");
  ASSERT_NE(n, nullptr);
  ASSERT_NE(e, nullptr);
  ASSERT_NE(s, nullptr);
  ASSERT_NE(w, nullptr);
  const float cx = (n->x + n->width / 2 + s->x + s->width / 2) / 2;
  const float cy = (e->y + e->height / 2 + w->y + w->height / 2) / 2;
  const float rx = (e->x + e->width / 2 - w->x - w->width / 2) / 2;
  const float ry = (n->y - s->y) / 2;
  ASSERT_GT(rx, ry);
  ASSERT_GT(ry, 0);
  for (const auto &[id, signs] : std::array<std::pair<const char *, std::array<int, 2>>, 3>{
           {{"views.left", {-1, 1}}, {"views.back", {-1, -1}}, {"views.bottom", {1, -1}}}})
  {
    const auto *item = rect(layout, id);
    ASSERT_NE(item, nullptr);
    const float nx = (item->x + item->width / 2 - cx) / rx;
    const float ny = (item->y + item->height / 2 - cy) / ry;
    EXPECT_NEAR(std::abs(ny), .5f, .001f);  // Equal row steps, not equal angular steps.
    EXPECT_GT(nx * signs[0], 0);
    EXPECT_GT(ny * signs[1], 0);
    EXPECT_LT(std::abs(nx), .9f);  // Diagonals cannot remain at the old rectangular corners.
    EXPECT_LT(std::abs(ny), .9f);
    EXPECT_EQ(hit_menu(layout, item->x + item->width / 2, item->y + item->height / 2), id);
  }
}

TEST(axismeld_hotbox_menu, WindowAtTwoTimesScaleShowsCompleteSecondaryColumns)
{
  expect_complete_native(default_snapshot(), "common.select", 960, 540, 480, 270);
  expect_complete_native(default_snapshot(), "common.display", 960, 540, 480, 270);
}


TEST(axismeld_hotbox_menu, AllPrimaryTitlesRemainVisibleWithoutCompactGroupShells)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(snapshot, 960, 540, 480, 270, {}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  for (const auto &group : snapshot.menus) {
    if (group.id != "common" && group.id != "pane" && group.id != "modeling") { continue; }
    for (const auto &node : group.children) { EXPECT_NE(rect(layout, node.id), nullptr) << node.id; }
    EXPECT_EQ(rect(layout, group.id), nullptr);
  }
  for (const auto &node : layout.rects) { EXPECT_FALSE(node.id.starts_with("@scroll:")); }
}


TEST(axismeld_hotbox_menu, SmallViewportRefusesMenus)
{
  MenuSnapshot snapshot{};
  EXPECT_FALSE(layout_menu(snapshot, 339, 200, 100, 100, {}, {}, {}).supported);
  EXPECT_FALSE(layout_menu(snapshot, 340, 199, 100, 100, {}, {}, {}).supported);
}

TEST(axismeld_hotbox_menu, MissingInvalidOrUnrenderableMeasurementsRefuseAtomically)
{
  const MenuSnapshot snapshot = default_snapshot();
  auto widths = measured(snapshot);
  widths.erase("views.left");
  EXPECT_FALSE(layout_menu(snapshot, 480, 320, 240, 160, {}, {}, widths).supported);
  for (const float invalid : {-1.0f,
                              std::numeric_limits<float>::infinity(),
                              std::numeric_limits<float>::quiet_NaN(),
                              1000.0f})
  {
    widths = measured(snapshot);
    widths["views.left"] = invalid;
    const MenuLayout layout = layout_menu(snapshot, 480, 320, 240, 160, {"center", "views"}, {}, widths);
    EXPECT_FALSE(layout.supported);
    EXPECT_TRUE(layout.rects.empty());
  }
  EXPECT_FALSE(layout_menu(snapshot, NAN, 320, 240, 160, {}, {}, measured(snapshot)).supported);
}

TEST(axismeld_hotbox_menu, VisibleViewsCenterRefusesAnOversizedLabelAtomically)
{
  MenuSnapshot snapshot = default_snapshot();
  auto widths = measured(snapshot);
  widths["views"] = 2000;
  for (const char *style : {"rows", "zones", "center"}) {
    snapshot.style = style;
    const MenuLayout layout = layout_menu(snapshot, 480, 320, 240, 160, {}, {}, widths);
    EXPECT_FALSE(layout.supported) << style;
    EXPECT_TRUE(layout.rects.empty()) << style;
  }
}

TEST(axismeld_hotbox_menu, DeepestRectangleWinsAndDisabledOccludesWithoutDispatch)
{
  MenuLayout layout{{{"title", 0, 0, 100, 100, 0}, {"leaf", 20, 20, 40, 40, 1}}, true};
  EXPECT_EQ(hit_menu(layout, 30, 30), "leaf");
  layout.rects.push_back({"disabled", 25, 25, 20, 20, 2, false});
  EXPECT_EQ(hit_menu(layout, 30, 30), "");
  EXPECT_EQ(hit_menu(layout, 10, 10), "title");
  EXPECT_EQ(hit_menu(layout, NAN, 10), "");
  layout.supported = false;
  EXPECT_EQ(hit_menu(layout, 10, 10), "");
}

TEST(axismeld_hotbox_menu, RestrictedClosePolicyUsesLiteralCommandIdentities)
{
  for (const char *command : {"view.perspective",
                              "view.side",
                              "view.left",
                              "view.back",
                              "view.bottom",
                              "view.front",
                              "view.top",
                              "view.focus_selected",
                              "view.frame_all",
                              "view.wireframe",
                              "view.shaded"})
  {
    EXPECT_FALSE(hotbox_command_closes(command)) << command;
  }
  for (const char *command : {"view.toggle_quad",
                              "selection.toggle_component",
                              "selection.vertex_mode",
                              "selection.edge_mode",
                              "selection.face_mode",
                              "selection.select_all",
                              "selection.grow",
                              "selection.shrink",
                              "transform.move",
                              "transform.rotate",
                              "transform.scale",
                              "view.unknown",
                              "hotbox.open",
                              "",
                              "setting.style"})
  {
    EXPECT_TRUE(hotbox_command_closes(command)) << command;
  }
}

TEST(axismeld_hotbox_menu, RealDefaultTreeHasClickablePathsAtCornersAndCenter)
{
  MenuSnapshot snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  for (const auto size : {std::array<float, 2>{1920, 1080}}) {
    for (const auto point : {std::array<float, 2>{0, 0},
                             {size[0], 0},
                             {0, size[1]},
                             {size[0], size[1]},
                             {size[0] / 2, size[1] / 2}})
    {
      SCOPED_TRACE(testing::Message()
                   << size[0] << "x" << size[1] << " @ " << point[0] << "," << point[1]);
      const auto initial = layout_menu(
          snapshot, size[0], size[1], point[0], point[1], {}, {}, widths);
      ASSERT_TRUE(initial.supported);
      const MenuRect *center = rect(initial, "views");
      ASSERT_NE(center, nullptr);
      EXPECT_LE(center->x, point[0]);
      EXPECT_GE(center->x + center->width, point[0]);
      EXPECT_LE(center->y, point[1]);
      EXPECT_GE(center->y + center->height, point[1]);
      EXPECT_EQ(hit_menu(initial, point[0], point[1]), "views");
      std::set<std::string> reached;
      std::function<void(const std::vector<MenuNode> &,
                         const std::string &,
                         std::vector<std::string>,
                         std::unordered_map<std::string, int>, bool)>
          browse;
      browse = [&](const std::vector<MenuNode> &nodes,
                   const std::string &owner,
                   std::vector<std::string> path,
                   std::unordered_map<std::string, int> offsets, const bool companion) {
        for (int scroll = 0; scroll < int(nodes.size()); scroll++) {
          offsets[owner] = scroll;
          std::string_view radial_root = object_modeling_root;
          if (companion && !path.empty()) {
            for (const auto &[root, menu] : companion_roots) {
              if (path.front() == menu) { radial_root = root; break; }
            }
          }
          const auto layout = companion ?
              layout_menu(snapshot, size[0], size[1], point[0], point[1],
                          {std::string(radial_root)}, offsets, widths, nullptr,
                          radial_root, path) :
              layout_menu(snapshot, size[0], size[1], point[0], point[1], path, offsets, widths);
          ASSERT_TRUE(layout.supported);
          for (const auto &item : layout.rects) {
            EXPECT_GE(item.x, 0);
            EXPECT_GE(item.y, 0);
            EXPECT_LE(item.x + item.width, size[0]);
            EXPECT_LE(item.y + item.height, size[1]) << item.id;
          }
          for (const MenuNode &node : nodes) {
            const MenuRect *item = rect(layout, node.id);
            if (!item) {
              continue;
            }
            // An options cell is a separately reachable action even when its main row is disabled.
            if (node.kind != MenuKind::Menu && !node.children.empty()) {
              ASSERT_EQ(node.children.size(), 1);
              const auto &option = node.children[0];
              const auto *cell = rect(layout, option.id);
              ASSERT_NE(cell, nullptr) << option.id;
              EXPECT_TRUE(cell->option_box);
              EXPECT_EQ(cell->width, 24);
              EXPECT_EQ(cell->x, item->x + item->width);
              const auto option_hit = hit_menu(layout, cell->x + 12, cell->y + cell->height / 2);
              EXPECT_EQ(option_hit, option.enabled ? option.id : "") << option.id;
              reached.insert(option.id);
            }
            const std::string hit = hit_menu(
                layout, item->x + item->width / 2, item->y + item->height / 2);
            if (!node.enabled || node.kind == MenuKind::Separator ||
                node.kind == MenuKind::Disabled)
            {
              EXPECT_TRUE(hit.empty()) << node.id;
              reached.insert(node.id);
              continue;
            }
            if (hit != node.id || reached.count(node.id)) {
              continue;
            }
            reached.insert(node.id);
            if (node.kind == MenuKind::Menu) {
              auto child_path = path;
              child_path.push_back(node.id);
              browse(node.children, node.id, child_path, offsets, companion);
            }
          }
          // Every non-terminal page has a visible, hittable forward control.
          if (const MenuRect *next = rect(layout, "@scroll:" + owner + ":next")) {
            if (next->interactive) {
              EXPECT_EQ(hit_menu(layout, next->x + next->width / 2, next->y + next->height / 2),
                        next->id);
            }
            else {
              break;
            }
          }
          else {
            break;
          }
        }
      };
      for (const MenuNode &row : snapshot.menus) {
        if (companion_owner(row.id) == row.id) {
          // Companion roots enter only through their associated radial tool roots.
          browse(row.children, row.id, {row.id}, {}, true);
        }
        else if (row.id == "internal") {
          // Internal adapters have an explicit mapped entry, never a visible main-row title.
          // Traverse that entry and every descendant instead of silently omitting hidden roots.
          const auto saved = snapshot.center_buttons[0];
          snapshot.center_buttons[0] = row.id;
          browse(row.children, row.id, {"center", row.id}, {}, false);
          snapshot.center_buttons[0] = saved;
        }
        else {
          browse(row.children, row.id, {}, {}, false);
        }
      }
      for (const MenuNode &row : snapshot.menus) {
        visit(row.children, [&](const MenuNode &node) {
          // The seven-view ring has an empty NE sector rather than the old list separator.
          if (node.id != "views.separator.style") {
            EXPECT_TRUE(reached.count(node.id)) << node.id;
          }
        });
      }
    }
  }
}

TEST(axismeld_hotbox_menu, CompleteChildrenKeepParentsWithoutStoredPageState)
{
  auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto parent = layout_menu(snapshot, 1920, 1080, 960, 540, {"common.display"}, {}, widths);
  const auto child = layout_menu(snapshot, 1920, 1080, 960, 540,
                                {"common.display", "maya.common.display.object_display"}, {}, widths);
  ASSERT_TRUE(parent.supported); ASSERT_TRUE(child.supported);
  EXPECT_TRUE(child.native_scroll_bounds.empty());
  EXPECT_NE(rect(child, "maya.common.display.object_display"), nullptr);
  const auto returned = layout_menu(snapshot, 1920, 1080, 960, 540, {"common.display"},
                                    {{"common.display", 999}}, widths);
  ASSERT_EQ(returned.rects.size(), parent.rects.size());
  for (const auto &item : parent.rects) {
    const auto *same = rect(returned, item.id);
    ASSERT_NE(same, nullptr); EXPECT_EQ(same->x, item.x); EXPECT_EQ(same->y, item.y);
  }
}


TEST(axismeld_hotbox_menu, FullSizeRowsKeepCanonicalVerticalOrderAndCentralSiblings)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *common = rect(layout, "common.file"), *pane = rect(layout, "pane.view"),
             *center = rect(layout, "views"), *recent = rect(layout, "center.recent"),
             *controls = rect(layout, "center.controls"),
             *modeling = rect(layout, "modeling.mesh");
  ASSERT_NE(common, nullptr);
  ASSERT_NE(pane, nullptr);
  ASSERT_NE(center, nullptr);
  ASSERT_NE(recent, nullptr);
  ASSERT_NE(controls, nullptr);
  ASSERT_NE(modeling, nullptr);
  EXPECT_GT(common->y, pane->y);
  EXPECT_GT(pane->y, center->y);
  EXPECT_GT(center->y, modeling->y);
  EXPECT_EQ(recent->y, center->y);
  EXPECT_EQ(controls->y, center->y);
  EXPECT_LT(recent->x, center->x);
  EXPECT_GT(controls->x, center->x);
}

TEST(axismeld_hotbox_menu, StandardMainCompositionKeepsOuterTaperAndIsolatedCentralButtons)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  // Independently bounded label measurements: all default siblings fit a desktop viewport.
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  ASSERT_TRUE(layout.supported);
  const auto *center = rect(layout, "views");
  ASSERT_NE(center, nullptr);
  std::map<float, std::array<float, 2>> spans;
  for (const MenuRect &item : layout.rects) {
    ASSERT_EQ(item.depth, 0);
    EXPECT_FALSE(item.id.starts_with("@scroll:"));
    auto [span, inserted] = spans.try_emplace(item.y,
                                              std::array<float, 2>{item.x, item.x + item.width});
    if (!inserted) {
      span->second[0] = std::min(span->second[0], item.x);
      span->second[1] = std::max(span->second[1], item.x + item.width);
    }
    EXPECT_EQ(hit_menu_rect(layout, item.x + item.width / 2, item.y + item.height / 2)->id,
              item.id);
  }
  ASSERT_EQ(spans.size(), 5);
  std::vector<float> row_widths;
  for (const auto &[y, span] : spans) {
    if (y != center->y) {
      EXPECT_NEAR((span[0] + span[1]) / 2, 960, 0.01);
    }
    row_widths.push_back(span[1] - span[0]);
  }
  EXPECT_LT(row_widths[0], row_widths[1]);
  EXPECT_LT(row_widths[2], row_widths[1]);
  EXPECT_LT(row_widths[2], row_widths[3]);
  EXPECT_GT(row_widths[3], row_widths[4]);
  const auto modeling_root = std::find_if(snapshot.menus.begin(), snapshot.menus.end(),
      [](const MenuNode &node) { return node.id == "modeling"; });
  ASSERT_NE(modeling_root, snapshot.menus.end());
  const auto &modeling = modeling_root->children;
  const MenuRect *previous = nullptr;
  for (const auto &node : modeling) {
    const auto *item = rect(layout, node.id);
    ASSERT_NE(item, nullptr) << node.id;
    EXPECT_LT(item->y, center->y);
    if (previous) {
      EXPECT_TRUE(item->y < previous->y ||
                  (item->y == previous->y && item->x >= previous->x + previous->width));
    }
    previous = item;
  }
  const auto companion = std::find_if(snapshot.menus.begin(), snapshot.menus.end(),
      [](const MenuNode &node) { return node.id == object_modeling_menu; });
  ASSERT_NE(companion, snapshot.menus.end());
  EXPECT_EQ(rect(layout, companion->id), nullptr);
  visit(companion->children, [&](const MenuNode &node) { EXPECT_EQ(rect(layout, node.id), nullptr); });
}

TEST(axismeld_hotbox_menu, InwardRowsKeepCanonicalOrderAtTrueCorners)
{
  const auto snapshot = default_snapshot();
  for (const auto point : {std::array<float, 2>{0, 0}, {960, 0}, {0, 540}, {960, 540}}) {
    const auto layout = layout_menu(
        snapshot, 960, 540, point[0], point[1], {}, {}, measured(snapshot));
    ASSERT_TRUE(layout.supported);
    const auto *common = rect(layout, "common.file"), *pane = rect(layout, "pane.view"),
               *recent = rect(layout, "center.recent"), *modeling = rect(layout, "modeling.mesh");
    ASSERT_NE(common, nullptr);
    ASSERT_NE(pane, nullptr);
    ASSERT_NE(recent, nullptr);
    ASSERT_NE(modeling, nullptr);
    EXPECT_GT(common->y, pane->y);
    EXPECT_GT(pane->y, recent->y);
    EXPECT_GT(recent->y, modeling->y);
    const auto *center = rect(layout, "views");
    ASSERT_NE(center, nullptr);
    for (const auto &item : layout.rects) {
      if (item.id == "views") {
        continue;
      }
      EXPECT_TRUE(item.x >= center->x + center->width || item.x + item.width <= center->x ||
                  item.y >= center->y + center->height || item.y + item.height <= center->y);
    }
  }
}

TEST(axismeld_hotbox_menu, HidingRowsDoesNotMovePaneBelowTheCentralRow)
{
  auto snapshot = default_snapshot();
  snapshot.rows = {"common", "pane"};
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *pane = rect(layout, "pane.view"), *center = rect(layout, "views");
  ASSERT_NE(pane, nullptr);
  ASSERT_NE(center, nullptr);
  EXPECT_GT(pane->y, center->y);
  EXPECT_EQ(rect(layout, "modeling.mesh"), nullptr);
}

TEST(axismeld_hotbox_menu, EveryRowSubsetAvoidsCentralButtonAtTopAndBottomEdges)
{
  const std::array<std::string, 3> row_ids = {"common", "pane", "modeling"};
  for (const auto size : {std::array<float, 2>{960, 540}, {1920, 1080}}) {
    for (int mask = 0; mask < 8; mask++) {
      auto snapshot = default_snapshot();
      snapshot.rows.clear();
      for (int index = 0; index < 3; index++) {
        if (mask & (1 << index)) {
          snapshot.rows.push_back(row_ids[index]);
        }
      }
      for (const float x : {0.0f, size[0] / 2, size[0]}) {
        for (const float y : {0.0f, size[1]}) {
          SCOPED_TRACE(testing::Message()
                       << size[0] << "x" << size[1] << " rows=" << mask << " @ " << x << "," << y);
          const auto layout = layout_menu(
              snapshot, size[0], size[1], x, y, {}, {}, measured(snapshot));
          ASSERT_TRUE(layout.supported);
          const auto *center = rect(layout, "views");
          ASSERT_NE(center, nullptr);
          EXPECT_EQ(hit_menu(layout, x, y), "views");
          for (const auto &item : layout.rects) {
            if (item.id == "views") {
              continue;
            }
            EXPECT_TRUE(item.x >= center->x + center->width || item.x + item.width <= center->x ||
                        item.y >= center->y + center->height || item.y + item.height <= center->y)
                << item.id << " overlaps central button";
          }
        }
      }
    }
  }
}

TEST(axismeld_hotbox_menu, CenterOnlyCanOpenAGlobalMappedMenu)
{
  auto snapshot = default_snapshot();
  snapshot.style = "center";
  snapshot.center_buttons[2] = "common.select";
  const auto layout = layout_menu(snapshot,
                                  480,
                                  320,
                                  0,
                                  0,
                                  {"center", "common.select"},
                                  {{"common.select", 2}},
                                  measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *leaf = rect(layout, "maya.common.select.all");
  ASSERT_NE(leaf, nullptr);
  EXPECT_EQ(hit_menu(layout, leaf->x + leaf->width / 2, leaf->y + leaf->height / 2), leaf->id);
  EXPECT_EQ(rect(layout, "common.select"), nullptr);
  EXPECT_EQ(rect(layout, "views.front"), nullptr);
  EXPECT_TRUE(hit_menu(layout, 0, 0).empty());
  for (const char *invalid : {"missing", "maya.common.select.all", "maya.common.file.new_scene"}) {
    snapshot.center_buttons[2] = invalid;
    const auto rejected = layout_menu(
        snapshot, 480, 320, 0, 0, {"center", invalid}, {}, measured(snapshot));
    EXPECT_FALSE(rejected.supported);
    EXPECT_TRUE(rejected.rects.empty());
  }
}

TEST(axismeld_hotbox_menu, TheSameMenuUsesAnExplicitTitleOrCentralAnchor)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[0] = "common.select";
  const auto widths = measured(snapshot);
  // The real Select catalog grows with modeling entries. Keep both lists away from
  // vertical clamping, which would erase the title/center anchor difference.
  const auto title = layout_menu(snapshot, 1920, 2160, 960, 1080, {"common.select"}, {}, widths);
  const auto central = layout_menu(
      snapshot, 1920, 2160, 960, 1080, {"center", "common.select"}, {}, widths);
  ASSERT_TRUE(title.supported);
  ASSERT_TRUE(central.supported);
  const auto *title_anchor = rect(title, "common.select"), *center_anchor = rect(central, "views");
  const auto *title_first = rect(title, "maya.common.select.all"),
             *center_first = rect(central, "maya.common.select.all");
  ASSERT_NE(title_anchor, nullptr);
  ASSERT_NE(center_anchor, nullptr);
  ASSERT_NE(title_first, nullptr);
  ASSERT_NE(center_first, nullptr);
  EXPECT_FLOAT_EQ(title_first->y + title_first->height, title_anchor->y + title_anchor->height);
  EXPECT_FLOAT_EQ(center_first->y + center_first->height, center_anchor->y + center_anchor->height);
  const auto *a = rect(title, "maya.common.select.all"), *b = rect(central, "maya.common.select.all");
  ASSERT_NE(a, nullptr);
  ASSERT_NE(b, nullptr);
  EXPECT_NE(a->y, b->y);
  EXPECT_TRUE(a->native_menu);
  EXPECT_TRUE(b->native_menu);
  EXPECT_EQ(rect(title, "@back:common.select"), nullptr);
  EXPECT_EQ(rect(central, "@back:common.select"), nullptr);
  EXPECT_NE(rect(title, "views"), nullptr);
  EXPECT_NE(rect(central, "views"), nullptr);
}

TEST(axismeld_hotbox_menu, CenterRootMappingIsNotMistakenForAPathCycle)
{
  auto snapshot = default_snapshot();
  snapshot.style = "center";
  snapshot.center_buttons[1] = "center";
  const auto layout = layout_menu(snapshot,
                                  1920,
                                  1080,
                                  960,
                                  540,
                                  {"center", "center", "center.controls"},
                                  {},
                                  measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *style = rect(layout, "center.controls.style");
  ASSERT_NE(style, nullptr);
  EXPECT_EQ(style->depth, 2);
  EXPECT_EQ(hit_menu(layout, style->x + style->width / 2, style->y + style->height / 2),
            style->id);
}
TEST(axismeld_hotbox_menu, UnopenedLongLabelsCannotDisableViewsOrTools)
{
  auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  widths["common.file"] = 2000.0f;  // A visible impossible title must still fail atomically.
  auto visible = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  EXPECT_FALSE(visible.supported);
  widths = measured(snapshot);
  widths["center.controls.buttons.rightmouse.none"] = 2000.0f;
  const auto main = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  EXPECT_TRUE(main.supported);
  const auto tools = layout_menu(snapshot, 1920, 1080, 960, 540,
                                {"tools.move"}, {}, widths, nullptr, "tools.move");
  EXPECT_TRUE(tools.supported);
}

TEST(axismeld_hotbox_menu, LongNativeListsExposeAllSixtyRowsInCompleteColumns)
{
  auto snapshot = default_snapshot();
  MenuNode owner{"fixture.long", "Long list", "", "", "", MenuKind::Menu, true, {}};
  for (int i = 0; i < 60; i++) {
    owner.children.push_back({"fixture.item" + std::to_string(i), "Action", "selection.clear",
                              "", "", MenuKind::Command, true, {}});
  }
  snapshot.menus.push_back(owner);
  expect_complete_native(snapshot, owner.id, 960, 540, 480, 270);
}


TEST(axismeld_hotbox_menu, RectHitPreservesVisibleOccurrenceAndDisabledOcclusion)
{
  MenuLayout layout{{{"views", 0, 0, 100, 28, 0},
                     {"views", 50, 0, 100, 28, 1},
                     {"disabled", 80, 0, 10, 28, 2, false},
                     {"last", 120, 0, 20, 28, 1}},
                    true};
  EXPECT_EQ(hit_menu_rect(layout, 20, 10), &layout.rects[0]);
  EXPECT_EQ(hit_menu_rect(layout, 60, 10), &layout.rects[1]);
  EXPECT_EQ(hit_menu_rect(layout, 85, 10), &layout.rects[2]);
  EXPECT_EQ(hit_menu(layout, 85, 10), "");
  EXPECT_EQ(hit_menu_rect(layout, 130, 10), &layout.rects[3]);
  EXPECT_EQ(hit_menu_rect(layout, -1, 10), nullptr);
  layout.supported = false;
  EXPECT_EQ(hit_menu_rect(layout, 60, 10), nullptr);
}
TEST(axismeld_hotbox_menu, FullMenusShowEveryDisplayRowWithoutNavigation)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 300,
                                  {"common.display"}, {{"common.display", 20}}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const MenuNode *owner = nullptr;
  visit(snapshot.menus, [&](const MenuNode &node) { if (node.id == "common.display") { owner = &node; } });
  ASSERT_NE(owner, nullptr);
  for (const auto &node : owner->children) {
    EXPECT_NE(rect(layout, node.id), nullptr) << node.id;
  }
  for (const auto &item : layout.rects) {
    EXPECT_FALSE(item.id.starts_with("@scroll:") || item.id.starts_with("@back:")) << item.id;
  }
}

TEST(axismeld_hotbox_menu, FullCompanionBottomAlignmentPreservesEveryRow)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(snapshot, 1920, 1080, 960, 120,
                                  {"context.modeling_object"}, {}, measured(snapshot), nullptr,
                                  "context.modeling_object");
  ASSERT_TRUE(layout.supported);
  const MenuNode *owner = nullptr;
  visit(snapshot.menus, [&](const MenuNode &node) { if (node.id == "context.modeling_object_menu") { owner = &node; } });
  ASSERT_NE(owner, nullptr);
  float bottom = 1080;
  for (const auto &node : owner->children) {
    const auto *item = rect(layout, node.id);
    ASSERT_NE(item, nullptr) << node.id;
    bottom = std::min(bottom, item->y);
    EXPECT_FLOAT_EQ(item->height, node.kind == MenuKind::Separator && node.label.empty() ? 6 : 24);
  }
  float list_top = 0, ring_bottom = 1080;
  for (const auto &item : layout.rects) {
    if (item.companion) { list_top = std::max(list_top, item.y + item.height); }
    else if (item.direction_label || item.option_box) { ring_bottom = std::min(ring_bottom, item.y); }
  }
  EXPECT_FLOAT_EQ(ring_bottom - list_top, 12);
  ASSERT_FALSE(layout.return_regions.empty());
  const auto &center = layout.return_regions.back();
  EXPECT_EQ(menu_return_target(layout, center.x+center.width/2, center.y+center.height/2),
            "context.modeling_object");
  EXPECT_FLOAT_EQ(bottom, 12);
  for (const auto &item : layout.rects) {
    EXPECT_FALSE(item.id.starts_with("@scroll:") || item.id.starts_with("@back:")) << item.id;
  }
}

TEST(axismeld_hotbox_menu, NativeColumnGapsOccludeWithoutBlockingTheirRealRows)
{
  auto snapshot = overflow_snapshot(); snapshot.style = "center";
  snapshot.center_buttons[0] = "fixture.overflow";
  const auto layout = layout_menu(snapshot, 960, 540, 480, 270,
                                  {"center", "fixture.overflow"}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  ASSERT_GT(layout.native_columns.size(), 1);
  for (size_t index = 1; index < layout.native_columns.size(); index++) {
    const auto &left = layout.native_columns[index-1], &right = layout.native_columns[index];
    ASSERT_EQ(left.owner, right.owner);
    EXPECT_FLOAT_EQ(right.x-left.x-left.width, 4);
    const float x = left.x+left.width+2, y = std::max(left.y,right.y)+12;
    const auto *gap = hit_menu_rect(layout,x,y);
    ASSERT_NE(gap,nullptr);
    EXPECT_FALSE(gap->interactive);
    EXPECT_TRUE(hit_menu(layout,x,y).empty());
    EXPECT_EQ(nearest_marking_rect(layout,x,y),nullptr);
  }
}

TEST(axismeld_hotbox_menu, FullCompositionTranslationIncludesAllGeometryAndColumnBounds)
{
  const auto snapshot = default_snapshot(); const auto widths = measured(snapshot);
  const auto local = layout_menu(snapshot,960,540,480,90,{"context.modeling_object"},{},widths,
                                 nullptr,"context.modeling_object");
  const MenuBounds bounds{-180,55,780,595};
  const auto shifted = layout_menu_in_bounds(snapshot,bounds,300,145,{"context.modeling_object"},
                                             {},widths,nullptr,"context.modeling_object");
  ASSERT_TRUE(local.supported); ASSERT_TRUE(shifted.supported);
  const std::array<std::pair<const std::vector<MenuRect> *,const std::vector<MenuRect> *>,5> groups = {{
      {&local.rects,&shifted.rects},{&local.return_regions,&shifted.return_regions},
      {&local.marking_gaps,&shifted.marking_gaps},{&local.occlusion_regions,&shifted.occlusion_regions},
      {&local.native_columns,&shifted.native_columns}}};
  for (const auto &[before,after] : groups) {
    ASSERT_EQ(before->size(),after->size());
    for (size_t i=0;i<before->size();i++) {
      EXPECT_FLOAT_EQ((*after)[i].x,(*before)[i].x-180);
      EXPECT_FLOAT_EQ((*after)[i].y,(*before)[i].y+55);
      EXPECT_EQ((*after)[i].column,(*before)[i].column);
    }
  }
}

TEST(axismeld_hotbox_menu, FullMenusRejectImpossibleFixedWidthWithoutPartialGeometry)
{
  auto snapshot = default_snapshot(); snapshot.style = "center";
  snapshot.center_buttons[0] = "common.display";
  auto widths = measured(snapshot); widths["display.hide_selected"] = 2000;
  // Pick an actual immediate child rather than relying on an adapter-specific ID.
  for (const auto &node : snapshot.menus[0].children) {
    if (node.id == "common.display") { widths[node.children.front().id] = 2000; }
  }
  const auto layout = layout_menu(snapshot,960,540,480,270,{"center","common.display"},{},widths);
  EXPECT_FALSE(layout.supported);
  EXPECT_TRUE(layout.rects.empty()); EXPECT_TRUE(layout.return_regions.empty());
  EXPECT_TRUE(layout.marking_gaps.empty()); EXPECT_TRUE(layout.occlusion_regions.empty());
  EXPECT_TRUE(layout.native_columns.empty());
}

TEST(axismeld_hotbox_menu, CompactSevenViewsKeepTheirNarrowGeometryAndEmptyNorthEast)
{
  auto snapshot = default_snapshot();
  // Isolate the Views ring: complete primary menus now use the larger window
  // surface, but that must not weaken the established compact Views geometry.
  snapshot.style = "center";
  const auto layout = layout_menu(snapshot,392,210,196,105,{"center","views"},{},measured(snapshot));
  ASSERT_TRUE(layout.supported);
  int count = 0;
  for (const auto &item : layout.rects) {
    if (!item.direction_label) { continue; }
    count++;
    EXPECT_TRUE(item.compact_label);
    EXPECT_FLOAT_EQ(item.height,24);
    EXPECT_EQ(hit_menu(layout,item.x+item.width/2,item.y+12),item.id);
  }
  EXPECT_EQ(count,7);
  EXPECT_EQ(rect(layout,"views.camera"),nullptr);
  ASSERT_NE(rect(layout,"views.style"),nullptr);
  ASSERT_EQ(layout.marking_gaps.size(),1);
  const auto &empty = layout.marking_gaps.front();
  EXPECT_EQ(empty.id,"views.camera");
  EXPECT_FALSE(empty.interactive);
  const auto *direction = hit_marking_menu_rect(layout,"views",empty.x+empty.width/2,empty.y+12);
  ASSERT_NE(direction,nullptr);
  EXPECT_EQ(direction->id,"views.camera");
  EXPECT_TRUE(hit_menu(layout,empty.x+empty.width/2,empty.y+12).empty());
  const auto *west=rect(layout,"views.top"), *east=rect(layout,"views.side");
  const auto *sw=rect(layout,"views.back"), *se=rect(layout,"views.bottom");
  ASSERT_NE(west,nullptr); ASSERT_NE(east,nullptr); ASSERT_NE(sw,nullptr); ASSERT_NE(se,nullptr);
  EXPECT_FLOAT_EQ(east->x-west->x-west->width-(se->x-sw->x-sw->width),32);
}

TEST(axismeld_hotbox_menu, FullViewsStyleKeepsActualPressOriginClearAndEveryRowHittable)
{
  auto snapshot = default_snapshot(); snapshot.style="center";
  const auto widths=measured(snapshot);
  for (const auto size : {std::array<float,2>{392,210},{480,320},{960,540}}) {
    for (const auto point : {std::array<float,2>{size[0]/2,size[1]/2},{0,0},{size[0],size[1]}}) {
      SCOPED_TRACE(testing::Message()<<size[0]<<"x"<<size[1]<<" @ "<<point[0]<<","<<point[1]);
      const auto layout=layout_menu(snapshot,size[0],size[1],point[0],point[1],
                    {"center","views","views.style"},{},widths,&point);
      ASSERT_TRUE(layout.supported);
      const auto *entry=rect(layout,"views.style"); ASSERT_NE(entry,nullptr);
      EXPECT_EQ(hit_menu(layout,entry->x+entry->width/2,entry->y+12),entry->id);
      for (const std::string suffix : {".rows",".zones",".center"}) {
        const auto *row=rect(layout,"views.style"+suffix); ASSERT_NE(row,nullptr);
        const float dx=point[0]-std::clamp(point[0],row->x,row->x+row->width);
        const float dy=point[1]-std::clamp(point[1],row->y,row->y+row->height);
        EXPECT_GT(dx*dx+dy*dy,12*12);
        EXPECT_FLOAT_EQ(row->height,24);
        EXPECT_EQ(hit_menu(layout,row->x+row->width/2,row->y+12),row->id);
        EXPECT_TRUE(row->x>=entry->x+entry->width || row->x+row->width<=entry->x ||
                    row->y>=entry->y+entry->height || row->y+row->height<=entry->y);
      }
    }
  }
}

}  // namespace blender::axismeld::tests

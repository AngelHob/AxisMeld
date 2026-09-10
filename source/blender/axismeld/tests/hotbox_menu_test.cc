/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <map>
#include <set>

#include "AXM_hotbox_menu.hh"
#include "testing/testing.h"

namespace blender::axismeld::tests {
#include "hotbox_menu_fixture.hh"

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
  visit(snapshot.menus, [&](const MenuNode &node) {
    result[node.id] = node.id.starts_with("views.") && node.kind == MenuKind::Command ? 38.0f :
                                                                                        80.0f;
  });
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

TEST(axismeld_hotbox_menu, SecondaryCommandsOccupyAnEllipseInsteadOfAColumn)
{
  const auto snapshot = default_snapshot();
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
  EXPECT_EQ(children, 5);
  EXPECT_NE(rect(layout, "@back:common.select"), nullptr);
  EXPECT_GE(centers_x.size(), 3);
  EXPECT_GE(centers_y.size(), 3);
}

TEST(axismeld_hotbox_menu, CompactSecondaryHitTargetsDoNotInheritPrimaryPadding)
{
  const auto snapshot = default_snapshot();
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
        EXPECT_FLOAT_EQ(item.width, widths.at(item.id) + 16) << item.id;
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
  EXPECT_LE(style->y + style->height + 9.99f, front->y);
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

TEST(axismeld_hotbox_menu, ViewOverlayUsesFullLabelsAndDisabledNorthEastCamera)
{
  const auto snapshot = default_snapshot();
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  const std::array<float, 2> origin = {972, 544};
  const auto layout = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "views"}, {}, widths, &origin);
  ASSERT_TRUE(layout.supported);
  const auto *root = rect(layout, "views"), *camera = rect(layout, "views.camera");
  ASSERT_NE(root, nullptr);
  ASSERT_NE(camera, nullptr);
  EXPECT_FLOAT_EQ(root->x + root->width / 2, 960);
  EXPECT_FLOAT_EQ(root->y + root->height / 2, 540);
  EXPECT_GT(camera->x + camera->width / 2, origin[0]);
  EXPECT_GT(camera->y + camera->height / 2, origin[1]);
  EXPECT_FALSE(camera->interactive);
  EXPECT_TRUE(
      hit_menu(layout, camera->x + camera->width / 2, camera->y + camera->height / 2).empty());
  for (const auto &item : layout.rects) {
    EXPECT_FALSE(item.compact_label);
  }
  const auto *perspective = rect(layout, "views.perspective");
  ASSERT_NE(perspective, nullptr);
  EXPECT_FLOAT_EQ(perspective->width, widths.at("views.perspective") + 16);
}

TEST(axismeld_hotbox_menu, ActiveEllipseDoesNotExposeUnderlyingRootHitTargets)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(snapshot,
                                  1920,
                                  1080,
                                  960,
                                  540,
                                  {"center.controls", "center.controls.buttons"},
                                  {},
                                  measured(snapshot));
  ASSERT_TRUE(layout.supported);
  for (const auto &item : layout.rects) {
    if (item.depth == 0) {
      const auto *hit = hit_menu_rect(layout, item.x + item.width / 2, item.y + item.height / 2);
      EXPECT_TRUE(!hit || hit->depth == 2) << item.id;
    }
    else {
      EXPECT_EQ(item.depth, 2) << item.id;
    }
  }
  EXPECT_NE(rect(layout, "@back:center.controls.buttons"), nullptr);
}

TEST(axismeld_hotbox_menu, SevenViewsLieOnHorizontalEllipseWithTheOriginalDirections)
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
    EXPECT_NEAR(nx * nx + ny * ny, 1.0f, .001f);
    EXPECT_GT(nx * signs[0], 0);
    EXPECT_GT(ny * signs[1], 0);
    EXPECT_LT(std::abs(nx), .9f);  // Diagonals cannot remain at the old rectangular corners.
    EXPECT_LT(std::abs(ny), .9f);
    EXPECT_EQ(hit_menu(layout, item->x + item->width / 2, item->y + item->height / 2), id);
  }
}

TEST(axismeld_hotbox_menu, QuadAtTwoTimesScalePagesSecondaryWithoutShrinking)
{
  auto snapshot = default_snapshot();
  auto &owner = snapshot.menus[0].children[3];
  owner.children.clear();
  for (int i = 0; i < 18; i++) {
    owner.children.push_back({"roomy." + std::to_string(i),
                              "Roomy command",
                              "view.front",
                              "",
                              "",
                              MenuKind::Command,
                              i != 4,
                              {}});
  }
  auto widths = measured(snapshot);
  visit(snapshot.menus, [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
  snapshot.center_buttons[2] = "common.select";
  std::set<std::string> reached;
  for (int page = 0; page < 18; page++) {
    const auto layout = layout_menu(snapshot,
                                    392,
                                    210,
                                    196,
                                    105,
                                    {"center", "common.select"},
                                    {{"common.select", page}},
                                    widths);
    ASSERT_TRUE(layout.supported) << page;
    int visible_children = 0;
    for (const auto &item : layout.rects) {
      EXPECT_FLOAT_EQ(item.height, item.depth ? 24 : 38);
      EXPECT_GE(item.x, 0);
      EXPECT_GE(item.y, 0);
      EXPECT_LE(item.x + item.width, 392);
      EXPECT_LE(item.y + item.height, 210);
      if (item.id.starts_with("roomy.")) {
        visible_children++;
        const auto *hit = hit_menu_rect(layout, item.x + item.width / 2, item.y + item.height / 2);
        ASSERT_NE(hit, nullptr);
        EXPECT_EQ(hit->id, item.id);
        reached.insert(item.id);
        if (item.id == "roomy.4") {
          EXPECT_TRUE(hit_menu(layout, item.x + item.width / 2, item.y + item.height / 2).empty());
        }
      }
    }
    EXPECT_GT(visible_children, 0);
    EXPECT_LT(visible_children, 18);
    EXPECT_NE(rect(layout, "@scroll:common.select:next"), nullptr);
  }
  EXPECT_EQ(reached.size(), 18);
}

TEST(axismeld_hotbox_menu, QuadSevenViewsAndCompactRootGroupsRemainReachable)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto views = layout_menu(snapshot, 392, 210, 0, 0, {"center", "views"}, {}, widths);
  ASSERT_TRUE(views.supported);
  int count = 0;
  for (const auto &item : views.rects) {
    EXPECT_FLOAT_EQ(item.height, item.depth ? 24 : 38);
    EXPECT_GE(item.x, 0);
    EXPECT_GE(item.y, 0);
    EXPECT_LE(item.x + item.width, 392);
    EXPECT_LE(item.y + item.height, 210);
    if (item.direction_label) {
      count++;
      EXPECT_EQ(hit_menu(views, item.x + item.width / 2, item.y + item.height / 2), item.id);
    }
  }
  EXPECT_EQ(count, 7);
  EXPECT_EQ(rect(views, "views.style"), nullptr);
  EXPECT_EQ(rect(views, "@back:views"), nullptr);
  EXPECT_NE(rect(views, "views"), nullptr);
  std::set<std::string> groups;
  for (int page = 0; page < 4; page++) {
    const auto main = layout_menu(snapshot, 392, 210, 196, 105, {}, {{"@main", page}}, widths);
    ASSERT_TRUE(main.supported);
    EXPECT_NE(rect(main, "views"), nullptr);
    for (const auto &group : snapshot.menus) {
      if (const auto *item = rect(main, group.id)) {
        groups.insert(group.id);
        EXPECT_EQ(hit_menu(main, item->x + item->width / 2, item->y + item->height / 2), group.id);
      }
    }
  }
  EXPECT_EQ(groups, (std::set<std::string>{"common", "pane", "center", "modeling"}));
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
    const MenuLayout layout = layout_menu(snapshot, 480, 320, 240, 160, {}, {}, widths);
    EXPECT_FALSE(layout.supported);
    EXPECT_TRUE(layout.rects.empty());
  }
  EXPECT_FALSE(layout_menu(snapshot, NAN, 320, 240, 160, {}, {}, measured(snapshot)).supported);
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
  const MenuSnapshot snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  for (const auto size : {std::array<float, 2>{480, 320}, {1920, 1080}}) {
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
                         std::unordered_map<std::string, int>)>
          browse;
      browse = [&](const std::vector<MenuNode> &nodes,
                   const std::string &owner,
                   std::vector<std::string> path,
                   std::unordered_map<std::string, int> offsets) {
        for (int scroll = 0; scroll < int(nodes.size()); scroll++) {
          offsets[owner] = scroll;
          const auto layout = layout_menu(
              snapshot, size[0], size[1], point[0], point[1], path, offsets, widths);
          ASSERT_TRUE(layout.supported);
          for (const auto &item : layout.rects) {
            EXPECT_GE(item.x, 0);
            EXPECT_GE(item.y, 0);
            EXPECT_LE(item.x + item.width, size[0]);
            EXPECT_LE(item.y + item.height, size[1]);
          }
          for (const MenuNode &node : nodes) {
            const MenuRect *item = rect(layout, node.id);
            if (!item) {
              continue;
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
              browse(node.children, node.id, child_path, offsets);
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
        browse(row.children, row.id, {}, {});
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

TEST(axismeld_hotbox_menu, ScrollingChildrenKeepsRootAndRestoresTheParentPage)
{
  auto snapshot = default_snapshot();
  auto &children = snapshot.menus[1].children.back().children.front().children;
  for (int i = 0; i < 30; i++) {
    children.push_back({"long." + std::to_string(i),
                        "Action",
                        "view.front",
                        "",
                        "",
                        MenuKind::Command,
                        true,
                        {}});
  }
  const auto widths = measured(snapshot);
  const std::unordered_map<std::string, int> offsets{{"pane", 5}};
  const auto closed = layout_menu(snapshot, 480, 320, 240, 160, {}, offsets, widths);
  const auto opened = layout_menu(
      snapshot, 480, 320, 240, 160, {"pane.panels", "pane.panels.views"}, offsets, widths);
  auto scrolled_offsets = offsets;
  scrolled_offsets["pane.panels.views"] = 10;
  const auto scrolled = layout_menu(snapshot,
                                    480,
                                    320,
                                    240,
                                    160,
                                    {"pane.panels", "pane.panels.views"},
                                    scrolled_offsets,
                                    widths);
  for (const auto *layout : {&closed, &opened, &scrolled}) {
    ASSERT_TRUE(layout->supported);
  }
  const auto restored_main = layout_menu(
      snapshot, 480, 320, 240, 160, {}, scrolled_offsets, widths);
  ASSERT_TRUE(restored_main.supported);
  for (const char *id : {"pane.panels", "views"}) {
    const auto *a = rect(closed, id), *b = rect(restored_main, id);
    ASSERT_NE(a, nullptr);
    ASSERT_NE(b, nullptr);
    EXPECT_EQ(a->x, b->x);
    EXPECT_EQ(a->y, b->y);
    ASSERT_NE(rect(opened, id), nullptr);
    ASSERT_NE(rect(scrolled, id), nullptr);
    EXPECT_EQ(rect(opened, id)->depth, 0);
    EXPECT_EQ(rect(scrolled, id)->depth, 0);
  }
  const auto *a = rect(opened, "@back:pane.panels.views"),
             *b = rect(scrolled, "@back:pane.panels.views");
  ASSERT_NE(a, nullptr);
  ASSERT_NE(b, nullptr);
  EXPECT_EQ(a->x, b->x);
  EXPECT_EQ(a->y, b->y);
  EXPECT_NE(rect(opened, "pane.panels.perspective"), nullptr);
  EXPECT_EQ(rect(scrolled, "pane.panels.perspective"), nullptr);
  EXPECT_NE(rect(scrolled, "long.3"), nullptr);
  // Popping the active path restores the prior owner without losing either page offset.
  const auto parent = layout_menu(
      snapshot, 480, 320, 240, 160, {"pane.panels"}, scrolled_offsets, widths);
  ASSERT_TRUE(parent.supported);
  EXPECT_NE(rect(parent, "pane.panels.views"), nullptr);
  EXPECT_EQ(rect(parent, "long.3"), nullptr);
  EXPECT_NE(rect(parent, "@back:pane.panels"), nullptr);
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
  const auto &modeling = snapshot.menus.back().children;
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
}

TEST(axismeld_hotbox_menu, InwardRowsKeepCanonicalOrderAtTrueCorners)
{
  const auto snapshot = default_snapshot();
  for (const auto point : {std::array<float, 2>{0, 0}, {480, 0}, {0, 320}, {480, 320}}) {
    const auto layout = layout_menu(
        snapshot, 480, 320, point[0], point[1], {}, {}, measured(snapshot));
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
  for (const auto size : {std::array<float, 2>{480, 320}, {1920, 1080}}) {
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
  const auto *leaf = rect(layout, "common.select.vertex");
  ASSERT_NE(leaf, nullptr);
  EXPECT_EQ(hit_menu(layout, leaf->x + leaf->width / 2, leaf->y + leaf->height / 2), leaf->id);
  EXPECT_EQ(rect(layout, "common.select"), nullptr);
  EXPECT_EQ(rect(layout, "views.front"), nullptr);
  EXPECT_TRUE(hit_menu(layout, 0, 0).empty());
  for (const char *invalid : {"missing", "common.select.vertex", "common.file"}) {
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
  const auto title = layout_menu(snapshot, 1920, 1080, 960, 540, {"common.select"}, {}, widths);
  const auto central = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "common.select"}, {}, widths);
  ASSERT_TRUE(title.supported);
  ASSERT_TRUE(central.supported);
  const auto *a = rect(title, "common.select.vertex"), *b = rect(central, "common.select.vertex");
  ASSERT_NE(a, nullptr);
  ASSERT_NE(b, nullptr);
  EXPECT_NE(a->y, b->y);
  const auto *origin_a = rect(title, "@back:common.select"),
             *origin_b = rect(central, "@back:common.select");
  ASSERT_NE(origin_a, nullptr);
  ASSERT_NE(origin_b, nullptr);
  EXPECT_NE(origin_a->y, origin_b->y);
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
}  // namespace blender::axismeld::tests

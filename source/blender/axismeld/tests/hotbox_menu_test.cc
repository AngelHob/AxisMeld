/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
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
  // Fixed logical measurements, deliberately wide enough to exercise default-row overflow.
  visit(snapshot.menus, [&](const MenuNode &node) { result[node.id] = 160.0f; });
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

TEST(axismeld_hotbox_menu, SmallViewportRefusesMenus)
{
  MenuSnapshot snapshot{};
  EXPECT_FALSE(layout_menu(snapshot, 479, 320, 100, 100, {}, {}, {}).supported);
  EXPECT_FALSE(layout_menu(snapshot, 480, 319, 100, 100, {}, {}, {}).supported);
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
        visit(row.children,
              [&](const MenuNode &node) { EXPECT_TRUE(reached.count(node.id)) << node.id; });
      }
    }
  }
}

TEST(axismeld_hotbox_menu, ScrollingChildrenKeepsAncestorAndRootAnchors)
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
  scrolled_offsets["pane.panels.views"] = 3;
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
  for (const char *id : {"pane.panels", "views"}) {
    const auto *a = rect(closed, id), *b = rect(opened, id), *c = rect(scrolled, id);
    ASSERT_NE(a, nullptr);
    ASSERT_NE(b, nullptr);
    ASSERT_NE(c, nullptr);
    EXPECT_EQ(a->x, b->x);
    EXPECT_EQ(a->y, b->y);
    EXPECT_EQ(b->x, c->x);
    EXPECT_EQ(b->y, c->y);
  }
  const auto *a = rect(opened, "pane.panels.views"), *b = rect(scrolled, "pane.panels.views");
  ASSERT_NE(a, nullptr);
  ASSERT_NE(b, nullptr);
  EXPECT_EQ(a->x, b->x);
  EXPECT_EQ(a->y, b->y);
  EXPECT_NE(rect(opened, "pane.panels.perspective"), nullptr);
  EXPECT_EQ(rect(scrolled, "pane.panels.perspective"), nullptr);
  EXPECT_NE(rect(scrolled, "long.3"), nullptr);
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

TEST(axismeld_hotbox_menu, CenterOnlyCanOpenAGlobalMappedMenu)
{
  auto snapshot = default_snapshot();
  snapshot.style = "center";
  snapshot.center_buttons[2] = "common.select";
  const auto layout = layout_menu(
      snapshot, 480, 320, 0, 0, {"center", "common.select"}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  const auto *leaf = rect(layout, "common.select.vertex");
  ASSERT_NE(leaf, nullptr);
  EXPECT_EQ(hit_menu(layout, leaf->x + leaf->width / 2, leaf->y + leaf->height / 2), leaf->id);
  EXPECT_EQ(rect(layout, "common.select"), nullptr);
  EXPECT_EQ(rect(layout, "views.front"), nullptr);
  EXPECT_EQ(hit_menu(layout, 0, 0), "views");
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
  const auto *origin_a = rect(title, "views"), *origin_b = rect(central, "views");
  ASSERT_NE(origin_a, nullptr);
  ASSERT_NE(origin_b, nullptr);
  EXPECT_EQ(origin_a->x, origin_b->x);
  EXPECT_EQ(origin_a->y, origin_b->y);
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
}  // namespace blender::axismeld::tests

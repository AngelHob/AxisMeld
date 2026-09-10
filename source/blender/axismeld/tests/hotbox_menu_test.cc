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
        EXPECT_FLOAT_EQ(item.width, widths.at(item.id) + (item.native_menu ? 60 : 16)) << item.id;
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

TEST(axismeld_hotbox_menu, ControlsRowsUsesAContiguousNativeMenu)
{
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const auto root = layout_menu(snapshot, 1920, 1080, 960, 540, {}, {}, widths);
  const auto layout = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center.controls", "center.controls.rows"}, {}, widths);
  ASSERT_TRUE(root.supported);
  ASSERT_TRUE(layout.supported);
  const auto *entry = rect(layout, "center.controls.rows");
  ASSERT_NE(entry, nullptr);
  EXPECT_TRUE(entry->native_menu);
  EXPECT_FLOAT_EQ(entry->height, 24);
  EXPECT_FLOAT_EQ(entry->width, widths.at("center.controls.rows") + 60);
  const std::array<const char *, 3> ids = {
      "center.controls.rows.common", "center.controls.rows.pane", "center.controls.rows.modeling"};
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
  EXPECT_EQ(rect(layout, "@back:center.controls.rows"), nullptr);
  for (const MenuRect &original : root.rects) {
    const auto *preserved = rect(layout, original.id);
    ASSERT_NE(preserved, nullptr) << original.id;
    EXPECT_EQ(preserved->depth, 0) << original.id;
    EXPECT_FALSE(preserved->native_menu) << original.id;
  }
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
  const auto snapshot = default_snapshot();
  const auto widths = measured(snapshot);
  const std::array<const char *, 3> owners = {"center.controls.buttons.leftmouse",
                                              "center.controls.buttons.middlemouse",
                                              "center.controls.buttons.rightmouse"};
  const auto parent = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center.controls", "center.controls.buttons"}, {}, widths);
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
                                    {"center.controls", "center.controls.buttons", owner},
                                    {},
                                    widths);
    ASSERT_TRUE(layout.supported);
    const auto *entry = rect(layout, "center.controls.buttons");
    ASSERT_NE(entry, nullptr);
    EXPECT_TRUE(entry->native_menu);
    EXPECT_TRUE(entry->native_menu_standalone);
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
      EXPECT_FLOAT_EQ(item->width, 120);
      if (last) {
        EXPECT_FLOAT_EQ(item->x, last->x);
        EXPECT_FLOAT_EQ(item->width, last->width);
        EXPECT_FLOAT_EQ(last->y, item->y + 24);
      }
      last = item;
    }
  }
}

TEST(axismeld_hotbox_menu, NarrowMappingPagesReachAllChoicesWithBoundedNativeRows)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[2] = "center.controls";
  const std::array<const char *, 3> owners = {"center.controls.buttons.leftmouse",
                                              "center.controls.buttons.middlemouse",
                                              "center.controls.buttons.rightmouse"};
  for (const bool label_widths : {false, true}) {
    auto widths = measured(snapshot);
    if (label_widths) {
      visit(snapshot.menus,
            [&](const MenuNode &node) { widths[node.id] = node.label.size() * 7.0f; });
    }
    for (const auto size : {std::array<float, 2>{392, 212.5f}, {480, 320}}) {
      const std::array<std::array<float, 2>, 5> points = {
          {{size[0] / 2, size[1] / 2}, {0, 0}, {size[0], 0}, {0, size[1]}, {size[0], size[1]}}};
      for (const auto point : points) {
        for (const char *owner : owners) {
          SCOPED_TRACE(testing::Message()
                       << (label_widths ? "labels" : "independent") << " " << size[0] << "x"
                       << size[1] << " @ " << point[0] << "," << point[1] << " " << owner);
          std::set<std::string> reached;
          std::vector<std::string> first_page;
          std::vector<std::string> second_page;
          for (int offset = 0; offset < 13; offset++) {
            const auto layout = layout_menu(
                snapshot,
                size[0],
                size[1],
                point[0],
                point[1],
                {"center", "center.controls", "center.controls.buttons", owner},
                {{owner, offset}},
                widths);
            ASSERT_TRUE(layout.supported) << "offset=" << offset;
            for (const MenuRect &item : layout.rects) {
              if (item.depth == 0) {
                continue;
              }
              EXPECT_GE(item.x, 12) << item.id;
              EXPECT_GE(item.y, 12) << item.id;
              EXPECT_LE(item.x + item.width, size[0] - 12) << item.id;
              EXPECT_LE(item.y + item.height, size[1] - 12) << item.id;
            }
            const auto *entry = rect(layout, owner);
            ASSERT_NE(entry, nullptr);
            const auto *previous = rect(layout, std::string("@scroll:") + owner + ":previous");
            const auto *next = rect(layout, std::string("@scroll:") + owner + ":next");
            ASSERT_NE(previous, nullptr);
            ASSERT_NE(next, nullptr);
            EXPECT_FALSE(previous->interactive && offset == 0);
            EXPECT_FALSE(next->interactive && offset == 12);

            std::vector<const MenuRect *> column{previous};
            std::vector<std::string> visible;
            for (const char *suffix : mapping_suffixes) {
              const std::string id = std::string(owner) + "." + suffix;
              if (const MenuRect *item = rect(layout, id)) {
                reached.insert(id);
                visible.push_back(id);
                column.push_back(item);
              }
            }
            column.push_back(next);
            ASSERT_FALSE(visible.empty());
            if (offset == 0) {
              first_page = visible;
            }
            if (offset == 1) {
              second_page = visible;
            }
            for (int i = 0; i < int(column.size()); i++) {
              const MenuRect *item = column[i];
              EXPECT_TRUE(item->native_menu) << item->id;
              EXPECT_FALSE(item->native_menu_standalone) << item->id;
              EXPECT_FLOAT_EQ(item->height, 24) << item->id;
              EXPECT_GE(item->x, 12) << item->id;
              EXPECT_GE(item->y, 12) << item->id;
              EXPECT_LE(item->x + item->width, size[0] - 12) << item->id;
              EXPECT_LE(item->y + item->height, size[1] - 12) << item->id;
              EXPECT_TRUE(separated_by(*entry, *item, 9.99f)) << item->id;
              if (i > 0) {
                EXPECT_FLOAT_EQ(item->x, column[0]->x) << item->id;
                EXPECT_FLOAT_EQ(item->width, column[0]->width) << item->id;
                EXPECT_FLOAT_EQ(column[i - 1]->y, item->y + 24) << item->id;
              }
            }
          }
          EXPECT_EQ(reached.size(), 13);
          ASSERT_FALSE(first_page.empty());
          ASSERT_EQ(second_page.size(), first_page.size());
          EXPECT_EQ(first_page.front(), std::string(owner) + ".none");
          EXPECT_EQ(second_page.front(), std::string(owner) + ".views");
        }
      }
    }
  }
}

TEST(axismeld_hotbox_menu, MappingOffsetsClampAndAncestorOffsetsDoNotHideTheOpenOwner)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[2] = "center.controls";
  const auto widths = measured(snapshot);
  const std::string owner = "center.controls.buttons.rightmouse";
  const std::vector<std::string> path = {
      "center", "center.controls", "center.controls.buttons", owner};
  const auto first = layout_menu(snapshot, 392, 212.5f, 196, 106.25f, path, {{owner, -9}}, widths);
  const auto last = layout_menu(snapshot, 392, 212.5f, 196, 106.25f, path, {{owner, 99}}, widths);
  const auto ancestor = layout_menu(snapshot,
                                    392,
                                    212.5f,
                                    196,
                                    106.25f,
                                    path,
                                    {{"center.controls.buttons", 99}, {owner, 6}},
                                    widths);
  ASSERT_TRUE(first.supported);
  ASSERT_TRUE(last.supported);
  ASSERT_TRUE(ancestor.supported);
  const auto *first_previous = rect(first, "@scroll:" + owner + ":previous");
  const auto *last_next = rect(last, "@scroll:" + owner + ":next");
  ASSERT_NE(first_previous, nullptr);
  ASSERT_NE(last_next, nullptr);
  EXPECT_FALSE(first_previous->interactive);
  EXPECT_FALSE(last_next->interactive);
  EXPECT_NE(rect(first, owner + ".none"), nullptr);
  EXPECT_NE(rect(last, owner + ".modeling"), nullptr);
  EXPECT_NE(rect(ancestor, owner), nullptr);
  EXPECT_NE(rect(ancestor, owner + ".common_modify"), nullptr);
}

TEST(axismeld_hotbox_menu, ShortNativeSettingsListsFitNarrowViewportCornersWithoutDroppingRows)
{
  auto snapshot = default_snapshot();
  snapshot.center_buttons[2] = "center.controls";
  const auto widths = measured(snapshot);
  const std::array<std::pair<const char *, std::vector<const char *>>, 2> lists = {{
      {"center.controls.rows",
       {"center.controls.rows.common",
        "center.controls.rows.pane",
        "center.controls.rows.modeling"}},
      {"center.controls.transparency",
       {"center.controls.transparency.0",
        "center.controls.transparency.25",
        "center.controls.transparency.50",
        "center.controls.transparency.75",
        "center.controls.transparency.100"}},
  }};
  for (const auto &[owner, ids] : lists) {
    for (const auto point : {std::array<float, 2>{0, 0}, {392, 0}, {0, 210}, {392, 210}}) {
      SCOPED_TRACE(testing::Message() << owner << " @ " << point[0] << "," << point[1]);
      const auto layout = layout_menu(snapshot,
                                      392,
                                      210,
                                      point[0],
                                      point[1],
                                      {"center", "center.controls", owner},
                                      {},
                                      widths);
      ASSERT_TRUE(layout.supported);
      const auto *entry = rect(layout, owner);
      ASSERT_NE(entry, nullptr);
      EXPECT_TRUE(entry->native_menu);
      EXPECT_FLOAT_EQ(entry->height, 24);
      EXPECT_FLOAT_EQ(entry->width, widths.at(owner) + 60);
      const auto *first = rect(layout, ids.front());
      ASSERT_NE(first, nullptr);
      const MenuRect *previous = nullptr;
      for (const char *id : ids) {
        const auto *item = rect(layout, id);
        ASSERT_NE(item, nullptr) << id;
        EXPECT_TRUE(item->native_menu);
        EXPECT_FLOAT_EQ(item->height, 24);
        EXPECT_GE(item->x, 12);
        EXPECT_GE(item->y, 12);
        EXPECT_LE(item->x + item->width, 380);
        EXPECT_LE(item->y + item->height, 198);
        EXPECT_FLOAT_EQ(item->x, first->x);
        if (previous) {
          EXPECT_FLOAT_EQ(previous->y, item->y + 24);
        }
        EXPECT_TRUE(item->x >= entry->x + entry->width + 9.99f ||
                    entry->x >= item->x + item->width + 9.99f ||
                    item->y >= entry->y + entry->height + 9.99f ||
                    entry->y >= item->y + item->height + 9.99f);
        previous = item;
      }
    }
  }
}

TEST(axismeld_hotbox_menu, NarrowStylePopupDoesNotCoverItsEntry)
{
  const auto snapshot = default_snapshot();
  for (const float width : {392.0f, 340.0f}) {
    for (const float offset : {0.0f, 30.0f}) {
      const std::array<float, 2> origin{width / 2 + offset, 105};
      const auto layout = layout_menu(snapshot,
                                      width,
                                      210,
                                      width / 2,
                                      105,
                                      {"center", "views", "views.style"},
                                      {},
                                      measured(snapshot),
                                      offset == 0 ? nullptr : &origin);
      ASSERT_TRUE(layout.supported);
      const auto *entry = rect(layout, "views.style");
      ASSERT_NE(entry, nullptr);
      EXPECT_EQ(hit_menu(layout, entry->x + entry->width / 2, entry->y + 12), entry->id);
      for (const char *suffix : {".rows", ".zones", ".center"}) {
        const auto *item = rect(layout, std::string("views.style") + suffix);
        ASSERT_NE(item, nullptr);
        EXPECT_GE(item->x, 12);
        EXPECT_LE(item->x + item->width, width - 12);
        EXPECT_GE(item->y, 12);
        EXPECT_LE(item->y + item->height, 198);
        const float dx = origin[0] - std::clamp(origin[0], item->x, item->x + item->width);
        const float dy = 105 - std::clamp(105.0f, item->y, item->y + item->height);
        EXPECT_GT(dx * dx + dy * dy, 12 * 12) << "Style must not cover the marking return zone";
        EXPECT_TRUE(item->x >= entry->x + entry->width + 9.99f ||
                    entry->x >= item->x + item->width + 9.99f ||
                    item->y >= entry->y + entry->height + 9.99f ||
                    entry->y >= item->y + item->height + 9.99f);
        EXPECT_EQ(hit_menu(layout, item->x + item->width / 2, item->y + 12), item->id);
      }
    }
  }
}

TEST(axismeld_hotbox_menu, TighterViewRingExposesNearerTargetsWithoutOverlap)
{
  const auto snapshot = default_snapshot();
  const auto layout = layout_menu(
      snapshot, 1920, 1080, 960, 540, {"center", "views"}, {}, measured(snapshot));
  ASSERT_TRUE(layout.supported);
  // A shorter horizontal reach must acquire the now-visible Right View button,
  // not remain in the old ring's empty corridor.
  EXPECT_EQ(hit_menu(layout, 1050, 540), "views.side");
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

TEST(axismeld_hotbox_menu, ActiveNativeListDoesNotExposeUnderlyingRootHitTargets)
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
      EXPECT_TRUE(!hit || hit->depth > 0) << item.id;
    }
    else {
      EXPECT_TRUE(item.depth == 1 || item.depth == 2) << item.id;
    }
  }
  EXPECT_EQ(rect(layout, "@back:center.controls.buttons"), nullptr);
  const auto *entry = rect(layout, "center.controls.buttons");
  const auto *button = rect(layout, "center.controls.buttons.leftmouse");
  ASSERT_NE(entry, nullptr);
  ASSERT_NE(button, nullptr);
  EXPECT_TRUE(entry->native_menu_standalone);
  EXPECT_FALSE(button->native_menu_standalone);
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
      EXPECT_EQ(hit_menu(views, item.x + item.width / 2, item.y + item.height / 2),
                item.interactive ? item.id : "");
    }
  }
  EXPECT_EQ(count, 8);  // The tighter ring now fits the complete overlay in this fixture.
  EXPECT_NE(rect(views, "views.style"), nullptr);
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

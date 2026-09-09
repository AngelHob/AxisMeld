/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_hotbox_menu.hh"
#include "testing/testing.h"

namespace blender::axismeld {
bool parse_menu_snapshot(std::string_view json, MenuSnapshot &out, std::string &error);

static std::string menu(const std::string &id, const std::string &children = "")
{
  return "{\"id\":\"" + id +
         "\",\"kind\":\"menu\",\"label\":\"Menu\",\"command\":\"\",\"enabled\":true,"
         "\"reason\":\"\",\"children\":[" +
         children + "]}";
}

static std::string snapshot(const std::string &child = "")
{
  return R"({"schema_version":1,"generation":7,"settings":{"style":"rows","transparency":25,"rows":["common","pane","modeling"],"center_buttons":{"LEFTMOUSE":null,"MIDDLEMOUSE":"views","RIGHTMOUSE":"views"}},"menus":[)" +
         menu("common", child) + "," + menu("pane") + "," + menu("center", menu("views")) + "," +
         menu("modeling") + "]}";
}

static std::string replace(std::string input, const std::string &from, const std::string &to)
{
  const size_t index = input.find(from);
  EXPECT_NE(index, std::string::npos);
  input.replace(index, from.size(), to);
  return input;
}

TEST(hotbox_model, ValidSnapshotOwnsDataAndNormalizesNull)
{
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(snapshot(), out, error));
  EXPECT_EQ(out.generation, 7);
  EXPECT_EQ(out.transparency, 25);
  ASSERT_EQ(out.menus.size(), 4);
  EXPECT_EQ(out.menus[2].children[0].id, "views");
  EXPECT_TRUE(out.center_buttons[0].empty());
  EXPECT_EQ(out.center_buttons[2], "views");
}

TEST(hotbox_model, BoundaryValidationCannotPartiallyReplaceSnapshot)
{
  const std::string valid = snapshot();
  const std::vector<std::string> invalid = {
      replace(valid, "\"schema_version\":1", "\"schema_version\":true"),
      replace(valid, "\"generation\":7", "\"generation\":0"),
      replace(valid, "\"generation\":7", "\"generation\":7.0"),
      replace(valid, "\"transparency\":25", "\"transparency\":false"),
      replace(valid, "\"transparency\":25", "\"transparency\":26"),
      replace(valid, "\"style\":\"rows\"", "\"style\":\"unknown\""),
      replace(valid, "\"LEFTMOUSE\":null", "\"LEFTMOUSE\":\"missing\""),
      replace(valid, "\"LEFTMOUSE\":null", "\"LEFTMOUSE\":7"),
      replace(
          valid, "\"rows\":[\"common\",\"pane\",\"modeling\"]", "\"rows\":[\"pane\",\"common\"]"),
      replace(valid, "\"id\":\"pane\"", "\"id\":\"common\""),
      replace(valid, "\"id\":\"pane\"", "\"id\":\"@scroll:pane:next\""),
      replace(valid, "\"kind\":\"menu\"", "\"kind\":\"group\""),
      replace(valid, "\"enabled\":true", "\"enabled\":1"),
      replace(valid, "\"label\":\"Menu\"", "\"label\":\"" + std::string(129, 'x') + "\""),
      replace(valid, "\"generation\":7", "\"generation\":7,\"script\":\"foo\""),
      replace(valid, "\"enabled\":true", "\"enabled\":true,\"close_before\":false"),
      snapshot(
          R"({"id":"bad","kind":"command","label":"Bad","command":"wm.open_mainfile","enabled":true,"reason":"","children":[]})"),
      snapshot(
          R"({"id":"bad","kind":"command","label":"Bad","command":"view.front","enabled":true,"reason":"","value":"bad","children":[]})"),
      snapshot(
          R"({"id":"bad","kind":"setting","label":"Bad","command":"style","enabled":true,"reason":"","value":"bad","children":[]})"),
      snapshot(
          R"({"id":"bad","kind":"disabled","label":"Bad","command":"","enabled":false,"reason":"","children":[]})")};
  for (const auto &json : invalid) {
    MenuSnapshot out{};
    out.generation = 99;
    out.style = "untouched";
    std::string error;
    EXPECT_FALSE(parse_menu_snapshot(json, out, error)) << json;
    EXPECT_EQ(out.generation, 99);
    EXPECT_EQ(out.style, "untouched");
  }
}

TEST(hotbox_model, NodeCountAndDepthAreBounded)
{
  std::string children;
  for (int i = 0; i < 252; i++) {
    if (i)
      children += ",";
    children += menu("child" + std::to_string(i));
  }
  MenuSnapshot out{};
  std::string error;
  EXPECT_FALSE(parse_menu_snapshot(snapshot(children), out, error));
  children.clear();
  for (int i = 0; i < 8; i++)
    children = menu("depth" + std::to_string(i), children);
  EXPECT_FALSE(parse_menu_snapshot(snapshot(children), out, error));
  EXPECT_FALSE(parse_menu_snapshot(std::string(10000, '['), out, error));
}

TEST(hotbox_model, InvalidInputIsAtomic)
{
  for (const std::string input : {std::string("{"),
                                  std::string("null"),
                                  std::string(256 * 1024 + 1, ' '),
                                  std::string(R"({"schema_version":true})")})
  {
    MenuSnapshot out{};
    out.generation = 77;
    out.style = "sentinel";
    std::string error;
    EXPECT_FALSE(parse_menu_snapshot(input, out, error));
    EXPECT_EQ(out.generation, 77);
    EXPECT_EQ(out.style, "sentinel");
    EXPECT_FALSE(error.empty());
  }
}
}  // namespace blender::axismeld

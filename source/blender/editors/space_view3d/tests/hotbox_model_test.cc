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

TEST(hotbox_model, IndependentOptionLeafHasOneExactParentAndNoGrandchildren)
{
  const std::string option = R"({"id":"action.options","kind":"command","label":"Options","command":"mesh.quad_remesh","enabled":true,"reason":"","children":[]})";
  const std::string row = R"({"id":"action","kind":"disabled","label":"Action","command":"","enabled":false,"reason":"Unavailable","children":[)" + option + "]}";
  MenuSnapshot out{};
  std::string error;
  ASSERT_TRUE(parse_menu_snapshot(snapshot(row), out, error)) << error;
  EXPECT_TRUE(out.menus[0].children[0].children[0].enabled);
  for (const std::string &bad : {replace(row, "action.options", "other.options"),
                                 replace(row, option, option + "," + option),
                                 replace(row, "\"label\":\"Options\"", "\"label\":\"Options\",\"direction\":\"E\""),
                                 replace(row, option, menu("action.options")),
                                 replace(row, "\"kind\":\"disabled\"", "\"kind\":\"separator\""),
                                 replace(row, "\"children\":[]", "\"children\":[" + replace(option, "action.options", "action.options.options") + "]")}) {
    out.generation = 99;
    EXPECT_FALSE(parse_menu_snapshot(snapshot(bad), out, error));
    EXPECT_EQ(out.generation, 99);
  }
}

TEST(hotbox_model, ObjectCompanionIsTheOnlyOptionalFifthRootAndActionAdmissionIsExact)
{
  const std::string companion = replace(menu("context.modeling_object_menu"),
                                        "\"kind\":\"menu\"", "\"kind\":\"menu\",\"presentation\":\"list\"");
  const auto fifth = [&](const std::string &root) {
    auto json = snapshot();
    json.insert(json.size() - 2, "," + root);
    return json;
  };
  MenuSnapshot out{};
  std::string error;
  ASSERT_TRUE(parse_menu_snapshot(fifth(companion), out, error)) << error;
  EXPECT_EQ(out.menus.size(), 5);
  EXPECT_FALSE(parse_menu_snapshot(fifth(replace(companion, "context.modeling_object_menu", "context.any_menu")), out, error));
  EXPECT_FALSE(parse_menu_snapshot(fifth(replace(companion, "\"list\"", "\"radial\"")), out, error));
  const auto action = [](const std::string &command) {
    return R"({"id":"action","kind":"command","label":"Action","command":")" + command +
           R"(","enabled":true,"reason":"","children":[]})";
  };
  for (const auto command : {"object.modeling_smooth", "object.modeling_smooth_options",
                             "object.modeling_mirror", "object.modeling_mirror_options",
                             "object.modeling_reduce", "object.modeling_reduce_options",
                             "object.modeling_remesh", "object.modeling_remesh_options",
                             "tool.object_mesh_offset_loop"}) {
    EXPECT_TRUE(parse_menu_snapshot(snapshot(action(command)), out, error)) << command << error;
  }
  for (const auto command : {"object.modeling_eval", "object.modeling_smooth.extra", "object.modeling_smooth_options_extra"}) {
    EXPECT_FALSE(parse_menu_snapshot(snapshot(action(command)), out, error)) << command;
  }
}

TEST(hotbox_model, ExpandedToolTreeRetainsBoundedAtomicParsing)
{
  MenuSnapshot out{};
  std::string error, children;
  for (int i = 0; i < 800; i++) {
    children += (i ? "," : "") + menu("entry" + std::to_string(i));
  }
  ASSERT_TRUE(parse_menu_snapshot(snapshot(children), out, error));
  for (int i = 800; i < 2049; i++) {
    children += "," + menu("entry" + std::to_string(i));
  }
  EXPECT_FALSE(parse_menu_snapshot(snapshot(children), out, error));
  EXPECT_EQ(out.generation, 7);
  EXPECT_EQ(out.menus.front().children.size(), 800);
}

TEST(hotbox_model, ModelingCommandsAndReadOnlyIndicatorsRemainExplicit)
{
  const char *registered[] = {
#include "../view3d_axismeld_modeling_commands.inc"
  };
  MenuSnapshot out{};
  std::string error;
  const auto leaf = [](const std::string &command) {
    return R"({"id":"action","kind":"command","label":"Action","enabled":true,"reason":"","children":[],"command":")" +
           command + R"(","indicator":"radio","checked":false})";
  };
  for (const auto *command : registered) {
    ASSERT_TRUE(parse_menu_snapshot(snapshot(leaf(command)), out, error)) << command << error;
    EXPECT_EQ(menu_radio_state(out, out.menus[0].children[0]), MenuRadioState::Unselected);
  }
  const std::string valid = leaf(registered[0]);
  for (const auto &bad : {leaf("modeling.execute_arbitrary"),
                          replace(valid, "\"checked\":false", "\"checked\":0"),
                          replace(valid, "\"radio\"", "\"operator_path\""),
                          replace(valid, "\"command\",\"label\"", "\"menu\",\"label\"")})
  {
    out.generation = 99;
    EXPECT_FALSE(parse_menu_snapshot(snapshot(bad), out, error));
    EXPECT_EQ(out.generation, 99);
  }
  ASSERT_TRUE(parse_menu_snapshot(snapshot(replace(valid, "\"checked\":false", "\"checked\":true")), out, error));
  EXPECT_EQ(menu_radio_state(out, out.menus[0].children[0]), MenuRadioState::Selected);
}

TEST(hotbox_model, ObjectToolCatalogLeavesAreExplicitAndUnknownToolsAreRejectedAtomically)
{
  MenuSnapshot out{};
  std::string error;
  const auto leaf = [](const std::string &command, const std::string &direction) {
    return "{\"id\":\"" + command +
           "\",\"kind\":\"command\",\"label\":\"Object Tool\",\"command\":\"" + command +
           "\",\"enabled\":true,\"reason\":\"\",\"children\":[],\"direction\":\"" + direction + "\"}";
  };
  const auto root = [](const std::string &children) {
    return replace(menu("context.modeling_object", children),
                   "\"kind\":\"menu\"", "\"kind\":\"menu\",\"presentation\":\"radial\"");
  };
  // Independent catalog spellings: do not let a shared misspelled allowlist define the test.
  const std::string children = leaf("tool.object_mesh_poly_build", "E") + "," +
                               leaf("tool.object_mesh_loopcut", "SW") + "," +
                               leaf("tool.object_mesh_knife", "W");
  ASSERT_TRUE(parse_menu_snapshot(snapshot(root(children)), out, error)) << error;
  ASSERT_EQ(out.menus[0].children[0].children.size(), 3);
  for (const auto command : {"tool.object_mesh_poly_build", "tool.object_mesh_loopcut",
                             "tool.object_mesh_knife"}) {
    EXPECT_TRUE(parse_menu_snapshot(snapshot(root(leaf(command, "W"))), out, error))
        << command << ": " << error;
  }
  for (const auto command : {"tool.object_mesh_loop_cut", "tool.object_mesh_knife.extra",
                             "tool.object_mesh_eval", "object_modeling.execute_arbitrary"}) {
    out.generation = 99;
    EXPECT_FALSE(parse_menu_snapshot(snapshot(root(leaf(command, "W"))), out, error)) << command;
    EXPECT_EQ(out.generation, 99);
  }
}

TEST(hotbox_model, CreationCommandsAreExplicitAndUnknownGeometryIsRejected)
{
  MenuSnapshot out{};
  std::string error;
  const auto command_node = [](const std::string &command) {
    return "{\"id\":\"create\",\"kind\":\"command\",\"label\":\"Create\",\"command\":\"" +
           command + "\",\"enabled\":true,\"reason\":\"\",\"children\":[]}";
  };
  for (const std::string name : {"disc", "sphere", "torus", "cube", "cone", "cylinder", "plane"}) {
    EXPECT_TRUE(parse_menu_snapshot(snapshot(command_node("mesh.create_" + name)), out, error))
        << name << ": " << error;
  }
  for (const std::string name : {"unknown", "extrude", "eval"}) {
    EXPECT_FALSE(parse_menu_snapshot(snapshot(command_node("mesh.create_" + name)), out, error));
  }
}

TEST(hotbox_model, DirectionMetadataIsOptionalStrictAndAtomic)
{
  const std::string child = replace(
      menu("north"), "\"kind\":\"menu\"", "\"direction\":\"N\",\"kind\":\"menu\"");
  const std::string radial = replace(
      menu("ring", child), "\"id\":\"ring\"", "\"id\":\"ring\",\"presentation\":\"radial\"");
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(snapshot(radial), out, error));
  for (const auto &bad : {replace(radial, "\"N\"", "\"UP\""),
                          replace(radial, "\"radial\"", "\"list\""),
                          replace(radial, "\"N\"", "true"),
                          replace(radial, "\"radial\"", "false")})
  {
    out.generation = 99;
    EXPECT_FALSE(parse_menu_snapshot(snapshot(bad), out, error));
    EXPECT_EQ(out.generation, 99);
  }
}

TEST(hotbox_model, RadialChildRequiresDirectionAtomically)
{
  const std::string radial = replace(menu("ring", menu("north")),
                                     "\"id\":\"ring\"",
                                     "\"id\":\"ring\",\"presentation\":\"radial\"");
  MenuSnapshot out{};
  out.generation = 99;
  std::string error;
  EXPECT_FALSE(parse_menu_snapshot(snapshot(radial), out, error));
  EXPECT_EQ(out.generation, 99);
}

TEST(hotbox_model, ValidSnapshotOwnsDataAndNormalizesNull)
{
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(snapshot(), out, error));
  EXPECT_EQ(out.generation, 7);
  EXPECT_EQ(out.transparency, 25);
  EXPECT_EQ(out.appearance.brightness, -13);
  EXPECT_TRUE(out.appearance.theme_background);
  ASSERT_EQ(out.menus.size(), 4);
  EXPECT_EQ(out.menus[2].children[0].id, "views");
  EXPECT_TRUE(out.center_buttons[0].empty());
  EXPECT_EQ(out.center_buttons[2], "views");
}

TEST(hotbox_model, OptionalAppearanceAcceptsValidColorsAndRejectsMalformedValuesAtomically)
{
  const auto with_appearance = [](const std::string &appearance) {
    return replace(
        snapshot(), "\"style\":\"rows\"", "\"appearance\":" + appearance + ",\"style\":\"rows\"");
  };
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(
      with_appearance(
          R"({"theme_background":false,"background":[40,50,60],"brightness":-13,"text":[160,160,160],"placeholder":[0,0,0],"theme_hover_text":false,"hover_text":[200,210,220]})"),
      out,
      error));
  EXPECT_FALSE(out.appearance.theme_background);
  EXPECT_EQ(out.appearance.background, (std::array<int, 3>{40, 50, 60}));
  EXPECT_FALSE(out.appearance.theme_hover_text);
  EXPECT_EQ(out.appearance.hover_text, (std::array<int, 3>{200, 210, 220}));
  for (const std::string appearance : {R"({"text":[-1,0,0]})",
                                       R"({"text":[0,0]})",
                                       R"({"text":[true,0,0]})",
                                       R"({"text":[0.5,0,0]})",
                                       R"({"brightness":129})",
                                       R"({"brightness":true})",
                                       R"({"text":[256,0,0]})",
                                       R"({"brightness":-129})",
                                       R"({"brightness":1.5})",
                                       R"({"theme_background":1})",
                                       R"({"unknown":0})",
                                       "null"})
  {
    out.generation = 99;
    EXPECT_FALSE(parse_menu_snapshot(with_appearance(appearance), out, error));
    EXPECT_EQ(out.generation, 99);
  }
}

TEST(hotbox_model, SelectionActionsUseLiteralRegisteredIdsAndUnknownRemainsAtomic)
{
  const std::array<std::pair<const char *, const char *>, 4> actions = {
      std::pair{"context.components.object", "mode.object"},
      std::pair{"common.select.all", "selection.select_all"},
      std::pair{"common.select.grow", "selection.grow"},
      std::pair{"common.select.shrink", "selection.shrink"},
  };
  for (const auto &[id, command] : actions) {
    const std::string child = "{\"id\":\"" + std::string(id) +
                              "\",\"kind\":\"command\",\"label\":\"Selection Action\"," +
                              "\"command\":\"" + command +
                              "\",\"enabled\":true,\"reason\":\"\",\"children\":[]}";
    MenuSnapshot out{};
    std::string error;
    ASSERT_TRUE(parse_menu_snapshot(snapshot(child), out, error)) << error;
    ASSERT_EQ(out.menus[0].children.size(), 1);
    EXPECT_EQ(out.menus[0].children[0].id, id);
    EXPECT_EQ(out.menus[0].children[0].command, command);
  }

  MenuSnapshot out{};
  out.generation = 99;
  out.style = "untouched";
  std::string error;
  EXPECT_FALSE(parse_menu_snapshot(
      snapshot(
          R"({"id":"common.select.unknown","kind":"command","label":"Unknown","command":"selection.unknown","enabled":true,"reason":"","children":[]})"),
      out,
      error));
  EXPECT_EQ(out.generation, 99);
  EXPECT_EQ(out.style, "untouched");
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
          R"({"id":"bad","kind":"setting","label":"Bad","command":"center.RIGHTMOUSE","enabled":true,"reason":"","value":"missing.menu","children":[]})"),
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

TEST(hotbox_model, CenterButtonSettingAcceptsRegisteredMenuOrDisabledOnly)
{
  const std::string registered =
      R"({"id":"center.mapping","kind":"setting","label":"Pane Shading","command":"center.RIGHTMOUSE","enabled":true,"reason":"","value":"views","children":[]})";
  const std::string disabled =
      R"({"id":"center.disabled","kind":"setting","label":"Disabled","command":"center.LEFTMOUSE","enabled":true,"reason":"","value":"none","children":[]})";
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(snapshot(registered + "," + disabled), out, error));
}

TEST(hotbox_model, NodeCountAndDepthAreBounded)
{
  std::string children;
  for (int i = 0; i < 2044; i++) {
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
                                  std::string(512 * 1024 + 1, ' '),
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

TEST(hotbox_model, CreationCompanionIsOnlyTheFixedSixthRootAndWorkflowStateIsReadOnly)
{
  const std::string state = R"({"id":"context.create_menu.exit_on_completion","kind":"disabled","label":"Exit On Completion","command":"","enabled":false,"reason":"Not implemented","indicator":"checkbox","checked":true,"children":[]})";
  const auto list = [&](const std::string &id, const std::string &children) {
    return replace(menu(id, children), "\"children\":", "\"presentation\":\"list\",\"children\":");
  };
  std::string valid = snapshot();
  valid.insert(valid.size() - 2, "," + list("context.modeling_object_menu", "") + "," + list("context.create_menu", state));
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(valid, out, error)) << error;
  for (const auto &invalid : {
      replace(valid, "context.create_menu\",", "context.create_menu_extra\","),
      replace(valid, "\"indicator\":\"checkbox\"", "\"indicator\":\"radio\""),
      replace(valid, "context.create_menu.exit_on_completion", "unrelated.disabled"),
      replace(valid, "\"enabled\":false", "\"enabled\":true")}) {
    EXPECT_FALSE(parse_menu_snapshot(invalid, out, error));
  }
}

TEST(hotbox_model, ExtendedSnapshotByteLimitStillRejectsOversizeAtomically)
{
  auto json = snapshot();
  json.append(512 * 1024 - json.size(), ' ');
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(json, out, error));
  out.generation = 91;
  json += ' ';
  EXPECT_FALSE(parse_menu_snapshot(json, out, error));
  EXPECT_EQ(out.generation, 91);
}

TEST(hotbox_model, TrailingContentIsRejectedAtomically)
{
  for (const std::string suffix : {" {}", " true", " garbage", "\n[]"}) {
    MenuSnapshot out{};
    out.generation = 77;
    out.style = "sentinel";
    std::string error;
    EXPECT_FALSE(parse_menu_snapshot(snapshot() + suffix, out, error)) << suffix;
    EXPECT_EQ(out.generation, 77);
    EXPECT_EQ(out.style, "sentinel");
    EXPECT_FALSE(error.empty());
  }
  MenuSnapshot out{};
  std::string error;
  EXPECT_TRUE(parse_menu_snapshot(snapshot() + " \t\r\n", out, error));
  EXPECT_EQ(out.generation, 7);
}
}  // namespace blender::axismeld

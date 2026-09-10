/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_hotbox_menu.hh"
#include "BLI_serialize.hh"
#include <algorithm>
#include <sstream>
#include <unordered_set>

namespace blender::axismeld {
namespace {
using namespace io::serialize;
bool fields(const DictionaryValue *dict,
            std::initializer_list<std::string_view> required,
            std::initializer_list<std::string_view> optional = {})
{
  if (!dict)
    return false;
  for (const auto key : required) {
    if (!dict->lookup(std::string(key)))
      return false;
  }
  for (const auto &item : dict->elements()) {
    if (std::find(required.begin(), required.end(), item.first) == required.end() &&
        std::find(optional.begin(), optional.end(), item.first) == optional.end())
      return false;
  }
  return true;
}

bool text(const DictionaryValue &dict,
          const char *key,
          std::string &out,
          const bool identifier = false,
          const bool limited = false)
{
  const auto value = dict.lookup_str(key);
  if (!value)
    return false;
  out = *value;
  size_t characters = 0;
  for (const unsigned char c : out) {
    if (c < 32 || (identifier && c >= 127))
      return false;
    characters += (c & 0xc0) != 0x80;
  }
  return (!limited || characters <= 128) &&
         (!identifier || (!out.empty() && out.size() <= 128 && !out.starts_with("@scroll:")));
}

bool setting_value(const std::string &command, const std::string &value)
{
  if (command == "style")
    return value == "rows" || value == "zones" || value == "center";
  if (command == "transparency")
    return value == "0" || value == "25" || value == "50" || value == "75" || value == "100";
  if (command == "center.LEFTMOUSE" || command == "center.MIDDLEMOUSE" ||
      command == "center.RIGHTMOUSE")
    return !value.empty();
  return (command == "row.common" || command == "row.pane" || command == "row.modeling") &&
         value == "toggle";
}

const std::unordered_set<std::string> commands = {"tool.select",
                                                  "transform.move",
                                                  "transform.rotate",
                                                  "transform.scale",
                                                  "selection.toggle_component",
                                                  "selection.vertex_mode",
                                                  "selection.edge_mode",
                                                  "selection.face_mode",
                                                  "selection.select_all",
                                                  "selection.grow",
                                                  "selection.shrink",
                                                  "view.focus_selected",
                                                  "view.frame_all",
                                                  "view.orbit",
                                                  "view.pan",
                                                  "view.dolly",
                                                  "view.wireframe",
                                                  "view.shaded",
                                                  "hotbox.open",
                                                  "view.toggle_quad",
                                                  "view.perspective",
                                                  "view.side",
                                                  "view.front",
                                                  "view.top",
                                                  "view.left",
                                                  "view.back",
                                                  "view.bottom"};

struct Parser {
  std::unordered_set<std::string> ids, menu_ids;
  std::vector<std::pair<std::string, std::string>> center_settings;
  bool node(const Value &value, MenuNode &out, const int depth)
  {
    const auto *dict = value.as_dictionary_value();
    if (depth > 8 || ids.size() >= 256 ||
        !fields(
            dict, {"id", "kind", "label", "command", "enabled", "reason", "children"}, {"value"}))
      return false;
    std::string kind;
    if (!text(*dict, "id", out.id, true) || !ids.insert(out.id).second ||
        !text(*dict, "kind", kind) || !text(*dict, "label", out.label, false, true) ||
        !text(*dict, "command", out.command) || !text(*dict, "reason", out.reason))
      return false;
    const auto enabled = dict->lookup_bool("enabled");
    const auto *children = dict->lookup_array("children");
    if (!enabled || !children)
      return false;
    out.enabled = *enabled;
    if (dict->lookup("value") && !text(*dict, "value", out.value))
      return false;
    if (kind == "menu") {
      out.kind = MenuKind::Menu;
      menu_ids.insert(out.id);
      if (!out.command.empty() || !out.value.empty())
        return false;
    }
    else {
      if (!children->elements().is_empty())
        return false;
      if (kind == "command") {
        out.kind = MenuKind::Command;
        if (!commands.contains(out.command) || !out.value.empty())
          return false;
      }
      else if (kind == "setting") {
        out.kind = MenuKind::Setting;
        if (!setting_value(out.command, out.value))
          return false;
        if (out.command.starts_with("center."))
          center_settings.emplace_back(out.command, out.value);
      }
      else {
        if (out.enabled || !out.command.empty() || !out.value.empty())
          return false;
        if (kind == "disabled" && !out.reason.empty())
          out.kind = MenuKind::Disabled;
        else if (kind == "separator")
          out.kind = MenuKind::Separator;
        else
          return false;
      }
    }
    for (const auto &child : children->elements()) {
      MenuNode next{};
      if (!node(*child, next, depth + 1))
        return false;
      out.children.push_back(std::move(next));
    }
    return true;
  }
};
}  // namespace

bool parse_menu_snapshot(const std::string_view json, MenuSnapshot &out, std::string &error)
{
  error = "Invalid hotbox snapshot";
  if (json.size() > 256 * 1024)
    return false;
  // Bound nesting before the generic JSON decoder allocates a recursively nested value tree.
  int nesting = 0;
  bool quoted = false, escape = false;
  for (const char c : json) {
    if (quoted) {
      if (escape)
        escape = false;
      else if (c == '\\')
        escape = true;
      else if (c == '"')
        quoted = false;
    }
    else if (c == '"')
      quoted = true;
    else if ((c == '{' || c == '[') && ++nesting > 20)
      return false;
    else if (c == '}' || c == ']')
      --nesting;
  }
  std::istringstream stream{std::string(json)};
  blender::io::serialize::JsonFormatter formatter;
  auto root = formatter.deserialize(stream);
  // The shared formatter extracts one value; this boundary accepts exactly one JSON document.
  if (!root || (stream >> std::ws).peek() != std::char_traits<char>::eof()) {
    error = "Invalid hotbox JSON";
    return false;
  }
  const auto *dict = root->as_dictionary_value();
  if (!fields(dict, {"schema_version", "generation", "settings", "menus"}))
    return false;
  const auto schema = dict->lookup_int("schema_version"),
             generation = dict->lookup_int("generation");
  const auto *settings = dict->lookup_dict("settings");
  const auto *menus = dict->lookup_array("menus");
  if (!schema || *schema != 1 || !generation || *generation <= 0 || !menus ||
      !fields(settings, {"style", "transparency", "rows", "center_buttons"}))
    return false;
  MenuSnapshot next{};
  next.generation = *generation;
  const auto transparency = settings->lookup_int("transparency");
  const auto *rows = settings->lookup_array("rows");
  const auto *buttons = settings->lookup_dict("center_buttons");
  if (!text(*settings, "style", next.style) || !setting_value("style", next.style) ||
      !transparency || *transparency < 0 || *transparency > 100 || *transparency % 25 || !rows ||
      !fields(buttons, {"LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE"}))
    return false;
  next.transparency = int(*transparency);
  const std::vector<std::string> canonical = {"common", "pane", "modeling"};
  int previous = -1;
  for (const auto &row : rows->elements()) {
    const auto *str = row->as_string_value();
    if (!str)
      return false;
    const auto it = std::find(canonical.begin(), canonical.end(), str->value());
    const int index = int(it - canonical.begin());
    if (it == canonical.end() || index <= previous)
      return false;
    previous = index;
    next.rows.push_back(*it);
  }
  Parser parser;
  for (const auto &menu : menus->elements()) {
    MenuNode node{};
    if (!parser.node(*menu, node, 1))
      return false;
    next.menus.push_back(std::move(node));
  }
  const char *groups[] = {"common", "pane", "center", "modeling"};
  if (next.menus.size() != 4)
    return false;
  for (int i = 0; i < 4; i++) {
    if (next.menus[i].id != groups[i] || next.menus[i].kind != MenuKind::Menu)
      return false;
  }
  const char *names[] = {"LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE"};
  for (int i = 0; i < 3; i++) {
    const Value &value = **buttons->lookup(names[i]);
    if (value.type() == eValueType::Null)
      continue;
    const auto *str = value.as_string_value();
    if (!str || !parser.menu_ids.contains(str->value()))
      return false;
    next.center_buttons[i] = str->value();
  }
  for (const auto &[command, value] : parser.center_settings) {
    if (value != "none" && !parser.menu_ids.contains(value))
      return false;
  }
  out = std::move(next);
  error.clear();
  return true;
}
}  // namespace blender::axismeld

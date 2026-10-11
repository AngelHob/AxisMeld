/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "AXM_hotbox_menu.hh"

#include <array>
#include <string>
#include <string_view>
#include <utility>

namespace blender::axismeld {

inline constexpr std::string_view history_root = "context.history";

inline bool history_command_allowed(const std::string_view command)
{
  return command == "edit.bake_selected" || command == "edit.bake_selected_non_deform" ||
         command == "transform.apply_all" || command == "transform.reset_all";
}

struct HistorySelectionSignature {
  unsigned int active_uid = 0, active_data_uid = 0;
  std::vector<std::pair<unsigned int, unsigned int>> selected;

  bool operator==(const HistorySelectionSignature &) const = default;
};

/* Maya buildSelectAllMM: posting and choosing never execute; the trigger's
 * release commits. A posted-but-cancelled menu must never fall back to Frame All. */
class HistoryHoldState {
  bool posted_ = false;
  bool invalidated_ = false;
  std::string selected_;
  HistorySelectionSignature context_;

 public:
  void post(const HistorySelectionSignature &context)
  {
    posted_ = true;
    invalidated_ = false;
    selected_.clear();
    context_ = context;
  }
  bool validate_context(const HistorySelectionSignature &context)
  {
    if (posted_ && (invalidated_ || context_ != context)) {
      invalidated_ = true;
      selected_.clear();
      return false;
    }
    return true;
  }
  bool select(const std::string_view command, const HistorySelectionSignature &context)
  {
    selected_.clear();
    if (!posted_ || !validate_context(context) || !history_command_allowed(command)) {
      return false;
    }
    selected_ = command;
    return true;
  }
  std::string release_command(const HistorySelectionSignature &context)
  {
    validate_context(context);
    return posted_ ? selected_ : "view.frame_all";
  }
};

inline bool history_tree_allowed(const MenuNode &root)
{
  struct Entry {
    std::string_view suffix, direction, command;
  };
  constexpr std::array<Entry, 8> entries = {{{"inputs", "W", ""}, {"outputs", "E", ""},
      {"enable", "N", ""}, {"disable", "S", ""}, {"delete", "NW", "edit.bake_selected"},
      {"delete_non_deformer", "NE", "edit.bake_selected_non_deform"},
      {"freeze", "SE", "transform.apply_all"}, {"reset", "SW", "transform.reset_all"}}};
  if (root.id != history_root || root.kind != MenuKind::Menu ||
      root.presentation != "radial" || root.children.size() != entries.size()) {
    return false;
  }
  for (size_t i = 0; i < entries.size(); i++) {
    const Entry &entry = entries[i];
    const MenuNode &node = root.children[i];
    const std::string id = std::string(history_root) + "." + std::string(entry.suffix);
    const bool options = entry.suffix == "freeze" || entry.suffix == "reset";
    if (node.id != id || node.direction != entry.direction || node.command != entry.command ||
        node.kind != (entry.command.empty() ? MenuKind::Disabled : MenuKind::Command) ||
        (entry.command.empty() && node.enabled) || node.children.size() != size_t(options)) {
      return false;
    }
    if (options) {
      const MenuNode &option = node.children.front();
      if (option.id != id + ".options" || option.kind != MenuKind::Disabled || option.enabled ||
          !option.command.empty() || !option.children.empty()) {
        return false;
      }
    }
  }
  return true;
}

}  // namespace blender::axismeld

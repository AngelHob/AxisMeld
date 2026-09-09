/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "AXM_hotbox_menu.hh"
#include "AXM_hotbox_state.hh"
#include "WM_types.hh"
#include <string>

namespace blender::axismeld {
bool parse_menu_snapshot(std::string_view json, MenuSnapshot &out, std::string &error);
const MenuNode *hotbox_find_node(const std::vector<MenuNode> &nodes, std::string_view id);
/* One owning visual model. Coordinates are logical region pixels, including real pointer origins.
 */
struct HotboxVisual {
  MenuSnapshot snapshot;
  std::vector<std::string> open_path;
  std::unordered_map<std::string, int> scroll_offsets;
  std::unordered_map<std::string, float> label_widths;
  MenuLayout menu_layout;
  std::string pending_leaf;
  std::string hover_id;
  int hover_depth = -1;
  int active_mouse = 0;
  bool marking = false;
  bool tap_eligible = true;
  HotboxAction candidate = HotboxAction::None;
  float center[2], origin[2];
  float scale = 1;
  float width, height;
};
void hotbox_measure(HotboxVisual &data);
void hotbox_layout(HotboxVisual &data);
void hotbox_draw(const HotboxVisual &data);
}  // namespace blender::axismeld

namespace blender {
struct bContext;
/* Copy a fresh Python snapshot; empty on failure, never a previous response. */
std::string axismeld_hotbox_refresh(bContext *C);
/* Caller owns UI lifetime: close-before policy, remove visuals, dispatch, then guard. */
wmOperatorStatus axismeld_hotbox_dispatch(bContext *C, const char *command);
wmOperatorStatus axismeld_hotbox_setting(bContext *C, const char *setting, const char *value);
wmOperatorStatus axismeld_hotbox_guard_begin(
    bContext *C, int trigger_type, int mouse_type, bool trigger_down, bool mouse_down);
}  // namespace blender

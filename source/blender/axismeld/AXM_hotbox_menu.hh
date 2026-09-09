/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace blender::axismeld {
enum class MenuKind { Menu, Command, Separator, Disabled, Setting };
struct MenuNode {
  std::string id, label, command, reason, value;
  MenuKind kind;
  bool enabled;
  std::vector<MenuNode> children;
};
struct MenuSnapshot {
  uint64_t generation;
  std::string style;
  int transparency;
  std::vector<std::string> rows;
  std::array<std::string, 3> center_buttons;
  std::vector<MenuNode> menus;
};
struct MenuRect {
  std::string id;
  float x, y, width, height;
  int depth;
  bool interactive = true;
};
struct MenuLayout {
  std::vector<MenuRect> rects;
  bool supported;
};

/* Logical pixel coordinates, bottom-left origin. All nodes require measured label widths.
 * open_path contains menu IDs, starting with a visible title (not a root row group).
 * {"center", mapped_menu_id, ...} explicitly anchors a configured menu at the central button;
 * this leading center is an anchor marker, not a parent node (even for {"center", "center"}).
 * Offsets are first child indices, keyed independently by row/menu ID; absent means zero.
 * Layout-only @scroll:<owner>:previous/next IDs navigate; they are never commands.
 * The visible central button can extend inward at edges. Gesture origins remain caller-owned.
 */
MenuLayout layout_menu(const MenuSnapshot &snapshot,
                       float width,
                       float height,
                       float center_x,
                       float center_y,
                       const std::vector<std::string> &open_path,
                       const std::unordered_map<std::string, int> &scroll_offsets,
                       const std::unordered_map<std::string, float> &label_widths);
std::string hit_menu(const MenuLayout &layout, float x, float y);
/* Includes disabled/separator occlusion and preserves the exact visible occurrence/depth. */
const MenuRect *hit_menu_rect(const MenuLayout &layout, float x, float y);
bool hotbox_command_closes(std::string_view command);
}  // namespace blender::axismeld

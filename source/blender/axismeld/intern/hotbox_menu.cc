/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_hotbox_menu.hh"

#include <algorithm>
#include <cmath>

namespace blender::axismeld {
namespace {
constexpr float row_height = 28.0f;
constexpr float gap = 4.0f;
constexpr float margin = 8.0f;
constexpr float padding = 24.0f;
constexpr float scroll_width = 24.0f;

bool interactive(const MenuNode &node)
{
  return node.enabled && node.kind != MenuKind::Disabled && node.kind != MenuKind::Separator;
}

const MenuNode *find_node(const std::vector<MenuNode> &nodes, const std::string &id)
{
  for (const MenuNode &node : nodes) {
    if (node.id == id) {
      return &node;
    }
    if (const MenuNode *found = find_node(node.children, id)) {
      return found;
    }
  }
  return nullptr;
}

bool valid_widths(const std::vector<MenuNode> &nodes,
                  const std::unordered_map<std::string, float> &widths,
                  const float available)
{
  for (const MenuNode &node : nodes) {
    const auto width = widths.find(node.id);
    if (width == widths.end() || !std::isfinite(width->second) || width->second < 0 ||
        width->second + padding > available || !valid_widths(node.children, widths, available))
    {
      return false;
    }
  }
  return true;
}

class LayoutBuilder {
 public:
  MenuLayout result{{}, true};
  const float width, height, center_x, center_y;
  const std::vector<std::string> &path;
  const std::unordered_map<std::string, int> &offsets;
  const std::unordered_map<std::string, float> &widths;

  int offset(const std::string &owner, const int count) const
  {
    const auto item = offsets.find(owner);
    return std::clamp(item == offsets.end() ? 0 : item->second, 0, std::max(0, count - 1));
  }

  const MenuRect *rect(const std::string &id) const
  {
    for (auto item = result.rects.rbegin(); item != result.rects.rend(); ++item) {
      if (item->id == id) {
        return &*item;
      }
    }
    return nullptr;
  }

  void add(const MenuNode &node, float x, float y, float w, int depth)
  {
    result.rects.push_back({node.id, x, y, w, row_height, depth, interactive(node)});
  }

  void control(const std::string &owner,
               const char *direction,
               float x,
               float y,
               float w,
               int depth,
               bool enabled)
  {
    result.rects.push_back(
        {"@scroll:" + owner + ":" + direction, x, y, w, row_height, depth, enabled});
  }

  std::vector<float> free_rows(const int count) const
  {
    std::vector<float> rows;
    const MenuRect *center = rect("views");
    const float origin = center ? center->y : center_y - row_height / 2;
    const float block_height = count * (row_height + gap) - gap;
    const float above = origin + row_height + gap;
    const float below = origin - gap - block_height;
    const bool above_fits = above + block_height <= height;
    const float bottom = above_fits && (center_y <= height / 2 || below < 0) ? above : below;
    if (bottom < 0 || bottom + block_height > height) {
      return rows;
    }
    for (int i = count - 1; i >= 0; i--) {
      rows.push_back(bottom + i * (row_height + gap));
    }
    return rows;
  }

  void row(const MenuNode &owner, const std::vector<const MenuNode *> &nodes, float y)
  {
    if (nodes.empty()) {
      return;
    }
    float total = -gap;
    for (const MenuNode *node : nodes) {
      total += widths.at(node->id) + padding + gap;
    }
    const bool overflow = total > width - 2 * margin;
    const float room = width - 2 * margin - (overflow ? 2 * (scroll_width + gap) : 0);
    int first = overflow ? offset(owner.id, int(nodes.size())) : 0;
    auto end_of_page = [&](const int start) {
      float used = 0;
      int end = start;
      while (end < int(nodes.size())) {
        const float item_width = widths.at(nodes[end]->id) + padding;
        if (used + item_width > room) {
          break;
        }
        used += item_width + gap;
        end++;
      }
      return end;
    };
    // Preserve a scrolled title when its submenu opens, including caller-provided stale offsets.
    for (int i = 0; i < int(nodes.size()); i++) {
      if (std::find(path.begin(), path.end(), nodes[i]->id) != path.end()) {
        first = std::min(first, i);
        while (end_of_page(first) <= i) {
          first++;
        }
        break;
      }
    }
    const int end = end_of_page(first);
    if (end == first || y < 0) {
      result.supported = false;
      return;
    }
    total = -gap;
    for (int i = first; i < end; i++) {
      total += widths.at(nodes[i]->id) + padding + gap;
    }
    total += overflow ? 2 * (scroll_width + gap) : 0;
    float x = std::clamp(center_x - total / 2, margin, width - margin - total);
    if (overflow) {
      control(owner.id, "previous", x, y, scroll_width, 0, first > 0);
      x += scroll_width + gap;
    }
    for (int i = first; i < end; i++) {
      const float w = widths.at(nodes[i]->id) + padding;
      add(*nodes[i], x, y, w, 0);
      x += w + gap;
    }
    if (overflow) {
      control(owner.id, "next", x, y, scroll_width, 0, end < int(nodes.size()));
    }
  }

  void popup(const MenuNode &owner,
             const MenuRect anchor,
             const int depth,
             const std::string &next)
  {
    if (owner.children.empty()) {
      return;
    }
    float w = 0;
    for (const MenuNode &node : owner.children) {
      w = std::max(w, widths.at(node.id) + padding);
    }
    const int count = int(owner.children.size());
    const int max_rows = int((height - 2 * margin) / row_height);
    const bool overflow = count > max_rows;
    const int capacity = overflow ? max_rows - 2 : count;
    int first = overflow ? std::min(offset(owner.id, count), count - capacity) : 0;
    for (int i = 0; i < count; i++) {
      if (owner.children[i].id == next) {
        first = std::clamp(first, std::max(0, i - capacity + 1), i);
      }
    }
    const float h = (capacity + (overflow ? 2 : 0)) * row_height;
    float x = anchor.x + anchor.width + gap;
    if (x + w > width - margin) {
      x = anchor.x - gap - w;
    }
    x = std::clamp(x, margin, width - margin - w);
    const float bottom = std::clamp(anchor.y + anchor.height - h, margin, height - margin - h);
    float y = bottom + h - row_height;
    if (overflow) {
      control(owner.id, "previous", x, y, w, depth, first > 0);
      y -= row_height;
    }
    for (int i = first; i < first + capacity; i++) {
      add(owner.children[i], x, y, w, depth);
      y -= row_height;
    }
    if (overflow) {
      control(owner.id, "next", x, y, w, depth, first + capacity < count);
    }
  }
};
}  // namespace

MenuLayout layout_menu(const MenuSnapshot &snapshot,
                       const float width,
                       const float height,
                       const float center_x,
                       const float center_y,
                       const std::vector<std::string> &open_path,
                       const std::unordered_map<std::string, int> &scroll_offsets,
                       const std::unordered_map<std::string, float> &label_widths)
{
  if (!std::isfinite(width) || !std::isfinite(height) || !std::isfinite(center_x) ||
      !std::isfinite(center_y) || width < 480 || height < 320 || center_x < 0 ||
      center_x > width || center_y < 0 || center_y > height ||
      !valid_widths(snapshot.menus, label_widths, width - 2 * margin - 2 * (scroll_width + gap)))
  {
    return {{}, false};
  }
  const bool central_path = !open_path.empty() && open_path.front() == "center";
  if (central_path) {
    const MenuNode *target = open_path.size() > 1 ? find_node(snapshot.menus, open_path[1]) :
                                                    nullptr;
    if (!target || target->kind != MenuKind::Menu || !interactive(*target) ||
        std::find(snapshot.center_buttons.begin(), snapshot.center_buttons.end(), target->id) ==
            snapshot.center_buttons.end())
    {
      return {{}, false};
    }
  }
  // A central invocation does not scroll a duplicate title into view on its ordinary main row.
  const std::vector<std::string> row_path = central_path ? std::vector<std::string>{} : open_path;
  LayoutBuilder build{
      {{}, true}, width, height, center_x, center_y, row_path, scroll_offsets, label_widths};
  if (const MenuNode *center = find_node(snapshot.menus, "views")) {
    const float w = label_widths.at(center->id) + padding;
    build.add(*center,
              std::clamp(center_x - w / 2, 0.0f, width - w),
              std::clamp(center_y - row_height / 2, 0.0f, height - row_height),
              w,
              0);
  }
  bool normal_rows = true;
  if (const MenuRect *anchor = build.rect("views")) {
    const MenuNode *central = find_node(snapshot.menus, "center");
    if (central && central->children.size() == 3 && snapshot.style != "center") {
      normal_rows = anchor->x - gap - label_widths.at(central->children.front().id) - padding >=
                        margin &&
                    anchor->x + anchor->width + gap +
                            label_widths.at(central->children.back().id) + padding <=
                        width - margin;
    }
    if (snapshot.style == "rows") {
      for (const std::string &row : snapshot.rows) {
        const float y = anchor->y + (row == "common" ? 64 : row == "pane" ? 32 : -32);
        normal_rows &= y >= 0 && y + row_height <= height;
      }
    }
  }
  std::vector<std::pair<const MenuNode *, std::vector<const MenuNode *>>> rows;
  for (const MenuNode &group : snapshot.menus) {
    const bool central = group.id == "center";
    if (!central &&
        (snapshot.style != "rows" ||
         std::find(snapshot.rows.begin(), snapshot.rows.end(), group.id) == snapshot.rows.end()))
    {
      continue;
    }
    if (central && snapshot.style == "center") {
      continue;
    }
    std::vector<const MenuNode *> nodes;
    for (const MenuNode &node : group.children) {
      if (node.id != "views") {
        nodes.push_back(&node);
      }
    }
    if (normal_rows && central && nodes.size() == 2) {
      // Keep the normal three-button central row whenever the fixed anchor leaves room.
      if (const MenuRect *anchor = build.rect("views")) {
        const MenuRect center = *anchor;
        const float left_width = label_widths.at(nodes[0]->id) + padding;
        const float right_width = label_widths.at(nodes[1]->id) + padding;
        if (center.x - gap - left_width >= margin &&
            center.x + center.width + gap + right_width <= width - margin)
        {
          build.add(*nodes[0], center.x - gap - left_width, center.y, left_width, 0);
          build.add(*nodes[1], center.x + center.width + gap, center.y, right_width, 0);
          continue;
        }
      }
    }
    if (!nodes.empty()) {
      rows.push_back({&group, std::move(nodes)});
    }
  }
  std::vector<float> row_positions;
  if (normal_rows) {
    const MenuRect *center = build.rect("views");
    const float row_origin = center ? center->y : center_y - row_height / 2;
    for (const auto &row : rows) {
      row_positions.push_back(row_origin + (row.first->id == "common" ? 64 :
                                            row.first->id == "pane"   ? 32 :
                                                                        -32));
    }
  }
  else {
    row_positions = build.free_rows(int(rows.size()));
  }
  if (row_positions.size() != rows.size()) {
    return {{}, false};
  }
  for (int i = 0; i < int(rows.size()); i++) {
    build.row(*rows[i].first, rows[i].second, row_positions[i]);
  }
  const MenuNode *previous = nullptr;
  const int first = central_path ? 1 : 0;
  for (int index = first; index < int(open_path.size()); index++) {
    const MenuNode *node = previous ? find_node(previous->children, open_path[index]) :
                                      find_node(snapshot.menus, open_path[index]);
    const MenuRect *anchor = build.rect(central_path && index == first ? "views" :
                                                                         open_path[index]);
    if (!node || !anchor || !interactive(*node) || node->kind != MenuKind::Menu) {
      break;
    }
    build.popup(*node,
                *anchor,
                index - first + 1,
                index + 1 < int(open_path.size()) ? open_path[index + 1] : "");
    previous = node;
  }
  if (!build.result.supported) {
    build.result.rects.clear();
  }
  return build.result;
}

std::string hit_menu(const MenuLayout &layout, const float x, const float y)
{
  if (!layout.supported || !std::isfinite(x) || !std::isfinite(y)) {
    return {};
  }
  const MenuRect *hit = nullptr;
  for (const MenuRect &item : layout.rects) {
    if (x >= item.x && x <= item.x + item.width && y >= item.y && y <= item.y + item.height &&
        (!hit || item.depth >= hit->depth))
    {
      hit = &item;
    }
  }
  return hit && hit->interactive ? hit->id : "";
}

bool hotbox_command_closes(const std::string_view command)
{
  constexpr std::string_view immediate[] = {"view.perspective",
                                            "view.side",
                                            "view.bottom",
                                            "view.front",
                                            "view.back",
                                            "view.top",
                                            "view.left",
                                            "view.focus_selected",
                                            "view.frame_all",
                                            "view.wireframe",
                                            "view.shaded"};
  return std::find(std::begin(immediate), std::end(immediate), command) == std::end(immediate);
}
}  // namespace blender::axismeld

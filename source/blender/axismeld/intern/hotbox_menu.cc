/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_hotbox_menu.hh"

#include <algorithm>
#include <cmath>

namespace blender::axismeld {
namespace {
constexpr float row_height = 38.0f;
constexpr float gap = 10.0f;
// User-supplied Maya reference: ~87px of space beside a ~40px-high central button.
constexpr float center_gap = 2.2f * row_height;
constexpr float margin = 12.0f;
constexpr float padding = 40.0f;
constexpr float secondary_height = 24.0f;
constexpr float secondary_padding = 16.0f;
constexpr float secondary_gap = 4.0f;
constexpr float native_menu_padding = 40.0f;
constexpr float native_entry_padding = 60.0f;  // Native submenu icon/arrow and text padding.
constexpr float scroll_width = 38.0f;
constexpr float row_step = row_height + gap;

bool interactive(const MenuNode &node)
{
  return node.enabled && node.kind != MenuKind::Disabled && node.kind != MenuKind::Separator;
}

bool mapping_list(const std::string &id)
{
  return id == "center.controls.buttons.leftmouse" ||
         id == "center.controls.buttons.middlemouse" || id == "center.controls.buttons.rightmouse";
}

bool native_list(const std::string &id)
{
  return id == "views.style" || id == "center.controls.style" || id == "center.controls.rows" ||
         id == "center.controls.transparency" || id == "center.controls.buttons" ||
         mapping_list(id);
}

float child_padding(const MenuNode &node)
{
  return native_list(node.id) ? native_entry_padding : secondary_padding;
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
  const std::array<float, 2> *popup_origin;

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
    result.rects.push_back(
        {node.id, x, y, w, depth ? secondary_height : row_height, depth, interactive(node)});
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

  bool oval_main(const MenuSnapshot &snapshot)
  {
    if (snapshot.style != "rows" || snapshot.rows.size() != 3) {
      return false;
    }
    const MenuNode *common = find_node(snapshot.menus, "common");
    const MenuNode *pane = find_node(snapshot.menus, "pane");
    const MenuNode *central = find_node(snapshot.menus, "center");
    const MenuNode *modeling = find_node(snapshot.menus, "modeling");
    const MenuRect *anchor = rect("views");
    if (!common || !pane || !central || central->children.size() != 3 || !modeling ||
        modeling->children.size() < 2 || !anchor)
    {
      return false;
    }
    const MenuRect center = *anchor;
    const int split = (int(modeling->children.size()) + 1) / 2;
    std::array<std::vector<const MenuNode *>, 4> rows;
    for (const auto &node : common->children) {
      rows[0].push_back(&node);
    }
    for (const auto &node : pane->children) {
      rows[1].push_back(&node);
    }
    for (int i = 0; i < int(modeling->children.size()); i++) {
      rows[i < split ? 2 : 3].push_back(&modeling->children[i]);
    }
    const std::array<float, 4> taper = {0.72f, 0.92f, 0.92f, 0.64f};
    const std::array<float, 4> y_offset = {2 * row_step, row_step, -row_step, -2 * row_step};
    std::array<float, 4> natural{};
    float span = center.width + 2 * (center_gap + padding +
                                     std::max(widths.at(central->children.front().id),
                                              widths.at(central->children.back().id)));
    for (int i = 0; i < 4; i++) {
      if (rows[i].empty()) {
        return false;
      }
      natural[i] = -gap;
      for (const MenuNode *node : rows[i]) {
        natural[i] += widths.at(node->id) + padding + gap;
      }
      span = std::max(span, natural[i] / taper[i]);
    }
    // A real oval envelope around the invocation point. Compact/edge layouts retain the
    // bounded paged rows below; never move the central hit target away from the press.
    if (center_x - span / 2 < margin || center_x + span / 2 > width - margin ||
        center.y - 2 * row_step < margin || center.y + 2 * row_step + row_height > height - margin)
    {
      return false;
    }
    const float left_width = widths.at(central->children.front().id) + padding;
    const float right_width = widths.at(central->children.back().id) + padding;
    add(central->children.front(), center.x - center_gap - left_width, center.y, left_width, 0);
    add(central->children.back(), center.x + center.width + center_gap, center.y, right_width, 0);
    for (int i = 0; i < 4; i++) {
      const float row_width = span * taper[i];
      const float extra = (row_width - natural[i]) / rows[i].size();
      float x = center_x - row_width / 2;
      for (const MenuNode *node : rows[i]) {
        const float w = widths.at(node->id) + padding + extra;
        add(*node, x, center.y + y_offset[i], w, 0);
        x += w + gap;
      }
    }
    return true;
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
      // Wider central separation can require a separate utility row in small panes.
      // If one side alone is too short, use free slots on both sides of the fixed anchor.
      for (int step = 1; step * row_step < height && int(rows.size()) < count; step++) {
        for (const float y : {origin + step * row_step, origin - step * row_step}) {
          if (y >= margin && y + row_height <= height - margin && int(rows.size()) < count) {
            rows.push_back(y);
          }
        }
      }
      if (int(rows.size()) != count) {
        return {};
      }
      std::sort(rows.begin(), rows.end(), std::greater<float>());
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

  struct EllipseItem {
    const MenuNode *node;
    std::string id;
    float width, nx, ny;
    bool enabled, direction = false;
  };

  bool ellipse(const MenuNode &owner,
               const MenuRect &anchor,
               const int depth,
               const std::vector<EllipseItem> &items,
               const float reference_width,
               const MenuNode *tail = nullptr,
               const bool view_ring = false,
               const bool compact = false)
  {
    const float center_width = anchor.width;
    const float center_height = view_ring ? row_height : secondary_height;
    float button_width = reference_width;
    for (const EllipseItem &item : items) {
      if (item.node) {
        button_width = std::max(button_width, item.width);
      }
    }
    std::vector<MenuRect> local;
    float left = 0, right = 0, bottom = 0, top = 0;
    bool found = false;
    // The ratio fixes a horizontal ellipse. Grow radii, never shrink target sizes.
    for (float ry = 24; ry < height; ry += 1) {
      const float rx = 1.7f * ry;
      local.clear();
      const MenuRect center = {"@back:" + owner.id,
                               -center_width / 2,
                               -center_height / 2,
                               center_width,
                               center_height,
                               depth};
      local.push_back(center);
      bool clear = true;
      left = center.x;
      right = center.x + center.width;
      bottom = center.y;
      top = center.y + center.height;
      for (const EllipseItem &item : items) {
        const float fit_width = item.node ? button_width : item.width;
        const MenuRect candidate{item.id,
                                 item.nx * rx - fit_width / 2,
                                 item.ny * ry - secondary_height / 2,
                                 fit_width,
                                 secondary_height,
                                 depth,
                                 item.enabled,
                                 item.direction,
                                 compact};
        for (const MenuRect &other : local) {
          clear &= candidate.x + candidate.width + secondary_gap <= other.x ||
                   other.x + other.width + secondary_gap <= candidate.x ||
                   candidate.y + candidate.height + secondary_gap <= other.y ||
                   other.y + other.height + secondary_gap <= candidate.y;
        }
        local.push_back(candidate);
        left = std::min(left, candidate.x);
        right = std::max(right, candidate.x + candidate.width);
        bottom = std::min(bottom, candidate.y);
        top = std::max(top, candidate.y + candidate.height);
      }
      if (tail) {
        const float w = widths.at(tail->id) + child_padding(*tail);
        local.push_back({tail->id,
                         -w / 2,
                         bottom - secondary_gap - secondary_height,
                         w,
                         secondary_height,
                         depth});
        bottom = local.back().y;
        left = std::min(left, -w / 2);
        right = std::max(right, w / 2);
      }
      if (right - left > width - 2 * margin || top - bottom > height - 2 * margin) {
        break;
      }
      if (clear) {
        found = true;
        break;
      }
    }
    if (!found) {
      return false;
    }
    const float cx = std::clamp(
        anchor.x + anchor.width / 2, margin - left, width - margin - right);
    const float cy = std::clamp(
        anchor.y + anchor.height / 2, margin - bottom, height - margin - top);
    // Ordinary directories retain one active ring and explicit Back/page navigation.
    // The root remains a draw-only background; the Views ring has no center control.
    std::erase_if(result.rects, [](const MenuRect &item) { return item.depth > 0; });
    for (int i = view_ring ? 1 : 0; i < int(local.size()); i++) {
      MenuRect item = local[i];
      item.x += cx;
      item.y += cy;
      item.native_menu = native_list(item.id);
      item.native_menu_standalone = item.native_menu;
      result.rects.push_back(item);
    }
    return true;
  }

  bool native_popup_position(const MenuRect &anchor,
                             const float desired_width,
                             const float desired_height,
                             const bool exclude_origin,
                             float &x,
                             float &y) const
  {
    x = anchor.x + anchor.width;
    y = std::clamp(
        anchor.y + anchor.height - desired_height, margin, height - margin - desired_height);
    if (x + desired_width <= width - margin) {
      return true;
    }
    x = anchor.x - desired_width;
    if (x >= margin) {
      return true;
    }

    const float origin_x = popup_origin ? (*popup_origin)[0] : center_x;
    const float origin_y = popup_origin ? (*popup_origin)[1] : center_y;
    for (const float candidate_y : {anchor.y + anchor.height, anchor.y - desired_height}) {
      if (candidate_y < margin || candidate_y + desired_height > height - margin) {
        continue;
      }
      for (const float candidate_x : {std::clamp(anchor.x, margin, width - margin - desired_width),
                                      margin,
                                      width - margin - desired_width})
      {
        const float dx = origin_x - std::clamp(origin_x, candidate_x, candidate_x + desired_width);
        const float dy = origin_y -
                         std::clamp(origin_y, candidate_y, candidate_y + desired_height);
        if (exclude_origin && dx * dx + dy * dy <= 12 * 12) {
          continue;
        }
        x = candidate_x;
        y = candidate_y;
        return true;
      }
    }
    return false;
  }

  void popup(const MenuNode &owner,
             const MenuRect anchor,
             const int depth,
             const std::string &next)
  {
    if (owner.children.empty()) {
      return;
    }
    if (owner.id == "views") {
      const MenuNode *style = find_node(owner.children, "views.style");
      if (!style) {
        result.supported = false;
        return;
      }
      constexpr float diagonal = 0.70710678118f;
      const std::array<std::pair<const char *, std::array<float, 2>>, 8> directions = {{
          {"views.perspective", {0, 1}},
          {"views.side", {1, 0}},
          {"views.front", {0, -1}},
          {"views.top", {-1, 0}},
          {"views.left", {-diagonal, diagonal}},
          {"views.back", {-diagonal, -diagonal}},
          {"views.bottom", {diagonal, -diagonal}},
          {"views.camera", {diagonal, diagonal}},
      }};
      std::vector<EllipseItem> items;
      for (const auto &[id, position] : directions) {
        if (const MenuNode *node = find_node(owner.children, id)) {
          items.push_back({node,
                           id,
                           widths.at(id) + secondary_padding,
                           position[0],
                           position[1],
                           interactive(*node),
                           true});
        }
      }
      if (ellipse(owner, anchor, depth, items, 0, style, true)) {
        return;
      }
      // Small panes retain the established seven-direction gestures, not tiny targets.
      std::erase_if(items, [](const EllipseItem &item) { return item.id == "views.camera"; });
      for (EllipseItem &item : items) {
        const auto short_width = widths.find("@compact:" + item.id);
        if (short_width != widths.end()) {
          item.width = short_width->second + secondary_padding;
        }
      }
      result.supported &= items.size() == 7 &&
                          (ellipse(owner, anchor, depth, items, 0, style, true, true) ||
                           ellipse(owner, anchor, depth, items, 0, nullptr, true, true));
      return;
    }
    if (native_list(owner.id)) {
      float w = 0;
      for (const MenuNode &node : owner.children) {
        const float item_padding = node.kind == MenuKind::Menu ? native_entry_padding :
                                                                 native_menu_padding;
        w = std::max(w, widths.at(node.id) + item_padding);
      }
      if (w > width - 2 * margin) {
        result.supported = false;
        return;
      }

      const int count = int(owner.children.size());
      const int minimum_capacity = mapping_list(owner.id) ? 1 : count;
      for (int capacity = count; capacity >= minimum_capacity; capacity--) {
        const bool paged = capacity < count;
        const float h = (capacity + (paged ? 2 : 0)) * secondary_height;
        if (h > height - 2 * margin) {
          continue;
        }
        float x, y;
        if (!native_popup_position(anchor, w, h, owner.id == "views.style", x, y)) {
          continue;
        }

        int first = paged ? std::min(offset(owner.id, count), count - capacity) : 0;
        for (int i = 0; i < count; i++) {
          if (owner.children[i].id == next) {
            first = std::clamp(first, std::max(0, i - capacity + 1), i);
          }
        }
        if (mapping_list(owner.id)) {
          result.native_scroll_bounds[owner.id] = {first, count - capacity};
        }
        int row = 0;
        auto add_native_row = [&](const std::string &id, const bool enabled) {
          result.rects.push_back(
              {id, x, y + h - (row + 1) * secondary_height, w, secondary_height, depth, enabled});
          result.rects.back().native_menu = true;
          row++;
        };
        if (paged) {
          add_native_row("@scroll:" + owner.id + ":previous", first > 0);
        }
        for (int i = first; i < first + capacity; i++) {
          add(owner.children[i], x, y + h - (row + 1) * secondary_height, w, depth);
          result.rects.back().native_menu = true;
          row++;
        }
        if (paged) {
          add_native_row("@scroll:" + owner.id + ":next", first + capacity < count);
        }
        return;
      }

      result.supported = false;
      return;
    }
    const int count = int(owner.children.size());
    float reference_width = 0;
    for (const MenuNode &node : owner.children) {
      reference_width = std::max(reference_width, widths.at(node.id) + child_padding(node));
    }
    for (int capacity = std::min(count, 8); capacity >= 1; capacity--) {
      const bool paged = count > capacity;
      int first = paged ? std::min(offset(owner.id, count), count - capacity) : 0;
      for (int i = 0; i < count; i++) {
        if (owner.children[i].id == next) {
          first = std::clamp(first, std::max(0, i - capacity + 1), i);
        }
      }
      std::vector<EllipseItem> items;
      if (paged) {
        items.push_back(
            {nullptr, "@scroll:" + owner.id + ":previous", scroll_width, 0, 0, first > 0});
      }
      for (int i = first; i < first + capacity; i++) {
        const MenuNode &node = owner.children[i];
        items.push_back(
            {&node, node.id, widths.at(node.id) + child_padding(node), 0, 0, interactive(node)});
      }
      if (paged) {
        items.push_back({nullptr,
                         "@scroll:" + owner.id + ":next",
                         scroll_width,
                         0,
                         0,
                         first + capacity < count});
      }
      const float pi = 3.14159265359f;
      for (int i = 0; i < int(items.size()); i++) {
        const float angle = (items.size() == 2 ? pi / 4 : pi / 2) - 2 * pi * i / items.size();
        items[i].nx = std::cos(angle);
        items[i].ny = std::sin(angle);
      }
      if (ellipse(owner, anchor, depth, items, reference_width)) {
        return;
      }
    }
    result.supported = false;
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
                       const std::unordered_map<std::string, float> &label_widths,
                       const std::array<float, 2> *popup_origin)
{
  if (!std::isfinite(width) || !std::isfinite(height) || !std::isfinite(center_x) ||
      !std::isfinite(center_y) || width < 340 || height < 200 || center_x < 0 ||
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
  LayoutBuilder build{{{}, true},
                      width,
                      height,
                      center_x,
                      center_y,
                      row_path,
                      scroll_offsets,
                      label_widths,
                      popup_origin};
  if (const MenuNode *center = find_node(snapshot.menus, "views")) {
    const float w = label_widths.at(center->id) + padding;
    build.add(*center,
              std::clamp(center_x - w / 2, 0.0f, width - w),
              std::clamp(center_y - row_height / 2, 0.0f, height - row_height),
              w,
              0);
  }
  if (width < 480 || height < 320) {
    std::vector<const MenuNode *> groups;
    for (const MenuNode &group : snapshot.menus) {
      if ((group.id == "center" && snapshot.style != "center") ||
          (snapshot.style == "rows" &&
           std::find(snapshot.rows.begin(), snapshot.rows.end(), group.id) != snapshot.rows.end()))
      {
        groups.push_back(&group);
      }
    }
    if (!groups.empty()) {
      const auto positions = build.free_rows(1);
      if (positions.empty()) {
        return {{}, false};
      }
      const MenuNode pages{"@main", "Main groups", "", "", "", MenuKind::Menu, true, {}};
      build.row(pages, groups, positions.front());
    }
  }
  else if (!build.oval_main(snapshot)) {
    bool normal_rows = true;
    if (const MenuRect *anchor = build.rect("views")) {
      const MenuNode *central = find_node(snapshot.menus, "center");
      if (central && central->children.size() == 3 && snapshot.style != "center") {
        normal_rows = anchor->x - center_gap - label_widths.at(central->children.front().id) -
                              padding >=
                          margin &&
                      anchor->x + anchor->width + center_gap +
                              label_widths.at(central->children.back().id) + padding <=
                          width - margin;
      }
      if (snapshot.style == "rows") {
        for (const std::string &row : snapshot.rows) {
          const float y = anchor->y + (row == "common" ? 2 * row_step :
                                       row == "pane"   ? row_step :
                                                         -row_step);
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
          if (center.x - center_gap - left_width >= margin &&
              center.x + center.width + center_gap + right_width <= width - margin)
          {
            build.add(*nodes[0], center.x - center_gap - left_width, center.y, left_width, 0);
            build.add(*nodes[1], center.x + center.width + center_gap, center.y, right_width, 0);
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
        row_positions.push_back(row_origin + (row.first->id == "common" ? 2 * row_step :
                                              row.first->id == "pane"   ? row_step :
                                                                          -row_step));
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
    MenuRect popup_anchor = *anchor;
    if (popup_origin && node->id == "views") {
      popup_anchor.x = (*popup_origin)[0] - anchor->width / 2;
      popup_anchor.y = (*popup_origin)[1] - anchor->height / 2;
    }
    build.popup(*node,
                popup_anchor,
                index - first + 1,
                index + 1 < int(open_path.size()) ? open_path[index + 1] : "");
    previous = node;
  }
  if (!build.result.supported) {
    build.result.rects.clear();
    build.result.native_scroll_bounds.clear();
  }
  else if (std::any_of(build.result.rects.begin(),
                       build.result.rects.end(),
                       [](const MenuRect &item) { return item.depth > 0; }))
  {
    // Retain the first-level background without allowing it to steal a secondary gesture.
    build.result.hit_depth = 1;
    int native_depth = 0;
    for (const MenuRect &item : build.result.rects) {
      if (item.native_menu && !item.native_menu_standalone) {
        native_depth = std::max(native_depth, item.depth);
      }
    }
    for (MenuRect &item : build.result.rects) {
      // A retained marking ring must not steal a gesture heading into a native cascade.
      // Keep the active anchors, native sibling rows and explicit Back navigation available.
      item.retained_only = item.depth > 0 && item.depth < native_depth &&
                           (!item.native_menu || item.native_menu_standalone) &&
                           !item.id.starts_with("@back:") &&
                           std::find(open_path.begin(), open_path.end(), item.id) ==
                               open_path.end();
    }
  }
  return build.result;
}

int menu_scroll_offset_transition(const MenuLayout &layout,
                                  const std::string_view owner,
                                  const int stored_offset,
                                  const int delta,
                                  const int item_count)
{
  const auto native_bounds = layout.native_scroll_bounds.find(std::string(owner));
  if (native_bounds != layout.native_scroll_bounds.end()) {
    return std::clamp(
        native_bounds->second.effective_first + delta, 0, native_bounds->second.maximum_first);
  }
  return std::clamp(stored_offset + delta, 0, std::max(0, item_count - 1));
}

std::string hit_menu(const MenuLayout &layout, const float x, const float y)
{
  const MenuRect *hit = hit_menu_rect(layout, x, y);
  return hit && hit->interactive ? hit->id : "";
}

const MenuRect *hit_menu_rect(const MenuLayout &layout, const float x, const float y)
{
  if (!layout.supported || !std::isfinite(x) || !std::isfinite(y)) {
    return nullptr;
  }
  const MenuRect *hit = nullptr;
  for (const MenuRect &item : layout.rects) {
    if (!item.retained_only && item.depth >= layout.hit_depth && x >= item.x &&
        x <= item.x + item.width && y >= item.y && y <= item.y + item.height &&
        (!hit || item.depth >= hit->depth))
    {
      hit = &item;
    }
  }
  return hit;
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

std::string_view hotbox_view_short_label(const std::string_view command)
{
  if (command == "view.perspective") {
    return "Persp";
  }
  if (command == "view.side") {
    return "Side";
  }
  if (command == "view.front") {
    return "Front";
  }
  if (command == "view.top") {
    return "Top";
  }
  if (command == "view.left") {
    return "Left";
  }
  if (command == "view.back") {
    return "Back";
  }
  if (command == "view.bottom") {
    return "Bottom";
  }
  return {};
}
}  // namespace blender::axismeld

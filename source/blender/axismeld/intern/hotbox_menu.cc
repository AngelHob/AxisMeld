/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_hotbox_menu.hh"
#include "AXM_context_modeling.hh"

#include <algorithm>
#include <cmath>

namespace blender::axismeld {
MenuRadioState menu_radio_state(const MenuSnapshot &snapshot, const MenuNode &node)
{
  if (node.kind == MenuKind::Command && node.indicator == "radio") {
    return node.checked ? MenuRadioState::Selected : MenuRadioState::Unselected;
  }
  if (node.kind != MenuKind::Setting) {
    return MenuRadioState::None;
  }
  std::string_view current;
  const std::string transparency = std::to_string(snapshot.transparency);
  if (node.command == "style") {
    current = snapshot.style;
  }
  else if (node.command == "transparency") {
    current = transparency;
  }
  else if (node.command == "center.LEFTMOUSE") {
    current = snapshot.center_buttons[0];
  }
  else if (node.command == "center.MIDDLEMOUSE") {
    current = snapshot.center_buttons[1];
  }
  else if (node.command == "center.RIGHTMOUSE") {
    current = snapshot.center_buttons[2];
  }
  else {
    return MenuRadioState::None;
  }
  /* The snapshot parser represents a disabled (JSON null) button mapping as empty. */
  if (node.command.starts_with("center.") && current.empty()) {
    current = "none";
  }
  return node.value == current ? MenuRadioState::Selected : MenuRadioState::Unselected;
}

std::string menu_return_target(const MenuLayout &layout, const float x, const float y)
{
  if (!layout.supported) {
    return {};
  }
  // Nested rings can cover an ancestor center; do not turn a visible child into
  // an invisible Back target. Retained background rectangles do not block return.
  if (const MenuRect *hit = hit_menu_rect(layout, x, y)) {
    if (!hit->retained_only && hit->depth >= layout.hit_depth) {
      return {};
    }
  }
  for (auto item = layout.return_regions.rbegin(); item != layout.return_regions.rend(); ++item) {
    if (x >= item->x && x < item->x + item->width && y >= item->y && y < item->y + item->height) {
      return item->id;
    }
  }
  return {};
}
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

std::array<float, 2> marking_position(const float nx,
                                      const float ny,
                                      const float button_width,
                                      const float center_width,
                                      const float center_height,
                                      const bool compact)
{
  // All marking rings share five staggered rows. Label width changes X only.
  const float step = std::max(secondary_height + (compact ? 4 : 8),
                              (center_height + secondary_height) / 2 + secondary_gap);
  const float side = (button_width + center_width) / 2 + 8;
  return {nx == 0 ? 0 : std::copysign(side - (ny == 0 ? 0 : 16), nx),
          ny == 0 ? 0 : std::copysign(step * (nx == 0 ? 2 : 1), ny)};
}

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

bool native_list(const MenuNode &node)
{
  return node.presentation == "list" || native_list(node.id);
}

float child_padding(const MenuNode &node)
{
  return (native_list(node) ? native_entry_padding : secondary_padding) +
         (node.kind != MenuKind::Menu && !node.children.empty() ? 24.0f : 0.0f);
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
                  const std::unordered_map<std::string, float> &widths)
{
  for (const MenuNode &node : nodes) {
    const auto width = widths.find(node.id);
    if (width == widths.end() || !std::isfinite(width->second) || width->second < 0 ||
        !valid_widths(node.children, widths))
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

  float native_width(const MenuNode &owner) const
  {
    float w = 0;
    for (const auto &node : owner.children) {
      w = std::max(w, widths.at(node.id) +
                         (node.kind == MenuKind::Menu ? native_entry_padding : native_menu_padding) +
                         (node.kind != MenuKind::Menu && !node.children.empty() ? 24.0f : 0.0f));
    }
    return w;
  }

  static float native_row_height(const MenuNode &node)
  {
    return node.kind == MenuKind::Separator ? 6.0f : secondary_height;
  }

  struct NativePage {
    int first = 0, end = 0, maximum_first = 0;
    float height = 0;
    bool paged = false;
  };

  NativePage native_page(const MenuNode &owner, const float room, const std::string &next) const
  {
    NativePage page;
    const int count = int(owner.children.size());
    float total = 0;
    for (const auto &node : owner.children) { total += native_row_height(node); }
    if (total <= room) { page.end = count; page.height = total; return page; }
    page.paged = true;
    const float content_room = room - 2 * secondary_height;
    if (content_room <= 0) { return page; }
    float suffix_height = 0;
    page.maximum_first = count;
    while (page.maximum_first > 0 &&
           suffix_height + native_row_height(owner.children[page.maximum_first - 1]) <= content_room) {
      suffix_height += native_row_height(owner.children[--page.maximum_first]);
    }
    if (page.maximum_first == count) { return page; }
    page.first = std::min(offset(owner.id, count), page.maximum_first);
    const auto end_of_page = [&](const int first) {
      int end = first;
      float used = 0;
      while (end < count && used + native_row_height(owner.children[end]) <= content_room) {
        used += native_row_height(owner.children[end++]);
      }
      return end;
    };
    for (int i = 0; i < count; i++) {
      if (owner.children[i].id == next) {
        page.first = std::min(page.first, i);
        while (end_of_page(page.first) <= i && page.first < page.maximum_first) { page.first++; }
        break;
      }
    }
    page.end = end_of_page(page.first);
    page.height = 2 * secondary_height;
    for (int i = page.first; i < page.end; i++) { page.height += native_row_height(owner.children[i]); }
    return page;
  }

  void native_rows(const MenuNode &owner, const float x, const float top, const float w,
                   const NativePage &page, const int depth, const bool companion)
  {
    result.native_scroll_bounds[owner.id] = {page.first, page.maximum_first};
    float y = top;
    const auto add_row = [&](const std::string &id, const bool enabled, const float h) {
      y -= h;
      MenuRect item{id, x, y, w, h, depth, enabled};
      item.native_menu = true;
      item.companion = companion;
      item.owner = owner.id;
      result.rects.push_back(std::move(item));
    };
    if (page.paged) { add_row("@scroll:" + owner.id + ":previous", page.first > 0, secondary_height); }
    for (int i = page.first; i < page.end; i++) {
      add_row(owner.children[i].id, interactive(owner.children[i]), native_row_height(owner.children[i]));
    }
    if (page.paged) { add_row("@scroll:" + owner.id + ":next", page.first < page.maximum_first, secondary_height); }
    if (companion) {
      MenuRect block{"", x, y, w, top - y, depth, false};
      block.companion = true;
      block.owner = owner.id;
      result.occlusion_regions.push_back(std::move(block));
    }
  }

  /* Append after all radial layout: ellipse rebuilding must never erase the companion. */
  void companion(const MenuNode &owner, const std::vector<std::string> &companion_path)
  {
    if (owner.presentation != "list" || owner.children.empty()) { return; }
    const int base_depth = result.return_regions.empty() ? 1 : result.return_regions.back().depth;
    float left = width, right = 0, bottom = height, top = 0;
    for (const auto &item : result.rects) {
      if (item.depth > 0) {
        left = std::min(left, item.x); right = std::max(right, item.x + item.width);
        bottom = std::min(bottom, item.y); top = std::max(top, item.y + item.height);
      }
    }
    const float w = native_width(owner);
    if (w > width - 2 * margin || left > right) { result.supported = false; return; }
    const int count = int(owner.children.size());
    const auto next_id = [&](const size_t index) -> std::string {
      return index < companion_path.size() ? companion_path[index] : "";
    };
    float x = std::clamp((left + right - w) / 2, margin, width - margin - w);
    float list_top = bottom - margin;
    auto page = native_page(owner, list_top - margin, next_id(1));
    if (page.end - page.first < std::min(count, 3)) {
      const float side_x = right + margin + w <= width - margin ? right + margin : left - margin - w;
      if (side_x >= margin && side_x + w <= width - margin) {
        x = side_x;
        page = native_page(owner, height - 2 * margin, next_id(1));
        list_top = std::clamp(top, margin + page.height, height - margin);
      }
      else if (page.end == page.first) {
        // Keep ring geometry intact while making room for one content row and paging.
        const float room = secondary_height * (count > 1 ? 3 : 1);
        const float dy = margin + room + margin - bottom;
        if (top + dy > height - margin) { result.supported = false; return; }
        for (auto *rects : {&result.rects, &result.return_regions, &result.marking_gaps}) {
          for (auto &item : *rects) { if (item.depth > 0) { item.y += dy; } }
        }
        bottom += dy;
        list_top = bottom - margin;
        page = native_page(owner, list_top - margin, next_id(1));
      }
    }
    if (page.end == page.first) { result.supported = false; return; }
    native_rows(owner, x, list_top, w, page, base_depth, true);
    // The short gap from the ring to the main list is an intentional no-marking corridor.
    if (list_top < bottom && x < right && x + w > left) {
      result.occlusion_regions.push_back({"", x, list_top, w, bottom - list_top, base_depth, false});
    }
    const MenuNode *parent = &owner;
    for (size_t index = 1; index < companion_path.size(); index++) {
      const MenuNode *child = find_node(parent->children, companion_path[index]);
      const MenuRect *anchor_ptr = rect(companion_path[index]);
      if (!child || child->kind != MenuKind::Menu || !interactive(*child) || !anchor_ptr) { break; }
      const MenuRect anchor = *anchor_ptr;
      const float child_w = native_width(*child);
      const int child_count = int(child->children.size());
      if (child_count == 0 || child_w > width - 2 * margin) { break; }
      const auto child_page = native_page(*child, height - 2 * margin, next_id(index + 1));
      if (child_page.end == child_page.first) { break; }
      const float h = child_page.height;
      float child_x, child_y;
      if (!native_popup_position(anchor, child_w, h, true, child_x, child_y)) { break; }
      native_rows(*child, child_x, child_y + h, child_w, child_page,
                  base_depth + int(index), true);
      // Keep native cascade transit spatially owned, including its disabled/empty areas.
      const float corridor_left = child_x >= anchor.x ? anchor.x + anchor.width : child_x + child_w;
      const float corridor_right = child_x >= anchor.x ? child_x : anchor.x;
      if (corridor_right >= corridor_left) {
        result.occlusion_regions.push_back({"", corridor_left - 1, std::min(child_y, anchor.y),
            corridor_right - corridor_left + 2,
            std::max(child_y + h, anchor.y + anchor.height) - std::min(child_y, anchor.y),
            base_depth + int(index), false});
      }
      parent = child;
    }
  }

  void split_options(const MenuSnapshot &snapshot)
  {
    std::vector<MenuRect> cells;
    for (auto &item : result.rects) {
      const MenuNode *node = find_node(snapshot.menus, item.id);
      if (!node || node->kind == MenuKind::Menu || node->children.size() != 1) { continue; }
      const MenuNode &option = node->children[0];
      if (option.id != node->id + ".options" || item.width <= 24) { continue; }
      MenuRect cell = item;
      item.width -= 24;
      cell.id = option.id;
      cell.x = item.x + item.width;
      cell.width = 24;
      cell.interactive = interactive(option);
      cell.direction_label = false;
      cell.option_box = true;
      cells.push_back(std::move(cell));
    }
    result.rects.insert(result.rects.end(), cells.begin(), cells.end());
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
    if (std::any_of(nodes.begin(), nodes.end(), [&](const MenuNode *node) {
          return widths.at(node->id) + padding > room;
        }))
    {
      result.supported = false;
      return;
    }
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
    const float center_height = view_ring && !compact && owner.presentation != "radial" ?
                                    row_height :
                                    secondary_height;
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
      // Tool rings keep native submenu text/arrow padding; a slightly rounder ellipse
      // fits their full labels in small panes without narrowing the actual buttons.
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
        const bool tool_ring = owner.presentation == "radial";
        const float fit_width = tool_ring ? std::max(84.0f, item.width) :
                                           item.node ? button_width : item.width;
        const auto position = marking_position(item.nx, item.ny,
                                                tool_ring ? fit_width : button_width,
                                                center_width, center_height, compact);
        const float px = view_ring ? position[0] : item.nx * rx;
        const float py = view_ring ? position[1] : item.ny * ry;
        const MenuRect candidate{item.id,
                                 px - fit_width / 2,
                                 py - secondary_height / 2,
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
      if (view_ring) {
        break;  // Fixed row geometry cannot improve by growing legacy radii.
      }
    }
    if (!found) {
      return false;
    }
    const float cx = std::clamp(
        anchor.x + anchor.width / 2, margin - left, width - margin - right);
    const float cy = std::clamp(
        anchor.y + anchor.height / 2, margin - bottom, height - margin - top);
    if (view_ring) {
      const float return_width = center_width + 16;
      const float return_height = compact ? 32 : owner.presentation == "radial" ? 40 : 46;
      result.return_regions.push_back({owner.id,
                                       cx - return_width / 2,
                                       cy - return_height / 2,
                                       return_width,
                                       return_height,
                                       depth});
    }
    // Ordinary directories retain one active ring and explicit Back/page navigation.
    // The root remains a draw-only background; the Views ring has no center control.
    std::erase_if(result.rects, [](const MenuRect &item) { return item.depth > 0; });
    result.marking_gaps.clear();
    for (int i = view_ring ? 1 : 0; i < int(local.size()); i++) {
      MenuRect item = local[i];
      item.x += cx;
      item.y += cy;
      item.native_menu = native_list(item.id);
      if (const MenuNode *node = find_node(owner.children, item.id)) {
        item.native_menu |= native_list(*node);
      }
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
    if (owner.presentation == "radial") {
      constexpr float d = 0.70710678118f;
      const std::unordered_map<std::string, std::array<float, 2>> directions = {{"N", {0, 1}},
                                                                                {"NE", {d, d}},
                                                                                {"E", {1, 0}},
                                                                                {"SE", {d, -d}},
                                                                                {"S", {0, -1}},
                                                                                {"SW", {-d, -d}},
                                                                                {"W", {-1, 0}},
                                                                                {"NW", {-d, d}}};
      std::vector<EllipseItem> items;
      for (const MenuNode &node : owner.children) {
        const auto direction = directions.find(node.direction);
        if (direction == directions.end()) {
          result.supported = false;
          return;
        }
        items.push_back({&node,
                         node.id,
                         widths.at(node.id) +
                             (node.kind == MenuKind::Menu ? native_entry_padding : secondary_padding) +
                             (node.kind != MenuKind::Menu && !node.children.empty() ? 24.0f : 0.0f),
                         direction->second[0],
                         direction->second[1],
                         interactive(node),
                         true});
      }
      // Match the actual Views center, not the width of the directory that opened
      // this ring. A 24px center with the same side padding leaves only 8px between
      // diagonal rows. Keep the gesture origin and vertical spacing unchanged.
      const float center_width = widths.at("views") + padding;
      MenuRect ring_anchor = anchor;
      ring_anchor.x += (anchor.width - center_width) / 2;
      ring_anchor.y += (anchor.height - 24) / 2;
      ring_anchor.width = center_width;
      ring_anchor.height = 24;
      result.supported &= ellipse(owner, ring_anchor, depth, items, 0, nullptr, true);
      if (result.supported) {
        // Absent directions block gestures but never consume viewport fitting space
        // or become visible entries. Use the same template at the clamped center.
        const auto &center = result.return_regions.back();
        for (const auto &[direction, vector] : directions) {
          if (std::any_of(owner.children.begin(), owner.children.end(), [&](const MenuNode &node) {
                return node.direction == direction;
              })) {
            continue;
          }
          const float w = 84;
          const auto position = marking_position(vector[0], vector[1], w, center_width, 24, false);
          result.marking_gaps.push_back({"@gap:" + owner.id + ":" + direction,
                                         center.x + center.width / 2 + position[0] - w / 2,
                                         center.y + center.height / 2 + position[1] - 12,
                                         w, secondary_height, depth, false, true});
        }
      }
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
      if (result.supported) {
        for (const MenuRect &item : result.rects) {
          if (item.id == "views.left") {
            const MenuRect &center = result.return_regions.back();
            MenuRect empty = item;
            empty.id = "views.camera";
            empty.x = 2 * (center.x + center.width / 2) - item.x - item.width;
            empty.interactive = false;
            result.marking_gaps.push_back(empty);
            break;
          }
        }
      }
      return;
    }
    if (native_list(owner)) {
      float w = 0;
      for (const MenuNode &node : owner.children) {
        const float item_padding = node.kind == MenuKind::Menu ? native_entry_padding :
                                                                 native_menu_padding;
        w = std::max(w, widths.at(node.id) + item_padding +
                           (node.kind != MenuKind::Menu && !node.children.empty() ? 24.0f : 0.0f));
      }
      if (w > width - 2 * margin) {
        result.supported = false;
        return;
      }

      // Try actual pixel heights, not a count of uniform rows. This keeps separator
      // geometry, page bounds, hit testing and cascade anchors in agreement.
      for (float room = height - 2 * margin; room >= 6; room -= 6) {
        const auto page = native_page(owner, room, next);
        if (page.end == page.first) { continue; }
        float x, y;
        if (!native_popup_position(anchor, w, page.height, owner.id == "views.style", x, y)) {
          continue;
        }
        native_rows(owner, x, y + page.height, w, page, depth, false);
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

MenuLayout layout_menu_in_bounds(
    const MenuSnapshot &snapshot,
    const MenuBounds &bounds,
    const float center_x,
    const float center_y,
    const std::vector<std::string> &open_path,
    const std::unordered_map<std::string, int> &scroll_offsets,
    const std::unordered_map<std::string, float> &label_widths,
    const std::array<float, 2> *popup_origin,
    const std::string_view tool_root,
    const std::vector<std::string> &companion_path)
{
  if (!std::isfinite(bounds.xmin) || !std::isfinite(bounds.ymin) ||
      !std::isfinite(bounds.xmax) || !std::isfinite(bounds.ymax) ||
      bounds.xmax <= bounds.xmin || bounds.ymax <= bounds.ymin ||
      !std::isfinite(center_x) || !std::isfinite(center_y) ||
      (popup_origin && (!std::isfinite((*popup_origin)[0]) ||
                        !std::isfinite((*popup_origin)[1]))))
  {
    return {{}, false};
  }
  const float width = bounds.xmax - bounds.xmin;
  const float height = bounds.ymax - bounds.ymin;
  std::array<float, 2> local_origin;
  if (popup_origin) {
    local_origin = {std::clamp((*popup_origin)[0] - bounds.xmin, 0.0f, width),
                    std::clamp((*popup_origin)[1] - bounds.ymin, 0.0f, height)};
  }
  auto layout = layout_menu(snapshot,
                            width,
                            height,
                            std::clamp(center_x - bounds.xmin, 0.0f, width),
                            std::clamp(center_y - bounds.ymin, 0.0f, height),
                            open_path,
                            scroll_offsets,
                            label_widths,
                            popup_origin ? &local_origin : nullptr,
                            tool_root,
                            companion_path);
  if (!layout.supported) {
    return {{}, false};
  }
  for (auto *rects : {&layout.rects, &layout.return_regions, &layout.marking_gaps,
                      &layout.occlusion_regions}) {
    for (MenuRect &rect : *rects) {
      rect.x += bounds.xmin;
      rect.y += bounds.ymin;
    }
  }
  return layout;
}

MenuLayout layout_menu(const MenuSnapshot &snapshot,
                       const float width,
                       const float height,
                       const float center_x,
                       const float center_y,
                       const std::vector<std::string> &open_path,
                       const std::unordered_map<std::string, int> &scroll_offsets,
                       const std::unordered_map<std::string, float> &label_widths,
                       const std::array<float, 2> *popup_origin,
                       const std::string_view tool_root,
                       const std::vector<std::string> &companion_path)
{
  if (!std::isfinite(width) || !std::isfinite(height) || !std::isfinite(center_x) ||
      !std::isfinite(center_y) || width < 340 || height < 200 || center_x < 0 ||
      center_x > width || center_y < 0 || center_y > height ||
      !valid_widths(snapshot.menus, label_widths))
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
  if (!tool_root.empty()) {
    const MenuNode *node = find_node(snapshot.menus, std::string(tool_root));
    if (!node || node->presentation != "radial" || open_path.empty() ||
        open_path.front() != tool_root)
    {
      return {{}, false};
    }
    MenuRect anchor{node->id, center_x - 12, center_y - 12, 24, 24, 0};
    for (int index = 0; index < int(open_path.size()); index++) {
      if (index) {
        node = find_node(node->children, open_path[index]);
        const MenuRect *found = build.rect(open_path[index]);
        if (!node || !found || node->kind != MenuKind::Menu || !interactive(*node)) {
          break;
        }
        anchor = *found;
      }
      build.popup(
          *node, anchor, index + 1, index + 1 < int(open_path.size()) ? open_path[index + 1] : "");
    }
    if (!build.result.supported) {
      return {{}, false};
    }
    build.result.hit_depth = 1;
    int native_depth = 0;
    for (const MenuRect &item : build.result.rects) {
      if (item.native_menu && !item.native_menu_standalone) {
        native_depth = std::max(native_depth, item.depth);
      }
    }
    for (MenuRect &item : build.result.rects) {
      item.retained_only = item.depth < native_depth &&
                           (!item.native_menu || item.native_menu_standalone) &&
                           std::find(open_path.begin(), open_path.end(), item.id) ==
                               open_path.end();
    }
    if (const auto companion_id = companion_root(tool_root); !companion_id.empty()) {
      if (const MenuNode *companion = find_node(snapshot.menus, std::string(companion_id))) {
        build.companion(*companion, companion_path);
      }
    }
    build.split_options(snapshot);
    return build.result;
  }
  if (const MenuNode *center = find_node(snapshot.menus, "views")) {
    const float w = label_widths.at(center->id) + padding;
    if (w > width || row_height > height) {
      return {{}, false};
    }
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
  for (const auto &root : open_path) {
    if (const auto companion_id = companion_root(root); !companion_id.empty()) {
      if (const MenuNode *companion = find_node(snapshot.menus, std::string(companion_id))) {
        build.companion(*companion, companion_path);
      }
      break;
    }
  }
  build.split_options(snapshot);
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
  if (!hit || !hit->companion) {
    for (const auto &region : layout.occlusion_regions) {
      if (x >= region.x && x <= region.x + region.width &&
          y >= region.y && y <= region.y + region.height) {
        return &region;
      }
    }
  }
  return hit;
}

static const MenuRect *nearest_marking_rect_impl(const MenuLayout &layout,
                                                const float x,
                                                const float y,
                                                const std::array<float, 2> *gesture_origin,
                                                const MenuRect *active_center)
{
  if (!layout.supported || !std::isfinite(x) || !std::isfinite(y)) {
    return nullptr;
  }
  for (const auto &region : layout.occlusion_regions) {
    if (x >= region.x && x <= region.x + region.width &&
        y >= region.y && y <= region.y + region.height) {
      return nullptr;
    }
  }
  const MenuRect *nearest = nullptr;
  float best = INFINITY, best_secondary = INFINITY;
  float left = INFINITY, right = -INFINITY, bottom = INFINITY, top = -INFINITY;
  std::vector<const MenuRect *> directions;
  for (const auto *rects : {&layout.rects, &layout.marking_gaps}) {
    for (const MenuRect &item : *rects) {
      if (!item.retained_only && item.depth >= layout.hit_depth && item.direction_label &&
          (!active_center || item.depth == active_center->depth) &&
          (!item.native_menu || item.native_menu_standalone)) {
        directions.push_back(&item);
        left = std::min(left, item.x);
        right = std::max(right, item.x + item.width);
        bottom = std::min(bottom, item.y);
        top = std::max(top, item.y + item.height);
      }
    }
  }
  if (left > right) {
    return nullptr;
  }
  // The visual center remains the blind-gesture zone; use the layout's actual
  // dimensions, not an unrelated circular threshold that can turn Side into Bottom.
  for (const MenuRect &center : layout.return_regions) {
    if (active_center && &center != active_center) {
      continue;
    }
    if (!active_center && center.id == "views" && gesture_origin) {
      const float dx = x - (*gesture_origin)[0], dy = y - (*gesture_origin)[1];
      const float radius = std::min(center.width, center.height) / 2;
      if (dx * dx + dy * dy <= radius * radius) {
        return nullptr;
      }
    }
    if ((active_center || center.id == "views") &&
        x >= center.x && x <= center.x + center.width &&
        y >= center.y && y <= center.y + center.height) {
      return nullptr;
    }
  }
  // When edge placement shifts the whole ring inward, preserve blind gestures in
  // the empty corridor from the real press to the ring. Visible rectangles win upstream.
  if (gesture_origin && (((*gesture_origin)[0] < left && x < left) ||
                         ((*gesture_origin)[0] > right && x > right) ||
                         ((*gesture_origin)[1] < bottom && y < bottom) ||
                         ((*gesture_origin)[1] > top && y > top))) {
    return nullptr;
  }
  if (active_center) {
    // Content-sized radial labels have different outer edges. Continue an actual
    // row as soon as its edge is crossed, before the whole ring's bounding edge;
    // otherwise a longer neighbouring row can capture the short button's tail.
    const float cx = active_center->x + active_center->width / 2;
    for (const MenuRect *item : directions) {
      const float item_cx = item->x + item->width / 2;
      if (y >= item->y && y <= item->y + item->height &&
          ((item_cx <= cx && x < item->x) ||
           (item_cx >= cx && x > item->x + item->width))) {
        return item;
      }
    }
  }
  // Continue the outer edge regions outward. Otherwise a farther horizontal stroke
  // eventually prefers the slightly protruding middle row over its adjacent row.
  const float px = std::clamp(x, left, right), py = std::clamp(y, bottom, top);
  for (const MenuRect *direction : directions) {
    const MenuRect &item = *direction;
    const float dx = px - std::clamp(px, item.x, item.x + item.width);
    const float dy = py - std::clamp(py, item.y, item.y + item.height);
    // Straight outward strokes continue their displayed row/column. Comparing only
    // Euclidean distance would let a protruding neighbour capture the far end again.
    const bool horizontal = (x < left || x > right) && y >= bottom && y <= top;
    const bool vertical = (y < bottom || y > top) && x >= left && x <= right;
    const float distance = horizontal ? std::abs(dy) : vertical ? std::abs(dx) : dx * dx + dy * dy;
    const float secondary = horizontal ? std::abs(dx) : vertical ? std::abs(dy) : 0;
    if (distance < best || (distance == best && secondary < best_secondary)) {
      nearest = &item;
      best = distance;
      best_secondary = secondary;
    }
  }
  return nearest;
}

const MenuRect *nearest_marking_rect(const MenuLayout &layout, const float x, const float y,
                                    const std::array<float, 2> *gesture_origin)
{
  return nearest_marking_rect_impl(layout, x, y, gesture_origin, nullptr);
}

const MenuRect *hit_marking_menu_rect(const MenuLayout &layout, const std::string_view owner,
                                    const float x, const float y)
{
  if (!layout.supported || !std::isfinite(x) || !std::isfinite(y) ||
      layout.return_regions.empty() || layout.return_regions.back().id != owner) {
    return nullptr;
  }
  const MenuRect &center = layout.return_regions.back();
  for (const MenuRect &item : layout.rects) {
    if (!item.retained_only && item.depth >= center.depth && item.native_menu &&
        !item.native_menu_standalone && !item.companion) {
      return nullptr;
    }
  }
  if (const MenuRect *hit = hit_menu_rect(layout, x, y)) {
    return hit->depth == center.depth && hit->direction_label ? hit : nullptr;
  }
  return nearest_marking_rect_impl(layout, x, y, nullptr, &center);
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

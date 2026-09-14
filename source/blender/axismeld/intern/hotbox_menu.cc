/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_hotbox_menu.hh"
#include "AXM_context_modeling.hh"

#include <algorithm>
#include <cmath>

namespace blender::axismeld {
MenuRadioState menu_radio_state(const MenuSnapshot &snapshot, const MenuNode &node)
{
  if ((node.kind == MenuKind::Command || node.kind == MenuKind::Disabled) && node.indicator == "radio") {
    return node.checked ? MenuRadioState::Selected : MenuRadioState::Unselected;
  }
  if (node.kind != MenuKind::Setting) {
    return MenuRadioState::None;
  }
  std::string_view current;
  const std::string transparency = std::to_string(snapshot.transparency);
  if (node.command == "style") {
    /* Maya's Hotbox Style entries are ordinary executable items, not radio choices. */
    return MenuRadioState::None;
  }
  if (node.command == "transparency") {
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
  return node.kind == MenuKind::Menu && node.presentation != "radial" && node.id != "views";
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
    // Maya divider labels are native noninteractive headings, not thin rules.
    return node.kind == MenuKind::Separator && node.label.empty() ? 6.0f : secondary_height;
  }

  struct NativeColumn {
    int first, end;
    float height;
  };
  struct NativeColumns {
    std::vector<NativeColumn> columns;
    float width = 0, height = 0, row_width = 0;
  };

  NativeColumns native_columns(const MenuNode &owner, const float room) const
  {
    NativeColumns result;
    if (room < secondary_height) { return result; }
    result.row_width = native_width(owner);
    const int count = int(owner.children.size());
    for (const bool prefer_separator : {true, false}) {
      result.columns.clear();
      result.height = 0;
      for (int first = 0; first < count;) {
        int end = first, separator = -1;
        float used = 0, separator_height = 0;
        while (end < count && used + native_row_height(owner.children[end]) <= room) {
          const MenuNode &node = owner.children[end];
          const bool heading = node.kind == MenuKind::Separator && !node.label.empty();
          if (heading) {
            // A heading belongs with the first following action. Include intervening
            // headings/rules so a column never strands a section title at its foot.
            float group_height = native_row_height(node);
            for (int next = end + 1; next < count; next++) {
              group_height += native_row_height(owner.children[next]);
              if (owner.children[next].kind != MenuKind::Separator) { break; }
            }
            if (used + group_height > room) { break; }
            if (used >= room / 2) {
              separator = end;
              separator_height = used;
            }
          }
          used += native_row_height(node);
          if (node.kind == MenuKind::Separator && !heading && used >= room / 2) {
            separator = end + 1;
            separator_height = used;
          }
          end++;
        }
        if (end == first) { return {}; }
        if (prefer_separator && end < count && separator > first) {
          end = separator;
          used = separator_height;
        }
        result.columns.push_back({first, end, used});
        result.height = std::max(result.height, used);
        first = end;
      }
      result.width = result.columns.size() * (result.row_width + secondary_gap) - secondary_gap;
      if (result.width <= width - 2 * margin) { return result; }
    }
    return {};
  }

  void native_rows(const MenuNode &owner, const float x, const float top,
                   const NativeColumns &columns, const int depth, const bool companion)
  {
    for (int column = 0; column < int(columns.columns.size()); column++) {
      const auto &range = columns.columns[column];
      const float left = x + column * (columns.row_width + secondary_gap);
      float y = top;
      for (int index = range.first; index < range.end; index++) {
        const MenuNode &node = owner.children[index];
        const float h = native_row_height(node);
        y -= h;
        MenuRect item{node.id, left, y, columns.row_width, h, depth, interactive(node)};
        item.native_menu = true;
        item.companion = companion;
        item.owner = owner.id;
        item.column = column;
        result.rects.push_back(std::move(item));
      }
      MenuRect block{"", left, y, columns.row_width, top - y, depth, false};
      block.native_menu = true;
      block.companion = companion;
      block.owner = owner.id;
      block.column = column;
      result.native_columns.push_back(block);
      result.occlusion_regions.push_back(block);
    }
    // Inter-column whitespace is spatially owned, not a passage to the ring below.
    if (columns.columns.size() > 1) {
      MenuRect hull{"", x, top - columns.height, columns.width, columns.height, depth, false};
      hull.owner = owner.id;
      hull.companion = companion;
      result.occlusion_regions.push_back(hull);
    }
  }

  void translate_active(const float dx, const float dy)
  {
    for (auto *rects : {&result.rects, &result.return_regions, &result.marking_gaps,
                       &result.occlusion_regions, &result.native_columns}) {
      for (MenuRect &item : *rects) {
        if (item.depth > 0) { item.x += dx; item.y += dy; }
      }
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
    if (left > right) { result.supported = false; return; }
    // Reserve the unmodified marking ring first, then fit the complete list below.
    const auto columns = native_columns(owner, height - 2 * margin - (top - bottom) - margin);
    if (columns.columns.empty()) { result.supported = false; return; }
    const float dy = std::max(0.0f, margin + columns.height + margin - bottom);
    if (top + dy > height - margin) { result.supported = false; return; }
    translate_active(0, dy);
    bottom += dy;
    top += dy;
    const float x = std::clamp((left + right - columns.width) / 2,
                               margin, width - margin - columns.width);
    const float list_top = bottom - margin;
    native_rows(owner, x, list_top, columns, base_depth, true);
    result.occlusion_regions.push_back({"", x, list_top, columns.width,
                                        margin, base_depth, false});
    const MenuNode *parent = &owner;
    for (size_t index = 1; index < companion_path.size(); index++) {
      const MenuNode *child = find_node(parent->children, companion_path[index]);
      const MenuRect *anchor_ptr = rect(companion_path[index]);
      if (!child || child->kind != MenuKind::Menu || !interactive(*child) || !anchor_ptr) { break; }
      const MenuRect anchor = *anchor_ptr;
      const auto child_columns = native_columns(*child, height - 2 * margin);
      if (child_columns.columns.empty()) { result.supported = false; return; }
      const float h = child_columns.height;
      float child_x, child_y;
      if (!native_popup_position(anchor, child_columns.width, h, true, child_x, child_y)) {
        result.supported = false; return;
      }
      const float child_w = child_columns.width;
      native_rows(*child, child_x, child_y + h, child_columns,
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
    // complete wrapped rows below; never move the central hit target away from the press.
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

  void row(const MenuNode & /*owner*/, const std::vector<const MenuNode *> &nodes, float y)
  {
    if (nodes.empty()) {
      return;
    }
    float total = -gap;
    for (const MenuNode *node : nodes) {
      total += widths.at(node->id) + padding + gap;
    }
    if (total > width - 2 * margin || y < 0) {
      result.supported = false;
      return;
    }
    float x = std::clamp(center_x - total / 2, margin, width - margin - total);
    for (const MenuNode *node : nodes) {
      const float w = widths.at(node->id) + padding;
      add(*node, x, y, w, 0);
      x += w + gap;
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
    result.occlusion_regions.clear();
    result.native_columns.clear();
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
    MenuRect parent = anchor;
    for (const MenuRect &column : result.native_columns) {
      if (column.owner == anchor.owner && column.depth == anchor.depth && !anchor.owner.empty()) {
        const float right = std::max(parent.x + parent.width, column.x + column.width);
        const float top = std::max(parent.y + parent.height, column.y + column.height);
        parent.x = std::min(parent.x, column.x);
        parent.y = std::min(parent.y, column.y);
        parent.width = right - parent.x;
        parent.height = top - parent.y;
      }
    }
    const auto clear = [&](const float px, const float py) {
      for (const MenuRect &column : result.native_columns) {
        if (column.owner != anchor.owner || anchor.owner.empty()) { continue; }
        if (px < column.x + column.width && px + desired_width > column.x &&
            py < column.y + column.height && py + desired_height > column.y) {
          return false;
        }
      }
      return true;
    };
    x = parent.x + parent.width;
    y = std::clamp(anchor.y + anchor.height - desired_height, margin, height - margin - desired_height);
    if (x + desired_width <= width - margin && clear(x, y)) { return true; }
    x = parent.x - desired_width;
    if (x >= margin && clear(x, y)) { return true; }

    const float origin_x = popup_origin ? (*popup_origin)[0] : center_x;
    const float origin_y = popup_origin ? (*popup_origin)[1] : center_y;
    for (const float candidate_y : {parent.y + parent.height, parent.y - desired_height}) {
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
        if (!clear(candidate_x, candidate_y) || (exclude_origin && dx * dx + dy * dy <= 12 * 12)) {
          continue;
        }
        x = candidate_x;
        y = candidate_y;
        return true;
      }
    }
    // Last resort: retain every row while covering lower-level ancestor content.
    // The direct anchor and actual Views press-origin remain unobscured.
    for (const float py : {margin, height - margin - desired_height}) {
      for (const float px : {margin, width - margin - desired_width}) {
        const bool covers_anchor = px < anchor.x + anchor.width && px + desired_width > anchor.x &&
                                   py < anchor.y + anchor.height && py + desired_height > anchor.y;
        const float dx = origin_x - std::clamp(origin_x, px, px + desired_width);
        const float dy = origin_y - std::clamp(origin_y, py, py + desired_height);
        if ((!covers_anchor || anchor.depth == 0) &&
            (!exclude_origin || dx * dx + dy * dy > 12 * 12)) {
          x = px; y = py; return true;
        }
      }
    }
    return false;
  }

  void popup(const MenuNode &owner,
             const MenuRect anchor,
             const int depth,
             const std::string & /*next*/)
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
        if (!find_node(owner.children, "views.camera")) {
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
    for (float room = height - 2 * margin; room >= secondary_height; room -= 6) {
      const auto columns = native_columns(owner, room);
      if (columns.columns.empty()) { continue; }
      float x, y;
      if (native_popup_position(anchor, columns.width, columns.height,
                                owner.id == "views.style", x, y)) {
        native_rows(owner, x, y + columns.height, columns, depth, false);
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
    local_origin = {(*popup_origin)[0] - bounds.xmin,
                    (*popup_origin)[1] - bounds.ymin};
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
                      &layout.occlusion_regions, &layout.native_columns}) {
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
    if (const auto companion_id = active_companion_root(open_path); !companion_id.empty()) {
      if (const MenuNode *companion = find_node(snapshot.menus, std::string(companion_id))) {
        build.companion(*companion,
            !companion_path.empty() && companion_path.front() == companion_id ? companion_path :
                                                                               std::vector<std::string>{});
      }
    }
    if (!build.result.supported) { return {{}, false}; }
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
  if (!build.oval_main(snapshot)) {
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
    // Preserve every main title. Overflow wraps to additional complete title rows,
    // never to a hidden group shell or a spatial page.
    std::vector<std::pair<const MenuNode *, std::vector<const MenuNode *>>> wrapped_rows;
    for (const auto &[owner, nodes] : rows) {
      std::vector<const MenuNode *> line;
      float used = 0;
      for (const MenuNode *node : nodes) {
        const float item_width = label_widths.at(node->id) + padding;
        if (item_width > width - 2 * margin) { return {{}, false}; }
        if (!line.empty() && used + gap + item_width > width - 2 * margin) {
          wrapped_rows.push_back({owner, std::move(line)});
          line.clear();
          used = 0;
          normal_rows = false;
        }
        used += (line.empty() ? 0 : gap) + item_width;
        line.push_back(node);
      }
      if (!line.empty()) { wrapped_rows.push_back({owner, std::move(line)}); }
    }
    rows = std::move(wrapped_rows);
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
  if (const auto companion_id = active_companion_root(open_path); !companion_id.empty()) {
    if (const MenuNode *companion = find_node(snapshot.menus, std::string(companion_id))) {
      build.companion(*companion,
          !companion_path.empty() && companion_path.front() == companion_id ? companion_path :
                                                                             std::vector<std::string>{});
    }
  }
  if (!build.result.supported) { return {{}, false}; }
  build.split_options(snapshot);
  return build.result;
}

int menu_scroll_offset_transition(const MenuLayout & /*layout*/,
                                  const std::string_view /*owner*/,
                                  const int /*stored_offset*/,
                                  const int /*delta*/,
                                  const int /*item_count*/)
{
  return 0;  // Compatibility only: complete menus have no spatial pages.
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
  const MenuRect *occlusion = nullptr;
  for (const auto &region : layout.occlusion_regions) {
    if (hit && hit->native_menu && hit->depth >= region.depth) { continue; }
    if (x >= region.x && x <= region.x + region.width &&
        y >= region.y && y <= region.y + region.height &&
        (!occlusion || region.depth >= occlusion->depth)) {
      occlusion = &region;
    }
  }
  if (occlusion) { return occlusion; }
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

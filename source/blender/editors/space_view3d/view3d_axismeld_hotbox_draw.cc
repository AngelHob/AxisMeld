/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cstring>

#include "BLF_api.hh"
#include "GPU_immediate.hh"
#include "GPU_state.hh"
#include "view3d_axismeld_hotbox_internal.hh"

namespace blender::axismeld {
const MenuNode *hotbox_find_node(const std::vector<MenuNode> &nodes, const std::string_view id)
{
  for (const MenuNode &node : nodes) {
    if (node.id == id) {
      return &node;
    }
    if (const MenuNode *found = hotbox_find_node(node.children, id)) {
      return found;
    }
  }
  return nullptr;
}

void hotbox_measure(HotboxVisual &data)
{
  data.label_widths.clear();
  const int font = BLF_default();
  BLF_size(font, 12 * data.scale);
  auto measure = [&](auto &&self, const std::vector<MenuNode> &nodes) -> void {
    for (const MenuNode &node : nodes) {
      data.label_widths[node.id] = BLF_width(font, node.label.c_str(), node.label.size()) /
                                   data.scale;
      self(self, node.children);
    }
  };
  measure(measure, data.snapshot.menus);
}

void hotbox_layout(HotboxVisual &data)
{
  data.menu_layout = layout_menu(data.snapshot,
                                 data.width,
                                 data.height,
                                 data.center[0],
                                 data.center[1],
                                 data.open_path,
                                 data.scroll_offsets,
                                 data.label_widths);
  if (data.marking) {
    // Reuse the layout engine's appended-list anchor and nested popup rectangles. The seven
    // view leaves are sectors while marking, so their rectangular list counterparts are hidden.
    std::erase_if(data.menu_layout.rects,
                  [](const MenuRect &rect) { return rect.id != "views.style" && rect.depth < 2; });
  }
}

void hotbox_draw(const HotboxVisual &data)
{
  struct Entry {
    MenuRect rect;
    std::string text;
    bool selected, disabled, separator;
  };
  std::vector<Entry> entries;
  if (data.marking) {
    struct Direction {
      const char *id;
      float x, y;
      HotboxAction action;
    };
    const Direction directions[] = {{"views", 0, 0, HotboxAction::None},
                                    {"views.perspective", 0, 64, HotboxAction::Perspective},
                                    {"views.side", 1, 0, HotboxAction::Side},
                                    {"views.front", 0, -64, HotboxAction::Front},
                                    {"views.top", -1, 0, HotboxAction::Top},
                                    {"views.left", -1, 64, HotboxAction::Left},
                                    {"views.back", -1, -64, HotboxAction::Back},
                                    {"views.bottom", 1, -64, HotboxAction::Bottom}};
    float width = 0;
    for (const Direction &d : directions) {
      const auto measured = data.label_widths.find(d.id);
      if (measured != data.label_widths.end()) {
        width = std::max(width, measured->second + 24);
      }
    }
    const float extent = width * 1.5f + 8;
    // Shift the visual group inward. Direction selection still uses the actual captured origin.
    const float cx = extent <= data.width / 2 ?
                         std::clamp(data.origin[0], extent, data.width - extent) :
                         data.width / 2;
    float cy = std::clamp(data.origin[1], 78.0f, data.height - 78.0f);
    float list_top = 0, list_bottom = data.height;
    bool overlaps = false;
    for (const MenuRect &rect : data.menu_layout.rects) {
      list_top = std::max(list_top, rect.y + rect.height);
      list_bottom = std::min(list_bottom, rect.y);
      overlaps |= rect.x < cx + extent && rect.x + rect.width > cx - extent && rect.y < cy + 78 &&
                  rect.y + rect.height > cy - 78;
    }
    if (overlaps) {
      // The default appended Style tree fits beside a 156px-high direction group even at
      // 480x320. Move only the drawing group; lists retain the authoritative layout rectangles
      // and angular selection retains the captured physical mouse origin.
      if (list_top + 4 + 156 <= data.height) {
        cy = list_top + 4 + 78;
      }
      else if (list_bottom - 4 - 156 >= 0) {
        cy = list_bottom - 4 - 78;
      }
    }
    for (const Direction &d : directions) {
      const MenuNode *node = hotbox_find_node(data.snapshot.menus, d.id);
      if (!node) {
        continue;
      }
      entries.push_back({{"", cx + d.x * (width + 8) - width / 2, cy + d.y - 14, width, 28, 0},
                         node->label,
                         d.action != HotboxAction::None && data.candidate == d.action,
                         !node->enabled,
                         false});
    }
  }
  {
    for (const MenuRect &rect : data.menu_layout.rects) {
      const MenuNode *node = hotbox_find_node(data.snapshot.menus, rect.id);
      const std::string label = node ? node->label : rect.id.ends_with(":previous") ? "<" : ">";
      entries.push_back({rect,
                         label,
                         data.hover_id == rect.id && data.hover_depth == rect.depth,
                         !rect.interactive,
                         node && node->kind == MenuKind::Separator});
    }
  }
  const float scale = data.scale;
  const int font = BLF_default();
  BLF_size(font, 12 * scale);
  GPU_blend(GPU_BLEND_ALPHA);
  const uint pos = GPU_vertformat_attr_add(
      immVertexFormat(), "pos", gpu::VertAttrType::SFLOAT_32_32);
  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
  for (const Entry &entry : entries) {
    const MenuRect &r = entry.rect;
    const bool selected = entry.selected && !entry.disabled;
    immUniformColor4f(selected ? .17f : .055f,
                      selected ? .40f : .055f,
                      selected ? .26f : .065f,
                      1 - data.snapshot.transparency / 100.0f);
    immRectf(pos, r.x * scale, r.y * scale, (r.x + r.width) * scale, (r.y + r.height) * scale);
    if (entry.separator) {
      immUniformColor4f(.4f, .4f, .4f, .8f);
      immRectf(pos,
               (r.x + 6) * scale,
               (r.y + 14) * scale,
               (r.x + r.width - 6) * scale,
               (r.y + 15) * scale);
    }
  }
  immUnbindProgram();
  for (const Entry &entry : entries) {
    const MenuRect &r = entry.rect;
    // Alpha is the chosen menu transparency, not permission for obscured menu text to bleed
    // through. Higher-depth rectangles already own these pixels for hit testing.
    const bool occluded = std::any_of(entries.begin(), entries.end(), [&](const Entry &other) {
      const MenuRect &s = other.rect;
      return s.depth > r.depth && r.x < s.x + s.width && r.x + r.width > s.x &&
             r.y < s.y + s.height && r.y + r.height > s.y;
    });
    if (occluded) {
      continue;
    }
    const float brightness = entry.disabled ? .54f : .95f;
    BLF_color4f(font, brightness, brightness, brightness, 1);
    const float width = BLF_width(font, entry.text.c_str(), entry.text.size());
    BLF_position(font, (r.x + r.width / 2) * scale - width / 2, (r.y + 10) * scale, 0);
    BLF_draw(font, entry.text.c_str(), entry.text.size());
  }
  if (!data.marking) {
    const MenuNode *hover = hotbox_find_node(data.snapshot.menus, data.hover_id);
    if (hover && !hover->reason.empty()) {
      BLF_color4f(font, 1, .8f, .5f, 1);
      BLF_position(font, 12 * scale, 12 * scale, 0);
      BLF_draw(font, hover->reason.c_str(), hover->reason.size());
    }
  }
  GPU_blend(GPU_BLEND_NONE);
}
}  // namespace blender::axismeld

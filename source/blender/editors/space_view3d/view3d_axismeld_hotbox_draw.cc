/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cstring>

#include "BLF_api.hh"
#include "DNA_theme_types.h"
#include "GPU_state.hh"
#include "UI_interface_c.hh"
#include "UI_resources.hh"
#include "view3d_axismeld_hotbox_internal.hh"

namespace blender::axismeld {
namespace {
int menu_icon(const MenuNode &node)
{
  if (node.id == "views" || node.value == "views") {
    return ICON_ORIENTATION_GLOBAL;
  }
  if (node.id == "center.recent" || node.value == "center.recent") {
    return ICON_RECOVER_LAST;
  }
  if (node.id == "center.controls" || node.value == "center.controls") {
    return ICON_PREFERENCES;
  }
  if (node.command == "view.wireframe") {
    return ICON_SHADING_WIRE;
  }
  if (node.command == "view.shaded") {
    return ICON_SHADING_SOLID;
  }
  if (node.command == "view.perspective") {
    return ICON_VIEW_PERSPECTIVE;
  }
  if (node.command == "view.side" || node.command == "view.bottom" ||
      node.command == "view.front" || node.command == "view.back" ||
      node.command == "view.top" || node.command == "view.left")
  {
    return ICON_VIEW_ORTHO;
  }
  if (node.command == "selection.vertex_mode") {
    return ICON_VERTEXSEL;
  }
  if (node.command == "selection.edge_mode") {
    return ICON_EDGESEL;
  }
  if (node.command == "selection.face_mode") {
    return ICON_FACESEL;
  }
  return ICON_NONE;
}
}  // namespace

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
  const uiFontStyle &style = ui::style_get_dpi()->widget;
  ui::fontstyle_set(&style);
  const int font = style.uifont_id;
  auto measure = [&](auto &&self, const std::vector<MenuNode> &nodes) -> void {
    for (const MenuNode &node : nodes) {
      data.label_widths[node.id] = BLF_width(font, node.label.c_str(), node.label.size()) /
                                   data.scale + (menu_icon(node) != ICON_NONE ? 20.0f : 0.0f);
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
    int icon = ICON_NONE;
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
                         false,
                         menu_icon(*node)});
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
                         node && node->kind == MenuKind::Separator,
                         node ? menu_icon(*node) : ICON_NONE});
    }
  }
  const float scale = data.scale;
  const uiFontStyle &style = ui::style_get_dpi()->widget;
  ui::fontstyle_set(&style);
  const int font = style.uifont_id;
  const ThemeUI &theme = ui::theme::theme_get()->tui;
  GPU_blend(GPU_BLEND_ALPHA);
  ui::draw_roundbox_corner_set(ui::CNR_ALL);
  for (const Entry &entry : entries) {
    const MenuRect &r = entry.rect;
    const bool selected = entry.selected && !entry.disabled;
    const uiWidgetColors &colors = r.depth > 0 ? theme.wcol_menu_item : theme.wcol_menu;
    const uchar *inner = selected ? colors.inner_sel :
                                   r.depth > 0 ? theme.wcol_menu_back.inner : colors.inner;
    const uchar *outline = selected ? colors.outline_sel : colors.outline;
    float background[4], border[4];
    for (int i = 0; i < 4; i++) {
      background[i] = inner[i] / 255.0f;
      border[i] = outline[i] / 255.0f;
    }
    background[3] *= 1 - data.snapshot.transparency / 100.0f;
    border[3] *= 1 - data.snapshot.transparency / 100.0f;
    const rctf bounds = {
        r.x * scale, (r.x + r.width) * scale, r.y * scale, (r.y + r.height) * scale};
    ui::draw_roundbox_4fv_ex(
        &bounds, background, nullptr, 1.0f, border, scale, colors.roundness * 20 * scale);
    if (entry.separator) {
      float line[4];
      for (int i = 0; i < 4; i++) {
        line[i] = colors.text[i] / 255.0f;
      }
      line[3] *= 0.3f;
      const rctf separator = {(r.x + 6) * scale,
                              (r.x + r.width - 6) * scale,
                              (r.y + 14) * scale,
                              (r.y + 15) * scale};
      ui::draw_roundbox_4fv(&separator, true, 0, line);
    }
  }
  for (const Entry &entry : entries) {
    const MenuRect &r = entry.rect;
    // Alpha is the chosen menu transparency, not permission for obscured menu text to bleed
    // through. Higher-depth rectangles already own these pixels for hit testing.
    const bool occluded = std::any_of(entries.begin(), entries.end(), [&](const Entry &other) {
      const MenuRect &s = other.rect;
      return s.depth > r.depth && r.x < s.x + s.width && r.x + r.width > s.x &&
             r.y < s.y + s.height && r.y + r.height > s.y;
    });
    if (occluded || entry.separator) {
      continue;
    }
    const uiWidgetColors &colors = r.depth > 0 ? theme.wcol_menu_item : theme.wcol_menu;
    uchar color[4];
    std::memcpy(color, entry.selected && !entry.disabled ? colors.text_sel : colors.text, 4);
    // Native menu items retain their theme foreground RGB and halve disabled text alpha.
    if (entry.disabled) {
      color[3] /= 2;
    }
    const float text_width = BLF_width(font, entry.text.c_str(), entry.text.size());
    const float icon_width = entry.icon != ICON_NONE ? 20 * scale : 0;
    const float left = (r.x + r.width / 2) * scale - (text_width + icon_width) / 2;
    if (entry.icon != ICON_NONE) {
      ui::icon_draw_ex(left,
                       (r.y + 6) * scale,
                       entry.icon,
                       1.0f / scale,
                       1.0f,
                       0.0f,
                       color,
                       false,
                       nullptr);
    }
    const rcti text_rect = {int(left + icon_width),
                            int(left + icon_width + text_width + 1),
                            int(r.y * scale),
                            int((r.y + r.height) * scale)};
    const ui::FontStyleDrawParams params{ui::UI_STYLE_TEXT_CENTER, 0, false};
    ui::fontstyle_draw(&style, &text_rect, entry.text.c_str(), entry.text.size(), color, &params);
  }
  if (!data.marking) {
    const MenuNode *hover = hotbox_find_node(data.snapshot.menus, data.hover_id);
    if (hover && !hover->reason.empty()) {
      BLF_color4ubv(font, theme.wcol_menu_back.text);
      BLF_position(font, 12 * scale, 12 * scale, 0);
      BLF_draw(font, hover->reason.c_str(), hover->reason.size());
    }
  }
  GPU_blend(GPU_BLEND_NONE);
}
}  // namespace blender::axismeld

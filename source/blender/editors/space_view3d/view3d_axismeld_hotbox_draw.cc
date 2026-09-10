/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cstring>

#include "BLF_api.hh"
#include "DNA_theme_types.h"
#include "GPU_immediate.hh"
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
      node.command == "view.front" || node.command == "view.back" || node.command == "view.top" ||
      node.command == "view.left")
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
      const bool view_label = node.id.starts_with("views.") && node.kind == MenuKind::Command;
      const std::string_view label = view_label ? hotbox_view_short_label(node.command) :
                                                  node.label;
      data.label_widths[node.id] = BLF_width(font, label.data(), label.size()) / data.scale +
                                   (!view_label && menu_icon(node) != ICON_NONE ? 20.0f : 0.0f);
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
                                 data.marking ? data.origin[0] : data.center[0],
                                 data.marking ? data.origin[1] : data.center[1],
                                 data.open_path,
                                 data.scroll_offsets,
                                 data.label_widths);
  if (data.marking) {
    // Direction labels and Style now share the same ellipse geometry as ordinary menu hits.
    std::erase_if(data.menu_layout.rects, [](const MenuRect &rect) { return rect.depth == 0; });
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
  {
    for (const MenuRect &rect : data.menu_layout.rects) {
      const bool back = rect.id.starts_with("@back:");
      const MenuNode *node = hotbox_find_node(data.snapshot.menus,
                                              back ? rect.id.substr(6) : rect.id);
      const std::string label = rect.direction_label ?
                                    std::string(hotbox_view_short_label(node->command)) :
                                node                           ? node->label :
                                rect.id.ends_with(":previous") ? "<" :
                                                                 ">";
      bool selected = data.hover_id == rect.id && data.hover_depth == rect.depth;
      if (data.marking && rect.direction_label) {
        selected = data.pending_leaf == rect.id;
      }
      if (data.marking && rect.id == "views.style") {
        selected = false;
      }
      entries.push_back({rect,
                         label,
                         selected,
                         !rect.interactive,
                         node && node->kind == MenuKind::Separator,
                         back                 ? ICON_BACK :
                         rect.direction_label ? ICON_NONE :
                         node                 ? menu_icon(*node) :
                                                ICON_NONE});
    }
  }
  const float scale = data.scale;
  const uiFontStyle &style = ui::style_get_dpi()->widget;
  ui::fontstyle_set(&style);
  const int font = style.uifont_id;
  const ThemeUI &theme = ui::theme::theme_get()->tui;
  GPU_blend(GPU_BLEND_ALPHA);
  if (data.active_mouse && (data.pointer_position[0] != data.press_position[0] ||
                            data.pointer_position[1] != data.press_position[1]))
  {
    // An owned gesture, not a menu-center decoration. Draw below all targets so text stays clear.
    const uint pos = GPU_vertformat_attr_add(
        immVertexFormat(), "pos", gpu::VertAttrType::SFLOAT_32_32);
    float viewport[4];
    GPU_viewport_size_get_f(viewport);
    immBindBuiltinProgram(GPU_SHADER_3D_POLYLINE_UNIFORM_COLOR);
    immUniform2fv("viewportSize", &viewport[2]);
    immUniform1f("lineWidth", 1.25f * scale);
    immUniformColor4ubv(theme.wcol_menu.text);
    immBegin(GPU_PRIM_LINES, 2);
    immVertex2f(pos, data.press_position[0] * scale, data.press_position[1] * scale);
    immVertex2f(pos, data.pointer_position[0] * scale, data.pointer_position[1] * scale);
    immEnd();
    immUnbindProgram();
  }
  ui::draw_roundbox_corner_set(ui::CNR_ALL);
  for (const Entry &entry : entries) {
    const MenuRect &r = entry.rect;
    const bool selected = entry.selected && !entry.disabled;
    const uiWidgetColors &colors = r.depth > 0 ? theme.wcol_menu_item : theme.wcol_menu;
    const uchar *inner = selected    ? colors.inner_sel :
                         r.depth > 0 ? theme.wcol_menu_back.inner :
                                       colors.inner;
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
                              (r.y + r.height / 2) * scale,
                              (r.y + r.height / 2 + 1) * scale};
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
                       (r.y + (r.height - 16) / 2) * scale,
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

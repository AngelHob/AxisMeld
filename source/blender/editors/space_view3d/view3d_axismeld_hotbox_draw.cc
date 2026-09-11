/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <algorithm>
#include <cstring>
#include <map>

#include "BLF_api.hh"
#include "DNA_theme_types.h"
#include "GPU_immediate.hh"
#include "GPU_state.hh"
#include "UI_interface_c.hh"
#include "UI_menu_overlay.hh"
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
      const std::string_view label = node.label;
      data.label_widths[node.id] = BLF_width(font, label.data(), label.size()) / data.scale +
                                   (!view_label && menu_icon(node) != ICON_NONE ? 20.0f : 0.0f);
      if (view_label) {
        const auto compact = hotbox_view_short_label(node.command);
        data.label_widths["@compact:" + node.id] = BLF_width(
                                                       font, compact.data(), compact.size()) /
                                                   data.scale;
      }
      self(self, node.children);
    }
  };
  measure(measure, data.snapshot.menus);
}

void hotbox_layout(HotboxVisual &data)
{
  const std::array<float, 2> origin = {data.origin[0], data.origin[1]};
  data.menu_layout = layout_menu(data.snapshot,
                                 data.width,
                                 data.height,
                                 data.center[0],
                                 data.center[1],
                                 data.open_path,
                                 data.scroll_offsets,
                                 data.label_widths,
                                 data.marking ? &origin : nullptr);
}

void hotbox_draw(const bContext *C, const HotboxVisual &data)
{
  struct Entry {
    MenuRect rect;
    std::string text;
    bool selected, disabled, separator, placeholder;
    int icon = ICON_NONE;
  };
  std::vector<Entry> entries;
  {
    for (const MenuRect &rect : data.menu_layout.rects) {
      const bool back = rect.id.starts_with("@back:");
      const MenuNode *node = hotbox_find_node(data.snapshot.menus,
                                              back ? rect.id.substr(6) : rect.id);
      const std::string label = rect.compact_label ?
                                    std::string(hotbox_view_short_label(node->command)) :
                                node                           ? node->label :
                                rect.id.ends_with(":previous") ? "<" :
                                                                 ">";
      bool selected = data.hover_id == rect.id && data.hover_depth == rect.depth;
      if (data.marking && rect.direction_label) {
        selected = data.pending_leaf == rect.id;
      }
      entries.push_back({rect,
                         label,
                         selected,
                         !rect.interactive,
                         node && node->kind == MenuKind::Separator,
                         node && node->kind == MenuKind::Disabled,
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
    if (r.native_menu || r.depth > 0) {
      continue;
    }
    const bool selected = entry.selected && !entry.disabled;
    const uiWidgetColors &colors = theme.wcol_menu;
    const uchar *inner = selected ? colors.inner_sel : colors.inner;
    const uchar *outline = selected ? colors.outline_sel : colors.outline;
    float background[4], border[4];
    for (int i = 0; i < 4; i++) {
      background[i] = inner[i] / 255.0f;
      border[i] = outline[i] / 255.0f;
    }
    if (!selected) {
      /* Lift only the primary idle fill; retain native hover and secondary styling. */
      for (int i = 0; i < 3; i++) {
        background[i] = std::min(background[i] + 0.08f, 1.0f);
      }
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
      continue;
    }
    const float text_width = BLF_width(font, entry.text.c_str(), entry.text.size());
    const float icon_width = entry.icon != ICON_NONE ? 20 * scale : 0;
    const float left = (r.x + r.width / 2) * scale - (text_width + icon_width) / 2;
    // Occlude the label, not its padded button. Otherwise a few covered padding pixels
    // erase an entirely visible parent label. Covered labels must not bleed through a
    // translucent child and make its view name unreadable.
    const float label_height = std::max(float(BLF_height_max(font)),
                                        entry.icon != ICON_NONE ? 16 * scale : 0.0f);
    const float label_bottom = (r.y + r.height / 2) * scale - label_height / 2;
    const bool occluded = std::any_of(entries.begin(), entries.end(), [&](const Entry &other) {
      const MenuRect &s = other.rect;
      return s.depth > r.depth && left < (s.x + s.width) * scale &&
             left + text_width + icon_width > s.x * scale &&
             label_bottom < (s.y + s.height) * scale && label_bottom + label_height > s.y * scale;
    });
    if (occluded) {
      continue;
    }
    uchar color[4];
    std::memcpy(color, entry.selected && !entry.disabled ? colors.text_sel : colors.text, 4);
    // Native menu items retain their theme foreground RGB and halve disabled text alpha.
    if (entry.disabled) {
      color[3] /= 2;
    }
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
    if (entry.placeholder) {
      color[0] = color[1] = color[2] = 0;
      color[3] = 255;
    }
    else if (!selected) {
      color[0] = color[1] = color[2] = 160;
    }
    const rcti text_rect = {int(left + icon_width),
                            int(left + icon_width + text_width + 1),
                            int(r.y * scale),
                            int((r.y + r.height) * scale)};
    const ui::FontStyleDrawParams params{ui::UI_STYLE_TEXT_CENTER, 0, false};
    ui::fontstyle_draw(&style, &text_rect, entry.text.c_str(), entry.text.size(), color, &params);
  }
  // Standalone hotbox entries are separate native blocks. Native submenu and leaf rows
  // stay in one block so their backgrounds remain continuous.
  struct NativeBlock {
    bool standalone;
    std::vector<ui::MenuOverlayItem> items;
  };
  std::map<int, std::vector<NativeBlock>> menu_levels;
  for (const Entry &entry : entries) {
    const MenuRect &r = entry.rect;
    if (r.native_menu || r.depth > 0) {
      const MenuNode *node = hotbox_find_node(data.snapshot.menus, r.id);
      const bool submenu = r.native_menu && node && node->kind == MenuKind::Menu;
      const int icon_only = r.id.starts_with("@scroll:") && r.id.ends_with(":previous") ?
                                ICON_TRIA_UP :
                            r.id.starts_with("@scroll:") && r.id.ends_with(":next") ?
                                ICON_TRIA_DOWN :
                                ICON_NONE;
      auto &blocks = menu_levels[r.depth];
      const bool standalone = r.native_menu_standalone || !r.native_menu;
      if (standalone || blocks.empty() || blocks.back().standalone) {
        blocks.push_back({standalone, {}});
      }
      blocks.back().items.push_back({entry.text,
                                     {int(r.x * scale),
                                      int((r.x + r.width) * scale),
                                      int(r.y * scale),
                                      int((r.y + r.height) * scale)},
                                     entry.selected,
                                     !entry.disabled,
                                     submenu,
                                     icon_only,
                                     r.native_menu ? ICON_NONE : entry.icon,
                                     !r.native_menu,
                                     entry.separator});
    }
  }
  for (const auto &[depth, blocks] : menu_levels) {
    for (const NativeBlock &block : blocks) {
      ui::menu_overlay_draw(C, block.items, true);
    }
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

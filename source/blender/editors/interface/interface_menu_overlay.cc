/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <cmath>

#include "BKE_context.hh"
#include "GPU_matrix.hh"
#include "UI_interface_c.hh"
#include "UI_menu_overlay.hh"
#include "interface_intern.hh"

namespace blender::ui {
void menu_overlay_draw(const bContext *C,
                       const Span<MenuOverlayItem> items,
                       const bool force_opaque)
{
  if (items.is_empty()) {
    return;
  }
  ARegion *region = CTX_wm_region(C);
  if (!region) {
    return;
  }
  // Unattached native blocks are temporary drawing components, not popup handlers.
  // Use the caller's region projection instead of block_begin's window projection.
  Block *block = block_begin(C, nullptr, "AxisMeld Menu Overlay", EmbossType::Pulldown);
  GPU_matrix_projection_get(block->winmat);
  block->aspect = 2.0f / std::abs(region->winx * block->winmat[0][0]);
  block_theme_style_set(block, BLOCK_THEME_STYLE_POPUP);
  Vector<Button *> centered_buttons;
  for (const MenuOverlayItem &item : items) {
    Button *button = item.icon_only ?
                         uiDefIconBut(block,
                                      ButtonType::But,
                                      item.icon_only,
                                      item.rect.xmin,
                                      item.rect.ymin,
                                      item.rect.xmax - item.rect.xmin,
                                      item.rect.ymax - item.rect.ymin,
                                      nullptr,
                                      0,
                                      0,
                                      std::nullopt) :
                     item.submenu ?
                         uiDefIconTextMenuBut(block,
                                              nullptr,
                                              nullptr,
                                              ICON_NONE,
                                              item.label,
                                              item.rect.xmin,
                                              item.rect.ymin,
                                              item.rect.xmax - item.rect.xmin,
                                              item.rect.ymax - item.rect.ymin,
                                              std::nullopt) :
                         uiDefIconTextBut(block,
                                          item.separator ? ButtonType::SeprLine : ButtonType::But,
                                          item.icon,
                                          item.label,
                                          item.rect.xmin,
                                          item.rect.ymin,
                                          item.rect.xmax - item.rect.xmin,
                                          item.rect.ymax - item.rect.ymin,
                                          nullptr,
                                          std::nullopt);
    if (item.centered) {
      centered_buttons.append(button);
    }
    if (item.hovered) {
      button->flag |= UI_HOVER;
    }
    if (!item.enabled) {
      button_disable(button, "");
    }
  }
  block_bounds_set_normal(block, 0);
  block_end(C, block);
  for (Button *button : centered_buttons) {
    button->drawflag &= ~BUT_TEXT_LEFT;
  }
  if (force_opaque) {
    rcti bounds = items.first().rect;
    for (const MenuOverlayItem &item : items) {
      BLI_rcti_union(&bounds, &item.rect);
    }
    // Reuse the native backdrop with a local alpha override, then draw the native rows.
    draw_menu_back(nullptr, block, &bounds, true);
    block->flag &= ~BLOCK_LOOP;
  }
  block_draw(C, block);
  block_free(C, block);
}
}  // namespace blender::ui

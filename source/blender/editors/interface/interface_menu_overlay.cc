/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <cmath>

#include "BKE_context.hh"
#include "DNA_theme_types.h"
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
    const auto apply_state = [&](Button *button) {
      // Native labels/rules never handle input. Keep the normal menu-label theme
      // instead of dimming section headings as unavailable command buttons.
      if (item.separator) { return; }
      if (item.hovered) {
        button->flag |= UI_HOVER;
      }
      if (!item.enabled) {
        button_disable(button, "");
      }
    };
    // One native block owns the backdrop. A separate drawing-only button preserves
    // both the status and semantic icon, including empty status cells between pages.
    const int state_width = !item.icon_only && !item.separator &&
                                    (item.state_column || item.state_icon) ?
                                int(20 * UI_SCALE_FAC) :
                                0;
    if (state_width) {
      Button *state = uiDefIconBut(block,
                                  ButtonType::But,
                                  item.state_icon,
                                  item.rect.xmin,
                                  item.rect.ymin,
                                  state_width,
                                  item.rect.ymax - item.rect.ymin,
                                  nullptr,
                                  0,
                                  0,
                                  std::nullopt);
      apply_state(state);
    }
    const int label_x = item.rect.xmin + state_width;
    const int label_width = item.rect.xmax - label_x;
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
                                              item.icon,
                                              item.label,
                                              label_x,
                                              item.rect.ymin,
                                              label_width,
                                              item.rect.ymax - item.rect.ymin,
                                              std::nullopt) :
                         uiDefIconTextBut(block,
                                          item.separator ? (item.label.is_empty() ? ButtonType::SeprLine :
                                                                                    ButtonType::Label) :
                                                           ButtonType::But,
                                          item.icon,
                                          item.label,
                                          label_x,
                                          item.rect.ymin,
                                          label_width,
                                          item.rect.ymax - item.rect.ymin,
                                          nullptr,
                                          std::nullopt);
    if (item.centered) {
      centered_buttons.append(button);
    }
    apply_state(button);
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

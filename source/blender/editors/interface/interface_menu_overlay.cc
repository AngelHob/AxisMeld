/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include <cmath>

#include "BKE_context.hh"
#include "GPU_matrix.hh"
#include "UI_interface_c.hh"
#include "UI_menu_overlay.hh"
#include "interface_intern.hh"

namespace blender::ui {
void menu_overlay_draw(const bContext *C, const Span<MenuOverlayItem> items)
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
  for (const MenuOverlayItem &item : items) {
    Button *button = uiDefBut(block,
                              ButtonType::But,
                              item.label,
                              item.rect.xmin,
                              item.rect.ymin,
                              item.rect.xmax - item.rect.xmin,
                              item.rect.ymax - item.rect.ymin,
                              nullptr,
                              0,
                              0,
                              std::nullopt);
    if (item.hovered) {
      button->flag |= UI_HOVER;
    }
    if (!item.enabled) {
      button_disable(button, "");
    }
  }
  block_bounds_set_normal(block, 0);
  block_end(C, block);
  block_draw(C, block);
  block_free(C, block);
}
}  // namespace blender::ui

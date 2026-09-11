/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "BLI_rect.hh"
#include "BLI_span.hh"
#include "BLI_string_ref.hh"

namespace blender {
struct bContext;
namespace ui {
struct MenuOverlayItem {
  StringRef label;
  rcti rect;  // Region pixel coordinates, in the caller's pixel-space projection.
  bool hovered;
  bool enabled;
  bool submenu = false;
  int icon_only = 0;  // ICON_NONE; nonzero requests a native icon-only navigation row.
  int icon = 0;       // Optional icon beside the label.
  bool centered = false;
  bool separator = false;
};

/** Draw native menu components without registering blocks or input handlers.
 * The caller owns hit testing, input and lifetime. Rows must form a contiguous menu.
 * force_opaque only overrides this block's backdrop alpha, not the global theme.
 */
void menu_overlay_draw(const bContext *C, Span<MenuOverlayItem> items, bool force_opaque = false);
}  // namespace ui
}  // namespace blender

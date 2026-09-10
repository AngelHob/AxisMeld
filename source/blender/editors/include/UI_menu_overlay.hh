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
};

/** Draw native menu components without registering blocks or input handlers.
 * The caller owns hit testing, input and lifetime. Rows must form a contiguous menu.
 */
void menu_overlay_draw(const bContext *C, Span<MenuOverlayItem> items);
}  // namespace ui
}  // namespace blender

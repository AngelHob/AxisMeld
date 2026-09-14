/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

namespace blender::axismeld {
struct MenuNode;
/** Read-only built-in icon identity; never changes command admission or snapshot data. */
int hotbox_semantic_icon(const MenuNode &node);
}  // namespace blender::axismeld

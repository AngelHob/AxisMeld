/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "AXM_hotbox_menu.hh"
#include "AXM_hotbox_state.hh"

namespace blender {
struct bContext;
struct ScrArea;
struct wmOperator;
struct wmOperatorType;
void VIEW3D_OT_axismeld_hotbox(wmOperatorType *ot);
void VIEW3D_OT_axismeld_hotbox_release_guard(wmOperatorType *ot);
void VIEW3D_OT_axismeld_view(wmOperatorType *ot);
bool axismeld_view_context_poll(bContext *C);
bool axismeld_view_action(bContext *C, wmOperator *op, axismeld::HotboxAction action);
void axismeld_view_cache_free(void *cache);
/* Only AxisMeld-owned topology may retain an incomplete quad's last valid clip volume. */
bool axismeld_boxview_clip_preserve(const ScrArea *area);
}  // namespace blender

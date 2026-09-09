/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "WM_types.hh"
#include <string>

namespace blender {
struct bContext;
/* Copy a fresh Python snapshot; empty on failure, never a previous response. */
std::string axismeld_hotbox_refresh(bContext *C);
/* Caller owns UI lifetime: close-before policy, remove visuals, dispatch, then guard. */
wmOperatorStatus axismeld_hotbox_dispatch(bContext *C, const char *command);
wmOperatorStatus axismeld_hotbox_setting(bContext *C, const char *setting, const char *value);
wmOperatorStatus axismeld_hotbox_guard_begin(
    bContext *C, int trigger_type, int mouse_type, bool trigger_down, bool mouse_down);
}  // namespace blender

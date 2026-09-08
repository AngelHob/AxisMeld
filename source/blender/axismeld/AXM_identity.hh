/* SPDX-FileCopyrightText: 2026 AxisMeld contributors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <string>
#include <string_view>

namespace blender::axismeld {

std::string_view product_name();
std::string_view project_version();
std::string version_line(std::string_view blender_version);

}  // namespace blender::axismeld

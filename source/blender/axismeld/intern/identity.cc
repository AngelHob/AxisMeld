/* SPDX-FileCopyrightText: 2026 AxisMeld contributors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "AXM_identity.hh"

namespace blender::axismeld {

std::string_view product_name()
{
  return "AxisMeld";
}

std::string_view project_version()
{
  return "0.1.0-dev";
}

std::string version_line(const std::string_view blender_version)
{
  return std::string(product_name()) + " " + std::string(project_version()) +
         " (based on Blender " + std::string(blender_version) + ")";
}

}  // namespace blender::axismeld

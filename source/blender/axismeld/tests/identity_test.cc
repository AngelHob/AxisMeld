/* SPDX-FileCopyrightText: 2026 AxisMeld contributors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "AXM_identity.hh"
#include "testing/testing.h"

namespace blender::axismeld::tests {

TEST(axismeld_identity, ProductConstants)
{
  EXPECT_EQ(product_name(), "AxisMeld");
  EXPECT_EQ(project_version(), "0.1.0-dev");
}

TEST(axismeld_identity, CombinedVersionLine)
{
  EXPECT_EQ(version_line("5.3.0 Alpha"), "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Alpha)");
}

}  // namespace blender::axismeld::tests

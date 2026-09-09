/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "AXM_transform_axis.hh"
#include "testing/testing.h"

namespace blender::axismeld::tests {
TEST(axismeld_transform_axis, RetainsSelectionWithinContext)
{
  TransformAxisState state{};
  EXPECT_EQ(state.axis(), -1);
  state.update_context(12, 0, 1);
  state.select(0);
  state.update_context(12, 0, 1);
  EXPECT_EQ(state.axis(), 0);
  state.select(2);
  EXPECT_EQ(state.axis(), 2);
  state.clear();
  EXPECT_EQ(state.axis(), -1);
}
TEST(axismeld_transform_axis, ClearsWhenContextChanges)
{
  TransformAxisState state{};
  state.update_context(12, 0, 1);
  state.select(0);
  state.update_context(13, 0, 1);
  EXPECT_EQ(state.axis(), -1);
  state.select(1);
  state.update_context(13, 1, 1);
  EXPECT_EQ(state.axis(), -1);
  state.select(1);
  state.update_context(13, 1, 2);
  EXPECT_EQ(state.axis(), -1);
  state.select(2);
  state.update_context(0, 0, 0);
  EXPECT_EQ(state.axis(), -1);
  state.select(0);
  EXPECT_EQ(state.axis(), -1);
}
TEST(axismeld_transform_axis, InvalidSelectionAndRegionIsolation)
{
  TransformAxisState a{}, b{};
  a.update_context(12, 0, 1);
  b.update_context(12, 0, 1);
  a.select(1);
  EXPECT_EQ(b.axis(), -1);
  a.select(3);
  EXPECT_EQ(a.axis(), -1);
  a.select(-1);
  EXPECT_EQ(a.axis(), -1);
}
}  // namespace blender::axismeld::tests

/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "transform_axismeld_snap.hh"
#include "gtest/gtest.h"
#include <type_traits>

namespace blender::ed::transform::tests {
using Key = AxisMeldSnapKey;
static_assert(std::is_trivial_v<AxisMeldSnapState>);

TEST(axismeld_transform_snap, HeldOrderAndRepeat)
{
  AxisMeldSnapState state{};
  EXPECT_TRUE(state.press(Key::Grid, {15, false, false}));
  EXPECT_EQ(state.active(), Key::Grid);
  EXPECT_FALSE(state.press(Key::Grid, {99, true, true}));
  EXPECT_EQ(state.base.mode, 15);
  EXPECT_TRUE(state.press(Key::Vertex, {}));
  EXPECT_TRUE(state.press(Key::Increment, {}));
  EXPECT_EQ(state.active(), Key::Increment);
  EXPECT_TRUE(state.release(Key::Vertex));
  EXPECT_EQ(state.active(), Key::Increment);
  EXPECT_TRUE(state.release(Key::Increment));
  EXPECT_EQ(state.active(), Key::Grid);
  EXPECT_TRUE(state.release(Key::Grid));
  EXPECT_EQ(state.active(), Key::None);
  EXPECT_FALSE(state.release(Key::Grid));
  EXPECT_EQ(state.base.mode, 15);
}

TEST(axismeld_transform_snap, TemporarySnapNeverOverwritesBase)
{
  AxisMeldSnapState state{};
  state.press(Key::Grid, {15, false, true});
  const auto grid = state.effective(1, 2, 3);
  EXPECT_EQ(grid.mode, 1);
  EXPECT_TRUE(grid.enabled);
  EXPECT_FALSE(grid.invert);
  EXPECT_EQ(state.base.mode, 15);
  EXPECT_FALSE(state.base.enabled);
  EXPECT_TRUE(state.base.invert);
  state.base.invert = false;  // Ctrl release while the letter still owns snapping.
  state.release(Key::Grid);
  EXPECT_FALSE(state.effective(1, 2, 3).enabled);
  EXPECT_FALSE(state.effective(1, 2, 3).invert);
}

TEST(axismeld_transform_snap, IncrementInvertsEffectiveBaseline)
{
  for (const bool enabled : {false, true}) {
    for (const bool invert : {false, true}) {
      AxisMeldSnapState state{};
      state.press(Key::Increment, {15, enabled, invert});
      const auto temporary = state.effective(1, 2, 3);
      EXPECT_EQ(temporary.mode, 3);
      EXPECT_EQ(temporary.enabled, !(enabled != invert));
      EXPECT_FALSE(temporary.invert);
      state.release(Key::Increment);
      EXPECT_EQ(state.effective(1, 2, 3).enabled, enabled);
      EXPECT_EQ(state.effective(1, 2, 3).invert, invert);
    }
  }
}

TEST(axismeld_transform_snap, ModeResetAndCancel)
{
  AxisMeldSnapState state{};
  state.press(Key::Vertex, {15, true, false});
  state.base = {27, false, true};
  EXPECT_EQ(state.effective(1, 2, 3).mode, 2);
  state.clear();
  EXPECT_EQ(state.active(), Key::None);
  EXPECT_EQ(state.effective(1, 2, 3).mode, 27);
  EXPECT_FALSE(state.release(Key::Vertex));
  state.press(Key::Grid, {9, true, false});
  EXPECT_EQ(state.base.mode, 9);
}

}  // namespace blender::ed::transform::tests

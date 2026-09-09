/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <limits>

#include "AXM_hotbox_state.hh"
#include "testing/testing.h"

namespace blender::axismeld::tests {

TEST(axismeld_hotbox_state, ShortTapTogglesExactlyOnce)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(10.0, 0.4));
  EXPECT_EQ(state.release_trigger(10.2), HotboxAction::ToggleQuad);
  EXPECT_EQ(state.release_trigger(10.21), HotboxAction::None);
}

TEST(axismeld_hotbox_state, EqualityAtTapThresholdCountsAsHold)
{
  HotboxState before;
  EXPECT_TRUE(before.begin(0.0, 0.4));
  EXPECT_EQ(before.release_trigger(0.399), HotboxAction::ToggleQuad);

  HotboxState equal;
  EXPECT_TRUE(equal.begin(0.0, 0.4));
  EXPECT_EQ(equal.release_trigger(0.4), HotboxAction::Close);

  HotboxState after;
  EXPECT_TRUE(after.begin(0.0, 0.4));
  EXPECT_EQ(after.release_trigger(0.401), HotboxAction::Close);
}

TEST(axismeld_hotbox_state, RepeatAndActivePressesDoNotStartOrResetTiming)
{
  HotboxState idle;
  EXPECT_FALSE(idle.begin(0.0, 0.4, true));
  EXPECT_EQ(idle.phase(), HotboxPhase::Idle);

  HotboxState state;
  EXPECT_TRUE(state.begin(10.0, 0.4));
  EXPECT_FALSE(state.begin(10.3, 1.0, true));
  EXPECT_FALSE(state.begin(10.35, 1.0));
  EXPECT_EQ(state.release_trigger(10.5), HotboxAction::Close);
}

TEST(axismeld_hotbox_state, MarkingCanCommitBeforeTapThreshold)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.begin_marking();
  EXPECT_EQ(state.phase(), HotboxPhase::Marking);
  state.motion(0.0f, 40.0f, 12.0f);
  EXPECT_EQ(state.candidate(), HotboxAction::Perspective);
  EXPECT_EQ(state.release_mouse(), HotboxAction::Perspective);
  EXPECT_EQ(state.phase(), HotboxPhase::Held);
  EXPECT_EQ(state.release_trigger(0.1), HotboxAction::Close);
}

TEST(axismeld_hotbox_state, DeadZoneGestureConsumesTapEligibility)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.begin_marking();
  state.motion(3.0f, 4.0f, 5.0f);
  EXPECT_EQ(state.candidate(), HotboxAction::None);
  EXPECT_EQ(state.release_mouse(), HotboxAction::None);
  EXPECT_EQ(state.phase(), HotboxPhase::Held);
  EXPECT_EQ(state.release_trigger(0.2), HotboxAction::Close);
}

TEST(axismeld_hotbox_state, TriggerReleaseCancelsUnreleasedMouseCandidate)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.begin_marking();
  state.motion(40.0f, 0.0f, 12.0f);
  EXPECT_EQ(state.release_trigger(0.1), HotboxAction::Close);
  EXPECT_EQ(state.phase(), HotboxPhase::Idle);
  EXPECT_EQ(state.candidate(), HotboxAction::None);
  EXPECT_EQ(state.release_mouse(), HotboxAction::None);
}

TEST(axismeld_hotbox_state, CancelConsumesReleaseAndAllowsFreshRepress)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.cancel();
  EXPECT_EQ(state.phase(), HotboxPhase::Cancelled);
  EXPECT_FALSE(state.begin(0.1, 0.4, true));
  EXPECT_EQ(state.release_trigger(0.2), HotboxAction::None);
  EXPECT_EQ(state.phase(), HotboxPhase::Idle);

  EXPECT_TRUE(state.begin(1.0, 0.4));
  state.cancel();
  EXPECT_TRUE(state.begin(2.0, 0.4));
  EXPECT_EQ(state.release_trigger(2.1), HotboxAction::ToggleQuad);
}

TEST(axismeld_hotbox_state, SeparateMouseGesturesCommitOnceEach)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.begin_marking();
  state.motion(0.0f, 40.0f, 12.0f);
  EXPECT_EQ(state.release_mouse(), HotboxAction::Perspective);
  EXPECT_EQ(state.release_mouse(), HotboxAction::None);
  EXPECT_EQ(state.candidate(), HotboxAction::None);

  state.begin_marking();
  state.motion(40.0f, 0.0f, 12.0f);
  EXPECT_EQ(state.release_mouse(), HotboxAction::Side);
  EXPECT_EQ(state.release_mouse(), HotboxAction::None);
  EXPECT_EQ(state.release_trigger(0.2), HotboxAction::Close);
}

TEST(axismeld_hotbox_state, CardinalDirectionsUseFixedViewMapping)
{
  EXPECT_EQ(hotbox_direction(0.0f, 40.0f, 12.0f), HotboxAction::Perspective);
  EXPECT_EQ(hotbox_direction(40.0f, 0.0f, 12.0f), HotboxAction::Side);
  EXPECT_EQ(hotbox_direction(0.0f, -40.0f, 12.0f), HotboxAction::Front);
  EXPECT_EQ(hotbox_direction(-40.0f, 0.0f, 12.0f), HotboxAction::Top);
}

TEST(axismeld_hotbox_state, DeadZoneAndDiagonalBoundarySelectNothing)
{
  EXPECT_EQ(hotbox_direction(3.0f, 4.0f, 5.0f), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(40.0f, 40.0f, 12.0f), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(-40.0f, 40.0f, 12.0f), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(40.0f, -40.0f, 12.0f), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(-40.0f, -40.0f, 12.0f), HotboxAction::None);
}

TEST(axismeld_hotbox_state, LogicalDeadZoneSupportsDpiScaledCoordinates)
{
  EXPECT_EQ(hotbox_direction(0.0f, 30.0f, 24.0f), HotboxAction::Perspective);
  EXPECT_EQ(hotbox_direction(0.0f, 20.0f, 24.0f), HotboxAction::None);
}

TEST(axismeld_hotbox_state, NonFiniteInputNeverSelectsOrToggles)
{
  const double double_nan = std::numeric_limits<double>::quiet_NaN();
  const double double_inf = std::numeric_limits<double>::infinity();
  const float float_nan = std::numeric_limits<float>::quiet_NaN();
  const float float_inf = std::numeric_limits<float>::infinity();

  HotboxState invalid;
  EXPECT_FALSE(invalid.begin(double_nan, 0.4));
  EXPECT_FALSE(invalid.begin(0.0, double_inf));
  EXPECT_EQ(invalid.phase(), HotboxPhase::Idle);
  EXPECT_EQ(hotbox_direction(float_nan, 40.0f, 12.0f), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(0.0f, float_inf, 12.0f), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(0.0f, 40.0f, float_nan), HotboxAction::None);

  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.advance(double_nan);
  EXPECT_EQ(state.phase(), HotboxPhase::Pending);
  state.begin_marking();
  state.motion(0.0f, 40.0f, 12.0f);
  EXPECT_EQ(state.candidate(), HotboxAction::Perspective);
  state.motion(float_inf, 0.0f, 12.0f);
  EXPECT_EQ(state.candidate(), HotboxAction::None);

  HotboxState release;
  EXPECT_TRUE(release.begin(0.0, 0.4));
  EXPECT_EQ(release.release_trigger(double_nan), HotboxAction::Close);
}

TEST(axismeld_hotbox_state, AdvanceAtThresholdOnlyMovesToHeld)
{
  HotboxState state;
  EXPECT_TRUE(state.begin(0.0, 0.4));
  state.advance(0.399);
  EXPECT_EQ(state.phase(), HotboxPhase::Pending);
  EXPECT_EQ(state.candidate(), HotboxAction::None);
  state.advance(0.4);
  EXPECT_EQ(state.phase(), HotboxPhase::Held);
  EXPECT_EQ(state.candidate(), HotboxAction::None);
  EXPECT_EQ(state.release_trigger(0.4), HotboxAction::Close);
}

}  // namespace blender::axismeld::tests

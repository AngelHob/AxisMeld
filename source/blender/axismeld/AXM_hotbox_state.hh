/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <cmath>

namespace blender::axismeld {

enum class HotboxPhase { Idle, Pending, Held, Marking, Cancelled };
enum class HotboxAction { None, ToggleQuad, Perspective, Side, Front, Top, Close };

inline HotboxAction hotbox_direction(const float dx, const float dy, const float dead_zone)
{
  if (!std::isfinite(dx) || !std::isfinite(dy) || !std::isfinite(dead_zone) || dead_zone < 0.0f) {
    return HotboxAction::None;
  }

  if (std::hypot(dx, dy) <= dead_zone) {
    return HotboxAction::None;
  }

  const float abs_x = std::fabs(dx);
  const float abs_y = std::fabs(dy);
  if (abs_x == abs_y) {
    return HotboxAction::None;
  }
  if (abs_x > abs_y) {
    return dx > 0.0f ? HotboxAction::Side : HotboxAction::Top;
  }
  return dy > 0.0f ? HotboxAction::Perspective : HotboxAction::Front;
}

class HotboxState {
 private:
  HotboxPhase phase_ = HotboxPhase::Idle;
  HotboxAction candidate_ = HotboxAction::None;
  double start_time_ = 0.0;
  double tap_seconds_ = 0.0;

 public:
  bool begin(const double now, const double tap_seconds, const bool is_repeat = false)
  {
    if (is_repeat || (phase_ != HotboxPhase::Idle && phase_ != HotboxPhase::Cancelled) ||
        !std::isfinite(now) || !std::isfinite(tap_seconds) || tap_seconds < 0.0)
    {
      return false;
    }

    phase_ = HotboxPhase::Pending;
    candidate_ = HotboxAction::None;
    start_time_ = now;
    tap_seconds_ = tap_seconds;
    return true;
  }
  void advance(const double now)
  {
    if (phase_ == HotboxPhase::Pending && std::isfinite(now) && now >= start_time_ &&
        now - start_time_ >= tap_seconds_)
    {
      phase_ = HotboxPhase::Held;
    }
  }
  void begin_marking()
  {
    if (phase_ == HotboxPhase::Pending || phase_ == HotboxPhase::Held) {
      phase_ = HotboxPhase::Marking;
      candidate_ = HotboxAction::None;
    }
  }
  void motion(const float dx, const float dy, const float dead_zone)
  {
    if (phase_ == HotboxPhase::Marking) {
      candidate_ = hotbox_direction(dx, dy, dead_zone);
    }
  }
  HotboxAction release_mouse()
  {
    if (phase_ != HotboxPhase::Marking) {
      return HotboxAction::None;
    }

    const HotboxAction action = candidate_;
    candidate_ = HotboxAction::None;
    phase_ = HotboxPhase::Held;
    return action;
  }
  HotboxAction release_trigger(const double now)
  {
    if (phase_ == HotboxPhase::Idle) {
      return HotboxAction::None;
    }
    if (phase_ == HotboxPhase::Cancelled) {
      phase_ = HotboxPhase::Idle;
      candidate_ = HotboxAction::None;
      return HotboxAction::None;
    }

    const bool is_tap = phase_ == HotboxPhase::Pending && std::isfinite(now) &&
                        now >= start_time_ && now - start_time_ < tap_seconds_;
    phase_ = HotboxPhase::Idle;
    candidate_ = HotboxAction::None;
    return is_tap ? HotboxAction::ToggleQuad : HotboxAction::Close;
  }
  void cancel()
  {
    candidate_ = HotboxAction::None;
    if (phase_ != HotboxPhase::Idle) {
      phase_ = HotboxPhase::Cancelled;
    }
  }
  HotboxPhase phase() const
  {
    return phase_;
  }
  HotboxAction candidate() const
  {
    return candidate_;
  }
};

}  // namespace blender::axismeld

/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

namespace blender::axismeld {

/** Transient state owned by one viewport gizmo group. Zero initialization means unarmed. */
struct TransformAxisState {
 private:
  unsigned int object_;
  int mode_;
  int tool_;
  int selected_;

 public:
  void clear()
  {
    selected_ = 0;
  }
  void update_context(const unsigned int object, const int mode, const int tool)
  {
    if (object != object_ || mode != mode_ || tool != tool_ || object == 0 || tool == 0) {
      clear();
    }
    object_ = object;
    mode_ = mode;
    tool_ = tool;
  }
  void select(const int axis)
  {
    selected_ = object_ != 0 && tool_ != 0 && axis >= 0 && axis < 3 ? axis + 1 : 0;
  }
  int axis() const
  {
    return selected_ - 1;
  }
};

}  // namespace blender::axismeld

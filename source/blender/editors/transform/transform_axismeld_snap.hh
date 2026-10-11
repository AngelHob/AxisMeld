/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

namespace blender {
struct wmEvent;
}

namespace blender::ed::transform {

enum class AxisMeldSnapKey { None, Grid, Vertex, Increment };

struct AxisMeldSnapSettings {
  int mode;
  bool enabled;
  bool invert;
};

/* TransInfo uses MEM_new_zeroed: preserve a trivial, zero-initializable member. */
struct AxisMeldSnapState {
  bool enabled;
  bool mode_reset_pending;
  AxisMeldSnapSettings base;
  AxisMeldSnapKey keys[3];
  int size;

  AxisMeldSnapKey active() const
  {
    return size ? keys[size - 1] : AxisMeldSnapKey::None;
  }
  bool held(const AxisMeldSnapKey key) const
  {
    for (int i = 0; i < size; i++) {
      if (keys[i] == key) {
        return true;
      }
    }
    return false;
  }
  bool press(const AxisMeldSnapKey key, const AxisMeldSnapSettings current)
  {
    if (key == AxisMeldSnapKey::None || held(key)) {
      return false;
    }
    if (size == 0) {
      base = current;
    }
    keys[size++] = key;
    return true;
  }
  bool release(const AxisMeldSnapKey key)
  {
    for (int i = 0; i < size; i++) {
      if (keys[i] == key) {
        for (int j = i + 1; j < size; j++) {
          keys[j - 1] = keys[j];
        }
        size--;
        return true;
      }
    }
    return false;
  }
  void clear()
  {
    size = 0;
    mode_reset_pending = false;
  }
  AxisMeldSnapSettings effective(const int grid, const int vertex, const int increment) const
  {
    switch (active()) {
      case AxisMeldSnapKey::Grid:
        return {grid, true, false};
      case AxisMeldSnapKey::Vertex:
        return {vertex, true, false};
      case AxisMeldSnapKey::Increment:
        return {increment, !(base.enabled != base.invert), false};
      case AxisMeldSnapKey::None:
        return base;
    }
    return base;
  }
};

struct TransInfo;
void axismeld_transform_snap_init(TransInfo *t, const wmEvent *event);
bool axismeld_transform_snap_event(TransInfo *t, const wmEvent *event);
void axismeld_transform_snap_after_event(TransInfo *t);
void axismeld_transform_snap_finish(TransInfo *t);

}  // namespace blender::ed::transform

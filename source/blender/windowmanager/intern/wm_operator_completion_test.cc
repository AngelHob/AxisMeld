/* SPDX-FileCopyrightText: 2026 AxisMeld Authors
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "DNA_windowmanager_types.h"
#include "MEM_guardedalloc.h"
#include "WM_api.hh"
#include "testing/testing.h"

namespace blender::tests {
struct CompletionCounts {
  int finished = 0, cancelled = 0, freed = 0;
};
static void complete(bContext *, void *data, bool finished)
{
  auto &counts = *static_cast<CompletionCounts *>(data);
  (finished ? counts.finished : counts.cancelled)++;
}
static void release(void *data)
{
  static_cast<CompletionCounts *>(data)->freed++;
}
TEST(wm_operator_completion, TerminalCallbackRunsOnceAndDoesNotSurviveRedo)
{
  wmOperator op;
  CompletionCounts counts;
  EXPECT_TRUE(WM_operator_completion_callback_set(&op, complete, &counts, release));
  EXPECT_FALSE(WM_operator_completion_callback_set(&op, complete, &counts, release));
  WM_operator_completion_callback_call(nullptr, &op, true);
  WM_operator_completion_callback_call(nullptr, &op, false);
  EXPECT_EQ(counts.finished, 1);
  EXPECT_EQ(counts.cancelled, 0);
  EXPECT_EQ(counts.freed, 1);
}
TEST(wm_operator_completion, CancelAndContextlessFreeHaveDifferentSemantics)
{
  CompletionCounts counts;
  wmOperator *cancelled = MEM_new<wmOperator>(__func__);
  EXPECT_TRUE(WM_operator_completion_callback_set(cancelled, complete, &counts, release));
  WM_operator_completion_callback_call(nullptr, cancelled, false);
  WM_operator_free(cancelled);
  EXPECT_EQ(counts.cancelled, 1);
  EXPECT_EQ(counts.freed, 1);
  wmOperator *abandoned = MEM_new<wmOperator>(__func__);
  EXPECT_TRUE(WM_operator_completion_callback_set(abandoned, complete, &counts, release));
  WM_operator_free(abandoned);
  EXPECT_EQ(counts.cancelled, 1);
  EXPECT_EQ(counts.finished, 0);
  EXPECT_EQ(counts.freed, 2);
}
}  // namespace blender::tests

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure session-history behavior; live dispatch/settings are covered by release suite."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'modules'))
from axismeld import hotbox_runtime


class RecentCommandsTest(unittest.TestCase):
    def test_session_history_is_newest_first_unique_and_copy_safe(self):
        self.assertTrue(hasattr(hotbox_runtime, 'RecentCommands'), 'session history is missing')
        recent = hotbox_runtime.RecentCommands()
        recent.record('view.front')
        recent.record('view.top')
        recent.record('view.front')
        self.assertEqual(recent.items(), ('view.front', 'view.top'))
        self.assertEqual(hotbox_runtime.RecentCommands().items(), ())

    def test_only_supported_replayable_semantics_can_enter_history(self):
        self.assertTrue(hasattr(hotbox_runtime, 'RecentCommands'), 'session history is missing')
        recent = hotbox_runtime.RecentCommands()
        for command in ('hotbox.open', 'style', 'wm.open_mainfile', 'view.orbit',
                        'view.pan', 'tool.select', '', '../private/file.blend', None):
            recent.record(command)
        self.assertEqual(recent.items(), ())
        recent.record('transform.move')
        self.assertEqual(recent.items(), ('transform.move',))

    def test_ten_item_limit_discards_oldest_and_replaying_promotes(self):
        self.assertTrue(hasattr(hotbox_runtime, 'RecentCommands'), 'session history is missing')
        recent = hotbox_runtime.RecentCommands()
        commands = ('view.perspective', 'view.side', 'view.bottom', 'view.front',
                    'view.back', 'view.top', 'view.left', 'view.focus_selected',
                    'view.frame_all', 'view.wireframe', 'view.shaded')
        for command in commands:
            recent.record(command)
        self.assertEqual(recent.items(), tuple(reversed(commands[1:])))
        recent.record('view.front')
        self.assertEqual(recent.items()[0], 'view.front')
        self.assertEqual(len(recent.items()), 10)


if __name__ == '__main__':
    unittest.main()

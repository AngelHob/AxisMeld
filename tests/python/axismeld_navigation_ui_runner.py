# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run only navigation acceptance in a disposable hidden GUI process."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--blender', required=True)
parser.add_argument('--suite', choices=('navigation', 'view-lock'), default='navigation')
args = parser.parse_args()
script, marker = ('axismeld_view_lock_events.py', b'AXISMELD_VIEW_LOCK_EVENTS_PASS') if (
    args.suite == 'view-lock') else ('axismeld_navigation_events.py', b'AXISMELD_NAVIGATION_EVENTS_PASS')
startup = None
if sys.platform == 'win32':
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
with tempfile.TemporaryDirectory(prefix='axismeld-navigation-') as directory:
    env = os.environ.copy()
    env['BLENDER_USER_CONFIG'] = directory
    env['TEMP'] = env['TMP'] = env['TMPDIR'] = directory
    env['AXISMELD_TEST_ROOT'] = directory
    result = subprocess.run(
        [args.blender, '--factory-startup', '--enable-event-simulate', '--python-exit-code', '1',
         '--python', str(Path(__file__).with_name(script))],
        env=env, startupinfo=startup, capture_output=True, timeout=240)
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    if result.returncode or marker not in result.stdout:
        raise SystemExit(result.returncode or 1)
    if b'Traceback (most recent call last):' in result.stdout + result.stderr:
        raise SystemExit('Python traceback reported during navigation acceptance')

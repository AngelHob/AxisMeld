# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Launch an isolated, hidden GUI test process; leave user sessions/configuration untouched."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--blender', required=True)
args = parser.parse_args()
startup = None
if sys.platform == 'win32':
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
with tempfile.TemporaryDirectory(prefix='axismeld-ui-') as directory:
    env = os.environ.copy()
    env['BLENDER_USER_CONFIG'] = directory
    env['TEMP'] = env['TMP'] = env['TMPDIR'] = directory
    env['AXISMELD_TEST_ROOT'] = directory
    result = subprocess.run(
        [args.blender, '--factory-startup', '--enable-event-simulate', '--python-exit-code', '1', '--python',
         str(Path(__file__).with_name('axismeld_manipulator_events.py'))],
        env=env, startupinfo=startup, capture_output=True, timeout=180)
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    if result.returncode or b'AXISMELD_MANIPULATOR_EVENTS_PASS' not in result.stdout:
        raise SystemExit(result.returncode or 1)

# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run native hotbox acceptance in a disposable hidden GUI process."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--blender', required=True)
parser.add_argument('--artifacts', help='Optional directory for isolated factory-scene screenshots')
args = parser.parse_args()
startup = None
if sys.platform == 'win32':
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
with tempfile.TemporaryDirectory(prefix='axismeld-hotbox-') as directory:
    env = os.environ.copy()
    env['BLENDER_USER_CONFIG'] = directory
    env['TEMP'] = env['TMP'] = env['TMPDIR'] = directory
    env['AXISMELD_TEST_ROOT'] = directory
    if args.artifacts:
        artifacts = Path(args.artifacts).resolve()
        artifacts.mkdir(parents=True, exist_ok=True)
        env['AXISMELD_TEST_ARTIFACTS'] = str(artifacts)
    result = subprocess.run(
        [args.blender, '--factory-startup', '--enable-event-simulate', '--python-exit-code', '1',
         '--python', str(Path(__file__).with_name('axismeld_hotbox_events.py'))],
        env=env, startupinfo=startup, capture_output=True, timeout=240)
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    if result.returncode or b'AXISMELD_HOTBOX_EVENTS_PASS' not in result.stdout:
        raise SystemExit(result.returncode or 1)
    if b"empty keymap 'AxisMeld Hotbox'" in result.stdout + result.stderr:
        raise SystemExit('Empty optional hotbox keymap must not warn on normal input')
    if b'Traceback (most recent call last):' in result.stdout + result.stderr:
        raise SystemExit('Python traceback reported during hotbox or Keymap preferences draw')

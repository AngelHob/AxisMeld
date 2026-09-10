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
parser.add_argument('--suite', choices=('hotbox', 'menus', 'native-style', 'mappings', 'release', 'release-cross-window', 'profiles', 'selection'), default='hotbox')
args = parser.parse_args()
suite_script, pass_marker = {
    'hotbox': ('axismeld_hotbox_events.py', b'AXISMELD_HOTBOX_EVENTS_PASS'),
    'menus': ('axismeld_hotbox_menu_events.py', b'AXISMELD_HOTBOX_MENU_EVENTS_PASS'),
    'native-style': ('axismeld_hotbox_native_style_events.py', b'AXISMELD_HOTBOX_NATIVE_STYLE_PASS'),
    'mappings': ('axismeld_hotbox_native_style_events.py', b'AXISMELD_HOTBOX_MAPPING_LISTS_PASS'),
    'release': ('axismeld_hotbox_release_events.py', b'AXISMELD_HOTBOX_RELEASE_EVENTS_PASS'),
    'release-cross-window': ('axismeld_hotbox_release_events.py', b'AXISMELD_HOTBOX_CROSS_WINDOW_PASS'),
    'profiles': ('axismeld_hotbox_profiles_blender.py', b'AXISMELD_HOTBOX_PROFILES_PASS'),
    'selection': ('axismeld_selection_events.py', b'AXISMELD_SELECTION_EVENTS_PASS'),
}[args.suite]
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
    env['AXISMELD_TEST_SUITE'] = args.suite
    if args.artifacts:
        artifacts = Path(args.artifacts).resolve()
        artifacts.mkdir(parents=True, exist_ok=True)
        env['AXISMELD_TEST_ARTIFACTS'] = str(artifacts)
    blender_args = [args.blender, '--factory-startup']
    if args.suite == 'profiles':
        blender_args.append('--background')
    else:
        blender_args.append('--enable-event-simulate')
    result = subprocess.run(
        [*blender_args, '--python-exit-code', '1',
         '--python', str(Path(__file__).with_name(suite_script))],
        env=env, startupinfo=startup, capture_output=True, timeout=240)
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    if result.returncode or pass_marker not in result.stdout:
        raise SystemExit(result.returncode or 1)
    if b"empty keymap 'AxisMeld Hotbox'" in result.stdout + result.stderr:
        raise SystemExit('Empty optional hotbox keymap must not warn on normal input')
    if b'Traceback (most recent call last):' in result.stdout + result.stderr:
        raise SystemExit('Python traceback reported during hotbox or Keymap preferences draw')

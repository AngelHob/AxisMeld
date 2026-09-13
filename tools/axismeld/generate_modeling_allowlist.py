# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generate the explicit native M3 allowlist; --check fails on source drift."""
from pathlib import Path
import argparse
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'scripts/modules'))
from axismeld.modeling_registry import SPECS

parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
target = root / 'source/blender/editors/space_view3d/view3d_axismeld_modeling_commands.inc'
expected = ('/* Generated from the trusted M3 registry; no prefix or arbitrary operator admission. */\n' +
            ''.join('"' + identifier + '",\n' for identifier in sorted(SPECS)))
if args.check:
    if not target.exists() or target.read_text(encoding='utf8') != expected:
        raise SystemExit('Native M3 allowlist is stale')
else:
    target.write_text(expected, encoding='utf8')
print(f'Native M3 allowlist: {len(SPECS)} explicit commands')

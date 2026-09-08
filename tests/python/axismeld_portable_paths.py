# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import pathlib
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("--blender", required=True)
args = parser.parse_args()

expression = "import bpy; print('AXISMELD_CONFIG=' + bpy.utils.user_resource('CONFIG'))"
result = subprocess.run(
    [args.blender, "--background", "--factory-startup", "--python-expr", expression],
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
line = next(line for line in result.stdout.splitlines() if line.startswith("AXISMELD_CONFIG="))
config_path = pathlib.Path(line.split("=", 1)[1]).resolve()
expected_root = (pathlib.Path(args.blender).resolve().parent / "portable").resolve()
assert config_path.is_relative_to(expected_root), (config_path, expected_root)

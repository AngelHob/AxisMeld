# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import re
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("--blender", required=True)
args = parser.parse_args()

result = subprocess.run(
    [args.blender, "--version"],
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
first_line = result.stdout.splitlines()[0]
assert re.fullmatch(
    r"AxisMeld 0\.1\.0-dev \(based on Blender \d+\.\d+\.\d+(?: [A-Za-z]+)?\)",
    first_line,
), first_line

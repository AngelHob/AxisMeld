# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import re
import subprocess


VERSION_LINE_PATTERN = re.compile(
    r"AxisMeld 0\.1\.0-dev \(based on Blender \d+\.\d+\.\d+"
    r"(?: (?:Alpha|Beta|Release Candidate|LTS))?\)"
)


for valid_line in (
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0)",
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Alpha)",
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Beta)",
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Release Candidate)",
    "AxisMeld 0.1.0-dev (based on Blender 4.5.1 LTS)",
):
    assert VERSION_LINE_PATTERN.fullmatch(valid_line), valid_line

for invalid_line in (
    "AxisMeld 0.1.0-dev (based on Blender 5.3)",
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Preview)",
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Release)",
    "AxisMeld 0.1.0-dev (based on Blender 5.3.0 LTS extra)",
):
    assert not VERSION_LINE_PATTERN.fullmatch(invalid_line), invalid_line


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
assert VERSION_LINE_PATTERN.fullmatch(first_line), first_line

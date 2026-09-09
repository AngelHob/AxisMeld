# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Dispatch-only timings: not physical input latency, GPU frame time or a stutter fix claim."""
import json
import statistics
import time
import bpy

area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')
tools = [('transform.move', 'builtin.move'), ('transform.rotate', 'builtin.rotate'),
         ('transform.scale', 'builtin.scale')]
report = {}
with bpy.context.temp_override(area=area, region=region):
    for label in ('native', 'adapter'):
        samples = []
        for i in range(101):
            command, tool = tools[i % 3]
            start = time.perf_counter_ns()
            if label == 'native':
                bpy.ops.wm.tool_set_by_id(name=tool, cycle=False)
            else:
                bpy.ops.axismeld.command(command=command)
            samples.append((time.perf_counter_ns() - start) / 1e6)
        warm = sorted(samples[1:])
        report[label] = {'first_ms': samples[0], 'median_ms': statistics.median(warm),
                         'p95_ms': warm[94], 'max_ms': max(warm)}
report['scope'] = 'sequential native then adapter dispatch; shared caches; no event-to-frame measurement'
print('AXISMELD_INPUT_BENCHMARK ' + json.dumps(report), flush=True)

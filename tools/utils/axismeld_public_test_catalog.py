# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export technical manual cases, never personal cloud progress, for GitHub Pages."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
# Keep obsolete acceptance instructions discoverable without asking visitors to
# verify superseded application-bar, Deform/Generate or component-root layouts.
SUPERSEDED = {
    'MB-01', 'MB-02', 'MB-05', 'MB-19', 'MB-23',
    'MB-28', 'MB-29', 'MB-31', 'MB-32', 'MB-33', 'MB-34', 'MB-35',
}


def public_text(text):
    text = text.replace('`', '').replace('**', '')
    text = re.sub(r'(?<![A-Za-z])[A-Za-z]:[/\\][^\s，；。|）)]+', '对应历史构建目录', text)
    return re.sub(r'https?://[^\s]*chatgpt\.site[^\s]*', '私人测试记录入口', text)


def build():
    source = ROOT / 'docs/compatibility/2026-09-14-manual-test-ledger.md'
    rows, group = [], ''
    for line in source.read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            group = line[3:]
        if not re.match(r'^\| [A-Z][A-Z0-9]*-\d+ \|', line):
            continue
        identifier, steps, expected, state = [part.strip() for part in line.strip('|').split('|')]
        rows.append(dict(id=identifier, title=public_text(steps), group=public_text(group),
                         steps=[public_text(steps)], expected=[public_text(expected)],
                         superseded=identifier in SUPERSEDED,
                         maintainerStatus='tested' if state.startswith('已测试') else 'pending'))
    assert rows and len(rows) == len({row['id'] for row in rows})
    for row in rows:
        row['isNew'] = row['group'] == rows[-1]['group']
    output = json.dumps(dict(schemaVersion=1, items=rows), ensure_ascii=False, indent=2) + '\n'
    if re.search(r'(?<![A-Za-z])[A-Za-z]:[/\\]|chatgpt\.site|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', output):
        raise ValueError('Public test catalog contains a private path or account reference')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'tools/testing_site/catalog.json'
    data = build()
    if args.check:
        if not path.is_file() or path.read_text(encoding='utf-8') != data:
            raise SystemExit('Public test catalog is outdated')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
    rows = json.loads(data)['items']
    print(json.dumps(dict(count=len(rows), historicalTested=sum(r['maintainerStatus']=='tested' for r in rows),
                          new=sum(r['isNew'] for r in rows), checked=args.check)))

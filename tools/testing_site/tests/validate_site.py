#!/usr/bin/env python3
"""Validate only public portal source data; never read the private test ledger."""
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8-sig"))
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8-sig"))
    assert catalog["schemaVersion"] == config["schemaVersion"] == 1
    assert config["buildId"] and config["sourceBranch"]
    items = catalog["items"]
    assert items, "The public test catalog must not be empty."
    seen = set()
    for item in items:
        assert re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", item["id"]), item
        assert item["id"] not in seen, item["id"]
        seen.add(item["id"])
        assert isinstance(item["title"], str) and item["title"]
        assert isinstance(item["group"], str) and item["group"]
        for field in ("steps", "expected"):
            assert isinstance(item[field], list) and item[field], (item["id"], field)
            assert all(isinstance(value, str) and value for value in item[field])
        assert set(item) <= {"id", "title", "group", "steps", "expected", "isNew", "superseded", "maintainerStatus"}, item["id"]
        assert item.get("maintainerStatus") in {None, "pending", "untested", "tested", "passed", "failed"}
    public_text = json.dumps([catalog, config], ensure_ascii=False)
    for pattern in (r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", r"file://", r"chatgpt\.site", r"localhost", r"127\.0\.0\.1", r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_", r"Bearer\s+[A-Za-z0-9_-]{16,}"):
        assert not re.search(pattern, public_text, re.I), f"Private/local value in public payload: {pattern}"
    for key in ("repoUrl", "releaseUrl"):
        if config.get(key):
            url = urlparse(config[key])
            assert url.scheme == "https" and url.netloc == "github.com", key
    assert config["feedback"]["mode"] in {"github", "external", "disabled"}
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assets = re.findall(r'(?:src|href)="(\./[^"]+)"', html)
    for asset in assets:
        assert (ROOT / asset).exists(), asset
    assert "https://" not in html and "http://" not in html, "Outbound links must come from the checked config."
    app = (ROOT / "app.mjs").read_text(encoding="utf-8")
    assert "innerHTML" not in app and "insertAdjacentHTML" not in app
    assert "PAGE_SIZE = 50" in app
    print(json.dumps({"result": "passed", "items": len(items), "unique_ids": len(seen), "recent": sum(i.get("isNew", False) for i in items), "historical": sum(i.get("superseded", False) for i in items), "historically_tested": sum(i.get("maintainerStatus") == "tested" for i in items), "relative_assets": len(assets)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

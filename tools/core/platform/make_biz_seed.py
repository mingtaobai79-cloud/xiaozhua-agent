#!/usr/bin/env python3
"""给 CHIT-extra 的 biz 构件造一个最小 interfaces.json，喂给 rebuild_surfaces。"""
import json
from pathlib import Path

root = Path("<MAVEN_REPO>-extra")
sources = {}
for d in sorted(root.iterdir()):
    if not d.is_dir():
        continue
    js = sorted(d.rglob("*.jar"))
    if not js:
        continue
    sources[d.name] = {"jar": js[-1].name, "file": str(js[-1])}

out = {"sources": sources, "classes": {}, "method_index": {}}
p = Path("<SEEYON_AGENT_ROOT>/docs/audit/artifacts/extension-surface-20261029/biz-seed.json")
p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(sources)} 个构件 → {p}")
for k, v in list(sources.items())[:5]:
    print(f"  {k}: {v['jar']}")

#!/usr/bin/env python3
"""抽出自定义微流程可调用的服务/方法清单，带依赖标注。

自定义微流程的「自定义服务节点」链路是：选应用 → 选服务 → 选方法 → 加载出入参。
平台返回的候选就是注册在册的 AppService。本脚本把本地反编译面里的 AppService
摊平成可检索索引，并给每个方法标上**来自哪个构件（jar + 版本）** —— 这就是依赖坐标。

用法：
    python tools/build_app_service_index.py --evidence docs/audit/artifacts/extension-surface-20261029
    python tools/build_app_service_index.py --check

输出 TSV（第二列是构件 jar，可据此推 groupId:artifactId:version）：
    com.x.YAppService<TAB>app-y-facade-5.3.295.jar
    com.x.YAppService#doIt(com.x.Req):SingleResponse<Long><TAB>app-y-facade-5.3.295.jar
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "audit" / "reference" / "svc-app-service.txt.gz"


def _types(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return ",".join((x.get("type", "") if isinstance(x, dict) else str(x)) for x in v)
    return ""


def build(evidence: Path) -> tuple[list[str], int, int]:
    ij = evidence / "interfaces.json"
    classes = json.loads(ij.read_text(encoding="utf-8"))["classes"] if ij.exists() else {}
    rows: list[str] = []
    seen: set[str] = set()
    dep_of: dict[str, str] = {}
    for bd in sorted(evidence.glob("batch*")):
        for f in sorted(bd.glob("*.json")):
            if f.name.startswith("_"):
                continue
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(obj, dict) or "classes" not in obj:
                continue
            jar = obj.get("jar") or obj.get("jar_path_hint") or f.stem
            recs = obj["classes"]
            if isinstance(recs, dict):
                recs = list(recs.values())
            for r in recs:
                if not isinstance(r, dict):
                    continue
                e = r.get("entry", "")
                if not e.endswith(".class"):
                    continue
                fq = e[:-6].replace("/", ".")
                if fq.endswith("AppService"):
                    dep_of.setdefault(fq, jar)
    for fq, jar in sorted(dep_of.items()):
        if fq in seen:
            continue
        seen.add(fq)
        rows.append(f"{fq}\t{jar}")
        for m in classes.get(fq, {}).get("methods", []):
            rows.append(f"{fq}#{m['name']}({_types(m.get('args'))}):{m.get('returns','')}\t{jar}")
    return rows, len(dep_of), len({j for j in dep_of.values()})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="建自定义微流程可用服务索引")
    ap.add_argument("--evidence", default=str(ROOT / "docs/audit/artifacts/extension-surface-20261029"))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    ev = Path(a.evidence)
    if not ev.exists():
        print(f"[x] 证据目录不存在: {ev}\n    先跑 python tools/regen_evidence.py", file=sys.stderr)
        return 2
    rows, n_cls, n_dep = build(ev)
    print(f"[*] AppService {n_cls} 个 / 依赖构件 {n_dep} 个 / 索引 {len(rows)} 行")
    if a.check:
        return 0
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wb", 6) as f:
        f.write("\n".join(rows).encode("utf-8"))
    print(f"[ok] {out}  {out.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

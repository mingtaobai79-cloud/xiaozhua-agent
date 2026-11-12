#!/usr/bin/env python3
"""从实现 jar 扫「接口 → 实现类」真实映射，替代按命名规则猜。

为什么：平台命名不规则。`com.seeyon.bpm.api.common.BpmAppService` 的实现是
`BpmApiAppServiceImpl`（不是 `BpmAppServiceImpl`）——靠 `XxxAppService` → `XxxAppServiceImpl`
猜会漏掉整个 BPM 核心接口。必须读字节码的 implements 子句。

用法：
  python tools/core/platform/build_impl_map.py --repo <MAVEN_REPO>-extra --emit <impl-map.json>
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"
RE_IMPL = re.compile(r"\bimplements\s+([\w.$<>,\s]+?)\s*\{")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    root = Path(a.repo)
    mapping: dict[str, list[dict]] = {}
    total = 0

    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        js = sorted(d.rglob("*.jar"))
        if not js:
            continue
        jar = js[-1]
        with zipfile.ZipFile(jar) as z:
            names = [n for n in z.namelist()
                     if n.endswith("AppServiceImpl.class") and "$" not in n]
        print(f"{d.name}: {len(names)} 个 AppServiceImpl", flush=True)
        for name in names:
            fq = name[:-6].replace("/", ".")
            try:
                r = subprocess.run([JAVAP, "-cp", str(jar), fq],
                                   capture_output=True, text=True, timeout=60,
                                   encoding="utf-8", errors="replace")
            except subprocess.TimeoutExpired:
                continue
            if r.returncode != 0:
                continue
            m = RE_IMPL.search(r.stdout)
            if not m:
                continue
            for iface in m.group(1).split(","):
                iface = iface.strip().split("<")[0]
                if not iface:
                    continue
                mapping.setdefault(iface, []).append(
                    {"impl": fq.split(".")[-1], "jar": jar.name, "pkg": d.name})
                total += 1

    out = {"iface_count": len(mapping), "impl_count": total, "map": mapping}
    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(mapping)} 个接口 / {total} 条实现关系 → {p}（{p.stat().st_size//1024} KB）")
    # 抽查关键接口
    for k in ("com.seeyon.bpm.api.common.BpmAppService",
              "com.seeyon.organization.api.OrgCommonAppService"):
        if k in mapping:
            print(f"  ✓ {k.split('.')[-1]} → {[x['impl'] for x in mapping[k]]}")
        else:
            print(f"  ✗ 缺 {k}")
    if len(mapping) < 50:
        print("ERR: 接口过少")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

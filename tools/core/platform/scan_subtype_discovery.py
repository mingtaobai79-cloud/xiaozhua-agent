#!/usr/bin/env python3
"""扫「子类型反射发现」这条注册通路：谁调 BeanReflections.getSubTypesOf / Reflections。

背景：平台注册扩展点有四条通路，第四条是
  `BeanReflections.getSubTypesOf(X)` → `getReflections("com.seeyon").getSubTypesOf(type)`
即用 Reflections 库扫 com.seeyon 整个包下 X 的所有实现类，**不写任何注册文件**。
走这条路的扩展点，静态文件里查不到注册痕迹，只能靠扫调用点发现。

做法：逐 class 扫常量池字节找 `getSubTypesOf`，命中后用 javap -c 提 `ldc class` 参数。

用法：
  python tools/core/platform/scan_subtype_discovery.py --repo <MAVEN_REPO>/com/seeyon --emit <out.json>
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"
LDC_CLASS = re.compile(r"ldc.*?class ([\w.$/]+)")
# 一次 javap -c 输出里，从 ldc 到 getSubTypesOf 的窗口
WINDOW = 6


def jars_of(repo: Path) -> list[Path]:
    # 每个构件取版本最高的一份
    by_pkg: dict[str, Path] = {}
    for d in sorted(repo.iterdir()):
        if not d.is_dir():
            continue
        js = sorted(d.rglob("*.jar"))
        if js:
            by_pkg[d.name] = js[-1]
    return sorted(by_pkg.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    repo = Path(a.repo)
    jars = jars_of(repo)
    print(f"扫 {len(jars)} 个 jar", flush=True)

    hits: list[tuple[Path, str]] = []
    for jar in jars:
        try:
            with zipfile.ZipFile(jar) as z:
                for name in z.namelist():
                    if not name.endswith(".class") or "$" in name:
                        continue
                    try:
                        raw = z.read(name)
                    except Exception:
                        continue
                    if b"getSubTypesOf" in raw:
                        hits.append((jar, name))
        except zipfile.BadZipFile:
            continue
    print(f"命中 {len(hits)} 个 class 调用 getSubTypesOf", flush=True)

    # 对命中项反编译，提被扫的接口
    found: dict[str, set[str]] = {}
    detail = []
    for jar, name in hits:
        fq = name[:-6].replace("/", ".")
        try:
            r = subprocess.run([JAVAP, "-p", "-c", "-cp", str(jar), fq],
                               capture_output=True, text=True, timeout=60,
                               encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            continue
        if r.returncode != 0:
            continue
        lines = r.stdout.splitlines()
        for i, line in enumerate(lines):
            if "getSubTypesOf" not in line:
                continue
            for j in range(i, max(0, i - WINDOW), -1):
                m = LDC_CLASS.search(lines[j])
                if m:
                    t = m.group(1).replace("/", ".")
                    if t != fq and not t.startswith("java."):
                        found.setdefault(t, set()).add(fq)
                        detail.append({"scanned_type": t, "caller": fq, "jar": jar.name})
                    break

    out = {"scanned_types": {k: sorted(v) for k, v in found.items()},
           "total_types": len(found),
           "total_callsites": len(detail),
           "detail": detail}
    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n发现 {len(found)} 个类型走子类型扫描：")
    for t, callers in sorted(found.items(), key=lambda x: -len(x[1])):
        print(f"  {len(callers)} 处  {t}")
    print(f"\n→ {p}（{p.stat().st_size//1024} KB）")
    if len(found) < 3:
        print("WARN: 发现的类型过少，可能是扫描窗口或常量池匹配失效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

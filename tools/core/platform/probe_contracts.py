#!/usr/bin/env python3
"""编译探针：用真实 jar 编译手写的调用代码，验证契约理解正确。

为什么需要：静态抽取只能证明「签名长这样」，不能证明「按这个写法能编译」。
编译通过才能排除：接口全名写错、方法名写错、DTO 字段名/类型错、取值链错、
类放错构件（EntityDto 在 udc-common 而不是 udc-facade）。

classpath 自动推导：从 Java 的 import 反查 interfaces.json 的 pkg 字段，
再去 repo 找该构件的 jar。不用手写一长串 -cp。

用法：
  python tools/core/platform/probe_contracts.py \
      --src tools/core/platform/probe_contracts --repo <MAVEN_REPO> \
      --interfaces <interfaces.json> [--javac <LOCAL_ROOT>/java/bin/javac.exe]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RE_IMPORT = re.compile(r"^import\s+(com\.seeyon\.[\w.]+);", re.M)
JAVAC = "<LOCAL_ROOT>/java/bin/javac.exe"


def pick_jar(repo: Path, pkg: str) -> Path | None:
    d = repo / "com" / "xiaozhua" / pkg
    if not d.is_dir():
        return None
    jars = sorted(d.rglob("*.jar"))
    if not jars:
        return None
    # 取版本号最高的（按目录名 sort -V 的近似：按元组比）
    def key(p: Path):
        v = p.parent.name
        return tuple(int(x) for x in re.findall(r"\d+", v)) or (0,)
    return sorted(jars, key=key)[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="含 *.java 的目录")
    ap.add_argument("--repo", default="<MAVEN_REPO>")
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--javac", default=JAVAC)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cs = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))["classes"]
    src_dir = Path(a.src)
    files = sorted(src_dir.glob("*.java"))
    if not files:
        print("ERR: 没有 .java")
        return 5

    needed_pkgs: set[str] = set()
    missing: list[str] = []
    for f in files:
        for fq in RE_IMPORT.findall(f.read_text(encoding="utf-8")):
            c = cs.get(fq)
            if c and c.get("pkg"):
                needed_pkgs.add(c["pkg"])
            else:
                missing.append(f"{f.name}: {fq}")

    repo = Path(a.repo)
    jars: list[str] = []
    unresolved: list[str] = []
    for pkg in sorted(needed_pkgs):
        j = pick_jar(repo, pkg)
        if j:
            jars.append(str(j).replace("\\", "/"))
        else:
            unresolved.append(pkg)

    print(f"{len(files)} 个探针 / {len(needed_pkgs)} 个构件")
    for j in jars:
        print(f"  {j}")
    if missing:
        print("  未在索引里找到（可能是 JDK 类）：")
        for m in missing[:5]:
            print(f"    {m}")
    if unresolved:
        print(f"  ERR 找不到 jar: {unresolved}")
        return 5

    out = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix="probe-"))
    out.mkdir(parents=True, exist_ok=True)
    cp = ";".join(jars)
    rc = 0
    for f in files:
        r = subprocess.run([a.javac, "-encoding", "UTF-8", "-nowarn",
                            "-cp", cp, "-d", str(out), str(f)],
                           capture_output=True, text=True, timeout=300,
                           encoding="gbk", errors="replace")
        ok = r.returncode == 0
        print(f"  {'PASS' if ok else 'FAIL'} {f.name}")
        if not ok:
            rc = 6
            for line in (r.stderr or "").splitlines()[:8]:
                print(f"       {line}")
    classes = list(out.glob("*.class"))
    print(f"\n{len(classes)} 个 .class → {out}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

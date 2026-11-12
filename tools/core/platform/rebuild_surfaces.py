#!/usr/bin/env python3
"""按「仓库里该构件的最新版本」重抽全部签名面。

背景：首轮抽取按目录遍历取了某一版，66/91 个构件是旧版（boot 族 5.3.358、
udc 族 5.3.517），而扩展工程 pom 用的是 5.3.600/5.3.603/5.3.601/5.3.605。
版本对不上 = 签名不可信，等于白抽。

本脚本：
  1. 对每个构件解析目标 jar（默认取仓库里版本号最高的）
  2. 调 extract_jar_symbols.py 逐个抽（javap -p 全类，--limit 3000）
  3. 并发跑（javap 每次一进程，串行太慢）

用法：
  python tools/core/platform/rebuild_surfaces.py \
      --interfaces <interfaces.json> --repo <MAVEN_REPO>/com/seeyon \
      --out-dir docs/audit/artifacts/extension-surface-20261029/batch2 \
      --only-changed --jobs 6
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTRACT = HERE / "extract_jar_symbols.py"


def vkey(v: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", v)] or [0]


def pick_jar(repo: Path, pkg: str, recorded: str | None) -> tuple[Path | None, str, bool]:
    """返回 (jar, 版本, 是否与记录版本不同)。优先仓库里版本最高的。"""
    d = repo / pkg
    if not d.is_dir():
        hits = sorted(repo.glob(f"{pkg}-*.jar"))
        if hits:
            return hits[-1], "?", True
        return None, "?", False
    vers = sorted([p for p in d.iterdir() if p.is_dir()], key=lambda p: vkey(p.name))
    if not vers:
        jars = sorted(d.glob("*.jar"), key=lambda p: vkey(p.name))
        return (jars[-1], "?", True) if jars else (None, "?", False)
    chosen = vers[-1]
    jars = sorted(chosen.glob("*.jar"), key=lambda p: p.stat().st_size, reverse=True)
    if not jars:
        return None, chosen.name, False
    rec_v = (re.search(r"(\d+\.\d+\.\d+)", recorded or "") or [None, None])[1]
    return jars[0], chosen.name, (rec_v != chosen.name)


def run_one(pkg: str, jar: Path, out: Path, javap: str | None, timeout: int) -> dict:
    cmd = [sys.executable, str(EXTRACT), "--jar", str(jar), "--emit", str(out),
           "--limit", "3000", "--timeout", str(timeout)]
    if javap:
        cmd += ["--javap", javap]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 6)
        ok = r.returncode == 0 and out.exists()
        return {"pkg": pkg, "ok": ok, "rc": r.returncode,
                "tail": (r.stdout or r.stderr or "").strip().splitlines()[-1:] }
    except subprocess.TimeoutExpired:
        return {"pkg": pkg, "ok": False, "rc": -1, "tail": ["超时"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--repo", default="<MAVEN_REPO>/com/seeyon")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--only-changed", action="store_true", help="只重抽版本变了的构件")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--javap", default="<LOCAL_ROOT>/java/bin/javap.exe")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    data = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    sources = data["sources"]
    repo = Path(a.repo)
    outdir = Path(a.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    javap = a.javap if Path(a.javap).exists() else None

    todo = []
    skipped = []
    for pkg, info in sorted(sources.items()):
        jar, ver, changed = pick_jar(repo, pkg, info.get("jar"))
        if jar is None:
            skipped.append((pkg, "无 jar"))
            continue
        if a.only_changed and not changed:
            skipped.append((pkg, f"已是 {ver}"))
            continue
        todo.append((pkg, jar, ver))

    print(f"待抽 {len(todo)} 个 / 跳过 {len(skipped)} 个，jobs={a.jobs}", flush=True)
    for pkg, jar, ver in todo[:5]:
        print(f"  样例 {pkg:26s} -> {jar.name}", flush=True)

    results = []
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(run_one, pkg, jar, outdir / f"{pkg}.json", javap, a.timeout): (pkg, ver)
                for pkg, jar, ver in todo}
        done = 0
        for f in cf.as_completed(futs):
            pkg, ver = futs[f]
            r = f.result()
            r["ver"] = ver
            results.append(r)
            done += 1
            if done % 10 == 0 or not r["ok"]:
                print(f"  [{done}/{len(todo)}] {pkg} ver={ver} ok={r['ok']} {r['tail']}", flush=True)

    bad = [r for r in results if not r["ok"]]
    print(f"\n完成 {len(results)-len(bad)} / 失败 {len(bad)}", flush=True)
    for r in bad:
        print(f"  FAIL {r['pkg']} rc={r['rc']} {r['tail']}")
    if bad:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

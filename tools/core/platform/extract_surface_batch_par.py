#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""并行抽取一批 jar 的方法签名面（只读）。

为什么并行：截图里 84 个包；单进程 javap 一个 jar 约 26s、带 cfr 约 60s，
串行要 40~85 分钟。取方法签名只需 javap，故可并发。

纪律（踩过的坑）：
  * 默认不走 cfr：cfr 单 jar 会撞超时重试，慢一倍以上且对「签名面」无增量。
    要反编译正文时才加 --cfr。
  * 每个包跑完立即追加一行进度，中断后重跑自动跳过已完成（按 artifact 去重）。
  * 产物文件名 = <artifact>.json，便于与清单对账，缺哪个一眼看出来。

用法：
  uv run --no-project python tools/core/platform/extract_surface_batch_par.py \
      --targets <targets.json> --emit-dir <dir> --progress <dir>/_progress.jsonl \
      --javap <javap> [--cfr <cfr.jar>] [--workers 8] [--limit 200]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
_LOCK = threading.Lock()


def run_one(artifact: str, version: str, jar: str, include: str, emit: Path,
            javap: str, cfr: str | None, limit: int, timeout: int) -> dict:
    cmd = [sys.executable, str(HERE / "extract_jar_symbols.py"),
           "--jar", jar, "--include", include, "--emit", str(emit),
           "--javap", javap, "--limit", str(limit), "--timeout", str(timeout)]
    if cfr:
        cmd += ["--cfr", cfr]
    t0 = time.time()
    rec = {"artifact": artifact, "version": version, "jar": Path(jar).name,
           "emit": emit.name, "ok": False}
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 30 + 180)
        if emit.exists():
            d = json.loads(emit.read_text(encoding="utf-8"))
            rec.update(ok=p.returncode == 0,
                       classes=d.get("class_count_scanned"),
                       methods=d.get("total_methods"),
                       interfaces=d.get("interfaces"),
                       routes=d.get("routes"))
        else:
            rec["tail"] = (p.stderr or p.stdout or "")[-300:]
    except subprocess.TimeoutExpired:
        rec["tail"] = "超时"
    except Exception as e:  # noqa: BLE001
        rec["tail"] = f"{type(e).__name__}: {e}"
    rec["secs"] = round(time.time() - t0, 1)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True, help="{artifact: [version, jarPath]}")
    ap.add_argument("--emit-dir", required=True)
    ap.add_argument("--progress", required=True)
    ap.add_argument("--javap", required=True)
    ap.add_argument("--cfr", default=None, help="给了才走反编译（慢）")
    ap.add_argument("--include-prefix", default="com/seeyon")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    targets = json.loads(Path(a.targets).read_text(encoding="utf-8"))
    emit_dir = Path(a.emit_dir); emit_dir.mkdir(parents=True, exist_ok=True)
    prog = Path(a.progress); prog.parent.mkdir(parents=True, exist_ok=True)

    done = set()
    if prog.exists():
        for line in prog.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                if r.get("ok"):
                    done.add(r["artifact"])
            except Exception:  # noqa: BLE001
                pass
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    todo = [(k, v[0], v[1]) for k, v in targets.items()
            if k not in done and (not only or k in only)]
    print(f"目标 {len(targets)}，已完成 {len(done)}，本轮 {len(todo)}，并发 {a.workers}",
          flush=True)

    t_all = time.time()
    with prog.open("a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(run_one, art, ver, jar, a.include_prefix,
                          emit_dir / f"{art}.json", a.javap, a.cfr, a.limit, a.timeout): art
                for art, ver, jar in todo}
        n = 0
        for f in as_completed(futs):
            n += 1
            rec = f.result()
            with _LOCK:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()
            print(f"[{n}/{len(todo)}] {'OK ' if rec['ok'] else 'FAIL'} {rec['artifact']} "
                  f"{rec['version']} c={rec.get('classes','-')} m={rec.get('methods','-')} "
                  f"{rec['secs']}s {rec.get('tail','')}", flush=True)

    rows = [json.loads(l) for l in prog.read_text(encoding="utf-8").splitlines() if l.strip()]
    okn = sum(1 for r in rows if r.get("ok"))
    print(f"\n总计 {len(rows)} 条记录，成功 {okn}，失败 {len(rows)-okn}，"
          f"耗时 {round(time.time()-t_all,1)}s", flush=True)
    sys.exit(0 if okn == len(targets) else 2)


if __name__ == "__main__":
    main()

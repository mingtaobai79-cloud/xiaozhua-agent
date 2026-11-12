"""chunk_unpack.py — 用 Wakaru(REA 的 JS 引擎)把 webpack chunk 拆成按 module id 命名的可读模块。

替代手工 grep 字节偏移考古：以前定位 module 74964 要 `grep -b "74964:"` 记偏移再数 259KB，
现在直接 unpack 后读 module-<id>.js；provenance.json 保留模块↔原 bundle 字节区间映射。

用法：
    python tools/chunk_unpack.py <chunk.js> [chunk2.js ...] --out <dir>
    python tools/chunk_unpack.py --find <dir> <module_id>     # 在已拆目录里找模块归属

依赖：wakaru 引擎二进制（npm install wakaru@1.14.0 后用 @wakaru/cli-win32-x64/wakaru.exe，
或 REA 全局装好后 rea 的 recover_javascript_sources 等价路径）。
证据纪律：拆出的模块是 STATIC 证据（反格式化产物），引用时保留原 chunk 路径 + provenance；
不得把反格式化命名当成源码原命名。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

WAKARU_CANDIDATES = (
    # 本仓约定：二进制路径走环境/config，不写死机器值；探测顺序：env → PATH → node_modules
    ("WAKARU_COMMAND", None),
    (None, "wakaru"),
    (None, str(Path("node_modules/@wakaru/cli-win32-x64/wakaru.exe"))),
    (None, str(Path("node_modules/@wakaru/cli-linux-x64/wakaru"))),
)


def find_wakaru() -> str:
    import os
    env = os.environ.get("WAKARU_COMMAND")
    if env and Path(env).exists():
        return env
    for _env_key, name in WAKARU_CANDIDATES:
        if name is None:
            continue
        p = shutil.which(name)
        if p:
            return p
        if Path(name).exists():
            return str(Path(name).resolve())
    raise SystemExit(
        "wakaru 引擎未找到。装法：npm install wakaru@1.14.0（平台二进制随包），"
        "或设 WAKARU_COMMAND 环境变量。REA 全家桶自带等价能力。")


def unpack(chunk: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    cmd = [find_wakaru(), str(chunk), "--unpack", "--provenance", "-o", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    prov = out / "provenance.json"
    modules = []
    if prov.exists():
        data = json.loads(prov.read_text(encoding="utf-8"))
        modules = list((data.get("modules") or {}).keys())
    return {"chunk": str(chunk), "out": str(out),
            "returncode": r.returncode,
            "module_count": len(modules),
            "provenance": str(prov) if prov.exists() else None,
            "stderr": (r.stderr or "")[:400]}


def find_module(unpacked_dir: Path, module_id: str) -> list[dict]:
    hits = []
    for f in unpacked_dir.glob("module-*.js"):
        if module_id in f.stem:
            hits.append({"file": str(f), "size": f.stat().st_size})
    # 兜底：模块内部 require 图（拆出文件互相引用 ./module-X.js）
    for f in unpacked_dir.glob("module-*.js"):
        if f.read_text(encoding="utf-8", errors="replace").find(f'module-{module_id}.js') >= 0:
            hits.append({"file": str(f), "relation": "references-it"})
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="unpacked", help="输出目录（每 chunk 一个子目录）")
    ap.add_argument("--find", metavar="DIR", help="在已拆目录中查找模块归属（配 --module）")
    ap.add_argument("--module", metavar="ID", help="与 --find 搭配的 webpack module id")
    ap.add_argument("chunks", nargs="*", help="webpack chunk .js 文件")
    ns = ap.parse_args(argv)
    if ns.find:
        if not ns.module:
            raise SystemExit("--find 需要 --module <id>")
        d = Path(ns.find)
        if not d.exists():
            # 允许传前缀目录名：解析成实际目录
            parent = d.parent
            cands = [p for p in parent.glob(d.name + "*") if p.is_dir()] if parent.exists() else []
            if cands:
                d = cands[0]
        print(json.dumps(find_module(d, ns.module), ensure_ascii=False, indent=1))
        return 0
    results = []
    for c in ns.chunks:
        chunk = Path(c)
        if not chunk.exists():
            raise SystemExit(f"chunk 不存在: {chunk}")
        results.append(unpack(chunk, Path(ns.out) / chunk.stem[:60]))
    print(json.dumps(results, ensure_ascii=False, indent=1))
    return 0 if all(r["returncode"] == 0 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

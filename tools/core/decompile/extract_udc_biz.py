"""udc-biz JAR 结构提取 —— 代码生成模板清单 + 包结构 + 关键类签名。

udc-web 有 javap 全景产物（54 controller / 671 API），udc-biz 此前没有。
本脚本用本机 JDK javap 提取 udc-biz 的：
  1. autocode/JAVA/<ver>/templates/<domain>/ 代码生成模板全清单（微流程节点/实体规则/实体/...）；
  2. com/seeyon/udc/<pkg> 包结构 class 计数；
  3. 指定关键类的 javap -p 方法签名（microflow/detection/entity 服务）。

用法：
    python tools/extract_udc_biz.py <jar> [--out <dir>] [--classes A,B,...]

证据边界：产物是 STATIC_BYTECODE（javap 观测），不证明运行态行为；
jar 本身不入 git（.gitignore），产物落 docs/audit/artifacts/。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"   # 可在 --javap 覆盖


def _unzip_list(jar: Path) -> list[str]:
    out = subprocess.run(["unzip", "-l", str(jar)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return out.stdout.splitlines()


def templates(lines: list[str]) -> dict[str, list[str]]:
    """autocode/JAVA/<ver>/templates/<domain>/<Name>.ftl → {ver/domain: [names]}"""
    by = defaultdict(list)
    for ln in lines:
        m = re.search(r'(autocode/JAVA/[\d.]+/templates/(\w+)/(\S+))', ln)
        if m:
            ver = re.search(r'JAVA/([\d.]+)/', m.group(1)).group(1)
            by[f"{ver}/{m.group(2)}"].append(m.group(3))
    return {k: sorted(set(v)) for k, v in sorted(by.items())}


def package_census(lines: list[str]) -> dict[str, int]:
    pkgs: dict[str, int] = defaultdict(int)
    for ln in lines:
        m = re.search(r'(com/seeyon/udc/\w+(?:/\w+)?)/\S+\.class', ln)
        if m:
            pkgs[m.group(1)] += 1
    return {k: v for k, v in sorted(pkgs.items(), key=lambda x: -x[1])}


def javap_class(jar: Path, fqn: str, javap: str = JAVAP) -> str:
    out = subprocess.run([javap, "-p", "-classpath", str(jar), fqn],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return out.stdout or f"ERR: {out.stderr}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jar")
    ap.add_argument("--out", default="docs/audit/artifacts/udc-biz-5.3.517")
    ap.add_argument("--classes", default="", help="逗号分隔 FQN，抽 javap -p 签名")
    ap.add_argument("--javap", default=JAVAP)
    ns = ap.parse_args()
    jar = Path(ns.jar)
    lines = _unzip_list(jar)
    tpl = templates(lines)
    pkgs = package_census(lines)
    out_dir = Path(ns.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 模板清单
    (out_dir / "_codegen_templates.json").write_text(
        json.dumps(tpl, ensure_ascii=False, indent=1), encoding="utf-8")
    # 包结构
    (out_dir / "_package_census.json").write_text(
        json.dumps(pkgs, ensure_ascii=False, indent=1), encoding="utf-8")
    # 摘要 markdown
    md = ["# udc-biz 代码生成模板与包结构（javap/zip 静态）", "",
          f"> JAR: {jar.name} | 来源: Artifactory libs-release", "",
          f"## 代码生成模板（{sum(len(v) for v in tpl.values())} 个文件）", ""]
    for k in tpl:
        md.append(f"### {k}（{len(tpl[k])}）")
        md += [f"- `{n}`" for n in tpl[k]]
        md.append("")
    md += ["## 包结构（class 计数）", "", "| 包 | class 数 |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in pkgs.items()]
    (out_dir / "_UDC-BIZ-PANORAMA.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # 关键类签名
    if ns.classes:
        for fqn in [c.strip() for c in ns.classes.split(",") if c.strip()]:
            sig = javap_class(jar, fqn, ns.javap)
            safe = fqn.split(".")[-1]
            (out_dir / f"{safe}.javap.txt").write_text(sig, encoding="utf-8")
            print(f"javap {fqn}: {len(sig.splitlines())} 行")
    print(f"模板组: {len(tpl)} | 包: {len(pkgs)} | 落盘: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

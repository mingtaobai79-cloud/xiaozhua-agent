#!/usr/bin/env python3
"""扫 DTO 字段的校验注解，回答「哪些字段必填、有什么长度/范围约束」。

为什么：使用卡只有「字段名 + 类型」不够。真正写调用代码时第一个问题是
「这个字段能不能不填」。答案在 javax.validation 注解里（@NotNull / @NotBlank /
@NotEmpty / @Length / @Size / @Min / @Max / @Pattern），字节码里是 RuntimeVisibleAnnotations。

用法：
  python tools/core/platform/scan_dto_validations.py \
      --interfaces <interfaces.json> --emit <dto-validations.json> [--repo <MAVEN_REPO>-extra <MAVEN_REPO>]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"
RE_FIELD = re.compile(r"^  (?:private|protected|public)[\w.$<>, \[\]]*\s+([\w$]+);\s*$")
RE_ANNO = re.compile(r"^\s+\d+: #\d+\(\S*\)\s*$")
RE_ANNO_NAME = re.compile(r"^\s+(?:javax\.validation[\w.]*|jakarta\.validation[\w.]*)\.(\w+)\(")
RE_ARG = re.compile(r'^\s+(message|value|min|max|regexp)\s*=\s*(.+?)\s*$')
KEEP = {"NotNull", "NotBlank", "NotEmpty", "Length", "Size", "Min", "Max",
        "Pattern", "Email", "Range", "DecimalMin", "DecimalMax", "Valid", "Past", "Future"}


def jar_index(repos: list[Path]) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for r in repos:
        for j in r.rglob("*.jar"):
            try:
                with zipfile.ZipFile(j) as z:
                    for n in z.namelist():
                        if n.endswith(".class"):
                            idx.setdefault(n[:-6].replace("/", "."), j)
            except Exception:
                continue
    return idx


def scan(jar: Path, fq: str) -> dict[str, list[str]]:
    try:
        r = subprocess.run([JAVAP, "-v", "-cp", str(jar), fq],
                           capture_output=True, text=True, timeout=90,
                           encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {}
    if r.returncode != 0:
        return {}
    out: dict[str, list[str]] = {}
    cur = None
    for line in r.stdout.splitlines():
        m = RE_FIELD.match(line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
            continue
        if cur and RE_ANNO.match(line):
            continue
        m = RE_ANNO_NAME.match(line)
        if m and cur:
            name = m.group(1)
            if name in KEEP:
                out[cur].append(name)
            continue
    return {k: v for k, v in out.items() if v}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit", required=True)
    ap.add_argument("--repo", nargs="*", default=["<MAVEN_REPO>-extra", "<MAVEN_REPO>"])
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]
    # 目标 DTO：被 AppService 方法引用的入参/返回类型
    REQ = re.compile(r"(?:SingleRequest|ListRequest|PageRequest)<\s*([\w.$]+)\s*>")
    RESP = re.compile(r"(?:SingleResponse|ListResponse|PageResponse)<\s*([\w.$]+)\s*>")
    targets: set[str] = set()
    for fq, c in cs.items():
        if c.get("kind") != "interface" or not fq.split(".")[-1].endswith("AppService"):
            continue
        for m in c["methods"]:
            for rx in (REQ, RESP):
                mm = rx.search(m.get("signature", ""))
                if mm:
                    targets.add(mm.group(1))
    targets = {t for t in targets if t in cs}
    print(f"目标 DTO {len(targets)} 个", flush=True)

    repos = [Path(x) for x in a.repo]
    idx = jar_index(repos)
    print(f"jar 索引 {len(idx)} 个类", flush=True)

    result: dict[str, dict] = {}
    miss = 0
    for i, fq in enumerate(sorted(targets), 1):
        jar = idx.get(fq)
        if not jar:
            miss += 1
            continue
        v = scan(jar, fq)
        if v:
            result[fq] = v
        if i % 100 == 0:
            print(f"  {i}/{len(targets)} 有约束 {len(result)}", flush=True)

    out = {"scanned": len(targets), "with_constraints": len(result),
           "not_found": miss, "map": result}
    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(result)}/{len(targets)} 个 DTO 有校验注解（{miss} 个类找不到）→ {p}"
          f"（{p.stat().st_size//1024} KB）")
    # 抽查
    for fq in list(result)[:3]:
        print(f"  {fq.split('.')[-1]}: {result[fq]}")
    if len(result) < 50:
        print("WARN: 有约束的 DTO 过少，注解可能不在 javax.validation 包")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

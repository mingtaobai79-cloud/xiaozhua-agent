#!/usr/bin/env python3
"""一句话重建反编译证据（docs/audit/artifacts）。

    python tools/regen_evidence.py                    # 抽取 + 聚合 + 自检
    python tools/regen_evidence.py --aggregate-only    # 只把已有批量产物汇总成 interfaces.json
    python tools/regen_evidence.py --check             # 只检查前置条件，不写任何文件

为什么需要它：分发树不带 docs/audit/artifacts（约 390MB / 8800 文件），
但那些是「这条事实凭什么成立」的依据。构件清单在 config/evidence-manifest.json（91 项）。

前置（缺一即退出并说明）：
  --maven  本地 maven 仓库根，默认 D:/repo/CHIT/com.seeyon
  --javap  javap 可执行文件，默认 D:/software/java/bin/javap.exe

产物：
  <evidence>/batch2/*.json          逐构件签名面
  <evidence>/interfaces.json        sources + classes + method_index
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = ROOT / "config" / "evidence-manifest.json"
EVIDENCE = ROOT / "docs" / "audit" / "artifacts" / "extension-surface-20261029"

MODS = {
    "public", "protected", "private", "static", "final", "abstract", "default",
    "synchronized", "native", "strictfp", "transient", "volatile", "sealed",
    "non-sealed",
}


# --------------------------------------------------------------------------- #
# javap 文本 → interfaces.json 的类结构
# --------------------------------------------------------------------------- #
def _split_top(s: str, sep: str = ",") -> list[str]:
    """按顶层分隔符切分，忽略尖括号/方括号内部的逗号。"""
    out, buf, depth = [], [], 0
    for ch in s:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf))
    return [x.strip() for x in out if x.strip()]


def _kind_of(decl: str) -> str:
    if "interface" in decl.replace("@interface", "interface"):
        return "interface"
    if re.search(r"extends\s+java\.lang\.Enum\s*<", decl):
        return "enum"
    return "class"


def _clause(decl: str, kw: str) -> list[str]:
    m = re.search(rf"\b{kw}\s+(.+?)(?=\bimplements\b|\bextends\b|\{{|$)", decl)
    if not m:
        return []
    return _split_top(m.group(1))


def _parse_member(line: str) -> dict | None:
    s = line.strip()
    if not s or s.startswith("//") or s in ("{", "}"):
        return None
    if "(" in s and s.endswith(";"):
        return _parse_method(s)
    if s.endswith(";") and "(" not in s:
        return _parse_field(s)
    return None


_IDENT = re.compile(r"^[A-Za-z_$][\w$]*(?:\$\d+)?$")


def _parse_method(s: str) -> dict | None:
    body = s[:-1].strip()                      # 去掉结尾分号
    lp = body.find("(")
    if lp < 0:
        return None
    # 字段初始化式里也可能带括号（字符串常量 / 匿名类），先排除
    if " = " in body[:lp]:
        return None
    if lp < 0:
        return None
    # 从右往左找配对的右括号（末尾可能就是 ')'）
    rp = body.rfind(")")
    if rp < lp:
        return None
    head = body[:lp].strip()
    args_s = body[lp + 1:rp].strip()

    toks = head.split()
    mods = []
    while toks and toks[0] in MODS:
        mods.append(toks.pop(0))
    if not toks:
        return None
    name = toks[-1]
    if not _IDENT.match(name) and "<init>" not in name:
        return None
    returns = " ".join(toks[:-1]).strip()
    if not returns:                            # 构造器：javap 里是 fqcn(...)
        returns = name
        name = name.rsplit(".", 1)[-1]

    args = []
    for i, a in enumerate(_split_top(args_s)):
        parts = a.split()
        if len(parts) >= 2:
            args.append({"type": " ".join(parts[:-1]), "name": parts[-1]})
        else:
            args.append({"type": a, "name": f"arg{i}"})
    return {"name": name, "returns": returns, "args": args,
            "modifiers": mods, "signature": s}


def _parse_field(s: str) -> dict | None:
    body = s[:-1].strip()
    value = None
    if " = " in body:
        body, value = body.split(" = ", 1)
    toks = body.split()
    mods = []
    while toks and toks[0] in MODS:
        mods.append(toks.pop(0))
    if not toks:
        return None
    name = toks[-1]
    ftype = " ".join(toks[:-1]).strip()
    if not ftype:
        return None
    d = {"name": name, "type": ftype, "modifiers": mods}
    if value is not None:
        d["value"] = value.strip()
    return d


def parse_class_record(rec: dict) -> tuple[str, dict] | None:
    entry = rec.get("entry") or ""
    if not entry.endswith(".class"):
        return None
    fqcn = entry[:-6].replace("/", ".")
    text = rec.get("javap") or ""
    lines = [l.rstrip() for l in text.splitlines()]
    decl = next((l.strip() for l in lines
                 if "{" in l and re.search(r"\b(class|interface|enum)\b", l)), "")
    if not decl:
        return None

    methods, fields = [], []
    body = False
    for line in lines:
        if not body:
            if "{" in line:
                body = True
            continue
        if line.strip() == "}":
            break
        m = _parse_member(line)
        if not m:
            continue
        (methods if "signature" in m else fields).append(m)

    kind = _kind_of(decl)
    entry_obj = {
        "kind": kind,
        "fqcn": fqcn,
        "pkg": fqcn.rsplit(".", 1)[0],
        "decl": decl,
        "extends": _clause(decl, "extends"),
        "implements": _clause(decl, "implements"),
        "methods": methods,
        "fields": fields,
    }
    if kind == "enum":
        entry_obj["constants"] = [f["name"] for f in fields if f.get("type") == fqcn]
    return fqcn, entry_obj


# --------------------------------------------------------------------------- #
# 聚合
# --------------------------------------------------------------------------- #
def _iter_artifact_files(evidence: Path):
    for d in sorted(evidence.glob("batch*")):
        for f in sorted(d.glob("*.json")):
            if f.name.startswith("_"):
                continue
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(obj, dict) and "classes" in obj:
                yield d.name, f, obj


def aggregate(evidence: Path) -> dict:
    sources: dict[str, dict] = {}
    classes: dict[str, dict] = {}
    method_index: dict[str, list[str]] = {}

    for batch, path, obj in _iter_artifact_files(evidence):
        name = path.stem
        recs = obj.get("classes") or []
        if isinstance(recs, dict):
            recs = list(recs.values())
        n_ok = 0
        n_methods = 0
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            parsed = parse_class_record(rec)
            if not parsed:
                continue
            fqcn, entry = parsed
            classes[fqcn] = entry
            n_ok += 1
            n_methods += len(entry["methods"])
            for m in entry["methods"]:
                method_index.setdefault(m["name"], [])
                ref = f"{fqcn}#{m['name']}"
                if ref not in method_index[m["name"]]:
                    method_index[m["name"]].append(ref)
        sources[name] = {
            "jar": obj.get("jar") or obj.get("jar_path_hint", ""),
            "file": f"{batch}/{path.name}",
            "classes": n_ok,
            "total_methods": n_methods or obj.get("total_methods", 0),
        }

    return {"sources": sources, "classes": classes, "method_index": method_index}


# --------------------------------------------------------------------------- #
# 抽取（调 extract_surface_batch_par.py）
# --------------------------------------------------------------------------- #
def resolve_targets(maven: Path, manifest: dict) -> tuple[dict, list[str]]:
    targets, missing = {}, []
    for a in manifest["artifacts"]:
        jar_name = a["jar"]
        hits = sorted(maven.rglob(jar_name))
        if not hits:
            missing.append(f"{a['name']} ({jar_name})")
            continue
        targets[a["name"]] = [a["version"], str(hits[0]).replace("\\", "/")]
    return targets, missing


def run_extract(targets: dict, evidence: Path, javap: str, workers: int) -> int:
    script = ROOT / "tools" / "core" / "platform" / "extract_surface_batch_par.py"
    if not script.exists():
        print(f"[x] 缺抽取脚本: {script}", file=sys.stderr)
        return 2
    batch = evidence / "batch2"
    batch.mkdir(parents=True, exist_ok=True)
    tfile = evidence / "_targets.json"
    tfile.write_text(json.dumps(targets, ensure_ascii=False), encoding="utf-8")
    cmd = [sys.executable, str(script),
           "--targets", str(tfile),
           "--emit-dir", str(batch),
           "--progress", str(evidence / "_progress.jsonl"),
           "--javap", javap,
           "--limit", "100000",
           "--workers", str(workers)]
    print("[*] 抽取:", " ".join(cmd[:1] + [str(Path(cmd[1]).name)]))
    t0 = time.time()
    rc = subprocess.run(cmd, cwd=str(ROOT)).returncode
    print(f"[*] 抽取结束 rc={rc} 用时 {time.time()-t0:.0f}s")
    return rc


def _arg_types(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return ",".join((x.get("type", "") if isinstance(x, dict) else str(x)) for x in v)
    return ""


def write_signature_index(data: dict, out: Path) -> int:
    """把 classes 摊成一行一成员的可检索文本（gzip）。

    为什么是文本而不是原 JSON：原 interfaces.json 63.9MB，摊平后 33MB，
    gzip 后 2.3MB —— 差 28 倍，而查询速度一样（解压 0.2s + 内存过滤）。
    agent 直接 grep 或走 tools/signature_lookup.py 都能用。
    """
    import gzip
    lines: list[str] = []
    for fqcn, c in data["classes"].items():
        lines.append(f"{fqcn}\t{c.get('kind', 'class')}")
        for m in c.get("methods", []):
            lines.append(f"{fqcn}#{m['name']}({_arg_types(m.get('args'))}):{m.get('returns','')}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wb", 6) as f:
        f.write("\n".join(lines).encode("utf-8"))
    print(f"[ok] {out}  {len(lines)} 行 / {out.stat().st_size/1024/1024:.2f} MB")
    return len(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="一句话重建反编译证据")
    ap.add_argument("--maven", default="D:/repo/CHIT/com/seeyon")
    ap.add_argument("--javap", default="D:/software/java/bin/javap.exe")
    ap.add_argument("--evidence", default=str(EVIDENCE))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="", help="interfaces.json 输出路径（默认 <evidence>/interfaces.json）")
    ap.add_argument("--index", default=str(ROOT / "docs" / "audit" / "signatures.txt.gz"),
                    help="签名索引输出路径（gzip 文本，供 tools/signature_lookup.py 查）")
    ap.add_argument("--check", action="store_true", help="只检查前置条件")
    ap.add_argument("--aggregate-only", action="store_true", help="跳过抽取，直接聚合")
    a = ap.parse_args(argv)

    evidence = Path(a.evidence)
    maven = Path(a.maven)

    if not MANIFEST.exists():
        print(f"[x] 缺构件清单: {MANIFEST}", file=sys.stderr)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # 前置检查
    problems = []
    need_jars = not a.aggregate_only          # 只聚合时不碰 jar
    if need_jars and not maven.is_dir():
        problems.append(f"maven 仓库不存在: {maven}（--maven 指定，或在 --aggregate-only 下忽略）")
    if need_jars and not Path(a.javap).exists():
        problems.append(f"javap 不存在: {a.javap}")
    targets, missing = (resolve_targets(maven, manifest)
                        if need_jars and maven.is_dir() else ({}, []))
    print(f"[*] 构件 {len(manifest['artifacts'])} 项 | 本地可定位 {len(targets)} | 缺 {len(missing)}")
    if missing:
        for m in missing[:5]:
            print("    缺:", m)
        if len(missing) > 5:
            print(f"    …共 {len(missing)} 项缺")

    if problems:
        for p in problems:
            print("[x]", p, file=sys.stderr)
        return 2
    if a.check:
        print("[ok] 前置条件齐备")
        return 0 if not missing else 1

    if not a.aggregate_only:
        if missing:
            print(f"[!] {len(missing)} 个构件定位不到，先补齐再抽取（--check 看清单）", file=sys.stderr)
            return 2
        rc = run_extract(targets, evidence, a.javap, a.workers)
        if rc != 0:
            return rc

    print("[*] 聚合 interfaces.json …")
    t0 = time.time()
    data = aggregate(evidence)
    out = Path(a.out) if a.out else evidence / "interfaces.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] {out}  {len(data['classes'])} 类 / {len(data['method_index'])} 方法名 / "
          f"{len(data['sources'])} 构件  ({out.stat().st_size/1024/1024:.1f} MB, {time.time()-t0:.0f}s)")

    if a.index:
        write_signature_index(data, Path(a.index))

    # 自检：与清单登记的类数比对
    reg = {a["name"]: a["classes"] for a in manifest["artifacts"] if a.get("classes")}
    off = [(n, data["sources"][n]["classes"], c) for n, c in reg.items()
           if n in data["sources"] and data["sources"][n]["classes"] != c]
    if off:
        print(f"[!] {len(off)} 个构件类数与清单不符（清单可能是旧基线）")
        for n, got, want in off[:5]:
            print(f"    {n}: 实抽 {got} / 清单 {want}")
    else:
        print("[ok] 全部构件类数与清单一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())

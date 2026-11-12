# -*- coding: utf-8 -*-
"""抽取 jar 内「类 / 接口的方法级签名面」——用于沉淀平台标品能力用法。

为什么单独一个脚本：
  `extract_extension_surface.py` 只回答「哪些包可用」（依赖面）；
  本脚本回答「这些包里有哪些方法、签名是什么」（方法级），
  而方法级证据只能来自字节码（cfr 反编译 / javap）。

做法（双路，互为交叉验证）：
  ① javap -p（JDK 自带，签名权威但看不到方法体）
  ② cfr 反编译（能看到泛型/注解/默认实现与注释级别的线索）
两个都跑、都入件，读者任取其一即可复核；只跑一个时在输出里标 `routes`。

用法：
    python tools/core/platform/extract_jar_symbols.py \
        --jar <jar 路径> \
        --include com/seeyon/udc/facade/ \
        --emit docs/audit/artifacts/<...>/symbols.json \
        [--cfr <cfr.jar>] [--javap <javap.exe>] [--limit 80]

不写死 jar 路径 / 环境：jar 由 --jar 传入，工具路径可由参数或 PATH 解析。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def resolve_tool(explicit: str | None, name: str) -> str | None:
    """找 javap/javac：显式参数 > JAVA_HOME/bin > PATH。"""
    if explicit:
        return explicit if Path(explicit).exists() else None
    jh = os.environ.get("JAVA_HOME")
    if jh:
        exe = "javap.exe" if os.name == "nt" else "javap"
        cand = Path(jh) / "bin" / ("javap" if name == "javap" else name)
        if cand.with_suffix(".exe").exists():
            return str(cand.with_suffix(".exe"))
        if cand.exists():
            return str(cand)
    return shutil.which(name)


RE_CLASS_METHOD = re.compile(
    r"^\s*(?:public|protected|private)\s+"
    r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:abstract\s+)?"
    r"([\w$.<>\[\], ?]+?)\s+(\w+)\s*\(([^)]*)\)",
    re.M)
RE_INTERFACE_SIG = re.compile(r"^\s*public\s+interface\s+(\w+)(?:\s+extends\s+([\w$.,\s<>]+))?", re.M)
RE_CLASS_DECL = re.compile(r"^\s*public\s+(?:final\s+)?(?:abstract\s+)?class\s+(\w+)([^{]*)\{", re.M)
RE_FIELD = re.compile(r"^\s*private\s+(?:final\s+)?([\w$.<>\[\], ?]+?)\s+(\w+)\s*;", re.M)


def list_classes(jar: Path, include: str, limit: int) -> list[str]:
    out = []
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if not n.endswith(".class") or "$" in n:
                continue
            if include and not n.startswith(include):
                continue
            out.append(n)
    return sorted(out)[:limit]


def run(cmd: list[str], timeout=180) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")


def parse_source(java_src: str) -> dict:
    """从 cfr 产出的 Java 源里抽类级符号面（方法签名 / 字段 / 接口继承）。"""
    methods = []
    for ret, name, args in RE_CLASS_METHOD.findall(java_src):
        methods.append({"name": name, "returns": " ".join(ret.split()),
                        "args": " ".join(args.split())})
    iface = RE_INTERFACE_SIG.search(java_src)
    cls = RE_CLASS_DECL.search(java_src)
    fields = [{"type": " ".join(t.split()), "name": n} for t, n in RE_FIELD.findall(java_src)]
    ext = None
    if iface:
        ext = iface.group(2)
    elif cls:
        ext = cls.group(2)
    return {
        "kind": "interface" if iface else ("class" if cls else "unknown"),
        "name": (iface.group(1) if iface else (cls.group(1) if cls else None)),
        "extends": " ".join((ext or "").split()),
        "method_count": len(methods),
        "methods": methods,
        "fields": fields,
    }


def parse_javap(text: str) -> dict:
    """从 javap 输出里抽类级符号面。

    为什么需要它：cfr 只是「更丰富」的那一路，不是唯一一路。
    早先实现只在 cfr 命中时才产出 symbols，于是纯 javap 模式下
    total_methods 恒为 0 —— 84 个包跑完只有类数没有方法数，等于白跑。
    javap 的输出格式稳定（声明行 + 缩进成员行），足够取签名。
    """
    lines = text.splitlines()
    kind, name, ext = "unknown", None, ""
    methods, fields = [], []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("Compiled from") or s in ("{", "}"):
            continue
        # 声明行
        m = re.match(r"^public\s+(?:final\s+|abstract\s+)?(interface|class|enum)\s+([\w$.]+)(.*)$", s)
        if m:
            kind = m.group(1)
            name = m.group(2).split(".")[-1]
            tail = m.group(3)
            em = re.search(r"\bextends\s+([\w$.,\s<>]+?)(?:\s+implements\b|\s*\{|$)", tail)
            im = re.search(r"\bimplements\s+([\w$.,\s<>]+?)(?:\s*\{|$)", tail)
            parts = []
            if em:
                parts.append("extends " + " ".join(em.group(1).split()))
            if im:
                parts.append("implements " + " ".join(im.group(1).split()))
            ext = " ".join(parts)
            continue
        if kind == "unknown":
            continue
        body = s.rstrip(";")
        # 方法：名字( 且以 ) 收尾（忽略 throws 之后的内容）
        mm = re.match(r"^(.*?)\b([\w$]+)\s*\(([^)]*)\)", body)
        if mm and "(" in body:
            owner = mm.group(1).strip()
            fname = mm.group(2)
            # 排除构造器（无返回类型）
            if not owner or fname == name:
                continue
            methods.append({"name": fname, "returns": " ".join(owner.split()),
                            "args": " ".join(mm.group(3).split())})
            continue
        # 字段
        fm = re.match(r"^(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?"
                      r"([\w$.<>\[\], ?]+?)\s+([\w$]+)$", body)
        if fm and "(" not in body:
            fields.append({"type": " ".join(fm.group(1).split()), "name": fm.group(2)})
    return {
        "kind": kind if kind != "enum" else "class",
        "name": name,
        "extends": ext,
        "method_count": len(methods),
        "methods": methods,
        "fields": fields,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="抽取 jar 内类/接口的方法签名面（只读）")
    ap.add_argument("--jar", required=True)
    ap.add_argument("--include", default="", help="类名前缀过滤，如 com/seeyon/udc/")
    ap.add_argument("--emit", required=True)
    ap.add_argument("--cfr", default=None, help="cfr jar 路径（不给则跳过反编译路）")
    ap.add_argument("--javap", default=None, help="javap 可执行文件路径")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args(argv)

    jar = Path(a.jar)
    if not jar.exists():
        print(f"ERR: jar 不存在 {jar}", file=sys.stderr)
        return 2

    classes = list_classes(jar, a.include, a.limit)
    if not classes:
        print(f"ERR: 无匹配类（include={a.include!r}）", file=sys.stderr)
        return 3

    javap = resolve_tool(a.javap, "javap")
    cfr = a.cfr if a.cfr and Path(a.cfr).exists() else None

    result = {
        "jar": jar.name,
        "jar_path_hint": jar.parent.name + "/" + jar.name,
        "include": a.include,
        "class_count_scanned": len(classes),
        "routes": [r for r, ok in (("javap", bool(javap)), ("cfr", bool(cfr))) if ok],
        "classes": [],
    }

    tmp = Path(tempfile.mkdtemp(prefix="jarsym_"))
    for entry in classes:
        rec: dict = {"entry": entry}
        # javap 路
        if javap:
            rc, out = run([javap, "-p", "-constants", "-cp", str(jar), entry[:-6].replace("/", ".")], a.timeout)
            rec["javap_rc"] = rc
            if rc == 0:
                rec["javap"] = out.strip()
                parsed = parse_javap(out)
                if parsed["name"]:
                    rec.setdefault("symbols", parsed)
                    rec["symbols_source"] = "javap"
        # cfr 路
        if cfr:
            with zipfile.ZipFile(jar) as z:
                z.extract(entry, tmp)
            rc, out = run(["java", "-jar", cfr, str(tmp / entry)], a.timeout)
            rec["cfr_rc"] = rc
            if rc == 0 and out.strip():
                rec["cfr_source_head"] = "\n".join(out.splitlines()[:400])
                rec["symbols"] = parse_source(out)
                rec["symbols_source"] = "cfr"
        result["classes"].append(rec)

    with_syms = [c for c in result["classes"] if "symbols" in c]
    result["classes_with_symbols"] = len(with_syms)
    result["total_methods"] = sum(c["symbols"]["method_count"] for c in with_syms)
    result["interfaces"] = sum(1 for c in with_syms if c["symbols"]["kind"] == "interface")

    out_p = Path(a.emit)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"jar={jar.name} classes={len(classes)} with_symbols={result['classes_with_symbols']} "
          f"methods={result['total_methods']} interfaces={result['interfaces']} routes={result['routes']}")
    print(f"emit -> {out_p}（{out_p.stat().st_size} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""扫 DTO 的 @DtoAttribute / @DtoInfo，拿到平台自己写的中文字段名、说明、示例值。

为什么这是「怎么填」的权威答案：
    private java.lang.Long templateId;
      @DtoAttribute(
        value="模板ID",
        example="",
        description="模板code/模板ID两者传一个，如果两个都传以模板code为准"
      )
    private java.lang.Long currentUserId;
      @DtoAttribute(value="当前用户ID", example="1",
                    relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto")

比猜字段语义强一万倍。注解定义（com.seeyon.boot.annotation.DtoAttribute）的元素：
  value / description / hidden / xssProcess / dataI18n / relationApp / relationHostAppName /
  relationAppName / relationDto / subRelation / example / sort / customs
类级 com.seeyon.boot.annotation.DtoInfo：value / entity / sort / isPublic / customs

坑：
  · javap 必须带 -p，否则 private 字段整个不输出（-v 单独用看不到字段）
  · javap 输出用系统编码（中文 Windows = GBK），按 utf-8 解会得到「ģ��code」这种乱码

用法：
  python tools/core/platform/scan_dto_meta.py --interfaces <interfaces.json> \
      --emit <dto-meta.json> [--repo <MAVEN_REPO>-extra <MAVEN_REPO>]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"
RE_FIELD = re.compile(r"^\s+(?:private|protected|public)\s+[\w.$<>, \[\]]+\s+([\w$]+);\s*$")
RE_ANNO_START = re.compile(r"^\s+(com\.seeyon\.boot\.annotation\.(?:DtoAttribute|DtoInfo))\(\s*$")
RE_KV = re.compile(r'^\s+(\w+)="(.*)"\s*$')
RE_CLASS = re.compile(r"^(?:public |final |abstract )*(?:class|interface) ([\w.$]+)")


def jar_index(repos: list[Path]) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for r in repos:
        for j in r.rglob("*.jar"):
            try:
                with zipfile.ZipFile(j) as z:
                    for n in z.namelist():
                        if n.endswith(".class") and "$" not in n:
                            idx.setdefault(n[:-6].replace("/", "."), j)
            except Exception:
                continue
    return idx


def decode(raw: bytes) -> str:
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("gbk", "replace")


def scan(jar: Path, fq: str) -> dict:
    try:
        r = subprocess.run([JAVAP, "-p", "-v", "-cp", str(jar), fq],
                           capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {}
    if r.returncode != 0:
        return {}
    lines = decode(r.stdout).splitlines()
    fields: dict[str, dict] = {}
    cls_meta: dict = {}
    cur: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = RE_FIELD.match(line)
        if m:
            cur = m.group(1)
            fields.setdefault(cur, {})
            i += 1
            continue
        m = RE_ANNO_START.match(line)
        if m:
            anno = m.group(1).split(".")[-1]
            kv: dict[str, str] = {}
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(")"):
                mm = RE_KV.match(lines[i])
                if mm:
                    kv[mm.group(1)] = mm.group(2)
                i += 1
            if anno == "DtoAttribute" and cur:
                fields[cur] = kv
            elif anno == "DtoInfo":
                cls_meta = kv
            i += 1
            continue
        i += 1
    out: dict = {}
    if cls_meta:
        out["__class__"] = cls_meta
    real = {k: v for k, v in fields.items()
            if v and k not in ("serialVersionUID",)}
    if real:
        out["fields"] = real
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit", required=True)
    ap.add_argument("--repo", nargs="*", default=["<MAVEN_REPO>-extra", "<MAVEN_REPO>"])
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]
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
    # 嵌套 DTO 也扫（relationDto 指向的那些）
    targets = {t for t in targets if t in cs}
    if a.limit:
        targets = set(sorted(targets)[:a.limit])
    print(f"目标 DTO {len(targets)} 个", flush=True)

    idx = jar_index([Path(x) for x in a.repo])
    print(f"jar 索引 {len(idx)} 类", flush=True)

    result: dict = {}
    miss = 0
    for i, fq in enumerate(sorted(targets), 1):
        jar = idx.get(fq)
        if not jar:
            miss += 1
            continue
        v = scan(jar, fq)
        if v:
            result[fq] = v
        if i % 150 == 0:
            print(f"  {i}/{len(targets)} 有元信息 {len(result)}", flush=True)

    out = {"scanned": len(targets), "with_meta": len(result),
           "not_found": miss, "map": result}
    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(result)}/{len(targets)} 个 DTO 有 @DtoAttribute 元信息（{miss} 找不到）"
          f" → {p}（{p.stat().st_size//1024} KB）")
    for fq in list(result)[:2]:
        v = result[fq]
        print(f"  {fq.split('.')[-1]}: class={v.get('__class__')}")
        for k, fv in list(v.get("fields", {}).items())[:3]:
            print(f"    {k}: {fv}")
    if len(result) < 50:
        print("ERR: 有元信息的 DTO 过少，注解解析可能失效")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

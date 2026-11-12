#!/usr/bin/env python3
"""按域导出 AppService 入参 DTO 的字段表 —— 补上「怎么传参」的最后一块。

方法签名只给到 `SingleResponse<X> send(SingleRequest<BpmSendDto>)`，
但 BpmSendDto 里有哪些字段、什么类型、必填与否，签名里看不到。
本脚本从 interfaces.json 里把这些 DTO 的字段全导出来。

用法：
  python tools/core/platform/emit_dto_fields.py \
      --interfaces <interfaces.json> --emit-dir <dir>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

REQ = re.compile(r"(?:SingleRequest|ListRequest)<\s*([\w.$]+)\s*>")

DOMAIN_TITLES = {
    "bpm": "BPM 流程", "organization": "组织架构", "ctp": "协同（事项/人员/消息）",
    "cip": "连接器", "udc": "UDC 低代码", "boot": "平台基础", "app": "应用通用",
    "m5": "移动端", "portal": "门户", "cdp": "数据平台", "devops": "研发运维",
}


def domain_of(fq: str) -> str:
    parts = fq.split(".")
    if len(parts) >= 3 and parts[0] == "com" and parts[1] == "xiaozhua":
        return parts[2]
    return parts[0]


def field_line(f: dict) -> str:
    mods = f.get("modifiers", "") or ""
    static = "static " if "static" in mods else ""
    t = f.get("type", "")
    return f"| `{f['name']}` | {static}`{t}` |"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit-dir", required=True)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]
    svc = {f: c for f, c in cs.items()
           if c.get("kind") == "interface" and f.split(".")[-1].endswith("AppService")}

    # dto -> [(接口, 方法, 用法)]
    usage: dict[str, list] = collections.defaultdict(list)
    BARE = re.compile(r"([\w.$]+Dto)\b")
    for fq, c in cs.items():
        if c.get("kind") != "interface":
            continue
        for m in c["methods"]:
            sig = m.get("signature", "")
            for t in REQ.findall(sig):
                usage[t.split("<")[0]].append((fq, m["name"], "包装入参"))
            # 裸参数：`upload(StorageUploadRequestDto)` 这种没包 SingleRequest 的。
            # 只看参数列表，避免把 SingleResponse<XxxResultDto> 的返回类型也当入参。
            lo, hi = sig.find("("), sig.find(")")
            args = sig[lo + 1:hi] if 0 <= lo < hi else ""
            for t in BARE.findall(args):
                if t not in usage or all(u[1] != m["name"] for u in usage[t]):
                    usage[t].append((fq, m["name"], "裸参数"))

    by_domain: dict[str, dict[str, list]] = collections.defaultdict(dict)
    missing = []
    for dto, uses in usage.items():
        c = cs.get(dto)
        if not c or not c.get("fields"):
            missing.append(dto)
            continue
        by_domain[domain_of(dto)][dto] = (c, uses)

    outdir = Path(a.emit_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    index = ["# AppService 入参 DTO 字段表（索引）", "",
             "> 自动生成，勿手改。`tools/core/platform/emit_dto_fields.py` 重跑即可。",
             "> 用法：方法签名里看到 `SingleRequest<XxxDto>` → 到本目录对应域文件查 `XxxDto` 的字段。",
             "",
             "| 域 | 文件 | DTO 数 | 被引用的方法数 |", "|---|---|---|---|"]
    total = 0
    for dom, dtos in sorted(by_domain.items(), key=lambda x: -len(x[1])):
        title = DOMAIN_TITLES.get(dom, dom)
        lines = [f"# {title}：入参 DTO 字段表", "",
                 f"> 自动生成。包前缀 `com.seeyon.{dom}`。共 {len(dtos)} 个 DTO。",
                 "> 字段类型逐字来自 javap；`static` 前缀表示常量而非实例字段。", ""]
        for dto in sorted(dtos, key=lambda x: (-len(cs[x]["fields"]), x)):
            c, uses = dtos[dto]
            lines.append(f"## `{dto.split('.')[-1]}`（{len(c['fields'])} 字段）")
            lines.append("")
            lines.append(f"`{dto}`")
            lines.append("")
            lines.append("被这些方法当入参：")
            lines.append("")
            for ifq, meth, kind in uses[:6]:
                lines.append(f"- `{ifq.split('.')[-1]}.{meth}()`（{kind}）")
            if len(uses) > 6:
                lines.append(f"- … 另 {len(uses)-6} 处")
            lines.append("")
            lines.append("| 字段 | 类型 |")
            lines.append("|---|---|")
            for f in c["fields"]:
                lines.append(field_line(f))
            lines.append("")
        p = outdir / f"{dom}.md"
        p.write_text("\n".join(lines), encoding="utf-8")
        n_meth = sum(len(v[1]) for v in dtos.values())
        index.append(f"| {title} | `{dom}.md` | {len(dtos)} | {n_meth} |")
        total += len(dtos)
        print(f"  {dom:14s} {len(dtos):4d} DTO / {n_meth:5d} 处引用 → {p.name}（{p.stat().st_size//1024} KB）")

    index += ["", f"合计 **{total} 个 DTO**；{len(missing)} 个 DTO 在索引里查不到字段"
              "（多为外部 jar 或纯接口，按需反编译）。"]
    (outdir / "README.md").write_text("\n".join(index), encoding="utf-8")
    print(f"\n合计 {total} 个 DTO / 缺字段 {len(missing)} 个")
    if missing[:5]:
        print("  缺字段样例:", ", ".join(x.split(".")[-1] for x in missing[:5]))
    if total < 500:
        print("ERR: DTO 数过少，抽取口径可能坏了")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

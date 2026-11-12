#!/usr/bin/env python3
"""按业务动作生成索引：动作 → 入口方法 → 入参 DTO → 是否可追流转 → 流转要点。

解决什么问题：2258 个 AppService 方法散在 91 个构件里，写扩展时想知道
「我要做 X 这件事，该调哪个方法、传什么、背后会发生什么」。

三类证据合一：
  interfaces.json      → 方法签名 + 入参 DTO + 实现类
  dto-fields/*.md      → DTO 字段（指向，不重复）
  service-flow/*.md    → 实现类方法体的调用链

诚实边界：322 个 AppService 里只有 68 个在仓库有实现类（46 个在 udc-biz），
其余 254 个的实现在平台服务端，**流转追不到**，只给接口 + DTO。

用法：
  python tools/core/platform/emit_action_index.py \
      --interfaces <interfaces.json> --flow-dir <service-flow 目录> --emit <action-index.md>
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REQ = re.compile(r"(?:SingleRequest|ListRequest)<\s*([\w.$]+)\s*>")
RE_FLOW_CLASS = re.compile(r"^## `([\w$]+)`\s*$", re.M)
RE_FLOW_METHOD = re.compile(r"^### `([\w$]+)\(\)`\s*$", re.M)
RE_FLOW_LINE = re.compile(r"^- \*\*(\w+)\*\* `([\w$]+)` → (.+)$")

GROUPS = [
    ("创建", ["create", "save", "add", "insert", "new", "init"]),
    ("修改", ["update", "modify", "edit", "set", "change"]),
    ("删除", ["delete", "remove", "del", "clear", "cancel"]),
    ("流程", ["send", "submit", "approve", "reject", "back", "stop", "revoke",
              "finish", "complete", "repeal", "takeback"]),
    ("发布", ["deploy", "publish", "build", "release", "upgrade", "shelf"]),
    ("导入导出", ["import", "export", "transfer", "transport", "copy", "saveas"]),
    ("校验", ["check", "validate", "verify", "detection", "exist", "has"]),
    ("启用禁用", ["enable", "disable", "start", "pause", "resume"]),
    ("查询", ["get", "query", "select", "list", "find", "search", "page",
              "count", "load", "fetch"]),
]


def action_of(name: str) -> str:
    m = re.match(r"[a-z]+", name)
    v = m.group(0) if m else ""
    for g, keys in GROUPS:
        if any(v.startswith(k) for k in keys):
            return g
    return "其他"


def parse_flow(md: str) -> dict[tuple[str, str], list[str]]:
    """从 service-flow md 解出 (类短名, 方法名) → [调用摘要]。"""
    out: dict[tuple[str, str], list[str]] = {}
    cur_cls = None
    cur_meth = None
    for line in md.splitlines():
        m = RE_FLOW_CLASS.match(line)
        if m:
            cur_cls, cur_meth = m.group(1), None
            continue
        m = RE_FLOW_METHOD.match(line)
        if m and cur_cls:
            cur_meth = m.group(1)
            out[(cur_cls, cur_meth)] = []
            continue
        m = RE_FLOW_LINE.match(line)
        if m and cur_cls and cur_meth:
            kind, target, meths = m.group(1), m.group(2), m.group(3)
            out[(cur_cls, cur_meth)].append(f"{kind}:{target}({meths.split(',')[0].strip()})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--flow-dir", required=True)
    ap.add_argument("--impl-map", default=None,
                    help="build_impl_map.py 的产物。平台命名不规则"
                         "（BpmAppService 的实现叫 BpmApiAppServiceImpl），必须读字节码映射。")
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]
    svc = {f: c for f, c in cs.items()
           if c.get("kind") == "interface" and f.split(".")[-1].endswith("AppService")}

    # 接口 → 实现类短名：先 interfaces.json，再 impl-map（读字节码，覆盖 CHIT-extra 的实现 jar）
    impl_of: dict[str, str] = {}
    for fq, c in cs.items():
        for i in (c.get("implements") or []):
            base = i.split("<")[0]
            if base in svc:
                impl_of[base] = fq.split(".")[-1]
    if a.impl_map:
        m = json.loads(Path(a.impl_map).read_text(encoding="utf-8"))["map"]
        for iface, impls in m.items():
            if iface in svc and impls:
                impl_of.setdefault(iface, impls[0]["impl"])

    flow: dict[tuple[str, str], list[str]] = {}
    fd = Path(a.flow_dir)
    for f in fd.glob("*.md"):
        flow.update(parse_flow(f.read_text(encoding="utf-8", errors="replace")))

    buckets: dict[str, list[dict]] = defaultdict(list)
    for fq, c in svc.items():
        short = fq.split(".")[-1]
        impl = impl_of.get(fq)
        # interfaces.json 只覆盖 68 个实现（<MAVEN_REPO>）。
        # 实现 jar（bpm-biz/organization-biz 等，<MAVEN_REPO>-extra）不在索引里，
        # 按平台命名规则 XxxAppService → XxxAppServiceImpl 兜底，且必须在 flow 里真出现过。
        cand = short[:-len("AppService")] + "AppServiceImpl" if short.endswith("AppService") else None
        for m in c["methods"]:
            req = REQ.search(m.get("signature", ""))
            dto = req.group(1).split(".")[-1] if req else ""
            use_impl = impl
            if not use_impl and cand and (cand, m["name"]) in flow:
                use_impl = cand
            chain = flow.get((use_impl, m["name"]), []) if use_impl else []
            buckets[action_of(m["name"])].append({
                "iface": short, "meth": m["name"], "dto": dto,
                "impl": use_impl or "", "chain": chain,
            })

    total = sum(len(v) for v in buckets.values())
    with_impl = sum(1 for v in buckets.values() for x in v if x["impl"])
    with_flow = sum(1 for v in buckets.values() for x in v if x["chain"])

    out = [
        "# 业务动作索引：要做什么 → 调哪个方法 → 传什么 → 背后发生什么",
        "",
        "> 自动生成，勿手改。`tools/core/platform/emit_action_index.py` 重跑即可。",
        f"> 数据源：`interfaces.json`（{len(svc)} 个 AppService / {total} 个方法）"
        f"+ `service-flow-20261103/`（方法体调用链）。",
        "",
        "## 覆盖现实（先看这段，别指望全部能追）",
        "",
        "| 项 | 数量 | 说明 |",
        "|---|---|---|",
        f"| AppService 方法总数 | **{total}** | 322 个接口 |",
        f"| 仓库里有实现类 | **{with_impl}** | 68 个接口（46 个在 udc-biz） |",
        f"| 能追到方法体流转 | **{with_flow}** | 其余实现在平台服务端，jar 里只有接口 |",
        "",
        "⇒ **BPM / 组织架构 / 事项 / 连接器 的实现在平台服务端**，仓库里只有接口 jar，",
        "流转追不到。这些域只能给「接口 + 入参 DTO」，具体动作要实测或看平台日志。",
        "**UDC 域（46 个 AppService）能追全链**。",
        "",
        "## 动作分布",
        "",
        "| 动作 | 方法数 | 有实现 | 有流转 |",
        "|---|---|---|---|",
    ]
    for g, _ in GROUPS + [("其他", [])]:
        items = buckets.get(g, [])
        if not items:
            continue
        out.append(f"| {g} | {len(items)} | {sum(1 for x in items if x['impl'])} | "
                   f"{sum(1 for x in items if x['chain'])} |")
    out.append("")

    # 核心动作逐条列；查询类按接口聚合
    for g, _ in GROUPS:
        items = buckets.get(g, [])
        if not items:
            continue
        out += [f"## {g}（{len(items)}）", ""]
        if g == "查询":
            agg: dict[str, list[str]] = defaultdict(list)
            for x in items:
                agg[x["iface"]].append(x["meth"])
            out += ["查询类 1197 个方法太碎，按接口聚合（完整签名去 `packages/` 查）：", "",
                    "| 接口 | 方法数 | 方法 |", "|---|---|---|"]
            for iface, meths in sorted(agg.items(), key=lambda x: -len(x[1])):
                show = ", ".join(f"`{m}`" for m in meths[:6])
                if len(meths) > 6:
                    show += f" … 另 {len(meths)-6}"
                out.append(f"| `{iface}` | {len(meths)} | {show} |")
            out.append("")
            continue
        out += ["| 动作方法 | 接口 | 入参 DTO | 实现 | 流转（第一步） |", "|---|---|---|---|---|"]
        for x in sorted(items, key=lambda y: (not y["chain"], y["iface"], y["meth"])):
            impl = f"`{x['impl']}`" if x["impl"] else "平台服务端"
            chain = x["chain"][0] if x["chain"] else ("—" if not x["impl"] else "见 flow 文件")
            dto = f"`{x['dto']}`" if x["dto"] else "—"
            out.append(f"| `{x['meth']}` | `{x['iface']}` | {dto} | {impl} | {chain} |")
        out.append("")

    out += ["## 怎么用", "",
            "```",
            "① 我要做某件事 → 在本文件找对应动作分组",
            "② 找到入口方法 → 记下接口名和入参 DTO",
            "③ DTO 有什么字段 → dto-fields/<域>.md",
            "④ 背后发生什么 → service-flow-20261103/<构件>.md 搜那个实现类",
            "⑤ 完整签名 → packages/<构件>.md 或 domains/<域>.md",
            "```", "",
            "## 缺口",
            "",
            "- 254 个 AppService 无实现类 → 流转 UNVERIFIED（实现在平台服务端）",
            "- 「其他」类动作（392 个）多为 `batch*` / `dynamic*` / `process*` 前缀，未归类",
            "- 流转只给第一步调用，完整链路见 flow 文件",
            ""]

    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"action-index  {total} 方法 / 有实现 {with_impl} / 有流转 {with_flow} → {p}（{p.stat().st_size//1024} KB）")
    for g, _ in GROUPS + [("其他", [])]:
        if buckets.get(g):
            print(f"  {g:6s} {len(buckets[g]):5d}")
    if with_flow < 100:
        print("WARN: 能追流转的方法过少，flow 解析可能失效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

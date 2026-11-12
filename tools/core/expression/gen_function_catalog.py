# -*- coding: utf-8 -*-
"""gen_function_catalog.py — 从 preset/list 原文生成函数用法目录

产出 core/facts/udc/expression/functions.md：
  按 8 个分组，每个函数列出 参数 / 说明 / 示例。
这是"每个函数都有自己的用法"的落地件，避免每次现查。
"""
import json
from pathlib import Path

REPO = Path(r"<SEEYON_AGENT_ROOT>")
SRC = Path(r"<HERMES_HOME>\cache\scratch\expression_preset.json")

doc = json.loads(SRC.read_text(encoding="utf-8"))
content = doc["data"]["content"]
groups = content.get("functionInfo") or []

lines = [
    "# 表达式函数用法目录（88 个 / 8 组）",
    "",
    "> 证据等级：**LIVE**（`POST /service/udc/expression/preset/list`，",
    "> test2 2026-10-23，`terminalSupportType=BACKEND`）",
    "> 生成器：`tools/core/expression/gen_function_catalog.py`（勿手改本文件，改生成器）",
    ">",
    "> ⚠ `BACKEND` 88 个；`FRONTEND` 只要 81 个（缺「变化函数」「枚举函数」两组，",
    "> 且「基础函数」从 15 降到 11）。见 `terminal.py`。",
    ">",
    "> 用法：函数 token 的 `value` 用下表 `函数名`，`subOps` 按参数顺序给二维数组；",
    "> 参数是变量时必须带 `uniformityParams.paramId`。",
    "",
    "## 总览",
    "",
    "| 分组 | 数量 | 函数 |",
    "|---|---|---|",
]
for g in groups:
    fs = g.get("functions") or []
    lines.append("| %s | %d | %s |" % (
        g.get("categoryName"), len(fs),
        "、".join(str(f.get("name")) for f in fs)))

lines += ["", "---", ""]

for g in groups:
    cat = g.get("categoryName")
    fs = g.get("functions") or []
    lines += ["## %s（%d）" % (cat, len(fs)), ""]
    for f in fs:
        name = f.get("name")
        desc = f.get("description") or ""
        params = f.get("parameters") or []
        ex = (f.get("explain") or {}) or {}
        lines.append("### `%s` — %s" % (name, desc))
        # 参数
        if params:
            pdesc = []
            for p in params:
                d = p.get("description") or "?"
                agg = p.get("isAggregationProperty")
                pdesc.append("%s%s" % (d, "（聚合属性）" if agg else ""))
            lines.append("")
            lines.append("参数：`%s`" % " / ".join(pdesc))
        else:
            lines.append("")
            lines.append("参数：无")
        # 说明
        u = ex.get("useage") or ex.get("description")
        if u and u != desc:
            lines.append("")
            lines.append("说明：%s" % u)
        # 示例
        e = ex.get("example") or {}
        if e:
            args = e.get("args") or []
            types = e.get("argTypes") or []
            tips = e.get("tips") or ""
            sig = "%s(%s)" % (name, ", ".join(str(a) for a in args))
            lines.append("")
            lines.append("示例：`%s`%s" % (
                sig, ("　参数类型：" + " / ".join(str(t) for t in types)) if types else ""))
            if tips:
                lines.append("")
                lines.append("→ %s" % tips)
        lines.append("")

out = REPO / "core" / "facts" / "udc" / "expression" / "functions.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("已生成 %s" % out)
print("函数总数 %d / 分组 %d" % (sum(len(g.get('functions') or []) for g in groups), len(groups)))
print("行数 %d" % len(lines))

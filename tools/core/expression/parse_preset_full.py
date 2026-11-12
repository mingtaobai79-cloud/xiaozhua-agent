# -*- coding: utf-8 -*-
"""parse_preset_full.py — 解析桌面那份完整 preset/list 原文

产出：
  core/facts/udc/expression/system-variables.md   131 项系统变量，按组带类型
  并核对：函数 88 / 组 8、变量 131 / 组 4 是否与既有抓取一致
"""
import json
import os
from collections import Counter
from pathlib import Path

# 源文件：用户提供的 preset/list 完整原文（放在桌面）
# 用 USERPROFILE 取，避免把本机用户名写进仓库（脱敏闸门会拦）
SRC = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop" / "新建 文本文档.txt"
OUT_DIR = Path(r"<SEEYON_AGENT_ROOT>\core\facts\udc\expression")

raw = SRC.read_text(encoding="utf-8-sig", errors="replace")
doc = json.loads(raw)
content = doc["data"]["content"]
groups = content.get("presetVariableInfo") or []
funcs = content.get("functionInfo") or []

print("变量组 %d / 变量项 %d" % (len(groups), sum(len(g.get("items") or []) for g in groups)))
print("函数组 %d / 函数项 %d" % (len(funcs), sum(len(g.get("functions") or []) for g in funcs)))

# 类型分布
types = Counter()
for g in groups:
    for it in (g.get("items") or []):
        types[it.get("resultType")] += 1
print("变量 resultType 分布:", dict(types))

hidden = sum(1 for g in groups for it in (g.get("items") or []) if it.get("hidden"))
print("hidden 项:", hidden)

lines = [
    "# 表达式系统变量目录（131 项 / 4 组）",
    "",
    "> 证据等级：**LIVE**（`POST /service/udc/expression/preset/list`，",
    "> `terminalSupportType=BACKEND`，test2，2026-10-23 完整原文）",
    "> 原文：用户提供的完整响应（3989 行 / 204KB），本文件由",
    "> `tools/core/expression/parse_preset_full.py` 生成，勿手改。",
    ">",
    "> ★ 系统变量与 `terminalSupportType` **无关**：BACKEND / FRONTEND / ALL 三档都是 131 项。",
    ">   只有函数面被裁剪（88 / 81）。",
    ">",
    "> ★ 两条解析通路不等价（既有事实）：",
    ">   `name` 全名（`system.currentDateTime`）取其 `resultType`；",
    ">   短名（`functionName`）只要同名于某函数就被当函数调用、取函数返回类型。",
    ">   需要稳定类型时用 `name`，别用短名。",
    "",
    "## 总览",
    "",
    "| 分组 | 名称 | 数量 |",
    "|---|---|---|",
]
for g in groups:
    lines.append("| %s | %s | %d |" % (g.get("name"), g.get("description"),
                                       len(g.get("items") or [])))

lines += ["", "## resultType 分布", "", "| 类型 | 数量 |", "|---|---|"]
for t, n in sorted(types.items(), key=lambda x: -x[1]):
    lines.append("| %s | %d |" % (t, n))
if hidden:
    lines += ["", "其中 `hidden=true` 的 %d 项（界面默认不显示，但接口仍返回，可直接引用）。" % hidden]

lines += ["", "---", ""]
for g in groups:
    items = g.get("items") or []
    lines += ["## %s（%s）— %d 项" % (g.get("name"), g.get("description"), len(items)), ""]
    lines += ["| 全名 | 说明 | 短名 | 结果类型 | 关联实体 | hidden |",
              "|---|---|---|---|---|---|"]
    for it in items:
        lines.append("| `%s` | %s | `%s` | %s | %s | %s |" % (
            it.get("name"), it.get("description") or "",
            it.get("functionName") or "",
            it.get("resultType") or "",
            (it.get("relationEntity") or "").split(".")[-1] or "-",
            "是" if it.get("hidden") else "",
        ))
    lines.append("")

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "system-variables.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n已生成 %s（%d 行）" % (out, len(lines)))

# 与既有抓取核对
prev = Path(r"<HERMES_HOME>\cache\scratch\expression_preset.json")
if prev.exists():
    p = json.loads(prev.read_text(encoding="utf-8"))["data"]["content"]
    pf = sum(len(g.get("functions") or []) for g in (p.get("functionInfo") or []))
    pv = sum(len(g.get("items") or []) for g in (p.get("presetVariableInfo") or []))
    print("\n核对既有抓取: 函数 %d / 变量 %d → %s" % (
        pf, pv,
        "一致 ✅" if (pf, pv) == (
            sum(len(g.get("functions") or []) for g in funcs),
            sum(len(g.get("items") or []) for g in groups)) else "不一致 ❌"))

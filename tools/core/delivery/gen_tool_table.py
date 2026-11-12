# -*- coding: utf-8 -*-
"""从 docs/delivery/tool-status.json 生成 README 的工具清单表。

为什么要有这个脚本：
  54 个工具的状态靠手抄一定会漂（本轮就发生过：把 option_set_body /
  option_set_item_body 标成已验，其实 batch1 只验了它们的分类）。
  清单只允许有一个真相源 —— tool-status.json，表格一律生成。

用法：
  python tools/core/delivery/gen_tool_table.py            # 打印 markdown
  python tools/core/delivery/gen_tool_table.py --write     # 回写到 README 标记区
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATUS = ROOT / "docs" / "delivery" / "tool-status.json"
README = ROOT / "README.md"

BEGIN = "<!-- BEGIN GENERATED:TOOL-TABLE -->"
END = "<!-- END GENERATED:TOOL-TABLE -->"

KIND_LABEL = {
    "local": "本地",
    "read": "只读",
    "write": "写",
    "delete": "删",
}
STATUS_LABEL = {
    "VERIFIED": "✅ 已验证",
    "UNVERIFIED": "⚠ 未验证",
    "PARTIAL": "◐ 部分验证",
    "NEEDS_AUTH": "🔒 需授权",
    "BROKEN": "❌ 已知不通",
}


def _cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def render() -> str:
    doc = json.loads(STATUS.read_text(encoding="utf-8"))
    tools = doc["tools"]

    by_status: dict[str, int] = {}
    for t in tools:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1

    plat = [t for t in tools if t["kind"] != "local"]
    local = [t for t in tools if t["kind"] == "local"]
    plat_v = [t for t in plat if t["status"] == "VERIFIED"]

    lines: list[str] = []
    lines.append(BEGIN)
    lines.append("")
    lines.append(
        "> 本表由 `tools/core/delivery/gen_tool_table.py` 从 "
        "`docs/delivery/tool-status.json` 生成，**不要手改**。"
    )
    lines.append("")
    lines.append(
        "合计 **%d** 个工具：平台侧 %d 个（其中 **%d** 个真机验证过），"
        "本地工具 %d 个。" % (len(tools), len(plat), len(plat_v), len(local))
    )
    lines.append("")
    lines.append("| 状态 | 数量 |")
    lines.append("|---|---:|")
    for k in ("VERIFIED", "PARTIAL", "UNVERIFIED", "NEEDS_AUTH", "BROKEN"):
        if by_status.get(k):
            lines.append("| %s | %d |" % (STATUS_LABEL[k], by_status[k]))
    lines.append("")
    lines.append("### 平台工具")
    lines.append("")
    lines.append("| 工具 | 类型 | 需授权 | 状态 | 说明 / 阻塞原因 |")
    lines.append("|---|---|:---:|---|---|")
    for t in plat:
        why = t.get("blocker") or t.get("note") or ""
        if t.get("danger"):
            why = "⚠ " + t["danger"] + ("；" + why if why else "")
        lines.append(
            "| `%s` | %s | %s | %s | %s |"
            % (
                t["key"],
                KIND_LABEL.get(t["kind"], t["kind"]),
                "是" if t.get("auth") else "—",
                STATUS_LABEL[t["status"]],
                _cell(why),
            )
        )
    lines.append("")
    lines.append("### 本地工具（不连平台，装上即可用）")
    lines.append("")
    lines.append("| 工具 | 类型 | 需授权 | 状态 | 说明 |")
    lines.append("|---|---|:---:|---|---|")
    for t in local:
        lines.append(
            "| `%s` | %s | %s | %s | %s |"
            % (
                t["key"],
                KIND_LABEL.get(t["kind"], t["kind"]),
                "是" if t.get("auth") else "—",
                STATUS_LABEL[t["status"]],
                _cell(t.get("note") or ""),
            )
        )
    lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    table = render()
    if "--write" not in argv:
        print(table)
        return 0

    text = README.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print("README 里找不到生成标记，先手工插入：\n%s\n...\n%s" % (BEGIN, END),
              file=sys.stderr)
        return 2
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    README.write_text(head + table + tail, encoding="utf-8")
    print("已回写 README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

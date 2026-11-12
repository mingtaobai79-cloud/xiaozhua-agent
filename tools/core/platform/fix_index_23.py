#!/usr/bin/env python3
"""INDEX.md 加第 23 格（接口使用卡）。"""
from pathlib import Path

P = Path("<XIAOZHUA_AGENT_ROOT>/core/facts/INDEX.md")
NEW = (
    "㉓`api-usage-cards.md` **接口使用卡**（拿到就能调：一页一接口——接口全名 + 实现类 + "
    "每个方法的签名/入参 DTO 逐字段/返回 DTO 逐字段/流转第一步 + 泛化调用五个值怎么填；"
    "产物 `docs/audit/artifacts/api-usage/` 11 个域文件 3 MB；**关键突破**：平台不用 "
    "javax.validation，用自定义 `@DtoAttribute(value/description/example/relationDto)` "
    "写了字段中文名/示例/业务规则——如 `templateId ← 模板ID · 模板code/模板ID两者传其一，"
    "如果都传以模板code为准`，1331 个 DTO 里 1305 个有元信息（98%）；两个坑：javap 必须带 -p "
    "否则 private 字段注解全丢、输出是 GBK 按 utf-8 解会乱码；`value` 不总是中文名"
    "（`currentUserId` 的 value 是 `userCode`），靠 example/relationDto 补；必填无注解可依，"
    "只能从 description 措辞判断或实测）。"
)


def main() -> int:
    t = P.read_text(encoding="utf-8")
    t = t.replace("| standard-product | 22 格平台能力（包用法，环境无关） |",
                  "| standard-product | 23 格平台能力（包用法，环境无关） |")
    if "㉓" in t:
        print("已存在 ㉓")
        return 0
    anchor = "证据 `docs/audit/artifacts/extension-surface-20261029"
    i = t.find(anchor)
    if i == -1:
        print("ERR: 找不到锚点")
        return 5
    t = t[:i] + NEW + t[i:]
    P.write_text(t, encoding="utf-8")
    print("已插入 ㉓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

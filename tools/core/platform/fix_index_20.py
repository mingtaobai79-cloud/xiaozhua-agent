#!/usr/bin/env python3
"""修复 INDEX.md 里被 bash 反引号吃掉的 ⑳ 条目（改用脚本写，避开 shell 引号）。"""
from pathlib import Path

P = Path("<XIAOZHUA_AGENT_ROOT>/core/facts/INDEX.md")
NEW = (
    "⑳`service-business-flow.md` **Service 业务流转**（方法背后动了什么：两层结构——"
    "`XxxAppServiceImpl` 只做一行转发、真正业务在 `domain/service/XxxService`"
    "（是具体类不是 Impl，只扫 `*Impl` 会漏掉整个业务层）；反编译方法体提 Dao/Service/Util/Event 四类调用——"
    "`udc-biz-appservice.md` 83 类 151KB、`udc-biz-domain.md` 265 类 646KB"
    "（Dao 706/Service 1099/Util 4355/Event 261）、客户应用 `znxmglpt…-biz.md` 458 类 2.4MB / "
    "`xiangmuguanli…` 130 类 / `datamigration…` 27 类；典型流转三形态：查询组装"
    "（Wrapper→Dao.selectListByWrapper→MultiThreadTransaction.executeSplit）、事件驱动"
    "（DetectionProperties 开关→PartDetectionDeleteEvent.builder→EventBus.publishAfterTransaction 事务后发）、"
    "客户应用生成式骨架（校验→Dto转Entity→Dao.insert→触发特性）；**拿不到**：业务规则语义、"
    "真实 SQL（109 jar 仅 8 个 mapper XML，走 dynamicsql 动态拼）、分支走向）。"
)


def main() -> int:
    t = P.read_text(encoding="utf-8")
    i = t.find("⑳")
    if i == -1:
        print("ERR: 找不到 ⑳")
        return 5
    # ⑳ 段结束于后面的「证据 `docs/audit/artifacts/extension-surface-20261029」
    j = t.find("证据 `docs/audit/artifacts/extension-surface-20261029", i)
    if j == -1:
        print("ERR: 找不到段尾")
        return 5
    old = t[i:j]
    t = t[:i] + NEW + t[j:]
    P.write_text(t, encoding="utf-8")
    print(f"已替换 {len(old)} 字符 → {len(NEW)} 字符")
    print("新内容预览:", t[i:i + 120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

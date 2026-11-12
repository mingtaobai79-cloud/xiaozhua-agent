#!/usr/bin/env python3
"""统一 UDC 接口口径：274 = 250 真接口 + 24 注解；250 = 55 AppService + 128 扩展点 + 67 无 abstract。"""
from __future__ import annotations

from pathlib import Path

FD = Path("<XIAOZHUA_AGENT_ROOT>/core/facts/standard-product")

OLD_79 = """数据源 `interfaces.json`（91 个构件）：**1145 个接口**，其中 845 个带 abstract。
人读全量清单 `interface-inventory.md`（1017 行）；扩展点 × 平台实现落地表
`extension-points.md`。

UDC 自己 **151 个带 abstract 的接口**（已排除 26 个 `*AppService` 调用面），分两种性质：
**128 个是真接口**（101 个平台已有实现、27 个纯扩展位）+ **23 个是注解**（`@interface`，"""

NEW_79 = """数据源 `interfaces.json`（91 个构件）：**1145 个接口** = **1036 个真接口** + **109 个注解**
（`@interface` 不能 implements）。真接口里 **755 个带 abstract** = 真正可 implements 的。
人读全量清单 `interface-inventory.md`；扩展点 × 平台实现落地表 `extension-points.md`。

**UDC 侧口径链（四个数别混）**：

```
274 个 UDC 接口 = 250 个真接口 + 24 个注解
250 个真接口   = 55 个 *AppService（调用面，你调它，不实现它）
               + 195 个其他
195 个其他     = 128 个带 abstract（= 扩展点，可实现）+ 67 个无 abstract（标记 / 纯 default）

⇒ 128 扩展点 + 23 注解 = 151 个带 abstract 的接口
   （55 个 AppService 也全带 abstract，但它们是调用面，不计入扩展点）
```

**151 个带 abstract 的接口**分两种性质：
**128 个是真接口**（101 个平台已有实现、27 个纯扩展位）+ **23 个是注解**（`@interface`，"""


def main() -> int:
    # ① 主口径段
    p = FD / "udc-microflow-extend-interfaces.md"
    t = p.read_text(encoding="utf-8")
    if OLD_79 in t:
        p.write_text(t.replace(OLD_79, NEW_79), encoding="utf-8")
        print("  udc-microflow-extend-interfaces.md §7.9 口径已重写")
    elif "274 个 UDC 接口 = 250 个真接口" in t:
        print("  udc-microflow-extend-interfaces.md 已是新口径")
    else:
        print("  WARN: udc-microflow-extend-interfaces.md 未匹配，人工核对")

    # ② 引用面格：183 的口径说明
    p = FD / "extension-point-consumers.md"
    t = p.read_text(encoding="utf-8")
    old = ("本格给出 183 个 UDC 接口在 12252 个 class 常量池里的引用统计，按证据强度分三级。")
    new = ("本格给出 **183 个 UDC 真接口**（= 128 个扩展点 + 55 个 `*AppService` 调用面，"
           "两者都带 abstract）在 12252 个 class 常量池里的引用统计，按证据强度分三级。")
    if old in t:
        p.write_text(t.replace(old, new), encoding="utf-8")
        print("  extension-point-consumers.md 已补 183 的口径")
    else:
        print("  WARN: consumers 口径未匹配")

    p = FD / "extension-point-consumers.md"
    t = p.read_text(encoding="utf-8")
    old2 = "| **跨包引用（cross）** | **154** | 其他 jar 里的类引用了这个接口 |"
    if "55 个 `*AppService`" not in t and old2 in t:
        print("  WARN: consumers 头部未更新")
    # ③ 决策表格：加口径脚注
    p = FD / "extension-point-decision-table.md"
    t = p.read_text(encoding="utf-8")
    anchor = "### 7.1"
    note = ("**口径**：`interfaces.json` 里 UDC 有 274 个接口 = 250 真接口 + 24 注解；"
            "真接口里 55 个是 `*AppService` 调用面（你调它）、128 个带 abstract 是扩展点（你实现它）、"
            "67 个无 abstract 是标记/纯 default。本表只讲这 128 个。\n\n")
    if "本表只讲这 128 个" not in t:
        i = t.find(anchor)
        if i != -1:
            t = t[:i] + note + t[i:]
            p.write_text(t, encoding="utf-8")
            print("  extension-point-decision-table.md 已加口径脚注")
    else:
        print("  extension-point-decision-table.md 已有口径脚注")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

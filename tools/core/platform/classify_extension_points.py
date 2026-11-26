#!/usr/bin/env python3
"""给 UDC 扩展点分档：plain（普通 implements）/ plugin（插件式）/ spi（平台 SPI）。

## 为什么要分

150 个「UDC 扩展点」名字上都叫接口，但落到工程上是三种完全不同的东西：

| 档 | 形态 | 代码 | 生成/注册格式 |
|---|---|---|---|
| plain | 一个类 implements 接口 | `extend/` 下写实现 | 放进去即可（平台内部扫描） |
| plugin | 插件描述符（`PluginDefinition`） | 一个类实现描述符，向平台交出 CodeTasks / PomDependencies / TransportHandlers / Detections | 插件 jar（机制**未取证**） |
| spi | 平台 SPI 插件（`cip-connector-api` 等） | 一个类 implements 扩展点 | `META-INF/spring.factories` + `metadata/spi_info.json` + Nacos `seeyon.spi.enable/spi-plugins` |

混在一张表里，等于让写代码的人按 plain 的方式去写 plugin / spi —— 格式一对不上就加载不到。

## 判据（只用可复核的包名/类名，不猜语义）

- `spi`  ：接口全名含 `.spi.` / `cip.connector` / 以 `Provider` 结尾
- `plugin`：接口全名等于 `com.seeyon.udc.PluginDefinition`，或包名含 `.plugin`
- `plain` ：其余

输入：`extension-points.md`（平台/实现落的落地表）
输出：`extension-points-classified.json`（机器可读，带 category 与 registration）

用法：
  python tools/core/platform/classify_extension_points.py \
      --points docs/audit/artifacts/extension-surface-20261118/extension-points.md \
      --emit   docs/audit/artifacts/extension-surface-20261118/extension-points-classified.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

PLUGIN_FQNS = {"com.seeyon.udc.PluginDefinition"}

REGISTRATION = {
    "plain": "类 implements 接口，放客开工程 extend/（平台侧自行扫描，无 spring.factories / 无 META-INF/services）",
    "plugin": "插件 jar：实现 PluginDefinition 交出 CodeTasks/PomDependencies/TransportHandlers/Detections；发现机制 UNVERIFIED（udc-plugin-api 内无 spring.factories / META-INF/services）",
    "spi": "插件 jar + META-INF/spring.factories（接口FQN=实现类FQN）+ metadata/spi_info.json + Nacos seeyon.spi.enable/spi-plugins",
}


def classify(fqn: str) -> str:
    low = fqn.lower()
    if fqn in PLUGIN_FQNS or ".plugin" in low:
        return "plugin"
    if ".spi." in low or "cip.connector" in low or fqn.endswith("Provider"):
        return "spi"
    return "plain"


def parse_points(md: str) -> list[dict]:
    """表格列：接口 | abstract | impl | 代表实现类 | 包。第二节少一列（无 impl）。"""
    out: list[dict] = []
    for line in md.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        name = cells[0].strip("`")
        try:
            abstract = int(cells[1])
        except ValueError:
            continue
        impl = 0
        if len(cells) >= 5:              # 第一节：有 impl 列
            try:
                impl = int(cells[2])
            except ValueError:
                impl = 0
            pkg = cells[-1].strip("`")
        else:                             # 第二节：接口 | abstract | 包
            pkg = cells[-1].strip("`")
        fqn = f"{pkg}.{name}" if pkg and not pkg.endswith(name) else name
        out.append({"name": name, "package": pkg, "fqn": fqn,
                    "abstract": abstract, "impl": impl,
                    "category": classify(fqn)})
    # 同名不同包会重复出现（BaseNode / BaseTrigger / Functor），用 fqn 去重
    seen: dict[str, dict] = {}
    for p in out:
        seen.setdefault(p["fqn"], p)
    return list(seen.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    src = Path(a.points)
    md = src.read_text(encoding="utf-8")
    pts = parse_points(md)
    if not pts:
        print("ERR: 一个扩展点都没解析出来，表格结构变了")
        return 5

    by_cat = collections.Counter(p["category"] for p in pts)
    payload = {
        "source": str(src.as_posix()),
        "total": len(pts),
        "counts": dict(by_cat),
        "registration": REGISTRATION,
        "note": "分类判据只看包名/类名（可复核）；plugin 的发现机制 UNVERIFIED，别当已验证写进方案。",
        "points": sorted(pts, key=lambda p: (p["category"], p["package"], p["name"])),
    }
    out = Path(a.emit)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{out}  total={len(pts)}  {dict(by_cat)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
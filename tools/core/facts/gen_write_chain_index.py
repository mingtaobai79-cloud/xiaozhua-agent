# -*- coding: utf-8 -*-
"""gen_write_chain_index.py — 生成 core/facts/udc/write-chain/README.md 的文件表

为什么不手工维护：该目录已有 45 个事实件，手工表必然滞后。
本生成器只读文件头（标题 + 证据等级 + 行数），不解释内容。

用法：
    python tools/core/facts/gen_write_chain_index.py          # 打印
    python tools/core/facts/gen_write_chain_index.py --write   # 落盘
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FACTS = REPO / "core" / "facts"
TARGET = FACTS / "udc" / "write-chain"
README = TARGET / "README.md"

LEVELS = ("LIVE PASS", "LIVE", "VERIFIED_STATIC_BYTECODE",
          "VERIFIED_STATIC", "OBSERVED", "UNVERIFIED")

HEAD = """# udc/write-chain 索引

> 为什么有这个文件：本目录有 **{n} 个事实件**，此前一个都没登记 INDEX。
> 按文件名搜不到 → 等于没沉淀。这里给一张可检索的表。
>
> ★ 本表由 `tools/core/facts/gen_write_chain_index.py` 生成，不要手改。
> ★ 新增事实件后重跑生成器。

## 读法

```
LIVE / LIVE PASS               真发过请求、真回读过（可信度最高）
VERIFIED_STATIC_BYTECODE       反编译坐实代码路径，没跑过
UNVERIFIED                     推测，不能当依据
未标                            作者没写等级 —— 用前先看正文有无实测记录
```

## 文件表

| 文件 | 主题 | 等级 | 行数 |
|---|---|---|---|
"""


def level_of(txt: str) -> str:
    for lv in LEVELS:
        if lv in txt:
            return lv
    return "未标"


def title_of(p: Path, txt: str) -> str:
    m = re.search(r"(?m)^#\s+(.+)$", txt)
    t = (m.group(1) if m else p.stem).strip()
    t = t.replace("|", "/").replace("`", "")
    # 去掉尾部破折号串与过长的副标题
    t = re.sub(r"\s*[—–-]{1,2}\s*$", "", t)
    return t[:60]


def build() -> str:
    rows = []
    for p in sorted(TARGET.rglob("*.md")):
        if p.name == "README.md":
            continue
        rel = p.relative_to(TARGET).as_posix()
        txt = p.read_text(encoding="utf-8", errors="replace")
        rows.append("| `%s` | %s | %s | %d |"
                    % (rel, title_of(p, txt), level_of(txt),
                       len(txt.splitlines())))
    return HEAD.format(n=len(rows)) + "\n".join(rows) + "\n"


if __name__ == "__main__":
    out = build()
    if "--write" in sys.argv:
        README.write_bytes(out.encode("utf-8"))
        print("已写入 %s（%d 行）" % (README.relative_to(REPO).as_posix(),
                                     len(out.splitlines())))
    else:
        print(out[:1500])

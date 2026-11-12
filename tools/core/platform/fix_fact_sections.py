#!/usr/bin/env python3
"""把 ## 8. Verification / ## 9. Evidence 的顺序改成规范：8=Evidence、9=Verified。"""
from __future__ import annotations

import re
from pathlib import Path

FD = Path("<SEEYON_AGENT_ROOT>/core/facts/standard-product")
TARGETS = ["extension-point-consumers.md", "extension-point-decision-table.md",
           "extension-project-skeleton.md", "extension-registration-mechanisms.md"]


def main() -> int:
    for name in TARGETS:
        p = FD / name
        t = p.read_text(encoding="utf-8")
        if "## 8. Verification" not in t or "## 9. Evidence" not in t:
            print(f"  跳过 {name}（已是规范顺序或无此段）")
            continue
        i8 = t.index("## 8. Verification")
        i9 = t.index("## 9. Evidence")
        head = t[:i8]
        ver_block = t[i8 + len("## 8. Verification"):i9].rstrip()
        ev_block = t[i9 + len("## 9. Evidence"):].strip()
        new = (head
               + "## 8. Evidence\n\n" + ev_block + "\n\n"
               + "## 9. Verified\n" + ver_block + "\n")
        p.write_text(new, encoding="utf-8")
        print(f"  修正 {name}")
    # 自检
    for name in TARGETS:
        t = (FD / name).read_text(encoding="utf-8")
        ok = ("## 8. Evidence" in t and "## 9. Verified" in t
              and t.index("## 8. Evidence") < t.index("## 9. Verified"))
        print(f"  {'OK ' if ok else 'BAD'} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

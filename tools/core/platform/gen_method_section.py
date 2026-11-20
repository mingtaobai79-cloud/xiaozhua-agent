# -*- coding: utf-8 -*-
"""把方法级落表写进模块 README：`## 方法级落表（写接口）` 段。

语义要说清：这是**触及表的上界**（方法体直接引用的实体/DAO），不是「只写这张表」。
用法: python gen_method_section.py [--dry]
"""
import io, json, os, sys

REPO = r"C:/Users/白明涛/xiaozhua-agent"
M = os.path.join(REPO, "docs/audit/artifacts/method-tables")

MOD = {
    "organization": "03-business-app", "bpm": "03-business-app",
    "ctp-affair": "03-business-app", "ctp-user": "03-business-app",
    "ctp-message": "03-business-app", "ctp-other": "03-business-app",
    "cip-connector": "03-business-app", "cip-capability": "03-business-app",
    "cip-provider": "03-business-app", "cip-other": "03-business-app",
    "udc": "02-udc", "cdp": "03-business-app", "app": "03-business-app",
    "portal": "03-business-app", "m5": "03-business-app", "ai": "03-business-app",
}

WRITE_TOTAL = {
    "organization": 35, "bpm": 64, "ctp-affair": 34, "ctp-user": 42,
    "ctp-message": 12, "ctp-other": 13, "cip-connector": 24, "cip-capability": 102,
    "cip-provider": 58, "cip-other": 31, "udc": 179, "cdp": 13, "app": 37,
    "portal": 23, "m5": 10,
}


def main():
    dry = "--dry" in sys.argv
    for slug, group in MOD.items():
        jp = os.path.join(M, f"{slug}.json")
        rp = os.path.join(REPO, "core/facts/modules", group, slug, "README.md")
        if not os.path.exists(rp):
            continue
        d = json.load(io.open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
        total = WRITE_TOTAL.get(slug, 0)
        L = ["## 方法级落表（写接口）", ""]
        if not d:
            L += ["⚠️ **UNVERIFIED** —— 写方法的实现类里没有可解析的实体/DAO 引用。",
                  "", "原因：实现走 Dubbo 远端、动态 SQL 拼表名、或实现在未提取的构件里。不猜。", ""]
        else:
            L += [
                "> **口径：触及表的上界，不是「只写这张表」。** 证据链是"
                "「方法体引用的实体/DAO → 实体类 `@TableName` 字面量」，",
                "> 方法若再做条件分支，实际只写其中一部分。判断影响面用它，判断唯一落点还得看 SQL。",
                "> 等级 `VERIFIED_STATIC_BYTECODE`（引用与表名都来自字节码），"
                "**上界推断**部分标 `STATIC_INFERENCE`。",
                "",
                f"本模块 {total} 个写方法中，**{len(d)}** 个解析出触及表：",
                "",
                "| 接口#方法 | 触及表 | 依据（引用链） |",
                "|---|---|---|",
            ]
            for k in sorted(d):
                v = d[k]
                tabs = ", ".join(f"`{t}`" for t in v["tables"][:6])
                if len(v["tables"]) > 6:
                    tabs += f" …(+{len(v['tables'])-6})"
                ch = "; ".join(v["chain"][:2])
                L.append(f"| `{k}` | {tabs} | `{ch}` |")
            L.append("")
        block = "\n".join(L)

        s = io.open(rp, encoding="utf-8").read()
        if "## 方法级落表（写接口）" in s and "## REST 路由" in s:
            i, j = s.index("## 方法级落表（写接口）"), s.index("## REST 路由")
            s = s[:i] + block + "\n" + s[j:]
        elif "## REST 路由" in s:
            j = s.index("## REST 路由")
            s = s[:j] + block + "\n" + s[j:]
        else:
            print(f"  ! {slug}: 锚点缺失")
            continue
        if not dry:
            io.open(rp, "w", encoding="utf-8").write(s)
        print(f"  {'✓' if d else '-'} {slug}: {len(d)}/{total} 写方法{'（dry）' if dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
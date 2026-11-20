# -*- coding: utf-8 -*-
"""把 DTO 字段级摘要写进模块 README：`## 入参 DTO（字段级）` 段。

明细在 docs/audit/artifacts/dto/DTO-<slug>.md，README 只放 top 12 与入口。
用法: python gen_dto_section.py [--dry]
"""
import io, json, os, sys

REPO = r"C:/Users/白明涛/xiaozhua-agent"
D = os.path.join(REPO, "docs/audit/artifacts/dto")

MOD = {
    "organization": "03-business-app", "bpm": "03-business-app",
    "ctp-affair": "03-business-app", "ctp-user": "03-business-app",
    "ctp-message": "03-business-app", "ctp-other": "03-business-app",
    "cip-connector": "03-business-app", "cip-capability": "03-business-app",
    "cip-provider": "03-business-app", "cip-other": "03-business-app",
    "udc": "02-udc", "boot": "01-platform", "cdp": "03-business-app",
    "app": "03-business-app", "portal": "03-business-app", "m5": "03-business-app",
    "ai": "03-business-app", "ocip": "03-business-app",
    "devops": "01-platform", "gateway": "01-platform",
    "maven": "01-platform", "mymojo": "01-platform",
}


def main():
    dry = "--dry" in sys.argv
    for slug, group in MOD.items():
        jp = os.path.join(D, f"{slug}.json")
        rp = os.path.join(REPO, "core/facts/modules", group, slug, "README.md")
        if not (os.path.exists(jp) and os.path.exists(rp)):
            continue
        d = json.load(io.open(jp, encoding="utf-8"))
        withf = [(k, v) for k, v in d.items() if v.get("fields")]
        withf.sort(key=lambda kv: -kv[1]["usage"])

        L = ["## 入参 DTO（字段级）", ""]
        if not withf:
            L += ["⚠️ **UNVERIFIED** —— 本模块 facade 的入参类型在索引里没有字段。",
                  "", "原因：入参是枚举/接口/纯 Map，或类型来自未提取的构件。不写推测字段。", ""]
        else:
            L += [
                "> 字段来自字节码 `fields`（含继承链，最多 3 层）；**字段名即 JSON 键名**"
                "（平台用 Jackson 默认命名，`shortName` 对应库列 `short_name`）。",
                "> 包装类已揭开：`SingleRequest<T>` / `ListResponse<T>` 里看的是 `T` 的字段。",
                "> 等级 `VERIFIED_STATIC_BYTECODE`。全量字段表："
                f"`docs/audit/artifacts/dto/DTO-{slug}.md`",
                "",
                f"本模块 **{len(d)}** 个入参/返回 DTO，**{len(withf)}** 个能取到字段。Top 12（按出现次数）：",
                "",
                "| DTO | 出现 | 字段数 | 关键字段 |",
                "|---|---:|---:|---|",
            ]
            for k, v in withf[:12]:
                names = [f["name"] for f in v["fields"]][:8]
                L.append(f"| `{k.rsplit('.', 1)[-1]}` | {v['usage']} | {len(v['fields'])} "
                         f"| {', '.join('`%s`' % n for n in names)} |")
            L.append("")

        block = "\n".join(L)
        s = io.open(rp, encoding="utf-8").read()
        if "## 入参 DTO（字段级）" in s and "## 落表" in s:
            i, j = s.index("## 入参 DTO（字段级）"), s.index("## 落表")
            s = s[:i] + block + "\n" + s[j:]
        elif "## 落表" in s:
            j = s.index("## 落表")
            s = s[:j] + block + "\n" + s[j:]
        else:
            print(f"  ! {slug}: 锚点缺失")
            continue

        if not dry:
            io.open(rp, "w", encoding="utf-8").write(s)
        print(f"  {'✓' if withf else '-'} {slug}: {len(d)} DTO / {len(withf)} 有字段"
              f"{'（dry）' if dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
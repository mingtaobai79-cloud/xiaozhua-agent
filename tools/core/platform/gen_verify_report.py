# -*- coding: utf-8 -*-
"""汇总真机验证结果，生成 VERIFY-LIVE.md，并把结论回写模块 README 的证据表。

读: docs/audit/artifacts/rest/verify/results.jsonl
出: docs/audit/artifacts/rest/VERIFY-LIVE.md
用法: python gen_verify_report.py [--write-readme]
"""
import json, io, os, sys

REPO = r"C:/Users/白明涛/xiaozhua-agent"
R = os.path.join(REPO, "docs/audit/artifacts/rest")
OUT = os.path.join(R, "verify")
DONE = os.path.join(OUT, "results.jsonl")

MOD = {
    "organization": ("03-business-app", "organization-web"),
    "bpm": ("03-business-app", "bpm-web"),
    "ctp-affair": ("03-business-app", "ctp-affair-web"),
    "ctp-user": ("03-business-app", "ctp-user-web"),
    "ctp-message": ("03-business-app", "ctp-message-web"),
    "ctp-other": ("03-business-app", "ctp-media-web"),
    "cip-connector": ("03-business-app", "cip-connector-web"),
    "cip-capability": ("03-business-app", "cip-capability-web"),
    "cip-other": ("03-business-app", "cip-manager-web"),
    "udc": ("02-udc", "udc-web"),
    "boot": ("01-platform", "boot-starter-web"),
    "cdp": ("03-business-app", "cdp-data-web"),
    "app": ("03-business-app", "app-common-web"),
    "portal": ("03-business-app", "portal-web"),
    "m5": ("03-business-app", "m5-web"),
    "ai": ("03-business-app", "ai-web"),
}


def main():
    if not os.path.exists(DONE):
        print("无结果文件"); return 1
    rows = [json.loads(l) for l in open(DONE, encoding="utf-8") if l.strip()]
    by_art, notfound = {}, []
    for r in rows:
        d = by_art.setdefault(r["artifact"], {"EXISTS": 0, "NOT_FOUND": 0, "other": 0})
        if r["verdict"] in ("EXISTS", "OTHER_200"):
            d["EXISTS"] += 1
        elif r["verdict"] == "NOT_FOUND":
            d["NOT_FOUND"] += 1
            notfound.append(r)
        else:
            d["other"] += 1

    L = ["# REST 路由真机验证（test2 / localhost:3000 会话）", "",
         f"> 共验证 **{len(rows)}** 条路由，判定方式：CDP 在已登录页面上下文里 fetch。",
         "> 判据：`Whitelabel/405/404` = 映射不存在；`JSON 业务码（含 BOOT_3000）` = 映射命中。",
         "> 只验**安全方法**（select/query/get/find/search/page/check/load…）——",
         "> 写操作接口不做空 body 探测，避免落脏数据。", "",
         "| 构件 | EXISTS | NOT_FOUND | 其它 | 命中率 |", "|---|---:|---:|---:|---:|"]
    total_e = total_n = 0
    for a, c in sorted(by_art.items(), key=lambda x: -(x[1]["EXISTS"] + x[1]["NOT_FOUND"])):
        n = c["EXISTS"] + c["NOT_FOUND"] + c["other"]
        rate = (100.0 * c["EXISTS"] / n) if n else 0
        total_e += c["EXISTS"]
        total_n += c["NOT_FOUND"]
        L.append(f"| `{a}` | {c['EXISTS']} | {c['NOT_FOUND']} | {c['other']} | {rate:.0f}% |")
    n_all = total_e + total_n
    L.append(f"| **合计** | **{total_e}** | **{total_n}** | | **{(100.0*total_e/n_all if n_all else 0):.1f}%** |")
    L.append("")

    if notfound:
        L += ["## 未命中的路由（说明拼接或提取有问题，需单独看）", "",
              "| 路由 | HTTP | 构件 | java 方法 |", "|---|---|---|---|"]
        for r in notfound[:200]:
            L.append(f"| `{r['route']}` | {r['http']} | `{r['artifact']}` | `{r['java_method']}` |")
        if len(notfound) > 200:
            L.append(f"| … 共 {len(notfound)} 条 | | | |")
        L.append("")

    p = os.path.join(R, "VERIFY-LIVE.md")
    io.open(p, "w", encoding="utf-8").write("\n".join(L))
    print(f"→ {p}")
    print(f"EXISTS {total_e} / NOT_FOUND {total_n} / 命中率 {(100.0*total_e/n_all if n_all else 0):.1f}%")

    if "--write-readme" in sys.argv:
        for slug, (group, art) in MOD.items():
            c = by_art.get(art)
            if not c:
                continue
            n = c["EXISTS"] + c["NOT_FOUND"] + c["other"]
            rp = os.path.join(REPO, "core/facts/modules", group, slug, "README.md")
            if not os.path.exists(rp):
                continue
            s = io.open(rp, encoding="utf-8").read()
            old = None
            for cand in ("| REST 路径（", "| 落表"):
                pass
            # 在证据表里加/替换一行「真机验证」
            line = (f"| REST 真机验证 | {c['EXISTS']}/{n} 条安全路由命中"
                    f"（{100.0*c['EXISTS']/n:.0f}%） | `LIVE` |")
            if "| REST 真机验证 |" in s:
                import re
                s = re.sub(r"\| REST 真机验证 \|[^\n]*", line, s)
            elif "| REST 路径" in s:
                i = s.index("| REST 路径")
                j = s.index("\n", i) + 1
                s = s[:j] + line + "\n" + s[j:]
            else:
                i = s.index("## 证据与自证")
                j = s.index("| 内容 | 证据 | 等级 |")
                k = s.index("\n", s.index("|---|---|---|", j)) + 1
                s = s[:k] + line + "\n" + s[k:]
            io.open(rp, "w", encoding="utf-8").write(s)
        print("README 已回写")
    return 0


if __name__ == "__main__":
    sys.exit(main())
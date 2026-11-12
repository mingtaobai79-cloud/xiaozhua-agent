#!/usr/bin/env python
"""设置域操作存在性探针（只读，空 body）。

把「端点存在，未实测」这类 UNVERIFIED 一次性收口成 存在 / 不存在。
**不构造有效写入** —— 只发空 body，靠错误码判别，不会改动任何数据。

用法
----
    python tools/core/setting/probe_setting_ops.py                 # 跑内置全表
    python tools/core/setting/probe_setting_ops.py --only 选项集
    python tools/core/setting/probe_setting_ops.py --port 9250 \
        --url-match app-design

三处必须做对（上一版全错在这，见 core/facts/udc/setting/operation-matrix.md §一）
  1 GraphQL 的 code 嵌在 data.data0.code，不是顶层
  2 字段集 / 二维码 / 导入导出模板走 REST，不是 GraphQL（用 GraphQL 探是假阴性）
  3 不能用 str(None) 判真假 —— str(None)=="None" 恒真

判别口径
  GraphQL  data.data0.code 非空字符串 → 存在；FieldUndefined → 不存在
  REST     404 → 不存在；405 → 存在但方法不对；其它 → 存在
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

GRAPHQL_OPS: dict[str, list[str]] = {
    "选项集": ["udcUdcEnumUpdatePost", "udcUdcEnumItemUpdatePost",
              "udcUdcEnumItemDeletePost", "udcUdcEnumBatchDeletePost",
              "udcUdcEnumCategoryDeletePost", "udcUdcEnumCategoryUpdatePost"],
    "参数": ["udcCtpParameterDefinitonDeletePost", "udcCtpParameterDefinitonSearch",
            "udcCtpParameterDefinitonUpdatePost"],
    "流水号": ["udcSerialSchemeUpdatePost", "udcSerialSchemeDeletePost"],
    "自定义对象": ["udcDataTransferObjectUpdateDtoPost"],
    "扩展实体": ["udcScalabilityDeletePost", "udcScalabilityOptionUpdatePost"],
}

REST_OPS: dict[str, list[str]] = {
    "字段集": ["/service/udc/attributeSet/delete",
              "/service/udc/attributeSet/update",
              "/service/udc/attributeSet/search-list",
              "/service/udc/attributeSet/search/term"],
    "二维码": ["/service/udc/qrcode-rule/update",
              "/service/udc/qrcode-rule/delete",
              "/service/udc/qrcode-rule/search"],
    "导入导出模板": ["/service/udc/excel/update-template",
                   "/service/udc/excel/delete-template",
                   "/service/udc/excel/export-excel-template",
                   "/service/udc/excel/search"],
}

JS = ('(async () => { const r = await fetch(PATH, {method:"POST", credentials:"include", '
      'headers:{"Content-Type":"application/json","Accept":"application/json"}, '
      'body: BODY}); const t = await r.text(); '
      'return JSON.stringify({http:r.status, body:t}); })()')


def _post(client, path, body):
    js = (JS.replace("PATH", json.dumps(path))
          .replace("BODY", json.dumps(json.dumps(body, ensure_ascii=False))))
    raw = json.loads(client.evaluate(js, await_promise=True))
    try:
        return raw["http"], json.loads(raw["body"]), raw["body"]
    except Exception:
        return raw["http"], None, raw["body"]


def probe_graphql(client, domain: str, op: str):
    q = ("mutation graphqlLoader ($params0: %sInputBody) { data0: %s(body: $params0) "
         "{ code data { content } message status } }" % (op, op))
    http, r, text = _post(client, "/service/udc/graphql?" + op,
                          {"query": q, "variables": {"params0": {}}})
    if "FieldUndefined" in text:
        return "不存在", "FieldUndefined"
    if r and isinstance(r.get("data"), dict):
        d0 = (r.get("data") or {}).get("data0") or {}
        code = d0.get("code")
        if isinstance(code, str) and code:
            return "存在", "%s %s" % (code, str(d0.get("message"))[:50])
        return "存在?", "data0 无 code: %s" % text[:80]
    if "Invalid Syntax" in text:
        return "语法未定", "Invalid Syntax"
    return "未定", text[:70]


def probe_rest(client, domain: str, path: str):
    http, r, text = _post(client, path, {})
    low = (text or "").lower()
    if http == 404 or "server_404" in low or "no handler" in low or "not found" in low:
        return "不存在", "HTTP %s" % http
    if http == 405:
        return "存在(GET?)", "HTTP 405"
    if r is not None:
        return "存在", "HTTP %s code=%s %s" % (http, r.get("code"),
                                               str(r.get("message"))[:40])
    return "存在?", "HTTP %s %s" % (http, text[:60])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--url-match", default="",
                    help="按 URL 子串挑标签页；留空 = 首个 page")
    ap.add_argument("--only", default="", help="只跑某个域，如 选项集")
    a = ap.parse_args()

    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=90)
    kw = {"url_substr": a.url_match} if a.url_match else {}
    c.connect(**kw)

    # ★ origin 自检：连到 devtools:// 或 chrome:// 时，fetch 会返回
    #   body="HTTP/1.1 404 Not Found" 且 status=200，于是所有路径都被误判成"不存在"。
    #   实测踩过：url_match 留空 → 连中 devtools tab → 4 条 REST 全假阴性。
    origin = c.evaluate("location.origin")
    if not str(origin).startswith("http"):
        print("❌ 连到了 %r，不是真实站点页。"
              "请用 --url-match 指定页面（如 --url-match app-design）" % (origin,))
        c.close()
        return 2
    print("origin = %s" % origin)

    want = (a.only or "").strip()
    results = {}
    try:
        print("=" * 92)
        print("A. GraphQL 通道")
        print("-" * 92)
        print("%-10s %-38s %-8s %s" % ("域", "operation", "判定", "依据"))
        for domain, ops in GRAPHQL_OPS.items():
            if want and want != domain:
                continue
            for op in ops:
                v, why = probe_graphql(c, domain, op)
                results[(domain, op, "graphql")] = (v, why)
                print("%-10s %-38s %-8s %s" % (domain, op, v, why))

        print("\n" + "=" * 92)
        print("B. REST 通道")
        print("-" * 92)
        print("%-12s %-46s %-8s %s" % ("域", "path", "判定", "依据"))
        for domain, paths in REST_OPS.items():
            if want and want != domain:
                continue
            for p in paths:
                v, why = probe_rest(c, domain, p)
                results[(domain, p, "rest")] = (v, why)
                print("%-12s %-46s %-8s %s" % (domain, p, v, why))
    finally:
        c.close()

    print("\n" + "=" * 92)
    print("汇总")
    print("-" * 92)
    print("  ", dict(Counter(v[0] for v in results.values())))
    missing = [(d, op, v[1]) for (d, op, _), v in results.items() if v[0] == "不存在"]
    if missing:
        print("\n  确实不存在（VACUUM）:")
        for d, op, why in missing:
            print("    %-12s %-44s %s" % (d, op, why))
    print("\n  ⚠ 这是「端点存在性」，不是「能力可用性」。"
          "报打通仍须真实参数实发 + DB 回读。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

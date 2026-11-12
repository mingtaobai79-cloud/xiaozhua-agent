"""设置域 · 选项集：建两套完整样本（分组 → 选项集 → 多个选项项）。

用途：给用户页面验收"生成是否正确"。走 xiaozhua-agent 自己的构造器 + 校验器，
不是裸脚本拼 body。

用法：
  python tools/core/setting/option_set_seed.py --port 9231 --plan samples
  python tools/core/setting/option_set_seed.py --port 9231 --plan samples \
      --i-have-write-authorization        # 真写
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.option_set_constraints import (  # noqa: E402
    build_option_set_body, build_option_set_category_body, build_option_set_item_body,
    validate_option_set_body, validate_option_set_category_body,
    validate_option_set_item_body,
)

APP_ID = None  # ★ 由 --app-id / XIAOZHUA_APP_ID 提供
APP_ID = __import__("os").environ.get("XIAOZHUA_APP_ID") or APP_ID

APP_GUID = "2275741415570096882"

# 两套样本（用户要求"新建两个给我看看"）
SAMPLES = [
    {
        "group": {"name": "ZxjSampleGroupA", "caption": "验收分组A", "order_no": 11},
        "set": {"name": "ZxjSampleSetA", "caption": "验收选项集A", "order_no": 11},
        "items": [
            {"name": "PENDING", "caption": "待处理", "code": 1, "order_no": 1},
            {"name": "RUNNING", "caption": "处理中", "code": 2, "order_no": 2},
            {"name": "DONE", "caption": "已完成", "code": 3, "order_no": 3},
        ],
    },
    {
        "group": {"name": "ZxjSampleGroupB", "caption": "验收分组B", "order_no": 12},
        "set": {"name": "ZxjSampleSetB", "caption": "验收选项集B", "order_no": 12},
        "items": [
            {"name": "LOW", "caption": "低", "code": 1, "order_no": 1},
            {"name": "MIDDLE", "caption": "中", "code": 2, "order_no": 2},
            {"name": "HIGH", "caption": "高", "code": 3, "order_no": 3},
            {"name": "URGENT", "caption": "紧急", "code": 4, "order_no": 4},
        ],
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--plan", default="samples", choices=["samples"])
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\opt-seed")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page" and "lowcode-test2" in t.get("url", "")]
    if not pages:
        print("没有可用的 lowcode-test2 标签页")
        return 1
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=pages[0])

    def gql(op, body):
        q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
             "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
        payload = {"query": q, "variables": {"params0": body}}
        js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
              % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
        raw = c.evaluate(js, await_promise=True)
        return json.loads(raw)["data"]["data0"]

    # ---- 构造 + 本地校验（不写）
    plan = []
    for s in SAMPLES:
        cat_body = build_option_set_category_body(
            APP_ID, APP_GUID, name=s["group"]["name"], caption=s["group"]["caption"],
            order_no=s["group"]["order_no"])
        set_body = build_option_set_body(
            APP_ID, APP_GUID, name=s["set"]["name"], caption=s["set"]["caption"],
            category_id="<待填>", order_no=s["set"]["order_no"])
        item_bodies = [build_option_set_item_body(
            APP_ID, APP_GUID, enum_id="<待填>", **it) for it in s["items"]]
        errs = (validate_option_set_category_body(cat_body)
                + validate_option_set_body(set_body)
                + [e for b in item_bodies for e in validate_option_set_item_body(b)])
        plan.append({"sample": s, "cat": cat_body, "set": set_body,
                     "items": item_bodies, "errors": errs})

    for p in plan:
        print(f"[{p['cat']['caption']}] 本地校验: {p['errors'] or '✅ 通过'}")
        print(f"  分组 {p['cat']['name']}  选项集 {p['set']['name']}  "
              f"选项项 {len(p['items'])} 个")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

    if not a.i_have_write_authorization:
        print(f"\n只构造未写入。加 --i-have-write-authorization 才提交。\n计划 -> {out/'plan.json'}")
        c.close()
        return 0

    bad = [p for p in plan if p["errors"]]
    if bad:
        print("\n有本地校验错误，拒绝提交")
        c.close()
        return 2

    results = []
    for p in plan:
        r1 = gql("udcUdcEnumCategoryPost", p["cat"])
        if r1.get("code") != "BOOT_0000":
            print("分组创建失败:", json.dumps(r1, ensure_ascii=False)[:250])
            results.append({"stage": "category", "resp": r1})
            break
        cat_id = r1["data"]["content"]
        p["set"]["categoryId"] = str(cat_id)
        r2 = gql("udcUdcEnumPost", p["set"])
        if r2.get("code") != "BOOT_0000":
            print("选项集创建失败:", json.dumps(r2, ensure_ascii=False)[:250])
            results.append({"stage": "set", "resp": r2})
            break
        set_id = r2["data"]["content"]
        item_ids = []
        failed = None
        for ib in p["items"]:
            ib["enumId"] = str(set_id)
            r3 = gql("udcUdcEnumItemPost", ib)
            if r3.get("code") != "BOOT_0000":
                failed = {"item": ib["name"], "resp": r3}
                break
            item_ids.append(r3["data"]["content"])
        results.append({"group": p["cat"]["caption"], "set": p["set"]["caption"],
                        "cat_id": cat_id, "set_id": set_id,
                        "item_ids": item_ids, "failed": failed})
        print(f"\n✅ {p['set']['caption']}")
        print(f"   分组   id={cat_id}")
        print(f"   选项集 id={set_id}  name={p['set']['name']}")
        print(f"   选项项 {len(item_ids)}/{len(p['items'])} 个"
              + (f"  ❌ 失败: {failed}" if failed else ""))
        if failed:
            break

    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n结果 -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

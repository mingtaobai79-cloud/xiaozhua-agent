"""用真实生产微流程回归闸门（误报基线 + 漏报注入）。

为什么需要这个脚本：只拿自己造的干净样本测闸门等于没测。
在某个真实应用上跑一次，误报率经常 40%~65%，而每一条误报都会挡住真实业务流。

用法（只读，不写不改不删）：
    # 应用 id：UDC 应用名形如 znxmglpt<应用ID>，接口要纯数字部分
    python regress_gates.py --app 3289082814923688017 --app-name znxmglpt<应用ID>
    python regress_gates.py --app 3289082814923688017 --limit 200 --no-inject

输出两段：
    A. 误报基线：有问题的流程数 / 总流程数；剩下的每一条都要能解释成「生产本身的真实缺陷」
    B. 漏报注入：向覆盖最全的样本注入各类缺陷，命中率必须 6/6

前置：浏览器已开 CDP（UDC_CDP，默认 http://127.0.0.1:9222），且已登录目标环境。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from components.udc.microflow.gates import (
    run_gates, run_end_gate, run_leak_gate, run_order_gate, _walk_nodes)
from components.udc.microflow.live.cdp import Driver


# ── 只读取数（同步 XHR，浏览器自带会话，不读 cookie）────────────────
_XHR = ("(function(){{var x=new XMLHttpRequest();"
        "x.open('POST','/service/udc/graphql?{op}',false);"
        "x.setRequestHeader('Content-Type','application/json');"
        "x.send({payload});return x.responseText;}})()")


def _post(d, op: str, query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables})
    raw = d.eval(_XHR.format(op=op, payload=json.dumps(payload)))
    try:
        return json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception:
        return {}


def list_microflows(d, app_id: str, types=("SERVICE", "CUSTOM")) -> list[dict]:
    """列应用全部微流程。★ 结构是 pageInfo/params 两个嵌套对象，不是扁平字段。"""
    q = ("query g($p: udcMicroflowSearchInputBody){ data0: udcMicroflowSearch(body:$p){"
         " code message data { content { id name caption type triggerType state } } } }")
    v = {"p": {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": 999,
                            "pages": 0, "total": 0},
               "params": {"appId": str(app_id), "IN_type": list(types)}}}
    r = _post(d, "udcMicroflowSearch", q, v)
    d0 = ((r.get("data") or {}).get("data0") or {})
    if d0.get("code") != "BOOT_0000":
        raise SystemExit("udcMicroflowSearch 失败: %s %s" % (d0.get("code"), d0.get("message")))
    return ((d0.get("data") or {}).get("content")) or []


def fetch_schema(d, mid) -> dict | None:
    """★ 变量类型 udcMicroflowFindByIdGetInputPath，参数名 path 不是 body。"""
    q = ("query g($p: udcMicroflowFindByIdGetInputPath){ data0: udcMicroflowFindByIdGet(path:$p){"
         " code message data { content { id state dataSchema } } } }")
    r = _post(d, "udcMicroflowFindByIdGet", q, {"p": {"id": str(mid)}})
    c = ((((r.get("data") or {}).get("data0") or {}).get("data")) or {}).get("content") or {}
    ds = c.get("dataSchema")
    if isinstance(ds, str):
        try:
            ds = json.loads(ds)
        except Exception:
            return None
    return ds if isinstance(ds, dict) else None


# ── 闸门跑批 ────────────────────────────────────────────────────
def all_gates(schema: dict) -> list[str]:
    out: list[str] = []
    for fn in (run_gates, run_end_gate, run_leak_gate, run_order_gate):
        try:
            out += fn(schema)
        except Exception as exc:                      # 闸门崩了也要看得见
            out.append("EXCEPTION@%s: %s" % (fn.__name__, exc))
    return out


def baseline(samples: dict) -> None:
    print("=" * 62)
    print("A. 误报基线：%d 条真实 RELEASE 生产流程" % len(samples))
    print("=" * 62)
    bad, total, buckets = [], 0, collections.Counter()
    for mid, rec in samples.items():
        probs = all_gates(rec["ds"])
        if probs:
            bad.append((rec.get("caption"), probs))
            total += len(probs)
            for p in probs:
                buckets[p.split()[0]] += 1
    pct = 100.0 * len(bad) / len(samples) if samples else 0.0
    print("报出问题的流程: %d / %d (%.1f%%)   问题总数: %d\n" % (len(bad), len(samples), pct, total))
    for tag, n in buckets.most_common():
        print("  %-6s %d" % (tag, n))
    print()
    for cap, probs in bad[:20]:
        print("  [%s] %d 个" % (cap or "?", len(probs)))
        for p in probs[:2]:
            print("     ", p[:150])
    print("\n判据：剩下的每一条都要能解释成「生产本身的真实缺陷」。")
    print("解释不了的 → 闸门判据过严，改闸门，不要改样本。\n")


def injections(samples: dict) -> None:
    """向覆盖 actionType 最多的一条注入各类缺陷，命中率必须 6/6。"""
    print("=" * 62)
    print("B. 漏报检测：注入已知缺陷")
    print("=" * 62)
    base_rec, best = None, -1
    for rec in samples.values():
        n = len({x.get("actionType") for x in _walk_nodes(rec["ds"].get("nodes"))
                 if x.get("actionType")})
        if n > best:
            best, base_rec = n, rec
    if not base_rec:
        print("  无样本可注入")
        return
    base = json.loads(json.dumps(base_rec["ds"]))
    print("注入基底: %s（覆盖 %d 类节点）\n" % (base_rec.get("caption"), best))

    cases: list[tuple[str, dict]] = []

    b = json.loads(json.dumps(base))                       # 1 MAP_OPERATION basic 裸字符串
    for n in b.get("nodes") or []:
        if n.get("actionType") == "MAP_OPERATION":
            n["basic"] = "STRING"
            n["structure"] = {"0": "S", "1": "T"}
            cases.append(("basic 裸字符串", b))
            break

    b = json.loads(json.dumps(base))                       # 2 endNode 塞进 nodes
    if b.get("endNode"):
        b["nodes"].append(dict(b["endNode"]))
        b["endNode"] = {}
        cases.append(("endNode 进 nodes", b))

    b = json.loads(json.dumps(base))                       # 3 引用泄漏
    for n in b.get("nodes") or []:
        sp = n.get("selectParam")
        if isinstance(sp, dict) and sp.get("outputName"):
            sp["nodeInfo"] = {"nodeId": "CREATE_VARIABLE_NOTEXIST"}
            cases.append(("引用泄漏(nodeInfo)", b))
            break

    b = json.loads(json.dumps(base))                       # 4 elseBranch 带表达式
    for n in _walk_nodes(b.get("nodes")):
        if n.get("name") == "elseBranch":
            n["expression"] = {"title": "x", "schema": "{}"}
            cases.append(("elseBranch 带表达式", b))
            break

    b = json.loads(json.dumps(base))                       # 5 事件投递选错字段
    b["nodes"].append({"nodeId": "PUBLISH_BUSINESS_EVENT_x","type": "ACTIVITY",
                       "actionType": "PUBLISH_BUSINESS_EVENT","caption": "事件投递",
                       "eventType": "AMONG_APP","mappingType": "attrs","attrs": [{}]})
    cases.append(("事件投递缺 selectMq/app", b))

    b = json.loads(json.dumps(base))                       # 6 CONNECTOR 无 app
    b["nodes"].append({"nodeId": "CONNECTOR_x","type": "ACTIVITY",
                       "actionType": "CONNECTOR","caption": "连接器"})
    cases.append(("CONNECTOR 无 app", b))

    b = json.loads(json.dumps(base))                       # 7 CONDITION name 非法
    for n in _walk_nodes(b.get("nodes")):
        if n.get("type") == "CONDITION":
            n["name"] = "wrongBranch"
            cases.append(("CONDITION name 非法", b))
            break

    hit = 0
    for label, sch in cases:
        probs = all_gates(sch)
        tags = sorted({p.split()[0] for p in probs if p})
        hit += bool(probs)
        print("  %-24s → %d 问题 %s %s" % (label, len(probs), "✓" if probs else "✗漏报", tags))
    print("\n漏报检测: %d / %d 命中（必须全中）" % (hit, len(cases)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True, help="纯数字 appId")
    ap.add_argument("--app-name", default="", help="UDC 应用名（如 znxmglpt<应用ID>）")
    ap.add_argument("--limit", type=int, default=0, help="最多取多少条（0=全部）")
    ap.add_argument("--no-inject", action="store_true", help="跳过漏报注入")
    ap.add_argument("--save", default="", help="把抓到的 schema 存成 json，下次免重抓")
    args = ap.parse_args()

    samples: dict = {}
    if args.save and os.path.exists(args.save):
        samples = json.load(open(args.save, encoding="utf-8"))
        print("从缓存读入 %d 条" % len(samples))
    else:
        d = Driver()
        d.connect()
        mfs = [m for m in list_microflows(d, args.app) if m.get("state") == "RELEASE"]
        if args.limit:
            mfs = mfs[: args.limit]
        print("RELEASE 微流程 %d 条，开始拉 dataSchema（只读）..." % len(mfs))
        for i, m in enumerate(mfs, 1):
            ds = fetch_schema(d, m["id"])
            if ds:
                samples[str(m["id"])] = {"caption": m.get("caption"), "ds": ds}
            if i % 50 == 0:
                print("  ... %d/%d" % (i, len(mfs)))
        if args.save:
            json.dump(samples, open(args.save, "w", encoding="utf-8"), ensure_ascii=False)
            print("已存 %s" % args.save)

    if not samples:
        raise SystemExit("没有可回归的样本")
    baseline(samples)
    if not args.no_inject:
        injections(samples)


if __name__ == "__main__":
    main()

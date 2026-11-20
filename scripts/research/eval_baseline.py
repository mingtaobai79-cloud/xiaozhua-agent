#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
业务意图检索基线评估
====================
读取 evaluation/intent-capability-set-v1.json，对 positive 集跑 find_action，
计算 Top-1 / Top-5 / Recall@5 / MRR，并按错误类型归因。

用法：
  python scripts/research/eval_baseline.py
  python scripts/research/eval_baseline.py --k 5
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

EVAL = os.path.join(ROOT, "core/research/platform-dev-system/evaluation/intent-capability-set-v1.json")


def norm(s):
    """归一化方法标识：取 # 后半段的方法名，去 @ 前缀和泛型，小写。"""
    if not s:
        return ""
    s = s.split("#")[-1]
    s = s.lstrip("@")
    s = re.sub(r"<.*?>", "", s)
    return s.strip().lower()


def hit_any(hits, expected):
    """expected 里的任一项是否命中 hits（按方法名或 类#方法 双口径）。"""
    ex_norm = {norm(e) for e in expected if "#" in e}
    ex_cls = {e.split("#")[0].lstrip("@").lower() for e in expected if "#" in e}
    ex_bare = {norm(e) for e in expected if "#" not in e}

    for h in hits:
        m = norm(h.get("method", ""))
        i = (h.get("iface") or "").lstrip("@").lower()
        full = (h.get("ifaceFull") or "").lower()
        if m in ex_norm:
            # 方法名命中，且类名也对得上（若 expected 指定了类）
            if not ex_cls or i in ex_cls or any(c in full for c in ex_cls):
                return True
            # 只给了方法名（无类限定）也算
            if ex_bare:
                return True
        if m in ex_bare:
            return True
    return False


def hit_any_cap(hits, entry):
    """能力级命中：方法名或能力标识任一命中即可。

    用于注解类（@AntiReCommit 等）：索引里 iface=AntiReCommit, method=annotation，
    归一化后 'antirecommit#annotation' != 'antirecommit'，但语义上是同一个东西。
    """
    if hit_any(hits, entry.get("expected_top1") or []):
        return True
    cap = (entry.get("expected_capability") or "").lower().replace("_", "")
    for h in hits:
        c = (h.get("capability") or "").lower().replace("_", "")
        if cap and c == cap:
            return True
        # 注解：iface 就是注解名
        iface = (h.get("iface") or "").lstrip("@").lower().replace("_", "")
        for e in (entry.get("expected_top1") or []):
            en = e.lstrip("@").split("#")[0].lower().replace("_", "")
            if en and (en == iface or en == c):
                return True
    return False


def forbidden_hit(hits, forbidden):
    """forbidden 模式（支持 * 通配）是否出现在 hits 里。

    语义区分，避免假命中：
      - 含 '#' 的模式：与 "Class#method" 精确比较（去通配后）
      - 不含 '#': 与方法名精确比较，或是类名的一部分
    """
    if not forbidden:
        return False
    for h in hits:
        meth = norm(h.get("method", ""))
        cls = (h.get("iface") or "").lstrip("@")
        label = f"{cls}#{h.get('method','')}".lower()
        for pat in forbidden:
            p = pat.lower()
            star = "*" in p
            p2 = p.replace("*", "")
            if not p2:
                continue
            if "#" in p2:
                # 类#方法：精确（含通配时退化为子串）
                if (label == p2) or (star and p2 in label):
                    return True
            else:
                # 只给类名 or 方法名
                if p2 == meth or p2 == cls.lower():
                    return True
                if star and p2 in cls.lower():
                    return True
    return False


def classify_error(entry, hits, top1_ok, top5_ok):
    """错误类型归因。"""
    if top1_ok:
        return None
    if not hits:
        return "no_result"
    if top5_ok:
        return "rank_too_low"
    # 看是否命中同域但错动作
    cap = entry.get("expected_capability", "")
    got = norm(hits[0].get("method", ""))
    exp = norm(entry["expected_top1"][0]) if entry.get("expected_top1") else ""
    if exp and got:
        # 简单前缀判断动词是否一致
        for verb in ("select", "create", "update", "delete", "get", "save", "submit", "send", "eval", "transform"):
            if exp.startswith(verb) and not got.startswith(verb):
                return "action_mismatch"
    return "wrong_capability"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()

    from components.construction.business_code_bridge import find_action

    data = json.load(open(EVAL, encoding="utf-8"))
    pos = data["positive"]

    n = len(pos)
    top1 = top5 = 0
    rr_sum = 0.0
    errors = {}
    rows = []
    forbidden_violations = []

    for e in pos:
        intent = e["intent"]
        r = find_action(intent=intent)
        hits = (r.get("hits") or [])[:a.k]

        t1 = bool(hits) and hit_any(hits[:1], e["expected_top1"])
        t5 = bool(hits) and hit_any(hits, e["expected_top1"])

        # MRR
        rr = 0.0
        for rank, h in enumerate(hits, 1):
            if hit_any([h], e["expected_top1"]):
                rr = 1.0 / rank
                break

        top1 += t1
        top5 += t5
        rr_sum += rr

        # forbidden 检查
        fv = forbidden_hit(hits, e.get("forbidden"))
        if fv:
            forbidden_violations.append(e["id"])

        err = classify_error(e, hits, t1, t5)
        if err:
            errors[err] = errors.get(err, 0) + 1

        rows.append({
            "id": e["id"],
            "intent": intent,
            "expected": e["expected_top1"],
            "got_top1": f"{hits[0].get('iface','')}#{hits[0].get('method','')}" if hits else "",
            "top1": t1, "top5": t5, "rr": round(rr, 3), "error": err,
            "forbidden_hit": fv,
        })

    print("=" * 70)
    print("业务意图检索基线（positive 集）")
    print("=" * 70)
    print(f"样本数        : {n}")
    print(f"Top-1 命中    : {top1}/{n} = {top1/n:.1%}")
    print(f"Top-{a} 命中    : {top5}/{n} = {top5/n:.1%}")
    print(f"MRR           : {rr_sum/n:.3f}")
    print(f"forbidden 违反: {len(forbidden_violations)} {forbidden_violations if forbidden_violations else ''}")
    print()
    print("错误类型分布：")
    if errors:
        for k, v in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"  {k:20s} {v}")
    else:
        print("  无错误")
    print()
    print("逐条结果：")
    for r in rows:
        mark = "✅" if r["top1"] else ("🔶" if r["top5"] else "❌")
        print(f"  {mark} {r['id']:8s} {r['intent'][:24]:26s} 期望={r['expected'][0][:40]:42s} 实际={r['got_top1'][:40]}")
        if r["error"]:
            print(f"        └─ {r['error']}")

    out = os.path.join(ROOT, "core/research/platform-dev-system/evaluation/baseline-v1.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "n": n, "top1": top1, "topk": top5, "k": a.k,
            "top1_rate": round(top1/n, 4), "topk_rate": round(top5/n, 4),
            "mrr": round(rr_sum/n, 4),
            "errors": errors,
            "forbidden_violations": forbidden_violations,
            "rows": rows,
        }, f, ensure_ascii=False, indent=1)
    print()
    print(f"已写入: {out}")


if __name__ == "__main__":
    main()

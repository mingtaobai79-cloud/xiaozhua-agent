#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整评估（四类全覆盖）
======================
positive  : Top-1 / Top-5 / MRR / forbidden
synonym   : held-out 泛化（112 条 utterance）
negative  : 违规率（forbidden 是否被推荐）
ambiguous : 澄清率（是否给出多个候选 / 未强行单推）

用法：
  python scripts/research/eval_full.py
  python scripts/research/eval_full.py --save
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts/research"))

from dev_capability_index import search          # noqa: E402
from eval_baseline import hit_any_cap, forbidden_hit  # noqa: E402

EVAL = os.path.join(ROOT, "core/research/platform-dev-system/evaluation/intent-capability-set-v1.json")


def run():
    ev = json.load(open(EVAL, encoding="utf-8"))
    r = {}

    # ---------------- positive ----------------
    pos = ev["positive"]
    t1 = t5 = 0
    rr = 0.0
    fv = []
    errs = {}
    for e in pos:
        hits = search(e["intent"], top_k=5, forbidden=e.get("forbidden"))
        a1 = bool(hits) and hit_any_cap(hits[:1], e)
        a5 = bool(hits) and hit_any_cap(hits, e)
        rank = 0
        for i, h in enumerate(hits, 1):
            if hit_any_cap([h], e):
                rank = i
                break
        t1 += a1
        t5 += a5
        rr += (1.0 / rank) if rank else 0.0
        if forbidden_hit(hits, e.get("forbidden")):
            fv.append(e["id"])
        if not a1:
            errs.setdefault("rank>1" if a5 else ("no_result" if not hits else "wrong_capability"), []).append(e["id"])
    r["positive"] = {
        "n": len(pos), "top1": t1, "top5": t5,
        "top1_rate": round(t1 / len(pos), 4),
        "top5_rate": round(t5 / len(pos), 4),
        "mrr": round(rr / len(pos), 4),
        "forbidden_violations": fv,
        "misses": errs,
    }

    # ---------------- synonym (held-out) ----------------
    syn = ev["synonym"]
    tot = st1 = st5 = 0
    sfails = []
    for e in syn:
        fake = {"expected_top1": e["expected_top1"], "expected_capability": e["capability"]}
        for utt in e["utterances"]:
            tot += 1
            hits = search(utt, top_k=5, forbidden=e.get("forbidden"))
            a1 = bool(hits) and hit_any_cap(hits[:1], fake)
            a5 = bool(hits) and hit_any_cap(hits, fake)
            st1 += a1
            st5 += a5
            if not a1:
                sfails.append({
                    "id": e["id"], "utterance": utt,
                    "expected": e["expected_top1"][0],
                    "got": f"{hits[0]['iface']}#{hits[0]['method']}" if hits else "",
                })
    r["synonym"] = {
        "n": tot, "top1": st1, "top5": st5,
        "top1_rate": round(st1 / tot, 4),
        "top5_rate": round(st5 / tot, 4),
        "misses": sfails,
    }

    # ---------------- negative ----------------
    neg = ev["negative"]
    nviol = []
    nt1 = 0
    for e in neg:
        hits = search(e["intent"], top_k=5, forbidden=e.get("forbidden"))
        ok = bool(hits) and not forbidden_hit(hits, e.get("forbidden"))
        nt1 += ok
        if not ok:
            nviol.append({"id": e["id"], "intent": e["intent"],
                          "got": [(h["iface"] + "#" + h["method"]) for h in hits[:3]]})
    r["negative"] = {
        "n": len(neg), "clean": nt1,
        "clean_rate": round(nt1 / len(neg), 4),
        "violations": nviol,
    }

    # ---------------- ambiguous ----------------
    # 判定标准：Top-5 里命中 ≥2 个不同能力 → 认为有足够信息触发澄清
    #           （真实 Agent 应先问，而不是单推）
    amb = ev["ambiguous"]
    aok = 0
    adetail = []
    for e in amb:
        hits = search(e["utterance"], top_k=5)
        caps = {h["capability"] for h in hits}
        ok = len(caps) >= 2 or not hits          # 无结果也算"没乱推"
        aok += ok
        if not ok:
            adetail.append({"id": e["id"], "utterance": e["utterance"],
                            "single_cap": list(caps)[:1],
                            "must_not": e["must_not"]})
    r["ambiguous"] = {
        "n": len(amb), "not_overconfident": aok,
        "rate": round(aok / len(amb), 4),
        "overconfident": adetail,
    }
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()
    r = run()

    print("=" * 72)
    print("四类评估总表")
    print("=" * 72)

    p = r["positive"]
    print(f"\n【positive 正例】n={p['n']}")
    print(f"  Top-1           {p['top1']}/{p['n']} = {p['top1_rate']:.1%}")
    print(f"  Top-5           {p['top5']}/{p['n']} = {p['top5_rate']:.1%}")
    print(f"  MRR             {p['mrr']:.3f}")
    print(f"  forbidden 违反  {len(p['forbidden_violations'])}")
    if p["misses"]:
        print(f"  未命中          {p['misses']}")

    s = r["synonym"]
    print(f"\n【synonym 近义（held-out）】n={s['n']} 条 utterance")
    print(f"  Top-1           {s['top1']}/{s['n']} = {s['top1_rate']:.1%}")
    print(f"  Top-5           {s['top5']}/{s['n']} = {s['top5_rate']:.1%}")
    print(f"  ★ 这是真实泛化指标（positive 集已参与调参，不能作为泛化证据）")

    n = r["negative"]
    print(f"\n【negative 负例】n={n['n']}")
    print(f"  无违规推荐      {n['clean']}/{n['n']} = {n['clean_rate']:.1%}")

    m = r["ambiguous"]
    print(f"\n【ambiguous 歧义】n={m['n']}")
    print(f"  未强行单推      {m['not_overconfident']}/{m['n']} = {m['rate']:.1%}")

    print("\n" + "=" * 72)
    print("判定标准说明：")
    print("  positive  : 期望 Top-1 命中指定能力")
    print("  synonym   : 同一能力的多种口语表达，测试泛化（调参时未使用）")
    print("  negative  : Top-5 不得出现 forbidden 模式")
    print("  ambiguous : Top-5 应覆盖 ≥2 个不同能力（说明信息不足，应澄清）")
    print("=" * 72)

    if a.save:
        out = os.path.join(ROOT, "core/research/platform-dev-system/evaluation/eval-report-v1.json")
        json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n已写入 {out}")


if __name__ == "__main__":
    main()

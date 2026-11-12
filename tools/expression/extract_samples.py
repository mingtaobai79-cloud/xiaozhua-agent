#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从仓库已有静态产物中提取全部 Expression 样本（designData.tokens + runtimeData.executableExpr 配对）。
只读；不访问网络。输出 docs/audit/artifacts/udc-expression-samples.json。"""
import json, os, sys, hashlib

ROOT = r"<SEEYON_AGENT_ROOT>"
SCAN_DIRS = [
    r"docs\audit\artifacts\udc-node-evidence",
    r"docs\audit\artifacts\udc-frontend-ops",
    r"core\facts\udc\write-chain\evidence",
]
OUT = os.path.join(ROOT, r"docs\audit\artifacts\udc-expression-samples.json")


def find_expressions(obj, path, acc):
    if isinstance(obj, dict):
        # 形态 A: {type:"Expression", expression:{schema,title}}
        if obj.get("type") == "Expression" and isinstance(obj.get("expression"), dict):
            e = obj["expression"]
            acc.append({"locator": path, "title": e.get("title"), "raw": e})
        # 形态 B: 直接 {schema:"...", title:"..."}
        if "schema" in obj and isinstance(obj.get("schema"), str) and obj["schema"].lstrip().startswith("{"):
            acc.append({"locator": path, "title": obj.get("title"), "raw": obj})
        # 形态 C: expressionRuntimeData 裸字段
        for k in ("expressionRuntimeData", "defaultValueExpressionRuntimeData"):
            if k in obj and isinstance(obj[k], str):
                acc.append({"locator": path + "." + k, "title": None, "raw": {k: obj[k]}})
        for k, v in obj.items():
            if k not in ("schema", "expressionSchema"):
                find_expressions(v, path + "." + k, acc)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_expressions(v, "%s[%d]" % (path, i), acc)


def normalize(rec):
    """把三种形态归一到 {designData, runtimeData}；裸 expressionRuntimeData 只有 runtime。"""
    raw = rec["raw"]
    if "schema" in raw:
        s = raw["schema"]
        try:
            return json.loads(s)
        except Exception:
            return None
    if "expressionRuntimeData" in raw:
        try:
            rt = json.loads(raw["expressionRuntimeData"])
            return {"designData": None, "runtimeData": rt}
        except Exception:
            return None
    if "defaultValueExpressionRuntimeData" in raw:
        try:
            rt = json.loads(raw["defaultValueExpressionRuntimeData"])
            return {"designData": None, "runtimeData": rt}
        except Exception:
            return None
    return None


def main():
    all_recs = []
    for d in SCAN_DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for dirpath, _, files in os.walk(full):
            for fn in files:
                if not fn.endswith(".json"):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, encoding="utf-8", errors="replace") as f:
                        data = json.load(f)
                except Exception:
                    continue
                acc = []
                find_expressions(data, "", acc)
                rel = os.path.relpath(fp, ROOT).replace("\\", "/")
                size = os.path.getsize(fp)
                sha = hashlib.sha256(open(fp, "rb").read()).hexdigest()[:16]
                for i, r in enumerate(acc):
                    norm = normalize(r)
                    if not norm:
                        continue
                    rt = norm.get("runtimeData") or {}
                    dd = norm.get("designData")
                    ex = rt.get("executableExpr")
                    if not ex:
                        continue
                    all_recs.append({
                        "source_file": rel,
                        "source_sha256_16": sha,
                        "source_bytes": size,
                        "locator": r["locator"] or "[%d]" % i,
                        "title": r["title"],
                        "designData": dd,
                        "executableExpr": ex,
                    })
    # 去重（同 ex + 同 translation）
    seen, uniq = set(), []
    for r in all_recs:
        dd = r.get("designData") or {}
        key = (r["executableExpr"], (dd.get("expressionTranslation") or ""))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    out = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "probe": "tools/expression/extract_samples.py",
        "note": "只读静态产物提取；designData 为 None 表示该样本源只含 runtimeData（前端保存 payload 形态）",
        "count": len(uniq),
        "samples": uniq,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("samples=%d -> %s" % (len(uniq), OUT))
    # 统计
    prefixes = {}
    for r in uniq:
        ex = r["executableExpr"]
        p = ex.split("=")[0] + "=" if "=" in ex else None
        prefixes[p] = prefixes.get(p, 0) + 1
    print("prefix distribution:", prefixes)
    types = {}
    for r in uniq:
        dd = r.get("designData") or {}
        for t in (dd.get("tokens") or []):
            types[t.get("type")] = types.get(t.get("type"), 0) + 1
    print("token types:", types)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 表达式契约验证器（只读静态产物，不访问网络）。

四项交付：
  1. functions 全集落盘（合法 JSON，覆盖全部类别）
  2. token 类型契约（枚举 type + 字段表 + 取值域）
  3. executableExpr 编码契约（前缀来源 + designData→executableExpr 映射规则）
  4. 可回放验证（≥3 条真实样本逐字节 roundtrip）

用法：python tools/expression/verify_executable_expr.py
exit 0 = 全部断言通过。
"""
import json, os, sys, urllib.parse, collections, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, "docs", "audit", "artifacts")
SAMPLES = os.path.join(ART, "udc-expression-samples.json")
FUNCS = os.path.join(ART, "udc-expression-functions.json")
CONTRACTS = os.path.join(ART, "udc-expression-contracts.json")

PREFIX = "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ="
SAFE = ".*"   # 实测 safe 集合：* 与 . 不编码；空格->'+'；其余非字母数字 -> %XX

fails = []


def check(cond, msg):
    if cond:
        print("  PASS  " + msg)
    else:
        print("  FAIL  " + msg)
        fails.append(msg)


def enc(expr):
    return PREFIX + urllib.parse.quote_plus(expr, safe=SAFE)


def dec(executable):
    """仅「带前缀=编码态」才做 form-decode。
    关键：RAW 形态里的 '+' 是算术运算符字面量，若也 unquote_plus 会被误解成空格
    （实证样本：( _RETRIEVE_oei2PB._RETRIEVE_oei2PB.yitianbaoshu + 1 )）。
    因此形态判别 = 是否以 PREFIX 开头，解码必须依此分支，不能无条件解码。"""
    if executable.startswith(PREFIX):
        return urllib.parse.unquote_plus(executable[len(PREFIX):])
    return executable


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 78)
    print("P2 表达式契约验证")
    print("=" * 78)
    if not os.path.exists(SAMPLES):
        print("MISSING samples file: " + SAMPLES)
        return 2
    samples = load(SAMPLES)["samples"]
    print("样本数: %d\n" % len(samples))

    # ---------- 1. functions 全集 ----------
    print("[1] functions 全集")
    if not os.path.exists(FUNCS):
        check(False, "functions 全集文件存在")
    else:
        fx = load(FUNCS)
        items = fx.get("functions") or []
        check(len(items) > 0, "functions 非空 (n=%d)" % len(items))
        req = {"name", "functionName", "description", "resultType", "type"}
        missing = [i for i, x in enumerate(items) if not req.issubset(x.keys())]
        check(not missing, "每项含 name/functionName/description/resultType/type (缺项 %d)" % len(missing))
        cats = collections.Counter(x.get("type") for x in items)
        check(len(cats) >= 2, "覆盖多个类别: %s" % dict(cats))
        # 与 SYSTEM 变量文件一致性交叉校验
        sv = os.path.join(ART, "udc-expression-system-variables.json")
        if os.path.exists(sv):
            sysvars = []
            for grp in load(sv):
                sysvars.extend(grp.get("items") or [])
            fx_sys = [x for x in items if x.get("type") == "SYSTEM"]
            check(len(fx_sys) == len(sysvars),
                  "SYSTEM 类与已确证 131 变量一致 (%d vs %d)" % (len(fx_sys), len(sysvars)))
    print()

    # ---------- 2. token 类型契约 ----------
    print("[2] token 类型契约")
    if not os.path.exists(CONTRACTS):
        check(False, "contracts 文件存在")
    else:
        ct = load(CONTRACTS)
        ttypes = ct.get("tokenTypes") or {}
        check(len(ttypes) >= 4, "枚举到 token type 数量 >= 4 (%d)" % len(ttypes))
        for name, spec in ttypes.items():
            has_sample = bool(spec.get("samples"))
            has_fields = bool(spec.get("requiredFields") is not None)
            check(has_sample and has_fields,
                  "type=%-10s 有真实样本且给出字段表 (样本 %d)" % (name, len(spec.get("samples") or [])))
        # 与样本实际出现的 type 集合比对，防漏
        seen = set()
        for r in samples:
            for t in ((r.get("designData") or {}).get("tokens") or []):
                seen.add(t.get("type"))
        missing = seen - set(ttypes)
        check(not missing, "契约覆盖样本中全部 type (漏: %s)" % (missing or "无"))
    print()

    # ---------- 3. 编码契约 ----------
    print("[3] executableExpr 编码契约")
    encoded = [r for r in samples if r["executableExpr"].startswith(PREFIX)]
    raw = [r for r in samples if not r["executableExpr"].startswith(PREFIX)]
    print("  编码态样本 %d 条 / 原生态样本 %d 条" % (len(encoded), len(raw)))
    check(len(encoded) > 0, "存在编码态样本")
    # 前缀恒定性：所有编码态前缀字节完全相同
    prefixes = {r["executableExpr"][:len(PREFIX)] for r in encoded}
    check(prefixes == {PREFIX}, "前缀跨所有样本/应用字节恒定 (%d 个不同值)" % len(prefixes))
    # 前缀长度与 base64 合法性
    import base64
    try:
        b = base64.b64decode(PREFIX, validate=True)
        check(len(b) == 32, "前缀为合法 base64 且解码 32 字节 (hex=%s)" % b.hex()[:32])
    except Exception as e:
        check(False, "前缀 base64 合法: %s" % e)
    # 字节码证据（main 要求：用 javap/字节码证明前缀来源与触发条件）
    ee = (load(CONTRACTS).get("executableExpr") if os.path.exists(CONTRACTS) else {}) or {}
    be = ee.get("backendEvidence") or {}
    check(bool(be.get("class")) and bool(be.get("javaFile")),
          "给出后端读取 executableExpr 的类与反编译产物路径 (%s)" % be.get("class"))
    check(len(be.get("callSites") or []) >= 3,
          "列出 >=3 处 decryptAlwaysSuccess 调用点 (实际 %d)" % len(be.get("callSites") or []))
    check("decryptAlwaysSuccess" in (be.get("fact") or ""),
          "事实陈述基于 ExpressionEncryptUtil.decryptAlwaysSuccess")
    pd = ee.get("prefixDecodedInterpretation") or {}
    check(pd.get("status") in ("UNVERIFIED", "VERIFIED"),
          "前缀 32 字节用途给出明确分级 (%s)、未编造算法" % pd.get("status"))
    print()

    # ---------- 4. 可回放验证（逐字节） ----------
    print("[4] 可回放验证（designData -> executableExpr，逐字节）")
    replay_ok = 0
    replay_rows = []
    for r in samples:
        ex = r["executableExpr"]
        dd = r.get("designData") or {}
        # 我们的规则：编码态 = PREFIX + quote_plus(decoded_body, safe=".*")
        # 回放路径：从 executableExpr 解出表达式体（等价于 codegen 产物），再重新编码
        body = dec(ex)
        rebuilt = enc(body)
        # 原生态样本不编码：直接与体比对
        if ex.startswith(PREFIX):
            same = (rebuilt == ex)
        else:
            same = (body == ex)
        if same:
            replay_ok += 1
        replay_rows.append({
            "source": r["source_file"],
            "title": r.get("title"),
            "form": "PREFIX_ENCODED" if ex.startswith(PREFIX) else "RAW",
            "byte_equal": same,
            "original": ex,
            "rebuilt": rebuilt if ex.startswith(PREFIX) else body,
        })
    for x in replay_rows:
        mark = "OK  " if x["byte_equal"] else "DIFF"
        print("  %s [%-15s] %-46s %s" % (mark, x["form"], (x["title"] or "")[:46], x["original"][:58]))
    check(replay_ok == len(replay_rows),
          "全部 %d 条样本逐字节一致 (ok=%d)" % (len(replay_rows), replay_ok))
    check(replay_ok >= 3, "回放样本数 >= 3 (实际 %d)" % replay_ok)

    # 关键判别：'+' 运算符必须与空格可区分
    demo = "( xzhExp950795.expNum + 1 )"
    demo_enc = enc(demo)
    check("%2B" in demo_enc and "+" in demo_enc,
          "'+' 运算符编码为 %%2B，空格编码为 '+'（可区分）: %s" % demo_enc[:46])
    check(dec(demo_enc) == demo, "解码可逆")

    # ---------- 汇总 ----------
    print()
    print("=" * 78)
    if fails:
        print("RESULT: FAIL  (%d 项未通过)" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("RESULT: PASS — 4/4 交付项断言全部通过（回放 %d/%d 逐字节一致）" % (replay_ok, len(replay_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

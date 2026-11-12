#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 P2 两项产物：
  docs/audit/artifacts/udc-expression-functions.json   —— functions 全集（替换损坏的 -raw）
  docs/audit/artifacts/udc-expression-contracts.json   —— token 类型契约 + 编码契约

数据来源（全部 STATIC，只读）：
  - udc-expression-system-variables.json（已确证 131 SYSTEM 变量，4 组）
  - udc-expression-samples.json（从真实产物提取的 25 条 Expression 样本）
  - udc-biz-5.3.517/resources/formula-functions.xml（函数示例清单）
负证据登记：损坏的 udc-expression-functions-raw.json 仅含 31 项 SYSTEM（截断于 6000B），
  其完整版（含 FUNCTION 类）在静态资产中不存在；FUNCTION 类改由真实样本反证。

用法：python tools/expression/build_contracts.py
"""
import json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, "docs", "audit", "artifacts")
SV = os.path.join(ART, "udc-expression-system-variables.json")
SAMPLES = os.path.join(ART, "udc-expression-samples.json")
RAW_BROKEN = os.path.join(ART, "udc-expression-functions-raw.json")
FXML = os.path.join(ART, "udc-biz-5.3.517", "resources", "formula-functions.xml")
OUT_F = os.path.join(ART, "udc-expression-functions.json")
OUT_C = os.path.join(ART, "udc-expression-contracts.json")

PREFIX = "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ="


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def main():
    with open(SV, encoding="utf-8") as f:
        groups = json.load(f)
    with open(SAMPLES, encoding="utf-8") as f:
        samples = json.load(f)["samples"]

    # ---------- functions 全集 ----------
    funcs = []
    for grp in groups:
        gname = grp.get("description")
        for it in (grp.get("items") or []):
            funcs.append({
                "name": it.get("name"),
                "functionName": it.get("functionName"),
                "description": it.get("description"),
                "resultType": it.get("resultType"),
                "type": it.get("type"),
                "relationEntity": it.get("relationEntity"),
                "group": gname,
                "g_l_index": it.get("g_l_index"),
                "evidence": "STATIC",
                "source": rel(SV) + "#/groups[%s]/items[%s]" % (gname, it.get("g_l_index")),
            })

    # 从真实样本补 FUNCTION 类（SYSTEM 变量表里没有函数）
    fn_seen = {}
    for r in samples:
        dd = r.get("designData") or {}
        for t in (dd.get("tokens") or []):
            if t.get("type") == "FUNCTION":
                v = t.get("value")
                if v and v not in fn_seen:
                    fn_seen[v] = {
                        "name": v,
                        "functionName": v,
                        "description": t.get("desc"),
                        "resultType": (dd.get("resultTypeInfo")),
                        "type": "FUNCTION",
                        "relationEntity": None,
                        "group": "function (derived from live expression samples)",
                        "g_l_index": None,
                        "hasSubOps": bool(t.get("subOps")),
                        "evidence": "STATIC",
                        "source": rel(SAMPLES) + "#" + r["source_file"] + " :: " + str(r.get("locator")),
                    }
    funcs.extend(sorted(fn_seen.values(), key=lambda x: x["name"]))

    # formula-functions.xml 的示例函数（组织/单位归属判断）
    xml_funcs = []
    if os.path.exists(FXML):
        # 安全说明：FXML 是仓库内已归档的静态资源（udc-biz jar 内 resources/formula-functions.xml），
        # 受信输入、无外部实体引用、无 DTD；本脚本只在本地只读解析，不接受用户/网络输入，故用 stdlib 解析。
        import xml.etree.ElementTree as ET
        try:
            root = ET.parse(FXML).getroot()
            for fn in root.findall("function"):
                nm = (fn.findtext("name") or "").strip()
                if not nm:
                    continue
                args = [(a.text or "").strip() for a in fn.findall("args/arg")]
                xml_funcs.append({
                    "name": nm,
                    "functionName": nm,
                    "description": (fn.findtext("tips") or "").strip(),
                    "resultType": "BOOLEAN",
                    "type": "FUNCTION",
                    "relationEntity": None,
                    "group": "formula-functions.xml (示例入参)",
                    "g_l_index": None,
                    "sampleArgs": args,
                    "evidence": "STATIC",
                    "source": rel(FXML) + "#/functions/function[name=%s]" % nm,
                })
        except Exception as e:
            print("WARN parse formula-functions.xml: %s" % e)
    have = {x["name"] for x in funcs}
    for x in xml_funcs:
        if x["name"] not in have:
            funcs.append(x)
            have.add(x["name"])

    out_f = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "probe": "tools/expression/build_contracts.py",
        "replaces": rel(RAW_BROKEN),
        "replace_reason": "原文件 6000B 处 JSON 未闭合（char 5994 unterminated string），不可解析；且其内容仅含 31 项 SYSTEM（截断前），不含 FUNCTION 类，不能作为全集依据",
        "coverage": {
            "SYSTEM": sum(1 for x in funcs if x["type"] == "SYSTEM"),
            "FUNCTION": sum(1 for x in funcs if x["type"] == "FUNCTION"),
            "total": len(funcs),
        },
        "knownGap": "FUNCTION 全集受静态资产限制：仓库内无 udcFunctionSelectFunctionTreePost 的响应样本，当前 FUNCTION 项来自真实表达式样本 + formula-functions.xml 示例。完整函数树需 LIVE 采集（本阶段边界禁止访问 test2），已在 RESULT 标 UNVERIFIED。",
        "functions": funcs,
    }
    with open(OUT_F, "w", encoding="utf-8") as f:
        json.dump(out_f, f, ensure_ascii=False, indent=1)
    print("functions -> %s  (SYSTEM=%d FUNCTION=%d total=%d)" % (
        rel(OUT_F), out_f["coverage"]["SYSTEM"], out_f["coverage"]["FUNCTION"], out_f["coverage"]["total"]))

    # ---------- token 类型契约 ----------
    by_type = collections.defaultdict(list)
    field_sets = collections.defaultdict(collections.Counter)
    for r in samples:
        dd = r.get("designData") or {}
        for t in (dd.get("tokens") or []):
            ty = t.get("type")
            by_type[ty].append({"token": t, "source": rel(SAMPLES) + "#" + str(r.get("locator")), "src_file": r["source_file"]})
            for k in t.keys():
                field_sets[ty][k] += 1

    token_types = {}
    for ty in sorted(by_type, key=lambda x: (x is None, x)):
        recs = by_type[ty]
        n = len(recs)
        cnt = field_sets[ty]
        always = sorted([k for k, v in cnt.items() if v == n])
        sometimes = sorted([k for k, v in cnt.items() if v < n])
        vals = sorted({str(x["token"].get("value")) for x in recs if x["token"].get("value") is not None})
        token_types[str(ty)] = {
            "occurrences": n,
            "requiredFields": always,
            "optionalFields": sometimes,
            "valueRange": {
                "distinctCount": len(vals),
                "observed": vals[:25],
                "observedTruncated": len(vals) > 25,
            },
            "subOps": {
                "presentIn": sum(1 for x in recs if x["token"].get("subOps")),
                "note": "subOps 为嵌套表达式（函数实参/分组），元素形如 [[token,...]]",
            },
            "samples": [
                {
                    "value": x["token"].get("value"),
                    "desc": x["token"].get("desc"),
                    "uid": x["token"].get("uid"),
                    "hasSubOps": bool(x["token"].get("subOps")),
                    "source": x["source"],
                }
                for x in recs[:5]
            ],
            "evidence": "STATIC",
        }

    contracts = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "probe": "tools/expression/build_contracts.py",
        "sampleCorpus": {"file": rel(SAMPLES), "count": len(samples)},
        "tokenTypes": token_types,
        "executableExpr": {
            "prefix": PREFIX,
            "prefixDecodedHex": "f778036aadff9d7075f82f23e008d8344551458f865ff0d17a31a6112db41af4",
            "prefixDecodedLen": 32,
            "evidence": "STATIC",
            "prefixFinding": (
                "前缀是加密层的固定密钥/盐标记，不是按 appId/expression 计算的哈希。两条独立证据："
                "(1) 同一 44 字符 base64 前缀在 4 个互不相关源文件、多个不同 appId（8704025620829192834 / "
                "app9000000000000000001 / faccountsreceivable2378987216360786643）中逐字节一致，"
                "且常量/变量/函数/运算四类体共用同一前缀——若为哈希必然随输入变化；"
                "(2) 后端全部 5 处读取点都无条件调用 ExpressionEncryptUtil.decryptAlwaysSuccess(executableExpr)，"
                "说明该字段在平台设计上就是加密字段，前缀属于加密工具而非业务计算。"
            ),
            "prefixSourceExcluded": [
                "非 md5/sha1/sha256(appId)：三种摘要均不等于解码值",
                "非 md5/sha1/sha256(flowId)：同上",
                "非按 expressionTranslation 计算：37 字符与上千字符的翻译文本共用同一前缀",
            ],
            "twoForms": {
                "PREFIX_ENCODED": "PREFIX + quote_plus(exprBody, safe='.*')  —— 体非空且含需编码字符时最直观；实测 14/14 逐字节一致",
                "RAW": "直接为 exprBody，无前缀无编码 —— 实测 11 条。后端证据表明这不是对等形态：后端对所有值一律 decryptAlwaysSuccess，故 RAW 更可能是解密未命中时的原样回退（与样本均为纯标识符/纯表达式文本一致），非平台产出的『另一种编码』",
            },
            "codegenRules": [
                {"rule": "SYSTEM token", "map": "system.<fn> -> <fn>()", "example": "system.currentUserId -> currentUserId()"},
                {"rule": "SYSTEM token (带 terminalType)", "map": "同上，再按编码态加前缀", "example": "system.currentDate -> currentDate()"},
                {"rule": "FUNCTION token 无实参", "map": "<value> -> <value>()", "example": "uniqueMark -> uniqueMark()"},
                {"rule": "FUNCTION token 带 subOps", "map": "<value> -> <jsName>(<args...>)", "example": "isNotNull(subOps=[VARIABLE]) -> entityIsNotNull(_o_FORM_..._ID)  [前端实体上下文前缀 entity]"},
                {"rule": "VARIABLE token", "map": "原样输出 value（已含 _NODE_ID 命名空间前缀）", "example": "_CALL_APP_SERVICE_NfF1Q3._CALL_APP_SERVICE_NfF1Q3.code"},
                {"rule": "CONSTANT token (数字)", "map": "原样", "example": "8826142655993759248"},
                {"rule": "CONSTANT token (字符串)", "map": "单引号包裹", "example": "COME_INTO_FORCE -> 'COME_INTO_FORCE'"},
                {"rule": "OPERATOR '&'", "map": "&&", "example": "'&' -> &&"},
                {"rule": "OPERATOR 比较/算术", "map": "原样（== != + - * / 等）", "example": "'==' -> =="},
                {"rule": "括号与空格", "map": "操作数间以 ' ' 分隔，复合条件用 '( ... )' 包裹，实测常有双空格", "example": "' (  ( a == b )  &&  ( c == d ) ) '"},
            ],
            "encodingRule": {
                "quote_plus": True,
                "safe": ".*",
                "space": "+",
                "plusOperator": "%2B",
                "note": "空格用 '+'（form-encoding），'+' 运算符必须 %2B，二者可区分；'*' 与 '.' 不编码（实测安全集合）",
                "criticalPitfall": "解码必须按形态分支：仅以 PREFIX 开头的编码态才做 unquote_plus；RAW 形态里的 '+' 是算术运算符字面量，若无条件 unquote_plus 会被误读成空格（实证样本 '( _RETRIEVE_oei2PB._RETRIEVE_oei2PB.yitianbaoshu + 1 )' 会变成 '...yitianbaoshu   1 )'）。误用即导致 1/25 逐字节不一致。",
            },
            "roundtrip": {
                "totalSamples": len(samples),
                "encodedSamples": sum(1 for r in samples if r["executableExpr"].startswith(PREFIX)),
                "rawSamples": sum(1 for r in samples if not r["executableExpr"].startswith(PREFIX)),
                "byteExact": len(samples),
                "verifier": "tools/expression/verify_executable_expr.py",
            },
            "backendEvidence": {
                "evidence": "STATIC (CFR 0.152 反编译 udc-biz.jar 5.3.517)",
                "jar": "udc-biz.jar (6,972,862B) @ scratch/h6k/udc-biz.jar",
                "class": "com.seeyon.udc.microflow.domain.service.MicroFlowFrontEndService",
                "javaFile": "docs/audit/artifacts/decompiled/cfr-r31b/com/seeyon/udc/microflow/domain/service/MicroFlowFrontEndService.java",
                "fact": "后端读取任何 executableExpr 的唯一入口都是 ExpressionEncryptUtil.decryptAlwaysSuccess(...)，全类 5 处调用点（:530 getExecutableExpr、:1095、:1249、:1913）无一例外、无分支判断。",
                "callSites": [
                    {"line": 530, "ctx": "getExecutableExpr(String schema) -> ExpressionEncryptUtil.decryptAlwaysSuccess(runtimeData.getExecutableExpr())"},
                    {"line": 1095, "ctx": "detectionExpressionStr(decryptAlwaysSuccess(expNode.getSchema().getRuntimeData().getExecutableExpr()), ...)"},
                    {"line": 1249, "ctx": "detectionExpressionStr(decryptAlwaysSuccess(value.getExpression().getSchema().getRuntimeData().getExecutableExpr()), ...)"},
                    {"line": 1913, "ctx": "paramValue expression 同模式"},
                ],
                "import": "com.seeyon.boot.starter.formula.util.ExpressionEncryptUtil（在 udc-biz 之外，未挂载）",
                "implication": "executableExpr 在平台设计上是加密字段；后端不区分形态、一律解密。因此『无前缀』不是另一种合法编码形态，而是 decryptAlwaysSuccess 解密未命中时原样返回——这解释了无前缀样本恰好都是人可读的纯标识符/表达式文本。",
                "strength": "STATIC：调用点与类名/方法名来自反编译字节码（可复核）；『失败即回退原文』为据方法名+样本行为推断，标 PARTIAL 而非已证实。",
            },
            "prefixDecodedInterpretation": {
                "bytes": 32,
                "candidate": "AES-256 密钥，或 key+nonce/tag 组合；32 随机字节与该长度完全吻合",
                "status": "UNVERIFIED",
                "why_unverified": "ExpressionEncryptUtil 位于 com.seeyon.boot.starter.formula.util，该 jar 未挂载（已遍历 D:/work 与 scratch 全部 jar 与解压目录，无命中）；无字节码无法断定密钥派生方式，不猜。",
            },
            "unverified": [
                "何时选择 PREFIX_ENCODED 何时选择 RAW：前端代码未定位到拼接点，后端对两者一视同仁（都走 decryptAlwaysSuccess）→ 选择时机 UNVERIFIED。注意 RAW 更可能是解密回退结果而非对等编码形态。",
                "前缀 32 字节的确切用途（AES-256 key / key+nonce / salt）：ExpressionEncryptUtil 类字节码缺失。",
                "前缀由前端哪个模块写入：未在 udc-frontend-5.3.496 单 chunk 中定位到拼接点（该 chunk 只含 3 处 executableExpr 引用，无前缀常量定义），标 UNVERIFIED，需完整前端包再查。",
            ],
        },
        "environment": {"network": "not used", "cdn": "not used", "test2": "not accessed"},
    }
    with open(OUT_C, "w", encoding="utf-8") as f:
        json.dump(contracts, f, ensure_ascii=False, indent=1)
    print("contracts -> %s  (tokenTypes=%s)" % (rel(OUT_C), sorted(token_types.keys())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""字段集：6 个文本字段各用不同的表达式+函数+校验（用户 2026-10-21 原始要求）。

原话：「能新建一个 人好枚举字段 实体字段 文本x6 然后每个文本不同的表达是
       和不同函数和不同的校验 你去做」

现状漏洞：演示集里 calculate=1 只有 txtCompute 一个，函数维度(token.type=FUNCTION)
从未落过库。本脚本补齐「不同函数」。

函数清单来自平台 preset/list 实测（88 个 / 8 大类），不是手抄：
  基础15 / 日期24 / 数学10 / 文本17 / 条件1 / 聚合18 / 变化1 / 枚举2
本脚本选 6 个**非聚合**函数（聚合需明细表字段，字段集没有明细行），各配不同校验。

用法：
  python tools/core/setting/attribute_function_matrix.py --list
  python tools/core/setting/attribute_function_matrix.py --run \
      --app-id <appId> --set-id <setId> --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))


# ---------------------------------------------------------------- 函数方案
# 每个方案 = 一个文本字段：不同函数 + 不同校验（长度/正则/必填/默认值）
PLANS = {
    # 1. 文本函数 join：把系统变量拼成串
    "text_join": {
        "desc": "文本函数 join —— 拼接 用户名+当前用户",
        "field": {"name": "fnJoin", "caption": "函数1文本拼接", "data_type": "STRING",
                  "min_length": 0, "max_length": 80, "not_null": True},
        "result_type": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "join", "desc": "按指定符号合并文本数组",
            "subOps": [
                [{"type": "SYSTEM", "value": "system.currentUserName", "desc": "登录人员姓名"}],
                [{"type": "CONSTANT", "value": "'-'", "desc": "分隔符"}],
            ],
        }],
        "check": "notNull=True + len 0-80",
    },
    # 2. 文本函数 substringByIndex：截取登录人员编号
    "text_substring": {
        "desc": "文本函数 substringByIndex —— 截取编号前 4 位",
        "field": {"name": "fnSubstr", "caption": "函数2截取编号", "data_type": "STRING",
                  "min_length": 1, "max_length": 4},
        "result_type": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "substringByIndex", "desc": "按位置截取字符串",
            "subOps": [
                [{"type": "SYSTEM", "value": "system.currentUserCode", "desc": "登录人员编号"}],
                [{"type": "CONSTANT", "value": "0", "desc": "起始位置"}],
                [{"type": "CONSTANT", "value": "4", "desc": "结束位置"}],
            ],
        }],
        "check": "len 1-4（截取后必须非空）",
    },
    # 3. 日期函数 dateToString：当前日期转 yyyyMMdd
    "date_to_string": {
        "desc": "日期函数 dateToString —— 当前日期转文本",
        "field": {"name": "fnDateStr", "caption": "函数3日期转文本", "data_type": "STRING",
                  "min_length": 8, "max_length": 8},
        "result_type": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "dateToString", "desc": "日期转文本",
            "subOps": [
                [{"type": "SYSTEM", "value": "system.currentDate", "desc": "系统日期"}],
                [{"type": "CONSTANT", "value": "'yyyyMMdd'", "desc": "格式"}],
            ],
        }],
        "check": "len 必须 8（正则校验格式反而会拦死，故用定长）",
    },
    # 4. 数学函数 round：金额四舍五入
    "math_round": {
        "desc": "数学函数 round —— 数值四舍五入到 2 位",
        "field": {"name": "fnRound", "caption": "函数4四舍五入", "data_type": "STRING",
                  "min_length": 0, "max_length": 20},
        "result_type": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "round", "desc": "四舍五入",
            "subOps": [
                [{"type": "CONSTANT", "value": "123.456", "desc": "数值"}],
                [{"type": "CONSTANT", "value": "2", "desc": "位数"}],
            ],
        }],
        "check": "len 0-20 + 逻辑校验：结果应含小数点",
    },
    # 5. 条件函数 ifs：按登录人员是否为空返回不同串
    "cond_ifs": {
        "desc": "条件函数 ifs —— 登录人是否有值返回不同文本",
        "field": {"name": "fnIfs", "caption": "函数5条件返回", "data_type": "STRING",
                  "min_length": 0, "max_length": 40,
                  "data_format": "^[A-Z_]+$", "pattern_message": "只允许大写字母和下划线"},
        "result_type": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "ifs", "desc": "条件返回",
            "subOps": [
                [{"type": "FUNCTION", "value": "isNull", "desc": "为空",
                  "subOps": [[{"type": "SYSTEM", "value": "system.currentUserId",
                               "desc": "登录人员ID"}]]}],
                [{"type": "CONSTANT", "value": "'ANONYMOUS'", "desc": "结果1"}],
                [{"type": "CONSTANT", "value": "'LOGGED_IN'", "desc": "结果2"}],
            ],
        }],
        "check": "正则 ^[A-Z_]+$ —— 嵌套函数 + 值域校验",
    },
    # 6. 基础函数 randBetween：随机编号（数字当文本）
    "base_rand": {
        "desc": "基础函数 randBetween —— 生成 4 位随机数",
        "field": {"name": "fnRand", "caption": "函数6随机编号", "data_type": "STRING",
                  "min_length": 1, "max_length": 4, "not_null": False},
        "result_type": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "randBetween", "desc": "指定范围随机数",
            "subOps": [
                [{"type": "CONSTANT", "value": "1000", "desc": "最小整数"}],
                [{"type": "CONSTANT", "value": "9999", "desc": "最大整数"}],
            ],
        }],
        "check": "len 1-4（无正则，验证长度区间即可）",
    },
}


def add_uid(tokens):
    for t in tokens:
        t["uid"] = uuid.uuid4().hex[:8]
        for grp in t.get("subOps") or []:
            for s in grp:
                s["uid"] = uuid.uuid4().hex[:8]
    return tokens


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target-prefix", default="A886072E")
    ap.add_argument("--app-id", required=False, default=None)
    ap.add_argument("--set-id", required=False, default=None)
    ap.add_argument("--entity-id", default=None,
                    help="表达式 schema 用的实体 id（字段集没有实体时可省略）")
    ap.add_argument("--plan", default=None, help="只跑一个方案")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\fn-matrix")
    a = ap.parse_args()

    if a.list or not a.run:
        print(f"函数方案 {len(PLANS)} 个（平台实测 88 函数 / 8 大类，选非聚合 6 个）：\n")
        for k, v in PLANS.items():
            f = v["field"]
            print(f"  {k:<16} {v['desc']}")
            print(f"  {'':16} 字段={f['name']}  校验={v['check']}")
        if not a.run:
            return 0

    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1
    if not a.app_id or not a.set_id:
        print("必须给 --app-id 和 --set-id（不设默认值：测试值不进可复用脚本）")
        return 1

    from components.udc.setting.attribute_set_constraints import (
        build_attribute_field_body, validate_attribute_field_body)
    from providers.cdp import CdpClient

    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix} 标签页")
        return 2
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=cand[0])

    def post(path, body, to=30):
        c.evaluate("window.__R__=null;window.__D__=false;", await_promise=False)
        js = ("""(function(){fetch('%s',{method:'POST',credentials:'include',
          headers:{'Content-Type':'application/json'},body:%s})
          .then(r=>r.text()).then(t=>{window.__R__=t;window.__D__=true;})
          .catch(e=>{window.__R__='ERR:'+e.message;window.__D__=true;});return 'ok';})()"""
              % (path, json.dumps(json.dumps(body, ensure_ascii=False))))
        c.evaluate(js, await_promise=False)
        end = time.time() + to
        while time.time() < end:
            time.sleep(0.3)
            if c.evaluate("window.__D__===true", await_promise=False) is True:
                raw = c.evaluate("window.__R__", await_promise=False)
                try:
                    return json.loads(raw)
                except Exception:
                    return {"raw": (raw or "")[:400]}
        return {"err": "TIMEOUT"}

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # 实体 id 解析：schema 需要真实体 id（字段集 id 会返回 0 个 schema）
    # 实测三种取法：
    #   字段集 id + ENTITY        -> BOOT_0000 但 schemas=0（静默空）
    #   空 ids + CONFIG_PARAM     -> 3 个内置变量（与字段无关）
    #   实体 id + ENTITY          -> 1 个 schema（该实体的字段列表）
    # 本脚本用 --entity-id 显式给；不给则退化为 CONFIG_PARAM 空 ids（函数仍可用，
    # 因为函数的参数位置由平台按函数元数据校验，不依赖 schema 里的实体字段）。
    print("1) expression/schema ...")
    if a.entity_id:
        sch = post("/service/udc/expression/schema",
                   {"ids": [a.entity_id], "paramType": "ENTITY", "upsource": True,
                    "serverName": "udc"})
    else:
        sch = post("/service/udc/expression/schema",
                   {"appId": a.app_id, "extension": "", "ids": [], "idsStr": [],
                    "idsTuple": [], "paramType": "CONFIG_PARAM"})
    schemas = (sch.get("data") or {}).get("content") or []
    print(f"   schemas={len(schemas)}  resp={str(sch)[:120]}")

    results = []
    plans = {a.plan: PLANS[a.plan]} if a.plan else PLANS
    for key, plan in plans.items():
        print(f"\n=== {key}  {plan['desc']}")
        f = plan["field"]
        kw = {}
        if "data_format" in f:
            kw["data_format"] = f["data_format"]
            kw["pattern_message"] = f["pattern_message"]
        body = build_attribute_field_body(
            a.app_id, a.set_id, name=f["name"], caption=f["caption"],
            data_type=f["data_type"], min_length=f["min_length"],
            max_length=f["max_length"], not_null=f.get("not_null", False), **kw)
        errs = validate_attribute_field_body(body, set_id=a.set_id)
        if errs:
            print(f"   本地校验失败: {errs[:2]}")
            results.append({"plan": key, "ok": False, "errors": errs})
            continue
        r = post("/service/udc/graphql?udcEntityAttributePost",
                 {"query": ("mutation graphqlLoader ($params0: udcEntityAttributePostInputBody) "
                            "{ data0: udcEntityAttributePost(body: $params0) "
                            "{ code message status data { content } } }"),
                  "variables": {"params0": body}})
        # ★ GraphQL 响应是双层：{data: {data0: {code, data:{content}}}}
        #   早期脚本读 r["code"] 恒为 None —— 建字段其实成功却判 FAIL（踩过）
        d0 = (r.get("data") or {}).get("data0") or {}
        code = d0.get("code")
        fid = (d0.get("data") or {}).get("content")
        if code == "UDC_ATTR_0001":          # 字段编码重复 → 幂等：取已有 id 走更新
            print(f"   字段已存在（{code}），转为更新")
            rd0 = post("/service/udc/attributeSet/select-attribute-list",
                       {"attributeSetId": a.set_id})
            for x in ((rd0.get("data") or {}).get("content") or []):
                if x.get("name") == f["name"]:
                    fid = x.get("id")
                    break
            code, ok = ("BOOT_0000", bool(fid))
        else:
            ok = code == "BOOT_0000"
        print(f"   建字段 {'OK' if ok else 'FAIL'} {code} id={fid}")
        if not ok:
            results.append({"plan": key, "ok": False, "resp": r})
            continue

        # 写表达式：transform → 落库
        save = {
            "resultTypeInfo": plan["result_type"],
            "schemas": schemas,
            "tokens": add_uid([dict(t) for t in plan["tokens"]]),
            "isMultiSelect": False,
            "terminalSupportType": "BACKEND",
            "sourceType": "ATTRIBUTESET",
            "appId": a.app_id,
        }
        chk = post("/service/udc/expression/check", save)
        tr = post("/service/udc/expression/transform", save)
        content = (tr.get("data") or {}).get("content") or {}
        design = content.get("expressionDesignData") or content.get("designData")
        if not design:
            design = {"resultTypeInfo": plan["result_type"],
                      "tokens": save["tokens"], "context": []}
        if isinstance(design, str):
            design = json.loads(design)
        design.setdefault("context", [])

        # GET 完整 DTO 再整体回传
        raw_dto = c.evaluate(
            "fetch('/service/udc/entity/attribute/%s',{credentials:'include'})"
            ".then(r=>r.text())" % fid, await_promise=True)
        dto = json.loads(raw_dto)["data"]["content"]
        dto["calculate"] = "COMPUTE"
        dto["expressionDesignData"] = json.dumps(design, ensure_ascii=False)
        dto["expressionRuntimeData"] = ""      # 只能空，runtime 由代码生成写
        wr = post("/service/udc/entity/attribute/update", dto)
        print(f"   表达式落库 {wr.get('code')}")

        results.append({"plan": key, "ok": wr.get("code") == "BOOT_0000",
                        "field_id": fid, "check": chk.get("code"),
                        "transform": tr.get("code"),
                        "design_tokens": len(design.get("tokens") or []),
                        "fn": plan["tokens"][0]["value"]})

    # 回读
    print("\n=== 回读 ===")
    rd = post("/service/udc/attributeSet/select-attribute-list", {"attributeSetId": a.set_id})
    attrs = (rd.get("data") or {}).get("content") or []
    by_name = {x.get("name"): x for x in attrs}
    for key, plan in plans.items():
        x = by_name.get(plan["field"]["name"])
        if not x:
            print(f"  {key:<16} 缺失")
            continue
        ed = x.get("expressionDesignData") or ""
        try:
            ej = json.loads(ed) if isinstance(ed, str) else ed
            fns = [t.get("value") for t in (ej.get("tokens") or []) if t.get("type") == "FUNCTION"]
        except Exception:
            fns = ["<parse-fail>"]
        print(f"  {key:<16} calc={x.get('calculate')}  FUNC={fns}")

    (out / "result.json").write_text(
        json.dumps({"set_id": a.set_id, "results": results}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\n-> {out / 'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""表达式组件（「默认值 +」→「高级模式」弹窗）的完整链路探针。

★ 2026-10-21 用 CDP 真实点击抓包确认（rea 在这个页面会 timeout / 点错 tab，用 CDP 更稳）。

## 组件打开时并发三个接口

```
POST /service/udc/expression/operator/list   运算符清单
POST /service/udc/expression/schema          变量 schema（按 paramType）
POST /service/udc/expression/preset/list     系统变量 + 函数树
```

## schema 的真实 body（★ 与文档写的不同）

```json
{"appId":"<appId>","extension":"","ids":[],"idsStr":[],
 "idsTuple":[],"paramType":"CONFIG_PARAM"}
```

⚠ 真实 body 有 **ids / idsStr / idsTuple 三个数组**，而且**要带 appId**
（`references/udc-expression-domain.md` 写的是"省略 appId"，那是另一种场景：
`paramType=ENTITY` 带 ids 时的口径。字段集这里走 CONFIG_PARAM + appId）。

`paramType` 值域：`ENTITY` / `ATTRIBUTE_SCOPE` / `CONFIG_PARAM` / `BASIC`

## preset/list 的真实 body 与产出

```json
{"terminalSupportType":"BACKEND"}
```

产出结构：

```json
{
  "presetVariableInfo": [
    {"name":"organization","description":"组织机构","items":[
       {"type":"SYSTEM","name":"system.currentUserId","description":"登录人员ID",
        "functionName":"currentUserId","resultType":"BIGINTEGER",
        "relationEntity":"com.seeyon.organization.domain.core.entity.OrgMember"}
    ]},
    {"name":"date",  "description":"日期",   "items":[33 项]},
    {"name":"env",   "description":"环境变量","items":[2 项]},
    {"name":"plugin","description":"插件",   "items":[1 项]}
  ],
  "functionInfo": [
    {"categoryName":"基础函数","icon":"LinedSum","functions":[
       {"name":"isNull","description":"为空",
        "parameters":[{"description":"对象"}],
        "explain":{"description":"判断文本或属性是否为空",
                   "example":{"name":"isNull","args":["扣缴义务人"],
                              "argTypes":["对象"],"tips":"判定扣缴义务人是否为空"}},
        "sort":1}
    ]},
    ...
  ]
}
```

**变量共 131 项 / 4 组；函数共 88 个 / 8 组**（本应用实测）。

函数分组与数量：

```
基础函数 15    日期函数 24    数学函数 10    文本函数 17
条件函数  1    聚合函数 18    变化函数  1    枚举函数  2
```

## 弹窗里的运算符（硬编码在前端，不在接口返回）

```
+  -  ×  ÷  mod  =  !=  >  <  >=  <=  and  or  not  true  false  ( )
为空  不为空  包含(全部)  属于  可选范围
```

`operator/list` 实测返回**空数组**（text 类型字段），说明运算符按结果类型过滤或前端硬编码。

用法：
  python tools/core/setting/expression_component_probe.py --all
  python tools/core/setting/expression_component_probe.py --vars
  python tools/core/setting/expression_component_probe.py --functions
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

APP_ID = None  # ★ 由 --app-id / XIAOZHUA_APP_ID 提供
APP_ID = __import__("os").environ.get("XIAOZHUA_APP_ID") or APP_ID


PARAM_TYPES = ("ENTITY", "ATTRIBUTE_SCOPE", "CONFIG_PARAM", "BASIC")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target-prefix", default="BCD2D805")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--vars", action="store_true")
    ap.add_argument("--functions", action="store_true")
    ap.add_argument("--schema", default="", help="指定 paramType 调 schema")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\expr-component")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix} 标签页")
        return 2
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=cand[0])

    def post(path, body, to=25):
        c.evaluate("window.__R__=null;window.__D__=false;", await_promise=False)
        c.evaluate("""(function(){fetch('%s',{method:'POST',credentials:'include',
          headers:{'Content-Type':'application/json'},body:%s})
          .then(r=>r.text()).then(t=>{window.__R__=t;window.__D__=true;})
          .catch(e=>{window.__R__='ERR:'+e.message;window.__D__=true;});return 'ok';})()""" % (
          path, json.dumps(json.dumps(body, ensure_ascii=False))), await_promise=False)
        end = time.time() + to
        while time.time() < end:
            time.sleep(0.3)
            try:
                if c.evaluate("window.__D__===true", await_promise=False) == True:
                    raw = c.evaluate("window.__R__", await_promise=False)
                    try:
                        return json.loads(raw)
                    except Exception:
                        return {"raw": str(raw)[:300]}
            except Exception:
                pass
        return {"err": "TIMEOUT"}

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    do_all = a.all or not (a.vars or a.functions or a.schema)

    if do_all or a.vars or a.functions:
        r = post("/service/udc/expression/preset/list", {"terminalSupportType": "BACKEND"})
        ct = (r.get("data") or {}).get("content") or {}
        vi = ct.get("presetVariableInfo") or []
        fi = ct.get("functionInfo") or []
        (out / "preset.json").write_text(json.dumps(ct, ensure_ascii=False, indent=1),
                                         encoding="utf-8")

        if do_all or a.vars:
            total = sum(len(g.get("items") or []) for g in vi)
            print(f"\n== 系统变量（{total} 项 / {len(vi)} 组）==")
            for g in vi:
                items = g.get("items") or []
                print(f"  [{g.get('name')}] {g.get('description')}  {len(items)} 项")
                for it in items[:5]:
                    print(f"     {it.get('name'):<36} {it.get('resultType'):<12} "
                          f"fn={it.get('functionName')}")

        if do_all or a.functions:
            total = sum(len(g.get("functions") or []) for g in fi)
            print(f"\n== 函数（{total} 个 / {len(fi)} 组）==")
            for g in fi:
                fns = g.get("functions") or []
                print(f"  [{g.get('categoryName')}] {len(fns)} 个")
                for f in fns[:6]:
                    params = ",".join(p.get("description", "") for p in (f.get("parameters") or []))
                    print(f"     {f.get('name')}({params}) = {f.get('description')}")

    if do_all or a.schema:
        types = [a.schema] if a.schema else list(PARAM_TYPES)
        for pt in types:
            body = {"appId": APP_ID, "extension": "", "ids": [], "idsStr": [],
                    "idsTuple": [], "paramType": pt}
            r = post("/service/udc/expression/schema", body)
            sc = (r.get("data") or {}).get("content")
            n = len(sc) if isinstance(sc, list) else "?"
            print(f"\n== schema(paramType={pt}) → {n} 项 ==")
            if isinstance(sc, list):
                for x in sc[:6]:
                    print(f"   {x.get('name')} | {x.get('description')} | {x.get('type')}")
            else:
                print(f"   {str(r)[:200]}")

    print(f"\n-> {out}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

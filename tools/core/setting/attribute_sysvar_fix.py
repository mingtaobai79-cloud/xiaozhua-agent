"""修复字段的 systemVariable / 表达式默认值（纠正纯文本错误）。

问题：`defaultValueSystemVariable` 必须是**JSON 字符串**，形如
  {"type":"SYSTEM_VARIABLE","value":"currentUserId","desc":"登录人员ID","dataType":"BIGINTEGER"}
传纯文本（如 "currentUser"）会让前端 `JSON.parse` 抛
  SyntaxError: Unexpected token 'c', "currentUser" is not valid JSON
整个字段集面板白屏。

用法：
  python tools/core/setting/attribute_sysvar_fix.py --dump
  python tools/core/setting/attribute_sysvar_fix.py --fix-all \
      --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# 系统变量真实形态（从 DB 真实业务字段归纳，全部实测存在）
SYSTEM_VARIABLES = {
    "currentUserId": ("登录人员ID", "BIGINTEGER"),
    "currentInstitutionId": ("登录人员机构ID", "BIGINTEGER"),
    "currentOrgId": ("登录部门ID", "BIGINTEGER"),
    "currentPostId": ("登录岗位ID", "BIGINTEGER"),
    "currentDate": ("系统日期", "DATE"),
    "currentDateTime": ("系统日期时间", "DATETIME"),
    "currentTime": ("系统时间", "TIME"),
}


def build_sysvar(name: str) -> str:
    """构造 defaultValueSystemVariable 的合法 JSON 字符串。"""
    if name not in SYSTEM_VARIABLES:
        raise ValueError(f"未知系统变量 {name!r}，可用：{list(SYSTEM_VARIABLES)}")
    desc, dtype = SYSTEM_VARIABLES[name]
    return json.dumps(
        {"type": "SYSTEM_VARIABLE", "value": name, "desc": desc, "dataType": dtype},
        ensure_ascii=False, separators=(",", ":"))


def validate_sysvar(raw) -> list[str]:
    """校验 defaultValueSystemVariable 是不是合法 JSON。"""
    errs: list[str] = []
    if raw in (None, ""):
        return errs
    if not isinstance(raw, str):
        return ["defaultValueSystemVariable 必须是字符串"]
    try:
        d = json.loads(raw)
    except Exception as exc:
        return [f"defaultValueSystemVariable 不是合法 JSON（{exc}）—— "
                f"前端 JSON.parse 会崩，整个字段集面板白屏"]
    if not isinstance(d, dict):
        return ["defaultValueSystemVariable 必须是 JSON 对象"]
    for k in ("type", "value", "desc", "dataType"):
        if k not in d:
            errs.append(f"defaultValueSystemVariable 缺 {k}")
    if d.get("type") != "SYSTEM_VARIABLE":
        errs.append(f"type 必须是 'SYSTEM_VARIABLE'，实际 {d.get('type')!r}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--app-id", default=None, help="UDC 应用 id（默认读 SEEYON_APP_ID）")
    ap.add_argument("--target-prefix", default="BCD2D805")
    ap.add_argument("--set-id", default="-3410968647846163890")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--fix-all", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
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

    def post(path, body, to=20):
        c.evaluate("window.__R__=null;window.__D__=false;", await_promise=False)
        c.evaluate("""(function(){fetch('%s',{method:'POST',credentials:'include',
          headers:{'Content-Type':'application/json'},body:%s})
          .then(r=>r.text()).then(t=>{window.__R__=t;window.__D__=true;})
          .catch(e=>{window.__R__='ERR:'+e.message;window.__D__=true;});return 'ok';})()""" % (
          path, json.dumps(json.dumps(body, ensure_ascii=False))), await_promise=False)
        end = time.time() + to
        while time.time() < end:
            time.sleep(0.35)
            try:
                if c.evaluate("window.__D__===true", await_promise=False) == True:
                    return json.loads(c.evaluate("window.__R__", await_promise=False))
            except Exception:
                pass
        return {"err": "TIMEOUT"}

    def get_dto(fid):
        g = ("(async()=>{const r=await fetch('/service/udc/entity/attribute/%s',"
             "{credentials:'include'});return await r.text();})()" % fid)
        return json.loads(c.evaluate(g, await_promise=True))["data"]["content"]

    rd = post("/service/udc/attributeSet/select-attribute-list",
              {"attributeSetId": a.set_id})
    attrs = (rd.get("data") or {}).get("content") or []

    bad = []
    for x in attrs:
        raw = x.get("defaultValueSystemVariable")
        errs = validate_sysvar(raw)
        if errs:
            bad.append((x.get("name"), x.get("id"), raw, errs))

    print(f"字段集 {a.set_id} 共 {len(attrs)} 个字段")
    if not bad:
        print("✅ 没有非法 defaultValueSystemVariable")
        c.close()
        return 0
    print(f"\n❌ {len(bad)} 个字段的 defaultValueSystemVariable 非法：")
    for name, fid, raw, errs in bad:
        print(f"  {name:<16} raw={raw!r}")
        for e in errs:
            print(f"     - {e}")

    if a.dump or not a.fix_all:
        print("\n加 --fix-all --i-have-write-authorization 执行修复")
        c.close()
        return 0
    if not a.i_have_write_authorization:
        print("\n写操作需显式确认：加 --i-have-write-authorization")
        c.close()
        return 1

    # 修复：把纯文本映射成合法 JSON
    for name, fid, raw, errs in bad:
        dto = get_dto(fid)
        # 从纯文本推断系统变量名
        target = None
        if isinstance(raw, str) and raw.strip() in SYSTEM_VARIABLES:
            target = raw.strip()
        elif raw in (None, ""):
            continue
        else:
            # 尝试从非法内容里提取 currentXxx
            import re
            m = re.search(r"current[A-Za-z]+", str(raw))
            if m and m.group(0) in SYSTEM_VARIABLES:
                target = m.group(0)
        if not target:
            print(f"  ⚠ {name}: 无法推断系统变量，跳过（raw={raw!r}）")
            continue
        dto["defaultValueSystemVariable"] = build_sysvar(target)
        dto["expressionRuntimeData"] = None
        r = post("/service/udc/entity/attribute/update", dto)
        print(f"  {name:<16} -> {build_sysvar(target)[:50]}  {r.get('code')}")

    # 回读
    rd2 = post("/service/udc/attributeSet/select-attribute-list",
               {"attributeSetId": a.set_id})
    print("\n回读：")
    for x in ((rd2.get("data") or {}).get("content") or []):
        raw = x.get("defaultValueSystemVariable")
        if raw:
            errs = validate_sysvar(raw)
            print(f"  {x.get('name'):<16} {'✅' if not errs else '❌'} {raw[:70]}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

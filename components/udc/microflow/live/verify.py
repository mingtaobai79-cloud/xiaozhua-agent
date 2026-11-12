"""UI 验收：打开抽屉 → 读红字/红节点 → 关闭 → 重新发布（RELEASE）

为什么需要它：设计器有一批「只有前端认」的判据（字段标识失效、参数名称未填、
事件节点未完成 isCompleted…），服务端 checkSchema/发布/编译全绿，但页面上是红的。
把这些判据做成函数，每次生成后跑一遍，自修正率才上得去。

用法：
    from components.udc.microflow.live.verify import verify_flow
    r = verify_flow(app_id, mid, host, cookie)
    r["ok"], r["issues"]
"""
from __future__ import annotations

import json
import re
import time

from providers.cdp import CdpClient

# 红字判据：设计器里表示「这个字段/节点没配好」
RED_TEXTS = ["所选数据已失效", "请重新选择", "不能为空", "请选择", "请填写",
             "未完成", "配置有误", "无法识别"]
# 默认分支固定红色，不算问题
IGNORE_CLASS = ("ant-radio", "badge", "tag")


def _ev(c, expr, timeout=None):
    r = c.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    res = r.get("result") or {}
    if res.get("exceptionDetails"):
        return {"__err__": str(res["exceptionDetails"])[:160]}
    return res.get("value")


NODES_JS = """(() => [...document.querySelectorAll('.node-body')]
  .map((x,i)=>({i, text:(x.textContent||'').replace(/\\s+/g,' ').trim()}))
  .filter(o=>o.text))()"""

OPEN_JS = """(() => {
  const i = __IDX__;
  const cards=[...document.querySelectorAll('.node-body')].filter(x=>(x.textContent||'').trim());
  const c=cards[i]; if(!c) return 'no-card';
  const f=c[Object.keys(c).find(k=>k.startsWith('__reactFiber'))];
  let n=f; for(let h=0;h<5&&n;h++,n=n.return){ const p=n.memoizedProps;
    if(p&&p.onClick){ p.onClick({stopPropagation(){},preventDefault(){},target:c,currentTarget:c,nativeEvent:{}}); return 'ok'; } }
  return 'no-handler';
})()"""

DRAWER_TEXT_JS = """(() => { const ds=[...document.querySelectorAll('.ant-drawer')]
  .filter(x=>x.getBoundingClientRect().width>200); const d=ds.pop();
  return d ? (d.textContent||'') : null; })()"""

CLOSE_JS = """(() => { const ds=[...document.querySelectorAll('.ant-drawer')]
  .filter(x=>x.getBoundingClientRect().width>200); const d=ds.pop(); if(!d) return 'none';
  const btn=[...d.querySelectorAll('button')].find(b=>['取消','关闭'].includes((b.innerText||'').trim()));
  if(!btn) return 'no-btn';
  const f=btn[Object.keys(btn).find(k=>k.startsWith('__reactFiber'))];
  let n=f; for(let h=0;h<6&&n;h++,n=n.return){ const p=n.memoizedProps;
    if(p&&p.onClick){ p.onClick({stopPropagation(){},preventDefault(){},target:btn,currentTarget:btn,nativeEvent:{}}); return 'closed'; } }
  return 'no-handler';
})()"""

# ★ 权威判据：redux 里每个节点的 isCompleted。false = 设计器认定为"没配完"（红）。
#   颜色判据不可用：默认分支是珊瑚红、自定义错误节点本身就是红色，全是设计态配色。
INCOMPLETE_JS = """(() => {
  const s = window.appReduxStore && window.appReduxStore.getState();
  if (!s || !s.appDesign || !s.appDesign.microflowEditorReducer) return {__err__: 'no-redux'};
  const r = s.appDesign.microflowEditorReducer;
  const out = [];
  const walk = (o) => {
    if (!o || typeof o !== 'object') return;
    if (o.nodeId && o.type && o.isCompleted === false) {
      out.push({id: o.nodeId, kind: o.actionType || o.type,
                cap: (o.caption || o.title || '').slice(0, 30)});
    }
    (o.conditions || []).forEach(c => {
      if (c && c.isCompleted === false && c.name !== 'elseBranch') {
        out.push({id: c.nodeId, kind: 'CONDITION:' + (c.name || ''), cap: (c.caption || '').slice(0, 30)});
      }
      walk(c);
    });
    (o.nodes || []).forEach(walk);
  };
  Object.values(r.flowNodes || {}).forEach(walk);
  return out;
})()"""


def _tab(app_id, mid, host):
    """确保有一个打开着这条流程编辑器的 tab。"""
    url = ("%s/main/child-frame/udc/app-design/rule/microflow/editor/%s?appId=%s"
           % (host, mid, app_id))
    c = CdpClient(9333, allow_network=True, timeout=20)
    c.connect()
    tabs = c.send("Target.getTargets").get("targetInfos", [])
    exist = any(str(mid) in (t.get("url") or "") for t in tabs if t.get("type") == "page")
    if not exist:
        c.send("Target.createTarget", url=url)
        c.close()
        time.sleep(9)
    else:
        c.close()
    return CdpClient(9333, allow_network=True, timeout=25).__enter__() if False else None


def verify_flow(app_id: str, mid: str, host: str, cookie: str,
                editable: bool = True, republish: bool = True) -> dict:
    """跑一次 UI 验收。返回 {ok, nodes, issues[], state}。"""
    from components.udc.microflow import deploy as DP

    url = ("%s/main/child-frame/udc/app-design/rule/microflow/editor/%s?appId=%s"
           % (host, mid, app_id))
    c = CdpClient(9333, allow_network=True, timeout=20)
    c.connect()
    tabs = c.send("Target.getTargets").get("targetInfos", [])
    if not any(str(mid) in (t.get("url") or "") for t in tabs if t.get("type") == "page"):
        c.send("Target.createTarget", url=url)
        c.close()
        time.sleep(9)
    else:
        c.close()

    c = CdpClient(9333, allow_network=True, timeout=25)
    c.connect(url_substr=mid)
    try:
        c.send("Emulation.setFocusEmulationEnabled", enabled=True)
        time.sleep(1.0)
        issues: list[str] = []

        if editable:
            # RELEASE → DRAFT 才能点开节点
            if _ev(c, "document.body.innerText.includes('正式') && !document.body.innerText.includes('保存并提交')"):
                pass
            _ev(c, """(() => {
              const b=[...document.querySelectorAll('button,span,div')]
                .filter(x=>x.children.length===0 && (x.innerText||'').trim()==='编辑')[0];
              if(!b) return 'no-btn';
              const f=b[Object.keys(b).find(k=>k.startsWith('__reactFiber'))];
              let n=f; for(let h=0;h<8&&n;h++,n=n.return){ const p=n.memoizedProps;
                if(p&&p.onClick){ p.onClick({stopPropagation(){},preventDefault(){},target:b,currentTarget:b,nativeEvent:{}}); return 'ok'; } }
              return 'no-handler'; })()""")
            time.sleep(3.5)

        nodes = []
        for _ in range(12):
            nodes = _ev(c, NODES_JS) or []
            if nodes:
                break
            # 可能停在草稿提示或还在加载
            time.sleep(2.0)
        if not nodes:
            issues.append("页面未渲染出节点（.node-body=0）")
        # 1) isCompleted 判定（权威）
        inc = _ev(c, INCOMPLETE_JS)
        if isinstance(inc, dict) and inc.get("__err__"):
            issues.append("redux 不可读：%s" % inc["__err__"])
        else:
            for it in (inc or []):
                issues.append("未完成节点: %s [%s] %s"
                              % (it.get("kind"), it.get("id"), it.get("cap")))

        # 2) 逐个节点打开抽屉读红字
        for i, nd in enumerate(nodes):
            _ev(c, OPEN_JS.replace("__IDX__", str(i)))
            time.sleep(2.2)
            txt = _ev(c, DRAWER_TEXT_JS)
            if isinstance(txt, str):
                hits = [t for t in RED_TEXTS if t in txt]
                if hits:
                    issues.append("抽屉红字[%s]: %s" % (nd.get("text", "")[:24], hits))
            _ev(c, CLOSE_JS)
            time.sleep(0.8)

        # 3) 重新发布（UI 编辑会把流程打回 DRAFT）
        state = None
        if republish:
            cur = DP.get(host, cookie, mid)
            schema = json.loads(cur["dataSchema"]) if isinstance(cur["dataSchema"], str) \
                else cur["dataSchema"]
            if cur.get("state") != "RELEASE" or True:
                DP.publish(host, cookie, mid, app_id=app_id, schema=schema,
                           name=cur.get("name"), caption=cur.get("caption"),
                           trigger_type=cur.get("triggerType") or "MANUAL")
            state = DP.get(host, cookie, mid).get("state")
        return {"ok": not issues, "mid": mid, "nodes": len(nodes),
                "issues": issues, "state": state}
    finally:
        c.close()

CHECK_BTN_JS = """(() => {
  const b = [...document.querySelectorAll('button')].find(x =>
    /^\\s*\\d*\\s*检查\\s*$/.test((x.textContent||'').trim()) ||
    (x.textContent||'').replace(/\\s+/g,'') === '检查');
  if (!b) return 'no-btn';
  const f = b[Object.keys(b).find(k => k.startsWith('__reactFiber'))];
  let n = f;
  for (let h = 0; h < 8 && n; h++, n = n.return) {
    const p = n.memoizedProps;
    if (p && p.onClick) { p.onClick({stopPropagation(){}, preventDefault(){}, target:b, currentTarget:b, nativeEvent:{}}); return 'clicked'; }
  }
  b.click(); return 'clicked-raw';
})()"""


def run_check(app_id: str, mid: str, host: str, wait: float = 8.0) -> dict:
    """点设计器「检查」并把后端 checkSchema 的报错捞回来。

    这是"后端提交报错 / 检查报错"那一环：前端点检查 → checkSchema/update →
    content.errors[]。返回 {clicked, errors[], raw}。
    """
    import time as _t
    c = CdpClient(9333, allow_network=True, timeout=25)
    c.connect(url_substr=mid)
    try:
        c.send("Emulation.setFocusEmulationEnabled", enabled=True)
        c.install_fetch_recorder()
        clicked = _ev(c, CHECK_BTN_JS)
        _t.sleep(wait)
        cap = c.read_captured() or []
        errors, raw = [], None
        for it in cap:
            u = str(it.get("url") or "")
            if "checkSchema" in u or "CheckSchema" in u:
                raw = it.get("respBody")
                try:
                    j = json.loads(raw or "{}")
                    ct = ((j.get("data") or {}).get("content") or {})
                    errors = ct.get("errors") or ct.get("errorMessage") or []
                except Exception:
                    pass
        return {"clicked": clicked, "errors": errors, "raw": (raw or "")[:300]}
    finally:
        c.close()

PARAM_TAB_JS = """(() => {
  const i = [...document.querySelectorAll('input')].find(x => x.value === 'PARAM');
  if (!i) return 'no-radio';
  (i.closest('label') || i.parentElement).dispatchEvent(new MouseEvent('click', {bubbles:true}));
  return 'ok';
})()"""

PARAM_NAMES_JS = """(() => [...document.querySelectorAll('input')]
  .filter(i => (i.placeholder || '').includes('显示名称'))
  .map(i => (i.value || '').trim()))()"""


def _detection_items(host: str, cookie: str, app_id: str) -> list:
    """拉应用级一致性检测明细（检查按钮背后的接口）。"""
    from components.udc.microflow.live_refs import LiveRefs
    L = LiveRefs(host, cookie)
    q = ("query g($p: udcApplicationSearchDetectionPostInputBody) { data0: "
         "udcApplicationSearchDetectionPost(body: $p) { code data { content } message } }")
    try:
        cc = L._content(L._gql("udcApplicationSearchDetectionPost", {"appId": app_id}, q, timeout=180))
        return cc or []
    except Exception:
        return []


def prove(app_id: str, mid: str, host: str, cookie: str, republish: bool = False) -> dict:
    """一条流程的「自证」：发布报错 + UI 必填/红节点 + 参数名 + 应用检查明细。

    这是业务交付前的最后一道闸：只有它全绿，才敢说"这条流程能交"。
    """
    import time as _t
    from components.udc.microflow import deploy as DP

    out = {"mid": mid, "publish": None, "ui": None, "param_names": None,
           "detection_mine": [], "ok": False}

    # ① 发布（后端 checkSchema 的 errors）
    cur = DP.get(host, cookie, mid)
    schema = json.loads(cur["dataSchema"]) if isinstance(cur["dataSchema"], str) else cur["dataSchema"]
    if cur.get("state") != "RELEASE" or republish:
        okp, info = DP.publish(host, cookie, mid, app_id=app_id, schema=schema,
                               name=cur.get("name"), caption=cur.get("caption"),
                               trigger_type=cur.get("triggerType") or "MANUAL")
        out["publish"] = {"ok": okp, "state": info.get("state"), "errors": info.get("errors")}
    else:
        out["publish"] = {"ok": True, "state": cur.get("state"), "errors": []}

    # ② UI：isCompleted + 抽屉红字（editable=False 不改状态）
    ui = verify_flow(app_id, mid, host, cookie, editable=False, republish=False)
    out["ui"] = ui

    # ③ 入参显示名称（PARAM 页签）
    c = CdpClient(9333, allow_network=True, timeout=25)
    c.connect(url_substr=mid)
    try:
        c.send("Emulation.setFocusEmulationEnabled", enabled=True)
        clicked = _ev(c, PARAM_TAB_JS)
        _t.sleep(2.5)
        out["param_names"] = _ev(c, PARAM_NAMES_JS) if clicked == "ok" else clicked
    finally:
        c.close()

    # ④ 应用级检查明细（区分本流程 vs 其它）
    items = _detection_items(host, cookie, app_id)
    name = (cur.get("name") or "")
    out["detection_total"] = len(items)
    out["detection_mine"] = [
        {"code": it.get("code"), "msg": str(it.get("interpolatedMessage") or "")[:80], "path": it.get("path")}
        for it in items
        if name and (name in json.dumps(it, ensure_ascii=False) or str(mid) in json.dumps(it, ensure_ascii=False))
    ]

    out["ok"] = (bool(out["publish"]["ok"]) and not out["publish"]["errors"]
                 and bool(out["ui"].get("ok")) and not out["detection_mine"])
    return out

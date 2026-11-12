"""L2 页面整体状态采集：一次读全量 flowNodes，本地对照契约，不逐节点开抽屉。

用法：
    from components.udc.microflow.live.l2_state import read_state, check_state
    st = read_state(app_id, mid, host)         # {"nodes": {...}, "raw_count": n}
    issues = check_state(st["nodes"])          # [{"nodeId","caption","field","kind","detail"}]

设计要点：
  * 只读 redux（microflowEditorReducer.flowNodes），不做任何点击；
  * 契约来源 node-contract-from-samples.json（与构造器同一份事实）；
  * 只报「机器可判定」的问题：缺 MUST 键、isCompleted=false、selectParam 为空、
    引用的 outputName 不在本流程节点表里；
  * 抽屉（L3）仍然保留，用于契约判不出来的前端指纹类问题。
"""
from __future__ import annotations
import json
import os
import time
from typing import Any

def _repo_root() -> str:
    p = os.path.dirname(os.path.abspath(__file__))
    while p and not os.path.isdir(os.path.join(p, "core", "facts")):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return p


ROOT = _repo_root()
CONTRACT = os.path.join(ROOT, "core/facts/udc/microflow/node-contract-from-samples.json")

_READ_JS = """
(() => {
  const s = window.appReduxStore && appReduxStore.getState();
  const ed = s && s.appDesign && s.appDesign.microflowEditorReducer;
  if (!ed || !ed.flowNodes) return null;
  const out = {};
  for (const [k, v] of Object.entries(ed.flowNodes)) out[k] = v;
  return JSON.stringify({nodes: out, keys: Object.keys(ed)});
})()
"""


def _contract() -> dict:
    return json.load(open(CONTRACT, encoding="utf-8"))["contract"]


def read_state(app_id: str, mid: str, host: str, *, port: int | None = None,
               wait: float = 10.0, reuse_tab: bool = True) -> dict[str, Any]:
    """打开（或复用）编辑器标签，读一次全量 flowNodes。"""
    import sys
    sys.path.insert(0, ROOT)
    from providers.cdp import CdpClient

    if port is None:
        # 默认 CDP 端口可被环境变量覆盖（历史默认 9333，用户浏览器常在 9222）
        port = int(os.environ.get("UDC_CDP_PORT", "9333"))

    # ★★ 编辑器真实入口（2026-11-01 实测）：
    #   /main/child-frame/udc/app-design/rule/microflow/editor/<mid>?appId=<app>
    # 旧写法 .../rule?appId=<app>&id=<mid> 现在落到**列表页**，
    # redux 里只有 microFlowList / microFlowMenuData，flowNodes 永远为空，
    # read_state 返回 {"nodes": {}} 而不报错 —— 会让 UI 复测静默变成假通过。
    url_part = str(mid)
    designer_url = (host.rstrip("/") + "/main/child-frame/udc/app-design/rule/microflow/editor/"
                    + str(mid) + "?appId=" + app_id)
    c = CdpClient(port, allow_network=True, timeout=30)
    page = None
    try:
        page = c.find_page(url_part)
    except Exception:
        page = None
    if page and reuse_tab:
        c.connect(url_part)
    else:
        c.connect()
        c.send("Target.createTarget", url=designer_url)
        c.close()
        time.sleep(wait)
        c = CdpClient(port, allow_network=True, timeout=30)
        c.connect(url_part)

    raw = None
    deadline = time.time() + wait
    while time.time() < deadline:
        raw = c.evaluate(_READ_JS)
        if raw:
            break
        time.sleep(1.0)
    c.close()
    if not raw:
        raise RuntimeError("读不到 flowNodes（编辑器未就绪或 redux 结构变了）")
    data = json.loads(raw)
    return {"nodes": data["nodes"], "state_keys": data.get("keys") or []}


def _flatten(nodes: dict) -> list[dict]:
    out: list[dict] = []
    for n in (nodes or {}).values():
        out.append(n)
        for sub in (n.get("nodes") or []):
            out.append(sub)
        for cd in (n.get("conditions") or []):
            for sub in (cd.get("nodes") or []):
                out.append(sub)
    return out


def _output_names(nodes: dict) -> set[str]:
    names: set[str] = set()
    for n in _flatten(nodes):
        o = n.get("output") or {}
        for k in ("name", "outputName"):
            if o.get(k):
                names.add(str(o[k]))
        if n.get("outputName"):
            names.add(str(n["outputName"]))
        sp = n.get("selectParam")
        if isinstance(sp, dict) and sp.get("outputName"):
            names.add(str(sp["outputName"]))
    return names


# redux 形态与落库形态不同：BRANCH 的分支在 redux 里是独立的 CONDITION_* 节点，
# BRANCH 自身没有 conditions 键；触发/结束节点不属于 actionType 契约。
STRUCTURAL = {"MANUAL", "SCHEDULE", "BUSINESS_EVENT", "END_NODE", "BRANCH", "CONDITION"}


def check_state(nodes: dict) -> list[dict[str, Any]]:
    """对照契约做本地校验，返回问题清单（结构节点按 redux 规则单独判）。"""
    contract = _contract()
    issues: list[dict[str, Any]] = []
    outs = _output_names(nodes)

    for n in _flatten(nodes):
        at = n.get("actionType") or n.get("type")
        nid = n.get("nodeId") or "?"
        cap = n.get("caption") or ""
        if at in STRUCTURAL:
            if at == "CONDITION" and n.get("name") != "elseBranch" and not n.get("expression"):
                issues.append({"nodeId": nid, "caption": cap, "field": "expression",
                               "kind": "MISSING_EXPRESSION", "detail": at})
            continue
        if at not in contract:
            issues.append({"nodeId": nid, "caption": cap, "field": "-", "kind": "UNKNOWN_TYPE", "detail": at})
            continue
        spec = contract[at]
        for k, meta in spec["keys"].items():
            if meta["level"] == "MUST" and k not in n and not k.startswith("nodes"):
                issues.append({"nodeId": nid, "caption": cap, "field": k, "kind": "MISSING_MUST", "detail": at})
        if n.get("isCompleted") is False:
            issues.append({"nodeId": nid, "caption": cap, "field": "isCompleted", "kind": "INCOMPLETE", "detail": at})
        sp = n.get("selectParam")
        if isinstance(sp, dict) and not sp.get("outputName") and at in (
                "CHANGE_VARIABLE", "CHANGE_ENTITY", "CHANGE_LIST", "CREATE_VARIABLE"):
            issues.append({"nodeId": nid, "caption": cap, "field": "selectParam", "kind": "EMPTY_SELECT", "detail": at})
        # attrType 引用四键（同 G25/G27）：实体字段映射缺键 → 页面红字「所选数据已失效」
        if (at == "CREATE_VARIABLE" and n.get("paramType") == "ENTITY_OBJECT") or \
           (at == "CHANGE_VARIABLE" and n.get("mappingType") == "attrs"):
            for a in (n.get("attrs") or []):
                miss = [k for k in ("refId", "relationEntity", "relationEntityId", "filterRelationEntity")
                        if k not in (a.get("attrType") or {})]
                if miss:
                    issues.append({"nodeId": nid, "caption": cap, "field": "attrType",
                                   "kind": "ATTR_MISSING_REF", "detail": ",".join(miss)})
                    break

    # 引用完整性：任何 selectParam.outputName / value.selectParam.outputName 必须在本流程出参表里
    def scan_refs(obj: Any, owner: dict) -> None:
        if isinstance(obj, dict):
            if obj.get("outputName") and obj.get("type") in ("SelectParam", None) and "key" in obj:
                on = str(obj["outputName"])
                if on and on not in outs:
                    issues.append({"nodeId": owner.get("nodeId"), "caption": owner.get("caption") or "",
                                   "field": "outputName", "kind": "DANGLING_REF", "detail": on})
            for v in obj.values():
                scan_refs(v, owner)
        elif isinstance(obj, list):
            for v in obj:
                scan_refs(v, owner)

    for n in _flatten(nodes):
        for k in ("value", "selectParam", "attrs", "condition", "expression"):
            if k in n:
                scan_refs(n[k], n)
    return issues


def summarize(issues: list[dict]) -> str:
    if not issues:
        return "L2 通过：0 问题"
    kinds: dict[str, int] = {}
    for i in issues:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    return "L2 问题 %d 项：%s" % (len(issues), ", ".join("%s×%d" % kv for kv in kinds.items()))

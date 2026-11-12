"""P2-4 保存链编排器：按固定顺序生成 → 保存 → 回读 → 表达式校验 → L2 → L3。

## 顺序（不可颠倒，每一步的产出是下一步的输入）

    ① 定义入参/出参        build_schema（trigger.paramType / endNode）
    ② 参数页签单独保存      ★ UI 路径必须；API 路径 dataSchema 一次带全
    ③ 保存微流程画布        create → checkSchema/update
    ④ 回读前序节点及依赖    DP.get → dataSchema（★ 只认回读，不认本地对象）
    ⑤ 表达式接口校验        /expression/check + /transform + roundtrip
    ⑥ 页面 L2 检查          read_state + check_state（需 UI 打开编辑器）
    ⑦ 异常时 L3 抽屉定向    只对 ⑥ 报出来的节点开抽屉

## 为什么「只认回读」

平台保存时会做服务端归一（dataType casing、默认值补齐、数组形态约定）。
本地对象 delta ≠ 库里对象。任何「我发出去的就是对的」判断都是假绿：
必须 get 回来，再对**回来的**做表达式校验和 L2 比对。

## 为什么参数页要单独保存（UI 路径）

实测记录：只保存画布不保存参数页时，参数页签的出入参改动不落库，
后续节点引用的入参 context 还是旧的 → 表达式 check 过、运行期取不到值。
API 路径把 trigger/endNode 一起放进 dataSchema 提交，等价于「两处都存」，
但**验收仍然要回读确认** trigger.paramType 与 endNode 是新的。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from .expression_audit import iter_expressions, parse_expression
from .expression_api import build_save_dto

# 校验状态（与既有五级验证状态一致）
CONSTRUCTED = "CONSTRUCTED"
SCHEMA_VERIFIED = "SCHEMA_VERIFIED"
UI_VERIFIED = "UI_VERIFIED"
BUILD_VERIFIED = "BUILD_VERIFIED"


@dataclass
class StageResult:
    name: str
    ok: bool
    detail: Any = None
    problems: list = dc_field(default_factory=list)

    def as_dict(self) -> dict:
        return {"stage": self.name, "ok": self.ok,
                "detail": self.detail, "problems": self.problems}


# ---------------------------------------------------------------- ⑤ 表达式校验
def _has_variable_token(tokens) -> bool:
    """表达式是否含 VARIABLE token（递归 subOps）。"""
    def walk(ts):
        for t in ts or []:
            if not isinstance(t, dict):
                continue
            if t.get("type") == "VARIABLE":
                return True
            if walk(t.get("subOps") or []):
                return True
        return False
    for grp in (tokens if isinstance(tokens, list) else []):
        if isinstance(grp, list):
            if walk(grp):
                return True
        elif walk([grp]):
            return True
    return False


def verify_schema_expressions(backend, schema: dict, *,
                             require_roundtrip: bool = True) -> StageResult:
    """对 dataSchema 里**每个**表达式跑 check + transform。

    require_roundtrip=True 时还比对：库里已有的 executableExpr 是否与本次
    transform 结果一致（不一致 = 表达式在平台眼里已变质，必须人工看）。
    """
    problems: list[str] = []
    checked = 0
    skipped_var = 0
    for node in _walk_all_nodes(schema.get("nodes")):
        for path, expr in _iter_own_expressions(node):
            info = parse_expression(expr)
            if not info["tokens"]:
                continue                      # 空表达式（未填）交给契约闸门
            # ★ 含 VARIABLE 的表达式**不能**走 /expression/check 校验：
            #   实测连平台自己保存的真实表达式原样重发也报 FORMULA_6058
            #   （context 的显示路径由设计器运行期按完整流程树生成，离线拼不出）。
            #   这类表达式的真校验是 checkSchema（见 facts §十三），这里跳过。
            if _has_variable_token(info["tokens"]):
                skipped_var += 1
                continue
            dto = build_save_dto(expr)
            chk = backend.check(dto)
            checked += 1
            cap = node.get("caption") or node.get("nodeId") or "?"
            if not chk.get("ok"):
                problems.append("[%s] %s check 失败 code=%s msg=%s"
                                % (cap, path, chk.get("code"), chk.get("message")))
                continue
            tr = backend.transform(dto)
            if not tr.get("ok"):
                problems.append("[%s] %s transform 失败 code=%s msg=%s"
                                % (cap, path, tr.get("code"), tr.get("message")))
                continue
            if require_roundtrip:
                old = info.get("executableExpr") or ""
                new = tr.get("executableExpr") or ""
                # ★ 占位串（含字段引用的表达式未进 UI 定稿）不算"变质"：
                #   它本来就要等设计器重算，这里只报告、不改判。
                placeholder = "__NEEDS_UI_FINALIZE__"
                if old and new and old != new and old != placeholder:
                    problems.append("[%s] %s executableExpr 不一致（库中已变质）"
                                    % (cap, path))
    return StageResult("expression_verify", not problems,
                       {"checked": checked, "skipped_variable": skipped_var,
                        "note": "含 VARIABLE 的表达式由 checkSchema 校验（facts §十三）"},
                       problems)


# ---------------------------------------------------------------- ④ 回读比对
def readback_compare(stored: dict, expected: dict) -> StageResult:
    """回读 dataSchema 与提交对象的差异（只看机器可判定字段）。

    平台会做归一（casing/默认值），所以这里只报**语义级**差异：
    节点数、nodeId 集合、每个节点的 actionType、output.name、表达式 token 数。
    """
    problems: list[str] = []
    s_nodes = _node_sig(stored)
    e_nodes = _node_sig(expected)
    if set(s_nodes) != set(e_nodes):
        miss = set(e_nodes) - set(s_nodes)
        extra = set(s_nodes) - set(e_nodes)
        if miss:
            problems.append("回读缺节点: %s" % sorted(miss)[:6])
        if extra:
            problems.append("回读多节点: %s" % sorted(extra)[:6])
    for nid in sorted(set(s_nodes) & set(e_nodes)):
        if s_nodes[nid] != e_nodes[nid]:
            problems.append("节点 %s 形态差异: 回读=%s 提交=%s"
                            % (nid, s_nodes[nid], e_nodes[nid]))
    return StageResult("readback", not problems, {"nodes": len(s_nodes)}, problems)


def _iter_own_expressions(node: dict):
    """只产出节点**自身**的表达式（不进子节点）。

    iter_expressions 会递归 nodes / conditions[].nodes，
    若外层已经 _walk_all_nodes，会重复计数并把问题归到错误的宿主上。
    """
    own = {k: v for k, v in node.items() if k != "nodes"}
    if own.get("conditions"):
        own["conditions"] = [{k: v for k, v in c.items() if k != "nodes"}
                             for c in own["conditions"] if isinstance(c, dict)]
    yield from iter_expressions(own)


def _node_sig(schema: dict) -> dict:
    out = {}
    for n in _walk_all_nodes(schema.get("nodes")):
        nid = n.get("nodeId")
        if not nid:
            continue
        o = n.get("output") or {}
        out[nid] = (n.get("actionType") or n.get("type"), o.get("name"),
                    o.get("dataType"), len(list(_iter_own_expressions(n))))
    return out


def _walk_all_nodes(nodes) -> list[dict]:
    out: list[dict] = []

    def walk(seq):
        for n in seq or []:
            if not isinstance(n, dict):
                continue
            out.append(n)
            for c in n.get("conditions") or []:
                walk(c.get("nodes"))
            walk(n.get("nodes"))

    walk(nodes)
    return out


# ---------------------------------------------------------------- ⑥ L2 检查
def l2_check(app_id: str, mid: str, host: str, **kw) -> StageResult:
    """页面 L2 全量读取 + 契约对照（需 CDP）。"""
    from .live.l2_state import read_state, check_state
    st = read_state(app_id, mid, host, **kw)
    issues = check_state(st["nodes"])
    return StageResult(
        "l2_check", not issues,
        {"nodes": len(st["nodes"]), "raw_count": st.get("raw_count")},
        ["[%s] %s %s: %s" % (i.get("caption") or i.get("nodeId"), i.get("field"),
                             i.get("kind"), i.get("detail")) for i in issues])


# ---------------------------------------------------------------- 全链
def run_pipeline(*, host: str, cookie: str, app_id: str, app_name: str,
                 schema: dict, name: str, caption: str, group_id: str = "",
                 keep: bool = False, l2: bool = True, backend=None) -> dict:
    """完整保存链。返回 {ok, state, mid, stages:[...], problems:[...]}。

    keep=False 时无论成败都删掉验证流（★ 平台残留 DRAFT 会污染应用）。
    """
    from . import deploy as DP
    from .expression_transport import CurlBackend

    be = backend or CurlBackend(host, cookie)
    stages: list[StageResult] = []

    # ③（②的等价）create + checkSchema/update
    mid = None
    try:
        mid = DP.create(host, cookie, app_id=app_id, app_name=app_name, name=name,
                        caption=caption, schema=schema, group_id=group_id,
                        trigger_type=_trigger_type(schema))
        # ★ 发布体只能走 deploy.publish（唯一实现）：
        #   自拼 body 少一个键就是 BOOT_1001 Parameter Error，且不给明细。
        #   这里捕获 PublishError 转成阶段失败，保留 check=false 的明细。
        try:
            ok, info = DP.publish(host, cookie, mid, app_id=app_id, schema=schema,
                                  name=name, caption=caption, group_id=group_id,
                                  trigger_type=_trigger_type(schema))
            errs = (info or {}).get("errors") or []
            stages.append(StageResult(
                "save", bool(ok), {"code": "BOOT_0000", "check": bool(ok), "mid": mid},
                ["%s %s" % (e.get("nodeCaption"), e.get("errorCode")) for e in errs]))
        except Exception as e:
            msg = str(e)
            stages.append(StageResult("save", False, {"mid": mid}, [msg[:400]]))

        # ④ 回读
        stored = _stored_schema(DP.get(host, cookie, mid))
        stages.append(readback_compare(stored, schema))

        # ⑤ 表达式校验（对回读对象做，不是对提交对象做）
        stages.append(verify_schema_expressions(be, stored))

        # ⑥ L2
        if l2:
            try:
                stages.append(l2_check(app_id, str(mid), host, wait=25.0))
            except Exception as e:
                stages.append(StageResult("l2_check", False, None,
                                          ["L2 不可用: %s" % str(e)[:160]]))
    finally:
        if mid is not None and not keep:
            try:
                DP.delete(host, cookie, str(mid))
            except Exception:
                pass

    problems = [p for s in stages for p in s.problems]
    state = _state_of(stages)
    return {"ok": all(s.ok for s in stages), "state": state,
            "mid": mid, "stages": [s.as_dict() for s in stages],
            "problems": problems}


def _state_of(stages: list[StageResult]) -> str:
    names = {s.name: s.ok for s in stages}
    if not names.get("save"):
        return CONSTRUCTED
    if names.get("readback") and names.get("expression_verify") and names.get("l2_check"):
        return UI_VERIFIED
    if names.get("readback") and names.get("expression_verify"):
        return SCHEMA_VERIFIED
    return CONSTRUCTED


def _trigger_type(schema: dict) -> str:
    """从 schema 的 trigger.type 取真实触发类型（SCHEDULE/EVENT/MQ/MANUAL）。

    ★ 曾写死返回 MANUAL：定时/事件流程的 create/publish 被降成 MANUAL，
      与 schema 里 trigger.type=SCHEDULE 矛盾，第二次 publish 报 BOOT_3000。
    """
    t = (schema.get("trigger") or {}).get("type") or ""
    return t if t else "MANUAL"


def _stored_schema(cur: dict) -> dict:
    import json
    ds = cur.get("dataSchema")
    if isinstance(ds, str):
        return json.loads(ds)
    return ds or {}


def _update_body(cur: dict, schema: dict, app_id: str, app_name: str,
                 name: str, caption: str, group_id: str) -> dict:
    """checkSchema/update 的 body（实测与手动 body 一致，勿换用 deploy.publish）。"""
    import json
    body = {
        "description": "", "publishState": "UNPUBLISH",
        "lastVersionMetadataState": "DISABLED", "restPath": None,
        "appId": app_id, "id": str(cur.get("id")), "name": name, "caption": caption,
        "type": "SERVICE", "triggerType": _trigger_type(schema), "state": "RELEASE",
        "dataSchema": json.dumps(schema, ensure_ascii=False),
        "serviceInterface": None, "sourceType": "PAGE", "creationMethod": "MANUAL",
        "groupType": "DEFAULT", "versionCode": 100, "openApi": "STOP",
        "restApi": "DISABLED", "scheduleCaption": "-", "businessEventCaption": "-",
        "microFlowGroupId": group_id,
    }
    if cur.get("guid"):
        body["guid"] = cur["guid"]
    return body

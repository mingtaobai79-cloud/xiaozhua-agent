"""契约闸门：构造器产物必须满足真实样本的 MUST 字段集。

这不是「再写一个闸门」，而是把 643 条真实流程的字段契约变成可执行断言，
让构造器无法再漏字段、也无法再凭空加真实样本里没有的字段。
"""
from __future__ import annotations

import json
import os
from typing import Any

_CONTRACT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))),
    "core", "facts", "udc", "microflow", "node-contract-from-samples.json")

_cache: dict[str, Any] | None = None


def load_contract() -> dict[str, Any]:
    global _cache
    if _cache is None:
        with open(_CONTRACT_PATH, encoding="utf-8") as fh:
            _cache = json.load(fh)["contract"]
    return _cache


# actionType 恒为 null 的节点（真机 941/384/1981/32/25 个样本全部无)
TYPE_ONLY_NODES = {"BRANCH", "CONDITION", "FOR", "FOR_EACH", "CUSTOM_ERROR"}


# 服务端 checkSchema 明确要求的字段，但 643 条样本里恰好没出现（样本过少）
# CALL_DATA_FLOW：只有 1 个样本，缺 outputName 报 PROPERTY_IS_REQUIRED
ALLOWED_EXTRA: dict[str, set[str]] = {"CALL_DATA_FLOW": {"outputName", "outPutDesc"}}


def normalize_node(node: dict) -> dict:
    """剥掉「真实保存态从未出现」的字段，让构造器产物与生产数据同形。

    ★ 为什么必须剥：前端 `addNode` 模板与**保存后的落库形态**不是一回事。
      模板里有 6 个字段真实 643 条流程从未出现（CUSTOM_ERROR/FOR_EACH 的
      actionType、CREATE_MAP 的 paramType/dataType、SUB_MICROFLOW 的 pageInfo、
      CALL_DATA_FLOW 的 selectParam），它们是前端新建节点的临时占位，
      保存链路会丢掉。生成器若不剥，schema 与生产数据不同形，
      后续拿生产样本反推契约时会被这些噪声带偏。
    """
    contract = load_contract()
    at = node.get("actionType") or node.get("type")
    if at not in contract:
        return node
    real = contract[at]["keys"]
    keep = ALLOWED_EXTRA.get(at, set())   # 服务端硬要求但样本里没有的字段
    for k in [k for k in node if k not in real and k not in keep]:
        del node[k]
    return node


def check_node(node: dict, *, allow_opt: bool = True) -> list[str]:
    """校验单个节点是否满足真实样本契约。

    返回问题清单（空 = 通过）。判据全部来自
    core/facts/udc/microflow/node-contract-from-samples.json。
    """
    contract = load_contract()
    at = node.get("actionType") or node.get("type")
    if at not in contract:
        return ["%s: 真实样本中不存在该 actionType（26 类之外）" % at]

    spec = contract[at]
    keys = spec["keys"]
    got = set(node.keys())
    problems: list[str] = []

    # 1. MUST 字段必须全有
    must = [k for k, v in keys.items() if v["level"] == "MUST"]
    for k in must:
        if k not in got:
            problems.append("%s: 缺 MUST 字段 %r（真实 %d 个样本 100%% 都有）"
                            % (at, k, spec["samples"]))

    # 2. 真实样本里从未出现过的字段 → 污染
    #    ★ 例外：CALL_DATA_FLOW 只有 1 个样本，服务端 checkSchema 明确要求
    #      outputName（PROPERTY_IS_REQUIRED），outPutDesc 与它同源，放行。
    allow_extra = ALLOWED_EXTRA.get(at, set())
    unknown = sorted(k for k in got if k not in keys and k not in allow_extra)
    if unknown:
        problems.append("%s: 有真实样本从未出现的字段 %s → 前端可能不认"
                        % (at, unknown))

    # 3. actionType 恒 null 的控制节点不能带 actionType
    if at in TYPE_ONLY_NODES and "actionType" in node:
        problems.append("%s: 真实样本 actionType 恒为 null，不该写"
                        % at)

    # 3b. ★ 常量字面量语境：值槽位只能 Simple / SelectParam / Expression / CtpEnum / Enum，
    #     全平台 643 条流程里 value 槽位出现 CONSTANT **0 次**。
    #     把查询条件的 CONSTANT 用到值槽位 → checkSchema 报 value.type DATA_INVALID。
    def _scan_val(o, path):
        if isinstance(o, dict):
            t = o.get("type")
            if t == "CONSTANT":
                problems.append(
                    "%s: %s 用了 CONSTANT —— 值槽位不支持该类型（真实 0 次），"
                    "应用 Simple" % (at, path))
            for k, v in o.items():
                _scan_val(v, path + "." + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                _scan_val(v, "%s[%d]" % (path, i))

    for slot in ("value", "attrs", "entries", "mappingRule"):
        if slot in node:
            _scan_val(node[slot], slot)

    # 3c. LIST_OPERATION / CHANGE_LIST 引**实体**列表时 selectParam 必须有 dtoType。
    #     ★ 判据按真实分布定：803 个有 dtoType 的样本全是实体/自定义 DTO
    #       （SUB_ENTITY 527 / MASTER_ENTITY 200 / CUSTOM 76）；
    #       168 个缺的全是**基础类型列表**（BIGINTEGER 92 / STRING 70 / DECIMAL 6，
    #       udcApp=None）。所以基础类型列表缺 dtoType 是合法的，
    #       一刀切要求「必须有」会在真实语料上误报 168 次。
    if at in ("LIST_OPERATION", "CHANGE_LIST") and isinstance(node.get("selectParam"), dict):
        sp = node["selectParam"]
        is_entity_list = (sp.get("dataType") == "DTO" or sp.get("udcApp") is True
                          or bool(sp.get("relationEntity")))
        if is_entity_list and not sp.get("dtoType"):
            problems.append("%s: 引实体列表但 selectParam 缺 dtoType"
                            "（实体列表 803/803 都有；基础类型列表可无）" % at)

    # 4. 形态校验：真实 100% 是 null 的字段不该给值
    for k, v in keys.items():
        if k not in node:
            continue
        sh = v["shapes"]
        if sh.get("null", 0) == spec["samples"] and node[k] is not None:
            problems.append("%s: 字段 %r 真实样本 100%% 为 null，给了 %r"
                            % (at, k, type(node[k]).__name__))
        # 真实 100% 是 dict 的字段不能给 None
        elif sh.get("dict", 0) == spec["samples"] and not isinstance(node[k], dict):
            problems.append("%s: 字段 %r 真实样本 100%% 是对象，给了 %s"
                            % (at, k, type(node[k]).__name__))
    return problems


def check_schema(schema: dict) -> list[str]:
    """校验整条 schema 里所有节点（含分支条件）的契约。"""
    problems: list[str] = []

    def walk(ns):
        for n in ns or []:
            if not isinstance(n, dict):
                continue
            nid = n.get("nodeId") or "?"
            for p in check_node(n):
                problems.append("%s: %s" % (nid, p))
            for c in n.get("conditions") or []:
                if isinstance(c, dict):
                    for p in check_node(c):
                        problems.append("%s: %s" % (c.get("nodeId", "?"), p))
                    walk(c.get("nodes"))
            walk(n.get("nodes"))

    walk(schema.get("nodes"))
    return problems

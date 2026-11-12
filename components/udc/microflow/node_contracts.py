"""节点契约模型 —— 把「点开抽屉逐项填」固化成可静态校验的规则。

为什么要有它：设计器里每个节点的抽屉是分页签的（例如「查询单条数据」分
ID 查询 / 条件查询），不同页签必填项不同，而且有一批字段只有前端认
（服务端 checkSchema 全绿，页面上是空黄框）。这些规则散落在 643 条语料里，
人工记不住，所以固化成数据 + 一个校验器，生成时先照表填，填完先自查。

用法：
    from components.udc.microflow.node_contracts import check_contracts
    problems = check_contracts(schema)      # [] 表示每个节点都符合契约

契约字段语义：
    required  必填（缺了 UI 就是空黄框 / 红字）
    optional  可空（真实语料里大量为空，不影响）
    expr      支持表达式 / 变量引用的位置
    tabs      该节点在设计器里的页签（不同页签必填不同）
    note      踩过的坑
"""

from __future__ import annotations

import re
from typing import Any

# ── 触发节点 ────────────────────────────────────────────────────────────────
TRIGGER_CONTRACTS: dict[str, dict[str, Any]] = {
    "MANUAL": {
        "caption": "手动触发 / 服务定义",
        "tabs": {
            "参数(NONE)": {"required": [], "note": "无入参无出参"},
            "参数(BASIC)": {"required": ["output.name", "output.desc", "desc", "basic"],
                            "note": "「参数名称」绑 trigger.desc，必须 == output.desc（G21）"},
            "参数(ENTITY_OBJECT)": {"required": ["output.name", "output.desc", "desc", "entityObject"]},
        },
        "required": ["type", "paramType"],
        "note": "顶层 input = trigger.output（有参时）",
    },
    "SCHEDULE": {
        "caption": "定时任务",
        "tabs": {"定时": {"required": ["scheduleCronRule.jobCaption",
                                        "scheduleCronRule.cronRules[0].cycleType",
                                        "scheduleCronRule.cronRules[0].startTime"]}},
        "required": ["scheduleCronRule"],
        "note": "input/output 恒 null；endNode 只有 9 键",
    },
    "BUSINESS_EVENT": {
        "caption": "业务事件触发",
        "tabs": {"事件": {"required": ["messageInfo.eventName", "output.name"]}},
        "required": ["messageInfo", "output"],
        "note": "顶层 input = trigger.output；事件实体挂 output.info",
    },
}

# ── 活动节点 / 控制节点 ─────────────────────────────────────────────────────
NODE_CONTRACTS: dict[str, dict[str, Any]] = {
    "RETRIEVE": {
        "caption": "查询单条数据",
        "tabs": {
            "ID查询": {"required": ["selectParam(记录ID)"],
                       "note": "selectParam 必须是引用的记录ID；空 = 空黄框，且部署一致性检测会拒"},
            "条件查询": {"required": ["condition"],
                         "note": "condition[0].type=GROUP，内层 conditions[] 每项 type=CONDITION"},
        },
        "required": ["output.name"],
        "optional": ["size", "sort"],
        "note": "未查到数据时 选「继续执行，自行处理空值判断」",
    },
    "RETRIEVE_ARRAY": {
        "caption": "查询多条数据",
        "tabs": {
            "条件查询": {"required": ["condition"],
                         "note": "无条件下拉空会查全量；筛选条件右值三种形态见 CONTEXT_VARIABLE"},
            "ID集合查询": {"required": ["selectParam(ids)"],
                           "note": "ids 必须是列表；事件对象里没有 ids，别在这里硬塞"},
        },
        "required": ["output.name"],
        "optional": ["size", "pageSearch", "scope", "selectType"],
        "note": "出参 dataType=DTO/type=ARRAY，不带 relationEntity",
    },
    "CREATE_ENTITY": {
        "caption": "创建单条数据",
        "required": ["structure", "attrs"],
        "optional": ["selectParam"],
        "expr": ["attrs[].value"],
        "note": "出参 BIGINTEGER（新记录ID）",
    },
    "CREATE_BATCH_ENTITY": {
        "caption": "创建多条数据",
        "required": ["selectParam(列表)", "output.name"],
        "note": "实体来自 selectParam 列表本身；出参 INTEGER（影响行数），写操作出参必须是标量",
    },
    "CHANGE_ENTITY": {
        "caption": "更新数据",
        "required": ["selectParam(操作对象)", "attrs"],
        "expr": ["attrs[].value"],
        "note": "操作对象必须是活动节点出参，不能直引 FOR_EACH 循环项（G20）",
    },
    "CHANGE_BATCH_ENTITY": {
        "caption": "批量更新",
        # ★ 2026-11-02 更正：原契约 required 里写了 "attrs"，
        #   实测全仓 95 个样本（含真实业务流 r44_e1_orig、真实前端抓包
        #   real-type0-node-structures）**带 attrs 的是 0 个**。
        #   批量节点根本不做字段映射：它把「列表元素自带的字段值」原样落库，
        #   所以没有 attrs 可填。照原契约生成会被 C-CHANGE_BATCH_ENTITY 拦死。
        #   真实出参：dataType=INTEGER / type=OBJECT，desc="批量更新…成功的数量"。
        "required": ["selectParam(列表)", "output.name"],
        "note": "出参 INTEGER（影响行数）；无 attrs，值来自列表元素",
    },
    "DELETE_ENTITY": {
        "caption": "删除数据",
        # ★ 2026-11-02 更正：原契约写 present=["selectParam"]，注释称
        #   「语料 CONDITION 8/8 selectParam=null（键在即可）」——
        #   实测全量 fixtures 里 8 个 DELETE_ENTITY 样本，**含 selectParam 键的是 0 个**，
        #   注释与语料矛盾。照原契约生成会被自己的闸门拦死（C-DELETE_ENTITY 缺 selectParam），
        #   而真实平台样本根本没有这个键。真实形态：条件删除靠 condition，
        #   deleteType 恒为 CONDITION（build() 已默认带上）。
        "present": [],
        "note": "出参 INTEGER；删除范围由 condition 决定，无 selectParam 键",
    },
    "CREATE_VARIABLE": {
        "caption": "创建变量",
        "tabs": {
            "基本类型": {"required": ["dataType", "value"]},
            "实体对象": {"required": ["structure(实体)", "attrs(字段映射)"],
                         "note": "左列下拉必须绑定实体字段，否则「所选数据已失效」"},
            "自定义对象": {"required": ["structure", "attrs"]},
        },
        "required": ["output.name"],
        "note": "实体对象字段映射的 attrType 必须真实 16 键",
    },
    "CHANGE_VARIABLE": {"caption": "修改变量", "required": ["selectParam"],
                        "note": "基本类型用 value，实体对象用 attrs，二者必居其一"},
    "LIST_OPERATION": {
        "caption": "列表操作",
        "required": ["selectParam(列表)", "operationType"],
        "note": "14 种操作无 ADD；SIZE 出参 INTEGER；引实体列表 selectParam 必带 dtoType",
    },
    "CREATE_LIST": {
        "caption": "创建列表",
        "present": ["structure", "value"],   # 语料 BASIC 731 条 structure=null（键在即可）
        "note": "paramType=ENTITY_OBJECT 时 structure 是实体、value 是 []",
    },
    "CHANGE_LIST": {
        "caption": "列表增删",
        # ★ dataSource 不再是全局必填：CLEAR 的真实样本（15 条）没有 dataSource。
        #   按 action 分形态由 G40 把关（ADD/REPLACE 要 dataSource，REMOVE 还要 countAttrs）。
        "required": ["selectParam(列表)", "action"],
        "note": "ADD 266/REPLACE 28 → +dataSource；CLEAR 15 → 只有 selectParam；REMOVE 8 → +dataSource+countAttrs",
    },
    "DATA_MAPPING": {
        "caption": "数据转换",
        "required": ["selectParam(源数据)", "mappingRule", "structure(目标)"],
        "note": "源/目标实体不同，字段按名字映射；mappingRule 空会生成空对象",
    },
    "SUB_MICROFLOW": {
        "caption": "子微流程",
        "required": ["mfService.id"],
        "note": "mfService.path=/microflow/{name}；hasInput=true 时必须填 attrs 映射",
    },
    "CALL_APP_SERVICE": {
        "caption": "调用应用服务",
        "required": ["selectMethod", "output.name"],
        "note": "入参/出参由后端反射返回（SearchMethodByName），DTO 字段走 FindCustomDto",
    },
    "CUSTOM_ERROR": {
        "caption": "自定义错误",
        "required": ["error"],
        "note": "设计态节点本身是红色（不是错误），信息为空才是错",
    },
    # 控制节点
    "BRANCH": {
        "caption": "条件分支",
        "required": ["conditions"],
        "note": "ifBranch.expression 必须非空；elseBranch.isCompleted 恒 None（正常）",
    },
    "FOR_EACH": {
        "caption": "循环（列表）",
        "required": ["selectParam(循环对象)", "output.name"],
        "note": "循环体内改数据要 RETRIEVE(IDS) 中转，别直引循环项",
    },
    "FOR": {
        "caption": "计数循环",
        "required": ["forStart", "forEnd", "forStep", "targetName", "output.name"],
        "optional": ["operator"],
        "note": "operator 默认 '<='；步长 forStep 是数字，不是表达式",
    },
    "BREAK": {"caption": "跳出循环", "required": []},
}


def _nonempty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, (str, list, dict)) and len(v) == 0:
        return False
    return True


def _get(node: dict, path: str) -> Any:
    """支持 "output.name" / "conditions[0].expression" / "selectParam(记录ID)" 三种写法。"""
    path = re.sub(r"\([^)]*\)", "", path)          # 去掉中文括注
    cur: Any = node
    for seg in re.split(r"[.\[\]]", path):
        if not seg:
            continue
        if cur is None:
            return None
        if seg.isdigit():
            cur = cur[int(seg)] if isinstance(cur, list) and len(cur) > int(seg) else None
        elif isinstance(cur, dict):
            cur = cur.get(seg)
        else:
            return None
    return cur


def _walk(nodes, out):
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        out.append(n)
        for c in n.get("conditions") or []:
            if isinstance(c, dict):
                _walk(c.get("nodes"), out)
        _walk(n.get("nodes"), out)
    return out


def _kind(node: dict) -> str:
    at = node.get("actionType")
    if at:
        return at
    t = node.get("type")
    return t if t in ("BRANCH", "FOR_EACH", "FOR", "BREAK") else (t or "")


def _variant(node: dict, kind: str) -> str | None:
    if kind == "RETRIEVE":
        return "ID查询" if _nonempty(node.get("selectParam")) else "条件查询"
    if kind == "RETRIEVE_ARRAY":
        sp = node.get("selectParam") or {}
        if _nonempty(sp) and str((sp.get("nodeInfo") or {}).get("actionType")) in ("FOR_EACH", "RETRIEVE_ARRAY"):
            return None
        return "条件查询"
    if kind == "CREATE_VARIABLE":
        st = node.get("structure") or {}
        if _nonempty(node.get("attrs")):
            return "实体对象"
        return "基本类型"
    return None


def check_contracts(schema: dict) -> list[str]:
    """按契约逐节点自查。返回问题列表（空 = 全部符合）。"""
    problems: list[str] = []

    trg = schema.get("trigger") or {}
    tt = trg.get("type")
    tc = TRIGGER_CONTRACTS.get(tt)
    if tc:
        reqs = list(tc.get("required", []))
        if tt == "MANUAL" and (trg.get("paramType") or "NONE") != "NONE":
            reqs.append("output")
        for req in reqs:
            if not _nonempty(_get(trg, req)):
                problems.append(f"C-触发[{tc['caption']}]: 缺 {req}")
        if tt == "MANUAL" and (trg.get("paramType") or "NONE") != "NONE":
            if not _nonempty(trg.get("desc")):
                problems.append("C-触发[MANUAL]: 缺 trigger.desc（设计器「参数名称」空黄框）")

    for n in _walk(schema.get("nodes"), []):
        kind = _kind(n)
        if not kind or n.get("type") == "CONDITION":
            continue
        cc = NODE_CONTRACTS.get(kind)
        if not cc:
            continue
        name = n.get("caption") or n.get("nodeId")
        for req in cc.get("required", []):
            if req in ("错误信息",):
                ok = any(_nonempty(n.get(k)) for k in ("errorMessage", "message", "content",
                                                       "customMessage", "errorInfo", "desc"))
                if not ok:
                    problems.append(f"C-{kind}[{name}]: 自定义错误信息为空")
                continue
            if not _nonempty(_get(n, req)):
                problems.append(f"C-{kind}[{name}]: 缺 {req}")
        for pre in cc.get("present", []):
            if pre not in n:
                problems.append(f"C-{kind}[{name}]: 缺 {pre} 字段（可为空但不能没有）")
        # 条件分支：ifBranch 表达式必须非空
        if kind == "BRANCH":
            conds = n.get("conditions") or []
            if conds and not _nonempty((conds[0] or {}).get("expression")):
                problems.append(f"C-BRANCH[{name}]: 符合条件分支缺表达式")
        if kind == "CHANGE_VARIABLE":
            if not (_nonempty(n.get("attrs")) or _nonempty(n.get("value"))):
                problems.append(f"C-CHANGE_VARIABLE[{name}]: attrs 与 value 都为空")
        if kind == "SUB_MICROFLOW":
            if (n.get("mfService") or {}).get("hasOutput") and not _nonempty(_get(n, "output.name")):
                problems.append(f"C-SUB_MICROFLOW[{name}]: 有出参却缺 output.name")
        if kind == "LIST_OPERATION":
            sp = n.get("selectParam") or {}
            if (sp.get("dataType") == "DTO") and not _nonempty(sp.get("dtoType")):
                problems.append(f"C-LIST_OPERATION[{name}]: 引实体列表缺 dtoType")
    return problems

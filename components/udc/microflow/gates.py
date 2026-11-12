"""微流程生成闸门：把平台侧报过的错，在生成期拦下来。

设计原则
--------
生成器只做"拼装"是不够的——平台 `checkSchema` 是浅校验，真正的错在
`CheckUtils.parseNodes → ActivityNode.nodeLogicCheck` 才暴露（04004/04000）。
所以每个踩过的错都要在**生成后、提交前**变成一条可判定规则；规则不过就不许生成，
而不是生成完再拿脚本去改。

规则 ↔ 错误对照（全部来自活体报错）
----------------------------------
G1 EXPR_SEGMENT_MISMATCH  → UDC_CE_MICRO_FLOW_04000 ArrayList.rangeCheck
    MicroFlowComponentUtils.checkExpressionNode 按 translation 段数取 tokens。
    tokens 数 ≠ translation 段数即越界。段 = 操作数 / 运算符 / 函数调用括号。
G2 DANGLING_REF           → UDC_MICRO_FLOW_04004 "前序节点发生变更请重新选择"
    SelectParam.outputName 必须等于本流程某个节点的 output.name 或 _FLOW_INPUT_*。
G3 TYPE_MISMATCH          → "不是根实体对象(x)" / "不是文本类型(x)" / "对象类型不匹配(x)"
    CREATE_ENTITY/CREATE_BATCH_ENTITY 只收实体对象(DTO)或实体列表；
    CHANGE_LIST 只收文本列表；CHANGE_VARIABLE(entity) 只收实体对象。
G4 MAPPING_RULE_NO_NAME   → 提交门禁 "DATA_MAPPING.mappingRule 缺 'name'"
G5 CROSS_APP_NOT_DEPENDED → "依赖应用已删除"
    跨应用节点的 app.appName 必须在 inApp 或依赖应用清单里。
G6 SERVICE_ATTR_STALE     → "必填参数未配置" / "前序节点发生变更"
    自定义服务的 attrs 必须来自该 selectMethod 的 parameter 契约，不能整节点搬用。

用法
----
    from components.udc.microflow.gates import run_gates
    problems = run_gates(schema, app_name=..., dep_apps={...})
    if problems: raise SystemExit("\n".join(problems))
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterable

# 中缀运算符表（按 643 条生产流程的 expressionTranslation 实测补全）。
# ★ 中文中缀：`包含` / `不包含` 是二元运算符（a 包含 b → 3 个 token），
#   不是函数。只写 `含` 会漏掉 `包含`，导致 `a 包含 b` 被判 1 段而实际 3 段。
#   注意顺序：长符在前，否则 `包含` 会被 `含` 先匹配成单字，`>=` 会被 `>` 抢先。
_OPERATORS = ("不包含", "包含", "不等于", "等于", "大于等于", "小于等于", "大于", "小于",
              "&&", "||", "==", "!=", ">=", "<=", ">", "<", "=",
              "+", "-", "*", "/", "含", "且", "或")


def _iter_tokens_recursive(tokens: Iterable[dict]) -> Iterable[dict]:
    """递归遍历 token 树（含 FUNCTION.subOps）。subOps 是 [[子token序列]]。"""
    for t in tokens or []:
        if not isinstance(t, dict):
            continue
        yield t
        sub = t.get("subOps")
        if isinstance(sub, list):
            for grp in sub:
                if isinstance(grp, list):
                    yield from _iter_tokens_recursive(grp)


def _segments(translation: str) -> int:
    """顶层段数 = 2 * 顶层运算符数 + 1（按 643 条生产流程 1216 个表达式校准）。

    ★ 关键：**括号内的运算符不计入顶层段数**。
      函数调用的括号内容要整体剥掉，再数剩下的顶层运算符。

    实测对照（真实生产样本）：
      `不为空(a)&& 不为空(b)&& 不为空(c)`        → tokens 5  (3 FUNC + 2 OP)
      `不为空(a)`                                → tokens 1
      `a != b`                                   → tokens 3
      `a == 文本转日期(日期转文本(b,yyyy-MM-dd),y)` → tokens 3 (括号内运算符不计)
      `a 包含 b || 为空(a)`                       → tokens 3

    旧实现「只要有括号就返回 1」会把 `f(a)&&f(b)` 判成 1 段而实际是 5 段，
    在 643 条生产流程上误报 442 次。已按真实样本重写。
    """
    s = (translation or "").strip()
    if not s:
        return 0
    # 1) 剥掉所有括号及其内容（含中文括号），保留顶层结构
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\([^()]*\)", "", s)
        s = re.sub(r"（[^（）]*）", "", s)
    # 2) 顶层运算符计数
    ops = 0
    i = 0
    while i < len(s):
        hit = False
        for op in _OPERATORS:
            if s.startswith(op, i):
                ops += 1
                i += len(op) - 1
                hit = True
                break
        i += 1
    # 3) 顶层没运算符但原文有括号 → 单个函数调用，1 个 token
    if ops == 0:
        return 1
    return 2 * ops + 1


def _walk_nodes(nodes: Iterable[dict]) -> Iterable[dict]:
    """递归遍历全部节点，含 BRANCH 的 conditions[] 里的 CONDITION。

    ★ CONDITION 自身也要 yield：它在 conditions 数组里，不在 nodes 里。
      旧实现只 yield 了 `c.get("nodes")`（分支下的子节点），
      把 CONDITION 本身漏掉，导致所有条件类校验（G12）从未执行。
    """
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        yield n
        for c in n.get("conditions") or []:
            if not isinstance(c, dict):
                continue
            yield c                       # ← CONDITION 自身（type="CONDITION"）
            yield from _walk_nodes(c.get("nodes") or [])
        yield from _walk_nodes(n.get("nodes") or [])


def _iter_values(node: dict) -> Iterable[dict]:
    for a in node.get("attrs") or []:
        v = a.get("value") or {}
        if v:
            yield v
    for key in ("value", "pageInfo", "forStart", "forEnd", "condition", "error"):
        v = node.get(key)
        if isinstance(v, dict) and v.get("type"):
            yield v
    # MAP_OPERATION 的键值映射（entries[].key / entries[].value）
    for e in node.get("entries") or []:
        if not isinstance(e, dict):
            continue
        for k in ("key", "value"):
            v = e.get(k)
            if isinstance(v, dict) and v.get("type"):
                yield v


def _check_expression_design_data(dd: dict, outs: set, problems: list,
                                  nid: str, at: str):
    """G1/G2 共用：检查表达式 designData 的段/token 匹配 + 悬空引用（含 subOps 递归）。"""
    tr = dd.get("expressionTranslation") or ""
    toks = dd.get("tokens") or []
    if tr and toks:
        # ★ G1 判据已按 643 条生产流程重写（旧「2*运算符数+1」误报率 43%）。
        #   真相：tokens 是**中序平铺**的，括号 `(` `)` 各占一个 OPERATOR token，
        #   中文「包含」是 FUNCTION 不是中缀，`&`/`|` 是单字符。
        #   唯一稳的判据是结构性的三条：
        #     a) 首 token 不能是二元 OPERATOR（`==` `>` `&` `|` 等）——那是错位
        #     b) tokens 里 `(` 与 `)` 数量必须相等
        #     c) 纯布尔字面量（单个 OPERATOR true/false）合法
        first = toks[0]
        binary_ops = {"==", "!=", ">", "<", ">=", "<=", "+", "-", "*", "/", "&", "|"}
        if first.get("type") == "OPERATOR" and str(first.get("value")) in binary_ops:
            problems.append(
                f"G1 {nid} {at}: 首个 token 是二元运算符 {first.get('value')!r} "
                f"→ 运算符错位，前端会渲染成「1 1」")
        vals = [str(t.get("value")) for t in toks if t.get("type") == "OPERATOR"]
        n_lp = vals.count("(")
        n_rp = vals.count(")")
        if n_lp != n_rp:
            problems.append(
                f"G1 {nid} {at}: 括号不配对 ( {n_lp} 个 / ) {n_rp} 个")
        # ★ 布尔字面量与逻辑非不是二元运算符：`false`/`true`（单 token 整个表达式）、
        #   `!` 前缀。实测生产里有 68 个表达式就是单 token `false`/`true`。
        literals = {"true", "false"}
        core = [v for v in vals if v not in ("(", ")") and v not in literals]
        # 全是字面量（无二元运算符无括号）→ 单 token 表达式，合法
        if not core and n_lp == 0:
            pass
        else:
            # 段数口径：括号也算 token，所以 tokens 数 = 2*运算符数+1 + 2*括号对数
            want = 2 * len(core) + 1 + 2 * n_lp
            if len(toks) != want:
                problems.append(
                    f"G1 {nid} {at}: token 数 {len(toks)} != 期望 {want} "
                    f"（{len(core)} 个运算符 + {n_lp} 对括号）translation={tr[:60]!r}")
    for t in _iter_tokens_recursive(toks):
        # ★ 系统变量不算悬空：真机里 27 次 G2 误报全是 `__SYSTEM_PARAMS.xxx`
        #   （应用配置参数，如系统名称/邮件通知系统连接）与 `system.currentUserId`。
        #   SYSTEM 类型 token 本来就不在 outs 里，按类型判断直接跳过。
        if t.get("type") != "VARIABLE":
            continue
        raw = str(t.get("value") or "")
        if raw.startswith("__SYSTEM_PARAMS") or raw.startswith("system."):
            continue
        if raw.split(".")[0] not in outs and raw not in outs:
            problems.append(f"G2 {nid} {at}: 表达式引用悬空 {raw!r}")


# 节点顶层直接引用前序出参的字段（区别于值槽位里的 selectParam）
# 这些字段本身就是一个 SelectParam，悬空会报 04004「前序节点发生变更请重新选择」
NODE_REF_FIELDS: tuple[str, ...] = ("selectParam", "selectMap", "dataSource")


def _entity_key(node: dict) -> str:
    """从 CREATE_ENTITY 节点取出实体短名（如 MigrationCheckpoint）。

    实体标识在 structure 里（id 是 domain fullName），取最后一段。
    """
    st = node.get("structure") or {}
    for cand in (st.get("id"), st.get("fullName"), st.get("name")):
        if cand and isinstance(cand, str):
            tail = cand.rsplit(".", 1)[-1]
            if tail and tail[0].isupper():
                return tail
    ob = node.get("output") or {}
    oid = ob.get("id") or ""
    if isinstance(oid, str) and oid:
        tail = oid.rsplit(".", 1)[-1]
        if tail.endswith("Dto"):
            return tail[:-3]
    return ""


def _load_entity_caps() -> dict | None:
    """读 entity-write-capability.json（构建产物扫描结果）。

    文件不存在时返回 None → G34/G35 静默跳过（不能因为缺证据就拦全量）。
    """
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "..", "..", "core", "facts", "udc", "microflow",
                        "entity-write-capability.json")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


_ENTITY_CAPS = _load_entity_caps()

# 系统字段的默认值表达式是平台惯例（修改人=当前用户、创建时间=当前时间等），
# 业务本来就不该给它们赋值，因此 G35 不把它们算作「覆盖了业务值」。
_SYSTEM_EXPR_FIELDS: frozenset[str] = frozenset({
    "updater", "creator", "createTime", "updateTime", "draft", "id",
    "creatorInstitution", "creatorDepartment", "creatorPost",
})


def _iter_node_refs(node: dict) -> Iterable[tuple[str, dict]]:
    """产出节点顶层的引用字段（selectParam / selectMap / dataSource）。"""
    for key in NODE_REF_FIELDS:
        v = node.get(key)
        if isinstance(v, dict) and v.get("outputName"):
            yield key, v


def _outputs(schema: dict) -> set[str]:
    names = set()
    inp = (schema.get("input") or {}).get("name")
    if inp:
        names.add(inp)
    # ★ MANUAL 触发时入参真名在 trigger.output.name（input 可能为 None），
    #   真实 643 条里 BASIC 入参 name=_FLOW_INPUT_*，引用它的节点不算悬空
    tout = (schema.get("trigger") or {}).get("output") or {}
    if isinstance(tout, dict) and tout.get("name"):
        names.add(tout["name"])
    for n in _walk_nodes(schema.get("nodes")):
        o = n.get("output") or {}
        if isinstance(o, dict) and o.get("name"):
            names.add(o["name"])
    return names


def run_gates(schema: dict, *, dep_apps: set[str] | None = None,
              app_name: str | None = None) -> list[str]:
    problems: list[str] = []
    outs = _outputs(schema)

    for n in _walk_nodes(schema.get("nodes")):
        nid = n.get("nodeId") or "?"
        at = n.get("actionType") or n.get("type") or "?"
        # G1 / G2
        for v in _iter_values(n):
            if v.get("type") == "Expression":
                try:
                    dd = json.loads((v.get("expression") or {}).get("schema") or "{}")["designData"]
                except Exception:
                    problems.append(f"G1 {nid}: Expression schema 无法解析")
                    continue
                _check_expression_design_data(dd, outs, problems, nid, at)
            sp = v.get("selectParam") if isinstance(v, dict) else None
            # ★ 只校「节点引用」：带 nodeInfo 或 outputName 指向真实 output。
            #   实体对象引用（outputName 形如 _<relationEntityId>）不在 outs 里，不算悬空。
            if isinstance(sp, dict) and sp.get("outputName") and sp.get("nodeInfo"):
                if sp["outputName"] not in outs:
                    problems.append(
                        f"G2 {nid} {at}: SelectParam.outputName 悬空 "
                        f"{sp['outputName']!r} → 会报 04004 前序节点已变更")
        # G2：节点顶层引用字段（selectParam/selectMap/dataSource）悬空
        for key, ref in _iter_node_refs(n):
            if ref.get("outputName") not in outs:
                problems.append(
                    f"G2 {nid} {at}: {key}.outputName 悬空 {ref['outputName']!r} "
                    f"→ 会报 04004 前序节点已变更")
        # G1 / G2（BRANCH 条件表达式，形态 2：{title,schema} 无 type/expression 外层包装）
        for c in n.get("conditions") or []:
            if not isinstance(c, dict):
                continue
            e = c.get("expression")
            if isinstance(e, dict) and e.get("schema"):
                try:
                    dd = json.loads(e["schema"])["designData"]
                except Exception:
                    problems.append(f"G1 {nid}: 分支条件表达式 schema 无法解析")
                    continue
                _check_expression_design_data(dd, outs, problems, nid, at)

        # G3 类型匹配
        if at in ("CREATE_ENTITY", "CREATE_BATCH_ENTITY", "CREATE_ENTITY_BATCH"):
            val = n.get("value") or {}
            sp = (val.get("selectParam") or {}) if isinstance(val, dict) else {}
            if val and val.get("type") == "SelectParam":
                if (sp.get("dataType") or "") not in ("DTO", "OBJECT"):
                    problems.append(f"G3 {nid} {at}: 只收实体对象，收到 {sp.get('dataType')}")
        if at == "CHANGE_LIST":
            ds = n.get("dataSource") or {}
            if ds.get("type") == "SelectParam" and (ds.get("selectParam") or {}).get("dataType") not in ("STRING", "OBJECT"):
                problems.append(f"G3 {nid} CHANGE_LIST: 只收文本列表，收到 "
                                f"{(ds.get('selectParam') or {}).get('dataType')}")

        # G7 分页必填 pageInfo（平台：propertyKey=pageInfo 必填未配置）
        if at in ("RETRIEVE_ARRAY", "RETRIEVE") and str(n.get("pageSearch")).lower() == "true":
            if not isinstance(n.get("pageInfo"), dict) or not n["pageInfo"].get("type"):
                problems.append(f"G7 {nid} {at}: pageSearch=true 但 pageInfo 为空 → 报「必填参数未配置」")

        # G4 数据映射
        # ★ 只查 id/caption：生产母版 DATA_MAPPING 的 mappingRule 本身就没有 name
        #   （master fixtures/microflow/backup/xzhAllNodesV16 实证），查 name 是误报
        if at == "DATA_MAPPING":
            mr = n.get("mappingRule")
            if not isinstance(mr, dict) or not (mr.get("id") or mr.get("caption")):
                problems.append(f"G4 {nid}: mappingRule 缺 id/caption（映射关系未配置）")

        # G5 跨应用依赖
        # ★ 只有调用方显式传入 dep_apps 才校验：dataSchema 顶层没有依赖字段
        #   （master/live 顶层 keys 均为 endNode/output/input/sourceType/trigger/nodes），
        #   依赖声明在 create body 上而非 schema 内，无 dep_apps 时跳过
        if at == "CALL_APP_SERVICE":
            app = n.get("app") or {}
            if dep_apps and not app.get("inApp"):
                name = app.get("appName")
                if name and name not in dep_apps:
                    problems.append(f"G5 {nid}: 应用 {name!r} 未声明依赖 → 会报「依赖应用已删除」")
            # G6 服务参数契约
            sm = n.get("selectMethod") or {}
            param = ((sm.get("parameter") or {}).get("item") or {})
            item_type = param.get("itemType") or ""
            for a in n.get("attrs") or []:
                at_id = (a.get("attrType") or {}).get("id") or ""
                if item_type and not at_id.startswith(item_type + "."):
                    problems.append(
                        f"G6 {nid}: 参数 {at_id!r} 不属于 {item_type} → 会报「必填参数未配置」")

        # ── G9 字段形态闸门（checkSchema 与 UI 都抓不到，只有抽屉里才看得出）──
        # MAP_OPERATION：basic 必须是 treeListSelector 选项对象，不能是裸字符串。
        #   传 "STRING" → 抽屉「数据类型」显示空占位；且 structure:{...basic}
        #   会把字符串迭代成 {"0":"S","1":"T",...} 垃圾。
        if at == "MAP_OPERATION" and (n.get("operationType") or "GET") == "GET":
            basic = n.get("basic")
            if not isinstance(basic, dict):
                problems.append(
                    f"G9 {nid} MAP_OPERATION: basic={basic!r} 必须是选项对象 "
                    f"{{label,value,key,dataType}}，裸字符串会让「数据类型」显示空占位")
            elif not (basic.get("dataType") or basic.get("key")):
                problems.append(f"G9 {nid} MAP_OPERATION: basic 缺 dataType/key")
            st = n.get("structure")
            if isinstance(st, dict):
                bad = [k for k in st if str(k).isdigit()]
                if bad:
                    problems.append(
                        f"G9 {nid} MAP_OPERATION: structure 被字符串迭代成字符下标 "
                        f"{bad[:6]}（根因是 basic 传了字符串）")
            # ★ nullPromptMessage 在 **UI 抽屉里**是必填（点「确定」报「请输入提示内容」），
            #   但 643 条生产流程里 24 个 MAP_OPERATION 全部为空且正常运行 →
            #   说明它是「UI 新增强校验」，存量数据不受影响，新建节点才需要。
            #   闸门不能因此拦存量/生产流程，只在显式要求校验 UI 时才报。
            #   （保留提示能力：调用方传 strict_ui=True 时检查）

        # CREATE_LIST：BASIC 列表建议带 value（默认值）。
        # ★ 母版 CREATE_LIST_U7yqmc 无 value 也能发布运行，故这里不算硬错；
        #   只有调用方要求「列表有初值」时才应显式传 default_value。
        #   （不加入 problems，避免对母版误报）

        # CREATE_ENTITY 的 value 若是 SelectParam，必须指向真实节点输出
        if at in ("CREATE_ENTITY", "CREATE_BATCH_ENTITY"):
            val = n.get("value")
            if isinstance(val, dict) and val.get("type") == "SelectParam":
                sp = val.get("selectParam") or {}
                if not sp.get("nodeInfo") and sp.get("outputName") not in outs:
                    problems.append(
                        f"G9 {nid} {at}: value 指向 {sp.get('outputName')!r} "
                        f"但该 output 不存在且无 nodeInfo → 运行时炸弹")

        # ── G12 分支条件（CONDITION）闸门 ──
        # 真机证据：智能项目管理平台 643 条 RELEASE 流程里 1981 个 CONDITION，
        #   name 只有 ifBranch(952) / elseBranch(941) / elseIfBranch(88) 三种，
        #   ifBranch 的 expression.resultTypeInfo 必须是 BOOLEAN，
        #   elseBranch 的 expression 必须是 null（不能赋表达式）。
        if at == "CONDITION":
            nm = n.get("name")
            if nm not in ("ifBranch", "elseBranch", "elseIfBranch"):
                problems.append(
                    f"G12 {nid}: CONDITION.name={nm!r} 非法，"
                    f"只能是 ifBranch / elseBranch / elseIfBranch")
            expr = n.get("expression")
            if nm == "elseBranch":
                if expr is not None:
                    problems.append(
                        f"G12 {nid} elseBranch: expression 必须为 null，"
                        f"给了 {type(expr).__name__} → 画布会把 else 当条件分支")
            else:
                if not isinstance(expr, dict) or not expr.get("schema"):
                    problems.append(
                        f"G12 {nid} {nm}: expression 未配置 → 保存报「请配置分支条件」")
                else:
                    sch = expr.get("schema")
                    try:
                        _s = json.loads(sch) if isinstance(sch, str) else sch
                        dd = (_s or {}).get("designData") or {}
                        rt = dd.get("resultTypeInfo")
                        if rt != "BOOLEAN":
                            problems.append(
                                f"G12 {nid} {nm}: resultTypeInfo={rt!r}，分支条件必须 BOOLEAN")
                        if not ((dd.get("runtimeData") or {}).get("executableExpr")
                                or (dd.get("expressionTranslation") or "").strip()):
                            problems.append(f"G12 {nid} {nm}: 表达式为空壳")
                    except Exception as e:
                        problems.append(f"G12 {nid} {nm}: expression.schema 解析失败 {e}")
                if not n.get("isCompleted"):
                    problems.append(f"G12 {nid} {nm}: isCompleted 非 true → 保存校验拦")

        # ── G13 事件投递（PUBLISH_BUSINESS_EVENT）闸门 ──
        # 真机证据：9 条生产流程 24 个节点，两种 eventType 字段集完全不同：
        #   IN_APP    → selectEvent（不是 selectMq！）
        #   AMONG_APP → selectMq + app（+ 可选 messageType / executeTime）
        if at == "PUBLISH_BUSINESS_EVENT":
            et = n.get("eventType")
            if et == "IN_APP":
                if not n.get("selectEvent"):
                    problems.append(
                        f"G13 {nid}: eventType=IN_APP 必须有 selectEvent"
                        f"（用 selectMq 是错的，事件选不上）")
            elif et == "AMONG_APP":
                if not n.get("selectMq"):
                    problems.append(
                        f"G13 {nid}: eventType=AMONG_APP 必须有 selectMq"
                        f"（用 selectEvent 是错的）")
                if not n.get("app"):
                    problems.append(f"G13 {nid}: eventType=AMONG_APP 必须有 app")
            else:
                problems.append(
                    f"G13 {nid}: eventType={et!r} 非法，只能是 IN_APP / AMONG_APP")
            if n.get("mappingType") == "attrs" and not (n.get("attrs") or []):
                problems.append(f"G13 {nid}: mappingType=attrs 但 attrs 为空 → 消息无载荷")

        # ── G14 连接器（CONNECTOR）闸门 ──
        # 643 条生产流程 0 样本，字段契约未验证；一旦出现必须有依赖应用
        if at == "CONNECTOR":
            app = n.get("app") or {}
            if not app.get("appName"):
                problems.append(
                    f"G14 {nid} CONNECTOR: 缺 app → 抽屉报「连接器依赖已移除，"
                    f"请在应用管理添加依赖后使用」（该节点无生产样本，契约待补测）")

        # END_NODE 不能出现在 nodes 数组里（前端保存时从 flowFrame 抽到顶层 endNode）
        if at in ("END_NODE", "END") and nid == "MFEndNode":
            problems.append(
                f"G9 {nid}: END 节点出现在 nodes 数组里 → 画布渲染「节点开发中...」；"
                f"必须在 schema 顶层 endNode，且 nodes 里不能有 END")
    # ── G15: RETRIEVE/RETRIEVE_ARRAY 组合查询条件顶层必须 GROUP（2026-10-30 实测）──
    # 手写 type="CONDITION" → 发布报 BOOT_3000「源对象不能为空」，checkSchema 全绿不报。
    # 15 轮发布二分定位。643 条真实样本 193/193 条件顶层都是 GROUP。
    for n in _walk_nodes(schema.get("nodes")):
        nid = n.get("nodeId") or "?"
        at = n.get("actionType") or n.get("type") or "?"
        for cond in n.get("condition") or []:
            if isinstance(cond, dict) and cond.get("type") == "CONDITION":
                problems.append(
                    f'G15 {nid}: condition[0].type 必须 "GROUP"（写 "CONDITION" → '
                    f'发布报 BOOT_3000 源对象不能为空，checkSchema 不报）')
                break

    # ── G16: 节点 type 必须与 actionType 匹配（实测：RETRIEVE type=ACTIVITY）──
    # 手写 RETRIEVE 节点 type="RETRIEVE" → checkSchema 报 DATA_INVALID。
    # 真实分布：RETRIEVE/CHANGE_ENTITY/CHANGE_VARIABLE/CREATE_* 等活动节点 type=ACTIVITY；
    # FOR_EACH type=FOR_EACH；BRANCH type=BRANCH；BREAK type=BREAK。
    _TYPE_MAP = {"ACTIVITY": {"RETRIEVE", "RETRIEVE_ARRAY", "CHANGE_ENTITY",
                              "CREATE_ENTITY", "DELETE_ENTITY", "CHANGE_VARIABLE",
                              "CREATE_VARIABLE", "CHANGE_BATCH_ENTITY",
                              "CREATE_BATCH_ENTITY", "CALL_APP_SERVICE",
                              "SUB_MICROFLOW", "CALL_DATA_FLOW", "LIST_OPERATION",
                              "CHANGE_LIST", "CREATE_LIST", "CREATE_MAP",
                              "MAP_OPERATION", "CONVERT_DATA", "DATA_MAPPING",
                              "PUBLISH_BUSINESS_EVENT", "CONNECTOR"}}
    # ★ 2026-11-02 更正：CUSTOM_ERROR / FOR_COUNT 不属于 ACTIVITY 族。
    #   证据：代码生成模板 `nodeActivityHandler` 的 21 个 case 里**没有** CustomError，
    #   CUSTOM_ERROR 在 `nodesLogicHandler` 里是独立的 `<#case "CustomError">`；
    #   `MicroFlowNodeTypeEnum.CUSTOM_ERROR(3,"CustomError")` 是独立枚举值。
    #   语料 3 个 CUSTOM_ERROR 样本全部 type=CUSTOM_ERROR。
    #   把 CUSTOM_ERROR 归到 ACTIVITY（旧版 G16 的做法）会逼着构造器写错 type，
    #   结果节点在代码生成阶段被静默丢弃——G38 就是为此设的。
    for n in _walk_nodes(schema.get("nodes")):
        nid = n.get("nodeId") or "?"
        at = n.get("actionType")
        ntype = n.get("type")
        if at and at in _TYPE_MAP.get("ACTIVITY", set()) and ntype != "ACTIVITY":
            problems.append(
                f"G16 {nid}: actionType={at} 的节点 type 必须 'ACTIVITY'，"
                f"现在是 {ntype!r}（checkSchema 报 DATA_INVALID）")

    # ── G17: BASIC 变量引用一致性（PageInfo 残留检测，2026-10-30 实测）──
    # CREATE_VARIABLE(BASIC)/RETRIEVE BASIC 出参是标量（dtoType 空）。
    # 任何引用它们的 SelectParam 若带 DTO 结构残留（id=DTO全名/dtoType 非空，
    # 如 CREATE_VARIABLE 模板的 PageInfo structure 被 _out_ref 误当 DTO），
    # 前端表达式就悬空：「变量: vJdbc. 在上下文中不存在」。checkSchema 不报。
    _BASIC_DT = ("BOOLEAN", "STRING", "BIGINTEGER", "DECIMAL", "INTEGER", "DATETIME")
    _basic_outputs = {}   # outputName -> dataType（仅标量出参）
    for n0 in _walk_nodes(schema.get("nodes")):
        o0 = n0.get("output") or {}
        if (isinstance(o0, dict) and o0.get("name")
                and o0.get("dataType") in _BASIC_DT and not o0.get("dtoType")):
            _basic_outputs[o0["name"]] = o0["dataType"]
    to0 = schema.get("trigger", {}).get("output") or {}
    if isinstance(to0, dict) and to0.get("dataType") in _BASIC_DT and not to0.get("dtoType"):
        _basic_outputs[to0.get("name")] = to0["dataType"]

    def _scan_basic_ref(obj, path):
        if isinstance(obj, dict):
            if obj.get("type") == "SelectParam" and isinstance(obj.get("selectParam"), dict):
                sp0 = obj["selectParam"]
                on0 = sp0.get("outputName")
                if on0 in _basic_outputs and (sp0.get("id") or sp0.get("dtoType")):
                    problems.append(
                        f"G17 {path}: 引用 BASIC 变量 {on0} 的 selectParam "
                        f"id/dtoType 必须空串（现在 id={sp0.get('id')!r}, "
                        f"dtoType={sp0.get('dtoType')!r}）→ PageInfo 模板残留")
            for k0, v0 in obj.items():
                _scan_basic_ref(v0, path + "." + str(k0))
        elif isinstance(obj, list):
            for i0, v0 in enumerate(obj):
                _scan_basic_ref(v0, path + "[%d]" % i0)
    _scan_basic_ref(schema.get("endNode") or {}, "endNode")
    for n0 in _walk_nodes(schema.get("nodes")):
        _scan_basic_ref(n0, n0.get("nodeId") or "?")

    # ── G18: MANUAL 入参/出参 name 必须 _FLOW_INPUT_/_FLOW_OUTPUT_ 前缀 ──
    # name 写业务名（如 "数据源ID"）前端变量表不认 → 表达式悬空「vJdbc. 不存在」。
    # 643 条真实样本：MANUAL trigger.output.name 恒 _FLOW_INPUT_xxxxxx（随机6位），
    # endNode BASIC output.name 恒 _FLOW_OUTPUT_xxxxxx。业务名在 desc。
    trg = schema.get("trigger") or {}
    _BASIC_TYPES = ("BOOLEAN", "STRING", "BIGINTEGER", "DECIMAL", "INTEGER", "DATETIME")
    if (trg.get("type") == "MANUAL" and isinstance(trg.get("output"), dict)
            and (trg["output"].get("paramType") == "BASIC"
                 or trg["output"].get("dataType") in _BASIC_TYPES)):
        nm = trg["output"].get("name") or ""
        if not nm.startswith("_FLOW_INPUT_"):
            problems.append(
                f"G18 trigger.output.name={nm!r} 必须 _FLOW_INPUT_ 前缀"
                f"（业务名放 desc，前端按 _FLOW_INPUT_ 注册变量表）")
    endn = schema.get("endNode") or {}
    if (isinstance(endn.get("output"), dict)
            and endn["output"].get("dataType") in ("BOOLEAN", "STRING", "BIGINTEGER",
                                                    "DECIMAL", "INTEGER", "DATETIME")):
        nm = endn["output"].get("name") or ""
        if nm and not nm.startswith("_FLOW_OUTPUT_"):
            problems.append(
                f"G18 endNode.output.name={nm!r} 必须 _FLOW_OUTPUT_ 前缀")

    # ── G19: 写操作节点出参必须是「影响行数」标量，不是实体 DTO（2026-10-30 编译实证）──
    # 643 条真实样本 100%：CHANGE_ENTITY 103/103 INTEGER、CHANGE_BATCH_ENTITY 41/41 INTEGER、
    # DELETE_ENTITY 13/13 INTEGER、CREATE_BATCH_ENTITY 6/6 INTEGER、CREATE_ENTITY 32/32 BIGINTEGER。
    # 写成 DTO → 平台生成 SingleResponse<Integer> 赋给 SingleResponse<Dto> → Java 编译失败
    # （实测报错：不兼容的类型: SingleResponse<java.lang.Integer> 无法转换）。
    # ★ checkSchema 与发布全绿，只有真构建才炸。
    _WRITE_ACTIONS = {
        "CHANGE_ENTITY": ("INTEGER", "BIGINTEGER"),
        "CHANGE_BATCH_ENTITY": ("INTEGER", "BIGINTEGER"),
        "DELETE_ENTITY": ("INTEGER", "BIGINTEGER"),
        "CREATE_BATCH_ENTITY": ("INTEGER", "BIGINTEGER"),
        "CREATE_ENTITY": ("BIGINTEGER", "INTEGER"),
    }
    for n1 in _walk_nodes(schema.get("nodes")):
        at1 = n1.get("actionType")
        if at1 not in _WRITE_ACTIONS:
            continue
        o1 = n1.get("output") or {}
        if not isinstance(o1, dict):
            continue
        dt1 = o1.get("dataType")
        if dt1 not in _WRITE_ACTIONS[at1] or o1.get("dtoType"):
            problems.append(
                f"G19 {n1.get('caption') or n1.get('nodeId')}: {at1} 出参必须是影响行数"
                f"（dataType={'/'.join(_WRITE_ACTIONS[at1])}、dtoType 空），"
                f"现在是 dataType={dt1!r} dtoType={o1.get('dtoType')!r} → 平台生成"
                f" SingleResponse<Integer> 无法赋给 Dto，Java 编译失败")

    # ── G20: 写操作节点的操作对象必须引用「活动节点」出参，不能直引控制节点（循环/分支）──
    # 643 条真实样本：CHANGE_ENTITY 的 selectParam 来源 103/103 是活动节点
    # （RETRIEVE 95 / CREATE_VARIABLE 4 / FLOW 3 / BUSINESS 1），0 例直引 FOR_EACH。
    # 直引循环项 → 平台生成代码把循环下标(int)当 Dto 传参 → 编译失败
    # （实测报错：不兼容的类型: int无法转换为...MigrationDatasourceDto）。
    # 正确做法：循环体内先 RETRIEVE(IDS, 引循环项.id) 或 CREATE_VARIABLE(ENTITY_OBJECT)，
    # 写操作引用该活动节点出参。
    for n2 in _walk_nodes(schema.get("nodes")):
        at2 = n2.get("actionType")
        if at2 not in _WRITE_ACTIONS:
            continue
        sp2 = n2.get("selectParam")
        if not isinstance(sp2, dict):
            continue
        ni2 = sp2.get("nodeInfo") or {}
        nt2 = ni2.get("type")
        if nt2 and nt2 != "ACTIVITY":
            problems.append(
                f"G20 {n2.get('caption') or n2.get('nodeId')}: {at2} 的操作对象直引了 "
                f"{nt2} 节点出参（{sp2.get('outputName')}）→ 平台生成 int→DTO 代码，Java 编译失败；"
                f"循环内请改走 RETRIEVE(IDS, 引循环项.id) 中转后再引用")


    # ── G21: MANUAL 触发必须带「参数显示名称」trigger.desc（且与 output.desc 一致）──
    # 设计器「参数名称」必填框绑的是 trigger.desc；只有 output.desc 时前端是一个空黄框，
    # 服务端 checkSchema/发布/编译全绿，但 UI 上必填未填（用户截图三次）。
    trg_ = schema.get("trigger") or {}
    if (trg_.get("type") == "MANUAL"
            and trg_.get("paramType") not in (None, "NONE")):
        out_ = trg_.get("output") or {}
        d_trg, d_out = (trg_.get("desc") or "").strip(), (out_.get("desc") or "").strip()
        if not d_trg:
            problems.append(
                "G21 触发节点: MANUAL 入参缺 trigger.desc（参数显示名称）→ 设计器「参数名称」是空黄框")
        elif d_out and d_trg != d_out:
            problems.append(
                f"G21 触发节点: trigger.desc={d_trg!r} 与 output.desc={d_out!r} 不一致（真实样本恒相等）")

    # ── G22: 每个节点必须有非空 caption 且 isCompleted 不为 False ──
    # 红色节点（未完成态）的唯一权威来源就是这个字段；缺省/False 一律拦。
    for n3 in _walk_nodes(schema.get("nodes")):
        cap3 = (n3.get("caption") or "").strip()
        if not cap3:
            problems.append(f"G22 {n3.get('nodeId')}: 节点缺 caption（设计器显示为空节点）")
        if n3.get("isCompleted") is False:
            problems.append(f"G22 {n3.get('caption') or n3.get('nodeId')}: isCompleted=False（设计器显示红色未完成）")

    # ── G24: 更新数据的 selectParam 必须带 key（否则「选择更新的数据」下拉空白）──
    # 事件来源还必须是 <eventMfCustomDtoName>.info + position=children，带 relationEntity
    # 等多余键会被判成「所选"X"已变更」。
    for n4 in _walk_nodes(schema.get("nodes")):
        if n4.get("actionType") != "CHANGE_ENTITY":
            continue
        sp4 = n4.get("selectParam") or {}
        cap4 = n4.get("caption") or n4.get("nodeId")
        if not sp4.get("key"):
            problems.append(f"G24 {cap4}: selectParam 缺 key（设计器「选择更新的数据」空白黄框）")
        src4 = (sp4.get("nodeInfo") or {}).get("actionType")
        if src4 == "BUSINESS_EVENT":
            if sp4.get("position") != "children":
                problems.append(f"G24 {cap4}: 事件来源 position 必须 children（现 {sp4.get('position')!r}）")
            if not str(sp4.get("id") or "").endswith(".info"):
                problems.append(f"G24 {cap4}: 事件来源 id 必须是 <eventMfCustomDtoName>.info")
            for bad in ("relationEntity", "relationEntityFullName", "nodeInfo"):
                if bad in sp4 and bad != "nodeInfo":
                    problems.append(f"G24 {cap4}: 事件来源不能带 {bad}（会被判「所选已变更」）")

    # ── G25: 创建变量(实体对象) 的 attrType 必须 20 键齐（缺则左侧红字「所选数据已失效」）──
    _NEED = ("refId", "relationEntity", "relationEntityId", "filterRelationEntity")
    for n5 in _walk_nodes(schema.get("nodes")):
        if n5.get("actionType") != "CREATE_VARIABLE" or n5.get("paramType") != "ENTITY_OBJECT":
            continue
        for a5 in (n5.get("attrs") or []):
            at5 = a5.get("attrType") or {}
            miss = [k for k in _NEED if k not in at5]
            if miss:
                problems.append(
                    "G25 %s: attrType 缺 %s（设计器字段映射左侧红字「所选数据已失效」）"
                    % (n5.get("caption") or n5.get("nodeId"), ",".join(miss)))
                break

    # ── G26: 自定义服务必须带完整方法签名（md5/parameter/returnValue）──
    #    实测：删掉 selectMethod.md5 后 G1–G25 全绿、发布也能过，
    #    但设计器里「参数」页签取不到出入参 → 必填参数全空。签名必须来自接口原样返回。
    for n6 in _walk_nodes(schema.get("nodes")):
        if n6.get("actionType") != "CALL_APP_SERVICE":
            continue
        m6 = n6.get("selectMethod") or {}
        miss6 = [k for k in ("md5", "parameter", "returnValue", "fullName") if not m6.get(k)]
        if miss6:
            problems.append("G26 %s: selectMethod 缺 %s（必须原样取自 SearchMethodByNamePost，"
                            "否则设计器参数页签取不到出入参）"
                            % (n6.get("caption") or n6.get("nodeId"), ",".join(miss6)))

    # ── G27: 修改变量(attrs 字段映射) 的 attrType 同样必须带引用四键 ──
    #    实测：G25 只查 CREATE_VARIABLE，CHANGE_VARIABLE 的 attrs 走同一套
    #    「所选数据已失效」前端校验，缺键一样红字，必须同规则拦。
    for n7 in _walk_nodes(schema.get("nodes")):
        if n7.get("actionType") != "CHANGE_VARIABLE" or n7.get("mappingType") != "attrs":
            continue
        for a7 in (n7.get("attrs") or []):
            at7 = a7.get("attrType") or {}
            miss7 = [k for k in _NEED if k not in at7]
            if miss7:
                problems.append(
                    "G27 %s: attrType 缺 %s（设计器字段映射左侧红字「所选数据已失效」，同 G25）"
                    % (n7.get("caption") or n7.get("nodeId"), ",".join(miss7)))
                break

    # ── G28: DATA_MAPPING 每条映射行必须 targetField/mappingMode/value 齐 ──
    #    实测：G4 只查 mappingRule 顶层 name；行级缺 targetField 时全绿放行，
    #    设计器里该行显示为空映射，提交后转换结果字段为空。
    for n8 in _walk_nodes(schema.get("nodes")):
        if n8.get("actionType") != "DATA_MAPPING":
            continue
        rows8 = ((n8.get("mappingRule") or {}).get("mappingRows")) or []
        if not rows8:
            problems.append("G28 %s: mappingRule.mappingRows 为空（设计器映射表空白）"
                            % (n8.get("caption") or n8.get("nodeId")))
            continue
        for r8 in rows8:
            miss8 = [k for k in ("targetField", "mappingMode", "value") if not r8.get(k)]
            if miss8:
                problems.append("G28 %s: 映射行缺 %s（该行会变成空映射）"
                                % (n8.get("caption") or n8.get("nodeId"), ",".join(miss8)))
                break

    # ── G29: DATA_MAPPING 不接受「单对象实体」上游（真实构建实测 2026-10-31）──
    #    语料 39 条：主流形态 SUB_ENTITY/children（13 条）+ 空引用（22 条）；
    #    MASTER_ENTITY+parent 单对象形态代码生成器会把节点输出声明成 List<Dto>
    #    再对它取字段 → 后端编译失败（VerifyDataMapping1928Service.getName() 找不到符号，
    #    backBuild.log compile-info/8704025620829192834/20261031185114）。
    #    设计器/checkSchema/一致性检测全不拦，只有构建能暴露 —— 必须闸门拦。
    for n9 in _walk_nodes(schema.get("nodes")):
        if n9.get("actionType") != "DATA_MAPPING":
            continue
        sp9 = n9.get("selectParam") or {}
        # 语料 39 条：parent 位置 10 条里 9 条 type=ARRAY（列表引用），OBJECT 单对象仅
        # 1 条且引用的是实体入参变量而非节点出参。实测单对象节点出参上游 → 构建编译失败。
        if sp9.get("type") == "OBJECT" and sp9.get("dtoType") == "MASTER_ENTITY" and sp9.get("position") == "parent":
            problems.append(
                "G29 %s: DATA_MAPPING 上游为单对象主实体（type=OBJECT）→ 代码生成器按 List 处理"
                "会编译失败（backBuild.log 20261031185114 实证）；上游必须是列表（type=ARRAY，"
                "RETRIEVE_ARRAY/子表列表）" % (n9.get("caption") or n9.get("nodeId")))

    # ── G30: 赋值方式/引用形态硬校验（来源=node-settings-capability.json 矩阵）──
    #    用户实测：赋值方式不选 → 前端不知道生成什么类型代码，依赖配置不出现，构建必炸。
    #    语料裁决：实体型（ENTITY_OBJECT/DEFAULT_OBJECT/OTHER）100% 显式带
    #    mappingType ∈ {attrs=字段映射, value=对象引用, mapping=自动映射}；
    #    BASIC 无 mappingType（模式由 value 形态表达），但 value=SelectParam 引用
    #    25/25 带 selectParam.path。
    for nA in _walk_nodes(schema.get("nodes")):
        atA = nA.get("actionType")
        if atA == "CREATE_VARIABLE":
            ptA = nA.get("paramType")
            mtA = nA.get("mappingType")
            if ptA in ("ENTITY_OBJECT", "DEFAULT_OBJECT", "OTHER") and mtA not in ("attrs", "value", "mapping"):
                problems.append("G30 %s: 变量类型=%s 必须显式带 mappingType（attrs/value/mapping 三选一，"
                                "语料 100%%）" % (nA.get("caption") or nA.get("nodeId"), ptA))
            elif mtA == "value":
                # 对象引用形态（语料 36/36）：value.type=SelectParam 且恒无 attrs
                vA0 = nA.get("value") or {}
                if vA0.get("type") != "SelectParam":
                    problems.append("G30 %s: mappingType=value（对象引用）必须 value.type=SelectParam（语料 36/36）"
                                    % (nA.get("caption") or nA.get("nodeId")))
                if nA.get("attrs"):
                    problems.append("G30 %s: mappingType=value 不应带 attrs（语料 36/36 恒无）"
                                    % (nA.get("caption") or nA.get("nodeId")))
            elif mtA == "mapping":
                # 自动映射形态（语料 35 条）：必须有 mapping[] 且带 selectParam 源对象
                if not (nA.get("mapping") or []):
                    problems.append("G30 %s: mappingType=mapping（自动映射）缺 mapping[] 行"
                                    % (nA.get("caption") or nA.get("nodeId")))
                if not (nA.get("selectParam") or {}).get("outputName"):
                    problems.append("G30 %s: mappingType=mapping 缺 selectParam 源对象引用"
                                    % (nA.get("caption") or nA.get("nodeId")))
                for rA in (nA.get("mapping") or []):
                    if not (rA.get("attrType") or {}).get("id") or not (rA.get("value") or {}).get("selectParam"):
                        problems.append("G30 %s: mapping 行缺 attrType.id 或 value.selectParam"
                                        % (nA.get("caption") or nA.get("nodeId")))
                        break
            vA = nA.get("value")
            if ptA == "BASIC" and isinstance(vA, dict) and vA.get("type") == "SelectParam":
                spA = vA.get("selectParam") or {}
                # path 仅在「DTO 字段引用」（id=<Dto>.<field>）时必需（语料 25/25 均此形态）；
                # 引用 BASIC 标量出参（id 空串，G17 形态）无字段可指，豁免
                if spA.get("id") and "." in str(spA.get("id")) and not spA.get("path"):
                    problems.append("G30 %s: BASIC 引用 DTO 字段缺 selectParam.path（语料 25/25 必带）"
                                    % (nA.get("caption") or nA.get("nodeId")))
        elif atA == "CHANGE_VARIABLE":
            if nA.get("mappingType") == "attrs" and not nA.get("attrs"):
                problems.append("G30 %s: mappingType=attrs 但 attrs 为空（字段映射没配行）"
                                % (nA.get("caption") or nA.get("nodeId")))
            elif nA.get("mappingType") == "value" and not nA.get("value"):
                problems.append("G30 %s: mappingType=value（对象引用）但 value 为空"
                                % (nA.get("caption") or nA.get("nodeId")))
            elif not nA.get("mappingType") and not nA.get("value"):
                problems.append("G30 %s: attrs 与 value 都为空（赋值方式没选）"
                                % (nA.get("caption") or nA.get("nodeId")))

    # ── G31: 引用链类型校验（前后数据流通性）──
    #    引用槽（selectParam/selectMap/dataSource/value）的 outputName 必须来自
    #    前序节点出参/入参；dataType 与 ARRAY/OBJECT 必须与出参声明一致。
    _collect_outputs = {}
    _inp = (schema.get("trigger") or {}).get("input") or {}
    # ★ 事件触发器（BUSINESS_EVENT）的入参在 schema["input"]（= trigger.output 事件数据），
    #   MANUAL 的在 trigger.input。finish() 里 BUSINESS_EVENT 的 input 是 ev_in=trigger.output，
    #   而 trigger.input 恒为 None —— 只读 trigger.input 会漏掉事件入参，误报悬空。
    if not _inp.get("name"):
        _inp = schema.get("input") or {}
    if _inp.get("name"):
        _collect_outputs[_inp["name"]] = ("INPUT", _inp.get("dataType"), _inp.get("type", "OBJECT"))
    for nB in _walk_nodes(schema.get("nodes")):
        refs = []
        for slot in ("selectParam", "selectMap", "dataSource", "value"):
            vB = nB.get(slot)
            if isinstance(vB, dict) and vB.get("type") == "SelectParam":
                refs.append(vB.get("selectParam") or {})
            elif isinstance(vB, dict) and vB.get("outputName") and vB.get("type") in ("ARRAY", "OBJECT"):
                refs.append(vB)
        capB = nB.get("caption") or nB.get("nodeId")
        for ref in refs:
            on = ref.get("outputName")
            if not on or on.startswith("_FLOW_INPUT_"):
                continue
            if on not in _collect_outputs:
                problems.append("G31 %s: 引用 %r 不存在于任何前序节点出参/入参（悬空引用）" % (capB, on))
            else:
                _src, _dt, _ty = _collect_outputs[on]
                # 字段级引用（position=children）：selectParam.dataType 是**字段**类型，
                # 不是出参类型（出参是 DTO 容器），不与出参声明比对；
                # outputName 存在性已在上行校验。
                # ★ 字段级引用的真判据不是 position：
                #   语料里 position=parent 且 dataType=字段类型 的有 1646 条
                #   （循环项字段、部分实体字段都用 parent）。
                #   可靠判据：整节点引用的 name 恒等于 outputName（2301+19 条），
                #   字段引用的 name 是字段名（7951 条）—— 用 name 判，不用 position。
                _whole = (ref.get("name") == on)
                _field_ref = not _whole
                if ref.get("dataType") and _dt and not _field_ref and ref["dataType"] != _dt:
                    problems.append("G31 %s: 引用 %r dataType=%s 与出参声明 %s 不一致" % (capB, on, ref["dataType"], _dt))
                if ref.get("type") and _ty and ref["type"] != _ty:
                    problems.append("G31 %s: 引用 %r type=%s 与出参声明 %s 不一致（List/单对象错接）" % (capB, on, ref["type"], _ty))
        ob = nB.get("output") or {}
        if isinstance(ob, dict) and ob.get("name"):
            _collect_outputs[ob["name"]] = ("NODE:" + capB, ob.get("dataType"), ob.get("type", "OBJECT"))

    # ── G23: 节点契约（逐节点必填/形态，见 node_contracts.py）──
    try:
        from .node_contracts import check_contracts
        problems.extend(check_contracts(schema))
    except Exception as _e:  # 契约表本身出错不能静默
        problems.append(f"G23 契约校验异常: {_e}")

    # ── G32: CONVERT_DATA 类型转换形态（语料 214 条裁决，2026-10-31）──
    _CD = {"Split": (("OBJECT", "STRING"), ("ARRAY", "STRING"), True),
           "multiAssociation2List": (("OBJECT", "ENTITY"), ("ARRAY", "BIGINTEGER"), False),
           "List2multiAssociation": (("ARRAY", "BIGINTEGER"), ("OBJECT", "STRING"), False),
           "String2Long": (("OBJECT", "STRING"), ("OBJECT", "BIGINTEGER"), False),
           "BasicData2String": (("OBJECT", None), ("OBJECT", "STRING"), False)}
    _RX = ("COMMA", "DIVLINE", "SLASH", "PERIOD", "MIDLINE")
    for n in _walk_nodes(schema.get("nodes")):
        if (n.get("actionType") or n.get("type")) != "CONVERT_DATA":
            continue
        cap = n.get("caption") or n.get("nodeId") or "?"
        ct = n.get("convertType") or {}
        kind = ct.get("value")
        if not kind:
            problems.append("G32 [%s] convertType 缺失（子模式没选）" % cap)
            continue
        if kind not in _CD:
            problems.append("G32 [%s] convertType.value=%r 不在语料枚举 %s"
                            % (cap, kind, sorted(_CD)))
            continue
        src_shape, out_shape, need_rx = _CD[kind]
        sp = n.get("selectParam") or {}
        if not sp.get("outputName"):
            problems.append("G32 [%s] selectParam 缺 outputName（源没选）" % cap)
        else:
            st, sd = src_shape
            if st and sp.get("type") != st:
                problems.append("G32 [%s] %s 源 selectParam.type 应为 %s，得到 %r"
                                % (cap, kind, st, sp.get("type")))
            if sd and sp.get("dataType") != sd:
                problems.append("G32 [%s] %s 源 selectParam.dataType 应为 %s，得到 %r"
                                % (cap, kind, sd, sp.get("dataType")))
        # 目标形态三处一致：convertType vs output
        ob = n.get("output") or {}
        for key, exp in (("type", out_shape[0]), ("dataType", out_shape[1])):
            if ob.get(key) != exp or ct.get(key) != exp:
                problems.append("G32 [%s] %s 目标 %s 应为 %r（convertType=%r output=%r）"
                                % (cap, kind, key, exp, ct.get(key), ob.get(key)))
        # javaType 必须跟着 dataType 走：只改 dataType 会让代码生成按模板的 String
        # 声明变量，运行期赋 Long → 编译「Long 无法转换为 String」（2026-11-03 实测）
        _JT = {"Split": "java.lang.String", "multiAssociation2List": "java.lang.Long",
               "List2multiAssociation": "java.lang.String",
               "BasicData2String": "java.lang.String", "String2Long": "java.lang.Long"}
        if ob.get("javaType") != _JT[kind]:
            problems.append("G32 [%s] %s 目标 javaType 应为 %r，得到 %r"
                            % (cap, kind, _JT[kind], ob.get("javaType")))
        # regex：Split 必带且枚举内；其余语料恒无
        if need_rx:
            if n.get("regex") not in _RX:
                problems.append("G32 [%s] Split 必须带 regex（枚举 %s），得到 %r"
                                % (cap, _RX, n.get("regex")))
        elif n.get("regex") is not None:
            problems.append("G32 [%s] %s 语料恒无 regex，却带了 %r"
                            % (cap, kind, n.get("regex")))

    # ── G33: CALL_DATA_FLOW 执行生单规则（语料 1 条 + dataflow-api.md）──
    # ★ 2026-11-02 双证：前端 merge:{dataFlowMappingId:"dataFlow.id"} 强制两者相等；
    #   运行时 CallDataFlowActivity.parseActivityNode 只读 dataFlowMappingId（dataFlow 不参与解析），
    #   校验集合键名 data-flow-mapping-id-used-by-micro-flow 由 DataFlowMappingDto.getId() 填充
    #   → 值必须是 DataFlowMapping 主键（列表行 id），不是 dataFlowId。
    #   CONDITION 模式（默认）下 condition 必填：buildConditionInfo(..., required=true)。
    for n in _walk_nodes(schema.get("nodes")):
        if (n.get("actionType") or n.get("type")) != "CALL_DATA_FLOW":
            continue
        cap = n.get("caption") or n.get("nodeId") or "?"
        df = n.get("dataFlow") or {}
        if not df.get("id"):
            problems.append("G33 [%s] dataFlow 缺 id（生单规则没选）" % cap)
        if str(n.get("dataFlowMappingId") or "") != str(df.get("id") or ""):
            problems.append("G33 [%s] dataFlowMappingId(%r) 与 dataFlow.id(%r) 不一致"
                            % (cap, n.get("dataFlowMappingId"), df.get("id")))
        if n.get("dataSourceType") != "CONDITION":
            problems.append("G33 [%s] dataSourceType=%r，语料实测仅 CONDITION"
                            "（选择数据形态无样本，暂不放行）" % (cap, n.get("dataSourceType")))
        if not n.get("condition"):
            problems.append("G33 [%s] condition 缺失（CONDITION 形态必须带条件组）" % cap)
        if not n.get("structure"):
            problems.append("G33 [%s] structure 缺失（来源实体）" % cap)
        ob = n.get("output") or {}
        if ob.get("id") != "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto":
            problems.append("G33 [%s] output 恒平台固定 CallDataFlowResultDto，实际 %r"
                            % (cap, ob.get("id")))

    # ── G34/G35: CREATE_ENTITY 实体可写性（源码级证据，2026-11-02）──
    #   G34 平台把 CREATE_ENTITY 编译成 xxxAppService.create(SingleRequest)，
    #       实体没有 create() 方法 → 构建期「找不到符号」，必须提前拦。
    #   G35 实体字段若配了默认值表达式且 requireNull=false，preCreateBatch 会
    #       无条件覆盖传入值（源码 executeExpression* 第二参数）。配了
    #       currentYear() 之类又撞自身约束的实体，永远插不进去。
    if _ENTITY_CAPS is not None:
        for n in _walk_nodes(schema.get("nodes")):
            if (n.get("actionType") or n.get("type")) != "CREATE_ENTITY":
                continue
            cap = n.get("caption") or n.get("nodeId") or "?"
            ent = _entity_key(n)
            if not ent:
                continue
            info = (_ENTITY_CAPS.get("entities") or {}).get(ent)
            if info is None:
                continue
            if info.get("has_create") is False:
                problems.append(
                    "G34 [%s] 实体 %s 没有 create() 方法（facade api 无 "
                    "SingleResponse<Long> create(SingleRequest)）→ 构建期必然"
                    "「找不到符号」，CREATE_ENTITY 不可用于此实体" % (cap, ent))
            risky = sorted(f for f, d in (info.get("fields") or {}).items()
                           if not d.get("require_null")
                           and f not in _SYSTEM_EXPR_FIELDS)
            if risky:
                problems.append(
                    "G35 [%s] 实体 %s 的字段 %s 配了默认值表达式且 requireNull=false，"
                    "create 时会被无条件覆盖 → 传入值不生效"
                    % (cap, ent, ", ".join(risky[:6])))

    # ── G36 DELETE_ENTITY 模式与字段自洽 ────────────────────────────
    # 2026-11-02 实测：CONDITION 模式的条件右值填 SelectParam（节点引用）→
    #   publish 被拒 `BOOT_1001 Parameter Error`，响应无任何字段级提示，
    #   只能靠二分才定位到。要按动态记录删除必须走 SELECT_PARAM 模式。
    for n in _walk_nodes(schema.get("nodes")):
        if (n.get("actionType") or "").upper() != "DELETE_ENTITY":
            continue
        cap = n.get("caption") or n.get("nodeId")
        dt = (n.get("deleteType") or "").upper()
        if dt == "SELECT_PARAM":
            if not n.get("selectParam"):
                problems.append(
                    "G36 [%s] deleteType=SELECT_PARAM 但缺 selectParam"
                    "（要删除哪条记录？引用前序 DTO 出参）" % cap)
            for k in ("app", "structure", "condition", "methodLegal"):
                if k in n:
                    problems.append(
                        "G36 [%s] deleteType=SELECT_PARAM 不应带 %s 键"
                        "（那是 CONDITION 模式的字段，混带会被平台拒）" % (cap, k))
        else:
            for grp in (n.get("condition") or []):
                for c in (grp.get("conditions") or []):
                    for rp in (c.get("rightParams") or []):
                        if (rp.get("type") or "") == "SelectParam":
                            problems.append(
                                "G36 [%s] CONDITION 模式的删除条件右值不能引用节点"
                                "（SelectParam）→ publish 必被拒 BOOT_1001；"
                                "按动态记录删除请改用 from_node → SELECT_PARAM 模式"
                                % cap)

    # G37：引用槽必须指向前序节点的出参（outputName 不能为空）
    # ★ 2026-11-02 实测：把 CHANGE_LIST 节点当列表源传给 CREATE_BATCH_ENTITY，
    #   而 CHANGE_LIST 真实样本 output 恒为 null（原地改列表），于是 batch 的
    #   selectParam.outputName 为空 —— 本地全部闸门放行，publish 才被拒：
    #     check=false errors=[('[4-批量插入]','….selectParam.outputName','PROPERTY_IS_REQUIRED')]
    # 语料核查：fixtures 里 10 种节点的 selectParam 共 22 个，空 outputName 的 0 个。
    node_ids = {n.get("nodeId") for n in _walk_nodes(schema.get("nodes")) if n.get("nodeId")}
    trig_id = (schema.get("trigger") or {}).get("nodeId")
    for n in _walk_nodes(schema.get("nodes")):
        sp = n.get("selectParam")
        if not isinstance(sp, dict) or not sp:
            continue
        cap = n.get("caption") or n.get("nodeId")
        src = ((sp.get("nodeInfo") or {}).get("nodeId") or "")
        if "outputName" in sp and not (sp.get("outputName") or "").strip():
            problems.append(
                "G37 [%s] selectParam.outputName 为空 → publish 必被拒 PROPERTY_IS_REQUIRED。%s"
                % (cap, ("引用的 %s 没有出参（如 CHANGE_LIST 原地改列表、output=null），"
                         "请改引它操作的那个列表节点" % src) if src else "引用槽没指向任何节点"))
        elif "outputName" in sp and src and src not in node_ids and src != trig_id:
            problems.append("G37 [%s] selectParam 引用的节点 %s 不在流程里（悬空引用）"
                            % (cap, src))

    # G38：逻辑节点的 type 必须等于它的 actionType（BREAK / CUSTOM_ERROR）
    # ★ 2026-11-02 实测 + 字节码双证：解析器按 `MicroFlowNodeTypeEnum.valueOf(type)` 选解析器，
    #   代码生成模板按 `node.type` 分发（`<#case "Break">` → `break;`）。
    #   把 BREAK 写成 type=ACTIVITY 时：ActivityNodeTypeEnum 里没有 BREAK、
    #   Activity 分支里也没有 BREAK case → **节点被静默丢弃**。
    #   实测后果：构建 SUCCESS、publish 通过、运行 success=true，但循环照跑 3 次（对照也是 3 次），
    #   全程零报错。这是最难查的一类：所有闸门都绿，只有业务结果不对。
    _LOGIC_TYPES = ("BREAK", "CUSTOM_ERROR")
    for n in _walk_nodes(schema.get("nodes")):
        at, ty = n.get("actionType"), n.get("type")
        if at in _LOGIC_TYPES and ty != at:
            problems.append(
                "G38 [%s] actionType=%s 但 type=%r → 会被解析成普通 Activity 并静默丢弃"
                "（构建/发布/运行全不报错，只是不生效）。type 必须写成 %r"
                % (n.get("caption") or n.get("nodeId"), at, ty, at))
        elif ty in _LOGIC_TYPES and at is not None and at != ty:
            problems.append("G38 [%s] type=%s 但 actionType=%r（两者必须一致）"
                            % (n.get("caption") or n.get("nodeId"), ty, at))
        elif ty == "BREAK" and at is None:
            # ★ BREAK 真实样本 32/32 都有 actionType（node-contract keys 含 actionType），
            #   只有 CUSTOM_ERROR 是「无 actionType、type=CUSTOM_ERROR」。
            #   BREAK 缺 actionType 仍拦；CUSTOM_ERROR 缺 actionType 放行（真实形态）。
            problems.append("G38 [%s] type=BREAK 但缺 actionType（真实样本必有，"
                            "写 type=BREAK + actionType=BREAK）"
                            % (n.get("caption") or n.get("nodeId")))

    # G39：条件右值必须是平台认识的槽（CONSTANT/SelectParam/Expression…）
    # ★ 2026-11-02 实测：把 DSL 的 {"const": x} 原样塞进 rightParams 时，平台解析出
    #   value=""、desc=""，**条件静默失效** —— RETRIEVE_ARRAY 返回整张表（23 条），
    #   构建 SUCCESS、运行 success=true，只有读侧数据不对。
    #   合法形态必须是 {"type":"CONSTANT","value":...,"desc":...} 这类带 type 的槽。
    for n in _walk_nodes(schema.get("nodes")):
        for grp in n.get("condition") or []:
            if not isinstance(grp, dict):
                continue
            for c in grp.get("conditions") or []:
                if not isinstance(c, dict):
                    continue
                for rp in c.get("rightParams") or []:
                    if not isinstance(rp, dict):
                        continue
                    if "type" not in rp:
                        problems.append(
                            "G39 [%s] 条件右值缺 type（%r）→ 平台会解析成空值，条件静默失效"
                            % (n.get("caption") or n.get("nodeId"),
                               list(rp)[:4]))
                    elif rp.get("type") == "CONSTANT" and "value" not in rp:
                        problems.append(
                            "G39 [%s] CONSTANT 右值缺 value → 条件静默失效"
                            % (n.get("caption") or n.get("nodeId")))

    # G40：CHANGE_LIST 的四种动作形态必须与真实枚举一致（317 条样本实测）
    #   ADD 266 / REPLACE 28 → selectParam + dataSource(元素)
    #   CLEAR 15            → 只有 selectParam（带 dataSource 会被判非法）
    #   REMOVE 8            → selectParam + dataSource + countAttrs（按字段匹配元素）
    #   ★ 枚举里没有 DELETE；早期构造器无条件写 dataSource 且默认 ADD。
    _CL_ACTIONS = ("ADD", "REPLACE", "CLEAR", "REMOVE")
    for n in _walk_nodes(schema.get("nodes")):
        if (n.get("actionType") or "") != "CHANGE_LIST":
            continue
        act = (n.get("action") or "").upper()
        cap = n.get("caption") or n.get("nodeId")
        if act not in _CL_ACTIONS:
            problems.append("G40 [%s] action=%r 非法（真实枚举 %s）"
                            % (cap, n.get("action"), list(_CL_ACTIONS)))
            continue
        has_ds = bool(n.get("dataSource"))
        if act == "CLEAR":
            if has_ds:
                problems.append("G40 [%s] CLEAR 不该有 dataSource（15 条真实样本都没有）" % cap)
        elif not has_ds:
            problems.append("G40 [%s] %s 缺 dataSource" % (cap, act))
        if act == "REMOVE" and not (n.get("countAttrs") or []):
            problems.append("G40 [%s] REMOVE 缺 countAttrs（按哪些字段匹配元素）" % cap)

    # G41：字段级引用（SelectParam position=children）类型必须匹配目标字段
    #   2026-11-04 实测：processedRows(BIGINTEGER) 引用 totalAmount(DECIMAL 字段) →
    #   前端抽屉标红「所选'总金额'已变更」，运行时 BigDecimal 自动转 Long 假绿（读库正确）。
    #   字段级引用 children 时 selectParam.dataType 必须等于 attrType.dataType；
    #   标量出参（SIZE/SUM/MIN/MAX）走表达式（_scalar_value_slot），不是 children，不受此约束。
    _WRITE_ACTIONS = ("CREATE_ENTITY", "CHANGE_ENTITY", "CREATE_BATCH_ENTITY", "CHANGE_BATCH_ENTITY")
    for n in _walk_nodes(schema.get("nodes")):
        if (n.get("actionType") or "") not in _WRITE_ACTIONS:
            continue
        cap = n.get("caption") or n.get("nodeId")
        for at in n.get("attrs") or []:
            v = at.get("value") or {}
            if v.get("type") != "SelectParam":
                continue
            sp = v.get("selectParam") or {}
            if sp.get("position") != "children":
                continue  # 整节点引用（parent）不在本闸门范围
            tgt = (at.get("attrType") or {}).get("dataType")
            src = sp.get("dataType")
            if tgt and src and tgt != src:
                problems.append(
                    "G41 [%s] 字段级引用类型不匹配：%s(%s) 引用 %s(%s) → 前端「已变更」"
                    % (cap, (at.get("attrType") or {}).get("name"), tgt,
                       sp.get("name"), src))

    return problems


def run_end_gate(schema: dict) -> list[str]:
    """G11 结束节点闸门：顶层 endNode 必须完整，否则画布显示「节点开发中...」。

    权威结构（前端 bundle + fixtures/microflow/backup/xzhAllNodesV16 双证）：
      nodeId=MFEndNode / type=END / actionType=END_NODE / caption=结束
    前端保存时 `o.endNode = flowNodes[END]`，nodes 只放 flowFrame.slice(1)，
    所以 END 塞进 nodes 会渲染成占位符。
    """
    problems: list[str] = []
    en = schema.get("endNode")
    if not isinstance(en, dict) or not en:
        problems.append("G11 endNode 缺失或为空 {} → 画布结束节点显示「节点开发中...」")
        return problems
    for k, want in (("nodeId", "MFEndNode"), ("type", "END"), ("actionType", "END_NODE")):
        if en.get(k) != want:
            problems.append(f"G11 endNode.{k}={en.get(k)!r}，应为 {want!r}")
    if not en.get("caption"):
        problems.append("G11 endNode.caption 为空")
    # ★ endNode.value 为空是合法状态，实测 643 条生产流程：
    #   paramType=NONE(88) / DEFAULT_OBJECT(83) / BASIC(51) / None(79) 都可无 value；
    #   事件监听(61) 与定时任务(24) 本身无对外出参。只有 paramType 明确声明
    #   了对象类型（ENTITY_OBJECT/DEFAULT_OBJECT 且要求引用）时才该有 value，
    #   但那属于业务配置，不是结构缺陷 → 不报。

    return problems


def run_leak_gate(schema: dict, node_ids: set[str] | None = None) -> list[str]:
    """G10 模板引用泄漏闸门。

    从 fixtures 模板复制节点时，模板里指向**它自己兄弟节点**的引用
    （dataSource.name / selectMap.name / selectParam.name）不会自动重写。
    这类悬空引用会让前端报「引用的参数 vText 已失效，请重新配置！」
    或让「选择映射」下拉空着；而 checkSchema 只校验必填字段存在，
    不校验指向有效性，所以能发布成功却在 UI 报错。

    判据：任何 SelectParam 的 `nodeInfo.nodeId` 必须在本流程节点表内；
    无 nodeInfo 时退化为校验 `outputName` 是否等于某个节点 output.name。
    """
    problems: list[str] = []
    known: set[str] = set(node_ids or ())
    outs: set[str] = set()
    for n in _walk_nodes(schema.get("nodes")):
        if n.get("nodeId"):
            known.add(n["nodeId"])
        o = n.get("output") or {}
        if isinstance(o, dict) and o.get("name"):
            outs.add(o["name"])
    # ★ trigger 也是合法引用源：事件监听/定时任务的出参（如 _BUSINESS_EVENT_xxx）
    #   不在 nodes 里，但前序节点可以引用它。实测 643 条流程里 327 次 G10
    #   全是这个误报——事件类流程必然引用 trigger 出参。
    trg = schema.get("trigger") or {}
    if trg.get("nodeId"):
        known.add(trg["nodeId"])
    to = trg.get("output") or {}
    if isinstance(to, dict) and to.get("name"):
        outs.add(to["name"])
    known.update({"MFStartNode", "MFEndNode"})

    def _check_ref(sp, path):
        """校验单个引用对象的 nodeInfo.nodeId / outputName 是否指向本流程真实节点。"""
        ni = (sp.get("nodeInfo") or {}).get("nodeId")
        on = sp.get("outputName")
        if ni:
            if ni not in known:
                problems.append(
                    f"G10 {path}: 引用 nodeInfo.nodeId={ni!r} 不在本流程节点表 → "
                    f"前端报「引用的参数已失效」")
        elif on and on not in outs:
            # ★ 无 nodeInfo 时只对「形似节点输出」的名字报警（_<ACTION>_<hex6>）；
            #   实体引用 _<relationEntityId> 是纯数字 id，不是节点引用，跳过
            if re.match(r"^_[A-Z][A-Z_]+_[A-Za-z0-9]{4,}$", str(on)):
                problems.append(
                    f"G10 {path}: 引用 outputName={on!r} 不存在 → "
                    f"前端报「引用的参数已失效」")

    # ★ 引用有两类载体，必须都扫（本闸门曾只扫值槽位而漏掉节点顶层引用）：
    #   ① 值槽位：{type:"SelectParam", selectParam:{...}}
    #   ② 节点顶层裸引用字段：node.selectParam / node.selectMap / node.dataSource
    #      这些没有 type 外壳，直接就是引用对象
    BARE_REF_FIELDS = ("selectParam", "selectMap", "dataSource")

    def scan(obj, path="root"):
        if isinstance(obj, dict):
            if obj.get("type") == "SelectParam" and isinstance(obj.get("selectParam"), dict):
                sp = obj["selectParam"]
                _check_ref(sp, path)
            # ② 节点顶层裸引用字段（无 type 外壳）
            for f in BARE_REF_FIELDS:
                v = obj.get(f)
                if isinstance(v, dict) and (v.get("outputName") or v.get("nodeInfo")):
                    _check_ref(v, "%s.%s" % (path, f))
            for k, v in obj.items():
                scan(v, "%s.%s" % (path, k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, "%s[%d]" % (path, i))

    scan(schema)

    return problems


def run_order_gate(schema: dict, strict: bool = False) -> list[str]:
    """G8 顺序闸门：赋值/条件只能引用它**前面**已出现的节点出参。

    平台「前序节点发生变更请重新选择」有两类根因：
      a) 引用名不存在（G2/G10 拦）
      b) 引用名存在但排在后面（本闸门，仅 strict=True 时拦）

    ★ 生产母版实证：`CHANGE_VARIABLE_sqv49j`(index 9) 引用了后序的
      `RETRIEVE_KNCEzh`(index 10)，母版可正常发布运行 → 平台**不强制**
      引用顺序。所以默认 strict=False 不报顺序问题，避免挡真实业务流；
      只在需要「按执行顺序最稳」的场景显式开 strict。
    """
    problems: list[str] = []
    seen: set[str] = set()
    inp = (schema.get("input") or {}).get("name")
    if inp:
        seen.add(inp)

    def refs(n):
        out = []
        for v in _iter_values(n):
            sp = v.get("selectParam") if isinstance(v, dict) else None
            if isinstance(sp, dict) and sp.get("outputName"):
                out.append(sp["outputName"])
            if v.get("type") == "Expression":
                try:
                    dd = json.loads((v.get("expression") or {}).get("schema") or "{}")["designData"]
                    for t in _iter_tokens_recursive(dd.get("tokens")):
                        if t.get("type") == "VARIABLE":
                            out.append(str(t.get("value", "")).split(".")[0])
                except Exception:
                    pass
        return out

    def walk(ns):
        for n in ns or []:
            nid = n.get("nodeId") or "?"
            at = n.get("actionType") or n.get("type")
            if strict:
                for r in refs(n):
                    if r not in seen:
                        problems.append("G8 %s %s: 引用了尚未出现的 %r" % (nid, at, r))
            o = (n.get("output") or {}).get("name")
            if o:
                seen.add(o)
            for c in n.get("conditions") or []:
                walk(c.get("nodes"))
            walk(n.get("nodes"))
    walk(schema.get("nodes"))
    return problems

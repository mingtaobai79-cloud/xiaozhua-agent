"""高频微流程节点构造器。

所有字段名都来自**全库真实节点反推**（见
`components/udc/microflow_constraints.py` 的 NODE_REQUIRED_FIELDS 注释），
不是从反编译参数名猜的 —— 两套名字不一样，按反编译写会 100% 误杀。

三条硬约束：

  1. **必填字段照真实表填** —— 生成后立刻跑 `validate_node_fields`，不通过就抛。
  2. **选择器字段不能自造** —— `RETRIEVE`/`RETRIEVE_ARRAY` 的 `app`/`structure`/
     `title`/`selectType`/`scope`/`methodLegal`、`CHANGE_ENTITY` 的 `selectParam`、
     `CALL_APP_SERVICE` 的 `app`/`selectMethod`、`SUB_MICROFLOW` 的 `mfService`
     全部由平台选择器回填，本模块只接受调用方传进来的真实对象。
  3. **无出参的节点写 output=None** —— 不许造假。

用法：
    from components.udc.microflow.nodes import (
        condition, left_param, retrieve, change_entity, create_variable,
    )
    # app / structure 必须来自实体选择器接口
    n = retrieve(app, structure, title="合同档案_1",
                 condition_=condition(left_param("dto", "fInt"), "EQ", 1))
"""
from __future__ import annotations

from components.udc.microflow.build import make_node, param, uid6
from components.udc.microflow_constraints import (
    CONDITION_OPERATORS,
    condition_operator_size,
    validate_node_fields,
)

# ---------------------------------------------------------------------------
# 条件
# ---------------------------------------------------------------------------


def left_param(dto: str, field: str) -> dict:
    """条件左值。后端 LeftParamDto 要求 dto + field 均 @NotBlank。"""
    return {"dto": dto, "field": field}


def right_param(value, *, kind: str = "CONSTANT") -> dict:
    """条件右值。kind ∈ CONSTANT / EXPRESSION / CONTEXT_VARIABLE。"""
    return {"type": kind, "value": value}


def condition(left: dict, operator: str, right=None, *, right_kind: str = "CONSTANT") -> dict:
    """单条件。

    operator 必须是 CONDITION_OPERATORS 里的 22 个之一；
    右参数个数由表决定（0 个：NULL/NOTNULL/ZERO/NOTZERO；2 个：BETWEEN/NOTBETWEEN）。
    """
    if operator not in CONDITION_OPERATORS:
        raise ValueError("未知操作符 %r，只能是 %s" % (operator, sorted(CONDITION_OPERATORS)))
    size = condition_operator_size(operator)
    rights = []
    if size == 0:
        if right is not None:
            raise ValueError("%s 不接受右参数" % operator)
    elif size == 1:
        if right is None:
            raise ValueError("%s 需要 1 个右参数" % operator)
        rights = [right_param(right, kind=right_kind)]
    elif size == 2:
        if not isinstance(right, (list, tuple)) or len(right) != 2:
            raise ValueError("%s 需要 2 个右参数（列表）" % operator)
        rights = [right_param(v, kind=right_kind) for v in right]

    return {
        "type": "CONDITION",
        "leftParam": left,
        "operator": operator,
        "rightParams": rights,
        "nullRightValueCondType": "IGNORE_IF_ANY_NULL",
        "relation": "ONE2ONE",
    }


def condition_group(items: list[dict], *, logical: str = "AND") -> dict:
    """条件组。

    ★ 后端 checkConditionLegal：GROUP 内从第 2 个条件起 logicalOperator 不可为空，
      所以这里给每个子项都补上，而不是只给组本身。
    """
    if logical not in ("AND", "OR"):
        raise ValueError("logical 只能是 AND / OR")
    if not items:
        raise ValueError("条件组不能为空")
    filled = []
    for i, it in enumerate(items):
        x = dict(it)
        if i >= 1:
            x.setdefault("logicalOperator", logical)
        filled.append(x)
    return {
        "type": "GROUP",
        "logicalOperator": logical,
        "leftParam": None,
        "operator": None,
        "rightParams": [],
        "conditions": filled,
    }


def _check(action_type: str, node: dict) -> dict:
    errs = validate_node_fields(action_type, node)
    if errs:
        raise ValueError("；".join(errs))
    return node


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------


def _retrieve_output(structure: dict, *, data_type: str, desc: str,
                     prefix: str = "_RETRIEVE_") -> dict:
    """出参从 structure 推导 —— 真实节点就是这么长的。"""
    return {
        "appName": structure.get("appName") or "",
        "id": structure.get("id") or "",
        "javaType": structure.get("fullName") or structure.get("id") or "",
        "dataType": data_type,
        "type": "OBJECT",
        "desc": desc,
        "dtoType": structure.get("dtoType") or "",
        "udcApp": structure.get("udcApp"),
        "name": "%s%s" % (prefix, uid6()),
    }


def retrieve(app: dict, structure: dict, *, title: str,
             condition_=None, value=None, fetch_type: str = "CONDITION",
             null_handling: str = "CONTINUE", null_prompt: str = "",
             select_type: str = "DTO", scope: str = "OBJECT",
             need_cascade: bool = None, output_desc: str = "",
             caption: str = "查询单条数据") -> dict:
    """查询单条数据（RETRIEVE）。

    app / structure: **必须来自实体选择器接口的真实返回**，不能手拼。
    title:           选择器回填的显示名（如「合同档案_1」）。
    """
    for k in ("id", "fullName"):
        if not structure.get(k):
            raise ValueError("structure 缺 %r：必须来自实体选择器，不能自造" % k)
    if not app.get("appName"):
        raise ValueError("app.appName 不能为空（必须来自实体选择器）")
    if fetch_type == "CONDITION" and condition_ is None and value is None:
        raise ValueError("fetchType=CONDITION 时 condition 或 value 至少要有一个")

    node = make_node(
        "RETRIEVE", caption=caption,
        fetchType=fetch_type,
        app=app,
        structure=structure,
        title=title,
        selectType=select_type,
        scope=scope,
        nullHandling=null_handling,
        methodLegal=structure.get("methodLegal"),
        condition=condition_,
        value=value,
        output=_retrieve_output(structure, data_type=select_type,
                                desc=output_desc or title),
    )
    if need_cascade is not None:
        node["needCascade"] = need_cascade
    if null_handling == "TERMINATION":
        node["nullPromptMessage"] = null_prompt
    for k in ("condition", "value"):
        if node.get(k) is None:
            node.pop(k, None)
    return _check("RETRIEVE", node)


def retrieve_array(app: dict, structure: dict, *, variable_title: str,
                   condition_=None, value=None, fetch_type: str = "CONDITION",
                   select_type: str = "DTO", scope: str = "OBJECT",
                   size: int = None, page_search: bool = None,
                   output_desc: str = "", caption: str = "查询多条数据") -> dict:
    """查询多条数据（RETRIEVE_ARRAY）。

    ★ 注意字段名是 `variableTitle` 不是 `title`（实测 523 个节点全是 variableTitle）。
    """
    for k in ("id", "fullName"):
        if not structure.get(k):
            raise ValueError("structure 缺 %r：必须来自实体选择器，不能自造" % k)
    if not app.get("appName"):
        raise ValueError("app.appName 不能为空（必须来自实体选择器）")
    if fetch_type == "CONDITION" and condition_ is None and value is None:
        raise ValueError("fetchType=CONDITION 时 condition 或 value 至少要有一个")

    node = make_node(
        "RETRIEVE_ARRAY", caption=caption,
        fetchType=fetch_type,
        app=app,
        structure=structure,
        variableTitle=variable_title,
        selectType=select_type,
        scope=scope,
        methodLegal=structure.get("methodLegal"),
        condition=condition_,
        value=value,
        output=_retrieve_output(structure, data_type="ARRAY",
                                desc=output_desc or variable_title,
                                prefix="_RETRIEVE_ARRAY_"),
    )
    if size is not None:
        node["size"] = size
    if page_search is not None:
        node["pageSearch"] = page_search
    for k in ("condition", "value"):
        if node.get(k) is None:
            node.pop(k, None)
    return _check("RETRIEVE_ARRAY", node)


# ---------------------------------------------------------------------------
# 写
# ---------------------------------------------------------------------------


def change_entity(select_param: dict, *, title: str, condition_=None,
                  caption: str = "更新数据") -> dict:
    """更新数据（CHANGE_ENTITY）。

    ★ 真实必填是 `selectParam` + `title`，**不是 `mappingType`**
      （旧表按反编译写 mappingType，374/374 = 100% 误杀）。
    """
    if not select_param:
        raise ValueError("selectParam 不能为空（必须来自实体/字段选择器）")
    node = make_node(
        "CHANGE_ENTITY", caption=caption,
        selectParam=select_param, title=title,
        condition=condition_,
        output=None,          # 无出参
    )
    if node.get("condition") is None:
        node.pop("condition", None)
    return _check("CHANGE_ENTITY", node)


def create_entity(entity: dict, *, mapping_type: str = "attrs",
                  mapping: list = None, caption: str = "插入数据",
                  app: dict = None, structure: dict = None,
                  value: dict = None, title: str = None) -> dict:
    """插入数据。

    ★ 前端权威必填：app / structure / mappingType / value / title
      —— value 即使 mappingType=attrs 也要给，否则页面报必填。
    """
    if value is None:
        name = "_" + str((structure or {}).get("relationEntity") or "entity")
        value = {"type": "SelectParam", "selectParam": {
            "name": name, "description": title or caption,
            "dataType": "DTO", "type": "OBJECT", "position": "parent",
            "outputName": name}}
    node = make_node(
        "CREATE_ENTITY", caption=caption,
        entity=entity, app=app, structure=structure,
        mappingType=mapping_type, mapping=mapping or [],
        value=value, title=title or caption,
        output=None,
    )
    return _check("CREATE_ENTITY", node)


def delete_entity(entity: dict, *, delete_type: str = "CONDITION",
                  condition_=None, caption: str = "删除数据",
                  app: dict = None, structure: dict = None,
                  title: str = None, condition=None) -> dict:
    """删除数据。

    ★ 前端权威必填：deleteType / app / structure / condition / title
    """
    node = make_node(
        "DELETE_ENTITY", caption=caption,
        entity=entity, app=app, structure=structure,
        deleteType=delete_type,
        condition=condition if condition is not None else condition_,
        title=title or caption,
        output=None,
    )
    return _check("DELETE_ENTITY", node)


# ---------------------------------------------------------------------------
# 调用
# ---------------------------------------------------------------------------


def signature(param_item_type: str, return_item_type: str, *,
              param_caption: str = None, ret_caption: str = None,
              param_type: str = "SingleRequest",
              return_type: str = "SingleResponse") -> dict:
    """生成合法的 selectMethod 参数签名（直接喂给 `call_app_service`）。

    ★ type 是**全限定名**，真实数据就是 `com.seeyon.boot.transport.SingleRequest`；
      校验器按短名比对，所以传短名也会被自动补成 FQN。
    ★ item.itemType 是作用域键，`attrs[].attrType.id` 必须带它做前缀 —— 不能猜，
      这个值必须来自 searchMethodByName 的真实返回。
    """
    PT = "com.seeyon.boot.transport."
    p_t = param_type if "." in param_type else PT + param_type
    r_t = return_type if "." in return_type else PT + return_type
    return {
        "parameter": {"caption": param_caption, "type": p_t,
                      "item": {"enums": None, "itemType": param_item_type, "item": None}},
        "returnValue": {"caption": ret_caption, "type": r_t,
                        "item": {"enums": None, "itemType": return_item_type, "item": None}},
    }


def call_app_service(app: dict, select_method: dict, *, mapping_type: str = None,
                     value=None, select_param=None, page_info=None,
                     output_name: str = None, output_desc: str = "",
                     caption: str = "自定义服务") -> dict:
    """自定义服务（CALL_APP_SERVICE）。

    app:           {"appName":..., "inApp":bool, "caption":..., "udcApp":False,
                    "dynamicDependency":"NONE"} —— 必须来自 searchApps 的真实返回
    select_method: {"fullName":..., "implClass":..., "parameter":..., "returnValue":...}
                   来自 searchMethodByName；也可用 `signature()` 组装

    ★ 入参是 DTO 时必须 mappingType="attrs" 并给 attrs[]；
      入参是标量（java.lang.Long 等）时 mappingType 应为 None、用 value 传单值。
      实测 39 个真实节点：24 个 DTO(attrs) + 15 个标量(null)。
    """
    if not app.get("appName"):
        raise ValueError("app.appName 不能为空（必须来自 searchApps）")
    if not select_method.get("fullName"):
        raise ValueError("selectMethod.fullName 不能为空（必须来自候选集接口）")

    sm = dict(select_method)
    for key in ("parameter", "returnValue"):
        item = (sm.get(key) or {}).get("item") or {}
        if not item.get("itemType"):
            raise ValueError(
                "selectMethod.%s.item.itemType 缺失：该字段是作用域键，不能猜。"
                "请用 searchMethodByName(methodFullName=<类名>.<方法名>) 取真实签名，"
                "或用 signature(param_item_type=..., return_item_type=...) 组装" % key)

    suffix = uid6()
    node = make_node(
        "CALL_APP_SERVICE", caption=caption,
        app=app,
        selectMethod=sm,
        value=value,
        selectParam=select_param if select_param is not None else {},
        pageInfo=page_info if page_info is not None else {"needTotal": False,
                                                          "pageNumber": 1, "pageSize": 20},
        outputName=output_name or suffix,
        outPutDesc=output_desc,
    )
    if mapping_type is not None:
        node["mappingType"] = mapping_type
    node["output"] = param("_CALL_APP_SERVICE_%s" % suffix, "OBJECT", output_desc)
    return _check("CALL_APP_SERVICE", node)


def sub_microflow(mf_service: dict, *, mapping_type: str = None, value=None,
                  output_desc: str = "", caption: str = "子微流程") -> dict:
    """子微流程（SUB_MICROFLOW）。

    ★ 真实必填只有 `mfService`（旧表写 mappingType，327/640 = 51% 误杀）。
    mf_service.type 必须是 0(SERVICE) / 3(CUSTOM)；type=1 前端微流程不可引用。
    """
    if not mf_service:
        raise ValueError("mfService 不能为空（必须来自微流程候选集）")
    if str(mf_service.get("type")) == "1":
        raise ValueError("type=1 是前端微流程，不可被规则/微流程引用")
    suffix = uid6()
    node = make_node(
        "SUB_MICROFLOW", caption=caption,
        mfService=mf_service,
        value=value,
        outputName=suffix,
        output=param("_SUB_MICROFLOW_%s" % suffix, "OBJECT", output_desc),
    )
    if mapping_type is not None:
        node["mappingType"] = mapping_type
    return _check("SUB_MICROFLOW", node)


# ---------------------------------------------------------------------------
# 变量 / 循环 / 错误
# ---------------------------------------------------------------------------


_JAVA_TYPE = {
    "STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
    "LONG": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
    "DOUBLE": "java.lang.Double", "DATE": "java.util.Date",
    "DECIMAL": "java.math.BigDecimal",
}


def create_variable(title: str, data_type: str = "STRING", *, param_type: str = "BASIC",
                    value=None, desc: str = "", caption: str = "创建变量") -> dict:
    """创建变量（CREATE_VARIABLE）。

    ★ 真实必填是 `paramType` + `title` + `dataType`；
      旧表写 `metaDataType`/`otherType`，1782/1782 = 100% 误杀。
    `title` 是变量显示名（如「变量_1」），不是变量名。
    """
    if not title:
        raise ValueError("title 不能为空（变量显示名，如「变量_1」）")
    node = make_node(
        "CREATE_VARIABLE", caption=caption,
        paramType=param_type, title=title, dataType=data_type,
        value=value,
        output={
            "id": "", "javaType": _JAVA_TYPE.get(data_type, data_type),
            "dataType": data_type, "type": "OBJECT", "desc": desc or title,
            "dtoType": "", "name": "_CREATE_VARIABLE_%s" % uid6(),
        },
    )
    if node.get("value") is None:
        node.pop("value", None)
    return _check("CREATE_VARIABLE", node)


def change_variable(select_param: dict, *, value=None, caption: str = "修改变量") -> dict:
    """修改变量（CHANGE_VARIABLE）。真实必填只有 `selectParam`。"""
    if not select_param:
        raise ValueError("selectParam 不能为空（必须来自变量选择器）")
    node = make_node("CHANGE_VARIABLE", caption=caption,
                     selectParam=select_param, value=value, output=None)
    if node.get("value") is None:
        node.pop("value", None)
    return _check("CHANGE_VARIABLE", node)


def for_each(for_end, nodes: list[dict], *, for_start=1, step: int = 1,
             operator: str = "<=", caption: str = "计数循环",
             target_name: str = "序号") -> dict:
    """计数循环（FOR）。

    ★ 真实形态是**计数循环**，不是列表遍历：
      operator / forStep / forStart / forEnd 四项全必填，foreach 恒为 null。
      （旧实现用 items/operator/forStep，漏了 forStart/forEnd，直接报必填。）
    ★ output 也必填，否则 checkSchema 报 PROPERTY_IS_REQUIRED。
    ★ 要"跳出循环"必须写成 FOR { BRANCH { ifBranch: [BREAK] } }，
      BREAK 不能直接挂在 FOR 的 nodes 下（40/40 真实样本父节点都是 BRANCH）。
    """
    suffix = uid6()

    def _bound(v):
        if isinstance(v, dict):
            return v
        return {"type": "Simple", "simple": v, "desc": v}

    node = make_node(
        "FOR", caption=caption,
        targetName=target_name,
        operator=operator, forStep=step,
        forStart=_bound(for_start), forEnd=_bound(for_end),
        foreach=None,
        nodes=nodes,
        output={"id": None, "javaType": "java.lang.Integer", "dataType": "INTEGER",
                "type": "OBJECT", "desc": "", "name": "_FOR_%s" % suffix},
    )
    return _check("FOR", node)


def custom_error(message: str, *, level: str = "ERROR", caption: str = "自定义错误") -> dict:
    node = make_node("CUSTOM_ERROR", caption=caption, error=message,
                     errorType=level, output=None)
    return _check("CUSTOM_ERROR", node)


__all__ = [
    "left_param", "right_param", "condition", "condition_group",
    "retrieve", "retrieve_array",
    "change_entity", "create_entity", "delete_entity",
    "call_app_service", "signature", "sub_microflow",
    "create_variable", "change_variable", "for_each", "custom_error",
]

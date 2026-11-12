"""节点构造 v2：数据节点（CRUD）+ 变量节点。定义驱动，字段从定义库取 md5。

依赖 node_builder.NodeBuilder + microflow_fields。
"""
from __future__ import annotations

from typing import Any

from .microflow_fields import (
    entity_structure, field_attr, field_left_param, field_select_param,
    condition_group, constant, simple, context_variable,
)
from .node_builder import NodeBuilder


# ★ 写操作节点出参不是实体 DTO，而是「影响行数」（643 条真实样本 100% 一致）：
#   CHANGE_ENTITY 103/103 INTEGER / CHANGE_BATCH_ENTITY 41/41 INTEGER
#   DELETE_ENTITY 13/13 INTEGER / CREATE_BATCH_ENTITY 6/6 INTEGER
#   CREATE_ENTITY 32/32 BIGINTEGER（新增记录 id）
# 写成 DTO 会让平台生成 SingleResponse<Integer> → SingleResponse<Dto> 的 Java 代码编译失败
# （实测报错：不兼容的类型 SingleResponse<java.lang.Integer> 无法转换）。
_WRITE_RESULT = {
    "CHANGE_ENTITY": ("INTEGER", "java.lang.Integer", "更新成功的数量"),
    "CHANGE_BATCH_ENTITY": ("INTEGER", "java.lang.Integer", "更新成功的数量"),
    "DELETE_ENTITY": ("INTEGER", "java.lang.Integer", "删除成功的数量"),
    "CREATE_BATCH_ENTITY": ("INTEGER", "java.lang.Integer", "新增成功的数量"),
    "CREATE_ENTITY": ("BIGINTEGER", "java.lang.Long", "新增数据的ID"),
}


def _write_output(action_type: str, node_id: str, caption_suffix: str = "") -> dict[str, Any]:
    """写操作节点出参：影响行数（INTEGER）/ 新增 id（BIGINTEGER）。"""
    dt, jt, desc = _WRITE_RESULT.get(action_type, ("INTEGER", "java.lang.Integer", "成功的数量"))
    return {"id": None, "javaType": jt, "dataType": dt, "type": "OBJECT",
            "desc": desc + caption_suffix, "name": "_" + node_id}


def _entity_output(entity: dict[str, Any], node_id: str, caption_suffix: str = "_1",
                   is_array: bool = False) -> dict[str, Any]:
    """实体 DTO 出参（查询类节点用）。写操作节点请用 _write_output。"""
    dto = entity["fullName"]
    return {
        "id": dto, "javaType": dto, "dataType": "DTO",
        "type": "ARRAY" if is_array else "OBJECT", "desc": entity["caption"] + caption_suffix,
        "appName": entity.get("refApp"), "dtoType": "MASTER_ENTITY", "udcApp": True,
        "relationEntity": entity["relationEntityId"], "name": "_" + node_id,
    }


# --------------------------------------------------------------------------
# 数据活动
# --------------------------------------------------------------------------
def retrieve(builder: NodeBuilder, entity: dict[str, Any], cond_field: str,
             right_value: dict[str, Any] | None = None,
             caption: str = "查询单条数据",
             id_value: dict[str, Any] | None = None,
             null_handling: str = "CONTINUE",
             null_message: str = "") -> dict[str, Any]:
    """查询单条数据。两种真实形态（实测 246 IDS / 375 CONDITION）：

    | 形态 | fetchType | 判别载荷 | 业务含义 |
    |---|---|---|---|
    | 条件查询 | `CONDITION` | `condition[]` | 按字段过滤 |
    | ID 查询   | `IDS`       | `value{}`    | 按主键 ID 取一条 |

    ★ ID 查询（246 次真实用法）**没有 `condition`**，判别字段是 `fetchType="IDS"`
      把 ID 放进顶层 `value: {type:"SelectParam", selectParam:{...BIGINTEGER 字段引用}}`。
      用 cond_field 走条件查询时 fetchType 保持 CONDITION。

    id_value 传 ID 引用（SelectParam），cond_field/right_value 走条件查询。
    二者择一：传了 id_value 即 ID 查询，忽略 cond_field。
    """
    node = builder.build("RETRIEVE", caption=caption)
    node["app"] = builder._app_ref()
    node["structure"] = entity_structure(entity)
    node["title"] = entity["caption"] + "_1"
    node["output"] = _entity_output(entity, node["nodeId"])
    node["nullHandling"] = null_handling
    if null_handling == "TERMINATION":
        # 仅 TERMINATION 时需要提示文案（前端 textarea 必填）
        node["nullPromptMessage"] = null_message or "未查询到数据"

    if id_value is not None:
        node["fetchType"] = "IDS"
        node["value"] = id_value
        node["condition"] = []
        return node

    node["fetchType"] = "CONDITION"
    if cond_field:
        node["condition"] = [condition_group(entity, cond_field, right_value)]
    else:
        # cond_field 为空 = 先占位（调用方随后改写成 IDS 形态并覆盖 condition）
        node["condition"] = []
    node["sortParams"] = []
    return node


def retrieve_by_id(builder: NodeBuilder, entity: dict[str, Any],
                   id_ref: dict[str, Any], caption: str = "查询单条数据",
                   null_handling: str = "CONTINUE") -> dict[str, Any]:
    """按 ID 查单条的便捷入口（246 次真实用法的形态）。id_ref 是 ID 字段的 SelectParam。"""
    return retrieve(builder, entity, "", None, caption=caption,
                    id_value=id_ref, null_handling=null_handling)


def retrieve_array(builder: NodeBuilder, entity: dict[str, Any], cond_field: str,
                   right_value: dict[str, Any], caption: str = "查询多条数据",
                   page_info_node: dict[str, Any] | None = None,
                   fetch_type: str = "CONDITION",
                   ids_node: dict[str, Any] | None = None,
                   sort_params: list | None = None) -> dict[str, Any]:
    """查询多条数据。

    fetchType 三种真实形态（217 条语料）：
      CONDITION 184 → 条件查询；COUNT 13 → 只返总数（OBJECT/INTEGER）；
      IDS 19 → 按 id 列表查（value=ARRAY<BIGINTEGER> 的 SelectParam，**没有 condition**）。
    """
    node = builder.build("RETRIEVE_ARRAY", caption=caption)
    node["app"] = builder._app_ref()
    node["structure"] = entity_structure(entity)
    node["output"] = _entity_output(entity, node["nodeId"], is_array=True)
    if cond_field:
        node["condition"] = [condition_group(entity, cond_field, right_value)]
    else:
        node["condition"] = []   # 占位：调用方随后写组合条件
    node["sortParams"] = sort_params or []
    node["nullHandling"] = "CONTINUE"
    if fetch_type and fetch_type != "CONDITION":
        node["fetchType"] = fetch_type
    if fetch_type == "COUNT":
        # 只返总数：OBJECT/INTEGER，不是列表
        node["output"] = {"id": None, "javaType": "java.lang.Integer", "dataType": "INTEGER",
                          "type": "OBJECT", "desc": "总数", "dtoType": None, "udcApp": None,
                          "appName": None, "name": "_" + node["nodeId"]}
    elif fetch_type == "IDS":
        # 按 id 列表查：value 指向 ARRAY<BIGINTEGER> 出参，condition 必须为空
        node.pop("condition", None)
        src = ids_node or {}
        so = src.get("output") or {}
        on = builder.output_name(src)
        node["value"] = {"type": "SelectParam", "selectParam": {
            "description": src.get("caption") or "", "name": on,
            "dataType": so.get("dataType") or "BIGINTEGER",
            "type": so.get("type") or "ARRAY",
            "desc": src.get("caption") or "", "javaType": so.get("javaType") or "java.lang.Long",
            "position": "parent", "outputName": on,
            "nodeInfo": {"nodeId": src.get("nodeId"), "type": "ACTIVITY",
                         "actionType": src.get("actionType")},
            "key": "%s_%s" % (on, on), "disabled": False, "isLeaf": True}}
    if page_info_node is not None:
        node["pageSearch"] = "true"
        node["pageInfo"] = {
            "type": "SelectParam", "selectParam": {
                "outputName": builder.output_name(page_info_node),
                "type": "OBJECT", "dataType": "DTO", "dtoType": "CUSTOM",
                "udcApp": True, "appName": builder.app_name,
                "javaType": "com.seeyon.boot.transport.PageInfo",
                "desc": "分页参数对象",
                "path": "comseeyonboottransportPageInfo",
                "id": "com.seeyon.boot.transport.PageInfo",
                "javaType": "com.seeyon.boot.transport.PageInfo",
                "name": "comseeyonboottransportPageInfo", "position": "parent",
                "description": "分页参数对象",
            },
        }
    return node


def create_entity(builder: NodeBuilder, entity: dict[str, Any],
                  field_values: list[tuple[str, dict[str, Any]]],
                  caption: str = "插入数据") -> dict[str, Any]:
    """field_values: [(字段名, value对象), ...]"""
    node = builder.build("CREATE_ENTITY", caption=caption)
    node["app"] = builder._app_ref()
    node["structure"] = entity_structure(entity)
    node["title"] = entity["caption"]
    node["output"] = _write_output("CREATE_ENTITY", node["nodeId"])
    # ★ mappingType 不能去：契约统计 32 个真实样本 100% 都有（MUST 级）。
    #   2026-11-01 曾假设它是模板残留而 pop 掉，被组装闸门拦回——推断错误。
    node["mappingType"] = "attrs"
    proto = node["attrs"][0]["attrType"]  # 模板里的 attrType 骨架
    built = []
    for order, (fname, value) in enumerate(field_values):
        at = dict(proto)  # 保留模板骨架键
        at.update(field_attr(entity, fname, sort=order))
        # ★★ customs 必须按字段重写，不能沿用模板骨架。
        #   field_attr 不含 customs，dict(proto) 会把模板字段（f01text）的
        #   customs 原样带给每个字段：name=f01text、dataType=STRING、id=<f01text的id>。
        #   平台编译时按 customs.dataType 做类型转换，数值字段（INTEGER/DECIMAL）
        #   按 STRING 转不过去就被丢弃，INSERT 落到实体默认值——
        #   表现为 publish/build/UI 全绿而运行时字段值不生效（P5 唯一阻塞项）。
        #   实体属性自带的 customs 与真实样本逐字段一致
        #   （f03int: id=-6040618203145140416, dataType=INTEGER），直接用。
        f = entity["attributes"][fname]
        if f.get("customs"):
            at["customs"] = dict(f["customs"])
        else:
            cu = dict(at.get("customs") or {})
            cu.update({"dataType": f["dataType"], "name": fname, "id": f["id"]})
            at["customs"] = cu
        built.append({"attrType": at, "value": value})
    node["attrs"] = built
    return node


def change_entity(builder: NodeBuilder, entity: dict[str, Any],
                  src_node: dict[str, Any],
                  field_values: list[tuple[str, dict[str, Any]]],
                  caption: str = "更新数据") -> dict[str, Any]:
    """更新数据：selectParam 引用前序实体，attrs 是字段赋值。"""
    node = builder.build("CHANGE_ENTITY", caption=caption)
    src_name = builder.output_name(src_node)
    # ★ 2026-10-31：真实 selectParam 22 键。缺 key/relationEntityFullName 时设计器
    # 「更新数据 → 选择更新的数据」下拉显示空白（黄框），发布与 checkSchema 全绿。
    node["selectParam"] = {
        "id": entity["fullName"], "javaType": entity["fullName"], "dataType": "DTO",
        "type": "OBJECT", "desc": src_node.get("title") or entity["caption"],
        "dtoType": "MASTER_ENTITY", "udcApp": True, "name": src_name,
        "outputName": src_name, "position": "parent",
        "relationEntity": entity["relationEntityId"], "appName": entity.get("refApp"),
        "key": src_name + entity["fullName"],
        "path": str(entity["fullName"]).replace(".", ""),
        "relationEntityFullName": entity.get("entityFullName")
        or str(entity["fullName"]).replace(".dto.", ".domain.entity.").replace("Dto", ""),
        "description": src_node.get("title") or entity["caption"],
        "disabled": False, "isLeaf": True, "parentLabel": entity["caption"],
        "iconKey": "entity",
        "nodeInfo": {"nodeId": src_node["nodeId"], "type": "ACTIVITY",
                     "actionType": src_node.get("actionType")},
    }
    node["title"] = entity["caption"]
    node["output"] = _write_output("CHANGE_ENTITY", node["nodeId"])
    built = []
    for order, (fname, value) in enumerate(field_values):
        built.append({"attrType": field_attr(entity, fname, sort=order), "value": value})
    node["attrs"] = built
    return node


def delete_entity_by_param(builder: NodeBuilder, entity: dict[str, Any],
                           select_param: dict[str, Any],
                           caption: str = "删除数据") -> dict[str, Any]:
    """删除指定记录（deleteType=SELECT_PARAM）。

    ★ 这是「按动态 ID 删除」的唯一可用路径（2026-11-02 实测）：
      CONDITION 模式的右值填 SelectParam 引用 → publish 被拒 BOOT_1001
      Parameter Error，响应无字段级提示，极难定位。SELECT_PARAM 模式则正常。

    形态与真实样本一致：只有 deleteType/title/selectParam，
    **不带** app / structure / condition / methodLegal（那是 CONDITION 模式才有的）。
    select_param 由调用方给（composer 的 _out_ref 产出），引用前序 DTO 出参。
    """
    node = builder.build("DELETE_ENTITY", caption=caption)
    node["deleteType"] = "SELECT_PARAM"
    node["selectParam"] = dict(select_param)
    node["title"] = entity["caption"]
    node["output"] = _write_output("DELETE_ENTITY", node["nodeId"])
    for k in ("app", "structure", "condition", "methodLegal"):
        node.pop(k, None)
    return node


def delete_entity(builder: NodeBuilder, entity: dict[str, Any], cond_field: str,
                  right_value: dict[str, Any], caption: str = "删除数据") -> dict[str, Any]:
    node = builder.build("DELETE_ENTITY", caption=caption)
    node["app"] = builder._app_ref()
    node["structure"] = entity_structure(entity)
    node["title"] = entity["caption"]
    node["output"] = _write_output("DELETE_ENTITY", node["nodeId"])
    node["condition"] = [condition_group(entity, cond_field, right_value)]
    return node


# --------------------------------------------------------------------------
# 变量活动
# --------------------------------------------------------------------------
_JAVA = {"STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
         "BIGINTEGER": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
         "DECIMAL": "java.math.BigDecimal", "DATETIME": "java.util.Date"}


def _to_mapping_select_param(sp: dict[str, Any]) -> dict[str, Any]:
    """attrs 用的 selectParam → mapping 行用的 selectParam。

    ★★ 两种场景键集不同（语料 2392 个 mapping 样本 100% 覆盖）：

       mapping[].value.selectParam 必带：
         key name id description position path outputName dataType type
         javaType dtoType appName udcApp multiSelect customs parentLabel
       attrs[].value.selectParam 反而**没有** nodeInfo 之外的差异，但有
         nodeInfo/iconKey/title/generics/disabled 这些 UI 键。

    平台对 mapping 行校验更严：
       - 缺 dtoType → PROPERTY_IS_REQUIRED ...mapping.value.selectParam.dtoType
       - value.type 写成 OBJECT → DATA_INVALID（必须 SelectParam）
    dtoType 取值：CUSTOM(2187) 配 udcApp=False，SUB_ENTITY(204) 配 udcApp=True。
    """
    keep = ("key", "name", "id", "description", "position", "path", "outputName",
            "dataType", "type", "javaType", "dtoType", "appName", "udcApp",
            "multiSelect", "customs", "parentLabel", "relationEntity",
            "relationType", "relationApp", "refId", "refApp", "refType", "enums")
    out = {k: sp[k] for k in keep if k in sp}
    out.setdefault("type", "OBJECT")
    out.setdefault("dtoType", "CUSTOM")
    out.setdefault("udcApp", out.get("dtoType") == "SUB_ENTITY")
    out.setdefault("multiSelect", False)
    out.setdefault("customs", {"basicType": False, "mfDataI18n": False,
                               "defaultOrExpression": False, "notNull": False})
    out.setdefault("parentLabel", "")
    out.setdefault("appName", sp.get("appName") or "")
    # ★ UI 键不能带进 mapping（语料里一个都没有）
    for k in ("nodeInfo", "iconKey", "title", "generics", "disabled",
              "hasPagination", "relationEntityFullName"):
        out.pop(k, None)
    return out


def create_variable(builder: NodeBuilder, title: str, data_type: str = "STRING",
                    value: dict[str, Any] | None = None,
                    caption: str = "创建变量",
                    entity: dict[str, Any] | None = None,
                    default_object: dict[str, Any] | None = None,
                    other_type: str | None = None,
                    attrs: list | None = None,
                    value_ref: dict[str, Any] | None = None,
                    auto_map_from: dict[str, Any] | None = None) -> dict[str, Any]:
    """创建变量。四种真实形态（实测 429 BASIC / 177 ENTITY_OBJECT / 75 DEFAULT_OBJECT / 31 OTHER）：

    | paramType | 判别载荷 | 恒有键 | 业务含义 |
    |---|---|---|---|
    | `BASIC` | `value` | value/dataType/output | 基本类型变量 |
    | `ENTITY_OBJECT` | `structure`+`app`+`mappingType` | 无 value，有 attrs | 存一条实体 |
    | `DEFAULT_OBJECT` | `structure`+`app`+`mappingType` | 同上 | 存自定义 DTO |
    | `OTHER` | `otherType`+`structure` | 无 app | 系统对象（页面分页等） |

    ★ 关键差异：非 BASIC 型**没有 `value` 键**，值是走 `attrs[].value`。
      给实体型塞 value 会让抽屉里「默认值」和字段映射打架。

    赋值方式三形态（矩阵 node-settings-capability.json → mappingType）：
    - attrs（字段映射）：attrs=[]，默认
    - value（对象引用，语料 36 条）：value_ref=完整 selectParam 引用前序 DTO 对象，恒无 attrs
    - mapping（自动映射，语料 35 条）：auto_map_from=源对象，同名配对生成 mapping[]
      mapping 行 = {attrType: 字段元数据, value: {desc, type, selectParam}}

    - entity 传实体模型（走 LiveRefs.entity_model）→ ENTITY_OBJECT
    - default_object 传自定义 DTO 的 structure → DEFAULT_OBJECT
    - other_type 传 SYSTEM_PAGE_INFO → OTHER（PageInfo 分页对象）
    """
    value = _as_slot(value)
    node = builder.build("CREATE_VARIABLE", caption=caption)
    node["title"] = title

    if entity is not None:
        node["paramType"] = "ENTITY_OBJECT"
        node["dataType"] = "DTO"
        node["app"] = builder._app_ref()
        node["structure"] = entity_structure(entity)
        out = _entity_output(entity, node["nodeId"])
        out["desc"] = title
        node["output"] = out
        if value_ref is not None:
            # 对象引用形态（mappingType=value，语料 36/36 恒无 attrs 键——键都不能有）
            node["mappingType"] = "value"
            node["value"] = {"type": "SelectParam", "selectParam": value_ref}
            node.pop("attrs", None)
        elif auto_map_from is not None:
            # 自动映射形态（mappingType=mapping，语料 35 条）：同名配对
            node["mappingType"] = "mapping"
            node["selectParam"] = auto_map_from["selectParam"]
            node.pop("attrs", None)   # 语料 mapping 形态无 attrs 键（attrs=None 也不行）
            ameta = entity.get("attributes") or {}
            rows = []
            for fname, sp in (auto_map_from.get("fields") or {}).items():
                if fname not in ameta:
                    raise ValueError("自动映射字段 %r 不在实体属性表（可用：%s）"
                                     % (fname, sorted(ameta)[:10]))
                rows.append({"attrType": field_attr({"attributes": ameta}, fname, len(rows)),
                             # 语料裁决：mapping 行 value.type 恒 SelectParam（2392/2392）
                             "value": {"type": "SelectParam", "desc": "%s [%s]" % (ameta[fname].get("desc") or fname, ameta[fname].get("dataType") or ""),
                                       "selectParam": _to_mapping_select_param(sp)}})
            node["mapping"] = rows
        else:
            node["mappingType"] = "attrs"
            node["attrs"] = attrs or []
        return node

    if default_object is not None:
        node["paramType"] = "DEFAULT_OBJECT"
        node["dataType"] = "DTO"
        node["app"] = builder._app_ref()
        node["structure"] = default_object
        node["mappingType"] = "attrs"
        node["attrs"] = attrs or []
        dto = default_object.get("fullName") or default_object.get("id")
        node["output"] = {
            "id": dto, "javaType": dto, "dataType": "DTO", "type": "OBJECT",
            "desc": title, "appName": builder.app_name,
            "dtoType": "CUSTOM", "udcApp": True, "name": "_" + node["nodeId"],
        }
        return node

    if other_type is not None:
        node["paramType"] = "OTHER"
        node["otherType"] = other_type
        node["dataType"] = "DTO"
        node["mappingType"] = "attrs"
        node["attrs"] = attrs or []
        if other_type == "SYSTEM_PAGE_INFO":
            pi = "com.seeyon.boot.transport.PageInfo"
            node["structure"] = {"dataType": "DTO", "dtoId": None, "dtoType": "CUSTOM",
                                 "fullName": pi, "id": pi,
                                 "label": "分页对象", "value": pi}
            node["output"] = {"id": pi, "javaType": pi, "dataType": "DTO",
                              "type": "OBJECT", "desc": title,
                              "appName": builder.app_name, "dtoType": "CUSTOM",
                              "udcApp": True, "name": "_" + node["nodeId"]}
            return node
        raise ValueError("未知 otherType=%r（真实样本只见过 SYSTEM_PAGE_INFO）" % other_type)

    # BASIC
    # 矩阵（node-settings-capability.json → CREATE_VARIABLE）：
    #   - BASIC 无 mappingType（模式由 value 形态表达：Simple=常量/SelectParam=引用/Expression=表达式）
    #   - value=SelectParam 引用：语料 25/25 带 selectParam.path（DTO去点.字段）；23/25 带 customs
    if value is None:
        raise ValueError("BASIC 型创建变量必须给 value（真实 429 个样本恒有 value）")
    node["paramType"] = "BASIC"
    node["dataType"] = data_type
    node["mappingType"] = None
    node["attrs"] = None
    # ★ 语料 429/429 BASIC 的 structure 恒 None：模板基座带的是
    #   com.seeyon.boot.transport.PageInfo（系统分页对象），留着会让
    #   表达式引用解析把变量当成 PageInfo 实体去查（查不到 → G7 误杀）。
    node["structure"] = None
    if isinstance(value, dict) and value.get("type") == "SelectParam":
        sp = value.setdefault("selectParam", {})
        if not sp.get("path"):
            _id = sp.get("id") or ""
            if _id and "." in _id:
                # path = DTO 全名去点 + ".字段"（语料 25/25 形态）
                sp["path"] = _id[:_id.rfind(".")].replace(".", "") + _id[_id.rfind("."):]
    node["value"] = value
    node["output"] = {
        "id": "", "javaType": _JAVA.get(data_type, "java.lang.String"),
        "dataType": data_type, "type": "OBJECT", "desc": title,
        "dtoType": "", "name": "_" + node["nodeId"],
    }
    return node


def change_variable(builder: NodeBuilder, src_node: dict[str, Any],
                    value: dict[str, Any] | None = None,
                    caption: str = "修改变量",
                    field_values: dict[str, dict] | None = None,
                    entity_model: dict[str, Any] | None = None) -> dict[str, Any]:
    """修改变量。两种真实形态（实测 717 value / 335 attrs）：

    | 形态 | mappingType | 载荷 | 业务含义 |
    |---|---|---|---|
    | 整体赋值 | 无（None/缺） | `value{}` | 把整个变量改成新值 |
    | 字段级映射 | `attrs` | `attrs[{attrType,value}]` | 只改实体的某几个字段 |

    ★ 字段级映射（335 次）**没有 `value` 键**，`selectParam` 指向**实体变量（DTO）**，
      每个 `attrs[]` 是 `{attrType: 字段元数据, value: 新值}`。
      这是「更新实体变量的某字段」这个业务动作，和「整体赋值」是两件事。

    field_values: {字段名: 值}，走 attrs 形态。
    entity_model: 实体模型（LiveRefs.entity_model 的产物，含 attributes），
                  attrs 形态必传 —— structure 里没有字段元数据，只有实体标识。
    """
    value = _as_slot(value)
    node = builder.build("CHANGE_VARIABLE", caption=caption)
    src_name = builder.output_name(src_node)
    src_title = src_node.get("title") or ""
    out = src_node.get("output") or {}
    src_type = out.get("dataType", "STRING")
    ent = src_node.get("structure") or {}

    node["selectParam"] = {
        "id": out.get("id"), "javaType": out.get("javaType"),
        "dataType": src_type, "type": "OBJECT", "desc": src_title,
        "name": src_name, "outputName": src_name, "position": "parent",
        "description": src_title,
        "appName": out.get("appName"), "dtoType": out.get("dtoType"),
        "udcApp": out.get("udcApp"),
        "nodeInfo": {"nodeId": src_node["nodeId"], "type": "ACTIVITY",
                     "actionType": src_node.get("actionType")},
    }

    if field_values:
        # 字段级映射形态：selectParam 指向实体，改哪几个字段由 attrs 决定
        if src_type != "DTO":
            raise ValueError("字段级映射需要 selectParam 指向实体变量（DTO），"
                             "实际 dataType=%r" % src_type)
        if not entity_model or not entity_model.get("attributes"):
            raise ValueError("attrs 形态必须传 entity_model（含 attributes），"
                             "structure 里没有字段元数据")
        attrs_meta = entity_model["attributes"]
        attrs = []
        for i, (fname, val) in enumerate(field_values.items()):
            if fname not in attrs_meta:
                raise ValueError("字段 %r 不在该实体的属性表里（可用：%s）"
                                 % (fname, sorted(attrs_meta)[:10]))
            attrs.append({"attrType": field_attr({"attributes": attrs_meta}, fname, i),
                          "value": val if isinstance(val, dict) else simple(val)})
        node["mappingType"] = "attrs"
        node["attrs"] = attrs
        return node

    if value is None:
        raise ValueError("整体赋值形态必须给 value（真实 717 个样本恒有 value）")
    node["mappingType"] = None
    node["attrs"] = None
    node["value"] = value
    return node

def loop_item_field_ref(entity: dict[str, Any], fname: str, fe_output_name: str,
                        position: str = "children") -> dict[str, Any]:
    """引用「列表循环」循环项的某个字段（真实形态，样例 8146471602492 hetonghao）。

    ★ key = 循环出参名 + DTO全名 + "." + 字段名（**DTO 带点**），
      path = DTO全名去点 + "." + 字段名，dtoType=CUSTOM，udcApp=false，
      customs 直接沿用该属性的真实 customs 块。
    """
    f = entity["attributes"][fname]
    dto = entity["fullName"]
    return {
        "description": f.get("caption"),
        "key": fe_output_name + dto + "." + fname,
        "name": fname,
        "id": f["id"],
        "appName": entity.get("refApp"),
        "position": position,
        "path": dto.replace(".", "") + "." + fname,
        "outputName": fe_output_name,
        "dataType": f["dataType"],
        "type": "OBJECT",
        "javaType": f["javaType"],
        "dtoType": "CUSTOM",
        "udcApp": False,
        "multiSelect": False,
        "customs": dict(f.get("customs") or {}),
    }


def loop_item_ref(entity: dict[str, Any], fe_output_name: str) -> dict[str, Any]:
    """引用「列表循环」循环项整体（DTO 对象）。真实形态 101 例（全部出现在 CHANGE_VARIABLE）。

    ★ key = 循环出参名 + DTO全名（**DTO 带点**），dtoType=SUB_ENTITY。
    ⚠ 只能用于 CHANGE_VARIABLE/CREATE_VARIABLE 赋值；
      写操作节点（CHANGE_ENTITY 等）直引循环项会生成 int→DTO 代码并编译失败（实测）。
    """
    dto = entity["fullName"]
    return {
        "id": dto, "javaType": dto, "dataType": "DTO", "type": "OBJECT",
        "desc": entity["caption"], "dtoType": "SUB_ENTITY", "udcApp": True,
        "appName": entity.get("refApp"), "name": dto.replace(".", ""),
        "key": fe_output_name + dto, "path": dto.replace(".", ""),
        "outputName": fe_output_name, "position": "parent",
        "relationEntity": entity.get("relationEntityId"),
    }


def event_info_param(trigger: dict[str, Any], entity: dict[str, Any]) -> dict[str, Any]:
    """事件监听 → 更新数据：selectParam 严格照抄真实语料（AfterCreateEvent 唯一 1 例）。

    真实 19 键，注意三个坑：
      - position = "children"（不是 parent）
      - id = <appName>.<eventFullName>.info，path 为去点号同串
      - 不带 relationEntity / nodeInfo / relationEntityFullName —— 带上反而让设计器
        判成「所选"X"已变更」，下拉只剩占位「请选择类型为实体的数据」
    """
    out = trigger.get("output") or {}
    mi = trigger.get("messageInfo") or {}
    ev_name = out.get("name") or ""
    dto = mi.get("eventMfCustomDtoName") or ""
    full = "%s.info" % dto
    desc = out.get("desc") or "事件对象"
    return {
        "description": desc,
        "key": ev_name + entity["fullName"] + "info",
        "name": "info",
        "id": full,
        "appName": entity.get("refApp"),
        "position": "children",
        "path": full.replace(".", ""),
        "outputName": ev_name,
        "dataType": "DTO",
        "type": "OBJECT",
        "javaType": entity["fullName"],
        "dtoType": "MASTER_ENTITY",
        "udcApp": True,
        "multiSelect": False,
        "customs": {"basicType": False},
        "disabled": False,
        "isLeaf": True,
        "iconKey": "LinedCheckCircle",
        "parentLabel": "",
    }


def change_entity_from_event(builder: NodeBuilder, entity: dict[str, Any],
                             trigger: dict[str, Any],
                             field_values: list[tuple[str, dict[str, Any]]],
                             caption: str = "更新数据") -> dict[str, Any]:
    """事件监听直接更新数据（selectParam = 事件.info）。"""
    node = builder.build("CHANGE_ENTITY", caption=caption)
    node["selectParam"] = event_info_param(trigger, entity)
    node["title"] = entity["caption"]
    node["output"] = _write_output("CHANGE_ENTITY", node["nodeId"])
    node["attrs"] = [{"attrType": field_attr(entity, f, sort=i), "value": v}
                     for i, (f, v) in enumerate(field_values)]
    return node


def _as_slot(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """值槽归一：表达式引擎产物 {title, schema} 自动包装成平台形态。

    ★ 表达式引擎（expression_model.build_remote）返回 {title, schema}；
    平台值槽要求 {"type":"Expression","expression":{title,schema},"desc":...}。
    在构造器入口统一归一，避免每个调用点各包一遍（重复实现是漂移之源）。
    """
    if not isinstance(value, dict):
        return value
    if value.get("type") in ("Simple", "SelectParam", "Expression"):
        return value
    if "schema" in value and "title" in value:
        from ..udc.microflow.expression_model import to_value_slot
        return to_value_slot(value)
    return value


# ---------------------------------------------------------------------------
# CONVERT_DATA 类型转换（语料 214 条全归类，2026-10-31）
# convertType 本身编码目标形态：{desc, value, dataType=目标 dataType, type=目标 type}
_CONVERT_TABLE = {
    # value: (desc, 源形态(type,dataType), 目标(type,dataType,javaType), regex 必带?)
    "Split": ("指定符号拆分文本", ("OBJECT", "STRING"),
              ("ARRAY", "STRING", "java.lang.String"), True),
    "multiAssociation2List": ("多选数据拆分为长整数列表", ("OBJECT", "ENTITY"),
                              ("ARRAY", "BIGINTEGER", "java.lang.Long"), False),
    "List2multiAssociation": ("长整数列表拼接为多选数据", ("ARRAY", "BIGINTEGER"),
                              ("OBJECT", "STRING", "java.lang.String"), False),
    "String2Long": ("文本转长整数【ID】", ("OBJECT", "STRING"),
                    ("OBJECT", "BIGINTEGER", "java.lang.Long"), False),
    "BasicData2String": ("基础类型转文本", ("OBJECT", None),
                         ("OBJECT", "STRING", "java.lang.String"), False),
}
REGEX_ENUM = ("COMMA", "DIVLINE", "SLASH", "PERIOD", "MIDLINE")  # 语料 4 值+模板 MIDLINE


def convert_data(builder: NodeBuilder, src_ref: dict[str, Any], kind: str,
                 caption: str = "类型转换", regex: str | None = None) -> dict[str, Any]:
    """类型转换节点。src_ref 是字段级引用 selectParam（真实形态 22 键，同 CHANGE_ENTITY 口径），
    引用上游 outputName 由 G31 校验。kind 必须在 _CONVERT_TABLE。"""
    if kind not in _CONVERT_TABLE:
        raise ValueError("未知转换 %r（语料只见 %s）" % (kind, sorted(_CONVERT_TABLE)))
    desc, src_shape, out_shape, need_regex = _CONVERT_TABLE[kind]
    if need_regex:
        if regex not in REGEX_ENUM:
            raise ValueError("Split 必须带 regex（枚举 %s）" % (REGEX_ENUM,))
    elif regex is not None:
        raise ValueError("%s 语料恒无 regex" % kind)
    # 源形态校验（静态归类裁决）
    st, sd = src_shape
    if st is not None and src_ref.get("type") != st:
        raise ValueError("%s 源 selectParam.type 应为 %s，得到 %r"
                         % (kind, st, src_ref.get("type")))
    if sd is not None and src_ref.get("dataType") != sd:
        raise ValueError("%s 源 selectParam.dataType 应为 %s，得到 %r"
                         % (kind, sd, src_ref.get("dataType")))
    ot, od, oj = out_shape
    node = builder.build("CONVERT_DATA", caption=caption)
    node["convertType"] = {"desc": desc, "value": kind, "dataType": od, "type": ot}
    node["selectParam"] = src_ref
    node["output"] = {"id": None, "javaType": oj, "dataType": od, "type": ot,
                      "desc": desc.replace("指定符号", "").replace("指定", "") or kind,
                      "name": "_" + node["nodeId"]}
    if need_regex:
        node["regex"] = regex
    else:
        node.pop("regex", None)
    node["title"] = node.get("caption")
    return node


# ---------------------------------------------------------------------------
# CALL_DATA_FLOW 执行生单规则（语料 1 条 + dataflow-api.md 链路，2026-10-31）
# output 恒平台固定 CallDataFlowResultDto；outputName 就是标准 output.name
#（无单独字段——历史疑问就此关闭）。
def call_data_flow(builder: NodeBuilder, entity: dict[str, Any],
                   data_flow: dict[str, Any], cond_field: str,
                   right_value: dict[str, Any] | None = None,
                   caption: str = "执行生单规则") -> dict[str, Any]:
    """执行生单规则。data_flow 来自 LiveRefs.data_flow_candidates(app_id, source_entity_id)；
    condition 与 RETRIEVE 同构。"""
    for k in ("id", "name", "appId", "appUrl", "sourceEntityId"):
        if not data_flow.get(k):
            raise ValueError("data_flow 缺 %s（必须来自 udcDataFlowListManuallyMappingPost）" % k)
    if not data_flow.get("title"):
        data_flow["title"] = data_flow["caption"]   # 接口行无 title 字段，用 caption
    node = builder.build("CALL_DATA_FLOW", caption=caption)
    node["dataSourceType"] = "CONDITION"          # 语料 1 条；选择数据形态无样本
    node["dataFlow"] = {"id": data_flow["id"], "key": data_flow["id"],
                        "value": data_flow["id"], "title": data_flow["title"],
                        "appId": data_flow["appId"], "appUrl": data_flow["appUrl"],
                        "caption": data_flow["caption"], "name": data_flow["name"],
                        "sourceEntityId": data_flow["sourceEntityId"],
                        "g_l_index": "1"}
    node["dataFlowMappingId"] = data_flow["id"]
    node["structure"] = {"caption": entity["caption"], "dataType": "DTO", "type": "OBJECT",
                         "entity": entity["entity"], "entityId": entity["relationEntityId"],
                         "id": entity["fullName"], "dtoType": "MASTER_ENTITY",
                         "udcApp": True, "appName": entity["refApp"]}
    node["condition"] = [condition_group(entity, cond_field, right_value)]
    node["output"] = {"id": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                      "javaType": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                      "dataType": "DTO", "type": "OBJECT", "udcApp": True,
                      "dtoType": "CUSTOM", "desc": node.get("caption"),
                      "appName": entity["refApp"], "name": "_" + node["nodeId"]}
    node["title"] = data_flow["title"] + "的结果_1"
    return node


def break_node(builder: NodeBuilder, caption: str = "跳出循环") -> dict[str, Any]:
    """跳出循环（BREAK）。只放 FOR / FOR_EACH / FOR_COUNT 的 body 内。

    ★★ `type` 必须是 "BREAK"，不能是 "ACTIVITY"（2026-11-02 实测 + 字节码双证）：

    解析器 `MicroFlowParser.node()` 用 `MicroFlowNodeTypeEnum.valueOf(type.toUpperCase())`
    选解析器。枚举只有 CONDITION/FOR_EACH/BRANCH/CUSTOM_ERROR/END/ACTIVITY/FOR/BREAK。
    `type="ACTIVITY"` 会被当成普通 Activity：
      - `ActivityNodeTypeEnum` 里**没有** BREAK（0 处），activityNodeType 为 null
      - 代码生成模板 `MicroFlowDomainService.java.ftl` 按 `node.type` 分发，
        BREAK 的 case 是 `<#case "Break">` → `break;`；Activity 分支里**没有** BREAK case
    结果：节点被静默丢弃——构建 SUCCESS、publish 通过、运行 success=true，
    但循环**照跑 N 次**（实测 3/3，对照也是 3/3）。全程零报错，最难查的那种。

    闸门 G38 拦这个错法。
    """
    node = builder.build("BREAK", caption=caption)
    node["type"] = "BREAK"
    node["output"] = None
    return node

PAGE_INFO_ID = "com.seeyon.boot.transport.PageInfo"


def create_variable_page_info(builder: NodeBuilder, page_number: int = 1,
                              page_size: int = 20, need_total: bool = True,
                              caption: str = "分页参数") -> dict[str, Any]:
    """造分页参数对象（CREATE_VARIABLE + paramType=OTHER/otherType=SYSTEM_PAGE_INFO）。

    真实形态（44 条 pageSearch=true 样本）：
      paramType=OTHER  otherType=SYSTEM_PAGE_INFO  dataType=DTO  mappingType=attrs
      attrs = [pageNumber, pageSize, needTotal]，每个 value 是 Simple 常量
      output.id/javaType = com.seeyon.boot.transport.PageInfo（平台内建类）
    """
    node = builder.build("CREATE_VARIABLE", caption=caption)
    node["paramType"] = "OTHER"
    node["otherType"] = "SYSTEM_PAGE_INFO"
    node["mappingType"] = "attrs"
    node["dataType"] = "DTO"
    node["title"] = "分页参数对象"
    node["structure"] = {"dataType": "DTO", "dtoId": None, "dtoType": "CUSTOM",
                         "fullName": PAGE_INFO_ID, "id": PAGE_INFO_ID, "key": PAGE_INFO_ID,
                         "value": PAGE_INFO_ID, "label": "分页对象", "udcApp": True}
    node["output"] = {"id": PAGE_INFO_ID, "javaType": PAGE_INFO_ID, "dataType": "DTO",
                      "type": "OBJECT", "desc": "分页参数对象",
                      "dtoType": "CUSTOM", "udcApp": True,
                      "appName": builder.app_name, "name": "CREATE_VARIABLE_" + node["nodeId"][-6:]}

    def _attr(name, jt, dt, desc_, val):
        return {"attrType": {"name": name, "id": PAGE_INFO_ID + "." + name,
                             "fullName": PAGE_INFO_ID + "." + name, "javaType": jt,
                             "dataType": dt, "type": "OBJECT", "desc": desc_,
                             "relationApp": "udc", "refApp": "udc", "multiSelect": False,
                             "filterDataType": dt,
                             "filterFullName": PAGE_INFO_ID + "." + name,
                             "filterType": "OBJECT", "dataI18n": False, "sort": 0,
                             "description": ""},
                "value": {"type": "Simple", "simple": val, "desc": val}}

    node["attrs"] = [_attr("pageNumber", "java.lang.Integer", "INTEGER", "当前页数", page_number),
                     _attr("pageSize", "java.lang.Integer", "INTEGER", "每页条数", page_size),
                     _attr("needTotal", "java.lang.Boolean", "BOOLEAN", "需要总数", need_total)]
    return node

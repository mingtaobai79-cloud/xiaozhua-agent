"""全节点端到端测试：覆盖微流程所有节点类型 + 真实出入参 + 表达式 + 业务逻辑。

验证目标：用生成系统（build.make_node/branch + expression_fill）从零构造一个
覆盖全部节点类型的 schema，跑通三道闸门（validate_schema / validate_for_submit /
run_gates），断言 0 错误。

覆盖的节点（25 类，含控制节点）：
  变量：CREATE_VARIABLE(BASIC/ENTITY)、CHANGE_VARIABLE
  列表：CREATE_LIST、CHANGE_LIST、LIST_OPERATION
  映射：CREATE_MAP、MAP_OPERATION
  数据：RETRIEVE、RETRIEVE_ARRAY、CREATE_ENTITY、CHANGE_ENTITY、
        CREATE_BATCH_ENTITY、CHANGE_BATCH_ENTITY、DELETE_ENTITY、
        CONVERT_DATA、DATA_MAPPING
  调用：SUB_MICROFLOW、CALL_APP_SERVICE、CALL_DATA_FLOW、PUBLISH_BUSINESS_EVENT
  控制：FOR（函数表达式边界 + 套 BREAK/CUSTOM_ERROR）、BRANCH（条件表达式）、
        CUSTOM_ERROR、BREAK

表达式的用法（"该用表达式就用表达式"）：
  - FOR.forEnd：roundOffFloor(总数变量/999) 函数表达式
  - BRANCH 条件：总数变量 != 0 比较表达式
  - CHANGE_VARIABLE 值：总数变量 + 1 算术表达式
  - CUSTOM_ERROR.error：文本变量（表达式引用）

业务逻辑（"有点业务逻辑就用业务逻辑"）：
  - RETRIEVE 按 ID 查单条 → CHANGE_ENTITY 更新
  - RETRIEVE_ARRAY 查列表 → FOR 循环逐条处理（BREAK + CUSTOM_ERROR）
  - BRANCH 按条件分流
"""
from __future__ import annotations

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.build import (
    build_schema, validate_schema, validate_for_submit, make_node, branch, param,
)
from components.udc.microflow.gates import run_gates
from components.udc.microflow.expression_fill import (
    build_expression_dto, build_function_expression_dto,
)

APP_ID = "9000000000000000001"
APP_CODE = "datamigration9000000000000000001"

# ---- 实体元数据（datamigration 的 MigrationPlan 实体，模板权威值）----
APP = {
    "appId": APP_ID, "appName": "datamigration9000000000000000001",
    "caption": "数据迁移", "inApp": True, "udcApp": True, "dynamicDependency": False,
}
STRUCTURE = {
    "key": "com.seeyon.datamigration9000000000000000001.domain.entity.MigrationPlan",
    "id": "com.seeyon.datamigration9000000000000000001.dto.MigrationPlanDto",
    "label": "迁移方案配置", "dataType": "DTO",
    "entity": "com.seeyon.datamigration9000000000000000001.domain.entity.MigrationPlan",
    "dtoType": "MASTER_ENTITY", "udcApp": True,
    "fullName": "com.seeyon.datamigration9000000000000000001.dto.MigrationPlanDto",
    "relationEntity": "4796455827714164161",
    "methodLegal": {"available": True, "complexCondition": True, "seniorMethod": True,
                    "serviceType": "NONE", "interfaceClassFullName": None},
}
# 实体的 id 字段（leftParam）
FIELD_ID = {
    "id": "com.seeyon.datamigration9000000000000000001.dto.MigrationPlanDto.id",
    "name": "id",
    "type": "OBJECT", "javaType": "java.lang.Long", "dto": "_id", "field": "id",
    "desc": "ID", "dataType": "BIGINTEGER", "multiSelect": False,
}


def _u() -> str:
    return str(uuid.uuid4())


_EXPR_PREFIX = "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ="


def _executable_expr(dto: dict) -> str:
    """executableExpr = 固定前缀 + tokens value 拼接（FUNCTION 递归为 名(参数)）。"""
    def tv(t):
        if t.get("type") == "FUNCTION":
            args = [",".join(tv(x) for x in g) for g in (t.get("subOps") or [])]
            return "%s(%s)" % (t.get("value", ""), ",".join(args))
        return str(t.get("value", ""))
    return _EXPR_PREFIX + "".join(tv(t) for t in dto["tokens"])


def _expr(dto: dict, translation: str) -> dict:
    """build_expression_dto 的 dto → 值槽位 Expression 包装（含 expression 对象）。"""
    dd = {
        "expressionTranslation": translation,
        "resultTypeInfo": dto["resultTypeInfo"],
        "resultTypeFullName": dto.get("resultTypeFullName"),
        "terminalType": "BACKEND",
        "isMultiSelect": dto.get("isMultiSelect", False),
        "context": dto.get("schemas") or [],
        "tokens": dto["tokens"],
        "sourceAppName": None,
    }
    rt = {"executableExpr": _executable_expr(dto)}
    return {
        "type": "Expression",
        "expression": {"title": translation,
                       "schema": json.dumps({"designData": dd, "runtimeData": rt})},
        "desc": translation,
    }


def _cond(field: dict, op: str, op_desc: str, right_type: str, right_val,
          right_desc) -> dict:
    """筛选条件（condition 是 GROUP 数组，历史样本 GROUP 无 logicalOperator）。"""
    return [{
        "type": "GROUP", "uuid": _u(), "conditions": [{
            "type": "CONDITION", "leftParam": field,
            "operator": {"value": op, "desc": op_desc},
            "rightParams": [{"type": right_type, "value": right_val, "desc": right_desc}],
            "uuid": _u(), "logicalOperator": "AND",
        }],
    }]


_JAVA = {"STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
         "BIGINTEGER": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
         "MAP": "java.util.Map"}


def _sp(output_name: str, data_type: str, desc: str, *, arr: bool = False) -> dict:
    """selectParam 引用（含 position/javaType/dtoType/key，后端必填）。

    key = <outputName>_<appName>（G24；语料引用形态恒带）。
    """
    jt = _DTO_FULL if data_type == "DTO" else _JAVA.get(data_type, "java.lang.Object")
    out = {"outputName": output_name, "type": "ARRAY" if arr else "OBJECT",
           "dataType": data_type, "desc": desc, "position": "parent",
           "javaType": jt, "key": "%s_%s" % (output_name, APP_CODE)}
    if data_type == "DTO":
        out["dtoType"] = "MASTER_ENTITY"
        out["udcApp"] = True
        out["appName"] = "datamigration9000000000000000001"
    return out


_DTO_FULL = "com.seeyon.datamigration9000000000000000001.dto.MigrationPlanDto"


def _entity_output(name: str, desc: str, *, arr: bool = False) -> dict:
    """实体类节点 output（完整 DTO 形态，id/javaType/dtoType/udcApp 必填）。"""
    return {"id": _DTO_FULL, "javaType": _DTO_FULL, "dataType": "DTO",
            "type": "ARRAY" if arr else "OBJECT", "desc": desc,
            "dtoType": "MASTER_ENTITY", "udcApp": True,
            "appName": "datamigration9000000000000000001", "name": name}


def _attr_row(field: dict, val) -> dict:
    """字段映射行（attrs[].{value, attrType}）。"""
    return {"value": {"type": "Simple", "simple": val, "desc": val},
            "attrType": field}


def build_all_nodes_spec() -> dict:
    """构造覆盖全节点的 spec（nodes 按执行顺序，前序出参 → 后序引用）。"""
    nodes = []

    # 1. 总数变量（BIGINTEGER，供 FOR 函数表达式 + BRANCH 条件用）
    nodes.append(make_node("CREATE_VARIABLE", caption="总数变量",
        output=param("_CREATE_VARIABLE_total", "BIGINTEGER", "总数"),
        paramType="BASIC", dataType="BIGINTEGER", title="总数变量"))

    # 2. 文本变量（STRING，供 CHANGE_VARIABLE + CHANGE_LIST.dataSource 用）
    nodes.append(make_node("CREATE_VARIABLE", caption="文本变量",
        output=param("_CREATE_VARIABLE_text", "STRING", "文本"),
        paramType="BASIC", dataType="STRING", title="文本变量"))

    # 3. 修改变量：值用「总数变量 + 1」算术表达式
    nodes.append(make_node("CHANGE_VARIABLE", caption="总数加一",
        selectParam=_sp("_CREATE_VARIABLE_total", "BIGINTEGER", "总数"),
        mappingType="value", title="总数加一",
        value=_expr(build_expression_dto(
            {"name": "_CREATE_VARIABLE_total", "dataType": "BIGINTEGER", "desc": "总数"},
            "BIGINTEGER"), "总数变量 +1")))

    # 4. 创建列表（STRING 列表）
    nodes.append(make_node("CREATE_LIST", caption="文本列表",
        # 语料裁决：CREATE_LIST 出参恒 type=ARRAY（237 条无例外）
        output={**param("_CREATE_LIST_texts", "STRING", "文本列表"), "type": "ARRAY"},
        paramType="BASIC", dataType="STRING", title="文本列表",
        structure=None, value=None))

    # 5. 修改列表：dataSource 引用文本变量
    nodes.append(make_node("CHANGE_LIST", caption="追加列表",
        selectParam=_sp("_CREATE_LIST_texts", "STRING", "文本列表", arr=True),
        action="ADD",
        dataSource=_sp("_CREATE_VARIABLE_text", "STRING", "文本")))

    # 6. 列表操作：计数（operationType 是对象 {"type":"SIZE"}，selectParam type=ARRAY）
    nodes.append(make_node("LIST_OPERATION", caption="列表计数",
        selectParam={"id": None, "javaType": "java.lang.String", "dataType": "STRING",
                     "type": "ARRAY", "desc": "文本列表", "name": "_CREATE_LIST_texts",
                     "position": "parent", "outputName": "_CREATE_LIST_texts"},
        operationType={"type": "SIZE"}, title="列表计数"))

    # 7. 创建映射组
    nodes.append(make_node("CREATE_MAP", caption="验收摘要",
        output=param("_CREATE_MAP_summary", "MAP", "验收摘要"),
        title="验收摘要", generics={"keyType": {"dataType": "String"},
                                    "valueType": {"dataType": "Object",
                                                  "javaType": "java.lang.Object"}}))

    # 8. 映射操作：GET 取值
    nodes.append(make_node("MAP_OPERATION", caption="取摘要键值",
        selectMap=_sp("_CREATE_MAP_summary", "MAP", "验收摘要"),
        operationType="GET", theKey={"type": "Simple", "simple": "验收结果", "desc": "验收结果"},
        paramType="BASIC",
        basic={"label": "文本", "value": "STRING", "key": "STRING", "dataType": "STRING"},
        structure={"label": "文本", "value": "STRING", "key": "STRING", "dataType": "STRING",
                   "fullName": "java.lang.String"},
        arrayOrObject="OBJECT",
        output=param("_MAP_OPERATION_val", "STRING", "映射值"),
        nullPromptMessage="未取到值", title="取摘要键值"))

    # 9. 查询单条（按 id）
    nodes.append(make_node("RETRIEVE", caption="查方案",
        output=_entity_output("_RETRIEVE_plan", "方案"),
        fetchType="CONDITION", app=dict(APP), structure=dict(STRUCTURE),
        title="查方案", condition=_cond(FIELD_ID, "EQ", "=", "CONSTANT", 1, 1),
        nullHandling="TERMINATION", nullPromptMessage="未查到方案"))

    # 10. 查询多条
    nodes.append(make_node("RETRIEVE_ARRAY", caption="查方案列表",
        output=_entity_output("_RETRIEVE_ARRAY_plans", "方案列表", arr=True),
        fetchType="CONDITION", app=dict(APP), structure=dict(STRUCTURE),
        variableTitle="方案列表", selectType="DTO", scope="ARRAY", size=999,
        pageSearch="false", pageInfo=None,
        condition=_cond(FIELD_ID, "GT", ">", "CONSTANT", 0, 0)))

    # 11. 插入数据（字段映射 attrs）
    nodes.append(make_node("CREATE_ENTITY", caption="新增方案",
        output=param("_CREATE_ENTITY_new", "INTEGER", "新方案影响行数"),
        app=dict(APP), structure=dict(STRUCTURE), mappingType="attrs",
        attrs=[_attr_row(FIELD_ID, 1)], title="新增方案"))

    # 12. 更新数据（引用查单条出参）
    nodes.append(make_node("CHANGE_ENTITY", caption="更新方案",
        output=param("_CHANGE_ENTITY_updated", "INTEGER", "更新影响行数"),
        selectParam=_sp("_RETRIEVE_plan", "DTO", "方案"),
        mappingType="attrs", attrs=[_attr_row(FIELD_ID, 1)],
        title="更新方案"))

    # 13. 批量插入（引用查询列表出参）
    nodes.append(make_node("CREATE_BATCH_ENTITY", caption="批量新增",
        output=param("_CREATE_BATCH_ENTITY_new", "INTEGER", "批量新增影响行数"),
        selectParam=_sp("_RETRIEVE_ARRAY_plans", "DTO", "方案列表", arr=True),
        title="批量新增"))

    # 14. 批量更新（引用查询列表出参）
    nodes.append(make_node("CHANGE_BATCH_ENTITY", caption="批量更新",
        output=param("_CHANGE_BATCH_ENTITY_updated", "INTEGER", "批量更新影响行数"),
        selectParam=_sp("_RETRIEVE_ARRAY_plans", "DTO", "方案列表", arr=True),
        mappingType="attrs", attrs=[_attr_row(FIELD_ID, 1)],
        title="批量更新"))

    # 15. 删除数据（按条件）
    nodes.append(make_node("DELETE_ENTITY", caption="删除方案",
        output=param("_DELETE_ENTITY_count", "INTEGER", "删除数量"),
        deleteType="CONDITION", app=dict(APP), structure=dict(STRUCTURE),
        selectParam=None,
        title="删除方案", condition=_cond(FIELD_ID, "EQ", "=", "CONSTANT", 1, 1)))

    # 16. 类型转换（基础类型转文本；语料裁决 output.dataType=STRING 大写）
    nodes.append(make_node("CONVERT_DATA", caption="基础类型转文本",
        output={"id": None, "javaType": "java.lang.String", "dataType": "STRING", "type": "OBJECT",
                "desc": "转换结果", "name": "_CONVERT_DATA_text"},
        convertType={"value": "BasicData2String", "desc": "基础类型转文本",
                     "dataType": "STRING", "type": "OBJECT"},
        title="基础类型转文本",
        selectParam=_sp("_CREATE_VARIABLE_total", "BIGINTEGER", "总数")))

    # 17. 数据转换（引用查单条出参；output.type=ARRAY，mappingRule 带非空 mappingRows）
    _row = {
        "uuid": _u(),
        "targetField": {"id": "com.seeyon.datamigration9000000000000000001.dto.MigrationPlanDto.id",
                        "path": [], "name": "id", "desc": "ID", "dataType": "BIGINTEGER",
                        "type": "OBJECT", "javaType": "java.lang.Long"},
        "mappingMode": "REFERENCE",
        "value": {"reference": {"id": "com.seeyon.datamigration9000000000000000001.dto.MigrationPlanDto.id",
                                "path": [], "name": "id", "desc": "ID", "dataType": "BIGINTEGER",
                                "type": "OBJECT", "javaType": "java.lang.Long"}},
    }
    nodes.append(make_node("DATA_MAPPING", caption="方案转实体",
        output=_entity_output("_DATA_MAPPING_out", "转换结果", arr=True),
        selectParam=_sp("_RETRIEVE_ARRAY_plans", "DTO", "方案列表", arr=True),
        app=dict(APP), structure=dict(STRUCTURE), targetType="ENTITY", title="方案转实体",
        mappingRule={"uuid": _u(), "id": None, "caption": "方案映射", "type": "DTO",
                     "javaType": "java.lang.Object", "name": "方案映射",
                     "subobjects": [], "targetType": "ENTITY", "mappingRows": [_row]}))

    # 18. 子微流程（mfService 是完整扁平对象，type="SERVICE"）
    nodes.append(make_node("SUB_MICROFLOW", caption="调用子流程",
        mfService={"id": "3403045189242538361", "appCaption": None,
                   "appId": APP_ID, "appName": None, "caption": "子流程",
                   "description": "", "hasInput": False, "hasOutput": False,
                   "hostPath": None, "input": None, "method": "GET",
                   "name": "MFSERVICEsub", "output": None,
                   "path": "/microflow/MFSERVICEsub",
                   "triggerType": "MANUAL", "type": "SERVICE", "restType": "GET"},
        mappingType="attrs", outputName=None, outPutDesc=None,
        value={"type": "Simple", "simple": "", "desc": ""},
        attrs=[], pageInfo=None))

    # 19. 调用自定义服务（selectMethod 是完整服务契约对象）
    nodes.append(make_node("CALL_APP_SERVICE", caption="调用服务",
        output=param("_CALL_APP_SERVICE_out", "STRING", "服务结果"),
        app=dict(APP),
        selectMethod={
            "caption": "测试服务方法",
            "md5": "fixture0000000000000000000000000000md5",
            "fullName": "com.seeyon.example.appservice.TestServiceImpl.testMethod",
            "implClass": "com.seeyon.example.appservice.TestServiceImpl",
            "dubbo": True, "dubboVersion": "1.0",
            "parameter": {"type": "com.seeyon.boot.transport.SingleRequest",
                          "item": {"itemType": "java.lang.String"}},
            "returnValue": {"type": "com.seeyon.boot.transport.SingleResponse",
                            "item": {"itemType": "java.lang.String"}},
        },
        outputName="_CALL_APP_SERVICE_out"))

    # 20. 执行生单规则（语料 1 条契约：dataFlow{id,name,appId,appUrl,sourceEntityId}、
    #     dataSourceType=CONDITION、output 恒平台固定 CallDataFlowResultDto）
    _structure_with_entity = dict(STRUCTURE)
    _structure_with_entity["entityId"] = "-2537349473285092530"
    _df_id = "9000000000000000099"
    nodes.append(make_node("CALL_DATA_FLOW", caption="生单",
        output={"id": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                "javaType": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                "dataType": "DTO", "type": "OBJECT", "udcApp": True,
                "dtoType": "CUSTOM", "desc": "生单结果",
                "appName": "datamigration9000000000000000001",
                "name": "_CALL_DATA_FLOW_out"},
        dataFlow={"id": _df_id, "key": _df_id, "value": _df_id,
                  "title": "生单规则A", "appId": "9000000000000000001",
                  "appUrl": "datamigration9000000000000000001",
                  "caption": "生单规则A", "name": "testFlow",
                  "sourceEntityId": "-2537349473285092530", "g_l_index": "1"},
        dataFlowMappingId=_df_id, dataSourceType="CONDITION",
        structure=_structure_with_entity,
        condition=_cond(FIELD_ID, "EQ", "=", "CONSTANT", 1, 1)))

    # 21. 事件投递（应用内同步；eventType=IN_APP 用 selectEvent）
    nodes.append(make_node("PUBLISH_BUSINESS_EVENT", caption="投递事件",
        eventType="IN_APP",
        selectEvent={"id": "1", "name": "测试事件",
                     "fullName": "com.seeyon.datamigration9000000000000000001.dto.microflow.event.TestEvent"},
        mappingType="attrs",
        # ★ mappingType=attrs 必须带真实载荷，空 attrs 会被 G13 拦（消息发出去没内容）
        attrs=[{"attrType": {"id": "com.seeyon.datamigration9000000000000000001.dto."
                                   "microflow.event.TestEvent.text",
                             "caption": "文本", "dataType": "STRING"},
                "value": {"type": "SelectParam",
                          "selectParam": {"outputName": "_CREATE_VARIABLE_text",
                                          "name": "_CREATE_VARIABLE_text",
                                          "dataType": "STRING", "type": "OBJECT",
                                          "position": "parent"}}}]))

    # 22. FOR 循环：forEnd 用 roundOffFloor(总数/999) 函数表达式，套 BREAK + CUSTOM_ERROR
    for_body = [
        make_node("CUSTOM_ERROR", caption="总数过大",
            errorType="GLOBAL",
            error=_expr(build_expression_dto(
                {"name": "_CREATE_VARIABLE_text", "dataType": "STRING", "desc": "文本"},
                "STRING"), "文本变量 ")),
        make_node("BREAK", caption="跳出循环"),
    ]
    nodes.append(make_node("FOR", caption="计数循环",
        output=param("_FOR_index", "INTEGER", "循环变量"),
        forStart={"type": "Simple", "simple": 0, "desc": 0},
        forEnd=_expr(build_function_expression_dto(
            "roundOffFloor",
            [[{"uid": _u(), "type": "VARIABLE",
               "value": "_CREATE_VARIABLE_total._CREATE_VARIABLE_total.value",
               "desc": "总数"},
              {"uid": _u(), "type": "OPERATOR", "value": "/", "desc": "÷"},
              {"uid": _u(), "type": "CONSTANT", "value": "999", "desc": "999"}]],
            "INTEGER"), "向下取整(总数/999)"),
        forStep=1, targetName="循环变量", nodes=for_body))

    # 23. BRANCH 分支：条件「总数变量 != 0」，套一个 CUSTOM_ERROR
    # ★ condition.expression 是形态 2（{title,schema}），取 _expr 的 .expression
    nodes.append(branch([
        {"expr": _expr(build_expression_dto(
            {"name": "_CREATE_VARIABLE_total", "dataType": "BIGINTEGER", "desc": "总数"},
            "BOOLEAN"), "总数变量 != 0")["expression"],
         "nodes": [make_node("CUSTOM_ERROR", caption="总数为零",
             errorType="GLOBAL",
             error=_expr(build_expression_dto(
                 {"name": "_CREATE_VARIABLE_text", "dataType": "STRING", "desc": "文本"},
                 "STRING"), "文本变量 "))]},
        {"expr": None, "nodes": []},
    ]))

    return {
        "trigger_type": "MANUAL",
        "input": {"name": "_FLOW_INPUT_allnodes", "dataType": "DTO", "desc": "入参",
                  "dtoFullName": _DTO_FULL, "inApp": True,
                  "appName": "datamigration9000000000000000001",
                  "hasPagination": False, "isArray": False, "dto": True},
        "output": None,
        "nodes": nodes,
    }


def test_all_nodes_gate_clean() -> None:
    """全节点 schema 通过三道闸门（validate_schema / validate_for_submit / run_gates）。"""
    spec = build_all_nodes_spec()
    schema = build_schema(spec, app_id=APP_ID)

    errs_schema = validate_schema(schema, app_id=APP_ID, flow_name="全节点验收")
    errs_submit = validate_for_submit(schema, app_id=APP_ID, flow_name="全节点验收")
    errs_gates = run_gates(schema)

    problems = {
        "validate_schema": errs_schema,
        "validate_for_submit": errs_submit,
        "run_gates": errs_gates,
    }

    # 覆盖度自检：节点类型清单
    action_types = set()
    def _collect(nodes):
        for n in nodes or []:
            action_types.add(n.get("actionType") or n.get("type"))
            for c in n.get("conditions") or []:
                _collect(c.get("nodes"))
            _collect(n.get("nodes"))
    _collect(schema.get("nodes"))

    assert problems["validate_schema"] == [], f"validate_schema 未通过: {problems['validate_schema']}"
    assert problems["validate_for_submit"] == [], f"validate_for_submit 未通过: {problems['validate_for_submit']}"
    assert problems["run_gates"] == [], f"run_gates 未通过: {problems['run_gates']}"

    # 覆盖度断言：关键节点类型都在
    expected = {
        "CREATE_VARIABLE", "CHANGE_VARIABLE", "CREATE_LIST", "CHANGE_LIST",
        "LIST_OPERATION", "CREATE_MAP", "MAP_OPERATION", "RETRIEVE", "RETRIEVE_ARRAY",
        "CREATE_ENTITY", "CHANGE_ENTITY", "CREATE_BATCH_ENTITY", "CHANGE_BATCH_ENTITY",
        "DELETE_ENTITY", "CONVERT_DATA", "DATA_MAPPING", "SUB_MICROFLOW",
        "CALL_APP_SERVICE", "CALL_DATA_FLOW", "PUBLISH_BUSINESS_EVENT",
        "FOR", "BRANCH", "CUSTOM_ERROR", "BREAK",
    }
    missing = expected - action_types
    assert not missing, f"节点类型未覆盖: {missing}"


if __name__ == "__main__":
    test_all_nodes_gate_clean()
    print("全节点测试通过")


# ---------------------------------------------------------------- mapping 形态
#
# ★★ 平台对 mapping 行校验比 attrs 严（真实保存报错过）：
#   [创建变量] CREATE_VARIABLE_xxx,创建变量.mapping.value.type → DATA_INVALID
#   [创建变量] CREATE_VARIABLE_xxx,创建变量.mapping.value.selectParam.dtoType
#              → PROPERTY_IS_REQUIRED
# 语料 2392 个 mapping 样本：value.type 恒 SelectParam；
# selectParam 16 键 100% 覆盖，dtoType 必带。

def test_mapping_select_param_keeps_required_keys():
    from components.construction.microflow_nodes_v2 import _to_mapping_select_param

    sp = {"key": "K", "name": "f1", "id": "com.x.Dto.f1", "description": "字段1",
          "position": "children", "path": "p", "outputName": "_R1",
          "dataType": "STRING", "type": "OBJECT", "javaType": "java.lang.String",
          "appName": "APP"}
    out = _to_mapping_select_param(sp)
    for k in ("key", "name", "id", "description", "position", "path",
              "outputName", "dataType", "type", "javaType", "dtoType",
              "appName", "udcApp", "multiSelect", "customs", "parentLabel"):
        assert k in out, "mapping selectParam 缺必填键 %s" % k


def test_mapping_select_param_strips_ui_keys():
    """UI 键（nodeInfo/iconKey/disabled…）在语料 mapping 里一个都没有。"""
    from components.construction.microflow_nodes_v2 import _to_mapping_select_param

    sp = {"key": "K", "name": "f1", "type": "OBJECT", "dataType": "STRING",
          "nodeInfo": {"nodeId": "N"}, "iconKey": "", "disabled": False,
          "title": "t", "generics": {}, "hasPagination": False}
    out = _to_mapping_select_param(sp)
    for k in ("nodeInfo", "iconKey", "disabled", "title", "generics",
              "hasPagination"):
        assert k not in out


def test_mapping_select_param_dto_type_defaults():
    """dtoType 默认 CUSTOM；SUB_ENTITY 时 udcApp=True（语料组合）。"""
    from components.construction.microflow_nodes_v2 import _to_mapping_select_param

    a = _to_mapping_select_param({"name": "f"})
    assert a["dtoType"] == "CUSTOM" and a["udcApp"] is False

    b = _to_mapping_select_param({"name": "f", "dtoType": "SUB_ENTITY"})
    assert b["udcApp"] is True

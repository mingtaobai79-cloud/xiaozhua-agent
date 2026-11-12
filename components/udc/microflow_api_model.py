"""规则域 —— 微流程（MicroFlow）API 全集模型。

MicroFlowController（udc/microflow，66 API，udc-web-5.3.517 javap，STATIC_BYTECODE）
是规则域核心，同时是订单应用「微流程查询订单→转列表→查流程/日志/意见并拼接」节点
构建时的元数据/能力来源。

分组（按 desc 编号）：
  1.x 微流程 CRUD/校验/移动/检索
  2.x 服务定义微流程 + 实体规则检索 + caption/name 查重
  3.x 复制 + 设计态元数据检索（DTO/实体树/AppService/method）
  4.x 元数据过滤（事件/MQ/枚举/应用/节点/DTO树）+ 消息投递
  5.x 消息对象 CRUD + 微流程事件/消息查询 + 聚合 DTO/JavaEnum
  6.x 上下游调用信息 + 节点 Schema + 部署查询 + 扩展/连接器服务节点

证据边界：STATIC_BYTECODE。查询类是否真返回数据需宿主执行回读。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.rule.microflow-api.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

MICROFLOW_CONTROLLER = "MicroFlowController"

# 语义 → 真实方法名（javap 实证）；订单应用微流程节点构建会用到的高频项已标注
MICROFLOW_OPS: dict[str, str] = {
    # 1.x 基础
    "微流程_按id": "getMicroFlowDefinition",
    "微流程_分页": "selectPageByCondition",
    "微流程_校验": "checkSchema",
    "微流程_校验并更新": "checkSchemaAndUpdate",
    "微流程_创建": "create",
    "微流程_更新": "update",
    "微流程_排序分组": "updateOrderNoAndGroup",
    "微流程_批量移动": "batchMove",
    "微流程_按标题": "searchListByCaption",
    "微流程_按sourceId详情": "selectDetailsBySourceId",
    "微流程_停用上版元数据": "disableLastVersionMetadata",
    "微流程_按实体查业务规则": "selectEntityRulePageByEntityId",
    "微流程_按sourceId删": "deleteBySourceId",
    "微流程_按id删": "deleteById",
    "微流程_批量删": "deleteByIds",
    "微流程_列表操作分组": "getListOperationType",
    # 2.x 服务定义
    "服务微流程_分页": "selectServiceMicroFlowPageByAppId",
    "服务微流程_子MF分页": "selectSubMfPageByAppId",
    "服务微流程_详情": "getServiceById",
    "服务微流程_动态详情": "getServiceByIdAndHostAppName",
    "微流程_caption查重": "checkMicroFlowCaptionIsExists",
    "微流程_name查重": "checkMicroFlowNameIsExists",
    "微流程_AppService元数据": "getMicroFlowAppServiceMetaDataBoById",
    # 3.x 复制 + 元数据检索
    "微流程_复制": "copy",
    "微流程_按sourceId复制": "copyBySourceId",
    "微流程_复制页面规则控件": "copyPageRuleBoundControl",
    "元数据_非实体DTO": "searchNonEntityDtoByAppName",
    "元数据_自定义DTO": "findCustomDto",
    "元数据_实体树": "searchTreeEntity",
    "元数据_AppService": "searchAppService",
    "元数据_AppService按应用": "searchAppServiceByAppName",
    "元数据_AppService按名": "searchAppServiceByName",
    "元数据_method按名": "searchMethodByName",
    "元数据_DTO按实体": "findDtoByEntity",
    "元数据_聚合DTO批量": "selectMfAggDtoByAggDtoFullNameList",
    "元数据_Rest排除组件": "searchRestExcludeBoot",
    # 4.x 过滤
    "过滤_实体事件": "filterEvent",
    "过滤_系统MQ": "filterSystemMqInfo",
    "过滤_枚举按应用": "searchEnumByAppName",
    "过滤_枚举按名": "findEnumByName",
    "过滤_应用列表": "searchApps",
    "过滤_不可用节点": "getDisableNodes",
    "过滤_实体DTO树": "searchTreeEntityDto",
    "过滤_可投递MQ": "sendMqList",
    "过滤_事件列表": "searchMicroFlowEventList",
    # 5.x 消息对象
    "消息_创建": "createMessage",
    "消息_修改": "updateMessage",
    "消息_按应用查询": "selectMicroFlowMessageByAppId",
    "事件_按应用查询": "selectMicroFlowEventByAppId",
    "消息_删除": "deleteMessageById",
    "消息_按应用列表": "searchMessageDtoByAppName",
    "消息_详情含属性": "selectMessageDtoWithAttrsById",
    "消息_元数据存在校验": "checkDtoMetadataExist",
    "服务微流程_前端页面子流程": "selectServiceFrontendPageBySourceId",
    "元数据_聚合JavaEnum批量": "selectMfJavaEnumByAggDtoFullNameList",
    "元数据_全量聚合DTO": "selectMfFullAggDto",
    "元数据_数据体系": "selectDataSystemInfo",
    "过滤_非虚拟DTO": "filterNotVirtualDto",
    # 6.x 上下游 + 节点Schema + 部署
    "调用_上游": "findUpstreamCallInfo",
    "调用_下游": "findDownstreamCallInfo",
    "节点_按条件Schema": "findNodeSchemaByCondition",
    "部署_全量微流程": "selectListByCondition4Deploy",
    "节点_扩展服务": "findCallExtendAppServiceNode",
    "节点_连接器服务": "findCallConnectorAppService",
    "微流程_恢复": "recover",
    "微流程_复制简": "copy",
    "微流程_测试实体引用": "entityRef",
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def microflow_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    ctrl = data.get(MICROFLOW_CONTROLLER, {})
    by_name = {m["method"]: m for m in ctrl.get("methods", [])}
    out: dict[str, dict[str, Any]] = {}
    for op, name in MICROFLOW_OPS.items():
        m = by_name.get(name)
        out[op] = ({"controller": MICROFLOW_CONTROLLER, "http": m["http"],
                    "full_path": m["full_path"], "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": MICROFLOW_CONTROLLER, "method_name": name,
                              "resolved": False})
    return out


def microflow_coverage() -> dict[str, Any]:
    """MicroFlowController 全 66 方法是否都被语义目录覆盖（同一方法可映射多语义）。"""
    data = _load()
    ctrl = data.get(MICROFLOW_CONTROLLER, {})
    all_methods = {m["method"] for m in ctrl.get("methods", [])}
    mapped = set(MICROFLOW_OPS.values())
    return {"schema": SCHEMA_ID, "controller": MICROFLOW_CONTROLLER,
            "class_mapping": ctrl.get("class_mapping"), "api_count": ctrl.get("api_count", 0),
            "total_methods": len(all_methods), "mapped_methods": len(mapped & all_methods),
            "unmapped": sorted(all_methods - mapped)}


__all__ = ["SCHEMA_ID", "MICROFLOW_CONTROLLER", "MICROFLOW_OPS",
           "microflow_api_map", "microflow_coverage"]

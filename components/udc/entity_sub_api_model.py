"""实体域 —— 子域 controller API 综合模型。

覆盖 EntityController 之外的实体域 9 个 controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- DataTypeController（udc/data-type，6）       数据类型（人员多选/基础/参数）
- EventController（udc/event，12）             实体事件（含 with-data 变体、业务事件）
- IndexController（udc/index，7）              索引（订单号索引）
- AttributeSetController（udc/attributeSet，10）字段集（枚举选项集/默认值来源）
- AttributeGroupController（udc/attribute-group，7）属性分组
- StereotypeController（udc/stereotype，1）    版型清单（与 platform_mechanism_model 呼应）
- EntityOpenApiController（udc/entity-open-api，1）openApi 展示
- ScalabilityController（udc/scalability，6）+ ScalabilityOptionController（udc/scalability-option，8）扩展方案

订单应用映射：订单号索引=Index、枚举选项集/默认值=AttributeSet、实体事件=Event、
人员多选=DataType（人员类型）、扩展字段=Scalability。

证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.entity.subapi.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

ENTITY_SUB_CONTROLLERS = [
    "DataTypeController", "EventController", "IndexController",
    "AttributeSetController", "AttributeGroupController", "StereotypeController",
    "EntityOpenApiController", "ScalabilityController", "ScalabilityOptionController",
    "ReferConfigController",
]

# 子域语义 → (controller, method)
ENTITY_SUB_OPS: dict[str, tuple[str, str]] = {
    # 数据类型
    "数据类型_列表": ("DataTypeController", "selectDataTypes"),
    "数据类型_基础": ("DataTypeController", "selectBaseDataTypes"),
    "数据类型_参数": ("DataTypeController", "selectParameterDataTypes"),
    "数据类型_按应用": ("DataTypeController", "selectDataTypesByAppId"),
    "数据类型_详情": ("DataTypeController", "selectDataTypeByName"),
    "数据类型_按条件": ("DataTypeController", "selectDataTypeByParams"),
    # 事件
    "事件_创建": ("EventController", "create"),
    "事件_创建带数据": ("EventController", "createWithEventData"),
    "事件_修改": ("EventController", "update"),
    "事件_修改带数据": ("EventController", "updateWithEventData"),
    "事件_删除": ("EventController", "deleteById"),
    "事件_批量删除": ("EventController", "deleteByIds"),
    "事件_分页": ("EventController", "search"),
    "事件_列表": ("EventController", "selectListWithDataByConditions"),
    "事件_详情": ("EventController", "selectById"),
    "事件_模糊": ("EventController", "selectListWithDataByTerm"),
    "事件_业务事件": ("EventController", "selectBusinessEvent"),
    "事件_详情带数据": ("EventController", "selectEvents"),
    # 索引
    "索引_创建": ("IndexController", "create"),
    "索引_删除": ("IndexController", "deleteById"),
    "索引_批量删除": ("IndexController", "deleteByIds"),
    "索引_修改": ("IndexController", "update"),
    "索引_详情": ("IndexController", "selectById"),
    "索引_按实体列表": ("IndexController", "selectByEntityId"),
    "索引_可选字段": ("IndexController", "selectMatchesAttributeByEntityId"),
    # 字段集
    "字段集_创建": ("AttributeSetController", "create"),
    "字段集_删除": ("AttributeSetController", "deleteById"),
    "字段集_批量删除": ("AttributeSetController", "deleteByIds"),
    "字段集_修改": ("AttributeSetController", "update"),
    "字段集_详情": ("AttributeSetController", "selectById"),
    "字段集_列表": ("AttributeSetController", "selectListByConditions"),
    "字段集_按应用": ("AttributeSetController", "selectListByAppId"),
    "字段集_按名称含属性": ("AttributeSetController", "selectListByNameWithAttributes"),
    "字段集_模糊": ("AttributeSetController", "selectListByTerm"),
    "字段集_字段列表": ("AttributeSetController", "selectByAttributeSetId"),
    # 属性分组
    "属性分组_创建": ("AttributeGroupController", "create"),
    "属性分组_修改": ("AttributeGroupController", "update"),
    "属性分组_取消": ("AttributeGroupController", "cancel"),
    "属性分组_移除": ("AttributeGroupController", "remove"),
    "属性分组_交换顺序": ("AttributeGroupController", "swap"),
    "属性分组_全表编辑": ("AttributeGroupController", "operateBatch"),
    "属性分组_按实体": ("AttributeGroupController", "selectListByEntityId"),
    # 版型 / openApi
    "版型_清单": ("StereotypeController", "list"),
    "openApi_展示": ("EntityOpenApiController", "selectOpenApiData"),
    # 参照配置（ReferConfigController）
    "参照配置_创建带终端": ("ReferConfigController", "createConfigInfo"),
    "参照配置_更新带终端": ("ReferConfigController", "updateConfigInfo"),
    "参照配置_删按组分": ("ReferConfigController", "deleteByGroupId"),
    "参照配置_组列表": ("ReferConfigController", "selectGroupListByConditions"),
    "参照配置_PC转移动": ("ReferConfigController", "convertToMobile"),
    # 属性分组补（swap 已在 EntityController，此处补 AttributeGroupController）
    "属性分组_交换顺序2": ("AttributeGroupController", "swap"),
    # 扩展方案
    "扩展明细_创建": ("ScalabilityController", "create"),
    "扩展明细_修改": ("ScalabilityController", "update"),
    "扩展明细_删除": ("ScalabilityController", "deleteById"),
    "扩展明细_批量删除": ("ScalabilityController", "deleteByIds"),
    "扩展明细_详情": ("ScalabilityController", "selectById"),
    "扩展明细_按方案": ("ScalabilityController", "selectByOptionId"),
    "扩展方案_创建": ("ScalabilityOptionController", "create"),
    "扩展方案_修改": ("ScalabilityOptionController", "update"),
    "扩展方案_删除": ("ScalabilityOptionController", "deleteById"),
    "扩展方案_详情": ("ScalabilityOptionController", "selectById"),
    "扩展方案_树按应用": ("ScalabilityOptionController", "selectByAppId"),
    "扩展方案_含明细": ("ScalabilityOptionController", "selectByAppIdWithDetail"),
    "扩展方案_全部名称": ("ScalabilityOptionController", "selectAllOptionName"),
    "扩展方案_数据类型": ("ScalabilityOptionController", "selectScalabilityDataType"),
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def entity_sub_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, (ctrl, name) in ENTITY_SUB_OPS.items():
        v = data.get(ctrl, {})
        m = next((x for x in v.get("methods", []) if x["method"] == name), None)
        out[op] = ({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                    "http": m["http"], "full_path": m["full_path"],
                    "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ctrl, "method_name": name, "resolved": False})
    return out


def entity_sub_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in ENTITY_SUB_CONTROLLERS},
            "op_count": len(ENTITY_SUB_OPS)}


__all__ = ["SCHEMA_ID", "ENTITY_SUB_CONTROLLERS", "ENTITY_SUB_OPS",
           "entity_sub_api_map", "entity_sub_summary"]

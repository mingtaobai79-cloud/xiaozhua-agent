"""实体域 —— EntityController API 全集模型。

EntityController（udc/entity，54 API，udc-web-5.3.517 javap，STATIC_BYTECODE）
是实体域核心。分组：
  实体 CRUD + 树/主实体/根    create/update/delete/selectPage/selectTree/selectPrimary...
  属性 CRUD + 批量 + 查询      attribute、attribute-batch、attribute/update、select-all-by-entity-id...
  属性分组                     attribute-group/create-update、cancel-group、bath-update
  预置（Excel/预置实体）        preset-*、create-default-excel-template
  关联/序列/约束                association/entity、association/serial、constraint/entity
  SQL 修护（部署记录）          sql/deploy-record/*、sql/unlock-*、sql/not-null-repair

订单应用映射：新订单实体(create)、订单信息(attribute)、人员多选(attribute 类型)、
订单号索引(index 域)、默认值(attribute default)、字段集(attributeSet 域)。

证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.entity.api.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

ENTITY_CONTROLLER = "EntityController"

ENTITY_OPS: dict[str, str] = {
    # 实体
    "实体_创建": "create",
    "实体_修改": "update",
    "实体_批量改组号排序": "updateBatch4EntityGroupIdAndOrderNo",
    "实体_修改扩展联动": "updateExtensionLinkage",
    "实体_删除": "deleteById",
    "实体_批量删除": "deleteByIds",
    "实体_详情": "selectById",
    "实体_分页": "selectPageByCondition",
    "实体_列表": "selectListByConditions",
    "实体_模糊": "selectListByTerm",
    "实体_父实体": "selectParentById",
    "实体_子实体": "selectChildrenByCondition",
    "实体_主实体按应用": "selectPrimaryEntityByAppId",
    "实体_树按应用": "selectEntitiesByAppId4Tree",
    "实体_全量按应用": "selectAllEntitiesByAppId",
    "实体_根id": "selectRootId",
    "实体_全量按实体id": "selectAllEntitiesByEntityId",
    "实体_事件数据": "selectEventDatasByEntityId",
    "实体_主实体数量": "selectMasterEntityCount",
    "实体_复制": "copyEntity",
    # 属性
    "属性_迁移": "attributeTransfer",
    "属性_创建": "createAttribute",
    "属性_批量创建": "createAttributionBatch",
    "属性_修改": "updateAttribute",
    "属性_批量修改": "updateAttributeBatch",
    "属性_删除": "deleteAttributeById",
    "属性_批量删除": "deleteAttributeByIds",
    "属性_详情": "selectAttributeById",
    "属性_列表按条件": "selectEntityAttributeListByCondition",
    "属性_模糊": "selectAttributeListByTerm",
    "属性_按主实体": "selectByPrimaryEntityId",
    "属性_全量按实体": "selectAllAttributeByEntityId",
    "属性_父枚举属性": "selectParentEnumAttributes",
    "属性_预置容量": "selectAllPreSetAttributeCapacity",
    # 属性分组
    "分组_列表": "selectEntityAttributeGroupList",
    "分组_创建更新": "createGroup",
    "分组_取消": "cancelGroup",
    # 预置
    "预置_实体按应用": "selectPresetEntityListByAppId",
    "预置_列表按应用": "selectPresetListByAppId",
    "预置_按实体": "selectPresetByEntityId",
    "预置_默认Excel模板": "createDefaultExcelTemplate",
    "预置_创建": "createPreset",
    "预置_修改": "updatePreset",
    # 关联/序列/约束
    "关联_实体分组": "selectAssociationEntityGroup",
    "约束_实体": "selectConstraintEntity",
    "序列_列表": "selectSerialListByConditions",
    "序列_分组": "selectAssociationSerialGroup",
    # SQL 修护
    "SQL_部署记录表": "selectEntityTableSqlFromDeployRecord",
    "SQL_替换存储键": "replaceDeployRecordSqlStorageKey",
    "SQL_修复存储键": "repairSqlStorageKey",
    "SQL_解锁实体": "unlockEntity",
    "SQL_解锁属性": "unlockAttribute",
    "SQL_非空修复": "notNullRepair",
    "扩展_移除联动": "removeExtEntityLinkage",
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def entity_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    ctrl = data.get(ENTITY_CONTROLLER, {})
    by_name = {m["method"]: m for m in ctrl.get("methods", [])}
    out: dict[str, dict[str, Any]] = {}
    for op, name in ENTITY_OPS.items():
        m = by_name.get(name)
        out[op] = ({"controller": ENTITY_CONTROLLER, "http": m["http"],
                    "full_path": m["full_path"], "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ENTITY_CONTROLLER, "method_name": name,
                              "resolved": False})
    return out


def entity_coverage() -> dict[str, Any]:
    data = _load()
    ctrl = data.get(ENTITY_CONTROLLER, {})
    all_methods = {m["method"] for m in ctrl.get("methods", [])}
    mapped = set(ENTITY_OPS.values())
    return {"schema": SCHEMA_ID, "controller": ENTITY_CONTROLLER,
            "class_mapping": ctrl.get("class_mapping"), "api_count": ctrl.get("api_count", 0),
            "total_methods": len(all_methods), "mapped_methods": len(mapped & all_methods),
            "unmapped": sorted(all_methods - mapped)}


__all__ = ["SCHEMA_ID", "ENTITY_CONTROLLER", "ENTITY_OPS", "entity_api_map",
           "entity_coverage"]

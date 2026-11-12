"""设置域 —— 设计态元数据查询 API 模型（订单应用构建的元数据面）。

两 controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- MetaDataController（udc/meta-data，28 API）：设计态元数据查询主入口。
  【实体】select-entity / 聚合根 / 【参照】select-refer-by-entity / 【枚举】ctp-enum / java-enum /
  【页面】select-page / select-all-page-by-app / 【外框】select-all-layout-by-app。
- UdcDesignMetadataController（udc/design-metadata，47 API）：按服务名查微服务元数据。
  Rest / OpenApi / DTO / Entity / JavaEnum / AppService / MQ / Agg（聚合根）/ Refer / Page ...
  多带 "exclude-boot"（排除组件）变体 + by-name / by-names 批量。

这是「设计器页面从元数据拉取可选实体/参照/枚举/页面」的后端契约，
也是订单应用（新订单实体/参照/枚举选项集/页面排版）构建时的元数据取证面。

证据边界：STATIC_BYTECODE。查询类 GET/POST 是否真返回数据需宿主执行回读。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.settings.design-metadata.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

METADATA_CONTROLLERS = ["MetaDataController", "UdcDesignMetadataController"]

# MetaDataController 查询语义 → 真实方法名（javap 实证）
METADATA_QUERIES: dict[str, dict[str, str]] = {
    # 实体 / 聚合根
    "实体_按id或fullName": {"method": "selectEntityMetaData"},
    "实体_按应用取聚合根名": {"method": "selectEntityMetaDataByAppId"},
    "聚合根_按实体id含关联": {"method": "selectAggEntityIncludeAssociation"},
    "聚合根_按实体无关联": {"method": "selectAggEntity"},
    "聚合根_按应用名": {"method": "selectEntityMetaDataByAppName"},
    # 参照
    "参照_按实体": {"method": "selectReferMetaDataByEntity"},
    "参照_按实体含微服务": {"method": "selectReferAndAppMetadataByEntity"},
    "参照_合并映射": {"method": "mergeReferMetaData"},
    "参照_页面自定义": {"method": "selectCustomReferMetaDataByPageId"},
    # 枚举
    "库枚举_按应用": {"method": "selectCtpEnumMetaDataListData"},
    "库枚举_按应用含关联": {"method": "selectCtpEnumMetaDataListData1"},
    "库枚举项": {"method": "selectCtpEnumItemList"},
    "java枚举_按应用": {"method": "selectJavaEnumMetaDataList"},
    "java枚举项": {"method": "selectJavaEnumItemMetaDataList"},
    # 页面
    "页面_按id或fullName": {"method": "selectPageMetaData"},
    "页面_信息列表": {"method": "selectPageInfoMetaData"},
    "页面_按应用全量": {"method": "selectAllPageMetaDataByApp"},
    "页面_菜单树含页面": {"method": "selectFunctionNodeWithPageInfoDtoTreeByApp"},
    # 外框
    "外框_按应用": {"method": "selectAllLayoutMetaDataByApp"},
    "外框_页面外框信息": {"method": "selectPageLayoutInfoMetaData"},
    "外框_含Schema": {"method": "selectPageLayoutMetaData"},
    "外框_批量含Schema": {"method": "selectPageLayoutMetaDataList"},
    # 辅助 / 依赖查询
    "应用_可被依赖": {"method": "selectPageAvailableAppMetaDataByCondition"},
    "应用_可被依赖多版本": {"method": "selectPageAvailableAppMultiVersionMetaDataByCondition"},
    "应用_可升级": {"method": "selectAvailableUpgradeAppMetadataById"},
    "页面_BPM Schema": {"method": "selectPageSchema4Bpm"},
    "元数据_按文件名": {"method": "selectMetadataByFileName"},
    "元数据_按应用": {"method": "selectMetadataByAppId"},
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def metadata_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    ctrl = data.get("MetaDataController", {})
    by_name = {m["method"]: m for m in ctrl.get("methods", [])}
    out: dict[str, dict[str, Any]] = {}
    for op, spec in METADATA_QUERIES.items():
        m = by_name.get(spec["method"])
        out[op] = ({"controller": "MetaDataController", "http": m["http"],
                    "full_path": m["full_path"], "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": "MetaDataController",
                              "method_name": spec["method"], "resolved": False})
    return out


def design_metadata_summary() -> dict[str, Any]:
    """UdcDesignMetadataController 按元数据类型聚合（Rest/DTO/Entity/Agg/Refer/Page...）。"""
    data = _load()
    ctrl = data.get("UdcDesignMetadataController", {})
    groups: dict[str, list[dict]] = {}
    for m in ctrl.get("methods", []):
        desc = m.get("desc", "")
        kind = desc.split(".")[0] if "." in desc else "中"
        groups.setdefault(kind, []).append({"method": m["method"], "http": m["http"],
                                            "full_path": m["full_path"]})
    return {"schema": SCHEMA_ID, "controller": "UdcDesignMetadataController",
            "class_mapping": ctrl.get("class_mapping"), "api_count": ctrl.get("api_count", 0),
            "kinds": {k: len(v) for k, v in sorted(groups.items())},
            "groups": groups}


# UdcDesignMetadataController 全 47 方法：按元数据类型 × 操作模式（javap 实证方法名）
# 模式：base=按服务, names=批量 by fullNames, name=单个 by fullName, boot=exclude-boot
DESIGN_METADATA_KINDS: dict[str, dict[str, str]] = {
    "Service": {"base": "selectServiceMetadata"},
    "Rest": {"base": "selectRestApiMetadata", "names": "selectRestApiMetadataByFullNames",
             "name": "selectRestApiMetadataByFullName", "boot": "selectRestApiMetadataExcludeBoot"},
    "OpenApi": {"base": "selectOpenApiMetadata", "names": "selectOpenApiMetadataByFullNames",
                "name": "selectOpenApiMetadataByFullName"},
    "DTO": {"base": "selectDtoMetadata", "names": "selectDtoMetadataByFullNames",
            "name": "selectDtoMetadataByFullName", "boot": "selectDtoMetadataExcludeBoot",
            "relation": "selectEntityRelationDtoMetadata",
            "relation_boot": "selectEntityRelationDtoMetadataExcludeBoot",
            "by_entity": "selectDtoMetadataByEntityFullName",
            "by_entities": "selectDtoMetadataByEntityFullNames"},
    "Enum": {"base": "selectEnumMetadata", "names": "selectEnumMetadataByFullNames",
             "name": "selectEnumMetadataByFullName"},
    "Entity": {"base": "selectEntityMetadata", "names": "selectEntityMetadataByFullNames",
               "name": "selectEntityMetadataByFullName", "boot": "selectEntityMetadataExcludeBoot"},
    "AppService": {"base": "selectAppServiceMetadata", "names": "selectAppServiceMetadataByFullNames",
                   "name": "selectAppServiceMetadataByFullName", "boot": "selectAppServiceMetadataExcludeBoot",
                   "by_dto": "selectAppServiceMetadataByDto"},
    "MQ": {"base": "selectMqMetadata", "names": "selectMqMetadataByFullNames",
           "name": "selectMqMetadataByFullName", "boot": "selectMqMetadataExcludeBoot"},
    "Agg": {"base": "selectAggMetadata", "names": "selectAggMetadataByFullNames",
            "name": "selectAggMetadataByFullName", "boot": "selectAggMetadataExcludeBoot",
            "entity": "selectAggEntityMetadata", "entity_name": "selectAggEntityMetadataByFullName",
            "entity_names": "selectAggEntityMetadataByFullNames",
            "entity_boot": "selectAggEntityMetadataExcludeBoot",
            "entity_by_agg": "selectEntityListByAgg"},
    "Refer": {"base": "selectReferMetadataByEntity", "and_app": "selectReferAndAppMetadataByEntity"},
    "BasicEntity": {"base": "selectBasicEntityMetadata", "names": "selectBasicEntityMetadataByFullNames",
                    "name": "selectBasicEntityMetadataByFullName"},
    "Page": {"name": "selectPageMetadataByFullName"},
}


def design_metadata_api_map() -> dict[str, dict[str, Any]]:
    """UdcDesignMetadataController 全 47 方法 → 语义键 `设计元数据_<Kind>_<mode>`。"""
    data = _load()
    ctrl = data.get("UdcDesignMetadataController", {})
    by_name = {m["method"]: m for m in ctrl.get("methods", [])}
    out: dict[str, dict[str, Any]] = {}
    for kind, modes in DESIGN_METADATA_KINDS.items():
        for mode, name in modes.items():
            m = by_name.get(name)
            key = f"设计元数据_{kind}_{mode}"
            out[key] = ({"controller": "UdcDesignMetadataController", "http": m["http"],
                         "full_path": m["full_path"], "desc": m.get("desc", ""), "resolved": True}
                        if m else {"controller": "UdcDesignMetadataController",
                                   "method_name": name, "resolved": False})
    return out


__all__ = ["SCHEMA_ID", "METADATA_CONTROLLERS", "METADATA_QUERIES",
           "metadata_api_map", "design_metadata_summary",
           "DESIGN_METADATA_KINDS", "design_metadata_api_map"]

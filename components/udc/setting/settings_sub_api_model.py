"""设置域 —— DataFlow/DTO/Manager/多编辑/日志/文件 等子域 controller API 综合模型。

controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- DataFlowDesignController（udc/data-flow，24）：生单规则图 + 映射规则
- DataTransferObjectController（udc/data-transfer-object，20）：数据传输对象（DTO）+ 属性
- UdcManagerController（udc/manager，13）：限流/请求状态/日志/日志配置
- COLISplitController（udc/app-split，8）：中海应用拆分
- MultiEditController（udc/multi-edit，5）：多端并发编辑锁
- OperationLogController（udc/operation-log，6）：操作日志
- FeatureController（udc/feature，2）：特性/系统属性清单
- UdcCtpEnumController（udc/udc-enum-item，5）：运行时枚举项（补 enum_model 未覆盖的查询）
- UdcSandBoxLogController（udc/sandbox/logs，5）：沙箱运行态日志
- UdcFileController（udc/runtime/file，2）：运行时文件下载

证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.settings.sub-api.v1"

_API = (Path(__file__).resolve().parents[3] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

SETTINGS_SUB_CONTROLLERS = [
    "DataFlowDesignController", "DataTransferObjectController", "UdcManagerController",
    "COLISplitController", "MultiEditController", "OperationLogController",
    "FeatureController", "UdcCtpEnumController", "UdcSandBoxLogController",
    "UdcFileController",
]

SETTINGS_SUB_OPS: dict[str, tuple[str, str]] = {
    # 生单规则图
    "生单图_按应用": ("DataFlowDesignController", "selectByAppId"),
    "生单图_详情": ("DataFlowDesignController", "selectById"),
    "生单图_创建": ("DataFlowDesignController", "create"),
    "生单图_更新": ("DataFlowDesignController", "update"),
    "生单图_删除": ("DataFlowDesignController", "deleteById"),
    "生单图_批量删除": ("DataFlowDesignController", "deleteByIds"),
    "生单图_分页": ("DataFlowDesignController", "selectPageByCondition"),
    "生单图_可选实体": ("DataFlowDesignController", "selectEntityListByCondition"),
    "生单图_映射数": ("DataFlowDesignController", "selectMappingCountByEntityId"),
    "生单图_线映射数": ("DataFlowDesignController", "selectLineMappingCountByEntity"),
    "生单图_删线或节点": ("DataFlowDesignController", "deleteLineOrNodeInGraph"),
    "生单图_映射初始化": ("DataFlowDesignController", "selectMappingInitData"),
    "生单图_创建映射": ("DataFlowDesignController", "createMapping"),
    "生单图_更新映射": ("DataFlowDesignController", "updateMapping"),
    "生单图_映射详情": ("DataFlowDesignController", "selectMappingById"),
    "生单图_删映射": ("DataFlowDesignController", "deleteMapping"),
    "生单图_映射列表": ("DataFlowDesignController", "selectMappingListByCondition"),
    "生单图_映射批量详情": ("DataFlowDesignController", "selectByIds"),
    "生单图_应用列表": ("DataFlowDesignController", "selectApplicationListByAppId"),
    "生单图_手动映射": ("DataFlowDesignController", "selectManuallyMapping"),
    "生单图_事件实体": ("DataFlowDesignController", "selectEntityListByAppId"),
    "生单图_事件列表": ("DataFlowDesignController", "selectEventListByCondition"),
    "生单图_事件数据": ("DataFlowDesignController", "selectEventDataByFullName"),
    # DTO
    "DTO_创建": ("DataTransferObjectController", "create"),
    "DTO_创建含属性": ("DataTransferObjectController", "createDtoWithAttrs"),
    "DTO_更新": ("DataTransferObjectController", "update"),
    "DTO_更新含属性": ("DataTransferObjectController", "updateDtoWithAttrs"),
    "DTO_删除": ("DataTransferObjectController", "deleteById"),
    "DTO_详情": ("DataTransferObjectController", "selectById"),
    "DTO_详情含属性": ("DataTransferObjectController", "selectDtoWithAttrsById"),
    "DTO_可选中列表": ("DataTransferObjectController", "selectListByConditions"),
    "DTO_创建含属性和引用": ("DataTransferObjectController", "createDtoWithAttrsAndRefDtos"),
    "DTO_更新含属性和引用": ("DataTransferObjectController", "updateDtoWithAttrsAndRefDtos"),
    "DTO_详情含属性和引用": ("DataTransferObjectController", "selectDtoWithAttrsAndRefDtos"),
    "DTO_按来源id": ("DataTransferObjectController", "selectListBySourceId"),
    "DTO_微流程自定义按应用": ("DataTransferObjectController", "selectMicroFlowCustomDtoByAppId"),
    "DTO_微流程自定义分页": ("DataTransferObjectController", "selectPageMicroFlowCustomDtoByAppId"),
    "DTO_按微流程id": ("DataTransferObjectController", "selectAllByMicroFlowId"),
    "DTO_删除含属性和引用": ("DataTransferObjectController", "deleteDtoWithAttrsAndRefDtos"),
    "DTO_存在校验": ("DataTransferObjectController", "checkExists"),
    "DTO属性_修改": ("DataTransferObjectController", "updateAttribute"),
    "DTO属性_删除": ("DataTransferObjectController", "deleteAttributeById"),
    "DTO属性_列表": ("DataTransferObjectController", "selectAttributeListByConditions"),
    # 管理器
    "管理器_限流说明": ("UdcManagerController", "explain"),
    "管理器_清超期许可": ("UdcManagerController", "clearTimeout"),
    "管理器_强制清许可": ("UdcManagerController", "clearForce"),
    "管理器_请求状态": ("UdcManagerController", "getRequestStatus"),
    "管理器_日志": ("UdcManagerController", "getLogs"),
    "管理器_组件日志": ("UdcManagerController", "getComponentLogs"),
    "管理器_应用日志配置更新": ("UdcManagerController", "enableAppLogConfig"),
    "管理器_应用日志配置重置": ("UdcManagerController", "resetAppLogConfig"),
    "管理器_应用日志配置查询": ("UdcManagerController", "getAppLogConfig"),
    "管理器_数据日志配置重置": ("UdcManagerController", "resetAppDataLogConfig"),
    "管理器_数据日志配置查询": ("UdcManagerController", "getAppDataLogConfig"),
    "管理器_应用分页": ("UdcManagerController", "selectPageByConditions"),
    "管理器_子应用分页": ("UdcManagerController", "selectSubAppPageByConditions"),
    # 拆分
    "拆分_上传": ("COLISplitController", "upload"),
    "拆分_导入应用": ("COLISplitController", "coliImportAppSchema"),
    "拆分_请求状态": ("COLISplitController", "getRequestStatus"),
    "拆分_结果": ("COLISplitController", "selectSplitResult"),
    "拆分_删应用": ("COLISplitController", "deleteBySourceAppId"),
    "拆分_实体名映射": ("COLISplitController", "selectEntityNameConvertMap"),
    "拆分_删记录": ("COLISplitController", "deleteRecordBySourceAppId"),
    "拆分_导入记录列表": ("COLISplitController", "selectSplitImportRecordList"),
    # 多编辑锁
    "锁_获取": ("MultiEditController", "lock"),
    "锁_续期": ("MultiEditController", "renewal"),
    "锁_取消": ("MultiEditController", "unlock"),
    "锁_强制取消": ("MultiEditController", "forceUnlock"),
    "锁_当前": ("MultiEditController", "getCurrentLock"),
    # 操作日志
    "操作日志_查询": ("OperationLogController", "search"),
    "操作日志_按存储键": ("OperationLogController", "search4StorageKey"),
    "操作日志_全删": ("OperationLogController", "deleteAll"),
    "操作日志_初始化": ("OperationLogController", "initData"),
    "操作日志_详情": ("OperationLogController", "searchOperationLogDetailsById"),
    "操作日志_元素存在": ("OperationLogController", "elementIsExist"),
    # 特性
    "特性_清单": ("FeatureController", "list"),
    "特性_系统属性": ("FeatureController", "listSystemAttributeNames"),
    # 运行时枚举（补 enum_model）
    "枚举项_按id和应用": ("UdcCtpEnumController", "selectOneByIdAndApp"),
    "枚举项_按依赖应用": ("UdcCtpEnumController", "selectByEnumItemByDependentApp"),
    # 沙箱日志
    "沙箱日志_微流程": ("UdcSandBoxLogController", "search"),
    "沙箱日志_微流程详情": ("UdcSandBoxLogController", "searchDetails"),
    "沙箱日志_流程日志": ("UdcSandBoxLogController", "searchFlowDetails"),
    "沙箱日志_页面": ("UdcSandBoxLogController", "searchPageLog"),
    "沙箱日志_页面无元数据": ("UdcSandBoxLogController", "searchPageLogNonMetadata"),
    # 文件
    "文件_下载": ("UdcFileController", "download"),
    "文件_元数据下载": ("UdcFileController", "metadataDownload"),
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def settings_sub_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, (ctrl, name) in SETTINGS_SUB_OPS.items():
        v = data.get(ctrl, {})
        m = next((x for x in v.get("methods", []) if x["method"] == name), None)
        out[op] = ({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                    "http": m["http"], "full_path": m["full_path"],
                    "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ctrl, "method_name": name, "resolved": False})
    return out


def settings_sub_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in SETTINGS_SUB_CONTROLLERS},
            "op_count": len(SETTINGS_SUB_OPS)}


__all__ = ["SCHEMA_ID", "SETTINGS_SUB_CONTROLLERS", "SETTINGS_SUB_OPS",
           "settings_sub_api_map", "settings_sub_summary"]

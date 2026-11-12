"""测试：运行态（udc-starter-runtime 5.3.517）端点目录与 DTO 约束。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.runtime_constraints import (
    RUNTIME_CONTROLLERS, RUNTIME_ENDPOINTS, RUNTIME_ENDPOINT_PATHS,
    RUNTIME_DTO_REQUIRED, validate_runtime_dto,
    is_readonly_endpoint, find_endpoint,
)


def test_controller_base_paths():
    assert RUNTIME_CONTROLLERS["UdcFormDataQueryController"] == "udc-runtime/data"
    assert RUNTIME_CONTROLLERS["UdcSerialConfigController"] == "udc-runtime/serial-config"
    assert RUNTIME_CONTROLLERS["GraphqlProxyController"] == "udc-runtime/graphql-proxy"
    # extmetadata 的 Controller（UdcMetaDataController 同挂 meta-data 基址）
    assert RUNTIME_CONTROLLERS["UdcMetaDataController"] == "udc-runtime/meta-data"
    assert RUNTIME_CONTROLLERS["UdcAppInfoController"] == "udc-app-info"
    assert len(RUNTIME_CONTROLLERS) == 21


def test_endpoint_catalog_complete():
    # 98 个端点全部登记（78 udc-starter-runtime + 18 extmetadata + 2 app-info）
    assert len(RUNTIME_ENDPOINTS) == 98
    assert len(RUNTIME_ENDPOINT_PATHS) == 98
    # 核心只读端点
    assert find_endpoint("udc-runtime/data/query") == ("POST", "表单数据查询", True)
    assert find_endpoint("udc-runtime/database/query-data") == ("GET", "查询数据库数据", True)
    assert find_endpoint("udc-runtime/datatype/getAll") == ("GET", "全部数据类型", True)
    # 路径变量归一化
    assert find_endpoint("udc-runtime/app-log/datalog/123") == ("GET", "数据日志详情", True)
    assert find_endpoint("udc-runtime/app-log/datalog/list-by-dataid/456") == ("GET", "按数据Id查日志", True)
    assert is_readonly_endpoint("udc-runtime/evn-check/build-info/myapp") is True
    # import/status 查询是只读（名字含 import 但功能是查询状态）
    assert is_readonly_endpoint("udc-runtime/dynamic/jar/import/status/req1") is True
    # extmetadata 端点
    assert find_endpoint("udc-runtime/meta-data/select-entity") == ("POST", "查实体元数据", True)
    assert find_endpoint("udc-runtime/meta-data/select-all-entity-by-app-name/zzprobe") == ("GET", "应用全部实体简表", True)
    assert find_endpoint("udc-app-info/entity-table/zzprobe") == ("GET", "应用实体→表映射", True)
    assert is_readonly_endpoint("udc-runtime/meta-data/delete-metadata-by-app-name") is False
    assert find_endpoint("udc-runtime/meta-data/test") is None  # 测试端点不登记


def test_write_endpoints_not_readonly():
    # 写端点必须标 False（LIVE 探针禁调）；import/status 是查询不算写
    for path, (_m, _d, ro) in RUNTIME_ENDPOINT_PATHS.items():
        if "import/status" in path:
            assert ro is True
            continue
        if any(k in path for k in ("delete", "create", "update", "clear", "unload",
                                   "init-tenant", "enable-log", "import", "upgrade")):
            assert ro is False, f"{path} 是写操作但标了只读"
    assert is_readonly_endpoint("udc-runtime/custom-app/delete") is False
    assert is_readonly_endpoint("udc-runtime/serial-config/update") is False
    assert is_readonly_endpoint("udc-runtime/app-draft/create") is False


def test_unknown_endpoint():
    assert find_endpoint("udc-runtime/nope/nope") is None
    assert is_readonly_endpoint("udc-runtime/nope/nope") is None


def test_dto_required_validation():
    # EntityDataRequestDto 三必填
    errs = validate_runtime_dto("EntityDataRequestDto", {})
    assert sorted(errs) == [
        "EntityDataRequestDto 缺必填字段 appName",
        "EntityDataRequestDto 缺必填字段 dataId",
        "EntityDataRequestDto 缺必填字段 entityFullName",
    ]
    ok = {"appName": "zzprobe", "entityFullName": "com.seeyon.Order", "dataId": 1}
    assert validate_runtime_dto("EntityDataRequestDto", ok) == []
    # UdcSerialConfigDto 两必填
    assert validate_runtime_dto(
        "UdcSerialConfigDto", {"sourceFullName": "x", "entityFullName": "y"}) == []
    assert validate_runtime_dto("UdcSerialConfigDto", {"sourceFullName": "x"}) == [
        "UdcSerialConfigDto 缺必填字段 entityFullName"]
    # 无必填
    assert validate_runtime_dto("RuntimeDataBaseQueryDataReqDto", {}) == []
    # 未登记
    assert "未登记" in validate_runtime_dto("UnknownDto", {})[0]


def test_design_time_vs_runtime_separation():
    # 设计态 /udc/* 与运行态 /udc-runtime/* 不可混；udc-app-info 是元数据面（独立前缀）
    for p in RUNTIME_ENDPOINT_PATHS:
        assert p.startswith(("udc-runtime/", "udc-app-info/")), f"运行态/元数据端点前缀非法: {p}"

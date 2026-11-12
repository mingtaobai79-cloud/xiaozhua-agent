"""应用域 API 模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.application_api_model import (
    APPLICATION_CONTROLLERS, APPLICATION_OPS, application_api_map, application_summary)


def test_all_application_ops_resolve():
    m = application_api_map()
    assert len(m) == len(APPLICATION_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_app_crud_import_export():
    m = application_api_map()
    assert m["应用_创建"]["full_path"] == "/udc/application"
    assert m["应用_导入"]["full_path"] == "/udc/application/import/new"
    assert m["应用_下载包"]["full_path"] == "/udc/application/schema/download/{id}"
    assert m["应用_复制"]["full_path"] == "/udc/application/copy"


def test_deploy_chain():
    m = application_api_map()
    assert m["部署_普通构建"]["full_path"] == "/udc/runtime/deploy-normal"
    assert m["发布_上线"]["full_path"] == "/udc/deployment/app-online"
    assert m["沙箱_构建信息"]["full_path"] == "/udc/sandbox/build-info/{appId}"
    assert m["发布_增量部署"]["full_path"] == "/udc/deployment/app-delta-deploy"


def test_dependency_ops():
    m = application_api_map()
    assert m["依赖_创建"]["full_path"] == "/udc/application/dependent-application/create"
    assert m["依赖_列表按应用"]["full_path"] == "/udc/application/dependent-application/select-by-app-id"


def test_team_and_feature():
    m = application_api_map()
    assert m["应用_角色资源"]["full_path"] == "/udc/application/role-resource"
    assert m["应用_特征按应用"]["full_path"] == "/udc/application/appFeature/{appId}"
    assert m["协作_移交"]["full_path"] == "/udc/collaboration/handover"


def test_summary_eight_controllers():
    s = application_summary()
    assert len(s["controllers"]) == 8
    assert s["controllers"]["ApplicationController"]["api_count"] == 73
    assert s["controllers"]["DeployController"]["api_count"] == 12

"""规则域微流程 API 全集模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_api_model import (
    MICROFLOW_CONTROLLER, MICROFLOW_OPS, microflow_api_map, microflow_coverage)


def test_all_microflow_ops_resolve():
    m = microflow_api_map()
    assert len(m) == len(MICROFLOW_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_microflow_crud_paths():
    m = microflow_api_map()
    assert m["微流程_创建"]["full_path"] == "/udc/microflow/create"
    assert m["微流程_更新"]["full_path"] == "/udc/microflow/update"
    assert m["微流程_按id"]["full_path"] == "/udc/microflow/findById/{id}"
    assert m["微流程_校验并更新"]["full_path"] == "/udc/microflow/checkSchema/update"


def test_microflow_caption_name_check():
    m = microflow_api_map()
    assert m["微流程_caption查重"]["full_path"] == "/udc/microflow/check/micro-flow/caption"
    assert m["微流程_name查重"]["full_path"] == "/udc/microflow/check/micro-flow/name"


def test_order_app_relevant_metadata_queries():
    """订单应用微流程节点构建相关的元数据查询。"""
    m = microflow_api_map()
    assert m["元数据_实体树"]["full_path"] == "/udc/microflow/search/treeEntity"
    assert m["元数据_DTO按实体"]["full_path"] == "/udc/microflow/find/dto-by-entity"
    assert m["元数据_数据体系"]["full_path"] == "/udc/microflow/find/data-system"
    assert m["节点_按条件Schema"]["full_path"] == "/udc/microflow/find/node-schema"
    assert m["调用_下游"]["full_path"] == "/udc/microflow/find/call-info/downstream"
    assert m["节点_连接器服务"]["full_path"] == "/udc/microflow/select-call-connector-app-service/{appId}"


def test_microflow_message_ops():
    m = microflow_api_map()
    assert m["消息_创建"]["full_path"] == "/udc/microflow/create-message"
    assert m["消息_按应用查询"]["full_path"] == "/udc/microflow/search-micro-flow-message/{appId}"


def test_coverage_includes_all_but_test_endpoint():
    c = microflow_coverage()
    assert c["api_count"] == 67
    assert c["unmapped"] == []   # 全方法已被语义目录覆盖（含 entityRef 测试端点）

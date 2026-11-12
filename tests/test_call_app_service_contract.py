"""P6：CALL_APP_SERVICE / 事件触发字段引用的契约测试。

1. starter 服务归属自动推导：com.seeyon.boot.starter.serialnumber.* → boot-starter-serialnumber
2. attrs 支持字段级 attrType 覆盖（parameter 是 SingleRequest<Dto> 时必须字段级）
3. 事件触发（_BUSINESS_EVENT*）字段引用产出 position=children 的 SelectParam
"""
from components.construction.microflow_nodes_svc import call_app_service
from components.construction.node_builder import NodeBuilder

APP, AN = "1", "demo"   # 契约测试不依赖真实应用


def _svc():
    return {"fullName": "com.seeyon.boot.starter.serialnumber.appservice."
                        "SerialNumberAppService.getSerialNumber",
            "implClass": "com.seeyon.boot.starter.serialnumber.appservice.SerialNumberAppService",
            "md5": "413b1d849eaae74b9b1f8e292e4d9fc8",
            "parameter": {"caption": None, "type": "com.seeyon.boot.transport.SingleRequest",
                          "item": {"itemType": "com.seeyon.boot.starter.serialnumber."
                                              "domain.dto.SerialNumberDto"}},
            "returnValue": {"caption": "流水号", "type": "com.seeyon.boot.transport.SingleResponse",
                            "item": {"itemType": "java.lang.String"}}}


def test_starter_app_name_derived():
    node = call_app_service(NodeBuilder(app_id=APP, app_name=AN), "any", [], select_method=_svc())
    assert node["app"]["appName"] == "boot-starter-serialnumber"
    assert node["app"]["inApp"] is False and node["app"]["udcApp"] is False


def test_attr_type_override_kept():
    field_attr = {"name": "serialSchemeCode", "id": "X.serialSchemeCode",
                  "fullName": "X.serialSchemeCode", "dataType": "STRING"}
    node = call_app_service(NodeBuilder(app_id=APP, app_name=AN), "any",
                            [{"attrType": field_attr,
                              "value": {"type": "Simple", "simple": "ZxjContractNo"}}],
                            select_method=_svc())
    assert node["attrs"][0]["attrType"]["name"] == "serialSchemeCode"
    assert node["mappingType"] == "attrs"


def test_output_is_string_for_simple_return():
    node = call_app_service(NodeBuilder(app_id=APP, app_name=AN), "any", [], select_method=_svc())
    assert node["output"]["javaType"] == "java.lang.String"
    assert node["output"]["dataType"] == "STRING"

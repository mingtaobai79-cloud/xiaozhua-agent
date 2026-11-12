"""RED: CALL_APP_SERVICE 节点的「调用配置」必须有本地校验器。

为什么需要：`NODE_REQUIRED_FIELDS['CALL_APP_SERVICE'] = ()` —— 空元组，
等于这类节点在本地模型里完全不校验。而它恰恰是微流程里真正"调服务"的节点：
调错方法名、调错参数载体、入参前缀与参数类型不匹配，平台 checkSchema 都不会报
（已实测为浅校验），只会在运行期失败或静默错。

权威来源（逐字取自 docs/operation-contracts/udc/microflow/cappservice-parameter-semantics.md §5）：
  selectMethod.fullName                  必填；稳定性键；implClass 须为其前缀
  selectMethod.md5                       禁等值比对（同一 fullName 可有多个 md5）
  selectMethod.parameter.type            ∈ {SingleRequest, PageDtoRequest}
  selectMethod.parameter.item.itemType   非空；attrs[].attrType.id 前缀须等于它
  selectMethod.returnValue.type          ∈ {SingleResponse, ListResponse, PageResponse}
  selectMethod.returnValue.item.itemType 非空
  node.mappingType                       等值 "attrs"
  node.output.name                       同流程唯一
  node.input                             实测恒 null，不写

范围声明：本测试只覆盖契约 §5 表里【有硬规则】的字段。标 UNVERIFIED 的
（pageInfo 内部语义、非空壳判据等）不在此断言，避免把未取证当成约束。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_constraints import validate_node_fields

IMPL = "com.seeyon.datamigration9000000000000000001.appservice.XzhExp950795AppServiceImpl"
DTO = "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto"


def _node(**over):
    """一个形态完整的 CALL_APP_SERVICE 节点（对齐契约 §5 逐字段表）。"""
    n = {
        "actionType": "CALL_APP_SERVICE",
        "nodeId": "CALL_APP_SERVICE_abc123",
        "type": "ACTIVITY",
        "caption": "调服务",
        "mappingType": "attrs",
        # app 来自 searchApps 的真实返回（必填）
        "app": {"appId": "9000000000000000001",
                "appName": "datamigration9000000000000000001",
                "caption": "实验应用", "inApp": True, "udcApp": True,
                "dynamicDependency": False},
        "selectMethod": {
            "fullName": IMPL + ".selectById",
            "implClass": IMPL,
            "md5": "3277002066736383209",
            "dubbo": False,
            "isCondition": False,
            "parameter": {"type": "SingleRequest",
                          "item": {"itemType": DTO}},
            "returnValue": {"type": "SingleResponse",
                            "item": {"itemType": DTO}},
        },
        "output": {"id": DTO, "type": "OBJECT", "name": "_CALL_APP_SERVICE_abc123"},
        "attrs": [{"attrType": {"id": DTO + ".name"}, "value": {"expression": "x"}}],
        "input": None,
    }
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(n.get(k), dict):
            merged = dict(n[k])
            merged.update(v)
            n[k] = merged
        else:
            n[k] = v
    return n


def test_complete_call_app_service_node_passes():
    """回归护栏：形态完整的节点不得报错。"""
    errs = validate_node_fields("CALL_APP_SERVICE", _node())
    assert not errs, f"完整节点不应报错: {errs}"


def test_missing_select_method_fullname_is_error():
    """selectMethod.fullName 是唯一稳定匹配键，缺了无法定位服务。"""
    n = _node()
    n["selectMethod"] = {k: v for k, v in n["selectMethod"].items() if k != "fullName"}
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "缺 selectMethod.fullName 必须报错"
    assert any("fullName" in e for e in errs), errs


def test_impl_class_must_be_prefix_of_fullname():
    """implClass 是 fullName 前缀（§2.1：fullName == implClass + '.' + 方法名）。"""
    n = _node()
    n["selectMethod"] = dict(n["selectMethod"], implClass="com.other.NotTheSame")
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "implClass 与 fullName 前缀不一致必须报错"
    assert any("implClass" in e for e in errs), errs


def test_parameter_type_outside_domain_is_error():
    """parameter.type 必须 ∈ {SingleRequest, PageDtoRequest}（§5）。"""
    n = _node()
    n["selectMethod"] = dict(n["selectMethod"],
                             parameter={"type": "BogusRequest",
                                        "item": {"itemType": DTO}})
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "parameter.type 越界必须报错"
    assert any("parameter" in e for e in errs), errs


def test_return_value_type_outside_domain_is_error():
    """returnValue.type 必须 ∈ {SingleResponse, ListResponse, PageResponse}。"""
    n = _node()
    n["selectMethod"] = dict(n["selectMethod"],
                             returnValue={"type": "BogusResponse",
                                          "item": {"itemType": DTO}})
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "returnValue.type 越界必须报错"
    assert any("returnValue" in e for e in errs), errs


def test_item_type_must_be_non_empty():
    """parameter.item.itemType / returnValue.item.itemType 非空（作用域键）。"""
    n = _node()
    n["selectMethod"] = dict(n["selectMethod"],
                             parameter={"type": "SingleRequest", "item": {"itemType": ""}})
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "parameter.item.itemType 为空必须报错"
    assert any("itemType" in e for e in errs), errs


def test_mapping_type_must_be_attrs():
    """mappingType 等值 'attrs'（§5）。"""
    n = _node(mappingType="rows")
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "mappingType != 'attrs' 必须报错"
    assert any("mappingType" in e for e in errs), errs


def test_attr_type_prefix_must_match_parameter_item_type():
    """attrs[].attrType.id 前缀 == parameter.item.itemType（§5 最后一行）。

    这是"入参绑错类型"的直接判据：把 A 类型的字段绑到 B 类型的服务参数上，
    平台不报错，运行期才炸。
    """
    n = _node()
    n["attrs"] = [{"attrType": {"id": "com.other.dto.OtherDto.name"},
                   "value": {"expression": "x"}}]
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert errs, "attrType.id 前缀与 parameter.item.itemType 不符必须报错"
    assert any("attrType" in e for e in errs), errs


def test_md5_absence_is_not_an_error():
    """范围护栏：md5 禁等值比对，缺失不得因此报错（容器条键可缺省）。"""
    n = _node()
    n["selectMethod"] = {k: v for k, v in n["selectMethod"].items() if k != "md5"}
    errs = validate_node_fields("CALL_APP_SERVICE", n)
    assert not [e for e in errs if "md5" in e], f"md5 缺失不应报错: {errs}"

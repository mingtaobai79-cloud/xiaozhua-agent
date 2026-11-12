"""分页参数（PageInfo 变量）与 RETRIEVE_ARRAY 分页接线。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.node_builder import NodeBuilder
from components.construction.microflow_nodes_v2 import (create_variable_page_info,
                                                        retrieve_array)

APP = "1000000000000000001"
AN = "demotenant"
PAGE_INFO = "com.seeyon.boot.transport.PageInfo"


def _builder():
    return NodeBuilder(app_id=APP, app_name=AN)


def test_page_info_variable_shape():
    n = create_variable_page_info(_builder(), page_number=1, page_size=2)
    assert n["paramType"] == "OTHER"
    assert n["otherType"] == "SYSTEM_PAGE_INFO"
    assert n["dataType"] == "DTO"
    assert n["mappingType"] == "attrs"
    assert [a["attrType"]["name"] for a in n["attrs"]] == ["pageNumber", "pageSize", "needTotal"]
    assert n["attrs"][1]["value"]["simple"] == 2
    assert n["output"]["id"] == PAGE_INFO
    assert n["output"]["javaType"] == PAGE_INFO


def test_page_info_values_are_simple_constants():
    n = create_variable_page_info(_builder(), page_number=3, page_size=50,
                                  need_total=False)
    vals = {a["attrType"]["name"]: a["value"] for a in n["attrs"]}
    assert vals["pageNumber"]["type"] == "Simple"
    assert vals["pageNumber"]["simple"] == 3
    assert vals["pageSize"]["simple"] == 50
    assert vals["needTotal"]["simple"] is False


def test_retrieve_array_paging_sets_page_search_and_select_param():
    """pageSearch 是字符串 "true"；selectParam 少填属性平台会 PROPERTY_IS_REQUIRED。"""
    b = _builder()
    pg = create_variable_page_info(b, page_size=2)
    pg["nodeId"] = "PGNODE1"
    ent = {"fullName": "x.Dto", "entity": "Demo", "caption": "演示",
           "relationEntityId": "123"}
    n = retrieve_array(b, entity=ent, cond_field="",
                       right_value=None, page_info_node=pg)
    assert n["pageSearch"] == "true"
    sp = n["pageInfo"]["selectParam"]
    for k in ("type", "dataType", "dtoType", "udcApp", "appName", "javaType",
              "path", "desc", "outputName", "id"):
        assert sp.get(k), "pageInfo.selectParam 缺 %s（会 PROPERTY_IS_REQUIRED）" % k
    assert sp["type"] == "OBJECT"
    assert sp["dtoType"] == "CUSTOM"

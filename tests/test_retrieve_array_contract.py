"""RETRIEVE_ARRAY 出参契约 + 列表操作取元素的回归测试。

语料（另一应用 643 条 RELEASE 流程）里的硬事实：

RETRIEVE_ARRAY 217 条样本按 fetchType 的出参形态：
    CONDITION → ARRAY / DTO   184
    IDS       → ARRAY / DTO    19
    COUNT     → OBJECT / INTEGER 13
    OTHERS    → OBJECT / DECIMAL  1
→ **只要是取记录，就一定是 ARRAY**；OBJECT 只出现在 COUNT/OTHERS 这类聚合。
  单条记录也不会降级成 OBJECT（平台按 fetchType 决定，不按行数）。

LIST_OPERATION 654 条样本：
    FIRST_ONE/LAST_ONE/PICK_ONE → OBJECT（元素）
    SIZE/MIN/MAX/SUM            → OBJECT 标量
    FILTER/SORT/DISTINCT/MAP…   → ARRAY
早期构造器把出参一律写死 INTEGER，取元素造不出来（P5-S2 踩到）。
"""
import json

from components.construction.microflow_nodes_extra import list_operation
from components.construction.microflow_nodes_v2 import retrieve_array
from components.udc.microflow.expression_refs import ReferenceResolver

ENTITY = {
    "caption": "迁移断点",
    "fullName": "com.seeyon.x.dto.MigrationCheckpointDto",
    "entity": "com.seeyon.x.domain.entity.MigrationCheckpoint",
    "relationEntityId": "1",
    "attributes": {
        "taskId": {"name": "taskId", "dataType": "STRING", "javaType": "java.lang.String",
                   "id": "com.seeyon.x.dto.MigrationCheckpointDto.taskId", "caption": "任务ID"},
        "sourceTable": {"name": "sourceTable", "dataType": "STRING",
                        "javaType": "java.lang.String",
                        "id": "com.seeyon.x.dto.MigrationCheckpointDto.sourceTable",
                        "caption": "源表"},
    },
}


class _B:
    app_name = "app"

    def build(self, action_type, caption=None):
        return {"nodeId": action_type + "_t1", "type": "ACTIVITY",
                "actionType": action_type, "caption": caption}

    def _app_ref(self):
        return {"appId": "1", "appName": "app", "caption": "app",
                "inApp": True, "udcApp": True, "dynamicDependency": False}

    def output_name(self, node):
        return (node.get("output") or {}).get("name")


# ── RETRIEVE_ARRAY 出参 ─────────────────────────────────────────────────────
def test_retrieve_array_outputs_array_of_dto():
    n = retrieve_array(_B(), ENTITY, "taskId", {"type": "CONSTANT", "value": "X"})
    o = n["output"]
    assert o["type"] == "ARRAY", "取记录必须是 ARRAY，单条也不降级"
    assert o["dataType"] == "DTO"
    assert o["id"] == ENTITY["fullName"]
    assert o["javaType"] == ENTITY["fullName"]


def test_retrieve_array_has_condition_group():
    n = retrieve_array(_B(), ENTITY, "taskId", {"type": "CONSTANT", "value": "X"})
    assert isinstance(n.get("condition"), list) and n["condition"]
    assert n["condition"][0]["type"] == "GROUP"
    cond = n["condition"][0]["conditions"][0]
    assert cond["type"] == "CONDITION"
    assert cond["leftParam"]["field"] == "taskId"


# ── LIST_OPERATION 出参随操作走 ─────────────────────────────────────────────
SRC = {"nodeId": "RETRIEVE_ARRAY_t1", "output": {"id": ENTITY["fullName"], "javaType": ENTITY["fullName"],
                  "type": "ARRAY", "dataType": "DTO",
                  "dtoType": "MASTER_ENTITY", "appName": "app",
                  "udcApp": True, "name": "_RETRIEVE_ARRAY_t1"}}


def test_size_returns_integer_object():
    n = list_operation(_B(), SRC, op_type="SIZE", title="数量")
    assert n["output"]["type"] == "OBJECT"
    assert n["output"]["dataType"] == "INTEGER"
    assert n["output"]["javaType"] == "java.lang.Integer"


def test_first_one_returns_element_dto():
    n = list_operation(_B(), SRC, op_type="FIRST_ONE", title="第一个")
    o = n["output"]
    assert o["type"] == "OBJECT"
    assert o["dataType"] == "DTO"
    assert o["id"] == ENTITY["fullName"], "元素出参要带 DTO 全名，字段引用才解析得了"
    assert o["name"].startswith("_LIST_OPERATION")


def test_last_one_and_pick_one_also_element():
    for op in ("LAST_ONE", "PICK_ONE"):
        n = list_operation(_B(), SRC, op_type=op, title="x")
        assert n["output"]["dataType"] == "DTO"


# ── 没有 structure 的元素节点也能解析字段 ───────────────────────────────────
class _FakeRefs:
    def entity_model(self, app_id, app_name=None, *, label="", dto_full=""):
        return {"attributes": ENTITY["attributes"]}


def test_lookup_field_resolves_from_output_id_without_structure():
    res = ReferenceResolver("1", "app", live_refs=_FakeRefs())
    meta = res._lookup_field({"output": {"id": ENTITY["fullName"]}}, "sourceTable")
    assert meta["dataType"] == "STRING"
    assert meta["id"].endswith(".sourceTable")
    assert meta["caption"] == "源表"


def test_lookup_field_still_prefers_structure():
    res = ReferenceResolver("1", "app", live_refs=_FakeRefs())
    node = {"structure": {"id": ENTITY["fullName"]},
            "output": {"id": "com.other.Dto"}}
    meta = res._lookup_field(node, "taskId")
    assert meta["id"].endswith(".taskId")

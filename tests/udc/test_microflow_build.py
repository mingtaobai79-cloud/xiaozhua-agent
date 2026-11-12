"""微流程生成器的结构断言。

约定来自全库取证（含 1.7MB 真实微流程），不是猜的：
- 顶层固定 6 键，且**没有 flowPaths**
- 执行顺序 = nodes 数组顺序，runAfter 恒 null
- 分支 = conditions[].nodes 嵌套，name ∈ ifBranch / elseIfBranch / elseBranch
- 出参名 = _<actionType>_<6位>，开始节点 = _FLOW_INPUT_<6位>
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.udc.microflow.build import (  # noqa: E402
    TOP_KEYS, branch, build_schema, make_node, node_id, param, validate_schema,
)


def test_top_keys_exact():
    s = build_schema({"nodes": []}, app_id="x")
    assert tuple(s.keys()) == TOP_KEYS
    assert "flowPaths" not in s


def test_no_run_after_on_nodes():
    n = make_node("CUSTOM_ERROR", error="x", errorType="ERROR")
    assert n["runAfter"] is None
    assert "conditions" not in n


def test_node_id_and_output_name_share_suffix():
    n = make_node("RETRIEVE")
    suffix = n["nodeId"].rsplit("_", 1)[-1]
    p = param("_RETRIEVE_%s" % suffix, "ENTITY", "账单")
    assert n["nodeId"].startswith("RETRIEVE_")
    assert p["name"] == "_RETRIEVE_%s" % suffix


def test_param_java_type_mapping():
    assert param("x", "BIGINTEGER")["javaType"] == "java.lang.Long"
    assert param("x", "STRING")["javaType"] == "java.lang.String"
    assert param("x", "ENTITY")["hasPagination"] is False


def test_input_name_prefix():
    s = build_schema({"input": {"desc": "入参", "dataType": "STRING"}, "nodes": []},
                     app_id="x")
    assert s["input"]["name"].startswith("_FLOW_INPUT_")
    assert s["trigger"]["output"] is s["input"]


def test_branch_auto_appends_else():
    b = branch([{"expr": {"title": "x"}, "nodes": []}])
    assert [c["name"] for c in b["conditions"]] == ["ifBranch", "elseBranch"]
    assert b["conditions"][-1]["expression"] is None


def test_branch_case_names():
    b = branch([
        {"expr": {"title": "a"}, "nodes": []},
        {"expr": {"title": "b"}, "nodes": []},
        {"expr": None, "nodes": []},
    ])
    assert [c["name"] for c in b["conditions"]] == ["ifBranch", "elseIfBranch", "elseBranch"]


def test_branch_nested_nodes_preserved():
    inner = make_node("CUSTOM_ERROR", error="e", errorType="WARN")
    b = branch([{"expr": None, "nodes": [inner]}])
    assert b["conditions"][0]["nodes"][0]["nodeId"] == inner["nodeId"]


def test_validate_catches_missing_required():
    """RETRIEVE 缺选择器字段 / CHANGE_ENTITY 缺 selectParam 必须被拦。"""
    s = build_schema({"nodes": [make_node("RETRIEVE"),
                                make_node("CHANGE_ENTITY")]}, app_id="x")
    errs = validate_schema(s)
    assert any("structure" in e for e in errs)
    assert any("selectParam" in e for e in errs)


def test_validate_rejects_extra_top_key():
    s = build_schema({"nodes": []}, app_id="x")
    s["flowPaths"] = []
    errs = validate_schema(s)
    assert any("flowPaths" in e for e in errs)


def test_validate_ok_for_minimal_error_node():
    s = build_schema({"nodes": [make_node("CUSTOM_ERROR", error="e", errorType="ERROR")]},
                     app_id="x")
    assert validate_schema(s) == []


def test_node_id_unique_enough():
    ids = {node_id("RETRIEVE") for _ in range(50)}
    assert len(ids) > 45

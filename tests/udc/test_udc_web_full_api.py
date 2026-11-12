"""udc-web 完整 RESTful API 契约测试（方法级 path 全量机器化）。

数据源：docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json
（类级路径 + 方法级 http/path/描述；udc-web-5.3.517.jar javap -v，STATIC_BYTECODE）。
与 components.udc.function_node_model.FUNCTION_ENDPOINTS 等手录路径交叉核对。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

_F = ROOT / "docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json"


def _load():
    return json.loads(_F.read_text(encoding="utf-8"))


def _paths(ctrl):
    return {m["method"]: (m["http"], m["full_path"]) for m in _load()[ctrl]["methods"]}


def test_full_contract_shape():
    d = _load()
    assert len(d) == 54
    tot = sum(v["api_count"] for v in d.values())
    assert tot == 674
    with_desc = sum(1 for v in d.values() for m in v["methods"] if m["desc"])
    assert with_desc >= 650   # 中文描述几乎全覆盖


def test_entity_controller_full_paths():
    p = _paths("EntityController")
    assert p["create"] == ("POST", "/udc/entity")
    assert p["update"] == ("POST", "/udc/entity/update")
    assert p["deleteById"] == ("POST", "/udc/entity/delete")
    assert p["selectById"] == ("GET", "/udc/entity/{id}")
    assert p["selectParentById"] == ("GET", "/udc/entity/{id}/parent")
    assert p["selectListByTerm"] == ("POST", "/udc/entity/search/term")


def test_function_node_paths_match_recorded_endpoints():
    """与 function_node_model.FUNCTION_ENDPOINTS 手录路径交叉核对。"""
    p = _paths("FunctionNodeController")
    assert p["createFunction"] == ("POST", "/udc/function")
    assert p["createFunctionRefer"] == ("POST", "/udc/function/create/function-refer")
    assert p["updateFunctionRefer"] == ("POST", "/udc/function/update/function-refer")
    assert p["selectFunctionTree"] == ("POST", "/udc/function/select/function-tree")
    assert p["findMenuTree"] == ("POST", "/udc/function/find/tree-and-group")
    assert p["setFunctionDefaultPage"] == ("POST", "/udc/function/default_page")
    assert p["findPageInParams"] == ("GET", "/udc/function/page/in_params/{referId}")


def test_refer_config_paths():
    p = _paths("ReferConfigController")
    assert p["createConfigInfo"] == ("POST", "/udc/refer-config/create-config-info")
    assert p["updateConfigInfo"] == ("POST", "/udc/refer-config/update-config-info")


def test_every_api_has_http_verb():
    d = _load()
    for ctrl, v in d.items():
        for m in v["methods"]:
            assert m["http"] in ("GET", "POST", "PUT", "DELETE", None), (ctrl, m)

# ---------------------------------------------------------------------------
# 回归护栏：full_path = 类级 mapping + 方法级 value **恒拼接**（Spring 语义）
# ---------------------------------------------------------------------------
def test_class_level_mapping_is_always_concatenated():
    """方法级 value 以 "/" 开头也**不是**绝对路径（Spring 从不这样解析）。

    历史缺陷（tools/core/decompile/merge_udc_web_api.py）：曾把 "/xxx" 当绝对路径并前置 "/udc"，
    使 657 方法中 159 个（24.2%）full_path 错，并造出线上不存在的 op。
    字节码：PageInfoController 类级 @RequestMapping("udc/page-info")
            + 方法级 @PostMapping("/base-info/create")
            → 真路径 /udc/page-info/base-info/create
    LIVE 佐证：components/udc/live_write_templates.py 的 page_create 实例
            POST /service/udc/page-info/base-info/create 在线创建成功。
    """
    p = _paths("PageInfoController")
    assert p["createBaseInfo"] == ("POST", "/udc/page-info/base-info/create")
    assert p["batchCreateBaseInfo"] == ("POST", "/udc/page-info/base-info/batch-create")
    assert p["updateBaseInfo"] == ("POST", "/udc/page-info/base-info/update")
    assert p["updateDesignerVersion"] == (
        "POST", "/udc/page-info/base-info/update/designer/version")


def test_no_full_path_drops_its_class_mapping():
    """全量护栏：任何方法的 full_path 都必须以其类的 class_mapping 为前缀。

    方法级 value 以 "/" 开头、类级 mapping 非空时，路径必须形如
    "/<class_mapping>/<value 去前导斜杠>"——不允许退化成 "/udc/<value>"。
    """
    d = _load()
    offenders = []
    for ctrl, v in d.items():
        base = (v.get("class_mapping") or "").strip("/")
        if not base:
            continue
        for m in v["methods"]:
            frag = (m["path"] or "").lstrip("/")
            expected = "/" + base + "/" + frag if frag else "/" + base
            if m["full_path"] != expected:
                offenders.append((ctrl, m["method"], m["full_path"], expected))
    assert not offenders, f"类级 mapping 未拼接: {offenders[:5]}"


def test_absolute_path_regression_is_gone():
    """负面护栏：曾由缺陷造出的"看似合法但线上不存在"的路径不得复活。"""
    p = _paths("PageInfoController")
    assert p["createBaseInfo"][1] != "/udc/base-info/create"
    assert p["selectDetailsById"][1] != "/udc/detail/{id}"
    assert _paths("PortletController")["createPortlet"][1] != "/udc/create-portlet"
    assert _paths("PageTemplateController")["publish"][1] != "/udc/publish"
    assert _paths("MicroFlowController")["selectPageByCondition"][1] != "/udc/search-no-page"
    assert _paths("AppCollaborationController")["handoverApp"][1] != "/udc/handover"

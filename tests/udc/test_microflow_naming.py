"""op 名 / 类型名生成规则（对齐 boot-starter-graphql 反编译实现）。"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from components.udc.microflow.read import path_to_op_name, type_name  # noqa: E402


# ── op 名：LIVE 验证过的四个 ──
def test_service_list_op():
    assert path_to_op_name("/udc/microflow/serviceList", "POST") == "udcMicroflowServiceListPost"


def test_search_apps_op():
    assert path_to_op_name("/udc/microflow/searchApps", "POST") == "udcMicroflowSearchAppsPost"


def test_search_app_service_by_name_op():
    assert path_to_op_name("/udc/microflow/searchAppServiceByName", "POST") == \
        "udcMicroflowSearchAppServiceByNamePost"


def test_disable_node_op():
    assert path_to_op_name("/udc/microflow/disableNode", "POST") == "udcMicroflowDisableNodePost"


def test_get_method_uses_lowercase_suffix():
    # pathToCamel 里 httpMethod 是 toLowerCase() 后拼上去的
    assert path_to_op_name("/udc/microflow/serviceList", "GET") == "udcMicroflowServiceListGet"


def test_path_param_braces_removed():
    assert path_to_op_name("/udc/entity/{id}", "GET") == "udcEntityGet"


def test_trailing_id_rule_is_effectively_unreachable():
    """`Id$` 在 path+" /post" 的拼法下几乎不可达 —— 结尾永远是 httpMethod。

    保留这条是为了把「规则存在但打不到」这件事写进测试，避免后人误解。
    真能打到 Id 结尾的只有 httpMethod 为空的情况。
    """
    assert path_to_op_name("/udc/microflow/serviceListId", "POST") == "udcMicroflowServiceListIdPost"


def test_id_get_becomes_get():
    # ★ 真正生效的是 IdGet$：{id} 去花括号后 + /get 得 "...IdGet"
    assert path_to_op_name("/udc/microflow/query/{id}", "GET") == "udcMicroflowQueryGet"


def test_search_post_becomes_search():
    # path 以 ".../search" + "/post" 拼成 SearchPost 才触发
    assert path_to_op_name("/udc/microflow/search", "POST") == "udcMicroflowSearch"


def test_hyphen_and_underscore_are_delimiters():
    assert path_to_op_name("/udc/micro-flow/do_it", "POST") == "udcMicroFlowDoItPost"


# ── 类型名：LIVE 报错原文验证 ──
def test_type_name_matches_live_error():
    got = type_name("com.seeyon.udc.microflow.dto.definition.MicroFlowSubMfDto", "udc")
    assert got == "UdccomseeyonudcmicroflowdtodefinitionMicroFlowSubMfDto"


def test_type_name_input_body_suffix():
    got = type_name("com.x.FooDto", "udc", is_input=True)
    assert got == "UdccomxFooDtoInputBody"


def test_type_name_app_name_camel():
    # appName 里的 '-' 会被 toCamelCase 消掉并大写下一个字母
    got = type_name("com.x.FooDto", "my-app")
    assert got == "MyAppcomxFooDto"


def test_type_name_strips_non_alnum():
    assert "!" not in type_name("com.x.Foo$Dto", "udc")

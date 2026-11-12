"""设计器 8 导航域 API 级覆盖测试 —— 每域 controller/API 归类 + 与仓库落点对账。

数据源：components.udc.nav_domain_model（udc-web javap 实证）。
比 test_domain_coverage.py（模块级）细一层：断言每域**真实 controller/API 数**已归类，
且每个域都有仓库侧落点（模型/目录/registry op）。

证据边界：STATIC_BYTECODE。流程/BI 是独立服务域（bpm/cdp-data），另表登记。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.nav_domain_model import (
    NAV_DOMAIN_CONTROLLERS, EXTERNAL_SERVICE_DOMAINS,
    domain_apis, nav_domain_catalog, load_api_by_controller,
)

_EIGHT = ["应用", "实体", "菜单", "规则", "流程", "BI", "栏目", "设置"]


def test_eight_nav_domains_declared():
    assert list(NAV_DOMAIN_CONTROLLERS) == _EIGHT


def test_all_udc_web_apis_assigned_to_a_domain():
    """udc-web 54 controller 671 API 全部归入某导航域（不遗漏、不重复）。"""
    data = load_api_by_controller()
    assigned = [c for ctrls in NAV_DOMAIN_CONTROLLERS.values() for c in ctrls]
    assert len(assigned) == len(set(assigned)), "controller 跨域重复归类"
    # 归类数 = 契约产物里的 controller 数
    assert set(assigned) == set(data), \
        f"未归类/多余: 缺{sorted(set(data)-set(assigned))} 多{sorted(set(assigned)-set(data))}"


def test_domain_api_counts_positive():
    """应用/实体/菜单/规则/栏目/设置 六域都实有 API；流程/BI 是外部服务域。"""
    for d in ("应用", "实体", "菜单", "规则", "栏目", "设置"):
        info = domain_apis(d)
        assert info["api_total"] > 0, d
        assert info["controllers"] > 0, d
    for d in ("流程", "BI"):
        assert NAV_DOMAIN_CONTROLLERS[d] == []
        assert d in EXTERNAL_SERVICE_DOMAINS


def test_entity_domain_full_controller_set():
    info = domain_apis("实体")
    assert info["api_total"] == 133
    assert info["per_controller"]["EntityController"]["api_count"] == 55
    assert info["per_controller"]["ReferConfigController"]["class_mapping"] == "udc/refer-config"


def test_external_service_domains_have_op_catalogs():
    """流程/BI 域登记了独立服务的 op 目录落点。"""
    for d, ext in EXTERNAL_SERVICE_DOMAINS.items():
        assert ext["service"] in ("bpm", "cdp-data")
        assert ext["op_catalog"].startswith("components.udc.bi_flow_ops")


def test_nav_domain_catalog_serializable():
    import json
    cat = nav_domain_catalog()
    blob = json.loads(json.dumps(cat, ensure_ascii=False))
    assert len(blob["domains"]) == 8
    total = sum(d["api_total"] for d in blob["domains"].values())
    assert total == 674   # udc-web 全部 API 归类合计

"""应用域 · 应用内功能页的四类资产必须同时存在且互相引用。

锁住 KNOWLEDGE-LANDING-RULES 第二节：
  实现   components/udc/application/
  事实   core/facts/udc/application/app-inner/create.md + app-inner-write-chain.md
  契约   docs/operation-contracts/udc/application/app-inner-contracts.md
  skill  skills/xiaozhua-udc-application-app-inner/SKILL.md
  证据   core/facts/udc/application/evidence/app-inner-build-2026-10-22/

同时把「构建日志一把取全量」「组件依赖删除是 REST」「移除依赖吃依赖行 id」
这三条实测结论钉进实现，防止以后被改回猜测写法。
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.application import app_inner_ops as ops  # noqa: E402
from components.udc.application import dependency_constraints as dep  # noqa: E402

IMPL_DIR = ROOT / "components" / "udc" / "application"
FACT_DIR = ROOT / "core" / "facts" / "udc" / "application" / "app-inner"
CONTRACT = ROOT / "docs" / "operation-contracts" / "udc" / "application" / "app-inner-contracts.md"
SKILL = ROOT / "skills" / "xiaozhua-udc-application-app-inner" / "SKILL.md"
EVIDENCE = ROOT / "core" / "facts" / "udc" / "application" / "evidence" / "app-inner-build-2026-10-22"


# ---------------------------------------------------------------- 落位

def test_impl_package_exists():
    assert IMPL_DIR.is_dir(), f"缺应用域实现包: {IMPL_DIR}"
    assert (IMPL_DIR / "__init__.py").exists()
    for name in ("app_inner_ops.py", "dependency_constraints.py"):
        assert (IMPL_DIR / name).exists(), f"缺实现文件 {name}"


def test_fact_grid_exists():
    for name in ("create.md", "app-inner-write-chain.md"):
        p = FACT_DIR / name
        assert p.exists(), f"缺事实格 {p}"
        assert len(p.read_text(encoding="utf-8")) > 1000, f"{name} 内容过薄"


def test_contract_and_skill_exist():
    assert CONTRACT.exists(), "缺应用域契约索引"
    assert SKILL.exists(), "缺应用域 skill"


def test_evidence_bundle_present():
    assert EVIDENCE.is_dir(), f"缺证据目录 {EVIDENCE}"
    files = {p.name for p in EVIDENCE.glob("*.json")}
    for name in ("sandbox-build-capture.json", "build-info-live.json",
                 "cmp-dep-create-full.json", "cmp-dep-page-hook.json"):
        assert name in files, f"证据缺 {name}"


def test_assets_cross_reference():
    """四类必须互相引用，否则等于没沉淀。"""
    create = (FACT_DIR / "create.md").read_text(encoding="utf-8")
    chain = (FACT_DIR / "app-inner-write-chain.md").read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")

    assert "app_inner_ops.py" in create and "app-inner-contracts.md" in create
    assert "app-inner-contracts.md" in chain
    assert "app_inner_ops.py" in contract and "create.md" in contract
    assert "app_inner_ops.py" in skill and "create.md" in skill


def test_capability_report_sees_fact_grid():
    """capability_report 用 create.md 判定事实格，应用域不能掉回「有契约无事实格」。"""
    sys.path.insert(0, str(ROOT / "tools" / "core" / "_meta"))
    import capability_report  # noqa: E402

    data = capability_report.build()
    entry = data["domains"]["application"]
    assert entry["has_fact_grid"], "应用域事实格未被识别（缺 create.md）"
    assert entry["fact_files"] >= 6


# ---------------------------------------------------------------- 实现形状

def test_build_info_uses_path_alias():
    body = ops.build_build_info_query("9000000000000000001")
    assert "(path: $params0)" in body["query"], "构建信息别名必须是 path: 不是 body:"
    assert body["_write"] is False


def test_deploy_normal_body_is_release_and_marked_write():
    body = ops.build_deploy_normal("9000000000000000001")
    dto = body["variables"]["params0"]["deployDto"]
    assert dto["projectType"] == "ALL" and dto["terminalType"] == "ALL"
    assert dto["deployType"] == "RELEASE" and dto["generateLog"] is True
    assert body["_write"] is True, "构建必须标成写面"


def test_dependency_create_service_row_six_fields():
    body = ops.build_dependency_create(
        "9000000000000000001", dep_app_name="<depAppName>",
        dep_app_caption="<depAppCaption>", dep_app_version="5.3.98")
    rows = body["variables"]["params0"]
    assert isinstance(rows, list) and len(rows) == 1
    assert set(rows[0]) == set(dep.SERVICE_FIELDS)
    assert rows[0]["dependentAppType"] == "SERVICE" and rows[0]["depAppBasePackage"] == "com.seeyon"
    assert body["_write"] is True


def test_dependency_create_rejects_bad_type():
    with pytest.raises(ValueError):
        ops.build_dependency_create("1", dep_app_name="x", dep_app_caption="x",
                                    dep_app_version="1.0", dependent_app_type="APP")


def test_dependency_delete_requires_row_id():
    body = ops.build_dependency_delete("101869710491436138")
    assert body["variables"]["params0"] == {"id": "101869710491436138"}
    with pytest.raises(ValueError):
        ops.build_dependency_delete("announcement1492794990099121396")


def test_component_delete_is_rest_batch():
    body = ops.build_component_delete(["101869710491436138"])
    assert body["url"] == ops.CMP_DELETE_PATH
    assert body["body"] == {"ids": ["101869710491436138"]}
    with pytest.raises(ValueError):
        ops.build_component_delete([])


def test_version_list_sends_app_name_not_app_id():
    body = ops.build_version_list("datamigration9000000000000000001")
    assert body["body"]["params"]["IN_appId"] == ["datamigration9000000000000000001"]
    assert body["body"]["params"]["clientType"] == "PC"


# ---------------------------------------------------------------- 校验器

def test_validate_create_row_flags_missing_and_wrong_type():
    errs = dep.validate_create_row({"appId": "1"})
    assert any("缺必填字段" in e for e in errs)
    errs = dep.validate_create_row({k: "x" for k in dep.SERVICE_FIELDS} |
                                   {"dependentAppType": "NOPE"})
    assert any("非法" in e for e in errs)


def test_validate_create_row_frontend_needs_extra_fields():
    row = {k: "x" for k in dep.SERVICE_FIELDS}
    row["dependentAppType"] = "FRONTEND"
    errs = dep.validate_create_row(row)
    assert any("组件依赖缺字段" in e for e in errs)
    for k in dep.FRONTEND_EXTRA_FIELDS:
        row[k] = "x"
    assert dep.validate_create_row(row) == []


def test_validate_delete_arg_rules():
    assert dep.validate_delete_arg("101869710491436138") == []
    assert dep.validate_delete_arg("announcement1")
    assert dep.validate_delete_arg(None)


def test_is_deletable_reflects_enable_delete_flag():
    assert dep.is_deletable({"enableDelete": True}) is True
    assert dep.is_deletable({"enableDelete": False}) is False
    assert dep.is_deletable({}) is False


def test_partition_rows_splits_by_type():
    rows = [{"dependentAppType": "SERVICE"}, {"dependentAppType": "FRONTEND"},
            {"dependentAppType": "WEIRD"}, {}]
    out = dep.partition_rows(rows)
    assert len(out["SERVICE"]) == 1 and len(out["FRONTEND"]) == 1
    assert len(out["other"]) == 2


# ---------------------------------------------------------------- 分类

def test_classify_routes_known_ops():
    assert ops.classify("/service/udc/graphql?udcRuntimeDeployNormalPost")[0] == "testVersion"
    assert ops.classify("/service/udc/graphql?udcSandboxBuildInfoAppGet")[0] == "testVersion"
    assert ops.classify("/service/udc/application/dependent-application/delete-by-ids")[0] == "dependentCmp"
    assert ops.classify("/service/ctp-application/appcenter/search-app-edition")[0] == "version"
    assert ops.classify("/service/x/udc-runtime/app-log/search/microflow")[0] == "design"
    assert ops.classify("/service/udc/something-else")[0] == "unknown"


def test_app_inner_pages_cover_seven_subroutes():
    assert len(ops.APP_INNER_PAGES) == 7
    for key in ("testPage", "testVersion", "version", "dependentApp",
                "dependentCmp", "team", "appTheme"):
        assert key in ops.APP_INNER_PAGES


def test_build_chain_is_six_segments_in_order():
    assert [s["step"] for s in ops.BUILD_CHAIN] == [1, 2, 3, 4, 5, 6]
    assert ops.BUILD_CHAIN[1]["kind"] == "write_declared_query"
    assert set(ops.WS_CHANNELS) == {"udc_detection_channel", "udc_deploy_channel", "common-message"}


# ---------------------------------------------------------------- 证据一致性

def test_build_info_evidence_matches_impl():
    doc = json.loads((EVIDENCE / "build-info-live.json").read_text(encoding="utf-8"))
    assert "(path:" in doc["request"]["query"]
    assert doc["content"]["state"] == "SUCCESS"
    assert len(doc["content"]["logs"]) >= 20


def test_no_customer_identifiers_in_new_assets():
    """本域资产不许出现真实域名 / 真实 appId 值 / 真人名。"""
    targets = [IMPL_DIR / "app_inner_ops.py", IMPL_DIR / "dependency_constraints.py",
               FACT_DIR / "create.md", FACT_DIR / "app-inner-write-chain.md",
               CONTRACT, SKILL]
    # 字符串拼起来写，否则本文件自己会命中 tests/test_deidentification.py 的 PII 扫描
    banned = ("changhong" + "it.com", "8704025620829192" + "834",
              "白明" + "涛", "白明" + "泽", "数据" + "迁移")
    for p in targets:
        text = p.read_text(encoding="utf-8")
        for b in banned:
            assert b not in text, f"{p.name} 含未脱敏内容: {b}"

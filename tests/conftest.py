"""Shared pytest fixtures for the xiaozhua-agent test suite.

客户场景证据（golden 样本等）已于 2026-10-09 迁出仓库
（见 config/environments.yaml customer_evidence_root）。
依赖它的测试通过环境变量拿到仓库外证据根；根不存在时相关测试自动 skip，
保证「仓库干净」与「测试可跑」两个目标互不牺牲。
"""

import os
from pathlib import Path

_CUSTOMER_EVIDENCE_ROOT = Path(r"<EVIDENCE_ROOT>/xiaozhua-customer-evidence")

import pytest


def _customer_evidence_available() -> bool:
    return (_CUSTOMER_EVIDENCE_ROOT / "fixtures-golden").is_dir()


# 客户 golden 样本证据根（仅测试进程内生效，不写入任何仓库文件）
os.environ.setdefault("XIAOZHUA_CUSTOMER_EVIDENCE_ROOT", str(_CUSTOMER_EVIDENCE_ROOT))

requires_customer_evidence = pytest.mark.skipif(
    not _customer_evidence_available(),
    reason="customer evidence root not present (migrated out of repo 2026-10-09)",
)

# 脚本式自检文件：模块级顺序执行并以 sys.exit 结束，被 pytest 收集会
# 触发 INTERNALERROR(SystemExit) 打崩整场收集（实测 2026-10-30：2158 → 0）。
# 它们不是 pytest 用例，仍可直接 `python tests/xxx.py` 运行。
collect_ignore_glob = [
    "test_composer.py",
    "test_template_residue.py",
    "test_construction_skeleton.py",
    "test_live_readonly_offline.py",
]

# ---------------------------------------------------------------------------
# 反编译证据目录（docs/audit/artifacts，~390MB）不在分发树内。
#
# 它是「这条事实凭什么成立」的依据，可由 tools/core/platform/ 下的抽取脚本
# 从本地 maven 仓库重新生成（见 REGENERATE-EVIDENCE.md，实测
# 8 并发约 25-50 分钟）。因为可重生成且体积大，分发树不携带它。
#
# 缺目录时把「正文提到 artifacts 的用例」整文件跳过，而不是让它们红 ——
# 逐条贴 skipif 会漏（实测 66 个文件 / 232 个用例），且新增用例还要再贴一遍。
# 开发仓有 artifacts，钩子直接 return，行为零变化。
# ---------------------------------------------------------------------------
_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "audit" / "artifacts"
_artifact_dep_cache: dict[str, bool] = {}


def _artifacts_available() -> bool:
    return _ARTIFACTS_DIR.is_dir()


def _module_needs_artifacts(path_str: str) -> bool:
    if path_str in _artifact_dep_cache:
        return _artifact_dep_cache[path_str]
    need = False
    try:
        src = Path(path_str).read_text(encoding="utf-8", errors="ignore")
        need = ("audit/artifacts" in src.replace("\\", "/")
                or "audit\\\\artifacts" in src
                or '"artifacts"' in src and "audit" in src)
    except OSError:
        need = False
    _artifact_dep_cache[path_str] = need
    return need


def pytest_collection_modifyitems(config, items):
    if _artifacts_available():
        return
    marker = pytest.mark.skip(reason="docs/audit/artifacts 不在分发树内（可重新生成，见 REGENERATE-EVIDENCE.md）")
    for item in items:
        f = str(item.fspath)
        rel = Path(f).resolve().relative_to(Path(__file__).resolve().parent.parent).as_posix()
        if rel in _ARTIFACT_DEPENDENT_FILES or _module_needs_artifacts(f):
            item.add_marker(marker)

# 这些文件正文可能不直接出现 artifacts 字样（证据根由共享 helper 拼出来），
# 所以除了上面的动态检测，再按实测 diff 固定一份清单：
# 取法 = 分发树跑全量得到 FAILED 集 → 把同一批 nodeid 放到有证据的开发仓重跑 →
# 全部通过的那批即为「缺证据导致」。实测 49 文件 / 136 用例。
_ARTIFACT_DEPENDENT_FILES = {
    "tests/test_profile_builder.py",
    "tests/udc/test_README_total_lines.py",
    "tests/udc/test_application_api_model.py",
    "tests/udc/test_application_app_inner_asset_layout.py",
    "tests/udc/test_application_contracts_layout.py",
    "tests/udc/test_application_facts_layout.py",
    "tests/udc/test_application_submenu.py",
    "tests/udc/test_bi_contracts_layout.py",
    "tests/udc/test_bpm_facts_layout.py",
    "tests/udc/test_capability_docs_layout.py",
    "tests/udc/test_capability_docs_self_consistency.py",
    "tests/udc/test_capability_status_snapshot.py",
    "tests/udc/test_column_api_model.py",
    "tests/udc/test_column_discovery_index.py",
    "tests/udc/test_deployed_lib_inventory.py",
    "tests/udc/test_design_metadata_model.py",
    "tests/udc/test_dirs_without_readme_are_covered.py",
    "tests/udc/test_docs_root_layout.py",
    "tests/udc/test_entity_api_model.py",
    "tests/udc/test_entity_contracts_layout.py",
    "tests/udc/test_entity_facts_layout.py",
    "tests/udc/test_entity_sub_api_model.py",
    "tests/udc/test_entry_headline_counts.py",
    "tests/udc/test_enum_model.py",
    "tests/udc/test_facts_index_anchors.py",
    "tests/udc/test_flow_contracts_layout.py",
    "tests/udc/test_ledger_layout.py",
    "tests/udc/test_menu_api_model.py",
    "tests/udc/test_menu_contracts_layout.py",
    "tests/udc/test_microflow_api_model.py",
    "tests/udc/test_nav_domain_api.py",
    "tests/udc/test_operation_contracts_udc_layout.py",
    "tests/udc/test_page_contracts_layout.py",
    "tests/udc/test_publish_resource_rule_layout.py",
    "tests/udc/test_readme_totals_match_disk.py",
    "tests/udc/test_role_audit_layout.py",
    "tests/udc/test_role_contracts_override.py",
    "tests/udc/test_route_implementation_verdict.py",
    "tests/udc/test_route_literal_similarity.py",
    "tests/udc/test_rule_settings_sub_api.py",
    "tests/udc/test_setting_contracts_layout.py",
    "tests/udc/test_setting_contracts_override.py",
    "tests/udc/test_setting_custom_object_asset_layout.py",
    "tests/udc/test_setting_enum_asset_layout.py",
    "tests/udc/test_setting_facts_layout.py",
    "tests/udc/test_spi_facts_layout.py",
    "tests/udc/test_standard_product_anchors.py",
    "tests/udc/test_udc_facts_root_layout.py",
    "tests/udc/test_udc_facts_scale_table.py",
}

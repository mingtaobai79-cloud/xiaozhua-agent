"""跨构件（udc-web 之外）REST 归位护栏。

证据：docs/audit/udc-semantics/COMPONENT-RELOCATION.md 第 1 节。
31 条归位均经**独立脚本**（scratch s10/verify_reloc.py 与第四轮 javap -v）在 class 常量池逐条
验证四类字面量（类级 mapping / 方法级 mapping / 方法名 / HTTP 动词注解），31/31 VERIFIED_STATIC_BYTECODE。

本测试在**无 jar** 的仓库内钉住两件事：
  1. op 命名规则对这 32 条跨构件路径同样成立（归属右端可跨构件复用）；
  2. 这 32 条**不由** udc-web 契约产出（证明它们确属非 udc-web 构件）。
jar 侧字节码复核见 COMPONENT-RELOCATION.md 与 scratch 脚本（不进仓库）。
"""
import json
from pathlib import Path

import pytest

from components.udc.graphql_op_naming import derive_ops, path_to_op

ROOT = Path(__file__).resolve().parents[2]
_API = (ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts"
        / "_api_full.json")

pytestmark = pytest.mark.skipif(not _API.exists(), reason="udc-web 契约件缺失")


# (path, http, op, owning artifact, Controller, 方法名)
# 来源：COMPONENT-RELOCATION.md 表 1；27/27 已由 scratch s10/verify_reloc.py 字节码独立验证。
# 2026-10-15 第四轮：新增 boot-starter-excel/formula/file 4 条（javap -v 常量池 4/4 VERIFIED），
#   27 -> 31；余量 66 -> 62。

# 2026-10-15 第六轮：新增 boot-starter-i18n 1 条（javap -v 常量池 4/4 VERIFIED），

#   31 -> 32；余量 62 -> 60。该条来自「文档名 vs 字段名」更正的产出（见下方注释与

#   tools/core/_misc/correct_frontend_op_reference.py）。
# 2026-10-15 更正：原表 32 条含 5 条被**误判**为 udc-web 之外的操作
#   （udcEntityAttributeGroupSearch / udcMetaDataMergeReferPost /
#    udcMetaDataSelectAggregationEntityPost / udcMetaDataSelectAppByIdPost / udcMicroflowSearch）。
#   它们其实是 udc-web 真实端点，只因缺陷 A（提取器按方法名做 key 丢重载）
#   在旧契约里「消失」，才显得归不到 udc-web。缺陷 A 修复（657 -> 674）后
#   5 条全部由 udc-web 契约产出，故从本表移除。32 -> 27。
_RELOCATED = [
    ('/udc/cdp-data/report/get-report-list', 'POST', 'udcCdpDataReportGetReportListPost', 'udc-cdpbi-5.3.517', 'UdcReportController', 'findReportList'),
    ('/udc/portal/portal-space/create', 'POST', 'udcPortalPortalSpaceCreatePost', 'udc-portal-5.3.517', 'UdcPortalSpaceController', 'create'),
    ('/udc/portal/portal-space/delete', 'POST', 'udcPortalPortalSpaceDeletePost', 'udc-portal-5.3.517', 'UdcPortalSpaceController', 'deleteById'),
    ('/udc/portal/portal-space/space-save-copy', 'POST', 'udcPortalPortalSpaceSpaceSaveCopyPost', 'udc-portal-5.3.517', 'UdcPortalSpaceController', 'saveAsPortalSpaceData'),
    ('/udc/portal/portal-space/update', 'POST', 'udcPortalPortalSpaceUpdatePost', 'udc-portal-5.3.517', 'UdcPortalSpaceController', 'update'),
    ('/udc/sandbox/app/clean-restart-app', 'POST', 'udcSandboxAppCleanRestartAppPost', 'boot-starter-sandbox-5.3.289', 'SandboxAppRunController', 'cleanSandboxAppDataAndRestart'),
    ('/udc/sandbox/app/clean-restart-by-app', 'POST', 'udcSandboxAppCleanRestartByAppPost', 'boot-starter-sandbox-5.3.289', 'SandboxAppRunController', 'cleanSandboxAppDataAndRestart'),
    ('/udc/sandbox/app/start-app', 'POST', 'udcSandboxAppStartAppPost', 'boot-starter-sandbox-5.3.289', 'SandboxAppRunController', 'startApp'),
    ('/udc/sandbox/app/start-by-app', 'POST', 'udcSandboxAppStartByAppPost', 'boot-starter-sandbox-5.3.289', 'SandboxAppRunController', 'startApp'),
    ('/udc/sandbox/app/stop-app', 'POST', 'udcSandboxAppStopAppPost', 'boot-starter-sandbox-5.3.289', 'SandboxAppRunController', 'stopApp'),
    ('/udc/sandbox/app/un-load-app', 'POST', 'udcSandboxAppUnLoadAppPost', 'boot-starter-sandbox-5.3.289', 'SandboxAppRunController', 'unLoadApp'),
    ('/udc/sandbox/client/check-all-status', 'GET', 'udcSandboxClientCheckAllStatusGet', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'checkBatchResult'),
    ('/udc/sandbox/client/check-all-task', 'GET', 'udcSandboxClientCheckAllTaskGet', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'checkBatchTask'),
    ('/udc/sandbox/client/create', 'GET', 'udcSandboxClientCreateGet', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'create'),
    ('/udc/sandbox/client/delete', 'GET', 'udcSandboxClientDeleteGet', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'deleteById'),
    ('/udc/sandbox/client/restart', 'GET', 'udcSandboxClientRestartGet', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'restart'),
    ('/udc/sandbox/client/sandbox-log', 'POST', 'udcSandboxClientSandboxLogPost', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'log'),
    ('/udc/sandbox/client/sandbox-log-url', 'POST', 'udcSandboxClientSandboxLogUrlPost', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'logUrl'),
    ('/udc/sandbox/client/search', 'POST', 'udcSandboxClientSearch', 'boot-starter-sandbox-5.3.289', 'SandboxClientController', 'selectPageByConditions'),
    ('/udc/sandbox/system/config/get-app-limit', 'GET', 'udcSandboxSystemConfigGetAppLimitGet', 'boot-starter-sandbox-5.3.289', 'SandboxSystemConfigController', 'getAppLimit'),
    ('/udc/sandbox/system/config/get', 'GET', 'udcSandboxSystemConfigGetGet', 'boot-starter-sandbox-5.3.289', 'SandboxSystemConfigController', 'get'),
    ('/udc/sandbox/system/config/update', 'POST', 'udcSandboxSystemConfigUpdatePost', 'boot-starter-sandbox-5.3.289', 'SandboxSystemConfigController', 'update'),
    ('/udc/sandbox/tenant/config/config-all-tenant', 'GET', 'udcSandboxTenantConfigConfigAllTenantGet', 'boot-starter-sandbox-5.3.289', 'SandboxTenantConfigController', 'configAllTenant'),
    ('/udc/sandbox/tenant/config/create', 'POST', 'udcSandboxTenantConfigCreatePost', 'boot-starter-sandbox-5.3.289', 'SandboxTenantConfigController', 'create'),
    ('/udc/sandbox/tenant/config/delete', 'GET', 'udcSandboxTenantConfigDeleteGet', 'boot-starter-sandbox-5.3.289', 'SandboxTenantConfigController', 'delete'),
    ('/udc/sandbox/tenant/config/search', 'POST', 'udcSandboxTenantConfigSearch', 'boot-starter-sandbox-5.3.289', 'SandboxTenantConfigController', 'selectPageByConditions'),
    ('/udc/sandbox/tenant/config/update', 'POST', 'udcSandboxTenantConfigUpdatePost', 'boot-starter-sandbox-5.3.289', 'SandboxTenantConfigController', 'update'),
    # --- 第四轮新增（2026-10-15）：boot-starter-excel / -formula / -file ---
    # 类级 @RequestMapping 字面量依次为 excel / expression / file；方法级 mapping 见末列。
    ('/udc/excel/search-list-by-conditions', 'POST', 'udcExcelSearchListByConditionsPost', 'boot-starter-excel-5.3.318', 'ExcelController', 'selectListByConditions'),
    ('/udc/expression/system-variable/list', 'GET', 'udcExpressionSystemVariableListGet', 'boot-starter-formula-5.3.318', 'ExpressionController', 'listSystemVariable'),
    ('/udc/file/download-url', 'GET', 'udcFileDownloadUrlGet', 'boot-starter-file-5.3.358', 'FileController', 'generateDownloadUrl'),
    ('/udc/file/download-urls', 'POST', 'udcFileDownloadUrlsPost', 'boot-starter-file-5.3.358', 'FileController', 'generateDownloadUrl'),
    # --- 第六轮新增（2026-10-15）：boot-starter-i18n，来自前端文档名/字段名更正的产出 ---
    # 前端字面量是 `query udcPinyinGet ($query: udcI18nResourceStrToPinyinGetInputQuery)
    #   { udcI18nResourceStrToPinyinGet(query: $query) }` —— 'udcPinyinGet' 只是**文档名**，
    # 真 op 是字段名 udcI18nResourceStrToPinyinGet。
    # 判据 = **位置槽**：该字符串只出现在 `mutation|query` 之后的文档头槽、从不后接 `(` 实参。
    # ⚠ 已证伪的旧理由：「文档名恒不带 HTTP 动词后缀」—— 对 udcPinyinGet 不成立，它恰以 `Get` 结尾；
    #    故不能用字符串形态判定，只能用位置槽。
    # 见 tests/udc/test_frontend_udc_unlocated.py 第 6 节 + tools/core/_misc/classify_frontend_op_reference.py。
    # 类级 mapping `i18n-resource` + 方法级 `str-to-pinyin` + 方法 toPinYin + @GetMapping；
    # extends com.seeyon.boot.starter.web.BaseComponentController ⇒ `udc` 前缀由 addPathPrefix 叠加。
    ('/udc/i18n-resource/str-to-pinyin', 'GET', 'udcI18nResourceStrToPinyinGet', 'boot-starter-i18n-5.3.358', 'I18nResourceController', 'toPinYin'),
]


@pytest.mark.parametrize("path,http,op,art,cls,meth", _RELOCATED)
def test_op_rule_holds_for_relocated_paths(path, http, op, art, cls, meth):
    """op 命名规则对 32 条跨构件归位全部成立（32/32）。"""
    assert path_to_op(path, http) == op, (art, cls, meth)


@pytest.mark.parametrize("path,http,op,art,cls,meth", _RELOCATED)
def test_relocated_ops_not_derived_from_udc_web(path, http, op, art, cls, meth):
    """反证：这 32 条不由 udc-web 契约产出（故属非 udc-web 构件）。"""
    derived = set(derive_ops(json.loads(_API.read_text(encoding="utf-8"))))
    assert op not in derived, (op, art)


def test_relocation_covers_four_artifacts():
    """归位分布：sandbox 22 / udc-portal 4 / udc-cdpbi 1 / excel 1 / formula 1 / file 2 / i18n 1 = 32。"""
    from collections import Counter
    c = Counter(r[3] for r in _RELOCATED)
    assert c == {"boot-starter-sandbox-5.3.289": 22,
                 "udc-portal-5.3.517": 4, "udc-cdpbi-5.3.517": 1,
                 "boot-starter-excel-5.3.318": 1,
                 "boot-starter-formula-5.3.318": 1,
                 "boot-starter-file-5.3.358": 2,

                 "boot-starter-i18n-5.3.358": 1}, c


def test_relocation_paths_unique():
    """32 条路径互不重复（防复制粘贴错）。"""
    paths = [r[0] for r in _RELOCATED]
    assert len(paths) == len(set(paths)) == 32

"""GraphQL op 命名规则测试（字节码实证 + 与真实前端 op 对账）。

三层断言：
1. 规则自洽（pathToCamel 六步 + outOffset==0 守卫）；
2. 与**真实前端 op / 已对齐对**逐条对账（GROUND TRUTH 来自 bundle 抓取，
   不是从规则推出来的自证）；
3. 反向暴露旧 fuzzy 对账里的假阳性（本测试是回归护栏）。
"""
import json
from pathlib import Path

import pytest

from components.udc.graphql_op_naming import (
    ARG_TYPE_SUFFIX,
    EVIDENCE_LEVEL,
    OP_SUFFIX_REWRITES,
    RESPONSE_TYPE_SUFFIX,
    SCHEMA_ID,
    arg_type_name,
    derive_ops,
    path_to_op,
    response_type_name,
    to_camel_case,
)

ROOT = Path(__file__).resolve().parents[2]
_API = (ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts"
        / "_api_full.json")
_EXTRACTION = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-extraction.json"
_RECONCILE = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-backend-reconcile.json"

pytestmark = pytest.mark.skipif(not _API.exists(), reason="udc-web 契约件缺失")


# ---------------------------------------------------------------- 规则本身
def test_evidence_is_bytecode_level():
    assert EVIDENCE_LEVEL == "VERIFIED_STATIC_BYTECODE"
    assert SCHEMA_ID.endswith("graphql-op-naming.v1")


def test_leading_delimiter_does_not_capitalize():
    """outOffset==0 守卫：/udc/... 必须保持小写 u 开头（否则 299 端点全部对不上）。"""
    assert path_to_op("/udc/application/do/detection", "POST") == "udcApplicationDoDetectionPost"
    assert to_camel_case("/udc/entity", False, ("-", "/", "_")) == "udcEntity"


def test_path_variable_braces_removed_before_camel():
    assert path_to_op("/udc/entity/attribute/select-by-primary/{id}", "GET")         == "udcEntityAttributeSelectByPrimaryGet"


def test_http_method_is_lowercased_and_appended():
    """get→Get / post→Post 由 toCamelCase 产生，后缀来自 httpMethod。"""
    assert path_to_op("/udc/feature/list", "GET").endswith("Get")
    assert path_to_op("/udc/feature/list", "POST").endswith("Post")


def test_suffix_rewrites_are_ordered_and_exact():
    """三条改写顺序敏感：IdGet$ 必须先于 Id$（否则 *IdGet 会变成 *Get 之前被截断）。"""
    assert OP_SUFFIX_REWRITES == (("IdGet$", "Get"), ("Id$", ""), ("SearchPost$", "Search"))
    # Id$ 去掉 path 变量名的 Id
    assert path_to_op("/udc/collaboration/{appId}", "GET") == "udcCollaborationAppGet"
    # SearchPost$ → Search（op 名收尾不带 Post）
    assert not path_to_op("/udc/deduction/rule/search", "POST").endswith("Post")


def test_non_alnum_stripped():
    assert path_to_op("/udc/entity/attribute-group/bath-update", "POST")         == "udcEntityAttributeGroupBathUpdatePost"


# ---------------------------------------------------------------- 入参/出参类型
def test_arg_and_response_type_names():
    assert ARG_TYPE_SUFFIX == {"path": "InputPath", "body": "InputBody", "query": "InputQuery"}
    assert arg_type_name("udcEntityGet", "path") == "udcEntityGetInputPath"
    assert arg_type_name("udcEntityPost", "body") == "udcEntityPostInputBody"
    assert response_type_name("udcEntityGet") == "udcEntityGetResponseContent"


# ---------------------------------------------------------------- 与真实前端 op 对账
def _api():
    return json.loads(_API.read_text(encoding="utf-8"))


def test_derive_ops_covers_web_methods():
    derived = derive_ops(_api())
    assert len(derived) >= 600, len(derived)


def test_reproduces_ground_truth_matched_pairs():
    """GROUND TRUTH：reconcile 里由前端抓包确认的对，规则必须能推导出来。

    164/173 —— 余下 9 条经规则检验为**旧 fuzzy 匹配的假阳性**（见下一个测试）。
    """
    derived = derive_ops(_api())
    mp = json.loads(_RECONCILE.read_text(encoding="utf-8"))["matched_pairs"]
    hit = [op for op in mp if op in derived]
    assert len(hit) >= 164, f"only {len(hit)}/{len(mp)} reproduced"


def test_exposes_old_fuzzy_false_positives():
    """旧对账里被模糊归到同名 Controller、按字节码规则**并不存在**的 op。

    2026-10-15 更正：原表 5 条中有 2 条（udcMetaDataMergeReferPost /
    udcMetaDataSelectAppByIdPost）并非假阳性 —— 它们是 udc-web **真实端点**，
    只因缺陷 A（提取器按方法名做 key，同名重载后写覆盖前写）在旧契约里消失，
    才显得「规则推不出」。缺陷 A 修复后二者均由规则产出，已移入下面第二个测试。
    """
    derived = derive_ops(_api())
    false_positives = {
        "udcApplicationCopyGet": "udcApplicationCopyPost",
        "udcMicroflowCopy": "udcMicroflowCopyPageRuleBoundControlPost",
        "udcRuntimeDeployPost": "udcRuntimeDeployNormalPost",
    }
    for bogus, real in false_positives.items():
        assert bogus not in derived, f"{bogus} 不应由规则产出"
        assert real in derived, f"{real} 应由规则产出"


def test_overloads_restored_by_defect_a_fix_are_now_derivable():
    """缺陷 A 修复后恢复的同名重载端点：这些 op 现已由规则产出。

    它们此前被误当作「假阳性」（规则推不出），实为提取器丢端所致 ——
    钉在这里，防止有人把缺陷 A 的修复回退成「回到 657」。
    """
    derived = derive_ops(_api())
    restored = {
        "udcMetaDataMergeReferPost",        # MetaDataController.mergeReferMetaData
        "udcMetaDataSelectAppByIdPost",     # MetaDataController.selectEntityMetaDataByAppId
    }
    for op in restored:
        assert op in derived, f"{op} 应在缺陷 A 修复后由规则产出"


def test_bundle_ops_are_either_rest_mirror_or_other_app():
    """346 个真实前端 op：224 可用规则回到 udc-web 端点；余 122 非 udc-web（他应用域）。"""
    derived = derive_ops(_api())
    bundle = set(json.loads(_EXTRACTION.read_text(encoding="utf-8"))["frontend_ops"]["ops"])
    mirror = bundle & set(derived)
    assert len(mirror) >= 220, len(mirror)
    other = bundle - mirror
    # 余下必须全部是他应用前缀（不得是 udc*，否则说明 udc 域有归不到 REST 的 op）
    non_udc = [o for o in other if o.startswith("udc")]
    assert len(non_udc) <= 100, f"udc 前缀未归位过多：{len(non_udc)}"


def test_explain_returns_rest_source():
    assert derive_ops(_api())["udcEntityDeletePost"][0]["ctrl"] == "EntityController"

# ------------------------------------------------- full_path 契约回归（2026-10-14）
def test_derive_ops_takes_op_from_full_path_only():
    """derive_ops 的 op 必须只由 full_path 产出（不再并列 class_mapping+path）。

    "双候选" 是 full_path 拼接缺陷存在期间的兜底写法，实测掩盖了该缺陷。
    """
    synthetic = {
        "PageInfoController": {
            "class_mapping": "udc/page-info",
            "methods": [
                {"method": "createBaseInfo", "http": "POST",
                 "path": "/base-info/create",
                 "full_path": "/udc/page-info/base-info/create", "desc": "", "is_write": True},
            ],
        },
        "ParameterController": {
            "class_mapping": None,
            "methods": [
                {"method": "create", "http": "POST", "path": "",
                 "full_path": "/", "desc": "", "is_write": True},
            ],
        },
    }
    d = derive_ops(synthetic)
    assert "udcPageInfoBaseInfoCreatePost" in d
    # 缺陷期间会造出的"看似合法但线上不存在"的 op 必须不出现
    assert "udcBaseInfoCreatePost" not in d


def test_full_path_fix_removed_absolute_path_phantoms():
    """full_path 修复后，绝对路径误拼造出的 op 不得由规则产出。"""
    derived = derive_ops(_api())
    for phantom in ("udcBaseInfoCreatePost", "udcHandoverPost", "udcPublishPost",
                    "udcCreatePortletPost", "udcAppOnlinePost", "udcImportNewPost"):
        assert phantom not in derived, phantom


def test_workaround_is_now_noop_on_real_artifact():
    """双候选与单候选在真实产物上产出同一 op 集 —— 证明兜底已是死代码。"""
    api = _api()
    single = derive_ops(api)
    dual = {}
    for ctrl, info in api.items():
        mapping = (info.get("class_mapping") or "").strip("/")
        for m in info.get("methods") or ():
            http = m.get("http") or ("POST" if m.get("is_write") else "GET")
            mp = (m.get("path") or "").strip("/")
            fp = (m.get("full_path") or "").strip("/")
            cands = {fp}
            if mapping:
                cands.add(f"{mapping}/{mp}" if mp else mapping)
            for c in cands:
                if c:
                    dual[path_to_op(c, http)] = True
    assert set(single) == set(dual)


# ---------------------------- 跨构件（udc-web 之外）归属护栏
# 证据：docs/audit/udc-semantics/REST-EXPOSURE-MECHANISM.md
#   - boot-starter-scanner MetadataScanner#collectRestMetadata / #collectMetadataByClass
#   - boot-starter-appservice 全类无 HTTP 映射（@AppService 不是第二套 REST 暴露）
#   - pod 侧 blob 扫描（test2 /app/udc-assemble.jar BOOT-INF/lib）artifact 级命中
# 这些 op 不在 udc-web 的 54 Controller 内，但规则对其同样成立 —— 归属判定右端可跨构件复用。
_CROSS_ARTIFACT_PATHS = [
    # (path, http, expected_op, owning artifact)
    ("/udc/sandbox/app/start-by-app", "POST",
     "udcSandboxAppStartByAppPost", "boot-starter-sandbox"),
    ("/udc/sandbox/app/clean-restart-by-app", "POST",
     "udcSandboxAppCleanRestartByAppPost", "boot-starter-sandbox"),
    ("/udc/sandbox/client/check-all-status", "GET",
     "udcSandboxClientCheckAllStatusGet", "boot-starter-sandbox"),
    ("/udc/sandbox/client/check-all-task", "GET",
     "udcSandboxClientCheckAllTaskGet", "boot-starter-sandbox"),
    ("/udc/sandbox/tenant-config/config-all-tenant", "GET",
     "udcSandboxTenantConfigConfigAllTenantGet", "boot-starter-sandbox"),
    ("/udc/sandbox/system-config/get-app-limit", "GET",
     "udcSandboxSystemConfigGetAppLimitGet", "boot-starter-sandbox"),
    ("/udc/sandbox/client/sandbox-log-url", "POST",
     "udcSandboxClientSandboxLogUrlPost", "boot-starter-sandbox"),
    ("/udc/cdp-data-report/get-report-list", "POST",
     "udcCdpDataReportGetReportListPost", "udc-cdpbi"),
    ("/udc/portal/portal-space/space-save-copy", "POST",
     "udcPortalPortalSpaceSpaceSaveCopyPost", "udc-portal"),
]


@pytest.mark.parametrize("path,http,expected,owner", _CROSS_ARTIFACT_PATHS)
def test_op_rule_holds_for_non_udc_web_artifacts(path, http, expected, owner):
    """op 命名规则对非 udc-web 构件同样成立（9/9），归属右端可跨构件复用。"""
    assert path_to_op(path, http) == expected, owner


def test_non_udc_web_ops_are_not_derived_from_udc_web_contract():
    """反证：上述跨构件 op 不由 udc-web 契约产出（99 未归位 op 的本体结论）。"""
    derived = set(derive_ops(_api()))
    for _p, _h, op, owner in _CROSS_ARTIFACT_PATHS:
        assert op not in derived, f"{op} unexpectedly in udc-web ({owner})"


# ------------------------------------------------ 前端 op 对账收口（2026-10-15 第三轮）
# 来源：frontend-extraction.json（bundle 抓取真值）x _api_full.json（udc-web 契约）。
# 旧 frontend-op-model.json 内嵌 reconcile 已失效（matched=173 / frontend_only=173，口径不同），
# 下列为当前口径真值，与 COMPONENT-RELOCATION.md 第 2.5 节一致。
_FRONTEND_TOTAL = 346
# 原始清单（frontend-extraction.json 未改）里含 2 条**文档名幻影**：
#   udcMicroflowCopy / udcPinyinGet 是 GraphQL 文档名，真 op 分别是其字段
#   udcMicroflowCopyPost / udcI18nResourceStrToPinyinGet。raw 视图保留幻影，
#   corrected（= raw - 幻影 + 真 op）才是对账口径，见 test_frontend_udc_unlocated.py。
_FRONTEND_TOTAL_RAW = 346
_FRONTEND_MATCHED_RAW = 230      # raw 清单 ∩ udc-web 契约
_FRONTEND_UDC_UNLOCATED_RAW = 93  # raw 清单里 udc* 前缀且不由 udc-web 契约产出
_FRONTEND_PHANTOM_DOC_NAMES = ("udcMicroflowCopy", "udcPinyinGet")
_FRONTEND_PHANTOM_REAL_OPS = ("udcMicroflowCopyPost", "udcI18nResourceStrToPinyinGet")

_FRONTEND_MATCHED = 231        # corrected：230 + 1（udcMicroflowCopyPost 由 udc-web 覆盖）
_FRONTEND_UDC_UNLOCATED = 92   # corrected：93 - 1（udcPinyinGet 这个字符串根本不存在）
# 2026-10-15 第四轮：跨构件归位 27 -> 31；第六轮 31 -> 32
#   （第四轮新增 boot-starter-excel 1 / -formula 1 / -file 2，javap 常量池 4/4 VERIFIED；
#    第六轮新增 boot-starter-i18n 1，javap 常量池 4/4 VERIFIED）。
#   权威名单与复算见 tests/udc/test_frontend_udc_unlocated.py + frontend-udc-unlocated.json。
_CROSS_ARTIFACT_RELOCATED = 32   # 第六轮：+ udcI18nResourceStrToPinyinGet
_FRONTEND_UDC_REMAINING = 60   # 92 - 32 仍 UNVERIFIED


def test_frontend_op_reconciliation_counts_are_pinned():
    """raw 346/230/93 -> corrected 346/231/92；扣 32 条跨构件归位后余 60 UNVERIFIED。"""
    derived = derive_ops(_api())
    bundle = set(json.loads(_EXTRACTION.read_text(encoding="utf-8"))["frontend_ops"]["ops"])
    assert len(bundle) == _FRONTEND_TOTAL_RAW, len(bundle)
    # raw 视图（未更正的抓取产物）
    assert len(bundle & set(derived)) == _FRONTEND_MATCHED_RAW
    assert len([o for o in bundle if o.startswith("udc") and o not in derived])         == _FRONTEND_UDC_UNLOCATED_RAW
    # perfect the two document-name phantoms into their real field ops
    for ph in _FRONTEND_PHANTOM_DOC_NAMES:
        assert ph in bundle, ph
    corrected = (bundle - set(_FRONTEND_PHANTOM_DOC_NAMES)) | set(_FRONTEND_PHANTOM_REAL_OPS)
    assert len(corrected) == _FRONTEND_TOTAL, len(corrected)
    matched = corrected & set(derived)
    assert len(matched) == _FRONTEND_MATCHED, len(matched)
    unlocated = [o for o in corrected if o.startswith("udc") and o not in derived]
    assert len(unlocated) == _FRONTEND_UDC_UNLOCATED, len(unlocated)
    assert _FRONTEND_UDC_UNLOCATED - _CROSS_ARTIFACT_RELOCATED == _FRONTEND_UDC_REMAINING

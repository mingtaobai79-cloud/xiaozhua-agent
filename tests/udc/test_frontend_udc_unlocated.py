"""前端 op 面「udc* 未归位」收口护栏（2026-10-15 第四轮）。

证据落盘：`docs/audit/udc-semantics/frontend-udc-unlocated.json`
（由前端 bundle 真值 x udc-web 契约机械复算，非人工抄录）。

口径（raw / corrected 两视图；见 `frontend-udc-unlocated.json#reference_kind_correction`）：
    raw       346 = 230 可由 udc-web 契约推导 + 116 不可推导，其中 `udc*` 前缀 = 93
    corrected 346 = 231 + 115，其中 `udc*` 前缀 = 92
      —— 差额来自 2 条 GraphQL **文档名幻影**（`udcMicroflowCopy` / `udcPinyinGet`），
         真 op 是其花括号后的**字段名**（`udcMicroflowCopyPost` /
         `udcI18nResourceStrToPinyinGet`）。
         判据 = **位置槽**（measured，非形态）：把 bundle 内该字符串的每次出现分类为
         「文档头槽」（紧跟 `mutation|query|subscription`）或「字段槽」（后接 `(` 实参），
         只出现在文档头槽者即文档名、不是 op。见第 6 节护栏。
         ⚠ 已证伪的旧理由：「文档名恒不带 HTTP 动词后缀」—— **错**，
           `udcPinyinGet` 恰以 `Get` 结尾（它作为文档名的名字本身就像 op）。
           故判据只能是位置槽，不能靠字符串形态。
    92 = 32（跨构件已归位，字节码 VERIFIED）+ 60（仍 UNVERIFIED）

本测试在**无 jar** 的仓库内钉住五件事：
  1. 60 条名单**逐条**是 bundle 里的字面量 op（真 op，不是规则臆造出来的名）；
  2. 60 条**不由** udc-web 契约产出（故确属非 udc-web 构件）；
  3. 32 条归位 op 的算术（92 - 32 = 60）与名单互斥且穷尽；
  4. 落盘 JSON 与测试内常量一致（防两处口径漂移）；
  5. 2 条文档名幻影**不得**回到余量名单（负向护栏，见第 6 节）。

jar 侧字节码复核见 COMPONENT-RELOCATION.md 第 3 节（javap -v 常量池），不进仓库。
"""
import json
import re
from pathlib import Path

import pytest

from components.udc.graphql_op_naming import derive_ops, path_to_op

ROOT = Path(__file__).resolve().parents[2]
_API = (ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts"
        / "_api_full.json")
_EXTRACTION = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-extraction.json"
_UNLOCATED = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-udc-unlocated.json"

pytestmark = pytest.mark.skipif(
    not (_API.exists() and _UNLOCATED.exists()), reason="udc-web 契约件缺失"
)

# ------------------------------------------------------------------ 计数真值
# raw 视图：抓取产物 frontend-extraction.json 的**原值**，特意保留未改（可分离对照）
_FRONTEND_TOTAL_RAW = 346
_MATCHED_UDC_WEB_RAW = 230
_UDC_UNLOCATED_RAW = 93
# corrected 视图：raw - 2 文档名幻影 + 2 真 op
# 复算工具：`uv run --no-project python tools/core/_misc/correct_frontend_op_reference.py --check`
_FRONTEND_TOTAL = 346
_MATCHED_UDC_WEB = 231
_UDC_UNLOCATED = 92
_RELOCATED = 32          # 27（第三轮）+ 4（第四轮）+ 1（第六轮 i18n，见第 3 / 6 节）
_REMAINING = 60          # 92 - 32
# GraphQL 文档名 -> 其字段真 op（文档名不带 HTTP 动词后缀 ⇒ 构造上不可达）
_PHANTOM_DOC_NAMES = ("udcMicroflowCopy", "udcPinyinGet")
_PHANTOM_REAL_OPS = ("udcMicroflowCopyPost", "udcI18nResourceStrToPinyinGet")


def _spec():
    return json.loads(_UNLOCATED.read_text(encoding="utf-8"))


def _bundle():
    return set(json.loads(_EXTRACTION.read_text(encoding="utf-8"))["frontend_ops"]["ops"])


def _derived():
    return set(derive_ops(json.loads(_API.read_text(encoding="utf-8"))))


def _corrected_bundle():
    """raw bundle 去幻影补真 op —— 对账口径（raw 视图永不改动）。"""
    return (_bundle() - set(_PHANTOM_DOC_NAMES)) | set(_PHANTOM_REAL_OPS)


def _remaining():
    return list(_spec()["remaining_ops"])


def _relocated():
    return list(_spec()["relocated_ops"])


# ------------------------------------------------------------------ 1. 清单钉桩
def test_frontend_unlocated_spec_is_schema_locked():
    """落盘物是机械复算产物，字段不可被手改成宽松口径。"""
    s = _spec()
    assert s["schema"] == "frontend-udc-unlocated.v1"
    assert s["frontend_total"] == _FRONTEND_TOTAL
    assert s["matched_udc_web"] == _MATCHED_UDC_WEB
    assert s["udc_unlocated"] == _UDC_UNLOCATED
    assert s["relocated_cross_artifact"] == _RELOCATED
    assert s["remaining"] == _REMAINING
    assert len(s["remaining_ops"]) == _REMAINING
    assert len(s["relocated_ops"]) == _RELOCATED


def test_counts_are_mutually_exclusive_and_exhaustive():
    """corrected 口径：92 = 32 归位 + 60 剩余，两类互斥且穷尽（机械复算，不靠人工抄）。"""
    corrected, derived = _corrected_bundle(), _derived()
    unlocated = [o for o in corrected if o.startswith("udc") and o not in derived]
    assert len(unlocated) == _UDC_UNLOCATED, len(unlocated)
    rel, rem = set(_relocated()), set(_remaining())
    assert rel.isdisjoint(rem), sorted(rel & rem)
    assert rel | rem == set(unlocated), sorted(set(unlocated) - (rel | rem))
    assert len(rel) + len(rem) == _UDC_UNLOCATED


def test_reconciliation_counts_recompute_from_sources():
    """raw 346/230/93 与 corrected 346/231/92 都必须能从 bundle 与契约现场复算出来。"""
    bundle, derived = _bundle(), _derived()
    # raw（抓取产物原值）
    assert len(bundle) == _FRONTEND_TOTAL_RAW
    assert len(bundle & derived) == _MATCHED_UDC_WEB_RAW
    assert len([o for o in bundle if o.startswith("udc") and o not in derived])         == _UDC_UNLOCATED_RAW
    # corrected（去幻影补真 op）
    corrected = _corrected_bundle()
    assert len(corrected) == _FRONTEND_TOTAL
    assert len(corrected & derived) == _MATCHED_UDC_WEB
    assert len([o for o in corrected if o.startswith("udc") and o not in derived])         == _UDC_UNLOCATED


# ------------------------------------------- 2. 62 条：真 op + 非 udc-web 产出
@pytest.mark.parametrize("op", _remaining())
def test_remaining_op_is_literal_in_bundle(op):
    """60 条**逐条**必须是 bundle 中的字面量 —— 挡「用规则拼一个看似合法的 op」。"""
    assert op in _bundle(), op


@pytest.mark.parametrize("op", _remaining())
def test_remaining_op_not_derived_from_udc_web(op):
    """60 条均不由 udc-web 契约产出 —— 故唯一定域途径是补采非 udc-web 构件事实源。"""
    assert op not in _derived(), op


def test_remaining_ops_union_is_exact():
    """60 条并集精确等于落盘名单（防漏登记 / 多登记）。"""
    rem = _remaining()
    assert len(rem) == len(set(rem)) == _REMAINING
    assert sorted(rem) == sorted(_spec()["remaining_ops"])


# --------------------------------------------- 3. 第四/第六轮新增 5 条（字节码 VERIFIED）
# 证据：docs/audit/udc-semantics/COMPONENT-RELOCATION.md 第 3 节（javap -v 常量池）。
# 四条均齐备：类级 @RequestMapping 字面量 + 方法级 mapping 字面量 +
#             @RestApiOperation + HTTP 动词注解；类均 extends BaseComponentController
#             （`udc` 前缀由 Spring 层 addPathPrefix 叠加，与已验 27 条同构）。
_NEW_RELOCATED = [
    ("/udc/excel/search-list-by-conditions", "POST",
     "udcExcelSearchListByConditionsPost", "boot-starter-excel-5.3.318",
     "ExcelController", "selectListByConditions", "excel"),
    ("/udc/expression/system-variable/list", "GET",
     "udcExpressionSystemVariableListGet", "boot-starter-formula-5.3.318",
     "ExpressionController", "listSystemVariable", "expression"),
    ("/udc/file/download-url", "GET",
     "udcFileDownloadUrlGet", "boot-starter-file-5.3.358",
     "FileController", "generateDownloadUrl", "file"),
    ("/udc/file/download-urls", "POST",
     "udcFileDownloadUrlsPost", "boot-starter-file-5.3.358",
     "FileController", "generateDownloadUrl", "file"),
]


@pytest.mark.parametrize("path,http,op,art,cls,meth,cls_map", _NEW_RELOCATED)
def test_op_rule_holds_for_new_relocated_paths(path, http, op, art, cls, meth, cls_map):
    """op 命名规则对第四轮 4 条归位成立（类级 mapping + 方法级 mapping 恒拼接）。"""
    assert path_to_op(path, http) == op, (art, cls, meth)


# 第六轮新增 1 条：真 op 来自「文档名 vs 字段名」更正（前端字面量只给了文档名 udcPinyinGet）。
# 四类字面量齐备：类级 mapping `i18n-resource` + 方法级 `str-to-pinyin` + 方法名 `toPinYin`
# + @GetMapping；类 extends com.seeyon.boot.starter.web.BaseComponentController
# ⇒ `udc` 前缀由 addPathPrefix 叠加（与已验 sandbox 族同构）。
_ROUND6_RELOCATED = [
    ("/udc/i18n-resource/str-to-pinyin", "GET",
     "udcI18nResourceStrToPinyinGet", "boot-starter-i18n-5.3.358",
     "I18nResourceController", "toPinYin", "i18n-resource"),
]


@pytest.mark.parametrize("path,http,op,art,cls,meth,cls_map", _ROUND6_RELOCATED)
def test_op_rule_holds_for_round6_relocated_paths(path, http, op, art, cls, meth, cls_map):
    """op 命名规则对第六轮 1 条归位成立（类级 + 方法级 mapping 恒拼接）。"""
    assert path_to_op(path, http) == op, (art, cls, meth)


@pytest.mark.parametrize("path,http,op,art,cls,meth,cls_map", _ROUND6_RELOCATED)
def test_round6_relocated_op_not_derived_from_udc_web(path, http, op, art, cls, meth, cls_map):
    """反证：i18n 真实 op 不由 udc-web 契约产出（确属非 udc-web 构件）。

    注意它**不在** raw bundle 里 —— raw 里只有文档名 udcPinyinGet，故必须在 corrected
    bundle 上校验（这正是「文档名 vs 字段名」更正的对账后果）。
    """
    assert op not in _derived(), (op, art)
    assert op not in _bundle(), op          # raw 抓取产物里没有它（只有文档名）
    assert op in _corrected_bundle(), op
    assert op not in set(_remaining()), op  # 已归位，必须从余量名单消失


@pytest.mark.parametrize("path,http,op,art,cls,meth,cls_map", _NEW_RELOCATED)
def test_new_relocated_ops_not_derived_from_udc_web(path, http, op, art, cls, meth, cls_map):
    """反证：4 条不由 udc-web 契约产出（确属非 udc-web 构件）。"""
    assert op not in _derived(), (op, art)


def test_new_relocated_ops_are_in_remaining_unlocated_set():
    """4 条原属 93 未归位 —— 归位后必须从余量名单中消失（防口径回退）。"""
    unlocated = {o for o in _bundle() if o.startswith("udc") and o not in _derived()}
    for _p, _h, op, art, cls, _m, _c in _NEW_RELOCATED:
        assert op in unlocated, (op, art)
        assert op not in set(_remaining()), op


def test_phantom_and_relocation_regression_to_62_is_rejected():
    """口径回退护栏：退回「2 幻影在册 + 31 归位」即回得 62 —— 钉死 92/32/60。"""
    assert _UDC_UNLOCATED - _RELOCATED == _REMAINING == 60
    assert _UDC_UNLOCATED + 1 == 93            # 幻影 1：文档名被就地当成 op（原 raw 口径）
    assert _RELOCATED - 1 == 31                # 幻影 2：i18n 真 op 未归位
    assert (_UDC_UNLOCATED + 1) - (_RELOCATED - 1) == 62
    assert _FRONTEND_TOTAL_RAW == _FRONTEND_TOTAL


# ------------------------- 4. store_registry 契约覆盖（非归位，仅入参契约证据）
def test_registry_contract_coverage_count_is_pinned():
    """60 条中 25 条可从 bundle 内嵌 Apollo store_registry 取到入参契约（非路径归属）。"""
    s = _spec()
    sr = json.loads(_EXTRACTION.read_text(encoding="utf-8"))["store_registry"]["ops"]
    assert set(s["remaining_registry_ops"]) <= set(_remaining())
    assert len(s["remaining_registry_ops"]) == s["remaining_with_registry_contract"]
    assert sorted(s["remaining_registry_ops"]) == sorted(o for o in _remaining() if o in sr)


def test_registry_ops_all_keyed_in_store():
    """落盘的 registry 覆盖清单必须条条真在 registry 里（重复算不作数）。"""
    sr = json.loads(_EXTRACTION.read_text(encoding="utf-8"))["store_registry"]["ops"]
    for op in _spec()["remaining_registry_ops"]:
        assert op in sr, op


# --------------------------------------------- 5. 族分布（机械复算，非人工抄录）
# 第六轮更正：Microflow / Pinyin 两族随「文档名幻影」清零而消失（余量族 18 -> 16）。
_TOKENS = ("FormUpgradeDeploy", "CustomDataType", "PageComponent", "RuntimeUpgrade", "CtpManager",
           "Message", "Sandbox", "PageInfo", "PageAdmin", "Portal", "MetaData",
           "Application", "Affair", "Entity", "Env")


def _family(op):
    hits = sorted((t for t in _TOKENS if op.startswith("udc" + t)), key=len, reverse=True)
    return hits[0] if hits else "OTHER"


def test_remaining_families_recompute_matches_document():
    """族分布必须能从名单现场复算，且与落盘 JSON 一致（防文档数字漂移）。"""
    import collections
    c = collections.Counter(_family(o) for o in _remaining())
    spec = _spec()["remaining_families"]
    assert sum(c.values()) == _REMAINING
    assert {k: v for k, v in c.items()} == spec, (dict(c), spec)
    # 文档 COMPONENT-RELOCATION.md 第 3.2 节引用的关键族数
    assert c["Sandbox"] == 11 and c["Message"] == 8 and c["FormUpgradeDeploy"] == 7
    assert c["CustomDataType"] == 6 and c["PageComponent"] == 6 and c["Affair"] == 5


def test_family_partition_is_exhaustive_over_remaining_list():
    """每个族桶的并集精确等于 60 名单（无遗漏、无重复计数）。"""
    import collections
    buckets = collections.defaultdict(list)
    for op in _remaining():
        buckets[_family(op)].append(op)
    flat = [o for ops in buckets.values() for o in ops]
    assert sorted(flat) == sorted(_remaining())
    assert len(flat) == len(set(flat)) == _REMAINING



# --------------------------------------------- 6. 文档名幻影负向护栏（第六轮）
def test_document_name_phantoms_cannot_return_to_remaining_list():
    """2 条 GraphQL 文档名不得被当成 op：raw 里在、corrected 里不在、各名单里都不在。

    判据三重：
      ① 语法自证 —— 文档名不含 HTTP 动词小写后缀，而 path→op 规则恒追加该后缀 ⇒ 构造上不可达；
      ② 归属自证 —— 契约侧不产出它们，真 op 另有其人；
      ③ 名单自证 —— 幻影既不在 60 余量、也不在 32 归位名单里。
    """
    derived, rem, rel = _derived(), set(_remaining()), set(_relocated())
    raw = _bundle()
    harvested = json.loads(_EXTRACTION.read_text(encoding="utf-8"))["frontend_ops"]["ops"]
    chunk = (ROOT / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496"
             / "chunks" / "src_redux_store_ts.14dc061e.js")
    text = chunk.read_text(encoding="utf-8", errors="replace") if chunk.exists() else ""
    for phantom, real in zip(_PHANTOM_DOC_NAMES, _PHANTOM_REAL_OPS):
        # ① 位置槽判据（形态判据已证伪：udcPinyinGet 恰以 Get 结尾，看形态会误判）
        if text:
            hdr = fld = 0
            for m in re.finditer(r"\b%s\b" % re.escape(phantom), text):
                if re.search(r"(?:mutation|query|subscription)\s+$",
                             text[max(0, m.start() - 40):m.start()]):
                    hdr += 1
                elif re.match(r"\s*\(\s*(?:body|query|path)?\s*[:)]",
                              text[m.end():m.end() + 12]):
                    fld += 1
            assert hdr >= 1 and fld == 0, (phantom, hdr, fld)
        assert phantom in raw and phantom in harvested, phantom
        assert phantom not in _corrected_bundle(), phantom
        assert phantom not in derived and phantom not in rem and phantom not in rel, phantom
        assert real not in raw, real                   # 真 op 不在 raw（raw 只有文档名）
        assert real in _corrected_bundle(), real
        # corrected 里两条真 op 的**归属不同**（不得混为一谈）：
        #   udcMicroflowCopyPost        -> udc-web 契约承接 => 计入 matched(231)，**不是**归位
        #   udcI18nResourceStrToPinyinGet -> 非 udc-web => 跨构件归位 => 计入 relocated(32)
        assert (real in rel) == (real not in derived), real
        assert (real in rel) != (real == "udcMicroflowCopyPost"), real


def test_phantom_real_ops_are_accounted_for_where_they_belong():
    """2 条真 op 各自归位：udcMicroflowCopyPost 由 udc-web 契约承接；i18n 真 op 跨构件归位。"""
    derived = _derived()
    assert "udcMicroflowCopyPost" in derived                 # udc-web 覆盖（matched 230 -> 231）
    assert "udcI18nResourceStrToPinyinGet" not in derived    # 非 udc-web ⇒ 跨构件归位（31 -> 32）

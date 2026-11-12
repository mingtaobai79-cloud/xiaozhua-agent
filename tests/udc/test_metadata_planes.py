"""并行 metadata 面护栏（候选 (v) 收口）。

**为什么需要**：平台操作面长期按**单构件**（udc-web 674 端点）口径理解。
那个数字读起来像"平台全部端点"，实际上：
  1. udc-web 自己就注册了**两个** metadata 前缀，只差一个连字符
     （udc/meta-data 32 / udc/design-metadata 47）；
  2. /udc/metadata/** （无连字符）由**别的构件**（ctp MetadataController）提供 105 条。
后两者有 **43 个同名字面量**，所以"按语义猜路径"在 design-metadata 上几乎总能拼出
一个语法成立的路径，而该面在本窗口**零调用**（死面）。

本护栏把三个面、交集、并集口径、以及"哪个面是活的"两条独立轴**逐条钉死**，
防止有人再退回单构件口径，也防止两个数字口径互相污染。

证据源全部**仓内耐久**（不受 scratch 24h 清理影响）：
  - _api_full.json（udc-web 契约）
  - metadata-5.3.358/MetadataController.class（ctp 字节码，直读常量池）
  - udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js（设计器 chunk）
  - RUNTIME-URL-SURFACE.json（LIVE 计数）

本文件只引平台构件/路径/op 名，不含客户业务明细。
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "docs" / "audit" / "udc-semantics" / "METADATA-PLANES.json"
DOC = ROOT / "docs" / "audit" / "udc-semantics" / "RUNTIME-METADATA-CONSTRAINTS.md"
TOOL = ROOT / "tools" / "core" / "decompile" / "enumerate_metadata_planes.py"
CONTRACT = (ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts"
            / "_api_full.json")
CHUNK = (ROOT / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496" / "chunks"
         / "src_redux_store_ts.14dc061e.js")
LIVE = ROOT / "docs" / "audit" / "udc-semantics" / "RUNTIME-URL-SURFACE.json"

PINNED = {
    "meta-data-udcweb": ("/udc/meta-data/", "udc-web-5.3.517", "MetaDataController", 32, 30),
    "design-metadata-udcweb": ("/udc/design-metadata/", "udc-web-5.3.517",
                               "UdcDesignMetadataController", 47, 47),
    "metadata-ctp": ("/udc/metadata/", "metadata-5.3.358",
                     "com.seeyon.ctp.metadata.controller.MetadataController", 105, 105),
}
PINNED_SHARED_DESIGN_METADATA = 43
PINNED_UDC_WEB_TOTAL = 674
PINNED_UDC_WEB_CONTROLLERS = 54
PINNED_UNION = 779
PINNED_CHUNK_FAMILY_HITS = {"udcMetaData": 68, "udcDesignMetadata": 0}

pytestmark = pytest.mark.skipif(
    not (EVID.exists() and TOOL.exists() and CONTRACT.exists() and CHUNK.exists()),
    reason="并行 metadata 面证据件 / 复算器 / 源缺失")


def _evid():
    return json.loads(EVID.read_text(encoding="utf-8"))


def _tool():
    spec = importlib.util.spec_from_file_location("enumerate_metadata_planes", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_evidence_schema_and_plane_set_is_pinned():
    d = _evid()
    assert d["schema"] == "metadata-planes.v1"
    assert [p["id"] for p in d["planes"]] == list(PINNED)
    for p in d["planes"]:
        prefix, comp, cls, eps, leaves = PINNED[p["id"]]
        assert p["external_prefix"] == prefix, p["id"]
        assert p["controller"] == cls, p["id"]
        assert p["endpoints"] == eps, p["id"]
        assert p["distinct_leaves"] == leaves, p["id"]


def test_recomputation_matches_the_evidence_file_endpoint_for_endpoint(tmp_path):
    """证据件必须能由复算器**字节级**原样重现（不是人工抄录）。

    ★ 此前只比 parsed：换行/掉格式漂移一直隐形。
    本件此前靠 print() 在 Windows 隐式转 CRLF 才能重现，Linux 上会出 LF
    ⇒ 该不变量本来是宿主依赖的；现已在生成处显式钉死 CRLF。
    """
    assert _tool().enumerate_planes() == _evid()          # 结论面
    out = tmp_path / "rerun.json"
    assert _tool().main(["--emit", str(out)]) == 0
    assert out.read_bytes() == EVID.read_bytes(), "复算输出与证据件非字节一致"


def test_guardrail_bites_on_an_lf_reserialization():
    """会咬自证：LF 版本 parsed 等价，但必须被判字节不等。"""
    raw = EVID.read_bytes()
    assert raw.count(bytes([13, 10])) > 0, "证据件应为 CRLF"
    lf = raw.replace(bytes([13, 10]), bytes([10]))
    assert json.loads(lf.decode("utf-8")) == _evid()
    assert lf != raw


def test_plane_membership_is_derived_from_declared_provider_not_guessed():
    """面 1/2 成员来自 udc-web 契约，且 class_mapping 与外部前缀一致。"""
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["MetaDataController"]["class_mapping"] == "udc/meta-data"
    assert contract["UdcDesignMetadataController"]["class_mapping"] == "udc/design-metadata"
    for ctrl, mapping in (("MetaDataController", "udc/meta-data"),
                          ("UdcDesignMetadataController", "udc/design-metadata")):
        for m in contract[ctrl]["methods"]:
            assert m["full_path"].startswith("/" + mapping + "/"), m["full_path"]
    plane3 = next(p for p in _evid()["planes"] if p["id"] == "metadata-ctp")
    assert plane3["class_mapping"] == "metadata"


def test_the_three_metadata_prefixes_are_pairwise_distinct():
    """口径陷阱本体：三面前缀两两不同（防止有人"合并"成一个面）。"""
    d = {p["id"]: p for p in _evid()["planes"]}
    prefixes = {p["external_prefix"] for p in _evid()["planes"]}
    assert len(prefixes) == 3
    assert d["meta-data-udcweb"]["external_prefix"] == "/udc/meta-data/"
    assert d["design-metadata-udcweb"]["external_prefix"] == "/udc/design-metadata/"
    assert d["metadata-ctp"]["external_prefix"] == "/udc/metadata/"


def test_shared_leaf_counts_are_pinned():
    c = _evid()["cross_plane"]
    assert c["leafs_meta_data_and_design_metadata_shared"] == 1
    assert c["leafs_meta_data_and_metadata_shared"] == 1
    assert c["leafs_design_metadata_and_metadata_shared"] == PINNED_SHARED_DESIGN_METADATA
    assert c["leafs_shared_by_all_three"] == ["refer-and-app"]
    assert len(c["shared_leaves_design_metadata_vs_metadata"]) == 43


def test_the_one_hyphen_near_miss_pair_is_real_and_shared_by_all_three():
    """refer-and-app 在三面都存在；meta-data 与 metadata 版本只差一个连字符。"""
    leaves = {p["id"]: set(p["leaves"]) for p in _evid()["planes"]}
    for pid in PINNED:
        assert "refer-and-app" in leaves[pid], pid
    assert "/udc/meta-data/refer-and-app" != "/udc/metadata/refer-and-app"


def test_surface_arithmetic_separates_the_two_calibres():
    """674（单构件）与 779（并集）是两个口径，必须同时登记且不可混用。"""
    a = _evid()["surface_arithmetic"]
    assert a["udc_web_contract_endpoints"] == PINNED_UDC_WEB_TOTAL
    assert a["udc_web_controllers"] == PINNED_UDC_WEB_CONTROLLERS
    assert a["ctp_metadata_endpoints"] == 105
    assert a["platform_union_endpoints"] == PINNED_UNION
    assert PINNED_UDC_WEB_TOTAL + 105 == PINNED_UNION
    assert "不可混用" in a["note"]
    assert "不是运行期全量" in a["note"]


def test_designer_frontend_uses_the_hyphenated_plane_only():
    """轴 1：设计器 chunk 只出现 udcMetaData 族，udcDesignMetadata 族 0 次。"""
    text = CHUNK.read_text(encoding="utf-8", errors="replace")
    assert text.count("udcMetaData") == PINNED_CHUNK_FAMILY_HITS["udcMetaData"]
    assert text.count("udcDesignMetadata") == 0
    assert _evid()["frontend_op_family_usage"]["hits"] == PINNED_CHUNK_FAMILY_HITS


def test_live_window_shows_the_ctp_plane_alive_and_design_metadata_dead():
    """轴 2（独立于前端）：LIVE 计数 /udc/metadata/ 20 vs /udc/design-metadata/ 0。"""
    usage = json.loads(LIVE.read_text(encoding="utf-8"))["control_plane"]["route_family_usage_in_window"]
    assert usage["/udc/metadata/"] == 20
    assert usage["/udc/design-metadata/"] == 0
    ev = _evid()["live_cross_check"]["family_calls_in_window"]
    assert ev["/udc/metadata/"] == 20 and ev["/udc/design-metadata/"] == 0


def test_the_concrete_near_miss_pair_appears_in_the_evidence_and_the_contracts():
    """把"只差一个连字符"的具体路径钉死（不是形容词，是可查的事实）。"""
    d = _evid()
    by_id = {p["id"]: p for p in d["planes"]}
    # refer-and-app 是三面**唯一**共有字面量 —— 三面都真有这条路径，只是前缀不同
    for pid, path in (("meta-data-udcweb", "/udc/meta-data/refer-and-app"),
                      ("design-metadata-udcweb", "/udc/design-metadata/refer-and-app")):
        assert path in by_id[pid]["full_paths"], pid
    assert "refer-and-app" in by_id["metadata-ctp"]["leaves"]
    # 面 1 与面 3 的具体路径只差一个连字符（最危险的一对）
    p1, p3 = "/udc/meta-data/refer-and-app", "/udc/metadata/refer-and-app"
    assert p1.replace("meta-data", "metadata") == p3
    assert p1 != p3 and p1 != "/udc/design-metadata/refer-and-app"
    # 面 2 与面 3 确有 43 个同名 leaf；取其中一个现场复算
    shared = set(by_id["design-metadata-udcweb"]["leaves"]).intersection(
        by_id["metadata-ctp"]["leaves"])
    assert len(shared) == PINNED_SHARED_DESIGN_METADATA
    sample = sorted(shared)[0]
    assert "/udc/design-metadata/" + sample != "/udc/metadata/" + sample


def test_op_names_diverge_across_the_three_planes():
    """三面同名 leaf 派生三个不同 op（调用方拿错 op 名即打到错面）。"""
    from components.udc.graphql_op_naming import path_to_op
    ops = {
        path_to_op("/udc/meta-data/refer-and-app", "post"),
        path_to_op("/udc/design-metadata/app-service-by-name", "post"),
        path_to_op("/udc/metadata/app-service-by-name", "post"),
    }
    assert len(ops) == 3
    assert "udcMetaDataReferAndAppPost" in ops


def test_candidate_v_answer_and_limitations_are_recorded():
    d = _evid()
    assert "三个并行面" in d["answer"]
    assert len(d["limitations"]) >= 4
    joined = " ".join(d["limitations"])
    for boundary in ("5.3.496", "5.3.517", "单窗口"):
        assert boundary in joined, boundary


def test_doc_states_the_calibre_correction_and_the_dead_plane():
    text = DOC.read_text(encoding="utf-8")
    for needle in ("三个**并行** metadata 面", "/udc/meta-data/", "/udc/design-metadata/",
                   "/udc/metadata/", "674", "779", "全构件并集", "死面", "不可混用"):
        assert needle in text, needle


def test_guardrail_bites_on_a_mutated_evidence_file():
    """内存内突变自证：并集口径漂移 / 重叠抹平 / 前端族点击数必须被抓住（不写文件）。"""
    d = _evid()
    d["surface_arithmetic"]["platform_union_endpoints"] = 674      # 退回单构件口径
    a = d["surface_arithmetic"]
    assert not (a["platform_union_endpoints"] == PINNED_UNION
                and a["ctp_metadata_endpoints"] == 105
                and a["udc_web_contract_endpoints"] == PINNED_UDC_WEB_TOTAL)
    d2 = _evid()
    d2["cross_plane"]["leafs_design_metadata_and_metadata_shared"] = 0   # 抹掉重叠陷阱
    assert d2["cross_plane"]["leafs_design_metadata_and_metadata_shared"] != PINNED_SHARED_DESIGN_METADATA
    d3 = _evid()
    d3["frontend_op_family_usage"]["hits"] = {"udcMetaData": 68, "udcDesignMetadata": 5}
    assert d3["frontend_op_family_usage"]["hits"] != PINNED_CHUNK_FAMILY_HITS


# 清洗门要查的标记（拼接构造：避免本文件"自己命中自己"这种自反假失败）
_FORBIDDEN = ("xiaozhua" + ".com", "client" + "_", "_" + "customer")


def test_no_customer_identifiers_in_new_artifacts():
    """清洗门：新产物零客户业务明细（长数字串 = 失败）。

    只查**产物**（证据件 / 文档 / 工具），不查本护栏文件自身 ——
    否则 "本文件包含了它禁止的字面量" 会变成一条永远红的自反断言。
    """
    for path in (EVID, DOC, TOOL):
        text = path.read_text(encoding="utf-8", errors="replace")
        assert re.findall(r"\d{6,}", text) == [], path
        for bad in _FORBIDDEN:
            assert bad not in text, (path, bad)


def test_cleaning_gate_actually_bites_on_a_planted_long_id(tmp_path):
    """会咬自证：清洗门的正则**确实**能抓到长数字串（不写仓内文件）。"""
    long_id = "1" + "234567890"
    planted = tmp_path / "planted.json"
    planted.write_text('{"key": "%s"}' % long_id, encoding="utf-8")
    hits = re.findall(r"\d{6,}", planted.read_text(encoding="utf-8"))
    assert hits == [long_id]          # 抓到 ⇒ 门有效
    clean = tmp_path / "clean.json"
    clean.write_text('{"key": "5.3.517"}', encoding="utf-8")
    assert re.findall(r"\d{6,}", clean.read_text(encoding="utf-8")) == []

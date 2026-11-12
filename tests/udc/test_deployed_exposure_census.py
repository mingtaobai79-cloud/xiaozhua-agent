# -*- coding: utf-8 -*-
"""部署域「HTTP 暴露能力」闭包护栏 —— marker 判据的第二条独立检验。

**为什么必须加这一件**：`DEPLOYED-MARKER-CLOSURE.json` 以「常量池含 `bind/annotation`」
当「能暴露注解路由」的必要条件。该判据**只覆盖 Spring MVC** —— JAX-RS（`@Path`）与
原生 Servlet（`@WebServlet`/`@WebFilter`/`extends HttpServlet`）不需要该串即可暴露端点。
本件补上第二条必要条件并逐件实测，检验 marker 判据之外是否有窟窿。

**关键陷阱（本件专门钉死）**：`javax/servlet/http/HttpServlet` 是
`javax/servlet/http/HttpServletRequest` 的**前缀子串**。以子串判「继承 HttpServlet」
会把所有引用 HttpServletRequest 的类误判为 servlet（实测会从 2 件膨胀到 23 件假阳）。
⇒ 必须解析 `super_class` 常量池槽位做精确相等。
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "docs" / "audit" / "udc-semantics" / "DEPLOYED-EXPOSURE-CENSUS.json"
TOOL = ROOT / "tools" / "core" / "decompile" / "enumerate_deployed_exposure_census.py"
LIBINV = Path("<HERMES_HOME>/cache/scratch/lib_inventory.json")

PLATFORM_PREFIXES = ("udc-", "boot-starter-", "boot-", "ctp-", "cdp-", "cip-",
                     "devops-starter-", "app-common-", "organization-", "bpm-")


def _evid():
    return json.loads(EVID.read_text(encoding="utf-8"))


def _load_tool():
    spec = importlib.util.spec_from_file_location("dece", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_census_splits_every_deployed_jar_exhaustively():
    d = _evid()
    assert d["total"] == 544
    assert d["scanned"] + d["not_obtainable"] == d["total"]
    assert d["marker_bearing"] + d["zero_marker"] == d["scanned"]
    assert len(d["not_obtainable_jars"]) == d["not_obtainable"]
    assert len(d["marker_jars"]) == d["marker_bearing"]


def test_marker_counts_agree_with_the_sibling_closure_artifact():
    """本件与 DEPLOYED-MARKER-CLOSURE.json 必须对「哪些构件含 marker」逐字一致。

    两件若打架，说明扫描根或判据被改过 ⇒ 两个闭包论证不能同时成立。
    """
    sib = ROOT / "docs" / "audit" / "udc-semantics" / "DEPLOYED-MARKER-CLOSURE.json"
    other = json.loads(sib.read_text(encoding="utf-8"))
    d = _evid()
    assert set(d["marker_jars"]) == set(other["marker_jars"])
    assert d["not_obtainable"] == other["not_obtainable"]
    assert set(d["not_obtainable_jars"]) == set(other["not_obtainable_jars"])
    assert d["marker_bearing"] == other["marker_bearing"]
    assert d["zero_marker"] == other["zero_marker"]
    assert d["scanned"] == other["scanned"]
    assert d["total"] == other["total"]


def test_exposure_closure_passes_for_platform_artifacts():
    """★ 本件核心：marker 之外的两条暴露通道，在 0-marker 构件上不得命中平台家族。"""
    c = _evid()["closure_over_exposure_capability"]
    assert c["zero_marker_with_real_http_exposure_platform_family"] == []
    assert c["verdict"] == "PASS"


def test_the_two_exposed_zero_marker_jars_are_exactly_third_party_containers():
    """实测只有 2 件；且都必须是第三方容器/库（不是平台构件）。"""
    c = _evid()["closure_over_exposure_capability"]
    got = set(c["zero_marker_with_real_http_exposure"])
    assert got == {"jersey-common-2.35.jar", "tomcat-embed-core-9.0.104.jar"}, got
    for j in got:
        assert not j.startswith(PLATFORM_PREFIXES), f"{j} 竟是平台构件？闭包有真窟窿"
    assert set(c["zero_marker_with_real_http_exposure_third_party"]) == got


def test_no_platform_jar_carries_a_non_spring_route_annotation():
    assert _evid()["platform_jars_with_non_spring_route_annotation"] == []


def test_platform_family_zero_marker_set_is_large_and_all_platform():
    """把这条诚实边界钉住：0-marker 里有 48 件平台构件（含 udc-biz）。

    ⇒ 「0-marker 构件不可能是暴露者」这一句**不能**只靠 marker 判据说；
    必须由本件的第二条必要条件兑现。此断言防止有人把该集合悄悄改小来掩盖问题。
    """
    d = _evid()
    assert d["platform_family_zero_marker"] >= 48
    for j in d["platform_family_zero_marker_jars"]:
        assert j.startswith(PLATFORM_PREFIXES), j


def test_substring_trap_is_really_a_trap_and_we_avoid_it():
    """**对抗自证**：证伪「用子串判继承就够了」。

    直接对真实的 tomcat-embed-core 做两次判定：
      • 子串法（错）：`javax/servlet/http/HttpServlet` in bytes ⇒ 会命中大量
        仅引用 HttpServletRequest/Response 的类；
      • super_class 法（对）：只认出真正继承 HttpServlet 的类。
    两者计数必须**不相等**，否则本件的 trap 说明是空话、测试失去意义。
    """
    import zipfile
    idx = _load_tool().local_index(["<HERMES_HOME>/cache/scratch"])
    p = idx.get("tomcat-embed-core-9.0.104.jar")
    if not p:
        import pytest
        pytest.skip("tomcat-embed-core 不可得（扫描根已清理）")
    mod = _load_tool()
    substring_hits = super_hits = 0
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            if not n.endswith(".class"):
                continue
            d = z.read(n)
            if b"javax/servlet/http/HttpServlet" in d:
                substring_hits += 1
            if (b"javax/servlet/http/HttpServlet" in d
                    and mod.super_class_name(d)
                    in {"javax/servlet/http/HttpServlet", "jakarta/servlet/http/HttpServlet"}):
                super_hits += 1
    assert substring_hits > super_hits, (
        f"子串法({substring_hits}) 未高于精确法({super_hits}) ⇒ 本 trap 未被证明，"
        "该断言形同虚设，须复核 super_class_name")
    assert super_hits == 0, "tomcat 自身不该有类直接继承 HttpServlet（它是容器实现）"


def test_census_is_recomputable_by_the_tool(tmp_path):
    """证据件可由复算器原样重现（字节级：本件是复算产物，格式也是契约的一部分）。"""
    if not LIBINV.is_file():
        import pytest
        pytest.skip(f"544 jar 清单不可用（scratch 已清理）: {LIBINV}")
    out = tmp_path / "exposure.json"
    assert _load_tool().main(["--inventory", str(LIBINV), "--emit", str(out)]) == 0
    assert out.read_bytes() == EVID.read_bytes(), (
        "证据件与复算器输出非字节一致 ⇒ 该件被手工改写过：请改"
        " tools/core/decompile/enumerate_deployed_exposure_census.py 的生成处后重跑，勿直接编辑本件")


def test_byte_identity_bites_on_a_whitespace_only_edit():
    """会咬自证：只改空白（parsed 等价）也必须判不一致。"""
    raw = EVID.read_bytes()
    mutated = raw.replace(b'"zero_marker"', b' "zero_marker"', 1)
    assert mutated != raw, "突变没生效，测试无效"
    assert json.loads(mutated.decode("utf-8")) == json.loads(raw.decode("utf-8"))
    assert mutated != EVID.read_bytes()


def test_criterion_records_the_second_necessary_condition_and_the_trap():
    d = _evid()
    assert "HttpServlet" in d["criterion"]
    assert "Path" in d["criterion"]
    assert "HttpServletRequest" in d["known_trap_avoided"]
    assert "super_class" in d["known_trap_avoided"]


def test_limitations_state_the_unscanned_not_obtainable_gap():
    lim = " ".join(_evid()["limitations"])
    assert "NOT_OBTAINABLE" in lim
    assert "未扫" in lim or "未知" in lim


def test_scan_scale_does_not_shrink():
    d = _evid()
    assert d["scanned"] >= 515
    assert d["marker_bearing"] >= 87
    assert d["zero_marker"] >= 428


def test_cleaning_gate_no_customer_identifiers():
    s = EVID.read_text(encoding="utf-8")
    for token in ("znxmglpt", "chjh", "sy_access_token", "xiangmuguanli", "peixunudc"):
        assert token not in s, f"含客户/敏感串 {token!r}"
    assert not re.search(r"\d{15,}", s), "含长数字串（疑似客户 appId/记录 id）"

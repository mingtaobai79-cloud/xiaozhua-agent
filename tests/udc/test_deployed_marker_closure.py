# -*- coding: utf-8 -*-
"""部署域闭包护栏（LIVE-DEPLOYED + VERIFIED_STATIC_BYTECODE）。

**要解决的口径问题**：第二十轮把「余 60 条 op 在部署域内 0 命中」的域从 22 个 udc jar
扩到 94 个 jar 的注解路由面，但部署态 BOOT-INF/lib 实为 **544 jar** ⇒ 「域是否漏构件」
此前只能靠抽样（~90/544）。本件把该问题变成一条**可复算的闭包命题**：

  ① **判据**：marker = .class 常量池含 bind/annotation。任何带 @RequestMapping/... 的类
     必然引用 org/springframework/web/bind/annotation/* ⇒ 含 marker 是「能暴露注解路由」
     的**必要条件**；⇒ **0-marker 构件结构上不可能暴露注解路由**，漏掉它不可能藏端点。
  ② **闭包命题**：全部含 marker 的部署构件 ⊆ 扫描域（缺失清单须为空）。
     ⇒ 「域外」只剩两类：0-marker 构件（无注解路由）与取不到的第三方构件。
  ③ **诚实边界**：NOT_OBTAINABLE 构件的 marker 状态**未知**，不得当 0 marker 用；
     故闭包只在已扫子集上成立，件里必须同时报不可取清单。

**为什么本件独立于 op 面裁定**：本件只判「构件能否暴露注解路由」（必要条件），
不判路由字面量，故与 tools/core/decompile/enumerate_full_domain_op_surface.py 的裁定互不背书。
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "docs" / "audit" / "udc-semantics" / "DEPLOYED-MARKER-CLOSURE.json"
TOOL = ROOT / "tools" / "core" / "decompile" / "enumerate_deployed_marker_census.py"
LIBINV = Path("<HERMES_HOME>/cache/scratch/lib_inventory.json")
CLASSDIR = Path("<HERMES_HOME>/cache/scratch/sup_v2")


def _evid():
    return json.loads(EVID.read_text(encoding="utf-8"))


def _load_tool():
    spec = importlib.util.spec_from_file_location("dmc", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_census_covers_every_deployed_jar_and_splits_them_exhaustively():
    d = _evid()
    assert d["total"] == 544
    assert d["scanned"] + d["not_obtainable"] == d["total"]
    assert d["marker_bearing"] + d["zero_marker"] == d["scanned"]
    assert len(d["marker_jars"]) == d["marker_bearing"]
    assert len(d["not_obtainable_jars"]) == d["not_obtainable"]


def test_marker_bearing_jars_are_all_inside_the_scan_domain():
    """★ 闭包命题本体：marker 构件 ⊆ 域。缺一即 FAIL（域漏构件）。"""
    c = _evid()["closure_over_marker_bearing"]
    assert c is not None, "缺闭包判据 ⇒ 本件退化为普查清单"
    assert c["marker_jars_missing_from_domain"] == []
    assert c["verdict"] == "PASS"


def test_not_obtainable_jars_are_never_counted_as_zero_marker():
    """诚实边界：取不到的构件 marker 状态未知，不得记为 0 marker（否则闭包是假的）。"""
    d = _evid()
    na = set(d["not_obtainable_jars"])
    assert na, "竟全部可取？与 Artifactory 侧 29 个第三方件取不到的事实不符，须复核"
    assert not (na & set(d["marker_jars"]))
    lim = " ".join(d["limitations"])
    assert "未知" in lim and "已扫子集" in lim


def test_not_obtainable_jars_are_all_third_party():
    """★ 关键补强：取不到的 29 件若含 seeyon 家族构件，则闭包论证就有一个真窟窿。

    实测全部为第三方（无 udc-/boot-starter-/ctp-/cdp-/cip-/devops-starter- 前缀）⇒
    未扫子集里「可能是平台自身构件」的一个也没有。
    """
    d = _evid()
    fam = ("udc-", "boot-starter-", "boot-", "ctp-", "cdp-", "cip-", "devops-starter-",
           "app-common-", "organization-", "bpm-")
    bad = [j for j in d["not_obtainable_jars"] if j.startswith(fam)]
    assert bad == [], f"取不到的清单里出现了平台家族构件: {bad}"


def test_scan_scale_does_not_shrink():
    """域规模下界（只允许增长）：缩水 ⇒ 扫描根/缓存被清，闭包论证失效。"""
    d = _evid()
    assert d["scanned"] >= 515
    assert d["marker_bearing"] >= 87
    assert d["classes_scanned"] >= 216782


def test_domain_covers_every_marker_bearing_deployed_artifact_by_name():
    """按构件名（去版本）复核一遍，不只看计数 —— 防止两边同时漏同一个名字。"""
    d = _evid()
    if not CLASSDIR.is_dir():
        import pytest
        pytest.skip(f"域 class 根不可用（scratch 已清理）: {CLASSDIR}")
    import os
    dom = set(os.listdir(CLASSDIR))
    missing = [j for j in d["marker_jars"] if j[:-4] not in dom]
    assert missing == [], f"含 marker 的部署构件不在域内: {missing}"


def test_census_is_recomputable_by_the_tool(tmp_path):
    """证据件可由复算器原样重现（字节级：本件是复算产物，格式也是契约的一部分）。"""
    if not LIBINV.is_file():
        import pytest
        pytest.skip(f"544 jar 清单不可用（scratch 已清理）: {LIBINV}")
    out = tmp_path / "census.json"
    args = ["--inventory", str(LIBINV), "--emit", str(out)]
    if CLASSDIR.is_dir():
        args += ["--class-dir", str(CLASSDIR)]
    assert _load_tool().main(args) == 0
    assert json.loads(out.read_text(encoding="utf-8")) == _evid()
    assert out.read_bytes() == EVID.read_bytes(), (
        "证据件与复算器输出非字节一致 ⇒ 该件被手工改写过：请改"
        " tools/core/decompile/enumerate_deployed_marker_census.py 的生成处后重跑，勿直接编辑本件")


def test_byte_identity_bites_on_a_whitespace_only_edit():
    """会咬自证：只改缩进（parsed 等价）也必须判不一致 —— 证伪「只比 parsed 就够」。"""
    raw = EVID.read_bytes()
    mutated = raw.replace(b"\"marker_bearing\"", b" \"marker_bearing\"", 1)
    assert mutated != raw, "突变没生效，测试无效"
    assert json.loads(mutated.decode("utf-8")) == json.loads(raw.decode("utf-8"))
    assert mutated != EVID.read_bytes()


def test_marker_criterion_is_recorded_with_its_reason():
    """判据必须带理由，不得只剩一个魔法串。"""
    crit = _evid()["criterion"]
    assert "bind/annotation" in crit
    assert "必要条件" in crit


def test_cleaning_gate_no_customer_identifiers():
    s = EVID.read_text(encoding="utf-8")
    for token in ("znxmglpt", "chjh", "sy_access_token", "xiangmuguanli", "peixunudc"):
        assert token not in s, f"含客户/敏感串 {token!r}"
    assert not re.search(r"\d{15,}", s), "含长数字串（疑似客户 appId/记录 id）"

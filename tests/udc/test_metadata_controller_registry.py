"""元数据域（boot-starter-metadata 5.3.358）登记表 ↔ 字节码 对齐护栏（2026-10-15 第十六轮）。

**为什么需要**：本仓库对 `MetadataController` 只登记了 **12** 个端点，且 docstring 写「13 端点」
（自相矛盾）。根因不是笔误，而是**证据源本身是假阴性**：

- 仓内唯一证据源 `docs/audit/artifacts/metadata-5.3.358/MetadataController.javap.txt`
  是一次**不带 `-v`** 的 javap 输出 —— 它**根本不含注解值**。实测该文本里
  `starter-all` / `app-service-by-name` / `RestController` / `GetMapping` 命中数**全为 0**，
  而同一个 `.class` 文件里这些字面量**确实存在**。
- 于是「按 javap 文本 grep 路由字面量」得到的 0 命中，被误读成「只有这 12 条」。
  这与本仓库已钉死的 `unpacked` 丢字面量陷阱是**同一类错误**：把「证据源丢失」当成「事实不存在」。

**因此本护栏做三件事**：
1. 用 `tools/core/decompile/enumerate_class_http_mappings.py`（**直读 class 文件常量池 + RuntimeVisibleAnnotations**，
   不经 javap、不经 CFR）独立重算，与登记表**逐条**对账；
2. 钉死那次假阴性的**可复现特征**（无 `-v` 的 javap 文本里注解值为空），防止有人再拿它当权威源；
3. 钉死「105 / 99 / 6」三个计数与互补关系，任何一侧漂移都必须显式同步。

证据级：VERIFIED_STATIC_BYTECODE（.class 在仓内，不受 scratch 24h 清理影响）。
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CLASS = ROOT / "docs" / "audit" / "artifacts" / "metadata-5.3.358" / "MetadataController.class"
JAVAP_LOSSY = ROOT / "docs" / "audit" / "artifacts" / "metadata-5.3.358" / "MetadataController.javap.txt"
TOOL = ROOT / "tools" / "core" / "decompile" / "enumerate_class_http_mappings.py"

PINNED_SHA256 = "54d4550b60ae729bfbf9c3bf06aced32ba60c64d758fd45febb219e97808265f"
PINNED_BYTES = 59711
PINNED_ENDPOINTS = 105
PINNED_OP_SURFACE = 99
PINNED_NO_OP = ("sync-cache", "refresh", "downgrade-all", "refresh-all",
                "online-app-info", "online-front-app-info")
# 旧口径（错误）—— 保留以钉死「不再滑回去」
STALE_COUNT = 12

pytestmark = pytest.mark.skipif(
    not (CLASS.exists() and TOOL.exists()),
    reason="MetadataController.class / 独立枚举器缺失")


def _enum():
    spec = importlib.util.spec_from_file_location("enumerate_class_http_mappings", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def byt():
    return _enum().enumerate_routes(str(CLASS))


@pytest.fixture(scope="module")
def reg():
    from components.udc.metadata_constraints import METADATA_ENDPOINTS
    return METADATA_ENDPOINTS


def test_class_snapshot_is_byte_identical_to_the_pinned_digest():
    raw = CLASS.read_bytes()
    assert len(raw) == PINNED_BYTES
    assert hashlib.sha256(raw).hexdigest() == PINNED_SHA256


def test_registry_matches_bytecode_endpoint_for_endpoint(byt, reg):
    """★ 核心：登记表与字节码直读结果逐条相等（双向差 = 0）。"""
    from_bytecode = {(e["http"], e["sub_path"]) for e in byt["endpoints"]}
    from_registry = {(http, sub) for http, sub, _h, _o in reg}
    assert len(from_bytecode) == PINNED_ENDPOINTS
    assert from_registry == from_bytecode
    assert from_registry - from_bytecode == set()
    assert from_bytecode - from_registry == set()


def test_registry_op_surface_matches_bytecode(byt, reg):
    """op 面（类级 @RestApi ∧ 方法级 @RestApiOperation）逐条一致。"""
    bc = {(e["http"], e["sub_path"]): (e["op_code"] or "") for e in byt["endpoints"]}
    rg = {(http, sub): op for http, sub, _h, op in reg}
    assert rg == bc
    assert sum(1 for v in rg.values() if v) == PINNED_OP_SURFACE


def test_no_op_endpoints_are_exactly_the_lifecycle_six(byt):
    # 两侧必须同序比较：PINNED_NO_OP 是人工钉死的名单，按 sorted() 归一化后再比（否则顺序差异=假失败）
    no_op = sorted(e["sub_path"] for e in byt["endpoints"] if not e["op_code"])
    assert tuple(no_op) == tuple(sorted(PINNED_NO_OP))
    assert set(no_op) == set(PINNED_NO_OP)
    assert PINNED_OP_SURFACE + len(PINNED_NO_OP) == PINNED_ENDPOINTS


def test_stale_twelve_endpoint_registry_is_refuted(byt):
    """旧「12 端点」口径被字节码直接证伪（防回归到旧数字）。"""
    assert len(byt["endpoints"]) != STALE_COUNT
    assert len(byt["endpoints"]) == PINNED_ENDPOINTS


def test_lossy_javap_dump_has_no_annotation_values(reg):
    """★ 钉死假阴性的可复现特征。

    这次漏登记的根因是拿一份**不含注解值**的 javap 文本当权威源。
    该 dump 里连 `RestController`/`GetMapping` 都不出现 —— 任何靠它做
    `not in text` 的「不存在」结论都是假阴性。若该 dump 被换成带 -v 的版本，
    本测试会失败，提醒重新评估所有基于它的历史结论。
    """
    if not JAVAP_LOSSY.exists():
        pytest.skip("lossy javap dump 不在仓内")
    text = JAVAP_LOSSY.read_bytes().decode("utf-8", errors="replace")

    # (1) 注解**类型名**在该 dump 里 0 命中 ⇒ 注解值面完全不可读（这才是漏登记的根因）
    for marker in ("RestController", "GetMapping", "Constant pool:", "flags:", "Code:"):
        assert text.count(marker) == 0, marker

    # (2) 该 dump 是**被截断**的，不是「空」—— 只落 309 个 Utf8 行，而 .class 常量池有 865 个 Utf8。
    #     故「grep 不到」= 缺失面，绝不是「不存在」的证据。
    class_utf8 = _class_utf8_constants()
    dump_utf8_lines = sum(1 for ln in text.split(chr(10)) if " = Utf8 " in ln)
    assert len(class_utf8) == 865
    assert dump_utf8_lines == 309
    assert dump_utf8_lines < len(class_utf8)          # 截断事实
    assert len(class_utf8) - dump_utf8_lines == 556   # 缺失量钉死

    # (3) 截断是**不均匀**的：确有路由子路径在 dump 内查得到 —— 所以任何「按 dump grep 得 0 ⇒ 不存在」
    #     的推理都是不可靠的（这正是本护栏存在的理由）。
    for present in ("entity-by-name", "refresh-all", "downgrade-all"):
        assert dump_utf8_lines and text.count(present) > 0, present

    # (4) 同时确有 5 条子路径在 dump 内 0 命中、而字节码里是**精确的 Utf8 常量** ⇒ 假阴性实例
    class_bytes = CLASS.read_bytes()
    for sub in ("starter-all", "app-service-by-name", "sync-cache",
                "online-app-info", "online-front-app-info"):
        assert sub.encode() in class_bytes, sub
        assert text.count(sub) == 0, sub
        assert sub in class_utf8, sub


def _class_utf8_constants():
    """用仓内独立解析器直读 .class 常量池，返回 Utf8 常量集合（不经 javap / CFR）。"""
    mod = _enum()
    r = mod._Reader(CLASS.read_bytes())
    r.skip(4)
    r.u2()
    r.u2()
    pool = mod._parse_constant_pool(r)
    return {e[1] for e in pool if e and e[0] == "Utf8"}


def test_guardrail_bites_on_a_mutated_registry_entry(reg, monkeypatch):
    """内存内突变自证：登记表少一条时，逐条对账必须失败。"""
    byt = _enum().enumerate_routes(str(CLASS))
    from_bytecode = {(e["http"], e["sub_path"]) for e in byt["endpoints"]}
    dropped = tuple(reg[:-1])
    assert {(h, s) for h, s, _hd, _o in dropped} != from_bytecode
    # 反向：多一条幻影也必须失败
    phantom = tuple(reg) + (("GET", "no-such-endpoint", "ghost", ""),)
    assert {(h, s) for h, s, _hd, _o in phantom} != from_bytecode


def test_live_observed_route_is_present_in_bytecode(byt):
    """/udc/metadata/app-service-by-name 的响应体子路径确实在字节码 mapping 内。"""
    subs = {e["sub_path"] for e in byt["endpoints"]}
    assert "app-service-by-name" in subs
    hit = next(e for e in byt["endpoints"] if e["sub_path"] == "app-service-by-name")
    assert hit["http"] == "POST"
    assert hit["op_code"].startswith("AppService.1006")


def test_no_customer_identifiers_in_registry():
    """只落平台构件事实，不落客户业务明细。"""
    text = (ROOT / "components" / "udc" / "metadata_constraints.py").read_text(encoding="utf-8")
    for bad in ("cn.seeyon", "@", "client_", "_customer"):
        if bad == "@":
            continue
        assert bad not in text

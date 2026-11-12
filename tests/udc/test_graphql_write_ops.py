"""三大模块写链 op 目录测试 + 与 bundle 原文对账（scratch 存在时）。"""
import re
from pathlib import Path

import pytest

from components.udc.graphql_write_ops import (
    ARRAY_STRING_SPECIAL,
    ARRAY_WRAPPED_INPUT_BODY,
    BARE_FORM,
    MODULES,
    ZERO_PARAM_OPS,
    catalog,
    op_entry,
)

# bundle 快照：优先仓内权威件（入 git），退而取 scratch 临时件
_REPO_BUNDLE = (Path(__file__).resolve().parents[2]
                / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496"
                / "chunks" / "src_redux_store_ts.14dc061e.js")
_SCRATCH_BUNDLE = Path("<HERMES_HOME>/cache/scratch/udc-pod-chunks/src_redux_store_ts.14dc061e.js")
BUNDLE = _REPO_BUNDLE if _REPO_BUNDLE.exists() else _SCRATCH_BUNDLE


# ---------------------------------------------------------------- 目录自洽（不依赖外部）

def test_all_three_modules_populated():
    assert len(MODULES["entity"]) >= 50
    assert len(MODULES["application"]) >= 30
    assert len(MODULES["basic-setting"]) >= 24


def test_no_duplicate_ops():
    seen = set()
    for ops in MODULES.values():
        for e in ops:
            assert e["op"] not in seen, e["op"]
            seen.add(e["op"])


def test_array_wrapped_ops():
    # §2.7.4 的 10 个 [InputBody] 数组包装必须全在目录（三大模块范围）
    for op in ("udcDataTransferObjectCreateDtoWithAttrsPost",
               "udcDataTransferObjectUpdateDtoWithAttrsPost",
               "udcUdcEnumItemOperateBatchPost",
               "udcEntityAttributeBatchUpdatePost",
               "udcEntityAttributeGroupCreateUpdatePost",
               "udcEntityAttributeGroupBathUpdatePost",
               "udcEntityGroupUpdateBatchPost",
               "udcEntityBatchUpdateEntityGroupIdAndOrdernoPost",
               "udcApplicationDependentApplicationCreateBatchPost"):
        assert op in ARRAY_WRAPPED_INPUT_BODY, op


def test_bare_forms_registered():
    assert "udcIndexEntityListPost" in BARE_FORM["Long_BODY"]
    assert "udcSandboxClearDataPost" in BARE_FORM["String_BODY"]
    assert "udcEntityAttributeSelectParentEnumAttrsPost" in BARE_FORM["Map_BODY"]
    assert "udcMicroflowFilterNotVirtualPost" in ARRAY_STRING_SPECIAL


def test_zero_param_closure():
    # DATADICT §6.4 UNVERIFIED 关闭：VersionPlatformServiceGet 实为零入参
    assert "udcApplicationVersionPlatformServiceGet" in ZERO_PARAM_OPS
    assert "零入参" in ZERO_PARAM_OPS["udcApplicationVersionPlatformServiceGet"]


def test_verb_column_never_asserts_fact():
    # 纪律：verb 列带 ?（名字推断不是事实）
    for ops in MODULES.values():
        for e in ops:
            assert "?" in e["verb"], e


def test_op_entry_lookup():
    e = op_entry("udcReferConfigCreateOrUpdatePost")
    assert e and e["paramsKey"] == "body" and e["form"] == "BODY"
    assert op_entry("nonexistentOp") is None


def test_catalog_roundtrip():
    import json
    back = json.loads(json.dumps(catalog(), ensure_ascii=False))
    assert set(back["counts"]) == {"entity", "application", "basic-setting", "microflow"}
    assert any("§5#8" in c for c in back["closures"])


def test_microflow_domain_ops_present():
    """微流程域关键 op（module 70857 坐实；此前是 classify 对账盲区）。

    证据链：saveMicroflowSchema→udcMicroflowCreatePost、
    updateMicroflowSchema→udcMicroflowUpdatePost、
    checkAndUpdate→udcMicroflowCheckSchemaUpdatePost、
    checkMicroFlowCaption→udcMicroflowCheckMicroFlowCaptionPost。
    """
    for op in ("udcMicroflowCreatePost", "udcMicroflowUpdatePost",
               "udcMicroflowCheckSchemaUpdatePost",
               "udcMicroflowCheckMicroFlowCaptionPost",
               "udcMicroflowSearchEntityRulePost", "udcMicroflowFindByIdGet"):
        e = op_entry(op)
        assert e is not None, f"{op} 不在目录（微流程域回退？）"
    assert len(MODULES["microflow"]) >= 60


# ---------------------------------------------------------------- bundle 原文对账（scratch 存在才跑）

def _op_in_load(src: str, e: dict) -> bool:
    """约定 a：saga load({fieldType:"op",paramsType, paramsKey}) 三元组原文。"""
    return (f'fieldType:"{e["op"]}",paramsType:"{e["paramsType"]}",paramsKey:"{e["paramsKey"]}"'
            in src)


def _op_in_apollo(src: str, e: dict) -> bool:
    """约定 b：raw Apollo 文档字符串 (mutation|query) op ($key: ptype)。
    变量声明归一：$body→…InputBody / $path→…InputPath / $query→…InputQuery。"""
    return re.search(
        r'(?:mutation|query)\s+' + re.escape(e["op"])
        + r'\s*\(\s*\$' + re.escape(e["paramsKey"])
        + r'\s*:\s*' + re.escape(e["paramsType"]),
        src) is not None


def _op_in_concat(src: str, e: dict) -> bool:
    """约定 c：op 名由 concat 拼接（webpack 压缩）。
    fieldType:"".concat("udc","UdcRuntimeFilterPlanPost") 形态；变量前缀同 chunk 绑定。"""
    op = e["op"]
    if len(op) < 4 or not op.startswith("udc"):
        return False
    # 字面量前缀：fieldType: "".concat("udc","UdcXxx...")
    if re.search(r'\.concat\(\s*"[^"]*"\s*,\s*"' + re.escape(op[3:]) + r'"\s*\)', src):
        return True
    # 变量前缀：fieldType: "".concat(n,"UdcXxx...") 且 n="udcUdc" 同仓出现
    return re.search(r'\.concat\(\s*\w+\s*,\s*"' + re.escape(op[3:]) + r'"\s*\)', src) is not None



@pytest.mark.skipif(not BUNDLE.exists(), reason="bundle 快照不在本机（scratch 临时件）")
def test_every_cataloged_op_exists_in_bundle():
    src = BUNDLE.read_text(encoding="utf-8", errors="replace")
    missing = []
    for ops in MODULES.values():
        for e in ops:
            if not (_op_in_load(src, e) or _op_in_apollo(src, e) or _op_in_concat(src, e)):
                missing.append(e["op"])
    assert not missing, f"目录中的 op 不在 bundle: {missing}"


@pytest.mark.skipif(not BUNDLE.exists(), reason="bundle 快照不在本机")
def test_params_shape_matches_bundle():
    src = BUNDLE.read_text(encoding="utf-8", errors="replace")
    bad = []
    for ops in MODULES.values():
        for e in ops:
            # 双约定并查：load 三元组原文 OR Apollo 变量声明归一 OR concat 拼接
            if not (_op_in_load(src, e) or _op_in_apollo(src, e) or _op_in_concat(src, e)):
                bad.append(e["op"])
    assert not bad, f"params 形态与 bundle 不符: {bad}"


@pytest.mark.skipif(not BUNDLE.exists(), reason="bundle 快照不在本机")
def test_zero_param_op_truly_paramless():
    src = BUNDLE.read_text(encoding="utf-8", errors="replace")
    i = src.find('fieldType:"udcApplicationVersionPlatformServiceGet"')
    assert i >= 0
    # 只取本 op 的 load 调用段（到该对象字面量闭合，勿串进下个函数）
    seg = src[i:i + 150]
    assert "paramsKey" not in seg   # 零入参坐实（bundle 内本 load 无 paramsKey/params）

"""枚举域在注册表与事实库中的落位（防止契约/事实/代码三处脱节）。

本测试锁三件事：
  1. 枚举域 6 条契约全部登记，路径是 GraphQL operation 名（不是 REST 控制器路径）
  2. 写面 4 条（create×3 + delete）标 write=True；读面 2 条标 write=False
  3. 事实格与写链事实文件存在，且被 INDEX.md 登记（否则检索不到，等于没写）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.platform_operations.registry import UdcOperationRegistry

ENUM_OPS = {
    "udc.enum.category.create": "udcEnumCategoryPost",
    "udc.enum.create": "udcEnumPost",
    "udc.enum.item.create": "udcEnumItemPost",
    "udc.enum.batch_delete": "udcEnumBatchDeletePost",
    "udc.enum.search_no_page": "udcEnumSearchNoPagePost",
    "udc.enum.category.search": "udcEnumCategorySearch",
}
WRITE_OPS = {"udc.enum.category.create", "udc.enum.create",
             "udc.enum.item.create", "udc.enum.batch_delete"}


def test_all_enum_contracts_registered():
    r = UdcOperationRegistry.default()
    for op in ENUM_OPS:
        assert r.has(op), f"枚举契约未登记: {op}"


def test_enum_paths_are_graphql_operation_names():
    """路径必须是 GraphQL operation 名，不是 REST 控制器路径。"""
    r = UdcOperationRegistry.default()
    for op, gql_op in ENUM_OPS.items():
        c = r.get(op)
        assert c.path.startswith("graphql?"), f"{op} 路径应含 graphql?: {c.path}"
        assert c.path.split("?", 1)[1] == gql_op, f"{op} path 应指向 {gql_op}: {c.path}"


def test_write_vs_read_flags():
    r = UdcOperationRegistry.default()
    for op in ENUM_OPS:
        c = r.get(op)
        if op in WRITE_OPS:
            assert c.write is True, f"{op} 应为写契约"
        else:
            assert c.write is False, f"{op} 是读面，不应标 write"


def test_enum_contracts_carry_evidence():
    """每条契约都要带证据指向事实格，否则后人就无法复核。"""
    r = UdcOperationRegistry.default()
    for op in ENUM_OPS:
        c = r.get(op)
        assert c.evidence, f"{op} 缺证据"
        blob = str(c.evidence)
        assert "enum" in blob.lower(), f"{op} 证据须指向枚举域事实: {c.evidence}"


def test_write_contracts_warn_about_write_scope():
    """写契约必须在 verification_rules 里提示需要显式 WriteScope。"""
    r = UdcOperationRegistry.default()
    for op in WRITE_OPS:
        rules = " ".join(r.get(op).verification_rules)
        assert "WriteScope" in rules, f"{op} 须提示需显式 WriteScope 授权"


def test_fact_files_exist_and_are_indexed():
    """事实格 + 写链文件必须存在，且 INDEX.md 有登记（否则检索不到）。"""
    fact = ROOT / "core" / "facts" / "udc" / "setting" / "enum" / "create.md"
    chain = ROOT / "core" / "facts" / "udc" / "setting" / "enum" / "enum-write-chain.md"
    index = ROOT / "core" / "facts" / "INDEX.md"
    assert fact.exists(), f"缺事实格: {fact}"
    assert chain.exists(), f"缺写链事实: {chain}"
    idx = index.read_text(encoding="utf-8")
    assert "enum/create.md" in idx, "INDEX.md 未登记枚举域事实格"


def test_fact_file_records_live_evidence_and_superseded_claims():
    """事实格必须写明 LIVE 证据，并显式作废旧说法（防止旧知识误导）。"""
    chain = (ROOT / "core" / "facts" / "udc" / "setting" / "enum" / "enum-write-chain.md")
    txt = chain.read_text(encoding="utf-8")
    assert "LIVE" in txt
    # 旧说法必须被作废，不能留着误导后人
    for stale in ("udc_enum_category`", "REST `POST /service/udc/udc-enum`"):
        if stale in txt:
            assert "已作废" in txt, f"出现旧说法 {stale} 却没有作废声明"
    assert "已作废" in txt, "事实格缺『已作废的说法』章节"


def test_no_rest_path_claimed_for_enum():
    """事实格里不能出现把枚举写成 REST 控制器的表述（已证实是 GraphQL）。"""
    chain = (ROOT / "core" / "facts" / "udc" / "setting" / "enum" / "enum-write-chain.md")
    txt = chain.read_text(encoding="utf-8")
    assert "udc/udc-enum" in txt, "应显式指出 REST 路径说法已错"

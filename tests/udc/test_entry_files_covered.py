"""入口文件总闸门：每个 README/INDEX 都必须被某个测试守住，且自身不腐坏。

为什么有这个测试
----------------
2026-11-07 前，仓库陆续补了十几个目录入口（README.md），每个都配了专用闸门。
但实测发现一个问题：**16 个闸门测试只覆盖了 34 个 README/INDEX 中的 9 个**。
剩下 25 个没有任何测试——它们腐坏时没人知道，而"入口登记的数字过期"恰恰是最容易发生的腐坏
（本次整理过程中，我自己的入口闸门就连续三轮抓到我自己写的过期数字）。

本测试做两件事，都是与具体目录无关的通用检查：

1. **覆盖登记**：每个 README/INDEX 必须出现在 `ENTRY_GATES` 的映射里，
   指向至少一个"守它的测试"。新增入口而不登记 = 这个入口是无人看守的。
2. **通用腐坏检查**：入口里所有「`文件名` | 数字 | 数字」形态的表格行，
   若该文件名在本目录（或同级）真实存在，则数字必须与磁盘一致。
   这条不需要为每个目录手写正则，能自动覆盖所有"规模表"形态的入口。

注意：`ENTRY_GATES` 是**登记表，不是免检证**。它保证"有人管"，不保证"管得好"。
专门闸门（如 test_docs_root_layout.py）负责各目录的细则。
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SKIP_PARTS = {".git", "_attic_pending", ".venv", "__pycache__", "scratch", ".pytest_cache",
              "node_modules", "_attic", ".idea"}

# 入口文件 → 守它的测试（相对 tests/ 的路径）。新增入口必须在这里登记。
ENTRY_GATES = {
    "README.md": ["test_documentation_contract.py"],
    "docs/README.md": [
        "udc/test_docs_py_refs_alive.py",
        "udc/test_docs_root_layout.py",
    ],
    "docs/audit/README.md": ["test_documentation_contract.py"],
    "docs/audit/artifacts/service-flow-20261103/README.md": ["udc/test_service_flow_layout.py"],
    "docs/audit/artifacts/api-usage/README.md": ["udc/test_api_usage_layout.py"],
    "docs/ledger/README.md": ["udc/test_ledger_layout.py"],
    "core/facts/udc/application/README.md": ["udc/test_application_facts_layout.py"],
    "docs/operation-contracts/udc/application/README.md": [
        "udc/test_application_contracts_override.py",
        "udc/test_application_contracts_layout.py",
    ],
    "docs/operation-contracts/udc/bi/README.md": ["udc/test_bi_contracts_layout.py"],
    "docs/operation-contracts/udc/entity/README.md": ["udc/test_entity_contracts_layout.py"],
    "docs/operation-contracts/udc/menu/README.md": ["udc/test_menu_contracts_layout.py"],
    "docs/operation-contracts/udc/flow/README.md": ["udc/test_flow_contracts_layout.py"],
    "docs/operation-contracts/udc/runtime/README.md": ["udc/test_runtime_contracts_layout.py"],
    "docs/operation-contracts/udc/page/README.md": ["udc/test_page_contracts_layout.py"],
    "docs/operation-contracts/udc/role/README.md": [
        "udc/test_role_contracts_override.py",
        "udc/test_role_contracts_layout.py",
    ],
    "docs/operation-contracts/udc/publish/README.md": ["udc/test_publish_resource_rule_layout.py"],
    "docs/operation-contracts/udc/resource/README.md": ["udc/test_publish_resource_rule_layout.py"],
    "docs/operation-contracts/udc/rule/README.md": ["udc/test_publish_resource_rule_layout.py"],
    "docs/audit/artifacts/u5-storage/README.md": ["udc/test_u5_storage_layout.py"],
    "docs/audit/artifacts/README.md": ["udc/test_artifacts_root_layout.py"],
    "docs/audit/artifacts/extension-surface-20261029/README.md": ["udc/test_extension_usage_assets.py"],
    "docs/audit/artifacts/extension-surface-20261029/packages/README.md":
        ["udc/test_extension_surface_packages_layout.py"],
    "docs/audit/artifacts/extension-surface-20261029/dto-fields/README.md":
        ["udc/test_extension_usage_assets.py"],
    "docs/audit/artifacts/decompiled/env358/README.md": ["udc/test_artifacts_root_layout.py"],
    "docs/audit/artifacts/decompiled/r37_cfr/README.md": ["udc/test_artifacts_root_layout.py"],
    "docs/audit/role/README.md": ["udc/test_role_audit_layout.py"],
    "docs/audit/udc-semantics/README.md": ["udc/test_udc_semantics_index.py"],
    "docs/audit/entity-field-matrix/README.md": ["udc/test_entity_field_matrix_index.py"],
    "docs/audit/column-discovery/README.md": ["udc/test_column_discovery_index.py"],
    "docs/audit/microflow-acceptance-suite/README.md": ["udc/test_artifacts_root_layout.py"],
    "docs/audit/microflow-acceptance-suite/INDEX.md": ["udc/test_artifacts_root_layout.py"],
    "docs/capability/README.md": [
        "udc/test_capability_docs_self_consistency.py",
        "udc/test_capability_docs_layout.py",
    ],
    "docs/operation-contracts/udc/README.md": ["udc/test_operation_contracts_udc_layout.py"],
    "docs/operation-contracts/README.md": ["udc/test_setting_contracts_layout.py"],
    "docs/operation-contracts/udc/setting/README.md": [
        "udc/test_setting_contracts_layout.py",
        "udc/test_setting_contracts_override.py",
    ],
    "docs/operation-contracts/udc/microflow/README.md": [
        "udc/test_microflow_contracts_override.py",
        "udc/test_setting_contracts_layout.py",
    ],
    "docs/operation-contracts/udc/column/README.md": ["udc/test_setting_contracts_layout.py"],
    "docs/plans/README.md": ["test_documentation_contract.py"],
    "core/facts/standard-product/README.md": ["udc/test_standard_product_anchors.py"],
    "core/facts/bpm/README.md": ["udc/test_bpm_facts_layout.py"],
    "core/facts/spi/README.md": ["udc/test_spi_facts_layout.py"],
    "core/facts/udc/README.md": ["udc/test_udc_facts_root_layout.py"],
    "core/facts/udc/setting/README.md": ["udc/test_setting_facts_layout.py"],
    "core/facts/udc/entity/README.md": ["udc/test_entity_facts_layout.py"],
    "core/facts/udc/entity/evidence/entity-surface-2026-10-23/README.md":
        ["udc/test_entity_facts_layout.py"],
    "core/facts/INDEX.md": ["udc/test_facts_index_anchors.py", "udc/test_fact_discoverability.py"],
    "core/facts/udc/microflow/README.md": ["udc/test_fact_discoverability.py"],
    "core/facts/udc/microflow/INDEX.md": ["udc/test_fact_discoverability.py"],
    "core/facts/udc/write-chain/README.md": ["udc/test_facts_index_anchors.py"],
    "core/facts/udc/expression/README.md": [
        "udc/test_fact_discoverability.py",
        "udc/test_dirs_without_readme_are_covered.py",
    ],
    "adapters/README.md": ["udc/test_dirs_without_readme_are_covered.py"],
    "core/facts/spi/evidence/README.md": ["udc/test_facts_index_anchors.py"],
    "core/role/README.md": ["test_documentation_contract.py"],
    "core/tools/udc/README.md": ["test_documentation_contract.py"],
    "config/README.md": ["test_documentation_contract.py"],
    "skills/README.md": ["test_documentation_contract.py"],
    "installer/README.md": ["test_documentation_contract.py"],
}

# 「`文件名` | 1,234 | 567」形态的规模行（行尾允许更多列）
SIZE_ROW = re.compile(r"^\|\s*\**`([^`|]+\.(?:md|json|py|txt|yaml|yml))`\**\s*\|\s*\**([\d,]+)\**\s*\|\s*\**([\d,]+)\**", re.M)


def _entry_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_PARTS and not d.startswith(".")]
        for f in filenames:
            if f in ("README.md", "INDEX.md"):
                out.append(Path(dirpath) / f)
    return sorted(out)


def test_every_entry_is_registered():
    entries = _entry_files()
    assert entries, "一个入口文件都没找到，路径判定有问题"
    rel = {str(p.relative_to(ROOT)).replace("\\", "/") for p in entries}
    missing = sorted(rel - set(ENTRY_GATES))
    assert not missing, (
        "这些入口文件没有登记「谁守它」——新增入口必须在 ENTRY_GATES 里登记：\n  "
        + "\n  ".join(missing)
    )
    stale = sorted(set(ENTRY_GATES) - rel)
    assert not stale, (
        "ENTRY_GATES 里登记了不存在的入口（改名或删了？）：\n  " + "\n  ".join(stale)
    )


def test_registered_gates_exist():
    tests_dir = ROOT / "tests"
    existing = {str(p.relative_to(tests_dir)).replace("\\", "/") for p in tests_dir.rglob("*.py")}
    bad = []
    for entry, gates in ENTRY_GATES.items():
        for g in gates:
            if g not in existing:
                bad.append("%s -> %s（测试文件不存在）" % (entry, g))
    assert not bad, "登记表指向了不存在的测试：\n  " + "\n  ".join(bad)


def test_size_tables_are_not_stale():
    """所有入口里「文件名 | 字节 | 行数」形态的行，必须与磁盘一致。

    这条是通用的：不依赖每个目录的专属正则，能自动发现任何规模表腐坏。
    """
    bad = []
    for entry in _entry_files():
        text = entry.read_text(encoding="utf-8", errors="replace")
        for name, size_s, lines_s in SIZE_ROW.findall(text):
            # 在该入口所在目录、其父目录、仓库根依次找
            cands = [entry.parent / name, entry.parent.parent / name, ROOT / name]
            target = next((c for c in cands if c.is_file()), None)
            if target is None:
                continue  # 指向别处的文件，交给该目录的专属闸门
            raw = target.read_bytes()
            size = target.stat().st_size
            # 行数口径必须是 splitlines()，不能用 count(b"\n")：
            # 全库有 16 份 md 没有结尾换行（如 docs/operation-contracts/udc/rule/
            # RULE-GENERATION-CONTRACT-20261019.md），两者会差 1，把正确的表判成腐坏。
            nlines = len(raw.decode("utf-8", errors="replace").splitlines())
            if size != int(size_s.replace(",", "")):
                bad.append("%s: %s 写 %s B 磁盘 %d" % (
                    entry.relative_to(ROOT), name, size_s, size))
            if nlines != int(lines_s.replace(",", "")):
                bad.append("%s: %s 写 %s 行 磁盘 %d" % (
                    entry.relative_to(ROOT), name, lines_s, nlines))
    assert not bad, "入口规模表已腐坏：\n  " + "\n  ".join(bad)

def test_test_files_root_resolves_to_repo():
    """测试文件的 ROOT 必须真的解析到仓库根，不能靠 sys.path 侥幸。

    2026-11-07 这个错犯了 5 次（tests/udc/x.py 写成 parents[3]，或 tests/x.py 写成 parents[2]）。
    症状：整组测试全红且报"缺 <文件>"，看起来像文件丢了，实际是基准错了一层。

    判据不看写法，**看实际解析结果**——
    因为 `dirname(dirname(abspath(__file__)))` 与 `parents[1]` 等价，
    而 `Path(__file__).parents[2]` 在 tests/x.py 里会指到仓库根之上（<EVIDENCE_ROOT>）。
    """
    import re
    bad = []
    for p in (ROOT / "tests").rglob("*.py"):
        rel = p.relative_to(ROOT).as_posix()
        depth = len(p.relative_to(ROOT / "tests").parts) - 1  # tests/x.py=0, tests/sub/x.py=1
        expect = p.parents[depth + 1]   # tests/x.py → parents[1]；tests/sub/x.py → parents[2]
        # 该文件里 ROOT 应等于 expect
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not re.match(r"^ROOT\s*=", s):
                continue
            m = re.search(r"parents\[(\d+)\]", s)
            if m:
                got = p.parents[int(m.group(1))]
            elif "dirname(os.path.dirname" in s or s.count("dirname") >= 2:
                got = p.parent.parent
            else:
                continue  # 其他写法（如 ROOT = Path(__file__).parent）不在此判据内
            if got != expect:
                bad.append("%s: ROOT 解析到 %s，应为 %s" % (rel, got, expect))
    assert not bad, (
        "这些测试文件的 ROOT 没解析到仓库根（会报「缺文件」，像文件丢了其实是路径错）：\n  "
        + "\n  ".join(bad))

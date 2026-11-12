"""设置域 · 枚举的三类资产必须分开且归位正确。

用户要求（2026-10-20）：
  「我们现在推进的是设置模块里面的枚举……这个要放到对应的文件夹，
    脚本和事实和 skill 都得分开」

本测试锁住这个结构，防止以后又被摊平到仓库各处：

  实现/脚本   components/udc/setting/enum_*.py
  事实        core/facts/udc/setting/enum/
  操作契约    docs/operation-contracts/udc/setting/enum-contracts.md
  操作脚本    tools/core/setting/
  skill       skills/xiaozhua-udc-setting/SKILL.md
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

SETTING_IMPL = [
    "enum_constraints.py",
    "enum_model.py",
    "enum_reference_analysis.py",
    "settings_tab_model.py",
    "settings_sub_api_model.py",
]


def test_setting_impl_package_exists():
    """设置域实现必须在自己的包里。"""
    pkg = ROOT / "components" / "udc" / "setting"
    assert pkg.is_dir(), f"缺设置域实现包: {pkg}"
    assert (pkg / "__init__.py").exists(), "设置域包缺 __init__.py"


def test_enum_impl_files_are_in_setting_package():
    """枚举的实现文件不能还留在 components/udc/ 根上。"""
    for name in SETTING_IMPL:
        assert (ROOT / "components" / "udc" / "setting" / name).exists(), \
            f"{name} 未归位到 components/udc/setting/"
        assert not (ROOT / "components" / "udc" / name).exists(), \
            f"{name} 仍留在 components/udc/ 根上（应归设置域）"


def test_setting_impl_does_not_leak_to_other_domains():
    """设置域的实现不能被放到别的域目录里。"""
    for other in ("entity", "page", "menu", "rule", "microflow", "application"):
        d = ROOT / "components" / "udc" / other
        if not d.is_dir():
            continue
        for name in SETTING_IMPL:
            assert not (d / name).exists(), f"{name} 误置于 {other}/"


def test_facts_are_under_setting_domain():
    """事实格必须在 core/facts/udc/setting/enum/ 下。"""
    d = ROOT / "core" / "facts" / "udc" / "setting" / "enum"
    assert d.is_dir(), f"缺设置域事实目录: {d}"
    assert (d / "create.md").exists(), "缺九段式事实格 create.md"
    assert (d / "enum-write-chain.md").exists(), "缺写链事实 enum-write-chain.md"


def test_no_stale_enum_fact_locations():
    """旧的枚举事实位置不得残留（否则两处事实会互相矛盾）。"""
    assert not (ROOT / "core" / "facts" / "udc" / "enum").exists(), \
        "旧位置 core/facts/udc/enum/ 仍在（应已归位到 setting/）"
    assert not (ROOT / "core" / "facts" / "udc" / "write-chain" / "enum-write-chain.md").exists(), \
        "旧位置 write-chain/enum-write-chain.md 仍在"


def test_operation_contract_is_under_setting_domain():
    """操作契约在 docs/operation-contracts/udc/setting/ 下。"""
    p = ROOT / "docs" / "operation-contracts" / "udc" / "setting" / "enum-contracts.md"
    assert p.exists(), f"缺枚举操作契约: {p}"


def test_skill_is_separate_and_names_the_domain():
    """skill 独立成文件，且要说清自己属「设置」域。"""
    p = ROOT / "skills" / "xiaozhua-udc-setting" / "SKILL.md"
    assert p.exists(), f"缺设置域 skill: {p}"
    txt = p.read_text(encoding="utf-8")
    assert "设置" in txt, "skill 须声明自己属设置域"
    assert "枚举" in txt, "skill 须覆盖枚举子域"
    # skill 不能把实现代码写进去——那是 components 的事
    assert "build_enum_body" not in txt or "components/udc/setting" in txt, \
        "skill 提到构造器时应指向实现位置，而不是内联实现"


def test_skill_points_to_all_three_asset_kinds():
    """skill 必须分别指向脚本、事实、契约三处。"""
    txt = (ROOT / "skills" / "xiaozhua-udc-setting" / "SKILL.md").read_text(encoding="utf-8")
    assert "components/udc/setting" in txt, "skill 未指向实现位置"
    assert "core/facts/udc/setting" in txt, "skill 未指向事实位置"
    assert "docs/operation-contracts/udc/setting" in txt, "skill 未指向契约位置"


def test_tool_scripts_under_setting():
    """枚举操作脚本应在 tools/core/setting/ 下。"""
    d = ROOT / "tools" / "core" / "setting"
    assert d.is_dir(), f"缺设置域脚本目录: {d}"


def test_facts_index_points_to_new_location():
    """INDEX.md 的登记行须仍指向枚举事实（内容可含旧路径字样，但要有登记）。"""
    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8")
    assert "enum" in idx, "INDEX.md 未登记枚举事实"

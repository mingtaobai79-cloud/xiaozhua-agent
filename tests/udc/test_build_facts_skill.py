"""事实 → skill 构造器的回归测试。

核心断言：构造器**不能把半句话当规则**。
历史问题：早期版本抓 `★` 行，产出一堆「……它们来自其它模块，」「……整个从可选范围里移除**，」
这类残句；skill 里全是断头话，等于没有索引价值。
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "core" / "_meta"))

import build_facts_skill as B  # noqa: E402


SAMPLE = """
# 某域事实

## 铁律

- `category` 必须传字符串枚举名，传数字直接 BOOT_3000
- 事件绑的是 DTO 不是实体，必须指向数据传输对象 id
- 我在这一轮又踩了一次，这个坑必须记住不要重犯
- 这就是为什么上次会失败的原因
- 半句话的条目以逗号结尾，会被丢掉，
- 太短

## 1. 正文

★ 这是一条回退路径下的要点，完整可读且信息量足够
"""


def test_extracts_iron_law_block():
    rows = B.diff_table(SAMPLE)
    assert any("category" in r for r in rows)
    assert any("DTO" in r for r in rows)


def test_drops_half_sentences():
    """以逗号/顿号/冒号结尾的半句必须丢。"""
    rows = B.diff_table(SAMPLE)
    assert not any(r.endswith("，") for r in rows)
    assert not any("半句话的条目" in r for r in rows)


def test_drops_first_person_narration():
    """「我/本轮/这次」开头是过程叙述，不是规则。"""
    rows = B.diff_table(SAMPLE)
    assert not any(r.startswith(("我", "本轮", "这次")) for r in rows)


def test_drops_too_short():
    assert not any(len(r) < 16 for r in B.diff_table(SAMPLE))


def test_falls_back_to_star_lines():
    text = "no iron law block here\n\n★ 这是一条足够长的回退要点，能被提取出来\n"
    rows = B.diff_table(text)
    assert any("回退要点" in r for r in rows)


def test_level_prefers_strongest():
    assert B.level_of("LIVE PASS，已回读") == "LIVE PASS"
    assert B.level_of("LIVE 但渲染未验") == "LIVE"
    assert B.level_of("反编译字节码坐实，未跑") == "VERIFIED_STATIC_BYTECODE"
    assert B.level_of("BLOCKED-ENV 登录过期") == "BLOCKED-ENV"
    assert B.level_of("什么都还没试") == "UNVERIFIED"


def test_pii_scan_catches_customer_markers():
    hits = B.pii_scan("app datamigration9000000000000000001")
    assert hits, "客户应用名必须被自检拦下"


def test_pii_scan_passes_clean_text():
    assert B.pii_scan("`category` 必须传字符串枚举名 `ENTITY`") == []


def test_title_and_evidence_extraction():
    assert B.title_of(SAMPLE, "x") == "某域事实"
    ev = B.evidence_section("R-E8 Evidence\n- docs/audit/artifacts/x/y.json\n- 复现 python tools/x.py\n")
    assert any("docs/audit" in e for e in ev)


def test_scan_constraints_finds_validators(tmp_path):
    p = tmp_path / "demo_constraints.py"
    p.write_text(
        '"""Demo constraints."""\n\n'
        "DOMAIN_NODES = {}\n\n\n"
        "def validate_rule_scope(schema: dict, group_type) -> list[str]:\n"
        "    return []\n\n\n"
        "def validate_other(x: dict) -> list[str]:\n"
        "    return []\n",
        encoding="utf-8",
    )
    got = B.scan_constraints([p])
    assert got and "validate_rule_scope" in " ".join(got[0]["validators"])
    assert "DOMAIN_NODES" in got[0]["constants"]

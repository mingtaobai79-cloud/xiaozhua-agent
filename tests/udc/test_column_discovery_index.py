"""`docs/audit/column-discovery/` 是列域的**上游原始取证**，其入口必须承载更正索引。

为什么值得单独一条闸门：
这个域最初被判定为 VACUUM（近乎零证据），根因不是"没查"，而是**查错了对象名** ——
按 `udc_column` / `udc_portal` 扫 DB 命中 0，于是结论是"栏目域没有表"；
真实对象是 `udc_portlet`，四张表全在（含跨 schema 两张）。

⇒ 这是全库最好的「**负证据被名字骗了**」样本：查错名字得到的 0 命中，
   和真的没有，输出长得一模一样。

守五件事：
1. 三份正文都要在入口被点名（不许漏，尤其 S2 那 10 处）。
2. 入口的规模声明（3 份 / 61,911 B / 12 份原始件）必须与磁盘一致。
3. 最贵那条（对象名 `udc_portlet`、`portlet_id` = pageRelationId）必须在更正表里。
4. 「表述为真但结论误导」这条必须被显式命名 —— 它是最难自查的一类错。
5. 必须明写 `raw/*.json` 含运行态数据、不可外发（本目录**不在** EVIDENCE_DATA_DIRS 豁免内）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
D = ROOT / "docs" / "audit" / "column-discovery"
README = D / "README.md"
CORRECTION = re.compile(r"推翻|作废|纠正|撤回|更正|超额")


def _readme() -> str:
    assert README.is_file(), "column-discovery 缺入口 README.md"
    return README.read_text(encoding="utf-8")


def _bodies():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def _missing_names(text: str):
    """入口文本里没被点名的正文文件。抽成函数是为了让变异用例能对"挖空版"复用同一判据。"""
    return [f.name for f in _bodies() if f.name not in text]


def test_all_three_bodies_are_named():
    missing = _missing_names(_readme())
    assert not missing, "入口没点名这些正文：%s" % missing


def test_declared_sizes_match_disk():
    t = _readme()
    m = re.search(r"(\d+)\s*份\s*`\.md`（([\d,]+)\s*B）\+\s*(\d+)\s*份\s*`\.json`", t)
    assert m, "入口缺「N 份 .md（X B）+ M 份 .json」规模声明"
    claimed_n, claimed_bytes, claimed_raw = int(m.group(1)), int(m.group(2).replace(",", "")), int(m.group(3))
    bodies = _bodies()
    real_bytes = sum(len(f.read_bytes()) for f in bodies)
    assert len(bodies) == claimed_n, "声称 %d 份，磁盘 %d 份" % (claimed_n, len(bodies))
    assert real_bytes == claimed_bytes, "声称 %s B，实测 %d B" % (claimed_bytes, real_bytes)
    real_raw = len(list(D.rglob("*.json"))) + len(list(D.rglob("*.txt")))
    assert real_raw == claimed_raw, "声称 %d 份 json/txt，实测 %d 份" % (claimed_raw, real_raw)


def test_correction_count_declared_matches_disk():
    """声明「15 处更正标记」必须等于磁盘实测（按文件细分）。"""
    t = _readme()
    m = re.search(r"共\s*\*\*(\d+)\s*处\*\*更正标记", t)
    assert m, "入口缺「共 N 处更正标记」声明"
    claimed = int(m.group(1))
    detail = {f.name: len(CORRECTION.findall(f.read_text(encoding="utf-8", errors="replace")))
              for f in _bodies()}
    total = sum(detail.values())
    assert total == claimed, "声称 %d 处，实测 %d 处（明细 %s）" % (claimed, total, detail)
    assert all(n > 0 for n in detail.values()), (
        "有正文本已无更正标记（%s）—— 若确已清理，应同步下调入口声明" % detail)


def test_most_expensive_corrections_present():
    """对象名与 portlet_id 映射这两条必须在表里。"""
    t = _readme()
    must = [
        ("udc_portlet", "① 对象名：真实对象是 Portlet，不是 udc_column/udc_portal"),
        ("pageRelationId", "③ portlet_id 映射：= pageRelationId，不是 udc_portlet.id"),
        ("表述**为真但结论误导**", "② 「表述为真、结论误导」—— 最难自查的一类错"),
    ]
    missing = [why for needle, why in must if needle not in t]
    assert not missing, "入口缺这些高价更正：%s" % missing


def test_negative_evidence_lesson_is_stated():
    """必须明写「关键词 0 命中 ≠ 域不存在」——这是本目录存在的理由。"""
    t = _readme()
    assert "查错名字" in t or "查的名字" in t, (
        "入口没写「负证据要先问'我查的名字对吗'」——这等于把本目录最有价值的一课丢了")
    assert "0 命中" in t, "入口没提 0 命中这个陷阱的具体形态"


def test_raw_artifacts_are_marked_not_for_distribution():
    """raw/*.json 含运行态数据，必须显式标注不外发（本目录不在豁免目录内）。"""
    t = _readme()
    assert "不要外发" in t or "不可外发" in t, "入口没标注 raw/*.json 不可外发"
    assert "EVIDENCE_DATA_DIRS" in t or "豁免" in t, (
        "入口没说明「本目录不在 EVIDENCE_DATA_DIRS 豁免内」——不说明会被误当成已豁免")


def test_gate_bites_on_mutation():
    """变异用例：把入口里的文件名全部抹掉后，第 1 条断言必须变红。

    没有变异用例的闸门，无法证明它真的在守东西 —— 一个恒真的断言也能"通过"。
    """
    bodies = _bodies()
    assert bodies, "本目录已无正文，闸门无对象，应复核是否该删"
    assert not _missing_names(_readme()), "前提不成立：正常 README 本应全部点名"

    gutted = _readme()
    for b in bodies:
        gutted = gutted.replace(b.name, "").replace(b.stem, "")
    still_missing = _missing_names(gutted)
    assert len(still_missing) == len(bodies), (
        "变异用例失效：抹掉文件名后仍有 %d 个被判「已点名」—— 说明断言会假通过"
        % (len(bodies) - len(still_missing)))

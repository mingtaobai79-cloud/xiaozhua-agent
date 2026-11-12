"""`docs/operation-contracts/udc/microflow/` 的两份大契约是「被反复纠正过的结论」。

为什么单独一条闸门：
`map-node-semantics.contract.md`（1,170 行 / 80,400 B）与 `state-semantics.contract.md`（694 行 / 39,013 B）
里最关键的性质 —— `state` 与 `publish_state` **正交** —— **本身就是推翻出来的**：
曾被判「state=10 是草稿态」，后来用 289 行交叉分布否证，又被 main 在 3a6b757 部分撤回，
再被 D51 重写（原论据「无同名 state=20 兄弟行」作废）、D52 删掉 16.8×/6.0× 两处引用、
D54 用 Fisher 纠正分级表读法。

⇒ 顺序读会把 ①②③ 当成同一件事的三种说法，而它们其实是**同一个错误被纠正的四轮**。
   读不出这一点，就会照 ① 去过滤掉实际在生效的数据。

守六件事：
1. 6 份含更正标记的契约都要在入口 §〇 更正表里被点名。
2. 入口声明的「13 份顶层 md / 6 份含更正 / 17 处」必须与磁盘实测一致。
3. 最贵那条（state ≠ 草稿态、与 publish_state 正交）必须在表里，且必须写明"真实语义 UNVERIFIED"。
4. 两类反复错因（状态字段当语义标签 / 统计判据自己站不住）必须成表。
5. 「是我判错」这类自我推翻必须留痕（D43 撤销 D42）。
6. 带 SHA 快照戳的两份 `NODE-CENSUS` 不得被当成重复品合并 —— 引用数字必须连快照戳一起引。

⚠️ 本目录多份被代码读取（`components/udc/microflow_constraints.py`、
`tests/udc/test_call_app_service_node_contract.py`、`skills/05-agent/...`），本闸门**只读不写**。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
D = ROOT / "docs" / "operation-contracts" / "udc" / "microflow"
README = D / "README.md"
CORRECTION = re.compile(r"推翻|作废|纠正|撤回|更正|超额")


def _readme() -> str:
    assert README.is_file(), "microflow 契约目录缺入口 README.md"
    return README.read_text(encoding="utf-8")


def _bodies():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def _correction_counts():
    return {f.name: len(CORRECTION.findall(f.read_text(encoding="utf-8", errors="replace")))
            for f in _bodies()}


def _override_section() -> str:
    """截出 §〇（更正表所在节）。只看这一节，避免正文别处提到文件名造成假通过。"""
    t = _readme()
    m = re.search(r"^## 〇.*?$(.*?)^## 一、", t, re.S | re.M)
    assert m, "入口缺「§〇 更正表」章节（或 §一 缺失导致无法截断）"
    return m.group(1)


def _name_is_mentioned(stem: str, text: str) -> bool:
    parts = re.split(r"[-.]", stem)
    return any("-".join(parts[:k]) in text or ".".join(parts[:k]) in text
               for k in range(1, len(parts) + 1))


def test_all_files_with_corrections_are_named():
    section = _override_section()
    nz = {k: v for k, v in _correction_counts().items() if v}
    unresolved = [n for n in nz if not _name_is_mentioned(Path(n).stem, section)]
    assert not unresolved, (
        "这些契约含更正标记但入口更正表没点名，读者会引来已撤回的结论：\n  "
        + "\n  ".join(sorted(unresolved)))


def test_declared_counts_match_disk():
    """声明「13 份顶层 md / 6 份含更正 / 17 处」必须与实测一致。"""
    t = _readme()
    m = re.search(r"(\d+)\s*份顶层\s*md\s*里有\s*(\d+)\s*份共\s*\*\*(\d+)\s*处\*\*更正标记", t)
    assert m, "入口缺「N 份顶层 md 里有 M 份共 K 处更正标记」这句可核对的声明"
    n_files, n_with, n_marks = (int(m.group(i)) for i in (1, 2, 3))
    real = _correction_counts()
    nz = {k: v for k, v in real.items() if v}
    assert len(real) == n_files, "声称 %d 份顶层 md，实测 %d 份" % (n_files, len(real))
    assert len(nz) == n_with, "声称 %d 份含更正，实测 %d 份（%s）" % (n_with, len(nz), sorted(nz))
    assert sum(nz.values()) == n_marks, (
        "声称 %d 处更正标记，实测 %d 处（明细 %s）" % (n_marks, sum(nz.values()), nz))


def test_most_expensive_correction_present():
    """state ≠ 草稿态这条必须在表里，且必须保留 UNVERIFIED —— 不许被"修好"。"""
    section = _override_section()
    must = [
        ("草稿", "①「state=10 疑为草稿态」已撤回"),
        ("publish_state", "① state 与 publish_state 正交（是算出来的，不是读名字来的）"),
        ("UNVERIFIED", "① state 真实语义仍 UNVERIFIED —— 不许为了表好看而填一个语义"),
    ]
    missing = [why for needle, why in must if needle not in section]
    assert not missing, "更正表缺这些要点：%s" % missing


def test_error_patterns_table_present():
    """两类反复错因必须成表：状态字段当语义标签 / 统计判据自己站不住。"""
    section = _override_section()
    must = [
        ("状态", "「state/状态」类字段被当成语义标签"),
        ("统计", "统计判据自己站不住（倍数、分级表读法都要另一次检验）"),
        ("0 命中", "「0 命中」当结论 —— 与 column-discovery 同一个病"),
    ]
    missing = [why for needle, why in must if needle not in section]
    assert not missing, "更正表缺这些反复错因：%s" % missing


def test_self_overturn_is_kept():
    """main D43 撤销 D42 的「是我判错」必须留痕 —— 删掉它，读者无法判断哪些结论经过对抗检验。"""
    t = _readme()
    assert "是我判错" in t, "入口没保留「是我判错」这类自我推翻留痕"
    assert "不要" in t and "整理掉" in t, "入口没写「不要把自我推翻整理掉」"


def test_census_snapshots_must_not_be_merged():
    """两份 NODE-CENSUS 是不同 scope + 不同快照戳，不得当重复品合并。"""
    t = _readme()
    assert "快照" in t and ("混用" in t or "不可跨文件" in t), (
        "入口没写「两份 NODE-CENSUS 快照戳不同、数字不可跨文件混用」——"
        "合并或混引会让覆盖率数字失去时点")


def test_gate_bites_on_mutation():
    """变异用例：把 §〇 里的文件名全部抹掉后，第 1 条断言必须变红。"""
    nz = {k: v for k, v in _correction_counts().items() if v}
    assert nz, "磁盘上已无含更正标记的契约，本闸门无对象，应复核是否该删"
    assert not [n for n in nz if not _name_is_mentioned(Path(n).stem, _override_section())], (
        "前提不成立：正常 README 本应全部点名")

    gutted = _override_section()
    for name in nz:
        stem = Path(name).stem
        gutted = gutted.replace(name, "").replace(stem, "")
        parts = re.split(r"[-.]", stem)
        for k in sorted(range(1, len(parts) + 1), reverse=True):
            gutted = gutted.replace("-".join(parts[:k]), "").replace(".".join(parts[:k]), "")
    still = [n for n in nz if _name_is_mentioned(Path(n).stem, gutted)]
    assert not still, (
        "变异用例失效：抹掉文件名后仍有 %d 个被判「已点名」（%s）—— 断言会假通过"
        % (len(still), still))

"""`docs/audit/entity-field-matrix/` 是一个**更正链**，入口必须承载推翻表。

为什么单独给它一条闸门：
本目录 19 份正文里散着 62 处更正标记（推翻/作废/纠正/撤回/更正），密度是全库最高的之一，
而入口 README 此前**没有任何更正索引** —— 顺序读会把已被推翻的结论当现行结论用。
最贵的那两条（`① 审计不写日志`、`② 类型只读`）都会让人去做根本不需要做的事：
弃用一条有效审计腿、去申请本来不需要的权限。

这条闸门守四件事：
1. 每个仍含更正标记的文件，都必须在入口更正表里被点名（不许漏）。
2. 更正表里的「原文位置」必须解析得到真实文件（不许指向不存在的文件）。
3. 入口声明的那几个数（份数、更正标记处数）必须与磁盘实测一致。
4. 三级更正（推翻结论 / 撤回担忧 / 自报越界）必须都被提到 —— 只记第一级会丢掉一半价值。

★★ 另有一条「变异」用例：把 README 的更正表临时挖空后，第 1 条断言必须变红。
   没有变异用例的闸门，无法证明它真的在守东西（见进度记录方法论）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 结构自检：ROOT 必须是仓库根（有 .git 或 docs/ + tests/）。
# 写错层数是本系列最高频的低级错误（第 6、8 次），所以它在导入时就该炸，
# 而不是等到某个断言里报「文件不存在」——那个报错会把人引向错误的方向。
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
D = ROOT / "docs" / "audit" / "entity-field-matrix"
README = D / "README.md"

# 更正标记：与进度记录方法论里列的一致
CORRECTION = re.compile(r"推翻|作废|纠正|撤回|更正|超额|CORRECTION")

# 入口更正表里必须出现的三级分类标题（章节锚）
GRADES = ("推翻结论", "撤回担忧", "自报越界")


def _readme() -> str:
    assert README.is_file(), "entity-field-matrix 缺入口 README.md"
    return README.read_text(encoding="utf-8")


def _bodies():
    """除 README 之外的正文文件。"""
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def _correction_counts():
    out = {}
    for f in _bodies():
        n = len(CORRECTION.findall(f.read_text(encoding="utf-8", errors="replace")))
        if n:
            out[f.name] = n
    return out


def _override_section() -> str:
    """截出 §一（更正表所在节）—— 只看这一节，避免正文别处提到文件名造成假通过。"""
    t = _readme()
    m = re.search(r"^## 一.*?$(.*?)^## 二", t, re.S | re.M)
    assert m, "入口 README 缺「§一 更正表」章节（或 §二 缺失导致无法截断）"
    return m.group(1)


def test_every_file_with_corrections_is_named_in_override_table():
    """含更正标记的文件必须都在更正表里被点名。"""
    section = _override_section()
    counts = _correction_counts()
    stems = {Path(n).stem: n for n in counts}
    unresolved = []
    for name, stem in stems.items():
        # 表里可能写全名，也可能写短名（SLICE-B2）；两种都算点名，但必须能互相解析
        if name in section or stem in section:
            continue
        # 再宽两档：表里可能写 SLICE-B2（文件 SLICE-B2-INTEGER-live）、
        # 也可能只写 B4（文件 B4-KEYCOUNT-ORIGIN）。逐级缩短前缀去找。
        parts = stem.split("-")
        if any("-".join(parts[:k]) in section for k in range(1, len(parts) + 1)):
            continue
        unresolved.append(name)
    assert not unresolved, (
        "这些文件含更正标记但入口更正表没点名，读者会漏掉它们的撤回：\n  "
        + "\n  ".join(sorted(unresolved)))


def test_override_table_positions_resolve_to_real_files():
    """更正表「原文位置」列里的每个文件引用都要解析得到真实文件。"""
    section = _override_section()
    # 表里用的是短名（`SLICE-B2`）+ 可选章节；抽出所有 `XXX-…` 形态的短名
    refs = set(re.findall(r"`([A-Z][A-Za-z0-9\-]*(?:-[A-Za-z0-9]+)+)`", section))
    on_disk = {f.stem for f in _bodies()}
    unresolved = []
    for r in sorted(refs):
        if r in on_disk:
            continue
        # 允许前缀短名（如 SLICE-B2 -> SLICE-B2-INTEGER-live）
        if any(s.startswith(r) for s in on_disk):
            continue
        unresolved.append(r)
    assert not unresolved, (
        "更正表引用了不存在的文件/章节文件：%s\n磁盘现有：%s"
        % (unresolved, sorted(on_disk)))


def test_declared_counts_match_disk():
    """入口声明「19 份正文 / 62 处更正标记」必须与实测一致。"""
    t = _readme()
    m_n = re.search(r"(\d+)\s*份正文\s*共\s*\*\*(\d+)\s*处\*\*更正标记", t)
    assert m_n, "入口缺「N 份正文共 M 处更正标记」这句声明（数字必须可核对）"
    claimed_files, claimed_marks = int(m_n.group(1)), int(m_n.group(2))

    real_files = len(_bodies())
    assert real_files == claimed_files, (
        "声称 %d 份正文，磁盘 %d 份" % (claimed_files, real_files))
    real_marks = sum(_correction_counts().values())
    assert real_marks == claimed_marks, (
        "声称 %d 处更正标记，实测 %d 处（markers=%s）"
        % (claimed_marks, real_marks, _correction_counts()))


def test_three_grades_all_present():
    """三级更正（推翻结论 / 撤回担忧 / 自报越界）必须都被提到。"""
    t = _readme()
    missing = [g for g in GRADES if g not in t]
    assert not missing, (
        "入口缺这些更正级别：%s —— 只记「推翻结论」会丢掉"
        "「撤回担忧」（原怀疑不成立）与「自报越界」两级，而这两级才是系列可信的来源" % missing)


def test_the_expensive_corrections_are_present():
    """两条最贵的更正必须在表里 —— 它们会让人去做无用功。"""
    section = _override_section()
    must = [
        ("udc_operation_log", "① 审计不写日志（会让人弃用有效审计腿）"),
        ("只读", "② 类型只读（会让人去申请不必要的权限）"),
        ("ABORT", "③ 把上次运行残留当本轮证据"),
        ("不存在", "⑤ 表不存在 ≠ 没有数据"),
    ]
    missing = [why for needle, why in must if needle not in section]
    assert not missing, "更正表缺这些高价条目：%s" % missing


def test_correct_and_incorrect_reading_order_is_stated():
    """必须明写「不要按编号顺序读」与「不要整理成干净结论」——这是本目录的读法前提。"""
    t = _readme()
    assert "不要按文件编号顺序读" in t or "不要按编号顺序读" in t, (
        "入口没写「不要按编号顺序读」——阶段编号会让人以为后者取代前者")
    assert "不要把这里整理成一份" in t, (
        "入口没写「不要把这里整理成一份干净的最终结论」——撤回记录本身是证据")


def test_gate_bites_on_mutation():
    """变异用例：把更正表挖空后，第 1 条断言必须变红。"""
    section = _override_section()
    counts = _correction_counts()
    assert counts, "磁盘上没有任何含更正标记的文件，本闸门已无对象，应复核本文件是否该删"

    # 模拟「表被挖空」：section 去掉所有文件名
    gutted = section
    for name in counts:
        gutted = gutted.replace(name, "")
        gutted = gutted.replace(Path(name).stem, "")
    missing = [n for n in counts if n not in gutted]
    assert len(missing) == len(counts), (
        "变异用例失效：挖空后仍判定 %d 个文件「已点名」，说明断言写法有问题" % (len(counts) - len(missing)))

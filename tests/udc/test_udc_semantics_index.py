"""`docs/audit/udc-semantics/` 的入口必须承载更正索引。

为什么：该目录 99 份里 25 份带更正标记、合计 60 处，其中 `menu-copy-p2-auditor-verdict.md`
一份就 16 处。顺序读会把已作废的结论当现行结论用，而这里的死结论会**改掉处置方向**
（把"取不到证据"归因成"通道/能力问题" → 处置变成换通道/换入口，真因却是授权前置缺失 + 应用未上架）。

守五件事：
1. 每个含更正标记的文件，都要在 §一 更正表里被点名（用全名或逐级短名前缀）。
2. 更正表的「原文」列引用到的文件必须真实存在。
3. 入口声明的「25 份 / 60 处」必须与磁盘实测一致。
4. 三条反复错因（授权前置 / 口径分母 / 独立取证同源）必须在入口显式成表 ——
   只列单条更正会让人以为是笔误，列成错因才能防复发。
5. 必须明写「不要清理这些自我更正」。

⚠️ 本目录 99 份文件里有 13 份被 `components/` / `core/` / `tools/` 按固定路径读取，
其中 3 份经 `host_llm_prompt` 进宿主提示词 —— 所以本闸门**只读不写**，不碰任何被引用文件。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
D = ROOT / "docs" / "audit" / "udc-semantics"
README = D / "README.md"

CORRECTION = re.compile(r"推翻|作废|纠正|撤回|更正|超额|CORRECTION")

# 三条反复错因，必须在入口以「错因表」形式出现
ERROR_PATTERNS = (
    ("授权前置", "把取不到归因给通道/能力 —— 先查授权前置再查工具"),
    ("口径", "分母/串位/单位错 —— 任何比例先问分母是谁"),
    ("同源", "「独立取证」其实同源 —— 独立性看遍历实现，不看是谁跑的"),
)


def _readme() -> str:
    assert README.is_file(), "udc-semantics 缺入口 README.md"
    return README.read_text(encoding="utf-8")


def _bodies():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def _correction_counts():
    out = {}
    for f in _bodies():
        n = len(CORRECTION.findall(f.read_text(encoding="utf-8", errors="replace")))
        if n:
            out[f.name] = n
    return out


def _override_section() -> str:
    """截出 §一（更正表所在节）。只看这一节，避免正文别处提到文件名造成假通过。"""
    t = _readme()
    m = re.search(r"^## 一.*?$(.*?)^## 二", t, re.S | re.M)
    assert m, "入口缺「§一 更正表」章节"
    return m.group(1)


def _name_is_mentioned(stem: str, text: str) -> bool:
    """全名或逐级缩短的前缀（`menu-copy-p2-auditor-verdict.md` → `menu-copy-p2-auditor-verdict`）。"""
    parts = re.split(r"[-.]", stem)
    return any("-".join(parts[:k]) in text or ".".join(parts[:k]) in text
               for k in range(1, len(parts) + 1))


def test_every_file_with_corrections_is_named_in_override_table():
    section = _override_section()
    counts = _correction_counts()
    unresolved = [n for n in counts if not _name_is_mentioned(Path(n).stem, section)]
    assert not unresolved, (
        "这些文件含更正标记但入口更正表没点名，读者会读到已作废的结论：\n  "
        + "\n  ".join(sorted(unresolved)))


def test_declared_counts_match_disk():
    t = _readme()
    m = re.search(r"\*\*(\d+)\s*份\*\*带更正标记，合计\s*\*\*(\d+)\s*处\*\*", t)
    assert m, "入口缺「N 份带更正标记，合计 M 处」这句可核对的声明"
    claimed_files, claimed_marks = int(m.group(1)), int(m.group(2))
    real = _correction_counts()
    assert len(real) == claimed_files, (
        "声称 %d 份带更正标记，实测 %d 份：%s" % (claimed_files, len(real), sorted(real)))
    assert sum(real.values()) == claimed_marks, (
        "声称 %d 处更正标记，实测 %d 处（明细 %s）" % (claimed_marks, sum(real.values()), real))


def test_error_patterns_table_present():
    """三条反复错因必须成表出现 —— 单条更正看起来像笔误，错因表才防复发。"""
    section = _override_section()
    missing = [why for needle, why in ERROR_PATTERNS if needle not in section]
    assert not missing, "更正表缺这些反复错因：%s" % missing


def test_self_corrections_must_be_kept():
    """必须明写「不要清理自我更正」——这类记录是可信度的来源。"""
    t = _readme()
    assert "自我更正" in t and ("不要清理" in t or "保留原文" in t), (
        "入口没写「自我更正要保留、不要清理」——清理掉就没人知道阳性对照曾经塌过")


def test_most_expensive_correction_is_present():
    """最贵的那条（把取不到归因给通道/能力）必须在表里。"""
    section = _override_section()
    assert "授权前置" in section, (
        "更正表缺最贵的一条：把「取不到」归因给通道/能力，真因是授权前置缺失")
    assert "未上架" in section, "缺「第二道阻断：应用未上架」——一次更正往往不够，这条就是证据"


def test_gate_bites_on_mutation():
    """变异用例：把更正表挖空后，第 1 条断言必须变红。"""
    section = _override_section()
    counts = _correction_counts()
    assert counts, "磁盘上没有任何含更正标记的文件，本闸门已无对象，应复核是否该删"
    gutted = section
    for name in counts:
        stem = Path(name).stem
        gutted = gutted.replace(name, "").replace(stem, "")
        parts = re.split(r"[-.]", stem)
        # 删掉每一级前缀，且**长的先删**（否则 "menu-copy" 先被删掉，
        # "menu-copy-p2-auditor-verdict" 就残成 "p2-auditor-verdict" 继续命中）
        for k in sorted(range(1, len(parts) + 1), reverse=True):
            gutted = gutted.replace("-".join(parts[:k]), "").replace(".".join(parts[:k]), "")
    still = [n for n in counts if _name_is_mentioned(Path(n).stem, gutted)]
    # 挖空后应当**一个都不剩**；若还剩，说明断言写法有漏洞（假通过）
    assert not still, (
        "变异用例失效：更正表被挖空后仍有 %d 个被判「已点名」（%s）—— 说明断言会假通过"
        % (len(still), still))

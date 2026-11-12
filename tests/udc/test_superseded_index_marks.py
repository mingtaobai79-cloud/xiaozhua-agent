"""降级（superseded）必须是双向的，而且 INDEX 必须跟着降级。

## 为什么需要这条闸门

P3 的做法是三段：「内容并入主文档 → 原文件头部加一行『已并入 X』 → 在对应 INDEX 标注主文档」。

第 71 轮实测这三段**都做了**，5 对降级全部双向：
    registry-entries-code.md  ↔ registry-entries.md
    FRONTEND-EXTRACTION-STATUS.md ↔ -v2.md
    S7-WRITE-CHAIN-LIVE.md    ↔ -v2.md
    rules-microflow.md        ↔ rule-domain.md
    FRONTEND-OP-TO-ENDPOINT-ALIGNMENT.md ↔ GRAPHQL-OP-NAMING-RULE.md

★ 但 INDEX 那一段漏了：`core/facts/INDEX.md` L54 把已并入的 `rules-microflow.md`
  按 **「✅ LIVE PASS(10-23)」** 登记，描述完整、没有任何降级标记。
  读者从 INDEX 出发，会以为那是一份独立的现行证据 —— 而它其实是历史副本。

⇒ 判据：**降级有三个落点，最容易被漏的是"入口"那一个。**
   文件头写了、主文档反向指针写了，读者从正文走是对的；
   但从 INDEX 进来的人看到的是一份"现行 LIVE 证据"。
   **入口的错误比正文的错误更贵，因为入口是所有人的第一站。**

⇒ 所以这条闸门守两件事：
   ① 文件头标了 superseded 的文件，INDEX 那一行也必须标（第 71 轮修的就是这个）
   ② 降级必须双向：旧文件指向主文档，主文档正文必须提到旧文件名
"""

import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "core" / "facts"
INDEX = FACTS / "INDEX.md"
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

SUP = re.compile(r"(已并入|保留作历史|superseded|已被.{0,20}取代|已作废|不再作为|历史记录)", re.I)

# 第 71 轮实测的降级对：(旧文件, 主文档)，路径相对仓库根
PAIRS = [
    ("docs/operation-contracts/udc/entity/registry-entries-code.md",
     "docs/operation-contracts/udc/entity/registry-entries.md"),
    ("docs/audit/udc-semantics/FRONTEND-EXTRACTION-STATUS.md",
     "docs/audit/udc-semantics/FRONTEND-EXTRACTION-STATUS-v2.md"),
    ("docs/audit/udc-semantics/S7-WRITE-CHAIN-LIVE.md",
     "docs/audit/udc-semantics/S7-WRITE-CHAIN-LIVE-v2.md"),
    ("core/facts/udc/entity/rules-microflow.md",
     "core/facts/udc/entity/rule-domain.md"),
    ("docs/audit/udc-semantics/FRONTEND-OP-TO-ENDPOINT-ALIGNMENT.md",
     "docs/audit/udc-semantics/GRAPHQL-OP-NAMING-RULE.md"),
]


def _head(p, n=15):
    return "\n".join(p.read_text(encoding="utf-8", errors="replace").split("\n")[:n])


def test_superseded_is_bidirectional():
    """旧文件头部指向主文档，主文档正文必须提到旧文件名。"""
    bad = []
    for old, new in PAIRS:
        po, pn = ROOT / old, ROOT / new
        assert po.is_file(), "旧文件不存在：%s" % old
        assert pn.is_file(), "主文档不存在：%s" % new
        assert SUP.search(_head(po)), "%s 头部没有降级标记" % old
        assert pn.name in _head(po), (
            "%s 头部标了降级，但没写并入哪一份 —— 读者无处可去" % old)
        assert po.name in pn.read_text(encoding="utf-8"), (
            "%s 没提到 %s —— 从主文档进来的人不知道有历史副本，"
            "下次整理时可能把它当孤儿删掉" % (new, po.name))
    assert not bad, "\n".join(bad)


def test_index_marks_superseded_rows():
    """INDEX 里登记的文件若已降级，那一行也必须标降级。"""
    t = INDEX.read_text(encoding="utf-8")
    bad = []
    for i, line in enumerate(t.split("\n"), 1):
        if not line.strip().startswith("|"):
            continue
        m = re.search(r"`?([\w/\-\.]+\.md)`?", line)
        if not m:
            continue
        rel = m.group(1)
        p = FACTS / rel
        if not p.is_file():
            cand = list(FACTS.rglob(Path(rel).name))
            if len(cand) != 1:
                continue
            p = cand[0]
        if SUP.search(_head(p, 12)) and not SUP.search(line):
            bad.append("INDEX L%d 把已降级的 %s 当现行证据登记" % (i, rel))
    assert not bad, (
        "\n".join(bad)
        + "\n\n修法：那一行的状态列改成「⚠ 历史记录」，描述里写明并入哪一份。"
          "**入口的错误比正文的错误更贵** —— 正文写对了，从 INDEX 进来的人照样看错。")


def test_named_row_is_downgraded():
    """点名守 L54 那一条 —— 第 71 轮修的就是它，不许回退。"""
    t = INDEX.read_text(encoding="utf-8")
    for line in t.split("\n"):
        if "entity/rules-microflow.md" in line:
            assert SUP.search(line), (
                "INDEX 里 entity/rules-microflow.md 又变回「现行证据」了 —— "
                "它已并入 rule-domain.md §4/§5，是历史副本")
            assert "rule-domain.md" in line, (
                "该行没指向 rule-domain.md，读者不知道该去哪查规则域契约")
            return
    raise AssertionError("INDEX 里找不到 entity/rules-microflow.md 这一行")


def test_downgrades_are_not_deleted():
    """反退化：不许靠删掉降级标记 / 删掉旧文件来变绿。

    这 5 对是 P3 的产出。物理删除旧文件需要用户授权（待裁决），
    在授权之前它们必须都在盘上、都带标记。
    """
    missing = []
    for old, new in PAIRS:
        po = ROOT / old
        if not po.is_file():
            missing.append("旧文件不见了：%s（删除需要用户授权）" % old)
        elif not SUP.search(_head(po)):
            missing.append("旧文件的降级标记被删了：%s" % old)
    assert not missing, "\n".join(missing)
    assert len(PAIRS) >= 5, "降级对少于 5 组 —— 是不是把登记表删了？"

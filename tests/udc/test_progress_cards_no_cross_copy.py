"""进度卡片不许复制另一个进度文件的易变数字。

## 为什么需要这条闸门

`docs/plans/seeyon-distribution-progress.md`（分发线入口）里有一段
「**文档整理第 1–5 轮**」，而文档整理早已转到独立循环
（`docs/plans/doc-consolidation-progress.md`）。

第 65 轮复核时，这段落后 **59 轮**；同一张卡片的「下一步」第 4 条还列着
「P5 剩余、P6 临时件登记」—— **这两件事在第 5 / 6 轮就已完成**。

⇒ 失败模式很具体：**一个文件复制另一个文件的易变数字，必然过期，而且没人会回来改它。**
   因为改它的人正在改主文件，根本不知道副卡片里也有一份。

⇒ 判据：**跨文件的进度只留指针，不复制数字。**
   「第 1–5 轮」作为历史事实可以保留，但必须同时说明「此后转入独立循环、以主文件为准」，
   并且**分发线的「下一步」里不许再出现文档整理的任务**。

## 这条闸门不做什么

它**不**检查分发线的技术结论（那些要靠真实构建/安装验证，本仓库目前 BLOCKED）。
它只管一件事：**两张卡片的职责边界有没有被糊掉。**
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "docs" / "plans" / "seeyon-distribution-progress.md"
CONS = ROOT / "docs" / "plans" / "doc-consolidation-progress.md"
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()


def _max_round():
    t = CONS.read_text(encoding="utf-8")
    rs = [int(m.group(1)) for m in re.finditer(r"^\| (\d+) \|", t, re.M)]
    assert rs, "doc-consolidation-progress.md 的轮次表解析出 0 行"
    return max(rs)


def test_distribution_card_points_to_consolidation_card():
    """分发卡片必须给出文档整理的权威指针。"""
    t = DIST.read_text(encoding="utf-8")
    assert "doc-consolidation-progress.md" in t, (
        "分发卡片没指向 `docs/plans/doc-consolidation-progress.md` —— "
        "读者会以为文档整理就停在这张卡片写的那几轮")


def test_round_range_is_marked_as_history():
    """若出现「第 X–Y 轮」，必须写明那是历史、并说明此后以主文件为准。

    否则读者会把它当**当前进度**——第 65 轮时它落后 59 轮。
    """
    t = DIST.read_text(encoding="utf-8")
    for m in re.finditer(r"第\s*(\d+)\s*[–\-~]\s*(\d+)\s*轮", t):
        lo, hi = int(m.group(1)), int(m.group(2))
        # 上下文窗口：前后各 500 字
        s = max(0, m.start() - 500)
        ctx = t[s:m.end() + 700]
        assert ("转入独立循环" in ctx) or ("已落后" in ctx) or ("以主文件为准" in ctx), (
            "「第 %d–%d 轮」被当成当前进度在写，但没有标注它是历史：\n  %s"
            % (lo, hi, ctx[:200].replace("\n", " ")))


def test_next_steps_section_excludes_doc_work():
    """分发线的「下一步」不许再列文档整理任务（职责分离）。

    P5 / P6 早已完成，但它们曾长期占着分发线的「下一步」第 4 条 ——
    于是读分发线的人会以为文档整理还欠两件事。
    """
    t = DIST.read_text(encoding="utf-8")
    i = t.find("### 下一步")
    assert i >= 0, "分发卡片缺「### 下一步」小节"
    j = t.find("\n### ", i + 5)
    sec = t[i:] if j < 0 else t[i:j]
    # 允许以删除线保留（~~...~~）—— 那是「已完成」的记录，不是待办
    live = "\n".join(
        ln for ln in sec.split("\n")
        if not ln.strip().startswith(">") and "~~" not in ln
    )
    assert "文档整理" not in live, (
        "分发线的「下一步」里还列着文档整理任务 —— 那是另一条线的事，\n"
        "读者会以为文档整理没做完。改成指针或划掉。\n当前「下一步」：\n" + live)


def test_consolidation_card_is_the_live_one():
    """反证：主文件的轮次必须远超分发卡片里写的终值。

    这条防的是「反过来把主文件也钉死在早期轮次」—— 那样两条线一起停住，
    上面三条会全绿而系统其实已经不转了。
    """
    assert _max_round() >= 30, (
        "doc-consolidation-progress.md 最大轮次只有 %d —— 文档整理循环停了吗？"
        % _max_round())

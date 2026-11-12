"""待裁决清单的每一条都必须带「实测 + 时点」。

## 为什么需要这条闸门

`docs/plans/doc-consolidation-progress.md` §三「待裁决」是**用户做决定的依据**。
但它此前的数字**从没被复核过**：

- 第 2 条「19 位平台对象 ID（结论区 2,359 处）」写于第 10 轮，
  一直挂到第 64 轮才第一次重算 —— 实测 237 文件 / 2,098 处（且口径与原文不完全一致）。
- 第 1 条「`_attic_pending/` 156 MB」实测 158.5 MB / 1,843 文件。

**挂得越久的待裁决越危险**：读者会按一个过期规模去权衡代价。
一条待裁决写着「2,359 处会大幅降低可复现性」，和写着「1,350 处」，
用户的心理门槛是不同的 —— 而这两个数当时都出现在同一个仓库里。

⇒ 判据：**待裁决项不是"待办"，是"待决策"，决策依据必须是可复核的实测值 + 时点。**
   没有实测的待裁决，等于把"我印象里大概是这么多"当成事实交给用户。

## 这条闸门不做什么

它**不**判断实测值对不对（那要靠复跑，写在表下方的「复跑方法」里）。
它只保证：**每一条都声称自己有实测，并写明是什么时候测的** ——
这样过期能被看见，而不是悄悄烂在里面。
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "docs" / "plans" / "doc-consolidation-progress.md"
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()


def _section():
    t = P.read_text(encoding="utf-8")
    i = t.find("## 三、待裁决")
    assert i >= 0, "找不到 §三「待裁决」小节 —— 它被改名或删了？"
    j = t.find("\n## ", i + 10)
    return t[i:] if j < 0 else t[i:j]


def _rows(sec):
    """解析 `| N | 事项 | 现状 | 理由 |` 行，跳过划掉的（~~）与表头/分隔行。"""
    out = []
    for line in sec.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if not re.fullmatch(r"\d+|~~\d+~~", cells[0]):
            continue
        out.append((cells[0], cells[1], cells[2]))
    return out


def test_every_pending_item_carries_a_measurement():
    """每条待裁决的「现状」列必须含「实测」+ 日期。"""
    rows = _rows(_section())
    assert rows, "§三 解析出 0 条待裁决 —— 表格结构变了？"
    bad = []
    for num, item, status in rows:
        if num.startswith("~~"):
            continue          # 已关闭的条目保留作历史，不要求实测
        if "实测" not in status:
            bad.append("%s：缺「实测」（%s）" % (num, item[:36]))
        elif not re.search(r"\d{4}-\d{2}-\d{2}", status):
            bad.append("%s：有「实测」但没有日期（%s）" % (num, item[:36]))
    assert not bad, (
        "待裁决项缺可复核的事实基础（用户要按它权衡代价）：\n  "
        + "\n  ".join(bad)
        + "\n\n补法：跑一遍表下方的「复跑方法」，把实测值 + 日期写进「现状」列。")


def test_pending_list_is_not_emptied_to_pass():
    """反退化：不许靠删待裁决项让闸门变绿。

    这四条都是**真的需要用户拍板**的事（不可逆删除 / 脱敏范围 / 合并方向 / 闸门口径），
    不是我们能在文档整理里顺手解决的。删掉它们等于把决策悄悄吞了。
    """
    rows = [r for r in _rows(_section()) if not r[0].startswith("~~")]
    assert len(rows) >= 4, (
        "未关闭的待裁决只剩 %d 条（应 ≥4）—— 有人把需要用户拍板的事删了？" % len(rows))


def test_reproduce_recipe_exists():
    """表下方必须有「复跑方法」——没有复跑方法的实测值，下一轮照样会烂。"""
    sec = _section()
    assert "复跑方法" in sec, (
        "§三 缺「复跑方法」段 —— 没有复跑命令，下一轮的人只能凭记忆改数字")


def test_no_stale_hardcoded_2359():
    """反退化：那个挂了 54 轮的「2,359 处」不许原样回来当现值。

    只查**表格的「现状」列** —— 说明段落里提到旧值是在讲历史，本来就该允许。
    这条一开始写成了「扫整节」，闸门立刻抓住我自己写的那句
    「第 2 条的「2,359 处」写于第 10 轮」——判据打偏了会逼人删掉历史说明。
    """
    for num, item, status in _rows(_section()):
        if num.startswith("~~") or "2,359" not in status:
            continue
        assert "原记" in status or "未复现" in status, (
            "2,359 又变回现值了？它必须标成「原记」（第 10 轮口径）并注明未复现：\n  "
            + status[:160])

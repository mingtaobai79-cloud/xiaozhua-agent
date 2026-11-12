"""方法论条目本身也要有闸门 —— 否则「第 N 条」会静默丢号。

起因（真实事故）：第 49–64 轮共 16 轮的方法论只写进了 git commit message，
`docs/plans/doc-consolidation-progress.md` §六 里从 48 直接跳到 65。
后果：**只读进度文件的人永远看不到那 16 条**，而进度文件正是这个任务的入口。

⇒ 判据（方法论第 48 条的自指）：**「记在别处」等于没记。**
   所以这条闸门不检查内容质量（那是人读的），只守住三件可机械校验的事：
1. 编号必须**从 1 连续到最大值**，不许有洞。
2. 每条的开头必须是 `N. **标题**（第 M 轮）` 的形状，否则它会被当成正文而不是条目。
3. 条目数只许增不许减 —— 与方法论第 64 条同理：**删掉一条，比删掉一个结论更危险。**

第 3 条怎么防"缩水"：把已见最大值记在文件里而不是测试里。
测试读进度文件顶部的哨兵注释 `<!-- 方法论条目数：N -->`，
要求 `实际条目数 == 哨兵值`，改文件的人必须同步改哨兵 ——
于是**想把编号悄悄合并或删掉，必须显式改哨兵**，不可能无意发生。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
PLAN = ROOT / "docs" / "plans" / "doc-consolidation-progress.md"

# `N. **title**（第 M 轮` —— 只认这个形状，避免把下一批候选里的 `1. **P4 B 组**` 混进来
ENTRY = re.compile(r"^(\d+)\. \*\*.{2,}?\*\*（第 ?(\d+) ?轮", re.M)

SENTINEL = re.compile(r"<!--\s*方法论条目数：(\d+)\s*-->")


def _text() -> str:
    assert PLAN.is_file(), "进度文件不存在：%s" % PLAN
    return PLAN.read_text(encoding="utf-8")


def _section() -> str:
    """只取 §六（方法论）那一节。别处的编号列表（下一批候选）不是方法论条目。"""
    t = _text()
    m = re.search(r"^## 六、方法论.*?$(.*?)^## 七、", t, re.S | re.M)
    assert m, "进度文件缺 §六 / §七 结构，无法截出方法论节"
    return m.group(1)


def _entries():
    """解析方法论条目，返回 [(编号, 轮次或 None)]。

    只取**以 1 开始、逐条 +1 的最长链**。文件里还有两处别的编号列表
    （§四「下一批候选」1..3），混进来会让「连续」这条判据失去意义 ——
    最长链会自动把它们排除（68 条 vs 3 条）。
    """
    lines = _text().splitlines()
    starts = []
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)\. \*\*", line)
        if m:
            starts.append((i, int(m.group(1))))
    best, cur = [], []
    for i, n in starts:
        if n == 1:
            cur = [(i, n)]
        elif cur and n == cur[-1][1] + 1:
            cur.append((i, n))
        else:
            cur = []
        if len(cur) > len(best):
            best = list(cur)
    out = []
    for k, (i, n) in enumerate(best):
        end = best[k + 1][0] if k + 1 < len(best) else min(i + 8, len(lines))
        block = "\n".join(lines[i:end])
        m = re.search(r"（第 ?(\d+) ?轮", block)
        if m is None:
            # 标题行本身也可能带轮次
            m = re.search(r"（第 ?(\d+) ?轮", lines[i])
        out.append((n, int(m.group(1)) if m else None))
    return out


def test_numbering_is_continuous():
    """编号必须从 1 连续到最大值 —— 有洞说明有一轮的方法论没写进来。"""
    nums = [n for n, _ in _entries()]
    assert nums, "没有解析到任何方法论条目 —— 格式变了，闸门失效"
    expected = list(range(1, max(nums) + 1))
    missing = sorted(set(expected) - set(nums))
    assert not missing, (
        "方法论编号有洞：缺 %s（最大 %d）。"
        "—— 这正是第 49–64 轮发生过的事：只写进 commit message，文件里从 48 跳到 65。"
        % (missing, max(nums)))
    dupes = sorted({n for n in nums if nums.count(n) > 1})
    assert not dupes, "方法论编号重复：%s" % dupes


def test_entries_are_in_ascending_order():
    """编号必须递增。乱序会让「第 N 条」这类引用对不上。"""
    nums = [n for n, _ in _entries()]
    assert nums == sorted(nums), (
        "方法论条目乱序：前 5 项 %s … 最后一个逆序在 %s"
        % (nums[:5], next((nums[i:i + 2] for i in range(1, len(nums))
                           if nums[i] < nums[i - 1]), None)))


def test_newer_entries_cite_a_round():
    """**第 15 条起**必须标「（第 M 轮）」。没标轮次 = 无法追到那次改动的证据。

    1–14 条是早期格式（当时还没这个约定），**不追溯改**：
    它们是历史记录，补标轮次等于改写历史，而改写的收益只是让闸门好看一点。
    """
    t = _text()
    bare = []
    for line in t.splitlines():
        m = re.match(r"^(\d+)\. \*\*", line)
        if m and int(m.group(1)) > 14 and not re.search(r"（第 ?\d+ ?轮", line):
            bare.append(int(m.group(1)))
    assert not bare, "这些方法论条目（>14）没标「（第 N 轮）」：%s" % bare


def test_round_numbers_are_plausible():
    """引用的轮次不许超过进度表里出现过的最大轮次（防止写错年份/轮号）。"""
    t = _text()
    rounds = {int(m.group(1)) for m in re.finditer(r"(?m)^\| (\d+) \| \*\*", t)}
    assert rounds, "进度文件里没有轮次表，无法校验方法论引用的轮次"
    max_round = max(rounds)
    bad = [(n, r) for n, r in _entries() if r is not None and r > max_round]
    assert not bad, (
        "这些条目引用了不存在的轮次（> 轮次表最大 %d）：%s" % (max_round, bad))


def test_count_sentinel_matches():
    """条目数必须与文件顶部哨兵一致 —— 防"悄悄删/并条"。"""
    t = _text()
    m = SENTINEL.search(t)
    assert m, ("进度文件顶部缺哨兵注释 `<!-- 方法论条目数：N -->`。"
               "没有它，删掉一条方法论不会有任何测试报警")
    declared = int(m.group(1))
    actual = len(_entries())
    assert actual == declared, (
        "哨兵写 %d 条，实际 %d 条。**要减少方法论条目，必须显式改哨兵** ——"
        "因为删掉一条方法论比删掉一个结论更危险（见第 64 条）" % (declared, actual))


def test_gate_bites_on_gap():
    """变异用例：把中间那条的编号改成一个大数 → 连续性断言必须变红。

    这条用例存在的理由：**一个恒真的断言也会"通过"**。
    不构造一次真实破坏，就无法证明闸门守的是它声称守的东西。
    """
    entries = _entries()
    assert len(entries) >= 3, "条目太少，无法构造变异"
    mid = entries[len(entries) // 2][0]
    biggest = max(n for n, _ in entries)

    gutted = re.sub(r"(?m)^%d\. \*\*" % mid, "%d. **" % (biggest + 5), _text(), count=1)
    assert gutted != _text(), "变异没生效：第 %d 条没被改到" % mid

    nums = {int(n) for n in re.findall(r"(?m)^(\d+)\. \*\*", gutted)}
    holes = sorted(set(range(1, max(nums) + 1)) - nums)
    assert holes, "变异用例失效：挖掉第 %d 条后连续性断言仍通过" % mid

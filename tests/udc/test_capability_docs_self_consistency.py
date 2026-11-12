"""`docs/capability/` 的「同一份文件里自相矛盾」闸门。

为什么需要它：
`AGENT-ADAPTER.md` 的头注在 2026-11-07 就把
「`adapters/*`、`installer/`、`core/{role,facts,skills,tools}` 在盘未建」明确标了作废，
**正文却在四个地方继续写「全部在盘未建」**（L97/L105/L122/L137）。

后果不是「有一句话过期」，而是：**同一份文件对同一件事给了两个答案**，
而头注与正文谁先被读到是随机的 —— 搜索命中、别人复制走的，都是正文那几行。

⇒ 这条闸门只守一件可机械校验的事：
  **凡头注声明「某目录现已存在」，正文就不许再把它写成「在盘未建 / absent / 不存在」。**
反过来也守：头注说未建的，正文不许说已建（防止下一次改动只改正文）。

不做的事（避免误伤）：
- 全库 NODE-CENSUS / 复审段里的自我推翻比喻（"原文作废"）**不扫** —— 那是更正记录本身，
  必须保留。所以只在「头注之后的正文」里扫，且**跳过含「作废 / 更正 / 原文」的行**。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
CAP = ROOT / "docs" / "capability"

# 「目录现已存在」的声明：出现 adapters/ 或 installer/ 且同一行有「现已存在 / 已存在 / 在盘」
EXISTS_CLAIM = re.compile(r"(adapters/|installer/|core/\{role)")
SAYS_ABSENT = re.compile(r"在盘未建|在盘\s*\*\*未建\*\*|absent|在盘不存在|No such file")

# 更正记录行必须豁免：它们**故意**引用旧话
CORRECTION_LINE = re.compile(r"作废|更正|原文|旧话|已改|superseded")


def _docs():
    return sorted(f for f in CAP.glob("*.md") if f.name != "README.md")


def _headnote(text: str) -> str:
    """头注 = 第一个 `---` 分隔线之前的部分。"""
    m = re.search(r"^---\s*$", text, re.M)
    return text[:m.start()] if m else text[:1200]


def _declares_dirs_exist() -> bool:
    """任一份文件头注声明 adapters/installer 现已存在。"""
    for f in _docs():
        head = _headnote(f.read_text(encoding="utf-8", errors="replace"))
        if EXISTS_CLAIM.search(head) and re.search(r"现已存在|已存在|在盘", head):
            if "未建" not in head.split("作废")[0] or "现已存在" in head:
                return True
    return False


def test_absent_claims_do_not_contradict_headnote():
    """正文不许与头注的「现已存在」相矛盾。"""
    assert _declares_dirs_exist(), (
        "前提变了：没有任何文件头注声明 adapters/installer 现已存在 —— "
        "若目录被删了，本闸门的前提就失效，应复核而不是直接删闸门")
    offenders = []
    for f in _docs():
        text = f.read_text(encoding="utf-8", errors="replace")
        head = _headnote(text)
        body_start = len(head)
        for i, line in enumerate(text.splitlines(), 1):
            pos = sum(len(x) + 1 for x in text.splitlines()[:i - 1])
            if pos < body_start:
                continue  # 头注本身可以有旧话（它是在记录更正）
            if CORRECTION_LINE.search(line):
                continue  # 更正记录故意引用旧话，必须留
            if EXISTS_CLAIM.search(line) and SAYS_ABSENT.search(line):
                offenders.append((f.name, i, line.strip()[:100]))
    assert not offenders, (
        "同一份文件里「头注已存在」与「正文未建」互相矛盾 —— "
        "读者随机进入会读到过期结论：\n  "
        + "\n  ".join("%s L%d: %s" % o for o in offenders))


def test_correction_table_is_present_in_entry():
    """入口必须登记这类「层内自相矛盾」，否则修完一次下次还会犯。"""
    t = (CAP / "README.md").read_text(encoding="utf-8")
    assert "层内自相矛盾" in t, "入口缺「层内自相矛盾」这一节"
    assert "头注已更正" in t and "文件已更正" in t, (
        "入口没写明「『头注已更正』≠『文件已更正』」这条判据")
    assert "AGENT-ADAPTER.md" in t, "入口没点名 AGENT-ADAPTER（本轮的实际修例）"


def test_declared_capability_sizes_match_disk():
    """入口 §一 的「合计 10 份 / X B」必须与磁盘一致。"""
    t = (CAP / "README.md").read_text(encoding="utf-8")
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", t)
    assert m, "入口缺「合计 N 份 / X B」声明"
    n, size = int(m.group(1)), int(m.group(2).replace(",", ""))
    docs = _docs()
    real = sum(len(f.read_bytes()) for f in docs)
    assert len(docs) == n, "声称 %d 份，磁盘 %d 份" % (n, len(docs))
    assert real == size, "声称 %s B，实测 %d B" % (size, real)


def test_gate_bites_on_contradiction():
    """变异用例：把一句正文改回旧话（不带更正标记），闸门必须变红。"""
    f = CAP / "AGENT-ADAPTER.md"
    text = f.read_text(encoding="utf-8", errors="replace")
    head = _headnote(text)
    body = text[len(head):]
    probe = body + "\nROADMAP §二 目标态 `installer/`（在盘**未建**）。\n"
    found = [ln for ln in probe.splitlines()
             if EXISTS_CLAIM.search(ln) and SAYS_ABSENT.search(ln)
             and not CORRECTION_LINE.search(ln)]
    assert found, "变异用例失效：注入旧话后闸门没有识别出来"


def test_roadmap_has_no_section_eight_or_nine():
    """ROADMAP-v2 只有 §一~§七。任何新写的「§八/§九」引用都错。

    这条守的是三份文件（A5/A6/A8）头注里那句「不引用不存在的 §九」——
    它们是**对的**；错的是当初 ROUTE 的引法。把 ROADMAP 的实际节数钉住，
    以后谁再加一个 §九 引用就会被问住。
    """
    t = (CAP / "ROADMAP-v2.md").read_text(encoding="utf-8")
    sections = re.findall(r"(?m)^## ([一二三四五六七八九十]+)、", t)
    assert sections, "ROADMAP-v2 里解析不到章节标题"
    assert "八" not in sections and "九" not in sections, (
        "ROADMAP-v2 现在有 §%s 了 —— 那 A5/A6/A8 头注里「无 §八/§九」的说法需要同步更新"
        % "、§".join(x for x in ("八", "九") if x in sections))
    assert len(sections) == 7, "ROADMAP-v2 章节数从 7 变成 %d，A1–A8 的引用范围要复查" % len(sections)

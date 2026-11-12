"""没有自己 README 的目录，上一层 README 必须真的逐份覆盖它。

## 为什么需要这条闸门

`core/facts/udc/README.md` §六有一条明文禁令：

    - **不要**给 `page/` `serial/` 批量生成 README：两域共 5 份，本文件已覆盖导航。
      哪个域开始被人反复查，再给它单独入口（`setting/` 就是这么来的）。

这条禁令是对的 —— 5 份文件为它们各建一个 README 是过度设计。
**但它承诺了「本文件已覆盖导航」，那就必须真的覆盖。**

第 72 轮实测：`page/` 的 3 份在 §五 表格里逐个列了路径，
`serial/` 的 2 份**只写了中文描述**（「流水号：应用草稿、流水号配置」），**没有任何路径**。
读者从「不要给 serial 生成 README」这句话出发，找不到 `serial/app-draft.md`。

⇒ 判据：**「已经覆盖了」是一句承诺，承诺必须可核。**
   写了「本文件已覆盖导航」却不给路径，比不写更糟 ——
   它让人停止寻找入口。

## 判定范围

两类：

**A. 明确放弃独立 README 的目录** —— 上一层必须逐份列出它们的文件。
   只登记这类，不给「所有目录」建闸门，因为：
   - `evidence/` 类目录本来就不该有 README
   - `skills/*/references/` 由 SKILL.md 引用，不需要
   - 份数 ≥10 的目录用 INDEX.md / 分组表，不逐份列

**B. 有 README 但它是正文不是索引的目录** —— README 里必须有索引表列全文件。
   第 72 轮发现 `udc/expression/`：README 20,404 B 讲引擎语义，
   另外 3 份 77 KB 一个都没列，读者只能平铺 grep。
   第 73 轮发现 `adapters/`：9 份、四个宿主的注册件，**顶层连 README 都没有**。

范围小、判据硬，比范围大、判据软有用。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

# (无 README 的目录, 负责覆盖它的上层 README)
COVERED_ELSEWHERE = [
    ("core/facts/udc/page",   "core/facts/udc/README.md"),
    ("core/facts/udc/serial", "core/facts/udc/README.md"),
]

# 有 README 但 README 兼作索引的目录（必须列全自己目录下的文件）
SELF_INDEXED = [
    "core/facts/udc/expression",
    "adapters",
]


def test_covers_every_file_in_those_dirs():
    """上层 README 必须提到每个文件名（只提中文描述不算）。"""
    bad = []
    for d_rel, readme_rel in COVERED_ELSEWHERE:
        d = ROOT / d_rel
        readme = ROOT / readme_rel
        assert d.is_dir(), "目录不存在：%s" % d_rel
        assert readme.is_file(), "上层 README 不存在：%s" % readme_rel
        t = readme.read_text(encoding="utf-8")
        files = sorted(f.name for f in d.glob("*.md") if f.name != "README.md")
        assert files, "%s 下没有 .md —— 这个登记项该删了" % d_rel
        for name in files:
            if name not in t:
                bad.append("%s 没提到 %s/%s" % (readme_rel, d_rel, name))
    assert not bad, (
        "\n".join(bad)
        + "\n\n上层 README 说了「本文件已覆盖导航」，那就必须给出路径。"
          "只写中文描述等于没覆盖 —— 读者拿不到可点开的东西。")


def test_these_dirs_still_have_no_readme():
    """反退化：不许用「偷偷补个 README」来让上一条变绿。

    禁令是「不要给 page/ serial/ 批量生成 README」。
    补了 README 就等于推翻这个决策 —— 那需要改禁令原文，不能悄悄做。
    """
    wrong = [d for d, _ in COVERED_ELSEWHERE if (ROOT / d / "README.md").is_file()]
    assert not wrong, (
        "这些目录本来约定不给 README，现在有了：%s\n"
        "如果是决策变了，请先改 core/facts/udc/README.md §六的禁令原文，"
        "再删掉本测试里的登记项 —— 不要两头不一致。" % wrong)


def test_the_prohibition_is_still_there():
    """禁令原文必须在 —— 它是这两条登记项的依据。"""
    t = (ROOT / "core/facts/udc/README.md").read_text(encoding="utf-8")
    assert "不要" in t and "生成 README" in t, (
        "§六那条「不要给 page/ serial/ 批量生成 README」的禁令被删了 —— "
        "那么本测试的两个登记项就失去依据，应该一起删")
    assert "已覆盖导航" in t, (
        "禁令里「本文件已覆盖导航」这句承诺被删了 —— "
        "删掉它等于放弃覆盖义务，但 page/ serial/ 仍然没有自己的入口")


def test_expression_index_lists_all_four():
    """`udc/expression/` 有 README，但它是事实格不是索引 —— §〇 索引表必须列全 4 份。"""
    d = ROOT / "core/facts/udc/expression"
    t = (d / "README.md").read_text(encoding="utf-8")
    for name in sorted(f.name for f in d.glob("*.md")):
        assert name in t, (
            "expression/README.md 的 §〇 索引表没列 %s —— "
            "这个目录 4 份 77 KB，没有索引读者只能平铺 grep" % name)
    assert "本目录 4 份" in t, "§〇 索引表的标题被删了"


def test_self_indexed_dirs_list_every_file():
    """SELF_INDEXED 里的目录：README 必须提到自己目录下每个 .md。"""
    bad = []
    for rel in SELF_INDEXED:
        d = ROOT / rel
        readme = d / "README.md"
        assert d.is_dir(), "目录不存在：%s" % rel
        assert readme.is_file(), "%s 没有 README —— 它是 SELF_INDEXED 登记项" % rel
        t = readme.read_text(encoding="utf-8")
        for f in sorted(d.rglob("*.md")):
            if f == readme:
                continue
            name = f.name
            if name not in t:
                bad.append("%s/README.md 没提到 %s" % (rel, f.relative_to(d).as_posix()))
    assert not bad, (
        "\n".join(bad)
        + "\n\n这些目录的 README 兼作索引。不列全 = 读者找不到，"
          "等于这个目录没有入口。")


def test_adapters_declares_its_own_total():
    """adapters/README.md 的「合计 9 份 / N B / M 行」必须等于实测。"""
    d = ROOT / "adapters"
    fs = [f for f in sorted(d.rglob("*.md")) if f.name != "README.md"]
    n = len(fs)
    b = sum(len(f.read_bytes()) for f in fs)
    lines = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in fs)
    t = (d / "README.md").read_text(encoding="utf-8")
    want = "**合计 %d 份 / %s B / %s 行。**" % (n, format(b, ","), format(lines, ","))
    assert want in t, (
        "adapters/README.md 的合计行与实测不符。\n  实测：%d 份 / %s B / %s 行\n"
        "  应写：%s" % (n, format(b, ","), format(lines, ","), want))


def test_three_manifests_are_not_merged():
    """反退化：三份 MCP-TOOL-MANIFEST 不许被合并成一份。

    它们看起来同构，实际是三个宿主各自的声明件 ——
    合并会丢掉「每个宿主自己那一层还没实现」的信息，
    而那正是分发前必须逐宿主确认的东西。
    """
    found = sorted(p.parent.name for p in ROOT.glob("adapters/*/MCP-TOOL-MANIFEST.md"))
    assert found == ["claude-code", "codex", "hermes"], (
        "三宿主各自的 MCP-TOOL-MANIFEST.md 少了一份：%s\n"
        "它们是按宿主分别声明的，不是同一份文件的副本。"
        "要合并请先改 adapters/README.md §一 的说明，不要只删文件。" % found)
    t = (ROOT / "adapters" / "README.md").read_text(encoding="utf-8")
    assert "不是同一份文件的副本" in t or "不要把这三份合并" in t, (
        "adapters/README.md 里「三份 MANIFEST 不是重复」的说明被删了 —— "
        "没有这句话，下一个整理的人一定会去合并它们")

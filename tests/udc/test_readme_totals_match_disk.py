"""全库每个 README 的「合计 N 份 / X B」都必须能被复算 —— 表驱动。

## 为什么需要这条闸门

第 69 轮做了两件事：

1. 普查全库表格的「行」+「字节」列：**129 行，全部正确**。
   —— 因为每个域都有自己的 `test_<域>_layout.py` 守着逐行。
2. 普查全库的「合计 N 份 / X B」：10 处现值，**当前全部正确**。
   但 grep 测试目录后发现：**只有 2 处被任何测试引用**（`79,892` / `1,393,550`），
   其余 **6 处没有任何闸门**。

⇒ 这就是问题所在：**逐行有闸门、合计没有**。
   逐行错了立刻红；合计错了要等下一轮普查才有人发现（第 68 轮就踩过：
   逐行全对、合计是第三种口径，错了 10 万字节没人知道）。

⇒ 判据：**「合计」是一个独立声明，必须有独立断言。**
   逐行闸门不会替你检查它，因为逐行确实是对的。

## 为什么用表驱动而不是每处写一个测试

口径在仓库里**确实有四种**，而且从表上看不出来：

    top_no_readme                  顶层 md，不含 README
    recursive_no_readme            递归 md，不含 README
    recursive_all_except_top_readme  递归全部，只排除顶层那一份 README
    (core/facts/udc/ 的 158 份是第四种：159 递归含 R 减去顶层 README)

把它们显式写进这张表，好处是：**改口径必须改测试** ——
而改测试的人会被迫重新确认这个数。藏在文档里的口径没人会重新确认。
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

# (README 路径, 声明的份数, 声明的字节, 口径)
# 口径说明见模块 docstring。数字取自 2026-11-07 第 69 轮实测。
TABLE = [
    ("docs/README.md",                              10,     50_302, "top_no_readme"),
    ("docs/capability/README.md",                   10,    104_121, "recursive_no_readme"),
    ("docs/audit/role/README.md",                    9,    236_279, "recursive_no_readme"),
    ("core/facts/udc/entity/README.md",              9,     84_266, "top_no_readme"),
    ("core/facts/udc/setting/README.md",            17,    179_489, "recursive_no_readme"),
    ("docs/operation-contracts/udc/setting/README.md", 11,  79_262, "recursive_no_readme"),
    ("core/facts/bpm/README.md",                     5,     79_892, "recursive_no_readme"),
    ("core/facts/udc/README.md",                   163,  1_430_820, "recursive_all_except_top_readme"),
]

TOTAL = re.compile(r"合计\s*\*{0,2}\s*(?:[\d,]+\s*个[^/]{0,12}/\s*)?(\d+)\s*份\s*/\s*([\d,]+)\s*B")


def _measure(readme, scope):
    d = readme.parent
    if scope == "top_no_readme":
        fs = [f for f in sorted(d.glob("*.md")) if f.name != "README.md"]
    elif scope == "recursive_no_readme":
        fs = [f for f in sorted(d.rglob("*.md")) if f.name != "README.md"]
    elif scope == "recursive_all_except_top_readme":
        fs = [f for f in sorted(d.rglob("*.md")) if f != readme]
    else:
        raise AssertionError("未知口径：%s" % scope)
    return len(fs), sum(len(f.read_bytes()) for f in fs)


def test_every_declared_total_matches_disk():
    """8 处合计，逐处按它自己的口径复算。"""
    bad = []
    for rel, n, b, scope in TABLE:
        p = ROOT / rel
        assert p.is_file(), "README 不存在：%s" % rel
        real_n, real_b = _measure(p, scope)
        if (real_n, real_b) != (n, b):
            bad.append("%s（%s）：登记 %d 份 / %s B，实测 %d 份 / %s B"
                       % (rel, scope, n, format(b, ","), real_n, format(real_b, ",")))
    assert not bad, (
        "合计声明与磁盘不符：\n  " + "\n  ".join(bad)
        + "\n\n改了这些目录里的正文就要同步这里的数。**注意口径**（见模块 docstring）——"
          "用错口径会得出另一个「也对」的数，然后去改一个本来正确的值。")


def test_readme_still_says_the_same_total():
    """README 正文里的合计行必须与上表一致（防"只改测试不改文档"或反之）。"""
    bad = []
    for rel, n, b, _ in TABLE:
        t = (ROOT / rel).read_text(encoding="utf-8")
        m = TOTAL.search(t)
        if not m:
            bad.append("%s：正文里找不到「合计 N 份 / X B」" % rel)
            continue
        if (int(m.group(1)), int(m.group(2).replace(",", ""))) != (n, b):
            bad.append("%s：正文合计是 %s 份 / %s B，表里登记 %d 份 / %s B"
                       % (rel, m.group(1), m.group(2), n, format(b, ",")))
    assert not bad, "文档与闸门表不同步：\n  " + "\n  ".join(bad)


def test_all_four_scopes_are_represented():
    """反退化：口径不许被统一成一种。

    仓库里确实有四种口径。如果有人把它们都改成 recursive_no_readme
    "为了整齐"，那 4 处数字会变，然后他会去改文档 —— 把一个对的数改错。
    """
    scopes = {s for _, _, _, s in TABLE}
    assert scopes == {"top_no_readme", "recursive_no_readme",
                      "recursive_all_except_top_readme"}, (
        "口径集合变了：%s —— 仓库里本来有四种口径，统一它们会改错数" % scopes)


def test_no_readme_lost_its_total():
    """反退化：不许靠删掉「合计」行让闸门变绿。"""
    missing = [rel for rel, _, _, _ in TABLE
               if not TOTAL.search((ROOT / rel).read_text(encoding="utf-8"))]
    assert not missing, "这些 README 的「合计」行被删了：%s" % missing

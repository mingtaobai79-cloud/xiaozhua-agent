"""`docs/operation-contracts/udc/setting/` 入口必须登记「成功码 + 空」的四义。

## 为什么这个目录需要一条闸门

设置域 11 份契约里，有 **4 份**各写过一次「调用成功、读回来是空的」，
但它们写的是**四种不同原因**，处置正好相反：

| 原因 | 该做什么 | 证据 |
|---|---|---|
| 真没写进去（REST 父级不处理子集合） | 改走 GraphQL | `attribute-set` 4 次尝试 + `scalability` 3 次 |
| 写进去了但读错字段（`columnList` 恒 null） | 换读法，别重写 | `excel-template` L32 |
| 本来就是空（`udc_scalability` 0 行） | 什么都不用做 | `scalability` §关键对照 |
| 上下文/授权不对（`content=[]`） | 先查上下文再判空 | `expression-component` L43 |

**只读一份文件的人，只会知道其中一种** —— 然后按那一种去处置另外三种。
`attribute-set` 那条最坑：它明确写「REST 父级不处理子集合」，读者容易推广成
「所有 REST 子集合都不行」，于是把 `excel-template` 那个**已经写成功**的 `columnList`
也去"修"，反而写坏。

所以本闸门守两件事：
1. 入口 README 必须有 §〇★ 四义对照表，且四种原因都在；
2. 四份文件必须反向指回 §〇★（否则读者永远看不到另外三种）。
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "setting"
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

# 四份各持一种成因的文件
BEARERS = {
    "attribute-set-contracts.md": "真没写进去",
    "scalability-contracts.md": "本来就是空",
    "excel-template-contracts.md": "读错字段",
    "expression-component-contracts.md": "上下文不对",
}


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/setting/README.md"
    return p.read_text(encoding="utf-8")


def test_readme_has_the_four_meaning_table():
    t = _readme()
    assert "## 〇★" in t, "README 缺 §〇★（四义对照）—— 这是本域最贵的一条判据"
    assert "四种原因" in t or "4 种" in t, "§〇★ 没说明有四种（会被人当成两种或一种）"
    for k in ("真没写进去", "换读法", "本来就没数据", "上下文不对"):
        assert k in t, "§〇★ 缺成因：%s" % k
    # 四份出处都要点名
    for name in BEARERS:
        assert name in t, "§〇★ 的对照表没点名 %s（读者找不到原始证据）" % name


def test_readme_declares_seven_failed_attempts():
    """① 的规模必须写出来：7 次尝试 7 次都拿到成功码 —— 这是"不能推广到其它 REST"的依据。"""
    t = _readme()
    assert "7 次" in t, "没写「7 次尝试」——读者会以为只是个别现象"
    assert "BOOT_0000" in t, "没给出成功码，读者无法识别自己遇到的是不是同一类"


def test_each_bearer_points_back_to_readme():
    """四份必须反向指回 §〇★。没有反向指针，读者只知道自己手上那一种。"""
    missing = []
    for name, why in BEARERS.items():
        t = (D / name).read_text(encoding="utf-8")
        if "§〇★" not in t:
            missing.append("%s（持有成因：%s）" % (name, why))
    assert not missing, (
        "这些文件没指回 README §〇★，读者会把自己遇到的那一种当成通则：\n  "
        + "\n  ".join(missing))


def test_scalability_says_its_own_zero_rows_are_normal():
    """最反直觉的一条：同一份文件里既有「真没写进去」，又有「0 行是正常的」。

    两者相距不到 30 行。不写清就会互相污染 —— 读者会把 `udc_scalability` 0 行
    也当成「REST 不处理子集合」的证据，然后去改一个没坏的东西。
    """
    t = (D / "scalability-contracts.md").read_text(encoding="utf-8")
    assert "同一份文件里就有一个反例" in t, (
        "scalability 必须自己点明：§已推翻的 REST 尝试 与 §关键对照 是相反结论")
    assert "正常空" in t, "没写「正常空」这个说法，0 行仍会被读成失败"


def test_excel_template_warns_against_rewriting():
    """`columnList` 恒 null 的正确处置是「换读法」，不是「重写」。

    这是四种里**唯一处置会让事情变坏**的一种：写侧本来成功，照着 null 重写会把对的写坏。
    """
    t = (D / "excel-template-contracts.md").read_text(encoding="utf-8")
    assert "这不是写失败" in t, "没明写「不是写失败」"
    assert "写坏" in t, "没警告「照着 null 去重写会把已经对的写坏」"


def test_no_generalisation_of_rest_rule():
    """反退化：「REST 父级不处理子集合」不许被写成通则。

    实测只有 `attribute-set` 与 `scalability` 两个父级端点有这个问题；
    `excel-template` 是 REST 且**写成功了**。把它写成通则会直接导致误改。
    """
    t = _readme()
    assert "不能推出" in t or "别把这一条当通则" in t, (
        "README 没写「父级写成功 ≠ 子集合写成功」只能在有证据的端点上用")
    # 四份里至少有一处明确的「别当通则」
    bearer_txt = "\n".join((D / n).read_text(encoding="utf-8") for n in BEARERS)
    assert "别把这一条当通则" in bearer_txt, "四份里没有一处提醒「别当通则」"


def test_table_sizes_match_disk():
    """规模表与磁盘一致（改了正文必然改字节，这条防漂移）。"""
    t = _readme()
    rows = re.findall(r"^\| `([\w.-]+\.md)` \|(.*?)\|\s*([\d,]+) \|\s*(\d+) \|\s*$", t, re.M)
    assert len(rows) == 11, "规模表解析出 %d 行（应有 11 份）" % len(rows)
    bad = []
    for name, _mid, size_s, line_s in rows:
        f = D / name
        if not f.is_file():
            bad.append("%s 不存在" % name)
            continue
        a = len(f.read_bytes())
        n = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        if a != int(size_s.replace(",", "")):
            bad.append("%s 字节 表写 %s 磁盘 %d" % (name, size_s, a))
        if n != int(line_s):
            bad.append("%s 行数 表写 %s 磁盘 %d" % (name, line_s, n))
    assert not bad, "规模表已腐坏：\n  " + "\n  ".join(bad)
    total = sum(len((D / n).read_bytes()) for n in BEARERS) + sum(
        len(f.read_bytes()) for f in D.glob("*.md")
        if f.name not in BEARERS and f.name != "README.md")
    m = re.search(r"合计 \*\*11 份 / ([\d,]+) B\*\*", t)
    assert m, "README 找不到「合计 11 份 / X B」"
    assert int(m.group(1).replace(",", "")) == total, (
        "合计写 %s，磁盘实算 %d" % (m.group(1), total))

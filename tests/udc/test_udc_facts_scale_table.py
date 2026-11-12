"""`core/facts/udc/README.md` 的规模表必须与磁盘一致，且口径必须写明。

## 为什么需要这条闸门

这张表是 `core/facts/udc/`（158 份 / 1.39 MB）唯一的规模总览。
第 67 轮实测：**10 行里 9 行对，只有 `docs/operation-contracts/udc/microflow/`
的字节错**（声明 271,168，实测 277,025，差 5,857 B）。

## 更重要的发现：这张表混用两种口径，而且看不出来

同一张表里，「份」有的按**顶层**算、有的按**递归**算：

    子域            顶层    递归    表里写的
    microflow/       62      62      62     ← 无子目录，看不出口径
    write-chain/     39      46      46     ← 递归
    setting/          3      16      16     ← 递归
    entity/          10      12      12     ← 递归
    application/      5       8       8     ← 递归
    expression/       4       4       4     ← 无子目录
    page/             3       3       3     ← 无子目录
    serial/           2       2       2     ← 无子目录

⇒ **只看 microflow / expression / page / serial 这四个，永远发现不了口径混用** ——
   它们没有子目录，两种算法同值。而恰好这四个里有三个排在表格最前面/最显眼的位置。

⇒ 判据：**规模表必须写明口径，闸门必须按写明的口径算。**
   不写口径的表，读者会默认「同一列同一标准」—— 而这里是两种标准。

口径：**递归含子目录，且含该子域自己的 `README.md`**。
（`microflow/` 62 份里含 `microflow/README.md`；`page/` `serial/` 没有 README，
所以它们表里「入口」列是 ❌，两件事一致。）
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "core" / "facts" / "udc" / "README.md"
assert (ROOT / "core").is_dir() and (ROOT / "tests").is_dir()

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([\d,]+)\s*\|")


def _rows():
    """抓所有 `| \\`路径\\` | 份 | 字节 |` 行，返回 [(路径, 份, 字节)]。"""
    out = []
    for line in P.read_text(encoding="utf-8").split("\n"):
        m = ROW.match(line.strip())
        if not m:
            continue
        out.append((m.group(1), int(m.group(2)), int(m.group(3).replace(",", ""))))
    return out


def _measure(rel):
    """双路径解析：先按仓库根，再按本文档同级目录（8 子域表用的是相对路径）。

    `microflow/` 这种写法在仓库根不存在，只有相对于 `core/facts/udc/` 才成立。
    """
    cands = [ROOT / rel]
    if not rel.startswith(("core/", "docs/")):
        cands.append(P.parent / rel)
    for d in cands:
        if d.is_dir():
            files = sorted(d.rglob("*.md"))
            return len(files), sum(len(f.read_bytes()) for f in files)
    raise AssertionError("表里写的路径不存在：%s" % rel)


def test_subdomain_rows_match_disk():
    """8 个子域行 + 3 处位置行，份与字节都要对（递归含子目录 + 含自身 README）。"""
    bad = []
    checked = 0
    for rel, n, b in _rows():
        if not rel.endswith("/"):
            continue
        try:
            real_n, real_b = _measure(rel)
        except AssertionError:
            continue          # 表里可能写的是别名/说明性路径，跳过
        checked += 1
        if (n, b) != (real_n, real_b):
            bad.append("%s：声明 %d 份 / %s B，实测 %d 份 / %s B"
                       % (rel, n, format(b, ","), real_n, format(real_b, ",")))
    assert checked >= 8, "只核到 %d 行路径，表结构变了？" % checked
    assert not bad, (
        "core/facts/udc/README.md 规模表与磁盘不符：\n  " + "\n  ".join(bad)
        + "\n\n注意口径：**递归含子目录 + 含该子域自己的 README.md**。")


def test_measurement_scope_is_declared():
    """反退化：口径说明必须在。

    第 67 轮之前这张表没写口径，而它实际混用顶层/递归两种算法。
    没有这句，下一个人用 `glob("*.md")` 复算 write-chain 会得到 39，
    然后「修正」表里那个对的 46。
    """
    t = P.read_text(encoding="utf-8")
    assert "递归含子目录" in t, (
        "缺「递归含子目录」这个口径短语 —— 只写「递归」不够："
        "表里「递归 46 份」这种例子本身就含「递归」二字，"
        "断言太松的话，删掉口径声明也测不出来（第 67 轮变异实测踩到）")
    assert "含该子域自己的 `README.md`" in t or "含自身 README" in t or "含该子域自己的" in t, (
        "缺「是否含自身 README」的口径说明 —— "
        "microflow/ 的 62 份里是含 README 的，不说清就没人能复算")
    assert "write-chain/" in t and "39" in t, (
        "缺「write-chain 顶层 39 / 递归 46」这个具体例子 —— "
        "它是最能说明口径混用的一行（差 7 份全在子目录里）")


def test_no_top_level_only_numbers():
    """反退化：不许把递归数悄悄换成顶层数（那会让表看起来"变小了"）。"""
    rows = {rel: (n, b) for rel, n, b in _rows()}
    for rel, top_only in [("core/facts/udc/write-chain/", 39),
                          ("core/facts/udc/setting/", 3),
                          ("core/facts/udc/entity/", 10),
                          ("core/facts/udc/application/", 5)]:
        if rel in rows:
            assert rows[rel][0] != top_only, (
                "%s 的份数变成了顶层值 %d —— 表的口径是递归，不是顶层" % (rel, top_only))


def test_operation_contracts_microflow_byte_count():
    """点名：这行的字节随契约正文变化 —— 第 67 轮修过 271,168，第 74 轮改 b6 命令路径后又变了一次。

    断言是动态的（`_measure` 对磁盘），不写死数字，所以正文一改它就红、改对就绿。
    """
    rows = {rel: (n, b) for rel, n, b in _rows()}
    key = "docs/operation-contracts/udc/microflow/"
    assert key in rows, "位置表里缺 %s 这一行" % key
    n, b = rows[key]
    real_n, real_b = _measure(key)
    assert (n, b) == (real_n, real_b), (
        "%s 声明 %d 份 / %s B，实测 %d 份 / %s B" % (key, n, format(b, ","), real_n, format(real_b, ",")))
    assert "live-evidence/" in P.read_text(encoding="utf-8"), (
        "这 25 份里有 11 份在 live-evidence/ 子目录 —— 不注明，读者会以为是 14 份顶层契约")

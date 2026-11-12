"""全库「域入口首行声明」必须与磁盘一致 —— 份 / 字节 / 行 三个分量都要核。

## 为什么单开一条闸门

仓库里有**四种**「N 份 / X B」声明，前三种都已各有闸门：

| 声明形式 | 例子 | 谁在守 |
|---|---|---|
| 规模表逐行 | `\\| \\`x.md\\` \\| ... \\| 4,112 \\| 90 \\|` | `test_operation_contracts_udc_layout` / `test_setting_contracts_override` 等 |
| 合计行 | `合计 **158 份 / 1,393,550 B**` | `test_udc_facts_root_layout` / `test_README_total_lines` |
| 入口 HEAD 表 | `docs/capability/STATUS.md` 的 sha/字节 | `test_capability_status_snapshot` |
| **域入口首行** | `> **UTD 契约层的应用域**：7 份 / 121,177 B / 1,395 行。` | **此前无人守** |

第 63 轮实测：11 处首行声明里 **2 处漂移**，而且两处的错法完全不同：

- `application/`：份数对、**字节差 60 B** —— 第 60 轮改了正文里的三条 java 路径
  （`DeployNormalDto` / `DeployBusinessTypeEnum` / `AppErrorCode`），字节变了，首行没跟。
- `menu/`：份数对、**字节也对**、**行数差 192 行（449 声明 vs 257 实测，虚报 75%）**。

`menu/` 那处是关键证据：**「行」这个分量从来没被任何闸门核过**。
前三种声明形式里，规模表闸门大多只比字节和份数，合计闸门只比份数和字节。
于是「行」成了唯一可以长期胡说而无人发现的字段 —— 而它恰好是最常被人用来判断
「这份东西有多重」的那一个。

## 判据

对每个含 `README.md`、且顶层有 ≥2 份 md 的 `docs/` 目录：
读 README 前 12 行，若出现 `N 份 / X B`（可带 `/ L 行`），
则三个分量都必须等于**除 README 自身外**顶层 md 的实测值。

「除 README 自身外」是这几个域入口的既定口径（README 是导航，不是被登记的内容）。
带子目录的目录（如 `core/facts/udc/`）不在此列 —— 它们有自己的合计闸门。
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

DECL = re.compile(r"(\d+)\s*份\s*/\s*([\d,]+)\s*B(?:\s*/\s*([\d,]+)\s*行)?")
SKIP = ("/artifacts/", "/ledger/", "/node_modules/", "/.venv/")


def _entries():
    """(目录, README 路径, 实测(份, 字节, 行), 声明 match) 的列表。"""
    out = []
    for d in sorted(ROOT.joinpath("docs").rglob("*")):
        if not d.is_dir():
            continue
        rel = d.relative_to(ROOT).as_posix()
        if any(s in rel for s in SKIP):
            continue
        readme = d / "README.md"
        if not readme.is_file():
            continue
        mds = [f for f in d.glob("*.md") if f.name != "README.md"]
        if len(mds) < 2:
            continue
        head = "\n".join(readme.read_text(encoding="utf-8", errors="replace").split("\n")[:12])
        m = DECL.search(head)
        if not m:
            continue
        real = (
            len(mds),
            sum(len(f.read_bytes()) for f in mds),
            sum(len(f.read_text(encoding="utf-8", errors="replace").splitlines()) for f in mds),
        )
        out.append((rel, m, real))
    return out


def test_entry_headline_counts_match_disk():
    """首行「N 份 / X B / L 行」三个分量都要对。"""
    bad = []
    for rel, m, (n, b, l) in _entries():
        d_n = int(m.group(1))
        d_b = int(m.group(2).replace(",", ""))
        d_l = int(m.group(3).replace(",", "")) if m.group(3) else None
        if d_n != n:
            bad.append("%s: 份 声明 %d 磁盘 %d" % (rel, d_n, n))
        if d_b != b:
            bad.append("%s: 字节 声明 %s 磁盘 %s" % (rel, m.group(2), format(b, ",")))
        if d_l is not None and d_l != l:
            bad.append("%s: 行 声明 %s 磁盘 %s" % (rel, m.group(3), format(l, ",")))
    assert not bad, (
        "域入口首行声明已漂移（改了正文必然改字节/行，首行最容易忘）：\n  "
        + "\n  ".join(bad)
        + "\n\n修法：改成实测值。**不要**删掉「行」这个分量 —— "
          "它是四种声明形式里唯一长期无人核的字段，删掉就等于继续让它烂。")


def test_line_component_is_actually_present_somewhere():
    """反退化：「行」这个分量不许被整体删掉来让闸门变绿。

    第 63 轮之前没有任何闸门核过「行」，所以最省事的"修复"是把它删了。
    这条断言守住最低覆盖：至少 5 处首行声明必须还带着行数。
    """
    with_lines = [rel for rel, m, _ in _entries() if m.group(3)]
    assert len(with_lines) >= 5, (
        "只剩 %d 处首行声明带「行」分量（应 ≥5）—— 有人把行数删掉来绕过闸门？\n  %s"
        % (len(with_lines), with_lines))


def test_menu_line_count_is_not_inflated():
    """`menu/` 的行数曾是 449，实测 257（虚报 75%）。留一条点名断言防回退。

    这处特别值得记：份数和字节都是对的，只有行数错 —— 说明它不是手误抄错，
    而是「行」这个维度根本没被核过。只看份/字节的检查永远不会发现它。
    """
    d = ROOT / "docs/operation-contracts/udc/menu"
    mds = [f for f in d.glob("*.md") if f.name != "README.md"]
    real = sum(len(f.read_text(encoding="utf-8", errors="replace").splitlines()) for f in mds)
    head = "\n".join((d / "README.md").read_text(encoding="utf-8").split("\n")[:12])
    assert "%s 行" % format(real, ",") in head, (
        "menu/ 首行没写实测行数 %s（历史上这里写过 449，虚报 75%%）" % format(real, ","))
    assert "449 行" not in head, "menu/ 首行又回到 449 行了"

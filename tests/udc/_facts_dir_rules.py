"""目录计数口径的单一来源。

**为什么要有这个文件：** 同一个口径（含不含 README、递归不递归）在
`test_README_total_lines.py` 与 `test_entity_facts_layout.py` 里各算一遍，
只要任一处改了，两处就会给出互相矛盾的判决，而「哪个对」没人知道。

第 47 轮教训：**方法论写在进度文件里等于没生效，得落成闸门里的断言。**
本文件是那句断言的零件——口径只写一次。

口径定义：
- `TOP(non_readme)`  = 目录下 `*.md` 顶层计数，**不含 README.md**（全库主流写法）
- `REC(non_readme)`  = 递归子目录的 `*.md` 计数，**不含本目录 README.md**
- 行数一律 `splitlines()`，**绝不用 count(b"\n")**（全库 16 份 md 无结尾换行，两者差 1）
"""
from pathlib import Path


def count_top(d: Path) -> tuple[int, int]:
    """顶层：份数（不含 README.md）、字节数（不含 README.md）。"""
    fs = [f for f in d.glob("*.md") if f.is_file() and f.name != "README.md"]
    return len(fs), sum(f.stat().st_size for f in fs)


def count_all(d: Path, *, include_self: bool = False) -> tuple[int, int]:
    """递归：份数、字节数。include_self=False 时排除 d/README.md 自身。"""
    fs = [f for f in d.rglob("*.md") if f.is_file()]
    if not include_self:
        fs = [f for f in fs if f != d / "README.md"]
    return len(fs), sum(f.stat().st_size for f in fs)


def lines_of(f: Path) -> int:
    """行数唯一口径 —— splitlines()。"""
    return len(f.read_bytes().decode("utf-8", errors="replace").splitlines())

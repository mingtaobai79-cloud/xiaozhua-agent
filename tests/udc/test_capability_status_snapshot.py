# -*- coding: utf-8 -*-
"""docs/capability/STATUS.md 的「2026-11-07 实测」列必须与磁盘一致。

背景：STATUS.md 是 phase1 交付时点的快照，正文里 8 处 `NNNN B / sha256` 全是历史值。
2026-11-07 复核发现 8 份能力文档里 7 份已漂移、A8 反而又改过一轮，人工核对一次就过期一次。

本测试把「右侧实测列」变成闸门：
- A1–A8 每一行的字节数与 sha256 前 8 位必须等于磁盘
- 目录存在性断言（`adapters/`、`installer/`、`core/{role,facts,skills,tools}` 必须在；
  `modules/`、`sandbox/`、`core/capabilities/` 必须不在）

判据纪律：左列是历史时点值，**不校验**也不改；只校验右列与本轮实测是否同步。
改这 8 份文档却不同步改表 → 红灯。
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "capability" / "STATUS.md"
CAP = ROOT / "docs" / "capability"

# 表格行形如：| A1 ARCHITECTURE.md | 16594 B / `00391301…` | 16843 B / `d6a3dcfe…` |
ROW = re.compile(
    r"\| A(\d) ([A-Za-z0-9_\-]+\.md) \| [^|]* \| (\d+) B / `([0-9a-f]{8})…`"
)

EXPECT_PRESENT = [
    "adapters",
    "installer",
    "core/role",
    "core/facts",
    "core/skills",
    "core/tools",
]
EXPECT_ABSENT = ["modules", "sandbox", "core/capabilities"]


def parse_rows(text: str) -> dict:
    """解析 A1–A8 实测表 → {序号: (文件名, 字节数, sha8)}。"""
    rows = {}
    for m in ROW.finditer(text):
        rows[int(m.group(1))] = (m.group(2), int(m.group(3)), m.group(4))
    return rows


def check_measured_column(rows: dict, cap_dir: Path) -> list:
    """逐条比对实测列与磁盘。返回问题列表（空 = 通过）。"""
    problems = []
    for n, (name, size, sha8) in sorted(rows.items()):
        target = cap_dir / name
        if not target.is_file():
            problems.append("A%d %s: 文件不存在" % (n, name))
            continue
        data = target.read_bytes()
        real = hashlib.sha256(data).hexdigest()
        if len(data) != size:
            problems.append("A%d %s: 表说 %d B，磁盘 %d B" % (n, name, size, len(data)))
        if not real.startswith(sha8):
            problems.append("A%d %s: 表说 %s…，磁盘 %s…" % (n, name, sha8, real[:8]))
    return problems


def _rows():
    return parse_rows(DOC.read_text(encoding="utf-8"))


def test_table_covers_all_eight_docs():
    """8 行都在，且文件名对得上——防止表格被改坏导致闸门静默失效。"""
    rows = _rows()
    assert sorted(rows) == list(range(1, 9)), "STATUS.md 的 A1–A8 实测表行数不对: %r" % sorted(rows)
    for n, (name, _size, _sha) in rows.items():
        assert (CAP / name).is_file(), "A%d 指向的 %s 不存在" % (n, name)


def test_measured_column_matches_disk():
    """右侧「实测」列必须与磁盘字节一致；漂移即失败并打印差异。"""
    problems = check_measured_column(_rows(), CAP)
    assert not problems, "STATUS.md 实测列已漂移（改文档就同步改表）:\n  " + "\n  ".join(problems)


def test_gate_bites_on_mutation():
    """内存内突变自证：把某行改错，check 必须报错（不写文件 ⇒ 失败不可能是并发会话造成）。"""
    rows = _rows()
    assert rows, "表格没解析出任何行，突变测试无从进行"
    n = sorted(rows)[0]
    name, size, sha8 = rows[n]
    mutated = dict(rows)
    mutated[n] = (name, size + 1, sha8)
    assert check_measured_column(mutated, CAP), "字节数改错 1 也没报，闸门失效"
    mutated[n] = (name, size, "00000000")
    assert check_measured_column(mutated, CAP), "sha 改错也没报，闸门失效"


def test_directory_existence_claims_hold():
    """目录存在性断言：表里说存在的必须在，说未建的必须不在。"""
    missing = [d for d in EXPECT_PRESENT if not (ROOT / d).is_dir()]
    created = [d for d in EXPECT_ABSENT if (ROOT / d).exists()]
    problems = []
    if missing:
        problems.append("表说在盘但实际不存在: " + ", ".join(missing))
    if created:
        problems.append("表说未建但实际已建: " + ", ".join(created))
    assert not problems, "；".join(problems)

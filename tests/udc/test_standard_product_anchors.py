"""core/facts/standard-product/ 的 sha256 锚点必须与磁盘一致。

背景：`tests/udc/test_facts_index_anchors.py` 只守 `core/facts/spi/` 子树的锚。
`core/facts/standard-product/` 有三条锚散落在两处（INDEX L119 + 该目录 README.md §五），
2026-11-07 就因为一次脱敏提交（`85f0b211` 把本机 jar 路径改成 Maven 坐标、
manifest.json 去掉 `source_jar_path`）而**静默漂移**：
INDEX 里还写着 `4cd71033…efede` / `d7643f75…34f8`，磁盘上却是 `9b89172f…` / `7da53941…`。

判据：
- INDEX L119 与 standard-product/README.md §五 声称的 sha256 前 8 位 == 磁盘
- 声称的字节数 == 磁盘
- 23 格表里每行的字节数与行数 == 磁盘（表是人工维护的，容易腐坏）
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "core" / "facts" / "INDEX.md"
SP = ROOT / "core" / "facts" / "standard-product"

# 被锚定的大件：`<文件名>`=`abcdef12…34567`
ANCHORED = [
    SP / "standard-product-contracts.md",
    SP / "evidence" / "bytecode" / "manifest.json",
    SP / "reconciliation.md",
]

# 23 格表行：`| ① | \`file.md\` | 11,830 | 219 |`
ROW = re.compile(r"^\|\s*[①-㉓]\s*\|\s*`([^`]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|$", re.M)


def _sha(p: Path):
    data = p.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def _claimed_anchor(text: str, name: str):
    """找出 `<name>`=`abcdef12…34567` 形式的声称锚（只取**当前**锚，不取「旧锚 xx 作废」）。"""
    pat = re.compile(
        r"`(?:[A-Za-z0-9_\-./]*/)?" + re.escape(name) + "`"
        + r"=`([0-9a-f]{8})…([0-9a-f]{3,8})`"
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(1), m.group(2)


def test_index_anchors_match_disk():
    """INDEX L119 声称的两条锚必须与磁盘一致。"""
    text = INDEX.read_text(encoding="utf-8")
    bad = []
    for p in ANCHORED[:2]:  # INDEX 只锚 contracts 与 manifest
        got = _claimed_anchor(text, p.name)
        if got is None:
            bad.append("%s: INDEX 里找不到锚" % p.name)
            continue
        sha, size = _sha(p)
        head, tail = got
        if not sha.startswith(head) or not sha.endswith(tail):
            bad.append(
                "%s: INDEX 锚 %s…%s 但磁盘是 %s…%s"
                % (p.name, head, tail, sha[:8], sha[-5:])
            )
        # 若锚附近写了字节数（`34,217 B`），也要对
        if p == ANCHORED[0] and "34,217 B" in text and size != 34217:
            bad.append("%s: INDEX 写 34,217 B 但磁盘 %d" % (p.name, size))
    assert not bad, "INDEX 的 standard-product 锚已漂移：\n  " + "\n  ".join(bad)


def test_readme_anchor_block_matches_disk():
    """standard-product/README.md §五 的四行锚块必须与磁盘逐条一致。"""
    readme = SP / "README.md"
    assert readme.exists(), "缺 core/facts/standard-product/README.md（目录入口）"
    text = readme.read_text(encoding="utf-8")
    block = text.split("## 五、锚点现值")[1].split("```")[1]
    checked = 0
    for p in ANCHORED:
        line = next((l for l in block.splitlines() if p.name in l), None)
        if line is None:
            continue
        m = re.search(r"([\d,]{3,})\s*B\s+([0-9a-f]{8})(?:…([0-9a-f]{3,8})|([0-9a-f]{56}))", line)
        assert m, "README 锚行格式坏了：%r" % line
        size_claimed = int(m.group(1).replace(",", ""))
        head = m.group(2)
        tail = m.group(3) if m.group(3) else (m.group(4) or "")[-5:]
        sha, size = _sha(p)
        assert size_claimed == size, "%s: README 写 %d B 但磁盘 %d" % (p.name, size_claimed, size)
        assert sha.startswith(head) and sha.endswith(tail), (
            "%s: README 锚 %s…%s 但磁盘 %s…%s"
            % (p.name, head, tail, sha[:8], sha[-5:])
        )
        checked += 1
    assert checked == len(ANCHORED), "README 锚块只核到 %d 条，应为 %d" % (checked, len(ANCHORED))


def test_fact_table_rows_match_disk():
    """23 格表的每行字节数/行数必须与磁盘一致（人工维护的表容易腐坏）。"""
    text = (SP / "README.md").read_text(encoding="utf-8")
    rows = ROW.findall(text)
    assert len(rows) == 23, "23 格表只解析出 %d 行（表格式被改坏了？）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = SP / name
        if not p.exists():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        size = p.stat().st_size
        nlines = p.read_bytes().count(b"\n")
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, size))
        if nlines != int(lines_s):
            bad.append("%s: 表写 %s 行磁盘 %d" % (name, lines_s, nlines))
    assert not bad, "23 格表已腐坏：\n  " + "\n  ".join(bad)


def test_readme_lists_every_md_file():
    """目录下每个 .md（除 README）都必须在本文件里被提到，否则等于没入口。"""
    text = (SP / "README.md").read_text(encoding="utf-8")
    missing = sorted(
        p.name for p in SP.glob("*.md")
        if p.name != "README.md" and p.name not in text
    )
    assert not missing, "这些事实格没在入口 README 里出现：%s" % missing

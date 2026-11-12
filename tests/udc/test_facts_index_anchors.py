"""core/facts/INDEX.md 的 sha256 锚点必须与磁盘一致。

背景：INDEX 的 SPI 行把四格事实件 + evidence/README.md 的 `sha256前缀…(字节数)`
直接写在表格里当锚。这些锚一旦漂移，索引就在无声地撒谎——2026-11-07 实测就漂了 2 条
（spi-ext-runtime.md 被脱敏改写主机名、evidence/README.md 被补时点声明）。

本测试把"人工核对锚点"变成闸门：解析 INDEX 里形如 `xxx.md abcd1234…(1234B)` 的锚，
按 SPI 目录树找同名文件，逐条比对 sha256 前缀与字节数。

判据：
- sha256 前 8 位必须与磁盘一致
- 若锚里写了字节数，必须精确相等
- 找不到文件 → 失败（锚指向不存在的件）
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "core" / "facts" / "INDEX.md"
SPI = ROOT / "core" / "facts" / "spi"

# `spi-ext-runtime.md b76b68f2…(18529B)` / `evidence/README.md 98762a6b…(4340B)`
ANCHOR = re.compile(r"([A-Za-z0-9_\-./]+\.(?:md|txt|json))\s*([0-9a-f]{8})…\((\d+)B")


def _spi_files() -> dict:
    """SPI 子树下所有文件，按 basename 建索引（锚里只写文件名或 evidence/xxx）。"""
    out = {}
    for p in SPI.rglob("*"):
        if p.is_file():
            out.setdefault(p.name, []).append(p)
    return out


def _anchors():
    text = INDEX.read_text(encoding="utf-8")
    seen = set()
    for m in ANCHOR.finditer(text):
        name, sha8, size = m.group(1), m.group(2), int(m.group(3))
        key = (name, sha8, size)
        if key in seen:
            continue
        seen.add(key)
        yield name, sha8, size


def test_index_anchor_format_is_parseable():
    """锚格式本身没被改坏——至少能解析出 4 条（四格事实件）。"""
    anchors = list(_anchors())
    names = {a[0] for a in anchors}
    assert len(anchors) >= 4, "INDEX SPI 行的 sha 锚少于 4 条，格式可能被改坏了: %r" % anchors
    assert "spi-ext-registration.md" in names
    assert "spi-ext-runtime.md" in names


def test_index_sha_anchors_match_disk():
    """每一条锚都必须与磁盘字节一致。漂移即失败，提示改锚或改件。"""
    files = _spi_files()
    bad = []
    for name, sha8, size in _anchors():
        cands = files.get(Path(name).name, [])
        if not cands:
            bad.append("%s: 锚指向的文件在 core/facts/spi/ 下找不到" % name)
            continue
        # 同名多份时优先取路径后缀匹配的那份
        target = cands[0]
        for c in cands:
            if str(c).replace("\\", "/").endswith(name):
                target = c
                break
        data = target.read_bytes()
        real = hashlib.sha256(data).hexdigest()
        if not real.startswith(sha8):
            bad.append(
                "%s: 锚 sha256 %s… 但磁盘是 %s…（%d B）"
                % (name, sha8, real[:8], len(data))
            )
        elif len(data) != size:
            bad.append(
                "%s: 锚字节数 %d 但磁盘是 %d" % (name, size, len(data))
            )
    assert not bad, "INDEX 的 sha 锚已漂移：\n  " + "\n  ".join(bad)

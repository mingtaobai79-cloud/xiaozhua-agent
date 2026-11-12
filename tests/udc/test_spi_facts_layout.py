"""core/facts/spi/ 的事实层入口必须与磁盘一致。

本目录 18 份 / 137,857 B = 顶层 5 份事实格 + evidence/ 13 份，2026-11-07 前零入口
（evidence/README.md 只管证据，不管这 5 份事实格）。

两条最值钱的东西，本测试守着不许被整理掉：
1. **判据边界**：配置启用 ≠ 插件已加载 ≠ 实现被调用；通道不可达 ≠ 运行态未发生。
   这句话在三份文件里反复出现，是这一域最容易误判的地方。
2. **e7/e8 是 BLOCKED 的记录，不是失败要清理的垃圾**：e8 明文记
   「host-key 绕行 0 / 重试 0 / 写面 0」，e9 之所以可信正因为 e8 记了"没绕行"。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "core" / "facts" / "spi"

TOP = re.compile(r"^\|\s*`(spi-ext-[a-z-]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)
EVDIR = re.compile(r"^\|\s*`(evidence(?:/[a-z-]+)?)/?`\s*\|\s*(\d+)\s*\|\s*([\d,]+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 core/facts/spi/README.md（事实层入口）"
    return p.read_text(encoding="utf-8")


def _stat(d, exclude_self=False):
    files = [p for p in Path(d).rglob("*.md")]
    if exclude_self:
        files = [p for p in files if p != Path(d) / "README.md"]
    return len(files), sum(p.stat().st_size for p in files)


def test_top_level_table_matches_disk():
    rows = TOP.findall(_readme())
    assert len(rows) == 5, "顶层事实格表解析出 %d 行（应有 5 份）" % len(rows)
    bad = []
    for name, size_s, lines_s, refs_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s 不存在" % name)
            continue
        if p.stat().st_size != int(size_s.replace(",", "")):
            bad.append("%s 字节表写 %s 磁盘 %d" % (name, size_s, p.stat().st_size))
        nl = p.read_bytes().count(bytes([10]))
        if nl != int(lines_s.replace(",", "")):
            bad.append("%s 行数表写 %s 磁盘 %d" % (name, lines_s, nl))
    assert not bad, "顶层事实格表已腐坏：\n  " + "\n  ".join(bad)


def test_evidence_dirs_match_disk():
    rows = EVDIR.findall(_readme())
    assert rows, "README 里找不到 evidence 子目录规模表"
    bad = []
    for rel, n_s, size_s in rows:
        d = D / rel.strip("/")
        if not d.is_dir():
            bad.append("%s/ 不存在" % rel)
            continue
        n, size = _stat(d)
        if n != int(n_s):
            bad.append("%s/: 表写 %s 份 磁盘 %d 份" % (rel, n_s, n))
        if size != int(size_s.replace(",", "")):
            bad.append("%s/: 表写 %s B 磁盘 %d B" % (rel, size_s, size))
    assert not bad, "evidence 子目录规模表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches_disk():
    m = re.search(r"(\d+) 份 / \*\*([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「N 份 / X B」声明"
    n, size = _stat(D, exclude_self=True)
    claimed_n = int(m.group(1))
    claimed_b = int(m.group(2).replace(",", ""))
    assert claimed_n == n, "声称 %s 份，磁盘（不含本 README）%d 份" % (claimed_n, n)
    assert claimed_b == size, "声称合计 %s B，磁盘实算 %d B" % (claimed_b, size)


def test_all_fact_cells_named():
    text = _readme()
    missing = [p.name for p in D.glob("spi-ext-*.md") if p.name not in text]
    assert not missing, "这些事实格没在入口 README 里出现：%s" % missing


def test_judgement_boundary_still_in_sources():
    """判据边界是本域最贵的一句话，原始文件里必须还在。"""
    for f, needles in (
        ("spi-ext-live.md", ["配置启用", "插件已加载", "实现被调用"]),
        ("spi-ext-runtime.md", ["配置启用 ≠ 插件已加载 ≠ 实现被调用", "通道不可达"]),
    ):
        p = D / f
        assert p.is_file(), "%s 不见了" % f
        txt = p.read_text(encoding="utf-8", errors="replace")
        for n in needles:
            assert n in txt, "%s 里的判据边界「%s」被删了" % (f, n)
    # README 自己也要把这条判据写出来
    assert "配置启用 ≠ 插件已加载 ≠ 实现被调用" in _readme(), (
        "入口 README 没把最贵的判据边界写进去")


def test_blocked_evidence_not_deleted():
    """e7/e8 是 BLOCKED 记录，e9 可信的前提。不许因为"失败"而删。"""
    live = D / "evidence" / "live"
    for name in ("e8-runtime-plugin-load-blocked-20261004.md",
                 "e9-live-plugin-drop-and-registration-20261004.md"):
        assert (live / name).is_file(), (
            "%s 不见了。e8 记的是「不绕行」的纪律，e9 之所以可信正因为 e8 记了没绕行" % name)
    e8 = (live / "e8-runtime-plugin-load-blocked-20261004.md").read_text(
        encoding="utf-8", errors="replace")
    assert "host-key" in e8 and "255" in e8, (
        "e8 的失败记录（host-key / rc=255）被改了——那是它作为证据的全部价值")
    assert "不构成新的 LIVE 证据" in e8, "e8 的自我限定声明被删了"


def test_no_customer_identifiers_in_readme():
    """本层证据件含客开模块名与客户域名，但入口 README 只许写形态、不许写值。"""
    text = _readme()
    banned = ["changhong", "CHNs", "cip-spi-user", "seeyon-test2", "lowcode-test2"]
    hit = [b for b in banned if b.lower() in text.lower()]
    assert not hit, "入口 README 里出现了客户标识：%s（本层只写形态不写值）" % hit

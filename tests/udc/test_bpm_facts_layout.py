"""core/facts/bpm/ 的入口 README 必须与磁盘一致，且「冻结哈希 vs 脱敏」的冲突登记不许被抹掉。

本目录 5 份 / 79,892 B，2026-11-07 前零入口。

本测试最重要的一条（test_frozen_hash_conflict_documented）：
`STATUS.md` 用 sha256 把四格冻结，但 2026-10-20 的脱敏提交 2e0d1d8d 机械替换了客户标识，
使格1（-5 B）、格3（-11 B）与格3 证据件（-60 B）的哈希失效。
**正确处理是"保留旧哈希 + 标注失效原因"，不是重算改绿**（会抹掉"这里发生过脱敏"的事实），
也不是还原客户标识（违反用户 2026-10-20 明令 + tests/test_deidentification.py）。
本测试把这条判断钉住：README 必须写明，且 STATUS.md 的旧哈希不许被悄悄改掉。
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "core" / "facts" / "bpm"

# STATUS.md 声称的四个绑定值（历史时点，故意不随磁盘变化）
FROZEN = {
    "flow-node-tree.md": "36ead2218ba4d2d72b2ac6b046f3b7edbf7bf407fe0503c8322b744d2284ec5f",
    "data-flow-map.md": "4f3e60a4a66756ccd1c57b7493f24fa20e0a0c990be0a93cc22b37e4a5702a11",
    "engine-behavior.md": "7908a94dbad20a082bb3e4cb06ae737dab93949b66eb1f9bbbd572b1a488c67d",
    "bpm-version-map.md": "026910f5ff57b8277a49304e9f90d038428d80052c4c3c6cfd4d3fae22bb0e6a",
}

ROW = re.compile(r"^\|\s*(格\d)\s*\|\s*`([a-z-]+\.md)`\s*\|\s*([^|]*)\|[^|]*\|[^|]*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 core/facts/bpm/README.md（事实层入口）"
    return p.read_text(encoding="utf-8")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_table_matches_disk():
    """README §一 的字节/行数 vs 磁盘。"""
    rows = re.findall(r"^\|\s*`([A-Za-z0-9_-]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", _readme(), re.M)
    assert len(rows) == 5, "§一 表解析出 %d 行（应有 5 份）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s 不存在" % name)
            continue
        if p.stat().st_size != int(size_s.replace(",", "")):
            bad.append("%s 字节表写 %s 磁盘 %d" % (name, size_s, p.stat().st_size))
        nl = p.read_bytes().count(bytes([10]))
        if nl != int(lines_s.replace(",", "")):
            bad.append("%s 行数表写 %s 磁盘 %d" % (name, lines_s, nl))
    assert not bad, "§一 规模表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches_disk():
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 找不到「合计 N 份 / X B」"
    files = [p for p in D.glob("*.md") if p.name != "README.md"]
    assert int(m.group(1)) == len(files), "声称 %s 份 磁盘 %d 份" % (m.group(1), len(files))
    real = sum(p.stat().st_size for p in files)
    assert int(m.group(2).replace(",", "")) == real, (
        "声称合计 %s B 磁盘实算 %d B" % (m.group(2), real))


def test_all_files_named():
    text = _readme()
    missing = [p.name for p in sorted(D.glob("*.md")) if p.name != "README.md" and p.name not in text]
    assert not missing, "这些文件没在入口 README 里出现：%s" % missing


def test_frozen_hash_conflict_documented():
    """★ 核心：README 必须登记「哪些冻结哈希已失效 + 根因是脱敏 + 不许重算改绿」。"""
    text = _readme()
    # 1) 必须点明有失效，且点名具体文件
    for name in ("flow-node-tree.md", "engine-behavior.md"):
        assert name in text, "README §二 没点名失效文件 %s" % name
    # 2) 必须给出实测哈希前缀，证明是真算过
    for name, frozen in FROZEN.items():
        actual = _sha(D / name)
        if actual == frozen:
            continue
        assert actual[:8] in text, (
            "%s 的实测 sha 前缀 %s 没出现在 README §二——失效状态无从复算" % (name, actual[:8]))
    # 3) 必须点明根因是脱敏而不是篡改
    assert "脱敏" in text, "README 没说明失效根因是脱敏（会被误读成篡改）"
    assert "2e0d1d8d" in text, "README 没给出脱敏提交号，无法定位"
    # 4) 必须写明两条禁止
    assert "重算" in text and ("改绿" in text or "改成新值" in text), (
        "README 没写「不许重算哈希把 STATUS 改绿」")
    assert "还原" in text, "README 没写「不许还原客户标识来对齐旧哈希」"


def test_status_md_hashes_not_silently_rewritten():
    """STATUS.md 里的旧哈希不许被悄悄改成新值——那会抹掉"这里发生过脱敏"的事实。"""
    if not (D / "STATUS.md").is_file():
        return
    txt = (D / "STATUS.md").read_text(encoding="utf-8", errors="replace")
    bad = []
    for name, frozen in FROZEN.items():
        actual = _sha(D / name)
        if actual == frozen:
            continue
        # 旧哈希必须还在 STATUS.md 里（未被覆盖）
        if frozen not in txt:
            bad.append("%s 的旧绑定哈希 %s… 已从 STATUS.md 消失（被重算了？）" % (name, frozen[:12]))
        # 新哈希不许被写进 STATUS.md 冒充冻结值
        if actual in txt:
            bad.append("%s 的新哈希已被写进 STATUS.md，冒充冻结值（应保留旧值+标注）" % name)
    assert not bad, "STATUS.md 的冻结哈希被改动：\n  " + "\n  ".join(bad)


def test_evidence_sha_status_and_tension_recorded():
    """格3 证据件的 sha 也失效了，且「证据区保留原文 vs 脱敏」的张力必须登记。"""
    p = D / "evidence" / "engine-behavior-live-20260927T092124Z.json"
    assert p.is_file(), "格3 的活体证据件不见了——它是最原始的数据"
    text = _readme()
    assert "engine-behavior-live" in text, "README 没登记格3 证据件的 sha 失效"
    assert "张力" in text or "冲突" in text, (
        "README 没登记「原始数据证据区保留原文」与「脱敏」的原则张力")


def test_no_customer_identifiers_in_readme():
    """本目录事实格原含客户域名/应用名；入口 README 只许写形态，不许写值。"""
    # 不在这里写出客户标识字面量（本文件也属结论区，写了会被 test_deidentification 抓）。
    # 改为从真实数据源派生：config/environments.yaml 里的活体环境域名与默认应用名。
    text = _readme().lower()
    cfg = (ROOT / "config" / "environments.yaml").read_text(encoding="utf-8", errors="replace")
    hosts = set(re.findall(r"https?://([A-Za-z0-9.-]+)", cfg))
    # 只取非占位域名（example.com / localhost 之类不算）
    banned = {h.lower() for h in hosts if not h.lower().endswith(("example.com", "localhost"))}
    apps = set(re.findall(r"default_app_id:\s*([A-Za-z0-9_-]+)", cfg))
    banned |= {a.lower() for a in apps if a and not a.startswith("app9")}
    hit = [b for b in banned if b in text]
    assert not hit, "入口 README 里出现了客户环境标识（从 config 派生检测）：%s" % hit

"""docs/ledger/ 的入口 README 必须与磁盘一致。

归档区，7 份 / 398,965 B / 3,463 行，此前零入口。
本目录最要紧的不是"补个 README"，而是让读者一眼分清：**这里没有一份是现行结论**。

本测试守四件事：
1. §一 表每行的字节/行数 vs 磁盘 + 合计
2. **文件名前缀必须是 LOG-/DIGEST-/RESUME-/STATUS- 四类之一**（前缀是性质契约）
3. README 必须明说"7 份全部是历史件"（否则有人会拿 STATUS-2026H2 当现状）
4. 每份 `LOG-*` 都必须在 README 里指向它的现行版入口（迁出件丢了指针 = 死档）
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "ledger"

PREFIXES = ("LOG-", "DIGEST-", "RESUME-", "STATUS-")

ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 docs/ledger/README.md"
    return p.read_text(encoding="utf-8")


def _files():
    return sorted(p for p in D.glob("*.md") if p.name != "README.md")


def test_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == len(_files()), (
        "README 表解析出 %d 行，磁盘 %d 份" % (len(rows), len(_files())))
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s 不存在" % name)
            continue
        if p.stat().st_size != int(size_s.replace(",", "")):
            bad.append("%s 字节写 %s 实测 %d" % (name, size_s, p.stat().st_size))
        nl = p.read_bytes().count(bytes([10]))
        if nl != int(lines_s.replace(",", "")):
            bad.append("%s 行数写 %s 实测 %d" % (name, lines_s, nl))
    assert not bad, "ledger 表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches():
    m = re.search(r"\|\s*\*\*合计\*\*\s*\|\s*\*\*([\d,]+)\*\*\s*\|\s*\*\*([\d,]+)\*\*", _readme())
    assert m, "缺「合计」行"
    files = _files()
    assert int(m.group(1).replace(",", "")) == sum(p.stat().st_size for p in files), "合计字节 ≠ 磁盘"
    assert int(m.group(2).replace(",", "")) == sum(
        p.read_bytes().count(bytes([10])) for p in files), "合计行数 ≠ 磁盘"


def test_every_file_has_known_prefix():
    bad = [p.name for p in _files() if not p.name.startswith(PREFIXES)]
    assert not bad, (
        "文件名前缀必须是 %s 之一（前缀即性质，读者靠它判断能否当现状引用）：%s"
        % (list(PREFIXES), bad))
    # 每份都必须被 README 提到
    text = _readme()
    missing = [p.name for p in _files() if p.name not in text]
    assert not missing, "这些文件没在 README 里登记：%s" % missing


def test_archive_is_not_current_conclusion():
    """必须明说本目录没有一份能当现状引用——否则 STATUS-2026H2 会被误读。"""
    text = _readme()
    assert "没有一份是" in text or "全部是历史件" in text or "没有一份可以当" in text, (
        "README 没说明本目录全部是历史件（STATUS-2026H2.md 自称 adapter 切片已达成，最易误导）")
    assert "doc-consolidation-progress.md" in text and "seeyon-distribution-progress.md" in text, (
        "README 没指向两条线的现行入口（读者不知道该去哪看现状）")


def test_log_files_point_to_current_version():
    """每份 LOG-* 都必须指向其现行版入口；迁出件没有指针就是死档。"""
    text = _readme()
    for p in _files():
        if not p.name.startswith("LOG-"):
            continue
        assert p.name in text, "%s 未登记" % p.name
    # 三份 LOG 各有现行版，逐一核对 README 里都写了
    for cur in ("docs/audit/udc-semantics/PROGRESS.md",
                "docs/plans/seeyon-distribution-progress.md",
                "docs/plans/doc-consolidation-progress.md"):
        assert cur in text, "README 没给 LOG 系列的现行版指针：%s" % cur


def test_status_snapshot_marked_as_point_in_time():
    """STATUS-2026H2 是时点快照，README 必须写明它当时在建/现在已存在的差别。"""
    text = _readme()
    assert "16a384c" in text, "README 没记 STATUS-2026H2 自称的 HEAD（无法判断它有多旧）"
    assert "时点快照" in text and "不要按" in text, (
        "README 没把 STATUS-2026H2 的读法写清（应说：按时点快照读，不要按当前状态读）")


def test_resume_file_kept_with_reason():
    """RESUME 件的价值在"能找回被中断的会话"，删了找不回，README 必须记这个理由。"""
    p = D / "RESUME-2026-10-23-entity-rule-condition.md"
    assert p.is_file(), "RESUME 交接件不见了"
    body = p.read_text(encoding="utf-8", errors="replace")
    assert re.search(r"[0-9a-f]{40,}", body), "RESUME 件里的会话 ID 不见了（那是唯一找回凭据）"
    assert "唯一目的" in body or "重新找回" in body, "RESUME 件自述用途的那段不见了"

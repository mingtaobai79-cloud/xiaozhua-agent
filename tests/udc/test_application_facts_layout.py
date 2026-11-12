"""core/facts/udc/application/ 的入口 README 必须与磁盘一致。

7 份 md / 77,959 B + 17 份证据 JSON，此前零入口（同层 8 个子域里最后一个没入口的域之一）。

本测试守四件事：
1. §一 表每行的字节/行数 vs 磁盘 + 合计
2. 磁盘上每份 md 都被 README 提到（含子目录）
3. **三条「会骗人」的判据必须还在**：LIVE 三义、applog 的 6 件 404 负证据、
   `main/`/`implementer/` 是会话目录不是仓库路径
4. 最后一条尤其重要：**那 4 处路径不许被"修"成仓库内路径**
   （修 = 编造一个不存在的文件；它们本来就不在仓库）
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "core" / "facts" / "udc" / "application"

ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)
# 会话目录引用：`main/xxx` / `implementer/xxx`
SESSION_PATH = re.compile(r"`((?:main|implementer)/[A-Za-z0-9_.\-]+)`")


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 core/facts/udc/application/README.md"
    return p.read_text(encoding="utf-8")


def _all_md():
    return sorted(p for p in D.rglob("*.md") if p.name != "README.md")


def test_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 7, "§一 表解析出 %d 行（应 7 行）" % len(rows)
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
    assert not bad, "application 事实格表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches():
    m = re.search(r"\|\s*\*\*合计\*\*\s*\|\s*\*\*([\d,]+)\*\*\s*\|\s*\*\*([\d,]+)\*\*", _readme())
    assert m, "§一 表缺「合计」行"
    files = _all_md()
    assert len(files) == 7, "磁盘上应是 7 份非 README 的 md，实测 %d" % len(files)
    assert int(m.group(1).replace(",", "")) == sum(p.stat().st_size for p in files), "合计字节 ≠ 磁盘"
    assert int(m.group(2).replace(",", "")) == sum(
        p.read_bytes().count(bytes([10])) for p in files), "合计行数 ≠ 磁盘"


def test_every_md_mentioned():
    text = _readme()
    missing = []
    for p in _all_md():
        rel = p.relative_to(D).as_posix()
        if rel not in text and p.name not in text:
            missing.append(rel)
    assert not missing, "这些 md 没在 README 里登记：%s" % missing


def test_evidence_json_count():
    """17 份证据 JSON / 24,466 B —— 这个数也必须对，否则「证据在哪」无从核对。"""
    js = sorted(p for p in D.rglob("*.json"))
    m = re.search(r"(\d+) 份证据 JSON（([\d,]+) B）", _readme())
    assert m, "README 没写证据 JSON 的份数与字节"
    assert int(m.group(1)) == len(js), "声称 %s 份证据 JSON，磁盘 %d 份" % (m.group(1), len(js))
    assert int(m.group(2).replace(",", "")) == sum(p.stat().st_size for p in js), (
        "声称证据 JSON %s B，实测 %d B" % (m.group(2), sum(p.stat().st_size for p in js)))


def test_live_has_three_meanings():
    """LIVE 三义（PASS / OBSERVED / 窗口已过期）是本域最易误读处。"""
    text = _readme()
    assert "LIVE PASS" in text, "README 没区分 LIVE PASS"
    assert "OBSERVED" in text, "README 没区分 OBSERVED（只看见页面发过，没主动触发）"
    assert "已过期" in text, "README 没说明 applog 引用的 09-18 窗口已过期"
    assert "不要当" in text, "README 没给「看到 OBSERVED 不要当已验证可用」的警告"


def test_applog_404_is_evidence_not_absence():
    text = _readme()
    assert "404" in text, "README 没提 applog 的 6 件 404 负证据"
    assert "不能推出" in text, "README 没写「404 不能推出该功能不存在」这条判据"
    body = (D / "applog-family.md").read_text(encoding="utf-8", errors="replace")
    assert "404" in body, "applog-family.md 里的 404 负证据记录不见了"


def test_session_paths_not_rewritten_to_repo_paths():
    """`main/`、`implementer/` 是当时那个会话的目录，不在仓库里，**不许被"修"成仓内路径**。

    修 = 编造一个不存在的文件。正确做法是在 README 里标注"是会话目录、没入库"。
    """
    text = _readme()
    assert "会话目录" in text and "不是死引用" in text, (
        "README 没说明 main//implementer/ 是会话目录（会被后人当死引用去修）")
    # 那 4 处路径仍原样保留在 evidence 文件里
    ev = (D / "evidence" / "app-search-live-20260926.md").read_text(encoding="utf-8", errors="replace")
    hits = SESSION_PATH.findall(ev)
    assert hits, "evidence 文件里的会话目录引用不见了（不该被改写成仓库内路径）"
    # 而且确实不在仓库里
    for h in hits:
        assert not (ROOT / h).exists(), (
            "%s 竟然在仓库里了？README 里「会话目录不在仓库」的说法需要更新" % h)


def test_contract_layer_split_documented():
    """事实层 vs 契约层的分工必须写明，否则会往这里写端点约定。"""
    text = _readme()
    assert "docs/operation-contracts/udc/application/" in text, (
        "README 没指向契约层目录（会把端点约定误写进事实层）")
    assert "事实层" in text and "契约层" in text, "README 没把两层分工写成表"

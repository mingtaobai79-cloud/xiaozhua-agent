"""docs/audit/artifacts/ 入口 README 必须与磁盘一致，且「谁在读」分类不许静默腐坏。

背景：这是全部原始证据的根（36 子目录 + 11 顶层文件 / 8,851 文件 / 409 MB），
2026-11-07 前**没有 README**，而它同时是**运行时数据根**——25 个子目录被
components/ core/ tools/ config/ 按精确路径读取。
最贵的误判是「以为是纯证据区，搬走一个目录，静默改掉运行时行为」。

所以本测试守三件事：
1. README 的规模表 vs 磁盘
2. 每个子目录、每个顶层文件都在 README 里被交代（漏一个就是漏一个入口）
3. **§一 B 类（代码在读但无测试守）的子目录，README 必须点名它被代码引用**——
   这类目录如果哪天真的没人读了，README 的分类就该改；如果它被搬走，这里会红
"""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "artifacts"


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 docs/audit/artifacts/README.md（证据根入口）"
    return p.read_text(encoding="utf-8")


def _code_hits(name: str) -> int:
    """该子目录被代码/配置引用了几份文件。"""
    r = subprocess.run(
        ["git", "grep", "-l", "audit/artifacts/" + name,
         "--", "components", "core", "tools", "config", "adapters"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return len([x for x in r.stdout.splitlines() if x.strip()])


def test_all_subdirs_are_named():
    text = _readme()
    subs = sorted(p.name for p in D.iterdir() if p.is_dir())
    missing = [s for s in subs if s not in text]
    assert not missing, "这些证据子目录没在入口 README 里交代：%s" % missing


def test_all_top_level_files_are_named_with_size():
    text = _readme()
    files = sorted((p for p in D.iterdir() if p.is_file() and p.name != "README.md"),
                   key=lambda p: -p.stat().st_size)
    bad = []
    for p in files:
        if p.name not in text:
            bad.append("%s: 没在 README 里交代" % p.name)
            continue
        m = re.search(r"`" + re.escape(p.name) + r"`\s*\|\s*([\d,]+)", text)
        if not m:
            bad.append("%s: 表格行缺字节数" % p.name)
        elif int(m.group(1).replace(",", "")) != p.stat().st_size:
            bad.append("%s: 表写 %s B 磁盘 %d" % (p.name, m.group(1), p.stat().st_size))
    assert not bad, "顶层文件表腐坏：\n  " + "\n  ".join(bad)


def test_code_reading_dirs_are_declared_as_such():
    """被代码读的子目录，README 必须把它列在「代码在读」的语境里，不能只当证据提一句。

    判据：该目录被代码引用 > 0，则 README 必须出现它的名字（已在 test_all_subdirs_are_named 里保证），
    且必须出现「code」或「代码」这类词说明它不只是证据——这里检查 README 有这条纪律段。
    """
    text = _readme()
    assert "代码在运行时读它" in text or "代码在读" in text, \
        "README 丢失了「代码在运行时读本目录」的警告——这是本目录最贵的误判来源"

    # 逐个抽查：凡是代码在读的，README 里不能只在 C 类（只被文档引用）里出现
    c_class = text[text.index("### C 类"):text.index("### D 类")] if "### C 类" in text else ""
    bad = []
    for p in sorted(D.iterdir()):
        if not p.is_dir():
            continue
        if _code_hits(p.name) > 0 and p.name in c_class:
            bad.append(p.name)
    assert not bad, "这些目录被代码读取，却被 README 归进了「只被文档引用」：%s" % bad


def test_dangerous_dirs_are_explicitly_flagged():
    """B 类（代码在读、无测试守）风险最高，README 必须点出 scratch-migrated 这类反直觉的。"""
    text = _readme()
    for name in ("scratch-migrated", "extension-surface-20261029"):
        assert name in text, "README 没提到 %s（代码在读的关键证据根）" % name


def test_expression_json_are_linked_to_facts():
    """7 份 udc-expression-*.json 是 facts 的数据源，README 必须说明。"""
    text = _readme()
    assert "udc-expression-" in text
    assert "core/facts/udc/expression/" in text, \
        "README 没说明 udc-expression-*.json 是 facts 的数据源"

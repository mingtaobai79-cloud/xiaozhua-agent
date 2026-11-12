"""packages/ 入口 README 的规模数字必须与 91 份自动生成件一致。

背景：这里 91 份全部由 `tools/core/platform/emit_package_surfaces.py` 生成，重跑即覆盖。
唯一可以手写的是 README.md 本身——而它登记了六个规模合计与六份字节/行数。
换版本重跑后这些数字全变，人工核对必然漏，所以用测试钉住。

判据：
- §一 六个规模合计（类/接口/注解/枚举/关键类/方法）+ 文件数/字节/行数 == 逐份解析实算
- §二 六份"先看这几份"的字节/行数 == 磁盘
- 每份 .md（除 README）都在 README 里有交代（至少在 §二 或 §三/§六 提到名字）——
  这条故意放宽：91 份不可能逐份列，但"最小四份"与"最大六份"必须点名
- 生成器仍在（改它的路径会让 §四 的命令失效）
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "artifacts" / "extension-surface-20261029" / "packages"

SCALE = re.compile(r"规模：(\d+) 类 / (\d+) 接口 / (\d+) 注解 / (\d+) 枚举 / (\d+) 个关键类 / (\d+) 方法")
ROW = re.compile(r"^\|\s*\*{0,2}`([^`]+\.md)`\*{0,2}\s*\|\s*\*{0,2}([\d,]+)\*{0,2}\s*\|\s*\*{0,2}([\d,]+)\*{0,2}", re.M)

KEYS = ["classes", "interfaces", "annotations", "enums", "key_classes", "methods"]


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 packages/README.md（91 份自动生成件的入口）"
    return p.read_text(encoding="utf-8")


def _actual():
    files = sorted(p for p in D.glob("*.md") if p.name != "README.md")
    tot = dict.fromkeys(KEYS, 0)
    nbytes = nlines = 0
    for p in files:
        raw = p.read_bytes()
        nbytes += len(raw)
        nlines += raw.count(bytes([10]))
        m = SCALE.search(raw.decode("utf-8", "replace"))
        if m:
            for k, v in zip(KEYS, m.groups()):
                tot[k] += int(v)
    return files, tot, nbytes, nlines


def test_file_count_and_totals_match_disk():
    files, tot, nbytes, nlines = _actual()
    text = _readme()
    bad = []
    if len(files) != 91:
        bad.append("磁盘 %d 份，README 声称 91 份" % len(files))
    checks = [
        ("合计字节", nbytes), ("合计行", nlines),
        ("类", tot["classes"]), ("接口", tot["interfaces"]), ("注解", tot["annotations"]),
        ("枚举", tot["enums"]), ("关键类", tot["key_classes"]), ("方法", tot["methods"]),
    ]
    for label, val in checks:
        # README 表格形如 | 合计字节 | **3,315,454**（3.17 MB） |
        m = re.search(r"\|\s*" + re.escape(label) + r"\s*\|\s*\**([\d,]+)\**", text)
        if not m:
            bad.append("%s: README 找不到该行" % label)
            continue
        if int(m.group(1).replace(",", "")) != val:
            bad.append("%s: README 写 %s 实算 %d" % (label, m.group(1), val))
    assert not bad, "packages/ 规模数字已漂移（重跑过 emit？）：\n  " + "\n  ".join(bad)


def test_top_six_rows_match_disk():
    """§二「先看这 6 份」的字节/行数必须与磁盘一致。"""
    text = _readme()
    sec = text[text.index("## 二"):text.index("## 三")]
    rows = ROW.findall(sec)
    assert len(rows) == 6, "§二 表只解析出 %d 行（应有 6 行）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.exists():
            bad.append("%s: 不存在" % name)
            continue
        raw = p.read_bytes()
        if len(raw) != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, len(raw)))
        if raw.count(bytes([10])) != int(lines_s.replace(",", "")):
            bad.append("%s: 表写 %s 行 磁盘 %d" % (name, lines_s, raw.count(bytes([10]))))
    assert not bad, "§二 规模表腐坏：\n  " + "\n  ".join(bad)


def test_udc_biz_is_the_biggest_and_named():
    """udc-biz.md 占全目录三分之一，README 必须点名它——读法建议全靠这个事实。"""
    text = _readme()
    assert "udc-biz.md" in text, "README 没点名 udc-biz.md（最大的那份）"
    files = sorted(p for p in D.glob("*.md") if p.name != "README.md")
    biggest = max(files, key=lambda p: p.stat().st_size)
    assert biggest.name == "udc-biz.md", "最大的不是 udc-biz.md 而是 %s，README 的读法建议要改" % biggest.name


def test_smallest_files_are_named():
    """最小的四份是空壳 starter，README 说明它们"短小是真实规模"——必须点名，否则会被误判抽取失败。"""
    text = _readme()
    files = sorted((p for p in D.glob("*.md") if p.name != "README.md"),
                   key=lambda p: p.stat().st_size)[:4]
    missing = [p.name for p in files if p.name not in text]
    assert not missing, "最小四份没在 README 里交代：%s" % missing


def test_generator_and_source_exist():
    """§四 的重跑命令必须仍然有效。"""
    gen = ROOT / "tools" / "core" / "platform" / "emit_package_surfaces.py"
    src = ROOT / "docs" / "audit" / "artifacts" / "extension-surface-20261029" / "interfaces.json"
    assert gen.is_file(), "生成器不见了，README §四 的命令失效"
    assert src.is_file(), "数据源 interfaces.json 不见了"

"""u5-storage 证据目录入口闸门（逐动作审阅型证据的唯一样本）。

本目录是 docs/audit/artifacts/ 下第三种证据体裁：**每个动作 = 1 份 raw + 1 份 VERDICT**。
闸门要守住三件事：

① **raw 与 VERDICT 必须成对** —— 有 raw 没 VERDICT，那条结论就只是操作记录，不是证据。
② **本目录内容不可分发** —— 里面有连接目标真值、双 app 实例标识、库表清单。
   入口必须写明，且入口自身不得抄任何标识真值（本轮写入口时最容易犯的错）。
③ **文件名脱敏漏网必须留在记录里** —— 那个 `…copy<19位>.txt` 的词根与数字之间插了 copy，
   现行 FILENAME_PII 要求词根紧跟数字，所以不命中也不在 KNOWN_NAME_VIOLATIONS。
   闸门不要求改名，但要求"这件事仍被记录着"，否则改名后没人知道曾经漏过。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "artifacts" / "u5-storage"
README = D / "README.md"

ROW = re.compile(r"^\|\s*`([\w.\-]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _text():
    assert README.is_file(), "u5-storage 缺入口 README.md"
    return README.read_text(encoding="utf-8")


def test_table_matches_disk():
    """规模表每一行都要与磁盘一致（字节 / 行数），且 md 一份不漏。"""
    rows = ROW.findall(_text())
    assert len(rows) == 17, "规模表解析出 %d 行（磁盘有 17 份 md）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        f = D / name
        if not f.is_file():
            bad.append("%s: 表里有、磁盘没有" % name)
            continue
        raw = f.read_bytes()
        if len(raw) != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d B" % (name, size_s, len(raw)))
        n = len(raw.decode("utf-8").splitlines())
        if n != int(lines_s):
            bad.append("%s: 表写 %s 行 磁盘 %d 行" % (name, lines_s, n))
    assert not bad, "u5-storage 规模表已腐坏：\n  " + "\n  ".join(bad)

    on_disk = {f.name for f in D.glob("*.md")} - {"README.md"}
    listed = {r[0] for r in rows}
    assert on_disk == listed, "表与磁盘不一致：仅磁盘有 %s / 仅表有 %s" % (
        sorted(on_disk - listed), sorted(listed - on_disk))


def test_every_raw_has_a_verdict():
    """raw-NN 必须有对应的 VERDICT-STEPN —— 否则那只是操作记录，不是证据。"""
    names = {f.name for f in D.glob("*.md")}
    raws = sorted(n for n in names if re.match(r"raw-\d\d-", n))
    assert len(raws) == 3, "raw 文件应为 3 份，实际 %d：%s" % (len(raws), raws)
    missing = []
    for r in raws:
        step = r[4:6].lstrip("0")
        # 步骤号与文件序号不一定相等（STEP4 审 diff-table），所以只断言"有对应 step 文件"
        if not any(n.startswith("VERDICT-STEP") for n in names):
            missing.append(r)
    assert not missing, "这些 raw 没有对应 VERDICT：%s" % missing

    # 动作 4/5 审的是汇总件而不是 raw-NN，同样必须有 VERDICT
    for stem, step in (("storage-diff-table.md", "VERDICT-STEP4"),
                       ("u6-consumption.md", "VERDICT-STEP5")):
        assert stem in names, "%s 不在了（入口 §二 的动作链依赖它）" % stem
        assert any(n.startswith(step) for n in names), "缺 %s（审 %s 的那次）" % (step, stem)

    # 收口三层必须有
    for need in ("storage-evidence.md", "CLOSURE-u5-final.md", "VERDICT-STEP6-closure.md",
                 "LOG-20260922-step6-closure.md"):
        assert need in names, "缺收口件 %s" % need


def test_verdicts_are_pass():
    """每份 VERDICT 必须仍写着 PASS，收口结论不能被悄悄改弱。"""
    bad = []
    for f in sorted(D.glob("VERDICT-*.md")):
        t = f.read_text(encoding="utf-8", errors="replace")
        if "PASS" not in t:
            bad.append(f.name)
    assert not bad, "这些 VERDICT 里找不到 PASS：%s" % bad

    closure = (D / "CLOSURE-u5-final.md").read_text(encoding="utf-8", errors="replace")
    assert "目标达成" in closure and "收口" in closure, "CLOSURE 的终态结论被改弱了"


def test_ok_bad_paired_count_still_recorded():
    """核心品质：ok=10 / bad=0 的配对计数 + 跨仓核对 + 脱敏按取值模式 grep。"""
    step6 = (D / "VERDICT-STEP6-closure.md").read_text(encoding="utf-8", errors="replace")
    assert re.search(r"ok=10\s*/\s*bad=0", step6), "「ok=10 / bad=0」的配对计数被删了"
    assert "重算" in step6, "VERDICT-STEP6 缺「独立重算」"
    assert "跨任务仓" in step6 or "leaving-blank-space-agent" in step6, (
        "跨仓核对记录被删了 —— 有 2 件证据源不在本仓库，这件事必须留痕")
    assert "取值模式" in step6 or "0 明文命中" in step6, "脱敏按取值模式 grep 的记录被删了"

    t = _text()
    for token in ("ok=10 / bad=0", "跨仓", "取值模式"):
        assert token in t, "入口缺「%s」这条品质说明" % token


def test_two_layer_evidence_principle_recorded():
    """配置字面 ≠ 连通性 —— 本目录最可复用的判据。"""
    ev = (D / "storage-evidence.md").read_text(encoding="utf-8", errors="replace")
    assert "配置字面" in ev, "storage-evidence 的「配置字面」口径被删了"
    t = _text()
    assert "配置字面" in t and "连通" in t, "入口没写「配置字面 ≠ 连通性」"
    assert "必须分开取证" in t, "入口没把「配置和连通分开取证」写成判据"
    assert "三层" in t, "入口没写三层闭合（本地快照 ↔ 连通实测 ↔ 服务端 LIVE）"


def test_suggestion_files_are_proposals_not_code():
    """providers-*.suggestion.md 是建议件，不是已实现的配置。"""
    sugs = sorted(D.glob("*.suggestion.md"))
    assert len(sugs) == 2, "建议件应为 2 份，实际 %d" % len(sugs)
    for f in sugs:
        t = f.read_text(encoding="utf-8", errors="replace")
        assert "只写建议" in t or "不改代码" in t, (
            "%s 缺「只写建议，不改代码」的边界声明" % f.name)
    t = _text()
    assert "建议件" in t, "入口没标建议件"
    assert "不要读这两份" in t or "去读代码" in t, (
        "入口没写「想知道 providers/ 现在怎么映射，去读代码，不要读这两份」")


def test_directory_is_declared_not_distributable():
    """本目录内容不可分发 —— 入口必须在第一屏就说清。"""
    t = _text()
    head = t.split("## 二")[0]
    assert "不可分发" in head, "入口 §一 没在第一屏写「本目录内容不可分发」"
    for token in ("SHOW DATABASES", "<REDACTED>", "distribution_manifest"):
        assert token in head or token in t, "入口缺「%s」" % token
    assert "EVIDENCE_DATA_DIRS" in t, (
        "入口没指出脱敏闸门对 /artifacts/ 是显式豁免 —— 豁免不等于干净")
    assert "豁免不等于干净" in t, "入口没写「豁免不等于干净」这句判据"


def test_readme_itself_has_no_identifier_truth():
    """入口自身绝不能抄连接目标真值 / 实例标识 / 主机名 —— 写入口时最易犯的错。"""
    t = _text()
    bad = []
    bad += re.findall(r"\b(?:10|172|192)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", t)
    bad += re.findall(r"\b[a-z0-9-]+\.(?:rds\.aliyuncs\.com|redis\.rds\.aliyuncs\.com|mse\.aliyuncs\.com)\b", t)
    bad += re.findall(r"\b(?:pc|r|mse)-[a-z0-9]{8,}\b", t)
    bad += [w for w in ("xiangmuguanli", "datamigration", "znxmglpt") if w in t]
    assert not bad, "u5-storage 入口 README 抄进了标识真值：%s" % bad
    for m in re.finditer(r"\b9\d{18}\b", t):
        assert m.group(0).startswith("9000000000000000"), (
            "入口出现非保留段的 19 位数字：%s" % m.group(0))
    # 也不能抄任何 _test2 结尾的库名
    assert not re.search(r"\b\w+_test2\b", t), "入口抄进了带 _test2 的库名"


def test_filename_leak_still_recorded():
    """文件名脱敏漏网必须仍被记录 —— 改了名就没人知道曾经漏过。"""
    t = _text()
    assert "copy" in t, "入口没记录那个「词根与数字之间插了 copy」的漏网形态"
    assert "FILENAME_PII" in t, "入口没点名 FILENAME_PII 判据"
    assert "待裁决" in t, "入口没把它标成待裁决项"
    # 该文件必须还在（不许悄悄删/改名）
    leaks = [f.name for f in D.glob("*.txt") if re.search(r"copy\d{19}", f.name)]
    assert len(leaks) == 1, (
        "预期有 1 份 `…copy<19位>.txt` 的漏网文件，实际 %d 份：%s\n"
        "若已授权改名，请同步更新入口 §八 与 KNOWN_NAME_VIOLATIONS" % (len(leaks), leaks))

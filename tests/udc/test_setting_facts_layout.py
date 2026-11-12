"""core/facts/udc/setting/ 的入口 README 必须与磁盘一致，且两份「父子两协议」文件必须被点名。

背景：这是设置域的事实层（15 份 / 10 个 tab 子目录），和
`docs/operation-contracts/udc/setting/`（契约层）同名极易走错。2026-11-07 前没有入口。

最贵的知识是两份文件 §零 都写着同一句「最大发现：父子两级用两种协议」——
`attribute-set`（父 REST / 子 GraphQL）与 `scalability`（同构）。
原文记录：最初以为字段也走 REST，**4 种变体全部静默失败**（`BOOT_0000` 但零写入）。
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "core" / "facts" / "udc" / "setting"

ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 core/facts/udc/setting/README.md（设置域事实层入口）"
    return p.read_text(encoding="utf-8")


def _all_md():
    return sorted(p for p in D.rglob("*.md") if p.name != "README.md")


def test_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 17, "规模表只解析出 %d 行（应有 17 行）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        size = p.stat().st_size
        nlines = p.read_bytes().count(bytes([10]))
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, size))
        if nlines != int(lines_s.replace(",", "")):
            bad.append("%s: 表写 %s 行 磁盘 %d" % (name, lines_s, nlines))
    assert not bad, "设置域规模表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches_disk():
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「合计 N 份 / X B」声明"
    claimed_n, claimed = int(m.group(1)), int(m.group(2).replace(",", ""))
    files = _all_md()
    assert len(files) == claimed_n, "声称 %d 份，磁盘 %d 份" % (claimed_n, len(files))
    real = sum(p.stat().st_size for p in files)
    assert real == claimed, "声称合计 %d B，磁盘实算 %d B" % (claimed, real)


def test_every_fact_is_named():
    text = _readme()
    missing = [p.name for p in _all_md() if p.name not in text]
    assert not missing, "这些事实格没在入口 README 里出现：%s" % missing


def test_two_protocol_pitfall_still_documented():
    """两份文件 §零 的「父子两级用两种协议」是本域最贵的知识，原文必须还在。"""
    for name, needle in (("attribute-set/create.md", "父子两级用"),
                         ("scalability/create.md", "父子两级用")):
        p = D / name
        assert p.is_file(), "%s 不见了" % name
        assert needle in p.read_text(encoding="utf-8", errors="replace"), \
            "%s 的「父子两级用两种协议」段落被删了——这是本域最贵的教训" % name


def test_parameter_misspelling_not_fixed():
    """parameter 的平台拼写错是真实行为：Definition 少一个 i。有人"顺手修正"会让请求失败。"""
    p = D / "parameter" / "create.md"
    txt = p.read_text(encoding="utf-8", errors="replace")
    assert "udcCtpParameterDefinitonPost" in txt, \
        "parameter/create.md 里的拼写错不见了——照抄错的才对，不能改成 Definition"
    assert "udcCtpParameterDefinitionPost" not in txt, \
        "有人把拼写错改成了 Definition——平台真实 op 名少一个 i，改了请求会失败"


def test_contract_layer_sibling_is_declared():
    """README 必须点明与契约层同名目录的分工，否则下一个人会走错。"""
    text = _readme()
    assert "docs/operation-contracts/udc/setting/" in text, \
        "README 没说明与契约层的分工——两个同名目录极易走错"

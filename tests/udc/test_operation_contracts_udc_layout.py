"""docs/operation-contracts/udc/ 的入口 README 必须与磁盘一致。

这一层此前零入口（只有 2026-10-18 的三域总览），14 个子域里 11 个靠本 README 导航。

最贵的一条是 §二：9 份同名 `registry-entries.md` 全写着「供 UDC-MERGE 照抄」，
读者极易误以为还没做。实测 UDC-MERGE 早已执行——所以入口把「128 条契约 / 提出 42 /
已落库 37 / 剩 5 条各有原因」写成了表；本测试守的就是这几个数不许腐坏。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([a-z-]+)/`\s*\|\s*(\d+)\s*\|\s*([\d,]+)\s*\|\s*(✅|❌)\s*`?([^|]*)\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 docs/operation-contracts/udc/README.md"
    return p.read_text(encoding="utf-8")


def _doms():
    return sorted(d for d in D.iterdir() if d.is_dir())


def test_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 14, "规模表解析出 %d 行（应有 14 个子域）" % len(rows)
    bad = []
    for name, n_s, size_s, mark, _ in rows:
        d = D / name
        if not d.is_dir():
            bad.append("%s/: 表里登记了但目录不存在" % name)
            continue
        files = sorted(f for f in d.iterdir() if f.suffix == ".md")
        size = sum(f.stat().st_size for f in files)
        if len(files) != int(n_s):
            bad.append("%s/: 表写 %s 份 磁盘 %d 份" % (name, n_s, len(files)))
        if size != int(size_s.replace(",", "")):
            bad.append("%s/: 表写 %s B 磁盘 %d B" % (name, size_s, size))
    assert not bad, "子域规模表已腐坏：\n  " + "\n  ".join(bad)


def test_total_equals_row_sum():
    """合计必须等于 14 行之和 —— 这条此前没有，于是逐行全对、合计却错了。

    第 68 轮实测：14 行全对（顶层含 README），但合计写「14 个子域 / 1,049,082 B」。
    那个数用的是**第三种口径**：各子域顶层**不含** README（67 份 / 1,029,907 B）
    **加上**顶层 `C-GROUP-OVERVIEW-20261018.md`（19,176 B）= 1,049,083 B。

    ⇒ 逐行闸门抓不到它，因为逐行确实是对的。
      合计行必须单独断言 —— 它是"第三种算法"最容易被塞进去的地方。
    """
    t = _readme()
    rows = ROW.findall(t)
    sum_n = sum(int(r[1]) for r in rows)
    sum_b = sum(int(r[2].replace(",", "")) for r in rows)
    m = re.search(r"合计 \*\*14 个子域 / ([\d,]+) 份 / ([\d,]+) B\*\*", t)
    assert m, "缺「合计 **14 个子域 / N 份 / M B**」这一行（必须同时给份数和字节）"
    tot_n = int(m.group(1).replace(",", ""))
    tot_b = int(m.group(2).replace(",", ""))
    assert (tot_n, tot_b) == (sum_n, sum_b), (
        "合计与逐行之和不符：合计 %s 份 / %s B，逐行和 %d 份 / %s B。\n"
        "合计行是「第三种口径」最容易被塞进去的地方 —— 必须与逐行同口径（顶层含 README）。"
        % (format(tot_n, ","), format(tot_b, ","), sum_n, format(sum_b, ",")))


def test_scope_is_declared():
    """口径说明必须在：本表顶层含 README，与 core/facts/udc 的递归口径不同。"""
    t = _readme()
    assert "含该子域自己的 `README.md`" in t, "缺「含该子域自己的 README.md」口径说明"
    assert "不递归" in t, "缺「不递归子目录」口径说明"
    assert "core/facts/udc/README.md" in t, (
        "缺与 core/facts/udc/README.md 的交叉对照 —— 同一个 microflow/ 在那边是 25 份（递归），"
        "在这里是 14 份（顶层），不写明读者会以为其中一个错了")
    assert "250,405" in t and "277,632" in t, (
        "交叉对照表必须同时给出两个数（14/250,405 顶层 vs 25/277,632 递归）")


def test_entry_marker_matches_disk():
    """✅/❌ 必须与「该域有无 README.md」相符——否则读者会以为有入口而去翻，或反之。"""
    bad = []
    for name, _, _, mark, _ in ROW.findall(_readme()):
        has = (D / name / "README.md").is_file()
        if has != (mark == "✅"):
            bad.append("%s/: 表标 %s 但磁盘 %s README.md" % (
                name, mark, "有" if has else "无"))
    assert not bad, "入口标记与磁盘不符：\n  " + "\n  ".join(bad)


def test_all_domains_listed():
    text = _readme()
    missing = [d.name for d in _doms() if "`%s/`" % d.name not in text]
    assert not missing, "这些子域没在入口 README 里出现：%s" % missing


def test_registry_numbers_are_real():
    """§二的三个数（128 / 42 / 37）是本层最容易腐坏的地方——registry.py 会继续长。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    landed = set(re.findall(r'"(udc\.[a-z0-9_.]+)"', reg))
    text = _readme()

    m = re.search(r"现有契约条数 \| \*\*(\d+)\*\*", text)
    assert m, "README §二 找不到「现有契约条数 | **N**」"
    claimed = int(m.group(1))
    # registry.py 头部注释里记录了照抄批次，条数以字符串常量去重数为准
    assert claimed >= len(landed) * 0.95, (
        "README 声称 registry.py 有 %d 条契约，但实测至少 %d 个唯一 operation_id"
        % (claimed, len(landed)))

    proposed = 0
    hit = 0
    for d in _doms():
        f = d / "registry-entries.md"
        if not f.is_file():
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        oids = set(re.findall(r'["\']?operation_id["\']?\s*[=:]\s*["\']([a-z0-9_.]+)["\']', t))
        if not oids:
            oids = set(re.findall(r"`(udc\.[a-z0-9_.]+)`", t))
        proposed += len(oids)
        hit += len([o for o in oids if o in landed])

    mp = re.search(r"共提出的 operation_id \| \*\*(\d+)\*\*", text)
    mh = re.search(r"其中\*\*已在 registry.py 中\*\* \| \*\*(\d+)\*\*", text)
    assert mp and mh, "README §二 缺少「提出 N 条 / 已落库 M 条」声明"
    assert int(mp.group(1)) == proposed, (
        "README 声称提出 %s 条，实测 %d 条" % (mp.group(1), proposed))
    assert int(mh.group(1)) == hit, (
        "README 声称已落库 %s 条，实测 %d 条" % (mh.group(1), hit))


def test_merge_already_done_is_declared():
    """必须点明「UDC-MERGE 已执行」，否则读者会把这 9 份当待办。"""
    text = _readme()
    assert "UDC-MERGE 已经执行过了" in text, (
        "README 没说清 UDC-MERGE 已执行——9 份 registry-entries.md 会被误读成待办事项")
    for f in ("registry-entries.md", "components/platform_operations/registry.py"):
        assert f in text, "README 没提到 %s" % f


def test_unnamed_gap_documented():
    """5 条未落库中，只有 2 条是「无注记且名字对不上」的真缺口，必须点名。"""
    text = _readme()
    for oid in ("udc.applog.select_app_data_by_id",
                "udc.page.check_exists",
                "udc.page.select_host_only_pages"):
        assert oid in text, "README §二 没登记未落库条目 %s" % oid
    assert "udc.page_info.check_exists" in text, (
        "README 没指出 registry.py 里实际叫 udc.page_info.check_exists——名字对不上正是缺口所在")

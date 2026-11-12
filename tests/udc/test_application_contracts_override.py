"""`docs/operation-contracts/udc/application/` 的更正索引闸门。

为什么单独一条：
本目录 7 份契约里只有 1 份（`udc-app-online-contract.md`，784 行）带 8 处更正，
但**最贵那条是把「安全实现」记成了「数据质量风险」** ——
`ImportDelegateColi.saveAs` 的 catch 块里 `log.error` 紧接着 `BootException.throwIt`，
且 `@Transactional(rollbackFor={Exception.class})` + 调用方无 try/catch ⇒ 异常重抛、事务回滚。
原判断说它「吞异常、静默降级」，照着去"修"会去修一个不需要修的地方，
而真正的静默失败点反而放过。

另外两条同族的：③「3 处直接调用」是**只做符号 grep** 得出的（漏掉全程不出现方法名的纯间接路径）
—— 与 column-discovery「查错名字的 0 命中」是同一个病；②「撞门」被当成「被拦」。

守五件事：
1. 含更正标记的契约必须在 §〇 更正表里被点名。
2. 声明「8 处」必须与磁盘实测一致。
3. 五条高价更正必须在表里（吞异常 / 撞门≠被拦 / 3 处 / 9→7 / 草稿面结构不存在）。
4. 三条贯穿性错因必须成表。
5. 「我判错」必须留痕，且不许被整理成"已更正"。

⚠️ 本目录多份被代码与测试按固定路径读取（registry 条目字面量、契约层布局测试），
   本闸门**只读不写**，不校验字节数（字节数由 `test_operation_contracts_udc_layout` 守）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
D = ROOT / "docs" / "operation-contracts" / "udc" / "application"
README = D / "README.md"
CORRECTION = re.compile(r"推翻|作废|纠正|撤回|更正|超额")


def _readme() -> str:
    assert README.is_file(), "application 契约目录缺入口 README.md"
    return README.read_text(encoding="utf-8")


def _bodies():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def _correction_counts():
    return {f.name: len(CORRECTION.findall(f.read_text(encoding="utf-8", errors="replace")))
            for f in _bodies()}


def _override_section() -> str:
    """截出 §〇（更正表所在节）。只看这一节，避免正文别处提到文件名造成假通过。"""
    t = _readme()
    m = re.search(r"^## 〇.*?$(.*?)^## 一、", t, re.S | re.M)
    assert m, "入口缺「§〇 更正表」章节（或 §一 缺失导致无法截断）"
    return m.group(1)


def _name_is_mentioned(stem: str, text: str) -> bool:
    parts = re.split(r"[-.]", stem)
    return any("-".join(parts[:k]) in text or ".".join(parts[:k]) in text
               for k in range(1, len(parts) + 1))


def test_files_with_corrections_are_named():
    section = _override_section()
    nz = {k: v for k, v in _correction_counts().items() if v}
    unresolved = [n for n in nz if not _name_is_mentioned(Path(n).stem, section)]
    assert not unresolved, (
        "这些契约含更正标记但入口更正表没点名，读者会引来已撤回的结论：\n  "
        + "\n  ".join(sorted(unresolved)))


def test_declared_count_matches_disk():
    t = _readme()
    m = re.search(r"带\s*\*\*(\d+)\s*处\*\*更正", t)
    assert m, "入口缺「带 N 处更正」这句可核对的声明"
    claimed = int(m.group(1))
    real = sum(_correction_counts().values())
    assert real == claimed, "声称 %d 处，实测 %d 处（明细 %s）" % (
        claimed, real, {k: v for k, v in _correction_counts().items() if v})


def test_most_expensive_correction_present():
    """把安全实现记成风险这条必须在表里 —— 这是本目录最贵的一条。"""
    section = _override_section()
    must = [
        ("吞异常", "① 原判断「吞异常 / 静默降级」"),
        ("BootException.throwIt", "① 真实现是重新抛出（BOOT_3000）"),
        ("回滚", "① 事务回滚 ⇒ 不是静默降级"),
    ]
    missing = [why for needle, why in must if needle not in section]
    assert not missing, "更正表缺「吞异常」那条的要点：%s" % missing


def test_other_high_price_corrections_present():
    section = _override_section()
    must = [
        ("撞门 ≠ 被拦", "② 调用 vs 生效"),
        ("符号 grep", "③ 「3 处直接调用」的错因：只做符号 grep"),
        ("9", "④ 9 → 7 两个口径"),
        ("7", "④ 9 → 7 两个口径"),
        ("结构上不存在", "⑤ 草稿面这条链不是「未定位」而是不存在"),
    ]
    missing = [why for needle, why in must if needle not in section]
    assert not missing, "更正表缺这些高价更正：%s" % missing


def test_error_patterns_table_present():
    section = _override_section()
    must = [
        ("搜不到 ≠ 不存在", "符号 grep 的边界"),
        ("调用", "「调用」当「生效」"),
        ("口径", "口径不随数字走"),
    ]
    missing = [why for needle, why in must if needle not in section]
    assert not missing, "更正表缺这些贯穿性错因：%s" % missing


def test_self_blame_is_kept():
    """「我判错」留痕不许被整理成一句"已更正"。"""
    t = _readme()
    assert "我判错" in t, "入口没保留「我判错」留痕"
    assert "整理成一句" in t or "不要把这些" in t, (
        "入口没说清「不要把『我判错』整理成一句『已更正』」——"
        "写『已更正』等于删掉了『下次要用什么手段查』")


def test_gate_bites_on_mutation():
    """变异用例：抹掉 §〇 里的文件名后，第 1 条断言必须变红。"""
    nz = {k: v for k, v in _correction_counts().items() if v}
    assert nz, "磁盘上已无含更正标记的契约，本闸门无对象，应复核是否该删"
    assert not [n for n in nz if not _name_is_mentioned(Path(n).stem, _override_section())], (
        "前提不成立：正常 README 本应全部点名")

    gutted = _override_section()
    for name in nz:
        stem = Path(name).stem
        gutted = gutted.replace(name, "").replace(stem, "")
        parts = re.split(r"[-.]", stem)
        for k in sorted(range(1, len(parts) + 1), reverse=True):
            gutted = gutted.replace("-".join(parts[:k]), "").replace(".".join(parts[:k]), "")
    still = [n for n in nz if _name_is_mentioned(Path(n).stem, gutted)]
    assert not still, (
        "变异用例失效：抹掉文件名后仍有 %d 个被判「已点名」（%s）—— 断言会假通过"
        % (len(still), still))

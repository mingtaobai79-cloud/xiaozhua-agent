"""两份 ARCHITECTURE 必须互引、不互抄、且各自保留分工头注。

## 为什么需要这条闸门

`docs/ARCHITECTURE.md`（仓库实现视图，10,327 B / 207 行）与
`docs/capability/ARCHITECTURE.md`（目标架构，16,843 B / 228 行）是**两份不同的东西**，
P2 的要求原话是「继续保持互引、不互抄」。

第 70 轮实测：

- 互引：**都在**（各引用对方 1 次）✓
- 不互抄：**23 段落各、完全相同 0、高相似 0** ✓

也就是说，**当前状态是对的** —— 但这三条**零守卫**。
`test_docs_root_layout.py` 和 `test_capability_docs_layout.py` 只是在
「必需文件清单」里列了 `ARCHITECTURE.md`，从不检查它们之间的关系。

⇒ 失败模式：某次重构把 capability 侧的一段整段复制到 docs 侧「方便读者」，
   两份文档开始分叉、然后同步、然后其中一份变成另一份的旧副本。
   而两份都还在、都在必需清单里 —— 所有闸门全绿。

⇒ 判据：**「有闸门」是文件级事实，「关系正确」是关系级事实**。
   后者必须单独断言，前者不会替你检查它。

## 「不互抄」怎么判定

按空行切段落，只看 ≥100 字符的段落（短句撞车是正常的，
比如「本文是时点记录」这种通用句不该报红）。
两两比对：完全相同 → 红；相似度 >0.90 → 红。

第 70 轮实测相似度最高的一条 <0.85，所以 0.90 这个阈值留了余量，
不会因为一次无关的小改就误报。
"""
import difflib
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "docs" / "ARCHITECTURE.md"
GOAL = ROOT / "docs" / "capability" / "ARCHITECTURE.md"
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

SIM_LIMIT = 0.90
MIN_PARA = 100


def _paras(p):
    """按空行 / `---` 切段落，只保留 ≥MIN_PARA 字符的。"""
    out, buf = [], []
    for line in p.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if s == "" or s == "---":
            if buf:
                out.append("\n".join(buf))
                buf = []
        else:
            buf.append(s)
    if buf:
        out.append("\n".join(buf))
    return [x for x in out if len(x) >= MIN_PARA]


def test_mutual_reference():
    """两份必须互相引用 —— 只引一边，读者会以为另一边不存在。"""
    impl = IMPL.read_text(encoding="utf-8")
    goal = GOAL.read_text(encoding="utf-8")
    assert "capability/ARCHITECTURE.md" in impl, (
        "docs/ARCHITECTURE.md 没指向 docs/capability/ARCHITECTURE.md —— "
        "读者会以为实现视图就是全部")
    assert "../ARCHITECTURE.md" in goal, (
        "docs/capability/ARCHITECTURE.md 没指向 ../ARCHITECTURE.md —— "
        "读者会以为目标架构就是仓库现状")


def test_no_paragraph_is_copied():
    """不互抄：≥100 字符的段落不许相同、不许高度相似。"""
    a, b = _paras(IMPL), _paras(GOAL)
    assert len(a) >= 10 and len(b) >= 10, (
        "段落数异常（impl %d / goal %d）—— 解析规则或文件结构变了" % (len(a), len(b)))
    bad = []
    for x in a:
        for y in b:
            if x == y:
                bad.append("完全相同：%s…" % x[:80].replace("\n", " "))
                continue
            # 长度差太大不可能高相似，先剪枝
            if abs(len(x) - len(y)) > 0.35 * max(len(x), len(y)):
                continue
            r = difflib.SequenceMatcher(None, x, y).ratio()
            if r > SIM_LIMIT:
                bad.append("相似度 %.2f：A=%s… / B=%s…" % (r, x[:60].replace("\n", " "),
                                                          y[:60].replace("\n", " ")))
    assert not bad, (
        "两份 ARCHITECTURE 开始互抄了（P2 要求「互引、不互抄」）：\n  "
        + "\n  ".join(bad[:5])
        + "\n\n修法：删掉重复那段，改成一句指针指向对方。"
          "两份文档的职责不同 —— 一份讲「盘上现在有什么」，一份讲「目标是什么」。"
          "同一段话不可能同时回答这两个问题。")


def test_each_keeps_its_division_note():
    """分工头注必须各自保留 —— 这是读者分清两份文档的唯一线索。"""
    impl = IMPL.read_text(encoding="utf-8")[:1200]
    goal = GOAL.read_text(encoding="utf-8")[:1200]
    assert "仓库实现" in impl, "docs/ARCHITECTURE.md 头注丢了「仓库实现」定位"
    assert "目标架构" in impl, "docs/ARCHITECTURE.md 头注丢了「目标架构见 …」的指针"
    assert "目标架构" in goal, "capability/ARCHITECTURE.md 头注丢了「目标架构」定位"
    assert "仓库实现" in goal or "../ARCHITECTURE.md" in goal, (
        "capability/ARCHITECTURE.md 头注丢了「仓库实现视图见 ../ARCHITECTURE.md」")


def test_impl_side_marks_status_tags():
    """docs 侧必须保留【现状】/【目标】标记 —— 没有它，读者分不清哪段已实现。

    这是 docs/ARCHITECTURE.md 头注里自己承诺的：
    「不得把【目标】当作已实现的系统结构」。
    """
    impl = IMPL.read_text(encoding="utf-8")
    assert "【现状】" in impl and "【目标】" in impl, (
        "docs/ARCHITECTURE.md 缺【现状】/【目标】标记 —— "
        "头注承诺了这两个标记，正文里没有就等于没承诺")
    assert re.search(r"不得把【目标】当作已实现", impl), (
        "头注那条禁令被删了 —— 它是这份文档最重要的读法说明")

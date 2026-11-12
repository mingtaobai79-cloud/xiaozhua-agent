"""文档里指向仓库内资产的路径，必须要么存在，要么标明它去哪了。

为什么需要它：
`76d6305e`（建立 `_attic_pending/` 双桶）把 `tools/core/` 下 63 个审计脚本移走后，
**没有任何一份文档跟着改**。结果 18 种路径 / 39 处引用全部指空，
而其中 34 种**只是前缀搬了家**（`tools/core/x.py` → `tools/core/decompile/x.py`），
真实文件一直在，只是文档还写着老地址。

这类死引用的危害不是「点不开」，而是：
**读者照着文档敲 `python tools/core/xxx.py` 得到 "No such file"，会以为这项能力不存在了。**
（同 `column-discovery` 的「查错名字的 0 命中」——错名字的失败和真的没有，输出一模一样。）

判据（三条，缺一不可）：
1. 反引号里的 `tools|core|components|tests/**/*.py` 路径必须真实存在；
2. 不存在时，**同一行**必须带「已移入 `_attic…`」标记（说明去哪了，而不是装作还在）；
3. `docs/ledger/`（历史日志）与 `docs/audit/artifacts/`（运行时数据根）**不扫** ——
   前者是留痕，后者里的路径是当时会话的现场记录，改了就是伪造证据。

不做的事：
- 不自动修。改路径需要判断"是不是同一个文件"，本闸门只负责**让漏网的变红**。
- 不扫表格行 —— 表格列数有别的闸门守，自动加字会打乱列宽。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)

# 仓库内 .py 的反引号引用
REF = re.compile(r"`((?:tools|core|components|tests)/[\w/\-\.]+\.py)`")
# 「已移入收容桶」的标记：同一行出现即可
MOVED_MARK = re.compile(r"已移入 `_attic")
# 描述"删除/清除某文件"的叙述行不算死引用
DELETION_NARRATIVE = re.compile(r"清除|删除|移除|孤儿")

SKIP_DIRS = ("/ledger/", "/artifacts/", "/node_modules/")
# 本文件自身会写出示例路径
SKIP_FILES = ("docs/plans/doc-consolidation-progress.md",)


def _docs():
    for f in sorted(ROOT.joinpath("docs").rglob("*.md")):
        rel = f.relative_to(ROOT).as_posix()
        if any(s in rel for s in SKIP_DIRS) or rel in SKIP_FILES:
            continue
        yield rel, f


def _dead_refs():
    """返回 (rel, lineno, path, marked) —— 只收不存在且未标记的。"""
    out, marked = [], []
    for rel, f in _docs():
        text = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            for m in REF.finditer(line):
                p = m.group(1)
                if (ROOT / p).is_file():
                    continue
                if DELETION_NARRATIVE.search(line):
                    continue
                if MOVED_MARK.search(line):
                    marked.append((rel, i, p))
                else:
                    out.append((rel, i, p))
    return out, marked


def test_no_unmarked_dead_py_refs_in_docs():
    """核心断言：不存在且未标「已移入」的 .py 引用 = 0。"""
    dead, marked = _dead_refs()
    assert not dead, (
        "文档引用了仓库内不存在的 .py，且没说明它去哪了（读者敲这条命令会 404）：\n  "
        + "\n  ".join("%s L%d: %s" % d for d in dead)
        + "\n\n修法二选一：① 若同名文件搬到了别处，改成真实路径；"
          "② 若被 `_attic_pending/` 收容，在该路径后加「（**已移入 `_attic_.../x.py`**）」。")


def test_the_2010_move_is_actually_recorded():
    """反退化：`_attic_pending/` 收容的脚本，必须仍然可寻 —— 两种写法都算。

    第 74 轮修正口径：原来只统计「路径不存在 + 标了去向」的引用，
    但**把路径直接改成收容桶内的真实路径**是更强的处置
    （读者敲命令能跑），那种引用因为「存在」而从统计里消失了 ——
    于是闸门在处置变好时反而变红。

    ⇒ 判据：**「可寻」有两种写法，都要认**：
      ① 老路径 + 「（已移入 `_attic_pending/...`）」标注
      ② 直接写收容桶内的真实路径
    """
    _, marked = _dead_refs()
    # ② 直接指向收容桶真实路径的引用
    direct = []
    for rel, f in _docs():
        text = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if "_attic_pending/" in line:
                direct.append((rel, i, "_attic_pending/"))
    total = len(marked) + len(direct)
    assert total >= 15, (
        "可寻的收容引用只有 %d 处（标注 %d + 直指真实路径 %d），少于应有的 15+ 处 —— "
        "有人把去向标记清掉了，或者把真实路径改回了老路径？"
        % (total, len(marked), len(direct)))
    assert direct, (
        "没有任何引用直接指向 `_attic_pending/` 内的真实路径 —— "
        "第 74 轮把 b6_*.py 的 17 处从「老路径+标注」改成了「收容桶真实路径」，"
        "这个处置比标注更强，不该退回")


def test_real_prefix_moves_use_real_paths_not_attic_marks():
    """真实文件仍在仓库里（只是换了子目录）时，必须给真实路径，不能标「已移入」。

    `tools/core/x.py` → `tools/core/decompile/x.py` 这类搬迁，
    标「已移入收容桶」是**错的** —— 那会让人以为能力已废弃。
    """
    by_name = {}
    for p in ROOT.rglob("*.py"):
        if "_attic" in p.parts or ".venv" in p.parts or ".git" in p.parts:
            continue
        by_name.setdefault(p.name, []).append(p.relative_to(ROOT).as_posix())
    dead, _ = _dead_refs()
    # 只算「仓库内真实存在且不在收容桶」的同名文件
    wrong = [d for d in dead
             if any("_attic" not in x for x in by_name.get(Path(d[2]).name, []))]
    assert not wrong, (
        "这些路径的文件其实还在仓库里（换了子目录），应当改成真实路径而不是留空引用：\n  "
        + "\n  ".join("%s L%d: %s → 实为 %s"
                      % (d[0], d[1], d[2], by_name[Path(d[2]).name]) for d in wrong))


def test_attic_bucket_exists_in_gitignore_and_has_readme():
    """判据前提：收容桶存在且被 gitignore 排除（否则"已移入"指向一个空目录）。"""
    attic = ROOT / "_attic_pending"
    assert attic.is_dir(), "`_attic_pending/` 不见了 —— 所有「已移入」标记都会指空"
    assert (attic / "README.md").is_file(), "收容桶缺 README（抽离流程 + 台账）—— 标记无据可查"
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="replace")
    assert "_attic_pending" in gi, "收容桶未进 .gitignore —— 它会把 156 MB 拖进仓库"


def test_gate_bites_on_a_reintroduced_dead_ref():
    """变异用例：在一份真实文档里注入一条指空的引用，判据必须识别出来。"""
    rel = "docs/audit/udc-semantics/COMPONENT-RELOCATION.md"
    line = "复跑：`tools/core/this_file_never_existed.py`"
    probe = line + "\n"
    hits = [m.group(1) for m in REF.finditer(probe)
            if not (ROOT / m.group(1)).is_file() and not MOVED_MARK.search(probe)]
    assert hits == ["tools/core/this_file_never_existed.py"], (
        "变异用例失效：注入的死引用没被 REF 抓到（正则写错了？）")
    # 再确认：加了「已移入」标记后应当被豁免
    probe2 = "复跑：`tools/core/this_file_never_existed.py`（**已移入 `_attic_pending/one-off/x.py`**）"
    assert MOVED_MARK.search(probe2), "标记正则没认出「已移入 `_attic」—— 豁免会失效"


# ────────────────────────────────────────────────────────────────
# 第二部分：非 .py 资产（.md / .json / .java / .javap.txt / .jar …）
#
# 第 60 轮补：`e6268556` 把客户场景证据整体迁出到 `<EVIDENCE_ROOT>/xiaozhua-customer-evidence/`
# （131 件 javap + 71 件前端 chunks + 1543 件元数据 dump），
# **同样没有任何文档跟着改** —— 11 种路径 / 13 处全部指空。
# 与 `.py` 那批的区别：这里的文件是真的不在本仓了（迁出是**正确**处置，
# 客户证据不该进分发仓），所以正确修法只有一种：**标注去向**，不能"改回真实路径"。
# ────────────────────────────────────────────────────────────────

ASSET_REF = re.compile(
    r"`((?:docs|core|components|tools|skills|adapters|installer|tests)/"
    r"[\w/\-\.\u4e00-\u9fff]+\.(?:md|json|txt|ya?ml|jar|class|java))`")
# 「已迁出到底稿库」/「已移入收容桶」——两者都表示"不在这了，但知道在哪"
# 三种「不在这里」的正当理由（缺一即死链）：
#   ① 客户证据迁出（迁出是正确处置，只需标去向）
#   ② 进了收容桶（可回退）
#   ③ **计划里写了但从未产出**（必须写明「从未生成」，否则读者以为能拿到）
RELOCATED = re.compile(r"已迁出至|已移入 `_attic|从未生成|从未产出")
# 第 78 轮补：**「已删除」类负引用也有多种中文写法**，只认 `已删除` 会漏。
# 实测：`xiaozhua-udc-custom-extension-engine/SKILL.md` 写的是
#   「⚠ 早先落在这两处的资产**已作废并删除**，不要再去读：`core/facts/udc/extension/` 与
#    `tests/udc/test_udc_extension_asset_layout.py`」
# —— 三个词都不是 `已删除`，扫描器判成死链。这类「告诫读者别去读」的行，
# 恰恰是最该保留的负证据，不能因为写法不同就当成错误。
TOMBSTONED = re.compile(r"已作废|作废并删除|不要再去读|已废弃|已不再存在|已下线")
# 省略号写法（`a/.../b.java`）本身就不可能被解析，单列一条守
ELLIPSIS_PATH = re.compile(r"`[^`]*/\.\.\./[^`]*`")

# 第 74 轮补：**绝对路径形式**此前完全没被扫过。
# `ASSET_REF` 只认 `` `docs/...` `` 这种以目录名开头的反引号路径；
# 而代码块里写的是 `python <XIAOZHUA_AGENT_ROOT>/tools/core/b6_x.py` ——
# 既不在反引号里，也不以目录名开头，于是 27 处死引用一直躺着。
# 实测三种成因，修法相反（同方法论 80）：
#   ① `tools/core/b5_*.py` → 真的搬到了 `tools/audit/`（**改路径**）
#   ② `tools/core/b6_*.py` → 进了 `_attic_pending/legacy-audit/`（**改路径到收容桶**）
#   ③ `docs/audit/frontend/chunks/*.js` → 客户证据迁出（**只能标去向**，不能改回仓库路径）
ABS_REF = re.compile(
    r"D:[/\\]work[/\\]chit[/\\]xiaozhua-agent[/\\]"
    r"([\w/\-\.\u4e00-\u9fff]+\.(?:md|json|txt|ya?ml|jar|class|java|js|py))")


def _asset_dead():
    dead, marked = [], []
    for rel, f in _docs():
        text = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            refs = [m.group(1) for m in ASSET_REF.finditer(line)]
            refs += [m.group(1).replace("\\", "/") for m in ABS_REF.finditer(line)]
            for p in refs:
                if (ROOT / p).exists():
                    continue
                if RELOCATED.search(line) or TOMBSTONED.search(line):
                    marked.append((rel, i, p))
                else:
                    dead.append((rel, i, p))
    return dead, marked


def test_no_unmarked_dead_asset_refs():
    """不存在且未标去向的非 .py 资产引用 = 0。"""
    dead, _ = _asset_dead()
    assert not dead, (
        "文档引用了仓库内不存在的资产，且没说明它去哪了：\n  "
        + "\n  ".join("%s L%d: %s" % d for d in dead)
        + "\n\n客户场景证据已迁出到 `<EVIDENCE_ROOT>/xiaozhua-customer-evidence/`，"
          "正确修法是标「（**客户场景证据，已迁出至 `xiaozhua-customer-evidence/…`**）」——"
          "**不要改回仓库路径**（那些文件不该进分发仓）。")


def test_known_absent_refs_carry_a_reason():
    """反退化：8 处「已迁出」+ 1 处「从未生成」必须留理由。

    迁出本身是对的（客户证据不进分发仓），但**不留去向就等于能力消失**：
    读者看到 `docs/audit/frontend/xxx.md` 在仓库里找不到，会以为这份证据从未存在。
    """
    _, marked = _asset_dead()
    # 实测 8 处（另有多处在表格里没加反引号，本判据只认反引号形式）
    assert len(marked) >= 8, (
        "标了「已迁出至」的引用只有 %d 处（应 ≥8）—— 有人把去向标记删了？"
        "迁出的客户证据就再也找不回来了" % len(marked))


def test_no_ellipsis_paths_in_evidence_refs():
    """引用路径不许写 `/.../`（省略号）。

    第 60 轮实测：`cfr-r31b/.../AppErrorCode.java` 三份文档都这么写，
    人眼看得懂，**机器和读者都点不开**；而真实路径就在
    `cfr-r31b/com/seeyon/udc/exception/AppErrorCode.java`。
    ⇒ 判据：省略号是「我知道大概在哪，但没去查」的记号，不该进证据引用。
    """
    hits = []
    for rel, f in _docs():
        text = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if ELLIPSIS_PATH.search(line) and ("`docs/" in line or "`tools/" in line):
                hits.append((rel, i, line.strip()[:90]))
    assert not hits, ("证据引用里出现 `/.../` 省略号路径（点不开、也不可复现）：\n  "
                      + "\n  ".join("%s L%d: %s" % h for h in hits))


def test_plan_checkbox_x_does_not_mean_reproducible():
    """`frontend-ui-full-extraction.md` 的 `[x]` 只表示「当时做过」。

    第 60 轮实测：S1–S4 的四个中间产物（`module_detail.json` / `symbol_table.json` /
    `symbol_resolver.py` / `page_button_ops.json`）**全库不存在、git 从未入库**，
    而计划里四步都打了 `[x]`。S6 的 `frontend-backend-reconcile.md` 也从未产出
    （只有同名 `.json` 数据在盘）。

    ⇒ 这条守的是「产物落地核对表必须在」，否则下一个人会照着 `[x]` 去找那几个文件。
    """
    p = ROOT / "docs/plans/hermes/plans/frontend-ui-full-extraction.md"
    assert p.is_file(), "计划文件不见了：%s" % p
    t = p.read_text(encoding="utf-8", errors="replace")
    assert "产物落地核对" in t, (
        "计划缺「产物落地核对」表 —— `[x]` 会被读成「现在可复现」，而那四个中间件文件全库不存在")
    assert "只表示「当时做过」" in t, "核对表没写明 `[x]` 的确切含义"
    # 四个中间产物确实不存在（若哪天有人补回来了，这行要改，而不是让表变谎话）
    for name in ("module_detail.json", "symbol_table.json",
                 "symbol_resolver.py", "page_button_ops.json"):
        assert not (ROOT / "docs/audit/udc-semantics" / name).exists(), (
            "%s 现在存在了 —— 核对表需要同步更新（它现在写的是「不存在」）" % name)

# ────────────────────────────────────────────────────────────────
# 第三部分：非 docs 树（core/ components/ skills/ config/）
#
# 第 61 轮补：`docs/` 扫完之后还有一片 —— **facts 与 skills 里的路径**。
# 它们比 docs 更要紧：`core/facts/` 是"事实"，`skills/*/SKILL.md` 是**执行手册**，
# 手册里的路径写错，AI 会照着敲、敲不通、然后以为能力不存在。
# 实测这一片有 12 种 / 34 处，其中最有价值的一条是**测试被删了但事实表还写着它在守**。
# ────────────────────────────────────────────────────────────────

TREES = ("core", "components", "skills", "config")
HAND_WRITTEN = ("/node_modules/", "_attic", "/.venv/")
# 这些理由都能让一条"路径不存在"变成正当：
#   已迁出 / 已移入收容桶 / 从未生成 / 从未入库 / 已删除
EXCUSED = re.compile(r"已迁出至|已移入 `_attic|从未生成|从未产出|从未入库|never committed|was never|已删|已于 `?\w{6,8}`? 删")
# 示例占位符不是引用（`tools/core/x.py`、`tests/udc/xxx.py`）
PLACEHOLDER = re.compile(r"/(?:x|xxx|foo|bar)\.py$")


def _tree_docs():
    for tree in TREES:
        base = ROOT / tree
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*.md")):
            rel = f.relative_to(ROOT).as_posix()
            if any(s in rel for s in HAND_WRITTEN):
                continue
            yield rel, f


def _tree_dead():
    dead = []
    for rel, f in _tree_docs():
        text = f.read_text(encoding="utf-8", errors="replace")
        # ★ 豁免标记常常写在引用**前一行**（「⚠ 以下资产已作废，不要再去读：」+ 下一行才列路径）。
        #   只判当前行会把最该保留的负证据判成死链 —— 实测
        #   `xiaozhua-udc-custom-extension-engine/SKILL.md` L328 是标记、L329 才是路径。
        #   所以带一个「上一行的标记是否仍有效」的上下文（空行打断）。
        excuse_above = False
        for i, line in enumerate(text.splitlines(), 1):
            marked_here = bool(EXCUSED.search(line) or TOMBSTONED.search(line))
            if marked_here or excuse_above:
                if marked_here or line.strip():
                    excuse_above = marked_here
                    continue
            excuse_above = False
            for m in REF.finditer(line):
                p = m.group(1)
                if (ROOT / p).exists() or PLACEHOLDER.search(p):
                    continue
                dead.append((rel, i, p))
    return dead


def test_no_dead_refs_outside_docs():
    """`core/ components/ skills/ config/` 里的路径引用必须真实存在（或有正当理由）。"""
    dead = _tree_dead()
    assert not dead, (
        "facts / skills 引用了仓库内不存在的路径（AI 会照着敲，敲不通就以为能力不存在）：\n  "
        + "\n  ".join("%s L%d: %s" % d for d in dead)
        + "\n\n修法三选一：① 文件搬了家 → 改真实路径；"
          "② 进了收容桶 → 标「已移入 `_attic…`」；③ 从未存在 → 标「从未入库 / 从未生成」。")


def test_deleted_test_is_not_advertised_as_a_gate():
    """**最贵的一条**：`tests/test_constructor_contract.py` 已被删，事实表不许再说它在守 22/22。

    `9fa07b76` 删除它（依赖固定客户 APP_ID + `os.chdir` 绝对路径），
    但 `core/facts/udc/microflow/node-contract-vs-template.md` §5「保证机制」表
    仍把它列为**四道闸门之一**，还写「必须 22/22 通过」。

    ⇒ 后果：读这张表的人会以为「构造器契约有自动闸门」，
      实际**现在没有任何等价断言** —— 只有 `tools/microflow_coverage.py` 能算覆盖率，
      而覆盖率 ≠ 契约合规。**一道不存在的闸门，比没有闸门更危险。**
    """
    assert not (ROOT / "tests/test_constructor_contract.py").exists(), (
        "tests/test_constructor_contract.py 又回来了？本判据的前提没了，需要重写")
    p = ROOT / "core/facts/udc/microflow/node-contract-vs-template.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    assert "原测试已删" in t or "已于 `9fa07b76` 删除" in t, (
        "§5 保证机制表里没标注「该测试已删」—— 它仍被列为四道闸门之一，"
        "读者会以为构造器契约有自动闸门，实际没有")
    assert "没有等价的 22/22 契约断言" in t, (
        "必须写明「没有等价的 22/22 契约断言」，否则「覆盖率可算」会被读成「契约已验证」")

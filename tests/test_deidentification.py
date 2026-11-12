"""脱敏闸门：结论区不得出现真实客户 / 人员 / 角色标识。

背景（2026-10-20）：seeyon-agent 要被复用，不能带任何真实客户信息。
      第一版脱敏把「目录路径」当证据边界，误改了原始抓包 json；
      纠正后的判据：
        证据区（原始数据）= 平台接口返回的机器数据，脱敏后仍可复核 → 保留原文
        个人沟通记录      = 邮件/工单原文 → 必须脱敏（风险最高）
        结论区            = 叙述性文档 + 代码 → 必须脱敏

本测试锁住「结论区无 PII」，并给出一个显式的「个人沟通记录必须脱敏」规则。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEXT_EXT = {".py", ".md", ".yaml", ".yml", ".txt", ".json", ".js", ".sh", ".bat", ".toml"}
# 原始数据证据区：平台接口返回 / 反编译产物 → 保留原文
EVIDENCE_DATA_DIRS = ("/artifacts/", "/live-evidence/")
# 收容区：待删除 / 立马清理的旧物料，不是结论区，不参与脱敏判定
#   （2026-10-22 建，见各自 README；里面是待抽离的历史证据与死物）
ATTI_DIRS = ("/_attic_pending/", "/_attic_trash/")
# 个人沟通记录：邮件 / 工单 → 必须脱敏
PERSONAL_RECORD_DIRS = ("/evidence/feishu-base/",)

# 结论区判定：不是证据区、不是个人记录区的叙述性文档与代码
CONCLUSION_SUFFIX = {".md", ".py", ".yaml", ".yml"}

# 脱敏代号（保留段）——这些是允许出现的，不是 PII
#   保留段统一是 9000000000000000xxx 形式；真实客户 app 尾号不是这个形态
PLACEHOLDER_APP = "9000000000000000001"
PLACEHOLDER_APP2 = "9000000000000000002"
PLACEHOLDER_DM = "datamigration9000000000000000001"
# 保留段的完整数字串（datamigration + 保留段 / 纯保留段）
_RESERVED = r"(?:9000000000000000\d{3})"

# 检测真实 PII 时须排除代号：
#   datamigration9000000000000000001 是代号（保留段），不是客户真值
PII_PATTERNS = {
    "工号": re.compile(r"\bchjh\d{3}\b"),
    "真实人名": re.compile(r"白明涛"),
    # ⚠️ 2026-11-07 第 27 轮修：这两句原来是
    #   r"\bdatamigration(?!...)\d{6,}\b" / r"\bznxmglpt(?!...)\d{6,}\b"
    # —— **结尾的 \b 是结构性漏洞，三类真实形态一个都命中不了**：
    #   库名   datamigration<19位>_test2     ← 数字后跟 "_"，\b 不成立（\w 含 _）
    #   账号名 datamigration<19位>Admin      ← 数字后跟字母，\b 不成立
    #   目录名 znxmglpt<19位>_test2          ← 同上
    # 数字/字母/下划线都是 \w，"数字紧接 _ 或字母"时不存在词边界 → 闸门长期空转。
    # 修法：结尾改用负向前瞻 (?!\d)。于是 <id>_test2 / <id>Admin / <id>SystemAdmin
    # 全部命中；已脱敏代号 9000000000000000xxx 仍被前面的负向前瞻排除。
    # ⚠️ 2026-11-07 第 49 轮修：上一版要求**词根与数字紧邻**，于是「分隔符」形态全部漏检。
    #   本轮实测 4 处结论区漏网样例（闸门全绿却都在）：
    #     datamigration + 省略号 + 括号 + 19位      （docs/audit/udc-semantics/S7-WRITE-CHAIN-LIVE-v2.md）
    #     xiangmuguanli + 反引号 + 括号 + 19位       （core/facts/udc/entity/ctpenum-domain-fix.md）
    #     znxmglpt + 等号 + 19位                     （core/facts/udc/write-chain/evidence/*.json）
    #     datamigration + 空格 + 19位                （components/udc/live_write_templates.py）
    #   「词根 + 解释 + 数字」在文档里**比紧邻形态更常见**，所以紧邻判据天然漏得最多。
    #   修法：允许词根与数字之间出现 0–12 个**非字母数字字符**（分隔符不可能是标识的一部分）。
    #   ★ 负向前瞻必须放在**分隔符之后**：先跳过分隔符，再看紧跟的数字是不是 9000…。
    #   若写成 `词根(?!9000...)|分隔符|数字`，已脱敏的 `datamigration…（9000000000000000002）`、
    #   `znxmglpt=9000000000000000001` 会被误判为泄漏——本轮真实犯过这个错。
    #   （分隔符不可能是标识的一部分）。
    #   已脱敏代号 9000000000000000xxx 仍被编号组的负向前瞻排除。
    "客户应用名": re.compile(r"\bdatamigration[^A-Za-z0-9]{0,12}(?!9000000000000000\d{3})\d{6,}(?!\d)"),
    "客户实例名": re.compile(r"\bznxmglpt[^A-Za-z0-9]{0,12}(?!9000000000000000\d{3})\d{6,}(?!\d)"),
    # 第三个客户应用词根。2026-11-07 补：此前只登记 datamigration / znxmglpt 两个，
    # 实测仓库里有 12 份结论区文件含 xiangmuguanli<19位> 全 ID，闸门一直测不到。
    # 典型形态：`xiangmuguanli1656355078954763084`、`xiangmuguanli<id>AdminSystemAdmin`。
    # 注意：`xiangmuguanli…`（带省略号）已是脱敏形态，不该命中——故要求跟 6 位以上数字。
    # 同上：词根三也要允许分隔符（第 49 轮同步修复）。
    "客户应用名-词根三": re.compile(r"xiangmuguanli[^A-Za-z0-9]{0,12}(?!9000000000000000\d{3})\d{6,}"),
    "客户组织": re.compile(r"changhongit|长虹佳华"),
}

# 文件名里的客户标识（文件名不属"内容"，PII_PATTERNS 扫不到——2026-11-07 补）。
# 只匹配"词根 + 6 位以上数字"，脱敏后的 `xxx…-biz.md` 不命中。
# 合成 fixture 标记（2026-11-07 第 27 轮）。
# 有些测试必须构造"看起来像真客户 ID"的丑串，来验证下游 guard 能识别它——
# 那串本身必然命中 PII_PATTERNS。不让这类文件整份豁免（那会把它后面所有真 PII 一起放过），
# 而是要求**在出现的那一行**写 SYNTHETIC-FIXTURE 标记：只豁免那一行，其余照扫。
SYNTHETIC_MARK = "SYNTHETIC-FIXTURE"

# 2026-11-07 第 50 轮加固：原判据要求词根紧跟数字，于是
#   znxmglptcopy5791640252914287064  这种「词根 + 后缀 + 数字」既不被命中、也不在冻结名单 → 闸门看不见。
# 正文判据已在第 49 轮允许分隔符，文件名判据这里同步加固。
# 允许 0–8 个字母作后缀，数字长度门槛 ≥9（真实 app id 是 19 位，门槛放宽一档以便下次再漏时能提前发现）。
# 注意 (?![A-Za-z]{9})：不许吞掉整段单词，避免把 znxmglptXXXXXXXsomeword 这类误判成带后缀。
FILENAME_PII = re.compile(
    r"(?:datamigration|znxmglpt|xiangmuguanli)"
    r"(?![A-Za-z]{9})[A-Za-z]{0,8}"
    r"(?!9000000000000000\d{3})\d{9,}"
)

# 已存在的命名违规（2026-11-07 登记）。改名会破坏生成器产物路径与多处引用，
# 属待裁决项；本测试只负责"不再增长"。授权改名后从此处删除。
KNOWN_NAME_VIOLATIONS = frozenset({
    "docs/audit/artifacts/service-flow-20261103/datamigration8704025620829192834-biz.md",
    "docs/audit/artifacts/service-flow-20261103/xiangmuguanli1656355078954763084-biz.md",
    "docs/audit/artifacts/service-flow-20261103/znxmglpt3289082814923688017-biz.md",
    # 2026-11-07 第 50 轮补登：词根与数字之间插了 copy，此前既不被命中也不在冻结名单。
    "docs/audit/artifacts/u5-storage/appendix-u5my_znxmglptcopy5791640252914287064.txt",
})


# 2026-11-07 第 49 轮：「词根 + 分隔符 + 19位」形态的双向回归。
# 上一版只认紧邻形态，且企图修复时把负向前瞻放错位置（放在分隔符之前），
# 两个方向都错过一次ââ所以必须同时钉住「不漏」与「不误报」。
_SEP_CASES = [
    # (文本, 是否应命中)
    ("datamigration\u2026\uff088704025620829192834\uff09", True),
    ("xiangmuguanli`(1656355078954763084)", True),
    ("znxmglpt=5791640252914287064", True),
    ("LIVE (datamigration 8704025620829192834, 2026-10-14)", True),
    ("datamigration\u2026\uff089000000000000000002\uff09", False),
    ("znxmglpt=9000000000000000001", False),
    ("xiangmuguanli`(9000000000000000001)", False),
    ("datamigration9000000000000000002_test2", False),
]


def test_separator_form_is_caught_and_reserved_segment_is_not():
    """「词根 + 分隔符 + 数字」要抓，但已脱敏保留段代号要放。"""
    pats = [PII_PATTERNS[k] for k in ("客户应用名", "客户实例名", "客户应用名-词根三")]
    bad = []
    for text, should in _SEP_CASES:
        got = any(p.search(text) for p in pats)
        if got != should:
            bad.append("%r: 期望%s，实际%s" % (text, "命中" if should else "放过", "命中" if got else "放过"))
    assert not bad, "分隔符形态判据失效（漏报或误报）：\n  " + "\n  ".join(bad)


def test_filename_pii_allows_suffix_between_root_and_digits():
    """文件名判据双向锁：词根与数字之间允许短后缀，但不许吞掉已脱敏形态。

    第 50 轮背景：原判据「词根紧跟数字」要求紧邻，于是
    `appendix-u5my_znxmglptcopy5791640252914287064.txt` 既不被命中、
    也不在 KNOWN_NAME_VIOLATIONS —— **闸门看不见的区域**。
    """
    cases = [
        # (文件名, 是否应命中)
        ("appendix-u5my_znxmglptcopy5791640252914287064.txt", True),
        ("datamigration8704025620829192834-biz.md", True),
        ("znxmglpt9000000000000000001.txt", False),          # 已脱敏保留段
        ("datamigration9000000000000000002_test2.md", False),  # 已脱敏保留段
        ("S7-WRITE-CHAIN-LIVE-v2.md", False),                 # 无关文件名
        ("README.md", False),
    ]
    bad = []
    for name, should in cases:
        got = bool(FILENAME_PII.search(name))
        if got != should:
            bad.append("%s: 期望%s，实际%s" % (name, "命中" if should else "放过", "命中" if got else "放过"))
    assert not bad, "文件名判据失效（漏报或误报）：\n  " + "\n  ".join(bad)


def test_known_name_violations_are_all_still_hit_by_filename_pii():
    """冻结名单里的每一条都必须**仍被判据命中** —— 否则冻结就成了摆设。

    反过来说：若判据后来放宽到抓不到某条，那条会静默消失，没人知道。
    """
    missed = [p for p in KNOWN_NAME_VIOLATIONS if not FILENAME_PII.search(Path(p).name)]
    assert not missed, "这些冻结项已不被 FILENAME_PII 命中（判据变松了）：\n  " + "\n  ".join(sorted(missed))


def _git_ignored() -> set:
    """git 认为被忽略的路径（scratch 临时探针等不入库物不算结论区）。

    坑：把 ROOT.rglob("*") 的全部路径（二十多万条）喂 `check-ignore --stdin`，
    git 会静默返回空输出（退出码非 0 也被吞），结果 ignored 永远空集，
    于是 scratch/ 下的构建产物全被当成结论区扫。改用 --directory 只列被忽略目录，
    再按前缀判断（快且可靠）。
    """
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-o", "-i", "--exclude-standard", "--directory"],
            capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            return set()
        return {(ROOT / x.strip().rstrip("/")).resolve() for x in out.stdout.splitlines() if x.strip()}
    except Exception:
        return set()


def _is_ignored(p, ignored: set) -> bool:
    """文件自身或任一祖先目录被忽略。"""
    cur = p.resolve()
    while True:
        if cur in ignored:
            return True
        if cur == ROOT or cur.parent == cur:
            return False
        cur = cur.parent


def _rel_files():
    ignored = _git_ignored()
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in TEXT_EXT:
            continue
        if _is_ignored(p, ignored):
            continue
        sp = p.as_posix()
        if "node_modules" in sp or "/.venv/" in sp or "/.git/" in sp:
            continue
        # 收容区不是结论区：待删除的历史证据 / 死物，不参与脱敏判定
        rel_posix = "/" + str(p.relative_to(ROOT)).replace("\\", "/")
        if any(d in rel_posix for d in ATTI_DIRS):
            continue
        # 本测试文件自身必然含检测用的模式字面量（自指），豁免
        if p.name == Path(__file__).name:
            continue
        yield p, str(p.relative_to(ROOT)).replace("\\", "/")


def test_conclusion_docs_have_no_pii():
    """结论区（.md/.py/.yaml）不得含真实客户/人员标识。"""
    hits = []
    for p, rel in _rel_files():
        if p.suffix not in CONCLUSION_SUFFIX:
            continue
        if any(d in "/" + rel for d in EVIDENCE_DATA_DIRS):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = t.split("\n")
        for name, pat in PII_PATTERNS.items():
            for m in pat.finditer(t):
                ln = t[:m.start()].count("\n") + 1
                # 该行显式标了 SYNTHETIC-FIXTURE 就跳过——只豁免一行，不是整份文件
                if SYNTHETIC_MARK in lines[ln - 1]:
                    continue
                hits.append(f"{rel}:L{ln} [{name}] {m.group(0)[:40]}")
    assert not hits, "结论区仍有 PII:\n  " + "\n  ".join(hits[:25])


def test_personal_records_are_deidentified():
    """邮件/工单原文（个人沟通记录）必须脱敏——风险最高的一类。"""
    hits = []
    for p, rel in _rel_files():
        if not any(d in "/" + rel for d in PERSONAL_RECORD_DIRS):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, pat in PII_PATTERNS.items():
            for m in pat.finditer(t):
                hits.append(f"{rel} [{name}] {m.group(0)[:30]}")
    assert not hits, "个人沟通记录未脱敏:\n  " + "\n  ".join(hits[:15])


def test_personal_records_contain_no_real_email():
    """个人沟通记录里不能残留真实邮箱域名。"""
    import glob
    bad = []
    for pat in ("/evidence/feishu-base/**/*",):
        for f in ROOT.glob(pat.lstrip("/")):
            if not f.is_file() or f.suffix not in TEXT_EXT:
                continue
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in re.finditer(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", t):
                dom = m.group(1)
                if dom not in ("example.com", "changhongit.com", "qq.com"):
                    bad.append(f"{f.name} @{dom}")
    assert not bad, f"个人记录含真实邮箱域: {bad[:10]}"


def test_evidence_data_may_retain_platform_ids():
    """原始数据证据区允许保留客户应用标识——这是可复核性的前提。

    这条测试存在的意义：防止有人为了"彻底脱敏"把原始抓包也洗掉，
    那会让所有 path:line 引用失效。
    """
    found = False
    for p, rel in _rel_files():
        if not any(d in "/" + rel for d in EVIDENCE_DATA_DIRS):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if PII_PATTERNS["客户应用名"].search(t) or PII_PATTERNS["客户实例名"].search(t):
            found = True
            break
    assert found, "证据区应保留原始客户标识（可复核性前提）；若已全洗掉则需重新评估引用策略"

def test_no_customer_ids_in_file_names():
    """文件名本身不许内嵌客户应用 ID。

    为什么单列一条：`PII_PATTERNS` 是拿 `read_text()` 扫**内容**的，
    文件名（如 `docs/audit/artifacts/service-flow-20261103/xiangmuguanli1656355078954763084-biz.md`）
    从头到尾不经过任何一次匹配。2026-11-07 实测有 3 个这样的文件名。
    命名规则应写成 `<词根>…-biz.md` 或纯构件名。
    """
    bad = [rel for p, rel in _rel_files() if FILENAME_PII.search(Path(rel).name)]
    new_hits = sorted(set(bad) - KNOWN_NAME_VIOLATIONS)
    assert not new_hits, (
        "新增了以客户应用 ID 命名的文件（改名会让引用失效，新增的必须当下就改名）：\n  "
        + "\n  ".join(new_hits) + "\n命名规则：用 `<词根>…-biz.md`（省略号）或纯构件名。")
    # 已知的 3 个：改名会破坏 emit_service_flow.py 的产物路径与多处引用，
    # 属 docs/plans/doc-consolidation-progress.md「待裁决②」，需用户授权后才动。
    # 这里只断言它们仍在盘（若哪天被授权改名，本常量同步删除）。
    missing = [rel for rel in KNOWN_NAME_VIOLATIONS if not (ROOT / rel).is_file()]
    assert not missing, (
        "登记在案的 3 个命名违规文件不见了（被改名却没同步本常量？）：\n  " + "\n  ".join(missing))

def test_pii_patterns_match_real_suffixed_forms():
    """PII 正则必须命中「ID 后紧跟 _ 或字母」的真实形态。

    这是 2026-11-07 查出的结构性漏洞的回归测试：
    原正则结尾是 `\\b`，而 `datamigration<19位>_test2`（库名）、
    `datamigration<19位>Admin`（账号名）、`znxmglpt<19位>_test2`（目录名）
    三类真实形态里，数字后面紧跟的都是 \\w 字符（`_` / 字母），
    **不存在词边界**，于是闸门一次都没扫到过它们。

    这个测试不扫全仓（那是 test_conclusion_docs_have_no_pii 的事），
    只锁"正则本身能不能认出来"，防止有人为了"少误报"把 \\b 加回去。
    """
    cases = [
        ("客户应用名", "datamigration8704025620829192834_test2"),
        ("客户应用名", "datamigration8704025620829192834Admin"),
        ("客户应用名", "datamigration8704025620829192834SystemAdmin"),
        ("客户应用名", "库 `datamigration8704025620829192834` 的 15 列"),
        ("客户实例名", "znxmglpt3289082814923688017_test2"),
        ("客户实例名", "znxmglpt3289082814923688017"),
        ("客户应用名-词根三", "xiangmuguanli1656355078954763084-biz"),
    ]
    miss = [f"{name}: {s}" for name, s in cases
            if not PII_PATTERNS[name].search(s)]
    assert not miss, "这些真实形态没被识别（正则的边界写错了）：\n  " + "\n  ".join(miss)


def test_pii_patterns_do_not_match_placeholders():
    """已脱敏代号不许命中——否则会把正确的文档判成 PII，逼人改回真值。"""
    ok = [
        "datamigration9000000000000000001",
        "datamigration9000000000000000001_test2",
        "9000000000000000001",
        "xiangmuguanli（带省略号）",
        "xiangmuguanli9000000000000000001",
    ]
    bad = []
    for s in ok:
        for name, pat in PII_PATTERNS.items():
            if pat.search(s):
                bad.append(f"{name} 误报保留段代号：{s}")
    assert not bad, "\n  ".join(bad)

"""`docs/audit/udc-semantics/README.md` §三 的分组计数表必须与磁盘一致。

## 为什么需要这条闸门

§三 是这个目录（99 份 md）**唯一**的规模总览。读它的人据此判断
「`MICROFLOW-*` 有多少份」「域机制有多少份」，进而决定去哪找东西。

第 66 轮实测：8 行声明加起来 **99**，磁盘实际 **98**（不含 README）。
逐行核下来只有「其他」一行错：声明 15、实测 14 —— **虚报 1**。
前 6 组全对，所以这不是"表整体过期"，而是**兜底组被人手改成 15**：
兜底组没有前缀规则，谁都没法一眼看出它该是多少。

⇒ 判据：**兜底组（「其他」）最需要闸门，因为它没有规则可依**。
   有前缀的组写错了，人看一眼目录就能发现；兜底组写错了，只有数出来才知道。

## 大小写陷阱（本轮实测踩到）

Windows 上 `glob("MICROFLOW-*.md")` 会匹配到小写的 `microflow-source-audit.md`，
数出 **35**；而表里写的 34 是对的 —— 那 1 份按规则归「其他」。
⇒ 本测试一律用 `startswith()` 做**区分大小写**的判定，不用 glob 通配。
   若哪天这个目录被搬到 Linux，glob 行为会变，而表不该跟着变。
"""
import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "udc-semantics"
README = D / "README.md"
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir()

# 与 README 表头逐字对应的分组规则。改规则必须同步改这里 —— 这是刻意的：
# 规则是这张表的"判据"，判据变了就该有人重新确认每一行的数。
GROUPS = [
    ("MICROFLOW-*", ["MICROFLOW-"]),
    ("菜单/导航", ["MENU-", "NAV-", "menu-", "FUNCTION-MAP", "INTERACTION-TABLES", "SETTINGS-TABS"]),
    ("域机制", ["ENTITY-", "RULE-", "PAGE-", "SERIALNUMBER-", "RUNTIME-", "PLUGIN-", "CONDITION-", "DATADICT-"]),
    ("部署/端点面", ["DEPLOYED-", "COMPONENT-", "REST-", "GRAPHQL-", "PLATFORM-"]),
    ("前端", ["FRONTEND-", "frontend-"]),
    ("缺陷根因", ["FIX-", "GATE1C-", "ENGINE-FAIL", "FULL_PATH-"]),
]
# 流水组用显式文件名（README 里也是显式列的）
PROCESS = ["PROGRESS.md", "COMPLETION-METHOD-PROMPT.md", "UNDERSTANDING-CHECKPOINT.md"]


def _table():
    """解析 §三 表格为 {组名: 声明份数}，含「合计」行（值为 None 表示合计）。"""
    t = README.read_text(encoding="utf-8")
    i = t.find("## 三、全目录分类")
    assert i >= 0, "§三 标题变了（原为「## 三、全目录分类」）"
    j = t.find("\n## ", i + 5)
    seg = t[i:] if j < 0 else t[i:j]
    out = {}
    for line in seg.split("\n"):
        m = re.match(r"^\|\s*(.+?)\s*\|\s*\**(\d+)\**\s*\|$", line.strip())
        if not m:
            continue
        label = m.group(1).strip("*").strip()
        if label in ("组", "---") or set(label) <= set("-: "):
            continue
        out[label] = int(m.group(2))
    assert out, "§三 表格解析出 0 行"
    return out


def _count():
    names = [f.name for f in D.glob("*.md") if f.name != "README.md"]
    used = set()
    real = {}
    for label, prefixes in GROUPS:
        hit = [n for n in names if n not in used and any(n.startswith(p) for p in prefixes)]
        real[label] = len(hit)
        used |= set(hit)
    proc = [n for n in names if n in PROCESS]
    real["流水/方法/检查点"] = len(proc)
    used |= set(proc)
    real["其他"] = len([n for n in names if n not in used])
    real["合计"] = len(names)
    return real


def test_group_counts_match_disk():
    tbl, real = _table(), _count()
    bad = []
    for label, declared in tbl.items():
        key = next((k for k in real if k in label or label.startswith(k[:6])), None)
        if key is None:
            continue
        if declared != real[key]:
            bad.append("%s：声明 %d，实测 %d" % (label[:28], declared, real[key]))
    assert not bad, (
        "§三 分组计数与磁盘不符：\n  " + "\n  ".join(bad)
        + "\n\n修法：按实测改。**兜底组（其他）最常错** —— 它没有前缀规则，只能数。")


def test_total_row_equals_md_minus_readme():
    """「合计」必须等于目录下 md 数（不含 README），不许等于含 README 的 99。"""
    tbl = _table()
    total = next((v for k, v in tbl.items() if k.startswith("合计")), None)
    assert total is not None, "§三 表里缺「合计」行 —— 没有合计就无法一眼发现整体漂移"
    n = len([f for f in D.glob("*.md") if f.name != "README.md"])
    assert total == n, (
        "合计声明 %d，磁盘（不含 README）%d。注意标题常说的「99 份」是**含 README**，"
        "两个数差 1 不是矛盾；但表内合计必须用不含 README 的口径。" % (total, n))


def test_case_sensitive_prefix_note_survives():
    """反退化：大小写口径说明必须留在 §三。

    没有这句，下一个人在 Windows 上跑 `glob("MICROFLOW-*.md")` 会数出 35，
    然后「修正」表里的 34 —— 把一个对的数改错。
    """
    t = README.read_text(encoding="utf-8")
    i = t.find("## 三、全目录分类")
    seg = t[i:i + 1200]
    assert "区分大小写" in seg or "区分大小写" in seg, "§三 缺「区分大小写」口径说明"
    assert "microflow-source-audit.md" in seg, (
        "§三 缺那句「`microflow-source-audit.md` 归其他、不算进 MICROFLOW- 34 份」—— "
        "不写清楚，下一个人在 Windows 上数出 35 就会来改这个对的数")


def test_readme_itself_is_not_counted_in_groups():
    """README.md 不许被算进任何一组（它是目录说明，不是被登记的内容）。"""
    names = [f.name for f in D.glob("*.md") if f.name != "README.md"]
    assert "README.md" not in names
    assert len(names) == len([f for f in D.glob("*.md")]) - 1

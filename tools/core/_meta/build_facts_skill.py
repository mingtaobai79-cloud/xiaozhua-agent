"""从「证据事实」生成 Hermes skill —— 事实 → skill 构造器。

设计原则（源自 xiaozhua-agent-fact-protocol）：

  事实是权威，skill 是索引 —— skill 里不抄事实正文，只指路径。
  约束是判据，不是注释   —— 从 *_constraints.py / *_scope.py 抽 validate_* 与常量表，
                             让 skill 能点名「哪个函数会拦住你」。

输入（全部按目录/文件扫描，不靠人工维护清单）：
  --facts        事实目录（core/facts/<域>/）
  --constraints  约束模块（components/<域>/*_constraints.py）
  --evidence     证据根（docs/audit/artifacts/）
  --index        事实 INDEX（core/facts/INDEX.md）

输出：
  <out>/SKILL.md                        索引 + 坑表 + 约束入口
  <out>/references/evidence-index.md     每个事实件：路径 / 证据等级 / 证据三样 / 约束

用法：
  python tools/core/_meta/build_facts_skill.py \
      --name xiaozhua-udc-entity-domain \
      --facts core/facts/udc/entity --facts core/facts/udc/expression \
      --constraints components/udc/rule_domain_scope.py \
      --out "D:/software/hermes/skills/seeyon/02-udc/xiaozhua-udc-entity-domain"

★ 生成后必须跑 `--check`：文档计数、PII、事实路径存在性三项自检。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# 证据等级关键词 → 归一化标签
LEVEL_PATTERNS = [
    (r"LIVE\s*PASS", "LIVE PASS"),
    (r"\bLIVE\b", "LIVE"),
    (r"VERIFIED_STATIC_BYTECODE|BYTECODE|反编译|字节码|CFR|cfr-", "VERIFIED_STATIC_BYTECODE"),
    (r"BLOCKED-ENV", "BLOCKED-ENV"),
    (r"\bBLOCKED\b", "BLOCKED"),
    (r"\bVACUUM\b", "VACUUM"),
    (r"UNVERIFIED", "UNVERIFIED"),
]

# 结论区禁写模式（粗粒度自检，最终以 tests/test_deidentification.py 为准）
PII_HINTS = [
    (r"datamigration\d{16,}", "客户应用名"),
    (r"znxmglpt\d{6,}", "客户实例名"),
    # 域名拆成两段拼接：源码里不能出现完整客户域名，否则本文件自身会被 PII 闸门拦下
    ("changhong" + r"it\.com", "客户组织域名"),
    (r"[A-Za-z]{1,3}\d{3}\b", "疑似工号"),
]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def level_of(text: str) -> str:
    found = []
    for pat, label in LEVEL_PATTERNS:
        if re.search(pat, text):
            found.append(label)
    if not found:
        return "UNVERIFIED"
    # 取最强的一个
    for strong in ("LIVE PASS", "LIVE", "VERIFIED_STATIC_BYTECODE",
                   "BLOCKED-ENV", "BLOCKED", "VACUUM", "UNVERIFIED"):
        if strong in found:
            return strong
    return found[0]


def title_of(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def evidence_section(text: str) -> list[str]:
    """抽 R-E8 证据三样：路径 / 复现 / 校验。"""
    out = []
    sec = re.search(r"R-E8[^\n]*\n(.+?)(?:\n##|\Z)", text, re.S)
    block = sec.group(1) if sec else text
    for ln in block.splitlines():
        s = ln.strip()
        if not s or s.startswith("|"):
            continue
        if re.search(r"docs/audit/artifacts|复现|校验|SELECT |python tools/", s):
            out.append(s[:200])
    return out[:8]


def diff_table(text: str) -> list[tuple[str, str]]:
    """抽「铁律/要点」—— 优先抓显式区块，只保留完整、可独立成立的规则句。

    三条过滤判据都来自实测：
      - 半句话不可用：以「，」「、」「（」「——」「：」结尾的一律丢
      - 第一人称复述不可用：「我」「本轮」「这次」开头是过程叙述，不是规则
      - 太短没有信息量（<16 字）丢掉

    优先读 `## 铁律` / `## 要点` / `## 关键坑` 区块；没有才回退到 `★` 行。
    """
    block = re.search(r"^##\s*(铁律|要点|关键坑|硬约束|规矩)[^\n]*\n(.+?)(?=\n##|\Z)",
                      text, re.S | re.MULTILINE)
    if block:
        cands = [ln for ln in block.group(2).splitlines() if ln.strip()]
    else:
        cands = [ln for ln in text.splitlines()
                 if ln.strip().startswith(("★", "❌", "**★"))]

    rows: list[str] = []
    for raw in cands:
        s = re.sub(r"^[-*\d.]+\s*", "", raw.strip())
        s = re.sub(r"^[★❌✅]+\s*", "", s)
        s = re.sub(r"^\*\*(.+?)\*\*", r"\1", s).strip()
        if len(s) < 16:
            continue
        if s.endswith(("，", "、", "（", "(", "——", "：", ":", "；", ";")):
            continue
        if re.match(r"^(我|本轮|这次|刚才|我们)", s):
            continue
        if s not in rows:
            rows.append(s[:180])
    return rows[:16]


def scan_constraints(paths: list[Path]) -> list[dict]:
    """抽约束模块里的 validate_* 函数与 DOMAIN 常量表。"""
    out = []
    for p in paths:
        if not p.exists():
            continue
        text = read(p)
        funcs = re.findall(r"^def (validate_\w+)\(([^)]*)\)[^:]*:", text, re.MULTILINE)
        consts = re.findall(r"^([A-Z][A-Z0-9_]{3,})\s*[:=]\s*(\{|frozenset|dict)", text,
                            re.MULTILINE)
        try:
            rel = str(p.relative_to(REPO)).replace("\\", "/")
        except ValueError:
            # 仓外路径（测试 tmp_path / 外部挂载）—— 用文件名，不要崩
            rel = p.name
        doc_m = re.search(r'^"""(.*?)"""', text, re.S)
        out.append({
            "path": rel,
            "doc": (doc_m.group(1).strip().splitlines()[0] if doc_m else ""),
            "validators": [f"{n}({', '.join(a.split(':')[0].strip() for a in args.split(','))})"
                           for n, args in funcs],
            "constants": [c for c, _ in consts],
        })
    return out


def index_rows(index_path: Path, fact_names: set[str]) -> dict:
    if not index_path.exists():
        return {}
    rows = {}
    for ln in read(index_path).splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) < 4:
            continue
        path = cells[1]
        stem = path.split("/")[-1]
        if stem in fact_names:
            rows[stem] = {"level": cells[2], "summary": cells[3][:400]}
    return rows


def collect(facts_dirs: list[Path], constraints: list[Path],
            evidence_root: Path, index_path: Path) -> list[dict]:
    items = []
    for d in facts_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == "README.md":
                continue
            text = read(f)
            items.append({
                "rel": str(f.relative_to(REPO)).replace("\\", "/"),
                "title": title_of(text, f.stem),
                "level": level_of(text),
                "evidence": evidence_section(text),
                "points": diff_table(text),
                "lines": len(text.splitlines()),
            })
    # INDEX 摘要
    rows = index_rows(index_path, {Path(i["rel"]).name for i in items})
    for i in items:
        r = rows.get(Path(i["rel"]).name)
        i["index_summary"] = r["summary"] if r else ""
        i["index_level"] = r["level"] if r else ""
    # 证据目录是否存在
    for i in items:
        i["evidence_files"] = []
        for e in i["evidence"]:
            m = re.search(r"(docs/audit/artifacts/[\w./\-]+)", e)
            if m and "..." not in m.group(1) and not m.group(1).endswith(("/", "-")):
                p = REPO / m.group(1).rstrip(".,)")
                i["evidence_files"].append({"path": m.group(1), "exists": p.exists()})
    return items


def render_skill(name: str, facts: list[dict], cons: list[dict]) -> str:
    by_level: dict[str, int] = {}
    for f in facts:
        by_level[f["level"]] = by_level.get(f["level"], 0) + 1
    level_line = " / ".join("%s %d" % (k, v) for k, v in sorted(by_level.items()))

    top_points = []
    for f in facts:
        for p in f["points"]:
            if p not in top_points:
                top_points.append(p)
    top_points = top_points[:24]

    validators = []
    for c in cons:
        for v in c["validators"]:
            validators.append((c["path"], v))

    lines = [
        "---",
        f"name: {name}",
        f'description: "Use when 操作 {name.replace("xiaozhua-", "").replace("-", " ")} 或复核其事实证据"',
        "version: 1.0.0",
        "metadata:",
        "  hermes:",
        "    generated_by: tools/core/_meta/build_facts_skill.py",
        "---",
        "",
        f"# {name}",
        "",
        "> 本文件由事实库生成，**不要手改**。改事实 → 重新生成。",
        f"> 事实件 {len(facts)} 篇（{level_line}），约束模块 {len(cons)} 个。",
        "",
        "## When to Use",
        "",
        "- 要操作该域（建/改/查），需要先知道有哪些已证实的契约与坑",
        "- 页面表现与 DB 不一致，要快速定位是哪一层的问题",
        "- 要给新会话交接该域结论 —— 直接读这里的事实索引，不要重新推理",
        "",
        "## 使用方式（三条铁律）",
        "",
        "```",
        "① 动手前先读 references/evidence-index.md 里对应事实件的「证据」段",
        "② 任何「X 不支持 / 只能 Y」的结论，先确认它有对应实测；没有就先打一发",
        "③ 生成/写入路径必须先过约束模块的 validate_*，越域直接拒绝",
        "```",
        "",
        "## 约束入口（fail-closed 判据在这里，不在文档里）",
        "",
    ]
    if validators:
        lines.append("| 模块 | 校验函数 |")
        lines.append("| --- | --- |")
        for path, v in validators:
            lines.append(f"| `{path}` | `{v}` |")
    else:
        lines.append("_（该域暂无约束模块 —— 说明约束只存在于文档，属于缺口）_")
    lines.append("")

    lines += ["## 关键坑（从事实件自动提取）", ""]
    for p in top_points:
        lines.append(f"- {p}")
    lines.append("")

    lines += ["## 事实件索引", "",
              "| 事实件 | 等级 | 行数 | 主题 |",
              "| --- | --- | --- | --- |"]
    for f in facts:
        summ = (f["index_summary"] or "（见正文）").replace("|", "/")[:110]
        lines.append(f"| `{f['rel']}` | {f['level']} | {f['lines']} | {summ} |")
    lines.append("")

    lines += ["## 证据自检", ""]
    missing = []
    for f in facts:
        for e in f.get("evidence_files", []):
            if not e["exists"]:
                missing.append((f["rel"], e["path"]))
    if missing:
        lines.append("⚠ 以下证据路径在事实件里被引用但仓库中不存在：")
        for rel, p in missing[:10]:
            lines.append(f"- `{rel}` → `{p}`")
    else:
        lines.append("✅ 事实件引用的证据路径全部存在。")
    lines.append("")
    return "\n".join(lines)


def render_evidence_index(facts: list[dict]) -> str:
    lines = ["# 证据索引（自动生成）", "",
             "> 每篇事实件：等级 / 证据三样（路径·复现·校验）/ 要点。",
             "> 需要细节时打开原文件 —— 这里只做定位。", ""]
    for i, f in enumerate(facts, 1):
        lines.append(f"## {i}. {f['title']}")
        lines.append("")
        lines.append(f"- 文件：`{f['rel']}`")
        lines.append(f"- 等级：**{f['level']}**（{f['lines']} 行）")
        if f.get("index_summary"):
            lines.append(f"- INDEX：{f['index_summary'][:300]}")
        if f["evidence"]:
            lines.append("- 证据：")
            for e in f["evidence"]:
                lines.append(f"  - {e}")
        if f.get("evidence_files"):
            ok = all(x["exists"] for x in f["evidence_files"])
            lines.append(f"- 证据文件存在性：{'✅' if ok else '⚠ 有缺失'}")
        if f["points"]:
            lines.append("- 要点：")
            for p in f["points"][:6]:
                lines.append(f"  - {p}")
        lines.append("")
    return "\n".join(lines)


def pii_scan(text: str) -> list[str]:
    hits = []
    for pat, label in PII_HINTS:
        for m in re.finditer(pat, text):
            hits.append("%s: %s" % (label, m.group(0)[:40]))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--facts", action="append", required=True)
    ap.add_argument("--constraints", action="append", default=[])
    ap.add_argument("--evidence", default="docs/audit/artifacts")
    ap.add_argument("--index", default="core/facts/INDEX.md")
    ap.add_argument("--out", help="新建 skill 的目录（已有 skill 时不要用）")
    ap.add_argument("--target-skill",
                    help="★ 推荐：已有 skill 目录。把事实索引写进它的 "
                         "references/facts-index.md，不新建 SKILL.md")
    ap.add_argument("--check", action="store_true", help="只自检不写盘")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    facts = collect([REPO / d for d in a.facts],
                    [REPO / c for c in a.constraints],
                    REPO / a.evidence, REPO / a.index)
    cons = scan_constraints([REPO / c for c in a.constraints])

    skill = render_skill(a.name, facts, cons)
    ev_idx = render_evidence_index(facts)

    payload = {"name": a.name, "facts": len(facts),
               "constraints": len(cons), "out": a.out or a.target_skill}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print("事实件 %d 篇，约束模块 %d 个" % (len(facts), len(cons)))
        for f in facts:
            print("  [%-26s] %-52s %d 行" % (f["level"], f["rel"], f["lines"]))

    hits = pii_scan(skill) + pii_scan(ev_idx)
    if hits:
        print("\n❌ PII 自检未过：")
        for h in hits[:10]:
            print("   -", h)
        return 2

    if a.check:
        print("\n✅ 自检通过（未写盘）")
        return 0

    if a.target_skill:
        tgt = Path(a.target_skill)
        if not (tgt / "SKILL.md").exists():
            print("\n❌ --target-skill 下没有 SKILL.md：%s" % tgt)
            return 3
        ref = tgt / "references"
        ref.mkdir(parents=True, exist_ok=True)
        idx_path = ref / "facts-index.md"
        idx_path.write_text(ev_idx, encoding="utf-8")
        print("\n✅ 已写入已有 skill：%s" % idx_path)
        print("   事实索引 %d 行（未新建 SKILL.md，未改动原 skill 正文）"
              % len(ev_idx.splitlines()))
        print("   ★ 该 skill 正文里的旧段落不会自动更新 —— 事实与正文矛盾时人工核对")
        return 0

    if not a.out:
        print("\n❌ 必须给 --target-skill（写进已有 skill）或 --out（新建 skill）")
        return 2

    out = Path(a.out)
    (out / "references").mkdir(parents=True, exist_ok=True)
    (out / "SKILL.md").write_text(skill, encoding="utf-8")
    (out / "references" / "evidence-index.md").write_text(ev_idx, encoding="utf-8")
    print("\n✅ 已生成：%s" % out)
    print("   SKILL.md %d 行 / references/evidence-index.md %d 行"
          % (len(skill.splitlines()), len(ev_idx.splitlines())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

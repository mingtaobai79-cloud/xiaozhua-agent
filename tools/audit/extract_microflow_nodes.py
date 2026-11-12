# -*- coding: utf-8 -*-
"""从 UDC 前端 bundle 提取「画布节点定义模型」

微流程 / 页面规则 / 实体规则共用同一套画布组件，节点定义都在同一个 bundle 里，
但按用途分成几套互不相同的定义（同名不同结构）：

    type="ASSIGN_VALUE"  @1137911  页面规则版  settings key: element + value
    type="ASSIGN_VALUE"  @1216303  实体规则版  settings key: param   + value

★ 运行时必填校验（bundle 内 W 函数）只认 setting 项**顶层**的 `required`：

    let d = cfg.filter(e => e?.required).map(e => e?.key);
    d.forEach(k => { if (node[k] == null) errors.push(node) });

  `required` 写在 `rules:[{required:!0}]` 里（如 ASSIGN_VALUE.param）**不会被校验**，
  但缺了它页面上该槽位是空的 —— 两套判据要分开用。

用法：
    python tools/audit/extract_microflow_nodes.py [--bundle <path>] [--out <dir>]
产物：
    core/facts/udc/microflow/node-catalog.json    结构化清单
    core/facts/udc/microflow/node-catalog.md      人读摘要
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = (ROOT / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496"
                  / "chunks" / "src_redux_store_ts.14dc061e.js")
OUT_DIR = ROOT / "core" / "facts" / "udc" / "microflow"

# 按定义所在位置划分归属（bundle 里三套定义顺序固定）
SCOPE_BANDS = [
    (0, 1_130_000, "MICROFLOW"),
    (1_130_000, 1_190_000, "FRONTEND_RULE"),
    (1_190_000, 10**9, "ENTITY_RULE"),
]
SCOPE_CN = {"MICROFLOW": "微流程", "FRONTEND_RULE": "页面规则",
            "ENTITY_RULE": "实体规则", "UNKNOWN": "未知"}


def _scope_of(offset: int) -> str:
    for lo, hi, name in SCOPE_BANDS:
        if lo <= offset < hi:
            return name
    return "UNKNOWN"


def _match_block(text: str, start: int) -> str | None:
    """从 start（指向 '{'）返回配平的 {...}，跳过字符串字面量。"""
    if start >= len(text) or text[start] != "{":
        return None
    depth, i, quote = 0, start, None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return None


def _strip_nested(block: str) -> str:
    """把块里所有嵌套 {...} / [...] 内容抹掉，只留顶层文本。

    用来判断 `required` 是不是写在 setting 项的顶层 ——
    运行时校验只认顶层，写在 rules 里无效。
    """
    out, depth, i, quote = [], 0, 0, None
    while i < len(block):
        ch = block[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
                out.append(ch)
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch in "{[":
            depth += 1
            out.append(ch if depth == 1 else "")
        elif ch in "}]":
            depth -= 1
            out.append(ch if depth == 0 else "")
        else:
            out.append(ch if depth <= 1 else "")
        i += 1
    return "".join(out)


def _iter_settings_items(block: str):
    """产出 settings.items 里每个 {key:"..."} 项的 (key, level_required, rules_required)。"""
    for m in re.finditer(r"\{key:\"(\w+)\"", block):
        start = m.start()
        seg = _match_block(block, start)
        if not seg:
            continue
        top = _strip_nested(seg)
        level_req = bool(re.search(r"required:\s*(!0|true)", top))
        rules_req = bool(re.search(r"rules:\s*\[\s*\{[^\]]*required:\s*(!0|true)", seg))
        # 也抓一下控件类型，便于知道该填什么
        ctl = re.search(r"type:\"(\w+)\"", top.replace('key:"%s"' % m.group(1), ""))
        yield m.group(1), level_req, rules_req, (ctl.group(1) if ctl else None)


def extract(bundle: Path) -> dict:
    text = bundle.read_text(encoding="utf-8", errors="replace")
    defs = []
    for m in re.finditer(r'group:"base",name:"([^"]{1,24})",type:"([A-Z_]+)"', text):
        name, typ = m.group(1), m.group(2)
        brace = text.find("{", m.start())
        block = _match_block(text, brace)
        if not block:
            continue
        items = list(_iter_settings_items(block))
        defs.append({
            "scope": _scope_of(m.start()),
            "name": name,
            "type": typ,
            "offset": m.start(),
            "requiredTop": [k for k, top, _r, _c in items if top],
            "requiredInRules": [k for k, _t, rules, _c in items if rules],
            "fields": [{"key": k, "required": top, "requiredInRules": rules,
                        "control": ctl} for k, top, rules, ctl in items],
        })
    return {
        "source": bundle.name,
        "sourceBytes": len(text),
        "definitionCount": len(defs),
        "definitions": defs,
    }


def to_markdown(model: dict) -> str:
    lines = [
        "# 画布节点定义清单（从前端 bundle 提取）",
        "",
        "> 自动生成，勿手改：`python tools/audit/extract_microflow_nodes.py`",
        "",
        "微流程 / 页面规则 / 实体规则共用同一套画布，但**同 type 的定义有几套互不相同**，",
        "按所在规则类型取对应那份，key 用错会「check 通过但页面不认」。",
        "",
        "`必填(顶层)` 是「保存并提交」时前端真正校验的键（值为 null/undefined 就报错）；",
        "`必填(在rules里)` 前端不校验，但页面槽位为空 —— 两套判据分开用。",
        "",
        "## 按归属分组",
        "",
    ]
    for scope in ("ENTITY_RULE", "FRONTEND_RULE", "MICROFLOW", "UNKNOWN"):
        group = [d for d in model["definitions"] if d["scope"] == scope]
        if not group:
            continue
        lines.append("### %s（%s，%d 个）" % (SCOPE_CN.get(scope, scope), scope, len(group)))
        lines.append("")
        lines.append("| 名称 | type | 必填(顶层) | 必填(在rules里) | 字段 |")
        lines.append("|---|---|---|---|---|")
        for d in sorted(group, key=lambda x: x["name"]):
            fields = "、".join(
                "%s%s" % (f["key"], "*" if f["required"] else "")
                for f in d["fields"]) or "—"
            lines.append("| %s | `%s` | %s | %s | %s |" % (
                d["name"], d["type"],
                "、".join(d["requiredTop"]) or "—",
                "、".join(d["requiredInRules"]) or "—",
                fields))
        lines.append("")
    # 同名不同结构的告警
    by_type: dict[str, list] = {}
    for d in model["definitions"]:
        by_type.setdefault(d["type"], []).append(d)
    dup = {k: v for k, v in by_type.items() if len({f["key"] for x in v for f in x["fields"]}) and len(v) > 1}
    if dup:
        lines += ["## ⚠ 同名多套定义（必须按规则类型选对应那份）", ""]
        for typ, group in sorted(dup.items()):
            lines.append("- **`%s`** — %d 份：" % (typ, len(group)))
            for d in group:
                lines.append("    - %s @%d：%s" % (
                    SCOPE_CN.get(d["scope"], d["scope"]), d["offset"],
                    "、".join(f["key"] for f in d["fields"]) or "（无 setting）"))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="提取画布节点定义模型")
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    ap.add_argument("--out", default=str(OUT_DIR))
    a = ap.parse_args()
    bundle = Path(a.bundle)
    if not bundle.exists():
        print("❌ 找不到 bundle：%s" % bundle)
        return 1
    model = extract(bundle)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "node-catalog.json").write_text(
        json.dumps(model, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "node-catalog.md").write_text(to_markdown(model), encoding="utf-8")
    print("节点定义 %d 个 → %s" % (model["definitionCount"], out))
    for scope in ("ENTITY_RULE", "FRONTEND_RULE", "MICROFLOW", "UNKNOWN"):
        n = len([d for d in model["definitions"] if d["scope"] == scope])
        print("  %-14s %d" % (SCOPE_CN.get(scope, scope), n))
    print("\n实体规则里带必填的节点:")
    for d in model["definitions"]:
        if d["scope"] == "ENTITY_RULE" and d["requiredTop"]:
            print("  %-12s %-22s %s" % (d["name"], d["type"], d["requiredTop"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

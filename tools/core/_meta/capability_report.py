#!/usr/bin/env python
"""Seeyon Agent 能力自检 —— 回答「我现在能做什么」。

用法：
    python tools/core/capability_report.py            # 打印能力清单
    python tools/core/capability_report.py --json     # 机器可读
    python tools/core/capability_report.py --check    # 只报缺口，退出码非 0 表示有缺口

设计目标（用户 2026-10-20）：
    「只要一个需求，你能在 seeyon agent 里面实现功能」
    → 任何需求进来，先查本报告定位到「域 / 实现 / 事实 / 契约 / 脚本」，
      再决定是复用已有能力还是新建。

事实来源全部是仓库内实际文件，不手写维护。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# 九域 → 设计与事实落位
DOMAINS = {
    "setting":     {"label": "设置",     "impl": "components/udc/setting",
                    "facts": "core/facts/udc/setting",
                    "contracts": "docs/operation-contracts/udc/setting",
                    "scripts": "tools/core/setting"},
    "entity":      {"label": "实体",     "impl": "components/udc",
                    "facts": "core/facts/udc/entity",
                    "contracts": "docs/operation-contracts/udc/entity",
                    "scripts": "tools/core/setting"},
    "application": {"label": "应用",     "impl": "components/udc",
                    "facts": "core/facts/udc/application",
                    "contracts": "docs/operation-contracts/udc/application",
                    "scripts": "tools/core/audit"},
    "menu":        {"label": "菜单",     "impl": "components/udc",
                    "facts": "core/facts/udc/menu",
                    "contracts": "docs/operation-contracts/udc/menu",
                    "scripts": "tools/core/audit"},
    "rule":        {"label": "规则",     "impl": "components/udc",
                    "facts": "core/facts/udc/rule",
                    "contracts": "docs/operation-contracts/udc/rule",
                    "scripts": "tools/core/audit"},
    "microflow":   {"label": "流程/微流程", "impl": "components/udc",
                    "facts": "core/facts/udc/microflow",
                    "contracts": "docs/operation-contracts/udc/microflow",
                    "scripts": "tools/core/setting"},
    "bi":          {"label": "BI",       "impl": "components/udc",
                    "facts": "core/facts/udc/bi",
                    "contracts": "docs/operation-contracts/udc/bi",
                    "scripts": "tools/core/audit"},
    "column":      {"label": "栏目",     "impl": "components/udc",
                    "facts": "core/facts/udc/column",
                    "contracts": "docs/operation-contracts/udc/column",
                    "scripts": "tools/core/audit"},
    "role":        {"label": "角色",     "impl": "components/udc",
                    "facts": "core/facts/udc/role",
                    "contracts": "docs/operation-contracts/udc/role",
                    "scripts": "tools/core/audit"},
}


def _py_files(rel: str) -> list[str]:
    d = REPO / rel
    if not d.is_dir():
        return []
    return sorted(p.relative_to(REPO).as_posix() for p in d.rglob("*.py"))


def _md_files(rel: str) -> list[str]:
    d = REPO / rel
    if not d.is_dir():
        return []
    return sorted(p.relative_to(REPO).as_posix() for p in d.rglob("*.md"))


def _contracts(rel: str) -> int:
    """该域登记了多少条 operation 契约（从 registry 实读，不手写）。"""
    try:
        sys.path.insert(0, str(REPO))
        from components.platform_operations.registry import UdcOperationRegistry
        reg = UdcOperationRegistry.default()
        return sum(1 for c in reg._contracts.values() if c.path)
    except Exception:
        return 0


def build() -> dict:
    out = {"repo": str(REPO), "domains": {}, "gaps": []}
    # registry 必须在 sys.path 就位后导入（脚本可能被从任意 cwd 调用）
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    try:
        from components.platform_operations.registry import UdcOperationRegistry
        reg = UdcOperationRegistry.default()
        all_contracts = len(list(reg._contracts.values()))
        write_contracts = sum(1 for c in reg._contracts.values() if c.write)
    except Exception as exc:  # 契约读不到必须显式暴露，不能静默报 0
        all_contracts = write_contracts = -1
        out["registry_error"] = f"{type(exc).__name__}: {exc}"
    out["contracts_total"] = all_contracts
    out["contracts_write"] = write_contracts

    for key, spec in DOMAINS.items():
        impl = _py_files(spec["impl"])
        facts = _md_files(spec["facts"])
        contracts = _md_files(spec["contracts"])
        scripts = _py_files(spec["scripts"]) if spec.get("scripts") else []
        entry = {
            "label": spec["label"],
            "impl_files": len(impl),
            "fact_files": len(facts),
            "contract_files": len(contracts),
            "script_files": len(scripts),
            "facts": facts,
            "contracts": contracts,
            "has_fact_grid": any("create.md" in f for f in facts),
        }
        out["domains"][key] = entry
        if not facts:
            out["gaps"].append(f"{key}（{spec['label']}）缺事实格 —— core/facts/udc/{key}/")
    # skill
    sk = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
    out["skills"] = sk
    return out


def render(data: dict) -> str:
    L = []
    L.append("=" * 74)
    L.append("Seeyon Agent 能力清单（实测自仓库文件，非手写维护）")
    L.append("=" * 74)
    L.append(f"仓库    {data['repo']}")
    L.append(f"操作契约 {data['contracts_total']} 条（其中声明写面 {data['contracts_write']} 条）")
    L.append("")
    L.append(f"{'域':<14}{'实现':>5}{'事实':>5}{'契约':>5}{'脚本':>5}  状态")
    L.append("-" * 74)
    for key, e in data["domains"].items():
        gap = "⚠ 缺事实格" if not e["fact_files"] else (
            "✅ 完整" if e["has_fact_grid"] else "○ 有契约无事实格")
        L.append(f"  {e['label']:<12}{e['impl_files']:>5}{e['fact_files']:>5}"
                 f"{e['contract_files']:>5}{e['script_files']:>5}  {gap}")
    L.append("")
    L.append("=== 各域事实与契约落位 ===")
    for key, e in data["domains"].items():
        if not e["facts"] and not e["contracts"]:
            continue
        L.append(f"\n[{e['label']}]")
        for f in e["facts"]:
            L.append(f"  事实  {f}")
        for f in e["contracts"]:
            L.append(f"  契约  {f}")
    L.append("")
    L.append(f"=== 仓库内 skill（{len(data['skills'])} 个）===")
    for s in data["skills"]:
        L.append(f"  {s}")
    if data["gaps"]:
        L.append("")
        L.append("=== 缺口 ===")
        for g in data["gaps"]:
            L.append(f"  {g}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    data = build()
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render(data))
    if a.check:
        return 1 if data["gaps"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

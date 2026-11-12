"""能力登记（P6）：把能力矩阵 + 证据目录变成可查询、可校验、可回填的结构。

设计目标（不是又一份文档，而是闭环）：
  1. 读 `core/facts/udc/microflow/capability-matrix.md` → 结构化能力表
  2. 读 `evidence/*.json` → 每个节点类型的证据文件
  3. `advisory(schema)` → 生成出来的流程里，哪些节点类型还没有运行证据（生成时就能看见）
  4. `record_evidence(...)` → 一次真实验证完成后，证据落盘 + 矩阵该行等级自动更新

★ 等级只能由真实运行证据提升，不能手工写高。`record_evidence` 要求 payload 里带
  `cases`（每条含 pass=True 与 before/after 或等价读侧断言），否则拒绝写入。

★ 自报 pass ≠ 证据（`classify_case`）：`{"case": ..., "pass": true}` 单独一条什么也
  证明不了——既不能证明来源（哪次运行）、也不能证明版本、更不能证明覆盖范围。
  因此证据分成三档：`self_report`（只有 pass，仅留痕）/ `trace`（有可比对的回读标记）/
  `readback`（expect 与回读数值一致）。只有后两档、且证据文件带运行来源
  （`_has_run_provenance`）时才算 `evidence_provenance`，`evidence_backed` 才为真。
  证据文件里的 `not_covered` 不吞掉：advisory 对已验类型照样点名未覆盖范围。
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
MATRIX = os.path.join(ROOT, "core", "facts", "udc", "microflow", "capability-matrix.md")
EVIDENCE_DIR = os.path.join(ROOT, "core", "facts", "udc", "microflow", "evidence")

LEVELS = ("RUNTIME_VERIFIED", "LIVE_EXECUTED", "BUILD_VERIFIED", "SCHEMA_VERIFIED",
          "CONSTRUCTED", "NONE")

_ROW = re.compile(r"^\|\s*([A-Z_]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+%)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|")


@dataclass
class Capability:
    action: str
    instances: int
    pct: str
    builder: str
    dsl: str
    note: str = ""
    evidence: list = field(default_factory=list)
    evidence_passed: int = 0          # 所有 pass=True 用例（含自报）
    evidence_provenance: int = 0      # 有运行来源 + 可比对回读的通过用例
    evidence_contradictions: int = 0  # pass=True 但与数值回读矛盾的用例
    not_covered: list = field(default_factory=list)

    @property
    def level(self) -> str:
        """矩阵声明的最高档。**这是声明，不是证据**（见 evidence_backed）。"""
        match = re.match(r"^\s*(?:\*\*)?(" + "|".join(LEVELS) + r")(?![A-Z_])", self.note)
        return match.group(1) if match else "NONE"

    @property
    def scope(self) -> str:
        """范围限定：note 里「（…）」中的形态说明 + 「未验」片段。"""
        out = []
        m = re.search(r"[（(]([^）)]*)[）)]", self.note)
        if m:
            out.append(m.group(1))
        for seg in re.findall(r"([^。；|]*未验[^。；|]*)", self.note):
            out.append(seg.strip())
        return "；".join(x for x in out if x)

    @property
    def verified(self) -> bool:
        """矩阵是否声明到 RUNTIME_VERIFIED。保持旧语义，只代表声明。"""
        return self.level == "RUNTIME_VERIFIED"

    @property
    def evidence_backed(self) -> bool:
        """是否有**可追溯到来源**的运行证据。

        与 level 分离：矩阵自述 RUNTIME_VERIFIED 但没有证据文件、证据里只有自报
        pass（无来源/无可比对回读）、或证据用例自相矛盾，都不算有证据。
        """
        return bool(self.evidence) and self.evidence_provenance > 0


# 运行来源：既要有「在哪跑」（应用/环境），也要有「哪一次」（日期/流程/构建）。
_RUN_SCOPE_KEYS = ("app_id", "appId", "application_id", "env")
_RUN_TRACE_KEYS = ("date", "flow", "mid", "microflowId", "build", "builds",
                   "run", "run_log")

_MISSING = object()


def _has_run_provenance(payload: dict) -> bool:
    """证据文件是否说清「哪一次运行」——否则回读值无法归因。"""
    has_scope = any(payload.get(k) for k in _RUN_SCOPE_KEYS)
    has_trace = any(payload.get(k) for k in _RUN_TRACE_KEYS)
    return bool(has_scope and has_trace)


def _numeric(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def classify_case(case) -> str:
    """单条用例的证据强度，返回 'readback' / 'trace' / 'self_report' /
    'contradicted' / 'not_pass'。

    - readback：`expect` 与 `after`/`actual`/`observed` 都是数值且相等
    - trace：带 `evidence` 回读标记，或有 before/after 差分
    - contradicted：`pass=True` 但数值回读与 `expect` 不符（自相矛盾）
    - self_report：只有 pass=True，别的什么都没有
    """
    if not isinstance(case, dict) or case.get("pass") is not True:
        return "not_pass"
    exp = case.get("expect", _MISSING)
    got = next((case[k] for k in ("after", "actual", "observed") if k in case),
               _MISSING)
    if exp is not _MISSING and got is not _MISSING and _numeric(exp) and _numeric(got):
        return "readback" if float(exp) == float(got) else "contradicted"
    if case.get("evidence"):
        return "trace"
    if "before" in case and "after" in case:
        return "trace"
    return "self_report"


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def load(matrix_path: str = MATRIX, evidence_dir: str = EVIDENCE_DIR) -> dict:
    """返回 {action: Capability}。证据按 JSON 里的 `node` 字段挂到对应类型。"""
    caps: dict[str, Capability] = {}
    if not os.path.isfile(matrix_path):
        raise FileNotFoundError("capability matrix unavailable")
    if os.path.exists(matrix_path):
        for line in _read(matrix_path).splitlines():
            m = _ROW.match(line.strip())
            if not m:
                continue
            act, n, pct, builder, dsl, note = m.groups()
            caps[act] = Capability(act, int(n), pct, builder.strip(), dsl.strip(),
                                   note.strip())
    if not caps:
        raise ValueError("capability matrix has no recognized rows")
    if os.path.isdir(evidence_dir):
        for fn in sorted(os.listdir(evidence_dir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(evidence_dir, fn)
            try:
                payload = json.loads(_read(path))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            node = (payload.get("node") or "").upper()
            if node in caps:
                caps[node].evidence.append(fn)
                # ★ 只数机器可判定的通过用例（cases / assertions 两种既有形态）。
                #   散文式证据（run.success、notes）不计入，避免把叙述当证据。
                # ★ 但「写了 pass=True」不等于「证明得了」：只有可追溯来源、且
                #   不自我矛盾的用例才计入 evidence_provenance（见 classify_case）。
                prov = _has_run_provenance(payload)
                for key in ("cases", "assertions"):
                    for c in payload.get(key) or []:
                        verdict = classify_case(c)
                        if verdict == "not_pass":
                            continue
                        caps[node].evidence_passed += 1
                        if verdict == "contradicted":
                            caps[node].evidence_contradictions += 1
                        elif verdict in ("readback", "trace") and prov:
                            caps[node].evidence_provenance += 1
                for x in payload.get("not_covered") or []:
                    if x not in caps[node].not_covered:
                        caps[node].not_covered.append(x)
    return caps


def summary(caps: dict | None = None) -> dict:
    caps = load() if caps is None else caps
    total = sum(c.instances for c in caps.values()) or 1
    out = {}
    for lv in LEVELS:
        group = [c for c in caps.values() if c.level == lv]
        if group:
            out[lv] = {"classes": len(group),
                       "instances": sum(c.instances for c in group),
                       "pct": round(100 * sum(c.instances for c in group) / total, 1),
                       "actions": sorted(c.action for c in group)}
    return out


def advisory(schema: dict, caps: dict | None = None) -> list:
    """生成结果里哪些节点类型还没有运行证据。

    返回 ["RETRIEVE_ARRAY: 未达 RUNTIME_VERIFIED（当前 SCHEMA_VERIFIED）", ...]
    同一类型只报一次，保持出现顺序。

    矩阵声明与证据分离：note 里写着 RUNTIME_VERIFIED 但没有机器可读通过证据时，
    一律报 UNVERIFIED 并点明「矩阵声明」，不把声明当证据。

    三种缺口分开说，不合并成一句「无证据」：
      1. 声明到 RUNTIME_VERIFIED 但只有自报 pass → 「仅有自报通过，缺来源/回读」
      2. 用例 pass 与数值回读矛盾 → 「回读与预期矛盾」
      3. 证据够但 not_covered 非空 → 「已验范围内 X，未覆盖 Y」（不报 UNVERIFIED）
    """
    caps = load() if caps is None else caps
    seen, out = set(), []
    def judge(act, c):
        if c is None:
            return "%s: UNVERIFIED（能力矩阵未收录）" % act
        if not c.verified:
            return "%s: 未达 RUNTIME_VERIFIED（当前 %s）" % (act, c.level)
        if c.evidence_contradictions:
            return ("%s: UNVERIFIED（矩阵声明 RUNTIME_VERIFIED，但 %d 条用例 "
                    "pass=True 与数值回读矛盾）" % (act, c.evidence_contradictions))
        if not c.evidence_backed:
            if c.evidence_passed:
                return ("%s: UNVERIFIED（矩阵声明 RUNTIME_VERIFIED，但只有 %d 条自报"
                        "通过，缺运行来源或可比对回读）" % (act, c.evidence_passed))
            return ("%s: UNVERIFIED（矩阵声明 RUNTIME_VERIFIED，"
                    "但无机器可读通过证据）" % act)
        if c.not_covered:
            return ("%s: 已验（%d 条可追溯用例），未覆盖 %d 项：%s"
                    % (act, c.evidence_provenance, len(c.not_covered),
                       "；".join(str(x) for x in c.not_covered)))
        return None
    def walk(ns):
        for n in ns or []:
            if not isinstance(n, dict):
                continue
            act = n.get("actionType") or n.get("type")
            if act and act not in seen:
                seen.add(act)
                msg = judge(act, caps.get(act))
                if msg:
                    out.append(msg)
            walk(n.get("nodes"))
            for cond in n.get("conditions") or []:
                walk(cond.get("nodes"))
    walk(schema.get("nodes"))
    return out


def record_evidence(action: str, payload: dict, *, level: str = "RUNTIME_VERIFIED",
                    note: str | None = None, matrix_path: str = MATRIX,
                    evidence_dir: str = EVIDENCE_DIR) -> str:
    """一次真实验证完成后调用：证据落盘 + 矩阵该行等级更新。

    ★ 拒绝没有通过用例的 payload —— 等级只能由真实运行证据提升。
    ★ 通过用例也要能追溯来源：只有自报 `pass=True`（无回读标记、无运行来源）时，
      证据照样落盘留痕，但**不写矩阵等级**（不改声明、也不伪造提升）。
    """
    action = action.upper()
    cases = payload.get("cases") or []
    passed = [c for c in cases if isinstance(c, dict) and c.get("pass") is True]
    if not passed:
        raise ValueError("%s 没有 pass=True 的用例，不能提升等级" % action)
    # 证据强度按用例分类，和 load() 用同一把尺子，避免「写进去算数、读出来不算」。
    traceable = [c for c in passed if classify_case(c) in ("readback", "trace")]
    upgrade = bool(traceable) and _has_run_provenance(payload)
    payload.setdefault("evidence_strength",
                       "readback" if upgrade else "self_report")
    if not upgrade:
        payload.setdefault("_upgrade_blocked",
                           "仅自报 pass 或无运行来源（app/env + date/flow/build），"
                           "不提升矩阵等级")
    os.makedirs(evidence_dir, exist_ok=True)
    fn = "%s-runtime-%s.json" % (action.lower(), payload.get("date")
                                 or time.strftime("%Y-%m-%d"))
    path = os.path.join(evidence_dir, fn)
    payload.setdefault("node", action)
    # ★ 同一天第二次验证不能覆盖第一次的证据（audit 必须是只增不改）：
    #   已有文件时合并 cases（按 case 文本去重、新覆盖旧）与 not_covered。
    if os.path.exists(path):
        try:
            old = json.load(open(path, encoding="utf-8"))
        except Exception:
            old = None
        if isinstance(old, dict):
            merged = []
            seen = set()
            for c in (payload.get("cases") or []):
                merged.append(c)
                seen.add(str(c.get("case")))
            for c in (old.get("cases") or []):
                if str(c.get("case")) in seen:
                    continue
                merged.append(c)
            for k, v in old.items():
                if k == "cases" or k in payload:
                    continue
                payload[k] = v
            nc = list(payload.get("not_covered") or [])
            for x in (old.get("not_covered") or []):
                if x not in nc:
                    nc.append(x)
            if nc:
                payload["not_covered"] = nc
            payload["cases"] = merged
            payload["supersedes"] = old.get("supersedes") or []
            payload["runs"] = (old.get("runs") or 1) + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    text = _read(matrix_path)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _ROW.match(line.strip())
        if not m or m.group(1) != action:
            continue
        if not upgrade:
            break          # 证据已落盘，矩阵声明保持原样（不升也不降）
        cells = line.strip().strip("|").split("|")
        new_note = note or ("**%s**（%d 条用例通过，证据 %s）"
                            % (level, len(traceable), fn))
        cells[5] = " " + new_note + " "
        lines[i] = "|" + "|".join(cells) + "|"
        break
    else:
        raise KeyError("能力矩阵里没有 %s 这一行" % action)
    if upgrade:
        with open(matrix_path, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(lines) + "\n")
    return path


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="能力登记查询")
    ap.add_argument("action", nargs="?", help="节点类型，如 RETRIEVE_ARRAY")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    caps = load()
    if a.action:
        c = caps.get(a.action.upper())
        if not c:
            print("没有该节点类型:", a.action)
            return 1
        info = {"action": c.action, "instances": c.instances, "level": c.level,
                "evidence_backed": c.evidence_backed, "evidence_passed": c.evidence_passed,
                "evidence_provenance": c.evidence_provenance,
                "evidence_contradictions": c.evidence_contradictions,
                "not_covered": c.not_covered,
                "scope": c.scope, "evidence": c.evidence, "note": c.note}
        print(json.dumps(info, ensure_ascii=False, indent=1) if a.json
              else "%s: %s%s（%d 实例）\n  范围: %s\n  证据: %s\n  可追溯用例: %d/%d"
              % (c.action, c.level, "" if c.evidence_backed else " [UNVERIFIED: 无机器可读通过证据]",
                 c.instances, c.scope or "-", ", ".join(c.evidence) or "-",
                 c.evidence_provenance, c.evidence_passed))
        if c.not_covered:
            print("  未覆盖: %s" % "；".join(str(x) for x in c.not_covered))
        return 0
    s = summary(caps)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=1))
        return 0
    for lv, v in s.items():
        print("%-18s %2d 类 %5.1f%%  %s" % (lv, v["classes"], v["pct"],
                                            ",".join(v["actions"])[:80]))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

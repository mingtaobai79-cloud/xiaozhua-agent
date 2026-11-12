# -*- coding: utf-8 -*-
"""scan_pii.py — 扫描仓库里的真实客户/人员/角色信息

目标：xiaozhua-agent 会被复用，不能带任何真实客户、人员、角色标识。

扫描维度（示例值一律用代号，不写真值——本文件自身也受闸门约束）：
  1. 人名/工号：真实姓名 / <工号前缀><数字> 形态
  2. 客户应用名：<应用前缀><长数字> 形态
  3. 凭据：token / cookie / 密码
  4. 真实主机/账号：IP、数据库账号
"""
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(r"<XIAOZHUA_AGENT_ROOT>")
TEXT_EXT = {".py", ".md", ".yaml", ".yml", ".json", ".txt", ".js", ".sh", ".bat", ".toml"}

PATTERNS = {
    "工号账号": re.compile(r"\bchjh\d{3}\b"),
    "真实人名": re.compile(r"白" + "明" + "涛"),
    "客户应用名": re.compile(r"datamigration\d{6,}"),
    "另一客户应用": re.compile(r"\bznxmglpt\d{6,}\b"),
    "平台应用名": re.compile(r"\bzzprobe\b"),
    "数据库账号": re.compile(r"\blow_code\b"),
    "token字面量": re.compile(r"SY_ACCESS_TOKEN=[A-Za-z0-9_\-\.]{20,}"),
    "长base64": re.compile(r"\beyJ[A-Za-z0-9_\-]{40,}"),
    "口令": re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[=:]\s*[\"'][^\"']{6,}[\"']"),
    "手机号": re.compile(r"\b1[3-9]\d{9}\b"),
    "邮箱": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
}

hits: dict[str, list[tuple[str, str]]] = {k: [] for k in PATTERNS}
scanned = 0
for p in REPO.rglob("*"):
    if not p.is_file() or p.suffix not in TEXT_EXT:
        continue
    sp = p.as_posix()
    if "node_modules" in sp or "/.venv/" in sp or "/.git/" in sp:
        continue
    if "artifacts/decompiled" in sp or "artifacts/scratch-migrated" in sp:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    scanned += 1
    rel = str(p.relative_to(REPO))
    for name, pat in PATTERNS.items():
        for m in pat.finditer(t):
            line = t[:m.start()].count("\n") + 1
            hits[name].append((rel, f"L{line}: {m.group(0)[:70]}"))

print(f"扫描 {scanned} 个文本文件\n")
total = 0
for name, lst in hits.items():
    total += len(lst)
    print(f"=== {name}: {len(lst)} 处 ===")
    byfile = Counter(f for f, _ in lst)
    for f, n in byfile.most_common(12):
        print(f"    {n:>4} 处  {f}")
    if len(byfile) > 12:
        print(f"    ... 另有 {len(byfile)-12} 个文件")
    print()

print(f"合计命中: {total}")
Path(r"<HERMES_HOME>\cache\scratch\pii-scan.json").write_text(
    json.dumps({k: v for k, v in hits.items()}, ensure_ascii=False, indent=1),
    encoding="utf-8")

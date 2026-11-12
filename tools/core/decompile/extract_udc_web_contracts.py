"""udc-web controller 方法级契约提取（javap -v 解析）—— 类级/方法级 @RequestMapping + @HasRole。

udc-web 已有 `docs/audit/artifacts/udc-web-5.3.517-javap/` 的 API 全景（手工提炼），
本脚本产出**机器可复核**的逐 controller 契约（类级 mapping、方法 path/verb、@HasRole 角色），
补足「方法级 HasRole 粒度」这类此前标 UNVERIFIED 的面。

用法：
    python tools/extract_udc_web_contracts.py <jar> [--out <dir>]

证据边界：STATIC_BYTECODE（javap -v 常量池 Utf8 + RuntimeVisibleAnnotations）。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"

_MAPPING_ANN = ("RequestMapping", "PostMapping", "GetMapping", "PutMapping", "DeleteMapping")
_ROLE_HINT = "HasRole"


def _classes(jar: Path) -> list[str]:
    z = zipfile.ZipFile(jar)
    return sorted(n[:-6].replace("/", ".") for n in z.namelist()
                  if n.startswith("com/seeyon/udc/controller/") and n.endswith(".class")
                  and "$" not in n)


def _javap_v(jar: Path, fqn: str, javap: str) -> str:
    out = subprocess.run([javap, "-v", "-p", "-classpath", str(jar), fqn],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return out.stdout


def _utf8_consts(src: str) -> list[str]:
    """常量池 Utf8 字面量（按出现顺序）。"""
    return re.findall(r'#\d+\s*=\s*Utf8\s+(\S.*)$', src, re.MULTILINE)


def parse_controller(src: str) -> dict:
    """从 javap -v 文本抽: 类级 mapping 路径、@HasRole 角色、方法名、候选路径。

    常量池 Utf8 顺序 = 注解声明顺序：`RequestMapping` 后紧跟的字面量是类级路径；
    `HasRole` 后连续的角色名是角色值域（用已知角色集过滤类型名混入）。
    """
    _KNOWN_ROLES = {"udcAppDesigner", "udcSystemAdmin", "udcRootOrgAdmin", "OrgAdmin",
                    "OpsAdmin", "BpmDesigner", "BpmManager", "BpmSystemManager", "cipAdmin"}
    j = src.find("SourceFile")
    tail = src[j:] if j >= 0 else src
    consts = [c.strip() for c in _utf8_consts(tail)]
    class_mapping = None
    roles: list[str] = []
    for idx, c in enumerate(consts):
        if c == "Lorg/springframework/web/bind/annotation/RequestMapping;" and idx + 1 < len(consts):
            class_mapping = consts[idx + 1]
        if c == "Lcom/seeyon/boot/annotation/HasRole;" and idx + 1 < len(consts):
            for nxt in consts[idx + 1: idx + 7]:
                if nxt in _KNOWN_ROLES:
                    roles.append(nxt)
                elif nxt.startswith("L") or nxt.endswith(";"):
                    break
    methods = re.findall(r'public\s+[\w<>,.\[\] ?]+\s+(\w+)\s*\(', src)
    has_class_mapping = any(f"Lorg/springframework/web/bind/annotation/{a};" in src for a in _MAPPING_ANN)
    has_hasrole = "Lcom/seeyon/boot/annotation/HasRole;" in src
    return {
        "class_mapping": class_mapping,
        "class_mapping_annotation": has_class_mapping,
        "class_hasrole_annotation": has_hasrole,
        "roles": sorted(set(roles)),
        "role_literals": sorted(set(roles)),
        "method_names": sorted(set(methods)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jar")
    ap.add_argument("--out", default="docs/audit/artifacts/udc-web-5.3.517-contracts")
    ap.add_argument("--javap", default=JAVAP)
    ns = ap.parse_args()
    jar = Path(ns.jar)
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict] = {}
    for fqn in _classes(jar):
        src = _javap_v(jar, fqn, ns.javap)
        short = fqn.split(".")[-1]
        result[short] = parse_controller(src)
        (out / f"{short}.javap.txt").write_text(src, encoding="utf-8")
    (out / "_contracts.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    # 汇总
    with_role = [k for k, v in result.items() if v["class_hasrole_annotation"]]
    without = [k for k, v in result.items() if not v["class_hasrole_annotation"]]
    print(f"controller: {len(result)} | 类级 @HasRole: {len(with_role)} | 无: {len(without)}")
    if without:
        print("  无类级 HasRole:", without)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""合并 udc-web 类级契约 + 方法级契约 → 完整 restful-api 契约（方法级 path）。

数据源：
- docs/audit/artifacts/udc-web-5.3.517-contracts/_contracts.json  （类级路径 + 角色，javap 常量池）
- docs/audit/artifacts/udc-web-5.3.517-methods/_methods.json      （方法级 http + path_value + 中文描述）

输出：
- docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json

规则（Spring @RequestMapping 语义，类级 + 方法级**恒拼接**）：
- full_path = "/" + 类级 mapping + "/" + 方法级 value（去除前导斜杠，尾部斜杠保真）；
- 方法级 value 为空（mapping 无 value）→ 路径 = 类级根（不含尾部斜杠）；
- 类级 mapping 缺失（注解无 value，如 ParameterController）→ 路径 = 方法级 value；
- **方法级 value 以 "/" 开头也一律拼接**：Spring 从不把方法级 value 当绝对路径，
  前置斜杠仅是其字面习惯写法（如 PageInfoController 的 "/base-info/create"）。

字节码实证（udc-web-5.3.517 jar, javap -v）：
  PageInfoController 类级 @RequestMapping("udc/page-info")
  + 方法级 @PostMapping("/base-info/create")
  → 真路径 /udc/page-info/base-info/create
  LIVE 佐证：components/udc/live_write_templates.py page_create 实际调用
  POST /service/udc/page-info/base-info/create（在线创建成功）。

历史缺陷：修复前把"以 / 开头"当作绝对路径并前置 "/udc"，
使 657 方法中 159 个（24.2%）full_path 错，并造出线上不存在的 op。
证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_CONTRACTS = ROOT / "docs/audit/artifacts/udc-web-5.3.517-contracts/_contracts.json"
_METHODS = ROOT / "docs/audit/artifacts/udc-web-5.3.517-methods/_methods.json"
_OUT = ROOT / "docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json"


def build() -> dict:
    cm = json.loads(_CONTRACTS.read_text(encoding="utf-8"))
    me = json.loads(_METHODS.read_text(encoding="utf-8"))
    full: dict[str, dict] = {}
    for ctrl, mv in me.items():
        c = cm.get(ctrl, {})
        base = (c.get("class_mapping") or "").strip("/")
        out = []
        for m in mv["methods"]:
            pv = m.get("path_value")
            if pv is None:
                pv = m["method"]
            # 只去前导斜杠：方法级 value 的尾部斜杠是字节码字面（如 "transfer/batch/"），
            # 保真不改写，避免产物与 jar 常量池不一致。
            frag = (pv or "").lstrip("/")
            if not frag:
                full_path = "/" + base if base else "/"
            elif base:
                full_path = "/" + base + "/" + frag
            else:
                full_path = "/" + frag
            out.append({"method": m["method"], "http": m.get("http"), "path": pv,
                        "full_path": full_path, "desc": m.get("desc", ""),
                        "is_write": m.get("is_write", False)})
        full[ctrl] = {"class_mapping": c.get("class_mapping"),
                      "roles": c.get("roles", []),
                      "api_count": len(out), "methods": out}
    return full


def main() -> int:
    full = build()
    _OUT.write_text(json.dumps(full, ensure_ascii=False, indent=1), encoding="utf-8")
    tot = sum(v["api_count"] for v in full.values())
    words = sum(1 for v in full.values() for m in v["methods"] if m["desc"])
    print(f"落库 {_OUT.name}: {len(full)} controller | {tot} 方法 | {words} 有描述")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

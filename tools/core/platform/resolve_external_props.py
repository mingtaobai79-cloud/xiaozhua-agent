#!/usr/bin/env python3
"""补全「组件 props 指向外部包类型」的缺口。

问题：@seeyon/ui 的组件大量是 `React.FC<AlertProps>`，而 `AlertProps` 来自 `antd`。
抽取器只扫包内 d.ts，所以 16 个 antd 派生组件的 props 是空的。

做法：
  1. 扫外部包（默认 antd）的 d.ts，建「类型名 → 字段表」索引
  2. 对 signatures.json 里 props 为空的组件，按 propsType 命中索引 → 挂上字段
  3. 打 `propsFrom` 标记来源，下游一眼看出「这是 antd 的 props，不是平台自造」

用法：
  python tools/core/platform/resolve_external_props.py \
      --signatures docs/audit/artifacts/frontend-surface-20261102/signatures.json \
      --node-modules <PATH> \
      --externals antd
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from extract_extension_surface import (  # noqa: E402
    RE_IFACE, RE_TYPE_OBJ, _block_at, parse_props_fields,
)


RE_TYPE_ALIAS = re.compile(
    r"(?:export\s+)?(?:declare\s+)?type\s+(\w+)\s*(?:<[^>]*>)?\s*=\s*"
    r"(Omit|Pick|Partial|Required)<\s*([\w.$]+)\s*(?:,\s*([^>]*))?\s*>")


def index_package(root: Path) -> dict[str, dict]:
    """把一个包的 d.ts 全扫一遍，返回 {类型名: {fields, extends, from}}。"""
    idx: dict[str, dict] = {}
    files = sorted(root.rglob("*.d.ts"))
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(root)).replace("\\", "/")
        for rx in (RE_IFACE, RE_TYPE_OBJ):
            for m in rx.finditer(t):
                name = m.group(1)
                body = _block_at(t, m.end() - 1)
                fields = parse_props_fields(body)
                entry = {"kind": "interface" if rx is RE_IFACE else "type",
                         "fields": fields, "from": rel}
                if rx is RE_IFACE and m.lastindex and m.lastindex >= 2 and m.group(2):
                    entry["extends"] = m.group(2).strip()
                if fields or entry.get("extends"):
                    # 同名多处定义时保留字段最多的那份
                    old = idx.get(name)
                    if old is None or len(fields) > len(old["fields"]):
                        idx[name] = entry
        # `type X = Omit<Y, 'k'>` 这类别名（无花括号），记下来供 _expand 解引用
        for m in RE_TYPE_ALIAS.finditer(t):
            name, op, target, arg = m.group(1), m.group(2), m.group(3), m.group(4) or ""
            keys = re.findall(r"['\"](\w+)['\"]", arg)
            if name not in idx:
                idx[name] = {"kind": "alias", "op": op, "target": target.split(".")[-1],
                             "keys": keys, "fields": [], "from": rel}
    return idx


def _expand(idx: dict[str, dict], name: str, depth: int = 0) -> dict:
    """沿 extends / Omit 别名链合并字段（antd 的 Props 常是层层继承，字段在父类型里）。"""
    hit = idx.get(name)
    if not hit or depth > 4:
        return {"fields": [], "extends": ""}
    if hit.get("kind") == "alias":
        base = _expand(idx, hit["target"], depth + 1)
        fields = base["fields"]
        if hit.get("op") in ("Omit", "Pick") and hit.get("keys"):
            if hit["op"] == "Omit":
                fields = [f for f in fields if f["name"] not in hit["keys"]]
            else:
                fields = [f for f in fields if f["name"] in hit["keys"]]
        return {"fields": fields, "extends": f"{hit['op']}<{hit['target']}>"} 
    fields = list(hit["fields"])
    seen = {f["name"] for f in fields}
    parents = []
    ext = hit.get("extends") or ""
    if ext:
        for part in ext.split(","):
            for tok in re.findall(r"[A-Za-z_$][\w$]*", part):
                if tok in ("Omit", "Pick", "Partial", "Required", "Readonly", "Exclude", "Extract"):
                    continue
                parents.append(tok)
    for p in parents:
        sub = _expand(idx, p, depth + 1)
        for f in sub["fields"]:
            if f["name"] not in seen:
                fields.append(f)
                seen.add(f["name"])
    if parents:
        ext = (ext + "," if ext else "") + "→" + ",".join(parents)
    return {"fields": fields, "extends": ext}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signatures", required=True)
    ap.add_argument("--node-modules", required=True)
    ap.add_argument("--externals", nargs="+", default=["antd"])
    a = ap.parse_args()

    nm = Path(a.node_modules)
    ext_idx: dict[str, dict] = {}
    for pkg in a.externals:
        # antd 的类型在 es/，也有 lib/（老版本）
        for sub in ("es", "lib", ""):
            root = nm / pkg / sub
            if root.is_dir() and any(root.rglob("*.d.ts")):
                idx = index_package(root)
                for k, v in idx.items():
                    old = ext_idx.get(k)
                    if old is None or len(v["fields"]) > len(old["fields"]):
                        v = dict(v, pkg=pkg)
                        ext_idx[k] = v
                print(f"  {pkg}/{sub}: {len(idx)} 个类型")

    sig = json.loads(Path(a.signatures).read_text(encoding="utf-8"))
    pkgs = sig["sources"]["frontend"]["packages"]

    filled = []
    still = []
    for pname, p in pkgs.items():
        for cname, info in (p.get("components") or {}).items():
            if info.get("props"):
                continue
            pt = info.get("propsType") or ""
            hit = ext_idx.get(pt)
            if hit:
                exp = _expand(ext_idx, pt)
                if exp["fields"]:
                    info["props"] = exp["fields"]
                    info["propsFrom"] = f"{hit.get('pkg')}:{hit['from']}"
                    if exp["extends"]:
                        info["propsExtends"] = exp["extends"]
                    filled.append((pname, cname, pt, len(exp["fields"])))
                    continue
            still.append((pname, cname, pt))

    Path(a.signatures).write_text(json.dumps(sig, ensure_ascii=False), encoding="utf-8")

    print(f"\n补全 {len(filled)} 个组件：")
    for pname, cname, pt, n in filled:
        print(f"  {pname.split('/')[-1]:20s} {cname:26s} {pt:26s} {n:3d} 字段")
    print(f"\n仍无 props {len(still)} 个：")
    for pname, cname, pt in still:
        print(f"  {pname.split('/')[-1]:20s} {cname:26s} {pt[:40]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

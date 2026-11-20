# -*- coding: utf-8 -*-
"""从字节码索引提取 facade 方法入参/返回 DTO 的字段级结构。

入参形态：SingleRequest<X> / ListRequest<X> / PageRequest<X> …
返回形态：SingleResponse<X> / ListResponse<X> / PageResponse<X> …
X 才是真正的 DTO；X 的字段来自索引里的 classes[fqcn].fields（含继承链，最多 3 层）。

输出：
  docs/audit/artifacts/dto/<slug>.json   完整结构
  docs/audit/artifacts/dto/DTO-<slug>.md 字段表
用法: python extract_dto_fields.py [slug ...]
"""
import json, io, os, re, sys
from collections import Counter

REPO = r"C:/Users/白明涛/xiaozhua-agent"
INDEX = os.path.join(REPO, "docs/audit/artifacts/extension-surface-full/interfaces-full.json")
OUT = os.path.join(REPO, "docs/audit/artifacts/dto")
FACADE = os.path.join(REPO, "docs/audit/artifacts/facade")

SKIP_DTO = {"PageRequest", "ListRequest", "SingleRequest", "PageResponse",
            "ListResponse", "SingleResponse", "PageInfo", "Sort", "Order",
            "BatchRequest", "BatchResponse", "MultiRequest", "MultiResponse"}

WRAPPER = re.compile(r"^(?:com\.seeyon\.boot\.transport\.)?"
                     r"(?:Single|List|Page|Batch|Multi|Tree|Map)?"
                     r"(?:Request|Response|Result|Dto)?<(.+)>$")
GENERIC = re.compile(r"^([\w\.\$]+)<(.+)>$")


def unwrap(t):
    """揭开 Response/Request 包装，返回内部类型（最多两层）。"""
    t = (t or "").strip()
    for _ in range(2):
        m = GENERIC.match(t)
        if not m:
            return t
        head, inner = m.group(1), m.group(2)
        if not (head.endswith("Request") or head.endswith("Response") or
                head.endswith("Wrapper") or head.endswith("Page")):
            return t
        t = inner.strip()
    return t


def split_generics(s):
    """把 'A<B>, C<D>' 这类参数串按顶层逗号切开并揭开包装。"""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [unwrap(x) for x in out if x.strip()]


def fields_of(idx, fqcn, depth=0, seen=None):
    seen = seen or set()
    if fqcn in seen or depth > 3:
        return []
    seen.add(fqcn)
    c = idx["classes"].get(fqcn)
    if not c:
        return []
    rows, names = [], set()
    own = []
    for f in (c.get("fields") or []):
        mods = f.get("modifiers") or []
        if "static" in mods:
            continue
        own.append({"name": f.get("name"), "type": f.get("type"),
                    "owner": fqcn.rsplit(".", 1)[-1]})
        names.add(f.get("name"))
    rows += own
    for ext in (c.get("extends") or []):
        for fl in fields_of(idx, ext, depth + 1, seen):
            if fl["name"] in names:      # 子类已声明，跳过父类同名字段
                continue
            names.add(fl["name"])
            rows.append(fl)
    return rows


def params(fqcn, m):
    """解析方法参数：'SingleRequest<OrgUnitDto> arg0' -> 内部类型。"""
    out = []
    for a in (m.get("raw_args") or []):
        t = a.rsplit(" ", 1)[0] if " " in a else a
        out.append(unwrap(t))
    return out


def main():
    slugs = sys.argv[1:] or [f[:-5] for f in sorted(os.listdir(FACADE)) if f.endswith(".json")]
    idx = json.load(io.open(INDEX, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)

    for slug in slugs:
        fp = os.path.join(FACADE, f"{slug}.json")
        if not os.path.exists(fp):
            print(f"  ! {slug}: 无 facade")
            continue
        d = json.load(io.open(fp, encoding="utf-8"))
        usage = Counter()
        wants = {}   # fqcn -> 来自哪个方法（示例）
        for f in d.get("facades", []):
            for m in f.get("methods", []):
                for t in params(f["fqcn"], m):
                    if t.startswith("com.seeyon") and t.rsplit(".", 1)[-1] not in SKIP_DTO:
                        usage[t] += 1
                        wants.setdefault(t, f"{f['name']}.{m['name']}(入参)")
                rt = unwrap(m.get("raw_returns") or "")
                if rt.startswith("com.seeyon") and rt.rsplit(".", 1)[-1] not in SKIP_DTO:
                    usage[rt] += 1
                    wants.setdefault(rt, f"{f['name']}.{m['name']}(返回)")

        dtos = {}
        for t, n in usage.most_common():
            fl = fields_of(idx, t)
            if not fl:
                dtos[t] = {"usage": n, "fields": [], "note": "索引里无该类字段（可能是枚举/接口/外部类型）"}
                continue
            dtos[t] = {"usage": n, "fields": fl, "example": wants.get(t, "")}

        io.open(os.path.join(OUT, f"{slug}.json"), "w", encoding="utf-8").write(
            json.dumps(dtos, ensure_ascii=False, indent=1))

        with_f = [(k, v) for k, v in dtos.items() if v["fields"]]
        with_f.sort(key=lambda kv: -kv[1]["usage"])
        L = [f"# 入参/返回 DTO 字段：{slug}", "",
             f"> 来源：字节码索引（`javap` 的 fields），{len(dtos)} 个 DTO，{len(with_f)} 个有字段。",
             "> 等级：`VERIFIED_STATIC_BYTECODE`。字段名即 JSON 键名（平台用 Jackson 默认命名）。",
             "> 包装类 `SingleRequest<T>` / `ListResponse<T>` 已揭开，下表是 T 的字段。", ""]
        for k, v in with_f:
            L.append(f"## `{k.rsplit('.', 1)[-1]}`  （在 {v['usage']} 处出现）")
            L.append("")
            if v.get("example"):
                L.append(f"> 例：`{v['example']}`")
                L.append("")
            L.append("| 字段 | 类型 | 声明于 |")
            L.append("|---|---|---|")
            for fl in v["fields"]:
                L.append(f"| `{fl['name']}` | `{fl['type']}` | {fl['owner']} |")
            L.append("")
        io.open(os.path.join(OUT, f"DTO-{slug}.md"), "w", encoding="utf-8").write("\n".join(L))
        print(f"  ✓ {slug}: {len(dtos)} DTO / {len(with_f)} 带字段 / 现场使用 {sum(usage.values())} 次")
    return 0


if __name__ == "__main__":
    sys.exit(main())
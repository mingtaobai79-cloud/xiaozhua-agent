# -*- coding: utf-8 -*-
"""抽取「UDC 扩展工程可用依赖面」——pom 依赖清单 + @seeyon 前端包导出符号。

回答的问题：一个 UDC 应用的**手写扩展工程**能用哪些平台的包/组件/方法？
用法由「工程实际解析到的依赖」决定，不是由平台全量构件决定。

三个数据源，全部只读：
  ① 后端  ext 工程 pom.xml 的 <dependency> 清单（含 parent pom 的依赖）
  ② 后端  编译期 classpath（target/compile_args.txt 的 -cp），= 实际可引用 jar 全集
  ③ 前端  package.json dependencies/devDependencies + node_modules/@seeyon/*/**.d.ts

输出 JSON 到 --emit，事实格引用它作为证据件（R-E8 三样：路径/复现/校验）。

用法：
    python tools/core/platform/extract_extension_surface.py \
        --backend <后端扩展工程根> \
        --frontend <前端扩展工程/pc 根> \
        --emit docs/audit/artifacts/extension-surface-<版本>/surface.json

不写死任何域名 / 客户应用名：路径与名称一律由参数或 pom 内容得出。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_pom_deps(pom: Path) -> list[dict]:
    """解析 pom 里的 <dependency>，返回 groupId/artifactId/version/scope。"""
    t = pom.read_text(encoding="utf-8", errors="replace")
    out = []
    for body in re.findall(r"<dependency>(.*?)</dependency>", t, re.S):
        def g(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", body, re.S)
            return m.group(1).strip() if m else ""
        d = {k: g(k) for k in ("groupId", "artifactId", "version", "scope")}
        # 注释行不算依赖
        if d["artifactId"]:
            out.append(d)
    return out


def parse_parent(pom: Path) -> dict:
    t = pom.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<parent>(.*?)</parent>", t, re.S)
    if not m:
        return {}
    b = m.group(1)

    def g(tag):
        mm = re.search(rf"<{tag}>(.*?)</{tag}>", b, re.S)
        return mm.group(1).strip() if mm else ""

    return {k: g(k) for k in ("groupId", "artifactId", "version")}


def resolve_parent_pom(pom: Path, parent: dict, repo: Path | None) -> Path | None:
    """在本地 maven 仓库里找 parent pom（<repo>/<group 路径>/<artifact>/<version>/）。"""
    if not repo or not parent.get("artifactId"):
        return None
    p = (repo / parent["groupId"].replace(".", "/") / parent["artifactId"]
         / parent["version"] / f"{parent['artifactId']}-{parent['version']}.pom")
    return p if p.exists() else None


def parse_classpath(compile_args: Path) -> list[str]:
    """从 javac argfile 首行 -cp 里抽出 jar 路径列表（去引号、去空项）。"""
    if not compile_args.exists():
        return []
    first = compile_args.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    m = re.search(r'-cp\s+(.*)$', first)
    if not m:
        return []
    raw = m.group(1)
    jars = []
    for part in raw.split(";"):
        p = part.strip().strip('"').strip()
        if p and p.lower().endswith(".jar"):
            jars.append(p.replace("\\", "/"))
    return jars


def jar_artifact(p: str) -> tuple[str, str]:
    """jar 路径 → (artifactId, version)，按 maven 仓库布局 <artifact>/<version>/<artifact>-<version>.jar。"""
    path = Path(p)
    ver = path.parent.name
    name = path.name
    suffix = f"-{ver}.jar"
    art = name[: -len(suffix)] if name.endswith(suffix) else path.stem
    # classifier 形态 artifact-1.0.0-sources.jar 之类不进本函数范围
    return art, ver


def find_hoisted_top_level(nm: Path) -> dict[str, str]:
    """顶层 node_modules 里的第三方包 → {包名: 版本}（含 @scope/name 形式）。

    为什么需要：实测存在「源码 import 了但 package.json 没声明」的包
    （传递依赖被 npm/yarn 提升到顶层）。它今天能编译，但不受 lockfile 保护。
    三态判定要靠这份清单把 HOISTED 与 MISSING 分开。

    ★ 不许设条数上限：实测按字母序截前 400 条时，lodash（第 600+ 位）
      被漏掉 → 已安装的包被判成「不存在」，是最典型的假缺口。
      只排除 @seeyon 自己的包（另有 seeyon_packages 收录）。
    """
    if not nm.is_dir():
        return {}
    out: dict[str, str] = {}

    def read_one(pkg_dir: Path, name: str) -> None:
        pj = pkg_dir / "package.json"
        if not pj.exists():
            return
        try:
            meta = json.loads(pj.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return
        out[name] = meta.get("version")

    for pkg in sorted(nm.iterdir()):
        if not pkg.is_dir():
            continue
        if pkg.name.startswith("@"):
            if pkg.name == "@seeyon":
                continue
            for sub in sorted(pkg.iterdir()):
                if sub.is_dir():
                    read_one(sub, f"{pkg.name}/{sub.name}")
            continue
        read_one(pkg, pkg.name)
    return out


def parse_package_json(pc: Path) -> dict:
    p = pc / "package.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    keep = ("name", "version", "scripts")
    out = {k: data[k] for k in keep if k in data}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        if data.get(k):
            out[k] = data[k]
    return out


# `export { A, B as C } from "..."` / `export * from` / `export type { ... }`
RE_EXPORT_LIST = re.compile(r"export\s+(?:type\s+)?\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", re.S)
RE_EXPORT_STAR = re.compile(r"export\s+\*\s+from\s*['\"]([^'\"]+)['\"]")
RE_DECLARE_CALLABLE = re.compile(
    r"export\s+declare\s+(?:const|function)\s+(\w+)\s*[:=]?\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?::\s*([^;]+))?",
    re.S)
# 各类导出声明（原实现只抓 declare const/function，漏掉 interface/type/class/enum/namespace）
RE_DECL_ALL = re.compile(
    r"export\s+(?:declare\s+)?(?:abstract\s+)?"
    r"(function|const|let|var|class|interface|type|enum|namespace)\s+(\w+)")
RE_EXPORT_AS_NS = re.compile(r"export\s+\*\s+as\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]")
# 一个正则覆盖两种形态：`export { A } from './x'`（有 from）与 `export { A }`（先 import 再导出）
RE_EXPORT_ANY = re.compile(
    r"export\s+(?:type\s+)?\{([^}]*)\}\s*(?:from\s*['\"]([^'\"]+)['\"])?", re.S)
# 文件级 declare（无 export 前缀）：`declare const X: ...` + 末尾 `export default X` 的包写法
RE_DECL_TOP = re.compile(
    r"^declare\s+(const|let|var|function|class|interface|type|enum|namespace)\s+(\w+)", re.M)
RE_EXPORT_DEFAULT = re.compile(
    r"export\s+default\s+(?:(?:abstract\s+)?class|function)?\s*(\w+)?")


def _clean_names(syms: str) -> list[str]:
    """`export { /**@deprecated */ Foo, Bar as Baz }` → ['Foo','Baz']，注释残渣直接丢弃。"""
    s = re.sub(r"/\*.*?\*/", " ", syms, flags=re.S)
    s = re.sub(r"//[^\n]*", " ", s)
    out = []
    for part in s.replace("\n", " ").split(","):
        nm = part.strip().split(" as ")[-1].strip().strip("'\"").strip()
        if nm and nm != "default" and re.fullmatch(r"[A-Za-z_$][\w$]*", nm):
            out.append(nm)
    return out


def _resolve_dts(spec: str, from_file: Path, pkg_root: Path) -> Path | None:
    """把 export 说明符解析成盘上 .d.ts。只包内解析，不跨包（跨包的裸包名直接放弃）。"""
    base = (from_file.parent / spec) if spec.startswith(".") else (pkg_root / spec)
    cands = [base] if base.suffix in (".ts", ".d.ts") else [
        base.with_suffix(".d.ts"), base / "index.d.ts", base.with_suffix(".ts")]
    for c in cands:
        try:
            c = c.resolve()
        except OSError:
            continue
        if c.is_file() and c.suffix in (".ts", ".d.ts"):
            return c
    return None


def parse_dts_exports_deep(entry: Path, pkg_root: Path, max_files: int = 1500) -> dict:
    """从入口 .d.ts **递归**展开 export * / export {...} from，收集包内全部可达导出符号。

    为什么必须递归：实测 50 个 @seeyon 包里 47 个入口只是 re-export 壳
    （如 biz-org-selector 的 dist/es/index.d.ts 只有 5 条 export *），
    只看入口一层会得到 0 个符号，且脚本照样 exit 0 —— 证据区躺着 47 个空壳
    却看着全绿。递归 + main() 里的闸门是这条的配套。
    """
    pend = [entry]
    seen: set[Path] = set()
    symbols: dict[str, dict] = {}
    by_module: dict[str, list[str]] = {}
    stars: list[str] = []

    def rel(p: Path) -> str:
        return str(p.relative_to(pkg_root)).replace("\\", "/") if p.is_relative_to(pkg_root) else str(p)

    while pend and len(seen) < max_files:
        f = pend.pop()
        try:
            f = f.resolve()
        except OSError:
            continue
        if f in seen:
            continue
        seen.add(f)
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for syms, mod in RE_EXPORT_ANY.findall(t):
            names = _clean_names(syms)
            if mod:
                if names:
                    by_module.setdefault(mod, []).extend(names)
                    for nm in names:
                        symbols.setdefault(nm, {"kind": "reexport", "from": mod})
                tgt = _resolve_dts(mod, f, pkg_root)
                if tgt:
                    pend.append(tgt)
            else:
                # `import X from './x'; export { X };` —— 平台包常见写法，原实现漏掉这类
                for nm in names:
                    symbols.setdefault(nm, {"kind": "local-export", "from": rel(f)})

        # 文件级 declare（无 export 前缀）+ `export default X` 收尾的包写法
        for kind, nm in RE_DECL_TOP.findall(t):
            symbols.setdefault(nm, {"kind": f"declare-{kind}", "from": rel(f)})
        for nm in RE_EXPORT_DEFAULT.findall(t):
            if nm:
                symbols.setdefault(nm, {"kind": "default", "from": rel(f)})

        for mod in RE_EXPORT_STAR.findall(t):
            stars.append(mod)
            tgt = _resolve_dts(mod, f, pkg_root)
            if tgt:
                pend.append(tgt)

        for ns, mod in RE_EXPORT_AS_NS.findall(t):
            symbols.setdefault(ns, {"kind": "namespace", "from": mod})
            tgt = _resolve_dts(mod, f, pkg_root)
            if tgt:
                pend.append(tgt)

        for kind, nm in RE_DECL_ALL.findall(t):
            symbols.setdefault(nm, {"kind": kind, "from": rel(f)})

    return {
        "entry": rel(entry),
        "files_scanned": len(seen),
        "files": sorted(rel(p) for p in seen),
        "symbol_count": len(symbols),
        "symbols": dict(sorted(symbols.items())),
        "reexport_by_module": {k: sorted(set(v)) for k, v in sorted(by_module.items())},
        "export_star": sorted(set(stars)),
        "truncated": len(seen) >= max_files,
    }


# ---------------------------------------------------------------- 签名面（组件 props / 函数 / 类方法）
# 目的：不止知道「有哪些符号」，还要知道「怎么传参」。数据源仍是包内 d.ts 原文。

RE_IFACE = re.compile(r"(?:export\s+)?(?:declare\s+)?interface\s+(\w+)\s*(?:<[^>]*>)?\s*(?:extends\s+([^{]+?))?\s*\{")
# 泛型别名必须放行 `<T>`，否则 `type XxxProps<T> = Omit<A,'k'> & B & {…}` 整条丢失
RE_TYPE_OBJ = re.compile(r"(?:export\s+)?(?:declare\s+)?type\s+(\w+)\s*(?:<[^>]*>)?\s*=\s*[^;{]*\{")
RE_COMP_FC = re.compile(
    r"(?:export\s+)?(?:declare\s+)?const\s+(\w+)\s*:\s*"
    r"(?:React\.)?(?:FC|FunctionComponent|MemoExoticComponent)<\s*([\w.]+)\s*>"
    r"|(?:export\s+)?(?:declare\s+)?const\s+(\w+)\s*[:=]\s*\(\s*props\s*:\s*([\w.]+)\s*\)\s*=>")
# ui 一类包的组件是 type 别名：`export type ButtonType = React.FC<ButtonProps> & {…}`
RE_COMP_TYPE = re.compile(
    r"(?:export\s+)?type\s+(\w+)\s*=\s*(?:React\.)?"
    r"(?:FC|FunctionComponent|ForwardRefExoticComponent|MemoExoticComponent)<\s*([\w.]+)")
RE_FUNC = re.compile(
    r"(?:export\s+)?(?:declare\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?::\s*([^;{\n]+))?")
RE_CLASS = re.compile(r"(?:export\s+)?(?:declare\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+([\w.]+))?")
# 任何相对路径的 from（import / export 都算）：签名扫描靠它把子模块一并读进来
RE_RELATIVE = re.compile(r"from\s*['\"](\.[^'\"]+)['\"]")


def _block_at(t: str, open_idx: int) -> str:
    """从 `{` 的下标取配对块内容（大括号计数）。"""
    depth = 0
    for i in range(open_idx, len(t)):
        c = t[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return t[open_idx + 1:i]
    return t[open_idx + 1:]


def _split_members(body: str) -> list[str]:
    """按顶层 `;` 或换行切成员（忽略括号/大括号内的分隔符）。"""
    out, buf, depth = [], [], 0
    for ch in body:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if ch in ";\n" and depth == 0:
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []
        else:
            buf.append(ch)
    s = "".join(buf).strip()
    if s:
        out.append(s)
    return out


def parse_props_fields(body: str) -> list[dict]:
    """interface 正文 → [{name, optional, type}]。保留联合类型与函数类型的原始文本。"""
    fields = []
    for raw in _split_members(body):
        m = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S)
        m = re.sub(r"//[^\n]*", " ", m).strip().rstrip(";").strip()
        mm = re.match(r"(?:readonly\s+)?([\w$]+)\s*(\?)?\s*:\s*(.+)", m, re.S)
        if not mm:
            continue
        fields.append({
            "name": mm.group(1),
            "optional": bool(mm.group(2)),
            "type": " ".join(mm.group(3).split())[:200],
        })
    return fields


def parse_classes_methods(body: str) -> list[dict]:
    """class 正文 → [{name, args, returns}]（只收方法/构造器，不收字段）。"""
    out = []
    for raw in _split_members(body):
        m = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S)
        m = " ".join(re.sub(r"//[^\n]*", " ", m).split())
        mm = re.match(r"(?:public\s+|private\s+|protected\s+|static\s+|abstract\s+)*"
                      r"(constructor|[\w$]+)\s*\((.*?)\)\s*(?::\s*([^;{]+))?", m)
        if not mm or "(" not in raw:
            continue
        if mm.group(1) in ("if", "for", "while", "switch", "return"):
            continue
        out.append({
            "name": mm.group(1),
            "args": " ".join(mm.group(2).split())[:300],
            "returns": " ".join((mm.group(3) or "").split())[:160],
        })
    return out


def _collect_related_files(entry: Path, pkg_root: Path, max_files: int = 2000) -> list[Path]:
    """从入口出发，沿 `from './x'`（import / export 都算）收全部相关 d.ts。

    签名面要的不只是「导出链」：平台包常见
        import { ExcelImportModal } from './components/excel-import-modal';
        export { ExcelImportModal };
    子文件不在 export 链上（export 无 from），只跟 export 会漏掉 props 定义。
    """
    pend, seen = [entry], set()
    while pend and len(seen) < max_files:
        f = pend.pop()
        try:
            f = f.resolve()
        except OSError:
            continue
        if f in seen:
            continue
        seen.add(f)
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for mod in RE_RELATIVE.findall(t):
            tgt = _resolve_dts(mod, f, pkg_root)
            if tgt:
                pend.append(tgt)
    return sorted(seen)


def parse_signatures(files: list[Path], pkg_root: Path,
                     allowed: set[str] | None = None) -> dict:
    """从 d.ts 抽签名面：props 字段表、组件→props 绑定、函数签名、类方法表。

    props_types 全量收（供组件匹配），组件/函数/类只收 `allowed`（= 该包对外导出符号），
    避免把包内私有实现当 API 列出来。
    """
    def ok(n: str) -> bool:
        if allowed is None:
            return True
        return n in allowed or (n.endswith("Type") and n[:-4] in allowed)

    props: dict[str, dict] = {}
    comps: dict[str, dict] = {}
    funcs: dict[str, dict] = {}
    classes: dict[str, dict] = {}
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(pkg_root)).replace("\\", "/") if f.is_relative_to(pkg_root) else str(f)
        for rx in (RE_IFACE, RE_TYPE_OBJ):
            for m in rx.finditer(t):
                name = m.group(1)
                body = _block_at(t, m.end() - 1)
                entry = {"kind": "interface" if rx is RE_IFACE else "type",
                         "fields": parse_props_fields(body), "from": rel}
                if rx is RE_IFACE and m.lastindex and m.lastindex >= 2 and m.group(2):
                    entry["extends"] = m.group(2).strip()
                if entry["fields"] or entry.get("extends"):
                    props.setdefault(name, entry)
        for m in RE_COMP_FC.finditer(t):
            cname = m.group(1) or m.group(3)
            ptype = m.group(2) or m.group(4) or ""
            if cname and ok(cname):
                comps.setdefault(cname, {"propsType": ptype, "from": rel})
        for m in RE_COMP_TYPE.finditer(t):
            if ok(m.group(1)):
                comps.setdefault(m.group(1), {"propsType": m.group(2), "from": rel})

    # 函数与类（同一文件可能重复声明，保留首个）
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(pkg_root)).replace("\\", "/") if f.is_relative_to(pkg_root) else str(f)
        for m in RE_FUNC.finditer(t):
            if not ok(m.group(1)):
                continue
            funcs.setdefault(m.group(1), {"args": " ".join(m.group(2).split())[:300],
                                          "returns": " ".join((m.group(3) or "").split())[:160],
                                          "from": rel})
        for m in RE_CLASS.finditer(t):
            if not ok(m.group(1)):
                continue
            idx = t.find("{", m.end())
            body = _block_at(t, idx) if idx != -1 else ""
            classes.setdefault(m.group(1), {"extends": m.group(2) or "", "methods": parse_classes_methods(body),
                                            "from": rel})

    # 组件若拿得到 props 类型，挂上字段表（下游直接「组件 → 字段」）
    for cname, c in comps.items():
        p = props.get(c["propsType"])
        if p:
            c["props"] = p["fields"]
    # `XxxType` 是 ui 一类包的组件类型别名，补一个 `Xxx` 别名方便按组件名查
    for cname in list(comps):
        if cname.endswith("Type") and cname[:-4] and cname[:-4] not in comps:
            comps[cname[:-4]] = dict(comps[cname])
    return {"props_types": props, "components": comps, "functions": funcs, "classes": classes}


def parse_dts_exports(dts: Path, rel_root: Path) -> dict:
    """从 .d.ts 抽导出符号面：按 from 模块分组 + 直接声明的可调用符号签名。"""
    t = dts.read_text(encoding="utf-8", errors="replace")
    by_module: dict[str, list[str]] = {}
    for syms, mod in RE_EXPORT_LIST.findall(t):
        lst = _clean_names(syms)
        by_module.setdefault(mod, []).extend(lst)
    stars = RE_EXPORT_STAR.findall(t)
    callables = {}
    for name, args, ret in RE_DECLARE_CALLABLE.findall(t):
        callables[name] = {"args": " ".join(args.split()), "returns": (ret or "").strip()}
    return {
        "path": str(dts.relative_to(rel_root)).replace("\\", "/") if dts.is_relative_to(rel_root) else str(dts),
        "reexport_by_module": {k: v for k, v in sorted(by_module.items())},
        "export_star": sorted(set(stars)),
        "declared_callables": callables,
    }


def find_seeyon_packages(nm: Path) -> list[dict]:
    """枚举 node_modules/@seeyon/<pkg>，取其 package.json 与顶层 d.ts 导出面。"""
    scope = nm / "@seeyon"
    if not scope.is_dir():
        return []
    out = []
    for pkg in sorted(scope.iterdir()):
        if not pkg.is_dir():
            continue
        pj = pkg / "package.json"
        if not pj.exists():
            continue
        try:
            meta = json.loads(pj.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            out.append({"package": pkg.name, "error": f"package.json 解析失败: {e}"})
            continue
        entry = {"package": f"@seeyon/{pkg.name}", "version": meta.get("version"),
                 "description": meta.get("description"), "typings": meta.get("typings") or meta.get("types")}
        # 顶层 d.ts：优先 package.json 声明的 typings，否则按常见布局猜，最后兜底取最短 index.d.ts
        cand = None
        if entry["typings"]:
            cand = pkg / entry["typings"]
        if not cand or not cand.exists():
            for guess in ("dist/index.d.ts", "es/index.d.ts", "types/index.d.ts", "index.d.ts",
                          "lib/index.d.ts", "esm/index.d.ts", "dist/types/index.d.ts",
                          "dist/es/index.d.ts", "typings/index.d.ts", "dist/dist/index.d.ts"):
                if (pkg / guess).exists():
                    cand = pkg / guess
                    break
        if not cand or not cand.exists():
            # 兜底：包内任意 index.d.ts 取路径最短的那个（实测 biz-enums 的 d.ts 在 dist/dist/types/ 下）
            inner = sorted((p for p in pkg.rglob("index.d.ts") if "node_modules" not in p.parts),
                           key=lambda p: (len(p.parts), str(p)))
            if inner:
                cand = inner[0]
        if cand and cand.exists():
            entry["top_level_dts"] = parse_dts_exports(cand, pkg)
            entry["symbols"] = parse_dts_exports_deep(cand, pkg)
        else:
            # 无任何 .d.ts：真无类型包（如 syf 是构建工具），main() 里按 WARN 计数，不算闸门失败
            entry["symbols"] = {"entry": None, "files_scanned": 0, "symbol_count": 0,
                                "symbols": {}, "reexport_by_module": {}, "export_star": [],
                                "truncated": False}
        out.append(entry)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="抽取 UDC 扩展工程可用依赖面（只读）")
    ap.add_argument("--backend", help="后端扩展工程根目录（含 pom.xml）")
    ap.add_argument("--frontend", help="前端扩展工程 pc 目录（含 package.json / node_modules）")
    ap.add_argument("--repo", help="本地 maven 仓库根（用于解析 parent pom），可选")
    ap.add_argument("--emit", required=True, help="输出 JSON 路径")
    ap.add_argument("--emit-signatures",
                    help="可选：输出签名面 JSON（组件 props / 函数参数 / 类方法），需配合 --frontend")
    a = ap.parse_args(argv)

    if not a.backend and not a.frontend:
        ap.error("至少给 --backend 或 --frontend 之一")
    result: dict = {"sources": {}}

    if a.backend:
        bk = Path(a.backend)
        pom = bk / "pom.xml"
        if not pom.exists():
            print(f"ERR: {pom} 不存在", file=sys.stderr)
            return 2
        deps = parse_pom_deps(pom)
        parent = parse_parent(pom)
        parent_pom = resolve_parent_pom(pom, parent, Path(a.repo) if a.repo else None)
        cp = parse_classpath(bk / "target" / "compile_args.txt")
        jars = []
        for j in cp:
            art, ver = jar_artifact(j)
            jars.append({"artifact": art, "version": ver, "jar": j,
                         "group": "com.seeyon" if "/com/seeyon/" in j else ""})
        result["sources"]["backend"] = {
            "root": bk.name,
            "pom": {
                "parent": parent,
                "parent_pom_found": str(parent_pom) if parent_pom else None,
                "own_dependencies": deps,
                "parent_dependencies": parse_pom_deps(parent_pom) if parent_pom else [],
            },
            "compile_classpath": {
                "source": str((bk / "target" / "compile_args.txt").as_posix()),
                "jar_count": len(jars),
                "seeyon_jar_count": sum(1 for j in jars if j["group"]),
                "jars": jars,
            },
        }

    if a.frontend:
        pc = Path(a.frontend)
        result["sources"]["frontend"] = {
            "root": pc.name,
            "package_json": parse_package_json(pc),
            "seeyon_packages": find_seeyon_packages(pc / "node_modules"),
            "hoisted_top_level": find_hoisted_top_level(pc / "node_modules"),
        }

    out = Path(a.emit)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 签名面（可选）：把「有哪些符号」补成「怎么传参」
    if a.emit_signatures:
        if not a.frontend:
            print("ERR: --emit-signatures 需要配合 --frontend", file=sys.stderr)
            return 2
        nm = Path(a.frontend) / "node_modules" / "@seeyon"
        sig = {"sources": {"frontend": {"root": Path(a.frontend).name, "packages": {}}}}
        for x in result["sources"]["frontend"]["seeyon_packages"]:
            name = x["package"].split("/")[-1]
            pkg_dir = nm / name
            entry_rel = (x.get("symbols") or {}).get("entry")
            if not entry_rel:
                continue
            # 全包扫 d.ts：props 定义常在「可达链之外」的兄弟文件里
            # （如 ui 的组件在 es/components/x/x.d.ts，入口只 export 一个类型名）。
            # 组件识别仍靠可达面，这里只是让 props 类型库变全。
            files = sorted(p for p in pkg_dir.rglob("*.d.ts")
                           if "node_modules" not in p.relative_to(pkg_dir).parts)
            if not files:
                continue
            allowed = set((x.get("symbols") or {}).get("symbols") or {})
            sig["sources"]["frontend"]["packages"][x["package"]] = parse_signatures(files, pkg_dir, allowed)
        sp = Path(a.emit_signatures)
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(sig, ensure_ascii=False, indent=2), encoding="utf-8")
        n_comp = sum(len(p["components"]) for p in sig["sources"]["frontend"]["packages"].values())
        n_props = sum(len(p["props_types"]) for p in sig["sources"]["frontend"]["packages"].values())
        n_fn = sum(len(p["functions"]) for p in sig["sources"]["frontend"]["packages"].values())
        print(f"signatures  组件 {n_comp} / props 类型 {n_props} / 函数 {n_fn} "
              f"→ {sp}（{sp.stat().st_size} B）")

    # 摘要（人读）
    if a.backend:
        b = result["sources"]["backend"]
        pdeps = len(b["pom"]["parent_dependencies"])
        print(f"backend  pom 自有依赖 {len(b['pom']['own_dependencies'])} / "
              f"parent 依赖 {pdeps} / "
              f"classpath jar {b['compile_classpath']['jar_count']}"
              f"（seeyon {b['compile_classpath']['seeyon_jar_count']}）")
        # ★ parent pom 解析失败会让「平台能力清单」整段变空，但摘要看着正常。
        #   实测：工程 parent 已前进到本地仓库拿不到的版本时，目录里只有 *.lastUpdated，
        #   parent 依赖静默变 0。这里必须显式报错，不能当成功。
        if pdeps == 0:
            par = b["pom"].get("parent") or {}
            print(
                "ERR: parent 依赖解析为 0 条 —— parent pom 未取到，平台能力清单不完整。\n"
                f"     需求版本 {par.get('groupId')}:{par.get('artifactId')}:{par.get('version')}\n"
                "     查 <repo>/<groupId 路径>/<artifactId>/<version>/ 下是否有 .pom 本体；\n"
                "     只有 *.pom.lastUpdated（且 .error= 为空）表示拉取失败，需先让本地仓库能取到该版本。",
                file=sys.stderr)
            return 4
    if a.frontend:
        f = result["sources"]["frontend"]
        pkgs = f["seeyon_packages"]
        total_sym = sum((p.get("symbols") or {}).get("symbol_count", 0) for p in pkgs)
        no_types = [p["package"] for p in pkgs if not (p.get("symbols") or {}).get("files_scanned")]
        empty = [p["package"] for p in pkgs
                 if (p.get("symbols") or {}).get("files_scanned")
                 and not (p.get("symbols") or {}).get("symbol_count")]
        print(f"frontend  @seeyon 包 {len(pkgs)} 个 / 导出符号合计 {total_sym}")
        if no_types:
            print(f"WARN: {len(no_types)} 个包无任何 .d.ts（真无类型，不计失败）: "
                  f"{', '.join(no_types[:8])}")
        # ★ 入口 d.ts 常常只是 export * 壳；不递归会得到 0 符号却 exit 0。
        #   实测 47/50 包曾因此成为空壳证据。有 .d.ts 却 0 符号 = 抽取失败，必须显式失败。
        if empty:
            print(f"ERR: {len(empty)} 个包有 .d.ts 但递归后 0 导出符号 —— 抽取失败，不能当成功：",
                  file=sys.stderr)
            for n in empty:
                print(f"      {n}", file=sys.stderr)
            return 5
    print(f"emit -> {out}（{out.stat().st_size} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

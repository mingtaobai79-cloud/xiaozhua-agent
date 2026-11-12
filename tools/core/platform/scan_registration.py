#!/usr/bin/env python3
"""扫标品 jar 的注册面：META-INF/services、spring.factories、spring/*.imports。

回答的问题：扩展点写完之后，平台凭什么发现你的类？
  ① Java SPI（META-INF/services/接口全名，文件内容是实现类全名）
  ② Spring Boot 自动装配（META-INF/spring.factories 的 EnableAutoConfiguration 等）
  ③ Spring 组件扫描（靠 @Component 等注解，本脚本看不到，需 javap -v）
  ④ 平台自己的元数据注册（如 udc_deploy_record / 设计态配置，静态取不到）

本脚本把 ①②③ 里的 ① ② 全部取出来，作为「注册模板」。

用法：
  python tools/core/platform/scan_registration.py \
      --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
      --emit docs/audit/artifacts/extension-surface-20261029/registration-scan.json
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


def read_jar(jar: Path) -> dict:
    out: dict = {"services": {}, "spring_factories": {}, "imports": {}}
    try:
        zf = zipfile.ZipFile(jar)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
        return out
    with zf:
        names = zf.namelist()
        for n in names:
            if n.startswith("META-INF/services/") and not n.endswith("/"):
                iface = n.rsplit("/", 1)[-1]
                try:
                    body = zf.read(n).decode("utf-8", "replace")
                except Exception:  # noqa: BLE001
                    continue
                impls = [ln.strip() for ln in body.splitlines()
                         if ln.strip() and not ln.strip().startswith("#")]
                if impls:
                    out["services"][iface] = impls
            elif n == "META-INF/spring.factories":
                try:
                    body = zf.read(n).decode("utf-8", "replace")
                except Exception:  # noqa: BLE001
                    continue
                cur = None
                for ln in body.splitlines():
                    s = ln.strip()
                    if not s or s.startswith("#"):
                        continue
                    if s.endswith("\\"):
                        s = s[:-1]
                    if "=" in s and not s.startswith("\\"):
                        k, v = s.split("=", 1)
                        cur = k.strip()
                        out["spring_factories"].setdefault(cur, [])
                        if v.strip():
                            out["spring_factories"][cur].append(v.strip())
                    elif cur:
                        out["spring_factories"][cur].append(s)
            elif n.startswith("META-INF/spring/") and n.endswith(".imports"):
                try:
                    body = zf.read(n).decode("utf-8", "replace")
                except Exception:  # noqa: BLE001
                    continue
                key = n.rsplit("/", 1)[-1]
                out["imports"][key] = [ln.strip() for ln in body.splitlines()
                                       if ln.strip() and not ln.strip().startswith("#")]
    return out


def resolve_jar(repo: Path, pkg: str, jar_name: str) -> tuple[Path | None, str]:
    """sources 里只存了 jar 文件名，这里按仓库布局 <pkg>/<version>/<jar> 解析。

    返回 (实际路径, 说明)。版本可能与索引记录的不同（仓库里只有一版时以磁盘为准）。
    """
    p = Path(jar_name)
    if p.is_absolute() and p.exists():
        return p, "绝对路径"
    d = repo / pkg
    if d.is_dir():
        hits = sorted(d.rglob(p.name))
        if hits:
            return hits[-1], ("版本一致" if hits[-1].name == p.name else f"磁盘版 {hits[-1].name}")
        allj = sorted(d.rglob("*.jar"))
        if allj:
            return allj[-1], f"记录版 {p.name} 不在，用磁盘最新 {allj[-1].name}"
    hits = sorted(repo.rglob(p.name))
    if hits:
        return hits[-1], "跨目录命中"
    allj = sorted(repo.rglob(f"{pkg}-*.jar"))
    if allj:
        return allj[-1], f"按前缀命中 {allj[-1].name}"
    return None, "找不到"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit", required=True)
    ap.add_argument("--repo", default="<MAVEN_REPO>/com/seeyon")
    a = ap.parse_args()

    data = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    sources = data["sources"]
    repo = Path(a.repo)

    result: dict = {"jars": {}, "summary": {}}
    n_svc = n_sf = n_imp = 0
    for pkg, info in sorted(sources.items()):
        jar = info.get("jar")
        if not jar:
            continue
        p, how = resolve_jar(repo, pkg, jar)
        if p is None:
            result["jars"][pkg] = {"error": f"jar 找不到: {jar}（{how}）"}
            continue
        r = read_jar(p)
        r["jar"] = str(p)
        r["resolve"] = how
        r["recorded"] = jar
        result["jars"][pkg] = r
        n_svc += len(r["services"])
        n_sf += len(r["spring_factories"])
        n_imp += len(r["imports"])

    result["summary"] = {
        "jars": len(result["jars"]),
        "jars_with_services": sum(1 for r in result["jars"].values() if r.get("services")),
        "jars_with_spring_factories": sum(1 for r in result["jars"].values() if r.get("spring_factories")),
        "jars_with_imports": sum(1 for r in result["jars"].values() if r.get("imports")),
        "service_entries": n_svc,
        "spring_factories_keys": n_sf,
        "imports_files": n_imp,
    }
    Path(a.emit).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    s = result["summary"]
    print(f"jar {s['jars']} 个 → {a.emit}")
    print(f"  有 META-INF/services 的 jar: {s['jars_with_services']} 个，共 {s['service_entries']} 个 SPI 文件")
    print(f"  有 spring.factories 的 jar: {s['jars_with_spring_factories']} 个，共 {s['spring_factories_keys']} 个键")
    print(f"  有 spring/*.imports 的 jar: {s['jars_with_imports']} 个")
    print()
    print("SPI 注册面（前 20）：")
    rows = []
    for pkg, r in result["jars"].items():
        for iface, impls in (r.get("services") or {}).items():
            rows.append((len(impls), iface, pkg))
    for n, iface, pkg in sorted(rows, reverse=True)[:20]:
        print(f"  {n:3d} 个实现  {iface:60s} [{pkg}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

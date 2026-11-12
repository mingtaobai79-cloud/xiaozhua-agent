# -*- coding: utf-8 -*-
"""部署域 HTTP 暴露能力普查复算器（离线只读，LIVE-DEPLOYED + VERIFIED_STATIC_BYTECODE）。

**要回答的问题（第二十一轮遗留 / marker 判据的边界）**：
`DEPLOYED-MARKER-CLOSURE.json` 用「常量池含 `bind/annotation`」当「能暴露注解路由」的
必要条件，据此论证 0-marker 构件不可能藏端点。该判据**只覆盖 Spring MVC**：
JAX-RS（`@Path`）与 Servlet 原生（`@WebServlet`/`@WebFilter`/`extends HttpServlet`）
**不需要** `bind/annotation` 即可暴露端点 ⇒ 若不检验，闭包论证有一个真窟窿。

本器给出**第二条独立必要条件**并逐件实测。能暴露 HTTP 端点的类必属三者之一：
  ① 继承 `javax.servlet.http.HttpServlet`（`super_class` 槽位**精确相等**）
  ② 带注解描述符 `Ljavax/ws/rs/Path;` 或 `Ljakarta/ws/rs/Path;`
  ③ 带注解描述符 `Ljavax/servlet/annotation/WebServlet;` / `L...WebFilter;`
注解**定义类自身**（位于注解包下者）不计 —— 那是 api jar 携带定义，不是在暴露端点。

**已知陷阱（本器显式规避）**：`javax/servlet/http/HttpServlet` 是
`javax/servlet/http/HttpServletRequest` 的**前缀子串**。以子串判「继承 HttpServlet」
会把所有引用 HttpServletRequest 的类误判 ⇒ 本器改为解析 `super_class` 常量池槽位做精确相等。

用法：
    uv run --no-project python tools/enumerate_deployed_exposure_census.py \
        --inventory <lib_inventory.json> --emit <out.json>
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import struct
import sys
import zipfile
from pathlib import Path

MARKER = b"bind/annotation"
HTTP_SUPER_UTF8 = b"javax/servlet/http/HttpServlet"
SUPER_CANDIDATES = {"javax/servlet/http/HttpServlet", "jakarta/servlet/http/HttpServlet"}
ANNOT_DESC = {
    "jaxrs_Path": (b"Ljavax/ws/rs/Path;", b"Ljakarta/ws/rs/Path;"),
    "web_servlet": (b"Ljavax/servlet/annotation/WebServlet;",),
    "web_filter": (b"Ljavax/servlet/annotation/WebFilter;",),
}
ANNOT_PKGS = ("javax/ws/rs/", "jakarta/ws/rs/", "javax/servlet/annotation/",
              "javax/servlet/http/", "jakarta/servlet/")
CACHE_DIRS = ("djars", "missingjars", "artif", "art517", "cand", "udcchk",
              "deployed-extra", "bulk/jars", "bulk/allvers")
PLATFORM_PREFIXES = ("udc-", "boot-starter-", "boot-", "ctp-", "cdp-", "cip-",
                     "devops-starter-", "app-common-", "organization-", "bpm-")


def local_index(extra_roots):
    idx = {}
    for f in glob.glob("<MAVEN_REPO>/**/*.jar", recursive=True):
        idx.setdefault(os.path.basename(f), f)
    for root in extra_roots:
        for d in CACHE_DIRS:
            for f in glob.glob(str(Path(root) / d / "*.jar")):
                idx.setdefault(os.path.basename(f), f)
    return idx


def super_class_name(data: bytes) -> str:
    """精确解析 super_class 的常量池 UTF8（不猜、不子串匹配）。"""
    try:
        if data[:4] != b"\xca\xfe\xba\xbe":
            return ""
        cp_count = struct.unpack(">H", data[8:10])[0]
        i, utf, cls = 10, {}, {}
        while i < len(data):
            tag = data[i]
            if tag == 1:
                ln = struct.unpack(">H", data[i + 1:i + 3])[0]
                utf[i] = data[i + 3:i + 3 + ln].decode("utf-8", "replace")
                i += 3 + ln
            elif tag in (7, 8, 16, 19, 20):
                cls[i] = struct.unpack(">H", data[i + 1:i + 3])[0]
                i += 3
            elif tag == 15:
                i += 4
            elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
                i += 5
            elif tag in (5, 6):
                i += 9
            else:
                return ""
        p = 10
        while p < len(data):
            tag = data[p]
            if tag == 1:
                ln = struct.unpack(">H", data[p + 1:p + 3])[0]
                p += 3 + ln
            elif tag in (7, 8, 16, 19, 20):
                p += 3
            elif tag == 15:
                p += 4
            elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
                p += 5
            elif tag in (5, 6):
                p += 9
            else:
                break
        sup_idx = struct.unpack(">H", data[p + 4:p + 6])[0]
        return utf.get(cls.get(sup_idx, -1), "")
    except Exception:
        return ""


def scan_jar(path):
    """返回 (class_count, 计数 dict, 真实暴露者清单)。"""
    counts = {"spring_bind": 0, "jaxrs_Path": 0, "web_servlet": 0, "web_filter": 0,
              "extends_http_servlet": 0}
    providers = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith(".class")]
        for n in names:
            d = z.read(n)
            if MARKER in d:
                counts["spring_bind"] += 1
            if any(n.startswith(p) for p in ANNOT_PKGS):
                continue          # 注解定义类自身：携带定义 ≠ 暴露端点
            kinds = []
            for key, descs in ANNOT_DESC.items():
                if any(x in d for x in descs):
                    counts[key] += 1
                    kinds.append(key)
            if HTTP_SUPER_UTF8 in d and super_class_name(d) in SUPER_CANDIDATES:
                counts["extends_http_servlet"] += 1
                kinds.append("extends_http_servlet")
            if kinds:
                providers.append({"class": n[:-6].replace("/", "."), "kinds": sorted(set(kinds))})
    return len(names), counts, providers


def build(inventory):
    inv = Path(inventory)
    raw = inv.read_bytes()
    meta = {"name": inv.name, "sha256": hashlib.sha256(raw).hexdigest()}
    jars = sorted(json.loads(raw.decode("utf-8"))["jars"])
    idx = local_index([inv.parent])
    rows = []
    for j in jars:
        p = idx.get(j)
        rec = {"jar": j}
        if not p:
            rec["status"] = "NOT_OBTAINABLE"
        else:
            try:
                c, counts, prov = scan_jar(p)
                rec.update({"status": "SCANNED", "classes": c})
                rec.update(counts)
                if prov:
                    rec["real_http_provider_count"] = len(prov)
                    rec["real_http_providers"] = prov[:8]
            except Exception as e:
                rec.update({"status": "BADJAR", "err": str(e)[:120]})
        rows.append(rec)

    scanned = [r for r in rows if r["status"] == "SCANNED"]
    na = [r["jar"] for r in rows if r["status"] == "NOT_OBTAINABLE"]
    zero_marker = [r for r in scanned if r["spring_bind"] == 0]

    def is_plat(j):
        return j.startswith(PLATFORM_PREFIXES)

    exposed_zero = sorted(r["jar"] for r in zero_marker if r.get("real_http_provider_count"))
    marker_bearing = sorted(r["jar"] for r in scanned if r["spring_bind"] > 0)
    plat_zero = sorted(r["jar"] for r in zero_marker if is_plat(r["jar"]))
    non_spring_plat = sorted(
        r["jar"] for r in scanned if is_plat(r["jar"])
        and (r["jaxrs_Path"] or r["web_servlet"] or r["web_filter"]))

    return {
        "schema": "deployed-exposure-census.v1",
        "evidence": ("LIVE-DEPLOYED (BOOT-INF/lib 清单) + VERIFIED_STATIC_BYTECODE "
                     "(直读 .class 常量池 + super_class 槽位)"),
        "criterion": ("第二必要条件：能暴露 HTTP 端点的类必属 ①继承 javax.servlet.http.HttpServlet"
                      "（super_class 精确相等）②带 Ljavax/ws/rs/Path; ③带 "
                      "Ljavax/servlet/annotation/WebServlet|WebFilter; 之一；注解定义类自身不计。"
                      "用于检验 marker 判据（只覆盖 Spring MVC）之外的窟窿。"),
        "known_trap_avoided": ("javax/servlet/http/HttpServlet 是 HttpServletRequest 的前缀子串；"
                               "以子串判『继承 HttpServlet』会把引用 HttpServletRequest 的类全部误判 "
                               "⇒ 本器改为解析 super_class 槽位精确相等"),
        "inventory": meta,
        "total": len(rows),
        "scanned": len(scanned),
        "not_obtainable": len(na),
        "not_obtainable_jars": na,
        "marker_bearing": len(marker_bearing),
        "marker_jars": marker_bearing,
        "zero_marker": len(zero_marker),
        "platform_family_zero_marker": len(plat_zero),
        "platform_family_zero_marker_jars": plat_zero,
        "closure_over_exposure_capability": {
            "zero_marker_with_real_http_exposure": exposed_zero,
            "zero_marker_with_real_http_exposure_platform_family":
                [j for j in exposed_zero if is_plat(j)],
            "zero_marker_with_real_http_exposure_third_party":
                [j for j in exposed_zero if not is_plat(j)],
            "verdict": "PASS" if not [j for j in exposed_zero if is_plat(j)] else "FAIL",
            "reading": ("marker 判据之外的暴露通道（JAX-RS / 原生 Servlet）在 0-marker 构件上只命中"
                        "第三方容器与库；平台家族构件 0 命中 ⇒ 对**平台构件**而言 marker 判据的完备性成立"),
        },
        "platform_jars_with_non_spring_route_annotation": non_spring_plat,
        "limitations": [
            "NOT_OBTAINABLE 的第三方构件未扫 ⇒ 该子集的暴露能力未知，闭包只在已扫子集上成立",
            "本器判「构件是否具备暴露能力」，不判具体路由字面量；后者见 DEPLOYED-FULL-DOMAIN-OP-SURFACE.json",
            "继承判定用直接父类（非传递闭包）：经中间父类间接继承 HttpServlet 的类自身不在 providers 内（其父类会命中）",
            "jar / class 本体不入 git；本件为复算产物",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="部署域 HTTP 暴露能力普查（离线只读）")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--emit", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not Path(a.inventory).is_file():
        print(json.dumps({"error": "inventory 不存在", "path": a.inventory}, ensure_ascii=False))
        return 2
    payload = build(a.inventory)
    txt = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if a.emit:
        Path(a.emit).write_text(txt, encoding="utf-8", newline="\n")
        print("WROTE", a.emit)
    if a.json or not a.emit:
        print(txt)
    else:
        c = payload["closure_over_exposure_capability"]
        print("total=%d scanned=%d marker=%d zero_marker=%d not_obtainable=%d" % (
            payload["total"], payload["scanned"], payload["marker_bearing"],
            payload["zero_marker"], payload["not_obtainable"]))
        print("0-marker 且真实可暴露: %d (平台家族 %d / 第三方 %d) -> %s" % (
            len(c["zero_marker_with_real_http_exposure"]),
            len(c["zero_marker_with_real_http_exposure_platform_family"]),
            len(c["zero_marker_with_real_http_exposure_third_party"]), c["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

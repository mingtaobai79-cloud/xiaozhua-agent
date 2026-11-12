#!/usr/bin/env python3
"""按标品域导出「接口 × 逐字方法签名」清单。

回答的问题：BPM 怎么发起流程？组织怎么查人？连接器怎么调？——要能直接照抄的签名，
不是方法名列表。

数据源：interfaces.json（javap 原文结构化）。每个域产出一个 md：
  一、接口全签名（按方法数降序）
  二、关键类全签名（名字含 AppService/Service/Utils/Helper/Dao/Factory/Manager 且方法数 >= 5）

用法：
  python tools/core/platform/emit_domain_surfaces.py \
      --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
      --emit-dir docs/audit/artifacts/extension-surface-20261029/domains
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# 域 → (显示名, 包前缀, 一句话用途)
DOMAINS: dict[str, tuple[str, str, str]] = {
    "dubbo": ("Dubbo 跨服务调用", "com.seeyon.boot.starter.dubbo",
              "跨应用/跨服务调用：工厂、代理、灰度、可靠投递"),
    "bpm": ("BPM 流程", "com.seeyon.bpm",
            "流程发起/提交/退回/终止/暂停、模板、表单权限、节点权限"),
    "organization": ("组织架构", "com.seeyon.organization",
                     "组织/单位/部门/岗位/人员查询与构造"),
    "mybatis": ("MyBatis / Dao", "com.seeyon.boot.starter.mybatis",
                "通用 Dao、条件查询、分页、方言"),
    "datasource": ("数据源", "com.seeyon.boot.starter.datasource",
                   "数据源装配、多库路由"),
    "connector": ("连接器", "com.seeyon.cip.connector",
                  "连接器应用、配置、认证、数据库执行器、移动端 Provider"),
    "affair": ("事项", "com.seeyon.ctp.affair",
               "事项发起与流转（UDC 侧入口）"),
    "formconvert": ("单据转文档", "com.seeyon.boot.starter.formconvert",
                    "表单/单据转文档、模板套用"),
    "formula": ("表达式", "com.seeyon.boot.starter.formula",
                "表达式引擎：函数、解析、语义、脚本构建"),
    "systemvariable": ("系统变量", "com.seeyon.boot.starter.systemvariable",
                       "系统变量取值（126 个静态面）"),
    "file": ("文件存储", "com.seeyon.boot.starter.file",
             "附件/文件上传下载、存储桶"),
}

KEY_CLASS_HINTS = ("AppService", "Service", "Utils", "Util", "Helper", "Dao", "Factory",
                   "Manager", "Provider", "Executor", "Template")


def sig_of(m: dict) -> str:
    s = m.get("signature", "")
    for p in ("public abstract ", "public static ", "public "):
        if s.startswith(p):
            s = s[len(p):]
            break
    return s.split(" throws")[0].strip()


def render(name: str, title: str, prefix: str, purpose: str,
           classes: dict[str, dict]) -> str:
    hits = {fq: c for fq, c in classes.items() if fq.startswith(prefix)}
    if not hits:
        return ""
    ifaces = {fq: c for fq, c in hits.items() if c.get("kind") == "interface"}
    key_cls = {fq: c for fq, c in hits.items()
               if c.get("kind") != "interface"
               and len(c["methods"]) >= 5
               and any(h in fq.split(".")[-1] for h in KEY_CLASS_HINTS)}

    total_m = sum(len(c["methods"]) for c in hits.values())
    out = [
        f"# {title}：接口与方法签名",
        "",
        f"> 自动生成，勿手改。`tools/core/platform/emit_domain_surfaces.py` 重跑即可。",
        f"> 用途：{purpose}",
        f"> 规模：{len(hits)} 类 / {len(ifaces)} 接口 / {len(key_cls)} 个关键类 / {total_m} 方法。"
        f"包前缀 `{prefix}`。",
        "> 签名逐字来自 javap 原文，已去掉 `public` 等修饰前缀与 `throws`。",
        "",
        f"## 一、接口（{len(ifaces)}）",
        "",
    ]
    for fq, c in sorted(ifaces.items(), key=lambda x: (-len(x[1]["methods"]), x[0])):
        ext = c.get("extends") or []
        ext_s = f" extends {', '.join(x.split('.')[-1] for x in ext)}" if ext else ""
        out += [f"### `{fq.split('.')[-1]}`（{len(c['methods'])} 方法）{ext_s}", "",
                f"`{fq}`", "", "```java"]
        for m in c["methods"]:
            if m["name"].startswith(("lambda$", "access$")):
                continue
            out.append("    " + sig_of(m))
        out += ["```", ""]

    out += [f"## 二、关键类（{len(key_cls)}）", ""]
    for fq, c in sorted(key_cls.items(), key=lambda x: (-len(x[1]["methods"]), x[0])):
        out += [f"### `{fq.split('.')[-1]}`（{len(c['methods'])} 方法）", "",
                f"`{fq}`", "", "```java"]
        for m in c["methods"]:
            if m["name"].startswith(("lambda$", "access$")):
                continue
            mods = m.get("modifiers", "")
            prefix_s = "static " if "static" in mods else ""
            out.append("    " + prefix_s + sig_of(m))
        out += ["```", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit-dir", required=True)
    a = ap.parse_args()

    classes = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))["classes"]
    outdir = Path(a.emit_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    empty = []
    for name, (title, prefix, purpose) in DOMAINS.items():
        md = render(name, title, prefix, purpose, classes)
        if not md:
            empty.append(name)
            continue
        p = outdir / f"{name}.md"
        p.write_text(md, encoding="utf-8")
        n_if = md.count("### `")
        rows.append((name, title, p.stat().st_size, n_if))

    if empty:
        print(f"WARN: {len(empty)} 个域在索引里没有类：{empty}")

    print(f"emit-dir {outdir}：{len(rows)} 个域")
    for name, title, size, n in rows:
        print(f"  {name:16s} {size:>8d} B  {n:3d} 段  {title}")
    if len(rows) < 6:
        print("ERR: 生成的域太少，包前缀可能写错")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

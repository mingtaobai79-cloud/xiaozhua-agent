#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seeyon 平台开发体系研究 —— 统计口径脚本
==========================================
用途：为 stage-1 统计登记表提供可重复执行的统计依据。
原则：
  1. 每个统计项都必须写明数据源、口径、去重规则、包范围。
  2. 脚本只读，不修改任何文件。
  3. 输出为 JSON，供 statistics-registry.md 引用。
  4. 任何数字都必须能被这个脚本复现。

用法：
  python scripts/research/stats_registry.py            # 打印 JSON
  python scripts/research/stats_registry.py --md       # 打印 markdown 表格
  python scripts/research/stats_registry.py --out x.json
"""
import argparse
import gzip
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIG = os.path.join(ROOT, "docs/audit/signatures.txt.gz")
SVC = os.path.join(ROOT, "docs/audit/reference/svc-app-service.txt.gz")
PLATFORM_TGZ = os.path.join(ROOT, "docs/audit/reference/udc-platform-5.3.517.tar.gz")
PLATFORM_VER = "udc-platform-5.3.517"

KIND_TOKENS = ("class", "interface", "enum", "@interface")


# ---------------------------------------------------------------- 基础读取
def read_sig_lines():
    with gzip.open(SIG, "rt", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def parse_sig(lines):
    """把签名库拆成 类声明 与 方法声明 两类。

    签名库格式（实测）：
      com.x.Y\tclass
      com.x.Y#method(args):ret
    判定规则：
      含 TAB 且 TAB 后为 class/interface/enum/@interface -> 类声明
      含 '#' 且含 '('                                  -> 方法声明
    """
    classes = {}   # fqcn -> kind
    methods = []   # (fqcn, method_name, raw)
    for ln in lines:
        if "\t" in ln:
            fq, _, kind = ln.partition("\t")
            kind = kind.strip()
            if kind in KIND_TOKENS:
                classes[fq] = kind
                continue
        if "#" in ln and "(" in ln:
            fq = ln.split("#", 1)[0]
            m = re.match(r"[^#]+#([\w$<>]+)\(", ln)
            methods.append((fq, m.group(1) if m else "", ln))
    return classes, methods


def read_tar_member(member):
    """从 udc-platform tar.gz 读一个成员（文本）。不存在返回 None。"""
    import tarfile
    with tarfile.open(PLATFORM_TGZ, "r:gz") as tf:
        for m in tf.getmembers():
            if m.name == member:
                f = tf.extractfile(m)
                return f.read().decode("utf-8", "replace") if f else None
    return None


# ---------------------------------------------------------------- 各项统计
def stat_signatures(lines, classes, methods):
    return {
        "total_lines": len(lines),
        "class_declarations": len(classes),
        "method_declarations": len(methods),
        "kind_breakdown": dict(Counter(classes.values())),
    }


def stat_codetask(classes, methods):
    """CodeTask 实现类：以「声明 code(CodeContext)」为准，而不是类名后缀。"""
    target = "#code(com.seeyon.udc.common.autocode.context.CodeContext)"
    impl = sorted({fq for fq, _, raw in methods if target in raw})
    by_pkg = Counter(".".join(c.split(".")[:-1]) for c in impl)
    # 接口自身
    iface = "com.seeyon.udc.common.autocode.CodeTask"
    # 类名后缀法（对照口径，说明差异）
    suffix = sorted({c for c in classes if c.split(".")[-1].endswith("Task")})
    return {
        "criterion": "声明 code(com.seeyon.udc.common.autocode.context.CodeContext) 的类去重",
        "total": len(impl),
        "includes_interface_itself": iface in impl,
        "by_package": dict(sorted(by_pkg.items())),
        "classes": impl,
        "cross_check_suffix_based": {
            "criterion": "类名以 Task 结尾（全平台，任意包）",
            "total": len(suffix),
            "note": "口径不同，不可与主口径混用",
        },
    }


def stat_template(classes, methods):
    """Template：区分「声明 getTemplateOutMap()」与「类名后缀 Template」两种口径。"""
    decl = sorted({fq for fq, _, raw in methods if "#getTemplateOutMap()" in raw})
    by_pkg = Counter(".".join(c.split(".")[:-1]) for c in decl)
    suffix = sorted({c for c in classes if c.split(".")[-1].endswith("Template")})
    base = sorted({c for c in classes if ".autocode.template.base." in c})
    return {
        "criterion_A_declare_getTemplateOutMap": {
            "desc": "声明 getTemplateOutMap() 的类去重（≈实际参与生成的模板载体）",
            "total": len(decl),
            "by_package": dict(sorted(by_pkg.items())),
            "classes": decl,
        },
        "criterion_B_suffix_Template": {
            "desc": "类名以 Template 结尾（全平台，含非 UDC 生成器）",
            "total": len(suffix),
            "by_package": dict(sorted(Counter(
                ".".join(c.split(".")[:-1]) for c in suffix).items())),
            "note": "含 bpm/cip/portal 等无关模板，不可直接当生成器模板数",
        },
        "template_base_abstract": {
            "desc": "udc.autocode.template.base 包内抽象基类",
            "total": len(base),
            "classes": base,
        },
    }


def stat_codegen_templates_json():
    """模板清单：直接解析 _codegen_templates.json。"""
    raw = read_tar_member("udc-biz-5.3.517/_codegen_templates.json")
    if raw is None:
        return {"error": "member not found"}
    d = json.loads(raw)
    groups = {k: len(v) for k, v in d.items()}
    versions = Counter(k.split("/")[0] for k in d)
    total = sum(groups.values())
    return {
        "criterion": "41 组 value 数组元素总数（含目录占位项，如 'third/'）",
        "total_entries": total,
        "group_count": len(d),
        "version_breakdown": dict(sorted(versions.items())),
        "groups": dict(sorted(groups.items())),
        "note": "条目含目录占位（以 / 结尾），非纯文件数",
    }


def stat_dao(methods):
    dao = "com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao"
    abs_dao = "com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao"
    m1 = [raw for fq, _, raw in methods if fq == dao]
    m2 = [raw for fq, _, raw in methods if fq == abs_dao]
    n1 = [re.match(r"[^#]+#([\w$]+)\(", r).group(1) for r in m1]
    n2 = [re.match(r"[^#]+#([\w$]+)\(", r).group(1) for r in m2]
    return {
        "AllInOneBaseDao": {
            "fqcn": dao,
            "method_count": len(m1),
            "unique_names": len(set(n1)),
            "overloads": len(n1) - len(set(n1)),
            "names": sorted(set(n1)),
        },
        "AbstractAllInOneBaseDao": {
            "fqcn": abs_dao,
            "method_count": len(m2),
            "unique_names": len(set(n2)),
            "overloads": len(n2) - len(set(n2)),
        },
        "note": "接口声明方法数；实现类继承关系与覆盖情况未在此脚本判定",
    }


def stat_appservice():
    """AppService：区分 类 / 接口 / 实现 / 方法 四个口径。"""
    with gzip.open(SVC, "rt", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    rows = [l for l in lines if "#" in l]
    owners = {l.split("#", 1)[0] for l in rows}
    iface_like = {o for o in owners if o.endswith("AppService")}
    impl_like = {o for o in owners if o.endswith("AppServiceImpl")}
    return {
        "data_source": "docs/audit/reference/svc-app-service.txt.gz",
        "total_lines": len(lines),
        "rows_with_method": len(rows),
        "distinct_owner_classes": len(owners),
        "owner_named_AppService": len(iface_like),
        "owner_named_AppServiceImpl": len(impl_like),
        "other_owners": len(owners) - len(iface_like) - len(impl_like),
        "note": "该文件是 AppService→jar 映射，owner 可能同时含接口与实现",
    }


def stat_entity_service(methods):
    """udc 域实体 Service 接口。"""
    pat = re.compile(r"udc.*\.(api|service)\.\w+Service$")
    ents = sorted({fq for fq, _, _ in methods if pat.search(fq)})
    return {
        "criterion": r"类名匹配 udc.*\.(api|service)\.\w+Service$ 且有方法行",
        "total": len(ents),
        "sample": ents[:10],
    }


# ---------------------------------------------------------------- 主流程
def build():
    lines = read_sig_lines()
    classes, methods = parse_sig(lines)
    out = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platform_version": PLATFORM_VER,
        "data_sources": {
            "signatures": os.path.relpath(SIG, ROOT).replace("\\", "/"),
            "svc_app_service": os.path.relpath(SVC, ROOT).replace("\\", "/"),
            "platform_tgz": os.path.relpath(PLATFORM_TGZ, ROOT).replace("\\", "/"),
        },
        "script": "scripts/research/stats_registry.py",
        "stats": {
            "signatures": stat_signatures(lines, classes, methods),
            "codetask": stat_codetask(classes, methods),
            "template": stat_template(classes, methods),
            "codegen_templates_json": stat_codegen_templates_json(),
            "dao": stat_dao(methods),
            "appservice": stat_appservice(),
            "entity_service": stat_entity_service(methods),
        },
    }
    return out


def to_md(d):
    s = d["stats"]
    L = []
    L.append("# 统计结果（由 scripts/research/stats_registry.py 生成）")
    L.append("")
    L.append(f"- 生成时间：{d['generated_at']}")
    L.append(f"- 平台版本：{d['platform_version']}")
    L.append(f"- 脚本：`{d['script']}`")
    L.append("")
    L.append("## 1. 签名库")
    sig = s["signatures"]
    L.append(f"| 指标 | 值 |")
    L.append("|---|---|")
    L.append(f"| 总行数 | {sig['total_lines']} |")
    L.append(f"| 类声明 | {sig['class_declarations']} |")
    L.append(f"| 方法声明 | {sig['method_declarations']} |")
    L.append("")
    L.append("## 2. CodeTask 实现")
    ct = s["codetask"]
    L.append(f"- 口径：{ct['criterion']}")
    L.append(f"- **总数：{ct['total']}**")
    L.append(f"- 含接口自身 `CodeTask`：{ct['includes_interface_itself']}")
    L.append("")
    L.append("| 包 | 数量 |")
    L.append("|---|---|")
    for k, v in ct["by_package"].items():
        L.append(f"| `{k}` | {v} |")
    L.append("")
    L.append(f"对照口径（{ct['cross_check_suffix_based']['criterion']}）："
             f"{ct['cross_check_suffix_based']['total']} 个 —— 不可与主口径混用")
    L.append("")
    L.append("## 3. Template")
    t = s["template"]
    a = t["criterion_A_declare_getTemplateOutMap"]
    b = t["criterion_B_suffix_Template"]
    L.append(f"**口径 A（主）：{a['desc']}** → **{a['total']}**")
    L.append("")
    L.append("| 包 | 数量 |")
    L.append("|---|---|")
    for k, v in a["by_package"].items():
        L.append(f"| `{k}` | {v} |")
    L.append("")
    L.append(f"**口径 B（对照）：{b['desc']}** → {b['total']}")
    L.append(f"> {b['note']}")
    L.append("")
    L.append(f"**template.base 抽象基类** → {t['template_base_abstract']['total']}")
    L.append("")
    L.append("## 4. 模板清单 _codegen_templates.json")
    j = s["codegen_templates_json"]
    L.append(f"- 口径：{j['criterion']}")
    L.append(f"- **条目总数：{j['total_entries']}**")
    L.append(f"- 分组数：{j['group_count']}")
    L.append(f"- 版本分布：{j['version_breakdown']}")
    L.append(f"- 注意：{j['note']}")
    L.append("")
    L.append("## 5. DAO")
    dao = s["dao"]
    for k in ("AllInOneBaseDao", "AbstractAllInOneBaseDao"):
        v = dao[k]
        L.append(f"- `{k}`：方法 {v['method_count']} 个，"
                 f"唯一名 {v['unique_names']}，重载 {v['overloads']}")
    L.append(f"- 注意：{dao['note']}")
    L.append("")
    L.append("## 6. AppService")
    ap = s["appservice"]
    L.append(f"- 数据源：`{ap['data_source']}`")
    L.append(f"- 总行数：{ap['total_lines']}")
    L.append(f"- 含方法行：{ap['rows_with_method']}")
    L.append(f"- 唯一 owner 类：{ap['distinct_owner_classes']}")
    L.append(f"- 名字以 AppService 结尾：{ap['owner_named_AppService']}")
    L.append(f"- 名字以 AppServiceImpl 结尾：{ap['owner_named_AppServiceImpl']}")
    L.append(f"- 其他 owner：{ap['other_owners']}")
    L.append(f"> {ap['note']}")
    L.append("")
    L.append("## 7. udc 实体 Service 接口")
    es = s["entity_service"]
    L.append(f"- 口径：{es['criterion']}")
    L.append(f"- **总数：{es['total']}**")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    d = build()
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(f"written: {a.out}")
    if a.md:
        print(to_md(d))
    elif not a.out:
        print(json.dumps(d, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

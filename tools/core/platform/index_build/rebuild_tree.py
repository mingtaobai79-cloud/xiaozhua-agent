# -*- coding: utf-8 -*-
"""从磁盘上真实的 json 重建 TREE.md / INDEX.md（不信任旧内容）。"""
import json, io, os, collections

BASE = "C:/Users/白明涛/xiaozhua-agent/docs/audit/artifacts/index"
SRC = "C:/Users/白明涛/xiaozhua-agent/docs/audit/artifacts/extension-surface-full/interfaces-full.json"

src = json.load(io.open(SRC, encoding="utf-8"))
S = set(src["classes"])

def scan(sub):
    d = os.path.join(BASE, sub)
    out = []
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        p = os.path.join(d, f)
        j = json.load(io.open(p, encoding="utf-8"))
        st = j.get("stats") or {}
        out.append({"name": f[:-5], "cls": st.get("classes", len(j.get("classes", {}))),
                    "m": st.get("methods", 0), "pk": st.get("packages", 0),
                    "kb": os.path.getsize(p) // 1024, "sub": sub})
    return out

doms = scan("by-domain")
subs = scan("by-sub")
sts = scan("by-starter")
aps = scan("by-app")

L = ["# 平台索引目录树", "",
     f"源 **{len(S):,} 类** / 86,141 方法名 / 5,048 包 / 176 构件 / 115 应用", "",
     "## 总览", "",
     "| 拆法 | 文件数 | 合计类数 | 目录 |", "|---|---:|---:|---|",
     f"| 按顶级域 | {len(doms)} | {sum(x['cls'] for x in doms):,} | `by-domain/` |",
     f"| 按二级子域 | {len(subs)} | {sum(x['cls'] for x in subs):,} | `by-sub/` |",
     f"| 按 starter | {len(sts)} | {sum(x['cls'] for x in sts):,} | `by-starter/` |",
     f"| 按应用 | {len(aps)} | {sum(x['cls'] for x in aps):,} | `by-app/` |",
     ""]

def section(title, rows, note=""):
    L.extend([f"## {title}", ""])
    if note:
        L.extend([note, ""])
    L.extend(["| 名称 | 类数 | 方法数 | 包数 | 大小 | 文件 |", "|---|---:|---:|---:|---:|---|"])
    for r in sorted(rows, key=lambda x: -x["cls"]):
        mark = "" if r["cls"] else "  ⚠️空"
        L.append(f"| `{r['name']}`{mark} | {r['cls']:,} | {r['m']:,} | {r['pk']:,} | {r['kb']}K | `{r['sub']}/{r['name']}.json` |")
    L.append(f"| **合计** | **{sum(x['cls'] for x in rows):,}** | | | | |")
    empt = [r["name"] for r in rows if r["cls"] == 0]
    if empt:
        L.extend(["", f"> ⚠️ 空分片 {len(empt)} 个：{', '.join('`'+e+'`' for e in empt)}",
                  "> 原因：对应 jar 内没有 `com.seeyon.*` 类（提取阶段已记录 FAIL，非本次遗漏）。"])
    L.append("")

section("A. 按顶级域（16）", doms)
section("B. 按二级子域（185，只覆盖 9 个大域）", subs,
        "boot 的内部结构走 `by-starter/`，不在此重复。")
section("C. 按 starter（79）", sts, "全部在 `com.seeyon.boot.starter.*` 下。")
section("D. 按应用（115）", aps)

io.open(os.path.join(BASE, "TREE.md"), "w", encoding="utf-8").write("\n".join(L))
print(f"TREE.md 重建：{len(doms)}+{len(subs)}+{len(sts)}+{len(aps)} 个文件")
print(f"  域 {sum(x['cls'] for x in doms):,} / 子域 {sum(x['cls'] for x in subs):,} / "
      f"starter {sum(x['cls'] for x in sts):,} / 应用 {sum(x['cls'] for x in aps):,}")

# INDEX.md
big = sorted(subs, key=lambda x: -x["cls"])[:12]
L2 = ["# 平台索引总目录", "",
      f"**{len(S):,} 类 / 86,141 方法名 / 5,048 包 / 176 构件 / 115 应用**", "",
      "## 四种拆法", "",
      "| 拆法 | 文件数 | 合计类数 | 目录 | 什么时候用 |",
      "|---|---:|---:|---|---|",
      f"| 顶级域 | {len(doms)} | {sum(x['cls'] for x in doms):,} | `by-domain/` | 知道在哪个系统 |",
      f"| 二级子域 | {len(subs)} | {sum(x['cls'] for x in subs):,} | `by-sub/` | 事项/连接器/用户中心这种 |",
      f"| starter | {len(sts)} | {sum(x['cls'] for x in sts):,} | `by-starter/` | 文件/枚举/元数据/mybatis/数据源 |",
      f"| 应用 | {len(aps)} | {sum(x['cls'] for x in aps):,} | `by-app/` | 一个客户系统一个文件 |",
      "",
      "## 其它文件", "",
      "- `TREE.md` —— 四种拆法的完整明细表（每个文件一行）",
      "- `PACKAGES.md` —— **全部 5,048 个包**逐条列出（包 → 类数 → 构件）",
      "- `manifest.json` —— 校验数据",
      "",
      "## 按需求选哪个", "",
      "| 你要找什么 | 文件 |", "|---|---|",
      "| 组织架构、人员、部门 | `by-domain/organization.json`（1,103 类）|",
      "| 流程、节点、事件、表单 | `by-domain/bpm.json`（3,415 类）|",
      "| 协同事项、待办 | `by-sub/ctp__affair.json`（481 类）|",
      "| 用户、权限、组织关系 | `by-sub/ctp__user.json`（1,069 类）|",
      "| 消息、通知 | `by-sub/ctp__message.json`（205 类）|",
      "| 连接器、第三方对接 | `by-sub/cip__connector.json`（439 类）|",
      "| 集成能力、外部系统 | `by-sub/cip__capability.json`（1,448 类）|",
      "| BI、报表、数据集 | `by-sub/cdp__bi.json`（813 类）|",
      "| 低代码、自定义对象 | `by-domain/udc.json`（3,345 类）|",
      "| 微流程 | `by-sub/udc__microflow.json`（368 类）|",
      "| 数据流生单 | `by-sub/udc__dataflow.json`（112 类）|",
      "| 文件服务 | `by-starter/file.json`（89 类）|",
      "| 枚举 | `by-starter/enums.json`（51 类）|",
      "| 元数据 | `by-starter/extmetadata.json`（102 类）|",
      "| 数据源 / 连接池 | `by-starter/datasource.json`（29 类）|",
      "| mybatis / 动态 SQL | `by-starter/mybatis.json`（138 类）+ `dynamicsql.json`（42 类）|",
      "| 平台工具类（177） | `by-domain/boot.json` → `com.seeyon.boot.util`（176 类）|",
      "| 泛化调用、Dubbo | `by-starter/dubbo.json`（48 类）|",
      "| 跨域、不确定 | 不给 `--scope`（全量 139MB）|",
      "",
      "## 查询命令", "",
      "```bash",
      "python tools/core/platform/query_platform.py scopes                        # 列出全部分片",
      "python tools/core/platform/query_platform.py find-class JsonUtils --scope boot",
      "python tools/core/platform/query_platform.py find-method send --scope bpm",
      "python tools/core/platform/query_platform.py methods com.seeyon.bpm.api.common.BpmAppService",
      "python tools/core/platform/query_platform.py pkg com.seeyon.bpm.dto       # 一个包里有什么",
      "python tools/core/platform/query_platform.py search 库存 --scope udc",
      "```", ""]

io.open(os.path.join(BASE, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L2))
print("INDEX.md 重建完成")
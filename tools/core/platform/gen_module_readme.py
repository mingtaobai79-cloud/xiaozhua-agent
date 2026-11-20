# -*- coding: utf-8 -*-
"""生成应用模块 README（facade + biz + web 三段）。

用法：
  python gen_module_readme.py organization \
      --group 03-business-app --name organization \
      --title "组织架构（organization）"
"""
import json, io, os, sys, re, collections, argparse

REPO = "C:/Users/白明涛/xiaozhua-agent"
IDX = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
FACADE = f"{REPO}/docs/audit/artifacts/facade"
MODULES = f"{REPO}/core/facts/modules"
APPS = "D:/software/hermes/cache/scratch/rebuild/apps.json"

sys.path.insert(0, os.path.join(REPO, "tools/core/platform"))
import gen_app_doc  # noqa


def load_idx():
    return json.load(io.open(IDX, encoding="utf-8"))


def arts_of(dom):
    """该域涉及的构件及类数"""
    d = load_idx()
    c = collections.Counter()
    for fq, cl in d["classes"].items():
        if fq.startswith(f"com.seeyon.{dom}."):
            c[cl.get("pkg")] += 1
    return c


def classes_matching(d, dom, pred):
    return [(fq, cl) for fq, cl in d["classes"].items()
            if fq.startswith(f"com.seeyon.{dom}.") and pred(fq, cl)]


def nm(cl):
    return len([m for m in (cl.get("methods") or []) if not m["name"].startswith("lambda$")])


def svc_role(fq, cl):
    """按方法名动词分布归纳服务职责（证据：方法名，非推测表结构）"""
    short = fq.split(".")[-1].replace("Service", "")
    ent = gen_app_doc._ent(short) or short
    verbs = collections.Counter()
    for m in (cl.get("methods") or []):
        if m["name"].startswith("lambda$"):
            continue
        words = gen_app_doc.split_camel(m["name"])
        for w in words[:2]:
            if w.lower() in gen_app_doc.VERB_WORDS:
                verbs[gen_app_doc.VERB_WORDS[w.lower()]] += 1
                break
    if not verbs:
        return f"{ent}（无业务方法，可能为纯装配类）"
    top = " / ".join(f"{k}×{v}" for k, v in verbs.most_common(3))
    return f"{ent} · {top}"


def group_con(controllers):
    g = collections.defaultdict(list)
    for fq, cl in controllers:
        n = fq.split(".")[-1].replace("Controller", "")
        if n.startswith("Refer"):
            k = "推送/被引用（Refer*）"
        elif n.startswith("OrgExternal"):
            k = "外部人员（External*）"
        elif n.startswith("SelectPeople"):
            k = "选人组件（SelectPeople*）"
        elif n.startswith("OrgTeam") or n.startswith("OrgUnitTeam") or n.startswith("OrgPersonalTeam"):
            k = "团队（*Team*）"
        elif n.startswith("OrgBusiness"):
            k = "业务线（Business*）"
        elif n.startswith("OrgSync") or n.startswith("OrgInit") or n.startswith("OrgTransfer"):
            k = "同步/初始化/迁移"
        elif "VisitPermission" in n:
            k = "访问权限"
        else:
            k = "核心实体 CRUD"
        g[k].append((fq, cl))
    return g


def render(dom, group, name, title, extra_biz="", extra_web="", extra_chain=""):
    d = load_idx()
    o = json.load(io.open(f"{FACADE}/{dom}.json", encoding="utf-8"))
    arts = arts_of(dom)
    total = sum(arts.values())

    L = [f"# {title}", ""]

    L += ["## 一句话", "",
          f"`com.seeyon.{dom}` 域的**可调用接口面**：{len(arts)} 个构件、{total:,} 个类、"
          f"{o['n_facades']} 个 facade 接口 / {o['n_methods']} 个方法。", ""]

    # 构件
    L += ["## 一、构件清单", "", "| 构件 | 层 | 类数 |", "|---|---|---:|"]
    for a, n in arts.most_common():
        layer = ("facade" if a.endswith("-facade") else
                 "web" if a.endswith("-web") else
                 "biz" if a.endswith("-biz") else
                 "api" if a.endswith("-api") else
                 "common" if a.endswith("-common") else "其他")
        L.append(f"| `{a}` | {layer} | {n:,} |")
    L.append(f"| **合计** | | **{total:,}** |")
    L.append("")

    # 分层规律
    L += ["## 二、分层规律（写代码前必读）", "",
          f"`com.seeyon.{dom}` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：", "",
          "| 接口族 | 包 | 能力 | 什么时候用 |", "|---|---|---|---|",
          "| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |",
          "| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |",
          "| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |",
          "",
          "调用顺序建议：", "",
          "```",
          "知道 id       →  XxxCoreAppService.selectXxxById        （最轻）",
          "知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData",
          "要写          →  XxxBaseAppService.create / update",
          "```", ""]

    if extra_biz:
        L += [extra_biz, ""]

    # facade
    body, o2, unc = gen_app_doc.render(dom)
    L += [body]

    # biz
    services = classes_matching(d, dom, lambda fq, cl:
                                (".domain." in fq or ".biz." in fq)
                                and fq.split(".")[-1].endswith("Service")
                                and cl.get("kind") == "class")
    L += ["## biz 层：领域服务", "",
          f"共 {len(services)} 个领域服务，下表列**方法数最多的 {min(len(services),40)} 个**。",
          "职责由**该服务方法名的动词分布**归纳，不是猜的。", "",
          "| 服务 | 方法数 | 职责（按方法名统计） |", "|---|---:|---|"]
    for fq, cl in sorted(services, key=lambda x: -nm(x[1]))[:40]:
        short = fq.split(".")[-1]
        L.append(f"| `{short}` | {nm(cl)} | {svc_role(fq, cl)} |")
    L.append("")

    # 事件
    events = classes_matching(d, dom, lambda fq, cl: fq.split(".")[-1].endswith("Event"))
    listeners = classes_matching(d, dom, lambda fq, cl: fq.split(".")[-1].endswith("EventListener"))
    L += ["## biz 层：事件与监听", "",
          f"事件 {len(events)} 个 · 监听器 {len(listeners)} 个。", "",
          "**领域事件**（实体变更时发，本地事务内）：", ""]
    ev_by = collections.defaultdict(list)
    for fq, cl in events:
        n = fq.split(".")[-1]
        m = re.match(r"^(Org)?(\w+?)(Create|Update|Delete)", n)
        k = m.group(2) if m else n.replace("Event", "")
        ev_by[k].append(n)
    L += ["| 实体 | 事件 |", "|---|---|"]
    for k in sorted(ev_by):
        L.append(f"| {k} | {', '.join('`'+x+'`' for x in sorted(set(ev_by[k])))} |")
    L.append("")
    if listeners:
        L += ["**监听器**（在事务内做联动）：", ""]
        L += ["| 监听器 | 方法数 |", "|---|---:|"]
        for fq, cl in sorted(listeners, key=lambda x: -nm(x[1])):
            L.append(f"| `{fq.split('.')[-1]}` | {nm(cl)} |")
        L.append("")

    # web
    cons = classes_matching(d, dom, lambda fq, cl: ".controller." in fq
                            and fq.split(".")[-1].endswith("Controller"))
    L += ["## web 层：Controller", "",
          f"共 {len(cons)} 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），",
          "需要时按下面两法取：", "",
          "1. 反编译 `organization-web` 的 Controller 读注解",
          "2. CDP 抓页面请求（真实路径 + 请求体）", ""]
    g = group_con(cons)
    L += ["| 分组 | Controller | 方法数 |", "|---|---|---:|"]
    for k in sorted(g):
        for fq, cl in sorted(g[k], key=lambda x: -nm(x[1])):
            L.append(f"| {k} | `{fq.split('.')[-1]}` | {nm(cl)} |")
    L.append("")

    if extra_web:
        L += [extra_web, ""]

    if extra_chain:
        L += [extra_chain, ""]

    # 手工补充片段（不在自动生成范围，重跑不会丢）
    custom = os.path.join(f"{REPO}/tools/core/platform/notes", f"{dom}.custom.md")
    if os.path.exists(custom):
        L += [io.open(custom, encoding="utf-8").read(), ""]

    # 落表
    L += ["## 落表", "",
          "⚠️ **UNVERIFIED** —— 字节码索引不含 SQL/表名，本文件不写推测的表名。", "",
          "取证路径（三条，任选其一，务必留证据）：", "",
          "1. **jar 内 mapper**：`organization-biz` 里 `*.xml` / `*Mapper.java`",
          "2. **库结构**：连 test2 的 MySQL 查 `information_schema.columns` 里 `tb_org_%`",
          "3. **运行态**：开 SQL 日志跑一次写操作，看真实表名", "",
          "在拿到上述证据前，本文件对「落哪张表」保持空。", ""]

    # 自证
    L += ["## 证据与自证", "",
          "| 内容 | 证据 | 等级 |", "|---|---|---|",
          f"| {o['n_facades']} 接口 / {o['n_methods']} 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |",
          f"| {len(services)} 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |",
          f"| {len(events)} 事件 / {len(listeners)} 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |",
          f"| {len(cons)} 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |",
          "| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |",
          f"| {unc} 个语义待定方法 | 名称不足 | `UNVERIFIED` |",
          "| REST 路径 | 未取证 | `UNVERIFIED` |",
          "| 落表 | 未取证 | `UNVERIFIED` |",
          ""]

    # 输出
    outdir = os.path.join(MODULES, group, name)
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, "README.md")
    io.open(p, "w", encoding="utf-8").write("\n".join(L))
    return p, o, len(services), len(events), len(listeners), len(cons), unc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("--group", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--title", required=True)
    a = ap.parse_args()
    p, o, ns, ne, nl, nc, unc = render(a.domain, a.group, a.name, a.title)
    print(f"{p}")
    print(f"  接口 {o['n_facades']} / 方法 {o['n_methods']} / 服务 {ns} / 事件 {ne} "
          f"/ 监听 {nl} / Controller {nc} / 待定语义 {unc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
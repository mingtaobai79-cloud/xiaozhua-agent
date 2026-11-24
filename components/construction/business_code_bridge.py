"""业务意图 → 平台代码 的关联索引（business_code_bridge）。

## 为什么需要它（这是白明涛指出来的核心问题）

只给「类签名」不够。LLM 看到 `JsonUtils.toMap(String)` 仍然不知道：
- 这是干什么用的（业务语义）
- 什么场景该用它
- 入参里每个字段填什么（中文名）
- 平台内部谁在用它（可信度）

所以要把**代码**和**业务理解**接起来，不是并列两套索引。

## 四层数据怎么接（全部离线，来自 surface-index.tar.gz）

```
① 业务意图   domains/*.md 的「用途」行
   "bpm → 流程发起/提交/退回/终止/暂停、模板、表单权限、节点权限"

② 动作 → 方法  action-index.md（682 条动作行）
   "流程 | send | BpmAppService | BpmSendDto | BpmApiAppServiceImpl | 流转第一步"

③ 接口 → 实现  impl-map.json（269 接口 / 270 实现 / jar 名）
④ DTO 中文字段  dto-meta.json（1331 DTO / 1305 有中文元信息）
   "BpmSendDto → 工作流发送dto；templateCode → 模板code"

⑤ 谁在用    consumers.json（183 接口 / 12252 类扫描）
```

## 关键设计：查询从「业务词」出发，不是从类名出发

旧路径（`platform_class_search`）：
    用户想「发起流程」→ 猜类名 → 猜错就查不到

新路径（本模块）：
    "发起流程" → 命中动作节「流程」→ send → BpmAppService
              → 入参 BpmSendDto（中文名「工作流发送dto」）
              → 字段：templateCode=模板code、currentUserId=userCode...
              → 实现 BpmApiAppServiceImpl
              → 平台内部谁在用

## 边界（必须守）

★ `action-index.md` 自己写明：BPM/组织/事项/连接器的**实现在平台服务端**，
  仓库只有接口 jar，流转追不到。这些域只能给「接口 + 入参 DTO」，
  具体行为要实测或看日志。**本模块不假装知道它们的行为。**
★ 中文元信息来自 `@DtoAttribute(value=...)` 注解，是平台自己写的，
  不是我猜的；但注解值可能和实际语义有偏差（如 currentUserId→"userCode"），
  原样呈现，不美化。
★ 查不到就说查不到，不给「大概是这个」的猜测。
"""
from __future__ import annotations

import json
import re
import tarfile
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_SURFACE_TGZ = _REPO / "fixtures" / "reference" / "surface-index.tar.gz"  # 随产品发行，不在 docs/（工作区）


def _read_member(name: str) -> str:
    """从 tar.gz 直接读一个成员（不解包到磁盘）。"""
    if not _SURFACE_TGZ.exists():
        return ""
    with tarfile.open(_SURFACE_TGZ, "r:gz") as tf:
        try:
            f = tf.extractfile(name)
            return f.read().decode("utf-8", "replace") if f else ""
        except KeyError:
            return ""


@lru_cache(maxsize=1)
def _domains() -> dict[str, dict[str, Any]]:
    """域 → {purpose, scale, interfaces}。"""
    out: dict[str, dict[str, Any]] = {}
    if not _SURFACE_TGZ.exists():
        return out
    with tarfile.open(_SURFACE_TGZ, "r:gz") as tf:
        names = [n for n in tf.getnames() if n.startswith("domains/") and n.endswith(".md")]
        for n in names:
            f = tf.extractfile(n)
            if not f:
                continue
            txt = f.read().decode("utf-8", "replace")
            dom = Path(n).stem
            purpose = ""
            scale = ""
            m = re.search(r"^> 用途：(.+)$", txt, re.M)
            if m:
                purpose = m.group(1).strip()
            m = re.search(r"^> 规模：(.+)$", txt, re.M)
            if m:
                scale = m.group(1).strip()
            # 抽接口名
            ifaces = re.findall(r"^### `(\w+)`（(\d+) 方法）", txt, re.M)
            out[dom] = {"domain": dom, "purpose": purpose, "scale": scale,
                        "interfaces": [{"name": a, "methods": int(b)} for a, b in ifaces]}
    return out


@lru_cache(maxsize=1)
def _actions() -> list[dict[str, Any]]:
    """action-index.md → 结构化动作行。

    每行：{section, method, iface, dto, impl, flow}
    """
    txt = _read_member("action-index.md")
    if not txt:
        return []

    rows: list[dict[str, Any]] = []
    section = ""
    for line in txt.splitlines():
        m = re.match(r"^## (\S+?)（(\d+)）", line)
        if m:
            section = m.group(1)
            continue
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        # 查询节是「接口 | 方法数 | 方法列表」另一种形状
        if section == "查询":
            continue
        method = cells[0].strip("`")
        iface = cells[1].strip("`")
        dto = cells[2].strip("`").strip() if len(cells) > 2 else ""
        impl = cells[3].strip("`").strip() if len(cells) > 3 else ""
        flow = cells[4].strip() if len(cells) > 4 else ""
        rows.append({"section": section, "method": method, "iface": iface,
                     "dto": "" if dto in ("—", "-", "") else dto,
                     "impl": "" if impl in ("—", "-", "") else impl,
                     "flow": flow})
    return rows


@lru_cache(maxsize=1)
def _query_ifaces() -> list[dict[str, Any]]:
    """查询节单独处理（按接口聚合，不是按方法）。"""
    txt = _read_member("action-index.md")
    if not txt:
        return []
    i = txt.find("## 查询（")
    if i < 0:
        return []
    out = []
    for line in txt[i:].splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        name = cells[0].strip("`")
        try:
            cnt = int(cells[1])
        except ValueError:
            continue
        out.append({"iface": name, "methods": cnt,
                    "sample": [x.strip().strip("`") for x in cells[2].split(",")[:6]]})
    return out


@lru_cache(maxsize=1)
def _dto_meta() -> dict[str, Any]:
    txt = _read_member("dto-meta.json")
    if not txt:
        return {}
    try:
        return json.loads(txt).get("map", {})
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _impl_map() -> dict[str, Any]:
    txt = _read_member("impl-map.json")
    if not txt:
        return {}
    try:
        return json.loads(txt).get("map", {})
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _consumers() -> dict[str, Any]:
    txt = _read_member("consumers.json")
    if not txt:
        return {}
    try:
        return json.loads(txt)
    except Exception:
        return {}


# ───────────────────── 中文名解析 ─────────────────────

def _dto_zh(dto_full: str) -> dict[str, Any]:
    """DTO 全名 → 中文类名 + 字段中文名。短名会自动补全。"""
    meta = _dto_meta()
    if not meta or not dto_full:
        return {}

    key = dto_full if dto_full in meta else ""
    if not key:
        # action-index 里只写短名（BpmSendDto），要补全
        cands = [k for k in meta if k.split(".")[-1] == dto_full]
        if len(cands) == 1:
            key = cands[0]
        elif cands:
            # 多个同名：优先 openapi 包（动作索引里的多是这类）
            pref = [k for k in cands if ".openapi." in k]
            key = (pref or cands)[0]
    if not key:
        return {}

    m = meta[key]
    fields = {}
    for fname, fmeta in (m.get("fields") or {}).items():
        v = fmeta.get("value") if isinstance(fmeta, dict) else fmeta
        if v:
            fields[fname] = v
    return {
        "fullName": key,
        "zh": (m.get("__class__") or {}).get("value", ""),
        "fields": fields,
        "fieldCount": len(fields),
    }


# ───────────────────── 对外 API ─────────────────────

def find_action(intent: str = "", domain: str = "", action: str = "",
                limit: int = 12) -> dict[str, Any]:
    """★从业务意图找平台方法：这是「代码 ↔ 业务理解」的主入口。

    参数
    ----
    intent : 业务语言，如「发起流程」「上传附件」「查询人员」「发邮件」
    domain : 域过滤（bpm/organization/file/affair/connector/...）
    action : 动作过滤（创建/修改/删除/流程/发布/导入导出/校验/启用禁用）
    limit  : 上限

    返回每条都带：方法、接口、入参 DTO（含中文字段）、实现类、平台流转第一步。
    """
    if not _SURFACE_TGZ.exists():
        return {"error": "surface-index.tar.gz 缺件，业务桥不可用",
                "intent": intent, "hits": []}

    # ★ 业务动作同义词表：把「发起」这类词映射到真实方法名 send/submit/create
    #   不做这层，滑窗匹配会让 stopCase（终止）排在 send（发起）前面。
    #   ★ 只用「业务动词」做映射。名词（人员/附件/文件）不能映射到方法名，
    #     否则「上传附件」会命中 editFileHistory（编辑），语义完全错。
    SYNONYM: dict[str, list[str]] = {
        "发起": ["send", "start", "submit"],
        "提交": ["submit", "send"],
        "撤回": ["repeal", "revoke", "withdraw"],
        "撤销": ["repeal", "revoke", "cancel"],
        "终止": ["stop", "terminate"],
        "暂停": ["pause", "suspend"],
        "退回": ["return", "reject"],
        "查询": ["select", "query", "page"],
        "上传": ["upload"],
        "下载": ["download"],
        "删除": ["delete", "remove"],
        "修改": ["update", "modify"],
        "新增": ["create", "add", "insert"],
        "创建": ["create", "add"],
        "发布": ["publish", "release"],
        "导入": ["import"],
        "导出": ["export"],
        "校验": ["check", "validate"],
        "启用": ["enable"],
        "禁用": ["disable"],
        "发邮件": ["sendnormalemail", "sendpersonalemail", "sendtemplateemail"],
        "发消息": ["sendmessage"],
        "保存草稿": ["savedraft"],
    }

    # ★ 业务名词 → 接口/类名 token（整词匹配，不做子串）
    #   用子串会把「附件」→file 命中 CipFileAppService（文件删除），语义全错。
    NOUN: dict[str, list[str]] = {
        "人员": ["orgmember", "user", "member", "people"],
        "组织": ["org"],
        "部门": ["orgunit", "department"],
        "附件": ["attachment", "storage"],
        "文件": ["file", "storage"],
        "邮件": ["email"],
        "流程": ["bpm", "affair"],
        "审批": ["bpm"],
        "日期": ["date", "systemvariable"],
        "缓存": ["cache"],
        "消息": ["message"],
    }

    intent = (intent or "").strip()
    il = intent.lower()
    hits: list[dict[str, Any]] = []

    # ★ 中文业务词要拆开匹配：「发起流程」得能命中域用途里的「流程发起」
    #   整句 substring 匹配必然 0 命中（顺序相反）。所以拆成 2~4 字滑窗。
    terms: list[str] = []
    if intent:
        terms.append(il)
        if re.search(r"[\u4e00-\u9fff]", intent):
            for n in (2, 3, 4):
                for i in range(len(intent) - n + 1):
                    w = intent[i:i + n]
                    if re.search(r"[\u4e00-\u9fff]", w):
                        terms.append(w.lower())
    terms = [t for t in dict.fromkeys(terms) if t]

    # ★ 同义词展开：业务词 → 真实方法名片段（权重最高）
    strong: list[str] = []
    for zh, ens in SYNONYM.items():
        if zh in intent:
            strong.extend(ens)
    strong = [s for s in dict.fromkeys(strong) if s]

    # ★ 名词展开：业务名词 → 接口/类名片段（中等权重，用来收窄域）
    nouns: list[str] = []
    for zh, ens in NOUN.items():
        if zh in intent:
            nouns.extend(ens)
    nouns = [s for s in dict.fromkeys(nouns) if s]

    # ① 域匹配：任一 term 命中域用途
    doms = _domains()
    hit_domains = []
    for d, info in doms.items():
        if domain and d != domain:
            continue
        p = (info.get("purpose") or "").lower()
        if not intent or any(t in p or t in d.lower() for t in terms):
            hit_domains.append(d)

    # ② 动作匹配
    acts = _actions()
    for row in acts:
        if action and row["section"] != action:
            continue
        score = 0
        if intent:
            # 同义词命中方法名 → 最高权重（"发起"→send 必须压过 "流程"→stopCase）
            for s in strong:
                if row["method"].lower() == s:
                    score += 20
                elif s in row["method"].lower():
                    score += 10
            for t in terms:
                if t in row["method"].lower():
                    score += 3
                if t in row["section"]:
                    score += 3
                if t in row["iface"].lower():
                    score += 2
                if row["dto"] and t in row["dto"].lower():
                    score += 1
            # 名词命中接口名 → 加权（"人员"→Org*，"附件"→*File*）
            for n in nouns:
                if n in row["iface"].lower():
                    score += 6
        # ★ 有强同义词命中时，没命中强同义词的行要降权，
        #   否则「上传附件」会被一堆 editFile*（只因含 file）挤上来。
        #   ★ 但降权不能反超：动词完全不沾边的（如「上传」命中 deleteByStorageKeys）
        #     必须直接剔掉，否则脏数据会排在真结果前面。
        if strong:
            method_hits_strong = any(
                row["method"].lower() == s or s in row["method"].lower()
                for s in strong)
            if not method_hits_strong:
                # 动词不对但「接口名同时含名词 token」才保留（如 Attachment 服务），
                # 仅靠 file 这种泛词命中不算。
                noun_ok = any(n in row["iface"].lower() for n in nouns)
                if not noun_ok:
                    continue
                score = int(score * 0.2)
        if action and row["section"] == action:
            score += 2
        if domain and row["iface"].lower().startswith("com.seeyon." + domain):
            score += 2
        if score == 0 and (intent or action or domain):
            continue
        hits.append({**row, "score": score, "kind": "action"})

    # ③ ★ 方法名兜底：action-index 只有 682 条，签名库有 23842 个方法。
    #     强同义词在 action-index 里查不到时（如「上传」→upload），
    #     直接扫签名库找 AppService 的匹配方法。这是最实用的一路。
    #     ★ 必须放在域级兜底之前，否则 upload 这类会被域接口挤掉。
    if strong:
        try:
            from .platform_class_index import _index as _cls_index
            classes, err = _cls_index()
            if not err:
                seen = {(h.get("iface"), h.get("method")) for h in hits}
                for cname, c in classes.items():
                    if c["bucket"] != "appservice":
                        continue
                    for m in c["methods"]:
                        mname = (m.get("name") or "").lower()
                        if not mname:
                            continue
                        bonus = 0
                        for s in strong:
                            if mname == s:
                                bonus = 40
                                break
                            if s in mname:
                                bonus = 18
                                break
                        if not bonus:
                            continue
                        # 名词收窄：命中接口名再加权
                        for n in nouns:
                            if n in c["simple"].lower():
                                bonus += 12
                        # ★ 动词在方法名 + 名词在接口名（upload + Attachment）
                        #   这是最可信的组合，给最高加成，压过泛化的 upload()
                        if any(n in c["simple"].lower() for n in nouns):
                            bonus += 30
                        key = (c["simple"], m.get("name"))
                        if key in seen:
                            continue
                        seen.add(key)
                        hits.append({
                            "section": "", "method": m.get("name"),
                            "iface": c["simple"], "ifaceFull": cname,
                            "dto": "", "impl": "", "flow": "",
                            "params": m.get("params"), "returns": m.get("returns"),
                            "score": bonus, "kind": "signature-method",
                        })
        except Exception:
            pass

    # ④ 域级兜底：动作词没命中任何方法时，给该域主要接口（信息量最低）
    if not hits and hit_domains:
        for d in hit_domains:
            for iface in doms[d]["interfaces"][:limit]:
                hits.append({"section": "", "method": "", "iface": iface["name"],
                             "dto": "", "impl": "", "flow": "",
                             "score": 1, "kind": "domain-interface",
                             "domain": d, "domainPurpose": doms[d]["purpose"],
                             "ifaceMethods": iface["methods"]})

    # ★ 排序：分数优先（分数已经体现了动词/名词命中质量），
    #   同分时 action-index 条目优先（信息量更大：有 DTO + 实现 + 流转）。
    #   ★ 不能反过来先按 kind 分层 —— 那会让脏数据（如「删除」节里的
    #     deleteByStorageKeys 出现在「下载文件」查询里，score=1）压过
    #     真正的 getDownloadUrl（score=60）。
    def _rank(h: dict[str, Any]) -> tuple:
        kind_rank = {
            "action": 0,
            "domain-interface": 1,
            "signature-method": 2,
        }.get(h.get("kind"), 3)
        return (-h["score"], kind_rank, h["iface"])

    hits.sort(key=_rank)

    # ④ 补齐：DTO 中文名 + 实现类 + 平台调用者
    impl_map = _impl_map()
    for h in hits[: int(limit)]:
        if h.get("dto"):
            zh = _dto_zh(h["dto"])
            if zh:
                h["dtoZh"] = zh
        if h.get("iface"):
            impls = impl_map.get(h["iface"]) or []
            # 短名兜底
            if not impls:
                cands = [k for k in impl_map if k.split(".")[-1] == h["iface"]]
                if cands:
                    impls = impl_map[cands[0]]
            if impls:
                h["implementations"] = impls

    out: dict[str, Any] = {
        "intent": intent, "domain": domain, "action": action,
        "total": len(hits),
        "hits": hits[: int(limit)],
        "matchedDomains": [{"domain": d, "purpose": doms[d]["purpose"],
                            "scale": doms[d]["scale"]} for d in hit_domains],
        "level": "VERIFIED_STATIC_BYTECODE",
    }
    if not hits:
        out["note"] = (
            "0 命中。换业务词试试（发起流程/上传附件/查询人员/发邮件/建应用），"
            "或用 domain 参数指定域（bpm/organization/file/affair/connector/"
            "systemvariable/formula/mybatis/dubbo/datasource/formconvert）。"
            "仍无 → 该能力标品可能没有，标 UNVERIFIED 并问用户。"
        )
    else:
        out["note"] = (
            "★ 入参 DTO 的中文字段名来自平台 @DtoAttribute 注解，原样呈现不美化。"
            "★ BPM/组织/事项/连接器的实现在平台服务端，仓库只有接口 jar，"
            "「流转」列只是第一步，不代表完整行为 —— 具体效果必须实测。"
        )
    return out


def explain_class(class_name: str) -> dict[str, Any]:
    """★给一个类，返回它在业务上是什么、怎么用、谁在用。

    这是把「代码」翻译成「业务理解」的反向入口。
    """
    if not class_name:
        return {"error": "class_name 必填"}

    simple = class_name.split(".")[-1]
    out: dict[str, Any] = {"class": class_name, "simple": simple}

    # ① 它是不是某个域的接口
    doms = _domains()
    for d, info in doms.items():
        for iface in info["interfaces"]:
            if iface["name"] == simple:
                out["domain"] = {"domain": d, "purpose": info["purpose"],
                                 "scale": info["scale"]}
                break

    # ② 它出现在哪些业务动作里
    acts = [r for r in _actions() if r["iface"] == simple or r["impl"] == simple]
    if acts:
        out["actions"] = [{"section": r["section"], "method": r["method"],
                           "dto": r["dto"], "flow": r["flow"]} for r in acts[:20]]
        out["actionCount"] = len(acts)

    # ③ 它是 DTO 吗
    zh = _dto_zh(class_name)
    if zh:
        out["asDto"] = zh

    # ④ 它是谁实现的
    impl_map = _impl_map()
    impls = impl_map.get(class_name)
    if not impls:
        cands = [k for k in impl_map if k.split(".")[-1] == simple]
        if cands:
            impls = impl_map[cands[0]]
    if impls:
        out["implementations"] = impls

    # ⑤ 平台内部谁在用它（consumers）
    cs = _consumers()
    for row in (cs.get("rows") or []):
        if row.get("simple") == simple:
            out["consumers"] = {"refCount": row.get("ref_count"),
                                "crossCount": row.get("cross_count"),
                                "refs": (row.get("refs") or [])[:10]}
            break

    if len(out) <= 2:
        out["note"] = ("这个类不在业务桥的四层数据里（域/动作/DTO/实现/消费者都无命中）。"
                       "它可能只是内部实现类；用 platform_class_search 看签名。")
    return out


def explain_dto(dto_name: str) -> dict[str, Any]:
    """DTO 的中文类名 + 全部字段中文名（写代码填参数时用）。"""
    zh = _dto_zh(dto_name)
    if not zh:
        return {"dto": dto_name, "note": "该 DTO 无中文元信息（平台没写 @DtoAttribute，或名字不对）"}
    return {"dto": dto_name, **zh,
            "level": "VERIFIED_STATIC_BYTECODE",
            "source": "@DtoAttribute 注解（平台自己写的，非推测）"}


def domain_map() -> dict[str, Any]:
    """全部域的用途一览（业务能力地图）。"""
    doms = _domains()
    return {
        "domains": [{"domain": d, "purpose": v["purpose"], "scale": v["scale"],
                     "interfaceCount": len(v["interfaces"]),
                     "topInterfaces": [i["name"] for i in v["interfaces"][:5]]}
                    for d, v in sorted(doms.items())],
        "total": len(doms),
        "note": "用途行逐字来自 surface-index 的 domains/*.md，非推测。",
    }


def stats() -> dict[str, Any]:
    """业务桥数据规模。"""
    doms = _domains()
    acts = _actions()
    qs = _query_ifaces()
    meta = _dto_meta()
    impl = _impl_map()
    cs = _consumers()
    return {
        "source": "fixtures/reference/surface-index.tar.gz",
        "domains": len(doms),
        "actionRows": len(acts),
        "queryInterfaces": len(qs),
        "dtoWithZhMeta": len(meta),
        "implMappedInterfaces": len(impl),
        "consumerRows": len(cs.get("rows") or []),
        "consumerScannedClasses": cs.get("scanned_classes"),
        "level": "VERIFIED_STATIC_BYTECODE",
    }

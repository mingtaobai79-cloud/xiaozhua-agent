"""业务动作 → 标品能力 反查索引（business_action_index）。

## 解决什么问题

`microflow_service_catalog` 只能按**类名/方法名子串**查：

    query="BpmAppService"  → 4 个服务（能查到）
    query="发起流程"        → 0 个（查不到）

所以 LLM 写扩展代码或搭微流程时，**根本不知道标品已经有现成能力**，
于是自己手搓：自己拼 SQL 查组织、自己发 HTTP 调流程、自己算日期。
这是「不会用标品」的机制性根因 —— 不是 LLM 笨，是索引的检索面错了。

本模块建一张「业务词 → (接口, 方法, 入参 DTO, 依赖 jar)」的表，
让 LLM 能用**业务语言**反查到标品能力，并在计划阶段就把
「该用标品还是自己写」摆到台面上。

## 数据来源（全部离线，不联网）

- `docs/audit/signatures.txt.gz`          245709 行类/方法签名（英文）
- `core/facts/standard-product/appservice-dto-fields.md`  高频 DTO 中文说明
- `core/facts/standard-product/business-action-index.md`  2258 个方法按动作归类
- 本文件内 `CURATED`  人工整理的高频业务动作（中文 → 接口/方法）

## 边界

★ 只做「查到」，不做「决定」。查到多个候选时全部返回，让人/LLM 选，
  不替用户挑。查不到就明说没有，绝不编一个方法名出来。
★ `CURATED` 里每条都标 `evidence`，来自粗体实测或平台 javap，
  **不允许出现「大概应该是」的条目**。
"""
from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_SIG = _REPO / "docs" / "audit" / "signatures.txt.gz"

# ───────────────────────────── 手工整理的高频业务动作 ─────────────────────────────
# 结构：中文业务词（含同义词） → 条目
# 每条必须有 evidence，指向可核对的来源（禁止臆造方法名）

CURATED: list[dict[str, Any]] = [
    # ---- BPM 流程 ----
    {"terms": ["发起流程", "发起审批", "提交审批", "走流程", "发起工作流"],
     "service": "com.seeyon.bpm.api.common.BpmAppService",
     "method": "send",
     "dto": "com.seeyon.bpm.api.common.dto.BpmSendDto",
     "returns": "BpmSendResultDto",
     "keyFields": ["templateCode/templateId（二选一）", "currentUserId", "orgId",
                   "formRecordId", "parameterData（键=实体属性名）"],
     "evidence": "appservice-dto-fields.md §7.2 逐字字段表 / business-action-index「流程 22 个方法全在 BpmAppService」"},
    {"terms": ["提交", "提交流程", "送审"],
     "service": "com.seeyon.bpm.api.common.BpmAppService", "method": "submit",
     "dto": "BpmSubmitDto", "returns": "BpmSubmitResultDto", "keyFields": [],
     "evidence": "appservice-dto-fields.md §7.2「submit() → BpmSubmitDto（10 字段）」"},
    {"terms": ["保存草稿", "暂存流程"],
     "service": "com.seeyon.bpm.api.common.BpmAppService", "method": "saveDraft",
     "dto": "BpmSaveDraftDto", "returns": "", "keyFields": [],
     "evidence": "appservice-dto-fields.md §7.2"},

    # ---- 组织人员 ----
    {"terms": ["查人", "查人员", "按条件查人", "找人", "取人员信息"],
     "service": "com.seeyon.organization.api.OrgCommonAppService",
     "method": "（按 OrgUnitDto / SelectPeopleDataDto 查，见 action-index 查询 1197 项）",
     "dto": "com.seeyon.organization.api.dto.OrgUnitDto / SelectPeopleDataDto",
     "returns": "", "keyFields": [],
     "evidence": "appservice-dto-fields.md §7.2「组织侧 OrgCommonAppService 入参多为 OrgUnitDto / SelectPeopleDataDto」；"
                 "标准品域表面表 organization-facade 391 类/51 接口/6108 方法"},
    {"terms": ["查组织", "组织机构", "部门树", "单位信息"],
     "service": "com.seeyon.organization.api.OrgUnitBaseAppService",
     "method": "（Base / Core 两套，查询类）",
     "dto": "com.seeyon.organization.api.dto.OrgUnitDto",
     "returns": "", "keyFields": [],
     "evidence": "standard-product-appservice-surfaces.md §7.1「组织域分 Base / Core 两套」"},

    # ---- 事项 / 待办 ----
    {"terms": ["待办", "事项", "待办列表", "我的待办"],
     "service": "com.seeyon.ctp.affair.api.AffairUdcAppService",
     "method": "（UDC 侧接缝，*ForUdc 方法族）",
     "dto": "com.seeyon.ctp.affair.api.dto.AffairSimpleDto",
     "returns": "", "keyFields": ["AffairSimpleDto 61 字段"],
     "evidence": "appservice-dto-fields.md §7.2「事项侧 AffairUdcAppService 用 AffairSimpleDto（61 字段）」"},

    # ---- 文件 ----
    {"terms": ["上传文件", "附件上传", "存文件", "文件存证"],
     "service": "com.seeyon.boot.starter.file.api.StorageService",
     "method": "（三桶：public/private/temp）",
     "dto": "", "returns": "", "keyFields": [],
     "evidence": "INDEX.md standard-product 格⑤「文件 StorageService+StorageSpi 三桶」；"
                 "appservice-cookbook.md §4 文件上传/下载"},

    # ---- 枚举 ----
    {"terms": ["枚举", "字典", "选项值", "下拉数据"],
     "service": "com.seeyon.boot.starter.enums.api.EnumService",
     "method": "（Service/AppService 双层风格）",
     "dto": "", "returns": "", "keyFields": [],
     "evidence": "INDEX.md standard-product 格⑤「枚举 Service/AppService 双层风格」；"
                 "standard-product-appservice-surfaces.md 枚举域 51 类/4 接口/754 方法"},

    # ---- 系统变量 / 日期 ----
    {"terms": ["系统变量", "当前用户", "当前日期", "系统日期", "租户信息"],
     "service": "com.seeyon.boot.starter.systemvariable.api.SystemVariableUtils",
     "method": "（126 静态面，288 个变量名）",
     "dto": "", "returns": "", "keyFields": [],
     "evidence": "INDEX.md standard-product 格⑤「系统变量 SystemVariableUtils 126 静态面」"},
    {"terms": ["日期格式化", "日期计算", "加天数", "日期转文本"],
     "service": "（表达式函数，不是 AppService）",
     "method": "dateToString / addDay / dateDiff",
     "dto": "", "returns": "STRING",
     "keyFields": ["走 /service/udc/expression/check + /transform 编译"],
     "evidence": "core/facts/udc/expression/functions.md 88 个函数；"
                 "DateFunction 230 个函数名（enums-and-constants.md）"},
]

# 不该重复造轮子的标品域（写扩展代码前必须确认「这里有没有现成的」）
NO_REINVENT = {
    "organization": "组织/人员/部门/岗位 —— 查 OrgCommonAppService / OrgUnitBaseAppService",
    "bpm": "流程发起/提交/退回/加签 —— 查 BpmAppService（22 个方法）",
    "affair": "待办/事项 —— 查 AffairUdcAppService / AffairMicroflowAppService",
    "file": "文件上传下载 —— 查 StorageService（三桶）",
    "enum": "枚举/字典 —— 查 EnumService / EnumAppService",
    "systemvariable": "系统变量/当前用户/日期 —— 查 SystemVariableUtils",
    "expression": "日期/文本/列表函数 —— 查 88 个表达式函数，别手写 Java",
    "connector": "对接外部系统 —— 先查 cip-connector 的 *ProviderService 扩展点族",
}


# ───────────────────────────── 检索 ─────────────────────────────

def _load_signatures() -> tuple[list[str], str]:
    if not _SIG.exists():
        return [], "signatures.txt.gz 不存在（离线索引缺件）"
    with gzip.open(_SIG, "rt", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines(), ""


def search(term: str, limit: int = 10) -> dict[str, Any]:
    """按业务语言（中文）或接口名查标品能力。

    两路检索：
      ① CURATED：中文业务词 → 已知标品能力（精确、带字段说明）
      ② 签名库：接口名/方法名子串（英文，兜底）
    """
    term = (term or "").strip()
    if not term:
        return {"query": term, "hits": [], "note": "term 为空",
                "no_reinvent_hint": NO_REINVENT}

    hits: list[dict[str, Any]] = []
    t = term.lower()

    # ① 业务词命中
    for row in CURATED:
        if any(term in x or x in term for x in row["terms"]) or \
           any(t in x.lower() for x in row["terms"]):
            hits.append({"match": "业务词:" + "/".join(
                [x for x in row["terms"] if term in x or x in term][:3] or row["terms"][:2]),
                "service": row["service"], "method": row["method"],
                "inputDto": row["dto"], "returns": row["returns"],
                "keyFields": row["keyFields"], "evidence": row["evidence"],
                "level": "VERIFIED_STATIC_BYTECODE"})

    # ② 签名库兜底（只找 AppService，避免淹没）
    lines, err = _load_signatures()
    if not err:
        lim = max(0, int(limit) - len(hits))
        n = 0
        for line in lines:
            if n >= lim:
                break
            low = line.lower()
            if t in low and "AppService" in line:
                hits.append({"match": "签名:" + t, "signature": line.strip()[:300],
                             "level": "VERIFIED_STATIC_BYTECODE"})
                n += 1

    return {
        "query": term,
        "hits": hits[: int(limit)],
        "total": len(hits),
        "no_reinvent_hint": NO_REINVENT,
        "note": ("命中 0 条时不要自己发明方法名：先换中文业务词再查，"
                 "或用 signature_search 按包/类名精确查；仍无 → 标 UNVERIFIED 问用户。"
                 if not hits else
                 "多条命中时全部列出，不替用户挑；确认入参 DTO 字段后再写代码。"),
    }


def suggest_for_capability(capability: str) -> list[dict[str, Any]]:
    """给一句业务能力描述，返回可能相关的标品域（用于计划阶段提醒）。

    只做「提醒有现成的」，不判断能不能完全覆盖 —— 覆盖度要人看。
    """
    cap = (capability or "")
    out = []
    kw = {
        "organization": ["人员", "人", "组织", "部门", "岗位", "机构", "单位"],
        "bpm": ["流程", "审批", "发起", "提交", "送审", "退回"],
        "affair": ["待办", "事项", "任务"],
        "file": ["文件", "附件", "上传", "下载", "存证"],
        "enum": ["枚举", "字典", "选项", "下拉"],
        "systemvariable": ["当前用户", "当前日期", "租户", "系统变量"],
        "expression": ["日期", "时间", "格式化", "计算"],
        "connector": ["外部接口", "第三方", "对接", "集成"],
    }
    for domain, words in kw.items():
        if any(w in cap for w in words):
            out.append({"domain": domain, "hint": NO_REINVENT[domain]})
    return out


def render_markdown(limit: int = 0) -> str:
    """给宿主 LLM 的 markdown 片段（塞进组装提示词用）。"""
    lines = ["## 标品已有能力（写代码前先看这里，不要重复造轮子）", ""]
    rows = CURATED if not limit else CURATED[:limit]
    for r in rows:
        lines.append("- **%s** → `%s#%s`" % ("/".join(r["terms"][:2]),
                                            r["service"], r["method"]))
        if r["dto"]:
            lines.append("    - 入参：`%s`" % r["dto"])
        if r["keyFields"]:
            lines.append("    - 关键字段：%s" % "；".join(r["keyFields"]))
    lines += ["", "### 这些域平台已有实现，不要自己造", ""]
    for k, v in NO_REINVENT.items():
        lines.append("- **%s**：%s" % (k, v))
    return "\n".join(lines)

"""BI 域(cdp-data) 与 流程域(bpm) 设计态只读 op 目录 —— 活体取证固化。

证据边界（docs/audit/udc-semantics/NAV-LIVE-CAPTURE-20261012-ROUND2.md）：
- 两个域是**独立微服务段**（网关 /service/(.*) → ctp-webapi-gateway 按第一段路由），
  不是 udc 自己的表，归属对象边界 = Extension/标品服务，与 UDC Platform 分开建档。
- 端点全部 2026-10-12 round2 活体 CDP 抓包 LIVE PASS（HTTP 200 + BOOT_0000），
  证据级 = OBSERVED_LIVE（非 javap 静态，封顶 OBSERVED_LIVE，不冒称 VERIFIED_STATIC_BYTECODE）。
- 本目录只做「op 事实登记 + 结构校验」，不实现写、不拼前缀臆造；
  分页/读 op 多为 POST（查询语义），在 PlatformOperationLayer 上维持 POLICY_DENIED
  （执行链仅放行 GET），与 udc.metadata.page_tree 同边界，可执行性留活体。

方法：宿主从设计器壳（basic-info 落地页）内真实点击导航触发抓包，
  独立 tab 深链会因 window.xcbpbi 未注入报 cdp.udc.app.no.auth（机制见 round1 §0）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_ID = "udc.seeyon-agent.op-catalog.v1"

# 网关 service 前缀（round2 活体 URL 逐字）：两个域各自独立段，不并入 /service/udc/
BI_SERVICE_PREFIX = "/service/cdp-data/"
FLOW_SERVICE_PREFIX = "/service/bpm/"


@dataclass(frozen=True)
class DomainOp:
    op_id: str
    service: str          # "cdp-data" | "bpm"
    method: str          # "GET" | "POST"
    path: str            # 网关全路径（含 /service/ 段），逐字照录不美化
    purpose: str
    evidence: str = "OBSERVED_LIVE"
    live_data: str = ""   # round2 实测数据摘要（空数据/真实行数等）
    readonly: bool = True


# ---- BI 域（cdp-data）设计态 op（round2 §1 BI 表，全部 LIVE PASS）----
BI_OPS: tuple[DomainOp, ...] = (
    DomainOp("bi.env.variable", "cdp-data", "GET",
             "/service/cdp-data/env/variable",
             "BI 插件环境自报（cdpBiPlugin/cdpDfPlugin 开关、etlEngine）",
             live_data="cdpBiPlugin=true, etlEngine=sql_etl, monolithic=false"),
    DomainOp("bi.dataset.list_page", "cdp-data", "POST",
             "/service/cdp-data/udc/dataset/get-list-page",
             "BI 数据分析-数据集 tab 分页（该 app 0 条）",
             live_data="total=0"),
    DomainOp("bi.stream.list_page", "cdp-data", "POST",
             "/service/cdp-data/udc/stream/get-list-page",
             "BI 数据分析-数据流 tab 分页",
             live_data="total=0"),
    DomainOp("bi.indicator.derive.list", "cdp-data", "POST",
             "/service/cdp-data/udc/indicator/derive/select-page-list",
             "BI 数据分析-指标管理 tab 派生指标分页",
             live_data="total=0"),
    DomainOp("bi.report.list_page", "cdp-data", "POST",
             "/service/cdp-data/udc/report-design/get-report-page",
             "BI 数据分析-报表管理 tab 分页",
             live_data="total=0"),
    # 四 tab 的类别树入口（round1 §1 cdp-data 段 + round2 四 tab 实证）
    DomainOp("bi.dataset.category_tree", "cdp-data", "GET",
             "/service/cdp-data/udc/dataset/get-category-tree",
             "数据集分类树", live_data="BOOT_0000"),
    DomainOp("bi.semantic.category_tree", "cdp-data", "GET",
             "/service/cdp-data/udc/semantic-model/get-category-tree",
             "语义模型分类树", live_data="BOOT_0000"),
)

# 四 tab 结构（DOM 实证）：数据分析 = 数据集 / 数据流 / 指标管理 / 报表管理
BI_DATANAALYSIS_TABS: tuple[str, ...] = ("数据集", "数据流", "指标管理", "报表管理")

# ---- 流程域（bpm）设计态 op（round2 §1 流程表，全部 LIVE PASS）----
FLOW_OPS: tuple[DomainOp, ...] = (
    DomainOp("flow.template.group_by_tag", "bpm", "POST",
             "/service/bpm/graphql?bpmTemplateSelectByAppIdGroupByTagPost",
             "BPM 流程模板按 tag 分组（设计态；该 app 未建模板=空）",
             live_data="total=0"),
)

# 流程域页面结构（DOM 实证）：流程 = 流程模板 / 流程配置 两 tab；
# 模板分 固定流程 / 自由流程 两类（空态文案「前往创建」）。
FLOW_PAGE_TABS: tuple[str, ...] = ("流程模板", "流程配置")
FLOW_TEMPLATE_KINDS: tuple[str, ...] = ("固定流程", "自由流程")


def bi_ops() -> list[DomainOp]:
    return list(BI_OPS)


def flow_ops() -> list[DomainOp]:
    return list(FLOW_OPS)


def load_catalog_file(root) -> dict:
    """从仓库落盘的 JSON 事实件读 op catalog（存在则用，便于跨会话复核）。"""
    path = Path(root) / "bi-flow-op-catalog.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def to_catalog_json() -> dict:
    """导出可落盘事实件（宿主据此写 docs/evidence）。"""
    return {
        "schema": SCHEMA_ID,
        "status": "OBSERVED_LIVE",
        "date": "2026-10-12",
        "evidence": "docs/audit/udc-semantics/NAV-LIVE-CAPTURE-20261012-ROUND2.md",
        "bi": {
            "service": "cdp-data",
            "gateway_prefix": BI_SERVICE_PREFIX,
            "data_analysis_tabs": list(BI_DATANAALYSIS_TABS),
            "ops": [vars(o) for o in BI_OPS],
        },
        "flow": {
            "service": "bpm",
            "gateway_prefix": FLOW_SERVICE_PREFIX,
            "page_tabs": list(FLOW_PAGE_TABS),
            "template_kinds": list(FLOW_TEMPLATE_KINDS),
            "ops": [vars(o) for o in FLOW_OPS],
        },
        "boundary": [
            "BI/流程是独立微服务段，非 udc 表；对象边界独立建档",
            "POST 查询 op 在 PlatformOperationLayer 维持 POLICY_DENIED（仅放行 GET）",
            "全部证据级 OBSERVED_LIVE，未 javap，不冒称 VERIFIED_STATIC_BYTECODE",
        ],
    }


__all__ = [
    "SCHEMA_ID", "BI_SERVICE_PREFIX", "FLOW_SERVICE_PREFIX", "DomainOp",
    "BI_OPS", "FLOW_OPS", "BI_DATANAALYSIS_TABS", "FLOW_PAGE_TABS", "FLOW_TEMPLATE_KINDS",
    "bi_ops", "flow_ops", "to_catalog_json", "load_catalog_file",
]

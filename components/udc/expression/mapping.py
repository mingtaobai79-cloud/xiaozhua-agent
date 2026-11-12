"""表达式落位映射 —— 公用的「写哪两列、用哪个 paramType」。

为什么要这张表
--------------
同一个表达式能力，落到不同模块时写的是**不同的列**、用**不同的 paramType**。
这些差异以前分散在各域实现里（例如字段集自己写了一份 ExpressionSaveDto 构造器），
导致同一条规则两处各写一遍，改一处忘一处。

本表把「差异」集中声明，各域**只引用**，不重写。

证据来源
--------
- `components/udc/attribute_expression_constraints.py`（实体域，LIVE）
  ATTRIBUTE_EXPRESSION_COLUMNS / ATTRIBUTE_EXPRESSION_PAIRS
- `core/facts/udc/setting/attribute-set/default-value-chain.md`（字段集域，LIVE）
  两条值链互斥、runtime 不许置空
- `components/udc/setting/attribute_set_constraints.py`（字段集实现，LIVE PASS）

★ 已实证的域间差异（不是设计选择，是平台现状）
    实体域   有「默认值」和「计算值」两个入口，写不同的列
    字段集域 只有「默认值」一个入口，**没有计算值** ——
             早期把默认值当成计算值写，导致"DB 有值、接口 200、页面全空"
"""
from __future__ import annotations

from dataclasses import dataclass

from .param_types import PARAM_TYPE_REGISTRY

# ---------------------------------------------------------------- 计算态（实体域）
CALCULATE_NORMAL = "NORMAL"
CALCULATE_COMPUTE = "COMPUTE"
CALCULATE_AGGREGATION = "AGGREGATION"


@dataclass(frozen=True)
class ExpressionSlot:
    """一个「表达式落位点」的完整契约。"""

    domain: str                 # entity / setting
    purpose: str                # default_value / calculated_value / scope
    param_type: str             # schema 用的 paramType
    design_column: str | None   # 设计态列（None = 该槽位不存设计态）
    runtime_column: str | None  # 运行态列
    calculate_state: str | None = None
    pairable: bool = True       # design/runtime 是否必须成对写
    note: str = ""


_SLOTS: tuple[ExpressionSlot, ...] = (
    ExpressionSlot(
        domain="entity",
        purpose="default_value",
        param_type="ATTR_DEFAULT_VALUE",
        design_column="default_value_expr_design",
        runtime_column="default_value_expr_runtime",
        note="字段默认值。runtime 不许置空，否则设计器有值页面空白",
    ),
    ExpressionSlot(
        domain="entity",
        purpose="calculated_value",
        param_type="ENTITY",
        design_column="expression_design_data",
        runtime_column="expression_runtime_data",
        calculate_state=CALCULATE_COMPUTE,
        note="字段计算值。写时 calculate 必须是 COMPUTE，否则只是挂了个不生效的表达式",
    ),
    ExpressionSlot(
        domain="entity",
        purpose="scope",
        param_type="ATTRIBUTE_SCOPE",
        design_column=None,
        runtime_column="value_scope_expression",
        pairable=False,
        note="字段取值范围。单列承载，不是 design/runtime 对",
    ),
    ExpressionSlot(
        domain="setting",
        purpose="default_value",
        param_type="CONFIG_PARAM",
        design_column="default_value_expr_design",
        runtime_column="default_value_expr_runtime",
        note="字段集默认值。★ 字段集**没有**计算值入口，别把默认值当计算值写",
    ),
)

# (domain, purpose) → slot
SLOTS: dict[tuple[str, str], ExpressionSlot] = {
    (s.domain, s.purpose): s for s in _SLOTS
}

# 已知「不存在」的落位点 —— 显式登记，防止未来又被臆造出来
ABSENT_SLOTS: dict[tuple[str, str], str] = {
    ("setting", "calculated_value"):
        "字段集面板只有「默认值」一个入口。曾把默认值按计算值那套列写，"
        "结果 DB 有值、接口 BOOT_0000、页面全空（2026-10-22 实证纠正）",
    ("setting", "scope"):
        "字段集没有取值范围入口",
}


def slots_for_domain(domain: str) -> tuple[ExpressionSlot, ...]:
    return tuple(s for s in _SLOTS if s.domain == domain)


def get_slot(domain: str, purpose: str) -> ExpressionSlot:
    key = (domain, purpose)
    if key in ABSENT_SLOTS:
        raise KeyError("%s/%s 不存在：%s" % (domain, purpose, ABSENT_SLOTS[key]))
    try:
        return SLOTS[key]
    except KeyError:
        raise KeyError(
            "未知落位点 %s/%s；已有: %s"
            % (domain, purpose, ", ".join("%s/%s" % k for k in SLOTS))
        ) from None


def columns_for(domain: str, purpose: str) -> tuple[str, ...]:
    """该槽位要写的列（按写序）。"""
    s = get_slot(domain, purpose)
    out = []
    if s.design_column:
        out.append(s.design_column)
    if s.runtime_column:
        out.append(s.runtime_column)
    return tuple(out)


def validate_slot_consistency() -> list[str]:
    """自检：每个槽位的 paramType 必须在 @ParamLoadService 注册表里。

    返回错误列表，空 = 一致。
    """
    errs = []
    for s in _SLOTS:
        if s.param_type not in PARAM_TYPE_REGISTRY:
            errs.append("%s/%s 的 paramType=%s 未注册"
                        % (s.domain, s.purpose, s.param_type))
        if s.pairable and not (s.design_column and s.runtime_column):
            errs.append("%s/%s 声明成对写但列不全" % (s.domain, s.purpose))
        if not s.pairable and s.design_column and s.runtime_column:
            errs.append("%s/%s 声明单列却给了两列" % (s.domain, s.purpose))
    return errs

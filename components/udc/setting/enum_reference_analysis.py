"""枚举引用分析器 —— 删除枚举前的安全闸门。

背景
----
2026-10-20 清理枚举时，第一版引用分析只看 `udc_page_info.page_schema`，
得到"页面 0 命中"的结论，于是把 363 个枚举全删了。**那是误判**：
页面的 schema 根本不在 `udc_page_info`，而在 `udc_page_schema` 表。
真相是页面**确实**引用枚举（下拉/单选控件绑定 ctpEnumInfo）。

本模块把正确做法固化为可执行断言，避免后人重犯。

引用载体（2026-10-20 实读原文确认）
------------------------------------
页面 / 资源 / 导出模板的参数 JSON 里有 ctpEnumInfo 结构：

    {"ctpEnumInfo": {"id": "<枚举id>", "code": "<枚举code>", "appId": "<应用id>",
                     "caption": "业务类型",
                     "CTPENUM": {"appName": "...", "fullName": "...",
                                 "currentAppId": "...", "id": "<枚举id>"},
                     "relationCtpEnum": {"enumType": "SAME_LEVEL", "enumLevel": 0}}}

三个必守的判据
--------------
1. **载体要对**：页面查 `udc_page_schema`，不是 `udc_page_info`。
2. **阳性对照**：分析器必须能检出「实体属性在用」的枚举 code，检出率 100%。
   检不出说明方法有缺口，此时的"无引用"结论不可信。
3. **阴性对照**：不存在的枚举不得被检出（防子串误判，如 code="bool" 命中 "boolean"）。
4. **引用方有效性**：引用方自身已删（`is_deleted=1`）时不算活引用——
   否则会得出"这枚举不能删"的假结论（第一版就踩了这个，还漏 SELECT is_deleted 字段）。

死引用 vs 活引用
--------------
  活引用  引用方有效 → 枚举**绝对不能删**（删了产生悬空引用，
         表现为后端代码生成编译失败）
  死引用  引用方已删 → 枚举可删；记录下来用于审计
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# ctpEnumInfo 块：id 必抽；code 若有则一并抽。
# 注意：code 在 id 之后出现，块内可能没有 code（只给 id），
#   所以分成两个正则——id 单独抽（必须有），code 作为可选补充。
_CTP_ENUM_ID = re.compile(r'"ctpEnumInfo"\s*:\s*\{[^{}]*?"id"\s*:\s*"(-?\d+)"', re.S)
_CTP_ENUM_CODE = re.compile(r'"ctpEnumInfo"\s*:\s*\{[^{}]*?"code"\s*:\s*"([^"]*)"', re.S)
# 兜底：enumId / enumCode 字段
_FIELD_PAIR = re.compile(r'"enum(?:Id|Code)"\s*:\s*"?(-?\d+|[A-Za-z0-9_]+)"?', re.I)

# 已知引用字段名（用于 enumRefValues）
_REF_FIELDS = ("enumId", "enumCode", "enumValue", "ctpEnumId", "ctpEnumCode", "unitId")


def enum_ref_values(blob: str) -> set[str]:
    """从一段 JSON 文本里抽出它引用的枚举标识（id 与 code 都算）。

    只认两种结构：
      1. ctpEnumInfo 块（权威载体）
      2. enumId/enumCode 字段（微流程里常见）
    不做泛化子串匹配——短 code（如 bool）会误命中别的词。
    """
    out: set[str] = set()
    for m in _CTP_ENUM_ID.finditer(blob):
        out.add(m.group(1))
    for m in _CTP_ENUM_CODE.finditer(blob):
        if m.group(1):
            out.add(m.group(1))
    for m in _FIELD_PAIR.finditer(blob):
        out.add(m.group(1))
    return out


@dataclass
class EnumRef:
    """一条引用。"""

    source: str            # 载体表名
    source_id: str         # 引用方 id
    source_alive: bool     # 引用方是否仍有效
    via: str               # 命中方式：ctpEnumInfo / field
    value: str             # 命中的枚举 id 或 code


@dataclass
class EnumRefReport:
    """引用分析结果。"""

    app_id: str
    total_enums: int = 0
    all_enum_ids: set[str] = field(default_factory=set)
    live_referenced: dict[str, list[str]] = field(default_factory=dict)   # enum_id -> 引用描述
    dead_referenced: dict[str, list[str]] = field(default_factory=dict)
    control_detected: list[str] = field(default_factory=list)
    control_total: int = 0
    negative_detected: list[str] = field(default_factory=list)
    method_valid: bool = False

    @property
    def keep_ids(self) -> set[str]:
        """必须保留的枚举 id（有活引用）。"""
        return set(self.live_referenced)

    @property
    def deletable_ids(self) -> set[str]:
        """可删的枚举 id（既无活引用，也无死引用记录）。

        注意：只给出「确定无引用」的集合。引用方已删的死引用（dead_referenced）
        也归入可删，但会单独记录以便审计。
        """
        referenced = set(self.live_referenced) | set(self.dead_referenced)
        return set(self.all_enum_ids) - referenced

    def summary(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "total_enums": self.total_enums,
            "live_referenced": len(self.live_referenced),
            "dead_referenced": len(self.dead_referenced),
            "method_valid": self.method_valid,
            "control_detected": self.control_detected,
            "negative_detected": self.negative_detected,
        }


def classify(enums: Iterable[dict[str, Any]],
            sources: Iterable[tuple[str, str, bool, str]],
            *,
            app_id: str,
            control_codes: Iterable[str] = (),
            negative_codes: Iterable[str] = (),
            control_total: int | None = None) -> EnumRefReport:
    """把枚举与引用源归类。

    ``enums``   每项须含 id / code / is_delete
    ``sources`` 每项为 (table, source_id, source_alive, blob)
    """
    enums = list(enums)
    report = EnumRefReport(app_id=app_id, total_enums=len(enums))
    report.all_enum_ids = {str(e.get("id")) for e in enums}

    # 预抽各源的引用值
    per_source: list[tuple[str, str, bool, set[str]]] = []
    all_vals: set[str] = set()
    for table, sid, alive, blob in sources:
        vals = enum_ref_values(blob or "")
        per_source.append((table, sid, alive, vals))
        all_vals |= vals

    # 对照
    ctrl = set(control_codes)
    neg = set(negative_codes)
    report.control_total = control_total if control_total is not None else len(ctrl)
    report.control_detected = sorted(ctrl & all_vals)
    report.negative_detected = sorted(neg & all_vals)
    report.method_valid = (
        len(report.control_detected) == report.control_total
        and not report.negative_detected
    )

    # 归类
    for e in enums:
        eid = str(e.get("id"))
        code = str(e.get("code") or "")
        live: list[str] = []
        dead: list[str] = []
        for table, sid, alive, vals in per_source:
            hit = (code and code in vals) or (eid and eid in vals)
            if not hit:
                continue
            desc = f"{table}({sid})"
            (live if alive else dead).append(desc)
        if live:
            report.live_referenced[eid] = live
        elif dead:
            report.dead_referenced[eid] = dead
    return report


__all__ = ["enum_ref_values", "classify", "EnumRef", "EnumRefReport"]

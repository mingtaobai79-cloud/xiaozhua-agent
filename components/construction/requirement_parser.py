"""需求解析器 —— 自然语言需求 → NormalizedEntityModel（确定性规则，不臆造）。

北极星落点：宿主 LLM 从需求里圈出实体/字段后（或用户直接给结构化清单），
本模块把「半结构化需求文本」解析为实体模型候选，歧义处标 UNVERIFIED，
再交给 ConstructionEngine/渲染器出骨架。

设计边界（证据纪律）：
- 只做确定性规则：实体名（「实体X」/「X实体」/「新建X」）、字段行（名称+类型）、
  标题（「标题/名为X」）；类型词表 = golden javap 观测映射，未识别类型保留原文并记 unknown。
- 不调 LLM、不联网；解析不出实体名 → status=UNVERIFIED + reason，不伪造模型。
- 宿主 LLM 侧的语义理解发生在宿主（Hermes/CC/Codex），本模块只做结构化与校验。
"""
from __future__ import annotations

import re
from typing import Any

from .models import UNKNOWN, NormalizedEntityModel
from .skeleton import JAVA_TYPES

# 中文需求里常见的类型字面 → golden 观测类型（未命中保留原文，由调用方决定 UNVERIFIED）
_TYPE_ALIASES = {
    "字符串": "String", "文本": "String", "文本型": "String",
    "整数": "Long", "长整数": "Long", "数字": "Long", "数值": "Long",
    "小数": "java.math.BigDecimal", "金额": "java.math.BigDecimal",
    "布尔": "java.lang.Boolean", "是/否": "java.lang.Boolean", "是否": "java.lang.Boolean",
    "日期": "java.util.Date", "时间": "java.util.Date", "日期时间": "java.util.Date",
}

_ENTITY_PATTERNS = (
    # ★ 三处都必须带 `\s*`：中文需求里「新建实体 PurchaseApply」几乎总带空格，
    #   原版 `实体[「"']?([\w\u4e00-\u9fff]+)` 中间不允许空白 → 最常见的写法一句都匹配不到。
    # ★ 第三处（`X实体`）必须把捕获面收紧到 Java 标识符：
    #   原版 `([\w\u4e00-\u9fff]+)实体` 是贪婪中文，会把动词一起吃掉 ——
    #   「新建实体 PurchaseApply」被解析出 entity_name="新建"（实测）。
    re.compile(r"(?:新建|创建|建)(?:一个)?实体\s*[「\"']?([\w\u4e00-\u9fff]+)[」\"']?"),
    re.compile(r"实体[名称为]+[是为]?\s*[「\"']?([\w\u4e00-\u9fff]+)[」\"']?"),
    re.compile(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*实体"),
)
_CAPTION_PATTERNS = (
    re.compile(r"[标题名称为]+\s*[「\"'是:]?\s*([\w\u4e00-\u9fff]+)"),
)
# 字段行："- 字段名：类型" / "字段名 类型" / "字段名(类型)"
_FIELD_LINE = re.compile(
    r"^\s*[-*•]?\s*([\w\u4e00-\u9fff][\w\u4e00-\u9fff0-9]*)\s*[（(]?\s*[：:=]?\s*([\w\u4e00-\u9fff.<>\[\]]+)\s*[）)]?\s*$"
)
# 中文实体名 → Java 类名（拼音/原文保留；中文不上类名，转 UNVERIFIED）
_JAVA_IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


class RequirementParser:
    SCHEMA = "udc.construction.requirement-parse.v1"

    def parse(self, text: str, application_id: str) -> dict[str, Any]:
        unknowns: list[str] = []
        type_verified: list[tuple[str, bool]] = []
        entity_name = None
        for pat in _ENTITY_PATTERNS:
            m = pat.search(text)
            if m:
                entity_name = m.group(1)
                break
        if not entity_name:
            return {"status": "UNVERIFIED", "reason": "no entity name found",
                    "schema": self.SCHEMA, "application_id": application_id}
        if not _JAVA_IDENT.match(entity_name):
            unknowns.append(f"entity-name-not-java-identifier:{entity_name}")

        caption = None
        for pat in _CAPTION_PATTERNS:
            m = pat.search(text)
            if m:
                caption = m.group(1)
                break

        attributes: list[dict[str, Any]] = []
        # ★ 字段行解析前先**剥掉实体声明子句**：单行需求「新建实体 PurchaseApply」整句
        #   会被 `_FIELD_LINE` 当成「字段名 类型」吞下，产出
        #   `attribute-name-not-java-identifier:新建一个实体` 这种垃圾（实测）。
        #   多行清单场景不受影响 —— 只删声明那一段。
        field_text = text
        for pat in _ENTITY_PATTERNS:
            field_text = pat.sub(" ", field_text)
        for line in field_text.splitlines():
            m = _FIELD_LINE.match(line)
            if not m:
                continue
            name, raw_type = m.group(1), m.group(2)
            if name in ("实体", "标题", "名称", "字段") and not attributes:
                continue
            # 字段名不允许含空白/动词性中文（剥掉声明后仍剩下的整句不是字段）
            if len(name) > 24:
                continue
            t = _TYPE_ALIASES.get(raw_type, JAVA_TYPES.get(raw_type, raw_type))
            if not _JAVA_IDENT.match(name):
                # 中文属性名：golden 观测的生成物字段名是拼音/英文（fahuodanweiyouxiang 等），
                # 拼音转换规则无证据 → 不臆造，标注 UNVERIFIED 交宿主确认
                unknowns.append(f"attribute-name-not-java-identifier:{name}")
            if JAVA_TYPES.get(t) or t in JAVA_TYPES.values():
                type_verified.append((name, True))
            else:
                type_verified.append((name, False))
                unknowns.append(f"attribute-type-unverified:{name}:{raw_type}")
            attributes.append({"name": name, "type": t})

        model = NormalizedEntityModel(
            application_id, None, entity_name, attributes, caption=caption or UNKNOWN,
        )
        return {
            "status": "PASS" if attributes and not unknowns else
                      ("UNVERIFIED" if not attributes else "PASS_WITH_UNKNOWNS"),
            "schema": self.SCHEMA,
            "application_id": application_id,
            "model": model,
            "unknowns": unknowns,
            "type_verified": dict(type_verified),
        }


__all__ = ["RequirementParser"]

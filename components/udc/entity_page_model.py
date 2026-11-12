"""实体页面 6 tab op 目录 + 写链陷阱 + 能力驱动表 —— 功能字典固化。

证据基线（docs/audit/udc-semantics/ENTITY-PAGE-INVENTORY.md §2.7/§2.8/§3/§4，
9 项缺口全部落地；全部 LIVE 或 bundle/javap 原文，不臆造）：

- 6 tab 定义对象 R 有 8 个 key（relation/data 为预留不渲染）；tab 可见性由
  CAF 谓词过滤（第三方实体/扩展实体隐藏 规则·事件·索引；参照 tab 仅
  ONE2MANY 显示）——这是 tab 显示条件的权威口径。
- op→tab 权威绑定（§2.7.1）：基本 udcEntityPost(appId 由 redux 注入)/
  字段 udcEntityAttribute{Post,UpdatePost}/ 规则 udcMicroflowSearchEntityRulePost
  (body.params.sourceId + groupType 三组键)/ 参照 udcReferConfigCreateOrUpdatePost/
  事件 udcEventCreateWithDataPost / 索引 udcIndexPost。
- 表达式四接口 LIVE PASS（§2.7.5）：/expression/preset/list {}、
  /expression/schema(注意 ids 数组+paramType+upsource+serverName 否则 BOOT_3002)、
  /expression/transform、/expression/check；后端属 **boot-starter-formula**，非 udc。
- paramsType 特例 14 个不能按 InputBody 猜（§2.7.4）：
  Long 裸值(udcIndexEntityListPost) / String / Map / [XxxInputBody] 数组包装 10 个 / [String]。
- 删除陷阱（§2.7.7 LIVE）：udcEntityAttributeBatchDeletePost 返回 BOOT_0000 但
  content=0（数组两种传法都不删）；单删 udcEntityAttributeDeletePost {id} 才删。
  纪律：删除必须断言 content>=1 并回读，不能只看业务码。
- 数据类型能力表（§2.8.2⑥）：每种 dataType 的 enable*（DefaultValue/Index/Unique/
  Required/MultiSelect/Encryption/Sensitive/LengthRange/…）由 udcDataTypeDataTypesByAppIdAppGet
  驱动，不是前端写死——**构造字段前须先取能力表**。
- 索引禁用矩阵（§2.8.3①）：caption/remark/submit 仅 isNew&&!isLastVersionApp；
  fieldIds/type 另受非自建限制；已发布不可改；非新建且非自建不可删；
  索引名前缀 idx_(普通)/uk_(唯一)；fieldIds=逗号分隔字符串。
- 实体规则三组（VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE）= MicroFlow groupType，
  不是字段 defaultValue（与 attribute_semantics 同源边界）。
- 权限两层（§3）：后端类级 @HasRole（实体域=udcAppDesigner+udcSystemAdmin，
  方法级=类级已核）；CAF=布局位置树非权限；真权限在 udc_role_resource+@HasRole。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.entity-page.v1"

# tab 定义对象 8 key（§2.8，relation/data 不渲染=预留）
ENTITY_TAB_KEYS: tuple[str, ...] = ("basicInfo", "attributeSet", "rule", "refer",
                                     "event", "relation", "index", "data")
RENDERED_TAB_KEYS: tuple[str, ...] = ("basicInfo", "attributeSet", "rule", "refer",
                                      "event", "index")
RESERVED_NOT_RENDERED: tuple[str, ...] = ("relation", "data")

# tab 显示条件（§2.8.1 switch 原文）
TAB_VISIBILITY_RULES: dict[str, str] = {
    "basicInfo": "en.includes('basicInfo')（CAF 过滤）",
    "attributeSet": "无额外条件（默认 tab；pathname 尾段=entity）",
    "rule": "!isThirdEntity && category!=='EXT'（第三方/扩展实体隐藏）",
    "refer": "entityDetails.multiplicity === 'ONE2MANY'（非主子表无参照 tab）",
    "event": "!isThirdEntity && category!=='EXT'",
    "index": "!isThirdEntity && category!=='EXT'",
}

# op → tab 权威绑定（写面）
TAB_WRITE_OPS: dict[str, tuple[str, ...]] = {
    "basicInfo": ("udcEntityPost", "udcEntityUpdatePost", "udcEntityEntityCopyPost",
                  "udcStereotypeListGet", "udcEntityOpenApiSelectGet"),
    "attributeSet": ("udcEntityAttributePost", "udcEntityAttributeUpdatePost",
                     "udcEntityAttributeBatchPost", "udcEntityAttributeTransferPost"),
    "rule": ("udcMicroflowCreatePost", "udcMicroflowUpdatePost",
             "udcMicroflowSearchEntityRulePost", "udcMicroflowDeletePost"),
    "refer": ("udcReferConfigCreateOrUpdatePost", "udcReferConfigDeleteByGroupIdPost"),
    "event": ("udcEventCreateWithDataPost", "udcEventPost", "udcEventUpdatePost"),
    "index": ("udcIndexPost", "udcIndexUpdatePost", "udcIndexDeletePost"),
}

# paramsType 特例（§2.7.4；这些 op 不能按 InputBody 猜）
PARAMSTYPE_EXCEPTIONS: dict[str, str] = {
    "udcIndexEntityListPost": "Long（裸实体 id，对象形态返回空）",
    "udcSandboxClearDataPost": "String",
    "udcEntityAttributeSelectParentEnumAttrsPost": "Map",
    "udcEntityAttributeGroupBathUpdatePost": "[InputBody] 数组包装",
    "udcEntityAttributeBatchUpdatePost": "[InputBody] 数组包装",
    "udcEntityAttributeGroupCreateUpdatePost": "[InputBody] 数组包装",
    "udcEntityGroupUpdateBatchPost": "[InputBody] 数组包装",
    "udcEntityBatchUpdateEntityGroupIdAndOrdernoPost": "[InputBody] 数组包装",
    "udcUdcEnumItemOperateBatchPost": "[InputBody] 数组包装",
    "udcDataTransferObjectCreateDtoWithAttrsPost": "[InputBody] 数组包装",
    "udcDataTransferObjectUpdateDtoWithAttrsPost": "[InputBody] 数组包装",
    "udcConditionCheckPost": "[InputBody] 数组包装",
    "udcApplicationDependentApplicationCreateBatchPost": "[InputBody] 数组包装",
    "udcMicroflowFilterNotVirtualPost": "[String]",
}

# 表达式四接口（§2.7.5，全 LIVE PASS；后端 boot-starter-formula，无 @HasRole）
EXPRESSION_ENDPOINTS: dict[str, dict[str, Any]] = {
    "/expression/preset/list": {"method": "POST", "body": {}, "gives": "系统变量/函数预置"},
    "/expression/schema": {
        "method": "POST", "body_required": ("appId", "ids:数组", "paramType", "upsource", "serverName"),
        "note": "idsStr/extension:null 报 BOOT_3002（LIVE 实测）"},
    "/expression/transform": {"method": "POST", "body": "ExpressionSaveDto",
                              "gives": "designData.expressionTranslation"},
    "/expression/check": {"method": "POST", "body": "ExpressionSaveDto", "gives": "Boolean"},
}

# 删除陷阱（§2.7.7，业务码成功但数据不动的隐蔽层）
DELETE_TRAP: dict[str, str] = {
    "op": "udcEntityAttributeBatchDeletePost",
    "observed": "BOOT_0000 + content=0（裸 id 数组/对象数组两种传法都不删）",
    "working_path": "udcEntityAttributeDeletePost body:{id} → content=1 + 回读已不存在",
    "discipline": "删除必须断言 content>=1 并回读确认；HTTP200/业务码成功≠数据已动",
}

# 数据类型能力键（§2.8.2⑥；构造字段前从能力表判断该类型支持什么）
DATATYPE_CAPABILITY_KEYS: tuple[str, ...] = (
    "enableCalculable", "enableAggregation", "enableDecimalDigits", "enableDefaultValue",
    "enableEncryption", "enableIndex", "enableLengthRange", "enableLog",
    "enableMaxAndMin", "enableMultiSelect", "enablePattern", "enableRequired",
    "enableSensitive", "enableUnique", "enableSearch", "enableSensitiveWordCheck",
)

# 索引矩阵（§2.8.3①）
INDEX_NAME_PREFIX: dict[str, str] = {"NORMAL": "idx_", "UNIQUE": "uk_"}
INDEX_FIELD_MAX = 5
INDEX_FIELD_IDS_FORMAT = "comma-joined-string"   # 给数组 BOOT_3002
INDEX_DISABLE_MATRIX: dict[str, str] = {
    "caption": "可编辑 ⟺ isNew && !isLastVersionApp",
    "remark": "同 caption",
    "submit": "同 caption",
    "fieldIds": "同 caption 或 indexSource!=='MANUAL_CREATE' 时不可改",
    "type": "同 fieldIds（非自建不可改）",
    "delete": "非新建 且 非自建 → 禁删；已发布不可改",
}

# 权限权威口径（§3）
PERMISSION_MODEL: tuple[str, ...] = (
    "后端类级 @HasRole：实体域=udcAppDesigner+udcSystemAdmin；方法级=类级（8 controller 已核无差异）",
    "ReferConfigController 额外含 OrgAdmin",
    "CAF identity=布局位置树+可配置UI体系（非权限）；判定数据在平台 CAF 服务端",
    "真权限存储=udc_role_resource + udc_role（应用级业务角色）+ udc_resource（运行态资源）",
)

# 版本硬约束（§2.8.1 文案）
VERSION_CONSTRAINT = "已上架版本无法 添加/复制/转移 实体/字段/字段集/索引，请另存版本后操作"


@dataclass
class EntityTabBinding:
    """单 tab 的功能绑定校验（离线：op 齐全 + 陷阱登记）。"""
    tab: str
    planned_ops: list[str] = field(default_factory=list)
    params_exceptions_used: list[str] = field(default_factory=list)

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        known = set(TAB_WRITE_OPS.get(self.tab, ()))
        if self.tab in RESERVED_NOT_RENDERED:
            errors.append(f"tab {self.tab!r} 为预留 key（当前版本不渲染，§2.8.1 已定性）")
        for op in self.planned_ops:
            base = op.split("(")[0]
            if base not in known and base not in PARAMSTYPE_EXCEPTIONS:
                warnings.append(f"op {base!r} 不在 tab={self.tab} 已证写 op 清单（UNVERIFIED）")
            if base in PARAMSTYPE_EXCEPTIONS:
                # 必须显式声明 paramsType 特例形态
                declared = next((p for p in self.params_exceptions_used if p == base), None)
                if not declared:
                    errors.append(f"op {base} 属 paramsType 特例：{PARAMSTYPE_EXCEPTIONS[base]}（必须按特例构造，不得 InputBody 臆猜）")
        return {"schema": SCHEMA_ID, "kind": "entity_tab_binding", "tab": self.tab,
                "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
                "errors": errors, "warnings": warnings,
                "write_ops_proven": sorted(known), "can_execute": False}


def check_delete_plan(op: str, expect_deleted_count: int) -> dict[str, str]:
    """删除计划守卫（把 §2.7.7 陷阱变成函数级纪律）。"""
    if op == "udcEntityAttributeBatchDeletePost":
        return {"decision": "RECOMMEND_SINGLE_DELETE",
                "reason": DELETE_TRAP["observed"] + " → 改用 " + DELETE_TRAP["working_path"],
                "verify": "content>=1 且回读不存在才算删除；" + DELETE_TRAP["discipline"]}
    if op == "udcEntityAttributeDeletePost":
        return {"decision": "ALLOWED", "verify": f"断言 content>={max(1, expect_deleted_count)} + 回读确认"}
    return {"decision": "UNKNOWN_OP", "verify": "未在已证删除 op 清单，先取证"}


def catalog() -> dict[str, Any]:
    return {"schema": SCHEMA_ID, "date": "2026-10-12",
            "evidence": "docs/audit/udc-semantics/ENTITY-PAGE-INVENTORY.md",
            "tabs_all": list(ENTITY_TAB_KEYS),
            "tabs_rendered": list(RENDERED_TAB_KEYS),
            "reserved_not_rendered": list(RESERVED_NOT_RENDERED),
            "tab_visibility": TAB_VISIBILITY_RULES,
            "write_ops": {k: list(v) for k, v in TAB_WRITE_OPS.items()},
            "params_type_exceptions": PARAMSTYPE_EXCEPTIONS,
            "expression_endpoints": {k: v for k, v in EXPRESSION_ENDPOINTS.items()},
            "delete_trap": DELETE_TRAP,
            "datatype_capability_keys": list(DATATYPE_CAPABILITY_KEYS),
            "index_matrix": INDEX_DISABLE_MATRIX,
            "permission_model": list(PERMISSION_MODEL),
            "version_constraint": VERSION_CONSTRAINT}


__all__ = [
    "SCHEMA_ID", "ENTITY_TAB_KEYS", "RENDERED_TAB_KEYS", "RESERVED_NOT_RENDERED",
    "TAB_VISIBILITY_RULES", "TAB_WRITE_OPS", "PARAMSTYPE_EXCEPTIONS", "EXPRESSION_ENDPOINTS",
    "DELETE_TRAP", "DATATYPE_CAPABILITY_KEYS", "INDEX_DISABLE_MATRIX", "INDEX_NAME_PREFIX",
    "INDEX_FIELD_MAX", "INDEX_FIELD_IDS_FORMAT", "PERMISSION_MODEL", "VERSION_CONSTRAINT",
    "EntityTabBinding", "check_delete_plan", "catalog",
]

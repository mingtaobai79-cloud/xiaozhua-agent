"""UDC 低代码运行时框架（udc-starter-lowcode 5.3.517）约束模型。

证据（CFR 反编译 udc-starter-lowcode-5.3.517.jar）：
- core/EntityMeta / AttributeMeta / BaseEntityCurdService（实体元数据与 CRUD 基类）
- callback/*（13 个生命周期回调接口）
- service/BaseEntityCurdService / BaseMicroFlowService / BaseDataFlowService / BaseDeductionService
- enums/FlowActionType / RecursiveType / AttrSnapshotRefType
- cache/*（EntityCacheManager / RedisCacheResolver 等）

用途：低代码应用运行时框架约束 —— 实体元数据结构、CRUD 契约、
生命周期回调（ preCreate/preUpdate/validate/permission/secret/approval/billState ）。
"""
from __future__ import annotations

# ---- FlowActionType（流转动作类型，6 种+code）----
FLOW_ACTION_TYPES: dict[str, int] = {
    "NONE": 0, "SAVE": 1, "SEND": 2, "REPEAL": 3, "TASK_TO_SENDER": 4, "RE_SEND": 5,
}
# ---- RecursiveType（递归类型）----
RECURSIVE_TYPES: dict[str, int] = {"TEMPLATE": 0, "FORWARD": 1}
# ---- AttrSnapshotRefType（属性快照引用类型）----
ATTR_SNAPSHOT_REF_TYPES: dict[str, int] = {"ENTITY": 0, "CTP_ENUM": 1}

# ---- EntityMeta 字段（运行态实体元数据结构）----
ENTITY_META_FIELDS: dict[str, str] = {
    "entityType": "实体类型（EntityType）",
    "entityCategory": "实体类别（EntityCategoryEnum）",
    "relationType": "关系类型（RelationType）",
    "entityId": "实体Id",
    "entityTable": "实体表名",
    "name": "实体编码",
    "caption": "实体名称",
    "stereotype": "业务版型",
    "entityClass": "实体类",
    "dtoClass": "DTO 类",
    "dtoListName": "列表 DTO 名（子实体集合）",
    "parentFullName": "父实体 fullName",
    "fullName": "实体 fullName（业务表命名基础）",
    "sortField": "是否有排序字段",
    "children": "子实体元数据列表（树形）",
}

# ---- AttributeMeta 字段（运行态属性元数据结构）----
ATTRIBUTE_META_FIELDS: dict[str, str] = {
    "fullName": "属性 fullName",
    "name": "属性编码",
    "caption": "属性名称",
    "description": "描述",
    "multiSelect": "是否多选",
    "dataI18n": "是否数据国际化",
    "dataType": "数据类型（前端展示用）",
    "realDataType": "真实数据类型（运行时）",
    "relationAppName": "关联应用名",
    "relationEntity": "关联实体",
    "useSnapshot": "是否使用快照",
    "attrGuid": "属性 GUID",
    "maskType": "脱敏类型（Maskable）",
}

# ---- BaseEntityCurdService 方法契约（CRUD 基类）----
CURD_SERVICE_METHODS: tuple[tuple[str, str], ...] = (
    ("create", "创建（单个）"),
    ("createBatch", "批量创建"),
    ("createWithResult", "创建并返回结果"),
    ("copyAndInsert", "复制并插入"),
    ("runtimeCopy", "运行态复制"),
    ("update", "更新"),
    ("updateNoEvents", "更新（不触发事件）"),
    ("updateWithFields", "按字段更新"),
    ("updateRootEntity", "更新根实体（级联子实体）"),
    ("updateStatusType", "更新状态类型"),
    ("updateBatch", "批量更新"),
    ("updateBatchWithResult", "批量更新并返回结果"),
    ("selectCascadeById", "级联查（含子实体）"),
    ("selectCascadeByIds", "批量级联查"),
    ("selectCascadeListByWrapper", "按 Wrapper 级联查"),
    ("selectCascadeListByConditions", "按条件级联查"),
    ("deleteById", "按Id删除"),
    ("deleteByIds", "批量删除"),
    ("deleteByComplexConditions", "按复杂条件删除"),
    ("operateRootBatch", "批量操作根实体"),
    ("validate", "校验"),
    ("listToMap", "列表转Map"),
)

# ---- 生命周期回调接口（13 个）----
CALLBACK_TYPES: dict[str, str] = {
    "PreCreateCallBack": "创建前回调（preCreate/preCreateBatch）",
    "PreUpdateCallBack": "更新前回调（preUpdate/preUpdateBatch）",
    "PreCopyCallBack": "复制前回调",
    "ValidateCallBack": "JSR303 校验回调（assertjsr303）",
    "PermissionCallBack": "权限回调（buildInitialValue + requiredValidate）",
    "SecretCallBack": "密文检查回调（checkSecret）",
    "ApprovalCallBack": "审批回调（before/afterApprovalCreate/Update）",
    "BillStateCallBack": "单据状态回调（checkBillState）",
    "EntityAttrSnapshotCallBack": "实体属性快照回调",
    "EntityDataDiffCallBack": "实体数据差异回调",
    "EntityRuntimeLogCallBack": "实体运行日志回调",
    "MethodCallBack": "方法回调",
    "ApprovalCallBackExt": "审批回调扩展",
}

# ---- DataTransferAppService（数据传输契约）----
DATA_TRANSFER_OPERATION: str = "dataTransfer(SingleRequest<DataTransferRequest>) -> SingleResponse<DataTransferResponse>"

# ---- 服务基类（4 个，业务领域基类）----
LOWCODE_BASE_SERVICES: tuple[str, ...] = (
    "BaseEntityCurdService",   # 实体增删改查（方法契约见上）
    "BaseMicroFlowService",    # 微流程基类
    "BaseDataFlowService",     # 数据流基类
    "BaseDeductionService",    # 推导基类
)

# ---- 缓存机制（cache 包关键类）----
LOWCODE_CACHE_CLASSES: tuple[str, ...] = (
    "EntityCacheManager",       # 实体缓存管理
    "EntityKeyGenerator",       # 实体键生成
    "SingleEntityKeyGenerator", # 单实体键生成
    "RedisCacheManagerResolver",# Redis 缓存管理解析
    "RedisCacheResolver",       # Redis 缓存解析
    "CacheTransactionContext",  # 缓存事务上下文
    "CacheAspect",              # 缓存切面
)
# 注解驱动：@RCacheable / @ECacheable（实体缓存）/ @ECachePut / @ECacheEvict / @ENoCache / @PriorityCache
CACHE_ANNOTATIONS: tuple[str, ...] = (
    "RCacheable", "ECacheable", "ECachePut", "ECacheEvict", "ENoCache", "PriorityCache",
)


def validate_entity_meta(meta: dict) -> list[str]:
    """校验运行态实体元数据关键字段（空=通过）。"""
    errs: list[str] = []
    for f in ("name", "fullName", "entityTable", "stereotype", "entityCategory"):
        v = meta.get(f)
        if v is None or v == "":
            errs.append(f"EntityMeta 缺关键字段 {f}（{ENTITY_META_FIELDS.get(f, '')}）")
    return errs


def validate_flow_action_type(action: str) -> bool:
    """流转动作类型是否合法。"""
    return action in FLOW_ACTION_TYPES

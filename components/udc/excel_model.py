"""Excel 模板/导入导出模型 —— 模板存储、列映射双结构、异步句柄语义。

证据基线（docs/audit/udc-semantics/flow-excel-source-audit.md §1/§4，逐行可复核）：
- 模板持久化（§4，ExcelExportTemplate.java:22-88）：表 ctp_excel_export_template，
  键 app_id(String!)/app_guid/app_name/main_full_name/signature_code/
  metadata_content/excel_head_info/custom_flag/import_flag/default_flag/
  belong_group_id/auth_info。
  **appId 在此表/DTO 是 String，不得套其他 UDC 面的 Long appId 协议**（§4 原文警示）。
- 模板不是 udc_page_schema 子字段，也不只存在于实体 preset JSON（§1 纠正结论 2）。
- 默认模板链（§4）：EntityController.preset/create-default-excel-template →
  EntityPresetAppServiceImpl → EntityPresetService.createDefaultExcelTemplate →
  ExcelExportAppService.createExcelDataGridTemplate → ExcelExportTemplateService.create；
  按 appId+mainFullName+isImport/isCustom/isDefault 查找复用；
  Many2One 参照字段用唯一标识字段；CTPENUM 单独处理；
  **层级 metadataContent 与拉平 excelHeadInfo 是两份结构**——只给中文表头 ≠ 列映射完整。
- check 端点有副作用（§1/§4）：excel/check-excel（及旧版 check-excel-data）会解析上传
  模板、必要时跨环境创建模板（templateService.create）、发 ASYNC 校验事件、写 Redis DOING。
  **不得因叫 check 就进只读白名单**。
- 异步句柄语义（§4）：导入/导出返回 redisKey 只是任务句柄；验收必须到
  文件/行结果/错误文件层。导出链 ExcelExportAppService→ExcelExportEvent→
  ExcelEventListener.onExcelImport→…→saveTreeList→invokeSaveBatch。
- 已知异常缺口候选（§4）：saveTreeList 更新异常 catch 只记日志、不置 successFlag=false
  （STATIC_SOURCE 缺口候选，未对部署版本验证）→ 异步 SUCCESS 不能替代业务数据回读。

本模型只做结构 + 语义纪律校验；can_execute=False；副作用显式分类。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.excel-model.v1"

EXCEL_TEMPLATE_TABLE = "ctp_excel_export_template"

# 模板表/DTO 键（§4 逐字；app_id 类型警示在 app_id_is_string 断言）
EXCEL_TEMPLATE_KEYS: tuple[str, ...] = (
    "app_id", "app_guid", "app_name", "main_full_name", "signature_code",
    "metadata_content", "excel_head_info", "custom_flag", "import_flag",
    "default_flag", "belong_group_id", "auth_info",
)
APP_ID_IS_STRING = True   # ctp_excel_export_template.app_id 是 String（勿套 Long 协议）

# 默认模板复用查找键（§4）
TEMPLATE_REUSE_LOOKUP_KEYS: tuple[str, ...] = (
    "appId", "mainFullName", "isImport", "isCustom", "isDefault",
)

# 列映射双结构（§4：两份结构缺一即列映射不完整）
COLUMN_STRUCTURES: tuple[str, str] = ("metadata_content(层级)", "excel_head_info(拉平表头)")

# 有副作用、不得自动进只读白名单的操作（§1/§4 显式分类）
SIDE_EFFECT_OPERATIONS: dict[str, str] = {
    "excel/check-excel": "解析上传模板 + 可能跨环境创建模板 + ASYNC 校验事件 + 写 Redis DOING",
    "excel/check-excel-data": "旧版同型副作用",
    "excel/import": "识别 signatureCode/实体/模板 + ASYNC 导入事件（redisKey 句柄）",
    "excel/export": "ASYNC 导出事件（redisKey 句柄；验收要到文件层）",
}

# 参照字段列映射规则（§4）
REFERENCE_FIELD_RULES: tuple[str, ...] = (
    "Many2One 参照字段使用唯一标识字段",
    "CTPENUM 选项集字段单独处理",
)

# 已知异常传播缺口候选（§4，STATIC_SOURCE，未验部署版本）
KNOWN_EXCEPTION_GAP = ("saveTreeList 更新异常 catch 只记日志不置 successFlag=false"
                       "（STATIC_SOURCE 缺口候选）→ 异步 SUCCESS ≠ 业务行成功")


@dataclass
class ExcelTemplateModel:
    """模板结构声明（离线校验面：键类型 + 双列结构 + 复用键）。"""
    app_id: str = ""                 # 必须 str（不是 int！）
    main_full_name: str = ""
    signature_code: str = ""
    metadata_content: Any = None     # 层级列元数据
    excel_head_info: Any = None      # 拉平表头
    import_flag: bool = False
    custom_flag: bool = False
    default_flag: bool = False
    belong_group_id: str = ""

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not isinstance(self.app_id, str):
            errors.append(f"app_id 类型={type(self.app_id).__name__}；ctp_excel_export_template 为 String（§4）")
        if not self.main_full_name:
            errors.append("缺 main_full_name（模板归属实体）")
        if self.metadata_content is not None and self.excel_head_info is None:
            errors.append("有层级 metadataContent 无拉平 excelHeadInfo：两份结构缺一=列映射不完整（§4）")
        if self.signature_code:
            pass
        else:
            warnings.append("无 signatureCode：跨环境签名查找将 miss → check/import 可能触发 templateService.create 副作用")
        return {"schema": SCHEMA_ID, "kind": "excel_template",
                "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
                "errors": errors, "warnings": warnings,
                "table": EXCEL_TEMPLATE_TABLE, "can_execute": False}


@dataclass
class ExcelAsyncTask:
    """异步句柄语义：redisKey ≠ 结果；终态必须回读文件/行结果/错误文件。"""
    redis_key: str = ""
    direction: str = "import"        # import | export
    state: str = "DOING"
    file_ready: bool = False         # export 到文件层 / import 到错误文件
    row_results_checked: bool = False

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        if self.direction not in ("import", "export"):
            errors.append(f"direction={self.direction!r} 不在 import/export")
        return {
            "schema": SCHEMA_ID, "kind": "excel_async_task",
            "status": "FAIL" if errors else ("PASS" if self.accepted() else "UNVERIFIED"),
            "errors": errors,
            "acceptance_rule": "redisKey 只是任务句柄；验收=文件/行结果/错误文件回读（§4）",
            "known_exception_gap": KNOWN_EXCEPTION_GAP,
            "can_execute": False,
        }

    def accepted(self) -> bool:
        return self.state == "SUCCESS" and self.file_ready and self.row_results_checked


def side_effect_classification() -> dict[str, str]:
    """供只读白名单/审计消费的副作用显式分类表。"""
    return dict(SIDE_EFFECT_OPERATIONS)


__all__ = [
    "SCHEMA_ID", "EXCEL_TEMPLATE_TABLE", "EXCEL_TEMPLATE_KEYS", "APP_ID_IS_STRING",
    "TEMPLATE_REUSE_LOOKUP_KEYS", "COLUMN_STRUCTURES", "SIDE_EFFECT_OPERATIONS",
    "REFERENCE_FIELD_RULES", "KNOWN_EXCEPTION_GAP",
    "ExcelTemplateModel", "ExcelAsyncTask", "side_effect_classification",
]

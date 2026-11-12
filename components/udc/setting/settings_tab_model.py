"""设置面板 13 tab op 目录 —— op 名/参数形态/后端归属固化。

证据基线（docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md §2.5/§3 全表，LIVE+STATIC）：
- GraphQL 调用形态四类（§1.1）：A loader 描述符 / A' mutation loader /
  B apolloQuery+前缀拼接 / C 字面量 query；D REST 直连。
- 命名硬规则（§1.2）：入参类型 `<op>InputBody|InputPath|InputQuery`；
  paramsKey=body/path/query 决定变量位置；前缀可由 appName/appId 驼峰生成。
- 关键拼写铁律：CtpParameterDefinitonPost 少一个 i 是平台原样，禁止"修正"。
- 枚举/选项集交叉命名陷阱（§2.5/§3.1-3.2）：JS key `collections` 标签"枚举"、
  key `enumeration` uniformityKey=enum 标签"选项集"——勿凭 key 猜语义。
- 外框/页面模板同一组件靠 category 分流（§3.10/3.11）；FORM 应用下两 tab 隐藏。
- 角色权限=ctp-user 微前端 RemoteComponent（§3.12），不是 udc 代码。
- 建后初始化链（§3.13）：udcBasicDataDesignInitBasicdataPagePost 返回
  masterEntityIds + dataSourceDtoList。

状态分级照 SETTINGS 文档：✅=链闭环 / ⚠️=部分 / ❌=op 已知后端未定位。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.xiaozhua-agent.settings-tab-catalog.v1"

CALLBACK_FORMS: dict[str, str] = {
    "A": "queryLoader.load({fieldType,paramsType,paramsKey,params,queryFields})",
    "A2": "udcMutationLoader.load({…})",
    "B": "apolloQuery('mutation ' + PREFIX + op + 'InputBody')",
    "C": "字面量 query（含 $params 名）",
    "D": "REST 直连 axios（如 POST /excel/set-auth）",
}

NAMING_RULES: tuple[str, ...] = (
    "入参类型命名 <Op>InputBody / <Op>InputPath / <Op>InputQuery",
    "paramsKey ∈ {body, path, query} 决定 GraphQL 变量位置",
    "op 名前缀可变形：默认 udc / appName 驼峰（qr code）/ appId 驼峰+实体末段（Excel 按实体动态 op）",
    "GraphQL introspection 已关闭 → op 原文只能从 chunk 挖，不能问 schema",
)


@dataclass
class SettingTab:
    tab: str                       # 中文标签（以 chunk 内标签为准，非 JS key）
    js_key: str = ""
    uniformity_key: str = ""
    ops: tuple[str, ...] = ()
    backend: str = ""              # 后端 Controller/服务归属；标品侧写 CTP 前缀
    status: str = "OK"             # OK / PARTIAL / UNLOCATED（照文档 ✅⚠️❌）
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"tab": self.tab, "js_key": self.js_key, "uniformityKey": self.uniformity_key,
                "ops": list(self.ops), "backend": self.backend,
                "status": self.status, "note": self.note}


SETTING_TABS: tuple[SettingTab, ...] = (
    SettingTab("枚举", js_key="collections", uniformity_key="",
               ops=("udcMetaDataSelectCtpEnumAppGet(path)",
                    "udcMetaDataSelectCtpEnumItemPost(body)",
                    "EnumCategorySearchCategoryAndEnumPost(body)"),
               backend="UdcEnumController/UdcEnumItemController/UdcEnumCategoryController/UdcCtpEnumController",
               status="OK", note="JS key 叫 collections 但标签是枚举（交叉命名陷阱）"),
    SettingTab("选项集", js_key="enumeration", uniformity_key="enum",
               ops=("EnumSearchParentByCodePost(body)",
                    "BasicDataDesignCreatePost(body,形态B)", "BasicDataDesignUpdatePost",
                    "BasicDataDesignDeletePost", "BasicDataDesignBatchDeletePost"),
               backend="DataTypeController(data-types/base) 待确认归属",
               status="PARTIAL", note="写侧 op 是否复用基础资料命名空间未验证"),
    SettingTab("自定义对象(DTO)", js_key="objectDefinition", uniformity_key="dto",
               ops=("udcCustomDataTypeSearch(body)", "SerialSchemeSearchNoPagePost"),
               backend="DataTransferObjectController(20 api)",
               status="PARTIAL", note="tab 实际渲染子页未逐层追到；DTO create-dto-with-attrs 已 LIVE"),
    SettingTab("字段集", js_key="fieldSet", uniformity_key="fieldSet",
               ops=("postEntityAttribute", "postBatchField", "updateBatchField",
                    "deleteField", "udcPageGroupCreatePost(body)", "udcPageGroupDeleteIdPost(path)"),
               backend="AttributeGroupController(7)/AttributeSetController(10)",
               status="OK"),
    SettingTab("参数", js_key="arguments", uniformity_key="arguments",
               ops=("CtpParameterDefinitonPost(body)", "CtpParameterDefinitonUpdatePost",
                    "CtpParameterDefinitonDeletePost", "CtpParameterDefinitonBatchDeletePost",
                    "udcDataTypeDataTypesParamGet"),
               backend="ParameterController(6 api)",
               status="OK", note="Definiton 拼写是平台原样，禁止修正"),
    SettingTab("扩展实体", js_key="customExtension", uniformity_key="customExtension",
               ops=("udcScalabilityOptionSelectAllOptionNamePost(body,形态A')",
                    "GET /service/udc/scalability/selectByOptionId(REST 存在性)",
                    "GET /service/udc/scalability-option/selectByAppId?appId="),
               backend="ScalabilityController(6)/ScalabilityOptionController(8)",
               status="OK", note="op↔method 名对上；写侧 GraphQL op 未逐个定位"),
    SettingTab("流水号", js_key="serialCode", uniformity_key="serial",
               ops=("udcUdcSerialSelectPost(body)", "SerialConditionBatchCreatePost(body,形态B)"),
               backend="UdcSerialConfigController(udc-runtime/serial-config)",
               status="PARTIAL", note="写侧 op 未定"),
    SettingTab("导入导出模板", js_key="excelSetting", uniformity_key="",
               ops=("udcExcelSearchListByConditionsPost(body)",
                    "<appId驼峰><实体>ExcelSearchListByConditionsPost(形态B)",
                    "udcFileDownloadUrlsPost(body)", "POST /excel/set-auth(REST D)"),
               backend="AttachmentTemplateController(7)",
               status="PARTIAL", note="落表 ctp_excel_export_template（excel_model 同源）"),
    SettingTab("二维码", js_key="qrcode", uniformity_key="qrcode",
               ops=("<appName驼峰>CtpQrcodePageMetadataListPost(body,形态B)",),
               backend="udc-web 0 命中 → 标品 Ctp 侧，UNLOCATED",
               status="UNLOCATED", note="op 构造完整；后端未定位；无独立 chunk"),
    SettingTab("页面模板", js_key="pageTemplateManage", uniformity_key="",
               ops=("udcPageTemplateGet(path)", "udcPageTemplateClassSelectTreeCategoryGet(path)",
                    "udcPageTemplateCreateOrUpdatePost", "udcPageTemplatePublishPost",
                    "udcPageTemplateDeleteByIdsPost", "udcPageTemplateCheckNamePost",
                    "udcPageTemplateSearchNoPagePost", "udcPageTemplateSearchWithRightsPost",
                    "udcPageTemplatePublishedSearchNoPagePost"),
               backend="PageTemplateController(14)/PageTemplateClassController(7)/PageTemplatePublishedController(9)",
               status="OK", note="LIVE PASS×2；FORM 应用隐藏；与外框模板同组件靠 category=PAGE 分流"),
    SettingTab("外框模板", js_key="layoutTemplateManage", uniformity_key="",
               ops=("同页面模板九个 op，靠 pageType=LAYOUT 区分",),
               backend="模板层=PageTemplateController(LAYOUT)；实例层=PageLayoutController(18)+udc_page_layout",
               status="OK", note="两层勿混；published 表 LAYOUT 6 条 LIVE"),
    SettingTab("角色权限", js_key="rolePermission", uniformity_key="",
               ops=("ctpUserCtpRoleSystemRoleSearch(body)",),
               backend="ctp-user 微前端 RemoteComponent(/ctp-user/remoteEntry.js)，非 udc",
               status="PARTIAL", note="前端 4 chunk+op 齐；后端属 ctp-user 服务未解"),
    SettingTab("基础资料", js_key="basicData", uniformity_key="",
               ops=("BasicDataSearch(A,pageInfo+sort)", "<prefix>BasicDataDesignCreatePost(B)",
                    "<prefix>BasicDataDesignUpdatePost(B)",
                    "udcBasicDataDesignInitBasicdataPagePost(A)",  # 建完即初始化页面
                    "<prefix>BasicDataDataTypesGet(A 零入参)", "<prefix>BasicDataSelectPresetAttributesGet(A 零入参)"),
               backend="javap 无 BasicData*Controller → UNLOCATED",
               status="PARTIAL", note="redux 命名空间 data-management；初始化链返回 masterEntityIds+dataSourceDtoList"),
)


def tab_catalog() -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "date": "2026-10-12",
        "evidence": "docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md",
        "call_forms": CALLBACK_FORMS,
        "naming_rules": list(NAMING_RULES),
        "tabs": [t.to_dict() for t in SETTING_TABS],
        "status_legend": {"OK": "调用链闭环", "PARTIAL": "部分", "UNLOCATED": "op 已知后端未定位"},
    }


def tabs_by_status(status: str) -> list[SettingTab]:
    return [t for t in SETTING_TABS if t.status == status]


def all_op_names() -> list[str]:
    out: list[str] = []
    for t in SETTING_TABS:
        for o in t.ops:
            out.append(o.split("(")[0])
    return out


__all__ = [
    "SCHEMA_ID", "CALLBACK_FORMS", "NAMING_RULES",
    "SettingTab", "SETTING_TABS", "tab_catalog", "tabs_by_status", "all_op_names",
]

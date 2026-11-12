from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldSpec:
    """实体字段 spec。

    订单应用语义扩展（全部可选，构造面与 attribute_semantics 对齐）：
    - options: 枚举选项值域（dataType=ENUM 时选项集 code 列表）
    - enum_name: 选项集（udcUdcEnum）引用名，options 为空时按名取
    - reference: 参照目标（dataType=ENTITY 时 relationApp/relationEntity/multiSelect）
    - default_value: 默认值六件套子集（L1 装配面证据；create 面受键 UNVERIFIED，
      build 计划里进 plan_only 不擅自进 create body）
    - uniqueness: 唯一性 Boolean（字符串报 BOOT_3002 纪律）
    - multi_select: 多选（须 dataType=ENTITY）
    """
    name: str
    type: str
    length: int | None = None
    required: bool = False
    caption: str = ""
    options: list[Any] = field(default_factory=list)
    enum_name: str = ""
    reference: dict[str, Any] = field(default_factory=dict)   # relationApp/relationEntity/...
    default_value: dict[str, Any] = field(default_factory=dict)  # 六件套子集
    uniqueness: bool | None = None
    multi_select: bool | None = None
    remark: str = ""

    def to_dict(self):
        data = {"name": self.name, "type": self.type, "length": self.length,
                "required": self.required}
        if self.caption:
            data["caption"] = self.caption
        if self.options:
            data["options"] = self.options
        if self.enum_name:
            data["enum_name"] = self.enum_name
        if self.reference:
            data["reference"] = self.reference
        if self.default_value:
            data["default_value"] = self.default_value
        if self.uniqueness is not None:
            data["uniqueness"] = self.uniqueness
        if self.multi_select is not None:
            data["multi_select"] = self.multi_select
        if self.remark:
            data["remark"] = self.remark
        return data


@dataclass
class IndexSpec:
    """实体索引（§2.8.3①：idx_/uk_ 前缀、fieldIds≤5、逗号分隔）。"""
    caption: str
    type: str = "NORMAL"          # NORMAL→idx_ / UNIQUE→uk_
    fields: list[str] = field(default_factory=list)
    remark: str = ""

    def to_dict(self):
        return {"caption": self.caption, "type": self.type,
                "fields": list(self.fields), "remark": self.remark}


@dataclass
class EventSpec:
    """实体事件（微流程事件；trigger 值域与 MicroFlowSpec.trigger 同源）。"""
    name: str
    caption: str = ""
    trigger: str = "MANUAL"      # BUSINESS_EVENT/MANUAL/SCHEDULE

    def to_dict(self):
        return {"name": self.name, "caption": self.caption, "trigger": self.trigger}


@dataclass
class EnumOptionSpec:
    """选项集（基础设置 UDC 枚举）+ 选项项。"""
    name: str
    caption: str
    items: list[dict[str, Any]] = field(default_factory=list)  # {code:int, caption, name}

    def to_dict(self):
        return {"name": self.name, "caption": self.caption, "items": list(self.items)}


@dataclass
class ReferSpec:
    """参照配置（§2.8.3③ 三步向导 body 骨架：where/columns/terminal）。"""
    caption: str
    entity: str                  # 参照实体
    terminal: str = "PC"         # PC/MOBILE
    where: list[dict[str, Any]] = field(default_factory=list)   # 条件配置
    columns: list[str] = field(default_factory=list)
    id: str | None = None        # 有 id=更新（UpdateConfigInfo）无=新建（CreateConfigInfo）

    def to_dict(self):
        return {"caption": self.caption, "entity": self.entity, "terminal": self.terminal,
                "where": self.where, "columns": list(self.columns), "id": self.id}


@dataclass
class EntitySpec:
    name: str
    fields: list[FieldSpec] = field(default_factory=list)
    # 订单应用扩展（全部可选）
    stereotype: str = ""                      # 版型（标准/单据/平铺档案/树形档案）
    parent_entity: str = ""                    # 父实体（主子表）
    attribute_set: str = ""                    # 字段集
    indexes: list[IndexSpec] = field(default_factory=list)
    events: list[EventSpec] = field(default_factory=list)
    refer: list[ReferSpec] = field(default_factory=list)
    open_api: list[str] = field(default_factory=list)   # 创建/删除/更新/查询 子集
    data_permission: bool = False              # udc_entity.permission 开关
    caption: str = ""

    def to_dict(self):
        data: dict[str, Any] = {"name": self.name, "fields": [x.to_dict() for x in self.fields]}
        for k, v in (("stereotype", self.stereotype), ("parent_entity", self.parent_entity),
                     ("attribute_set", self.attribute_set), ("caption", self.caption),
                     ("data_permission", self.data_permission)):
            if v:
                data[k] = v
        if self.indexes:
            data["indexes"] = [x.to_dict() for x in self.indexes]
        if self.events:
            data["events"] = [x.to_dict() for x in self.events]
        if self.refer:
            data["refer"] = [x.to_dict() for x in self.refer]
        if self.open_api:
            data["open_api"] = list(self.open_api)
        return data


@dataclass
class MenuSpec:
    """菜单/功能节点（function tree）。"""
    caption: str
    page: str = ""
    terminal: str = "PC"
    icon: str = ""
    order_no: int = 0
    refer_page_id: str = ""          # 菜单挂页面

    def to_dict(self):
        return {"caption": self.caption, "page": self.page, "terminal": self.terminal,
                "icon": self.icon, "order_no": self.order_no,
                "refer_page_id": self.refer_page_id}


@dataclass
class PageSpec:
    name: str
    page_url: str | None = None
    # 订单应用扩展（全部可选）
    page_type: str = ""             # LIST/DETAIL/FORM（layout_model PAGE_TYPES）
    layout: dict[str, Any] = field(default_factory=dict)      # 排版/列宽/标签
    toolbar: list[str] = field(default_factory=list)          # 工具栏按钮（含测试按钮位）
    detail: dict[str, Any] = field(default_factory=dict)      # 编辑穿透详情/详情排版
    panels: list[dict[str, Any]] = field(default_factory=list)  # 面板与打开面板动作
    page_rules: list[dict[str, Any]] = field(default_factory=list)  # 页面规则弹窗
    bind_microflow: str = ""        # 绑定微流程名
    columns: list[dict[str, Any]] = field(default_factory=list)     # 明细表列宽

    def to_dict(self):
        data = {"name": self.name, "page_url": self.page_url}
        for k, v in (("page_type", self.page_type), ("bind_microflow", self.bind_microflow)):
            if v:
                data[k] = v
        for k, v in (("layout", self.layout), ("detail", self.detail), ("columns", self.columns)):
            if v:
                data[k] = v
        for k, v in (("toolbar", self.toolbar), ("panels", self.panels),
                     ("page_rules", self.page_rules)):
            if v:
                data[k] = list(v)
        return data


@dataclass
class ExcelSpec:
    """实体 Excel 导入/导出模板与数据（ctp_excel_export_template 证据域）。"""
    entity: str
    direction: str = "export"        # import/export
    template_id: str = ""           # 有=复用模板，无=新建
    data: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return {"entity": self.entity, "direction": self.direction,
                "template_id": self.template_id, "data": list(self.data)}


@dataclass
class MicroFlowSpec:
    name: str
    trigger: str = "manual"
    nodes: list[dict[str, Any]] = field(default_factory=list)
    # 订单应用扩展：查询→转列表→查单据流程/流转日志/意见 拼接链
    group_type: str = ""            # VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE（实体规则三组）
    source_id: str = ""             # 关联实体 sourceId

    def to_dict(self):
        data = {"name": self.name, "trigger": self.trigger, "nodes": self.nodes}
        if self.group_type:
            data["group_type"] = self.group_type
        if self.source_id:
            data["source_id"] = self.source_id
        return data


@dataclass
class ApplicationSpec:
    name: str
    caption: str
    entities: list[EntitySpec] = field(default_factory=list)
    pages: list[PageSpec] = field(default_factory=list)
    microflows: list[MicroFlowSpec] = field(default_factory=list)
    # 订单应用扩展（全部可选）
    enums: list[EnumOptionSpec] = field(default_factory=list)        # 选项集
    menus: list[MenuSpec] = field(default_factory=list)             # 菜单
    excel: list[ExcelSpec] = field(default_factory=list)            # 导入导出
    app_stereotype: str = ""

    def to_dict(self):
        data = {
            "name": self.name, "caption": self.caption,
            "entities": [x.to_dict() for x in self.entities],
            "pages": [x.to_dict() for x in self.pages],
            "microflows": [x.to_dict() for x in self.microflows],
        }
        for k, v in (("enums", self.enums), ("menus", self.menus), ("excel", self.excel)):
            if v:
                data[k] = [x.to_dict() for x in v]
        if self.app_stereotype:
            data["app_stereotype"] = self.app_stereotype
        return data

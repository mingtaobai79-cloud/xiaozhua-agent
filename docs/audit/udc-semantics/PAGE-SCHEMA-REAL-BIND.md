# 页面 schema 真绑实体模板（LIVE 实证，对照成熟页逐字段对齐）

> 日期：2026-10-14 | 应用：datamigration… | 证据：**LIVE**（update-draf + update 双通，回读 FORMAL）

## 纠错：此前实验页面是空壳

第一版 schema 只塞了 `settings.entity`，**没绑数据源、没列定义** —— 不是设计器里
真实拖出的表格。本轮对照成熟列表页（迁移日志，41KB schema）逐字段解剖后重做。

## 真实 UdcDataGridView 绑实体的三要素

### 1. dataSource（数据源绑定，11 字段，核心）
```json
{
  "type": "ENTITY", "subType": "NORMAL",
  "key": "<gridId>-<entityId>",
  "isRoot": true, "isRef": false,
  "dataShape": "LIST",
  "entity": {
    "id": "<entityId>", "name": "<EntityName>",
    "fullName": "com.seeyon.<appName>.domain.entity.<EntityName>",
    "caption": "<caption>", "stereotype": "standard",
    "category": "ENTITY", "supportOrderNo": true,
    "appName": "<appName>", "appId": "<appId>",
    "parent": { ... 父实体完整信息（标准版型实体有层级时）}
  },
  "fields": [], "dataTarget": "<gridId>", "fieldBindMap": {}, "hiddenFields": []
}
```
**fullName 是硬要求**：`com.seeyon.<appName>.domain.entity.<Name首字母大写>`
（实体详情接口返回，可直接用；注意 Name 首字母大写与 name 字段不同）

### 2. settings.columns[]（列定义 = 实体字段逐一映射）
```json
{
  "dataIndex": "<字段name>", "dataType": "<STRING|BIGINTEGER|DATETIME|BOOLEAN|MULTILINESTRING|CTPENUM...>",
  "title": {"type": "Simple", "simple": "<字段caption>"},
  "componentName": "列",
  "hide": {"type": "Simple", "simple": false},
  "sorter": false, "calcColumn": {"type": "Simple"},
  "align": "left", "headerAlign": "", "description": "",
  "IconColumnOperates": [], "enableList": false,
  "displayFormate": "default", "displayFormateTime": "default",
  "decimalPlace": 2, "supportClear": false, "displayStyle": "input",
  "isGroupEnable": true
}
```
（13 列实测：STRING/BIGINTEGER/DATETIME/BOOLEAN/MULTILINESTRING 均出现）

### 3. uiModel（组件 UI 行为）
```json
{"title": {"type": "Simple", "simple": "<表格标题>", "__original__": ""}}
```
成熟页还有 controlledProps（行操作按钮：查看/编辑/删除）、flowAuthKeys。

## 保存链（两步，均已 LIVE 通）
```
① POST /udc/page-info/update-draf  {draftPageSchema: "<schema字符串>"} → 草稿 DRAFT
② POST /udc/page-info/update       {pageSchema:  "<schema字符串>"} → 正式 FORMAL
```
（schema 是 JSON **字符串**非嵌套对象；两接口 body 同构）

## LIVE 结果
- 实验页面 1520098474917276520：13 列全绑实验实体字段
- pageSchema=draftPageSchema=8121B，schemaState=**FORMAL**
- dataSource.entity.fullName 回读一致

## 待补（对照成熟页还有差距）
- uiModel.controlledProps（行按钮：查看/编辑/删除）
- UdcFilter 查询组件（容器内，条件字段绑定）
- eventDefine（页面事件/页面规则）
- 列的 showFormat/displayStyle 按字段类型差异化

## 补充：业务列 + 行按钮 + 事件（定理落地，LIVE 二次实证）

### 定理（用户定）
1. 组件操作必须带全参数类型字段与可设置项
2. **表格列只放业务字段，系统交互字段（9 个预置）不写出来**

### 验证
成熟页 13 列零系统字段 → 设计器默认剔除。实验页面重做：
- 业务列 2（expText/expEnum），系统字段泄漏 = 无 ✅
- 行按钮 3：uiModel.controlledProps = [{key,type:Button,name:查看/编辑/删除,parentCode:"actionColumnOperates"}]
- flowAuthKeys：topOperates + actionColumnOperates（各含 正常/禁用/隐藏）
- 事件 3（组件 events[]）：
  - 查看/编辑 → actionType=buildin, actionName=openPage, pageInfoType=DETAIL, openMode=view|edit
  - 删除 → actionType=widget, actionName=ENTITY_DELETE
- 保存：draft + formal 双通，回读 FORMAL，列=2 按钮=3 事件=3

### 值域引用
components/udc/page_event_model.py（ACTION_TYPES/BUILTIN_ACTIONS/WIDGET_ACTIONS/PAGE_INFO_TYPES）

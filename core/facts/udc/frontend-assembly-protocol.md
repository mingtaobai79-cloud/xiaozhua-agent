# UDC 设计器前端组装与校验协议（源码级）

> 来源: test2 设计器前端 chunk 反编译分析 + 标品 schema 实测。回答"组件是 JSON 注册还是存库、
> 画布 JSON 怎么组装、怎么校验、交互难点在哪"。

## 1. 组件注册机制：**前端内置 JSON 注册表，不是数据库**
- 设计器左侧拖拽面板 = 前端 bundle 内置的控件 schema 清单（`getControlSchema(type, terminal)`）
- 每个控件注册: `type` + 默认 `settings` + `dataSourceContainerKey` + `uiModel` + `uiModelSchema` + 可拖入的 `children` 约束
- 拖入画布 → `addCmp` action 生成 `{id, type, parentId, settings, dataSource, events, uiModel}` 节点 → 进 Redux `cmps.byId[terminal]`
- **页面实例化后才写 DB**: `udc_page_schema.page_schema`（LONGTEXT JSON）
- 结论: 构造 pageSchema 时，字段规矩的权威来源是**前端内置 schema**，比 DB 抄标品更根本

## 2. 画布 JSON 组装（childById 树）
```
{
  children: [控件id...],          // 顶层子控件
  childById: {
    <cmpId>: {
      id, type, parentId,          // 树结构
      settings: {...},             // 控件配置
      dataSource: {...},           // 数据源绑定(控件顶层, 非 settings 内!)
      events: [...],               // 事件绑定
      uiModel, uiModelSchema, extraChildren, children
    }
  },
  pageSchema 顶层: appId/pageType/pageUrl/guid/masterEntityIds/...
}
```

## 3. 数据源绑定（dataSource）——**控件顶层字段，11 键**
```
{
  type: "ENTITY", subType: "NORMAL",
  key: "<控件id>-<实体id>",
  isRoot: true, isRef: false, dataShape: "LIST",
  entity: {id, name, fullName, caption, stereotype, category, supportOrderNo, appName, appId},
  fields: [{id, name, fieldPath, fullName, parentId, group, readonly}],
  dataTarget: "<控件id>",
  fieldBindMap: {列id: 字段名},
  hiddenFields: []
}
```
- 漏 `dataSource` = "重复表查询没选实体"（实测 bug）
- `dataSource.type !== INPUT` 决定数据流传递（`getLatestDataSourceCmp` 沿 parentId 向上找）

## 4. 事件绑定（events[]）—— 按钮/表格行为的挂载点
```
{
  id, eventType: "<按钮addOperates[].id>",   // 挂到哪个触发点
  actionType: "buildin"|"microflow"|"widget",
  actionName: "ENTITY_NEW|OPEN_PAGE|...",
  callbackDataType: "ROW_DATA",              // 行数据事件
  target: "<控件id>", noticeEntitys: [实体fullName],
  condEvents: [], enableValidate: false
}
```
- `widget` 类: `target` 指定控件 + `noticeEntitys` 删除后刷新
- `buildin` 类: 内置动作（60+ 枚举: ENTITY_*/OPEN_PAGE/SET_VALUE/WEBHOOK...）
- 无 events = 按钮渲染但无行为（实测 bug: 三个按钮点不动）

## 5. 列渲染必需字段（58 键，缺 componentName 会渲染异常）
标品列模板含: `componentName:"列"` / `title` / `hide` / `sorter` / `headerAlign` / `uiModel` / `dateFormat` / `unit` / `autoGrow` 等。
**自造列只给 33 键缺 `componentName` → 表格渲染残缺**（实测 bug）。

## 6. 校验机制：schema 驱动，前端 + 后端双层
- 前端: `getControlSchema(type)` 返回内置 schema，拖入/保存时按 schema 校验 `settings`/`dataSource` 必填项
- 后端: 保存时 `submitPage`（BOOT_0000 不校验结构）；**部署时**一致性检测（`UDC_CE_PAGE_03907` 空页面阻断）
- "每次加组件→保存→看一致性错误"= 用后端校验兜底，但**最优是先按前端 schema 规矩构造**

## 7. 交互难点（实测踩坑汇总）
| 坑 | 根因 | 正解 |
|---|---|---|
| 按钮无行为 | events[] 空 | 绑 buildin/widget 动作 |
| 重复表查询没选实体 | dataSource 漏了/放错位置 | 控件顶层 11 键 |
| 表格渲染残缺 | 列缺 componentName 等 25 键 | 照抄标品列模板 |
| 顶部放新增/删除 | 套单据模板没看数据语义 | 明细表只留刷新, 操作列放尾巴 |
| dynamic-rest 402 | 应用坐标(publishState) | 需 app-online 转正(test2 环境限制) |

## 8. 写入通道（test2 现实路径）
- `dynamic-rest/{entityAppName}/{entityName}/{controlId}/create|update|delete|...`（19 模板，字节码提取）
- BOOT_4002 应用坐标 = publishState 未转正；test2 无 push 目标环境 → 不可达
- 可用: ①DB 直插+data/query 回读(已通) ②CRUD 表单页 TEST 部署 ③微流程数据保存节点

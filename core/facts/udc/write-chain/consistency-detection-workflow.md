# 页面一致性检测与修复 REST 工作流 —— LIVE 取证（2026-10-15 下午）

> 主路径 REST（CDP 仅用于读设计器内存态）。完整闭环：修复数据源绑定 → REST 保存 → REST 检测 → REST 构建 ×5 轮。

## 1. 修复动作（REST 闭环）

### 病灶
`udc_page_schema.page_schema`（page_id=1520098474917276520）中 `udcDataGridView_xzh1.dataSource.fields=[]、fieldBindMap={}`（10-14 保存引入）→ 一致性检测 ERROR → 构建 FAIL。

### 修复路径
1. **设计器内点击**（取证）：大钢树选表格 → 属性面板"实体"输入框 → "选择实体"弹窗 → 重选同一实体 → 确定。redux 内存态 fields 0→2。
2. **导出 schema**：`window.reduxStore.getState().cmps.byId.PC`（PAGE + grid 全量 JSON，7.5KB）。
3. **REST 保存**（关键发现：保存协议见 `designer-save-protocol.md`，直接按契约发 GraphQL）：

```
POST /service/udc/graphql?udcPageInfoUpdatePost
{query:"query graphqlLoader ($params0: udcPageInfoUpdatePostInputBody) {
   data0: udcPageInfoUpdatePost(body: $params0) { code data { content } message status } }",
 variables:{params0:{appId, id:<originId>, caption, pageType, pageUrl, urlType, guid,
   relationGroupId, pageSchema:<JSON.stringify(完整schema)>, draftPageSchema:<同>,
   masterEntityIds, eventDefine, pageVariable, inParams, outParameters, inPortletParams,
   settings, layoutInfo:'', layoutId:'0'}}}
→ BOOT_0000 SUCCESS，DB 回读：update_time 变化、fields=2、bindMap=2 ✓
```

## 2. schema 结构规约（重要事实）

**正常页面 schema 顶层即 PAGE 内容，`childById` 只含真实子控件、不含 PAGE 自身。**
我们最初从 redux 导出时把 PAGE 也塞进了 childById（`childById.PAGE.type='PAGE'`），检测器报
`UDC_CE_PAGE_03108 The component has been deleted (path=childById.PAGE.type)`。
修正结构后 03108 **消除（LIVE VERIFIED）**。

正常页面（对照样张 5175227629061096197）顶层键：
`masterEntityIds, appId, children, urlType, defaultOpenType, handWritten, settings,
layoutVisibleControl, pageLayout, outParameters, pageVariable, type(PAGE), eventDefine,
terminal, toBeChangedMicorflowIds, ...` + `childById{各控件}`。
注意：无 `id/publishState/caption/isDraftPage/inParams`（这些在 udc_page_info 表列，不在 schema JSON 里）。

## 3. 一致性检测 REST 面

```
POST /service/udc/graphql?udcApplicationSearchDetectionPost
variables.params0 = {appId}
→ content[]: {detectionType: ERROR|WARN, code, moduleType, domainEntityId,
   interpolatedDocument/Element/Message, path, elementType, moduleProperty, elementProperty}
```

ERROR 检码（本轮实测全量）：
| code | 语义 |
|---|---|
| UDC_CE_ENTITY_02104 | Attr relation ctpEnum not exist（枚举字段关联的 CTP 枚举不存在）|
| UDC_MICRO_FLOW_04004 | micro flow node data error：依赖应用已删除 |
| UDC_CE_PAGE_03907 | 页面 menu-widget 内容为空，从未设计保存 |
| UDC_CE_PAGE_03108 | childById 里的组件 type 不在合法组件表（如混入 'PAGE'）|
| UDC_CE_PAGE_03103 | widget 事件关联页面不存在/不属于当前端（pageUrl 指向的页面无效）|

检测在构建流水线的 `doParallel` 阶段并行执行（AbstractDeployService.java:242），任一 ERROR → 整体 FAIL，不进编译。

## 4. 构建验证 ×5（deploy-normal RELEASE → search-deploy-status）

| 轮 | jarVersion | 结果 | 说明 |
|---|---|---|---|
| 1 | 1.0.8 | FAIL | fields 修复已保存，但 schema 里还有 childById.PAGE（我们导出的结构错）|
| 2 | 1.0.9 | FAIL | pageUrl 补绑详情页 → 详情页本身空（03907）级联 |
| 3 | 1.0.10 | FAIL | pageUrl 已清但 DB 回读未生效（save 引用了旧 childById 引用对象）|
| 4 | 1.0.11 | FAIL | 结构修正（去 childById.PAGE）→ **03108 消除** ✓；余固有 ERROR |
| 5 | 1.0.12 | FAIL | 同上，余 7 ERROR |

## 5. 遗留 ERROR（应用固有，非本次修复范围）

1. `03907` ×3：页面 :WEB端 / 小爪实验详情958006 / 958033 的菜单 widget 空——**详情页 schema_len=0**（菜单自动生成、从未设计保存）
2. `03103` ×2：列表页 ev_view/ev_edit 事件关联页面无效（指向空详情页；事件已删仍报 → 检测器可能读发布镜像或另有缓存，**UNVERIFIED**）
3. `02104`：expEnum 字段关联的 CTP 枚举不存在（实体级）
4. `04004`：微流程"小爪实验微流程953182-已更新"的"微流程入参"节点依赖应用已删除

**结论：fields 空绑定修复 = LIVE VERIFIED（03108 消除 + DB 落库三方一致）。构建要绿需先清固有 ERROR（设计保存两个详情页/修枚举关联/修微流程引用）——这是后续任务。**

## 6. 工具沉淀（scratch/）

- `cdp_drive.js`（eval/open/net）、`cdp_click.js`（坐标点击）、`cdp_drag.js`（CDP 原生拖拽）、`click_save.js`（React onClick 安全调用）
- reduxStore 直读四域：cmps / entityMetaData / dataSource / history
- `submit_body.json` 组装函数（本文件 §1.3 的 body 结构可直接复用）

## 5. ★★ UI 三个数字 vs API detectionType 的对应关系（2026-11-01 实测）

设计器底部面板显示「N 阻断 / N 严重 / N 警告」，
GraphQL `udcApplicationSearchDetectionPost` 返回的是 `detectionType` 字段。
两者是同一批数据的不同口径：

| UI 显示 | API detectionType | 是否阻塞发布 |
|---|---|---|
| 阻断（红色锁） | `ERROR` | **是**，构建必失败 |
| 严重（紫色 ×） | 更高等级（本次样本 0 条） | 不阻塞 |
| 警告（黄色三角） | `WARN` | 否 |

实测对照（同一时刻）：

```
UI :  2 阻断 / 0 严重 / 13 警告   = 15 条
API:  2 ERROR / 13 WARN          = 15 条
```

★ 只看 API 的 `detectionType == 'ERROR'` 数量即可等价判断 UI 的「阻断」，
不必猜。但**汇报时必须两边都取一次**——UI 才是用户看到的。

## 6. 阻断的典型成因：旧流程引用了失效的实体属性

```
[ERROR] 查询数据源:实体属性已更改(ID)
  文档: UI最终化探测        | 元素: 查询数据源
  文档: 验收3-多字段-524500 | 元素: 查询数据源
```

实体属性变更（改名/删除/换 ID）后，旧微流程里保存的字段引用就悬空了。
平台把它判成**阻断**，整个应用构建被挡（日志：`一致性检测未通过`）。

处理：删掉这些旧流程（测试残留）或重新选字段。
本次删 2 条后：`13 WARN → 11 WARN，ERROR=0`，UI 同步变成 `0 阻断 / 0 严重 / 11 警告`，
构建随即成功。

★ 教训：**测试流程不要发布成 RELEASE**。它们引用的字段一旦失效，
就会变成阻断，把整个应用的构建链拖死。

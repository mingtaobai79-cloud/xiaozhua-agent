# 页面规则域（type=1 FRONTEND）节点流转 —— 真机验证

> 承接 `microflow-vs-pagerule-node-domains.md`（两域分离）。
> 状态：**页面规则入口已定位 + 28 种前端节点融合流程 LIVE 渲染通过**

## 1. ★ 页面规则入口与标识（真机取证）

```
入口路径:  /main/child-frame/udc/app-design/pagerules?appId=<appId>
           （不是 page-rule / rule/pagerule，那些白屏）
编辑器:    /main/child-frame/udc/app-design/rule/microflow/editor/<id>?appId=<appId>
```

**页面规则 = `udc_microflow_info` 里 `type=1 (FRONTEND)` 的微流程**，与标准微流程同表不同 type。

### 列表筛选（真机捕获）
```
POST /service/udc/graphql?udcMicroflowSearch
{"params": {"appId": <appId>, "type": "FUNCTION"}, "pageInfo": {...}, "sort": {"orders": [{"direction":"ASC","property":"caption"}]}}
```
分组：`udcMicroFlowGroupSelectByTypePost` `{appId, type:"FRONTEND_FUNCTION"}`。

### `MicroFlowGroupTypeEnum`
```
BACKEND(0) / FRONTEND(1) / ALL(2)
```

## 2. ★★ 前端微流程必须绑页面（`sourceId`）

```
POST udcMicroflowCreatePost（type=FRONTEND，不带 sourceId）
→ UDC_MICROFLOW_0015 "The microFlow schema parameter sourceId does not exist"
```

`udc_microflow_info.source_id` = **绑定的页面 id**（`udc_page_info.id`）。实测样本：
```
保存       source_id=7286622650788629332
全量同步   source_id=114216775019154694     (= 迁移方案配置列表)
111        source_id=72064815891039882      (= 日志详情)
11         source_id=1805559981642060210     (= 小爪实验详情958033)
```
⇒ **页面规则依赖应用页面**（`type=1` + `sourceId`），标准微流程（`type=0`）不需要。

## 3. 前端微流程 vs 标准微流程 dataSchema 差异

| 维度 | 标准（type=0） | 页面规则（type=1） |
|---|---|---|
| `trigger` | `{nodeId:MFStartNode, type:MANUAL, paramType:BASIC, basic, isArray, desc, output}` | `{nodeId:MFStartNode, caption:"开始", type:MANUAL, input:null, output:null}`（**无 paramType/basic**）|
| `input`/`output` | 顶层必填（DTO/ARRAY） | **常为 null** |
| `endNode` | 含 `paramType/basic/isArray` + output | `{nodeId:MFEndNode, type:END, actionType:END_NODE, caption:"结束"}`（简版）|
| `sourceId` | 不需要 | **必填**（页面 id）|
| `triggerType` | MANUAL / SCHEDULE | `FRONTEND_PARAM(3)` |

## 4. ★ 28 种前端节点（真实结构已收集 `real_type1_nodes.json`）

```
调用类:  CALL_MICRO_FLOW(调用微流程) / CALL_FRONT_FLOW(调用前端流程) / CALL_DATA_FLOW_FRONT(执行生单规则)
变量:    CREATE_VARIABLE_FRONT / CHANGE_VARIABLE_FRONT
列表:    CREATE_LIST_FRONT / CHANGE_LIST_FRONT / FED_LIST_OPERATION
控件:    CONTROL_ACTION / CONTROL_STATUS
表单:    ENTITY_SAVE / ENTITY_SAVE_DRAFT / ENTITY_REFRESH
提示:    MESSAGE_INFO / MODAL / CONFIRM_CLOSE_PAGE
页面:    OPEN_PAGE / OPEN_LINK / RELOAD_PAGE
事件:    THROW_EVENT / FLOW_ACTION
附件:    ATTACHMENT_UPLOAD / ATTACHMENT_DOWNLOAD
导入导出: ENTITY_IMPORT / ENTITY_EXPORT
值处理:  VALUE_HANDLE / CONVERT_DATA_FRONT
共用:    BRANCH
```

## 5. LIVE 验证（28 前端节点融合）

```
caption: 小爪页面规则-全前端节点
id:      4774717078364917047
type:    FRONTEND (1)
sourceId: 1520098474917276520   （小爪实验页面951440）
jsonSchema: NULL
checkSchema: {check:true, errors:0}
真机渲染: hasStart=true, hasEnd=true, hasUndefined=false  ✅ 画布正常
```

节点链（28 种，真实结构 + 本应用实体引用）：
```
调用微流程 → 调用前端流程 → 执行生单规则 → 值操作 → 创建变量(前端) → 修改变量(前端) →
创建列表(前端) → 修改列表(前端) → 列表操作(前端) → 控件动作 → 控件状态 → 保存记录 →
保存草稿 → 刷新实体 → 提示消息 → 弹窗 → 确认关闭页面 → 打开页面 → 打开链接 →
重新加载页面 → 抛出页面事件 → 附件上传 → 附件下载 → 导入 → 导出 → 流程动作 →
类型转换(前端) → 分支
```

## 6. 复现

```bash
python collect_front.py       # 收集 28 种真实 type=1 节点结构
python front_all_build2.py    # 建页面规则微流程（含 sourceId）
node cdp_login.js "<编辑器URL>"  # 真机打开验证渲染
```

## 7. 边界（未做）

- 页面规则**绑定到页面控件**（哪个按钮触发）未做——`sourceId` 只绑了页面，未绑控件事件。
- `udcMicroflowCopyPageRuleBoundControlPost`（复制页面规则绑定控件）未测。
- 页面规则**运行期**未触发（前端需页面交互）。
- `MODAL`/`OPEN_PAGE` 的页面参数（`pageId`/`pageParamsMapping`）用了真实样本的原值，未换成本应用页面。

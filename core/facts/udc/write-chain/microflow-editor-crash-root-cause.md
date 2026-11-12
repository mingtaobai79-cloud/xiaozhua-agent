# 微流程编辑器"点击报错"根因 —— jsonSchema + 节点字段完整性

> 用户报告：`TypeError: Cannot read properties of undefined (reading 'map')` at `e1 (src_redux_store_ts...)`
> 状态：**根因已定位 + 最终正确流程已建成并真机渲染验证**

## 1. 报错定位（前端 bundle 反查）

```
TypeError: Cannot read properties of undefined (reading 'map')
    at e1 (src_redux_store_ts.14dc061e.js:1:1375069)
```
`e1 = ({nodeLists}) => createElement(eH, null, nodeLists.map(...))` —— **`nodeLists` 为 undefined 时崩**。

调用点（同 bundle）：
```js
case "FOR_EACH": case "FOR":
  u = createElement(ez, d, createElement(eK, null, createElement(e1, {nodeLists: i})));
  break;
```
⇒ `i`（容器节点的 children）缺失 → `e1` 收到 undefined → `.map` 崩。

## 2. ★ 两个根因

### 根因 A：`jsonSchema` 塞了假结构

- **本应用所有真实标准微流程的 `json_schema` 都是 NULL**（`小爪标品服务定义`/`定时任务`/`事件监听`/`消息总线监听` 全部 `js=null`）。
- 我 create 时传了 `{"nodes":[],"lines":[]}`（26 字节）→ 前端按图形结构渲染，找不到 TRIGGER/END → 崩。
- 真实 `jsonSchema`（type=1 样本）是**完整图**：
  `{id,appId,sourceId,version,versionCode,name,caption,description,type,triggerType,entityId,eventId,input,output,sourceType,endNode,publishState,state,creationMethod,serviceInterface,nodeNumberList,nodes[],trigger}`
  其中 `nodeNumberList` = `{actionType: count}` 映射。

**修法**：`jsonSchema` 留 NULL（与所有真实流程一致），让前端从 `dataSchema` 构建。

### 根因 B：★ 手写节点字段不完整

**二分定位**（用正常流程 4 节点为底，逐个追加我的节点，真机打开看是否崩）：

| 结果 | 节点 |
|---|---|
| ✅ 正常渲染 | CREATE_VARIABLE / CREATE_LIST / CHANGE_LIST / LIST_OPERATION / MAP_OPERATION / DATA_MAPPING / CHANGE_VARIABLE / CHANGE_ENTITY / DELETE_ENTITY / SUB_MICROFLOW / CALL_APP_SERVICE / PUBLISH_BUSINESS_EVENT |
| ❌ 画布崩 (`undefined.undefined`) | **CREATE_ENTITY** / **CONVERT_DATA** |
| ⚠️ 异常 | CHANGE_BATCH_ENTITY（沙箱准备中） |

崩溃时控制台：`Uncaught (in promise)` at `seeyon.vendor.global...js`。

**结论**：我手写的 `CREATE_ENTITY` / `CONVERT_DATA` 节点字段不完整（缺真实样本里的 `customs`/`iconKey`/`parentLabel`/`disabled` 等 selectParam 子字段，或 output/selectParam 形态差异）→ 前端渲染器取不到必需字段 → 崩。

## 3. ★ 正确做法：逐字照抄真实 type=0 节点结构

从全库 `type=0` 微流程中收集 **18 种节点的真实完整结构**（`real_type0_nodes.json`），
只重写 `nodeId` / `runAfter` / `output.name`，实体引用换成本应用实体。

```python
# 关键：adapt() 只换实体引用，不删字段
if isinstance(n.get('app'), dict): n['app'] = MY_APP_INFO
if isinstance(n.get('structure'), dict): n['structure'] = MY_STRUCT
o = n.get('output')
if isinstance(o, dict) and o.get('dataType')=='DTO': o['id']=DTO; o['javaType']=DTO; ...
sp = n.get('selectParam')
if isinstance(sp, dict): sp['appName']=APPNAME; ...  # 保留 customs/iconKey 等原字段
```

## 4. LIVE 验证（最终正确流程）

```
caption: 小爪标准微流程-全节点流转(最终)
id:      -1014184770817921434
type:    SERVICE (0)
jsonSchema: NULL
checkSchema: {check:true, errors:0}
真机渲染: hasStart=true, hasEnd=true, hasUndefined=false  ✅ 画布正常
```

节点链（18 种，runAfter 扁平 null，真实结构）：

```
创建变量 → 查询单条 → 查询多条 → 创建列表 → 修改列表 → 列表操作 → 映射操作 →
数据转换 → 修改变量 → 更新数据 → 批量更新 → 插入数据 → 删除数据 → 类型转换 →
子微流程 → 自定义服务 → 事件投递 → 分支
```

## 5. 节点结构陷阱清单（真机踩坑）

| 陷阱 | 表现 | 正确做法 |
|---|---|---|
| `jsonSchema` 塞假结构 | 画布白屏/`.map` 崩 | 留 NULL |
| 手写节点字段不全 | CREATE_ENTITY/CONVERT_DATA 崩 | 照抄真实完整结构 |
| `name` 含下划线 | `UDC_ENTITY_0001 illegal, must be combination of letters and numbers` | 纯字母数字 |
| `caption` 重复 | `UDC_MICROFLOW_0002 caption already exists` | 唯一 |
| `name` 重复 | `UDC_MICROFLOW_0001 name already exists` | 唯一 |
| `type` 用 CUSTOM | 不是标准微流程 | SERVICE(0) |
| 缺顶层 `output` | 不是标准微流程 | 必填 |

## 6. 复现

```bash
python collect_real.py      # 收集 18 种真实 type=0 节点结构
python bisect3.py           # 二分：正常节点 + 我的单节点，建流程
node bisect_ui.js           # 真机逐个打开，判断崩/不崩
python final_build.py       # 真实结构 + 本应用实体 → 最终流程
```

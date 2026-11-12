# PUBLISH_BUSINESS_EVENT（事件投递）节点契约

取证：CDP 真实建节点 → 两种 eventType × 两种 messageType 全枚举 → 空提交抓必填 → 前端 bundle `ec={group:"base",name:"事件投递",type:"BusinessEvent"}` 权威定义交叉验证 → 数据源函数 `ed`/`eu` 反编译。
证据目录：`scratch/publish_event-evidence/`。

> **落库状态：UNVERIFIED** —— 当前测试应用无可投递的 MQ 消息定义，
> 两个事件下拉均为空（下拉显示「暂无数据 新建」），无法完成完整提交。
> 已用 `udcMicroflowSearchEventListPost`（传 `appId`）验证事件列表接口可用，
> 返回 `XzhVerifyEvent`（小爪验收事件）。
> 以下节点结构结论来自**前端权威定义 + UI 实测联动**，未经后端回读证实。
> 落库前置条件：应用需先配置 MQ 消息定义（应用设计 → 消息定义）。

## 1. 双「事件类型」标签陷阱（最容易踩）

抽屉里有**两个 label 都叫「事件类型」**的 form-item，靠 DOM `id` 区分：

| form-item 索引 | DOM id | key | 选项 |
|---|---|---|---|
| 第 1 个 | `#eventType` | `eventType` | 应用间(异步) `AMONG_APP` / 应用内(同步) `IN_APP` |
| 第 2 个 | `#messageType` | `messageType` | 普通事件 `DEFAULT` / 延迟事件 `DELAY` |

DOM 结构（实测）：
```html
<div class="ant-radio-group ... xiaozhua-btn" id="eventType">
  <label class="ant-radio-button-wrapper ...">
    <input type="radio" class="ant-radio-button-input" value="AMONG_APP">
    <span>应用间(异步)</span></label>
  <label class="ant-radio-button-wrapper ...">
    <input type="radio" class="ant-radio-button-input" value="IN_APP">
    <span>应用内(同步)</span></label>
</div>
<div class="ant-radio-group ... xiaozhua-radio" id="messageType">
  <label class="ant-radio-wrapper ...">
    <input type="radio" class="ant-radio-input" value="DEFAULT"><span>普通事件</span></label>
  <label class="ant-radio-wrapper ...">
    <input type="radio" class="ant-radio-input" value="DELAY"><span>延迟事件</span></label>
</div>
```

**注意**：`eventType` 用的是 `ant-radio-button-wrapper`（button 型），
`messageType` 用的是 `ant-radio-wrapper`（圆点型）。
按 `.ant-radio-wrapper` 找 `eventType` 会拿到空文本，必须同时匹配两种类名。

## 2. 联动矩阵（实测）

| eventType | messageType | 显示字段 |
|---|---|---|
| `AMONG_APP` | `DEFAULT` | 事件类型 / 选择应用 / 可投递的事件 / 事件类型 |
| `AMONG_APP` | `DELAY` | 事件类型 / 选择应用 / 可投递的事件 / 事件类型 / **发送时间** |
| `IN_APP` | —（隐藏） | 事件类型 / 可投递的事件 |

- **`IN_APP` 时「选择应用」被隐藏**（`ishidden: eventType !== "AMONG_APP"`）
- **`IN_APP` 时 `messageType` 整块隐藏**（`ishidden: eventType !== "AMONG_APP" || dynamicDependency === "INTEGRATION"`）
- **`DELAY` 时「发送时间」必填**（`DateTime` 类型）

## 3. 字段与必填

| key | 标签 | 类型 | 必填 | 默认值 | 显示条件 |
|---|---|---|---|---|---|
| `eventType` | 事件类型 | radio(button) | ❌ | `"AMONG_APP"` | 恒显示 |
| `app` | 选择应用 | applicationSelector | ✅ | 当前应用 | `eventType == "AMONG_APP"` |
| `selectMq` | 可投递的事件 | treeListSelector | ✅ | — | `eventType == "AMONG_APP"` |
| `selectEvent` | 可投递的事件 | treeListSelector | ✅ | — | `eventType == "IN_APP"` |
| `messageType` | 事件类型 | radio | ❌ | `"DEFAULT"` | `AMONG_APP` 且非 INTEGRATION 应用 |
| `executeTime` | 发送时间 | valueComponent | ✅ | — | `AMONG_APP && messageType == "DELAY"` |
| `mappingType` | 赋值方式 | radio(button) | ✅ | `"attrs"` | 选中事件且事件有 contentDto |
| `value` | 参数 | prenodeSelector | ✅ | — | 选中事件且事件有 contentDto |
| `attrs` | 参数映射 | attrsField | ❌ | — | `mappingType == "attrs"` |

空提交实测报错：
```
selectMq  请输入可投递的事件
```

## 4. 数据源（反编译证实）

```javascript
// AMONG_APP 专用：可发送的 MQ 消息
function ed(e){
  if(!g.sZ || !e?.appName) return [];
  let t = await fetchSendMqList({appId: g.sZ, appName: e.appName});
  return Array.isArray(t) ? t.map(e=>({
    key:e.fullName, label:e.caption, value:e.fullName,
    fullName:e.fullName, topic:e.topic, contentDto:e.contentDto,
    customs:e.customs, caption:e.caption
  })) : [];
}

// IN_APP 专用：微流程事件 DTO
function eu(e){
  if(!g.sZ || !e?.appName) return [];
  let t = await fetchMicroFlowEventDtoList({appId: g.sZ, appName: e.appName});
  return Array.isArray(t) ? t.map(e=>({
    key:e.fullName, label:e.caption, value:e.fullName, fullName:e.fullName,
    caption:e.caption, source:e.source, dtoType:e.dtoType, udcApp:e.udcApp
  })) : [];
}
```

**两种事件源完全不同**：
- `AMONG_APP` → `fetchSendMqList`，返回带 `topic` + `contentDto` + `customs` 的 MQ 消息
- `IN_APP` → `fetchMicroFlowEventDtoList`，返回带 `source` + `dtoType` + `udcApp` 的事件

## 5. 关键认知

1. **两种「可投递的事件」字段名不同**：
   - `AMONG_APP` → **`selectMq`**
   - `IN_APP` → **`selectEvent`**
   两者共用同一个 label「可投递的事件」，但 key 完全不同。
2. **`selectMq` 的选项结构必须带 `contentDto`**：
   `{key, label, value, fullName, topic, contentDto, customs, caption}`
   缺少 `contentDto` 会导致后续「赋值方式 / 参数」字段不显示。
3. **`setEmptyBeforeChanged` 清空链**：
   - 切 `eventType` → 清空 `app / selectMq / messageType / attrs / mappingType`
   - 切 `app` → 清空 `selectMq / messageType / attrs / mappingType`
   - 切 `selectMq` → 清空 `value / attrs / mappingType / messageType`
   - 切 `messageType` → 清空 `executeTime`
   → 切换顺序必须 从外到内（eventType → app → 事件 → messageType）。
4. **`type` 是 `BusinessEvent`（首字母大写）**，不是全大写 `PUBLISH_BUSINESS_EVENT`。
   回读用 `actionType == 'PUBLISH_BUSINESS_EVENT'`。
5. **落库前置条件**：应用必须先配置 MQ 消息定义，否则 `fetchSendMqList` 返回空。
   这是**环境依赖**，不是节点契约缺陷。
6. **事件列表接口**：`udcMicroflowSearchEventListPost`，body 必须传 **`appId`**（不是 `appName`），
   否则报 `当前应用Id 不能为null`。返回项含 `fullName / caption / source / dtoType / udcApp / id`。

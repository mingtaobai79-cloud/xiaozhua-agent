# udc.designer.protocol｜页面设计器保存/提交协议（前端源码级）

## 保存协议（从 React 前端源码 src_redux_store_ts 提取）

### 暂存草稿
```
GraphQL Mutation: savePageDraft($body: udcPageInfoUpdateDrafPostInputBody)
  → udcPageInfoUpdateDrafPost(body: $body)
```

### 保存并提交
```
GraphQL Mutation: submitPage($body: udcPageInfoUpdatePostInputBody)
  → udcPageInfoUpdatePost(body: $body)
```

### body 关键字段（前端源码逐字提取，2026-11 复核）

**两条链路 body 不同，别混：**

| 动作 | mutation | schema 键 |
|---|---|---|
| 暂存草稿 | `udcPageInfoUpdateDrafPost` | `draftPageSchema` |
| 保存并提交 | `udcPageInfoUpdatePost` | `pageSchema` |

两者都由同一个序列化函数 `l.m()` 产出，**不是 `JSON.stringify` 裸调**（见下节）。

`submitPage` 的真实 body（函数 `A(e)`，offset ~2130913 附近，21 键）：

```javascript
{
  appId,                 // v.appId
  id,                    // v.originId   ← 不是 v.id
  urlType,               // v.terminal
  pageSchema,            // (0,l.m)(v)   ← 序列化后的完整页面树
  pageUrl, pageType,
  publicAccess,          // v.settings.publicAccess ?? false
  defaultOpenType, description, groupId,
  guid, relationGroupId, sortNo,
  inParams,              // JSON.stringify，空则 undefined
  outParameters,         // JSON.stringify
  inPortletParams,       // JSON.stringify
  layoutId,              // v.layoutInfo?.id ?? "0"
  layoutInfo,            // JSON.stringify，空则 ""
  referConfigParameters, // 空则 null
  defaultPlan,
  operationLog,          // (0,o.Mc)(E, terminal) 的返回值
}
```

**此格 2026-11 之前写的字段有误，已按下述源码改正：**

| 旧写法 | 实际 |
|---|---|
| 同时传 `pageSchema` + `draftPageSchema` | 二选一，由 mutation 决定 |
| `caption` | **不在 body**（只进 `operationLog` 的入参 E） |
| `masterEntityIds` | **不在 body**（只出现在读回来的页面对象里） |
| `settings: JSON.stringify(...)` | **不在 body**，只取 `settings.publicAccess` |
| `eventDefine` / `pageVariable` | **不在 body** |
| — | 缺 `defaultOpenType` / `description` / `groupId` / `sortNo` / `defaultPlan` / `referConfigParameters` / `operationLog` |

### pageSchema 序列化：不是 JSON.stringify

`l.m(v)`（webpack 模块 21252）真实实现：

```javascript
l = e => {
  let t = {};
  e.expressSchemaPathMaps = "__EXPRESS_PATH_REPLACE__";
  return JSON.stringify(e, (0,a.m4)(e,t))
           .replace(/"__EXPRESS_PATH_REPLACE__"/g, JSON.stringify(t))
}
```

`m4`（模块 19222）是 replacer，做表达式路径编码：

```
字段名里的 - 删除、. 换成 _dot_、空格换成 _p_
表达式中 ORDER 作用域加 _o_ 前后缀
Enum / CtpEnum / Entity 类型的路径段会被裁掉
```

**推论（未实测，标 UNVERIFIED）**：离线拼 pageSchema 时若直接 `json.dumps`，表达式绑定会因路径编码不同而在打开设计器时丢失或错位。要走平台同款序列化才安全。

### 证据级

`VERIFIED_FRONTEND_SOURCE` —— 全部从 `src_redux_store_ts.14dc061e.js` 反混淆提取，**未经 LIVE 提交验证**。真实提交需在 test2 上建页并回读比对。

### DB 存储
```
udc_page_schema.page_schema = pageSchema JSON（正式）
udc_page_schema.draft_page_schema = draftPageSchema JSON（草稿）
udc_page_schema.page_id → udc_page_info.id
udc_page_schema.schema_state = 2 (FORMAL)
```

### 微流程保存协议
```
GraphQL Mutation: 类似 submitPage → dataSchema: JSON.stringify(dataSchema)
dataSchema = {
  appId, name, caption, type: "SERVICE",
  triggerType: "MANUAL" | "EVENT" | "SCHEDULE",
  entityId, eventId,
  input: {...}, output: {...},
  nodes: [...],                            // 画布节点
  sourceType: "PAGE"
}
```

## 源码位置
- 前端 chunk: `docs/audit/frontend/chunks/src_redux_store_ts.14dc061e.js`
- 关键函数: `savePageDraf`(s()) 与 `submitPage`(m()) 的 GraphQL 串在 offset ~2121648
- 草稿 body 组装: 函数 `I(e,t)` @ ~2127200（用 s() = DrafPost）
- 正式 body 组装: 函数 `A(e)` @ ~2130913（用 m() = UpdatePost），含 operationLog
- 序列化: webpack 模块 21252 (`l.m`) + 19222 (`m4` replacer) @ ~2341892
- 页面 schema 读取: `udcPageInfoDesignerSelectDetailListByConditionsPost`
- 微流程 Schema 组装: `dataSchema: JSON.stringify(Z)` @ offset ~1256681

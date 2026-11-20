# 两类微流程必须完全分开（用户指正，2026-11-18）

> 来源：白明涛明确指正
> 「自定义微流程和标准微流程不是一个东西，一个是搭建，一个是写代码，
>   虽然本质都是一样的，但是实现逻辑不一样，你得完全分开，
>   自定义微流程没有什么节点。
>   还要就是自定义微流程不要加数据库断言，有时候你都不知道能不能访问数据库。」

---

## 1. ★★★ 核心区分

| 维度 | **标准微流程** | **自定义微流程** |
|---|---|---|
| **实现方式** | **页面搭建**（拖节点） | **写代码**（Java 扩展） |
| **有无节点** | **有 56 种 actionType** | **没有节点概念** |
| **谁来做** | 业务人员在页面上配置 | 开发人员写 Java |
| **产物** | `data_schema` JSON（DB 里） | Java 类 + 扩展点实现 |
| **入口** | 微流程设计器 | 代码 |
| **验证方式** | 画布必填 + 构建 + 运行 | 编译 + 部署 + 调用 |
| **数据库断言** | ✅ 适用（流程内可读写实体） | ❌ **不适用**（不保证能访问数据库） |

---

## 2. 标准微流程（页面搭建）

### 2.1 节点体系

**后端 56 种 actionType**（LIVE 级，4,943 条真实微流程统计）：

| actionType | 次数 | 中文名 |
|---|---|---|
| `BRANCH` | 2,573 | 分支 |
| `CALL_MICRO_FLOW` | 1,460 | 调用微流程 |
| `RETRIEVE` | 910 | 查询单条数据 |
| `CREATE_VARIABLE` | 752 | 创建变量 |
| `VALUE_HANDLE` | 637 | 值操作 |
| `CHANGE_VARIABLE_FRONT` | 537 | 修改变量（前端） |
| `FOR_EACH` | 488 | 列表循环 |
| `CREATE_LIST` | 389 | 创建列表 |
| `CREATE_VARIABLE_FRONT` | 382 | 创建变量（前端） |
| `RETRIEVE_ARRAY` | 320 | 查询列表 |

**完整 56 种（字母序）：**
```
ATTACHMENT_DOWNLOAD      ATTACHMENT_PREVIEW      ATTACHMENT_UPLOAD
BRANCH                   CALL_APP_SERVICE        CALL_DATA_FLOW
CALL_DATA_FLOW_FRONT     CALL_FRONT_FLOW         CALL_MICRO_FLOW
CHANGE_BATCH_ENTITY      CHANGE_ENTITY           CHANGE_LIST
CHANGE_LIST_FRONT        CHANGE_VARIABLE         CHANGE_VARIABLE_FRONT
CLOSE_PAGE               CONFIRM_CLOSE_PAGE      CONTROL_ACTION
CONTROL_STATUS           CONVERT_DATA            CONVERT_DATA_FRONT
CREATE_BATCH_ENTITY      CREATE_ENTITY           CREATE_LIST
CREATE_LIST_FRONT        CREATE_MAP              CREATE_VARIABLE
CREATE_VARIABLE_FRONT    CUSTOM_ERROR            DATA_MAPPING
DELETE_ENTITY            ENTITY_EXPORT           ENTITY_IMPORT
ENTITY_REFRESH           ENTITY_SAVE             ENTITY_SAVE_DRAFT
FED_LIST_OPERATION       FLOW_ACTION             FOR
FOR_EACH                 FORM_CONVERT            LIST_OPERATION
LOCATION_CMP             MAP_OPERATION           MESSAGE_INFO
MODAL                    OPEN_LINK               OPEN_PAGE
PUBLISH_BUSINESS_EVENT   RELOAD_PAGE             RETRIEVE
RETRIEVE_ARRAY           SUB_MICROFLOW           THROW_EVENT
VALUE_HANDLE             VISIBLE
```

**前端 51 种**（`node-catalog.json`）：`ASSIGN_VALUE` / `VISIBLE` / `OPEN_PAGE` / `DIALOG` / `ATTACHMENT_UPLOAD` / `THROW_EVENT` / `RELOAD_PAGE` / `SET_DATASOURCE` 等。

### 2.2 顶层结构（铁律）

```json
{
  "endNode": {...},
  "output": null,
  "input": {"name":"_FLOW_INPUT_xxxxxx", ...},
  "sourceType": "PAGE",
  "trigger": {...},
  "nodes": [...]
}
```

**固定 6 键，多一个前端保存时丢弃。**
**没有 `flowPaths`** —— 执行顺序 = `nodes` 数组顺序。
**分支 = `conditions[].nodes` 嵌套**，`name` 只能取 `ifBranch` / `elseIfBranch` / `elseBranch`。

### 2.3 生成链

```
结构化草稿 → 归一化 → 逻辑图(logic_graph) → 构造 → 保存 → 发布 → 构建 → 运行
```

**LIVE 实证（execution_id = e2e-573258e3e6ec）：**
```
CREATE_ENTITY(5条种子) → RETRIEVE_ARRAY → FILTER(>2) → SIZE → CREATE_ENTITY(写RESULT)
→ RESULT processed_rows = 3  ✓
```

### 2.4 数据库断言

**✅ 适用。** 标准微流程内部可以读写实体，跑完可以回查数据库验证业务结果。

---

## 3. 自定义微流程（写代码）

### 3.1 没有节点

**⚠️ 这是最容易犯的错：把标准微流程的 actionType 套到自定义微流程上。**

自定义微流程**不通过 data_schema 的 nodes 描述**，而是：

```
写 Java 类
  → 实现扩展点（SPI / Abstract*）
  → 部署到应用
  → 由平台在某个时机调用
```

**⇒ 没有「节点」这个概念，没有 56 种 actionType。**

### 3.2 已知的扩展点家族（从 jar 实证）

| 扩展点 | 所在 jar | 说明 |
|---|---|---|
| `AbstractAffairRefreshService` | ctp-affair-facade | 事项刷新 |
| `AbstractAffairSearchService` | ctp-affair-facade | 事项搜索 |
| `AbstractThirdAffairService` | ctp-affair-facade | 第三方事项 |
| `AbstractAuthenticationProvider` | ctp-user-api | 认证 |
| `CtpUserSsoAuthProviderService` | ctp-user-api | SSO |
| `CtpAvoidLoginBackendProviderService` / `ClientMode` / `MiddlePage` | ctp-user-api | 免登 |
| `AbstractThirdMenuService` | ctp-user-api | 第三方菜单 |
| `AbstractLoginQrCodeService` | ctp-user-api | 登录二维码 |
| `StorageSpi` | boot-starter-file | 自定义存储 |
| `ApprovalCallBack` | udc-starter-lowcode | 单据审批回调（6 扩展点） |
| `CodeContextAware` / `TenantDataFilter` | udc | 代码生成 / 数据过滤 |
| `NacosService` | boot-starter-nacos | 配置中心 SPI |
| 27 个纯扩展位（零实现） | 多包 | 见 `statistics-registry.md` §9 |

### 3.3 ❌ 不要加数据库断言

**用户明确要求：**
> 自定义微流程不要加数据库断言，有时候你都不知道能不能访问数据库。

**原因：**
- 自定义微流程的**执行时机**由平台决定（可能是回调、可能是事件）
- 执行**上下文**不确定（可能没有 RequestContext、没有租户上下文）
- **不保证有数据源访问权限**
- 断言会因为环境差异（缺表、缺种子数据）误判失败

**⇒ 验证方式改为：**
```
① 编译通过
② 部署成功（类加载 + 注册）
③ 扩展点被调用的日志
④ 返回值的结构正确性（不查库）
```

---

## 4. 我之前犯的错（记录）

| 错 | 对 |
|---|---|
| 把 56 种 actionType 当成「微流程节点」笼统讲 | **那是标准微流程专属**，自定义微流程没有节点 |
| 用标准微流程的 E2E 流程（含数据库断言）来证明「微流程业务链路通」 | 那只证明**标准微流程**通，与自定义微流程无关 |
| 说「微流程生单/扣减」时没区分两类 | 生单规则（`CALL_DATA_FLOW`）和扣减规则（`LIST_OPERATION.SUBTRACT`）都是**标准微流程**的节点 |

---

## 5. 标准微流程的两个业务能力（用户重点关心）

### 5.1 生单规则（`CALL_DATA_FLOW`）

**关键：生单规则不是静态的，按来源实体动态查出来。**

```
① udcMetaDataSelectEntityByAppIdAppGet        选来源实体
② udcMicroflowFindDtoByEntityPost             实体 → DTO + 字段
③ udcDataFlowListManuallyMappingPost          按 sourceEntityId 查生单规则
   body: {appId, sourceEntityId}
```

**⇒ 生成器必须先拿到来源实体 id，不能凭空写规则 id。**

**节点形态：**
```json
dataFlow: {id, key, value, title, appId, appUrl, caption, name, sourceEntityId, g_l_index}
```
**⚠️ `entityId` 校验读的是 `structure.entityId`，节点顶层给了也不认。**

**两类数据来源：**
```
查询数据   按「过滤条件」查实体数据，批量执行生单规则
选择数据   引用「来源实体数据」（前序节点的实体变量）
```

### 5.2 扣减规则

**API（GraphQL）：**
```
udcDeductionRulePost / UpdatePost / DeletePost / CountPost / InitDataPost / ValidRulePost
udcDeductionMapPost / UpdatePost / DeletePost / DeleteContentPost
udcDeductionEntityListPost / EntityNotExistIdsPost
```

**节点侧两种：**

**① 集合差（`LIST_OPERATION.SUBTRACT`）**
```
selectParam    = 左列表（被减）
operationParam = 右列表（减数）
SUBTRACT 需 countAttrs 指定比较键（如 id）
```
实测：`MAP(id)全量 SUBTRACT MAP(id)>2 → 2`

⚠️ `INTERSECT` 对 DTO 列表无效，必须先 MAP 成标量列表。

**② 数值扣减（表达式）**
```json
{"arith": "SUB", "items": [{"field": "stock"}, {"field": "qty"}]}
```
⚠️ 运算符键是 `arith` 字符串，**不是** `{"op":"ADD"}`。

---

## 6. Agent 使用时的判断顺序

```
用户说「微流程」
  ↓
问：是搭页面还是写代码？
  ├─ 搭页面 → 标准微流程
  │    ├─ 查 actionType 清单（56 种）
  │    ├─ 用 data_schema 结构
  │    ├─ 可加数据库断言
  │    └─ 生单/扣减走 CALL_DATA_FLOW / LIST_OPERATION
  │
  └─ 写代码 → 自定义微流程
       ├─ 找扩展点（SPI / Abstract*）
       ├─ 写 Java 实现
       ├─ 不套节点概念
       └─ 不加数据库断言
```
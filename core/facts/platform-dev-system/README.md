# core/facts/platform-dev-system/ 索引

## 这个目录是什么

**自定义微流程开发的使用手册** —— 告诉你**代码怎么写、怎么调、怎么引用**。

**不是**生成器内部原理（那是 `core/research/` 的事，不升级）。

### 与相邻目录的分工（重要，别查错）

| 目录 | 讲什么 | 例子 |
|---|---|---|
| `standard-product/` | **平台 API 怎么调**（AppService / Dao / 扩展点） | "BpmAppService 怎么发流程" |
| `udc/` | **UDC 怎么建**（写链 / 真实 body / 节点契约） | "微流程节点怎么配" / "枚举怎么建" |
| **本目录** | **自定义微流程怎么写代码** | "改哪个类" / "怎么注入 Service" / "签名怎么来" |

**⇒ 查「节点怎么配」去 `udc/microflow/`；查「代码怎么写」来本目录。**

---

## 一、六格

| # | 文件 | 字节 | 回答什么 |
|---|---|---:|---|
| 01 | `01-custom-microflow-implement.md` | 11,177 | **改哪个类、签名怎么来、平台怎么找到你** |
| 02 | `02-udc-generated-reference.md` | 9,557 | **生成物包路径、`@Autowired` 写法、Request/Response 包装** |
| 03 | `03-io-params-and-custom-object.md` | 10,799 | **出入参决定签名、怎么取值、自定义对象怎么用** |
| **04** | **`04-generated-service-methods.md`** | **17,667** | **★ 注入之后能调哪些方法**（CRUD 全表 + 24 钩子 + AppService 40 方法） |
| **05** | **`05-calling-platform-capabilities.md`** | **18,304** | **★ 怎么调标品/平台组件**（可复制的调用片段 + 真实返回类型） |
| **06** | **`06-beforeupdate-listener-code.md`** | **14,353** | **★ 监听更新前事件改数据的可抄代码**（注解 + 类 + 改哪个字段） |

---

## 二、按问题找格

### 实现层

| 我要问 | 去哪 |
|---|---|
| 自定义微流程改哪个类？ | `01` |
| 为什么不写实现也能编译？ | `01` |
| 我实现了但没生效？ | `01` |
| 平台怎么找到我的实现？ | `01` |
| 我的方法签名该是什么？ | `03` |
| 有分页时入参是什么？ | `03` |
| 怎么从入参取值？ | `03` |

### 注入层

| 我要问 | 去哪 |
|---|---|
| UDC 生成的 Service 包在哪？ | `02` |
| Dao 叫什么名字？ | `02` |
| `getData()` 拿到的是包装体？ | `02` |
| 主子表怎么拿子表？ | `02` |
| 跨应用怎么引用？ | `02` |

### ★ 调用层（Agent 最常用）

| 我要问 | 去哪 |
|---|---|
| **注入了 `OrderService`，能调什么？** | **`04` §二** |
| **建完怎么拿 id？** | **`04` §4.1**（`createWithResult`） |
| **查一条单号匹配的记录？** | **`04` §2.2**（`selectListByCondition`） |
| **要完整单据含子表？** | **`04` §4.2**（`selectCascadeById`） |
| **更新前改数据在哪改？** | **`04` §三**（`preUpdateBatch`） |
| **`{E}Service` 有哪些钩子？** | **`04` §三**（24 个） |
| **`{E}AppService` 有哪些方法？** | **`04` §四**（40 个） |
| **怎么查组织的人？返回什么？** | **`05` §二** |
| **怎么发流程 / 提交 / 回退？** | **`05` §三** |
| **怎么在微流程里生成待办？** | **`05` §3.3** |
| **id 怎么生成？拷贝用什么？** | **`05` §五** |
| **监听更新前事件，注解怎么写？** | **`06` §一/§三**（`@EventHandler` + `@EventSubscribe`） |
| **为什么改了数据没生效？** | **`06` §五**（三条死规则） |
| **拿当前登录用户 id？** | **`06` §10.1**（`SystemVariableUtils`） |

---

## 三、核心机制（一页速记）

### 3.1 只写一个类

```
平台生成 7 个类
     └─ 只有 {App}CustomMicroFlowService 是你写的（implements 它）

链路：
  REST / GraphQL / Dubbo
    → CustomMicroFlow{Page}Controller           （平台生成）
    → {App}CustomMicroFlowAppService             （平台生成，接口）
    → Default{App}CustomMicroFlowAppServiceImpl  （平台生成）
         ├─ @Autowired(required = false) 你的实现
         ├─ 你为 null  → 抛 UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED
         └─ 你实现了   → 后处理器移除默认实现，你的生效
```

### 3.2 生成物包路径

```
{appPackagePath}.api              {E}AppService       ← facade
{appPackagePath}.dto              {E}Dto              ← facade
{appPackagePath}.appservice       {E}AppServiceImpl   ← biz
{appPackagePath}.domain.entity    {E}
{appPackagePath}.domain.service   {E}Service          ← 业务在这
{appPackagePath}.domain.dao       {appName}{E}Dao     ← ★ 带应用名前缀
{appPackagePath}.domain.event     {E}Event
{appPackagePath}.controller       {E}Controller
```

### 3.3 签名由 `hasPagination` 决定

```
hasPagination = true   → {Out} flow({Req}<{In}> request)
hasPagination = false  → {Out} flow({In} {inputName})
```

★ **已真机对照（2026-11-22）**：`String p0ManualProbe(String _FLOW_INPUT_P0IN01)` 生成物逐字，
「有出参 ⇒ 返回值不是 void」坐实；同时发现生成侧坑——`dataSchema` 必须把
`trigger.output`/`endNode.output` 镜像到顶层 `input`/`output`，否则即使面板填了出入参也生成 `void`。
细节见 `03` 的「LIVE 对照」节。

### 3.4 调用两种形态

```
{E}Service     直接传 DTO
               OrderDto r = orderService.create(dto);

{E}AppService  必须包 Request，取值两层
               SingleResponse<OrderDto> resp = orderAppService.create(SingleRequest.from(dto));
               OrderDto r = resp.getData().getContent();
```

### 3.5 分页入参（实测，容易踩）

```java
PageRequest request;
Map<String,Object> params = request.getParams();    // 条件（Map，不是 DTO）
PageInfo pageInfo         = request.getPageInfo();  // 分页
Sort sort                 = request.getSort();      // 排序

// ★ 没有 getData()。继承链 PageRequest → ListRequest → BaseRequest
```

---

## 四、证据等级

| 等级 | 含义 |
|---|---|
| `STATIC_RULE` | 模板原文，可逐字复核 |
| `VERIFIED_STATIC_BYTECODE` | CFR 反编译核实 |
| `LIVE` | 真实反射 / 真实产物 / 真实 JSON |
| `BLOCKED` | 缺资产无法推进（明确记录） |

---

## 五、已知阻塞（如实记录）

| 项 | 状态 |
|---|---|
| **完整接口渲染（含真实签名）** | **BLOCKED** —— `VirtualFullNameTransformer` 的 `<clinit>` 需真实 `AppContext` 实例；`from(null)` / `new(null)` 均 NPE；`AppContext` 是接口无构造，Proxy 注入也失败 |
| 真实工程生成一次验证 | **BLOCKED** —— 同上，需 Spring 容器 |

**⇒ 因此 01/02/03 的签名规则来自**模板原文**（STATIC_RULE）+ **DTO 字段反射**（LIVE），不是从真实渲染产物抄的。**

---

## 六、已修正的错误（保留记录）

| # | 我先前写错 | 实测真相 |
|---|---|---|
| 1 | `PageRequest.getData()` 取条件 | **没有 `getData()`**，用 `getParams()` 拿 Map |
| 2 | 「档案/表单各 1 个枚举」 | 三套 Enum JSON 结构完全一致（8+2），只是前缀不同 |
| 3 | `JsonUtils.toBean(json, Class)` | **没有 `toBean`**，用 `fromJson(json, Class)` |
| 4 | `Ids.newId()` | **没有 `newId`**，用 `gidLong()` / `gidString()` / `uuidString()` |
| 5 | `OrgCommonAppService.selectMemberInfoByIds(...)` | **方法不存在**，批量查人用 `selectMemberBySelectPeopleData` |
| 6 | 组织查人返回强类型 DTO | **返回 `Map` 或 `Long`**；只有 `selectMemberBySelectPeopleData` / `selectMemberByUserId` 给 `OrgMemberCoreDto` |
| 7 | 「BPM 更新链只发 `BeforeUpdateBatchEvent`」 | **单事件和批量事件都会发**（`EntityEventHelper.beforeEvent` case2 发两次） |
| 8 | `com.seeyon.boot.context.ContextUtil.getCurrentUserId()` | **类不存在**，用 `SystemVariableUtils.currentUserId()`（`com.seeyon.boot.starter.systemvariable.util`） |
| 9 | 「出参没有回传通道（只有 void）」 | **错**：那是 EVENT/SCHEDULE 的形态（没有消费者）。**MANUAL 有出参**——入参=方法形参，出参=方法返回值，`Default*Impl` 用 `SingleResponse.from(...)` 包装。真机产物见 `03` 的 LIVE 对照节 |

**★ 第 3~8 条是 2026-11-19 新增 04/05/06 三格时，用 `interfaces.json` 逐方法核对发现的 ——
  全部靠「方法名/类名在索引里查不到」暴露出来。这就是维护规则第 6 条的来由。**

---

## 七、来源

`core/research/platform-dev-system/` 第 24–29 轮（59 篇）。

**⚠️ `core/research/` 下的内容不得被 Agent 检索为知识 —— 本目录是唯一入口。**

---

## 八、维护规则

1. **新增格必须在本文件登记**（表格 + 「按问题找格」）
2. **只写「怎么用」，不写生成器内部原理**
3. `UNVERIFIED` / `BLOCKED` 必须标清缺什么
4. **与 `udc/` / `standard-product/` 的边界不可破坏**
5. 写错的结论修正后**保留在第六节**，不要静默删除
6. **本目录里的每个方法名都必须能在 `interfaces.json` 或模板原文里查到** —— 不许凭经验写
7. **新增格后跑一次方法名自查**：`python D:/software/hermes/cache/scratch/rebuild/verify_04_05.py`（或按同模式写一份）
# 调用形态三分（别用 REST 说微流程）

> 用户指正（2026-11-20）：「你的 body 放什么字段是啥意思，自定义微流程是 service 方法啊」
> 结论先说：**自定义微流程没有 HTTP body，它是一个 service 方法。**

同一件事在这个平台上有三种调用形态，混着讲就会像在说外行话：

| 形态 | 调用单位 | 入参长什么样 | 谁在用 |
|---|---|---|---|
| **REST** | URL + JSON | 请求体 DTO（Jackson 键名） | 设计态 CRUD、平台对外接口、前端 |
| **自定义微流程** | `serviceInterface#name` 方法 | 方法参数：`BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` | Agent 写的业务扩展、被节点或 dubbo 调用 |
| **Java 调用** | facade 接口方法 | 方法参数（`SingleRequest<X>` 等） | 客开代码、SPI 实现、远程 Dubbo |

---

## 一、自定义微流程 = 一个 service 方法

证据：`trigger-and-type-mapping.md`（CUSTOM 独有字段）

```
serviceInterface   所属接口（业务分类名，如 MigrationService）
name               方法名（编码即方法名）
trigger / endNode  只有出入参，没有节点
```

**自定义微流程（CUSTOM）：仅出入参，无节点。**
标准微流程（SERVICE）：有 56 种 actionType 节点，**没有** `serviceInterface`。

这两者不能套同一套说法：
- 标准微流程 → 说「节点、画布、runAfter、checkSchema」
- 自定义微流程 → 说「serviceInterface、方法名、出入参、paramType」

## 二、入参是哪种，由 paramType 决定

`trigger.output.paramType` / `endNode.output.paramType` 四值：

| paramType | 入参形态 | 配套字段 | Agent 要交代的 |
|---|---|---|---|
| `NONE` | 无参数 | — | — |
| `BASIC` | 基本类型 | `javaType` + `dataType` + **`desc`（9 键）** | 业务名放 `desc`，不是 `description` |
| `ENTITY_OBJECT` | 实体对象 | `entityObject`（MASTER_ENTITY） | 哪个实体 + 取哪些字段 |
| `DEFAULT_OBJECT` | 自定义对象 | `defaultObject`（dtoType=CUSTOM） | 哪个自定义对象 + 字段清单 |

★ 标量入参用 9 键 `desc`，DTO 入参才用 12 键 `description`——写反了前端显示的是
`_FLOW_INPUT_xxxxxx` 编码，不是业务名（踩过，见同文件「BASIC 入参结构规范」）。

## 三、自定义对象的字段从哪来（不是猜 DTO）

```
① udcMicroflowSearchMethodByNamePost   拿到 parameter / returnValue（含 DTO fullName + md5）
② udcMicroflowFindCustomDtoPost        dtoFullName → attributes（字段列表）
③ 参数映射里能填的就是 attributes 里的字段
```

「参数定义是后端返回的，不是前端写死的」——这是这套链的核心机制，
所以 Agent 不要自己编字段名，按 ①② 拿到的定义来填。

## 四、平台 REST 在设计态里做什么（别当成业务调用）

`/service/udc/microflow/create|update|checkSchema`、`udcMicroflow...Post` 这些 op
是**设计态**的：建/改/检查/发布微流程本身。

业务执行不是打这些接口：
- 标准微流程 → 由页面规则、事件、定时任务触发（`jobInfo/execute-onetime` 可手工触发定时流程）
- 自定义微流程 → 由平台在扩展点/节点调用时执行，**没有面向业务的 REST 触发口**

## 五、UDC 生成代码怎么引用

```
实体/服务：<实体名>AppService          ← 每个 UDC 应用都自动有一批
方法清单：udcMicroflowSearchAppServiceByAppNamePost
          （body {appId, appName, needDynamicConnector}）
          → methods[] 里就是可被微流程调用的方法
```

自定义服务节点（`CALL_APP_SERVICE`）选的就是这套服务清单，
**不是** facade 接口清单——两套命名体系不要互相套。

---

## 小结

| 说法 | 对错 |
|---|---|
| 「Agent 写自定义微流程，就是写一个 service 方法，有 serviceInterface + 方法名 + 出入参」 | ✅ |
| 「自定义微流程的 body 放什么字段」 | ❌ 没有 body，是方法参数 |
| 「标准微流程的节点怎么配」 | ✅ 但只对 SERVICE 类 |
| 「DTO 字段表能告诉 Agent 自定义传入参」 | ⚠️ 只能给 REST/Java 调用的入参；微流程入参要走 `FindCustomDtoPost` 的 attributes |
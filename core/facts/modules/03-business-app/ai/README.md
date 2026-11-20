# AI 能力（ai）

## 一句话

`com.seeyon.ai` 域的**可调用接口面**：3 个构件、237 个类、0 个 facade 接口 / 0 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `ai-biz` | biz | 132 |
| `ai-core` | 其他 | 101 |
| `ai-web` | web | 4 |
| **合计** | | **237** |

## 二、分层规律（写代码前必读）

`com.seeyon.ai` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

| 接口族 | 包 | 能力 | 什么时候用 |
|---|---|---|---|
| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |
| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |
| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |

调用顺序建议：

```
知道 id       →  XxxCoreAppService.selectXxxById        （最轻）
知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData
要写          →  XxxBaseAppService.create / update
```

## facade 层：0 个接口 / 0 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| **合计** | **0** | **0** |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 13 个领域服务，下表列**方法数最多的 13 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `AiEntityService` | 26 | 实体 · 查询×6 / 判断有×4 / 获取×4 |
| `AiFormAssistantAsyncService` | 9 | AssistantAsync · 获取×3 / 上传×1 / 处理×1 |
| `AiUserService` | 7 | 用户 · 查询×4 / 检查×2 / 获取×1 |
| `ICoMiInterfaceService` | 5 | ICoMiInterface · 获取×3 / 新建×1 / 删除×1 |
| `AiOrganizationService` | 5 | Organization · 查询×4 / 获取×1 |
| `AiAppAuthorityService` | 5 | 应用 · 新建×2 / 查询×2 / 获取×1 |
| `AiAuthorityService` | 5 | Authority · 查询×2 / 新建×1 / 修改×1 |
| `AiSummaryService` | 5 | 摘要 · 获取×3 / 新建×1 |
| `ICoMiPageInfoService` | 4 | 页面 · 新建×1 / 获取×1 / 修改×1 |
| `AiPluginInfoService` | 3 | Plugin · 获取×1 / 列出×1 / 搜索×1 |
| `AiSessionInfoService` | 2 | Session · 获取×1 / 查询×1 |
| `AiAppServiceReliableService` | 1 | 应用 · 注册×1 |
| `AiAssistantService` | 1 | Assistant · 获取×1 |

## biz 层：事件与监听

事件 0 个 · 监听器 0 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|

## web 层：Controller

共 4 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `AiAuthorityController` | 11 |
| 核心实体 CRUD | `SchemaTransformerController` | 7 |
| 核心实体 CRUD | `ICoMiPageInfoController` | 7 |
| 核心实体 CRUD | `AiFormAssistantAsyncController` | 6 |

## 这个域没有 facade（为什么）

`com.seeyon.ai` 共 237 个类，**没有 `*.api.*` / `*.appservice.*` 接口**。
它的结构是 `ai.core.infrastructure` / `ai.core.common` 这类内部实现包。

**这带来两个结论**：

1. AI 能力**不通过 AppService 对外提供**，Agent 不能按「引 facade 接口」的方式用它；
2. 若外部要用，只能走 HTTP（`ai-web` 的 Controller）或消息。

⚠️ 未取证：`ai` 是否有自己的 SPI 扩展点。需要时反编译 `ai-biz` 找 `*Provider` / `*Handler`。

另外注意：`com.seeyon.ai.core.common.JsonUtils` 是**私有副本**，
不要用它替代 `com.seeyon.boot.util.JsonUtils`（见 `U0` §3.1）。


## 落表

⚠️ **UNVERIFIED** —— `ai-biz` 的 class 常量池里没有表名字面量。

原因：该模块的 SQL/表名不在 biz 层常量池（走 Dubbo 远端 / 走配置 / 纯计算或 SDK）。
不写推测表名。

## REST 路由

> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。
> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。

**拼法**（端口/前缀按环境配置，以下为通用形）：

```
POST /service/{类级路径}/{方法级路径}
      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层
  例：POST /service/udc/runtime/deploy-normal
      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）
```

控制器 **4** 个、路由 **30** 条（来源：`ai-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-ai.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `AiAuthorityController` | `ai/authority` | 11 |
| `ICoMiPageInfoController` | `ai/comi` | 7 |
| `SchemaTransformerController` | `ai/form/assistant` | 6 |
| `AiFormAssistantAsyncController` | `ai/form/assistant/async` | 6 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `PostMapping` | `/service/ai/authority/save-authority` |
| `GetMapping` | `/service/ai/authority/select-authority` |
| `GetMapping` | `/service/ai/authority/front/select-authority` |
| `GetMapping` | `/service/ai/authority/get-current-user-info` |
| `PostMapping` | `/service/ai/authority/register-ai-app-authority` |
| `PostMapping` | `/service/ai/authority/select-ai-app-info` |
| `GetMapping` | `/service/ai/authority/get-user-ai-app-authority` |
| `GetMapping` | `/service/ai/authority/select-smart-portal-config` |
| `PostMapping` | `/service/ai/authority/save-smart-portal-config` |
| `GetMapping` | `/service/ai/authority/front/select-user-ai-authority` |
| `GetMapping` | `/service/ai/authority/front/select-smart-portal-authority` |
| `PostMapping` | `/service/ai/form/assistant/async//ocr/identify` |
| `PostMapping` | `/service/ai/form/assistant/async/edoc/identify` |
| `GetMapping` | `/service/ai/form/assistant/async//getFlow` |
| `PostMapping` | `/service/ai/form/assistant/async//upload` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 0 接口 / 0 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 13 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 0 事件 / 0 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 4 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（30 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| 落表（4 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |

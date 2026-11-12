---
name: seeyon-udc-runtime
description: Use when analyzing Seeyon UDC low-code runtime.
version: 0.1.0
author: operator-a, Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [seeyon, udc, low-code, metadata, code-generation, runtime, redis, mysql]
    related_skills: [seeyon-low-code-environment]
---

# Seeyon UDC Runtime

## When to Use

- 用户要求分析 UDC/低代码配置、生成物或运行态。
- 用户要求按版本审计 UDC jar、类、方法和跨应用调用。
- 用户要求追踪前台配置到后端、数据库、Redis 或微流程。


本 skill 只描述 UDC 低代码设计器、应用生成、运行态和客户应用扩展，不负责 SPI 生成或 SPI 契约。SPI 是独立后端可插拔体系（组织架构、单点登录、基础组件等），使用 `seeyon-v8-spi` skill 单独审计；UDC 应用本身不调用 SPI。UDC 生成的应用是独立微服务，通常包含 `web`、`core`、`ext`、`biz` 等代码分层，自定义微流程通过 `ext` 扩展代码实现。

当前客户项目只是样本、调用链证据和差异案例，不是统一 UDC 产品模板。目标是抽象跨客户、跨版本复用的 UDC Core，客户特有字段、页面、流程、权限、外部接口和业务规则归入扩展层。

## Seeyon Agent 中的组件定位

UDC 不是独立的总 Agent，而是 `Seeyon Agent` 下的一个平台组件，与 SPI、Integration、Runtime 等组件并列：

```text
Seeyon Agent
├── Core（意图、上下文、计划、执行、证据、安全策略）
├── Components
│   ├── UDC（低代码设计态、生成物、运行态）
│   ├── SPI（SSO、组织、MQ、文件、数据源等可插拔能力）
│   ├── Integration（三方接口和同步）
│   └── Runtime（Pod、Nacos、MySQL、Redis、日志）
├── Providers（Kubernetes、MySQL、Redis、Nacos、Browser、HTTP）
└── Workflows（跨组件任务编排）
```

UDC 与 SPI 在 Components 下并列，不建立默认的 UDC → SPI 调用链。客户生成应用的 `ext` 是否调用某个 SPI，必须由实际依赖和代码证据确认。

UDC 组件内部按以下层级组织：

```text
components/udc/
├── model/
├── contract/
├── version/
├── adapters/
├── analyzers/
├── planners/
├── executors/
└── evidence/
```

当前 `seeyon-udc-runtime` skill 负责 UDC 领域知识、证据规则和操作边界；未来代码工程负责 Seeyon Agent Core、Components、Providers 和 Workflows，两者不混为同一层。

## 核心链路

```text
UDC 设计态
  → 配置保存/校验
  → 元数据与版本
  → 发布/生成
  → 前端与后端生成物
  → 运行态注册
  → Redis 缓存
  → Controller/AppService/Entity
  → 业务表
```

必须区分：设计态配置、生成物、运行态元数据、物理表、Redis 缓存。

## 元数据是搭建的必然产物（锚点规则）

- 凡通过平台（后台/设计器/API）搭建 UDC 对象——应用、实体、字段、关系、页面、菜单、微流程、流程、BI、权限——平台都会同步落一份**元数据**。元数据是搭建结果的权威载体，也是唯一的验收锚点。
- 因此建模「搭建/改造」能力时以**元数据读写为主线**，绝不直改物理表；平台自身的 meta-data 接口是首选读写面（本地 5.3.517 已证实 `udc-runtime/meta-data/select-function-node-tree/{appName}`、`udc-runtime/meta-data/check-page-exists`、`udc-runtime/meta-data/select-host-and-only-page-pages` 属元数据族）。
- 判断「搭建成功」必须**回读元数据做 identity_matches**；HTTP 200、Boolean、页面不报错都不算证据。
- 运行态写操作走「设计态 REST `/udc/*`（udc-web 54 Controller） / GraphQL 动态字段（`udc-runtime/graphql-proxy/graphql`→GraphqlProxyAppServiceImpl） / 运行态 REST `/udc-runtime/*`（**udc-starter-runtime 自带 19 个 Controller，不是 udc-web 的子集**） / 元数据 `/metadata/*`（boot-starter-metadata）」四张面，追端点先问在哪一面，串面必 404。`udc-starter-*` starter 里可以有完整 Controller 层，抽端点目录时 `@RequestMapping` 扫描范围必须包含它们。
- 元数据分层不可互相顶替：设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis 缓存；改了一层不等于另一层生效。
- 元数据结构随 UDC 版本演进，**不保证跨大版本一致**：按版本族隔离建模；同一操作在 5.3 与更高版本可能元数据字段/路径不同，须各自取证，禁止用一版推断另一版。

## 设计态写接口契约恢复与检测漂移

写端点契约不靠猜。固定四级推进：**类级 `@RequestMapping` 取前缀 → DTO 用 CFR 取全字段（注意 `extends` 继承的父类字段）→ 逐条读 `BOOT_1001 xxx must not be null` 补必填 → 报错无文案时读 pod `udc-error.log` 堆栈再按 `类:行号` CFR 反编译该方法**。缺的构件先直连 Artifactory 按包路径拉（不判「本地不可得」）。**每次设计态写后必须复核一致性检测**（触发 `udc/application/do/detection` → 轮询 `do/detection-state` → GraphQL 读 `udcApplicationSearchDetectionPost`，读时必须带 `query` 字段），因为写接口会接受检测器判为 ERROR 的数据（如图节点 id 必须为真实实体 id，否则 `UDC_CE_DATA_FLOW_05005`）。方法、样例与漂移清单见 `references/metadata-storage-and-write-chain.md`。

### 路径前缀只有一种拼法：`/service/udc/<资源>`

设计态控制器的路径段是**去掉 `Udc` 前缀与 `Controller` 后缀后的资源名**，不是类名。`UdcEntityController` → `entity`，`UdcMicroflowController` → `microflow`。

```text
✅ /service/udc/entity
✅ /service/udc/microflow/create
❌ /service/udc/udc-entity        ← 把类名拼进去
❌ /service/udc/udc/entity        ← 多一层 udc
```

**404 的响应体自带 `path` 字段，直接告诉你服务端实际收到了什么**——比对它和你的预期，一次就能定位多拼/少拼的那一段，不要靠枚举候选路径试。

## 枚举与自定义对象的引用分析（删前必做）

「哪些枚举没人用，删掉」这类需求不能按名字筛。枚举分两张表且引用方式不同：

```text
udc_enum   设计态自建枚举，有 app_id          —— 本应用自己建的
ctp_enum   系统共享枚举表，也有 app_id       —— 导入应用包时成批进来的业务枚举
```

一个应用在 `ctp_enum` 里可能有几百条（实测 372 条），绝大多数是随包导入的**业务枚举**（考核类型、变更类型、税率范围…），不是垃圾。

实体属性引用枚举的方式是：`data_type='CTPENUM'` + `relation_code`（枚举 code）+ `relation_entity`（枚举 id）+ `relation_entity_name`。按这个查引用，不要猜列名（`parent_enum_attr_id` 不是引用键）。

⇒ 删除清单必须同时满两条件才给：①已无实体属性引用；②已无页面/规则/微流程引用。只查第一项就报「大部分可删」是危险的——导入包里的枚举常被页面下拉和规则表达式用着，而这两处不在实体属性表里。`ctp_enum.name` 可能是 `{"zh_CN":"xxx"}` JSON 串，展示前要解码。`is_delete=1` 的是已标记删除，页面不可见，物理清理无收益，不要顺手删。

## 证据与版本

- `FACT`：用户源码/反编译 class、前端 Network、Nacos GET、MySQL 回读、Redis 只读结果、Pod 日志原文。
- `OBSERVATION`：一次真实运行现象、客户项目样例或文档描述。
- `HYPOTHESIS`：尚未直接验证的版本差异或机制推断。

版本最小证据单元：`artifact + version + sha256`。不能用单个 5.3 小版本推断全部 5.3，更不能用一个客户项目推断所有客户。

## 研究顺序

1. 读取低代码操作文档，建立设计态动作清单。
2. 选择最小闭环：一个应用、实体、字段、页面、微流程和一次数据新增。
3. 记录前端实际请求：URL、HTTP 方法、请求体、响应、页面路由和发布动作。
4. 反查后端 Controller、Service、生成器和运行态服务。
5. 对比 MySQL 设计态/运行态/业务表前后变化。
6. 只读检查 Redis key pattern、类型、TTL、缓存失效和重载日志。
7. 下载并按版本索引 UDC jar，针对每个类审计职责、调用者、被调用者、表、缓存和跨应用交互。
8. 与第二个版本或第二个项目对比，只有稳定部分才能上提为 UDC Core。

## 统一模型与客户扩展

统一模型：

```text
Application / Entity / Field / Relation / Page / Widget
MicroFlow / Node / DataSource / Permission / PublishVersion
```

客户扩展：

```text
CustomerExtension / BusinessRule / ExternalConnector
SpiAdapter / FieldMapping / PageTemplate
```

统一 Core 不直接包含客户应用 ID、客户表名、客户字段名和客户接口地址。

## 客户应用机制审计

溯源「某应用某机制是配置表还是写死」（邮件、催办、自动下发等）时，按 `references/app-mechanism-audit.md` 的顺序取证：本地代码仓 → 元数据导出（注意只含 FRONTEND 微流程、dataSchema 双重编码需二次 loads）→ Nacos 运行配置 → 经授权的库表数据。**无本地代码仓时，运行 pod 的扩展 jar（`<appId>-ext-*.jar` 的 `extend/controller/*`）是等价权威产物**——base64 单行命令批量导出 class + 本地 CFR 反编译，再用常量池中文关键词定位承载类，步骤见该 reference 的「手写扩展代码的定位」节。

「为某业务动作补邮件/待办提醒」先按入口层分流（页面微流程 / 手写扩展 Controller / 事件监听），选错整轮返工；**外部系统主动调接口创建单据的场景入口在手写 Controller，不在页面微流程**。分发表与双环境提醒口径见同一 reference 的「通知类需求先定入口层」节。

排查「设计态写了但运行态查不到」「实体/字段数据落哪层」时，按 `references/metadata-storage-and-write-chain.md` 的三层模型（MySQL 设计态权威源 → Redis 运行态缓存 → OSS 发布镜像）定位；设计态写后未发布查不到运行态元数据是预期行为。

## 前端校验规则与报错文案的溯源（用户问「为什么提示 X」）

「页面为什么提示这句、什么条件下弹」不要从后端或业务表猜。前端校验有它自己的落点，按顺序取：

1. **先拿报错文案原文。** 用报错原文（不是用户口语转述）全仓搜索，命中的是**微流程**而不是页面：
   `grep -rl "<报错原文>"` 在 `frontend/pc/src/microflows/`。文案是 i18n 键，形如
   `{k}":"<app>.microflow.FRONTEND.<微流程名>.<节点类型>.<节点ID>.content","d":"<报错原文>"}`。
   节点类型决定机制：`FRONT_CUSTOM_ERROR` / `MESSAGE_INFO` = 前端自定义校验；命名规律是
   `FRONT_CUSTOM_ERROR_<随机6字>`、`MESSAGE_INFO_<随机6字>`，同一段逻辑会在**多个微流程里复制**。
2. **把条件读出来。** 校验节点前面一定有一个 `CONDITION_*` 分支，条件是一份 JSON
   （`{"__EXPRESSION__":...}`），里面 `VariableIdentifier.name` 写的是「数据路径 + 组件 id」，
   形如 `FORM kuozhanxinxiDto.fukuanbiliheji udcForm_rHXS_... inputNumber_...`。
   中段（`Dto.字段名`）是实体字段，尾段（`udcForm_*`/`inputNumber_*`）是页面组件 id。
   跟该节点相邻的 `log?.addLog({... input: '…当前条件为【…】'})` 里有平台自己翻译好的**中文条件描述**，
   直接引用它比手翻 JSON 可靠。
3. **字段 → 物理列 + 列注释用 DB 反查**（不要按业务名猜表）：
   `information_schema.columns WHERE column_name='<字段>'`，会同时命中业务表、`bak_*` 备份表、
   多个历史副本——用 `TABLE_NAME` + `COLUMN_COMMENT`（如「付款比例合计」）确认。
4. **一个文案命中多个微流程时，三处都要改。** 同一判定常被复制到 2-4 个微流程（例如同一句「必须等于100%」
   出现于两个不同前缀的微流程，另一处文案多一个「所有行」字）。先列出全部命中再开工。
5. **枚举比较是硬编码项 id，而枚举项常有重 id。** 条件里 `{"type":"Literal","value":"-2235029774768033675","dataType":"CTPENUM"}`
   这种就是 `ctp_enum_item.id`。**同一 `enum_code` 下同名项可以存在两枚不同 id**（如「其他」两枚），
   微流程只比其中一枚 → 页面选中另一枚就漏判/误判。碰到枚举类校验，先
   `SELECT id,name,item_value,order_no,enable FROM ctp_enum_item WHERE enum_code='<码>' AND is_delete=0`
   看有没有成对的重复项（含 `enable=0` 的历史项）。

配套查询：生成单据的表实体（如 `htmbzxsc_*`）与其明细表（`mubanfuku_*`）是两套表；
页面行级明细的字段（`fukuanbili1` 等）在明细表上，表头合计字段（`fukuanbiliheji`）在单据表上。
定位「合计为什么对不上」时先把这两个层次分开。

## 生成物与路由

低代码应用 HTTP 入口通常为：

```text
{APP_BASE_URL}/service/{applicationId}/{业务路径}
```

路由必须从 Controller 注解或实际 Network 请求确认。记录 `@RestApi`、`@RequestMapping`、`@PostMapping/@GetMapping`、Controller FQCN、AppService FQCN、method ID 和请求 DTO。不能根据中文业务名称猜 URL。

## Jar 审计

jar 来源：Artifactory/组件库、本地 Maven 仓库、工程 target/lib、运行镜像或挂载目录。

先建立 artifact/version/sha256/class/package 索引，再 targeted decompile。涉及 UDC 的 jar 需要逐类审计，但分批保存结果，避免一次把完整反编译源码塞进上下文。

每个类至少记录：

```yaml
artifact:
version:
sha256:
fqn:
kind:
annotations:
constructors:
methods:
fields:
callers:
callees:
database_tables:
redis_patterns:
external_services:
cross_application_calls:
side_effects:
compatibility:
evidence:
```

重点包：`metadata`、`entity`、`field`、`page`、`widget`、`microflow`、`runtime`、`generator`、`publish`、`datasource`、`cache`、`redis`、`application`。

## 前端、数据库与 Redis

前端用于发现设计态契约：页面路由、保存/发布请求、字段组件模型、权限请求、数据源请求和生成物对应关系。优先使用浏览器 Network/CDP 或前端静态资源分析。

数据库先盘点表名、注释、字段、索引、关联 ID 和数据量，再关联应用、实体、页面、微流程和版本。不能把直接 INSERT 当作完整 UDC 配置保存，除非已证明校验、版本、关联、事件、缓存和发布副作用全部覆盖。

Redis 只读记录 key pattern、类型、TTL、大小、序列化形式、关联应用/实体/版本和写入/失效时机。不保存密码、Token 或完整敏感缓存内容。

## 环境与运行态 Agent

应用地址由 `seeyon-low-code-environment` 的配置层提供（`config/environments.yaml` 的 `app` 段 + `.env`），本 skill 不写死客户地址：

```text
SEEYON_ENV                 选择环境（test2 / uat …）
SEEYON_APP_BASE_URL        应用 HTTP 基础地址
SEEYON_APP_IP              应用/节点 IP
SEEYON_APP_ID              低代码应用 ID
SEEYON_APP_SERVICE_PREFIX  默认 /service
```

读取方式：`python <seeyon-low-code-environment>/scripts/conn.py show --sub=app`，或 `from env import load_env`。

最终拆成：

```text
seeyon-udc-core
seeyon-udc-runtime-agent
```

Agent 默认只读；数据库、Redis、Nacos、发布、清缓存、重启和运行态元数据修改必须确认并回读。

## 报告格式

```text
结论：PASS / FAIL / BLOCKED / UNVERIFIED
环境：test2|uat，namespace，应用
设计态：前台动作和请求
生成物：前端/后端文件与版本
运行态：元数据、路由、缓存
调用链：Controller → Service → Runtime → DB/Redis
版本：artifact/version/sha256 与差异
客户差异：Core / Extension
证据：FACT / OBSERVATION / HYPOTHESIS
```

## 沙箱（app-sandbox）构建/部署链

「设计器点构建/发布后发生了什么」「构建卡在哪」「应用库怎么清」走沙箱链，按 `references/sandbox-build-deploy-chain.md` 取证。要点：sandbox pod 是 UDC 应用的构建+部署执行器（app-sandbox，不是业务应用，前端无页面）；入队靠 Redis `{env}:sandbox:build:{queue|hash|status}`，消费方 BuildTask 回调 `SandboxClientAppService.taskCallBack`；部署态在 `{env}:udc:app:test:deploy:run:{sandboxId}` 与 `{env}:udc:app:sandbox:deploy-info:{appName}`。udc-web 侧三个控制器是查询/触发面：`udc/sandbox`（select、build-info、delta-build-info、release-build-info）、`udc/runtime`（deploy-normal/deploy-form/stop/ferry/search-deploy-status）、`udc/deployment`（restart、app-ready-state、app-online(-new)、app-delta-deploy）。构建进度/日志直接 GET `build-info/{appId}` 拿全量流水日志，不要上 pod 翻文件；查不到应用先确认应用是否已删（报 UDC_APP_0001）。

## Jar 审计提效（可选）

多 jar 反编译可按模块拆给子代理并行，但 delegation 的 provider+model 必须是真实存在且额度足够的组合；免费额度通道并发 3 个子代理会 429 全灭，此时直接自己 CFR 反编译更快（单类秒级）。

## 标准节点微流程 ≠ 自定义微流程（建错类型的代价极高）

**用户明确要求过多次：建「微流程」默认指标准节点微流程，不是自定义微流程。**

```text
标准节点微流程  create 传 type="SERVICE"  → 落库 type=0 + serviceInterface='CustomMicroFlowAppService'
自定义微流程    create 传 type="CUSTOM"   → 落库 type=3，节点树/生成物/入口全不同
```

`create` REST 收字符串枚举，DB 存数字，必须按此映射核对落库结果：

| 字段 | REST 字符串 | DB 数字 |
|---|---|---|
| `type` | `SERVICE` / `FRONTEND` / `ENTITY_RULE` / `CUSTOM` / `FUNCTION` | 0 / 1 / 2 / 3 / 4 |
| `triggerType` | `BUSINESS_EVENT` / `SCHEDULE` / `MANUAL` / `FRONTEND_PARAM` | 0 / 1 / 2 / 3 |
| `state` | `DRAFT` / `RELEASE` | 10 / 20 |

⇒ **create 之后必须 DB 回读 `type` 与 `state`**。REST 返回 `BOOT_0000` 且落库成功，不代表类型对；`state` 传 `DRAFT` 也可能落成 `RELEASE`。回读不符就删掉重建，不要靠 update 改 type。

## 删微流程不会清理生成物（会直接把构建搞挂）

删除引用了某实体的微流程后，平台**不会**同步清理该实体已生成的 Java 源码。下次构建报：

```text
XxxService.java:[169,144] 程序包 com.seeyon.<app>.domain.message.<实体小写> 不存在
```

机制：`domain.message.<entity>` 包只在「该实体仍有微流程引用」时才生成；实体自身的 `XxxService.java` 则无条件生成并 import 该包 → 删除微流程即制造悬空 import。

⇒ 清理实验微流程前先查实体依赖；若某实体不再被任何微流程引用，要么连实体一起删（先做全表引用扫描），要么保留一条引用它的流程。**不要先删流程再等着看构建**——构建失败时错误信息只暴露包名，不暴露是哪次删除导致的。

## 生成前置校验必须在本地做（checkSchema 只拦一半）

`POST /udc/microflow/checkSchema` 对同一 DTO 注入语义类非法内容（错的 `actionType`、错的 `conditions[].operator.name`、错的 `trigger.paramType`、`nodes=[]` 空流程）全部返回 `check:true, errors:0`。它不校验节点类型值域、操作符、参数类型，也不拦空流程。

**但它会拦「必填字段缺失」和「形状/类型不符」**——实测这几类返回 `check:false`：根 `output.id` 为 null（应为 `output=null` 而非空对象）、`RETRIEVE_ARRAY.structure` 缺失、`fetchType` 不在枚举值域、`size` 传字符串而非整数。

⇒ 两条规则同时成立：

1. **生成前置校验必须在本地做**——语义值域类错误只有本地约束模型能拦，`checkSchema` 全部放行。
2. **`check:false` 必须立即中止，禁止继续 `update`**——把 `check:false` 当「可能是误报」跳过，等于把必炸的 schema 写进库，而错误会在几十分钟后的构建期才浮现，届时已难归因。判定写法是取 `data.content.check is True`，不是只看 HTTP 200。

⇒ **凡是在生成期才炸或在运行期静默错的配置，必须在本地约束模型前置拦截**；把 `checkSchema` 通过当作「配置正确」是错的，把它当生成前的最后一道闸更是错的。写链（create→update→回读）能成功落库，只证明「平台接受了这个形状」，不证明「这个形状是对的」。

已知必须本地拦的两类，机制与字段表见 `references/microflow-generation-prerequisites.md`：

1. **MESSAGE 监听分支要求根 `input` 完整**（含 `javaType` 与 `name`）。缺任一项，构建期在 `BusinessEventListener.java.ftl` 抛 Freemarker `InvalidReferenceException`——`?then` 惰性求值使「input 为 null」和「input 缺 javaType」两种形态都必炸，只查前者会漏。
2. **`CALL_APP_SERVICE` 节点的调用配置必须可定位唯一服务**。该类节点在本地 `NODE_REQUIRED_FIELDS` 里是空元组（等于不校验），而契约表早已写全规则——`selectMethod.fullName` 必填且为 `implClass` 前缀、`parameter.type` / `returnValue.type` 在值域内、`attrs[].attrType.id` 前缀等于 `parameter.item.itemType`。调错方法或绑错入参类型，平台不报错，运行期才错。

写这两个校验器时保持同一纪律：`md5` 禁等值比对（同一 `fullName` 可对应多个 md5，容器条可缺省该键），标 UNVERIFIED 的字段不做断言，只把已有硬规则落成代码。

**校验器自身必须不崩——一次 TypeError 会让整条流程的所有其他错误一起消失。** 真实数据里 `convertType`、`mappingMode`、`itemType` 这类「枚举字段」的实际形态可能是 dict 而非字符串，`ct not in FROZENSET` 对 dict 直接抛 `TypeError: unhashable type: 'dict'`，解析在此中断，调用方看到的是一条「解析异常」而不是该流程真正的 N 个字段错误。批量校验时这会伪装成「只有 2 条有问题」，实际那 2 条的全部问题都被吞掉了。规则：**任何集合成员判定前先 `isinstance(x, str)`**；形态不符时记 warning（说明「dict 形态，未参与值域判定」），不要判硬错也不要抛。同理，`validate_node_fields` 之类返回 `list[str]` 的函数若在某些分支返回裸 `str`，调用方 `errs.extend(r)` 会按字符逐个展开成 `['解','析','异','常']` —— 统一 `if isinstance(r, str): r = [r]`。批量校验脚本还要在每个流程外层 try/except 并记录 `type(exc).__name__`，否则一个流程的异常会中断整轮扫描。

## 禁止事项

不把 SPI skill 内容混入 UDC skill；不把单客户代码直接抽象成平台机制；不只改物理表就声称元数据已生效；不只看 HTTP 200 或 Boolean 就声称写入成功；不直接修改 UDC 运行态数据库；不把相邻版本类和方法当作目标版本事实；不在索引中写入密码、Token、私钥和完整 kubeconfig。

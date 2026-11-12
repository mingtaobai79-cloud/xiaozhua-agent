---
name: v8-framework-development
description: 按 V8 官方客开通路编写或修改代码。适用于用户要求实现、修改或生成客开代码；不要用于只出方案文档、纯知识问答或纯源码定位。
---

# V8 通用客开开发编排

这个 Skill 用于“要设计、实现、修改或生成 V8 客开代码”的任务。它不是单一组织同步 Skill：先识别需求属于配置、扩展、接口调用、新服务、SPI、集成中的哪一种，再读取对应资料和源码证据，最后形成可测试的实现闭环。

## 0. 先建立边界与证据

1. 读取当前任务说明、产品版本、应用编码、前后端目录和构建文件；确认改动属于 UDC、标品扩展、独立服务、SPI、CIP、移动端还是混合场景。
2. 首个工作台调用使用 `get_platform_context`，确认已登记的只读 Markdown 资料源和可读源码目录。该调用由工作台自动统计，不要另造身份或事件记录。
3. 先读取知识库入口 `v8客开知识库/00-客开导航.md`，再按下面路由读取 2–5 组资料：架构/形态、业务领域、接口或 DTO、集成边界、测试/质量。
4. 每个 V8 内部结论必须带资料路径和引用 ID；源码结论还要带 `代码源别名:相对路径#Lx-Ly`（例如 `v8:backend/foo/Bar.java#L10-L22`）。源码目录按请求时读取，不承诺 Git 快照。资料不足时写“待验证”，不得用通用经验补齐 V8 接口。
5. 不要直接改基线 `backend/` 或 `frontend/apps/` 业务源码来覆盖产品；优先使用官方扩展工程、Facade、UDC、插槽或 SPI。

当现有知识库资料不足以支撑实现时，必须补充源码取证：先读取源码导航地图确定代码源和候选目录，再按“定义 → 调用方 → 测试 → 有限上下文”调用源码 MCP。源码证据只能证明当前挂载版本的实现，不得把路径推断当成契约；若未命中或代码源未登记，标记“源码未核实”，并把待确认项带入方案和测试。

## 1. 开发通路识别与决策矩阵

| 先判断的需求 | 正确通路 | 主要产物 | 典型场景 |
|---|---|---|---|
| 页面、表单、列表、流程由设计器配置 | 配置型客开（UDC 设计器、门户、参数、迁移） | UDC 应用/页面/微流程配置 | 快速交付业务表单、列表、审批和门户栏目 |
| 需要整页手写交互 | UDC 手写页面 | `customPage.tsx`，PC/Mobile 扩展工程 | 复杂交互、特殊布局、无法由设计器表达的页面 |
| 需要拖拽复用的 UI | UDC 控件 | `sy.config.json` + design/schema/runtime 模块 | 可配置组件、行业控件、重复使用的输入/展示控件 |
| 需要在设计器里配置动作 | UDC 行为 | `actions` + `runtime.ts`/`schema.ts` | 保存后动作、提交前后动作、调用接口或提示 |
| 标品已有挂载点 | 命名插槽 / `SlotsExtends` | 自定义库、插槽组件或劫持注册 | 在门户、列表、按钮等预留位置插入或增强 UI |
| 平台页面小范围改造 | 平台 HTML/JS/CSS/JSSDK 扩展 | `extend-html` 或前端扩展包 | 隐藏字段、样式修正、事件拦截、脚本注入 |
| 跨服务读取/写入业务能力 | 普通 Dubbo facade | ext 服务或客开服务，`@DubboReference` | 组织、BPM、事项、用户、门户、UDC 等能力调用 |
| 要替换平台扩展点实现 | SPI / Super SPI | 独立 SPI JAR 或扩展工程 | SSO、接口鉴权、移动插件、短信/存储等厂商通道 |
| 对接第三方系统 | CIP 集成 / OpenAPI | 连接器、同步中间表、Provider、OpenAPI | 组织同步、待办/消息、SSO、能力通道 |
| 需要独立领域服务 | Java / Spring Cloud 服务 | `facade` + `biz` + `web`/assemble | 长流程业务、独立事务、对外 REST/OpenAPI |
| PC 与移动端同时交付 | 混合客开 | PC/Mobile 页面或组件 + 后端契约 | 同一业务在 Web、M5/H5 双终端使用 |

不得把 UDC 页面需求默认判定为 React 手写；先确认设计器配置、控件/行为还是整页自定义。查询接口 ≠ 写入接口，先确认读写语义、权限和幂等策略。

## 2. 前端客开路由

先读 `frontend/README.md`、`frontend/01-architecture.md`、`frontend/02-getting-started.md`、`frontend/03-extension-patterns.md`，再按场景补充 `04-global-api.md`、`05-reusable-packages.md`、`07-url-to-source.md`、`08-path-index.md`。

### 2.1 UDC 与设计器

- **UDC 自定义页面**：工程是独立前端仓库（`<gitlab>/<组>/frontend/<appId>.git`），内含 `pc/` 与 `mobile/` 两端；**页面标识是目录名、不是文件名** —— `pc/src/pages/<页面标识>/customPage.tsx`（`customPage.tsx` 固定不变）。调试：`webpack-overrides-custom.js` 的 `hostName` 指向测试环境 → `yarn start`（`syf dev-udc-custom`）→ `localhost:3000/main/portal/<appId>/<页面标识>`；构建：`yarn build`（`syf build-udc-custom`）。工程结构、registry/版本、三方库 `third_modules` + `syf build-multiple-bundless-module`、请求与响应约定、流式下载与定时轮询写法：`references/udc-custom-page.md`。缺少前端仓库时要向用户要地址或平台导出的代码包，不要假装能交付页面。
- **UDC 控件**：在 `sy.config.json` 声明 `controls`，拆成 `designModule`、`schemaModule`、`runtimeModule`；用 bundless 本地调试和构建。适合设计器拖拽复用，不适合只存在于一个页面的一次性代码。
- **UDC 行为**：在 `sy.config.json` 声明 `actions`，客开 key 使用 `KK_` 前缀，`src/actions/runtime.ts` 与 `schema.ts` 必须存在。适合把保存、提交、校验和接口调用做成设计器可选动作。
- **UDC 微流程**：优先在设计器定义节点/接口，再构建发布，最后在后端 ext 实现；不要在没有生成契约前猜接口。

### 2.2 标品页面和公共能力扩展

- 平台页面 HTML/JS/CSS/JSSDK 扩展：用于小范围覆盖和注入，不要复制整个标品页面。
- 命名插槽 `extendSlots`：只使用资料中确认的槽名；无槽时组件应可安全降级。
- `SlotsExtends`：用于已有组件事件、数据或 UI 的受控劫持，先确认挂载点和注册契约。
- 门户栏目、门户元素、菜单扩展：优先走 portal/portal-portlet 资料和官方入口。
- 公共接口优先从 `@seeyon/global` 调用 `ajax`、`i18n`、`OpenWindow`、事件总线、权限、租户和远程模块加载；PC 使用 `@seeyon/ui`，移动端使用 `@seeyon/mui`。
- 选人、流程、UDC、门户等复用 `@seeyon/biz-*` / `@seeyon/mbiz-*`；第三方库按脚手架要求放入 `third_modules` 并 bundless，避免重复打包 React。

### 2.3 移动与第三方页面

- M5 / 移动端：读取 M5/H5 集成资料，使用 `nativeSdk` / `jsSdk` 和移动组件；确认 PC/Mobile 差异后再复用页面逻辑。
- 外部系统嵌入：使用 iframe 消息 SDK 或门户动态三方栏目，明确登录、跨域、销毁和失败回退。
- 线上 URL 定位源码：先按 `07-url-to-source.md` / `08-path-index.md` 判断基线 app、UDC 动态应用或三方站点。

## 3. 后端客开路由

先读 `backend/README.md`、`backend/01-architecture.md`、`backend/02-getting-started.md`，再按业务读取 `03-organization.md`、`04-05-06`（BPM）、`07-affair.md`、`08-integration.md`、`09-other-modules.md`、`10-utils-conventions.md`、`11-tenant.md`、`13-udc-ext-development.md` 和对应规范。

### 3.1 普通 Java / Spring 服务与 Facade

- 模块边界通常是 `xxx-facade`（接口、DTO、枚举、SPI 契约）→ `xxx-biz`（`@DubboService` 实现）→ `xxx-web`（REST）→ assemble（打包）。
- 客开默认依赖现场版本的 facade，在 ext 或独立服务中用 `@DubboReference` 调用；入参使用 `SingleRequest` / `ListRequest` / `PageRequest`，出参先判断 `resp.success()` 再取 `getData().getContent()`。
- 组织、BPM、事项、用户、门户、UDC 等先找对应 facade；不要直接调用内部 `*InnerAppService`，也不要注入具体 `*AppServiceImpl`。
- 普通 Dubbo facade 适合已有平台能力的调用；新业务才考虑新增 facade/服务。写操作要确认当前用户、租户、事务、幂等、失败补偿和权限。

### 3.2 组织、BPM、事项与 UDC 后端

- 组织对象先分清 `OrgUnit`（单位/部门由 `UnitTypeEnum` 区分）、`OrgMember`、岗位、职务、职级、任职和角色；人员停用通常不是物理删除。
- `*BaseAppService` 面向 UDC/页面维护，`*CoreAppService` 主要只读，`*SyncAppService` 面向三方同步 upsert/停用。组织同步优先查 `OrgUnitSyncAppService`、`OrgMemberSyncAppService` 等契约。
- BPM 操作走 `BpmAppService`；节点跳过走 `BpmSuperviseAppService.skip`；事项 `Affair` 与流程工作项不能只改一边。
- UDC 后端手写只进 `autocode-extend/backend/{应用编码}.git` 的 `${appId}-ext`，微流程先设计态定义并构建发布，再在 `extend.appservice` 实现。
- 需要跨 UDC 应用且没有编译依赖时才使用泛化调用；能直接依赖 facade 时不要用泛化调用。
- **自定义 `@RestController` 的路径前缀必须带应用编码**（`/<appId>/extend/...`）。不带前缀的路径平台不会注册进本应用路由表，接口写对了也 404/被拦；`@RequestMapping` 与代码里回给前端的 URL 要同源（一个常量两处引用），并加一条「前缀含 appId」的正向断言锁死。
- **自建 REST 与页面联调先排三个「假故障」**，它们都不在业务代码里：
  ① **405 Method Not Allowed** —— 页面走 `ajax.post`，后端只声明了 `@GetMapping`；查询端点一律用 `@RequestMapping(method = {GET, POST})`。
  ② **404 且 `Content-Type: application/xml`、响应头带 `X-Oss-*`** —— 原生 `fetch` 没补 `/service` 网关前缀（ajax 会自动补，fetch 不会）；真实对外路径是 `/service/<appId>/...`，用 `SERVICE_BASE = '/service' + BASE` 派生。
  ③ **200 但 `{"status":2,"code":"BOOT_1006","data":{"content":{"redirectUrl":"...sso..."}}}`** —— 未登录被 SSO 网关拦；浏览器里能拿到 405/404 说明当时是登录态、请求确实到了后端，用 curl 复现时要先带登录 cookie。
  看到这三个特征不要先查业务逻辑。
- **测试期优先改前端适配，不要卡在后端发版上。** 后端只映射 GET 而页面发 POST 时，改前端用 `ajax.get(url, params)` 旧后端立刻能通，后端再补双方法支持；两条路都留。因为「等一个含修复的镜像」把一次联调拖成一整轮发布，是本类任务最常见的浪费。
- **UI 不得手写原生控件。** `@seeyon/ui` 就是 antd 封装（Card/Statistic/Table/Progress/Tag/Modal/Space/Select/Input/Empty/Tooltip/Button 齐全，另有 `udc-table`/`udc-data-grid`/`udc-panel`/`udc-tool-bar` 等标品专用件），用户会把自绘控件直接评价为「好丑」。不确定组件 props 就读 `node_modules/@seeyon/ui/es/components/<x>/index.d.ts`（多数组件复用 antd 类型），不要退回原生元素。
- **UDC 微流程 type=3（自定义服务）能用之前先做「链路三查」**，任一不成立就不要去补 schema、也不要把「后端方法已写好」当成按钮可用：① `udc_microflow_info.json_schema` 是否为 `{"nodes":[],"lines":[]}` 空壳；② `udc_page_schema.page_schema` 里是否零引用该微流程（`LIKE '%<微流程 name>%'`）；③ 平台生成的 `api/microflow/<X>Service`（**不进 git、构建时按微流程生成**）方法清单里有没有对应方法。断链时的最小成本解是开 `@RestController` 或独立门面 Bean，不要手工造生成接口的 DTO。
- **给微流程「调用服务」节点的门面，入出参一律 `String`。** 平台按微流程定义生成的 DTO/接口在构建前不存在，ext 里写死 `SingleRequest<XxxDto>` 会本地绿、构建红；全部 `public String xxx(String ...)`，返回值当提示信息出参，空入参与依赖未注入时回友好文案而不是抛异常。这类方法要 public、非 static、Bean 实例方法。
- **流式响应（大文件导出）与进度轮询不能塞进 UDC 页面规则微流程**：页面规则是同步执行、没有轮询/长任务能力，只能落到自定义页面（`references/udc-custom-page.md`：原生 `fetch` + `blob` 触发下载、`setInterval` 轮询并在卸载时清除）。页面里的请求照抄工程既有写法 `ajax.post('/<appId>/...')`；后端若自建 REST，响应包成 `{status:0,message,data:{content}}` 或 `{success:true,content}`，一个页面只用一种。

### 3.3 SPI / Super SPI

SPI / Super SPI 是替换或接入平台扩展点的独立契约，不等于普通 Java 服务，也不等于直接修改基线。先确认接口、注册方式和部署入口，再决定是否实现：

- SSO、统一身份认证、免登、接口鉴权、移动插件等 `cip-connector-api` / 用户 SPI；
- 短信、OCR、在线文档、电子签章、文件存储等 `ProviderService` 能力通道；
- BPM/事项等 facade 内声明的业务 SPI / Super SPI。

实现通常打独立 JAR，使用 `spring.factories` 或现场约定注册；密钥和地址走应用参数/环境配置，日志脱敏，版本与现场 5.30 对齐。

### 3.4 CIP 集成与异步扩展

- 组织同步有两条通路：已有可靠数据时直接调组织 `*SyncAppService`；按 CIP 标准接入时使用 `MiddleTableOperationAppService` 中间表（`saveUnit`、`saveMember`、`fullFinish`、`delete`、立即同步等）。不要直接写组织内部表。
- 三方待办/消息使用 CIP connector/manager 的 facade；撤销、终止、重试要使用对应契约，避免三方状态悬挂。
- SSO/连接器执行走 `SsoExecutorAppService`、`LinkerAppService` 或对应 SPI；能力通道实现 `ProviderService` 子接口。
- 事件监听、MQ、线程池适合异步通知和解耦；必须考虑事务提交后发送、重复消费、顺序、重试、幂等和资源释放，不要用裸线程替代平台机制。

### 3.5 平台基础能力

按需读取租户、缓存、DynamicSQL、MyBatis、ES、文件、日志、Nacos、数据迁移和安全规范。跨租户代码使用 `TenantChangeFunction` 并在结束后恢复；自定义 SQL 处理租户条件和注入风险；外部地址、Token、密码不写死。

## 4. 混合客开闭环

当需求同时涉及前后端时，按以下顺序组织：

1. **需求拆分**：页面/交互、数据模型、接口、权限、异步事件、第三方边界分别列出。
2. **资料取证**：前端读取 UDC/扩展形态和公共 API；后端读取 facade、DTO、状态和集成文档；对同一个业务对象使用同一版本证据。
3. **契约确认**：先确定请求/响应、错误码、权限、租户、幂等和状态流转，再写前端调用和后端实现。
4. **实现**：前端复用平台包和扩展点；后端通过 facade/ext/SPI/CIP 实现，禁止越过边界直接改基线或数据库。
5. **验证**：运行单元、接口、页面、SPI/MCP 契约和失败路径测试；必要时用已登记源码目录做定义 → 调用 → 测试核验。
6. **交付**：说明已证实事实、通用工程建议、待验证项、引用 ID、部署步骤和回滚方式。

## 5. MCP 取证与检索规则

## 工具怎么选

不要把源码检索合成一个接口。按问题类型选工具：

1. 查文档、客开怎么做：`get_development_context` / `search_v8_knowledge`
2. 口语找公开接口，例如「同步部门有哪些增删改接口」：`resolve_v8_api`（向量命中后自动 Zoekt 定位）。只要签名时才用 `search_v8_public_apis`
3. 已知类名、方法名、要文件位置：`search_v8_code` / `find_v8_symbol`（Zoekt 全仓文本）
4. 已知类名要读类体：`get_v8_type_source`
5. 核对调用和测试：`get_v8_usage_examples` / `get_v8_code_context`
6. 按路径读片段：`read_v8_code`，带行号范围，不要整仓灌进对话

`search_v8_public_apis` 只覆盖 facade/api/services 的公开签名，不能替代 Zoekt，也不是知识库。


- 首个调用：`get_platform_context`。
- 知识检索：工作台已混合全文和向量，仍只传 `query`。先用 `get_development_context` 聚合资料、相似实现、约束和测试建议；再用 `search_v8_knowledge` 查接口名、类名、包名和精确术语。不要传 `module`，禁止把「后端开发 / 前端开发 / UDC / Java / React / 架构/开发方式」当作模块名。
- 同义词和中英文交叉检索仍然要做；“组织架构同步”至少继续查“组织同步、部门、人员、OrgUnit、OrgMember、Sync”。向量近义命中不能替代精确词，不得把单次检索零命中当作资料不存在。
- 结果必须保留来源路径、版本、模块、更新时间和引用 ID；零结果只能说明当前证据不足，不得编造接口。
- 命中资料时必须提供知识引用：最终回答增加“知识引用”小节，并将关键结论关联到 MCP 返回的 `citation_id`、路径、版本和片段。
- 未登记代码目录、工具拒绝或资料不足时，只能基于 Markdown 证据并明确“源码未核实”。不得上传完整项目、凭据、原始日志或完整本地 Diff。

源码导航优先使用 `v8-source-navigation`。口语找公开接口先 `search_v8_public_apis`；已知类名/方法名再 `search_v8_code` / `find_v8_symbol`（默认不要传 `path`，Zoekt 会全仓检索并把定义排前）。只有结果明显串模块时才加 `path="backend/organization-facade"`。`repository` 只能用 `get_platform_context.code_directories` 的别名（通常 `v8`），不要把 `backend`/`frontend` 当作 repository。实现前至少核对一个定义、一个调用方或测试示例；若知识库与源码冲突，按当前源码标记版本差异并要求人工确认。

## 6. 质量与安全硬约束

- 质量检查使用 `v8-quality-inspection`，远端规则优先，再补充业务闭环、异常处理、死循环、资源释放、可用性与宕机风险等通用基线。
- 写操作必须核对权限、当前用户/租户、事务边界、幂等、重试和回滚；跨服务调用失败不可吞掉。
- 生产配置中的地址、账号、Token、密码、连接串和个人数据必须脱敏；质量报告只保存结构化发现和路径哈希，不保存完整 Diff 或原始日志。
- “调研/说明/评估/不要修改”只输出判断和建议；明确的“实现”“修改”或“生成”请求即构成授权，才修改本地工程，并在交付前运行相关测试。

## 7. 常见误判

- 不要把普通 Java 代码默认判定为 SPI。
- 不得把 UDC 页面需求默认判定为 React 手写。
- 不要把第三方同步默认判定为直接数据库操作。
- 不要把 `Base`、`Core`、`Sync` AppService 混用。
- 不要把 UDC 设计态、UDC ext 后端、标品前端扩展和独立 SPI 工程混为一谈。
- 不要把“能查到一个方法”当作完成；必须继续核对定义、调用方、状态、异常和测试。

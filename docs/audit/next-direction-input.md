# 2小爪 Agent 下一阶段方向审计输入

> ✅ **P6 裁决（2026-11-07）：保留原地，不移动、不删除。**
> 本文件是下一阶段方向的审计输入（高难度问题 / 决策闸门 / 证据要求），**仍被程序读取**：
> `components/audit_summary.py:12` 的 `REPORTS["next_direction"]` 直接指向本文件名（2026-11-07 实测确认），
> `seeyon_cli.py` 的 `audit-summary` 子命令走 `components.audit_summary.build_summary(dir, ...)` 读它；
> `tests/test_audit_summary.py:20` 也按此文件名写临时输入。
> ⇒ 要动本文件，必须同步改代码与测试。上级登记见 `docs/audit/README.md` §六。

> 目的：在已完成的 UDC 静态审计和当前 2小爪 Agent 只读骨架基础上，整理下一阶段必须继续回答的高难度问题、决策闸门和证据要求。本文**不是实施方案**，不定义功能代码、接口改造或环境操作；未授权连接 test2，也不以静态证据替代动态验证。
>
> 证据口径：`FACT` 表示已有直接文件/源码/反编译/哈希证据；`OBSERVATION` 表示审计中观察到的现象；`UNVERIFIED/HYPOTHESIS` 表示尚未形成闭环。版本结论仅适用于明确的 artifact + version + sha256，不外推到全部 5.3 或全部客户。

## 1. 审计范围与当前边界

### 1.1 已证实的骨架事实（FACT）

- 仓库为 `<SEEYON_AGENT_ROOT>`，README 将当前版本定义为“可测试的只读骨架”。组件入口包括 Core、UDC、Runtime、Integration 和 Providers 端口预留。
- Core 已有 `SeeyonAgent`、意图路由、宿主注入的 Context/Session/Policy、组件注册与执行事件记录；默认策略为只允许 `inspect_*` 与 `dry_run`。
- UDC 组件 `components/udc/` 已具备模型、证据目录、分析器、版本注册、计划器和组件入口；能力清单为 `inspect_application`、`inspect_entity`、`inspect_page`、`inspect_microflow`、`dry_run`。
- UDC 组件默认 `read_only = True`；README 明确列出尚未实现的创建应用、修改实体、数据库/Redis 写入、发布、部署和真实 GraphQL 写入。
- UDC 当前以本地审计目录/快照为输入；`UdcEvidenceCatalog`、`UdcAnalyzer` 和 `UdcVersionRegistry` 读取 JSON 证据，不连接真实环境。缺失文件或未知版本会降级为 `UNVERIFIED`。
- 当前骨架测试文件覆盖 UDC 模型序列化、目录汇总、域分析、版本精确匹配、只读计划和拒绝写操作；README 记录的基线为 `11 passed`（应以重新执行时的实际结果为准）。

### 1.2 已完成 UDC 审计可直接引用的事实（FACT）

以下结论来自本机 `<USER_HOME>/... 下的已生成审计文件，目标 artifact 主要为 `5.3.517`：

- `udc_web_controller_contracts.json`：`udc-web-5.3.517.jar`，54 个 Controller、672 个 endpoint，解析失败列表为空；这是静态反编译注解/方法合同，不是线上可达性证明。
- `udc_controller_service_edges.json`：54 个 Controller、672 条 Controller→Service 边；仍需把调用者、服务实现、持久化和运行态副作用串成闭环。
- `udc_frontend_core_api_mapping.json`：前端核心 loader 映射 36 个 unique calls，其中 16 个被列入 FACT、20 个列入 UNVERIFIED；FACT 受限于下载 chunk 中直接可见的 `fieldType/paramsType/queryFields` 和明确匹配规则。
- `udc_dynamic_contract_gap_catalog.json`：后端操作目录 145 条；`EntityDto`、`AttributeDto`、`PageInfoDto`、`MicroFlowDefinitionDto`、`DataFlowDto`、部署 DTO 等关键保存/发布输入仍存在未匹配的前端调用缺口。
- `udc_5_3_517_module_audit.json`：8 个 jar、全部类 3482 个，审计域类 3422 个；其中 P0 1、P1 36、P2 3385。此优先级是静态筛选结果，不等于实现优先级或线上风险等级。
- `udc_5_3_517_core_chain_audit.json`：已有 20 个 targeted decompile、184 条调用边；下一批高分对象集中在微流程运行时实体数据源、页面/实体代码元数据任务、发布状态/元数据后处理、部署检测、SaveAs 和代码模板等链路。
- `udc_service_persistence_audit_2.json`：静态证据显示基础实体 CRUD 涉及 INSERT/UPDATE 分支、运行态数据库元数据查询；也观察到实体缓存、Redis CacheManager、缓存淘汰注解/调用，但未形成具体业务表、key、TTL、失效时机和事务边界的完整动态证据。
- `udc_runtime_side_effect_catalog.json`：记录为本地只读源码扫描，明确规定缺少 key prefix/TTL/event/executor/call edge 时不得推断；因此不能把其中空证据解释为“没有副作用”。
- `udc_version_samples_manifest.json` 与 `udc_version_compatibility_catalog.json`：采样 6 个版本（`3.8.227`、`3.12.124`、`5.3.314`、`5.3.380`、`5.3.477`、`5.3.517`），覆盖 `udc-web`、`udc-starter-runtime`、`udc-starter-lowcode`、`udc-starter-autocode`。版本差异目录明确：字节码成员存在/描述符稳定不证明行为或 wire/API 兼容；3.x→5.3 是重大兼容边界，5.3 patchline 仍存在资源变化。
- `udc_deployment_artifacts_audit.json` 与 `udc_frontend_static_source_gap.json`：已证明客户 Pod 存在独立 frontend jar/assemble-resource 等部署证据，并记录独立前端 artifact 的强支持结论；但 OSS bucket/object、Ingress 到 jar/对象的精确映射，以及“实际由 OSS 提供的字节”仍未证实。
- `udc_front_back_chain_audit.json`：目标客户应用源码可见后端 Controller、生成 AppService、实体和 `extend` 微流程候选；未发现可直接命名为 FRONTEND 的独立源码目录，所需设计器真实路由、Network 请求、完整元数据 JSON、发布后刷新链路被列为后续证据。

## 2. 待动态验证的问题清单（下一阶段审计输入）

> 动态验证必须另行确认目标环境、namespace、应用 ID、时间窗和只读权限；本清单不授权执行 test2 操作。

### D1. 设计态保存协议是否与后端合同一一对应

- **问题**：创建应用、实体、字段、页面 Schema、微流程、数据流的真实前端路由/loader/ajax 请求，是否分别对应已识别的 Controller、DTO、参数键和响应结构？
- **所需证据**：脱敏 Network 记录（URL、HTTP 方法、请求体、响应、路由上下文）、前端 chunk/loader 定位、Controller 注解、DTO 字段反编译和关联 ID。
- **当前缺口**：关键 DTO 的前端调用身份仍为 UNVERIFIED，尤其实体字段保存、PageInfo、MicroFlow、DataFlow 和 Deploy。
- **闸门**：没有达到“前端请求→后端入口→DTO 字段→服务实现”的逐项闭环前，不得固化统一写入契约，也不得实现写操作。

### D2. 发布/部署是否是一个可重放且可观测的状态机

- **问题**：保存、生成、发布、部署、运行态注册、前端静态资源发布之间的顺序、异步任务、重试、幂等键和失败补偿是什么？
- **所需证据**：发布前后版本/状态读取、任务 ID、日志 trace、事件/队列记录、生成物清单、运行态 metadata/runtimejson 回读，以及失败重试后的状态变化。
- **当前缺口**：已有 PublishState/metadata/deploy 相关静态类和调用候选，但未证明实际编排、异步边界和最终一致性。
- **闸门**：若状态机或幂等性未被证明，方向只能停留在只读诊断/报告，不能进入自动发布、自动重试或补偿设计。

### D3. 元数据、物理表、实体运行态三者如何一致

- **问题**：设计态元数据、生成实体/DTO、运行态注册、物理表和 Redis 缓存的权威源及一致性窗口分别是什么？
- **所需证据**：同一应用/实体/字段的设计态 JSON、生成物、运行态元数据、MySQL schema/业务表只读快照、Redis key/type/TTL/序列化、操作前后日志与 trace。
- **当前缺口**：静态审计只证明存在数据库元数据查询和缓存机制；不能证明某一字段变更会如何传播，也不能以改物理表代替元数据变更。
- **闸门**：未能回答“哪个层先变、谁触发刷新、失败如何回滚/重建”前，不得给出字段迁移或缓存清理方案。

### D4. 运行时缓存和事件副作用是否跨租户/跨应用隔离

- **问题**：`udc-sandbox`、entity cache、事件总线和资源权限注册的 key 命名、租户/应用维度、TTL、淘汰和事务关系是什么？
- **所需证据**：只读 key pattern、类型、TTL、脱敏 value 结构、调用时机、事件 payload 类型、日志关联；禁止导出凭据和完整敏感缓存。
- **当前缺口**：源码中可见 Redis/缓存和事件类，但动态 key、TTL、失效时机和执行者不完整。
- **闸门**：隔离边界未证实前，不得假设清缓存是安全的，也不得实现按名称/应用 ID 的批量删除。

### D5. 生成应用前端资源真实交付链路

- **问题**：客户 frontend jar、assemble-resource、Pod 文件、Ingress/OSS 对象之间的映射是否确定？`pageUrl`/应用 ID 是否参与路由拼接？
- **所需证据**：目标部署清单、manifest/入口 chunk、Ingress/网关只读配置、实际响应头/静态资源路径、jar 内路径到服务 URL 的对应关系。
- **当前缺口**：独立 artifact 已有静态部署证据，但 OSS bucket/object/prefix 和最终字节来源未证实，客户仓库亦无独立前端源码。
- **闸门**：未确认交付源和路由规则前，不得设计前端发布、资源替换、URL 推导或自动回滚。

### D6. 真实业务入口的 DTO→实体→物理表映射

- **问题**：客户扩展微流程/Controller 使用的 DTO、底层实体、主表/子表、唯一键和事务边界是否可以逐条追踪？
- **所需证据**：扩展代码、实体元数据、表结构/注释/索引、执行日志、业务唯一键和前后快照；区分 API PASS、LIVE PASS、TIMEOUT、FAIL、UNVERIFIED。
- **当前缺口**：已有客户后端链路扫描和微流程候选，不足以证明所有业务写入路径或物理表关系。
- **闸门**：未完成同一 trace 下的日志与数据库回读前，不得把 HTTP 200/Boolean/固定成功值视为落库成功。

### D7. 版本兼容边界的行为验证

- **问题**：目录标记的 stable class/method 是否在真实请求、元数据格式、缓存、发布和生成行为上兼容？5.3 patchline 的资源差异是否影响运行？
- **所需证据**：每个目标版本 artifact/version/sha256、相同最小闭环的静态合同差异、脱敏请求/响应、运行日志和生成物差异。
- **当前缺口**：目前只有六版本成员差异；目录已声明其不能推出行为/wire/API 兼容。
- **闸门**：没有目标版本的行为证据，不得把 5.3.517 骨架契约升级为跨版本适配层；至少要按重大边界和 patchline 差异拆分证据。

### D8. 失败、超时、重试和并发的一致性

- **问题**：发布/生成/同步超时后是否仍在后台执行？重复提交、并发发布、部分成功和重试是否产生重复表数据、脏元数据或缓存污染？
- **所需证据**：客户端超时、Pod 日志、任务状态、数据库前后快照、幂等字段/锁、重试窗口和 trace 关联。
- **当前缺口**：静态类名和调用边不能证明事务提交/回滚、锁和异步执行语义。
- **闸门**：没有可观测终态和幂等证明前，不得设计自动 retry、并行执行或超时后的“未执行”判定。

### D9. Agent 审计输入是否足够表达证据与决策

- **问题**：当前统一 `Result/Evidence` 是否能承载 artifact 哈希、环境、时间窗、关联 trace、证据等级、缺口、负面证据和读写边界？
- **所需证据**：用现有审计文件和模拟输入做离线契约检查；检查缺失文件、版本不匹配、解析失败、部分证据和敏感字段脱敏是否可区分。
- **当前缺口**：骨架已有通用 envelope，但 UDC 的报告字段仍以本地目录统计为主，尚未表达完整调用链和决策状态。
- **闸门**：若报告模型不能区分 FACT/OBSERVATION/UNVERIFIED、API PASS/LIVE PASS、静态/动态来源，则先完善审计表达能力，不进入执行器方向。

## 3. 架构风险（不是待实现方案）

### R1. 只读骨架与未来执行能力之间存在边界穿透风险

当前 Core 通过组件注册和 Policy 分发动作，UDC 组件能力字符串包含 `dry_run`，但真实写操作尚未存在。未来若直接把 `planner` 输出升级为 executor，可能绕过动作白名单、确认、回读和副作用审计。风险等级：**高**。决策要求：任何执行方向必须先证明策略边界、动作分类、审批/确认、幂等和回读协议。

### R2. 静态证据数量可能制造“完整性错觉”

672 endpoints、145 backend operations、3422 domain classes 和 36 frontend calls 是目录规模，不是闭环覆盖率。名称匹配、反编译 import 和 class/member diff 都可能无法证明真实调用、参数语义或运行时生效。风险等级：**高**。不得用数量替代关键路径覆盖矩阵。

### R3. 组件边界可能把 UDC、Runtime、Integration、SPI 误连成默认链路

当前设计将 UDC 与 SPI、Integration、Runtime 并列；UDC skill 明确“不建立默认 UDC→SPI 调用链”。客户 `ext` 是否调用 SPI 必须看真实依赖和代码证据。风险等级：**高**。未经证据不得在 Core 中建立隐式跨组件编排。

### R4. 领域模型过早固化会丢失版本/客户差异

当前 `ApplicationSpec/EntitySpec/PageSpec/MicroFlowSpec` 是最小模型，不能代表完整 UDC 元数据、权限、关系、数据源、发布版本、生成物和客户扩展。风险等级：**高**。在关键 DTO/版本/客户第二样本未闭环前，不得把该模型当作通用写入 schema。

### R5. 版本适配层可能把 ABI 稳定误判为 API/行为稳定

6 版本目录已显示 major boundary、patchline resource changes 和 parse limitations。风险等级：**高**。版本适配必须以目标 artifact 哈希和行为证据为单位，并保留不可复用项。

### R6. 报告中的默认值和静态回退可能掩盖缺证

当前部分目录逻辑在缺少 dynamic contract 数据时使用已知审计数值或返回 `UNVERIFIED`；这适合当前测试夹具，但若用于生产决策，可能把历史事实误当作当前目标事实。风险等级：**中高**。审计输出必须携带来源文件、目标、生成时间和是否为回退值。

### R7. 数据库/Redis/发布副作用的跨层耦合尚未被建模

静态证据同时出现 CRUD、实体元数据查询、Redis cache manager、缓存淘汰和事件监听。若只按 HTTP endpoint 建模，会遗漏事务、事件和缓存后果。风险等级：**高**。方向选择前必须形成调用链及副作用图。

### R8. 前端来源不明会限制端到端自动化

客户前端源码缺失、OSS/Ingress 映射未证实；只依赖后端 Controller 无法还原设计器操作和路由。风险等级：**中高**。在前端证据补齐前，只能做后端合同/离线审计，不应声称端到端覆盖。

### R9. Agent 统一入口的意图路由是启发式，不是领域解析器

当前 `SeeyonAgent.route` 通过关键词路由 `udc/integration/runtime/spi`。复杂任务可能同时涉及多个组件，或因词汇变化落入 unknown。风险等级：**中**。不得以当前路由结果证明跨组件任务编排正确；需要先定义任务分解和证据依赖。

## 4. 不可假设项（在后续任何决策中保持 UNKNOWN）

以下内容没有直接证据时必须标记 `UNVERIFIED`，不可由命名、HTTP 200、类名、单客户样例或相邻版本推断：

1. 不能假设 `udc-web` endpoint 可从公网/当前环境访问、鉴权方式已知或与静态 route 完全一致。
2. 不能假设 frontend loader 的 `fieldType` 就是 REST URL，也不能假设 GraphQL loader 与 direct ajax endpoint 等价。
3. 不能假设 `EntityDto`/`AttributeDto`/`PageInfoDto` 等 DTO 的字段、默认值、校验和前端 payload 已完全对应。
4. 不能假设设计态保存成功就代表生成物已生成、发布已完成、运行态已注册或业务表已可用。
5. 不能假设物理表字段变更就会改变运行时实体元数据；也不能假设缓存会自动失效。
6. 不能假设 Redis key 的租户、应用、版本隔离方式、TTL、序列化或删除副作用；源码出现 `600L` 只代表某处静态字面量证据，不代表全局 TTL 规则。
7. 不能假设事件监听必然同步执行、一次执行、事务内执行或成功后可重放。
8. 不能假设任务/发布/生成不存在异步执行、后台继续执行、部分成功或客户端超时后已回写。
9. 不能假设 DTO 名称去掉 `Dto` 就是底层实体，也不能假设实体名就是物理表名。
10. 不能假设一个客户项目、一个应用 ID、一个表名或一个业务接口可以提炼为 UDC Core 通用规则。
11. 不能假设 5.3.517 的 class/member 存在性可以覆盖 3.x、5.3 其他 patch 或未采样版本；不能假设资源变化无运行影响。
12. 不能假设客户 frontend jar 已由 OSS 提供、Ingress 已按 pageUrl/应用 ID 映射，或本地后端 jar 能替代客户 frontend 内容证据。
13. 不能假设 `API PASS`、HTTP 200、外层 `true`、固定 `BOOT_0000` 或客户端未报错等同于 `LIVE PASS`。
14. 不能假设当前 UDC 与 SPI 存在默认调用链；客户扩展是否调用 SPI 必须由依赖/代码证据确认。
15. 不能假设当前 `ApplicationSpec` 等 Python dataclass 是完整 UDC schema，也不能据此生成真实写请求。
16. 不能假设本阶段可以连接 test2、修改 Nacos/数据库/Redis、发布、清缓存、重启 Pod 或提交任何 GraphQL/HTTP 写请求。

## 5. 决策闸门（Gate）

| 闸门 | 必须先回答的问题 | 放行证据 | 未通过时的允许范围 | 禁止越过的动作 |
|---|---|---|---|---|
| G0 范围与授权 | 目标环境、namespace、应用、时间窗、读写权限是否明确？ | 书面范围 + 环境标识 + 脱敏策略 | 本地文件/已有快照审计 | 连接 test2、任何外部写入 |
| G1 证据可追溯 | 每个事实能否回到 artifact/version/sha256、文件/类/行或动态 trace？ | 证据索引、生成时间、来源和负面证据 | 静态目录补全、离线模型检查 | 将推断写成 FACT |
| G2 前后端合同闭环 | 保存/发布关键 payload 是否已与 Controller/DTO/Service 对应？ | Network + 反编译 DTO/Controller + 调用链 | 只读合同审计 | 实现通用写入器 |
| G3 运行态一致性 | 元数据、生成物、运行态、DB、Redis 的传播和失效是否可观测？ | 同一目标的前后快照、日志、key/TTL、状态 | 只读诊断和差异报告 | 修改表/清缓存/重载 |
| G4 状态机与幂等 | 发布/生成/同步的异步、重试、锁、补偿和终态是否证明？ | 任务/事件/日志/DB 的闭环及重复执行实验授权 | 失败分类和风险登记 | 自动重试/并发发布 |
| G5 版本/客户边界 | 结论适用于哪个 artifact、版本和客户？ | 多版本/多样本对比，明确 stable/changed/non-reusable | 版本限定的只读适配研究 | 跨版本通用化 |
| G6 安全与副作用 | 租户隔离、权限、凭据脱敏、审计、回滚是否明确？ | 策略检查、最小权限、审计记录和回读设计 | 只读离线能力 | 生产写操作和批量操作 |
| G7 方向确认 | 目标究竟是审计助手、诊断助手、规划器还是执行器？ | 用户确认 + 通过 G0-G6 的证据/风险清单 | 继续审计输入整理 | 擅自进入方案实现 |

## 6. 建议的下一轮取证顺序（仅审计顺序）

1. **先补 D1**：以最小闭环（一个应用、一个实体、一个字段、一个页面、一个微流程）建立设计器动作到后端合同的映射；只采集和回读，不写入。
2. **再补 D3/D4**：针对同一闭环盘点运行态 metadata、业务表和 Redis 的关联、TTL、失效及日志证据，区分静态观察与动态事实。
3. **并行补 D5**：锁定客户前端 artifact、入口资源、Ingress/OSS 映射和 pageUrl 路由来源。
4. **随后补 D2/D8**：围绕一次已授权的发布/生成观察窗口，追踪任务、状态、超时、重试和最终一致性；若无法授权动态操作，保持 UNVERIFIED。
5. **最后补 D7/D9**：将已闭环路径按版本分层，校验骨架 Result/Evidence 是否能完整表达证据等级、环境、版本、trace、缺口和决策状态。

## 7. 本阶段明确结论

- 当前可继续推进的是：**只读证据目录、静态合同差异、调用链补证、风险登记和决策闸门定义**。
- 当前不能推进的是：**功能实现、真实写入器、自动发布/部署、数据库/Redis 修改、GraphQL 写入、连接 test2，以及把单客户/单版本事实抽象为通用方案**。
- 下一阶段是否进入方案策划，取决于 G0-G3 至少通过；是否进入任何自动执行方向，还必须通过 G4-G6，并取得用户对 G7 的明确确认。


## 8. 用户纠偏后的主线（2026-09-04）

本任务不以客户项目作为主要规则来源。客户项目只在 UDC 构造规则完成后作为验证样本。

正确主线：

```text
UDC 全量平台代码
  + UDC 前端构造物
  + UDC 依赖 Artifact
  + Nacos 配置/元数据/初始化 SQL
  + 数据库对象关系
  + Runtime 生成与消费链
        ↓
UDC Construction Rule Model
        ↓
最小可拼接应用构造链
```

### 8.1 绝对边界

- UDC、BPM、SPI、Connector 是 2小爪 Agent 的同级独立平台模块。
- `UDC/BPM Construction`、`UDC/SPI Construction`、`UDC/Connector Construction` 是 UDC 的构造规则，不是对应平台模块的子模块。
- 客户项目不用于反推 UDC 通用规则，只用于最后验证标准规则和识别客户扩展。

### 8.2 下一轮必须先做的工作

1. 盘点 UDC 5.3.517 全量 Artifact、class、package、依赖和资源；对构造域建立索引。
2. 获取并分析 UDC 前端 `remoteEntry.js`、`manifest.json` 及其分片，优先从已授权浏览器/服务器只读路径保存真实字节。
3. 以“创建应用、创建实体、创建字段、拖拽页面组件、绑定实体、保存/发布”为主线，从前端状态和 payload 反查后端 DTO、Controller、Service。
4. 读取 Nacos 中的 UDC 配置、元数据、模板和 SQL，区分平台初始化数据、构造模板和运行时配置。
5. 将每条规则落成：对象、输入、固定模板、动态参数、依赖对象、生成结果、保存位置、引用方式、运行时消费者。
6. 独立建立 BPM/SPI/Connector 平台能力索引，再建立它们与 UDC 构造规则的证据关系。
7. 在上述主线完成前，不再把客户项目扫描作为主要推进方向。

### 8.3 当前证据状态

- UDC 后端/生成/运行时代码：已有大量本地 JAR 与反编译源码，可继续定向深挖。
- UDC 前端：此前只保留过远程入口可达性观察；当前工作进程直接下载因 TLS EOF 阻塞，尚未取得本地前端字节。
- 已知前端只读观察：UDC `remoteEntry.js` 返回 200、约 47,564 bytes；`manifest.json` 返回 200、约 66 bytes；这些是前序 HTTP 观察，不等于当前已保存前端内容。
- 客户项目：已暂停作为主线，不再扩展客户业务扫描。

### 8.4 构造规则证据等级

- `RULE_CANDIDATE`：仅由类名、字段名或路径命名发现。
- `STATIC_RULE`：前端 payload/生成代码/DTO/Service 或模板至少形成静态链路。
- `VERIFIED_RULE`：前端构造动作、后端处理、元数据/SQL/生成物之间形成可追溯闭环。
- `LIVE_RULE`：在明确授权的只读/最小实验环境中有真实请求、回读和运行态消费证据。

当前不得把已有后端类名直接称为完整构造规则；必须完成前后端和持久化拼接。

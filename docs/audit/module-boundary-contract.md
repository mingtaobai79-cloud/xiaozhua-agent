# xiaozhua Agent 模块边界与联动契约

## 结论

UDC、Standard Product Application、SPI、Integration、Runtime 是并列对象/模块，不存在“把标品或 SPI 放进 UDC”的归属关系。它们可以通过证据图建立联动，但联动不改变模块归属。

```text
xiaozhua Agent Core
├── UDC                         # 低代码设计态、生成物、UDC 运行态机制
├── Standard Product Application # bpm、ctp-user、ctp-affair、cip-* 等标品服务
├── SPI                         # 可插拔契约/扩展实现（SSO、MQ、文件、数据源等）
├── Integration                 # 三方系统接口、同步、鉴权和适配
└── Runtime                     # Pod、Nacos、MySQL、Redis、日志、部署观测
```

## 归属规则

| 对象 | 所属模块 | 不得做的归类 | 允许的联动证据 |
|---|---|---|---|
| UDC 平台 | UDC | 不归入标品或 SPI | 生成/运行客户应用、读取运行态元数据 |
| bpm、ctp-user、ctp-affair、cip-* | Standard Product Application | 不归入 UDC | 客户应用调用标品 API、运行依赖、路由/配置绑定 |
| SSO、MQ、文件、数据源等 SPI | SPI | 不归入 UDC 或标品业务代码 | 客户扩展的精确依赖与调用点 |
| 三方接口/同步/鉴权适配 | Integration | 不归入 UDC Core | 客户应用或标品通过适配器调用 |
| Pod/Nacos/MySQL/Redis/日志/部署 | Runtime | 不归入上述业务模块 | 运行对象承载、配置绑定、状态回读 |
| 客户 UDC 应用与 ext | Customer UDC Application / Extension | 不提升为 UDC Core、标品或 SPI 通用事实 | 仅作为边界样本和按需调用链证据 |

## 联动不等于归属

允许表达：

```text
UDC Platform --generates--> Customer UDC Application
Customer UDC Application --calls--> Standard Product Application
Customer Extension --uses--> SPI
Customer Extension --integrates-with--> External System
Runtime --hosts/loads/observes--> UDC / Standard App / SPI / Integration
Nacos dataId --binds-config--> 某个具体应用或平台组件
```

禁止表达：

```text
UDC contains all standard applications
UDC contains SPI
UDC calls SPI（无精确源码/依赖/调用点证据）
Pod 名称直接决定模块归属
客户实体/页面/微流程清单代表 UDC 通用能力
````

## 证据升级规则

- 模块归属：需要源码、Artifact、Deployment、Nacos 或明确契约证据。
- 联动关系：至少需要两端对象身份 + 关系类型 + 精确 locator。
- 仅有 Maven 依赖：只能记为静态依赖观察，不能证明运行时调用。
- 仅有 Pod/Image：只能证明运行时清单，不证明代码调用链。
- 仅有 Nacos dataId：只能证明配置对象存在/读取成功，不证明业务加载和调用成功。
- 客户业务明细（实体、页面、微流程、业务表、ext 文件）默认 `QUERY_ON_DEMAND_NOT_DURABLE`，不进入通用事实图。

## 当前工程状态

- UDC：已有离线证据、Analyzer、PolicyGate 和 CLI。
- Standard Product Application：作为独立 Profile 类型保留，当前仅在有直接证据时建立具体档案。
- SPI：当前代码仍是路由占位，不能报告为已实现；知识契约由 `xiaozhua-v8-spi` 单独维护。
- Integration：与 UDC 并列，不把客户外部接口提升为 UDC 能力。
- Runtime：已具备 test2 只读证据报告，和业务模块分离。

## 任务路由

复杂任务可以跨模块，但先拆成独立子任务：

```text
UDC：设计态/生成/运行元数据
Standard App：标品服务契约和调用者
SPI：SPI 接口、版本、注册和实现边界
Integration：第三方调用和同步链路
Runtime：承载、配置、存储、缓存、日志、部署
```

最终报告必须分别给出各模块的 `FACT / OBSERVATION / UNVERIFIED / BLOCKED`，再单独列联动关系；不能用联动关系覆盖模块边界。

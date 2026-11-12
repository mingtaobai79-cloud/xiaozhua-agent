---
name: seeyon-extension-usage
description: "Use when 写 UDC 自定义页面/微流程扩展代码，或要查平台接口怎么调、DTO 字段怎么填、方法背后动了什么时。"
version: 2.0.0
author: 小爪 🐾
license: MIT
platforms: [windows, macos, linux]
tags: [seeyon, udc, extension, custom-page, microflow, transport, appservice, api-usage]
metadata:
  hermes:
    tags: [seeyon, udc, extension, custom-page, microflow, transport, appservice, api-usage]
    related_skills: [seeyon-agent-fact-protocol, seeyon-udc-design-time-build, seeyon-udc-runtime]
---

# Seeyon 扩展代码 · 平台用法入口

## When to Use

- 要写/改 **UDC 自定义页面**（前端 `customPage.tsx`）或 **自定义微流程**（后端 extend 工程）的业务代码
- 知道「要做什么事」但不知道「调哪个方法、传什么、字段怎么填」
- 手上有后端编译错误（`SingleResponse.getData()` 取不到值、`Sort` 类型不兼容…）要查正确写法
- 想知道「这个方法背后会动什么」或「我该挂哪个扩展点」
- 前端页面出现「接口 200 但报失败」、跳转白屏、组件 props 不生效

不适用：设计器里的元数据写面（那是 UDC 设计态的事，见 `seeyon-udc-design-time-build`）；
往本仓库落事实/证据（见 `seeyon-agent-fact-protocol`）。

## 一、导航：我想干什么 → 查哪个文件

**仓库根 = `<ROOT>`**（本机 `<SEEYON_AGENT_ROOT>`）。产物全是自动生成的，**不要手改**，重跑生成器即可。

| 我要… | 查 | 体量 |
|---|---|---|
| 知道「这件事该调哪个方法」 | `docs/audit/artifacts/extension-surface-*/action-index.md` | 125 KB |
| 知道「这个方法传什么、字段怎么填」 | `docs/audit/artifacts/api-usage/<域>.md` | 3.4 MB / 11 份 |
| 知道「字段的中文含义/示例/业务规则」 | 同上（卡片 `←` 后面）+ `dto-meta.json` | 932 KB |
| 知道「这个方法背后动了什么」 | `docs/audit/artifacts/service-flow-*/<构件>.md` | 5.2 MB / 16 份 |
| 知道「接口在哪个构件 / 实现类叫什么」 | `interfaces.json`（`pkg` 字段）+ `impl-map.json` | 65 MB / 51 KB |
| 知道「该挂哪个扩展点」 | `core/facts/standard-product/extension-point-decision-table.md` | 20 KB |
| 查完整签名 | `.../extension-surface-*/packages/<构件>.md` | 3.4 MB / 91 份 |
| 查某域全部类 | `.../extension-surface-*/domains/<域>.md` | 408 KB / 11 份 |

**五份产物怎么配合**（写一段扩展代码的完整路径）：

```
① 要做什么       → action-index.md          入口方法 + 接口名 + 入参 DTO
② 字段怎么填     → api-usage/<域>.md         字段名 + 类型 + 平台写的中文说明
③ 背后动什么     → service-flow-*/<构件>.md  调用链（Dao/Service/Event）
④ 编译验证       → probe_contracts.py        用真实 jar 编译你写的代码
⑤ 类型细节       → packages/<构件>.md        完整签名
```

权威事实在 `core/facts/**`（环境无关，23 格），**先读它们，不要重新推**。

## 二、后端：出入参一律套 transport 包装

```java
SingleRequest<T> / SingleResponse<T> / ListRequest / ListResponse<T>
PageRequest / PageDtoRequest<T> / PageResponse<T> / PageInfo / Sort
```

三条最容易犯：

1. **取值要两层**：`resp.getData()` 是 `SingleData<T>`，要再 `.getContent()`。
   `ListResponse` 同理得 `ListData<T>` 再 `.getContent()`。写 `resp.getData().getId()` 编译不过。
2. **`Sort` 用 `com.seeyon.boot.transport.Sort`**，不是 Spring 的 `Sort`，混用报「不兼容的类型」。
3. **入参恒为 `SingleRequest<T>`**（T 可以是 `Long`/`List<Long>`/`Dto`/`List<Dto>`）；
   多参数方法是**多个 `SingleRequest` 平铺 + 裸 `Sort`**，不要打包成一个 DTO。

```java
// 实测形态（已用真实 jar 编译通过）
SingleResponse<BpmSendResultDto> r = bpmAppService.send(SingleRequest.from(dto));
BpmSendResultDto result = r.getData().getContent();

ListRequest.from(map, sort);
service.selectListByTerm(SingleRequest.from(entityId), SingleRequest.from(keyword), sort);
service.updateBatch(SingleRequest.from(dtoList));
```

## 三、后端：两条调用通路

| 通路 | 适用 | 怎么写 |
|---|---|---|
| **Spring 注入** | 已知接口类型（推荐） | `@Autowired BpmAppService svc;` |
| **泛化调用** | 只有接口名字符串 / 动态模块 | `AppServiceProxy.invokeAppService(AppServiceInvokeDto)` |

泛化调用 = **本地 Spring BeanFactory 反射**，不是 Dubbo（不用跨进程）。关键字段：

```java
interfaceName  = "com.seeyon.bpm.api.common.BpmAppService"          // 接口全名
methodName     = "send"
paramType      = "com.seeyon.boot.transport.SingleRequest"           // 包装类型，不是 DTO
genericType    = "com.seeyon.bpm.dto.operation.openapi.BpmSendDto"   // DTO 放这里
paramJson      = "{\"templateCode\":\"xxx\",\"currentUserId\":123}"
returnJson     = Boolean.TRUE    // 想直接拿 JSON 字符串就开
```

6 层 Bean 查找兜底（末段首字母小写 → 接口全名 → ModuleAppBeanCache → 动态 Bean 名 →
`beanName` → `getBeansOfType`），全找不到抛 **BOOT_4014**（日志会打全 5 个参数）。

⚠️ **能调的前提是实现带 `@AppService`**（= `@Service` + `@Primary`）。
普通 `domain/service/XxxService` 不是 AppService Bean，只能注入不能泛化调。

⚠️ **命名不规则，别猜**：`com.seeyon.bpm.api.common.BpmAppService` 的实现是
`BpmApiAppServiceImpl`，不是 `BpmAppServiceImpl`。必须读 `impl-map.json`（字节码 implements 子句）。

→ 细节见 `core/facts/standard-product/appservice-invocation.md`

## 四、后端：分层、Dao 与自证

```
Dao        AllInOneBaseDao<T>（41 方法）/ BaseMybatisDao<T>（22 Mapper 组合）
Service    domain/service/XxxService（具体类，业务全在这）
AppService Service 的方法包装（出入参 DTO 契约层，XxxAppServiceImpl 只做一行转发）
```

**关键结构**：`XxxAppServiceImpl` 里几乎没有业务，真正逻辑在 `domain/service/XxxService`。
所以「这个接口背后动了什么」要查 domain 层，不是看 Impl。

- 运行时链路是 **REST → proxy controller → proxy appservice → domain service**；扩展代码挂在后两层。
- 写操作返回 `Integer`（行数）或 `Long`（新 id）；`update` 回 0 = 没命中行，不是异常。
- 批量用 `createBatch`/`updateBatch`/`deleteByIds`，不要循环调单个方法。
- 幂等（`CtpIdempotent` + 切面）、事务、异常翻译（`ExceptionHandler` 链 + 各库 `DBExceptionParser`）
  都是**框架 AOP**：抛语义异常即可，不要自己写 try/catch 拼响应。
- 切面里要上下文信息从 `AppServiceContext` 取，不要自建 ThreadLocal。
- 跨应用调标品用 `DubboFactory.getProxy`；调别的应用 AppService 用 `AppServiceProxy`。

### Dao 层（不要手搓 SQL）

- 首选 `AllInOneBaseDao<T>`（41 方法）；想缩小接口面就只 mixin 需要的单 Mapper。
- Dao 返回 `PageData<T>`，**不要在这一层套 transport 的 `PageResponse`**（那是 AppService 的事）。
- 三套条件按需选：`ByCondition(s)` → 保序 `ByComplexConditions(LinkedHashMap)` → 最灵活 `ByDynamicConditions(SeeyonCondition)`。
- `*Internal` 是批量真实现，业务调 `createBatch`/`deleteByIds` 这类 default 方法。
- 平台**不走 XML SQL**（109 个 jar 只有 8 个 mapper XML），条件靠 Wrapper 动态拼，别指望看 SQL 反推业务。
- 多数据库走 `DatabaseDialect`（已内置 10 种：MySQL/Oracle/PostgreSQL/SQLServer/达梦/金仓/GBase/神通/巨杉/TDSQL/TiDB），
  不要写「当前是不是 MySQL」的 if-else。
- 审计/脱敏/权限/加密/验签都是拦截器 + 注解/SPI，不要在业务 SQL 里手写。

### 标品接口面（8 个域，先查再写）

```
组织     organization-facade    OrgCommonAppService(35) / OrgUnitBaseAppService(20)  ← Base 与 Core 成对
流程     bpm-facade             BpmAppService(22) / BpmTemplateAppService(32)
UDC→BPM  bpm-facade             BpmUdcApiService(4)：sendForUdc / repealForUdc / stopForUdc / deleteCaseByIdForUdc
事项     ctp-affair-facade      AffairCommonAppService(47) / AffairUdcAppService / AffairMicroflowAppService
文件     boot-starter-file      StorageService(14) / StorageSpi(9)（三桶：private/public/ferryboat）
枚举     boot-starter-enums     CtpEnumItemService(135) / CtpEnumService(68) / CtpEnumAppService(19)
系统变量 boot-starter-systemvariable  SystemVariableUtils(126)
连接器   cip-connector-api      DataBaseExecutorService(14) / LinkerSecurityService(9) / SsoService(7)
```

- UDC 发起/撤销/终止流程走 `*ForUdc` 接缝，**不要直调 `BpmAppService.send`**。
- 接自建对象存储实现 `StorageSpi`（含三个桶名），不要改 `StorageService`。
- 枚举：`CtpEnum*Service` 是 domain 层（裸返回类型），`CtpEnumAppService` 是契约层（套 transport），风格不同是设计。
- 取当前用户/单位/部门一律 `SystemVariableUtils`，不要自己读 Session/ThreadLocal。
- 连接器扩展点是一族 `*ProviderService`（实现 Provider 并提供 `getPageJson` + `jsonCheck`），不是改 `LinkerAppService`。

### 跨服务（Dubbo）

- 拿标品服务代理用 `DubboFactory.getProxy(...)` 五个重载（类名 → +group → +version → +timeout）；
  不要自己写 `@DubboReference`/`@Reference`，会绕过 group/version 约定在灰度下取错实例。
- 自己的实现要导出：放在 `DubboProperties.packagesToScan` 覆盖的包下 + 带平台导出注解，不要手写 `ServiceConfig`。
- 跨应用调 AppService 用 `AppServiceProxy`，按目标返回类型选单对象/列表/分页入口；可靠送达用 `reliableInvokeAppService` + 回调。
- 上下文透传由 `DubboContextFilter` 完成，不要手动塞 header；灰度用 `GrayContext` 且用完 `removeAll()`。

### core jar 工具类与注解（写之前先查）

- `JsonUtils`(28)：按场景选变体 —— 去 null `toJsonNotIncludeNull`、Long 精度 `toJsonLongToString`、
  金额 `toJsonDecimalToString`、枚举出 code `toJsonEnumToCode`。
- `DateUtils`(61) / `StringUtils`(35) / `BeanUtils`(7) / `IoUtils` / `FileUtils` / `DatabaseUtils`(47)。
- 脱敏用 `StringUtils.mask(String,int,int[,char])`，不要自己 substring 拼星号。
- 自定义类型转换注册 `TypeConverter` 到 `TypeConverterManager`，不要写散落 if-else。
- 开放 OpenAPI 是**注解组合**：`@AppService` + `@AppServiceOperation(openApi=@OpenApi(isOpenApi=true,url="..."))`。
- 加密/脱敏/验签替换实现走 `boot-spi` 的 `EntityEncryption`/`SensitiveSpi`/`DataSignExecution`。
- 主键用 `IdentifierGenerator.generateLong()`。

## 五、扩展点：先查决策表再动手

`core/facts/standard-product/extension-point-decision-table.md`（60 行场景表）：
「我要干什么 → 实现哪个接口 → 必实现哪个方法 → 平台参照实现有几个」。

高频八条：

| 我要干什么 | 实现 | 必实现方法 |
|---|---|---|
| 发布前校验拦下 | `DeployBeforeService` | `boolean handle(AppContext)`（false = 拦） |
| 元数据构建后补一段 | `AppMetaDataContextPostProcess` | `void postProcessAppMetaDataContext(AppContext)` |
| 生成新文件/配置类 | `CodeTask` | `String code(CodeContext)` |
| 导出加一类产物 | `TransportHandler` | `List<SchemaInfo> out(CodeContext)` |
| 导入自己处理一段 | `Importable` | `void in(TransportData)` |
| 属性类型 A→B 迁数据 | `TypeChangeSqlResolver` | `boolean match(AttributeDto, AttributeDto, CodeContext)` |
| 操作权限判定 | `ExtendAppOperationAuthCheck` | `boolean hasRight(ExtendAppAuthCheckInfoDto)` |
| 加一致性检测 | `DetectionTask` | `getDomainObjects()` + `detection(DetectionContext)` |

⚠️ **帖注解即注册**：`AppService` / `Importer` / `ConsistencyDetection` / `TypeMapping` /
`ParamLoadService` / `ExpressionFilter` / `EventHandler` / `ImportUpgradeHandler` 自带 Spring 元注解，
**忘贴 = 静默失效**（有实现但永不触发）。

⚠️ 只有 `-ext` 模块可写，`-facade`/`-biz`/`-web` 是标品生成，改了会被覆盖。

## 六、前端：三个包的分工

```
@seeyon/ui               UI 组件（antd 封装，只有具名导出，94 个）
@seeyon/global           请求/路由/事件/存储/租户/枚举/打印/i18n
@seeyon/udc-runtime-core 页面运行时：入参、组件取值赋值、微流程调用、表达式
```

三条最容易犯：

1. **组件从 `@seeyon/ui` 导入，不从 `antd`** —— antd 是传递依赖，不受 lockfile 保护。
   增量 props 读 `es/components/<组件>/*.d.ts`（如 `Table.stripe`、`Select.isUnControlMode`、`Button.isDebounce`）。
2. **`ajax` 只认平台响应格式**，非平台格式直接 reject → 页面「Network 200 但界面报失败」。
   处置：双格式 unwrap（`status===0 → data.content`；`success===true → content`），
   或改原生 fetch + `credentials:'include'`（此时 `/service` 前缀要自己补）。
3. **页内跳转用 `useSyHistory`**（兜底 `openTabLink` → `location.href`）。
   整页 `location.href` 会重建门户，进详情等一次白屏。

页面运行时（读页面数据/触发微流程/取表达式值）走 `@seeyon/udc-runtime-core`，不要自己拼 graphql。
页面路由恒为 `/main/portal/<应用编码>/<页面标识>`。

## 七、工程落位（与具体环境无关的规矩）

- 后端手写代码只写 `com/seeyon/<应用编码>/extend` 下；写在主工程会被构建覆盖。
- 手写 mybatis 放 `src/main/resources/mybatis/*.xml`；预制数据放 `src/main/resources/init/...`。
- 前端页面入口恒为 `src/pages/<页面标识>/customPage.tsx`；公共请求层放 `src/pages/common/` 复用，不要抄一份。
- 平台未预置的三方库必须走完整四步：`third_modules` 安装 → `syf build-multiple-bundless-module`
  → webpack alias → tsconfig `paths`。
- 换调试环境只改 dev server 覆盖文件里的 hostName，不要动应用编码。

## 八、可用性怎么判（不要靠猜）

**一个包/方法能不能用，取决于工程是否解析到它**，不取决于 maven 仓库或 node_modules 里有没有。

```bash
# 后端：classpath 里有没有这个 artifact
uv run --no-project python tools/core/platform/extract_extension_surface.py \
    --backend <ext 工程根> --frontend <pc 根> --repo <maven 仓库根> --emit <out.json>
# 前端：三态判定
python -c "from components.udc.extension_surface import *; ..."   # check_frontend_package
```

前端三态：`DECLARED`（package.json 声明）→ 最稳；`HOISTED`（传递依赖带进来的，
实测 lodash/antd/dayjs 就是）→ 能编译但不受 lockfile 保护，用前先补声明；
`MISSING` → 必须走 third_modules 四步。

> ⚠ 平台依赖面细节（parent pom 是主体、构件混版、parent 版本可能已发布但本地拉不到）
> 属**工程相关**结论，见 Hermes 侧工作手册与当轮抽取输出，不要写进本 skill。

## 九、写完怎么验：编译探针

文档说「这么写」，但没人保证真能编译。**用真实 jar 编译一遍**（不运行）：

```bash
python tools/core/platform/probe_contracts.py \
  --src tools/core/platform/probe_contracts --repo <MAVEN_REPO> \
  --interfaces docs/audit/artifacts/extension-surface-*/interfaces.json
```

classpath 从 `interfaces.json` 的 `pkg` 字段**自动推导**（import 的类 → 构件 → jar）。
顺带解决「这个类在哪个 jar」——实测 `EntityDto` 在 `udc-common` 不在 `udc-facade`。

加自己的探针：往 `tools/core/platform/probe_contracts/` 放 `.java` 即可，自动纳入。

现有探针：`ProbeBpmSend.java`（BPM 发起）、`ProbeUdc.java`（建实体 + 发布应用）。

## 十、抽包用法时的方法

```bash
# jar 方法签名面（javap + cfr 双路）
uv run --no-project python tools/core/platform/extract_jar_symbols.py \
    --jar <jar> --include <包前缀> \
    --javap <javap 原生路径> --cfr <cfr.jar> --limit 200 --emit <out.json>
```

四条纪律：

- `--limit` 必须 ≥ 该类总数：实测按字母序取前 30 会漏掉 `SingleRequest`/`SingleResponse`/`Sort`（字母序靠后）。
- `--javap` 传**原生路径**；MSYS 风格路径在 Python 里不存在，会被判成工具缺失而静默降级成单路。
- **`javap -p -v` 缺一不可**：`-v` 单独用**不输出 private 字段**（字段注解全丢）；
  输出是 GBK，按 utf-8 解会得到 `ģ��code` 这种乱码。
- 复合容器里的字符串要先解压再 grep（jar 里 `.class` 是 deflate 压缩的；
  前端产物是 gzip 的），否则「已存在」会被误判成「不存在」。

## 十一、references

| 文件 | 内容 |
|---|---|
| `references/appservice-cookbook.md` | 高频动作的完整调用写法（真实字段 + 平台说明） |
| `references/extension-points.md` | 扩展点全集、注册机制、被谁调用 |
| `references/evidence-index.md` | 所有证据件路径、体量、重跑命令、可信等级 |

**三者的分工**：本 SKILL 教「怎么想、怎么查」；`core/facts/**` 是权威事实（环境无关，23 格）；
`docs/audit/artifacts/**` 是证据件（含版本，可重跑）。**不要互相抄**——抄了就会不同步。

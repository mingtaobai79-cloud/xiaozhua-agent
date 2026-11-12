# runtime-engine-location.contract｜B-8 微流程执行引擎定位

> 切片：B-8（HANDOFF 20261018T031306Z）｜证据等级：**STATIC**（全部字节码/常量池证据，0 /service，0 写，0 DB）
> 仓库：<XIAOZHUA_AGENT_ROOT>｜HEAD：d946c0d（本切片未 commit 前的基线）
> 目标：定位微流程运行时执行引擎；判定执行链是否有 state 条件（B-7 遗留#1 指定证据源）

---

## 0. 结论（TL;DR）

**微流程运行时"引擎"不是一个解释器组件，而是三层结构：**

1. **代理入口层**（udc-starter-runtime-5.3.517.jar，`com.seeyon.boot.starter.udcrt.proxy`）：
   `UdcBaseGeneralController.doGetMicroFlow / doPostMicroFlow` →
   `MicroFlowRestPathParser.buildMetadata` → `MicroFlowProxyAppMicroFlow.invokeAppServiceMethod`。
2. **反射分发层**：`InvokeMethodMetadata.invoke()` 按命名约定
   `com.seeyon.{app}.api.microflow.MicroFlowAppService`（facade jar 接口）反射定位 Spring bean 与方法。
3. **生成执行层**（`{app}-biz` jar，`domain.service.microflow.*Service`）：
   每个微流程一个**构建期代码生成**的 Service 类，节点逻辑（RETRIEVE/CREATE_VARIABLE/MAP…）
   以 Java 方法体内联，运行时无逐节点解释器。

**state 过滤判定：执行链全段无 `state` 条件。**
根因是**结构性的**：代理层元数据走 `LoadJarResourceAppService.getRuntimeJsonData`
（jar 内 `@MicroFlow@SERVICE@BaseInfo.json` 构建产物），**从不查询 `udc_microflow_info` 表**
——而 `state` 是该表的列（B-7 §3.1）。执行层直接消费生成类，同样不触 DB。
即：不是"执行时看了 state 然后放行"，而是**整条运行时执行链上 state 列根本不可达**。

> **调用方声明（铁律 30，紧邻判定句）**：本"无 state 条件"判定的**调用方**是
> HTTP 入口 `microflow/{microFlowName}`（GET）/同路径 POST（字节码常量 #388/#389，注释 10.1/10.2），
> **消费方**是运行时执行微流程的三个类：
> `UdcBaseGeneralController`（调用 `MicroFlowProxyAppMicroFlow.invokeAppServiceMethod`）
> → `MicroFlowProxyAppMicroFlow`（调用 `InvokeMethodMetadata.invoke`）
> → `{app}-biz` 生成类（被反射调用）。
> 这条链**不包含**设计态代码生成（消费方 autocode）与前端可见性（消费方 UI 列表）两个场景，
> 故本判定不得外推到那两处。

> 引用纪律（铁律 30）：本判定只覆盖「运行时代理/执行链」这一场景。
> B-7 已证的设计态代码生成链（`selectEntity4Code` 硬过滤 state=20）不受本结论影响——
> 那是构建期路径，消费方是 autocode，不是本契约的运行时链。

### 0.1 DB × jar 配对补证：state 在设计态是**必要条件**（§6 详述）

原 §0 只有"运行时链不读 DB"的**结构性推演**。补一个可证伪的**配对检验**（本应用 47 行 × biz jar 3 个生成类）：

```
                           有生成类   无生成类
state=10 (DRAFT)              0           4      ← 0/4，无例外
state=20 (RELEASE)            3           3      ← 3/6
type=1 (FRONTEND, 27 行)      0          27
type=3 (CUSTOM,  10 行)       0          10
```

→ **state=10 的 SERVICE 流程 0/4 有生成类**（否定侧成立，无例外）；
→ **state=20 侧只 3/6**，不是 100% → 只能写成「state=20 是生成类产出的**必要不充分**条件」。
→ 3 个反例中 **2 个由时间序解释**（`MFSERVICEntaQB9`/`xzhSvcSchcHXa` 的 `update_time`
   晚于 jar 构建时点 2026-10-13 11:32:54），剩 1 个（`xzhMsgBusL1`）同因；
   `MigrationScheduler` 是唯一双向矛盾（jar 有类但 update_time 晚于构建），属**重新发布未重构建**场景。
→ **结论收窄**：不能写"state 决定生成类"，只能写"非 RELEASE 必不生成类"。
   §6 给出完整配对表与时间序检验。

---

## 1. 证据链（逐跳，全部 STATIC 字节码）

### 1.1 入口：`UdcBaseGeneralController`（udc-starter-runtime-5.3.517.jar）

jar 路径：`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`（844KB，346 class）
证据来源：已有解包产物 `docs/audit/artifacts/udc-runtime-5.3.517/r2_endpoints_flat.json`
（jar_sha256 登记，endpoints=133），其中：

```json
{"class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController",
 "member": "doGetMicroFlow",  …}
{"class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController",
 "member": "doPostMicroFlow", …}
```

`javap -v` 常量池（本机 scratch `b8javap/`）：

```
#381 = Utf8   doGetMicroFlow
#387 = Utf8   10.1: 执行 GET 微流程        ← 微流程执行端点注释
#388 = Utf8   microflow/{microFlowName}    ← @GetMapping 路径
#389 = Utf8   host/microflow/{microFlowName}
#390 = Utf8   doPostMicroFlow
#394 = Utf8   10.2: 执行 POST 微流程
#378 = Utf8   dataflow/{entityName}/{restMappingName}   ← 同 Controller 的 dataflow 执行面
```

### 1.2 `doPostMicroFlow` 字节码（javap -c，完整）

```
public java.lang.Object doPostMicroFlow(java.lang.String, java.lang.Object);
  0: aload_0
  1: getfield  #78  // Field microFlowRestPathParser:...MicroFlowRestPathParser;
  4: aload_1
  5: invokevirtual #79 // MicroFlowRestPathParser.buildMetadata:(String)...MicroFlowRestPathMetadataDto;
  9-11: MicroFlowRestRequestDto.fromPost:(Object, MetadataDto)
 16-22: invokevirtual #82 // MicroFlowProxyAppMicroFlow.invokeAppServiceMethod:(MicroFlowRestRequestDto)Object
 25: areturn
```

（doGetMicroFlow 同构，用 `fromGet`。）

### 1.3 路径解析：`MicroFlowRestPathParser.buildMetadata`

同 jar `com/seeyon/boot/starter/udcrt/proxy/MicroFlowRestPathParser.class`。
字符串常量（javap 全量提取）：`/dynamic-rest/com-seeyon/`、`getRuntimeJsonData`、`host`、`name`。

`loadTargetMicroFlowBaseInfo(String, String)` 字节码（完整）：

```
 0: new com/seeyon/ctp/metadata/dto/request/SearchJsonMetadataDto
10: SearchJsonMetadataDto.setAppName(appName)
15: invokestatic MicroFlowControllerProxyUtils.buildBaseInfoJsonFileName:(String)String
18: SearchJsonMetadataDto.setJsonFileName(...)
26: invokeinterface LoadJarResourceAppService.getRuntimeJsonData:(SingleRequest)SingleResponse
52: JsonUtils.toList(String, Map.class) → stream().filter(name==microFlowName).findAny()
93: areturn   // Map<String,Object> 或 emptyMap
```

**关键**：元数据来源 = `com.seeyon.ctp.metadata.api.LoadJarResourceAppService.getRuntimeJsonData`
—— **jar 资源读取，非 DB 查询**。全程无 `select/Mapper/QueryWrapper/state` 引用
（`javap -c` 中 grep state/State/select/Select/Mapper/Repository/QueryWrapper/udc_microflow = **0 命中**）。

### 1.4 元数据文件名：`MicroFlowControllerProxyUtils.buildBaseInfoJsonFileName`

udc-common-5.3.517.jar，字符串常量：**`@MicroFlow@SERVICE@BaseInfo.json`**。

该 json 的生成者 = udc-biz-5.3.517.jar
`com/seeyon/udc/autocode/transport/out/BaseInfoTransportHandler.class`
（`@AutomaticCode` 注解，`transport(CodeContext)→List<SchemaInfo>`，内容为 ApplicationDto/
VersionControl/schemaInfos 的构建期快照）。BaseInfo 字段常量类位于
**udc-plugin-api-5.3.517.jar** `com/seeyon/udc/common/autocode/config/BaseInfo.class`
（字段全部是路径/超类常量：BACKEND/FRONTEND/METADATA/SUPER_*，无 state 语义字段）。

本地三个本应用 jar（biz/facade/web 1.0.7）内**均无** `@MicroFlow@` 资源 →
BaseInfo.json 在 assemble 构建期由平台生成打进部署包（与
`docs/audit/artifacts/udc-assemble-5.3.517-deployed/DEPLOYED-VERSION-NOTE.md` §2
的 BOOT-INF/lib 布局一致）。**此文件实际内容 UNVERIFIED（本地无样本），但不影响结论**：
即使 json 内含 state 字样，Parser 的消费代码（§1.3）也只做 `name` 过滤
（lambda$0 按 microFlowName 过滤，javap 中唯一 filter 谓词参数）。

### 1.5 反射分发：`MicroFlowProxyAppMicroFlow$InvokeMethodMetadata`

同 jar。`invokeAppServiceMethod` 字节码：
`InvokeMethodMetadata.from(request)` → `.invoke()` → displayName 包装 → 返回。

`InvokeMethodMetadata` 常量池中的命名约定字符串（决定性）：

```
com.seeyon.%s.api.microflow.%s
com.seeyon.%s.api.microflow.MicroFlowAppService
[{}]AppService
```

方法引用：`ClassUtils`/`AopTargetUtils`/`ReflectionUtils`/`Method.invoke` —— 纯反射，
**无任何 DB/Mybatis 引用**（常量池 grep mapper/QueryWrapper/udc_ = 0）。

### 1.6 接口与实现（本应用，1.0.7）

- `datamigration9000000000000000001-facade-1.0.7.jar`：
  `api/microflow/MicroFlowAppService.class` = **空标记接口**（javap -v 全文 `{}`，177 bytes）
  `api/microflow/MigrationService.class` = 真实执行接口
  （`syncEnumData / mFCUSTOM9dn28n / getProgressByPlan / syncNowData / executeAll`）
- `datamigration9000000000000000001-biz-1.0.7.jar`（39 class）：
  `appservice/microflow/MicroFlowAppServiceImpl implements ...api.microflow.MicroFlowAppService`，
  方法 `mFSERVICEHbICrp / getMigrationsource` 直通
  `domain/service/microflow/MFSERVICEHbICrpService / GetMigrationsourceService`。
  注册：`registry/DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor` +
  `custom/processor/MicroFlowDubboExportBeanPostProcessor` + `custom/config/DefaultCustomMicroFlowConfig`。

### 1.7 生成执行层：节点逻辑内联（引擎=代码生成）

`GetMigrationsourceService.class` 常量池/局部变量（javap）：

```
_FLOW_INPUT_tiyMkd / _CREATE_VARIABLE_cc4x98 / resp_RETRIEVE_iEnAzJ / _RETRIEVE_iEnAzJ / _FLOW_OUTPUT_qPcOdT
microFlow start microflowName:getMigrationsource caption:1.7
nodeId:CREATE_VARIABLE_UbopxB caption: (1) start CreateVariable
@Autowired ExpressionEvaluator (com.seeyon.boot.starter.formula)
@Autowired DynamicSelectAppService (udcrt)
@UseUdcAppLog(appName="datamigration9000000000000000001")
```

→ 节点（FLOW_INPUT/CREATE_VARIABLE/RETRIEVE/FLOW_OUTPUT）在**构建期**生成 Java 语句，
运行时由 JVM 顺序执行；表达式经 `ExpressionEvaluator` 求值，查询经 `DynamicSelectAppService`。

### 1.8 执行日志面（旁证，同一 jar）

`UdcAppLogHelper.buildActivityStartLog(String, MicroFlowActivityTypeEnum, …)` /
`UdcAppLogService`（RedisTemplate 缓冲 + ExecutorService 异步落日志）。
引用方仅 `UdcRuleLogUtil` / `UdcAppLogAspect` / `UdcAppLogFilter`（AOP/切面记录），
无独立调度器 —— 与「生成类顺序执行 + AOP 记日志」的结论一致。

---

## 2. 引擎不在哪些 jar（扫描范围清单，铁律 9）

| jar（5.3.517 或最新本应用版本） | class 数 | MicroFlow/Exec/Engine/Trigger 类 | actionType 字面量 | 判定 |
|---|---|---|---|---|
| udc-starter-runtime-5.3.517（844KB） | 346 | 23（代理/DTO/枚举/日志） | 仅 MicroFlowActivityTypeEnum 自身 | **代理入口层** |
| udc-starter-dataflow-5.3.517（280KB） | 121 | 0 | 0 | dataflow/扣减 starter，非微流程引擎 |
| udc-biz-5.3.517 | 2312（B-7 §4.2） | 0（B-7 已证） | 仅枚举+NodeDictionary（设计态） | 设计态，无执行引擎 |
| udc-common-5.3.517 | — | 枚举/日志 DTO | 枚举自身 | 契约/枚举库 |
| boot-formula-engine-5.3.318（110KB） | — | 表达式引擎（被生成类消费） | 0 | 表达式求值器，非流程引擎 |
| datamigration…-biz-1.0.7 | 39 | 8（含 2 个生成 Service） | 2 | **生成执行层** |
| datamigration…-facade-1.0.7 | — | api 接口 | 0 | 接口契约 |
| znxmglpt…-biz（1.0.10349–1.0.11228，47 个版本） | 232–499 | `domain.service.microflow` 数量随版本增长 | 同结构 | 同构客户应用（旁证：本应用结构=平台标准产物） |
| xiangmuguanli…-biz（同上 30+ 版本） | 同构 | 同构 | 同构 | 同上 |

### 2.1 「无逐节点解释器」的证法修正（自查发现原写法过弱）

原版本写：「全 repo 探针 `MicroFlowNodeAppService/NodeExecute/executeNode/FlowExecutor/
MicroFlowExecutor/MicroFlowExecution/executeMicroFlow` = **0 命中** → 平台侧不存在任何逐节点执行器」。

**这段话有三个问题，已自查并修正：**

1. **探针选词决定结论**（铁律 9 的典型风险）。换成宽松探针
   （`<含 MicroFlow*DefinitionDto> ∧ <含 exec/invoke/run/dispatch/handle>`）后，
   udc-biz-5.3.517 内**命中 88 个 class** —— 包括 `MicroflowNodeParserFactory`（22 个内部类）
   和 `MicroFlowParser`。若只看窄探针就下"不存在"的结论，等于「查的位置不对就说没有」。

2. **这 88 个 class 经逐个分类后全部是设计态**。对 `*Microflow*Parser*` 6 个非内部类做
   全量签名分类（`b8_parser_classify.py`）：

   | class | 方法数 | 主方法返回 | 判定 |
   |---|---|---|---|
   | `MicroflowNodeParser` | 1 | `Collection<Relation>` | 依赖/引用解析 |
   | `MicroflowNodeParserFactory` | 19 | `Collection<Relation>` | 依赖/引用解析（22 个 node-type 分支） |
   | `MicroflowReferenceParser` | 12 | `Collection<Relation>` | 依赖/引用解析 |
   | `MicroFlowParser` | 20 | `MicroFlowDeserializationResult` / `List<BaseNode>` / `MicroFlowBo` | **JSON→BO 反序列化** |
   | `MicroFlowParserUtils`（udc.microflow.util） | 33 | `MicroFlowDeserializationResult` / `List<BaseNode>` | 反序列化工具 |
   | `MicroFlowParserUtils`（autocode.v27.utils） | 8 | `boolean hasTargetNode(...)` | 构建期节点查询 |

   其中 `MicroFlowParser` 的方法名为 `deserialize / parseRoot / parseRootWithoutNodes / node /
   trigger / input / addNodeDependency` —— **是 schema 反序列化，不是执行**。
   `MicroflowNodeParserFactory` 是「按 node type 分派到 22 个 Relation 提取器」
   （常量池 `missing node type:{}`、`parsers: Map<String, MicroflowNodeParser>`），
   唯一调用方 `MicroflowReferenceParser`，最终返回 `Collection<Relation>` 供
   `ReferenceChecker`/`RelationService` 使用 —— 即 B-7 已证的设计态引用解析链。

3. **判据改成签名特征，不是名字匹配**：
   - 执行器签名特征 = 入参 `MicroFlowDefinitionDto`/`BaseNode`，**返回 void 或执行结果**，
     且常量池含 udcrt 执行服务（`ExpressionEvaluator`/`DynamicSelectAppService`/`UdcAppLogHelper`）。
   - 上述 6 个 class **无一满足**（返回类型全是 `Collection<Relation>` 或反序列化结果）。
   - 反过来，满足该特征的类只有 `{app}-biz` 里的**生成类**（§1.7）。

→ **结论不变但证法加强**：平台侧无逐节点解释器；"执行"以**构建期代码生成**实现。
   原「0 命中」表述已作废，改为本节的全量分类证据。

---

## 3. state 过滤判定（本切片的验收核心）

**判定：无。证据等级 STATIC。**

- 代理层：`MicroFlowRestPathParser` 全 class 无 state/DB 引用（§1.3）；
  元数据 = jar 内 json 资源（§1.4）。
- 分发层：`InvokeMethodMetadata` 纯反射，无 DB（§1.5）。
- 执行层：生成类直接消费，节点逻辑构建期内联（§1.7），不读 `udc_microflow_info`。
- **调用方声明（铁律 30）**：本链的调用方是 HTTP 入口
  `microflow/{microFlowName}`（GET）/同 POST（注释 10.1/10.2），
  消费场景是「运行时执行微流程」，与 B-7 §3.2 的前端可见性场景、§3.1 的设计态代码生成场景
  三者互斥，不互推。

**对 B-7 遗留#1 的回答**：「运行时是否执行 state=10 宿主」→ 运行时执行链不读
`udc_microflow_info`，`state` 列在执行链上不可达 → 该问题的提法本身失效；
真正决定"能不能执行"的是**构建产物里有没有对应的生成类 + BaseInfo.json 有没有该流程条目**
（发布动作产出这两者，B-6/D9「一次成功发布即产出运行态行」与此互证）。

## 4. 遗留 / UNVERIFIED

| # | 项 | 状态 | 下一步证据源 |
|---|---|---|---|
| 1 | `@MicroFlow@SERVICE@BaseInfo.json` 实际内容（字段/是否含流程清单） | UNVERIFIED（本地无样本） | test2 部署态 fatjar 逐 entry 读（同 R21 P1 纪律） |
| 2 | `MigrationService.executeAll`（全量执行）与 `MigrationSchedulerService` 的调度关系 | UNVERIFIED（本轮未展开，属域内下一片） | `MigrationSchedulerService` 字节码 |
| 3 | 表达式 `ExpressionEvaluator` 的求值契约 | 已有独立契约（8085235 表达式契约），未重复验证 | — |

## 5. 边界与红线

- 0 次 /service、0 写、未 push；全部证据来自本地 jar 常量池/javap 与既有解包产物。
  **例外声明（铁律 2）**：§6 的配对检验用了 **1 次只读 DB 查询**（`SELECT ... FROM udc_microflow_info
  WHERE app_id=8704025620829192834`，47 行），不是 /service 调用，不写库。
  这是把 §0 的结构性推演变成可证伪检验所必需的；§0–§5 的 STATIC 定性不受影响，
  §6 单列证据等级 **STATIC+DB-READ**（不是 LIVE —— 没有真实执行回读）。
- 未动 B-6/B-7 已结项内容；未扩到 21 节点全采集（B-1 仍绑 SSO 窗口）。
- 复现：`javap -p -c com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController`
  等本文所列类，classpath 指向 `<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/`。

---

## 6. DB × jar 配对检验：state 在设计态是**必要不充分**条件

> 证据等级：**STATIC + DB-READ**（jar 字节码 + 1 次只读 DB）。**不是 LIVE**（无真实执行回读）。
> 脚本：`<HERMES_HOME>/cache/scratch/impl/b8_state_vs_genclass_v2.py`（EXIT=0）

### 6.1 配对表（本应用 type=0 SERVICE，n=10）

jar 内 `domain/service/microflow/` 生成类 = **3 个**：
`GetMigrationsourceService` / `MFSERVICEHbICrpService` / `MigrationSchedulerService`。

| flow name | state | 节点数 | jar 生成类 | update_time |
|---|---|---|---|---|
| xzhFinalAllNodes | 10 | 30 | — | 2026-10-16 23:57:15 |
| xzhStdReal31046 | 10 | 28 | — | 2026-10-16 14:10:45 |
| xzhSvcDefK4Ge | 10 | 5 | — | 2026-10-15 18:17:44 |
| xzhSvcEvtBpDA | 10 | 4 | — | 2026-10-16 20:09:54 |
| MFSERVICEHbICrp | 20 | 6 | ✅ MFSERVICEHbICrpService | 2026-10-12 17:15:20 |
| MigrationScheduler | 20 | 2 | ✅ MigrationSchedulerService | 2026-10-14 14:41:57 |
| getMigrationsource | 20 | 7 | ✅ GetMigrationsourceService | 2026-10-12 17:15:20 |
| MFSERVICEntaQB9 | 20 | 2 | — | 2026-10-16 01:19:18 |
| xzhSvcSchcHXa | 20 | 4 | — | 2026-10-16 05:17:45 |
| xzhMsgBusL1 | 20 | 1 | — | 2026-10-16 19:50:34 |

四格：

```
state=10 & 有生成类 : 0 / 4   ← 否定侧无例外
state=10 & 无生成类 : 4
state=20 & 有生成类 : 3 / 6
state=20 & 无生成类 : 3       ← 肯定侧有反例，H 不能写成充要条件
```

跨类型：type=1（FRONTEND，27 行）0 个生成类；type=3（CUSTOM，10 行）0 个生成类。

### 6.2 时间序检验：3 个反例中有 2 个被"jar 构建时点"解释

biz jar 的 zip entry 时间 = **2026-10-13 11:32:48–11:32:56**（生成类均 11:32:54），
jar mtime 2026-10-13 11:36:49。以构建时点 11:32:54 切：

| flow | 有类? | update_time | update < build? | 一致? |
|---|---|---|---|---|
| MFSERVICEHbICrp | 有 | 10-12 17:15 | 是 | ✅ |
| getMigrationsource | 有 | 10-12 17:15 | 是 | ✅ |
| MigrationScheduler | 有 | 10-14 14:41 | 否 | ❌ 唯一矛盾 |
| xzhSvcDefK4Ge | 无 | 10-15 18:17 | 否 | ✅ |
| MFSERVICEntaQB9 | 无 | 10-16 01:19 | 否 | ✅ |
| xzhSvcSchcHXa | 无 | 10-16 05:17 | 否 | ✅ |
| xzhStdReal31046 | 无 | 10-16 14:10 | 否 | ✅ |
| xzhMsgBusL1 | 无 | 10-16 19:50 | 否 | ✅ |
| xzhSvcEvtBpDA | 无 | 10-16 20:09 | 否 | ✅ |
| xzhFinalAllNodes | 无 | 10-16 23:57 | 否 | ✅ |

**一致 9 / 矛盾 1。** 唯一矛盾 `MigrationScheduler`（jar 有类但 update 晚于构建）
= **发布后改过、构建未跟上**，属构建产物与 DB 的快照时差，不是 state 语义。

→ 因此「state=20 但无生成类」的 3 例**全部**可由两件事解释：
① update_time 晚于 jar 构建时点（3/3 成立）；② `MigrationScheduler` 的逆向矛盾也是时差。
**不需要引入"state 之外还有闸门"的额外假设**，但也不能证明 state=20 就必然生成。

### 6.3 结论（必须这样写，不能更强）

- ✅ **可断言**：本应用 type=0 且 `state=10`(DRAFT) 的流程 **0/4 无生成类** ——
  `state≠RELEASE` 是"不产出生成类"的**必要条件**侧证据（无例外）。
- ✅ **可断言**：生成类存在 ⟹ 该流程当时是 `state=20`，且构建时点晚于其发布
  （9/10 一致，1 例为构建未跟上）。
- ❌ **不可断言**："state=20 就必然产出生成类"（3/6）、"state 决定生成类"（因果）。
  3 个缺失例全由时间序解释，样本无法把 state 与"发布后是否重构建"分离。
- ⚠️ **仍然 UNVERIFIED**：`@MicroFlow@SERVICE@BaseInfo.json` 是否也按 state 过滤
  （见 §4 遗留#1）。这是运行时链的关键一环，本地无样本。

### 6.4 与 B-7 的关系（不越界）

> **0/4 的权威源声明（铁律11）**：本文 `0/4` 共 6 处。其中 **§0.1 代码块（L47）** 与
> **§6.1 四格（L319）** 是**权威事实源**，各有逐行断言保护；其余（§0.1 叙述 L53、
> §6.3 正文 L354、本章两条引用 L366/L369）是**引用**，不是独立事实源。
> 改任何一处引用都必须先改权威源；闸门对这三处引用加**禁止改动断言**（见 b8_gate
> 「0/4 引用禁止改动」段），防止被静默篡改。

- B-7 §3.1 已证 `selectEntity4Code` **硬过滤 `RELEASE.code()==20`**（字节码）。§6.1 的
  0/4 是该字节码过滤的**DB 侧配对印证**，不是新机制。
- B-7 的**统计结论**（映射节点与 state 的关联）仍是 `UNVERIFIED 无法定论`（auditor D56 后定稿）。
  §6 **不触碰、不支持、不推翻**该统计结论 —— 两者样本与命题都不同（这里是"有无生成类"，
  不是"含不含映射"）。**禁止把 §6 的 0/4 引用为 B-7 统计结论的证据。**


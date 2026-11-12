# Service 业务流转：方法背后动了什么

## 1. Capability

回答写扩展代码时真正要问的问题：**「我调这个方法，它实际会动哪些业务组件、落哪些表、发什么事件」**。

方法签名只告诉你传什么、返回什么；DTO 字段告诉你传的内容长什么样。
但「这一步之后系统会发生什么」——只有反编译方法体才能看到。

## 2. Version

同 `BASELINE.md`。本格产物基于仓库现有 jar（udc-biz 5.3.517、客户应用 biz 各自版本）。

## 3. Input

```
javap -p -c 每个业务类
  → 按方法切块
  → 提 `// Method a.b.C.m:(...)` 调用目标
  → 过滤 java.* / spring / slf4j / apache 噪音
  → 按 Dao / Service / Util / Event / Other 分类
```

## 4. Required

读之前先知道两层结构：

| 层 | 类形态 | 干什么 |
|---|---|---|
| **门面层** | `XxxAppServiceImpl`（implements `XxxAppService`） | 几乎全是**一行转发**，校验参数后交给业务层 |
| **业务层** | `domain/service/XxxService`（具体类，不是 `XxxServiceImpl`） | 真正的业务：查库、发事件、多线程、配置判断 |

⚠️ 平台的业务 Service 常是**具体类**（`udc/collaboration/domain/service/AppCollaborationService`），
不是 `XxxServiceImpl`。只扫 `*Impl.class` 会漏掉整个业务层——这是第一版抽空了的原因。

## 5. Execution

```
① 知道方法名 → 在 <构件>-appservice.md 找门面，看它转发给谁
② 顺着那个 Service → 在 <构件>-domain.md（或客户 biz 文件）找它的方法体
③ 读那一节的 Dao/Service/Event 行 = 这个方法真实的动作序列
④ 要传什么 → 回到 appservice-dto-fields.md 查 DTO 字段
```

## 6. Side Effects

无（只读反编译产物）。但读出来的动作序列就是**副作用清单**：
`Dao.insert` = 落库、`EventBus.publishAfterTransaction` = 事务提交后发事件、
`MultiThreadTransaction.executeSplit` = 分批并发。

## 7. Known Constraints

### 7.1 产物在哪

`docs/audit/artifacts/service-flow-20261103/`

| 文件 | 内容 | 规模 | 调用统计 |
|---|---|---|---|
| `udc-biz-appservice.md` | UDC 门面层 83 个 AppServiceImpl | 151 KB | Dao 41 / Service 688 / Util 287 / Event 52 |
| `udc-biz-domain.md` | **UDC 业务层 265 个类**（collaboration/page/metadata/autocode/detection） | 646 KB | Dao 706 / Service 1099 / Util 4355 / Event 261 |
| `znxmglpt…-biz.md` | 客户应用「项目管理平台」458 个 ServiceImpl | 2.4 MB | Dao 105 / Service 13019 |
| `xiangmuguanli…-biz.md` | 客户应用「项目管理」130 个 | 719 KB | Dao 147 / Service 3885 |
| `datamigration…-biz.md` | 客户应用「数据迁移」27 个 | 164 KB | Service 901 |
| `bpm-biz-appservice.md` | **BPM 门面 52 类** | 143 KB | Dao 21 / Service 628 / Util 394 / Event 4 |
| `organization-biz-appservice.md` | **组织 53 类** | 326 KB | Dao 678 / Service 2253 / Util 887 / Event 4 |
| `cip-capability-biz-appservice.md` | 连接器能力 132 类 | 323 KB | Dao 128 / Service 2936 / Util 1985 / Event 24 |
| `cip-connector-biz-appservice.md` | 连接器 97 类 | 180 KB | Dao 14 / Service 1146 / Util 1024 / Event 41 |
| `ctp-user-biz-appservice.md` | 人员 50 类 | 74 KB | Dao 15 / Service 346 / Util 214 |
| `cdp-data-biz-appservice.md` | 数据平台 55 类 | 82 KB | Dao 11 / Service 43 / Util 93 |
| `ctp-affair-biz-appservice.md` | 事项 10 类 | 21 KB | Dao 1 / Service 90 / Util 35 |
| `app-common-biz-appservice.md` 等 | 应用通用等 5 个 | 41 KB | — |

客户应用的 biz 是**平台按元数据生成**的 ServiceImpl（每个实体一套 CRUD），
所以能看到「一个业务动作 → 哪些实体的 Service → 哪些 Dao」的完整链路，
是理解平台业务组织方式最好的样本。

### 7.2 典型流转一：查询组装（`AppCollaborationService.selectCollaborativeAppNames()`）

```
Wrapper.and              ← 构造查询条件
Example$Criteria.andEqualTo
AppCollaborationEntityDao.selectListByWrapper   ← 落库查询
MultiThreadTransaction.executeSplit             ← 多线程分批
Apps.getRequestContext / RequestContext.getUserId  ← 取当前用户
```

读法：**条件怎么拼 → 查哪张表 → 要不要分批 → 依赖哪些上下文**。

### 7.3 典型流转二：事件驱动（`ConsistenceDetectionService.deleteDetection4Dto()`）

```
DetectionProperties.isDeleteFirst      ← 配置开关先判断
BaseTraceableDto.getId                 ← 取标识
PartDetectionDeleteEvent.builder       ← 构造事件（appId / deleteDtoList / domainClazz）
EventBus.publishAfterTransaction       ← 事务提交后才发
```

读法：**先看配置 → 再构造事件 → 事务后发**。
`publishAfterTransaction` 是关键：事件在事务提交后才投递，所以监听方看到的数据一定是已提交的。
写扩展要挂这个流程，监听 `PartDetectionDeleteEvent` 即可，不用改业务代码。

### 7.4 典型流转三：客户应用的生成式 Service

`znxmglpt…-biz` 里 458 个 ServiceImpl、13019 次 Service 调用，几乎全是这种形态：

```
XxxServiceImpl.save(SingleRequest<XxxDto>)
  → 校验（EntityRuleUtil / EntityAuthHelper）
  → 组装实体（Dto→Entity 转换）
  → XxxEntityDao.insert / update
  → 触发特性/事件（AppFeature / EventBus）
```

这说明**平台的业务骨架是固定的**：校验 → 转换 → 落库 → 触发。
客开要在某个环节插一手，不用重写，挂对应的扩展点（`@EntityAttribute` 校验、
`AppFeature` 特性、`DetectionTask` 检测）就行。

### 7.5 拿不到的东西（别指望从这里得到）

**① 业务规则本身**
字节码只有调用，没有「为什么」。比如「金额超过 10 万要二级审批」这种规则，
只能从 `if` 比较的常量 + 配置项反推，不保证完整。

**② SQL 语句**
实测 109 个 jar 里只有 **8 个 mapper XML**，平台基本不用 XML SQL
（走 `boot-starter-dynamicsql` 动态拼 + MyBatis-Plus Wrapper）。
所以「查哪张表」只能从 `XxxEntityDao` 的类名推断，看不到真实 SQL。

**③ 参数的实际取值**
`parameterData` 是 `Map<String,Object>`，键是什么、值从哪来，字节码里没有。

**④ 运行时分支走哪条**
同一个方法有多个 `if` 分支，只有真实请求才知道走哪条。

### 7.6 与 DTO 字段表配合用

```
签名     → packages/<构件>.md / domains/<域>.md      （传什么类型）
字段     → dto-fields/<域>.md                        （类型里有什么）
流转     → service-flow-20261103/<构件>.md            （调了之后发生什么）
```

三份合起来才够写一段能跑的扩展代码。

## 8. Evidence

```
docs/audit/artifacts/service-flow-20261103/   16 份 / 5.2 MB
  平台实现（<MAVEN_REPO>-extra，21 个 *-biz jar）
    bpm-biz-appservice.md            143 KB / 52 类
    organization-biz-appservice.md   326 KB / 53 类
    cip-capability-biz-appservice.md 323 KB / 132 类
    cip-connector-biz-appservice.md  180 KB / 97 类
    ctp-user-biz / cdp-data-biz / ctp-affair-biz / ctp-message-biz / cip-manager-biz …
  UDC（<MAVEN_REPO>）
    udc-biz-appservice.md  151 KB / 83 类（门面层）
    udc-biz-domain.md      647 KB / 265 类（业务层）
  客户应用
    znxmglpt…-biz.md       2.4 MB / 458 类
    xiangmuguanli…-biz.md  720 KB / 130 类
    datamigration…-biz.md  165 KB / 27 类

实现 jar 来源 http://10.0.0.1/artifactory/libs-release/com/seeyon（只读 GET，21 个 *-biz，40 MB）
⚠️ 仓库无 -sources.jar，是反编译 class 不是读源码

生成器 tools/core/platform/emit_service_flow.py
  --repo <仓库根> --pkg <构件...> [--only-impl | --paths <路径片段...>] [--suffix=-xxx]
  闸门：单个构件抽到的类 < 5 则跳过（不中断整批）

踩过的坑
  ① javap -c 的调用行是 `// Method com/seeyon/...`，正则不含 `/` 就一条都抽不到（第一次跑 0 个类）
  ② 业务 Service 是具体类不是 XxxServiceImpl，只扫 *Impl 会漏掉整个业务层（151 KB vs 646 KB 的差别）
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 每个方法调了哪些 Dao/Service/Util/Event | `VERIFIED_STATIC_BYTECODE`（javap -c 原文） |
| 「门面层只转发、业务在 domain/service」 | `VERIFIED_STATIC_BYTECODE`（逐类比对） |
| 平台不用 XML SQL（109 jar 仅 8 个 xml） | `VERIFIED_STATIC_BYTECODE`（jar 目录扫描） |
| 业务规则语义 | **UNVERIFIED**（字节码无注释，需业务文档或实测） |
| 实际执行的 SQL | **UNVERIFIED**（动态拼接，运行期才成形） |
| 分支实际走向 | **UNVERIFIED**（需真实请求） |

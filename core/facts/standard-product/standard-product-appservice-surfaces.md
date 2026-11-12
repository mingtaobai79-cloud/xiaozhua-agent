# standard-product｜标品 AppService 接口面（环境无关）

> 本格只讲**包内有什么方法、签名是什么**。不涉及任何具体应用/工程/环境。
> 适用：扩展代码要调标品能力（组织/BPM/事项/文件/枚举/系统变量/连接器）时查「调哪个类、什么签名」。

分级：`VERIFIED_STATIC_BYTECODE`（javap 逐类，见 §8）。

## 1. Capability

回答「这个平台能力在哪个 AppService、方法叫什么、出入参什么形态」。
本格是**方法名与签名的索引**，不是语义文档：语义要回各域契约。

覆盖 8 个标品域（顶层规模，全部实测）：

| 域 | artifact | 类 | 接口 | 方法 |
|---|---|---|---|---|
| 组织 | `organization-facade` | 391 | 51 | 6108 |
| BPM | `bpm-facade` | 533 | 40 | 5893 |
| 事项 | `ctp-affair-facade` | 122 | 13 | 1442 |
| 用户 | `ctp-user-facade` | 263 | 44 | 2987 |
| 连接器 | `cip-connector-api` / `cip-connector-facade` | 119 / 121 | 23 / 15 | 1504 / 1165 |
| 文件 | `boot-starter-file` | 89 | 8 | 1045 |
| 枚举 | `boot-starter-enums` | 51 | 4 | 754 |
| 系统变量 | `boot-starter-systemvariable` | 4 | 0 | 147 |

## 2. Version

见 §8 证据表（各 artifact 版本号；同族构件是同一主版本线）。

## 3. Input

各 facade / starter jar（坐标 = `com.seeyon:<artifact>:<ver>`）；
抽取命令见 §8。

## 4. Required

无前置（纯静态读 jar）。

## 5. Execution

按包前缀抽 javap 签名面 → 按「能力关键词」归组。见 §7。

## 6. Side Effects

只读 jar。

## 7. Known Constraints

### 7.1 组织域（`organization-facade`）—— 分「Base / Core」两套

```
OrgCommonAppService(35)          跨实体公共查询（查人/查部门/查管辖/查角色）
OrgWorkFlowAppService(30)        选人组件与流程匹配专用
OrgUnitBaseAppService(20)        部门：CRUD + 级联查
OrgMemberBaseAppService(16)      人员：CRUD + 级联查
OrgLevelBaseAppService(14)       层级
OrgPostBaseAppService(14)        岗位
OrgMemberPostBaseAppService(12)  人员岗位关系
OrgMemberRoleBaseAppService(11)  人员角色关系
OrgRoleBaseAppService(11)        角色
OrgJobBaseAppService(14)         职务
OrgMetadataCoreAppService(12)    组织元数据
```
同级还有 `*CoreAppService`（6~13 方法），**Base 与 Core 是一对**：Base 面大、Core 面小而稳。
另有 `Ocip*AppService`（OCIP 组织同步，`OcipUnitAppService` 8 / `OcipMemberAppService` 4）。
引用前先确认是 Base 还是 Core（两者都可能只在其中一个里有你要的方法）。

实测签名样例（组织侧固定形态，与 AppService 通用约定一致）：

```java
// OrgMemberBaseAppService
SingleResponse<Long>            create(SingleRequest<OrgMemberDto>)
SingleResponse<Integer>         update(SingleRequest<OrgMemberDto>)
SingleResponse<OrgMemberDto>    selectById(SingleRequest<Long>)
ListResponse<OrgMemberDto>      selectByIds(SingleRequest<List<Long>>)
ListResponse<OrgMemberDto>      selectCascadeListByConditions(ListRequest)
PageResponse<OrgMemberDto>      selectPageByConditions(PageRequest)
PageResponse<OrgMemberDto>      dynamicSelect(PageRequest)

// OrgCommonAppService（跨实体查询，返回 id 列表或 Map）
ListResponse<Long>              selectMemberByOrgId(SingleRequest<Long>)
PageResponse<Long>              selectPageMemberByOrgId(PageRequest)
SingleResponse<Boolean>         isMemberInSelectPeopleDataJson(...)
SingleResponse<OrgUnitCoreDto>  selectRoot(SingleRequest<?>)
```

关键词检索：查人 → `selectMember*`；查部门 → `selectOrg*` / `selectUnit*`；级联 → `selectCascade*`；
管辖/权限 → `selectManageOrgByRole` / `canManage` / `selectInOrgScopeIds`；选人组件 → `SelectPeopleData`。

### 7.2 BPM 域（`bpm-facade`）—— 发起/流转/模板三段

```
BpmAppService(22)                  事项操作：发起与流转
BpmTemplateAppService(32)          流程模板：发布/启停/授权
BpmApiTransportAppService(6)       流程模板导入导出
BpmApiProcessAppService(1)         发起
BpmApiFormPermissionAppService(12) 表单权限
BpmDeployAppService(6)             部署
BpmProcessLogAppService(5)         流程日志
BpmApiNodePermissionAppService(4)  节点权限
BpmThirdTemplateSyncAppService(4)  第三方模板同步
BpmUdcApiService(4)                ★ UDC 专用（见下）
BpmSuperviseAppService(3)          督办
BpmOpinionAppService(2)            意见
BpmCaseAppService(2)               案件
BpmAutoApprovalAppService(4)       自动审批
```

`BpmAppService` 实测方法名（发起与流转的完整动作集）：

```java
SingleResponse<BpmSendResultDto>        send(SingleRequest<?>)
SingleResponse<BpmSubmitResultDto>      submit(...)
SingleResponse<BpmSaveDraftResultDto>   saveDraft(...)
SingleResponse<CommonResultDto>         stepBack / repeal / stop / takeBack / replace / multipleReplace
ListResponse<BpmPauseResponseDto>       pause / cancelPause
SingleResponse<BpmCaseFullInfo>         selectFullCaseInfo(...)
SingleResponse<ChangeNodeResponseDto>   counterSignNode / addNode
ListResponse<BpmItemInfoDto>            addExecuteMember(...)
ListResponse<BpmBatchResponseDto>       batchDeal(...)
SingleResponse<Void>                    deleteDraft / deleteDraftAffair
```

★ **`BpmUdcApiService` 是 UDC 与 BPM 的接缝**（实测 4 个方法，全部以 `ForUdc` 结尾，命名刻意区分）：

```java
SingleResponse<BpmApiSendApiResponseDto>  sendForUdc(...)
SingleResponse<Void>                      repealForUdc(...)
SingleResponse<CommonResultDto>           stopForUdc(...)
SingleResponse<Void>                      deleteCaseByIdForUdc(...)
```

⇒ UDC 侧发起/撤销/终止流程走这四个；**不要**直接调 `BpmAppService.send`（那是标品内部入口，
不承担 UDC 的入参校验与租户/应用隔离）。

### 7.3 事项域（`ctp-affair-facade`）—— 待办/待阅

```
AffairCommonAppService(47)      待办公共操作（面最大）
AffairOpenAppService(12)        对外开放接口
AffairNodePermissionAppService(5)
AffairMicroflowAppService(4)    ★ 微流程专用
AffairCategoryAppService(3)     事项分类
AffairSuperviseAppService(3)
AffairCustomOperationAppService(1)
AffairDataScopeAppService(1)
AffairUdcAppService(1)          ★ UDC 专用
```

⇒ 与 BPM 同模式：UDC/微流程各有一个专属接缝接口（`AffairUdcAppService` / `AffairMicroflowAppService`），
通用场景才用 `AffairCommonAppService`。

### 7.4 文件域（`boot-starter-file`）—— 存储抽象 + SPI

```
StorageService(14)        统一存储入口（多实现：本地/OSS/…）
StorageSpi(9)             存储 SPI：upload/download/copy/exist + 三个桶名
V5StorageSpi(4)           V5 兼容存储 SPI
StorageKeyGenerator(4)    storageKey 生成与解析
ICoder(3)                 加解密
WaterMarkControl(1)       下载水印控制
FileInfoProxy(1)
FileDao(0)
```

```java
// StorageService
String          getStorageType();
void            init();     void shutdown();
UploadResultDto upload(...);
InputStream     download(...);      boolean delete(...);   boolean exist(...);
// StorageSpi —— 桶名由 SPI 提供，不要写死
String getPrivateBucketName(); String getPublicBucketName(); String getFerryboatBucketName();
```

⇒ 要接自建对象存储：实现 `StorageSpi`，**不要**改 `StorageService`（那是聚合入口，按 type 路由到 SPI）。
桶分三类（private/public/ferryboat），落文件前先确定归哪类。

### 7.5 枚举域（`boot-starter-enums`）—— Service 有三层

```
CtpEnumService(68)         枚举定义
CtpEnumItemService(135)    枚举项（面最大）
CtpEnumCategoryService(36) 枚举分类
CtpEnumAppService(19)      appservice 面（出入参走 transport）
```

```java
// CtpEnumAppService —— 走 transport 包装
SingleResponse<Long>           create(SingleRequest<CtpEnumDto>)
SingleResponse<Integer>        update(...)
SingleResponse<Integer>        deleteByIds(...)
SingleResponse<CtpEnumDto>     selectById(...)
ListResponse<CtpEnumDto>       selectByIds(...)
SingleResponse<Long>           copyById(...)
SingleResponse<Integer>        createOrUpdateBatchForOnlypage(...)   // 页面保存专用
SingleResponse<Integer>        updatePresetBatch(...)                 // 预制数据批量
```
Service 层（`CtpEnum*Service`）返回裸类型（`Long`/`Integer`/`Dto`），不套 transport ——
**Service 是 domain 层，AppService 才是契约层**，两者风格不同不是错。
`CtpEnumItemService` 内含 `checkNameUnique` / `checkValueUnique` / `checkEnumType`（校验在 Service 层）。

### 7.6 系统变量域（`boot-starter-systemvariable`）—— 三个类吃完

```
SystemVariableUtils(126)  静态工具面（最常用）
SystemVariableService(13) 实例服务面
SystemVariableKeyEnum(5)  变量 key 枚举
EnvFunction(3)            环境函数（语言/密钥开关）
```

```java
// SystemVariableUtils —— 取当前上下文（扩展代码里最常要的东西）
Long        currentUserId();
Long        currentOrgId();
Long        currentLegalOrgId();
Long        rootInstitutionId();
String      currentUserName();  String currentUserCode();  String currentUserLoginName();
String      currentUserType();
List<T>     getCurrentMultiOrgInfo();
List<Long>  currentMultiOrgId();  List<String> currentMultiOrgCode();  List<String> currentMultiOrgName();
Long>       getOrgPath(...);
```
⇒ 要「当前用户/当前单位/当前部门」**一律用 `SystemVariableUtils`**，不要自己去 `Session`/`ThreadLocal` 取。

### 7.7 连接器域（`cip-connector-api`）—— 连接器的扩展点是一族 Provider

```
DataBaseExecutorService(14)            数据库执行器
MobileConfigProviderService(14)        移动端配置
MobileApplicationProviderService(10)   移动应用
MobileOrgSyncProviderService(9)        移动组织同步
LinkerSecurityService(9)               认证/鉴权
SsoService(7)                          单点登录
BaseConfigAppService(11)               基础配置
LinkerAppService(10)                   连接器本体
LinkerMigrationAppService(4)           连接器迁移
LinkerEnumAppService(1)
ApplicationPluginStatusAppService(2)
```

⇒ 连接器的可扩展面**集中在 `*ProviderService` / `*Service` 接口**：接一个新系统 = 实现对应的 Provider
（配置/安全/同步各一类），而不是改 `LinkerAppService`。
`MobileConfigProviderService` 与 `LinkerSecurityService` 都有 `jsonCheck`（配置校验）与
`getPageJson`（配置界面）—— 实现一个 Provider 时要同时提供「配置界面描述」与「配置校验」。

### 7.8 逐字签名全量表（本格只到方法名级，全签名在 `domains/`）

§7.1~7.7 给的是「有哪些接口、各有多少方法、关键方法名」，够判断走哪条路。
真要照抄签名（参数类型、返回泛型、是不是 default）看逐字表：

`docs/audit/artifacts/extension-surface-20261029/domains/<域>.md`

| 域 | 文件 | 接口 | 关键类 | 方法 |
|---|---|---|---|---|
| Dubbo 跨服务调用 | `dubbo.md` | 4 | 6 | 220 |
| BPM 流程 | `bpm.md` | 40 | 24 | 5893 |
| 组织架构 | `organization.md` | 55 | 3 | 6409 |
| MyBatis / Dao | `mybatis.md` | 44 | 18 | 878 |
| 数据源 | `datasource.md` | 2 | 4 | 622 |
| 连接器 | `connector.md` | 28 | 4 | 1971 |
| 事项 | `affair.md` | 13 | 2 | 1442 |
| 单据转文档 | `formconvert.md` | 2 | 14 | 402 |
| 表达式 | `formula.md` | 21 | 15 | 1547 |
| 系统变量 | `systemvariable.md` | 0 | 2 | 147 |
| 文件存储 | `file.md` | 8 | 20 | 1045 |

生成：`python tools/core/platform/emit_domain_surfaces.py --interfaces <interfaces.json> --emit-dir <domains>`

⇒ 分工：**本格定方向**（该找哪个域、哪个接口），`domains/*.md` **抄签名**。
BPM 例：`BpmAppService`（26 方法）全部入参 `SingleRequest<XxxDto>`、返回 `SingleResponse`/`ListResponse`；
`consult` / `hasten` / `monitorNodeRun` / `check` 是 `default` 方法，其余是 abstract。

### 7.9 按构件一包一份（覆盖 pom 里每一个标品依赖）

`domains/` 是按业务场景合并的视角；要确认**某个 pom 依赖里到底有什么**，看按构件的：

`docs/audit/artifacts/extension-surface-20261029/packages/<构件名>.md`

共 **91 份**（扩展工程 pom 里的 86 个标品构件 + 后补的 udc-biz / udc-web / udc-cicd /
udc-extend / udc-plugin-api），合计 3.1 MB。每份含：接口全签名 / 关键类全签名 / 注解元素 / 枚举常量。

| 构件 | 大小 | 类 | 段 |
|---|---|---|---|
| `udc-biz` | 1053 KB | 1855 | 652 |
| `udc-starter-runtime` | 124 KB | 307 | 104 |
| `cip-capability-facade` | 117 KB | 490 | 79 |
| `boot-core` | 102 KB | 512 | 134 |
| `organization-facade` | 93 KB | 414 | 59 |
| `bpm-facade` | 83 KB | 533 | 84 |
| `udc-plugin-api` | 77 KB | 307 | 96 |
| `boot-starter-datamigration` | 73 KB | 247 | 88 |
| `boot-starter-mybatis` | 64 KB | 138 | 75 |
| `boot-starter-excel` | 61 KB | 72 | 28 |
| `ctp-user-facade` | 56 KB | 263 | 59 |

生成：`python tools/core/platform/emit_package_surfaces.py --interfaces <interfaces.json> --emit-dir <packages>`

⇒ 两个视角别混：
- 问「我要做 X，该用哪个域/接口」→ `domains/`（bpm / organization / connector …）
- 问「我 pom 里这个依赖能干什么」→ `packages/`（一包一份，86 个截图构件一个不缺）

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/
        batch2/organization-facade.json / bpm-facade.json / ctp-affair-facade.json
        batch2/ctp-user-facade.json / cip-connector-api.json / cip-connector-facade.json
        batch2/boot-starter-file.json / boot-starter-enums.json / boot-starter-systemvariable.json
        batch2/_index.json（84 包汇总：7255 类 / 758 接口 / 70990 方法）
② 复现  uv run --no-project python tools/core/platform/extract_surface_batch_par.py \
          --targets <targets.json> --emit-dir <out> --progress <out>/_progress.jsonl \
          --javap <javap 原生路径> --workers 10 --limit 1000
③ 校验  本格每个类名+方法名+返回类型都能在对应 batch2/<artifact>.json 的
        classes[].symbols.methods[] 里逐字命中；
        顶层类/接口/方法数取自 _progress.jsonl（84 条，成功 84）。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 8 个域的类/接口/方法数 | `VERIFIED_STATIC_BYTECODE`（javap 逐类） |
| 组织 Base/Core 成对结构与方法名 | `VERIFIED_STATIC_BYTECODE` |
| BPM 三段与非公开入口 `ForUdc` 四方法 | `VERIFIED_STATIC_BYTECODE` |
| 事项 UDC/微流程专属接缝接口 | `VERIFIED_STATIC_BYTECODE` |
| 文件 Storage SPI 三桶名 | `VERIFIED_STATIC_BYTECODE` |
| 枚举 Service→AppService 风格差异 | `VERIFIED_STATIC_BYTECODE` |
| 系统变量 `SystemVariableUtils` 静态面 | `VERIFIED_STATIC_BYTECODE` |
| 连接器 Provider 扩展点族 | `VERIFIED_STATIC_BYTECODE` |
| 各方法的业务语义/租户隔离行为 | **UNVERIFIED**（本格只给签名） |

## 铁律

- 查标品能力先按域找 AppService：组织 `organization-facade` / 流程 `bpm-facade` / 事项 `ctp-affair-facade` / 连接器 `cip-connector-*` / 文件 `boot-starter-file` / 枚举 `boot-starter-enums` / 系统变量 `boot-starter-systemvariable`。
- 组织域 `Base` 与 `Core` 成对存在，引用前先确认目标方法在哪个里。
- UDC 走 BPM/事项要用 `*ForUdc` / `AffairUdcAppService` 接缝，不要直调 `BpmAppService.send`。
- 文件存储接自建 OSS 实现 `StorageSpi`（含三个桶名），不要改 `StorageService`。
- 枚举：`CtpEnum*Service` 是 domain 层（裸返回类型），`CtpEnumAppService` 是契约层（套 transport）；两层风格不同是设计而非缺陷。
- 取当前用户/单位/部门一律 `SystemVariableUtils`，不要自己读 Session/ThreadLocal。
- 连接器扩展点是一族 `*ProviderService`（实现 Provider 并提供 `getPageJson` + `jsonCheck`），不是改 `LinkerAppService`。

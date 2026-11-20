# 专题 6：基础组件体系

> 状态：**研究中（第一轮·静态）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 最近更新：2026-11-17
> 原则：**不重复堆积类名，只回答「该不该用、怎么用、有什么坑」**

---

## 1. 研究目标

在已有 2669 类索引基础上，补**使用知识**：
每个组件回答 9 项：用途 / 适用场景 / 调用方式 / 参数返回 / 使用约束 / 副作用 / 异常 / 真实样例 / **不适用场景**

---

## 2. 组件总览（12 类）

| # | 组件 | 核心类 | 状态 |
|---|---|---|---|
| 1 | JSON | `JsonUtils` / `JsonNodeUtil` / `JsonUtil` | 签名有，边界待补 |
| 2 | 日期 | `DateUtils` / `DateTransformUtil` | 签名有 |
| 3 | 文件/附件 | `StorageService` / `FileAppService` | **本轮已摸清** |
| 4 | 缓存 | `UserCacheUtils` / `OrgCacheUtils` | 签名有 |
| 5 | 组织人员 | `OrgCommonAppService`（45 方法） | **本轮已摸清** |
| 6 | 流程 | `BpmAppService` | 待补 |
| 7 | Excel | `ExcelTemplateUtil` | 待补 |
| 8 | HTTP | `HttpClientUtil`（93 方法） | **本轮已摸清** |
| 9 | 分布式锁 | `DistributedLockFactory`（6 方法） | **本轮已摸清** |
| 10 | 表达式 | `ExpressionEvaluator` | 见专题 4 |
| 11 | 持久化 | `BaseEntityCurdService` | 见专题 3 |
| 12 | 序列化/传输 | `PageInfo` / `PageData` / `Sort` | 见专题 3 |

---

## 3. 文件与附件（★ 本轮重点）

### 3.1 两套 API 分工

```
StorageService（接口，14 方法）    ← 底层存储抽象（MinIO/NFS/OBS/OSS/SFOss）
FileAppService（class，14 方法）   ← 业务层文件服务（URL/缩略图/登记）
```

**⇒ 业务代码用 `FileAppService`，不要直接用 `StorageService`。**

### 3.2 `StorageService`（14 方法）

```java
com.seeyon.boot.starter.file.storage.StorageService    ← interface
  # getStorageType(): String
  # init(StorageProperties, String): void
  # shutdown(): void
  # upload(StorageUploadRequestDto): UploadResultDto
  # download(String): InputStream
  # download(String, HttpServletResponse): void
  # delete(String): boolean
  # exist(String): boolean
  # copy(String, String): void
  # enablePartUpload(): boolean                              ← ★ 是否支持分片
  # partUploadInit(PartUploadInitRequestDto): PartUploadInitResult
  # partUpload(PartUploadInfoDto, PartUploadRequestDto): boolean
  # partUploadEnd(PartUploadInfoDto): UploadResultDto
  # check(CtpOBSInfoDto): boolean
```

**★ 分片上传三件套：`partUploadInit` → `partUpload` → `partUploadEnd`**
**⇒ 大文件必须走分片，且要先 `enablePartUpload()` 判断后端是否支持。**

### 3.3 五种存储后端（已枚举）

```
minio.SeeyonMinioClient / MinIoService        MinIO
nfs.NfsService                                NFS
obs.ObsService                                华为 OBS
oss.OssService                                阿里 OSS
sfoss.SFOssService                            深信服 OSS
```

**配套工具：**
```
StorageKeyService          key 生成
StorageSelectService       后端选择
StorageTenantUtils         租户隔离
FileNameUtils              文件名处理
ThumbnailUtils             缩略图
DownloadUtils              下载
StorageSpiService          SPI 扩展点
V5StorageSpiService        v5 版本 SPI
```

**⇒ 存储后端可插拔（SPI），且有租户隔离工具。**

### 3.4 `FileAppService`（14 方法）

```java
com.seeyon.boot.starter.file.appservice.FileAppService    ← class
  # getDownloadUrl(SingleRequest<String>): SingleResponse<String>          ← 下载 URL
  # getBackendDownloadUrl(SingleRequest<String>): SingleResponse<String>   ← 后端下载 URL
  # getDownloadUrls(SingleRequest<List<String>>): SingleResponse<Map<...>>
  # getThumbnailUrl(SingleRequest<ThumbnailRequestDto>): ...               ← 缩略图
  # getThumbnailUrls(SingleRequest<List<ThumbnailRequestDto>>): ...
  # selectByStorageKey(SingleRequest<String>): SingleResponse<FileDto>     ← 查文件信息
  # selectByStorageKeys(SingleRequest<List<String>>): ListResponse<FileDto>
  # saveFileInfo(SingleRequest<FileDto>): SingleResponse<...>              ← ★ 登记文件
  # saveFileInfos(SingleRequest<List<FileDto>>): SingleResponse<...>
  # getFileConfig(): SingleResponse<FileConfigDto>
  # getAllAppFileConfig(): SingleResponse<Map<String, FileConfigDto>>
  # copy(SingleRequest<String>): SingleResponse<String>
  # generateShareUrl(SingleRequest<String>): SingleResponse<String>        ← 分享链接
  # modifyFileName(SingleRequest<ModifyFileNameDto>): SingleResponse<...>
```

### 3.5 ★ 附件关联到业务实体的正确姿势（推断）

```
① 前端上传 → 拿到 storageKey
② 业务代码调 FileAppService#saveFileInfo(FileDto) 登记
③ 实体字段（dataType=ENTITY 或 STRING）存 storageKey
④ 读取时调 FileAppService#getDownloadUrl(storageKey)
```

**⚠️ 这是从 API 设计推断的流程，未实测。标 `UNVERIFIED`。**

### 3.6 不适用场景

- ❌ **不要自己 new 文件流写盘**（绕过存储抽象，多租户/集群会出问题）
- ❌ **不要直接用 `StorageService`**（缺少租户隔离和业务登记）
- ❌ **大文件不要一次性 `upload`**（应走分片）

---

## 4. 组织人员（★ 本轮重点）

### 4.1 `OrgCommonAppService`（45 方法）

```java
com.seeyon.organization.api.common.OrgCommonAppService
```

**核心方法（前 12 个）：**
```java
selectMemberInfoById(SingleRequest<Long>): ...                          ← 按 ID 查人员
selectMemberDepartmentInfoById(SingleRequest<Long>): ...                ← 查部门信息
selectMemberMultiDimOrgInfo(SingleRequest<Long>): ...                   ← ★ 多维组织信息
selectMemberInstitutionInfoById(SingleRequest<Long>): ...               ← 查机构
selectMemberBySelectPeopleData(SingleRequest<List<SelectPeopleData>>)   ← ★ 按选择器数据查
selectPageMemberBySelectPeopleData(PageDtoRequest<...>)                 ← 分页
selectPageMemberBySelectPeopleIdData(PageDtoRequest<...>)
selectMemberBySelectPeopleDatas(SingleRequest<List<List<...>>>)         ← 多组
selectMemberBySelectPeopleDataJson(SingleRequest<String>)               ← ★ JSON 入参
selectPageMemberBySelectPeopleDataJson(PageDtoRequest<String>)
selectPageMemberBySelectPeopleIdDataJson(PageDtoRequest<String>)
selectMemberBySelectPeopleDataJsons(SingleRequest<List<String>>)
```

**★ 关键观察：**
1. **有 `Json` 后缀的变体** — 支持直接传 JSON 字符串（跨语言/动态场景）
2. **有 `SelectPeopleData` 类型** — 前端人员选择器的数据结构
3. **`selectMemberMultiDimOrgInfo`** — 多维组织（一人多岗）

### 4.2 调用方式

**⇒ 这是 `AppService`，走 `SingleRequest`/`SingleResponse` 契约。**
**⇒ 业务代码里通过 `@Autowired OrgCommonAppService` 或泛化调用。**

### 4.3 不适用场景

- ❌ **不要自己查组织表**（组织有缓存和多维模型）
- ❌ **不要用 `OrgCacheUtils` 直接读**（缓存可能过期，应用 `OrgCommonAppService`）

---

## 5. HTTP（`HttpClientUtil`，93 方法）

### 5.1 结构

```java
com.seeyon.boot.util.http.HttpClientUtil
  # create(HttpConfig): void                                    ← 全局配置
  # get(String[, Charset][, Class<T>]): String|T
  # get(String, Map<String,Object>[, int][, Class<T>])
  # get(String, int[, Class<T>])
  # get(String, Charset, int, HttpHeader, Map<...>)
  # ...（93 个重载）
```

**配套类：**
```
com.seeyon.boot.util.http.common.HttpConfig     全局配置
com.seeyon.boot.util.http.common.HttpHeader     请求头
```

### 5.2 使用约束（推断）

| 项 | 约束 |
|---|---|
| 超时 | 必须显式设置（多个重载带 `int` 超时参数） |
| 编码 | 默认可能非 UTF-8，需显式 `Charset` |
| 连接池 | `HttpConfig` 统一配置，不要每处 new |

### 5.3 不适用场景

- ❌ **微流程里不要用**（微流程无 HTTP 节点，应用 `CipConnector`）
- ❌ **不要用于内部服务调用**（应用 Dubbo/AppService）
- ⚠️ **93 个重载容易选错**（选带超时+编码的版本）

---

## 6. 分布式锁（★ 用户踩过坑的组件）

### 6.1 `DistributedLockFactory`（6 方法）

```java
com.seeyon.boot.starter.lock.DistributedLockFactory
  # newLock(String): Lock
  # newLock(String, Long): Lock
  # newLock(String, Long, boolean): Lock
  # newLockIgnoreTenant(String): Lock
  # newLockIgnoreTenant(String, Long): Lock
  # instanceLock(String, String, Long, String): Lock
```

**⇒ 返回标准 `java.util.concurrent.locks.Lock`，不是自定义接口。**

**⇒ 默认带租户隔离，`IgnoreTenant` 可关闭。**

### 6.2 ★ 重要：平台自带分布式锁

**用户复盘文档里记录「自己实现锁续约 40s/120s」。**
**⇒ 但平台有 `DistributedLockFactory`，不需要自己实现。**

**⚠️ 但平台锁的续约机制未证**（`newLock(String, Long)` 的 Long 是超时还是租约？）
**⇒ 需反编译确认。标 `UNVERIFIED`。**

### 6.3 配套

```
DistributedLockAutoConfiguration      自动配置
DistributedLockComponentInitializer   组件初始化
```

### 6.4 不适用场景

- ❌ **不要自己用 Redis SETNX 实现锁**（平台已有）
- ⚠️ **跨租户操作需 `newLockIgnoreTenant`**

---

## 7. 其他组件（签名级，边界待补）

### 7.1 JSON（★ 本轮已摸清：实际是 4 个类，不是 3 个）

**⚠️ 修正：所谓「JsonUtils 三兄弟」实际有 4 个同名/近名类，用途完全不同。**

| 类 | 方法数 | 用途 |
|---|---|---|
| **`com.seeyon.boot.util.JsonUtils`** | **28** | **★ 通用 JSON 工具（业务代码用这个）** |
| `com.seeyon.boot.license.JsonUtils` | **1** | license 模块专用（只有 `toJson`） |
| `com.seeyon.udc.jackson.util.JsonNodeUtil` | **56** | Jackson `JsonNode` 树操作（UDC 专用） |
| `com.seeyon.ai.aiFormSchemaTransformer.util.JsonUtil` | 20 | AI 模块专用 |
| `com.seeyon.boot.starter.excel.utils.JsonUtil` | 10 | Excel 模块专用 |

**⇒ 同名坑：`JsonUtils` 有 2 个，`JsonUtil` 有 2 个。import 错会编译失败或行为不同。**

#### 7.1.1 ★★ `boot.util.JsonUtils` 的核心模式：静默版 vs ThrowError 版

**28 个方法里有 5 对「静默/抛错」变体：**

| 静默版 | 抛错版 | 差异（推断） |
|---|---|---|
| `toJson(Object)` | `toJsonThrowError(Object)` | 序列化失败：返回 null vs 抛异常 |
| `fromJson(String, Class)` | `fromJsonThrowError(String, Class)` | 反序列化失败：返回 null vs 抛异常 |
| `toMap(String)` | `toMapThrowError(String)` | 同上 |
| `toStringMap(String)` | `toStringMapThrowError(String)` | 同上 |
| `toList(String)` / `toList(String, Class)` | `toListThrowError(...)` | 同上 |

**⇒ 使用约束：业务代码应优先用 `ThrowError` 版，避免静默失败。**
**⚠️ 「静默版真的返回 null 吗」未证（需方法体）。标 `UNVERIFIED`。**

#### 7.1.2 ★ 4 个特殊序列化变体（解决具体问题）

| 方法 | 解决的问题 |
|---|---|
| **`toJsonLongToString(Object)`** | **★ Long 转 String → 解决雪花 ID 传到前端精度丢失** |
| **`toJsonDecimalToString(Object)`** | BigDecimal 转 String → 避免浮点精度问题 |
| `toJsonEnumToCode(Object)` | 枚举序列化为 `code` 而不是 `name` |
| `toJsonNotIncludeNull(Object)` | 不输出 null 字段（减小报文） |

**★★ `toJsonLongToString` 是最有价值的一个：**
**平台用雪花 ID（19 位 Long），JS `Number` 只有 53 位精度 → 直接传会丢精度。**
**⇒ 前端交互必须用这个方法，或实体 DTO 字段声明为 String。**

#### 7.1.3 其他方法

```java
toJson(Object, boolean)                  // 带标志的重载（含义未知）
fromJson(String, Class, Class)           // 带泛型参数
fromJson(String, Class, Class, Class)    // 三泛型
toMap(String, Class<K>, Class<V>)        // 指定 K/V 类型
toStringList(String)                     // 转 String 列表
readValue(String, JavaType)              // Jackson 原生
readValue(String, Class<T>)              // Jackson 原生
clearCache(int)                          // 清理 Jackson 缓存
main(String[])                           // ← 有 main 方法（工具类残留）
```

**⚠️ `toJson(Object, boolean)` 的 boolean 含义未证。**
**⚠️ `main(String[])` 的存在说明这个类可能从别处拷贝而来，不是纯粹的 API 类。**

#### 7.1.4 `JsonNodeUtil`（56 方法，UDC 专用）

```
com.seeyon.udc.jackson.util.JsonNodeUtil
```

**⇒ 56 个方法，操作 Jackson `JsonNode` 树（读路径、取节点、类型判断）。**
**⇒ 用途：处理 GraphQL / 元数据 JSON 的深层取值，不是通用的序列化。**
**⚠️ 具体方法未逐个提取（56 个，价值低于 JsonUtils）。**

#### 7.1.5 不适用场景

- ❌ **不要用 `license.JsonUtils`**（只有 1 个方法，是 license 模块私有）
- ❌ **不要用 `ai.*.JsonUtil` 或 `excel.*.JsonUtil`**（模块私有）
- ❌ **前端交互不要用 `toJson`**（Long 精度丢失）→ 用 `toJsonLongToString`
- ❌ **不要用静默版做关键路径**（失败无声）→ 用 `ThrowError` 版

### 7.2 日期

| 类 | 方法数 |
|---|---|
| `DateUtils` | 61 |
| `DateTransformUtil` | 19 |

**⇒ 与表达式 `dateToString` 的选择边界：代码里用 `DateUtils`，表达式里用内置函数。**

### 7.3 缓存

| 类 | 方法数 |
|---|---|
| `UserCacheUtils` | 125 |
| `OrgCacheUtils` | 47 |

**⚠️ 缓存失效时机未证，读写一致性需注意。**

### 7.4 Excel

| 类 | 方法数 |
|---|---|
| `ExcelTemplateUtil` | 70 |

**⇒ 与平台「导入导出模板」的关系待查。**
**★ 已发现 `BaseEntityCurdService#importEntityInitData(ExcelImportTransDto)` 是实体级导入入口。**

### 7.5 流程（★ 本轮已摸清 `BpmAppService` 26 方法）

```java
com.seeyon.bpm.api.common.BpmAppService    ← 26 方法（不是 22）
```

#### 7.5.1 三类「发起」操作的边界（★ 用户最关心）

| 方法 | 入参 | 语义 | 单据状态 |
|---|---|---|---|
| **`saveDraft`** | `BpmSaveDraftDto` | **保存草稿**（不发起流程） | `DRAFT`(0) |
| **`submit`** | `BpmSubmitDto` | **提交**（草稿 → 流程） | `DRAFT` → `PENDING_REVIEW`(2) |
| **`send`** | `BpmSendDto` | **发起**（新建流程实例） | → `PENDING_REVIEW`(2) |

**⇒ 三者不是别名，是三个不同阶段的操作：**
```
saveDraft → 草稿态（可改可删）
submit    → 从草稿提交（已有 caseId）
send      → 直接发起（新 caseId）
```

**⚠️ 未证：`submit` 与 `send` 的 DTO 字段差异、是否都能用于 UDC 单据。需实测。**

#### 7.5.2 完整 26 方法清单

| 方法 | 语义 |
|---|---|
| `send(BpmSendDto)` | 发起 |
| `saveDraft(BpmSaveDraftDto)` | **保存草稿** |
| `submit(BpmSubmitDto)` | **提交** |
| `stepBack(BpmStepBackDto)` | 退回 |
| `repeal(BpmRepealDto)` | 撤销 |
| `stop(BpmStopDto)` | 终止 |
| `takeBack(BpmTakeBackDto)` | 取回 |
| `replace(BpmReplaceDto)` | 替换处理人 |
| `multipleReplace(BpmMultipleReplaceDto)` | 批量替换 |
| `consult(BpmConsultDto)` | 传阅/咨询 |
| `hasten(BpmHastenDto)` | 催办 |
| `pause(BpmPauseDto)` | 暂停 |
| `cancelPause(BpmPauseDto)` | 取消暂停 |
| `superviseRelive(BpmReliveDto)` | 督办复活 |
| `superviseReliveFull(BpmReliveFullDto)` | 督办复活（完整） |
| `inform(BpmInformDto)` | 通知 |
| `addExecuteMember(BpmAddExecuteUserDto)` | 加签 |
| `cancelItems(BpmCancelItemDto)` | 取消事项 |
| `batchDeal(BpmBatchReqDto)` | 批量处理 |
| `selectFullCaseInfo(BpmCaseFullInfoSearch)` | 查完整流程信息 |
| `counterSignNode(SimpleChangeProcessRequestDto)` | 会签节点 |
| `addNode(SimpleChangeProcessRequestDto)` | 加节点 |
| `monitorNodeRun(BpmMonitorRunDto)` | 监控节点运行 |
| `check(SecurityCheckDto)` | 安全检查 |
| `deleteDraft(Long)` | 删草稿 |
| `deleteDraftAffair(DeleteDraftReqDto)` | 删草稿事项 |

**★ 关键观察：**
1. **26 个方法全是 `SingleRequest`/`SingleResponse` 契约**（标准 AppService）
2. **`pause`/`cancelPause` 返回 `ListResponse`**（不是 Single）—— 批量语义
3. **`hasten` 返回 `ListResponse`** —— 可能催办多人
4. **有 `deleteDraft` 但没有 `deleteBill`** —— 单据删除可能走 `nullify`（作废）而非物理删除

#### 7.5.3 UDC 专用 BPM 服务

```java
com.seeyon.udc.api.UdcBpmAppService
  # selectDefaultLayoutAppName(): SingleResponse<String>    ← 1 个方法
```

**⇒ UDC 侧对 BPM 的扩展只有 1 个方法（取默认布局应用名）。**
**⇒ 说明 UDC 单据的流程操作**复用** `BpmAppService`，没有独立一套。**

#### 7.5.4 数据流触发 BPM

```java
com.seeyon.boot.starter.dataflow.api.DataFlowForBpmAppService
  # asyncTriggerFlowForBpm(SingleRequest<BpmTriggerFlowUdcFinishDto>)   ← 异步触发
  # fillErrorFlowData(SingleRequest<FillFlowReqDto>)                    ← 填充错误数据
```

**⇒ 数据流（生单规则）完成后可异步触发 BPM 流程。**
**⇒ 这是「数据流 → 单据」的桥梁（与 `dataFlowEnabled` 对应）。**

#### 7.5.5 不适用场景

- ❌ **不要自己拼 BPM 参数**（DTO 有 26 种，各有必填字段）
- ❌ **不要用 `send` 代替 `saveDraft`**（会直接发起流程，无法再改）
- ⚠️ **`pause`/`hasten` 返回 ListResponse，注意取结果方式**

---

## 8. 组件选择决策表

| 需求 | 该用 | 不该用 |
|---|---|---|
| 上传附件 | `FileAppService#saveFileInfo` | 直接 `StorageService#upload` |
| 大文件上传 | `partUploadInit/partUpload/partUploadEnd` | 一次性 `upload` |
| 取下载链接 | `FileAppService#getDownloadUrl` | 拼 URL |
| 查人员 | `OrgCommonAppService` | 直接查组织表 |
| 调外部 API | `HttpClientUtil`（带超时+编码） | 裸 `HttpURLConnection` |
| 微流程调外部 | `CipConnector` | `HttpClientUtil` |
| 并发控制 | `DistributedLockFactory` | 自己 SETNX |
| 分页 | `PageInfo` + `PageData` | 自己算 offset |
| 不需要总数 | `PageInfo#setNeedTotal(false)` | 每次都 COUNT |
| 实体 CRUD | `BaseEntityCurdService` | 自己写 Mapper |
| 主子表 | `recursiveCreate/Update/Delete` | 手动循环 |
| 单据 | `create4Bpm` / `update4Bpm` | `create` |
| 表达式 | `ExpressionEvaluator#eval` | 自己解析字符串 |

---

## 9. 证据清单

| # | 结论 | 等级 | 来源 |
|---|---|---|---|
| 1 | `StorageService` 14 方法，含分片上传三件套 | `VERIFIED` | 签名 |
| 2 | 5 种存储后端（MinIO/NFS/OBS/OSS/SFOss） | `VERIFIED` | 类枚举 |
| 3 | `FileAppService` 14 方法（URL/缩略图/登记） | `VERIFIED` | 签名 |
| 4 | `OrgCommonAppService` 45 方法（含 Json 变体） | `VERIFIED` | 签名 |
| 5 | `HttpClientUtil` 93 方法 + HttpConfig/HttpHeader | `VERIFIED` | 签名 |
| 6 | **`DistributedLockFactory` 6 方法，返回标准 Lock** | `VERIFIED` | 签名 |
| 7 | 锁默认带租户，可 IgnoreTenant | `VERIFIED` | 方法名 |
| 8 | `StorageTenantUtils` 租户隔离 | `VERIFIED` | 类名 |
| 9 | `StorageSpiService` 存储可插拔 | `VERIFIED` | 类名 |
| 10 | 附件关联流程 | **UNVERIFIED** | 推断 |
| 11 | 锁续约机制 | **UNVERIFIED** | — |
| 12 | 缓存失效时机 | **UNVERIFIED** | — |
| 13 | `JsonUtils` 多同名类 | `VERIFIED` | 类枚举 |
| 14 | `ExcelTemplateUtil` 与导入模板关系 | **UNVERIFIED** | — |

---

## 10. 下一轮任务

1. `JsonUtils` / `JsonNodeUtil` / `JsonUtil` 方法差异对比
2. `BpmAppService` 22 方法逐个说明（send/submit/start 边界）
3. `ExcelTemplateUtil` 与 `BaseEntityCurdService#importEntityInitData` 的关系
4. 缓存类的方法分组
5. 转专题 7：业务能力关联骨架

# 基础包能力清单：枚举（enums）+ 文件（file）

> 来源：`boot-starter-enums-5.3.603.jar`（51 类）+ `boot-starter-file-5.3.600.jar`（89 类）CFR 反编译
> ⚠️ **VERSION_CAVEAT**：本机 5.3.600/5.3.603，用户环境 5.3.517。
> 等级：`VERIFIED_STATIC_SOURCE`

---

## 一、枚举包（boot-starter-enums，51 类）

**包：** `com.seeyon.boot.starter.enums`

### 1.1 核心模型：三个实体 + 一个类型枚举

#### `CtpEnum` —— 枚举定义

| 类型 | 说明 |
|---|---|
| `SAME_LEVEL` | 平级枚举（单层，如「性别」）|
| `MULTI_LEVEL` | 多级枚举（树形，如「行政区划」）|
| `CASCADE` | 级联枚举（父子联动，如「省→市→区」）|

**⇒ 三种枚举类型决定数据的组织方式，选错会导致前端级联失效。**

#### `CtpEnumItem` —— 枚举项（15 个字段）

```java
private String   name;              // 显示名
private String   itemValue;         // ★ 存储值（不是 id，是业务值）
private Integer  itemLevel = 1;     // 层级（多级枚举用）
private Boolean  leaf = true;       // 是否叶子节点
private Boolean  enable = true;     // 是否启用
private String   enumCode;          // 所属枚举编码
private Long     enumId;            // 所属枚举 ID
private Long     parentId;          // ★ 父项 ID（树形/级联）
private String   parentItemValue;   // ★ 父项的值
private String   imageKey = "";     // 图片 key
private Integer  orderNo = 1;       // 排序
private Boolean  delete = false;    // 逻辑删除
private String   appId = "";        // 所属应用
private Long     appGuid = -1L;
private String   hostAppName;       // 宿主应用名
```

**⇒ `itemValue` 是**业务存取值**，`enumId`/`parentId` 是内部主键。**
**⇒ 业务表里存的是 `itemValue`，不是 ID —— 这点极重要。**
**⇒ `parentItemValue` 同时冗余了父项值，方便级联查询不 join。**

### 1.2 `CtpEnumAppService` —— 枚举管理（22 方法）

```java
create(SingleRequest<CtpEnumDto>)                      : SingleResponse<Long>
update(SingleRequest<CtpEnumDto>)                      : SingleResponse<Integer>
deleteByIds(SingleRequest<List<Long>>)                 : SingleResponse<Integer>
copyById(SingleRequest<Long>)                          : SingleResponse<Long>

createBatchForAppApproval(...)                         : ★ 应用审批时批量建枚举
createOrUpdateBatchForOnlypage(...)                    : ★ 页面专用批量
updatePresetBatch(...)                                 : ★ 预设批量更新
updateDataStatusBatch(...)                             : ★ 批量改状态

selectById(SingleRequest<Long>)                        : SingleResponse<CtpEnumDto>
selectByIds(SingleRequest<List<Long>>)                 : ListResponse<CtpEnumDto>
selectPageByConditions(PageRequest)                    : PageResponse<CtpEnumDto>
selectListByConditions(ListRequest)                    : ListResponse<CtpEnumDto>
selectListByConditionsNoLevel(ListRequest)             : ★ 不含层级
selectByConditionsContainsCascade(ListRequest)         : ★ 含级联子项
selectByCode(SingleRequest<String>)                    : ★ 按编码查（最常用）
selectParentByCode(SingleRequest<String>)              : ★ 按编码查父项
selectByRootEnumIdAndEnumLevel(...)                    : ★ 按根+层级查
selectByAppGuid(SingleRequest<Long>)                   : ★ 按应用查
calcEnumOrderNo(...)                                   : 算排序号
```

**⇒ `selectByCode` 是业务代码取枚举的标准入口。**

### 1.3 其他关键类

| 类 | 作用 |
|---|---|
| `CtpEnumItemAppService` | 枚举项管理 |
| `CtpEnumCategoryAppService` | **枚举分类**（枚举的分组）|
| `CtpEnumItemFilterService` / `CtpEnumItemFilterInterface` | **枚举项过滤**（按权限/条件筛选项）|
| `EnumCacheUtils` | **枚举缓存** |
| `EnumItemExportUtils` | 枚举项导出 |
| `CtpEnumDataInitBeforeUpdateService` | 数据初始化前置 |
| `CtpEnumUpgradeExtendService` | 枚举升级扩展 |
| `CtpEnumItemImportDto` / `CtpEnumItemImportResultDto` | 枚举项导入 |
| `GenericInvocationAuthService` | 泛化调用鉴权 |

**⇒ `CtpEnumItemFilterService` 是「不同用户看到不同枚举项」的实现点。**

### 1.4 事件体系（枚举变更会发事件）

```java
CtpEnumCreateEvent / CtpEnumUpdateEvent / CtpEnumDeleteEvent
CtpEnumItemCreateEvent / CtpEnumItemUpdateEvent / CtpEnumItemDeleteEvent
CtpEnumItemBatchDeleteEvent
CtpEnumUpdateListener / CtpEnumDeleteListener
```

**⇒ 枚举变更会触发事件，可用于清理业务侧缓存。**

### 1.5 开发要点

```
取枚举项         → CtpEnumAppService.selectByCode(code)
业务表存什么     → itemValue（不是 enumId）
多级/级联枚举    → 用 parentId / parentItemValue
按权限筛选项     → CtpEnumItemFilterService
枚举缓存         → EnumCacheUtils（改枚举后要清）
```

---

## 二、文件包（boot-starter-file，89 类）

**包：** `com.seeyon.boot.starter.file`

### 2.1 ★★★ 存储抽象层：`StorageService`（14 方法）

**这是所有存储实现的统一接口。**

```java
String              getStorageType();          // 存储类型标识
void                init(StorageProperties, String);
void                shutdown();

boolean             delete(String key);
UploadResultDto     upload(StorageUploadRequestDto);
InputStream         download(String key);
void                download(String key, HttpServletResponse);   // 直接写响应流
boolean             exist(String key);
void                copy(String src, String dest);

// ★ 分片上传（大文件）
boolean                     enablePartUpload();
PartUploadInitResultDto     partUploadInit(PartUploadInitRequestDto);
boolean                     partUpload(PartUploadInfoDto, PartUploadRequestDto);
UploadResultDto             partUploadEnd(PartUploadInfoDto);

boolean             check(CtpOBSInfoDto);
```

**⇒ 分片上传是**四步**：`init` → `partUpload`（多次）→ `end`。**
**⇒ `enablePartUpload()` 要先判断存储类型是否支持。**

### 2.2 存储实现（8 种后端）

| 实现类 | 存储类型 |
|---|---|
| `NfsService` | NFS 文件系统 |
| `OssService` | 阿里云 OSS |
| `SfoOssService` | SFO OSS |
| `ObsService` | 华为云 OBS |
| `MinIoService` | MinIO |
| `V5StorageSpi` / `V5StorageSpiService` | V5 兼容存储 |
| `StorageSpi` / `StorageSpiService` | SPI 扩展点 |
| `StorageSelectService` | **存储选择器**（按配置选后端）|

**⇒ `StorageSelectService` 是「怎么决定用哪个存储」的入口。**

### 2.3 `StorageSpi`（9 方法）—— 自定义存储的扩展点

```java
String  getPrivateBucketName();
String  getPublicBucketName();
String  getFerryboatBucketName();       // ★ 摆渡桶（内外网文件交换）
UploadResultDto upload(SpiUploadRequestDto);
void    download(String bucket, String key, HttpServletResponse);
InputStream download(String bucket, String key);
String  copy(String srcBucket, String srcKey, String destBucket, String destKey);
boolean exist(String bucket, String key);
boolean delete(String bucket, String key);
```

**⇒ 实现这 9 个方法就能接入新存储（如腾讯云 COS）。**
**⇒ 三个桶：private / public / ferryboat（摆渡）。**

### 2.4 `FileAppService`（11+ 方法）—— 业务侧文件接口

```java
getDownloadUrl(SingleRequest<...>)          : SingleResponse<String>      ★ 下载 URL
getBackendDownloadUrl(...)                  : SingleResponse<String>      ★ 后端下载 URL
getThumbnailUrl(...)                        : SingleResponse<String>      ★ 缩略图
selectByStorageKey(SingleRequest<String>)   : SingleResponse<FileDto>
selectByStorageKeys(...)                    : ListResponse<FileDto>
saveFileInfo(SingleRequest<FileDto>)        : SingleResponse<FileDto>     ★ 登记文件
saveFileInfos(...)                          : SingleResponse<Integer>     ★ 批量登记
getFileConfig(...)                          : SingleResponse<FileConfigDto>
copy(...)                                   : SingleResponse<String>
generateShareUrl(...)                       : SingleResponse<String>      ★ 生成分享链接
modifyFileName(...)                         : SingleResponse<FileDto>     ★ 改文件名
```

**⇒ 上传分两步：`StorageService.upload` 拿 storageKey → `FileAppService.saveFileInfo` 登记元数据。**
**⇒ 下载用 `getDownloadUrl` 拿临时 URL，不是直接读流。**

### 2.5 其他文件服务

| 接口 | 职责 |
|---|---|
| `FileService`（91 方法）| 文件综合服务（最全）|
| `FileDownloadService`（23 方法）| 下载专用 |
| `FileInfoService`（13 方法）| 文件元数据 |
| `StorageKeyService`（7 方法）| storageKey 生成/解析 |
| `EncryptConfigService` | **加解密配置** |
| `QrcodeUploadService` | 二维码上传 |
| `ZipFileService` | ZIP 打包 |

### 2.6 开发要点

```
上传小文件   → StorageService.upload → FileAppService.saveFileInfo
上传大文件   → partUploadInit → partUpload × N → partUploadEnd → saveFileInfo
下载         → FileAppService.getDownloadUrl（临时URL）
缩略图       → FileAppService.getThumbnailUrl
改文件名     → FileAppService.modifyFileName
分享         → FileAppService.generateShareUrl
接入新存储   → 实现 StorageSpi 9 个方法
```

**⇒⚠️ 上传后**必须**调 `saveFileInfo` 登记，否则文件在存储里但没有元数据，查不到。**

---

## 三、枚举与文件的交叉点

```
枚举的 imageKey 字段  → 指向文件存储的 key
枚举项图片           → FileAppService.getThumbnailUrl(imageKey)
```

**⇒ 枚举项的图标是「存 key + 按需取 URL」，不是存完整 URL。**

---

## 四、与其他域的关系

```
enums（枚举）
    ↑ 被所有域引用
    ├─ udc（实体字段引用枚举，存 itemValue）
    ├─ bpm（表单下拉、节点条件）
    └─ organization（人员属性枚举）

file（文件）
    ↑ 被所有域引用
    ├─ udc（附件字段）
    ├─ bpm（流程附件、意见附件）
    ├─ organization（人员头像、敏感文件）
    └─ enums（枚举项图标）
```

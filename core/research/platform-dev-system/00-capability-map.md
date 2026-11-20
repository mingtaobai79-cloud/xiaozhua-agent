# 平台能力地图（按「有什么能力」组织，不按「UDC 怎么调」）

> 数据源：`/d/repo/CHIT/com/seeyon/` 全部 107 个 jar 的 class 清单实证
> 等级：`VERIFIED_STATIC_BYTECODE`（zip class 清单，未反编译方法体）
> ⚠️ 用户环境 5.3.517，本机多数 5.3.600+，`VERSION_CAVEAT` 全程适用

---

## 0. 调用方式的三种形态（最重要的一层）

**用户明确指出的分类，这是组织整张地图的骨架：**

| 形态 | 适用 | 机制 |
|---|---|---|
| **① Dubbo / 泛化调用** | **标品业务应用**（org / bpm / affair / message / connector / portal / schedule …） | `*AppService` 接口 + `SingleRequest/Response` 包装，跨进程 |
| **② @Autowired 直接注入** | **业务组件**（file / enum / cache / excel / i18n …） | 同 JVM 内 Spring Bean，直接调 `Service` / `AppService` |
| **③ 工具类静态调用** | **基础工具**（json / http / 加密 / 日期 / 线程池 …） | `*Utils` / `*Helper`，无状态静态方法 |

**⇒ 这三层决定了「获取能力的入口」，是 Agent 理解平台的第一道判断。**

---

## 一、标品业务应用（Dubbo / 泛化调用）

### 1.1 组织（organization-facade 5.3.601，414 类）

**能力：** 组织架构全维度查询与维护

| 能力 | 入口 |
|---|---|
| 人员查询（按部门/岗位/职级/userId） | `OrgCommonAppService`（45 方法） |
| 人员/部门 CRUD | `OrgMemberBaseAppService` / `OrgUnitBaseAppService` |
| 组织数据同步（三方对接） | `OrgMemberSyncAppService` / `OrgUnitSyncAppService` |
| 流程选人匹配 | `OrgWorkFlowAppService`（37 方法） |
| 元数据维度查询（自定义字段筛人） | `OrgMetadataCoreAppService` |
| 多维组织 | `selectMemberMultiDimOrgInfo` |
| 敏感字段权限 | `selectSensitiveFieldInfo` |

**关键约束：** 返回 `Map<String,Object>` 不是强类型 DTO —— 组织字段元数据可配置。
**大数据量：** `selectMemberPostBySelectPeoplesReturnFile` → 写文件 → `selectReturnFileByKey` 读 → **必须 `deleteReturnFileByKey` 清理**。

### 1.2 流程（bpm-facade 5.3.374，533 类）

**能力：** 流程模板、实例、权限、意见、监控

| 能力 | 入口 | 方法数 |
|---|---|---|
| 流程操作（发起/提交/退回/撤销/终止/取回/移交/加签/暂停/督办） | `BpmAppService` | 26 |
| 流程实例查询 | `BpmCaseAppService` | 22 |
| 流程模板管理 | `BpmTemplateAppService` | 54 |
| **UDC 集成专用** | `BpmUdcApiService` | 10 |
| 表单权限（能看/改哪些字段） | `BpmApiFormPermissionAppService` | 18 |
| 节点权限（谁能办） | `BpmApiNodePermissionAppService` | 11 |
| 意见 | `BpmOpinionAppService` | 7 |
| 自动审批 | `BpmAutoApprovalAppService` | 4 |
| 流程检测 | `BpmApiDetectionService` | 9 |

**关键约束：**
- 全部 `SingleRequest<T>` → `*Response<R>`，不能直接传原始参数
- 表单权限 ≠ 节点权限，两套独立
- 模板发布两阶段：`publishLock` → `publishCheck` → `publishFinish`，改完必须 `cleanCacheByApplicationName`
- 单据找模板：`rootEntityName` 为主键，不是 `templateCode`

### 1.3 事项（ctp-affair-facade 5.3.315，122 类）

**能力：** 待办/已办事项管理

| 接口 | 能力 |
|---|---|
| `AffairCommonAppService` | 事项通用查询 |
| `AffairCategoryAppService` | 事项分类 |
| `AffairCustomOperationAppService` | 自定义操作 |
| `AffairDataScopeAppService` | **数据范围** |
| `AffairNodePermissionAppService` | **节点权限** |
| **`AffairUdcAppService`** | **UDC 专用** |
| `AffairOpenAppService` | 对外开放 |
| `AffairSuperviseAppService` | 督办 |
| `Affair4WorkflowAppService` | 流程集成 |
| SPI：`AbstractAffairRefreshService` / `AbstractAffairSearchService` / `AbstractThirdAffairService` | 扩展点 |

**工具：** `AffairStateUtil` / `AffairDefaultUtil`

### 1.4 消息（ctp-message-facade 5.3.287，45 类）

| 接口 | 能力 |
|---|---|
| `CtpMessageManageAppService` | 消息管理 |
| `CtpMessageOperateAppService` | 消息操作（发/读/删） |
| **`CtpUdcMessageSendAppService`** | **UDC 消息发送** |
| `CtpMessageOpenApiService` | 开放 API |
| `CtpMessageSourceTypeAppService` | 消息来源类型 |

**工具：** `MessageUtil` / `MessageCacheKeyUtil`

### 1.5 用户与认证（ctp-user-facade 5.3.429，263 类 + ctp-user-api 5.3.351，42 类）

**能力：** 账号、租户、认证、SSO、权限

| 能力 | 入口 |
|---|---|
| 用户核心 | `CtpUserCoreAppService`（18 方法） |
| 权限 | `CtpUserPermissionCommonAppService`（18 方法） |
| 租户管理 | `CtpManagerTenantAppService`（14 方法） |
| 角色 | `CtpRoleCoreAppService`（14 方法） |
| 密钥/凭证 | `CtpSecretCommonAppService`（13 方法） |
| 认证核心 | `CtpAuthCoreAppService`（13 方法） |
| 组织管理员 | `CtpOrgAdminOrgAppService`（13 方法） |
| **SSO 扩展** | `CtpUserSsoAuthProviderService` / `AbstractAuthenticationProvider` |
| **免登扩展** | `CtpAvoidLoginBackendProviderService` / `ClientMode` / `MiddlePage` |
| **第三方菜单** | `AbstractThirdMenuService` |
| **登录二维码** | `AbstractLoginQrCodeService` |
| **密码校验** | `PasswordCheckService` |
| 自定义用户信息 | `CustomUserInfoService` |

**⇒ 这一域大量是 `Abstract*` 抽象类，是**留给二开实现**的 SPI。**

### 1.6 连接器（cip-*，共 6 个 jar，约 1,260 类）

**能力：** 第三方系统集成

| jar | 类数 | 能力 |
|---|---|---|
| `cip-capability-facade` | 490 | **能力定义**（capability 包） |
| `cip-capability-common` | 425 | 能力 Provider（355 个） |
| `cip-connector-facade` | 121 | 连接器（application 71 / connector 40） |
| `cip-connector-api` | 119 | 连接器 API |
| `cip-manager-facade` | 95 | 连接器管理 |
| `cip-openapi-common` | 21 | 开放 API 公共 |
| `cip-convert-facade` | 9 | 数据转换 |

**⇒ `cip-capability-common` 里 355 个 Provider 说明：每个第三方能力对应一个 Provider 实现。**

### 1.7 其他标品应用

| jar | 类数 | 能力 |
|---|---|---|
| `portal-facade` | 49 | 门户 |
| `app-common-facade` | 103 | 应用公共 |
| `app-approval-facade` | 25 | 应用审批 |
| `schedulemanagement*-facade` | 129 | 日程管理 |
| `m5-facade` | 55 | 移动端 |
| `cdp-data-facade` | 127 | 数据平台（common 56 / index 31 / etl 15） |

---

## 二、业务组件（@Autowired 直接注入）

### 2.1 文件（boot-starter-file 5.3.600，89 类）

**能力：** 存储抽象 + 文件元数据 + 分片上传 + 多后端

| 组件 | 能力 |
|---|---|
| `StorageService`（13 方法） | 存储抽象：upload/download/delete/exist/copy + 四步分片 |
| `StorageSpi` | **自定义存储扩展点**（3 桶：private/public/ferryboat 摆渡） |
| `FileAppService` | 业务侧：getDownloadUrl / getThumbnailUrl / saveFileInfo / generateShareUrl |
| `FileService`（91 方法） | **最全的文件接口**（未读） |
| `FileDownloadService` / `FileInfoService` | 下载 / 元数据 |
| `StorageKeyService` | storageKey 生成/解析 |
| `EncryptConfigService` | 加解密配置 |
| `ZipFileService` / `QrcodeUploadService` | 打包 / 二维码 |
| 实现：`NfsService` / `OssService` / `ObsService` / `MinIoService` / `SfoOssService` / `V5StorageSpi` | 6 种后端 |

**关键：** 上传分两步 `StorageService.upload` → `FileAppService.saveFileInfo`，漏第二步文件查不到。

### 2.2 枚举（boot-starter-enums 5.3.603，51 类）

**能力：** 数据字典

| 组件 | 能力 |
|---|---|
| `CtpEnumAppService`（22 方法） | 枚举 CRUD + `selectByCode` 取值 |
| `CtpEnumItemAppService` | 枚举项 |
| `CtpEnumCategoryAppService` | 枚举分类 |
| **`CtpEnumItemFilterService`** | **按权限/条件过滤枚举项** |
| `EnumCacheUtils` | 枚举缓存 |
| `EnumItemExportUtils` | 导出 |
| 事件：`CtpEnumCreateEvent` / `ItemCreate/Update/Delete/BatchDeleteEvent` | 变更通知 |

**三种类型：** `SAME_LEVEL`（平级）/ `MULTI_LEVEL`（多级树）/ `CASCADE`（级联）
**关键：** 业务表存 `itemValue` 不是 `enumId`；`parentItemValue` 冗余父值避免 join。

### 2.3 缓存（boot-starter-cache 5.3.600，50 类）

**能力：** 本地缓存 + Redis + 内嵌 Redis + 限流

| 组件 | 能力 |
|---|---|
| `CacheUtils` | 缓存工具（最常用） |
| `RedisUtils` | Redis 操作 |
| `RedisLogUtils` | Redis 日志 |
| `CtpRedisTemplate` | Redis 模板 |
| `DefaultCacheManager` / `CtpLocalCacheManager` | 缓存管理器 |
| `DefaultCache` / `DefaultLocalCache` | 缓存实现 |
| `DefaultCacheErrorHandler` | 缓存异常处理 |
| `RedisContext` / `RedisExecProvider` | 内嵌 Redis 上下文 |
| `PortProvider`（3 实现：Ephemeral/Predefined/Sequence） | 内嵌 Redis 端口策略 |
| `TenantUtils` | **租户隔离** |
| `RateChecker` | **限流** |

### 2.4 国际化（boot-starter-i18n 5.3.600，28 类）

| 组件 | 能力 |
|---|---|
| `I18nLocaleService` / `I18nResourceService` | 语言/资源服务 |
| `I18nLocaleAppService` / `I18nResourceAppService` | AppService 包装 |
| `DataI18nUtils` | **数据多语言** |
| `I18nResourceUtils` | 资源工具 |
| `I18nResourceChangeListener` | 变更监听 |
| **`LocaleContext`**（在 boot-core） | 当前语言上下文 |

### 2.5 元数据（boot-starter-metadata 5.3.600，81 类 + boot-starter-extmetadata 5.3.603，106 类）

**这是「元数据能力」的两个包，要分清：**

**`boot-starter-metadata`（通用元数据）**

| 组件 | 能力 |
|---|---|
| `MetadataCreateAppService` | 元数据创建 |
| `MetadataModifyAppService` | 元数据修改 |
| `MetadataDeleteAppService` | 元数据删除 |
| `MetadataQueryAppService` | 元数据查询 |
| `TenantMetadataQueryAppService` | 租户级查询 |
| `LoadJarResourceAppService` | 加载 jar 资源 |
| `MetadataService` | 核心服务 |
| `MetadataBuildUtils` / `MetadataI18nUtils` / `MetadataMD5Utils` / `MetadataRedisKeyUtils` | 工具 |

**`boot-starter-extmetadata`（UDC 扩展元数据，106 类）**

| 组件 | 能力 |
|---|---|
| `UdcEntityMetaDataService` | **实体元数据** |
| `UdcDtoMetaDataService` | **DTO 元数据** |
| `UdcServiceMetadataService` | **Service 元数据** |
| `UdcPageInfoMetaDataService` | **页面元数据** |
| `UdcAppServiceMetaDataService` | AppService 元数据 |
| `UdcEnumMetaDataService` / `UdcCtpEnumMetaDataService` / `UdcCtpEnumItemMetaDataService` | 枚举元数据 |
| `UdcReferMetaDataService` | 关联元数据 |
| `UdcMetaDataAppService` / `UdcMetaDataAppV2Service` | AppService |
| **OSS 系列**：`UdcEnumMetadata4OssService` / `UdcPageMetadata4OssService` / `UdcDataSource4OssService` / `UdcIdFullNameMetadata4OssService` / `UdcCtpParameterDefinition4OssService` | **元数据落 OSS** |
| `UdcDynamicResourceService` / `UdcFrontendResourceService` / `UdcLoadResourceService` | 资源加载 |
| `MetadataConvertUtil` / `MetadataJsonPathHelper` / `UdcI18nUtils` / `UdcMethod2ActionUtil` / `UdeMetadataCheckUtil` | 工具 |

**关键：** extmetadata 里的 `*4OssService` 说明**元数据是存 OSS 的**，不是只存 DB。

### 2.6 Excel 导入导出（boot-starter-excel 5.3.603，72 类）

| 组件 | 能力 |
|---|---|
| `ExcelImportAppService` | 导入 |
| `ExcelExportAppService` | 导出 |
| `ExcelExportTemplateService` | **导出模板管理** |
| `ExcelConvertService` | 转换 |
| `DesignMetadataQueryApi` | 设计态元数据查询 |
| Handler：`CascadeDropDownHandler` / `CascadeWriteHandler` / `ColumnStyleHandler` 等 | **级联下拉/级联写入/列样式** |

### 2.7 流水号（boot-starter-serialnumber 5.3.603，85 类）

**能力：** 单据编号生成（未深入读）

### 2.8 条件（boot-starter-condition 5.3.603，77 类）

**能力：** 条件表达式（未深入读）

### 2.9 公式（boot-starter-formula 5.3.603，202 类 + boot-formula-engine 5.3.603，41 类）

**能力：** 公式引擎（未深入读）
**⚠️ 用户明确说：「表达式那些本质是给 UDC 设计用的，你用出不大」** —— 优先级降低。

### 2.10 附件 / 意见 / 二维码 / 条码

| jar | 能力 |
|---|---|
| `boot-starter-attachment`（15 类） | 附件（是 file 的上层包装） |
| `boot-starter-opinion`（64 类） | 意见 |
| `boot-starter-qrcode`（59 类） | 二维码 |
| `boot-starter-labelprint`（23 类） | 标签打印 |
| `boot-starter-ganttchart`（50 类） | 甘特图 |

### 2.11 定时任务（boot-starter-schedule 5.3.600，50 类）

### 2.12 消息队列（boot-starter-mq 5.3.600，68 类）

### 2.13 事件总线（boot-starter-eventbus 5.3.600，24 类）

**能力：** 应用内事件发布/订阅（微流程 `PUBLISH_BUSINESS_EVENT` 的底层）

---

## 三、基础框架（@Autowired + 工具类）

### 3.1 权限与安全（boot-starter-security 5.3.600，17 类）

| 组件 | 能力 |
|---|---|
| `SecurityService` | 安全服务 |
| `SecretService` / `SecretAppService` | 密级/保密 |
| `DataPermissionCheckService` | **数据权限校验** |
| `EncryptService` | **加解密** |
| `SecurityResourcePermissionService` | 资源权限 |
| `SeeyonSecurityUtil` | 安全工具 |
| `ConditionParserUtil` | 条件解析（权限条件） |
| `DataEventListener` | 数据事件监听 |

### 3.2 线程池（boot-starter-threadpool 5.3.600，14 类）

| 组件 | 能力 |
|---|---|
| `SeeyonExecutorService` | 平台线程池 |
| `IsolatorExecutorService` | **隔离线程池**（防互相拖垮） |

### 3.3 Web（boot-starter-web 5.3.600，65 类）

| 组件 | 能力 |
|---|---|
| `WebUtils` / `ComponentRequestUtils` | Web 工具 |
| `CtpBaseService` | Controller 基类 |
| `WebExceptionHandler` | 全局异常处理 |
| `HttpServletRequestContext` | 请求上下文 |
| `DynamicFormRegisterService` | **动态表单注册** |
| `UpgradeProxyService` | 升级代理 |

### 3.4 Nacos 配置中心（boot-starter-nacos 5.3.600，26 类）

**★ 用户明确要求：「涉及到配置文件的你写了 config 类似的，需要在配置中心 nacos 或者等自己写进去对应的信息」**

| 组件 | 能力 |
|---|---|
| **`ConfigCenterService`** | **配置中心读写** |
| **`RegisterCenterService`** | **服务注册** |
| `NacosService`（SPI） | Nacos SPI |
| `SeeyonNacosConfigService` | Nacos 配置服务 |
| `ConfigCenterApplicationRunListener` | 启动监听 |

### 3.5 MyBatis / 持久化（boot-starter-mybatis 5.3.600，140 类）

| 组件 | 能力 |
|---|---|
| `AllInOneDBUtil` / `AllInOneDBDynamicUtil` / `AllInOneDBComplexUtil` | **AllInOne 系列 DB 工具** |
| `AllInOneDataParseUtil` / `AllInOneDBDynamicSeeyonKeyMapUtil` | 数据解析 |
| `DynamicAllInOneDaoService` | 动态 DAO |
| `AllDbService` | 全库服务 |
| `EntityClassContext` | 实体类上下文 |
| `EntityEncryptionService` / `DataSignService` / `DataSignRuleService` / `DataSignMybatisService` | **字段加密 + 数据签名** |
| `SensitiveService` | 敏感数据 |
| `DatabaseDialectManager` | 多数据库方言 |
| `PageObjectFactory` / `PageObjectWrapperFactory` | 分页 |
| `DataAuditCache` / `EntityAnnotationCache` / `SecurityEntityCache` | 三类缓存 |
| TypeHandler：`EnumCodeTypeHandler` / `EnumArrayCodeTypeHandler` / `SeeyonDateTypeHandler` / `NullValueHandler` / `BooleanValueHandler` | 类型转换 |
| `PluginEventService` / `MybatisSpiProviderRegisterListener` / `MybatisModuleListener` | 插件/SPI |

### 3.6 Dubbo（boot-starter-dubbo 5.3.600，55 类）

| 组件 | 能力 |
|---|---|
| `DubboFactory` | Dubbo 工厂 |
| `SeeyonNamingService` | 命名服务 |
| `NacosRegistryFactory` / `SeeyonNacosConnectionManager` | Nacos 注册 |
| **`DynamicRouterFactory` / `GrayStateRouterFactory`** | **动态路由 + 灰度路由** |
| `GrayContext` | 灰度上下文 |
| `CtpDubboShardingListener` | 分库分表监听 |
| `SysOpsDubboService` | 运维 Dubbo |

### 3.7 GraphQL（boot-starter-graphql 5.3.600，772 类）

**平台前端与后端的主要协议层。**

| 组件 | 能力 |
|---|---|
| `SeeyonSchemaService` | Schema 服务 |
| `MetadataProxyService` | 元数据代理 |
| `ScheduledService` | 调度 |

### 3.8 AppService 框架（boot-starter-appservice 5.3.600，41 类）

| 组件 | 能力 |
|---|---|
| `AppServiceContext` | AppService 上下文 |
| **`CtpIdempotentService` / `CtpIdempotentClearService`** | **幂等控制** |
| 异常处理族：`BusinessExceptionHandler` / `RpcExceptionHandler` / `RequestCheckExceptionHandler` / `ThrowableExceptionHandler` / `ExceptionHandler` | 分层异常 |
| `JavasistUtils` | 字节码工具 |

### 3.9 事务 / 锁

| jar | 类数 | 能力 |
|---|---|---|
| `boot-starter-transaction` | 15 | 事务 |
| `boot-starter-lock` | 9 | 分布式锁 |

### 3.10 Artifact / 制品（boot-starter-artifact 5.3.600，16 类）

| 组件 | 能力 |
|---|---|
| `BootArtifactManager` | 制品管理 |
| `MavenArtifactService` / `MavenStorageService` / `BootMavenServiceFactory` | **Maven 制品存取** |

**⇒ 这是「构建产物怎么存怎么取」的能力。**

### 3.11 其他基础组件

| jar | 类数 | 能力 |
|---|---|---|
| `boot-starter-datasource` | 31 | 数据源 |
| `boot-starter-sharding` | 61 | **分库分表** |
| `boot-starter-dynamicsql` | 42 | 动态 SQL |
| `boot-starter-datatype` | 23 | 数据类型 |
| `boot-starter-parameter` | 22 | 参数 |
| `boot-starter-systemvariable` | 4 | 系统变量 |
| `boot-starter-spi` | 12 | SPI 机制 |
| `boot-starter-filterchain` | 8 | 过滤器链 |
| `boot-starter-proxy` | 18 | 代理 |
| `boot-starter-index` | 24 | 索引 |
| `boot-starter-elasticsearch` | 25 | ES |
| `boot-starter-swagger` | 25 | API 文档 |
| `boot-starter-monitor` / `prometheus` | 15 / 32 | 监控 |
| `boot-starter-license` | 17 | 授权 |
| `boot-starter-environment` | 13 | 环境 |
| `boot-starter-dynamicloader` | 15 | 动态加载 |
| `boot-starter-module` | 40 | 模块 |
| `boot-starter-scanner` | 2 | 扫描 |
| `boot-starter-frontend-log` | 8 | 前端日志 |
| `boot-starter-shortlink` | 5 | 短链 |
| `boot-starter-websocket` | 8 | WebSocket |
| `boot-starter-tomcat` | 7 | Tomcat |
| `boot-starter-mgn-export` | 9 | 管理端导出 |
| `boot-starter-formconvert` | 40 | 表单转换 |
| `boot-starter-sensitive` | 9 | 敏感数据 |
| `boot-starter-datainit` | 88 | 数据初始化 |
| `boot-starter-datamigration` | 247 | 数据迁移 |
| `boot-starter-cip` | 98 | 连接器集成 |

---

## 四、boot-core（512 类）—— 平台内核

**这是最底层，其他所有 jar 都依赖它。**

| 包 | 能力 |
|---|---|
| `com.seeyon.boot.context` | **`RequestContext`** / `TransferRequestContext` —— 请求上下文 |
| `com.seeyon.boot.annotation` | `@AppService` / `@OpenApi` / `@RestApi` / `@DtoInfo` / `@EntityInfo` |
| `com.seeyon.boot.transport` | `SingleRequest` / `SingleResponse` / `ListRequest` / `PageRequest` 等 |
| `com.seeyon.boot.exception` | 异常体系 |
| `com.seeyon.boot.security` | `ComponentSecurityService` |
| `com.seeyon.boot.tenant` | `SystemTenantInvocationHandler` —— **租户隔离** |
| `com.seeyon.boot.trace` | `TraceContext` / `SeeyonSpanContext` —— **链路追踪** |
| `com.seeyon.boot.monitor` | `TraceMonitorService` / `SyMonitorRecordUtil` |
| `com.seeyon.boot.log.context` | 各类性能日志 Context（DB / Dubbo / MQ / Redis / Rest） |
| `com.seeyon.boot.cache` | `LRUMapListener` |
| `com.seeyon.boot.inspection` | `InspectionService` |
| `com.seeyon.boot.loader` | `ModuleAppBeanCache` / `SpringModuleUnloadListener` |
| `com.seeyon.boot.spring` | `SeeyonBeanFactory` |
| `com.seeyon.boot.sys` | `SysOpsDubboApi` |

### 4.1 ★★ `com.seeyon.boot.util` 的 177 个工具类（用户点名的「工具类」层）

**这是第三层调用形态的实际载体。全部类名实测：**

**【JSON】4 个**
```
JsonUtils             ← 主力
SeeyonObjectMapper    ← 定制 ObjectMapper
EnumJsonSerializer / EnumJsonDeserializer
JacksonSerializer
```

**【HTTP】15 个**
```
HttpClientUtil        ← 主力（含路由/心跳/轮询）
RestServiceUtil
ComponentUrlUtil
HttpMethods / HttpHeader / HttpResult / HttpConfig
HttpClientRoundRobinRouting / HttpClientRouteConfig / HttpClientRouteHeartbeat
HttpClientMetrics / HttpProcessException / HttpVersionEnum
FileUploadModel / FileStreamUploadModel
```

**【加密】7 个**
```
AESUtils / DESUtils / RSAUtils
MD5 / MD5Utils / SHA1Utils / SHA256Utils
SecretProperties
```

**【日期】5 个**
```
DateUtils / DateStrFormat
DateTypeConverter / StringToDateConverter / TimestampTypeConverter
```

**【字符串】**
```
StringUtils / ToStringUtils
```

**【IO / 文件】**
```
FileUtils / IoUtils / ZipUtils / ZipReader / ZipWriter
ResourceUtils / ImageUtils / PdfUtils / MimeTypeUtils
```

**【反射 / Bean 拷贝】**
```
BeanCopier / BeanUtils / BeanReflections
ClassUtils / ClassPoolUtils / AopTargetUtils / ClassScanner
```

**【类型转换】50+ 个（最庞大的一组）**
```
TypeConverter / TypeConverterManager / SimpleTypeConverterManager
AbstractTypeConverter / AbstractPrimitiveUtils / AbstractTypeConverterUtils
每种基础类型一对：StringTypeConverter / IntTypeConverter / LongTypeConverter
  / DoubleTypeConverter / BooleanTypeConverter / BigDecimalTypeConverter
  / BigIntegerTypeConverter / DateTypeConverter / EnumTypeConverter
  / ListTypeConverter / SetTypeConverter / QueueTypeConverter
  / ArrayTypeConverter / *PrimitiveTypeConverter / *PrimitiveArrayTypeConverter
ConverterNotFoundException / TypeConversionException
```

**【校验】6 个**
```
Asserts / Validators / DataValidity
HibernateValidatorFactory
SqlCheckUtils / SQLWildcardEscaper / SQLWildcardUtil
```

**【ID 生成】**
```
Ids                 ← 主力（Ids.gidLong() 就是单据主键生成）
IdentifierGenerator / IdGeneratorProperties
SnowflakeIDGenerator / SnowflakeIDElement / NetAddressIdWorker
UUIDGenerator
```

**【缓存】**
```
LocalCache / LocalCacheBuilder / CacheEviction / AutoClearable
BootCacheUtils
ConcurrentReferenceMap / SetFromMap
```

**【数据库 / 分页 / SQL】**
```
DatabaseUtils / PageUtils / SqlCheckUtils
```

**【其他】**
```
Hex / IpUtils / MACAddressParser / ServerUtils / ShutdownHooks
PropertiesBuilder / YamlUtil / PomXmlUtil
LockUtils / EnumArrayUtil / ExcelUtils
SeeyonCellDataValidityStrategy / SeeyonColumnWidthStyleStrategy
SeeyonHiddenSheetStrategy / SeeyonRowHeightStyleStrategy / SeeyonPropertyNamingStrategy
```

**⇒ 结论：** 用户说的「工具类，json，http，加密」全部在 `com.seeyon.boot.util`，共 **177 个**，我上一条已列全。

---

## 五、设计态生成构建（UDC）

### 5.1 代码生成（udc-biz 5.3.517，autocode 包 341 类）

**能力：** 元数据 → Java 类

**已知（来自 `02-codegen.md` + 签名库）：**
```
CodeTask          52 个实现
Template          36 个载体
AutoCodeExecutor  执行器
CodeContext / CodeParam / CodeTask
```

**生成物：** Entity / DTO / AppService / Service / DAO / Mapper / MyBatis XML / 表达式方法

**⚠️ 用户明确：「没必要了解 UDC 怎么调用它，只要知道它有什么能力、能做什么」**
**⇒ 研究重点从「怎么调」转向「生成什么、生成物长什么样」。**

### 5.2 元数据（extmetadata 106 类，见 §2.5）

**设计态：** MySQL `udc_entity` / `udc_attribute`
**运行态：** Redis（180h）→ OSS
**关键：** `*4OssService` 系列证明元数据落 OSS

### 5.3 构建与部署

| jar | 能力 |
|---|---|
| `udc-cicd`（65 类） | deploy（14）/ pipeline（11）/ repo（7） |
| `boot-starter-artifact`（16 类） | Maven 制品存取 |
| `devops-starter-artifact`（51 类） | DevOps 制品 |

### 5.4 微流程（udc-biz microflow 包 368 类）

**两类要完全分开（用户指正）：**

| 类型 | 实现方式 | 入口 |
|---|---|---|
| **自定义微流程** | **写代码**（Java 扩展） | 无节点概念，直接写 Service |
| **标准微流程** | **页面搭建**（拖节点） | 56 种 actionType |

**⚠️ 我之前的错误：把两者混为一谈。**
- 标准微流程：`BRANCH` / `RETRIEVE` / `CREATE_ENTITY` 等 56 种 actionType
- 自定义微流程：**没有节点**，是 Java 代码

---

## 六、用户特别强调的约束（已记录）

| # | 约束 | 来源 |
|---|---|---|
| **1** | **自定义微流程 ≠ 标准微流程**：一个写代码，一个搭页面，实现逻辑完全不同，必须完全分开 | 用户指正 |
| **2** | **自定义微流程不加数据库断言**：因为不一定能访问数据库 | 用户指正 |
| **3** | **标品应用（org/bpm/connector）走 Dubbo 或泛化调用** | 用户指正 |
| **4** | **业务组件（file/enum）走 @Autowired 直接调 Service / AppService** | 用户指正 |
| **5** | **工具类（json/http/加密/excel）是第三类** | 用户指正 |
| **6** | **表达式主要给 UDC 设计用，我的用处不大** | 用户指正 |
| **7** | **配置文件写到 Nacos 配置中心**（`ConfigCenterService`），不要只写本地 config | 用户指正 |
| **8** | **重点不是「UDC 怎么调」，而是「有什么能力、能做什么」** | 用户指正 |

---

## 七、三块空白已补完（2026-11-18）

**上一版标记的三个缺口全部补齐，详见：**

| 缺口 | 补齐情况 | 文档 |
|---|---|---|
| `boot-core/util` 177 类方法 | ✅ **全部 javap 提取，1,989 条签名** | `09-boot-core-utils.md` |
| `cip-capability-common` 355 Provider | ✅ **修正为 46 个能力接口**（355 是 DTO 数） | `15-connector-capabilities.md` |
| `boot-starter-graphql` 772 类 | ✅ **771 类里 701 是开源库，只有 71 个致远类** | `16-graphql-protocol.md` |

### 7.1 ★ 工具类实证要点（`09-boot-core-utils.md`）

**JsonUtils（25 方法）**
```
toJson / toJsonThrowError           失败静默 vs 抛异常
toJsonLongToString                  ★ 防 JS 精度丢失（雪花ID 19位 > 2^53）
toJsonDecimalToString               ★ 金额
fromJson(json, List.class, Dto.class)  泛型反序列化
```

**HttpClientUtil（大量重载）**
```
四层返回：String / <T>T / HttpResult / Map
判成功必须用 HttpResult 看 status，不能只看有没有抛异常
HttpClientRoundRobinRouting   ★ 平台自建 HTTP 负载均衡 + 心跳
```

**加密（4 类）**：`AESUtils` / `DESUtils` / `RSAUtils` / `MD5`+`SHA1`+`SHA256`
**⇒ 不要自己写 JCE，算法参数不一致会对不上。**

**Ids（7 方法）**
```
Ids.gidLong()           ★ 全平台主键生成
Ids.analyzeDate(id)     ★ 从雪花ID反解创建时间
```

**BeanCopier**：`copy(src, Target.class)` —— DTO↔Entity 标准转换
**Asserts（26）** / `Validators.assertjsr303` —— 手写校验 vs 注解校验
**StringUtils**：`maskMobileNo` / `maskByType`（★ 脱敏内建）、`toPinyin`（★ 拼音内建）
**DatabaseUtils**：`mysql2Dm/Oracle/Postgre/KingbaseV8/Sqlserver` —— 5 种方言

### 7.2 ★ 连接器实证要点（`15-connector-capabilities.md`）

**46 个能力接口**（不是 355 个 Provider）：

| 高频能力 | 方法数 | 能做什么 |
|---|---|---|
| `CapabilityManageAppService` | 53 | **能力管理（启停/切换 Provider）** |
| `SignatureAppService` | 39 | 电子签章（上传→发起→预签→盖章→验章） |
| `DocOnlineAppService` | 28 | 在线文档预览/编辑 |
| `OcrAppService` | 20 | 身份证/银行卡/名片/营业执照 OCR |
| `InvoiceAppService` | 9 | 发票 OCR + 验真 |
| `PayAppService` | 8 | H5 支付/退款/查单 |
| `FaceIdAppService` | 4 | 人脸录入/核验 |

**★★ `updateDefaultProvider` 说明能力层是「多 Provider 可切换」设计。**

**连接器（20 个 SPI）** —— 与能力完全不同：
```
中间表模式：MiddleTableOrgSyncSpiPull/Listener/Callback
移动端模式：MobileOrgSyncProvider / MobileTodoProvider
数据库：   DataBaseExecutorService
SSO：      SsoService
```
**⇒ 能力是「点」，连接器是「面」。**

### 7.3 ★ GraphQL 实证要点（`16-graphql-protocol.md`）

**772 类里只有 71 个是致远的，701 个是 graphql-java + antlr4 开源库。**

**★★ 核心发现：Schema 是动态从元数据生成的**
```
实体元数据 → MetadataProxyService → GraphQLTypeMappingUtil
  → SeeyonSchemaService → SeeyonSchema → GraphQLController
```
**⇒ 新建 UDC 实体自动多一套 GraphQL 接口，前端不用逐个写。**

**★★ 之前把 `udcMicroflowCreatePost` 当 REST 路径 —— 错，那是 GraphQL mutation 名。**
**⇒ 前端调 `POST /{appName}/graphql` + query/variables。**

**N+1 已内建解决：** `ChildrenDataLoader` 批量加载
**Long 精度：** `SeeyonScalars` 自定义 Scalar

---

## 八、仍然未覆盖（按优先级）
| # | jar | 类数 | 已知 | 缺口 |
|---|---|---|---|---|
| 1 | `udc-plugin-api` | 307 | 插件契约 | common(153)/detection(30)/dto(26) 具体内容 |
| 2 | `boot-starter-datamigration` | 247 | 数据迁移 | 迁移引擎机制 |
| 3 | `boot-starter-mybatis` | 140 | AllInOne 系列 | `AllInOneDBUtil` 具体方法 |
| 4 | `boot-starter-extmetadata` | 106 | 元数据服务清单 | 每个 MetaDataService 的读写时机 |
| 5 | `boot-starter-datainit` | 88 | 数据初始化 | 初始化什么、何时触发 |
| 6 | `boot-starter-serialnumber` | 85 | 流水号 | 编号规则怎么配、并发怎么保证 |
| 7 | `boot-starter-condition` | 77 | 条件 | 条件模型 |
| 8 | `boot-starter-mq` | 68 | 消息队列 | 队列模型 |
| 9 | `boot-starter-schedule` | 50 | 定时任务 | 调度机制 |
| 10 | `boot-starter-cache` | 50 | 类名已知 | `CacheUtils`/`RedisUtils` 具体方法 |
| 11 | `boot-starter-i18n` | 28 | 类名已知 | 资源加载时机 |
| 12 | `boot-starter-formula` | 202 | 公式引擎 | **用户说优先级低** |

**下一轮优先级建议：**
1. **`boot-starter-cache`（50）** —— 缓存是高频需求，方法少，快
2. **`boot-starter-serialnumber`（85）** —— 单据编号是业务刚需
3. **`boot-starter-mybatis`（140）** —— `AllInOneDBUtil` 是持久化核心
4. **`boot-starter-extmetadata`（106）** —— 元数据读写时机（设计态/运行态）
5. `udc-plugin-api`（307）—— 插件契约，扩展开发必看

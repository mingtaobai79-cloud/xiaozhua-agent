# CIP 集成族：cip-capability-common / boot-starter-cip / cip-manager-facade

## Capability

**集成平台（CIP）在客开侧可见的三个包**，职责分层很硬：

```
cip-capability-common   工具与注解（Base64/加密/短链/版本校验 + @CipChannelRouter 等）
boot-starter-cip        运行时能力（MQ 投递 / 文档版本 / 字段逃逸 / 单据 / V5 迁移）
cip-manager-facade      标品扩展面（组织集成 / 中间表 / 开放能力 / OpenAPI 文件与消息 / 预警）
```

> 只想「接一个外部系统」→ 用 `connector` 那套（`core/facts/connector/`）；
> 本格是**CIP 平台自身**的面，客开在做集成插件/中间表/开放能力时才碰。

## Version

`cip-capability-common` 5.3.276 / `boot-starter-cip` 5.3.603 / `cip-manager-facade` 5.3.273。

## ★ 一、cip-capability-common：能直接用的工具

```
Base64Util / Base64UrlUtil        编解码
EncryptUtils / Sha1Util           加密与摘要
ShortUrlGenerator                 短链生成
PdfConvertHtmlUtil                PDF → HTML
VersionCheckUtil                  版本比较
CommonUtil
@CipChannelRouter                 通道路由注解（provider 侧）
@CipDaoCondition / @CipDaoSelectEnum   Dao 条件/枚举映射注解
```

## ★ 二、boot-starter-cip：运行时能力（都是 AppService 形态）

```java
// MQ 投递（集成链里把消息投到 MQ）
SingleResponse<Boolean> deliveryMqMessage(SingleRequest<CipMqDeliveryInnerDto>);

// 文档版本（集成附件）
SingleResponse<DocFileDto>                 getAuthorityUploadStreamProxy(SingleRequest<DocAuthorityUploadStreamProxyRequestDto>);
SingleResponse<DocSaveVersionProxyResponseDto> saveVersionProxy(SingleRequest<DocSaveVersionProxyRequestDto>);
SingleResponse<DocFileVersion>             getDocFileVersionProxy(SingleRequest<DocFileVersionProxyRequestDto>);
SingleResponse<DocFileVersion>             createFileVersionInfo(SingleRequest<DocFileInfoStarterDto>);

// 字段逃逸（外部数据 ↔ 平台字段）
ListResponse<TableColumnInfoResultDto>     fetchColumnsByUniqueKey(SingleRequest<TableColumnInfoQueryDto>);   // EntityEscape
// EnumEscapeAppService / ParamEscapeAppService / WeakTypeEscapeService 同族

// 单据取值
SingleResponse<VoucherEntityResultDto>          queryVoucherData(SingleRequest<VoucherEntityQueryDto>);
ListResponse<Map<String,Object>>                getEntityColumnValues(SingleRequest<EntityColumnDto>);

// 其它
OpenApiErrorCodeAppService      开放接口错误码
V5MigrateAppService             V5 数据迁移
EscapeCacheService / VoucherCacheService   上述能力的缓存层
```

## ★ 三、cip-manager-facade：标品扩展面（按域）

```java
basic/OrgIntegrationAppService
  queryCardInfo / updateCardInfo / queryServiceTypeInfo / queryCardRunInfo / queryJsApiAddressByCode

plug/MiddleTableOperationAppService          // 中间表同步（组织域）
  saveUnit / saveLevel / savePost / saveDuty / saveMember   （全部 default 方法，返回 SingleResponse<Void>）

capability/OpenCapabilityAppService          // 开放能力开通与配额
  createApp / createTenantApp / updateAppCharges / queryUseCount / getTicket

openapi/CipFileAppService                    // 开放接口文件
  uploadFiles(SingleRequest<Void>) / deleteByStorageKeys(SingleRequest<FileDeleteDto>)

openapi/CipMessageAppService / OpenApiNotifyAppService / WarningManageAppService / WarningCallBackAppService
plug/PluginAffairAppService / PluginMessageAppService
custom/WarningManageAppService
```

## Side Effects

- `MiddleTableOperationAppService.saveXxx` 是**覆盖式同步**：传什么就是什么，不会保留平台侧多出来的数据。
- `CipFileAppService.deleteByStorageKeys` 是物理删（文件服务），删前确认没有业务引用。
- `OpenCapabilityAppService.updateAppCharges` 影响计费/配额，非运维场景别调。

## Known Constraints

1. 这三个包**不是给普通客开直接用的**：集成要做在 connector/插件扩展点上，本族是平台内部面。
2. `MiddleTableOperationAppService` 全 default 方法 → 实现类在平台内部，注入接口即可，别自己 new。
3. `OrgIntegrationAppService.queryCardRunInfo` 返回 `Map<String, QueryRunResDto>`（键是卡片编码），不是 List。
4. `cip-capability-common` 里没有「连接器」API——连接器在 `cip-connector-api`（已有格）。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 工具/注解类清单（12 个） | 类清单 + `javap` | VERIFIED_STATIC_BYTECODE |
| `CipMqDeliveryAppService` / `DocGeneralizeStarterAppService` 方法 | `javap -p` 5.3.603 | VERIFIED_STATIC_BYTECODE |
| `EntityEscapeAppService` / `VoucherAppService` 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `OrgIntegrationAppService` 5 方法、`MiddleTableOperationAppService` 5 个 save | `javap -p` 5.3.273 | VERIFIED_STATIC_BYTECODE |
| `OpenCapabilityAppService` 5 方法、`CipFileAppService` 2 方法 | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 全部签名逐字可复核
- ⚠️ 未真机调用（集成环境未起）

## 给 Agent 的判据

```
接外部系统            → 先看 connector 族，不是这一族
要投递 MQ             → CipMqDeliveryAppService.deliveryMqMessage
要同步组织中间表       → MiddleTableOperationAppService.saveUnit/saveLevel/savePost...
要开通/查配额         → OpenCapabilityAppService
要 PDF 转 HTML/短链   → cip-capability-common 的 PdfConvertHtmlUtil / ShortUrlGenerator
字段对不上（外部表）    → EntityEscapeAppService.fetchColumnsByUniqueKey
```

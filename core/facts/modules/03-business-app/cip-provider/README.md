# 集成提供方（provider）

## 一句话

`com.seeyon.cip` 域的**可调用接口面**：2 个构件、724 个类、48 个 facade 接口 / 330 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `cip-capability-api` | api | 369 |
| `cip-capability-common` | common | 355 |
| **合计** | | **724** |

## 二、分层规律（写代码前必读）

`com.seeyon.cip` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

| 接口族 | 包 | 能力 | 什么时候用 |
|---|---|---|---|
| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |
| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |
| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |

调用顺序建议：

```
知道 id       →  XxxCoreAppService.selectXxxById        （最轻）
知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData
要写          →  XxxBaseAppService.create / update
```

## facade 层：48 个接口 / 330 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.cip.provider.api` | 3 | 18 |
| `com.seeyon.cip.provider.api.Invoice` | 1 | 10 |
| `com.seeyon.cip.provider.api.ai` | 1 | 4 |
| `com.seeyon.cip.provider.api.archives` | 1 | 5 |
| `com.seeyon.cip.provider.api.bankpay` | 1 | 11 |
| `com.seeyon.cip.provider.api.callback` | 2 | 3 |
| `com.seeyon.cip.provider.api.censor` | 1 | 2 |
| `com.seeyon.cip.provider.api.common` | 10 | 22 |
| `com.seeyon.cip.provider.api.credit` | 1 | 25 |
| `com.seeyon.cip.provider.api.doc` | 2 | 25 |
| `com.seeyon.cip.provider.api.econtracts` | 1 | 6 |
| `com.seeyon.cip.provider.api.email` | 1 | 2 |
| `com.seeyon.cip.provider.api.faceid` | 1 | 5 |
| `com.seeyon.cip.provider.api.gis` | 1 | 2 |
| `com.seeyon.cip.provider.api.location` | 1 | 7 |
| `com.seeyon.cip.provider.api.message` | 1 | 2 |
| `com.seeyon.cip.provider.api.missive` | 1 | 32 |
| `com.seeyon.cip.provider.api.ocr` | 1 | 8 |
| `com.seeyon.cip.provider.api.ofd` | 1 | 7 |
| `com.seeyon.cip.provider.api.pay` | 1 | 9 |
| `com.seeyon.cip.provider.api.physicalseal` | 1 | 9 |
| `com.seeyon.cip.provider.api.print.label` | 1 | 1 |
| `com.seeyon.cip.provider.api.resume` | 1 | 2 |
| `com.seeyon.cip.provider.api.schedule` | 1 | 5 |
| `com.seeyon.cip.provider.api.search` | 1 | 2 |
| `com.seeyon.cip.provider.api.signature.electronic` | 1 | 42 |
| `com.seeyon.cip.provider.api.sms` | 3 | 15 |
| `com.seeyon.cip.provider.api.test` | 1 | 2 |
| `com.seeyon.cip.provider.api.translation` | 1 | 3 |
| `com.seeyon.cip.provider.api.trip` | 1 | 14 |
| `com.seeyon.cip.provider.api.video` | 1 | 18 |
| `com.seeyon.cip.provider.api.voice` | 1 | 8 |
| `com.seeyon.cip.provider.api.weather` | 1 | 4 |
| **合计** | **48** | **330** |

### `com.seeyon.cip.provider.api`

#### CipCapabilityRemotingInvoker

`com.seeyon.cip.provider.api.CipCapabilityRemotingInvoker` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `remoteInvoke` | `—` | `V` | 调用 |

#### ProviderService

`com.seeyon.cip.provider.api.ProviderService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getBeanName` | `—` | `String` | 获取名称Bean |
| `getDescription` | `—` | `String` | 获取Description |
| `checkConfig` | `—` | `boolean` | 检查配置 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `getChannelCode` | `—` | `String` | 获取通道编码 |
| `getFeatures` | `—` | `List<ServiceFeatureDto>` | 获取Features |
| `deleteToken` | `—` | `void` | 删除令牌 |
| `checkFeature` | `—` | `List<ServiceFeatureDto>` | 检查Feature |
| `getFeatureDto` | `String arg0` | `ServiceFeatureDto` | 获取FeatureDto |
| `getConfigMap` | `—` | `Map<String, Map<String, Map<String, String>>>` | 获取配置Map |
| `getParamsMap` | `—` | `Map<String, String>` | 获取ParamsMap |
| `getInfo` | `—` | `Map<String, Map<String, String>>` | 获取 |
| `getInfoMap` | `—` | `Map<String, String>` | 获取Map |

#### RoutingService

`com.seeyon.cip.provider.api.RoutingService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getProvider` | `CapabilityEnum arg0` | `ProviderService` | 获取Provider |
| `getDebuggingProvider` | `CapabilityEnum arg0` | `ProviderService` | 获取DebuggingProvider |
| `getProviderByName` | `CapabilityEnum arg0` | `ProviderService` | 获取Provider按名称 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.Invoice`

#### InvoiceProviderService

`com.seeyon.cip.provider.api.Invoice.InvoiceProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getInvoicesOcr` | `InvoiceSingleOcrApiDto arg0` | `InvoiceOutItemApiDto` | 获取InvoicesOcr |
| `getInvoicesOcr` | `InvoiceOcrProviderApiDto arg0` | `List<InvoiceOutItemApiDto>` | 获取InvoicesOcr |
| `checkBatchInvoice` | `InvoiceCheckApiDto arg0` | `InvoiceCheckOutApiDto` | 批量检查Invoice |
| `batchGetCheck` | `String arg0` | `InvoiceCheckOutApiDto` | 获取Check |
| `singleCheck` | `InvoiceCheckItemApiDto arg0` | `InvoiceCheckOutItemApiDto` | 检查（InvoiceCheckItemApiDto） |
| `createImageTask` | `InvoiceImageApiReqDto arg0` | `InvoiceImageApiResDto` | 新建任务Image |
| `uploadImageFile` | `InvoiceImageUploadApiReqDto arg0` | `InvoiceImageUploadApiResDto` | 上传文件Image |
| `imageFileSize` | `—` | `int` | 发票提供方：校验发票图片大小限制 |
| `imageFormat` | `—` | `String` | 格式化 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.ai`

#### AiProviderService

`com.seeyon.cip.provider.api.ai.AiProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `createThirdApp` | `AiAppInfoDto arg0` | `AiThirdAppInfoDto` | 新建第三方应用 |
| `thirdAppIncrease` | `AiAppIncreaseDto arg0` | `AiThirdAppInfoDto` | AI 提供方：从第三方按增量拉取 |
| `queryUsageAmount` | `AiAppUsageQueryDto arg0` | `AiAppUsageInfoDto` | 查询UsageAmount |

### `com.seeyon.cip.provider.api.archives`

#### ArchivesProviderService

`com.seeyon.cip.provider.api.archives.ArchivesProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `titleAttribute` | `—` | `String` | 档案提供方：取档案标题字段 |
| `queryArchiveSystemCategory` | `Long arg0` | `List<ArchiveSettingCategoryDto>` | 查询分类ArchiveSystem |
| `selectAttributesByTypeIds` | `FieldMappingRequestDto arg0` | `List<FieldMappingDto>` | 查询Attributes按类型 |
| `startArchiving` | `ArchivingInfoWrapperDto arg0` | `ArchiveResultDto` | 启动Archiving |

### `com.seeyon.cip.provider.api.bankpay`

#### BankpayProviderService

`com.seeyon.cip.provider.api.bankpay.BankpayProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `balanceQuery` | `BalanceQueryReqDto arg0` | `BalanceQueryRespDto` | 查询（BalanceQueryReqDto） |
| `paymentTransfer` | `PaymentTransferReqDto arg0` | `PaymentTransferRespDto` | 转移（PaymentTransferReqDto） |
| `accountDetail` | `AccountDetailReqDto arg0` | `PageData<AccountDetailRespDto>` | 银企提供方：查账户明细 |
| `accountSummary` | `AccountDetailReqDto arg0` | `PageData<AccountSummaryRespDto>` | 银企提供方：查账户汇总 |
| `accountInDetail` | `AccountInDetailReqDto arg0` | `AccountInDetailRespDto` | 银企提供方：查账户入账明细 |
| `expensesFinance` | `ExpenseReqDto arg0` | `ExpenseRespDto` | 银企提供方：查费用/财务数据 |
| `cityCodeComparisonTableDownload` | `CityCodeComparisonTableDownloadReqDto arg0` | `List<CityCodeComparisonTableDownloadRespDto>` | 银企提供方：下载城市编码对照表 |
| `currencyCodeComparisonTableDownload` | `CurrencyCodeComparisonTableDownloadReqDto arg0` | `List<CurrencyCodeComparisonTableDownloadRespDto>` | 银企提供方：下载币种编码对照表 |
| `paymentBankInformation` | `PaymentBankInformationReqDto arg0` | `List<PaymentBankInformationRespDto>` | 银企提供方：查付款银行信息 |
| `accountNameCheck` | `AccountNameCheckReqDto arg0` | `AccountNameCheckRespDto` | 检查（AccountNameCheckReqDto） |
| `transactionStatusQuery` | `TransactionStatusQueryReqDto arg0` | `TransactionStatusQueryRespDto` | 查询（TransactionStatusQueryReqDto） |

### `com.seeyon.cip.provider.api.callback`

#### CipCallbackMessageSendService

`com.seeyon.cip.provider.api.callback.CipCallbackMessageSendService` · 构件 `cip-capability-api` · extends `BaseDto>`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendMsgAsync` | `T arg0` | `void` | 发送MsgAsync |
| `sendMsgSync` | `T arg0` | `void` | 发送MsgSync |

#### CipCallbackProviderService

`com.seeyon.cip.provider.api.callback.CipCallbackProviderService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `doCallback` | `CipCallbackRequestDto arg0` | `Res` | SPI 扩展点：Callback（框架回调） |

### `com.seeyon.cip.provider.api.censor`

#### CensorProviderService

`com.seeyon.cip.provider.api.censor.CensorProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `textCensor` | `TextCensorApiReqDto arg0` | `TextCensorApiResDto` | 内容审核提供方：文本送审 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.common`

#### CapabilityManageCallback

`com.seeyon.cip.provider.api.common.CapabilityManageCallback` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `open` | `Long arg0` | `void` | 打开（Long） |
| `close` | `Long arg0` | `void` | 关闭（Long） |

#### CipAccessLogDbService

`com.seeyon.cip.provider.api.common.CipAccessLogDbService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByConditions` | `PageInfo arg0` | `PageData<CipAccessOpenLogDto>` | 分页查询按条件（PageInfo） |
| `deleteById` | `Long arg0` | `void` | 删除按 id（Long） |
| `update` | `CipAccessOpenLogDto arg0` | `void` | 修改（CipAccessOpenLogDto） |

#### CipMonitorRule

`com.seeyon.cip.provider.api.common.CipMonitorRule` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `doMonitorExecute` | `Long arg0` | `Boolean` | SPI 扩展点：MonitorExecute（框架回调） |

#### CompanyAccountApiService

`com.seeyon.cip.provider.api.common.CompanyAccountApiService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAccount` | `Long arg0` | `CompanyAccountData` | 获取账户 |
| `getAppKey` | `String arg0` | `String` | 获取应用键 |

#### ContractSignMessagePublishApiService

`com.seeyon.cip.provider.api.common.ContractSignMessagePublishApiService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `publishFileUpdateMessage` | `Long arg0` | `void` | 发布文件消息Update |
| `publishSignTaskFinishMessage` | `Long arg0` | `void` | 发布任务消息SignFinish |

#### LogService

`com.seeyon.cip.provider.api.common.LogService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveLog` | `CipAccessLogDto arg0` | `void` | 保存日志 |
| `getLogDto` | `ProviderService arg0` | `CipAccessLogDto` | 获取日志Dto |

#### ParameterService

`com.seeyon.cip.provider.api.common.ParameterService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getProviderParameter` | `String arg0` | `Map<String, String>` | 获取参数Provider |
| `getProviderParameter` | `String arg0` | `Object` | 获取参数Provider |
| `getProviderParameterRefresh` | `String arg0` | `Object` | 获取参数ProviderRefresh |
| `getProviderParameterMapRefresh` | `String arg0` | `Map<String, String>` | 获取参数ProviderMapRefresh |
| `refreshProviderParameter` | `String arg0` | `void` | 刷新参数Provider |
| `getProviderParameterIgnoreTenant` | `String arg0` | `Long` | 获取参数Provider |

#### SealSynchronizeService

`com.seeyon.cip.provider.api.common.SealSynchronizeService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `synchronize` | `ContractsProviderService arg0` | `void` | 印章提供方：同步印章数据（定时/触发） |

#### StandardCodeSwitchService

`com.seeyon.cip.provider.api.common.StandardCodeSwitchService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `response` | `String arg0` | `CipProvideResultDto` | 标准码转换提供方：把第三方返回码转成平台标准码 |

#### TokenManagerService

`com.seeyon.cip.provider.api.common.TokenManagerService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getDefinitionToken` | `String arg0` | `String` | 获取令牌Definition |
| `getRegisterToken` | `TokenDefinition arg0` | `String` | 获取令牌Register |

### `com.seeyon.cip.provider.api.credit`

#### CreditProviderService

`com.seeyon.cip.provider.api.credit.CreditProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getEnterpriseInfo` | `Integer arg0` | `EnterpriseInfoResponseData` | 获取Enterprise |
| `getBasicBusinessInfo` | `String arg0` | `EnterpriseBasicBusinessInfoResponseData` | 获取业务Basic |
| `getBasicInfo` | `CreditRequestDto arg0` | `EnterpriseBasicInfoDto` | 获取Basic |
| `getPartners` | `CreditRequestDto arg0` | `EnterprisePartnersDto` | 获取Partners |
| `getCourtNotice` | `CreditRequestDto arg0` | `EnterpriseCourtNoticeDto` | 获取通知Court |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `getCaseDetailList` | `CreditRequestDto arg0` | `EnterpriseCaseDetailDto` | 列表获取流程实例Detail |
| `getAdminPunish` | `CreditRequestDto arg0` | `EnterpriseAdminPunishDto` | 获取AdminPunish |
| `getEnvp` | `CreditRequestDto arg0` | `EnterpriseEnvpDto` | 获取Envp |
| `getEnvpDetail` | `CreditRequestDto arg0` | `EnterpriseEnvpDetailDto` | 获取EnvpDetail |
| `getBiddingList` | `CreditRequestDto arg0` | `EnterpriseBiddingDto` | 列表获取Bidding |
| `getBiddingDetail` | `CreditRequestDto arg0` | `EnterpriseBiddingDetailDto` | 获取BiddingDetail |
| `getAdministrativeLicenseList` | `CreditRequestDto arg0` | `EnterpriseAdministrativeLicenseDto` | 列表获取AdministrativeLicense |
| `getEntCreditRating` | `CreditRequestDto arg0` | `EnterpriseEntCreditRatingDto` | 获取EntCreditRating |
| `getTaxpayerList` | `CreditRequestDto arg0` | `List<EnterpriseTaxpayerDto>` | 列表获取Taxpayer |
| `getTrademark` | `CreditRequestDto arg0` | `EnterpriseTrademarkDto` | 获取Trademark |
| `getTrademarkDetail` | `CreditRequestDto arg0` | `EnterpriseTrademarkDetailDto` | 获取TrademarkDetail |
| `getPatentList` | `CreditRequestDto arg0` | `EnterprisePatentDto` | 列表获取Patent |
| `getPatentDetail` | `CreditRequestDto arg0` | `EnterprisePatentDetailDto` | 获取PatentDetail |
| `getCopyrightSoft` | `CreditRequestDto arg0` | `EnterpriseCopyrightSoftDto` | 获取CopyrightSoft |
| `getCertificate` | `CreditRequestDto arg0` | `EnterpriseCertificateDto` | 获取Certificate |
| `getProject` | `CreditRequestDto arg0` | `EnterpriseProjectDto` | 获取Project |
| `getFinancing` | `CreditRequestDto arg0` | `EnterpriseFinancingDto` | 获取Financing |
| `getShellEntInfoByName` | `CreditRequestDto arg0` | `EnterpriseShellEntInfoDto` | 获取ShellEnt按名称 |
| `getEntJusticeScore` | `CreditRequestExtendDto arg0` | `EntJusticeScoreDto` | 获取EntJusticeScore |

### `com.seeyon.cip.provider.api.doc`

#### DocFileService

`com.seeyon.cip.provider.api.doc.DocFileService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getDownloadUrl` | `DocFileReqDto arg0` | `String` | 获取DownloadUrl |
| `uploadFile` | `InputStream arg0` | `FileDto` | 上传文件 |
| `getDecodeInputStream` | `DocFileReqDto arg0` | `InputStream` | 获取DecodeInputStream |
| `updateProperties` | `Map<String, Object> arg0` | `Boolean` | 指定字段修改（Map） |
| `checkAndEncryptFile` | `DocEncryptFileApiReqDto arg0` | `DocEncryptFileApiResDto` | 检查文件AndEncrypt |

#### DocOnlineProviderService

`com.seeyon.cip.provider.api.doc.DocOnlineProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `checkToken` | `String arg0` | `Map<String, Object>` | 检查令牌 |
| `getDocOnlineProperties` | `—` | `FilePropertiesDto` | 指定字段获取在线Doc |
| `getOfficeViewUrl` | `FileViewDto arg0` | `DocUrlDto` | 获取OfficeUrl |
| `getOfficeEditUrl` | `FileEditDto arg0` | `DocUrlDto` | 获取OfficeEditUrl |
| `cpsOfficeOperateClean` | `FileOperateCleanDto arg0` | `FileOperateCleanDto` | 在线文档提供方：清理文档 |
| `cpsCleanSupportFileFormat` | `—` | `List<String>` | 清理文件SupportFormat |
| `cpsOfficeOperateTextWatermark` | `FileOperateTextWatermarkDto arg0` | `FileOperateTextWatermarkDto` | 在线文档提供方：加文字水印 |
| `cpsOfficeOperateImageWatermark` | `FileOperateImageWatermarkDto arg0` | `FileOperateImageWatermarkDto` | 在线文档提供方：加图片水印 |
| `cpsOfficeConvert` | `FileConvertDto arg0` | `FileConvertDto` | 转换（FileConvertDto） |
| `cpsDownload` | `Map<String, Object> arg0` | `FileConvertResultDto` | 下载（Map） |
| `cpsTaskQuery` | `String arg0` | `FileConvertResultDto` | 查询（String） |
| `getDocumentTemplateTab` | `FileConvertDto arg0` | `FileConvertDto` | 获取模板DocumentTab |
| `cpsWrapHeader` | `FileWrapHeaderDto arg0` | `FileWrapHeaderDto` | 在线文档提供方：抽取文档头 |
| `setBookmarkPermissions` | `FileSetBookmarkPermissionsApiDto arg0` | `FileSetBookmarkPermissionsApiDto` | 设置BookmarkPermissions |
| `cpsMerge` | `FileMergeDto arg0` | `FileMergeResDto` | 合并（FileMergeDto） |
| `extractPictures` | `DocExtractPicApiReqDto arg0` | `DocExtractPicApiResDto` | 在线文档提供方：抽取图片 |
| `getFileUrl` | `DocFileUrlApiReqDto arg0` | `DocFileUrlApiResDto` | 获取文件Url |
| `closeFile` | `DocCloseFileApiReqDto arg0` | `DocCloseFileApiResDto` | 关闭文件 |
| `fileFormat` | `—` | `String` | 格式化 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.econtracts`

#### ContractsProviderService

`com.seeyon.cip.provider.api.econtracts.ContractsProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `invokeApi` | `ContractApiUrlable arg0` | `BaseContractsResponseData` | 调用API |
| `invokeApiWithFile` | `ContractApiUrlable arg0` | `BaseContractsResponseData` | 调用API文件With |
| `getAccessTokenApi` | `String arg0` | `String` | 获取可见令牌API |
| `invokeApiSynCallBack` | `ContractApiUrlable arg0` | `String` | 调用APISynCallBack |
| `getMaxSealSize` | `—` | `Long` | 获取MaxSealSize |
| `getValidImageFormat` | `—` | `String` | 获取ValidImageFormat |

### `com.seeyon.cip.provider.api.email`

#### EmailProviderService

`com.seeyon.cip.provider.api.email.EmailProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendEmail` | `String arg0` | `CipProvideResultDto` | 发送Email |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.faceid`

#### FaceIdProviderService

`com.seeyon.cip.provider.api.faceid.FaceIdProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `addFace` | `FaceAddApiReqDto arg0` | `FaceAddApiResDto` | 新增Face |
| `faceCheck` | `FaceIdentifyApiReqDto arg0` | `FaceIdentifyApiResDto` | 检查（FaceIdentifyApiReqDto） |
| `updateFace` | `FaceUpdateApiReqDto arg0` | `FaceUpdateApiResDto` | 修改Face |
| `getAccessToken` | `—` | `String` | 获取可见令牌 |

### `com.seeyon.cip.provider.api.gis`

#### GisProviderService

`com.seeyon.cip.provider.api.gis.GisProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `getToken` | `GisTokenRequestDto arg0` | `String` | 获取令牌 |

### `com.seeyon.cip.provider.api.location`

#### LocationProviderService

`com.seeyon.cip.provider.api.location.LocationProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getLocation` | `—` | `String` | 获取Location |
| `regionSearch` | `RegionDto arg0` | `List<DistrictsDto>` | 搜索（RegionDto） |
| `getJsApiInfo` | `—` | `JsApiDto` | 获取APIJs |
| `geocoding` | `GeocoderRequestDto arg0` | `GeocoderResultDto` | 地图提供方：地址转经纬度 |
| `keywordSearch` | `KeywordSearchDto arg0` | `List<SearchResultDto>` | 搜索（KeywordSearchDto） |
| `aroundSearch` | `AroundSearchDto arg0` | `List<SearchResultDto>` | 搜索（AroundSearchDto） |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.message`

#### OfflineMessageProviderService

`com.seeyon.cip.provider.api.message.OfflineMessageProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pushMessage` | `OfflineMessageDto arg0` | `void` | 推送消息 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.missive`

#### IntelligentMissiveProviderService

`com.seeyon.cip.provider.api.missive.IntelligentMissiveProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `getPropertiesDto` | `—` | `PropertiesDto` | 指定字段获取Dto |
| `createRecommend` | `RecommendApiReqDto arg0` | `RecommendApiResDto` | 新建Recommend |
| `createWrite` | `IntelligentWriteApiReqDto arg0` | `IntelligentWriteApiResDto` | 新建Write |
| `queryWrite` | `IntelligentWriteQueryApiReqDto arg0` | `IntelligentWriteQueryApiResDto` | 查询Write |
| `queryCardPage` | `CardPageApiReqDto arg0` | `CardPageApiResDto` | 分页查询Card |
| `createExtractingTask` | `ExtractingTaskApiReqDto arg0` | `ExtractingTaskApiResDto` | 新建任务Extracting |
| `queryExtractingPage` | `ExtractingPageApiReqDto arg0` | `ExtractingPageApiResDto` | 分页查询Extracting |
| `queryExtractingDetail` | `ExtractingDetailApiReqDto arg0` | `ExtractingDetailApiResDto` | 查询ExtractingDetail |
| `queryDiffRule` | `DiffRuleApiReqDto arg0` | `DiffRuleApiResDto` | 查询规则Diff |
| `createDocDiffTask` | `DiffTaskApiReqDto arg0` | `DiffTaskApiResDto` | 新建任务DocDiff |
| `queryDocDiffPage` | `DiffPageApiReqDto arg0` | `DiffPageApiResDto` | 分页查询DocDiff |
| `queryDocDiffDetail` | `DiffDetailApiReqDto arg0` | `DiffDetailApiResDto` | 查询DocDiffDetail |
| `downloadDiffFile` | `Map<String, Object> arg0` | `DiffDownApiResDto` | SPI 扩展点：文件（框架回调） |
| `queryDocDiffView` | `DiffDetailApiReqDto arg0` | `DiffDetailViewApiResDto` | 查询DocDiff |
| `queryCardRule` | `CardRuleApiReqDto arg0` | `CardRuleApiResDto` | 查询规则Card |
| `createReviewTask` | `ReviewTaskApiReqDto arg0` | `ReviewTaskApiResDto` | 新建任务Review |
| `queryReviewPage` | `ReviewPageApiReqDto arg0` | `ReviewPageApiResDto` | 分页查询Review |
| `queryReviewDetail` | `ReviewDetailApiReqDto arg0` | `ReviewDetailApiResDto` | 查询ReviewDetail |
| `createTableTask` | `TableTaskApiReqDto arg0` | `TableTaskApiResDto` | 新建表任务 |
| `queryTableDetail` | `TableDetailApiReqDto arg0` | `TableDetailApiResDto` | 查询表Detail |
| `createSettingByTemplate` | `SettingTaskApiReqDto arg0` | `SettingTaskApiResDto` | 新建设置按模板 |
| `createOnlineProofread` | `ProofreadTaskApiReqDto arg0` | `ProofreadTaskApiResDto` | 新建在线Proofread |
| `queryProofreadDetail` | `ProofreadTaskDetailApiReqDto arg0` | `ProofreadTaskApiResDto` | 查询ProofreadDetail |
| `checkSensitiveWord` | `SensitiveWordApiReqDto arg0` | `SensitiveWordApiResDto` | 检查敏感Word |
| `uploadTempFile` | `UploadTempFileApiReqDto arg0` | `UploadTempFileApiResDto` | 上传文件Temp |
| `pushOfficial` | `IntelligentPushOfficialApiReqDto arg0` | `IntelligentPushOfficialApiResDto` | 推送Official |
| `assistReading` | `AssistReadingApiReqDto arg0` | `AssistReadingApiResDto` | 智能公文提供方：辅助阅读 |
| `queryResultByTaskId` | `QueryResultApiReqDto arg0` | `QueryResultApiResDto` | 查询Result按任务 |
| `readingDetail` | `ReadingDetailApiReqDto arg0` | `ReadingDetailApiResDto` | 智能公文提供方：阅读详情 |
| `retrieval` | `RetrievalApiReqDto arg0` | `RetrievalApiResDto` | 智能公文提供方：语义检索 |
| `queryRelated` | `RelatedApiReqDto arg0` | `RelatedApiResDto` | 查询Related |

### `com.seeyon.cip.provider.api.ocr`

#### OcrProviderService

`com.seeyon.cip.provider.api.ocr.OcrProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOcrByBase64` | `String arg0` | `CipBaseResponseData` | 获取Ocr按Base64 |
| `getOcrByBase64` | `String arg0` | `OcrCommonResultDto` | 获取Ocr按Base64 |
| `verificationInvoice` | `String arg0` | `InvoiceVerificationResponseData` | OCR 提供方：发票查验 |
| `getOcrByCustom` | `String arg0` | `CipBaseResponseData` | 获取Ocr按Custom |
| `imageFileSize` | `—` | `int` | OCR 提供方：校验图片大小 |
| `imageFormat` | `—` | `String` | 格式化 |
| `extractContent` | `ExtractContentApiReqDto arg0` | `ExtractContentApiResDto` | OCR 提供方：文字抽取 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.ofd`

#### OfdProviderService

`com.seeyon.cip.provider.api.ofd.OfdProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `checkToken` | `String arg0` | `Map<String, Object>` | 检查令牌 |
| `getOfdViewUrl` | `OfdFileApiRequestDto arg0` | `OfdFileApiResponseDto` | 获取OfdUrl |
| `downFile` | `OfdDownApiReqDto arg0` | `OfdDownApiResDto` | SPI 扩展点：文件（框架回调） |
| `getSealInfo` | `OfdSealApiReqDto arg0` | `OfdSealApiResDto` | 获取Seal |
| `getOfdProperties` | `—` | `OfdPropertiesDto` | 指定字段获取Ofd |
| `getSealList` | `String arg0` | `List<OfdSealItemApiReqDto>` | 列表获取Seal |

### `com.seeyon.cip.provider.api.pay`

#### PayProviderService

`com.seeyon.cip.provider.api.pay.PayProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `h5Pay` | `H5PayOrderParamsDto arg0` | `H5PayOrderResultDto` | 支付提供方：H5 支付 |
| `queryTransactionByOutTradeNo` | `TransactionParamsDto arg0` | `TransactionResultDto` | 查询Transaction按OutTradeNo |
| `closeTransaction` | `TransactionParamsDto arg0` | `void` | 关闭Transaction |
| `refund` | `RefundParamsDto arg0` | `RefundResultDto` | 支付提供方：退款 |
| `queryRefund` | `QueryRefundParamsDto arg0` | `QueryRefundResultDto` | 查询Refund |
| `downloadTradeBill` | `BillDownloadParamsDto arg0` | `BillDownloadResultDto` | SPI 扩展点：downloadTradeBill（框架回调） |
| `downloadFundFlowBill` | `BillDownloadParamsDto arg0` | `BillDownloadResultDto` | SPI 扩展点：downloadFundFlowBill（框架回调） |
| `getCert` | `CertificateReqDto arg0` | `List<CertificateDto>` | 获取Cert |

### `com.seeyon.cip.provider.api.physicalseal`

#### PhysicalSealProviderService

`com.seeyon.cip.provider.api.physicalseal.PhysicalSealProviderService` · 构件 `cip-capability-api` · extends `ProviderService, CipCallbackProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `syncDept` | `PhysicalSealDeptDto arg0` | `void` | 同步部门 |
| `syncMember` | `PhysicalSealMemberDto arg0` | `void` | 同步成员 |
| `applyAuthorize` | `PhysicalSealApplyDto arg0` | `String` | 实体印章提供方：申请用印授权 |
| `queryApplyRecord` | `String arg0` | `String` | 查询ApplyRecord |
| `cancelApply` | `String arg0` | `void` | 取消Apply |
| `querySeals` | `—` | `PhysicalSealsDto` | 查询Seals |
| `getImageByApplyId` | `String arg0` | `PhysicalSealImagesDto` | 获取Image按ApplyId |
| `getImage` | `PhysicalSealImageDto arg0` | `List<PhysicalSealFileDto>` | 获取Image |

### `com.seeyon.cip.provider.api.print.label`

#### LabelPrintProviderService

`com.seeyon.cip.provider.api.print.label.LabelPrintProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.resume`

#### ResumeProviderService

`com.seeyon.cip.provider.api.resume.ResumeProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `analysisResume` | `ResumeRequestDto arg0` | `ResumeResultDto` | 恢复（ResumeRequestDto） |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.schedule`

#### ScheduleProviderService

`com.seeyon.cip.provider.api.schedule.ScheduleProviderService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `addSchedule` | `AddScheduleDto arg0` | `ScheduleInfoDto` | 新增调度 |
| `updateSchedule` | `UpdateScheduleDto arg0` | `ScheduleInfoDto` | 修改调度 |
| `cancelSchedule` | `ScheduleInfoDto arg0` | `void` | 取消调度 |
| `detailSchedule` | `ScheduleInfoDto arg0` | `ScheduleDetailDto` | 日程提供方：查日程详情 |

### `com.seeyon.cip.provider.api.search`

#### SearchProviderService

`com.seeyon.cip.provider.api.search.SearchProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `querySearchUrl` | `QuerySearchApiReqDto arg0` | `QuerySearchApiResDto` | 查询SearchUrl |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.signature.electronic`

#### SignatureProviderService

`com.seeyon.cip.provider.api.signature.electronic.SignatureProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `checkToken` | `String arg0` | `Map<String, Object>` | 检查令牌 |
| `getSignatureViewUrl` | `SignatureFileApiRequestDto arg0` | `SignatureFileApiResponseDto` | 获取SignatureUrl |
| `downFile` | `SignatureDownApiReqDto arg0` | `SignatureDownApiResDto` | SPI 扩展点：文件（框架回调） |
| `getSealInfo` | `SignatureSealApiReqDto arg0` | `SignatureSealApiResDto` | 获取Seal |
| `getSignatureProperties` | `—` | `SignaturePropertiesDto` | 指定字段获取Signature |
| `uploadFile` | `UploadFileDto arg0` | `FileInfoDto` | 上传文件 |
| `initiateSign` | `InitiateSignDto arg0` | `InitiateSignResultDto` | 签署（InitiateSignDto） |
| `initiateSignFree` | `InitiateSignFreeDto arg0` | `InitiateSignResultDto` | 签署Free |
| `createOrg` | `OrganizationDto arg0` | `OrganizationResultDto` | 新建组织 |
| `updateOrg` | `OrganizationUpdateDto arg0` | `OrganizationResultDto` | 修改组织 |
| `detailOrg` | `OrganizationQueryDto arg0` | `OrganizationDetailDto` | 电子签提供方：查组织详情 |
| `createUser` | `BatchCreateUserDto arg0` | `UserResultDto` | 新建用户 |
| `userUpdate` | `UserUpdateDto arg0` | `SuccessData` | 修改（UserUpdateDto） |
| `userDetail` | `UserQueryDto arg0` | `UserUpdateDto` | 电子签提供方：查用户详情 |
| `selectPageByConditions` | `PageInfo arg0` | `PageData<TemplateInfoDto>` | 分页查询按条件（PageInfo） |
| `getTemplateContents` | `TemplateBaseDto arg0` | `TemplateControlResultDto` | 获取模板Contents |
| `generatePdfFile` | `GeneratePdfDto arg0` | `GeneratePdfResultDto` | 生成文件Pdf |
| `signToolsConfig` | `SignAreaConfigDto arg0` | `SignAreaResultDto` | 签署配置Tools |
| `signToolsConfigDetail` | `SignAreaSelectDto arg0` | `SignAreaDetailDto` | 签署配置ToolsDetail |
| `verifySignature` | `VerifySignatureDto arg0` | `VerifySignatureResultDto` | 校验Signature |
| `sealList` | `PageInfo arg0` | `PageData<SealDataDto>` | 列出（PageInfo） |
| `downLoadFile` | `FileInfoDto arg0` | `FileDownloadDto` | SPI 扩展点：文件（框架回调） |
| `invalidFlow` | `InvalidFlowReqDto arg0` | `InvalidFlowResDto` | 电子签提供方：作废签署流程 |
| `createOuterOrg` | `OuterOrganizationDto arg0` | `OrganizationResultDto` | 新建组织Outer |
| `updateOuterOrg` | `OuterOrganizationUpdateDto arg0` | `OrganizationResultDto` | 修改组织Outer |
| `detailOuterOrg` | `OrganizationQueryDto arg0` | `OuterOrganizationDetailDto` | 电子签提供方：查外部组织 |
| `createOuterUser` | `OuterBatchCreateUserDto arg0` | `UserResultDto` | 新建用户Outer |
| `outerUserUpdate` | `OuterUserUpdateDto arg0` | `SuccessData` | 修改（OuterUserUpdateDto） |
| `outerUserDetail` | `UserQueryDto arg0` | `OuterUserUpdateDto` | 电子签提供方：查外部用户 |
| `deleteInnerUsers` | `DeleteInnerUsersReqDto arg0` | `DeleteInnerUsersResDto` | 删除InnerUsers |
| `querySsoUrl` | `QuerySsoReqDto arg0` | `QuerySsoResDto` | 查询SsoUrl |
| `sealSigners` | `PageInfo arg0` | `PageData<SealSignerDataDto>` | 电子签提供方：取可签署人 |
| `stamp` | `ThreePartySealIntegrationDto arg0` | `String` | 电子签提供方：盖章 |
| `withfileupload` | `ThreePartySealIntegrationDto arg0` | `ContractResponseDto` | 电子签提供方：带文件上传签署 |
| `invalid` | `ThreePartySealIntegrationDto arg0` | `AgainContractResponse` | 电子签提供方：作废 |
| `recall` | `ThreePartySealIntegrationDto arg0` | `SingleResponse` | 电子签提供方：撤回 |
| `sealGetList` | `ThreePartySealIntegrationDto arg0` | `SealListResultDto` | 列表获取（ThreePartySealIntegrationDto） |
| `preSign` | `PreSignDto arg0` | `String` | 签署（PreSignDto） |
| `initPreSign` | `InitPreSignDto arg0` | `String` | 初始化PreSign |
| `verifySeal` | `VerifySealDto arg0` | `String` | 校验Seal |
| `finish` | `ContractLockRequestDto arg0` | `SingleResponse` | 完成（ContractLockRequestDto） |

### `com.seeyon.cip.provider.api.sms`

#### SmsProviderService

`com.seeyon.cip.provider.api.sms.SmsProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendShortMessage` | `String arg0` | `CipProvideResultDto` | 发送消息Short |
| `inspectShortMessageSend` | `SmsInspectionDTO arg0` | `CipProvideResultDto` | 短信提供方：查发送状态 |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

#### SmsSignAutoService

`com.seeyon.cip.provider.api.sms.SmsSignAutoService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addSign` | `SmsSignDto arg0` | `String` | 新增Sign |
| `querySign` | `String arg0` | `SmsSignDto` | 查询Sign |
| `updateSign` | `SmsSignDto arg0` | `String` | 修改Sign |
| `deleteSign` | `String arg0` | `void` | 删除Sign |
| `subscribeSign` | `String arg0` | `SmsQuerySignDto` | 订阅Sign |
| `provider` | `—` | `String` | 短信签名自动服务：返回所属提供方标识（SPI 路由用） |

#### SmsTemplateAutoService

`com.seeyon.cip.provider.api.sms.SmsTemplateAutoService` · 构件 `cip-capability-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addTemplate` | `SmsTemplateDto arg0` | `SmsTemplateDto` | 新增模板 |
| `queryTemplate` | `SmsTemplateQueryDto arg0` | `SmsQueryTemplateDto` | 查询模板 |
| `updateTemplate` | `SmsTemplateDto arg0` | `SmsTemplateDto` | 修改模板 |
| `deleteTemplate` | `String arg0` | `void` | 删除模板 |
| `subscribeTemplate` | `String arg0` | `SmsQueryTemplateDto` | 订阅模板 |
| `provider` | `—` | `String` | 短信模板自动服务：返回所属提供方标识（SPI 路由用） |

### `com.seeyon.cip.provider.api.test`

#### TestProviderService

`com.seeyon.cip.provider.api.test.TestProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `test` | `String arg0` | `String` | 测试（String） |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.translation`

#### TranslationProviderService

`com.seeyon.cip.provider.api.translation.TranslationProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `translate` | `String arg0` | `String` | 翻译（String） |
| `getLanguages` | `—` | `List<LanguageDto>` | 获取Languages |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

### `com.seeyon.cip.provider.api.trip`

#### BusinessTripProviderService

`com.seeyon.cip.provider.api.trip.BusinessTripProviderService` · 构件 `cip-capability-api` · extends `ProviderService, CipCallbackProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `departmentSync` | `TripDeptSyncRequestDto arg0` | `void` | 同步（TripDeptSyncRequestDto） |
| `isvUserSync` | `TripUserSyncRequestDto arg0` | `void` | 同步（TripUserSyncRequestDto） |
| `addressGetBook` | `TripAddressGetBookRequestDto arg0` | `String` | 获取Book |
| `addressGetOrder` | `TripAddressGetOrderRequestDto arg0` | `String` | 获取Order |
| `addressGetManager` | `TripAddressGetManagerRequestDto arg0` | `String` | 获取负责人 |
| `addressGetH5` | `TripAddressGetH5RequestDto arg0` | `String` | 获取H5 |
| `costCenterQuery` | `TripCostCenterQueryRequestDto arg0` | `TripCostCenterQueryResponseDto` | 查询（TripCostCenterQueryRequestDto） |
| `invoiceSearch` | `TripInvoiceQueryRequestDto arg0` | `TripInvoiceQueryResponseDto` | 搜索（TripInvoiceQueryRequestDto） |
| `applyAdd` | `TripApplyAddRequestDto arg0` | `TripApplyAddResponseDto` | 新增（TripApplyAddRequestDto） |
| `applyApprove` | `TripApplyApproveRequestDto arg0` | `void` | 审批（TripApplyApproveRequestDto） |
| `exceedApplySync` | `TripExceedApplySyncRequestDto arg0` | `void` | 同步（TripExceedApplySyncRequestDto） |
| `commonApplySync` | `TripCommonApplySyncRequestDto arg0` | `void` | 同步（TripCommonApplySyncRequestDto） |
| `isvCitySync` | `TripCitySyncRequestDto arg0` | `TripCitySyncResponseDto` | 同步（TripCitySyncRequestDto） |

### `com.seeyon.cip.provider.api.video`

#### VideoProviderService

`com.seeyon.cip.provider.api.video.VideoProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `createVideoMeeting` | `VideoMeetingCreateDto arg0` | `VideoMeetingOutDto` | 新建VideoMeeting |
| `createPersonalVideoMeeting` | `VideoMeetingPersonalCreateDto arg0` | `VideoMeetingOutDto` | 新建PersonalVideoMeeting |
| `updateVideoMeeting` | `VideoMeetingUpdateDto arg0` | `VideoMeetingOutDto` | 修改VideoMeeting |
| `cancelVideoMeeting` | `VideoMeetingOperateDto arg0` | `void` | 取消VideoMeeting |
| `finishVideoMeeting` | `VideoMeetingOperateDto arg0` | `void` | 完成VideoMeeting |
| `selectVmrMeetingRoom` | `PageInfo arg0` | `List<VideoMeetingRoomDto>` | 查询VmrMeetingRoom |
| `selectVmrMeetingRoomResource` | `PageInfo arg0` | `PageData<VideoMeetingRoomResourceResultDto>` | 查询资源VmrMeetingRoom |
| `selectMemberVmrMeetingRoom` | `PageInfo arg0` | `List<VideoMeetingRoomMemberDto>` | 查询成员VmrMeetingRoom |
| `deleteVmwareMeetingRoom` | `VideoMeetingRoomOperateDto arg0` | `void` | 删除VmwareMeetingRoom |
| `allotVmwareMeetingRoom` | `VideoMeetingRoomAllotDto arg0` | `void` | 视频提供方：分配会议室 |
| `updateVmwareMeetingRoom` | `VideoMeetingRoomUpdateDto arg0` | `void` | 修改VmwareMeetingRoom |
| `recycleVmwareMeetingRoom` | `VideoMeetingRoomOperateDto arg0` | `void` | 视频提供方：回收会议室 |
| `addUser` | `VideoMeetingUserDto arg0` | `VideoMeetingUserDto` | 新增用户 |
| `authentication` | `String arg0` | `VideoMeetingAuthOutDto` | 视频提供方：认证 |
| `getEndedMeetingDetail` | `VideoMeetingEndedSelectDto arg0` | `VideoMeetingEndedDetailDto` | 获取EndedMeetingDetail |
| `getMeetingRecord` | `VideoMeetingRecordSelectDto arg0` | `VideoMeetingRecordDto` | 获取MeetingRecord |
| `getMeetingDetail` | `VideoMeetingDetailDto arg0` | `VideoMeetingOutDto` | 获取MeetingDetail |

### `com.seeyon.cip.provider.api.voice`

#### VoiceProviderService

`com.seeyon.cip.provider.api.voice.VoiceProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createRealTime` | `RealtimeApiDto arg0` | `RealTimeApiResDto` | 新建RealTime |
| `createVoiceFile` | `QueryVoiceApiDto arg0` | `QueryVoiceApiResDto` | 新建文件Voice |
| `queryVoiceFileResult` | `QueryVoiceFileApiDto arg0` | `QueryVoiceFileApiResDto` | 查询文件VoiceResult |
| `createFileConvertWords` | `CreateWordsApiDto arg0` | `CreateWordsApiResDto` | 新建文件ConvertWords |
| `queryConvertWordsResult` | `QueryConvertResultApiDto arg0` | `QueryConvertResultApiResDto` | 查询ConvertWordsResult |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |
| `createIntelligentDigest` | `CreateIntelligentDigestApiDto arg0` | `CreateIntelligentDigestApiResDto` | 新建IntelligentDigest |
| `queryIntelligentDigestResult` | `QueryIntelligentDigestApiDto arg0` | `QueryIntelligentDigestApiResDto` | 查询IntelligentDigestResult |

### `com.seeyon.cip.provider.api.weather`

#### WeatherProviderService

`com.seeyon.cip.provider.api.weather.WeatherProviderService` · 构件 `cip-capability-api` · extends `ProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getLocation` | `—` | `LocationDto` | 获取Location |
| `getWeatherCity` | `String arg0` | `WeatherData` | 获取WeatherCity |
| `getWeatherBatch` | `—` | `List<WeatherData>` | 批量获取Weather |
| `getCapabilityEnum` | `—` | `CapabilityEnum` | 获取集成能力枚举 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 0 个领域服务，下表列**方法数最多的 0 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|

## biz 层：事件与监听

事件 0 个 · 监听器 0 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|

## web 层：Controller

共 0 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|

## 入参 DTO（字段级）

> 字段来自字节码 `fields`（含继承链，最多 3 层）；**字段名即 JSON 键名**（平台用 Jackson 默认命名，`shortName` 对应库列 `short_name`）。
> 包装类已揭开：`SingleRequest<T>` / `ListResponse<T>` 里看的是 `T` 的字段。
> 等级 `VERIFIED_STATIC_BYTECODE`。全量字段表：`docs/audit/artifacts/dto/DTO-cip-provider.md`

本模块 **330** 个入参/返回 DTO，**318** 个能取到字段。Top 12（按出现次数）：

| DTO | 出现 | 字段数 | 关键字段 |
|---|---:|---:|---|
| `CapabilityEnum` | 33 | 5 | `isHidden`, `code`, `description`, `nameByI18n`, `sort` |
| `CreditRequestDto` | 21 | 7 | `keyword`, `skip`, `appName`, `debugging`, `count`, `provider`, `validate` |
| `ThreePartySealIntegrationDto` | 5 | 29 | `storageKey`, `keyword`, `control`, `startPage`, `endPage`, `position`, `flag`, `page` |
| `CipProvideResultDto` | 4 | 4 | `data`, `code`, `message`, `validate` |
| `FileConvertDto` | 4 | 10 | `taskId`, `docUrl`, `fileName`, `userId`, `sync`, `routeKey`, `downloadId`, `FileExtMap` |
| `ScheduleInfoDto` | 4 | 7 | `scheduleId`, `map`, `appName`, `debugging`, `count`, `provider`, `validate` |
| `OrganizationResultDto` | 4 | 3 | `orgId`, `thirdOrgId`, `validate` |
| `SmsTemplateDto` | 4 | 13 | `templateName`, `templateContent`, `remark`, `templateTypeCode`, `templateType`, `templateCode`, `reason`, `providerTemplateContent` |
| `VideoMeetingOutDto` | 4 | 17 | `meetingId`, `meetingUUID`, `meetingSize`, `subject`, `meetingTimeZoneID`, `startTime`, `endTime`, `mediaTypes` |
| `BaseCommonContractData` | 3 | 2 | `token`, `accountId` |
| `SmsSignDto` | 3 | 9 | `tags`, `signName`, `remark`, `templateType`, `signStatus`, `reason`, `qualificationFile`, `commissionFile` |
| `InvoiceCheckOutApiDto` | 2 | 5 | `batchNO`, `itemDtoList`, `code`, `message`, `validate` |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **84** 张（来源构件：`cip-connector-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `cip_mobile_corp` | 移动插件企业表 | 4 |
| `cip_sync_result` | 中间表同步日志表 | 4 |
| `cip_sync_duty` | 组织同步职务中间表 | 3 |
| `cip_sync_level` | 组织同步职级中间表 | 3 |
| `cip_sync_member` | 组织同步人员中间表 | 3 |
| `cip_sync_post` | 组织同步岗位中间表 | 3 |
| `cip_sync_unit` | 组织同步组织中间表 | 3 |
| `org_job` | 职务 | 3 |
| `org_level` | 职级 | 3 |
| `cip_custom_app` | 集成应用信息表 | 2 |
| `cip_database_info` | 数据库配置信息表 | 2 |
| `cip_download_log` | 文件下载历史表 | 2 |
| `cip_linker_auth_info` | 连接器认证信息表 | 2 |
| `cip_linker_classify_info` | 连接器分类表 | 2 |
| `cip_linker_detail` | 连接器动作详情表 | 2 |
| `cip_linker_detail_classify` | 连接器动作分类表 | 2 |
| `cip_linker_enum` | 连接器枚举类 | 2 |
| `cip_linker_enum_item` | 连接器枚举项类 | 2 |
| `cip_linker_event_detail` | 连接器事件详情表 | 2 |
| `cip_linker_event_detail_poll` | 连接器事件轮询表 | 2 |
| `cip_linker_executor_log` | 连接器执行日志表 | 2 |
| `cip_linker_info` | 连接器信息表 | 2 |
| `cip_linker_metadata_info` | 连接器元数据记录表 | 2 |
| `cip_linker_mq_event_detail` | 连接器mq事件信息表 | 2 |
| `cip_linker_sign_info` | 连接器签名信息表 | 2 |
| `cip_linker_spi_ref` | 连接器spi引用依赖表 | 2 |
| `cip_mapping_config` | 映射配置 | 2 |
| `cip_p_capability_info` | 插件能力基本信息表 | 2 |
| `cip_p_data_check_conf` | 基础插件数据补偿配置 | 2 |
| `cip_p_ldap_info` | ldap信息 | 2 |
| `cip_p_operate_log` | 插件操作日志表 | 2 |
| `cip_p_org_running_config` | 组织结构同步运行态数据 | 2 |
| `cip_p_org_sync_config` | 组织同步插件能力的配置详情 | 2 |
| `cip_p_param_mapping` | 插件参数映射表 | 2 |
| `cip_p_plugin_info` | 插件基本信息表 | 2 |
| `cip_p_running_detail` | 插件运行态详情表 | 2 |
| `cip_p_sync_affair` | 事项已同步数据 | 2 |
| `cip_p_sync_his` | 插件同步历史数据表 | 2 |
| `cip_p_sync_org` | 组织模型已同步数据表 | 2 |
| `cip_p_timer_job` | 插件定时任务信息表 | 2 |
| `cip_p_todo_config` | 待办/消息配置详情表 | 2 |
| `cip_sync_duty_view` | 组织同步职务中间表_查询 | 2 |
| `cip_sync_level_view` | 组织同步职级中间表_查询 | 2 |
| `cip_sync_member_view` | 组织同步人员中间表_查询 | 2 |
| `cip_sync_post_view` | 组织同步岗位中间表_查询 | 2 |
| `cip_sync_unit_view` | 组织同步组织中间表_查询 | 2 |
| `cip_user_mapping_column` | 用户映射的列信息 | 2 |
| `cip_user_mapping_detail` | 用户映射具体配置信息表 | 2 |
| `cip_user_mapping_value` | 用户映射的值信息 | 2 |
| `cip_warning_log` | 集成预警信息表 | 2 |
| `cip_ability_dingtalk_link` | 钉钉消息链接表 | 1 |
| `cip_app_param` | 应用参数 | 1 |
| `cip_app_param_detail` | 应用参数明细 | 1 |
| `cip_applet_version` | 小程序版本管理表 | 1 |
| `cip_data_check_config` | 基础插件数据补偿配置 | 1 |
| `cip_dingtalk_link` | 钉钉消息链接表 | 1 |
| `cip_ldap_info` | ldap信息 | 1 |
| `cip_mobile_app` | 移动插件表 | 1 |
| `cip_mobile_applet` | 小程序版本管理表 | 1 |
| `cip_mobile_config` | 第三方平台配置信息 | 1 |
| `cip_mobile_log` | 日志记录表 | 1 |
| `cip_mobile_msg_mapping` | 移动插件消息映射表 | 1 |
| `cip_mobile_plugin` | 移动插件表 | 1 |
| `cip_mobile_swtich` | 移动插件开关配置 | 1 |
| `cip_mobile_swtich_config` | 移动插件开关配置 | 1 |
| `cip_mobile_sync_config` | 组织同步配置表（向外） | 1 |
| `cip_mobile_todo_mapping` | 移动插件待办映射表 | 1 |
| `cip_mp_menu` | 微信公众号菜单表 | 1 |
| `cip_ocip_access_log` | ocip访问日志 | 1 |
| `cip_org_mapping_detail` | 用户映射具体配置信息表 | 1 |
| `cip_org_running_config` | 组织结构同步运行态数据 | 1 |
| `cip_org_sync_config` | 组织同步插件能力的配置详情 | 1 |
| `cip_plugin_capability_info` | 插件能力基本信息表 | 1 |
| `cip_plugin_info` | 插件基本信息表 | 1 |
| `cip_plugin_org_sync_config` | 组织同步配置表（向外） | 1 |
| `cip_plugin_param_mapping` | 插件参数映射表 | 1 |
| `cip_plugin_timer_job` | 插件定时任务信息表 | 1 |
| `cip_push_affair_log` | 外推待办日志表 | 1 |
| `cip_third_menu` | 应用菜单管理 | 1 |
| `cip_third_platform_config` | 第三方平台配置信息 | 1 |
| `cip_third_template` | 三方模板表 | 1 |
| `cip_todo_config` | 待办/消息配置详情表 | 1 |
| `cip_user_sso_info` | 单点登录信息 | 1 |
| `ctp_user` | 用户 | 1 |

## 方法级落表（写接口）

> **口径：触及表的上界，不是「只写这张表」。** 证据链是「方法体引用的实体/DAO → 实体类 `@TableName` 字面量」，
> 方法若再做条件分支，实际只写其中一部分。判断影响面用它，判断唯一落点还得看 SQL。
> 等级 `VERIFIED_STATIC_BYTECODE`（引用与表名都来自字节码），**上界推断**部分标 `STATIC_INFERENCE`。

本模块 58 个写方法中，**3** 个解析出触及表：

| 接口#方法 | 触及表 | 依据（引用链） |
|---|---|---|
| `CipAccessLogDbService#deleteById` | `cip_ability_log_record` | `CipLogRecordDao=>CipLogRecord->cip_ability_log_record` |
| `CipAccessLogDbService#update` | `cip_ability_log_record` | `CipLogRecord->cip_ability_log_record; CipLogRecordDao=>CipLogRecord->cip_ability_log_record` |
| `LogService#saveLog` | `cip_ability_log_record` | `CipLogRecordDao=>CipLogRecord->cip_ability_log_record` |

## REST 路由

> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。
> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。

**拼法**（以 `organization` 为例，`:8080` 之类按环境）：

```
POST /service/{类级路径}/{方法级路径}
      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层
  例：POST /service/udc/runtime/deploy-normal
      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）
```

控制器 **33** 个、路由 **368** 条（来源：`cip-connector-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-cip-provider.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `LinkerController` | `cip-connector/connector-info` | 67 |
| `LinkerUserMappingController` | `cip-connector/connector/mapping` | 38 |
| `PluginCapabilityController` | `cip-connector/plug/capability` | 28 |
| `MobileApplicationController` | `cip-connector/mobile` | 18 |
| `OrgSyncDesignController` | `cip-connector/plug/org-sync-design` | 16 |
| `CipApplicationController` | `cip-connector/custom-app` | 14 |
| `MobileController` | `cip-connector/mobile` | 14 |
| `PluginDataCheckController` | `cip-connector/plug/data-check` | 12 |
| `CipBaseConfigController` | `cip-connector/base-config` | 12 |
| `AppRegisterController` | `cip-connector/connector/appreg` | 12 |
| `MobileAppletController` | `cip-connector/mobile` | 11 |
| `CipConnectorApiController` | `cip-connector/apitest` | 11 |
| `MiddleTableViewController` | `cip-connector/plug/midview` | 9 |
| `MobileOrgSyncController` | `cip-connector/mobile` | 8 |
| `MiddleTableController` | `cip-connector/plug/middletable` | 8 |
| `LinkerClassifyController` | `cip-connector/connector-classify` | 8 |
| `LinkerSsoController` | `cip-connector/connector/sso` | 8 |
| `LinkerEnumController` | `cip-connector/connector-enum` | 8 |
| `OrgSyncRunningController` | `cip-connector/plug/org-sync-running` | 7 |
| `CipWarningController` | `cip-connector/warning` | 6 |
| `TodoRedirectController` | `cip-connector/plug/redirect-url` | 6 |
| `PluginInfoController` | `cip-connector/plug/basic` | 6 |
| `ConnectorCallbackController` | `cip-connector/base/callback` | 6 |
| `AuthController` | `cip-connector/connector-auth` | 6 |
| `LinkerMetadataController` | `cip-connector/connector-metadata` | 6 |
| `CipMenuManageController` | `cip-connector/application/menu` | 5 |
| `CipTemplateController` | `cip-connector/third/template` | 5 |
| `MobileTestController` | `cip-connector/mobile` | 4 |
| `MobileCallbackController` | `cip-connector/mobile/auth` | 2 |
| `FileApiController` | `cip-connector/apitest/file` | 2 |
| `CallbackController` | `cip-connector/call-back` | 2 |
| `CipMigrationController` | `cip-manager/migration` | 2 |
| `MobileUserMappingController` | `cip-connector/mobile/usermapping` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `GetMapping` | `/service/cip-connector/apitest/callback/get-url` |
| `GetMapping` | `/service/cip-connector/apitest/ocip/ocipConfig` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/check` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/doc/async` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/doc/sync` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/user/sk` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/user/body` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/data/transfer` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/sk/delete` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/log/list` |
| `PostMapping` | `/service/cip-connector/apitest/org-sync/middle-table/clear/test` |
| `PostMapping` | `/service/cip-connector/apitest/file/upload` |
| `PostMapping` | `/service/cip-connector/apitest/file/get` |
| `PostMapping` | `/service/cip-connector/connector/appreg/add` |
| `PostMapping` | `/service/cip-connector/connector/appreg/modify` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 48 接口 / 330 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 0 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 0 事件 / 0 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 0 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（368 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| 落表（87 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |

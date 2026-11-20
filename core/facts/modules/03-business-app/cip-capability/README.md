# 集成能力（capability）

## 一句话

`com.seeyon.cip` 域的**可调用接口面**：7 个构件、1,448 个类、47 个 facade 接口 / 446 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `cip-capability-biz` | biz | 839 |
| `cip-capability-facade` | facade | 490 |
| `cip-capability-common` | common | 70 |
| `cip-manager-web` | web | 32 |
| `cip-capability-web` | web | 11 |
| `cip-manager-biz` | biz | 3 |
| `cip-manager-facade` | facade | 3 |
| **合计** | | **1,448** |

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

## facade 层：47 个接口 / 446 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.cip.capability.api.common.archives` | 1 | 4 |
| `com.seeyon.cip.capability.api.common.bankpay` | 1 | 11 |
| `com.seeyon.cip.capability.api.common.censor` | 1 | 2 |
| `com.seeyon.cip.capability.api.common.credit` | 1 | 25 |
| `com.seeyon.cip.capability.api.common.doc` | 3 | 41 |
| `com.seeyon.cip.capability.api.common.econtracts` | 4 | 21 |
| `com.seeyon.cip.capability.api.common.email` | 2 | 20 |
| `com.seeyon.cip.capability.api.common.faceid` | 1 | 4 |
| `com.seeyon.cip.capability.api.common.gis` | 1 | 1 |
| `com.seeyon.cip.capability.api.common.invoice` | 2 | 11 |
| `com.seeyon.cip.capability.api.common.location` | 1 | 7 |
| `com.seeyon.cip.capability.api.common.message` | 1 | 1 |
| `com.seeyon.cip.capability.api.common.missive` | 1 | 26 |
| `com.seeyon.cip.capability.api.common.mobileplugin` | 2 | 20 |
| `com.seeyon.cip.capability.api.common.ocr` | 1 | 20 |
| `com.seeyon.cip.capability.api.common.ofd` | 1 | 5 |
| `com.seeyon.cip.capability.api.common.pay` | 2 | 13 |
| `com.seeyon.cip.capability.api.common.physical` | 1 | 10 |
| `com.seeyon.cip.capability.api.common.resume` | 1 | 1 |
| `com.seeyon.cip.capability.api.common.schedule` | 1 | 4 |
| `com.seeyon.cip.capability.api.common.search` | 1 | 1 |
| `com.seeyon.cip.capability.api.common.signature` | 1 | 39 |
| `com.seeyon.cip.capability.api.common.sms` | 1 | 4 |
| `com.seeyon.cip.capability.api.common.translation` | 1 | 2 |
| `com.seeyon.cip.capability.api.common.trip` | 1 | 14 |
| `com.seeyon.cip.capability.api.common.video` | 1 | 20 |
| `com.seeyon.cip.capability.api.common.voice` | 1 | 7 |
| `com.seeyon.cip.capability.api.common.weather` | 1 | 2 |
| `com.seeyon.cip.capability.api.core.ai` | 1 | 3 |
| `com.seeyon.cip.capability.api.core.info` | 1 | 9 |
| `com.seeyon.cip.capability.api.core.log` | 1 | 3 |
| `com.seeyon.cip.capability.api.core.manage` | 1 | 53 |
| `com.seeyon.cip.capability.api.core.sms` | 4 | 34 |
| `com.seeyon.cip.capability.api.core.token` | 1 | 2 |
| `com.seeyon.cip.capability.appservice.api` | 1 | 6 |
| **合计** | **47** | **446** |

### `com.seeyon.cip.capability.api.common.archives`

#### ArchivesAppService

`com.seeyon.cip.capability.api.common.archives.ArchivesAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `titleAttribute` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 档案集成：取档案的标题字段值 |
| `queryArchiveSystemCategory` | `SingleRequest<Long> arg0` | `ListResponse<ArchiveSettingCategoryDto>` | 查询分类ArchiveSystem |
| `selectAttributesByTypeIds` | `SingleRequest<FieldMappingRequestDto> arg0` | `ListResponse<FieldMappingDto>` | 查询Attributes按类型 |
| `startArchiving` | `SingleRequest<ArchivingInfoWrapperDto> arg0` | `SingleResponse<ArchiveResultDto>` | 启动Archiving |

### `com.seeyon.cip.capability.api.common.bankpay`

#### BankpayAppService

`com.seeyon.cip.capability.api.common.bankpay.BankpayAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `balanceQuery` | `SingleRequest<BalanceQueryReqDto> arg0` | `SingleResponse<BalanceQueryRespDto>` | 查询BalanceQueryReq |
| `paymentTransfer` | `SingleRequest<PaymentTransferReqDto> arg0` | `SingleResponse<PaymentTransferRespDto>` | 转移PaymentTransferReq |
| `accountDetail` | `PageDtoRequest<AccountDetailReqDto> arg0` | `PageResponse<AccountDetailRespDto>` | 银企直连：查账户明细 |
| `accountSummary` | `PageDtoRequest<AccountDetailReqDto> arg0` | `PageResponse<AccountSummaryRespDto>` | 银企直连：查账户汇总（余额） |
| `accountInDetail` | `SingleRequest<AccountInDetailReqDto> arg0` | `SingleResponse<AccountInDetailRespDto>` | 银企直连：查账户入账明细 |
| `expensesFinance` | `SingleRequest<ExpenseReqDto> arg0` | `SingleResponse<ExpenseRespDto>` | 银企直连：查费用/财务凭证数据 |
| `cityCodeComparisonTableDownload` | `SingleRequest<CityCodeComparisonTableDownloadReqDto> arg0` | `ListResponse<CityCodeComparisonTableDownloadRespDto>` | 银企直连：下载城市编码对照表 |
| `currencyCodeComparisonTableDownload` | `SingleRequest<CurrencyCodeComparisonTableDownloadReqDto> arg0` | `ListResponse<CurrencyCodeComparisonTableDownloadRespDto>` | 银企直连：下载币种编码对照表 |
| `paymentBankInformation` | `SingleRequest<PaymentBankInformationReqDto> arg0` | `ListResponse<PaymentBankInformationRespDto>` | 银企直连：查付款银行信息 |
| `accountNameCheck` | `SingleRequest<AccountNameCheckReqDto> arg0` | `SingleResponse<AccountNameCheckRespDto>` | 检查账户名称 |
| `transactionStatusQuery` | `SingleRequest<TransactionStatusQueryReqDto> arg0` | `SingleResponse<TransactionStatusQueryRespDto>` | 查询TransactionStatusQueryReq |

### `com.seeyon.cip.capability.api.common.censor`

#### CensorAppService

`com.seeyon.cip.capability.api.common.censor.CensorAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `textCensor` | `SingleRequest<TextCensorReqDto> arg0` | `SingleResponse<TextCensorResDto>` | 内容审核：文本送审 |
| `censorChange` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 内容审核：审核结果变更回调 |

### `com.seeyon.cip.capability.api.common.credit`

#### EnterpriseCreditAppService

`com.seeyon.cip.capability.api.common.credit.EnterpriseCreditAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pageEnterpriseInfo` | `PageRequest arg0` | `PageResponse<EnterpriseBasicInfoResponse>` | 企业征信：分页查企业工商信息 |
| `getBasicBusinessInfo` | `SingleRequest<EnterpriseCreditRequestDto> arg0` | `SingleResponse<EnterpriseBasicBusinessInfoResponseDto>` | 获取业务Basic |
| `pageEnterpriseInfo` | `PageDtoRequest<EnterpriseCreditRequestDto> arg0` | `PageResponse<EnterpriseBasicInfoResponse>` | 企业征信：分页查企业工商信息 |
| `getBasicInfo` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseBasicInfoDto>` | 获取Basic |
| `getPartners` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterprisePartnersDto>` | 获取Partners |
| `getCourtNotice` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseCourtNoticeDto>` | 获取通知Court |
| `getCaseDetailList` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseCaseDetailDto>` | 列表获取流程实例Detail |
| `getAdminPunish` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseAdminPunishDto>` | 获取AdminPunish |
| `getEnvp` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseEnvpDto>` | 获取Envp |
| `getEnvpDetail` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseEnvpDetailDto>` | 获取EnvpDetail |
| `getBiddingList` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseBiddingDto>` | 列表获取Bidding |
| `getBiddingDetail` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseBiddingDetailDto>` | 获取BiddingDetail |
| `getAdministrativeLicenseList` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseAdministrativeLicenseDto>` | 列表获取AdministrativeLicense |
| `getEntCreditRating` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseEntCreditRatingDto>` | 获取EntCreditRating |
| `getTaxpayerList` | `SingleRequest<CreditRequestDto> arg0` | `ListResponse<EnterpriseTaxpayerDto>` | 列表获取Taxpayer |
| `getTrademark` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseTrademarkDto>` | 获取Trademark |
| `getTrademarkDetail` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseTrademarkDetailDto>` | 获取TrademarkDetail |
| `getPatentList` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterprisePatentDto>` | 列表获取Patent |
| `getPatentDetail` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterprisePatentDetailDto>` | 获取PatentDetail |
| `getCopyrightSoft` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseCopyrightSoftDto>` | 获取CopyrightSoft |
| `getCertificate` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseCertificateDto>` | 获取Certificate |
| `getProject` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseProjectDto>` | 获取Project |
| `getFinancing` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseFinancingDto>` | 获取Financing |
| `getShellEntInfoByName` | `SingleRequest<CreditRequestDto> arg0` | `SingleResponse<EnterpriseShellEntInfoDto>` | 获取ShellEnt按名称 |
| `getEntJusticeScore` | `SingleRequest<CreditRequestExtendDto> arg0` | `SingleResponse<EntJusticeScoreDto>` | 获取EntJusticeScore |

### `com.seeyon.cip.capability.api.common.doc`

#### DocCallBackAppService

`com.seeyon.cip.capability.api.common.doc.DocCallBackAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `fileInfo` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 文档回调：取文件信息 |
| `userInfo` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 文档回调：取用户信息 |
| `editFileOnline` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件在线 |
| `editFileSave` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件Save |
| `editFileVersion` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件版本 |
| `editFileRename` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件Rename |
| `editOnNotify` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑OnNotify |
| `editUserAuth` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑用户认证 |
| `editInfo` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件 |
| `editFileHistory` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件History |
| `editFileNotify` | `SingleRequest<DocFileInfoDto> arg0` | `SingleResponse<DocCallbackDto>` | 编辑文件Notify |
| `fileConvert` | `SingleRequest<Map<String, Object>> arg0` | `void` | 转换（SingleRequest） |

#### DocGeneralizeAppService

`com.seeyon.cip.capability.api.common.doc.DocGeneralizeAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAuthorityInfoProxy` | `SingleRequest<DocAuthorityInfoProxyRequestDto> arg0` | `SingleResponse<DocAuthorityInfoResponseDto>` | 获取AuthorityProxy |

#### DocOnlineAppService

`com.seeyon.cip.capability.api.common.doc.DocOnlineAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOfficeViewUrl` | `SingleRequest<DocViewDto> arg0` | `SingleResponse<DocViewUrlDto>` | 获取OfficeUrl |
| `getCompositeViewUrl` | `SingleRequest<CompositeViewDto> arg0` | `SingleResponse<CompositeViewResDto>` | 获取CompositeUrl |
| `getLatestPicViewUrl` | `SingleRequest<LatestPicViewDto> arg0` | `SingleResponse<LatestPicViewResDto>` | 获取LatestPicUrl |
| `getOfficeEditUrl` | `SingleRequest<DocEditDto> arg0` | `SingleResponse<DocEditUrlDto>` | 获取OfficeEditUrl |
| `cpsOfficeConvert` | `SingleRequest<DocFileConvertDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 转换文件 |
| `cpsOfficeBatchConvert` | `SingleRequest<DocFileBatchConvertDto> arg0` | `SingleResponse<DocFileConvertBatchStateDto>` | 在线文档：CPS 批量格式转换 |
| `cpsOfficeConvertPdfToSinglePng` | `SingleRequest<DocFileSingleConvertDto> arg0` | `SingleResponse<DocFileSingleConvertResDto>` | 转换PdfToSinglePng |
| `cpsOfficeConvertPdfToHtml` | `SingleRequest<DocFileSingleConvertDto> arg0` | `SingleResponse<DocFileSingleConvertResDto>` | 转换PdfToHtml |
| `cpsOfficeOperateClean` | `SingleRequest<DocFileOperateCleanDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 在线文档：清理文档缓存/痕迹 |
| `cpsOfficeOperateTextWatermark` | `SingleRequest<DocFileOperateTextWatermarkDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 在线文档：加文字水印 |
| `cpsOfficeOperateBatchTextWatermark` | `SingleRequest<DocFileOperateBatchTextWatermarkDto> arg0` | `SingleResponse<DocFileConvertBatchStateDto>` | 在线文档：批量加文字水印 |
| `cpsOfficeOperateImageWatermark` | `SingleRequest<DocFileOperateImageWatermarkDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 在线文档：加图片水印 |
| `getLatestDocFileInfoByStorageKey` | `SingleRequest<DocFileInfoRequestDto> arg0` | `SingleResponse<DocFileInfoResponseDto>` | 获取文件LatestDoc按存储键 |
| `batchGetLatestDocFileInfoByStorageKey` | `SingleRequest<DocFileInfoBatchRequestDto> arg0` | `SingleResponse<DocFileInfoBatchResponseDto>` | 获取文件LatestDoc按存储键 |
| `selectDocFileVersionPage` | `SingleRequest<DocFileVersionPageRequestDto> arg0` | `PageResponse<DocFileVersionPageResponseDto>` | 分页查询文件版本Doc |
| `getAuthorityInfo` | `SingleRequest<DocAuthorityInfoRequestDto> arg0` | `SingleResponse<DocAuthorityInfoResponseDto>` | 获取Authority |
| `cpsOfficeBookmark` | `SingleRequest<DocQueryBookmarkDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 在线文档：读写书签 |
| `cpsWrapHeader` | `SingleRequest<DocWrapHeaderDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 在线文档：抽取/包装文档头 |
| `setBookmarkPermissions` | `SingleRequest<DocSetBookmarkPermissionsDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 设置BookmarkPermissions |
| `encryptPdfProtection` | `SingleRequest<DocPdfEncryptRequestDto> arg0` | `SingleResponse<DocPdfEncryptResponseDto>` | 在线文档：PDF 加密保护 |
| `cpsMerge` | `SingleRequest<DocMergeDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 合并DocMerge |
| `cpsTaskQuery` | `SingleRequest<DocQueryTaskDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 查询任务 |
| `onNotify` | `SingleRequest<NotifyReqDto> arg0` | `SingleResponse<NotifyResDto>` | 通知NotifyReq |
| `getFileUrl` | `SingleRequest<DocFileUrlReqDto> arg0` | `SingleResponse<DocFileUrlResDto>` | 获取文件Url |
| `extractPictures` | `SingleRequest<DocExtractPicReqDto> arg0` | `SingleResponse<DocFileConvertStateDto>` | 在线文档：抽取文档内图片 |
| `userNotify` | `SingleRequest<DocUserNotifyReqDto> arg0` | `SingleResponse<DocUserNotifyResDto>` | 通知用户 |
| `checkContent` | `SingleRequest<DocCheckContentRequestDto> arg0` | `SingleResponse<DocCheckContentResponseDto>` | 检查内容 |
| `checkAndEncrypt` | `SingleRequest<DocEncryptFileRequestDto> arg0` | `SingleResponse<DocEncryptFileResponseDto>` | 检查AndEncrypt |

### `com.seeyon.cip.capability.api.common.econtracts`

#### CompanyAccountServiceAppService

`com.seeyon.cip.capability.api.common.econtracts.CompanyAccountServiceAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createOrUpdate` | `SingleRequest<CommonCompanyAccountDto> arg0` | `SingleResponse<Integer>` | 新建OrUpdate |
| `queryCompanyAccountInfo` | `SingleRequest<Long> arg0` | `SingleResponse<CommonCompanyAccountDto>` | 查询账户Company |

#### ContractsAppService

`com.seeyon.cip.capability.api.common.econtracts.ContractsAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `processPersonalCertificate` | `SingleRequest<PersonalCertificateRequestDto> arg0` | `SingleResponse<PersonalCertificateResponse>` | 处理PersonalCertificate |
| `processPersonCertificateInfo` | `SingleRequest<PersonalCertificateRequestDto> arg0` | `SingleResponse<PersonCertificateInfoResponse>` | 处理PersonCertificate |
| `processEnterpriseCertificate` | `SingleRequest<EnterpriseCertificateRequestDto> arg0` | `SingleResponse<CompanyCertificateResponse>` | 处理EnterpriseCertificate |
| `processBpmTemplateValidCheck` | `SingleRequest<BpmTemplateValidCheckRequestDto> arg0` | `SingleResponse<BpmTemplateValidCheckResponse>` | 处理模板BpmValidCheck |
| `processFileUpload` | `SingleRequest<FileUploadRequestDto> arg0` | `SingleResponse<ContractsUploadResponse>` | 处理文件Upload |
| `processSignTaskCreate` | `SingleRequest<SignTaskCreateRequestDto> arg0` | `SingleResponse<SignTaskUrlResponse>` | 处理任务SignCreate |
| `processSignTaskUrl` | `SingleRequest<SignTaskRequestDto> arg0` | `SingleResponse<SignTaskUrlResponse>` | 处理任务SignUrl |
| `processSignTaskDetails` | `SingleRequest<SignTaskRequestDto> arg0` | `SingleResponse<SignTaskDetailResponse>` | 处理任务SignDetails |
| `processSignTaskExternal` | `SingleRequest<SignTaskRequestDto> arg0` | `SingleResponse<SignTaskExternalStatusResponse>` | 处理任务外部人员Sign |
| `processSignTaskFile` | `SingleRequest<SignTaskRequestDto> arg0` | `SingleResponse<SignTaskFileResponse>` | 处理任务文件Sign |
| `processSignTaskCancel` | `SingleRequest<SignTaskRequestDto> arg0` | `SingleResponse<SignTaskCancelResponse>` | 处理任务SignCancel |

#### ContractsCallBackAppService

`com.seeyon.cip.capability.api.common.econtracts.ContractsCallBackAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `callBack` | `SingleRequest<BaseContractsRequestDto> arg0` | `SingleResponse<String>` | 调用Back |

#### SealAppService

`com.seeyon.cip.capability.api.common.econtracts.SealAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `uploadSeal` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 上传Seal |
| `listSeal` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 列出Seal |
| `getSealDetails` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 获取SealDetails |
| `authSeal` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 电子印章：印章使用授权 |
| `cancelAuthSeal` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 取消认证Seal |
| `deleteAuthSeal` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 删除认证Seal |
| `syncCompanySeal` | `SingleRequest<SealRequestDto> arg0` | `SingleResponse<BaseContractsResponse>` | 同步CompanySeal |

### `com.seeyon.cip.capability.api.common.email`

#### EmailAppService

`com.seeyon.cip.capability.api.common.email.EmailAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendNormalEmail` | `SingleRequest<EmailDetailsDto> arg0` | `SingleResponse<EmailSendResultDto>` | 发送NormalEmail |
| `sendNormalEmailByAccount` | `SingleRequest<EmailAppointAccountDto> arg0` | `SingleResponse<EmailSendResultDto>` | 发送NormalEmail按账户 |
| `sendPersonalEmail` | `SingleRequest<EmailDetailsDto> arg0` | `SingleResponse<EmailSendResultDto>` | 发送PersonalEmail |
| `testSendPersonalEmail` | `SingleRequest<CipEmailUserAccountTestDto> arg0` | `SingleResponse<EmailSendResultDto>` | 测试SendPersonalEmail |
| `insertOrUpdate` | `SingleRequest<CipEmailUserAccountDto> arg0` | `SingleResponse<Integer>` | 插入OrUpdate |
| `findCipEmailUserAccount` | `SingleRequest<Void> arg0` | `SingleResponse<CipEmailUserAccountDto>` | 查找用户账户CipEmail |
| `sendTemplateEmail` | `SingleRequest<EmailTemplateSendDto> arg0` | `SingleResponse<EmailSendResultDto>` | 发送模板Email |
| `selectPageEmailTemplate` | `PageRequest arg0` | `PageResponse<CipEmailTemplateDto>` | 分页查询模板Email |
| `captchaEmail` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 邮件：发送验证码邮件 |

#### EmailPrivateAppService

`com.seeyon.cip.capability.api.common.email.EmailPrivateAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `insertOrUpdateEmailConfig` | `SingleRequest<CipEmailConfigDto> arg0` | `SingleResponse<Void>` | 插入配置OrUpdateEmail |
| `deleteEmailConfig` | `—` | `SingleResponse<Void>` | 删除配置Email |
| `getCompanySystemEmail` | `—` | `SingleResponse<CipEmailConfigDto>` | 获取CompanySystemEmail |
| `addEmailTemplate` | `SingleRequest<CipEmailTemplateDto> arg0` | `SingleResponse<Void>` | 新增模板Email |
| `modifyEmailTemplate` | `SingleRequest<CipEmailTemplateDto> arg0` | `SingleResponse<Void>` | 修改模板Email |
| `selectEmailTemplate` | `SingleRequest<Long> arg0` | `SingleResponse<CipEmailTemplateDto>` | 查询模板Email |
| `deleteEmailTemplate` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 删除模板Email |
| `deleteEmailTemplates` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除EmailTemplates |
| `testSendEmail` | `SingleRequest<EmailConfigTestDto> arg0` | `SingleResponse<EmailSendResultDto>` | 测试SendEmail |
| `insertOrUpdateEmailLimitConfig` | `SingleRequest<CipEmailLimitConfigDto> arg0` | `SingleResponse<Void>` | 插入配置OrUpdateEmailLimit |
| `getEmailLimit` | `—` | `SingleResponse<CipEmailLimitConfigDto>` | 获取EmailLimit |

### `com.seeyon.cip.capability.api.common.faceid`

#### FaceIdAppService

`com.seeyon.cip.capability.api.common.faceid.FaceIdAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addFace` | `SingleRequest<FaceAddReqDto> arg0` | `SingleResponse<FaceAddResDto>` | 新增Face |
| `faceCheck` | `SingleRequest<FaceIdentifyReqDto> arg0` | `SingleResponse<FaceIdentifyResDto>` | 检查FaceIdentifyReq |
| `updateFace` | `SingleRequest<FaceUpdateReqDto> arg0` | `SingleResponse<FaceUpdateResDto>` | 修改Face |
| `getAccessToken` | `SingleRequest<Void> arg0` | `SingleResponse<String>` | 获取可见令牌 |

### `com.seeyon.cip.capability.api.common.gis`

#### GisAppService

`com.seeyon.cip.capability.api.common.gis.GisAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getToken` | `SingleRequest<GisTokenRequestDto> arg0` | `SingleResponse<GisTokenDto>` | 获取令牌 |

### `com.seeyon.cip.capability.api.common.invoice`

#### InvoiceAppService

`com.seeyon.cip.capability.api.common.invoice.InvoiceAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOcrInvoiceData` | `SingleRequest<InvoiceOcrDto> arg0` | `SingleResponse<InvoiceOutDto>` | 获取数据OcrInvoice |
| `getOcrAsyncResult` | `SingleRequest<InvoiceOcrAsyncDto> arg0` | `SingleResponse<InvoiceOutDto>` | 获取OcrAsyncResult |
| `getOcrInvoiceSingle` | `SingleRequest<String> arg0` | `SingleResponse<InvoiceOutItemDto>` | 获取OcrInvoiceSingle |
| `verificationInvoice` | `SingleRequest<InvoiceCheckDto> arg0` | `SingleResponse<String>` | 发票：发票查验（真伪） |
| `batchGetInvoice` | `SingleRequest<String> arg0` | `SingleResponse<InvoiceCheckOutDto>` | 获取Invoice |
| `scanCodeIdentifyInvoice` | `SingleRequest<String> arg0` | `SingleResponse<InvoiceCheckOutItemDto>` | 扫描编码IdentifyInvoice |
| `invoiceOcrAndCheck` | `SingleRequest<String> arg0` | `SingleResponse<InvoiceCheckOutItemDto>` | 发票：OCR 识别 + 查验一体 |
| `queryOcrPage` | `SingleRequest<InvoiceOcrPageReqDto> arg0` | `PageResponse<InvoiceOcrPageResDto>` | 分页查询Ocr |
| `queryCheckPage` | `SingleRequest<InvoiceCheckPageReqDto> arg0` | `PageResponse<InvoiceCheckPageResDto>` | 分页查询Check |

#### InvoiceImageAppService

`com.seeyon.cip.capability.api.common.invoice.InvoiceImageAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createImageTask` | `SingleRequest<InvoiceImageReqDto> arg0` | `SingleResponse<InvoiceImageResDto>` | 新建任务Image |
| `uploadImageFile` | `SingleRequest<InvoiceImageUploadReqDto> arg0` | `SingleResponse<InvoiceImageUploadResDto>` | 上传文件Image |

### `com.seeyon.cip.capability.api.common.location`

#### LocationAppService

`com.seeyon.cip.capability.api.common.location.LocationAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getLocation` | `SingleRequest<Void> arg0` | `SingleResponse<String>` | 获取Location |
| `getDistance` | `SingleRequest<DistanceDto> arg0` | `SingleResponse<String>` | 获取Distance |
| `geocoding` | `SingleRequest<GeocoderRequestDto> arg0` | `SingleResponse<GeocoderResultDto>` | 地图：地址转经纬度 |
| `regionSearch` | `SingleRequest<RegionDto> arg0` | `ListResponse<DistrictsDto>` | 搜索Region |
| `getJsApiInfo` | `SingleRequest<Void> arg0` | `SingleResponse<JsApiDto>` | 获取APIJs |
| `keywordSearch` | `SingleRequest<KeywordSearchDto> arg0` | `ListResponse<SearchResultDto>` | 搜索KeywordSearch |
| `aroundSearch` | `SingleRequest<AroundSearchDto> arg0` | `ListResponse<SearchResultDto>` | 搜索AroundSearch |

### `com.seeyon.cip.capability.api.common.message`

#### OfflineMessageAppService

`com.seeyon.cip.capability.api.common.message.OfflineMessageAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pushMessage` | `SingleRequest<OfflineMessageDto> arg0` | `SingleResponse<Void>` | 推送消息 |

### `com.seeyon.cip.capability.api.common.missive`

#### IntelligentMissiveAppService

`com.seeyon.cip.capability.api.common.missive.IntelligentMissiveAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createExtractingTask` | `SingleRequest<ExtractingTaskReqDto> arg0` | `SingleResponse<ExtractingTaskResDto>` | 新建任务Extracting |
| `queryExtractingDetail` | `SingleRequest<ExtractingDetailReqDto> arg0` | `SingleResponse<ExtractingDetailResDto>` | 查询ExtractingDetail |
| `queryDiffRule` | `SingleRequest<DiffRuleReqDto> arg0` | `SingleResponse<DiffRuleResDto>` | 查询规则Diff |
| `createDocDiffTask` | `SingleRequest<DiffTaskReqDto> arg0` | `SingleResponse<DiffTaskResDto>` | 新建任务DocDiff |
| `queryDocDiffPage` | `SingleRequest<DiffPageReqDto> arg0` | `SingleResponse<DiffPageResDto>` | 分页查询DocDiff |
| `queryDocDiffDetail` | `SingleRequest<DiffDetailReqDto> arg0` | `SingleResponse<DiffDetailResDto>` | 查询DocDiffDetail |
| `queryDocDiffView` | `SingleRequest<DiffDetailReqDto> arg0` | `SingleResponse<DiffDetailViewResDto>` | 查询DocDiff |
| `queryCardRule` | `SingleRequest<CardRuleReqDto> arg0` | `SingleResponse<CardRuleResDto>` | 查询规则Card |
| `createReviewTask` | `SingleRequest<ReviewTaskReqDto> arg0` | `SingleResponse<ReviewTaskResDto>` | 新建任务Review |
| `queryReviewDetail` | `SingleRequest<ReviewDetailReqDto> arg0` | `SingleResponse<ReviewDetailResDto>` | 查询ReviewDetail |
| `createTableTask` | `SingleRequest<TableTaskReqDto> arg0` | `SingleResponse<TableTaskResDto>` | 新建表任务 |
| `queryTableDetail` | `SingleRequest<TableDetailReqDto> arg0` | `SingleResponse<TableDetailResDto>` | 查询表Detail |
| `createSettingByTemplate` | `SingleRequest<SettingTaskReqDto> arg0` | `SingleResponse<SettingTaskResDto>` | 新建设置按模板 |
| `createOnlineProofread` | `SingleRequest<ProofreadTaskReqDto> arg0` | `SingleResponse<ProofreadTaskResDto>` | 新建在线Proofread |
| `queryProofreadDetail` | `SingleRequest<ProofreadTaskDetailReqDto> arg0` | `SingleResponse<ProofreadTaskResDto>` | 查询ProofreadDetail |
| `checkSensitiveWord` | `SingleRequest<SensitiveWordReqDto> arg0` | `SingleResponse<SensitiveWordResDto>` | 检查敏感Word |
| `uploadTempFile` | `SingleRequest<UploadTempFileReqDto> arg0` | `SingleResponse<UploadTempFileResDto>` | 上传文件Temp |
| `createRecommend` | `SingleRequest<RecommendReqDto> arg0` | `PageResponse<RecommendResDto>` | 新建Recommend |
| `createWrite` | `SingleRequest<IntelligentWriteReqDto> arg0` | `SingleResponse<IntelligentWriteResDto>` | 新建Write |
| `queryWrite` | `SingleRequest<IntelligentWriteQueryReqDto> arg0` | `SingleResponse<IntelligentWriteQueryResDto>` | 查询Write |
| `pushOfficial` | `SingleRequest<IntelligentPushOfficialReqDto> arg0` | `SingleResponse<IntelligentPushOfficialResDto>` | 推送Official |
| `assistReading` | `SingleRequest<AssistReadingReqDto> arg0` | `SingleResponse<AssistReadingResDto>` | 智能公文：辅助阅读（摘要/要点） |
| `queryResultByTaskId` | `SingleRequest<QueryResultReqDto> arg0` | `SingleResponse<QueryResultResDto>` | 查询Result按任务 |
| `readingDetail` | `SingleRequest<ReadingDetailReqDto> arg0` | `SingleResponse<ReadingDetailResDto>` | 智能公文：阅读详情 |
| `retrieval` | `SingleRequest<RetrievalReqDto> arg0` | `PageResponse<RetrievalResDto>` | 智能公文：语义检索 |
| `queryRelated` | `SingleRequest<RelatedReqDto> arg0` | `SingleResponse<RelatedResDto>` | 查询Related |

### `com.seeyon.cip.capability.api.common.mobileplugin`

#### MobilePluginAppletAppService

`com.seeyon.cip.capability.api.common.mobileplugin.MobilePluginAppletAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `receiveTicket` | `SingleRequest<MobilePluginAppletReceiveTicketDto> arg0` | `SingleResponse<String>` | 接收Ticket |
| `bindAuth` | `SingleRequest<MobilePluginAppletOpenQueryDto> arg0` | `SingleResponse<MobilePluginAppletOpenQueryAuthResultDto>` | 绑定认证 |
| `authUrl` | `SingleRequest<MobilePluginAppletOpenPreAuthDto> arg0` | `SingleResponse<String>` | 移动小程序：取授权跳转 URL |
| `templateList` | `SingleRequest<String> arg0` | `ListResponse<MobilePluginAppletCodeTemplateDto>` | 列出编码模板 |
| `uploadCode` | `SingleRequest<MobilePluginAppletOpenCommitDto> arg0` | `SingleResponse<MobilePluginAppletOpenResultDto>` | 上传编码 |
| `privacySetting` | `SingleRequest<MobilePluginAppletOpenQueryDto> arg0` | `SingleResponse<MobilePluginAppletOpenResultDto>` | 移动小程序：隐私授权设置 |
| `submitAudit` | `SingleRequest<MobilePluginAppletOpenQueryDto> arg0` | `SingleResponse<MobilePluginAppletOpenAuditResultDto>` | 提交Audit |
| `getAuditStatus` | `SingleRequest<MobilePluginMobilePluginAppletOpenAuditQueryDto> arg0` | `SingleResponse<MobilePluginAppletOpenAuditStatusDto>` | 获取AuditStatus |
| `undoCodeAudit` | `SingleRequest<MobilePluginAppletOpenCommonDto> arg0` | `SingleResponse<MobilePluginAppletOpenResultDto>` | 审计MobilePluginAppletOpenCommon |
| `releaseAudited` | `SingleRequest<MobilePluginAppletOpenCommonDto> arg0` | `SingleResponse<MobilePluginAppletOpenResultDto>` | 释放Audited |
| `queryBindAuth` | `SingleRequest<MobilePluginAppletOpenQueryDto> arg0` | `SingleResponse<String>` | 查询认证Bind |

#### MobilePluginConfigAppService

`com.seeyon.cip.capability.api.common.mobileplugin.MobilePluginConfigAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOneByConditions` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<MobilePluginPlatformConfigDto>` | 查询One按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<MobilePluginPlatformConfigDto>` | 查询配置按 id |
| `create` | `SingleRequest<MobilePluginPlatformConfigDto> arg0` | `SingleResponse<Long>` | 新建配置 |
| `update` | `SingleRequest<MobilePluginPlatformConfigDto> arg0` | `SingleResponse<Integer>` | 修改配置 |
| `updateStatus` | `SingleRequest<MobilePluginPlatformConfigDto> arg0` | `SingleResponse<Integer>` | 修改Status |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `getWorkWxAccessMode` | `SingleRequest<Void> arg0` | `SingleResponse<AccessModeEnum>` | 获取可见WorkWxMode |
| `getPlatformTypeList` | `SingleRequest<Void> arg0` | `ListResponse<MobilePluginPlatformTypeDto>` | 列表获取类型Platform |
| `selectOneByConditionsIgnoreTenant` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<MobilePluginPlatformConfigDto>` | 查询One按条件租户 |

### `com.seeyon.cip.capability.api.common.ocr`

#### OcrAppService

`com.seeyon.cip.capability.api.common.ocr.OcrAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getIdCardFrontData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<IdCardFrontResponse>` | 获取数据CardFront |
| `getIdCardBackData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<IdCardBackResponse>` | 获取数据CardBack |
| `getBankCardData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<BankCardResponse>` | 获取数据BankCard |
| `getBusinessCardData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<BusinessCardResponse>` | 获取业务数据Card |
| `getBusinessLicenseData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<BusinessLicenseResponse>` | 获取业务数据License |
| `getTaxInvoiceData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<TaxInvoiceResponse>` | 获取数据TaxInvoice |
| `getTaxRollInvoiceData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<TaxInvoiceResponse>` | 获取数据TaxRollInvoice |
| `getTrainTicketData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<TrainTicketResponse>` | 获取数据TrainTicket |
| `getTaxiReceiptData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<TaxiReceiptResponse>` | 获取数据TaxiReceipt |
| `getAirTicketData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<AirTicketResponse>` | 获取数据AirTicket |
| `getTollInvoiceData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<TollInvoiceResponse>` | 获取数据TollInvoice |
| `getBusTicketData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<BusTicketResponse>` | 获取数据BusTicket |
| `getQuotaInvoiceData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<QuotaInvoiceResponse>` | 获取数据QuotaInvoice |
| `getWaybillData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<WayBillResponse>` | 获取数据Waybill |
| `getGeneralInVoiceData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<GeneralInVoiceResponse>` | 获取数据GeneralInVoice |
| `getCustomData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<CustomOcrResponse>` | 获取数据Custom |
| `verificationInvoice` | `SingleRequest<InvoiceVerificationRequestDto> arg0` | `SingleResponse<InvoiceVerificationResponse>` | OCR：发票识别并查验 |
| `getCommonParentData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<CipBaseResponse>` | 获取上级数据Common |
| `getCommonData` | `SingleRequest<OcrRequestDto> arg0` | `SingleResponse<OcrCommonResponse>` | 获取数据Common |
| `extractContent` | `SingleRequest<ExtractContentReqDto> arg0` | `SingleResponse<ExtractContentResDto>` | OCR：通用文字抽取 |

### `com.seeyon.cip.capability.api.common.ofd`

#### OfdAppService

`com.seeyon.cip.capability.api.common.ofd.OfdAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOfdViewUrl` | `SingleRequest<OfdFileRequestDto> arg0` | `SingleResponse<OfdFileResponseDto>` | 获取OfdUrl |
| `downFile` | `SingleRequest<OfdDownReqDto> arg0` | `SingleResponse<OfdDownResDto>` | SPI 扩展点：文件（框架回调） |
| `getSealInfo` | `SingleRequest<OfdSealReqDto> arg0` | `SingleResponse<OfdSealResDto>` | 获取Seal |
| `getSealList` | `SingleRequest<OfdSealItemReqDto> arg0` | `ListResponse<OfdSealItemResDto>` | 列表获取Seal |
| `getOfdMetaData` | `SingleRequest<OfdMetaDataReqDto> arg0` | `ListResponse<OfdMetaDataResDto>` | 获取数据OfdMeta |

### `com.seeyon.cip.capability.api.common.pay`

#### MerchantAppService

`com.seeyon.cip.capability.api.common.pay.MerchantAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createMerchant` | `SingleRequest<MerchantDto> arg0` | `SingleResponse<Long>` | 新建Merchant |
| `updateMerchant` | `SingleRequest<MerchantDto> arg0` | `SingleResponse<Integer>` | 修改Merchant |
| `deleteMerchant` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Merchant |
| `detailMerchant` | `SingleRequest<Long> arg0` | `SingleResponse<MerchantDto>` | 支付：查商户详情 |
| `selectPageMerchantByConditions` | `PageRequest arg0` | `PageResponse<MerchantDto>` | 分页查询Merchant按条件 |

#### PayAppService

`com.seeyon.cip.capability.api.common.pay.PayAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `h5Pay` | `SingleRequest<H5PayOrderParamsDto> arg0` | `SingleResponse<H5PayOrderResultDto>` | 支付：发起 H5 支付 |
| `queryTransactionByOutTradeNo` | `SingleRequest<TransactionParamsDto> arg0` | `SingleResponse<TransactionResultDto>` | 查询Transaction按OutTradeNo |
| `closeTransaction` | `SingleRequest<TransactionParamsDto> arg0` | `SingleResponse<Void>` | 关闭Transaction |
| `refund` | `SingleRequest<RefundParamsDto> arg0` | `SingleResponse<RefundResultDto>` | 支付：发起退款 |
| `queryRefund` | `SingleRequest<QueryRefundParamsDto> arg0` | `SingleResponse<QueryRefundResultDto>` | 查询Refund |
| `downloadTradeBill` | `SingleRequest<BillDownloadParamsDto> arg0` | `SingleResponse<BillDownloadResultDto>` | SPI 扩展点：downloadTradeBill（框架回调） |
| `downloadFundFlowBill` | `SingleRequest<BillDownloadParamsDto> arg0` | `SingleResponse<BillDownloadResultDto>` | SPI 扩展点：downloadFundFlowBill（框架回调） |
| `getCert` | `SingleRequest<CertificateReqDto> arg0` | `ListResponse<CertificateDto>` | 获取Cert |

### `com.seeyon.cip.capability.api.common.physical`

#### PhysicalSealAppService

`com.seeyon.cip.capability.api.common.physical.PhysicalSealAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncDept` | `SingleRequest<PhysicalSealDeptDto> arg0` | `SingleResponse<Void>` | 同步部门 |
| `syncMember` | `SingleRequest<PhysicalSealMemberDto> arg0` | `SingleResponse<Void>` | 同步成员 |
| `applyAuthorize` | `SingleRequest<PhysicalSealApplyDto> arg0` | `SingleResponse<String>` | 实体印章：申请用印授权 |
| `queryApplyRecord` | `SingleRequest<PhysicalSealApplyIdDto> arg0` | `SingleResponse<String>` | 查询ApplyRecord |
| `cancelApply` | `SingleRequest<PhysicalSealApplyIdDto> arg0` | `SingleResponse<Void>` | 取消Apply |
| `querySeals` | `SingleRequest<PhysicalSealEmptyDto> arg0` | `SingleResponse<PhysicalSealsDto>` | 查询Seals |
| `getImageByApplyId` | `SingleRequest<PhysicalSealApplyIdDto> arg0` | `SingleResponse<PhysicalSealImagesDto>` | 获取Image按ApplyId |
| `getImage` | `SingleRequest<PhysicalSealImageDto> arg0` | `SingleResponse<List<PhysicalSealFileDto>>` | 获取Image |
| `reWrite` | `SingleRequest<PhysicalSealReWriteDto> arg0` | `SingleResponse<PhysicalSealReWriteDto>` | 写入PhysicalSealReWrite |
| `eventCallback` | `SingleRequest<PhysicalSealReWriteDto> arg0` | `<Res> Res` | 实体印章：用印事件回调 |

### `com.seeyon.cip.capability.api.common.resume`

#### ResumeAppService

`com.seeyon.cip.capability.api.common.resume.ResumeAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `analysisResume` | `SingleRequest<ResumeRequestDto> arg0` | `SingleResponse<ResumeResultDto>` | 恢复Resume |

### `com.seeyon.cip.capability.api.common.schedule`

#### ScheduleAppService

`com.seeyon.cip.capability.api.common.schedule.ScheduleAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addSchedule` | `SingleRequest<AddScheduleDto> arg0` | `SingleResponse<ScheduleInfoDto>` | 新增调度 |
| `updateSchedule` | `SingleRequest<UpdateScheduleDto> arg0` | `SingleResponse<ScheduleInfoDto>` | 修改调度 |
| `cancelSchedule` | `SingleRequest<ScheduleInfoDto> arg0` | `SingleResponse<Void>` | 取消调度 |
| `detailSchedule` | `SingleRequest<ScheduleInfoDto> arg0` | `SingleResponse<ScheduleDetailDto>` | 日程集成：查日程详情 |

### `com.seeyon.cip.capability.api.common.search`

#### SearchAppService

`com.seeyon.cip.capability.api.common.search.SearchAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `querySearchUrl` | `SingleRequest<QuerySearchReqDto> arg0` | `SingleResponse<QuerySearchResDto>` | 查询SearchUrl |

### `com.seeyon.cip.capability.api.common.signature`

#### SignatureAppService

`com.seeyon.cip.capability.api.common.signature.SignatureAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getSignatureViewUrl` | `SingleRequest<SignatureFileRequestDto> arg0` | `SingleResponse<SignatureFileResponseDto>` | 获取SignatureUrl |
| `downFile` | `SingleRequest<SignatureDownReqDto> arg0` | `SingleResponse<SignatureDownResDto>` | SPI 扩展点：文件（框架回调） |
| `getSealInfo` | `SingleRequest<SignatureSealReqDto> arg0` | `SingleResponse<SignatureSealResDto>` | 获取Seal |
| `uploadFile` | `SingleRequest<UploadFileDto> arg0` | `SingleResponse<FileInfoDto>` | 上传文件 |
| `initiateSign` | `SingleRequest<InitiateSignDto> arg0` | `SingleResponse<InitiateSignResultDto>` | 签署InitiateSign |
| `initiateSignFree` | `SingleRequest<InitiateSignFreeDto> arg0` | `SingleResponse<InitiateSignResultDto>` | 签署Free |
| `createOrg` | `SingleRequest<OrganizationDto> arg0` | `SingleResponse<OrganizationResultDto>` | 新建组织 |
| `updateOrg` | `SingleRequest<OrganizationUpdateDto> arg0` | `SingleResponse<OrganizationResultDto>` | 修改组织 |
| `detailOrg` | `SingleRequest<OrganizationQueryDto> arg0` | `SingleResponse<OrganizationDetailDto>` | 电子签：查组织详情 |
| `batchCreateUser` | `SingleRequest<BatchCreateUserDto> arg0` | `SingleResponse<UserResultDto>` | 新建用户 |
| `selectPageByConditions` | `PageDtoRequest<TemplatePageDto> arg0` | `PageResponse<TemplateInfoDto>` | 分页查询模板页面按条件 |
| `getTemplateContents` | `SingleRequest<TemplateBaseDto> arg0` | `SingleResponse<TemplateControlResultDto>` | 获取模板Contents |
| `generatePdfFile` | `SingleRequest<GeneratePdfDto> arg0` | `SingleResponse<GeneratePdfResultDto>` | 生成文件Pdf |
| `signToolsConfig` | `SingleRequest<SignAreaConfigDto> arg0` | `SingleResponse<SignAreaResultDto>` | 签署配置Tools |
| `signToolsConfigDetail` | `SingleRequest<SignAreaSelectDto> arg0` | `SingleResponse<SignAreaDetailDto>` | 签署配置ToolsDetail |
| `verifySignature` | `SingleRequest<VerifySignatureDto> arg0` | `SingleResponse<VerifySignatureResultDto>` | 校验Signature |
| `userUpdate` | `SingleRequest<UserUpdateDto> arg0` | `SingleResponse<SuccessData>` | 修改用户 |
| `userDetail` | `SingleRequest<UserQueryDto> arg0` | `SingleResponse<UserUpdateDto>` | 电子签：查用户详情 |
| `sealList` | `PageDtoRequest<SealQueryDto> arg0` | `PageResponse<SealDataDto>` | 列出SealQuery |
| `downloadFile` | `SingleRequest<FileInfoDto> arg0` | `SingleResponse<FileDownloadDto>` | SPI 扩展点：文件（框架回调） |
| `invalidFlow` | `SingleRequest<InvalidFlowReqDto> arg0` | `SingleResponse<InvalidFlowResDto>` | 电子签：作废签署流程 |
| `createOuterOrg` | `SingleRequest<OuterOrganizationDto> arg0` | `SingleResponse<OrganizationResultDto>` | 新建组织Outer |
| `updateOuterOrg` | `SingleRequest<OuterOrganizationUpdateDto> arg0` | `SingleResponse<OrganizationResultDto>` | 修改组织Outer |
| `detailOuterOrg` | `SingleRequest<OrganizationQueryDto> arg0` | `SingleResponse<OuterOrganizationDetailDto>` | 电子签：查外部组织详情 |
| `batchCreateOuterUser` | `SingleRequest<OuterBatchCreateUserDto> arg0` | `SingleResponse<UserResultDto>` | 新建用户Outer |
| `outerUserUpdate` | `SingleRequest<OuterUserUpdateDto> arg0` | `SingleResponse<SuccessData>` | 修改用户 |
| `outerUserDetail` | `SingleRequest<UserQueryDto> arg0` | `SingleResponse<OuterUserUpdateDto>` | 电子签：查外部用户详情 |
| `deleteInnerUsers` | `SingleRequest<DeleteInnerUsersReqDto> arg0` | `SingleResponse<DeleteInnerUsersResDto>` | 删除InnerUsers |
| `querySsoUrl` | `SingleRequest<QuerySsoReqDto> arg0` | `SingleResponse<QuerySsoResDto>` | 查询SsoUrl |
| `sealSigners` | `PageDtoRequest<SealSignerQueryDto> arg0` | `PageResponse<SealSignerDataDto>` | 电子签：取印章可签署人 |
| `stamp` | `SingleRequest<ThreePartySealIntegrationDto> arg0` | `SingleResponse<String>` | 电子签：执行盖章 |
| `withfileupload` | `SingleRequest<ThreePartySealIntegrationDto> arg0` | `SingleResponse<ContractResponseDto>` | 电子签：带文件上传的签署 |
| `invalid` | `SingleRequest<ThreePartySealIntegrationDto> arg0` | `SingleResponse<AgainContractResponse>` | 电子签：作废 |
| `recall` | `SingleRequest<ThreePartySealIntegrationDto> arg0` | `SingleResponse` | 电子签：撤回 |
| `sealGetList` | `SingleRequest<ThreePartySealIntegrationDto> arg0` | `SingleResponse<SealListResultDto>` | 列表获取ThreePartySealIntegration |
| `preSign` | `SingleRequest<PreSignDto> arg0` | `SingleResponse<String>` | 签署PreSign |
| `initPreSign` | `SingleRequest<InitPreSignDto> arg0` | `SingleResponse<String>` | 初始化PreSign |
| `verifySeal` | `SingleRequest<VerifySealDto> arg0` | `SingleResponse<String>` | 校验Seal |
| `finish` | `SingleRequest<ContractLockRequestDto> arg0` | `SingleResponse` | 完成ContractLock |

### `com.seeyon.cip.capability.api.common.sms`

#### ShortMessageAppService

`com.seeyon.cip.capability.api.common.sms.ShortMessageAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendShortMessage` | `SingleRequest<SmsSendDto> arg0` | `SingleResponse<Void>` | 发送消息Short |
| `sendSycShortMessage` | `SingleRequest<SmsSendDto> arg0` | `SingleResponse<SmsResponseDto>` | 发送消息SycShort |
| `sendShortMessageAsync` | `SingleRequest<List<SmsSendDto>> arg0` | `SingleResponse<Void>` | 发送消息ShortAsync |
| `inspectSms` | `SingleRequest<SmsInspectionDto> arg0` | `SingleResponse<SmsResponseDto>` | 短信：查询发送状态 |

### `com.seeyon.cip.capability.api.common.translation`

#### TranslationAppService

`com.seeyon.cip.capability.api.common.translation.TranslationAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `translate` | `SingleRequest<TranslationDto> arg0` | `SingleResponse<String>` | 翻译Translation |
| `getLanguages` | `SingleRequest<Void> arg0` | `ListResponse<LanguageDto>` | 获取Languages |

### `com.seeyon.cip.capability.api.common.trip`

#### BusinessTripAppService

`com.seeyon.cip.capability.api.common.trip.BusinessTripAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `departmentSync` | `SingleRequest<TripDeptSyncRequestDto> arg0` | `SingleResponse<Void>` | 同步部门 |
| `isvUserSync` | `SingleRequest<TripUserSyncRequestDto> arg0` | `SingleResponse<Void>` | 同步用户 |
| `isvCitySync` | `SingleRequest<TripCitySyncRequestDto> arg0` | `SingleResponse<TripCitySyncResponseDto>` | 同步TripCitySync |
| `addressGetBook` | `SingleRequest<TripAddressGetBookRequestDto> arg0` | `SingleResponse<String>` | 获取Book |
| `addressGetOrder` | `SingleRequest<TripAddressGetOrderRequestDto> arg0` | `SingleResponse<String>` | 获取Order |
| `addressGetManager` | `SingleRequest<TripAddressGetManagerRequestDto> arg0` | `SingleResponse<String>` | 获取负责人 |
| `addressGetH5` | `SingleRequest<TripAddressGetH5RequestDto> arg0` | `SingleResponse<String>` | 获取H5 |
| `costCenterQuery` | `SingleRequest<TripCostCenterQueryRequestDto> arg0` | `SingleResponse<TripCostCenterQueryResponseDto>` | 查询TripCostCenterQuery |
| `invoiceSearch` | `SingleRequest<TripInvoiceQueryRequestDto> arg0` | `SingleResponse<TripInvoiceQueryResponseDto>` | 搜索TripInvoiceQuery |
| `applyAdd` | `SingleRequest<TripApplyAddRequestDto> arg0` | `SingleResponse<TripApplyAddResponseDto>` | 新增TripApplyAdd |
| `applyApprove` | `SingleRequest<TripApplyApproveRequestDto> arg0` | `SingleResponse<TripApplyAddResponseDto>` | 审批TripApplyApprove |
| `exceedApplySync` | `SingleRequest<TripExceedApplySyncRequestDto> arg0` | `SingleResponse<TripApplyAddResponseDto>` | 同步TripExceedApplySync |
| `commonApplySync` | `SingleRequest<TripCommonApplySyncRequestDto> arg0` | `SingleResponse<TripApplyAddResponseDto>` | 同步TripCommonApplySync |
| `eventCallback` | `SingleRequest<EventMsgDto> arg0` | `<Res> Res` | 差旅：事件回调（审批结果回传） |

### `com.seeyon.cip.capability.api.common.video`

#### VideoMeetingAppService

`com.seeyon.cip.capability.api.common.video.VideoMeetingAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createVideoMeeting` | `SingleRequest<VideoMeetingCreateDto> arg0` | `SingleResponse<VideoMeetingOutDto>` | 新建VideoMeeting |
| `createPersonalVideoMeeting` | `SingleRequest<VideoMeetingPersonalCreateDto> arg0` | `SingleResponse<VideoMeetingOutDto>` | 新建PersonalVideoMeeting |
| `updateVideoMeeting` | `SingleRequest<VideoMeetingUpdateDto> arg0` | `SingleResponse<VideoMeetingOutDto>` | 修改VideoMeeting |
| `cancelVideoMeeting` | `SingleRequest<VideoMeetingOperateDto> arg0` | `SingleResponse<Void>` | 取消VideoMeeting |
| `finishVideoMeeting` | `SingleRequest<VideoMeetingOperateDto> arg0` | `SingleResponse<Void>` | 完成VideoMeeting |
| `getMeetingDetail` | `SingleRequest<VideoMeetingDetailDto> arg0` | `SingleResponse<VideoMeetingOutDto>` | 获取MeetingDetail |
| `auth` | `SingleRequest<String> arg0` | `SingleResponse<VideoMeetingAuthOutDto>` | 视频会议：认证 |
| `selectVideoMeetingRoom` | `SingleRequest<VideoMeetingRoomSelectDto> arg0` | `ListResponse<VideoMeetingRoomDto>` | 查询VideoMeetingRoom |
| `selectMemberMeetingRoom` | `SingleRequest<VideoMeetingRoomSelectDto> arg0` | `ListResponse<VideoMeetingRoomMemberDto>` | 查询成员MeetingRoom |
| `updateVideoMeetingRoom` | `SingleRequest<VideoMeetingRoomUpdateDto> arg0` | `SingleResponse<Void>` | 修改VideoMeetingRoom |
| `deleteVideoMeetingRoom` | `SingleRequest<VideoMeetingRoomOperateDto> arg0` | `SingleResponse<Void>` | 删除VideoMeetingRoom |
| `allotVmwareMeetingRoom` | `SingleRequest<VideoMeetingRoomAllotDto> arg0` | `SingleResponse<Void>` | 视频会议：分配会议室（VMware） |
| `recycleVmwareMeetingRoom` | `SingleRequest<VideoMeetingRoomOperateDto> arg0` | `SingleResponse<Void>` | 视频会议：回收会议室（VMware） |
| `addMeetingUser` | `SingleRequest<VideoMeetingUserDto> arg0` | `SingleResponse<VideoMeetingUserDto>` | 新增用户Meeting |
| `getEndedMeetingDetail` | `SingleRequest<VideoMeetingEndedSelectDto> arg0` | `SingleResponse<VideoMeetingEndedDetailDto>` | 获取EndedMeetingDetail |
| `getMeetingRecord` | `SingleRequest<VideoMeetingRecordSelectDto> arg0` | `SingleResponse<VideoMeetingRecordDto>` | 获取MeetingRecord |
| `addMeetingRoomResource` | `SingleRequest<VideoMeetingRoomResourceDto> arg0` | `SingleResponse<Void>` | 新增资源MeetingRoom |
| `updateMeetingRoomResource` | `SingleRequest<VideoMeetingRoomResourceDto> arg0` | `SingleResponse<Void>` | 修改资源MeetingRoom |
| `refreshMeetingRoomResource` | `SingleRequest<Void> arg0` | `SingleResponse<Void>` | 刷新资源MeetingRoom |
| `eventCallback` | `SingleRequest<T> arg0` | `<T, Res> Res` | 视频会议：事件回调 |

### `com.seeyon.cip.capability.api.common.voice`

#### VoiceAppService

`com.seeyon.cip.capability.api.common.voice.VoiceAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createRealTime` | `SingleRequest<RealtimeDto> arg0` | `SingleResponse<RealTimeResDto>` | 新建RealTime |
| `createVoiceFile` | `SingleRequest<CreateVoiceFileDto> arg0` | `SingleResponse<CreateVoiceFileResDto>` | 新建文件Voice |
| `queryVoiceFileResult` | `SingleRequest<QueryVoiceFileDto> arg0` | `SingleResponse<QueryVoiceFileResDto>` | 查询文件VoiceResult |
| `createFileConvertWords` | `SingleRequest<CreateWordsDto> arg0` | `SingleResponse<CreateWordsResDto>` | 新建文件ConvertWords |
| `queryConvertWordsResult` | `SingleRequest<QueryConvertResultDto> arg0` | `SingleResponse<QueryConvertResultResDto>` | 查询ConvertWordsResult |
| `createIntelligentDigest` | `SingleRequest<CreateIntelligentDigestDto> arg0` | `SingleResponse<CreateIntelligentDigestResDto>` | 新建IntelligentDigest |
| `queryIntelligentDigestResult` | `SingleRequest<QueryIntelligentDigestDto> arg0` | `SingleResponse<QueryIntelligentDigestResDto>` | 查询IntelligentDigestResult |

### `com.seeyon.cip.capability.api.common.weather`

#### WeatherAppService

`com.seeyon.cip.capability.api.common.weather.WeatherAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getLocation` | `SingleRequest<Void> arg0` | `SingleResponse<LocationDto>` | 获取Location |
| `getWeather` | `SingleRequest<String> arg0` | `SingleResponse<WeatherDto>` | 获取Weather |

### `com.seeyon.cip.capability.api.core.ai`

#### AiAppService

`com.seeyon.cip.capability.api.core.ai.AiAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createThirdApp` | `SingleRequest<AiAppInfoDto> arg0` | `SingleResponse<AiThirdAppInfoDto>` | 新建第三方应用 |
| `thirdAppIncrease` | `SingleRequest<AiAppInfoDto> arg0` | `SingleResponse<AiThirdAppInfoDto>` | AI 能力：从第三方增量拉取 |
| `queryUsageAmount` | `SingleRequest<AiAppUsageQueryDto> arg0` | `SingleResponse<AiAppUsageInfoDto>` | 查询UsageAmount |

### `com.seeyon.cip.capability.api.core.info`

#### CapabilityEnumAppService

`com.seeyon.cip.capability.api.core.info.CapabilityEnumAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectList` | `ListRequest arg0` | `ListResponse<CapabilityEnumDto>` | 列表查询集成能力枚举 |
| `selectItemList` | `ListRequest arg0` | `ListResponse<CapabilityEnumItemDto>` | 列表查询Item |
| `create` | `SingleRequest<CapabilityEnumDto> arg0` | `SingleResponse<Long>` | 新建集成能力枚举 |
| `createItem` | `SingleRequest<CapabilityEnumItemDto> arg0` | `SingleResponse<Long>` | 新建Item |
| `delete` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除（SingleRequest） |
| `deleteItem` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Item |
| `update` | `SingleRequest<CapabilityEnumDto> arg0` | `SingleResponse<Integer>` | 修改集成能力枚举 |
| `updateItem` | `SingleRequest<CapabilityEnumItemDto> arg0` | `SingleResponse<Integer>` | 修改Item |
| `deleteItemByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除Item按 ids |

### `com.seeyon.cip.capability.api.core.log`

#### CapabilityAccessLogDbAppService

`com.seeyon.cip.capability.api.core.log.CapabilityAccessLogDbAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<String> arg0` | `SingleResponse<CipAccessOpenLogDto>` | 查询可见日志按 id |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CipAccessOpenLogDto>` | 分页查询可见日志按条件 |
| `countByConditions` | `SingleRequest<CapabilityStatisticalRequestDto> arg0` | `ListResponse<CapabilityStatisticalResultsDto>` | 统计集成能力按条件 |

### `com.seeyon.cip.capability.api.core.manage`

#### CapabilityManageAppService

`com.seeyon.cip.capability.api.core.manage.CapabilityManageAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<SelectProviderDto>` | 分页查询SelectProvider按条件 |
| `operationEnable` | `SingleRequest<SelectProvicerEnableDto> arg0` | `SingleResponse<Boolean>` | 启用SelectProvicerEnable |
| `updateDefaultProvider` | `SingleRequest<SelectProvicerEnableDto> arg0` | `SingleResponse<Boolean>` | 修改DefaultProvider |
| `selectProvidersByEnum` | `SingleRequest<CapabilityEnum> arg0` | `ListResponse<ClassifyProviderDto>` | 查询Providers按枚举 |
| `selectEnableProvidersByEnum` | `SingleRequest<CapabilityEnum> arg0` | `ListResponse<ClassifyProviderDto>` | 查询EnableProviders按枚举 |
| `selectProvidersListByEnum` | `SingleRequest<CapabilityEnum> arg0` | `ListResponse<ClassifyProviderCloudDto>` | 列表查询Providers按枚举 |
| `selectOptionalProvider` | `SingleRequest<Long> arg0` | `SingleResponse<SelectProviderDto>` | 查询OptionalProvider |
| `editProviderParams` | `SingleRequest<Long> arg0` | `ListResponse<ProviderParameterDto>` | 编辑ProviderParams |
| `createParamBatch` | `SingleRequest<ProviderParameterRequestDto> arg0` | `SingleResponse<Integer>` | 批量新建Param |
| `deleteParam` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Param |
| `refreshProvide` | `—` | `SingleResponse<Void>` | 刷新Provide |
| `selectActiveXFunctionByEnum` | `SingleRequest<CapabilityEnum> arg0` | `ListResponse<OcrActiveXInfoResponse>` | 查询ActiveXFunction按枚举 |
| `getLinkProperties` | `—` | `SingleResponse<CloudConnectPropertiesDto>` | 指定字段获取Link |
| `getCloudProperties` | `SingleRequest<Void> arg0` | `SingleResponse<CloudConnectPropertiesDto>` | 指定字段获取Cloud |
| `saveLinkProperties` | `SingleRequest<CloudConnectPropertiesDto> arg0` | `SingleResponse<Integer>` | 指定字段保存Link |
| `sendOpenApiRequest` | `SingleRequest<OpenApiSendDto> arg0` | `SingleResponse<ApiSingleResponse>` | 发送APIOpenRequest |
| `sendOpenApiRequestPage` | `SingleRequest<OpenApiSendDto> arg0` | `SingleResponse<ApiPageResponse>` | 分页发送APIOpenRequest |
| `getCloudConnect` | `SingleRequest<Void> arg0` | `SingleResponse<CloudConnectInfoDto>` | 获取CloudConnect |
| `getCurrentCapabilityChannelInfo` | `SingleRequest<ProviderChannelRequestDto> arg0` | `SingleResponse<ProviderChannelResponseDto>` | 获取当前集成能力通道 |
| `selectProviderParameter` | `SingleRequest<BaseInfoParameterDto> arg0` | `ListResponse<ProviderParameterDto>` | 查询参数Provider |
| `queryEnableByEnum` | `SingleRequest<CapabilityEnum> arg0` | `SingleResponse<ProviderEnableDto>` | 查询Enable按枚举 |
| `batchQueryEnableByEnum` | `SingleRequest<BatchQueryEnableReqDto> arg0` | `SingleResponse<BatchQueryEnableResDto>` | 查询Enable按枚举 |
| `queryEnable` | `SingleRequest<CapabilityNameEnumDto> arg0` | `SingleResponse<ProviderEnableDto>` | 查询Enable |
| `checkFeatureByEnum` | `SingleRequest<CapabilityEnum> arg0` | `SingleResponse<Void>` | 检查Feature按枚举 |
| `selectFeatureByEnum` | `SingleRequest<CapabilityEnum> arg0` | `ListResponse<ServiceFeatureDto>` | 查询Feature按枚举 |
| `selectCountByEnum` | `SingleRequest<CountQueryDto> arg0` | `ListResponse<CountResultDto>` | 查询Count按枚举 |
| `selectOpenapiCount` | `SingleRequest<OpenapiCountQueryDto> arg0` | `ListResponse<CountResultDto>` | 查询OpenapiCount |
| `selectCloudCount` | `SingleRequest<OpenapiCapabilityQueryDto> arg0` | `SingleResponse<CapabilityCycleCountResultDto>` | 查询CloudCount |
| `selectLocalCloudCount` | `SingleRequest<OpenapiCapabilityQueryDto> arg0` | `SingleResponse<CapabilityCycleCountResultDto>` | 查询LocalCloudCount |
| `setCapabilityCycleCount` | `SingleRequest<CapabilityCycleCountDto> arg0` | `SingleResponse<Void>` | 设置集成能力CycleCount |
| `setAllCapabilityCycleCount` | `SingleRequest<AllCapabilityCycleCountDto> arg0` | `SingleResponse<Void>` | 全部设置集成能力CycleCount |
| `rechargeCapabilityCycleCount` | `SingleRequest<AllCapabilityCycleCountDto> arg0` | `SingleResponse<Void>` | 能力管理：充值能力的周期调用次数 |
| `selectCallbackConfig` | `SingleRequest<EventCallbackConfigQueryDto> arg0` | `SingleResponse<EventCallbackConfigResultDto>` | 查询配置Callback |
| `refreshEventToken` | `SingleRequest<EventCallbackConfigQueryDto> arg0` | `SingleResponse<String>` | 刷新令牌Event |
| `modifyEventToken` | `SingleRequest<EventCallbackConfigQueryDto> arg0` | `SingleResponse<Void>` | 修改令牌Event |
| `authConfigEdit` | `SingleRequest<AuthConfigDto> arg0` | `SingleResponse<Void>` | 编辑认证配置 |
| `authConfigQuery` | `SingleRequest<CountQueryDto> arg0` | `SingleResponse<AuthConfigDto>` | 查询CountQuery |
| `queryUseCount` | `SingleRequest<UseCountQueryDto> arg0` | `ListResponse<OpeningCapabilityDto>` | 查询UseCount |
| `operationEnableChannel` | `SingleRequest<OperateChannelEnableDto> arg0` | `SingleResponse<Void>` | 启用通道 |
| `queryThirdAppInfo` | `SingleRequest<OpenAppQueryDto> arg0` | `SingleResponse<ThirdAppInfoDto>` | 查询第三方应用 |
| `queryParams` | `SingleRequest<QueryParameterReqDto> arg0` | `ListResponse<QueryParameterResDto>` | 查询Params |
| `queryRegisterAppInfo` | `SingleRequest<QueryRegisterAppInfoReqDto> arg0` | `SingleResponse<QueryRegisterAppInfoResDto>` | 查询应用Register |
| `queryFeature` | `SingleRequest<QueryFeatureDto> arg0` | `SingleResponse<QueryFeatureResDto>` | 查询Feature |
| `appEnable` | `SingleRequest<CipAppEnableDto> arg0` | `SingleResponse<Long>` | 启用应用 |
| `selectAppPageByConditions` | `PageRequest arg0` | `PageResponse<CipAppQueryDto>` | 分页查询应用按条件 |
| `createApp` | `SingleRequest<CipAppCreateDto> arg0` | `SingleResponse<Long>` | 新建应用 |
| `updateApp` | `SingleRequest<CipAppUpdateDto> arg0` | `SingleResponse<Integer>` | 修改应用 |
| `deleteApp` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除应用 |
| `queryFeatureWithChannelByAbilityEnum` | `SingleRequest<QueryFeatureWithChannelDto> arg0` | `SingleResponse<QueryFeatureWithChannelResDto>` | 查询通道FeatureWith按枚举 |
| `createAppConfig` | `SingleRequest<CipAppFeatureProviderCreateInDto> arg0` | `SingleResponse<Integer>` | 新建应用配置 |
| `updateAppConfig` | `SingleRequest<CipAppFeatureProviderCreateInDto> arg0` | `SingleResponse<Integer>` | 修改应用配置 |
| `getAppConfig` | `SingleRequest<Long> arg0` | `SingleResponse<List<CipAppFeatureProviderDetailDto>>` | 获取应用配置 |
| `selectAppFeatureMappingDetails` | `SingleRequest<Long> arg0` | `ListResponse<CipAppFeatureMappingDto>` | 查询应用映射FeatureDetails |

### `com.seeyon.cip.capability.api.core.sms`

#### ExcelSmsImportAndExportAppService

`com.seeyon.cip.capability.api.core.sms.ExcelSmsImportAndExportAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `importExcel` | `SingleRequest<ExcelSmsImportDto> arg0` | `ListResponse<ExcelImportResponseDto>` | 导入Excel |
| `exportExcel` | `SingleRequest<ExcelSheetEnum> arg0` | `SingleResponse<String>` | 导出Excel |
| `exportExcelTemplate` | `SingleRequest<ExcelSheetEnum> arg0` | `SingleResponse<String>` | 导出模板Excel |

#### ShortMessageProviderTemplateAppService

`com.seeyon.cip.capability.api.core.sms.ShortMessageProviderTemplateAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createShortMessageTemplateContent` | `SingleRequest<ShortMessageProviderTemplateDto> arg0` | `SingleResponse<Long>` | 新建消息模板内容Short |
| `updateTemplateContent` | `SingleRequest<ShortMessageProviderTemplateDto> arg0` | `SingleResponse<Integer>` | 修改模板内容 |
| `selectTemplateContentById` | `SingleRequest<Long> arg0` | `SingleResponse<ShortMessageProviderTemplateDto>` | 查询模板内容按 id |
| `deleteTemplateContent` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除模板内容 |
| `selectTemplateContentByConditions` | `PageRequest arg0` | `ListResponse<ShortMessageProviderTemplateDto>` | 查询模板内容按条件 |

#### ShortMessageSignAppService

`com.seeyon.cip.capability.api.core.sms.ShortMessageSignAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createShortMessageSign` | `SingleRequest<ShortMessageSignDto> arg0` | `SingleResponse<Long>` | 新建消息ShortSign |
| `createSmsSign` | `SingleRequest<SmsSignCloudDto> arg0` | `SingleResponse<Long>` | 新建短信Sign |
| `updateTemplateSign` | `SingleRequest<ShortMessageSignDto> arg0` | `SingleResponse<Integer>` | 修改模板Sign |
| `updateSmsSign` | `SingleRequest<SmsSignCloudDto> arg0` | `SingleResponse<Integer>` | 修改短信Sign |
| `updateShortMessageSign` | `SingleRequest<ShortMessageSignDto> arg0` | `SingleResponse<Integer>` | 修改消息ShortSign |
| `checkRepeatSignName` | `SingleRequest<RepeatSignRequestDto> arg0` | `SingleResponse<Boolean>` | 检查名称RepeatSign |
| `selectRecentTimeSign` | `SingleRequest<Void> arg0` | `SingleResponse<ShortMessageSignDto>` | 查询RecentTimeSign |
| `selectValidSign` | `SingleRequest<SmsSearchDto> arg0` | `ListResponse<ShortMessageSignDto>` | 查询ValidSign |
| `deleteShortMessageSign` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除消息ShortSign |
| `selectPageSignByConditions` | `SingleRequest<SmsSearchDto> arg0` | `PageResponse<ShortMessageSignDto>` | 分页查询Sign按条件 |
| `exportSignByConditions` | `PageRequest arg0` | `PageResponse<ShortMessageSignDto>` | 导出Sign按条件 |
| `selectSignById` | `SingleRequest<Long> arg0` | `SingleResponse<ShortMessageSignDto>` | 查询Sign按 id |

#### ShortMessageTemplateAppService

`com.seeyon.cip.capability.api.core.sms.ShortMessageTemplateAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createShortMessageTemplate` | `SingleRequest<ShortMessageTemplateDto> arg0` | `SingleResponse<ShortMessageProviderTemplateDto>` | 新建消息模板Short |
| `createSMSTemplate` | `SingleRequest<ShortMessageTemplateDto> arg0` | `SingleResponse<ShortMessageProviderTemplateDto>` | 新建模板SMS |
| `updateTemplate` | `SingleRequest<ShortMessageTemplateDto> arg0` | `SingleResponse<Integer>` | 修改模板 |
| `setTemplateSign` | `SingleRequest<SmsSetSignDto> arg0` | `SingleResponse<Integer>` | 设置模板Sign |
| `selectTemplateById` | `SingleRequest<Long> arg0` | `SingleResponse<ShortMessageTemplateDto>` | 查询模板按 id |
| `selectTemplateByCode` | `SingleRequest<SmsTemplateQueryDto> arg0` | `SingleResponse<ShortMessageTemplateDto>` | 查询模板按编码 |
| `selectPageStoreLibrary` | `PageRequest arg0` | `PageResponse<ShortMessageStorehouseDto>` | 分页查询StoreLibrary |
| `deleteTemplateById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除模板按 id |
| `deleteTemplateByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除模板按 ids |
| `updateShortMessageTemplate` | `SingleRequest<ShortMessageTemplateDto> arg0` | `SingleResponse<Integer>` | 修改消息模板Short |
| `selectPageByConditions` | `SingleRequest<SmsSearchDto> arg0` | `PageResponse<ShortMessageTemplateDto>` | 分页查询短信按条件 |
| `selectTemplateTypeListByConditions` | `SingleRequest<SmsSearchDto> arg0` | `ListResponse<CapabilityEnumItemDto>` | 列表查询模板类型按条件 |
| `checkTemplateCode` | `SingleRequest<RepeatTemplateCodeRequestDto> arg0` | `SingleResponse<Boolean>` | 检查模板编码 |
| `getLanguage` | `—` | `ListResponse<LanguageDto>` | 获取Language |

### `com.seeyon.cip.capability.api.core.token`

#### TokenAppService

`com.seeyon.cip.capability.api.core.token.TokenAppService` · 构件 `cip-capability-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectTokenExpireTime` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 查询令牌ExpireTime |
| `saveTokenExpireTime` | `SingleRequest<String> arg0` | `SingleResponse<Boolean>` | 保存令牌ExpireTime |

### `com.seeyon.cip.capability.appservice.api`

#### OpenCapabilityAppService

`com.seeyon.cip.capability.appservice.api.OpenCapabilityAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createApp` | `SingleRequest<AppCreateDto> arg0` | `SingleResponse<AppBasicInfoDto>` | 新建应用 |
| `updateAppCharges` | `SingleRequest<CapabilityRechargeDto> arg0` | `SingleResponse<Void>` | 修改应用Charges |
| `queryUseCount` | `SingleRequest<CapabilityCountQueryDto> arg0` | `ListResponse<OpeningCapabilityDto>` | 查询UseCount |
| `createTenantApp` | `SingleRequest<TenantAppCreateDto> arg0` | `SingleResponse<AppBasicInfoDto>` | 新建应用 |
| `getTicket` | `SingleRequest<CreateUserDto> arg0` | `SingleResponse<TicketDto>` | 获取Ticket |
| `getAppUrl` | `SingleRequest<AppUrlRequestDto> arg0` | `SingleResponse<AppUrlResponseDto>` | 获取应用Url |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 81 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `DocOnlineService` | 95 | 在线 · 获取×31 / 设置×5 / 检查×4 |
| `ProviderManageService` | 49 | 管理 · 获取×15 / 查询×12 / 设置×4 |
| `IntelligentMissiveService` | 47 | IntelligentMissive · 查询×16 / 新建×8 / 获取×4 |
| `SignatureService` | 46 | Signature · 获取×8 / 签署×5 / 新建×4 |
| `ShortMessageTemplateService` | 40 | 消息模板 · 查询×13 / 获取×6 / 新建×5 |
| `ShortMessageSignService` | 33 | 消息 · 查询×9 / 获取×7 / 修改×5 |
| `CreditService` | 25 | Credit · 获取×25 |
| `ProviderSelectorService` | 25 | ProviderSelector · 查询×13 / 新建×2 / 获取×2 |
| `EmailService` | 24 | Email · 发送×5 / 获取×4 / 删除×2 |
| `InvoiceService` | 22 | Invoice · 获取×9 / 查询×3 / 新建×3 |
| `DocCallBackService` | 20 | DocCallBack · 获取×8 / 编辑×3 / 修改×2 |
| `ProviderParameterService` | 20 | 参数 · 获取×6 / 查询×4 / 新建×3 |
| `MobilePluginAppletCapabilityService` | 19 | 集成能力 · 获取×4 / 上传×2 / 提交×2 |
| `ShortMessageProviderTemplateService` | 19 | 消息模板 · 查询×9 / 修改×3 / 新建×2 |
| `VideoMeetingManagerService` | 16 | 负责人 · 获取×5 / 发送×4 / 新建×2 |
| `VideoMeetingRoomService` | 15 | VideoMeetingRoom · 获取×3 / 查询×2 / 修改×2 |
| `MobilePluginWxAppletComponentConfigService` | 14 | 组件配置 · 获取×4 / 查询×2 / 提交×2 |
| `PhysicalSealService` | 14 | PhysicalSeal · 发送×4 / 获取×3 / 同步×2 |
| `CipAppFeatureProviderService` | 13 | 应用 · 获取×4 / 查询×3 / 设置×2 |
| `BankpayService` | 12 | Bankpay · 获取×1 / 查询×1 / 转移×1 |
| `OpenApiPropertiesService` | 12 | API属性 · 获取×6 / 发送×2 / 查询×1 |
| `CheckFeatureService` | 11 | CheckFeature · 检查×8 / 修改×1 / 获取×1 |
| `OcrService` | 11 | Ocr · 获取×4 / 检查×3 / 上传×1 |
| `ExcelSmsImportService` | 11 | 短信 · 获取×5 / 导入×4 / 检查×1 |
| `CipEmailTemplateService` | 10 | 模板 · 删除×2 / 查询×2 / 获取×2 |
| `CipAppService` | 10 | 应用 · 查询×2 / 删除×2 / 启用×1 |
| `AiService` | 9 | Ai · 查询×4 / 设置×2 / 新建×1 |
| `ArchivesService` | 9 | Archives · 获取×3 / 查询×2 / 发送×2 |
| `CapabilityEnumItemService` | 9 | 集成能力枚举 · 删除×3 / 查询×2 / 检查×2 |
| `PayCallBackService` | 9 | PayCallBack · 通知×2 / 获取×2 / 初始化×2 |
| `PayService` | 9 | Pay · 获取×2 / 查询×2 / 下载×2 |
| `ScheduleService` | 9 | 调度 · 发送×4 / 新增×1 / 修改×1 |
| `LocationService` | 8 | Location · 获取×4 / 搜索×3 |
| `OfdService` | 8 | Ofd · 获取×6 / 上传×1 |
| `SmsCloudLeagueService` | 8 | 短信 · 获取×3 / 新建×2 / 修改×1 |
| `VoiceService` | 8 | Voice · 新建×4 / 查询×3 / 获取×1 |
| `MobilePluginConfigCapabilityService` | 7 | 配置集成能力 · 修改×2 / 查询×1 / 获取×1 |
| `MerchantService` | 7 | Merchant · 查询×4 / 新建×1 / 修改×1 |
| `SignatureCallBackService` | 7 | SignatureCallBack · 获取×3 / 执行×1 / 发送×1 |
| `SmsAutoService` | 7 | 短信 · 获取×6 / 运行×1 |

## biz 层：事件与监听

事件 6 个 · 监听器 2 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| M5 | `M5Event` |
| MeetingCallback | `MeetingCallbackDeleteBusEvent` |
| MeetingCallbackRegisterBus | `MeetingCallbackRegisterBusEvent` |
| SeeyonCensorSelected | `SeeyonCensorSelectedEvent` |
| SignSubscribe | `SignSubscribeEvent` |
| TemplateSubscribe | `TemplateSubscribeEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `TimingEventListener` | 3 |
| `CapabilitySpiEventListener` | 1 |

## web 层：Controller

共 43 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `DocCallBackController` | 40 |
| 核心实体 CRUD | `CapabilityManageController` | 39 |
| 核心实体 CRUD | `SignatureController` | 38 |
| 核心实体 CRUD | `OnlineDocController` | 29 |
| 核心实体 CRUD | `SmsManagerController` | 26 |
| 核心实体 CRUD | `IntelligentMissiveController` | 24 |
| 核心实体 CRUD | `EnterpriseCreditController` | 21 |
| 核心实体 CRUD | `EmailController` | 20 |
| 核心实体 CRUD | `VideoMeetingController` | 18 |
| 核心实体 CRUD | `OcrDataController` | 16 |
| 核心实体 CRUD | `BusinessTripController` | 13 |
| 核心实体 CRUD | `BankpayController` | 11 |
| 核心实体 CRUD | `PhysicalSealController` | 10 |
| 核心实体 CRUD | `CipBaseCallbackController` | 9 |
| 核心实体 CRUD | `ApiTestCallBackController` | 8 |
| 核心实体 CRUD | `MobilePluginWxOpenNotifyController` | 8 |
| 核心实体 CRUD | `CapabiityAppChannelManagerController` | 8 |
| 核心实体 CRUD | `PayController` | 8 |
| 核心实体 CRUD | `SignatureCallBackController` | 7 |
| 核心实体 CRUD | `InvoiceDataController` | 7 |
| 核心实体 CRUD | `OfdController` | 7 |
| 核心实体 CRUD | `VoiceController` | 7 |
| 核心实体 CRUD | `CapabilityEnumController` | 6 |
| 核心实体 CRUD | `LocationController` | 6 |
| 核心实体 CRUD | `MerchantController` | 5 |
| 核心实体 CRUD | `TestController` | 4 |
| 核心实体 CRUD | `WeixinPayCallBackController` | 4 |
| 核心实体 CRUD | `FaceIdController` | 4 |
| 核心实体 CRUD | `ScheduleController` | 4 |
| 核心实体 CRUD | `OfdCallBackController` | 3 |
| 核心实体 CRUD | `VideoCallbackController` | 3 |
| 核心实体 CRUD | `SmsController` | 3 |
| 核心实体 CRUD | `InvoiceImageController` | 2 |
| 核心实体 CRUD | `CapabilityAccessLogController` | 2 |
| 核心实体 CRUD | `WeatherController` | 2 |
| 核心实体 CRUD | `PhysicalsealCallBackController` | 1 |
| 核心实体 CRUD | `TripCallbackController` | 1 |
| 核心实体 CRUD | `CensorController` | 1 |
| 核心实体 CRUD | `CloudConnectController` | 1 |
| 核心实体 CRUD | `GisController` | 1 |
| 核心实体 CRUD | `OfflineMessageController` | 1 |
| 核心实体 CRUD | `ResumeController` | 1 |
| 核心实体 CRUD | `SearchController` | 1 |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **31** 张（来源构件：`cip-capability-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `cip_ability_app_channel_mng` | 应用通道管理表 | 2 |
| `cip_ability_app_feature_prov` | 应用能力特征通道配置明细表 | 2 |
| `cip_ability_count` | 用量统计表 | 2 |
| `cip_ability_cycle` | 能力周期表 | 2 |
| `cip_ability_doc_diff_record` | 文档比对记录表 | 2 |
| `cip_ability_email_config` | 电子邮件配置信息表 | 2 |
| `cip_ability_email_template` | 电子邮件模板信息表 | 2 |
| `cip_ability_email_user_a` | 电子邮件用户账户表 | 2 |
| `cip_ability_enum` | 能力接入枚举类 | 2 |
| `cip_ability_enum_item` | 能力接入枚举项 | 2 |
| `cip_ability_feature` | 能力特征表 | 2 |
| `cip_ability_invoice_check` | 发票验真请求执行详细记录表 | 2 |
| `cip_ability_invoice_record` | 发票OCR请求执行详细记录 | 2 |
| `cip_ability_log_record` | 日志记录表 | 2 |
| `cip_ability_mapper` | 三方服务和本地映射表 | 2 |
| `cip_ability_message_repush` | 推送失败的单独记录表 | 2 |
| `cip_ability_provider_manage` | 能力服务运维信息表 | 2 |
| `cip_ability_provider_params` | 能力服务配置信息表 | 2 |
| `cip_ability_provider_select` | 能力实现者运维信息表 | 2 |
| `cip_ability_sms_provide_t` | 短信厂商模版表 | 2 |
| `cip_ability_sms_sign` | 短信签名 | 2 |
| `cip_ability_sms_template` | 短信模版表 | 2 |
| `cip_ability_third_info` | 能力开放三方应用信息表 | 2 |
| `cip_ability_third_purchase` | 能力开放三方应用增购记录 | 2 |
| `cip_provider_charges` | 能力服务执行统计表 | 2 |
| `cip_provider_charges_record` | 能力服务执行记录表 | 2 |
| `cip_ability_dingtalk_link` | 钉钉消息链接表 | 1 |
| `cip_merchant` | 商户信息表 | 1 |
| `cip_third_platform_config` | 第三方平台配置信息 | 1 |
| `cip_video_meetingroom_resource` | 会议室资源管理 | 1 |
| `cip_video_user` | 视频用户信息 | 1 |

### 接口 → 表（3 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `ShortMessageProviderTemplateAppService` | `ShortMessageProviderTemplate` | `cip_ability_sms_provide_t` | `stem` |
| `ShortMessageSignAppService` | `ShortMessageSign` | `cip_ability_sms_sign` | `stem` |
| `ShortMessageTemplateAppService` | `ShortMessageTemplate` | `cip_ability_sms_template` | `stem` |

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

控制器 **13** 个、路由 **84** 条（来源：`cip-capability-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-cip-capability.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `IntelligentMissiveController` | `cip-capability/missive` | 26 |
| `DocCallBackController` | `cip-capability/doc` | 25 |
| `SignatureCallBackController` | `cip-capability/callback/signature` | 5 |
| `ApiTestCallBackController` | `cip-capability/apitest/callback` | 5 |
| `MobilePluginWxOpenNotifyController` | `cip-capability/wx-open` | 5 |
| `TestController` | `cip-capability/test` | 4 |
| `CipBaseCallbackController` | `cip-capability/base/callback` | 4 |
| `VideoCallbackController` | `cip-capability/video-meeting/callback` | 3 |
| `OfdCallBackController` | `cip-capability/ofd` | 2 |
| `WeixinPayCallBackController` | `cip-capability/work-wx-open` | 2 |
| `TripCallbackController` | `cip-capability/trip/callback` | 1 |
| `PhysicalsealCallBackController` | `cip-capability/physicalseal/callback` | 1 |
| `OcrDataController` | `cip-capability/ocr` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `RequestMapping` | `/service/cip-capability/base/callback` |
| `RequestMapping` | `/service/cip-capability/base/callback/cip` |
| `RequestMapping` | `/service/cip-capability/base/callback` |
| `RequestMapping` | `/service/cip-capability/base/callback/cip` |
| `PostMapping` | `/service/cip-capability/test/ai-test-create-third-app` |
| `PostMapping` | `/service/cip-capability/test/ai-test-third-app-increase` |
| `PostMapping` | `/service/cip-capability/test/ai-test-query-usage-amount` |
| `PostMapping` | `/service/cip-capability/test/test-query-third-app-info` |
| `GetMapping` | `/service/cip-capability/apitest/callback/signature/biz` |
| `GetMapping` | `/service/cip-capability/apitest/callback/video-meeting/callback/notify-hw` |
| `GetMapping` | `/service/cip-capability/apitest/callback/video-meeting/callback/notify-tx/{path}` |
| `PostMapping` | `/service/cip-capability/apitest/callback/video-meeting/callback/notify-tx/{path}` |
| `PostMapping` | `/service/cip-capability/apitest/callback/trip/callback/alibaba/{path}` |
| `GetMapping` | `/service/cip-capability/doc/wps/view/info` |
| `PostMapping` | `/service/cip-capability/doc/wps/edit/user/info` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 47 接口 / 446 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 81 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 6 事件 / 2 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 43 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（84 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 18/18 条安全路由命中（100%） | `LIVE` |
| 落表（33 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |

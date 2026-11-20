# 连接器能力清单（CIP：46 个能力接口 + 连接器体系）

> 数据源：`cip-capability-facade-5.3.276.jar` / `cip-capability-common` / `cip-connector-api` / `cip-connector-facade`
> 等级：`VERIFIED_STATIC_BYTECODE`（javap 方法签名实测）
>
> ## ⚠️⚠️⚠️ 版本与交付范围警示（2026-11-18 核对后补）
>
> **本文档依据的 4 个 jar 全部不在用户提供的官方 102 jar 清单内。**
>
> | jar | 是否在官方 102 | 说明 |
> |---|---|---|
> | `cip-capability-facade` | ❌ 不在 | 能力接口（OCR/签章/支付） |
> | `cip-capability-common` | ❌ 不在 | 能力 DTO |
> | `cip-connector-api` | ❌ 不在 | 连接器 SPI |
> | `cip-connector-facade` | ✅ 在（5.3.600，本机 5.3.286 旧版） | 连接器 facade |
>
> **⇒ 真实情况：能力（OCR/签章/支付）属于「可插拔能力包」，不在标准交付清单里。**
> **⇒ 但 `CHIT-extra/cip-capability-biz`（840 类，5.3.276）确实存在实现 —— 功能真实存在，只是非标准交付。**
> **⇒ 结论：内容可参考，但**引用时必须说明「非标准交付能力包」**，且版本是 5.3.276，官方无对应版本。**
>
> **官方清单里真正的 cip 相关包是 `boot-starter-cip`（5.3.603）—— 那是参数转义/开放API/V5迁移，与本文件讲的能力完全不同。见 `00A-repo-version-baseline.md` §5。**

---

## 0. 先纠正我上一条的错误

**我上一条写「cip-capability-common 里 355 个 Provider」——这是错的。**

实测包结构：
```
cip-capability-common    425 类
  ├─ provider.dto         299  ← DTO，不是 Provider
  ├─ capability.dto        58
  ├─ provider.enums        39
  └─ 其他                  29

cip-capability-facade    490 类
  ├─ capability.dto       425
  ├─ capability.api        46  ← ★ 真正的 46 个能力接口
  ├─ capability.enums      10
  └─ 其他                  9
```

**⇒ 是 **46 个能力接口**，不是 355 个 Provider。355 那个数是我把 DTO 数量说成 Provider 了。**

---

## 1. ★★★ 46 个能力接口全清单（按方法数排序）

**包：** `com.seeyon.cip.capability.api`
**全部是 `default` 方法 + `SingleRequest/Response` 包装，形态与 bpm/organization 一致。**

| # | 能力接口 | 方法数 | 能做什么 |
|---|---|---:|---|
| 1 | **`CapabilityManageAppService`** | **53** | **能力管理本身**（启停/默认 Provider/查询） |
| 2 | **`SignatureAppService`** | **39** | **电子签章** |
| 3 | **`DocOnlineAppService`** | **28** | **在线文档预览/编辑** |
| 4 | `IntelligentMissiveAppService` | 26 | **智能公文**（提取/比对/生成） |
| 5 | `EnterpriseCreditAppService` | 25 | **企业征信查询** |
| 6 | **`OcrAppService`** | **20** | **OCR 识别** |
| 7 | `VideoMeetingAppService` | 20 | 视频会议 |
| 8 | `BusinessTripAppService` | 14 | 商旅（部门/用户/城市同步、地址簿） |
| 9 | `ShortMessageTemplateAppService` | 14 | 短信模板管理 |
| 10 | `DocCallBackAppService` | 12 | 文档回调（文件信息/在线编辑/版本） |
| 11 | `ShortMessageSignAppService` | 12 | 短信签名管理 |
| 12 | `BankpayAppService` | 11 | 银行支付（余额/转账/明细/对账） |
| 13 | `ContractsAppService` | 11 | 合同（个人/企业证书流程） |
| 14 | `EmailPrivateAppService` | 11 | 私有邮箱配置 |
| 15 | `PhysicalSealAppService` | 10 | 物理印章（部门/人员同步、授权申请） |
| 16 | `EmailAppService` | 9 | 邮件发送 |
| 17 | **`InvoiceAppService`** | **9** | **发票 OCR + 验真** |
| 18 | `MobilePluginConfigAppService` | 9 | 移动插件配置 |
| 19 | `CapabilityEnumAppService` | 9 | 能力枚举管理 |
| 20 | **`PayAppService`** | **8** | **支付**（H5/退款/查询/证书） |
| 21 | `SealAppService` | 7 | 印章（上传/列表/详情/授权） |
| 22 | `LocationAppService` | 7 | 定位/距离/地理编码/行政区搜索 |
| 23 | `VoiceAppService` | 7 | 语音（实时/文件/识别） |
| 24 | `OfdAppService` | 5 | OFD 版式文件（预览/下载/印章/元数据） |
| 25 | `MerchantAppService` | 5 | 商户管理 |
| 26 | `ShortMessageProviderTemplateAppService` | 5 | 短信供应商模板 |
| 27 | `ArchivesAppService` | 4 | 档案（标题属性/分类/属性查询） |
| 28 | **`FaceIdAppService`** | **4** | **人脸识别**（录入/核验/更新/Token） |
| 29 | `MobilePluginAppletAppService` | 4 | 移动小程序（票据/绑定/免登 URL） |
| 30 | `ScheduleAppService` | 4 | 日程（增改/取消/详情） |
| 31 | `ShortMessageAppService` | 4 | 短信发送（同步/异步） |
| 32 | `AiAppService` | 3 | AI（第三方应用创建/用量） |
| 33 | `CapabilityAccessLogDbAppService` | 3 | 能力访问日志 |
| 34 | `ExcelSmsImportAndExportAppService` | 3 | 短信 Excel 导入导出 |
| 35 | `CensorAppService` | 2 | 文本审核 |
| 36 | `CompanyAccountServiceAppService` | 2 | 企业账户 |
| 37 | `InvoiceImageAppService` | 2 | 发票图片（建任务/上传） |
| 38 | `TranslationAppService` | 2 | 翻译（翻译/语言列表） |
| 39 | `WeatherAppService` | 2 | 天气（定位/查询） |
| 40 | `TokenAppService` | 2 | Token 有效期（查/存） |
| 41 | `DocGeneralizeAppService` | 1 | 文档通用（权限代理） |
| 42 | `ContractsCallBackAppService` | 1 | 合同回调 |
| 43 | `GisAppService` | 1 | GIS Token |
| 44 | `OfflineMessageAppService` | 1 | 离线消息推送 |
| 45 | `ResumeAppService` | 1 | 简历解析 |
| 46 | `SearchAppService` | 1 | 搜索 URL |

**合计 46 个能力接口。**

---

## 2. ★★ 六个高频能力的真实方法

### 2.1 OCR（`OcrAppService`，20 方法）

```java
getIdCardFrontData(...)      身份证正面
getIdCardBackData(...)       身份证反面
getBankCardData(...)         银行卡
getBusinessCardData(...)     名片
getBusinessLicenseData(...)  营业执照
// 还有约 15 个：发票/票据/表格/通用文字识别
```

**⇒ OCR 已覆盖**身份证、银行卡、名片、营业执照、发票**等主流证件。**

### 2.2 发票（`InvoiceAppService`，9 方法）

```java
getOcrInvoiceData(...)       发票 OCR 识别
getOcrAsyncResult(...)       异步识别结果（★ 大票走异步）
getOcrInvoiceSingle(...)     单张识别
verification(...)            发票验真
// 还有约 5 个
```

**★ `getOcrAsyncResult` 说明：大量发票走**异步队列**，不是同步返回。**

### 2.3 签章（`SignatureAppService`，39 方法）

```java
getSignatureViewUrl(...)     签章视图 URL
getSealInfo(...)             印章信息
getSealList(...)             印章列表
uploadFile(...)              上传待签文件
downFile(...)                下载已签文件
initiateSign(...)            发起签署
preSign(...)                 预签署
initPreSign(...)             初始化预签署
stamp(...)                   盖章
verifySeal(...)              验章
finish(...)                  完成
recall(...)                  撤回
```

**⇒ 完整电子签章流程：上传 → 发起 → 预签 → 盖章 → 验章 → 完成，支持撤回。**

### 2.4 在线文档（`DocOnlineAppService`，28 方法）

```java
getOfficeViewUrl(...)         Office 在线预览 URL
getOfficeEditUrl(...)         Office 在线编辑 URL
getCompositeViewUrl(...)      组合视图
getLatestPicViewUrl(...)      最新图片视图
```

**⇒ 文档在线预览/编辑走 URL 重定向，不是返回文件流。**

### 2.5 支付（`PayAppService`，8 方法）

```java
h5Pay(...)                         H5 支付下单
queryTransactionByOutTradeNo(...)  按外部单号查交易
closeTransaction(...)              关闭交易
refund(...)                        退款
queryRefund(...)                   查退款
getCertificateList(...)            获取证书列表
// 还有 2 个
```

**★ 完整支付生命周期：下单 → 查单 → 关单 → 退款 → 查退款。**

### 2.6 人脸识别（`FaceIdAppService`，4 方法）

```java
addFace(...)          录入人脸
faceCheck(...)        人脸核验
updateFace(...)       更新人脸
getAccessToken(...)   获取访问 Token
```

---

## 3. ★★ 能力管理（`CapabilityManageAppService`，53 方法）

**这是「能力的能力」—— 管理其他能力用哪个 Provider。**

```java
selectPageByConditions(...)     分页查能力
operationEnable(...)            ★ 启停能力
updateDefaultProvider(...)      ★ 切换默认 Provider
select(...)                     查询
// 还有 49 个
```

**★★ `updateDefaultProvider` 是关键：**
```
同一个能力（如 OCR）可以有多个 Provider（阿里云/腾讯云/百度）
默认用哪个由这个接口决定
```
**⇒ 这说明平台的能力层是「**多 Provider 可切换**」设计，不是绑死一家。**

### 支撑能力

| 接口 | 方法数 | 用途 |
|---|---|---|
| `CapabilityEnumAppService` | 9 | 能力枚举（能力类型字典） |
| `CapabilityAccessLogDbAppService` | 3 | 能力访问审计 |
| `TokenAppService` | 2 | Token 有效期管理 |

---

## 4. 连接器体系（cip-connector-*）

**连接器 = 把第三方系统的**组织结构/待办/消息**同步进平台的通道。**

### 4.1 `cip-connector-api` 的 20 个 SPI（扩展点）

**这些是给**第三方厂商实现**的接口：**

| SPI | 用途 |
|---|---|
| `MiddleTableOrgSyncSpiListenerService` | **中间表组织同步 - 监听** |
| `MiddleTableOrgSyncSpiPullService` | **中间表组织同步 - 拉取** |
| `MiddleTableOrgSyncDataCallbackService` | 中间表同步数据回调 |
| `MiddleTableOrgSyncExecuteCallbackService` | 中间表同步执行回调 |
| `MiddleTableOrgSyncMarkCallbackService` | 中间表同步标记回调 |
| `MobileOrgSyncProviderService` | 移动端组织同步 |
| `MobileOrgSyncBatchProviderService` | 移动端批量同步 |
| `MobileOrgSyncPullProviderService` | 移动端拉取同步 |
| `MobileProviderService` | 移动端通用 |
| `MobileTodoProviderService` | **移动端待办** |
| `MobileCallBackProviderService` | 移动端回调 |
| `MobileConfigProviderService` | 移动端配置 |
| `MobileApplicationProviderService` | 移动端应用 |
| `CipThirdAffairService` | 第三方事项 |
| `ConnectorCallbackMessageSendService` | 回调消息发送 |
| `ConnectorCallbackProviderService` | 回调 Provider |
| `DataBaseExecutorService` | **数据库执行器**（连接器直连库） |
| `LinkerSecurityService` / `LinkerSignService` | **Linker 安全/签名** |
| `SsoService` | SSO |

**★ 两个同步模式：**
```
中间表模式（MiddleTable*）  第三方往中间表写，平台按标记拉
移动端模式（Mobile*）        第三方提供 API，平台调
```

### 4.2 连接器枚举（17 个，说明支持的模式）

```java
AccessModeEnum               接入模式
AuthInfoModeEnum             认证信息模式
ClientScopeEnum              客户端范围
ConfigModeEnum               配置模式
DbStatementType              数据库语句类型
DbTypeEnum                   数据库类型
MobileTodoPriorityEnum       移动待办优先级
RequestTypeEnum              请求类型
SsoClientTypeEnum            SSO 客户端类型
VerifyFailProcessorTypeEnum  校验失败处理类型
WxMenuTypeEnum               微信菜单类型
GenderSpiEnum                性别
MemberTypeSpiEnum            人员类型
MiddleTableCategorySpiEnum   中间表分类
MiddleTableUnitTypeEnum      中间表单位类型
OrgSyncTypeSpiEnum           组织同步类型
ScopeTypeSpiEnum             范围类型
```

**★ `WxMenuTypeEnum` / `SsoClientTypeEnum` 说明：连接器支持**微信菜单**和 **SSO** 集成。**

### 4.3 `cip-connector-facade` 的连接器定义

| 包 | 类数 | 内容 |
|---|---|---|
| `application.dto` | 51 | 连接器应用 DTO |
| `connector.dto` | 25 | 连接器 DTO |
| `application.enums` | 11 | 应用枚举 |
| `connector.enums` | 10 | 连接器枚举 |
| `application.api` | 9 | 应用 API |
| `connector.api` | 5 | 连接器 API |
| `plug.enums` | 5 | 插件枚举 |
| `plug.dto` / `plug.api` / `ocip.dto` | 5 | 插件 |

### 4.4 其他连接器相关 jar

| jar | 类数 | 用途 |
|---|---|---|
| `cip-manager-facade` | 95 | 连接器管理（plug 41 / basic 23 / openapi 21） |
| `cip-openapi-common` | 21 | 开放 API 公共 |
| `cip-convert-facade` | 9 | 数据转换 |

---

## 5. ★ 能力 vs 连接器（必须区分）

| | **能力（Capability）** | **连接器（Connector）** |
|---|---|---|
| 包 | `cip-capability-*` | `cip-connector-*` |
| 解决什么 | **单个功能调用**（OCR/签章/支付/短信） | **系统级集成**（组织/待办同步） |
| 谁实现 | 能力 Provider（阿里云/腾讯云等） | 第三方厂商实现 SPI |
| 调用形态 | `*AppService` + Request/Response | SPI 接口，平台回调 |
| 例子 | `OcrAppService.getIdCardFrontData` | `MiddleTableOrgSyncSpiPullService` |

**⇒ 能力是「点」，连接器是「面」。**

---

## 6. Agent 使用判断

```
用户说要对接某个第三方功能
  ↓
问：是「调一个功能」还是「打通一个系统」？
  ├─ 调功能（OCR/发票/短信/签章/支付/人脸/翻译/天气）
  │    → 找 cip-capability-facade 的 46 个 *AppService
  │    → 先查 CapabilityManageAppService 看该能力有没有配 Provider
  │
  └─ 打通系统（组织同步/待办/SSO/消息）
       → 找 cip-connector-api 的 20 个 SPI
       → 判断用中间表模式还是移动端 API 模式
```

---

## 7. 未覆盖

| 项 | 说明 |
|---|---|
| 46 个接口的完整方法签名 | 我只列了总表 + 6 个高频的详细方法，其余只列方法名摘要 |
| 能力 Provider 实现类在哪 | **未找到**（可能在各厂商扩展包，不在标品 jar） |
| `CapabilityManageAppService` 53 方法的完整语义 | 未逐个读 |
| 连接器 SPI 的具体契约 | 未读方法体 |
| 能力与 Provider 的映射表 | 未读（可能在 DB 或配置） |
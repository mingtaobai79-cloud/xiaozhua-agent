# CIP 能力实现层（cip-capability-biz 5.3.276，840 类）

> 数据源：`D:/repo/CHIT-extra/cip-capability-biz/5.3.276/cip-capability-biz-5.3.276.jar`（2.3 MB，840 个顶层类）
> 等级：`VERIFIED_STATIC_BYTECODE`（zipfile 类清单 + 正则包路径 + 常量池域名扫描）
> ⚠️ **重要定位**：本 jar **不在**用户官方 102 清单内 → **「可插拔能力包」**，非标准交付。
> ⚠️ 对应 facade 版本 5.3.276，同理非标准。

---

## 0. ★★★ 这是「能力」的真实现层

**上一个验证过的 `cip-capability-facade`（46 个接口）只是契约。真实现全在这 840 个类里。**

```
cip-capability-facade（490 类）  ← 46 个 AppService 接口 + DTO
        ↓ 实现
cip-capability-biz（840 类）    ← ★ 本文件：37 个能力域 + 各大厂商 Provider
        ↓ 调用
第三方云服务（阿里云/腾讯云/百度/华为/微信…）
```

---

## 1. ★★★ 37 个能力域（按类数）

| 能力域 | 类数 | 能做什么 |
|---|---:|---|
| **video** | **147** | **视频会议**（腾讯/华为/企业微信） |
| **missive** | **64** | **智能公文**（泛微 Funcun / IdpsV10 / TextIn） |
| **signature** | **49** | **电子签章**（安信/点聚/数科/天印） |
| **ocr** | **48** | **OCR 识别**（百度/腾讯/泛微/默认） |
| **sms** | **36** | **短信**（阿里云/腾讯云/华为） |
| message | 31 | 消息推送（离线消息） |
| doc | 26 | 在线文档（WPS/永中/福昕/联想/明智） |
| invoice | 26 | 发票（EleCloud 电子云） |
| ofd | 24 | OFD 版式文件（点聚/金格/福昕/永中/WPS/联想） |
| resume | 18 | 简历解析（Mesoor） |
| schedule | 14 | 日程（企业微信） |
| censor | 13 | 文本审核（百度/自研） |
| manage | 11 | **能力管理（Provider 配置）** |
| mobileplugin | 10 | 移动插件（微信） |
| location | 9 | 定位（百度/高德） |
| voice | 9 | 语音（慧言/科大讯飞） |
| trip | 9 | 商旅（阿里商旅） |
| pay | 7 | 支付（微信支付） |
| translation | 7 | 翻译（百度） |
| email | 6 | 邮件（SMTP） |
| bankpay | 6 | 银行支付（中信银行） |
| credit | 6 | 企业征信（启信宝） |
| physicalseal | 5 | 物理印章（群杰） |
| weather | 5 | 天气（百度/高德） |
| search | 5 | 搜索（V5） |
| routing | 4 | **Provider 路由（核心机制）** |
| gis | 4 | GIS（农信采/SNKoudai） |
| openapi | 3 | 开放 API |
| faceid | 3 | 人脸识别（旷视） |
| ai | 3 | AI（致远自研 Chat） |
| archives | 3 | 档案 |
| printlabel | 2 | 标签打印（驰阔/硕方） |
| info / log / callback / file / mapper | 各 1–2 | 支撑 |

**⇒ 37 个域，每个域独立分包 `domain/service/<域>/(spi/<厂商>/)`。**

---

## 2. ★★★ SPI 厂商矩阵（**这份清单最有用**）

**★★★ 关键发现：每个能力域有 `spi/<厂商>/` 子包，装着该厂商的实现。**

### 2.1 OCR（48 类，4 个 Provider）

```
ocr / baidu    BaiduOcrServiceImpl + BaiduDataAdapter
               + card(5) / common / custom / finance(9) 适配包
ocr / tencent  TencentOcrServiceImpl + OcrClientFactoryBean
               + TencentDataAdapter + TencentInvoiceVerificationApi
               + card(7) / enums(2) / finance(10)
ocr / funcun   FuncunOcrServiceImpl（泛微）
ocr / impl     DefaultOcrServiceImpl（★ 兜底默认实现）
ocr / test     TestOcrServiceImpl（★ 测试桩）
```

**★ 三个结构性发现：**
1. **有 `impl` 兜底 + `test` 测试桩** —— 说明 Provider 体系是**契约-实现-测试**三层
2. **厂商实现内部再分 `card` / `finance` 子包** —— 按证件类型/票据类型细分
3. **`tencent` 里有 `TencentInvoiceVerificationApi`** —— 腾讯系能直接做发票查验

### 2.2 电子签章（49 类，4 个厂商）

```
signature / anxin     AnxinServiceImpl + StampingProperties + strategy(5)
signature / dianju    DianjuSignatureServiceImpl
signature / suwell    SuWellSignatureServiceImpl（数科）
signature / tianyin   TianyinServiceImpl + TianyinConstant + dto(22)
```

**★ `anxin` 里有 `strategy(5)` —— 签章策略模式（不同签章场景不同策略）。**
**★ `tianyin` 有 22 个 DTO —— 天印的接口最复杂。**

### 2.3 在线文档（26 类，6 个厂商）

```
doc / wpsv6        WpsV6OnlineServiceImpl + dto(13)
doc / yozo         YoZoOnlineServiceImpl（永中）
doc / suwell       SuWellOnlineServiceImpl（数科/福昕系）
doc / lenovo       LenovoOnlineServiceImpl + FileBookMarkTypeAdapterEnum
doc / wisemedical  WiseMedicalOnlineServiceImpl + WiseMedicalJwtUtil（明智医疗）
doc / impl         DefaultDocOnlineServiceImpl
doc / test         TestDocServiceImpl
```

### 2.4 OFD 版式（24 类，6 个厂商）

```
ofd / dianju    DianjuServiceImpl
ofd / kinggrid  KingGridServiceImpl + KingGridFixedLayoutProperties + MyPdfFileResource
ofd / suwell    SuWellFixedLayoutServiceImpl + OfdMetaExtractorUtil
ofd / yozo      YoZoFixedLayoutServiceImpl
ofd / wpsv6     WpsV6FixedLayoutServiceImpl
ofd / lenovo    LenovoFixedLayoutServiceImpl
```

**★ 6 个厂商都支持 OFD —— 信创适配做的很全。**

### 2.5 短信（36 类，3 大云 + 默认 + 测试）

```
sms / ali      AliYunSmsServiceImpl（发送）
               AliYunSignAutoServiceImpl（★ 签名自动申请）
               AliYunTemplateAutoServiceImpl（★ 模板自动申请）
               AliErrorCodeEnum / AliConstants
sms / tencent  TencentSmsServiceImpl + SmsClientFactoryBean
               TencentSmsSignAutoServiceImpl / TencentSmsTemplateAutoServiceImpl
               TencentErrorCodeEnum / TencentSmsConstants
sms / huawei   HuaWeiSmsServiceImpl + HuaWeiSmsSignAutoServiceImpl
               HuaWeiSmsTemplateAutoServiceImpl + HuaWeiUtils
               SSLCipherSuiteUtil / UnsupportProtocolException（★ SSL 适配）
sms / impl     DefaultSmsServiceImpl + DefaultSmsSignAutoService
               DefaultSmsTemplateAutoService + SmsCloudLeagueService
sms / test     TestSmsServiceImpl + TestSmsSignAutoServiceImpl + TestSmsTemplateAutoServiceImpl
```

**★★ 三家云都有「签名自动申请」和「模板自动申请」—— 说明平台做了**短信资质自动报备**。**
**⇒ 这是很深度的集成（一般只能手工去云控制台申请）。**

### 2.6 视频会议（147 类，3 个厂商 —— 最大域）

```
video / tencent   TencentVideoMeetingServiceImpl
                  + client(5) / common(8) / callback / dto(40+) / enums(2)
video / huawei    HuaweiVideoMeetingServiceImpl + HuaweiRequest + HmacSHA256
                  + DubboGeneralizeHandler     ★★ 注意这个！
                  + adapter(2) / callback(2) / request(20) / response(20) / dto(30+)
video / qywechat  QyWechatVideoMeetingServiceImpl + QyWechatVideoProperties
                  + QyWechatVideoTokenService + dto(9)
video / test      TestVideoServiceImpl
```

**★★★ `video/huawei/DubboGeneralizeHandler` —— 华为视频会议走 Dubbo 泛化调用！**
**⇒ 这印证了「标品应用可以 Dubbo 泛化」的形态。**

### 2.7 智能公文（64 类，3 个厂商）

```
missive / funcun    FuncunServiceImpl + adapter + dto(40)     ← 泛微
missive / idpsv10   IdpsV10ServiceImpl + dto(3) + enums
missive / textin    TextInServiceImpl + dto(7) + enums         ← TextIn（合合）
missive / test      TestMissiveServiceImpl
missive / enums     ResultCodeEnum
```

**★ `TextIn` 是合合信息的文档解析，用于公文的结构化提取。**

### 2.8 其他厂商

| 域 | 厂商 → 实现 |
|---|---|
| **发票** | `elecloud`（电子云）→ `EleCloudInvoiceServiceImpl` + `EleCloudDataAdapter` + finance(13) + verification(2)；`impl` 默认；`test` |
| **简历** | `mesoor` → `MesoorResumeServiceImpl` + dto(15) |
| **征信** | `qixinbao`（启信宝）→ `QiXinBaoProviderServiceImpl`；`impl` 默认 |
| **支付** | `weixin` → `WeixinPayServiceImpl` + `WeixinPayProperties` + `CertificateExtendService`（证书） |
| **银行支付** | `citic`（中信）→ `CiticBankpayProviderServiceImpl` + `CiticProperties` |
| **人脸** | `kuangshi`（旷视）→ `KuangShiFaceIdProviderServiceImpl` + Properties |
| **位置** | `baidu` → `BaiduLocationProviderServiceImpl`；`gaode` → `GaoDeLocationProviderServiceImpl` |
| **天气** | `baidu` / `gaode` |
| **翻译** | `baidu` → `BaiDuTranslationServiceImpl` + `BaiDuLanguages` + `Md5Util` |
| **语音** | `huiyan`（慧言）→ `HuiyanVoiceServiceImpl` + socket；`kedaxunfei`（科大讯飞） |
| **文本审核** | `baidu` → `BaiduCensorServiceImpl`；`impl` → `SeeyonCensorServiceImpl` + `SeeyonWordAllow/Deny`（★ 自研词库） |
| **日程** | `qywechat` → `QyWechatScheduleProviderServiceImpl` + TokenService |
| **商旅** | `alibtrip`（阿里商旅）→ `AlibabaTripServiceImpl` + client(3) |
| **物理印章** | `qunjie`（群杰）→ `qunjie` 子包 |
| **标签打印** | `chicore`（驰阔）/ `supoin`（硕方） |
| **GIS** | `nyncw`（农信采）/ `snkoudai` |
| **搜索** | `v5` → `V5SearchServiceImpl`（★ V5 数据源） |
| **AI** | `seeyon` → `SeeyonChatServiceImpl`（★ 致远自研对话） |

---

## 3. ★★ Provider 路由机制（`routing` 包，4 类）

```
domain/service/routing/ProviderHandler
domain/service/routing/ProviderServiceLoader
```

**★ 这两个类是**能力域到具体 Provider 的分发器**。**
**⇒ 配合 `manage` 包（11 类）的 `ProviderSelectorService` / `ProviderManageService`：**

```
manage/ProviderSelectorService     选择用哪个 Provider
manage/ProviderManageService       Provider 配置管理
manage/ProviderParameterService    Provider 参数（AK/SK）
manage/ProviderOpenApiService      开放 API
manage/ProviderCycleCountService   ★ 调用次数轮询计数
manage/ProviderEventConfigService  ★ 事件配置
```

**★★★ 这就是「多 Provider 可切换」的实现：**
```
同一能力域（如 OCR）
  ├─ 配多个 Provider（百度/腾讯/泛微）
  ├─ ProviderSelectorService 决定用哪个
  ├─ ProviderParameterService 存各自的 AK/SK
  └─ ProviderCycleCountService 做用量统计/轮询
```

**★ 实体层也有对应的表：**
```
CipProviderManage         Provider 主表
CipProviderParameter      Provider 参数表
CipSelectProvider         选中的 Provider
CipProviderCharges        Provider 计费
CipProviderChargesRecord  计费记录      ★ 说明有成本统计
```

---

## 4. ★ 从常量池扫到的真实外部域名

| 次数 | 域名 | 用途 |
|---:|---|---|
| **26** | `api.weixin.qq.com` | **微信（最多）** |
| 2 | `qyapi.weixin.qq.com` | 企业微信 |
| 2 | `mp.weixin.qq.com` | 微信公众号 |
| 1 | `restapi.amap.com` | 高德地图 |
| 1 | `api.mch.weixin.qq.com` | 微信商户（支付） |
| 1 | `fanyi-api.baidu.com` | 百度翻译 |
| 1 | `apifox.com` | 接口文档（开发期） |
| 1 | `127.0.0.1` | 本机 |
| 1 | `202.108.57.65` | 某固定 IP |

**★ 只有 9 个硬编码域名 —— 说明大部分厂商地址是**配置项**（存在 `CipProviderParameter` 表里），不是硬编码。**
**⇒ 这正是「能力可切换」的前提：地址可配。**

**⚠️ 大部分厂商 SDK 的域名在 jar 包里（如 `tencentcloud-sdk-java`）不在这里。**

---

## 5. ★★★ 三个必须理解的架构特征

### 5.1 契约-实现-测试三层

**每个能力域都有：**
```
XxxAppServiceImpl        对外门面（实现 facade 的接口）
XxxService               域内业务逻辑
spi/<厂商>/XxxImpl       厂商实现
spi/impl/DefaultXxxImpl  ★ 兜底默认实现
spi/test/TestXxxImpl     ★ 测试桩
```

**⇒ `impl` + `test` 的存在说明这是**可插拔架构的标准形态**。**
**⇒ `test` 桩意味着**能力可以不接外部就测通**。

### 5.2 配置化而非硬编码

```
9 个硬编码域名 vs 37 个能力域
```
**⇒ 地址/密钥/参数都在 DB 表（`CipProviderParameter`）+ 配置中心。**
**⇒ 符合你的要求：「配置文件的要写进 nacos」。**

### 5.3 计费与用量统计内建

```
ProviderCycleCountService    调用次数轮询
CipProviderCharges           计费
CipProviderChargesRecord     计费记录
```

**★ 每个 Provider 的调用成本被记录 —— 说明这是**商业化能力市场**的设计。**

---

## 6. ★ 与 facade 文档（15 号）的关系修正

**我在 `15-connector-capabilities.md` 里按 46 个接口列的「能力」，现在能对上实现：**

| facade 接口（15 号文档） | biz 实现（本文件） | 一致？ |
|---|---|---|
| `OcrAppService`（20 方法） | `ocr/OcrAppServiceImpl` + 4 厂商 | ✅ |
| `SignatureAppService`（39） | `signature/SignatureAppServiceImpl` + 4 厂商 | ✅ |
| `DocOnlineAppService`（28） | `doc/DocOnlineAppServiceImpl` + 6 厂商 | ✅ |
| `InvoiceAppService`（9） | `invoice/InvoiceAppServiceImpl` + EleCloud | ✅ |
| `PayAppService`（8） | `pay/...` + weixin | ✅ |
| `FaceIdAppService`（4） | `faceid/...` + kuangshi | ✅ |
| `CapabilityManageAppService`（53） | `manage/` + routing | ✅ |
| **`VideoMeetingAppService`（20）** | `video/` **147 类** ← **最大** | ⚠️ 15 号文档只列了名字 |
| `IntelligentMissiveAppService`（26） | `missive/` 64 类 | ⚠️ 同上 |
| `TranslationAppService`（2） | `translation/` + baidu | ✅ |
| `WeatherAppService`（2） | `weather/` + baidu/gaode | ✅ |

**⇒ 结论：15 号文档的接口清单**是对的**，只是当时不知道实现层有 840 类、37 个域、20+ 厂商。**

---

## 7. ★ 完整能力-厂商对照表（Agent 查表用）

```
能力        可选厂商
──────────────────────────────────────────────
OCR         baidu / tencent / funcun / (默认)
发票        elecloud / (腾讯OCR带查验) / (默认)
签章        anxin / dianju / suwell / tianyin
OFD         dianju / kinggrid / suwell / yozo / wpsv6 / lenovo
在线文档    wpsv6 / yozo / suwell / lenovo / wisemedical / (默认)
文档智能    funcun / idpsv10 / textin
短信        ali / tencent / huawei / (默认)
视频会议    tencent / huawei / qywechat
语音        huiyan / kedaxunfei
翻译        baidu
文本审核    baidu / (致远自研词库)
定位        baidu / gaode
天气        baidu / gaode
地图GIS     nyncw / snkoudai
人脸        kuangshi
征信        qixinbao / (默认)
简历        mesoor
支付        weixin
银行支付    citic
商旅        alibtrip
日程        qywechat
物理印章    qunjie
标签打印    chicore / supoin
搜索        v5
AI          seeyon（自研）
邮件        smtp
```

---

## 8. 未覆盖

| 项 | 说明 |
|---|---|
| 各厂商实现的方法体 | **未反编译**，只有类名/包结构 |
| `routing/ProviderHandler` 的选择算法 | 未读（轮询？权重？故障转移？） |
| `CipProviderParameter` 表字段 | 未 dump |
| 各厂商 SDK 版本 | 未读 `pom`/`MANIFEST` |
| `ProviderCycleCountService` 的计费模型 | 未读 |
| 为什么 `video/huawei` 用 `DubboGeneralizeHandler` | **未验证**（推测华为能力通过 Dubbo 暴露） |
| 46 个 facade 接口 ↔ 37 个 biz 域的**精确映射** | 部分推断（有 `XxxAppServiceImpl` 的能对上） |
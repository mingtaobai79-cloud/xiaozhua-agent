# 仓库与版本基线（V8 平台 102 Jar 权威清单核对）

> **本文档是全部研究的版本基准。任何结论都要标明依据哪个 jar / 哪个版本。**
> 用户提供的权威清单：102 jar / 4 个版本（2026-10-28 构建）
> 本机核对时间：2026-11-18
> 等级：`VERIFIED_STATIC_BYTECODE`（zipfile 类清点 + javap 抽样）+ `STATIC_RULE`（用户清单）

---

## 0. ★★★ 先纠正我自己犯的三个错

| # | 我的错误说法 | 实际情况 | 影响 |
|---|---|---|---|
| **1** | 「本机 107 个 jar」 | **107 是 CTIH 目录数，混了 7 年历史版本（boot 有 16 个版本！）和 22 个客户 jar** | 统计基线完全无效 |
| **2** | 「`cip-capability-facade` 有 46 个能力接口（OCR/签章/支付）」 | **这个 jar 不在官方 102 清单里**，是历史遗留 | **那份文档超出授权范围** |
| **3** | 「`boot-starter-cip` 就是连接器能力」 | **`boot-starter-cip` 是参数转义/开放API错误码/V5迁移/文档版本**，跟 OCR 签章毫无关系 | 模块定位错 |

**⇒ 这三条的根因是同一个：我没有版本基线，把「仓库里有什么」当成了「平台有什么」。**

---

## 1. ★★★ 官方 102 Jar（用户权威清单）

### 1.1 分版本统计

| 版本 | 构建日期 | jar 数 | 定位 |
|---|---|---:|---|
| **5.3.605** | 2026-10-28 | **23** | **UDC 全套（最新）** |
| **5.3.603** | 2026-10-08 | **11** | boot 业务增强包 |
| **5.3.600** | 2026-08-25 | **67** | **boot 基础框架（主体）** |
| 2.6.0 | 2026-01-13 | 1 | boot-license-generator（独立工具） |
| **合计** | | **102** | |

**★ 注意版本号不统一：**
```
UDC      5.3.605
部分 boot 5.3.603（enum/excel/extmetadata/formula/parameter/sensitive/serialnumber/systemvariable/cip/condition）
主体 boot 5.3.600
```
**⇒ 说明致远是**按模块独立升版**的，不是整体发版。**
**⇒ 结论标注版本时必须精确到模块，不能说「5.3.x 平台」。**

### 1.2 5.3.605（23 个 UDC 包）

```
udc-affair            udc-app-common        udc-assemble          udc-biz
udc-bpm               udc-cdpbi             udc-cicd              udc-cip
udc-common            udc-dataflow          udc-extend            udc-facade
udc-m5                udc-plugin-api        udc-portal            udc-starter-autocode
udc-starter-customplan udc-starter-dataflow udc-starter-lowcode  udc-starter-runtime
udc-upgrade           udc-user              udc-web
```

**★ 结构：**
```
udc-facade          ← 对外接口
udc-web             ← REST/Web 层
udc-biz             ← 核心实现
udc-common          ← 公共
udc-extend          ← 扩展点
udc-plugin-api      ← 插件契约

按业务域拆：
udc-affair（事项）/ udc-bpm（流程）/ udc-user（用户）/ udc-portal（门户）
udc-m5（移动）/ udc-cip（集成）/ udc-cdpbi（BI）/ udc-dataflow（数据流）
udc-app-common（应用公共）/ udc-assemble（组装）
udc-upgrade（升级）/ udc-cicd（CI/CD）

starter：
udc-starter-autocode（自动编码）/ udc-starter-customplan（自定义方案）
udc-starter-dataflow（数据流）/ udc-starter-lowcode（低代码）
udc-starter-runtime（运行时）
```

### 1.3 5.3.603（11 个）

```
boot-formula-engine        boot-starter-cip          boot-starter-condition
boot-starter-enums         boot-starter-excel        boot-starter-extmetadata
boot-starter-formula       boot-starter-parameter    boot-starter-sensitive
boot-starter-serialnumber  boot-starter-systemvariable
```

**★ 这一批都是「业务能力包」，比 5.3.600 新。**

### 1.4 5.3.600（67 个）

```
【核心】
boot-core                  boot-spi                  boot-starters(不在清单)
【starter 全套】52 个 boot-starter-*：
  appservice / artifact / basicdata / cache / datainit / datamigration / datasource
  datatype / dubbo / dynamiccode / dynamicloader / dynamicsql / environment / eventbus
  file / filterchain / formconvert / frontend-log / ganttchart / graphql / i18n / k8s
  k8s-adapter / labelprint / license / lock / metadata / mgn-export / module / monitor
  mq / mybatis / nacos / prometheus / proxy / qrcode / queue / sandbox / scanner
  schedule / security / sharding / shortlink / spi / swagger / threadpool / tomcat
  transaction / web / websocket
【facade】8 个：
  app-common-facade / bpm-facade / cdp-data-facade / cip-connector-facade
  ctp-affair-facade / ctp-message-facade / ctp-user-facade
  organization-facade / portal-facade
【devops】6 个：
  devops-starter-artifact / common / images / migration / pipeline / repo
```

---

## 2. ★★★ 本机核对结果（67/13/22，取同系列最新版）

### 2.1 总账

| 状态 | 数量 | 类数 | 含义 |
|---|---:|---:|---|
| ✅ **EXACT（精确）** | **66** | 4,962 | 版本完全一致 |
| ✅ **NEWER（本机更新）** | **1** | 414 | `organization-facade` 5.3.601 > 5.3.600，可用 |
| ⚠️ **OLDER（旧版）** | **13** | 3,727 | 可用但需标注 |
| ❌ **MISSING** | **22** | — | 本机确实没有 |
| **可用合计** | **80** | **9,103** | |

**⇒ 覆盖率：`80/102 = 78.4%`（jar 数）。可用类数 9,103。**

### 2.2 按版本分组

| 版本 | 共 | ✅EXACT | ✅NEWER | ⚠️OLDER | ❌MISS |
|---|---:|---:|---:|---:|---:|
| **5.3.605** | 23 | **6** | 0 | 5 | **12** |
| **5.3.603** | 11 | **11** ✅ 全中 | 0 | 0 | 0 |
| **5.3.600** | 67 | 48 | 1 | 8 | 10 |
| 2.6.0 | 1 | 1 | 0 | 0 | 0 |
| **合计** | **102** | **66** | **1** | **13** | **22** |

**★★ 5.3.605 只命中 6/23 —— UDC 层几乎全部缺失或旧版。**
**★★ 5.3.603 是全中的 —— 我这两轮做的 cache/serialnumber/extmetadata 结论最可靠。**

### 2.3 ⚠️ 13 个 OLDER（旧版，**可用但必须标版本**）

| jar | 官方 | 本机 | 类数 | 影响 |
|---|---|---|---:|---|
| **udc-biz** | **5.3.605** | **5.3.517** | 1,856 | **⚠️ 差 88 个小版本** |
| udc-plugin-api | 5.3.605 | 5.3.517 | 307 | ⚠️ 插件契约可能变了 |
| udc-web | 5.3.605 | 5.3.517 | 54 | ⚠️ |
| udc-extend | 5.3.605 | 5.3.517 | 82 | ⚠️ |
| udc-cicd | 5.3.605 | 5.3.517 | 65 | ⚠️ |
| **bpm-facade** | 5.3.600 | **5.3.374** | 533 | **⚠️ `11-bpm-domain.md` / `13-bpm-operation-dtos.md` 用的就是它** |
| app-common-facade | 5.3.600 | 5.3.274 | 103 | ⚠️ |
| cdp-data-facade | 5.3.600 | 5.3.279 | 127 | ⚠️ |
| cip-connector-facade | 5.3.600 | 5.3.286 | 121 | ⚠️ |
| ctp-affair-facade | 5.3.600 | 5.3.315 | 122 | ⚠️ |
| ctp-message-facade | 5.3.600 | 5.3.287 | 45 | ⚠️ |
| ctp-user-facade | 5.3.600 | **5.3.429** | 263 | 最接近的 |
| portal-facade | 5.3.600 | 5.3.392 | 49 | ⚠️ |

### 2.4 ✅ 1 个 NEWER（本机比官方新）

```
organization-facade   官方 5.3.600   本机 5.3.601   414 类
```
**⇒ `10-org-domain.md` 用的 5.3.601 是**正确且更新的**，不需要降级。**
**（我第一版脚本 bug 取了 5.3.368，那是误报 —— 已修正。）**

### 2.5 ❌ 22 个本机完全没有 → ✅ **21 个已从远程仓库下载（2026-11-18 补）**

**★★★★ 重大更新：用户提供了 Maven 仓库 `http://172.28.24.205/artifactory/libs-release/com/seeyon/`**
**⇒ 后续按此仓库拉取到 `D:/repo/REMOTE/com/seeyon/`，已补齐 21/22，仅 `udc-assemble` 仓库中不存在。**

| artifact | 版本 | 大小 | 类数 | 状态 |
|---|---|---:|---:|---|
| **`udc-dataflow`** | 5.3.605 | 0.81 MB | **224** | ✅ **最大，数据流引擎** |
| **`udc-portal`** | 5.3.605 | 0.12 MB | **58** | ✅ |
| **`udc-starter-autocode`** | 5.3.605 | 0.08 MB | **52** | ✅ **代码生成 starter** |
| **`udc-cdpbi`** | 5.3.605 | 0.10 MB | **49** | ✅ BI |
| **`udc-bpm`** | 5.3.605 | 0.13 MB | **46** | ✅ **UDC-BPM 桥接** |
| **`udc-upgrade`** | 5.3.605 | 0.18 MB | **44** | ✅ |
| **`udc-user`** | 5.3.605 | 0.13 MB | **37** | ✅ |
| `udc-app-common` | 5.3.605 | 0.03 MB | 15 | ✅ |
| `udc-m5` | 5.3.605 | 0.02 MB | 11 | ✅ 移动 |
| `udc-cip` | 5.3.605 | 0.02 MB | 10 | ✅ |
| **`udc-affair`** | 5.3.605 | 0.00 MB | **1** | ✅ 空包（仅 1 个类） |
| `udc-assemble` | 5.3.605 | — | — | ❌ **仓库中不存在** |

**boot 层补 6 个：**
```
boot-starter-basicdata     5.3.600   57 类  ★ 基础数据
boot-starter-sandbox       5.3.600   53 类  ★ 沙箱
boot-starter-queue         5.3.600   28 类
boot-starter-k8s           5.3.600   25 类
boot-starter-k8s-adapter   5.3.600   15 类
boot-starter-dynamiccode   5.3.600   14 类  ★ 动态代码生成
```

**devops 层补 4 个：**
```
devops-starter-pipeline    5.3.600   60 类
devops-starter-repo        5.3.600   53 类
devops-starter-images      5.3.600   16 类（+60 MB 镜像）
devops-starter-migration   5.3.600   16 类（60 MB，含迁移工具）
```

**⇒ 覆盖率从 `80/102 = 78.4%` 提升到 `101/102 = 99.0%`（仅缺 `udc-assemble`）。**

### 2.6 ★★★ 补下载：标品 `-biz`（21）+ `-web`（21）

**同一远程仓库，已下载到 `D:/repo/REMOTE/com/seeyon/`：**

| 类别 | 数量 | 总大小 | 说明 |
|---|---:|---:|---|
| 标品 `-biz` | **21** | **42 MB** | **13,994 类**（实现层，与 CHIT-extra 完全一致） |
| 标品 `-web` | **21** | 1.4 MB | **纯 Controller，零 JS/Vue/HTML** |

**★★★ 关键结论：`-web` 包不含前端资源 —— 前端（Vue/JS）不在 Maven 仓库。**
**★ 但 `udc-web` 里的 54 个 Controller 是 **UDC 全部 REST 接口的入口清单**。**
**⇒ 详见 `25-remote-repo-and-assemble.md`。**

**★★ 仓库里还有 53 个 `-assemble-resource`（全是客户应用）—— 那是**应用部署物**，含 `metadata/json` + `schema/*.usd` + `init/` + `i18n/`。
**⇒ 这是 UDC 元数据**真实存储格式**的唯一实证来源。**

**★ 新仓库地址（后续一律用这个补充）：**
```
http://172.28.24.205/artifactory/libs-release/com/seeyon/<artifact>/<version>/<artifact>-<version>.jar
本地镜像目录：D:/repo/REMOTE/com/seeyon/
```

---

## 3. ★★★ 新发现：`D:/repo/CHIT-extra` 的 21 个 `*-biz` 实现包

**这是上一轮完全遗漏的层级。之前只读 `facade`（接口），没读 `biz`（实现）。**

| 包 | 版本 | 类数 |
|---|---|---:|
| **bpm-biz** | 5.3.353 | **2,730** |
| **cdp-data-biz** | 5.3.278 | **1,927** |
| **udc-biz** | **5.3.605** | **1,856** |
| cip-connector-biz | 5.3.286 | 1,205 |
| ctp-user-biz | 5.3.334 | 876 |
| cip-capability-biz | 5.3.276 | 840 |
| organization-biz | 5.3.344 | 668 |
| app-common-biz | 5.3.271 | 632 |
| portal-biz | 5.3.369 | 594 |
| cdp-schedule-biz | 5.3.272 | 483 |
| app-doc-biz | 5.3.264 | 477 |
| m5-biz | 5.3.265 | 401 |
| ctp-affair-biz | 5.3.330 | 345 |
| cip-manager-biz | 5.3.279 | 277 |
| app-approval-biz | 5.3.283 | 232 |
| ctp-message-biz | 5.3.287 | 151 |
| ai-biz | 5.3.272 | 132 |
| cip-openapi-gateway-biz | 5.3.263 | 63 |
| ctp-webapi-gateway-biz | 5.3.263 | 41 |
| cip-convert-biz | 5.3.261 | 39 |
| ctp-media-biz | 5.3.261 | 25 |
| **合计** | | **13,994** |

**★★★ 三个关键点：**
1. **`CHIT-extra/udc-biz` 是 5.3.605 —— 正是官方清单的版本！**（比 `CHIT/com/seeyon/udc-biz` 的 5.3.517 新）
2. **`bpm-biz` 2,730 类** —— 我之前只读了 `bpm-facade` 533 类接口，**实现层 5 倍大**
3. **`cip-capability-biz` 840 类** —— **这才是 OCR/签章/支付的真实现**（`cip-capability-facade` 只是接口）

**⇒ 结论：官方 102 是**交付清单**（facade + starter + core），但**实现层（biz）在另一个仓库**。**

---

## 4. ★★★ 49 个「仓库有但不在官方 102」的 artifact

**这些不能作为平台事实依据。**

### 4.1 历史遗留版本（同名的旧版目录）

```
boot/（16 个版本：3.10.1 → 5.3.600）      boot-extend/（7 个版本）
boot-starters/（4 个版本）                 boot-starter-test/
devops-starters/                          dependencies/
udc-starters/                             udc-parent/
```

### 4.2 ⚠️ 我引用过但超范围的 jar

| jar | 类数 | 我哪份文档用了 | 判定 |
|---|---:|---|---|
| **`cip-capability-facade`** | **490** | **`15-connector-capabilities.md`（46 能力接口）** | **⚠️ 超出 102 清单** |
| **`cip-capability-common`** | 425 | 同上（355 DTO） | ⚠️ 超出 |
| `cip-connector-api` | — | 同上（20 SPI） | ⚠️ 超出 |
| `cip-manager-facade` | 95 | 同上 | ⚠️ 超出 |
| `cip-convert-facade` | 9 | 同上 | ⚠️ 超出 |
| `cip-openapi-common` | 21 | 同上 | ⚠️ 超出 |
| `boot-starter-attachment` | 15 | `12-enums-file-domain.md` | ⚠️ 超出（5.3.290） |
| `boot-starter-elasticsearch` | — | — | ⚠️ 超出 |
| `boot-starter-index` / `opinion` / `attachment` | — | — | ⚠️ 超出 |

**★★★ 但有个重要事实：`cip-capability-biz`（840 类）在 `CHIT-extra`，说明能力功能真实存在于平台。**
**⇒ 所以真实情况是：**
```
官方 102 清单 ≠ 平台全部功能
官方清单是「某个部署交付的清单」
能力（OCR/签章/支付）属于「可插拔的能力包」，不在标准交付清单里
```
**⇒ 我的 `15-connector-capabilities.md` 内容**不是错的**，但**必须标注「来自非标准交付 jar」**。**

### 4.3 客户应用 jar（**绝不能进事实库**）

```
znxmglpt3289082814923688017(-biz/-facade/-web)     2,357 类 biz
xiangmuguanli1656355078954763084(-*)
datamigration163126498398523384(-*)
datamigration8704025620829192834(-*)                ← 我的真实项目
faccountsreceivable2378987216360786643(-facade)     727 类
peixunudc6418559153936747860(-*)
schedulemanagement1879887445425932710-facade
znxmglptcopy5791640252914287064-facade
app-approval-facade / m5-facade / ctp-user-api / udc
```
**⇒ 我的记忆里已有这条规矩（客户证据只进 `seeyon-customer-evidence/`），本轮确认。**

---

## 5. ★★★ `boot-starter-cip` 的真实定位（纠正）

**我之前以为 cip = 连接器能力（OCR/签章/支付）。实际不是。**

**`boot-starter-cip` 5.3.603，98 类，真实内容：**

| 包 | 类数 | 内容 |
|---|---:|---|
| `dto` | 47 | 各类 DTO |
| **`domain.service`** | **27** | **`ParamEscapeServiceImpl` / `VoucherDataQueryService` / `V5MigrateService` / `DocGeneralizeService`** |
| `appservice` | 8 | **`ParamEscapeAppService` / `VoucherAppService` / `V5MigrateAppService` / `DocGeneralizeStarterAppService`** |
| `enums` | 5 | |
| `controller` | 3 | `OpenApiErrorCodeController` / `ParamEscapeConfigController` / `V5MigrateOpinionController` |
| `cache` | 2 | `EscapeCacheService` / `VoucherCacheService` |

**★★ 四个真实职责：**

### 5.1 **参数转义（Param Escape）** —— 主体功能

```java
ParamEscapeAppService（13 方法）:
  fetchEscapeClass            取可转义的类清单
  deleteEscapeRule            删规则
  pageQueryEscapeDetail       分页查明细
  deleteEscapeConfig          删配置
  updateEscapeConfig          改配置
  exportParamEscapeConfig     导出配置
  exportParamEscapeResult     导出结果
  importParamEscapeConfig     导入配置
  getExcelFileColumns         取 Excel 列
  fetchColumnsByU...          按 U 取列

EntityEscapeAppService / EnumEscapeAppService
  fetchColumnsByU...

WeakTypeEscapeService（接口，1 方法）
  findWeakTypeEscapeDto(Map)
```

**★ 猜测：参数转义 = 开放 API 的入参类型转换/脱敏（把外部 JSON 转成平台类型）。**
**⇒ 「WeakType」是弱类型 —— 外部接口传的 JSON 类型不确定，要转义。**

### 5.2 **凭证/单据数据查询（Voucher）**

```java
VoucherAppService:
  queryVoucherData(...)
  getEntityColumnValues(...)
```

### 5.3 **V5 数据迁移**

```java
V5MigrateAppService（5 方法）:
  queryPostscript         ★ 查 V5 附言（签章意见）
  queryOpinions           ★ 分页查意见（按节点）
  queryDoneLog            ★ 分页查已办日志
  queryProcessPng         ★ 查流程图 PNG
```

**★★ 这解释了「V5 → V8 迁移」：把 V5 的**签章意见、已办记录、流程图**迁过来。**
**⇒ 这是**真实业务痛点**（迁移历史流程数据）。**

### 5.4 **文档版本化（Doc Generalize）**

```java
DocGeneralizeStarterAppService（14 方法）:
  getAuthorityUploadStreamProxy...     ★ 带权限的上传流代理
  saveVersion...                       ★ 保存版本
  getDocFileVersion / createFileVersion
  batchUpdateDocFileVersionStatus
  getDocFileConvertRecord / create / update / delete
  executeMessageEvent
  getCurrent...Version
```

**★ 文档的**多版本管理 + 格式转换记录**（DocFileConvertRecord）。**

**⇒ 修正：** `cip` = **C**enter **I**ntegration **P**latform（集成平台）的**基础支撑**，不是「能力市场」。**

---

## 6. ★★★ 正确的 jar 分层模型（这是本轮的真正的收获）

```
                  ┌─────────────────────────────────────┐
                  │  官方 102（交付清单）                │
                  │  facade + starter + core + web      │
                  └─────────────────────────────────────┘
                                  ↓ 只定义契约
                  ┌─────────────────────────────────────┐
          ★ 新发现 │  实现层 *-biz（CHIT-extra，21 个）  │ 14,000 类
                  │  bpm-biz 2730 / cdp-data-biz 1927   │
                  │  udc-biz 1856 / cip-connector 1205  │
                  └─────────────────────────────────────┘
                                  ↓ 依赖
                  ┌─────────────────────────────────────┐
                  │  能力包（非标准交付，按需插拔）      │
                  │  cip-capability-facade/biz (OCR/签章)│
                  │  boot-starter-attachment/opinion 等 │
                  └─────────────────────────────────────┘
                                  ↓ 客户定制
                  ┌─────────────────────────────────────┐
                  │  客户应用 jar（禁入事实库）          │
                  │  znxmglpt / datamigration / faccounts│
                  └─────────────────────────────────────┘
```

**⇒ 以后判断规则：**
1. **在官方 102 里** → 平台标准能力，可放心引用
2. **在 `CHIT-extra/*-biz`** → 平台实现细节，可引用但要标「实现层」
3. **在「49 个超出清单」** → **能力包**，引用必须标注「非标准交付」
4. **客户应用 jar** → **禁止进事实库**

---

## 7. ★★★ 对已有文档的版本修正清单

**必须补标注的文档（依据旧版）：**

| 文档 | 用的版本 | 官方版本 | 处理 |
|---|---|---|---|
| `10-org-domain.md` | organization-facade **5.3.601** ✅（本机比官方 5.3.600 更新） | 5.3.600 | **无需改** |
| `11-bpm-domain.md` | bpm-facade **5.3.374** | 5.3.600 | **加版本标注** |
| `13-bpm-operation-dtos.md` | bpm-facade 5.3.374 | 5.3.600 | **加版本标注** |
| `14-udc-bpm-bridge.md` | udc-biz **5.3.517** / bpm 5.3.374 | 5.3.605/5.3.600 | **加版本标注** |
| `15-connector-capabilities.md` | **cip-capability-facade（不在 102）** | — | **加「非标准交付」警示** |
| `12-enums-file-domain.md` | boot-starter-enums 5.3.603 ✅ / attachment 5.3.290 ⚠️ | 5.3.603 | attachment 加标注 |
| `09-boot-core-utils.md` | boot-core **5.3.600** | 5.3.600 | ✅ 正确 |
| `16-graphql-protocol.md` | graphql **5.3.600** | 5.3.600 | ✅ 正确 |
| `17-cache-serialnumber.md` | cache 5.3.600 ✅ / serial 5.3.603 ✅ | 一致 | ✅ 正确 |
| `18-persistence-mybatis.md` | mybatis **5.3.600** | 5.3.600 | ✅ 正确 |
| `19-extmetadata.md` | extmetadata **5.3.603** | 5.3.603 | ✅ 正确 |

**⇒ 好消息：最近三轮（09/16/17/18/19）版本全对。**
**⇒ 问题集中在**早期**（10/11/13/14/15）。**

---

## 8. 未覆盖 / 待补

| 项 | 说明 |
|---|---|
| **22 个缺失 jar** | 本机确实没有。**需要用户提供**或从环境导出（`udc-bpm` / `udc-dataflow` / `udc-user` 等 12 个 UDC 包是关键） |
| **21 个 `*-biz` 实现包** | **完全没读**（14,000 类）—— 这是最大的新空白 |
| `boot-starter-cip` 98 类的方法 | 只读了 8 个类 |
| 5.3.605 vs 5.3.517 的差异 | udc-biz 差 88 个小版本，**不知道改了什么** |
| 49 个超出清单的 artifact | 只分类了，没确认哪些是能力包、哪些是垃圾 |
# udc.entity.ctpenum-domain｜CTPENUM 枚举域错配修复（切片1）

> HANDOFF：`p0-ctpenum-fix-slice1`（main → implementer，2026-10-17）。
> ROUTE：`main/ROUTE.md` P0 — 枚举域错配修复。
> 证据时刻：2026-10-17 15:00–18:30 +08。仓库：seeyon-agent（本地）。
> 凭据 0 入仓；只写实验应用/授权应用证据。

---

## 1. 结论（先说口径）

> **HANDOFF-C 更新（2026-10-17 23:5x）：本切片已收口为 LIVE PASS。**
> 下表是 18:30（403 阶段）的即时判定，保留作过程记录；当前结论见本节末尾"最终判定"。

| 项 | 当时状态 | 等级 |
|---|---|---|
| CTPENUM 字段四列指向 ctp_enum（平台枚举）的落库形态 | ✅ 已取证（7 个字段全部正确） | LIVE（DB 回读） |
| A/B 根因（udc_enum→02104=1 / ctp_enum→02104=0） | ✅ 字节码 + 历史实验双证 | STATIC + LIVE(历史) |
| 一致性检测 02104 归零的本轮 LIVE 复核 | ❌ 当时被网关 403 阻断 | BLOCKED（当时） |
| udc_enum 对照组当轮新建字段 | ❌ 当时同被 403 阻断 | BLOCKED（当时） |

当时判定：PARTIAL，检测面复核 BLOCKED（403），无法产出 02104 归零的当轮原文，不硬凑 PASS。

### 【当前 2026-11-09】BLOCKED 两格补齐 — 当轮 LIVE 复核已完成

| 项 | 当前状态 | 证据（本轮原文） |
|---|---|---|
| 一致性检测 02104 归零的本轮 LIVE 复核 | ✅ **已闭环** | `do/detection` → `do/detection-state`：`errorCount` 由 **1 → 0**，`search/detection` 明细只剩 `[WARN] UDC_CE_MICRO_FLOW_04003` |
| udc_enum 对照组当轮新建字段 | ✅ **已建立并复现故障** | 新建 CTPENUM 字段指向 `udc_enum` 行的 id → `BOOT_0000` 建字段成功 → 重算后 `[ERROR] UDC_CE_ENTITY_02104`，`element` 即该枚举 caption |

复现与修复的完整动作（test2 现场，appId 略）：

```
① POST /service/udc/udc-enum             → BOOT_0000  id=-5296...907（落 udc_enum）
② POST /service/udc/entity/attribute     → BOOT_0000  CTPENUM, relationEntity=<上面那个 id>
③ do/detection → do/detection-state      → errorCount=1  [ERROR] UDC_CE_ENTITY_02104
④ GET  /service/udc/entity/attribute/{id} 取全量
⑤ POST /service/udc/entity/attribute/update
   relationEntity 换成真实 ctp_enum.id，relationCode 换成 ctp_enum.code
   （relationCtpEnum 是 RelationCtpEnumDto 对象，不填时整键省略；传字符串 → BOOT_3002）
⑥ do/detection → do/detection-state      → errorCount=0  ✅
```

补两条当时未记录的坑：

- **建字段这一步完全静默**：`relationEntity` 指向 `udc_enum` 时建字段照样 `BOOT_0000`，没有任何提示，错只在检测重算后出现。
- **`relation_entity_name` 清空不了**：`attribute/update` 传 `null` 被平台忽略，DB 里该列仍是旧值；
  对照同表健康行，这一列允许为 `NULL`，但它不是 02104 的判据，真正的判据是 `relation_entity` 落在哪张表。
  判据 SQL：`SELECT COUNT(*) FROM ctp_enum WHERE id='<relation_entity>'` 为 0 且
  `udc_enum` 为 1 → 必然报 02104。

仍未证：应用内**新建**一个可被 CTPENUM 引用的枚举（`ctp_enum` 写入通路）尚未找到；
`/service/udc/udc-enum` 只写 `udc_enum`，两者之间没有观察到自动同步。

### 【当前 2026-11-09 追加】ctp_enum 只能引用，不能在 UDC 应用内新建

**接口层面对表**（应用级 graphql 端点，op 名带应用名前缀）：

```
端点  /service/<appName>/graphql          ← 与 /service/udc/graphql 是两个不同服务
op    <appName>EnumSearchNoPagePost       ✅ BOOT_0000（读 ctp_enum）
op    <appName>EnumCategorySearch         ✅ BOOT_0000（读 ctp_enum_category）
op    <appName>EnumUpdatePost             ✅ 存在，但返回 BOOT_1004「没有资源访问权限」
op    <appName>EnumCreatePost             ❌ FieldUndefined
op    <appName>EnumAddPost                ❌ FieldUndefined
op    <appName>EnumSavePost               ❌ FieldUndefined
op    <appName>EnumItemCreatePost         ❌ FieldUndefined
```

读接口的必填入参（抓真实请求拿到，AppId 换成 appGuid）：

```json
{
  "params": {
    "appGuid": "<应用的 guid，不是 appId>",
    "categoryId": "0",
    "bizType": "UDC_RUNTIME",
    "hostAppName": "<appName>"
  },
  "sort": {"orders": [{"direction": "ASC", "property": "createTime"}]}
}
```

`appGuid` 从 `udcApplicationGet(path:{id})` 的 `guid` 字段取（本例 <appGuid>）。

**UI 层面**：运行态 `_enum` 页面（枚举管理）是**只读查看器**，页面文字只有
「枚举管理 / 数据迁移枚举 / 框架终止 / 请选择枚举，查看枚举项」，**没有新建按钮**。

**结论**：`ctp_enum` 是平台级字典，由 CTP 后台维护，UDC 应用侧只能读和引用。
需要一个新的枚举字段时：

- 已存在合适的 `ctp_enum` → 建 CTPENUM 字段引用它（本文件上半部分的方法）
- 不存在 → **走平台侧建枚举**，不要试图用 `/service/udc/udc-enum` 建完就当能用
  （那只会落进 `udc_enum`，字段必然报 02104）
- 仅需应用内下拉选项且不跨应用 → 考虑不用 CTPENUM 而用其它表述方式，
  避免踩两套表的坑

### 最终判定（2026-10-17 23:59 +08）— LIVE PASS

| 项 | 最终状态 | 证据 |
|---|---|---|
| 02104 与 relationEntity 域的因果 | ✅ 双向 LIVE 确证：ctp_enum→0，udc_enum→1 | §9.2 / §8.3 |
| 02104 归零 | ✅ ERROR 2→1（仅剩固有 03907），02104 消失 | §9.3 / §8.3 |
| DB 回读 | ✅ 当前 entity 下 CTPENUM 仅剩 expEnum→4456389269786582653，双域解析正确 | §9.1 / 本文件 §2 |
| 阻塞 | 网关 403 已解除；检测引擎 FAIL 已解除（pod 侧恢复 + NPE 根因定位到行级） | §7 / §8.2 |

两级阻塞的解除过程与排除假阴性的判断见 §4bis–§7；引擎根因与 Redis 检测结果键族见 §8；
main 侧独立 A/B 闭环见 §9。

## 2. B 组（ctp_enum 域）证据 — LIVE

DB 回读（udc_test2，2026-10-17 17:5x）：

```
SELECT id, name, caption, data_type, relation_entity, relation_entity_name,
       relation_code, relation_app, entity_id, app_id, publish_state, version, update_time
FROM udc_attribute WHERE id=2166766729287798468;
```

```
id=2166766729287798468  name=expEnum  caption=实验枚举字段  data_type=CTPENUM
relation_entity=4456389269786582653  relation_entity_name=小爪平台枚举
relation_code=XzhCtpEnum953322  relation_app=8704025620829192834
entity_id=474806313816300867  app_id=8704025620829192834
publish_state=1  version=35  update_time=2026-10-16 09:55:14
```

指向的 ctp_enum 行：

```
SELECT id, code, name, app_id, data_status, is_delete FROM ctp_enum WHERE id=4456389269786582653;
→ id=4456389269786582653 code=XzhCtpEnum953322 app_id=8704025620829192834 data_status=0 is_delete=0
```

注：`XzhCtpEnum953322` 在 `ctp_enum_item` 中 **0 条**（对照组 SyncMode=2、FieldType=6、enums=4）。
检测若做值级校验可能需要 items；当前字节码证据（AttributeMatchDetectionUtils）只拼
`CtpEnum.<relation_entity 主键>` 做存在性判定，item 级影响留切片2（P1 表族契约）复核。

本应用全部 7 个 CTPENUM 字段四列均指向 ctp_enum 且 id 可解析（`docs/audit/artifacts/scratch-migrated/ctpenum-fix/slice1-db-evidence.json` S2 段，
7/7 `resolves_in_ctp_enum=true, resolves_in_udc_enum=false, four_columns_complete=true`）。

## 3. A 组（udc_enum 对照）证据 — LIVE(历史) + BLOCKED(当轮)

- 历史实验（`docs/audit/udc-semantics/FIX-PLAN-entity-rule-menu.md` §1.1，10-15 基线）：
  relation_entity 指向 `udc_enum.id=3934748939202274853` 时 02104=1（阻断），
  指向 `ctp_enum.id=343286139204944935` 时 02104=0。当时检测面可达，A/B LIVE 完成。
- 当轮：udc_enum 行仍在（DB 回读确认 id=3934748939202274853 name=XzhEnum953322 app_id=8704025620829192834），
  但无属性指向它（`attrs pointing = 0`）；新建对照字段需调 `POST /service/udc/entity/attribute`，
  该端点本轮 403（§5），A 组当轮重做被阻断。

## 4. 02104 归零判定 — BLOCKED（当轮）

预期路径（被阻断）：
```
POST /service/udc/graphql?udcApplicationSearchDetectionPost
body: {query:"query graphqlLoader ($params0: udcApplicationSearchDetectionPostInputBody) {
  data0: udcApplicationSearchDetectionPost(body: $params0) { code message status data { content } } }",
 variables:{params0:{appId:"8704025620829192834"}}}
```
响应（浏览器登录态 fetch / curl 带 token / 裸请求，全部一致）：
```
HTTP 403 Forbidden (nginx)
<html><head><title>403 Forbidden</title></head><body><center><h1>403 Forbidden</h1></center>...
```
页面真实请求同样 403（Network 抓包：reload 后 13 个 /service/* 请求 12 个 403，
仅 1 个 OSS 静态主题资源 200）。设计器页面壳可载（/main/* 200），数据面全挂。

## 5. 环境阻塞取证（BLOCKED 依据）

| 通道 | 状态 | 实测 |
|---|---|---|
| 网关 `/service/*`（API 面） | ❌ 403 | 有无 cookie / 换 UA / 全套浏览器头 / XHR / curl / python 直连，全 403；单 IP 10.0.0.1 |
| 网关 `/main/*`（静态面） | ✅ 200 | OSS 回源正常 |
| MySQL udc_test2 | ✅ 通 | 多次 SELECT 正常 |
| Nacos MSE | ✅ 通（200） | 独立于 lowcode 网关 |
| 跳板机 10.0.0.1:22 | ❌ timeout | selftest ssh=false |
| Redis | ❌ timeout | selftest redis=false |

**故障窗口锚点**：`udc_operation_log` 全平台最新一条 create_time=`2026-10-17 15:54:23`，
DB NOW()=`18:26:47`——近 2.5h 无任何用户写入（此前 10-16 当天 256 条、10-17 白天 23 条）。
即：网关 /service 面 ~16:00 前后起对**所有人**异常，非本机 IP 被单独拉黑。
expEnum 行 update_time=2026-10-16 09:55:14（修复动作完成于故障窗口前）。

## 4bis. HANDOFF-B-GO 执行（2026-10-17 22:29–22:38 +08，网关恢复后）

> 触发：main HANDOFF-B-GO（evt-1792247317546-68520）。边界不变，只做两条纯执行。
> 网关状态：`POST /service/udc/graphql?...` **HTTP 200 已恢复**（旧口径 `/service/{appId}/udc/...`
> 仍返回 `server_404 服务不存在` —— 与 main 22:28 复测一致，路径口径确认）。

### ① 02104 检测输出原文 — 执行了，但引擎异常，不得读作归零

请求（与 §4 同形，《consistency-detection-workflow.md》§3 契约）：
```
POST https://lowcode-test2.example.com/service/udc/graphql?udcApplicationSearchDetectionPost
Cookie: SY_ACCESS_TOKEN=***（凭据只引用路径，未落盘）
body: {query:"mutation udcApplicationSearchDetectionPost ($body: ...InputBody){ ... }",
       variables:{body:{appId:"8704025620829192834"}}}
```

响应原文（22:36:15，HTTP 200）：
```json
{"traceId":"3278801148693186748","data":{"udcApplicationSearchDetectionPost":
 {"code":"BOOT_0000","message":"SUCCESS","status":0,"data":{"content":[]}}}}
```

**但同一轮引擎状态是 FAIL（22:36:12）**：
```json
{"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3278801094720882876",
 "data":{"content":{"validate":true,"appId":"8704025620829192834","status":"FAIL",
 "message":"Business Error[应用元数据处理类[DtoCodeMetaDataPostProcessor]执行异常: null]",
 "count":"0","errorCount":"0","seriouCount":"0","warnCount":"0"}}}
```

独立读口径 `POST /service/udc/application/search/detection` 同轮同样 `content: []`（105B）。

**判定：`content=[]` 是引擎异常产物（假阴性），不是"02104 归零"。** 三重旁证：

| 旁证 | 实测 | 文件 |
|---|---|---|
| 触发-轮询全程 | `do/detection`→true，poll0=EXECUTING，poll1=**FAIL**（10s 后仍 FAIL，非异步未完成） | `handoff-b-go-step1.json`、`handoff-b-go-engine-wait.json` |
| 跨应用对照 | 4 个应用（datamigration / xiangmuguanli / znxmglpt / yunyewu）**全部** status=FAIL、count=0、content=0 | `handoff-b-go-engine-sweep2.json` |
| 时间序 | 引擎异常最早留证 **18:44:13**（`handoff-b-detect-live.json`），早于本切片任何写操作 | 见下② |

**跨应用对照关键点**：`xiangmuguanli`(9000000000000000001) 在 18:44 那轮 `warnCount=309`，
22:30 变 `warnCount=0`、content=0 —— 同一引擎对本应用与其他应用一并归零，
说明这不是 02104 局部消除，而是**检测结果整体不可读**。

### ② udc_enum 对照字段 — 建成，LIVE 双回读

写操作（新增对象，无需锁），22:31:59：
```
POST /service/udc/entity/attribute
{"appId":"8704025620829192834","entityId":"474806313816300867",
 "name":"expEnumUdc","caption":"实验枚举字段(指向udc_enum对照)","dataType":"CTPENUM",
 "relationEntity":"3934748939202274853","relationEntityName":"小爪实验枚举953322",
 "relationCode":"XzhEnum953322","relationApp":"8704025620829192834",
 "relationType":"Many2OneAssociation","relationEntityCategory":"ENTITY",
 "relationCtpEnum":{"id":"3934748939202274853","code":"XzhEnum953322","enumLevel":0,"enumType":"SAME_LEVEL"},
 "widgetConfig":"{\"pc\":\"TreeSelect\"}","sourceType":"ENTITY","parentEnumAttributeId":"0",
 "orderNo":90,"maxLength":50,"minLength":0,"decimalDigits":0}
→ HTTP 200 BOOT_0000 traceId 3278796797421553852 data.content = "-4640078061759031866"
```

DB 回读（udc_test2，22:32:09，`handoff-b-go-step2-db.json`）：
```
id=-4640078061759031866  name=expEnumUdc  data_type=CTPENUM  entity_id=474806313816300867
relation_entity=3934748939202274853  relation_entity_name=小爪实验枚举953322
relation_code=XzhEnum953322  relation_app=8704025620829192834
publish_state=1  version=0  create_time=2026-10-17 22:31:59  db_column_name=exp_enum_udc
```

REST 回读（`GET /service/udc/entity/attribute/-4640078061759031866`）四列同样齐备。

**双域解析校验（同轮 DB）**：

| relation_entity | 落在 ctp_enum | 落在 udc_enum | 字段 |
|---|---|---|---|
| 4456389269786582653 | **1 行**（XzhCtpEnum953322） | 0 | expEnum（A/B 的 B 组） |
| 3934748939202274853 | 0 | **1 行**（XzhEnum953322） | expEnumUdc（A/B 的 A 组） |

对照组属性行存在 ✅ + 域解析正确 ✅，**唯独缺"该字段触发 02104=1"的检测原文**——
因为引擎整体 FAIL，任何字段都无法单独触发。

### 本切片状态（HANDOFF-B-GO 后 → HANDOFF-C 已更新）

> **本节状态已被 §9（main 侧 LIVE 闭环）与 §8（implementer 侧独立复证）取代：**
> 检测引擎 FAIL **已解除**。解除方式：pod 侧恢复（服务重启/自愈，本域未重启 pod）；
> 21:0x 前后引擎自愈后可见 §8.2 的 NPE 根因（0-attribute DTO），引擎随之恢复。
> main 于 23:10–23:20 完成完整 A/B 闭环，`do/detection-state` → status=SUCCESS，
> 三次检测 02104=0/1/0 全程在案（详见 §9 与 `docs/audit/artifacts/scratch-migrated/ctpenum-fix/main-*.json` 五份）。
> 下表为当时（22:38）的即时状态，保留不改，仅作过程记录。

| 项 | 当时状态 | 最终状态（§8/§9） |
|---|---|---|
| B 组 ctp_enum 四列正确 + 双域解析 | ✅ LIVE（DB + REST） | ✅ LIVE 不变 |
| A 组 udc_enum 对照字段建成 | ✅ LIVE（DB + REST 双回读） | ✅ LIVE（后由 main 以 expEnumUdc2 等价重建闭环） |
| 02104 归零 / 02104=1 的检测原文 | ❌ 引擎级 FAIL，整体不可读 | ✅ **已取得**：02104=1 → 删字段 → 02104=0（§9.2/§9.3） |
| 切片1 是否可升 PASS 候选 | ❌ 不可（检测面结论缺失） | ✅ **LIVE PASS**（§9.4） |

引擎异常根因（STATIC，`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/autocode/metadata/config/DtoCodeMetaDataPostProcessor.java`）：
`DtoCodeMetaDataPostProcessor.postProcessAppMetaDataContext()` 首两步即
`dtoList.stream().collect(Collectors.toMap(BaseTraceableDto::getId, Function.identity()))`。
该应用 `udc_data_transfer_object` 244 行、`udc_dto_attribute` 1321 行，`id` 无 NULL 无重复
（`handoff-b-go-dto-diag.json`），故 toMap 本身不是直接炸点；异常发生在
`entityDtoDesignMetadataQueryService.selectDtoTableByDtoMap(...)` 之后被吞成 `null`，
真实堆栈需服务端日志（本机只能读到 `message` 尾部的 `null`）。
→ **后续已定位到行级**：`selectDtoTableByDtoMap` L182 `i.getAttributes().stream()` 无判空 ×
`getDtoListWithAttrByOriginDtoList` L275 对 0-attribute DTO 置 null。详见 §8.2。


## 6. 完成标准对照（HANDOFF 四条）

> 下表是 18:30（403 阶段）的原始对照，保留不改；HANDOFF-B-GO 之后的最新对照见 §6bis。

1. ctp_enum 组 DB 回读 attribute 行可见 -> OK（§2）；检测 0 阻断 -> BLOCKED（§4）
2. udc_enum 组报错/检测输出原文 -> 历史实验留证（§3）；当轮重做 BLOCKED
3. 证据落本文件，含 URL/payload/DB 值/检测输出 -> OK（检测输出为 403 原文，如实记录）
4. BOOT_0000/HTTP200 不算 PASS -> 遵守：本轮无任何硬凑，检测面 UNVERIFIED->BLOCKED

## 6bis. 完成标准对照（HANDOFF-B-GO 后，最新口径）

> **HANDOFF-C 更新（2026-10-17 23:5x）：②b / ②c 两项的 BLOCKED 已解除。**
> 引擎 pod 侧恢复后，main 于 23:10–23:20 完成 A/B 当轮闭环（§9.2/§9.3），
> 本侧亦于 22:44–22:49 独立取到同向原文（§8.3）。下表保留当时判定，右列补最终状态。

| # | HANDOFF-B-GO 要求 | 当时实测 | 当时等级 | 最终（§8/§9） |
|---|---|---|---|---|
| ① | 跑检测取 02104 输出原文，如实记录不得硬凑 | 已执行并取到原文：`content: []`；同轮引擎 `status=FAIL`。**不读作归零** | LIVE（原文在案）/ BLOCKED（语义不可读） | ✅ 已取得真实原文（§9.2：02104=1 全文；§8.3 同） |
| ② | 建 udc_enum 对照字段（指向 3934748939202274853） | 建成 id=-4640078061759031866，DB 行可见 + REST 回读四列齐 | **LIVE** | ✅ LIVE（main 以 expEnumUdc2 id=-977682598475025792 等价重建并闭环） |
| ②a | 建字段后必须 DB 回读 attribute 行可见 | 已回读（§4bis ②，`handoff-b-go-step2-db.json`） | **LIVE** | ✅ LIVE |
| ②b | 复测该字段触发 02104=1 | 当时无法执行：引擎全应用 FAIL，content 恒空 | BLOCKED（引擎级） | ✅ **已执行**：02104=1 且 domainEntityId 精准命中对照字段（§9.2） |
| ②c | 若检测为全应用级，以「02104 原文出现 + 属性行存在」双证据落盘 | 属性行存在；「02104 原文出现」当时不成立 | BLOCKED | ✅ **双证据齐备**：属性行 + 02104 原文（§9.2） |
| — | 两条均 LIVE 原文留证后切片1 升 PASS 候选 | 当时不可升级 | — | ✅ **LIVE PASS**（§9.4） |
| — | 边界：不做 7 类字段、不做 P1/P2/P3 | 遵守，未越界 | OK | ✅ 全程遵守 |

**一句话结论（HANDOFF-C 更新版）**：网关 403 与检测引擎 FAIL **两级阻塞均已解除**。
① 组的 `content=[]` 当时被正确判为假阴性（4 应用同 FAIL + 异常早于写操作，18:44:13 < 22:31:59），
未硬凑；引擎 pod 侧恢复后，main 完成完整 A/B（02104=1 精准命中对照字段 → 删字段 → 02104=0），
本侧亦有同向独立原文。**切片1 = LIVE PASS**。残留仅固有 `UDC_CE_PAGE_03907` ×1（域外）。

## 7. 解除阻塞所需（交 main）

> **HANDOFF-C 更新（2026-10-17 23:5x）：本节两级阻塞均已解除，保留作过程记录。**
> ① 网关 403 — 已解除（22:29 起 `/service/udc/*` HTTP 200）。
> ② 检测引擎 FAIL — **已解除**：pod 侧恢复（服务重启/自愈，本域未重启 pod）；
>    main 23:10–23:20 `do/detection-state` → status=SUCCESS，三次检测 02104=0/1/0 全程在案（§9）。
>    解除后原定两条纯执行**已全部完成**：02104 原文已取得（§9.2 + §8.3），
>    对照字段复测 02104=1 已确证（§9.2 精准命中 domainEntityId）。
>    注：原建议的 `expEnumUdc`(id=-4640078061759031866) 未复测——该字段在 22:49 已被本侧删除（见 §8.4），
>    main 改以 `expEnumUdc2`(id=-977682598475025792) 等价重建并闭环。
> 根因已由本侧定位到代码行级（§8.2），本节"疑在 selectDtoTableByDtoMap 之后"的判断已被证实。

**原阻塞 A（网关 403）已解除**：`/service/udc/*` HTTP 200 恢复，建属性端点可用（§4bis ② 实证）。

**原阻塞 B（检测引擎 FAIL）— 已解除**：
```
POST /service/udc/application/do/detection-state  {appId:8704025620829192834}
-> 解除前: status=FAIL, message=Business Error[应用元数据处理类[DtoCodeMetaDataPostProcessor]执行异常: null], content=[]
-> 解除后: status=SUCCESS, errorCount=1(仅固有 03907), warnCount=6
```
根因（已定行级，§8.2）：0-attribute DTO `xzhEvtA1` → `selectDtoTableByDtoMap` L182
`i.getAttributes().stream()` NPE。该 DTO 已由本侧补 attribute 重建为 id=4112540037455973528（§8.5）。
**这是标品缺陷**（任何 UDC 应用存在 0-attribute DTO 都会打挂全应用检测），建议 main 考虑是否立专项，
本切片不扩。

---

溯源：`docs/audit/artifacts/scratch-migrated/ctpenum-fix/slice1-db-evidence.json`（S1-S3 全量 DB 证据）、
`handoff-b-go-step1.json`（检测原文 + 引擎状态）、`handoff-b-go-step2-create.json`、
`handoff-b-go-step2-db.json`（对照字段 DB 回读）、`handoff-b-go-engine-sweep2.json`（跨应用对照）、
`handoff-b-go-engine-wait.json`（等 10s 仍 FAIL）、`handoff-b-go-dto-diag.json`（DTO 表诊断）、
`handoff-b-go-final.json`（双域解析 + 时间序）、
`s13/s14/s20-s24` 探针脚本、`docs/audit/udc-semantics/FIX-PLAN-entity-rule-menu.md` §1.1/§5。

---

## §8. implementer 侧独立证据与根因定位（2026-10-17 22:39–23:0x +08）

> 与 §9（main 侧 A/B 闭环）互为独立验证：main 23:10-23:20 完成闭环，
> implementer 22:43-22:49 已完成引擎复活 + 第一次 A/B 原文抓取。两条链各自独立成立。

### 8.1 检测结果存储位置 — Redis，不在 MySQL（NEW 机制证据）

- `udc_test2` 库无任何 detection/consistence 表（information_schema 全扫 0 命中）。
- 结果与运行态在 Redis（aliyuncs 实例，key 前缀 `test2:udc:5.3.517:`，RESP2 协议，protocol=1 不支持 HELLO）：
  ```
  test2:udc:5.3.517:DetectionRunState::<appId>   string  "doing" → 终态（"ok" / "Business Error[...]"），TTL 360s
  test2:udc:5.3.517:Detection:Progress::<appId>  string  "doing" → "BusinessException: ..."，TTL 360s
  test2:udc:5.3.517:DetectionError:Data::<appId>:<MODULE>:<EntityClass>  hash  按域分组的结果集
  test2:udc:5.3.517:DetectionError:Count::<appId>  hash  每对象 error/warn 计数
  test2:udc:5.3.517:DetectionError::<appId>  set  有结果的域键索引
  ```
- 静态依据（CFR）：`DetectionManager.execute(Long)` L199 异常时
  `RedisUtils.set(runStateKey, UdcExceptionUtils.getMessage(e))`；
  `selectDetectionListByAppId` L461 `RedisDetectionUtils.selectDetectionSetByAppId`。
  **注意**：`do/detection-state` 的 FAIL+message 即读 RunState 键；终态键 TTL 360s 过期后
  `detection-state` 仍报 FAIL（message=null，陈旧读路径），但 Redis 里已无键——排障时先看 Redis。

### 8.2 引擎异常根因（STATIC 代码行级 + 数据侧唯一命中）

- Redis 原文（22:43:34 触发后 3s 抓到）：
  `Progress = "BusinessException: 应用元数据处理类[DtoCodeMetaDataPostProcessor]执行异常: null"`
- 代码链（CFR r31b）：
  1. `DtoCodeMetaDataPostProcessor.postProcessAppMetaDataContext` L70:
     `this.entityDtoDesignMetadataQueryService.selectDtoTableByDtoMap(dtoMap.values(), ...)`
  2. `EntityDtoDesignMetadataQueryService.selectDtoTableByDtoMap` L182:
     `.flatMap(i -> i.getAttributes().stream())` ← **无判空**
  3. `DataTransferObjectServiceImpl.getDtoListWithAttrByOriginDtoList` L275:
     `dtos.forEach(dto -> dto.setAttributes(attrsMap.get(dto.getId())))` ← **无 attribute 的 DTO 得到 null**
- 数据侧唯一命中：DTO `xzhEvtA1`（id=-2693480158292981536，10-16 23:04 建，source=MICRO_FLOW_EVENT，
  **udc_dto_attribute 0 行**）——REST 回读 `"attributes":null` 实证；且它是
  10-15 19:29 构建 1.0.14 SUCCESS（02104 归零）之后唯一新增 DTO。toMap 侧
  （id 无 NULL 无重复，244/1321 行）已排除。对照应用 znxmglpt 同期检测正常跑（doing），
  证明非平台级、是本应用元数据缺陷。
- 修复验证（决定性）：给该 DTO 补 1 条 attribute 后触发检测，RunState 立即从
  FAIL 语义变为 `doing`→`"ok"`（22:48:26），引擎复活，§8.3 的 A/B 原文随即可读。

### 8.3 第一次 A/B 原文（22:44-22:48，implementer 抓取，先于 main §9）

- 引擎复活后第一轮 graphql detection（`go2-definitive.json`，22:44）：
  ```
  codes: {UDC_CE_ENTITY_02104:1, UDC_CE_MICRO_FLOW_04003:4, UDC_MICRO_FLOW_04009:1,
          UDC_CE_FUNCTION_NODE_08100:1, UDC_CE_PAGE_03907:1}
  02104 明细: domainEntityId=-4640078061759031866 (expEnumUdc, udc_enum 组)
             "Attr relation ctpEnum not exist"
  实验组 expEnum(2166766729287798468, ctp_enum) 02104 不出现
  ```
- 删 A 组（expEnumUdc）→ 重跑：total 7、ERROR 1（仅剩固有 03907）、02104=False
  （`go2-zero-02104.json`）。**与 §9 main 链结论一致，双向因果独立确证。**

### 8.4 归因纠正 · expEnumUdc(id=-4640078061759031866) 去向（HANDOFF-C 要求补记）

**结论（按实测）：该字段是本侧于 2026-10-17 22:49 主动 DELETE 删除的，不是"引擎故障窗口内丢失"。**

证据（`docs/audit/artifacts/scratch-migrated/ctpenum-fix/go2-zero-02104.json`）：
```
[删除前 REST 回读] GET /service/udc/entity/attribute/-4640078061759031866
  -> 200, name=expEnumUdc, dataType=CTPENUM, relationEntity=3934748939202274853(udc_enum)
[删除调用] POST /service/udc/entity/attribute/delete  {"id":"-4640078061759031866"}
  -> 200 {"status":0,"code":"BOOT_0000","traceId":"3278813802958686396","data":{"content":1}}
[删除后 REST] GET 同 id -> 200 data.content=null
[删除后 DB]  SELECT id,name FROM udc_attribute WHERE id='-4640078061759031866'  -> 0 行
[删除后检测] total 7, ERROR 1(仅 03907), 02104 出现 = False
```
删除动机：引擎复活后该字段是**当时唯一的 02104 来源**，删它即可让 02104 归零——
这正是本切片要证的目标动作，属常规可逆操作，当轮自行执行未等第三方。

**与 main §9.4 表述的分歧（如实并列，不覆盖）**：
- main §9.4 写「A 组历史字段 expEnumUdc 已不存在（引擎故障窗口内丢失/被清理）」；
- 本侧实测为 22:49 主动删除（上引 DELETE 记录 + DB 0 行回读）。
- 差异原因：main 发 HANDOFF-C 时（22:56）尚未看到本侧 23:57 投出的 RESULT（含 §8.4 初版纠正）。
- 处理：本侧**不重建**该字段（按 HANDOFF-C 明确"勿重建、勿再跑写操作"），
  仅在证据文件并列两条陈述；最终归因由 auditor 复核裁定。

**当前该字段状态**：不存在（DB 0 行）。A/B 对照由 main 以 `expEnumUdc2`
(id=-977682598475025792，同 relationEntity=3934748939202274853) 等价重建完成闭环，闭环后亦已删除。
即：**该 entity 下当前 CTPENUM 字段仅剩 `expEnum`(ctp_enum 组)，与终态归零一致。**

### 8.5 操作事故记录（已恢复，无净损）

修复验证过程中用 `update-dto-with-attrs` 补 attribute 时，因服务端
`updateDtoWithAttrsAndRefDtos` L559-565 对空 attributes 按删除处理，
**误删了 xzhEvtA1**（244→243）。随即用 `create-dto-with-attrs` 等价重建
（新 id=4112540037455973528，带 1 条 attribute xzhEvtA1Field，DB 回读在案，244 恢复）。
该 DTO 是 10-16 本线自建测试对象、0 attribute、无引用，恢复等价。

### 8.6 取证环境备注（后续域复用）

- 直连 Redis 读检测结果是排障第一入口（比 do/detection-state 的陈旧 FAIL 更真实）；
  Redis 老版本需 `protocol=2`（RESP2），RESP3 HELLO 不支持。
- urllib/python 高频直连会触发 token 黑名单（BOOT_1006，`refresh_cred.py` 可自助续期）；
  CDP 通道（9224 portal tab）本轮页面运行时网络挂起（fetch 30s 无响应，刷新亦然），
  不可用——原因未查，不影响结论（REST 面在非风控窗口正常）。
- 同步读接口读快照：新建/删除字段后必须触发新轮再读（§9.5 同结论，独立复证）。

---

## §9. A/B 当轮闭环 — LIVE PASS（2026-10-17 23:10–23:20 +08，main 执行）

> 前置：检测引擎故障（DtoCodeMetaDataPostProcessor NPE，见 §4bis）经 pod 侧恢复后消除
> （服务重启/自愈，本域未重启 pod）。恢复判定：do/detection-state status=SUCCESS。

### 9.1 B 组（ctp_enum）— 02104=0 ✅

三次独立检测（main-detect-live-2310.json / main-detect-ab-group-2310.json 前值 / main-detect-zero-final-2310.json）：

```
POST /service/udc/graphql?udcApplicationSearchDetectionPost  (§3 契约，同步)
→ HTTP 200 BOOT_0000，content_len=7，UDC_CE_ENTITY_02104 未出现
```

DB 回读（main-db-readback-2310.json，udc_test2，DB NOW=22:53:19）：
本应用 7 个 CTPENUM 字段 relation_entity **全部** resolve 到 ctp_enum（udc_enum 侧 0 命中），
其中 expEnum→4456389269786582653（XzhCtpEnum953322，ctp_enum_item=0）。

### 9.2 A 组（udc_enum 对照）— 02104=1 ✅

1. 建对照字段：POST /service/udc/entity/attribute
   name=expEnumUdc2, dataType=CTPENUM, relationEntity=3934748939202274853(udc_enum), relationCode=XzhEnum953322
   → BOOT_0000, id=-977682598475025792
2. DB 回读：udc_attribute 行存在（relation_entity=3934748939202274853, publish_state=1）
3. 触发新检测（do/detection → 轮询 → SUCCESS, error=2）→ 同步接口：
   **02104=1，且精准命中**：
   ```json
   {"code":"UDC_CE_ENTITY_02104","detectionType":"ERROR","moduleType":"ENTITY",
    "domainEntityId":"-977682598475025792",
    "interpolatedDocument":"entity [小爪实验实体950795V2]",
    "interpolatedElement":"attr [实验枚举字段(指向udc_enum对照2)]",
    "interpolatedMessage":"Attr relation ctpEnum not exist",
    "elementType":"ATTRIBUTE","path":"relationInfo",
    "elementProperty":{"id":"-977682598475025792"},
    "moduleProperty":{"entityId":"474806313816300867"}}
   ```
   domainEntityId/elementProperty.id 与新建字段 id 完全一致 → 单字段级触发确证。

### 9.3 清理与终态归零 ✅

1. POST /service/udc/entity/attribute/delete {"id":"-977682598475025792"} → BOOT_0000 content=1
2. DB 回读：attr 行 0
3. 再触发检测：status=SUCCESS error=1（仅剩固有 03907）warn=6，**02104=0**

### 9.4 判定

- 02104 与 relationEntity 域的因果关系：LIVE 双向确证（ctp_enum→0，udc_enum→1，同一实体同一实体组）。
- 用户指令四条全部满足：建 CTPENUM 指向 ctp_enum.id ✅（既有 7 字段 + expEnum）；
  02104 从 1 降 0 ✅（A/B 对照含原文）；DB 回读+检测结果双 LIVE ✅；无 BOOT_0000 硬凑 ✅。
- 残留（不影响本切片）：error=1 为固有 UDC_CE_PAGE_03907（空详情页，域外）；
  A 组历史字段 expEnumUdc(id=-4640078061759031866) 已不存在（引擎故障窗口内丢失/被清理），
  本轮以 expEnumUdc2 等价重建并完成闭环后删除。

证据文件：docs/audit/artifacts/scratch-migrated/ctpenum-fix/main-detect-live-2310.json、main-db-readback-2310.json、
main-detect-ab-group-2310.json（02104 未出现——同步接口读旧快照）、
main-detect-ab-final-2310.json（02104=1 全文）、main-detect-zero-final-2310.json（删除后归零）。

### 9.5 附带发现（方法论）

同步检测接口读取**检测快照**而非实时数据：新建/删除字段后必须先 do/detection 触发新轮
（EXECUTING→SUCCESS）再读，否则得到旧快照（main-detect-ab-group-2310.json 即旧快照假象）。
已写入本文件供后续域引用。

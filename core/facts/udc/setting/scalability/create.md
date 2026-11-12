# 设置域 · 扩展实体（Scalability Option）

> 版本：`udc-web-5.3.517` / `udc-biz-5.3.517`
> 证据等级：**LIVE PASS**（方案 + 预留组全打通）
> 实现：`components/udc/setting/scalability_constraints.py`

## 零、最大发现：父子两级用**两种协议**

```
方案    REST     /service/udc/scalability-option              ← 连字符
预留组  GraphQL  udcScalabilityPost                           ← ★ 不是 REST
读方案  REST     GET /service/udc/scalability-option/select-by-appid/with-detail/{appId}
```

我最初以为预留组也走 REST `update` 带 `scalabilityDtoList`，**2 种变体全部静默失败**
（子项 `id=0` 能过校验但 `udc_scalability` 零写入）。

真相是从页面真实操作抓包得到的 —— 表单底部点「确定」时发的是
`/service/udc/graphql?udcScalabilityPost`。

这与**字段集完全同一模式**（父 REST / 子 GraphQL）。

## R-E1 Capability

扩展实体 = 给实体预留一批字段（`前缀 + 两位序号`），避免改表结构。
页面上配「字段类型 / 字段名称前缀 / 预留字段数量（最多 20）」，右侧实时预览。

```
方案     udc_scalability_option    名称 + 应用
预留组   udc_scalability           前缀 + 数量 + 数据类型（option_id → 方案 id）
```

## R-E2 Version / 协议

```
方案 REST（连字符）
POST /service/udc/scalability-option                              新建（@RequestBody）
POST /service/udc/scalability-option/update
POST /service/udc/scalability-option/delete                       @MultiRequestBody Long id
GET  /service/udc/scalability-option/{id}
GET  /service/udc/scalability-option/select-by-appid/tree/{appId}
GET  /service/udc/scalability-option/select-by-appid/with-detail/{appId}
POST /service/udc/scalability-option/select-all-optionName
GET  /service/udc/scalability-option/data-type/{appId}

预留组 GraphQL ★
     udcScalabilityPost                                           加预留组
     udcScalabilityOptionOptionGet                                读某方案的预留组
```

## R-E3 Input

### ScalabilityOptionDto（REST 父级，反编译 udc-biz）

```java
Long   id                // @NotNull(groups=Update)
Long   appId             // @NotNull；-1 = 全局扩展
String name              // @NotBlank 方案编码
String caption           // @NotBlank 方案名称
List<ScalabilityDto> scalabilityDtoList   // ★ 本接口不消费
List<AttributeDto>   attributeDtoList
```

### 预留组 body（GraphQL `udcScalabilityPost`）

页面实际发出的完整 body（逐字）：

```json
{
  "dataType": "STRING",
  "prefix": "probeExt",
  "count": 5,
  "dataTypeProperties": "{\"minLength\":\"0\",\"maxLength\":50}",
  "optionId": "6348326125487248474",
  "caption": "probeExt"
}
```

⚠ `dataTypeProperties` 是**字符串化的 JSON**，且里面 `minLength` 是**字符串** `"0"`、
`maxLength` 是**数字** `50`（页面就这么发的，照抄）。

### ScalabilityDto（反编译对照）

```java
Long    id                // @NotNull(groups=Update)
Long    appId
Long    optionId          // @NotNull
String  prefix            // @NotBlank @Size(max=20)
String  caption           // @NotBlank
Integer count             // @NotNull @Max(50) —— 页面 UI 限 20
String  dataType          // @NotBlank，如 STRING
String  dataTypeProperties
```

## R-E4 Required

| 缺失/非法 | 报错 |
|---|---|
| appId | `BOOT_1001` appId 不能为null |
| name / caption | `BOOT_1001` 方案编码/名称 |
| 预留组 `optionId` | `BOOT_1001` 方案id 不能为null |
| 预留组 `id`（update 场景） | `BOOT_1001` id 不能为null |

## R-E5 Execution

### 1) 建方案（REST）

```
POST /service/udc/scalability-option
{ "appId": <appId>, "name": "zxjExtOpt", "caption": "验收扩展实体" }
→ BOOT_0000, data.content = <方案 id>
```

⚠ 不能一次带 `scalabilityDtoList`：子项 `optionId` 有 `@NotNull`，
create 时方案 id 还不存在 → `BOOT_1001 方案id 不能为null`。

### 2) 加预留组（GraphQL）★

```
POST /service/udc/graphql?udcScalabilityPost
mutation graphqlLoader ($params0: udcScalabilityPostInputBody) {
  data0: udcScalabilityPost(body: $params0) { code data { content } message status }
}
variables.params0 = <R-E3 的预留组 body>
→ BOOT_0000, data.content = <预留组 id>
```

### 3) 读方案（REST）

```
GET /service/udc/scalability-option/select-by-appid/with-detail/{appId}
→ data.content = [ScalabilityOptionDto, ...]
```

### 4) 读某方案的预留组

```
POST /service/udc/graphql?udcScalabilityOptionOptionGet
{"optionId": "<方案 id>"} → [{caption,count,dataType,dataTypeProperties,id,optionId,prefix,publishState}]
```

## R-E6 Side Effects

```
udc_scalability_option   方案主表
udc_scalability          预留组（option_id → 方案 id）
udc_custom_ext_field     实际派生字段（本 app 0 行 —— 预留是逻辑占位，不立即建物理字段）
```

## R-E7 Constraints

- `prefix` ≤ 20 字
- `count` ≤ 50（DTO `@Max(50)`）；**页面 UI 限 20**
- `appId = -1` 表示全局扩展
- 路径是连字符 `scalability-option`（与 `attributeSet` 驼峰不同）
- `dataTypeProperties` 是 JSON 字符串，`minLength` 用字符串、`maxLength` 用数字

## R-E8 Evidence

```
反编译 /d/repo/CHIT/com/seeyon/udc-web/5.3.517/udc-web-5.3.517.jar
       → ScalabilityOptionController（@RequestMapping "udc/scalability-option"）
反编译 /d/repo/CHIT/com/seeyon/udc-biz/5.3.517/udc-biz-5.3.517.jar
       → ScalabilityOptionDto / ScalabilityDto

页面抓包 2026-10-21（关键突破）
       扩展实体 → 左列表选中方案 → 右侧填「前缀=probeExt / 数量=5」
       → 预览区显示 probeExt01，probeExt02，…，probeExt05
       → 点 .extension-form-footer 内的「确定」
       → 页面发送 /service/udc/graphql?udcScalabilityPost
       → body 见 R-E3（完整逐字）

DB 回读 udc_scalability:
       id=-2554688686809495644  option_id=6348326125487248474
       prefix=probeExt  caption=probeExt  count=5  data_type=STRING
       data_type_properties={"minLength":"0","maxLength":50}
```

## R-E9 Verified

| 项 | 状态 | 证据 |
|---|---|---|
| 建方案（REST） | **LIVE PASS** | id=6348326125487248474，DB 回读正确 |
| **加预留组（GraphQL `udcScalabilityPost`）** | **LIVE PASS** | id=-2554688686809495644，DB 回读正确 |
| 读方案（with-detail） | **LIVE PASS** | 返回方案列表 |
| 读预留组（`udcScalabilityOptionOptionGet`） | **LIVE PASS** | 抓包确认 |
| `delete` | **LIVE PASS** | ★ 走 **GraphQL `udcScalabilityDeletePost`**，body `{appId, id}`。**REST `/udc/scalability-option/delete` 6 种 body 形态全部 `BOOT_3000 message:null`**（反序列化失败），只有 GraphQL 通道可用。回读该 id 已消失（负数 id `-8933883353214396219` 删除实测）。见 §R-E9-附 |
| `data-type/{appId}` | **LIVE PASS** | GET 返回 **18 种**，全部 `validate=true`（含 enableCalculable/enablePattern 等 20 余个能力位）。逐个实发后 **17 种可写**，仅 `CTPENUM` 被拒（`BOOT_1000 扩展字段不允许选择级联枚举`）。见 §10.3 |
| 实际派生物理字段（`udc_custom_ext_field`） | **✅ 定性完成：依赖 Ext 实体，本应用本就没有** | 见下 §物化条件 |

### R-E9-附：2026-10-22 完整验收（6 项）

```
① data-type 端点        HTTP 200，18 种类型                          PASS
② 读方案 with-detail     HTTP 200，2 个方案（zxjExtOpt / dsa）        PASS
③ 加预留组（类型覆盖）    25 组 / 17 种类型（DB 回读）                  PASS
④ 新建预留组             udcScalabilityPost → BOOT_0000
                        DB 回读 1 行（prefix=zva01, count=2）          PASS
⑤ delete 预留组          udcScalabilityDeletePost → BOOT_0000
                        DB 回读该 id 已消失，组数 26→25                PASS
⑥ 物理派生字段           本 schema 0 行 / 全实例 69 个 schema 有该表    定性
```

**★ delete 的通道结论（本轮新增，纠正旧记载）**：

```
旧记载  POST /udc/scalability-option/delete  @MultiRequestBody Long id
实况    REST 通道对本应用不可用：bare Long / {id} / {id:numeric} /
        {appId,id} / {appId,optionId,id} / {ids} 六种 body 全部
        BOOT_3000 message:null（platform 反序列化阶段就挂了，看不出真因）

        可用通道 = GraphQL udcScalabilityDeletePost
                   body {"appId": "...", "id": "<id 字符串>"}
                   → BOOT_0000 SUCCESS → 回读消失

        另 udcScalabilityBatchDeletePost 也返回 BOOT_0000（未逐个回读验证）
```

⚠ 与库内纪律一致：**同名能力可能有多条通道，REST 不通不代表能力缺失**；
先按「GraphQL 优先」（用户明示的前台协议）试，而不是死磕 REST body 形态。

### ★ 物化条件（2026-10-22 定论，原为 UNVERIFIED）

**结论：`udc_custom_ext_field` 不是「本应用 0 行 = 没生效」，而是「没有 Ext 实体就不写」。**

实测证据（全实例 69 个 schema 都有这张表，逐个 COUNT）：

```
非空 2 个：
  announcement1492794990099121396_test2   30 行
  announcement1492794990099121396_uat     30 行
空   67 个（含本应用业务库 —— 该库连表都没有，0 张表）
```

那 30 行的形态：

```json
{"app_name":"announcement1492794990099121396",
 "entity_full_name":"com.seeyon.announcement1492794990099121396.domain.entity.AnnouncementExt",
 "attribute_name":"enum03", "attribute_caption":"enum03",
 "data_type":"CTPENUM", "state":1}
```

⇒ **判据链**：

```
① entity_full_name 以 ...domain.entity.<Name>Ext 结尾 —— 是「扩展实体」(Ext)，
   不是普通业务实体
② attribute_name 形如 enum03 / bool01 / multiStr01 / multiOrg01 —— 是预留前缀 + 序号
③ data_type 含 CTPENUM / ENTITY —— 说明 Ext 实体能挂关系型字段（普通扩展实体
   「只支持 10 种基础类型」，Ext 实体不受此限）
```

所以流程是：**先有 Ext 实体（entity 的扩展），发布/构建时平台才把预留组物化成
`udc_custom_ext_field` 行**。本应用两个方案（`zxjExtOpt` 18 组 / `dsa` 0 组）
都没有对应 Ext 实体，因此 0 行是**正确行为**。

⚠ 因此**不能**把「本应用 0 行」当作扩展实体写失败的证据。
要验物化，必须先建 Ext 实体再发布——这是另一个动作，不在「设置」域内。

⚠ `udc_scalability` 全实例**只有本应用**有数据（18 组），
所以「换一个应用对照」这条路在当前环境不可用（没有第二份样本）。

## 已推翻的旧结论（留档，别再走）

```
① create 带 scalabilityDtoList（子项无 optionId）  → BOOT_1001 方案id 不能为null
② 建壳后 update 带子项（optionId 有，子项 id 缺）  → BOOT_1001 id 不能为null
③ 同上但子项 id=0                                → BOOT_0000，udc_scalability 仍 0 行
```

**REST 父级不处理子集合**。真正入口是 GraphQL `udcScalabilityPost`。

## 待删除清单

保留（有预留组样本）：
```
验收扩展实体  id=6348326125487248474   预留组 probeExt × 5
```

## 可用构造器

```python
from components.udc.setting.scalability_constraints import (
    build_scalability_option_body, build_scalability_group_body,
    validate_scalability_option_body, validate_scalability_group_body)

# 1) 方案（REST）
body = build_scalability_option_body(app_id, name="zxjExtOpt", caption="验收扩展实体")
errs = validate_scalability_option_body(body)

# 2) 预留组（GraphQL udcScalabilityPost）
gbody = build_scalability_group_body(option_id, app_id=app_id,
                                     prefix="probeExt", count=5)
gerrs = validate_scalability_group_body(gbody, option_id=option_id)
```

## 十、预留组类型 × 配置矩阵（2026-10-21 全量实测）

### 10.1 支持的 dataType（10/10 全通过）

扩展实体是**预留物理字段**，所以只支持基础类型（关联型/自定义型语义上不适用）：

```
1  STRING           ✅    2  MULTILINESTRING  ✅    3  INTEGER      ✅
4  BIGINTEGER       ✅    5  DECIMAL          ✅    6  CURRENCY     ✅
7  DATE             ✅    8  TIME             ✅    9  DATETIME     ✅
10 BOOLEAN          ✅
```

实测方案 `zxjExtOpt`（id=6348326125487248474），`udc_scalability` 共 18 条
（含先前 probeExt + sx 系列 + sy 系列），prefix/data_type/count/props 全部正确。

### 10.2 dataTypeProperties 按类型的取值

```
STRING          {"minLength":"0","maxLength":50}
MULTILINESTRING {"minLength":"0","maxLength":2000}
INTEGER         {"min":"0","max":"9999"}
BIGINTEGER      {"min":"0","max":"999999"}
DECIMAL         {"min":"0","max":"99999","decimalDigits":"2"}
CURRENCY        {"min":"0","max":"999999","decimalDigits":"2"}
DATE            {}
TIME            {}
DATETIME        {}
BOOLEAN         {}
```

⚠ 全部是**字符串化 JSON**，且里面所有值都是**字符串**（`"0"` 不是 `0`）——
这是页面实际发出的形态，照抄即可。

### 10.3 ★ 类型支持范围（2026-10-22 实测推翻旧结论）

**旧结论（错误，已作废）**：「扩展实体只支持 10 种基础类型，关联型/自定义型不适用」。

**实测：`data-type` 端点返回 18 种，全部 `validate=true`；逐个实发后 17 种可写，只有 1 种被拒。**

| 类型 | 类别 | 实测 | 说明 |
|---|---|---|---|
| STRING / MULTILINESTRING / INTEGER / BIGINTEGER / DECIMAL / CURRENCY / DATE / TIME / DATETIME / BOOLEAN | 基础 10 种 | **PASS** | 早前已实测 |
| `ENUM` | 选项集 | **PASS** | 新增：`ztd02` 落库 |
| `ATTACHMENT` | 附件 | **PASS** | 新增：`ztd03` 落库 |
| `ENTITY` | 关联实体 | **PASS** | 新增：`ztd04` 落库 |
| `DOCUMENTNUMBER` | 文号 | **PASS** | 新增：`ztd05` 落库 |
| `Serial` | 流水号 | **PASS** | 新增：`ztd06` 落库 |
| `OPINION` | 意见 | **PASS** | 新增：`ztd07` 落库 |
| `CONTENT` | 正文 | **PASS** | 新增：`ztd08` 落库 |
| **`CTPENUM`** | 平台枚举 | **FAIL** | `BOOT_1000 扩展字段不允许选择级联枚举` |

⇒ **只有 `CTPENUM` 真不适用**，而且理由不是「没有物理列形态」，是平台明确禁止**级联枚举**
（`CTPENUM` 是级联枚举，`ENUM`＝选项集不是，所以 ENUM 能过）。

DB 回读确认（`udc_test2.udc_scalability`，prefix `ztd01`–`ztd08`）：

```
ztd02 ENUM            ztd03 ATTACHMENT     ztd04 ENTITY
ztd05 DOCUMENTNUMBER  ztd06 Serial         ztd07 OPINION
ztd08 CONTENT         缺失 ztd01(CTPENUM)   ← 唯一失败
```

⚠ 旧结论的推理（「要落物理列所以不能挂关联型」）是**猜的**，不是实测。
这正是「先判能不能靠猜解决」的反例：看起来合理的架构推论，被一条 `BOOT_1000` 直接推翻。

### 10.4 页面上的配置项（用户截图对应）

扩展实体比字段集简单，右侧表单只有四项：

```
字段类型          下拉（data-type 端点候选；页面下拉实测只列基础型，
                  但接口层 17 种可写 —— 页面限制 ≠ 接口限制）
字段名称前缀      ≤20 字
预留字段数量      ≤20（页面）/ ≤50（DTO @Max）
预览              实时显示派生名 probeExt01，probeExt02，…
```

⚠ **页面下拉只列基础类型，接口却接受 17 种** —— 这是「UI 限制窄于 API」的又一例。
按接口写能成功，但页面上可能选不到；交付时要区分「接口能力」与「页面能力」。

**没有**默认值/描述/控件/脱敏这些项 —— 扩展实体只是占位，具体语义等实际用到时再配。

## 十一、可复用脚本

```bash
# 类型矩阵：10 种基础类型各建一个预留组
python tools/core/setting/scalability_type_matrix.py --run \
    --option-id <方案id> --prefix sy --count 3 \
    --i-have-write-authorization

# 只列候选类型与 props
python tools/core/setting/scalability_type_matrix.py --list
```

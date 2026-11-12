# SLICE-B2｜矩阵第 3 类 INTEGER（含值域验证）+ batch 契约原文回收

- 日期：2026-10-18
- 环境：test2（`lowcode-test2.example.com`），应用 `datamigration9000000000000000001`（数据迁移）
- 实体：`xzhExp950795V2`（entity_id=`474806313816300867`）
- 字段：**`b2IntField`**（attr id=`7734018642261617786`），`caption=b2IntField`
- 结论：**A 项 PARTIAL（类型 LIVE，值域 UNVERIFIED）／B 项 PASS（batch 原文已回收）／C 项 DONE**

---

## 一、一句话结论

| 项 | 结论 | 等级 |
|---|---|---|
| **A. 矩阵第 3 类 INTEGER** | 字段类型成功切换为 INTEGER 并落库，页面/DB/读接口/batch 原文/审计 diff **五方一致** | **LIVE（类型）** |
| A 附带的 min/max 值域 | **本片未设值域**（入口未打开；全库 3539 个 INTEGER 仅 1 个 min 有值、max 非空=0，但 710 行 max 被写成空串 ⇒ 通道存在） | **UNVERIFIED（入口层）** |
| **B. batch 契约原文** | `udcAttributeGroupOperateBatchPost` 请求（30259B）+ 响应（31590B）全部留存；**两份 EVIDENCE 已按 action 拆分**（见 §3.2） | **PASS** |
| **C. B1 文档 3 处更正** | 已全部落实（93be36d + 本次补漏 §二 操作步骤段） | **DONE** |
| **D. 文档修正轮（round 2）** | 撤回"类型UPDATE不写审计"、拆分证据错配、uniqueKey/数值键更正、值域表述降级、36键精简DTO与三档键集 | **DONE（见 §九）** |

> 不把「类型切换成功」写成「值域验证通过」。值域那一腿本片未打开入口，原因见 §五。

---

## 二、字段现状（四方一致）

### 2.1 DB 回读（LIVE）

```sql
SELECT id,name,caption,data_type,max_length,min,max,create_time,update_time
FROM udc_test2.udc_attribute WHERE id=7734018642261617786;
```

```json
[{"id": 7734018642261617786, "name": "b2IntField", "caption": "b2IntField",
  "data_type": "INTEGER", "max_length": "10", "min": "", "max": "",
  "create_time": "2026-10-18 04:08:54", "update_time": "2026-10-18 04:52:05"}]
```

- `data_type`：**STRING → INTEGER**（`update_time` 04:52:05 证明确实发生了更新，不再是初建的 STRING）
- `min` / `max` 为空字符串
- 业务字段计数：`is_system=0` → **11**（B1 的 10 + 本片 1）

### 2.2 服务端读接口（LIVE）

```
POST /service/udc/graphql?udcAttributeGroupEntityGet
{"variables":{"p":{"appId":"8704025620829192834","entityId":"474806313816300867"}}}
```

`traceId=3279181010616453308`：

```json
{"id":"7734018642261617786", "name":"b2IntField", "caption":"b2IntField",
 "dataType":"INTEGER", "min":"", "max":"", "maxLength":10,
 "columnName":"b2_int_field",
 "widgetConfig":"{\"pc\":\"InputNumber\",\"mobile\":\"InputNumber\",\"list\":true,\"detail\":true,\"quickSearch\":true}",
 "g_l_index":"8"}
```

> `widgetConfig.pc` 从 `Input` 自动变为 **`InputNumber`**，这是 INTEGER 类型的服务端派生产物，可作为类型生效的旁证。

### 2.3 页面可见（LIVE）

重载后表格第 15 行：

```
15 | b2IntField | b2IntField | 整数 | 整数：- 至 - | 0 | 请设置 | ...
```

- 类型列 = **整数**
- 阈值列 = **整数：- 至 -**（两端均为 `-`，即未设值域）

### 2.4 审计日志（LIVE，**类型变更确有记录**）

> ⚠️ 本节原写「字段类型的 UPDATE 不写 `udc_operation_log`」，**该推断是错的，已撤回**。
> 错因：我用 `domain_id = 7734018642261617786`（字段 id）查，只拿到 CREATE 那 1 条。
> 但 D31 已定：**`type=3`（批量 UPDATE）时 `domain_id` = 实体 id**，按字段 id 查必然 0 条假阴性。
> **知道规则却不按规则查，比不知道更危险**——这条错误若留着，会让后续切片主动弃用一个有效的审计腿。

**正确查法（operation_time 时间窗 + log_path 实体锚，不用 id 做水位）：**

```sql
SELECT id, action_type, domain_id, domain_caption,
       FROM_UNIXTIME(operation_time/1000) AS op_fmt, trace_id, log_path
FROM udc_test2.udc_operation_log
WHERE module=6 AND sub_module=11
  AND operation_time BETWEEN 1792267200000 AND 1792272600000   -- 2026-10-18 04:00~05:20
  AND log_path LIKE '%entity=474806313816300867%'
ORDER BY operation_time;
```

实测（2 行，两条都在）：

```
id=-1340401504201016951  type=1(CREATE)  domain_id=7734018642261617786  04:08:54.463
   log_path = entity=474806313816300867&attributeId=7734018642261617786
id=-8839657171955209174  type=3(UPDATE)  domain_id=474806313816300867  04:52:05.593   ← 实体 id
   log_path = entity=474806313816300867&attributeId=-5280541608646633310
```

两条的 `log_element` 都指向本字段：
```
["实体\\实体[小爪实验实体950795V2]\\实体字段[b2IntField]"]
```

`id=-8839657171955209174` 的 `log_details.elementRecords[].attributeRecords[]` 含 before/after diff（LIVE 原文）：

| attributeRecords.name | before | after |
|---|---|---|
| 类型 | `STRING` | `INTEGER` |
| 类型[引用对象] | `null` | `""` |
| 默认值[手输] | `""` | `"0"` |
| 阈值设置[最小长度] | `"0"` | `"null"` ← 字面字符串 |
| 阈值设置[最大长度] | `"50"` | `"10"` |
| 阈值设置[最小值] | `"null"` | `""` |
| 阈值设置[最大值] | `"null"` | `""` |

> ⚠️ **after 列是前端提交/中间态，不等于落库值。判落库一律以 DB + 响应端为准。**
> 本例 `阈值设置[最小长度]` 的 after 写的是字面 `"null"`，但 DB 实测 `min_length='0'`；
> INTEGER 全库 3539 行的 `min_length` **恒为 '0'（3539/3539，唯一取值）**；`min_length='null'` 字面 **0 行**、`max_length='null'` 字面 **0 行**。
> 机制与 §2.4.2 的 maxLength 同构：**payload 省略该键 → 服务端按类型默认补 → 落库**。那个 `"null"` 是前端中间态，不是落库字面。
> （响应端 `minLength=0`(int) / `maxLength=10`(int)，与 DB 一致，是可靠的第二腿。）

**正确表述（替换原错误结论）：**

> `udc_operation_log` **记录**字段类型变更（`action_type=3`，`domain_id`=**实体 id**，`log_element` 指向字段，
> `log_details.elementRecords[].attributeRecords[]` 含 before/after diff）。
> **不能用 `domain_id`=字段 id 查**（0/1 条假阴性）。用 `log_element LIKE '%字段名%'` 或
> `operation_time` 时间窗 + `log_path LIKE '%entity=<实体id>%'`。
> `id` 是 bigint 有符号、正负两支序列（id 序与 operation_time 序一致率仅 50.41%），**禁止用 id 做区间/水位/排序**。

### 2.4.1 `log_path.attributeId` 不等于本字段 id（一个会误判的坑，LIVE）

type=3 那条 `log_path` 里 `attributeId=-5280541608646633310`，而 b2IntField 的 id 是 `7734018642261617786`。
查库核实：**`-5280541608646633310` 是同一实体内另一个字段的 id（`name=createTime`）**。

⇒ 结论：**type=3 批量 UPDATE 的 `log_path.attributeId` 不能用来判定"这条属于哪个字段"**（它可能装的是批次里任意一个字段 id）。
判定字段归属必须用 `log_element LIKE '%实体字段[<字段名>]%'`，或读 `log_details` 里的 `attributeRecords`。
（这条与 D19/D31 互补：`domain_id` 随 action_type 分叉、`log_path.attributeId` 在 type=3 下不可靠，二者都不能单独当字段归属证据。）

### 2.4.2 maxLength 50→10 的来源已闭合

审计 diff 记 `阈值设置[最大长度] 50 → 10`，而请求 payload 里**没有 maxLength 键**。
不是"两者不同源"，而是：**整数类型的 max_length 平台默认值是 10**。
- 全库 INTEGER 3539 行里 `max_length='10'` 占 **2921（82.5%）** ⇒ 10 是类型默认
- 04:52:05 那次 UPDATE 的 DTO 只有 36 键，`maxLength` 不在其中（连 minLength/orderNo/valueScopeExpression 等 40 键一起省略）
- 响应端 77 键里 `maxLength` 被服务端补成 **10**

正确写法：「maxLength=10 = INTEGER 平台默认（LIVE，82.5% 分布支撑）；类型变更时前端省略该键；服务端补默认值 —— 补值代码路径 STATIC 未定位」。

---

## 三、B 项：batch 契约原文（本片核心交付，回收 B1 豁免）

### 3.1 捕获方式（常驻监听，修正 B1 丢体根因）

```javascript
// 关键顺序：监听先开，再导航
await send('Network.enable', { maxTotalBufferSize: 100000000, maxResourceBufferSize: 50000000 });
await send('Page.enable');
await send('Runtime.enable');
// ... 之后才 Page.navigate

// 事件驱动，不在脚本收尾时回头扫 events 数组：
ws.onmessage = async e => {
  if (m === 'Network.requestWillBeSent') { /* 立即落盘 postData */ }
  if (m === 'Network.responseReceived')  { /* 记 status */ }
  if (m === 'Network.loadingFinished')    { /* ★ 立即 getResponseBody 落盘 */ }
};
```

**这就是 B1 丢失响应体的根因修正**：B1 是「点保存 → sleep → 扫 events 数组」，
保存请求落在脚本结束的时序边沿外；本片改为 `loadingFinished` 事件里**即时**取体。

### 3.2 捕获结果

| 项 | 值 |
|---|---|
| 请求 URL | `POST /service/udc/graphql?udcAttributeGroupOperateBatchPost` |
| 请求体长度 | **30259** 字节 |
| 响应状态 | **HTTP 200** |
| 响应体长度 | **31590** 字节 |
| 响应 traceId | `17922703253568753914` |
| 响应 code | `BOOT_0000` / status=0 |
| 原始 jsonl | `docs/audit/artifacts/scratch-migrated/slice-b2/b2_v10_capture.jsonl`（两条：request + complete） |

**★ 证据文件必须按 action 分开（原文档把两份混了，已更正）：**

| 文件 | 装的是什么 | 关键字段 |
|---|---|---|
| `EVIDENCE-batch-contract-live.json` | **04:08:54 的 CREATE 批次**（B1 豁免欠的原文）<br>postDataLen=**30003**，`_meta.action="ADD/CREATE"` | `params0[1].attributeDtoList[7]` = `actionType=ADD` / `dataType=STRING` / `id=null` / **26 键**；其余 14 条 UPDATE 76 键 |
| `EVIDENCE-batch-update-live.json` | **04:52:05 的 UPDATE 批次**（本片类型变更）<br>postDataLen=**30259**，`_meta.action="UPDATE"` | 15 条全 UPDATE：14 条 76 键 + **b2IntField 那条 36 键**；同时装请求端与响应端全文 |

> 原 §17 写「请求 30259B → 落盘 EVIDENCE-batch-contract-live.json」是**错的**：那份 json 里 postDataLen=30003、
> b2IntField 是 `actionType=ADD`、`dataType=STRING` —— 是 04:08:54 的 CREATE。已按上表拆分，不重抓、只重组。

### 3.3 契约形状（LIVE 提取，非反编译）

**顶层：**

```json
{"query": "mutation graphqlLoader ($params0: udcAttributeGroupOperateBatchPostInputBody) { data0: udcAttributeGroupOperateBatchPost(body: $params0) { code data { content } message status } }",
 "variables": {"params0": [<AttributeGroupDto>, ...]}}
```

- `variables.params0` 是**属性组数组**（整表提交，本片 2 组：`系统` + `ex_defGroup`）
- **一次提交整表**：既有字段也带 `actionType:"UPDATE"`，不是只发变更项

**属性组（AttributeGroupDto）12 个键：**

```
appId, caption, entityId, guid, id, orderNo, preset, publishState,
virtual, attributeDtoList, actionType, uniqueKey
```

**属性 DTO 76 个键（完整列表）：**

```
relationCtpEnum, enableSensitiveWordCheck, enableOpenApiEncrypt, attributeFullName,
attributeGroup, attributeGroupId, auditLog, appId, actionType, calculate, caption,
createTime, dataFormat, dataI18n, dataType, dataTypeDisplayName, decimalDigits,
defaultValue, defaultValueExpressionDesignData, defaultValueExpressionRuntimeData,
defaultValueIsChange, defaultValueSystemVariable, description, desensitization,
edit, enableDesensitization, enableEncryption, encryption, entityId, existDto,
expressionDesignData, expressionRuntimeData, guid, hidden, id, inCondition,
inDataMapping, max, maxLength, min, minLength, multiSelect, name, notNull, orderNo,
parentEnumAttributeId, pattern, patternMessage, permission, publishState, relationApp,
relationCode, relationEntity, relationEntityCategory, relationEntityName, relationType,
relationStarter, searchable, serialNumberCode, serialNumberGuid, serialNumberName,
sourceId, sourceType, system, uniqueness, updateTime, defaultValueCaption,
valueScopeExpression, widgetConfig, columnName, useSnapshot, g_l_index, key,
uniqueKey, index, parentKey
```

**新增字段（`actionType:"ADD"`）实测形状（B2 首次建字段时捕获，id 不存在）：**

```json
{"uniqueKey":"486584055488826661", "attributeGroupId":"", "caption":"b2IntField",
 "entityId":"474806313816300867", "hidden":false, "createTime":"1792267710762",
 "name":"b2IntField", "dataType":"STRING", "edit":true, "notNull":false,
 "uniqueness":false, "defaultValue":"", "minLength":0, "maxLength":50,
 "columnName":"b2_int_field", "useSnapshot":false, "enableEncryption":false,
 "enableDesensitization":false, "auditLog":false, "searchable":false,
 "publishState":"UNPUBLISH", "defaultValueIsChange":true,
 "widgetConfig":"{\"pc\":\"Input\",\"mobile\":\"Input\",\"list\":true,\"detail\":true,\"quickSearch\":true}",
 "enableOpenApiEncrypt":false, "appId":"8704025620829192834", "actionType":"ADD"}
```

**类型变更（`actionType:"UPDATE"`，本次 04:52 那次）：**

```json
{"actionType":"UPDATE", "dataType":"INTEGER", "min":"", "max":"",
 "minLength":null, "maxLength":null, "columnName":"",
 "widgetConfig":"{\"pc\":\"InputNumber\",\"mobile\":\"InputNumber\",\"list\":true,\"detail\":true,\"quickSearch\":true}"}
```

**三档键集（D39，全部为请求端形态，已用两份 capture 逐条统计核对）**

| 形态 | 键数 | 实测条数 | 出现条件 |
|---|---|---|---|
| ADD（新建，无 id） | **26** | CREATE 批次 1 条 | 新建字段（走表单默认表 `f[type]`，无任何身份键） |
| UPDATE-精简 | **36** | UPDATE 批次 1 条（就是 b2IntField 类型变更那条） | **该字段本次走"重建"分支**：按当前 dataType 模板重拼 + 补身份键（触发器 UNVERIFIED，见 §5） |
| UPDATE-全量 | **76** | CREATE 14 条 + UPDATE 14 条 | **读接口对象原样回显直传**（77−5+4，等式精确） |
| （响应端） | **77** | UPDATE 批次 1 条 | 服务端补齐后返回 |

> **不要写成「76 和 36 是两种档位」** —— 真实机制是「**这条 DTO 从哪来**」：
> **76 = 读接口对象原样回传**（读回 77 键 → 删 5 个纯服务端键 → 加 4 个前端索引键 → 其余一个不改直传）；
> **36 = 按当前 dataType 模板重建**（`core(19) ∪ E[dataType](17) ∪ 身份关系键(8)`，代数式 0 残差）。
> 所以 40 键差额只是**重建方式的副产品**，不是设计意图。详见 `B4-KEYCOUNT-ORIGIN.md`。
>
> ~~旧表述：省略的 40 键"全是跟着类型走的派生键，类型一变全部失效"~~ → **本片更正**：
> 40 键只有 **8 键**属 `E[String]−E[Integer]`（maxLength/minLength/patternMessage/dataI18n/
> desensitization/enableDesensitization/enableEncryption/encryption）；另 **18 键是服务端只读回填**
> （orderNo/updateTime/attributeGroupId/sourceId/serialNumber*/parentEnumAttributeId/relationType…）、
> **8 键是前端索引**（g_l_index/index/key/parentKey/inCondition/inDataMapping/hidden/description）、
> **1 键**是 `valueScopeExpression`。这些跟类型无关，只是"重建时不带"。
>
> **限制**：只有 STRING→INTEGER **一个样本**，且该样本同时是"唯一类型变化"+"唯一被编辑字段"，
> 三因素重合 ⇒ **触发条件（哪个变量把它送进重建分支）UNVERIFIED**，不能推成通用规则。

**服务端补齐实测（同 traceId 请求→响应对照，LIVE）**

| 项 | 请求(36键) | 响应(77键) | 说明 |
|---|---|---|---|
| `maxLength` | 缺 | **10** | INTEGER 类型默认（全库 82.5% 为 10） |
| `minLength` | 缺 | **0** | |
| `orderNo` | 缺 | **17** | 补的是**库里旧值**，不是硬编码默认 |
| `columnName` | `""` | `b2_int_field` | 传空串 = 让服务端按 name 重算，不是省略/缺陷 |
| `decimalDigits` | 缺 | **0** | |
| `valueScopeExpression` | 缺 | **null** | 省略 ⇒ 服务端补旧值 null（不是 `""`） |
| `actionType` | `"UPDATE"` | **null** | 服务端不回传 |
| 新增键合计 | — | **41 个** | 见 `EVIDENCE-batch-update-live.json` → `server_side_reconciliation` |

**关键协议要点（原 5 条中 2 条已按实测更正）：**

1. `actionType`：`ADD`（新建，无 id）/ `UPDATE`（既有，带 id）
2. ~~`uniqueKey` 是前端生成的 18 位随机串~~ → **更正**：实测 **15/15 条 `uniqueKey` === `id`**（字段 id 的字符串镜像），**不是随机串**。
   唯一例外是 ADD 那条约 18 位数字（`486584055488826661`），因为 ADD 时还没有 id，前端先占位，落库后 id 与之不同。
3. `columnName` 前端下划线化（`b2IntField` → `b2_int_field`），但**类型变更时传空串**（= 请服务端按 name 重算）
4. `widgetConfig` 是 **JSON 字符串**（非对象），随类型变化：`Input` → `InputNumber`
5. `publishState` 传字符串 `"UNPUBLISH"`（不是数字）
6. ~~数值键传字符串~~ → **更正（round3 定稿，30 条 DTO 全量实测）**：
   - **恒为 str**：`id`(29/29 有值)、`entityId`(30/30)、`appId`(30/30)、`uniqueKey`(30/30)、`dataType`、`actionType`
   - **恒为 int**：`createTime`(29/30)、`updateTime`(28/28)、`maxLength`(29/29)、`minLength`(29/29)、`orderNo`(28/28)
   - **唯一例外**：`createTime` 在**ADD 那一条**传 **str**（`"1792267710762"`），与 `uniqueKey` 同为前端占位形态（ADD 时后端还没发号）
   - **不要**写「createTime/updateTime 全是 str」——updateTime 是 int，createTime 只有 ADD 是 str
7. `defaultValue` **三态**（30 条 DTO 实测）：`null` **22** / `str` **7** / `int` **1**
   - `null` 22：包在没填默认值的 UPDATE DTO 上（`defaultValue: null`）
   - `str` 7：`expText='"默认文本"'`、`expFlag='false'`、`B1wenbenyanzheng=''`、`b2IntField(ADD)=''` …
   - `int` 1：`b2IntField(UPDATE)=0`（类型变更那次，服务端/前端的数值化）
   ⇒ 默认值不传"统一类型"，**三态并存**，任何"恒为 X"的说法都会错。

**ADD DTO 26 键全清单（LIVE，CREATE 那次实测）：**
```
actionType, appId, attributeGroupId, auditLog, caption, columnName, createTime, dataType,
defaultValue, defaultValueIsChange, edit, enableDesensitization, enableEncryption,
enableOpenApiEncrypt, entityId, hidden, maxLength, minLength, name, notNull, publishState,
searchable, uniqueKey, uniqueness, useSnapshot, widgetConfig
```
> ADD **缺** `id/guid/orderNo/index/key/min/max/decimalDigits/valueScopeExpression/pattern/...`。
> 但**不能据此认为「ADD 不能带值域」**：全库近期页面建的 `税率统一调整`（id=-25970819265408883）CREATE 日志 25 项，
> 含 `阈值设置[最小值] -→0`、`[最大值] -→1`、`[最大长度] -→20`、`小数位数 -→2`，**一次性带齐**。
> ⇒ CREATE 一次就能带值域，关键是前端把值写进 DTO（本次 b2IntField 没填，所以只有 26 个基础键）。

---

## 四、A 项：类型切换的页面操作路径（B2 探索结论，可复用）

**这是本片最有价值的操作知识**——字段类型**不是**在表格只读 tag 上直接改，也不是新建时默认值。

### 4.1 正确路径

1. 定位目标行的类型单元格（td3）
2. **双击**该单元格里的 `[tabindex]` 元素（`.f9354872`）
   → 单元格从 `ant-tag`（只读）**变为 `ant-select` combobox**
3. 点 `.ant-select-selector` 展开下拉
4. **下拉渲染在离屏容器**（`.ant-select-item-option-content` 坐标约 `-9268,-9239`）
   → **不能靠坐标点击**，必须对 `.ant-select-item-option` 元素直接 `dispatchEvent`
5. 选中后按 `Enter` 提交
6. 阈值列自动从 `长度：0 至 50` 变为 `整数：- 至 -`

### 4.2 失败的尝试（记录以免后人重踩）

| 尝试 | 结果 |
|---|---|
| 直接点类型 tag | 无反应（只读展示） |
| 新建行找 combobox | 新建行类型也是只读 tag，无 combobox |
| 点「更多」菜单 | 坐标随滚动漂移，多次误命中分页器/侧边导航 |
| 对 `.threshold-box` 双击（JS dispatchEvent） | 只触发 tooltip（`ant-tooltip-open`），无编辑控件 |
| 对 `.threshold-box` 真实鼠标双击 | 同上，仍只有 tooltip |
| 阈值单元格内找 input | `inputCount: 0` |

### 4.3 ★ 更正：我曾写「已保存行的类型是只读 tag」——**这句是错的**

`b2_v4.js` L3 注释原写：「类型必须在新建未保存行时改（已保存行的类型是只读 tag）」。
但后来 `b2_v7.log [3d]` 实测：**已保存行的类型也能改成 INTEGER 并在 UI 上生效**（04:52:05 已落库）。

⇒ 这是**错误推断，不是平台事实**。正确表述：

- 类型 tag **不是只读展示**，双击其 `[tabindex]` 元素即可进入编辑态（第 4.1 节路径对已保存行同样成立）
- 之前失败的真正原因不是"只读"，而是**下拉选项节点渲染在视口外**：
  `optRect x=-9294 / y=-9351`（`.ant-select-item-option-content`）⇒ 按坐标 dispatchEvent 点不到
- 正解：**focus combobox → 输入过滤（如"整数"）→ Enter 提交**（b2_v7 [3d] 已验证成功）
- STATIC 佐证：dataType 选择器是 TreeSelect（模块 54019），按需挂载未激活节点到视口外，与观察一致

**这条更正有一个副作用（对后续切片很重要）**：
既然已保存行也能改类型，「新建 vs 修改」**不能靠自述区分**，必须靠审计日志 `action_type` 区分：
`action_type=1`=CREATE / `action_type=3`=UPDATE。见 §2.4。

---

## 五、值域 min/max 为什么做不出来（UNVERIFIED 的诚实说明）

**定性：入口层未打开，不是能力层不支持。**（原写"平台没有入口"过于绝对，已降级）

四条依据：

1. **本实体已有 INTEGER 字段同样无值域**：`expNum`（INTEGER）`min=**NULL**`、`max=**NULL**`
   （⚠️ 注意与本字段区分：本字段 `b2IntField` 是 `min=''`/`max=''` —— **空串不是 NULL**，两者不可说成"完全一致"，见 D36）
2. **全库分布（LIVE 复核 2026-10-18 11:0x）**：`data_type='INTEGER'` 共 **3539** 行
   ```
   min 非空 = 1      max 非空 = 0
   min = ''  = 709   max = ''  = 710
   min IS NULL = 2829  max IS NULL = 2829
   value_scope_expression 非空 = 1（唯一那条是 "共管账户ID"：min='0', max='', vse='{"min":"","max":""}'）
   ```
   ⇒ 「max 非空 = 0」是真的，但**710 行 max 被写成空串**、**vse 被写过**（口径见下）⇒ 值域通道**存在过写入**，不是能力缺失。

   **★ vse 精确分布（round3 更正，此前写「56 行 vse 被写过」口径错）**：
   ```
   value_scope_expression  NULL = 3483
                           空串 '' = 55
                           非空 = 1   ← 唯一先例：共管账户ID  vse='{"min":"","max":""}'
   合计 = 3539
   ```
   ⇒ **「字段被初始化」≠「值域被配过」**：那 55 行写的是空串 `''`，等于没配；真正有内容的只有 **1** 行。
   ⇒ 所以正确说法是：**非空 vse = 1 例**（不是 56 例）。56 = 非空 1 + 空串 55，是"被写过字段"的粗口径，不能当"配过值域"用。
3. **页面无可用入口（本片实测）**：阈值单元格 `.threshold-box` 双击（JS dispatchEvent + CDP 真实鼠标都试）只出 tooltip，`inputCount=0`；
   单元格 HTML 恒为 `<div class="threshold-box" tabindex="1"><div class="threshold-seeing">整数：- 至 -</div></div>`
4. **batch 原文里 min/max 传空串**：类型变成 INTEGER 后的那次 UPDATE，`min:""`, `max:""`
   —— 而审计 diff 显示 `阈值设置[最小值]` 由 `"null"` → `""`，即**前端显式传了空串**。

**结论（正确口径）**：
- INTEGER 值域在设计器表格视图下**未找到可用入口**（本片试过 4 种路径，见 §4.2），属 **UNVERIFIED（入口层）**。
- 全库存在 1 例成功写入（共管账户ID：`min='0'` + `vse='{"min":"","max":""}'` 同时非空）⇒ **能力层存在，只是入口未打开**。
- **不能写"平台不支持值域"**，也不能写"值域验证通过"。正确表述：**本片未设值域，只验 INTEGER 类型本身**。
- 若后续必须设值域：需要先定位那个唯一成功先例的入口（很可能是字段详情抽屉而非表格行内），
  或按 HANDOFF 授权的页面路径再试；**不为凑交付而绕 REST**（HANDOFF 硬要求「构建必须页面点击」）。

### 5.1 值域双载体（必须三处齐，只查 min/max 会误判）

bundle（`src_redux_store_ts.14dc061e.js` 模块 81578/27932）值域组件 `valueType=["CONSTANT","EXPRESSION"]`：

- **CONSTANT**：值写 `udc_attribute.min` / `.max`，同时 `value_scope_expression` 对应键置 `""`
- **EXPRESSION**：值写 `value_scope_expression`，同时 `min`/`.max` 置 `""`

LIVE 佐证：`共管账户ID`(INTEGER) `min="0"`、`max=""`、`vse='{"min":"","max":""}'` —— 正是 CONSTANT 形态。

**判定三件套（缺一不可）**：①页面配置面板两格显示所填值 ②DB `min`/`max` 有值 **且** `vse` 对应键为空串 ③读接口 `udcAttributeGroupEntityGet` 回读与 DB 一致。

**另注（防反向误判）**：`DATA_TYPE_VALUE_RANGE.Integer = {-2147483648, 2147483647}` 是**类型级边界**，
只用于校验"填的值不能超出类型范围"（校验器 `f()` 里 `case "min": d<r && push("最小值不能小于"+r)`），**不落库**。
⇒ 新建 INTEGER 后 min/max 为 null/空串是**正常默认**，不能写成"值域验证通过"。

### 5.2 本片 b2IntField 值域的实际状态（明确记账）

| 项 | 值 | 结论 |
|---|---|---|
| `min` | `''`（空串） | 未设值域 |
| `max` | `''`（空串） | 未设值域 |
| `value_scope_expression` | `NULL` | 未设值域 |
| 走 CONSTANT 还是 EXPRESSION | **都不是**（两者皆空） | — |

⇒ **本片未设值域，只验 INTEGER 类型本身。** 不得表述为"值域验证通过"，也不得表述为"平台不支持值域"。

---

## 六、C 项：B1 文档 3 处更正（已落实）

| # | 要求 | 状态 | commit |
|---|---|---|---|
| ① | 删除/降级「保存成功」作为因果证据 | ✅ 已改（§三 + §二 操作步骤段新增定性说明） | 93be36d + 本片补漏 |
| ② | `publish_state=1` 更正为 UNPUBLISH 且零区分度 | ✅ 已改（§五 加语义更正块） | 93be36d |
| ③ | batch 归因改为「v9 没执行到 [7]」 | ✅ 已改（§三 ③ 归因撤回） | 93be36d |

本次补漏：`SLICE-B1-STRING-live.md` §二「操作步骤」第 6 步原写「保存成功提示出现」，
已改为「保存是否由此点击触发 = UNVERIFIED」，并在该节加定性说明块——**操作步骤是复现路径，不是因果证明**。

---

## 七、边界与未达成项

- **A 项值域 min/max：UNVERIFIED（入口层）**。原因见 §五。**本片未设值域，只验 INTEGER 类型本身。**
  矩阵记账建议：INTEGER 该格记「类型矩阵 LIVE 通过；值域子项入口未打开（保留 UNVERIFIED）」。
- **审计日志确实记录类型变更**（见 §2.4，此前错误推断已撤回）。
  后续切片可用 `action_type=3` + `log_element LIKE '%字段名%'` + `log_details.elementRecords[].attributeRecords[]` 的 before/after diff 作为类型变更证据。
  禁用单锚：`domain_id` **随 action_type 分叉** —— `type=1`(CREATE) → **字段 id**（本轮实测 1 行 CREATE 证实：domain_id=7734018642261617786）；
  `type=3`(批量 UPDATE) → **实体 id**（实测：domain_id=474806313816300867）。
  **禁止用 `domain_id=字段id` 查 type=3 记录**（0/1 条假阴性）；但**也不能写"domain_id 任何值都不可用"**——type=1 时它就是字段 id，是可用的。
  唯一可靠锚 = `log_element LIKE '%实体字段[<字段名>]%'` 或 `operation_time` 时间窗 + `module=6 AND sub_module=11`；
  `log_path.attributeId` 在 type=3 下也不可靠（见 §2.4.1）。
- **b2IntField 现状与用途（必须写明，防下个切片误用）**：
  已于 **04:52:05 由 STRING 改为 INTEGER**，**D26 的「STRING 反例」已失效**。
  现状态：`data_type=INTEGER` / `max_length=10` / `min=''` / `max=''` / `vse=NULL` / `order_no=17` / `db_column_name=b2_int_field`。
  **它不是反例，也不能充当第 3 类的值域闭环证据（无值域）。留库仅供后续值域实验复用。** 删除需另行授权。
- 本片误操作记录：多次坐标点击误命中侧边导航/分页器，导致页面切到设计日志 tab；
  **未造成数据损坏**（DB 校验：业务字段 11 / 系统 8 / 总 19、b2IntField 仅 1 行、DISTINCT name=19、DISTINCT caption=19、无重复）。
- 0 次 REST 写调用（batch 是由页面点击真实触发的）；本地 commit 禁 push 已遵守。

---

## 八、复现

```bash
cd <SEEYON_AGENT_ROOT>
# CDP 9222 + cookie 注入后：
node docs/audit/artifacts/scratch-migrated/slice-b2/b2_v10.js    # ★ 一次跑完：双击类型→选整数→保存→抓 batch
# DB / 读接口 / 审计日志回读见 §二 SQL 与 curl
```

**capture / evidence 文件**：
- `docs/audit/artifacts/scratch-migrated/slice-b2/b2_network_capture.jsonl` — 04:08:54 CREATE 原始（1 行，postDataLen=30003）
- `docs/audit/artifacts/scratch-migrated/slice-b2/b2_v10_capture.jsonl` — 04:52:05 UPDATE 原始（2 行：request + complete，postDataLen=30259 / respLen=31590）
- `docs/audit/entity-field-matrix/EVIDENCE-batch-contract-live.json` — CREATE 批次结构化 + 形状分析（`_meta.action="ADD/CREATE"`）
- `docs/audit/entity-field-matrix/EVIDENCE-batch-update-live.json` — UPDATE 批次结构化 + 请求/响应全文 + `server_side_reconciliation`（`_meta.action="UPDATE"`）

**本轮文档修正的取证脚本（只读）**：
- `docs/audit/artifacts/scratch-migrated/slice-b3/b3_db_probe2.py`（b2IntField 现值 + 字段计数）
- `docs/audit/artifacts/scratch-migrated/slice-b3/b3_audit_probe.py`（审计窗口 + INTEGER 值域分布）
- `docs/audit/artifacts/scratch-migrated/slice-b3/b3_audit_details.py`（type=3 那条的 before/after diff 原文）
- `docs/audit/artifacts/scratch-migrated/slice-b3/b3_vse_probe.py`（vse 细分统计）
- `docs/audit/artifacts/scratch-migrated/slice-b3/b3_logpath_probe.py`（log_path.attributeId 归属核实）
- 日志：`docs/audit/artifacts/scratch-migrated/slice-b3/*.log`

**日志**：`docs/audit/artifacts/scratch-migrated/slice-b2/b2_v1.log` ~ `b2_v11.log`（完整探索轨迹含失败轮次）

---

## 九、文档修正轮（round 2，2026-10-18 11:0x）——逐条对账

来源：main DECISION（20261017T211108Z §二~§八）+ auditor VERDICT / REVIEW_FEEDBACK。**不改判定，纯更正 + 补证**。

| # | 要求 | 落点 | 状态 |
|---|---|---|---|
| 1 | **撤回「字段类型 UPDATE 不写 udc_operation_log」**（这是污染链，会让下个切片弃用有效审计腿） | §2.4 整节重写 + §七 | ✅ 已撤回并给出正确查法与 LIVE 原文 |
| 2 | maxLength 表述：不是"不同源"，是 **INTEGER 平台默认 10（82.5%）+ 前端省略 + 服务端补** | §2.4.2 | ✅ |
| 3 | **证据错配拆分**：`EVIDENCE-batch-contract-live.json` 保留为 CREATE（标 `_meta.action="ADD/CREATE"`）；另建 `EVIDENCE-batch-update-live.json` 装 30259B 那份 | §3.2 + §八 | ✅ 两份文件已落盘并各自标 action |
| 4 | `uniqueKey` 更正：**恒等于 id**（15/15 实测），不是随机串 | §3.3 要点 2 | ✅ |
| 5 | 「数值键传字符串」更正：**混合类型**（详见 §3.3 要点 6 的 round3 定稿：恒 str=id/entityId/appId/uniqueKey；恒 int=createTime(除 ADD)/updateTime/maxLength/minLength/orderNo） | §3.3 要点 6 | ✅ |
| 6 | **值域表述降级**：不是"平台不支持"，而是"入口未打开"（3539 INTEGER：max 非空=0，但 max=''=710、vse 非空=1） | §五 | ✅ 并加 §5.1 双载体 + §5.2 本片实际状态 |
| 7 | **补 §七 待查说明**：36 键精简 DTO 的成因 | §3.3 三档键集 | ✅ 归因为"派生键在类型变更时被省略"，并限定只有 STRING→INTEGER 一个样本 |
| 8 | **边界申报**：b2IntField 已非 STRING 反例，不能充当值域闭环证据 | §七 | ✅ |
| 9 | auditor 新增：`log_path.attributeId` 在 type=3 下不可靠（实测装的是另一字段 createTime 的 id） | §2.4.1 | ✅ 本轮新查证 |
| 10 | 撤回「已保存行类型只读」错误推断（D23） | §4.3 | ✅ |

**本轮新增的原始取证（全部只读，5 个脚本 + 日志在 `docs/audit/artifacts/scratch-migrated/slice-b3/`）**：
- 审计窗口查得 2 条记录（type=1 CREATE + type=3 UPDATE），并取到 type=3 的 `attributeRecords` before/after 全量 diff
- `log_path.attributeId=-5280541608646633310` 归属核实 → 查库为同实体 `createTime` 字段，**不是** b2IntField
- INTEGER 值域分布细分（min/max/vse 各档计数）
- b2IntField 现值复核：`INTEGER / max_length=10 / min='' / max='' / vse=NULL / order_no=17`
- 字段计数复核：业务 11 / 系统 8 / 总 19

**本轮没有做的事**：0 次页面操作、0 次 REST 调用、0 次写库、0 次浏览器操作。B2 判定不变（PARTIAL-A）。

---

## 十、round3 收口（2026-10-18 11:5x）—— 5 条修正 + 闸门升级

来源：main HANDOFF（20261018T034622Z）+ auditor REVIEW_FEEDBACK-AC707DB-ACK。**仍是文档/证据修正，无新 LIVE 抓取**。

### 10.1 五条修正（逐条落点）

| # | 修正 | 落点 | 实证来源 |
|---|---|---|---|
| ① | **createTime 通用契约**：id/entityId/appId/uniqueKey/dataType/actionType 恒 str；createTime(29/30)/updateTime(28/28)/maxLength(29/29)/minLength(29/29)/orderNo(28/28) 恒 int；唯一例外 = **ADD 那条 createTime 传 str** | §3.3 要点 6 | 30 条 DTO `isinstance` 实测 |
| ② | **defaultValue 三态**：None **22** / str **7** / int **1** | §3.3 要点 7 | 同上 |
| ③ | **vse 数字改正**：非空串 **1**（唯一先例）/ 空串 **55** / NULL **3483**；「字段被初始化」≠「值域被配过」 | §五 分布段 | DB 全库 3539 行三态统计 |
| ④ | **domain_id 补分叉前提**：type=1→字段id（本轮 1 行 CREATE 实测证实）/ type=3→实体id；唯一可靠锚=log_element 或 时间窗+module+sub_module；同时明确**否定**"任何值都不可用" | §七 | 审计表实测 |
| ⑤ | **§2.4 审计表下加**：after 列是前端提交/中间态，判落库一律以 DB+响应端为准（`min_length` after=`"null"` 而 DB=`'0'`，INTEGER 全库 3539/3539 恒 '0'；`'null'` 字面 0 行） | §2.4 表格下引注 | DB 实测 + 响应端 minLength=0 |

### 10.2 闸门升级（词面 grep → EVIDENCE 反解 + 负向 + 分叉）

`tools/audit/gate_b2_docfix.py` 重写，65 条断言，三类：

1. **从 EVIDENCE 反解（不 grep 正文数字）**：A0-A8 —— DTO 总数、各键 `isinstance` 类型、createTime 分叉、defaultValue 三态计数、uniqueKey==id 29/29、三档键数、响应端 maxLength/minLength/orderNo/vse、补键 41、请求端缺 maxLength/minLength/vse
2. **负向断言**：'56 行 vse 被写过' 必须不存在；旧错句「id/entityId/appId/createTime 是 str」必须不存在；裸句「禁用 domain_id=字段id；」必须不存在；「非空 vse = 56」必须不存在
3. **分叉断言**：domain_id 段落必须同时含 `action_type` + `字段 id` + `实体 id` + `type=1`/`type=3`，且必须含「不能写"任何值都不可用"」

**负向注入验证（8 次，全部 exit=1 精确命中，还原逐字节一致）**

| # | 注入 | 结果 |
|---|---|---|
| N1 | updateTime 挪到 str 组 | exit=1，命中 2 条（B1a + B1d） |
| N2 | 非空 vse 1 → 56 | exit=1，命中 2 条（B3f + B3g） |
| N3 | domain_id 改成"永不使用任何值" | exit=1，命中 B4f |
| N4 | defaultValue 三态数字改错（str 7→8） | exit=1，命中 B2a |
| N5 | after 声明改反（"after 即落库值"） | exit=1，命中 B5a |
| N6 | vse NULL 3483 → 3500 | exit=1，命中 B3a |
| N7 | 补键 41 → 40 | exit=1，命中 A7e |
| N8 | 响应 maxLength 10 → 50 | exit=1，命中 A7a |

> N2 是第二轮才补上的：首轮注入「非空 vse = 56」时闸门仍 PASS（因为分布块里「非空 = 1」还在），说明**只靠单点断言会被同义改写绕过**；补 B3f/B3g 两条负向+正口径绑定后才命中。这条教训比断言本身重要。

### 10.3 本轮未做的事

0 页面操作 / 0 REST / 0 写库。只读脚本：`docs/audit/artifacts/scratch-migrated/slice-b3/round3_db_verify.py`（+ `.log`）。
B2 判定不变 **PARTIAL-A**；值域腿仍 **UNVERIFIED（入口层）**，未升格。

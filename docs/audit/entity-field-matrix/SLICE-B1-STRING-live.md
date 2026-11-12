# SLICE-B1｜实体字段类型矩阵第 2 类：STRING —— 判定 **PARTIAL**

- 日期：2026-10-18
- 环境：test2（`lowcode-test2.example.com`），目标应用 `datamigration9000000000000000001`（数据迁移）
- 实体：`xzhExp950795V2`（小爪实验实体950795V2，entity_id=`474806313816300867`）
- 新增字段：**`B1文本验证` / `B1wenbenyanzheng` / `STRING` / `max_length=50`**（attr id=1021739412060058618）
- 执行方式：设计器页面交互构建（CDP Input 域真实事件），REST 只用于读面取证
- **结论等级（auditor VERDICT 定级）**：
  - **写链结果 = LIVE**（DB 落库 + `udc_operation_log` CREATE 审计 + `udcAttributeGroupEntityGet` 服务端回读，三方独立）
  - **「页面点击 → 保存成功」因果链 = UNVERIFIED**（保存点击的日志行缺失）
  - **`udcAttributeGroupOperateBatchPost` 请求原文 = UNVERIFIED**（ROUTE 要求的「请求证据」这一腿空缺）
  - → 按 ROUTE L12 完成标准（页面步骤 + 请求证据 + DB 回读），**请求证据缺失，故整体 PARTIAL**；
    豁免权在 main，本侧不自我豁免。

---

## 一、一句话结论

STRING 类型字段通过设计器页面点击（添加→填名→保存）完整走通设计态写链：
设计态元数据落库（`udc_attribute` 新增 1 行，业务字段 9→10），页面重载后字段可见。
物理表（`xzhexp950_m1719416608666233204`）尚无 `b1wenbenyanzheng` 列 —— 属预期，
物理列由应用构建/发布（沙箱流水线）生成，不在本切片验收口径内。

---

## 二、操作步骤（真实页面交互，全部 CDP Input 域真实事件）

1. 打开实体设计器：`https://lowcode-test2.example.com/main/child-frame/udc/app-design/entity?appId=9000000000000000002`
   > 路径要点：必须带 `/main/child-frame/udc/` 前缀；`/main/app-design/entity` 会得到「页面找不到了」。
2. 点击字段工具栏「添加」按钮（`button.ant-btn-link`，坐标 386,118）→ 表格新增第 14 行（编辑态，默认 caption=字段1 / 自动 name=ziduan1 / 类型=文本）
3. 真实鼠标点击名称输入框（td1 的 `input.ant-input`，坐标 501,548）→ `Input.insertText` 输入 `b1StrField` → Tab 失焦
4. 真实双击 caption 单元格（td2）进入编辑 → `Input.insertText` 输入 `B1文本验证` → Enter 提交
5. 点击「保存」按钮（坐标 470,118）
6. 平台行为：
   - **name 被平台自动改写**：我输入的 `b1StrField` 被替换为 **`B1wenbenyanzheng`**（平台按 caption 拼音自动生成 name）
   - **保存是否由此点击触发 = UNVERIFIED**（见 §三：v9 在 [2] 即 ABORT，未执行到保存点击；
     那句「保存成功」是后来读到页面既有状态，**不得作为本步的因果证据**）

> **⚠ 本「操作步骤」节的定性说明（main B1 裁决 + auditor §五①）**：
> 本节描述的是设计器的操作路径（可复现），**不是**「本次点击产生了该结果」的因果证明。
> 字段确实建成这一结论，由 §五(DB) + §六(审计日志/服务端读接口) 四方独立证据支撑；
> 「点击 → 保存成功」因果链维持 **UNVERIFIED**。

> 探索过程中的教训（每一条都有日志佐证）：
> - 前端编辑锁：「由于长时间未操作，页面已锁定」——点「重试」解锁后恢复正常，锁期间保存无效。
> - 草稿缓存：脏编辑行会写 `localStorage.AUTO_SAVE_CACHE`，刷新页面会复活，必须先清缓存或先处理草稿行再继续。
> - 值填写必须用真实键盘事件（`Input.insertText`）；`value setter + Event` 不进 React 状态（行文本不变）。
> - caption（td2）与 name（td1）是两个不同字段；caption 由用户填，name 平台按拼音自动生成。

## 三、请求证据 —— **本片缺失，标 UNVERIFIED**

**① 保存链证据失效（auditor VERDICT §二/§五①，2026-10-18 更正）**

本片初版在此处写「页面『保存成功』提示（v9 log [2] tail）」并归因「batch=0 是时序边沿」——**这两个说法都错**，已撤回：

- `b1_v9.js` L65：`if (r2.none) { log('ABORT_NO_EDIT_ROW'); ws.close(); return; }`
- `b1_v9.log` L2 的 r2 = `{"none":true,...}`，L3 = `ABORT_NO_EDIT_ROW`
- => **v9 在 [2] 就 return，从未执行到 [3] 的保存点击**；它的 `[7] BATCH reqs` 也没执行。
  那句 tail 是它**读到**的页面既有状态，不是它**产生**的结果。

时间线（auditor 核过）：
| 时刻 | 文件 | tail 末尾 |
|---|---|---|
| 03:09:46 | `b1_v7.log` [4] | `…请检查未完成的配置项`（无「保存成功」） |
| 03:12:10 | `b1_v8.log` | 止于 [4]，rowText 为空串（行被工具栏搜索框过滤） |
| 03:13:52 | `b1_v9.log` [2] | `…请检查未完成的配置项\n保存成功`（有） |

「保存成功」文本是 03:09:46→03:13:52 之间新出现的，与 DB `create_time=03:12:13` 同源——
**即它来自 v8 那一轮（v8 崩溃前已点过保存），不是 v9 的产物**。
另：`b1_v8.log` 现存文件可能是一次重跑产物（曾 `rm -f`），不能作为唯一时序锚点。

**修正后的定性：**

| 结论 | 等级 | 依据 |
|---|---|---|
| **写链结果成立**（字段确实建成了） | **LIVE** | ①`udc_operation_log` 有 CREATE 记录 ②`udc_attribute` 落库 ③`udcAttributeGroupEntityGet` 服务端回读——三方独立，**与点击日志无关** |
| **「页面点击 → 保存成功」因果链** | **UNVERIFIED** | 保存点击的日志行缺失。只有 `b1_v8.js` 里 `[5]` 无条件执行这一**代码结构**作支撑——是推断，不是证据 |
| `udcAttributeGroupOperateBatchPost` 请求/响应原文 | **UNVERIFIED** | 本片未取到（见 §九 补证计划） |

> **③ batch 归因撤回**：原写「保存请求发生在脚本 save 点击后的等待窗口、进程结束时序边沿外」——
> 该归因不成立，因为 v9 是 ABORT 而非边沿外。真实情况是：**本片没有任何一轮成功执行到保存点击并留下日志**。

> 判定说明：本片的 LIVE 判定**不由任何单次 HTTP 响应或点击日志支撑**，
> 而由「审计日志 + DB 落库 + 服务端读接口回读」三方独立确证（见 §五、§六、§七）。

## 五、DB 回读（LIVE）

```sql
SELECT id,name,caption,data_type,db_column_name,max_length,is_not_null,uniqueness,calculate,publish_state,create_time
FROM udc_test2.udc_attribute
WHERE entity_id=474806313816300867 AND caption LIKE 'B1%';
```

```json
[{"id": 1021739412060058618, "name": "B1wenbenyanzheng", "caption": "B1文本验证",
  "data_type": "STRING", "db_column_name": "b1wenbenyanzheng", "max_length": "50",
  "is_not_null": 0, "uniqueness": 0, "calculate": 0, "publish_state": 1,
  "create_time": "2026-10-18 03:12:13"}]
```

> **② `publish_state` 语义更正（auditor VERDICT §五②）**：`PublishStateEnum` 是
> **`PUBLISHED(0)` / `UNPUBLISH(1)`** —— 所以这里 `publish_state=1` 是 **`UNPUBLISH`（未发布/设计态）**，
> **不能**当作「状态正常/已发布」的证据。且它**零区分度**：auditor 实测 `udc_attribute`
> 全表 67863 行 `publish_state` 全为 1、本实体 18 行全为 1。
> 正确读法：`publish_state=1 (UNPUBLISH，设计态；全表统一值，无区分度)`。

业务字段计数：`SELECT COUNT(*) FROM udc_test2.udc_attribute WHERE entity_id=474806313816300867 AND is_system=0` → **10**（执行前 9）。
> auditor 独立复核：`is_system=0` 现 10 行、`is_system=1` 8 行、合计 18 行，与「9→10」一致。

物理表列检查（预期为空）：

```sql
SELECT COLUMN_NAME FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA='datamigration9000000000000000002_test2'
  AND TABLE_NAME='xzhexp950_m1719416608666233204' AND COLUMN_NAME LIKE 'b1%';
-- ROWS 0（物理列由应用构建/发布生成，非设计态保存产物）
```

## 六、服务端独立回读（LIVE，本片补证）——排除「localStorage 草稿假象」

页面可见（§七）单独不足以排除草稿假象。以下两条是**服务端**证据，与前端状态无关。

### 6.1 `udc_operation_log` 审计日志（CREATE 记录，含完整 before→after）

```sql
SELECT id,action_type,module,sub_module,operator_id,domain_id,domain_caption,
       operation_time,FROM_UNIXTIME(operation_time/1000),trace_id
FROM udc_test2.udc_operation_log WHERE domain_id=1021739412060058618;
```

```json
[{"id": -7706823437516783871, "action_type": 1, "module": 6, "sub_module": 11,
  "operator_id": -2638952494757493308, "domain_id": 1021739412060058618,
  "domain_caption": "小爪实验实体950795V2",
  "operation_time": 1792264333032, "trace_id": "17922643323482829867",
  "op_time_fmt": "2026-10-18 03:12:13.032000"}]
```

`log_details` 关键结构（逐字摘取）：

```json
{"appId":9000000000000000002, "domainId":1021739412060058618,
 "path":"entity=474806313816300867&attributeId=1021739412060058618",
 "actionType":"CREATE",
 "elementRecords":[{"element":"实体\\实体[小爪实验实体950795V2]\\实体字段[B1文本验证]",
   "actionType":"CREATE",
   "attributeRecords":[
     {"name":"名称","before":{"value":"-"},"after":{"value":"B1文本验证"}},
     {"name":"编码","before":{"value":"-"},"after":{"value":"B1wenbenyanzheng"}},
     {"name":"数据库列名","before":{"value":"-"},"after":{"value":"b1wenbenyanzheng"}},
     {"name":"类型","before":{"value":"-"},"after":{"value":"STRING"}},
     {"name":"类型[单多选]","before":{"value":"-"},"after":{"value":"单选"}},
     {"name":"阈值设置[最小长度]","before":{"value":"-"},"after":{"value":"0"}},
     {"name":"阈值设置[最大长度]","before":{"value":"-"},"after":{"value":"50"}},
     {"name":"必填","before":{"value":"-"},"after":{"value":"关闭"}},
     {"name":"唯一","before":{"value":"-"},"after":{"value":"关闭"}},
     {"name":"默认值修改","before":{"value":"-"},"after":{"value":"开启"}}
   ]}],
 "module":"ENTITY", "subModule":"ENTITY_ATTR"}
```

> 这是**平台自己记的操作审计**：谁（operator_id=test-account-1）、何时（03:12:13.032）、对什么（attributeId）、做了什么（CREATE）、每个字段 before→after。它不依赖任何前端状态。

### 6.2 `udcAttributeGroupEntityGet` 服务端读接口回读

```
POST /service/udc/graphql?udcAttributeGroupEntityGet
{"query":"query graphqlLoader ($p: udcAttributeGroupEntityGetInputPath) { data0: udcAttributeGroupEntityGet(path: $p) { code data { content { id entityId attributeDtoList { id name caption dataType maxLength orderNo publishState createTime } } } message status } }",
 "variables":{"p":{"appId":"9000000000000000002","entityId":"474806313816300867"}}}
```

响应 `traceId=3279131390473406652`，`BOOT_0000`，2 个属性组共 14 个 attribute，命中：

```json
{"id":"1021739412060058618", "name":"B1wenbenyanzheng", "caption":"B1文本验证",
 "dataType":"STRING", "maxLength":50, "orderNo":16,
 "publishState":"UNPUBLISH", "createTime":1792264333000, "g_l_index":"7"}
```

> `createTime=1792264333000` 换算 = **2026-10-18 03:12:13**，与 DB `create_time` 同源。
> 这是**服务端返回**的字段定义，页面重载后渲染的数据来自此处 —— 排除 localStorage 草稿假象。

---

## 七、页面可见（LIVE）

重载设计器页面后重新抓取（`verify_page.js`）：

```json
{"foundOnPage": true,
 "rowText": "14|\t|B1文本验证|\t|B1wenbenyanzheng|\t|文本|\t|长度：0 至 50|\t|请设置|\t|请设置|..."}
```

## 八、name 拼音生成机制（auditor 闭合：STATIC + LIVE）

原文猜测「后端 `PinyinUtils` 之类改写」——**方向对，机制错**。真实实现是**前端调后端拼音接口后覆盖 name 输入框**。

**STATIC**（`src_redux_store_ts.14dc061e.js` 模块 88804）：
- 判据：`RegExp("[\\u4E00-\\u9FFF]+").test(e)` —— 只有含汉字才走接口；纯 ASCII 原样返回
  （这解释了 `B1` 前缀为什么被保留）
- 调用：`udcApolloQuery("query udcPinyinGet ($query: udcI18nResourceStrToPinyinGetInputQuery) { udcI18nResourceStrToPinyinGet(query:$query){ code data{ content } message status } }", {query:{str:e, maxLength: t??20}})`
- debounce 300ms
- 后处理：只留 `/\w/` → 超 30 截断 → 去 `_`
- 前端**没有本地拼音库**（auditor 扫 47 个 JS chunk、1128 万字符：pinyin / pinyin-pro / tiny-pinyin / js-pinyin 全零命中）

**LIVE**（auditor 实打该端点 4 样本）：
| 输入 | 返回 |
|---|---|
| `B1文本验证` | `B1wenbenyanzheng` ← 与落库 name 逐字相同 |
| `实验文本` | `shiyanwenben` |
| `B1文本验证xyz` | `B1wenbenyanzhengxyz` |
| `纯ASCIIname` | `chunASCIIname` |

> **结论**：不是 Java 工具类，是 **GraphQL 操作 `udcI18nResourceStrToPinyinGet`**（i18n 资源体系的拼音能力）。
> 以后同类需求直接打这个端点，别翻字节码。

---

## 九、物理列边界（auditor 核实成立）

`datamigration9000000000000000002_test2.xzhexp950_m1719416608666233204` 存在、17 列、**无** `b1wenbenyanzheng`。

边界成立的依据（既有铁律，非本片判断）：
- `core/facts/udc/entity/attribute-create.md` L73：属性建入设计态元数据；物理列在 RELEASE 构建后落应用自身库
- `core/facts/udc/entity/create.md` L75-79：物理表随 RELEASE 构建落 `{app}_test2`，非 `udc_test2`
- TASK-GOAL 三段链路含「运行态可访问」，物理列属运行态，不在本切片

**→ 物理列缺失是预期，不构成缺陷。**

> 可复用推断（auditor 补）：该物理表已有 `exp_text`/`exp_enum`/`exp_date`/`exp_num`/`exp_flag`/`exp_members`（10-14 建的字段），
> 说明上次 RELEASE 构建在 10-14 之后；B1 是 10-18 建的所以缺列。
> **后续验物理列前必须先确认最近构建时间戳，不能假定「构建过就自动带新字段」。**

---

## 十、字段类型矩阵记账

| # | 类型 | 状态 | 证据 |
|---|---|---|---|
| 1 | CTPENUM | ✅ 已闭环 | 68b12ca（ctp_enum A/B 双向确证） |
| **2** | **STRING** | **写链结果 LIVE；请求证据 UNVERIFIED** | 本文档 §五/§六/§七（DB + 审计日志 + 服务端回读 + 页面） |
| 3+ | ENUM/DATE/DECIMAL/… | 待排 | — |

> 矩阵记账口径：STRING 的**设计态写链结果**已 LIVE 确证；但 ROUTE L12 要求的「请求证据」这一腿空缺，
> 故本片整体判 **PARTIAL**（auditor VERDICT），矩阵该格不记「完整 PASS」。

## 十一、复现（含上一轮的教训）

```bash
cd <SEEYON_AGENT_ROOT>
# CDP 9222 + cookie 注入后：
node docs/audit/artifacts/scratch-migrated/slice-b1/b1_v6.js     # 基线断言 + 添加 + 填名（平台会把输入值改为拼音名）
node docs/audit/artifacts/scratch-migrated/slice-b1/b1_v7.js     # 填 caption
# 注意：b1_v9.js 会在 [2] ABORT（设计缺陷），不要用它复现保存
```

**上一轮复现脚本的坑（务必避开）**：
- `b1_v9.js` L65 有 `if (r2.none) { ABORT; return }`，编辑行不存在时直接退出，**不会点保存**
- 别把它输出的 tail 当成"本轮产生的结果"——那只是它读到的页面既有状态
- 抓 batch 原文必须用**常驻监听**（`Network.enable` 后不 sleep 扫 events，而是事件里即时 `getResponseBody`）

## 十二、边界与诚实声明

- **`udcAttributeGroupOperateBatchPost` 的请求体/响应体未取到原文** → 契约级 **UNVERIFIED**。
  本片**不声称**契约闭合。补证计划见 §三。
- **「页面点击 → 保存成功」因果链未闭合** → **UNVERIFIED**。保存点击的日志行缺失；
  写链成立由 §五/§六 的服务端证据支撑，**与点击日志无关**。
- 本片新增字段 `B1文本验证` 留在应用中（不删除），供后续「矩阵第 3 类」「运行态物理列」验证复用；
  若需清理，删除动作属写操作，另行授权。
- 全程 0 次 REST 写调用；页面点击均通过 CDP Input 域真实事件派发。
- SSO：本轮共 2 次 token 失效（跨组互踢），均已按 30s 冷却 + 重新登录恢复，未中断切片。

---

## 十三、本轮更正记录（auditor VERDICT 后自查）

| # | 原错误表述 | 更正为 | 性质 |
|---|---|---|---|
| ① | 「页面『保存成功』提示（v9 log [2] tail）」当作本人点击产物 | v9 在 [2] 即 ABORT，从未点保存；该 tail 是读到的既有状态（来源 = 03:12:13 那轮） | **严重误读，已撤回** |
| ② | `publish_state=1` 与 create_time 并列，易读成「状态正常/已发布」 | `publish_state=1 = UNPUBLISH（未发布，设计态）`；全表 67863 行统一值，**零区分度** | 语义错误 |
| ③ | 「batch=0 因保存请求落在脚本等待窗口外（时序边沿）」 | 归因不成立：v9 是 ABORT 不是边沿外；真实情况是本片没有一轮执行到保存点击并留日志 | **归因错误，已撤回** |

> 这三处均**不影响写链结论**（写链由审计日志 + DB + 服务端回读三方独立支撑），
> 但会让复现者发现「v9 是 ABORT」从而怀疑整片——**因此必须更正而不是淡化**。

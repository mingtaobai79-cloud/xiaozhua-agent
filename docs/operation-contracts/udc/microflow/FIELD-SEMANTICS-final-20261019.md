# FIELD-SEMANTICS｜P2 收官（type=2·组装映射·落点互证）

> ℹ️ **同批三件之三（P2 收官）**：另两件 `FIELD-SEMANTICS-app-std-20261019.md`（ACTIVITY）、
> `FIELD-SEMANTICS-ctl-frontend-20261019.md`（CONTROL + 前端分层）。共用快照戳 2026-10-17 15:41:03。

> `datamigration9000000000000000001`/test2｜**LIVE**（DB/Redis 只读）＋**STATIC**｜0 `/service`、0 写库
> 戳 app `MAX(update_time)=2026-10-17 15:41:03`

## 一、口径

- **A** 47 条 → CONTROL 96（END 46／BRANCH 16／CONDITION 34）｜ACTIVITY 155
- **B** `type IN (0,3)` 20 → 31（20/4/7）｜56　**C** `type=1` 27 → 65（26/12/27）｜99
- **D** `type=2` 本 app **0 条** → §二 VACUUM

★ §二 全篇 A（96）：16+34+46=96 与 A 行自洽。
A 155 = B 56 + C 99。全库：ACTIVITY 28616 + CONTROL 27054 = 55670（两域不相交）。

## 二、type=2：本 app VACUUM ＋ 全库 3 种参考

**本 app type=2 = 0 条**（0:10／1:27／3:10 = 47）→ 3 种在本 app **0 实例**。负证据限本 app

全库 type=2：**25 行／17 name／5 app**（`MAX(update_time)=2026-10-14 09:53:34`）。**层位分开计**：节点树内 CONDITION 67／BRANCH 33／ACTIVITY 34，**树内 END = 0**；流程级 `endNode` 24
（actionType=`END_NODE`，只在顶层）。ACTIVITY 侧 3 种：

| actionType | 实例 | constraints 必填 | 定性 |
|---|---|---|---|
| `SHOW_MESSAGE` | 22 | **未收录** | 契约缺口（13 键全 22/22 在）|
| `SUB_MICROFLOW` | 7 | `('mappingType',)` | 完全匹配，缺 0（同第一段）|
| `ATTRIBUTE_REQUIRED` | 5 | **未收录** | 契约缺口（12 键全 5/5 在）|

**三个坑**：①24 LITE／唯一 FULL `rulesc8mOQ` 带 appId/sourceId/version 但**缺 endNode**→不可写「END 全有」。
②同名跨 app 8 组 md5 各异→去重口径 **(app_id,name)**，禁按 name。③`trigger` 25/25 为**空对象 `{}`**（非 None 非 list）。

`SUB_MICROFLOW` 三口径勿混：`output` 键在 **7/7**｜值为非 null dict **5**｜dict 内 `value` 非 null **0**
（2 例 `output=None` 均 `rulecUbY53`）。`outputName` 5/7（非 null 5）｜`outPutDesc` 5/7（**非 null 0**）｜
`mappingType`/`mfService`/`attrs` 7/7 非 null。

## 三、组装映射三层（STATIC）

**③-1 预制层**：`udc_microflow_preset_template` 4 行（`publish_state` 全 1），`json_schema_template` 带 `${}` 插槽，
最长 `DynamicMfSearch` **4970 字节／4818 字符**（字节/字符双查）。插槽五类：
`microFlowId`/`appId`/`entityId`/`microFlowName`/`microFlowCaption`（均 `${}`）。
**节点级模板 VACUUM**：`udc_microflow_node_template` 0 行；`udc_entity_preset` 0 行。
`presetData/attribute.json` = 系统属性模板，非主存储（metadata-storage §3）。

**③-2 选择层**：`NODE_REQUIRED_FIELDS` 21 键 + `ACTIVITY_NODE_TYPES` 30 + `CONTROL_NODE_TYPES` 8。
**③-3 组装层**（高频 5 种，逐字段标注）：

| 节点 | 字段 | 来源 | 填充规则 |
|---|---|---|---|
| CALL_MICRO_FLOW | `mfService` | 目标微流程 | `[实测]` 24/24 必填 |
| CALL_MICRO_FLOW | `attrs`／`mappingType` | 入参映射 | `[实测]` 有映射才带（`MAPPING_TYPES` 3 值）|
| CALL_MICRO_FLOW | `output`／`outputName` | 返回值 | `[实测]` 可选 |
| RETRIEVE | `fetchType` | 面板枚举 | `[实测]` 7 实例 CONDITION 4／IDS 3 |
| RETRIEVE | `entityObject` | 目标实体 | `[模板]` 同 `${entityId}` 插槽 |
| RETRIEVE | `nullPromptMessage` | 空值策略 | `[实测]` 仅 `TERMINATION` 必填（7/7 CONTINUE 不报）|
| DATA_MAPPING | `mappingRule` | 映射体 | `[实测]` **dict** 6/6，勿 `json.loads` |
| BRANCH | `conditions[].nodes` | 分支体 | `[实测]` 长 1×1／2×14／5×1；空 body 合法 |
| END | `output` | 出口值 | `[实测]` 键 46/46 在；null 34/46（9 键组 29/29 全 null）|

→ 表内推断仅 1 行，余逐实例实测。

## 四、CROSS-VERIFIED 方法试运行（不计入分档）

**对象**：`xzhFinalAllNodes`（type=0，`version=29`，`publish_state=1`）。设计态→MySQL only；已发布→Redis 戳+MySQL。

```
① MySQL id=-1014184770817921434 ver=29
  update_time=2026-10-16 23:57:15  data_schema=38078B/36626字符 → 存在（真源）
② Redis @SERVICE.json → "\"1.0.14-20261015193001\""  → 存在（带引号 JSON 字符串，版本戳非正文）
②'Redis @FRONTEND@-1014184770817921434.json → None（TTL=-2）→ 不存在（该微流程无同 id 页面）
③ OSS udc@<实体>.json → 不可达（pod 无 OSS env）
```
★ 本 app `MicroFlow*` **10 键**：`@FRONTEND@<id>`×6｜`@SERVICE`×2（Entity+Group）｜无后缀×2（同两实体）。
10/10 值均同上引号串——不是「查不到」，是**查到的值为版本戳、不含节点正文**。

**`@FRONTEND@<id>` = 页面 schema 键（非 type=1 流程键）**：全库 **381** = Entity 375 + Group 6（唯一 id 375，下数按 Entity）
→ 353 ∈ `udc_page_info`（DETAIL 168／SEARCH_LIST 132／SUBPAGE 30／OTHER 15／PORTLET 6／EDIT_LIST 2）→**0 ∈ `udc_microflow_info`**。
本 app 6 个：5 个对上本 app 页面（`publish_state=1`）；第 6 个 `3062424803371796128` 两表均无→**悬空键**（单列不解释）。
→ 该微流程在本 app **无同 id 页面**，故无 `@FRONTEND@` 键。

**FRESHNESS（机械式）**：戳 ≈ 发布链末次成功，**阈值 5 分钟**。
```
戳 1.0.14-20261015193001 → 19:30:01
deploy_record 末次成功 state=1「内部流水线构建成功」→ 19:29:35, jar_version=1.0.14
差 26 秒 → FRESHNESS 成立；版本段 1.0.14 逐字一致
```
**MySQL 晚于发布 28.5 小时** = 发布后设计态继续编辑，非再次发布：10-17 起 **4 次全 state=2**
（22:56 一致性检测未通过／23:43 NFE／10-18 01:41 NFE／10-19 11:00 NFE）。

**档位**：按 `LIVE + FRESHNESS` 记录，不作分档主张。
★ **CROSS-VERIFIED 因 body 侧 BLOCKED_SSO 未达成，本文档无一例 CROSS**——D172 要求 MySQL + 前端 HTTP body，
本文只有 MySQL + Redis 戳。OSS 不要求（无凭据，不计 BLOCKED）。TTL：配置 **180h**（剩余值递减，非配置值）。

## 五、未覆盖

- type=2 三种本 app 全 VACUUM，语义只有全库 34 实例口径
- 前端 body 未取（SSO BLOCKED）→ 节点语义级 CROSS 不可达
- 节点级模板 0 行，组装层只能靠流程级模板 + constraints 推

# P1 交叉验证 VERDICT：复制菜单字段行为（独立取证）

> 角色：auditor（独立验证者，不采信 implementer 自报）
> 被验对象：implementer RESULT `menu-p1-copy-menu-field-probe-result`
> 被验文档：`docs/audit/udc-semantics/menu-copy-field-behavior.md` @ `f110ee2`
> 环境：test2 / 应用 `8704025620829192834` / 2026-10-17 15:41
> 结论：**PASS（含 2 项否定修正 + 2 项新增缺陷）**

## 0. 独立取证方式（全部本次自抓，未引用 implementer 快照）

| 证据层 | 本次动作 | 落盘 |
|---|---|---|
| 页面点击 | CDP 真实右键 → 点「复制」，未直调 REST | `aud_copy_doit.py` |
| REST 抓包 | `Network.requestWillBeSent` + `getResponseBody` | `aud_copy_capture.json` |
| DB 回读 | 复制前后全量 id 集 diff（非样本对照） | `snap_before.json` / `snap_after.json` |
| 页面可见 | 设计器树节点定位 + 面板文本 + 截图 | `auditor-p1-copy-menu-tree.png` |
| 字节码 | CFR `FunctionNodeService.java` / `PageInfoService.java` 复核 | 引用 r31b |

工作目录：`<HERMES_HOME>\cache\scratch\aud_menu_copy\`

## 1. 逐条裁决

| # | implementer 声明 | auditor 独立结果 | 判定 |
|---|---|---|---|
| 1 | `udc_page_info.master_entity_ids` 与 schema `masterEntityIds` 均源值照抄 | 3 对页面全部相同；schema JSON 内实体字段仅 `masterEntityIds` 1 处，同为照抄 | **PASS（LIVE）** |
| 2 | 源 7 条规则随新行迁移，source_id 指向新 page_id | 4+3=7 条新行，id/name 全新，source_id 正确指向新 page | **PASS（LIVE）** |
| 3 | 事件随迁 UNVERIFIED（eventDefine 全空、udc_event 0 行） | **声明前提有误**：页面事件存在 `events` 键而非 `eventDefine`；源详情页 1 条 onLoad→microflow，新页已随迁且 microFlow 重映射为新规则 id | **UNVERIFIED → 修正为 PARTIAL（LIVE 正证）** |
| 4 | 默认页错位 / page_url 与 schema.pageUrl 双源 / URL 叠 copy | 三项全部独立复现，机制落到字节码 | **PASS（LIVE+STATIC）** |
| 5 | 静默失败：relation_id 查不到 relation_group_id 静默跳过 | 机制复现：坏值查 0 行、真值查 1 行；空副菜单 0 子节点 | **PASS（LIVE+STATIC）** |
| 6 | 契约 `POST graphql?udcFunctionCopyPost` → BOOT_0000 data=null | 抓包逐字一致（含 `copyOtherTerminal:true` 写死） | **PASS（LIVE）** |

**总判定：PASS** —— 六项声明中 5 项独立成立，第 3 项采错字段但方向相反（事件实际随迁），不构成 FAIL；另发现 2 项 implementer 未报告的缺陷。

## 2. 独立 LIVE 数据（本次自抓，可复核）

### 2.1 抓包原样

```
POST https://lowcode-test2.example.com/service/udc/graphql?udcFunctionCopyPost
{"query":"mutation graphqlLoader ($params0: udcFunctionCopyPostInputBody) {  data0: udcFunctionCopyPost(body: $params0) { code data { content } message status } }",
 "variables":{"params0":{"appId":"8704025620829192834","copyOtherTerminal":true,"terminalType":"PC","ids":["9183843213439484192"]}}}
HTTP 200
{"traceId":"17922228629611463494","data":{"data0":{"code":"BOOT_0000","data":null,"message":"SUCCESS","status":0}}}
```

页面动作：`右键 迁移方案配置(@x133,y743)` → dropdown `[重命名, 复制, 删除]` → 点「复制」。
**无弹窗、无 toast**（`modals: [], toasts: []`）——成功后前端零反馈，符合"只能靠 DB diff 拿新 id"。

### 2.2 前后 DB 全量 diff（app 范围 id 集差集）

| 表 | before | after | Δ | 本次新增 |
|---|---|---|---|---|
| `udc_function_node` | 2265 | 2269 | **+4** | 1 菜单 + 3 PAGE |
| `udc_page_info` | 1571 | 1574 | **+3** | 3 页面 |
| `udc_page_schema` | 1558 | 1561 | **+3** | 3 schema |
| `udc_microflow_info` | 4748 | 4755 | **+7** | 7 规则 |
| `udc_event` | 52 | 52 | **0** | — |
| `udc_micro_flow_group` | 265 | 265 | **0** | 未随迁 |

新菜单 `-389182344634194186`，`default_page=5284982198962389711`，`url=sjypzxxListPagecopycopycopy`。

### 2.3 实体照抄（LIVE，3/3 命中）

| 页面 | 源 page_id | 新 page_id | 源 master_entity_ids | 新 master_entity_ids | 同 |
|---|---|---|---|---|---|
| 列表 `qyfapzlb` | 114216775019154694 | 540101808703999634 | 4796455827714164161 | 4796455827714164161 | ✅ |
| 详情 `qyfapzxq` | 7286622650788629332 | 8267428021549491279 | 4796455827714164161 | 4796455827714164161 | ✅ |
| 弹窗 `sjypzxxListPagecopy` | 992522359796286320 | -8358257041803639157 | 5738598551920790169 | 5738598551920790169 | ✅ |

schema JSON 内 `masterEntityIds` 三对同样逐一相同。
字节码支撑：`FunctionNodeService:791/836` 仅 `setMasterEntityIds(pageInfoDto.getMasterEntityIds())`，全链无实体重映射。

### 2.4 规则随迁（LIVE，7/7）

| 新页面 | caption 集合 | 新规则数 |
|---|---|---|
| 540101808703999634（列表） | 立即同步/全量同步/保存数据/查看日志 | 4 |
| 8267428021549491279（详情） | 保存/选择对应数据源/加载数据源信息 | 3 |
| -8358257041803639157（弹窗） | — | 0 |

新规则 `name` 形如 `m2610171541030xx`，源为 `MFFRONTEND*`/`zVAAJupL` —— id 与 name 全换新，`source_id` 全部指向新 page_id。与 implementer 一致。

### 2.5 页面可见（设计器树）

```
[8463032321776371284 数据迁移]
  4774153827087238385 数据源配置
  9183843213439484192 迁移方案配置          ← 源
  7979915622848546953 迁移日志
  6054953263042158495 迁移方案配置_副本     ← implementer 上轮副本
 -389182344634194186  迁移方案配置_副本     ← auditor 本轮副本（同名并列）
    5284982198962389711 数据源配置信息列表弹窗选择页面_副本  默认 正式
    3730222570353692774 迁移方案配置详情_副本               正式
    5424505628747195904 迁移方案配置列表_副本               正式
```

截图：`docs/audit/artifacts/udc-menu-5.3.517/auditor-p1-copy-menu-tree.png`（88,978 B）

## 3. ★ 否定修正 1：事件随迁不是 UNVERIFIED，而是 LIVE 已随迁

implementer 依据 `eventDefine: []` 与 `udc_event 0 行` 判 UNVERIFIED，**采错字段**。页面事件真实落点是 schema JSON 的 `events` 数组（`eventDefine` 恒为 `[]`，不承载事件）。

源详情页 `7286622650788629332`：

```json
"events": [{"id":"zo8t0o","eventCaption":"页面初始化","eventType":"onLoad",
            "actionType":"microflow","microFlow":"8249313647887011099",
            "condEvents":[{"id":"ZEvUC3"},{"id":"pDtZut"}]}]
```

新详情页 `8267428021549491279`：

```json
"events": [{"id":"zo8t0o","eventCaption":"页面初始化","eventType":"onLoad",
            "actionType":"microflow","microFlow":"7362485689270341281",
            "condEvents":[{"id":"ZEvUC3"},{"id":"pDtZut"}]}]
```

`microFlow` 已由源规则 `8249313647887011099` 重映射为新规则 `7362485689270341281`（属新页面 8267428021549491279 的 3 条随迁规则之一）。**事件不仅随迁，且事件指向的规则引用被正确改指**。

对照检查（另两页面事件确实为空，implementer 大概率只抽样了这两个）：

| 页面 | `events` 条数 | `eventDefine` |
|---|---|---|
| qyfapzlb（列表） | 0 | `[]` |
| qyfapzxq（详情） | **1** | `[]` |
| sjypzxxListPagecopy（弹窗） | 0 | `[]` |

结论：**"事件不随迁"不成立**；正确表述是"事件随迁，落 `page_schema.events`，且 `microFlow` 引用一并重映射"。这直接影响 P2 —— 原计划"找 eventDefine 非空的源页面再复制"是**无效补证路线**，因为该字段恒空；P2 应改为校验 `events[].microFlow` 的重映射完整性。

## 4. ★ 否定修正 2：'全库 1452 个 PAGE 节点' 数字不实，且统计口径漏负 id

| 口径 | join 命中 | 不匹配 |
|---|---|---|
| `CAST(resource_id AS UNSIGNED)`（implementer 原式） | **894** | 1 |
| `CAST(resource_id AS SIGNED)` | **1336** | 1 |
| `type=1` 节点总数 | **1336** | — |
| `type<>0`（PAGE+REPORT+EXT_LINK） | 1374 | — |

- 全库 PAGE(type=1) 实为 **1336**，非 1452。
- implementer 原式 `AS UNSIGNED` 静默丢弃 **442** 个负 id 页面（`resource_id` 为负时转换失败），所以只扫到 894 个。
- 幸而两种口径的「不匹配数」结论一致 = **1**，且指向同一节点，**结论仍成立，数字与覆盖范围需更正**。

不匹配唯一节点（LIVE 复核）：

```
node 4630606675502338872 「小爪验收页面」
  node.relation_id        = 1431476845001478322
  page 1520098474917276520 relation_group_id = -6298081275352303163
```

机制实证：按 `1431476845001478322` 查 `page_info` → **0 行**；按 `-6298081275352303163` 查 → **1 行**。
故 `copyMenuFunction:744/768` 的 `CollectionUtils.isNotEmpty(pageInfoDtos)` 为假 → 整段复制体被跳过，**不抛异常、不报错**。
空副本 `-6340030840568160268` 落库复核：`default_page=null, url=null, resource_id=null`，子节点 **0**。

## 5. ★ 新增缺陷（implementer 未报告）

### 5.1 schema `relationGroupId` 未重映射（3/3 页面全部残留源值）

| 新页面 | page_info.relation_group_id | schema.relationGroupId | 一致 |
|---|---|---|---|
| 540101808703999634 | -4207444815775121714 | **-6767432651261196955**（源） | ❌ |
| 8267428021549491279 | -5269791848343575650 | **7427956962460123794**（源） | ❌ |
| -8358257041803639157 | 7855292447662599427 | **3676836814625326282**（源） | ❌ |

节点 `relation_id` 与 `page_info.relation_group_id` 一致（3/3 ✅），但 schema JSON 里那一份仍是源值。
性质与 5.2 的双源不一致**同源**：`buildPageDefinitionDto:836` 直接塞 `currentPage.getPageSchema()` 原串，未做 id 重写。implementer 只报了 `pageUrl` 一处，**漏了 `relationGroupId`，也漏了 `id`/`originId`**。

### 5.2 三层 URL / 三层 relation 一致性总表

| 项 | 新页面（列表） | 新页面（详情） | 新页面（弹窗） |
|---|---|---|---|
| node.url == page_url | ✅ | ✅ | ✅ |
| page_url == schema.pageUrl | ❌ | ❌ | ❌ |
| page.relation_group_id == schema.relationGroupId | ❌ | ❌ | ❌ |
| node.relation_id == page.relation_group_id | ✅ | ✅ | ✅ |

即：**修复侧要改 3 个地方而非 2 个** —— `udc_page_info.page_url`、`page_schema.pageUrl`、`page_schema.relationGroupId`（外加 schema `id`/`originId`）。

### 5.3 默认页错位根因确认（LIVE）

`handleFunctionDefaultPage`（CFR 约 :1181-1194）逻辑：
`map` 里找不到 `defaultPage` → 取子节点 `Comparator.comparing(BaseEntity::getCreateTime)` 最早者，并**同时覆盖 `url`**。

- 源：`default_page=1112131275754652923`（列表页，order 404，最晚）
- 新：`default_page=5284982198962389711`（弹窗页，order 1011，最早创建）
- 且新菜单 `url` 被一并覆盖成 `sjypzxxListPagecopycopycopy`（弹窗页 url）——implementer 未点明 **url 也被改**。

副作用放大证据：树里两个「迁移方案配置_副本」同名并列（`6054953263042158495` 与 `-389182344634194186`），仅靠 id 区分。

## 6. URL 叠 copy 规则（LIVE + STATIC 双向确认）

`PageInfoService.createPageInfoRetryPageUrl:429`：
```java
String[] suffix = new String[]{"copy", RandomUtil.randomString(16)};
String newPageUrl = ImportUtil.repeatInfoWithSuffix(existPageUrls, pageUrl, 0, suffix, 50);
```
`FunctionNodeService:836`：`setPageUrl(pageInfoDto.getPageUrl() + "copy")` 先拼一次，再由 `repeatInfoWithSuffix` 撞名时叠 `copy`。
LIVE 序列：`qyfapzlb` → `qyfapzlbcopy` → `qyfapzlbcopycopy`；`sjypzxxListPagecopy` → `...copycopy` → `...copycopycopy`。与声明一致，且已到第 3 层，**该测试菜单已累积 3 个副本，建议 main 收口时清理**。

## 7. 未取证 / 明确边界

| 项 | 状态 | 原因 |
|---|---|---|
| P3 运行态门户可点击进入 | **UNVERIFIED** | 本 REVIEW_REQUEST 范围为 P1 复制字段行为，未含门户路由跳转。属下一阶段 |
| 事件 `condEvents` 的条件表达式（`ZEvUC3`/`pDtZut`）内容是否完整迁移 | **UNVERIFIED** | 需逐项展开 condition 定义对比，超出本轮最小动作 |
| 跨应用复制时实体是否错绑 | **UNVERIFIED** | 本轮只在同应用内复制，实体本就同属；跨应用场景未实测，implementer 的"跨应用才成为错绑"是**推断非实测**，应降级标注 |
| `eventDefine` 语义（为何恒为 `[]`） | **UNVERIFIED** | 未追字段定义；仅确认它不承载页面事件 |

## 8. 副作用登记（本次 auditor 产生，授权应用内，可逆）

- 菜单 `迁移方案配置_副本` `-389182344634194186`
- 3 个 PAGE 子节点：`5284982198962389711` / `3730222570353692774` / `5424505628747195904`
- 3 行 `udc_page_info`、3 行 `udc_page_schema`、7 行 `udc_microflow_info`
- 与 implementer 遗留副本（`6054953263042158495`、`-6340030840568160268`）合计 **3 个副本待清理**

## 9. 给 main 的路线建议（仅建议，不接管）

1. **P1 判 PASS 可收**，但证据文档必须更正两处：事件随迁（§3）、1452→1336 口径（§4）。
2. **P2 路线需重写**：原"找 `eventDefine` 非空样本"不可行（字段恒空）。正确最小动作 = 校验 `page_schema.events[].microFlow` 在复制后是否 100% 重映射到新规则 id（本轮 1/1 命中，样本仍薄）。
3. **缺陷清单从 3 项扩到 5 项**：新增 schema `relationGroupId`/`id`/`originId` 未重映射、`url` 被默认页逻辑连带覆盖。
4. 未取证项不要写进 PASS 范围。跨应用实体错绑请降级为推断。

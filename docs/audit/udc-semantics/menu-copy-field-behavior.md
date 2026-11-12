# 复制菜单字段行为实测（P1）——「页面不换实体」字段定界 + 规则随迁 + 默认页错位

> 领域：菜单/导航 → `udcFunctionCopyPost` 复制路径的字段行为
> 状态：**LIVE PASS**（test2，app `8704025620829192834`，2026-10-17）
> 证据：页面点击（CDP 真实鼠标右键→复制）+ REST 抓包 + DB 前后快照 diff + CFR 字节码
> 接续：`core/facts/udc/write-chain/menu-default-page-write-chain.md`（建/绑/删/树回读）

## 0. 结论速览

| 问题 | 实测结论 | 等级 |
|---|---|---|
| 「页面不换实体」落在哪个字段 | `udc_page_info.master_entity_ids`（DB 列）+ `udc_page_schema.page_schema` JSON 内 `masterEntityIds`（schema 层），两处均为源页面原值逐字照抄 | LIVE |
| 规则是否随迁 | **随迁**。源 7 条页面规则 → 全部生成新行（新 id/name，caption 一一对应），挂在复制出的新页面下 | LIVE |
| 事件是否随迁 | **UNVERIFIED**——样本源页面 eventDefine 全空、udc_event 0 行，无事件可迁，样本不可证伪 | UNVERIFIED |
| 额外缺陷 | ① 复制后新菜单**默认页错位**；② 新页面 `page_url` 与 schema 内 `pageUrl` **双源不一致**；③ URL 后缀规则 = 源 url+`copy`，若撞名再叠 `copy` | LIVE |
| 静默失败分支 | `copyOtherTerminal=true` 分支用 `node.relation_id` 查 `page_info.relation_group_id`，查不到**静默跳过**（不报错、零落库） | LIVE |

## 1. 操作方式（满足"必须页面点击"约束）

CDP 真实鼠标操作设计器页面 `app-design/page-manage/functions`：
右键源菜单节点 → 等 dropdown 可见 → 左键点「复制」。REST 全程仅旁证抓包，未直调。

踩坑记录：**后台标签页 rAF 节流会导致 antd dropdown 定位失败**（dropdown 不渲染或坐标为 0），
必须先 `Page.bringToFront` 把设计器 tab 切前台再派发鼠标事件。

## 2. 复制契约（抓包原样）

```
POST /service/udc/graphql?udcFunctionCopyPost
{"query":"mutation graphqlLoader ($params0: udcFunctionCopyPostInputBody) {
   data0: udcFunctionCopyPost(body: $params0) { code data { content } message status } }",
 "variables":{"params0":{"appId":"8704025620829192834",
   "copyOtherTerminal":true,"terminalType":"PC","ids":["9183843213439484192"]}}}

响应：{"traceId":"...","data":{"data0":{"code":"BOOT_0000","data":null,"message":"SUCCESS","status":0}}}
```

- 入参 DTO = `FunctionBatchCopyDto {appId, copyOtherTerminal, terminalType, ids[]}`。
- **`copyOtherTerminal` 由前端写死为 `true`**，不是可选参数。
- controller 层 `data: null` 即成功，**新节点 id 不在响应里**，只能靠 DB diff 或树回读拿。

## 3. LIVE 实测：复制前 → 后 DB diff（干净源菜单）

源菜单 `迁移方案配置 9183843213439484192`（3 个 PAGE 子节点，7 条页面规则）：

| 表 | before | after | delta | 说明 |
|---|---|---|---|---|
| udc_function_node | 58 | 63 | +5 | 1 新菜单 + 3 PAGE 子节点 + 1 首轮空副本 |
| udc_page_info | 25 | 28 | +3 | 每个源页面各复制 1 行 |
| udc_microflow_info | 33 | 40 | +7 | 全部 7 条规则随迁 |
| udc_page_schema | 11 | 14 | +3 | 每页面 1 行 |
| udc_event | 4 | 4 | 0 | 样本无事件 |
| udc_micro_flow_group | 1 | 1 | 0 | 未随迁 |

## 4. ★「页面不换实体」的字段定界

### 4.1 DB 层（`udc_page_info.master_entity_ids`）

| 页面对 | 源 master_entity_ids | 新 master_entity_ids | 相同 |
|---|---|---|---|
| 列表页 源 114216775019154694 → 新 844278122493924338 | 4796455827714164161 | 4796455827714164161 | ✅ |
| 详情页 源 7286622650788629332 → 新 3254255197550241742 | 4796455827714164161 | 4796455827714164161 | ✅ |
| 弹窗页 源 992522359796286320 → 新 1185161788250969507 | 5738598551920790169 | 5738598551920790169 | ✅ |

实体归属核验：`4796455827714164161` = `migrationPlan`（迁移方案配置），`5738598551920790169` = `migrationDatasource`（数据源配置信息），
两者都属于**本应用**（app_id=8704025620829192834）——即同应用内复制时实体本来就同属一应用，字段照抄在**跨应用**场景才会成为错绑。

### 4.2 Schema 层（`udc_page_schema.page_schema` JSON）

新页面 `masterEntityIds` 与源完全一致（3 对全部相同），同时 `pageUrl` 也逐字照抄源值
（`qyfapzlb`/`qyfapzxq`/`sjypzxxListPagecopy`），**未更新为新的带 copy 后缀 URL**。

### 4.3 字节码侧（STATIC，CFR `FunctionNodeService.java`）

`copyFunctionNode` → `buildPageDefinitionDto`(:825起) / `buildPageDefinitionDtoWithOtherTerminal`(:782起)
只做 `setMasterEntityIds(pageInfoDto.getMasterEntityIds())`，整条复制链无任何实体 id 重映射。
复制本质 = **页面壳复制 + 实体指针照抄**。

## 5. 规则随迁（LIVE）

7 条全部生成新行，caption 一一对应，但 **id 与 name 全换新**（`m2610171518xxxx`），
不是源 `MFFRONTEND*`：

| caption | 源 source_id | 新 source_id | 新 name |
|---|---|---|---|
| 保存数据/立即同步/全量同步/查看日志 | 114216775019154694(列表) | 844278122493924338 | m2610171518501xx |
| 选择对应数据源/加载数据源信息/保存 | 7286622650788629332(详情) | 3254255197550241742 | m2610171518497xx |

规则所在新页面 `udc_microflow_info.source_id` 已正确指向新 page_id。
另注意源里 caption「保存」出现在详情页、「保存数据」在列表页——caption 跨页面对应关系
与直觉相反，修复侧做规则迁移时**不要按 caption 猜页面归属，按 source_id**。

## 6. 实测缺陷（复制路径自带，与本次操作方式无关）

### 6.1 复制后默认页错位（LIVE）

- 源菜单 `default_page=1112131275754652923`（迁移方案配置列表 / `qyfapzlb`）
- 新菜单 `6054953263042158495` `default_page=-3885312734344344686`（**弹窗选择页_副本**，order_no=1007，最早 create_time），url=`sjypzxxListPagecopycopy`
- 根因：`handleFunctionDefaultPage`(:1181) 取「最早创建的子节点」，复制时子节点创建顺序 ≠ 原 order_no → 默认页落到错误页面。

### 6.2 page_url 双源不一致（LIVE）

新页面 `udc_page_info.page_url` 加了 copy 后缀（`qyfapzlbcopy`），但 `page_schema.pageUrl`
仍是 `qyfapzlb`。两处 URL 不同源，修复/迁移动作要改就两处都要改。

### 6.3 URL 后缀规则（LIVE）

源 url + `copy`；若已存在同名（如源本身是上一次复制的产物 `sjypzxxListPagecopy`），
再叠 `copy` → `sjypzxxListPagecopycopy`。

### 6.4 静默失败分支（LIVE 复现 1 例 + 全库扫描佐证）

首轮对「小爪验收菜单」复制只生成 1 个空菜单节点、0 子页面、无报错。
根因：源 PAGE 节点 `4630606675502338872` 的 `relation_id=1431476845001478322`
≠ 其页面 `1520098474917276520` 的 `relation_group_id=-6298081275352303163`
（该脏 relation_id 来自上一轮 `create/function-refer` 时服务端自动补的值；全库 1452 个
PAGE 节点仅此 1 例不匹配）。`copyOtherTerminal=true` 分支按 `node.relation_id` 查
`page_info.relation_group_id`，查不到就静默跳过——**不报错、部分落库**。
推论：修复复制链路时不能只信 BOOT_0000，必须 DB 回读子节点数。

## 7. 副作用登记（授权应用内，全部可逆未清理）

- 菜单 `小爪验收菜单_副本`（-6340030840568160268，首轮静默失败的空副本）
- 菜单 `迁移方案配置_副本`（6054953263042158495）+ 3 个 PAGE 子节点
- 3 行 page_info + 3 行 page_schema + 7 行 microflow_info

## 8. 复现脚本（scratch，受 24h 清理）

`<HERMES_HOME>/cache/scratch/menu_copy/`：
`snapshot.py before|after|after2`（前后快照）、`copy_final.py` / `copy_clean.py`（页面点击复制+抓包）、
`diff.py` / `diff2.py`（diff）、`verify2.py`（schema/默认页/事件面）、`verify_branch.py`（静默失败根因）。
原始抓包：`copy_capture_clean.json`、`copy_capture.json`。

## 9. 未完成（明确）

1. **事件随迁 UNVERIFIED**：需找一个 eventDefine 非空的源页面再复制一次（可并入 P2）。
2. 交叉验证（auditor 独立抓包/回读）未做——按协议由 main 发 REVIEW_REQUEST。

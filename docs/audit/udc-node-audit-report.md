# UDC 标准微流程 100% 可生成化验收报告

- 审计时间：2026-10-17 09:20:37 +0800
- 审计方：小爪（独立只读审计）
- 目标流程：`-1014184770817921434`
- 应用：`datamigration9000000000000000001`（test2）
- 审计范围：P1 19 类节点、最新落库态 `FIXED20.json`、节点证据 JSON、CDP 编辑器面板
- 本轮未修改任何被审计的节点、证据或落库文件；仅生成本报告。

## 一、结论

# FAIL

当前成果不能验收为“100% 可生成化”。结构层有进步：CDP 独立新 tab 刷新后，实际可点击并捕获到 18 个节点标题，18 个已捕获面板的红字扫描均为 0；最新 `FIXED20.json` 中确实存在 19 个节点，且节点类型集合覆盖计划列出的 19 类。

但四层验收仍未闭合：

1. **面板身份未闭合**：`事件投递(1)` 与 `自定义服务(1)` 的面板文本完全相同，无法证明事件投递面板实际切换成功；既有身份审计已明确标记 `PANEL_IDENTITY_UNVERIFIED`。
2. **面板覆盖不完整**：落库态有 `RETRIEVE_ARRAY_n3（第一页的记录）`，本次 CDP 标题捕获中没有对应面板，不能把 18/18 红字=0 推广成 19/19。
3. **必填/语义存在硬缺口**：`CALL_APP_SERVICE_n16.attrs=[]`，但服务契约参数为 `java.lang.Long`；`CHANGE_BATCH_ENTITY_n11.attrs=[]`，批量更新没有字段赋值。文本面板能显示参数区域，不等于落库值已绑定。
4. **外部残留未通过双层扫描**：节点落库态 `FIXED20.json` 本身未命中词表，但节点证据目录仍有 `合同档案`、`应收`、`销售` 等命中，出现在 `events_own.json`、`real_map_samples.json`、`udcEventListPost_all.json`；因此“证据包 id+desc 双层扫描=0”不成立。

## 二、证据索引（四件套核对）

| 证据层 | 路径 | 结果 |
|---|---|---|
| ① 接口/契约证据 | `docs/audit/artifacts/udc-node-evidence/`（20 个 JSON） | **部分具备**；存在事件、映射、扣减等契约，但未形成 19 类节点一一对应的完整证据索引 |
| ② 落库态 | `<HERMES_HOME>/cache/scratch/FIXED20.json` | **存在**；解析出 19 个节点，节点类型集合与 P1 计划 19 类一致 |
| ③ CDP 面板身份/红字 | `docs/audit/artifacts/udc-node-evidence/microflow-panel-identity-audit.json` | **FAIL**；事件投递身份未验证，且明确记录文本抽取不含输入值/嵌套弹窗 |
| ④ 最新 CDP 实测 | `<HERMES_HOME>/cache/scratch/panelcheck2.js` 实际执行输出 | **结构部分 PASS**；捕获 18 个标题，18 个捕获面板红字均 0；不覆盖 `RETRIEVE_ARRAY_n3`，也不能替代字段值核验 |

补充契约证据：

- `docs/audit/artifacts/udc-node-evidence/live-rule0043-deduction-audit.json`
- `docs/audit/artifacts/udc-node-evidence/dataflow_mapping_7702563982566312936.json`
- `docs/audit/artifacts/udc-node-evidence/dataflow_mapping_get.json`
- `docs/audit/artifacts/udc-node-evidence/PUBLISH_BUSINESS_EVENT_panel_contract.json`
- `docs/audit/artifacts/udc-node-evidence/real_CALL_APP_SERVICE.json`

## 三、通过节点清单

本轮没有节点达到“四件套齐 + 四层全通过”的最终 PASS，因此**通过节点清单为空**。以下只能列为“结构红字观察到 0”，不能列为验收通过：

| 节点 | CDP 红字观察 | 最终状态 | 原因 |
|---|---:|---|---|
| 创建变量(1) | 0 | UNVERIFIED | 仅文本面板扫描，未完成字段值/契约/语义闭合 |
| 查询单条数据(1) | 0 | UNVERIFIED | 同上 |
| 创建列表(1) | 0 | UNVERIFIED | 同上 |
| 修改列表(1) | 0 | UNVERIFIED | 同上 |
| 列表操作(1) | 0 | UNVERIFIED | 同上 |
| 创建映射组(1) | 0 | UNVERIFIED | 同上 |
| 映射操作(1) | 0 | UNVERIFIED | 同上 |
| 数据转换(1) | 0 | UNVERIFIED | 映射弹窗/嵌套字段值未被 CDP 证据覆盖 |
| 修改变量(1) | 0 | UNVERIFIED | 同上 |
| 更新数据(1) | 0 | UNVERIFIED | 同上 |
| 批量更新数据(1) | 0 | FAIL | 落库 `CHANGE_BATCH_ENTITY_n11.attrs=[]` |
| 插入数据(1) | 0 | UNVERIFIED | 同上 |
| 删除数据(1) | 0 | UNVERIFIED | 同上 |
| 类型转换(1) | 0 | UNVERIFIED | 同上 |
| 子微流程(1) | 0 | UNVERIFIED | `mfService.appName`/`hostPath` 为空，需契约解释或补证据 |
| 自定义服务(1) | 0 | FAIL | 事件投递与其面板文本相同；`CALL_APP_SERVICE.attrs=[]` |
| 事件投递(1) | 0 | FAIL | `PANEL_IDENTITY_UNVERIFIED`，不能证明面板是事件面板 |
| 分支(2) | 0 | UNVERIFIED | 捕获了分支标题，但未完成分支节点/表达式字段级核验 |
| 第一页的记录（`RETRIEVE_ARRAY_n3`） | 未捕获 | FAIL | 落库存在，CDP 标题/面板清单缺失 |

## 四、打回清单

### P0：面板身份与覆盖

1. **节点：事件投递(1)**
   - 证据：`microflow-panel-identity-audit.json` 第 8–13 行。
   - 问题原文：`Different nodes produced identical panel text; click success does not establish panel switch.`
   - 定位：落库 `FIXED20.json` → `nodes[actionType=PUBLISH_BUSINESS_EVENT]`；CDP 证据 → `panels[label=事件投递(1)]`。
   - 建议修法：用节点内部唯一 id/选中态/面板标题或请求参数建立身份绑定；点击后必须读取当前选中节点 id，再验证 `selectEvent`、`eventType`、属性映射等事件专属字段。不能用相同 `innerText` 通过。

2. **节点：RETRIEVE_ARRAY_n3（第一页的记录）**
   - 证据：`FIXED20.json` → `nodes[2]`，`actionType=RETRIEVE_ARRAY`；CDP 本轮输出仅 18 个标题。
   - 问题原文：计划要求 19 类节点逐节点验收；实际 CDP 标题捕获没有“第一页的记录”。
   - 定位：`FIXED20.json:nodes[2]`；`panelcheck2.js` 的标题正则/标题捕获逻辑。
   - 建议修法：按保存 schema 递归枚举节点并以节点 id 驱动点击，不使用画布可见标题数作为覆盖分母；补抓 `RETRIEVE_ARRAY_n3` 面板并记录字段级值。

### P1：必填与业务语义

3. **节点：自定义服务(1) / `CALL_APP_SERVICE_n16`**
   - 证据：`FIXED20.json` → `nodes[actionType=CALL_APP_SERVICE]`。
   - 问题原文/值：`selectMethod.parameter.item.itemType=java.lang.Long`，但 `attrs=[]`；面板文本只显示“参数 小爪实验实体950795V2-ID长整数单条数据”，没有证明参数绑定值已落库。
   - 定位字段路径：`nodes[16].attrs`；服务契约 `nodes[16].selectMethod.parameter`。
   - 建议修法：为 Long 入参绑定一个可追溯的上游长整数值（或按契约明确的流程输入）；保存后回读并核对 `attrs[].value` 的 `outputName/nodeId/id`，再做面板身份复验。

4. **节点：批量更新数据(1) / `CHANGE_BATCH_ENTITY_n11`**
   - 证据：`FIXED20.json` → `nodes[actionType=CHANGE_BATCH_ENTITY]`。
   - 问题原文/值：`attrs=[]`，而节点类型是批量更新。
   - 定位字段路径：`nodes[11].attrs`。
   - 建议修法：若业务上确实只更新零字段，应提供平台契约证据说明其合法性；否则至少配置一个目标字段及来源值，并证明字段不重复赋值、来源不是常量垃圾值。不能以 `isCompleted=true` 代替字段值验收。

5. **节点：子微流程(1) / `SUB_MICROFLOW_n15`**
   - 证据：`FIXED20.json` → `nodes[actionType=SUB_MICROFLOW]`。
   - 问题值：`mfService.appName=null`、`hostPath=null`，虽然有 `id=301785209408604048`、`name=SyncEnumData`、`path=/microflow/SyncEnumData`。
   - 定位字段路径：`nodes[15].mfService`。
   - 建议修法：补齐/回读服务所属应用与服务唯一标识的来源证据；若 null 是平台合法返回值，保存一份接口响应或字节码契约解释，不要靠面板显示“所选微流程服务无参数”推断完整。

### P1：外部残留

6. **节点证据目录整体**
   - 命中原文：`events_own.json` 中“合同档案状态发生值变化时更新合同审批状态”“应收管理”“销售填报事件投递”；`real_map_samples.json` 中“应收计损罚息”“销售考核利润…”；`udcEventListPost_all.json` 存在大量“合同档案/应收/销售”。
   - 定位：上述三个文件的 `caption/appCaption/desc/title/label/entityCaption` 字段。
   - 建议修法：把与本次 `datamigration9000000000000000001` 样板无关的客户业务证据移出本验收证据集，或建立明确的样板对象范围过滤与残留白名单；同时对 `id` 与 `desc/caption/label/title` 两层分别扫描并输出命中路径。当前不能写外部残留=0。

## 五、业务语义与长数字 ID

### 已看到的可追溯链（仅列观察，不升级为 PASS）

- 应用 ID `8704025620829192834` 与多个 DTO/entity fullName 绑定，见 `FIXED20.json`。
- 实体 ID `474806313816300867` 在 `RETRIEVE/RETRIEVE_ARRAY/CREATE_LIST/CHANGE_ENTITY/CALL_APP_SERVICE` 等节点结构中重复出现，并与 `com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795` 关联。
- 服务 md5 `3277002066736383209` 和子微流程 id `301785209408604048` 被落库态记录，但仍需分别绑定到对应接口/服务查询响应，不能仅凭数字存在认定已溯源。
- `FIXED20.json` 文本未命中本轮外部残留词表；这只说明落库态局部扫描干净，不能覆盖全部证据 JSON。

### 语义硬问题

- `CALL_APP_SERVICE.attrs=[]` 与 `Long` 服务参数不匹配闭环。
- `CHANGE_BATCH_ENTITY.attrs=[]` 对“批量更新”语义不完整，至少当前没有字段更新证据。
- `CREATE_MAP` 的 `entries` 有一条 `expText → RETRIEVE_n2.expText`，可见不是空壳；但仍需与其面板值和契约逐字段对账。
- `DATA_MAPPING.mappingRule.mappingRows` 有 3 行，且字段来源/目标各自存在；这是局部进步，不等于整条数据转换面板四件套已闭合。

## 六、与上次验收的差异

上一轮可用记录只到“任务因模型通道 HTTP 503 未执行”，没有一份成功生成的验收报告可供完整对比；因此以下为**可验证差异**，不冒充历史全量差分：

### 进步

- 本轮实际执行了 CDP 刷新后逐节点扫描，得到 18 个可捕获标题；不是只依赖静态 JSON。
- 18 个已捕获面板的红字扫描结果均为 0。
- `FIXED20.json` 已包含 19 个节点类型，包含 `RETRIEVE_ARRAY`、`PUBLISH_BUSINESS_EVENT`、`BRANCH`，节点集合与 P1 计划对齐。
- 事件投递在落库态出现明确 `selectEvent`：`XzhEvtA1`、`source=MICRO_FLOW`、`eventType=IN_APP`，比完全空候选池更进一步。

### 退步/未闭合

- 事件投递的面板身份仍被证据明确判为未验证；不能把红字 0 当作事件面板通过。
- 从落库 19 节点到 CDP 实捕 18 面板仍有覆盖缺口。
- 自定义服务参数与批量更新字段仍为空；四层口径下应继续打回。
- 证据目录仍包含与样板无关的客户业务描述，外部残留层未通过。

## 七、下一步验收门槛（只给审计要求，不执行修复）

1. 重新用 schema 节点 id 驱动 CDP，补齐 `RETRIEVE_ARRAY_n3`，并为每次点击记录：点击前选中 id、点击后选中 id、面板专属字段签名、请求/响应 trace。
2. 单独复验 `PUBLISH_BUSINESS_EVENT_n17` 与 `CALL_APP_SERVICE_n16`，证明二者面板不会复用同一 DOM 文本；事件面板必须读到 `selectEvent/eventType`，服务面板必须读到 `selectMethod/attrs`。
3. 对所有节点执行字段级必填检查：`attrs/entries/mappingRows/selectParam/selectMethod/selectEvent/mfService/conditions` 等按节点类型建立规则，禁止只检查 `redN` 或 `isCompleted`。
4. 对所有长数字 ID 输出来源链：接口 URL/响应字段、对象 fullName 或节点引用、证据文件路径；孤立数字一律 UNVERIFIED。
5. 证据目录执行 `id + desc/caption/label/title` 双层词表扫描，并按文件/JSONPath 记录命中；未清理或未白名单化前不得宣称外部残留=0。

---

**最终判定：FAIL（结构红字局部 PASS；四层验收未通过）。**

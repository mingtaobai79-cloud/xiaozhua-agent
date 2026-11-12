# 门1 修复清单（STATIC · 零写交付物）

> HANDOFF：`menu-gate1-fix-plan` + `-revision-b` + `-revision-c`（以 revision-c 为最终版）
> 角色：implementer（菜单域）· 2026-10-18 00:38–00:48 GMT+8 · 环境 test2 · 应用 `datamigration9000000000000000001`
> **零写、零 HTTP、零浏览器、零凭据、未触发发布**。全部 MySQL SELECT + 既有反编译产物阅读。
> 取数时刻：**2026-10-18 00:39:19 – 00:45:20**（各表标注具体时刻）
> 证据等级：LIVE（DB 实测）· STATIC（字节码/javap/CFR）· 推断（明确标注）

---

## 0. 三句话结论（与 HANDOFF 预期有实质偏差，请先读这段）

1. **A 部分：105 处类名串命中已逐处定位（见 §1.2）。但「目标值 = 数字 entity id」这一列对其中绝大部分不成立** ——
   我做了健康应用对照：可通且发布成功过的 3 个应用里，`structure.key` 同为**类全名**形态（1411 / 938 / 302 处），
   `structure.relationEntity` 同为**数字**形态，`page_schema.dataSource.entity` 同为 **id+fullName 并存**。
   ⇒ **本应用的数据形态与健康应用完全同构，这些类名串是平台正常形态，不是缺陷。**
   **清理它们会把正常数据改坏。**
2. **真正会被 `Long.parseLong` 吃掉的是 `uniformityParams.paramId`（且 `paramCategory=="Entity"`）。**
   本应用该形态命中 **0 处**（全库 316 行有 Entity 类，paramId 845 处全为整数、0 处类全名）。
   ⇒ **§1.2 的 105 处里，没有一处落在 NFE 的真实输入点上。**
3. **B 部分（rg）：除 HANDOFF 已定的「降级为 P1 数据卫生」外，我实测到一条更硬的事实** ——
   `udc_page_info.relation_group_id` 在每次复制时**都生成了新值**（9 个页里 6 个副本全不等），
   只有 `page_schema.relationGroupId` 照抄源值。**重映射在表列层是做了的，只有 schema 内嵌副本没做。**
   这与 auditor「平台索引每次创建都新生成、天然唯一」完全吻合，进一步证伪「rg 阻断发布」。

---

## 1. A 部分：类名串清理清单

### 1.0 先说「目标值」这一列的判定依据（这是本清单最关键的一节）

HANDOFF 要求目标值填 `474806313816300867`（实体数字 id）。我按字段语义逐类核验，**只有一类字段确实该存数字**：

| 字段语义 | 应存形态 | 判定依据 |
|---|---|---|
| `structure.key` / `structure.entity` | **类全名**（`com.seeyon.<app>.domain.entity.X`） | 模板层 `EntityFileTemplate` 用它生成 Java 类型；健康应用 1411/938/302 处全为全名 |
| `*.relationEntityFullName` / `*.filterFullName` / `*.entityFullName` / `*.fullName` | **类全名**（字段名就叫 FullName） | 同上；健康应用同构 |
| `page_schema.dataSource.entity.id` | **数字** | 健康应用 112/80/105 处均为 `id`(数字) + `fullName`(全名) **并存**，本应用 23 处同样并存 |
| `page_schema.*.fullName`（列/字段） | **类全名 + 字段名**（`...XzhExp950795.expText`） | 与 `dataFieldId`(数字) 并存 |
| **`uniformityParams.paramId`（paramCategory=="Entity"）** | **数字** ← **唯一真会被 parseLong 的** | `EntityImporterBase.getNewEntityDto:488` 直接 `Long.parseLong(paramId)` |

⇒ **HANDOFF 的「目标值统一填数字 id」只对最后一类成立，而本应用该类命中 0。**

### 1.1 健康应用对照（决定性反证，取数时刻 2026-10-18 00:45:20）

```sql
SELECT data_schema FROM udc_microflow_info WHERE app_id = ?;   -- 逐条 JSON 展开 structure 节点
```

| 应用 | 发布状态 | 微流程数 | `structure.key`=类全名 | `structure.key`=数字 | `relationEntity`=数字 |
|---|---|---|---|---|---|
| **本应用 8704025620829192834** | 失败 | 47 | **30** | 0 | 30 |
| app9000000000000000001 | 可通 | 1788 | **1411** | 0 | 1397 |
| xiangmuguanli9000000000000000001 | 可通 | 716 | **938** | 0 | 930 |
| znxmglptcopy5791640252914287064 | 可通 | 411 | **302** | 0 | 296 |

`page_schema.dataSource.entity`：

| 应用 | 检查页数 | id+fullName 并存 | 仅 fullName | 仅 id |
|---|---|---|---|---|
| 本应用 | 17 | **23** | 0 | 0 |
| znxmglpt3289 | 40 | **112** | 0 | 0 |
| xiangmuguanli | 40 | **80** | 0 | 0 |
| znxmglptcopy | 40 | **105** | 0 | 0 |

⇒ **本应用与健康应用形态完全一致。这些不是「残留污染」，是平台的序列化格式。**

### 1.2 105 处命中的完整定位（LIVE，取数时刻 2026-10-18 00:39:19）

#### A-1 微流程 `data_schema`：7 条 / 91 处

| 对象 id | 名称 | caption | create_time | 命中 | 归本域? |
|---|---|---|---|---|---|
| 1524985498115296151 | xzhSvcEvtBpDA | 小爪标品事件监听 | 2026-10-14 17:31:17 | 7 | 实验残留 |
| 862673936068342178 | xzhSvcDefK4Ge | 小爪标品服务定义 | 2026-10-14 17:31:17 | 15 | 实验残留 |
| -8675485534859429311 | xzhSvcSchcHXa | 小爪标品定时任务 | 2026-10-14 17:31:18 | 10 | 实验残留 |
| -5161505652062878096 | xzhRestMf | 小爪REST微流程 | 2026-10-15 18:18:00 | 9 | 实验残留 |
| -1014184770817921434 | xzhFinalAllNodes | 小爪标准微流程-全节点流转(最终) | 2026-10-16 12:18:41 | 19 | 实验残留 |
| 4774717078364917047 | xzhFront27390 | 小爪页面规则-全前端节点 | 2026-10-16 13:09:50 | 17 | 实验残留（source_id=1520098474917276520） |
| -3790333238868911627 | xzhStdReal31046 | 小爪标准微流程-真数据全节点 | 2026-10-16 14:10:45 | 14 | 实验残留 |

> **P1/P2 的 14 条复制规则（m2610171518*/m2610171541*）不含该类名** —— 已核，7 条命中全部是 xzh 前缀实验对象。

**字段路径明细（18 类，含出现总数）**：

| # | JSON 路径模式 | 出现 | 语义 | 应存形态 | 目标值？ |
|---|---|---|---|---|---|
| 1 | `$.nodes[*].structure.key` | 30 | 节点实体类型 | 类全名 | **不适用（保持）** |
| 2 | `$.nodes[*].structure.entity` | 30 | 同上 | 类全名 | **不适用（保持）** |
| 3 | `$.endNode.entityObject.key` | 4 | 结束节点实体 | 类全名 | 不适用 |
| 4 | `$.endNode.entityObject.entity` | 4 | 同上 | 类全名 | 不适用 |
| 5 | `$.nodes[*].selectParam.relationEntityFullName` | 4 | 选择器关联实体 | 类全名 | 不适用 |
| 6 | `$.endNode.value.selectParam.relationEntityFullName` | 1 | 同上 | 类全名 | 不适用 |
| 7 | `$.nodes[*].value.selectParam.relationEntityFullName` | 2 | 同上 | 类全名 | 不适用 |
| 8 | `$.nodes[*].mappingRule.mappingRows[*].targetField.path[*].entityFullName` | 5 | 映射目标 | 类全名 | 不适用 |
| 9 | `$.nodes[*].mappingRule.mappingRows[*].value.reference.path[*].entityFullName` | 4 | 映射来源 | 类全名 | 不适用 |
| 10 | `$.nodes[*].attrs[*].attrType.filterFullName` | 2 | 前端属性过滤器 | 类全名 | 不适用 |
| 11 | `$.nodes[*].items[*].element[*].filterFullName` | 1 | 同上 | 类全名 | 不适用 |
| 12 | `$.nodes[*].items[*].value.selectParam.relationEntityFullName` | 1 | 选择器 | 类全名 | 不适用 |
| 13 | `$.nodes[*].selectParam.fullName` | 1 | 选择器 | 类全名 | 不适用 |
| 14 | `$.nodes[*].mfService.output.relationEntityFullName` | 1 | 服务输出 | 类全名 | 不适用 |
| 15 | `$.nodes[*].conditions[*].nodes[*].items[*].element[*].fullName` | 1 | 条件元素 | 类全名 | 不适用 |
| 16 | `$.nodes[*].conditions[*].nodes[*].items[*].element[*].filterFullName` | 1 | 同上 | 类全名 | 不适用 |
| 17 | `$.nodes[*].event.params[*].children[*]…[*].relationEntityFullName` | 4 | 事件参数（4 层嵌套） | 类全名 | 不适用 |
| — | **合计** | **91** | | | **0 处需改** |

#### A-2 页面 `page_schema` / `draft_page_schema`：3 页 / 14 处

| page_id | page_url | caption | schema_id | create_time | master_entity_ids | 命中 |
|---|---|---|---|---|---|---|
| 1805559981642060210 | xzhdetail958033 | 小爪实验详情958033 | -4517729194263201547 | 2026-10-14 14:07:12 | 474806313816300867 | 2（schema+draft 各 1） |
| 1520098474917276520 | xzhpage951440 | 小爪实验页面951440 | 8275986735913209 | 2026-10-14 12:17:19 | 474806313816300867 | 10（各 5） |
| -8121300410989827961 | xzhdetail958006 | 小爪实验详情958006 | 8396450323065814105 | 2026-10-14 14:06:46 | 474806313816300867 | 2（schema+draft 各 1） |

**字段路径明细**：

| page | JSON 路径 | 出现 | 同节点是否已有数字 id | 目标值？ |
|---|---|---|---|---|
| xzhdetail958033 / xzhdetail958006 | `$.childById.udcForm_xI10_1699879531349.dataSource.entity.fullName` | 各 2 | ✅ 同节点 `entity.id = 474806313816300867` **已存在** | **不适用（已并存）** |
| xzhpage951440 | `$.childById.udcDataGridView_xzh1.dataSource.entity.fullName` | 各 1 | ✅ 同上已存在 | 不适用（已并存） |
| xzhpage951440 | `$.childById.udcDataGridView_xzh1.settings.columns[*].fullName` | 各 2 | ✅ 同节点 `dataFieldId = 8016904624316689195`（数字） | 不适用（已并存） |
| xzhpage951440 | `$.childById.udcDataGridView_xzh1.dataSource.fields[*].fullName` | 各 2 | ✅ 同节点 `id = 8016904624316689195` | 不适用（已并存） |

**实测原始值**（证明 id 与 fullName 并存）：
```json
"entity": {"id":"474806313816300867","name":"xzhExp950795",
           "fullName":"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795",
           "caption":"小爪实验实体950795V2","category":"ENTITY", ...}
"fields[0]": {"id":"8016904624316689195","name":"expText","fieldPath":["8016904624316689195"],
              "fullName":"...domain.entity.XzhExp950795.expText", ...}
```
⇒ **数字 id 本来就在同一节点上，不存在「只有全名、缺 id」的情况。**

### 1.3 A 部分的实际可用动作（供决策，不建议直接执行）

| 方案 | 说明 | 我是否建议 |
|---|---|---|
| **A0 · 不动（推荐）** | 105 处全是平台正常形态，与健康应用同构；改它们会破坏序列化格式 | ✅ 推荐 |
| A1 · 只清 `uniformityParams.paramId` 里的类全名 | **本应用命中 0 处**，无对象可清 | 无意义 |
| A2 · 把 structure.key 等改成数字 id | 会与平台序列化格式冲突，健康应用全是全名 | ❌ 禁止 |

**⇒ A 部分结论：本应用数据里「找不到需要清理的类名串」。NFE 的输入源不在上述 105 处中。**

---

## 2. B 部分：relationGroupId 现状（已按 revision-b/c 降级）

### 2.0 头部两句话（HANDOFF 要求必须写）

> **① 本项修复的是 P1 缺陷本体（复制页 schema 内部自引用正确性），属数据卫生。**
> **② 本项与门1 解阻无因果关系** —— 184 个检测项里无 relationGroupId 唯一性校验，
> `DetectionManager:384` 判据只有 `errorCount>0`，rg 在检测代码里只做 PC/Mobile 配对（组内无 MOBILE 静默跳过）。
> （依据：auditor 反编译 VERDICT + main 撤回段 C）

### 2.1 实测现状（取数时刻 2026-10-18 00:44:57）

| RG | page_id | page_url | page_info.relation_group_id | schema.relationGroupId | 表列是否重映射 |
|---|---|---|---|---|---|
| 3676836814625326282 | 992522359796286320 | sjypzxxListPagecopy（**源**，10-12） | 3676836814625326282 | 3676836814625326282 | — |
| | 1185161788250969507 | sjypzxxListPagecopycopy | **186634189171591623** | 3676836814625326282 | ✅ **已重映射** |
| | -8358257041803639157 | sjypzxxListPagecopycopycopy | **7855292447662599427** | 3676836814625326282 | ✅ **已重映射** |
| -6767432651261196955 | 114216775019154694 | qyfapzlb（**源**） | -6767432651261196955 | -6767432651261196955 | — |
| | 844278122493924338 | qyfapzlbcopy | **-1703662691102987065** | -6767432651261196955 | ✅ |
| | 540101808703999634 | qyfapzlbcopycopy | **-4207444815775121714** | -6767432651261196955 | ✅ |
| 7427956962460123794 | 7286622650788629332 | qyfapzxq（**源**） | 7427956962460123794 | 7427956962460123794 | — |
| | 3254255197550241742 | qyfapzxqcopy | **1143568887012610676** | 7427956962460123794 | ✅ |
| | 8267428021549491279 | qyfapzxqcopycopy | **-5269791848343575650** | 7427956962460123794 | ✅ |

**字段路径**：`page_schema` **顶层** `$.relationGroupId`（唯一一处，非嵌套）。`draft_page_schema` 同构。

### 2.2 ★ 本轮新增事实（HANDOFF 未预期）

**`udc_page_info.relation_group_id` 在 6/6 副本上全部生成了新值**，与新值互不相同、也与源不同；
只有 `page_schema.relationGroupId` 照抄源值未更新。

⇒ 修正 P1 缺陷的**准确表述**：不是「relationGroupId 完全没重映射」，
而是 **「表列 `udc_page_info.relation_group_id` 重映射了，但页面 schema 内嵌的 `$.relationGroupId` 副本没跟着更新」——二者不一致**。
这与 auditor「平台索引 udc_page_info.relation_group_id 每次创建都新生成、天然唯一」完全吻合。
**P2 的 ROUTE 里「`schema.relationGroupId` 照抄」这一条观察是对的，但「未重映射」应限定为 schema 内嵌副本。**

### 2.3 建议（不执行）

- 属 P1 数据卫生，**优先级低于 A/D**；且修复需同时改 `page_schema` + `draft_page_schema` 两处，共 6 页 × 2 = 12 处。
- 目标值方案：`page_schema.$.relationGroupId` ← 对应 `page_info.relation_group_id` 的现有值（该值已唯一，无需新生成）。
- **不建议在本轮做**：与门1 解阻无关，且改动会污染 P1/P2 的取证对象。

---

## 3. C 部分：实验对象处置对比表

| 方案 | 动作 | 优点 | 风险 | 可逆性 |
|---|---|---|---|---|
| **清串保留** | 按 §1.2/§2.1 改值 | 保留数据、可验证 | ⚠ **经本轮实测：§1 无对象可清（105 处均为正常形态）**；仅 §2 的 12 处 rg 内嵌副本可改，而它与门1 无关 | 高（值可改回） |
| **删除对象** | 删 xzh 实体 + 实验页 + 实验微流程 + 全部 copy 副本 | 干净、改动面小；可一次性消掉「xzh 类名串是否存在」这类疑问 | ⚠ **删 6 个副本页含 P1/P2 取证对象**（P1 VERDICT 用的正是它们），删后本域 P1/P2 不可复查；`xzhVerifyEntity` 虽零引用但同组；删除不可逆 | **低（不可逆）** |
| **仅删 xzh 实验对象、保留 6 副本页**（新增第三选项） | 删 2 个 xzh 实体 + 3 个 xzh 实验页 + 7 条 xzh 微流程；6 个 copy 副本页原样保留 | 清掉实验残留、保住 P1/P2 取证对象；且 A 部分本就无需改值 | 删除不可逆；但对象全是实验残留、非业务数据 | 低（不可逆） |

**注（HANDOFF 要求写明）**：P1/P2 的取证对象 = 3 副本菜单 + 6 副本页 + 14 条复制规则。
若删除，本域 P1/P2 的可复核性受损。**我新增的第三选项专为避免此风险**，建议由 HUMAN 在知情后选。

---

## 4. D 部分：验证方案（按 revision-c「发布即实验」重写）

### 4.1 前提（必须写在方案头部）

- 当前检测快照 **0 ERROR / 6 WARN**（01:20 快照）→ 按 `DetectionManager:384` 判据（`errorCount>0`）应绿；
- **但 22:56 真红过一次，原因 UNVERIFIED（明细被覆盖）。「当前绿」≠「当时绿」**，发布前不得引用快照当保证；
- NFE 链路归属 = **UNVERIFIED**（auditor 已定：抛点在导入/复制 API 链，发布链内的触发点未证）。

### 4.2 三叉验证（TEST 发布本身就是链路归属的判定实验）

```
执行修复（按 HUMAN 裁决的方案）
  → 触发一次 TEST 发布（deploy_type=0）
  → 看结果，三叉：
     ┌ 成功
     │   → 门1 解除 + 「NFE 不在发布链」自动定案
     │   → 镜像验证（§4.3）→ 上架（另案）→ P3-c 端到端
     ├ 失败 + NFE 堆栈
     │   → 「发布链内嵌导入步骤」定案
     │   → 按堆栈定位下一层；auditor 日志授权保留作取证
     └ 失败 + 一致性 ERROR
         → 读 Redis DetectionError 新明细，逐条对清单
         → ⚠ 不要按已撤回的 rg 假设对（184 项无 rg 维度）
```

### 4.3 发布成功后的镜像验证（闭环标准）

| 检查项 | 期望 | 依据 |
|---|---|---|
| `test2:Metadata:Page:{app}` fields | **24 → 31** | 差集 7（6 副本页 + `_deduct`）闭合 |
| `test2:Metadata:JSON:MD5:{app}` MicroFlow 分片 | 增加 18 条规则对应分片 | REV7 §9.2.4 |
| `Metadata:Service` field | `1.0.14` → 新版本 | 锚点对齐 |
| P3-c | 门户直开 `/main/portal/{app}/qyfapzlbcopy` 渲染 | 上架后 |

### 4.4 一件必须说明的事

**若 A 部分按 §1.3 判「无对象可清」，则「清串 → 发布」这条路本身无从执行。**
此时 D 方案的入口应改为：**直接触发一次 TEST 发布**，看是否仍报 NFE。
- 若仍报 NFE → 说明 NFE 与类名串无关，链路归属需靠服务端应用日志（auditor 已获授权）；
- 若不报 NFE 且成功 → 说明 22:56 那次失败是**一次性/已自愈**，门1 自然解除。

---

## 5. 附录：平台侧缺陷登记（不属本域修复范围）

| 项 | 内容 |
|---|---|
| 位置 | `com.seeyon.udc.autocode.transport.in.entity.EntityImporterBase#getNewEntityDto`（udc-biz 5.3.517，字节码偏移 488） |
| 缺陷 | `String newEntityId = uniformityParams.getParamId(); return entityDtoMap.get(Long.parseLong(newEntityId));` —— **无 `NumberUtil.isNumber` 守卫** |
| 同族对照 | `:276` 有 targetGuid null 检查；`:332`（`lambda$doImportInfo$8`）有 `NumberUtil.isNumber` 前置过滤；**唯 :488 无任何守卫** |
| 后果 | 当 `paramId` 为非数字串（如实体全限定名）时抛 `NumberFormatException`，消息形态即 `For input string: "com.seeyon....entity.Xyz"` |
| 建议修复 | 加 `NumberUtil.isNumber` 守卫；非数字时 `log.error` + 返回 null（或抛明确业务异常），避免把实体全名当 id 解析 |
| 归属 | **平台面代码**（客开/平台补丁），需 HUMAN 决策，不进本域切片 |
| 定级 | STATIC（javap 实证代码形态）。**但「23:43 那次是否由它抛出」= UNVERIFIED**（auditor 已定抛点在导入 API 链，发布链内触发点未证） |

---

## 6. 未做 / 不给结论

1. 未执行任何修复（HANDOFF 边界）。
2. 未取 23:43 服务端应用日志（auditor 已获授权，避免重复劳动）。
3. **未解释 §2.4 矛盾**（23:43 是 RELEASE 记录，但 NFE 抛点链只挂在导入 API）—— UNVERIFIED，等日志。
4. 未复算 P1/P2 复制规则的 14 条内容（REV7 已做，本轮不复）。
5. 未核 `xzhVerifyEntity` 的 11 个属性是否有同类问题（它被引用数=0，本轮未展开）。

## 7. 边界与副作用

- **零 DB 写**（全部 SELECT）、零 HTTP、零浏览器、零凭据、未触发发布、未删未改任何对象。
- 未跨域：只查授权应用 + 为对照查了 3 个可通应用的只读统计。
- 临时脚本（只读，保留）：`_fixplan_scan.py` / `_fixplan_semantics.py` / `_check_paramcat.py` / `_check_entity_cat.py` / `_attr_entity_paramid.py` / `_attr_paramid_fix.py` / `_rg_status.py` / `_healthy_compare.py` / `_dump_values.py` / `_find_attr_hit.py` / `_dump_expr.py`

# docs/audit/udc-semantics/ 索引

## 这个目录是什么

UDC 语义补全线（2026-10 ~ 2026-11）的**取证过程与结论**：前端交互层实测、后端字节码反编译、
LIVE 探测结果、修复方案与审结。99 份 `.md` + 27 份 `.json`。

**它不是事实库。** 环境无关的结论已归位到 `core/facts/`；本目录保留「怎么测出来的」、
时点快照，以及尚未归位的独有内容。

---

## 一★、**先读这一节：这个目录里有一批结论已经被自己推翻了**

99 份里 **24 份**带更正标记，合计 **72 处**（`menu-copy-p2-auditor-verdict.md` 一份就 16 处）。
**顺序读会把死结论当活结论用**，而这个目录的死结论会直接改掉处置方向——
最典型的是 `menu-copy-p2-auditor-verdict` 那条：把「取不到证据」的成因写成
「取证能力/通道问题」，于是**处置变成"换通道/换入口"**，而真因是**平台授权前置缺失**
（token 黑名单触发原生 alert 锁死 renderer 主线程 + 应用未上架）。
⇒ **判据：机制归因错了，处置方向会整个跑偏，而且看起来很像在干活。**

### 更正表（按"会不会让人做错事"排序）

| # | 原判断（已作废 / 已撤回） | 更正为 | 代价 | 原文 |
|---|---|---|---|---|
| ① | 页面点击侧旁证取不到的成因 = 「取证能力/通道问题」 | **平台授权前置缺失**（token 黑名单触发原生 alert 锁死 renderer 主线程）+ **第二道阻断：应用未上架** | **最贵**：会让人去换通道/换入口，两条路都不通 | `menu-copy-p2-auditor-verdict` L18 / §6.2 / §6.5 |
| ② | 「JS 主线程挂死 / 单页路由死锁」 | **实测推翻**，真因见 ① | 同上（同一个病的两种说法） | `menu-runtime-route` L25 |
| ③ | §8.1 原声明（auditor 判 **FAIL**） | **撤回并更正**；原文标注「已作废，不得再引用」 | 会影响后续 P3 处置 | `menu-runtime-route` §8.1（L167–169） |
| ④ | 「依赖 `xzhExp950795` 创建才导致一致性检测失败」 | **连带撤回**：该对象创建于 10-14 12:06:35，而失败在它之前已有 2 条（10-12） | 时序方向错，会去查错对象 | `menu-runtime-route` L412 |
| ⑤ | 「99 未归位 op 的归属构件**不在本地仓库**」 | **表述不准确**：本地/Artifactory **有**事实源 | 会放弃一个其实能做的方向 | `COMPONENT-RELOCATION` §0（L13–15） |
| ⑥ | 跨构件归位 **32** 条 / 契约权威总量 657、663 | **27** 条（5 条改判回 udc-web）/ **674**；旧记 657、663 均作废 | 分母错会让覆盖率全错 | `COMPONENT-RELOCATION` L7–8、§1.5、L240 |
| ⑦ | 余量 **62** 条 | **60** 条（raw/corrected 口径更正）；另有「余 67 → 66」 | 同上 | `COMPONENT-RELOCATION` L59、§6.1 |
| ⑧ | 「形态判据」成立 | **已证伪**（本轮自我更正） | — | `COMPONENT-RELOCATION` §6.2 |
| ⑨ | 「两副本全部 **16** 条 microflow 引用」 | **14**（8 事件/7 引用 ×2）——**原 16 是事件数与引用数串位** | 会得出错误的重映射结论 | `menu-copy-events-migration` L49 / §162 |
| ⑩ | 弹窗选择页复制源 = `5175…` | **`9925…`**（四元组 `9925 == 1185 == -8358` 相等；`5175` 4 事件 ≠ `9925` 5 事件） | 会复制错源 | `menu-copy-events-migration` L80 / §163 |
| ⑪ | `pods/exec` **forbidden** | 第十八轮：**ALLOWED**；第二十一轮 LIVE 复检：**回到 DENIED**（三个 verb 全 `False`） | **两头都可能读错**，必须看时点 | `COMPLETION-METHOD-PROMPT` L82–88 |
| ⑫ | 「已归位 32 条 32/32 命中」当阳性对照 | **实测仅 5/32** —— 阳性对照本身就站不住 | 会让整条管线显得"已验证" | `COMPLETION-METHOD-PROMPT` L91 |
| ⑬ | `MetadataController`「**12** 端点」 | **105 mapping / 99 op 面**；旧稿是**假阴性**，源于一份不带 `-v` 的残缺 `javap` 文本 | **假阴性的典型成因：工具用法错** | `RUNTIME-METADATA-CONSTRAINTS` L39 |
| ⑭ | 「`674` 端点」当平台操作面全量 | **`674` 只是 udc-web 单构件视图** | 会低估整个平台面 | `RUNTIME-METADATA-CONSTRAINTS` L68 |
| ⑮ | 「空目录无处设默认页」 | CFR 判据是「无子节点 **或** 无 `type==MENU` 的子节点」⇒ 子节点全是 PAGE 也算"空目录"；**真实充分条件 = 无子页面可指向** | 判据边界错，会误报/漏报 | `FIX-COMPLETE-entity-rule-menu` L69 / §5 |
| ⑯ | `MICROFLOW-EVENT-OBJECT-SEMANTICS` 早期「空壳形态 B」；main D18 的 `occurrence=255 / unique=254 / 唯一重复键` | **D22 终裁正式撤回**，并确认 main 的 `walk(ds)` 与本档早期遍历缺陷**同源**（所谓"独立取证"**不独立**） | **"独立"取证其实同源** —— 这条最值得记 | `MICROFLOW-EVENT-OBJECT-SEMANTICS` L92 / L147 |
| ⑰ | `POST .../expression/schema` 传 `paramType:"ENTITY"` 的旧口径 | 2026-10-15 就地更正为 `{ids:["<实体id>"], paramType:"ENTITY", upsource:true, serverName:"udc"}` | 照旧写法调不通 | `ENTITY-PAGE-INVENTORY` L266 |
| ⑱ | `RETRIEVE_ARRAY` 必填（前端推断） | **按 `fetchType` 分**——后端字节码否决前端推断 | 前端推断不能当契约 | `MICROFLOW-NODE-BACKEND-CONSTRAINTS` §3 |
| ⑲ | `full_path` 拼接方式 | 已改为**恒拼接** `class_mapping`（657 方法中 **159 个** 被纠正），加 8 项回归护栏 | — | `FULL_PATH-CONCAT-DEFECT` L58 / L70、`S7-WRITE-CHAIN-LIVE` L25 |
| ⑳ | P1「两处证据需更正」：事件随迁、`1452→1336` 口径 | 结论仍成立（不匹配数 = **1**，指向同一节点），**数字与覆盖范围更正** | — | `menu-copy-p1-auditor-verdict` L142 / L219 |
| ㉑ | DEPLOYED-STATE 「方法/映射存在性」措辞 | 「方法存在、**映射字面不存在**」 | 会导出去改对的地方 | `DEPLOYED-STATE-VERDICT` L56 |
| ㉒ | 变更脚本锚点失效时记「作废」继续跑 | **不允许**：静默作废会让「变异没执行」看起来像「变异执行了但闸门没抓到」 | **闸门可信度**问题（D72 实测） | `MIGRATION-SCHEDULER-DISPATCH.contract` L291–294 |

| ㉓ | `udc_filter_plan` 被归类为"页面规则" | **分类错误，必须更正** | 会去错的地方找规则 | `UNDERSTANDING-CHECKPOINT` L167 |
| ㉔ | `MICROFLOW-DATASOURCE-TYPES` 记「历史 5 种」 | 漏了 `METADATA` / `MESSAGE` / `OTHER` | 枚举不全 | `MICROFLOW-DATASOURCE-TYPES` L12 |
| ㉕ | `FRONTEND-OP-TO-ENDPOINT-ALIGNMENT` 的「精确对齐 / 仅前端」 | **部分作废**：那是 **op 名模糊匹配**得出的 | **模糊匹配当精确对齐** —— 本目录第三大错源 | `FRONTEND-OP-TO-ENDPOINT-ALIGNMENT` L3 |
| ㉖ | `08100` 旧措辞 | 真实充分条件已更正（见 §4） | — | `MENU-FUNCTIONNODE-CONSTRAINTS` L86 |
| ㉗ | 用 `location.hash` 拼路由 | 会把 appId 污染成 `8704…#/app-design/...`，后端报 `BOOT_3000 For input string`（**capture2 全批作废**） | 整批取证白跑 | `NAV-LIVE-CAPTURE-20261012` L12 |
| ㉘ | `REST-EXPOSURE-MECHANISM` 上轮的负面结论 | 本文件 §4 **诚实标注更正** | — | `REST-EXPOSURE-MECHANISM` §4 |

### 三条反复出现的错因（读之前记住）

| 错因 | 本目录实例 | 判据 |
|---|---|---|
| **把"取不到"归因给通道/能力** | ①②③ | 取不到先查**授权前置**，再查工具；「工具不行」是最省事也最常错的解释 |
| **口径错（分母/串位/单位）** | ⑤⑥⑦⑨⑭⑳ | 任何比例/覆盖率，先问"分母是谁"；**事件数与引用数会串位** |
| **"独立取证"其实同源** | ⑯⑫ | 独立性要看**遍历实现**是否同一份代码，不看是谁跑的 |

### 两条"自我更正"比结论更有价值（保留原文，不要清理）

- `COMPLETION-METHOD-PROMPT` L91：`COMPONENT-RELOCATION` 先用「32/32 命中」当阳性对照，
  实测 `5/32` —— **阳性对照自己塌了**。这类记录保住了整条管线的可信度边界。
- `menu-copy-p2-auditor-verdict` §6.2 / §6.5：同一件事**连续二次更正**（23:20 → 23:32），
  第二次才发现还有第二道阻断。**一次更正往往不够。**

---

## 二、MICROFLOW-*（34 份）：与 facts 的分工，实测裁决


34 份都是**逐节点取证**，`core/facts/udc/microflow/node-*.md`（22 份）是**结论已归位的事实格**。
两者不是重复，是**层不同**：

| 层 | 位置 | 内容 |
|---|---|---|
| 事实（消费方直接读） | `core/facts/udc/microflow/node-<x>.md` | 运行时契约、构造器修正、验证记录、未覆盖项 |
| 取证（追溯用） | 本目录 `MICROFLOW-<X>-CONTRACT.md` | **前端交互层**：addNode 默认态必填、字段联动、值域全枚举、dataSchema 回读体、提交路径坑 |

逐 actionType 核对 facts 侧有无独立事实格（2026-11-07 脚本映射，目标文件存在性已断言）：

| 有 facts 对位（10 个 actionType） | 无 facts 对位（12 个） |
|---|---|
| BREAK -> `node-break.md`<br>CALL_APP_SERVICE -> `node-call-app-service.md`<br>CHANGE_BATCH_ENTITY / CREATE_BATCH_ENTITY -> `node-batch-entity.md`<br>CHANGE_LIST -> `node-change-list.md`<br>CREATE_ENTITY -> `node-insert-entity.md`<br>DELETE_ENTITY -> `node-change-delete-entity.md`<br>LIST_OPERATION -> `node-list-operation.md`<br>PUBLISH_BUSINESS_EVENT -> `node-publish-event.md`<br>RETRIEVE_ARRAY -> `node-retrieve-array.md` | CHANGE_ENTITY、CHANGE_VARIABLE、CONVERT_DATA、CREATE_MAP、CREATE_VARIABLE、CUSTOM_ERROR、DATA_MAPPING、FOR、FOR_EACH、MAP_OPERATION、RETRIEVE、EXPRESSION_EDITOR |

「无对位」的含义：该 actionType 在 `core/facts/udc/microflow/` 里只出现在
`capability-matrix.md` / `dataflow-and-node-matrix.md` 这类**矩阵行**，没有独立事实格 ——
**本目录这几份是唯一来源。**

「有对位」也不等于重复。抽两对实测行覆盖率：`BREAK` **0.13**、`RETRIEVE_ARRAY` **0.17**。
facts 讲运行时陷阱（`type` 必须是 `BREAK` 不能是 `ACTIVITY`、删除流程不停已注册定时任务；
分页 pageInfo 三坑），audit 讲前端交互（只能在循环体内添加、提交路径与普通节点不同；
4 种查询方式字段联动、OTHERS 4 种聚合矩阵）。

**结论：34 份没有一份可判定为「已并入 facts 的重复品」 -> 不合并、不移动。**

## 三、全目录分类（脚本实测计数）

> **口径**：本表 8 行合计 **98 份 = 目录下除 `README.md` 外的全部 `md`**。
> 标题里常说的「99 份」是**含 `README.md`** 的目录总数 —— 两个数差 1，不是矛盾。
> 前缀匹配**区分大小写**：`MICROFLOW-` 34 份不含小写的 `microflow-source-audit.md`
> （后者归「其他」）。在 Windows 上用 `glob("MICROFLOW-*.md")` 会连它一起数出 35，
> 那是 glob 不区分大小写，不是目录里有 35 份。

| 组 | 份数 |
|---|---|
| `MICROFLOW-*` 节点契约 | 34 |
| 菜单/导航（`MENU-` `NAV-` `menu-` `FUNCTION-MAP` `INTERACTION-TABLES` `SETTINGS-TABS`） | 14 |
| 域机制（`ENTITY-` `RULE-` `PAGE-` `SERIALNUMBER-` `RUNTIME-` `PLUGIN-` `CONDITION-` `DATADICT-`） | 13 |
| 部署/端点面（`DEPLOYED-` `COMPONENT-` `REST-` `GRAPHQL-` `PLATFORM-`） | 7 |
| 前端（`FRONTEND-` `frontend-`） | 7 |
| 缺陷根因（`FIX-` `GATE1C-` `ENGINE-FAIL` `FULL_PATH-`） | 6 |
| 流水/方法/检查点（`PROGRESS.md` `COMPLETION-METHOD-PROMPT.md` `UNDERSTANDING-CHECKPOINT.md`） | 3 |
| 其他（`S7-*` 三份、`*source-audit` 四份、`APP-*` `BPM-*` `FLOW-*` `STORAGE-*` `UDC-MAINLINE-AUDIT` `MIGRATION-SCHEDULER-DISPATCH` 等） | 14 |
| **合计** | **98** |

`DEPLOYED-COMPONENT-TAGS.json` 被 `tests/udc/test_deployed_tags_version_audit_alignment.py`
字节读取，改它必须同步改 `docs/audit/agent-version-audit.md` 2.1 节。

## 四、被代码读取的 13 份 —— 位置锁定，不得移动

判据：`git grep "udc-semantics/<文件名>"` 命中 `components|core|tools`

| 文件 | 引用处 |
|---|---|
| `SETTINGS-TABS-CALLCHAIN.md` | `components/udc/deploy_chain_model.py`、`components/udc/setting/settings_tab_model.py` |
| `ENTITY-PAGE-INVENTORY.md` | `components/udc/entity_page_model.py` |
| `RULE-DOMAIN-SCOPE-CONSTRAINTS.md` | `components/` 与 `tools/` 各 1 处 |
| `flow-excel-source-audit.md` | `components/` 2 处 |
| `MICROFLOW-PARAMS-TAB-DATACHAIN.md` | `components/udc/live_write_templates.py`、`core/facts/udc/microflow/ref-and-condition-contract.md` |
| `MICROFLOW-BUSINESS-EVENT-TRIGGERS.md` | `components/udc/live_write_templates.py` |
| `MICROFLOW-SERVICE-AND-ACTIVITY-NODES.md` | `components/udc/live_write_templates.py` |
| `MENU-FUNCTIONNODE-CONSTRAINTS.md` | `core/` |
| `FIX-PLAN-entity-rule-menu.md` | `core/` |
| `NAV-LIVE-CAPTURE-20261012-ROUND2.md` | `components/` |
| `UDC-MAINLINE-AUDIT.md` | `components/` |
| `microflow-source-audit.md` | `components/` |
| `page-menu-source-audit.md` | `components/` |

其中三份 `MICROFLOW-*` 经 `host_llm_prompt` 渲染进宿主提示词 —— **改它们等于改运行时提示。**

## 五、零精确引用的 65 份：为什么仍不删

按「`udc-semantics/<文件名>` 精确路径」统计，99 份里 65 份零引用。**这不是删除依据**：

- 每份都是某次具体取证的**唯一现场记录**（探针流程名、节点 ID、dataSchema 回读、退出码）。
- 12 个 actionType 的事实格**完全不存在**（见上表右列），删掉即断。
- 引用方可能是未跟踪脚本、会话历史、或未来才落的事实格 —— `git grep` 只搜已跟踪文件。

要动先读 `docs/audit/README.md` 与本目录的裁决记录；裁决**过程**（引用了什么、测了什么数）
在 `docs/ledger/LOG-doc-consolidation-20261107-rounds1-15.md` 第 4、14 轮。

## 六、不要做的事

- **不要**把 `MICROFLOW-*` 批量搬进 `core/facts/`：facts 要求环境无关，这些绑定了 test2 节点 ID、
  探针流程名、scratch 证据目录。
- **不要**把文中 `scratch/` 路径当成可用路径：多数已迁到 `_attic_pending/` 或已过期。
- **不要**因为「没被引用」就删除：34 份里 3 份被代码读取、12 个 actionType 只有它有契约。

## 七、60 秒读完这个目录

1. 读 §一 的更正表 —— 22 条死结论，尤其 ①（会把处置方向带偏）。
2. 要找 UDC 的**事实**：去 `core/facts/`，不要在这里找。这里是「怎么测出来的」。
3. 要引任何数字：先看它有没有被 §一 点名为已更正（分母/串位是本目录第一大错源）。
4. 想动某个文件：先看 §四（13 份被代码读取，3 份进宿主提示词）。

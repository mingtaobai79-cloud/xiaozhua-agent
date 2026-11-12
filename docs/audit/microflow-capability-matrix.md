# 微流程生成能力矩阵（P0 收口）

> ⚠️ **同一主题两份，分工如下（2026-11-07 登记，未合并）**：
> - **本文件**（`docs/audit/`）= P0 收口时的**审计视角**：状态定义、接口契约现状、P1–P4 验收标准、
>   修正记录。含 2026-10-31 的实测指标，属时点快照。
> - **`core/facts/udc/microflow/capability-matrix.md`** = **事实视角**（`capability_registry.py` 直接读取，
>   是运行时唯一数据源）：22 种 actionType 覆盖、按实例加权覆盖率、回答模板。
> - **判据以 facts 为准**（它有代码消费者）。本文件的价值在验收标准与修正记录，不在数字。
> - 两文件数字不一致时**不要合并数字**，先查是哪一版时点。

> 2026-10-31。P0 交付物：把"现在到底能用什么、什么没验、什么还坏着"一次性钉死。
> 数据来源：`core/facts/udc/microflow/node-contract-from-samples.json`（643 条真实语料）、
> `components/construction/*`（构造器源码）、`components/udc/microflow/gates.py`（闸门）、
> 以及本应用（`8704025620829192834`）分组 `-5906489607826727193` 里 15 条已验收流程的**真实 dataSchema**。

## 一、状态定义（不许混用）

| 状态 | 判据 | 含义 |
|---|---|---|
| VERIFIED | 出现在已验收流程里，且该流程 prove 全绿（publish errors=0 + UI isCompleted 全 true + 应用检测无本流程项） | 可以放心复用 |
| PUBLISHED | 只证明"能发布"，没做抽屉/检测验收 | 结构对，前端绑定未证 |
| CONSTRUCTED | 只有构造器，从没发布过 | 未知 |
| BLOCKED | 发布过但被一致性检测阻断且未清 | 不可用 |
| UNSUPPORTED | 无构造器 | 待建 |

## 二、节点能力矩阵

样本数 = 643 条真实流程里该 actionType 出现次数；"已验收流程"= 15 条 prove 全绿流程中出现的条数。

| actionType | 样本 | 构造器 | 已验收流程 | 状态 |
|---|---|---|---|---|
| RETRIEVE_ARRAY | 217 | `microflow_nodes_v2.retrieve_array` / `retrieve_by_id` | 15 | VERIFIED |
| LIST_OPERATION | 654 | `microflow_nodes_extra.list_operation` / `list_size` | 15 | VERIFIED |
| BRANCH | 941 | `microflow_nodes_extra.branch` + composer `branch_with_else` | 15 | VERIFIED |
| CUSTOM_ERROR | 25 | `microflow_nodes_extra.custom_error` | 15 | VERIFIED |
| CREATE_VARIABLE | 712 | `microflow_nodes_v2.create_variable` | 14 | VERIFIED |
| CHANGE_ENTITY | 103 | `microflow_nodes_v2.change_entity` / `change_entity_from_event` | 11 | VERIFIED |
| FOR_EACH | 384 | composer `for_each`（结构节点） | 10 | VERIFIED |
| CONVERT_DATA | 114 | `microflow_nodes_extra.convert_data` | 3 | VERIFIED |
| SUB_MICROFLOW | 251 | `microflow_nodes_extra.sub_microflow` | 3 | VERIFIED（含抽屉） |
| CALL_APP_SERVICE | 105 | `microflow_nodes_extra.call_app_service` | 2 | VERIFIED（含抽屉） |
| PUBLISH_BUSINESS_EVENT | 24 | `microflow_nodes_extra.publish_business_event` | 2 | VERIFIED（含抽屉） |
| CREATE_LIST | 239 | `microflow_nodes_extra.create_list` | 1 | VERIFIED |
| CHANGE_LIST | 317 | `microflow_nodes_extra.change_list` / `change_list_add` | 1 | VERIFIED |
| CREATE_BATCH_ENTITY | 6 | `microflow_nodes_extra.create_batch_entity` | 1 | VERIFIED |
| CALL_DATA_FLOW | 1 | `microflow_nodes_extra.call_data_flow` | 0 | BLOCKED（O1） |
| RETRIEVE | 639 | `microflow_nodes_v2.retrieve` | 1（3 形态） | VERIFIED（SCHEMA+UI） |
| CHANGE_VARIABLE | 1053 | `microflow_nodes_v2.change_variable` | 1（2 形态） | VERIFIED（SCHEMA+UI，attrs/整体赋值） |
| CREATE_ENTITY | 32 | `microflow_nodes_v2.create_entity` | 0 | CONSTRUCTED |
| DELETE_ENTITY | 13 | `microflow_nodes_v2.delete_entity` | 0 | CONSTRUCTED |
| CHANGE_BATCH_ENTITY | 41 | `microflow_nodes_extra.change_batch_entity` | 0 | CONSTRUCTED |
| CREATE_MAP | 4 | `microflow_nodes_extra.create_map` | 1 | VERIFIED（SCHEMA+UI） |
| MAP_OPERATION | 24 | `microflow_nodes_extra.map_operation` | 1 | VERIFIED（SCHEMA+UI） |
| DATA_MAPPING | 17 | `microflow_nodes_svc.data_mapping`（已泛化+列表校准） | 1 | VERIFIED（SCHEMA+UI+**BUILD**，列表形态；单对象形态 BLOCKED=G29） |
| FOR | 32 | `microflow_nodes_extra.for_count` | 1 | VERIFIED（SCHEMA+UI） |
| BREAK | 8 | 无 | 0 | UNSUPPORTED |
| CONDITION | 1981 | composer（结构节点） | 15 | VERIFIED（结构） |

**覆盖率结论（P1 构建轮后）：26 类里 19 类有验收证据（含 17 条流程 BUILD SUCCESS 1.0.79），DATA_MAPPING 单对象形态 BLOCKED（G29），3 类 CONSTRUCTED，1 类 UNSUPPORTED（BREAK）。**BUILD 是独立验收维度：SCHEMA+UI 全绿 ≠ 能编译（实测案例见 test-build-chain.md）。
`CONDITION` / `FOR_EACH` 属结构节点，由组装器生成，不算"无构造器"。**

> 构造器列由 `tools/microflow_coverage.py` 自动扫描（启发式：函数体里唯一的契约 actionType 字面量），
> 个别条目会带上同文件里的辅助函数名（如 `_rid`、`mf_service`），以实际可调用函数为准。

按真实语料加权（出现次数）覆盖率更高：前 8 类（RETRIEVE_ARRAY / LIST_OPERATION / BRANCH / CREATE_VARIABLE /
CHANGE_ENTITY / FOR_EACH / RETRIEVE / CHANGE_VARIABLE）占了 643 条流程的绝大多数，其中只有 RETRIEVE 和
CHANGE_VARIABLE 还没验。

## 三、各层现状

| 层 | 位置 | 现状 |
|---|---|---|
| 业务理解 | 无独立模块（`requirement_parser.py` 雏形） | **缺**，现在靠对话拆伪代码 |
| Evidence | `core/facts/udc/microflow/evidence/`、`docs/audit/artifacts/` | 有：643 条语料、反编译、抓包 |
| Facts | `core/facts/udc/microflow/*.md`（40 篇） | 有，但**与代码不同步**（O4） |
| Node Contracts | `node-contract-from-samples.json`（26 类，MUST/OPT 分级） | 有，`CALL_DATA_FLOW` 只有 1 样本 |
| Expression Contracts | `expression-layer-contract.md`、`ref-and-condition-contract.md` | 有机制描述，**无独立引擎**（O3） |
| 构造器 | `components/construction/microflow_nodes{,_v2,_extra,_svc,_batch}.py` | 23 类有函数；**svc 与 extra 重复实现**（O5） |
| 组装器 | `microflow_composer.py` | 有（trigger/step/finish/gates） |
| 闸门 | `components/udc/microflow/gates.py` | G1–G25（**G15 缺失**，O6） |
| 验证 | `live/verify.py`（prove）、`live_refs.py`、`deploy.py` | 有 |
| Skill | `xiaozhua-udc-microflow-generation`（正文 + 20 references） | 路由未拆分（O7） |
| Tests | `tests/test_composer.py` 13 条 | 只覆盖组装器，节点形态无回归 |

## 四、接口契约现状

| 接口 | 路径 | 证据 | 状态 |
|---|---|---|---|
| 表达式 check | `/service/udc/expression/` + `CHECK_PATH` | `expression_api.py`，纯 HTTP 可用 | 已确认 |
| 表达式 transform | 同上 `TRANSFORM_PATH` | 同上 | 已确认 |
| 服务清单 | `udcMicroflowSearchRestExcludeBootPost` | 本次实测 | 已确认 |
| 子流程清单 | `udcMicroflowServiceListSubMfPost` | 已确认 | 已确认 |
| 应用列表 | `udcMicroflowSearchAppsPost` | 本次实测（11 应用） | 已确认 |
| 应用服务 | `udcMicroflowSearchAppServiceByAppNamePost` | 本次实测（组织模型 25 服务） | 已确认 |
| 服务方法 | `udcMicroflowSearchMethodByNamePost` | 本次实测（含 md5/出入参） | 已确认 |
| 事件对象 | `udcMicroflowSearchEventListPost` | 本次实测 | 已确认 |
| 实体事件 | `POST /service/udc/microflow/filter/event` | 本次实测 | 已确认 |
| 生单规则 | `udcDataFlowListManuallyMappingPost`（body 用 `sourceEntity.relationEntityId`） | 本次实测 | 已确认 |
| 应用检测 | `udcApplicationSearchDetectionPost` | 已确认 | 已确认 |
| **变量/设置项** | 未单独取证（靠 `live_refs.dto_attributes` / `entity_model`） | — | **待确认**（O2） |

## 五、未关闭问题（不许当已解决）

**O1 生单规则必填（BLOCKED）**
`CALL_DATA_FLOW` 契约要求 `dataFlowMappingId`（= 规则列表行 id）与 `dataFlow.id`（= `dataFlowId`），
`dataSourceType` 只能是 `CONDITION`（查询数据）/ `SELECT_PARAM`（选择数据）；写 `ALL` 能发布但界面两个单选全空 → 检查阻断。
服务端另要求 `outputName`（`PROPERTY_IS_REQUIRED`），但唯一 1 条样本节点里没有该键，位置未定位。
**下一步**：在界面保存一次该节点，回读 schema 抓真实位置，再固化为契约。

**O2 变量/设置项接口未独立取证**
现在变量靠实体模型推导，用户手工配置的变量（设置模块）没有独立查询接口证据。

**O3 表达式没有独立引擎**
`expression_build.py` 只是拼 token，没有"逻辑图 → 引用"的推导层，也没有延迟校验（先保存再校验）。
已知真实右值三形态 `CONTEXT_VARIABLE` / `EXPRESSION` / `CONSTANT` 未统一收口。

**O4 事实库与闸门不同步**
`gates.py` 顶部 docstring 只写到 G6，实际用到 G1–G25（G15 缺号）；新加的 G24/G25 只活在代码里。

**O5 构造器双实现**
`microflow_nodes_svc.py` 与 `microflow_nodes_extra.py` 都实现了 `sub_microflow` / `convert_data` /
`call_app_service` / `call_data_flow` / `event_delivery`，且 svc 版本被 composer 引用、extra 版本被生成脚本引用 → 两套可能各自演化。

**O6 G15 缺号**：G15–G20 曾按 lineno 搬回，G15 在迁移中丢失，需确认是否被合并。

**O7 Skill 仍是单文件路由**：正文 + 20 references，没有按 10 个子域拆分入口。

**O8 子微流程属性指纹**
被调流程重发后，引用方 API 侧回写 `mfService` + `checkSchema/update` 重发成功（errors=0），
但检测仍报 `UDC_MICRO_FLOW_04004 微流程已更改`；必须在抽屉点「属性已更新，点击刷新」并重选。
**下一步**：抓「刷新」按钮实际调用的接口与数据变化，能接口化就接口化，不能则降级为定向 UI 刷新。

## 六、指标基线（本轮实测）

| 指标 | 当前值 | 采集方式 |
|---|---|---|
| 构造耗时（简单/中等/困难） | 0.17s / 0.50s / 1.00s | `scratch/bench_compose.py`，8/13/21 节点 |
| 发布+回读 | 0.49s | 同脚本 |
| UI 全量抽屉校验 | 37s / 11 节点（≈2.45s/节点） | `prove()` 计时 |
| 首次构造通过率 | 未统计（本轮 6 条里 2 条一次过 = 33%） | 需按节点形态分别记 |
| 首次页面通过率 | 未统计 | 同上 |
| 首次平台校验通过率 | 未统计 | 同上 |
| 首次构建通过率 | 未统计（上一轮 backBuild.log BUILD SUCCESS，128 文件） | 构建链 |
| 事实复用率 | 未统计 | 需记录"查询命中缓存/接口"次数 |

## 七、P1–P4 验收标准（与本文对应）

- **P1 节点/表达式测试矩阵**：把上面 9 个 CONSTRUCTED 类型逐个做到 VERIFIED；每个类型至少 2 种形态
  （如 RETRIEVE：ID 查询 / 条件查询），并注入错误验证闸门能拦。验收 = 本文矩阵状态列变更。
- **P2 表达式引擎 + 元数据缓存**：`ExpressionBuilder` 能从逻辑图推导前序引用（不查接口）；
  动态变量走接口；缓存键 = 应用+对象+版本+时间；校验一律在"保存草稿之后"。验收 = O3 关闭。
- **P3 UI 校验分三级**：L1 本地静态（必跑，0 浏览器）；L2 页面整体状态一次性读取（必跑）；
  L3 抽屉按需（仅新形态/高风险/抽样）。验收 = 日常生成 prove 从 37s 降到 ≤12s，且 04004 类问题仍能发现。
- **P4 一键流水线**：`需求 → 逻辑链 → 元数据 → 构造 → L1 → 保存草稿 → 表达式+检测 → 定向验收 → 纠错 → 发布 → 构建`。
  验收 = 每条失败都能回答"哪个节点/哪个字段/是构造器还是事实/能否自动纠正/纠正后是否复验"。

## 八、本轮不做

- 不再新增业务模板流程（现有 15 条只作回归语料）。
- 不做全量 UI 自动化替代构造（UI 只做验收）。
- 不在未保存状态下调表达式校验（会造假错误）。


## 九、P1 修正记录（2026-10-31）

1. **计数修正**：15 VERIFIED（原 14 漏数 CONDITION 结构节点）+ 9 CONSTRUCTED + 1 BLOCKED + 1 UNSUPPORTED = 26。
2. **状态五级化**：CONSTRUCTED / SCHEMA_VERIFIED / UI_VERIFIED / BUILD_VERIFIED / RUNTIME_VERIFIED，
   逐维度记录，不用单一 VERIFIED 掩盖（详见 p1-verification-report.md）。
3. **覆盖三口径**：类别 62%（含结构 65%）；实例加权 97.8%（含 CONDITION）/ 72.9%（不含）；
   业务组合 12/12。补 RETRIEVE/CHANGE_VARIABLE 后，未验实例仅 172/7937。
4. **新增闸门**：G26（自定义服务方法签名 md5/parameter/returnValue/fullName）、
   G27（CHANGE_VARIABLE attrs 引用四键，同 G25）。
5. **L2 落地**：`components/udc/microflow/live/l2_state.py`，43 节点 3s；边界证据：04004 指纹类 L2 不可见，L3 保留。

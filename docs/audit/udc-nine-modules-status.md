# UDC 九大模块 · 状态事实与证据审计（2026-10-17）

> 审计口径：只用仓库在盘证据 + 本次直连 MySQL(test2) 实测计数，不引用任何"完成度百分比"自报。
> 证据分级：LIVE（活体调用/DB 实测）/ STATIC（字节码/bundle/反编译）/ VACUUM（域内 0 条可证据化契约）/ UNVERIFIED（未取证）。
> 应用基线：`datamigration9000000000000000001`（appId `8704025620829192834`），环境 test2。

## 0. 总表

| # | 模块 | 状态 | 本应用 DB 行数 | 在盘证据量 | 核心缺口 |
|---|---|---|---|---|---|
| 1 | 应用 | PARTIAL（读面 LIVE；deploy_info+app-online 契约面双 PASS；运行态受外部阻塞） | udc_application=1（NORMAL 全库 10） | 30 文件 / 176KB | **建应用=NORMAL BLOCKED / FORM 3 通路 STATIC_CLOSED 未 LIVE**；target server_403 待授权；**HUMAN 四选一** |
| 2 | 实体 | PARTIAL（建实体/属性 LIVE，字段级语义多处错） | udc_entity=9，udc_attribute 全库 67862 | 145 文件 / 2740KB | 枚举域错配、字段级 LIVE 端到端未做全 |
| 3 | 菜单 | PARTIAL（写链有，绑定语义有缺陷） | udc_function_node=2260（全库） | 28 文件 / 173KB | 复制页面不带规则/事件、URL 硬复制 |
| 4 | 规则 | PARTIAL（生单 0043 已闭环，扣减仅设计态） | udc_data_flow=2，udc_deduction_rule=1 | 42 文件 / 1889KB | 扣减运行态未验；页面规则全覆盖未做 |
| 5 | 流程 | **IN PROGRESS / 当前 FAIL** | udc_microflow_info=33 | 145 文件 / 1919KB | v4 探针 PANEL_IDENTITY_FAIL，23 节点失败 |
| 6 | BI | **VACUUM（负证据完备）** | 无 udc_bi 表；仅 gantt_chart_schema | 162 文件 / 1258KB | 平台侧 0 条真 BI 契约；Gantt 5.3.260 独立面 |
| 7 | 栏目 | **PARTIAL（S1+S2 定位完成，写链 LIVE）** | 表族 = `udc_portlet`（type=0 分组 / type=1 栏目）+ `udc_page_info`(page_type='PORTLET') + 门户侧 `portal_portlet_category`/`portal_portlet_definition` | S1 导航抓包 + S2 建删全链（`docs/audit/column-discovery/`） | 域定位闭环；契约未写 |
| 8 | 设置 | PARTIAL（13 tab 调用链 LIVE，写面未全） | 无独立表（复用 app/entity 配置） | 102 文件 / 871KB | 各 tab 写入与回读未逐项验收 |
| 9 | 角色 | **VACUUM（真实域近乎空白）** | udc_role=96，udc_role_resource=12328 | 11 文件 / 27KB（多为 agent 角色卡，非 UDC 角色） | 角色/权限域在 seeyon-agent 内无契约、无取证 |

## 1. 应用（Application）

**状态**：PARTIAL → **契约面基本齐备，运行态受外部阻塞**（2026-10-17 轮15 更新）。

**主要事实**
- 应用读面已 LIVE：`application-search`、`applog` 两族。证据 `core/facts/udc/application/application-search.md`（19.6KB，S3 09-26 PASS）、`applog-family.md`（21.8KB，S4 09-27 PASS）。
- **deploy_info 契约面 = PASS**（2026-10-17）：`docs/operation-contracts/udc/application/udc-app-deploy-info-live-contract.md`（commit `b48d4ce` + 两处微修 `6b45e80`）。implementer RESULT + auditor VERDICT 双 PASS（独立复核 a-d 全过）。对照应用 LIVE 回读双发复现；appId 两形态并列登记（内层无引号 number / DTO String / DB bigint）。**target 运行态面单列 BLOCKED**，不得写作「deploy_info 打通」。
- **app-online 发布链契约面 = PASS**（2026-10-17）：`docs/operation-contracts/udc/application/udc-app-online-contract.md`（`4422b5d` 273 行 + `ddae1c2` §7 + `362f20a` 门2a + `3590e62` Traceid 判据）。auditor VERDICT=PASS（a 门链 / b pushEnv / c appId 来源 / d 无越级 全过）。含：`POST /service/udc/deployment/app-online-new`（`@RequestBody`，返回 `SingleResponse<Long>`）、5 道前置门逐条 CFR 行号、`pushEnv` 三态「已配置」（test2 Nacos currentEnv=development + deploymentEnvStr=development-implement-prod 命中 getPush 4 项白名单）、门后 4 条写面副作用。
- **custom-app/create NPE 根因 STATIC 闭合**：`CustomPageInfoService#create4CustomPage` **bci 227** `Collection::stream` 解引用 `getItemDefinitionDto.getRelationApps()` null（`relationApps` 仅 `copySchema=true` 分支赋值，`copySchema=false` 必 NPE，纯平台代码缺陷）。证据 `core/facts/udc/write-chain/custom-app-create-npe-relationapps-root-cause.md`。
- 应用草稿面：`core/facts/udc/serial/app-draft.md`（15.2KB）。**口径修正（2026-10-17）**：`app-draft/create` 是**设计态草稿写读环**（对象 `app_data_draft`：`data_id varchar + draft_data longtext` 键值表，**无 `udc_application` 外键**），**不产生应用实体行，不构成建应用路径**。旧记账「草稿面 = 建应用 LIVE PASS」已推翻。
- 写面其它：`appname` 相关 NPE 与 connector 目标已定位（`appname-key-npe-and-connector-target.md` 8.7KB）；`input-output-appname-dependent-app-gate.md` 6.7KB 记录依赖应用门禁。

**证据**
- DB：`udc_application` 本应用 1 行，全库 20 行（NORMAL `source_type=0 AND json_prefab=0` = **10** 个）。
- 文件：`core/facts/udc/application/{application-search,applog-family}.md` + `evidence/app-search-live-20260926.md`。
- 实测：`udcMicroflowSearchAppServiceByAppNamePost.json`（19.4KB，13 个真实 AppService 候选）。

**缺口（2026-10-17 判定，全部为外部输入依赖，非 agent 可解）**
1. **建应用 = NORMAL 域 BLOCKED；FORM 域存在 3 条静态通路（均未 LIVE 验证）**
   > **口径重写（2026-10-18）**：原判定「双 BLOCKED，无 agent 可行绕行」中的**配额分支对 FORM 路径不成立**。
   > 根因：`checkTenantLicenseAppCount`（CFR 件 L533-546 ≡ class LNT L511-523）**本身是条件门** ——
   > `if (isNull(dto) || NORMAL == dto.getSourceType())`，**非 NORMAL(FORM) 整块跳过，不计数不抛错**。
   > 三方独立验证（main / implementer / auditor），auditor javap 直读确认 `if_acmpne 38` 跳 return。

   - **窄门①（仍成立）**：`custom-app/create` 平台 NPE（bci 227，纯平台缺陷）。
   - **窄门②（仅对 NORMAL 成立）**：配额 `UDC_APP_0030` —— 计数条件 `source_type=NORMAL && json_prefab=false`，实测 = **10**；
     上限 `createAppNum` **10 vs 11 未决**（`ctp_sandbox_config` 两行冲突；`SandboxConfigService` 575 jar 全扫 0 命中）。
   - **窄门③（已排除）：草稿面不是第三路（结构性不存在）。**

   **FORM 域 3 条静态通路（均 STATIC 闭合，均未 LIVE 验证）**
   | # | 路径 | 为何不受配额门 | 状态 |
   |---|---|---|---|
   | 1 | `create(sourceType=null)` | L418 门在 L429-431 默认化**之前**；门判 `isNull(dto)` 非 `isNull(sourceType)` → 跳过 → 默认化为 FORM → L458 INSERT | **STATIC_CLOSED**（门序缺口） |
   | 2 | `create(sourceType=FORM)` | L534 首个条件不成立 → 整块跳过 | STATIC_CLOSED |
   | 3 | `saveAsNewDesign` | `SchemaManager.saveAs` L232 断言源应用必为 FORM → 链路 `dto.sourceType` 恒为 FORM → 跳过 | STATIC 闭合，待 LIVE |

   **门序缺口补证（STATIC_CLOSED）**：`buildApplicationDto4Create` 两实现均**不回写** sourceType；
   L443 `containCode` 只验码值 ∈{0,1}（FORM=1 通过）；`ApplicationDto.sourceType` L66-67 **无 `@NotNull`**；
   `ApplicationAppServiceImpl.create` L180-183 直传 `request.getData()`；
   另 `checkAssignOrgIdAndCreator` L479-481 `if (sourceType == FORM) return;`（连 OrgId/Creator 限制都不适用）。

   **`saveAsNewDesign` 可用源应用 = 7 个（不是 9）**
   `L1544 → AppVersionService.selectByAppIdAndDeployType` L272-281 **带 `state == DeployStateEnum.SUCCESS`(=1)** 过滤。
   test2 实测 `deploy_type=2` 的 FORM 应用 9 个，其中 **state=1 的 7 个**：
   `912667056861626502` / `3890487949927400401` / `5150746664960478913` / `5746064954083329093` /
   `6712017922882617636` / `7022003764439498867` / `7324620281389731265`。
   另 2 个非 SUCCESS（`6388488623384448921` state=0 发布中 / `5245855677018033156` state=-1 未发布）→ L1545 会抛 `UDC_APP_0033`。

   **关键区分（写死，防后人误读）**：
   - 「2 个 INSERT 出口 + 门前置」证明的是**「还有别的写入路径吗」= 否**，**不是**「所有路径都会被拦」= 否。
   - **撞门 ≠ 被拦**：计数条件与入口 source_type 无关，但**门体进入条件与 `dto.sourceType` 有关**。
   - 三条 FORM 通路**均未 LIVE 验证**，不得写作「可建应用」。

   - 验收第 2 条口径：**NORMAL 域按 BLOCKED 收口；FORM 域「路径存在、可行性未闭合」**。
2. **运行态 target `server_403` 未解**：`/service/{appName}/app-info/deploy-info` → HTTP 200 外壳 + `server_403「无权限访问」`。定性 = **应用内网关鉴权层**（非 WAF；事故前即 403，WAF 解除后仍 403）。归因指向运行态路由授权未建立（`udc_role_resource` target 391 vs 对照 4944，target 11 条角色无 `is_admin`）；**口径收紧：强相关非因果充分**（本环境无 `udc_role_member` 用户-角色绑定表，无法闭合「账号→角色→资源」链）。
   - 佐证（2026-10-17 22:54 实测）：`GET /service/udc/application/8704025620829192834` → **200/1282B BOOT_0000**，账号能读到 target 全部字段（guid/publishState/sourceAppId）→ **不是账号读不到应用**，是运行态宿主前缀层拒绝。
3. **`Apps.isRunInTest()` 已解**：判定依据 = `PropertySources.contains("Inlined Test Properties")`（`boot-core-5.3.358` L599-606）；test2 非 `@SpringBootTest` 上下文 → **false → 门 2（APP_DEPLOY 授权）不被短路，是真跑的**。
4. **`publishState` 不能作上线判据**：target 与对照应用 `publishState` 均 = `UNPUBLISH`、`deployId` 均 null，而对照应用运行态是 LIVE 的。
5. **P3-B（app-online LIVE）不发**：appId 三来源全闭（既有=授权门 / 新建=配额门 / 草稿转正=不存在）。

**进行中的收口**：P3 契约 4 条非阻断补正 + §9.7 配额口径改写（HANDOFF-05 在途）。

**所需输入（交 HUMAN，四选一）**
- **A** 释放 1 个 NORMAL 配额（删/归档 1 个现有应用；破坏性，需点名）
- **B** 确认生效上限 10 还是 11；若为 10 则提高 `createAppNum`
- **C** 承认 test2 建新应用不可达，验收第 2/3 条按 BLOCKED 收口
- **D（建议优先）** 直接给 target 应用授运行态 `APP_DEPLOY` —— 不改数据不改配置，无需建新应用即可跑通「发布→部署→运行态」，直接吃验收第 3 条

**目标**：应用 CRUD + deploy-info 全链 LIVE 回读，作为其他八域的前置。

## 2. 实体（Entity）

**状态**：PARTIAL，且是九域中证据最厚、坑最多的域。

**主要事实**
- 建实体/建属性已 LIVE：`core/facts/udc/entity/create.md`（B1 09-25 PASS，验收单 7670732978062038177）、`attribute-create.md`（B5 10-10 PASS，BOOT_0000 + 属性 id 回读）。
- 元数据存储机制已固化：`core/facts/udc/metadata-storage.md`——设计态权威源 MySQL `udc_entity`/`udc_attribute`；运行态读 Redis(180h TTL)→OSS 镜像；`presetData/attribute.json` 仅系统属性模板。
- **已知硬缺陷（FIX-PLAN-entity-rule-menu.md 认错条目）**：枚举建错域。`POST /udc/udc-enum` 建的是选项集 `udc_enum`，而 CTPENUM 字段要的是平台枚举 `ctp_enum`；字节码根因在 `AttributeMatchDetectionUtils` 自动拼 `com.seeyon.boot.starter.enums.domain.entity.CtpEnum.<值>`。
- 平台枚举表族（`ctp_enum`/`ctp_enum_item`/`ctp_enum_category`）此前**完全未纳入契约清单**。

**证据**
- DB：本应用 `udc_entity`=9，`udc_attribute` 全库 67862；`udc_enum`=1143，`ctp_enum`=1681。
- 文件：145 个 / 2740KB，最大件 `docs/construction-rules/entity/attribute-propagation-cross-sample.json`（1515KB）、`presetData/attributeSet.json`（100KB）。
- 契约：`docs/operation-contracts/udc/entity/` 5 份（62.7KB）。

**缺口**
- 字段级 LIVE 端到端从未做全（枚举、关联、多选各类型）。
- batch/update/delete 面 UNVERIFIED。

**目标**：字段类型矩阵（文本/数值/日期/布尔/枚举/关联/多选/子表）逐类型 LIVE 建-存-读-检测闭环。

## 3. 菜单（Menu）

**状态**：PARTIAL。

**主要事实**
- 菜单绑定写链在盘：`core/facts/udc/write-chain/menu-default-page-write-chain.md`（9.3KB）、`core/facts/udc/page/menu-bind.md`（27.1KB）。
- 平台侧无独立 `*Menu*Controller`：菜单/导航面 = 功能节点树 `UdcFunctionNodeController`（5.3.517 实证）。
- **已知缺陷**（FIX-PLAN）：只验过"建菜单成功"；URL 直接复制、页面绑定不换实体、复制来的页面无规则无事件。

**证据**
- DB：`udc_function_node` 全库 2260 行。
- 文件：28 个 / 173KB；`docs/audit/udc-semantics/page-menu-source-audit.md`（20.6KB）、`udc-menu-5.3.517/multi-request-body-get-binding.md`。
- 契约：`docs/operation-contracts/udc/menu/` 7 份（32.7KB）。

**缺口**
- 菜单创建 → 绑定页面 → 规则/事件随迁 → 运行态可访问，全链未验收。

**目标**：菜单建-绑-迁规则事件-运行态路由可达。

## 4. 规则（Rule）

**状态**：PARTIAL，内部差异大（生单较好，扣减最弱）。

**主要事实**
- **生单规则 0043 已彻底闭环**：`dataflow-rule-0043-root-cause.md`（7.2KB）。根因 = `rule_info` 误发到 `definition`；`definition` 是画布 String，`rule_info` 是 `mappingDetailDto` String。`udcDataFlowMappingUpdatePost` 已 SUCCESS（affectCount=1）。
- 生单写链契约：`dataflow-rule-rest-write-chain.md`（11.5KB）；扣减+生单模型：`deduction-and-dataflow-rules-model.md`（7.5KB）。
- 扣减规则：`deduction-rule-rest-write-chain.md` 在盘；四层模型 `deduction_map → deduction_rule → deduction_rule_detail → deduction_algorithm` 已确；算法操作符 `SUBTRACT_EQUAL` 已确。
- **扣减最大缺口**：`udc_deduction_rule_detail` 本应用 0 行，明细结构仍靠其他应用样本推定。
- 页面规则：`microflow-vs-pagerule-node-domains.md`（7.1KB）区分两域节点域，不能混用。

**证据**
- DB：本应用 `udc_data_flow`=2，`udc_deduction_rule`=1（全库 59 / 1）；运行态 `udc_rt_*` 全 0 行。
- 文件：42 个 / 1889KB；`live-rule0043-deduction-audit.json`（14.2KB）。
- 契约：`docs/operation-contracts/udc/page/` + ded 相关。

**缺口**
- 扣减运行态从未验证（`publishState=UNPUBLISH`）。
- 页面规则（page rule）与业务规则（event rule / 定时规则）分类未齐。

**目标**：扣减规则 run-time 触发 + 扣减结果 DB 回读；页面规则全类型覆盖。

## 5. 流程（Flow / MicroFlow）— 当前主战场

**状态**：IN PROGRESS，**当前证据为 FAIL**。

**主要事实**
- 33 条本应用微流程（`udc_microflow_info`=33）。
- 标准微流程 `-1014184770817921434` 必须保持 `type=SERVICE(0)` + `serviceInterface=CustomMicroFlowAppService`，曾误改 CUSTOM 被用户纠正。
- **v4 探针最新结果（2026-10-17T06:25:19Z）**：`status=PANEL_IDENTITY_FAIL`，`exitCode=3`，**23 个失败**。
  - `knownFailRecheck.customService.status = PANEL_SWITCH_FAIL`（drawerTitle=None）
  - `knownFailRecheck.eventPublish.status = NO_PANEL`（fingerprint=None）
  - `distinct = False` → `IDENTITY_FAIL`
- 根因链已推进三轮：v2 点击命中 `<input class="ant-input edit-input">` → 节点进编辑态；v3 发现抽屉(1309px, no-mask)未关闭遮挡画布 → 后续点击静默失效 → `.active` 残留上一节点 → 指纹被复制；v4 把该机制显式化后**暴露更多节点同样失败**（23 条），说明这不是单点问题而是"抽屉不留出口"的系统性采集障碍。
- 已知可用事实：事件投递候选来自 `MICRO_FLOW_EVENT` DTO（非 `udc_event`）；已建真实事件 DTO `小爪事件A1`；`selectParam` 面板扁平 / DB 带 wrapper 两形态；`runAfter=null` 不是断线证据。

**证据**
- 文件：145 个 / 1919KB；probe v2/v3/v4（111KB/131KB/108KB）。
- 契约：`docs/operation-contracts/udc/microflow/` 15 md + 49 json（816KB）——九域中最厚。
- 事实：`core/facts/udc/write-chain/` 下 35 份，其中微流程相关 12 份。

**缺口（按优先级）**
1. **采集器可信度未闭合**：抽屉遮挡导致面板身份不可证，v4 23 条失败。
2. 节点级字段/映射/表达式未逐个取证（数据转换映射、插入赋值、CREATE_MAP、事件对象、子流程类型）。
3. 表达式函数/token/executableExpr 契约未完成（131 系统变量已抓）。
4. 页面点击构建 + 受控业务执行 + 数据回读未做。

**目标**：采集器先可信（面板身份可证）→ 21 节点逐字段证据闭合 → 生成链可用 → 页面构建 + 受控执行回读。

## 6. BI

**状态**：**VACUUM（完备负证据）**，不是"未做"。

**主要事实**
- 唯一判定：**UDC 5.3.517 域内 0 条真 BI 只读契约**（`bi-vacuum-contract.md` 28.1KB）。
- 方法完备：6 个 UDC jar / 1217 class / 13 个 BI 关键词宽口径扫描 + 219 行端点字面量逐条判定 + 38 类 `javap -p -v`，逐条排除伪命中。
- 独立面：Gantt 图表 `ganttchart-5.3.260`（`docs/operation-contracts/udc/bi/ganttchart-5.3.260.md`），DB 有 `gantt_chart_schema` 表。
- **无 `udc_bi` / `udc_report` 表**——BI 能力不在 UDC 域内实现。

**证据**
- 文件：162 个 / 1258KB；`udc-bi-5.3.517/r1_step2_endpoints.json`（215KB）、`bi-endpoint-literal-scan.md`（106KB）。
- 契约：`docs/operation-contracts/udc/bi/` 3 份（52KB）。

**缺口**
- Gantt 之外是否还有 BI 落点（如门户报表/数据集）未扫。
- 若客户要 BI，需转入标品侧（非 UDC）建模。

**目标**：确认 BI 归属（UDC 域外），Gantt 面单独建模；不虚构 UDC BI 契约。

## 7. 栏目

> **2026-10-17 S2 定位完成**：栏目真实对象 = **Portlet**。设计态 `udc_portlet`（type=0 分组 / type=1 栏目本体）+ `udc_page_info`（page_type='PORTLET'）；门户侧 `portal_portlet_category`（分组→分类，category_code == 分组 id）+ `portal_portlet_definition`（栏目→定义，portlet_id == pageRelationId，删除为 delete_flag 软删）。
> 证据：`docs/audit/column-discovery/ROUTE-S1-nav-capture.md`、`ROUTE-S2-create-capture.md` + `raw/`（S2 建删全链 LIVE，含 H1–H6）。以下为定位前的历史记录，保留备查。

**状态（定位前）**：**VACUUM / 近乎零证据**——九域中最空的一块。

**主要事实**
- 仓库内相关证据：**仅 1 个文件 0.7KB** —— `core/facts/udc/write-chain/evidence/R6-column-module-20260930.json`。
- 无 `udc_column` / `udc_portal` 表（DB 实测 SHOW TABLES 命中 0）。
- 现有 `udc_page_layout`（页面布局）与 `udc_page_group` 可能是栏目真实落点，但**从未按"栏目"语义取证**。

**证据**
- 文件：1 个 / 0.7KB。
- 契约：`docs/operation-contracts/udc/` 下**无 column 目录**。**（2026-10-17 时点；当前已有 `column/` 140,182 B / 4 份，见本文件 §7 顶部更正块）**
- DB：`column`/`portal` 关键词表 0 命中。

**缺口（全部）**
- 栏目在 UDC 设计器中的真实对象（是 page_layout？page_group？还是门户侧 ctp 对象？）未定位。
- 前端 nav「栏目」页面的调用链未抓。
- 无任何写链/读链契约。

**目标**：先做域定位（前端页面 → 调用链 → 落表），再补契约；目标不是马上写，而是先把"栏目到底是什么"钉死。

## 8. 设置（Settings）

**状态**：PARTIAL，读面最强、写面最弱。

**主要事实**
- **13 个 tab 的前端页面与调用链路已 LIVE 取证**（`SETTINGS-TABS-CALLCHAIN.md` 27.2KB，2026-10-12 test2）。
- 版本边界已钉：后端镜像 `udc:5.3.517`，前端壳 `seeyonGlobalVersion=5.3.41`、`seeyonSyfVersion=5.3.11`，设计器远端 `/udc/remoteEntry.js`（47,554B / 166 chunk），静态存储 OSS `seeyon-public-test2` key=`udc/<chunk>.<hash>.js`。
- 四种调用形态已归纳：loader 描述符 / raw Apollo 文档 / saga / 其他。
- 数据字典与基础设置 API：`DATADICT-AND-BASESETTING-APIS.md`（17KB）。

**证据**
- 文件：102 个 / 871KB；`udc-publish-5.3.517/`（发布证据 193KB+168KB+72KB）、`u6-nacos-config/`（85KB）。
- 契约：`docs/operation-contracts/udc/publish/` 2 份、`runtime/` 3 份。

**缺口**
- 13 个 tab 的**写入 + 回读**只做了部分（读面强）。
- 发布（publish）与资源（resource）两域契约在盘，但写链未端到端。
- jar 级 class 确认 BLOCKED（`/app/udc-assemble.jar` 502MB，容器内 unzip 全静默失败）。

**目标**：13 tab 逐 tab 写-读-回滚闭环；发布链路补齐。

## 9. 角色

> ⚠️ **【当前 2026-11-07】本节整体已被后续取证覆盖，务必先看这条再读下面。**
> 本节写于 2026-10-17 之前，当时判断「角色域 VACUUM / 真实域空白」。**此后已建立两处证据与契约：**
>
> | 本节原判断 | 当前实测（2026-11-07） |
> |---|---|
> | 「`docs/operation-contracts/udc/` 下**无 role 目录**」（L257） | **在盘**：`docs/operation-contracts/udc/role/` = `README.md` 8,411 B + `write-chain.contract.md` 42,345 B。**该契约是全仓唯一「声称能自验且真的能自验」的一份**（复算 `15 / 1 / 16`，需 JDK 21 的 `javap`） |
> | 「UDC 角色域真实证据：仅 1 条 2.8KB」（L251） | **已远超**：`docs/audit/role/` **10 份 / 242,500 B**（P0 对象模型 44KB、P1 四条、P2 读回、P3 写链 64KB、P3b 权限面板复检、S5 写链收口） |
> | 「VACUUM（真实域空白）」（L247 / L256 的 11 文件 27KB） | 27KB 是**本节写时**的规模。当前 242,500 B，**约 9 倍** |
>
> **数字可能变化的只有规模，不变的是一条纪律**：仓库内 `core/role/` 是 **Agent 角色卡**，不是 UDC 平台角色域证据 —— 这条区分仍然成立，且仍然重要（混为一谈会虚报进度）。
>
> **本节保留原文不改**：它记录了「域被判为空白」的那一刻，而这正是后来 242KB 取证的起点。
> 当前状态请看 `docs/audit/role/README.md` 与 `docs/operation-contracts/udc/role/README.md`。

**状态（2026-10-17 时点）**：**VACUUM（真实域空白）**。

**主要事实**
- **重要区分**：仓库内 `core/role/`（ROLE-CARD.md、BEHAVIOR.md、EVIDENCE-DISCIPLINE.md、README.md）是**Agent 角色卡**，不是 UDC 平台角色域证据。混为一谈会虚报进度。
- UDC 角色域真实证据：仅 `docs/operation-contracts/udc/menu/P1-udc-role-has-system-admin.md`（2.8KB）一条，且是挂在 menu 域下的附带条目。
- DB 真实存在：`udc_role`=96、`udc_role_resource`=12328、`udc_resource`=6968——**数据和权限关系都在，但 seeyon-agent 内零契约、零写链、零取证**。
- 无 `udc_permission` / `udc_auth` 表（权限走 resource 关联）。

**证据**
- 文件：11 个 / 27KB，其中 4 个是 agent 角色卡（非 UDC）。
- 契约：`docs/operation-contracts/udc/` 下**无 role 目录**。
- DB：`udc_role`=96，`udc_role_resource`=12328。

**缺口（全部）**
- 角色创建/授权/资源绑定 写链未取证。
- 角色与菜单/页面/按钮的权限映射机制未知。
- 无任何读面契约。

**目标**：角色域从零建立：对象定位 → 表族 → 读写契约 → 授权生效验证。

## 10. 跨域结论

1. **九个域的状态差异极大**，不能用一个"完成度"概括：实体/流程有 1.9~2.7MB 证据且仍在深挖；栏目/角色几乎是零；BI 是"完备的零"（负证据），性质完全不同。
2. **唯一贯穿性缺陷**：把 `BOOT_0000` / HTTP 200 当成功。已在 `FIX-PLAN-entity-rule-menu.md` 认错，但同一错误在其他域仍可能出现。
3. **必须并行的理由**：九域证据底座、表族、契约目录都相互独立，串行推进会在同一块（当前是微流程）反复深挖，其余八域长期停滞。
4. **不能并行的部分**：微流程域当前处于 FAIL 状态且采集器不可信，必须先修采集器再推进节点；这一点作为该域自己的第一优先级，不阻塞其他八域启动。

---

生成时间：2026-10-17  |  证据源：仓库在盘文件 + MySQL test2 实测 + 现有 probe JSON

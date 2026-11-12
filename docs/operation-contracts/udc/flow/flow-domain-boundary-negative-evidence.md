# 流程域(BPM集成) 域边界穷尽性负证据 — flow-domain-boundary-negative-evidence.md
- 轮次: R6（本任务最后一刀，强化交付物#1 完备性）| 证据单元: 本地 Maven 5.3.517（6 jar，全离线，禁相邻版本混写）
- 证据底座: docs/audit/artifacts/udc-flow-5.3.517/controller-enumeration.txt（40 controller jar tf 原始输出 + 6 jar 路径/SHA-256）
- 证据等级: 枚举/逐类归属 = OBSERVATION；「0 遗漏」结论基于 40 类全枚举 + 6 域已契约化核对，非推测；**未把推断写成 FACT，未深挖任何 non-flow 方法体**。
- 硬约束: 只读 jar tf（javap 仅 main 复核用）；未碰 bpm-facade 5.3.374 / app-approval 5.3.295；未拼网关前缀；冻结件零写入。

## (1) 穷尽枚举
命令原文（逐 jar，jar tf 只读）：
```
jar tf <MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort
jar tf <MAVEN_REPO>/com/seeyon/udc-facade/5.3.517/udc-facade-5.3.517.jar | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort
jar tf <MAVEN_REPO>/com/seeyon/udc-starter-customplan/5.3.517/udc-starter-customplan-5.3.517.jar | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort
jar tf <MAVEN_REPO>/com/seeyon/udc-starter-dataflow/5.3.517/udc-starter-dataflow-5.3.517.jar | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort
jar tf <MAVEN_REPO>/com/seeyon/udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort
jar tf <MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort
```
jar tf 命中计数（OBSERVATION，原始输出全文见 controller-enumeration.txt）：

| jar | controller 命中 |
|---|---|
| udc-common | 0 |
| udc-facade | 0 |
| udc-starter-customplan | 5 |
| udc-starter-dataflow | 5 |
| udc-starter-lowcode | 0 |
| udc-starter-runtime | 30 |
| **合计** | **40** |

40 类全清单 = 6 域（BPM 集成）+ 34 非-flow（见 (2) 逐类归属）。

## (2) 逐类域判定（40 controller 逐个一行）
判定规则: 每类一行 = 「BPM 集成域」→ 映射 registry-entries.md 具体条目；或 「non-flow 域」→ 一行归属理由（page/log/dtype/app/deduction/attachment/graphql/proxy/… 哪类），不属 BPM 集成。**OBSERVATION 级，禁把推断写成 FACT，禁深挖方法体。**

### udc-starter-customplan（5）
| controller | 域判定 | 依据/映射 |
|---|---|---|
| BpmNodeInfoController | **BPM 集成域** | registry-entries: udc.flow.bpm_node_info_search（POST node-info/search，R2-C1） |
| CustomPlanController | non-flow | 自定义计划/方案管理（customplan 管理面），非 BPM 集成 |
| FilterPlanController | non-flow | 过滤方案管理（customplan 管理面），非 BPM 集成 |
| ScalabilityFieldController | non-flow | 扩展/弹性字段管理（customplan 管理面），非 BPM 集成 |
| UdcRuntimeHistoryMetaDataController | non-flow | 运行时历史元数据查询（meta-data 域），非 BPM 集成 |

### udc-starter-dataflow（5）
| controller | 域判定 | 依据/映射 |
|---|---|---|
| DataFlowForBpmController | **BPM 集成域（写侧）** | registry-entries 写侧: udc.flow.bpm_fill_error_data（POST udc-runtime/bpm/fill-data，write=true 未放开） |
| DataFlowRtMapController | **BPM 集成域** | registry-entries: udc.flow.data_flow_map_get_by_id（GET）+ udc.flow.data_flow_map_search（POST，R2-C4/C5） |
| DataFlowRtMappingController | **BPM 集成域** | registry-entries: 只读 udc.flow.data_flow_mapping_get_by_id/search_original/init_data/detail（R2-C6..C9）+ 写侧 data_flow_mapping_update/update_state |
| DeductionController | non-flow | 推断/演绎引擎（deduction 域），非 BPM 集成 |
| DeductionRtUpgradeController | non-flow | 推断引擎运行时升级（deduction 域），非 BPM 集成 |

### udc-starter-runtime（30）
| controller | 域判定 | 依据/映射 |
|---|---|---|
| UdcFunctionNodeController | **BPM 集成域** | registry-entries: udc.flow.function_node_tree（GET udc-runtime/meta-data/select-function-node-tree/{appName}，R2-C2；跨 microflow 域重叠） |
| UdcFormDataQueryController | **BPM 集成域** | registry-entries: udc.flow.form_data_query（POST udc-runtime/data/query，R2-C3） |
| AppDraftController | non-flow | 应用草稿管理（app 域），非 BPM 集成 |
| AttachmentTemplateController | non-flow | 附件模板管理（attachment 域），非 BPM 集成 |
| CustomApplicationController | non-flow | 自定义应用管理（app 域），非 BPM 集成 |
| DynamicJarController | non-flow | 动态 jar 加载（runtime 基础设施），非 BPM 集成 |
| FrontFunctionSupportController | non-flow | 前端函数支持（runtime 基础设施），非 BPM 集成 |
| GraphqlProxyController | non-flow | GraphQL 代理转发（graphql/proxy 域），非 BPM 集成 |
| RuntimeCOLISplitController | non-flow | 运行时 COLI 拆分（runtime 基础设施），非 BPM 集成 |
| RuntimeEnvCheckController | non-flow | 运行环境检查（runtime 基础设施），非 BPM 集成 |
| UdcAppLogController | non-flow | 应用日志查询（log 域），非 BPM 集成 |
| UdcAttrSnapshotRtController | non-flow | 属性快照运行时（snapshot 域），非 BPM 集成 |
| UdcDataTypeController | non-flow | 数据类型管理（dtype 域），非 BPM 集成 |
| UdcEntityUpdateRtTestController | non-flow | 实体更新测试（测试支撑），非 BPM 集成 |
| UdcRoleRtController | non-flow | 角色运行时（role 域），非 BPM 集成 |
| UdcRtPageInfoController | non-flow | 页面信息（page 域），非 BPM 集成 |
| UdcRtPageLogController | non-flow | 页面日志（page/log 域），非 BPM 集成 |
| UdcRuntimeDatabaseController | non-flow | 运行时数据库（db 基础设施），非 BPM 集成 |
| UdcSerialConfigController | non-flow | 序列号配置（serial 域），非 BPM 集成 |
| FormAppInfoController (proxy) | non-flow | 表单应用信息代理转发（proxy 域），非 BPM 集成 |
| FormAppMbController (proxy) | non-flow | 表单应用移动代理（proxy 域），非 BPM 集成 |
| FormAppPcController (proxy) | non-flow | 表单应用 PC 代理（proxy 域），非 BPM 集成 |
| FormReferController (proxy) | non-flow | 表单引用代理（proxy 域），非 BPM 集成 |
| NormalAppInfoController (proxy) | non-flow | 常规应用信息代理（proxy 域），非 BPM 集成 |
| NormalAppMbController (proxy) | non-flow | 常规应用移动代理（proxy 域），非 BPM 集成 |
| NormalAppPcController (proxy) | non-flow | 常规应用 PC 代理（proxy 域），非 BPM 集成 |
| NormalReferController (proxy) | non-flow | 常规引用代理（proxy 域），非 BPM 集成 |
| UdcBaseAppInfoController (proxy) | non-flow | 基础应用信息代理（proxy 域），非 BPM 集成 |
| UdcBaseGeneralController (proxy) | non-flow | 基础通用代理（proxy 域），非 BPM 集成 |
| UdcReferController (proxy) | non-flow | 基础引用代理（proxy 域），非 BPM 集成 |

> udc-common / udc-facade / udc-starter-lowcode 三 jar controller 命中 = 0，无逐类可判（OBSERVATION: 三 jar 不含任何 *Controller）。

## (3) 0 遗漏结论
- **BPM 集成域只读候选全集 = 9 只读 + 3 写侧，跨 6 个 controller**（BpmNodeInfoController / DataFlowRtMapController / DataFlowRtMappingController / DataFlowForBpmController / UdcFunctionNodeController / UdcFormDataQueryController），已全部契约化于 registry-entries.md（9 只读 write=False + 3 写侧 write=True 单列）。
- 40 controller 中 **34 属其他域**（customplan 管理面 4 + deduction 2 + runtime 非-flow 28），**不在本任务（BPM 集成域）范围**，逐类归属理由见 (2)。
- **未发现未契约化的 BPM 域只读端点**：BPM 域 6 controller 的方法已穷尽于 R2 javap（javap -p -v 全量），其余 34 non-flow 未深挖方法体（越界且非必要）。无 BPM 域只读端点被遗漏的反例。
- 域真空判定: 非真空 —— 9 只读 + 3 写侧 ≥ 4，无需扩到相邻版本（bpm-facade 5.3.374 / app-approval 5.3.295 仅作相邻版本参考标注，本轮未用作任何证据，未混写进契约）。

## R7 字节码级路径关键词复核（34 non-flow 逐类 javap 验证）
证据底座: docs/audit/artifacts/udc-flow-5.3.517/non-flow-path-scan.txt（34 节，javap -p -v 只读，全离线，VERIFIED_STATIC_BYTECODE 级路径证据）。
方法: 对 34 non-flow FQCN 各跑 javap -p -v -cp <对应jar>，提取 @*Mapping/value=[...] 行，再过滤 BPM 关键词 (flow/bpm/process/workitem/workorder)。

### 结果: 34/34 全扫，29 confirmed non-flow + 5 FLAGGED（交 main 评估）
- **confirmed non-flow (29)**: 无任何 BPM 关键词命中，逐类 javap 字节码证据确认属 page/log/dtype/app/deduction/attachment/graphql/proxy/serial/role/db/runtime 等域。
- **FLAGGED (5)**: 关键词命中但性质需 main 判断是否扩域补契约:
  1. `CustomPlanController`（customplan）: 命中来自 @RestApiOperation 描述串含 "bpm" 字样（`value="...bpm按钮"`），**非路径字面量**，路径为 `udc-runtime/page-custom/list|test|test/{appName}/{pageGuid}/{pageType}` — 判定**误报**（关键词在描述注释里，路径本身无 BPM 语义）。
  2. `UdcAppLogController`（runtime）: 命中来自日志查询路径 `search/microflow` / `search-details/microflow/flowLog` / `search/dataflow` / `search-details/dataflow` — **log 域按 flow 维度检索日志**，非 BPM 集成端点（查询的是日志数据源类型），判定**边缘**（路径含 "flow" 但语义是日志分类过滤，非流程操作）。
  3. `UdcAttrSnapshotRtController`（runtime）: 命中来自角色名注解 `value=["OrgAdmin","RootOrgAdmin","udcAppDesigner","BpmDesigner","BpmManager"]`，路径 `udc-runtime/attr-snapshot/delete-by-data-id/{dataId}` — 判定**误报**（关键词在 @PreAuthorize/@Roles 角色枚举里，非路径）。
  4. `UdcEntityUpdateRtTestController`（runtime）: 命中同上（角色名 `BpmDesigner/BpmManager`），路径 `udc-runtime/update-test/update-with-fields` — 判定**误报**（测试支撑 + 角色注解，非流程端点）。
  5. `UdcBaseGeneralController`（runtime/proxy）: 命中来自路径字面量 `create-bpm` / `update-bpm` / `microflow/{microFlowName}` / `host/microflow/{microFlowName}` / `dataflow/{entityName}/{restMappingName}/...`，共 10 行 — 判定**真命中**（proxy 通用 controller 含 BPM/微流程路径，语义上疑为 BPM/微流程集成端点，但挂 proxy 通用控制器下，非专门 flow controller）。

### R7 结论（对 R6「0 遗漏」结论的修正）
- R6「0 遗漏」结论基于 34 类逐类口头归属（OBSERVATION 级）→ R7 升级为字节码级路径关键词验证（VERIFIED_STATIC_BYTECODE 级）。
- **强化**: 29/34 确认 non-flow（无 BPM 关键词），R6 结论对这 29 条不变。
- **5 FLAGGED 逐条交 main 评估**: 其中 1(#1 CustomPlan)/3(#3 AttrSnapshot)/4(#4 EntityUpdateRtTest) 判定误报（关键词在描述串/角色注解，非路径）；#2 UdcAppLog 边缘（log 域按 flow 检索，非 BPM 端点）；**#5 UdcBaseGeneralController 真命中**（路径含 `create-bpm`/`update-bpm`/`microflow/{name}`/`dataflow/{entityName}/...`），建议 main 评估是否扩 BPM 集成域契约边界补入该 proxy controller 的 flow/microflow 只读端点（如评估扩域，须另行发 HANDOFF 明确范围，implementer 不自行扩）。
- 若 5 FLAGGED 全部维持 non-flow → 0 遗漏结论强化（34/34 confirmed non-flow）；若 #5 扩域 → 需新 HANDOFF 定边界。

## R7 main 裁定（R8 收口落地，2026-09-19）
main 独立复核 34/34 全扫通过，5 FLAGGED 逐条定性（R7 自判 → main 裁定结论一致）：
- #1 CustomPlanController：关键词在 @RestApiOperation 描述串（"bpm按钮"），路径 `udc-runtime/page-custom/*` 无 BPM 语义 → **confirmed non-flow**（误报）。
- #2 UdcAppLogController：log 域按 flow 维度检索日志（`search/microflow` / `search/dataflow` / `flowLog`），非 BPM 专属端点 → **confirmed non-flow**（边缘，日志分类过滤，非流程操作）。
- #3 UdcAttrSnapshotRtController / #4 UdcEntityUpdateRtTestController：关键词在角色枚举 `BpmDesigner`/`BpmManager`，非流程端点 → **confirmed non-flow**（误报，关键词在 @Roles/@PreAuthorize 枚举里）。
- #5 UdcBaseGeneralController（proxy 族，无类级前缀）：真命中 `create-bpm`/`update-bpm`（写侧）+ `dataflow/{entityName}/{restMappingName}` + `microflow/{name}`。

### 不扩域裁定（main 原文结论）
#5 **不扩流程域边界**，理由三条：
1. `microflow/{name}` 属**微流程域**（并发微流程会话 C1/C2/C3 已推进），非本任务 BPM 集成域；
2. `create-bpm`/`update-bpm` 为**写侧**，不属本任务只读契约范围（写侧已单列 fillErrorFlowData 登记不放开）；
3. 本任务非目标明确「不评价其他域」，proxy 族透明转发层不纳入本域 6 controller 专属契约。
→ #5 记为 **MERGE 移交项 ④**（见 registry-entries.md MERGE 说明区），交 UDC-MERGE 与微流程域合并裁定，本任务不落地。

### 结论
- 34/34 confirmed non-flow → **R6「0 遗漏」结论强化**：BPM 集成域只读候选全集 = 9 只读 + 3 写侧（6 controller），未发现未契约化的 BPM 域只读端点；#5 proxy 层 flow/microflow 透明路径归 MERGE 移交项④，不在本域范围。
- 本任务域边界穷尽：全离线（javap 只读、无 LIVE）、无相邻版本混写、冻结件零写入、未碰 6 BPM controller、未拼网关前缀。

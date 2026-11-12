# udc/write-chain 索引

> 为什么有这个文件：本目录有 **45 个事实件**，此前一个都没登记 INDEX。
> 按文件名搜不到 → 等于没沉淀。这里给一张可检索的表。
>
> ★ 本表由 `tools/core/facts/gen_write_chain_index.py` 生成，不要手改。
> ★ 新增事实件后重跑生成器。

## 读法

```
LIVE / LIVE PASS               真发过请求、真回读过（可信度最高）
VERIFIED_STATIC_BYTECODE       反编译坐实代码路径，没跑过
UNVERIFIED                     推测，不能当依据
未标                            作者没写等级 —— 用前先看正文有无实测记录
```

## 文件表

| 文件 | 主题 | 等级 | 行数 |
|---|---|---|---|
| `appname-key-npe-and-connector-target.md` | output.appName 缺键 = 检测面硬 NPE；CONNECTOR 监听目标 = 连接器动态 DTO | LIVE | 133 |
| `attribute-aggregation-write-chain.md` | 属性「汇总值」写链（calculate=AGGREGATION）—— AggregationDto 契约 | LIVE PASS | 104 |
| `build-deploy-live-workflow.md` | 构建/发布 REST 工作流 —— 端到端 LIVE 取证（2026-10-15） | LIVE | 176 |
| `consistency-detection-workflow.md` | 页面一致性检测与修复 REST 工作流 —— LIVE 取证（2026-10-15 下午） | LIVE | 122 |
| `ctpenum-vs-udc-enum-mechanism.md` | CTPENUM 字段的枚举归属：平台枚举(ctp_enum) vs 选项集(udc_enum) —— 字节码 + LIV | LIVE | 92 |
| `custom-app-create-npe-relationapps-root-cause.md` | udc.custom-app.create NPE 根因（create4CustomPage · relationApp | LIVE PASS | 311 |
| `dataflow-rule-0043-root-cause.md` | UDC 生单规则 —— 0043 根因闭环与权威写链契约 | LIVE PASS | 99 |
| `dataflow-rule-rest-write-chain.md` | 生单规则（DataFlow）REST 写链 —— 全链打通 | LIVE PASS | 242 |
| `deduction-and-dataflow-rules-model.md` | UDC 扣减规则 / 生单规则 —— 数据模型与权威契约（MySQL LIVE + CFR） | LIVE | 135 |
| `deduction-rule-detail-structure.md` | udc_deduction_rule_detail 明细结构契约（LIVE + STATIC） | LIVE | 297 |
| `deduction-rule-rest-write-chain.md` | 扣减规则写链 REST LIVE（扣除域，此前全库 0 行） | LIVE | 117 |
| `deduction-rule-runtime-vacuum.md` | 扣减规则运行态 —— VACUUM 负证据 + 设计态契约闭合（B-2 收口，D5 口径） | LIVE | 402 |
| `designer-save-protocol.md` | udc.designer.protocol｜页面设计器保存/提交协议（前端源码级） | 未标 | 79 |
| `detection-read-source.md` | 一致性检测面的读源机制（LIVE 取证 + 定论） | LIVE | 60 |
| `draft-warn-masking-mechanism.md` | 微流程 04003(WARN) 的掩蔽机制 + SERVICE 型发布 + 04004 真因族 | LIVE PASS | 135 |
| `endnode-selectparam-scope.md` | 微流程结束节点 SelectParam 作用域解析（04004 最后一条真因） | LIVE PASS | 73 |
| `entity-attribute-realmachine-write-chain.md` | 实体属性真机写链（CDP 取证）—— udcAttributeGroupOperateBatchPost | LIVE PASS | 129 |
| `event-rest-write-chain.md` | 事件域（udc_event）REST 写链 —— 全链打通 | LIVE PASS | 114 |
| `evidence/R1-app-create-20260930.md` | R1 建应用环｜证据件（test2 活体 · 2026-09-30 CST） | LIVE | 105 |
| `evidence/R1-app-create-unblock-20260930.md` | R1 unblock 环｜证据件（test2 活体 · 2026-09-30 16:30 CST） | 未标 | 74 |
| `evidence/R1-app-create-unblock-v2-20260930.md` | R1 unblock v2（路由修正）环｜证据件（test2 活体 · 2026-09-30 16:49 CST） | 未标 | 73 |
| `evidence/R1-app-create-unblock-v3-20260930.md` | R1 unblock v3（静默成功排除 + 独立建应用主线 B）环｜证据件（test2 活体 · 2026-09-30 | LIVE PASS | 86 |
| `evidence/R2-entity-create-20260930.md` | R2 实体环｜证据件（test2 活体 · 2026-09-30 18:14 CST） | LIVE PASS | 87 |
| `evidence/R3-page-create-20260930.md` | R3 页面环｜证据件（test2 活体 · 2026-09-30 18:44 CST） | LIVE PASS | 87 |
| `evidence/R4-data-write-20261001.md` | R4 数据写入环 · 实测汇总（2026-10-01 03:53–04:25 +08 · test2 活体 · impl | LIVE PASS | 80 |
| `expression-token-type-domain.md` | 表达式 token 类型域与系统变量面（写链事实件） | LIVE | 170 |
| `holder-javatype-contract.md` | 微流程 holder 的 dataType ↔ javaType 契约（权威表 + 适用边界） | LIVE | 96 |
| `input-output-appname-dependent-app-gate.md` | UDC_MICRO_FLOW_04004「依赖应用已删除」= input/output 的 appName 未跨接依赖应 | LIVE PASS | 100 |
| `menu-default-page-write-chain.md` | 菜单写链（PAGE 子节点 / default_page / 树回读）—— 全链打通 | LIVE PASS | 191 |
| `microflow-editor-crash-root-cause.md` | 微流程编辑器"点击报错"根因 —— jsonSchema + 节点字段完整性 | LIVE | 101 |
| `microflow-fullnode-audit-r2.md` | 标准微流程全节点审计报告（重做版，打回后补充事实） | LIVE | 49 |
| `microflow-node-catalog.md` | 微流程节点契约目录 + data_schema 结构（真机/DB 取证） | 未标 | 189 |
| `microflow-node-live-verification.md` | 微流程节点真机批量验证（10 类节点 LIVE + 检查/日志闭环） | LIVE PASS | 140 |
| `microflow-node-panel-snapshot.md` | UDC 微流程节点面板快照 —— 事实证据采集法（17 节点全量） | 未标 | 41 |
| `microflow-publish-event-candidates.md` | UDC 微流程「事件投递」节点事件候选池 —— 权威契约与根因（LIVE + CFR 双证） | LIVE | 105 |
| `microflow-realmachine-write-chain.md` | 微流程真机写链 + 检查日志取证 | LIVE PASS | 125 |
| `microflow-rest-write-chain.md` | 微流程写链 REST 全链 LIVE 取证（2026-10-15） | LIVE | 141 |
| `microflow-vs-pagerule-node-domains.md` | 微流程 vs 页面规则 —— 节点域分离（权威纠正） | LIVE PASS | 157 |
| `page-schema-protocol.md` | udc.page.schema｜页面设计器拖拽 Schema 协议 | 未标 | 119 |
| `pagerule-node-flow.md` | 页面规则域（type=1 FRONTEND）节点流转 —— 真机验证 | LIVE | 105 |
| `refer-config-rest-write-chain.md` | 参照域（udc_refer_config）REST 写链 —— 全链打通 | LIVE PASS | 123 |
| `sandbox-build-deploy-chain.md` | SANDBOX 构建部署机制 —— 权威事实（CFR 字节码 + LIVE 双源） | LIVE | 105 |
| `standard-microflow-node-flow.md` | 标准微流程（type=SERVICE）节点流转 —— 真机验证 + 修正 | 未标 | 104 |
| `url-ledger.md` | url-ledger | LIVE | 119 |
| `write-chain.md` | udc.write-chain｜建应用→实体→页面→数据 写路径全链（九段式事实格 · 骨架 + R1 段） | LIVE PASS | 511 |

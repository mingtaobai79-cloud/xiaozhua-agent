# UDC 平台补全 —— 进度看板（PROGRESS）

> **本文件是入口卡片，只放当前结论。**
> 历史全文（1,570 行倒序堆叠，2026-10-14 → 10-16 第五十三轮，逐字保留）已迁至
> `docs/ledger/LOG-udc-semantics-PROGRESS-20261014-20261016.md`。
> 该线对应 cron 已于 2026-10-16 停止，不再新增轮次记录。

## 当前结论（2026-11-07 复核）

### 已完成（有仓内耐久证据 + 护栏）
- **微流程 nodes**：50 Activity 类、48 码全表、每节点必填（本地 PASS）。
- **微流程 条件**：22 操作符 + GROUP 嵌套 + LogicalOperator（LIVE 实证，标品字节级）。
- **微流程 DATA_MAPPING**：mappingRows / REFERENCE|CONSTANT / ENTITY|DTO（LIVE 实证 path 元素）。
- **实体/属性**：EntityBaseDto/BaseUdcAttributeDto 必填；LIVE 从零构造 → 创建 → 回读一致。
- **页面/布局**：PageDefinitionDto/PageLayoutDefinitionDto + PageTypeEnum + pageItems.urlType（LIVE 创建成功）。
- **菜单/导航**：FunctionNodeDto/FunctionDto + 交互表 `udc_function_node`（LIVE 创建 + 回读一致）。
- **平台操作面**：299 REST + 240 GraphQL；op 命名规则字节码实证；full_path 拼接缺陷已修；
  udc-web 契约 657→674 端点；部署态 544 jar 扫描；三个并行 metadata 面已澄清
  （`/udc/meta-data/` 32 / `/udc/design-metadata/` 47 / `/udc/metadata/` 105，口径不可混用）。
- **存储层**：Redis key 模式 LIVE 实证 + 99 张交互表。

### 未完成 / 阻塞
- **余 60 条 op 仍 UNVERIFIED**：前端 346 op 中 231 已归位，92 未归位里 32 已跨构件归位，
  余 60 条在 Artifactory 静态域与部署态 udc-*.jar 域内**均 0 命中**（同域对照 674/674 PASS 后才成立）。
  域边界：只裁 `udc-*.jar`，`boot-starter-*` 等其余 522 jar 未纳入，**不得对全平台下结论**。
- **BPM / ORG / USER 域**：仅得 facade API 契约（30/132、44/342、41/199）；
  biz 类在加密 `assemble.jar` 内，本地无实现 → 该三域无法从零构造验证。
- **口径冲突（未裁决）**：微流程节点类数存在 **20 / 22 / 24** 三套说法；本线以 22 类为
  `capability-matrix` 基线，审计侧 `MICROFLOW-24-NODE-CONTRACTS.md` 记 24 类（含结构节点）。
  需先定主源口径再合并，见 `docs/plans/doc-consolidation-progress.md` 三·4（下一批候选）。

### 权威入口
- 模型：`components/udc/{microflow,entity,page,menu}_constraints.py`、`components/udc/graphql_op_naming.py`
- 文档：`docs/audit/udc-semantics/` 下 `PLATFORM-*` / `RUNTIME-*` / `DEPLOYED-*` / `COMPONENT-*`
- 逐节点契约：`MICROFLOW-<ACTION>-CONTRACT.md`（34 份，归属见本目录 `README.md`）
- 方法：skill `xiaozhua-constraint-extraction`
- 域进度表 / 已落模型清单 / 下一代下一步：见归档件「## 域进度」「## 已落模型 / 文档」「## 下一步（按序）」

### 证据纪律（本线自证）
- 复算器与护栏：`tests/udc/test_{deployed_op_surface,deployed_lib_inventory,metadata_planes,
  dynamic_register_channel,full_domain_op_surface,deployed_marker_closure,route_implementation_verdict}.py`
- 不变量：证据件必须能由复算器**字节级**重现（parsed 判等不够，换行漂移对其隐形）。
- 可变域计数（如 `jars_scanned`）**不得当契约**——那是环境指纹。
- 测试通过数不是契约，一律以实测为准。

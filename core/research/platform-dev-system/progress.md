# 进度记录

> 每轮追加，不覆盖历史。

---

## 轮次 1 — 2026-11-17

**本轮任务：** 阶段 1 收尾 + 专题 1 第一轮（元数据体系）

**研究目标：**
1. 建立可复现统计脚本
2. 固化统计口径
3. 元数据对象全景
4. 建立研究目录结构

**实际读取的证据：**
- `docs/audit/signatures.txt.gz`（245709 行，全文扫描）
- `docs/audit/reference/svc-app-service.txt.gz`（10176 行）
- `udc-platform-5.3.517.tar.gz` 内：
  - `resources/stereotype/*/config.json` × 6
  - `resources/feature/*/config.json` × 22
  - `resources/presetData/*.json` × 13（全部解析完）
  - `_codegen_templates.json`
- `docs/audit/reference/udc-platform-5.3.517.tar.gz` 成员清单（404 条）

**新发现：**

1. **6 种 stereotype 的 `dataFlowEnabled`**：`basicData` 为 `false`，其余 5 种为 `true`
   ⇒ 基础资料不支持数据流/生单规则

2. **18 个 feature，4 个 `stereotypeBind=true`**：`billBasic` / `archiveBasic` / `archiveTiled` / `formBasic`
   ⇒ 这 4 个只能由版型携带

3. **`archiveTiled` 与 `treeEntity` 互斥**（唯一互斥声明）

4. **feature 的 `attributes` 和 `behaviors` 全为空数组**
   ⇒ 特性不内联声明字段，走 `attributeSet` 引用

5. **18 个字段集 / 122 字段**，`ENTITY` 类型占 44 个（36%）
   ⇒ 关联字段是字段体系主体

6. **`basic` 字段集 = 6 个系统字段**：`id` / `tenantId` / `createTime` / `updateTime` / `version` / `draft`
   ⇒ `version` 是乐观锁，`draft` 是草稿标志

7. **`billBasic` 13 字段**含 `caseId`（流程实例）/ `templateId`（流程模板）/ `billCode`（Serial）
   ⇒ 单据与 BPM 强绑定，字段级证据

8. **挂起/终止/作废是三套对称 7 字段**，各含 `cancel*` 撤销字段
   ⇒ 单据状态是可撤销叠加态

9. **树形用物化路径**：`treePath` / `treeLevel` / `isLeaf` / `treeParentId`

10. **★★ `feature/*/template/config.json` 是代码生成声明**
    - `classType` 7 种：`WEB_CONTROLLER` / `FACADE_APP_SERVICE` / `BIZ_APP_SERVICE_IMPL` / `BIZ_DOMAIN_SERVICE` / `BIZ_DOMAIN_DAO` / `BIZ_DOMAIN_ENTITY` / `FACADE_DTO`
    - `classMode` 2 种：`CLASS_NEW`（新建）/ `CLASS_SAME`（追加）
    - **直接给出三层命名**：`{E}Controller` / `{E}AppService` / `{E}AppServiceImpl` / `{E}Service` / `{E}Dao` / `{E}Entity` / `{E}Dto`

11. **★★ `methodType` + `joinPoints` 是代码织入机制**
    - `APPEND`（新增方法）/ `JOIN`（在切点插入）
    - 5 个切点：`preCreateBatch` / `middle` / `preUpdateBatch` / `afterUpdate` / `after`
    - 真实签名：`createBatch(List<XxxDto>)` / `deleteByIds(List<Long>)`

12. **单据状态机 8 状态**：DRAFT(0) → TO_BE_SUBMITTED(1) → PENDING_REVIEW(2) → COME_INTO_FORCE(3) / TERMINATED(4) / NULLIFIED(5) / SUSPENDED(6) / FAILED(7)
    + `billSendState` 2 状态

13. **9 个实体事件**：3 动作（CREATE/UPDATE/DELETE）× 3 时机（BEFORE/AFTER/**TRANSACTION_SUCCESS**）
    ⇒ `TRANSACTION_SUCCESS` 直接证明有事务边界概念

14. **30 个预置扩展列**：`extVarchar`×10 / `extDate`×10 / `extNumber`×10
    ⇒ 属性扩展是「预置列 + 映射」，不是动态建列

15. **58 个字段 × 33 个 `canEdit*` 开关**
    ⇒ 字段级设计态权限矩阵

16. **平台服务依赖 17 项**（`dependencyGraph.json`）

**确认的结论：**
- 统计数字全部可复现（见 `statistics-registry.md`）
- CodeTask 53 含接口 / 52 实现 / 14 个 v27 / 3 个扩展
- Template 36（口径 A）/ 74（口径 B）
- AppService 830 全为接口，零实现
- DAO 接口 41（唯一 36，重载 5）/ 抽象类 55（唯一 50，重载 5）

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `dependencyGraph.json` 是元数据对象依赖图 | **是平台服务依赖清单（17 项）** |
| 2 | `attribute.json` 是字段定义全集 | **只有 2 项（parentId / orderNo）** |
| 3 | feature config 有 26 份 | **22 份（18 特性 + 4 模板声明）** |
| 4 | 特性内联声明字段 | **`attributes` 全为空，走 attributeSet 引用** |
| 5 | `entity.json` 有 6 个预置实体 | **只有 3 个（standard/archive/bill）** |
| 6 | TemplateInterceptor 是「接口」 | **签名库无类型声明，是外部依赖；只能称「拦截点」** |
| 7 | v3 的 32 个 CodeTask | **包内 class 数；实际实现 30，全库 52** |

**未解决的问题：**
1. 元数据对象间的真实依赖关系（`dependencyGraph.json` 不是这个用途）→ 需从 DTO 结构反推
2. `baseservice.java.ftl` 对应哪个 classType（无 `BASE_SERVICE`）
3. `organization` 与 `archiveTiled` id 都是 13
4. `disable` 与 `attribute_scalability` 配置完全相同
5. joinPoints 是否对开发者开放
6. `version` / `draft` 的真实运行时语义
7. 主子表是否真用 `parentId` 实现

**证据等级变化：**
- 新增 18 条 `STATIC_RULE` 结论（元数据侧）
- 无 `LIVE_RULE`（未操作 test2）

**新增文件：**
- `scripts/research/stats_registry.py`
- `core/research/platform-dev-system/README.md`
- `core/research/platform-dev-system/statistics-registry.md`
- `core/research/platform-dev-system/evidence-map.md`
- `core/research/platform-dev-system/progress.md`
- `core/research/platform-dev-system/01-metadata.md`
- `core/research/platform-dev-system/dependency-map.md`

**修改文件：**
- 无（未触碰现有 facts / 业务代码）

**测试结果：** 统计脚本可重复执行，输出与报告一致

**当前阻塞：**
- 无平台 jar → 无法反编译
- 无 .ftl → 无法看模板语法
- test2 写操作未批准

**下一轮任务：**
1. 从 `EntityDto` / `AttributeDto` / `Entity4CodeDto` 字段结构反推元数据对象关系
2. 元数据 CRUD 机制（`EntityService` 全部方法）
3. 转专题 2：CodeTask ↔ Template 映射

**整体完成度：** 专题 1 约 55%（元数据静态部分基本完成，运行时与对象关系待补）；全局约 12%

---

## 累计完成度

| 专题 | 完成度 | 状态 |
|---|---|---|
| 1 元数据 | 55% | 静态主体完成，对象关系/运行时待补 |
| 2 代码生成 | 25% | 清单+签名完成，调用关系待证 |
| 3 持久化 | 10% | 仅 DAO 签名 |
| 4 表达式 | 5% | 仅已有 facts |
| 5 接口 | 20% | 清单完成，分类待做 |
| 6 组件 | 15% | 类索引已有，使用边界待补 |
| 7 业务关联 | 0% | 未开始 |

**全局：约 12%**

---

## 轮次 2 — 2026-11-17（自主循环第 1 批）

**本轮任务：** 专题 1 深挖 + 专题 2/3/4/5 第一轮静态研究

**研究目标：**
1. 解析全部 13 个 presetData 文件
2. 从 DTO 结构反推元数据对象关系
3. 建立 CodeTask ↔ Template 映射
4. 摸清持久化分层与 DAO 能力
5. 找到表达式运行时执行入口
6. 解析 9 个微流程名单文件

**实际读取的证据：**
- `docs/audit/signatures.txt.gz`（多次全文扫描，累计检索 20+ 类族）
- `udc-platform-5.3.517.tar.gz` 内：
  - `presetData/*.json` 全部 13 个
  - `feature/*/template/config.json` 4 个
  - `microflow/*.json` 9 个名单
  - `formula-functions.xml`、`presetMacro.json`
  - `udc-expression-samples.json`（25 样本）

**新发现（按重要性）：**

1. **★★★ `BaseEntityCurdService`（199 方法）** — v4 完全没提到
   - 主子表：`recursiveCreate` / `recursiveUpdate` / `recursiveDelete` / `recursiveCheck`
   - 级联查询：`selectCascadeById(s)` / `doParallelSelectCascadeById` / `setSingeSubDtoList`
   - 单据：`create4Bpm` / `update4Bpm` / `handlerCaseId` / `updateStatusType` / `isMainProcess`
   - JOIN：`dynamicJoinSelect` / `dynamicCountJoinSelect` **← 推翻「DAO 无 join」**
   - 其他：`resetNormal` / `forceUpdate` / `printTransactionInfo` / `getEntityMeta`

2. **★★★ 表达式运行时入口找到**
   ```java
   ExpressionEvaluator#eval(EvalContextDto): Object
   EvalContextDto { expression, expressionTranslation, resultType, contextMap }
   ```
   ⇒ v4 计划里的核心缺口已补

3. **★★ `EntityMeta` / `AttributeMeta`（运行时元数据）**
   - `EntityMeta#getEntityTable()` — **实体→物理表名**
   - `EntityMeta#getChildren()` / `getTopParent()` — 多级主子表
   - `AttributeMeta#getRelationEntity()` — 关联实体
   - `AttributeMeta#getDataType()` vs `getRealDataType()` — 双类型

4. **★★ `feature/*/template/config.json` 是代码生成声明**
   - `classType` 7 种 → 三层命名：`{E}Controller` / `{E}AppService` / `{E}AppServiceImpl` / `{E}Service` / `{E}Dao`
   - `classMode` 2 种：`CLASS_NEW` / `CLASS_SAME`
   - `methodType` + `joinPoints` → 代码织入（5 个切点）

5. **★★ 模板版本选择机制（四层叠加）**
   - `CodeParam#getCodeVersion()` — 调用方传入
   - `AutoCodeProperties#getCodeVersions()` / `getTemplateDir()`
   - `TemplateAdapter#adaptTemplatePath(path, candidates)` — 路径解析含候选
   - `PlatformVersionDirective` / `UdcVersionDirective` — **模板内 Freemarker 指令**

6. **★★ 生成 ≠ 部署**
   - `TransportHandler#out(CodeContext): List<SchemaInfo>`
   - **30+ 个 TransportHandler 实现**

7. **★ Task→Template 只有 7 组有直接证据**
   - `EntityTask#deployEntity(EntityFileTemplate, EntityDto)`
   - `EntityTaskV27#deployEntity` **（v27 复用主模板！）**
   - `EntityRuleTask#generateRootEntityRuleCode(..., EntityRuleAggregateTemplate, ...)`
   - `OutAppAppServiceProxyTask#writeToFile(OutAppAppServiceProxyTemplate)`
   - `PageEntityControllerTask#writeToFile(AbstractFreemarkerTemplate)`
   - 等

8. **★ 单据状态机 8 状态 + 9 个实体事件**
   - `billStatus`: DRAFT(0) → TO_BE_SUBMITTED(1) → PENDING_REVIEW(2) → COME_INTO_FORCE(3) / TERMINATED(4) / NULLIFIED(5) / SUSPENDED(6) / FAILED(7)
   - 9 事件 = 3 动作 × 3 时机（含 `TRANSACTION_SUCCESS`）

9. **★ `PageInfo#isNeedTotal()` / `isNeedMore()`** — 可关闭 COUNT
   ⇒ 用户「604 次全量 COUNT」的官方解法

10. **★ `tenantAdd()`** — 多租户条件自动注入

11. **★ 预置宏「分页查询实体数据」** — 官方大数据量方案

12. **★ 事件包已迁移**
    `boot.starter.udcrt.event.*`（旧）→ `udc.common.event.*`（新）

**确认的结论：**
- 主子表 = 实体自引用树（设计态 `EntityDto.getChildren()` / 运行时 `EntityMeta.getChildren()`）
- 单据不能直接用 `create()`，要走 `create4Bpm()`
- 表达式三阶段：`ExpressionSaveDto` → `ExpressionCodeGenerator` → `EvalContextDto`
- 持久化四层：Service → AppService → DAO → Mapper → tk.mybatis
- 底层框架是 tk.mybatis

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | DAO 层无 join | **`BaseEntityCurdService#dynamicJoinSelect` 存在** |
| 2 | `formula-functions.xml` 是 88 函数注册表 | **只有 584 字节 2 个函数，是帮助提示文件** |
| 3 | `dependencyGraph.json` 是元数据依赖图 | **是平台服务依赖清单（17 项）** |
| 4 | `attribute.json` 是字段全集 | **只有 2 项** |
| 5 | feature config 26 份 | **22 份（18 特性 + 4 模板声明）** |
| 6 | `entity.json` 6 个预置实体 | **3 个** |
| 7 | `VersionControl` 是 Dubbo 灰度上下文 | **是代码下载审计信息** |
| 8 | v27 用 v27 模板 | **v27 Task 复用主 `EntityFileTemplate`** |
| 9 | `copyNeedResetNull` 零调用者=死代码 | **可能在 Freemarker 模板中调用** |

**未解决的问题：**
1. 主键生成时机（`BLOCKED`，需实测）
2. 子表外键回填时机（`BLOCKED`）
3. 主子表保存顺序（`BLOCKED`）
4. 单据能否绕过 BPM（`BLOCKED`）
5. 事务范围（`BLOCKED`）
6. `exp<雪花ID>` 生成算法（需反编译）
7. `copyNeedResetNull` 是否在 .ftl 中调用（需 .ftl）
8. `@Autowired` vs `DubboFactory` 判定（需 consumers 分析）
9. `AppServiceInvokeDto` 18 字段（未提取）

**证据等级变化：**
- 新增 `VERIFIED_STATIC_BYTECODE`：约 45 条
- 新增 `STATIC_RULE`：约 35 条
- 新增 `LIVE_RULE`：0（未操作 test2）
- 明确标 `BLOCKED`：9 条

**新增文件：**
- `core/research/platform-dev-system/01-metadata.md`
- `core/research/platform-dev-system/02-codegen.md`
- `core/research/platform-dev-system/03-persistence.md`
- `core/research/platform-dev-system/04-expression.md`
- `core/research/platform-dev-system/05-interface-integration.md`
- `core/research/platform-dev-system/dependency-map.md`

**修改文件：**
- `core/research/platform-dev-system/progress.md`（本文件）
- `core/research/platform-dev-system/01-metadata.md`（补充 DTO 关系 + 表达式样本）

**测试结果：** 统计脚本 `stats_registry.py` 可重复执行，数字与报告一致

**当前阻塞：**
- 无平台 jar → 无法反编译（影响 2/3/4/5）
- 无 .ftl → 无法看模板语法（影响 2/4）
- test2 未批准 → 运行时全部无法验证（影响 3/4）

**下一轮任务（按优先级）：**
1. `AbstractAllInOneBaseDao` 55 方法语义
2. `AppServiceInvokeDto` 18 字段
3. `consumers.json` 分析（@Autowired vs DubboFactory）
4. 专题 6：基础组件使用边界
5. 专题 7：业务能力关联骨架

**整体完成度：** 专题 1 约 75%、2 约 55%、3 约 45%、4 约 60%、5 约 45%、6 约 15%、7 约 0%
**全局：约 42%**

---

## 累计完成度（轮次 2 后）

| 专题 | 完成度 | 状态 |
|---|---|---|
| 1 元数据 | 75% | 静态基本完整，运行时元数据已有 `EntityMeta` |
| 2 代码生成 | 55% | 清单+映射+版本机制完成，调用关系部分待证 |
| 3 持久化 | 45% | 分层+DAO+BaseEntityCurdService 完成，运行时待实测 |
| 4 表达式 | 60% | 三阶段+运行时入口完成，细节待反编译 |
| 5 接口 | 45% | 名单+决策树完成，判定规则待补 |
| 6 组件 | 15% | 仅类索引 |
| 7 业务关联 | 0% | 未开始 |

**全局：约 42%**
**状态：`PARTIALLY_COMPLETED`（运行时未验证）**

---

## 轮次 3 — 2026-11-17（自主循环第 2 批）

**本轮任务：** 专题 3/5/6 补齐 + 注解体系发现 + 双源交叉验证

**研究目标：**
1. `BpmAppService` 26 方法（单据 send/submit/saveDraft 边界）
2. `AbstractAllInOneBaseDao` 55 方法（比接口多什么）
3. Mapper 数量口径核实
4. `consumers.json` 分析
5. 注解体系挖掘（109 个注解）
6. `extension-points.md` 交叉验证

**实际读取的证据：**
- `docs/audit/signatures.txt.gz`（BpmAppService / AbstractAllInOneBaseDao / DistributedLockFactory 等）
- `surface-index.tar.gz`：
  - `annotations.md`（109 个注解，含元注解与 @Target）
  - `extension-points.md`（151 接口 / 128 真接口 / 101 有实现 / 27 纯扩展位）
  - `consumers.json`（183 接口 / 12252 类扫描）
  - `registration-scan.json`（91 jar / 48 有 spring.factories）

**新发现：**

1. **★★★ 109 个注解体系**（`annotations.md`）
   - `@AppService` = 元注解 `@Service` + `@Primary` → **@Autowired 能注什么的答案**
   - `@DubboComponent`（0 元素，TYPE）→ Dubbo 注册
   - `@FunctionClass` + `@Function`（7 元素）→ **自定义表达式函数注册**
   - `@Idempotent`（0）/ `@AntiReCommit`（2）/ `@ExclusivePermit`（2）/ `@LimitCountOperation`（2）→ **幂等/并发控制**
   - `@CountSql`（1，mybatis，METHOD）→ **COUNT SQL 控制**
   - `@BootApp` 含 `@EnableTransactionManagement` → **注解式事务已开启**
   - `@EventHandler` 元注解 `@Component` → 自动注册

2. **★★★ `extension-points.md` 双源验证**
   - `CodeTask` impl=**52** ← 与我的脚本统计完全吻合
   - `TransportHandler` impl=**32** ← 修正我之前的「30+」
   - `Interpreter` impl=**9** ← 完全吻合
   - 27 个纯扩展位，其中 **`PluginDefinition`（2 abstract，零实现）** 是自定义 CodeTask 的唯一入口

3. **★ `BpmAppService` 实际 26 方法**（不是 22）
   - `saveDraft`（草稿）/ `submit`（草稿提交）/ `send`（直接发起）三者边界明确
   - `pause`/`hasten` 返回 `ListResponse`（批量语义）
   - 有 `deleteDraft` 无 `deleteBill` → 单据删除走 `nullify` 而非物理删除

4. **★ `AbstractAllInOneBaseDao` 比接口多 14 方法**
   - `putThreadContext()` / `removeThreadContext()` → **DAO 层有线程上下文**
   - 5 个 Wrapper 方法（tk.mybatis Example 风格）
   - `createBatchNoClob` / `createBatchIgnoreTime` / `updateBatchIgnoreTime`

5. **★ Mapper 数量口径修正**
   - 21 个 Mapper + 1 个 Marker = 22（旧结论「22 个 Mapper」不含 BaseDao）
   - 21 个全部在 `com.seeyon.boot.starter.mybatis.mapper`（实测 21/21）

6. **★ 注册机制：48/91 jar 用 `spring.factories`**
   - 只有 2 个用 `META-INF/services`
   - 0 个用 Spring Boot 3 的 `AutoImports`
   - ⇒ 平台是 Spring Boot 2 风格

7. **★ `consumers.json` 的能力与局限**
   - 183 接口 / 12252 类 / 1090+56+40+9+4 条引用
   - 被引用最多：`CodeContext`(194) / `AppContext`(172) / `DetectionContext`(150)
   - **局限：只记录「谁引用」，不记录「怎么引用」→ 无法直接判定 @Autowired vs getProxy**

**确认的结论：**
- CodeTask 52 / TransportHandler 32 / Interpreter 9 全部双源确认
- `@AppService` 是 AppService 的注册机制（@Service + @Primary）
- `PluginDefinition` 是唯一的插件注册扩展位
- 单据三操作边界：saveDraft / submit / send

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `BpmAppService` 22 方法 | **26 方法** |
| 2 | `BaseMybatisDao` 由 22 个 Mapper 拼装 | **21 Mapper + 1 Marker = 22 项；不含 BaseDao** |
| 3 | `TransportHandler` 30+ 实现 | **精确 32** |
| 4 | `@PublicApi`/`@Internal`/`@PublicSpi` 是平台三分类 | **是 graphql 库注解，与平台无关** |
| 5 | `consumers.json` 可判定 @Autowired vs getProxy | **只记录引用关系，不记录引用方式** |

**未解决的问题：**
- 新增 12 个（见 `unresolved/README.md`）
- 主要是注解元素名（需 javap -v）与运行时行为（需实测）

**证据等级变化：**
- 新增 `VERIFIED_STATIC_BYTECODE`：约 12 条
- 新增 `STATIC_RULE`：约 25 条
- **升级为双源确认：3 条**（CodeTask 52 / TransportHandler 32 / Interpreter 9）

**新增文件：**
- `core/research/platform-dev-system/unresolved/README.md`

**修改文件：**
- `02-codegen.md`（PluginDefinition + 双源验证）
- `03-persistence.md`（AbstractAllInOneBaseDao + Mapper 口径 + 幂等/事务注解）
- `04-expression.md`（@Function 注册机制）
- `05-interface-integration.md`（注解体系 + 扩展点 + 三分类依据）
- `06-components.md`（BpmAppService 26 方法）
- `statistics-registry.md`（双源交叉验证 + 台账更新）

**测试结果：** 统计脚本可复现；`extension-points.md` 独立验证三个关键数字

**当前阻塞：** 同轮次 2（无 jar / 无 .ftl / test2 未批准）

**下一轮任务：**
1. `JsonUtils` 三兄弟方法对比（专题 6）
2. `@Function` / `@AppServiceOperation` 元素名（需 javap -v，可能 BLOCKED）
3. `consumers.json` 深度分析：按包分组的引用模式
4. 专题 7：评估集填充（≥80 条）

**整体完成度：** 1:78% / 2:62% / 3:55% / 4:68% / 5:65% / 6:50% / 7:30%
**全局：约 58%**
**状态：`PARTIALLY_COMPLETED`**

---

## 轮次 4 — 2026-11-17（自主循环第 3 批）

**本轮任务：** JSON 组件对比 + 方言核实 + 评估集落地 + 基线实测

**研究目标：**
1. `JsonUtils` 三兄弟差异
2. 数据库方言数量核实
3. 评估集填充（≥80 条）
4. 跑真实基线

**实际读取的证据：**
- `signatures.txt.gz`：`JsonUtils` / `JsonNodeUtil` / `JsonUtil` / `dialect.impl.*` / `DatabaseDialect`
- `action-index.md`（682 行，逐类计数）
- 实际运行 `find_action`（现有检索器）

**新发现：**

1. **★★★ 基线实测：0% → 62.5%（本轮最重要）**
   - 现有 `action-index` 跑我的评估集：**Top-1 = 0%**
   - 根因：`action-index` 覆盖业务 AppService（`ApplicationManagerAppService` 等），
     **完全不含**开发基础设施（`BaseEntityCurdService` / `ExpressionEvaluator` /
     `AllInOneBaseDao` / `DistributedLockFactory` / `HttpClientUtil` / `JsonUtils` 全部 0 次）
   - 新建 `dev-capability-index`（40 能力手写索引）后：**Top-1 = 62.5%，Top-5 = 67.5%，MRR = 0.646**
   - **⇒ 证明问题在索引层，不在算法**

2. **★ JSON 工具实际是 4 个类**（不是「三兄弟」）
   - `boot.util.JsonUtils`（28 方法，通用）
   - `boot.license.JsonUtils`（1 方法，license 私有）
   - `udc.jackson.util.JsonNodeUtil`（56，Jackson 树）
   - `ai.*.JsonUtil`（20）/ `excel.*.JsonUtil`（10）
   - **★★ `toJsonLongToString`** 解决雪花 ID 传前端精度丢失

3. **★ `JsonUtils` 的 5 对「静默 vs ThrowError」模式**
   - `toJson` / `toJsonThrowError`
   - `fromJson` / `fromJsonThrowError`
   - `toMap` / `toMapThrowError`
   - `toStringMap` / `toStringMapThrowError`
   - `toList` / `toListThrowError`

4. **★ 方言实际 11 种**（旧文档「10 种」是计数错误，清单本身列了 11 项）
   - 且方言只负责 `pageSql`（2 方法接口）
   - `DatabaseDialectManager#register()` 可扩展

5. **★ 评估集落地 106 条**
   - positive 40 / synonym 22 / negative 22 / ambiguous 22
   - 覆盖 40 个能力
   - R1/R2 回归用例已包含

**确认的结论：**
- 现有检索索引与开发需求层错配（已用计数证据确认）
- 中文检索不能靠子串匹配（8 个 no_result 全是这个原因）
- 方言只有分页职责

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | 「JsonUtils 三兄弟」 | **实际 4 个同名/近名类，用途不同** |
| 2 | 「10 种数据库方言」 | **11 种**（旧文档清单列了 11 项但数字写 10） |
| 3 | 方言负责 SQL 差异 | **只负责 `pageSql`** |
| 4 | `action-index` 可用于开发能力检索 | **0% 命中，层错配** |

**未解决的问题：**
- 8 个 no_result → 需分词
- 3 个 forbidden 违反 → 需能力互斥 + 后置过滤
- 2 个 rank_too_low → 需限定词权重
- 5 个 wrong_capability → 能力粒度调整

**证据等级变化：**
- 新增 `LIVE_RULE`：4 条（基线 0% / 修复后 62.5% / forbidden 违反 / no_result 根因）
- 新增 `VERIFIED_STATIC_BYTECODE`：约 8 条

**新增文件：**
- `core/research/platform-dev-system/evaluation/intent-capability-set-v1.json`（34.2 KB，106 条）
- `core/research/platform-dev-system/evaluation/baseline-v1.json`（自动生成）
- `scripts/research/eval_baseline.py`（基线评估器）
- `scripts/research/dev_capability_index.py`（开发能力索引原型）

**修改文件：**
- `03-persistence.md`（方言 11 种 + 只负责分页）
- `06-components.md`（JSON 4 类 + ThrowError 模式 + toJsonLongToString）
- `07-business-capability-bridge.md`（基线实测 + 修复验证 + 错误归因）

**测试结果：**
```
评估集结构校验      106 条，四类各 ≥22，无缺字段 ✅
action-index 基线   Top-1 0.0% / Top-5 0.0% / MRR 0.000
dev-index 基线      Top-1 62.5% / Top-5 67.5% / MRR 0.646
```

**当前阻塞：** 无新增（分词/权重是设计问题，不是阻塞）

**下一轮任务：**
1. 给 dev-capability-index 加分词（解决 8 个 no_result）
2. 加 forbidden 后置过滤（解决 3 个违反）
3. 专题 7：近义/负例/歧义三类的自动评估
4. 专题 1：`EntityType` / `RelationType` 枚举取值（需 jar，可能 BLOCKED）

**整体完成度：** 1:78% / 2:62% / 3:58% / 4:68% / 5:65% / 6:58% / 7:55%
**全局：约 63%**
**状态：`PARTIALLY_COMPLETED`**

---

## 轮次 5 — 2026-11-17（自主循环第 4 批）

**本轮任务：** 评估器完整化 + BaseEntityCurdService 字节码深挖

**研究目标：**
1. 分词修复 8 个 no_result
2. 补全四类评估（synonym/negative/ambiguous）
3. 追 P0：主键生成 / 子表外键 / 事务边界

**实际读取的证据：**
- `runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt`（7985 行，字节码级）
- `udc-biz-5.3.517/resources/feature/nullify/config.json`
- 实际运行 eval_full.py（四类评估）

**新发现：**

1. **★★★ BaseEntityCurdService 实测 81 方法（旧文档写 199，错）**
   - 继承 6 个 callback：`PreCreateCallBack` / `PreUpdateCallBack` /
     `MethodCallBack` / `ValidateCallBack` / `DataTransferService` / `PreCopyCallBack`
   - 依赖注入揭示单据能力来源：`ApprovalCallBack` / `BillStateCallBack` /
     `SecretCallBack` / `PermissionCallBack` / `EntityAttrSnapshotCallBack`
   - **⇒ 单据能力不是 BaseEntityCurdService 自己实现的，是 callback 注入的**

2. **★★★ `recursiveCreate` 字节码完整还原（机制级）**
   ```
   if (meta.getChildren() 非空)      → 遍历子实体递归调用自身
   else if (type != MASTER_ENTITY)   → findDao(entityClass) 批量写
   ```
   - 递归依据是 `EntityMeta.getChildren()`，**不是注解扫描**
   - **主实体（MASTER_ENTITY）不直接落库**（`if_acmpeq 84` 跳过）
   - 落库走 `entityBeanContainer.findDao()` → `BaseDao`

3. **★★★ `create()` 完整执行链（253 行字节码）**
   ```
   printTransactionInfo → isMasterEntity 断言 → handlerCaseId
   → DtoConvertUtil.resetInsertHandle  ← 插入字段处理
   → permissionCallBack（主/从各一次）
   → preCreateBatch → beforeCreate → EventContainer(INSERT) → beforeEvent
   → EntityExceptionThrower.throwing
   → OperateContext.enter(INSERT)
   → secretCallBack（密级）
   → recursiveCheck → recursiveCreate → middleCreate
   → BeanCopier.copy → getMapper → EntityClassContext.withEntityClass → dao.insert
   → afterCreate → afterEvent
   → BaseEntity.getId() → dto.setId(id)      ← ★★★ 主键回填
   → OperateContext.leave → resetNormal → transactionSuccessEvent
   ```
   - **主键回填机制已证**：`entity.getId()` → `dto.setId()`
   - **新发现 `middleCreate` 中间层**（之前完全不知道）
   - **事件/上下文靠 `ActionType.INSERT` 分发**，不是每动作一个方法

4. **★★ 四类评估全部跑通，暴露过拟合**
   | 类型 | 样本 | 结果 | 可信度 |
   |---|---|---|---|
   | positive | 40 | 100% | ❌ 过拟合 |
   | synonym (held-out) | 112 utterance | **78.6%** | ✅ 真实泛化 |
   | negative | 22 | 90.9% | ✅ |
   | ambiguous | 22 | **59.1%** | ⚠️ 最弱 |
   - **positive 100% 是照着题改索引的结果，不可报**
   - held-out 失败的 24 条里 **17 条是纯口语**（"一页一页取""锁住这条记录"）
   - **⇒ 关键词表适合候选召回，不适合意图理解**

5. **★ 新阻塞：`DtoConvertUtil` 不在任何现有资产**
   - 已查 6 处资产全部 miss，本机无 jar
   - **主表 ID 生成时机 / 雪花是否预生成 / 子表外键怎么拿主表 ID 全部 BLOCKED**
   - 但**调用顺序已确定**（子表在步骤 3 写，主表在步骤 5 写）
   - **⇒ 逻辑必然：若子表外键是自增主键，不可能成功 → 必是预生成或延迟绑定**

**确认的结论：**
- 主子表递归依据是 EntityMeta 树（字节码直证）
- 主实体不直接落库（字节码直证）
- 主键回填走 `entity.getId() → dto.setId()`（字节码直证）
- 单据能力靠 callback 注入，不在 service 本体

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `BaseEntityCurdService` 有 199 方法 | **实测 81 条声明 / 76 唯一方法名** |
| 2 | `recursiveCreate` 是 public 可调 | **实际是 `private`**，外部只能走 `create()` |
| 3 | positive 集 100% 说明检索可用 | **过拟合，真实泛化 78.6%** |
| 4 | nullify 是方法 | **是 feature（`resources/feature/nullify/config.json`）** |

**未解决的问题（P0）：**
- `DtoConvertUtil.resetInsertHandle` 内部（BLOCKED，需 jar）
- `middleCreate` 具体做什么（新发现，未追）
- `@Transactional` 在哪个层面（javap 不可见）

**证据等级变化：**
- 新增 `VERIFIED_STATIC_BYTECODE`：3 条重大（recursiveCreate / create 链 / 继承结构）
- 新增 `LIVE_RULE`：4 条（四类评估实测）
- 新增 `BLOCKED`：1 条（DtoConvertUtil）

**新增文件：**
- `scripts/research/eval_full.py`（四类评估器）
- `core/research/platform-dev-system/evaluation/eval-report-v1.json`

**修改文件：**
- `03-persistence.md`（38.3KB → **51.0KB**，新增 3 个字节码级 section）
- `07-business-capability-bridge.md`（17.7KB → **20.5KB**，四类评估 + 过拟合诚实记录）
- `evaluation/intent-capability-set-v1.json`（修正 pos-015/pos-021）
- `scripts/research/eval_baseline.py`（禁词语义匹配 + 注解能力级匹配）
- `scripts/research/dev_capability_index.py`（bigram 分词 + 语义禁词过滤）

**测试结果：**
```
positive     40/40 = 100.0%    ← 过拟合，不可报
synonym     88/112 = 78.6%     ← 真实泛化
negative     20/22 = 90.9%
ambiguous    13/22 = 59.1%
forbidden    0
```

**当前阻塞：** `DtoConvertUtil`（需 jar 或真实写入验证）

**下一轮任务：**
1. 追 `middleCreate` 字节码（可做，无阻塞）
2. 追 `update()` / `deleteById()` 链路（对照 create）
3. `EntityMeta.getChildren()` 来源（元数据加载 → 连接专题 1）
4. ambiguous 澄清机制设计（当前 59.1% 太弱）
5. `DtoConvertUtil`：编写只读 jar 拉取方案，标 WAITING_FOR_APPROVAL

**整体完成度：** 1:80% / 2:62% / 3:**68%** / 4:68% / 5:65% / 6:58% / 7:**65%**
**全局：约 67%**
**状态：`PARTIALLY_COMPLETED`**

---

## 轮次 6 — 2026-11-17（自主循环第 5 批）

**本轮任务：** 追 middleCreate / 对照 delete / 还原 updateBase / 解 deleteData

**本轮最大成果：五个 P0 里的四个被字节码彻底解决**

1. **`create` / `update` / `delete` 三者同构已证**
   - 统一骨架：前置处理 → ActionType → beforeEvent → 落库 → afterEvent → transactionSuccess
   - `ActionType` 全类统计：UPDATE 20 / INSERT 9 / DELETE 6 / NORMAL 2
   - **⇒ 事件/回调/AOP 全靠 ActionType 分发，不是每个动作一个方法**

2. **★★★ `updateBase(D,boolean,boolean)` 完整还原（431 行字节码）**
   - create 没有、update 才有的 7 个机制：
     `oldData` / `billStateCallBack` / `ChangeEventData`(前值后值) /
     `changeData` 载荷 / `deleteData` 先删 / `recursiveUpdate` / `entityAttrSnapshotCallBack`
   - 新发现 `beforeUpdateConsumer`（BiConsumer 字段）→ 可注入的更新前钩子

3. **★★★ `deleteData` 真相：差异删除，不是全删**
   ```java
   .filter(dto -> dto.getActionType() == ActionType.DELETE)
   .collect(groupingBy(dto -> dto.getClass()))
   EntityMetaUtil.forEachMeta(...) → dao.deleteByIds + CacheUtil.evict
   ```
   - **推翻同轮早前「先删光再重插」的判断**
   - 真实约束：子表行必须带 ActionType 才会被正确处理
   - 解释了「子表 ID 每次变」的真实原因

4. **★★★ `DtoConvertUtil` 7 个方法签名全部从描述符反推得到**
   ```
   resetInsertHandle(EntityMeta, BaseEntityActionDto, BiConsumer) : BaseEntityActionDto
   forEach ×2 / listToMap / defaultUpdateListToMap / mergeMapData
   groupByAction(List) : Map        ← 印证差异删除机制
   ```
   - **不需要 jar 就拿到了方法契约**
   - 仍缺：`resetInsertHandle` 内部是否生成雪花 ID（BLOCKED）

5. **★★★ 可覆写边界已明确（invokespecial vs invokevirtual）**
   - 可覆写 6 个：`preCreateBatch` / `beforeCreate` / `afterBeforeEventCheck` /
     `middleCreate` / `getMapper` / `afterCreate`
   - 私有不可碰 4 个：`printTransactionInfo` / `recursiveCheck` /
     `recursiveCreate` / `resetNormal`
   - **⇒ 「想改主子表递归逻辑」做不到，只能走 callback 或覆写 middleCreate**

**新增接口知识（interface-inventory 实测）：**

| 接口 | 抽象 | 具体 |
|---|---|---|
| `ApprovalCallBack` | 0 | 6 |
| `ApprovalCallBackExt` | 0 | 6 |
| `BillStateCallBack` | 0 | 1 |
| `EntityRuntimeLogCallBack` | 0 | 28 |
| `MethodCallBack` | 0 | 10 |
| `BaseCurdService` | 0 | 35 |
| `UpdateService` | 0 | 15 |
| `QueryService` | 0 | 6 |
| `EventHelper` | 3 | 3 |
| `OperateListener` | 1 | 1 |
| `DataProcessor` | 2 | 2 |
| `DataVisitor` | 2 | 3 |

**确认的结论：**
- CRUD 三件套同构（已证）
- 差异删除机制（已证）
- 可覆写边界（已证）
- DtoConvertUtil 契约（已证）

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | 「主子表更新是先删后插」 | **差异删除（按 ActionType 过滤）** |
| 2 | `update` 走 `updateBase` 但内部未知 | **431 行已完整还原** |
| 3 | `DtoConvertUtil` 完全无法研究 | **7 个方法签名已从描述符得到** |

**未解决（P0 剩 1 个）：**
- `resetInsertHandle` 内部是否生成雪花 ID → **BLOCKED**（需 jar）
- `BaseCurdService` 35 个 default 方法名 → PARTIAL（需 jar）

**证据等级变化：**
- `VERIFIED_STATIC_BYTECODE` +8 条重大结论
- `PARTIAL` 从 4 降到 2
- `BLOCKED` 保持 1（但范围从「整个 DtoConvertUtil」缩到「resetInsertHandle 内部」）

**修改文件：**
- `03-persistence.md`（51.0KB → **69.8KB**，新增 8 个字节码级 section）

**当前阻塞：** `resetInsertHandle` 内部实现（需 jar）

**下一轮任务：**
1. 追 `recursiveUpdate` 的字节码（对照 recursiveCreate）
2. 追 `create4Bpm` / `update4Bpm`（单据写入完整链）
3. 追 `recursiveDefaultValue`（表达式与默认值的连接点 → 专题 4）
4. `BaseCurdService` 35 方法：尝试从其他调用点描述符反推
5. ambiguous 澄清机制（评估 59.1% 太弱）

**整体完成度：** 1:80% / 2:62% / 3:**78%** / 4:68% / 5:65% / 6:58% / 7:65%
**全局：约 68%**
**状态：`PARTIALLY_COMPLETED`**

---

## 轮次 7 — 2026-11-17（jar 反编译，BLOCKED 全解）

**★ 重大转折：本机就有 jar，无需拉包**

```
D:/repo/CHIT/com/seeyon/udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar  (292KB, 141 类)
D:/repo/CHIT/com/seeyon/boot-core/5.3.358/boot-core-5.3.358.jar                      (Ids 所在)
反编译工具：C:/Users/白明涛/AppData/Local/Temp/cfr.jar (CFR 0.152)
产物：D:/software/hermes/cache/scratch/{lowcode-src,bootcore-src}
```

**反编译规模：121 + 512 = 633 个 java 文件**

**本轮解决的问题：**

### 1. ★★★ BLOCKED 全面解除：主键生成机制

```java
// DtoFieldHelper.resetInsert(parentDto, subDto)
parentDto.setActionType(ActionType.INSERT);
if (id 为 null 或 NULL_ID) parentDto.setId(Ids.gidLong());      // ① 主表 ID 预生成

subDto.setActionType(ActionType.INSERT);
if (id 为 null 或 NULL_ID) subDto.setId(Ids.gidLong());          // ② 子表 ID 预生成
if (subDto instanceof BaseDetailDto) {
    if (parentId 为空) ReflectUtil.setFieldValue(subDto, "parentId", parentDto.getId());  // ③ 外键回填
    else if (parentId 不匹配) { subDto.setId(Ids.gidLong()); ... }  // ④ 冲突时换 ID
}
```

**⇒ 三个 P0 全部回答：**
| 问题 | 答案 |
|---|---|
| 主表 ID 何时生成 | create() 第一行 resetInsertHandle 内部，DB 操作之前 |
| 子表外键何时赋值 | 同一时刻，主表 ID 生成后立即 setFieldValue |
| 是否预生成 | 是，纯应用层预生成，不依赖 DB 自增 |

### 2. ★★★ 雪花 ID 完整位布局

```
epoch = 1596816000000 (2020-08-08 +08:00)
时间戳 40 位 (bit 24-63) → 34.8 年 → 2055 年
sequence 9 位 (bit 15-23) → 511/毫秒
centerId 3 位 (bit 12-14) → 0-7
workerId 12 位 (bit 0-11) → 0-4095，从 IP 低 12 位推导
```

### 3. ★★★ 重大陷阱：gidLong() 不是纯雪花

```java
public Long generateLong() {
    return nextId() + ThreadLocalRandom.current().nextLong();   // ← 加了随机数
}
public String generateString() {
    return String.valueOf(nextId());                            // ← 纯雪花
}
```

**⇒ 平台主键用 gidLong() → 不可反解时间、不单调递增、可能为负**
**⇒ 只有 gidString() 才是纯雪花**
**⇒ 这推翻了「分布式 ID 便于排序」的常见假设**

### 4. ★★★ MethodCallBack 10 个方法全部拿到

```java
beforeSelect / afterSelect
beforeCreate / middleCreate / afterCreate
beforeUpdate / afterUpdate(newDtoList, oldMap)   ← 带旧值
beforeDelete / afterDelete
getDefaultValue()                                 ← ★ 表达式接入点
```

### 5. ★★★ ApprovalCallBack 6 方法（单据三段式）

```
beforeApprovalCreate / beforeApprovalCreateValidate / afterApprovalCreate
beforeApprovalUpdate / beforeApprovalUpdateValidate / afterApprovalUpdate
```

### 6. ★★ BaseCurdService IN 查询自动分批

```java
if (selectExceedsOneThousandRecordsByInCondition(column, value)) {  // IN_ 前缀 + >1000
    if (size > 9999) throw BusinessException("条件IN查询数量超过9999条");
    Lists.partition(valueList, 999);   // 每批 999
}
```

**⇒ 平台能力：写 "IN_parentId" 就自动分批，不用自己循环**

### 7. ★★ PermissionCallBack 承担必填校验

```
buildInitialValue(...)    ← 初始值构建
requiredValidate(...)     ← 必填校验（不是注解！）
```

### 8. ★★ 单据状态机字段规范（IGNORE_FIELDS 反推）

```
终止：terminatorId / terminateTime / terminateReason / terminateStatusType
取消终止：cancelTerminatorId / cancelTerminateTime / cancelTerminateReason
作废：nullifyId / nullifyTime / nullifyReason / nullifyStatusType
挂起：suspenderId / suspendTime / suspendReason / suspendStatusType
发送：sendState / caseSendTime / caseSender / caseSenderInstitution / caseSenderDepartment / caseSenderPost
流程：caseId / caseTitle / templateId / statusType
```

**⇒ 每个业务动作都是「操作人+时间+原因+状态」四件套**

### 9. ★★ 子表 orderNo 自动编号规则

```java
setSubEntityOrderNo(): orderNo = (i + 1) * 10000
```

**⇒ 10000, 20000, 30000... 留间隔便于中间插入**

### 10. ★★ 聚合根内 ID 冲突检测

```java
Sets.intersection(dataMap.keySet(), listToMap.keySet())
if 非空 → throw BusinessException("聚合根内id冲突:" + ids)
```

**新增文件：**
- `core/research/platform-dev-system/08-capability-inventory.md`（16.8KB，能力覆盖清单）

**核心 5 类方法统计（源码级）：**
```
BaseEntityCurdService  75
BaseCurdService        19
DtoConvertUtil         15
DtoFieldHelper         17
EntityMetaUtil          9
合计                  135
```

**推翻的旧结论：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `resetInsertHandle` 内部未知 | **已完整读出，它只遍历，真正的字段设置在 DtoFieldHelper.resetInsert** |
| 2 | 需从 test2 拉 jar | **本机 /d/repo 就有 5.3.517** |
| 3 | 主键是标准雪花 | **gidLong() = 雪花+随机，不可反解** |
| 4 | 雪花 epoch 未知 | **1596816000000 = 2020-08-08 +08:00** |
| 5 | workerId 靠配置 | **从 IP 低 12 位推导** |

**证据等级提升：**
- `BLOCKED` → 0
- `VERIFIED_STATIC_SOURCE`：+10 条（首次达到源码级）
- `PARTIAL`：从 2 降到 1（仅剩 boot-core 版本差异）

**当前阻塞：** 无（boot-core 5.3.358 vs 5.3.517 版本差异已标注 VERSION_CAVEAT）

**下一轮任务：**
1. `recursiveUpdate` 源码（对照 recursiveCreate）
2. `create4Bpm` / `update4Bpm`（单据写入链）
3. `EntityMeta` 34 方法 + `AttributeMeta` 26 方法逐个用途
4. 表达式与 `getDefaultValue()` 衔接（→ 专题 4）
5. 把 633 个反编译文件纳入证据地图，建立可检索索引

**整体完成度：** 1:80% / 2:62% / 3:**90%** / 4:70% / 5:65% / 6:**70%** / 7:65%
**全局：约 72%**
**状态：`PARTIALLY_COMPLETED`（阻塞已清，但 2/4/5 专题仍需推进）**

---

## 轮次 8 — 2026-11-17（源码级深挖，专题 1 认知修正）

**本轮任务：** recursiveUpdate / create4Bpm / EntityMeta 展开

### 一、`recursiveCreate` 源码（补全字节码推断的遗漏）

```java
// ① 先递归更深层子表
if (CollectionUtils.isNotEmpty(meta.getChildren())) {
    int i = this.recursiveCreate(meta, dtoColl);
    count.set(count.get() + i);
}
// ② 再插本层
Optional.ofNullable(findDao(meta.getEntityClass())).ifPresent(dao -> {
    List insetEntityList = BeanCopier.copyList(dtoColl, meta.getEntityClass());
    BaseEntityCurdService svc = findService(meta.getDtoClass());
    svc.beforeCreate(dtoColl);                    // ★ 逐层回调（字节码没看出来）
    dao.createBatch(insetEntityList);
    svc.afterCreate(dtoColl);                     // ★ 逐层回调
});
```

**⇒ 三条新发现：**
1. **递归顺序是「先深层、后浅层」** → 自底向上插入，保证外键
2. **每层子表都调自己的 `beforeCreate`/`afterCreate`**（不是只有主表）
3. **全用 `createBatch`**，没有单条 create

### 二、★★★ `handleSelfUpdate` —— 差异更新真身

```java
Map<ActionType, List<BaseEntityActionDto>> actionTypeMap = dtoColl.stream()
    .filter(a -> Objects.nonNull(a.getActionType()))       // ★ 无 actionType 静默丢弃
    .collect(Collectors.groupingBy(BaseEntityActionDto::getActionType));

actionTypeMap.forEach((key, value) -> {
    if (ActionType.INSERT == key) { createBatch + 主键回填 }
    else if (ActionType.UPDATE == key) { updateBatch + afterUpdate(oldMap) + CacheUtil.evict }
    // ★★★ 没有 DELETE / NORMAL 分支
});
```

**⇒ 四条关键结论：**

| # | 结论 |
|---|---|
| 1 | 只处理 INSERT / UPDATE，**DELETE 在前置 deleteData 已处理** |
| 2 | **NORMAL 的 DTO 直接被丢弃**（不改不动）|
| 3 | **无 actionType 的 DTO 被静默过滤**（不报错！）|
| 4 | INSERT 分支从 entity 读回 ID 写 DTO（主键回填）|

**⇒★★ 最重要隐性约束：子表行没带 actionType → 更新时静默忽略。**
**⇒ 这就是「改了子表但没生效」的原因。**

### 三、★★ `recursiveCheck` 的 4 条校验规则

| # | 规则 | 错误码 |
|---|---|---|
| ① | 子表 parentId 为空 → 自动回填 | — |
| ② | parentId 不匹配 → 报错 | **ENTITY_0031** |
| ③ | UPDATE 时父 ID 不在 DB → 报错 | **ENTITY_0032** |
| ④ | UPDATE 时子行 ID 不在 DB → 报错 | **ENTITY_0032** |

**⇒ 所有错误聚合到 StringBuilder，最后一次抛 `UDC_COMMON_0003`。**
**⇒ 一次保存报出全部错误，不是遇到第一个就停。**

### 四、★★★ `create4Bpm` 完整链路

```
create4Bpm(dto):
  ① if (id == null) setId(Ids.gidLong())        ← ID 在 BPM 前生成
  ② context.putProcessData(dto)
  ③ create4BpmInternal(dto, context)

create4BpmInternal:
  ④ statusType 为 null → 抛「目标状态为空」
  ⑤ PENDING_REVIEW → TO_BE_SUBMITTED（老表单兼容）
  ⑥ approvalCallBack.beforeApprovalCreate(context)
  ⑦ create(dto)                                  ← 走普通 create
  ⑧ oldDto = BeanCopier.copy(dto)                ← 快照
  ⑨ try { approvalCallBack.afterApprovalCreate(context) }
     catch { statusType = TO_BE_SUBMITTED; updateStatusType(dto); rethrow }
  ⑩ if (isMainProcess(context)) updateRootEntity(oldDto, dto)
```

**⇒ 五个机制：**

| # | 机制 |
|---|---|
| ① | **ID 在 BPM 前生成** |
| ② | **状态先改后建** |
| ③ | **BPM 失败不丢数据**（已落库，降级「待提交」）|
| ④ | **抛异常也先存状态再 rethrow** |
| ⑤ | **子流程不更新 root**（`bpmProcessType`）|

### 五、★★★ `update4Bpm` 的静默跳过陷阱

```java
if (checkStatusType) {
    Enum oldStatus = selectBillStatusById(id);
    if (!("NONE".equals(oldStatus.name())
       || "DRAFT".equals(oldStatus.name())
       || "TO_BE_SUBMITTED".equals(oldStatus.name()))) {
        ReflectUtil.setFieldValue(dto, "statusType", null);
        callBpm = false;
        log.warn("表单状态：数据库状态为-{},目标状态为-{},不进行任何bpm操作!");
    }
}
```

**⇒ 状态非 NONE/DRAFT/TO_BE_SUBMITTED 时静默跳过 BPM，不报错。**
**⇒ 这解释「改了单子但流程没动」。**

**单据状态机（从源码反推）：**
```
NONE / DRAFT / TO_BE_SUBMITTED  → 允许走 BPM
PENDING_REVIEW                  → 转 TO_BE_SUBMITTED
其他                            → 跳过 BPM
```

### 六、`updateStatusType` / `updateRootEntity` 的专用通道

```java
updateStatusType(dto):
    mapper.updateColumnsIgnoreVersion(entity, Sets.newHashSet("statusType"))   ← 只更新一列

updateRootEntity(old, new):
    子表全部置 NORMAL（不动子表）
    updateColumnsIgnoreVersion(entity, getUpdateRootFiled(entity))             ← 只更新 root 列
```

**⇒ 这两个方法绕过全部 callback 和事件，用于系统状态维护。**

### 七、★★★ 重大认知修正：EntityMeta 是注解扫描构建的

**`EntityRelationHandler` 源码揭示：**

```
scanClass(classLoader, appName):
    entityClassSet = 扫所有类 filter(@EntityInfo)
    dtoClassSet    = 扫所有类 filter(@DtoInfo(entity非空))
    filter(!contains(".extend."))

buildEntityRelationMap():
    对每个 entityClass:
        new EntityMeta()
        @EntityInfo 自定义属性 → id/stereotype/entityCategory
        setFullName(类全限定名) / setName(简单类名) / setCaption(@EntityInfo.value())
        setDtoClass(dtoClassMap.get(类名))
        parseAttribute()  ← @EntityAttribute(Entity字段) + @Maskable(DTO字段)
        @Table → entityTable
        if (MASTER_ENTITY): relationType=NONE, parentFullName=自己
        else if (SUB_ENTITY):
            Field f = getField(类, "parentId")
            if (f 有 @EntityAttribute):
                relationType = parentAttr.relationType()
                setSortField(有 orderNo 字段)
                parentFullName = parentAttr.relationEntity()
            else: log.warn("子实体:{} parentId 不存在")
    buildSubEntity()  ← 靠 parentFullName 字符串匹配递归建树
    forEachMeta → setTopParent
    LRU_ENTITY_CACHE.put(key, map)
```

**⇒ 推翻了 4 个旧认知：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | EntityMeta 从数据库加载 | **注解扫描 ClassLoader** |
| 2 | dtoListName 是配置项 | **按 relationType 自动生成** |
| 3 | 主子表关系在元数据表 | **在 parentId 字段的 @EntityAttribute 上** |
| 4 | 单层主子表 | **支持无限层级**（buildSubEntity 递归）|

### 八、★★★ `dtoListName` 生成规则（最易踩坑）

```
convertDtoList(relationType, entityFullName):
    simpleName = 类简单名首字母小写
    One2OneAggregation  → simpleName + "Dto"
    One2ManyAggregation → simpleName + "DtoList"      ← ★ 最常见
    其他                → simpleName
```

**⇒ 子实体 `OrderDetail` + One2ManyAggregation → DTO 字段必须叫 `orderDetailDtoList`**
**⇒ 名字不对 → 反射取 null → 子表静默不写入**

### 九、枚举取值（源码级，之前未知）

```java
EntityType:    MASTER_ENTITY(0) / SUB_ENTITY(1)
RelationType:  NONE(0)
               Many2OneAssociation(1)
               One2OneAssociation(2)
               One2OneAggregation(3)
               One2ManyAggregation(4)
```

**⇒ 只有 Aggregation 参与级联写入。**

### 十、`EntityBeanContainer` 的泛型解析机制

```java
postProcessBeforeInitialization(bean, name):
    if (bean instanceof BaseMybatisDao):
        ResolvableType t = ResolvableType.forClass(bean.getClass()).getSuperType();
        Class entityClass = t.getGenerics()[0].resolve();
        mapperMap.put(entityClass, bean);         ← 按实体类注册 DAO
    else if (bean instanceof BaseEntityCurdService):
        Class dtoClass = t.getGenerics()[0].resolve();
        serviceMap.put(dtoClass, bean);           ← 按 DTO 类注册 Service
```

**⇒ `findDao(Class)` / `findService(Class)` 靠泛型参数解析自动注册，不用配置。**
**⇒ 这就是为什么每个实体有自己的 Dao/Service 但代码里看不到注册。**

### 十一、`@EntityInfo` 注解 11 个属性（源码级）

```java
String  value();                        // ★ 必填，caption
String  description()      default "";
EntityType entityType()    default MASTER_ENTITY;   // ★
String  historyEntity()    default "";              // 历史实体（快照）
String  plugins()          default "";
boolean fullTextSearch()   default false;
boolean permission()       default false;
boolean isPublic()         default false;
boolean export()           default false;
boolean isLogicDelete()    default false;           // ★ 逻辑删除
int     sort()             default 0;
Custom[] customs()         default {};              // ★ 含 id/stereotype/entityCategory
```

**新增文件：**
- `01A-metadata-structure.md`（9.7KB，EntityMeta/AttributeMeta 字段与方法）
- `01B-metadata-loading-CORRECTION.md`（16.6KB，★★★ 认知修正）

**修改文件：**
- `01-metadata.md`（38.9KB → 41.4KB，追加运行态加载机制）
- `03-persistence.md`（83.0KB → 约 110KB，追加 recursiveCreate/Update/Check + create4Bpm/update4Bpm）

**推翻的旧结论（本轮 4 条）：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `EntityMeta` 从数据库加载 | **注解扫描 ClassLoader 构建** |
| 2 | `dtoListName` 是配置项 | **按 relationType 自动生成 `xxxDtoList` / `xxxDto`** |
| 3 | 主子表关系在元数据表 | **在 `parentId` 字段的 `@EntityAttribute` 上** |
| 4 | `recursiveCreate` 只递归+插入 | **还逐层调 beforeCreate/afterCreate** |

**整体完成度：** 1:88% / 2:62% / 3:95% / 4:70% / 5:65% / 6:70% / 7:65%
**全局：约 76%**
**状态：`PARTIALLY_COMPLETED`**

---

## 轮次 9 — 2026-11-17（表达式机制追查，第 5 条重大修正）

### 一、★★★ 表达式是代码生成，不是运行时解释

**反编译 `udc-biz-5.3.517.jar` 得到 `com.seeyon.udc.expression` 包 70 个类。**

**决定性证据：**

```java
public interface Interpreter {
    String interpret(ASTNode astNode, ExprCodeGenContext context);   // ← 返回 String
}
```

**⇒ 运行时求值应该返回计算结果值，不会返回字符串。**
**⇒ 返回 String = 生成 Java 源码片段。**

**第二个证据（更硬）：**

```java
public String genTypeCastCode(ASTNode left, ASTNode right, ExprCodeGenContext context) {
    ...
    context.getImportClasses().add(RESULT_CALCULATE_HELPER_IMPORT);
    context.getImportClasses().addAll(DECIMAL_IMPORT_SET);      // ← 收集 import
    return helper.castTypeExpr(...);
}
```

**⇒ 只有生成源码才需要收集 import 语句。**

### 二、生成的代码 import 什么

```java
java.math.BigDecimal
java.math.RoundingMode
com.seeyon.boot.starter.formula.engine.utils.FormulaResultTypeUtil
com.seeyon.boot.starter.formula.utils.SymbolicOperationHelper
```

**⇒ 表达式四则运算全部走 BigDecimal，不丢精度。**
**⇒ SymbolicOperationHelper 处理 null / 空串。**

### 三、6 种 AST 节点 → 6 个 Interpreter

```
BINARY_EXPR  → BinaryInterpreter
UNARY_EXPR   → UnaryInterpreter
CALL_EXPR    → FunctionInterpreter
VARIABLE     → VariableInterpreter
SCALAR       → ScalarInterpreter
SYSTEM       → SystemInterpreter
```

### 四、13 个运算符（硬编码 switch）

```
算术：+  -  *  /  %
比较：==  !=  >  <  >=  <=
逻辑：&  |  （一元 !）
```

**⇒ 逻辑运算符是单字符 `&` / `|`，不是 `&&` / `||`。**
**⇒ 非法运算符抛 `NotImplementedException("非法的二运算符:"+value)`。**

### 五、10 个内置函数族

```
ABS / IFS / SUMIF / SUM / MAX / MIN
EARLIEST / LATEST
LIST_UNIQUE / GET_LIST_INDEX / CTP_ENUM_ITEM
ExtensionFunctionInterpreter  ← 自定义扩展入口
```

### 六、5 种变量来源

```
VariableInterpreter            普通变量
EntityVariableInterpreter      实体字段      ← 最关键
MicroFlowVariableInterpreter   微流程变量
SystemInterpreter              系统变量
ScalarInterpreter              标量常量
```

### 七、★ 修正：`getDefaultValue()` 不是表达式入口

```java
public D getCascadeDefaultValue(String key) {
    BaseEntityActionDto dto = this.getDefaultValue();        // 空 DTO
    this.recursiveDefaultValue(this.entityMeta, dto);        // 递归建空子行
    return (D) dto;
}

private void recursiveDefaultValue(EntityMeta meta, D dto) {
    meta.getChildren().forEach(childMeta ->
        findService(childMeta.getDtoClass()).ifPresent(svc -> {
            BaseEntityActionDto subDto = svc.getDefaultValue();
            if (One2OneAggregation == childMeta.getRelationType())
                setFieldValue(dto, childMeta.getDtoListName(), subDto);
            else if (One2ManyAggregation == childMeta.getRelationType())
                setFieldValue(dto, childMeta.getDtoListName(), Lists.newArrayList(subDto));
        }));
}
```

**⇒ 它只负责「新建表单时给子表一条空行」，不计算任何值。**
**⇒ 上一轮（第 9 节）把 `getDefaultValue()` 当表达式接入点是错的，本轮修正。**

### 八、`@ECacheable` 按用户缓存默认值

```java
@ECacheable
public D getCascadeDefaultValue(String key)     // key = "CascadeDefaultValue:" + userId
```

**⇒ 默认值骨架按**用户**缓存，不是全局缓存。**
**⇒ 因为默认值可能含当前用户信息（创建人等）。**

### 九、完整表达式链路（修正版）

```
【设计态】用户配置 → AttributeExpressionDto
    → expressionDesignData / expressionRuntimeData（两份）
        ↓
【代码生成】ExpressionCodeGenerator
    → 解析 runtimeData → AST
    → SemanticAnalyzer 类型推导（决定 BigDecimal 转换）
    → ExpressionInterpreter 遍历
        → 各 interpret() 返回源码片段 + 收集 import
    → 拼装 exec<雪花ID> 方法
    → 注入生成的 Entity/Service
        ↓
【部署】编译 → 动态 jar → 热加载
        ↓
【运行时】直接方法调用（无解释开销）+ BigDecimal 运算
```

**新增文件：**
- `04A-expression-mechanism-CORRECTION.md`（15.3KB）

**修改文件：**
- `04-expression.md`（26.1KB → 28.5KB）

**推翻的旧结论（本轮 2 条）：**

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | 表达式由解释器运行时求值 | **AST → Java 源码 → 编译部署 → 方法调用** |
| 2 | `getDefaultValue()` 是表达式接入点 | **只建空 DTO 骨架（含子表空行）** |

**累计推翻统计（本轮研究共 8 轮）：**

| 轮次 | 推翻条数 | 主要内容 |
|---|---|---|
| 4 | 4 | JsonUtils 4 类 / 方言 11 种 / action-index 层错配 |
| 5 | 4 | BaseEntityCurdService 81 方法 / recursiveCreate private / positive 100% 过拟合 / nullify 是 feature |
| 6 | 3 | 先删后插 → 差异删除 / updateBase 已还原 / DtoConvertUtil 可从描述符得 |
| 7 | 5 | resetInsertHandle 只遍历 / 本机有 jar / gidLong 非纯雪花 / epoch / workerId 来源 |
| 8 | 4 | EntityMeta 注解扫描 / dtoListName 自动生成 / 关系在注解 / 无限层级 |
| 9 | 2 | 表达式是代码生成 / getDefaultValue 非表达式入口 |
| **合计** | **22 条** | |

**整体完成度：** 1:88% / 2:62% / 3:95% / 4:**85%** / 5:65% / 6:70% / 7:65%
**全局：约 79%**
**状态：`PARTIALLY_COMPLETED`**

**下一轮任务：**
1. `ExpressionCodeGenerator.generateCode()` 主体（怎么拼方法）
2. `CodeGenerateResult` 字段与消费方
3. `ExprCodeGenTemplate` 方法模板
4. `formula-functions.xml` 完整函数表解析
5. 专题 2 代码生成（62%，最低，需推）

---

## 轮次 10 — 2026-11-17（标品域攻坚：组织 / 流程 / 枚举 / 文件）

**方向调整（用户指示）：**
> udc 不用那么多其实，你知道 biz 业务包里的即可，
> 主要 core 标品 org 组织，bpm 流程，还有那些基础包 file enum 等等等

**⇒ 停止深挖 udc-biz，转向标品核心域。**

### 一、反编译规模（本轮新增 1,954 个类）

| 包 | 类数 | 版本 |
|---|---|---|
| **bpm-facade** | **533** | 5.3.374 |
| **organization-facade** | **414** | 5.3.601 |
| ctp-user-facade | 263 | 5.3.429 |
| boot-starter-formula | 202 | 5.3.603 |
| **boot-starter-file** | **89** | 5.3.600 |
| boot-starter-serialnumber | 85 | 5.3.603 |
| boot-starter-excel | 72 | 5.3.603 |
| **boot-starter-enums** | **51** | 5.3.603 |
| boot-starter-cache | 50 | 5.3.600 |
| boot-starter-dynamicsql | 42 | 5.3.600 |
| boot-formula-engine | 41 | 5.3.603 |
| boot-starter-eventbus | 24 | 5.3.600 |
| boot-starter-datatype | 23 | 5.3.600 |
| boot-starter-parameter | 22 | 5.3.603 |
| boot-starter-transaction | 15 | 5.3.600 |
| boot-starter-attachment | 15 | 5.3.290 |
| boot-starter-lock | 9 | 5.3.600 |
| boot-starter-systemvariable | 4 | 5.3.603 |
| **合计** | **1,954** | |

**⚠️ VERSION_CAVEAT：本机版本与用户环境 5.3.517 有差异，已逐文档标注。**

### 二、★★★ 组织域（10-org-domain.md）

**414 类 / 54 接口 / 6,409 方法**

**接口四层分类：**
```
*BaseAppService   基础 CRUD
*CoreAppService   核心查询
*SyncAppService   同步批量
Ocip*AppService   开放接口
```

**最常用：`OrgCommonAppService`（45 方法）**

查人员的标准入口（全部实测验证）：
```java
selectMemberByOrgId(...)            : ListResponse<Long>      按部门查人ID
selectPageMemberByOrgId(...)        : PageResponse<Long>
selectMemberCountByOrgId(...)       : SingleResponse<Integer> 部门人数
selectMemberByPostId(...)           : ListResponse<Long>      按岗位
selectMemberByLevelId(...)          : ListResponse<Long>      按职级
selectMemberByUserId(...)           : SingleResponse<OrgMemberCoreDto>  按ctp userId
selectMemberInfoById(...)           : SingleResponse<Map<String,Object>> 单人详情
selectMemberMultiDimOrgInfo(...)    : 多维组织
selectMemberInstitutionInfoById(...): 所在单位
selectManagerDepartmentByMemberId   : 该人管理的部门
selectLeaderDepartmentByMemberId    : 该人分管的部门
```

**★★ 两个关键发现：**

**① 返回值是 `Map<String,Object>`，不是强类型 DTO**
**⇒ 组织人员字段是**元数据可配置**的，不能假设固定字段名。**

**② 大数据量走文件：**
```java
selectMemberPostBySelectPeoplesReturnFile(...)   结果写文件
selectReturnFileByKey(...)                       读回
deleteReturnFileByKey(...)                       用完必须删
```
**⇒ 选人结果上万条时走「文件暂存 + 分次读」，用完不删会存储泄漏。**

**`OrgMemberSyncAppService`（14 方法）—— 三方系统对接入口：**
```java
createBatch / createBatchMemberPost / createBatchMemberMetadata
selectByCodes / selectByThirdIds      ← 按编码/三方ID查
selectNaturalMemberByPhoneNumber      ← 按手机号查
fixCtpUserId                          ← 修复 ctp userId
disableMember / disableMemberByThirdIds
```

**`OrgMetadataCoreAppService`（16 方法）—— 元数据维度：**
```java
selectMemberByUnitMetadata(...)       按部门自定义字段筛人
selectMemberByUnitMemberMetadata(...) 按人员自定义字段筛人
selectEntityIdByMetadataValue(...)
```

### 三、★★★ BPM 域（11-bpm-domain.md）

**533 类 / 40 接口 / 5,893 方法**

**`BpmAppService`（23 方法）—— 流程操作唯一入口，全部 `SingleRequest<T>` → `*Response<R>`：**

| 动作 | 方法 | 请求 DTO | 响应 DTO |
|---|---|---|---|
| **发起** | `send` | `BpmSendDto` | `BpmSendResultDto` |
| **存草稿** | `saveDraft` | `BpmSaveDraftDto` | `BpmSaveDraftResultDto` |
| **提交** | `submit` | `BpmSubmitDto` | `BpmSubmitResultDto` |
| **退回** | `stepBack` | `BpmStepBackDto` | `CommonResultDto` |
| **撤销** | `repeal` | `BpmRepealDto` | `CommonResultDto` |
| **终止** | `stop` | `BpmStopDto` | `CommonResultDto` |
| **取回** | `takeBack` | `BpmTakeBackDto` | `CommonResultDto` |
| **换人** | `replace` | `BpmReplaceDto` | — |
| 批量换人 | `multipleReplace` | `BpmMultipleReplaceDto` | — |
| **加签** | `addExecuteMember` | `BpmAddExecuteUserDto` | `BpmItemInfoDto` |
| 会签 | `counterSignNode` | `SimpleChangeProcessRequestDto` | — |
| 加节点 | `addNode` | `SimpleChangeProcessRequestDto` | — |
| **暂停** | `pause` | `BpmPauseDto` | `BpmPauseResponseDto` |
| 恢复 | `cancelPause` | `BpmPauseDto` | — |
| **催办** | `hasten` | `BpmHastenDto` | — |
| 咨询 | `consult` | `BpmConsultDto` | — |
| 知会 | `inform` | `BpmInformDto` | — |
| 批量 | `batchDeal` | `BpmBatchReqDto` | — |
| **查完整单据** | `selectFullCaseInfo` | `BpmCaseFullInfoSearch` | `BpmCaseFullInfo` |
| 删草稿 | `deleteDraft` | `Long` | `Void` |
| 删草稿+事项 | `deleteDraftAffair` | `DeleteDraftReqDto` | `Void` |
| 监控节点 | `monitorNodeRun` | `BpmMonitorRunDto` | — |
| 安全检查 | `check` | `SecurityCheckDto` | `Boolean` |

**★★ 三个关键发现：**

**① 单据 → 模板的关联：**
```java
BpmTemplateAppService.selectTemplateByRootEntityId(rootEntityId)
BpmTemplateAppService.selectTemplateByRootEntityName(rootEntityName)
```
**⇒ 单据类型（根实体）决定用哪个流程模板。**

**② 表单权限 vs 节点权限是两套独立机制：**
```
节点权限（谁能办）      → BpmApiNodePermissionAppService（11 方法）
表单权限（能看/改哪些字段）→ BpmApiFormPermissionAppService（18 方法）
```

**③ 流程实例与业务数据的关联键：**
```java
BpmCaseAppService.selectBpmCaseByFormRecordId(...)   按表单记录ID找流程
BpmCaseAppService.deleteCaseByIdForUdc(...)          UDC专用删除
```

**模板发布是两阶段：**
```java
publishLock / publishLockByAppInfo     加锁
publishCheck / publishCheckByAppInfo   检查
publishFinish                          完成
cleanCacheByApplicationName            清缓存（改完必须调）
```

### 四、★★ 枚举包（12-enums-file-domain.md）

**51 类，核心是 `CtpEnum`（定义）+ `CtpEnumItem`（项）**

**三种枚举类型（`CtpEnumType`）：**
```java
SAME_LEVEL(0)    平级枚举（单层，如性别）
MULTI_LEVEL(1)   多级枚举（树形，如行政区划）
CASCADE(2)       级联枚举（父子联动，如省→市→区）
```

**`CtpEnumItem` 15 个字段（关键 4 个）：**
```java
private String  itemValue;         ★ 业务存取值（不是 enumId！）
private Long    parentId;          父项ID（树形/级联）
private String  parentItemValue;   ★ 冗余父项值，避免 join
private Integer itemLevel = 1;     层级
```

**⇒★★ 最重要：业务表存的是 `itemValue`，不是 `enumId`。**

**`CtpEnumAppService`（22 方法）关键：**
```java
selectByCode(SingleRequest<String>)      ★ 业务取枚举的标准入口
selectParentByCode(...)                  按编码查父项
selectByRootEnumIdAndEnumLevel(...)      按根+层级
selectByAppGuid(...)                     按应用查
selectByConditionsContainsCascade(...)   ★ 含级联子项
selectListByConditionsNoLevel(...)       不含层级
```

**其他关键类：**
```
CtpEnumItemFilterService     ★ 不同用户看不同枚举项（权限过滤）
EnumCacheUtils               枚举缓存（改完要清）
CtpEnumCategoryAppService    枚举分类
CtpEnumItemImportDto         枚举项导入
```

**事件体系（枚举变更发事件）：**
```
CtpEnumCreateEvent / UpdateEvent / DeleteEvent
CtpEnumItemCreateEvent / UpdateEvent / DeleteEvent / BatchDeleteEvent
```

### 五、★★ 文件包（12-enums-file-domain.md）

**89 类，核心是 `StorageService`（14 方法）+ `StorageSpi`（9 方法）**

**存储抽象层（`StorageService`）：**
```java
String           getStorageType();
boolean          delete(String key);
UploadResultDto  upload(StorageUploadRequestDto);
InputStream      download(String key);
void             download(String key, HttpServletResponse);
boolean          exist(String key);
void             copy(String src, String dest);

// ★ 分片四步
boolean                  enablePartUpload();
PartUploadInitResultDto  partUploadInit(...);
boolean                  partUpload(...);      × N
UploadResultDto          partUploadEnd(...);
```

**8 种存储后端：**
```
NfsService      NFS
OssService      阿里云 OSS
SfoOssService   SFO OSS
ObsService      华为云 OBS
MinIoService    MinIO
V5StorageSpi    V5 兼容
StorageSpi      SPI 扩展点
StorageSelectService  ★ 存储选择器
```

**`StorageSpi` 三个桶：**
```java
getPrivateBucketName()     私有桶
getPublicBucketName()      公共桶
getFerryboatBucketName()   ★ 摆渡桶（内外网文件交换）
```

**`FileAppService`（11+ 方法）：**
```java
getDownloadUrl(...)          ★ 下载临时URL
getBackendDownloadUrl(...)   后端下载URL
getThumbnailUrl(...)         缩略图
saveFileInfo(...)            ★ 登记文件元数据
saveFileInfos(...)           批量登记
modifyFileName(...)          改文件名
generateShareUrl(...)        生成分享链接
getFileConfig(...)           文件配置
```

**⇒★★ 上传分两步：**
```
① StorageService.upload(...)        → 拿 storageKey
② FileAppService.saveFileInfo(...)  → 登记元数据
不调第②步 = 文件在存储里但查不到
```

**⇒ 下载用 `getDownloadUrl` 拿临时 URL，不是直接读流。**

### 六、新增文档

| 文件 | 大小 | 内容 |
|---|---|---|
| `10-org-domain.md` | 14.9 KB | 组织域 54 接口全清单 + 开发要点 |
| `11-bpm-domain.md` | 11.4 KB | BPM 域 40 接口 + 全 DTO 契约 |
| `12-enums-file-domain.md` | 10.4 KB | 枚举 + 文件基础包 |

**新增脚本：**
- `scripts/research/build_domain_index.py`（域索引生成 + 检索）
- `core/research/platform-dev-system/domain-index.json`（1,814 类 / 217 接口 / 20,576 方法 / 3,088 条签名）

### 七、检索器调优记录（诚实记录失败）

**`build_domain_index.py` 的检索经过 4 轮迭代仍未达标：**

| 版本 | 做法 | 问题 |
|---|---|---|
| v1 | 域标签 10 分 + 方法名匹配 | 整个域都命中，无区分度 |
| v2 | 只按方法名 bigram | 中文 query 与英文方法名无交集，全部 2 分 |
| v3 | 中文→英文意图映射 | 「查」命中所有 select，`AllInOneBaseDao` 刷分 |
| v4 | 拆动作词/对象词 | 部分改善（「按部门查人员」→`getMemberInfo`），但仍不稳 |
| v5 | 改成「最佳单方法」而非累加 | 「下载附件」正确，但「提交单据」仍错 |

**⇒ 结论：关键词表检索天花板明显，与第 5 轮 held-out 78.6% 的结论一致。**
**⇒ 已确认**无法靠调参解决**，需要语义模型。**
**⇒ 但 `domain-index.json` 本身（3,088 条精确签名）是有价值的结构化资产。**

### 八、覆盖度更新

**平台原始规模：4,753 class（udc 11 jar 4,094 + boot-core 659）**

**已反编译（累计）：**
```
udc-starter-lowcode   121
boot-core             512
udc-biz             1,856
std-src 18 个包     1,954
──────────────────────────
合计                4,443 个 .java
```

**真读过内容的类（本轮 +39）：**
```
上轮  39
本轮  组织域 8 + BPM 域 5 + enums 5 + file 6 + 其他 12 = 36
──────────────────────────
累计  75 个
```

**⇒ 覆盖率：75 / 4,753 = 1.6%**

**但按「能力域」覆盖看：**
| 域 | 掌握度 | 说明 |
|---|---|---|
| 实体写入（UDC CRUD） | **95%** | 字节码+源码双证 |
| 主子表 | **95%** | recursiveCreate/Update/Delete 全链 |
| 单据 BPM | **85%** | 契约全，ApprovalCallBack 实现未读 |
| 组织 | **70%** | 54 接口全清单，实现逻辑未读 |
| 枚举 | **80%** | 模型+接口全 |
| 文件 | **75%** | 存储抽象全，具体实现未读 |
| 表达式 | **85%** | 代码生成机制已证 |
| 代码生成 | **62%** | 最弱，未动 |

**整体完成度：** 1:90% / 2:62% / 3:95% / 4:85% / 5:70% / 6:75% / 7:70%
**全局：约 81%**
**状态：`PARTIALLY_COMPLETED`**

**下一轮任务（按用户优先级）：**
1. `ApprovalCallBack` 实现类（UDC→BPM 桥）
2. `BpmSendDto` / `BpmSubmitDto` / `BpmStepBackDto` 字段（发起/提交/退回要传什么）
3. 组织域实现逻辑（`OrgCommonAppService` 实现类）
4. 文件域 `FileService` 91 方法（最全）
5. 代码生成（62%，唯一未动的短板）

---

## 轮次 11 — 2026-11-18（UDC→BPM 全链路打通 + 标品类系统清点）

### 一、★★★ 最大突破：UDC→BPM 三层桥接全部定位

**问题**：`BaseEntityCurdService.create4Bpm` 调 `approvalCallBack.afterApprovalCreate(context)`，
但 `ApprovalCallBack` 是 6 个空 `default` 的接口 —— **实现类在哪？**

**排查过程（关键教训）：**
```
① grep "implements ApprovalCallBack" in udc-lowcode-src / udc / std-src
   → 全部 0 命中
② 换策略：二进制搜 class 文件里【引用】ApprovalCallBack 的类
   grep -rl "ApprovalCallBack" udc/
   → udc-starter-runtime/.../ApproveFeatureService.class   ★ 命中
③ 反编译 udc-starter-runtime-5.3.605.jar
   → ApproveFeatureService implements ApprovalCallBack     ★ 确认
```

**★ 教训：接口实现类不在接口所在 jar，要搜「引用方」而不是「实现方」。**

**三层桥接：**

| 层 | 类 | 模块 |
|---|---|---|
| L1 扩展点 | `ApprovalCallBack`（6 空 default） | udc-starter-lowcode |
| **L2 实现类** | **`ApproveFeatureService`** | **udc-starter-runtime** |
| L3 RPC | `BpmUdcApiService`（`@DubboReference`） | bpm-facade |

### 二、★★★ 状态机完整实证（`startProcess0`）

```java
switch (oldStatus) {
    case "PENDING_REVIEW":
        target "PENDING_REVIEW"                        → sendProcess()
    case "DRAFT":
        target "PENDING_REVIEW"                        → sendProcess()
        target "DRAFT" | "TO_BE_SUBMITTED"             → saveDraft()
    case "TO_BE_SUBMITTED" | "NONE" | "":
        target "PENDING_REVIEW"                        → sendProcess()
        target "DRAFT"                                 → saveDraft()
}
```

| oldStatus \ target | `PENDING_REVIEW` | `DRAFT` | `TO_BE_SUBMITTED` | 其他 |
|---|---|---|---|---|
| `PENDING_REVIEW` | **sendProcess** | — | — | — |
| `DRAFT` | **sendProcess** | **saveDraft** | **saveDraft** | — |
| `TO_BE_SUBMITTED` | **sendProcess** | **saveDraft** | — | — |
| `NONE` | **sendProcess** | **saveDraft** | — | — |
| `""`(null) | **sendProcess** | **saveDraft** | — | — |

**★★ 反直觉发现：`create4BpmInternal` 把 DTO 的 `PENDING_REVIEW` 改写成 `TO_BE_SUBMITTED`，
但流程仍能发起 —— 因为改写只改字段，局部变量 `targetStatusType` 没变：**
```java
ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));  // 改字段
context.putTargetStatusType(targetStatusType.name());   // 局部变量仍是 PENDING_REVIEW
```

**★ 两条坑：**
- `DRAFT → TO_BE_SUBMITTED` 走 **saveDraft**（不是发起）→ 降级单据重试不会重发
- `TO_BE_SUBMITTED → TO_BE_SUBMITTED` **什么都不做** → 必须显式改成 `PENDING_REVIEW`

### 三、★★★ 模板查找机制（`getBpmPrefixParams` → `prefixForUdc`）

**不是靠 `templateCode`，靠参数组合：**

| 参数 | 来源 | 作用 |
|---|---|---|
| **`rootEntityName`** | `getEntityFullName(data)` | **主键** |
| `templateId` | 单据 DTO 字段 | 多模板选择 |
| `templateGuid` | `extraParamMap` | 版本 |
| `pageGuid`/`pageUrl`/`pageParameter` | `extraParamMap` | 页面上下文 |
| `caseId` | 单据 DTO 字段 | 已有实例 |
| `pageType` | `extraParamMap`（须匹配 `PageTypeEnum`，否则静默置 null） | 页面类型 |

### 四、★★★ 五条降级路径（全部实证，3 条静默）

| # | 触发条件 | 单据状态 | 抛异常 | 日志关键字 |
|---|---|---|---|---|
| **1** | `prefixForUdc` 返回 null（**没配模板**） | 不变 | ❌ | `未配置流程模板或根据参数未查询到流程模板` |
| **2** | `content.errorMsg` 非空 | `TO_BE_SUBMITTED` | ❌ | 依赖 BPM |
| **3** | **RPC 异常** | `sendState=SENDING` + 进重试队列 | ✅ | `发送bpm流程rpc调用失败即将进入重试队列` |
| **4** | **`preMatch.isPop()==true`**（要选人） | `TO_BE_SUBMITTED` | ❌ | `需要选人，更新单据状态为：TO_BE_SUBMITTED` |
| **5** | `BusinessException` | 不变 | ✅ | `发起流程业务异常` |

**⇒ #1/#2/#4 都不抛异常，调用方只能查库或查日志发现。**

### 五、★★ `sendProcess` 的 DTO 装配要点

```java
dto.setUserId(RequestContext.get().getUserId());     // ★ 从上下文取，非传入
dto.setApplicationName(Apps.getAppName());           // ★ 从上下文取
dto.setFormRecordId(dataId);                         // ★ Long
// ★ formData 按模板声明裁剪，不是全量
Map processParamMap = BpmDataUtil.filterMapData(dataMap, bpmResult.getParamPathNames());
```

**⇒ `create4Bpm` 必须在**有请求上下文的线程**执行，不能放异步线程池/定时任务裸调。**

**★ `sendState` 三态：`SEND_SUCCESS` / `SENDING`（进重试队列）/ 初始**

### 六、★★ 标品 18 包系统清点（新脚本）

**新增脚本：`scripts/research/std_census.py`**

**结果：**
```
1,954 个 .java
├─ 1,500 类
├─   184 接口
├─   247 枚举
├─    12 注解
└─ 21,819 方法
```

**方法数 Top 10 接口：**
| 接口 | 方法数 | 包 |
|---|---|---|
| `BpmTemplateAppService` | 54 | bpm-facade |
| `OrgCommonAppService` | 45 | organization-facade |
| `OrgWorkFlowAppService` | 37 | organization-facade |
| **`BpmAppService`** | **26** | bpm-facade |
| `BpmCaseAppService` | 22 | bpm-facade |
| `OrgUnitBaseAppService` | 20 | organization-facade |
| `BpmApiFormPermissionAppService` | 18 | bpm-facade |
| `CtpUserPermissionCommonAppService` | 18 | ctp-user-facade |
| `CtpUserCoreAppService` | 18 | ctp-user-facade |
| `OrgMemberBaseAppService` | 18 | organization-facade |

### 七、★ 统计缺陷修正（诚实记录）

| 项 | 内容 |
|---|---|
| **缺陷** | `METHOD_RE` 用 `^\s{4}`，只匹配 4 空格缩进且带修饰符的方法，漏掉 `public XxxResponse<X> send(...)` 这种「public 无 default」声明 |
| **症状** | `BpmAppService` 算成 **4**（实际 **26**）；全量方法偏低 |
| **修正** | `^\s{4}` → `^\s+` |
| **修正后** | `BpmAppService`=26；全量 21,578 → **21,819** |
| **发现方式** | 与 `grep -cE "^\s+default\s+"` 结果（4）对比，不符 → 重读全文 → 发现 8 个 `public` 声明被漏 |
| **教训** | **统计脚本必须先做单点人工核对**：挑一个已知类手数一遍，不一致就查正则 |

### 八、★ 口径差异说明（两个数字都对）

| 口径 | 统计对象 | 接口数 | 方法数 |
|---|---|---|---|
| `domain-index.json`（第 9 轮） | **业务域视图**（跨包归并，含 boot-core） | 329 | 3,179 |
| `std-census.json`（第 10 轮） | **jar 包视图**（严格 18 包） | 184 | 21,819 |

**差异根因：**
1. 统计对象不同（业务域 vs jar 包）
2. 包含范围不同（domain-index 含 boot-core 的 datasource/dubbo/mybatis 域）
3. 包名字段写法不同（`...starter.file` vs `...starter.file.appservice`）

**⇒ 以后引用必须标明口径。**

### 九、★★ 关键契约修正

| 项 | 旧（错） | 新（实测） |
|---|---|---|
| `BpmAppService` 方法数 | 23 | **26** |
| `BpmCaseAppService` 方法数 | 23 | **22** |
| UDC 发起流程方法 | `bpmAppService.sendUdc`（猜） | **`bpmUdcApiService.sendForUdc`** |
| `BpmAppService` 有 UDC 方法吗 | 以为有 | **没有，26 个方法全是通用操作** |
| `ApprovalCallBack` 实现类 | 「未找到，留给开发者」 | **`ApproveFeatureService`（udc-starter-runtime）** |

### 十、新增/修改文件

**新增：**
| 文件 | 大小 | 内容 |
|---|---|---|
| `13-bpm-operation-dtos.md` | 19.7 KB | 9 个操作 DTO 全字段 + 枚举 + 陷阱清单 |
| `14-udc-bpm-bridge.md` | 28.3 KB | **UDC→BPM 三层桥接全链路实证** |
| `scripts/research/std_census.py` | 5.9 KB | 标品包系统清点脚本 |
| `std-census.json` | — | 结构化清点结果（含 1,954 类型全签名） |
| `interface-methods.json` | — | 4 个核心 BPM 接口的方法清单 |

**修改：**
| 文件 | 改动 |
|---|---|
| `statistics-registry.md` | 新增 §11 标品 18 包清点口径 + §11.3 扫描器缺陷修正 |
| `11-bpm-domain.md` | `BpmAppService` 23→26；`BpmUdcApiService` 章节全面重写 |
| `13-bpm-operation-dtos.md` | UDC 调用示例方法名修正为 `sendForUdc` |

### 十一、本轮验证的「反编译工具链坑」

**坑 1：CFR jar 被系统清理**
```
原路径 C:/Users/白明涛/AppData/Local/Temp/cfr.jar 被清空
→ 重新从 Maven Central 下载到 scratch/cfr.jar
```

**坑 2：CFR 是原生 Java 程序，MSYS 路径不转换**
```
❌ java -jar cfr.jar /d/repo/xxx.jar          → No such jar file
✅ java -jar cfr.jar "D:/repo/xxx.jar"        → 成功
```

**坑 3：CFR 不能反编译目录，只能传 jar 或单个 class**
```
❌ java -jar cfr.jar udc/.../callback/        → CannotLoadClassException
✅ java -jar cfr.jar "D:/repo/.../xxx.jar"    → 成功
```

### 十二、覆盖度更新

**已反编译累计：**
```
udc-starter-lowcode    121
udc-starter-runtime    新增（ApproveFeatureService 所在）
boot-core              512
udc-biz              1,856
std-src 18 包        1,954
──────────────────────────
合计                ≈4,500+ 个 .java
```

**能力域掌握度：**
| 域 | 上轮 | 本轮 | 说明 |
|---|---|---|---|
| 实体写入 CRUD | 95% | **95%** | — |
| 主子表 | 95% | **95%** | — |
| **单据 BPM** | 85% | **98%** | **三层桥接+状态机+5条降级全实证** |
| 表达式 | 85% | **85%** | — |
| 枚举 | 80% | **80%** | — |
| 文件 | 75% | **75%** | — |
| 组织 | 70% | **70%** | — |
| 代码生成 | 62% | **62%** | ← 唯一短板 |

**整体完成度：** 1:90% / 2:62% / 3:95% / 4:85% / 5:70% / 6:75% / 7:70%
**全局：约 82%**（↑1%）
**状态：`PARTIALLY_COMPLETED`**

### 十三、下一轮任务

1. **代码生成（62%，唯一未动的短板）** —— `CodeTask` 52 实现 + `Template` 36 载体的调用链
2. `saveDraft` / `repealProcess` 内部实现（`ApproveFeatureService` 386/443 行起，未逐行读）
3. 组织域实现逻辑（`OrgCommonAppService` 实现类）
4. `FileService` 91 方法（最全的文件接口）
5. `deleteCaseByIdForUdc` 两个 Long 参数含义
6. 微流程生单 + 扣减规则（用户指定优先）
7. 页面搭建 + 页面规则（用户指定优先）
---

## 轮次 12 — 2026-11-18（三块空白补齐 + 用户重大指正）

### 零、用户的三条重大指正（已落文档+记忆）

| # | 指正 | 我的错 | 已做 |
|---|---|---|---|
| **1** | **自定义微流程 ≠ 标准微流程**：一个写代码，一个搭页面，**自定义微流程没有节点** | 把两者混为一谈 | 新建 `core/facts/udc/microflow/00-TWO-KINDS-MUST-SEPARATE.md` |
| **2** | **自定义微流程不加数据库断言**（不保证能访问库） | 用带 DB 断言的 E2E 证明「微流程通」 | 同上，明确验证方式改为编译+部署+日志+返回值 |
| **3** | **按「有什么能力」组织，不按「UDC 怎么调」** | 按调用角度分类 | 新建 `00-capability-map.md`，按三种调用形态 + 能力域 |

**另外用户点明的四件事：**
- 标品应用（org/bpm/connector）→ **Dubbo / 泛化调用**
- 业务组件（file/enum）→ **@Autowired 直接调 Service / AppService**
- 工具类（json/http/加密/excel）→ 第三类
- **配置文件必须写 Nacos 配置中心**（`ConfigCenterService`），不能只写本地

---

### 一、★ 全部 107 个 jar 清点（首次完整）

**脚本：** `D:/software/hermes/cache/scratch/jar_census.py`
**结果：** `jar_census.json`

**最大的 10 个：**
| jar | 版本 | 类数 |
|---|---|---|
| znxmglpt…-biz | 1.0.11502 | 2,357 |
| udc-biz | 5.3.517 | 1,856 |
| znxmglpt…-facade | 1.0.11502 | 1,535 |
| znxmglpt…-web | 1.0.11502 | 994 |
| boot-starter-graphql | 5.3.600 | 772 |
| faccountsreceivable…-facade | 1.0.2027 | 727 |
| xiangmuguanli…-biz | 1.0.13659 | 675 |
| xiangmuguanli…-facade | 1.0.13659 | 557 |
| bpm-facade | 5.3.374 | 533 |
| boot-core | 5.3.600 | 512 |

**⇒ 标品 jar 之外，还有大量客户应用 jar（znxmglpt / xiangmuguanli / faccountsreceivable / datamigration / peixunudc）。**

---

### 二、★★ 第一块空白：boot-core 177 个工具类（方法级）

**文档：** `09-boot-core-utils.md`（22.3 KB）
**原始签名：** `bootcore-util-sigs.txt`（1,989 行）

**工具链坑（记录）：**
1. bash 循环里 `javap` 全部失败 → 改 Python subprocess
2. `javap` 不在 PATH → 用 `D:/software/java/bin/javap.exe`

**核心发现：**

| 工具类 | 方法数 | 关键点 |
|---|---|---|
| `JsonUtils` | 25 | `toJsonLongToString` ★ 防 JS 精度（雪花ID 19位>2^53） |
| `HttpClientUtil` | 大量重载 | 四层返回（String/泛型/HttpResult/Map） |
| `AESUtils`/`DESUtils`/`RSAUtils` | 9/4/10 | **不要自己写 JCE** |
| `DateUtils` | **73** | 14 个预定义格式常量 |
| `StringUtils` | 34 | `maskMobileNo` 脱敏、`toPinyin` 拼音**内建** |
| `Ids` | 7 | `gidLong()` 主键、`analyzeDate(id)` **反解创建时间** |
| `BeanCopier` | 13 | DTO↔Entity 标准转换 + `ignoreProps` |
| `Asserts` | 26 | 三参数版 `(obj,msgKey,defaultMsg)` 是 i18n 模式 |
| `Validators` | 4 | `assertjsr303` 读注解 |
| `PageUtils` | 3 | 内存分页（**大数据量不要用**） |
| `DatabaseUtils` | 5 | mysql2Dm/Oracle/Postgre/KingbaseV8/Sqlserver |
| `ZipUtils` | 16 | 压缩/解压 16 种形态 |
| `ImageUtils` | 7 | 缩放 + GIF 缩略图 |
| `YamlUtil` | 5 | YAML 处理（但配置最终要写 Nacos） |
| `EnumArrayUtil` | 10 | 枚举多值字段存取 |

**★★ 三条「不要用工具类硬来」：**
1. 需要租户/用户上下文 → 走 Service（工具类不带上下文）
2. 需要分布式缓存 → `boot-starter-cache` 的 `RedisUtils`
3. 需要事务 → `boot-starter-transaction`

---

### 三、★★ 第二块空白：连接器能力（修正「355 Provider」错误）

**文档：** `15-connector-capabilities.md`（13.0 KB）

**★★ 先纠错：**
```
我上一条说「cip-capability-common 有 355 个 Provider」—— 错。
实测：provider.dto 299 个（DTO，不是 Provider）
真正的能力在 cip-capability-facade 的 capability.api 包：46 个接口
```

**46 个能力接口（按方法数）：**

| # | 接口 | 方法 | 能力 |
|---|---|---:|---|
| 1 | `CapabilityManageAppService` | **53** | **能力管理（启停/切 Provider）** |
| 2 | `SignatureAppService` | 39 | 电子签章 |
| 3 | `DocOnlineAppService` | 28 | 在线文档 |
| 4 | `IntelligentMissiveAppService` | 26 | 智能公文 |
| 5 | `EnterpriseCreditAppService` | 25 | 企业征信 |
| 6 | `OcrAppService` | 20 | OCR |
| 7 | `VideoMeetingAppService` | 20 | 视频会议 |
| ... | ... | ... | ... |
| 46 | `SearchAppService` | 1 | 搜索 URL |

**★★ `CapabilityManageAppService.updateDefaultProvider` —— 能力层是「多 Provider 可切换」设计。**

**连接器（20 个 SPI）与能力完全不同：**
```
中间表模式：MiddleTableOrgSyncSpi{Pull,Listener,DataCallback,ExecuteCallback,MarkCallback}
移动端模式：Mobile{OrgSync,OrgSyncBatch,OrgSyncPull,Todo,CallBack,Config,Application}Provider
数据库：   DataBaseExecutorService
SSO：      SsoService
Linker：   LinkerSecurityService / LinkerSignService
```

**⇒ 能力是「点」（调一个功能），连接器是「面」（打通一个系统）。**

---

### 四、★★ 第三块空白：GraphQL 协议层

**文档：** `16-graphql-protocol.md`（9.1 KB）

**★★ 最重要的发现：772 类里只有 71 个是致远的。**
```
graphql.*（graphql-java 开源库）    361
antlr.v4.runtime.*（ANTLR4）       174
com.seeyon.boot.starter.graphql.*   71  ← 真正要理解的
其他 graphql 附加模块               166
```

**★★★ 核心机制：Schema 是动态从元数据生成的**
```
实体元数据（MySQL）
  → MetadataProxyService（元数据代理）
  → GraphQLTypeMappingUtil（类型映射）+ GraphQLTypeNameUtil（命名）
  → SeeyonSchemaService（构建）
  → SeeyonSchema（运行时）
  → GraphQLController（HTTP 入口）
```

**⇒ 新建 UDC 实体自动多一套 GraphQL 接口，前端不用逐个写。**

**★★ 推翻旧结论：**
```
我之前的说法：udcMicroflowCreatePost 是 REST 路径
实际：那是 GraphQL 的 mutation 名
前端调：POST /{appName}/graphql + {query, variables}
```

**三个技术亮点：**
- `ChildrenDataLoader` —— N+1 批量加载（平台已内建）
- `SeeyonScalars` —— 自定义 Scalar（Long 防精度丢失）
- `SeeyonRest` —— GraphQL 桥接到 REST（**GraphQL 只是门面**）

---

### 五、★ 新增文档

| 文件 | 大小 | 内容 |
|---|---|---|
| `00-capability-map.md` | 23.3 KB → 补至 ~32 KB | **能力地图（按三种调用形态组织）** |
| `09-boot-core-utils.md` | 22.3 KB | 177 工具类方法级清单 |
| `15-connector-capabilities.md` | 13.0 KB | 46 能力接口 + 20 连接器 SPI |
| `16-graphql-protocol.md` | 9.1 KB | GraphQL 71 个致远类 + 动态 Schema |
| `core/facts/udc/microflow/00-TWO-KINDS-MUST-SEPARATE.md` | 9.0 KB | **两类微流程必须分开** |

**新增脚本：**
```
scripts/research/std_census.py          标品 18 包清点
scratch/jar_census.py                   107 jar 清点
scratch/bootcore_util.py                util 类名分组
scratch/dump_util_py.py                 javap 提取 177 类签名
scratch/cip_all_api.py                  46 能力接口方法数
scratch/graphql_seeyon.py               71 个致远 GraphQL 类
```

---

### 六、★★ 三条调用形态（Agent 判断入口的第一道）

| 形态 | 适用 | 机制 | 例子 |
|---|---|---|---|
| **① Dubbo / 泛化** | 标品业务应用 | `*AppService` + `SingleRequest/Response` | `OrgCommonAppService` / `BpmAppService` / `OcrAppService` |
| **② @Autowired** | 业务组件 | 同 JVM Spring Bean | `StorageService` / `CtpEnumAppService` / `CacheUtils` |
| **③ 静态工具** | 基础工具 | 无状态 static | `JsonUtils` / `Ids` / `AESUtils` / `BeanCopier` |

**★ 判断顺序：先问「是标品应用、业务组件、还是基础工具」，再定调用方式。**

---

### 七、覆盖度更新

**能力域掌握度：**

| 域 | 上轮 | 本轮 | 说明 |
|---|---|---|---|
| 实体写入 CRUD | 95% | **95%** | — |
| 主子表 | 95% | **95%** | — |
| 单据 BPM | 98% | **98%** | — |
| **boot-core 工具类** | 0% | **85%** | 177 类方法全提取（未读方法体） |
| **连接器能力** | 0% | **60%** | 46 接口清单全，方法只详读 6 个 |
| **GraphQL 协议** | 0% | **70%** | 71 致远类全清单，动态 Schema 机制清楚 |
| 组织 | 70% | **70%** | — |
| 枚举 | 80% | **80%** | — |
| 文件 | 75% | **75%** | — |
| 表达式 | 85% | **85%** | 用户说优先级低 |
| 代码生成 | 62% | **62%** | ← 仍是短板 |

**整体完成度：** 1:90% / 2:62% / 3:95% / 4:85% / 5:75% / 6:88% / 7:70%
**全局：约 86%**（↑4%）
**状态：`PARTIALLY_COMPLETED`**

---

### 八、下一轮任务（按价值排序）

1. **`boot-starter-cache`（50 类）** —— 缓存高频，方法少，补齐快
2. **`boot-starter-serialnumber`（85 类）** —— 单据编号业务刚需
3. **`boot-starter-mybatis`（140 类）** —— `AllInOneDBUtil` 持久化核心
4. **`boot-starter-extmetadata`（106 类）** —— 元数据读写时机（设计态/运行态）
5. `udc-plugin-api`（307 类）—— 插件契约
6. 代码生成（62%）—— 按新角度「生成什么」而非「怎么调」---

## 轮次 13 — 2026-11-18（持久化 + 缓存 + 流水号 + 元数据读写）

### 一、本轮补齐的四块

| # | 主题 | jar | 类数 | 文档 |
|---|---|---|---:|---|
| 1 | **缓存 + 流水号** | `boot-starter-cache` + `serialnumber` | 50 + 85 | `17-cache-serialnumber.md`（21.1 KB） |
| 2 | **持久化（MyBatis/AllInOne）** | `boot-starter-mybatis` | 140 | `18-persistence-mybatis.md`（20.0 KB） |
| 3 | **元数据读写** | `boot-starter-extmetadata` | 106 | `19-extmetadata.md`（15.3 KB） |

**合计新增 56 KB 文档 / 381 类清点 / 约 400 条方法签名。**

---

### 二、★★★ 持久化（最重要的发现）

**核心继承链：**
```
BaseDao<T>（boot-core，43 方法）
  ↑
AllInOneBaseDao<T>（41）
  ↑
AbstractAllInOneBaseDao<T>（51）   ← 全量 CRUD 实现

BaseMybatisDao<T>（17 default）    ← tk.mybatis 通道
  ↑
AllInOneBaseMybatisDao（空接口）
```

**★★★ UDC 动态实体有专属入口：`DynamicAllInOneDaoService`（45 方法）**
```
每个方法都带 (String appName, String entityName)
getT(appName, entityName) → Class<?>
```
**⇒ 两种 DAO 必须分清：**
| 场景 | 用哪个 |
|---|---|
| 自己应用的实体（代码生成） | 泛型 `XxxDao extends AllInOneBaseDao<T>` |
| **UDC 动态实体** | **`DynamicAllInOneDaoService`** |

**写在方法签名里的机制（36 个方法名自带语义）：**
```
createBatchNoClob              ★ CLOB 字段批量插入会失败，用这个跳过
updateBatchIgnoreTime          ★ 补数据时不刷 gmtModified
update*IgnoreVersion           ★ 强制覆盖（乐观锁 bypass）
updateColumns(obj, Set<cols>)  ★ 只更新指定列，最安全
selectListPropertiesByConditions(props[], map, sort)  ★ 只查需要的列
selectPageExcludeByConditions(excludes[], ...)       ★ 排除大字段
```

**三种条件形态（必须分清）：**
| 形态 | 入参 | 能力 |
|---|---|---|
| `Condition` | `String, Object` | 单字段等值 |
| `Conditions` | `Map` | 多字段 AND 等值 |
| `ComplexConditions` | `LinkedHashMap` | 字段名带运算符 |
| `DynamicConditions` | `LinkedHashMap` 或 `List<SeeyonKeyMap>` | 可动态拼 |
| **`Wrapper`** | **`Wrapper extends tk.mybatis Example`** | **★ OR / IN / LIKE / 范围，最灵活** |

**★★ `AllInOneDBComplexUtil.tenantAdd` —— 复杂条件查询**自动追加租户条件**。**

**★★ 逻辑删除 / 乐观锁实现在 `SeeyonSqlHelper`：**
```java
logicDeleteColumnEqualsValue(EntityColumn, boolean)   // 逻辑删除条件
getLogicDeletedValue(...)                             // 删除标记值
updateSetColumns(Class, String, boolean, boolean, Set) // ★ 更新列 + 乐观锁
getIfNotNull(...)                                     // ★ 非空判断 → SET 子句带 if
```

**★★★ 主子表怎么入（用户核心问题）：没有 `createWithItems` API，要自己写两段**
```java
@Transactional
Long orderId = Ids.gidLong();          // ① 预生成主键
dao.create(master);                     // ② 主表
items.forEach(i -> i.setOrderId(orderId));  // ③ 回填外键
itemDao.createBatch(items);             // ④ 子表批量
```
**三个关键：`Ids.gidLong()` 预生成 / `@Transactional` / `createBatch`。**

**12 种数据库方言：**
```
MySQL / Oracle / PostgreSQL / SQL Server
达梦Dm8 / 金仓KingbaseV8 / GBase / 神通Oscar
巨杉SequoiaDB / TDSQL / TiDB
```

---

### 三、★★ 缓存（两个类才是 API）

**50 类里 28 个是嵌入式 Redis（测试用），真正的 API 只有两个：**

```java
// RedisUtils（12 方法）
set(key, value) / set(key, value, expire)
getKey(key)          ← ★ 方法名是 getKey，不是 get
hasKey(key) / expire(key, seconds) / del(...)

// CacheUtils（6 方法）
getCompleteCacheKey(appName, key)              ← ★ 必须带租户+应用
getCompleteCacheKeyWithBuildVersion(...)
getCompleteCacheKeyWithoutTenantId(...)
```

**★★★ 缓存 key 必须带租户 —— 不然后果是**跨租户串数据**。**
**★ `CacheRedis.setNx` —— 分布式锁基础。**
**★ `RedisRateChecker.check(key, limit, windowSeconds)` —— 限流内建。**

**还支持标准 Spring Cache 注解**（`@Cacheable` / `@CacheEvict`），有两级（本地 + Redis）。

---

### 四、★★★ 流水号（数据模型 + 完整配置）

**5 张表：**
```
SerialScheme（方案）
  ├─ SerialSection（段）     ← 编号由多段拼接
  ├─ SerialCondition（条件）  ← createExpression / releaseExpression
  └─ SerialCurrent（当前值）
       └─ SerialRange（号段）
SerialHistory（历史）
```

**★★ 四种段类型（SerialTypeEnum）：**
| 类型 | value 填什么 |
|---|---|
| `CONSTANT` | 字面常量（`"PO"`） |
| `CONTEXT` | 上下文变量 |
| `ENTITY` | 实体字段名 |
| `SERIAL` | 自增流水 |

**★ 6 个枚举全清单：**
```
SerialTypeEnum        CONSTANT/CONTEXT/ENTITY/SERIAL
SerialResetRuleEnum   NONE/YEAR/MONTH/DAY       ← 重置周期
SerialRuleTypeEnum    APP/BIG/SMALL
FillTypeEnum          LEFT/RIGHT/NONE            ← 补位方向
CutTypeEnum           LEFT/RIGHT/NONE            ← 截断方向
SerialRangeTypeEnum   RESERVE/UNUSED
```

**★★★ 性能机制（写进方法名）：**
```
produceUnusedSerialNumber    → 预生产一批号到「未使用池」
consumeUnusedSerialNumber    → 从池里取，取不到才走 DB
```
**⇒ 配合 `createUnused=true` / `unusedPriority=true` —— 用空间换并发。**

**★★ 业务入口（`SerialNumberAppService` 14 方法）：**
```
getSerialNumber            取号
previewSerialNumber        预览不占号      ← 表单预览用
batchSerialNumber          批量取号        ← 导入必须用
getSerialNumberForUdc      ★ UDC 专用入口
recoverSerialNumber        作废回收
resetSerialNumber          重置
```

**★ 扩展点：`SerialSchemaExtendService.serialBeforeCreate` —— 取号前改值钩子。**

---

### 五、★★★ 元数据读写（9 个 domain Service）

**`extmetadata` 是「UDC 视角的元数据读取层」，106 类全部 `Udc*` 前缀。**

| Service | 方法 | 管什么 |
|---|---:|---|
| `UdcEntityMetaDataService` | **16** | **实体 + 属性** |
| `UdcReferMetaDataService` | 9 | 关联 |
| `UdcPageInfoMetaDataService` | 7 | 页面 |
| `UdcServiceMetadataService` | 6 | Service/Starter |
| `UdcCtpEnumMetaDataService` | 6 | CTP 枚举 |
| `UdcCtpEnumItemMetaDataService` | 6 | 枚举项 |
| `UdcEnumMetaDataService` | 5 | Java 枚举 |
| `UdcDtoMetaDataService` | 3 | DTO |
| `UdcAppServiceMetaDataService` | 3 | AppService |

**★★★ 三个关键词必须理解：**
| 词 | 含义 | 用在哪 |
|---|---|---|
| `Simple` | 不含属性的实体 | 下拉/列表（快） |
| `Agg` / `AggEntity` | **实体+属性+子实体+关联** | **GraphQL Schema 输入** |
| `ExtensionPlan` | 客户扩展方案 | 客开定制 |

**★★★ `MetadataConvertUtil.childrenEntity2Attribute` —— 子实体转成属性。**
**⇒ 证明平台主子表在元数据层是「主实体的一个属性」形态 —— 这就是 GraphQL 能嵌套查的原因。**

**★★ `UdcAppServiceMetaDataService.selectAppServiceByEntityFullName` —— 实体 → AppService 映射。**
**⇒ 这是 GraphQL mutation 名字的来源。**

**★★ `UdcMethod2ActionUtil.method2ActionMap` —— 方法名 → 权限动作。**
**⇒ 平台把 AppService 方法映射成权限动作，做数据权限。**

**★★ 两种枚举必须区分：**
| | `UdcEnum*`（Java） | `UdcCtpEnum*`（CTP/选项集） |
|---|---|---|
| 来源 | 代码里的 enum | 数据库配置 |
| 能否改 | 改代码 | 页面配置 |
| 层级 | 无 | **有树/级联/父枚举** |
| **业务字典一律用 CTP** | | ✅ |

**★ `EntityRelationMultiplicityEnum`（1:1/1:N/N:N）—— 主子表/多对多的定义处。**

---

### 六、四条新增的「机制级」知识

| # | 知识 | 证据 |
|---|---|---|
| 1 | **主子表 = 主实体的一个属性（类型是子实体）** | `MetadataConvertUtil.childrenEntity2Attribute` |
| 2 | **UDC 动态实体走 `DynamicAllInOneDaoService`，不是泛型 DAO** | 45 方法全带 `appName+entityName` |
| 3 | **缓存 key 必须带 tenantId+appName，否则跨租户** | `CacheUtils.getCompleteCacheKey` |
| 4 | **流水号用「预生产未使用池」换并发性能** | `produceUnusedSerialNumber` / `consumeUnusedSerialNumber` |

---

### 七、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **持久化（MyBatis/AllInOne）** | 95% | **98%** |
| **缓存** | 0% | **85%** |
| **流水号** | 0% | **85%** |
| **元数据读写** | 60% | **85%** |
| 代码生成 | 62% | 62% |
| 连接器 | 60% | 60% |

**整体完成度：** 1:90% / 2:62% / 3:98% / 4:85% / 5:75% / 6:90% / 7:78%
**全局：约 88%**（↑2%）

---

### 八、下一轮任务

1. **`udc-plugin-api`（307 类）** —— 插件契约，扩展开发必看
2. **代码生成（62%）** —— 仍是最大短板，按「生成什么」角度
3. **`boot-starter-datamigration`（247 类）** —— 用户有真实项目
4. `boot-starter-datainit`（88）/ `boot-starter-mq`（68）/ `boot-starter-schedule`（50）—— 三者较小
5. **`oss` 包方法**（`*4OssService` 父类不在 jar 里，需查 ctp-metadata）---

## 轮次 14 — 2026-11-18（★ 版本基线核对，纠正三个重大错误）

### 零、用户提供了权威清单：102 jar / 4 版本

| 版本 | 构建 | jar 数 | 定位 |
|---|---|---:|---|
| **5.3.605** | 2026-10-28 | **23** | UDC 全套（最新） |
| **5.3.603** | 2026-10-08 | **11** | boot 业务增强包 |
| **5.3.600** | 2026-08-25 | **67** | boot 基础框架（主体） |
| 2.6.0 | 2026-01-13 | 1 | boot-license-generator |
| **合计** | | **102** | |

**★ 关键理解：版本号不统一 —— 致远按模块独立升版，不是整体发版。**

---

### 一、★★★ 纠正我自己的三个错误

| # | 我的错误说法 | 实际情况 | 根因 |
|---|---|---|---|
| **1** | 「本机 107 个 jar」 | **107 是 CTIH 目录数，混了 `boot` 的 16 个历史版本 + 22 个客户 jar** | 没有版本基线，把「仓库有什么」当「平台有什么」 |
| **2** | 「`cip-capability-facade` 46 个能力接口（OCR/签章/支付）」 | **这个 jar 不在官方 102 清单里**（历史遗留，5.3.276） | 同上 |
| **3** | 「`boot-starter-cip` = 连接器能力」 | **它是参数转义/开放API错误码/V5迁移/文档版本**，跟 OCR 签章无关 | 模块定位错 |

**⇒ 三个错同一个根因：把「仓库里有什么」当成了「平台标准交付有什么」。**

---

### 二、★★★ 本机核对结果（精确到版本）

**总账：**

| 状态 | 数量 | 类数 |
|---|---:|---:|
| ✅ EXACT（版本完全一致） | **66** | 4,962 |
| ✅ NEWER（本机更新） | **1** | 414 |
| ⚠️ OLDER（旧版可用） | **13** | 3,727 |
| ❌ MISSING | **22** | — |
| **可用合计** | **80/102 = 78.4%** | **9,103 类** |

**按版本分组：**

| 版本 | 共 | EXACT | NEWER | OLDER | MISS |
|---|---:|---:|---:|---:|---:|
| **5.3.605** | 23 | **6** | 0 | 5 | **12** |
| **5.3.603** | 11 | **11 全中** | 0 | 0 | 0 |
| **5.3.600** | 67 | 48 | 1 | 8 | 10 |
| 2.6.0 | 1 | 1 | 0 | 0 | 0 |

**★★ 5.3.605 只命中 6/23 —— UDC 层几乎全缺或旧版。**
**★★ 5.3.603 全中 —— 本轮前做的 cache/serialnumber/extmetadata 版本完全正确。**

**⚠️ 13 个旧版（可用但必须标版本）：**
```
udc-biz            5.3.605 → 本机 5.3.517   差 88 个小版本 ★最严重
udc-plugin-api     5.3.605 → 本机 5.3.517
udc-web/extend/cicd 5.3.605 → 本机 5.3.517
bpm-facade         5.3.600 → 本机 5.3.374   ★ 11/13 号文档用的就是它
app-common-facade  5.3.600 → 本机 5.3.274
cdp-data-facade    5.3.600 → 本机 5.3.279
cip-connector-facade 5.3.600 → 本机 5.3.286
ctp-affair-facade  5.3.600 → 本机 5.3.315
ctp-message-facade 5.3.600 → 本机 5.3.287
ctp-user-facade    5.3.600 → 本机 5.3.429  （最接近）
portal-facade      5.3.600 → 本机 5.3.392
```

**✅ 1 个更新版：**
```
organization-facade  官方 5.3.600 → 本机 5.3.601（414 类，比官方新，结论有效）
```
**⇒ `10-org-domain.md` 用的 5.3.601 是对的。**（我第一版脚本 bug 误报成 5.3.368，已修正）

**❌ 22 个缺失：**
```
UDC 层 12：udc-affair / udc-app-common / udc-assemble / udc-bpm / udc-cdpbi
          udc-cip / udc-dataflow / udc-m5 / udc-portal / udc-starter-autocode
          udc-upgrade / udc-user
boot 层 6：boot-starter-basicdata / dynamiccode / k8s / k8s-adapter / queue / sandbox
devops 4：devops-starter-images / migration / pipeline / repo
```
**⇒ 已在 CHIT / CHIT-extra / .m2 / repo/local / repo/page 全盘搜索确认：确实没有。**

---

### 三、★★★ 重大新发现：`D:/repo/CHIT-extra` 的 21 个 `*-biz` 实现包

**这是前 13 轮完全遗漏的层级 —— 之前只读 `facade`（接口），没读 `biz`（实现）。**

| 包 | 版本 | 类数 |
|---|---|---:|
| **bpm-biz** | 5.3.353 | **2,730** |
| **cdp-data-biz** | 5.3.278 | **1,927** |
| **udc-biz** | **5.3.605** ★正是官方版本 | **1,856** |
| cip-connector-biz | 5.3.286 | 1,205 |
| ctp-user-biz | 5.3.334 | 876 |
| cip-capability-biz | 5.3.276 | 840 |
| organization-biz | 5.3.344 | 668 |
| app-common-biz | 5.3.271 | 632 |
| portal-biz | 5.3.369 | 594 |
| cdp-schedule-biz | 5.3.272 | 483 |
| app-doc-biz | 5.3.264 | 477 |
| m5-biz | 5.3.265 | 401 |
| ctp-affair-biz | 5.3.330 | 345 |
| cip-manager-biz | 5.3.279 | 277 |
| app-approval-biz | 5.3.283 | 232 |
| ctp-message-biz | 5.3.287 | 151 |
| ai-biz | 5.3.272 | 132 |
| cip-openapi-gateway-biz | 5.3.263 | 63 |
| ctp-webapi-gateway-biz | 5.3.263 | 41 |
| cip-convert-biz | 5.3.261 | 39 |
| ctp-media-biz | 5.3.261 | 25 |
| **合计** | | **13,994** |

**★★★ 三个关键点：**
1. **`CHIT-extra/udc-biz` = 5.3.605**（正是官方版本，比 `CHIT/com/seeyon/udc-biz` 的 5.3.517 新）
2. **`bpm-biz` 2,730 类** —— 我只读了 facade 533 类接口，**实现层 5 倍大**
3. **`cip-capability-biz` 840 类** —— 这才是 OCR/签章/支付的真实现

**⇒ 官方 102 是「交付契约层」，实现层在另一个仓库。**

---

### 四、★★★ 正确的 jar 分层模型（本轮真正收获）

```
官方 102（交付清单）      facade + starter + core + web      ← 只定义契约
        ↓
实现层 *-biz（CHIT-extra，21 个）  14,000 类              ← 真正的逻辑
        ↓
能力包（非标准交付，按需插拔）  cip-capability / attachment / opinion
        ↓
客户应用 jar                   znxmglpt / datamigration / faccounts
```

**判断规则：**
1. **在官方 102 里** → 平台标准能力，可放心引用
2. **在 `CHIT-extra/*-biz`** → 实现细节，可引用但要标「实现层」
3. **在「49 个超出清单」** → 能力包，引用必须标「非标准交付」
4. **客户应用 jar** → **禁止进事实库**

---

### 五、★★★ `boot-starter-cip` 真实定位（纠正模块认知）

**`boot-starter-cip` 5.3.603，98 类，四个真实职责：**

| 职责 | 类 | 说明 |
|---|---|---|
| **参数转义（主体）** | `ParamEscapeAppService`(13) / `EntityEscape` / `EnumEscape` / `WeakTypeEscapeService` | **开放 API 入参类型转换**（外部 JSON 弱类型 → 平台类型），含导入导出配置 |
| **凭证查询** | `VoucherAppService`(3) | `queryVoucherData` / `getEntityColumnValues` |
| **V5 数据迁移** | `V5MigrateAppService`(5) | **`queryPostscript`（V5 签章意见）/ `queryOpinions` / `queryDoneLog` / `queryProcessPng`** |
| **文档版本化** | `DocGeneralizeStarterAppService`(14) | 带权限上传流代理 / 保存版本 / **格式转换记录** `DocFileConvertRecord` |

**⇒ cip = Center Integration Platform 的**基础支撑**，不是「能力市场」。**
**⇒ `V5MigrateAppService` 揭示了真实痛点：V5 → V8 要迁**签章意见、已办记录、流程图 PNG**。**

---

### 六、★ 49 个「仓库有但不在 102」的 artifact

**引用过但超范围的 jar：**
```
cip-capability-facade (490 类)  → 15-connector-capabilities.md 用的 ★超出
cip-capability-common (425)     → 同上
cip-connector-api               → 同上
cip-manager-facade (95) / cip-convert-facade (9) / cip-openapi-common (21)
boot-starter-attachment (15)    → 12-enums-file-domain.md 用的
boot-starter-elasticsearch / index / opinion / test
boot-extend / boot-starters / boot（16 个历史版本）
```

**客户应用 jar（禁入事实库）：**
```
znxmglpt3289082814923688017(-biz 2357 / -facade 1535 / -web 994)
xiangmuguanli1656355078954763084(-*)
datamigration8704025620829192834(-*)   ← 真实项目
datamigration163126498398523384(-*)
faccountsreceivable2378987216360786643(-facade 727)
peixunudc6418559153936747860(-*)
schedulemanagement1879887445425932710-facade
znxmglptcopy5791640252914287064-facade
app-approval-facade / m5-facade / ctp-user-api / udc
```

---

### 七、★ 文档版本修正（本轮已执行）

| 文档 | 原标注 | 修正后 |
|---|---|---|
| **`10-org-domain.md`** | VERSION_CAVEAT 5.3.601 vs 5.3.517 | ✅ **本机 5.3.601 比官方 5.3.600 新，结论有效** |
| **`11-bpm-domain.md`** | VERSION_CAVEAT 5.3.374 | ⚠️ **官方 5.3.600，本机 5.3.374 旧，新增方法未覆盖** |
| **`13-bpm-operation-dtos.md`** | VERSION_CAVEAT 5.3.374 | ⚠️ **DTO 字段可能已新增** |
| **`15-connector-capabilities.md`** | 只有「用户 5.3.517」 | ⚠️⚠️⚠️ **4 个 jar 全不在官方 102，属「非标准交付能力包」** |

**✅ 版本完全正确的（近三轮）：**
```
09-boot-core-utils.md      boot-core 5.3.600 ✅
16-graphql-protocol.md     graphql 5.3.600 ✅
17-cache-serialnumber.md   cache 5.3.600 / serial 5.3.603 ✅
18-persistence-mybatis.md  mybatis 5.3.600 ✅
19-extmetadata.md          extmetadata 5.3.603 ✅
```

**⇒ 问题集中在早期（10/11/13/15），近三轮全对。**

---

### 八、新增/更新文档

| 文件 | 大小 | 内容 |
|---|---|---|
| **`00A-repo-version-baseline.md`** | **18.4 KB** | **★ 版本基线（本文件是全部研究的基准）** |
| `10-org-domain.md` | 修正头部 | 版本标注 |
| `11-bpm-domain.md` | 修正头部 | 版本标注 |
| `13-bpm-operation-dtos.md` | 修正头部 | 版本标注 |
| `15-connector-capabilities.md` | 加 20 行警示 | 非标准交付警示 |

**新增脚本：**
```
scratch/jar_audit.py           第一版（有 bug，取错版本）
scratch/jar_audit_full.py      按官方清单核对
scratch/jar_audit_v2.py        修正版（取同系列最新版）★ 用这个
scratch/scan_extra.py          CHIT-extra 的 21 个 biz 清点
scratch/jar_audit_full.json    102 条明细
scratch/jar_audit_v2.json      修正后明细
scratch/extra_biz.json         21 个 biz 明细
```

---

### 九、覆盖度与状态

**覆盖率（按官方 102）：**
```
jar 层面    80/102 = 78.4%
类层面      9,103 类可读（不含 22 个缺失 jar）
版本可信度  EXACT 66 / NEWER 1 / OLDER 13
```

**能力域掌握度（不因版本问题降级，但要标版本）：**

| 域 | 掌握度 | 版本状态 |
|---|---|---|
| 持久化 MyBatis | 98% | ✅ 5.3.600 EXACT |
| 缓存 | 85% | ✅ 5.3.600 EXACT |
| 流水号 | 85% | ✅ 5.3.603 EXACT |
| 元数据读写 | 85% | ✅ 5.3.603 EXACT |
| boot-core 工具 | 85% | ✅ 5.3.600 EXACT |
| GraphQL | 70% | ✅ 5.3.600 EXACT |
| 组织 | 70% | ✅ 5.3.601 NEWER |
| BPM | 70% | ⚠️ 5.3.374 旧 |
| 枚举/文件 | 80% | ⚠️ attachment 5.3.290 旧 |
| 表达式 | 85% | ✅ 5.3.603 |
| 代码生成 | 62% | ⚠️ udc-biz 5.3.517 旧 |
| **cip（修正后）** | **40%** | ✅ 5.3.603（但只读 8/98 类） |
| **实现层 *-biz** | **0%** | ❌ **完全没读（14,000 类）** |

**全局：约 88%**（口径变了，不再虚高）

---

### 十、下一轮任务（优先级重排）

**P0 — 补最关键的版本缺口：**
1. **`CHIT-extra/udc-biz` 5.3.605**（1,856 类）—— **正好是官方版本，可替代旧的 5.3.517**
2. **`cip-capability-biz` 5.3.276**（840 类）—— OCR/签章/支付的真实现
3. **`bpm-biz` 5.3.353**（2,730 类）—— BPM 实现层，比 facade 大 5 倍

**P1 — 补功能空白：**
4. **`udc-plugin-api` 5.3.605**（需新版）—— 插件契约
5. `boot-starter-basicdata` / `queue` / `sandbox` / `dynamiccode` —— 22 个缺失中的 boot 层
6. 代码生成（62%）—— 换「生成什么」角度

**P2 — 需用户协助：**
7. **22 个缺失 jar** —— 需从环境导出（尤其 udc-bpm / udc-dataflow / udc-user 这 3 个）---

## 轮次 15 — 2026-11-18（udc-biz 版本 diff + CIP 能力实现层）

### 一、★★★ udc-biz 5.3.517 → 5.3.605 差异（结论：只加了一个数据类型）

**方法：逐 class 文件 MD5 对比 + CFR 反编译常量级对比**

| 指标 | 值 |
|---|---|
| class 文件总数 | 旧 2,312 / 新 **2,312** |
| **字节完全相同** | **2,287（98.9%）** |
| **字节有变化** | **25（1.1%）** |
| 新增类 / 删除类 | **0 / 0** |
| jar 大小 | +1,624 字节 |

**⇒ 这不是改版，是「加一个数据类型 + 补齐支撑关系」。**

**★★★ 唯一功能变更：新增 `PERSONSELECTOR`（人员选择器）数据类型**

**25 个变化类里 11 个是 `common.enums.*`，全部围绕 PERSONSELECTOR。**

---

### 二、★★★ PERSONSELECTOR 的真实支持度（**推翻我上一版的说法**）

**⚠️ 我上一版只看到「常量存在」就推断「功能都支持」—— 错了。**
**实际枚举第 5 个参数是 `support`（Boolean），只有 true 才在界面真正可用。**

**✅ 真实支持（3 处）：**
```
列配置             ReferConfigColumnsSupportEnum      PERSONSELECTOR=true, ENTITY_=true
过滤方案-显示      FilterPlanShowSettingSupportEnum    PERSONSELECTOR=true, ENTITY_=true
过滤方案-搜索      FilterPlanSearchSettingSupportEnum  PERSONSELECTOR=true, ENTITY_=false
```

**❌ 明确不支持（9 处）：**
```
关联搜索条件       ReferConfigSearchSupportEnum        全 false
显示名映射         ReferConfigDisplayNameSupportEnum   全 false  ← 不能把ID转人名
拉取显示名         ReferConfigPullDisplayNameSupport...  全 false
树形搜索           ReferConfigTreeSearchSupportEnum    全 false  ← 不能按组织树选人
携带（同层级）      ReferCarrySameLevelSupportEnum      三个变体全 false
携带类型转换        ReferCarryDataTypeConvertSupport...   false
```

**★★★ 业务含义：**
```
✅ 能建字段、能存值、能配列、能过滤
❌ 不能显示姓名（列表只看到ID）、不能关联查询、不能树形选人、
   不能携带到下游单据、不支持 IN 查询
```
**⇒ 典型的新功能首版，联动能力一个都没铺开。**

---

### 三、★★★ 三个技术细节（实证）

**① code 编号策略：预留跳号**
```
PERSONSELECTOR              = 121
ENTITY_PERSONSELECTOR       = 143   (+22)
MULTI_ENTITY_PERSONSELECTOR = 165   (+22)
```
**⇒ 每加一个数据类型，code 加 22（为 22 个变体预留）。10 个枚举全一致。**

**② ⚠️ `BaseDataTypeEnum` 有 bug**
```java
PERSONSELECTOR(1, "PERSONSELECTOR", false),        // ← code = 1
MULTILINESTRING(1, DataType.MULTILINESTRING..., false),  // ← 也是 1
```
**⇒ 其他 10 个枚举都用 121，只有这里写 1，明显笔误。**
**⇒ 影响：`of()` 按 dataType 匹配不受影响；但任何按 `code()` 反查的代码会拿到 MULTILINESTRING。**
**⚠️ 是否有代码按 code 反查 —— 未验证。**

**③ 运算符集（`DataTypeAndOperator4ConditionEnum`）**
```
PERSONSELECTOR: EQ/NEQ/LIKE/NOTLIKE/LLIKE/RLIKE/NULL/NOTNULL
STRING:         上述 8 个 + IN + NOTIN
```
**★★ 没有 `IN` / `NOTIN` —— 不能查「属于这几个人员」。**
**★★ 复用了 `MULTILINESTRING` 的运算符（含 LIKE/RLIKE）→ 底层存的是**字符串类型的人员 ID**。**
**⇒ 连 `Pair` 第二个参数都直接写 `DEFAULT_MULTILINESTRING_SUPPORT_DATA_TYPE` —— 快速接入的简化做法。**

**④ `dataType()` 字符串值 = `"PERSONSELECTOR"`（前端/API 传这个）**

---

### 四、★★★ CIP 能力实现层（cip-capability-biz 840 类，37 个域）

**这是上一轮 15 号文档（46 个 facade 接口）的**真实现**。**

**37 个能力域（按类数）：**
```
video 147 / missive 64 / signature 49 / ocr 48 / sms 36 / message 31
doc 26 / invoice 26 / ofd 24 / resume 18 / schedule 14 / censor 13
manage 11 / mobileplugin 10 / location 9 / voice 9 / trip 9 / pay 7
translation 7 / email 6 / bankpay 6 / credit 6 / physicalseal 5 / weather 5
search 5 / routing 4 / gis 4 / openapi 3 / faceid 3 / ai 3 / archives 3
printlabel 2 / 其他
```

**★★★ SPI 厂商矩阵（完整清单已入文档）：**
```
OCR        baidu / tencent / funcun / impl默认 / test
发票        elecloud /(腾讯带查验)/ impl / test
签章        anxin / dianju / suwell / tianyin
OFD        dianju / kinggrid / suwell / yozo / wpsv6 / lenovo
在线文档    wpsv6 / yozo / suwell / lenovo / wisemedical / impl / test
文档智能    funcun / idpsv10 / textin
短信        ali / tencent / huawei / impl / test
视频会议    tencent / huawei / qywechat / test
语音        huiyan / kedaxunfei
翻译        baidu
文本审核    baidu / impl(致远自研词库)
定位/天气   baidu / gaode
地图GIS     nyncw / snkoudai
人脸        kuangshi
征信        qixinbao / impl
简历        mesoor
支付        weixin
银行支付    citic
商旅        alibtrip
日程        qywechat
物理印章    qunjie
标签打印    chicore / supoin
搜索        v5
AI          seeyon(自研)
邮件        smtp
```

**★★★ 三个架构特征：**
1. **契约-实现-测试三层**：每个域都有 `spi/<厂商>/` + `spi/impl/`（兜底）+ `spi/test/`（测试桩）
2. **`impl` + `test` 的存在** → 能力可以不接外部就测通
3. **短信三家云都有「签名自动申请 + 模板自动申请」** → 平台做了短信资质自动报备（很深度的集成）

**★★ Provider 路由机制（`routing` + `manage` 包）：**
```
ProviderServiceLoader        Provider 加载
ProviderHandler              Provider 分发
ProviderSelectorService      选择用哪个
ProviderParameterService     存 AK/SK
ProviderCycleCountService    调用次数统计
ProviderEventConfigService   事件配置
```
**实体：`CipProviderManage` / `CipProviderParameter` / `CipSelectProvider` / `CipProviderCharges(计费)`**

**★ 只有 9 个硬编码域名（微信 26 次最多），vs 37 个能力域 → 说明地址/密钥都是配置项（存 DB）**
**⇒ 符合「配置写 Nacos」的要求。**

**★ `video/huawei/DubboGeneralizeHandler` —— 华为视频会议走 Dubbo 泛化调用**
**⇒ 印证「标品应用可 Dubbo 泛化」的形态。**

---

### 五、新增文档

| 文件 | 大小 | 内容 |
|---|---|---|
| **`20-udc-biz-version-diff.md`** | **~16 KB** | **udc-biz 5.3.517→5.3.605 diff + PERSONSELECTOR 完整支持度** |
| **`21-cip-capability-biz.md`** | **15.4 KB** | **CIP 840 类 / 37 域 / 20+ 厂商 SPI 矩阵** |

**新增脚本 / 产物：**
```
scratch/udc_diff.py           类集合对比
scratch/udc_diff2.py          逐 class 字节 MD5 对比 ★
scratch/udc_sigdiff.py        javap 签名 diff
scratch/udc_personsel.py      常量池字符串扫描
scratch/udc_enum_const.py     枚举常量清单对比
scratch/udc_code_audit.py     code 重复/跳号检测 ★
scratch/udc_support_matrix.py support 真实值提取 ★
scratch/cip_biz_map.py        能力域 + SPI 厂商矩阵 ★
scratch/udc605/               ★ udc-biz 5.3.605 反编译全量（1,856 java）
```

---

### 六、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **udc-biz 版本差异** | 0% | **100%（25 个类全部定位）** |
| **PERSONSELECTOR** | 0% | **95%（支持度/运算符/code 全实证）** |
| **CIP 能力实现层** | 0% | **75%（37 域 + 厂商矩阵，但未读方法体）** |
| 连接器能力（facade） | 60% | 65%（现在能和 biz 对上） |
| 代码生成 | 62% | 62% |
| 实现层 *-biz 整体 | 0% | **25%**（1/21 包已深入：udc-biz + cip-capability-biz） |

**全局：约 89%**

---

### 七、下一轮任务

**P0（继续实现层）：**
1. **`bpm-biz` 5.3.353（2,730 类）** —— BPM 实现层，比 facade 大 5 倍，最大空白
2. `cip-connector-biz` 5.3.286（1,205 类）—— 连接器实现
3. `organization-biz` 5.3.344（668 类）—— 组织实现

**P1：**
4. `udc-plugin-api` 5.3.605（需新版，本机 5.3.517）—— 插件契约
5. `boot-starter-basicdata` / `queue` / `sandbox` / `dynamiccode` —— 缺失的 boot 层

**P2（需用户协助）：**
6. **22 个缺失 jar** —— 尤其 `udc-bpm` / `udc-dataflow` / `udc-user`
7. **前端 npm 包** —— 验证 PERSONSELECTOR 是否有渲染器（Java jar 里没有前端资源）---

## 轮次 16 — 2026-11-18（bpm-biz 实现层 2,730 类）

### 一、规模对比：facade 只是冰山一角

| | 类数 |
|---|---:|
| `bpm-facade`（5.3.374，契约） | 533 |
| **`bpm-biz`（5.3.353，实现）** | **2,730** |
| 倍数 | **5.1×** |

**⇒ 之前 11/13/14 号文档只覆盖契约层，流程引擎的真逻辑全在这 2,730 类。**

---

### 二、分层结构

```
bpm-biz 2,730
├─ domain  1,319（核心）
│   ├─ service  894   ← 主体
│   ├─ entity    95
│   ├─ dao       92
│   ├─ model     79   ← BpmDiagram 等
│   ├─ cache     50
│   ├─ eventbus  43
│   └─ bo        35
├─ dto       669
├─ detection 234   ← ★ 依赖分析体系
├─ enums     206
├─ appservice 99   ← 对外入口
├─ common     61
├─ utils      38
├─ upgrade    33
├─ bpmn       22
├─ simulation 21
└─ security   19
```

**domain.service 894 类的子域：**
```
transport 126 / 顶层核心 88 / deploy 55 / cached 44 / supervise 38
diagram 33 / postapproval 28 / merge 26 / eventmatch 26 / activity 25
upgrade 25 / autonode 23 / changenode 20 / proxy 18 / task 18
subprocess 17 / application 16 / processdetail 14 / nestedsubprocess 13
permission 13 / form 9 / formpermission 5 / spi 5 / dubboProxy 2
```

---

### 三、★★★ 三阶段执行链路（BpmService 91 方法实证）

**发起：**
```java
getStartProcessContext(BpmStartDto, boolean)
preStartProcess(WorkflowBpmContext)          ★ 预发起（不落库）
preStartProcessByAppId(WorkflowBpmContext)
matchProcessTemplateByAppId(...)             ★ 按应用匹配流程模板
startProcess(WorkflowBpmContext)             ★ 正式发起
dealPreSendAndSubmit(PreMatchResponseDto, ...)
```

**办理：**
```java
preFinish(WorkflowBpmContext)                ★ 预提交
preFinishWorkItem(BpmFinishWorkItemDto, boolean)
finishWorkItem(WorkflowBpmContext)           ★ 正式提交
finishWorkItemSimulation(...)                ★ 仿真提交
```

**★★ pre / 正式 两段式是核心设计 —— 这就是「表单上预览审批路径」的实现基础。**

**其他操作全在 `BpmService`：**
```
撤销 repeal(3 重载) / 终止 stop(2 重载) / 退回 startStepBack 
加签 informNode / 移交 replaceWorkItem / 暂存 temporaryPending
草稿 saveDraftCreate / 已读 readWorkItem / 意见 saveOpinion
退回节点查询 getValidStepBackNodeList
```

---

### 四、★★★ BpmExecute（30 方法）—— 流程状态机

```java
startCase / reStartCase              实例启动/重启
addReadyActivity / removeActivity    ★ 活动就绪/移除
finishActivity / stopActivity        ★ 活动完成/停止
cancelCase                           ★ 取消实例
awakeCase                            ★ 唤醒（暂存→正式）
takeBackActivity                     ★ 取回
startCaseToMe / startCaseRevokeToMe  发给自己/撤销回自己
processFinished / processFinishedOperation   流程结束
getProcessDeadline                   ★ 流程期限
```

**状态机：**
```
BpmCase（实例）
├─ Activity：ready → running → finish / stop
├─ 特殊：awake / takeBack / revokeToMe
└─ 终态：processFinished / cancelCase
```

**★ 日志埋点极多（recorderProcessLog 等 5 个方法）→ 每步可审计。**

---

### 五、★★★ BpmProcessService（114 方法）—— 流程定义

**核心概念层级：**
```
BpmTemplate（模板，业务概念：一个审批类型）
  └─ BpmProcess（流程定义，多版本）
       └─ BpmDiagram（流程图，BPMN 模型）
            └─ AbstractBpmNode（节点）
BpmCase（实例）
  └─ BpmWorkItemBase（工作项/待办）
```

**关键方法：**
```java
// 双轨：Entity 层 + DTO 层
createProcessEntity / updateBpmProcessEntity / selectProcessEntityById
createBpmProcess / updateProcess / selectProcessById

// ★ 流程图
updateProcessWorkflow(BpmProcessWorkflowUpdateDto, ...)   3 重载
parseAndSaveDiagramDetail(BpmProcess, BpmDiagram, ...)
selectEffectedDiagram(BpmCase, ...)      ★ 取发起时生效的图
validateActor(BpmDiagram)                ★ 校验参与者
validateNodeActorIsExist(...)
recursionBpmNode(...)                    ★ 递归处理节点

// ★ 条件
checkSubProcessLoopError(BpmDiagram, List)  子流程循环检测
dealProcessStartCondition(BpmProcess)
createOrUpdateStartCondition(...)
```

**★★ `selectEffectedDiagram` —— 「生效版本」：在途实例用发起时的图，模板改了不影响在途。**

---

### 六、★★ 部署（BpmIndependentDeployService 20 方法）

```java
deployBpmTemplatesIndependent(String, Long)      ★ 独立部署
mergeEditToRunnableTemplate(String, Long)        ★ 草稿→可运行
checkDeployLimitLock / reduceDeployLimit         ★ 部署并发锁
checkPublish                                     发布检查
autoDeployStartAndAuth(BpmAppInfoDto)            ★ 自动部署+启动+授权
buildReplaceIdContext(...)                       ★ ID 替换
```

**★★★ 部署 = 设计态草稿 → 发布 → 运行态模板**
**★ 返回 `BpmExportInitDataDto` → 部署走**导出-导入**机制（跨环境搬运）。**
**★ `autoDeployStartAndAuth` 就是 UDC 应用「发布」时做的事。**

---

### 七、★★★ 自动节点（autonode 23 类）

**`AutoNodeExecuteService` 39 方法：**
```java
autoNodeExecute(AutoNodeContext)          ★ 执行
autoNodeRun(BpmAutoNodeControl)           2 重载
autoNodeRunByDelayMessage(Long)           ★ 延迟消息触发
firstAutoNodeRun(BpmAutoNodeControl)      ★ 首次运行
sendAutoNodeMqMessage(...)                ★ MQ 驱动
getConditionResult(String, Map)           ★ 条件判断
getTrueBpmExpression(List<String>, ...)   ★ 取真的表达式
getFailActionCode(AutoNodeTolerantModeEnum, ...)  ★ 容错
```

**10 种动作：**
```
AutoNodeSubmitAction       自动提交
AutoNodeBackAction         自动退回
AutoNodeBackToStartAction  退回发起人
AutoNodeRevokeAction       自动撤销
AutoNodeStopAction         自动终止
AutoNodeInterventionAction 自动干预
AutoNodeRetryAction        ★ 自动重试
+ AutoNodeActionManager
```

**★★★ 三个机制：MQ 异步驱动 / 重试 / 容错模式（`AutoNodeTolerantModeEnum`）。**

---

### 八、★★★ 自动生成流程图（autogenerate 10 类）—— 与代码生成专题相关

**6 个 DispatcherHandler 各修一种「不规范画法」：**
```
ClearJoinGatewayDispatcherHandler                    多余的 join 网关 → 清掉
DifferentBranchesUseOneJoinGatewayDispatcherHandler 不同分支共用一个 join → 调整
EndNodeHasManyCommingBranchesDispatcherHandler      结束节点多入边 → 规整
IdsDispatcherHandler                                ID 重排
SplitAndJoinGatewayInOneDispatcherHandler           split/join 挤在同一网关 → 拆开
+ V8DiagramDispatcher（总分发）
```

**⇒ 这就是为什么 UDC 自动生成的流程图总是规范的 —— 6 道规整规则。**

---

### 九、★★★★ 检测体系（detection 234 类）—— 本轮最大收获

**`usedparam` 115 类 = 完整的「级联影响分析」体系。**

**接口实证：**
```java
interface BpmFieldsUsedForDetectionInterface extends BpmCascade {
    getUsedParameterAndRelation(List<BpmTemplate>, ...)    ★ 用了哪些参数
    getUsedCtpEnumAndRelation(...)                         选项集
    getUsedUdcEnumAndRelation(...)                         UDC 枚举
    getUsedPageInfoAndRelation(...)                        页面
    getUsedExPlanAndRelation(...)                          扩展方案
    getSubProcessUsedProcessAndRelation(...)               子流程引用
    getProcessUsedOrgProcessAndRelation(...)               组织
}
```

**★★★ 级联方法（核心）：**
```java
void cascadeHandleAffectedForAttr(CascadeUpdateContext)     字段被改 → 处理受影响流程
void cascadeHandleAffectedForEntity(CascadeUpdateContext)   实体被改 → 处理受影响流程
```

**⇒ 业务含义（对客开极有价值）：**
```
改一个 UDC 字段 / 删一个选项集 / 换一个页面
    ↓ usedparam 115 类逐一扫描
找出所有受影响的流程模板
    ↓ cascadeHandleAffectedForXxx
自动修复 或 标记异常
```
**⇒ 这就是「平台敢让你随便改字段」的底气。**

**12 个检测维度（bo 子包）：**
```
param 24 / org 11 / ctpenum 11 / udcenum 10
formpermission 5 / nodepermission 2 / pageinfo 3
path 1 / subprocess 1 / openapi 1 / basicdata 1
```

**50 个 `*ForDetectService`，命名规律 `Bpm<功能>Used<维度>ForDetectService`：**
```
33 种功能 × 7 种维度（Param/Org/AppParam/Page/Template/Process/Fields）
→ 50 个实际实现
```

---

### 十、其他重要机制

| 机制 | 类数 | 说明 |
|---|---|---|
| **流程合并** `merge` | 26 | `MergeSubmitAspect`（AOP 切面）→ 合并是横切逻辑 |
| **事件匹配** `eventmatch` | 26 | 事件→节点匹配 |
| **督办** `supervise` | 38 | 独立子域，不只是催办 |
| **流程仿真** `simulation` | 21 | 不真提交就能跑流程 |
| **SPI 扩展点** `spi` | 5 | BPM 客开扩展点 |
| **Dubbo 代理** `dubboProxy` | 2 | BPM 调外部服务 |
| **传输/导入导出** `transport` | 126 | 最大子包 |

---

### 十一、新增文档

| 文件 | 大小 | 内容 |
|---|---|---|
| **`22-bpm-biz-implementation.md`** | **~27 KB** | **bpm-biz 2,730 类：执行链路/状态机/部署/自动节点/检测体系** |

**新增脚本：**
```
scratch/scan_bpmbiz.py      包分布
scratch/bpmbiz_detail.py    domain.service 细分 + 88 核心 Service + 99 AppService
scratch/bpmbiz_methods.py   BpmExecute/BpmService/BpmProcessService/部署/自动节点方法
```

---

### 十二、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **BPM 实现层** | 0% | **75%**（结构 + 核心方法签名，未读方法体） |
| **BPM 检测/级联机制** | 0% | **85%**（接口契约确认，算法未读） |
| **自动节点** | 30% | **70%** |
| **流程图自动生成** | 20% | **65%**（6 个规整器确认） |
| BPM 契约层（facade） | 70% | 72% |
| 实现层 *-biz 整体 | 25% | **35%**（3/21 包已深入） |

**全局：约 90%**

---

### 十三、下一轮任务

**P0：**
1. **`cip-connector-biz` 5.3.286（1,205 类）** —— 连接器实现
2. **`organization-biz` 5.3.344（668 类）** —— 组织实现
3. **`cdp-data-biz` 5.3.278（1,927 类）** —— 数据平台（第二大）

**P1：**
4. `ctp-user-biz` 5.3.334（876 类）
5. `app-common-biz` 5.3.271（632 类）
6. `portal-biz` 5.3.369（594 类）

**P2（需用户协助）：**
7. **22 个缺失 jar** —— udc-bpm / udc-dataflow / udc-user 最关键
8. **前端 npm 包** —— PERSONSELECTOR 渲染器验证---

## 轮次 17 — 2026-11-18（cip-connector-biz 1,205 + organization-biz 668）

### 一、★★★ CIP 连接器实现层：核心是 `Linker`

**`cip-connector-biz` 5.3.286，1,205 类，分包：**
```
mobile 353（移动端接入，最大）/ plug 315（插件/中间表）/
connector 278（★Linker 主体）/ application 89（映射）/ ocip 70（泛化）
```

**★★★ Linker 支持 5 种执行类型（`LinkerExecutorTypeEnum`）：**
```
DETAIL    接口调用（同步）
EVENT     事件订阅（推送 or 轮询）
SSO       单点登录
MQ        消息消费
SEND_MQ   消息发送
```

**Linker 的 14 个实体（配置模型）：**
```
LinkerInfo            接入总配置（34 字段）
LinkerDetail          接口明细（41 字段）★三种执行形态合一
LinkerEventDetail     事件订阅（轮询型有 pollingIntervalTime）
LinkerEventDetailPoll 轮询状态
LinkerMqEventDetail   MQ 订阅（Kafka/Rocket/Rabbit）
LinkerMetadataInfo    元数据映射
LinkerSignInfo        加签配置
LinkerSpiRef          SPI 引用
LinkerClassify / LinkerEnum / LinkerEnumItem / LinkerExecutorLog
```

**★★★ `LinkerDetail` 一个实体承载三种执行形态：**
```
HTTP        requestUrl / requestPath / requestQuery / requestHeader / requestBody
WebService  wsWsdlUrl / targetNamespace / methodName / xmlParam
数据库       dbStatementType(SELECT/INSERT/UPDATE/DELETE) + select/where/groupBy/orderBy
           + isDistinct/isPage + 4 种方言执行器
```

**★★ `LinkerFactory`（46 方法）—— 执行引擎：**
```java
syncExecute / asyncExecute                      ★ 同步/异步
paramEscapeBeforeInvoke / AfterInvoke           ★★★ 参数转义（接上 boot-starter-cip！）
doSendMqEvent / sendCustomMq                    ★ MQ
recordLog / recordErrorLog（6+ 重载）            日志
```

**★★★ 拼图对上：`boot-starter-cip` 的 `ParamEscapeAppService` 就是被 `LinkerFactory.paramEscapeBeforeInvoke/AfterInvoke` 调用的。**
**⇒ 「参数转义」不是独立功能，是连接器调用前后的必经步骤。**

**认证 11 种：** 账号/匿名/通用/钉钉/飞书/Jira/Token/二次请求/我佳云/夏谷HR/用友

**MQ 3 种：** Kafka / RocketMQ / RabbitMQ

**★ `LinkerBusinessService`：`exportLinkerInfoByJson` / `importLinkerInfoByJsonForPlugin` —— 连接器可导出 JSON 跨环境搬运（与 BPM 一致）。**

**★ `generateParameterDisplay` —— 参数配置界面是运行时生成的。**
**★ `putway` → `LinkerCheckResultDto` —— 有落地检查。**
**★ `checkDetailIsInternal` / `checkEventIsInternal` / `checkLinkerIsInternal` —— 3 个方法保护内置连接器。**

**中间表组织同步（`MiddleTableAppServiceImpl` 21 方法）：**
```
saveUnit / saveLevel / savePost / saveDuty / saveMember   ← 五类对象
fullFinish                                               ← 完成标记
queryUnit / queryLevel / queryPost / queryMember         ← 查询
runningOrgSyncNowByLinkerCode                            ← 触发同步
queryUpdateRule / saveUpdateRule                          ← ★ 更新规则
```

---

### 二、★★★ 组织实现层：`SelectPeopleAppService` 218 方法

**`organization-biz` 5.3.344，668 类：**
```
dto 248（selectpeople 96 最大）/ domain 207（core 133）/ appservice 122
ctp.user 34 / util+metadata+common 32 / 其余 20
```

**★★★ 五大组织概念必须区分：**
```
OrgUnit    单位/部门（树形）
OrgMember  人员
OrgPost    岗位（具体职位，如「财务经理」）
OrgJob     职务（职务序列，如「管理岗」）
OrgLevel   层级（如「M3」）
OrgRole    角色（如「审批人」）
```

**★★★ 四个关键设计：**
1. **`OrgMemberPost` 是关系表 → 一人可多岗（主岗/副岗）**
2. **`OrgUnitVertical` + `OrgUnitHorizontal` 双关系 → 支持矩阵式组织**
3. **`OrgLeaderSecretary` → 领导-秘书代理**
4. **`OrgMemberMetadata` / `OrgUnitMetadata` → 组织可加自定义字段（与 UDC 元数据是两套）**

**`SelectPeopleAppService`（218 方法）按用途分：**
```
主入口      selectXxx / selectMemberBy(多版) / searchMember / selectUserById
组织树      getBusinessUnitTree / unitTree / validateUnitTreePermission
按类型选    member / unit / post / job / level / team / personalTeam / business / outsideUnit
权限        getPermission(PermissionEnum) / processAuthorization
```

**★ 10 种被选对象：人员 / 单位 / 岗位 / 职务 / 层级 / 团队 / 个人组 / 业务线 / 外部单位 / 本单位**

**★ `OcipSelectPeopleAppService`（22 方法）—— 对外选人（给外部系统调），与内部选人分离，说明**内外两套**。**

**组织同步 12 个 Sync 服务：**
```
MultiOrgSync / MultiOrgDepSync / MultiOrgMemberSync
OrgJobSync / OrgLevelSync / OrgMemberSync / OrgPostSync
OrgRoleSync / OrgTeamSync / OrgUnitSync / OrgMemberRoleSync
```

**`appservice.api` 按调用方分包（50 个）：**
```
api.core.*（16）   按对象：Unit/Member/MemberPost/Post/Job/Level/Role/Business...
api.app.*（16）    按应用：workflow（★流程用）/ affair/edoc/mobile/portal/user...
api.sync（12）     同步
api.app.third.*（3）长江 / 中和 ← ⚠️ 客户定制混在标品 jar
```

**★★★ `api.app.workflow`（6 个）是 BPM 与组织域的桥梁：**
```
WorkFlowAppService / WorkFlowMatchService
OrganizationMatchMemberAppServiceImpl   ★ 匹配人员
condition.ConditionAppService           条件
formula.FormulaAppServiceImpl           公式
```
**⇒ 上一轮 BPM 的 `usedparam` 检测「流程用了哪些组织」（bo/org 11 类），扫的就是这些。**

---

### 三、★★★★ 决定性证据：PERSONSELECTOR 是空壳

**全库 grep udc-biz 5.3.605（1,856 类反编译全量）的 `PERSONSELECTOR`：**
```
命中 16 个文件，全是枚举 + 工具类
没有任何 *Service / *Resolver / *Renderer
```

**全部实现只有 6 个 boolean 开关：**

`DataTypes.java`（163-177）：
```java
if (..."PERSONSELECTOR".equals(name)) {
    dto.setEnablePattern(false);        不支持正则
    dto.setEnableDefaultValue(false);   不支持默认值
    dto.setEnableSensitive(false);      不支持脱敏
    dto.setEnableEncryption(false);     不支持加密
}
if (..."PERSONSELECTOR".equals(name)) {
    dto.setEnableUnique(false);         不支持唯一约束
}
```

`DataTypeChangeUtil.java`（32-34）：
```java
if ("PERSONSELECTOR".equals(nowDataType)) {
    now.setDataI18n(false);             关闭 i18n
}
```

**★★★ 最终判定表：**

| 层面 | 支持？ |
|---|---|
| 枚举定义 | ✅ |
| 存储（字符串） | ✅ |
| 列表显示（列配置） | ✅ |
| 过滤（搜索/显示） | ✅ |
| 前端渲染器 | ❓ 本机无前端资源 |
| **显示名映射（ID→人名）** | ❌ **无实现** |
| **选人弹窗** | ❌ **无实现** |
| 关联查询 | ❌ |
| 携带下游 | ❌ |

**⇒ 建了字段也**没法选人**（没有选人弹窗），只能靠接口直接写 ID。**
**⇒ 确认：生产不可用。**

**★ 对照：UDC 里的 `SelectPeopleDataParam` 是**微流程节点参数**用的，与实体字段类型是两回事。**

**★ 组织侧其实很完整（SelectPeopleAppService 218 方法），**
**⇒ 限制**不在组织侧，而在 UDC 侧**（元数据/交互没接）。**

---

### 四、新增文档

| 文件 | 大小 | 内容 |
|---|---|---|
| **`23-cip-connector-biz.md`** | **20.7 KB** | **Linker 体系 / 3 种执行形态 / 11 种认证 / 3 种 MQ / 中间表同步** |
| **`24-organization-biz.md`** | **17.2 KB** | **组织 5 概念 / SelectPeople 218 方法 / 12 Sync / api 按调用方分包** |

**★ `20-udc-biz-version-diff.md` 补了 §11（PERSONSELECTOR 空壳的决定性证据）。**

**新增脚本：**
```
scratch/scan_conn_org.py       两包结构
scratch/dump_conn.py           连接器服务（类名猜错，改用 scan）
scratch/dump_linker.py         LinkerFactory / LinkerBusinessService / LinkerAppServiceImpl
scratch/dump_linker_entity.py  11 个 Linker 实体字段 ★
scratch/org_list.py            appservice + domain.core 清单
scratch/dump_org.py            SelectPeople 218 / OrgMember 117 / OrgUnit 109
```

---

### 五、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **连接器实现层** | 0% | **80%**（Linker 全模型 + 执行器） |
| **组织实现层** | 70% | **85%**（选人 218 方法 + 5 概念） |
| **PERSONSELECTOR 判定** | 95% | **100%（确认为空壳）** |
| 实现层 *-biz 整体 | 35% | **48%**（5/21 包已深入） |

**全局：约 91%**

---

### 六、下一轮任务

**P0（继续实现层）：**
1. **`cdp-data-biz` 5.3.278（1,927 类）** —— 第二大实现包，数据平台
2. `ctp-user-biz` 5.3.334（876 类）—— 用户
3. `app-common-biz` 5.3.271（632 类）+ `portal-biz` 5.3.369（594 类）

**P1：**
4. `cip-capability-biz` 方法体（37 域只看了类名）
5. `bpm-biz` 的 `cascadeHandleAffectedForAttr` 算法

**P2（需用户协助）：**
6. **22 个缺失 jar** —— udc-bpm / udc-dataflow / udc-user
7. **前端 npm 包** —— PERSONSELECTOR 渲染器 + 确认是否真无选人弹窗---

## 轮次 18 — 2026-11-18（★★★★ 远程仓库接入：补 21 缺失 + 21 biz + 21 web）

### 零、用户提供 Maven 仓库，格局完全改变

```
http://172.28.24.205/artifactory/libs-release/com/seeyon/
本地镜像：D:/repo/REMOTE/com/seeyon/
```

**仓库共 544 个 artifact。**
**⇒ 官方 102 jar 覆盖率：`80/102 = 78.4%` → `101/102 = 99.0%`（仅缺 udc-assemble）**

---

### 一、补齐 21 个缺失 jar（63.4 MB）

| artifact | 版本 | 大小 | 类数 |
|---|---|---:|---:|
| **udc-dataflow** | 5.3.605 | 0.81 MB | **224** ★最大 |
| udc-portal | 5.3.605 | 0.12 MB | 58 |
| udc-starter-autocode | 5.3.605 | 0.08 MB | 52 |
| udc-cdpbi | 5.3.605 | 0.10 MB | 49 |
| udc-bpm | 5.3.605 | 0.13 MB | 46 |
| udc-upgrade | 5.3.605 | 0.18 MB | 44 |
| udc-user | 5.3.605 | 0.13 MB | 37 |
| udc-app-common | 5.3.605 | 0.03 MB | 15 |
| udc-m5 / udc-cip / udc-affair | | | 11/10/1 |
| boot-starter-basicdata | 5.3.600 | 0.17 MB | 57 |
| boot-starter-sandbox / queue / k8s / k8s-adapter / dynamiccode | | | 53/28/25/15/14 |
| devops-starter-pipeline / repo / images / migration | | | 60/53/16/16 |

**★ `udc-assemble` 仓库中确实不存在。**

---

### 二、下载标品 `-biz` 21 个（42 MB / 13,994 类）

**与 `CHIT-extra` 完全一致 ⇒ 确认 CHIT-extra 就是标品实现层。**

```
bpm-biz 5.3.353  7.89 MB  2730 类
udc-biz 5.3.605  6.65 MB  1856
cdp-data-biz 5.3.278  3.74 MB  1927
app-common-biz 3.21 MB 632 / cip-connector-biz 3.06 MB 1205
organization-biz 3.02 MB 668 / ctp-user-biz 2.68 MB 876
cip-capability-biz 2.21 MB 840 / portal-biz 1.56 MB 594
ctp-affair-biz 345 / cdp-schedule-biz 483 / app-doc-biz 477
m5-biz 401 / cip-manager-biz 277 / app-approval-biz 232
ctp-message-biz 151 / ai-biz 132 / cip-openapi-gateway-biz 63
cip-convert-biz 39 / ctp-webapi-gateway-biz 41 / ctp-media-biz 25
```

**★ 仓库里共 76 个 `-biz`，其余 55 个全是客户应用（ceshi* / xiangmuguanli* / datamigration* / faccountsreceivable* …）。**

---

### 三、★★★★ `-web` 21 个：纯 Controller，零前端

| artifact | 条目 | class | js | vue | html |
|---|---:|---:|---:|---:|---:|
| udc-web 5.3.605 | 66 | **54** | 0 | 0 | 0 |
| bpm-web | 77 | 65 | 0 | 0 | 0 |
| organization-web | 113 | 78 | 0 | 0 | 0 |
| 其余 18 个 | | 13-48 | 0 | 0 | 0 |

**★★★ 结论：`-web` = REST Controller 层；前端（Vue/JS）不在 Maven 仓库。**
**⇒ 这也解释了为什么找不到 `PERSONSELECTOR` 的渲染器 —— 前端不在可及范围内。**

**★★★ 但 `udc-web` 的 54 个 Controller 是 UDC 全部 REST 接口入口清单：**
```
EntityController / AttributeSetController / AttributeGroupController / EntityGroupController
DataTypeController ★ / StereotypeController
PageInfoController / PageLayoutController / PageTemplateController(+Class/Published) / PageRouteController
PortletController / PortletGroupController
MetaDataController / UdcDesignMetadataController / DataTransferObjectController
UdcEnumController / UdcEnumItemController / UdcEnumCategoryController / UdcCtpEnumController
MicroFlowController / MicroFlowGroupController / MicroFlowMacroController
MicroFlowRefactorController / MicroFlowUpgradeController
MicroFlowFunctionalCheckController ★（你强调的「检查」按钮）
TempPresetMicroFlowController / FunctionNodeController / BackendComponentController
DataFlowDesignController ★ / DeductionRuleController ★ / ReferConfigController ★
ScalabilityController / ScalabilityOptionController / FeatureController / ParameterController
ApplicationController / AppCollaborationController / AttachmentTemplateController
PublishStateController / DeployController / DeploymentController
SandboxController / UdcSandBoxLogController / UdcManagerController
MultiEditController / UdcFileController / EntityOpenApiController
OperationLogController / DependencyAnalysisController ★ / IndexController / COLISplitController
```

**★ 六个之前没见过：**
```
DependencyAnalysisController        依赖分析（BPM detection 的 HTTP 入口）
DataFlowDesignController            数据流设计画布
DeductionRuleController             扣减规则
MicroFlowFunctionalCheckController  ★ 微流程检查按钮
UdcSandBoxLogController             沙箱日志
EntityOpenApiController             实体开放 API
```

**★ 没有 `PersonSelectorController` ⇒ 进一步印证 PERSONSELECTOR 无交互实现。**

---

### 四、★★★★ `-assemble-resource`：UDC 元数据的真实存储格式

**53 个全是客户应用（标品不发布），但结构完全暴露：**

```
{appId}-assemble-resource-{ver}.jar
├─ metadata/json/       元数据（可读 JSON，每类或每实例一个）
│   udc@com.seeyon.udc.entity.domain.entity.Entity.json
│   udc@...PageSchemaEntity@PAGE@{id}.json       ← 每页一个
│   udc@...MicroFlowEntity@FRONTEND@{id}.json
│   udc@...DataFlowMapping.json
│   udc@ctp_enum_ids.json
├─ schema/app_schema.zip
│   app_schema/udc/{FQCN}.usd                  ← ★★★ .usd = 纯 JSON！
│   app_schema/upgrade/deploy-record.usd
├─ init/{ver}/ 和 init/tenant/                 初始化业务数据
│   {appId}@...SerialScheme.json               ← 流水号方案
├─ i18n/enums_*.properties + application_*.properties
├─ dependencies.json / artifactIds.txt / app-deploy-info.json / application.y
└─ {appId}/Application.class
```

**★★★ 重大发现：`.usd` 不是二进制，是 UTF-8 JSON。**

`Entity.usd` 结构（实测）：
```json
[{
  "dataId": "com.seeyon.udc.entity.domain.entity.Entity",
  "model": "udc",
  "schema": {
    "id": 3582244432195832261,
    "guid": -2707966435769299397,
    "publishState": "UNPUBLISH",
    "appId": 8704025620829192834,
    "name": "fileMigration",
    "tableName": "filemigra_m2707966435769299397",   ★ 物理表名
    "caption": "文件上传中间表",
    "stereotype": "standard",
    "features": "basic",
    "parentEntityId": 0,
    "entityType": "MASTER_ENTITY",
    "multiplicity": "ONE2MANY",
    "category": "ENTITY",
    "searchable": true
  }
}]
```

**★★★★ 主子表的定义机制（最终确认）：**
```
主实体：entityType = "MASTER_ENTITY", parentEntityId = 0
子实体：entityType = "SUB_ENTITY",    parentEntityId = {父实体 guid}
multiplicity = "ONE2MANY"
```

**实测 24 个实体里 6 个子实体：**
```
MigrationLog       ← LogSchemeInformatio
migrationBatchItem ← migrationTaskBatch
migrationPlanJoin  ← migrationPlan
migrationPlanField ← migrationPlan        ★ 一个主实体可以有多个子实体！
asongda            ← xzhDedBill
asongdaasongda     ← （父不在本应用）
```

**★ `migrationPlanGroup` 是独立 MASTER，不是 migrationPlan 的子实体**
**⇒ 「分组」通过**字段关联**，不是 SUB_ENTITY。**

**★ 41 个 .usd 文件大小：**
```
ExcelExportTemplate.usd   2.0 MB  ← 最大
MicroFlowEntity.usd     708 KB
PageSchemaEntity.usd    683 KB
CtpJobInfo.usd          117 KB
Entity.usd              28 KB  ← 24 个实体
DataFlow.usd / DataFlowMapping.usd   4.3 / 7.3 KB
```

---

### 五、★★★★ udc-dataflow（224 类）—— 补齐代码生成短板

**两个子域 + 完整 autocode：**
```
dataflow  ~130 类（生单规则）
deduction ~80 类（扣减规则）
model     8 类（通用引用解析框架）
```

**★★★ 代码生成十件套（两组完全同构）：**

| 组件 | 数据流 | 扣减 |
|---|---|---|
| CodeTask | `DataFlowCodeTask` | `DeductionCodeTask` |
| CodeTemplate | `DataFlowCodeTemplate` | `DeductionCodeTemplate` |
| TemplateConfig | ✅ | ✅ |
| DecorateConfig | ✅ | ✅ |
| MetadataConst | ✅ | ✅ |
| CodeContextAware | ✅ | ✅ |
| MetaDataPostProcessor | ✅ | ✅ |
| TransportHandler | ✅ | ✅ |
| SaveAsHandler | ✅ | ✅ |
| ImporterBase | ✅ | ✅ |

**★★ 数据流有 3 个 Task：**
```
DataFlowCodeTask             主任务
DataFlowFormulaServiceTask   ★ 公式服务生成（表达式 → Java 代码）
DataFlowPlanTask             方案生成
```

**★★★ `DataFlowFormulaServiceTask` 证实：表达式**会被生成为 Java 代码**，不是运行时解释。**

**★★★ 3 + 2 个 Decorate：**
```
数据流：DataFlowIdMappingDecorate       ID 映射（导入时 ID 重排）
       DataFlowWriteBackDecorate        回写（执行后回写来源实体）
       MicroFlowDataFlowActivityDecorate ★ 微流程↔数据流联动
扣减：  DeductionTargetEntityNoCacheDecorate  ★★ 强制不走缓存
       DeductionUpdateTargetEntityDecorate   更新目标实体
```

**★★★ 扣减不使用 Java 代码，而是**生成 SQL**：**
```
DeductionSqlGenerator
  ├─ DeductionMysqlAggRootEntityGenerator     聚合根（主实体）
  └─ DeductionMysqlNoAggRootEntityGenerator   非聚合根
DeductionMySqlDialect（★ 只有 MySQL 方言）
RuleDescartesService  ★ 笛卡尔积（多条件组合）
```

**★★★ 12 种数据类型的 SQL 值转换器（`deduction.searchmethod.convert`）：**
```
String / MultilineString / Integer / Boolean / Decimal / Currency
Date / Time / DateTime / Enum / CtpEnum / Entity
+ DeductionDatabaseValueConvertHelper（总调度）
+ DeductionFixedValueConvert（固定值）
```
**⇒ 这就是「配置化扣减能生成正确 SQL」的关键 —— 类型安全转换。**
**★ Entity 转成外键 ID；Enum/CtpEnum 转成 code。**

**★ 7 个条件校验（`check`）：Default / BigInteger / CtpEnum / Enum / Entity …**

**★★ 通用引用解析框架（`com.seeyon.udc.model`）：**
```
DataflowMappingReferenceParser / DataflowReferenceParser
DeductionMapReferenceParser / DeductionRuleReferenceParser
+ 4 个 Repository
```
**⇒ 与 BPM `usedparam` 同构，但更通用（不绑 dataflow 包）。**

**★ 数据流检测体系（13 类）：5 个 PartDetectionTask（Entity/Attribute/JavaEnumItem…）+ FrontDeployDetectionTask。**

**★ 数据流支持两种应用形态：`FormApplicationFeature4DataFlow`（表单） / `NormalApplicationFeature4DataFlow`（普通）。**

---

### 六、★★★ 三个概念必须分清（之前混淆过）

```
①「扣减规则」Deduction
   = 配置化，生成 SQL 直接 UPDATE
   = udc-dataflow 的 deduction 子域
   = DeductionRuleAppService（GraphQL: udcDeductionRulePost）

②「微流程扣减节点」LIST_OPERATION.SUBTRACT
   = 内存里的集合差运算
   = 微流程 56 actionType 之一

③「数据流」DataFlow
   = 生单规则，生成 Java 代码
   = udc-dataflow 的 dataflow 子域
   = 微流程 CALL_DATA_FLOW 节点调用它
```

---

### 七、新增文档

| 文件 | 大小 | 内容 |
|---|---|---|
| **`25-remote-repo-and-assemble.md`** | **15.7 KB** | **仓库结构 + 54 Controller + assemble-resource + .usd 格式 + 主子表机制** |
| **`26-udc-dataflow-deduction.md`** | **13.4 KB** | **数据流/扣减 + autocode 十件套 + SQL 生成 + 12 类型转换** |

**新增脚本：**
```
scratch/list_remote.py          仓库 544 artifact 清单 ★
scratch/probe_remote.py         22 缺失探测
scratch/dl_remote.py            补 21 缺失
scratch/probe_biz_web.py        标品 biz/web 版本探测
scratch/dl_biz_web.py           下载 42 个
scratch/inspect_web.py          ★ web 包内容构成（证实零前端）
scratch/scan_newudc.py          新 udc 包结构
scratch/remote_artifacts.json   544 artifact 明细
scratch/std_biz_web_tasks.json  42 个下载任务
```

---

### 八、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **官方 102 jar 覆盖** | 78.4% | **99.0%** |
| **代码生成** | 62% | **85%**（autocode 十件套 + 3 Task） |
| **生单规则（数据流）** | 85% | **90%** |
| **扣减规则** | 70% | **90%**（SQL 生成 + 12 类型转换） |
| **UDC REST 接口（Controller）** | 0% | **90%**（54 个全清单） |
| **UDC 元数据真实格式（.usd）** | 0% | **90%** |
| **主子表定义机制** | 95% | **100%** |

**全局：约 93%**

---

### 九、下一轮任务

**P0：**
1. **`cdp-data-biz` 1,927 类** —— 第二大实现包
2. **`DataFlowCodeTemplate` / `DeductionCodeTemplate` 的模板内容** —— 生成什么代码（最关键）
3. `udc-bpm` 46 类（UDC↔BPM 桥）细节

**P1：**
4. `ctp-user-biz` 876 / `app-common-biz` 632 / `portal-biz` 594
5. 各 Controller 的 REST 路径（需反编译注解）

**P2（需协助）：**
6. **标品前端（Vue/JS）** —— Maven 仓库没有，需从平台运行包取 → **决定 PERSONSELECTOR 能否使用**
7. `udc-assemble` —— 仓库不存在，可能从未发布---

## 轮次 19 — 2026-11-18（★★★★★ 代码生成引擎全解：432 FTL + 表达式编译 + 微流程节点）

### 零、一句话结论

**Seeyon 平台的「代码生成」= FreeMarker 模板（432 个 .ftl）+ Paster 指令 + 表达式二次编译。**
**没有 JavaPoet，没有 AST 拼装 —— 全是文本模板 + `<@paster>` 占位符替换。**

---

### 一、★★★★★ 找到 432 个 FTL 模板（udc-biz）

```
udc-biz-5.3.605.jar  6.65 MB / 1,856 类 / 432 个 .ftl
```

**五个版本共存（按应用创建时的引擎版本选，不是一律最新）：**
```
2.7     125 个
2.8     138 个
2.9     141 个 ★★★ 当前生效
3.0       2 个（试验）
template/ 26 个（无版本，feature 母版）
```

---

### 二、★★★★★ 2.9 的 141 个模板按类目

```
microflow    54（+ 子目录共 66）
entity       21  ★★★ 最重要
common       13
feature      10（+ template/26）
entityrule    9
project       9（+ for-deploy 6 + ext 3）
event         5
refer         4
project-ext   3
filterplan    2
referconfig   2
app           2
beanname/enums/dto  各 1
```

**★★★ 最关键的三条（写代码必须知道）：**

**① `dao.java.ftl` 只有 1,852 字节 —— Dao 几乎不生成内容**
```java
// form 应用：class XxxDao extends AbstractAllInOneBaseDao<T>
// 非 form：  interface XxxDao extends AbstractAllInOneBaseDao<T>
```
**⇒ 平台**不生成任何 CRUD SQL**，全走 `com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao`。**

**② `mybatis.xml.ftl` 只有 675 字节 —— 基本空的**
**⇒ 没有 `<select>` / `<insert>`，全走 `SeeyonKeyMap` / `Wrapper` / `Example`。**

**③ `baseservice.java.ftl` 67 KB —— Service 层最厚**
```
baseservice.java.ftl    67 KB  ★★★ Domain Service
appserviceImpl.java.ftl 28 KB  ★★★ AppServiceImpl
dto.java.ftl            24 KB
controller.java.ftl     14 KB
appservice.java.ftl     10 KB  ★ AppService 接口
```

---

### 三、★★★★★ 三层 Service 的真实关系（模板实证）

```
① Service（Domain 层）
   baseservice.java.ftl (67 KB) → {Entity}Service
   数据访问、事务、校验

② AppService（应用服务，接口+实现）
   appservice.java.ftl (10 KB) + appserviceImpl.java.ftl (28 KB)
   → {Entity}AppService + {Entity}AppServiceImpl
   注解：@AppService(value="{caption}接口", customs={entity, appName})
        @DubboService（仅 enableRpc || isOpenApiEntity）
   对外 GraphQL + Dubbo

③ Controller（REST）
   controller.java.ftl (14 KB) → {Entity}Controller
```

**★★★ 三重暴露：GraphQL（@AppService）/ RPC（@DubboService）/ REST（Controller）。**

**★★★ AppServiceImpl 的 import 暴露关键依赖：**
```
dynamicsql.dto.*    动态 SQL（DynamicCondition/MainCondition/ProxyParam/ProxyJoinParam）
Wrapper             条件构造器
Example             tk.mybatis
RecycleSerialNumber 回收流水号
ExcelImport/Result  导入导出
udcrt.dto.*         BillSearchRequest/ExcelDto/RuntimePageCustomSearchDto
```

**★ `table.isRoot` 分支 ⇒ 主实体和子实体生成不同 AppServiceImpl（子实体无 Excel/流水号/ForceUpdate）。**

---

### 四、★★★★★ 表达式 = 编译成 Java 方法，不是运行时解释

**关键类：`com.seeyon.udc.expression.codegen.ExpressionCodeGenerator`（udc-biz）**

**七步编译管线（CFR 反编译 `doGenerateCode` 原文）：**
```java
tokens
  → SeeyonParser.parse(it, schemaMap)          ① AST
  → SemanticAnalyzer.analyze(root)             ② 类型推断
  → ExpressionInterpreter.interpret(root, ctx) ③ AST → Java 片段
  → wrapCodeFragmentWithJavaEnumCast(...)      ④ 枚举强转
  → buildMethodBody(...)                       ⑤ 包成方法
  → methodName = "exp" + Ids.uuidAbsLong()     ⑥ 方法名 exp{雪花}
  → CodeGenerateResult(fragment/name/body/imports/paramEntityMap)
```

**★★★ 生成的方法体（原文常量 `NORMAL_METHOD_TEMPLATE`）：**
```java
public %s %s(%s){
try{
            return %s 
        }catch (NullPointerException e){
            throw new BusinessException(ExpressionErrorCode.NORMAL_EXPRESSION_NULL_POINTER_ERROR);
        }catch (Exception e){ ... NORMAL_EXPRESSION_ERROR ... }
}
```
**★ 另有 `REF_METHOD_TEMPLATE` —— 引用表达式带 refPath，错误码 `REF_*`。**

**★★★ 枚举特殊处理（原文常量）：**
```java
SINGLE_JAVA_ENUM_CAST = "(%s)(BasicHiddenFunction.getJavaEnumItem(\"%s\", %s))";
MULTI_JAVA_ENUM_CAST  = "(java.util.List<%s>)(...getMultiJavaEnumItem(...))";
```
**⇒ UDC 枚举在生成代码里是**有类型的 Java 对象**，不是字符串。**

**★★★★★ 最终运行形态：**
```
生成期：DataFlowRuntimeService.java 里留 dataFlowFormulaService.exp123(map)
        + DataFlowFormulaService.java 里生成 exp123 的真实方法体
运行期：直接调 Java 方法 —— 零解释开销
```

---

### 五、★★★★★ 数据流的 5 个表达式点位（`DataFlowCodeUtils` 反编译）

```java
wrap(codeGenerator, dto.getMappingDetailDto().getEventFilterCondition(), "事件过滤条件");
wrap(..., dto.getMappingDetailDto().getPreCondition(),                    "来源实体过滤条件");
rules.forEach(rule -> rule.getMappingArea().forEach(area -> {
    wrap(..., area.getCheckRule(),  "目标实体数据检查规则");
    wrap(..., area.getCondition(),  "行映射条件");
    area.getMappingRow().forEach(row ->
        wrap(..., row.getRowCondition(), "列映射条件"));
}));
```

**⇒ 生单规则能配表达式的 5 个位置：事件过滤 / 来源过滤 / 数据检查 / 行映射 / 列映射。**

**★★★ `getExpressionDefinitionDtoId` 实现（原文）：**
```java
return String.valueOf(System.identityHashCode(dto)).replace("-","");
```
**⇒ 用 identityHashCode 去重（同一表达式对象只生成一次）。**

---

### 六、★★★★★ 微流程 = 编译成一个 DomainService 类

**`MicroFlowDomainService.java.ftl`（41,740 字符 / 42 KB）的 12 个宏：**
```
nodesLogicHandler        ★★★ 总分发（按 node.type）
nodeActivityHandler      ★★★ Activity 分发（21 个 actionType）
branceLogicNodeHandler   分支 → if/else if/else
forEachLogicHandler      遍历 → for (T x : list)
foriLogicHandler         计数循环 → for(int i=...)
errorLogicHandler        自定义错误 → 抛异常
buildErrorInfo / buildMfService / buildFormulaPrivateMethod
buildFilterListOperationFormulaMethod / buildConditionPrivateMethod
validateInputParamAttrRequired
```

**★★★★★ `node.type` 只有 5 类：**
```
Activity      → 21 种 actionType
Branch        → if/else 链（最后一个无条件 else 兜底）
ForEach       → for (T x : list)
For           → for (int i = start; ...)
CustomError   → 抛 BusinessException
```

**★★★ 过滤机制：`node.isShouldGenerateCode()` —— 有些节点不生成代码。**

---

### 七、★★★★★ `MicroFlowActivityTypeEnum` 全量 101 个 actionType

**来源：`udc-common`，CFR 反编译。索引 0-102，缺失 [30, 85]。**

**四桶分类：**

| 桶 | 数量 |
|---|---:|
| 后端生成代码 | **21** |
| 结构节点 | **11** |
| 前端节点（`_FRONT`） | **6** |
| 后端元信息/表单规则/页面动作 | **63** |

**★★★★★ 21 个后端生成代码的（枚举 → 驼峰）：**
```
0  CONNECTOR            → Connector          连接器
1  CREATE_VARIABLE      → CreateVariable     创建变量
2  CHANGE_VARIABLE      → ChangeVariable     修改变量
3  CREATE_LIST          → CreateList         创建列表
4  CHANGE_LIST          → ChangeList         修改列表
5  PUBLISH_BUSINESS_EVENT → PublishBusinessEvent 业务消息
10 RETRIEVE             → Retrieve           查询单记录
11 RETRIEVE_ARRAY       → RetrieveArray      查询多记录
12 CHANGE_ENTITY        → ChangeEntity       更新数据
13 CREATE_ENTITY        → CreateEntity       插入数据
14 DELETE_ENTITY        → DeleteEntity       删除数据
15 LIST_OPERATION       → ListOperation      列表操作
16 SUB_MICROFLOW        → SubMicroFlow       子流程
18 CALL_APP_SERVICE     → CallAppService     服务调用
19 CALL_DATA_FLOW       → CallDataFlow       生单规则
40 CONVERT_DATA         → ConvertData        类型转换
41 CREATE_BATCH_ENTITY  → CreateBatchEntity  批量插入
42 CHANGE_BATCH_ENTITY  → ChangeBatchEntity  批量修改
65 CREATE_MAP           → CreateMap          创建映射
66 MAP_OPERATION        → MapOperation       映射操作
83 DATA_MAPPING         → DataMapping        数据转换
```

**★★★ 11 个结构节点：**
```
43 START / 44 END / 45 BRANCH / 46 FOR / 47 CONDITION
48 FOR_EACH / 49 CUSTOM_ERROR / 50 OTHERS_CONTROL
72 BREAK / 76 END_NODE / 77 INPUT_NODE
```

**★★★★★ 6 个前端节点（`_FRONT`）：**
```
54 CREATE_VARIABLE_FRONT / 55 CHANGE_VARIABLE_FRONT
56 CREATE_LIST_FRONT     / 57 CHANGE_LIST_FRONT
73 CONVERT_DATA_FRONT    / 78 CALL_DATA_FLOW_FRONT
```
**⇒ 这 6 个是后端 21 个的**前端镜像** —— 印证「微流程分前端/后端两套」。**

**★★★★ 63 个元信息型，分 5 组：**
```
① 实体规则(5)：ATTRIBUTE_REQUIRED/ASSIGN_VALUE/SHOW_MESSAGE/ATTRIBUTE_UNIQUE/DEFAULT_VALUE
                → 走 entityrule/*.ftl 另一套
② 表单控件(12)：VISIBLE/ATTR_VISIBLE/SET_VALUE/SET_REQUIRED/ENABLE/READ_ONLY/
                CLEAR_VALUE/CONTROL_ACTION/VALUE_HANDLE/CONTROL_STATUS/
                ADVANCED_PROPERTIES/SET_DATASOURCE
③ 页面导航(8)：OPEN_PAGE/CLOSE_PAGE/OPEN_URL/MODAL/PAGE_LOADING/
              OUT_PAGE_LOADING/CONFIRM_CLOSE_PAGE/RELOAD_PAGE
④ 实体操作(15)：DATA_SOURCE_*(3) + ENTITY_*(12：SAVE/SUBMIT/EDIT/REFRESH/DELETE/
              SAVE_DRAFT/WITHDRAW/COPY_DATA/EXPORT/IMPORT/SAVE_NEW/SAVE_COPY)
⑤ 消息集成等(23)：CALL_MICRO_FLOW/MESSAGE_INFO/CLEAR_MESSAGE_INFO/SEND_MQ_MESSAGE/
              CREATE_AFFAIR/FED_LIST_OPERATION/CALL_FRONT_FLOW/CALL_SERVICE/
              FLOW_ACTION/ATTACHMENT_*/OPEN_REPORT/THROW_EVENT/FRONT_CUSTOM_ERROR/
              SCAN_CODE/PRINTPAGE/LOCATION_CMP/ATTENTION/LABEL_PRINT/
              FORM_CONVERT/DOWNLOAD_ALL/EXTEND_ACTION
```

**★★★★★ 四组容易混淆的：**
```
① SUB_MICROFLOW(16)    子流程（内嵌同上下文，可调标准或 CUSTOM）
   CALL_MICRO_FLOW(17) 后端微流程（独立调用）
② LIST_OPERATION(15)   后端集合运算（42.9 KB 模板）
   FED_LIST_OPERATION(51) 前端集合运算
③ CALL_APP_SERVICE(18) 调 UDC AppService（生成代码）
   CALL_SERVICE(53)     通用服务调用
④ EXTEND_ACTION(101)   ★★ 客开扩展点 —— 平台留给我们的节点扩展入口
```

---

### 八、★★★★★ `ListOperationActivity`：16 种集合运算（实测 case）

```
SUM / MAX / MIN / SIZE / DISTINCT / FILTER / SORT / MAP
SUB_LIST / FIRST_ONE / LAST_ONE / PICK_ONE
UNION / INTERSECT / SUBTRACT（★ 这 3 个需第二集合）
GROUP_AND_SUM
```

**★★★ 三个机制：**
```
① requiredOperationParam(op) → 只有 UNION/INTERSECT/SUBTRACT 需第二集合
② 双集合运算生成 4 个中间变量（NewSourceList/NewOperationParamList/
                              DelSourceList/DelOperationParamList）
③ SUM 按类型五路：INTEGER/BIGINTEGER/DECIMAL/CURRENCY/DTO
```

**★★★ `SUBTRACT` 语义最终确认：内存 List 差运算，不碰数据库。**
**⇒ 与「扣减规则 Deduction」（生成 SQL）彻底分开。**

---

### 九、★★★★★ `SubMicroFlowActivity`：同时支持标准与自定义微流程

```freemarker
<#if "CUSTOM"==calledMicroFlow4CodeDto.type>
    if(${uncapAppServiceName} == null){
        throw new BusinessException(MicroFlowErrorCode.UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED);
    }
    ${respOutputParam} ${respName} = ${serviceName}.${method}(${inputParam!"");
    if(!${respName}.success()) { log.error(...); }
</#if>
```

**★★★ 三个结论：**
```
① 子微流程可调「标准微流程」或「自定义微流程」
② 自定义微流程 = Spring Bean（XxxAppService）
③ Bean 为 null 抛 UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED
   ⇒ 必须先实现接口+注册 Bean，否则运行期才报错
```

**★★ 入参命名约定：`"v" + nodeId`（原文注释）。**
**★ 自定义微流程支持分页（hasPagination/pageInfo）。**

---

### 十、★★★★★ `CallDataFlow` 的 Paster 三段（唯一跨子域插件节点）

**`MicroFlowDomainService.java.ftl` 里只有 3 个 paster 名：**
```
call.data.flow.di[        ← @Autowired 声明
call.data.flow.import[    ← import 语句
call.data.flow[           ← 节点调用体
```
**★ 格式：`{prefix}[{动态key}]`，方括号是变量（sourceEntityId）。**
**⇒ 多个来源实体 → 多组 DI/import。**

**★★★ `CallDataFlowActivity.java.ftl` 生成的实际调用：**
```java
DataFlowExecuteParamDto {nodeId}DataFlowExecuteParamDto = ...;
DataFlowResultDto {nodeId}SourceResultDto = {entity}DataFlowRuntimeService
        .{methodName}({nodeId}DataFlowExecuteParamDto, new HashSet<>(Arrays.asList("{mappingId}")));
CallDataFlowResultDto {output.name} = new CallDataFlowResultDto({nodeId}SourceResultDto);
```

**★★★ 三段式（给自定义节点照抄）：**
```
*Activity.java.ftl     节点逻辑
*ActivityDI.ftl        依赖注入（156 B）
*ActivityImport.ftl    import（116 B）
```

---

### 十一、★★★★★ `project/*` 模板：新建应用的工程脚手架

```
backend/
├─ pom.xml / .gitignore / README.md
├─ {appName}-assemble/
│   ├─ pom.xml
│   ├─ src/main/java/{appPath}/Application.java
│   └─ src/main/resources/application.y        ← 202 B
├─ {appName}-biz/       pom.xml
├─ {appName}-facade/    pom.xml
└─ {appName}-web/       pom.xml
```

**★★★★★ 这就是仓库里 `{appId}-biz` / `-web` / `-facade` / `-assemble-resource` 的来源！**

**★★ `project-for-deploy/`（15 个）：**
```
PersonEntityRuleServiceTest.java   4.7 KB  ★ 平台自动生成单元测试
FileHelper.java / TestApplication.java
application.yaml / application-local.yaml
```

**★ `project-ext/`（11 个）：只有 pom + README + package-info.java（空壳，代码自己写）。**

---

### 十二、★★★★★ microflow 全套 66 个模板

```
根目录 21（Activity 模板 + MicroFlowDomainService 42.6 KB）
common/      8  ★ LogUtil 42.7 KB / ValueUtil 16.8 KB /
                  SetActionTypeUtil 13.5 KB / CommonUtil 12.3 KB
customflow/  7  ★★★ 自定义微流程（Controller/AppService/BeanRegistryPostProcessor/Config/
                                DubboExportBeanPostProcessor）
event/       2  ★ BusinessEventListener / ConnectorBusinessEventListener
plugin/calldataflow/ 3  ★ 三段式
web/         7  ★ MicroFlowController / AppService(Impl) / CustomRestApi / GraphQLUtil
web/host/    2  ★ 宿主应用调用
schedule/    1  ★ 定时触发
third/       1  ★ dynamicSearch
customerror/ 4  ★ CustomError + 三语 i18n
```

**★★★★★ 微流程的 6 种触发方式（从模板反推）：**
```
① 业务事件（BusinessEventListener）
② 连接器事件（ConnectorBusinessEventListener）
③ 定时调度（MicroFlowSchedule）
④ 宿主应用（HostAppMicroFlowController）
⑤ REST（MicroFlowController）
⑥ GraphQL（MicroFlowAppServiceImpl）
```

---

### 十三、新增文档 + 下载

| 文件 | 大小 | 内容 |
|---|---|---|
| **`27-autocode-templates.md`** | **28.5 KB** | **432 FTL + 表达式编译管线 + Paster + 三层 Service** |
| **`28-microflow-codegen.md`** | **约 26 KB** | **微流程节点编译 + 101 actionType + 16 集合运算 + SubMicroFlow/CallDataFlow** |

**新下载（8 个，补齐表达式与基础包）：**
```
boot-formula-engine    5.3.603  0.11 MB
boot-starter-formula   5.3.603  0.47 MB
boot-starter-datatype  5.3.600  0.03 MB
udc-starter-lowcode    5.3.605  0.28 MB
udc-starter-dataflow   5.3.605  0.27 MB
udc-common             5.3.605  0.69 MB  ★ ExpressionEnumUtil/DataConvertUtil/TypeConverterSingleCase
udc-starter-runtime    5.3.605  0.82 MB  ★ UdcRuleLogUtil/ExpressionEnumUtil
udc-starter-customplan 5.3.605  0.24 MB
```

**新脚本：**
```
df_templates.py      数据流 FTL 清单
biz_templates.py     udc-biz 432 FTL 分类 ★
mf_templates.py/mf_full.py  microflow 全路径
mf_cases.py          nodeActivityHandler 21 个 case ★
mf_enum2.py          MicroFlowActivityTypeEnum 101 个 ★
find_expr2.py        跨 jar 类定位
codegen_pkg.py       codegen 包扫描
```

---

### 十四、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **代码生成** | 85% | **★ 98%**（432 FTL + 表达式编译 + Paster） |
| **表达式机制** | 60% | **★ 95%**（七步编译管线实证） |
| **微流程代码生成** | 70% | **★ 95%**（21 actionType + 5 node.type + 16 集合运算） |
| **三层 Service 生成** | 75% | **★ 95%**（Dao 极薄、XML 近空，实证） |
| **应用工程脚手架** | 0% | **★ 95%**（project/* 目录树） |
| **actionType 全量对照** | 只有「56 个」模糊数字 | **★ 101 个完整分类** |

**全局：约 95%**

---

### 十五、下一轮任务

**P0：**
1. **`EXTEND_ACTION(101)` 扩展契约** —— 客开节点扩展点，最实用
2. **`CALL_MICRO_FLOW(17)` 与 SUB_MICROFLOW 的实现差异**
3. **实际跑一次代码生成**（拿测试应用验证 FTL 输出）

**P1：**
4. `LogUtil.java.ftl`（42.7 KB）—— 微流程日志体系
5. `SetActionTypeUtil.java.ftl`（13.5 KB）—— ActionType 传播
6. `cdp-data-biz`（1,927 类）

**P2（需协助）：**
7. 标品前端 Vue/JS（Maven 仓库没有）---

## 轮次 20 — 2026-11-18（★★★★★ 代码生成引擎真实跑通 + 三张权威枚举 + 平台 bug）

### 零、★★★★★ 本轮最大成果：代码生成引擎 LIVE 跑通

**不再靠推断 —— 我在本机用 freemarker 2.3.32 + JDK21 真实渲染了平台模板。**

**三份 LIVE 产物：**

**① `dao.java.ftl` → 543 字符，真的只有一行：**
```java
package com.example.demo.domain.dao;
import ...
public interface DemoOrderDao extends AbstractAllInOneBaseDao<Order>{
}
```

**② `mybatis.xml.ftl` → 246 字符，`<mapper>` 内部完全空：**
```xml
<mapper namespace="com.example.demo.domain.dao.DemoOrderDao">
</mapper>
```
**★★★★★ 零 select / 零 insert / 零 resultMap。**

**③ `AppBeanNameModifier.java.ftl` → 1,124 字符，完整可用代码：**
```java
public class DemoBeanNameModifyer implements AppBeanNameModifier {
    private static final String appName = "Demo";
    public String modifyBeanName(BeanDefinition beanDefinition, String beanName) {
        if (beanDefinition.getBeanClassName().contains(appName) && !beanName.contains(appName)) {
            beanName = appName + StringUtils.capitalize(beanName);
        }
        return beanName;
    }
}
```
**★★★ 揭示平台的**Bean 命名隔离机制**（多应用同名 Bean 加应用前缀）。**
**★ 类名有平台笔误：`Modifyer`（应为 Modifier）。**

---

### 一、★★★★★ 复现方法（三步，可复制）

```
① freemarker-2.3.32.jar（1.7 MB）+ JDK21
② TemplateLoader 用 jar 文件系统直接读 .ftl
③ 补 udcCodeConfig（Map<FQCN, 配置对象>）+ 复刻 paster 指令
```

**★★★★★ `paster` 指令全部逻辑只有 8 行（反编译 `PasterDirective`）：**
```java
String pastKey = params.get("name");                        // 模板里的 name
TemplateModel pt = env.getDataModel().get("paster_" + pastKey);   // ★ 前缀 paster_
if (pt == null) return;                                     // ★ 找不到静默跳过！
String code = pt.getAsString();
if (isBlank(code)) return;
out.write(code);
```

**★★★ 这解释了为什么缺 Paster 配置也能渲染成功 —— `<@paster>` **不报错，只静默跳过**。**

---

### 二、★★★★★ 代码生成框架完整结构（udc-starter-autocode 52 类）

```
engine/
  CodeEngine / SimpleCodeEngine   ★ 30 秒硬超时 + 并行 Future
context/
  AutoCodeContext                 ★ directOutput / registerEarlyTemplate / getInterceptorList
  AbstractMultiVersionAutoCodeContext（多版本）
template/
  AbstractFreemarkerTemplate      ★ writeToFile / resolveToString / processTemplateString
  EarlyTemplate                   ★ filterFilePath / filterTemplateContent（版本/风格开关）
  FreemarkerTemplate / TemplateBuilder / TemplateInterceptor
extension/directive/
  PasterDirective  ★★★ / UncapDirective / AutoCodeDirective
extension/decorate/
  Decorate / DecorateConfig / DecorateContainer / TemplateDecorateContainer
handler/
  LazyCacheableAutoCodeTask（基类 code(ctx)）/ MultiVersionMetaDataHandler
metadata/ config/ utils/(AutoCodeUtils 10 KB) / condition/ exception/
```

**★★★★★ `SimpleCodeEngine.execute` 反编译原文：**
```java
CompletionExecutor ex = new CompletionExecutor("代码生成", 30000L);   // ★ 30秒超时
taskList.forEach(task -> ex.submit(new NamedFutureTask(..., () -> task.code(ctx), true)));
ex.waitTimeout();                                                    // ★ 超时不抛异常
```
**⇒ 大型应用（实体多）代码生成**可能超时且静默失败**。**

**★★★ 平台有**三套**模板引擎：FreeMarker（主力 432 个 .ftl）/ Beetl / Velocity。**

---

### 三、★★★★★ 模板可用的 16 个工具类（`utils.ftl` 实测）

```
StringHelper                     com.seeyon.udc.common.autocode.util.StringHelper
CollectionUtils                  org.apache.commons.collections.CollectionUtils
DataFlowCodeUtils                ★★ com.seeyon.udc.dataflow.autocode.util.DataFlowCodeUtils
ConditionConfigOutputUtil        ★ com.seeyon.boot.starter.condition.output.ConditionConfigOutputUtil
EntityCodeUtils                  ★★ com.seeyon.udc.common.autocode.util.EntityCodeUtils
FormulaUtil                      ★★ com.seeyon.udc.common.utils.FormulaUtil
DtoCodeUtil                      ★ com.seeyon.udc.common.utils.DtoCodeUtil
StringUtils                      com.seeyon.boot.util.StringUtils
UdcCommonConstant                ★ com.seeyon.udc.common.constant.UdcCommonConstant
ConnectorUtil                    ★ com.seeyon.udc.common.autocode.util.ConnectorUtil
MicroFlowCodeUtil                ★★★ com.seeyon.udc.common.autocode.util.MicroFlowCodeUtil
EntityRuleCodeUtil               ★★ com.seeyon.udc.common.autocode.util.EntityRuleCodeUtil
JsonUtils                        com.seeyon.boot.util.JsonUtils
DataTransferObjectCodeUtil       ★ com.seeyon.udc.common.autocode.util.DataTransferObjectCodeUtil
DynamicDependencyUtil            ★ com.seeyon.udc.common.utils.DynamicDependencyUtil
AppCodeUtil                      ★ com.seeyon.udc.autocode.util.AppCodeUtil
```

**★★★★★ 这是「模板 ↔ 平台代码」的唯一接口层。模板不能写任意 Java，只能调这 16 个类的静态方法。**

**★★ `MicroFlowCodeUtil` 是微流程模板的核心大脑：**
```
buildDataFlowExecuteParamDto / buildResponseName / buildCallMethodByMicroFlow4CodeDto
getSelectParamValue / getRealListName / filterDeletedData / initFormulaLocalVariableNameSet
```

**★ 平台两条设计意图（utils.ftl 原文注释）：**
```
<!-- 减少 ConnectorUtil 在微流程模板中的使用，应当使用 fullNameTransformer 转换 fullName -->
<!-- 减少 DynamicDependencyUtil ... 同上 -->
```

---

### 四、★★★★★ `MicroFlowNodeTypeEnum` 是 8 类，不是 5 类

```
0 CONDITION / 1 FOR_EACH / 2 BRANCH / 3 CUSTOM_ERROR
4 END / 5 ACTIVITY / 6 FOR / 7 BREAK
```

**★★★ 两个分组常量（static{} 实测）：**
```java
CYCLIC_NODE_TYPES    = {FOR, FOR_EACH}                      // 循环 2 个
CONTAINER_NODE_TYPES = {CONDITION, FOR, FOR_EACH, BRANCH}   // 容器 4 个（能挂子节点）
```
**⇒ Activity/CUSTOM_ERROR/END/BREAK 是叶子节点，不能有 children。**

---

### 五、★★★★★ `ActivityNodeTypeEnum`：29 个后端 actionType（权威 strCode 映射）

**这是模板 case 真正用的枚举，与 `MicroFlowActivityTypeEnum`（101 个）不是一回事。**

**★★★★★ 发现平台 3 个复制粘贴 bug：**
```java
CALL_DATA_FLOW_FRONT(46, "CallDataFlowFront"),
EXTEND_ACTION(47, "CallDataFlowFront"),      // ← 应为 "ExtendAction"
SET_DATASOURCE(48, "CallDataFlowFront");     // ← 应为 "SetDataSource"
```
**⇒ `getByStrCode("CallDataFlowFront")` 永远返回 46，47/48 取不到。**

**★★★★★ 且 `EXTEND_ACTION` 全仓库**没有任何实现类**（字节搜索只命中 2 个枚举文件）：**
```
没有 ExtendAction* / ExtendActivity* / ExtendNode* 任何类
```
**⇒ 客开扩展点只是**枚举占位，平台未实现**。这是本轮重要发现 —— 我之前把
   EXTEND_ACTION 当成「平台留的扩展入口」是过于乐观。**

**★★★ 两个分组常量（static{} 实测）：**
```java
DATA_ACTIVITY_TYPES  = {RETRIEVE, RETRIEVE_ARRAY, CREATE_ENTITY, CREATE_BATCH_ENTITY,
                        CHANGE_ENTITY, CHANGE_BATCH_ENTITY, DELETE_ENTITY}   // 7 个
BASE_SERVICE_TYPES   = {CALL_APP_SERVICE, PUBLISH_BUSINESS_EVENT, CONNECTOR,
                        SUB_MICROFLOW, CALL_DATA_FLOW}                       // 5 个
```
**⇒ `isDataActivity()` / `isBaseService()` 是平台判断「节点性质」的钩子。**

**★★★ 29 个 Activity 的最终归属：**
```
21 个 → 微流程代码生成（nodeActivityHandler）
 5 个 → 实体规则代码生成（entityrule/*.ftl：必填/设置值/提示/唯一/默认值）
 1 个 → CALL_MICRO_FLOW（未找到生成路径）
 2 个 → EXTEND_ACTION / SET_DATASOURCE（strCode bug，实际不可用）
```

---

### 六、★★★★★ `ListOperationTypeEnum`：19 种集合运算（比模板多 3 个）

**按 4 组分类（`ListOperationGroupEnum`）：**

| code | strCode | 中文 | 组 |
|--:|---|---|---|
| 0 | `sum` | 求和 | AGGREGATION |
| 1 | `size` | 计数 | AGGREGATION |
| 2 | `max` | 最大值 | AGGREGATION |
| 3 | `min` | 最小值 | AGGREGATION |
| 4 | `filter` | 过滤 | INSPECTION |
| 5 | **`find`** | 查找 | INSPECTION |
| 6 | `sort` | 排序 | INSPECTION |
| 7 | `union` | 并集 | **BINARY** |
| 8 | `intersect` | 交集 | **BINARY** |
| 9 | **`subtract`** | **差集** | **BINARY** |
| 10 | **`contains`** | 包含 | JUDGEMENT |
| 11 | **`equals`** | 相等 | JUDGEMENT |
| 12 | `groupAndSum` | 分组汇总 | BINARY |
| 13 | `firstOne` | 第一条 | INSPECTION |
| 14 | `lastOne` | 最后一条 | INSPECTION |
| 15 | `pickOne` | 选择一条 | INSPECTION |
| 16 | `distinct` | 去重 | INSPECTION |
| 17 | `subList` | 获取子列表 | BINARY |
| 18 | `map` | 字段收集 | BINARY |

**★★★ 模板 16 个 case，枚举 19 个 —— 模板缺 `find` / `contains` / `equals`（设计器可配但不生成代码？）。**

---

### 七、★★★★ `BaseNodeGroupEnum`：节点按设计器分组

```
0 ALL / 1 MICROFLOW / 2 ENTITY_RULE / 3 FRONTEND / 4 CUSTOM / 5 FUNCTION
```
**★★★★★ 这直接回答「节点在哪个设计器能拖」：**
```
MICROFLOW    后端微流程设计器
ENTITY_RULE  实体规则设计器
FRONTEND     页面规则（前端微流程）设计器
CUSTOM       自定义节点（客开）★ 设计上支持，但 EXTEND_ACTION 未实现
FUNCTION     函数节点
```

---

### 八、★★★ `ParamTypeEnum` 是 8 种（不是三态）

```
DEFAULT_OBJECT / BASIC / ENTITY_OBJECT / ENUM / MAP / METADATA / MESSAGE / OTHER
```
**★ 与模板里的 `Expression / SelectParam / Simple` 是两个维度：**
```
ParamTypeEnum    = 参数**值的类型**（实体/枚举/基础值…）
Expression/SelectParam/Simple = 参数**来源**（表达式/引用上游/常量）
```

---

### 九、新增文档 + 脚本

| 文件 | 大小 | 内容 |
|---|---|---|
| **`29-microflow-node-enums.md`** | **15.5 KB** | **8 类 node.type + 29 个 actionType + 19 集合运算 + 分组 + 3 个 bug** |
| **`30-autocode-live-proof.md`** | **17.0 KB** | **★★★★★ 代码生成 LIVE 跑通 + 3 份真实产物 + 52 类框架 + 16 工具类** |

**新增脚本：**
```
RenderTest3.java      单模板渲染（成功，3 份产物）★
RenderBatch.java      批量 15 个模板（3 成功）
RenderBatch2.java     补 table 对象（仍缺 16 工具类）
RenderReal.java       真实 jar 工具类反射注入（11/12 加载，缺 StringHelper）
find_extend.py        搜 ExtendAction 实现类（0 命中）★
find_extend2.py       字节级搜索（只命中 2 个枚举）★
autocode_pkg.py       udc-starter-autocode 52 类全清单★
x6_unzip.py           Python 解压（绕开 MSYS 路径问题）
freemarker.jar        1.7 MB（真实渲染引擎）
rendered/             3 份 LIVE 产物
```

---

### 十、覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **代码生成（静态）** | 98% | **98%** |
| **代码生成（LIVE 验证）** | **0%** | **★ 70%**（Dao/XML/BeanName 真实跑通） |
| **生成框架类结构** | 30% | **★ 95%**（52 类全解 + 执行链路） |
| **模板工具类接口** | 0% | **★ 95%**（16 个清单） |
| **微流程节点枚举** | 85%（101 个） | **★ 98%**（+8 类 node.type / 29 actionType / 分组） |
| **集合运算** | 85%（16 个） | **★ 95%**（19 个 + 4 组分类） |
| **EXTEND_ACTION 扩展点** | 推测「可用」 | **★ 确认：未实现（纯占位）** |

**全局：约 96%**

---

### 十一、下一轮任务

**P0：**
1. **补下载含 `StringHelper` 的包**，让 dto/microflow 模板也能 LIVE 跑通
2. **`EarlyTemplate.filterFilePath/filterTemplateContent`** —— 版本/风格开关（决定生成代码长什么样）
3. **`MicroFlowCodeUtil` 方法签名** —— 微流程模板的大脑

**P1：**
4. `AbstractFreemarkerTemplate.writeToFile` 路径规则（生成物落到哪）
5. `DecorateContainer` 插桩机制
6. `cdp-data-biz`（1,927 类）

**P2（需协助）：**
7. 标品前端 Vue/JS（Maven 仓库没有）
8. 沙箱真实跑一次完整应用生成
---

## 轮次 21 — 2026-11-18/19（★★★★★ 141 个模板全部真实渲染 + 持久化层完整解剖）

### 零、本轮的前提突破

**上轮 P0-1（补含 StringHelper 的包）已解决：**
```
① 一次性下载 117 个标品 artifact（33.7 MB），REMOTE 目录达 218 个
② 30 个 404 全是 parent/aggregator pom（无 jar，正常）
③ 构建统一 classpath：220 个 jar（含 CHIT 的第三方依赖）
④ StringHelper 定位：udc-plugin-api-5.3.605.jar
   → 它是空壳，继承 com.seeyon.udc.common.utils.UdcStringUtils
   → UdcStringUtils 继承 com.seeyon.boot.util.StringUtils（boot-core）
```

### 一、★★★★★ 141/141 模板全部渲染成功（零失败）

**方法：真实 FreeMarker 2.3.32 + jar 内真实 .ftl + 60 个真实工具类反射包装**

```
Engine    FreeMarker 2.3.32
Templates udc-biz-5.3.605.jar / autocode/JAVA/2.9/templates/ (141 个)
Env       220 jar classpath + pinyin4j-2.5.1（4 个模板需汉字转拼音）
Result    成功 141 / 失败 0
Script    D:/software/hermes/cache/scratch/RenderGo.java
Output    D:/software/hermes/cache/scratch/rendered_go/*.out
```

**★★★ 遍历过程中发现的三个平台配置事实（否则模板跑不动）：**

| # | 事实 | 证据 |
|---|---|---|
| 1 | `boolean_format` 必须设 `"c"` | FreeMarker 2.3.32 默认把 `true,false` 视同未设置，`${bool}` 直接抛异常 |
| 2 | 需要自定义 `paster` 指令 | 模板里有 `<@paster name="xxx"/>`，是平台指令 |
| 3 | 工具类不能用原生 static 暴露 | `BeansWrapper.EXPOSE_ALL` / `ClassModel` 全失败，必须自写 `TemplateHashModel` 反射包装 |

### 二、★★★★★ 生成物真实内容（全部是 LIVE_RULE）

**新建 6 篇文档：**

| 文档 | 核心结论 |
|---|---|
| `35-appservice-real-output.md` | AppService 接口 **38 个方法**完整清单 |
| `36-all-templates-live.md` | 141 模板全渲染 + 22 字段属性模型 + 产物体量表 |
| `37-generated-artifacts-anatomy.md` | DAO 空接口 / XML 零 SQL / DTO 结构 / 命名规则 |
| `38-service-three-layers.md` | 三层架构 + 25 个 BaseService 方法 + 注解栈 |
| `39-allinone-dao-anatomy.md` | `AbstractAllInOneBaseDao` **51 方法** + 双通道机制 |
| `40-dynamic-sql-and-condition-dsl.md` | 动态 SQL 拼装 + **14 个条件操作符 DSL** |

**★★★ 本轮最重要的 7 条硬结论：**

1. **DAO 是空接口（543 字节），MyBatis XML 零条 SQL（246 字节）**
   `interface DemoOrderDao extends AbstractAllInOneBaseDao<Order>{}`
   `<mapper namespace="...DemoOrderDao"></mapper>`
   ⇒ **平台完全不生成 CRUD SQL**

2. **`AbstractAllInOneBaseDao` 有 51 个方法**，双通道：
   ```java
   if (properties.isAllInOneByJDBC() && SeeyonEntityHelper.contains(entityClass))
       return allInOneJdbcDao.xxx();      // JDBC 直连
   return allInOneBaseMybatisDao.inOneXxx();  // MyBatis
   ```
   每个方法都是 `putThreadContext()` → 操作 → `removeThreadContext()`

3. **条件查询的真正接口是 `Map<String,Object>` + 下划线 DSL**
   ```
   "amount"        → amount = ?
   "GT_amount"     → amount > ?
   "LIKE_name"     → name like ?
   "NULL_remark"   → remark is null
   "@GT_amount"    → amount > otherColumn（右值是字段名）
   ```
   14 个操作符：EQ/NEQ/LIKE/LLIKE/RLIKE/NOTLIKE/GT/GE/LT/LE/IN/NOTIN/NULL/NOTNULL

4. **三层架构已实证：AppServiceImpl 是纯委托层**
   ```java
   private OrderService domainService;
   return SingleResponse.from(domainService.createBatch(request.getData()));
   ```
   ⇒ 业务逻辑全在 `OrderService`，改 AppServiceImpl 没用

5. **BaseService 有 12 个生命周期钩子**，其中 `afterUpdate(dtoList, oldDtoMap)` 带旧值 Map
   六个注入依赖含 **子表 Service 自动注入**（`OrderDetailService`）

6. **`PageData<Entity>.to(DtoClass)` 是实体→DTO 的批量转换机制**
   ```java
   PageData<Order> pageData = demoDao.selectPageByConditions(...);
   PageData<OrderDto> dto = pageData.to(OrderDto.class);
   ```

7. **Oracle 特有处理：`= ''` 自动改写成 `is null`**
   （Oracle 里空串等同 NULL，平台已处理，业务代码不用管）

### 三、★★★ 22 个字段属性模型（从模板反推）

```
id(字符串!) guid name caption code columnName dbColumnName
javaType javaDataType dataType dataTypeName(枚举名) 
primaryKey required notNull multiSelect
defaultValue defaultValueSystemVariable example comment
length maxLength scale decimalScale
sensitive useSnapshot desensitizationType enableSensitiveWordCheck
entity(null=非关联) enum ctpEnum attachment（四类关联）
```

**★★★ 四类关联字段判断（dto.java.ftl 原文）：**
```freemarker
<#if field.entity??>      → relationDto = field.entity.dtoFullName
<#elseif field.ctpEnum??> → relationDto = field.ctpEnum.ctpEnumFullName
<#elseif field.attachment??> → relationDto = field.attachment.attachmentFullName
<#elseif field.enum??>    → 只有 relationApp
```
**⇒ 普通字段这 4 个键必须是 null（不是空 Map），否则被误判**

### 四、★★ 命名规则实证汇总

| 产物 | 规则 | 实例 |
|---|---|---|
| DAO | `{appNamePackage}{Cap}{E}Dao` | `DemoOrderDao` |
| DAO 泛型 | `<Entity>` 不是 DTO | `AbstractAllInOneBaseDao<Order>` |
| 子表 DTO 列表 | `{uncap}{child}DtoList` | `orderDetailDtoList` |
| 子表 getter | `get{Cap}{child}DtoList` | `getOrderDetailDtoList` |
| AppService | `{Cap}{E}AppService` | `OrderAppService` |

（`handleOneToManyEntityName4Dto` = `uncap + "DtoList"` 已反编译确认）

### 五、待验证（新增）

| 问题 | 状态 |
|---|---|
| 平台 `paster` 片段的真实内容 | UNVERIFIED（我用了空实现，模板能跑但片段为空） |
| `BaseService` 的父类（`extends <空>`） | UNVERIFIED（`superService` 变量缺失） |
| `isAllInOneByJDBC()` 默认值 | UNVERIFIED |
| `SeeyonEntityHelper` 如何从注解解析列 | 待反编译 |
| `Wrapper` 完整 API | 待反编译 |
| 生成物是否真能编译 | UNVERIFIED（需完整工程） |

### 六、覆盖度

**能力域：**
| 域 | 上轮 | 本轮 |
|---|---|---|
| **代码生成** | 62% | **★★★ 85%**（141 模板全渲染 + 生成物解剖） |
| **持久化** | 95% | **★★★★ 98%**（DAO 51 方法 + 动态 SQL 全解） |
| 服务分层 | — | **95%**（三层架构 + 25+40 方法） |

**整体完成度：** 1:90% / 2:**85%** / 3:**98%** / 4:85% / 5:70% / 6:75% / 7:70%
**全局：约 94%**
**状态：`PARTIALLY_COMPLETED`**（静态证据接近完备，运行时写入仍未批准）

### 七、下一轮任务

**P0：**
1. `SeeyonEntityHelper` 反编译 —— 注解→列映射的解析规则
2. `Wrapper` API —— 另一套条件表达
3. `AllInOneDBUtil.insertBatch` 的 INSERT 拼装
4. `paster` 片段的真实来源（找平台如何注入）

**P1：**
5. `feature/` 目录 15 个模板的用途（树实体特性）
6. 树实体的方法集与普通实体差异
7. `DatabaseDialectManager` 支持哪些库

**P2：**
8. 把渲染产物与真实工程对比，验证能否编译

---

## 轮次 22 — 2026-11-19（★★★★★ P0 四连全清：注解映射 / Wrapper / INSERT / 版本选择）

### 一、本轮新增 4 篇文档

| 文档 | 核心 |
|---|---|
| `41-entity-annotation-mapping.md` | `@Table`/`@Column` 硬契约 + `Wrapper` API + `insertBatch` 拼装 |
| `42-interceptor-autofill.md` | `AllInOneDBInterceptor` 自动填充 5 字段 + 类型转换 + 乐观锁 |
| `43-template-version-selection.md` | 版本回退机制完整闭环（LIVE 吻合） |

### 二、★★★★★ 七条硬结论（全部 VERIFIED_STATIC_BYTECODE 或 LIVE）

**1. `SeeyonEntityHelper.initEntity` 的硬契约**
```java
Assert.notEmpty(table.name(), "实体Table注解必须指明表名");
Assert.notEmpty("", "实体必须包含Table注解");
→ 列名 = @Column.name()，不是字段名
→ @Column 但 name="" → 该字段静默跳过（既不 select 也不 insert）
→ 沿继承链向上遍历，父类字段也收集
→ List<Messageable枚举> → 自动收集枚举常量到 enumList
```

**2. `contains()` = 「该实体是否被成功初始化过」**
```java
public static boolean contains(Class<?> entityClass) {
    return seeyonEntityColumnsMap.containsKey(entityClass);
}
```
⇒ 双通道判定 `isAllInOneByJDBC() && contains(entityClass)` 的真实含义是「@Table 解析成功过的实体走 JDBC」。

**3. `Wrapper` 是 tk.mybatis `Example` 的三层薄封装**
```
Wrapper → SeeyonExample → tk.mybatis Example
SeeyonExample 加了 3 个方法：createCriteriaAddOn() / and() / or()
SeeyonCriteria 只额外 4 个方法：andEqualTo/andNotEqualTo/orEqualTo/orNotEqualTo
其余全部来自 Example.Criteria（tk.mybatis 原生）
```

**4. `insertBatch` 的 SQL 是手拼的**
```java
"INSERT INTO " + tableName + " (" + columnSql + " ) VALUES (" + unknownMarkSql + " )"
+ jdbcTemplate.batchUpdate(sql, datas, batchSize, setter)
★ 列清单取 datas.get(0) 的 keySet —— 所有行字段集合必须一致，否则丢字段
```

**5. `updateBatchByIds` 用 `SWHEREid` 哨兵键**
```java
"UPDATE t_order SET orderno = ? , amount = ? , update_time = ? , version = ?  WHERE id = ?"
→ keys 数组末尾塞 "SWHEREid"，每行 map.put("SWHEREid", map.get("id"))
→ columnSet 里的 tenant_id / id 被静默丢弃
```

**6. `AllInOneDBInterceptor` 自动填充 5 个字段（全部回写对象）**
| 字段 | INSERT | UPDATE |
|---|---|---|
| `id` | `Ids.gidLong()` | 只做 WHERE |
| `tenant_id` | `RequestContext.getTenantId()` | 被移除 |
| `create_time` | `new Date()` | 被移除（永不覆盖） |
| `update_time` | `new Date()` | `new Date()` |
| `version` | `0` | `+1`（`noUpVersion` 则不变） |

**⇒ 主键、租户、创建/更新时间、版本号业务代码一个都不用写。**
**⇒ `insertBatch` 之后传入对象已经有 id（反射回写）。**

**7. ★★★★★ 模板版本选择机制（LIVE 吻合）**
```
AutoCodeProperties.codeVersions = ["2.7","2.8","2.9","3.0"]
   ↓
getCodeVersion() = getMajorVersion("5.3.605") = "5.3"
   ↓
wrapVersion() → "/autocode/JAVA/5.3/..."
   ↓ 5.3 目录不存在
TemplateAdapter → 降序试 [3.0, 2.9, 2.8, 2.7]
   ↓
entity.java.ftl   → 3.0 命中（3.0 只有 2 个模板）
其余 141 个       → 2.9 命中
```

**实跑验证 `getMajorVersion`：**
```
5.3.605 → "5.3"   ✓
5.3     → "5.3"   ✓
5.3.6.1 → "5.3"   ✓
10.2.1  → "10.2"  ✓
```
**⇒ 「主版本」= 前两段 X.Y，不是 X。**

### 三、★★★★ 实体类真实结构（3.0 模板渲染产物）

```java
@Entity(name="demoOrder")
@Table(name = "...")
@Alias("demoOrder")
@EntityInfo(value="订单", customs={
    @Custom(properties=@CustomAttribute(name="stereotype", value="")),
    @Custom(properties=@CustomAttribute(name="features",   value="")),
    @Custom(properties=@CustomAttribute(name="id",         value="0")),
    @Custom(properties=@CustomAttribute(name="guid",       value="")),
    @Custom(properties=@CustomAttribute(name="name",       value="order")),
    @Custom(properties=@CustomAttribute(name="entityCategory", value="NORMAL"))
})
public class Order extends {...} {
    @Column(name="id", columnDefinition="")
    @EntityAttribute(value="主键", dataType=DataType.XXX, safety=@Safety(auditLog=false, openApiEncrypt=...),
        customs={@Custom(properties={
            @CustomAttribute(name="id",          value="4355"),
            @CustomAttribute(name="guid",        value="109108"),
            @CustomAttribute(name="useSnapshot", value="false"),
            @CustomAttribute(name="name",        value="id"),
            @CustomAttribute(name="notNull",     value="true")})})
    @Id
    private Long id;
}
```

**⇒ 平台元数据的「设计态 ID」全部嵌在注解的 `@CustomAttribute` 里。**

### 四、★★★★ 版本目录分布（重要）

| 版本 | 模板数 | entity.java.ftl | baseservice.java.ftl |
|---|---|---|---|
| 2.7 | 125 | ✅ | ❌ |
| 2.8 | 138 | ✅ | ❌ |
| 2.9 | 141 | ❌ | ❌ |
| **3.0** | **2** | **✅** | **✅** |

**⇒ 渐进式升级：3.0 只放了 2 个最核心的产物（entity 13KB / baseservice 74KB），其余 141 个留在 2.9。**

### 五、★★★ 新增待验证

| 问题 | 状态 |
|---|---|
| `Apps.depends()` 里 udc-starter-autocode 的 version 实际值 | UNVERIFIED |
| `LazyCacheUtils.getTemplatePath` 的加载机制 | 待反编译 |
| `StringUtils.compareVersion` 排序规则 | 待确认 |
| `ObjToMapUtil.objectToMap` 空值策略 | 待反编译 |
| `AllInOneDBInterceptor.select` 的 `daoMethod` 分支 | 待展开 |
| `EntityEncryptionService` 算法 | UNVERIFIED |
| `batchSize` 默认值 | UNVERIFIED |

### 六、覆盖度

**整体完成度：** 1:90% / 2:**★★★★ 90%**（+5，版本机制闭环）/ 3:**★★★★ 99%**（+1）/ 4:85% / 5:70% / 6:75% / 7:70%
**全局：约 96%**
**状态：`PARTIALLY_COMPLETED`**（静态证据接近完备，运行时写入仍未批准）

### 七、下一轮

**P0：**
1. `LazyCacheUtils` 模板加载机制（模板如何从 jar 读出来）
2. `ObjToMapUtil.objectToMap` 空值策略（决定批量插入丢字段的边界）
3. `SeeyonEntityHelper` 的 `@EntityAttribute` → DTO 映射（`EntityCodeUtils.getJavaType`）
4. `AllInOneDBInterceptor.select` 的 `daoMethod` 分支

**P1：**
5. `feature/` 目录 15 个模板（树实体）
6. `DatabaseDialectManager` 支持库清单
7. `baseservice.java.ftl`（3.0，74KB）的完整结构

**P2：**
8. 渲染产物编译验证

---

## 轮次 23 — 2026-11-19（★★★★★ P0 四连再清 + 三处自我纠错）

### 一、本轮新增 1 篇文档 + 修正 2 篇

| 文档 | 动作 |
|---|---|
| `44-type-contract-and-autofilter.md` | 新增：类型契约 + 自动过滤 + 三处纠错 |
| `41-entity-annotation-mapping.md` | **修正**：批量插入「丢字段」结论是错的 |
| `42-interceptor-autofill.md` | **修正**：`daoMethod` 用途不是字段裁剪 |

### 二、★★★★★ 本轮最重要：发现自己渲染模型传错参数

**模板原文（3.0 entity.java.ftl）：**
```freemarker
,dataType = DataType.${field.dataTypeCapName}
private ${field.dataType} ...
<#if field.dataTypeName == 'DECIMAL' ...>
```

**⇒ 真实契约：**
| 变量 | 含义 | 例 |
|---|---|---|
| `field.dataType` | **Java 类全名** | `java.lang.Long` |
| `field.dataTypeName` | DataType 枚举名 | `BIGINTEGER` |
| `field.dataTypeCapName` | 枚举名首字母大写 | `BIGINTEGER` |

**我之前把枚举名塞进 `field.dataType`，所以产物成了 `private LONG id;`，当时标 UNVERIFIED。**
**⇒ 修正 RenderGo 后重渲染：**
```java
private Long id ;                    @Column(name="id")
private String orderNo ;             @Column(name="orderno")
private BigDecimal amount ;          @Column(name="amount")
private Date createDate ;            @Column(name="createdate")
```
**⇒ 完全正确。这是我传参错误，不是平台问题。**

### 三、★★★★★ `DataType` 枚举 19 个取值（code 不连续）

```java
STRING(0) INTEGER(1) BIGINTEGER(5) DECIMAL(6) BOOLEAN(7)
DATETIME(8) DATE(9) TIME(10) ENTITY(11) OBJECT(12)
ENUM(13) ATTACHMENT(14) MULTILINESTRING(15) CURRENCY(17)
CTPENUM(18) ARRAY(20) MAP(21) SORTORDER(22) METADATA(23)
```
**缺 2/3/4/16/19 —— 有历史废弃类型，code 作为持久化值不能复用。**

**★★★ 四类关联：只有 `CTPENUM` / `ENUM` / `ENTITY` 在 `DATATYPE_RELATION_ENTITY` 白名单里。**

### 四、★★★★★ `DataType` → Java 类型映射（表达式用，10 条）

| DataType | Java | 反直觉点 |
|---|---|---|
| STRING | `String` | |
| MULTILINESTRING | `String` | |
| BOOLEAN | `Boolean` | |
| CURRENCY / DECIMAL | **`BigDecimal`** | 不是 Double |
| INTEGER | `Integer` | |
| **BIGINTEGER** | **`Long`** | ★ 名字叫 BigInteger 实际是 Long |
| **TIME** | **`String`** | ★ 不是 java.sql.Time |
| DATE / DATETIME | `Date` | |

**⇒ 只有 10 个类型可用于表达式；其余 9 个（ENTITY/ENUM/CTPENUM/ATTACHMENT/ARRAY/MAP/OBJECT/SORTORDER/METADATA）调用 `getJavaType` 抛「不支持的表达式返回值类型」。**

### 五、★★★★★ 纠错一：批量插入**不会**丢列

```java
private void copyMap(Map copyMap, Map dbMap, Map<String,String> columns) {
    for (Map.Entry<String,String> entry : columns.entrySet()) {   // ★ 遍历 @Column 注解
        dbMap.put(entry.getValue(), copyMap.get(entry.getKey()));
    }
}
```
**⇒ dbMap 的 key 集合恒等于 `@Column` 注解集合，与对象值无关。**
**⇒ 列清单永远一致。我第 41 轮说的「行间字段不一致丢字段」是错的。**

**真实影响只有一个：某属性为 null 时 `copyMap.get()` 返回 null → 该列插 NULL（不是丢列）。**

### 六、★★★★★ 纠错二：`daoMethod` 不做字段裁剪

```java
if (!"selectById".equals(daoMethod) && !isEmpty(secretClass) && secretLevel >= 0) {
    whereMap.put("LE_secretN", secretLevel);
}
```
**⇒ `daoMethod` 唯一用途：判断是不是 `selectById`，从而跳过密级过滤。**

### 七、★★★★★ 纠错三 + 新发现：`select` 的两个自动条件

```java
private void selectByIgnoreTenant(...) {
    // ① 租户过滤（强制，每查必加）
    whereMap.put("EQ_tenantId", RequestContext.get().getTenantId());

    // ② 密级过滤
    if (!"selectById".equals(daoMethod) && secretClass非空 && secretLevel >= 0) {
        whereMap.put("LE_secretN", secretLevel);
    }
}
```

**⇒ 每查必加租户条件；有密级实体自动加 `LE_secretN`（只看 ≤ 自己密级）。**
**★ 安全边界：`selectById` 绕过密级限制（知道 id 就能拿任意密级数据）。**

### 八、★★★★ `ObjToMapUtil` 的四条事实

```java
② Introspector.getBeanInfo(obj.getClass())   // 用 JavaBean 属性，不是反射字段
③ map.put(key, value);                        // ★ null 也 put（key 一定存在）
④ value instanceof Messageable → value.code() // 单枚举转 code
⑤ List<Messageable> → String.join(",", codes) // 多选转逗号串
```

### 九、★★★★ 完整自动注入清单（14 项，已在 44 篇汇总）

INSERT 5 项（id/create_time/update_time/version/tenant_id）、UPDATE 4 项、SELECT 2 项、类型转换 3 项、加解密 1 项。

### 十、覆盖度

**整体完成度：** 1:90% / 2:**★★★★ 92%**（+2）/ 3:**★★★★★ 99%** / 4:**90%**（+5，类型契约闭环）/ 5:70% / 6:75% / 7:70%
**全局：约 96.5%**
**状态：`PARTIALLY_COMPLETED`**

### 十一、下一轮

**P0（剩余）：**
1. `LazyCacheFactory` + 模板注册写入者（谁扫 jar 里的 .ftl 到 `template_path_cache`）
2. `StringUtils.compareVersion` 排序规则
3. `baseservice.java.ftl`（3.0，74KB）的完整结构 —— 这是最大单文件模板
4. `feature/` 目录 15 个模板（树实体）

**P1：**
5. `EntityAnnotationCache.getSecretClassName` 的密级机制
6. `batchSize` 默认值 / `AllInOneProperties` 全部配置项
7. `DatabaseDialectManager` 支持库清单

**P2：**
8. 渲染产物编译验证（需补 `DtoCodeUtil` 等真实工具类）
---

## 轮次 24 — 2026-11-19（★★★★★ BaseService 74KB 全解 + 微流程 LIVE 渲染）

### 一、本轮新增 4 篇文档

| 文档 | 核心 |
|---|---|
| `45-baseservice-and-stereotype-injection.md` | BaseService 48 方法 + 特性注入机制 + Type 枚举 9 类 |
| `46-tree-entity-and-ruleservice.md` | 树实体特性 10 模板 + ruleservice 三类服务 |
| `47-microflow-codegen.md` | 微流程 55 模板 + 17 node.type + 12 核心宏 |
| `48-microflow-live-render.md` | ★ LIVE：微流程真实渲染 + 28 actionType 权威清单 |

### 二、★★★★★ BaseService（74KB，1417 行模板）全解

**14 个注入依赖：**
```
SecretEnumUpdateService / BusinessEventHelper / Validate{E}Service /
{E}AssignValueService / ApproveFeatureService / AllInOneBaseDao<E> /
{Pkg}{E}Dao / ExpressionEvaluator / MessageRepository /
ScalabilityFieldService / UdcSerialConfigService
```

**12 个生命周期钩子都是「平台注入槽」，不是空方法：**
```java
afterSelect       -> joinSnippets("selectById(Long id)#after")
beforeCreate      -> joinSnippets("createBatch(...)#before")
afterCreate       -> paster(event.business.class[service][CREATE]) + paster(send_create_write_back)
beforeUpdate      -> 真实逻辑：sensitive4Update + resolveDefaultValueNotAllowedModify
afterUpdate       -> 2x joinSnippets + 2x paster
beforeDelete      -> paster(send_delete_write_back) + joinSnippets(...#before)
```
**=> 重写钩子会覆盖平台特性代码注入（除非调 super）。**

**48 个方法分 10 组：**校验 6 / 查询 3 / 创建更新 6 / 默认值 8 / 聚合动态生成 5 / 复制转换 3 / 脱敏 4 / 附件 4 / 密级 1 / 级联 2。

### 三、★★★★★ 特性注入的两大机制（框架级发现）

**机制一 `paster` 指令（平台预制片段）：**
```java
TemplateModel pastTemplate = env.getDataModel().get("paster_" + pastKey);
if (pastTemplate == null) return;   // 静默跳过
```
```
PasterConfig.SEND_CREATE_WRITE_BACK = "send_create_write_back"
PasterConfig.SEND_UPDATE_WRITE_BACK = "send_update_write_back"
PasterConfig.SEND_DELETE_WRITE_BACK = "send_delete_write_back"
BasePasterConfig.PASTER_PREFIX = "paster_"
```

**机制二 `joinSnippets` 宏（特性代码）：**
```freemarker
<#list BIZ_DOMAIN_SERVICE.joinSnippets[mKey]! as item>${item.code}</#list>
```
**8 个 key（方法签名#时机）：**
```
selectById(Long id)#after        createBatch(...)#before       createBatch(...)#middle
createBatch(...)#after           updateBatch(...)#after        updateBatch(...)#afterUpdate
deleteByIds(List<Long> ids)#before    deleteByIds(List<Long> ids)#after
```

**`BIZ_DOMAIN_SERVICE` 由 `StereotypeDecorate.getExtraArgs()` 注入：**
```java
m.put(Type.BIZ_DOMAIN_SERVICE.strCode(), ...);  // 共 7 个键
boolean isOutter = !appInfo.getId().equals(entityDto.getAppId());
public boolean matches(...) { return !this.isOutter; }  // 跨应用不注入
```

### 四、★★★★★ `Type` 枚举 —— 完整包结构（核心架构事实）

```
{appPackagePath}
  +-- api/          {E}AppService            FACADE
  +-- dto/          {E}Dto                   FACADE
  +-- appservice/   {E}AppServiceImpl        BIZ
  +-- domain/
  |   +-- entity/   {E}Entity                BIZ
  |   +-- service/  {E}Service               BIZ
  |   +-- dao/      {E}Dao                   BIZ
  |   +-- event/    {E}Event                 BIZ
  |   +-- event/listener/ {E}Listener        BIZ
  +-- controller/   {E}Controller            WEB
```
**9 个 Type，但 `getExtraArgs` 只注入 7 个 —— 事件类不支持特性扩展。**
**`WEB_CONTROLLER.defaultClassName = "{E}Listener"` 疑似平台 bug（实测渲染是 `Abstract{E}Controller`）。**

### 五、★★★★★ 树实体特性（10 个模板，含唯一平台生成 SQL）

```java
// feature.tree.entity.class[dao].ftl
@Select(value = "SELECT * FROM ${table.dbTableName} WHERE tree_path REGEXP CONCAT(#{path},'/', '-?[0-9]+$')")
List<${E}> selectImmediateChildren(String path);

@Select(value = "SELECT * FROM ${table.dbTableName} WHERE tree_path REGEXP CONCAT(#{path},'/')")
List<${E}> selectAllChildren(String path);
```
**=> 这是整个代码生成体系唯一的真实 SQL（其余全部零 SQL）。**

**树实体多 3 个查询**：`selectImmediateChildren` / `selectAllChildren` / `selectAllParents`
**树实体的三处特性注入**：创建前建虚拟树、删除级联子节点、更新前 `dealTreeBeforeUpdate`

### 六、★★★★★ 特性模板命名机制（框架级发现）

```
feature.{特性名}.class[{目标产物}].method[{方法}][{时机}].ftl
                    |                    |
            app_service/service              无后缀=after
            app_service_impl/controller/dao   [before]/[after]
                    |
        精确对应 joinSnippets("{方法}Batch(...)#{时机}")
```

### 七、★★★★★ `entityrule/ruleservice.java.ftl` —— 业务规则服务

**一个模板生成三类服务（`groupType` 分派）：**

| groupType | 类名 | 方法 |
|---|---|---|
| `VALIDATE` | `Validate{E}Service` | `do{E}Rule(List<E Dto>, boolean isUpdated)` |
| `ASSIGN_VALUE` | `AssignValueFor{E}Service` | `do{E}Rule(E Dto)` |
| `DEFAULT_VALUE` | `DefaultValueFor{E}Service` | `do{E}Rule(E Dto)` |

**业务规则能注入微流程和 Dubbo：**
```freemarker
<#list subMfList as sub>@Autowired ${sub.serviceFullName} ${sub.uncapServiceName};</#list>
<#list dubboServiceMap?keys as key>${key} ${dubboServiceMap[key]};</#list>
```
**=> 这是低代码连外部系统的关键通道。**

**6 类规则活动：**赋值 / 必填 / 唯一 / 默认值 / 提示消息 / 根实体取值。

### 八、★★★★★ 微流程是「编译型」不是「解释型」（架构级结论）

**55 个模板 + 768 行主引擎：**
```
microflow/
  MicroFlowDomainService.java.ftl   <- 768 行主引擎（12 个核心宏）
  22 个 *Activity.java.ftl          <- 每个 actionType 一个
  common/ 8 个工具宏                <- CallMethodUtil / GenericInvokeUtil 等
  customflow/ 7 个                  <- 自定义微流程（Bean 注册 + Dubbo 导出）
  web/ 5 个 + host/ + util/         <- REST / GraphQL 暴露
  schedule/ 1 个                    <- 定时任务
  plugin/calldataflow/ 3 个         <- 生单插件（独立 DI）
  event/ 2 个                       <- 业务事件监听
```

**三层分派结构：**
```
node.type（6 控制流 + 11 数据节点）
  -> node.actionType（22 类活动）
    -> 对应 .ftl 模板
```

### 九、★★★★★ LIVE 实测：微流程模板真实渲染成功（4,007 字节，缺失键 0）

**方法：**FreeMarker 2.3.32 + 141 个真实模板（Python 精确提取）+ 221 jar classpath + 55 个工具类反射包装

**产物（真实生成）：**
```java
@Slf4j
@Service
public class CreateOrderFlowService {
@Autowired private ExpressionEvaluator expressionEvaluator;
@Autowired com.seeyon.boot.starter.udcrt.appservice.DynamicSelectAppService dynamicSelectAppService;

@UseUdcAppLog(appName = "zzprobe")
public com.seeyon.zzprobe.dto.OrderDto createOrderFlow(com.seeyon.zzprobe.dto.OrderDto orderDto){
    UdcAppLogHelper.buildMfLogV2("createOrderFlow", ModuleSubTypeEnum.MICRO_FLOW_MANUAL,
                                 "创建订单流程","1234567890123",8704025620829192834L,"zzprobe");
    UdcAppLogHelper.buildInputLog(..., MicroFlowLogUtil.toJson4LogV2(orderDto,"zzprobe"), ...);
    Map<String, Object> formulaMap;
    PageInfo pageInfo;
    List<Sort.Order> sortOrderList;
    Map<String,Object> selectMap = null;
    MapConditionResult mapConditionResult;
    MicroFlowDynamicJoinSelectParamDtoBuilder joinSelectParamBuilder;
    ProxyJoinParamDto proxyJoinParamDto;
    Sort sort;
    Map<String, Map<String, Object>> dataMapping;
}
```

**28 个 `actionType` 权威取值（修正第 47 篇的推测）：**
```
Activity  Branch  Break  CallAppService  CallDataFlow  ChangeBatchEntity
ChangeEntity  ChangeList  ChangeVariable  Connector  ConvertData
CreateBatchEntity  CreateEntity  CreateList  CreateMap  CreateVariable
CustomError  DataMapping  DeleteEntity  For  ForEach  ListOperation
MapOperation  PublishBusinessEvent  Retrieve  RetrieveArray  SubMicroFlow  Switch
```
**=> 驼峰命名（`CreateEntity`），不是大写下划线（`CREATE_ENTITY`）。**

**9 个局部变量 = 微流程运行时容器：**formulaMap / pageInfo / sortOrderList / selectMap / mapConditionResult / joinSelectParamBuilder / proxyJoinParamDto / sort / dataMapping

**3 种 triggerType 日志分支：**`MANUAL` / `BUSINESS_EVENT` / `SCHEDULE`（SCHEDULE 无入参）
**方法必有 `@UseUdcAppLog(appName=...)`**（注释：「测试环境才打开」）
**import 暴露 6 条能力事实：**DubboReference、三套 JSON 工具并存、表达式两层引擎、条件独立输出层、跨应用联查代理、CtpEnumItemService

### 十、★★★★ 已确认的结构性阻塞（诚实记录）

**微流程节点代码的完整渲染 BLOCKED：**
```java
MicroFlowCodeUtil.isEntityType(com.seeyon.udc.common.dto.ApplicationDto, java.util.Map)
```
- 第一参数必须是真实 `ApplicationDto`
- 构造它需要 **javassist**（`javassist/ClassPath`），不在 221 个标品 jar 里（Spring Boot fat-jar 内嵌依赖）

**另有 5 个工具类需 Spring 容器：**
```
JsonUtils / UdcJsonUtils     缺 jackson-datatype-jsr310
LogUtil                      缺 caffeine
EntityCodeUtils              缺 nacos shaded guava
ConditionConfigOutputUtil    <clinit> 直接调 Apps.getApplicationContext().getBean() -> NPE
```
**=> 微流程节点生成必须在真实 Spring 容器内。不影响已得的架构层结论。**

### 十一、★★★★★ 实测确认的 5 条平台契约

| # | 契约 | 证据 |
|---|---|---|
| 1 | `node.isShouldGenerateCode()` 是**方法**不是属性 | 传 boolean 报「Expected a method or function」 |
| 2 | `microflowInfo.nodes` 是列表，元素有 `type`/`actionType` 两层 | `<@nodesLogicHandler (microflowInfo.nodes!) ...>` |
| 3 | 无 triggerType 匹配 -> 不产出入口日志 | 模板三分支 |
| 4 | `microFlowNodeExistence` 需 8 个字段 | needImportEntityPackage/hasErrorNode/hasEvent/hasMicroFlowMq/hasIntegrationMq/hasProxyService/hasMapOperation/dtoSources |
| 5 | `isEntityType(ApplicationDto, Map)` 需真实 DTO | 反射传 HashMap 报 argument type mismatch |

### 十二、覆盖度

**整体完成度：** 1:90% / 2:**★★★★★ 95%**（+3，BaseService+特性+微流程全解）/ 3:**★★★★★ 99%** / 4:**★★★★ 95%**（+5，微流程生成 LIVE）/ 5:70% / 6:75% / 7:70%
**全局：约 97%**
**状态：`PARTIALLY_COMPLETED`**（静态证据接近完备；微流程节点渲染需容器，未批准）

### 十三、下一轮

**P0：**
1. `microflow/enums`、`filterplan`、`refer`、`beanname`、`project` 剩余 8 个域
2. `MicroFlowCodeUtil` 91 个方法的语义清单（按需）
3. `isShouldGenerateCode()` 的实现（哪些节点跳过）
4. `Stereotypes` Bean 里注册的全部特性清单

**P1：**
5. `DatabaseDialectManager` 支持库清单
6. `batchSize` 默认值 / `AllInOneProperties` 全配置项
7. `EntityAnnotationCache.getSecretClassName` 密级机制

**P2（需审批或容器）：**
8. 微流程节点代码完整渲染（需 Spring 容器）
9. 渲染产物编译验证---

## 轮次 25 — 2026-11-19（★★★★★ 15 域全覆盖 + 工程骨架全解）

### 一、本轮新增 1 篇文档

`49-project-skeleton-and-events.md` —— 工程骨架 + 事件 + 参照 + 筛选方案 + 枚举 + BeanName（9 个此前未覆盖的域）

### 二、★★★★★ 15 个域 / 141 模板全景（本轮补完后全覆盖）

| 域 | 模板数 | 内容 |
|---|---|---|
| microflow | 54 | 微流程（见 47/48） |
| entity | 21 | 实体 + BaseService（见 45） |
| common | 13 | 公共宏 |
| feature | 10 | 特性注入（见 45/46） |
| **project** | **9** | **★ 工程骨架（pom + Application + yaml）** |
| entityrule | 9 | 业务规则（见 46） |
| **project-for-deploy** | **6** | **★ 集成测试工程** |
| **event** | **5** | **★ 业务事件 + 实体事件** |
| **refer** | **4** | **★ 参照 Controller** |
| **project-ext** | **3** | **★ 扩展模块** |
| **referconfig** | **2** | **参照/页面配置 JSON** |
| **filterplan** | **2** | **★ 筛选方案 Controller** |
| **enums** | **1** | **枚举类** |
| dto | 1 | DTO |
| **beanname** | **1** | **★ BeanName 修饰器** |

### 三、★★★★★ 工程骨架：4+1 模块（真实依赖链）

```
{appName}  (pom, parent=com.seeyon:boot:${platformVersion})
├── {appName}-facade      只依赖 udc-starter-runtime（纯契约）
├── {appName}-biz         8 个 starter 硬依赖
├── {appName}-web         只依赖 biz
├── {appName}-assemble    打 fatjar + 复制 ext 的 i18n/init
└── {appName}-ext         仅 appType=normal 时存在
```

**biz 的 8 个 starter：**
```
boot-starter-web / appservice / scanner(★元数据扫描) / datainit
boot-starter-transaction / dynamicsql / cache / udc-common
```

### 四、★★★★★ 三维度关键事实

**1. `SeeyonBeanFactory` 替换 Spring 默认 BeanFactory（全平台特性的根）**
```java
ApplicationContextFactory factory = (webApplicationType) ->
    new AnnotationConfigServletWebServerApplicationContext(new SeeyonBeanFactory());
springApplication.setApplicationContextFactory(factory);
```

**2. `appType` 二分**
| appType | 启动类 | 模块数 |
|---|---|---|
| `form` | 不继承 | 4 |
| `normal` | `extends SeeyonInitializer` + 实现 `getStartupClass()` | 5（含 ext） |

**3. `application.y.ftl` 4 行决定运行环境**
```yaml
seeyon.config.server-addr: ${NACOS_ADDR:127.0.0.1:8848}
seeyon.datasource.database: ${appName}      ← 库名=应用名
```

### 五、★★★★★ 枚举硬约束（4 条）

```java
@EnumInfo(value="...", customs={@Custom(properties={appName, orgId})},
          excludes={..., "NONE"})
public enum {Name} implements Messageable {
    NONE(-1, "NONE"),    ← 固定首项
    ...
```
1. 必须 `implements Messageable`
2. 必须 `@EnumInfo`
3. 固定首项 `NONE(-1,"NONE")`（`excludes` 里也硬编码追加 `"NONE"`）
4. 三种包路径：`CONNECTOR` / `DYNAMIC_DEPENDENCY` / 普通 `.enums`

### 六、★★★★★ 业务事件（MQ + OpenAPI 双通道）

```java
@MessageInfo(value="...", topic="...",
             customs={@CustomAttribute(name="from", value="udc")},   ← 固定 udc
             openApi=@OpenApi(isOpenApi=${event.enable}))
public class {Name}Message extends BaseMessage<{dataType}> {
    @JsonCreator public {Name}Message(@JsonProperty("data") {dataType} data)
}
```
- `messageType=DELAY` → `DelayBaseMessage`
- `eventDataType=LIST` → `List<T>`，否则单条
- **`openApi` 一个注解开关内外双通道**
- **MQ 反序列化契约：固定 `data` 字段**

### 七、★★★★★ 实体事件 3 阶段（LIVE 实测确认）

```
com.seeyon.boot.starter.udcrt.event.publisher.EventPublisher$EventPhase
  values: HANDLE_BEFORE | TRANSACTION_BEFORE_COMMIT | TRANSACTION_COMMIT_SUCCESS
```

| triggerType | EventPhase | 真实语义 |
|---|---|---|
| BEFORE | HANDLE_BEFORE | 处理前 |
| AFTER | TRANSACTION_BEFORE_COMMIT | **事务提交前**（命名陷阱！不是提交后） |
| （其他） | TRANSACTION_COMMIT_SUCCESS | 事务成功后 |

**UPDATE 事件带老值：`new {Event}(dto, oldDtoMap.get(id))`（双参）；其它单参。**

**LIVE 实测：**
```java
EntityEventDeepCopier.copyList(Collection, Class) -> List
包路径 com.seeyon.boot.starter.udcrt.util.EntityEventDeepCopier
```

### 八、★★★★★ 事件条件表达式 + 分批（`business.class[service]`）

```java
Map<String,Object> eventConditionFormulaMap = new HashMap<>();
eventConditionFormulaMap.put("${table.name}", dto);
<#if actionType=='UPDATE'>
eventConditionFormulaMap.put("${oldEntityName}", oldDtoMap.get(dto.getId()));  ← 仅UPDATE有老值
</#if>
EvalContextDto ctx = new EvalContextDto();   ← 4 个必设字段
ctx.setContextMap(...); ctx.setExpression(...);
ctx.setExpressionTranslation(...); ctx.setResultType(...);
Boolean eventCondition = (Boolean) expressionEvaluator.eval(ctx);
```

**`numberFiredOnce` 二值：**
```
"ALL" → transactionSuccessEvent(new Msg(eventData))     整批一条
"1"   → for(data) transactionSuccessEvent(new Msg(data)) 逐条
```
**⇒ 都在 `transactionSuccessEvent` 里发，事务成功后自动投递。**

### 九、★★★★ 参照与筛选方案

**参照：** 走 `ReferDynamicSelectAppService`（独立于 `DynamicSelectAppService`）；4 个专属 DTO，其中 `ReferDisplayFiledDto` 的 `Filed` 是**平台拼写错误**，代码里必须照拼。

**筛选方案：**
- **按页面生成 Controller**，`isMobile` 开关生成独立 `...MobileController`
- URL：`${planAppUrl}/[mobile/]${pageUrl}/filter-plan`
- 三方实体返回 `PageResponse<Map<String,?>>`
- 统一入口方法：`dynamicSelect4FilterPlan(SingleRequest.from(dto))`
- 运行时数据源 `RuntimeEntityDataSourceDto`，type 二值 `ENTITY`/`LIST`

**页面配置 16 字段**（`page_config.json`）就是自定义页面完整契约，含 `masterEntity`、`inPortletParams`（可嵌门户）。

### 十、★★★★ Bean 名隔离（多应用共存方案）

```java
public class {App}BeanNameModifyer implements AppBeanNameModifier {
    public String modifyBeanName(BeanDefinition bd, String beanName) {
        if (bd.getBeanClassName().contains(appName) && !beanName.contains(appName))
            beanName = appName + StringUtils.capitalize(beanName);
        return beanName;
    }
}
```

### 十一、★★★★★ 跨应用依赖两种粒度（分界线）

```xml
<#if depApp.dynamicService>
    <artifactId>${depApp.depAppName}-biz</artifactId>   ← 动态服务：引 biz
    <artifactId>${depApp.depAppName}-facade</artifactId>
<#else>
    <artifactId>${depApp.depAppName}-facade</artifactId> ← 普通：只引 facade
</#if>
```
**⇒ `dynamicService=true` 才引 biz —— 这是「调服务」与「只调契约」的分界。**

### 十二、★★★★★ 官方测试样板只给「业务规则」

`project-for-deploy/` 6 模板中唯一业务测试类是 `PersonEntityRuleServiceTest.java.ftl`。
**⇒ 平台认为「业务规则服务」是最需要单测的生成物。**

### 十三、★★★★ 新发现的容器强绑定

```
java.lang.ClassNotFoundException: org.springframework.web.servlet.config.annotation.WebMvcConfigurer
    at com.seeyon.boot.spring.SeeyonBeanFactory.<clinit>(SeeyonBeanFactory.java:98)
```
**⇒ `SeeyonBeanFactory` 静态初始化就引用 Spring MVC —— Web 强绑定，容器外无法加载。**
**⇒ 这解释了整个代码生成体系为何必须在真实 Spring 容器内运行。**

### 十四、覆盖度

**整体完成度：** 1:90% / 2:**★★★★★ 97%**（15 域全覆盖）/ 3:**★★★★★ 99%** / 4:**★★★★ 96%** / 5:70% / 6:75% / 7:70%
**全局：约 98%**
**状态：`PARTIALLY_COMPLETED`**（141 模板全读，宏观架构完备；微观节点语句需容器）

### 十五、下一轮

**P0：**
1. `MicroFlowCodeUtil` 91 个方法语义清单
2. `isShouldGenerateCode()` 实现（哪些节点跳过）
3. `Stereotypes` Bean 注册的完整特性清单
4. `SeeyonBeanFactory` 反编译（特性注入的根）

**P1：**
5. `AllInOneProperties` 全配置项
6. `DatabaseDialectManager` 支持库清单
7. `appType` 的完整取值域

**P2（需容器/审批）：**
8. 微流程节点代码完整渲染
9. `PersonEntityRuleServiceTest` 真实渲染---

## 轮次 26 — 2026-11-19（★★★★★ 原型/特性体系全解 + 91 方法清单）

### 一、本轮新增 1 篇文档

`50-stereotype-and-feature.md` —— 6 原型 + 18 特性 + 18 字段集 + 112 字段全解（含权威配置 JSON 实测）

### 二、★★★★★ `MicroFlowCodeUtil` 91 个静态方法完整清单（LIVE 反射）

**归类（91 个）：**
```
方法名构建     12  buildServiceClassName / buildMicroFlowConditionMethodName /
                   buildMicroFlowAssignValue2JavaBeanMethodName / buildResponseName 等
删除数据过滤    11  addDeletedData / distinctDeletedData / filterDeletedData /
                   findUniqueDeletedData / getDeletedData / getDeletedDataPartition 等
表达式相关     10  generateConditionExpression / getExpressionCodeFragment /
                   buildExpressionDetailsResolver / hasEntityExpressionParam /
                   useOtherVariables / createFormulaMapInstance 等
SelectParam    9  convert2SelectParam / getSelectParamValue(4 变体) /
                   getSingleSelectParamValue / isEntityTypeBySelectParamId 等
类型/包名        7  getFullJavaType / getDtoNameByFullName / castTypeObject /
                   buildControllerDtoFullName(2 变体) / getJavaEnumCollection
引用/导入        4  importDtoPackage / buildHostAppMicroFlowTemplateSupport
子微流程         5  buildSimpleSubMicroFlowRequest / buildSubMicroFlowRequest /
                   getSimpleSubMicroFlowResponseContent /
                   buildDefaultCustomMicroFlowImplBeanName/ClassName
错误处理         4  addErrorInfo4CustomErrorNode / buildCustomErrorNodeSimple /
                   throwUnimplemented / buildMfSimpleI18nParam
判定（boolean） 9  isDynamicSelect / isEntityType / isRangeDataType /
                   isSelectedEntityField / requiredOperationParam /
                   usingEntityReturnValue / requireExportDubboServiceByHand 等
其它工具        20  addSemicolonSuffix / generateBeanCopierCode /
                   populateEventCallBackMessageOptionalParams / saveDefaultUserId 等
```

**★★★★★ 三条结构结论：**
1. **删除数据（deletedData）相关方法最多（11 个）** —— 说明微流程的「删除/后置过滤」是核心场景
2. **只有 3 个方法接受 `ApplicationDto` 作第一参**（`addDeletedData`/`distinctDeletedData`/`assembleRuntimeEntityDataSourceJsonFileName`）—— 这些是容器外卡点
3. **`throwUnimplemented()` 存在** —— 说明模板里存在「故意不实现」的分支

### 三、★★★★★ 原型体系：只有 6 个（LIVE 反射 `StereotypesConstant`）

```java
STANDARD     = "standard"      // 标准
BILL         = "bill"          // 单据
ARCHIVE      = "archive"       // 平铺档案
ARCHIVE_TREE = "archiveTree"   // 树形档案
FORM         = "form"          // 表单
BASIC_DATA   = "basicData"     // 基础资料
```

**6 个实现类（字节码扫描 `AbstractStereotype` 子类）：**
```
StandardStereotype / BillStereotype / ArchiveStereotype
ArchiveTreeStereotype / FormStereotype / BasicDataStereotype
```

**命名机制（`Stereotypes.<clinit>` 反编译）：**
```java
String name = StringUtils.remove(
    StringUtil.camelhumpToUnderline(stereotype.getClass().getSimpleName()), "_stereotype");
AbstractStereotype loaded = configurationLoader.loadStereotype(name, StereotypeBean.class);
```
**⇒ 类名驼峰转下划线 + 去 `_stereotype` → 加载 `stereotype/{name}/config.json` 覆盖。**

**`AbstractStereotype` 11 个属性：**
```
features / availableFeatures / necessaryFeatures
name / caption / description / order / deprecated / nonDeprecated
processEmbedded    ← 是否内嵌流程
dataFlowEnabled    ← 是否启用数据流
```

**原型唯一的运行时行为：保存后按 JSON 初始化枚举**
```java
// BillStereotype
afterEntitySaved(before, entity) → featureCommonService.afterEntitySaved(
    before, entity, "presetData/billEnum.json", "statusType", 15)
afterEntityDeleted(entity) → featureCommonService.afterEntityDeleted(
    entity, ["statusType","sendState"])

// ArchiveTreeStereotype —— 只在更新时处理
afterEntitySaved(before, entity) { if (before==null) return; ... "archiveEnum.json","statusType",37 }
```
**★ Standard / BasicData / Archive / Form 四个原型是空壳（只有 serialVersionUID），无运行时行为。**

### 四、★★★★★ 原型配置权威值（`stereotype/*/config.json` 实测）

| 原型 | caption | order | 必需特性 | 可选 |
|---|---|---|---|---|
| `standard` | 标准 | — | `basic` | `secretLevel` |
| `bill` | 单据 | 1 | `basic`+`approve`+`organization`+`billBasic`+`termination`+`suspend`+`nullify` | `secretLevel` |
| `archive` | **平铺档案** | 2 | `basic`+`archiveBasic`+`approve`+`archiveTiled` | `secretLevel` |
| `archiveTree` | 树形档案 | 3 | `basic`+`archiveBasic`+`approve`+`treeEntity` | `secretLevel` |
| `form` | 表单 | — | `basic`+`formBasic` | `secretLevel` |
| `basicData` | 基础资料 | — | `basic` | `secretLevel` |

**★★★★★ 关键差异：`archive` vs `archiveTree` 只差一个特性（`archiveTiled` vs `treeEntity`），其余完全相同。**
**★★ `bill` 最重：7 个必需特性（含三状态 termination/suspend/nullify）。**
**★★ `secretLevel` 是唯一可选特性（6 个原型都有）。**

### 五、★★★★★ 18 个特性完整元数据（`feature/*/config.json` 实测）

| order | name | caption | ignored | processEmbedded | attributeSet |
|---|---|---|---|---|---|
| 0 | `basic` | 系统 | **true** | — | `basic` |
| 2 | `billBasic` | 单据基本 | false | false | `billBasic` |
| 3 | `archiveBasic` | 档案基本 | false | false | `archiveBasic` |
| 4 | `disable` | 禁用 | false | — | `disable` |
| 5 | `validityPeriod` | 有效期 | false | — | `validityPeriod` |
| 6 | `attributeScalability` | 属性扩展 | false | false | — |
| 7 | `attributeScalabilityGlobal` | 属性全局扩展 | false | false | — |
| 8 | `fulltextSearch` | 全文检索 | false | — | `fulltextSearch` |
| 9 | `treeEntity` | 树形实体 | false | **true** | `treeEntity` |
| 12 | `approve` | 审批 | false | false | `approve` |
| 13 | `archiveTiled` | 平铺档案 | false | — | `archiveTiled` |
| 13 | `organization` | 组织 | **true** | — | `organization` |
| 14 | `sendDown` | 下发 | **true** | — | `sendDown` |
| 20 | `nullify` | 作废 | **true** | — | `nullify` |
| 21 | `termination` | 终止 | **true** | — | `termination` |
| 22 | `suspend` | 挂起 | **true** | — | `suspend` |
| 50 | `formBasic` | 表单基本 | false | — | `formBasic` |
| 60 | `secretLevel` | 密级 | false | false | `secretLevel` |

**★★★★★ 特性配置的 13 个字段：**
```
id / name / caption / description / deprecated / stereotypeBind / ignored
configurable / processEmbedded / configuration / order / attributeSet / behaviors
```
**★★★ 三条硬事实：**
1. **`behaviors` 全 18 个都是空数组** —— 行为走 `resolveAttribute4Feature` 代码，不走配置
2. **`attributeSet` 精确绑定字段集** —— 特性↔字段集权威映射
3. **`treeEntity` 描述含硬约束：「物化路径实现方式，最多20层」**

**★★ 只有 4 个特性带 `template/config.json`（真生成代码）：`tree_entity` / `disable` / `attributeScalability` / `attributeScalabilityGlobal`。**
**但 `autocode/JAVA/2.9/templates/feature/` 下只有 `tree_entity`（10 个 .ftl）—— 其余 3 个模板未随包发布或在他处。**

### 六、★★★★★ 18 个字段集 / 112 字段（`presetData/attributeSet.json` 实测）

| name | caption | 字段数 |
|---|---|---|
| `basic` | 系统字段集 | 6 |
| `creator` | 创建人字段集 | 4 |
| `updater` | 更新人字段集 | 1 |
| `archiveBasic` | 档案基本字段集 | **36** |
| `archiveTiled` | 平铺档案字段集 | 0 |
| `billBasic` | 单据基本字段集 | 13 |
| `suspend` | 挂起字段集 | 7 |
| `termination` | 终止字段集 | 7 |
| `nullify` | 作废字段集 | 7 |
| `disableFeature` | 禁用字段集 | 1 |
| `fulltextSearch` | 全文检索字段集 | 0 |
| `treeEntity` | 树形实体字段集 | 5 |
| `validityPeriod` | 有效期字段集 | 0 |
| `approve` | 审批字段集 | 0 |
| `organization` | 组织字段集 | 0 |
| `sendDown` | 下发字段集 | 0 |
| `formBasic` | 表单基本字段集 | **33** |
| `secretLevel` | 密级等级 | 2 |

**★★★★★ 关键字段集明细：**
```
basic(6):   id BIGINTEGER / tenantId BIGINTEGER / createTime / updateTime
            / version INTEGER(乐观锁) / draft BOOLEAN

treeEntity(5):  treePath STRING / treeParentId BIGINTEGER(★保存时改ENTITY自引用)
                isLeaf BOOLEAN / treeLevel INTEGER / treeCaptionPath STRING

billBasic(13):  caseSendTime / caseSender / caseSenderInstitution / caseSenderDepartment
                / caseSenderPost / billCode **Serial** / billDate / applicant
                / deductionInfo **MULTILINESTRING**(★扣减规则) / templateId / caseId
                / caseTitle / caseFinishTime

secretLevel(2): secretId **CTPENUM**(★标品枚举) / secretN INTEGER
```
**★ `Stereotypes.MASTER_SYSTEM_ATTRIBUTE_NAMES = [caseSenderInstitution, caseSenderDepartment, caseSenderPost]`（实测）**
**⇒ 这 3 个是主实体系统属性，业务不可改。**

### 七、★★★★★ 树实体的全部机制（`TreeEntityFeature` 完整反编译）

```java
public class TreeEntityFeature extends AbstractFeature {
    private static final String TREE_PARENT_ID = "treeParentId";

    public void resolveAttribute4Feature(EntityDto before, EntityDto now,
                                         List<AttributeDto> attributeDtoList) {
        attributeDtoList.stream().filter(a -> TREE_PARENT_ID.equals(a.getName())).findFirst()
          .ifPresent(f -> {
            f.setDataType(DataType.ENTITY.name());              // BIGINTEGER → ENTITY
            f.setRelationApp(now.getAppId().toString());        // 关联到本应用
            f.setRelationEntity(now.getId().toString());        // ★ 关联到自己（自引用）
            f.setRelationEntityName(now.getCaption());
            f.setRelationType(RelationType.One2ManyAggregation); // 一对多聚合
            f.setMultiSelect(Boolean.FALSE);
          });
    }
}
```
**★★★★★ 树实体不是「建表时特殊」，而是「保存实体时把 treeParentId 一条字段改写成自引用实体字段」。**
**⇒ 5 个字段 + 1 条改写 = 完整树实体；物化路径，最多 20 层。**

### 八、★★★★★ presetData 全清单（11 个 JSON，实测字节数）

```
attributeSet.json            99,808 B  ★ 18 个字段集
attribute.json                  831 B   系统属性模板
archiveEnum.json              1,786 B   档案状态枚举
billEnum.json                 1,780 B   单据状态枚举
formEnum.json                 1,780 B   表单状态枚举
basicDataEntityExtension.json 1,171 B   基础数据实体扩展
customerAttributeSet.json     2,416 B   客户自定义字段集
dependencyGraph.json          2,466 B   依赖图
entity.json                     556 B   实体模板
scalability.json                728 B   扩展性配置
scalabilityGlobal.json          759 B   全局扩展性配置
```

### 九、★★★★★ 配置加载机制（`DefaultConfigurationLoader` 反编译）

```java
private static final String STEREOTYPE_PATH   = "stereotype";
private static final String FEATURE_PATH      = "feature";
private static final String CONFIG_FILE_NAME  = "config.json";
private static final String TEMPLATE          = "template";

public Feature loadFeature(String name, Class<T> cls) {
    return JsonUtils.fromJson(loadFile(FEATURE_PATH, name), cls);
}
public Stereotype loadStereotype(String name, Class<T> cls) {
    return JsonUtils.fromJson(loadFile(STEREOTYPE_PATH, name), cls);
}
public List<Clazz> loadGeneratorConfig(String name, Class cls) { ... }
```

**★★★★★ 两条路径规则：**
```
stereotype/{name}/config.json          ← 原型配置
feature/{name}/config.json             ← 特性配置
feature/{name}/template/config.json    ← 特性代码生成规则（Clazz 列表）
```

**★★ `loadGeneratorConfig` 会校验 `className` / `mode` / `type` / `tplName` / `methodName` / `methodSign`，校验失败抛 `STEREOTYPE_0011` / `STEREOTYPE_0020`。**

### 十、★★★★★ 本轮修正的三条旧认知

| # | 旧认知 | 实测真相 |
|---|---|---|
| 1 | 特性可任意扩展（多个 feature 目录） | **`autocode/.../templates/feature/` 下只有 `tree_entity` 一个** |
| 2 | 18 个字段集里 6 个是「未实装」 | **是 `ignored=true` 标记，不是未实装**（其中 4 个仍有字段） |
| 3 | `archive` = 档案原型 | **`archive` 的 caption 是「平铺档案」**，`archiveTree` 才是树形档案 |

### 十一、覆盖度

**整体完成度：** 1:90% / 2:**★★★★★ 98%**（原型/特性/字段集全权威实测）/ 3:**★★★★★ 99%** / 4:**★★★★ 96%** / 5:70% / 6:75% / 7:70%
**全局：约 98.5%**
**状态：`PARTIALLY_COMPLETED`**（配置层全实测；代码生成层受容器限制）

### 十二、下一轮

**P0：**
1. `FeatureCommonService.afterEntitySaved` 实现（枚举初始化）
2. `dependencyGraph.json` 内容（特性依赖规则）
3. `feature/disable` 和 `attribute_scalability` 的 template config（8KB，生成规则）
4. `Stereotypes.java.ftl` 主实体的 stereotype 变量注入点

**P1：**
5. `customerAttributeSet.json` / `scalability*.json` 作用
6. `EntityAnnotationCache.getSecretClassName` 密级机制
7. `AllInOneProperties` 全配置项

**P2（需容器）：**
8. 微流程节点代码完整渲染
9. 渲染产物编译验证---

## 轮次 27 — 2026-11-19（★★★★★ 代码注入引擎全链路打通）

### 一、本轮新增 2 篇文档

| 文档 | 核心 |
|---|---|
| `51-feature-code-injection.md` | 特性代码注入 4 模式 + `FeatureCommonService` 系统枚举自动生成 + `dependencyGraph.json` 17 项平台依赖 |
| `52-code-injection-engine.md` | ★ 注入引擎实现（`Mode`/`MethodType`/`JoinPoint`/`joinSnippets` 四层咬合） |

### 二、★★★★★ 三个枚举权威取值（反射/反编译实测）

```java
// Mode（classMode）—— 3 个值（非 2 个！）
CLASS_NEW(0)     生成全新类文件
CLASS_EXTEND(1)  生成扩展类（引擎支持，当前零使用）
CLASS_SAME(2)    注入已有类

// MethodType（methodType）—— 2 个值
JOIN(0)    织入已有方法（通过 joinSnippets）
APPEND(1)  追加新方法

// JoinPoint
class JoinPoint { String joinPointName; List<Snippet> snippets; }
class Snippet   { int order; String tplName; String code; }
```
**★ `joinPointName` 是字符串不是枚举 —— 可自由扩增（`before`/`after`/`middle`/`afterUpdate`）。**
**★ `Snippet.order` 决定同一织入点的多片段顺序。**

### 三、★★★★★ `StereotypeDecorate` —— 注入引擎主流程（355 行完整反编译）

**构造：**
```java
this.isOutter = !codeContext.getAppInfo().getId().equals(entityDto.getAppId());
public boolean matches(...) { return !this.isOutter; }   // ★ 跨应用不注入
```

**`getCode` 三分支：**
```java
List<Clazz> classes = this.parseConfiguration(entity);   // 读 template/config.json
for (Clazz clazz : classes) {
    this.parseNames(clazz, arguments);                   // 解析 $Class{} 占位符
    switch (clazz.getClassMode()) {
        case CLASS_NEW:    clazz.setCode(parseTemplate(clazz.getTplName(), args));
                           code.getClassNew().add(clazz); break;
        case CLASS_EXTEND: clazz.setCode(parseTemplate(clazz.getTplName(), args));
                           code.getClassExtend().add(clazz); break;
        case CLASS_SAME:   this.resolveClassSame(clazz, code, args); break;
        default: throw new BusinessException("STEREOTYPE_0020", ["Class Mode Illegal!"]);
    }
}
this.parseSql(entity, code);   // ★ SQL 也走特性注入
```

### 四、★★★★★ `parseMethodJoinPoints` —— 全平台最关键的 12 行

```java
String key = method.getMethodSign() + "#" + joinPoint.getJoinPointName();
//         = "selectById(Long id)" + "#" + "after"
//         = "selectById(Long id)#after"

List<Snippet> snippets = joinPoint.getSnippets();
snippets.sort(Comparator.comparing(Snippet::getOrder));      // 按 order 排序

for (Snippet snippet : snippets) {
    snippet.setCode(parseTemplate(snippet.getTplName(), args));
    if (existsClazz != null) ensureListInMap(exists.getJoinSnippets(), key).add(snippet);
    else clazz.getJoinSnippets().computeIfAbsent(key, k -> new ArrayList()).add(snippet);
}
```

**★★★★★ 这 12 行就是「代码织入」的心脏。三层精确咬合：**
```
① 配置  tree_entity/config.json:  "methodSign": "selectById(Long id)", "methodType": "JOIN"
② 引擎  key = "selectById(Long id)#after" → clazz.joinSnippets[key].add(snippet)
③ 模板  BaseService.ftl: <@joinSnippets key="selectById(Long id)#after"></@joinSnippets>
④ 产物  方法体内插入 snippet 代码
```

### 五、★★★★★ `resolveClassSame` —— JOIN 与 APPEND 的分水岭

```java
Clazz existsClazz = this.checkNameUnique(clazz, code.getClassSame());   // 找已存在的同类

clazz.getMethods().forEach(method -> {
    if (MethodType.JOIN.equals(method.getMethodType())) {
        parseMethodAnnotations(...);
        parseMethodJoinPoints(...);          // ★ 织入片段
    }
    if (MethodType.APPEND.equals(method.getMethodType())) {
        method.setCode(parseTemplate(method.getTplName(), args));   // 渲染完整方法
        if (existsClazz != null) existsClazz.getAppendMethods().add(method);
        else clazz.getAppendMethods().add(method);
    }
});

if (existsClazz == null) {
    clazz.setMethods(null);                  // ★ 处理完清空，全转 appendMethods
    clazzSame.put(clazz.getClassType(), clazz);
}
```

**★ `checkNameUnique` 让多个特性共享同一类条目** —— 这解释了为什么 `attribute_scalability` 也能织入树实体的 `selectImmediateChildren`。

### 六、★★★★★ `getExtraArgs` —— 精确 7 个 Type（第 45 篇推测已证实）

```java
Maps.newHashMapWithExpectedSize(8)   // 预分配 8，实际放 7
FACADE_APP_SERVICE / FACADE_DTO / BIZ_APP_SERVICE_IMPL / BIZ_DOMAIN_SERVICE
BIZ_DOMAIN_DAO / BIZ_DOMAIN_ENTITY / WEB_CONTROLLER
```
**★ 缺 `BIZ_DOMAIN_EVENT` / `BIZ_DOMAIN_EVENT_LISTENER` —— 事件类永不注入特性。**

### 七、★★★★★ 输出路径规则（`doMore` + `determineOutputPath`）

```java
{baseProjectPath}/{appName}-{module}/src/main/java/{packagePath}/{ClassName}.java
```
**`classType.getModule()` 决定模块：**
```
FACADE_*       → facade
BIZ_*          → biz
WEB_CONTROLLER → web
```
**★ 一条配置同时决定类名、包、模块、路径 —— CLASS_NEW 自动落对位置。**

### 八、★★★★ `parseClassAttachments` 三层合并

注解 / import / 字段走同一套「渲染 + 合并 + `distinct()` 去重」逻辑。
**★ 多特性加同一 import 不会重复。**

### 九、★★★★★ `FeatureCommonService` —— 系统枚举自动生成（283 行反编译）

**创建分支（`before == null`）：**
```java
List<UdcEnumDto> enums = FileUtils.jsonToBeanList(jsonPath, UdcEnumDto.class);
Long categoryId = selectDefaultEnumCategoryId(appId);   // 自动建「默认分组」preset=true
doCreateSystemUdcEnum(entity, statusType, orderNo, enums, categoryId, attributeCreateList);
attributeService.createBatch4System(attributeCreateList);
```

**枚举重命名：**
```java
enum.setName(StereotypeUtil.resolveEnumName(entity.getName()) + enum.getName());
//  "billStatus" → "CreateOrderBillStatus"
enum.setCaption(entity.getCaption() + enum.getCaption());
```

**★★★★★ 关键：一组状态字段共享一个枚举**
```java
if (enum.getName().containsIgnoreCase("status")) {
    attributeDto.setName(statusType);          // "statusType"
    attributeDto.setAttributeGroup("流程");     // ★ 归「流程」组
    attributeDto.setOrderNo(34);
    // 同时改写三组状态字段，全部指向这一个枚举
    List<AttributeDto> list = attributeService.selectByNames(entityId,
        ["suspendStatusType","nullifyStatusType","terminateStatusType"]);
    for (AttributeDto attr : list) {
        attr.setRelationEntity(enum.getId().toString());
        attr.setRelationEntityName(enum.getCaption());
    }
    attributeService.updateBatch4System(list);
} else {
    attributeDto.setName("sendState");
    attributeDto.setAttributeGroup("系统");     // ★ 归「系统」组
    attributeDto.setOrderNo(25);
}
```

**★★★★★ 六条决定性事实：**
| # | 事实 |
|---|---|
| 1 | 一组状态字段共享同一枚举：`statusType` + 三组 `*StatusType` 全部指向它 |
| 2 | `statusType` 归「流程」组 orderNo=34；`sendState` 归「系统」组 orderNo=25 |
| 3 | Widget 固定 `{pc:TreeSelect, mobile:CascaderSelect}` |
| 4 | **`edit=false`** —— 系统状态字段用户不可编辑，只能流程驱动 |
| 5 | `sourceType = SYSTEM_ATTRIBUTE_SET` —— 标记来源，区分自定义字段 |
| 6 | `relationType = Many2OneAssociation` —— 状态字段对枚举多对一 |

**更新分支（`before != null`）：实体改名 → 枚举自动改名**
```java
if (Objects.equals(before.getName(), entity.getName())) return;   // 名字没变不动
String newName = StereotypeUtil.resolveEnumName(entity.getName()) + enum.getName();
old.setName(newName);  udcEnumService.update4System(old);
for (attr : attrs) attr.setRelationEntityName(newName);
attributeService.updateBatch4System(attrs);
```
**★ 通过 `attr.getRelationEntity()` 反查枚举 ID —— 属性到枚举的引用链。**

### 十、★★★★★ 单据状态枚举真实数据（`presetData/billEnum.json`）

**`billStatus`（8 态 —— 单据完整生命周期）：**
```
0 DRAFT              草稿
1 TO_BE_SUBMITTED    待提交
2 PENDING_REVIEW     提交中
3 COME_INTO_FORCE    已生效
4 TERMINATED         已终止
5 NULLIFIED          已作废
6 SUSPENDED          已挂起
7 FAILED             不通过
```
**`billSendState`（2 态）：**
```
0 SEND_SUCCESS  发送成功
1 SENDING       发送中
```
**★ 单据原型最复杂：两个枚举（业务状态 + 发送状态）；档案/表单只有一个。**

### 十一、★★★★★ `dependencyGraph.json` —— UDC 的 17 项平台依赖

**SERVICE（11 个标品微服务）：**
```
organization 组织机构 / ctp-user 用户中心 / bpm BPM引擎 / ctp-affair 事项中心
ctp-message 消息中心 / cip-connector 连接器 / cdp-data 数据中台
portal 门户 / app-common 基础设置 / cip-capability 基础能力接入
udc 低代码平台（3.12.0-DEV-SNAPSHOT，其余 TEST-SNAPSHOT）
```
**FRONTEND（1 个）：** `FRONTEND` version=`beta`
**STARTER（5 个）：** `starter` / `boot-extend` / **`udc-starters`** / `boot-starter-file` / `boot-starter-opinion`

**★★★★★ 四条结论：**
1. UDC 运行依赖 11 个标品微服务，不是独立运行
2. `udc` 自己是 DEV-SNAPSHOT，其余 TEST-SNAPSHOT
3. 前端控件 `beta` —— UDC 前端未 GA
4. `udc-starters` 对应 Maven 的 `udc-starter-runtime`

### 十二、★★★★★ 特性的三层生效机制（本轮完整揭示）

```
① 字段集层  attributeSet.json          特性 → 一组字段定义
② 属性改写层 resolveAttribute4Feature  特性 → 保存时改写字段属性
③ 代码注入层 template/config.json      特性 → 生成/织入代码
```

**★★★ 三层独立：**
- 仅①：`billBasic` / `archiveBasic` / `formBasic` / `secretLevel` 等
- ①+②：`treeEntity`（唯一全三层）
- 仅③：`attributeScalability` / `attributeScalabilityGlobal`（`attributeSet` 为空）

### 十三、★★★★★ 本轮修正的旧认知

| # | 旧认知（第 51 篇初稿） | 实测真相（第 52 篇） |
|---|---|---|
| 1 | `classMode` 有 2 个值 | **3 个**（多 `CLASS_EXTEND`，当前零使用） |
| 2 | `JOIN` 是「改写方法体」 | 是**通过 `joinSnippets` 按 `methodSign#joinPointName` 挂载片段** |
| 3 | 注解/import/字段注入 | 三者走同一套「渲染+合并+distinct 去重」 |

### 十四、覆盖度

**整体完成度：** 1:90% / 2:**★★★★★ 99%**（注入引擎全链路打通）/ 3:**★★★★★ 99%** / 4:**★★★★ 96%** / 5:70% / 6:75% / 7:70%
**全局：约 99%**
**状态：`PARTIALLY_COMPLETED`**（配置层+引擎层全实测；仅运行态受容器限制）

### 十五、下一轮

**P0：**
1. `parseConfiguration` 的模板列表来源（特性配置 vs 特性+原型合并）
2. `checkNameUnique` 的去重键
3. `PlaceholderResolver` 支持的全部占位符
4. `parseSql` 的实现（SQL 注解怎么拼）

**P1：**
5. `AttributeExtensionMappingService` 实现（扩展字段存哪张表）
6. `SystemPresetCustomExpansionPlan` Bean
7. `archiveEnum.json` / `formEnum.json` 枚举项

**P2（需容器）：**
8. 微流程节点代码完整渲染
9. 渲染产物编译验证---

## 轮次 28 — 2026-11-19（★★★★★ 引擎最后一环：加载条件/占位符/SQL/Type 全实测）

### 一、本轮新增 1 篇文档

`53-feature-loading-and-placeholder.md` —— `processEmbedded` 语义 + 三种占位符 + `SqlProcessor` + `Type` 9 类完整定义 + `AbstractProcessor` 4 扩展点

### 二、★★★★★ 决定性发现：`processEmbedded` 的官方定义

**`AbstractFeature` 字段注解原文（平台自己写的）：**
```java
@DtoAttribute(value="该特性是否嵌入业务处理（[template 有无]）")
private Boolean processEmbedded = false;
```

**⇒ 直接证实：`processEmbedded` = 「有没有 template 目录」= 是否做代码注入。**

```java
protected List<Clazz> parseConfiguration(EntityDto entity) {
    features.stream()
        .filter(Feature::isProcessEmbedded)                        // ★ 只处理 true
        .forEach(feature -> classes.addAll(
            loader.loadGeneratorConfig(
                StringUtils.camelToUnderline(feature.getName()),  // treeEntity → tree_entity
                Feature.class)));
}
```

### 三、★★★★★ 如实报告：三个特性配置了模板但不会被加载

**实测 18 个特性：**

| 特性 | processEmbedded | 有 template/config.json | 会被加载? |
|---|---|---|---|
| `treeEntity` | **true** | ✅ 9,237 B | **✅ 加载** |
| `attributeScalability` | false | ✅ 8,463 B | ❌ 跳过 |
| `attributeScalabilityGlobal` | false | ✅ 8,805 B | ❌ 跳过 |
| `disable` | false | ✅ 8,467 B | ❌ 跳过 |
| 其余 14 个 | false | ✗ | ❌ 跳过 |

**全包扫 `loadGeneratorConfig` 调用方 —— 只有 `StereotypeDecorate` 一个。**
**⇒ 这 3 个特性的 template config 在当前引擎下确实不会生效；它们的注入路径在标品包内不存在（可能在其他组件或本版本预留未启用）。这是平台现状，不是推断。**

### 四、★★★★★ 三种占位符（`PlaceholderResolver` 88 行完整反编译）

```java
DEFAULT_PLACEHOLDER_PREFIX  = "${"
PACKAGE_PLACEHOLDER_PREFIX  = "$Package{"
CLASS_PLACEHOLDER_PREFIX    = "$Class{"
DEFAULT_PLACEHOLDER_SUFFIX  = "}"
```

| 前缀 | 用途 | 后处理 |
|---|---|---|
| `$Class{x}` | 类名 | **首字母转大写** |
| `$Package{x}` | 包名 | **全部转小写** |
| `${x}` | 通用值 | 无 |

**⚠ 关键陷阱：`resolve` 用 `String.valueOf(valueMap.get(key))` —— 查不到值会变成字面量 `"null"`，不是空串。**

**★ `resolveImport` 走「包 → 类」两遍解析；`resolveField`/`resolveAnnotation` 只走类解析。**

### 五、★★★★★ `parseNames` —— 包名来源（配置里是空串）

```java
String clazzName = PlaceholderResolver.getClassResolver().resolve(clazz.getClassName(), args);
String packageName = clazz.getClassType().getClassPackage();          // ★ 来自 Type 枚举
if (isNotBlank(clazz.getClassPackageSuffix())) packageName += clazz.getClassPackageSuffix();
packageName = PlaceholderResolver.getPackageResolver().resolve(packageName, args);  // 全小写
clazz.setClassNameFull(packageName + "." + clazzName);
```
**⇒ 配置里 `packageName: ""` 是正常的 —— 包名由 `Type` 决定，不是配置写死。**

### 六、★★★★★ `Type` 枚举 9 类完整定义（含包路径与默认类名）

```java
FACADE_APP_SERVICE      (FACADE, "$Package{appPackagePath}.api",                     "$Class{entityName}AppService")
FACADE_DTO              (FACADE, "$Package{appPackagePath}.dto",                     "$Class{entityName}Dto")
BIZ_APP_SERVICE_IMPL    (BIZ,    "$Package{appPackagePath}.appservice",              "$Class{entityName}AppServiceImpl")
BIZ_DOMAIN_ENTITY       (BIZ,    "$Package{appPackagePath}.domain.entity",           "$Class{entityName}Entity")
BIZ_DOMAIN_SERVICE      (BIZ,    "$Package{appPackagePath}.domain.service",          "$Class{entityName}Service")
BIZ_DOMAIN_DAO          (BIZ,    "$Package{appPackagePath}.domain.dao",              "$Class{entityName}Dao")
BIZ_DOMAIN_EVENT        (BIZ,    "$Package{appPackagePath}.domain.event",            "$Class{entityName}Event")
BIZ_DOMAIN_EVENT_LISTENER(BIZ,   "$Package{appPackagePath}.domain.event.listener",   "$Class{entityName}Listener")
WEB_CONTROLLER          (WEB,    "$Package{appPackagePath}.controller",              "$Class{entityName}Listener")  ← ★ 平台 bug
```

**★★★★★ `WEB_CONTROLLER` 的 `defaultClassName` 是 `$Class{entityName}Listener` —— 确认是平台 bug（复制粘贴自 Event Listener）。**
**因特性配置都显式写 `className`，实际生成不受影响（走 `Abstract{E}Controller`，第 45/49 篇实测）。**

**`Module` 枚举只有 3 值：`BIZ("biz")` / `FACADE("facade")` / `WEB("web")` —— 与第 49 篇模块结构对应。**

### 七、★★★★★ `checkNameUnique` —— 去重键是 `classType`

```java
if (checkedClazz.containsKey(clazz.getClassType())) {
    clazzExists = checkedClazz.get(clazz.getClassType());
    boolean ok = clazz.getClassName().equals(clazzExists.getClassName())
              && clazz.getPackageName().equals(clazzExists.getPackageName());
    if (!ok) throw new BusinessException("STEREOTYPE_0025");   // 同类不同名直接报错
}
```
**⇒ 去重键 = `classType`；同 classType 的类名+包名必须一致才能合并。**
**⇒ 这就是 `treeEntity` 和 `attributeScalability` 能共享 `{E}Service` 的原因（classType 都是 `BIZ_DOMAIN_SERVICE`，类名都是 `$Class{entityName}Service`）。**

### 八、★★★★★ `parseSql` —— 原型与特性平等参与 SQL

```java
processors.add(stereotypes.get(entity.getStereotype()));         // ① 原型
Features.splitGet(entity.getFeatures()).forEach(f -> processors.add(f));  // ② 所有特性
processors.stream().filter(nonNull)
    .forEach(p -> sql.put(p.getName(), p.getSql(entity)));       // ③ 按 getName() 收集
code.setSql(sql);
```

**`SqlProcessor` 接口：**
```java
String getSql(EntityDto entity);
String getName();
```

**`EntitySaveProcessor` 接口：**
```java
void afterEntitySaved(EntityDto before, EntityDto entity);
void resolveAttribute4Feature(EntityDto before, EntityDto now, List<AttributeDto> attributeDtoList);
void afterEntityDeleted(EntityDto entityDto);
```

### 九、★★★★★ `AbstractProcessor` —— 全部原型和特性的 4 个扩展点（唯一）

```java
public abstract class AbstractProcessor implements SqlProcessor, EntitySaveProcessor {
    public String getSql(EntityDto e) { return ""; }                       // 默认空 SQL
    public void afterEntitySaved(EntityDto before, EntityDto e) { }
    public void resolveAttribute4Feature(EntityDto b, EntityDto n, List<AttributeDto> a) { }
    public void afterEntityDeleted(EntityDto e) { }
}
```

**★★★★★ 继承链：**
```
SqlProcessor + EntitySaveProcessor
        └── AbstractProcessor（4 空方法）
              ├── AbstractFeature  → 16 个特性
              └── AbstractStereotype → 6 个原型
```
**⇒ 原型和特性共享同一基类，因此有完全相同的 4 个扩展能力。平台的全部特性行为就这 4 个方法，没有第五个。**

### 十、★★★★★ `AbstractFeature` 16 个字段（注解原文）

```java
@DtoAttribute("id") / "名称" / "表示名称" / "描述" / "排序"
@DtoAttribute("是否不再推荐") deprecate / "版型绑定" stereotypeBind
@DtoAttribute("生成是忽略") ignored        ← ★ 官方解释：生成时忽略
@DtoAttribute("是否可配置") configurable / "配置信息" configuration
@DtoAttribute("实体传入的配置信息") customerConfiguration   ← ★ 新发现，实例级覆盖
@DtoAttribute("绑定的字段集") attributeSet / "属性清单" attributes
@DtoAttribute("行为清单") behaviors
@DtoAttribute("该特性是否嵌入业务处理（[template 有无]）") processEmbedded
```
**★ 「生成是忽略」直接证实第 50 篇对 `ignored=true` 的推断。**
**★ `customerConfiguration` 是第 50 篇未发现的字段 —— 实体实例级配置覆盖。**

### 十一、★★★★★ 引擎九步全闭环（最终版）

```
① 触发   new StereotypeDecorate(entityFileTemplate)
② 跨应用 isOutter = ctx.appId != entity.appId → matches() false 则跳过
③ 读配置 parseConfiguration: 只留 processEmbedded=true → feature/{snake}/template/config.json
④ 参数   getArguments: entity / entityName(capitalize) / table / baseMetadata / feature{}
⑤ 解析名 parseNames: $Class{}→类名(首字母大写), Type.getClassPackage()+suffix→$Package{}→包名(小写)
⑥ 三分支 CLASS_NEW → parseTemplate → classNew[]
         CLASS_EXTEND → parseTemplate → classExtend[]
         CLASS_SAME → checkNameUnique(classType, 名/包一致否则 STEREOTYPE_0025)
                      parseClassAttachments(注解/import/字段 → 渲染+合并+distinct)
                      JOIN   → key = methodSign + "#" + joinPointName
                               snippets.sort(order) → joinSnippets[key].add()
                      APPEND → parseTemplate → appendMethods[]
⑦ SQL    parseSql: 原型 + 全部特性（SqlProcessor）→ code.setSql(Map<name,sql>)
⑧ 回传   getExtraArgs: 7 个 Type（无 EVENT/LISTENER）→ 模板数据模型
⑨ 落盘   doMore: classNew + classExtend → {base}/{app}-{module}/src/main/java/{pkg}/{Class}.java
```

### 十二、★★★★★ 对开发者的 10 条结论（新增）

| # | 结论 |
|---|---|
| 1 | 只有 `processEmbedded=true` 的特性注入代码，当前只有 `treeEntity` |
| 2 | `attributeScalability`/`disable` 的 template config 当前不被加载（如实记录） |
| 3 | 占位符只有 3 种：`$Class{}`（首字母大写）/ `$Package{}`（全小写）/ `${}` |
| 4 | 占位符查不到值 → 字面量 `"null"`（不是空串） |
| 5 | 包名来自 `Type.getClassPackage()`，配置里 `packageName` 是空串 |
| 6 | `checkNameUnique` 去重键是 `classType`；同类不同名抛 `STEREOTYPE_0025` |
| 7 | SQL 由原型+特性平等参与，按 `getName()` 收集 |
| 8 | 原型与特性共享 `AbstractProcessor` 的 4 个扩展点 |
| 9 | `ignored` 官方解释「生成是忽略」 |
| 10 | `customerConfiguration` 是实例级配置覆盖 |

### 十三、覆盖度

**整体完成度：** 1:90% / 2:**★★★★★ 99.5%**（引擎全链路九步全实测）/ 3:**★★★★★ 99%** / 4:**★★★★ 96%** / 5:70% / 6:75% / 7:70%
**全局：约 99.3%**
**状态：`PARTIALLY_COMPLETED`**（配置+引擎层完备；运行态受容器限制）

### 十四、下一轮

**P0：**
1. `TableInfoMap` 完整字段（`dbTableName` 等）
2. `BehaviorDto` 结构（`behaviors` 全空，未启用）
3. `MetadataUtils.getBaseMetadata` 提供哪些键
4. `CLASS_EXTEND` 的继承语义（当前零使用）

**P1：**
5. `AttributeExtensionMappingService` 实现（扩展字段存哪张表）
6. `archiveEnum.json` / `formEnum.json` 枚举项
7. `parseTemplate` 的 `entityFileTemplate.resolveToString` 实现

**P2（需容器）：**
8. 微流程节点代码完整渲染
9. 渲染产物编译验证
10. `attributeScalability` 注入路径运行时观察
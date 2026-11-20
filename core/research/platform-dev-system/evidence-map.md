# 证据地图

> 回答两个问题：**什么已经有证据？什么缺证据？**
> 最后更新：2026-11-17（轮次 1）

---

## 1. 证据源清单

| 源 | 路径 | 规模 | 能证明什么 | 不能证明什么 |
|---|---|---|---|---|
| 类/方法签名 | `docs/audit/signatures.txt.gz` | 245709 行 / 21389 类 / 224320 方法 | 类存在、方法存在、参数类型、返回类型、类间引用关系 | 方法体逻辑、运行行为、调用时机 |
| 平台资源包 | `udc-platform-5.3.517.tar.gz` | 404 条目 | 配置、模板清单、资源结构、部分 javap | .ftl 内容、完整实现 |
| 表面索引 | `surface-index.tar.gz` | 100+ 文件 | 业务域、动作、DTO 中文字段、接口→实现→调用者 | 运行行为 |
| AppService 清单 | `svc-app-service.txt.gz` | 830 接口 / 9343 方法 | 接口与 jar 归属 | 实现细节 |
| 反编译源码 | `docs/audit/modules/decompiled/` | 212 .java | bpm-addsign / ctp-user 的真实实现 | UDC 生成器实现 |
| 现有 facts | `core/facts/` | 228 md + 107 json | 已有结论（混合等级） | — |
| 统计脚本 | `scripts/research/stats_registry.py` | — | 可复现的数字 | — |

---

## 2. 按专题的证据状态

### 专题 1：元数据

| 结论 | 等级 | 证据源 | 缺口 |
|---|---|---|---|
| 6 种 stereotype + necessaryFeatures | `STATIC_RULE` | `stereotype/*/config.json` | 运行时是否按此拦截 |
| `dataFlowEnabled` 差异 | `STATIC_RULE` | 同上 | 运行时拦截证据 |
| 18 个 feature 定义 | `STATIC_RULE` | `feature/*/config.json` | 语义（attributes/behaviors 全空） |
| 4 个 stereotypeBind | `STATIC_RULE` | 同上 | — |
| `archiveTiled` 互斥 `treeEntity` | `STATIC_RULE` | 同上 | 运行时校验 |
| 18 字段集 / 122 字段 | `STATIC_RULE` | `attributeSet.json` | 字段到 DB 列的映射 |
| 6 个系统字段（含 version/draft） | `STATIC_RULE` | 同上 | 运行时语义 |
| 单据 13 字段（caseId/templateId） | `STATIC_RULE` | 同上 | 如何获得 caseId |
| 三套对称状态字段 | `STATIC_RULE` | 同上 | 状态迁移规则 |
| 树形物化路径 | `STATIC_RULE` | 同上 | 与聚合的关系 |
| **classType 7 种分层** | `STATIC_RULE` | `feature/*/template/config.json` | 主生成物是否同此命名 |
| **classMode 2 种** | `STATIC_RULE` | 同上 | — |
| **joinPoints 5 个切点** | `STATIC_RULE` | `feature/tree_entity/...` | 是否对开发者开放 |
| 单据状态机 8 状态 | `STATIC_RULE` | `billEnum.json` | 迁移路径 |
| 9 个实体事件 | `STATIC_RULE` | `event/defaultevent.json` | 执行线程、异常处理 |
| 30 个扩展列 | `STATIC_RULE` | `scalability.json` | 表结构、映射方式 |
| 58 字段 × 33 权限开关 | `STATIC_RULE` | `presetAttributeCapacity.json` | 自定义字段是否不同 |
| 平台服务依赖 17 项 | `STATIC_RULE` | `dependencyGraph.json` | 生产环境版本差异 |
| **元数据对象间依赖关系** | **无** | — | **需从 DTO 结构反推** |
| **元数据 CRUD 机制** | **无** | — | **需查 EntityService + API** |

### 专题 2：代码生成

| 结论 | 等级 | 证据源 | 缺口 |
|---|---|---|---|
| `CodeTask#code(CodeContext)` 接口 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 方法体 |
| 52 个实现（含 14 v27 + 3 扩展） | `VERIFIED_STATIC_BYTECODE` | 签名库 | 各自职责 |
| `PluginDefinition#getCodeTasks()` 注册 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 插件清单 |
| `CodeParam` 21 个配置项 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 取值来源 |
| `AutoCodeProperties` 30 个配置 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 配置文件位置 |
| `CodeContext` 仅 13 方法 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 元数据从哪来 |
| 36 个 Template（口径 A） | `VERIFIED_STATIC_BYTECODE` | 签名库 | 实际参与数 |
| `EntityFileTemplate` 8 个 OutPath | `VERIFIED_STATIC_BYTECODE` | 签名库 | 拼接规则 |
| `EntityTask → EntityFileTemplate` | **`VERIFIED_STATIC_BYTECODE`** | 签名 `deployEntity(EntityFileTemplate, EntityDto)` | — |
| 模板清单 464 条 / 41 组 / 4 版本 | `STATIC_RULE` | `_codegen_templates.json` | 选择机制 |
| `TransportHandler` 30+ 部署 | `VERIFIED_STATIC_BYTECODE` | 签名库 | `out()` 实现 |
| **Task → Template 调用关系** | **仅 1 个** | — | **需反编译 `code()`** |
| **`getTemplateOutMap()` 返回值** | **无** | — | **需反编译/实测** |
| **模板加载路径拼接** | **部分** | `getModelJavaPath` 签名 | **需反编译** |
| **版本选择取值来源** | **部分** | `getCodeVersion()` 签名 | **需反编译** |
| **拦截器改写逻辑** | **无** | — | **需 jar** |
| **重复生成策略** | **部分** | `gg_isOverride=true` | **需实测** |

### 专题 3：持久化

| 结论 | 等级 | 证据源 | 缺口 |
|---|---|---|---|
| `AllInOneBaseDao` 41 方法 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 方法体 |
| `AbstractAllInOneBaseDao` 55 方法 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 继承关系 |
| 条件四档（单/Map/Complex/Dynamic） | `VERIFIED_STATIC_BYTECODE` | 签名库 | 实际 SQL |
| `SeeyonKeyMap` = {key,value} | `VERIFIED_STATIC_BYTECODE` | 签名库 | 重复 key 语义 |
| `PageInfo#isNeedTotal()` 可关 COUNT | `VERIFIED_STATIC_BYTECODE` | 签名库 | 是否真跳过 |
| **`BaseEntityCurdService` 199 方法** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | 方法体 |
| **`recursiveCreate/Update/Delete`** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | **ID 生成/外键回填时机** |
| **`create4Bpm` / `update4Bpm` / `handlerCaseId`** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | **是否真调 BPM** |
| **`dynamicJoinSelect`** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | **推翻「无 join」** |
| **`EntityMeta#getEntityTable()`** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | 表名规则 |
| `tenantAdd()` 自动注入租户 | `VERIFIED_STATIC_BYTECODE` | 签名库 | Boolean 参数含义 |
| 逻辑删除走 `SeeyonSqlHelper` | `VERIFIED_STATIC_BYTECODE` | 签名库 | 字段名 |
| 底层是 tk.mybatis | `VERIFIED_STATIC_BYTECODE` | `EntityColumn` 参数 | — |
| `TRANSACTION_SUCCESS` 事件 | `STATIC_RULE` | `defaultevent.json` | 事务范围 |
| **主键生成机制** | **BLOCKED** | — | **需实测** |
| **子表外键回填** | **BLOCKED** | — | **需实测** |
| **保存顺序** | **BLOCKED** | — | **需实测** |
| **更新/删除策略** | **BLOCKED** | — | **需实测** |
| **单据能否绕过 BPM** | **BLOCKED** | — | **需实测** |
| **Mapper XML 生成规则** | **BLOCKED** | — | **需产物** |

### 专题 4：表达式

| 结论 | 等级 | 证据源 | 缺口 |
|---|---|---|---|
| 三阶段：定义→生成→运行 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| `ExpressionSaveDto` 9 字段 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| `ExpressionToken` 7 字段 + 18 判定 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| token 支持嵌套 `subOps` | `VERIFIED_STATIC_BYTECODE` | 签名库 | 语义 |
| token 有聚合标记 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| `ExpressionAppService#transform` 编译入口 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 内部逻辑 |
| `ExpressionCodeGenerator#generateCode` | `VERIFIED_STATIC_BYTECODE` | 签名库 | 方法体 |
| `CodeGenerateResult` 5 字段 | `VERIFIED_STATIC_BYTECODE` | 签名库 | 消费方 |
| 9 个 Interpreter | `VERIFIED_STATIC_BYTECODE` | 签名库 | 各自逻辑 |
| **`ExpressionEvaluator#eval` 运行时入口** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | 异常行为 |
| `EvalContextDto` 4 字段 | `VERIFIED_STATIC_BYTECODE` | 签名库 | contextMap 键名 |
| executableExpr 两种形态 | `STATIC_RULE` | 样本 | 前缀语义 |
| `formula-functions.xml` 只是帮助文件 | `STATIC_RULE` | 逐字解析 | — |
| **`exp<雪花ID>` 生成算法** | **BLOCKED** | — | **需反编译** |
| **传入值 vs 表达式值冲突** | **BLOCKED** | — | **需实测** |
| **`copyNeedResetNull` 是否在 .ftl 调用** | **BLOCKED** | — | **需 .ftl** |
| **88 函数真实清单** | **BLOCKED** | — | **不在 formula-functions.xml** |

### 专题 5：接口

| 结论 | 等级 | 证据源 | 缺口 |
|---|---|---|---|
| 830 AppService / 9343 方法 | `STATIC_RULE` | `svc-app-service.txt.gz` | 分类 |
| `DubboFactory` 4 重载 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| `AppServiceInvokeDto` **9 字段** | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| 泛化调用完整链（含异步/补偿） | `VERIFIED_STATIC_BYTECODE` | 签名库 | 实现细节 |
| 9 个黑白名单内容 | `STATIC_RULE` | `microflow/*.json` | — |
| 事件包已迁移 | `STATIC_RULE` | 两份白名单对比 | — |
| 跨实体可调 9 方法 | `STATIC_RULE` | 名单 | — |
| `VersionControl` 是下载审计 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| **@Autowired vs DubboFactory 判定** | **无** | — | **需 consumers 分析** |
| **权限/异常/事务** | **无** | — | **需反编译** |

### 专题 6：组件

| 结论 | 等级 | 证据源 | 缺口 |
|---|---|---|---|
| `StorageService` 14 方法（含分片） | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| 5 种存储后端 | `VERIFIED_STATIC_BYTECODE` | 类枚举 | — |
| `FileAppService` 14 方法 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| `OrgCommonAppService` 45 方法 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| `HttpClientUtil` 93 方法 | `VERIFIED_STATIC_BYTECODE` | 签名库 | — |
| **`DistributedLockFactory` 6 方法** | **`VERIFIED_STATIC_BYTECODE`** | 签名库 | **续约机制** |
| 锁默认带租户 | `VERIFIED_STATIC_BYTECODE` | 方法名 | — |
| 附件关联流程 | **UNVERIFIED** | 推断 | 需实测 |
| 缓存失效时机 | **UNVERIFIED** | — | 需实测 |

### 专题 7：业务关联

| 结论 | 等级 |
|---|---|
| 关联模型 6 字段 | 设计 |
| 6 大域能力映射 | `VERIFIED`（引用） |
| 评估集四类 ≥80 条 | 设计 |
| 6 个指标（含 MRR + 澄清） | 设计 |
| R1/R2 回归用例 | `LIVE`（历史错误） |
| 6 个盲测场景 | 设计 |

---

## 3. 全局缺口汇总

### 3.1 阻塞型（需用户决策）

| 缺口 | 影响专题 | 需要什么 |
|---|---|---|
| 平台 jar 本体 | 2、3、4、5 | 用户提供路径 |
| .ftl 模板内容 | 2、4 | 需 jar |
| CFR 反编译工具 | 2、3、4 | 可安装（需批准） |
| test2 写操作 | 3、4 | 8 项审批（见 v4 §九） |

### 3.2 可绕过型（有替代路径）

| 缺口 | 替代方案 |
|---|---|
| 生成器方法体 | 实测产物反推（需审批 B） |
| `getTemplateOutMap()` 返回值 | 实测产物 + OutPath 签名交叉 |
| 元数据对象关系 | 从 DTO 字段结构反推 |
| Task→Template 映射 | 命名候选 + 实测产物验证 |

### 3.3 完全无替代

| 缺口 | 后果 |
|---|---|
| 主键生成机制 | 只能标 `UNVERIFIED` |
| 子表外键回填 | 只能标 `UNVERIFIED` |
| 单据流转路径 | 只能标 `UNVERIFIED` |
| runtime 主动执行表达式 | 只能标 `BLOCKED` |

---

## 4. 证据可信度分层

```
最可信  LIVE_RULE                     实测响应体 / DB 结果 / 生成产物
        ↑
        VERIFIED_STATIC_BYTECODE      签名 + 调用关系闭合
        ↑
        STATIC_RULE                   配置/清单/文档逐字
        ↑
        UNVERIFIED                    推测
        ↑
最不可信 BLOCKED                       无证据
```

**当前分布（估计）：**
- `LIVE_RULE`：约 5 条（全部来自已有 facts 的历史实测）
- `VERIFIED_STATIC_BYTECODE`：约 60 条
- `STATIC_RULE`：约 50 条（本轮新增 18 条）
- `UNVERIFIED`：约 20 条（明确标注）
- `BLOCKED`：约 10 条

**⇒ 结论：静态层已经比较扎实，运行时层几乎空白。**
**⇒ 这不是研究失败，是「未获批准写操作」的必然结果。**
**⇒ 必须在最终报告中标 `PARTIALLY_COMPLETED`，不得标 `COMPLETE`。**

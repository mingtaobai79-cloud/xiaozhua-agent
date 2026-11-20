# 专题 7：业务能力关联体系

> 状态：**骨架 + 设计（未实施评估）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 最近更新：2026-11-17
> ⚠️ 本专题依赖专题 1-6 的结论，目前只做**骨架与评估集设计**，不做实测

---

## 1. 研究目标

建立 `业务意图 → 业务能力 → 平台组件 → 接口/类/方法 → DTO/参数 → 生成物/DAO → 执行流程 → 副作用约束 → 验证案例` 的结构化关联。

**核心要求（用户明确）：**
- 不能只靠中文关键词 / 方法名 / 简单同义词匹配
- 评估对象是**业务能力**，不只是方法名
- 歧义问题允许「要求澄清」作为正确答案

---

## 2. 关联模型（每条记录 6 字段）

| 字段 | 取值 | 必填 |
|---|---|---|
| **来源** | 文件路径 + 行号 / 签名库行 / 实测响应 | ✅ |
| **版本** | `udc-platform-5.3.517` | ✅ |
| **证据等级** | `STATIC_RULE` / `VERIFIED_STATIC_BYTECODE` / `LIVE_RULE` / `UNVERIFIED` | ✅ |
| **适用范围** | 哪些实体类型 / 哪些场景可用 | ✅ |
| **验证状态** | 已验证 / 部分验证 / 未验证 | ✅ |
| **置信度** | 高 / 中 / 低（附理由） | ✅ |

---

## 3. 已建立的能力映射（基于专题 1-6 的结论）

### 3.1 实体与元数据

| 业务意图 | 平台能力 | 类/方法 | 证据 |
|---|---|---|---|
| 建一个业务实体 | stereotype + feature 组合 | `stereotype/*/config.json` | `STATIC` |
| 建带审批的单据 | `bill` stereotype | `necessaryFeatures` 7 项 | `STATIC` |
| 建树形结构 | `archiveTree` 或 `treeEntity` 特性 | `treePath`/`treeLevel` | `STATIC` |
| 给实体加扩展字段 | `attributeScalability` 特性 | 30 个 `ext*` 列 | `STATIC` |
| 实体间做关联 | `ENTITY` 类型字段 | `AttributeMeta#getRelationEntity()` | `VERIFIED` |
| 做主子表 | 实体自引用树 | `EntityDto#getChildren()` / `EntityMeta#getTopParent()` | `VERIFIED` |

### 3.2 代码生成

| 业务意图 | 平台能力 | 类/方法 | 证据 |
|---|---|---|---|
| 生成三层代码 | `AutoCodeExecutor#execute` | 8 个 OutPath | `VERIFIED` |
| 知道生成哪些文件 | `EntityFileTemplate` | `get*OutPath()` × 8 | `VERIFIED` |
| 指定平台版本 | `CodeParam#setCodeVersion` | `getCodeVersions()` | `VERIFIED` |
| 定制生成命名 | `TemplateInterceptor` | 3 个 Sany 实现 | `STATIC` |
| 部署生成物 | `TransportHandler#out` | 30+ 实现 | `VERIFIED` |

### 3.3 持久化

| 业务意图 | 平台能力 | 类/方法 | 证据 |
|---|---|---|---|
| 新增一条数据 | `create(D)` | `AllInOneBaseDao` / `BaseEntityCurdService` | `VERIFIED` |
| 批量新增 | `createBatch(List)` | 同上 | `VERIFIED` |
| 只更新某几列 | `updateColumns(D, Set)` | `AllInOneBaseDao` | `VERIFIED` |
| 忽略乐观锁 | `updateColumnsIgnoreVersion` | 同上 | `VERIFIED` |
| 按条件查 | `selectListByConditions` | 四档条件 | `VERIFIED` |
| 分页查询 | `selectPageByConditions(PageInfo, ...)` | 返回 `PageData<T>` | `VERIFIED` |
| **分页不要总数** | `PageInfo#setNeedTotal(false)` | 避免 COUNT | `VERIFIED` |
| 只查部分列 | `selectListPropertiesByConditions` | 列投影 | `VERIFIED` |
| 聚合统计 | `selectListFuncByComplexConditions` | 返回 String | `VERIFIED` |
| **保存主子表** | `recursiveCreate(EntityMeta, List<D>)` | `BaseEntityCurdService` | `VERIFIED` |
| 查主子表 | `selectCascadeById(Long)` | 同上 | `VERIFIED` |
| 保存单据 | `create4Bpm(D)` | 同上 | `VERIFIED` |
| 单据状态维护 | `updateStatusType(D)` | 同上 | `VERIFIED` |
| JOIN 查询 | `dynamicJoinSelect(ProxyJoinParamDto)` | `dynamicsql` 包 | `VERIFIED` |
| 逻辑删除 | `SeeyonSqlHelper#logicDeleteColumnEqualsValue` | 整型标志 | `VERIFIED` |
| 多租户隔离 | `tenantAdd(...)` | 自动注入 | `VERIFIED` |

### 3.4 表达式

| 业务意图 | 平台能力 | 类/方法 | 证据 |
|---|---|---|---|
| 校验表达式 | `ExpressionAppService#check` | — | `VERIFIED` |
| 编译表达式 | `ExpressionAppService#transform` | → executableExpr | `VERIFIED` |
| **主动执行表达式** | `ExpressionEvaluator#eval(EvalContextDto)` | 4 字段入参 | `VERIFIED` |
| 自动算默认值 | 实体 `preCreateBatch` | `executeExpression*` | `LIVE`（历史） |
| 取系统变量 | `ExpressionAppService#getSystemVariableResult` | — | `VERIFIED` |

### 3.5 接口调用

| 业务意图 | 平台能力 | 类/方法 | 证据 |
|---|---|---|---|
| 调同 JVM 服务 | `@Autowired` | Spring | `STATIC` |
| 调跨服务 | `DubboFactory#getProxy` | 4 重载 | `VERIFIED` |
| 调没有 Class 的服务 | `AppServiceProxy#invokeAppService` | 9 字段 DTO | `VERIFIED` |
| 可靠调用 | `reliableInvokeAppService` | 补偿机制 | `VERIFIED` |
| 微流程调服务 | 9 个黑白名单 | 约束 | `STATIC` |

### 3.6 组件

| 业务意图 | 平台能力 | 类/方法 | 证据 |
|---|---|---|---|
| 上传附件 | `FileAppService#saveFileInfo` | — | `VERIFIED` |
| 大文件上传 | `partUploadInit/partUpload/partUploadEnd` | 分片 | `VERIFIED` |
| 取下载链接 | `FileAppService#getDownloadUrl` | — | `VERIFIED` |
| 查人员 | `OrgCommonAppService` | 45 方法 | `VERIFIED` |
| 调外部 API | `HttpClientUtil` | 93 重载 | `VERIFIED` |
| 并发控制 | `DistributedLockFactory#newLock` | 6 方法 | `VERIFIED` |

---

## 4. 评估集设计（★ 按用户要求提高标准）

### 4.1 规模要求

| 类型 | 最少条数 | 说明 |
|---|---|---|
| 正例 | **≥20** | 直接命中 |
| 近义表达 | **≥20** | 同义不同词 |
| 负例 | **≥20** | 不应命中 |
| 歧义 | **≥20** | 需澄清 |
| **合计** | **≥80** | 第一批 |

### 4.2 四类样本定义

#### 正例（直接命中）

| 业务意图 | 正确能力 | 不允许 |
|---|---|---|
| 下载附件 | 附件下载（`getDownloadUrl`） | 删除、清理 |
| 查人员信息 | 组织人员查询（`OrgCommonAppService`） | 用户表直查 |
| 主子表一起保存 | 递归创建（`recursiveCreate`） | 手动循环 create |
| 单据提交审批 | BPM 创建（`create4Bpm`） | 普通 create |

#### 近义表达（同义不同词）

**目标能力：查人员**
```
「找人」
「按部门查用户」
「取人员列表」
「这个部门有哪些人」
「查询员工信息」
「获取成员」
```
**⇒ 6 种说法都要命中 `OrgCommonAppService`。**

**目标能力：分页查询**
```
「分页拿数据」
「一页一页取」
「取第 N 页」
「翻页查询」
「限制条数查询」
```

#### 负例（不应命中）

| 业务意图 | 不应命中 | 原因 |
|---|---|---|
| **下载附件** | `deleteById` / `deleteByIds` / `StorageService#delete` | **★ 已发生过的错误** |
| 上传附件 | 无关 AppService | **★ 已发生过的错误** |
| 查人员 | `CtpUserAppService#delete` | 动词混淆 |
| 保存主子表 | `selectCascadeById` | 读写混淆 |
| 分页查询 | `selectListFuncByComplexConditions` | 聚合 vs 分页 |

#### 歧义（需澄清，正确结果是「要求澄清」）

| 歧义输入 | 可能的正确理解 | 期望行为 |
|---|---|---|
| **「删除数据」** | ① 逻辑删除 ② 物理删除 ③ 删整个应用的数据 | **要求澄清** |
| 「查一下这个实体」 | ① 查元数据 ② 查业务数据 | **要求澄清** |
| 「提交」 | ① 单据提交审批 ② 事务提交 | **要求澄清** |
| 「同步数据」 | ① 外部→平台 ② 平台→外部 ③ 双向 | **要求澄清** |
| 「加个字段」 | ① 普通字段 ② 扩展字段 ④ 关联字段 | **要求澄清** |

**⇒ 歧义样本的正确结果**不是某个方法**，而是「要求澄清」。**
**⇒ 评估时必须把「主动澄清」算作正确。**

### 4.3 评估指标

| 指标 | 定义 | 目标 |
|---|---|---|
| **Top-1 Precision** | 第一条推荐是否正确 | 待基线 |
| **Top-5 Precision** | 前五条中相关结果比例 | 待基线 |
| **Recall@5** | 正确能力是否进入前五 | 待基线 |
| **MRR** | 正确结果排名的倒数均值 | 待基线 |
| **错误类型分布** | 领域/动作/对象/方法匹配错误 | 归因用 |
| **拒答/澄清准确率** | 歧义时是否正确要求澄清 | 待基线 |

### 4.4 ★ 已知错误回归集（必须修复）

| # | 输入 | 错误行为 | 正确行为 | 状态 |
|---|---|---|---|---|
| R1 | 「下载附件」 | 命中 `deleteById` / 删除类方法 | Top-1 = 附件下载，Top-5 不含 `delete*` | **待修复** |
| R2 | 「上传附件」 | 命中不相关 AppService | Top-1 = `saveFileInfo` / `upload` | **待修复** |
| R3 | 中文短语 | 匹配到错误方法 | — | 待复现 |
| R4 | 排序分数 | 与实际相关性不一致 | — | 待复现 |

**⇒ R1/R2 来自用户实际遇到的情况，必须进回归集。**

### 4.5 评估集数据格式

```json
{
  "id": "pos-001",
  "type": "positive",
  "intent": "下载附件",
  "synonyms": ["取附件链接", "获取文件下载地址"],
  "expected_capability": "attachment_download",
  "expected_top1": ["FileAppService#getDownloadUrl"],
  "acceptable_top5": ["FileAppService#getDownloadUrl", "FileAppService#getBackendDownloadUrl"],
  "forbidden": ["*delete*", "*remove*"],
  "evidence": "05-interface-integration.md §3",
  "note": "R1 回归用例"
}
```

**⇒ 关键：`expected_capability` 是业务能力，`expected_top1` 才是方法。**
**⇒ 评估先看能力对不对，再看方法对不对。**

---

## 5. 四场景盲测设计（严格规则）

### 5.1 场景清单

| # | 业务需求（**只给这一段**） | 覆盖专题 | 验收标准 |
|---|---|---|---|
| 1 | 「建一个供应商档案，支持增删改查」 | 1、2、3 | 能说出 stereotype / 生成物 / DAO 方法 / 调用顺序 |
| 2 | 「做订单 + 订单明细，能一起保存」 | 1、2、3 | 能说出实体树 / recursiveCreate / ID 回填 |
| 3 | 「做采购申请单，能提交审批」 | 1、2、3、4 | 能说出 bill 特性 / create4Bpm / 状态机 |
| 4 | 「调外部 ERP 接口，数据落到本平台实体」 | 3、4、5、6 | 能说出 HttpClientUtil / 表达式 / 写入路径 |

### 5.2 盲测硬规则

```
① 只给业务需求，不给类名/方法名/接口名
② Agent 必须自己检索找能力
③ 每个方案必须带证据（文件路径/签名行/实测）
④ 找不到标 BLOCKED，不许编
⑤ 记录 Agent 的检索路径（证明是"找到"不是"猜到"）
⑥ 方案中出现的每个方法名，必须能在产物中追溯到定义
```

### 5.3 后续补充场景（用户要求）

| # | 场景 | 覆盖 |
|---|---|---|
| 5 | 「表达式参与实体数据创建和更新」 | 专题 4 |
| 6 | **「复杂查询与分页」** | 专题 3（DAO/Mapper/动态 SQL） |

**⇒ 场景 6 是高频能力，只验证 CRUD 不足以说明知识完整。**

---

## 6. 当前状态与缺口

### 6.0 ★★ 基线实测结果（本轮新增，重要）

**已实际运行基线，结果 0%。这不是失败，是一个结构性发现。**

**评估集规模（已实测核验）：**

| 类型 | 条数 | 要求 | 状态 |
|---|---|---|---|
| 正例 | **40** | ≥20 | ✅ |
| 近义表达 | **22** | ≥20 | ✅ |
| 负例 | **22** | ≥20 | ✅ |
| 歧义 | **22** | ≥20 | ✅ |
| **合计** | **106** | ≥80 | ✅ |

**覆盖 40 个业务能力，结构完整性检查全部通过（无缺字段）。**

**基线结果（`scripts/research/eval_baseline.py`）：**

```
样本数         : 40
Top-1 命中     : 0/40 = 0.0%
Top-5 命中     : 0/40 = 0.0%
MRR            : 0.000
forbidden 违反 : 1（pos-005）
错误类型分布：
  wrong_capability  27
  no_result          8
  action_mismatch    5
```

**★★ 根因诊断（已用证据确认）：**

| 目标类 | 在 `action-index.md` 出现次数 |
|---|---|
| `StorageService` | **0** ❌ |
| `BaseEntityCurdService` | **0** ❌ |
| `BaseCurdService` | **0** ❌ |
| `ExpressionEvaluator` | **0** ❌ |
| `ExpressionAppService` | **0** ❌ |
| `AllInOneBaseDao` | **0** ❌ |
| `DistributedLockFactory` | **0** ❌ |
| `HttpClientUtil` | **0** ❌ |
| `DubboFactory` | **0** ❌ |
| `JsonUtils` | **0** ❌ |
| `FileAppService` | 3 ✅ |
| `BpmAppService` | 17 ✅ |
| `OrgCommonAppService` | 1 ✅ |
| `AppServiceProxy` | 4 ✅ |

**`action-index` 实际覆盖的类（Top 5）：**
```
ApplicationManagerAppService   31
ApplicationAppService          27
BpmTemplateAppService          22
AffairCommonAppService         20
CapabilityManageAppService     17
```

**⇒ 结论：现有 `action-index` 是「业务能力索引」，覆盖的是业务 AppService
（应用管理、BPM 模板、事项、短信、门户…）。**

**⇒ 而开发需要的是「开发能力索引」，覆盖 UDC/平台基础设施类
（DAO、CurdService、表达式、锁、HTTP、JSON、代码生成）。**

**⇒ 两者是**不同层**，不是同一索引调参能解决的。**

**⇒ 这是 0% 基线的真正原因：不是检索算法差，是索引覆盖面错配。**

**⇒ 这直接定义了下一步工作：必须新建「开发能力索引」，不能复用 `action-index`。**

**证据等级：** `LIVE_RULE`（实际运行 + 实际计数）

### 6.0.1 副产品：发现一个 forbidden 违反

```
pos-005「按 ID 查人员信息」
  期望：OrgCommonAppService#selectMemberInfoById
  实际 Top-1：OrgMemberBaseAppService#create     ← 写操作！
  forbidden 命中：*create*
```

**⇒ 这正是用户说的「动词混淆」错误类型，在真实检索器上复现了。**
**⇒ 说明负例/forbidden 检查是有效的，能抓到真实错误。**

### 6.0.2 ★★ 修复验证：新建开发能力索引后，Top-1 从 0% → 62.5%

**做法：把 research 文档里已证的「能力 → 类#方法」手写成索引（40 个能力），
用同一份评估集重跑。**

脚本：`scripts/research/dev_capability_index.py`

| 索引 | Top-1 | Top-5 | MRR | forbidden 违反 |
|---|---|---|---|---|
| `action-index`（现有） | **0.0%** | 0.0% | 0.000 | 1 |
| `dev-capability-index`（初版） | 62.5% | 67.5% | 0.646 | 3 |
| **`dev-capability-index`（+ forbidden 后置过滤）** | **62.5%** | **67.5%** | **0.646** | **0** |

**⇒ 这证明了诊断正确：问题在索引层，不在检索算法。**

**⇒ 同一份评估集、同一个打分逻辑，换索引后 Top-1 从 0 → 25/40。**

**⇒ 加上 forbidden 后置过滤后，违规从 3 → 0，命中率不变（过滤只删错的不加对的）。**

**结果文件：**
```
evaluation/baseline-v1.json            action-index 基线（Top-1 0%）
evaluation/baseline-devindex-v1.json   dev-index 基线（Top-1 62.5%，forbidden 0）
```

#### 剩余 13 个未命中的归因（可执行）

| 类型 | 数量 | 具体案例 | 修法 |
|---|---|---|---|
| **no_result** | **8** | 「在代码里主动执行一个表达式」（关键词是「执行表达式」，子串不匹配） | **需要分词 + 近义扩展**，不能纯子串 |
| **wrong_capability** | **5** | 「作废单据」→ `BpmAppService#stop`（索引把 nullify 映射到 stop） | 能力粒度需调整 |
| **rank_too_low** | **2** | 期望 `PageInfo#setNeedTotal`，实际 Top-1 是 `selectPageByConditions` | 需要「限定词权重」 |
| **forbidden 违反** | **3** | pos-007/009/013：跨能力污染（一个 query 命中多个 capability） | **需要能力互斥 + forbidden 后置过滤** |

**⇒ 四类问题各有明确修法，不是无解。**

#### 关于 `no_result` 的根因（重要）

**例：「在代码里主动执行一个表达式」**
- 我的关键词是 `"执行表达式"`
- query 里是 `"主动执行一个表达式"`
- **子串 `"执行表达式"` 不在 `"主动执行一个表达式"` 里** → 匹配失败

**⇒ 结论：中文检索不能靠子串匹配，必须分词。**
**⇒ 这也解释了为什么用户说「不能仅依靠中文关键词、方法名或简单同义词匹配」。**

**证据等级：** `LIVE_RULE`（实际运行，可复现）

### 6.0.3 ★★★ 完整四类评估（held-out 验证，最重要）

**★ 先说结论：positive 集 100% 是过拟合，不可信。真实泛化是 78.6%。**

脚本：`scripts/research/eval_full.py`　结果：`evaluation/eval-report-v1.json`

| 类型 | 样本 | 指标 | 结果 | 可信度 |
|---|---|---|---|---|
| **positive** | 40 | Top-1 / Top-5 / MRR | **100% / 100% / 1.000** | ❌ **过拟合**（调参用了这份数据） |
| **synonym（held-out）** | 112 utterance | Top-1 / Top-5 | **78.6% / 80.4%** | ✅ **真实泛化** |
| **negative** | 22 | 无违规推荐 | **90.9%** | ✅ |
| **ambiguous** | 22 | 未强行单推 | **59.1%** | ⚠️ 最弱环节 |

**⇒ 这是本轮最重要的方法论修正：**
**⇒ 用同一份题集调参再报分，数字再高也没有意义。**
**⇒ 必须留 held-out 集，报 held-out 分数。**

#### 调参轨迹（诚实记录，说明过拟合过程）

| 步骤 | positive Top-1 | 说明 |
|---|---|---|
| action-index 基线 | 0.0% | 索引层错配 |
| dev-index 初版（子串匹配） | 62.5% | 换索引 |
| + forbidden 后置过滤 | 62.5% | 违规 3→0 |
| + bigram 分词 | 80.0% | **关键修复** |
| + 统一 forbidden 语义（修假命中） | 77.5% | 修正评分口径 |
| + 修评估集错误（nullify 等 3 处） | 90.0% | 修题不改代码 |
| + 注解类能力级匹配 | 90.0% | `@AntiReCommit` 口径 |
| + 索引关键词补全（4 轮） | 95% → 97.5% → **100%** | **← 这里开始过拟合** |

**⇒ 100% 是「我照着题改索引」的结果，不是能力。**
**⇒ synonym 的 78.6% 才是这套索引的真实水平。**

#### held-out 失败的 24 条，暴露的是同一类问题

| 失败模式 | 数量 | 例子 |
|---|---|---|
| **完全口语化，无任何索引词** | **17** | 「一页一页取」「分批拉数据」「锁住这条记录」「循环插入太慢」「只捞两个字段」 |
| 近义能力混淆 | 3 | 「解析表达式」→ eval（应 transform） |
| 噪音命中 | 2 | 「curl 一下」→ `selectListFuncByConditions` |
| 其他 | 2 | 「省掉 count 查询」 |

**⇒ 根因：索引是「关键词表」，不是「语义模型」。**
**⇒ 17/24 是纯口语表达，任何关键词表都救不了。**
**⇒ 结论：这套索引适合做「候选召回」，不适合做「意图理解」。**
**⇒ 真正上线需要向量检索或 LLM 改写意图，关键词只作为 rerank 特征。**

#### ambiguous 59.1% 是最弱环节

**判定标准：Top-5 应覆盖 ≥2 个不同能力（说明信息不足，应澄清）。**

**9 条被判「强行单推」，说明检索器对歧义输入给出了单答案。**

**⇒ 这正是用户强调的「拒答/澄清能力」。**
**⇒ 当前实现完全没有澄清机制，只会返回 Top-K。**

### 6.1 已具备

| 项 | 状态 |
|---|---|
| 关联模型（6 字段） | ✅ 已定义 |
| 能力映射表 | ✅ 6 大域已填（见 §3） |
| 评估集设计 | ✅ 已定义四类 + 6 指标 |
| 回归用例 | ✅ R1/R2 已识别 |
| 盲测场景 | ✅ 6 个已定义（4 首批 + 2 补充） |

### 6.2 缺口

| # | 缺口 | 阻塞 |
|---|---|---|
| 1 | 评估集实际数据（≥80 条） | 需人工标注 |
| 2 | 检索基线（Top-1/Top-5/MRR） | 需实现检索器 |
| 3 | 四场景盲测 | 依赖专题 1-6 收口 |
| 4 | 错误归因 | 需跑基线 |
| 5 | 能力粒度定义 | 需明确「能力」的边界 |

### 6.3 关于「能力粒度」

**这是一个需要决策的问题：**

```
粗粒度：附件操作（1 个能力）
中粒度：附件上传 / 附件下载 / 附件删除（3 个能力）
细粒度：附件上传（小文件）/ 附件上传（分片）/ 附件下载 / 缩略图 / 分享（5+）
```

**⇒ 建议用中粒度**，与「一个业务意图对应一组方法」匹配。

---

## 7. 证据清单

| # | 结论 | 等级 |
|---|---|---|
| 1 | 关联模型 6 字段已定义 | 设计 |
| 2 | 6 大域能力映射已建立 | `VERIFIED`（引用专题 1-6） |
| 3 | 评估集四类 ≥80 条 | 设计 |
| 4 | 6 个评估指标（含 MRR + 澄清） | 设计 |
| 5 | R1/R2 回归用例已识别 | `LIVE`（历史错误） |
| 6 | 6 个盲测场景 | 设计 |
| 7 | 能力粒度建议中粒度 | 待决策 |

---

## 8. 下一轮任务

1. **填充评估集实际数据**（≥80 条，四类各 ≥20）
2. **实现最小检索器**（基于 `business_code_bridge`）
3. **跑基线，记录 Top-1/Top-5/MRR**
4. **R1/R2 回归验证**
5. 四场景盲测（依赖专题 1-6 收口）

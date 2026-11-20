# 未解决问题清单

> 每次发现新缺口就追加。解决后标记并保留记录。
> 最后更新：2026-11-17（轮次 3）

---

## 1. 按阻塞类型分组

### A. 缺资产（需用户提供）

| # | 问题 | 影响专题 | 需要什么 | 状态 |
|---|---|---|---|---|
| A1 | 方法体逻辑不可见 | 2、3、4、5 | 平台 jar 本体路径 | `WAITING` |
| A2 | 模板语法不可见 | 2、4 | .ftl 文件（在 jar 内） | `WAITING` |
| A3 | 无法反编译 | 2、3、4 | CFR 工具（可安装，需批准） | `WAITING` |
| A4 | 注解实例数据缺失 | 1、3、5 | 需 `javap -v` 全量扫描（当前只有注解定义） | `WAITING` |

### B. 需动态环境（8 项审批全未批）

| # | 问题 | 影响 | 对应审批项 |
|---|---|---|---|
| B1 | 主键生成时机 | 专题 3 | 审批 E |
| B2 | 子表外键回填时机 | 专题 3 | 审批 E |
| B3 | 主子表保存顺序 | 专题 3 | 审批 E |
| B4 | 更新策略（全量 vs 增量） | 专题 3 | 审批 E |
| B5 | 删除策略（级联 vs 手动） | 专题 3 | 审批 E |
| B6 | 单据能否绕过 BPM | 专题 3 | 审批 D/E |
| B7 | 事务范围 | 专题 3 | 审批 E |
| B8 | 传入值 vs 表达式值冲突 | 专题 4 | 审批 G |
| B9 | 表达式异常是否中断事务 | 专题 4 | 审批 G |
| B10 | 生成产物结构与命名 | 专题 2 | 审批 B |
| B11 | 重复生成是否覆盖手写代码 | 专题 2 | 审批 B |
| B12 | 锁续约机制 | 专题 6 | 审批 E |

### C. 静态可查但未查（下一轮）

| # | 问题 | 专题 | 方法 |
|---|---|---|---|
| C1 | `@Function` 的 7 个元素名 | 4 | `javap -v` 或 jar |
| C2 | `@AppServiceOperation` 的 9 个元素名 | 5 | 同上 |
| C3 | `@CountSql` 的 1 个元素 | 3 | 同上 |
| C4 | `@Idempotent` 的实现机制 | 3 | 需 jar |
| C5 | `JsonUtils` / `JsonNodeUtil` / `JsonUtil` 差异 | 6 | 方法对比 |
| C6 | `Wrapper` 类的实际能力 | 3 | 需 jar 或 tk.mybatis 文档 |
| C7 | `EntityType` / `RelationType` 枚举取值 | 1、3 | 需 jar |
| C8 | `EntityCategoryEnum` 取值 | 1 | 需 jar |
| C9 | 10 种数据库方言清单 | 3 | `DatabaseType` 枚举需 jar |
| C10 | `AppServiceInvokeDto` 各字段的实际用法 | 5 | consumers 反查 |
| C11 | 88 个表达式函数的真实清单 | 4 | 需扫 `@Function` 实例 |

### D. 已识别但暂无解的推断（UNVERIFIED）

| # | 推断 | 为什么不确定 |
|---|---|---|
| D1 | `getDataType` vs `getRealDataType` 是「逻辑类型 vs 物理列类型」 | 无方法体 |
| D2 | 租户信息来自 ThreadLocal | `putThreadContext()` 只证存在，不证内容 |
| D3 | `@Autowired` 同 JVM、`DubboFactory` 跨应用 | `@AppService` 的 `@Primary` 只证本地可行 |
| D4 | `SeeyonKeyMap` 重复 key 表达 OR | 需反编译 `jdbcDynamicCondition` |
| D5 | `@CountSql` 与 `isNeedTotal(false)` 是同一机制 | 两者独立存在，关系未证 |
| D6 | `copyNeedResetNull` 在 Freemarker 模板中调用 | 零 Java 调用者，但模板调用不入签名库 |
| D7 | 附件关联流程（saveFileInfo → storageKey → getDownloadUrl） | 从 API 设计推断 |
| D8 | `resetNormal` 与 `copyNeedResetNull` 同源 | 命名相似，无调用链证据 |

---

## 2. 按专题统计缺口数

| 专题 | A 类 | B 类 | C 类 | D 类 | 合计 |
|---|---|---|---|---|---|
| 1 元数据 | 1 | 0 | 2 | 1 | 4 |
| 2 代码生成 | 3 | 2 | 0 | 1 | 6 |
| 3 持久化 | 1 | 6 | 3 | 3 | 13 |
| 4 表达式 | 2 | 2 | 2 | 1 | 7 |
| 5 接口 | 1 | 0 | 2 | 1 | 4 |
| 6 组件 | 0 | 1 | 2 | 1 | 4 |
| 7 业务关联 | 0 | 0 | 1 | 0 | 1 |

**⇒ 专题 3（持久化）缺口最多（13 个），且 6 个是 B 类（需实测）。**
**⇒ 这符合预期：持久化行为本质上是运行时属性，静态无法穷尽。**

---

## 3. 已解决（保留记录）

| # | 原问题 | 解决方式 | 轮次 |
|---|---|---|---|
| 1 | runtime 主动执行表达式入口未知 | 找到 `ExpressionEvaluator#eval(EvalContextDto)` | 2 |
| 2 | 主子表机制未知 | 找到 `EntityDto.getChildren()` + `EntityMeta.getTopParent()` + `recursiveCreate` | 2 |
| 3 | 单据如何入数据 | 找到 `create4Bpm` / `update4Bpm` / `handlerCaseId` | 2 |
| 4 | 三层命名规则 | 找到 `classType` 7 种枚举 | 2 |
| 5 | 版本选择机制 | 找到四层叠加（CodeParam + AutoCodeProperties + TemplateAdapter + 2 Directive） | 2 |
| 6 | 生成与部署关系 | 找到 `TransportHandler#out`（32 实现） | 2 |
| 7 | `@Autowired` 能注什么 | 找到 `@AppService` = `@Service` + `@Primary` | 3 |
| 8 | 自定义表达式函数怎么注册 | 找到 `@FunctionClass` + `@Function` | 3 |
| 9 | 幂等机制 | 找到 `@Idempotent` / `@AntiReCommit` / `@ExclusivePermit` / `@LimitCountOperation` | 3 |
| 10 | 事务机制 | 找到 `@BootApp` 含 `@EnableTransactionManagement` | 3 |
| 11 | `send`/`submit`/`saveDraft` 边界 | 找到 `BpmAppService` 26 方法三者的 DTO 差异 | 3 |
| 12 | 平台自带分布式锁 | 找到 `DistributedLockFactory` 6 方法 | 2 |
| 13 | CodeTask 52 是否准确 | `extension-points.md` 双源确认 | 3 |

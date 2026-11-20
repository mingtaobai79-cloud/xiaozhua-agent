# 专题依赖关系图

> 说明：**这是研究组织依赖，不是平台内部架构依赖。**

---

## 1. 依赖图

```
                    ┌─────────────────────────────┐
                    │ 专题1 应用与元数据            │
                    │ （无前置依赖）                │
                    └──────────┬──────────────────┘
                               │ 元数据定义（EntityDto/AttributeDto/EntityMeta）
                               ▼
                    ┌─────────────────────────────┐
                    │ 专题2 代码生成                │
                    │ （依赖 1 的元数据模型）        │
                    └──────────┬──────────────────┘
                               │ 生成产物（8 个 OutPath）
                               ▼
                    ┌─────────────────────────────┐
                    │ 专题3 生成物与持久化          │
                    │ （依赖 2 的产物结构）          │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ 专题4 表达式  │  │ 专题5 接口    │  │ 专题6 组件    │
    │ （依赖3 写入） │  │ （依赖3 契约）│  │ （无前置）    │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             ▼
                  ┌─────────────────────────┐
                  │ 专题7 业务能力关联        │
                  │ （依赖 1-6 全部）         │
                  └─────────────────────────┘
```

---

## 2. 可并行关系

| 专题 | 可并行对象 | 原因 |
|---|---|---|
| 专题 1 | 专题 6 | 无依赖 |
| 专题 2 | 专题 5 | 5 只需接口签名，不需生成产物 |
| 专题 3 | 专题 4（部分） | 4 的定义/生成阶段不依赖 3 |
| 专题 5 | 专题 6 | 无依赖 |

**⇒ 静态研究阶段，1/2/5/6 可以任意并行。**
**⇒ 3 的运行时部分必须等实测批准。**
**⇒ 7 必须等 1-6 收口。**

---

## 3. 关键共享对象（跨专题）

| 对象 | 涉及专题 | 说明 |
|---|---|---|
| `EntityDto` / `Entity4CodeDto` | 1、2、3 | 设计态实体 |
| `EntityMeta` / `AttributeMeta` | 1、3 | **运行时**实体元数据 |
| `AttributeDto` | 1、3、4 | 字段（含 4 份表达式数据） |
| `EntityFileTemplate` | 2、3 | 8 个 OutPath 决定生成物 |
| `BaseEntityCurdService` | 3、4、5 | 199 方法，主子表/单据/表达式全在这 |
| `CodeParam` / `CodeContext` | 2、4 | 生成参数/上下文 |
| `EvalContextDto` / `ExpressionEvaluator` | 4 | 运行时表达式执行 |
| `PageInfo` / `PageData` | 3、5 | 分页（`isNeedTotal` 可关 COUNT） |
| 9 个实体事件 | 3、5 | 事务边界 + 微流程可调 |

---

## 4. 跨专题的关键链路（已证部分）

### 链路 A：实体 → 生成 → 持久化

```
EntityDto (设计态)
  → EntityFileTemplate (8 个 OutPath)
  → {E}Entity / {E}Dto / {E}AppService / {E}AppServiceImpl / {E}Service / {E}Dao / {E}Mapper.xml
  → EntityMeta (运行时)
  → BaseEntityCurdService (199 方法)
  → AllInOneBaseDao (41 方法)
  → tk.mybatis Mapper
  → DB
```

### 链路 B：表达式 → 生成 → 运行

```
AttributeDto.getExpressionDesignData()  (设计态)
  → ExpressionAppService#transform
  → executableExpr
  → AttributeDto.getExpressionRuntimeData()  (运行态)
  → ExpressionCodeGenerator#generateCode
  → CodeGenerateResult {methodName: exp<雪花ID>, methodBody}
  → 注入 {E}Service
  → 运行时：EvalContextDto + ExpressionEvaluator#eval
```

### 链路 C：主子表

```
EntityDto.getChildren()  (设计态树)
  → EntityRuleAggregateTemplate.getLayerMap()
  → EntityMeta.getChildren() / getTopParent()  (运行时树)
  → BaseEntityCurdService#recursiveCreate / recursiveUpdate / recursiveDelete
  → 实测待验证：ID 生成时机、外键回填、保存顺序
```

### 链路 D：单据

```
billBasic 13 字段 (caseId / templateId / billCode)
  → billStatus 8 状态机
  → BaseEntityCurdService#create4Bpm / update4Bpm / handlerCaseId / updateStatusType
  → 9 个事件（含 TRANSACTION_SUCCESS）
  → 实测待验证：能否绕过 BPM
```

---

## 5. 阻塞传播

| 阻塞 | 影响专题 | 影响方式 |
|---|---|---|
| 无平台 jar | 2、3、4、5 | 无法反编译方法体 |
| 无 .ftl | 2、4 | 无法看模板语法与 include 关系 |
| test2 未批准 | 3、4 | 运行时行为全部无法验证 |
| 无 CFR | 2、3、4 | 同上 |

**⇒ 静态研究不受影响，继续推进。**
**⇒ 运行时结论全部标 `BLOCKED`，最终状态 `PARTIALLY_COMPLETED`。**

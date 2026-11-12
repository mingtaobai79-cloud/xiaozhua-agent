# 全面覆盖：维度穷举与对标方法

> “全面覆盖所有可能”不能靠人列举（人只能列出踩过的），必须从**权威数据源穷举维度**，
> 再逐维度对标「平台有什么 / 我们用过没 / 业务会不会遇到」。
> 本文件给出**四个权威源 + 穷举方法 + 开卷清单**。

## 一、四个权威数据源（不靠记忆，靠这四份）

| 源 | 位置 | 能回答什么 | 规模 |
|---|---|---|---|
| **① 语料快照** | `scratch/pmp_schemas.json` | 真实世界里节点怎么组合/流转/嵌套 | 643 流程 / 2786 节点 |
| **② 配置项矩阵** | `core/facts/udc/microflow/node-settings-capability.json` | 每个节点有哪些配置项、子模式、必填、选项 | 24 节点 / 40 子模式 |
| **③ 能力等级矩阵** | `components/udc/microflow/capability_registry.py` | 每个节点验到哪一档、范围限定、证据 | 22 节点 |
| **④ 设置域事实** | `core/facts/udc/setting/{enum,option-set,attribute-set,serial,parameter,custom-object}/` | 除实体外还能用什么构件 | 6 类 |

**开工前对照这四个源，不靠记忆列清单。** 记忆里的清单＝踩过的坑，永远不全。

## 二、需穷举的六个维度

### 维度1：构件类型（建什么）—— 7 类

| 构件 | 何时用 | 事实文档 |
|---|---|---|
| 实体 | 有生命周期的单据/主数据 | `entity/create.md` |
| 枚举 / 选项集 | 封闭值域、页面要下拉 | `setting/enum/`、`setting/option-set/` |
| 字段集 | 跨实体复用的字段组合 | `setting/attribute-set/` |
| 参数 | 全局配置，不参与流转 | `setting/parameter/` |
| 流水号 | 单据编号 | `setting/serial/` |
| 自定义对象 | 无实体的轻量结构 | `setting/custom-object/` |
| 变量 | 仅流程内传递，不落库 | CREATE_VARIABLE |

★ 把「枚举」建成 STRING、把「编号」建成 const、把「配置」建成实体 —— 都是构件选错。
构件选错的代价远高于节点写错（要迁数据、改引用、重建）。

### 维度2：字段类型 × 约束（12 种）

`STRING / INTEGER / BIGINTEGER / DECIMAL / CURRENCY / BOOLEAN / DATE / DATETIME /
ENUM / CTPENUM / ENTITY / Serial`（+ `MULTILINESTRING`）

每类必须问三个问题（漏一个就返工）：

| 类型 | 必问 | 漏了会怎样 |
|---|---|---|
| DECIMAL / CURRENCY | `decimalDigits` 几位？`maxLength` 多少？ | scale=0，0.05→0、68.89→69 |
| ENTITY（关联） | `relationEntity` 指向谁？`relationApp`？`relationType`？ | 主子表断裂、外键漏赋值不报错 |
| ENUM / CTPENUM | 枚举实体建了没？`relationEntity`+`relationType=Many2OneAssociation`？ | `UDC_DATATYPE_0015` 关联枚举不存在 |
| Serial | `serialNumberName/Code/Guid` 三件套？ | `UDC_ATTR_0019` 必须指定流水号规则 |
| STRING / MULTILINESTRING | `maxLength` 够不够？ | 长文本被截断 |

★ **完整类型 × 必填表**：`core/facts/udc/setting/attribute-set/create.md` §11.3。

### 维度3：节点 × 子模式（40 个组合）

从配置矩阵实测，每个节点的子模式数：

```
CREATE_VARIABLE    7 种  基本类型/实体对象/DTO/列表/映射/页信息/...
LIST_OPERATION     6 种  计数/过滤/排序/去重/取值/聚合类
MAP_OPERATION      4 种  获取/设置/删除/键集
CHANGE_LIST        4 种  增加/全量替换/清空/移除
RETRIEVE_ARRAY     4 种  条件查询/ID集合/计数/分页
DELETE_ENTITY      3 种  指定删除/过滤条件删除/...
RETRIEVE           2 种  条件查询/ID查询
CREATE_ENTITY      2 种  字段映射/对象引用
CUSTOM_ERROR       2 种  全局提示/定位到页面元素
PUBLISH_BUSINESS_EVENT 2 种  应用间(异步)/应用内(同步)
CALL_DATA_FLOW     2 种  查询数据/选择数据
DATA_MAPPING       2 种  实体对象/其他
其余 13 个节点              单一形态
```

★ **子模式切换会增删必填项**（矩阵里 `fields_added`/`fields_removed`/`required`）。
用某个子模式前先查矩阵，别把 A 模式的字段带到 B 模式（如 CHANGE_LIST 的 CLEAR 必须
`pop` 掉 dataSource/countAttrs）。

### 维度4：节点间流转组合（真实语料 Top 模式）

从 643 条真实流程 / 2786 节点统计出的高频序列（用它校验自己的串法是否主流）：

```
CREATE_VARIABLE → BRANCH          130   ★ 存值后立即判断
LIST_OPERATION  → LIST_OPERATION  136   ★ 列表多次加工
RETRIEVE        → BRANCH           90   ★ 查询后分支
RETRIEVE        → CREATE_VARIABLE  78   ★ 查询后取值
CREATE_LIST     → FOR_EACH         56   ★ 建列表后遍历
CREATE_VARIABLE → FOR_EACH         47
RETRIEVE        → CREATE_LIST      40   ★ 查询后直接进列表
RETRIEVE_ARRAY  → CHANGE_LIST      35
CREATE_LIST     → LIST_OPERATION   26
FOR_EACH        → CHANGE_BATCH     25   ★ 循环后批量写
FOR_EACH        → FOR_EACH         24   ★ 嵌套循环
```

**循环体里通常装什么**（FOR_EACH/FOR 内部，实测）：
`CREATE_VARIABLE(132) / LIST_OPERATION(128) / BRANCH(117) / CHANGE_VARIABLE(92) /
CHANGE_LIST(84) / RETRIEVE_ARRAY(49) / RETRIEVE(46) / FOR_EACH(44) / SUB_MICROFLOW(17)`

★ **嵌套循环是主流形态**（44 次），不是特例。多层 BOM/明细展开很正常。

**触发方式分布**：MANUAL 558 / BUSINESS_EVENT 61 / SCHEDULE 24。
→ 绝大多数流程是 MANUAL，**MANUAL 无页面时没有 REST 入口**，这就是为什么端到端验证
需要额外建 SCHEDULE 编排流程。

### 维度5：数据流形态（值从哪来）

值槽三态（`value-literal-contexts.md`，643 条流程统计）：

| 形态 | 出现次数 | 语义 | 何时用 |
|---|---|---|---|
| SelectParam（引用） | **2482**（最多） | 引前序节点/字段 | 默认选这个 |
| Expression（表达式） | 998 | 计算 | 需要算的时候 |
| Simple（常量） | 757 | 固定值 | **只限枚举/状态/测试数据** |

写实体字段前先问：「这个值从前序来、算出来、还是真的固定？」

### 维度6：业务不变式（六类，见 SKILL.md 1b）

单据编号 / 汇总态vs明细态 / 状态机 / 主子表关联 / 数量金额口径 / 幂等重复。

## 三、自动化对标（新增业务开工前跑）

写一个盘点脚本，拿新业务需求对四个源做差集，输出「本次会用到什么、哪些没验过、哪些可能踩坑」：

```python
# 伪代码：开工前盘点
需求 = 解析任务书()                      # 实体/流程/事件/集成
for 节点 in 需求.所有节点:
    矩阵项 = 配置矩阵[节点]
    等级 = 能力矩阵[节点]
    if 等级.未 RUNTIME_VERIFIED:
        print(f"⚠️ {节点} 未运行验证：{等级.note}")
    for 子模式 in 矩阵项.submodes:
        if 子模式 not in 等级.已验范围:
            print(f"⚠️ {节点}.{子模式} 未验")

    for 字段 in 需求.写字段:
        if 字段类型 == DECIMAL and not 字段.decimalDigits:
            print(f"❌ {字段} DECIMAL 未定精度")
        if 字段类型 == ENTITY and not 字段.relationEntity:
            print(f"❌ {字段} 关联字段未指向实体")
```

**盘点输出就是开工风险清单**，先摆出来再动手，别等构建失败才发现。

## 四、覆盖度自检清单（交付前逐项打勾）

```
构件层：
[ ] 每张表都判定过「它真是实体吗」（不是枚举/参数/临时变量）
[ ] 所有编码字段都走流水号（无 const 占位）
[ ] 所有外键都是关联实体类型（relationEntity 非空）
[ ] 所有 DECIMAL 都有 decimalDigits + maxLength
[ ] 状态字段都指向枚举（不是裸 STRING）

流程层：
[ ] 每条流程的每个节点都对照过配置矩阵（子模式/必填）
[ ] 未 RUNTIME_VERIFIED 的节点/子模式已标风险
[ ] 循环写子表走批量写（不是逐条 create）
[ ] 变化的多层依赖走嵌套循环（44 次主流）
[ ] 跨流程传参动态取值（无 const 假 id）
[ ] 同一对流程未双触发（串调/事件二选一）

数据流：
[ ] 写实体字段的每个值都标了来源（引用/表达式/常量）
[ ] 常量只用于枚举/状态/测试数据
[ ] 字段级引用类型匹配目标字段

验证层：
[ ] 每条不变式都有对应断言
[ ] 断言脚本本身验证过（表名/列名/语义对）
[ ] 干净触发一次（无重复轮次污染）
```

## 五、遇到矩阵里没有的情况怎么办

**平台能力 > 矩阵**，矩阵只是已验集合。遇到矩阵没有的需求：

1. 先从 **语料** 找同类真实样本（643 条）——大概率别人用过
2. 找不到 → 从 **反编译/前端 bundle** 拿权威约束（不是猜）
3. 还没有 → 做最小真实验证（一个流程、一个节点），结论回写矩阵
4. **绝不**「矩阵没有→假设不支持→降级用别的方式」（这是把能力缺口固化）

★ 「必须进设计器才能做」是最后一种可能，不是默认结论。先离线重放一条语料样本再判定。

# 从一句业务话到节点方案

用户给的常常是**一句业务话**，不是 schema。本文是把它拆成可生成方案的完整走法。

## 拆解步骤

### 0. 先写伪代码，再拼节点（第一步，用户严令）

把业务写成一段伪代码，控制流在伪代码里定清楚，再逐句映射节点：

```
ds     = 查询(数据源, id == 入参)          // 未查到 → 终止
result = false
if (ds.enabled == true) {
    others = 查询列表(enabled == true && id != 入参)   // ★ 排除自己进查询条件
    for (o in others) { o.enabled = false; 更新(o) }
    if (文本包含(ds.jdbcUrl, "mysql")) {              // ★ 嵌在外层 if 里
        result = true
    }
}
return result
```

自查三问：这个判断依赖上一个判断吗（→ 嵌套）？「其他」排不排除自己（→ 查询条件）？
这个中间值有下游消费者吗（没有就不建变量）？

反面教材（实际发生过并被用户逐截图指错）：节点形态全对、发布 errors=0、逐节点无红字，
但组合错了——第二个 BRANCH 拼在顶层（未启用也去判 mysql）、查询没排除自己、
为中转值多建了「承接循环项」和 vJdbc 两个变量（截图里用户问「你创建变量做什么」）。
用户原话：「你的业务逻辑理解错了，只知道将节点写出来，但是你没理解怎么组合。
你为啥不能想象你在写代码呢，每个代码就是一个预制的语法。」

### 1. 逐句切动作

一句业务话里每个动词都是一个动作。以「校验数据迁移的数据源是不是有效的」为例：

> 入参是数据源的 id → 拿到 id 需要查询里面的数据 → 判断它是不是启用的 →
> 是的话，再判断查询其他的是不是有启用的 → 然后修改他们的启用状态为停用 →
> 然后修改数据 → 再判断现在的 jdbc 包含的是不是 mysql → 是的话出参 true 否则 false

切出 6 个动作：查询 / 判断启用 / 查其他启用的 / 改成停用 / 改数据 / 判断 jdbc → 出参。

### 2. 动作 → 节点

| 业务动作 | 节点 | 判别要点 |
|---|---|---|
| 按 ID 取一条 | `RETRIEVE` | `fetchType=IDS`，ID 入顶层 `value`，无 `condition` |
| 按条件查一条 | `RETRIEVE` | `fetchType=CONDITION` + `condition[]` |
| 按条件查多条 | `RETRIEVE_ARRAY` | `condition[]`，无 `title`、无 `selectParam` |
| 判断 X 是不是 Y | `BRANCH` | 2 分支；ifBranch 要有 `expression`(BOOLEAN)，elseBranch `expression=null` |
| 遍历一批逐条处理 | `RETRIEVE_ARRAY → FOR_EACH → 写操作` | `FOR_EACH.selectParam` 必须 `type=ARRAY` + `dtoType`；循环项经循环内 RETRIEVE(IDS) 承接 |
| 改实体字段/状态 | `CHANGE_ENTITY` | `attrs[{attrType,value}]`，`value` 用 `Simple`；无 structure/app 键 |
| 改变量 | `CHANGE_VARIABLE` | 整体赋值 `value{}` 或字段级 `attrs[]`（两件不同的事）|
| 存中间值 | `CREATE_VARIABLE` | 按值类型选 `paramType` |
| 算布尔结果给出参 | `CREATE_VARIABLE` 默认值 + 分支内 `CHANGE_VARIABLE` | 不要两分支各建同名变量 |
| 对外返回 | `END` | `paramType=BASIC` + `basic=<类型>` |
| 复用已有逻辑 | `SUB_MICROFLOW` | 只收 `state=RELEASE` |

### 3. 实体名不能凭业务名猜

用户说「数据源」，实体真名可能是「数据源配置信息」。

```python
# 错：精确匹配会落空
lr.find_entity(APP, APP_NAME, label="数据源")     # LookupError

# 对：先拉全量，按关键词过滤
for e in lr.entity(APP, APP_NAME):                 # 已递归拍平
    if re.search(r"数据源|连接|jdbc", (e.get("caption") or "")):
        print(e["caption"], e.get("dtoFullName"))
```

### 4. 字段靠 caption 反查，不靠英文习惯

```python
m = lr.entity_model(APP, APP_NAME, label="数据源配置信息")
for name, a in sorted(m["attributes"].items()):
    print(name, a["dataType"], a.get("caption"))   # enabled BOOLEAN 是否启用
```

「是否启用」→ `enabled` BOOLEAN；「JDBC URL」→ `jdbcUrl` STRING。
猜字段名的后果：`checkSchema` 能过，前端显示成完整路径 / 失效。

### 5. 「A 则 X 否则 Y」的变量形态

```
错：ifBranch 里 CREATE_VARIABLE vR=true
    elseBranch 里 CREATE_VARIABLE vR=false      → 变量重名，UDC_DTO_0001

对：CREATE_VARIABLE vR=false          ← 前置给默认值
    BRANCH ifBranch(...)：CHANGE_VARIABLE vR=true
           elseBranch：留空
    END → 引用 vR
```

## 歧义点：必须让用户拍板，不要替他选

业务原话天然含糊，选错的方向做出来「形态全对、能发布、errors=0，但业务是错的」。

| 类型 | 例 | 候选与后果 |
|---|---|---|
| 「其他」的范围 | 查其他启用的数据源 | A 排除自己（会把不该停用的停掉）/ B 同角色（会漏掉该停用的）/ C 含自己 |
| 「修改数据」的范围 | 改成停用「然后修改数据」 | 只改 `enabled` / 还要改 `updateTime` / 还要写停用原因 |
| 判断对象 | 「判断 jdbc 是否含 mysql」 | 当前这条 / 查出来的那一批 |
| 匹配精度 | 是否含 mysql | 区分大小写 / 只认 `jdbc:mysql` 前缀 |

每个歧义给候选 + **各自业务后果**，用户一句话就能选。

## 常用判断函数（`function_catalog.json` 实测）

| 需求 | 函数 | 参数 |
|---|---|---|
| 文本是否包含 | `containsText` | 文本包含（指定文本, 被包含文本）|
| 集合是否全含 | `contains` | 包含(全部)（参数, 被包含变量）|
| 集合含任一 | `containsAny` | 包含任一 |
| 查位置 | `find` | 查找文本位置（查找文本, 被查找文本, 起始位置）|
| 判空 | `isNull` / `isNotNull` | 为空 / 不为空 |

动工前先查 `components/udc/microflow/function_catalog.json`（88 个函数），别按中文描述猜函数名。

## 完整范例：数据源有效校验（v2 修正版，10 节点）

需求原话见上。伪代码见「拆解步骤 0」。对应节点（v1 错在组合层，v2 修正）：

```
[开始] MANUAL，入参 BASIC/BIGINTEGER（name 自动生成 _FLOW_INPUT_xxx，desc=数据源ID）
 1. RETRIEVE            ID 查询（value 引入参，nodeInfo=MFStartNode），
                        nullHandling=TERMINATION + 提示「数据源不存在」
 2. CREATE_VARIABLE     result=false（BASIC/BOOLEAN，默认值）
 3. BRANCH_1            if (ds.enabled == true)   ← 表达式 context 挂 ds 出参变量树
    ifBranch:
      3.1 RETRIEVE_ARRAY   enabled==true && id != 入参（NEQ+CONTEXT_VARIABLE）★ 排除自己
      3.2 FOR_EACH         遍历 others
            3.2.1 RETRIEVE        ID 查询（value 引循环项.id）——循环项经它承接
            3.2.2 CHANGE_ENTITY   enabled=false（selectParam 引 3.2.1 出参）
      3.3 BRANCH_2         if (containsText(ds.jdbcUrl, "mysql"))  ★ 嵌套
            ifBranch:  CHANGE_VARIABLE result=true（else 留空）
    elseBranch: 空
 4. END                 BASIC/BOOLEAN，引用 result（_FLOW_OUTPUT_xxx）
```

组合要点：BRANCH_2 在 BRANCH_1 的 ifBranch.nodes 里（嵌套 BRANCH 真实存在）；
不建 vJdbc 中转变量——表达式 context 直接挂 ds 节点，token 三级引 ds.jdbcUrl；
循环项经 RETRIEVE 承接再 CHANGE_ENTITY（直引 FOR_EACH 出参真实出现 0 次）。

动工前的构造器依赖（应先确认已支持）：END BASIC 布尔出参、`expression_build.field_equals` /
`text_contains`（走 /expression/transform）、组装器 `finish(basic_out="BOOLEAN")`。

## 交付后留给用户检查，不要立刻删

自验收（UI 逐节点无红字）通过后**不要删**——用户要亲自在页面上点检查。发布后给他编辑器直达 URL：
`/main/child-frame/udc/app-design/rule/microflow/editor/<mid>?appId=<appId>`
验收完即删他会问「你建在哪里」并要求重新发布留在环境里检查；等他确认没问题再清理。
另外：他检查时会把 RELEASE 打回 DRAFT，这是已知行为，他看完说一声就重新发布。

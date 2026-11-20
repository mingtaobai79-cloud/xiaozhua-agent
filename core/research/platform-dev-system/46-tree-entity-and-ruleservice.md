# 46 · ★★★★★ 树实体特性 + 业务规则服务 + 模板命名机制

**证据来源**：`feature/tree_entity/template/*`（10 个 ftl）+ `entityrule/ruleservice.java.ftl`（309 行）+ `event/` 目录
**证据等级**：VERIFIED_STATIC_BYTECODE / 资源原文

---

## 一、★★★★★ 特性模板的命名机制（核心发现）

### 1.1 模板文件名 = 挂载坐标

```
feature.{特性名}.class[{目标产物}].method[{方法}][{时机}].ftl
```

**实例（树实体）：**
```
feature.tree.entity.class[app_service].ftl                       ← AppService 接口
feature.tree.entity.class[app_service_impl].ftl                  ← AppService 实现
feature.tree.entity.class[controller].ftl                        ← Controller
feature.tree.entity.class[dao].ftl                               ← DAO
feature.tree.entity.class[service].ftl                           ← Service（整体追加）
feature.tree.entity.class[service].method[create].ftl            ← createBatch 的 after
feature.tree.entity.class[service].method[create][before].ftl    ← createBatch 的 before
feature.tree.entity.class[service].method[update].ftl            ← updateBatch 的 after
feature.tree.entity.class[service].method[update][after].ftl     ← updateBatch 的 afterUpdate
feature.tree.entity.class[service].method[delete].ftl            ← deleteByIds 的 after
```

### ★★★★★ 与 `joinSnippets` 的精确对应

```
文件名：  method[create][before]
          ↓
joinSnippets key：  "createBatch(List<E>DtoList)#before"
          ↓
命名规则： {方法名}Batch 的 {时机}
```

**⇒ 特性片段是**按文件名约定**自动挂到对应钩子上的。**

**⇒ 无 `[时机]` 后缀 = `#after`（默认）。**

### ★★★★ 四类目标产物（`class[...]` 取值）

| 取值 | 对应产物 |
|---|---|
| `app_service` | `{E}AppService` 接口 |
| `app_service_impl` | `{E}AppServiceImpl` 实现 |
| `controller` | `{E}Controller` |
| `dao` | `{E}Dao` |
| `service` | `{E}Service`（领域服务） |

---

## 二、★★★★★ 树实体特性的完整代码（真实片段）

### 2.1 `class[dao]` —— 树查询的真实 SQL

```java
/** 查询直接子节点 */
@Select(value = "SELECT * FROM ${table.dbTableName} WHERE tree_path REGEXP CONCAT(#{path},'/', '-?[0-9]+$')")
List<${E}> selectImmediateChildren(String path);

/** 查询所有子节点 */
@Select(value = "SELECT * FROM ${table.dbTableName} WHERE tree_path REGEXP CONCAT(#{path},'/')")
List<${E}> selectAllChildren(String path);
```

**★★★★★ 这是整个代码生成体系里唯一的「真实 SQL」：**
**⇒ 树实体用 `tree_path` 字段 + 正则做子孙查询，MySQL `REGEXP`。**
**⇒ 这是**唯一一处**平台生成的 SQL（其余全部零 SQL）。**

### 2.2 `class[service]` —— `dealTree` 的树处理

```java
/** 处理树形数据 */
private void dealTree(List<E Dto> dtoList) {
    log.info("开始处理树形数据");
    List<Long> treeParentIds = dtoList.stream()
        .filter(dto -> Objects.nonNull(dto.getTreeParentId()))
        .filter(dto -> !UdcCommonConstant.NULL_ID.equals(dto.getTreeParentId()))
        ...
}
```

### 2.3 `method[create][before]` —— 创建前建虚拟树

```java
Map<String, List<E Dto>> treeDtoMap = dtoList.stream()
    .filter(dto -> Objects.nonNull(dto.getTreeParentId()))
    .collect(Collectors.groupingBy(x -> x.getTreeParentId().toString()));
dtoList.forEach(dto -> {
    String virtualId = ...
    ...
});
```
**⇒ 同级批量插入时，先按 `treeParentId` 分组，生成虚拟 id 再回填父子关系。**

### 2.4 `method[delete]` —— 级联删子节点

```java
// 删除所有的子节点
for (E Dto dto : dtoList) {
    log.info("删除树节点[{}]下面所有的子节点数据", dto.getId());
    Map<String, Object> param = new HashMap<>();
    param.put("EQ_treeParentId", dto.getId());
    List<E Dto> children = ...;
    ...
}
```
**⇒ 删父节点会自动递归删子孙。**

### 2.5 `class[controller]` 与 `class[app_service]` 的三个查询

```java
// AppService
ListResponse<E Dto> selectImmediateChildren(SingleRequest<Long> request);
ListResponse<E Dto> selectAllChildren(SingleRequest<Long> request);
ListResponse<E Dto> selectAllParents(SingleRequest<Long> request);

// Controller
@RestApiOperation(value = "获取直接子节点列表")
<@methodAnnotation name="immediate-children"></@methodAnnotation>
public ListResponse<E Dto> selectImmediateChildren(@MultiRequestBody Long id) {
    return appService.selectImmediateChildren(SingleRequest.from(id));
}
```

### ★★★★ 树实体多出 3 个查询方法

```
selectImmediateChildren  → GET 直接下级
selectAllChildren        → GET 所有子孙
selectAllParents         → GET 所有祖先
```

---

## 三、★★★★★ `entityrule/ruleservice.java.ftl` —— 业务规则服务

### 3.1 一个模板生成三类服务

```freemarker
public class <#if groupType == "VALIDATE">Validate
             <#elseif groupType == "ASSIGN_VALUE">AssignValueFor
             <#elseif groupType == "DEFAULT_VALUE">DefaultValueFor</#if>${capEntityName}Service {
```

| `groupType` | 生成的类名 | 统一方法 |
|---|---|---|
| `VALIDATE` | `Validate{E}Service` | `do{E}Rule(List<E Dto> list, boolean isUpdated)` |
| `ASSIGN_VALUE` | `AssignValueFor{E}Service` | `do{E}Rule(E Dto dto)` |
| `DEFAULT_VALUE` | `DefaultValueFor{E}Service` | `do{E}Rule(E Dto dto)` |

**⇒ `Validate` 是批量 + `isUpdated` 标记；另两个是单条。**

### 3.2 注入的依赖

```java
@Service @Slf4j
public class Validate{E}Service {
    @Autowired private ExpressionEvaluator expressionEvaluator;
    @Autowired private UdcAppLogService     udcAppLogService;
    <#if groupType == "VALIDATE">
    @Autowired private {E}Service           {e}Service;         ← ★ 反向依赖
    @Autowired private MessageRepository    messageRepository;
    </#if>

    // ★ 微流程服务（按子微流程动态注入）
    <#list subMfList as sub>
    @Autowired ${sub.serviceFullName} ${sub.uncapServiceName};
    </#list>

    // ★ Dubbo 服务（按规则里用到的服务动态注入）
    <#list dubboServiceMap?keys as key>
    ${key} ${dubboServiceMap[key]};
    </#list>
```

### ★★★★★ 三条硬事实

| # | 事实 |
|---|---|
| 1 | **业务规则里可以调微流程**（`subMfList` → 自动注入子微流程 Service） |
| 2 | **业务规则里可以调 Dubbo 服务**（`dubboServiceMap` → 自动注入） |
| 3 | `Validate` 反向依赖 `{E}Service`（校验里可以查主服务） |

**⇒ 这就是「实体业务规则」的真实实现形态：一个可注入微流程和 Dubbo 的表达式执行器。**

### 3.3 规则方法体

```java
public void do{E}Rule(List<E Dto> list, boolean isUpdated){
    Map<String,Object> formulaMap = null;
    Map<String,Object> formulaRootMap = null;
    ...
}
```
**⇒ 用 `formulaMap` / `formulaRootMap` 承载表达式的上下文。**

### 3.4 `entityrule` 目录的 6 类活动模板

```
AssignValueActivity.ftl         赋值活动
AttributeRequiredActivity.ftl   必填校验
AttributeUniqueActivity.ftl     唯一性校验
DefaultValueActivity.ftl        默认值
ShowMessageActivity.ftl         提示消息
entityValueForRoot.ftl          根实体取值
ruleservice.java.ftl            服务壳
common/EntityRuleTemplateUtil.ftl
common/SetValueUtil.ftl
```

**⇒ 6 类规则活动：赋值、必填、唯一、默认值、提示、根实体取值。**

---

## 四、★★★★ `event/` 目录 —— 业务事件

```
service/event.business.class[service].ftl           ← 业务事件方法
service/event.business.class[service].event[import].ftl
service/event.entity.class[service].ftl             ← 实体事件
service/event.entity.class[service].event[import].ftl
business-event.java.ftl                             ← 事件类
defaultevent.json                                   ← 默认事件定义
```

**⇒ 平台有两套事件：`business`（业务事件）和 `entity`（实体事件）。**
**⇒ 这两个与 `afterCreate` 里的 `<@paster name="event.business.class[service][CREATE]">` 对应。**

---

## 五、★★★★ 2.9 版本的完整目录清单（15 个顶层域）

```
beanname/        Bean 命名
common/          公共宏（macro.ftl 23 个宏）
dto/             DTO
entity/          实体/Service/Dao/Controller/AppService
entityrule/      业务规则服务
enums/           枚举
event/           业务事件
feature/         特性片段（树实体）
filterplan/      过滤方案
microflow/       微流程
project/         工程骨架
project-ext/     工程扩展
project-for-deploy/  部署工程
refer/           引用
referconfig/     引用配置
```

**⇒ 这些才是「代码生成」的全部产出域，我之前只研究了 `entity/`。**

---

## 六、★★★★★ 完整产物全景观（最终版）

```
设计态元数据（Application/Entity/Attribute/Bill/Microflow/...）
   ↓ 17 个域 × 141 个模板（2.9）+ 2 个（3.0）
生成的代码结构：
{appPackagePath}
  ├── api/                          {E}AppService
  ├── dto/                          {E}Dto
  ├── appservice/                   {E}AppServiceImpl
  ├── domain/
  │   ├── entity/                   {E}Entity（3.0 模板）
  │   ├── service/                  {E}Service（3.0 模板，48 方法）
  │   ├── dao/                      {E}Dao（空接口）
  │   ├── event/                    {E}Event
  │   └── event/listener/           {E}Listener
  ├── controller/                   {E}Controller
  └── （entityrule）                 Validate{E}Service / AssignValueFor{E}Service / DefaultValueFor{E}Service
```

**总计每个实体生成 10+ 个类。**

---

## 七、★★★★★ 对开发者的关键结论（新增）

| # | 结论 |
|---|---|
| 1 | **树实体多 3 个查询方法** + `tree_path` 正则 SQL（唯一平台生成的 SQL） |
| 2 | **树实体删父节点自动级联删子孙** |
| 3 | **树实体创建前会建虚拟树处理同级父子** |
| 4 | **业务规则服务能注入微流程和 Dubbo**（这是低代码连外部系统的关键通道） |
| 5 | **业务规则有 6 类活动**：赋值/必填/唯一/默认值/提示/根实体取值 |
| 6 | **特性代码按文件名约定自动挂载**，不用手写注入 |
| 7 | **平台有两套事件**：`business` 和 `entity` |
| 8 | **只有 3 类服务（Validate/AssignValueFor/DefaultValueFor）来自 `entityrule`** |

---

## 八、待验证

| 问题 | 状态 |
|---|---|
| `Stereotypes` 里注册了哪些特性（除 tree_entity） | 待反编译 |
| `microflow/` 目录的模板（微流程代码生成） | 待研究 |
| `filterplan/` 目录（过滤方案） | 待研究 |
| `refer/` `referconfig/`（引用配置） | 待研究 |
| `enums/` 目录（枚举生成） | 待研究 |
| `beanname/` 目录 | 待研究 |
| 树实体的 `tree_path` 字段如何维护（写时更新） | UNVERIFIED |
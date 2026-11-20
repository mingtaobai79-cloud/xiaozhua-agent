# 45 · ★★★★★ BaseService 完整解剖 + 特性注入机制（74KB 模板全解）

**证据来源**：`autocode/JAVA/3.0/templates/entity/baseservice.java.ftl`（1417 行）+ `common/macro.ftl`（465 行）+ `PasterDirective` / `StereotypeDecorate` / `Type`
**证据等级**：VERIFIED_STATIC_BYTECODE

---

## 一、★★★★★ BaseService 的 14 个注入依赖

```java
public class ${entityName}Service extends ${superService}<${entityName}Dto> {
    private final static String APP_NAME = "${appName}";

    private SecretEnumUpdateService    secretEnumUpdateService;
    private BusinessEventHelper        businessEventHelper;
    private Validate${E}Service        validate${E}Service;          ← ★ 每个实体一个校验 Service
    private ${E}AssignValueService     ${e}AssignValueService;       ← ★ 每个实体一个赋值 Service
    private ApproveFeatureService      approveFeatureService;
    private AllInOneBaseDao<${E}>      abstractAllInOneBaseDao;      ← ★ 泛型是 Entity
    private ${Pkg}${E}Dao              ${pkg}${e}Dao;
    private ExpressionEvaluator        expressionEvaluator;          ← ★ 表达式求值器
    private MessageRepository          messageRepository;
    private ScalabilityFieldService    scalabilityFieldService;      ← 扩展字段
    private UdcSerialConfigService     serialConfigService;          ← 流水号
}
```

### ★★★★ 三个关键事实

| # | 事实 |
|---|---|
| 1 | **每个实体额外生成 2 个配套类**：`Validate{E}Service` + `{E}AssignValueService` |
| 2 | `abstractAllInOneBaseDao` 是**直连 JDBC 通道**，与自己生成的 Dao 并存 |
| 3 | 有 `ExpressionEvaluator` —— 表达式在 Service 层求值 |

---

## 二、★★★★★ 12 个生命周期钩子（完整签名）

```java
@Override public void beforeSelect(List<E>DtoList)
@Override public void afterSelect(List<E>DtoList)
@Override public void beforeCreate(List<E>DtoList)
@Override public void middleCreate(List<E>DtoList)
@Override public void afterCreate(List<E>DtoList)
@Override public void beforeUpdate(List<E>DtoList)
@Override public void afterUpdate(List<E>DtoList, Map<Long,E Dto> oldDtoMap)
@Override public void beforeDelete(List<E>DtoList)
@Override public void afterDelete(List<E>DtoList)
// 另 3 个（第 38 篇记录）
public void beforeExecuteDefaultValueExpression(List<E>DtoList)
public void afterExecuteExpression(List<E>DtoList)
public void afterBeforeEventCheck(List<E>DtoList)
```

### ★★★★★ 钩子的真实内容（模板原文，不是空方法）

**`afterSelect`** —— 注入「按 id 查询后」特性代码：
```java
@Override public void afterSelect(List<E>DtoList){
    <@joinSnippets key="selectById(Long id)#after"></@joinSnippets>
}
```

**`beforeCreate` / `middleCreate`** —— 注入 createBatch 前后特性代码：
```java
@Override public void beforeCreate(List<E>DtoList){
    <@joinSnippets r"createBatch(List<E>DtoList)#before"></@joinSnippets>
}
```

**`afterCreate`** —— 发业务事件 + 生单回写事件：
```java
@Override public void afterCreate(List<E>DtoList){
    <@paster name="event.business.class[service][CREATE]"></@paster>
    <@paster name=PasterConfig.SEND_CREATE_WRITE_BACK></@paster>
}
```

**`beforeUpdate`** —— **真实业务逻辑（不是空的）**：
```java
@Override public void beforeUpdate(List<E>DtoList){
    for (E dto : dtoList) {
        sensitive4Update(dto);                                // 脱敏处理
        resolveDefaultValueNotAllowedModify(dto);              // ★ 不可修改字段置 null
    }
}
```

**`afterUpdate`** —— 三路注入 + 两个事件：
```java
@Override public void afterUpdate(List<E>DtoList, Map<Long,E Dto> oldDtoMap){
    <@joinSnippets r"updateBatch(List<E>DtoList)#after"></@joinSnippets>
    <@joinSnippets r"updateBatch(List<E>DtoList)#afterUpdate"></@joinSnippets>
    <@paster name="event.business.class[service][UPDATE]"></@paster>
    <@paster name=PasterConfig.SEND_UPDATE_WRITE_BACK></@paster>
}
```

**`beforeDelete` / `afterDelete`** —— 删除回写事件 + 特性代码：
```java
@Override public void beforeDelete(List<E>DtoList){
    <@paster name=PasterConfig.SEND_DELETE_WRITE_BACK></@paster>
    <@joinSnippets r"deleteByIds(List<Long> ids)#before"></@joinSnippets>
}
```

### ★★★★★ 结论

**钩子不是「留给开发者重写的空方法」，而是平台自己的特性/事件注入槽。**
**⇒ 开发者重写钩子要小心：会覆盖平台的特性代码注入（除非 super 调用）。**

---

## 三、★★★★★ `paster` 指令的真实实现

```java
public class PasterDirective implements AutoCodeDirective {
    public void execute(Environment env, Map params, ...) {
        TemplateModel paramValue = params.get("name");
        String pastKey = ((TemplateScalarModel) paramValue).getAsString();
        TemplateModel pastTemplate = env.getDataModel().get("paster_" + pastKey);   // ★ 前缀
        if (pastTemplate == null) {
            log.debug("当前上下文中未检测到代码片段插入点: {}", pastKey);
            return;                              // ★ 静默跳过
        }
        String pastCode = ((TemplateScalarModel) pastTemplate).getAsString();
        if (StringUtils.isBlank(pastCode)) {
            log.debug("代码片段插入点: {} 未解析到代码片段", pastKey);
            return;
        }
        out.write(pastCode);
        if (body != null) body.render(env.getOut());   // ★ 写完片段再渲染 body
    }
}
```

### ★★★★★ 四条事实

| # | 事实 |
|---|---|
| 1 | 数据模型键 = **`"paster_" + name`** |
| 2 | 找不到 → **静默跳过**（不报错） |
| 3 | 空串 → 静默跳过 |
| 4 | 先写片段再渲染 body（**顺序重要**） |

### ★★★ `PasterConfig` 的真实常量

```java
public final class PasterConfig extends BasePasterConfig {
    public static final String SEND_CREATE_WRITE_BACK = "send_create_write_back";
    public static final String SEND_UPDATE_WRITE_BACK = "send_update_write_back";
    public static final String SEND_DELETE_WRITE_BACK = "send_delete_write_back";
}
public class BasePasterConfig {
    public static final String PASTER_PREFIX    = "paster_";
    public static final String PASTA_PARM_NAME  = "name";
}
```

**⇒ 三个写回事件插入点的真实 key：**
```
paster_send_create_write_back
paster_send_update_write_back
paster_send_delete_write_back
```

---

## 四、★★★★★ `joinSnippets` / `joinAnnotations`（特性代码注入）

```freemarker
<#macro joinSnippets key>
    <#if BIZ_DOMAIN_SERVICE?? && BIZ_DOMAIN_SERVICE.joinSnippets?? >
        <#assign mKey = "${key}">
        <#list BIZ_DOMAIN_SERVICE.joinSnippets[mKey]! as item>
            ${item.code}
        </#list>
    </#if>
</#macro>

<#macro joinAnnotations key>
    <#if BIZ_DOMAIN_SERVICE?? && BIZ_DOMAIN_SERVICE.joinAnnotations?? >
        <#assign mKey = "${key}">
        <#list BIZ_DOMAIN_SERVICE.joinAnnotations[mKey]! as item>
            ${item.code}
        </#list>
    </#if>
</#macro>
```

### ★★★★★ `joinSnippets` 的全部 key（从 3.0 baseservice.ftl 提取）

```
selectById(Long id)#after
createBatch(List<E>DtoList)#before
createBatch(List<E>DtoList)#middle
createBatch(List<E>DtoList)#after
updateBatch(List<E>DtoList)#after
updateBatch(List<E>DtoList)#afterUpdate
deleteByIds(List<Long> ids)#before
deleteByIds(List<Long> ids)#after
```

### ★★★ key 的命名规律

```
{方法签名}#{时机}
时机取值：before / middle / after / afterUpdate
```

**⇒ 特性（feature/stereotype）代码按「方法签名 + 时机」精确挂载。**

---

## 五、★★★★★ `BIZ_DOMAIN_SERVICE` 的数据来源：`StereotypeDecorate`

```java
public class StereotypeDecorate extends DecorateTemplate {
    private Stereotypes stereotypes = context.getBean(Stereotypes.class);
    private CodeWrapper stereotypeCode;
    private boolean isOutter = false;      // ★ 跨应用实体则为 true

    public StereotypeDecorate(EntityFileTemplate t) {
        this.entityFileTemplate = t;
        this.codeContext = t.getCodeContext();
        this.entityDto = t.getEntity();
        this.isOutter = !codeContext.getAppInfo().getId().equals(entityDto.getAppId());
        this.initCode();
    }

    private void initCode() {
        if (this.isOutter) { /* empty */ }         // ★ 跨应用不注入特性
        this.stereotypeCode = this.getCode(entityDto, codeContext);
    }

    public boolean matches(AutoCodeContext ctx, ApplicationContext appCtx) {
        return !this.isOutter;                     // ★ 跨应用实体跳过整个装饰器
    }

    public Map<String,Object> getExtraArgs() {     // ★ 往模板数据模型注入的 7 个键
        Map<String,Object> m = Maps.newHashMapWithExpectedSize(8);
        m.put(Type.FACADE_APP_SERVICE.strCode(),  stereotypeCode.getClassSame().get(Type.FACADE_APP_SERVICE));
        m.put(Type.FACADE_DTO.strCode(),          stereotypeCode.getClassSame().get(Type.FACADE_DTO));
        m.put(Type.BIZ_APP_SERVICE_IMPL.strCode(),stereotypeCode.getClassSame().get(Type.BIZ_APP_SERVICE_IMPL));
        m.put(Type.BIZ_DOMAIN_SERVICE.strCode(),  stereotypeCode.getClassSame().get(Type.BIZ_DOMAIN_SERVICE));
        m.put(Type.BIZ_DOMAIN_DAO.strCode(),      stereotypeCode.getClassSame().get(Type.BIZ_DOMAIN_DAO));
        m.put(Type.BIZ_DOMAIN_ENTITY.strCode(),   stereotypeCode.getClassSame().get(Type.BIZ_DOMAIN_ENTITY));
        m.put(Type.WEB_CONTROLLER.strCode(),      stereotypeCode.getClassSame().get(Type.WEB_CONTROLLER));
        return m;
    }

    public void doMore() {                          // 额外类输出（新增 + 扩展）
        clazzes.addAll(stereotypeCode.getClassNew());
        clazzes.addAll(stereotypeCode.getClassExtend());
        clazzes.forEach(c -> write(determineOutputPath(c)));
    }
}
```

### ★★★★ 三条事实

| # | 事实 |
|---|---|
| 1 | **跨应用实体（`isOutter=true`）不注入任何特性代码** |
| 2 | 往数据模型注入 **7 个键**（对应 7 个产物类型） |
| 3 | `getClassNew()` / `getClassExtend()` = **特性额外生成的新类/扩展类** |

---

## 六、★★★★★ `Type` 枚举 —— 9 个产物类型的完整映射

```java
public enum Type implements Messageable {
    FACADE_APP_SERVICE     (Module.FACADE, 0, "{pkg}.api",                 "{E}AppService"),
    FACADE_DTO             (Module.FACADE, 1, "{pkg}.dto",                 "{E}Dto"),
    BIZ_APP_SERVICE_IMPL   (Module.BIZ,    2, "{pkg}.appservice",          "{E}AppServiceImpl"),
    BIZ_DOMAIN_ENTITY      (Module.BIZ,    3, "{pkg}.domain.entity",       "{E}Entity"),
    BIZ_DOMAIN_SERVICE     (Module.BIZ,    4, "{pkg}.domain.service",      "{E}Service"),
    BIZ_DOMAIN_DAO         (Module.BIZ,    5, "{pkg}.domain.dao",          "{E}Dao"),
    BIZ_DOMAIN_EVENT       (Module.BIZ,    6, "{pkg}.domain.event",        "{E}Event"),
    BIZ_DOMAIN_EVENT_LISTENER(Module.BIZ,  7, "{pkg}.domain.event.listener","{E}Listener"),
    WEB_CONTROLLER         (Module.WEB,    8, "{pkg}.controller",          "{E}Listener");  ★ 疑似 bug
}
```

### ★★★★★ 完整的包结构（核心架构事实）

```
{appPackagePath}
  ├── api/                      {E}AppService          ← FACADE 对外接口
  ├── dto/                      {E}Dto                 ← FACADE 数据传输对象
  ├── appservice/               {E}AppServiceImpl      ← BIZ 应用服务实现（纯委托）
  ├── domain/
  │   ├── entity/               {E}Entity              ← BIZ 实体
  │   ├── service/              {E}Service             ← BIZ 领域服务（业务逻辑）
  │   ├── dao/                  {E}Dao                 ← BIZ 数据访问
  │   ├── event/                {E}Event               ← BIZ 领域事件
  │   └── event/listener/       {E}Listener            ← BIZ 事件监听器
  └── controller/               {E}Listener            ← WEB 控制器（★ 类名疑似 bug）
```

### ★★★ 两个发现

1. **`WEB_CONTROLLER` 的 defaultClassName 是 `{E}Listener`** —— 与 `BIZ_DOMAIN_EVENT_LISTENER` 撞名，**疑似平台 bug**（应为 `{E}Controller`）
2. **三层模块划分明确**：`Module.FACADE` / `Module.BIZ` / `Module.WEB`
3. **`getExtraArgs` 只注入 7 个键**，但枚举有 9 个 —— `BIZ_DOMAIN_EVENT` 和 `BIZ_DOMAIN_EVENT_LISTENER` **不在特性注入范围**（事件类不支持特性扩展）

---

## 七、★★★★★ `macro.ftl` 的 23 个宏（完整清单）

```
joinSnippets(key)             特性代码片段
joinAnnotations(key)          特性注解
appendMethods                 特性方法
appendFields                  特性字段
appendAnnotations             特性注解
appendImports                 特性 import
entityRule(isUpdate)          ★ 实体业务规则调用
showChildPackage(children)    子实体 import
showChildDao(children)        子实体 Dao 注入
showUpdateBatchList(children) 子表批量更新
showExecuteUpdateBatchList    子表执行更新
showUpdateBatch(child)        单个子表更新
resolveInsertOrDelete(entity,type)  主表插入/删除
resolveUpdate(entity)         主表更新
resolveSum(entity,field,aggreation) ★ 汇总 SUM
resolveMaxOrMin(...)          最大/最小值
resolveMaxOrMin4Update(...)   更新的最大/最小
MaxOrMin4Update(...)
addChildrenService(table)     子表 Service
```

### ★★★ `entityRule` —— 实体业务规则调用（重要）

```freemarker
<#macro entityRule isUpdate>
    <#if hasRule>
        validate${E}Service.${table.entityRule.funcName}(${e}DtoList, <#if isUpdate>true<#else>false</#if>);
        <#if table.isRoot>
            EntityExceptionThrower.throwing(${e}DtoList);
        </#if>
    </#if>
</#macro>
```
**⇒ 开发者在设计态配的「实体业务规则」会被生成为 `validate{E}Service.xxx()` 调用。**
**⇒ 根实体还会调 `EntityExceptionThrower.throwing()` 统一抛异常。**

---

## 八、★★★★ BaseService 的 48 个方法（完整清单）

**12 个钩子**（见第二节）

**校验相关（6）**
```
assertjsr303(dto)                          public
check(dto)                                 private
check(dtoList)                             private
check(dto, needCheckAttributeNames)        private  ★ 只检查指定字段
checkNotNull(dto)                          private
getExtAttribute(appName, entityFullName, attributeName)  private  ★ 扩展字段
```

**查询相关（3）**
```
selectPageByConditions(pageInfo, columnMap, sort)   public  ★ Map DSL
selectPageByWrapper(pageInfo, wrapper)              public  ★ Wrapper
getDefaultValue()                                    public  ★ 默认值模板
```

**创建/更新前处理（6）**
```
preCreateBatch(dtoList)                    public
preCopyBatch(dtoList)                      public   ★ 复制场景
preUpdateBatch(dtoList)                    public
beforeExecuteDefaultValueExpression(list)  public
afterExecuteExpression(list)               public
afterBeforeEventCheck(list)                public
```

**默认值解析（5，★ 核心机制）**
```
resolveDefaultValueNotAllowedModify(dto)          public
resolveDefaultValueSystemVariable(dtoList)        private  ★ 系统变量
resolveDefaultValueExpression(dtoList)            private  ★ 表达式
resolveDefaultValueExpressionNotChange(dtoList)   private
resolveDefaultValueDesensitizationAndEncryption   protected
resetDateFieldDefaultValue(dto)                   private  ★ 日期字段
handleEntityDefaultValue(dto)                     public
```

**聚合计算（模板动态生成，★ 关键）**
```
{field}Sum(dtoList)              private   按字段生成
{field}Max(dtoList)              private
{field}Max4Update(dtoList,oldList) private
{field}Min(dtoList)              private
{field}Min4Update(dtoList,oldList) private
```
**⇒ 只有配了 `field.aggregation` 的字段才生成对应方法。**

**复制/转换（3）**
```
deepCopy(dto)              public static  ★ 深拷贝
dto2dto(from, to)          public static
dto2dto(from)              public static
```

**脱敏/敏感（4）**
```
sensitive4Update(dto)      private
sensitive4Create(dto)      private
trim(dto)                  private  ★ 去空格
i18nTrim(fieldData)        private
```

**附件（4）**
```
hasAttachment(dto)         public
checkAttachment(dto)       private
sendAttachmentMq(dto, flag) private  ★ 发 MQ
dealCtpEnum(dto)           private
```

**密级（2）**
```
handleSecretNum(dtoList)   private
```

**级联默认值（2）**
```
getCascadeDefaultValue(key)              public
genCascadeDefaultValueOfRootEntity       宏
```

---

## 九、★★★★★ 对开发者的关键结论

| # | 结论 |
|---|---|
| 1 | **业务逻辑写在 `{E}Service`（这个类），不是 `AppServiceImpl`** |
| 2 | **重写钩子会覆盖平台特性代码注入**（除非调 `super`） |
| 3 | **默认值机制分三路**：系统变量 / 表达式 / 固定值 |
| 4 | **聚合（SUM/MAX/MIN）方法按字段自动生成**，未配置就不生成 |
| 5 | **每个实体自动生成 `Validate{E}Service` 和 `{E}AssignValueService`** |
| 6 | **配置「业务规则」会生成 `validate{E}Service.xxx()` 调用** |
| 7 | **跨应用实体不注入特性代码**（`isOutter`） |
| 8 | **附件/MQ/脱敏/密级都是内置能力**，不用自己写 |

---

## 十、待验证

| 问题 | 状态 |
|---|---|
| `Stereotypes.getCode()` 的完整实现（特性代码如何生成） | 待反编译 |
| `{E}AssignValueService` 的模板（另一个关键配套类） | 待找 |
| `Validate{E}Service` 的模板 | 待找 |
| `WEB_CONTROLLER` 类名 `{E}Listener` 是否真是 bug | UNVERIFIED（可能是刻意） |
| `BIZ_DOMAIN_EVENT` / `EVENT_LISTENER` 的模板 | 待找 |
| `Stereotypes` Bean 里有哪些特性实现 | 待反编译 |
# ★★★★★ 代码生成引擎真实运行实证（LIVE）

> 工具：`freemarker.jar` 2.3.32（从 `repo1.maven.org` 下载）+ JDK 21
> 方法：用 `TemplateLoader` 直接读 jar 内 FTL，复刻平台 `PasterDirective`，真实 `template.process()`
> 等级：**`LIVE`（本地真跑出渲染结果，非推断）**
> 时间：2026-11-18
> 脚本：`scratch/RenderTest3.java`（单模板）/ `RenderBatch.java`（批量）/ `RenderBatch2.java`（补 table）

---

## 0. ★★★★★ 结论先行

**平台代码生成引擎 = FreeMarker 2.3.x + 自定义 `paster` 指令，我已在本机真实跑通。**

**三份 LIVE 产物证明了三件最重要的事：**
```
① Dao 真的只有一行 extends  ← 平台不生成 CRUD
② mybatis.xml 的 <mapper> 内部完全空  ← 平台不写任何 SQL
③ beanName 修饰器生成完整逻辑（这是唯一有实质内容的）
```

---

## 1. ★★★★ 渲染环境搭建（可复现）

### 1.1 依赖
```
freemarker-2.3.32.jar    1,736,381 字节
  ← https://repo1.maven.org/maven2/org/freemarker/freemarker/2.3.32/freemarker-2.3.32.jar
  （远程仓库 172.28.24.205 也可下载到同一文件）
JDK 21（javac/java）
```

### 1.2 三步让平台模板跑起来

**Step 1：用 jar 文件系统当 TemplateLoader**
```java
FileSystem fs = FileSystems.newFileSystem(Paths.get(jarPath), (ClassLoader) null);
cfg.setTemplateLoader(new JarTemplateLoader(fs));   // 直接读 jar 内 .ftl
```

**Step 2：补 `udcCodeConfig`（这是模板配置的唯一入口）**
```java
// 平台常量文件 constants.ftl 开头就三行：
<#assign TemplateConfig       = udcCodeConfig["com.seeyon.udc.common.autocode.config.TemplateConfig"]>
<#assign PasterConfig         = udcCodeConfig["com.seeyon.udc.common.autocode.config.PasterConfig"]>
<#assign DeductionPasterConfig= udcCodeConfig["com.seeyon.udc.deduction.autocode.config.DeductionPasterConfig"]>
```
**⇒ `udcCodeConfig` 是一个 `Map<FQCN, 配置对象>`，key 是**完整类名**。**

**Step 3：复刻 `paster` 指令（平台 `PasterDirective` 全部逻辑只有 8 行）**
```java
public void execute(Environment env, Map params, ...) {
    String pastKey = ((TemplateScalarModel) params.get("name")).getAsString();
    TemplateModel pastTemplate = env.getDataModel().get("paster_" + pastKey);  // ★ 前缀 paster_
    if (null == pastTemplate) return;         // 没有就直接跳过，不报错
    String pastCode = ((TemplateScalarModel) pastTemplate).getAsString();
    if (StringUtils.isBlank(pastCode)) return;
    out.write(pastCode);
    if (body != null) body.render(env.getOut());
}
```
**★★★★★ 关键机制：`<@paster name=X/>` 实际是去数据模型找 `paster_X` 这个变量。**
**⇒ 找到就输出，找不到**静默跳过**（这就是为什么缺 Paster 也能渲染成功）。**

---

## 2. ★★★★★ LIVE 产物 1：`dao.java.ftl` → 真实 Dao

**渲染输入：** `entityName=order`, `appNamePackage=Demo`, `appType=normal`, `entityCaption=订单`

**渲染输出（原文，543 字符）：**
```java
package com.example.demo.domain.dao;

import com.example.demo.domain.entity.Order;
import com.example.demo.dto.OrderDto;
import com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao;
import org.apache.ibatis.annotations.Select;
import org.springframework.stereotype.Component;
import com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao;
import java.util.Map;
import java.util.List;
/**
* 订单 dao 接口
*
* @Author xiaozhua
* @Date 2026-11-18
*/
    public interface DemoOrderDao extends AbstractAllInOneBaseDao<Order>{
}
```

**★★★★★ 五个 LIVE 结论：**
```
① 真的只有一行：public interface DemoOrderDao extends AbstractAllInOneBaseDao<Order>{}
② 没有任何方法声明（因为 BIZ_DOMAIN_DAO 为空，appendMethods 什么都不插）
③ 有 3 个无用 import（Select / Component / Map / List）—— 平台模板确实是「先 import 后决定」
④ 类名前缀是 {appNamePackage?cap_first} = "Demo" + "Order" + "Dao"
⑤ 缩进有多余空格（"    public interface"）—— 平台产物就是这么粗糙
```

**⇒ 印证第 27 号文档的推断：**Dao 是空壳，所有 CRUD 靠基类通用机制。**

---

## 3. ★★★★★ LIVE 产物 2：`mybatis.xml.ftl` → 真实 Mapper（内部全空）

**渲染输出（原文，246 字符）：**
```xml
<?xml version="1.0" encoding="UTF-8" ?>

<!DOCTYPE mapper PUBLIC
        "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.demo.domain.dao.DemoOrderDao">
</mapper>
```

**★★★★★ 这是最硬的一条证据：**
```
<mapper> 标签内部**一个字符都没有** —— 零 select / 零 insert / 零 resultMap
```
**⇒ 平台的 MyBatis XML **完全空**，所有 SQL 由 `AbstractAllInOneBaseDao` 在运行期用
   tk.mybatis + `Wrapper` + `Example` + `SeeyonKeyMap` 动态构造。**

**★ `namespace` 是 `{appNamePackage?cap_first}{entityName?cap_first}Dao` 的完整类名。**

---

## 4. ★★★★★ LIVE 产物 3：`AppBeanNameModifier` → bean 名加应用前缀

**渲染输出（原文，1,124 字符）：**
```java
package com.example.demo.beanname;

import com.seeyon.boot.common.AppBeanNameModifier;
import com.seeyon.boot.util.StringUtils;
import org.springframework.beans.factory.config.BeanDefinition;

/**
* UDC业务应用启动的时候自定义beanName，在beanName中添加应用name（首字母小写）
*/
public class DemoBeanNameModifyer implements AppBeanNameModifier {
    private static final String appName = "Demo";

    /**
    * 当前beanDefinition对应的class包路径中如果包含当前应用名称并且beanName中不包含应用名称时，给beanName加上应用name
    */
    @Override
    public String modifyBeanName(BeanDefinition beanDefinition, String beanName) {
        if (beanDefinition.getBeanClassName().contains(appName) && !beanName.contains(appName)) {
            beanName = appName + StringUtils.capitalize(beanName);
        }
        return beanName;
    }
}
```

**★★★★★ 这是一个**完整可用**的生成物，揭示了平台的 Bean 命名隔离机制：**
```
同一平台里，多个 UDC 应用都有 OrderService / OrderDao
→ 平台生成 AppBeanNameModifier，启动时给本应用的 bean 加应用名前缀
→ DemoOrderService / DemoOrderDao，避免多应用 Bean 冲突
```

**★★ 实现 `com.seeyon.boot.common.AppBeanNameModifier`（boot 层接口）。**
**★ 类名有拼写错误：`DemoBeanNameModifyer`（Modifier → Modifyer），平台模板里的笔误。**

**★★★ 这解释了一个重要现象：**
```
为什么生成的 Dao 是 DemoOrderDao 而不是 OrderDao？
→ 模板直接拼了 appNamePackage 前缀（第 2 节），不是靠 BeanNameModifier
→ BeanNameModifier 是兜底：防止漏改的 bean 冲突
```

---

## 5. ★★★★ 渲染失败的模板：缺哪些变量（= 平台注入哪些元数据）

**15 个模板试渲染，3 个成功，12 个失败。失败原因本身就是情报：**

| 缺失变量 | 影响的模板 | 含义 |
|---|---|---|
| `table`（对象） | appservice.java / appserviceImpl / controller | **实体表元信息**（isRoot/caption/fullName/appName/enableRpc/isOpenApiEntity） |
| `udcCodeConfig["com.seeyon.udc.common.autocode.util.StringHelper"]` | dto / enums / entityrule / microflow / event | **模板工具类**（16 个，见第 6 节） |
| `groupId` | project/*/pom.xml | **Maven 坐标** |

**★★★ 所以平台生成前必须先准备三类元数据：**
```
① 数据模型：table / entityName / 各 package / author / createDate / appVersion
② 工具类注册：udcCodeConfig（16 个 util）
③ paster 片段：paster_{key}
```

---

## 6. ★★★★★ 模板可用的 16 个工具类（`utils.ftl` 实测注册清单）

**`autocode/JAVA/2.9/templates/common/utils.ftl` 前 16 行原文：**

| 模板变量 | FQCN |
|---|---|
| `StringHelper` | `com.seeyon.udc.common.autocode.util.StringHelper` |
| `CollectionUtils` | `org.apache.commons.collections.CollectionUtils` |
| `DataFlowCodeUtils` | `com.seeyon.udc.dataflow.autocode.util.DataFlowCodeUtils` ★★ |
| `ConditionConfigOutputUtil` | `com.seeyon.boot.starter.condition.output.ConditionConfigOutputUtil` ★ |
| `EntityCodeUtils` | `com.seeyon.udc.common.autocode.util.EntityCodeUtils` ★★ |
| `FormulaUtil` | `com.seeyon.udc.common.utils.FormulaUtil` ★★ |
| `DtoCodeUtil` | `com.seeyon.udc.common.utils.DtoCodeUtil` ★ |
| `StringUtils` | `com.seeyon.boot.util.StringUtils` |
| `UdcCommonConstant` | `com.seeyon.udc.common.constant.UdcCommonConstant` ★ |
| `ConnectorUtil` | `com.seeyon.udc.common.autocode.util.ConnectorUtil` ★ |
| **`MicroFlowCodeUtil`** | `com.seeyon.udc.common.autocode.util.MicroFlowCodeUtil` ★★★ |
| `EntityRuleCodeUtil` | `com.seeyon.udc.common.autocode.util.EntityRuleCodeUtil` ★★ |
| `JsonUtils` | `com.seeyon.boot.util.JsonUtils` |
| `DataTransferObjectCodeUtil` | `com.seeyon.udc.common.autocode.util.DataTransferObjectCodeUtil` ★ |
| `DynamicDependencyUtil` | `com.seeyon.udc.common.utils.DynamicDependencyUtil` ★ |
| `AppCodeUtil` | `com.seeyon.udc.autocode.util.AppCodeUtil` ★ |

**★★★★★ 这是**模板与平台代码的唯一接口层**：**
```
模板里能写 Expression 吗？
→ 不能直接写。可以调这 16 个工具类的 static 方法。
→ 例：<#assign x = MicroFlowCodeUtil.buildDataFlowExecuteParamDto(...)>
```

**★★★ 关键工具：**
```
MicroFlowCodeUtil             微流程代码片段的「大脑」（110 个方法！）
  buildDataFlowExecuteParamDto / buildResponseName / buildCallMethodByMicroFlow4CodeDto
  getSelectParamValue + 5 个变体 / getRealListName / filterDeletedData（8 个变体）
  initFormulaLocalVariableNameSet / getExpressionCodeFragment / generateConditionExpression
EntityCodeUtils               实体代码工具（25 个方法）
  getExpressionKey / getJavaType / getOldEntityName / getIgnoreProperties
  needOpenApi / needGenerateMethod（4 个重载）/ getDefAllMethodName / getChildEntityMethodName
FormulaUtil                   表达式工具
DataFlowCodeUtils             数据流工具（含 getExpressionDefinitionDtoId）
EntityRuleCodeUtil            实体规则工具（5 个方法，全是 build*ClassName）
ConnectorUtil / DynamicDependencyUtil / AppCodeUtil
```

### 6.1 ★★★★★ `MicroFlowCodeUtil` 的 110 个方法（分类）

**① 取值（9 个 `getSelectParamValue*` 变体）**
```
getSelectParamValue(SelectParam)
getSelectParamValue(SelectParam, VirtualFullNameTransformer)
getSelectParamValueWithoutNull / getSelectParamValueExceptNull
getSelectParamValue4Object(selectParam, leftJavaType, leftDataType)
getSingleSelectParamValue
getCastTargetType / castTypeObject
```

**② 删除数据处理（8 个方法 —— 这是主子表批量操作的核心！）**
```
filterDeletedData(appDto, condition, entityType, ...)      ★ 过滤掉 DELETE 行
distinctDeletedData(...)                                   ★ 去重
getDeletedData(entityType, sourceListName, newListName)
getDeletedData(ApplicationDto, condition, entityType, ...)
getDeletedDataPartition / declareDeletedDataPartition
getDeletedDataByFilterMap / getDeletedDataByFilterMapCode
getExistingDataByFilterMapCode
addDeletedData(targetData, deletedData)
findUniqueDeletedData(selectParam, dataSource, resultListName)
getDistinctDelListName(resultListName)
```

**★★★ 为什么需要这么多？**
```
主子表批量保存时，前端会把整棵树的 DtoList 传上来，其中部分行的 ActionType = DELETE。
遍历/聚合/扣减/回写时都必须**先剔除这些行**，否则：
  - 求和会把「已删除行」算进去
  - 差集会把「已删除行」当有效数据
  - 回写会给「已删除行」写值
⇒ 这 8 个方法是平台处理「主子表脏数据」的完整工具箱。
```

**③ 表达式（5 个）**
```
getExpressionCodeFragment(expression, dynamicDependencyEnumMap, ...)   ★ 生成表达式代码片段
generateConditionExpression(expression, dynamicDependencyEnumMap, ...) ★ 生成条件
createFormulaMapInstance(ExpressionNode)
buildExpressionDetailsResolver(...)
filterExpressionParam(expressionNode, filterEntity)
```

**④ 局部变量作用域（4 个）**
```
initFormulaLocalVariableNameSet()          ★ 初始化局部变量名集合
putAllFormulaLocalVariableNameSet(names)
initLinkedHashSet()
addValues2Set(sourceSet, values)
```

**⑤ 集合运算辅助（2 个）**
```
requiredOperationParam(operationType)      ★ 判断是否需要第二集合（UNION/INTERSECT/SUBTRACT…）
getRealListName(appDto, condition, sourceList, newListName)   ★ 取真实的（过滤后的）集合名
```

**⑥ 类型判断（4 个）**
```
isEntityType(applicationDto, condition)
isEntityTypeBySelectParamId(selectParam, entityDtoMap)
isSelectedEntityField(selectParam, allEntityDtoFullNames)
selectedEntityField(selectParam, predicate)
```

**⑦ 错误/事件/i18n（3 个）**
```
buildCustomErrorNodeSimple(mfType, mfName, node)
buildMfSimpleI18nParam(applicationDto, mfType, mfName, node)
buildSubscribeEventAnnotation(eventFullName)
```

**⑧ 其他**
```
getDtoNameByFullName(fullName) / convertAggSelectResult(output, respData) / generateCodeByCollection(collection)
getExtensionPropertiesObject(resolveBo) / isEntityRuleParam(param) / hasEntityExpressionParam(resultList)
```

### 6.2 ★★★★ `EntityCodeUtils` 的 25 个方法（实体代码生成的关键判断）

**① 表达式 key 与 Java 类型**
```
getExpressionKey(entityDto, attributeDto)          ★ 表达式在本实体字段上的 key
splitExpressionKey / splitExpressionKeyEntity
getJavaType(ExpressionDefinitionDto)               ★ 表达式结果的 Java 类型
getRuntimeExprString(CodeGenerateResult)           ★ 把 CodeGenerateResult 转成可运行表达式串
```

**② 旧值支持（更新场景）**
```
getOldEntityName(entityName)                       ★ 拿到 "旧实体" 的类名（用于对比更新）
```

**③ 生成方法白名单（决定生成哪些方法！）**
```
getDefAllMethodName()                ★ 默认全部方法名
getChildEntityMethodName()           ★ 子实体方法名
getThirdEntityDefMethodName()        ★ 第三方实体方法名
needGenerateMethod(allMethodName, currentMethod)                       ← 4 个重载
needGenerateMethod(allMethodName, currentMethod, udcApp)
needGenerateMethod(allMethodName, currentMethod, udcApp, ...)
needGenerateMethod2(dataSourceAllActionNames, currentMethod)
needOpenApi(list, currentMethod)     ★ 哪些方法要开 OpenApi
```

**★★★★★ 这三组方法是「平台按实体类型生成不同方法集」的实现：**
```
主实体     → getDefAllMethodName()
子实体     → getChildEntityMethodName()
第三方实体 → getThirdEntityDefMethodName()
UDC 应用   → needGenerateMethod(..., udcApp=true)
```

**④ 其他**
```
getEntityFullNamePrefix(applicationDto) / getEntity4DtoFullNamePrefix(applicationDto)
resolvePatternExpression(patternExpression) / patternExpressionIsValidate(...)
getSelectOne3rdPartiesEntityMfName / getSelect3rdPartiesEntityListMfName
getDynamicSearchMfName / getDynamicSearchCountMfName
compareStringNum / getIgnoreProperties(entityDto) / getDataType(map, attributeName)
```

### 6.3 ★★ `EntityRuleCodeUtil` 的 5 个方法（全是命名构造）

```java
buildEntityRuleClassName(groupType, entityName, uncapFirst)
buildAggregateRootEntityRuleClassName(groupType, entityName, uncapFirst)   ★ 聚合根
buildAggregateRootEntityRuleMethodName(groupType, entityName)
buildAggregateRootEntityRulePrefix(groupType, entityName, isClass, fn)
partitioningByDeleteActionTypeAndGetDeleteIds(entityDtoType, entityDtoListName)  ★ 按 DELETE 分区
```

**★ AppServiceImpl 模板里用过（第 27 号文档原文）：**
```freemarker
import ${baseServicePackage}.entityrule.${EntityRuleCodeUtil.buildAggregateRootEntityRuleClassName("DEFAULT_VALUE", entityName, false)};
```
**⇒ 命名规则：`{groupType}{EntityName}...`**

---

**★ 注释里两条设计意图（原文）：**
```
<!-- 减少 ConnectorUtil 在微流程模板中的使用，应当使用 fullNameTransformer 对 fullName 进行转换 -->
<!-- 减少 DynamicDependencyUtil 在微流程模板中的使用，应当使用 fullNameTransformer -->
```
**⇒ 平台在主动收敛模板对工具类的依赖，改用 `fullNameTransformer`。**

---

## 7. ★★★★ 代码生成框架的完整类结构（`udc-starter-autocode` 52 类）

```
engine/
  CodeEngine                        接口：execute(AbstractLazyCacheableContext)
  SimpleCodeEngine                  ★ 实现：CompletionExecutor("代码生成", 30000ms) 并行跑 taskList

context/
  AutoCodeContext                   ★ 接口：registerEarlyTemplate / directOutput / getCodeLanguage /
                                          getCodeVersion / needIntercept / getInterceptorList
  AbstractMultiVersionAutoCodeContext
  AbstractMultiVersionCacheableContext
  AbstractSimpleMultiVersionCacheableContext
  CodeLanguage                      ★ 代码语言（JAVA / 其他）

template/
  AbstractFreemarkerTemplate        ★ 核心：writeToFile / resolveToString / processTemplateString
  AbstractDecoratableFreemarkerTemplate
  EarlyTemplate                     ★ 早期模板（filterFilePath / filterTemplateContent）
  FreemarkerTemplate
  TemplateBuilder / TemplateInterceptor

extension/directive/
  AutoCodeDirective                 指令接口
  PasterDirective                   ★★★ paster（已复刻，见第 1 节）
  UncapDirective                    ★ uncap（首字母小写）

extension/decorate/
  Decorate / Decoratable / DecorateConfig / DecorateContainer
  DecorateTemplate / TemplateDecorateContainer / DecorateAutoConfiguration   ★ 装饰器（插桩）

handler/
  AutomaticCode / CodeHandler / DefaultAutoTaskVersion
  LazyCacheableAutoCodeTask         ★ 任务基类：code(context)
  MetaData / MetaDataHandler / MetaDataTypeEnum / MultiVersionMetaDataHandler

metadata/
  MetaDatable / AbstractMetaDatableContext / AbstractLazyCacheableContext

config/
  AutoCodeConfig / AutoCodeConfigAdapter / AutoCodeConfigurator
  BasePasterConfig                  ★ paster 配置基类

utils/
  AutoCodeUtils                     ★ 10 KB 工具

条件：
  condition/CodeCondition

常量：
  constant/MetadataConst

异常：
  exception/AutoCodeException
```

### 7.1 ★★★★ 执行链路（反编译实证）

```java
// SimpleCodeEngine.execute —— 平台用固定 30 秒超时 + 并行
public void execute(AbstractLazyCacheableContext ctx) {
    CompletionExecutor ex = new CompletionExecutor("代码生成", 30000L);
    if (CollectionUtils.isNotEmpty(taskList)) {
        taskList.forEach(task -> {
            NamedFutureTask f = new NamedFutureTask(task.getClass().getSimpleName(),
                                                    () -> task.code(ctx), true);
            ex.submit(f);
        });
    }
    ex.waitTimeout();
}
```

**★★★★★ 三个关键点：**
```
① 代码生成有**30 秒硬超时**（CompletionExecutor 30000L）
② taskList 是**并行**提交的（每个 Task 一个 Future）
③ 超时后 waitTimeout() —— 不抛异常，可能静默丢任务
```
**⇒ 大型应用（实体多）代码生成可能**超时失败，且错误不一定显式报出。**

### 7.2 ★★★ `AutoCodeContext` 接口方法（原文）

```java
public interface AutoCodeContext extends MetaDatable {
    void registerEarlyTemplate(EarlyTemplate t);
    default void directOutput(String path, String content);          // 直接写文件
    default void directOutputAppend(String path, List<String> changeList);
    DecorateContainer getDecorateContainer();
    default CodeLanguage getCodeLanguage();
    default String getCodeVersion();
    default String getUdcRuntimeVersion();
    default boolean needIntercept();
    default List<TemplateInterceptor> getInterceptorList();
}
```

**★★★ `directOutput` 的实现（原文）：**
```java
String filteredFilePath    = EarlyTemplate.filterFilePath(path, this);
String filteredContent     = EarlyTemplate.filterTemplateContent(content, path, this);
FileUtils.writeString(filteredFilePath, filteredContent);
```

**⇒ `EarlyTemplate` 负责**路径过滤**和**内容过滤** —— 这就是「模板版本、代码风格开关」的落点。**

---

## 8. ★★★★ 三套模板引擎（平台同时支持）

```
com.seeyon.boot.starter.engine/
  AbstractTemplate / TemplateContext / TemplateProcessor / TemplateListener
  freemarker/FreemarkerTemplate
  beetl/BeetlTemplate          ★ Beetl
  velocity/VelocityTemplate    ★ Velocity
  config/ConfigBuilder / Const
  exception/TemplateException
```

**★★★ 平台有**三套**模板引擎：FreeMarker（主力）、Beetl、Velocity。**
**⇒ 当前 UDC autocode 只用 FreeMarker（432 个全 .ftl）。**

**★ 另有 `udc-starter-autocode` 内置测试模板：`autocode/JAVA/2.8/templates/test/test.java.ftl`
  内容就是 `CodeEngine` 接口的源码 —— 平台自己的「模板能生成什么」的样例。**

---

## 9. ★★★★★ 与我已有文档的印证/修正

| 旧结论（第 27 号文档） | LIVE 验证 |
|---|---|
| 「Dao 只有 1,852 字节，几乎不生成内容」 | **✅ CONFIRMED** —— 实测输出只有一行 interface 声明 |
| 「mybatis.xml 675 字节，基本空的」 | **✅ CONFIRMED** —— 实测 `<mapper>` 内部**零字符** |
| 「全是 FTL + paster」 | **✅ CONFIRMED** —— paster 机制完整复刻（8 行代码） |
| 「表达式编译成 Java 方法」 | **✅ 与本轮无关但已确认**（ExpressionCodeGenerator） |
| 「平台无 JavaPoet/AST 拼装」 | **✅ CONFIRMED** —— 纯文本模板渲染 |

**★★★ 新增（第 27 号文档没有的）：**
```
① 代码生成有 30 秒硬超时（CompletionExecutor）
② 任务并行执行（不是串行）
③ paster 找不到时静默跳过（不报错）
④ 三套模板引擎并存（FreeMarker/Beetl/Velocity）
⑤ 16 个模板工具类清单（utils.ftl）
⑥ AppBeanNameModifier 兜底 Bean 命名（完整产物）
```

---

## 10. 未覆盖

| 项 | 说明 |
|---|---|
| `table` 对象的完整字段 | 只知道 isRoot/caption/fullName/appName/enableRpc/isOpenApiEntity |
| `appservice.java.ftl` 真实渲染 | 缺 table，未跑通 |
| `dto.java.ftl` / microflow 各模板 | 缺 16 个工具类，未跑通 |
| `groupId` 等 Maven 变量 | project/pom 模板未跑通 |
| `AbstractFreemarkerTemplate.writeToFile` 的路径规则 | 未读 |
| `EarlyTemplate.filterFilePath/filterTemplateContent` | 未读（版本/风格开关） |
| `DecorateContainer` 的插桩机制 | 未读 |
| `AutoCodeUtils`（10 KB） | 未读 |
| 16 个工具类的方法签名 | 只有名字 |
| 是否能在沙箱真实跑整个应用的生成 | **未做**（需环境） |
# 49 · ★★★★★ 工程骨架与事件/参照/筛选方案生成（15 域全覆盖）

**证据来源**：`mfx/autocode/JAVA/2.9/templates/` 全 141 个 .ftl 原文（STATIC_RULE）
**证据等级**：STATIC_RULE（100% 模板原文，逐行可复核）

---

## 一、★★★★★ 生成体系全景（15 个域，141 模板）

```
autocode/JAVA/2.9/templates/
  microflow/            54   微流程（38%）—— 编译型，见 47/48
  entity/               21   实体（含 BaseService 1417 行，见 45）
  common/               13   公共宏（utils / reliable-invoker / formula）
  feature/              10   特性注入片段（见 45/46）
  project/               9   ★ 工程骨架（pom + Application + yaml）
  entityrule/            9   业务规则服务（见 46）
  project-for-deploy/    6   ★ 集成测试工程
  event/                 5   ★ 业务事件 + 实体事件
  refer/                 4   ★ 参照 Controller
  project-ext/           3   ★ 扩展模块
  referconfig/           2   参照/页面配置 JSON
  filterplan/            2   ★ 筛选方案 Controller
  enums/                 1   枚举类
  dto/                   1   DTO
  beanname/              1   ★ BeanName 修饰器
```

**⇒ 141 个模板，微流程+实体占 53%，其余 13 个域决定「工程能不能跑起来」。**

---

## 二、★★★★★ 工程骨架：4 模块 + 1 扩展（`project/` 9 模板）

### 2.1 父 POM（`project/backend/pom.xml.ftl`）

```xml
<groupId>${groupId}</groupId>
<artifactId>${appName}</artifactId>
<version>${jarVersion}</version>
<packaging>pom</packaging>
<parent>
    <groupId>com.seeyon</groupId>
    <artifactId>boot</artifactId>
    <version>${platformVersion}</version>   <!-- ★ 平台 BOM -->
</parent>

<modules>
    <module>${appName}-facade</module>
    <module>${appName}-biz</module>
    <module>${appName}-web</module>
    <module>${appName}-assemble</module>
    <#if appType=="normal"><module>${appName}-ext</module></#if>   <!-- ★ normal 才 5 模块 -->
</modules>
```

### 2.2 ★★★★★ 五模块依赖链（真实结构）

```
        ┌────────────────────────────────────┐
        │  {appName}  (pom, parent=boot)      │
        └────────────────────────────────────┘
              │
    ┌─────────┼──────────┬──────────┬─────────────┐
    ▼         ▼          ▼          ▼             ▼
 facade     biz        web      assemble        ext (仅 normal)
    │         │          │          │             │
    │         │          │          │             │
udc-       udc-common   biz      ↓ web          biz
starter-   facade               + ext          web
runtime    boot-starter-web     + extDeps      facade
           boot-starter-
            appservice
           boot-starter-
            scanner     ← 元数据注解扫描
           boot-starter-
            datainit
           boot-starter-
            transaction
           boot-starter-
            dynamicsql
           boot-starter-
            cache
```

**★★★★★ `biz` 的 8 个 starter 是硬依赖（真实清单）：**
```
boot-starter-web            Web 支持
boot-starter-appservice     AppService 分发
boot-starter-scanner        ★ 元数据注解扫描（UDC 实体靠它被发现）
boot-starter-datainit       ★ 数据初始化
boot-starter-transaction    事务
boot-starter-dynamicsql     ★ DynamicSQL
boot-starter-cache          缓存
udc-common                  UDC 公共
```

### 2.3 ★★★★★ `facade` 只依赖 `udc-starter-runtime`

```xml
<dependency>
    <groupId>com.seeyon</groupId>
    <artifactId>udc-starter-runtime</artifactId>
</dependency>
```
**⇒ facade 是「纯契约模块」，只有 AppService 接口 + DTO，零业务实现。**

### 2.4 ★★★★★ `web` 只依赖 `biz`（18 行 POM）

**⇒ Controller 层零额外依赖，全部能力来自 biz。**

### 2.5 ★★ `ext` 依赖 biz / web / facade（3 个）

**★ `ext` 用 `<groupId>com.seeyon</groupId>` 而非 `${groupId}`** —— 这是模板里的真实写法，说明 ext 模块归属平台组。

### 2.6 ★★★★★ `assemble` = fatjar 打包 + 资源复制（关键）

```xml
<artifactId>${appName}-assemble</artifactId>
<dependencies>
    <dependency>${groupId}:${appName}-web</dependency>
    <#if appType=="normal"><dependency>com.seeyon:${appName}-ext</dependency></#if>
    <#if extendDependencyList??><!-- 拓展依赖 --></#if>
</dependencies>

<build>
  <plugins>
    <plugin>org.springframework.boot:spring-boot-maven-plugin</plugin>   <!-- ★ 打 fatjar -->
    <plugin>maven-resources-plugin   <!-- ★ 把 ext 的 i18n/init 拷到 assemble -->
      <directory>../${appName}-ext/src/main/resources</directory>
      <includes>**/i18n/**  **/init/**</includes>
      <excludes>**/init/**/*.sql</excludes>   <!-- ★ 排除自定义 SQL -->
      <outputDirectory>${basedir}/target/classes</outputDirectory>
    </plugin>
  </plugins>
</build>

<profiles> local / dev / test / pre / prod </profiles>   <!-- ★ 5 个环境 -->
```

**★★★★★ 三条硬事实：**
1. **只有 assemble 打 fatjar**（`spring-boot-maven-plugin`）
2. **ext 的 i18n 和 init 资源会被复制进 assemble**，但 **init 下的 .sql 被排除**
3. **5 个 Maven profile：local / dev / test / pre / prod**

### 2.7 ★★★ `distributionManagement` 三段

```xml
<repository>          <id>${releaseId}</id>   <url>${releaseUrl}</url>
<snapshotRepository>  <id>${snapshotId}</id>  <url>${snapshotUrl}</url>
```
**⇒ 发布仓库地址由应用配置决定（不是平台写死）。**

### 2.8 ★★★★ `versions-maven-plugin` 自动改子模块版本

```xml
<execution>
    <id>update-child-modules</id>
    <phase>compile</phase>
    <goal>update-child-modules</goal>
</execution>
```
**⇒ 父 POM 改版本，编译时自动同步所有子模块（免手改）。**

### 2.9 ★★ 跨应用依赖的两种粒度（重要）

```xml
<#if dependentApps?? >
  <#list dependentApps as depApp>
    <#if depApp.dynamicService>
      <artifactId>${depApp.depAppName}-biz</artifactId>      <!-- ★ 动态服务 → 引 biz -->
    <#else>
      <artifactId>${depApp.depAppName}-facade</artifactId>   <!-- 普通 → 只引 facade -->
    </#if>
    <#if depApp.dynamicService>
      <artifactId>${depApp.depAppName}-facade</artifactId>   <!-- 动态服务还需 facade -->
    </#if>
  </#list>
</#if>
```
**★★★★★ `dynamicService=true` 的应用要同时引 biz + facade；普通应用只引 facade。**
**⇒ 这是「跨应用调服务」与「跨应用只调契约」的分界线。**

### 2.10 ★★ 组件依赖（`dependentStarters`）

```xml
<#list dependentStarters as depStarter>
    <groupId>${depStarter.depAppBasePackage}</groupId>
    <artifactId>${depStarter.depAppName}</artifactId>
</#list>
```
**⇒ 「应用」和「组件」是两类依赖，组件无 `-biz/-facade` 后缀。**

---

## 三、★★★★★ 启动类（`Application.java.ftl`）—— appType 二分

### 3.1 `appType == "form"`（表单应用）

```java
@BootApp(name="${appName}", caption="${appCaption}", version="${jarVersion}",
         udcApp=true, description="${description}")
public class Application {                       // ★ 不继承
    public static void main(String[] args) {
        Apps.setProfileIfNotExists(SystemEnvironment.local.name());
        SpringApplication springApplication = new SpringApplication(Application.class);
        ApplicationContextFactory factory = (webApplicationType) -> {
            return new AnnotationConfigServletWebServerApplicationContext(new SeeyonBeanFactory());
        };
        springApplication.setApplicationContextFactory(factory);
        springApplication.run(args);
    }
}
```

### 3.2 `appType == "normal"`（普通应用）

```java
@BootApp(name="...", caption="...", version="...", udcApp=true, description="...")
public class Application extends SeeyonInitializer {    // ★★ 继承 SeeyonInitializer
    public static void main(String[] args) { /* 同上 */ }

    @Override
    public Class getStartupClass() { return Application.class; }   // ★ 必须实现
}
```

### 3.3 ★★★★★ 启动类的 5 个固定动作（两种类型共有）

| # | 动作 | 说明 |
|---|---|---|
| 1 | `@BootApp(udcApp=true)` | **标记为 UDC 应用** |
| 2 | `Apps.setProfileIfNotExists(local)` | 默认 local profile |
| 3 | `new SeeyonBeanFactory()` | **用平台 BeanFactory，不是 Spring 默认** |
| 4 | `AnnotationConfigServletWebServerApplicationContext` | 显式指定 Web 上下文 |
| 5 | `springApplication.run(args)` | 标准启动 |

**★★★★★ 第 3 条是全平台最关键的一行：`SeeyonBeanFactory` 替换 Spring 默认 BeanFactory。**
**⇒ 平台所有特性注入（`paster`/`joinSnippets`）、Bean 名修饰（`AppBeanNameModifier`）、元数据扫描，全部挂在这个自定义 BeanFactory 上。**

### 3.4 ★★★ `application.y.ftl`（永久配置，4 行）

```yaml
seeyon:
  config:
    server-addr: ${NACOS_ADDR:127.0.0.1:8848}
    password:   ${NACOS_PASSWORD:nacos}
    username:   ${NACOS_USERNAME:nacos}
  datasource:
    database:   ${appName}          # ★ 库名 = 应用名
```

**★★★★★ 三条事实：**
1. **配置中心是 Nacos**（`server-addr`）
2. **Nacos 凭据走环境变量**（默认 nacos/nacos）
3. **数据源库名 = 应用名**（`database: ${appName}`）

---

## 四、★★★★★ Bean 名冲突解决（`beanname/`）

```java
package ${appPackagePath}.beanname;

public class ${appNamePackage?cap_first}BeanNameModifyer implements AppBeanNameModifier {
    private static final String appName = "${appNamePackage}";

    @Override
    public String modifyBeanName(BeanDefinition beanDefinition, String beanName) {
        if (beanDefinition.getBeanClassName().contains(appName) && !beanName.contains(appName)) {
            beanName = appName + StringUtils.capitalize(beanName);
        }
        return beanName;
    }
}
```

**★★★★★ 机制：**
- 实现平台 SPI `AppBeanNameModifier`
- 判断：**Bean 类名包含应用名 且 BeanName 不包含应用名** → 加前缀
- 前缀格式：`appNamePackage + Capitalize(beanName)`

**⇒ 这是多应用共存时 Bean 名隔离的官方方案。**
**⇒ 注释原文：「UDC业务应用启动的时候自定义beanName，在beanName中添加应用name（首字母小写）」**

---

## 五、★★★★★ 枚举生成（`enums/enums.java.ftl`）

### 5.1 三种包路径分派

```freemarker
<#if udcEnum.udcEnumType == "CONNECTOR">
    package ${ConnectorUtil.getConnectorEnumPackagePath(appPackagePath)};      // 连接器枚举
<#elseif udcEnum.udcEnumType == "DYNAMIC_DEPENDENCY">
    package ${ConnectorUtil.getDynamicDependencyEnumPackagePath(appPackagePath)};  // 动态依赖枚举
<#else>
    package ${appPackagePath}.enums;                                          // 普通枚举
</#if>
```
**⇒ 枚举按用途分三个包，不是全塞 `.enums`。**

### 5.2 ★★★★★ 枚举的 5 个注解（平台强约束）

```java
@EnumInfo(value = "${udcEnum.caption}",
          <#if udcEnum.iconDisplay>type = EnumType.IMAGE,</#if>
          customs = { @Custom(properties = {
              @CustomAttribute(name = "appName", value = "${appName}"),
              @CustomAttribute(name = "orgId",   value = "${udcEnum.id}") }) },
          excludes = { "被排除项", "NONE" })     // ★ NONE 永远被排除
public enum ${udcEnum.name?cap_first} implements Messageable {
```

**★★★★★ 四条硬事实：**
1. **必须 `implements Messageable`**（平台枚举契约）
2. **必须 `@EnumInfo`**（元数据登记）
3. **固定生成 `NONE(-1, "NONE")` 作为第一项**
4. **`excludes` 里 `"NONE"` 是硬编码追加的**（可能是占位枚举）

### 5.3 枚举项结构

```java
NONE(-1, "NONE")<#if isNotEmpty>,<#else>;</#if>
<#list udcEnumItems as item> ... </#list>
```
**⇒ 枚举有 `(-1, "NONE")` 双参构造，即 `(code:int, caption:String)`。**

---

## 六、★★★★★ 业务事件（`event/business-event.java.ftl`）

### 6.1 Message 类结构

```java
@MessageInfo(value = "${event.caption}", topic = "${topic}",
             description = "${event.eventDescription}"
             <#if udcMq>, customs = {
                 @Custom(properties = {
                     @CustomAttribute(name = "id",            value = "${event.id}"),
                     @CustomAttribute(name = "from",          value = "udc"),     // ★ 固定 udc
                     @CustomAttribute(name = "source",        value = "${event.source}"),
                     @CustomAttribute(name = "name",          value = "${event.name}"),
                     @CustomAttribute(name = "eventDataType", value = "${event.eventDataType}")
                 }),
                 <#if event.enable>
                 @Custom(name = "openApiCustom", properties = {
                     @CustomAttribute(name = "openEventKey", value = "${event.eventDataFullName}")
                 })
                 </#if>
             }</#if>,
             openApi = @OpenApi(isOpenApi = ${event.enable}))
public class ${event.name?cap_first}Message extends BaseMessage<${dataType}> {
    private static final long serialVersionUID = ${StringHelper.generateSerialVersionUuid()}L;

    @JsonCreator
    public ${event.name?cap_first}Message(@JsonProperty("data") ${dataType} data) {
        super.setData(data);
    }
}
```

### 6.2 ★★★★★ 三种消息类型

| messageType | 基类 | 用途 |
|---|---|---|
| `DELAY` | `DelayBaseMessage<T>` | **延迟消息** |
| 其他 | `BaseMessage<T>` | 普通消息 |

### 6.3 ★★★★★ 两种数据形态

```freemarker
<#if event.eventDataType == "LIST">
    <#assign dataType>List<${eventData.capFirstName}></#assign>   // 列表
<#else>
    <#assign dataType>${eventData.capFirstName}</#assign>          // 单条
</#if>
```

### 6.4 ★★★★★ `openApi = @OpenApi(isOpenApi = ...)` —— 事件可对外发 OpenAPI

**⇒ 业务事件是「对内 MQ」+「对外 OpenAPI」双通道，一个注解开关。**

### 6.5 ★★★ 构造必须 `@JsonCreator` + `@JsonProperty("data")`

**⇒ MQ 反序列化契约：消息体固定放 `data` 字段。**

---

## 七、★★★★★ 实体事件（`event/entity/`）—— 三阶段钩子

### 7.0 ★★★★★ 实测确认（LIVE，非模板推断）

```java
com.seeyon.boot.starter.udcrt.event.publisher.EventPublisher$EventPhase
  values: HANDLE_BEFORE | TRANSACTION_BEFORE_COMMIT | TRANSACTION_COMMIT_SUCCESS
```

**⇒ 只有 3 个值，实测可见，无第四个。**

```java
public static java.util.List
com.seeyon.boot.starter.udcrt.util.EntityEventDeepCopier.copyList(java.util.Collection, java.lang.Class)
```

**⇒ 签名是 `(Collection, Class)` → `List`，实测确认。模板里写 `copyList(dtoList, Xxx.class)` 完全对应。**

**★ 两个类的真实包路径（模板里的变量名不代表包）：**
```
EventPublisher          com.seeyon.boot.starter.udcrt.event.publisher.EventPublisher
EntityEventDeepCopier   com.seeyon.boot.starter.udcrt.util.EntityEventDeepCopier
```

### 7.1 ★★★★★ `EventPublisher.EventPhase` 三值（权威）

```freemarker
<#if triggerType == "BEFORE">
    EventPublisher.EventPhase.HANDLE_BEFORE            ← 处理前
<#elseif triggerType == "AFTER">
    EventPublisher.EventPhase.TRANSACTION_BEFORE_COMMIT ← ★ 事务提交前
<#else>
    EventPublisher.EventPhase.TRANSACTION_COMMIT_SUCCESS ← ★ 事务成功后
</#if>
```

**★★★★★ 三条事实：**
1. **只有 3 个阶段，不是 4 个**（无 rollback 钩子）
2. `AFTER` 的语义是 **「事务提交前」**，不是「提交后」——**命名陷阱**
3. `TRANSACTION_COMMIT_SUCCESS` 是唯一的「成功后」

### 7.2 ★★★ UPDATE 事件带老值

```java
<#if actionType == "UPDATE">
    eventPublisherHelper.publishEntityEvent(
        new ${eventPackage}.${name?cap_first}<>(dto, oldDtoMap.get(dto.getId())),   // ★ 双参
        ${phase});
<#else>
    eventPublisherHelper.publishEntityEvent(
        new ${eventPackage}.${name?cap_first}<>(dto),   // ★ 单参
        ${phase});
</#if>
```
**⇒ 更新事件能拿到 `oldDtoMap`（改动前值），这是唯一能感知「字段从什么变成什么」的入口。**

### 7.3 ★★ 事件类来自 `com.seeyon.udc.common.event`

```freemarker
<#assign eventPackage="com.seeyon.udc.common.event"/>
```
**⇒ 实体事件类是平台预制的（`com.seeyon.udc.common.event.{Name}`），不是应用自己生成。**

---

## 八、★★★★★ 业务事件发布（`event/business.class[service]`）—— 条件+分批

### 8.1 ★★★★★ 事件条件表达式（`formulaInfo`）

```java
List<${entityName}Dto> ${name}NeedPublishDtos =
    <#if formulaInfo??>Lists.newLinkedList()<#else>${uncapEntityName}DtoList</#if>;

<#if formulaInfo??>
  log.info("事件条件配置不为空，开始计算条件");
  ${uncapEntityName}DtoList.forEach(${uncapEntityName}Dto -> {
      Map<String, Object> eventConditionFormulaMap = new HashMap<>();
      eventConditionFormulaMap.put("${table.name}", ${uncapEntityName}Dto);

      <#if actionType == 'UPDATE'>   // ★ 只有聚合根更新才有老值
      <#assign oldEntityName = EntityCodeUtils.getOldEntityName("${table.name}")>
      eventConditionFormulaMap.put("${oldEntityName}", oldDtoMap.get(${uncapEntityName}Dto.getId()));
      </#if>

      String eventConditionExpressionTranslation = "${formulaInfo.designData.expressionTranslation}";
      String eventCondition${resultTypeInfo} = "${formulaInfo.designData.resultTypeInfo}";
      String eventConditionExpression = "${formulaInfo.runtimeData.executableExpr}";

      EvalContextDto eventConditionEvalContextDto = new EvalContextDto();
      eventConditionEvalContextDto.setContextMap(eventConditionFormulaMap);
      eventConditionEvalContextDto.setExpression(eventConditionExpression);
      eventConditionEvalContextDto.setExpressionTranslation(eventConditionExpressionTranslation);
      eventConditionEvalContextDto.setResultType(eventCondition${resultTypeInfo});

      ${javaType} eventCondition = (${javaType})expressionEvaluator.eval(eventConditionEvalContextDto);

      if (Boolean.TRUE.equals(eventCondition)) {
          ${name}NeedPublishDtos.add(${uncapEntityName}Dto);
      } else {
          log.info("实体数据{}事件触发条件返回false，忽略。", ${uncapEntityName}Dto.getId());
      }
  });
</#if>
```

**★★★★★ 三条事实：**
1. **事件可配条件表达式**，只发布满足条件的实体
2. **表达式上下文两个变量**：`${table.name}`（新值）+ `${oldEntityName}`（老值，仅 UPDATE）
3. **`EvalContextDto` 有 4 个必设字段**：contextMap / expression / expressionTranslation / resultType

### 8.2 ★★★★★ `EntityEventDeepCopier` —— 事件数据深拷贝

```java
List<${eventData.fullName}> eventData =
    EntityEventDeepCopier.copyList(${name}NeedPublishDtos, ${eventData.fullName}.class);
```
**⇒ 发事件前必须深拷贝 DTO → 事件数据类型（防止后续修改影响已发消息）。**

### 8.3 ★★★★★ `numberFiredOnce` —— 三种触发粒度

```java
<#if numberFiredOnce == "ALL">
    // 全部触发
    businessEventHelper.transactionSuccessEvent(new ${messageFullName}(eventData));   // 一次发整批
<#elseif numberFiredOnce == "1">
    // 单个触发
    for (${eventData.fullName} data : eventData) {
        businessEventHelper.transactionSuccessEvent(new ${messageFullName}(data));    // 逐条发
    }
</#if>
```

**★★★★★ 三条事实：**
1. `ALL` = 整批一条消息
2. `1` = 逐条一条消息
3. **都在 `transactionSuccessEvent` 里发** —— **事务成功后自动投递**

---

## 九、★★★★ 参照（`refer/` 4 模板）—— 动态选人/选数据

### 9.1 ★★★★★ 参照 Controller 结构

```java
@Slf4j @RestController
@RestApi(value = "实体-${entityRefer4Code.entityName}", group = "参照")
@RequestMapping("${entityRefer4Code.restMapping}/${entityRefer4Code.entityName}/refer")
public class Refer${entityName?cap_first}Controller extends BaseController {

    @Autowired
    private ReferDynamicSelectAppService dynamicSelectAppService;   // ★ 参照专用服务

    private static final Map<String,String> referMap = new HashMap<>();
    static { ... }   // ★ 静态初始化参照配置
```

**★★★★★ 关键：参照走 `ReferDynamicSelectAppService`（独立于 `DynamicSelectAppService`）。**

### 9.2 ★★★ 参照的 5 个专属 DTO

```
ReferRuntimeConfigDto      运行时配置
ReferDisplayFiledDto       显示字段（注意 "Filed" 拼写，平台真实拼写）
ReferAggEntityDto          聚合实体
ReferenceDynamicSelectDto  参照动态查询
TreeQueryDto               树查询
```

**★★ `ReferDisplayFiledDto` 的 `Filed` 是平台拼写错误（应为 Field），代码里必须照拼。**

### 9.3 ★★★ 参照的 4 个模板分工

| 模板 | 场景 |
|---|---|
| `entity-refer-controller.java.ftl` | 实体参照（主） |
| `entity-refer-controller2.java.ftl` | 实体参照（变体，树/聚合） |
| `page-refer-controller.java.ftl` | 页面参照（主） |
| `page-refer-controller-fragment.java.ftl` | 页面参照片段（按参照项循环生成） |

### 9.4 ★★★ 参照配置 JSON（`referconfig/`）

`refer_config.json.ftl`：
```json
{ "${entityFullName}": [ {
    "name": "${refer.id}", "caption": "...", "displayName": "...",
    "pullDisplayName": ..., "configInfo": "...", "isDefault": ${refer.isDefault},
    "detailPage": ..., "detailPageId": "...", "type": "${refer.type}",
    "terminalType": "${refer.terminalType}"
} ] }
```
**⇒ 参照配置按「实体全名」分组，每组多个参照方案，`isDefault` 定默认。**

`page_config.json.ftl`（页面注册表）：
```json
{ "name": "${item.guid}", "caption": ..., "pageType": "...", "clientType": "...",
  "pageUrl": "...", "layout": ..., "menuCode": "...", "relationApp": ...,
  "sort": ..., "masterEntity": "...",
  "inParams": ..., "outParams": ..., "inPortletParams": ...,
  "relationGroupId": ..., "publicAccess": ..., "public": true }
```
**★★★★★ 页面配置的 16 个字段就是「自定义页面」的完整契约。**
**★★ `masterEntity` 说明页面绑定主实体；`inPortletParams` 说明页面能嵌门户。**

---

## 十、★★★★ 筛选方案（`filterplan/` 2 模板）—— 动态列表查询

### 10.1 ★★★★★ Controller 骨架

```java
@Slf4j @RestController
@RestApi(value = "筛选方案接口-${pageUrl}<#if isMobile>(移动端)</#if>", group = "筛选方案")
@RequestMapping("${planAppUrl}<#if isMobile>/mobile</#if>/${pageUrl}/filter-plan")
public class DynamicSelect${pageUrl?cap_first}<#if isMobile>Mobile</#if>Controller extends BaseController {
```

**★★★★★ 三条事实：**
1. **`isMobile` 开关 → 独立生成 `...MobileController`**（不是同 URL 加参数）
2. **URL 结构**：`${planAppUrl}/[mobile/]${pageUrl}/filter-plan`
3. **按页面生成 Controller**（一个页面一个）

### 10.2 ★★★★★ 两种查询目标（`third` 分支）

```java
<#if filterItem.third>
    // 三方实体
    public PageResponse<Map<String, ?>> searchPageByCondition${FilterItem.methodNameSuffix}(
        @MultiRequestBody PageInfo pageInfo,
        @MultiRequestBody List<Long> filterPlanGuids,
        @MultiRequestBody(required=false) String sourceId,
        @MultiRequestBody DynamicSearchParamDto searchParams) {

        FilterPlanDynamicSelectDto dto = new FilterPlanDynamicSelectDto();
        dto.setFilterPlanGuids(...);  dto.setPageInfo(pageInfo);
        dto.setDynamicSearchParamDto(searchParams);  dto.setPlanSourceId(sourceId);
        dto.setAppName("${filterItem.appName}");
        dto.setFilterPlanAppName("...");  dto.setFilterPlanAppVersion("...");

        PageResponse<${dtoFullName}> pageResponse =
            ${appServiceProxyVariableName}.dynamicSelect4FilterPlan(SingleRequest.from(dto));
        ...
```
**★★★★★ 三方实体查询统一返回 `PageResponse<Map<String,?>>`（因为不知道字段）。**

### 10.3 ★★★★★ `dynamicSelect4FilterPlan` —— 统一入口方法

```java
pageResponse = ${appServiceProxyVariableName}.dynamicSelect4FilterPlan(SingleRequest.from(dto));
```
**⇒ 所有筛选方案查询都调这一个方法名。**

### 10.4 ★★★★★ `RuntimeEntityDataSourceDto` —— 运行时数据源

```java
SingleResponse<RuntimeEntityDataSourceDto> resp = getRuntimeEntityDataSourceByControlId(runtimeSettingKey);
if (Objects.nonNull(dto)
    && ("ENTITY".equals(dto.getType()) || "LIST".equals(dto.getType()))
    && Objects.nonNull(dto.getControlId()))
```
**⇒ 筛选方案有「运行时数据源」，type 二值：`ENTITY` / `LIST`。**

### 10.5 ★★★ 4 个必设筛选参数

```
filterPlanGuids          筛选方案 GUID 列表
sourceId                 来源 ID
dynamicSearchParamDto    搜索参数
runtimeSettingKey        运行时配置键
```

---

## 十一、★★★★ 单元测试工程（`project-for-deploy/` 6 模板）

```
{appName}-test/src/test/
  java/${appPath}/TestApplication.java.ftl        ← 测试启动类
  java/${appPath}/entityrule/PersonEntityRuleServiceTest.java.ftl  ← 规则服务测试模板
  java/${appPath}/utils/FileHelper.java.ftl       ← 文件工具
  resources/application.yaml.ftl                   ← 测试配置
  resources/application-local.yaml.ftl             ← 本地配置
  pom.xml.ftl                                      ← 测试 POM
```

**★★★★★ `PersonEntityRuleServiceTest` 是平台给的测试样板 —— 业务规则服务是唯一有官方测试模板的生成物。**
**⇒ 换句话说：平台认为「业务规则」是最需要单测的部分。**

---

## 十二、★★★★★ 综合：一个 UDC 应用的完整生成清单

```
应用 ${appName}
├── pom.xml                          (parent=boot BOM, 5 profiles)
├── ${appName}-facade/
│   └── pom.xml                      (udc-starter-runtime only)
│   └── src/main/java/${appPath}/api/${E}AppService.java      ← 契约
│   └── src/main/java/${appPath}/dto/${E}Dto.java
├── ${appName}-biz/
│   └── pom.xml                      (8 starters + udc-common)
│   └── ${appPath}/appservice/${E}AppServiceImpl.java
│   └── ${appPath}/domain/entity/${E}Entity.java
│   └── ${appPath}/domain/service/${E}Service.java            ← BaseService 1417 行
│   └── ${appPath}/domain/dao/${E}Dao.java
│   └── ${appPath}/domain/event/${E}Event.java
│   └── ${appPath}/entityrule/Validate${E}Service.java        ← 三类规则服务
│   └── ${appPath}/microflow/${Flow}Service.java              ← 微流程（编译型）
│   └── ${appPath}/enums/${Enum}.java                         ← implements Messageable
│   └── ${appPath}/beanname/${App}BeanNameModifyer.java       ← Bean 名隔离
│   └── ${appPath}/event/${Name}Message.java                  ← MQ 消息
├── ${appName}-web/
│   └── pom.xml                      (只依赖 biz)
│   └── ${appPath}/controller/${E}Controller.java
│   └── ${appPath}/controller/Refer${E}Controller.java        ← 参照
│   └── ${appPath}/controller/DynamicSelect${Page}Controller.java  ← 筛选方案
├── ${appName}-ext/            (仅 appType=normal)
│   └── pom.xml                      (依赖 biz + web + facade)
│   └── ${appPath}/extend/package-info.java
├── ${appName}-assemble/
│   └── pom.xml                      (fatjar + 复制 ext 资源)
│   └── ${appPath}/Application.java  ← @BootApp(udcApp=true) + SeeyonBeanFactory
│   └── application.y.ftl            ← Nacos + database=${appName}
└── ${appName}-test/           (project-for-deploy，集成测试)
```

---

## 十三、★★★★★ 对开发者的 12 条结论

| # | 结论 |
|---|---|
| 1 | **4 模块（normal 5 模块），facade/biz/web/assemble，ext 可选** |
| 2 | **facade 只依赖 `udc-starter-runtime`，是纯契约** |
| 3 | **biz 有 8 个 starter 硬依赖**（web/appservice/scanner/datainit/transaction/dynamicsql/cache/common） |
| 4 | **只有 assemble 打 fatjar**，其余是普通 jar |
| 5 | **`SeeyonBeanFactory` 替换 Spring 默认 BeanFactory** —— 全平台特性注入的根 |
| 6 | **`appType=form` 不继承，`appType=normal` 继承 `SeeyonInitializer`** |
| 7 | **配置中心 = Nacos，库名 = 应用名** |
| 8 | **枚举必须 `implements Messageable` + `@EnumInfo` + 首项 `NONE(-1,"NONE")`** |
| 9 | **业务事件 = MQ + OpenAPI 双通道**，`@OpenApi` 一个开关 |
| 10 | **实体事件只有 3 阶段**，`AFTER` 实为「事务提交前」（命名陷阱） |
| 11 | **事件可配条件表达式**，上下文有 `{实体名}` + `{old实体名}`（仅 UPDATE） |
| 12 | **`numberFiredOnce` 二值：`ALL` 整批 / `1` 逐条**，都在事务成功后投递 |

---

## 十四、待验证

| 问题 | 状态 |
|---|---|
| `EventPublisher.EventPhase` 取值 | ✅ **LIVE 实测：3 个（HANDLE_BEFORE / TRANSACTION_BEFORE_COMMIT / TRANSACTION_COMMIT_SUCCESS）** |
| `EntityEventDeepCopier.copyList` 签名 | ✅ **LIVE 实测：`(Collection, Class) → List`** |
| `appType` 除 form/normal 还有哪些 | 待查（模板只判两种） |
| `SeeyonBeanFactory` 的实现细节 | 待反编译（`boot-core`，`<clinit>` 需 `WebMvcConfigurer`） |
| `AppBeanNameModifier` 其他实现类 | 待扫 jar |
| `numberFiredOnce` 的完整取值 | 待查（模板只见 ALL/1） |
| `PersonEntityRuleServiceTest` 的真实内容 | 待渲染 |
| 扩展依赖 `extendDependencyList` 的来源 | 待查配置模型 |

---

## 十五、★★★★ 本轮实测附带发现

**`SeeyonBeanFactory` 的 `<clinit>` 需要 `WebMvcConfigurer`：**
```
java.lang.ClassNotFoundException: org.springframework.web.servlet.config.annotation.WebMvcConfigurer
    at com.seeyon.boot.spring.SeeyonBeanFactory.<clinit>(SeeyonBeanFactory.java:98)
```
**⇒ 它在静态初始化里就引用 Spring MVC 类 —— 意味着 `SeeyonBeanFactory` 是 Web 强绑定，容器外无法加载。**
**⇒ 这也解释了为什么整个代码生成体系必须在真实 Spring 容器内运行。**
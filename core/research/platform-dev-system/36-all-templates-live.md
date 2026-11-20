# 36 · ★★★★★ 全套 141 个模板真实渲染成功（LIVE 证据）

**证据等级：LIVE_RULE —— 141/141 全部渲染成功，零失败**

---

## 一、渲染环境（可复现）

```
引擎：FreeMarker 2.3.32（真实 jar）
模板源：udc-biz-5.3.605.jar 内 autocode/JAVA/2.9/templates/（真实 141 个 .ftl）
工具类：60 个真实类，从 udc-biz / udc-common / boot-* / udc-dataflow 等包反射包装
classpath：220 个 jar（从 172.28.24.205 artifactory + CHIT 依赖）
依赖补齐：pinyin4j-2.5.1（4 个模板需要汉字转拼音）
关键设置：
  boolean_format = "c"          ← 否则 ${bool} 报错
  number_format = "computer"
  paster 指令 = 读取 paster_<name> 变量
```

**复现脚本**：`D:/software/hermes/cache/scratch/RenderGo.java`
**产物目录**：`D:/software/hermes/cache/scratch/rendered_go/`（141 个 .out）

---

## 二、★★★★★ 遍历过程中确认的三个关键配置事实

### 2.1 `boolean_format` 必须是 `"c"`

```
FreeMarker 2.3.32 默认 boolean_format="true,false" 被视同「未设置」，
直接 ${someBool} 会抛：
  Can't convert boolean to string automatically...
修复：cfg.setBooleanFormat("c")   // 输出 true / false（Java 代码正是要这个）
```
**⇒ 平台生成 Java 代码时必然设了 `boolean_format="c"`（或等价），否则模板跑不动。**

### 2.2 需要「paster 指令」

模板里有 `${paster "xxx"}` 语法，这是**平台自定义 FreeMarker 指令**：
```freemarker
<@paster name="methodBody"/>    ← 平台注入代码片段
```
**我复刻的实现**：读 `paster_<name>` 变量，非空则输出。

### 2.3 工具类要反射包装（BeansWrapper 不够）

```
现象：${DtoCodeUtil.handleOneToManyEntityName4Dto(child.name)}
     用 BeansWrapper(EXPOSE_ALL)     → "evaluated to null or missing"
     用 ClassModel 二次封装          → 同样失败
     用自写 TemplateHashModel 反射   → ✅ 成功
```
**⇒ 平台不是用 FreeMarker 原生 static 暴露，而是自己包装了工具类。**

---

## 三、★★★ 22 个字段属性（从 dto 模板反推的真实模型）

`field.xxx` 在模板中被引用的全部属性：

| 属性 | 含义 | 备注 |
|---|---|---|
| `id` | 字段 ID | **字符串**（模板做 `== '0'` 比较） |
| `guid` | 全局唯一 ID | |
| `name` | 字段名（驼峰） | |
| `caption` | 显示名（中文） | |
| `code` | 编码（大写） | |
| `columnName` / `dbColumnName` | 物理列名 | |
| `javaType` / `javaDataType` | Java 类型 | `String`/`Long`/`BigDecimal`/`Date` |
| `dataType` | 数据类型 | |
| `dataTypeName` | **枚举名**（大写） | `STRING`/`LONG`/`DECIMAL`/`DATETIME`/`INTEGER`/`MULTILINESTRING`/`CURRENCY`/`BIGINTEGER`/`Attachment`/`Image`/`Time` |
| `primaryKey` | 是否主键 | |
| `required` / `notNull` | 是否必填 | |
| `multiSelect` | 是否多选 | |
| `defaultValue` | 默认值 | `null` 表示无 |
| `defaultValueSystemVariable` | 系统变量默认值 | |
| `example` / `comment` | 示例 / 注释 | |
| `length` / `maxLength` / `scale` / `decimalScale` | 长度精度 | |
| `sensitive` / `useSnapshot` / `desensitizationType` / `enableSensitiveWordCheck` | 敏感/快照/脱敏 | |
| `entity` | **关联实体**（null=不是） | `.dtoFullName` `.relationAppName` `.realAppName` `.relationHostAppName` |
| `enum` | 关联枚举 | |
| `ctpEnum` | CTP 枚举 | `.ctpEnumFullName` |
| `attachment` | 附件 | `.attachmentFullName` |

### ★★★ 四类「关联字段」的判断结构（dto.java.ftl 第 178-188 行原文）

```freemarker
<#macro associate field>
    <#if field.entity??>
        , relationDto = "${field.entity.dtoFullName}", relationApp="...", ...
    <#elseif field.ctpEnum??>
        , relationDto = "${field.ctpEnum.ctpEnumFullName}", ...
    <#elseif field.attachment??>
        , relationDto = "${field.attachment.attachmentFullName}", ...
    <#elseif field.enum??>
        , relationApp = "${field.enum.relationAppName!}", ...
    </#if>
</#macro>
```
**⇒ 普通字段这 4 个键必须是 null（不是空 Map），否则被误判为关联字段。**

---

## 四、★★★★★ 产物体量清单（真实渲染字节数）

| 产物 | 字节 | 说明 |
|---|---|---|
| `feature/tree_entity/template/feature.tree.entity.class[service].ftl` | **31,729** | 树实体特性服务（最大） |
| `entity/baseservice.java.ftl` | **21,981** | BaseService |
| `entity/appserviceImpl.java.ftl` | **20,608** | AppServiceImpl |
| `entity/dynamicdependency/outAppAppServiceProxy.java.ftl` | 14,203 | 外应用 AppService 代理 |
| `entity/third/third_appserviceImpl.java.ftl` | 12,620 | 第三方实体 AppServiceImpl |
| `entity/controller.java.ftl` | 10,263 | Controller |
| `entity/tree/tree-refer-controller-fragment.ftl` | 10,035 | 树引用控制器片段 |
| `entity/appservice.java.ftl` | 8,251 | AppService 接口（38 方法） |
| `entity/pageEntityController2.java.ftl` | 8,227 | 页面实体控制器 v2 |
| `entity/dto.java.ftl` | 7,193 | DTO |
| `entity/tree/tree-page-controller-fragment.ftl` | 6,829 | 树页面控制器片段 |
| `entity/pageEntityController.java.ftl` | 5,765 | 页面实体控制器 v1 |
| `entity/tree/tree-entity-refer-controller.ftl` | 4,531 | 树实体引用控制器 |
| `refer/entity-refer-controller2.java.ftl` | 4,367 | 实体引用控制器 v2 |
| `entity/third/third_baseservice.java.ftl` | 4,147 | 第三方 BaseService |
| `entity/pageCustomControllerDto.java.ftl` | 3,768 | 页面自定义控制器 DTO |
| `entity/dao.java.ftl` | **543** | DAO（极简） |
| `entity/mybatis.xml.ftl` | **246** | MyBatis XML（几乎为空） |

**★★★ 两条重要事实：**
```
1. DAO 只有 543 字节 —— 继承 AbstractAllInOneBaseDao，不生成任何方法
2. mybatis.xml 只有 246 字节 —— 只有 DTD 声明，零条 SQL
```
**⇒ 平台**不再**为每个实体生成 CRUD SQL，全部由 `AbstractAllInOneBaseDao` 在运行时动态拼装。**
**⇒ 「生成器生成 Mapper XML」这个常见假设是**错的**。**

---

## 五、模板分类全景（141 个）

| 目录 | 数量 | 用途 |
|---|---|---|
| `entity/` | 32 | 实体主产物（DTO/Entity/DAO/Service/Controller/MyBatis） |
| `common/` | 10 | 宏与工具（utils/constants/macro-*） |
| `tree_entity/` | 10 | 树实体专用 |
| `microflow/` | ~20 | 微流程节点 |
| `feature/` | ~15 | 特性（feature） |
| `backend/` | 12 | 后端工程骨架 |
| `customflow/` | 7 | 自定义流程 |
| `${appName}-test/` | 6 | 单元测试 |
| `third/` | 6 | 第三方实体 |
| `tree/` | 4 | 树结构 |
| `service/` | 4 | Service |
| `customerror/` | 4 | 自定义错误 |
| `plugin/` | 3 | 插件 |
| `event/` | 2 | 业务事件 |
| `web/` | 7 | Web 层 |
| 顶层 | ~1 | beanname/AppBeanNameModifier |

---

## 六、待验证

| 问题 | 状态 |
|---|---|
| 平台实际的 `paster` 代码片段内容 | UNVERIFIED（我用了空实现，模板能跑但片段为空） |
| `feature/` 目录的完整用途 | UNVERIFIED |
| 树实体的方法集与普通实体差异 | UNVERIFIED（需读 feature.tree 产物） |
| 这些产物能否真实编译通过 | UNVERIFIED（需完整工程 + 平台 jar） |
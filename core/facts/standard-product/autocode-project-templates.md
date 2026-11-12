# autocode 工程模板：平台生成什么、放哪个包

> 证据级：**VERIFIED_STATIC_BYTECODE**（平台 jar 内 FreeMarker 模板逐字提取）
> 来源：`docs/audit/artifacts/decompiled/cfr-r30/biz/autocode/JAVA/2.9/templates/`
> 版本：2.7 / 2.8 / 2.9 / 3.0 四套并存，结构一致；本格以 2.9 为准

## 1. Capability

回答三个问题：

1. **客开工程是几个模块？** —— 一个。
2. **自定义微流程的代码是谁写的？** —— 平台生成的，人只填方法体。
3. **代码往哪个包放？** —— 模板里写死了，见 §4。

## 2. 两套工程模板，别混

```
templates/project/backend/          → 标品工程（五模块）
  ${appName}-assemble/  pom.xml + Application.java + application.y
  ${appName}-biz/       pom.xml
  ${appName}-facade/    pom.xml
  ${appName}-web/       pom.xml
  pom.xml               根 POM（<modules> 列四个）
  .gitignore / README.md

templates/project-ext/backend/      → 客开工程（单模块）
  ${appName}-ext/
    pom.xml
    README.md
    src/main/java/${appPath}/extend/package-info.java
```

★ **「单模块」不是异常，是客开工程的标准形态。**
`extension-project-skeleton.md` 描述的五模块是**标品**骨架，此前被误当成客开骨架。

## 3. `-ext` 与标品工程的关系

`${appName}-ext/pom.xml` 的 `<parent>` 指向 `${appName}`（标品根 POM），并依赖
`${appName}-biz` / `-web` / `-facade`。

README 原文给出两种用法：

```bash
# ① 独立工程开发（只有 -ext）
git clone --depth=1 ${gitExtUrl}

# ② 作为标品主工程的子模块
git clone --depth=1 --recursive ${gitUrl}
git submodule update --remote --recursive
```

`${gitExtUrl}` = 客开仓地址，`${gitUrl}` = 标品仓地址。
两者都由 nacos `repo.gitlab` 的 `apiUrl` + `parentExtendGroupPath` / `parentGroupPath` 派生，
见 `code-repo-and-targets.md` §二。

## 4. 客开可写路径（README 原文）

| 类型 | 落点 |
|---|---|
| 手写扩展代码 | `com/seeyon/[appName]/extend/` |
| 自定义 MyBatis | `src/main/resources/mybatis/xxx.xml` |
| 三方 jar | `pom.xml` 加 dependency |
| 预制数据 | `src/main/resources/init/tenant/xxx.json`、`init/file/private/xxx.jpg` |

模板里写的是 `${appPath}/extend/`，README 里写的是 `com/seeyon/[appName]/extend` ——
两者指同一处，`appPath` 展开为 `com/seeyon/{appName}`。

## 5. 自定义微流程：平台生成骨架，人填实现

`templates/microflow/customflow/` 下 7 个模板：

```
CustomMicroFlowAppService.java.ftl                     对外 facade 接口
CustomMicroFlowService.java.ftl                        业务 service 接口
CustomMicroFlowController.java.ftl                     web 层
DefaultCustomMicroFlowAppServiceImpl.java.ftl          AppService 实现
DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor.java.ftl
DefaultCustomMicroFlowConfig.java.ftl
MicroFlowDubboExportBeanPostProcessor.java.ftl         Dubbo 导出
```

包路径（模板字面量，未展开）：

```
facade 接口   ${appServicePackage}
AppService 实现  ${appPackagePath}.custom.appservice.microflow
service 接口     ${appPackagePath}.custom.service.microflow
```

**接口方法体是平台填的空壳**，原文：

```java
default ${resp}<${respOutputType}> ${name?uncap_first}(${req}<${inputType}> request) {
    ${MicroFlowCodeUtil.throwUnimplemented()}
}
```

★ 所以「自定义微流程」的完整链路是：

```
设计器建类型 + 定义出入参
  → 平台 autocode 生成 7 个类的骨架（含 throwUnimplemented 空实现）
  → 推送 / 拉取代码仓
  → 人在 Default*AppServiceImpl 里填方法体
  → 构建部署
  → 微流程「自定义服务」节点按 SearchAppServiceByAppName 搜得到
```

**不是**「先手写接口再注册」——接口是平台生成的。
此前 `xiaozhua-extension-usage` §7.3 的「代码里定义」表述需按本格修正。

## 6. 其余 autocode 模板（说明平台还替我们生成什么）

```
entity/       14 个   实体 + MyBatis + DDL
microflow/    29 个   含标品节点与 customflow
entityrule/    8 个   规则
refer/         4 个   关联
event/         3 个   事件
filterplan/    2 个   过滤方案
referconfig/   2 个   关联配置
common/       13 个   utils.ftl 等
beanname/ dto/ enums/ feature/ 各 1
project/ project-ext/ project-for-deploy/ 各 1
```

★ 推论：**凡是 autocode 能生成的，都不该手写模板**。手写的价值只在 `extend/` 那层。

## 7. 证据边界

| 结论 | 级别 |
|---|---|
| 模板目录结构、文件名、包变量名 | VERIFIED_STATIC_BYTECODE（逐字） |
| `${appPackagePath}` / `${appServicePackage}` 的实际展开值 | **UNVERIFIED** —— 需一次真实生成后看产物 |
| 生成动作由哪个接口触发 | **UNVERIFIED** |
| 生成后是推 git 还是落 `localBaseDir` | **UNVERIFIED**（nacos 有 `localBaseDir: /code/udc-code`，含义待证） |

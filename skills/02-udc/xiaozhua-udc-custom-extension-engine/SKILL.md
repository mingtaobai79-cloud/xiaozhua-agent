---
name: xiaozhua-udc-custom-extension-engine
description: "Use when 写/改 UDC 扩展代码，或从 jar 抽平台能力事实（Service/DTO/流转）。"
version: 1.0.0
author: 小爪 🐾
license: MIT
platforms: [windows]
tags: [xiaozhua, udc, custom-page, microflow, extend]
metadata:
  hermes:
    tags: [xiaozhua, udc, custom-page, microflow, extend]
---

# xiaozhua UDC · 手写扩展工程（自定义页面 + 自定义微流程）

## When to Use

- 要在 UDC 应用的自定义页面里写/改前端代码（customPage.tsx、dev 调试、加三方库）
- 要实现自定义微流程的后端业务代码（extend 工程、出入参 DTO、AppService/Dao 分层）
- 要找某个应用的扩展工程 git 地址，或分不清扩展工程与标品工程
- **要从 jar 抽平台能力事实**（Service 方法做了什么、DTO 有哪些字段、业务怎么流转）给写扩展当依据
  —— 这类任务的边界见下一节「只盯业务语义，不挖框架机制」

用户口述的平台机制（2026-10-29 固化），本机实物已核对（datamigration<19位应用ID> 工程）。真实环境地址/路径只留 Hermes 侧，仓库落位时按 xiaozhua-agent-fact-protocol 脱敏。

### 边界：只盯业务语义，不挖框架机制

用户明确纠正过（原话：「服务那些不是你的能力，那些人家都想好了」）：写 ext 要掌握的是
**jar 里的 Service 方法做什么、DTO 有哪些字段、业务怎么流转**，不是平台内部怎么装配。

| 该挖（业务面） | 不该挖（框架面，平台已想好） |
|---|---|
| Service 方法 → 调了哪些 Dao / Service / 事件 | 扩展点怎么被注册发现 |
| DTO 字段名与含义（= REST 键名） | Bean 名生成规则、组件扫描范围 |
| 枚举值名、错误码字面值 | 子类型反射扫描走哪些类 |
| 一个动作之后数据落到哪、发了什么事件 | 自动装配顺序、Conditional 条件 |

框架面只在**「我写的东西会不会被调」**这一个问题上才需要（`spring.factories` 键、
注解自带 `@Component`），查到能回答这个问题就停，不要往下钻实现细节。

## 一、总体模型

UDC 设计器里建的自定义页面/微流程 = **平台给的钩子 + 空壳**；真正业务代码写在外置的**前端/后端扩展工程**里。

- 页面出入参、页面变量、页面位置等在设计器里配置（页面属性面板：基础/外框布局/参数设置/高级），这部分固化在平台元数据。
- 扩展工程从 gitlab 拉取，**每个应用一个工程**。

### 三个词别混（混了就会写错地方）

| 说法 | 是什么 | 代码写在哪 |
|---|---|---|
| 标准微流程 | 设计器画布搭节点、存 GraphQL；节点类型如「自定义服务」、数据流、条件分支 | 不写代码，全在设计器里配 |
| **自定义微流程** | 后端 extend 工程手写 Java，通过 impl 实现钩子，外层是平台生成的包装层 | `com/seeyon/[appName]/extend` |
| **自定义页面** | 前端扩展工程手写 React | `pc/src/pages/<页面标识>/customPage.tsx` |

- 「自定义服务」是**标准微流程里的一个节点类型**（`CALL_APP_SERVICE`），不是「自定义微流程」。
  它调的是 AppService / REST / 连接器；微流程自身会暴露成 `MFSERVICE*Controller`，
  所以一个微流程能被另一个微流程当自定义服务调用。
- 自定义微流程 / 自定义页面的技术难点只有一件：**能用哪些库和包**（后端 classpath、前端 node_modules），
  其余就是普通 Java / React 开发。协议、节点结构、GraphQL 契约属于标准微流程那套，
  不要拿它来解释扩展工程，也不要用扩展工程的思路去改标准微流程。

## 二、Git 地址推导规则

```
前端扩展工程： <gitlab域名>/<组名>/frontend/<应用编码>
  例： https://<gitlab域名>/extend-test2/frontend/datamigration<19位应用ID>
标品(非扩展)工程：组名去掉 extend- 前缀
  例： https://<gitlab域名>/autocode-test2/
后端扩展工程： 路径里 frontend 换成 backend
```

git 地址可从 **nacos** 取到对应配置。拉取方式两种（见工程 README）：

```
独立拉取扩展工程：  git clone --depth=1 ${gitExtUrl} && git add . && git commit
扩展+主工程一起：   git clone --depth=1 --recursive ${gitUrl}
                    git submodule update --remote --recursive
                    git submodule foreach git checkout 1.0
```

工程骨架基于 sample 分支：可从 sample 分支单独建 xx 分支当骨架。

**铁律：只有 `-ext` 能写，其余四个模块都是生成物。**

平台给一个 UDC 应用生成的后端工程固定五模块，根包 `com.seeyon/<应用标识>`：

```
<app>-facade    契约：api/*AppService 接口、dto、enums、custom/service、domain/message
<app>-biz       实现：appservice/*Impl、beanname、context、custom/{appservice,config,processor}、
                domain/{entity,dao,service}、registry、schedule
<app>-web       REST：controller/Abstract*Controller（平台生成，Abstract 前缀）
<app>-ext       扩展点实现：extend/ ← 唯一可写层，默认只有 package-info.java
<app>-assemble  启动类 Application
```

依赖单向：`facade ← biz ← web`，`ext` 依赖三者，`assemble` 依赖 web + ext。

- facade / biz / web / assemble **按设计态元数据整包生成，重新构建即整体覆盖**，手改不留痕、无告警。
  这四个只能读（查契约长什么样、查生成的 AppService 有哪些方法），不能写。
- 要改生成层的行为，只能在 `-ext/extend/` 里 implements 扩展点（见决策表），
  改 `XxxAppServiceImpl` 或 Controller 都是白改。
- ext 里也**不要拿 `Abstract*Controller` 当继承抓手**——它随元数据变；要拦请求/改输出口径走钩子
  （`DeployBeforeService` 拦发布、`AppMetaDataContextPostProcess` 改元数据、`TransportHandler` 改导出）。

骨架与包职责表：`core/facts/standard-product/extension-project-skeleton.md`。

以上是**平台生成工程**的五模块；第四节讲的 Dao/Service/AppService 分层是扩展工程内部的代码分层，
两者不要混。

## 三、自定义页面（前端扩展工程）

### 结构与环境

- 环境：node 18.17.1 + yarn 1.22.22
- `pc/` 与 `mobile/` 两端代码并列；页面入口 = `pc/src/pages/<页面标识>/customPage.tsx`（**页面标识**在设计器「菜单 → 查看页面属性」里看：页面 URI）
- 语法就是 React + 平台组件库；`pc/node_modules/@seeyon/` 是平台组件包（清单含 ui/global/udc-core/udc-runtime-core/udc-microflow/biz-org-selector/biz-expression/biz-excel-component/syf 等约 50 个），有能力等价于写普通 React
- 本机实证（datamigration 前端）：6 个 customPage.tsx 已存在；webpack-overrides-custom.js 含 devServer proxy 把 `/<appName>/custom-page-*` 转发到本地端口

### 调试流程

```
1. pc/ (或 mobile/) 下 yarn install
2. 改 webpack-overrides-custom.js 的 hostName 变量为当前调试环境地址
3. yarn start
4. 浏览器访问 http://localhost:3000/login 登录
5. 访问 http://localhost:3000/main/portal/<应用英文名>/<页面URL>
   main/portal 固定；应用英文名=当前应用；页面URL=设计器里的页面 URI
```

### 加非平台预置的三方库（UDC 严格管控三方依赖）

```
1. pc/ 下新建 third_modules/ 目录，在其中安装依赖
2. 运行 yarn syf build-multiple-bundless-module
3. webpack-overrides-custom.js 加 alias：
   config.resolve.alias['echarts-for-react'] = path.resolve(__dirname,
     'third_modules/libs/echarts-for-react/3.0.2/module.js');
4. tsconfig.json 加类型提示：
   "paths": { "@third_modules/*": ["third_modules/node_modules/*"] }
```

### 前端 build/dev 坑（实测，详见 datamigration-audit skill）

- `npm run build` 会删 `dist/.temp/`，与 dev server 互斥；build 前停 dev server，`rm -rf dist node_modules/.cache` 再 build
- 同一 BUILD_VERSION 重复构建失败且产物名层层叠加
- 白屏 React #306 = lazy 动态 import 拿不到模块；「无版本别名 404」是正常形态，别当部署缺失
- 线上产物是 gzip 的，grep 探针先 gunzip

## 四、自定义微流程（后端扩展工程）

本质 = **业务代码，通过 impl 实现钩子**，外面是平台生成的包装层。

### 分层

```
Dao 层        与数据库交互，无限制（平台建的实体自带 CRUD）
Service 层    走平台校验、计算值、计算规则、聚合实体的区别和方法
AppService 层 Service 方法的包装（平台生成的 facade DTO 契约层）
```

- 平台建的实体基本都有 CRUD 方法；实体表自带标品 CRUD，**不要手搓 SQL**（用户裁决，见 datamigration-audit「实体建的表自带标品 CRUD」条）；实在不行可用自研 mybatis 组件，XML 写在 `src/main/resources/mybatis/xxx.xml`

### 出入参（微流程接口的关键）

```
基本类型    八大基本类型
实体类型    通过实体建的都有对应 DTO
绑定规则    出入参绑定的基本是 DTO
自定义对象  自建 DTO，字段可以是 List / 对象 / 实体类型
映射(map)   可以直接用 map 类型
```

### 写一段能跑的扩展代码需要三份事实（缺一份就写错）

| 要知道 | 查哪 | 例子 |
|---|---|---|
| 传什么类型、方法签名 | `packages/<构件>.md` / `domains/<域>.md` | `SingleResponse<BpmSendResultDto> send(SingleRequest<BpmSendDto>)` |
| 类型里有哪些字段、**每个字段怎么填** | `api-usage-cards.md` → `api-usage/<域>.md` | `templateId Long ← 模板ID · 模板code/模板ID两者传其一，如果都传以模板code为准` |
| 调了之后发生什么 | `service-business-flow.md` → `service-flow-*/<构件>.md` | 落哪张表、发什么事件、要不要分批 |
| 怎么把方法真正调起来 | `appservice-invocation.md` | `@Autowired` 注入 + `SingleRequest.from(dto)` + `getData().getContent()`；或泛化调用 |
| 要做的事叫什么方法 | `business-action-index.md` | 按九类动作（创建/修改/删除/流程/发布/导入导出/校验/查询/启用禁用）反查入口 |

**`api-usage/<域>.md` 是前三份的合并视图**（一页一接口：签名 + 入参逐字段 + 返回逐字段 + 流转第一步），
优先看它。字段后面「←」那段是**平台自己写的**（`@DtoAttribute` 的 `value` / `description` /
`example` / `relationDto`），不是猜的——覆盖 98% 的 DTO。
**平台完全不用 `javax.validation`**（扫 1331 个 DTO 命中 0），必填只能看 `description` 的措辞
（「必须」「两者传其一」）或实测；`value` 不总是中文名（`currentUserId` 的 value 是 `userCode`），
靠 `example` / `relationDto` 补。

**业务 Service 在下一层，不在 `XxxAppServiceImpl` 里**：AppServiceImpl 几乎全是一行转发
（`return ListResponse.from(xxxService.select(...))`），真正业务在 `domain/service/XxxService`
——注意它是**具体类，不叫 `XxxServiceImpl`**。只扫 `*Impl.class` 只会得到一份纯转发清单
（实测 151 KB），扫 `domain/service` 才有真业务（646 KB）。抽法与产物见
`references/business-flow-extraction.md`。

**实现 jar 不在 `<MAVEN_REPO>`，要单独从 Artifactory 下 `*-biz`**（本地仓库只有 facade/api 接口 jar）。
漏了这步会把 BPM/组织/事项/连接器 误判成「实现在平台服务端」——实际只是没下实现。
且接口→实现**命名不规则**（`BpmAppService` 的实现是 `BpmApiAppServiceImpl`），
必须读字节码 `implements`，不能按 `XxxAppServiceImpl` 猜。下法、构件清单与映射脚本见
`references/business-flow-extraction.md` §「实现 jar 不在本地仓库」。

### 平台标品能力（三个了解方向）

用法**已经抽好落在仓内**，先读事实格，不要重新反编译：

1. **标品基础组件** → `core/facts/standard-product/` 九格（能力地图、标品接口面、Dao、
   transport、Dubbo、core 工具类与注解）；事实格没覆盖到的才去反编译补
2. **标品 Dubbo 接口与泛化调用** → `dubbo-cross-service.md`（`DubboFactory` 注入即可用，
   四段后处理器自动导出，`AppServiceProxy` 跨应用调用）
3. **开放到 openapi** → 不是一个开关而是注解组合：`@AppService` + `@AppServiceOperation(openApi=@OpenApi(isOpenApi=true,...))`，
   见 `boot-core-utils-and-annotations.md`

引入三方依赖可以，**前提是客户允许**。

⚠ 反编译只是取证手段，**不是交付物**。只抽不写事实格，下一会话照样不会用；
用户对此有明确要求：抽完必须落成「带铁律 + 签名样例 + 证据路径」的事实格。

### 手工代码支持范围（工程 README）

```
- extend 包下写拓展代码： com/seeyon/[appName]/extend
- 手工自定义 mybatis： src/main/resources/mybatis/xxx.xml
- 三方 jar： 正常 maven dependency
- 预制数据： src/main/resources/init/tenant/xxx.json
            src/main/resources/init/file/private/xxx.jpg
```

### 后端既有坑（实测沉淀，详见 datamigration-audit）

- **写之前先用真实 jar 编译一遍探针**（`tools/core/platform/probe_contracts/`，classpath 从索引 `pkg` 字段自动推）：
  一次排掉接口全名 / 方法名 / DTO 字段名 / 取值链 / 类放错构件五类错。`EntityDto` 在 **udc-common**
  不在 udc-facade 就是这么发现的。注意 `DeployNormalDto` 只有 3 个字段、**没有 appId**——
  REST 请求体的字段不等于 AppService 入参，appId 走请求上下文。**编译通过 ≠ 运行时跑通**。
- facade jar 版本卡编译：先 `ls <MAVEN_REPO>/com/seeyon/<appId>-facade/` 查本地新版，javap 确认 setter，三 jar（facade/biz/web）版本一起升
- transport 类型与 Spring 同名类是两套；`SingleResponse.getData().getContent()` 两层取值
- 异步线程必须带租户上下文（tenantId/userId），否则 Dao 写静默失败
- 写完必须回读确认，catch 后 return SUCCESS = 假成功
- 参考代码：`<EVIDENCE_ROOT>`、`<PATH> 下业务代码很多，或 IDEA 直接看

### 写完怎么注册（写了不等于被调）

实现接口只是第一步。平台发现实现的通路只有一条主路：**`src/main/resources/META-INF/spring.factories`**。

- 91 个标品 jar 实测：`META-INF/services` 只有 2 个 jar、3 个文件，且全是第三方
  （ShardingSphere、nacos 集成）；`spring.factories` 48 个 jar、85 个键。
  **给 ext 注册扩展一律写 spring.factories，不要写 `META-INF/services`**——写了也不会被加载。
- 平台自有键 8 个：`ComponentInitializer` / `LogInitializer` / `ComponentDynamicRegister` /
  `ComponentDynamicLoader` / `FunctionSemanticAnalyzer` / `ExtensionFunctionScriptBuilder` /
  `ExtensionFunctionInterpreter` / `CallerSemanticAnalyzer`。逐字签名全表见
  `references/registration-mechanisms.md`。
- **自定义表达式函数必须注册三件套**（语义分析 `FunctionSemanticAnalyzer` + 脚本生成
  `ExtensionFunctionScriptBuilder` + 代码解释 `ExtensionFunctionInterpreter`）。
  只注册一个 = 能保存、跑不对；前端能跑、后端算错。这是表达式/变量域最容易踩的坑。
- **全 default 的接口漏覆写不报编译错**：`ComponentInitializer` 两个方法都是 default
  （父接口 `AutoConfigExclude` 也是），漏写 `initialize` 编译通过、运行时静默无操作。
  方法块全是 default 的接口，编译通过 ≠ 实现正确，要自己确认方法名写对。
- 27 个纯扩展位（`ApplicationInnerReference` / `LimitCountCheck` / `PluginExecutor` …）
  的发现方式仍未确认——8 个键里没有，jar 里也零实现。选它们之前先做最小验证：
  写空实现 + 打日志，构建部署看启动有没有被实例化。

## 五、参考样板

只项目管理平台（autocode 组）有**非扩展**与**扩展**两种页面的代码，可作为对照文档拉取阅读。

## 六、证据状态

### 已落仓的权威事实（xiaozhua-agent，优先读它们，不要重新推）

```
事实  core/facts/standard-product/   ← 包用法（环境无关），共 23 格：
        platform-package-capability-index.md     91 构件能力地图（我要做什么→去哪个包）
        transport-usage.md                       出入参包装
        appservice-usage.md                      AppService 调用约定 + 框架 AOP
        dao-and-mybatis.md                       Dao 层（AllInOneBaseDao / BaseMybatisDao）
        standard-product-appservice-surfaces.md  8 个标品域接口面
        dubbo-cross-service.md                   Dubbo 注入与跨服务
        boot-core-utils-and-annotations.md       core jar 工具类 + 平台注解
        udc-runtime-and-extend-packages.md       UDC 运行时四层链路 + 传输族 4 个扩展点
        frontend-platform-packages.md            前端三包（ui/global/udc-runtime-core 用法增量）
        frontend-package-capability-index.md     前端 50 包能力地图（我要做什么→去哪个包→抓手符号）
        frontend-component-signatures.md         页面组件怎么传参（101 组件 props 逐字字段 / 1686 props 类型 / 291 函数签名）
        udc-microflow-extend-interfaces.md       自定义微流程接口（151 带 abstract = 128 真接口 + 23 注解 / 传输族 4 契约 / 被调入口 / 传参对象 / 工具类）
        extension-project-skeleton.md            扩展工程骨架（facade/biz/web/ext/assemble 五模块职责 + 只有 ext 可写）
        extension-point-decision-table.md        扩展点决策表（9 组场景 → 接口 → 逐字方法 → 平台参照实现）
        extension-registration-mechanisms.md     注册机制（spring.factories 8 个平台键 / 表达式三件套 / 平台不用 Java SPI）
        extension-point-consumers.md             扩展点被谁调用（183 真接口 = 154 跨包 / 21 仅同包 / 8 零引用）
        appservice-dto-fields.md                 **入参 DTO 字段表**（969 个 DTO 字段，按 10 个域分文件）
        enums-and-constants.md                   **枚举与常量值**（758 枚举 / 5632 值名 / 157 常量类 5965 字面值）
        platform-annotations.md                  **注解速查**（109 个 @interface 的 Target/Retention/元注解）
        service-business-flow.md                 **Service 业务流转**（方法背后调了哪些 Dao/Service/事件）
        appservice-invocation.md                 **调用通路**（Spring 注入 vs 泛化调用；AppServiceInvokeDto 10 字段；6 层 Bean 查找；BOOT_4014）
        business-action-index.md                 **业务动作索引**（要做什么→调哪个方法，九类动作反查入口）
        api-usage-cards.md                       **接口使用卡**（一页一接口：签名+字段怎么填+流转+泛化调用模板）
索引  core/facts/INDEX.md（已登记）
实现  components/udc/extension_surface.py            依赖面三态判定（fail-closed）
脚本  tools/core/platform/extract_extension_surface.py   抽依赖面 → surface.json（--emit-signatures 出组件 props/函数签名）
      tools/core/platform/extract_jar_symbols.py         抽单 jar 方法签名面（javap+cfr 双路）
      tools/core/platform/extract_surface_batch_par.py   批量并行抽（进度可续跑）
      tools/core/platform/index_extracted_surface.py     汇总包级索引 + 方法索引
      tools/core/platform/index_backend_interfaces.py    从 javap 签名件归纳「类 → 方法签名 + implements」
      tools/core/platform/emit_interface_inventory.py    接口全量清单（interfaces.json → interface-inventory.md）
      tools/core/platform/emit_extension_points.py       扩展点落地表（接口 × 平台实现；分真接口 / 纯扩展位 / 注解）
      tools/core/platform/emit_domain_surfaces.py        按标品域导逐字签名表（→ domains/<域>.md）
      tools/core/platform/emit_package_surfaces.py       按构件一包一份（→ packages/<构件>.md）
      tools/core/platform/scan_registration.py           扫 jar 的 META-INF/services + spring.factories（→ registration-scan.json）
证据  docs/audit/artifacts/extension-surface-20261029/batch2/  清单内 84 包签名件 + _index.json
      （**是目标清单不是全量**：还须补 udc-biz / udc-web / udc-cicd；同一目录的 surface.json
        是工程相关采集产物，不作结论引用）
      docs/audit/artifacts/frontend-surface-*/surface.json       前端 50 包递归符号面（xiaozhua_packages[].symbols）
      docs/audit/artifacts/frontend-surface-*/signatures.json    组件 props / 函数签名面（components/props_types）
      docs/audit/artifacts/extension-surface-20261029/interfaces.json  类 / 方法 / method_index 总量现查，别抄死
      （清单 84 包 + udc-extend + udc-plugin-api + 补抽的 udc-biz / udc-web / udc-cicd；
        `udc-plugin-api` 是四族接口契约与 TransportData 所在，不在那 84 包里，漏抽会以为它不存在）
      docs/audit/artifacts/extension-surface-20261029/interface-inventory.md  接口全量人读清单（按顶层包分组）
      docs/audit/artifacts/extension-surface-20261029/domains/<域>.md   标品域逐字签名表
      （dubbo / bpm / organization / mybatis / datasource / connector / affair /
        formconvert / formula / systemvariable / file 共 11 个域；每域「接口全签名 + 关键类全签名」）
      docs/audit/artifacts/extension-surface-20261029/packages/<构件>.md  按构件逐包签名表
      （扩展工程 pom 里每个 artifact 一份；含接口全签名 / 关键类 / 注解元素 / 枚举常量）
      docs/audit/artifacts/extension-surface-20261029/registration-scan.json  91 jar 的注册面
      （services / spring_factories / imports 三段 + resolve 字段说明 jar 路径怎么解到的）
测试  tests/udc/test_extension_usage_assets.py         落位闸门（23 项：前端递归/闸门/产物、后端四族、扩展点、决策表接口真实性、11 个域签名表齐全、截图 86 构件逐包齐全、8 个注册键真实性）
skill skills/02-udc/xiaozhua-extension-usage/SKILL.md   仓内 skill（Hermes 侧同名 skill 只是入口）
```

改动用前先跑 `uv run --no-project python -m pytest tests/udc/test_extension_usage_assets.py -q`。

⚠ 早先落在这两处的资产已作废并删除，不要再去读：
`core/facts/udc/extension/`（4 格）与 `tests/udc/test_udc_extension_asset_layout.py`。
作废原因是那批文档混入了工程/环境信息（客户 appId、本地工程路径、parent 版本），
脱离本机就用不了；现已按「包用法归 standard-product、工程结论留证据区」重写。

### 五条会直接导致写错代码的硬结论（已实测，不要重推）

1. **可用清单取自工程依赖解析结果**（classpath / node_modules），不取自 maven 仓库目录。
   仓库里有 ≠ 能 import。
2. **后端平台能力在 parent pom（36 条）**，ext 工程自己的 pom 只有 9 条；只看后者会严重低估。
3. **前端有 HOISTED 态**：`package.json` 没声明但 node_modules 里有（实测 lodash/antd/dayjs），
   能编译但不受 lockfile 保护，用前先补声明。
4. **出入参一律套 transport 包装**；`SingleResponse.getData()` 是 `SingleData<T>` 要再 `.getContent()`；
   `Sort` 用 `com.seeyon.boot.transport.Sort` 不是 Spring 的。
5. **parent pom 版本可能已发布但本地拉不到**——目录里只有 `*.pom.lastUpdated` 时
   parent 依赖静默变 0 条；脚本已加闸门（退出码 4）。

### 抽包用法的方法（顺序 + 四个会让你白跑的坑）

目标不是「反编译了」，而是**把用法落成事实格**。反编译只是中间产物：
只抽不写，下一会话仍然不会用，等于没做。

```
① 定清单   从 classpath 解析结果取 artifact + 版本，不要从仓库目录列
② 批量抽   extract_surface_batch_par.py --workers 10 --limit 1000
③ 汇总     index_extracted_surface.py → 包级索引 + 方法索引（供「哪个类有这个方法」检索）
④ 写事实   按域分格落 core/facts/standard-product/，每格给「铁律」+ 签名样例 + 证据路径
⑤ 落闸门   tests/udc/test_extension_usage_assets.py 里断言分层要素齐全
```

四个坑，每个都曾让整批结果作废：

- **`--limit` 必须 ≥ 该类总数**：`list_classes` 是 `sorted()[:limit]`，按字母序截断会静默丢掉
  靠后的类（实测 `--limit 30` 漏掉 `SingleRequest`/`SingleResponse`/`Sort`，正是最该有的三个）。
  ⚠ 该参数**默认 60**：单 jar 不传 `--limit` 就只抽 60 类（实测 307 类的 jar 只出 60 类，输出零告警），
  一律显式传 `--limit 2000`。
- **只有 cfr 路产出 `symbols` 时，纯 javap 模式 `total_methods` 恒为 0**：84 个包跑完只有类数
  没有方法数，看起来全部成功。抽完必须抽查 `total_methods > 0`，否则整批重跑。
- **`--javap` 传原生路径**：MSYS 风格 `/d/...` 在 Python 里 `Path.exists()` 为 False，
  会被判成工具缺失而静默降级成单路（不报错）。本机 javap 不在 PATH，实际路径 `<LOCAL_ROOT>/java/bin/javap.exe`。
- **取签名面不需要 cfr**：cfr 单 jar 约 60s（会撞超时重试），javap 约 26s；
  84 包串行 cfr 要 85 分钟，javap + 并发 10 约 5 分钟。要反编译正文才加 `--cfr`。

批量脚本必须**每包一行进度 + 按 artifact 去重续跑**：中途超时/被杀后重跑要能跳过已完成的，
否则每次从头来。

**`index_backend_interfaces.py` 的 `extends` / `implements` 解析要容忍行尾 `{`。**
javap 类声明原文是 `public class X implements com.y.Importable {`；正则写成
`implements\s+(…)\s*$` 会因为末尾 `{` 匹配失败，`implements` 字段**整列变成空数组**而脚本
仍 exit 0——症状是「接口全在、实现类一个都统计不出来」。收尾用 `\s*\{?\s*$`；
`extends` 的字符集要带 `[\[\]]`（数组类型）。统计实现类前先断言「有 implements 的类数 > 0」，
否则拿到的是空表而不是零实现。

**证据件里有 ≠ 已经「列出来了」。** `interfaces.json` 里几百个接口对人是不可读的；
成文只写 4 个时，用户问「接口你全部列出来了吗」的答案就是「没有」。每个大集合
（接口 / 组件 / 方法）都要配一个**自动生成的清单文件** + 一条闸门断言（清单声明的条数 ==
源数据条数，且每个条目都能在清单里找到），否则下一个人会以为漏了。
现成范式：`tools/core/platform/emit_interface_inventory.py` → `interface-inventory.md`
（按顶层包分组，每行标 abstract 数与必实现方法）。

**事实格给方向，逐字签名表给可照抄的签名——两层都要有。** 事实格写到「有哪些接口、
各多少方法、关键方法名」就够判断走哪条路；但用户要的是能直接粘进 IDE 的东西，那是
`domains/<域>.md` 的职责（每域：接口全签名 + 关键类全签名，`emit_domain_surfaces.py` 生成）。
只写方法名级会被追问「dubbo / bpm / 组织架构 / mybatis datasource / 连接器 / 事项 /
单据转文档 / 表达式 / 变量 这些都写了吗」——而这些域里 `formconvert`（单据转文档）与
后端 `formula`（表达式）最容易被漏，因为前端有个同名的 JS 函数库，容易以为已覆盖。

**用户给的是「工程依赖清单」时，按构件一包一份，不要只按业务域合并。**
按域导出（`domains/`）回答的是「我要做 X 用哪个域」；但用户核对覆盖时看的是 pom 里
**每一个 artifact**。只做 11 个域会被追问「我截图的那些你没全部覆盖」——截图里
`boot-starter-*` 有 60 多个，域视角把它们并进几个域里，看不到逐包对应。
一包一份：`packages/<构件>.md`（截图 86 个构件 + 后补的 udc-biz/udc-web/udc-cicd/
udc-extend/udc-plugin-api）。闸门 `test_every_screenshot_package_has_surface` 把截图构件名
硬编码进测试，逐个要求文件存在，且文件总数 == `interfaces.json` 的 `sources` 数。
两个视角别混：问「用哪个域」看 `domains/`，问「这个 pom 依赖能干什么」看 `packages/`。

**`classes` 没有「来自哪个构件」字段时，按 Java 包前缀猜域不可靠**（`com.seeyon.boot.starter.*`
有几十个构件共用前缀，`cip-connector-api` 与 `cip-connector-facade` 更是同前缀不同 jar）。
要在 `index_backend_interfaces.py` 解析每个类时打上 `pkg`（来源构件名），重跑索引后再按 `pkg`
分组，否则一包一份根本切不出来。

**没有接口的构件要兜底列全部类**：纯自动装配/配置包（environment、frontend-log 这类）
0 接口 0 关键类，签名表只剩头部几百字节 = 空壳。`if not ifaces and not key_cls:` 时
把全部 class 列出来，别让闸门的「文件过小」检查替你发现。

**改测试就要同步文档计数，口径是 `pytest tests --collect-only -q`（不是仓库根目录）。**
`tests/test_documentation_contract.py` 会自己跑 `pytest tests --collect-only` 拿收集数，
要求 README / `docs/audit/agent-version-audit.md` / `docs/audit/code-reality-audit.md`
里写的 `当前实测：\`NNNN passed\`` 与之**完全相等**。每加一个测试，三份文件共 9 处数字一起改，
否则 4 个契约测试同时红。**先 collect 拿准数再改文档**，不要按上一轮的数字推算——
这轮就是靠猜数字连改三轮才对齐。

**闸门红了先分清是谁的改动。** 这个仓库有并发 agent 在工作，`git status` 里 `??` 的未跟踪
新文件可能是别人还没写完的活。PII 闸门扫全仓（`_rel_files()` 自己遍历磁盘，`--ignore` 也拦不住），
别人的新测试文件里含客户 appId 会让全仓红。这种情况：**不要改别人的文件**，报告是哪一条 + 给一行修法
（如把 `AN = "datamigration<appId>"` 改成 `"datamigration" + APP`），并用
`pytest tests --ignore=<该文件> -q` 自证自己这边是绿的（注意 PII 那条仍会红，因为它是全盘扫）。

**在 bash 里用 `python -c "..."` 改脚本时，反引号会被 shell 当命令替换。**
生成带反引号的 markdown 行（如 `` `Interface` ``）时写进文件的会是残缺内容
（实测变成 `out.append(f"|  | {args} |  |")`，接口名和包名被吃空），而脚本照样打印「已改」、
只在后续闸门才暴露。改脚本一律用 `write_file` / `patch` 工具；非要在 shell 里改，
用 `<<'EOF'` heredoc 并把 f-string 换成 `%` 格式化。

### 前端 d.ts 抽包：三种形态 + 坑（每条都曾让结果作废）

前端没有 cfr/javap，符号面直接来自 `node_modules/@seeyon/<pkg>/**/*.d.ts`，用同一个入口：

```
python tools/core/platform/extract_extension_surface.py \
    --frontend <前端扩展工程 pc 目录> --emit <out.json>
```

**入口 d.ts 绝大多数只是 re-export 壳，必须递归。** 实测 50 个包里 47 个是壳，只解析入口一层会
得到 0 个符号却 exit 0（假绿，证据区看着全绿其实什么都没有）。三类写法都要覆盖：

- `export * from './x'` → 递归进 `x.d.ts` / `x/index.d.ts`
- `import {...} from './x'; export {A, B};` → **export 不带 from**，真符号在 import 指向的文件里
- `declare const X: …; export default X;` → 文件级 declare（无 export 前缀）+ default 收尾

五个坑：

- **注释会被吞进符号名**：`export { /**@deprecated */ Foo }` 会抽出 `/**@deprecated */ Foo`。
  符号名必须整名匹配标识符，不匹配直接丢，不要清洗后拼接。
- **入口不一定在常见位置**：`types`/`typings`/`dist/index.d.ts` 试完仍没有，按路径最短的
  `rglob("index.d.ts")` 兜底（有包的 d.ts 在 `dist/dist/types/` 下）。
- **「有 d.ts 却 0 符号」必须判失败**（退出码非 0，列出包名）：那是解析器失效，不是真无类型。
  真无类型 = **整包没有 .d.ts**（构建脚手架、部分报表包），只报 WARN。
- **值级 ≠ 类型级**：组件本体常以 `export default` 导出，表里留下的是同名 Props/接口。
  分开计数，别把符号数当可用组件数（实测一个 UI 库 151 个符号里只有 19 个值级）。
- **组件有两种声明形态**：`declare const Button: React.FC<ButtonProps>` 之外，UI 库常用
  `export type ButtonType = React.FC<ButtonProps> & {...}`。只认前者会让 94 组件的库只抽到 20 个；
  后者要顺带补一个去掉 `Type` 后缀的别名，否则按组件名查不到。
- **props 常是交叉类型**：`type ButtonProps = Omit<AdButtonProps,'onClick'> & {...}`。
  正则要写成 `type <名> = [^;{]*\{`（等号后跳任意内容到第一个 `{`），只匹配 `= {` 会漏掉一大半组件。
- **签名面扫描要沿所有 `from './x'`（含 import），不能只沿 export 链**：平台包常见
  `import { X } from './components/x'; export { X };`，export 无 from，只跟 export 链会得到 comp=0 的全空结果。
- **抽完必须落事实格**：只出 surface.json 等于没做，下一会话仍然不知道 import 什么。
- **`interface` 的 `extends` 子句不能只放 `[\w.,\s<>]`**：真实写法是
  `interface X extends Omit<SelectProps, 'value' | 'onChange' | 'mode'> {`，带单引号和竖线，窄字符集匹配失败会把**整条 interface 丢掉**，
  症状是「组件有、props 空」。`extends` 段用 `[^{]+?` 收到第一个 `{` 为止。修一次 props 类型库从 734 涨到 1482。
- **全包扫 d.ts 时不能按 `"node_modules" not in p.parts` 过滤**：包目录自己就在 `node_modules/@seeyon/` 下，
  这条判断对每个文件都成立 → 组件数直接变 0 且不报错。要按 `p.relative_to(pkg_dir).parts` 判断（只排除包内嵌套的 node_modules）。
- **全包扫 + 白名单过滤**：props 定义常在「可达链之外」的兄弟文件里，所以 props 类型要全包扫；
  但组件/函数/类只收该包**对外导出符号集**（surface.json 的 `symbols` keys），否则会把包内私有实现当 API 列出来。
  组件名带 `Type` 后缀的补一个去后缀别名，否则按组件名查不到。

### 报覆盖前先算分母

任何「梳理完了」的判断，先拿**可验证的总量**做分母，写出「已覆盖 / 总量」再下结论，
不要用没有分母的「已梳理」这种话。

- **后端分母不能取清单。** `batch2/_batch_targets.json` 与 `_index.json` 的 `totals`
  是**人手写的目标清单**，不是磁盘真相：它只列了 6 个 udc 构件，漏掉 `udc-biz`
  （2380 类，平台全部 `TransportHandler` / `Importable` / `SaveAsHandler` /
  `AppMetaDataContextPostProcess` 真实现都在里面），也漏了 `udc-web` / `udc-cicd`。
  照清单干活会得出「68 个扩展点只有 21 个有实现类」这种假结论。
  真分母 = 磁盘：`<MAVEN_REPO>/com/seeyon/udc-*/*/*.jar` 逐个 `unzip -l | grep -c '\.class'`。
  闸门写法见 `test_all_udc_artifacts_are_indexed`：拿盘上带 jar 的构件集合减
  `interfaces.json` 的 `sources`，缺一个就红。**清单不可信，只认磁盘。**
- 前端分母 = `node_modules/@seeyon` 下的包数（50）与各包 d.ts 里的组件声明数。
- 现状数字不要抄进 skill：以 `interfaces.json` 的 `sources` / `signatures.json` 现场为准，
  每次现查现报（清单会变，抄死就会像上次那样报出过时的「84 包全量」）。

覆盖率不足时直接把数字和缺口摊开。被追问「我给你那么多包你都梳理好了吗」，
就说明分母没算过——先算分母再答，不要辩解。

### 还没做的（别以为已覆盖）

- 自定义页面的**创建 / 构建 / 打包 / 发布**链路没有事实格：现有页面事实只讲 detail-page /
  list-page / menu-bind 的结构，等于只有依赖面约束、没有落地打法。
- 扩展点已全量清点过，**四族只是传输族**。口径链（四个数别混——此前这里写成「26 个 AppService」是错的）：
  ```
  274 个 UDC 接口 = 250 个真接口 + 24 个注解
  250 个真接口   = 55 个 *AppService（调用面，你调它，不要 implements）+ 195 个其他
  195 个其他     = 128 个带 abstract（= 扩展点）+ 67 个无 abstract（标记 / 纯 default）
  ⇒ 128 扩展点 + 23 注解 = 151 个带 abstract（55 个 AppService 也全带 abstract，但不计扩展点）
  ```
  可实现的真接口是 **128 个**（101 个平台已有实现 / 27 个纯扩展位）+ **23 个注解**。
  **动手前先判注解，别 implements 一个注解**：`Importer` / `UpgradeMethod` / `OperationLog` /
  `LogDefault` / `LogDefaultUpdate` / `DelDetection` / `UpdateDetection` / `ConsistencyDetection` /
  `TypeMapping` / `AppOpsAuth` / `AuthModel` / `AuthOperation` / `AppIdRef` / `DataChangeAware` /
  `AttrTypeMatch` / `AttributeExist` / `EntityExist` / `DateValidation` / `TimeValidation` /
  `ExclusivePermit` / `ComparedSchema` / `ExprConsistency` / `LimitCountOperation` 全是
  **贴到类/字段/方法上的注解**，由平台读，不是实现对象。`Importer` 最坑：它的
  `source()` / `model()` 长得像接口方法，实际是 `@Importer(source=…, model=…)`。
  判定一条：`interfaces.json` 里该接口的 `extends` 含 `java.lang.annotation.Annotation`。
  按场景选钩子用 `extension-point-decision-table.md`（部署发布 / 代码生成 / 导入导出与复制 /
  权限 / 一致性检测 / 微流程 / 日志审计 / 应用特性，每行带逐字必实现方法与平台参照实现）；
  全量清单 `interface-inventory.md`；接口×实现落地表 `extension-points.md`。
- **`udc-extend` 里那 21 个类不是平台自动装配的组件，是客开示例**：扫 65 个 udc-* jar
  跨类引用 0 处；类级无 `@Component` / `@Indexed`；jar 内无 `META-INF/services`、无
  `spring.factories`、无配置类（全包仅 84 个 class）。`XxxImporterBase` 这类带 Base 后缀的
  就是给你照抄继承的模板，抄进自己工程要自己注册。**平台真实现全在 `udc-biz`**
  （`PageSaveAsHandler` / `EntityTransportHandler` / `AttributeSetImporterBase` /
  `EventMetaDataPostProcessor` …）。所以「继承实现类覆写 default」只在 udc-biz 的类上成立，
  继承 udc-extend 的类等于什么都没发生——先查 `implements` 来源 jar，再决定继承谁。
  传参对象 `TransportData` / `BaseTransportData` / `AppContext` / `CodeContext` / `SchemaParam` 在同格 §7.7
  （`TransportData` 在 `udc-plugin-api` jar，不在 extend/facade/runtime 那 6 个构件里，抽漏了会以为它不存在）。
  仍未做：这些方法的**运行时**真实行为（`matches()` 返回 false 时平台怎么跳过、`udcDefaultCopy` 覆盖哪些字段）。
- 工程链路（git 地址推导、nacos 取 `gitExtUrl`、打包上传）全部 UNVERIFIED，一次没实做过。

### 原始采集表

| 项 | 等级 |
|---|---|
| 前端工程结构/6 页面/webpack proxy/third_modules | VERIFIED_STATIC（本机实物核对 2026-10-29） |
| @seeyon 包清单（约 50 包） | VERIFIED_STATIC（本机 node_modules） |
| 后端 extend 包 + mybatis xml 存在 | VERIFIED_STATIC（本机实物） |
| git 地址推导规则 / nacos 关联 | 用户口述，UNVERIFIED（未实际从 nacos 取过） |
| yarn syf build-multiple-bundless-module 三方库流程 | 用户口述手册，UNVERIFIED（本工程用 console build 路线，未走此流程） |

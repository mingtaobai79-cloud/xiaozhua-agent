---
name: xiaozhua-constraint-extraction
description: Use when 从UDC jar/前端 bundle 提取权威约束并落成校验模型。
version: 1.0.0
author: 小爪
license: MIT
metadata:
  hermes:
    tags: [xiaozhua, udc, reverse-engineering, cfr, constraints]
    related_skills: [xiaozhua-v8-spi, reverse-engineer-anything, xiaozhua-low-code-environment]
---

# UDC 权威约束提取（jar → 模型 → LIVE 验证）

## When to Use
- 需要知道某 UDC 域（微流程/实体/页面/菜单/条件…）的**真实字段约束、枚举值域、必填项**时
- 出现"形状对但约束错"（如 `entityId` 反序列化失败、操作符非法、必填缺失）需要权威依据时
- 要把前端推断换成**后端编译产物证据**时


把"形状对、约束错"变为证据驱动：不靠抓一个示例或前端推断，而是从**编译产物**提取权威约束，落成常量+校验器，再用真实数据回读证明不误报。

## 方法论（用户明确要求，逐条执行）
方向：`前端功能 → REST/JSON 请求 → biz 业务 service → 交互表（元数据可能在 Redis/存储）`。
1. **以前端为主**：逆向设计器 bundle/chunk（chunk 名≈原源码路径）→ 找到渲染该页面的代码 → 追按钮 onClick → 调用链 → op 名 + body 形状（前端 runtime 真值：`components/udc/frontend_runtime_ops.py`）
2. **Controller 只是入参壳，业务逻辑在 biz**：`udc-web`=`com.seeyon.udc.controller.*`（路由/入参）；`udc-biz`=`com.seeyon.udc.*`（api/AppService、microflow、entity、page、metadata、autocode…）才是真逻辑——**必填/边界校验常在这里，不在 Controller/DTO**
3. **追交互表**：Entity 类的 `@Table(name=...)` 即表名，`@Column(columnDefinition="... NOT NULL ...")` 即列约束；元数据可能在 Redis/OSS，按 `config/` 找
4. 遇 BPM/ORG/USER 应用功能：**同法**追它们的前端+web+biz+交互表（bpm-facade / organization-facade / ctp-user-facade）——不要只按 UDC 一套想象

## 证据源优先级
**先分清要抽的是哪一类——「校验/必填链」与「值域/枚举全集/默认模板」的权威源不是同一个，别用一把尺子。**

### A. 校验与必填链（业务规则）
1. **biz Service 校验方法**（最权威，★DTO 注解常不全）：如 `PageInfoService.checkDefinitionPageDto`——**真实必填链在这里**，DTO 的 `@NotNull` 往往只覆盖一部分。**框架级 check 契约同理**：如 `boot-starter-condition` 的 `ConditionService.checkDetail` 规定 leftParam/operator/rightParams 三者不可 null、GROUP 内从第 2 个条件起 logicalOperator 不可空、type 只能 GROUP/CONDITION——这类结构契约不在 DTO 注解里，也要落成常量（`*_SERVICE_REQUIREMENTS` 或 `CONDITION_REQUIRED_PARTS` 形态）
2. **后端 DTO 注解**：`@NotNull`/`@NotBlank`/`@Length(max=)`/`@Min(0)` → 必填/长度
3. **后端解析器**：`XxxActivity.parseActivityNode()` 里 `NodeUtils.getXxx("f", node, required)` 的 required 标志
4. **后端枚举类构造参数**：`.name()` + 构造参数（如 `OperatorEnum("=","等于",1)` 的第三参=右参个数）

### B. 值域 / 类型全集 / 默认模板 / 控件映射（设计态）
1. **前端设计器 registration 表**（design-time 权威，常是**全集**）：类型注册表、中文名表、默认属性模板、值域上下限、控件映射——UI 的下拉/校验直接由它驱动
2. **后端 starter/jar 枚举**（常是**运行时子集**，用于补 caption/i18n key 与运行时行为）
3. 两侧都实测后**取并集并对差，哪边大以哪边为准，不预设方向**

**方向不定，必须实测**：条件操作符前端只露 20、后端 22（后端全集）；UDC 属性 dataType 前端 34 种、后端 `boot-starter-datatype` 只有 15 种（**前端全集**）。把任一侧写成「权威」都会判错。

## 工具链
- **CFR**：`<HERMES_HOME>/skills/seeyon/03-v8-extension/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar`
  - 单类：`java -jar cfr.jar <全限定类名> <jar路径>`
  - 整包：`java -jar cfr.jar <jar> --outputdir <dir>`
  - 内部类：`.../Outer$Inner`（如 `DataMappingRow$DataMappingMode`）
- jar 源：`<MAVEN_REPO>/com/seeyon/<artifact>/<version>/<artifact>-<version>.jar`（123+ 构件）；解包目录 `<HERMES_HOME>/cache/scratch/udc-biz-x`、`udc-web-x`
- 包→域：`udc-biz`=业务+元数据+`com/seeyon/udc/api/*AppService`（240方法）；`udc-web`=`com/seeyon/udc/controller/*`（54 Controller/299 REST）；`udc-common`=DTO/数据类型；`udc-plugin-api`=页面 DTO；`boot-starter-condition`=条件框架
- **四张调用面，追端点先问在哪一面**（串面必 404/误判）：
  1. 设计态 REST `/udc/*` — udc-web Controller（设计器页面操作）
  2. GraphQL 动态字段 — 前端 `udcQueryLoader`/`udcMutationLoader` → 后端 `udc-runtime/graphql-proxy/graphql`（GraphqlProxyController→GraphqlProxyAppServiceImpl，autocode `GraphQLControllerUtil.java.ftl` 生成桥接）
  3. 运行态 REST `/udc-runtime/*` — **按 URL 前缀跨构件取并集**：`udc-starter-runtime` 19 个 Controller **+ `boot-starter-extmetadata` 的 `UdcMetaDataController`（与 udc-starter-runtime 的两个 Controller 共用 `udc-runtime/meta-data` 基址）与 `UdcAppInfoController`（`udc-app-info` 基址）**，合计 21 Controller / 98 端点；不是 udc-web 的子集
  4. 元数据 `/metadata/*` — `boot-starter-metadata`（应用合法性/发布状态/`udcApp`/`enableGraphql`）
  starter 里也可以有完整 Controller 层：抽端点目录时 `@RequestMapping` 扫描范围必须包含 `udc-starter-*`，否则运行态整面会漏。**URL 前缀 ≠ 构件归属**：`udc-runtime/*` 由多个构件共同服务，端点清单必须跨构件按前缀求并集。详表（CFR jar 路径见 SKILL.md 工具链）见 `references/udc-rest-surfaces.md`
- **内建 starter 必挖**（约束常藏在这里，只挖 udc-biz/udc-web 会漏掉设计态值域与运行时行为）：`udc-starter-{runtime,lowcode,dataflow,customplan}`、`boot-starter-{datatype,condition,enums,metadata,extmetadata,dynamicsql,serialnumber,parameter,systemvariable,graphql}`；其中 `boot-starter-extmetadata` 的 `enums` 包是**实体/页面各级枚举值域的权威源**（EntityCategory 6 种 / AttributeCalculate 3 / AttributeSource 5 / PageSource 4 / MedaDataPageType 14 / OpenWay 2 / DependentApp 5，含 code 与中文显示名）；`boot-starter-serialnumber` 是**流水号全机制**（4 Controller / 45 端点 / 6 张表，`/serial-*` 独立前缀）。**各构件版本号可与 udc 不同**（如 datatype 5.3.358、serialnumber 5.3.318 对 udc 5.3.517），取该构件自身最新版
- **有两个功能完全不在 udc 构件里**：导入导出模板在 `boot-starter-excel`、二维码规则在 `boot-starter-qrcode`。
  这两个的 Controller/DTO 在 `udc-biz`/`udc-web` 里 `unzip -l` 都是空的，按 GET 路径去 udc 构件里找会得到假 VACUUM。
  **定位手法**：按业务词扫全仓 jar，而不是在 udc 构件里翻——
  `for j in $(find /d/repo/CHIT -name '*.jar'); do unzip -l "$j" 2>/dev/null | grep -qi 'ExcelExportTemplate' && echo "$j"; done`
  （`SerialScheme` / `QrCodeRule` 同法）。命中的 artifact 名就是归属。
  两个都是 **REST 而非 GraphQL**，且走 `/service/udc/<svc>/*` 前缀。
- **jar 内嵌资源是行为类约束的权威源**（比反编译更原始）：`app_feature/<type>/backend_config.json` 这类被打进 jar 的配置文件直接给出"什么应用能做什么"的矩阵——应用功能开关、实体版型白名单、默认版型、宿主依赖清单、是否动态服务。先 `unzip -l <jar> | grep -E '\.(json|xml|properties|yaml)'` 扫资源，落 `reference-src/` 后按域抽。实测：udc-plugin-api 的 `app_feature/{business,standard,form,integration,layout,onlypage}/backend_config.json` 是**应用类型→实体版型**约束的唯一权威（反编译枚举只能拿到 DependentAppTypeEnum，拿不到"标准应用只允许 standard 版型"这种组合规则）

## 前端 bundle 表抽取（design-time 值域的唯一可靠来源）
设计器前端以 webpack chunk 落地：`<解包目录>/<原源码路径·hash>/module-<id>.js`（chunk 目录名≈原源码路径）。每个 chunk 里的 `export let X = ...` 就是一张表：
- 类型注册表 `{String:"STRING", Integer:"INTEGER", ...}` → JavaType→dataType（**值域全集**）
- 中文名 `new Map([[pe.String,"文本"], ...])` → 值域→中文名（导出时 `Map`→object）
- 默认属性模板 / `{min,max}` 值域 / 控件映射（PC/MOBILE）/ 日期格式 → 另外几张导出表

**不要手抄，用 node 求值导出**：`node <skill>/scripts/extract_chunk_tables.mjs <unpacked-dir> <module-name...> --json tables.json`
（chunk 是 ESM 且内联 webpack `require(id)`；脚本注入 `require` stub 后 `import('file:///...mjs?t='+Date.now())`）。
定位宿主 chunk：`grep -rl "<只在设计器出现的值域字面量>" <unpacked-dir>`（如某个大写类型名），命中文件即注册表。
UDC 已实测的四张表与数值见 `references/frontend-bundle-mining.md`。

## 前端 op 无 REST 路径 = GraphQL 面（不是缺失）
前端 op 有两条通道：**LIVE REST**（`/udc/...`，`udc-web` Controller 承接）与 **GraphQL**（前端 `udcQueryLoader` / `udcMutationLoader`）。
- 某 op 翻遍所有 Controller 都没有路径 → 通常是 GraphQL 动态字段：后端由 autocode `GraphQLControllerUtil.java.ftl` 生成，转调 `boot.starter.udcrt.appservice.*`；`paramsKey` 只决定 GraphQL 变量名（`query`/`body`）。
- 生产环境 **introspection 被禁**（`__schema` 内省返回 0 字段）——别用内省枚举字段，也别据此判「字段不存在」；**前端 bundle 里的 loader 定义（`fieldType`/`paramsType`/`queryFields`/`params`）就是权威证据**。
- **调用形态固定**：`POST /service/udc/graphql?<op>`，`mutation graphqlLoader ($x: <op>InputBody) { data0: <op>(body: $x) { code message status data { content{...} } } }`；**`data` 下必须包 `content{...}`**，直接写字段报 `FieldUndefined`。业务错误是 HTTP 200 + `data0.status!=0`（`code` 为 `BOOT_*`/`UDC_*`），别按 HTTP 码判成败。
- **微流程（type=0）保存前有服务端校验探针** `udcMicroflowCheckSchemaUpdatePost`：REST 直调即可拿到 `content{check, errorMessage[]{nodeId,path,propertyKey,message}}`，是「不点界面判结构是否合法」的权威手段；type=FRONTEND/DRAFT 不校验直接存。完整配方与微流程节点落数据的「所选数据已变更」根因见 `references/udc-graphql-invocation.md`。

## 步骤
1. 定位域（微流程/实体/页面/菜单…）→ 找 DTO + 枚举 + Controller + **biz Service**（业务逻辑所在）
2. CFR 反编译 → 正则抽注解+类型+字段名：`((?:@\w+(?:\([^)]*\))?\s*)+)private\s+(@?\w[\w<>\[\], .]*?)\s+(\w+)\s*[;=]`
3. 落成 `components/udc/<domain>_constraints.py`：`FIELDS`/`REQUIRED`/枚举 dict + `validate_*()`；**只写有证据的项**，无证据的推断必须删（证据完整性）
4. 写 tests/udc/test_<domain>_constraints.py 断言值域/必填
5. **LIVE 回读**：拉真实数据（test2 app=8704025620829192834）跑 validate_*，要求**零误报**
6. **LIVE 终态验收**：从零构造对象 → 本地 `validate_*` → 在线创建 → 回读一致。**DTO 注解不全时用逐层迭代**：构造最小 body 打真实创建接口，读 biz 抛出的 `BusinessException` 文案，补字段，重复直到成功——每一条错误文案就是一条 biz 层约束（例：页面创建依次报 `pageUrl` → `pageItems[].urlType` → 菜单绑定 → `curTerminalType`）。**把捕获到的 biz 层强制项写进 `<domain>_constraints.py` 的 `*_SERVICE_REQUIREMENTS` 常量**，不要只留 DTO 的 @NotNull。具体端点/最小 body 见 `references/udc-creation-recipes.md`。

## 踩坑
- **GraphQL 面不校验未知字段 → 猜字段名不可收敛，必须反编译 DTO**：给 `body` 塞一个
  完全不存在的字段，和塞一个拼错的字段名，平台返回的是**同一个业务校验错**
  （例：`BOOT_1001 流水号段 个数必须在1和12之间`）。于是「试 N 个候选 key 看哪个不再报错」
  在这类端点上永远试不出来：报错信息里没有 "Unknown field"，猜错和猜对长得一模一样。
  判据：**只要错的是业务校验而不是反序列化/字段解析错，就说明字段被静默丢弃了**，
  停下来改走反编译（本章工具链），别再扩大猜词表。
- **DTO 字段名 ≠ 表列名，写库后回读要对两套名**：DTO 常用 camelCase 短名（`size`/`dateType`/`show`），
  物理列带前缀（`section_size`/`is_date_type`/`is_show`）。用 DTO 名查表会 1054 Unknown column，
  用列名拼 body 会被静默忽略——这正是上一条能藏住的原因。
- **枚举传字符串，DB 存 ordinal，两边不是同一套**：body 里写 `"NONE"`，落库是 `2`。
  回读时先用反编译的枚举常量表把 ordinal 反查成名字再判语义，**不要拿 DB 数字
  直接当值域**（会得出 `fill_type=0` 是“不填充”而实际是 `LEFT` 这类反向结论）。
- **同名不同父的枚举容易混搭**：一个 DTO 里 `serialType` 用 `SerialRuleTypeEnum`(APP/BIG/SMALL)，
  而同文件的段对象 `type` 用 `SerialTypeEnum`(CONSTANT/CONTEXT/ENTITY/SERIAL)。
  落校验器时每个字段必须绑到自己那个枚举类，绑错会在本地校验阶段就被自己拦住（这是好事）；
  但若校验器写松，错值就会等到线上才暴露。
- **f-string 花括号**：错误消息里写 `{type:'GROUP'}` 会 TypeError，须 `{{...}}`- **multiRequestBody**：`@MultiRequestBody Map params, @MultiRequestBody Sort sort` 的接口，body 要 `{"params":{...}}`（裸字段返回 `BOOT_3000`）
- **`@MultiRequestBody` 里的空对象 `{}` 也会炸**：每个 `@MultiRequestBody` 对应 body 里一个平铺 key，
  但传 `{"sort": {}}` 会报 `BOOT_3000 message:null`（反序列化空对象失败）——
  传 `{"sort": null}` 或直接省略该 key 才行。实测：二维码规则 search 三个
  `@MultiRequestBody`（pageInfo/paramsDto/sort），`sort:{}` 失败、`sort:null` 成功。
  判据：`BOOT_3000` + `message:null`（message 为空）几乎总意味着「某个入参反序列化失败」，
  优先怀疑空对象/空数组/类型不匹配的嵌套入参，而不是参数名。
- **分页对象不是 `{page, size}`**：平台分页 DTO 是 `{pageInfo:{pageNumber,pageSize}, params:{...}}`
  （`PageRequest extends ListRequest`，反编译 `boot-core` 的 `transport/PageRequest.java` 可得）。
  写成 `{page:1,size:10}` 同样返回 `BOOT_3000 message:null`——看着像接口不对，实际是参数形态错。
  另外 `params` 在不同 Controller 里可能叫 `params` 或 `paramsDto`，逐个看签名，不要套用上一个的。
- **列表接口可能内置隐式过滤条件**：`selectPageByCondition` 里硬写
  `columnMap.put("isCustom", false)`，于是自定义数据在标准列表里永远 0 条。
  遇到「DB 里明明有、接口返回 0」时，去反编译看 Service 方法体里对 `columnMap` 做了什么，
  而不是换查询条件、换应用 id 反复试。同理也解释了另一类现象：写入成功但查不到 =
  写入时带了不同的 flag（如 `isCustom=true` 落库、列表只查 `false`）。
- **列表读回来丢字段：JSON 字符串列替代了嵌套 List**：DTO 声明的 `List<List<X>>` 字段在
  响应里恒为 `null`，真实内容存在同名的 `String` 列里（如 `metadataContent`/`excelHeadInfo`
  存 `json.dumps(二维数组)`）。写的时候两个都要填同一份，读的时候优先读 JSON 字符串列、
  回落 DTO 字段——不要因为 DTO 有那个 List 字段就以为响应会填充它。
- **同 jar 多类打包**：CFR 输出 `X.java` 可能含多个类（依赖内联），用 `t.rfind("class X")` 定位真正的定义
- **CFR 反编译单个类必须先抽 .class**：直接 `java -jar cfr.jar <全限定类名> <jar>` 会 dump **整个 jar**（二十多万行）。正确姿势：`unzip -p <jar> com/x/Y.class > tmp/Y.class` 然后 `java -jar cfr.jar tmp/Y.class --extraclasspath <jar>`。类不在预期 jar 时先在仓库层 `unzip -l` 扫哪个构件含它
  - **批量反编译用脚本递归整包，别手列目录**：`node <skill>/scripts/dec_jar_classes.mjs <解压根目录> <输出目录> [--filter 子串]`（os.walk 等价遍历 + 跳过 $ 内部类 + 自动 --extraclasspath）。手列子目录常漏嵌套包（`domain/service`、`domain/event`），枚举类也可能在任意子包而非 `enums/`——dump 枚举同样用 `node <skill>/scripts/dump_enums.mjs <输出根目录> --json`，它按文件名 `*Enum.java` 递归查找
- **非 ASCII 常量在 CFR 输出里是 `\uXXXX` 转义**：要定位某中文报错文案（如『页面必需绑定归属资源』）出自哪个类，用 Python 按字节正则搜 .class（`re.finditer(rb'[\xe4-\xe9][\x80-\xbf]{2}...', data)` 再 decode），`grep \uXXXX` 和 `strings -e S` 往往匹配不到
- **operation name 规范**：`udc<Base去掉udc/前缀><Path Pascal>Post`，与前端 runtime op 对齐（`components/udc/frontend_runtime_ops.py`）
- **插入代码块的幂等判定要用「定义形态」而非裸子串**：`if "ENTITY_DATA_TYPES" not in src` 会被文件里早就存在的一句注释骗过 → 静默跳过，块根本没插进去（写入后行数几乎没变）。判 `NAME: tuple` / `NAME = {` / `def validate_` 这类定义形态。
- **加了新常量要同改测试的 import 块**：`tests/udc/test_<domain>_constraints.py` 顶部 `from components.udc.<domain>_constraints import (...)` 不补新符号，新用例直接 NameError——看着像逻辑错，其实只是 import 漏；改约束模块时把测试 import 一并改掉。
- **文档测试数**：`tests/test_documentation_contract.py` 断言 README/audit 里的 `N passed` 必须等于 `pytest --collect-only` 的 collected 数（不是 passed 数）。新计数必须**实际跑** `pytest tests --collect-only -q | tail -1` 取值，不要用加减法猜——既有文件内追加用例和新增测试文件一样都涨 collected，猜错就 4 个文档契约测试一起红。旧数字以**多种措辞散落在多个文件**（README.md / agent-version-audit.md / code-reality-audit.md，含 `N passed`、`N tests`、单独成段的 `` `N` ``、以及审计文档里引用的 collect 输出行）：只 sed 一种措辞会让 `_documented_count` 从同一文件抽出两个不同的数 → 集合不相等 → 4 个测试红在一起。grep 旧数字全仓扫一遍再统一替换，然后单跑 `pytest tests/test_documentation_contract.py -q`（秒级，是最快信号），不要等全量跑完再看
- **端点目录计数别信全局正则**：`@GetMapping(value={"datalog/{id}"})` 里的 `{var}` 会被截断正则吃成 `{id`，归一化后字典键 `{x}` 对不上，全局 grep 算出的"真实端点数"平白多出一堆假缺口/假多。逐 Controller 列出注解完整文本再计数，路径变量开闭括号两边都要核
- **枚举值域做全集对账，子集是静默 bug**：落模型的每个枚举都要与反编译**全量**常量逐个比对——只写权威值域的一个子集不会报错、没有测试能发现（除非测试断言全集），但写操作会被误判非法或错误归一化。两种典型病态：①值域只在注释里被引用、从未定义；②只列了 1/N（如 `ENTITY_CATEGORIES` 曾只有 `ENTITY`，权威 `EntityCategoryEnum` 是 6 种）。做法：把目标构件 `enums` 包整包反编译，逐枚举 dump 常量名+构造参数（code 可非连续：`AttributeSourceTypeEnum` 跳 3、`MedaDataPageTypeEnum` LAYOUT=14/SUBPAGE=13），再与模型 diff
- **dump 枚举常量必须用双模式正则**：只匹配 `NAME(` 会漏掉**无构造参数的简单枚举**（`PUBLISHED, UNPUBLISHED;` 结尾，`ServiceStatusEnum`/`SerialResetRuleEnum` 的尾部常量就是这种）。补一条 `^\s+([A-Z][A-Z0-9_]*)\s*[,;]` 抓无参常量，两模式取并集——单模式会把 3 值枚举 dump 成 2 值而**自己看不出错**（`CutTypeEnum` LEFT/RIGHT/NONE 曾被 dump 成 2 个）。凡是本技能历史上用旧 dump 落地的枚举表都有此风险，复用时先按双模式重 dump 校验一遍
- **路径模式查找要逐段匹配**：把 `{id}` 归一化成 `{x}` 存字典后，查 `datalog/123`（含具体值）用字面 key 必然 miss。查找函数要做段级比较（字面段相等 + `{x}` 段匹配任意非空段），否则"端点未登记"是假阳性
- **只读/写分级要按功能而非名字**：`dynamic/jar/import/status/{requestId}` 名字含 import 但功能是查导入状态 → 只读；写端点（delete*/create*/update*/clear*/unload*/init-tenant*/enable-log/import/upgrade/copy）在 LIVE 只读探针里禁调，分级错=禁区误入
- **仓库 git 卫生**：`tools/` 是共享目录，**其他任务（别的客户）的临时探查脚本会落在那里**；`git add -A` 会把它们一并扫进本仓。强制用 `git add <具体文件>`，提交前 `git status --short` 扫一眼未跟踪项；发现其他任务的脚本（看文件头用途/时间戳 / 只读别的 .env）就 `mv` 到 scratch，别提交。客户业务明细不进驻仓库事实库。

## 写入方 / 引用方追踪（编译期常量内联陷阱）

要找「谁写了这个 metadata key / 谁引用了这个常量」，**源码级 grep 常量名会给出 0 命中，而这个 0 是假的**：`public static final String` 是编译期常量，javac 把字面量内联进每个调用点的 class，常量类与调用方之间不再留符号引用。于是 `grep DATA_FLOW_MAPPING_ID *.java` 只能找到定义处自己，看起来像「没人写」。

正确做法是**字节码级搜字面量**——内联后字面量反而散落在所有调用点，搜得到：
```bash
# 1. 只解相关构件，不要全量解压（1500+ jar 的仓库全解开要跑很久，且会中途放弃）
for j in $(find /d/repo/CHIT -name '*.jar' | grep -iE 'udc|boot-starter|autocode|dataflow'); do
  unzip -o -q "$j" -d "mdt/j_$(basename "$j" .jar)"
done
# 2. 搜 key 字面量 → 读取方 + 定义方全集
grep -rl "<key字面量>" --include=*.class mdt | sed 's|^mdt/j_||'
# 3. 反编译全部含写入 API 的类，抽出每条调用行，逐条看 key 实参
for c in $(grep -rl "putMetadata" --include=*.class mdt); do
  java -jar cfr.jar "$c" --outputdir pkeys --silent true
done
grep -rh "putMetadata" pkeys --include=*.java
```

**判「不存在」必须给出可自证的分母**。只说「我没找到」等价于 UNVERIFIED；要写成 STATIC 否定，须报出四个数且命中为 0：解了哪些 jar（N 个）/ class 总数 / 含写入 API 的类数 / 调用行总数。分母越大否定越强，读者能复算才不是自述。

**追方法定义要沿继承链走到底，再判断可查边界**：`DetectionContext extends AppContext extends MetaDatable`，`getMetadata/putMetadata` 声明在最外层 `MetaDatable`，而它**不在仓库任一 jar 内**（逐个 `unzip -l | grep` 全空）——这时「写入方不可见」才是硬结论，而不是「还没找到」。在继承链上停早一步，会把父接口的方法误判成「不存在」，把「越界」误判成「没有」。

**同族对象按类型全集统计，别按单个样本名泛化**：同一语义字段会出现在多种节点类型上（`CALL_DATA_FLOW_FRONT` 与 `CALL_DATA_FLOW` 各有自己的 `dataFlowMappingId`，两套键喂同一个集合）。只查一种类型就报数 = 少算一个数量级，而且自己看不出来。先枚举全类型，再逐类给「有/无 + 分子/分母」。

**按 name 统计 = 跨对象混算**：同名流程/节点在全库普遍（同名 `executeAll` 跨三库 6 个不同 id）。任何分组统计前先把 id 取出来、按 id 归一，再谈「几个」。

## 应用类型约束链（udc-plugin-api `app_feature`，jar 内资源权威）

**应用类型 → 实体版型 → 宿主依赖**三级约束，决定"什么应用能建什么实体"。落在 `components/udc/plugin_api_constraints.py`。

| 应用类型 | featureType | 动态服务 | 实体版型 | 默认 | 宿主依赖 |
|---|---|---|---|---|---|
| 业务应用 | BUSINESS | false | archive / archiveTree / bill / standard | standard | 9（organization,bpm,ctp-affair,ctp-message,cip-connector,cdp-data,portal,ctp-user,app-common） |
| 标准应用 | STANDARD | false | **仅 standard** | standard | 6 |
| 表单应用 | FORM | true | standard / form | **form** | 5 |
| 集成应用 | INTEGRATION | true | 仅 standard | standard | 2（organization,ctp-user） |
| 布局应用 | LAYOUT | true | standard / form | standard | 4 |
| 单页应用 | ONLYPAGE | true | standard / form | standard | 3 |

- **组合约束（值域对账抓不到的第三类病态）**：`ENTITY_STEREOTYPES` 是 5 种全量并集，但**它按应用类型分级**——标准应用建 bill 版型是非法的。单查枚举或单查前端都发现不了这条规则，只有 `app_feature` 的 backend_config.json 同时给出「允许集合 + default」。校验器：`validate_entity_stereotype_for_app(app_type, stereotype)`
- 权限模型同包：`AuthOperationType` = CREATE(1)/DELETE(2)/UPDATE(3)/SELECT(4) + UNKNOWN(0)；`AuthCheck.check(op, entity|dataId) → AuthCheckResultDto{success,message,msgParams}`；`@AuthModel(name=...)` 注解标记模型；`AuthCheckFacade` 聚合
- 插件契约层（纯 AppService，无 Controller）：`ApplicationAppService` 52 方法（应用全生命周期 create/copyApp/saveAsTemplate/deployNormal/deployForm/一致性检测/导入导出）；`UdcSerialSchemeAppService` 5 方法（含 `createEasyScheme`——流水号方案设计态契约，与 udc-starter-runtime 的 `serial-config/list` 运行态查询面是两层）

## 在线写验证（终态验收延长链）
从零构造→校验→在线创建→回读：
- **实体创建**：`POST /service/udc/entity`（body=EntityDto）→ 返回 `data.content` = 新实体 id。
  端点无子路径（`POST /service/udc/entity`），不是 `/create`（那是 udc-web @PostMapping("create") 与网关路由不一致的坑）。
  回读：`GET /service/udc/entity/{id}`，`data` 可能直接是 EntityDto 或 `{content:...}`（两种都处理）。
- 回读后跑 `validate_entity` 确认必填字段一致。
- 微流程的从零验收见 `tests/udc/test_author_from_constraints.py`（本地 PASS，不下发）。

## 分页/列表接口的 MultiRequestBody 坑（再强调）
`@MultiRequestBody Map params, @MultiRequestBody Sort sort` → body 必须 `{"params":{...}}`（裸字段返回 `BOOT_3000`）。
例：`POST /service/udc/entity/attribute/search-list`。

## 长跑补全任务（用户要求的工作形态）
当一个任务要跨多轮/多会话把很多域补全到底（"直到所有位置完整"），用户要的是：
1. **一份方法提示词**落盘（如 `docs/audit/udc-semantics/COMPLETION-METHOD-PROMPT.md`）：目标、方法论、环境、硬约束、**完成判据 checklist**（可勾选，全部 ✅ 才可暂停）。
2. **一份进度看板** `PROGRESS.md`：每域一行「权威约束 / 从零验证 / 备注」+ 下一步排序 + 阻塞项；每轮**原地更新**（改状态行、记证据、重排下一步），cron run 也读它定下一步。
3. **每 N 分钟自检 cron**（`cronjob_manage`）：prompt 里写明「先读方法提示词+PROGRESS → 跑测试/compileall 确认基线未破 → 从下一步推 1 个最小项 → 原地更新 PROGRESS → 完成判据全 ✅ 则报『可暂停』」。配 `workdir=<仓库>` + `continuity=true`。
   - **cron 从 CLI 会话建时 `deliver` 默认只 `local`**：输出存下但**不推送回当前会话**；要真正提醒到平台，`deliver` 必须指向已连接的 messaging 平台（如 `telegram`/`all`）。建立时就告知用户这个区别，不要承诺会推送到本会话。
4. **达到判据前不暂停**；暂停时给清单一句话汇报（已达成 / 边界 / 未完成）。

## 参考
- **设置域里的 REST 子域（导入导出模板 / 二维码）**：DTO、枚举、
  `isCustom` 隐式过滤、`sort:{}` 报 BOOT_3000、构件归属定位法 →
  `references/rest-subdomains-excel-qrcode.md`
- 具体创建端点 + 最小可用 body（实体/页面/菜单）：`references/udc-creation-recipes.md`
- 前端 bundle 挖掘（chunk 布局 / 表抽取 / UDC dataType 四表实测值 / REST-vs-GraphQL 判定）：`references/frontend-bundle-mining.md`
- 四张调用面 + 运行态端点目录（跨构件并集、只读/写分级、DTO 必填、逐段匹配查找）：`references/udc-rest-surfaces.md`
- GraphQL 调用配方 + 微流程保存/校验链 + 节点引用候选列表铁律（「所选数据已变更」根因）：`references/udc-graphql-invocation.md`
- chunk 表抽取脚本：`scripts/extract_chunk_tables.mjs`
- 执行中的进度看板与方法提示词：`docs/audit/udc-semantics/PROGRESS.md` 与 `COMPLETION-METHOD-PROMPT.md`
- 应用类型功能矩阵与权限模型详解：`references/app-feature-matrix.md`

## 已落模型（本机）
见 MEMORY：`components/udc/{microflow,entity,page,menu,runtime,metadata,serialnumber,plugin_api}_constraints.py` + `docs/audit/udc-semantics/*.md`（运行态 98 端点目录与元数据域见 `references/udc-rest-surfaces.md` §2–3，流水号域见同文件 §5；实体/页面枚举值域表亦见同文件 §6）。

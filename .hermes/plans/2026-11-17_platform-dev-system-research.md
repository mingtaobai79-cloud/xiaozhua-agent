# Seeyon 平台开发体系研究计划与证据地图

> 状态：**计划阶段，未实施**。经确认后再开始研究。
> 生成日期：2026-11-17
> 仓库：`C:/Users/白明涛/xiaozhua-agent`

---

## 零、先看边界：这次研究能到哪一层（必须先说清）

盘点结果显示，**部分任务要求的证据源在当前仓库不存在**。这不是推测，是查证结果：

| 任务要求 | 资产是否存在 | 实际情况 |
|---|---|---|
| 检查生成器源码 | ❌ 无 | 仓库无 `autocode` 的 Java 源码，只有 1 个 javap |
| 检查模板内容（.ftl） | ❌ 无 | **只有模板清单** `_codegen_templates.json`，0 个 .ftl 文件 |
| 实际生成结果 | ⚠️ 部分 | 有 `_codegen_templates.json` + 3 个 udc-biz javap；无完整生成产物 |
| 平台 jar 本体 | ❌ 无 | 无 jar 文件；无 CFR 反编译工具 |
| 类/方法签名 | ✅ 有 | `signatures.txt.gz` 21389 类 / 224320 方法 |
| DTO 中文字段 | ✅ 有 | `dto-meta.json` 1305 个 DTO |
| 业务动作→方法 | ✅ 有 | `action-index.md` 682 条 |
| 接口→实现→jar | ✅ 有 | `impl-map.json` 269 接口 / 270 实现 |
| Controller 契约 | ✅ 有 | `udc-platform-5.3.517` 255 个 javap |
| 反编译源码 | ⚠️ 部分 | 212 个 .java，集中在 bpm-addsign / ctp-user |

**结论：任务二中「必须检查生成器源码、模板和实际生成结果」这一条，当前只能做到
「模板清单级 + 签名级」证据，做不到「模板源码级」。**

这一条会影响交付等级，我建议二选一（**需你确认**）：

- **方案 A**：先做能做的（签名级 + 清单级），把模板源码级标 `BLOCKED`，后续拿到 jar 再补
- **方案 B**：先补资产（拉 jar / 装 CFR / 下 .ftl），再做完整研究，周期更长

---

## 一、资产盘点（已完成，逐项核实）

### 1.1 现有 facts（228 md + 107 json）

```
core/facts/
├── standard-product/    29 md   标品域（任务一、五主战场）
├── udc/                 8 子域  entity/expression/microflow/page/serial/setting/write-chain/application
├── bpm/ connector/ spi/ runtime/ deploy/ gateway/ item-mgmt/
```

**与本次任务直接相关的已有研究（不重复整理）：**

| 文件 | 行数 | 已覆盖 | 本次任务怎么用 |
|---|---|---|---|
| `standard-product/dao-and-mybatis.md` | 205 | `AllInOneBaseDao` 41 方法、22 Mapper、10 方言 | **任务三基础**，只补缺失部分 |
| `standard-product/dubbo-cross-service.md` | 166 | `DubboFactory` 5 重载、`AppServiceProxy` 3 形态、灰度 | **任务一基础**，补清单与泛化全链 |
| `standard-product/autocode-project-templates.md` | 194 | 模板清单、`ServiceService` 命名规则 | **任务二基础**，补生成规则 |
| `standard-product/boot-core-utils-and-annotations.md` | 176 | JsonUtils 28 / DateUtils 61 / StringUtils 35 | **任务五基础** |
| `standard-product/appservice-invocation.md` | 163 | AppService 调用方式 | 任务一引用 |
| `standard-product/extension-point-decision-table.md` | 181 | 扩展点决策 | 任务一引用 |
| `udc/expression/engine.md` | 421 | 表达式引擎 | **任务四基础** |
| `udc/microflow/write-node-runtime-gap.md` | 282 | `executeExpression*` 覆盖坑 | **任务四关键证据** |
| `udc/microflow/node-insert-entity.md` | 106 | `preCreateBatch` + G34/G35 闸门 | **任务三关键证据** |

### 1.2 结构化数据资产

| 资产 | 规模 | 内容 | 本次用途 |
|---|---|---|---|
| `docs/audit/signatures.txt.gz` | 21389 类 / 224320 方法 | javap 全量签名 | 一切方法签名的权威源 |
| `docs/audit/reference/surface-index.tar.gz` | 8 MB / 100+ 文件 | domains 11 / action-index 682 / dto-meta 1305 / impl-map 269 / consumers 183 | **任务一、六主战场** |
| `docs/audit/reference/udc-platform-5.3.517.tar.gz` | 404 条目 | 255 javap + 87 json + **`_codegen_templates.json`** | **任务二核心** |
| `docs/audit/reference/svc-app-service.txt.gz` | 10176 行 | AppService → jar 映射 | 任务一 |
| `docs/audit/modules/decompiled/` | 212 .java | bpm-addsign 92 / ctp-user 36 | 任务一真实调用示例 |

### 1.3 ★ 关键发现：`_codegen_templates.json`

这是本次研究最重要的单点资产，**证明生成器存在且模板可枚举**：

```json
{
  "2.7/entity": [
    "appservice.java.ftl",        ← AppService 层
    "appserviceImpl.java.ftl",
    "baseservice.java.ftl",       ← Service 层
    "controller.java.ftl",        ← Controller 层
    "dao.java.ftl",               ← DAO 层
    "dto.java.ftl",
    "entity.java.ftl",
    "mybatis.xml.ftl",            ← Mapper XML
    "pageEntityController.java.ftl",
    "pagecontroller.java.ftl",
    "third/third_appservice.java.ftl",
    "tree/tree-entity-refer-controller.ftl"
  ],
  "2.7/common": [
    "macro-entity-update.ftl",
    "macro-entity-check.ftl",
    "macro-entity-attribute-check-not-null.ftl",
    "macro-entity-trim.ftl",
    "macro-formula-entity.ftl",    ← 表达式与实体结合
    "macro-appservice-approval.ftl" ← 单据审批相关
  ],
  "2.7/entityrule": [
    "AssignValueActivity.ftl", "AttributeRequiredActivity.ftl",
    "AttributeUniqueActivity.ftl", "DefaultValueActivity.ftl",
    "ShowMessageActivity.ftl", "SetValueUtil.ftl"
  ],
  "2.7/microflow": [ 29 个 Activity 模板 ],
  "2.7/event": [ 4 个事件模板 ],
  "2.7/feature/tree_entity": [ 10 个树形实体模板 ]
}
```

**这解决了任务二最关键的问题：三层生成物的模板名与职责边界可枚举。**
`macro-entity-update.ftl` / `macro-formula-entity.ftl` 直接指向「更新逻辑」和「表达式与实体」的生成规则。

### 1.4 生成器入口（已定位，待深挖）

从 `udc-biz-5.3.517/EntityRuleTask.javap.txt` 逐字读到：

```java
public class com.seeyon.udc.autocode.task.EntityRuleTask
    extends com.seeyon.udc.autocode.task.AbstractMicroFlowCodeTask
    implements com.seeyon.udc.common.autocode.CodeTask {

    public boolean matches(CodeContext, ApplicationContext);
    public String code(CodeContext) throws Exception;
    private void generateAggregateRootEntityRule(...);   ← 聚合根（主子表关键）
    private void generateRootEntityRuleCode(...);
    private LinkedHashMap<Long, List<EntityDto>> getEntityRule(...);
}
```

**⇒ 生成器契约是 `com.seeyon.udc.common.autocode.CodeTask`，入口方法 `code(CodeContext)`。**
`generateAggregateRootEntityRule` 是**主子表聚合根的生成入口**，这正是任务三 B 的核心线索。

### 1.5 明确不存在的东西

```
❌ 平台 jar 本体（0 个 .jar）
❌ .ftl 模板内容（0 个文件，只有清单）
❌ autocode Java 源码（只有 EntityRuleTask / EntityService / MicroflowNodeParserFactory 3 个 javap）
❌ CFR 反编译工具（本机无）
❌ Service/DAO 完整生成产物（只有签名，无源码）
```

---

## 二、研究地图（六任务 × 证据源 × 可达等级）

### 任务一：标品接口体系

**证据源：**
```
surface-index.tar.gz
  ├── domains/*.md              11 域，含「用途」行 + 接口清单
  ├── impl-map.json             269 接口 → 实现类 + jar
  ├── consumers.json            183 接口 → 谁在调用（12252 类扫描）
  └── packages/*.md             100+ 构件包清单
signatures.txt.gz               AppService 1000 个 / 方法 10760
svc-app-service.txt.gz          AppService → jar
docs/audit/modules/decompiled/  212 .java 真实调用示例
core/facts/standard-product/dubbo-cross-service.md  已有 Dubbo 结论
```

**待研究（现有 facts 未覆盖）：**

| 项 | 现状 | 方法 |
|---|---|---|
| 接口完整清单（按域） | domains 有 11 域，但只有「关键类」 | 从 signatures 全量提取 1000 个 AppService，按包分组 |
| @Autowired 可注入 vs Dubbo 取代理的判定 | 有 `DubboFactory.getProxy` 结论，**没说什么情况直接注入** | 从 consumers.json 反查真实注入点 |
| 泛化调用完整链路 | 只有 `AppServiceProxy` 签名 | 追 `AppServiceInvokeDto` 18 字段 + `GenericInvocationAuthService` |
| 公开/内部/扩展接口三分类 | ❌ 无 | 按包路径 + `@AppServiceOperation` 注解 + impl-map 的 jar 归属判定 |
| 权限/异常/事务机制 | 分散 | 从 `boot-starter-security` / `transaction` 包提取 |

**可达等级：** `VERIFIED_STATIC_BYTECODE`（签名 + 调用者关系）
**不可达：** 真实业务调用示例（除非 decompiled 里恰好有）

---

### 任务二：实体与代码生成体系 ★核心

**证据源：**
```
udc-platform-5.3.517.tar.gz
  ├── udc-biz-5.3.517/_codegen_templates.json    ★ 模板清单
  ├── udc-biz-5.3.517/EntityRuleTask.javap.txt   ★ 生成器入口
  └── udc-biz-5.3.517/_UDC-BIZ-PANORAMA.md
core/facts/udc/entity/*.md                       10 个实体 facts
core/facts/udc/entity/evidence/entity-write-2026-10-23/stereotype-authoritative.json
core/facts/standard-product/autocode-project-templates.md
signatures.txt.gz                                179 个实体 Service 接口 / 4309 方法
```

**六种实体类型（已核实，逐字来自 stereotype-authoritative.json）：**

```json
standard    标准      basic
form        表单      basic + formBasic
basicData   基础资料   basic
bill        单据      basic + approve + organization + billBasic + termination + suspend + nullify
archive     平铺档案   basic + archiveBasic + approve + archiveTiled
archiveTree 树形档案   basic + archiveBasic + approve + treeEntity
```

**待研究：**

| 项 | 方法 | 可达等级 |
|---|---|---|
| 每个实体生成哪些类 | 从 `_codegen_templates.json` 的 `2.7/entity` 12 个模板反推 | STATIC_RULE |
| 生成代码包路径/命名 | 从 `autocode-project-templates.md` 的 `${appServicePackage}` 变量 + 实测一次生成 | STATIC_RULE → 需实测升 LIVE |
| 三层职责与接口实现关系 | 179 个 Service 接口签名 + impl-map | VERIFIED_STATIC_BYTECODE |
| 方法生成规则 | **需模板源码，当前 BLOCKED** | BLOCKED |
| 实体↔表映射 | `entity.java.ftl` + `mybatis.xml.ftl` 清单 → 需实测 DDL | STATIC_RULE |
| 主子表实体关系 | `generateAggregateRootEntityRule` + `feature/tree_entity` 模板 | STATIC_RULE |
| 生成入口 | `CodeTask.code(CodeContext)` 已定位；**谁触发**未验 | STATIC_RULE |

**★ 阻塞点：模板内容（.ftl）不存在 → 「方法生成规则」这一条无法做到源码级。**

---

### 任务三：DAO 数据持久化 ★优先级最高

**证据源：**
```
core/facts/standard-product/dao-and-mybatis.md          ★ 已有 205 行，覆盖 41 方法 + 22 Mapper
core/facts/udc/microflow/node-insert-entity.md          ★ preCreateBatch + G34/G35
core/facts/udc/microflow/write-node-runtime-gap.md      ★ executeExpression 覆盖坑
signatures.txt.gz                                       AllInOneBaseDao 41 方法可逐字核
udc-biz-5.3.517/EntityService.javap.txt                 实体领域服务
```

**已确认可用（不重写）：**
```
AllInOneBaseDao<T> 41 方法
  写: create / createBatch / update / updateBatch / updateColumns / deleteById / deleteByIds / deleteByConditions...
  读: selectById / selectByIds / selectOneByCondition / selectListByCondition(s) / selectPageByCondition(s)...
  条件三档: ByCondition(s) → ByComplexConditions(LinkedHashMap) → ByDynamicConditions(SeeyonCondition)
  ★ 返回 PageData<T>，不是 transport 的 PageResponse
BaseMybatisDao<T> = 22 个 Mapper 组合
10 种数据库方言
```

**待研究（A/B/C/D 四项）：**

| 项 | 现状 | 方法 | 可达等级 |
|---|---|---|---|
| **A 普通实体 CRUD** | 41 方法有，**主键生成机制无** | 追 `IdentifierGenerator` + `entity.java.ftl` 清单 | VERIFIED_STATIC_BYTECODE |
| **B 主子表** | ❌ **完全空白**（`grep 主子表 core/facts` = 0） | `generateAggregateRootEntityRule` + `macro-entity-update.ftl` + 实测 | 需实测升 LIVE |
| **C 单据** | 只有 stereotype 特性定义 | `macro-appservice-approval.ftl` + `BpmAppService` 关联 | 需实测 |
| **D 查询** | 41 方法有，**XML 生成规则无** | `mybatis.xml.ftl` 清单 + 实测生成产物 | STATIC_RULE |

**★ 这是本次最值得投入的专题。** 用户实测踩过：
- 判重拉全表 → 重复 5 万行（`ListRequest.from()` 空参）
- `pageSize=100` → 604 次全量 COUNT
- 异步丢租户上下文

**这些是「不知道平台正确姿势」的直接后果，必须固化成事实。**

---

### 任务四：表达式执行机制

**证据源：**
```
core/facts/udc/expression/engine.md           421 行（design-time 编译）
core/facts/udc/expression/functions.md        800 行（88 函数）
core/facts/udc/expression/README.md           481 行
core/facts/udc/expression/system-variables.md 189 行
core/facts/udc/microflow/write-node-runtime-gap.md:215-245   ★ runtime 执行
```

**已确认的两条路：**

```
design-time:  /service/udc/expression/check → /transform → executableExpr
              "93gD...=dateToString%28addDay%28currentDate%28%29%2C-7%29%2C%27yyyy-MM-dd%27%29"

runtime:      平台生成 executeExpression<实体名>(list, requireNull, getter, expFn, setter, null)
              实体 Service 的 preCreateBatch 自动调用
              ★ requireNull=false → 无条件覆盖传入值（实测坑）
```

**待研究：**

| 项 | 方法 | 可达等级 |
|---|---|---|
| 表达式定义与注册 | `functions.md` 88 函数 + `system-variables.md` 131 变量 | VERIFIED_STATIC_BYTECODE |
| 解析链路 | `engine.md` 已有 | VERIFIED_STATIC_BYTECODE |
| **Java 侧主动执行入口** | ❌ **无**。只有被动 `preCreateBatch` | 需查 `boot-formula-engine` 包 |
| 上下文构建 | 部分（`expressionMap`） | STATIC_RULE |
| 实体字段访问 | `executeExpression*` 的 getter/setter 反射 | VERIFIED_STATIC_BYTECODE |
| 自定义表达式扩展 | ❌ 无 | 查 `boot-starter-formula` 扩展点 |

**★ 关键缺口：** 现在只知道「平台在 preCreateBatch 里自动执行」，
**不知道怎么在业务代码里主动执行一个表达式**。这是任务四要补的核心。

---

### 任务五：基础组件能力

**证据源：**
```
core/facts/standard-product/boot-core-utils-and-annotations.md   176 行（已有）
components/construction/platform_class_index.py                  ★ 已建索引 2669 类 / 26235 方法
signatures.txt.gz                                                821 个工具类
```

**已建成（本会话刚做）：**
```
platform_class_search     2669 类 / 26235 方法，中文可查
  日期 → DateUtils(61) / DateTransformUtil(19)
  JSON → JsonNodeUtil(56) / JsonUtils(28) / JsonUtil(20)
  缓存 → UserCacheUtils(125) / OrgCacheUtils(47)
  文件 → FileUtils(72) / ExcelTemplateUtil(70)
  HTTP → HttpClientUtil(93)
```

**待补：每个类的「什么情况该用/不该用」**

| 类 | 已有什么 | 缺什么 |
|---|---|---|
| `JsonUtils` | 28 方法签名 | `toMap` vs `toMapThrowError` 差异；与 `license.JsonUtils` 同名坑 |
| `DateUtils` | 61 方法签名 | 与表达式 `dateToString` 的选择边界 |
| `StorageService` | 三桶（public/private/temp） | 附件关联到业务实体的正确姿势 |
| `OrgCommonAppService` | 40 方法 | 「查人」的推荐路径 vs 备选 |
| `BpmAppService` | 22 方法 | send vs submit vs start 的边界 |
| `ExcelTemplateUtil` | 70 方法 | 与平台「导入导出模板」的关系 |
| `HttpClientUtil` | 93 方法 | **平台已有 HTTP 工具，但微流程无 HTTP 节点** |

**可达等级：** `VERIFIED_STATIC_BYTECODE` + 部分 `LIVE`（已有实测调用点）

---

### 任务六：业务开发知识关联

**这是最终交付形态。** 已有基础：

```
components/construction/business_code_bridge.py   ★ 本会话已建
  业务意图 → 域 → 动作 → 方法 → DTO(中文字段) → 实现类 → 调用者
components/construction/platform_class_index.py   2669 类中文检索
components/construction/business_action_index.py  业务词 → 标品能力
```

**10 个场景的当前覆盖：**

| # | 场景 | 现状 | 缺什么 |
|---|---|---|---|
| 1 | 普通实体 CRUD | 方法有，**方案无** | DAO 调用顺序、主键、事务 |
| 2 | 主子表 CRUD | ❌ **空白** | 全部（任务三 B） |
| 3 | 单据新增/修改 | ❌ 空白 | 单据写入机制 |
| 4 | 单据提交/流转 | 部分（`BpmAppService.send`） | 与实体 create 的关系 |
| 5 | 附件上传关联 | 部分（`StorageService`） | 关联到实体的正确姿势 |
| 6 | 组织人员查询 | ✅ `OrgCommonAppService` 已能查到 | 推荐路径 |
| 7 | 表达式执行 | 部分（design-time 有，runtime 主动执行无） | 任务四缺口 |
| 8 | Dubbo 调用 | ✅ `DubboFactory` 已记录 | 什么时候该用它 vs 直接注入 |
| 9 | 泛化调用 | 签名有，链路无 | 任务一 |
| 10 | 第三方接口集成 | ✅ 用户复盘文档有实测 | 固化进 facts |

---

## 三、实施顺序（按「证据可得性 × 用户痛点」排）

```
阶段 1（纯离线，零阻塞，先做）
  ├── 专题 3-B  主子表持久化        ← 完全空白 + 用户最痛
  ├── 专题 4    表达式 runtime 执行  ← 有明确缺口
  └── 专题 1    接口三分类 + 泛化链  ← 数据全在

阶段 2（需实测，动 test2）
  ├── 专题 3-A  普通实体 CRUD 主键
  ├── 专题 3-C  单据写入机制
  └── 专题 3-D  Mapper XML 生成

阶段 3（需补资产或降级）
  └── 专题 2    生成器方法规则      ← 模板源码 BLOCKED

阶段 4（汇总）
  ├── 专题 5    基础组件使用边界
  └── 专题 6    业务场景知识库
```

**理由：** 阶段 1 三块都能用现有签名 + 清单级证据得出结论，不需要动环境，
且正好覆盖用户实测踩坑最深的两个点（主子表、表达式覆盖）。

---

## 四、每个专题的产出格式（统一）

所有事实必须能被 Agent 检索，不是给人读的散文。统一结构：

```markdown
# 专题名

## 1. 结论（Agent 直接读这段）
| 场景 | 该调什么 | 证据等级 |

## 2. 机制
（调用链，每步标类名#方法名）

## 3. 真实代码示例
（可复制，含 import）

## 4. 边界与陷阱
（什么情况不能用）

## 5. 证据
- 文件路径 + 行号
- 签名库命中行（逐字）
- 实测响应体（LIVE 时）

## 6. 未解决
| 项 | 为什么没解决 | 需要什么 |
```

**证据等级统一用：**
```
STATIC_RULE            源码/模板/配置静态确认
VERIFIED_RULE          调用链/测试/字节码验证
LIVE_RULE              实际运行验证
UNVERIFIED / BLOCKED   证据不足
```

---

## 五、交付物清单（12 项）与可达性

| # | 交付物 | 可达 | 阻塞 |
|---|---|---|---|
| 1 | 平台开发体系总览 | ✅ | — |
| 2 | 标品接口知识库 | ✅ | — |
| 3 | 实体类型与生成机制 | ⚠️ | 模板源码无 → 降级到清单级 |
| 4 | AppService/Service/DAO 生成规范 | ⚠️ | 同上 |
| 5 | DAO 持久化专题 | ✅ | B/C 需实测 |
| 6 | 表达式机制专题 | ⚠️ | runtime 主动执行入口待查 |
| 7 | 基础组件使用知识库 | ✅ | — |
| 8 | 业务开发场景知识库 | ✅ | 依赖 5/6 |
| 9 | 类/方法/DTO/业务关联索引 | ✅ | 已有 business_code_bridge 基础 |
| 10 | 证据与未解决问题清单 | ✅ | — |
| 11 | Agent 检索与使用规范 | ✅ | — |
| 12 | 实战验证报告（3 场景盲测） | ✅ | 依赖前面 |

---

## 六、需要你确认的 4 个问题

**Q1. 模板源码缺失怎么办？**
任务二要求「必须检查生成器源码、模板和实际生成结果」，但仓库 0 个 .ftl。
- A：降级到「模板清单级」证据，标 BLOCKED，继续推进
- B：先补资产（拉 udc-biz jar + 装 CFR），再研究
- C：你有 jar 路径，我直接取

**Q2. 任务三 B/C（主子表、单据）必须实测吗？**
纯静态只能知道「方法存在」，不知道「调用顺序、外键回填时机」。
- A：允许在 test2 建测试实体实测（**测完清理**）
- B：只做静态，标 UNVERIFIED

**Q3. 优先级是否按我的排法？**
我建议先做 3-B（主子表）→ 4（表达式）→ 1（接口分类），理由：完全空白 + 用户最痛 + 纯离线。

**Q4. 盲测用哪三个场景？**
建议：主子表 CRUD / 单据提交流转 / 第三方接口集成（对应你复盘文档里真实踩过的坑）。

---

## 七、本阶段不做的事（对齐你的禁止事项）

- ❌ 不写新业务功能
- ❌ 不重复整理已有 228 个 facts（只补缺失）
- ❌ 不把签名索引当使用文档（每个结论必须配场景和边界）
- ❌ 不把实现类当可用接口（`*Impl` 一律标注「内部」）
- ❌ 不以 Controller 为主要方向（只作参考，标「自己写」）
- ❌ 不改现有 Agent 架构/工具注册（本阶段只产文档，不动代码）
- ❌ 不覆盖现有研究（新文件独立命名，旧文件只增不删）

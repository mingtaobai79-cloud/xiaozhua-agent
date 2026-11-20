# 平台能力事实补全计划（Dubbo / 实体生成物 / 基础组件）

**目标：** 让 LLM 在写扩展代码前，能查到「平台已经替我做了什么、我该在哪一层写、调哪个方法」，
而不是自己重写一遍标品已有能力。

**背景：** 现有 facts 覆盖了 DAO 层（`AllInOneBaseDao` 41 方法）、Dubbo 注入（`DubboFactory`）、
autocode 模板骨架，但**三块内容彼此割裂**，且用户实测中反复踩的坑（主子表写入、单据入数据、
表达式执行、平台生成方法适用范围）**没有统一入口**。

---

## 一、现状核查（已完成，非推测）

### 1.1 已有事实（可直接复用，不重写）

| 文件 | 行数 | 覆盖内容 |
|---|---|---|
| `core/facts/standard-product/dao-and-mybatis.md` | 205 | `AllInOneBaseDao` 41 方法、22 个 Mapper、10 种方言、横切拦截器 |
| `core/facts/standard-product/dubbo-cross-service.md` | 166 | `DubboFactory` 5 重载、`AppServiceProxy` 3 形态、灰度上下文 |
| `core/facts/standard-product/autocode-project-templates.md` | 194 | autocode 模板清单（entity 14 / microflow 29 / entityrule 8） |
| `core/facts/standard-product/boot-core-utils-and-annotations.md` | 176 | 工具类实测方法数（JsonUtils 28 / DateUtils 61 / StringUtils 35） |
| `core/facts/udc/microflow/node-insert-entity.md` | — | `preCreateBatch` 执行默认值表达式、G34/G35 闸门 |

### 1.2 已核实的实测数据

**实体生成的 Service 接口：179 个**（签名库 `udc.*.api/service.*Service`），
方法名前缀分布：

```
select 786 / delete 231 / create 192 / update 147 / check 145
batch 19 / pre 5 / post 2 / execute 2 / validate 1
```

代表接口（真实方法名，非推测）：

```
AttributeSetAppService       13 方法  create/createBatch/deleteById/deleteByIds/update/selectById...
DataTransferObjectAppService 22 方法  create/createDtoWithAttrs/updateDtoWithAttrs/createDtoWithAttrsAndRefDtos...
DtoAttributeAppService        8 方法  create/createBatch/update/deleteById/selectPageByConditions...
```

**平台按实体生成默认值表达式方法**，命名规则：

```java
executeExpressionYsFull6956(list, false, YsFull6956Dto::getF05dec,
                            this::exp9056335983934914588, YsFull6956Dto::setF05dec, null);
```
`executeExpression<实体名>` + `exp<雪花ID>`，第二参数 `requireNull`：
- `true` → 只在字段为 null 时填
- `false` → **无条件覆盖传入值**（实测坑，导致实体永远插不进数据）

**Dubbo 泛化调用入口（实测类名）：**

```
AppServiceProxy#invokeAppService / invokeAppServiceForList / invokeAppServiceForPage
              #reliableInvokeAppService（可靠投递）
AppServiceInvokeDto（18 字段）
GenericInvocationAuthService#invokeAppService(String, String, ...)
DubboFactory#getProxy(Class[, group[, version[, timeout]]])  5 重载
```

### 1.3 三块的真实缺口（这是本计划要补的）

| 缺口 | 现状 | 影响 |
|---|---|---|
| **主子表怎么入数据** | `grep 主子表 core/facts` → **0 命中** | 明细表场景只能靠猜 |
| **单据（bill）怎么入数据** | 只有 `node-data-flow.md:213` 一句「写入形态未验」 | 单据类实体写入无权威路径 |
| **三层 Service 的职责边界** | 分散在 autocode 文档，无对照表 | 不知道逻辑写哪层 |
| **平台生成方法的适用场景** | 179 接口 4309 方法无场景标注 | 看到 `createDtoWithAttrs` 不知道何时用 |
| **表达式在 Java 侧怎么执行** | 只有 `executeExpression*` 片段 | 想主动执行表达式无从下手 |
| **大数据量入数据** | 无 | 6 万条同步场景反复踩坑（用户文档已记录） |

---

## 二、要建的东西

### 2.1 核心产物：一份「分层能力事实表」

新建 `core/facts/standard-product/entity-layer-capabilities.md`，结构：

```
一、三层 Service 职责对照（谁调谁、写哪层）
    ├─ Controller（web 层，自己写）
    ├─ AppService（facade，对外/微流程可调，@AppServiceOperation）
    ├─ Service（business，业务逻辑，平台生成骨架+人填实现）
    └─ Dao（数据层，AllInOneBaseDao<T> 41 方法）
二、实体生成物清单（一个实体生成什么类）
三、写入路径：单条 / 批量 / 主子表 / 单据
四、平台生成的横切方法（preCreateBatch / postCreate / executeExpression*）
五、表达式执行（design-time 与 runtime 两条路）
六、大数据量写入（分片、幂等、异步）
七、平台方法适用场景速查表
```

### 2.2 索引侧：给 179 个实体 Service 接口打场景标签

新建 `components/construction/entity_capability_index.py`：
- 输入业务意图（「插入一条主子表数据」「批量更新」「执行字段表达式」）
- 输出：该调哪个接口的哪个方法 + 方法签名 + 适用场景 + 陷阱

---

## 三、分阶段任务

### 阶段 A：补齐事实（不改代码，只写文档 + 验证）

#### Task A1：核实主子表写入的真实机制

**Objective:** 确认平台对「主子表」实体的写入 API 形态，不猜。

**Files:**
- Read: `core/facts/standard-product/standard-product-appservice-surfaces.md`
- Read: `core/facts/udc/entity/attribute-create.md`（relationEntity / multiSelect 字段定义）
- Create: `docs/audit/entity-master-detail-write-evidence.md`

**Step 1:** 从签名库找带 `relationEntity` 的 DTO 写入方法

```bash
cd C:/Users/白明涛/xiaozhua-agent
./.venv/Scripts/python.exe -c "
import gzip, re
lines = gzip.open('docs/audit/signatures.txt.gz','rt',encoding='utf-8',errors='replace').read().splitlines()
for l in lines:
    if re.search(r'(Detail|Sub|Item|Line).*AppService#', l) and 'create' in l.lower():
        print(l[:160])
" | head -30
```

**Step 2:** 在 test2 环境建一个带子表的实体，实测 create 调用形态
（用户已授权 test2 可建测试数据，**测完必须清理**）

**Step 3:** 记录结论到 evidence 文档，标明 `VERIFIED_STATIC_BYTECODE` 或 `LIVE`

**验收：** 文档里每条结论都有签名库行号或实测响应体作为证据。

---

#### Task A2：核实单据（bill）实体的写入路径

**Objective:** 确认 bill 类型（带 approve/termination/suspend/nullify 特性）的实体，
写入时是否有额外步骤（如必须先建草稿再提交）。

**Files:**
- Read: `core/facts/udc/entity/evidence/entity-write-2026-10-23/stereotype-authoritative.json`
- Create: `docs/audit/entity-bill-write-evidence.md`

**已知事实（stereotype-authoritative.json 逐字）：**

```json
{"name": "bill", "caption": "单据",
 "necessaryFeatures": ["basic","approve","organization","billBasic",
                       "termination","suspend","nullify"]}
```

**Step 1:** 从 179 个实体 Service 接口里筛出 bill 类实体的（看是否有 submit/approve 相关方法）

**Step 2:** 对照 `BpmAppService.send/submit`（已确认存在）与实体 create 的关系

**Step 3:** 结论写入文档；拿不到实测就标 `UNVERIFIED`，**不许编**

---

#### Task A3：整理三层 Service 职责对照表

**Objective:** 给出「这段逻辑该写在哪层」的判定规则。

**Files:**
- Read: `core/facts/standard-product/autocode-project-templates.md:109-170`
- Create: `core/facts/standard-product/entity-layer-capabilities.md`（§一）

**内容（基于已核实事实）：**

| 层 | 包 | 平台生成 | 可写 | 典型用途 |
|---|---|---|---|---|
| Controller | `custom.web` / `*.controller` | 微流程有模板，普通业务**自己写** | ✅ | HTTP 入口、参数校验 |
| AppService | `api.*` / `${appServicePackage}` | 有（含 `@AppServiceOperation`） | ❌ 接口不可改 | 对外暴露、微流程「自定义服务」节点可调 |
| Service | `custom.service.microflow` | 有（`<Xxx>ServiceService`） | ✅ 实现 | 业务逻辑主体 |
| Dao | `*.dao` | entity 模板生成 | ✅ 可扩展 | 数据访问，`AllInOneBaseDao<T>` |

**关键规则（来自实测）：**
- 自定义微流程必须 `implements <Xxx>ServiceService`（`custom.service.microflow` 包）
- 方法签名是**裸 DTO 进出**，不包 `SingleRequest`/`SingleResponse`
- 写错这三个（包名/后缀/包装）→ 编译过但运行时 `UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED`

---

#### Task A4：平台生成方法适用场景速查表

**Objective:** 给 179 个实体 Service 接口的常用方法打场景标签。

**Files:**
- Create: `components/construction/entity_capability_index.py`
- Test: `tests/test_entity_capability_index.py`

**场景 → 方法映射（初版，基于实测方法名）：**

| 场景 | 该调 | 说明 |
|---|---|---|
| 单条新增 | `create(Dto)` | 触发 `preCreateBatch` 默认值表达式 |
| 批量新增 | `createBatch(List<Dto>)` | 同上，逐条执行表达式 |
| 带子对象新增 | `createDtoWithAttrsAndRefDtos` | 主+子一次写 |
| 按条件查 | `selectListByConditions(Map, Sort)` | 简单 map |
| 复杂条件查 | `selectListByComplexConditions(LinkedHashMap, Sort)` | 保序，and/or |
| 动态条件查 | `selectListByDynamicConditions(List<SeeyonCondition>, Sort)` | 最灵活 |
| 分页 | `selectPageByConditions(PageInfo, Map, Sort)` | 返回 `PageData<T>` |
| 单条更新 | `update(Dto)` | 带版本号 |
| 指定列更新 | `updateColumns(Dto, Set<String>)` | 只更新给定列 |
| 批量更新 | `updateBatch(List<Dto>)` | |
| 删除 | `deleteById` / `deleteByIds` / `deleteByConditions` | |
| 聚合 | `selectListFuncByComplexConditions(...)` | count/sum，返回 String |

**Step 1:** 写测试断言每个场景能查到正确方法

```python
def test_master_detail_write_finds_ref_dto_method():
    r = entity_capability_search("主子表新增")
    assert any("createDtoWithAttrsAndRefDtos" in str(h) for h in r["hits"])
```

**Step 2:** 跑测试确认失败（方法不存在）

**Step 3:** 实现 `entity_capability_index.py`

**Step 4:** 跑测试确认通过

**Step 5:** 提交

---

#### Task A5：表达式执行两条路

**Objective:** 说清 design-time（GraphQL 编译）与 runtime（Java 内执行）的区别。

**Files:**
- Read: `core/facts/udc/expression/engine.md`
- Read: `core/facts/udc/microflow/write-node-runtime-gap.md:215-245`
- Create: `core/facts/standard-product/entity-layer-capabilities.md`（§五）

**已核实内容：**

```
design-time: /service/udc/expression/check → /transform → executableExpr
             返回形如 93gD...=dateToString%28addDay%28currentDate%28%29...
runtime:     平台生成的 executeExpression<实体名>(list, requireNull, getter, expFn, setter, null)
             实体 Service 的 preCreateBatch 自动调用
★ requireNull=false → 无条件覆盖传入值（实测坑）
```

**关键结论：** 想主动执行表达式，需要先 design-time 编译拿到 `executableExpr`，
再在 Java 侧找对应的 `exp<雪花ID>` 方法；**不能直接传表达式字符串**。

---

#### Task A6：大数据量写入

**Objective:** 把用户实测踩坑（6 万条、604 次 COUNT、重复 5 万行）固化成事实。

**Files:**
- Create: `core/facts/standard-product/entity-layer-capabilities.md`（§六）
- 来源：用户文档 `自定义微流程对接外部接口-问题复盘.md` §9、§10

**内容：**

```
① 分页 pageSize 默认 2000（不是 100）
② 幂等写入用条件精确查询，禁止 ListRequest.from() 空参拉全表
③ 长任务异步 + taskKey + 分布式锁 + 锁续约（40s/120s）
④ 异步线程必须带 userId/tenantId
⑤ 状态由真正干活的方法回写，监听器只兜底
```

**每条都要标证据等级**：`LIVE`（实测过）或 `UNVERIFIED`（未验）。

---

### 阶段 B：接入 MCP（阶段 A 完成后）

#### Task B1：新增 `entity_capability_search` 工具

**Files:**
- Modify: `xiaozhua_host_bootstrap.py`（加函数 + 注册）
- Modify: `adapters/mcp/server.py`（TOOL_KEYS + 名称映射 + 说明）
- Modify: `tools/gen_mcp_manifest.py`（DOMAIN_OF）
- Modify: `tests/test_mcp_tools_smoke.py`（CASES）
- Modify: `docs/delivery/tool-status.json`

**工具签名：**

```python
def entity_capability_search(scenario: str = "", entity_type: str = "",
                             layer: str = "", limit: int = 15) -> dict:
    """按场景查实体层能力。
    scenario: 主子表新增 / 批量更新 / 分页查询 / 执行表达式 ...
    entity_type: standard/form/basicData/bill/archive/archiveTree
    layer: controller/appservice/service/dao
    """
```

**验收：** 跑通 6 个场景查询，每个都返回正确方法名 + 签名 + 场景说明。

---

#### Task B2：把三块接入 `business_plan` 的组装提示词

**Files:**
- Modify: `components/construction/host_llm_prompt.py`
- Modify: `components/construction/business_plan.py`

**目标：** 计划阶段就提醒「这块平台已有预制，别自己写」。

---

## 四、验证方式

每个 Task 完成后必须跑：

```bash
cd C:/Users/白明涛/xiaozhua-agent
./.venv/Scripts/python.exe -m pytest tests/ -q
```

全绿才算完成。新加的测试文件单独跑：

```bash
./.venv/Scripts/python.exe tests/test_entity_capability_index.py
```

---

## 五、风险与边界

### 5.1 明确不做

- **不改标品源码**（只读 jar）
- **不重建已有 facts**（dao-and-mybatis / dubbo-cross-service 已够用，只引用不重写）
- **不臆造方法名**（所有结论必须能在签名库 `signatures.txt.gz` 里逐字命中）
- **test2 测试数据必须清理**（用户明确要求）

### 5.2 已知不确定项（必须标 UNVERIFIED）

| 项 | 为什么不确定 |
|---|---|
| 主子表实际写入 API | 需实测，签名库只能看到方法存在 |
| bill 实体的完整写入流程 | 是否必须走 BPM 提交，未验 |
| `createDtoWithAttrsAndRefDtos` 的子对象结构 | 字段含义需实测 |
| 大数据量分片阈值 | 平台是否有硬限制，未验 |

### 5.3 与用户此前反馈的对齐

| 用户原话 | 本计划的落点 |
|---|---|
| 「dao 层用的也多」 | Task A3 三层对照 + Task A4 场景速查，Dao 41 方法单列 |
| 「web 层是自己写的，而不是查看标品的」 | Task A3 明确 Controller 层由人写，不进标品索引 |
| 「标品的 dubbo 接口、authod 类的接口、泛化的接口」 | Task A3 §一 + §二引用 dubbo-cross-service，补泛化调用入口 |
| 「业务应用实体生成的东西，实体的能力」 | Task A1/A2/A4 |
| 「基础组件的类的方法」 | 复用 boot-core-utils-and-annotations + platform_class_index（已建） |
| 「主子表怎么入数据，单据怎么入数据」 | Task A1/A2 |
| 「怎么执行表达式」 | Task A5 |
| 「平台生成的那些方法都适用什么地方」 | Task A4 场景速查表 |
| 「数据接口大数据怎么入」 | Task A6 |

---

## 六、执行顺序建议

```
A1 主子表  ┐
A2 单据    ├─ 可并行（都是查证 + 写文档）
A5 表达式  ┘
    ↓
A3 三层对照（依赖 A1/A2 结论）
    ↓
A4 场景索引（依赖 A3）
    ↓
A6 大数据（独立，可随时插入）
    ↓
B1 MCP 工具
    ↓
B2 接入提示词
```

**建议先做 A1 + A5**：这两块是用户实测踩坑最深的（主子表完全空白、表达式覆盖坑导致实体插不进数据），
且都能纯离线查证，不需要动 test2 环境。

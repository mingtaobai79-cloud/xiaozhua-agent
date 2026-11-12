# P1 验收报告（第一轮：RETRIEVE / CHANGE_VARIABLE / L2）

> 2026-10-31。范围：P1-1 矩阵修正、P1-2 RETRIEVE、P1-3 CHANGE_VARIABLE、P1-5 L2。
> P1-4（MAP_OPERATION / DATA_MAPPING / CREATE_MAP / FOR）未开始。构建（BUILD）与运行（RUNTIME）维度仍缺证据。

## 一、P1-1 矩阵修正

**计数修正**：26 类 = 15 VERIFIED（含结构节点 CONDITION）+ 9 CONSTRUCTED + 1 BLOCKED + 1 UNSUPPORTED = 26 ✓
（此前正文写 14，漏数了 CONDITION；能力矩阵已同步改。）

**状态五级化**（替代单一 VERIFIED）：

| 维度 | 判据 | 本轮状态 |
|---|---|---|
| CONSTRUCTED | 本地闸门通过 | 全部可构造节点 |
| SCHEMA_VERIFIED | 发布 checkSchema errors=0 | RETRIEVE×3 形态、CHANGE_VARIABLE×2 形态 ✓ |
| UI_VERIFIED | prove（isCompleted 全 true + 检测无本流程项） | 同上 ✓ |
| BUILD_VERIFIED | backBuild.log BUILD SUCCESS | **缺**（等构建放行，全程未编译） |
| RUNTIME_VERIFIED | 真实执行业务结果正确 | **缺** |

**覆盖三口径**（修正后的真实数字）：

| 口径 | 数值 | 说明 |
|---|---|---|
| 节点类别覆盖 | 16/26 = 62%（含结构 CONDITION 17/26 = 65%） | 从 54% 上来 |
| 实例加权覆盖 | **97.8%**（含 CONDITION）/ 72.9%（不含） | 未验实例仅 172/7937 |
| 业务组合覆盖 | 12/12 已验收流程含 ≥2 类节点组合 | 全部是多节点组合流 |

**结论**：类别口径下最刺眼的两个窟窿（RETRIEVE 639 样本、CHANGE_VARIABLE 1053 样本）本轮已填上；
剩余未验实例集中在 CHANGE_BATCH_ENTITY(41)/FOR(32)/CREATE_ENTITY(32)/MAP_OPERATION(24)/DATA_MAPPING(17)/
DELETE_ENTITY(13)/BREAK(8)/CREATE_MAP(4)/CALL_DATA_FLOW(1)。

## 二、P1-2 RETRIEVE（SCHEMA + UI 双Verified）

**真实形态（857 条语料）**：fetchType=CONDITION 393 / IDS 246 / 无 218；nullHandling=CONTINUE 559 / TERMINATION 80。

**验证流**：`验证-RETRIEVE三形态0209`（`1511141623726073240`，9 节点）
1. 条件查询（CONDITION + 右值常量）
2. ID 查询（IDS + 常量 ID）
3. 条件查询 + 空值终止（TERMINATION + nullPromptMessage）

**正向**：发布 errors=0；prove ok=True（ui 9/9，检测 mine=0）；L2 0 问题。

**反向注入**：

| 注入 | 结果 | 沉淀 |
|---|---|---|
| 条件右值用 `Simple` 形态 | 服务端 `BOOT_1001 Parameter Error`（真实右值只有 CONTEXT_VARIABLE 337 / CONSTANT 90 / EXPRESSION 65） | `condition_group` 归一 Simple→CONSTANT，事实写入 docstring |
| 自定义服务 selectMethod 缺 md5 | 原 G1–G25 全绿（漏！），设计器参数页签会取不到出入参 | **新增 G26**：md5/parameter/returnValue/fullName 缺一即拦 |
| SelectParam 引用不存在的 outputName | G2 拦 ✓ | 已有 |

## 三、P1-3 CHANGE_VARIABLE（SCHEMA + UI 双Verified）

**1053 条语料聚类（top 形态）**：

| 数量 | mappingType | selectParam | value 形态 | 含义 |
|---|---|---|---|---|
| 149 | 无 | STRING/parent | Expression | 基础变量表达式赋值 |
| 140 | attrs | DTO/MASTER_ENTITY | — | 实体变量字段映射 |
| 92 | 无 | DECIMAL/parent | Expression | 金额表达式赋值 |
| 90 | 无 | BOOLEAN/parent | Simple | 布尔赋值 |
| 86+61+37 | attrs | DTO/CUSTOM、SUB_ENTITY | — | 自定义/子实体字段映射 |
| 43+20+… | 无 | STRING/CUSTOM(children) | Simple/Expression | 自定义对象字段级赋值 |
| 82 | 无 | BIGINTEGER、STRING/parent | SelectParam | 前序节点引用赋值 |

**本轮验了 2 类**：整体赋值（value，Simple）+ 实体字段映射（attrs，DTO/MASTER_ENTITY）。
组合流 `验证-CHANGE_VARIABLE两形态0209`（`7138194478849107152`，10 节点）：
`RETRIEVE_ARRAY → CREATE_VARIABLE(BASIC) → CHANGE_VARIABLE(整体赋值) → CREATE_VARIABLE(ENTITY_OBJECT) → CHANGE_VARIABLE(attrs)`，
发布 errors=0、prove ok=True、L2 0 问题。

**反向注入**：

| 注入 | 结果 | 沉淀 |
|---|---|---|
| attrs 形态 attrType 缺 refId | 原 G1–G25 全绿（G25 只查 CREATE_VARIABLE，漏！） | **新增 G27**：CHANGE_VARIABLE attrs 同规则；L2 同步加 ATTR_MISSING_REF |
| 整体赋值形态丢 value | C-CHANGE_VARIABLE 拦 ✓ | 已有 |

**未验形态**（排入 P1-4 之后）：CUSTOM 对象 pos=children 的字段级赋值、Expression 值形态、SelectParam 值形态。

## 四、P1-5 L2 页面整体状态校验（已落地）

`components/udc.microflow.live.l2_state`：

```
read_state(app_id, mid, host)   # 一次读全量 redux flowNodes（复用 tab 0.1s / 新开 3s）
check_state(nodes)              # 缺 MUST 键 / isCompleted=false / selectParam 空 /
                                # attrType 引用四键 / 悬空 outputName 引用
```

实测：43 节点流程 3 秒内完成（对比 L3 逐抽屉 37s/11 节点）。

**一致性验证（关键）**：
- 正向：3 条流程 L2=0 问题，与 prove 抽屉结论一致；
- 反向1：注入 attrType 缺 refId 的 schema 喂给 L2 → 抓到 ATTR_MISSING_REF ✓；
- 反向2：**已知有 04004「微流程已更改」的流程，L2 = 0 问题** → 证明"属性指纹"类问题 L2 契约层看不见，
  **L3 抽屉必须保留**（这正是三级架构的分工依据，不是 L2 失败）。

## 五、事实沉淀清单（本轮新增）

1. 条件右值三形态契约（Simple 会 BOOT_1001）→ `microflow_fields.condition_group` docstring。
2. G26 自定义服务方法签名完整性。
3. G27 CHANGE_VARIABLE attrs 引用四键。
4. L2 模块 + "L2 看不见 04004 指纹"的边界证据。
5. CHANGE_VARIABLE 15 形态聚类表。
6. 流程名必须字母开头纯字母数字（`UDC_ENTITY_0001`，下划线都不行）。

## 五点五、P1-4 四节点验证（第二轮，已完成）

**最小验证流（互不混装，全部 SCHEMA+UI 双 Verified）**：

| 节点 | 流程 | id | 组合 |
|---|---|---|---|
| CREATE_MAP + MAP_OPERATION | 验证-MAP两节点 | -7062559916614323169 | PUT 写入 + GET 取出 + BASIC 变量承接 |
| DATA_MAPPING | 验证-DATA_MAPPING | 1294410053493386261 | RETRIEVE 单条 → 同实体映射 name→remarks |
| FOR | 验证-FOR计数循环 | -1617657248963268698 | 计数 1..3，循环体修改变量 |

**构造器修正（发布前被自家闸门拦下，属正向修正）**：
1. `map_operation` GET 形态：真实 10 个 GET 样本全部 `nullHandling=CONTINUE`、无 `nullPromptMessage`；
   原实现写 TERMINATION+提示语被契约闸门拦 → 改为仅显式传 null_prompt 才写。
2. BASIC 变量引用前序 BASIC 出参时 `selectParam.id/dtoType` 必须空串（G17 拦截后修正）。
3. `data_mapping` 原硬编码 expText 字段 → 泛化为 src_field/dst_field/target_entity。

**反向注入**：

| 注入 | 结果 |
|---|---|
| MAP_OPERATION GET `basic` 传裸字符串 | G9 拦 ✓（已有） |
| FOR 缺 forEnd | C-FOR 拦 ✓（已有） |
| DATA_MAPPING 映射行缺 targetField | 原全绿（漏！）→ **新增 G28**：mappingRows 空/缺 targetField/mappingMode/value 即拦 |
| MAP_OPERATION PUT entries 悬空引用 | G2 拦 ✓ |
| CREATE_MAP/CHANGE_VARIABLE 组合 | 基线 0 问题，15 条存量流程回归全通过 |

**CHANGE_VARIABLE 补充形态**（`验证-修改变量引用与表达式`，`-5694146294005387207`，6 节点，prove ok=True / L2 0 问题）：
- SelectParam 前序引用赋值（82 条样本形态）✓
- Expression 表达式赋值（327+ 条样本形态，布尔 = 统计数量 > 0）✓
- 至此 CHANGE_VARIABLE 15 形态中已验 4 类（Simple 整体赋值 / attrs 字段映射 / SelectParam / Expression），
  覆盖样本 ≈ 1000/1053；仅剩 CUSTOM pos=children 形态（需自定义 DTO 变量，挂起）。

**覆盖更新**：类别 21/26 = 81%；实例加权 7842/7937 = **98.8%**（未验仅 95 实例：
CHANGE_BATCH_ENTITY 41 / CREATE_ENTITY 32 / DELETE_ENTITY 13 / BREAK 8 / CALL_DATA_FLOW 1）。

## 五点八、构建轮（2026-10-31 晚，用户实测驱动）

**用户实测**：前端/后端校验全绿的 verifyDataMapping1928，点「测试」构建即报错 →
确认「以前端测试点击的接口为准」。抓到完整链：`udcRuntimeDeployNormalPost`（触发，deployType=RELEASE）
→ `udcSandboxBuildInfoAppGet`（状态/日志）→ `backBuild.log`（javac 错误全文）。
已沉淀 `core/facts/udc/microflow/test-build-chain.md`。

**首个 BUILD FAIL 根因**（进报告即为 RUNTIME 前置证据）：
- DATA_MAPPING 上游=单对象主实体时，代码生成器把节点输出声明成 `List<Dto>` 再取字段 →
  `VerifyDataMapping1928Service.java: 找不到符号 getName()`，构建 82% 处 FAIL。
- 语料 39 条中该形态仅 1 条（异常），主流是 SUB_ENTITY/children 列表转换。
- **新增 G29**：拦截 MASTER+parent 形态。坏流程已删，重建 → **BUILD SUCCESS 1.0.79**（六模块）。
- 校验层级铁证：L1/L2/L3 + 一致性检测全过 ≠ 能编译；BUILD 是独立维度。

**BUILD_VERIFIED 状态**：17 条存量流程（含 9 条业务复刻 + MAP/FOR/CV 验证流）全部随 1.0.79 构建通过。
DATA_MAPPING 状态改为 CONSTRUCTED（子表形态）/ 单对象形态 BLOCKED（G29）。

## 五点九、DATA_MAPPING 列表形态打通（三轮构建校准）

用户指路「数据源带子表」后推进：平台元数据核实该实体实际无子表（hasChild=false，已登记差异），
改用语料一致形态——RETRIEVE_ARRAY 上游。两轮 backBuild.log 校准：
① output.type 必须 ARRAY + structure.key 两段拼；② 列表出参不能接 END basic（List→Dto 编译错）。
最终 `验证-数据映射列表形态`（8266019240028362944）：发布 0 错 + UI 3/3 + L2 0 问题 +
**BUILD SUCCESS**（第 5 轮构建，1.0.8x）。DATA_MAPPING 列表形态 = 首个 SCHEMA+UI+BUILD 三级验证节点形态；
单对象形态由 G29 永久拦截。

## 六、遗留与下一步

1. **BUILD_VERIFIED / RUNTIME_VERIFIED 全缺**：需要一次 DELTA 构建（编译证据）；
   同一应用构建必须串行，前次未完成先 `deploy/stop`。
2. P1-4：MAP/CREATE_MAP/FOR 已验；DATA_MAPPING 子表形态待建带子表的测试实体后验。
3. CHANGE_VARIABLE 剩余形态（CUSTOM children / Expression / SelectParam）。
4. 事件类流程消失异常待查证（5 条 BUSINESS_EVENT 流程从分组消失，原因未明）。
   注意：事件触发流创建时平台可能驱逐同事件旧流程，重建前必须先查事件占用。
5. 生单规则 outputName 位置（O1）仍 OPEN。

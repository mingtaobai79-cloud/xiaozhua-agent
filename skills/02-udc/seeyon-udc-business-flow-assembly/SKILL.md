---
name: seeyon-udc-business-flow-assembly
description: Use when 把复杂业务需求组装成完整微流程链路。业务→实体→流程→事件→构建→断言。
version: 1.0.0
author: 小爪
license: internal
metadata:
  hermes:
    tags: [udc, microflow, business-flow, orchestration]
    related_skills: [seeyon-udc-microflow-generation, seeyon-udc-design-time-build]
---

# 业务 → 微流程链路组装

把一套复杂业务需求（任务书/自然语言描述）组装成**完整可运行的微流程链路**：
多实体 + 多流程 + 事件订阅 + 外部集成 + 最终业务断言。

节点级契约、闸门、表达式、运行时坑全在 `seeyon-udc-microflow-generation`（本 skill 的
"如何搭单个节点"），**本 skill 只管"如何把一套业务拆成链路并串起来"**。两套一起用：
先按本 skill 拆业务，再按 generation skill 搭节点。

## When to Use

用户给一套业务需求要建完整链路（不是单个节点验证）：
「建一套 XXX 业务」「销售订单→生产→发货闭环」「一波生成实体和流程」这类。
判别信号：任务书里有「N 张表 + M 条流程 + 事件 + 集成 + 测试数据 + 断言」。

单个节点/单个形态验证 → 用 `seeyon-udc-microflow-generation`，别用本 skill。

## 标准流程（9 步，顺序固定）

> ★★ **开工前必读 `references/business-to-capability-map.md`**：业务语义→平台构件（实体/枚举/选项集/
> 字段集/参数/流水号）→22 个节点按业务动作分类→四种流转串法→写死 vs 动态判据。
> 本文件讲「按什么顺序做」，那份讲「该用什么做」。

> ★★ **写完 draft 后、动手组装前，跑机器门禁（不要靠记忆自查）**：
> ```bash
> python scripts/business_readiness_audit.py --draft <draft脚本.py>
> python scripts/selftest_audit.py          # 验证门禁自身有效（改脚本后必跑）
> ```
> 门禁查：节点能力等级 / 子模式定位与必填项 / 编码字段走流水号 / 循环内逐条写 / 罕见流转组合。
> 退出码 2=有阻碍项，必须解决才能开工。门禁本身有故障注入自检（3 用例），改完门禁必须跑 selftest。
> 覆盖维度与校准方法见 `references/full-coverage-dimensions.md`。

### 1. 理解业务（先读任务书，别急着建）

★★★ **这一步决定后面所有工作对不对，跳过它做的都是「能跑的 CRUD 堆」。**
分两轮读：第一轮提「结构」，第二轮提「规则」。**结构提全了不等于业务理解了。**

#### 1a. 第一轮：提结构（四样清单）

- **实体清单**：N 张表，每张的主键/字段/类型/关联。注意任务书说 25 张实际列 26 张这类笔误，按实际列的表建。
- **流程清单**：M 条微流程，每条输入/输出/关键判断/失败路径。
- **事件清单**：谁发布、谁订阅、eventCode、载荷字段。
- **集成对象**：外部服务（AppService/DataFlow/DataMapping），区分"真实对象存在"vs"需模拟"。

#### 1b. 第二轮：提业务不变式（INVARIANT）—— 本 skill 的核心，别省

**业务不变式 = 「无论怎么跑都必须成立」的事实。** 每条不变式后面都必须能落成一条断言，
落不成断言的就是没理解透。任务书里的每个名词/字段/状态，都要追问一句「它在真实业务里受什么约束」。

固定提六类，逐类写清单（写不出来就说明没读懂，去问用户，别开工）：

| 类别 | 要问的问题 | 制造业踩过的反例（全部真发生） |
|---|---|---|
| **① 单据编号** | 这个编号是人工填还是系统生成？同类型能否重复？多轮运行会不会撞号？ | `poCode="PO-001"` 硬编码，第二单就重号。**编号必须走 `CALL_APP_SERVICE` 流水号（SerialNumberAppService），不是 const** |
| **② 汇总态 vs 明细态** | 写「流水/明细」之后，有没有一个「余额/汇总」也要变？两者谁派生谁？ | 只写库存流水不更新 available_qty、只写发货明细不回写订单状态 → 14 项断言 9 项挂 |
| **③ 状态机** | 每个状态字段有几个合法值？谁触发流转？流转后要不要回写上游单据？ | 发货后订单仍「生产中」，缺 PARTIALLY_SHIPPED 回写 |
| **④ 主子表关联** | 子表靠什么字段指向父表？父表必须先存在吗？ | 采购明细 poId 未赋值（=0）→ 收货查不到明细 → 库存不增 |
| **⑤ 数量/金额口径** | 含损耗吗？含税吗？精度几位？累计口径是什么？ | 损耗率 0.05 存成 decimal(20,0) 变成 0；单位成本 68.89→69 |
| **⑥ 幂等/重复** | 同一条链路跑两次会怎样？编号重复？余额翻倍？ | 编排流程 MINUTE/5 反复触发，写出 80+ 条重复领料单 |

**每类都要产出「字段 → 约束 → 对应断言」三列表**。例：

```
字段            业务约束                                  对应断言
po.poCode       系统生成、全局唯一                        第二单编号 ≠ 第一单
inventory.available_qty  每次流水都必须同步增减           MAT-A 终值 = 5+16-21 = 0
txSum(product)  流水合计 == 余额变动（同源）             SUM(quantity) = 终值 - 期初
sales_order.biz_status  发货后按量转为 PARTIALLY_SHIPPED  状态 == PARTIALLY_SHIPPED
bom_item.scrap_rate     支持两位小数（0.05 不能被截断）    requiredQty = 10×2×1.05 = 21
```

★ **判据：能不能在开工前把这个表写出来。** 写不出来说明需求没理解，
这时候建出来的流程一定会在断言环节返工——制造业案例就是先建完 8 条流程 + 26 实体，
再靠读库反查才把规则一条条补回来的，返工成本远高于当初多想 20 分钟。

★ **不变式里凡是涉及「唯一/生成/流水」的，一律优先怀疑该用平台服务（流水号/序列/生单规则），
不是 const。** 这是最高频的业务语义漏判。

#### 1c. 开工前必产出「组装计划表」（四张表，写不出来不许开工）

详细模板与完整示例见 **`references/business-to-capability-map.md`**（业务→构件→流转能力地图）。
四张表缺哪张，就说明哪块没想清楚：

| 表 | 内容 | 缺了会怎样 |
|---|---|---|
| **构件清单** | 哪些建实体、哪些用枚举/选项集/字段集/参数/流水号 | 不知道该建什么，建错构件（把枚举当 STRING、把编号当常量） |
| **流转图** | 每条流程：输入 / 写哪些表 / 更新哪些汇总态 / 输出 / 触发方式 | 不知道流程怎么串，漏掉汇总态更新 |
| **动态值清单** | 哪些字段必须动态取（编号/外键/关联 id）、取法是什么 | 写出 `PO-001` 这类重号隐患 |
| **不变式→断言** | 每条不变式对应的断言 SQL 预期值 | 无法验收，只能靠“跑通了”自欺 |

★ 这张表是后续组装的**对照单**：每次写完一条流程，对着流转图核对「该写的表写了没、该更新的汇总量更新了没」。
制造业案例就是没这张表，一路建完再靠读库反查，返工了 11 个 bug。

### 2. 澄清细节（拿不变式表去问，别空口问）

**把 1b 的不变式表直接摊给用户看**，逐行确认「我这么理解对吗」。这比问一百个开放题有效：
用户一眼能看出「这条你理解错了」，而「你还有什么要补充的」通常什么都问不出来。

重点问这几类（猜错就返工整条链）：

- **数据模型**：数量用 INTEGER 还是 DECIMAL？损耗率是百分比还是小数？金额几位小数？（→ 直接影响 `decimalDigits`）
- **编号生成**：哪些编号必须系统生成？用哪个流水号方案？（任务书不会写，必须问）
- **汇总态更新**：每写一笔明细，要同步更新哪些汇总/余额/状态字段？
- **输入输出**：每条流程的精确入参/出参（标量还是 DTO？）
- **关键判断**：分支条件的具体阈值（缺料 > 0？合格率 > 多少？）
- **测试数据**：固定测试数据 + 预期结果（这决定断言怎么写）

用户之前的口径：「业务歧义自己定默认开工，别为小事来回问」。所以：
**影响数据流/断言结构/编号唯一性的歧义必须问，纯展示/命名类歧义自己定默认。**

★ **编号生成、汇总态更新、状态机三类不允许「自己定默认」**——它们不只是实现细节，
而是业务规则本身，猜错就是整套返工。

### 3. 审计能力（识别"已验" vs "新能力"）

跑 `python -m components.udc.microflow.capability_registry <ACTION>` 查每个关键节点能力的等级：

- RUNTIME_VERIFIED → 直接用
- SCHEMA/BUILD_VERIFIED → 可用但没跑过，标记待验
- 未验形态 → 要么先验，要么降级 + 标 BLOCKED_BY_FIXTURE

**新能力（没验过运行期）是最大的时间变量**，先点出来，别等构建失败才发现。

### 4. 建实体（批量，避坑）

- 实体 `name` 限 **1-21 字符**（超了报 `BOOT_1001`），超长用缩写（`MaterialRequirement`→`MaterialReq`）。
- 字段名避开保留字（`orderNo`→`orderCode`、`status`→`bizStatus`、`receiptNo`→`receiptCode`、`result`→`inspectResult`）。
- 同应用多套业务加前缀防实体名冲突（RMA 用 `Rma` 前缀，制造业用 `Mfg` 前缀）。
- 建实体脚本模式见 `_attic_pending/biz/<topic>/01_create_entities.py`（幂等：查已有 fullName 跳过）。
- 字段类型统一：数量 INTEGER、金额/成本/损耗率 DECIMAL、状态/编码 STRING。**别混 INTEGER 和 DECIMAL**（数量字段混用会导致写字段类型不匹配，需 roundOff 转）。
- ★★ **外键字段必须建「关联实体」类型，不是 BIGINTEGER 普通字段**：子表外键（poId/materialId/warehouseId/productId/planId/supplierId…）建字段时 dataType 选「关联实体」（`dataType:"ENTITY"` + `relationApp` + `relationEntity`(父表实体 id/全名) + `relationType:1`），不能偷懒写成 BIGINTEGER——写成 BIGINTEGER 等于把主子表关系建成两张互不相干的表（relation_entity_name=null），平台关联下拉/级联全失效，微流程创建子表时外键要手动引父表 id 还容易漏（漏了平台不拦，落库外键=0，下游查明细全空）。制造业案例 26 实体所有外键全建成 BIGINTEGER，是这轮最底层的建模错误。建字段前先读 `seeyon-udc-design-time-build` 的 `references/entity-attribute-rest-add.md`（§ENTITY 类型）与 `attribute-set/create.md §11.3`。
- ★★ **DECIMAL 字段必须传 `decimalDigits` + `maxLength`（总精度），只传 `dataType:"DECIMAL"` 会 scale=0**：小数被四舍五入（损耗率 0.05→0、单位成本 68.89→69），业务断言全挂。正确 `{"decimalDigits":2,"maxLength":20}`。已建成 scale=0 的字段可 `POST /service/udc/entity/attribute/update`（GET 拿完整 DTO 改 decimalDigits 回传）修正。

### 5. 建集成对象（外部服务模拟）

真实 AppService/DataFlow 平台里不存在时（用户授权）：**用 SERVICE 微流程模拟**，
内部 create_variable 造模拟返回值，主流程 SUB_MICROFLOW 调它消费返回值。

- 标 `BLOCKED_BY_FIXTURE`（真实对象缺口），但用模拟服务让主流程数据流先跑通。
- 模拟服务必须返回"业务链下游真需要的值"（如询价返回 unitPrice，不是随便一个字符串）。

### 6. 建主流程（逐条，先 pilot 再批量）

- **先建一条最简单的流程作 pilot**（如入口流程），验证实体名/字段名能正确解析，再批量建其余。
- 每条流程独立脚本，模式见 `_attic_pending/biz/<topic>/0X_mf*.py`。
- 核心数据流（多层依赖）用真实引用，别硬编码：
  - 字段级引用先 RETRIEVE 中转成 DTO（§4.33）
  - 循环内写子表用批量写（create_list_entity → create_variable → change_list_add → create_batch_entity）
  - 循环内 RETRIEVE 按循环项字段查是平台硬约束，用 create_variable 中转
  - change_entity 目标要 DTO（先 retrieve 回读）
  - DECIMAL→INTEGER 用 roundOff 函数
  - ★ **外键（关联 id）必须动态引用，禁止 const 占位**：supplierId/warehouseId/productId/
    salesOrderId 这类外键，写 `{"const":"1"}` 是「用固定 ID 替代前序真实输出」——构造/构建全绿，
    但真实运行时外键指向不存在的 id，断言必然失败。动态获取方式：①从入参/前序节点字段引用
    （`wo.productId`）；②按编码/类型 retrieve 查真实 id（`retrieve_array supplierCode="SUP-001"`
    → FIRST_ONE → id）；③多级追溯（质检→工单→计划→订单逐级 retrieve 拿 salesOrderId）。
    只有「业务常量」（报废数、人工成本、任务号这类测试数据固定值）才允许 const。
- ★★ **单据编号走流水号服务，不用 const**（业务不变式 ①）：`poCode="PO-001"` 这类硬编码跑第二轮就重号。
  正确做法：`call_app_service` 调 `SerialNumberAppService.getSerialNumber`（仓库已 RUNTIME_VERIFIED，
  见 generation skill §4.20）。DSL：
  ```python
  {"id": "poNo", "kind": "call_app_service",
   "method_full": "com.seeyon.boot.starter.serial.service.SerialNumberAppService.getSerialNumber",
   "attrs": {"serialSchemeCode": {"const": "<应用流水号方案编码>"}},
   "caption": "取-采购单号"}
  # 写实体时 {"poCode": {"field": "poNo"}}
  ```
  流水号方案编码从 `<app>_test2.ctp_serial_scheme` 的 `code` 字段取（可用测试方案，别占业务方案）。
  **如果方案没建，先在平台建方案，别退回 const**——退回去就是重号隐患。
- 嵌套 for_each（外层成品 × 内层物料）用 LoopScopeStack 支持，循环项字段引用 `loop1.xxx`/`loop2.xxx`。
- ★ **业务一致性：写明细/流水必须同步更新汇总态（库存余额/订单状态/成本）**。
  只写明细不更新汇总 = 链路没真正串起来——流程能编译、节点能跑、BUILD_VERIFIED 站得住，
  但最终断言（库存余额=0、订单状态=已发货）全挂，BUSINESS_RESULT_VERIFIED 站不住。
  制造业案例踩过：MF-03 收货 / MF-04 领料 / MF-06 入库只写「库存流水」（明细态 movementType/quantity），
  从不更新「库存余额」（汇总态 available_qty），14 项断言 9 项失败。

  更新汇总态的 DSL 模式（循环内，对每个明细项同步更新）：

  ```python
  # 循环内用 retrieve_array CONDITION 模式（cond_field + right 引用循环内 create_variable 标量），
  # 不是 by_id 模式，所以不受「循环内 by_id 硬约束」限制，可编译运行
  {"id": "invUpd", "kind": "retrieve_array", "entity": "制造库存余额",
   "cond_field": "productId", "right": {"field": "materialIdVar"}},
  {"id": "invRec", "kind": "list_operation", "list_node": "invUpd", "op_type": "FIRST_ONE"},
  {"id": "newQty", "kind": "create_variable", "title": "newAvailableQty", "data_type": "INTEGER",
   "value": {"arith": "ADD", "items": [{"field": "invRec.availableQty"}, {"field": "loop.quantity"}]}},
  {"id": "updInv", "kind": "change_entity", "entity": "制造库存余额",
   "from_node": "invRec", "fields": {"availableQty": {"field": "newQty"}}},
  ```

  三个要点：①change_entity 目标 invRec 是 FIRST_ONE 返回的 DTO（不是标量 id）；②newQty 值用
  arith 表达式（ADD 入库/收货，SUB 出库/领料），data_type 必须匹配目标字段类型（available_qty 是 int
  → INTEGER，用 information_schema.COLUMNS 的 DATA_TYPE/NUMERIC_SCALE 确认）；③**造种子时补造所有
  会被变动的汇总态记录**（如 FG-A 成品仓库存 available_qty=0），否则运行时 FIRST_ONE 查不到 →
  空指针，整条流程回滚。

### 7. 建事件订阅（闭环）

- 订阅端 trigger 用 `mc.trigger_mf_event(event=evd)`，引用事件字段用 `{"input":"字段"}`，
  先 `res.bind_flow_input(trigger["output"], fields=...)`。
- 发布端 `publish_business_event` attrs 写 dict，`_event_attrs` 自动转列表。
- 事件驱动闭环：A 发布 → B 订阅 → B 调下一条流程。形成完整链路。
- ★★ **同一流程别「编排显式串调 + 事件订阅」双触发**：编排流程 SUB_MICROFLOW 串调了 MF-06，同时 MF-05 发布事件被 EVT-02 订阅也调 MF-06 → MF-06 执行 2 次，入库/发货各写 2 遍，库存余额多算（FG-A 应 1 实 2）。二选一：要么编排串调（事件只做通知不触发流程），要么事件订阅驱动（编排不显式串调该流程）。制造业案例去掉了编排的 call06、让 MF-06 只由 EVT-02 触发才修对。

### 8. 构建验证（一次构建编译全部）

- 构建是应用级，一次编译所有 RELEASE 流程。
- 状态卡 PUBLISHING 是平台落库 bug，下载 `backBuild.log` 确认 `BUILD SUCCESS` 才算数。

### 9. 造种子 + 运行验证 + 断言

- ★★ **断言的源头是 1b 的不变式表，不是临时想**。每条不变式对应一条断言，
  断言失败时先回去对：「是我理解错了不变式」还是「流程没实现它」——这两种返工方向完全不同。
- ★ **断言脚本本身也会错，先验证断言**：制造业曾因表名映射搞反（product↔report）、
  「流水一致性」语义写错，误报了两轮假失败。断言写完后先用已知预期对一遍：
  拿一条你确定的值去比较，确认脚本能读到正确表/列。
- ★ MANUAL 流程（无关联页面）**没有对外触发入口**：构建产物里只有 `domain/service/microflow/XxxService.java`
  （`@Service` + 普通方法），没有 REST controller、没有 @AppService 接口，**不能直接 POST 逐条触发**。
  要端到端跑，建一个 **SCHEDULE 编排流程**：内部 create_entity 造种子（基础资料+库存+订单）→
  SUB_MICROFLOW 串调各流程（`value:{"field":前序出参}` 动态传 id）→ 调度触发跑完整链路。
- ★ 编排流程 SCHEDULE 周期：`trigger_schedule(job_caption=…, cycle_type="SIMPLE",
  rotation_type="MINUTE", value="5")`——**MINUTE 最小是 5**，`value="1"` 会让调度任务
  根本不注册（ctp_job_info 0 行，日志 0 行），不是「触发慢」是「不触发」。
  ★ **编排流程 SCHEDULE 每触发一次就重跑整个「造种子 + 串调」链路，产生海量重复数据**
  （制造业案例反复触发了 80+ 条领料单）。验证完一次后立刻改回 `cycle_type="DAY"` 停掉（或删流程 +
  清数据），别让它在返工/验证期间继续污染——后续断言只认第一次触发前清干净的快照。
  ★★ **改调度周期后必须重新构建，否则运行时还是旧调度**：publish(MINUTE/5) 只改了设计态，
  沙箱运行的还是上一版包的调度配置（表现为 8 分钟完全不触发）。正确顺序：
  **publish MINUTE/5 → 构建 → 清数据 → 等第一次触发 → 立刻断言 → publish DAY**。
  反过来（先构建 DAY、后 publish MINUTE/5）等于永远不触发。
  ★ 每次 publish 调度流程都会在 `ctp_job_info` **新增一条 job（旧的不断）**，反复 publish 会堆出
  多条同名任务同时跑。收尾时查 `SELECT id,job_name,status,is_delete FROM ctp_job_info WHERE job_caption LIKE '%<名字>%'`，
  多条并存时一并停掉（改 DAY 后构建一次）。
- 断言只认读侧数据（物理表），不认脚本返回值/日志 success。最终断言 = 任务书预期结果逐条对。
- 读库用 `conn.py db`（见 generation skill §runtime），物理表字段是**下划线命名**（availableQty→available_qty），
  表名是「实体名前 8 字符 + _ + 随机尾号」，先 `SHOW TABLES LIKE '%mfg%'` 反查再 `SHOW COLUMNS`。
  ★ **相似前缀的表名（mfgproduc_xxx / mfgmateri_xxx / mfgshipme_xxx）极易搞混，必须用特征字段确认映射**，
  不能凭「名字像」猜：`SHOW COLUMNS` 看业务字段——有 `product_code` 的是产品表、有 `produced_qty` 的是报工表、
  有 `required_qty` 的是物料需求表、有 `issued_qty` 的是领料单表。制造业案例就曾把报工表当产品表查，
  浪费好几轮。字段类型用 `information_schema.COLUMNS` 一次查全（`DATA_TYPE`/`NUMERIC_SCALE`），
  确认 int 还是 decimal(20,0)，决定 change_entity 的类型匹配。

## 进度汇报口径

按 `seeyon-udc-microflow-generation` 的汇报口径：给时间点 + 已完成带数字（mid/提交号/测试数），
不给选择题。关键 milestone 汇报一次，别每条流程都停下来问。

## 脚本模板位置

一次性脚本放 `_attic_pending/biz/<topic>/`（**不是 scratch**，会被清）：

```
01_create_entities.py      # 建实体（幂等）
02_create_mock_services.py # 建模拟服务（幂等）
03_mf00_*.py ... 0X_mf*.py # 逐条主流程
1X_evt*.py                 # 事件订阅
entities.json              # 实体 fullName/caption/字段映射（供流程脚本引用）
```

## 关键决策清单（快速对照）

| 决策点 | 规则 |
|---|---|
| **业务不变式** | **开工前必须产出「字段→约束→断言」三列表，写不出来就不开工** |
| **单据编号** | **系统生成走 `CALL_APP_SERVICE` 流水号（SerialNumberAppService），禁用 const 占位** |
| 汇总态 | 写明细必须同步更新余额/汇总/上游状态 |
| 实体命名 | 21 字符内、避保留字、跨业务加前缀 |
| 外键字段 | 建「关联实体」类型（ENTITY+relationEntity），不是 BIGINTEGER |
| 字段精度 | DECIMAL 必传 `decimalDigits` + `maxLength` |
| 字段类型 | 数量 INTEGER / 金额 DECIMAL，别混 |
| 外部服务 | SERVICE 微流程模拟 + BLOCKED_BY_FIXTURE |
| 循环写子表 | 批量写（不是逐条 create_entity） |
| 循环内查 | create_variable 中转（by_id_from 循环项不支持） |
| change_entity | 目标 DTO（先 retrieve） |
| DECIMAL→INTEGER | roundOff 函数 |
| 事件 | trigger_mf_event + bind_flow_input + {"input":字段} |
| 双触发 | 编排串调 / 事件订阅 二选一，别双管 |
| 构建 | 应用级一次编译，卡 PUBLISHING 查 backBuild.log |
| 断言 | 只认读侧数据 |

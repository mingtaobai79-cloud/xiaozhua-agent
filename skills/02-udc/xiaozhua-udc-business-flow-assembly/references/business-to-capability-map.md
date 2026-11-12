# 业务 → 构件 → 流转：能力地图

> 写代码前先理解业务需求、找对应实体、再动手。UDC 同理：先明确「这个业务语义该用平台哪个构件表达」，
> 再定「这些构件之间怎么流转串通」，最后才写节点。
> **本文件是开工前的对照表，不是节点手册**（节点形态见 `xiaozhua-udc-microflow-generation`）。

## 一、业务语义 → 平台构件（建什么）

先判断一句话说的是哪类东西，再决定建什么。**建错构件比写错节点难改十倍**（要迁数据、改引用、重建）。

| 业务语义 | 平台构件 | 判据 | 反例（踩过） |
|---|---|---|---|
| 「一张单/一条记录/一个业务对象」，有自己的生命周期和编号 | **实体**（UDC 实体表） | 需要按条件查询、需要存多条、需要被别的流程引用 | 把「质检记录」做成变量 —— 查不到也统计不了 |
| 「一个可选值集合」，值固定且要被人读懂（待生产/生产中/已完工） | **枚举**（ENUM / CTPENUM） | 值域封闭、要显示中文、要在页面下拉 | 用 STRING 存状态 → 无法校验、无法筛选、报表全是字符串比对 |
| 「一组相关的可选值」，业务上成组出现（如故障类型+对应处理方式） | **选项集**（option-set） | 多个枚举成套、需要一起维护 | 拆成一堆独立枚举 → 改一处要改多处 |
| 「一类字段的组合」，多张表都要有（创建人/创建时间/审批信息） | **字段集**（attribute-set） | 字段组合跨实体复用 | 每个实体手建一遍 → 后续加字段要改 N 张表 |
| 「系统参数/业务配置」，不是单据数据（税率、默认仓库、阈值） | **参数**（parameter） | 全局读、极少改、不参与业务流转 | 建实体存配置 → 每次用都要 retrieve，还多一张表 |
| 「单据编号」，必须唯一、系统生成、连续或按规则 | **流水号**（serial） | 任何编码类字段（poCode/workOrderCode/receiptCode） | **const 硬编码 `PO-001` —— 第二单就重号，这是最高频错误** |
| 「临时结构」，只在一次流程内部传递，不需要落库 | **CREATE_VARIABLE（实体型/DTO型/标量）** | 不落库、不跨流程、不需要查 | 为传参建实体 → 表里全是垃圾数据 |

### 建实体的铁律（每条都踩过）

1. **外键字段必须建「关联实体」类型**，不是 BIGINTEGER：
   `dataType=ENTITY` + `relationEntity`(父表实体 id/全名) + `relationApp` + `relationType=Many2OneAssociation`。
   建成 BIGINTEGER → `relation_entity_name=null` → 主子表关系断裂、平台关联下拉失效、
   微流程漏赋值也不报错（落库外键=0，下游查明细全空）。
   对照：系统字段 `applicant` 是 `dataType=ENTITY, relation_entity_name=人员` —— 这才是关联字段的样子。
2. **DECIMAL 必须传 `decimalDigits` + `maxLength`**，只传 `dataType=DECIMAL` 会 scale=0：
   损耗率 0.05→0、单位成本 68.89→69。正确 `{"decimalDigits":2,"maxLength":20}`。
   已建错的用 `POST /service/udc/entity/attribute/update`（GET 完整 DTO 改 decimalDigits 回传）。
3. **实体 name 限 1-21 字符**（`BOOT_1001`），超长用缩写。
4. **字段名避保留字**：`orderNo/status/state/result/receiptNo` 等报 `UDC_ENTITY_0002`。
   改法：`status→bizStatus`、`orderNo→orderCode`、`result→inspectResult`、`receiptNo→receiptCode`。

## 二、业务动作 → 节点（怎么用）

22 个节点按「业务动作」归六类。**先看业务动作属于哪类，再选节点**，别记节点名找用途。
等级：✅RUNTIME_VERIFIED / 🔨BUILD / 📄SCHEMA。查询实时等级：
`python -m components.udc.microflow.capability_registry <ACTION>`

### A. 取数（读）

| 业务动作 | 节点 | 关键点 | 等级 |
|---|---|---|---|
| 按 id 查一条 | `retrieve` | `by_id_from` 传前序节点；要字段必须先 RETRIEVE 成 DTO | ✅ |
| 按条件查多条 | `retrieve_array` | `cond_field`+`right`；右值不能字段引用，要先用 create_variable 转标量 | ✅ |
| 统计条数（不要明细） | `retrieve_array` + `fetchType=COUNT` | 出参是 INTEGER 不是列表 | ✅ |
| 按 id 列表查 | `retrieve_array` + `fetchType=IDS` + `ids_from` | 无 condition | ✅ |
| 查分页 | `page_info` + `retrieve_array` `page_info_from` | pageInfo 少一个属性就 PROPERTY_IS_REQUIRED | ✅ |

### B. 写数（落库）

| 业务动作 | 节点 | 关键点 | 等级 |
|---|---|---|---|
| 新增一条 | `create_entity` | 出参是**标量 id**，没有字段 | ✅ |
| 修改一条 | `change_entity` | 目标必须是 DTO（先 retrieve），不能引 create 的标量 id | ✅ |
| 删除一条 | `delete_entity` | 动态删只能用 `SELECT_PARAM`；CONDITION 右值只能常量 | ✅ |
| 循环内批量新增子表 | `create_list_entity` → `create_variable`(entity) → `change_list_add` → `create_batch_entity` | **循环内别逐条 create_entity**（用户明确偏好批量）；列表元素不能带 id | ✅ |
| 批量改 | `change_batch_entity` | 无 attrs，出参是影响行数 | ✅ |

### C. 计算/加工

| 业务动作 | 节点 | 关键点 | 等级 |
|---|---|---|---|
| 存中间值/累加器 | `create_variable` / `change_variable` | 标量用 paramType=BASIC；实体型走 fields | ✅ |
| 算术/条件表达式 | `create_variable` 的 `value:{"arith":...}` | 键是 `arith:"ADD"` 字符串；DECIMAL→INTEGER 用 `roundOff` | ✅ |
| 改列表（增删改清） | `change_list` | 四动作形态完全不同（ADD/REPLACE/CLEAR/REMOVE），无出参 | ✅ |
| 列表操作（取值/排序/去重/聚合） | `list_operation` | 14 种；PICK_ONE **1 基**；DSL 字段是 `index_value` | ✅ |
| 列表过滤 | `list_operation` `op_type=FILTER` | 离线编译，不用进设计器 | ✅ |
| 类型转换 | `convert_data` | 出参 type/dataType/javaType 三件套要一起改 | ✅(仅 String2Long) |
| 建 Map / Map 操作 | `create_map` / `map_operation` | KEY_SET 已补分支；REMOVE 无专门分支 | ✅(PUT/GET) |
| 跨实体字段映射 | `data_mapping` | 上游必须是**列表** | ✅(单字段同实体) |

### D. 控制流

| 业务动作 | 节点 | 关键点 | 等级 |
|---|---|---|---|
| 条件分支 | `branch` | condition 走表达式引擎，**支持字段 vs 字段比较** | ✅ |
| 遍历列表 | `for_each` | 循环项字段引 `loop.xxx`；循环内 RETRIEVE by 循环项字段**平台不支持**，要 create_variable 中转 | ✅ |
| 固定次数循环 | `for_count` | | ✅ |
| 跳出循环 | `break` | **type 必须=BREAK**，写 ACTIVITY 会静默丢弃（零报错最难查） | ✅ |
| 业务异常终止 | `custom_error` | 无 actionType（会被 normalize 剥掉） | ✅ |
| 流程返回 | `end` | basic_out 必须匹配引用节点 output.dataType | ✅ |

### E. 集成（跨流程/跨服务）

| 业务动作 | 节点 | 关键点 | 等级 |
|---|---|---|---|
| 调子流程 | `sub_microflow` | hasInput/hasOutput 必须照抄子流程当前契约，改契约要重发父流程 | ✅ |
| 调平台服务（流水号等） | `call_app_service` | **单据编号就用这个**；attrs 要字段级 attrType（16-20 键，用 field_attr 造） | ✅ |
| 执行生单规则 | `call_data_flow` | `dataFlowMappingId` 存**行 id**，不是 dataFlow 对象 | ✅ |
| 发业务事件 | `publish_business_event` | attrs 写 dict，自动转列表 | ✅ |

### F. 触发器（怎么启动）

| 业务语义 | 触发器 | 关键点 |
|---|---|---|
| 人工/其他流程调用 | `trigger_manual` | 有入参出参；**无关联页面时构建产物没有 REST controller，不能直接 POST** |
| 定时跑 | `trigger_schedule` | **MINUTE 最小 5**，value=1 任务根本不注册；改周期后必须重建 |
| 实体数据变化触发 | `trigger_event` | ENTITY 事件 |
| 应用内流程事件 | `trigger_mf_event` | 订阅端引事件字段用 `{"input":"字段"}`，先 bind_flow_input |

## 三、构件之间怎么流转串通（怎么串）

四种串法，按业务耦合度选。**同一对流程只能选一种，双管会重复执行**。

### 1. 主子表（同一流程内，父子数据）

```
create_entity(父)  →  create_list_entity(子列表)
                     →  for_each(明细源)
                          create_variable(子对象, fields={父表外键: {"field": 父id}})
                          change_list_add
                     →  create_batch_entity(子表)
```

**铁律：子表外键必须显式引用父表 id**。漏了平台不拦，落库外键=0，下游按外键查明细全空 ——
这是隐蔽性最高的错误（构建绿、运行绿、只有业务结果错）。
父表必须在循环**之前**创建（要先有 id 才能被子表引用）。

### 2. 微流程串联（跨流程，顺序确定）

```
编排流程: create_entity(造种子) → sub_microflow(MF-00) → sub_microflow(MF-01, value=前序出参) → ...
```

- 用 `value:{"field": "前序节点id"}` 动态传，**不许 const 占位假 id**。
- 编排流程一般用 SCHEDULE 触发（MANUAL 流程无 REST 入口，串不起来）。

### 3. 事件驱动（跨流程，松耦合/异步）

```
A 流程: ... → publish_business_event(eventCode=X, bizKey=业务id)
订阅流程: trigger_mf_event → create_variable({"input":"bizKey"}) → sub_microflow(B)
```

适合「某件事发生后，可能有多方关心」。缺陷：链路难调试，要按 traceId 看 flowLog。

### 4. 定时扫描（无触发源的补偿）

`trigger_schedule` + `retrieve_array` 查「待处理」状态 → 逐条处理 → 改状态。
适合外部系统无回调的场景。

### ⚠️ 双触发陷阱（真踩过）

编排流程 SUB_MICROFLOW 串调了 MF-06，同时 MF-05 发布事件被 EVT-02 订阅也调 MF-06
→ MF-06 执行 2 次，入库/发货各写 2 遍，库存多算（FG-A 应 1 实 2）。
**同一对流程，串调与事件订阅二选一。**

## 四、写死 vs 动态：什么必须动态取

**判据：这个值在第二单/第二轮运行时会不会变？会变就不能写死。**

| 值 | 必须动态 | 取法 |
|---|---|---|
| **单据编号** | ✅ **绝对** | `call_app_service` 流水号（SerialNumberAppService.getSerialNumber） |
| **主子表外键** | ✅ **绝对** | 父表 create 出参 id（`{"field":"po"}`） |
| 关联实体 id（供应商/仓库/产品） | ✅ | 按编码/类型 retrieve → FIRST_ONE → id |
| 多级追溯（质检→工单→计划→订单） | ✅ | 逐级 retrieve |
| 循环项的值 | ✅ | `loop.xxx` 字段引用 |
| 汇总/余额 | ✅ | retrieve 现值 + arith 计算 + change_entity 回写 |
| 状态目标值 | ❌ 可常量 | `{"const":"已收货"}` —— 状态机本来就是固定值 |
| 业务测试数据（报废数/人工成本/任务号） | ❌ 可常量 | 任务书给定的固定值 |
| 枚举值 | ❌ 可常量 | 枚举就是封闭值域 |

★ **判据的反面同样重要**：状态值、枚举、任务书给的测试数据**该**用常量，
把它们也做成动态引用是过度设计（多建节点、链路变复杂、没业务意义）。

## 五、开工前必产出的「组装计划表」

理解完业务，先写这张表，**写不出来不许开工**。这张表就是后续所有组装工作的对照单，
也是断言脚本的来源。

```markdown
## 1. 构件清单
| 构件类型 | 名称 | 说明 | 为什么用这个 |
|---|---|---|---|
| 实体 | 采购订单 | poCode/supplierId/planId/totalAmount/bizStatus | 有生命周期、被明细和收货引用 |
| 实体 | 采购明细 | poId(关联实体→采购订单)/materialId/quantity | 主子表 |
| 枚举 | 订单状态 | 待收货/已收货 | 值域封闭、页面要下拉 |
| 流水号 | 采购单号方案 | PO+流水 | 编号必须唯一 |

## 2. 流转图（谁写谁、谁读谁）
| 流程 | 输入 | 写哪些表 | 更新哪些汇总态 | 输出 | 触发方式 |
|---|---|---|---|---|---|
| MF-02 采购 | planId | 采购订单、采购明细 | 采购订单.totalAmount | poId | 编排串调 |
| MF-03 收货 | poId | 收货单、收货明细、库存流水 | **库存余额.available_qty += 16** | receiptId | 编排串调 |

## 3. 动态值清单（哪些不能写死）
| 字段 | 动态取法 |
|---|---|
| po.poCode | call_app_service 流水号 |
| poItem.poId | {"field":"po"} |
| supplierId | retrieve_array supplierCode=SUP-001 → FIRST_ONE → id |

## 4. 不变式 → 断言
| 不变式 | 断言 SQL 预期 |
|---|---|
| MAT-A 库存 = 5+16-21 | SELECT available_qty → 0 |
| 流水与余额同源 | SUM(quantity) = 终值 - 期初 |
| 订单状态部分发货 | biz_status = 'PARTIALLY_SHIPPED' |
```

**四张表齐了才动手。** 缺哪张表就说明哪块没想清楚：
缺构件清单 → 不知道该建什么；缺流转图 → 不知道流程怎么串；
缺动态值清单 → 会写出 `PO-001`；缺不变式 → 断言写不出来、无法验收。

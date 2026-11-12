# P6 持续学习：证据驱动的能力登记

> 2026-11-03

## 1. 要解决的问题

P5 之前，能力等级靠人记、靠文档手写：
验证完一轮 → 人工改矩阵 → 下次生成时**没有任何东西会提醒你**「这个节点的这个形态还没验过」。
知识会漂移，等级会被虚报。

P6 把这条链变成代码：

```
真实验证（读侧断言）
      ↓  record_evidence(action, payload)
证据 JSON 落盘  +  矩阵该行等级自动更新
      ↓  load()
能力登记表（结构化）
      ↓  advisory(schema)
生成流程时立刻列出「哪些节点还没有运行证据」
```

## 2. 三个入口

### 2.1 `load()` / `summary()` — 能力登记

`components/udc/microflow/capability_registry.py` 直接读
`core/facts/udc/microflow/capability-matrix.md` + `evidence/*.json`：

```
$ python -m components.udc.microflow.capability_registry
RUNTIME_VERIFIED   15 类  88.5%  BREAK,CALL_DATA_FLOW,CHANGE_BATCH_ENTITY,...
LIVE_EXECUTED       1 类   0.5%  PUBLISH_BUSINESS_EVENT
SCHEMA_VERIFIED     4 类   8.3%  CONVERT_DATA,CREATE_LIST,CREATE_MAP,MAP_OPERATION
CONSTRUCTED         2 类   2.7%  CALL_APP_SERVICE,DATA_MAPPING

$ python -m components.udc.microflow.capability_registry CHANGE_LIST
CHANGE_LIST: RUNTIME_VERIFIED（317 实例）
  范围: 四动作；ADD 列表形态、REMOVE 多字段 countAttrs **未验**
  证据: change-list-runtime-2026-11-03.json
```

`scope` 是从矩阵备注里抽出来的**范围限定**——所以「RUNTIME_VERIFIED」永远带着边界，
不会被当成全形态通过。

### 2.2 `advisory(schema)` — 生成时可见

`MicroflowComposer.finish()` 组装完成后自动算一次，结果挂在 `mc.advisories`：

```
advisories: ['CREATE_LIST: 未达 RUNTIME_VERIFIED（当前 SCHEMA_VERIFIED）']
```

不阻塞构建（SCHEMA_VERIFIED 的节点照样能构建成功），只是**让缺口在生成那一刻就暴露**。

### 2.3 `record_evidence()` — 等级只能由证据提升

```python
record_evidence("CREATE_LIST", {"date": "...", "cases": [{"case": "...", "pass": True}]})
```

- payload 里没有 `pass=True` 的用例 → 直接抛错（**禁止口头升级**）
- 证据写 `evidence/<action>-runtime-<date>.json`，矩阵该行等级列自动改写
- 返回证据文件路径

## 3. 闭环的硬约束

| 约束 | 原因 |
|---|---|
| 没有 pass=True 用例不许升级 | 等级是事实，不是愿望 |
| 等级只从 note 里解析，不单独存字段 | 矩阵是唯一事实源，避免双写漂移 |
| advisory 只提示不拦截 | 未验证形态仍可构建，但要让人看见 |
| 范围限定必须写进 note | 防止「一种形态通过」被读成「全部通过」 |

## 4. 当前缺口（registry 自动列出）

- **4 类 SCHEMA_VERIFIED**：CREATE_LIST、CONVERT_DATA、MAP_OPERATION、CREATE_MAP
  → 都只需要补运行时用例，不缺平台对象
- **2 类 CONSTRUCTED**：CALL_APP_SERVICE、DATA_MAPPING → 缺真实平台对象
- **1 类 LIVE_EXECUTED**：PUBLISH_BUSINESS_EVENT → 缺订阅者

## 5. 测试

`tests/test_capability_registry.py`（7 条）：
矩阵解析、等级与范围、汇总一致性、advisory 去重与分支遍历、
拒绝空证据、证据回填后等级生效。

---

## 6. 闭环实测（2026-11-03，用 P6 自己的机制跑一轮）

拿最接近「只需要补运行时用例」的两个类型开刀：CREATE_LIST、CONVERT_DATA。

### 6.1 流程

```
1-建实体列表(CREATE_LIST paramType=ENTITY_OBJECT) → 2-SIZE → 3-写 CL0
4-查源列表(3 条) → 5-CHANGE_LIST(ADD，列表形态) → 6-SIZE → 7-写 CL1
8-建字符串"42" → 9-CONVERT_DATA(String2Long) → 10-写 CV
```

### 6.2 读侧结果（01:29:00，同一次执行）

| 行 | 值 | 断言 |
|---|---|---|
| CL0 | **0** | 空列表语义正确 |
| CL1 | **3** | ADD 的**列表形态**把 3 条整体追加进空列表 |
| CV | **42** | `"42"` 经 String2Long 变 42，写进 INTEGER 列 |

### 6.3 途中抓到的构造器缺陷（G32 先拦、编译再证）

- `convert_data` 只设了 `convertType`，没按转换方式改出参形态 → G32 报
  「String2Long 目标 type 应为 OBJECT」
- 补了 type/dataType 后**编译失败**：`Long 无法转换为 String`
  —— 因为 `javaType` 还留着模板的 `java.lang.String`，代码生成按 String 声明变量
- 修：出参 `type/dataType/javaType` 三者一起按转换方式设置；G32 增加 javaType 校验

这条正好印证 P5 的结论：**Schema 校验通过 ≠ 能编译 ≠ 运行正确**，三层证据缺一不可。

### 6.4 回填（不手改矩阵）

```python
record_evidence("CREATE_LIST", {...cases...}, note="RUNTIME_VERIFIED（ENTITY_OBJECT + ADD 列表形态）")
record_evidence("CONVERT_DATA", {...cases...}, note="RUNTIME_VERIFIED（仅 String2Long）")
```

结果：

```
RUNTIME_VERIFIED   17 类  96.2%
LIVE_EXECUTED       1 类   0.5%   PUBLISH_BUSINESS_EVENT
SCHEMA_VERIFIED     2 类   0.6%   CREATE_MAP, MAP_OPERATION
CONSTRUCTED         2 类   2.7%   CALL_APP_SERVICE, DATA_MAPPING
```

同时把 CHANGE_LIST 的「ADD 列表形态未验」从范围限定里去掉（本轮已验）。

### 6.5 剩下什么

| 类型 | 状态 | 缺什么 |
|---|---|---|
| CREATE_MAP / MAP_OPERATION | SCHEMA_VERIFIED | 只需运行时用例（下一轮） |
| CALL_APP_SERVICE / DATA_MAPPING | CONSTRUCTED | 真实平台对象 |
| PUBLISH_BUSINESS_EVENT | LIVE_EXECUTED | 订阅者 |

### 6.6 清理

流程已删、`P%` 数据 0 行、重建 SUCCESS 233s、平台 30 条流程无残留。

---

## 7. 闭环第二轮：CREATE_MAP + MAP_OPERATION（01:47）

```
1-建Map(STRING→STRING) → 2-PUT(k1=v1) → 3-GET(k1) → 4-写 sourceTable
```

读侧：`P6MAP1-GET.source_table = "v1"` —— PUT 确实写进 Map，GET 确实取出。

回填后：

```
RUNTIME_VERIFIED   19 类  96.8%
LIVE_EXECUTED       1 类   0.5%   PUBLISH_BUSINESS_EVENT
CONSTRUCTED         2 类   2.7%   CALL_APP_SERVICE, DATA_MAPPING
```

**SCHEMA_VERIFIED 已经清零**：凡是不依赖外部对象的节点类型，都拿到了运行证据。

## 8. P6 结束状态

| 维度 | 结果 |
|---|---|
| 能力登记 | 22 类全部结构化，等级由证据驱动 |
| 生成时提示 | `mc.advisories` 会列出未达 RUNTIME_VERIFIED 的节点 |
| 等级回填 | 4 次调用 `record_evidence`，矩阵自动更新，无手改 |
| 剩余缺口 | 2 类缺真实平台对象（不降级）、1 类缺订阅者 |
| 测试 | 2527 collect / 2505 passed / 22 skipped |

P6 的目标是「让每个学进去的结论都有真实执行证据」——现在等级只能由
`record_evidence` 提升，而它拒绝没有 `pass=True` 用例的 payload。这条硬约束
就是 P6 的验收标准。

---

## 9. 第三轮：CALL_APP_SERVICE / PUBLISH_BUSINESS_EVENT / DATA_MAPPING（全部收口）

### 9.1 CALL_APP_SERVICE — 流水号组件

```
SerialNumberAppService.getSerialNumber
SingleRequest<SerialNumberDto> → SingleResponse<String>
app = boot-starter-serialnumber（inApp=false）
```

`p6svc6sv01` 每 5 分钟取一次并落库：

```
09:46 HT2026111   09:51 HT2026112   09:56 HT2026113
ctp_serial_history 同刻记录（scheme_id=-9200500489397925395）
```

修了三个构造器缺陷：starter 服务归属自动推导、attrs 支持字段级 attrType、
简单类型返回值不再默认 DTO。

### 9.2 PUBLISH_BUSINESS_EVENT — 自建订阅者，载荷级证明

订阅流程 `p6evt6sv01`：`type=BUSINESS_EVENT` + `messageSource=MICRO_FLOW_EVENT`，
订阅端把收到的 `eventCode`/`remark` 写库。引用事件字段的形态是
`position=children` + `key=<触发output名>_<dto>.<字段>`（21 条真实样本），
新增 `_event_field_ref` 支持。

```
09:56:00  HT2026113 / SN         ← 发布端拿到的流水号
09:56:00  P6SV01    / p6-svc     ← 订阅端收到的分载荷，逐字相等
```

不是「有事件触发了」，是「订阅端收到的就是发布端投的那条」。

### 9.3 DATA_MAPPING — 列表映射 → 批量写

```
RETRIEVE_ARRAY(3 条) → DATA_MAPPING(sourceTable→taskId) → CREATE_BATCH_ENTITY
```

`10:19:00` 新增 3 行 `task_id='DM-SRC'`（源行 source_table 的值），逐字相等。

途中修了两个真 bug：
1. `ARRAY` 判定写在 `_entity_output` 之前 → 被覆盖回 OBJECT → 下游引用被 G31 判死
2. DSL 没暴露 `src_field/dst_field`，只能映射 name→name

已知未修：`FIRST_ONE` 接手 DATA_MAPPING 输出会丢 javaType（生成
`_LIST_OPERATION_xxx` 当类名 → 编译「找不到符号」），本轮改走批量插入规避。

## 10. P6 结束状态

```
RUNTIME_VERIFIED  22 类 100.0%
```

**22 类活动节点全部拿到真实运行证据，每一类都带范围限定。**
未覆盖的形态（如 SUB_MICROFLOW 的 DTO 入参、RETRIEVE_ARRAY 的多条件/分页、
LIST_OPERATION 其余 12 种操作、DATA_MAPPING 跨实体/多字段、事件的跨应用 MQ 形态）
都写在矩阵 note 里，不会被读成「全部通过」。

P6 的验收标准：等级只能由 `record_evidence` 提升，而它拒绝没有 `pass=True`
用例的 payload —— 本轮三次提升全部走了这条路径。

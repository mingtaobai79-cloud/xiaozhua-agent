# P7-E2E-1 端到端业务闭环实证（2026-11-03）

## 结论：E2E_BUSINESS_FLOW_VERIFIED

结构化草稿 → 归一化 → 逻辑图 → 构造 → 保存 → 发布 → 构建 → 运行 → 数据库结果正确，
全链路第一次跑通（非「仅 BUILD SUCCESS」）。

## 业务场景

「统计源表为 <MARK> 的断点中已处理行数 > 2 的记录数，写回一条新断点
（任务标识=<MARK>-RESULT，已处理行数=统计数）。」

草稿**用中文字段名**（任务标识 / 源表 / 已处理行数），验证归一化真名解析。

节点链：CREATE_ENTITY(5 条种子 1/2/5/8/9) → RETRIEVE_ARRAY(源表=<MARK>)
→ FILTER(已处理行数>2) → SIZE → CREATE_ENTITY(写 RESULT)。

## 证据链（execution_id = e2e-573258e3e6ec）

| 阶段 | 证据 |
|---|---|
| 归一化 | 任务标识→taskId / 源表→sourceTable / 已处理行数→processedRows（`resolved.fields`） |
| 构造 | 9 节点，alias→nodeId 映射齐全（CREATE_ENTITY_* / RETRIEVE_ARRAY_* / LIST_OPERATION_*） |
| 保存+发布 | state=RELEASE |
| 构建 | BUILD_SUCCESS，buildVersion=20261103193347 |
| 运行 | SCHEDULE(MINUTE/5) 触发 3 次（19:39/19:44/19:49），udc_rt_app_log is_success=1 |
| 数据库断言 | 第一次触发 RESULT processed_rows=**3**（= 1/2/5/8/9 过滤>2 得 3 条，**正确**） |

写结果节点 input：`processedRows=3`，output：`插入成功返回ID：-6872488476139806536`。

第 2/3 次 RESULT=6/9 是**种子累积**（每次触发又写 5 条种子，查询自然读到更多），
恰好反向证明 FILTER/SIZE 逻辑正确（5/8/9 三组 × 2 次 = 6、× 3 次 = 9）。

## 本轮修掉的 pipeline/保存链 bug（4 个）

1. `save_pipeline._trigger_type` 写死返回 MANUAL → 定时流程 create/publish 被降级，
   两次 publish trigger_type 不一致 → 第二次 publish BOOT_3000。
2. `read_state` CDP 端口写死 9333（实际用户浏览器在 9222）→ L2 连接 WinError 10061。
3. `PlatformBuilder.build` 对 UDC_DEPLOY_0002（app publishing 构建锁）不重试 → 直接 FAIL。
4. pipeline 无 skip_l2 选项（L2 是 CDP 驱动的 UI 检查，非业务结果核心）。

## ★ 新坑：写结果引用 LIST_OPERATION 标量出参的 UI 显示

构造器 `{"field":"sz"}` 引用 SIZE 出参，生成的是**正确的 SelectParam**（BASIC 标量整节点
引用，name=key=path=outputName、id=''、dtoType=''、position=parent）。

但平台**保存时把它规范化成 Expression**：

```
executableExpr = <44字符Base64> + _LIST_OPERATION_ec3ac4._LIST_OPERATION_ec3ac4   ← 两级
```

平台把 `name=outputName` 的整节点引用误当成「字段引用」（字段名=outputName），
生成「节点.节点」的畸形 executableExpr，前端抽屉显示红「所选"命中数"已变更」、
值变成 `{微流程.3-统计.命中数}`。

**但运行时求值正确**（=SIZE 结果 3）——第一次触发 RESULT=3 就是铁证。

所以这是** UI 显示层问题，不影响业务正确性**。若后续要消除红字，方向是：
引用 LIST_OPERATION 标量出参时用**对象引用/表达式**形态而非字段映射 SelectParam，
或让平台回读后重新 normalize。未在本轮修（非业务结果正确性阻塞项）。

## ★ 修复（2026-11-03，P6 整理轮）

写结果引用标量出参（SIZE/SUM/MIN/MAX）已改为**表达式形态**（不再用 SelectParam）：

- 根因：SelectParam 整节点引用（name=outputName）被平台保存时误当成「字段引用」，
  规范化成「节点.节点」畸形 executableExpr，前端红「所选"命中数"已变更」。
- 修复：`logic_graph._scalar_value_slot`——标量出参（node_dtype 是 BIGINTEGER/INTEGER 等）
  走 `ExpressionCompiler + build_remote + to_value_slot`，生成两级 VARIABLE token
  （value=`X.X`）+ 两级标量 context（顶层 OBJECT + 子项标量）+ 带前缀 executableExpr；
  DTO 字段引用仍走 SelectParam。
- 验证：DRY 下 create_entity 引用 SIZE 出参，`value.type == "Expression"`，
  tokens 两级 `_LIST_OPERATION_x._LIST_OPERATION_x`、context 子项 type=INTEGER。

## ★★ 表达式形态的三个边界（2026-11-04，MF-01 构建暴露）

`_scalar_value_slot` 把「引用标量出参」一律转 Expression 后，MF-01（采购申请→供应商比价）
端到端构建暴露三个 NOT_BIGINTEGER（`UDC_MICRO_FLOW_04004`）边界，逐个修掉：

1. **数值字段 const 常量必须转字符串**（`logic_graph._entity_fields`）：BIGINTEGER/INTEGER/DECIMAL
   字段传 int/float 常量（`{"const": 1}`），检测器 `CheckUtils.checkSimpleValue` 读
   `attrValue.getSimple()`（String）后 `Long.valueOf` 校验，int/float 被判「不是长整数」。
   修：按字段 dataType 把数值常量转字符串（`1`→`"1"`、`1000.0`→`"1000.0"`）。
   ★ 反编译里有两个 NOT_BIGINTEGER 抛点、方向相反：`CheckUtils.checkSimpleValue`
   （字符串 `Long.valueOf`）与 `NodeUtils.getLong`（JsonNode `isLong()`）。构建实际走
   `MicroFlowComponentUtils.buildAttrValue` 的 `simpleObj.asText()`→`checkSimpleValue`，
   是**字符串口径**，别按 `isLong` 的数字口径改。

2. **写操作 id 出参引用必须走 SelectParam，不走 Expression**（`logic_graph._scalar_value_slot`）：
   CREATE_ENTITY/CHANGE_ENTITY/DELETE_ENTITY（及 batch）的 id/影响行数出参虽是标量
   （BIGINTEGER/INTEGER），引用它要 SelectParam（引用节点 id 字段），转 Expression 报
   NOT_BIGINTEGER。修：`_node_ref` 的 ref 加 `node_action`；写操作族的标量出参在
   `_scalar_value_slot` 返回 None 走 SelectParam，只有 LIST_OPERATION 聚合标量
   （SIZE/SUM/MIN/MAX）才走表达式。

3. **Expression resultType 用目标字段 dataType，不是出参节点 dataType**：SIZE 出参是
   INTEGER，目标字段（如迁移断点.processedRows）可能是 BIGINTEGER，resultType 声明成
   INTEGER 被判类型不匹配报 NOT_BIGINTEGER。修：`_scalar_value_slot` 加 `field_name` 参数，
   结果类型用字段 dataType（可能宽化 INTEGER→BIGINTEGER），context 变量类型仍用出参
   dataType（SIZE=INTEGER）。

## 隔离与清理

- 测试数据用唯一 MARK（E2E-<时间戳>），任务标识 S1..S5 / RESULT，可隔离可追踪。
- 收尾：删流程 p7e2e1933 → 清 E2E-% 数据 → 重建（让包不含该流程、停定时任务）。

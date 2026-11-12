# C-5｜编辑/删除回流写（CRUD 闭环）

app 8704025620829192834｜实体 4796455827714164161｜zzprobeDecimal01 (6019556237194179089)｜test2
**结论：PASS**（两步各 CROSS-VERIFIED＋组装映射）

## 0. 基线：编辑前 43 行，目标 ml=18/dd=4/字段1。

## 1. ①编辑（dd 4→2）
双击类型单元格进编辑态→点「请输入小数位数」→Ctrl+A→逐字符输入 `2`→Tab→空白失焦；渲染「18位/2位」。

body（`save-batch.request.step1-update.json` 99,008 B）：`udcAttributeGroupOperateBatchPost` 的 `params0` **四组 attributeDtoList（7/19/6/7，Σ=39）39 条全 UPDATE**，目标 `params0[3].attributeDtoList[6]` ml=18 dd=2。
⇒ **修正 C-4 新-B：编辑=全量 39 条回写（四组），非仅编辑行、不止 params0[3] 的 7 条。**

DB：dd 4→2。**值层零漂移 DIFFS=1**（仅目标值变，其余 38 条零变），行数不变。update_time 整组刷新（现 42 行中 38 行=14:54:27、4 行 hidden=1 保持 10-12；14:48:41 已被覆盖不可复现）——零变化只证「值」未变，**不证「无写入」**。

op_log（写 1）：14:48:41 `action_type=3`/`module=6 sub=11`/`小数位数 4 -> 2`；`attributeId=5694401663173477663`（=createTime）**再次指错** ⇒ 按 A1 以 elementRecords 为准。

CROSS-VERIFIED（10 项）：zzprobeDecimal01｜DECIMAL｜ml=18｜**dd=2**｜min=0｜orderNo=43｜zzprobe_decimal01｜entityId 4796455827714164161｜appId 8704025620829192834｜id 6019556237194179089，三源一致。

## 2. ②删除
勾选行内 `.ant-checkbox`（点行无效）→「删除」→弹窗「确定删除吗？」→「确定」→页面 29→28→**再点「保存」才提交**（删除是暂存）。

body（`save-batch.request.step2-delete.json` 73,913 B）：**同一接口**，无独立删除接口。`params0` 四组仍 Σ=39：**38 UPDATE + `params0[3].attributeDtoList[6] actionType=DELETE`**（ml=18 dd=2 保留）⇒ **删除=全量回写中把目标 dto 改 DELETE**。

DB：**物理删除**。`WHERE id=` 与 `name=` 均无行，实体 43→42；order_no 43 空缺不回填；`hidden` 列（0:39/1:4）**未使用，行物理消失**。

op_log（写 1）：14:54:27 `action_type=2` / `module=6 sub=11`；**attributeId 这次正确**。elementRecords 给 **23 项全字段快照**：before 全 `-`、after 保留删除前值 ⇒ **删除审计=消失前遗照**。第二证：step2 `get-entity` 目标已不存在（dto Σ=38 vs 39），与 DB 独立互证。

CROSS-VERIFIED（6 项）：body actionType=DELETE ↔ DB 行不存在 ↔ op_log action_type=2+id 正确+23 项快照。

## 3. 组装映射
① 插槽：**不新建**，沿用 `content[3]` 虚拟组；删除后组内 7→6，组保留。
② 来源：编辑沿用 C-4 双通道（总长度→maxLength、小数位数→decimalDigits）；删除=**行级 checkbox**→「删除」→确认弹窗→dto `actionType=DELETE`。
③ 填充：编辑 `actionType=UPDATE`、`uniqueKey=id`、值直传；删除仍发全量 dto，仅目标条改 DELETE 并带完整原值定位。服务端不重编号 order_no、不写 hidden、行物理消失。审计 UPDATE 记差值、DELETE 记删除前全量快照。

## 4. 写计数（写 N＋读 M）
编辑 写**1**（14:48:41）+读 1；删除 写**1**（14:54:27）+读 1 ⇒ **写 2 + 读 2**，真源 `udc_operation_log`。

## 5. UNEXPLAINED
1. UPDATE 的 `attributeId` 指错（=createTime），DELETE 正确；埋点规则未证。
2. 删除两次动作，中间态页面少一行但 DB 未变；暂存层未溯源。
3. ~~39/43 刷新 update_time 与 7 条 dto 不符~~ → **销案**：39 即四组 dto 总数。
4. 删除后 order_no 43 不复用，是否重排未证。
5. 闲置自锁致按钮全 disabled；`/json/close` 收敛标签+reload 可解。

## 修订记录（VERDICT 15:01）
7→39 条回写｜快照 24→23｜update_time 改述整组刷新、时点不可复现｜值层零漂移不证无写入＋补 get-entity 第二证｜机制定性 PASS 维持。边界：CRUD≠物理表≠值域可用≠运行态可访问≠发布链路。

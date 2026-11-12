# C-8｜test2 新增 BOOLEAN 探针字段

2026-10-19 23:39｜app `8704025620829192834`｜实体 `4796455827714164161`(migrationPlan)｜**1 次页面保存**
verdict **PASS-with-deviation**（human 23:44 / ROUTE 23:47）
首次创建 `ff20a95`｜上版 `46bc056`｜本版定稿 `c05f231`+`442645c`｜存档 `artifacts/c8-20261019/`

## 0. DISCREPANCY-C8-1（接受现状不改）
- 预期 name `zzprobeBoolean01` → 实际 **`zizzprobeBoolean011`**（caption `字zzprobeBoolean011`，column `zizzprobe_boolean011`）
- 根因（可证边界）：可证的是**结果字符串** `字zzprobeBoolean011` 与**插入位置**（落在「字段」与「1」之间）；「Ctrl+A 未清空」属复原推断，非按键级事实
- 处置：**接受现状，不改名/不删除/不新建**（再写会破坏 create 快照，把干净创建拆成链式写）
- 影响：**不影响** BOOLEAN 类型创建映射链证据，仅标识不符字面约束
- 复核：`zzprobeBoolean01` 全库 0 行；`LIKE '%zzprobe%'` 2 行 = 本条 + `zzprobeBigint01`

**操作纪律（C-9 起复用）**：双击 → Ctrl+A → **Backspace 清空** → 输入；保存前读 DOM value 核对。

## 1. 只读预查（保存前）
`zzprobeBoolean01` 全库 **0**；实体匹配 ✔；字段 42 / order_no 上限 42；BOOLEAN 对照 max_length=5 min=0 dd=0、widget=Switch。

## 2. 页面证据（LIVE）
树选 `migrationPlan` → 底部「添加」；行数 **28 → 29**。名称单元格双击（placeholder=`请输入字段名称`，默认 `字段1`）；类型单元格双击 → 下拉 16 项 → 输入「布尔」→ **仅 1 项** → Enter，行渲染 `BOOLEAN\n布尔`。保存前 `{"dis":false,"open":0}`；保存走 React onClick。

## 3. 请求存档（LIVE，`artifacts/c8-20261019/save-batch-c8.json` 310,934 B + `manifest-c8.sha256`）
sha256 `0d5b34d5634c0f09a78a417b160dc051e5d083797279ba648155ad572a457013`
4 条 `udc/graphql` 全取到响应（请求B/响应B）：`udcMultiEditLockPost` 431/283；**`udcAttributeGroupOperateBatchPost` 72,973/75,120**（含 DTO）；`udcEntityAttributePresetAttributeCapacityAllAppGet` 282/53,147；`udcAttributeGroupEntityGet` 2,106/70,029。

新字段 DTO（`params0[3].attributeDtoList` 末条）：`actionType=ADD`｜`dataType=BOOLEAN`｜`name/caption` 同上｜`columnName=(空)`｜`publishState=UNPUBLISH`｜`uniqueKey=90733431722523781`｜`widgetConfig` pc/mobile=Switch、list/detail/quickSearch=true。**无 maxLength/minLength/decimalDigits**（见 §4）。

## 4. DB 回读（LIVE）与服务端填充证据
DB `udc_test2.udc_attribute` 新增行（name/caption/column 同 §0）：`id=-1484088835473923815`｜**`data_type=BOOLEAN`**｜`max_length=5`｜`min_length=0`｜`decimal_digits=0`｜`order_no=43`｜`create_time=2026-10-19 23:39:11`；实体 **43** 行。

**证据独立性更正**：响应 body 与读接口 `udcAttributeGroupEntityGet`（72 键，值同上）**同出服务端**，互证价值弱，不构成独立三源。真正支持「服务端填充」的是：**请求 DTO 缺 `maxLength/minLength/decimalDigits`，响应与 DB 却有 5/0/0**——仍标 **UNVERIFIED**（未取服务端代码、未做反例）。

## 5. 写/读计数
页面保存 **1 次**（授权内）；落库 **1 行 INSERT**；graphql 4 条（1 锁+1 写+2 读）；手工 `/service` **0**。

## 6. 页面重进可见性（LIVE）
`Page.reload` → 重选实体 → **29 行**、`found=1`，行渲染 `… 字zzprobeBoolean011 zizzprobeBoolean011 布尔 …` ⇒ 仍可见 ✔

## 7. 限制与未验（UNVERIFIED，不抬级）
- toast 未捕获（`MSG: []`）→ 保存成功以 DB 回读为准
- BOOLEAN 长度 5/0/0 的「服务端填充」为推断，见 §4，未独立验证
- 未发布/未沙箱/未触菜单/未改既有属性
- 其余 7 条 BOOLEAN 行 `update_time` 同刷 23:39:11（A2 全量回写）

## 8. 裁定与结论
human（23:44）裁定 PASS-with-deviation、main ROUTE（23:47）固化；改名 HANDOFF `a-c8-correct-same-boolean-row` 已被取代，**未执行**，零环境写收口。auditor 只复核证据与偏差登记。

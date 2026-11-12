# C-4｜DECIMAL 精度/标度建字段

2026-10-19｜test2｜CDP 9223｜app 8704025620829192834｜实体 migrationPlan 4796455827714164161
**结论：PASS**（三选三 + 三层组装映射全成）

## 0. 实体选择
沿用 migrationPlan：同 entity_id 使 C-3/C-4 基线可直接对照，zzprobeBigint01 值未动（20/0/42）证明未改既有字段值；注记（auditor）：同实体 39/43 行 update_time 被保存整组批量刷新至 14:22:40（另 4 行 hidden=1 保持 10-12），「未动」仅对字段值成立。基线 28 → 29 行。算法（auditor 补）：页面行数 = is_system=0 行数 − ENTITY 类型行数；C4: 35−6=29，C3: 34−6=28，C2: 33−6=27，三切片自洽。

## 1. 表单如何输入（LIVE）
- 新行默认「文本」。**双击**类型单元格才进编辑态（单击只选中行，仅渲染 ant-tag）。
- 编辑态出现 ant-select，16 项：文本/多行文本/整数/长整数/小数/货币/日期/时间/日期时间/布尔/选项集/枚举/附件/实体/流水号/正文。
- 点开下拉后**键盘输入「小数」+ Enter** 选中；点选项坐标不可靠（隐藏容器 rect=-9294）。
- 选中小数后同格出现两 input：`请输入总长度`=precision（默认 20）、`请输入小数位数`=scale（默认 2）。
- 输入须「点击 → Ctrl+A → 逐字符 char → Tab」。`Input.insertText` 只改 DOM value 不触发 onChange。焦点离开后渲染 `小数总长度：18位位数：4位`。

## 2. body 如何承载（LIVE，2026-10-19 14:45 恢复：抓包原件已归档 artifacts/c4-20261019/（8 文件 + manifest 含 sha256，commit b710d8e），main 独立复核 attributeDtoList[6] 7 键与正文一致；请求 99,008 B）
`udcAttributeGroupOperateBatchPost`，字段在 `variables.params0[3].attributeDtoList[6]`，76 键：

| 表单 | body 字段 | 实测 | 单位 |
|---|---|---|---|
| | 总长度 | `maxLength` | 18 | **个数**（字符总位数），非字节。依据（auditor 补强）：①DECIMAL(18,4) 若按字节约 9 字节，18 显非字节；②全库 DECIMAL 样本 20/22/24+2/4，若为字节则精度荒谬；③服务端审计字段名「阈值设置[最大长度]」与表单「总长度18位」同位 |
| 小数位数 | `decimalDigits` | 4 | **个数** |
| — | `minLength` | 0 | 个数 |

body **无 precision/scale 命名**；精度复用 maxLength，标度用 decimalDigits，无后缀无换算。首存（20）`maxLength=20`，改 18 后二次存 `maxLength=18`，`actionType` ADD→UPDATE。

## 2b. 服务端审计层补强（auditor 引入，比 body 存档更硬）
udc_operation_log 独立记录：14:17:22 CREATE「阈值设置[最大长度]-→20，小数位数-→4，类型-→DECIMAL」；14:20:16 UPDATE「最大长度20→18」（仅 1 项）。写链条在平台审计层闭合，与表单输入逐项对应。

## 3. DB 如何落列（LIVE，udc_test2.udc_attribute）
`id=6019556237194179089`，name/caption=`zzprobeDecimal01`/`字段1`
- `data_type`=DECIMAL｜**`max_length`=18**（←maxLength）｜**`decimal_digits`=4**（←decimalDigits）
- `min_length`=0｜`order_no`=43｜`db_column_name`=zzprobe_decimal01｜`publish_state`=1
- `guid`=7107955787235477438｜`widget_config` pc/mobile=InputNumber/list/detail/quickSearch=true
- **udc_attribute 无 precision/scale 列**（SHOW COLUMNS 已验），精度只能落 max_length。

## 4. CROSS-VERIFIED（3/3：body 存档 + DB + op_log 审计层均可独立复核；读接口/页面渲染同窗已在存档内）
name=zzprobeDecimal01｜dataType=DECIMAL｜maxLength=18｜decimalDigits=4｜minLength=0｜orderNo=43｜columnName=zzprobe_decimal01｜entityId=4796455827714164161｜appId=8704025620829192834｜id/guid=6019556237194179089/7107955787235477438 —— 三源逐项一致。

读接口 `udcAttributeGroupEntityGet` → `$.data.data0.data.content[3].attributeDtoList[6]`（72 键）。

## 5. 三层组装映射
**① 插槽**：类型 DECIMAL 决定插槽；行落虚拟组 `content[3]`（attributeGroupId=0、g_l_index=7），与 STRING/BIGINTEGER 同槽，未新建组。
**② 来源**：双输入框是**同格内类型专属联动的次级输入**，非独立表单字段。总长度→maxLength；小数位数→decimalDigits。换类型即销毁重建（切走消失，回来重置 20/2）。
**③ 填充规则**：整数直传无换算；列映射 max_length←maxLength、decimal_digits←decimalDigits，min_length 独立通道恒 0；columnName 服务端由 name 蛇形化（前端提交空串）；orderNo 服务端重编号（43 = 前最大 42+1）。

## 6. UNEXPLAINED
1. `publishState` 请求/读接口 UNPUBLISH vs DB `publish_state=1` → 口径改写（auditor 裁决）：全库 67878 行 publish_state 全为 1，该列零区分度、不承载发布态语义，应记「DB 该列无信息量」，非两层不同源待裁。
2. 首存 ADD → 二次存 UPDATE；uniqueKey 临时值 → 6019556237194179089。
3. `Input.insertText` 对 precision 不触发 onChange，对 scale 曾生效，差异未解释。

## 7. 验收
①保存成功/行可见 PASS：「保存成功」×2，行渲染 18位/4位。
②DB 回读 PASS：max_length=18、decimal_digits=4、DECIMAL。
③reload 后重选实体仍可见 PASS：29 行，值 18/4。
组装映射三成 PASS：第 5 节。

## 8. 写边界
授权对象仅 zzprobeDecimal01；保存 3 次均同一对象。zzprobeBigint01 复读 max_length=20/decimal_digits=0/order_no=42 未改动。`/service` 手工 0 次。


## 7. 补查事实裁决（implementer 14:45 DECISION-RESPONSE，main 裁 14:45）
- **审计 attributeId 错位**：14:20:16 UPDATE 的 path attributeId=5694401663173477663（实为 createTime DATETIME 行），非 zzprobeDecimal01；elementRecords 内容语义正确。裁决：审计埋点取行内邻近 attribute，**今后按 attributeId 追审计不可靠，以 elementRecords 内容为准**；不影响本切片写语义判定。
- **保存=全实体回写**：一次保存 attributeDtoList 共 7 条 dto 全 UPDATE（含 taskId/jindu/isOn/statuss/isConfigTable/zzprobeBigint01/zzprobeDecimal01），对 DB 现值 7/7 零漂移，平台聚合成 1 条审计。裁决：C-4「仅同一对象」表述修正为「每次回写全实体 7 属性，值零漂移」；zzprobeBigint01 未改动结论不变（值与 id 均未变）。

## 修订记录（auditor VERDICT 2026-10-19 14:32 落实，main 落）
- body 层 LIVE → UNVERIFIED（无 HAR/JSON 存档）；补审计层 2b 节（CREATE+UPDATE op_log，链条闭合）。
- 10/10 三源改「DB+op_log 双源全对，标注 2/3」。
- 写边界改「写2+读1」；zzprobeBigint01 注记「值未变、update_time 整组刷新（39/43 行）」。
- publishState 改「DB 该列无信息量」（全库恒 1，零区分度）——销案，不另开切片。
- 行数算法补写（is_system=0 − ENTITY）。
- 边界重申：字段建成 ≠ 值域可用 ≠ 物理表已建（information_schema 设计态查无，预期）≠ 运行态可访问。
- 14:45 增补：body 层恢复 LIVE（存档补齐 b710d8e）、三源回 3/3、补查两事实裁决入 §7。

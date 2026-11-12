# C-3｜BIGINTEGER 字段页面点击新建（migrationPlan）

2026-10-19｜appId `8704025620829192834`｜实体 `migrationPlan`「迁移方案配置」`4796455827714164161`｜CDP 9223｜test2
**判决：PASS**（①②③ 全达成，写边界零越界）

## 一、验收（三选二 → 三选三）

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| ① | 保存提示 + 出现在列表 | PASS | `保存成功`；表 27→28 行，末行 `38\|zzprobeBigint01\|长整数` 起（列序：序号/编码/名称/类型/范围/…/使用场景） |
| ② | DB 回读新行 | PASS | §二 |
| ③ | 重进页面仍可见 | PASS | `/json/new` 重进 → 28 行 hit=27；设计日志新增 `12:04:40 operator-a 实体字段[zzprobeBigint01] 1.0.0` |

③ 证据是平台自身审计流，与 DB 行、列表行互不依赖。

## 二、DB 回读（udc_test2.udc_attribute，SELECT only）

```
id=-6254649020690020123  name=caption=zzprobeBigint01  data_type=BIGINTEGER
entity_id=4796455827714164161  app_id=8704025620829192834
db_column_name=zzprobe_bigint01  max_length=20  min_length=0  order_no=42
publish_state=1  edit=1  guid=3239184580109746931
create_time=update_time=2026-10-19 12:04:40
```

## 三、CROSS-VERIFIED（读接口 ↔ MySQL，10/10 MATCH）

读接口 `udcAttributeGroupOperateBatchPost` 响应 68,281 B，字段在 `$.data.data0.data.content[3].attributeDtoList[5]`，72 键。
MATCH（10 项逐字相同）：id / name / caption / data_type / db_column_name / max_length / min_length / order_no / entity_id / app_id。

## 四、三层组装映射（DECISION 2）

**① 预制层**：类型插槽域 18 项（页面实测枚举）。分组槽在 DB `udc_attribute_group`，本实体 2 组：`系统`(8079203568266071198, preset=1)、`主子表`(2014909714575347206, preset=0)。新字段落 `content[3]`(virtual) 而非系统组 ⇒ 分组为上下文继承。

**② 用户选择层**：实际仅 2 个输入 —— `caption`/`name`（同一单元格驱动两列）、`dataType`（18 选 1）。其余 maxLength/min/max/notNull 等全默认，页面「请设置」= 可选插槽。

**③ 组装层**：请求 `params0{appId, entityId, attributeDtoList[]}`；**子项键集与回读 72/72 完全一致**（零字段请求有、回读无）⇒「固定 72 键模板 + 用户覆写 2 键 + 其余默认/上下文」可被数据完整解释。

**UNEXPLAINED（不倒推为规则）**
- `key`=45362213088735161 / `uniqueKey`=89064959871403571：前端临时标识，落库前丢弃，算法未知
- `index`=38（页内序号）vs DB `order_no`=42：**唯一一处请求↔回读不一致**，服务端重编号
- `createTime`=1792382217996(11:56:57)=点「添加」时刻，DB 取保存时刻；两套时间口径
- `publishState` 请求/回读 `UNPUBLISH` vs DB `1`，映射表未取到
- `attributeGroupId` 请求=系统组 id vs 回读 `"0"`/空：回读对 virtual 组不回报分组
- DB `id`（负雪花）请求侧不可见，服务端生成

## 五、写边界审计

授权写 1 次（一次「保存」）；真实写 mutation 1 条，余 3 条 POST = 锁/容量查询/回读。既有 9 行 BIGINTEGER **零改动**（id 逐行对照全同）；本实体 BIGINTEGER 4→5，app 业务 9→10；本实体 `ziduan%` 残留 **0**（全库 1341 行为存量）。手工 `/service` 0；凭据 0；git 0；仅 9223。

## 六、方法论沉淀（C-3 前置检查）

1. 页面久未操作会进「页面已锁定」，`onClick` 被 `preventDefault` 静默吞 ⇒ 调用成功但零变化。探针首步必验 `body.innerText.indexOf('页面已锁定')`。
2. child-frame 不可 `Page.navigate`（白屏）⇒ `/json/new`(PUT) 或先回 `/main/portal`。重进后树折叠；`onExpand`/`onSelect` 须带 `{node, expanded/selected, nativeEvent:{}}`，缺则抛 `reading 'target'`。
3. `onTabClick(key)` key≠文案（如 `fields`），返回成功≠已切换，须以 `.ant-tabs-tab-active` 回验。

## 七、未验证

Redis/OSS 按 DECISION 3 不查。`publishState` 串→tinyint 映射未取到。本实体 42 行 DB 全 `publish_state=1` 但接口全报 `UNPUBLISH`，两层不同源，未追。

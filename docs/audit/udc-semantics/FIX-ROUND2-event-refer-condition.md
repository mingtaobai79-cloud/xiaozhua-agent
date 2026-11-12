# 实体/规则/菜单 修复 —— 第二轮（事件 / 参照 / 条件结构 / 校验器）

> 承接 `FIX-COMPLETE-entity-rule-menu.md`（02104 / 03104 / 04004 → 构建 1.0.14 SUCCESS）。
> 本轮补齐用户点名的：事件（未建）、参照（只填了名字）、条件结构（全字段错）+ 校验器。

## 1. 事件（`udc_event` 0 → 1）LIVE

**契约反推（校验错误链）**：
```
POST /service/udc/event  缺少字段依次报：
  caption must not be blank; name must not be null
  → name length 1..30, caption length 1..50, sourceId must not be null
  → event_data cannot be empty
```
**成功体**（`udc_event` 列见下）：
```json
{"appId":<appId>, "name":"xzhEvtObj1", "caption":"小爪应用内事件对象",
 "sourceId":<entityId>,            // 事件源（本应用实体）
 "eventData":"79589321340960848",  // 事件数据 = DTO id（本应用 udc_data_transfer_object）
 "eventDataType":1, "actionType":1, "source":1, "messageType":0,
 "enabled":1, "numberFiredOnce":"1"}
→ content = "2806478477352020038"
```
**回读**（`GET /udc/event/{id}`）：
`source=MICRO_FLOW, sourceId=474806313816300867, actionType=UPDATE…, messageType=DEFAULT`。
**唯一约束**：同 eventData 重复 → `UDC_EVENT_0004 Duplicate message identification`（据此判重）。

`udc_event` 列（实测）：`id, action_type, app_id, caption, description, enabled, event_data,
event_data_type, exp_design_data, exp_runtime_data, message_tags, message_topic, name,
number_fired_once, source, source_id, message_type, original_id`。
写端点：`POST /udc/event`（create）/ `create-with-data` / `update` / `update-with-data` / `delete`；

## 2. 参照（`udc_refer_config` 0 → 1）LIVE

**契约（全库 1133 行样本反推）**：
`config_info` 是 JSON，五键齐全才有意义：
```jsonc
{
  "columns":  [{"width":120,"widthType":"px","path":[{"fieldId":<fid>,"entity":{"id":<eid>,"appName":null}}],"lineLimitedContent":"custom"}],
  "search":   [{"path":[{...}]}],
  "orders":   [{"path":[{...}],"direction":"ASC|DESC"}],
  "entities": ["<entityId>"],
  "whereCond":[{"type":"GROUP","uuid":"...","conditions":[...]}]
}
```
**成功体**：
```json
{"appId":<appId>,"caption":"小爪实验实体参照","type":"List","terminalType":1,"isDefault":true,
 "sourceType":0,"entityId":<eid>,"relationEntity":<eid>,"relationApp":<appId>,
 "configInfo":"<上述 JSON>","displayName":"<path JSON>","pageId":"0","detailPageId":null,"sourceRefer":""}
→ content = "8511242037609849268"
```
**回读**：`caption/type=List/entityId/isDefault=true/terminalType=PC`，`configInfo` 五键逐一对上。

写端点：`POST /udc/refer-config/create`（另有 `create-config-info` 带多端参照）。
`udc_refer_config` 列：`id, app_id, caption, config_info, detail_page_id, display_name, entity_id,
is_default, type, terminal_type, group_id, detail_page, source_type, page_id, relation_app,
relation_entity, source_refer, pull_display_name, original_id`。

## 3. 微流程条件结构 —— 按真实样本重写 + 落库 LIVE

真实样本（`udc_microflow_info.id=4405407084014816629`）逐键：

```jsonc
{"type":"GROUP","uuid":"...","conditions":[
  {"type":"CONDITION",
   "leftParam":{"id":"<dtoFullName>.<field>","type":"OBJECT","javaType":"java.lang.Boolean",
                "dto":"_enabled","field":"enabled","desc":"是否启用",
                "dataType":"BOOLEAN","multiSelect":false},     // 8 键
   "operator":{"value":"EQ","desc":"="},                      // 只有 value+desc
   "rightParams":[{"type":"CONSTANT","value":true,"desc":true}],  // value 保留原类型；desc 是显示值
   "uuid":"...","logicalOperator":"AND"}]}                    // 组内第 2 条起必填
```
**LIVE**：按此结构替换 `小爪REST微流程` 的 RETRIEVE_ARRAY.condition（3 条件：BOOLEAN EQ / STRING RLIKE / INTEGER GT，第 2、3 条带 `AND`）
→ `checkSchema` + `update` 成功 → 回读与真实样本逐键一致。

## 4. 校验器补齐（★ 这是"我为什么没拦住"的正面回答）

`components/udc/microflow_model.py::_validate_condition` 原来**只查 `operator.value`**，
上述 4 类错全部放行（`{name,value}` 的 `value` 恰好合法）。本轮新增：

| 新检查 | 拦什么 |
|---|---|
| `operator` 必须含 `value`+`desc`，**含 `name` 报错** | 我原来写的 `{name,value}` 结构 |
| `leftParam` 必须 8 键（id/type/javaType/dto/field/desc/dataType/multiSelect） | 我原来只写 4 键 |
| `rightParams[i]` 必须含 `value`+`desc`，**含 `key` 报错** | 我原来的 `{key,type,value}`；缺 `desc` 即前端空槽位 |
| 组内第 2 个条件起 `logicalOperator` 必填 | 我原来完全不查（ConditionService.checkDetail 契约） |

**连带**：测试夹具（`test_microflow_condition_constraints._cond_node` / `test_author_from_constraints._cond`）
当初固化的正是**我错的结构** → 校验器一收紧就 FAIL（先是我的补丁有 `NameError`，修掉后夹具暴露）。
已按真实结构改夹具，微流程套件 **37/37 PASS**。

提交：`1709180 fix(udc): 微流程条件结构校验补齐（真实样本键集）+ 测试夹具对抗真实结构`

## 5. 当前检测面

```
ERROR  = 0        （02104/03104/04004 全清）
WARN   = 9        04003×7 + 04009×1 + 08100×1
构建   = 1.0.14 SUCCESS
```

**WARN 分析**：
- `04003` 的 7 条微流程 `state=10`（**草稿**）；构建通过的 21 条是 `state=20`。
  `checkSchema/update` 后 state 仍 DRAFT ⇒ 该警告需通过设计器"保存并提交"（前端通道）或发布才消；
  **不阻塞构建已实测**（1.0.14 SUCCESS 时这 9 条 WARN 全在）。
- `08100` 对象 `-1628253460115858501` 是**空目录**（无子节点）→ 无处设默认页；属实验遗留。

## 6. 本轮产物

- `scratch/entity_constraints_test.py`（notNull/uniqueness/defaultValue/dataFormat LIVE）
- `scratch/refer_create.py`（参照 create + configInfo 回读）
- 事件 create/回读：inline（见 §1 契约）
- 提交 `1709180`（校验器 + 夹具）

## 7. 未做（下一批）

1. 04003/08100 的彻底消除（需前端提交通道或清理空目录）。
2. 计算值（`calculate` + `default_value_expr_design` 表达式引擎）—— 用户点名，仍未测。
3. 事件两类（应用内/应用间）、事件监听 4 种源（实体事件/消息总线/自定义对象）。
4. 生单规则（`udc_data_flow`/`DataFlowDesignController`）、扣减规则（`udc_deduction_*`）—— 用户点名，未动。
5. 菜单写链补全（default_page/绑页面/树回读）。

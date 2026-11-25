# 实体 / 规则 / 菜单 三模块修复清单（证据对齐版）

> 触发：用户指出我把「契约级/文档级」当成「打通级」，进度虚高。
> 本文件**不用文档结论**，每条都标注实测来源（DB 查询 / REST 调用 / 字节码行 / 检测面）。
> 应用：datamigration9000000000000000001（test2）。基线时刻：2026-10-15 19:xx +08。

---

## 0. 先认错（口径纠正）

| 我此前的说法 | 实际情况（实测） |
|---|---|
| "实体 90%、设置/枚举 ✅" | **枚举建错了域**：`POST /udc/udc-enum` 建的是「选项集」(udc_enum)，CTPENUM 字段要的是「平台枚举」(ctp_enum)。字段级 LIVE 端到端**从未做过**。 |
| "规则 85%" | 微流程只有**建/改**验证过；节点逐类、条件结构、事件监听配置**多数未验**。且我造的条件结构**全字段错**。 |
| "菜单 80%" | 只验过"建菜单成功"；**URL 直接复制、页面绑定不换实体、复制过来的页面无规则无事件**等问题未处理。 |

**根因**：我把「REST 调用返回 BOOT_0000」当成「功能可用」，把「契约已登记」当成「已测试」。
BOOT_0000 只证明**接口收下了**，不证明**语义正确**、**检测通过**、**构建通过**、**运行可用**。

---

## 1. 实体模块

### 1.1 枚举字段报错（阻断级，已定位根因）

**症状**：字段列表红色感叹号；一致性检查 `UDC_CE_ENTITY_02104`「字段关联枚举不存在」，阻断级。

**根因（字节码 + DB + LIVE A/B 三重）**：
`udc-biz-5.3.517` `AttributeMatchDetectionUtils`（CFR）：
CTPENUM 字段的 `relationEntity` 会被当作**平台枚举实体主键**，自动拼前缀
`com.seeyon.boot.starter.enums.domain.entity.CtpEnum.<值>`。

| 实验 | relation_entity 指向 | 02104 |
|---|---|---|
| A | `udc_enum.id=3934748939202274853`（选项集） | **1**（阻断） |
| B | `ctp_enum.id=343286139204944935`（平台枚举） | **0** ✅ |

**两域对照**（udc_test2 实测）：

| 域 | 表 | 端点 | 本应用行数 | 我的契约清单是否覆盖 |
|---|---|---|---|---|
| 平台枚举 | `ctp_enum` / `ctp_enum_item` / `ctp_enum_category` | `EnumController`(base=enum) / `EnumItemController` / `EnumCategoryController` @ **boot-starter-enums-5.3.308.jar** | **371** | ❌ **完全没有** |
| 选项集 | `udc_enum` / `udc_enum_item` / `udc_enum_category` | `UdcEnumController` @ udc-web | 1（我建的） | ✅ |

**修复动作**：
1. 实测 `boot-starter-enums` 的 create 路径（`/service/...` 前缀待网络恢复确认）→ 为本应用建平台枚举。
2. `expEnum.relation_entity` 指向它（四列齐：relation_entity / _entity_name / relation_code / relation_app）。
3. 重算检测 → 02104 应保持 0。
4. **契约清单补 boot-starter-enums 域**（3 控制器），设置域进度口径重算。

### 1.2 字段约束列全未设置（用户指出）

`udc_attribute` 实测（6 个实验字段）：

| 字段 | is_not_null | uniqueness | default_value | calculate | multi_select |
|---|---|---|---|---|---|
| expText | 0 | 0 | NULL | 0 | 0 |
| expEnum | 0 | 0 | NULL | 0 | 0 |
| expMembers | 0 | 0 | NULL | 0 | **1** |
| expDate | 0 | 0 | NULL | 0 | 0 |
| expNum | 0 | 0 | NULL | 0 | 0 |
| expFlag | 0 | 0 | NULL | 0 | 0 |

⇒ **必填 / 唯一 / 默认值 / 计算值 全部没测过**。计算设置（表达式引擎）完全未触碰。
需补：`is_not_null=1` / `uniqueness=1` / `default_value` / `default_value_expr_design` / `calculate`（含 formula 表达式）逐项 LIVE 验证 + 回读。

### 1.3 事件页签：0 行（用户指出）

`udc_event WHERE app_id=...` = **0**。
「对象定义」页有两类：**应用内事件对象 / 应用间事件对象**（截图显示均为「暂无数据」）。
⇒ 事件从未创建。端点：`EventController` base=`udc/event`（create / create-with-data / update / update-with-data / delete / list / list/business-event / list/events）。

### 1.4 索引页签：有数据但非我建

`udc_index` = 4 行（本实体 1 行）。需确认是否系统预置、以及我的创建链是否可用。

### 1.5 参照页签：0 行（用户指出）

`udc_refer_config` = **0**。截图里我只填了「参照显示字段」名称，**未走下一步**（选择数据源 / 选择字段 / 显示列 / 条件 / 排序 / 搜索）。
端点：`ReferConfigController` base=`udc/refer-config`（create / create-or-update / create-config-info / update-config-info / …）。

---

## 2. 规则（微流程）模块

### 2.1 我造的条件结构全字段错（用户指出「筛选条件这个都错了」）

真实样本（`udc_microflow_info.id=4405407084014816629`，标品）vs 我造的：

```jsonc
// 真实
"operator": { "value": "EQ", "desc": "=" }                      // 无 name
"leftParam": { "id": "<dtoFullName>.<field>", "type": "OBJECT",
               "javaType": "java.lang.Boolean", "dto": "_enabled",
               "field": "enabled", "desc": "是否启用",
               "dataType": "BOOLEAN", "multiSelect": false }     // 8 键
"rightParams": [ { "type": "CONSTANT", "value": true,
                   "desc": true } ]                              // 布尔态非字符串
// 组内第 2 条起：
"logicalOperator": "AND"
"type": "GROUP", "uuid": "<uuid>"

// 我造的（错）
"leftParam": { "field": "expFlag", "dataType": "STRING", "id": "...", "type": "OBJECT" }  // 缺 4 键 + BOOLEAN 标成 STRING
"operator":  { "name": "EQ", "value": "EQ" }                                              // 多 name 缺 desc
"rightParams":[ { "key": "expFlag", "type": "CONSTANT", "value": "false" } ]              // key 应为 desc；布尔写成字符串
// 无 logicalOperator
```

⇒ 截图里 `实验开关 = [空下拉] true` 的"空槽位"即 `rightParams[0].desc` 缺失 + dataType 错误所致。

**我的校验器为什么没拦住**（`microflow_model.py::_validate_condition`）：
- 只查 `operator.value` 是否在值域 → `{name:E, value:E}` 的 `value` 恰好合法，**放行**。
- 从不检查 `operator.desc`、`rightParams[].desc`、`leftParam.id/javaType/dto`、`logicalOperator`。
- `leftParam.dataType` 与真实字段类型**不做交叉校验**（BOOLEAN 标成 STRING 未被发现）。
⇒ 校验器需按真实样本补齐：operator 键集、leftParam 8 键、rightParams 键集、逻辑算子必填、dataType 与实体字段交叉核对。

### 2.2 事件监听：只覆盖了 2/4 种源（用户指出）

`udc_microflow_info` 里 trigger_type=0（事件监听）共 **2** 条：

| 微流程 | trigger.type | messageInfo.messageSource | 语义 | nodes |
|---|---|---|---|---|
| 小爪标品事件监听 | BUSINESS_EVENT | **EVENT**（`AfterUpdateEvent`，currentType=实体） | 实体事件 ✓ | 3 |
| 小爪实验事件监听 | BUSINESS_EVENT | **MESSAGE**（`BpmStartEvent`，topic=BPM） | 事件总线/消息 ✓ | **0（空）** |

未覆盖：
- **自定义对象监听**（messageSource/触发对象为 DTO）—— 未测。
- 「应用内事件对象」（`udc_event`）—— 0 行，未建。
- 事件选择弹窗曾报 `属性entityId的值反序列化为Long类型时失败`（截图 56）—— 未定位。

两条监听均被检测面报 **WARN `UDC_CE_MICRO_FLOW_04003`「未保存的微流程或者页面规则，这可能会影响调用」**（各 1 条，共 7 条 WARN 里占 6 条）。

### 2.3 「已设置」点击报错 + 节点映射未按规矩（用户指出）

数据转换节点（截图 57）：映射关系显示「已设置」，但点击报错；且 mapping 的边界规矩未落实。
需按 `DATA_MAPPING` 权威结构重做：`mappingRule = {uuid, targetType(ENTITY|DTO), mappingRows[{uuid, targetField{path}, mappingMode(REFERENCE|CONSTANT), value}]}`。
（我 2.1 那种"结构形状对、字段错"的同源问题在此节点同样存在。）

### 2.4 活动节点未逐类验证

动作面板共 **7 大类**（逻辑/变量/映射/列表/数据/基础服务/数据加工），仅 `microflow_constraints.py` 里有 **30** 个 ACTIVITY 值域的静态登记；**逐类 LIVE 验证只做了 3 个**（RETRIEVE_ARRAY / DATA_MAPPING / DELETE_ENTITY）。
⇒ 余 27 类未验证。

### 2.5 checkSchema 是浅校验（已证）

注入非法 actionType / operator / paramType / 空 nodes → 全部 `check:true`。**不能当校验器用**。

---

## 3. 菜单模块

### 3.1 实测现状（`udc_function_node`，本应用）

我建的在 `parent_id=7853445889453184321`（`xzhMenu951398`）下：

| id | name | type | page_type | url | default_page |
|---|---|---|---|---|---|
| 7853445889453184321 | xzhMenu951398 | 0(目录) | — | — | — |
| -4342605165649097565 | 小爪实验菜单951440 | 0 | — | xzhpage951440 | 1909192145328011364 |
| -4731096574698452042 | 小爪实验菜单958006 | 0 | — | xzhdetail958006 | -5295514491818198775 |
| 2785741575330086282 | 小爪实验菜单958033 | 0 | — | xzhdetail958033 | -1926650581124732806 |

节点：4 目录 + 3 页面（type=1）。

### 3.2 用户指出的问题（实测确认）

1. **`url` 直接复制**：菜单 url 与页面 `page_url` 同值 → 若目标是"不同实体不同字段"，此复制式绑定不成立。
2. **「测试连接」按钮/事件被整页复制过来**：导致详情页带上了不属于它的 widget 事件 → 检测面 **`UDC_CE_PAGE_03104`「控件事件关联微流程不存在」×4**（958006/958033 各 2 条：`[工具栏]`、`[测试连接]`）。
3. **复制来的页面无规则无事件**：`udc_page_info` 里 958006/958033 原 `schema_state=0`（空壳），我填了模板 schema，但模板里的微流程序号是别的应用的 → 03104。
4. **default_page 未设**：检测面 **WARN `UDC_CE_FUNCTION_NODE_08100`「Default page not set」**（小爪验收菜单）。
5. 菜单域从无 LIVE 的"新建节点→绑页面→设首页→存"完整链验证，只有"建菜单成功"。

### 3.3 修复动作

1. 详情页事件清理（去 `[工具栏]`/`[测试连接]` 的 03104 来源），或补上对应微流程。
2. `default_page` 逐节点设置。
3. 菜单 url 与页面绑定按"目标实体/页面"重设，不做复制式赋值。
4. 补菜单写链 LIVE：节点创建/页面绑定/首页设置/树形回读。

---

## 4. 检测面口径（此前统计不全）

**实测 16 行 = 9 ERROR(阻断) + 7 WARN**（我之前只报"7 ERROR"，漏了 WARN 与严重度分档）：

| 级别 | 码 | 对象 | 消息 |
|---|---|---|---|
| ERROR | UDC_CE_ENTITY_02104 | 实体/字段 expEnum | 字段关联枚举不存在 |
| ERROR | UDC_MICRO_FLOW_04004 ×4 | 微流程953182 入/出参 | 依赖应用已删除 / OpenApi标识不匹配 |
| ERROR | UDC_CE_PAGE_03104 ×4 | 详情958006/958033 | 控件事件关联微流程不存在 |
| WARN | UDC_CE_MICRO_FLOW_04003 ×6 | 6 条微流程 | 未保存的微流程或页面规则 |
| WARN | UDC_CE_FUNCTION_NODE_08100 | 菜单 | Default page not set |

严重度：① 阻断（阻塞发布，需立即修复）② 严重 ③ 警告（不阻塞发布）。
UI 面板「重新检查」按钮 = `POST /udc/application/do/detection`（重算）；`search/detection` 只读快照。

---

## 5. 环境阻塞（如实记）

| 面 | 状态 |
|---|---|
| MySQL `udc_test2` | ✅ 通（600s 内多条 SELECT 正常） |
| Nacos | ✅ 通 |
| 跳板机 SSH `10.0.0.1:22` | ❌ `Connection timed out` |
| Redis | ❌ 超时 |
| `https://lowcode-test2.example.com/service/*` | ❌ 全 **403**（浏览器内 fetch 同样 403；`/main/portal` 200） |

⇒ 环境侧网络/网关异常，**非脚本问题**。受影响：平台枚举 create 实测、检测重算、构建复跑、CDP 取证。
DB/Nacos 可用，故本轮以 DB + 本地字节码完成根因定位。

---

## 6. 修复顺序（按阻断优先）

1. `02104` 平台枚举归属（阻断，根因已定，待端点实测）
2. `03104` 详情页事件（阻断）
3. `04004` 微流程入出参（阻断，4 条）
4. `04003` 6 条微流程"未保存"警告
5. `08100` 菜单 default_page
6. 实体 1.2/1.3/1.5（必填唯一默认值计算值 / 事件 / 参照）
7. 规则 2.1 条件结构 + 校验器补齐；2.2 监听覆盖面；2.4 余 27 节点
8. 菜单 3.3 写链补全

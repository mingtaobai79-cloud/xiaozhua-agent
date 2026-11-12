---
name: xiaozhua-udc-microflow-generation
description: Use when 建/改/验 UDC 微流程（前端搭节点、建单、出入参、检查校验）。
version: 1.3.0
author: 小爪
license: internal
metadata:
  hermes:
    tags: [udc, microflow, graphql, cdp]
    related_skills: [xiaozhua-udc-runtime, xiaozhua-low-code-environment, udc-trace-to-api]
---

# UDC 微流程构建与验收


## ⛔ 铁律零：生成后必须做的四件事（用户严令，每次生成都执行）

**构造器/组装器产物一律不算完成。** 生成流程后必须依次做：

### 1. 前端点「检查」+ 逐节点点「确定」

- 设计器的「检查」= 应用级一致性检测；单流程结构校验在 publish 的 checkSchema 里，两者口径不同。
- 每个节点必须点开抽屉看一眼：红字、空黄框（必填未填）、`isCompleted=false`（红节点）。
- **控制节点（BRANCH / FOR_EACH / END）点「确定」会把顶层 endNode 搬进 nodes**，绝不动它们，看完点「取消」。
- 验收完必须重新 publish：UI 一进编辑态就把 RELEASE 打回 DRAFT。

### 2. 必填必须填满（两份清单都要满足）

- 后端 `checkSchema` 是浅校验；前端「保存并提交」是深度校验，缺必填时**零请求**（不发 UpdatePost）。
- 定位只认浏览器 console 里「值为空的必填属性」那一行，别猜。
- 已知两套必填不一致的节点见 `references/node-shapes.md`（必填字段契约 / 必填两套）。
- 契约表在 `components/udc/microflow/node_contracts.py`（G23），生成时就按它填，别等 UI 报。

### 3. 检查要简要，但必须真跑

- 汇报可以简短，但动作必须真执行；断言只认后端回读或 redux store，不认脚本返回值。
- 一条命令：`verify.py` 的 `prove(app_id, mid, host, cookie)` → publish errors + isCompleted/抽屉红字 + 参数名 + 检测明细。

### 4. ★★ 读不到 ≠ 通过（本条踩过三次，都是同一个错）

**「检查没报错」不等于「检查跑过」。** 任何校验下结论前先问一句：
这个工具**真的读到了数据**吗？空结果、旧结果、默认值，都不算证据。

三次实测，同一个错误换了三张皮：

| 看着像通过 | 实际 | 正确做法 |
|---|---|---|
| `create` 成功 | 只证明结构能被收下，语义没验 | 必须跑到 `publish`，`errors=[]` |
| UI 读回 `nodes={}` → 「0 个未完成节点」 | 编辑器入口落错页，根本没读到 | 先判 `nodes` 非空，空就报错 |
| 构建状态一直是旧 `FAIL` → 「构建卡住」 | 查的接口不对，平台侧早已 SUCCESS | 按 deployId 查，不用全局快照 |

**节点验证的最小闭环**：

```
构造 → create → 回读（确认落库形态） → publish（errors 必须为空）
```

21 类节点全组 create 都 OK 之后，publish 才暴露的真错误：

```
mapping.value.type → DATA_INVALID                （写成 OBJECT，语料里没有）
mapping.value.selectParam.dtoType → PROPERTY_IS_REQUIRED
```

只有 `publish ok=True, errors=[]` 才能标 SCHEMA_VERIFIED；只跑 create 的一律算
CONSTRUCTED，不许写进「已验证」列表。

汇报口径同样受这条约束：不说「测试通过」，说「publish errors=0」
或「UI 读到 N 个节点、0 未完成」。**给出数字，让用户能自己核对**。

### 4b. ★★ 新写的测试必须先注入故障，看它会不会红

**「测试通过」和「测试有效」是两件事。** 一条从没失败过的测试，很可能什么都没断言。

实测：给「闸门编号必须写进文档表格」写契约测试，第一版全文正则扫 `G34`——
删掉表格里那一行，测试**仍然 passed**，因为编号在后面的详解章节里也出现过。
改成只认表格行（`| G<n>` 开头）后才真正生效。

这与「规则插错函数」是同一个错误的两个面：**验证了「文本存在」，而不是「机制生效」**。

所以每写一条断言/闸门/校验，交付前做一次：

```
① 构造一个应当被它拦住的输入
② 跑，必须红，且报错信息指到具体那一条
③ 恢复，必须绿
```

三条缺一条都算没验。尤其是「双向契约」「一致性检查」这类**断言存在性**的测试，
最容易写成永远为真——先删一个元素看它报不报。

### 4.1 ★★★ 运行日志的 output 是「流程结束时的对象快照」

**不要用运行日志里任何节点的 output 去断言中间状态。**

实测：`CREATE(123) → RETRIEVE → CHANGE(999) → RETRIEVE` 的流程，
日志里「查初始值」那个 RETRIEVE（在 CHANGE **之前**执行）显示 `lastOffset=999`，
而同一份数据里 `version=0`（下一个 RETRIEVE 是 `version=1`）。

原因：`CHANGE_ENTITY` 就地修改了 RETRIEVE 返回的**同一个 DTO 对象**，
日志在流程结束时才序列化，看到的是被改过的值；`version` 只在读库时刷新，
所以留下「version=0 + lastOffset=999」这种自相矛盾的组合。

| 想证明 | ❌ 不能用 | ✅ 必须用 |
|---|---|---|
| CREATE 写入值 | 日志里 CREATE 的 output | 数据库行 |
| CHANGE 生效 | 日志里「更新成功」 | **数据库行**（改后值 + version + update_time） |
| 任何中间态 | 日志里任意节点 output | 独立快照（另起流程查 / 写入另一个变量） |

★ 推论：`success=true` 只说明没抛异常。写节点的结论必须落到**物理表**。
判据要带对照组：查被删记录得 0 行，同时查一条已知存在的记录得 1 行，
否则「0 行」可能只是表本身是空的（本轮就踩过：`migration_checkpoint` 全表 0 行，
差点当成「删除成功」，实际那张表根本不是该实体的表）。

### 4.2 ★★ 写节点：动态记录只能靠 SELECT_PARAM 删除

`DELETE_ENTITY` 有 `CONDITION` / `SELECT_PARAM` / `IDS` 三种模式：

- `CONDITION` 的条件右值**只能是常量**。填节点引用（SelectParam）→ publish 被拒
  `BOOT_1001 Parameter Error`，响应 `data=null` **没有任何字段级提示**，只能二分定位。
- 要删「刚创建的那一条」，用 `mc.step("delete_entity", from_node="r")` →
  生成 `deleteType=SELECT_PARAM` + `selectParam` 引用前序 DTO 出参，
  并去掉 `app`/`structure`/`condition`/`methodLegal`（混带也会被拒）。

闸门 **G36** 已拦这两种错法。相关事实见
`core/facts/udc/microflow/node-change-delete-entity.md`。

### 4.3 ★★ 批量写：无 attrs、出参是计数、插入的列表元素不能带 id

`CREATE_BATCH_ENTITY` / `CHANGE_BATCH_ENTITY` 的真实形态（全仓 95 个样本一致）：

- **没有 `attrs`**（0/95 带 attrs）。批量节点不做字段映射。
- 出参是 `dataType=INTEGER / type=OBJECT`，即**影响行数**，不是 DTO 数组。
- 值来自**列表元素自带的字段值**。

两个必踩的坑：

1. **`CREATE_BATCH` 的列表元素必须没有 id。**
   直接拿 `RETRIEVE_ARRAY` 的结果去批量插入 → 运行时 `违反主键约束`
   （元素是已落库的 DTO，会拿原 id 再插一遍）。
   正确链路：`CREATE_VARIABLE(entity, fields=…)` → `create_list_entity` →
   `change_list_add` → `create_batch_entity`。

   ★ **用户偏好（用户）：循环内写子表用批量写，不要循环内逐条 `create_entity`**。
   明细/轨迹/质检记录这类「循环遍历源列表、每项写一条子表记录」的场景，
   逐条 `create_entity` 每轮一次 INSERT（N 次）；批量写是循环内造对象、循环外一次 `CREATE_BATCH_ENTITY`。
   intent_draft DSL 形态：

   ```python
   {"kind": "create_list_entity", "entity": "物流轨迹", "title": "轨迹列表"}  # 循环外建空对象列表
   {"kind": "for_each", "list": "items", "body": [
       {"kind": "create_variable", "entity": "物流轨迹", "fields": {        # 造未落库对象
           "trackingNo": {"field": "ship"}, "eventCode": {"const": "PICKUP"}}},
       {"kind": "change_list_add", "list_node": "轨迹列表", "item": "轨迹对象"},  # 加进列表
   ]}
   {"kind": "create_batch_entity", "entity": "物流轨迹", "list_node": "轨迹列表"}  # 循环外批量新增
   ```

   ★ `create_variable(entity, fields)` 的 fields 必须由 `_do_create_variable` 透传（走
   `_entity_fields` 把 const/field/arith 转值槽）——早期逻辑图层只传 entity 不传 fields，
   DSL 层 fields 被静默丢弃，批量写链路走不通（2026-11-04 已修，commit 31e04674）。
★ **子表外键引用父表 id：父表实体必须在循环前先创建，否则子表外键落库为 0**（2026-11 制造业采购明细 poId=0 暴露）。循环内 `create_variable(entity, fields)` 造子表对象、fields 里含父外键（`poId:{"field":"po"}`）时，若父表 `create_entity` 排在循环**之后**，子表对象引用不到父 id → 外键写 0 → 下游按外键查子表查不到（收货明细 0 行、收货库存不更新）。父表字段若依赖循环累加（如采购订单 totalAmount 依赖循环内累加），先建父表（该字段写 const 0），循环累加后循环外 `retrieve` 回读 + `change_entity` 回填。
2. **`CHANGE_LIST` 没有出参**（真实样本 `output` 恒为 null，原地改列表）。
   下游批量节点要引用**它操作的那个 CREATE_LIST 节点**，引用 CHANGE_LIST 会让
   `selectParam.outputName` 为空 → publish 被拒 `PROPERTY_IS_REQUIRED`（闸门 G37 拦）。

批量节点相关事实：`core/facts/udc/microflow/node-batch-entity.md`。

### 4.4 ★★★ 流程是单事务：一个节点失败，整条流程回滚

实测：8 节点流程前 7 个全 success（含 2 次 CREATE 返回真实 id、CHANGE、CHANGE_BATCH
返回「批量更新成功：2条数据」），第 8 个 `CREATE_BATCH` 违反主键 → 流程 success=False，
**前面所有写入在库里查不到**（两个 id 均 0 行，同表其他数据 21 行说明没查错表）。

推论：
- **不能把「要取证的节点」和「可能失败的实验节点」放进同一条流程**，
  实验节点一失败，取证节点的数据就没了。
- 日志里的节点 success 不等于数据已落库。
- 外部调用（接口/消息）的副作用**不会**随事务回滚，失败清理要考虑它们。

### 4.5 ★★★ 节点 type 必须匹配 actionType，否则**静默丢弃**

2026-11-02 实测，BREAK 写成 `type="ACTIVITY"` 的后果：

```
构建 SUCCESS 224s / publish True / 运行 success=true / 每个节点都 success
库内：对照循环 3 行、实验循环 3 行   ← BREAK 完全没生效
```

**零报错**。这是最难查的一类：所有闸门绿、日志全绿，只有业务结果不对。

机制（字节码 + 代码生成模板双证）：

- 解析器 `MicroFlowParser.node()`：`MicroFlowNodeTypeEnum.valueOf(type.toUpperCase())` 选解析器。
  枚举只有 `CONDITION / FOR_EACH / BRANCH / CUSTOM_ERROR / END / ACTIVITY / FOR / BREAK`。
- 代码生成模板 `MicroFlowDomainService.java.ftl` 按 **`node.type`** 分发：
  `nodesLogicHandler` 里 BREAK 是 `<#case "Break"> break;`，
  Activity 分支的 21 个 case 里**没有** BREAK / CUSTOM_ERROR。

→ `type="ACTIVITY"` 的 BREAK/CUSTOM_ERROR 落进 Activity 分支 → **什么都不生成**。

规则：**逻辑节点的 `type` 必须等于 `actionType`**（`BREAK` / `CUSTOM_ERROR`）。
闸门 **G38** 拦。同时 G16 的 ACTIVITY 族里**不能**包含 CUSTOM_ERROR（旧版错了）。

★ **G38 的例外（2026-11-03 验收修正）**：真实样本里 **CUSTOM_ERROR 无 actionType**
（`node-contract-from-samples.json` keys 不含 actionType，只有 type=CUSTOM_ERROR），
**BREAK 有 actionType**（32/32 都有）。所以 G38 现在：BREAK 缺 actionType 仍拦；
CUSTOM_ERROR 缺 actionType 放行（`normalize_node` 会剥 CUSTOM_ERROR 的 actionType，
别在构造器里硬加回去）。

验证方式（同一条流程内自证，别跨流程比）：
```
FOR_COUNT(1..3) body=[CREATE_ENTITY(taskId=MARK+'N')]          → 期望 3 行
FOR_COUNT(1..3) body=[CREATE_ENTITY(taskId=MARK+'Y'), BREAK]   → 期望 1 行
```
实测修复后 3 : 1。事实见 `node-break.md`。

### 4.6 ★★★ 应用内事件投递：自建订阅流程就能验到载荷级

`PUBLISH_BUSINESS_EVENT` 的 IN_APP 形态生成的是：

```java
eventPublisherHelper.publishEntityEvent(dto, EventPublisher.EventPhase.TRANSACTION_COMMIT_SUCCESS);
```

走**进程内 EventBus，不写任何表**（`ctp_mq` 投递前后都是 0 行）。所以「查表看有没有记录」
这条路走不通 —— **但订阅者可以自己建**，建完就能验：

```
A 发布端：… → CREATE_ENTITY → PUBLISH_BUSINESS_EVENT(attrs 填 eventCode/remark)
B 订阅端：BUSINESS_EVENT 触发器 → CREATE_ENTITY(taskId ← 触发条件.eventCode,
                                                 sourceTable ← 触发条件.remark)
```

读侧断言不是「B 跑过了」，而是**B 写库的字段值 == A 投递的值**（实测 `P6SV01` / `p6-svc` 逐字相等，
与 A 的流水号写入同一秒）。这才叫载荷级证明。

订阅流程的两个形态要点：

- 触发器 `type="BUSINESS_EVENT"` + `messageInfo.messageSource="MICRO_FLOW_EVENT"`，
  `eventDataFullName` / `eventMfCustomDtoName` 填事件 DTO 全名，`eventName` / `currentId` 是
  **小写类名**，`currentType="microflow"`；`output` 与 `messageInfo.output` 都是该 DTO。
- 订阅端引用事件字段**不能**按普通节点写：必须是 `position="children"`，
  `key="<触发output名>_<dto全名>.<字段>"`，`path="<dto去点>.<字段>"`，`dtoType="CUSTOM"`。
  按普通引用会抛「引用了尚未执行的节点」——`_ref_value` 里对 `_BUSINESS_EVENT*` 走专门分支。

事件对象用 `udcMicroflowSearchEventListPost` 拿（body 是**顶层** `{appId, appName}`，
塞进 `params` 会报 `appId must not be null`）。细节见 `references/node-publish-event.md`。

★ **逻辑图 DSL 层事件订阅链路（2026-11-04 RMA 售后 EVT-01 落地，三个缺口已补）**：

- 订阅端 trigger 用 `mc.trigger_mf_event(event=evd, out_param_name=…)`（MICRO_FLOW_EVENT 源，
  区别于 `trigger_event` 的 ENTITY 事件）。evd 从 SearchEventListPost 行 + fullName 派生：
  `eventDataFullName/eventMfCustomDtoName=fullName`、`name=fullName.split('.')[-1].lower()`、
  `sourceId=行 id`、`appName=应用名`。
- 订阅端引用事件字段用 `{"input": "字段名"}`（如 `{"input": "bizKey"}`），并先
  `res.bind_flow_input(trigger["output"], fields=lr.dto_attributes(...))` 绑定事件入参字段——
  不 bind 就 G31 报「引用 _BUSINESS_EVENT_xxx 悬空」。
- 发布端 `publish_business_event` 的 attrs 在 DSL 层写 **dict**（`{"eventCode":{"const":...}}`），
  `_event_attrs` 自动转 `[{attrType: field_attr, value}]` 列表（拉事件 DTO 字段元数据）；
  event 字段引用前序节点用 `{"field": "retApp.id"}` / `{"field": "ship"}`。
- ★ G31 收事件入参要读 `schema["input"]`（BUSINESS_EVENT 的 input = trigger.output 事件数据，
  trigger.input 恒 None），只读 `trigger.input` 会把事件字段引用误报悬空。

### 4.7 ★★ 删流程不会停掉已注册的定时任务

实测：流程删掉（平台列表已无）后，`ctp_job_info` / `ctp_job_simple` 都标了 `is_delete=1`，
调度器**仍在按缓存触发**，继续往库里插数据（18:03 / 18:08 两轮）。

收尾顺序：**删流程 → 清数据 → 再构建一次（让包里不再含该流程）→ 等一个周期复查**。
实测对比：只删流程时下一轮照样跑（日志行数继续涨）；重建后紧接着的那个周期不再触发，行数停住。
所以「再构建一次」不是可选项，少了它就永远清不干净。

### 4.8 ★★★ `CALL_DATA_FLOW`：`dataFlowMappingId` 存的是**行 id**，`dataFlow` 是死字段

三个独立证据同向：

1. 设计器保存规则 `merge:{dataFlowMappingId:"dataFlow.id"}` → 两者必然相等
2. 运行时 `CallDataFlowActivity.parseActivityNode` **只读 `dataFlowMappingId`**，
   `dataFlow` 对象完全不参与解析（纯 UI）
3. 校验集合元数据键名 `data-flow-mapping-id-used-by-micro-flow`，
   由 `DataFlowMappingDto.getId()` 填充 → 必须是 **DataFlowMapping 主键**（列表行 id）

CONDITION 模式（默认）下 `condition` **必填**，空数组会被
`buildConditionInfo(..., required=true)` 拒。`SELECT_PARAM` 形态无样本、G33 不放行。

**实测**（源实体 0 行，不产单据）：`udc_rt_data_flow_log` 记下
`dataflow_mapping_id=<行 id>`、`is_success=1` —— 平台自己确认了这个口径。

### 4.9 ★★ 闸门代码也会重复：G33 曾报 3 次

G33 被复制进 `run_gates` / `run_end_gate` / `run_leak_gate.scan` 三处，
同一违规报 3 次（看到「G33 拦 6 项」其实是 2 条 × 3 份）。
**看到某个闸门一次报多条相同内容，先查它是不是被复制进了别的 gate 函数。**

### 4.10 ★★★ SUB_MICROFLOW：`hasInput/hasOutput` 必须照抄子流程当前契约

语料 251 条样本里，**无参子流程只有 6 条**（`(F,F)`），主流是带参调用
（`(T,T)` 207、`(T,F)` 30、`(F,T)` 8）。早期构造器写死 `hasInput=False / input=None`，
只能调这 2.4%。

必读子流程当前定义：`LiveRefs.microflow_detail(mf_id)` → `ds.input` / `ds.output`，
塞进 `mfService` 的 `hasInput/hasOutput/input/output/path`。
`sub_mf_candidates` 只回 id/name/caption，**不含契约**，光靠它必踩。

标量入参（`dataType != DTO`）：运行时直接置 `mappingType="value"` 并要求 `value` 合法；
DTO 入参才需要 `mappingType`（`value`/`attrs`）+ `pageInfo`。

★ **标量入参 `value.selectParam.desc` 用「子流程入参字段名」，不是父流程变量名**
（2026-11-04）：否则前端「参数」栏显示父流程变量名（reqId），用户看不到映射到
子流程哪个入参（MF-00 的「采购申请ID」）。`key/name/outputName` 仍指向父流程变量，
只改 desc。见 `references/node-sub-microflow.md` §9。

★ **BASIC 入参（标量）`basic_param()` 用 9 键 `desc`，不是 DTO 入参的 12 键 `description`**
（2026-11-04 纠错，方向曾反过一次）：前端表达式编辑器/「参数名称」读的是 `desc`，
误改成 `description` 会导致 desc=None、显示 name（编码 `_FLOW_INPUT_xxx`）。只有 DTO 入参
（dataType=DTO）才用 12 键 `description`（inApp/required/appName）。见
`references/triggers.md` + `core/facts/udc/microflow/trigger-and-type-mapping.md`。

★ **标量入参 `value` 的 `desc` 用子流程入参字段名，不是父流程变量名**：value 引用父流程
变量（如 reqId）时，selectParam.desc 若直接取父流程变量名，前端「参数」栏只显示 reqId，
看不到映射到子流程哪个入参（如 MF-00 的「采购申请ID」）。composer `_st_sub_microflow`
已用子流程入参的 desc 覆盖 value 的 desc/description，key/name/outputName 仍指向父流程变量。

★ **读 output 业务名一律 `o.get("desc") or o.get("description")` 双兼容**：`_id_ref`/`_out_ref`
曾只读 `o.get("desc")`，遇到用 `description` 的 output（DTO 入参）时 desc 退化成
trigger.caption「手动触发」，前端「选择该记录的ID」显示 undefined + 节点「数据已变更」。
判据：任何引用出参的地方，业务名都要 desc/description 双读。

逻辑图 DSL 的两个入口（都已接好，别在 scratch 手拼）：

```python
# 调用方传入标量：value 走引用槽，composer 会落 mappingType="value"
{"id": "call", "kind": "sub_microflow", "sub_id": CHILD_MID,
 "value": {"field": "mk"}, "out_desc": "子流程返回"}
# 子流程内部引用自己的入参（trigger.output，名形 _FLOW_INPUT_xxx）
{"fields": {"taskId": {"input": None}}}
```

`{"input": null}` 生成的是 `SelectParam{id/dtoType/udcApp=null,
name=key=path=outputName=入参名, position:"parent"}`，外层 `desc="标题 [文本]"`
（形态取自 85 个真实写节点样本）。**早期 `_ref_value` 没有这条分支，写节点一引用入参
就直接抛「不是已构建节点」** —— 遇到这个报错先查是不是走了旧版。

★★ **DTO 入参：可以无头建，不用进设计器。** 把流程 `input` 声明成实体 DTO
（`dtoType=MASTER_ENTITY`，`input` 与 `trigger.output` 指向同一份），`publish=True` 平台接受，
父流程就能按字段映射传参。`dtoType=CUSTOM` 的自定义参数 DTO（语料 109/112 条属这一档）
仍需设计器建，创建接口未找到。

调用方 DSL：`{"kind":"sub_microflow","sub_name":"…","inputs":{"taskId":{"const":"X"}}}`
→ `mappingType=attrs`，`attrs[].attrType` 是**子流程入参 DTO 的字段**（不是父流程的字段），
`value` 是 Simple 或 SelectParam。

★ 坑：子流程内部取自己入参的**字段**时，写成整变量引用（`position="parent"`、
`name=_FLOW_INPUT_xxx`）会让代码生成在同一方法里重复声明同名局部变量：
`已在方法 assignValue2JavaBeanCREATE_ENTITY_xxx(...) 中定义了变量 _FLOW_INPUT_xxx`。
DTO 入参取字段必须 `position="children"`、`key="<入参名>_<DTO全名>.<字段>"`、
`path="<DTO去点>.<字段>"`、`name=<纯字段名>`（`_ref_value` 里对 `_FLOW_INPUT*` 已有专门分支）。
实测：父流程传 `{taskId:'<MARK>-DTOIN', processedRows:7}` → 子流程写库原样到位。

★ **外部服务调用（物流取件/退款等）无真实服务对象时，用 SERVICE 微流程模拟**
（用户 2026-11-04 指示：「调用外部接口的不用想，创建空子微流程模拟，或自定义微流程模拟写业务」）：
建一条 SERVICE 微流程——入参=业务入参，内部 `create_variable` 造模拟返回值（trackingNo/paymentRef），
出参=返回值——主流程用 SUB_MICROFLOW 调它并消费返回值。模拟服务必须返回「业务链下游真需要的值」，
让「主流程消费服务返回值」这一步真实成立；这是模拟外部依赖，不是拿假结果冒充运行时验证（真实对象
缺口的节点仍按任务书标 BLOCKED_BY_FIXTURE，但用模拟服务让主流程的数据流先跑通）。

### 4.11 ★★★ 子流程改契约后：单流程发布会放行，**构建期一致性检测才拦**

实测（Child 出参 STRING→BIGINTEGER，父流程不刷新）：

```
父流程再次 publish → 通过（单流程 checkSchema 不做全局比对）
触发构建        → 11 秒 FAIL
  「发布失败: Business Error[一致性检测未通过]」
  com.seeyon.udc.pipeline.AbstractDeployService.doParallel(AbstractDeployService.java:242)
刷新（重读契约重建节点）→ 发布通过、构建 SUCCESS、运行期新契约生效
```

机制：`MicroFlowComponentUtils.checkMfService` 逐字比对 `mfService.input/output`
与子流程 schema，`compare()` **只比 dataType / type / id**（desc 改了不算）。
所以「属性已更新」只能靠改类型/结构复现，且**只重发 API 不改 mfService 绕不过去**。

### 4.28 ★★★ 删流程导致页面断链 → 一致性检测「page widget event association microFlow not exist」

之前验收「页面规则/前端流程」时若把**正式页面的控件事件**关联到了临时流程，
cleanup 删掉这些临时流程后页面断链，构建期一致性检测报 `page widget event association microFlow not exist`。

- **删流程前先查页面控件是否关联了它**：页面控件事件关联存 `udc_page_schema.page_schema`
  的 `childById.<控件>.events[].microFlow`（字符串 id）。删流程 + 清数据后「再构建一次」才会暴露
  这类断链（§4.7 的收尾顺序），构建 FAIL 的 msg 是「一致性检测未通过」。
- **排查**：`udcApplicationSearchDetectionPost`（body 是顶层 `{"appId":...}`，query 用 **`query`** 非 `mutation`），
  ERROR 项 `page widget event association microFlow not exist`。**`domainEntityId` 是页面 id 不是微流程 id**，
  真正的关联微流程 id 要进页面 schema 的 `events[].microFlow` 读。
- **修复**：递归删页面 schema 里 `microFlow` 指向已删流程的事件（保留指向存活流程的），
  走 `udcPageInfoUpdatePost` 保存（body 字段从 `udc_page_info` + `udc_page_schema` 拼：
  appId/id/caption/pageType/pageUrl/urlType/guid/relationGroupId/groupId/sortNo/publicAccess/
  pageSchema/draftPageSchema/masterEntityIds/eventDefine/pageVariable/inParams/outParameters/
  inPortletParams/settings/layoutInfo=''/layoutId='0'）。
- **直接 UPDATE DB 不生效**：检测器读发布镜像（Redis/OSS），不是 DB 的 `page_schema` 列。
  必须走 REST 保存才会刷新镜像。
- **SearchDetection 读旧缓存**：改完先 `udcApplicationDoDetectionPost`（触发重新检测，body `{"appId":...}`），
  sleep 几秒后 SearchDetection 才读到新结果（ERROR 才归 0）。只 SearchDetection 不触发 = 永远看到旧 20 个 ERROR。
- ★ 拿 `page_schema` 完整 JSON：conn.py 输出 longtext 含真实换行符会破坏 `json.loads`，
  用 pymysql 直连（复用 `xiaozhua-low-code-environment` 的 `env.load_env` 拿 mysql 配置）取完整值再解析。

### 4.29 ★★ 循环内 RETRIEVE 的 `from_field` 是循环项元素字段，不是本节点 entity 字段

`{"kind":"retrieve","entity":"A","by_id_from":"each","from_field":"外键"}` 里，
`from_field` 是循环项 `each` 的**元素字段**（外键属于源列表元素实体，如报价的 supplierId），
**不是** entity A（查询目标，如供应商）的字段。

`requirement_compiler` 归一化阶段曾把 `from_field` 与 `cond_field`/`by_field` 一起按 entity 归一化/校验，
导致「外键字段属于源列表元素实体、不属于查询目标实体」被误报 `FIELD_NOT_FOUND`。
已修：`from_field` 从归一化里拆出（跳过 entity 校验，它是英文真名、不需要中文转真名）。

★ **循环外同样适用，且 `_id_ref` 的字段元数据必须从前序节点实体取，不是目标实体**：
`{"kind":"retrieve","entity":"销售订单","by_id_from":"ticket","from_field":"orderId"}`
（按售后单 ticket 的 orderId 字段查销售订单）里，from_field=orderId 是 ticket（售后申请）的字段，
不是销售订单的字段。`_id_ref` 的 DTO 分支曾从 entity_model（目标实体销售订单）的 attributes
找 from_field，导致「按售后.orderId 查订单」误报 orderId 不在订单实体。
已修：从前序节点 `structure.label` 拿实体模型、从它的 attributes 取字段元数据。
通用规则：from_field 是「by_id_from 前序节点的字段」，字段元数据永远取自前序节点的实体，
不是查询目标实体——循环内外同一套，别只看循环内的例子。

★ **from_field 生成的 SelectParam 还要遵守 §4.22 字段级引用铁律，否则构建期 04004**：
`name`=纯字段名（不是 `outputName.fname`）、`relationEntity`=前序节点实体、`appName`=字段 refApp。
只修「字段元数据来源」还不够——name 用了 `outputName.fname` + 缺 relationEntity + appName 用
目标实体，publish/checkSchema 全绿，但**构建期**一致性检测报 04004「实体属性已更改(字段名)」。
04004 有两个独立根因，别修一个就收手：①字段元数据来源（本段）②name/relationEntity/appName
（§4.22）。判据：dump 该 RETRIEVE 节点的 `value.selectParam`，`name` 必须是纯字段名、
`id` 是前序节点 DTO 的字段 fullName、`relationEntity` 是前序节点实体 id。

★ **循环内 RETRIEVE 按循环项字段查（`by_id_from=循环项, from_field=循环项字段`）代码生成模板
不支持，编译直接 FAIL（2026-11-04 RMA 售后业务暴露）**：`by_id_from="loop", from_field="orderItemId"`
（循环内按售后明细的 orderItemId 查订单明细单价）生成的 Java 是
`selectCascadeById(SingleRequest.from(_ForEach_xxx))`——传了**整个循环项 DTO**（AftersaleItemDto），
而不是 orderItemId 字段（Long），编译报「不兼容的类型：Long vs AftersaleItemDto」。
根因：`_loop_item_select_param` 对循环项字段引用硬编码 `position=parent`（语料 37 条表达式引用
的真实形态），但「循环内 RETRIEVE 的 ID 查询 value」这个场景在 pmp_schemas.json 里**0 条样本**——
代码生成模板按 parent 把它当整项引用。这是平台硬约束，不是构造 bug，别去改 position 硬修。
正确做法（三选一）：①给源实体加金额字段，循环内直接 `loop.unitPrice`（字段级引用，最干净）；
②循环内 `create_variable`（`value:{"field":"loop.orderItemId"}`）中转 + `retrieve_array` 条件查询 +
FIRST_ONE 取第一条；③单价作为业务事实用 const 常量（标注「真实业务应关联单价」）。

### 4.30 ★★ 建实体字段名避开保留字（UDC_ENTITY_0002）

建属性时 `status`/`state`/`orderNo` 等字段名报 `UDC_ENTITY_0002 system reserved field`。
权威清单在反编译 `com.seeyon.udc.common.utils.Names.java`：

- `ENTITY_ATTR_NAME_RESERVED_WORDS`：`orderNo, parentId, actionType, linkSourceIds, extraParamMap,
  sort_i_no, extendMap, maskTypeMap, validate, secretId, secretN`
- `isAttributeReservedWord` 还含：以 `Dto`/`DtoList` 结尾、MyBatis OGNL（`eq/neq/gt/lt/gte/lte/shl/shr/ushr/band/and/bor/xor`）
- `status`/`state` 是 presetData 的 basic 属性集系统字段（不在上面清单，但也拒）。
- ★ **清单不全，实测还会拒清单外的词**：`result` 也报 `UDC_ENTITY_0002`（质检「结果」字段），
  反编译清单里没有它。建字段报保留字时别只对上面清单，直接换无冲突名（`result`→`inspectResult`，
  `status`/`state`→`bizStatus`，`orderNo`→`orderCode`，`receiptNo`→`receiptCode`）。
建实体 `POST /service/udc/entity` / 建属性 `POST /service/udc/entity/attribute` 都返回
`data.content` = 新 id 字符串（可为负）；建属性 body 必须带 `appId`（缺了报 `appId must not be null`）。

★ **实体 `name` 限 1-21 字符**（2026-11 制造业业务暴露）：`MfgMaterialRequirement`（23 字符）报
`BOOT_1001 name Entity name must be within 1-21 characters`。超长实体名用缩写（
`MaterialRequirement`→`MaterialReq`、`PurchaseReceiptItem`→`PoReceiptItem`、
`QualityInspectionItem`→`QualityItem`、`FinishedGoodsReceipt`→`FgReceipt`、
`InventoryTransaction`→`InvTransaction`、`ProductionCostSummary`→`CostSummary`）。
★ **微流程分组创建接口 `udcMicroFlowGroupCreatePost`**（GraphQL query，body `{appId, caption, type:"BACKEND_SERVICE"}`），
返回 `data.content` = 新分组 id（可为负）。查分组用 `udcMicroFlowGroupSelectByTypePost`
（body `{params0:{appId, type:"BACKEND_SERVICE"}}`）。
★ **DECIMAL/CURRENCY 字段精度靠 `decimalDigits`（小数位）+ `maxLength`（总精度），建属性只传 `dataType=DECIMAL` 会 scale 默认 0**（2026-11 制造业损耗率失效暴露）：损耗率 `0.05` 存 `decimal(20,0)` 被四舍五入成 `0`（BOM 展开算成 20 而非 21）、单位成本 `68.89` 成 `69`。建属性 body 加 `{"decimalDigits":4,"maxLength":20}`（decimalDigits=小数位，maxLength=总精度，不是 maxValue）。改已有字段精度：GET `/service/udc/entity/attribute/select-all-by-entity-id/{entityId}`（`data.content` 是**属性列表**不是 dict），找目标字段改 `decimalDigits`/`maxLength` 后 POST `/service/udc/entity/attribute/update` 整体回传（完整 77 键 DTO）。权威事实 `core/facts/udc/setting/attribute-set/create.md` §11.3。
★ **DECIMAL 标量赋给 INTEGER 字段报 `FORMULA_6902`，用 `roundOff` 函数转**：
`{"fn":"roundOff","args":[[{"field":"xxx"}]]}`（四舍五入取整）。88 函数目录还有
`roundOffCeiling`（向上）/`roundOffFloor`（向下）。见 `core/facts/udc/expression/functions.md` §数学函数。

### 4.31 ★★ 写实体数值字段的 const 常量必须转字符串（否则 NOT_BIGINTEGER）

`CREATE_ENTITY`/`CHANGE_ENTITY` 的字段值里，BIGINTEGER/INTEGER/DECIMAL 字段传 int/float 常量
（`{"const": 1}`、`{"const": 1000.0}`）会在构建期一致性检测报「插入数据:不是长整数类型」
（`UDC_MICRO_FLOW_04004` / `NOT_BIGINTEGER`）。

机制（反编译 `MicroFlowComponentUtils.buildAttrValue` + `CheckUtils.checkSimpleValue`）：
检测器读 `attrValue.getSimple()`（**String**）后 `Long.valueOf(value)` 校验，传 int/float 被判非长整数。
真实样本里 BIGINTEGER 字段值**几乎全走 SelectParam 引用前序节点**，Simple 常量是罕见场景，
所以这个坑只在「造种子 + 写数值字段」的流程里才暴露。

修复（`logic_graph._entity_fields`）：按字段 dataType 把 BIGINTEGER/INTEGER/DECIMAL 的
int/float 常量转字符串（`1`→`"1"`、`1000.0`→`"1000.0"`）。

★ **反编译里有两个 NOT_BIGINTEGER 抛点，方向相反，别混**：
- `CheckUtils.checkSimpleValue`：读 `getSimple()`（String）→ `Long.valueOf`，字符串 `"1"` 能过。
- `NodeUtils.getLong`：读 JsonNode → `v.isLong()`，数字 1 能过、字符串 `"1"` 反而报。
  实际构建走 `buildAttrValue`（`simpleObj.asText()` 转 String）→ `checkSimpleValue`，所以是**字符串口径**。

### 4.32 ★★ 构造器「有」某节点 ≠「实现」了它的所有 op_type（MAP_OPERATION KEY_SET 缺口）

`map_operation`（microflow_nodes_extra.py）早期只实现 GET/PUT，`op_type="KEY_SET"` 落进 else 分支
（当 PUT 处理）→ 生成 `entries` 但缺 `output` → publish 报 `PROPERTY_IS_REQUIRED`
（`Map操作.output`，批量验证 map-keyset 暴露）。

已补 KEY_SET 分支：出参=键组成的列表（`type=ARRAY, dataType=STRING, javaType=java.lang.String`），
不需要 theKey/basic（node-settings-capability 的「获取键列表」模式仅 3 必填：选择映射/操作类型/出参名称）。

★ 通用规则：**用构造器前先确认要用的 op_type/convert_type/子模式有专门分支**，别让未知取值
落进 else/默认分支被当成另一个形态。同类的 MAP_OPERATION REMOVE（删除）也未见专门分支，
用之前先查。

### 4.33 ★★★ 业务数据流构造：值编辑器三态 + 字段引用必须 RETRIEVE 中转（用户纠偏）

「节点覆盖率高、构建成功、测试多」是假象——如果写实体字段全用 const，生成的流程仍是
「互不相关的 CRUD 堆」，没验证节点间的数据传递。这是从「节点覆盖」转向「数据流覆盖」的核心。

**值槽三态的真实分布**（`value-literal-contexts.md`，643 条流程统计）：

| 类型 | 生产出现 | 语义 |
|---|---|---|
| SelectParam（引用） | **2482**（最多） | 引用前序节点 / 字段 |
| Expression（表达式） | 998 | 计算 |
| Simple（常量） | 757 | 固定值 |

写实体字段**优先用引用/表达式**，别默认全 const。但「该用动态引用的字段」才用引用，
基础测试数据/枚举/固定状态允许 const——不要为刷引用数造无意义依赖。

**字段级引用前必须先 RETRIEVE 中转成 DTO**（G20 同源，2026-11-04 业务链验证）：

```
❌ {"field": "req.totalAmount"}  （req 是 CREATE_ENTITY，出参是标量 id，没有字段）
   → 退化成整节点引用（parent/BIGINTEGER），字段部分被静默丢弃，不报错
✅ 先 {"kind":"retrieve","entity":"采购申请","by_id_from":"req"}  → reqDto（DTO 出参）
   再 {"field": "reqDto.totalAmount"} → SelectParam children/DECIMAL，正确
```

判据：dump 写节点的 attrs，看字段引用的 `selectParam.position` 是 `children`（字段级）
还是 `parent`（整节点）。写 BIGINTEGER/DECIMAL/STRING 字段却看到 parent+BIGINTEGER，
就是「引用了标量节点、字段丢了」。

**change_entity 的目标必须是 DTO，不能是 CREATE_ENTITY 标量 id**：
`selectParam` 引用前序 RETRIEVE 的 DTO 出参（dataType=DTO/dtoType=MASTER_ENTITY），
引用 CREATE_ENTITY（标量 id）会被 G31 拦「引用 dataType=DTO 与出参声明 BIGINTEGER 不一致」。
更新刚创建的记录 = 先 RETRIEVE 查成 DTO 再 change_entity。

**循环内累加（明细金额 = quantity × estimatedPrice 汇总）的表达式形态**：

```python
{"id": "acc", "kind": "create_variable", "title": "totalAmt", "data_type": "DECIMAL",
 "value": {"const": 0}}                       # 循环外累加器
{"id": "loop", "kind": "for_each", "list": "items", "body": [
    {"id": "accStep", "kind": "change_variable", "target": "acc",
     "value": {"arith": "ADD", "items": [
         {"field": "acc"},                    # 引用累加器（标量变量）
         {"arith": "MUL", "items": [
             {"field": "loop.quantity"},      # 循环项字段引用（loop 是 for_each 节点 id）
             {"field": "loop.estimatedPrice"}]},
     ]}},
]}
```

- 表达式算术的键是 **`arith` = 运算符名字符串**（`"ADD"`），不是 `{"op":"ADD"}`——
  写成 `{"arith":{"op":"ADD",...}}` 会报「arith 不支持运算符」。

★ **写实体字段（CREATE_ENTITY/CHANGE_ENTITY 的 fields）或 BRANCH condition 用 arith/op 表达式时，
三个表达式值槽坑（RMA 售后退换货 2026-11-04 暴露，`logic_graph.py` 已修，commit 46f90b90）**：
  1. `_build_expression` 必须 `to_value_slot` 包装成 Expression 值槽（带 type 键）——直接返回
     `{title,schema}` 会报 `value.type PROPERTY_IS_REQUIRED` + `DATA_INVALID`。
  2. 写字段的 result_type 必须用目标字段 dataType（不是硬编码 STRING），否则 DECIMAL 字段算成 STRING。
  3. `_exec_branch` 的 condition 拿到的也是 to_value_slot 包装，而 branch_node 要 `{title,schema}` 原始对象，
     必须先 `cond.get("expression")` 解包，否则 G12 报 ifBranch expression 未配置。
- 循环项字段引用 `{"field":"loop.xxx"}`，loop 是 for_each 节点的 id/别名（`loop_frame_from`
  用 `alias=n["id"]`），生成 context 带循环项字段类型（quantity/estimatedPrice 正确）。
- 累加器 `{"field":"acc"}` 引用 CREATE_VARIABLE 标量出参，走表达式（Expression），
  不是 SelectParam（标量出参走 `_scalar_value_slot`）。

**业务组合测试（第二层）与节点形态测试（第一层）要分开**，不能拿第一层通过率冒充第二层。
一条真正有数据依赖的链：CREATE_ENTITY(父) → CREATE_ENTITY(子,引用父ID) →
RETRIEVE_ARRAY(按父ID) → FOR_EACH(循环项字段) → 表达式累加 → CHANGE_ENTITY(回写父) →
RETRIEVE(回读) → 断言。字段来源逐条标：CONSTANT/PREVIOUS_NODE/PREVIOUS_NODE_FIELD/
LOOP_ITEM/EXPRESSION。凡业务上应继承前序结果的字段，不许无理由硬编码。

**字段级引用类型必须匹配，否则前端「所选'X'已变更」（假绿，2026-11-04）**：
`{"field":"reqDto2.totalAmount"}` 把 DECIMAL 字段赋给 BIGINTEGER 字段（如迁移断点
processedRows）→ 前端抽屉标红「所选'总金额'已变更」，但运行时 BigDecimal 自动转 Long、
读库正确——**假绿**，读库正确不等于前端认可。

判据：dump 写节点 attrs，字段级引用的 `selectParam.dataType` 必须等于目标字段 dataType：
`taskId`(STRING)←requestCode(STRING)→children/STRING ✅；
`processedRows`(BIGINTEGER)←totalAmount(DECIMAL)→children/DECIMAL ❌。

正确：类型匹配用 SelectParam（选值）；类型不匹配用表达式（resultType 用目标字段 dataType）；
标量出参（SIZE/SUM/MIN/MAX）引用到写字段走 `_scalar_value_slot` 表达式（resultType 用字段
dataType 宽化，§4.22/5cdcc974），不会「已变更」。**闸门 G41 已拦字段级引用类型不匹配**
（SelectParam position=children 的 dataType 必须等于目标字段 dataType）。业务上「行数」不该装「金额」——
字段赋值先问装什么值、什么类型，再定用引用还是表达式。

**数据血缘审计（Data Lineage Audit）—— 批量验证固定环节**（2026-11-04）：
`components/construction/lineage_audit.py` 的 `audit_lineage(draft)` 逐个分类写节点字段的
7 种来源（CONSTANT/TRIGGER_INPUT/PREVIOUS_NODE/PREVIOUS_NODE_FIELD/LOOP_ITEM/EXPRESSION/
SYSTEM_VALUE），输出 lineage-report + 统计。两个高级指标判「关联性不强」：
- **孤立节点**：DATA_NODE_KINDS（retrieve/retrieve_array/create_variable/list_operation）
  有数据出参却没被下游引用 = 读而不用 = 链断了。
- **硬编码关联**（HINT）：同写节点有字段引用前序上下文、另一些却是固定值，提示核查。
事实 `core/facts/udc/microflow/field-assignment-source-strategy.md`；测试
`tests/test_lineage_audit.py`。生成后跑一遍，孤立节点非空 / field_refs+loop_item_refs
+expr_refs 全 0 = 「各造各的 CRUD 堆」的信号。

**案例质量评分 `score_case(draft)`**：把血缘指标折成 0-100 分 + 分级（S≥90/A≥75/B≥60/C<60）。
数据流密度（非 const 占比，<50% 扣分）+ 孤立节点（每个 -20）+ 硬编码（每个 -10）。
纯读流程给 100。评分是相对排序工具，低分先看孤立节点/硬编码两条，再判断是业务合理还是该改。

### 4.12 ★★★ 节点运行时验证协议（每补一个 RUNTIME_VERIFIED 都按这个走）

把某个节点从 SCHEMA_VERIFIED / BUILD_VERIFIED 推到 **RUNTIME_VERIFIED** 时，
不是「跑一遍看 success」，而是一套固定顺序（详细模板与断言表见
`references/node-runtime-verification.md`）：

```
A 语料审计 → B 自建隔离对象 → C 调用链验证 → D 属性刷新 → E 结果断言 → F 定级
```

**四条硬规则（缺一条就不算验完）：**

1. **样本数先重数，不信文档。** 能力矩阵里的样本数会漂（实测 706 → 实际 251；另一节点 523 → 217，
   同一方向，普遍虚高 2~3 倍）。
   从原始 dump `scratch/pmp_schemas.json`（643 条 RELEASE 流程 / 7937 节点）重算，
   并把新旧数字的差异当成信号：**统计错了，形态结论也可能错**。
2. **`success=true` 不是验收标准。** 判据只能是读侧数据（物理表 / `udc_rt_data_flow_log` /
   业务行），而且**入参侧和出参侧都要有独立的读侧证据**——不能只看到「流程跑完了」。
3. **优先自建对象，不等外部依赖。** 能自己建父/子流程、自己造标记值的节点先验；
   需要真实业务单据/真实映射对象的往后排，别让它们堵住整条主线。
4. **证据等级不许混。** 只构建成功 → BUILD_VERIFIED；只保存 + schema 过 → SCHEMA_VERIFIED；
   部署了但没有可观测效果（如无订阅者的事件）→ LIVE_EXECUTED，**不许写 RUNTIME_VERIFIED**。

**收尾按 §4.7 的顺序**：删流程 → 清数据 → 再构建一次 → 等满一个周期复查。
只删流程或只清数据，都会继续长出新行。

**验证脚本按「构造 / 发布 / 构建」三段拆开写**，构建段要能单独重跑（轮询 `deploy_status` 到终态）。
不要把带清理前导动作（删同名流程、清数据）的脚本前半段 `exec` 进来复用——那会把正在验的流程删掉，
只能重新建单再等一轮构建。

### 4.13 ★★★ 查询条件右值：`{"const": x}` 必须转 CONSTANT，否则条件静默失效

平台把 `rightParams` 里不合规的槽解析成 `value=""`/`desc=""` ——
**查询条件等于没写**：RETRIEVE_ARRAY 返回整张表，构建 SUCCESS、运行 `success=true`，
三个 SIZE 全返回同一个数（实测 23），只有读侧数据不对。

合法形态：`{"type":"CONSTANT","value":"<str>","desc":"<str>"}`。
闸门 **G39** 拦：右值缺 `type`，或 CONSTANT 缺 `value`。

另注意 DSL 的键是 **`right`**（`_do_retrieve_array` 读 `n.get("right")`），
写成 `right_value` 会被忽略，退化成空常量——同样的静默失效。

**BRANCH 的 condition 走表达式引擎，字段 vs 字段比较是支持的**（与 retrieve_array 的 condition
**不是**同一套机制）：`{"op":"GE","left":{"field":"b.budgetAmount"},"right":{"field":"r.totalAmount"}}`
走 `_build_expression`（表达式引擎，字段引用 OK），用于「预算金额 >= 申请总额」这类跨字段判断。

★ **但 retrieve_array/retrieve 的 condition 右值（`_cond_value`）不支持字段引用**
（`{"field":"req.deptId"}`，field 含点号），两条路都堵死：
- CONTEXT_VARIABLE(children)：平台解析不了，查询**静默返回空**（`success=true` 但 SIZE 全 0，假绿）。
- EXPRESSION：`executableExpr` 是后端编译 blob，自己编（`build_remote`）保存/publish 直接 `BOOT_1001 Parameter Error`。

正确绕法：先用 `create_variable` 把字段值转成标量变量（`value:{"field":"req.deptId"}` 生成
SelectParam children 引用，正确），再让 condition 右值引用该变量（整节点 `parent` 引用，平台认）。
`_cond_value` 遇字段引用（field 含点号）已改为**显式报错**，提示改用 create_variable 中转，不再静默假绿。

★ **引用 DTO 节点（field 不含点号）同样会失败，判据是「被引用节点出参是标量还是 DTO」**：
`{"field":"req"}` 里 req 是 RETRIEVE（DTO 出参）而非 CREATE_ENTITY（标量 id）时，
`_ref_value` 生成 `position=children` 的 CONTEXT_VARIABLE 引用**整个 DTO**，缺 javaType →
publish 报 `查询-xxx.javaType PROPERTY_IS_REQUIRED`。只有引用**标量节点**（CREATE_ENTITY 的 id、
CREATE_VARIABLE 标量、LIST_OPERATION 聚合出参）才是 parent 引用、合法。

所以：查询条件右值引用前，先确认被引用节点 `output.dataType` 是标量（BIGINTEGER/INTEGER/…）还是
DTO。是 DTO 就先 `create_variable`（`value:{"field":"req.id"}` 取 id 字段）转标量，再引用该变量。
这条不是「含点号才要中转」，而是「引用非标量节点都要中转」——点号只是最容易被抓到的那个信号。

### 4.14 ★★★ 隔离测试数据必须用应用租户

平台写入的行是 `tenant_id=<应用租户> / creator=-1`，查询带租户过滤。
SQL 直接插的种子若用 `tenant_id=0`，平台一条都查不到（SIZE 全 0），
很容易被误判成「条件还是失效」。造种子前先抄一行平台写入的 tenant_id。

### 4.15 ★★ 构建失败先看「哪个模块挂了」，再判断是不是自己的问题

构建失败时**先下载 backBuild.log 并看模块级结果**，不要直接怀疑生成器：

```
[3/6] -biz  SUCCESS   ← 微流程生成的 XxxService.java 在这里
[5/6] -ext  FAILURE   ← 应用扩展代码，与微流程无关
```

- `-biz` SUCCESS 就已经证明**生成的 Java 编译通过**（含表达式、分支、出参类型）。
  整体 FAILURE 落在 `-ext` 时，问题在应用自己的扩展代码，不在微流程。
- 典型形态：扩展代码调 `setXxx/getXxx`，但实体没有该字段 →
  `找不到符号: 方法 setXxx(...) 位置: 类型为...domain.entity.Xxx`。
- ★ **删前端流程（自定义微流程）会连锁导致 `-ext` 编译失败**：门面接口（如
  `api.microflow.MigrationService`）是**按设计态微流程生成的**，删掉对应微流程后接口里
  就不再声明该方法，扩展代码里 `@Override` 该方法 → `方法不会覆盖或实现超类型的方法`。
  清理流程前先查这个流程有没有被扩展代码 `@Override` 实现。方法签名与接口一致时
  `@Override` 只是可选的编译期校验，删流程后去掉注解即可（或恢复流程让方法重新生成）。
  这不是「用户代码坏了」，是删流程的连锁反应。
- 判断实体到底有没有这个字段，用**属性接口读全量**，不要只信 `entity_model`
  （它过滤系统字段、且同一进程内有缓存）：
  `POST /service/udc/entity/attribute/select-by-primary/{entityId}` → `data.content.attributes`。
- 字段在元数据里齐全时，先重试构建一次再动手加字段——上一轮产物可能早于元数据变更。
  加字段属于改他人应用，先问。

★★ **自己留下的坏流程会毒化整个应用构建，报错还会扩散到平台胶水类。**
实测：残留两条坏流程（一条重复声明局部变量、一条类型不兼容）后，构建失败信息里出现
`DefaultCustomMicroFlowConfig` / `MicroFlowAppServiceImpl` 报「找不到符号: 变量 log」，
看着像平台模板坏了或用户在改的流程坏了。删掉自己的残留流程 → 重建立刻 SUCCESS。
**看到大范围 `log` 找不到符号，先查有没有自己留下的未清理流程，再怀疑别人。**

**构建终态只认 `deploy_status(deployId)` 轮询**：应用 build-info 快照会停在旧记录，
用它做基线判新旧的 `wait()` 会永远等下去（实测空转 10 分钟以上）。

★ **轮询超时但 backBuild.log 已 BUILD SUCCESS = 平台状态落库 bug，不是构建卡死**：
`udc_deploy_record.state` 偶发停在 0（update_time 停在创建后几秒），而 Maven 编译
几十秒就 BUILD SUCCESS 了。判据：先下载 backBuild.log 看 Maven 是否 SUCCESS，若是
**重新触发构建**（换新 deployId 轮询）即可，别等旧状态、别误判成构建锁或参数错。

### 4.16 ★★★ 重发必须幂等：节点 id 由别名派生

`nodeId` 用 `uuid4().hex[:6]` 时，每次 compose 都是新 id，出参名 `_"+nodeId` 和下游引用名跟着变。
把整张 schema 重发到同一个流程 id = **整图换节点**：设计器里开着的副本一比对就标红
`所选"xxx"已变更`（平台校验通过、构建 SUCCESS、运行正确，只有 UI 红），
页面规则 / 其他流程引用该节点会**断链**，服务端还堆孤儿节点。

正确做法：`node_builder._new_id` 按 `(actionType, 逻辑图别名, 该别名下第几次)` 取 md5 前 6 位；
`composer.step(kind, alias)` 是唯一收口点，进节点前设 `builder.node_key = alias`；
分支内 `CONDITION_*` 不走 step，在 `_exec_branch` 手动设同一个 key。

实测：同图重发 → id / 出参名 / 引用名**完全不变**；中间插入新节点 → 原有节点 id 全部保持。
**改别名 = 换 id**，所以改图优先「新增别名」，不要「删了重建同名」。
细节见 `references/node-id-stability.md`。

### 4.17 ★★★ CHANGE_LIST 四种动作的形态完全不同（G40 把关）

| action | 样本 | dataSource |
|---|---|---|
| ADD | 266 | 元素 OBJECT（125）/ 列表 ARRAY（52） |
| REPLACE | 28 | 列表 ARRAY（25）/ **单元素 OBJECT（3）** |
| CLEAR | 15 | **没有** |
| REMOVE | 8 | 列表 ARRAY + `countAttrs`（按 id 匹配元素，可多字段） |

枚举里**没有 DELETE**（传 DELETE 直接抛错）。节点无出参（`output` 恒 null）。
CLEAR 必须 `pop` 掉模板自带的 `dataSource` / `countAttrs`，否则带上非法字段。

★ **dataSource 的 ARRAY / OBJECT 不能按动作写死，要按来源节点出参类型选。**
REPLACE 两种形态在语料里都存在：出参 OBJECT 时用**元素引用**（拿首元素整体替换整张列表，
实测 4 条变 1 条），出参 ARRAY 时用列表引用。构造器写死 ARRAY → G31 当场拦
`引用 type=ARRAY 与出参声明 OBJECT 不一致（List/单对象错接）`；写死 OBJECT → 反向同错。
ADD 同理（元素 125 / 列表 52）。REMOVE 恒为列表 + `countAttrs`，多字段（id+业务字段）可行。

实测：`selectParam` 可以直接指向 `RETRIEVE_ARRAY` 出参，**查询结果数组在流程内可变**
（四动作 SIZE 分别 3→0 / 3→4 / 3→1 / 3→2），不需要先复制到变量。
细节见 `references/node-change-list.md`。

### 4.18 ★★ CONVERT_DATA：`type` / `dataType` / `javaType` 必须一起改

出参形态由 convertType 决定（114 条语料）：

```
Split                 ARRAY  STRING     java.lang.String    （必带 regex）
multiAssociation2List ARRAY  BIGINTEGER  java.lang.Long
List2multiAssociation OBJECT STRING     java.lang.String
BasicData2String      OBJECT STRING     java.lang.String
String2Long           OBJECT BIGINTEGER  java.lang.Long
```

模板默认是 Split 形态。**只改 `dataType` 不改 `javaType` → 构建 41 秒编译失败**：
`不兼容的类型: java.lang.Long无法转换为java.lang.String`（代码生成按模板的 String 声明变量）。
G32 现在三种一起校验。除 Split 外其余四种**语料恒无 `regex`**。

### 4.19 ★★ 能力等级由证据回填，不手改矩阵

`components/udc/microflow/capability_registry.py`：

```bash
python -m components.udc.microflow.capability_registry             # 全局分布
python -m components.udc.microflow.capability_registry CHANGE_LIST # 等级+范围限定+证据文件
```

- `load()/summary()` 读 `capability-matrix.md` + `evidence/*.json`；**等级只从矩阵 note 解析**（单一事实源）。
- `advisory(schema)`：`MicroflowComposer.finish()` 把「本次流程里还没拿到运行证据的节点类型」
  挂到 `mc.advisories`。不阻塞构建，但交付前必须看一遍。
- `record_evidence(action, payload)`：证据落盘 + 矩阵该行等级自动更新；
  **payload 里没有 `pass=True` 用例直接拒绝**——等级只能由真实运行证据提升。
  ★ **证据文件只增不改**：文件名是 `<action>-runtime-<日期>.json`，同一天验两轮若直接覆盖，
  第一批 case 就没了（实测 9 条变 2 条）。工具已改为存在即合并：cases 按 case 文本去重、
  新记录在前同文本以最新为准，`not_covered` 取并集，并记 `runs` 计数。
  给同一天已验过的节点补证据时**直接再调一次**即可，不要手工改 JSON。

★ 写断言能力等级的测试时，**不要拿真实矩阵里的任何类型当「未验证样本」**。
「挑一个长期停在 CONSTRUCTED 的类型」这种办法靠不住：`CALL_APP_SERVICE` 就被当成过样本，
本轮它升到 RUNTIME_VERIFIED 后测试当场假红（第二轮 `CREATE_MAP` 升级又红一次）。
正确做法是 `advisory(schema, caps)` 传入**自造 caps**（`Capability(action, n, pct, "✓", "✓", note="**SCHEMA_VERIFIED**")`），
测试与矩阵当前状态彻底解耦——矩阵怎么涨，测试都不会假红。

### 4.20 ★★★ CALL_APP_SERVICE：调 starter 服务（流水号）的三个必对细节

实测 `SerialNumberAppService.getSerialNumber`（`SingleRequest<SerialNumberDto>` →
`SingleResponse<java.lang.String>`），`HT2026111/112/113` 三轮递增落库，`ctp_serial_history` 同刻记录。

1. **starter 服务不属于当前应用**：`implClass` 以 `com.seeyon.boot.starter.<stem>.` 开头时，
   `app.appName="boot-starter-<stem>"`、`inApp=false`、`udcApp=false`。
   写成本应用 → 抽屉显示错归属、运行时可能找不到服务。构造器已按 implClass 自动推导。
2. **attrs 必须是字段级 attrType**：parameter 是 `SingleRequest<Dto>` 时，真实节点的 attrType 是
   `Dto.<字段>`（如 `SerialNumberDto.serialSchemeCode`），**不是** DTO 全名。
   只按 parameter 推会得到 DTO 级 → 字段映射对不上。构造器已支持调用方传 `attrType` 覆盖。

   ★ **字段级 attrType 必须用 `field_attr()` 从真实字段表构造，别手搓简化键**：
   `lr.dto_attributes(app_id, app_name, dto_full)` 拉字段表 + `field_attr(em, fname, sort=i)`
   造完整 16-20 键。手搓（只给 name/id/fullName/javaType/dataType/type/desc 这 8 键）会缺
   `filterDataType/filterType/filterFullName/relationApp/refId/relationEntity`，
   前端抽屉「所选数据已失效，请重新选择」红字（field_attr docstring 已记这个坑）。
   composer 的 `_st_call_app_service` 已自动把 DSL 层 attrs dict 转成 field_attr 列表，
   生成时写 dict（`{"attrs":{"serialSchemeCode":{"const":"HT"}}}`）即可，别自己拼列表。

   ★ **逻辑图 DSL 层 attrs 写字段映射 dict，不是列表**：
   `{"kind":"call_app_service","method_full":"…getSerialNumber","attrs":{"serialSchemeCode":{"const":"HT"}}}`。
   composer 会自动把 dict 转成构造器要的 `[{attrType:字段级, value:Simple}]` 列表。
   直接写列表（构造器内部格式）会被当 dict 遍历 keys（字符串）报
   `'str' object has no attribute 'get'`——DSL 层和构造器层是两种格式，别混。
   ★ **转换必须用 `dto_attributes()` + `field_attr()` 拉真实字段元数据（16-20 键）**，
   手搓 8 键简化 attrType 缺 `filterDataType/filterType/filterFullName/relationApp/refId/
   relationEntity` → 前端字段下拉红字「所选数据已失效，请重新选择」
   （`field_attr` docstring 已记这个坑，2026-11-04 业务链又踩一次）。
3. **简单类型返回值不能默认 DTO**：`returnValue.item.itemType=java.lang.String` 时
   `output.dataType` 必须是 `STRING`（`java.*` → STRING/BIGINTEGER/INTEGER/DECIMAL/BOOLEAN/DATETIME）。
   默认成 DTO 会让下游写节点按 DTO 处理。

★ 取流水号有副作用（消耗一个号），但这正好是「服务真被执行」的证据；验完不必回滚。
流水号方案编码从 `<app>_test2.ctp_serial_scheme` 取（`code` 字段），可用测试方案别占用业务方案。
细节见 `references/node-call-app-service.md`。

### 4.21 ★★ DATA_MAPPING：上游必须是列表，ARRAY 判定必须在 `_entity_output` 之后

实测链路 `RETRIEVE_ARRAY(3 条) → DATA_MAPPING(sourceTable→taskId) → CREATE_BATCH_ENTITY`，
写回 3 行 `task_id='DM-SRC'`（未映射字段为空 —— 证明确实是映射产物，不是原样复制）。

- **上游必须是列表**（G29 拦）；单对象主实体上游会生成 `List<Dto>` 对单对象取字段 → 构建 FAIL。
- **`node["output"]["type"]="ARRAY"` 必须写在 `_entity_output(...)` 之后**——它会整体覆盖 output，
  写前面会退回 OBJECT，下游引用被 G31 判「type=ARRAY 与出参声明 OBJECT 不一致」。
- DSL 必须能传 `src_field`/`dst_field`：默认 `name→name` 只适用于有 `name` 字段的实体，
  实体的字段叫 `taskId`/`sourceTable` 时直接 KeyError。`_do_data_mapping` 与 `_st_data_mapping`
  两处都要透传，只改一处等于没改。
- ★ **`FIRST_ONE` 接 DATA_MAPPING 曾经编译不过，根因已定位并修好**：症状是「找不到符号:
  类 `_LIST_OPERATION_xxx`」，看着像出参丢 javaType，实际是字段引用 `SelectParam.name`
  写成了「<节点输出名>.<字段>」（见 §4.22）。改成纯字段名后
  `retrieve → data_mapping(sourceTable→taskId) → FIRST_ONE → 写` 直接构建成功、映射值逐字落库。
  **遇到「类 _LIST_OPERATION_xxx 找不到符号」先查引用形态，别去改 list_operation 的出参。**

细节见 `references/node-data-mapping.md`。

### 4.22 ★★★ 字段引用的 name 是纯字段名；LIST_OPERATION 索引 1 基

**SelectParam（字段级）形态**（463 条 children 引用校准）：

```
name     = 字段名本身          ← 写成 "<节点输出名>.<字段>" 会让代码生成把节点名当类名
key      = "<outputName>_<字段全名>"
path     = "<dto 去点>.<字段>"
position = children
```

症状：编译报 `找不到符号: 类 _LIST_OPERATION_xxx`（位置显示在 DTO 类里）。
这不是节点构造错，是引用形态错。

**LIST_OPERATION**：
- `PICK_ONE` 从 **1** 开始（0 被平台拒：`LIST_OPERATION_PICK_ONE_LESS_THAN_ONE`），
  按检索顺序（RETRIEVE_ARRAY 默认 id 倒序）。DSL 字段名是 **`index_value`**（不是 `pick_index`）：
  `_do_list_operation` 只读 `n.get("index_value")`，写 `pick_index` 被静默忽略 →
  `indexValue.simple=null` → 运行时「获取第N条为空」且 `output=null`（MF-01 预算判断暴露）。
  这个错被「只断言 SIZE 不断言 PICK_ONE 结果」的验证掩盖过——PICK_ONE 上游查不到时别先怀疑查询，先查 `index_value` 有没有被读进来
- `DISTINCT` 必须给 `countAttrs`，否则发布被拒 `PROPERTY_IS_REQUIRED`
- `SORT`/`DISTINCT` 出参是 ARRAY；`SUM/MIN/MAX` 随字段类型。
  独立聚合 DSL：`{"op_type":"SUM","count_fields":["<字段>"]}`（**无 `group_by`**，`count_fields` 是聚合字段，
  可用中文字段名走归一化）。实测 `SUM(failedRows)` 出参 BIGINTEGER、写回 8 分毫不差
- `GROUP_AND_SUM`：`groupByAttrs`=分组字段、`countAttrs`=汇总字段，出参仍是 ARRAY（元素 DTO 不变）。
  DSL `{"op_type":"GROUP_AND_SUM","group_by":["sourceTable"],"count_fields":["processedRows"]}`。
  实测 3 行同组（1、2、5）→ 组数 1、汇总 8；多分组键未验
- ★ **取列表操作结果的字段，节点字段引用要用点号**：`{"field":"f1.processedRows"}`。
  写成 `{"field":"f1","from_field":"processedRows"}` 会被当成「整个元素引用」，
  平台报 `CREATE_ENTITY.attrs.value.selectParam.javaType PROPERTY_IS_REQUIRED`

★ **写结果引用 LIST_OPERATION 标量出参（SIZE/SUM/MIN/MAX）已改为表达式形态（2026-11-03 修复）**
  根因：SelectParam 整节点引用（name=outputName）被平台保存时误当成「字段引用」，
  规范化成「节点.节点」畸形 executableExpr，前端红「所选"命中数"已变更」（运行时虽正确）。
  修复：`logic_graph._scalar_value_slot`——标量出参（node_dtype 是 BIGINTEGER/INTEGER 等）
  走 `ExpressionCompiler + build_remote + to_value_slot`，生成两级 VARIABLE token（value=`X.X`）
  + 两级标量 context（顶层 OBJECT + 子项标量）+ 带前缀 executableExpr；DTO 字段引用仍走 SelectParam。
  ★ `NodeField` 本身就是 `Expr` 子类，纯引用可直接走表达式引擎（不用另造「纯引用」AST）。

  ★★ **表达式形态的两个边界（`_scalar_value_slot` 过度转 Expression 会报 NOT_BIGINTEGER）**：

  1. **写操作（CREATE_ENTITY/CHANGE_ENTITY/DELETE_ENTITY 及 batch）的 id/影响行数出参虽然是标量
     （BIGINTEGER/INTEGER），引用它必须走 SelectParam（引用节点 id 字段），不能走 Expression。**
     只有 LIST_OPERATION 的聚合标量（SIZE/SUM/MIN/MAX）才走表达式。
     区分靠 `ref.node_action`（`_node_ref` 里存的节点 actionType）：写操作族的标量出参在
     `_scalar_value_slot` 里返回 None 走 SelectParam。
  2. **Expression 的 resultType 必须用目标字段的 dataType，不是出参节点的 dataType。**
     SIZE 出参是 INTEGER，但目标字段（如迁移断点.processedRows）可能是 BIGINTEGER，
     resultType 声明成 INTEGER 会被一致性检测判类型不匹配报 NOT_BIGINTEGER。
     `_scalar_value_slot` 已加 `field_name` 参数，结果类型用字段 dataType（可能宽化 INTEGER→BIGINTEGER），
     context 变量类型仍用出参 dataType（SIZE=INTEGER）。

**MANUAL 流程的 `end.basic_out` 必须匹配引用节点的 `output.dataType`**（finish 会拦
「basic_out='X' 但引用节点 output.dataType='Y'」）。三类出参别记错：

| 节点族 | 出参 dataType | 举例 |
|---|---|---|
| 写节点 CREATE_ENTITY | BIGINTEGER（插入 id） | 引它 basic_out=BIGINTEGER |
| 写节点 CHANGE_ENTITY / DELETE_ENTITY | INTEGER（影响行数） | 引它 basic_out=INTEGER |
| 查询/取数 RETRIEVE / RETRIEVE_ARRAY / PICK_ONE / FIRST_ONE | **DTO** | 要出 BIGINTEGER 得先 `create_variable` 取 `.id`（`value:{"field":"best.id"}`）再引该变量 |
| LIST_OPERATION 聚合 SIZE/SUM/MIN/MAX | 标量（INTEGER/BIGINTEGER/DECIMAL 随字段） | 直接引 |
| CALL_APP_SERVICE | 返回类型（简单类型→STRING/…） | 直接引 |

写节点出参是「影响行数/插入 id」不是「写入的实体」，所以「返回最优报价 ID」这类出参必须
`create_variable` 中转 DTO 的 `.id` 字段，不能直接 basic_out 指 DTO 节点。

**隔离测试**：应用里别的流程会清表（实测外部 SQL 种子被删、聚合全 0）。
造数据要放进被测流程本身（同一事务），多条件断言必须自带
`sourceTable=<本批标记>`，否则会把别人的行算进来（首轮 MULTI 返回 6 就是这么来的）。

**SCHEDULE 每触发一次就再跑一遍整个流程**：「造种子 → 聚合 → 写结果」的流程，第 2/3 次触发会
把前几轮种子也查进来，聚合结果线性翻倍（实测 3/6/9、8/16/24）。**只认第一次触发的干净结果做断言**，
后续触发的翻倍是「聚合逻辑正确」的反向证据，不是失败。要断言干净就用唯一 `MARK` 且每次触发
换新标记（或让「写结果」的 taskId 带 `-SUM` 后缀，查询条件不命中它，避免把汇总行再算进聚合）。

★ **要干净触发一次（端到端业务断言用）：publish 改回 MINUTE/5 → 构建 → 清数据 → 轮询等下一次触发 → 立刻断言 → publish 改回 DAY 停调度。** 两个顺序陷阱都踩过：①**publish 调度配置后必须重新构建，运行时才加载新调度**——先构建（DAY）再 publish MINUTE/5，运行时仍用旧 jar 的 DAY 调度，等 8 分钟都不触发（`ctp_job_info` 有 job 但调度器不跑）；②先 publish MINUTE/5 再构建，会在构建重试期间就触发多轮——`UDC_DEPLOY_0002` 构建锁要 `30s × N` 次重试，这 4~5 分钟里调度器跑了 N 轮，种子/单据/流水翻倍（实测 4 轮 = 12 条库存余额、80 条领料单）。所以正确顺序是「publish MINUTE/5 → 构建 → 清数据（清掉构建期间触发的污染）→ 轮询等下一次干净触发 → 断言」。判据：查业务表 `COUNT(*)`，不是 3 的倍数（或远超预期条数）就是多轮污染，先清数据重来。

### 4.23 ★★ RETRIEVE_ARRAY 的三种 fetchType 与 sortParams

查询节点的形态由 `fetchType` 决定，出参完全不同（构造器已支持 `fetch_type` / `ids_from` / `sort_params`）：

| fetchType | 语料 | 入参 | 出参 |
|---|---|---|---|
| CONDITION | 184 | `condition`（单/多条件，单 GROUP 内多 CONDITION 为 AND） | ARRAY DTO |
| COUNT | 13 | 同 CONDITION | **OBJECT / INTEGER**（总数，不是列表） |
| IDS | 19 | **`value`** = 指向 `ARRAY<BIGINTEGER>` 出参的 SelectParam，**没有 condition** | ARRAY DTO |

- IDS 的入参不是条件：先把列表 `MAP(id)` 成标量数组再喂进来（构造器传 `ids_from=<别名>`）。
  条件字段校验必须按 fetchType 收窄，否则 IDS 会被「字段不存在」误拦。
- `sortParams` 形态 `[{"sortType":"DESC","attrType":<字段活引用>}]`，`attrType` 是实体属性对象
  （含 id/fullName/md5/dataType），不是字段名字符串。构造器原先写死 `[]`。
- ★ **多条件断言必须自带隔离条件**：只写 `processedRows>1 && <=3` 会把表里别人的行算进来
  （实测返回 6 而期望 2）。加上 `sourceTable=<本批标记>` 才是一次有效断言。
- ★ **分页已验（不需要设计器）**：`pageSearch="true"`（字符串）+ `pageInfo` 指向一个
  `CREATE_VARIABLE` 造的 PageInfo 对象：`paramType=OTHER` / `otherType=SYSTEM_PAGE_INFO` /
  `dataType=DTO` / `mappingType=attrs`，`attrs=[pageNumber, pageSize, needTotal]`（value 都是 Simple）。
  `pageInfo.selectParam` 少一个属性就 `PROPERTY_IS_REQUIRED`，实测连拦两轮：先缺 `type`、后缺 `dtoType`；
  完整需要 `type=OBJECT / dataType=DTO / dtoType=CUSTOM / udcApp / appName / javaType / path / desc / outputName`。
  DSL：`{"kind":"page_info","page_size":2}` + `{"kind":"retrieve_array","page_info_from":"pg"}`。
  实测种子 5 行 → 无分页 SIZE=5、`page_size=2` SIZE=2。
- 已验 `page_number>1` 翻页（`page_number=2` + `page_size=2` → 第 2 页 2 条 / 无分页对照 5 条，5 行种子）；未验：`needTotal` 回读总数、OTHERS、OR 语义。

细节见 `references/node-retrieve-array.md`。

### 4.24 ★★★ FILTER 过滤条件：离线编译，不需要设计器

★ **表达式里引用标量出参（SUM/SIZE/MIN/MAX）用 `{"ref": "<节点id>"}`，DTO 字段用 `{"field": "<节点id>.<字段>"}`**——两者不同，值槽里的 `{"field": "sz"}` 是节点引用（另一套语义），别混。

标量出参的 context 是**两级**（顶层 OBJECT + 子项 type=标量类型，无字段层），不是三级 DTO 树。
2026-11-03 曾因 `_build_context_entry` 硬编码 dataType=DTO 报 FORMULA_6161（operator not Math），
已修：`_node_ref` ref 带 `node_dtype`，`_build_context_entry` 识别非 DTO 走
`basic_scalar_context_entry`（/expression/check 反推出的形态 A）。事实
`expression-basic-scalar-context-gap.md`。

**先把结论摆正：含「过滤条件」字段引用的表达式，`/expression/check` + `/transform` 完全可用。**
把语料里一条真实 FILTER 表达式原样重放 → `BOOT_0000`，返回的 `executableExpr` 与设计器产出
**逐字节一致**。「必须进设计器点确定」只对「本地手拼 designData + 占位 executableExpr」那条降级路径成立。

实现：`components/construction/microflow_filter.py`，DSL 入口
`{"op_type":"FILTER","filter":{"field":"processedRows","op":"GT","right":2}}`。

三个形态，每个都错一次才通：

1. **context 要两级对象**
   ```
   根   name=<DTO 去点>  description=过滤条件  type=OBJECT  selectable=false
     └ 子   name=<DTO 去点>  description=<列表名>  type=OBJECT  selectable=true
          └ 字段  name=<字段名>  description=<中文名>  type=<字段类型>
   ```
   `uniformityParams.paramId` 用**带点**的 DTO 全名；根节点 `paramCategory=DTO`、子节点 `OBJECT`。
2. **token 有两种形态，别统一处理**
   - `OPERATOR`（`==` `!=` `>` `<` `>=` `<=` `and` `or`）：**平铺**在 tokens 数组里
     `[VARIABLE, OPERATOR, CONSTANT]`，**不带 subOps**
   - `FUNCTION`（`containsText` / `isNotNull`）：单个 token，参数放 `subOps`

   把 OPERATOR 也塞进 `subOps` → `FORMULA_6070 Operator: =, input error!`（操作符拿不到操作数）。
   这个报错看着像「类型不对」，实际是 token 结构不对。
3. **变量路径是 DTO 去点名重复两次**：`value="<Dto去点>.<Dto去点>.<字段名>"`，
   `desc="微流程.过滤条件.<列表名>.<字段中文名>"`。

实测：种子 4 行 → `FILTER processedRows > 2` 得 2 条、`FILTER taskId == '<MARK>-S3'` 得 1 条。
细节见 `references/node-list-operation.md` §9。

**FILTER 不止 `字段 op 常量`，还支持任意布尔表达式**（AST 全离线编译，同一套 check+transform）：

```json
{"op_type":"FILTER","filter":{"expr":{"logic":"AND","items":[
  {"op":"GT","left":{"arith":"ADD","items":[{"field":"processedRows"},{"const":3}]},
   "right":{"const":5}},
  {"fn":"containsText","args":[[{"field":"taskId"}],[{"const":"-S3"}]],"dtype":"BOOLEAN"}]}}}
```

构造链（都在 `components/construction/microflow_filter.py`）：`parse_filter_spec`（JSON→AST，字段按**实体字段**解析，
不是节点别名）→ `build_ast_expression`（AST→平台 expression，context 用 FILTER 专属两级「过滤条件」树，
不能用节点出参树，否则 BOOT_3000）→ `field_ref`/`field_expr`（路径 `<DTO去点>.<DTO去点>.<字段>`）。
支持 const / field / op / logic / arith / fn / cond 七种节点，`fn` 的参数组必须是 `[[a],[b]]`（每参数一组），
写成 `[[a,b]]` 是 1 组 → `FORMULA_6049 parameter number does not match`。
运行时已验证 8 类（算术 ADD / 逻辑 AND·OR / 比较 NE / 日期 year / 条件 IF / 文本 containsText / 布尔 isNotNull），
证据 `evidence/expression-runtime-2026-11-03.json`。

### 4.25 ★★ 声明「必须进设计器」之前，先离线重放一条语料样本

**「UI 才能做」是最后一种可能，不是默认结论。** 判定顺序固定：

```
① 从 scratch/pmp_schemas.json 找一条该形态的真实样本
② 把它的请求体原样重放给对应接口（expression/check+transform 这类纯编译接口）
③ 重放成功 → 形态是「上下文没拼对」，不是「被 UI 锁住」；按样本反推构造器
④ 只有重放也拒绝（返回设计态令牌/需登录态签名）时，才谈 UI
```

代价对比：离线重放 ≈ 1 分钟；UI 驱动要开 tab、算坐标、点树、弹模态，一步错重来。
本轮 FILTER 就是被「必须进设计器」误判了一整轮，实际接口一直可用。

**另一条同类教训：不要用「点不动」推断「做不到」。** 设计器是 canvas + 异步树，
坐标点击失败只说明这一种驱动方式不行，不说明平台能力不存在。

### 4.26 ★ 设计器入口 URL 必须带 `?appId=`

`/main/child-frame/udc/app-design/rule/microflow/editor/<mid>?appId=<appId>`。
少带 `appId` 会落到 `/microflow/welcome`，`flowFrame` 为空、画布不加载、点节点无反应 ——
看起来像「UI 驱动不通」，实际是入口错了。这与 L2 那节的入口要求是同一条。

### 4.27 ★★ 布尔函数与函数目录的两个坑（自动生成表达式必读）

**① 布尔函数不要包 `== true`。** 实测 `containsText(a,b) == true` 恒为 false（命中 0 条），
裸函数条件才对（1 条）。平台把布尔函数的结果当「能直接作条件」的值，再跟常量比一次语义就错。
`parse_filter_spec` 已自动解包 `{"op":"EQ","right":{"const":true}}`，但手写 token 时别踩。

**② `containsText` 参数顺序是 `(被查文本, 子串)`，不是 `(子串, 文本)`。** 反序恒 0，
已用反例流程钉死。同理其它「包含」族函数（contains/startsWith/endsWith）也要先验顺序，别按「先模式后文本」猜。

**③ 函数目录只有 `paramCount` + `argDescs`（中文），没有参数类型。** 自动生成函数调用时不能靠目录定类型：
按 `argDescs` 中文关键词推（日期→DATE、文本→STRING、长度/位置/下标/月→INTEGER、条件/布尔→BOOLEAN），
或直接拿真实字段试编译。真实 context 下逐个试编译，88 个函数里 **46 个可生成并被平台接受**；
剩余 42 个分两类：18 个聚合函数 + 2 个枚举函数要「明细表（子实体列表）字段」做参数（当前测试实体无子实体，
不是能力缺，是缺真实对象）；约 24 个是参数类型猜错（`FORMULA_6158 the N parameter type does not match`）。

要「全自动生成 88 个函数」还差：给目录补参数类型（人工标定 argDescs，或反编译前端 bundle 函数签名），
以及拿一个含子实体字段的实体验证聚合函数。

**④ 函数名不能按通用编程直觉假设，用之前先 grep 目录。** 88 函数目录里**没有** `concat`/`append`
这类拼接函数（文本拼接是 `join`/`replace`；`join` 是列表拼接，不是两字符串相加）。
假设 `concat` 存在会直接报「未知函数 'concat'（不在 88 函数目录 core/facts/udc/expression/functions.md）」——
用任何函数前先 `grep 函数名 core/facts/udc/expression/functions.md` 确认，别凭「大多数语言都有」去猜。

### 5. ★★ 判据不能依赖被测对象自己的配置

**设计验证判据时，先问：这个判据成立的前提，是不是恰好是被测对象可能破坏的那件事？**

踩过的实例：用「实体约束让默认值本身违规 → INSERT 成功 ⇔ 我传的值被应用」做判据，
而目标实体配了 20 个默认值表达式（`currentYear()`），把传入值无条件盖掉。
**判据从一开始就是坏的**，而它每次失败看起来都像「构造器有 bug」，
把一个库层面的缺陷结论（attrs 不生效）带进了事实库，方向错了很久。

同源教训：用「某字段的报错消失」当「该字段生效」——报错消失可能只是默认值恰好满足约束。

**做法**：
- 判据的双侧都要可控：正向（传 A 得 A）反向（传 B 得 B），不能只有一个方向。
- 先查被测对象有没有能盖掉你输入的配置（默认值/计算表达式/只读字段/触发器），
  有就换对象，不要靠推断绕。
- 判据只能证伪不能证实时，就换一个能证实的实现方式（如直接读生成代码）。

### 6. ★★ 源码先于实验：跑第二轮运行时实验之前，必须先读生成代码

构建产物 zip 里有**完整后端源码**（`metadata/udc/<appId>/<buildVersion>.zip`，含微流程编译出的
`Rtv…Service.java` + 实体 `*Service.java`），拉取方式见 `references/build.md`。

**成本对比决定顺序**：读生成代码 ≈ 1 分钟（拉 zip + grep）；跑一轮运行时实验 ≈ 8 分钟
（建流程 + 构建 3~4 分钟 + 等定时触发 3~4 分钟），而且失败时拿到的是症状不是原因。

所以：**第一轮实验失败后不要改参数重跑，先读那一轮生成的 Java。**
这条是本类任务里最贵的教训——曾为「写节点值不生效」连跑 6 轮黑盒实验
（Simple 字面量 / BASIC 变量引用 / DTO 字段引用 / customs 修复各来一遍，每轮 8 分钟），
最后答案在 `XxxService.preCreateBatch()` 里一行 `executeExpression(list, false, …)`，
源码里一眼可见；期间还把一个错误结论（attrs 不生效）写进了事实库。
用户的纠正：「测试其实已经推上去了，你去代码里查找一下最新的应用包，微流程编译的 service
你的业务代码你也能知道啊……runtime 也是看的这个应用包代码。」

排障次序固定为：**读生成的 Java → 读实体/服务源码 → 读运行时日志 → 黑盒试探**。
判据：**同一个现象需要跑第二轮，就说明第一轮该读代码而没读。**

### ⛔ 铁律负一：先用仓库的事实和工具，不许自己另起一套

- 「记住一定要用 xiaozhua agent 里面的事实和工具，而不是自己又在哪里瞎用。」
- 动手前先 `ls core/facts/udc/microflow/`；结构形态先挖 `scratch/pmp_schemas.json`（643 条真实语料）。
- **探测运行时路由 / 接口前先读 `references/runtime-invocation.md` 和 `references/runtime-execution-reality.md`**：哪些路由试过、返回什么都已记录，重复枚举后缀是纯浪费。
- 生成走 `components/construction/` 的构造器，闸门走 `components/udc/microflow/gates.py`，别在 scratch 手拼节点 JSON。
- **节点配置项知识先进矩阵再进代码**：任何配置项的选项/联动/取值能力，先查并更新
  `core/facts/udc/microflow/node-settings-capability.json`（矩阵），再改构造器/闸门；
  发现矩阵没有的形态，先补矩阵（带语料证据）再改代码，禁止只改构造器。
- **语料裁决优先 + 防误归纳**：落库语料（pmp_schemas.json 发布态）与后端回读态可能 casing/形态不同，
  写死约束前先确认证据来自哪一态；夹具与语料打架按语料改，语料量大者优先（如 mapping 行 value.type 恒 SelectParam 2374/2374）。
  ★ **但「手工搭的验收流」样本只证明字段存在，不证明取值正确**：同一份 `xzhAllNodesV16` 里
  BREAK / CUSTOM_ERROR 的 `type` 都写成 `ACTIVITY`（运行时被静默丢弃）、CALL_DATA_FLOW 的 `condition` 是空数组
  （平台必填）。**字段取值对错要去三处取证：前端 bundle 的 `merge:`/表单 `required` 定义 →
  运行时 `parseXxxActivity` 读了哪些键 → 校验集合的元数据键名与填充来源**，别拿这类样本当契约。
- 只在确实没有证据时才做最小真实验证，并把结论落回 facts，而不是留在会话里。

### ⛔ 铁律负二：技能和仓库是两套文件，改一边必须改另一边

**技能目录**（本文件所在，`skills/udc/xiaozhua-udc-microflow-generation/`）与
**仓库**（`<XIAOZHUA_AGENT_ROOT>`）是**完全独立的两份文件**，无任何同步机制。
只改一边必然漂移，而且要等到人发现——实测已发生：技能里补了 G34/G35 + 脚本自检，
仓库里只有代码没文档、只有 55 行草稿脚本没正式版，用户问「xiaozhua agent 里面的东西补充了吗」才暴露。

**改技能时，逐项回仓库确认这四类东西都落地了：**

| 技能里加了什么 | 仓库对应位置 |
|---|---|
| 闸门规则（G 编号） | `components/udc/microflow/gates.py` 的 `run_gates()` **函数体内**（不是文件里出现就算） |
| 闸门的判据/踩坑说明 | `core/facts/udc/microflow/generation-gates.md` 的**闸门清单表格**（`\| G<n> ` 开头那行） |
| 可复用脚本 | `scripts/`（不是 `scratch/`，不是 `_attic_pending/`），且必须自带自检与非零退出码 |
| 一次性长跑探针 / 收尾脚本 | `_attic_pending/<topic>/`，**不要放 `scratch/*.py`** |

★ **`scratch/*.py` 会在会话中途被清掉**（实测两次：跑到一半脚本消失，`can't open file`，
只能凭记忆重写）。只跑几十秒的验证探针放 scratch 无妨；任何要「建流程 → 等构建 → 等定时周期 →
清数据」的长跑脚本、以及收尾用的 cleanup 脚本，一律写到 `_attic_pending/<topic>/`，
否则等你回来执行第二步时文件已经不在了。
| 实测结论 | `core/facts/udc/microflow/*.md` 对应主题文件，不是只写在 SKILL.md |

**落 facts 时的两个硬约束（各踩过两次，`pytest` 会直接红）：**

- **完整客户应用名不能进 `.md` 结论区**（`datamigration<数字>` 这类会被 `test_deidentification` 拦）。
  写 DTO 全名用占位：`com.seeyon.<APP>.dto…`；原始证据放 `evidence/` 或 `scratch/`，那是豁免区。
  ★ **脚本（`scripts/*.py`）也属结论区**：从技能复制脚本到仓库时，argparse 的 default/help 里硬编码的
  客户名会触发 `test_deidentification`。脱敏方式：客户应用名/实例名用占位符
  （`datamigration9000000000000000001` / `znxmglpt9000000000000000001`），host 用环境变量
  （`default=os.environ.get("UDC_HOST", "")`）。注意「客户实例名」`znxmglpt` 的正则**曾缺占位符排除**
  （`datamigration` 有 `(?!9000…)`、`znxmglpt` 没有），导致占位符 `znxmglpt9000000000000000001` 也被拦——
  若遇到占位符仍被拦，先查 `test_deidentification.py` 的 `PII_PATTERNS` 是否给该类名加了排除。
- **提交只加显式文件路径，禁止 `git add <目录>`**：工作区常有别人未提交的大体量审计产物
  （`docs/audit/...` 下动辄百万行 JSON）。`git add docs/audit/` 会把它们全卷进自己的 commit，
  只能 `git reset --soft HEAD~1` + `git reset` 重做。提交后用 `git show --stat` 核对文件清单。
- **测试计数是契约**：`collect` 变了要同步 `README.md` / `docs/audit/agent-version-audit.md` /
  `docs/audit/code-reality-audit.md`（写 collect 数）与 `docs/audit/p5-stage-report.md`
  （写实际 passed 数）——两处口径不同，别写反。
  ★ **改之前先 grep 出文档里当前的数字**，别按记忆替换旧值：文档里的计数可能已被改成另一个数
  （实测按旧值替换时文档里已是另一个数，替换静默无效、契约测试照样红）。
  正确做法：`grep -oE '[0-9]{4} passed' README.md docs/audit/*.md | sort | uniq -c`，再按实际值替换。
- **改 `.md` 结论区要保住原换行符**：仓库里一部分 `.md` 是 CRLF、一部分是 LF。用 Python
  `io.open(p,'w',newline='')` 读改写会把 CRLF 文件整体转成 LF，diff 从几十行变成上千行
  （实测一次 +1512/−1271）。提交前看 `git show --stat`，整文件变动就转回原换行再 `--amend`。
- **正文带反引号时禁用 `python -c "..."` 内联写文档**：外层双引号会让 bash 先做命令替换，
  反引号里的内容被当命令执行，写出来的文档变成命令输出（实测把一节事实文档写坏，只能回滚重写）。
  长文本一律走 `write_file`，或 `cat >> file << 'EOF'`（定界符带引号才不展开）。

**反向也查**：仓库里新增的闸门/脚本/结论，同样要回技能补，否则下次开新会话时
没有这条知识（技能是唯一跨会话加载的入口）。

★ **技能内部也要查重复描述**：同一知识点（如 BASIC 入参结构、某节点的 output 键集）
会同时出现在 SKILL.md 正文和 references/ 里。改一处必须 `grep` 全部出现点一起改，
否则残留旧描述、技能内部自相矛盾（实测 desc/description 方向修正，改了
references/triggers.md 和 facts，却漏了 SKILL.md §4.10 里两条旧的错误描述，还要再单独纠一次）。
改完 `grep -rn "<关键词>"` 技能目录，确认没有漏网的旧说法。

仓库侧已有自动化兜底（`tests/test_gates_doc_contract.py`）：代码与文档的 G 编号
双向不一致 → pytest 直接红。但它**只查仓库内部一致性，不知道技能的存在**——
技能 → 仓库这一步仍然只能靠这条规则人工执行。

## When to Use

用户要求建/改/验 UDC 微流程（服务定义/事件监听/定时任务）：批量生成、逐个搭节点、报「前端显示空/报错/节点没搭/检查不过/这是糊 check」，或要做节点验收时。

也包含**线上排障**：用户甩一条 `/service/{appName}/…/microflow/MFSERVICE…` 的 URL 问「为什么返回 null / 报错」时，
按 `references/runtime-invocation.md` §5.1 先定性路由，再按 `references/runtime-log.md`「接口为什么返回 null」
用 traceId 定位到具体节点——**不要从入参猜起**。

两种通路都要会：**前端 CDP 逐节点搭（真实、可验收）** 和 **REST/GraphQL 批量建单**。节点一定是前端 `addNode` 造的，手拼节点 JSON 只能用在已确认过结构的字段上。

### ★★ pipeline 跑定时流程的四个必踩 bug（P7-E2E-1 全踩过，已修）

端到端用 `build_pipeline` + `pipe.run(trigger_type="SCHEDULE")` 跑定时流程时：

1. `save_pipeline._trigger_type(schema)` 曾写死返回 MANUAL（`return "MANUAL" if ... else "MANUAL"`），
   定时流程 create/publish 被降成 MANUAL，与 schema 里 trigger.type=SCHEDULE 矛盾，
   第二次 publish（_stage_publish）报 BOOT_3000 无 message。已修为从 schema 取真实类型。
2. `read_state` 默认 CDP 端口写死 9333，用户浏览器常在 9222 → L2 检查 WinError 10061。
   已修为读环境变量 `UDC_CDP_PORT`（fallback 9333）。
3. `PlatformBuilder.build` 对 UDC_DEPLOY_0002（app publishing 构建锁）不重试 → 直接 FAIL。
   已修为等 30s 重试最多 12 次。
4. pipeline 无 skip_l2 选项；L2 是 CDP 驱动的 UI 检查，定时任务流程的编辑器页面不稳定
   且非业务结果核心。已加 `run(skip_l2=True)` 跳过。
5. `_HttpAdapter._call` 的 curl 用 `-s`（silent）：连接失败 / cookie 过期时 stdout 空 →
   `json.loads("{}")={}` → 触发端误报「构建触发未返回 deployId：{}」，掩盖真实错误。
   诊断：看 dump 的 `build.last` 或 `failure.problems` 有没有 `redirectUrl`（SSO 登录跳转 =
   cookie 过期），或直接 curl 后端接口看是 `BOOT_0000`（正常）还是 `BOOT_1006`（登录过期）。
   **别把「deployId 空」当构建锁/参数错反复重跑，先验 cookie**。cookie 过期恢复的具体步骤：
   - 后端 `lowcode-test2` 的 `SY_ACCESS_TOKEN` 过期 → curl 回 `BOOT_1006` + `redirectUrl`（SSO 登录跳转）。
   - 前端 `localhost:3000`（编辑器）有**独立 session**，`SY_UID` 是数字 ID（不是后端的用户名），
     token 比后端更新鲜。
   - 恢复：CDP 9222 → `Network.getCookies` 读 `http://localhost:3000` 域的
     `SY_ACCESS_TOKEN`/`SY_UID`/`TK_EXP`，刷进 `scratch/_ck.txt`，再 curl 后端接口看回 `BOOT_0000`。
   - ★ `TK_EXP` 不是简单过期时间戳（前端 TK_EXP 可能“已过期”但 token 仍有效），
     判据以 curl 后端接口实际返回的 `BOOT_0000`/`BOOT_1006` 为准，别拿 TK_EXP 数字判断。

### ★ 先找构造器，不要 scratch 手拼（含「构造器本身也可能是错的」）

`components/construction/` 里已有 25 个 actionType 的构造器，**生成节点必须走它们**。在 `scratch/` 里手拼节点 JSON 是本类任务的重复性事故源头：手拼版本会漏掉构造器已处理的字段，而漏掉的又被 `checkSchema` 放过。

| 组 | 文件 | 覆盖 |
|---|---|---|
| ★ 同一 actionType 的构造器可能分散在多个文件（svc 是早期分组），import 后 `grep 'def <名>'` 确认真身再改，别按本表假定位置 | | |
| 变量/数据 | `microflow_nodes_v2.py` | create_variable（三赋值形态 value_ref/auto_map_from）/ change_variable / retrieve / retrieve_array / create_entity / change_entity / delete_entity / convert_data（5 子模式）/ call_data_flow / break_node |
| 列表/映射/逻辑 | `microflow_nodes_extra.py` | create_list / change_list / list_operation / create_map / map_operation / branch / for_count / custom_error / create_batch_entity / change_batch_entity / convert_data |
| 服务/加工 | `microflow_nodes_svc.py` | call_app_service / call_data_flow / sub_microflow / type_convert / data_mapping / for_each / event_delivery |
| 值/字段原语 | `microflow_fields.py` | entity_structure / entity_ref / field_attr / field_left_param / field_select_param / condition_group / simple |
| 端点 | `microflow_params.py` / `microflow_triggers.py` | make_end_entity / make_end_basic / make_trigger_entity / 各 trigger |

`CONDITION` 不是独立构造器——它是 BRANCH 的 `conditions[]` 子项。`CONNECTOR` 尚无构造器，动它之前先探抽屉落 facts。

**基础服务四件套（SUB_MICROFLOW / CALL_APP_SERVICE / PUBLISH_BUSINESS_EVENT / CALL_DATA_FLOW）与 CONVERT_DATA 的构造器实现在 `microflow_nodes_extra.py`**（`microflow_nodes_svc.py` 是早期分组，动之前先 import 一下确认真身）。它们的必填/真实形态与三个前端绑定坑见 `references/node-shapes.md` 的「基础服务类节点」。

**但「有构造器」不等于「构造器是对的」**：构造器只保证结构齐全，不保证语义正确，它可能漏字段、也可能写出前端不认的形态（`map_operation` 早期版本不写 `basic`/`structure`/`nullPromptMessage`，`create_list` 不写默认值，`create_map` 的 `generics` 形态错）。所以用之前**先拿构造器产物过闸门**：

```python
node = map_operation(b, map_node, key_value="k1", op_type="GET")
assert not run_gates({"nodes": [node], "endNode": {...}, ...})
```

发现构造器漏字段就地补（加参数或按分支走），**不要绕过它在生成脚本里手改 dict**——手改的版本下次生成又回归旧缺陷，而且手改不留痕，下一个人还会踩。

## ⛔ 命名铁律：节点必须带业务语义

设计器卡片只显示 actionType + 出参 `desc`。一排「匹配数量 [整数]」会让用户在选参数时根本分不清取哪个 —— 这是用户实际提出过的返工原因。

- `caption` = `动作-业务对象`，例：`统计-启用数据源数量`、`更新-草稿转正式`、`调用-采购状态回写子流程`。
- 出参 `desc` = 业务名，例：`启用数据源数量`、`剩余草稿数量`、`处理结果文本`。
- 禁止 `匹配数量 / 结果 / 数量 / 数据` 这类占位名；每个统计/查询/变量节点的出参必须能单独读成一个业务事实。
- 变量名同样处理：`处理结果汇总` 而不是 `变量1`。

## 流程（按序）

1. **取证构造契约，不猜字段**：反编译 `MicroFlowComponentUtils.buildAttrValue`（值字段映射）、前端 bundle 搜表单 `{key:"...",label:"..."}`（回显绑定）。生成器：`components/construction/`（NodeBuilder / microflow_triggers / microflow_nodes*）。
2. **拉定义清单**：实体事件=`udcEntityPrimarySelectByAppidAppGet` + 逐实体 `udcMicroflowFilterEventPost`（与前端「选择事件」对话框同源）；MF 自定义事件=同接口 `sourceTypes:["MICRO_FLOW_EVENT"], entityId:0`；MQ=`udcMicroflowFilterMqPost`。事件 DTO 字段用 `udcDataTransferObjectSelectDtoWithAttrsGet`（id 从 `udcMicroflowSearchMessageDtoPost` 拿）。
3. **写 schema（先看 6 组合矩阵，勿混）**：见「类型×触发 6 组合」节。**CUSTOM 无节点链**，只有首节点 + 出入参；**事件/定时无出入参**（标准和自定义都一样）。标准 MANUAL 才搭节点链。
4. **建单+检查**：`udcMicroflowCreatePost` → `udcMicroflowUpdatePost`（state=RELEASE）→ `udcMicroflowCheckSchemaUpdatePost`。check 返回空/None 时重试 update+check（偶发，非真实错误）。
   ★ **流程 `name` 只能是“字母开头的字母+数字”**：带下划线/纯数字会报
   `UDC_ENTITY_0001 … must use a combination of letters and numbers that first are letters`。
   生成名字用 `p5wrt` + 时间戳尾号，别用 `p5_wrt`。
5. **全量验证**：`udcApplicationDoDetectionPost` 必须 ERROR=0，再逐条 FindByIdGet 复核 state=RELEASE。
6. 让用户页面上点「检查」复核前端绑定类问题（checkSchema 报不出前端绑定错误）。

## 检查链路（三层，缺一层就会「后端绿、前端红」）

1. `udcMicroflowCheckSchemaUpdatePost`（GraphQL operation）——结构校验，返回 `{check:true,errors:0}`。**body 要完整 DTO（含 `guid`，从 `udcMicroflowFindByIdGet` 回读拿，不要硬编码），不是只传 `id`+`dataSchema`**。
   **但发布要走 REST `/service/udc/microflow/checkSchema/update`——GraphQL `udcMicroflowUpdatePost` 发不出去。** 用 GraphQL 带 `state:"RELEASE"` 提交会返回 `BOOT_0000 SUCCESS` + `content:1`，回读仍是 `DRAFT`：接口成功不等于状态改了。REST 这条 body 是 15 字段平铺（`appId/id/name/caption/type/triggerType/state/dataSchema/serviceInterface/sourceType/creationMethod/groupType/versionCode=100/openApi="STOP"/restApi="DISABLED"`，另加 `microFlowGroupId`），`dataSchema` 传 JSON 字符串；返回读 `data.content.{check, errors, errorMessage[]}`，`errorMessage` 的 `nodeCaption/path/errorCode/message` 直接指到出错节点。body 写错时它返回 `null` 而不是报错，别拿 null 当失败。
2. `udcApplicationDoDetectionPost` + `udcApplicationSearchDetectionPost`——应用级一致性检测，必须 `ERROR` 数为 0（WARN「未保存」可忽略）。用户说「检查」指的就是这个。
3. 前端「一致性检查」——前两项都绿仍可能红（title/inApp/nodeId 前缀这类前端绑定错误只有前端认得出）。必须让用户在页面上复核。

调用 SearchDetection 后要 sleep 3-4 秒等异步结果；直接读会拿到上一轮结果。

**发布时 `versionCode` 必须是 100**：从 `udcMicroflowFindByIdGet` 回读的 DTO 里 `versionCode:0` 直接拿去 `CheckSchemaUpdatePost` 会报 `BOOT_1001 Parameter Error`（同样不给明细），改成 100 立刻 `check:true`。校验通过不代表字段可省——DTO 里每个键都按平台契约校验，缺省值不是安全值。

## 生成节奏铁律（用户严令：每个节点确认保存一次）

错误做法是一次性拼完整个 schema 再 update。正确节奏，每个节点写入后立即走一遍闭环：

1. **写入节点**（POST /service/udc/microflow/update，DRAFT 态）
2. **刷新元数据**：重新 FindByIdGet 拉回最新 dataSchema（后端会对写入的节点做规范化，节点 id/输出名可能与写入值不同）——后续节点引用一律用**回读后的真实节点 id/输出名**，不用内存里拼的
3. **拿前序回读结构组装下一节点**（引用 outputName/nodeId 全部来自回读）
4. 全部节点完成后再 update + checkSchema + RELEASE

跳过第 2 步直接拼下一节点 = 引用名对不上 = 「前序节点发生变更请重新选择」。这就是批量生成必须逐节点 update+回读、不能一把梭的原因——所以单次批量别超过个位数，跑完人工抽查前端回显。

**增量推进可行性（方案2「一个一个处理」的技术基础，实测）**：checkSchema 在**中间态也返回 check:true**——即使只有 trigger + 首个节点、没有 endNode，也能单独 check 通过。所以可以按「建单(trigger+入参+首节点) → check → 追加下一节点 → check → … → 最后补 endNode 出参 → check」逐节点推进，每一步独立校验，出错即定位到刚加的那个节点，不必等整条流程拼完才验证。这是用户偏好「一个一个处理」而非一把梭的正确落地方式。

## 批量验证（多流程一次构建，别一个个构建）

**构建是应用级的**（`deploy-normal {appId}` 一次构建编译该应用所有已保存的 RELEASE 流程），
所以「验证 N 个形态」的正确节奏是**批量 deploy N 个流程 → 一次构建 → N 个流程同时触发 →
读库断言 N 个结果**，不是每个流程单独「保存→构建→等触发」循环（N×10 分钟，缩到 1×10 分钟）。

- 每个 case 一个独立流程 + 独立测试数据（taskId 带唯一 MARK），避免互相污染。
- SCHEDULE 触发最快要等 5 分钟（平台约束 MINUTE 最小 5），但批量后是「一次性等待」——
  N 个流程在下一个周期同时跑。MANUAL 秒级触发入口未找到（MANUAL 流程=服务定义，运行走
  AppService GraphQL，op 名未确认），别为它卡住主线。
- ★ `composer.trigger_schedule()` 默认 `cycle_type="DAY"/rotation_type="DAY"/value="1"`
  （每天一次）。要短周期触发必须显式传 `cycle_type="SIMPLE", rotation_type="MINUTE",
  value="5"`——漏传就是「每天一次」，流程看着 RELEASE 但永远等不到触发，会被误判成
  「SCHEDULE 没生效」（批量验证第一轮 conv-basic2str 未写库的根因，回读 trigger 的
  cronRules 显示 cycleType=DAY 才定位）。
  ★ **`value` 必须 ≥ 5（MINUTE 最小 5）**：显式传 `value="1"` 也会让调度任务**根本不注册**
  （`ctp_job_info` 0 行、`udc_rt_app_log` 0 行），不是「触发慢」是「不触发」。排障先
  `SELECT * FROM ctp_job_info WHERE job_name LIKE '%<流程 name>%'`（列是 job_name 不是 job_code），
  0 行 = value 非法/未注册，改 value="5" 重发 + 重新构建。
- 先搭框架（批量构造→批量 deploy→一次构建→批量触发→读库断言），用 2~3 个 pilot case
  跑通链路，再补全剩余 case；别一上来就写满全部 case 的 draft。
- 未验证形态清单（shape matrix）从 `capability-matrix.md` 的「未验」条目提取，不重验已
  RUNTIME_VERIFIED 的形态。批量框架脚本放 `_attic_pending/batch-verify/`（长跑，别放 scratch）。

## 复刻对方应用业务到本应用（只读 → 本地复刻）

用户要求「拿别人平台的真实业务，在我们这边复刻验证」时的固定顺序（细节见 `references/replication-workflow.md`）：

1. **只读对方**：从已落地的语料快照取流程形态，绝不调对方写接口。
2. **业务对齐**：先确认本应用有没有等价实体/字段，能不能承接这个业务语义。
3. **缺就本地补**：在本应用建实体/自定义对象/枚举，不碰对方环境。
4. **生成**：照契约表（G23）→ 构造器 → G 系列闸门。
5. **提交**：publish，`checkSchema.errors` 必须为空。
6. **自证**：`prove()` 四层，检测明细按流程名/id 过滤，别把应用既有问题算到新流程头上。
7. **构建**：DELTA → `backBuild.log` 的 BUILD SUCCESS 才算完。

覆盖验收：一轮里至少包含 **定时 / 事件 / 标准** 三类触发各一条。

## 生成流水线（顺序固定，跳步就制造假错误）

1. **业务理解**：目标 / 输入输出 / 触发方式 / 边界条件
2. **逻辑链路**：伪代码 → 节点顺序 → 数据流 → 分支 / 循环 / 异常路径。**先于任何 JSON 生成**
3. **依赖解析**：动态元数据走接口（服务方法 / 事件对象 / 生单规则 / 变量），静态结构走契约与模板
4. **构造**：NodeBuilder → 构造器 → `MicroflowComposer`
5. **L1 静态闸门**：G1–G40（G30 赋值方式 / G31 引用链类型 / G32 CONVERT_DATA 子模式形态（含 javaType）/ G33 生单规则引用 / G34 实体无 create / G35 字段被默认值表达式覆盖 / G36 DELETE 模式与字段自洽 / G37 引用槽 outputName 不能为空 / G38 逻辑节点 type 必须等于 actionType / G39 条件右值必须是带 type 的槽 / G40 CHANGE_LIST 四动作形态）+ 契约校验，0 浏览器
6. **保存草稿**：先让整图落库，前序节点才可能被引用
7. **平台校验**：表达式 API + 应用一致性检测。**必须在保存之后**——未落库就校验只会得到「引用不存在」这类假错误
8. **定向纠错**：按 `nodeCaption`/`path` 定位到节点字段，改**构造器规则**而不是改这一次的 dict
9. **发布 → 构建 → 运行**

## UI 校验分三级（不要每次全量开抽屉）

| 级 | 做什么 | 何时跑 |
|---|---|---|
| L1 本地静态 | 契约 / 必填 / 类型 / 引用形态，0 浏览器 | 每次必跑 |
| L2 页面整体状态 | 开一次编辑器，一次性读 redux `flowNodes` 全量 + `isCompleted`，对照契约；
  现成实现 `components/udc/microflow/live/l2_state.py`（`read_state`/`check_state`，43 节点约 3s）。
  **入口必须是 `/main/child-frame/udc/app-design/rule/microflow/editor/<mid>?appId=<app>`**；
  旧的 `.../rule?appId=&id=` 会落到列表页，`nodes` 返回空且不报错（会让 UI 复测假绿）。
  ★ 调用方必须自己判 `nodes` 非空：`check_state({}) == []` 是「没数据」不是「没问题」。
  **边界：04004「属性指纹」类问题 L2 契约层看不见（实测 04004 流程 L2 报 0 问题），这类仍归 L3** | 每次必跑 |
| L3 抽屉 | 逐个开抽屉看红字 / 空下拉 / 失效项 | 仅新形态、动态引用（子微流程 / 自定义服务 / 生单规则 / 创建变量）、曾出错节点、抽样回归 |

已多轮验证过的稳定节点不必每次用 UI 再证明一遍；UI 的职责是**发现未知问题**，不是重复验证已知知识。
逐节点开抽屉约 2.45s/节点（11 节点 37s），L2 只开一次页面，耗时与节点数解耦。

## 当前阶段主线：P5 全自动交付（P0–P4 已完成）

节点构造器（26 类）、G1–G38 闸门、P2 表达式引擎、P3 逻辑图执行器、
P3.1 循环作用域、P4 需求编译器均已收口。
生成微流程一律走逻辑图，**不要**写命令式 `comp.step(...)`：

```python
res  = BusinessRequirementCompiler(lr).compile(draft, app_id=..., app_name=..., text=需求原文)
# res.status: READY / AMBIGUOUS / BLOCKED；BLOCKED 时 res.graph 必为 None
schema = LogicGraphRunner(comp, resolver=res_, backend=CurlBackend(host, ck)).run(res.graph)
```

分工铁律：**LLM 只产「业务意图草稿」，Python 确定性生成逻辑图并执行**。
LLM 不许直接产平台 JSON，也不许写 Python 调构造器。

### P7-E2E-2：IntentDraft schema + 宿主 LLM Prompt（已交付 2026-11-03）

「LLM 理解业务 → 产草稿」已产品化，不再靠手工构造草稿：

- `components/construction/intent_draft_schema.py`：IntentDraft 正式 schema。
  `NODE_SPECS`=28 kind 字段单一事实源（与 `_STEP_KINDS` 双向一致，契约测试锁）；
  `VALUE_SLOTS`=值槽三态（const/field/input）；`EXPRESSION_FORMS`=表达式十形态；
  `to_json_schema()`/`render_markdown()` 导出、`validate()` 结构校验。
- `components/construction/host_llm_prompt.py`：`render(requirement, entities)` 产
  system+user prompt，硬边界=不产平台 JSON、不猜实体名、跨环境 id 只写业务名。

实测闭环：宿主 LLM 读自然语言需求 → 产中文草稿 → 归一化（任务ID→taskId 等）
→ SUM 聚合 → 数据库 failed_rows=8 正确（事实 `p7-e2e2-llm-draft.md`）。

必读：`references/logic-graph.md`（图格式 / 十个 DSL 形态 / 循环作用域 / 执行器坑）、
`references/requirement-to-graph.md`（P4 职责边界 / 真名解析 / 三档产出）、
`references/delivery-pipeline.md`（P5 阶段状态机 / 五道闸门 / ExpressionFinalizer 回读判真）、
`references/expression-engine.md`（★ 含字段引用走 transform 全自动，§十五）。

### DSL 入口铁律：声明 / 执行器 / composer step 三者必须一一对上

2026-11-02 核对发现 DSL 是**双向不一致**的（比「缺入口」更严重）：

| 症状 | 后果 | 当时的 kind |
|---|---|---|
| 声明了但没执行器 | `validate_graph` 放行，跑到一半 `GraphError: 还没接执行器` | `call_app_service` / `data_mapping` / `delete_entity` |
| 有执行器但没声明 | `validate_graph` 直接拒，执行器永远用不到 | `custom_error` |

现在 27 个 kind / 24 个执行器（branch、for_each、for_count 走 `_exec_branch`/`_exec_loop`），
`tests/test_dsl_step_coverage.py` 用 introspection 守这三条：
**加 kind 必须同时加执行器和 composer step**，否则测试立刻红。

★ 但「接线 ≠ 能跑」：`PUBLISH_BUSINESS_EVENT` 只到 LIVE_EXECUTED（无订阅者时投递无痕，见 §4.6）；
`CALL_DATA_FLOW` 已升 RUNTIME_VERIFIED（`udc_rt_data_flow_log` 读侧确认，见 §4.8）。
接线只是让它「能被生成」，不代表「能跑对」——每补一个入口都要配一条读侧证据才算数。

### 交付状态口径（铁律）

全链路跑通到 `BUILD_SUCCESS` 才算交付完成。`SAVED` / `PLATFORM_VALIDATED` /
`NEEDS_UI_FINALIZE` / `PUBLISHED` **都不是成功态**，任何一环不许静默跳过。
「保存成功」「checkSchema 绿」「构建成功」三件事各自独立，不能互相代替。

### 进度汇报口径：给时间点，不给选择题

被问「现在什么进度 / 还要多久能测」时，只给两样东西：

```
① 已完成的（带提交号 + 测试数 + 能力分级），不报「大致做完了」
② 分阶段的具体时间点：「N 天后可测 X」「N 天后可测 Y」，并标明卡在哪
```

**不要用 A/B 选项结尾**（「要我先做 A 还是先做 B？」）—— 用户要的是推进，
不是帮他做选择题；定了路线就直接往下做，阻塞点写成一句话陈述即可。
工期估算按真实工作量给区间，不美化；有不确定性就点名是哪个子模块。

### 被问「能不能正常生成了 / 现在什么状态」：先查代码，再分两栏答

这类问题是在验收能力边界，**凭记忆回答一定错**（能力表会变，记忆不会跟着变）。
先跑一次实际盘点，再答：

```python
# 构造器覆盖：别数 dir() 的个数就下结论，要拿全量 actionType 去差集
steps = {k[4:] for k in dir(MicroflowComposer) if k.startswith("_st_")}
# 逻辑图 DSL：结构节点不在 _st_ 里，要单独查 _STEP_KINDS
# 能力分级：读 references/capability-matrix.md 与 runtime-log.md 的「能证明/不能证明」
```

答法固定为两栏，**不要把「编译过」混进「跑通过」**：

```
① 端到端验证过的 —— 逐行给证据（deployId / 执行时间 / success / 返回 ID），带数字让人能核对
② 我不能说没问题的 —— 逐条点名哪个节点/哪个环节停在哪个级别，为什么
```

第二栏是重点。用户问「可以吗」，只答「可以」等于隐瞒；正确是「可以，但 X 只到
BUILD_VERIFIED、Y 还没验、Z 是平台限制」。**未验证项必须主动列出来，不等用户问。**

汇报里出现的每个能力声明都要能对到证据源（facts 文档 / 运行日志 / 构建记录），
不能对到「我记得跑过」。

**被追问「给你需求成功率多少 / 简单中等困难能到多少」时，不要只给一个总数。**
按复杂度分三档给区间，并且必须同时说清**卡点性质**（这比数字有用）：

```
简单 85~95%   失败基本是构造错，闸门拦得住，改一次就好
中等 60~75%   失败在配置项细节（attrType 键 / 表达式右值形态 / 循环内写要 RETRIEVE 中转）
困难 30~50%   失败在平台依赖（真实方法签名 / 数据流对象 / 映射行），不是构造问题
```

分档依据与逐节点验证档见 `references/capability-matrix.md` §四，数字变了要同步改那边，
不要在这里写死第二份。

### ★ 含字段引用的表达式也是全自动的（2026-11-01 结论反转）

**`/expression/check` 与 `/expression/transform` 对含 VARIABLE 的表达式完全可用。**
从设计器点「确定」抓到的真实请求体（5 字段：`resultTypeInfo` / `schemas` /
`tokens` / `isMultiSelect` / `terminalSupportType`）原样离线重放 → `BOOT_0000`，
返回的 `executableExpr` 与设计器生成的**逐字节一致**。

P4 时期报 `FORMULA_6058` 是 DTO 的 schemas/context 结构不对，不是接口不支持。
那些 bug 修完后 `_dto_has_variable` 的跳过分支成了多余 workaround，已删除。

**教训：临时绕过必须在根因修复后复查**，否则会把「接口不可用」这种错误结论固化进事实库。

`executableExpr` 格式 = `<44 字符固定 Base64 标记> + <URL 编码表达式>`，
前缀跨表达式恒定，**不需要逆向也不需要自己生成**，transform 直接返回。
详见 `references/expression-engine.md` §十五。

## 能力边界：每轮只提升通用能力

- 不再为「多生成几条业务」而生成；每条测试都要让节点 / 表达式 / 组合规则变强。业务只作回归语料，不做模板。
- 节点状态五级（用户定调，不用单一 VERIFIED 掩盖差异）：CONSTRUCTED（闸门过）/
  SCHEMA_VERIFIED（checkSchema+发布 0 错）/ UI_VERIFIED（prove 全绿）/
  BUILD_VERIFIED（backBuild.log BUILD SUCCESS）/ RUNTIME_VERIFIED（真实执行业务结果正确）。
  **只有构造器/只发布/只有页面通过的节点，一律不许标成端到端 VERIFIED。**
  实测：SCHEMA+UI+检测全绿的流程照样构建编译失败（见 `references/build.md` 构建链），
  所以 BUILD 是独立维度、必跑。
  RUNTIME 在**沙箱侧**执行，udc 网关上没有执行入口（这是对的，别再去试
  `/service/udc/runtime/execute` 之类的路径）。
  **但运行结果可以从日志侧验证**：`POST /service/{appName}/udc-runtime/app-log/search/microflow`
  能读到每次执行的 success / 耗时 / traceId ── 见 `references/runtime-log.md`。
  **更快的路子是直接查业务库表** `<appId>_<env>.udc_rt_app_log`（`micro_flow_code` / `node_id` / `input` / `error_msg` / `request_id`），无会话也能查；
  报「页面规则调用微流程执行失败」时先查它再读代码——判读口诀、查询模板与「绑定错 vs 时机错」的对照法见
  同级技能 `xiaozhua-low-code-environment` 的 references 目录下 `udc-runtime-app-log-diagnosis.md`。
  2026-11-01 已实证：生成器造的只读定时流程 publish → build(SUCCESS) → 定时触发
  → 日志 `success=true 6ms`，链路 `graph→construct→create→publish→build→sandbox→execute→log` 全通。
  ★ 仍不能证明：前端触发/子流程触发/并发/失败路径，以及下面未列出的写节点。
  **写节点已 RUNTIME_VERIFIED 的样本**：`CREATE_ENTITY`（插入返 ID + 字段逐个对上）、
  `CHANGE_ENTITY`（库内两字段变更 + version 递增 + update_time 变化）、
  `DELETE_ENTITY`（SELECT_PARAM 模式；目标 id 查 0 行 + 对照 id 查 1 行）、
  `CREATE_BATCH_ENTITY`（每轮插入 1 行、值全对）、`CHANGE_BATCH_ENTITY`（999 被写回 111，两行 update_time 完全相同）。
  `BREAK` 同样是 RUNTIME_VERIFIED（同流程双循环对照 3 行 : 1 行，见 §4.5）。
  `CALL_DATA_FLOW` 同样是 RUNTIME_VERIFIED（`udc_rt_data_flow_log` 记下 `dataflow_mapping_id=<行 id>`、
  `is_success=1`；仅 CONDITION 形态，`SELECT_PARAM` 无样本 G33 不放行，见 §4.8）。
  `PUBLISH_BUSINESS_EVENT` 也是 RUNTIME_VERIFIED——自建 `MICRO_FLOW_EVENT` 订阅流程，
  订阅端把收到的字段写库、与投递值逐字比对（见 §4.6）。
  `CALL_APP_SERVICE` 同样是 RUNTIME_VERIFIED（流水号组件连取三轮递增落库，见 §4.20）；
  `DATA_MAPPING` 同样是 RUNTIME_VERIFIED（列表映射后批量写，值逐字相等，见 §4.21）。
  ★ **别在本节维护全量清单**（会漂）：当前等级 + 范围限定 + 证据文件一律以
  `python -m components.udc.microflow.capability_registry [ACTION]` 为准，
  生成时看 `mc.advisories` 就知道本次流程里哪些节点还没运行证据。
  验证流程与判据见 `references/runtime-log.md` 与
  `core/facts/udc/microflow/node-change-delete-entity.md`。
  盘点方法与当前矩阵见 `references/capability-matrix.md`。

- ★★ **写节点「值不生效」的根因不在构造器：先查实体默认值表达式**

  症状：`create_entity(fields={...})` 配的字段值运行时**看不到效果**，报
  `UdcEntityCheckException`，且报错值恒等于某个平台默认值（如当年年份）。
  publish / build / UI 三层全绿，只有真跑才暴露。

  **根因（源码级已确证）：实体字段配了「默认值表达式」，且 `requireNull=false` 时无条件覆盖。**
  实体的 `XxxService.preCreateBatch()` 里为每个配了表达式的字段生成一条：

  ```java
  executeExpressionXxx(list, false, Dto::getF05dec, this::exp…, Dto::setF05dec, null);
  //                    ↑requireNull=false
  ```

  而 `executeExpressionXxx` 的分支是：

  ```java
  if (requireNull) { if (isNull(dto.get字段())) dto.set字段(表达式结果); }
  else             { dto.set字段(expressionFunction.apply(map)); }   // ★ 无条件覆盖
  ```

  所以传入值先被正确写入 DTO，到 `create() → preCreateBatch()` 又被表达式结果整个盖掉。
  常见表达式是 `DateFunction.currentYear()`，于是所有未显式配约束的字段全变成当年年份。

  **实测数据**：某验收实体 20 个字段全配了 `currentYear()` 表达式，而字段约束是
  `整数≤100 / 小数≤999.99` —— **2026 天然违反它自己的约束，这个实体永远插不进任何数据**，
  传什么值都一样。拿它做验证，得到的结论必然是「值不生效」。

  **处置**：
  1. 做写验证前先扫目标实体的 `domain/service/XxxService.java`。
     直接用 `scripts/entity_write_capability.py <metadata.zip>` 出矩阵，不要手写 grep：
     它同时给出 `has_create`、每个字段的表达式与 `require_null`，外加可直接拿来验证的实体清单。
     **优先选覆盖字段为空的实体**；实际项目里绝大多数有 `create` 的实体只有 `getUpdater`
     （修改人）一条表达式，那类可用。
  2. 「表达式数 0」还不够，还得看 AppService 有没有 `create`（见下条硬约束）。
     这两个条件必须**交叉筛**：实测某应用 24 个实体，表达式数 0 的那批大多恰好没有 `create`，
     能用的反而是「有 create + 只有 getUpdater」那批。
  3. 拿生成代码确认 attrs 到底是生效还是没生效，**不要再靠运行时症状反推**——
     见 `references/build.md`「构建产物 zip 是完整源码」。

- ★★ **`CREATE_ENTITY` / `CHANGE_ENTITY` 只能用在 AppService 有对应方法的实体上**

  节点编译成 `xxxAppService.create(SingleRequest<Dto>)` / `.update(...)`。
  实体没有该方法时，构建 40 秒就 FAIL：

  ```
  Rtv…Service.java:[118,138] 找不到符号
    符号:   方法 create(SingleRequest<…Dto>)
  ```

  实测某应用 24 个实体里 6 个没有 `create`（多为「明细/子表」类实体）。
  **已产品化为闸门 G34**（`gates.py`，能力表 `core/facts/udc/microflow/entity-write-capability.json`），
  生成时就会拦，不用手工查；但闸门依赖能力表存在，表缺失时静默跳过——
  给新应用写流程前先跑一次扫描补表：

  ```bash
  # 在构建产物源码里查（拿到 zip 后）—— 直接用脚本，不要手写 grep
  python scripts/entity_write_capability.py meta.zip --out entity-write-capability.json
  ```

  脚本同时给出「有 create 的实体」和「哪些字段会被默认值表达式覆盖」，
  并列出 `recommended`（有 create 且无覆盖字段）——做写验证直接从这里挑。

  没有 create 的实体只能用 `retrieve` 族读，不能挂写节点。

- ★★ **`attrType.customs` 模板污染：是真缺陷，但和运行时无关**

  `create_entity` 里 `at = dict(proto)` 从模板 attrType 复制骨架，而 `field_attr()`
  造的键集**不含 `customs`**，于是模板字段（`f01text`）的 customs 原样带给了每个字段——
  所有字段都写着 `customs.dataType="STRING"`、`customs.name="f01text"`。

  已修（直接用实体属性自带的 `f["customs"]`，与真实样本逐字段一致）。
  **但修完运行时报错一字不差** —— 它不是「值不生效」的根因，别把它当答案。

  仍然值得记的通用规则：**凡是「从模板复制骨架 + 用字段元数据覆盖」的地方，
  必须逐个核对骨架带过来的字段级元数据块有没有被真正覆盖。** `dict(proto)` 后接
  `update(field_attr(...))` 看着像全覆盖，实际漏掉的键会静默继承模板字段的身份，
  而且 publish / build / UI 三层都不报。

- ★★ **写节点验证的假设排除清单（别再重复走）**

  | 假设 | 结论 |
  |---|---|
  | 构造器形态/结构有缺陷 | ❌ 设计器改值再保存回读，与构造器产物**逐字段完全一致** |
  | `mappingType` 是模板残留 | ❌ 契约 32 个真实样本 100% 都有（MUST 级），被组装闸门拦回 |
  | 字面量 `Simple` 不生效、必须用 `SelectParam` 引用变量 | ❌ 字面量完全能用，三种形态运行时都生效 |
  | 字段 dataType 与实体定义不匹配 | ❌ 实体 `f03int=INTEGER` / `f05dec=DECIMAL`，传入一致 |
  | `attrType.customs` 污染是运行时根因 | ❌ 是真缺陷（已修），但修完错误不变 |
  | 平台读的是 `mapping` / `value` 而不是 `attrs` | ❌ `attrs` 就是生效的，生成代码里直接写着 `setF05dec(1.5)` |
  | 实体字段有默认值 | ❌ 实体 `customs` 只有标志位，**没有**实际默认值 |

  ★★ **不要用「某字段的报错消失了」当「该字段生效」的判据。**

  探针实体上 `f02multi` 从「不可为空」变成不报错，曾被当成「STRING 字段生效」的证据。
  真跑时节点 input 的实体 DTO 是：

  ```jsonc
  {"f01text":"", "f02multi":"2026", "f03int":2026, "f05dec":2026.00}
  ```

  **所有字段都是平台默认值**，`"2026"` 恰好满足非空约束而已。

  正确读法：**看节点 input 的实体 DTO 里每个字段的真实取值，逐个对上你传的值**。
  但注意：input 里的值是 **insert 前**的快照，它等于你传的值 **只证明 attrs 生效**；
  要证明「最终落库的值」，得看 `output` 里的返回 ID + 实体默认值表达式是否又盖了一层。

- ★★ **写节点 attrs 的三条路径：字面量最省事，`name` 是唯一编译期陷阱**

  真实样本（生产母版 `xzhAllNodesV16`）里 CREATE_ENTITY 的每个 attr 都是：

  ```
  CREATE_VARIABLE_uX6yCl   output.dataType = DTO     ← 实体类型变量，不是 BASIC
  CREATE_ENTITY.attrs[].value = SelectParam {
      id:         "…Dto.f03int"                    ← 字段 fullName
      name:       "f03int"                          ← 纯字段名
      key:        outputName + "…Dto.f03int"
      outputName: "_CREATE_VARIABLE_uX6yCl"
  }
  ```

  三段式路径（仓库全都有，只是逻辑图 DSL 之前没串起来）：

  ```python
  rec = mc.step("create_variable", "rec", title="rec", entity=EM["caption"])  # 注意传实体名，传 dict 会 unhashable
  mc.step("change_variable", "fill", target="rec", entity=EM["caption"],
          set_fields={"f03int": 1, "f05dec": 1.5, ...})
  fields = {f: mc.refs_field(rec, f) for f in (...)}
  mc.step("create_entity", "ce", entity=EM["caption"], fields=fields)
  ```

  `mc.finish()` 必须显式传 `trigger=`（否则 `scheduleCronRule` 丢失 →
  `[手动触发].scheduleCronRule PROPERTY_IS_REQUIRED`）；`basic_out` 必须等于引用节点的
  `output.dataType`（`create_entity` 构造器产出的是 `BIGINTEGER`，写 `DTO` 被闸门拦）。

  ★★ **`refs_field()` 的 `name` 必须是纯字段名**。写成 `"<outputName>.<field>"` 时，
  平台编译期把它当 DTO 的嵌套类去解析，构建 40 秒就 FAIL：

  ```
  Rtv…Service.java:[172,189] 找不到符号
    符号: 类 _CREATE_VARIABLE_xxx
    位置: 类 …dto.YsFull6956Dto
  ```

  这个错误只在「引用 DTO 字段」这条路上出现——字面量和 BASIC 变量引用都能编过，
  所以它藏了很久。**凡是从出参名拼出 `name` 的地方都要检查：`name` 是叶子字段名，
  `key` 才是 `outputName + 字段全名`，两者不是一回事。**

  三条路径全部实测过（都是在默认值表达式=0、有 `create` 的实体上跑的干净验证）：

  | 路径 | 形态 | 构建 | 运行时 |
  |---|---|---|---|
  | 字面量 Simple | `{"type":"Simple","simple":1}` | 成功 | ✅ |
  | 引用 BASIC 变量 | `id=""`, `key=outputName` | 成功 | ✅ |
  | 引用 DTO 变量字段 | `name="f03int"`, `key=out+Dto.f03int` | 成功（修 name 后） | ✅ |

  **三条都能用，`attrs` 是生效的。** 早前得出「三条全不生效」是因为目标实体配了
  默认值表达式（见上条），把传入值整个盖掉了。

  ⇒ 能用字面量就用字面量（最少的节点、最少的引用链）；只有当值确实来自前序节点时才走变量引用。

  ★★ **RUNTIME_VERIFIED 的硬证据长什么样**：看节点 input 的实体 DTO 里
  **每个字段的真实取值逐个对上你传的值**，且 `output` 是「插入成功返回ID：<平台生成的 id>」：

  ```jsonc
  input : {"id":4526324842265571554, "taskId":"P5VFY…", "lastOffset":123,
           "processedRows":456, "createTime":1793592360253, …}
  output: 插入成功返回ID：4526324842265571554
  ```

  平台生成的 `id` + `output` 含返回 ID = 真 INSERT 了；字段逐个对上 = attrs 真被应用。
  两个条件缺一个都不算 RUNTIME_VERIFIED。数据面回查接口不现成（列表走动态选择器），
  用运行日志详情就够。

  证据：`core/facts/udc/microflow/write-node-runtime-gap.md`（§12 为源码级定论）。

- ★★ **改构造器前先查契约统计，别靠形态直觉**：`core/facts/udc/microflow/node-contract-from-samples.json`
  记录每个 actionType 的键级 MUST/OPT 与样本数。曾凭「真实 CHANGE_ENTITY 没有 mappingType」
  推断它是模板残留并 `pop` 掉，结果契约显示 **32 个真实样本 100% 都有（MUST 级）**，
  当场被组装闸门拦回。不同 actionType 的键集不可互推——按 actionType 分别查。
- 事实（验证过的规则）/ 证据（原始响应与日志）/ 契约（必填与类型）/ 闸门（拦截）/ Skill（路由）分层存放，**同一知识只写一处**。

## 正式业务流程 vs 验收流程：建什么留什么，先分清

用户说「建业务」「建给我看」「我检查」时，要的是**正式业务流程**，不是验收流程——这两类不能混：

| | 验收流程（验证用） | 正式业务流程（交付用） |
|---|---|---|
| 目的 | 验证节点形态/契约，验完删 | 承载真实业务，留给用户检查、上线 |
| 触发 | 常 SCHEDULE（秒触发验证）或临时 MANUAL | MANUAL 服务定义（有入参/出参） |
| 命名 | `p5`/`p6`/`batch` 等临时前缀 | 业务语义名（`mf01bizquota` 等） |
| 收尾 | cleanup 删掉（§4.7） | **RELEASE 留着，不删** |
| 数据 | 造种子 + 唯一 MARK，验后清 | 真实业务数据流（外键引用前序 ID，不硬编码） |

判别信号：用户说「我检查」「建给我看」「这是业务」→ 建正式流程；说「验证」「验收」「测一下」→ 建验收流程。
正式流程的字段赋值必须走真实数据流（子表外键引用父表实际 ID、循环项字段、汇总回写），
不要拿验证流程里那种「全 const 造种子」的做法去应付正式业务——那是用户明确批评过的「各造各的 CRUD 堆」。

## 更新已有流程用 publish，不要 deploy

`deploy()` 是 create + publish，同名直接报 `UDC_MICROFLOW_0001 name already exists`。
重发、刷新引用、改一条已有流程，一律用
`deploy.publish(host, cookie, mid, app_id=..., schema=..., name=..., caption=...)`，传原 flow id。

★ **改了 `build_draft` 脚本（节点/字段/顺序）后必须重新 publish 该流程，构建才包含新逻辑**——只改脚本文件不 publish，`deploy-normal` 构建的仍是平台里旧版 schema（实测 MF-02 改采购明细加 poId 后没重新 publish，构建 jar 过了但采购明细 `po_id` 仍是 0，收货按外键查子表查不到）。改哪条流程就 publish 哪条（`deploy.publish` 传原 mid），再触发一次应用级构建。

## 参考文档索引（按需读，别全量加载）

| 文件 | 什么时候读 |
|---|---|
| `references/gates.md` | 改闸门 / 闸门误报 / G1 段数算法 / 引用载体 / 用真实流程校准 / **G34–G35 实体可写性及系统字段豁免** / **G36 DELETE 模式（CONDITION 右值不能引用节点）** / **G37 引用槽 outputName 不能为空** / **G38 逻辑节点 type 必须等于 actionType（写错=静默失效）** / **G39 条件右值必须是带 type 的槽（否则条件静默失效）** / **G40 CHANGE_LIST 四动作形态** / **G32 出参 type+dataType+javaType 三件套** / **往 gates.py 插规则的 ast 校验（插错函数 / `_walk_nodes` 传错参数 = 规则永不执行）** / **同一个闸门被复制进多个 gate 函数 → 同一违规重复上报（G33 曾报 3 次）** |
| `references/build.md` | 要证明「生成的 Java 能编译」、跑 delta 构建、读 backBuild.log、一致性检测、存量草稿体检、**★ 拉构建产物 zip 拿完整后端源码（生成代码/默认值表达式/AppService 方法）** |
| `references/node-shapes.md` | 写具体节点（FOR_EACH/END 出参/循环内改数据/查询条件/必填字段/24 类清单/硬契约） |
| `references/triggers.md` | MANUAL 出入参、endNode 契约、SCHEDULE、BUSINESS_EVENT |
| `references/expression.md` | 生成表达式（**含字段引用也走 transform，见 expression-engine §十五**） |
| `references/ui.md` | 用 CDP 操作设计器：document.hidden、抽屉三级兜底、节点真实创建、判据铁律、**可见性禁用 offsetParent**、多 target 同 URL 陷阱、关闭抽屉会卡死、**唯一有效的节点触发点是 node-body 的 onClick**、**node-title 是 caption / node-body 是实体名**、设计器规范化取证流程 |
| `references/delivery.md` | 交付物形态、需求→方案、构造器覆盖、宿主流程、跨应用复用 |
| `references/pitfalls.md` | 报错先查这里（坑 / 错误教训 / 生成节奏验证清单） |
| `references/checkschema-debugging.md` | checkSchema 拒绝定位：BOOT_3000/DATA_INVALID 分级、裸流对照+嫁接实验二分、模板基座键集污染、保存/回读 casing 差异、最小流平台实证样板 |
| `references/verification-chain.md` | `prove()` 四层自证链（发布/UI/参数名/检测）、CDP 端口选择、UI 三数字↔detectionType、测试流程不要发布 |
| `references/capability-matrix.md` | 能力盘点：四档状态判定、覆盖度脚本、当前矩阵基线、未关闭问题 |
| `references/node-contracts.md` | 节点契约表（G23）：节点×页签×必填 |
| `references/uncovered-nodes.md` | SUB_MICROFLOW / CALL_APP_SERVICE / FOR / DATA_MAPPING 的真实形态 |
| `references/replication-workflow.md` | 复刻对方应用业务：选料、对齐实体、本地补齐、三类触发覆盖、失败归因 |
| `references/group-and-batch-ops.md` | 建分组/清组/批量生成到新组、清理验收流程、部署锁 `UDC_DEPLOY_0002`、构建被一致性检测挡住时怎么归因 |
| `references/settings-capability-matrix.md` | 写任何节点配置项前先查这里：全节点配置项能力矩阵（唯一事实源，24 类 × 40 切换态 + 编译实证） |
| `references/create-variable-7x7-contract.md` | 创建变量 7 种 paramType 落库形态 + 实体型「赋值方式」三形态（attrs/value/mapping）键集与构造器入口 |
| `references/logic-graph.md` | 生成微流程的主路径：图格式、DSL 十形态、循环作用域、执行器与 G31/字段元数据的坑 |
| `references/requirement-to-graph.md` | 把业务需求变成逻辑图：LLM/Python 分工、真名解析、三档产出、验收测试集 |
| `references/expression-token-pitfalls.md` | 表达式四个 token 形态坑（均回 BOOT_3000）+ context 必须合并字段（P2 遗留）+ 引用核验要递归 |
| `references/delivery-pipeline.md` | P5 交付编排：11 态状态机、五道闸门、ExpressionFinalizer 接口与回读判真、构建验证（deploy-normal 的 deployDto 包裹 / 按 deployId 查 search-deploy-status）、断点恢复、工程节奏 |
| `references/node-break.md` / `node-publish-event.md` / `node-batch-entity.md` / `node-data-flow.md` / `node-sub-microflow.md` / `node-retrieve-array.md` / `node-list-operation.md` / `node-change-list.md` / `node-call-app-service.md` / `node-data-mapping.md` / `node-id-stability.md` / `sub-microflow-schema-compatibility.md` / `deleted-scheduled-flow-lifecycle.md` | 控制/写/服务/读节点的运行时契约（**LIST_OPERATION 14/14 种操作的附加键×出参表（含 GROUP_AND_SUM）、PICK_ONE 1 基索引、FILTER 过滤条件离线编译（OPERATOR 平铺 token / 两级 context）** 见 node-list-operation.md）：BREAK 的 type 陷阱与双循环对照法、事件投递的自建订阅者与载荷级证明、批量写无 attrs 与「列表元素不能带 id」、CALL_DATA_FLOW 的 `dataFlowMappingId`=行 id、SUB_MICROFLOW 的 `hasInput/hasOutput` 必须照抄子流程当前契约、RETRIEVE_ARRAY 的 fetchType×出参矩阵与条件右值陷阱、CHANGE_LIST 四动作形态、CALL_APP_SERVICE 调 starter 服务（归属/字段级 attrType/简单返回值）、DATA_MAPPING 的列表上游与 ARRAY 覆盖顺序、重发幂等（id 由别名派生）、子流程契约变更的构建期一致性检测、删流程后定时任务仍会跑 |
| `references/node-runtime-verification.md` | **把一个节点推到 RUNTIME_VERIFIED 的完整协议**：语料审计→自建隔离对象→调用链→属性刷新→结果断言表→定级→收尾；含四条硬规则与常见退化对照 |
| `references/runtime-log.md` | **运行验证 + 线上接口排障**：日志接口（前缀是应用名不是 udc）、AppLogRow 字段、`assert_ran` 判据、**「接口为什么返回 null」三步定位（flowLog 按 traceId 拉整条链、BOOT_3000=流程抛异常、data/query 反推分支、设计态查不到的三角判据）**、能证明与不能证明的边界 |
| `scripts/entity_write_capability.py` | 写节点选实体前必跑：从构建产物 zip 出实体可写性矩阵（有无 `create` / 哪些字段被默认值表达式无条件覆盖 / 可直接用于写验证的实体）。**带三档自检；扫错时以退出码 2 报出——看到非 0 不要用这张表** |
| `scripts/cleanup_verify_flows.py` | 每轮验证收尾必跑：按名字前缀删临时流程（**含 DRAFT**）→ 清测试数据 → 重建 → 轮询到终态。`--marks p5,p6 --where "task_id LIKE 'P6%'"`。删完仍需等一个调度周期复查行数不增长 |

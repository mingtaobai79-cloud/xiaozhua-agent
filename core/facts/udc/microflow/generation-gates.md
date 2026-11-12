# 微流程生成闸门：错误 → 规则 → 生成期拦截

> 目标：**生成即正确**。平台不是在 checkSchema 报错，而是在
> `CheckUtils.parseNodes → ActivityNode.nodeLogicCheck` 才报 04004/04000。
> 所以每条踩过的错都必须变成生成期可判定的规则（`components/udc/microflow/gates.py`），
> 规则不过就不生成、不提交，而不是生成完再拿脚本改。

## 闸门清单（`run_gates(schema, dep_apps=..., app_name=...)`）

| 闸门 | 拦截的错误（活体原文） | 判定规则 |
|---|---|---|
| G1 EXPR_SEGMENT_MISMATCH | `UDC_CE_MICRO_FLOW_04000 未知异常 java.util.ArrayList.rangeCheck`（`MicroFlowComponentUtils.checkExpressionNode:1716`） | `tokens` 数量必须等于 `expressionTranslation` 的段数（操作数/运算符/括号/逗号各一段） |
| G2 DANGLING_REF | `UDC_MICRO_FLOW_04004 前序节点发生变更请重新选择` | 每个 `SelectParam.outputName` 必须命中本流程某节点 `output.name` 或 `_FLOW_INPUT_*`；Expression 里 `VARIABLE` token 同理 |
| G3 TYPE_MISMATCH | `不是根实体对象(x)` / `不是文本类型(x)` / `对象类型不匹配(x)` | `CREATE_ENTITY`/`CREATE_BATCH_ENTITY` 只收 DTO；`CHANGE_LIST` 只收文本列表 |
| G4 MAPPING_RULE_NO_NAME | 提交门禁 `DATA_MAPPING.mappingRule 缺 'name'` | `mappingRule.name/caption` 必须显式写 |
| G5 CROSS_APP_NOT_DEPENDED | `依赖应用已删除` | 跨应用节点 `app.appName` 必须在 `udc_dependent_application`（本应用）清单里，或 `inApp=true` |
| G6 SERVICE_ATTR_STALE | `必填参数未配置，请点击该节点参数设置` | 服务节点 `attrs[].attrType.id` 必须以 `selectMethod.parameter.item.itemType` 为前缀 |
| G7 PAGESEARCH_NO_PAGEINFO | `必填参数未配置` | `pageSearch=true` 但 `pageInfo` 为空 |
| G8 ORDER_FORWARD_REF | `前序节点发生变更请重新选择` | 引用只能指向**前面**已出现的节点出参（引用名存在但排在后面也炸） |
| G9 MAP_OP_BASIC_TYPE | 类型不匹配 | `MAP_OPERATION.basic` 必须是选项对象，不是字符串 |
| G10 TEMPLATE_REF_LEAK | `04004 前序节点已变更` / 下拉空白 | 从模板复制节点时残留的兄弟节点引用（`dataSource.name`/`selectMap.name`/`selectParam.name`） |
| G11 END_NODE_SHAPE | 画布「节点开发中...」 | 顶层 `endNode` 必须 `nodeId=MFEndNode` / `type=END` / `actionType=END_NODE` |
| G12 CONDITION_NAME_ILLEGAL | 分支渲染异常 | `CONDITION.name` 只能 `ifBranch`/`elseIfBranch`/`elseBranch` |
| G13 EVENT_BINDING_MISSING | 事件节点红字 | `eventType=IN_APP` 必须带 `selectEvent`；`AMONG_APP` 必须带 `selectMq` + `app` |
| G14 CONNECTOR_DEP_MISSING | 「连接器依赖已移除」 | `CONNECTOR` 节点必须带 `app` |
| G15 RETRIEVE_COND_TOP_GROUP | 查询条件不生效 | `RETRIEVE`/`RETRIEVE_ARRAY` 组合条件顶层必须是 `GROUP`，写 `CONDITION` 会炸 |
| G16 TYPE_ACTION_MISMATCH | 平台拒收 | 节点 `type` 必须与 `actionType` 匹配（如 RETRIEVE 的 `type=ACTIVITY`） |
| G17 BASIC_REF_SHAPE | 畸形引用被拦 | BASIC 标量出参引用必须走 `_out_ref`（`id=""`/`dtoType=""`），否则生成 `<输出名>.<输出名>` |
| G18 FLOW_INPUT_PREFIX | 入参串味 | `MANUAL` 入参/出参 `name` 必须 `_FLOW_INPUT_`/`_FLOW_OUTPUT_` 前缀 |
| G19 WRITE_OUTPUT_SCALAR | `SingleResponse<Integer> 无法转换为 SingleResponse<Dto>` | 写操作出参是**影响行数标量**不是实体 DTO（CHANGE/DELETE/BATCH=INTEGER，CREATE_ENTITY=BIGINTEGER） |
| G20 WRITE_TARGET_NOT_CONTROL | `int 无法转换为 Dto` | 写操作对象必须引用**活动节点**出参，不能直引 FOR_EACH/控制节点 |
| G21 MANUAL_TRIGGER_DESC | 设计器「参数名称」空黄框 | `MANUAL` 入参必须带 `trigger.desc` 且与 `output.desc` 一致 |
| G22 NODE_CAPTION_EMPTY | 画布空白 | 每个节点必须有非空 `caption`，且 `isCompleted` 不为 False |
| G23 NODE_CONTRACT | 逐节点必填缺失 | 走 `node_contracts.py` 的逐节点契约校验 |
| G24 CHANGE_TARGET_NO_KEY | 「选择更新的数据」空白黄框 | `CHANGE_ENTITY.selectParam` 必须带 `key` |
| G25 CREATE_VAR_ATTR_20KEYS | 字段映射左侧红字「所选数据已失效」 | `CREATE_VARIABLE`(实体) 的 `attrType` 必须 20 键齐 |
| G26 SERVICE_METHOD_SIGNATURE | 参数页签取不到出入参 | 自定义服务必须带完整方法签名（md5/parameter/returnValue/fullName） |
| G27 CHANGE_VAR_ATTR_4KEYS | 同 G25 | `CHANGE_VARIABLE`(mappingType=attrs) 的 `attrType` 必须带引用四键 |
| G28 DATAMAPPING_ROW_EMPTY | 映射表空白 | `mappingRule.mappingRows` 每条必须有 `targetField`/`mappingMode`/`value` |
| G29 DATAMAPPING_SINGLE_OBJECT | 构建编译失败 `找不到符号 getName()` | `DATA_MAPPING` 上游不能是单对象主实体（生成器按 `List<Dto>` 处理） |
| G30 MAPPING_TYPE_REQUIRED | 赋值方式不选 → 构建必炸 | 实体型变量必须显式 `mappingType`；BASIC 引用 DTO 字段必带 `selectParam.path` |
| G31 REF_CHAIN_TYPE | 悬空 04004 / `List<Dto> 无法转换为 Dto` | 引用槽 `outputName` 必须来自前序节点出参/入参，`dataType` 与 `ARRAY`/`OBJECT` 一致 |
| G32 CONVERT_DATA_SHAPE | 类型转换错 | `CONVERT_DATA` 五子模式形态校验（`convertType`/源/目标三处一致 + regex 规则） |
| G33 CALL_DATA_FLOW_SHAPE | 生单规则错 | `dataFlow.id` 与 `dataFlowMappingId` 一致、`dataSourceType` 仅 `CONDITION`、`condition` 非空 |
| G34 ENTITY_NO_CREATE | 构建 40s FAIL `找不到符号: 方法 create(SingleRequest)` | `CREATE_ENTITY` 的实体在 facade api 无 `SingleResponse<Long> create(SingleRequest)` |
| G35 ENTITY_FIELD_OVERRIDDEN | 运行时 `UdcEntityCheckException`，传入值看不见效果 | 实体业务字段配了默认值表达式且 `requireNull=false`，create 时被无条件覆盖 |
| G36 DELETE_MODE_MISMATCH | publish 被拒 `BOOT_1001 Parameter Error`（**无字段级提示**，只能二分定位） | `DELETE_ENTITY` 用 CONDITION 模式却把条件右值填成节点引用（SelectParam）；或 SELECT_PARAM 模式混带 `app`/`structure`/`condition`/`methodLegal` |
| G37 REF_SLOT_EMPTY | publish 被拒 `check=false errors=[('[…节点]', '….selectParam.outputName', 'PROPERTY_IS_REQUIRED')]` | 引用槽 `outputName` 为空（典型：引用 `CHANGE_LIST`——它 output 恒为 null、原地改列表），或 `nodeInfo.nodeId` 悬空 |
| G38 LOGIC_NODE_TYPE_MISMATCH | **零报错**：构建 SUCCESS、publish 通过、运行 `success=true`，但节点不生效（BREAK 实测循环照跑 3/3） | `actionType=BREAK/CUSTOM_ERROR` 但 `type="ACTIVITY"`。解析器按 `MicroFlowNodeTypeEnum.valueOf(type)` 选解析器，代码生成模板按 `node.type` 分发（`<#case "Break">` → `break;`），Activity 分支里没有这两个 case → 节点被静默丢弃 |
| G39 CONDITION_RIGHT_VALUE_SHAPE | **零报错**：构建 SUCCESS、运行 `success=true`，但查询条件失效（RETRIEVE_ARRAY 返回整张表 23 条，三个 SIZE 全同一个数） | 条件 `rightParams` 缺 `type`（典型是把 DSL 的 `{"const": x}` 原样塞进去），平台解析成 `value=""`/`desc=""`。合法形态必须带 type（CONSTANT 还必须带 value） |
| G40 CHANGE_LIST_ACTION_SHAPE | **零报错**：构建 SUCCESS、运行成功，但动作语义不对（CLEAR 带上非法 dataSource，或 REMOVE 没有 countAttrs 时删不掉任何元素） | `action` 必须在 ADD/REPLACE/CLEAR/REMOVE 内（没有 DELETE）；CLEAR 不得有 dataSource；ADD/REPLACE 必须有；REMOVE 还必须有非空 countAttrs |
| G41 FIELD_REF_TYPE_MISMATCH | **假绿**：运行时类型自动转换、读库正确，但前端抽屉标红「所选'X'已变更」（BIGINTEGER 字段引用 DECIMAL 字段） | 字段级引用（SelectParam `position=children`）的 `dataType` 必须等于目标字段 `dataType`；标量出参（SIZE/SUM/MIN/MAX）走表达式（`_scalar_value_slot`），不是 children，不受此约束 |

## 实测有效性（2026-10-25，验收V1）

```
$ python scratch/run_gates.py
验收V1 闸门问题数: 4
 - G5 应用 'boot-starter-serialnumber' 未声明依赖 → 会报「依赖应用已删除」
 - G2 SelectParam.outputName 悬空 '_CREATE_VARIABLE_04QgeY' → 会报 04004
 - G2 SelectParam.outputName 悬空 '_RETRIEVE_PjOUCi' → 会报 04004
 - G2 SelectParam.outputName 悬空 '_FLOW_INPUT_c4ZeFK' → 会报 04004
```

这 4 条与平台 UI 检查报的 4 条阻断一一对应 —— 说明闸门口径与平台一致，
可以在**本地生成期**就拦住。

## 构造顺序（保证不出错的写法）

1. 先声明上下文：`input`（自定义对象/PageInfo）+ 变量节点，**收集所有 output.name**；
2. 再建引用型节点（查询/服务/变量赋值），一切 `SelectParam` 从已声明的 output 集合里取，不写字面量名字；
3. 表达式统一走构造函数：先切段，再逐段生成 token（VARIABLE/OPERATOR/SYSTEM/FUNCTION），段数即 token 数；
4. 跨应用服务：先把应用加进依赖（G5 过），再按 `parameter.item.itemType` 生成 attrs（G6 过）；
5. 收尾跑 `run_gates` → 0 问题才 `build_schema` → 提交。

## 反例（不要这样做）

- ❌ 从别的流程整节点搬 `CALL_APP_SERVICE`（`attrs` 里留着源流程的变量名）→ G2 必炸。
- ❌ 拼字符串表达式 `a+b` 只给 1 个 token（或给 3 个 token 但 translation 只有 1 段）→ G1 必炸。
- ❌ `CHANGE_LIST` 接实体列表、`CREATE_ENTITY` 接文本变量 → G3 必炸。
- ❌ 事后脚本改 schema 补字段 —— 应改构造器，让同类错误**生成不出来**。

---

# 写实体可写性：G34 / G35（2026-11-02 落地）

> 这两条拒的是「**选错实体**」，不是「构造器写错」。靠试跑永远定位不到根因：
> G34 在编译期炸，G35 在运行时**静默盖值**（看起来像构造器 bug）。

| 闸门 | 判据 | 真实后果 |
|---|---|---|
| G34 | `CREATE_ENTITY` 的实体在 facade api 无 `SingleResponse<Long> create(SingleRequest)` | 构建 40s FAIL：`找不到符号: 方法 create(SingleRequest<…Dto>)` |
| G35 | 实体业务字段配了默认值表达式且 `requireNull=false`（create 时无条件覆盖传入值） | 运行时 `UdcEntityCheckException`，传入值看不见效果 |

## 能力表怎么来

```bash
python scripts/entity_write_capability.py <metadata.zip> \
    --out core/facts/udc/microflow/entity-write-capability.json
```

`metadata.zip` 从构建日志 `backBuild.log` 第一屏的「构建元数据」地址取：

```
<HOST>/service/udc/file/download?storageKey=metadata/udc/<appId>/<buildVersion>.zip
```

**缺表时两条闸门必须静默跳过**（`_ENTITY_CAPS is None`）——不能因为缺证据就把全量流程拦掉。

## ★ 扫描口径必须做阳性对照

扫错的形态**不是报错**，而是「所有实体 `has_create=false`」或「所有实体表达式数 0」——
看起来完全合理，后果是 G34 拦掉全部流程（或一条不拦），而且没人会怀疑闸门。
**实测踩过两次，都是 glob 路径口径问题：**

```
glob('**\\facade\\**\\*AppService.java')   Windows 下多段 ** 匹配不到 → has_create 恒空
glob('**\\*AppService.java') 再判 '\\facade\\'   目录名其实是 <app>-facade，判不到 → 同样恒空
```

正确口径：先粗匹配 `**/*AppService.java`，再按**路径子串 `-facade`** 过滤
（模块目录叫 `<app>-facade`，不是 `facade`）；domain service 同理按 `/domain/service/`
子串过滤，且必须先归一化分隔符（`p.replace(os.sep, "/")`）。

**扫描脚本必须自带三档自检**，不通过以非零退出码报出来：

```
① 有 create 的实体数 > 0          ← 为 0 一定是口径错，不是真的一个都没有
② 已知有 create 的实体在集合里      ← 拿一个确定挂过写节点的实体做阳性样本
③ 已知被覆盖的字段出现在 fields 里  ← 否则 G35 永远不报
```

⚠ **能力表是构建产物快照，会过期**：实体新增字段 / 新增默认值表达式 / 新建实体后，
表里还是旧数据。触发重扫的时机：**新建或改过实体之后、给新应用写第一批写节点之前**。
表里 `source` 只写口径不写构建版本，无法从表自身判断新旧——靠人工记时机，
或比对实体数与当前应用实体数。

## ★ G35 必须豁免系统字段

`updater` / `creator` / `createTime` / `updateTime` / `creatorInstitution` /
`creatorDepartment` / `creatorPost` / `draft` / `id` 上的表达式是平台惯例
（修改人=当前用户），业务本来就不该给它们赋值。

不豁免的后果很实际：**有 `create` 且业务字段干净、恰恰最适合拿来做写验证的实体
（表达式只剩 `getUpdater`）会被自己的闸门拦掉**——实测这类实体占多数，
误报等于把可用候选清空。白名单位于 `gates._SYSTEM_EXPR_FIELDS`。

## 闸门自检四档（改这两条后必跑）

| 场景 | 期望 |
|---|---|
| 实体无 create | G34 拦 |
| 业务字段被覆盖 | G35 拦 |
| 只剩系统字段表达式 | 放行 |
| 两者都没有 | 放行 |

已固化为 `tests/test_gates_entity_write.py`（6 条，覆盖四档 + 能力表完整性）。

## ★ 改 gates.py 的插入纪律（插错函数 = 新规则永不执行）

往 `gates.py` 加规则时，靠文本定位插入点会**插进别的函数**：
`run_end_gate` / `run_order_gate` 里也有 `    return problems`，`rfind` 命中的往往不是 `run_gates`。
结果是编译过、import 过、AST 里能看到规则文本，但规则**根本不在被调用的那个函数里**——
注入缺陷回归全 MISS，看起来像「判据写错了」，实际是**代码没执行**。

> 本轮真实踩过：G34/G35 第一次就插进了 `run_leak_gate`。

- 定位：先 `grep -n '^def '` 列出**全部函数边界**，确认 `run_gates` 起止行号，再按行号区间放；
  只在脑海里有「G33 之后」这个概念就动文字锚点，必然插到隔壁函数。
  `gates.py` 里有 5~6 处一模一样的 `    return problems`，文本锚点天然不唯一。
- 精确定位：`ast.parse` 取目标函数节点的 `lineno/end_lineno`，插在它最后一个 `ast.Return` 之前。
- 复验：写盘后再 `ast.parse`，断言每个 G 编号出现在
  `ast.get_source_segment(全文件, 目标函数)` 里。

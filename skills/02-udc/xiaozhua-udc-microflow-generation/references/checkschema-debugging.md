# checkSchema 拒绝定位法（BOOT_3000 / DATA_INVALID 二分协议）

checkSchema 拒绝时**先分类，再二分**，不要逐键猜。

## 第一步：错误分级

| 返回 | 含义 | 定位方式 |
|---|---|---|
| `check=false` + `errorMessage[{nodeCaption,path,errorCode}]` | 节点级，有明细 | 直接按 path 定位到节点字段；注意 path 段名是 **UI 区块名不是存储键**（如 `创建变量.mapping.value.type` 里的 `mapping` 指「赋值方式」区块，不代表 mappingType=mapping） |
| `code=BOOT_3000`，`data=null` 无明细 | 服务级拒绝：引用悬空 / 条件右值为 null / 键触发服务端分支错判 | 走下面的二分协议 |
| body 写错返回 `null` | 不是失败也不是成功 | 修 body（15 字段平铺，见 SKILL.md 检查链路） |

已知 BOOT_3000 触发源：RETRIEVE 条件查询 `rightParams:[null]`（构造器调了却没传 right_value）；引用了不存在的 outputName；**表达式 context 字段不全**（见下节）。先查这三处再二分。

### ★ BOOT_3000 的隐形源：token/translation 全对，错在 context

表达式类的 BOOT_3000 最容易误判——`tokens` 的运算符、`expressionTranslation` 的文本、
字段元数据看起来**逐字正确**，但平台仍拒。真因往往是 **context 里少了表达式引用的某个字段**：

```
表达式 X.name == 'x' && X.driverClassName == 'y'
context[0].properties[0].properties == ['name']        ← driverClassName 不在里面
```

机制：同一节点被引用两次（`X.name`、`X.driverClassName`）就是两次 `register_node_output`，
早期实现见名即 return，只保留第一个字段。平台按 context 解析 token，解析不到就整体拒，**不给明细**。

定位动作（不用猜，直接读）：

```python
back = DP.get(host, ck, mid); sc = json.loads(back["dataSchema"])
# 取该表达式的 designData，把 context 里声明的字段列表
# 与 tokens 里出现的字段名做集合差 —— 差集非空就是它
```

## 单维度变体矩阵：无 message 报错时比二分更快

二分是「把流程砍半」，适用于**节点/结构**层。当问题落在**同一个节点的内容**上
（表达式形态、配置组合），改用变体矩阵：造 5 个只差**一个维度**的最小用例，
一次跑完，谁红谁就是病灶维度。

实测形态（表达式 AND 组合）：

```
A 单个函数                      PASS
B AND + 两个比较                FAIL   ← 仅此维度就红
C AND + 比较 + 函数             FAIL
D 单个比较                      PASS
E AND + 两个函数                PASS
```

结论直接指向「比较运算参与 AND」而不是「函数不能进 AND」——比反复猜 token 形态快一个量级。
判据：**变体之间必须只差一个维度**，否则红了也归因不了。

## 第二步：三段二分（用最小流实验，别改构造器盲试）

1. **裸流对照**：trigger + RETRIEVE + END 的最小流（不带目标节点）走 checkSchema。
   裸流也 3000 → 问题在 RETRIEVE/组装层；裸流绿 → 问题在目标节点。
2. **嫁接实验（最强定位）**：从 `scratch/pmp_schemas.json` 挖一个**同形态的真实节点**，
   原样 JSON 嫁接进你的最小流（引用对齐：改 RETRIEVE 的 nodeId/output.name 匹配它），checkSchema。
   - 语料节点绿 + 你的节点红 → 差异在你节点内部，做**递归键集 diff**（排除 appId/实体值类本该不同的项，专查键集差：仅我有/仅语料有）。
   - 语料节点也红 → 环境/流级差异。
3. **手动 body 对照**：`deploy()` 链失败时，用 `DP.create` + 手写 checkSchema/update body（与 deploy.publish 相同 15 字段）复跑，排除链路差异。

## 第三步：键集类根因的高发点

- **模板基座污染**：`fixtures/microflow/node_templates/*.json` 若带了某形态不该有的键（如 CREATE_VARIABLE 基座带 `otherType:SYSTEM_PAGE_INFO`），校验器**按键存在性走 OTHER 分支**，导致 value/mapping 形态全被 `mapping.value.type DATA_INVALID` 误杀——错误 path 与真实病灶差一层。新增构造器前先核对模板基座键集 == 语料该形态键集。
- **`attrs: None` 也算有键**：校验器分支只看键存在，不看值。语料形态「无 attrs 键」连 None 都不能设，用 `node.pop("attrs", None)`。
- **字段级引用 vs 对象级引用**：`selectParam.position=children`（字段级）时 `dataType` 是**字段**类型，不与出参 DTO 声明比对（G31 已按此精化）；对象级（parent）才比对。

## casing 差异：保存态 vs 回读态

- 发布/保存的 dataSchema：dataType 恒大写（STRING/BIGINTEGER，643 条发布语料）。
- 后端回读接口（FindByIdGet / 后端证据文件）：首字母大写（`String`/`Object`）。
- 平台自身做转换。校验器比对一律 `.upper()` 归一；**拿回读态当保存态契约写死旧约束是误归纳**，改校验器前先确认证据来自哪一态。

## UI 层实证的边界

- 后台 tab 受浏览器节流，画布不渲染（`.node-body=0`）——不是流程问题，别据此判红。
- 「检查」按钮仍可 CDP 真点，`run_check` 返回 `errors=[]` + 应用一致性检测明细（按流程名/id 过滤）即为「检查真跑」的有效证据；画布红字目检需前台窗口时段。

## 平台实证闭环样板（最小流：RETRIEVE → 目标节点 → END）

`DP.create` → 手写 body 调 `/service/udc/microflow/checkSchema/update` → 回读 `state==RELEASE` → `DP.delete` 验后即删。
guid 从回读拿；`dataSchema` 传 JSON 字符串。实证结论落回 `node-settings-capability.json` 的 `compile_or_ui_facts`，探针带真实字面量的收容 `_attic_pending/`。
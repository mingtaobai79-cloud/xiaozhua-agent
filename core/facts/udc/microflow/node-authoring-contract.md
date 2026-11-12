# 微流程节点正确生成契约（前端驱动，而不是拼 JSON）

> 触发：40 条批量生成的节点在 UI 里大面积异常（"所选'数据'已变更"、"请选择"、面板空白、
> "节点开发中…"）。根因不是某个字段写错，而是**生成路径错了**。

## 一、平台真实的节点生成链路（前端证据）

在微流程编辑器里手动加一个节点，控制台依次打印：

```
添加节点 => addNode {type: 'udc-microflow-edit/addNode', payload: {…}}
回填 nodeConfig {description: '', foreach: {…}, isCompleted: false}
attributes[key] {validate: true,
                 id: 'com.seeyon.datamigration9000000000000000001.dto.YsFull6956Dto.createTime',
                 name: 'createTime', fullName: '…createTime', md5: '3289788337887610457', …}
## 右值组件表达式参数: {config: {…}, ExpressionComponent: ƒ}
```

三件事只有前端做得到、后端 POST 做不到：

1. **addNode 后回填 nodeConfig**：`description`、`foreach`、`isCompleted` 等默认值由前端
   按节点类型补，不是后端补的。
2. **attributes 带 md5 逐个下发**：实体每个字段都带 `md5`（如 `f01text → 3289788337887872601`）。
   节点里的属性引用要和这个 md5 对齐；我手写的 attrType 没有 md5 → UI 判"所选'数据'已变更"。
3. **右值组件（ExpressionComponent）**：表达式右值由前端组件挂载时生成 config，
   我手拼的 `Expression.schema` 只是它的持久化形态。

## 二、结论（这就是之前所有怪象的统一解释）

| UI 现象 | 真实原因 |
|---|---|
| 所选'数据'已变更 | 属性引用缺 md5 / md5 与当前实体不一致 |
| 请选择（选择应用/实体为空） | 节点级 `app`/`structure` 没走前端回填 |
| 分支面板空白 | BRANCH 的 nodeConfig 未按前端模板生成 |
| 节点开发中… | 服务节点 selectMethod 不完整，前端无法渲染 |
| 修改变量不赋值 / 计数循环写死 | 生成器只填了结构，没填业务值 |

**一句话：整包 POST dataSchema 绕过了前端的"逐节点添加 + 确认"校验与回填，所以生成出来一定缺东西。**

## 三、正确的生成路径（改造后的生成器）

1. **模板来源**：每类节点在 UI 里添加一次 → 点「确认」（触发前端校验 + 回填）→ 抓
   `addNode` 之后 store 里的 nodeConfig 快照 → 存 `fixtures/microflow/node_templates/<ACTION>.json`。
2. **生成器只做参数替换**：换应用/实体/字段/引用/表达式，绝不重写结构；
   属性引用一律取模板里的 `attrType`（含 md5），只替换 `value`。
3. **表达式**：保留模板里 `runtimeData.executableExpr` 的前缀与 `uniformityParams`，
   只替换 tokens/translation，且段数与 token 数一致（G1）。
4. **引用**：只能指向本流程中**位于其前面**的节点出参（G8 顺序闸门）。
5. **校验顺序**：模板结构完整 → 替换 → run_gates + run_order_gate → 提交 → UI 逐节点复验。

## 四、必备证据（还差的部分）

- [ ] 每类节点的 nodeConfig 模板（含 md5 属性表）：CREATE_VARIABLE / RETRIEVE / RETRIEVE_ARRAY /
      CREATE_ENTITY / CHANGE_ENTITY / CHANGE_VARIABLE / CHANGE_LIST / LIST_OPERATION /
      MAP_OPERATION / FOR / BRANCH / CONDITION / BREAK / CUSTOM_ERROR / DATA_MAPPING /
      CONVERT_DATA / SUB_MICROFLOW / CALL_APP_SERVICE / DELETE_ENTITY
- [ ] 实体属性全覆盖表（`attributes[key]` 全量，带 md5）：`fixtures/microflow/entity_attrs.json`
- [ ] 右值（值编辑器）类型清单与各自的持久化形态

## 五、反面记录（不要再犯）

- ❌ 用 `Builder` 手拼十几个字段就当成节点 —— UI 缺 md5、缺模板默认值。
- ❌ 40 条同构配方复制，只为凑数量 —— 用户判定为"空壳"，直接打回。
- ❌ 生成后拿脚本改 schema —— 掩盖根因，下一批还会错。

## 五.5 前端深度校验「保存并提交」的必填字段清单（2026-10-28 实测）

后端 `checkSchema`（草稿态）是**浅校验**，过了不代表能用。前端「保存并提交」才是深度校验，
`console.log("firstErrorNode", node)` 报第一个缺字段的节点，**静默无请求**（不发 UpdatePost）。

实测手写构造器缺的字段（对照 node_templates 补齐）：

| 节点 | 必补字段 | 说明 |
|---|---|---|
| CREATE_ENTITY | `title` + `methodLegal` + `value:null` | methodLegal 从 entity_structure 取 |
| CHANGE_ENTITY | `title` | = 实体 label |
| CREATE_MAP | `paramType:null` + `dataType:null` + `title` + 顶层 `generics` | output.generics 也要 |
| MAP_OPERATION(GET) | `basic` + `arrayOrObject` + `title` + `nullPromptMessage` + `dataType` | GET 操作专属，PUT 不需要 |
| CONVERT_DATA | `regex`（Split 类型）+ `title` | output.type/dataType 大写 |
| CUSTOM_ERROR | `type:"CUSTOM_ERROR"` | 不是 "ACTIVITY"（铁律 3） |

★ `MAP_OPERATION.operationType` 是**字符串**（`GET`/`PUT`/`REMOVE`/`KEYS`），不是对象
  `{"type":"GET","key":...}`。这是手写最易错点。

★ 抓取方法：点「保存并提交」前注入 `console` 钩子，抓 `firstErrorNode` 后面的 node JSON，
  看 `值为空的必填属性=> <字段名>` 逐条列出缺的字段。

根因仍是 §二那句：**整包 POST dataSchema 绕过前端 addNode 回填**。正确路径是
node_templates 完整结构 + 只替换参数，不是手写构造器（手写必缺字段）。

## 五.6 逐节点 UI 添加的正确姿势（2026-10-28 LIVE 实测，12 类节点走通）

真正「一个一个节点处理」的路径 = 在 UI 里逐节点「加号 → 选类型 → 填必填 → 确定(onFinish)」，
前端回填完整字段 + 自动保存（udcMicroflowUpdatePost）。四条关键操作，每条都是踩出来的：

| # | 操作 | 正确做法 | 错误做法（会静默失败） |
|---|---|---|---|
| 1 | 打开节点面板 | 点 `.add-node-btn button` **中心** | 点 `.anticon.add-button`（span 图标）——点中图标不触发 button onClick |
| 2 | 选实体/列表 | 树形下拉 `.ant-select-tree-treenode` 找节点点它 | `.ant-select-item-option`——实体/列表是 ant-select-tree 不是普通 select |
| 3 | 填 input/textarea | React 受控组件：`HTMLInputElement.prototype` 的 value setter + dispatch `input`/`change` 事件 | `Input.insertText`（时序不对，值不落）/ 直接设 `.value`（React 不认） |
| 4 | 提交节点抽屉 | `ui.submit(d, strategy='onfinish')`（直调 Form.onFinish） | `b.click()` 点确定——撞 rc-field-form outOfDate 时序断言，抽屉关但零写入 |
| 5 | 切受控字段（radio/tabs/select）缺值 | `ui.set_form_field(d, field, value)`（form.setFieldsValue）+ onfinish | CDP 点 radio/tabs 的 input/wrapper/圆点——**都不触发**（onChange 在 rc-field-form 层，input 隐藏 opacity:0） |

实测：`pageSearch`（分页查询 radio）、`mappingType`（赋值方式 tabs）前端回填是 null/错误值，
CDP 怎么点都不切。正确 = `set_form_field(d,'pageSearch','false')` / `set_form_field(d,'mappingType','attrs')`
再 onfinish，回填立即正确。权威默认值查 `node_templates/<NODE>.json`（如 RETRIEVE_ARRAY.pageSearch="false"、
CREATE_ENTITY.mappingType="attrs"）。

配套工具：`scratch/node_add_fill_submit.py`（add → fill → onfinish → snapshot 通用框架，
每节点类型一个 `fill_xxx(d)` 函数）。产出证据 `scratch/ui-node-by-node/node-<名>.json`。

★ 残留抽屉坑：open_add_panel 点 span 失败会留一个 `.ant-drawer`（`ant-drawer-in` 但无
`ant-drawer-open`）空壳覆盖画布，拦截后续加号点击。判定：`elementFromPoint` 命中
`ant-drawer-body` 而 `drawers==0`。解法：`location.reload()` 重载（节点已 onfinish 保存，安全）。

## 七、确认的业务线（正确生成流程，用户拍板）

```
1. 节点组装：UI 里逐节点「添加」→ 每个节点弹各自的配置弹窗
2. 弹窗校验：每个节点类型有**不同的弹窗 + 各自的校验规则**，必须逐个拉出来（字段、必填、类型）
3. 推进确定：每弹窗填完点「确定」，触发该节点的前端校验 + nodeConfig 回填
4. 保存并提交：全部节点确定后，最后点「保存并提交」→ 走 checkSchema/update

不是：拼一整段 dataSchema 一次性 POST（那会绕过每个弹窗的校验与回填，必然缺字段/错引用）。
```

这意味着：生成器的**每个节点模板必须带「弹窗校验清单」**（哪些字段必填、值约束、引用约束），
生成时逐节点过校验，缺一项就不许过。模板来源 = UI 逐节点抓弹窗（字段 + required 标记 + 校验触发条件）。

## 八、核心机制：节点确定后元数据重载（用户强调，最重要）

每个节点的字段选项/赋值来源，**由前序节点的出参实体决定**：

1. 选定一个「来源数据/变量」后（如 选择更新的数据=vKey[小爪实验实体950795V2]），
   前端**按这个实体的元数据重载**字段列表（attributes 带 md5）。
2. 点「确定」一个节点后，它的元数据重载完成，**下游节点可选的字段随之更新**。
3. 所以「修改变量/更新数据/插入数据」等的字段下拉、多选、值编辑器选项，
   都不是固定的，而是**跟着前序出参的实体类型走**。

对生成器的约束：
- 节点必须**按顺序生成**（前序先落定），不能整包并行写；
- 每个节点的字段赋值，必须从「它引用的那个实体」的 metadata 取字段（含 md5），
  不能拿别的实体字段硬填（否则「所选数据已变更」）。

## 九、事件对象 vs 自定义对象（用户强调要区分）

- 事件投递/监听事件 里用到的「事件对象」本质是自定义对象，但和「设置」里的自定义对象
  是**不同类型**，需区分：
  - 自定义对象：普通 DTO（入参/出参/分页对象 等）
  - 事件对象：分「应用间事件对象(异步)」/「应用内事件对象(同步)」，用于事件投递与监听
- 事件投递 → 发布事件；后面「监听事件」节点能监听到同一事件（同一事件对象）。

## 十、链路机制：每个节点选择都触发接口加载数据（用户强调，生成器必须懂）

- 勾选/选中一个节点后，前端会调接口加载「这个节点需要的数据」（下拉列表、依赖的实体字段、
  子微流程的入参/出参、前序节点的出参等）。
- 不止前端校验，**后端也会加载数据**——这就是「链路」：节点配置不是静态的一套字段，
  而是「选了什么 → 触发什么接口 → 加载什么依赖数据」。
- 例子：
  - 子微流程节点：选中微流程服务 → `udcMicroflowServiceListSubMfPost` 列子微流程 →
    再加载该子微流程自己的 入参(参数配置) 和 出参(出参描述)。
  - 更新/插入数据节点：选实体 → 加载该实体 attributes(含 md5)。
  - 查询节点：选实体 → 加载字段(筛选/排序/聚合)。
- 对生成器约束：每个节点必须**按链路顺序**生成，选中某对象后要先「加载」它的依赖数据
  （走接口拿真实字段/入参/出参），再填下游字段；不能只凭一套静态字段模板硬填，否则少很多东西。

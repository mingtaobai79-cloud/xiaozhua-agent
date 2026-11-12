# 微流程节点验收 SOP（用户严令，逐字执行）

## 每个节点的固定七步节奏

```
1. 添加节点 → 抓默认状态（addNode payload + 回填 nodeConfig + 默认表单快照）
2. 逐项选择 → 每个 radio 每个值、每个 select 每个选项，全部切换一遍并抓子表单
3. 点确认 → 走前端校验，记录抛出的 unhandledrejection（values / errorFields / outOfDate）
4. 看必填 → 从校验结果和 DOM 的 .required-item / has-error 判定真实必填项
5. 处理必填 → 逐项填，每填一项再确认一次校验变化
6. 处理业务填写 → 按业务语义填，不是填占位垃圾
7. 再确认 → 通过后抓 store 节点 + 后端 dataSchema + 全链路接口
```

少一步都不算完成。

## 每种可能性都要试（不能只试默认值）

### 查询单条数据（RETRIEVE）
- 未查到数据时：`TERMINATION`（终止+提示）**和** `CONTINUE`（自行判空）两个都必须走通
- 提示内容：终止时必须填；继续时该字段应隐藏
- 过滤条件：
  - 单条件
  - **增加条件组**（GROUP 嵌套 GROUP，AND/OR 组合）
  - 右值三种形态：常量 CONSTANT、上下文变量 CONTEXT_VARIABLE、**表达式**（拼接口径）
- 排序规则：无 → 加一条 → 加多条，每个排序方向都试
- 查询方式：`CONDITION` 与 `IDS` 两种都要走
- 查询聚合对象：关闭/开启

### 查询多条数据（RETRIEVE_ARRAY）
- 查询方式四种全走：`CONDITION` / `IDS` / **`COUNT`** / **`OTHERS`**
- 分页查询：关闭 → 开启（开时"分页数据"变必填）
- 筛选条件、排序规则：同单条，含**条件组**和**表达式右值**

### 修改变量（CHANGE_VARIABLE）
- 必须用**表达式**，而且要覆盖多种修正方式：
  - 纯常量赋值（Simple）
  - 引用前序节点出参（SelectParam）
  - 表达式：`字段A + 字段B`（数值相加）
  - 表达式：`textToDecimal(文本字段) + 5`（类型转换后运算）
  - 表达式：`substring(文本,0,3) + '拼接串'`（截取+拼接）
  - 表达式：布尔运算/条件判断
- 每条表达式都必须走 `/service/udc/expression/transform` 生成，禁止手写 executableExpr

### 映射操作（MAP_OPERATION）
- 未获取到数据时：`OBJECT` / `ARRAY` / `TERMINATION` / `CONTINUE` 四种全走
- 操作类型：GET / PUT / REMOVE 等全走

### 插入/更新数据（CREATE_ENTITY / CHANGE_ENTITY）
- 赋值方式 `attrs`（字段映射）和 `value`（对象引用）两种全走
- 字段赋值：常量、引用、表达式三种右值都试

### 删除数据（DELETE_ENTITY）
- 删除规则三种全走：`SELECT_PARAM` / `CONDITION` / `IDS`

### 事件投递（PUBLISH_BUSINESS_EVENT）
- 事件类型：`IN_APP`（应用内）和 `AMONG_APP`（应用间）两种全走
- 字段映射：每个事件字段都要填一遍

### 数据转换（DATA_MAPPING）
- 目标类型：`ENTITY` 和 `DTO` 两种全走

### 创建变量 / 创建列表
- 所有 paramType 全走（创建变量 7 种、创建列表 5 种）
- BASIC 下所有 dataType 全走（7 种）
- 默认值：常量 + 表达式两种

### 计数循环（FOR）
- 起点/终点/步长：常量、引用、表达式三种形态都试
- 执行条件：`小于等于` / 其他操作符全试

### 分支（BRANCH）
- ifBranch 表达式、elseBranch
- 增加 elseIf 条件分支
- 每个分支里放子节点

## 链条接口必须捕捉

每步记录：
- 请求 URL（含 graphql operation 名）
- 请求 body（前 8000 字符）
- HTTP 状态
- 凡是写操作，回读确认

已确认的确认节点调用链：
```
udcMicroflowUpdatePost → udcMicroflowFindByIdGet → udcMicroflowSearch
→ udcMicroflowDisableNodePost + udcMicroflowFindCustomDtoPost → udcMicroFlowGroupSelectByTypePost
```

## 最后一步：保存提交 ≠ 通过

**后端 checkSchema 返回 `{check:true, errors:0}` 别高兴——可能是假通过。**

必须再做一致性检查：
1. `udcApplicationDoDetectionPost` 应用级检测，ERROR 必须 0
2. 回读 `dataSchema`，逐节点比对前端 store 里的节点与后端保存的节点是否一致
3. 检查节点 `output.name` 是否真的可被后续节点引用
4. 检查表达式 `executableExpr` 是否由服务端生成（不是手写）
5. 交付前在页面点一次「检查」，前端校验才最接近真实

## 记录规范

每个节点一份：
```
scratch/node_tests/<节点名>.json
{
  "default": {...},          # 默认状态快照
  "radios": {...},           # 每个 radio 值切换后的表单
  "selects": {...},          # 每个 select 的选项 + 每选项选中后的子表单
  "validations": [...],      # 每次点确认的校验结果
  "requiredFilled": {...},   # 必填处理后
  "businessFilled": {...},   # 业务填写后
  "finalNode": {...},        # store 里的最终节点
  "backendNode": {...},      # 后端 dataSchema 回读
  "net": [...],              # 全链路接口
  "pitfalls": [...]          # 本节点踩到的坑
}
```

## CDP 操作已知坑（累计）

| 坑 | 现象 | 解法 |
|---|---|---|
| 页面后台 | `document.hidden=true` 时 CSS 动画卡死，下拉 `opacity:0` 坐标 -9999 | `Page.bringToFront` |
| 点确定 | antd `validateFields` 报 `outOfDate:true` 竞态 | 在输入框内按 **Enter** |
| 点画布 + | JS `.click()` 无效 | CDP `Input.dispatchMouseEvent`（带 buttons） |
| 抽屉节点名 | — | `span.add-node-title` 的 `.click()` 有效 |
| 表单赋值 | 直接改 `.value` React 不认 | 原生 setter + 派发 `input`/`change`；或取 antd form 实例 `setFieldsValue` |
| 删节点 | 删除按钮被 `.node-top-line` 遮挡 | `Page.reload` 复位 |
| 下拉选项 | 需在同一个进程调用内完成"打开-读取-点击" | 否则跨进程失焦自动关闭 |
| 搜索框残留 | 之前输入过的搜索词让下拉显示"暂无数据" | 先清空搜索框 |
| awaitPromise | 后台标签页 `setTimeout` 被节流，Promise 不 resolve | 避免在 JS 里 await，改 Python 侧轮询 |

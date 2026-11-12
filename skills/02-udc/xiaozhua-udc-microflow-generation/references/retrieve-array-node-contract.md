# RETRIEVE_ARRAY（查询多条数据）节点契约

权威全文：`xiaozhua-agent/docs/audit/udc-semantics/MICROFLOW-RETRIEVE-ARRAY-CONTRACT.md`。
本文件只记最常用的判据，避免两处内容漂移。

## 与 RETRIEVE 的关键差异

- 出参名字段 **`variableTitle`**（单条是 `title`）；`scope="ARRAY"`、`output.type="ARRAY"`。
- 查询方式 4 种：`CONDITION` / `IDS` / `COUNT` / `OTHERS`（单条只有 CONDITION/IDS）。
- 默认必填：`structure` + `pageInfo` + `variableTitle`。
- **切换查询方式会清空 `structure`**，必须重选实体再提交。

## 字段联动

- COUNT：排序/分页/最多条数全消失，只剩筛选条件；output=`OBJECT`+`INTEGER`。
- OTHERS：多两个必填 `aggFunction`（聚合方法）、`countAttrs`（计算字段）。
- IDS：多 `value`（选择该记录的ID集合），**筛选条件也消失**。
- CONDITION 分页=是 → `pageInfo`（分页数据）；分页=否 → `size`（最多获取条数），
  后端 `pageSearch` 为**字符串** `"true"/"false"`。
- **前端逐节点搭时 `pageSearch` 默认是 `"true"`（「分页查询」radio 默认「是」）**，导致 `pageInfo` 变必填 →
  保存被 `值为空的必填属性=> pageInfo null` 阻塞。权威默认值 `node_templates/RETRIEVE_ARRAY.json` 是 `"false"`。
  修法：CDP 点「否」radio 切不动（onChange 在 rc-field-form 层、input opacity:0），改用
  `form.setFieldsValue({pageSearch:'false'})` + onfinish 提交，回读 `pageSearch="false"` 即解。

## OTHERS 聚合（4 种全实测）

- 方法：SUM / AVG / MAX / MIN。
- 计算字段联动：SUM/AVG 仅数值；MAX/MIN 数值+日期时间；未选方法时全类型。
- output：SUM/MAX/MIN 随字段类型；**AVG 恒 DECIMAL（java.math.BigDecimal）**。

## 依赖前序参数（下拉为空≠功能不存在）

- IDS 的 `value` 需长整数列表/数组参数；分页 `pageInfo` 需系统分页对象
  （CREATE_VARIABLE `paramType=OTHER` / `otherType=SYSTEM_PAGE_INFO`）。
  当前流程没有这些参数时下拉为空，须先补前置变量，不能记成「平台不支持」。

## 前置参数与排序/筛选（已回读闭环）

- `pageSearch="true"` 时 `pageInfo=SelectParam`，指向 `SYSTEM_PAGE_INFO` 变量
  （`com.seeyon.boot.transport.PageInfo` / OBJECT）；`size=null`。
- IDS 的 `value=SelectParam`，指向 CREATE_LIST 的 `BIGINTEGER/ARRAY` 出参；
  `pageSearch/pageInfo/size=null`。
- 排序后端 `sortParams=[{sortType:ASC/DESC,attrType:{...含md5}}]`；
  筛选后端 `condition GROUP/CONDITION`，右值 CONSTANT 的 value 保留数字类型。
- **确定自动保存的条件**：前端源码证实 `onSubmit` 更新 store 后，只有 `configChanged=true`
  才发 `saveMicroflowSchema(DRAFT)`。只改自定义控件可能不置位；真实修改出参名再点确定，
  接口出现 `FindCustomDtoPost → UpdatePost → FindByIdGet`，后端回读确认才算闭环。
- 应用一致性检查实测 `ERROR=0 / WARN=5`（均为警告）。

## 运行时契约（RUNTIME_VERIFIED，含下游消费）

217 条真实样本的 fetchType × 出参：

| fetchType | output.type | output.dataType | 样本 |
|---|---|---|---|
| CONDITION | ARRAY | DTO | 184 |
| IDS | ARRAY | DTO | 19 |
| COUNT | OBJECT | INTEGER | 13 |
| OTHERS | OBJECT | DECIMAL | 1 |

**取记录恒为 ARRAY，单条记录也不降级**；OBJECT 只出现在 COUNT/OTHERS 聚合。
所以「单条会不会变成 OBJECT」不用实测——形态由 fetchType 决定，与行数无关。

**条件右值必须是 `{"type":"CONSTANT","value":"<str>","desc":"<str>"}`。**
把 DSL 的 `{"const": x}` 原样塞进 `rightParams`，平台解析出 `value=""`/`desc=""`，
条件静默失效：返回整张表、构建 SUCCESS、运行 `success=true`，只有读侧不对。闸门 **G39** 拦。
逻辑图 DSL 的键是 **`right`**，写成 `right_value` 会被忽略，退化成空常量。

**隔离种子必须用应用租户**：平台查询带租户过滤，SQL 直插的行若 `tenant_id=0`，
平台一条都查不到（SIZE 全 0），很容易误判成「条件还是失效」。先抄一行平台写入的 tenant_id。

### 下游怎么消费 ARRAY

`LIST_OPERATION` 的出参随 `operationType` 走，不能一律 INTEGER：

| op | output |
|---|---|
| `SIZE` / `SUM` / `MIN` / `MAX` | OBJECT 标量（INTEGER / DECIMAL） |
| `FIRST_ONE` / `LAST_ONE` / `PICK_ONE` | OBJECT + 元素 DTO（id 取被操作数组的 DTO 全名） |
| `FILTER` / `SORT` / `DISTINCT` / `MAP` / `SUBTRACT` / `INTERSECT` | ARRAY |

元素节点（FIRST_ONE 等）**没有 `structure`**，字段引用要靠 `output.id`（DTO 全名）反查实体模型——
解析器只认 `structure` 时会报「缺 structure，无法解析字段」。

★ 写节点的 `attrs` **不接受字段级 SelectParam**（真实样本里 attrs 的 SelectParam 全是对象级，
无 `field`）。要比较元素字段值，用**表达式分支**（`{"op":"EQ","left":{"field":"f.sourceTable"},...}`），
不要往 attrs 里塞字段引用——那样会编译失败（`找不到符号: 类 _LIST_OPERATION_xxx`）。

### 读侧验收判据（可直接照用）

```
多条件种子：M 组 3 条 / O 组 1 条 / X 组 0 条
ra_multi → SIZE → 期望 3
ra_one   → SIZE → 期望 1      （同时证明单条仍是 ARRAY：SIZE/FIRST_ONE 都能作用）
ra_none  → SIZE → 期望 0      （空列表不是 null）
f_one    → FIRST_ONE → 分支比对 sourceTable == "S-ONE" → 写 ELEM-OK
```

六项断言：节点执行 / 出参为 ARRAY / 元素结构 / 元素数量 / 条件筛选 / 下游消费。
未验：IDS、COUNT、OTHERS、分页、排序、多条件 GROUP。

## 提交与回读坑

- **点「确定」可能零写入**（store 不变、无 UpdatePost、无 errorFields），
  删除残留行动态行后当场重填可恢复 store 写入；落库仍须回读确认。
- 抽屉空壳判据：`items` 非空，不是标题。用 `ui.ensure_node_drawer`。
- 本节点 `forms=2`，`submit(strategy="onfinish")` 拿到的可能是内层 form 的 onSubmit，
  返回 ok 也不代表已保存。
- 本机 urllib 回读可能 403（cookie 不全），页面内 fetch 更可靠；
  回读失败 ≠ 未保存，须分开判定。

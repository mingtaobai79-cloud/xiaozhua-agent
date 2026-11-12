# 扩展实体（扩展方案/Scalability）机制 — 实测 + 反编译双证

> 状态：LIVE PASS + BYTECODE。2026-10-23 实体域取证。
> 环境：测试网关 `<gateway-host>`，`appId=<app_id>`，udc-web/runtime 5.3.517。

## 1. 语义（与 UI 文案对照）

UI「高级设置 → 扩展实体」= 给实体挂一个**扩展字段方案**（ScalabilityOption）。
运行时动态扩展数据的落地形态：**平台自动生成一个影子实体** `<name>Ext`（caption `+扩展`），
扩展字段长在影子实体上，主实体通过 parentId 关联。用户口径「运行态动态扩展数据」的权威实现。

## 2. 关键字段（EntityBaseDto，反编译 cfr-r31）

| 字段 | 含义 | 备注 |
|---|---|---|
| `customScalabilityId` | 自定义扩展方案 id | Long，默认 "0"=未挂 |
| `customScalabilityGlobal` | 是否启用全局扩展 | 走应用的 `scalabilityOptionId` |
| `scalabilityOptionId` | 自定义扩展**字段**方案 id | EntityBaseDto 上另一槽位 |
| `linkageExtFiled` | 是否联动扩展字段 | Boolean |

方案数据结构（`ScalabilityOptionDto`）：`{id, appId, name, caption, scalabilityDtoList, attributeDtoList}`；
每个扩展字段（`ScalabilityDto`）：`{id, appId, optionId, prefix(≤20), caption, count(≤50), dataType, dataTypeProperties(JSON)}`。

## 3. 生成规则（EntityScalabilityService.resolveScalabilityAttribute，字节码）

- 每个扩展字段按 `count` 展开 count 个属性
- 属性 `name=caption=prefix+零填充序号`（`prefix001`/`prefix002`...）
- `sourceType=EXT`，`sourceId=扩展字段方案项 id`
- `dataTypeProperties` JSON 反序列化进属性（min/max/minLength/maxLength/decimalDigits；CURRENCY/DECIMAL 无 decimalDigits 时默认 2）
- `widgetConfig` 按平台默认控件枚举生成，list/detail/quickSearch 取 DataTypeDto 能力位
- orderNo 从 200 起累加
- 影子实体名：`name + "Ext"`（全局扩展 `name + "ExtGlobal"`），caption 后缀 `扩展`/`全局扩展`
- 影子实体自带 4 系统属性：createTime/updateTime/`parentId`(ENTITY,指主实体)/orderNo

## 4. 触发时机（EntityService，LIVE 双向验证）

- **create（udcEntityPost）不触发**：建实体带 `customScalabilityId` 只存值，不生成 Ext 实体
  （反编译：create() 方法体无 Scalability 调用；LIVE：带空方案 id 建实体，无 Ext 实体）
- **update（udcEntityUpdatePost）触发**：`resolveScalability(old, now)` →
  `updateScalability` + `updateScalabilityGlobal`（LIVE：更新带方案 id → 自动生成 `expHostExt` 影子实体）
- UI 上「新建弹窗选扩展实体 → 确定」走的是 post+update 链路，效果等同
- `customScalabilityId=null` 时落库为 `NULL_ID`(0)

## 5. LIVE 证据链（本轮实测，全部复原）

1. 方案列表：`udcScalabilityOptionSelectByAppidWithDetailAppGet`(path `{appId}`) →
   2 个方案；方案明细键名 **`scalabilityDtoList`**（不是 scalabilities）
2. 带含 Serial 扩展字段的方案建实体 → `UDC_ATTR_0019 必须指定流水号规则`
   （扩展字段含 Serial 时，方案里必须已配流水号方案，否则整链报错）
3. 空方案(id=4591...) post 不生成 Ext；update 带方案 → 生成 `expHostExt`(3439512140008539398)，
   属性组 4 系统属性（含 parentId ENTITY 指回主实体）
4. 清理：先删 Ext 实体再删宿主，均 BOOT_0000 content=1；列表回 10 条基线

## 6. 契约 ops

- 读：`udcScalabilityOptionSelectByAppidWithDetailAppGet` (query/path)
- 写：方案自身 CRUD 走 `udcScalability*` 族；实体挂方案 = `udcEntityUpdatePost` 带 `customScalabilityId`
- 影子实体与普通实体同构，删除主实体**不级联删 Ext 实体**（本轮手动先删 Ext）

## 7. 与其它槽位的区别

| 概念 | 落地 |
|---|---|
| 字段集 attributeSetIds | 复制预设属性组进本实体（orderNo=10 preset=true 组） |
| 扩展实体 customScalabilityId | 影子实体 name+Ext，扩展字段 sourceType=EXT |
| 父实体 parentEntityId | 子实体存 multiplicity，主子关联 |

## 8. 字段默认值/计算值（LIVE，另见 evidence/calculate-value-write.json）

- 默认值：cell 内嵌 input 直填静态值 → `defaultValue` 落库（LIVE：`defaultValue="默认文本X"` 回读）
- 计算值：cell「请设置」→ input → **Enter 打开「计算设置」表达式弹窗**（变量/函数树 + 验证/确定）；保存走
  `udcEntityAttributeUpdatePost`，关键字段 `expressionDesignData`/`expressionRuntimeData`
  + `calculate`(NORMAL=无)；LIVE 写入 → BOOT_0000 → 回读一致
- ★ expressionData 是 **JSON 字符串不是裸文本**：
  `{"designData":{context:[],expressionTranslation:"字段 = 1",resultTypeInfo:"INTEGER",tokens:[]},"runtimeData":<同构>}`
  —— 写裸文本（如 `整数字段 = 1`）后端 BOOT_0000 照收，但**前端 JSON.parse 直接抛 SyntaxError 整页崩**
  （NotFound removeChild 连锁）；designData 内层必须是对象（双 stringify 会让 expressionTranslation 取不到）
- 弹窗内「验证」做类型检查（STRING 字段对象类型结果被拒）
- 默认值表达式对：`defaultValueExpressionDesignData`/`RuntimeData`；`defaultValueIsChange`=UI「默认值修改」复选框
- 属性级更新用 `udcEntityAttributeUpdatePost`；`udcEntityAttributeGroupBathUpdatePost` 是组级替换（单属性会报 更新数据不存在）
- 详见 core/facts/udc/entity/rules-microflow.md 的姊妹文件与 evidence/calculate-value-write.json

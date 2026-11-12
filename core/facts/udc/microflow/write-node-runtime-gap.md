# 写节点运行时行为：CREATE_ENTITY 字段不生效（2026-11-01 LIVE 发现）

> **⚠️ 本文前半部分（§1–§11）的结论已被 §12 推翻，保留作纠错记录。**
> **最终结论：`attrs` 完全生效；真凶是实体自身的默认值表达式无条件覆盖。
> 2026-11-02 已在 `迁移断点` 上 RUNTIME_VERIFIED 通过。**
> 权威结论见 `node-insert-entity.md` §5。

> 证据等级 **LIVE**（真实执行日志 + 平台异常栈）
> 这是「业务结果验证」抓到的第一个问题——publish / build / UI 三层全绿，
> 真跑起来数据是错的。

## 1. 现象

用 `create_entity(fields={"f01text": "RTPROBE542937"})` 造流程，
publish `errors=0`、build `SUCCESS`、定时触发执行，结果：

```
CREATE_ENTITY 插入-运行验证  success=False
errorMsg:
  UdcEntityCheckException
  {"fullName":"...domain.entity.YsFull6956",
   "errorMsg":[{"-1":{"f05dec":["【小数字段】不能大于999.99"],
                     "f03int":["【整数字段】不能大于100"],
                     "f02multi":["多行文本不可为空"]}}]}
```

平台执行 INSERT 时 node input 的实体 DTO：

```jsonc
{"f01text":"",                    // ← 我设的 RTPROBE542937 没进去！
 "f02multi":"2026", "f03int":2026, "f05dec":2026.00,   // ← 实体默认值
 "f10bool":false, "f15enum":"NONE", ...}
```

即：**节点上配的字段值在运行时完全没有被应用**，平台用的是实体 DTO 的
全量默认值，于是撞上实体自身的校验规则（小数 >999.99、整数 >100、多行文本必填）。

## 2. 构造器产物是什么样

```python
node = mc.step("create_entity", "ce", entity=ENT,
               fields={"f01text": "MARK123"}, caption="插入-测试")
# → mappingType = "attrs"
# → attrs = [{attrType: {name: "f01text", ...}, value: {type: "Simple", simple: "MARK123"}}]
# → mapping = []        ← 空
# → value = None        ← 空
```

attrs 是有的、value 形态也对（`{"type":"Simple","simple":"MARK123"}`），
但运行时没生效。

## 3. 为什么之前没发现

- `create` / `publish(checkSchema)` 都过：结构合法，**平台不校验「运行时会不会生效」**
- UI 复测也过：设计器读 attrs 渲染，所以抽屉里看着是对的
- **48 条既有业务流程里一个 `CREATE_ENTITY` 都没有**（实测扫描）
  → 没有任何真实样本可对照，构造器形态从头到尾没被运行时验证过

## 4. 影响范围（待确认）

同类写节点用的是同一套 attrs 机制，因此**可能同样有问题**：

```
CREATE_ENTITY / CHANGE_ENTITY / DELETE_ENTITY（条件型）
CREATE_BATCH_ENTITY / CHANGE_BATCH_ENTITY
```

它们都只跑到过 `SCHEMA_VERIFIED`，从未验证运行时。

**这是一片空白区，不是单个节点的 bug。**

## 5. 待查

- [ ] 用设计器手搭一个 CREATE_ENTITY，回读真实形态对照（最权威）
- [ ] 或反编译运行时 jar（boot-starter-udcrt）看它读 attrs 还是 mapping
- [ ] 确认 `mappingType` 的正确取值（attrs / mapping / value 三选一？）
- [ ] 确认是否还缺字段（如 attrType 里的 transferPattern / pattern）

## 6. 已确认可用的旁证

- `CUSTOM_ERROR` 节点运行时**确实生效**（本次通过补 `_do_custom_error`
  + `_st_custom_error` 接上执行器；构造器 `microflow_nodes_extra.custom_error` 早已存在）
- 运行日志详情接口可按 traceId 拉逐步结果：
  `POST /service/{appName}/udc-runtime/app-log/search-details/microflow`
  body `{"params":{"traceId":...},"pageInfo":{...}}`
  ★ traceId 在一次调度批次里**多条流程共享**，必须再用 `microFlowCode` 过滤

## 7. 三条路径全部证伪（2026-11-02 更新）

为了确认「值形态」是不是根因，把能想到的三种写法全试了：

| 路径 | 形态 | 构建 | 运行时 |
|---|---|---|---|
| ① Simple 字面量 | `{"type":"Simple","simple":1}` | 成功 | 失败 |
| ② 引用 BASIC 变量 | `id=""`, `key=outputName` | 成功 | 失败 |
| ③ 引用 DTO 变量字段 | `name="f03int"`, `key=outputName+Dto.f03int` | 成功（修 name 后） | 失败 |

错误文本**逐字相同**：
```
UdcEntityCheckException: {"f05dec":["【小数字段】不能大于999.99"],
                          "f03int":["【整数字段】不能大于100"]}
```

### ★ 重要更正：`f02multi` 的「生效」是假象

早前观察到「`f02multi` 报错消失 ⇒ 字符串字段生效」，**这个推断是错的**。

回看节点 input 的实体 DTO：
```jsonc
{"f01text":"", "f02multi":"2026", "f03int":2026, "f05dec":2026.00}
```
`f02multi` 拿到的是 `"2026"`（平台统一填的默认值），不是我传的值。
它之所以不再报「不可为空」，只是因为 `"2026"` 恰好非空。

**结论：所有字段的 attrs 全都没被读取，不是「字符串生效、数值不生效」。**

## 8. 已排除的假设（全部实测否掉）

1. 结构/形态有问题 —— 设计器保存后回读与构造器产物逐字段一致（17 键、`mappingType=attrs`）
2. `mappingType` 是模板残留 —— 契约闸门 32 样本 100% 有
3. Simple 不生效、必须 SelectParam —— 两种都失败，错误相同
4. 数值类型不匹配 —— 实体定义（INTEGER/DECIMAL）与传入一致
5. `attrType.customs` 被模板污染 —— 确有其事（已修，见 §9），修好后错误不变
6. 实体字段有默认值 2026 —— 实体 `customs` 只有标志位 `defaultOrExpression:true`，**没有实际默认值**

## 9. 顺带确认并修复的两个真实缺陷

### ① `attrType.customs` 被模板污染

`create_entity` 里 `at = dict(proto)` 复制模板 `attrType`，而 `field_attr()` 不含 `customs`，
于是所有字段都背着模板字段（`f01text`）的身份：
`name=f01text, dataType=STRING, id=-4144494497326241617`。

平台按 `customs.dataType` 做类型转换。**已修**（直接用实体属性自带的 customs），
修复后与真实样本逐字段一致 —— 但运行时错误不变，所以它不是根因。

### ② `refs_field` 的 `name` 写成 `<outputName>.<field>`

平台编译期把它当 DTO 的嵌套类解析：
```
RtvXXXXService.java:[172,189] 找不到符号
  符号: 类 _CREATE_VARIABLE_2b08f1
  位置: 类 com.seeyon...dto.YsFull6956Dto
```
**已修**：`name` 改为纯字段名，与真实样本（`name="f03int"`）一致。

## 10. 构建注意事项（踩过的坑）

**`projectType: ALL` = 整个应用一起编**。任何一条历史遗留的错误流程都会让新流程构建失败，
报错还指向旧流程的类名 → 极易误判成新代码有问题。

- 构建失败先读 `deploy_status()["msg"]`（含 `compileLogUrl` + 完整 Maven 报错）。
  `p5_builder.wait()` 的 `problems` 对编译失败是空的。
- 临时验收流程用完即删，否则残留会持续污染后续构建。

## 11. 下一个该查的方向

**核心未知：平台运行时到底读节点的哪个键？** `attrs` 已证明不生效。

- 反编译运行时 jar（boot-starter-udcrt）看 CREATE_ENTITY 的取值逻辑 —— 本机无 kubectl，暂不可行
- **找 `CHANGE_ENTITY` 的真实运行样本**：业务里有用（`7268278945730137805`），
  如果它运行时生效，对比它的节点结构与 CREATE_ENTITY 的差异就是答案
- 设计器改一次数值字段后回读，看生成的形态与构造器产物差异

**UI 验证未完成**：读 ce 节点字段编辑器实际显示值的脚本已写（`scratch/_ui_check.py`），
但节点点击存在页面加载竞态（`NODE_NOT_SELECTED`），需加重试。

---

# ★★★ 根因彻底查明（2026-11-02，源码级证据）

> **前面 §7–§11 的推断全部作废。** 拿到构建产物源码后（`metadata/udc/<appId>/<buildVersion>.zip`，
> 含完整 `RtvXXXXService.java` + 实体 domain service），真相是：
> **`attrs` 完全生效；是实体自己的「默认值表达式」把值无条件覆盖了。**

## 12.1 怎么拿到源码（关键方法，以后直接用）

构建日志（`backBuild.log`）第一屏就写着元数据地址：

```
构建元数据: http://<HOST>/service//udc/file/download?storageKey=metadata/udc/<appId>/<buildVersion>.zip
日志路径:   /A8C/base/autocode/<appId>/<buildVersion>/backBuild.log
```

下载那个 zip（3.4MB / 3084 条目 / 258 个 java）即可拿到**完整后端源码**，
包含 `domain/service/microflow/RtvXXXXService.java`（微流程编译产物）。

```bash
curl -s -L -o meta.zip -H "Cookie: $CK" \
  "https://<HOST>/service/udc/file/download?storageKey=metadata/udc/<appId>/<buildVersion>.zip"
```

**不用反编译 runtime，不用进 pod，不用 kubectl。** 这条一出，之前所有黑盒猜测都该作废。

## 12.2 `attrs` 是生效的——生成的代码直接写着

`Rtv6553319Service.java:160-171`（CHANGE_VARIABLE）：

```java
private void assignValue2JavaBeanCHANGE_VARIABLE_f24862 (YsFull6956Dto javaBean) {
    javaBean.setF01text("RTV6553319");
    javaBean.setF02multi("RT");
    javaBean.setF03int(1);                              // ← 值是 1
    javaBean.setF05dec(new java.math.BigDecimal("1.5")); // ← 1.5
}
```

`:172-185`（CREATE_ENTITY 引用变量）：

```java
javaBean.setF03int(_CREATE_VARIABLE_8dcd86.getF03int());
javaBean.setF05dec(_CREATE_VARIABLE_8dcd86.getF05dec());
```

值一路正确传到 `create()`。**attrs / Simple / SelectParam / customs 全都不是问题。**

## 12.3 真凶：实体字段的「默认值表达式」无条件覆盖

`YsFull6956Service.preCreateBatch()`（每次 create 必走）：

```java
// 执行默认值表达式
executeExpressionYsFull6956(list, false, YsFull6956Dto::getF05dec,
                            this::exp9056335983934914588, YsFull6956Dto::setF05dec, null);
executeExpressionYsFull6956(list, false, YsFull6956Dto::getF03int, ...);
// …共 20 条
```

`executeExpressionYsFull6956` 的核心（注意第二个参数 `requireNull`）：

```java
if (requireNull) {
    if (isNull(setConditionFunction.apply(dto))) { dto.set字段(表达式结果); }
} else {
    T expressionResultValue = expressionFunction.apply(expressionMap);
    setFunction.accept(dto, expressionResultValue);     // ★ 无条件覆盖
}
```

表达式本体：

```java
public BigDecimal exp9056335983934914588(Map map) {
    return setDecimalScale((BigDecimal) dataTypeTransfer(
        DateFunction.currentYear(), "DECIMAL"), 2, HALF_UP);   // = 2026
}
```

**完整链路：**

```
传 f05dec = 1.5
  → 生成的代码 javaBean.setF05dec(1.5)          ✅ 生效
  → create() → preCreateBatch()
  → 执行默认值表达式 DateFunction.currentYear()
  → f05dec 被无条件覆盖成 2026.00               ← 传的值被丢弃
  → 校验 2026 > 999.99 → UdcEntityCheckException
```

## 12.4 结论：`小爪验收实体全量` 这个实体自己是坏的

扫描全部 24 个实体的 domain service：

| 实体 | 默认值表达式字段数 |
|---|---|
| `YsFull6956`（小爪验收实体全量） | **20**（含 f01text/f02multi/f03int/f05dec…） |
| `XzhExp950795` | 9 |
| `XzhDedBill` | 5 |
| 其余 20 个 | 2（仅 `getUpdater`，即"修改人=当前用户"） |
| `MigrationLog` / `MigrationPlanField` / `ExpTypeBase2` 等 8 个 | **0** |

`YsFull6956` 给 `f03int`/`f05dec` 配了 `currentYear()` 作为默认值表达式，
而字段约束是 `≤100` / `≤999.99`。**2026 天然违反自身约束 → 这个实体永远插入不了任何数据**，
不管传什么值。之前所有实验用的都是它，所以怎么看都是"值不生效"。

## 12.5 教训

1. **别用配了默认值表达式的实体做写验证**。它会把你要验证的东西整个盖掉。
   选实体前先扫 `*Service.java` 的 `executeExpression` 调用。
2. **构建产物 zip 是最高优先级证据源**，比 UI 回读、比运行时日志、比黑盒试探都强。
3. **"值不生效"要先怀疑实体配置**（默认值/计算表达式/不可修改字段），再怀疑构造器。
4. 一个判据如果依赖"我传的值会生效"，而目标实体有默认值表达式，这个判据从一开始就是坏的。

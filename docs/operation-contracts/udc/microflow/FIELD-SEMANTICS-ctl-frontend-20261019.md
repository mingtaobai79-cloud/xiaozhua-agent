# FIELD-SEMANTICS｜CONTROL 3 种 + 前端域分层

> ℹ️ **同批三件之二**：本文件 = CONTROL 3 种 + 前端域分层。另两件：
> `FIELD-SEMANTICS-app-std-20261019.md`（标准域 ACTIVITY）、
> `FIELD-SEMANTICS-final-20261019.md`（P2 收官）。共用快照戳 2026-10-17 15:41:03。

> `datamigration9000000000000000001`/test2 ｜ 输入 `NODE_REQUIRED_FIELDS`+`CONTROL_NODE_TYPES`
> **LIVE**（DB 只读逐实例）｜约束 **STATIC**｜0 `/service`、0 写库｜**戳 2026-10-17 15:41:03**

## 一、三个范围

- **A** 全部 47 条 → CONTROL **96**（END 46／BRANCH 16／CONDITION 34）｜ACTIVITY **155**
- **B** `type IN (0,3)` 20 条 → CONTROL 31（20/4/7）｜ACTIVITY 56
- **C** `type=1` 27 条 → CONTROL 65（26/12/27）｜ACTIVITY 99

★ ACTIVITY：A 155 = B 56 + C 99。「164 节点」= CONTROL 65 + ACTIVITY 99，**非 164 个 ACTIVITY**。
★ 全库 CONTROL 7 种／27054（CONDITION 14649、BRANCH 6390、END 4528、FOR_EACH 1241、CUSTOM_ERROR 123、FOR 68、BREAK 55）。
★ §二 全篇 A（96）：16+34+46=96 与 A 行自洽。

## 二、CONTROL 3 种（A，96）

约束仅 3 种有声明：`BRANCH:(conditions,)`、`CONDITION:(nodes,)`、`FOR:(operator,forStep)`；**`END` 未收录**。

### ②-1 BRANCH — 完全匹配（16／缺 0）

`conditions[]` 每项是一个 **CONDITION 节点**（非条件项），`nodes[]` 为分支体（可递归）。
**实测长度分布 1×1、2×14、5×1**（5 项者 `BRANCH_28vudK`@m260409150713320）。
→ 长度**非「1~2 不变量」**，只能写「以 2 项为主（14/16）」；5 项分支正常存库。

### ②-2 CONDITION — 约束过宽（34／缺 7）

nodes 有值 27／空 7。空 body 7 例：**末位 5**（x18、n18_1、EF5Kg0、sZ5OsR、f28_1）；**非末位 2**（n18_0、jxFAX9，二者 expr 均有值）。
★ **撤回上一版判据**「`nodes` 仅非末位且 expr 非空时应非空」：被 `n18_0`、`jxFAX9`（非末位＋expr 有值＋body 空）推翻。
→ 空 body 的**位置与 expression 都不能预测**它；7/34 可存库 = 设计器允许空分支体。
→ 定性仍 **约束过宽**（`nodes` 写成无条件必填），但**「何时必填」无判据**，需设计器语义，本切片不下结论。
→ **非脏数据**：7 例均可存库，合法空分支。

### ②-3 END — 契约缺口（46／未收录，低优先）

46 个全带 `actionType=END_NODE`。**键数分布** 9×29、10×3、13×1、14×4、15×1、17×4、18×1、19×2、25×1。
★ 最小 **9 键**（29 例）：`{actionType,caption,description,id,input,name,nodeId,output,type}` —— **`output` 键在、值 null**，不能写「无 output」。
→ 46/46 全带 `output`；差异在 `paramType`/`entityObject`/`hasPagination`/`isArray`/`mappingType`/`app|basic`。
→ **契约缺口，低优先**（后端不校验 END）；补契约须先定「最小 9 键是否合法」。上一版「仅 4 键」错。

### ②-4 声明 8／实测 3：VACUUM 5 种

未出现：`FOR_EACH`、`CUSTOM_ERROR`、`FOR`、`BREAK`、`ACTIVITY`（作 type）。
★ **负证据连范围**：限**本 app 47 条内 0 实例**，非全库 0（全库数见 §一全部 7 种）。`ACTIVITY` 作 type 全库也无（占位映射）。

## 三、前端域 type=1（27 流程／99 ACT／164 节点）

### ③-1 必填集矩阵：27 种**全部未收录**

27 种／99 实例，`NODE_REQUIRED_FIELDS` 命中 **0 种** → **整域契约缺口**，非「约束过宽」。
constraints 只建模后端标准域（`ACTIVITY_NODE_TYPES` 30 种），前端 37 种从未纳入；前端校验需独立建表，**超本切片**。

### ③-2 种类普查

`CALL_MICRO_FLOW` 24(2613)｜`MESSAGE_INFO` 16(1313)｜`VALUE_HANDLE` 10(1993)｜`OPEN_PAGE` 10(304)｜`ENTITY_SAVE` 7(196)｜`ENTITY_REFRESH` 7(239)｜`CONFIRM_CLOSE_PAGE` 4(123)｜`CONTROL_ACTION` 2(312)｜余 19 种各 1（括号=全库）

前 8 种 80＋余 19 = **99**。
全库 37 种、本 app 27 种；**本 app 有、全库无 0 种**；全库有本 app 无 10 种：`ADVANCED_PROPERTIES`/`ATTACHMENT_PREVIEW`/`CLOSE_PAGE`/`ENTITY_DELETE`/`ENTITY_SUBMIT`/`FORM_CONVERT`/`FRONT_CUSTOM_ERROR`/`LOCATION_CMP`/`SET_VALUE`/`VISIBLE`。

### ③-3 高频抽样（≥3 实例）

**CALL_MICRO_FLOW（24，抽 4）** 实测 11 键 `{actionType,caption,description,input,isCompleted,mfService,name,nodeId,output,runAfter,type}`。
★ 上一版「Zr49XT 仅四键」错：同样 11 键，`output` 在、值 null。
→ `mfService` **24/24 全有** = 实质必填锚点（未被收录）；`input`/`output`/`runAfter` 可选。

**ENTITY_SAVE（7，抽 4）** 稳定 `{actionType,caption,config,nodeId,type}`；`config` **7/7**、`output` **4/7**。

## 四、差集（逐实例）

```
CONTROL（A，96）  16+34+46 = 96 ← 与 §一 自洽
  BRANCH    16  缺 0         完全匹配（长 1×1/2×14/5×1）
  CONDITION 34  缺 7（nodes） 约束过宽（空 body 位置/expr 不可预测）
  END       46  未收录        契约缺口（低优先，46/46 带 output）
  未出现 5 种   —  —          VACUUM（限本 app；全库均有）

前端域（27 流程／99 ACTIVITY）
  27 种全部未收录  整域契约缺口 ｜ CALL_MICRO_FLOW 24/24 mfService ｜ ENTITY_SAVE 7/7 config、output 4/7
```
→ **无脏数据**：CONDITION 空 body 合法；前端未收录是建模范围问题。

## 五、抽样指针

```
CONTROL（A）
CONDITION_x18    xzhStdReal31046 末位  expr=YES body=0
CONDITION_n18_0  xzhFinalAllNodes 非末位 expr=YES body=0 ← 推翻旧判据
CONDITION_jxFAX9 MFSERVICEHbICrp 非末位 expr=YES body=0 ← 同上
CONDITION_sZ5OsR MFSERVICEHbICrp 末位  expr=no  body=0
CONDITION_EF5Kg0 m260409150713320 末位 expr=no body=0（type=1）
BRANCH_28vudK    m260409150713320 conditions=5（唯一非 2 项）
MFEndNode        xzhSch1EFP       9 键最小 output=null
MFEndNode        MFFRONTENDilmXlt 25 键 output=null
前端域
CALL_MICRO_FLOW_Zr49XT m261017154103069 11 键 output=null
ENTITY_SAVE_BvDL4i MFFRONTENDiGUQL7 有／JH2H1z 无 output
```

## 六、未覆盖

- 前端 27 种**未逐种展开**（只做普查+矩阵+抽样）；全库有本 app 无的 10 种未实测
- `FOR_EACH`/`FOR`/`BREAK`/`CUSTOM_ERROR` 全库有实例但本 app 无，**未取语义**
- **CONDITION 空 body「何时必填」无判据**；`END` 最小 9 键是否合法未定；前端 iframe/SSO 未触及

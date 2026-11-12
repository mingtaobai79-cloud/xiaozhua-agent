# RULE-GENERATION-CONTRACT｜规则生成契约（P3 切片①）

> 源：P2 收口文档 @`12e5b70`（app-std `87240c7`／ctl `7b5f96b`／final `12e5b70`）
> `datamigration9000000000000000001`/test2 ｜ **LIVE**（DB 只读复算）＋**STATIC**（constraints）
> 0 `/service`、0 写库 ｜ 所有数字本切片独立复算，非转抄

## 一、规则可引用项（四类）

### ① 字段语义（`[实测]` 逐实例）

| 项 | 取值 | 依据 | 用法 |
|---|---|---|---|
| `DATA_MAPPING.mappingRule` | **dict 非 JSON 串** | 本 app 6/6 | 勿 `json.loads` |
| `RETRIEVE` 必填 | `condition`(COND/COUNT/OTHERS)｜`value`(IDS)｜`nullPromptMessage`(仅 TERM) | L67 | **无 size/aggFunction** |
| `RETRIEVE_ARRAY` 必填 | `fetchType`｜`condition`(COND/COUNT/OTHERS)｜`value`(IDS)｜`size`(仅 COND)｜`aggFunction`+`countAttrs`(仅 OTHERS) | L36+L59 | 三者只属此节点 |
| `RETRIEVE.nullHandling` | 结构式1839：CONT1618／TERM219／None2 | 全库 | §二.2 |
| `CALL_MICRO_FLOW.mfService` | 目标流程 id | 本 app 24/24 | 必带 |
| `END.output` | 键 46/46 在，null 34/46 | 本 app | **有键无值合法**，禁判「无 output」 |

`[推断]` `mappingRule` 内部 8 键属 SUB_MICROFLOW 样本，**未在全库逐个核**；只读 `targetType`/`mappingRows`。

### ② 键集（`[静态]` constraints + `[实测]` 落库）

```
NODE_REQUIRED_FIELDS 21｜ACTIVITY_NODE_TYPES 30｜CONTROL_NODE_TYPES 8（同文件）
```
- 本 app ACTIVITY **18 种**，**未收录 2 种**（`CHANGE_BATCH_ENTITY`、`CREATE_MAP`）；实例数未单列
- `required_fields()` 按**逐实例**：`「缺」= 缺该字段的实例数`

★ **`pageSearch` 是 `RETRIEVE_ARRAY` 的 shape，不是 `RETRIEVE` 的**：`required_fields()` 对该节点只按
`fetchType` 过滤 `size`/`aggFunction`，**无 `pageSearch` 维度**→`fetchType=CONDITION` 且
`pageSearch=true` 时**不要补 `size`**（否则假失败；样本 `RETRIEVE_ARRAY_x3/_n3` 均 `size=null`）。
**`RETRIEVE` 无 `size`/`aggFunction` 字段**，勿混。

### ③ nullHandling（`[实测]` 全库对照）

```
结构式遍历全库 RETRIEVE = 1839（沿 nodes[] 与 conditions[].nodes[]）
  CONTINUE     1618 → nullPromptMessage 0 例带
  TERMINATION   219 → nullPromptMessage 219 例全带
  None            2 → 未配置，按 CONTINUE 处理（不补 prompt）
取证：§五.2
```
→ 判据：`nullHandling=="TERMINATION"` 才必填 `nullPromptMessage`。
★ **枚举是 `TERMINATION` 不是 `STOP`**（源码 L35 注释写 STOP 是注释错）。

### ④ fetchType（`RETRIEVE_ARRAY` 6／全库 603）

```
本 app 6（全 COND，IDS/COUNT/OTHERS 各 0）｜全库见 §5.5
```
× `pageSearch='false'` → `size` 必填、无 `pageInfo`
× `pageSearch='true'`  → `size` 不可填、`pageInfo` 有值或 None
★ 三写法（布尔串化、大小写不一）**读前先归一**，否则 `'false'` 被当真值

## 二、两条硬约束（生成器必须实现）

### 2.1 空分支体必须放行

```
conditions[].nodes = []   → 合法，禁止报错、禁止修复
```
| 范围 | COND | 空 body | 占比 |
|---|---|---|---|
| 本 app 47 条 | **34** | **7** | 7/34 |
| 全库 type=2 | **67** | **30** | 30/67 |

★ 原判据原句：**空 body 合法**。位置与 expression 均不可预测（末位 5／非末位 2，后者 expr 有值）。
→ 生成器与校验器一律放行，**不得**当脏数据清理。

### 2.2 流程去重一律 `(app_id, name)`，禁按 `name`

```
type=2 同名跨 app 8 组×2 app，组内 md5 全互异：rulecUbY53/ruleeZofmv/rulefXSC2F/ruleKkBf8U
/ruleLB3Ij0/rulePeIsl7/ruleRaZJhS/ruleVenDVd
```
→ **禁按 name**。仅按 `name` 会把两 app 同名流程判成同一条（md5 不同、语义不同）。
★ 反向证据：全库 847 组中 122 组组内 md5 有重复＝**全同 115＋部分 7**（§五.3），
但**md5 相同也不是合并理由**，键类型不同。

## 三、生成侧落库字段（`[实测]` 表结构）

`udc_microflow_info` NOT NULL 12 列：`id,create_time,tenant_id,update_time,version,guid,order_no,trigger_type,type,version_code,creation_method,original_id`（仅末列默认 0）。
`type=2` `data_schema` 顶层键 25/25：`output/input/sourceType/trigger/nodes`；`endNode` **24/25**（`rulesc8mOQ` 缺）。取证 §五.4

★ 写入口径（`[静态]` CFR）：`POST /service/udc/graphql?udcMicroflowCreatePost`（body=MicroFlowDefinitionDto），写前 `udcMicroflowCheckSchemaUpdatePost` 校验。

## 四、边界与未覆盖

- `[推断]` 仅 1 处（§一.① 末段），余皆实测或静态
- `type=1` 前端域 27 种枚举**不适用本契约**（另一套）
- `pageSearch` 缺口**仅记录未修**，不改 `required_fields()`
- 落库验证（§三）未执行：`zzprobe` 在 udc／udc_test2／udc_uat 三库均不存在

## 五、取证指针（本文新算数字，P2 三份无）

### 5.1 CONDITION 口径（7/34、30/67）
```
udc_test2.udc_microflow_info，仅 type=='BRANCH' 的 .conditions[]
本 app app_id=8704025620829192834 → 47 行 / BRANCH 16 / COND 34 / 空[] 7
全库 type=2                     → 25 行 / BRANCH 33 / COND 67 / 空[] 30
scratch/p3_cond2.py
```
★ 错口径（任意带 conditions 节点）→ 50/23、17108/6444

### 5.2 nullHandling × nullPromptMessage
```
udc_test2.udc_microflow_info 4755 行；结构式遍历（nodes[]+conditions[].nodes[]）
★ 递归全 dict 虚增（首版 2593）；仅顶层 856
CONTINUE 1618 → prompt 0 例｜TERMINATION 219 → prompt 219 例
```

### 5.3 去重键证据
```
udc_test2.udc_microflow_info
type=2 GROUP BY name HAVING COUNT(DISTINCT app_id)>1 → 8 组（MD5 全互异）
全库无过滤 → 847 组；md5 有重复 122＝全同 115＋部分 7
```

### 5.4 表结构（§三）
```
udc_test2.udc_microflow_info：DESC 32 列 / NOT NULL 12 列
type=2 25 行：顶层 output/input/sourceType/trigger/nodes 各 25/25；endNode 24/25
脚本 scratch/p3_fix1.py
```

### 5.5 RETRIEVE_ARRAY 603
```
603=COND482+COUNT39+IDS37+OTHERS43+None2
ps×size：'false'373全有｜'true'106全空｜'N'3有｜键缺112+None9空
scratch/p3_d195_tmp.py
```
# GENERATION-PLAN｜规则生成计划（P3②，只读比对）

> 状态：**UNVERIFIED**（③落库验证 BLOCKED，未解锁）
> 环境 `datamigration9000000000000000001`/test2 ｜ 只读 DB ｜ 0 `/service`、0 写库
> 契约基线 `RULE-GENERATION-CONTRACT-20261019.md` @`97c9f48`（D196 收口版）

## 一、只读比对：契约四类清单 × 现网 47 条流程

结构式遍历（`nodes[]` + `conditions[].nodes[]`）本 app `actionType` 去重 45 种（按流程分层 `type=0` 18／`type=1` 27／`type=3` 3），其中契约覆盖的：

| 节点 | 实例 | 契约清单字段实况 |
|---|---|---|
| `RETRIEVE` | 7 | `fetchType` 7/7、`nullHandling` 7/7、`condition` 4/7（键在 5/7）、`value` 3/7 |
| `RETRIEVE_ARRAY` | 6 | `fetchType` 6/6、`pageSearch` 6/6、`condition` 6/6、`size` 4/6、`nullHandling` 3/6、`aggFunction` 0/6（键在 1/6）、`countAttrs` 0/6（键在 1/6） |
| `DATA_MAPPING` | 6 | `mappingRule` 6/6（全 dict） |

★ **分母口径 = 值为非 null 的实例数 / 该类总数**（非「键存在」）。两者有差异处已双标：
```
RETRIEVE.condition        4/7  （键在 5/7）
RETRIEVE_ARRAY.aggFunction 0/6  （键在 1/6，唯一 1 例值为 null）
RETRIEVE_ARRAY.countAttrs  0/6  （同 1 例，与 aggFunction 同节点）
RETRIEVE_ARRAY.size        4/6  （键在 4/6，另 2 例键缺失）
```

**字段名全在契约内，无引用了契约外字段的实例。** 但 `countAttrs` 覆盖 **0/6**（键在 1/6、值为 null）——
它是契约 L15 `RETRIEVE_ARRAY` OTHERS 分支的必填项（D191 FAIL-3 补入），本 app 无正例可用，
**③ 生成时须显式写入，不得因「无现网样本」而省略**。

### 分层核对（必须分层，否则缺口统计失真）
```
flow type=0（后端域）18 种 actionType → 契约覆盖 16 种，缺 2：
    CHANGE_BATCH_ENTITY 2 实例 ｜ CREATE_MAP 1 实例（与 P2 app-std 口径一致）
flow type=1（前端域）27 种 actionType → 契约覆盖 0 种
    前端域是另一套枚举（CALL_MICRO_FLOW 24／MESSAGE_INFO 16／OPEN_PAGE 10…）
    → 本契约只覆盖后端域，前端域不计入缺口
```
若不分层，会得出「45 种中 29 种未覆盖」的假缺口。

## 二、比对发现的 3 个契约缺口（本切片新证）

### 缺口① `pageSearch` 取值有第 3 种形态 `'N'`
```
全库 RETRIEVE_ARRAY 603 实例：
  'false' 373 → size 有值 373/373     ← 契约覆盖
  'true'  106 → size 缺失 95 / null 11 ← 契约覆盖
  'N'       3 → size 有值 3/3          ← 契约未覆盖
  None      9 → size null 9/9
  MISSING 112 → size 也 MISSING
```
契约只写「布尔字符串化、大小写不一」，**未列 `'N'`**。生成器若只判 `'false'`，
这 3 例会被当成「未知值」报错或误补 `size` 判断。→ **归一化表须含 `'N'`→false**。

### 缺口② `size` 在 `pageSearch='true'` 时是「缺失」而非「null」
```
'true' 且 size 缺失 95 例 ／ 'true' 且 size=null 11 例
```
两种形态并存。契约写「不可填」，但**「不写这个键」与「写 null」都是合法的**，
生成器若强制写 `size:null` 会产生 95 例形态不一致。→ 应允许**省略键**。

### 缺口③ `RETRIEVE_ARRAY.nullHandling` 存在但契约未列
```
本 app 3/6 有 nullHandling（值全 CONTINUE）
```
`NODE_REQUIRED_FIELDS["RETRIEVE_ARRAY"]` 不含它，故非必填；但**现网 3/6 实际带**。
契约未说明该字段对 `RETRIEVE_ARRAY` 是否生效。→ 生成侧保守策略：**不主动写**，
若上游给了则保留，不校验。

## 三、生成步骤（③解锁后执行）

```
S1 取 zzprobe-p3 appId（BLOCKED：应用不存在 + test-account-1 无后台权限）
S2 POST /service/udc/graphql?udcMicroflowCheckSchemaUpdatePost 预校验
   body: {appId, type:2, data_schema:{endNode,output,input,sourceType,trigger,nodes}}
S3 校验通过 → udcMicroflowCreatePost
S4 DB 回读：SELECT data_schema FROM udc_microflow_info WHERE id=? AND app_id=?
S5 比对：字段集 ⊇ 契约必填集；空分支体 [] 不报错；name 唯一性按 (app_id,name)
```
每步 ≤1 次 `/service`（本轮 0 次），间隔 ≥30s。

## 四、校验点（回归清单）

| # | 校验点 | 判据 |
|---|---|---|
| C1 | 空分支体放行 | `conditions[].nodes=[]` 不报错（全库 30/67、本 app 7/34） |
| C2 | 去重键 | 按 `(app_id,name)`，非 `name`（type=2 同名跨 app 8 组 md5 互异） |
| C3 | `RETRIEVE` 无 size | 若生成器往 `RETRIEVE` 写 `size`/`aggFunction` 即 FAIL |
| C4 | `RETRIEVE_ARRAY.size` | 仅 `fetchType=CONDITION` 且 `pageSearch∉{true}` 才写 |
| C5 | `nullPromptMessage` | 仅 `nullHandling=TERMINATION` 才写 |
| C6 | `mappingRule` | dict，禁 `json.dumps` |

## 五、回填清单（③解锁后补 ②③）

- [ ] zzprobe-p3 appId 回执
- [ ] `udcMicroflowCheckSchemaUpdatePost` 响应（含 code）
- [ ] `udcMicroflowCreatePost` 响应 + 新 id
- [ ] DB 回读 `data_schema` 比对结果
- [ ] 运行态可达性（或明确 BLOCKED）
- [ ] 把缺口①②③ 回填契约文档（本轮只记录，不改契约）

## 六、解锁条件

```
BLOCKED 根因（两层）：
  1. zzprobe 应用不存在（udc/udc_test2/udc_uat 三库 0 行）
  2. test-account-1 无 /main/backstageManage 权限 → 无法页面建应用
解锁路径：用户授予后台权限 或 手工建 zzprobe-p3 并给 appId
```

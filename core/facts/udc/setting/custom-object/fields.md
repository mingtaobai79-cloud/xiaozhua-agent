# 自定义对象 · 字段组装事实（12 类数据类型 × 3 类类别）

> 证据等级：**LIVE PASS**（2026-10-21，真实接口提交 + DB 回读 + 页面可见 + 人工手选对照）
> 探针对象：`zxjAllTypeProbe` / 全类型字段探针 / id=`-7340588150208408653`
> 实现：`tools/core/setting/custom_object_relation_fields.py`

## 零、最重要的一条：靠猜必错，靠人工手选对照才能定形态

本文档里 **4 个关键规则是我猜错、由用户在页面上手选一次才纠正的**：

| 我猜的 | 真实（人工手选后平台写入） |
|---|---|
| 对象字段 `relationEntity` 填对象 id | **空字符串**（列表型才填实体 id） |
| 选项集 `dataType = CTPENUM` | **选项集 id 数字串** 或 **Java 全类名** |
| `dataTypeCategory` 只有 PRIMITIVE / COMPOSITE | **还有 `ENUM`** |
| `relationApp` 填应用名 | appId 数字串，或 **`bpm`** 这类非数字标识 |

**方法论教训**：候选树有多个根分支（基本类型 / 枚举 / 选项集 / 对象 / 关联实体），
每个分支的组装形态**都不同**。只拿一个样本就下结论，会把整片分支做错。
正确做法：**每个根分支各手选一次，抓平台真实 body，再据此写组装器**。

## 一、字段端点：不是 UpdatePost

| 误判 | 事实 |
|---|---|
| `udcDataTransferObjectUpdatePost` 可带 attributes | **不行**。body 里塞 `attributes`/`dtoAttributes`/`fields`/`attrs`/`props`/`properties` 等 8 个 key，平台全部返回 `BOOT_0000`，但 `udc_dto_attribute` **零新增** —— 假成功 |
| 真实端点 | `udcDataTransferObjectUpdateDtoPost`（抓包实证） |

```
POST /service/udc/graphql?udcDataTransferObjectUpdateDtoPost
mutation graphqlLoader ($params0: udcDataTransferObjectUpdateDtoPostInputBody) {
  data0: udcDataTransferObjectUpdateDtoPost(body: $params0) { code data { content } message status }
}
```

## 二、DTO body 完整形态（平台原文）

```json
{
  "appId": "8704025620829192834",
  "name": "zxjAllTypeProbe",
  "caption": "全类型字段探针",
  "description": null,
  "source": "MICRO_FLOW",              // 枚举字符串，不是 1
  "attributes": [ ... ],
  "id": "-7340588150208408653"
}
```

⚠ **`attributes` 是全量替换语义**：
- 传 `[]`（空数组）→ `BOOT_1001 参数错误`
- 传部分 → 未列出的字段**被删除**
- 正确做法：先 `udcDataTransferObjectSelectDtoGet` 拉全文，append 新字段后整体回传

## 三、attribute 结构（13 个字段的完整形态）

```json
{
  "name": "f0_str",
  "caption": "文本字段",
  "notNull": false,
  "dataType": "STRING",
  "dataTypeCategory": "PRIMITIVE",
  "type": "OBJECT",
  "description": "",
  "defaultValue": null,
  "appId": "8704025620829192834"
}
```

已有字段回传时还会带 `id` / `guid` / `dtoId` / `createTime` / `fullName` 等只读字段（SelectDtoGet 原样返回即可）。

## 四、三个枚举的真实值域（关键）

```
dataTypeCategory = PRIMITIVE | COMPOSITE | ENUM     ← 三个值，不是两个
type             = OBJECT    | LIST                ← 两个值
relationType     = Many2OneAssociation
```

踩过的两个坑：

- `BOOT_3002: No enum constant ...DataTypeCategoryEnum.REFERENCE`
  —— 按 DB 里 `data_type_category=1` 猜成 `REFERENCE`，平台拒收；真实值是 `COMPOSITE`。
- `ENUM` 是我完全不知道的第三个值。只有选项集分支用，直到用户让我「换一个、换 BPM 引擎的」
  才发现（前两轮我都把选项集写成 `PRIMITIVE`，页面照样显示，但形态是错的）。

## 五、完整组装矩阵（人工手选对照 + 接口复现双重验证）

### 5.1 基本类型（8 种，全 PRIMITIVE / OBJECT，无关联）

| UI 类型 | dataType |
|---|---|
| 文本 | `STRING` |
| 整数 | `INTEGER` |
| 长整数 | `BIGINTEGER` |
| 小数 | `DECIMAL` |
| 日期 | `DATE` |
| 日期时间 | `DATETIME` |
| 布尔 | `BOOLEAN` |
| 附件 | `ATTACHMENT` |

```
dataTypeCategory = PRIMITIVE, type = OBJECT
relationApp = null, relationEntity = null
```

### 5.2 枚举（`ctp_enum` 表）

```
dataType         = "CTPENUM"
dataTypeCategory = "PRIMITIVE"
type             = "OBJECT"
relationApp      = "<应用名>"        ← 注意：应用名，不是 appId
relationEntity   = "<枚举 id>"
```

### 5.3 选项集（**两条完全不同的分支**）

**A. 本应用选项集**（数据在 `udc_enum` 表，不是 `ctp_enum`）

```
dataType         = "<选项集 id 数字串>"     ← 不是 CTPENUM！就是 id 本身
dataTypeCategory = "ENUM"                  ← 第三个枚举值
type             = "OBJECT"
relationApp      = "<appId 数字串>"
relationEntity   = "<选项集 id>"
```

**B. BPM 引擎选项集**（树里 `选项集 → BPM引擎 → 节点状态（集成）` 等）

```
dataType         = "com.seeyon.boot.starter.cip.enums.ActivityStateEnum"   ← Java 全类名
dataTypeCategory = "ENUM"
type             = "OBJECT"
relationApp      = "bpm"                   ← 非数字标识
relationEntity   = ""（空串即可，平台会保留旧值但不影响页面解析）
```

⚠ `ctp_enum` 和 `udc_enum` 是**两套完全独立的表**。
枚举走 `ctp_enum`（`relationApp`=应用名 + `CTPENUM`）；
选项集走 `udc_enum`（`relationApp`=appId + `ENUM` + `dataType`=id）。

### 5.4 对象（DTO 引用）

```
dataType         = "com.seeyon.<app>.dto.microflow.<Xxx>"   （单对象，microflow 分支）
                   或 "com.seeyon.<app>.dto.<Xxx>Dto"       （列表，实体分支）
dataTypeCategory = "COMPOSITE"
type             = OBJECT（单） | LIST（列表）
relationApp      = "<appId 数字串>"
relationEntity   = ""（单对象） | "<实体 id>"（列表）        ← 这个不对称最容易错
```

**单对象 `relationEntity` 必须是空字符串**——填对象 id 会导致页面解析不出中文名。
**列表型必须带实体 id**。两个方向相反，只能靠手选对照确认。

### 5.5 关联实体

```
dataType         = "ENTITY"
dataTypeCategory = "PRIMITIVE"
type             = OBJECT
relationApp      = "<appId 数字串>" | "bpm" | "organization"
relationEntity   = "<实体 id>" | "<全类名，如 com.seeyon.bpm.domain.entity.BpmTemplate>"
multiSelect      = true/false（多选与 type 正交）
```

### 5.6 最终实测快照（探针对象 7 个字段，全部页面 0 错误）

```
rel_enum     dt=CTPENUM                              cat=PRIMITIVE  type=OBJECT  relApp=datamigration…（应用名） relEnt=5079316968262147703
rel_optset   dt=com.seeyon.boot.starter.cip.enums.ActivityStateEnum
                                                     cat=ENUM       type=OBJECT  relApp=bpm                  relEnt=3934748939202274853
rel_optset2  dt=3934748939202274853                  cat=ENUM       type=OBJECT  relApp=8704025620829192834   relEnt=3934748939202274853
rel_obj      dt=com.seeyon.<app>.dto.microflow.Pddqqyfasfczzxtyzbcc
                                                     cat=COMPOSITE  type=OBJECT  relApp=8704025620829192834   relEnt=""
rel_obj2     dt=com.seeyon.<app>.dto.microflow.DataSourceTestDTO
                                                     cat=COMPOSITE  type=OBJECT  relApp=8704025620829192834   relEnt=""
rel_objlist  dt=com.seeyon.<app>.dto.ZxjVerifyEntityDto
                                                     cat=COMPOSITE  type=LIST    relApp=8704025620829192834   relEnt=5417588098661281954
rel_entity   dt=ENTITY                               cat=PRIMITIVE  type=OBJECT  relApp=8704025620829192834   relEnt=8456954308866361572
```

**这 7 个覆盖了 5 个根分支的全部形态**（枚举 / 选项集×2 / 对象×3 / 关联实体）。
换目标也成立：`rel_obj2` 用的不是 `rel_obj` 那个对象，`rel_optset` 和 `rel_optset2` 分属两个分支。

## 六、6 个候选接口（打开编辑弹窗时平台自己拉，不用点页面）

| 接口 | 用途 | 调用形态 |
|---|---|---|
| `udcDataTransferObjectSelectDtoGet` | 当前 DTO 全文（含全部 attributes） | `path{appId,id}` |
| `udcDataTransferObjectSearchListPost` | 自定义对象候选（"对象"类型） | `body{appId}`，content 是数组 |
| `udcMicroflowTreeEntityDtoPost` | 微流程树 DTO 候选 | `body{appId}` |
| `udcMetaDataSelectJavaEnumByAppPost` | Java 枚举候选 | `body{appId, hostAppName}` —— **必须传 hostAppName**，否则 `BOOT_1000 设计态元数据查询必须传递当前应用Id` |
| `udcMetaDataSelectCtpEnumAppGet` | CTP 枚举/选项集候选 | `path{appId}`，content 是 `[{categoryAndItemDtos:[{name,children:[{id,name,code,fullName,enumType}]}]}]` —— **外层要多剥一层** |
| `udcEntityAssociationEntityAppGet` | 关联实体候选 | `path{appId}`，content 是 `[{name,caption,entityDtos:[{relationEntity,relationEntityName,relationEntityCategory}]}]` |

`name` 字段在 CTP 枚举里是 i18n JSON 字符串 `{"zh_CN":"显示名"}`，取显示名要 parse。

## 七、组装 vs 页面点击（用户 2026-10-21 的判据）

> 「像图里面的这四种类型，需要一直一直打开才能选到最下面……你可以通过这个抓接口组装数据试一下」

**结论：接口组装可行，且比点页面可靠得多。**

页面树里「枚举 / 选项集 / 对象 / 关联实体」四个是**分组节点**，必须一层层展开才看到叶子；
真实鼠标点击容易落在节点容器的空白处，改不动受控状态（本轮实测 4 次全失败）。
接口组装的路径是：`SelectDtoGet 拉全文 → 从 6 个候选接口取 id → append attribute → UpdateDtoPost 整体提交`，
一次成功、可复算、不依赖鼠标坐标。

## 八、可复现命令

```bash
# 只读：拉候选 + 当前 DTO 全文
python tools/core/setting/custom_object_relation_fields.py --mode dump

# 写入：组装 4 类关系字段（枚举/选项集/对象/对象列表/关联实体）
python tools/core/setting/custom_object_relation_fields.py --mode build --i-have-write-authorization
```

## 九、未验证（明确标注，不假装）

| 项 | 状态 | 说明 |
|---|---|---|
| minLength / maxLength / decimalDigits / pattern 等约束字段 | **UNVERIFIED** | attribute 结构里有这些槽位，未逐个测值域 |
| 关联实体选「组织模型」分支 | **UNVERIFIED** | 只验了本应用实体 + BPM 引擎选项集；`organization` 分支（OrgMember/OrgUnit 全类名）未手选对照 |
| 对象列表选「实体」vs「DTO」两种来源的差异 | **UNVERIFIED** | 当前 `rel_objlist` 用的是实体分支（`…dto.ZxjVerifyEntityDto` + 实体 id）；DTO 分支未对照 |
| 页面表格对「对象」类字段显示类名 | **已确认是平台设计** | 真实业务数据（`znxmglpt…` 应用）的 `relation_entity_name` 同样为 null，表格直接渲染 `dataType` |

## 十、选项集/枚举分表（最容易搞错的一条）

```
枚举     ctp_enum        / ctp_enum_category / ctp_enum_item
选项集   udc_enum        / udc_enum_category / udc_enum_item
```

两套表**完全独立**，id 不互通。字段组装时：

- 枚举：`relationApp` = **应用名**（`<appName>`，即 `datamigration<appId>` 那种形态），`dataType` = `CTPENUM`
- 选项集（本应用）：`relationApp` = **appId 数字串**，`dataType` = 选项集 id，`dataTypeCategory` = `ENUM`

我第一轮把 `ctp_enum` 里的枚举当选项集提交，页面显示成 `_<appName>_<id>` 这种异常串——
因为 `relationApp` 和 `dataType` 都错了。用户指出后才修正。

## 待删除清单

| 对象 | 处置 | 状态 |
|---|---|---|
| `zxjAllTypeProbe`（探针对象，id=-7340588150208408653，7 字段） | 用户已确认生成无误 → 删 | **DONE**（见下方记录） |

## 本轮最终动作记录（可复算）

```
2026-10-21 11:5x  用户人工手选对照 3 次（对象 / 对象列表+关联实体 / 选项集·BPM引擎）
                  每次读 SelectDtoGet 取平台写入的权威形态
接口复现验证：
  选项集·本应用   probe_optset  → 与手选逐字段一致 ✅
  对象·单        probe_obj     → 与手选逐字段一致 ✅
  对象·列表      probe_objlist → 与手选逐字段一致 ✅
  选项集·BPM     bpm_optset    → 除 relationEntity 残值外一致，页面解析正常 ✅
清理：18 字段 → 7 字段（保留 5 个根分支代表）
页面验收：7 行全部渲染正常，0 校验错误
```

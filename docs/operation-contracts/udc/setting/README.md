# docs/operation-contracts/udc/setting/ 索引

## 这个目录是什么

**设置域 11 个 tab 的 Operation Contract**：每个 tab 的端点、协议（GraphQL 还是 REST）、
必填槽位、错误码、落库表。

与三处相邻内容的分工，**不要混读**：

| 位置 | 说哪一层 |
|---|---|
| 本目录（11 份） | **契约**：某个 tab 的端点怎么调、必填什么、报什么错 |
| `core/facts/udc/setting/<tab>/` | **事实格**：写链细节、字段组装、默认值赋值链（13 份 md） |
| `core/facts/udc/setting/operation-matrix.md` | **存在性矩阵**：update/delete/search 到底存不存在（LIVE 探测，2026-10-23） |
| `core/facts/udc/setting/precondition-appguid.md` | **前置条件**：`appGuid` 从哪来 |
| `docs/operation-contracts/udc/C-GROUP-OVERVIEW-20261018.md` | 三域交付物总览（栏目/设置/角色），含锁点 commit 与 sha |

本文**不重复**上述任何内容，只给坐标。

## 〇★、先读这一节：**「读回来是 0 / null / 空数组」有四种原因，处置正好相反**

这是设置域**最贵的一条判据**，而它现在散在四份文件里各写了一遍、互不引用。
本节只做一件事：**把同一个症状的四种原因摆在一起**，因为你手上看到的那一份只会告诉你其中一种。

| # | 症状 | 真实原因 | 处置 | 出处 |
|---|---|---|---|---|
| ① | 写成功（`BOOT_0000`），**读回字段是 0 / 子表 0 行** | **真没写进去**：REST 父级端点**不处理子集合**，静默丢弃 | **改走 GraphQL**（`attribute-set` → `udcEntityAttributePost`） | `attribute-set-contracts.md` §已推翻的 REST 尝试（4 次尝试）；`scalability-contracts.md` 同节（3 次尝试） |
| ② | `columnList` 读回来**恒为 null** | **写进去了**，但读的不是那个字段：真实列定义在 `metadataContent` / `excelHeadInfo` 两个 **JSON 字符串**里 | **换读法**，别重写。照 null 重写会把已经对的写坏 | `excel-template-contracts.md` L32 §2 |
| ③ | `udc_scalability` 表 **0 行** | **本来就没数据**：`udc_scalability_option` 有记录、`scalabilityDtoList` 为空，是合法的空方案 | **什么都不用做**。别把它当"写失败"去修 | `scalability-contracts.md` §关键对照（`dsa` 方案，2026-10-21 12:11） |
| ④ | 查询端点 `BOOT_0000` 但 `content=[]` | **授权/上下文不对**，不是"没有数据" | 先查上下文，再判空 | `expression-component-contracts.md` L43（③ 字段集 id + `ENTITY`） |

**四个症状在外部完全一样**（都是"成功码 + 空"），只看返回值分不出来。唯一可靠的分法：
**先问"这个字段/表本该有数据吗"** ——
- 本该有 → 是 ① 或 ④（写入侧或上下文）；
- 本不该有 → 是 ③（正常空）；
- 说不好 → 先按 ② 换读法（读错字段是最容易被忽略的一种，因为写侧其实成功了）。

### ① 的规模：7 次尝试，7 次都拿到成功码

`attribute-set` 4 次 + `scalability` 3 次，全部返回 `BOOT_0000` 或更上游的校验码，
**没有一次报"子集合写不进去"**。`attribute-set` 那 4 次连"先建壳再 update"这种绕法都试过：

```
① create 带 attributes（entityId 空）      → BOOT_1001 实体主键ID 不能为null
② create 自带 id + 字段 entityId 指向它    → BOOT_0000，字段读回 0（静默忽略）
③ 先建壳再 update 带 attributes            → BOOT_0000 content=1，字段读回 0
④ update 带 sourceType=APP/3/缺省          → 0000 或 1001，字段始终 0
```

⇒ 判据：**「父级写成功」不能推出「子集合写成功」**。子集合必须单独读回验证，
而且验证要读**真实落库表**（`udc_attribute` / `udc_scalability`），不是读接口回包里的 `content`。

## 一、11 份一览

按协议分组——**协议搞错是这一域最贵的错误**：拿 GraphQL 去探 REST 端点必然 `FieldUndefined`，
那是假阴性，不代表端点不存在（这类坑在 `operation-matrix.md` §一 已写成判据）。

| 文件 | 协议 | tab | 落库表 | 字节 | 行 |
|---|---|---|---|---:|---:|
| `enum-contracts.md` | GraphQL | 枚举 | `ctp_enum` / `ctp_enum_category` / `ctp_enum_item` | 4,112 | 90 |
| `option-set-contracts.md` | GraphQL | 选项集 | `udc_enum` / `udc_enum_category` / `udc_enum_item` | 3,904 | 105 |
| `custom-object-contracts.md` | GraphQL | 自定义对象 | `udc_data_transfer_object` | 5,356 | 130 |
| `serial-contracts.md` | GraphQL | 流水号 | 见正文 | 3,997 | 132 |
| `parameter-contracts.md` | GraphQL | 参数 | `ctp_parameter_definition`（`app_id` 是 varchar） | 3,322 | 110 |
| `excel-template-contracts.md` | **REST** | 导入导出模板 | 见正文 | 3,714 | 115 |
| `expression-component-contracts.md` | **REST** | 表达式组件 | 见正文 | 6,936 | 171 |
| `qrcode-contracts.md` | **REST** | 二维码 | 见正文 | 3,865 | 95 |
| `attribute-set-contracts.md` | **REST 父级 + GraphQL 子列表** | 字段集 | 见正文 | 7,855 | 173 |
| `scalability-contracts.md` | **REST 父级 + GraphQL 子列表** | 扩展实体 | 见正文 | 5,288 | 142 |
| `publish-chain.runbook.md` | 混合（含页面点击硬约束） | 发布链 runbook | — | 30,913 | 458 |

合计 **11 份 / 79,262 B**。

### 三个最容易踩的协议坑（每份文件自己都写了，这里只做导航）

1. **`attribute-set` 与 `scalability` 是半开半合**：父级 `POST /udc/attributeSet`（REST）**静默忽略**
   `attributes`；字段写入必须另走 GraphQL。只看 REST 返回 200 会以为写成功了。
   ⇒ 这个「成功码 + 空」的症状在本域有**四种成因**，处置相反，见 §〇★。
2. **`option-set` 与 `enum` 是两套独立表**，id 不互通。把枚举 id 当选项集提交，页面会显示
   `_<appName>_<id>` 异常串。
3. **`parameter` 的平台拼写错**：`udcCtpParameterDefinitonPost`（`Definition` 少一个 `i`）。
   照抄错拼写才对，改成正确拼写反而 `FieldUndefined`。

## 二、外部引用清单（改前必查）

| 被引文件 | 引用方 |
|---|---|
| `custom-object-contracts.md` | `core/facts/udc/setting/custom-object/create.md`、`tests/udc/test_setting_custom_object_asset_layout.py`（断言路径常量） |
| `enum-contracts.md` | `skills/seeyon-udc-setting/SKILL.md`（L656 契约表）、`tests/udc/test_setting_enum_asset_layout.py`（含 L95 断言「skill 必须指向本目录」） |
| `serial-contracts.md` | `core/facts/INDEX.md`、`skills/seeyon-udc-setting/SKILL.md`（L470）、`tests/udc/test_setting_excel_qrcode.py` |
| `qrcode-contracts.md` | `core/facts/INDEX.md`、`tests/udc/test_setting_excel_qrcode.py`、`tools/core/setting/qrcode_rule_seed.py` |
| `attribute-set-contracts.md` | `core/facts/INDEX.md`、`core/facts/udc/setting/attribute-set/default-value-chain.md` |
| `scalability-contracts.md` | `core/facts/INDEX.md` |
| `publish-chain.runbook.md` | `docs/operation-contracts/udc/C-GROUP-OVERVIEW-20261018.md`（锁点表）、`docs/operation-contracts/udc/role/write-chain.contract.md` |
| 无外部引用 | `excel-template-contracts.md`、`expression-component-contracts.md`、`option-set-contracts.md`、`parameter-contracts.md` |

**零外部引用的 4 份不是垃圾**：它们是各自 tab 唯一的成文契约，facts 侧只写「实际长什么样」，
不写「端点叫什么、必填什么、报什么错」。`option-set` 与 `enum` 的「两套独立表」辨析、
`parameter` 的错拼写、`expression-component` 的 `schema` 三种语义，全仓只在这几份里。

## 三、与 facts 侧的对应关系

| 本目录契约 | facts 侧事实格 |
|---|---|
| `attribute-set-contracts.md` | `core/facts/udc/setting/attribute-set/{create,default-value-chain}.md` |
| `custom-object-contracts.md` | `core/facts/udc/setting/custom-object/{create,fields}.md` |
| `enum-contracts.md` | `core/facts/udc/setting/enum/{create,enum-write-chain}.md` |
| `excel-template-contracts.md` | `core/facts/udc/setting/excel-template/create.md` |
| `expression-component-contracts.md` | `core/facts/udc/setting/expression-component/component.md` |
| `option-set-contracts.md` | `core/facts/udc/setting/option-set/create.md` |
| `parameter-contracts.md` | `core/facts/udc/setting/parameter/create.md` |
| `qrcode-contracts.md` | `core/facts/udc/setting/qrcode/create.md` |
| `scalability-contracts.md` | `core/facts/udc/setting/scalability/create.md` |
| `serial-contracts.md` | `core/facts/udc/setting/serial/create.md` |
| `publish-chain.runbook.md` | 无对应格（runbook 是操作步骤，不是事实） |

`enum` 是唯一有两份 facts 的 tab（`create.md` 讲写链、`enum-write-chain.md` 讲坑），
两者关系已在各自正文互相说明，不需要合并。

## 四、不要做的事

- **不要**把 `enum` 与 `option-set` 合并成一份「枚举类」契约：两套表、两套端点、两套 id 空间，
  合并会直接制造错误。
- **不要**把 REST 三份（`excel-template` / `expression-component` / `qrcode`）改写成 GraphQL 形态：
  平台就是 REST，改写等于造假。
- **不要**搬动 `publish-chain.runbook.md`（458 行）：`C-GROUP-OVERVIEW` 的锁点表按路径 +
  sha256 登记它，搬了就断链。
- **不要**在本目录新建"第 12 份 tab 契约"同名文件：tab 全集就是这 11 个，
  新增 tab 要先在 facts 侧落格。

---

维护：新增 tab = facts 侧落格 → 本目录加契约 → §一 加一行 → §二/§三 补对应关系 → 更新上方合计字节数。

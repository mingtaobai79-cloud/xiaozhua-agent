# udc.enum｜枚举域写链事实格（分组 / 枚举 / 枚举项 / 删除 / 查询）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> **状态：LIVE PASS**（2026-10-20 三段写入链全通 + DB 回读 + 设计器 UI 抓包交叉证实）
> 目标环境：test2，`datamigration9000000000000000001`
> 验证方式：xiaozhua-agent 自身能力（`build_*` → `validate_*` → 提交 → DB 回读）
> 详细请求体、报错字典、踩坑清单见 **`core/facts/udc/setting/enum/enum-write-chain.md`**（本文件是事实格摘要）

## R-E1 Capability

| 能力 | 端点 | 方法 | 状态 |
|---|---|---|---|
| 分组新建 | `/service/udc/graphql?udcEnumCategoryPost` | POST | LIVE PASS |
| 枚举新建 | `/service/udc/graphql?udcEnumPost` | POST | LIVE PASS |
| 枚举项新建 | `/service/udc/graphql?udcEnumItemPost` | POST | LIVE PASS |
| 枚举批量删除 | `/service/udc/graphql?udcEnumBatchDeletePost` | POST | LIVE PASS（逻辑删除） |
| 枚举列表 | `udcEnumSearchNoPagePost` | POST | LIVE PASS |
| 分组列表 | `udcEnumCategorySearch` | POST | LIVE PASS |
| 排序号计算 | `udcEnumCalcOrderNumPost` | POST | LIVE PASS |

**入口路径**：应用设计 → 设置 → 枚举（分组是枚举树上的父节点，`categoryId` 指向分组 id）。

## R-E2 Version

- 平台 `udc-web` 5.3.517（`UdcEnumController` / `UdcEnumCategoryController` / `UdcEnumItemController`）
- 网关 `https://lowcode-test2.example.com`
- 写面全部走 **GraphQL**（`/service/udc/graphql?<operationName>`），**不是** REST 控制器路径

## R-E3 Input（三段 body 的必填槽位）

```
分组    name(i18n JSON) / orderNo / appGuid / appId / hostAppName / dataStatus
枚举    name(i18n JSON) / code / orderNo / categoryId / appGuid / appId /
        hostAppName / dataStatus / bizType / expansible / enable / enumType / children
枚举项  appId / enumId / enumCode / name(i18n JSON) / itemValue / parentId /
        itemLevel / leaf / enable / orderNo / appGuid / hostAppName / dataStatus
```

⚠ 枚举项必须**同时**给 `enumId` 与 `enumCode`；顶层项 `parentId="0"`。

## R-E4 Required（服务端错误字典实测坐实）

| 缺失/非法 | 平台报错 | code |
|---|---|---|
| `orderNo` 缺 | 排序号不能为空 | `BOOT_1001` |
| 枚举 `name` 传裸文本 | 枚举编码 不能为空（实缺 name 的 i18n 形态） | `BOOT_1001` |
| 枚举项 `itemValue` 缺 | 枚举项编码 不能为空 | `BOOT_1001` |
| 枚举项 `parentId` 缺 | 上级枚举项ID 不能为null | `BOOT_1001` |
| 枚举项 `enumCode` 缺 | 所属枚举ID 不能为 null | `BOOT_1001` |
| 枚举项 `enumId` 缺 | 所属枚举编码 不能为空 | `BOOT_1001` |
| 枚举项 `name` 非大写+下划线 | `UDC_ENUM_0002`（**报错说 code，实际校验 name**） | `BOOT_1001` |
| 旧写法 `code` 传字符串 | `BOOT_3002` to type Int | `BOOT_3002` |
| 分组名重复 | 枚举分类名称重复 | `ENUM_3009` |

## R-E5 Execution

```python
# 分组
body = build_enum_category_body(app_id, name="验收分组", order_no=1)
body.update(appGuid=APP_GUID, hostAppName=None, dataStatus=False)
assert validate_enum_category_body(body) == []
POST /service/udc/graphql?udcEnumCategoryPost

# 枚举
body = build_enum_body(app_id, caption="验收枚举", name="zxjAcceptEnum",
                       order_no=10, category_id=GROUP_ID, app_guid=APP_GUID)
assert validate_enum_body(body) == []
POST /service/udc/graphql?udcEnumPost

# 枚举项
body = build_enum_item_body(app_id, enum_id, caption="待处理",
                            item_value="1", enum_code="zxjAcceptEnum", order_no=10)
assert validate_enum_item_body(body) == []
POST /service/udc/graphql?udcEnumItemPost
```

**代码落点**：
- 构造器 `components/construction/metadata_artifacts.py`：`build_enum_body` / `build_enum_category_body` / `build_enum_item_body`
- 校验器 `components/udc/setting/enum_constraints.py`：`validate_enum_body` / `validate_enum_category_body` / `validate_enum_item_body`
- 宿主入口 `xiaozhua_host_bootstrap.py`：`enum_body` / `enum_category_body` / `enum_item_body`

## R-E6 Side Effects + 回滚

| 动作 | 副作用 | 回滚 |
|---|---|---|
| 分组新建 | `ctp_enum_category` 增 1 行 | 无平台删除端点；需人工或直接 `is_delete` |
| 枚举新建 | `ctp_enum` 增 1 行 | `udcEnumBatchDeletePost`（逻辑删除） |
| 枚举项新建 | `ctp_enum_item` 增 N 行 | 同上（按 enumId） |
| 枚举删除 | `ctp_enum.is_delete = 1`（**逻辑删除**，物理行仍在） | 置 `is_delete=0` |

⚠ **删除前必须做引用分析**（实体属性 `udc_attribute.data_type='CTPENUM'`、微流程/页面/规则 schema）。
有引用就删不得——删了会让属性/流程悬空，表现为后端代码生成编译失败。

## R-E7 Known Constraints

1. **表名易混**：分组落 `ctp_enum_category`（**不是** `udc_enum_category`）；枚举落 `ctp_enum`（**不是** `udc_enum`）。查错表会误判「没落库」。
2. **删除接口偶发误报**：`BOOT_4000 数据库错误` 但数据实际已 `is_delete=1`。回读确认，**不要重发**。
3. **输入法拼音中间态**：CDP 填中文用「`set('')`→`set(v)`」两步法会提交拼音串（实测 `zxjUiTraceEnum` → `UIguijimeiju`），平台**不报错**直接落库。编码框只填英文/数字；落库后回读 `ctp_enum.code` 核对。
4. **`appGuid` ≠ `appId`**：`appGuid` 取自 `udc_application.guid`。
5. **逻辑删除**：回读统计必须 `is_delete=0` 过滤。

## R-E8 Evidence（逐条实测，禁转述）

- 分组：id `6958645714436004610`，`ctp_enum_category` 落库确认
- 枚举：id `-1052013552430069963`，`ctp_enum.category_id` 正确指向分组
- 枚举项：2 条 BOOT_0000，`ctp_enum_item` 回读 `item_value=1/2`、`parent_id=0`、`item_level=1`、`leaf=1`、`is_delete=0`
- 请求体：设计器真实 UI 抓包（rea `capture_browser_scenario`）原文与构造器产出**逐字段同构**
- 引用分析：本应用 372 枚举 → 删 363（`is_delete=1`）、保留 9（有微流程/实体引用）

## R-E9 Verified

| 项 | 等级 | 备注 |
|---|---|---|
| 分组新建 | LIVE | BOOT_0000 + DB 回读 |
| 枚举新建 | LIVE | BOOT_0000 + DB 回读 + 抓包交叉 |
| 枚举项新建 | LIVE | BOOT_0000 + DB 回读 |
| 枚举删除 | LIVE | 逻辑删除，363 条批量验证 |
| 引用分析（实体/微流程） | LIVE | DB 扫描 |
| 引用分析（页面/资源/导出模板） | **LIVE** | 载体已精确定位（udc_page_schema + ctpEnumInfo 块），阳性 6/6 阴性 0/2 |
| 引用分析（规则） | **UNVERIFIED** | 规则表 schema 字段未逐一定位（扣减/生单规则未纳入本轮载体清单） |
| 分组删除 | **VACUUM** | 平台未见对应端点 |
| 枚举项删除 | **UNVERIFIED** | 未单独验证（走枚举批量删除推定） |

## 待删除清单（清理时处理）

本域的删除动作分两类：**已完成的**（有回读证据）与**待处理的**（需授权）。
两者必须分开记，不许混在「已完成」里。

| 对象 | 判定依据 | 处置 | 状态 |
|---|---|---|---|
| 本应用 363 个无引用枚举 | 引用分析（实体/微流程/页面/资源/导出模板）无活引用 + 用户授权 | 逻辑删除（`is_delete=1`），物理行保留 | **DONE**（2026-10-20，已回读确认 `is_delete=1`） |
| 10 个仅死引用枚举（`bool` / `business_type` / `kuangjialeixing` 等） | 引用方 `udc_resource` 已 `is_deleted=1` | 可删，但需用户确认 | **PENDING** |
| `XzhCtpEnum953322`（小爪平台枚举） | 仅被「小爪实验实体950795V2」引用；该实体删除后本枚举即无引用 | 待随该实体一并处理 | **PENDING**（绑定实体删除） |
| 「小爪实验实体950795V2」实体 + 其 2 个事件 | 导致 12:24 构建失败（`domain.message.xzhexp950795` 包缺失） | 删除实体后其枚举引用自动解除 | **PENDING**（需用户授权） |

### 遗留的实验残留（用户 2026-10-20 已手工清理大部分）

以下为清理过程中确认存在过的实验对象，供后续核对是否清干净：

```
枚举      zxjAcceptEnum / UIguijimeiju / zxjE2eEnum / zxjE2eEnum2
分组      验收分组2026 / 验收分组B / 1 / 验收分组E2E / 验收分组E2E二
实体      zxjVerifyEntity
微流程    zxjVerifyFlow / zxjStdFlow
```

⚠ `UIguijimeiju` 是输入法拼音中间态误产物（想填 `zxjUiTraceEnum`），**不是有意命名的对象**。
若看到它，说明自动化填表方式需要修正（见 enum-write-chain.md §7）。

## 状态标注纪律

本域的每个能力都必须落到上面三档之一，**不许写"已打通"这种混合表述**。

正确写法：

```
枚举新建/枚举项新建 = LIVE PASS
分组删除 = VACUUM（平台无该端点）
规则引用分析 = UNVERIFIED（扣减/生单规则未纳入载体清单）
引用分析（页面）= LIVE（载体 udc_page_schema + ctpEnumInfo 块）
```

错误写法：

```
❌ "枚举域已打通"          ← 混了 LIVE 与 UNVERIFIED
❌ "页面引用分析已完成"      ← 实际是载体查错表，结论作废
❌ "已删除 363 个枚举"       ← 未说明逻辑删除、未说明先做了引用分析
```

# 栏目域枚举双源映射（接口字符串 ↔ DB 数字）

> 切片：C1（HANDOFF-C1）｜ 生成时间：2026-10-18 +08
> 规则：**每个枚举项都必须双源标注**（接口侧 LIVE / STATIC，DB 侧 LIVE / STATIC）。两源不一致 → 标 `DISCREPANCY`，**双列并存，禁静默取一**。
> 主键形态差异是本域最大的坑之一：**接口用字符串枚举名**（`"GROUP"`/`"PC"`），**DB 用 smallint 数字**（`0`/`1`）。写 SQL 与判读响应时必须分开处理。

---

## 0. 四组枚举总览

| 枚举（Java 类） | 出现字段 | 接口形态 | DB 列 | DB 形态 | 一致性 |
|---|---|---|---|---|---|
| `PortletTypeEnum` | 请求 `type` / 响应 `type` / 树节点 `type` | 字符串 `GROUP`/`PORTLET` | `udc_portlet.type` | smallint `0`/`1` | ✅ 一致（可双向映射） |
| `TerminalTypeEnum` | 请求 `terminalType`/`curTerminalType`、响应 `terminalType`、`pageItems[].urlType`、`udc_page_info.url_type` | 字符串 `ALL`/`PC`/`MOBILE` | `udc_portlet.terminal_type`、`udc_page_info.url_type` | smallint `0`/`1`/`2` | ✅ 一致 |
| `PortletCategoryEnum` | 树节点 `category`、DB `category` | 字符串 `BASIC`/`ADVANCED`/`HAND_WRITTEN` | `udc_portlet.category` | smallint `0`/`1`/`13` | ⚠️ 部分项无 LIVE（见 §3 DISCREPANCY） |
| `publishState`（`DesignStateEnum` 系） | 响应/树 `publishState`、DB `publish_state` | 字符串 `UNPUBLISH`/… | `udc_portlet.publish_state` | smallint `0`/`1` | ⚠️ **数值方向存在 DISCREPANCY**（见 §4） |

---

## 1. `PortletTypeEnum`（type）

### 1.1 双源映射表

| 接口字符串 | DB 数值 | 语义 | 接口侧来源 | DB 侧来源 | 一致 |
|---|---|---|---|---|---|
| `GROUP` | `0` | 栏目分组（根层容器） | LIVE `raw/s2r1_group_create.json` 请求/响应 | LIVE `udc_portlet.type=0`（建分组后回读）+ STATIC bytecode | ✅ |
| `PORTLET` | `1` | 栏目本体 | LIVE `raw/s2r1_portlet_create.json` 请求/响应 | LIVE `udc_portlet.type=1` + STATIC bytecode | ✅ |

### 1.2 STATIC 依据（字节码常量池顺序）

`static-s2-endpoint-map-20261017.txt` §枚举码：
```
--- com.seeyon.udc.page.enums.PortletTypeEnum ---
4: ldc #8  // String GROUP    6: iconst_0   7: iconst_0
18: ldc #11 // String PORTLET 20: iconst_1  21: iconst_1
```
→ 枚举声明顺序 `GROUP(ordinal 0, value 0)`、`PORTLET(ordinal 1, value 1)`。

### 1.3 使用注意（LIVE）

- **请求体只接受字符串**（`"type":"GROUP"`），传数字会被拒（本域未实测拒绝形态，登记为「形态约定」）。
- **DB 只存数字**，写 SQL 传 `"GROUP"` 会因类型不匹配静默 0 行或报错。
- 树节点判别键：`type=="GROUP"` 表示有 `portletList` 的容器层；`type=="PORTLET"` 才是栏目本体。

---

## 2. `TerminalTypeEnum`（terminalType / curTerminalType / urlType）

### 2.1 双源映射表

| 接口字符串 | DB 数值 | 语义 | 接口侧来源 | DB 侧来源 | 一致 |
|---|---|---|---|---|---|
| `ALL` | `0` | 全部端 | STATIC bytecode；LIVE 见 S1 复放样例 `"terminalType":"ALL"`（应用 3289082814923688017） | LIVE `terminal_type=0` 全库 6 行 | ✅ |
| `PC` | `1` | Web 端 | LIVE `raw/s2r1_group_create.json`（`"terminalType":"PC"`）/ `raw/s2r1_portlet_create.json`（`"curTerminalType":"PC"`、`pageItems[].urlType="PC"`） | LIVE `terminal_type=1`（145 行）；`udc_page_info.url_type=1`（125 行） | ✅ |
| `MOBILE` | `2` | 移动端 | STATIC bytecode；LIVE 副作用面见 `udc_page_info.url_type=2`（11 行，历史数据） | LIVE `terminal_type=2` 全库 6 行；`url_type=2` 11 行 | ✅ |

### 2.2 STATIC 依据

```
--- com.seeyon.udc.common.enums.TerminalTypeEnum ---
4: ldc #9  // String ALL    6: iconst_0   7: iconst_0
20: ldc #13 // String PC    22: iconst_1  23: iconst_1
36: ldc #15 // String MOBILE 38: iconst_2 39: iconst_2
```

### 2.3 关键判读规则（LIVE，来自 S2 实操）

1. **`terminal_type` 不是单一用户选择**：`pageItems` 条数 > 1 时，服务端把类型推导为 `ALL(0)`（STATIC `S2-WRITE-CHAIN-STATIC-20261017.md` L130 `if (pageItems.size() > 1) tmt = TerminalTypeEnum.ALL`）。
2. **本域 S2 实测**：只勾 PC（`pageItems` 1 条）→ `terminal_type=1`、`udc_page_info` 只 1 行（`url_type=1`）。→ `page_info` 增量 = 勾选端数，本域 **+1** 非 +2。
3. **表单默认只勾 PC**：`raw/s2r1_portlet_form.json` → `PC=checked true / MOBILE=checked false`。
4. **同一字段在三个位置复用同一枚举**：`udc_portlet.terminal_type`（端类型）、`udc_page_info.url_type`（页面端）、`pageItems[].urlType`（请求端），**数值语义完全一致**，可交叉断言。

---

## 3. `PortletCategoryEnum`（category）

### 3.1 双源映射表

| 接口字符串 | DB 数值 | 语义 | 接口侧来源 | DB 侧来源 | 一致 |
|---|---|---|---|---|---|
| `BASIC` | `0` | 基础 | STATIC bytecode（常量池有 `BASIC`） | **无 LIVE**（全库 `category` 只有 1） | ⚠️ DISCREPANCY-1 |
| `ADVANCED` | `1` | 高级 | LIVE 树节点 `"category":"ADVANCED"`（`raw/s2r1_portlet_create.json` L32 段、`raw/s2r1_delete_portlet.json` L21 段） | LIVE `udc_portlet.category=1`（**全库 157/157 全为 1**） | ✅ |
| `HAND_WRITTEN` | `13` | 手写 | STATIC bytecode（`bipush 13`） | **无 LIVE**（全库无 13） | ⚠️ DISCREPANCY-1 |

### 3.2 STATIC 依据

```
--- com.seeyon.udc.page.enums.PortletCategoryEnum ---
4: ldc #8  // String BASIC        6: iconst_0   7: iconst_0
18: ldc #11 // String ADVANCED    20: iconst_1  21: iconst_1
32: ldc #13 // String HAND_WRITTEN 34: iconst_2 35: bipush 13
```
→ **注意 ordinal 与 value 不等**：`HAND_WRITTEN` 的 **ordinal=2 但 value=13**。任何「按 ordinal 映射数字」的写法都会错。这是本枚举最大的坑。

### 3.3 DISCREPANCY-1 登记（LIVE 覆盖不足，非两源冲突）

| 项 | 状态 | 处理 |
|---|---|---|
| `BASIC` / `HAND_WRITTEN` | 接口侧只有 STATIC（字节码常量池），**从未在 LIVE 响应中观察到** | 标 `STATIC-only`，**不得写成「LIVE 可用」** |
| DB 侧 `category=0` / `category=13` | 全库 **0 行** | 标「LIVE 未覆盖」 |
| `ADVANCED=1` | 接口 LIVE + DB LIVE 双源一致 | ✅ 可信 |

→ 结论：`category` 目前只有 `ADVANCED↔1` 一条双源可信映射；另两项**只登记不承诺**，需在有 BASIC/HAND_WRITTEN 实例的环境复测后才能升格。

### 3.4 观察（LIVE，不写为规则）

- 创建响应**不返回** `category`（两个 create op 的 content 均无该字段）；只有 `udcPortletSelectByAppIdAppGet` 返回。
- 全库 `category` 恒 1（157/157），包括历史数据 → 平台当前实现可能只写 ADVANCED。**这是观察，不作为契约断言**。

---

## 4. `publishState`（publish_state）

### 4.1 双源映射表

| 接口字符串 | 接口侧来源 | DB 数值 | DB 侧来源 | 一致 |
|---|---|---|---|---|
| `UNPUBLISH` | LIVE 树节点 `"publishState":"UNPUBLISH"`（`raw/s2r1_portlet_create.json` L32 段、`raw/s2r1_delete_portlet.json` L21 段、S1 复放样例） | 落库 `publish_state=1` | LIVE `udc_test2.udc_portlet` **157/157 = 1**（**仅租户库**；设计库 `udc` 为 131/133，另有 2 行 = 0） | ⚠️ **DISCREPANCY-2** |
| （未观测字符串） | — | `0` | `udc_test2` 0 行；**设计库 `udc` 有 2 行**（`type=0` 默认分组，id `1408543682968314403` / `3230368806375263258`） | 局部覆盖（非本租户链路） |

### 4.2 DISCREPANCY-2 详述（**方向声明缺失，必须双列并存**）

> **2026-10-18 订正（main C1 裁定追加更正 + 本节独立复测）**：本表初稿把「`1 = 已发布 / 0 = 未发布`」记为 **DB 列注释**，
> 经本轮 `information_schema` 实查**该注释不存在**（详见下方「DB 实文复测」）。该行来源已降级为
> **「S1 产物转述（未经 information_schema 证实）」**。方向冲突由「两源互斥」降级为「**DB 侧无方向声明**」，
> 但「禁跨源换算、双列并存」结论不变（因为方向仍然未知，不是已知）。

| 源 | 断言 | 依据 | 强度 |
|---|---|---|---|
| **S1 产物转述** | `1 = 已发布 / 0 = 未发布` | `ROUTE-S1-nav-capture.md` L117 字段对照表；同文件 L122 自述「字段对照属结构对齐…DB 列注释一一吻合」 | ⚠️ **转述，非 DB 实文**（已复测证伪） |
| **DB 实文（本条为负证据）** | `publish_state` 列注释**仅「发布状态」四字，无任何方向声明** | `information_schema.COLUMNS`：全库 **241 个** `publish_state` 列 / **69 个** schema，`COLUMN_COMMENT` 分布 = `{发布状态: 241}`，**非「发布状态」者 0 条** | `LIVE`（2026-10-18 本节直查） |
| **接口 LIVE** | 未发布对象返回 `publishState="UNPUBLISH"` | `raw/*` 三处树节点 + S1 复放 | `LIVE` |
| **DB LIVE（租户库）** | `udc_test2.udc_portlet` **157/157 = 1**，含 S2 新建的 UNPUBLISH 对象 | S2 建删链回读 | `LIVE` |
| **DB LIVE（设计库）** | `udc.udc_portlet` 133 行中 **2 行为 0**（均为 `type=0` 默认分组，2024-12-19 / 2025-12-18 系统创建），其余 131 行 = 1；`udc_uat` 12/12 = 1 | `information_schema` 同一次连接实查 | `LIVE`（**新发现**） |

→ **三种自洽解释的现状（按现有证据重排）**：
1. ~~若注释正确（1=已发布），则「UNPUBLISH 的对象 publish_state=1」矛盾~~ —— **前提被证伪**：DB 侧没有「1=已发布」这条注释，此解释无源可依；
2. 若 `1=未发布`，则 udc_test2 全库 157 行都是未发布（可能，但无 LIVE 反证）；**且设计库 `udc` 存在 2 行 =0**，说明该列**确实会取 0**，`0/1` 两值都是活的，不能当常量 1 处理；
3. **更可能**：`publish_state` 与接口 `publishState` **不是同一语义的两个表示**（设计态发布标记 vs 运行时/门户发布态），或二者由**不同发布流程**写入（`udc_test2` 仅走「设计器保存」路径，`udc` 的 0 值行是系统初始化默认分组，可能未走发布流程）。**现有证据无法排除 3，也无法确证 2。**

**本轮处理（按 HANDOFF 硬约束：禁静默取一）**：
- 表格双列并存，标 `DISCREPANCY-2`，**并显式标注 DB 侧「无方向声明」**（负证据也是证据）；
- **不写任何「publishState 映射规则」结论**；
- 判读时**只认接口字符串**（`UNPUBLISH`）或**只认 DB 数字**（`0`/`1`），**不得跨源换算**；
- **SQL 侧不得写 `publish_state = 1` 当「未发布」或「已发布」的等价条件**（此前「全库恒 1」的说法已按租户库限定）；
- 升级路径：需在有「已发布」与「未发布」成对实例的环境做双源对比。**候选样本已定位**：`udc.udc_portlet` 两行 `publish_state=0`（id `1408543682968314403` / `3230368806375263258`，均为默认分组），但它们在**设计库 `udc`**、非 `udc_test2` 租户链路，能否用于双源对比需 C4 判断。**留 C4 切片**（错误/边界形态）。

**本轮处理（按 HANDOFF 硬约束：禁静默取一）**：
- 表格双列并存，标 `DISCREPANCY-2`；
- **不写任何「publishState 映射规则」结论**；
- 判读时**只认接口字符串**（`UNPUBLISH`）或**只认 DB 数字**（`1`），**不得跨源换算**；
- 升级路径：需在有「已发布」实例的环境（页面点发布后）取一次双源对比，方可将该映射升格。**留 C4 切片**（错误/边界形态）。

### 4.3 已确认可用的单源事实

| 事实 | 来源 |
|---|---|
| **本租户库** `udc_test2` 新建对象（分组/栏目）落库 `publish_state` 恒为 `1`（157/157） | LIVE DB（S2 建删链 + 全表分布） |
| `publish_state` 列**可取 0**（证明 0/1 都是活值，非恒 1） | LIVE DB：`udc.udc_portlet` 2 行 = 0 |
| `publish_state` 列注释**无方向声明**（全库 241 列统一「发布状态」） | LIVE `information_schema`（2026-10-18 直查） |
| 树接口返回 `publishState="UNPUBLISH"` | LIVE 接口 |
| 创建响应内 `publishState` 为 `null` | LIVE（两个 create op） |
| 创建响应**不写** `publish_state`，由服务端默认值填 | LIVE（响应 null vs DB 1，反向印证） |

---

## 5. 跨枚举共性规则（写 SQL 与判读时必须遵守）

| # | 规则 | 依据 |
|---|---|---|
| 1 | 接口传**字符串枚举名**，DB 存 **smallint 数值**；两层不可混用 | 全 op LIVE |
| 2 | `PortletCategoryEnum` 的 **ordinal ≠ value**（HAND_WRITTEN 2→13），禁用 ordinal 换算 | STATIC bytecode |
| 3 | `terminal_type` 由 `pageItems` 条数推导（>1 → ALL=0），非用户直选 | STATIC L130 + LIVE（+1 端 = 1） |
| 4 | 创建响应 `orderNo` 恒 0、`guid` null、`publishState` null —— **三者都不可作断言依据**，须回读 | LIVE（Q6 + §1.2/§2.2 DISCREPANCY） |
| 5 | `publishState` ↔ `publish_state` **方向未知**（DB 列注释无方向声明，S1 转述已证伪），**禁止跨源换算**；SQL 不得把 `publish_state=1` 当已发布或未发布的等价条件 | 本文件 §4.2 |
| 6 | `category` 只有 `ADVANCED=1` 双源可信；`BASIC`/`HAND_WRITTEN` 仅 STATIC | 本文件 §3.3 |
| 7 | 门户侧 `portal_portlet_category` 无独立枚举列，其 `category_type`（0=注册分类）与 `data_status`（0=设计态）是**另一套**编号，不得与本文件的 `PortletCategoryEnum` 混用 | LIVE DB（`portal_test2.portal_portlet_category` 建分组行 `category_type=0, data_status=0`） |

---

## 6. DISCREPANCY 汇总（供后续切片与 auditor 复核）

| 编号 | 项 | 冲突内容 | 处理 | 升级条件 |
|---|---|---|---|---|
| `DISCREPANCY-1` | `PortletCategoryEnum` BASIC/HAND_WRITTEN | 仅 STATIC 有，LIVE 零覆盖 | 登记不承诺 | 找到含 `category` ≠ 1 的环境实例 |
| `DISCREPANCY-2` | `publishState` ↔ `publish_state` | ① S1 L117 转述「1=已发布」**已被 information_schema 证伪**（DB 侧无方向声明）；② 接口 `UNPUBLISH` 对象在 `udc_test2` 落库 =1；③ 设计库 `udc` 存在 0 值行 → 方向仍未知 | 双列并存 + 标注「DB 无方向声明」，禁跨源换算 | 有已发布/未发布成对实例的双源对比（C4）；候选 0 值样本已在 `udc` 定位 |
| `DISCREPANCY-3`（响应 vs DB 的一般形态） | 创建响应 `orderNo=0` / `guid=null` / `publishState=null` | 响应不反映落库 | 只作回显，断言回读 | — 已定论（Q6） |

---

## 7. 复现命令

```bash
cd <HERMES_HOME>/skills/seeyon/01-platform/seeyon-low-code-environment/scripts
# type 分布
python conn.py db "SELECT type, COUNT(*) c FROM udc_test2.udc_portlet GROUP BY type" --db=udc_test2 --env=test2
# terminal_type 分布（0=ALL 6 / 1=PC 145 / 2=MOBILE 6）
python conn.py db "SELECT terminal_type, COUNT(*) c FROM udc_test2.udc_portlet GROUP BY terminal_type" --db=udc_test2 --env=test2
# category 分布（全 1）
python conn.py db "SELECT category, COUNT(*) c FROM udc_test2.udc_portlet GROUP BY category" --db=udc_test2 --env=test2
# publish_state 分布（udc_test2 全 1；注意设计库 udc 有 2 行 = 0，见 §4.2）
python conn.py db "SELECT publish_state, COUNT(*) c FROM udc_test2.udc_portlet GROUP BY publish_state" --db=udc_test2 --env=test2

# ★ DISCREPANCY-2 的负证据复现（auditor 可直接跑，只读）
# 全库 publish_state 列注释分布 —— 预期只有「发布状态」一种，含方向声明者 0 条
python conn.py db "SELECT COLUMN_COMMENT, COUNT(*) c FROM information_schema.COLUMNS WHERE COLUMN_NAME='publish_state' GROUP BY COLUMN_COMMENT" --env=test2
# 含方向声明的列数 —— 预期 0
python conn.py db "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE COLUMN_NAME='publish_state' AND (COLUMN_COMMENT LIKE '%已发布%' OR COLUMN_COMMENT LIKE '%未发布%' OR COLUMN_COMMENT LIKE '%1=%' OR COLUMN_COMMENT LIKE '%0=%')" --env=test2
# 设计库 0 值行（C4 候选样本）—— 预期 2 行，均 type=0
python conn.py db "SELECT id, app_id, name, type, publish_state, create_time FROM udc.udc_portlet WHERE publish_state=0" --db=udc --env=test2
# page_info url_type 分布（1=125 / 2=11）
python conn.py db "SELECT url_type, COUNT(*) c FROM udc_test2.udc_page_info WHERE page_type='PORTLET' GROUP BY url_type" --db=udc_test2 --env=test2
```

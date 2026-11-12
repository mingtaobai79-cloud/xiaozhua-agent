# UDC 栏目（Column）域·契约索引｜阶段 2（P1）C1 切片

> 角色：implementer ｜ 切片：HANDOFF-C1（`column-s2-c1-handoff-v1`）｜ 时间：2026-10-18 00:29–01:0x +08
> 目标应用：`datamigration9000000000000000001`（test2）
> **本目录性质：纯文档。全部内容来自阶段 1 已收口的在盘证据，零新抓包、零 DB 变更、零 CDP。**
> 纪律基线：`S2-create-capture.md` §六之二 证据登记纪律 + ROUTE L143 表述纪律（同源复测 ≠ 独立复验）

---

## 一、域定位结论（指针，不重复论证）

阶段 1 已收口（S2=PASS，2026-10-18 00:2x）：

**栏目 = Portlet，双写两库四表**

| 层 | schema.表 | 语义 | 关键列 |
|---|---|---|---|
| 设计态 | `udc_test2.udc_portlet` | 分组（type=0）/ 栏目本体（type=1） | `app_id` / `group_id` / `type` / `order_no` / `terminal_type` / `category` / `page_relation_id` / `template_type` |
| 设计态 | `udc_test2.udc_page_info` | 栏目页面（`page_type='PORTLET'`） | `relation_group_id`（挂到 portlet 的 page_relation_id）/ `group_id`（分组 id）/ `url_type` |
| 门户态 | `portal_test2.portal_portlet_category` | 门户侧栏目分类（分组同步而来） | `category_code`（= 分组 id）/ `parent_category_code`（非根层=应用 code） |
| 门户态 | `portal_test2.portal_portlet_definition` | 门户侧栏目定义（保存页面同步而来） | `portlet_id`（= **page_relation_id**，非 udc_portlet.id）/ `delete_flag`（软删） |

**跨 schema 硬约束**：`portal_portlet_category` / `portal_portlet_definition` **不在** `udc_test2`，`information_schema` 实测只有 `portal` / `portal_test2` / `portal_uat` 三个 schema 有该表族。写 SQL 不限定 schema 必报 `1146`。

**权威证据件**
- 阶段 1 全链取证：`docs/audit/column-discovery/ROUTE-S2-create-capture.md` + `raw/`（7 件）
- 导航/首屏调用链：`docs/audit/column-discovery/ROUTE-S1-nav-capture.md`
- 静态字节码/实体映射：`docs/audit/column-discovery/S2-WRITE-CHAIN-STATIC-20261017.md`、`static-s2-endpoint-map-20261017.txt`
- 裁定汇总：`main/S2-RULING-20261017.md`、`main/S2-VERDICT-RULING-20261017.md`、ROUTE「S2 LIVE 事实更正」段

---

## 二、契约清单

| 文件 | 覆盖 | op 数 |
|---|---|---|
| `write-chain.contract.md` | 写链 + 读链结构化契约（6 op） | 6 |
| `enums.md` | 接口字符串 ↔ DB 数字双源映射（4 组枚举） | 4 |
| `SELF-CHECK-references-20261018.md` | §6.2 引用纪律自证报告（文件存在性 / LIVE 值回盘 / STATIC 原文 / 跨类边界） | — |

### 本目录的 UNVERIFIED 清单（明确不承诺）

| 项 | 状态 | 归属切片 |
|---|---|---|
| `22:36` 首轮提交失败真因 | `UNVERIFIED-22:36真因未定论`（请求已出网 + HTTP 200 + DB 零落行 + 响应体缺失；「下拉为空拦截」只是可能解释之一） | C4（错误/边界形态） |
| `publishState` ↔ `publish_state` 数值方向 | `DISCREPANCY-2`（**DB 列注释无方向声明**；S1 转述「1=已发布」已由 information_schema 证伪；方向未知，禁跨源换算） | C4 |
| `PortletCategoryEnum` 的 `BASIC` / `HAND_WRITTEN` | `DISCREPANCY-1`（仅 STATIC，LIVE 零覆盖） | 需新环境实例 |
| Dubbo 门户同步 RPC 契约 | 仅静态字节码 | C3 |
| `SelectByAppIdAppGet` 分页/排序/过滤参数 | 只观测到 `path.appId` | C2 |
| 重名冲突的失败形态 | 唯一键存在但未触发 | C4 |
| id 不存在时的删除失败形态 | 未观测 | C4 |

### 6 op 一览

| # | op | 类型 | GraphQL 根字段 | 触发入口 | 证据等级 |
|---|---|---|---|---|---|
| 1 | 建分组 | mutation | `udcPortletCreatePost` | 栏目列表页 folder 图标 | LIVE |
| 2 | 建栏目 | mutation | `udcPortletCreatePortletPost` | 栏目列表页 plus 图标 | LIVE |
| 3 | 删栏目 / 删分组 | mutation | `udcPortletDeleteIdPost` | 列表树 hover→more→删除 | LIVE |
| 4 | 保存并提交（触发门户定义同步） | mutation | `udcPageInfoUpdatePost` | 页面设计器「保存并提交」 | LIVE |
| 5 | 暂存草稿（不触发门户同步） | mutation | `udcPageInfoUpdateDrafPost` | 页面设计器「暂存草稿」 | LIVE |
| 6 | 读栏目树 | query | `udcPortletSelectByAppIdAppGet` | 栏目列表页首屏 | LIVE |

---

## 三、证据等级标注规则（本目录强制）

每个字段必须带下列**之一**，不得留空、不得猜测：

| 标注 | 含义 | 允许的参照物 |
|---|---|---|
| `LIVE` | 来自在盘真实抓包 / DB 实测 | `raw/*.json` 的行号或 op 名；DB 表列 + 回读值 |
| `STATIC` | 来自字节码 / 前端 bundle 反编译 | `static-s2-endpoint-map-20261017.txt` 的类名/常量池；`S2-WRITE-CHAIN-STATIC-20261017.md` 行号 |
| `DISCREPANCY` | LIVE 与 STATIC 不一致 | 必须**双列并存**，禁静默取一 |
| `INFERRED` | 由多个 LIVE 事实推出，非直接观测 | **只允许**出现在「判读」段，不得出现于 schema 字段表 |
| 无标注 | **不允许** | 无来源的字段一律不写（HANDOFF 硬约束） |

### 节级统一声明（允许形式，须登记）

当某一节的**全部行同源**时，允许在节首做一次统一声明，代替逐行重复标注。使用该形式的节必须在此登记，便于 auditor 复核：

| 节 | 统一声明 | 行数 |
|---|---|---|
| `write-chain.contract.md` §4.2 `operationLog` 子结构 | 全部 `LIVE`（`raw/s2r1_page_save_submit.json` 的 UpdatePost 请求体） | 14 |
| `write-chain.contract.md` §5.1 请求 schema（UpdateDrafPost） | 全部 `LIVE`（`raw/s2r1_page_save_submit.json` 的 UpdateDrafPost 请求体） | 6 |
| `write-chain.contract.md` §5.4 行为对照（原 §5.3，因新增 §5.2 请求样例后顺延） | 全部 `LIVE`（接口 raw 两件 + DB 建删链回读） | **4**（`isDraftPage` / `portal_portlet_definition` / op-log / 页面 schema 位） |
| `write-chain.contract.md` §5.2 请求原文样例 | 全部 `LIVE`（`raw/s2r1_page_save.json` 的 DrafPost 调用 body 原文逐字复制） | 1 个代码块 |
| `write-chain.contract.md` §1.2 / §2.2 DISCREPANCY 子表 | 响应侧 `LIVE`(raw) + DB 侧 `LIVE`(DB) 双源对照 | 6 |

不适用该形式：§附录 A（raw 文件索引，非字段表，不做来源标注）。

补充纪律（ROUTE L143）：
- 写「证实 / 确认 / 成立」时须标明主体是 **implementer LIVE 取证** / **同源复测（非独立证据链）** / **独立复验（不同证据源）**。
- 本目录所有 LIVE 标注均为 **implementer LIVE 取证**（我本人页面点击 + 抓包 + DB 回读）；auditor 的独立复验结论仅作为「一致」旁注出现。

---

## 四、本目录不覆盖的内容（避免误用）

- **门户侧 Dubbo 面（`UdcPortalPortletAppServiceImpl` / `PortalPortletAppService`）**：只有静态字节码证据，LIVE 侧仅拿到落库结果（category/definition 行），RPC 契约本身未取证 → 留给 C3 切片，本目录不写。
- **`udc_portlet_group`（栏目分类）表**：全程 0 行，与栏目分组无关，独立功能 → 本目录只登记「不参与」，不写契约。
- **错误码全集**：本目录只登记**已实际观测到**的失败形态（表单 required 机制 + BOOT_0000/SUCCESS 正常态），不做错误码穷举。**22:36 真因 `UNVERIFIED-22:36真因未定论`，不得写成「前置校验拒绝」** —— main 22:41 的该定性已正式废止（网络层确有 `requestWillBeSent` + HTTP 200，不支持纯前端拦截解释）。
- **分页/排序/过滤参数**：`udcPortletSelectByAppIdAppGet` 只观测到 `path.appId` 单参数形态 → 留 C2 切片补。

---

## 五、引用可复现路径

所有 `raw/` 引用相对于 `docs/audit/column-discovery/raw/`。
所有 `scratch/` 引用为 `<HERMES_HOME>/cache/scratch/`（**24h 自动清理**，故本目录凡引用 scratch 处均同时给出 innerText 原文，确保 scratch 过期后仍可判读）。

复现命令模板（只读）：
```bash
cd <HERMES_HOME>/skills/seeyon/01-platform/xiaozhua-low-code-environment/scripts
python conn.py db "<SQL>" --db=udc_test2 --env=test2
```

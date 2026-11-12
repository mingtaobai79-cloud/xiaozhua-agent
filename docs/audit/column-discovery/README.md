# docs/audit/column-discovery/ 入口

> 列域（栏目）**S1 导航 + S2 建删全链**的原始取证（2026-10-17 / 10-18）。
> 3 份 `.md`（61,911 B）+ 12 份 `.json`/`.txt` 原始件。
> **这里不是结论库。** 可消费的契约在 `docs/operation-contracts/udc/column/`；本目录是它的上游证据。
3 份正文共 **15 处**更正标记（S2 10 / S1 2 / 静态 3），其中 10 条列在 §一。

---

## 一★、**先读这一节：本目录有 15 处更正，而且改的是"对象是谁"**

这个域最初被判为 **VACUUM（近乎零证据）**，被判空的理由不是"没查"，而是**查错了对象名**：
按 `udc_column` / `udc_portal` 关键词扫 DB，命中 0，于是结论是"栏目域没有表"。
**真实对象是 `udc_portlet`（Portlet）**，门户侧还有两张表在**另一个 schema**。

⇒ **判据：负证据的杀伤力取决于"你查的是不是那个东西的名字"。**
   关键词 0 命中只能证明"这个词不存在"，不能证明"这个域不存在"。

### 更正表（按"会不会让人写错 SQL / 判错对象"排序）

| # | 原判断（错） | 更正为 | 代价 | 原文 |
|---|---|---|---|---|
| ① | 栏目真实对象 = `udc_column` / `udc_portal` 之类 | **`udc_portlet`**：`type=0` 分组 / `type=1` 栏目本体 | **最贵**：对象名错，后面所有 SQL、契约、写链全废 | `ROUTE-S2` L177 段、`S1` L191 |
| ② | 「无 `udc_column` / `udc_portal` 表 ⇒ 栏目域空」 | 表述**为真但结论误导**：真实表族是 `udc_portlet` + `udc_page_info(page_type='PORTLET')` + 门户侧 `portal_portlet_category` / `portal_portlet_definition` | **"表述为真、结论误导"是最难自查的一类错** —— 每个字都能复现，结论却反了 | `S1` L191、`S2` §七 L207 |
| ③ | `portal_portlet_definition.portlet_id` = `udc_portlet.id` | = **`8758458332069176381`（pageRelationId / relationGroupId）**，**不是** `udc_portlet.id` | 按旧映射写，外键全指错行（**跨表 join 会静默返回错结果**） | `S2` L171（重大映射更正） |
| ④ | 建栏目产生**两条** op-log（`PORTLET_PAGE=40` baseCreate + `PORTLET=5` create） | LIVE **未复现**：实际**一条** `sub_module=40`，内部 `log_element` 数组含 **2 个元素**；`PORTLET=5 create` 行完全未出现 | 按两条去找审计，会得出"审计缺失"的假结论 | `S2` §H4 L160 |
| ⑤ | `parent_category_code` = 字节码常量 `PARENT_CATEGORY_CODE="-1"` | 实为 **应用 code**；`-1` 只出现在 `category_path` 的**根前缀** | 会去改对的地方；`-1` 的语义是"路径根"不是"父分类值" | `S2` L137 |
| ⑥ | `udc_portlet_group` 期望 0 行 | 依据已按裁定 **I4** 更正 | — | `S2-WRITE-CHAIN-STATIC` §5.2 |
| ⑦ | H3 删除顺序原理由 | **原文已废止**，理由另立 | 照旧理由操作可能删错序 | `S2-WRITE-CHAIN-STATIC` §H3 L396 |
| ⑧ | 栏目域状态 `VACUUM（几乎零证据）` | **`PARTIAL（S1+S2 定位完成，写链 LIVE）`**；表族名一并更正 | 会重复做已完成的定位 | `S2` §七 L204–207 |
| ⑨ | `type=1` 的 `group_id` 指向 `udc_portlet_group` | 指向 **`udc_portlet` 自己的 type=0 行**（S1 强制更正交叉验证 ✅） | 分组归属查错表 | `S2` L70 |
| ⑩ | `udc_page_layout` / `udc_page_group` 可能是栏目落点 | 不是；真实落点是 `udc_portlet` + `udc_page_info(PORTLET)` | 会去查两张无关表 | `udc-nine-modules-status` §7「定位前」段 |

### 一条贯穿性的方法论（比上面 10 条都值钱）

**①②⑩ 是同一个病：拿"关键词 0 命中"当"域不存在"。**
- `udc_column` 0 命中 ⇒ 判"栏目域没有表"（真实表叫 `udc_portlet`）
- 同一个域后来用 `udc_portlet` 一扫，**四张表全在**（含跨 schema 两张）

⇒ **判据：负证据要先问"我查的名字对吗"，再问"是不是真没有"。**
   查错名字得到的 0 命中，和真没有，输出**长得一模一样**。

---

## 二、三份文件是什么关系（**不要按编号读**）

| 文件 | 角色 | 证据等级 | 何时读 |
|---|---|---|---|
| `ROUTE-S1-nav-capture.md`（198 行） | S1 **导航/首屏**调用链 LIVE 抓包 | LIVE | 想知道"点进栏目页时发生了什么" |
| `ROUTE-S2-create-capture.md`（224 行） | S2 **建/删全链** LIVE 抓包（H1–H6 六条假设逐条验） | LIVE | **主证据**。①③④⑤⑨ 都在这里，且 §六/§七 是对 ROUTE 与状态文档的更正清单 |
| `S2-WRITE-CHAIN-STATIC-20261017.md`（483 行） | 静态字节码 / 实体映射（写链的静态侧） | STATIC | 想知道"代码里应该是怎样的"；**与 LIVE 冲突时以 LIVE 为准** |

**LIVE × STATIC 的四处冲突，全部以 LIVE 改 STATIC**（③④⑤ 是其中三条）。
⇒ **判据：LIVE 推翻 STATIC 时，要改的是 STATIC 那份文档，不是把 LIVE 记成"异常"。**

## 三、原始件（`raw/` 等 12 份 JSON / TXT）

| 路径 | 内容 | 字节 |
|---|---|---|
| `raw/s2r1_portlet_create.json` | 建栏目请求/响应原文 | 106,568 |
| `raw/s2r1_page_save_submit.json` | 页面保存提交 | 129,513 |
| `raw/s2r1_page_save.json` | 页面保存 | 50,461 |
| `raw/s2r1_group_create.json` | 建分组 | 3,015 |
| `raw/s2r1_portlet_form.json` | 栏目表单 | 3,239 |
| `raw/s2r1_delete_portlet.json` / `raw/s2r1_delete_group.json` | 删栏目 / 删分组 | 2,266 / 1,918 |
| `raw-nav-capture-20261017.json` | S1 导航抓包 | 160,761 |
| `raw-db-probes-20261017.json` | DB 探针结果 | 6,287 |
| `raw-s2-write-chain-static-20261017.json` | 静态侧结构化结果 | 7,238 |
| `raw-s2-blocked-evidence-20261017.json` | 阻断项证据 | 5,336 |
| `static-s2-endpoint-map-20261017.txt` | 静态端点映射（纯文本） | 10,023 |

> 这些是**原始抓包**，含运行态业务数据（对象 id、页面内容）。
> 按 `tests/test_deidentification.py` 的 `EVIDENCE_DATA_DIRS`，`/artifacts/` 与 `/live-evidence/` 是显式豁免目录 ——
> **本目录不在豁免内**，所以文本件已核过：3 份 `.md` 对客户标识判据**零命中**（2026-11-07 复核）。
> 但 `raw/*.json` 是**原样回读**，含运行态 id，**不要外发、不要贴进文档**。

## 四、谁在用这些结论（下游入口）

| 消费方 | 用途 |
|---|---|
| `docs/operation-contracts/udc/column/README.md`（8,165 B） | 列域契约索引：域定位结论（四表双库）+ 6 op 一览 + UNVERIFIED 清单 |
| `docs/operation-contracts/udc/column/write-chain.contract.md`（90,460 B） | 写链/读链结构化契约 |
| `docs/operation-contracts/udc/column/enums.md`、`SELF-CHECK-references-20261018.md` | 枚举双源映射 / 引用纪律自证 |
| `docs/audit/udc-nine-modules-status.md` §7 | 九域状态表的「栏目」行（**已更正**，见该节顶部更正块） |

⇒ **要结论去 `operation-contracts/udc/column/`；要"怎么测出来的"回本目录。**

## 五、不要做的事

- **不要**把这里当"栏目域=VACUUM"的证据：那是查错名字得出的结论（见 §一）。
- **不要**按文件编号顺序读：`S2-WRITE-CHAIN-STATIC` 里 §H3/§5.2 有**已废止**的原文。
- **不要**把 `raw/*.json` 贴进任何文档或外发：含运行态对象 id。
- **不要**只读 STATIC 就下契约结论：本域 4 处冲突全部以 LIVE 改 STATIC。

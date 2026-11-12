# core/facts/udc/ 索引（UDC 事实层总入口）

## 这个目录是什么

**UDC 域的事实层总入口**：163 份 / **1,430,820 B**（2026-11-09 实测，不含本 README），8 个子域 + 5 份顶层文档。
回答的是「**实际长什么样**」——真实 body、真实报错、实测坑。

⚠️ **本目录此前零入口**。6 个子域（entity / expression / microflow / setting / write-chain / application）
各有自己的 `README.md`；**剩下 2 个（page / serial）没有**，靠本文件导航。
（`application/` 的入口是 2026-11-07 补的——按 §六 那条禁令自己的条件：「哪个域开始被反复查，
再给它单独入口」。实测 `application/` 被 **9** 份文档引用，`page/` 与 `serial/` 各只有 **1** 份。）

## 一、8 个子域（按字节降序）

> **口径（第 67 轮补）**：本节与下一节的「份 / 字节」一律**递归含子目录**，
> 也**含该子域自己的 `README.md`**。
> 这条必须写明，因为两种口径在本目录里**都出现过**：
> `write-chain/` 顶层只有 39 份，递归 46 份（差 7 份在 `write-chain/` 子目录里）；
> `setting/` 顶层 3 份、递归 16 份（10 个 tab 各一层）；
> `entity/` 10 → 12、`application/` 5 → 8。
> 没有子目录的域（`microflow/` `expression/` `page/` `serial/`）两种口径同值 ——
> **所以只看那几个域，永远发现不了这张表混用了口径**。

| 子域 | 份 | 字节 | 入口 | 一句话 |
|---|---:|---:|---|---|
| `microflow/` | 64 | 450,519 | ✅ | 微流程：节点契约（22 类 UI）、表达式引擎、生成链、生成闸门 |
| `write-chain/` | 46 | 407,343 | ✅ | **写面事实主库**：设计器保存协议、各类 REST 写链、检测修复工作流；`write-chain.md` 单份 51,826 B |
| `setting/` | 18 | 186,292 | ✅ | 设置域 10 个 tab 事实格 + 操作存在性矩阵 + 取 appGuid 前置 |
| `entity/` | 12 | 92,307 | ✅ | 实体：创建/属性/事件绑定/扩展实体/枚举域 |
| `application/` | 8 | 83,087 | ✅ | 应用域：前端调用面、内页、search、applog 家族、内页写链。★ 域入口 = `application/README.md`（含「LIVE 三义」与「会话目录不是死引用」两条判据） |
| `expression/` | 4 | 78,807 | ✅ | 表达式：函数目录（88 个，生成器产出勿手改）、系统变量、引擎 |
| `page/` | 4 | 79,584 | ❌ | 页面：详情页、列表页、菜单绑定；`custom-page-dev-server-glob.md` = 自定义页 dev server 只认启动时目录快照（404 / hello world 的真因）。**都在 20–30 KB**，没有一份是短的 |
| `serial/` | 2 | 32,196 | ❌ | 流水号：应用草稿、流水号配置 |

合计 **163 份 / 1,430,820 B**（不含本 README 自身；各子域行的份数与字节**含**该子域自己的 README）。

## 二、5 份顶层文档（跨域，不属于任何子域）

| 文件 | 字节 | 行 | 外部引用 | 职责 |
|---|---:|---:|---:|---|
| `metadata-storage.md` | 6,626 | 96 | 3 | 设计态元数据存储机制（九段式机制格） |
| `DOMAIN-SURVEY.md` | 5,334 | 131 | 2 | **九大域能力面盘点**——读 registry 全量 + 目录扫描得出的实际条数（application 42 / entity 28 / setting 39 / flow 13 / menu 5 / bi 5 / role 1 / **rule 0 · column 0**） |
| `frontend-assembly-protocol.md` | 4,429 | 82 | 2 | 设计器前端组装与校验协议（源码级） |
| `runtime-data-read.md` | 2,366 | 44 | 3 | 运行态表单数据查询（LIVE 2026-09-25） |
| `readonly-faces-batch2.md` | 1,930 | 21 | 2 | 运行态只读四格（serial + application.draft + role + node-tree） |

**`DOMAIN-SURVEY.md` 是本目录最该先读的一份**：它给的是「哪些域真有东西、哪些是空档」的实测，
`rule 0 · column 0` 这个结论能解释为什么 `docs/operation-contracts/udc/rule/` 只有 2 份规划文档。

## 三、★★ 微流程内容散在三处，共 1.86 MB（本层最容易走错的地方）

同名主题分布在三个目录，**互相几乎不引用**（实测交叉引用数 2 / 1 / 0 / 1）：

| 位置 | 份 | 字节 | 性质 |
|---|---:|---:|---|
| `core/facts/udc/microflow/`（**本目录下**） | 62 | 437,245 | 事实格：节点语义、生成链、闸门 |
| `docs/operation-contracts/udc/microflow/` | 25 | 277,632 | 契约层：三份大契约 + 节点普查（25 份含 `live-evidence/` 下 11 份）。⚠ `docs/operation-contracts/udc/README.md` 里同一条写 **14 份 / 250,405 B** —— 那是**顶层**口径，两个都对，差的正是 `live-evidence/` |
| `docs/audit/udc-semantics/` | 99 | 1,158,514 | 审计/取证：过程记录，含 34 份 `MICROFLOW-*.md` |

**为什么会这样**：三处不是"重复写"，是**三个阶段**的产物（取证 → 提炼成事实 → 定成契约）。
问题是**没有一条指针把它们串起来**，所以按关键词搜会命中三处、看不出该读哪份。

**读法**：
- 要「节点怎么配」→ `core/facts/udc/microflow/node-*.md`（22 类 UI 契约见 `node-ui-contracts-22.md`，23,245 B）
- 要「这个节点字段叫什么、必填什么」→ `docs/operation-contracts/udc/microflow/*.contract.md`
- 要「这个结论是怎么查出来的、有没有被推翻过」→ `docs/audit/udc-semantics/`
- **`docs/audit/udc-semantics/` 的 99 份是过程证据，不是当前结论**。判据见该目录既有文件头部的时点标注。

**不要**为了"消除重复"把三处合并或搬走：三处粒度不同（一节点 / 一契约 / 一次取证），
合并会丢掉「实测 → 提炼 → 定契约」的追溯链。这是本目录最大的结构性事实，先承认它。

## 四、与相邻目录的分工

| 目录 | 层级 | 回答 |
|---|---|---|
| `core/facts/udc/`（**本目录**） | 事实层 | 实际操作长什么样、真实 body、实测坑 |
| `docs/operation-contracts/udc/` | 契约层 | 端点叫什么、必填什么、返回什么形状 |
| `docs/audit/udc-semantics/` | 审计层 | 结论怎么来的、有没有被推翻 |
| `docs/audit/artifacts/` | 证据层 | 原始抓包 / 反编译产物 |

**同名子域陷阱**：`application/`、`entity/`、`setting/`、`microflow/` 四个名字在
本目录和 `docs/operation-contracts/udc/` 下**都存在**。**查用法来这边，查端点去那边。**
`core/facts/udc/setting/README.md` 与 `docs/operation-contracts/udc/README.md` 各有分工表。

## 五、按问题找文件

| 你要找什么 | 去哪 |
|---|---|
| 九大域各自有多少能力面、哪些是空档 | 顶层 `DOMAIN-SURVEY.md` |
| 某个写操作的完整 REST/GraphQL 写链 | `write-chain/<主题>-write-chain.md`，入口见 `write-chain/README.md`（45 行索引表，生成器维护） |
| 微流程某类节点怎么配 | `microflow/node-<类型>.md` |
| 设置域某 tab 的真实 body / 静默失败 | `setting/<tab>/create.md` |
| 实体创建/属性/扩展实体的坑 | `entity/create.md`、`entity/attribute-create.md`、`entity/scalability.md` |
| 表达式函数怎么用（88 个） | `expression/functions.md`（生成器产出，**勿手改**） |
| 页面/菜单怎么建 | `page/detail-page.md`、`page/list-page.md`、`page/menu-bind.md` |
| 应用域只读能力面 | `application/application-search.md`、`application/applog-family.md` |
| 应用草稿 / 流水号配置 | `serial/app-draft.md`、`serial/serial-config.md` |

## 六、不要做的事

- **不要**「零引用就删」：`page/detail-page.md`（25,805 B）实测**零外部引用**，但它是
  `page/` 三份之一，另两份（`list-page.md` ext=2、`menu-bind.md` ext=1）都与它同主题。
  删了会让另两份的上下文失据。**零引用 ≠ 可删**（本仓库已实证 6 次）。
- **不要**给 `page/` `serial/` 批量生成 README：两域共 5 份，本文件已覆盖导航。
  哪个域开始被人反复查，再给它单独入口（`setting/` 就是这么来的）。
  ✅ **2026-11-07：`application/` 已触发此条件并补了入口**——它从 3 份长到 7 份（含 `app-inner/`、
  `evidence/` 两个子目录、17 份证据 JSON），且被 9 份文档引用；`page/`(1) 与 `serial/`(1) 远未到这个程度。
  所以 `application/` 从本条移出，并非「违反禁令」，而是**禁令自带的条件兑现了**。
- **不要**手改 `expression/functions.md`（88 函数目录，生成器 `tools/core/expression/gen_function_catalog.py` 产出）
  和 `write-chain/README.md`（45 行索引表，生成器 `tools/core/facts/gen_write_chain_index.py` 产出）。
- **不要**把微流程三处合并（见 §三）。
- **不要**在本目录建第二份 index（`core/facts/INDEX.md` 是**全库能力面登记**，
  按「能力」而不是按「目录」组织；本文件是按目录组织的导航，两者不同层）。

---

维护：新增子域 → §一 加一行 → 更新合计；某子域补了 `README.md` → 把 §一 的 ❌ 改 ✅
（闸门测试会核对这个标记）。微流程三处的份数/字节变了 → 同步 §三 的表。
# docs/audit/role/ 索引

## 这个目录是什么

**UDC「角色」域审计的全部现场记录**：9 份，P0 → P1 → P2 → P3 → P3b → S5 一条时间链。

⚠️ **不要按文件序号当作阅读顺序。** 这条链里有**三处结论被后续文件推翻**，
按 P0→P1→P2→P3 顺序读会读到已被证伪的判断。正确读法在 §二。

消费方只有一个：`docs/operation-contracts/udc/role/write-chain.contract.md` §末尾的证据表
逐条引用这 9 份。**角色域的操作契约已收口，这 9 份是它的证据底。**

## 一、9 份一览（2026-11-07 实测）

| 文件 | 阶段 | 字节 | 行 | 一句话 |
|---|---|---:|---:|---|
| `P0-role-object-model.md` | P0 | 44,079 | 1,210 | 对象模型钉死：三表 DDL 原文（`udc_role` / `udc_role_resource` / `udc_resource`）+ 分布 |
| `P1-role-frontend-call-chain.md` | P1 | 18,687 | 257 | 设计器「角色」页接口调用链：15 端点 STATIC 全文 + DTO javap 实读 + 前端 bundle 实读 |
| `P1-LIVE-GAP-MATRIX.md` | P1 | 15,154 | 224 | 15 端点 × LIVE 佐证矩阵 + 六个写端点风险排序（只列不跑） |
| `P1-STRUCTURE-SUPPLEMENT.md` | P1 | 25,657 | 354 | 三块结构补齐：版本边界 / chunk 形态归类 / 端点↔页面元素 |
| `P1-FUNCAUTH-BRANCH-TRACE.md` | P1 | 17,256 | 337 | funcAuth 页面分支追溯：#13 vs #14 到底谁触发（两个不同弹窗） |
| `P2-role-live-readback.md` | P2 | 19,066 | 310 | LIVE 读链回读：基线重取 + 真实业务数据只读调用 |
| `P3-role-write-chain.md` | P3 | 64,604 | 954 | 写链实测（建角色 / 绑资源 / func-auth），**含 23:57 总更正** |
| `P3b-permission-panel-recheck.md` | P3b | 11,410 | 171 | 「查看权限」面板只读归因复盘（P-A 撤回 → P-A'/P-B 二分） |
| `S5-role-write-chain-closure.md` | S5 | 20,366 | 411 | 阶段5 写链收口：四次写实测 + 终态判定 |

合计 **9 份 / 236,279 B**。

## 二、三处结论推翻（**这才是读这个目录要先知道的**）

按时间链还原，每一处标注"原文在哪、更正后是什么、去哪读更正"。

### 推翻 ①｜「绑资源被 OrgAdmin 权限闸挡住」→ 不是权限闸

| | |
|---|---|
| 原判断 | 读链通、建角色通，但「绑资源」被 OrgAdmin 权限闸挡住（P3 初版 23:29） |
| 更正 | **不是权限闸**。「查看权限」面板 `permissionLook=true` 是查看模式，**结构性只读**，与权限无关 |
| 推翻依据 | main DB HEX 复核 + VERDICT-04 |
| 更正原文位置 | `P3-role-write-chain.md` 头部「23:57 总更正」块 + §2/§3/§5 就地补注 |
| 后续延续 | `P3b-permission-panel-recheck.md` 把归因拆成 P-A（撤回）/ P-B（权限位机制存在且生效）二分 |

**这是本目录最贵的一条**：错了会让人去要权限，而真正原因是面板形态。

### 推翻 ②｜`relationOrgRoleCode` 落库空串 → 正常落库

| | |
|---|---|
| 原判断 | 落库空串（P3 初版） |
| 更正 | 232441 实际正常落库 `departmentManager`，HEX 可验 |
| 更正原文位置 | `P3-role-write-chain.md` 头部同一「23:57 总更正」块 |

### 推翻 ③｜javap 的 SHA-256 能「自证来源」 → **不能**

| | |
|---|---|
| 原判断 | 用 javap 输出的 SHA-256 自证来源 |
| 更正 | **不能**。`P1-STRUCTURE-SUPPLEMENT.md` §1.0 自己纠正："先纠正我自己写的一句错话" |
| 为什么重要 | 保留原句会反复触发误判，白白消耗三方轮次 |

### 另有两处较小撤回（不是推翻结论，是撤回担心）

- `P1-FUNCAUTH-BRANCH-TRACE.md` §3：「点一次设置权限无法区分命中哪个」这个担心**已撤回**——两个触发点根本不在同一个弹窗里。
- `P3-role-write-chain.md` §1.4：**边界超额自报**——建了 2 个角色而非 1 个（自报，不是隐瞒）。

### 还有一处"作废"

`P3-role-write-chain.md` 结论表 D 行：**探针角色路径「作废」**——`ctp_role` 镜像来自应用导入，
手工建角色不产生镜像（0/3）。这条在 P3 内就地标注，无后续文件接续。

## 三、推荐读法

**要结论**：读 `S5-role-write-chain-closure.md`（终态判定）+ `docs/operation-contracts/udc/role/write-chain.contract.md`。

**要证据强度**：读 `P1-LIVE-GAP-MATRIX.md`（15 端点 × LIVE 佐证矩阵 + 补证优先级）。

**要对象模型 / DDL**：读 `P0-role-object-model.md`——**注意它有两处「语义纠正」块（2026-10-17 23:05，采纳 VERDICT-02 + P1 §5）**，
读之前先看纠正块，不要读被取代的原文判定。

**要理解"为什么当初判错了"**：读 `P3b-permission-panel-recheck.md`——这是全目录唯一的归因复盘，
P-A'/P-B 二分说明了「结构性只读」与「权限位生效」是两件事。

**只读一份**：`S5`。

## 四、不要做的事

- **不要**按 P0→P1→P2→P3 序号直线读：P3 初版的两条关键结论已被推翻，P0 也有两处语义纠正。
  每份文件头部都有更正块，**先读头部再读正文**。
- **不要**把这三处推翻"整理掉"（合并成一份干净的最终结论）：一条判断从"错"到"对"的过程
  本身就是证据——`P3b` 的 P-A/P-B 二分正是靠复盘才看清的。
- **不要**搬走任何一份：`operation-contracts/udc/role/write-chain.contract.md` §证据表按精确路径引用全部 9 份。
- **不要**在 `S5` 之上再写第 10 份"最终总结"：`S5` 就是终态，契约才是给人读的出口。

## 五、外部引用

| 引用方 | 引用方式 |
|---|---|
| `docs/operation-contracts/udc/role/write-chain.contract.md` | §证据表逐条引用全部 9 份（L709–L717），含每份的用途说明 |
| `docs/ledger/LOG-doc-consolidation-20261107-rounds1-15.md` | 提到 `P0-role-object-model.md`（作为"裸 19 位 ID 最多"的例子） |

除此之外零外部引用。**但这不是删除依据**：这 9 份是角色域契约的唯一证据底，
契约里每一行"LIVE PASS"都要靠它们复算。

---

维护：新增阶段（S6+）= 在 §一 加一行 → §二 若引入新的推翻/撤回必须登记 → 更新合计字节数 →
同步 `write-chain.contract.md` 的证据表。

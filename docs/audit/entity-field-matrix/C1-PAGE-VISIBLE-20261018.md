# C-1｜BIGINTEGER 页面可见证据｜PARTIAL（页面 LIVE，字段未取到）

时间：2026-10-18 18:22 (+08)　端口：CDP 9223（本组独占，未碰 9226/9229）
URL：`https://lowcode-test2.example.com/main/child-frame/udc/app-design/entity?appId=8704025620829192834`

## 一、已取到（LIVE，页面可见）

**页面鉴权与渲染**：Document `200`（非 302/login），`document.title` = `数据迁移`。
**实体树 DOM 文本**（`.ant-tree-title`，原样摘录）：

```
默认分组
小爪实验实体950795V2\n标准
小爪验收实体\n标准
日志专用                      ← 展开后含：
  文件上传中间表(fileMigration)\n标准
  日志方案信息(LogSchemeInformatio)\n标准
  迁移日志(MigrationLog)\n标准
数据迁移配置信息              ← 展开后含：
  数据源配置信息\n标准
  迁移方案配置\n标准
```

⇒ DB 基线 4 实体中，**3 个实体名在页面可见且带英文标识**（fileMigration / LogSchemeInformatio / MigrationLog）。
**migrationPlan 未以该名出现**（疑为「迁移方案配置」，未证实，不作结论）。

**字段表可读性自证**（证明抓取方法有效，非空抓）：选中 `小爪实验实体950795V2` 的「字段」页，读得真实字段行：

```
实验文本(已改) | expText   | 文本        | 长度：0 至 100
实验枚举字段   | expEnum   | 枚举：小爪平台枚举单选 | -
实验日期       | expDate   | 日期时间    | 日期时间：- 至 -
实验数量       | expNum    | 整数        | 整数：- 至 -
b2IntField     | b2IntField| 整数        | 整数：- 至 -
```
（字段单元格是 `<input>`，须读 `.value` 而非 `innerText`；这是本轮踩到的第一个坑。）

## 二、未取到（UNVERIFIED）

**9 条 BIGINTEGER 字段名（batchId / fileSize / processedRows / totalRows / duration / sourceDatasourceId / targetDatasourceId）在 DOM 中一条未命中。**

原因（实测，非推断）：点击目标实体后，**字段表未切换到该实体**，仍显示上一个实体的字段行。证据：
- 点击 `迁移日志(MigrationLog)` 后 `.ant-tree-treenode.selected` 为空（后续轮次才偶发成功选中）
- 字段表 `tbody tr` 数量与首行内容始终 = `小爪实验实体950795V2` 的字段（`实验文本(已改)`）
- 控制台持续抛 `NotFoundError: Failed to execute 'removeChild' on 'Node': The node to be removed is not a child of this node`（`seeyon.vendor.global.5.3.41-sdk`），异常为 `Uncaught (in promise)`，疑为表格重渲染被打断

尝试过的 9 种点击路径（均未换来字段表切换）：`itemTitle` 单击 / 双击 / `mouseMoved→mousePressed→mouseReleased`(120ms 间隔) / JS `dispatchEvent(click)` / 先展开分组 switcher / `?id=<entity_id>`（=MigrationLog 的 entity_id 1627860264017874938）直链 / 搜索框过滤后点击 / 静置 6–16s 再点 / 直接调用 React fiber 上的 `onClick`。

**最后一招的实际结果（最有诊断价值）**：从 `.ant-tree-treenode` 内 span 的 `__reactProps$…` 上取出真实 `onClick` 并调用 —— 返回 `INVOKED`（函数执行成功、无抛错），但 7 秒后 `.ant-tree-treenode.selected` 仍为 `(none)`，字段表 28 行不变（首行仍是 `实验文本(已改)`）。
⇒ **选择态未变；原因未定**（按 auditor 降级：INVOKED 只证明函数被同步调用未抛，不证明它是受控选择链入口；两并列候选 = handler 静默早返回 / commit 阶段 removeChild 异常打断，二者未分辨）。

## 三、/service 情况

本轮**未手工发起任何 `/service` 请求**（零 curl / 零 fetch）。观测到的请求全部是页面自身刷新流量：

```
Document 200  .../entity?appId=8704025620829192834
200 udc/graphql ×N
200 udc/application/user-role
200 udc/sandbox/delta-build-info/8704025620829192834
200 udc/application/search/front-detection
```
**零 302，零 ≥400，零写请求**（无 save/commit/delete/publish）。点击保存/提交/删除/发布 0 次。

## 四、等级判定

**PARTIAL**，按 HANDOFF「不得强凑 PASS」：
- 页面 Live 可访问 + 4/4 实体名可见（caption 口径：DB migrationPlan.caption=迁移方案配置，DOM 摘录已含该名）⇒ 这部分 **LIVE**
- BIGINTEGER 字段 **9 行（DISTINCT name=7）0 命中** ⇒ 目标验收项 **UNVERIFIED**
- 不构成「字段页面可见」的 PASS；也不等于建字段成功、不等于运行态可访问

## 五、缺什么才能判 PASS

需要在同一页面把字段表切到 `MigrationLog` / `fileMigration` / `LogSchemeInformatio` / `migrationPlan`（树显 caption=迁移方案配置），使 tbody 出现全部 7 个 DISTINCT 字段名：`batchId/fileSize/processedRows/totalRows/duration/sourceDatasourceId/targetDatasourceId`（对照口径=DB 9 行、7 名，缺 migrationPlan 两字段即未覆盖，不得判 PASS）。
当前卡点不是权限、不是限流，是**该设计器在本 Edge profile 下切换实体时表格渲染中断**（removeChild 异常）。
建议路径（需 main 决定，未擅自执行）：换 `--disable-features` 重启本组 profile 重建渲染环境；或改用 `小爪实验实体` 所在分组内的交互顺序；或由人工点一次确认是否人工可切换（区分"环境问题"与"我的驱动问题"）。


## 六、修订记录
- 2026-10-19 11:37（auditor C-2 审查后补记）：本文 §二「字段单元格是 <input> 须读 .value」的结论已被 C-2 修正——名称/编码列与序号列元素类型不同，C-1 当时混读 .value 与文本导致 9 字段名假阴性（另有正则双层转义 bug）；采集方法以 C2-RECOVERY-20261019.md §四为准。（按 auditor VERDICT 2026-10-19，main 落）
- §五验收清单补 migrationPlan 的 sourceDatasourceId/targetDatasourceId，对照口径改「9 行 / DISTINCT 7 名」。
- 「字段表 28 行」口径未定义且与 DB 不符（xzhExp950795 字段 19 = 业务 11 + 系统 8），作废，不再作行数证据；行集合未变以行内容比对为准。
- §二因果降级：INVOKED 不证明受控链入口；removeChild 与选择态未提交是两环节，原因未定。
- 实体可见改 4/4（caption 口径）；「9 条字段名」改「9 行（DISTINCT 7 名）」。

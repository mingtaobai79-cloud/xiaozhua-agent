# UDC 4 核心域可执行模型补齐 · 第 3 轮（代码落地）

日期：2026-10-12 深夜（续）
接续：ROUND1（9 域入口 LIVE）、ROUND2（实体/BI/规则深入 + 版本沙箱链）。
本轮性质：把已取证的"用法"从 doc 搬进可执行代码 + 全量审计测试。证据优先，不新造事实。

## 0. 判断（为什么是代码，不是继续 CDP）

用户原话："bi域和流程域，以及微流程，页面这几个核心的东西……你缺少很多，很多用法你都不知道。"
根因不在抓包不够，而在：**证据厚（doc 全在），但没进代码**——模型/契约/校验器缺，
导致"用法"停在文档层面，宿主/AI 无法逐用法执行与校验。
微流程画布 CDP 打开链已连卡 3 轮（表格不渲染，分组未选中则不渲染），
判定为低收益路径，本轮不投入，转代码补齐。

## 1. 本轮新增可执行落点（全部离线可测，证据驱动）

| 域 | 新落点 | 文件 | 证据来源 |
|----|--------|------|----------|
| 微流程 | 节点/动作模型 + dataSchema 解析器 + 校验器（8 控制节点 + 4 组活动值域 + CONVERT_DATA 11 值受控 + 前端 10 项创建类型映射 + 容器递归 + 作用域软检查） | `components/udc/microflow_model.py` | microflow-source-audit.md §1-§4,§7 |
| BI/流程 | cdp-data 设计态 op 目录（7 op，四 tab）+ bpm 设计态 op 目录 + 页面结构常量 + 可落盘 catalog JSON | `components/udc/bi_flow_ops.py` | NAV-LIVE-CAPTURE-20261012-ROUND2.md §1 |
| 页面 | 事件/动作值域模型 + 校验器（actionType 4 值 / buildin openPage 穿透 / widget ENTITY_DELETE+ROW_DATA / 面板 openPanel+target / microflow 按钮必绑 id / 对象边界 VALIDATE 组≠VALIDATE_ENTITY） | `components/udc/page_event_model.py` | UDC-MAINLINE-AUDIT.md §3 + page-menu-source-audit.md |
| 全量 | 9 导航域覆盖审计测试（应用/实体/菜单/规则/流程/BI/栏目/设置/角色 各断言有可执行落点 + registry op 真登记 + 可落盘覆盖矩阵） | `tests/udc/test_domain_coverage.py` | 交叉 registry.py + 上述三模块 |

配套测试（全离线，绿）：
- `tests/udc/test_microflow_model.py`（14）：值域自检 / 解析+校验 / 容器递归 / CONVERT_DATA 受控 / 作用域软检查 / 与 create builder trigger 值域衔接
- `tests/udc/test_page_event_model.py`（9）：动作值域 / 行穿透详情 / 行删需 ROW_DATA / 面板需 target / 微流程按钮必绑 id / 对象边界
- `tests/udc/test_bi_flow_ops.py`（6）：op 服务归属 / 四 tab+两 tab+固定自由分类 DOM 实证 / catalog JSON 往返 / 证据级封顶 OBSERVED_LIVE

## 2. 完成度更新（对 APP-DESIGN-NAV-INVENTORY §7 / UDC-MAINLINE-AUDIT 缺口表）

| 域 | 上轮(代码面) | 本轮(代码面) | 说明 |
|----|-------------|-------------|------|
| 微流程 | 仅 create body + checkSchema | **+节点/动作模型 + dataSchema 校验器**（audit §8 缺口 1/2/3/5 已覆盖） | 节点结构/值域/容器递归/作用域可离线校验 |
| 页面 | 仅列表/详情骨架 + 事件散落 | **+事件/动作值域模型 + 校验器**（组件事件/面板/微流程按钮/穿透详情可校验） | 面板 UdcPanel 仍 UNVERIFIED（无字段级证据，校验器不臆造其值域） |
| BI | registry 仅 ganttchart 5 条 | **+cdp-data 设计态 op 目录（7 op 四 tab）** | 写链（新建数据集/报表）仍 BLOCKED（该 app 1.0.2 构建 FAIL） |
| 流程 | registry 仅 bpm 只读族 | **+bpm 设计态 op 目录 + 页面结构常量** | 流程模板创建仍 BLOCKED（构建链坏） |
| 全量审计 | 无 | **9 域覆盖矩阵测试（强制不遗漏）** | 每域断言有落点，缺则 FAIL |

## 3. 全量回归

`pytest tests/ -q` → **484 passed**（基线 448，净增 36 = 微流程 14 + 页面 9 + bi/flow 6 + 覆盖审计 7）。
文档契约（test_documentation_contract）同步 448→484，3 文档已更新，全绿。
已提交 commit `572d9cf`。

## 4. 未尽事项（诚实登记，不谎称完成）

1. **微流程画布 CDP 打开链**：仍 UNVERIFIED（表格未选中分组不渲染；右键/图标/hover 三轮未触发设计器加载）。低收益，暂挂。
2. **页面设计器写链**：buildin/widget/microflow 动作可离线校验，但"设计器页面上按钮构建"真实 Network 等价性仍未逐字抓包（page-menu-source-audit §8 边界）——**构建必须走页面点击**，本轮未做。
3. **BI 写链 / 流程模板创建**：BLOCKED——该 app 1.0.2 沙箱构建 FAIL（round2 实证），写操作依赖构建成功会被挡。需先修复构建链或用可用 app。
4. **面板（UdcPanel）字段级证据**：UNVERIFIED（webpack 该版本未见注册体），校验器对面板只锁动作名不锁字段，符合"不臆造"。
5. **设置 13 tab 中"选项集写侧 op / 基础资料后端 controller / 二维码后端 / 角色权限后端"**：SETTINGS-TABS-CALLCHAIN §4 仍 UNVERIFIED（部分属 ctp-user 服务，非 udc）。
6. 本轮全部为**离线可证面**；任何"live PASS"仍需宿主在可用 app 上实际执行，未在本次声称。

## 5. 复核索引

- 新增代码：`components/udc/microflow_model.py`、`bi_flow_ops.py`、`page_event_model.py`（已导出到 `components/udc/__init__.py`）
- 新增测试：`tests/udc/`（test_microflow_model / test_page_event_model / test_bi_flow_ops / test_domain_coverage）
- 证据 doc：`docs/audit/udc-semantics/microflow-source-audit.md`、`page-menu-source-audit.md`、`SETTINGS-TABS-CALLCHAIN.md`、`NAV-LIVE-CAPTURE-20261012-ROUND2.md`、`UDC-MAINLINE-AUDIT.md`
- 证据链约定：jar 路径/版本/网关/appId 走 config/（铁律），本轮代码只引用值域与结构，不写死环境量。

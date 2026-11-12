# 计划：UDC 设计器前端「每页每个位置」功能全量提取

> 目标：把设计器前端每个页面、每个 tab、每个按钮/拖拽/弹窗 → 触发的接口，全部提取出来。
> 方法：前端 = 需求真相源；后端 = 实现手段。前端盘干净 → 再对后端 → 再执行。
> 主线：`<SEEYON_AGENT_ROOT>`；前端资产：`<HERMES_HOME>/cache/scratch/udc-frontend/`

## 基线（已完成）
- 前端全量落盘：158/166 chunk（11MB）+ 99 解包目录（wakaru 近源码）
- store op 注册表：291 op（fieldType+paramsType+paramsKey+queryFields）
- 页面组 16 个；打样生单规则页成功（90 文案 + 事件 + 组件）

## 缺口
「哪个按钮 → 哪个 op」这条线未连死。原因：设计器用共享 service 层 +
React props 传递，页面里只出现 `l.z()` 这类 minified 符号。1 跳传播只连上 15 chunk。

## 推进步骤（按序）

### S1 模块级索引 v2（基建）
每 module 抽：① require 绑定表（localvar→moduleId）② 局部 fieldType ③ 导出表（exportSym→定义体）
落：`module_detail.json`

### S2 函数符号表（桥）
module → { exportSym: fieldType | 转发目标(moduleId.sym) }
落：`symbol_table.json`

### S3 多跳解析器
pageModule 引用的符号 → 递归解析到 fieldType（≤3 跳），带证据链
落：`symbol_resolver.py` + 每步解析轨迹

### S4 逐页连链
每页面 chunk → 每个 handler/引用 → 解析出的 op 清单（含未解析项，不臆造）
落：`page_button_ops.json`

### S5 按钮级功能地图（交付物）
每页：tab / 按钮文案 / 表单项 / 拖拽 / 弹窗 → op
落：`docs/audit/udc-semantics/frontend-page-ui-map.md` + `.json`

### S6 前端↔后端对账
前端调用的 op ↔ `_api_full.json` 657 方法级契约：哪些命中、哪些前端有后端无、哪些后端有前端未用
落：`docs/audit/udc-semantics/frontend-backend-reconcile.md` —— **实测从未生成**（非客户证据迁出，就是没产出），只有同名 `.json` 数据（112,714 B），见文末「产物落地核对」

### S7 订单应用构建链路
基于页面功能地图，产出订单应用所需的「页面点击链路」清单 → 交给 planner

### S8 落库 + 测试
所有产物入 git；可复跑脚本入 `tools/`；关键断言入 `tests/udc/`

## 纪律
- 证据分级：STATIC（chunk 字节码）/ LIVE（活体）/ UNVERIFIED；不臆造
- 解析不出 → 落 unknowns，不猜
- 每个交付物可复跑（脚本 + 原始数据）

## 状态
- [x] 前端全量落盘 + op 注册表 + 打样
- [x] S1 模块级索引 v2（1811 模块/9876 require 边，精确 webpack 第三参 require 名）
- [x] S2 函数符号表（6 action NS / 93 方法；静态 13 解析通链语义正确）
- [x] S3 多跳解析器（静态收敛 13/93 后转运行时方案）
- [x] S4 逐页连链（direct ops 12 页可靠；洪泛层明确标注）
- [x] S5 按钮级功能地图（frontend_page_model.py 134 页 + ui-inventory 746 行）
- [x] S6 前后端对账（173 条 op↔method+path 映射）
- [x] S7 订单应用构建链路 ✅ — 数据迁移应用 LIVE 实验：
      8 条写链全通（实体/字段/文本+枚举字段/索引/菜单/页面/微流程建+改/枚举+项），
      全部回读验证；固化 live_write_templates.py（10 模板+依赖序+校验规则）；
      附带发现 _api_full 页面路径拼接缺前缀（已证 404）
- [x] S8 落库 + 测试（713 绿）
- [x] S13 运行时拦截 ✅ — Node webpack harness 全量跑通：463 函数路径/323 解析/322 唯一 op/145 语义名，
      frontend_runtime_ops.py（ops_of/fns_of 双向查询）。「按钮→接口」链路打通（RUNTIME 级证据）。

## 产物落地核对（2026-11-07 第 60 轮实测，逐项查磁盘）

本计划的 S1–S8 全部标了 `[x]`，但**落盘与标记不一致**。以下按 `落：` 行逐项实测：

| 步骤 | 计划落点 | 磁盘实测 | 结论 |
|---|---|---|---|
| S1 | `module_detail.json` | **不存在**（全库 rglob 无，git 从未入库） | 中间件，未留存 |
| S2 | `symbol_table.json` | **不存在**（同上） | 中间件，未留存 |
| S3 | `symbol_resolver.py` | **不存在**（同上） | 中间件，未留存 |
| S4 | `page_button_ops.json` | **不存在**（同上） | 中间件，未留存 |
| S5 | `frontend-page-ui-map.md` + `.json` | **在盘** 98,184 B / 277,133 B，已入 git | ✅ 交付物齐 |
| S6 | `frontend-backend-reconcile.md` | **不存在**；同名 `.json` 在盘 112,714 B（键：`frontend_total / backend_total / matched / frontend_only / backend_only / matched_pairs`） | ⚠️ **对账数据在，人读的 md 从未产出** |
| S7 | 订单应用构建链路 | `components/udc/live_write_templates.py` 在盘 | ✅ |
| S8 | 产物入 git + 脚本入 `tools/` + 断言入 `tests/udc/` | `components/udc/frontend_page_model.py`、`frontend_runtime_ops.py` 在盘 | ✅ |

**S1–S4 是中间件（中间产物），不是交付物** —— 它们的产物被 S5/S6 消费完后没有留存，
所以「`[x]` 已完成」与「产物可复跑」是两件事：**这一步做过，但现在重跑不了**。
本表的意义是：后来者看到 `[x]` 会以为能拿 `symbol_resolver.py` 复算，实际拿不到。

⇒ 引用纪律：**这个文件的 `[x]` 只表示「当时做过」，不表示「现在可复现」**。
   要复现 S1–S4 需重跑 wakaru 解包 + 重建符号表，不在本仓范围内。

（S13 是后加的步骤，不在 S1–S8 序列里，编号跳号不是漏项。）

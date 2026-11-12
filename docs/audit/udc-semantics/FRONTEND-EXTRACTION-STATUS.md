# UDC 设计器前端功能提取 —— 状态报告

> ⚠️ **已被取代**：本文件是 v1（S1–S6，op 数 346）。最新结论见 `FRONTEND-EXTRACTION-STATUS-v2.md`
> （op 并集 456、action 命名空间 6 个/55 方法）。本文件保留作历史记录，数字勿再引用。

> 日期：2026-10-13 | 主线：`<XIAOZHUA_AGENT_ROOT>`
> 前端资产：`<HERMES_HOME>/cache/scratch/udc-frontend/`（158 chunk + 99 解包目录）
> 证据：STATIC（chunk 字节码 + wakaru 解包近源码）

## 1. 已完成（可复跑）

| 产物 | 内容 | 文件 |
|---|---|---|
| 前端全量 chunk | 158/166（8 个 .less 404）| `scratch/udc-frontend/chunks/` |
| 解包近源码 | 99 目录（wakaru）| `scratch/udc-frontend/unpacked/` |
| 前端 op 全表 | **346** op（fieldType 215 / apollo 121 / 混合 10）| `frontend-extraction.json` |
| store 注册表 | 291 op（paramsType/paramsKey/queryFields）| `frontend-extraction.json` |
| UI 清单 | 99 页（文案/按钮/事件/组件/拖拽/弹窗）| `frontend-ui-inventory.md/.json` |
| 前后端对账 | 前端 346 ↔ 后端 657，匹配 **173** | `frontend-backend-reconcile.json` |

## 2. 关键机制（本轮新证）

### 2.1 前端 op 分派中心
`module 44456` 定义 `udcApolloQuery / udcQueryLoader / udcMutationLoader`，
由 `getRequestByAppName(域)` 生成，**每域独立命名空间**：
```
appApproval / udc / bpm / ctpMetadata / portal / main / appCommon / ctpUser
```
→ 解释了「流程(bpm)/BI(cdp-data) 不在 udc-web 命名空间」。

### 2.2 页面 → 接口的两种调用模式
```
① udcMutationLoader.load({fieldType:"udcXxxPost", paramsType, paramsKey, params})
② 域.apolloQuery("query udcXxxGet { ... }")   ← GraphQL 字符串
```

### 2.3 页面 → action → op 链路
```
页面组件 → X.xxxActions.method() → redux thunk → 内部 service 函数 → fieldType/apollo → op
```
action 命名空间示例：`appBasicInfoActions / entityFieldActions / enumActions /
enumldActions / customExtensionActions / entityRuleActions`

## 3. 对账结论

- 前端 346 op 中 **173 命中** 后端 udc-web 657 方法级契约
- 未命中 173：主要为 **域外服务**（bpm/ctp/appCommon/portal/cdp-data），少数命名差异
- 后端 451 未命中：**前端未调用的接口**（运维/内部/低代码生成用）—— 需分类

## 4. 未完成（诚实标注）

| 项 | 状态 | 卡点 |
|---|---|---|
| 按钮级「点哪个按钮 → 哪个 op」 | **部分** | 页面经 redux action + props 传递，minified 符号跨 chunk 解析成本高；已建立 action→op 骨架（3 ns/13 action），未全量 |
| 每页 tab 级细分 | 部分 | 16 页面组的 tab 已从 UI 文案可见，未逐 tab 建结构化表 |
| 按钮级权限（换角色验证） | 未做 | 需 test2 实机按角色点验 |
| 前端构建链（订单应用页面对齐） | 未做 | 依赖上两项 |

## 5. 下一步

1. 补 action→op 全量（建 wakaru 模块依赖图 + 函数符号表，把 `xxxActions.method → op` 连死）
2. 逐页 tab 结构化
3. 换角色 LIVE 验证按钮权限
4. 产出订单应用「页面点击链路」→ planner

## 6. 复跑脚本（scratch/udc-frontend/*.py）

```
parse_chunks.py     remoteEntry → chunk 清单
download_all.py     全量下载
unpack_all.py       wakaru 解包
s3_v5.py            三种模式 op 抽取 → frontend_all_ops.json
store_ops.py        store 注册表
s4_ui_inventory.py  99 页 UI 清单
s6_v2.py            前后端对账
s8_combine.py       汇总 frontend-extraction.json
```

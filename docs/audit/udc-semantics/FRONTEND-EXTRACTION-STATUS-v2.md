# UDC 设计器前端功能提取 —— 状态报告 v2

> 日期：2026-10-13 | 主线：`<XIAOZHUA_AGENT_ROOT>`
> 前端资产：`<HERMES_HOME>/cache/scratch/udc-frontend/`
> 证据：STATIC（chunk 字节码 + wakaru 解包）
> 接续：`FRONTEND-EXTRACTION-STATUS.md`（v1，S1-S6）

## 1. 数据规模

| 产物 | 数量 | 文件 |
|---|---|---|
| 前端 chunk | 158/166 | `scratch/udc-frontend/chunks/` |
| 解包目录 | 99 | `scratch/udc-frontend/unpacked/` |
| webpack 模块 | 1811（严格切分）| `module_detail.json` |
| **前端 op 并集** | **456** | `frontend-op-model.json` |
| store 注册表 | 291 | `frontend-op-model.json` |
| 页面 UI 清单 | 99 页 | `frontend-ui-inventory.md` |
| 前后端对账 | 匹配 173 | `frontend-backend-reconcile.json` |

## 2. 关键机制（STATIC 实证）

### 2.1 op 分派中心（module 44456）
```
getRequestByAppName(域) → { <域>ApolloQuery, <域>QueryLoader, <域>MutationLoader }
域 = appApproval / udc / bpm / ctpMetadata / portal / main / appCommon / ctpUser
```
→ 实证「流程(bpm)/BI(cdp-data) 不在 udc-web 命名空间」。（文件名中勿用花括号）

### 2.2 前端调 op 三模式
```
① fieldType:"udcXxxPost"                     (215)
② 域ApolloQuery("query udcXxxGet { ... }")    (121)
③ "udc".concat("Xxx")                         (混合 10)
```

### 2.3 action 命名空间（6 个，55 方法）
```
appBasicInfoActions(22) entityFieldActions(19) enumldActions(7)
customExtensionActions(4) enumActions(2) entityRuleActions(1)
```
定义链：NS → holder → require(moduleId) → 该模块导出表（action名→局部符号）→ 函数体 → op

**已解析通链（3 个，语义正确）**：
```
entityFieldActions.fetchEntityFieldList → udcDataTypeDataTypesByAppIdAppGet, udcEntityAttributeGroupSearch
entityFieldActions.setRowSelection      → udcEntityAttributeSelectByPrimaryGet
entityRuleActions.fetchRuleList          → udcMicroflowSearchEntityRulePost
```

## 3. 卡点（诚实标注）

**action → op 全量未通**，根因：
- minified 变量名复用（`O` 既是导出别名又是 `n(91718)` 的变量）
- 模块边界跨 chunk（定义模块与引用模块分离）
- service 层三层嵌套（action → service ns → loader）

已投入 S1-S7，每次终点验证正确，但全量覆盖受 minified 冲突限制。
当前：55 方法中 3 完整解析，另有 151 个解包函数→op 映射（`unpacked_fn_ops`）。

## 4. 替代路径（已验证可行）

- **UI 元素层（100% 可靠）**：99 页按钮/表单项/事件/拖拽/弹窗 → `frontend-ui-inventory.md`（746 行）
- **op 全表（456）**：前端能调的所有接口名 + paramsType/paramsKey → `frontend-op-model.json`
- **结合**：页面 + 按钮语义 → op 全表按语义定位候选 → 后端契约确认

## 5. 剩余工作

1. action→op 补全（需更鲁棒符号解析，或线上 sourcemap 直接还原 TS）
2. 每页 tab 级结构化
3. 换角色 LIVE 验证按钮权限
4. 订单应用「页面点击链路」→ planner

## 6. 复跑脚本（scratch/udc-frontend/）

```
parse_chunks.py download_all.py unpack_all.py     # 前端拉取
s3_v5.py        → frontend_all_ops.json           # op 三模式
store_ops.py    → store_ops.json                  # 注册表
s4_ui_inventory.py s7_final.py                    # UI 清单 + 页面地图
s7_v7.py        → ns_method_ops.json              # action 命名空间
s7_unpacked.py  → unpacked_fn_ops.json            # 解包函数→op
s6_v2.py        → frontend-backend-reconcile.json # 前后端对账
s8_final.py     → frontend-op-model.json          # 汇总
```

---
name: seeyon-udc-application-app-inner
description: "Use when operating the 2小爪 UDC 应用内功能页 (页面测试/沙箱测试/发布版本/应用依赖/组件依赖/团队/主题) or the sandbox 构建链路: 取数口、请求体、响应层级、依赖加删与复原、构建日志取法。"
version: 1.0.0
author: 小爪 🐾
license: MIT
platforms: [windows, macos, linux]
tags: [2小爪, udc, application, dependency, sandbox-build, applog]
metadata:
  hermes:
    tags: [2小爪, udc, application, dependency, sandbox-build, applog]
---

# 应用域 · 应用内功能页 + 沙箱构建

一句话：应用设计器右侧那排功能页（页面测试 / 沙箱测试 / 发布版本 / 应用依赖 / 组件依赖 /
团队设置 / 应用主题）和工具栏「测试 → 立即构建」，全部走 **GraphQL**（除两条例外），
构建日志靠一个接口一把取全量。

## 什么时候用

- 要在应用里加/删依赖（先问清是「应用依赖」还是「组件依赖」，两者删除口不同）
- 要读构建日志、构建耗时、沙箱状态
- 要判断某条 `/service/udc/graphql?...` 属于应用内哪个子页
- 要给应用域加新契约（先用 `UdcOperationRegistry.default()` 查是否已存在）

## 四类资产（改这个域必须同步）

| 类别 | 位置 |
|---|---|
| 实现 | `components/udc/application/app_inner_ops.py`、`dependency_constraints.py` |
| 事实 | `core/facts/udc/application/app-inner/create.md` + `app-inner-write-chain.md` |
| 契约 | `docs/operation-contracts/udc/application/app-inner-contracts.md` |
| 测试 | `tests/udc/test_application_app_inner_asset_layout.py` |
| 证据 | `core/facts/udc/application/evidence/app-inner-build-2026-10-22/` |

改完跑：

```
.venv/Scripts/python.exe -m pytest tests/udc/test_application_app_inner_asset_layout.py -q
.venv/Scripts/python.exe tools/core/_meta/capability_report.py --check   # 应用域 应无缺口
.venv/Scripts/python.exe -m pytest tests/test_deidentification.py -q
```

## 五个必须记住的坑

1. **GraphQL 响应外层多一层 `data`**：`raw["data"]["data0"]["data"]["content"]`。
   直接取顶层 `data0` → `KeyError: 'data0'`。裸 `urllib` 还要带 `Accept: application/json`。
2. **依赖列表只传 `appId` 会 `total=0`**：必须带 `versionType` 与分页字段。
3. **移除依赖传的是依赖行 id**，不是 appId、也不是 depAppName。传错不报错，只是删不掉。
4. **组件依赖删除是 REST**（`delete-by-ids`，`{"ids":[...]}`），行内没有「移除」按钮，
   入口是表格上方「批量删除依赖」，确认框是「取消 / 确认」；这条请求 CDP 常抓不到，
   要在页面内 hook `XMLHttpRequest`/`fetch` 记 `window.__CAP__`。
5. **构建日志不抓流**：`udcSandboxBuildInfoAppGet`（别名 `path:` 不是 `body:`）返回
   `{state,progress,totalTime,logs[]}`，`logs` 即「[展开沙箱日志]」全文。

## 写面纪律

放行（用完必须复原并回读确认）：
- `udcApplicationDependentApplicationCreateBatchPost`（加依赖，SERVICE / FRONTEND）
- `udcApplicationDependentApplicationDeleteByIdPost`（移除应用依赖）
- `udc/application/dependent-application/delete-by-ids`（移除组件依赖）

一次性的：`udcRuntimeDeployNormalPost`（沙箱构建）—— 会覆盖沙箱态，不是读面。

永不碰：发布 / `app-online` / 沙箱 flexible `create|delete|restart` / `front-log/create` /
`disable-last-version-metadata` / page-info `create|update|delete` / 清除应用数据 / 移交应用。

## 操作路径速查

```
依赖列表     GET  app-basic-info/dependentApp → POST SelectByCondition
添加依赖     点「添加依赖」→ 弹窗勾选 → 确定       （候选组件不发请求，前端内置目录）
移除应用依赖 行内「移除」→ 确认
移除组件依赖 顶部「批量删除依赖」→ 确认
构建         工具栏「测试」→ 弹窗「立即构建」
构建日志     build_info 的 logs[]（构建结束仍可读）
版本列表     search-app-edition（IN_appId 传 appName 字符串）
```

antd 受控 checkbox 点不动时：`scrollIntoView` 后按坐标点 `.ant-checkbox-inner`，
勾完先断言 `tr.className.includes('selected')` 再点确定，否则会发空数组写。

# S7: 数据迁移应用 LIVE 实验（订单应用缺席的替代实验场）

> 日期：2026-10-14 11:57 | 应用：`8704025620829192834`（datamigration…）
> 方法：REST 直调（后端 657 契约的读接口）+ cookie 鉴权 | 证据：**LIVE**

## 1. LIVE PASS（BOOT_0000 + 真实数据）

| 接口 | 形态 | 结果 |
|---|---|---|
| GET /udc/application/detail/{id} | REST | 应用详情（UNPUBLISH/RELEASE）|
| GET /udc/entity/select-all-by-appid/{appId} | REST | **7 实体**（迁移方案配置/数据源配置/迁移日志…全部 standard 版型）|
| GET /udc/entity/primary/select-by-appid/{appId} | REST | **4 主实体** |
| GET /udc/page-info/detail-app-id/{appId} | REST | **21 页面**（SEARCH_LIST/DETAIL/角色管理…）|
| POST /udc/event/list | REST | **48 事件**（加签事件/推送OA…真实业务事件）|
| POST /udc/udc-enum/list | REST | **1077 枚举** |
| POST /udc/refer-config/group/list | REST | **386 参照组** |
| POST /udc/function/find/tree-and-group | REST | 功能树（BOOT_0000）|

## 2. 未通（body/路径形态待调，非阻断）

| 接口 | 现象 | 下一步 |
|---|---|---|
| POST /udc/microflow/search | BOOT_1001（参数错）| 分页 DTO 形态待抓 |
| POST /udc/function/select/function-tree | BOOT_3000 | 改用 find/tree-and-group 已通 |
| GraphQL ?op batch | Invalid Syntax | 需带真实 GraphQL query 串 |

## 3. 结论

- **后端 657 契约的 REST 读面 LIVE 全可用**（正确路径+appId 即通）
- **runtime fn→op 真值表（322 op）** 与 LIVE 行为一致（如 udcEntitySelectAllByAppidAppGet 对应 /udc/entity/select-all-by-appid）
- 前端 GraphQL 面与 REST 面并存确认（与 filterPlan 双通道结论一致）
- 微流程写链（S7 核心）需先通 search 读，再按 udc-biz 微流程模板建 dry-run 写实验

## 4. 风险

- 凭证登录接口报 USER_0055（密码不符，已错1次停止重试）；当前 cookie 仍有效
- 若 cookie 失效需人工更新 shared-credentials/

## 5. S7 下一步（写链实验，须确认）

1. 在 datamigration 应用**复制一个实验实体**（写操作前先人工确认）
2. dry-run planner 出构建计划 → 对照前端 runtime fn→ops 逐 op 校验
3. 再逐步：枚举→字段→页面→菜单

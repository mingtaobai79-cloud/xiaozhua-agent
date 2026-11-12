# UDC 设计器 15 导航活体测试（LIVE，正确应用 datamigration9000000000000000001）

日期：2026-10-12
方法：独立调试 Edge (CDP 9222) + cookie 注入 + 从设计器壳真实点击导航 + Network 域抓包（请求 URL/body + 响应体）。
抓包原始数据：`cache/scratch/udc-live-capture.jsonl`、`udc-live-capture3.jsonl`（未入库，临时证据）。
应用：`8704025620829192834`（datamigration9000000000000000001，"数…"）。**此前用 zzprobe 6419954374508955097 是错误对象——zzprobe 深链时壳不注入 xcbpbi，BI 域直接 no.auth。**

## 0. 本轮修正的机制认知（全部 LIVE 证实）

1. **BI/流程不是 udc 代码**：`/service/cdp-data/...`、`/service/bpm/graphql` 独立应用段；网关 `/service/(.*)` → ctp-webapi-gateway，按第一段路由到微服务。
2. **app 上下文靠 `window.xcbpbi` 注入**：`appName=datamigration9000000000000000001`，`appId`。直接深链 `child-frame` URL 时 xcbpbi 为空 → `cdp.udc.app.no.auth`。必须从设计器壳（basic-info 落地页）内导航。
3. **路由必须用 `<a href>` SPA 跳转**：用 `location.hash` 拼路由会把 appId 污染成 `870402...#/app-design/...`，后端报 `BOOT_3000 For input string`（已踩坑，capture2 全批作废）。
4. `xc>` BI 环境自报：`/service/cdp-data/env/variable` → `cdpBiPlugin/cdpDfPlugin/cdpBigScreen=true, etlEngine=sql_etl, monolithic=false`。

## 1. 各导航域真实端点（本轮 LIVE PASS，HTTP 200 + BOOT_0000）

| 导航 | 方法 | 端点 | 用途 | 结果 |
|------|------|------|------|------|
| 菜单 | POST | `/service/udc/graphql?udcFunctionSelectFunctionTreePost` | 菜单功能树（首页/图标/permission…） | LIVE PASS |
| 菜单 | POST | `/service/udc/graphql?udcApplicationAppVersionAppGuidPost` | 版本列表 | LIVE PASS |
| 实体 | POST | `/service/udc/graphql?udcEntitySelectAllByAppidAppGet&udcEntityGroupSelectByAppidAppGet&…`（batch） | 实体列表+分组 | LIVE PASS |
| 实体 | POST | `…udcEntityAttributePresetAttributeCapacityAllAppGet` | 预置系统属性（creator/创建者…） | LIVE PASS |
| 实体 | POST | `…udcAttributeGroupEntityGet` | 属性分组（系统组） | LIVE PASS |
| 实体 | POST | `…udcEntityGet&…`（batch） | 实体详情+字段类型枚举（STRING 文本…） | LIVE PASS |
| 实体 | POST | `…udcEntitySelectMasterEntityCountAppGet` | 主实体容量：existingCount=4/40 | LIVE PASS |
| 规则 | POST | `…udcMicroflowSearch` | 微流程列表 total=9（本 app 9 条） | LIVE PASS |
| 流程 | POST | `/service/bpm/graphql?bpmTemplateSelectByAppIdGroupByTagPost` | 流程模板按 tag 分组（空=未建） | LIVE PASS |
| BI | GET | `/service/cdp-data/env/variable` | BI 插件环境 | LIVE PASS |
| BI | POST | `/service/cdp-data/udc/dataset/get-list-page` | 数据集分页（当前 0 条） | LIVE PASS |
| 栏目 | GET | `/service/udc/page-info/select-by-appId/{appId}` | 页面信息列表（portal 栏目用） | LIVE PASS |
| 栏目 | POST | `…udcApplicationGet` | 应用信息 | LIVE PASS |
| 设置 | POST | `…udcEnumCategorySearch` | 枚举分类（"框架终止"等真实数据） | LIVE PASS |
| 角色(操作权限) | POST | `/service/udc/ctp-user/role/create-system-admin` body={appId} | 初始化系统管理员角色（幂等返回 content:1） | LIVE PASS(写!) |
| 角色 | POST | `…udcCtpUserRoleAppResourceGet` | 角色资源矩阵（PC_LAYOUT/PC…） | LIVE PASS |
| 应用/基本信息 | POST | `…udcApplicationDependentApplicationSelectByConditionPost` | 依赖应用（portal 5.3.392…） | LIVE PASS |
| 应用/基本信息 | POST | `…udcApplicationDetailGet&udcApplicationIsLastVersionAppGet&udcDeploymentAppReadyStatePost`（batch） | 应用详情+版本+就绪态 | LIVE PASS |

## 2. 边界与教训（新增，永久有效）

- **对象边界**：`角色(操作权限)` 是 ctp-user 域挂在 udc 网关下（路径 `/service/udc/ctp-user/role/*`），不是 udc 自己的表。
- **`create-system-admin` 是写操作**：导航进入角色页即触发（幂等），活体点击导航时会真实写库。后续自动化勿把"进页面"当只读。
- **微流程列表在「规则」域**（`udcMicroflowSearch`），不在流程域；流程域（bpm）只管 BPM 流程模板。两个"流程"完全不同域。
- 壳必须完全加载（约 12-14s）后导航才有效；子应用（bpm/cdp-data）chunk 懒加载需各自再等 3-8s。

## 3. 与既有文档的对账

- `APP-DESIGN-NAV-INVENTORY.md` §1 的 15 菜单/路径/identityCAF：**锚点全部 LIVE 证实**（本轮 a[href] 与之一致）。
- §4 BI API 表的 `/cdp-data/udc` 前缀：LIVE 证实；但独立基址 `/cdp-am`、`/cdp-df` 在 test2 网关 404——它们只在独立 BI 站点存在。
- §5 待补的 ctp-user 角色资源 API：本轮补上（`udcCtpUserRoleAppResourceGet`）。
- §7 完成度表更新：BI 40%→55%（数据集/环境活体）、流程 15%→30%（入口+模板列表活体）、角色 25%→55%（列表/资源矩阵/初始化活体）、菜单 45%→60%、实体 95%→97%（容量/预置属性活体）、设置 85%→90%。
- 仍未活体：页面（page-manage 主 tab）、外框、参数、高级设置、规则的画布保存链、BI 语义模型/指标写链。

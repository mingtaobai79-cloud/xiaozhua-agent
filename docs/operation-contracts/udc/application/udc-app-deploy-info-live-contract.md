# udc.application.deploy_info 契约（HANDOFF-01 · Phase 1 / P1 · 2026-10-17 CST）

> 本件补充并落地既有契约 3（`udc-app-basic-readonly-contracts.md` §契约 3，VERIFIED_STATIC_BYTECODE@5.3.517）的
> **完整路由判定 + LIVE 回读 + Long 形态**三项缺口。证据分级逐条标注；HTTP 200/空结果不判 PASS。
> 环境口径：LIVE 侧 test2 镜像 **5.3.496**（jar 内同族类逐字核对，见 §STATIC）；与既有契约的 5.3.517 本地 Maven 单元**两单元禁混写**。
> 凭据只按路径引用 `shared-credentials/test2-web-credential.json`（config 键 `environments.test2.credential.file`），值 0 入仓。

## 1. 契约字段（补充既有契约 3，不重抄）

1. operation_id: `udc.application.deploy_info`（registry.py L90 既有条目，本件不新增 key）
2. HTTP method: `GET`（`@GetMapping(value=["deploy-info"])`，5.3.496 jar 内同族逐字）
3. **完整路由（本轮 LIVE 判定，闭合既有 UNVERIFIED）**：
   `{gateway_base}/service/{currentAppName}/app-info/deploy-info`
   - 宿主前缀段 = **currentAppName 本身**（应用 name，非数字 appId、非网关 appId）；网关 `/{appId数字}` 前缀 → `server_404「服务不存在」`（live-probe-round5）。
   - Normal 子类类级前缀 `{currentAppName}/app-info` + 方法级 `deploy-info` 装配坐实；Form 子类 `dynamic-rest/com-seeyon` 变体在 LIVE 同样存在（round14 同 403 群，未独立验收，登记 UNVERIFIED）。
   - **路由判定纪律（本轮修正性结论）**：`/service/{appName}/` 上 target 全部返回网关层 `server_403`（含假 op），**403 不能作为路由命中证据**；判路由必须用「同命名空间假 op 与真 op 响应不同」对照（§4 归因）。
4. 参数: `@PathVariable currentAppName`（1 个，路径段）
5. 返回: `SingleResponse<String>`，`data.content` 为**字符串化的内层 JSON**（`content_is_str=true`），内层键：`businessType / deployInfo / deployType / terminalType / previousSchemInfo / deployId / tenantId / versionInfo / envInfo / extraParamMap`（round16 实测 1349 字符）。
6. evidence（STATIC）:
   - LIVE 侧口径 jar：test2 镜像同族 5.3.496，class `com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController`
     class_sha256=`deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95`
   - javap 落盘：`docs/audit/artifacts/udc-app-deploy-info-5.3.496/UdcBaseAppInfoController.javap.txt`（含 `@RestApiOperation("获取应用的构建版本等信息")`）+ Form/Normal 两子类 javap.txt
   - 前端 bundle 侧：udc remoteEntry + 166 chunk 扫描 `deploy-info` **0 命中**（`bundle/scan-report.json` `remote_has_deploy_info=false`、`bundle/deploy-info-chunk-hits.json=[]`、`bundle/runtime-deploy-info-hits.json hits=[]`）→ **完备负证据**：设计器前端不调 deploy-info；该面属生成代码应用（运行态 pod）的面。设计器基本信息页 28 条真实请求全部为 graphql `udcSandboxBuildInfoAppGet` 族。
     > 防误读补注（2026-10-17 P2 附带微修）：`scan-report.json` 的 `remote_chunks` **因采集脚本 `[:60]` 截断只存了 60 条**，非全量。全量 **166** chunk 已由 auditor 从 `remoteEntry` 独立重算并逐 chunk 扫描 `deploy-info`，**命中 0**。结论不变，但引用 `remote_chunks` 字段时不得当作全量样本。

## 2. LIVE 回读（对照应用 = 已部署的 app9000000000000000001）

| 项 | 实测（round16，2026-10-17T15:49:50+0800） |
|---|---|
| URL（键组装） | `{gateway_base}/service/{currentAppName}/app-info/deploy-info`，currentAppName=`app9000000000000000001` |
| HTTP / 字节 | 200 / 1592 B ×2 |
| envelope | `status:0 / BOOT_0000 / SUCCESS` |
| traceId | 第 1 发 `3278392001468303548`，第 2 发 `3278392024771856572` |
| identity | 内层 content 双发 **identity_match_inner=true**（round16 落盘字段） |
| 内层 appId 形态 | `"appId":3289082814923688017`（**无引号，JSON number → Python int**）；`deployId:3371559894822748027`（int）、`tenantId:-8112660841495312922`（int）、`previousSchemInfo.appGuid:5958633360229354868`（int） |

**终态：契约面 = LIVE（对照应用）**；四要素（HTTP 200 + BOOT_0000 + traceId + 双发 identity）齐。

## 3. appId numeric Long 形态（三方一致）

| 面 | 实测 | 形态 |
|---|---|---|
| deploy-info 内层原文（LIVE round16） | `"appId":3289082814923688017` | **JSON number（Long）** |
| `GET /service/udc/application/{id}`（LIVE round6/round10） | `"id":"8704025620829192834"` | **字符串**（ApplicationDto 序列化为 String） |
| DB `udc_application.id`（r19 DB 实测） | `bigint(20)` | **bigint** |

→ 底层为 Long/bigint；**各接口外层序列化表现不一致**（deploy-info=数字、application DTO=字符串），两形态并列登记，写入契约，不归一。
附带负证据：`GET /service/udc/application/datamigration9000000000000000001`（name 代 id）→ `BOOT_3000 Failed to convert … String`（round15 B1）——该端点只收数字 id。

## 4. 目标应用（datamigration9000000000000000001）运行态面 = BLOCKED（应用级，非契约级）

同凭据、同路径形态、同实验（round14/16/17/20）：

| 面 | target（datamigration…） | ctrl（znxmglpt…） |
|---|---|---|
| `/service/{appName}/app-info/deploy-info` | **server_403「无权限访问」**（78B，traceId=n/a）×2 双发一致 | BOOT_0000 / 1592B |
| `/service/{appName}/app-info/no-such-op`（假 op 对照） | server_403（同 403） | **404**（进入 pod） |
| `/service/{appName}/`（根） | server_403 | 404 |
| `/{appName}/remoteEntry.js`（静态面，不经 /service） | 200 / 23858B | 200 |
| `/service/udc/sandbox/build-info/{appId}`、`/service/udc/application/{id}`、`/service/udc/deployment/latest-test-info` | BOOT_0000 | BOOT_0000 |

归因（全部实测，不靠猜）：
- 假 op 也 403 → 403 非 op 级结果，路由命中无法由 403 证明；
- 403 响应 `traceId:"n/a"`、无 Traceid 响应头，平台面有真实 traceId → **403 出自网关/前置层，未进 pod**（round20 a/b/c/d 组坐实：header 变体 Referer/UA/XFF 不改变 403）；
- 静态面同命名空间 200 → 命名空间未整体封禁，403 命中 `/service/{appName}/` 前缀；
- DB 对照（`r19-role-db-compare.out.txt`，只读 SELECT）：两应用 `udc_application.publish_state` 均 =1、`udc_app_version` 均 state=1 已成功部署（target 1.0.14 @2026-10-15 19:29:31 / ctrl 1.0.11232 @2026-10-16 18:12:50）；差异 = `udc_role_resource` 行数 target 391 vs ctrl 4944，target 角色 11 条无 is_admin。

**归因指向**：target 的**运行态路由授权未建立**（角色-资源/运行态白名单），非契约问题、非凭据问题、非部署未完成。
> 口径收紧（2026-10-17 P2 附带微修）：`udc_role_resource` 391 vs 4944 属**强相关**，非因果充分 —— 本环境无 `udc_role_member` 类**用户-角色绑定表**（实查仅 `udc_resource` / `udc_role` / `udc_role_resource`），无法闭合「当前账号 → 角色 → 资源」链，故只能写「归因指向」，不得写「判定为」。
**所需输入（交 main）**：该应用运行态访问授权（udc_role_resource 补齐，或管理端给当前账号授应用角色，或有权限账号代执行）。
**本片不受阻**：契约验收锚点 = 契约 LIVE（§2 对照应用），target 面单列 BLOCKED。

## 5. 验收对照（HANDOFF-01 三条完成标准）

1. 契约文档含真实 URL/op/出入参/bundle 证据来源 → ✅ 本件 §1（bundle 侧为完备负证据，已如实登记）。
2. LIVE 调用有真实回读与 traceId，appId Long 形态确认 → ✅ §2（对照应用双发 identity）+ §3（三方形态）。
   **如实标注**：target 应用自身 deploy-info 无 LIVE 成功样本（§4 BLOCKED）。
3. 证据分级 LIVE/STATIC，HTTP 200/空结果不判 PASS → ✅ 全件逐条标注；403/404/BOOT_1006 均未判 PASS。

## 6. 证据文件索引

| 项 | 路径 |
|---|---|
| LIVE round16（契约双发 + Long 形态 + identity） | `docs/audit/artifacts/udc-app-deploy-info-5.3.496/live-probe-round16.json` |
| LIVE round17（三应用对照 + latest-test-info） | `…/live-probe-round17.json` |
| LIVE round20（403 层级归因，含假 op 对照） | `…/live-probe-round20.json` |
| LIVE round14（路径形态枚举） | `…/live-probe-round14.json` |
| DB 对照（角色/资源/部署态） | `…/r19-role-db-compare.out.txt` |
| bundle 负证据 | `…/bundle/scan-report.json`、`…/bundle/deploy-info-chunk-hits.json`、`…/bundle/runtime-deploy-info-hits.json` |
| STATIC javap（5.3.496） | `…/UdcBaseAppInfoController.javap.txt` + Form/Normal 子类 |
| 探针脚本（只读） | `scratch/r9..r20_*.py`（仓库 scratch，未入 git 提交范围另行判断） |
| 既有契约 3（5.3.517 单元） | `docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md` §契约 3 |

> 本件写作时钟 2026-10-17 16:0x CST；探针运行窗口凭据 `expires_gmt8=2026-10-18 16:04`（本轮续期）。

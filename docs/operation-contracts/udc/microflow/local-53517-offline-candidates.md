# 本地 5.3.517 jar 离线取证 — 微流程只读候选（A1 补齐）

来源：`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`
（本地 Maven 仓库，VERIFIED_STATIC_BYTECODE，标注 local 5.3.517，不混写 test2 版本）

取证方式：`<LOCAL_ROOT>/java/bin/jar tf` + `<LOCAL_ROOT>/java/bin/javap -v -p`（只读命令，无网络）

## 已知 GET 只读候选（A1 可入 registry）

### C2：UdcDataTypeController.getDataTypes()
- 类：`com.seeyon.boot.starter.udcrt.controller.UdcDataTypeController`
- 方法：`getDataTypes()`（无参）
- 映射：`@RequestMapping("udc-runtime/datatype")` + `@GetMapping("getAll")`
- 路径（控制器原值）：`udc-runtime/datatype/getAll`
- 网关 service 前缀：离线不可确证，标 UNVERIFIED（同 C1）
- 入参：无
- 返回：`ListResponse<DataTypeDto>`
- 判定：GET 只读，入 A1 registry 候选
- evidence_level：VERIFIED_STATIC_BYTECODE（local 5.3.517）

### C3：UdcAppLogController.selectAppDataById(Long)
- 类：`com.seeyon.boot.starter.udcrt.controller.UdcAppLogController`
- 方法：`selectAppDataById(java.lang.Long)`
- 映射：`@RequestMapping("udc-runtime/app-log")` + `@GetMapping("datalog/{id}")`
- 路径（控制器原值）：`udc-runtime/app-log/datalog/{id}`
- 网关 service 前缀：离线不可确证，标 UNVERIFIED
- 入参：`Long id`（@PathVariable）
- 返回：`SingleResponse<UdcEntityMonitorLogDto>`
- 判定：GET 只读，入 A1 registry 候选
- evidence_level：VERIFIED_STATIC_BYTECODE（local 5.3.517）

## 排除项（同 controller 的 GET 但语义 destructive，不入 A1 只读 registry）

`UdcAppLogController` 中以下方法虽为 `@GetMapping` 但语义为写/清除/卸载，**不得**入只读契约：
- `deleteAll()` → GET `delete-all` — destructive
- `clearOrgManager()` → GET `clear-org-manager` — destructive
- `clearRuntimeDataSource()` → GET `clear-runtime-data-source-cache` — destructive
- `unloadDynamicApp(String)` → GET `unload-dynamic-app/{appName}` — destructive
- `setRestEnableLog(Boolean)` → GET `enable-log/{enable}` — write

记录在此作排除证据，防止后续误入。

## P1 支路 BLOCKED 记录
- SSH `root@10.0.0.1:22` 两次同参均 `Connection timed out`（EXIT=255）
- 本机无 VPN 路由到 172.26.x.x 内网段；按 SKILL 纪律不再重试
- P1 支路 scope：部署态 jar 拉取 / 反编译 / kubectl 定位 UDC Pod → 需 VPN 后重发
- 不影响 P2 本地取证（本地 5.3.517 全套 6 jar 已在 <MAVEN_REPO>）

## 扫描覆盖
- `udc-starter-runtime-5.3.517.jar`：共 30 个 `*Controller.class`（jar tf 实测）
- 此前离线提取（docs/audit/artifacts/udc-runtime-5.3.517/）仅含 25 个 javap 文件，本次全量扫描补齐
- 微流程相关类：`MicroFlowProxyAppMicroFlow`、`UdcFunctionNodeAppService`、`MicroFlowOrgPeopleService`、`MicroFlowRestPathParser`、`MicroFlowLogUtil`、`MicroFlowRuntimeUtil`（均为 service/util，非 Controller，不入 HTTP 契约）

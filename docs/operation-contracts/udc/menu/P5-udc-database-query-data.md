# P5 — udc.database.query_data（HYPOTHESIS，不入 registry）

| 要素 | 值 |
|---|---|
| operation_id（建议） | `udc.database.query_data` |
| HTTP method | `GET`（javap 原值 `@GetMapping(value=["query-data"])`） |
| 控制器原路径 | 类级 `@RequestMapping(value=["udc-runtime/database"])` + 方法级 `query-data` → 原值拼接：`udc-runtime/database/query-data`（禁拼网关前缀；网关 service 前缀 UNVERIFIED） |
| 参数形态 | 入参 `com.seeyon.boot.starter.udcrt.dto.RuntimeDataBaseQueryDataReqDto`（Java 方法签名）。**回读 javap.txt 确认：方法块无 `RuntimeVisibleParameterAnnotations`（全文件出现次数 = 0），即入参无任何显式绑定注解（无 @MultiRequestBody/@RequestBody/@PathVariable）**。GET 携带 DTO 入参的绑定方式静态不可确证 → 入参形态 = HYPOTHESIS |
| 返回 DTO | `com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcRuntimeDatabaseQueryRespDto>`（Signature，javap L105） |
| evidence | artifact=`udc-starter-runtime-5.3.517.jar`（sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/），class=`com.seeyon.boot.starter.udcrt.controller.UdcRuntimeDatabaseController`（classfile SHA-256 `588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48`），method=`queryData`，javap.txt=`docs/audit/artifacts/udc-menu-5.3.517/UdcRuntimeDatabaseController.javap.txt`，evidence_level=VERIFIED_STATIC_BYTECODE（仅路径与返回类型层面；入参绑定 = HYPOTHESIS） |
| LIVE 回读条件 | 需目标 app 环境 + 网关 service 前缀 UNVERIFIED 确认 + 实测入参绑定（GET + DTO 的传递约定）；本轮不做 LIVE |

## 判定
- 语义核查：queryData = 运行时数据库查询，纯读 ✓
- **处置（按 main/ROUTE.md R2 停止条件）：入参无显式绑定注解 → 标 HYPOTHESIS，不入 registry-entries.md。** 路径、方法、返回 DTO 证据保留在此供后续 UDC-MERGE 参考。

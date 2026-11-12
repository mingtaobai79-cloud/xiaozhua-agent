# P2 — udc.applog.datalog_get_by_id

| 要素 | 值 |
|---|---|
| operation_id | `udc.applog.datalog_get_by_id` |
| HTTP method | `GET`（javap 原值 `@GetMapping(value=["datalog/{id}"])`） |
| 控制器原路径 | 类级 `@RequestMapping(value=["udc-runtime/app-log"])` + 方法级 `datalog/{id}` → 原值拼接：`udc-runtime/app-log/datalog/{id}`（禁拼网关前缀；网关 service 前缀 UNVERIFIED） |
| 参数形态 | `java.lang.Long id`，参数注解逐字：`@PathVariable(value="id")` + `com.seeyon.boot.annotation.ParameterInfo(value="id")`（javap L775-783） |
| 返回 DTO | `com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>`（Signature Lcom/seeyon/boot/transport/SingleResponse<...UdcEntityMonitorLogDto;>） |
| evidence | artifact=`udc-starter-runtime-5.3.517.jar`（sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/），class=`com.seeyon.boot.starter.udcrt.controller.UdcAppLogController`（classfile SHA-256 `f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775`），method=`selectAppDataById`，javap.txt=`docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt`，evidence_level=VERIFIED_STATIC_BYTECODE |
| LIVE 回读条件 | **LIVE=已开火（HUMAN 18:16 供料, 新 token exp 20:12:26 北京）；本契约在线回读 status=VERIFIED_LIVE（content≠null, 业务存在性确认）**（离线字节码证据等级 VERIFIED_STATIC_BYTECODE 保持不变）。网关前缀已确证=`/service/{appId}`(test_app=`app9000000000000000001`, 源 test2-live-route-facts.json)。开火实测（LIVE-26, 2026-09-20 10:23:55 UTC / 18:23:55 北京）: P2 `/udc-runtime/app-log/datalog/2403684453414127860`（真实 dataLog id=`2403684453414127860` 取自 P3 content[0].id, 非 C3 占位 id=1）实测 HTTP 200 + BOOT_0000/SUCCESS + identity_matches=true + **data.content≠null**（9131B, entityCaption=离职交接配置, operatorName=系统, 业务存在性确认）→ envelope/identity/content 三判据全达标 → status UNVERIFIED→VERIFIED_LIVE(业务内容确证, 上一版 LIVE-22 的 content=open 已关闭)。仅只读 GET, 不写; 参数=合法 dataLog id（占位 id=1 业务空, 真实 id=2403684453414127860 取自 P3 content[0].id）。P2 复用 registry L52 `udc.applog.select_by_id`（本轮 grep 实测在 L52）, 同路径/同 controller/同 method, MERGE 时 P2 **不新增条目** 直接复用（见 registry-entries.md L16）。证据: main/LIVE-READBACK-VERIFIED.md §LIVE-26 + scratch/live-readback-result-LIVE26-20260920.json（1871B, sha256 b99604ea57826209d17d2dfa6d9b3c9339af7f5cc892357205ba6c26c1eea462）+ MANIFEST LIVE-26 条 |

## 排除核查
- 非 C1（C1 = UdcFunctionNodeController.selectFunctionNodeTreeMetaData，微流程域占用）✓
- 语义核查：selectAppDataById 为按 id 读取单条日志，纯读，无 delete/clear/unload/set/update 写语义 ✓
- 注：同控制器 delete-all / clear-org-manager / clear-runtime-data-source-cache / unload-dynamic-app / enable-log 虽为 GET 但为写/清缓存语义，已排除（见 SCAN.md 排除项清单）

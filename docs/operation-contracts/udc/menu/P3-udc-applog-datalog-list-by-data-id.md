# P3 — udc.applog.datalog_list_by_data_id

| 要素 | 值 |
|---|---|
| operation_id | `udc.applog.datalog_list_by_data_id` |
| HTTP method | `GET`（javap 原值 `@GetMapping(value=["datalog/list-by-dataid/{dataId}"])`） |
| 控制器原路径 | 类级 `@RequestMapping(value=["udc-runtime/app-log"])` + 方法级 `datalog/list-by-dataid/{dataId}` → 原值拼接：`udc-runtime/app-log/datalog/list-by-dataid/{dataId}`（禁拼网关前缀；网关 service 前缀 UNVERIFIED） |
| 参数形态 | `java.lang.Long dataId`，参数注解逐字：`@PathVariable(value="dataId")` + `com.seeyon.boot.annotation.ParameterInfo(value="dataId")`（javap L814-822） |
| 返回 DTO | `com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>`（Signature Lcom/seeyon/boot/transport/ListResponse<...UdcEntityMonitorLogDto;>） |
| evidence | artifact=`udc-starter-runtime-5.3.517.jar`（sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/），class=`com.seeyon.boot.starter.udcrt.controller.UdcAppLogController`（classfile SHA-256 `f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775`），method=`selectAppDataByDataId`，javap.txt=`docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt`，evidence_level=VERIFIED_STATIC_BYTECODE |
| LIVE 回读条件 | **LIVE=已开火（10:03/14:51/18:17 三批 token 窗口内, 历史阻塞已解除）；本契约在线回读 status=VERIFIED_LIVE**（2026-09-20 10:35:33 开火 HTTP 200 + BOOT_0000/SUCCESS + identity_matches=true；二次开火 2026-09-20 15:04 北京（07:04:42 UTC）P1/P3/P4 3/3 PASS，证据 main/LIVE-READBACK-VERIFIED.md LIVE-19 段 + scratch/live-readback-result-LIVE19-20260920.json，权威源 main/LIVE-READBACK-VERIFIED.md + scratch/live-readback-result.json；离线字节码证据等级 VERIFIED_STATIC_BYTECODE 保持不变）。网关前缀已确证=`/service/{appId}`(test_app=`app9000000000000000001`, 源 test2-live-route-facts.json)。2026-09-19 16:19 实测：main/test2-live-credential.json remaining=-9324s 与旧共享 test2-web-credential.json remaining=-96645s，两份皆 EXPIRED；harness live-readback.py 双结构已对齐（LIVE-4/R13：新结构 cookie_header_template+sy_access_token/tk_exp/sy_uid + 旧结构 headers.Cookie 均支持，DRY_RUN 自检 0 HTTP 通过），token 落盘即 gate-check+DRY_RUN 预演开火。仅离线改文字不发 HTTP；HUMAN 后续提供新 token 后方可执行只读 GET。参数=合法 dataId；仅只读 GET。详见 main/NEEDS-HUMAN-live-residual2.md（P1/P3/P4 已 LIVE 回读, 现行缺口件仅列 P2/request-body） |

## 排除核查
- 非 C1（C1 = UdcFunctionNodeController.selectFunctionNodeTreeMetaData，微流程域占用）✓
- 语义核查：selectAppDataByDataId 为按 dataId 列表读取监控日志，纯读 ✓

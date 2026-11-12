# gateway.route｜xiaozhua test2 网关路由契约（C1 正式格，2026-09-26）

> 基线：docs/capability/ROADMAP-v2.md。原料=u4-gateway S1–S4 证据件（VERDICT PASS，
> routes-evidence.md 逐件 SHA 登记）+ 09-24/25 本线部署/运行面 LIVE。
> C1 首派曾被 implementer 判重叠撤销（G1 批量格），本格为正式补位（main 领地表已划归 gateway）。

## 1. Capability
`gateway.route.resolve` — 从前端 URL 解析到后端服务的完整路由链（非写能力，属**路由事实**，
供 deploy_plan 拼址与 adapter 构造网关请求）。

## 2. Version
- 入口 ingress：nginx `lowcode-test`（101.200.221.95:80/443），剥 `/service/` 前缀 rewrite 至
  `ctp-webapi-gateway:80`（10.0.0.1，ClusterIP）。
- 网关镜像/jar：`ctp-webapi-gateway` jar 131013470B 逐位=冻结基线 r39b/r52（S1 实测 PRE==POST）。
- xiaozhua Canonical=5.3.517（UDC 侧）；网关本体版本独立，UNVERIFIED。

## 3. Input
无（路由表为静态事实）。消费面：`{gateway_base}/service/{appId}/{target_path}`；
`appId=udc` 公共命名空间实测可用（entity / page-info / runtime 族走 `/service/udc/...`，09-24/25 LIVE；**路径须含控制器类级前缀**，见 §4）。

## 4. Required（拼址规则）
- URL 形态：`/service/{appId}/{path}`（S4 已证 ingress+rewrite）；空 appId → server_500「服务异常」。
- **拼址必须带上控制器类级前缀（09-27 矫正）**：`deploy-normal` 真实可拼= `/service/udc/runtime/deploy-normal`
  （类级 `@RequestMapping("udc/runtime")` + 方法级 `deploy-normal`）；POST 实证 `200 BOOT_0000 + deployId`（09-27）。
  **旧的裸 `/service/udc/deploy-normal` 是错误路径**——09-27 三面 GET 探针复核：`/service/udc/deploy-normal` → **404 Not Found**（无映射），
  而 `/service/udc/runtime/deploy-normal` → **405 Method Not Allowed**（映射在、仅 POST-only），
  对照 `GET /service/udc/entity` → 405（已知可用面）证明探针判别力成立。
  故"`/service/udc/deploy-normal` 实测 BOOT_0000"的旧记录**作废**（疑为当时路径串位，非契约变更）。
- `{appId}` 段只吃**已注册命名空间/应用**：`/service/udc/...` 承载 udc-web 设计态控制器族（entity / page-info / runtime / application…）；
  `/service/udc-runtime/...` 直挂被 nginx 403——**udc-starter 的 udc-runtime 面只认应用前缀**（`/service/{app}/udc-runtime/...`），meta-data/data/serial 全族如此（09-24/25 双次实测）。
- 白名单事件（运维事实）：09-24 17:0x~09-25 15:3x 本机出口 IP 被 nginx 403（含登录端点），根路径 200——
  **IP 级策略**，非契约变更；恢复后全链无改动复通（09-25 15:39 续期+复测 BOOT_0000）。

## 5. Execution
读面：S1/S2 证据（pod/svc/actuator/路由样例）+ 09-24 登录端点 `/service/ctp-user/auth/token`（POST 免鉴权）
+ 本会话网关 cookie 鉴权（SY_ACCESS_TOKEN cookie 经 nginx→gateway JWT 校验，HmacSHA256 链=S2/S3 字节码级）。

## 6. Side Effects
无（事实格）。路由表变更属运维动作，不在本能力域。

## 7. Known Constraints
- `lb://{appId}` 运行时绑定 **UNVERIFIED**（U4 原结论：网关路由 ID/谓词在 ConfigMap，但服务发现绑定未活体确证）。
- cip-openapi-gateway 路由样例仅 tail-50 日志观察（部分路由），全量路由表 UNVERIFIED。
- nginx 出口 IP 策略随时可收紧（已发生一次），BLOCKED 先测 IP 面再疑契约。

## 8. Evidence
- STATIC+LIVE：u4-gateway 两件（proposal 6324B / routes-evidence 9590B，VERDICT PASS，SHA 登记）
- LIVE（09-24/25）：/service/udc/entity、/service/udc/page-info/* 全 BOOT 级响应；
  udc_runtime 族走应用前缀 200（serial/draft/role/node-tree/data/query 五面）。
- LIVE（09-27）：`/service/udc/runtime/deploy-normal` = 真拼址（POST 200 BOOT_0000 + deployId；GET 405 反证映射在）；
  裸 `/service/udc/deploy-normal` GET 404 → 旧记录作废（见 §4）。
- 本格 09-25 15:39 登录端点复通 traceId 级。

## 9. Verified
VERIFIED_STATIC + LIVE（拼址规则+白名单面）；`lb://` 绑定、全量路由表、网关本体版本 = UNVERIFIED。

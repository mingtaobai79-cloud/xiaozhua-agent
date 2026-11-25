# 网关前缀活体确证 + 部署态差异（test2, 无凭据 GET, 只读）

取证时间：2026-09-17T15:13Z · target: https://lowcode-test2.example.com · app=app9000000000000000001
方式：公网 GET（无需登录即可拿到业务 envelope）；只读；不打印凭据。

## 网关 service 前缀活体确证（与本地 5.3.517 静态分列，不混写）

本地 5.3.517 控制器 @RequestMapping 原文（静态事实，VERIFIED_STATIC_BYTECODE）：
- UdcFunctionNodeController → `udc-runtime/meta-data/select-function-node-tree/{appName}`
- UdcDataTypeController → `udc-runtime/datatype/getAll`
- UdcAppLogController → `udc-runtime/app-log/datalog/{id}`

test2 活体路由探测（部署态事实）：
| 探针 | 活体响应 | 判定 |
|---|---|---|
| GET /service/udc-runtime/datatype/getAll | status=3 code=server_404 "udc-runtime 服务不存在，请重启服务或重新发布应用后再试！" data=null | 该 service 命名域在 test2 **未部署** |
| GET /service/udc-runtime/meta-data/select-function-node-tree/{app} | 同上 server_404 udc-runtime 不存在 | 未部署 |
| GET /service/udc/datatype/getAll | status=2 code=BOOT_1006 → data.content.redirectUrl=https://uatsso.客户方.com/esc-sso/oauth2.0/... | 网关 service `udc` **存在**，进 SSO OAuth 鉴权墙 |
| GET /service/udc/meta-data/select-function-node-tree/{app} | 同上 BOOT_1006 SSO redirect | 存在 + 鉴权墙 |
| GET /service/{app}/udc/datatype/getAll | 同上 BOOT_1006 SSO redirect | 客户侧同走 SSO 墙 |

## 精确结论

1. **网关 service 前缀 = `udc`（test2 部署态确证），不是本地静态写的 `udc-runtime`。**
   本地 5.3.517 控制器路径段 `udc-runtime/...` 与 test2 实际网关 service 名 `udc` 不一致 →
   属"本地 5.3.517 vs 服务器部署版本"的路由差异，按纪律分列标注，不混写、不据活体改写静态契约路径原文。
   registry 中 C1/C2/C3 的 `path` 保持控制器原值（`udc-runtime/...`），网关 service 名段另记活体确证值 `udc`（UNVERIFIED→LIVE 确证的是 service 名，非 controller 路径段）。
2. **A2 LIVE PASS 卡点 = SSO OAuth 登录墙**：`/service/udc/...` 未登录时被网关 302 到
   `uatsso.客户方.com/esc-sso/oauth2.0/...`（code=BOOT_1006），拿不到业务 data。
   穿透该墙需 test2 UDC 只读登录凭据（用户名/密码 或 SSO session）；.env 无 XIAOZHUA_APP_TOKEN / APP_COOKIE。
3. **identity_matches 判读**：三条候选双发字节一致（sha 相同）但 data=null + code=server_404/BOOT_1006，
   属 layer.py 的 BUSINESS_NOT_FOUND / 鉴权墙边界，**不等于业务成功，不判 A2 PASS**。
4. udc-runtime service 在 test2 未部署 → 即便拿到凭据，`udc-runtime/*` 也可能仍 server_404；
   真正可读的 service 是 `udc`（存在），其内部路径段是否含 `meta-data`/`datatype`/`app-log` 需穿透 SSO 后确认。

## 缺口（精确）
- 缺：test2 UDC 只读登录凭据（穿透 uatsso SSO OAuth 墙）。→ NEEDS-HUMAN（凭据/授权类）。
- 非缺：网关 service 名（已活体确证 = udc）、路由存在性、鉴权墙形态。

# 应用域前端调用面（设计器已加载 chunk 实测提取）

- 环境：test2（`https://<gateway-host>`）
- 采集：2026-10-22，CDP 9250 附着在「示例应用」应用（appId `9000000000000000001`）设计器页，
  从 `performance.getEntriesByType('resource')` 取已加载 chunk，逐个 fetch 正则提取 `/udc/...` 字面量 + 邻近调用动词。
- 证据：`evidence/app-frontend-surface-2026-10-22.json`（按 bundle 分组，verb 取自调用点上下文）

## 1. 前端真的这么调（19 条，verb 已定）

| verb | path（逐字） | 出处 chunk |
|---|---|---|
| POST | `/udc/deployment/latest-test-info` | `src_pages_app-design_basic-info_index_tsx ...` |
| POST | `/udc/application/search/front-detection` | `src_redux_store_ts` |
| GET | `/udc/sandbox/delta-build-info/{appId}` | `src_redux_store_ts` |
| POST | `/udc/deployment/app-delta-deploy` | `src_redux_store_ts` |
| POST | `/udc/runtime/expect-deploy-time` | `src_redux_store_ts` |
| POST | `/udc/application/dependent-application/delete-by-ids` | `... basic-info_index_tsx` |
| POST | `/udc/front-log/create` | `src_redux_store_ts` |
| POST | `/udc/microflow/disable-last-version-metadata` | `src_redux_store_ts` |
| POST | `/udc/micro-flow-macro/select-items` | `src_redux_store_ts` |
| GET | `/udc/micro-flow-macro/select/{id}` | `src_redux_store_ts` |
| POST | `/udc/page-info/base-info/create` | `src_redux_store_ts` |
| POST | `/udc/page-info/base-info/update` | `src_redux_store_ts` |
| POST | `/udc/page-info/delete-by-conditions` | `src_redux_store_ts` |
| GET | `/udc/page-info/select-by-appId/{appId}` | `src_constants_design_page-type_ts ...` |
| POST | `/udc/graphql` | `src_redux_store_ts` |
| GET | `/udc/application/datadictionary/...` | `src_redux_store_ts` |
| GET | `/udc/file/download?storageKey=` | `ui.js`（框架层） |
| GET | `/udc/app-design`（模块入口） | `seeyon.vendor.global ...-sdk.js` |
| GET | `/udc/refer-config/list` | `src_redux_store_ts` |

判读要点：

- **「测试」入口** = `POST /udc/deployment/app-delta-deploy`（增量部署，body 为 deployParamDto），
  配 `POST /udc/runtime/expect-deploy-time` 预估耗时 + `GET /udc/sandbox/delta-build-info/{appId}` 轮询进度。
- **「发布」入口**不在本页 chunk 内（`app-online`/`deploy-normal` 关键字在已加载 40 个 chunk 中 0 命中），
  发布动作由主壳（portal）发起；后端面已有 `udc.deploy.normal`（`udc/runtime/deploy-normal`）与
  `udc.publish.deploy_info` 两条登记，前端字面量仍属 UNVERIFIED。
- 写面字面量（delta-deploy / delete-by-ids / front-log/create / disable-last-version-metadata /
  page-info create|update|delete）**只登记不发**：本轮零写操作。

## 2. 服务边界（实测反证，不是推测）

`/service/udc/sandbox/flexible/test-status` → **404**（`Not Found`，网关 udc 服务无此映射）。
`/service/sandbox/flexible/test-status` → **200 + `code=server_404`
`"sandbox 服务不存在，请重启服务或重新发布应用后再试！"`**。

结论：弹性部署（`sandbox/flexible/*`：create/delete/restart/test-status/select-deployment-page）
归属 **独立微服务 `sandbox`**，不是 `udc` 的子路径；test2 当前未部署该服务 → 该面在 test2 为
BLOCKED（服务缺席），不是路径笔误。已实测确认的 sandbox 侧入口仅 `udc/sandbox/*`（delta-build-info、
system/config/is-deploy-war、app/search），二者不同服务，禁止混前缀。

## 3. 与已登记契约的关系

| 前端现调 | registry 现状 |
|---|---|
| `POST /udc/deployment/app-delta-deploy` | 无（本轮新增只读旁路，写面仍 DENIED） |
| `POST /udc/deployment/latest-test-info` | 本轮新增 `udc.deployment.latest_test_info` |
| `POST /udc/application/search/front-detection` | 本轮新增 `udc.application.front_detection` |
| `GET /udc/sandbox/delta-build-info/{appId}` | 本轮新增 `udc.sandbox.delta_build_info` |
| `GET /udc/sandbox/system/config/is-deploy-war` | 本轮新增 `udc.sandbox.is_deploy_war` |
| `POST /udc/sandbox/app/search` | 本轮新增 `udc.sandbox.app_search` |
| `POST /udc/deployment/app-online`（发布） | 无前端字面量；`udc.deploy.normal` 已有后端面 |

## 4. 采集方法可复现

```
# 抓页面自身请求（只监听，不注入）
python tools/core/application/cdp_net_capture.py --port 9250 \
  --match app-design --seconds 30 \
  --out <HERMES_HOME>/cache/scratch/app-design/net.json
```

注意：**不要对设计师页发 Page.reload** —— 该页是 shell 内 child-frame 路由，
单独 reload 会落到 `chrome-error://chromewebdata/`（实测），要抓导航流量请走
应用列表→点击「设计」的真实入口。

## 1.1 弹性部署页 chunk 的字面量（VERIFIED_STATIC_BYTECODE，未发起）

来源：`src_pages_udc_sandbox_pages_elastic-deployment_index_tsx.<hash>.js`（服务端已下载到 scratch，逐字提取）

| verb | path |
|---|---|
| POST | `/udc/sandbox/app/search` |
| POST | `/udc/sandbox/flexible/create-deployment` |
| POST | `/udc/sandbox/flexible/delete-deployment` |
| POST | `/udc/sandbox/flexible/restart-deployment` |
| POST | `/udc/sandbox/flexible/select-deployment-page` |
| POST | `/udc/sandbox/flexible/test-status` |
| GET | `/udc/sandbox/system/config/is-deploy-war` |

判读：写法上带 `/udc/` 前缀，但**服务归属是 `sandbox`**（实测 `/service/udc/sandbox/flexible/test-status`
404、`/service/sandbox/flexible/test-status` 回 `server_404`「sandbox 服务不存在」）。即前端用的是
同源网关相对路径，网关按 **`/service/{service}/...`** 路由，`sandbox` 与 `udc` 是两个服务。
该族在 test2 未部署 → 全部不可用；写族 create/delete/restart 一律 DENIED，未发起。

`application-test` 页 chunk 只命中 `/udc/sandbox/app/search` 与 `/udc/sandbox/system/config/is-deploy-war`
两条（测试页复用沙箱列表与 war 形态判断），测试动作本身由 `POST /udc/deployment/app-delta-deploy` 触发。

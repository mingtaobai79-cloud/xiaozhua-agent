# Nacos v2 只读旁路探测（A2 缺口② Long 型 target 来源 · 封死证据）

取证：main 亲自 · 2026-09-18 07:5x CST · 只读 GET · 不打印业务明细/敏感值（仅 code + data 摘要）
实例：mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848（无鉴权 Open API）

## 结论：Nacos 只读路径封死（不能解 A2 缺口②）

### 1. 实例是 Nacos 2.x（修正上轮"v1 404 = 走不通"的以 v1 为据判断）
- v1 Open API：`/nacos/v1/cs/config`、`/nacos/v1/console/ns/list`、`/nacos/v1/ns/operator/metrics`
  → metrics 探活 200（实例可达），但 cs/config 与 console/ns/list 全 **404 Not Found**（Spring Boot 错误页）。
- v2 端点：**`/nacos/v2/cs/config` 通道可达**，返回 v2 协议 JSON（非 404）：
  `{"code":20004,"message":"resource not found","data":"config data not exist"}`。
  → 说明 Nacos 2.x 的 v2 cs/config 开放了只读查询，v1 只是未暴露（2.x 默认或网关策略）。

### 2. 目标配置在 Nacos 里查不到（全组合 20004）
- dataId=`app9000000000000000001` × group∈{seeyon, DEFAULT_GROUP, SEYYON} × tenant∈{空, seeyon-test2, test2, seeyon}
  → 全部 `code=20004 config data not exist`。
- 即该 customer applicationId 形态**不是 Nacos 里的 dataId**（test2 应用配置不用 applicationId 作 dataId，
  或用别的命名形态），Nacos 查不到 test2 数字型应用/实体 id。

### 3. 无法枚举真实 dataId（无配置列表端点）
- `/nacos/v2/console/ns/list`、`/nacos/v2/console/ns/page`、`/nacos/v2/openapi/configs`、
  `/nacos/v3/openapi/config`、`/nacos/actuator` → 全 **404**。
- 无 list/枚举端点暴露，不能靠遍历 dataId 找到 test2 数字型 id（也不应盲猜 dataId）。

## 对 A2 的影响
- A2 缺口②（Long 型 target 来源）的 Nacos 只读旁路**封死**：v2 通道虽可达，但目标配置不存在 + 无枚举端点。
- A2 三条活体/旁路路径现全证据化阻塞：
  ① P1 部署态 jar（SSH 10.0.0.1 无 VPN 路由，两次同参超时）；
  ② test2 活体回读（只读 token 过期 exp=1789660805，.env 无 APP_TOKEN/APP_COOKIE）；
  ③ Nacos 只读旁路（v1 404 + v2 通道通但目标配置不存在 + 无枚举端点）。
- A2 维持 UNVERIFIED；解阻仅余 **P1（VPN 恢复取部署态 jar）+ 新 test2 只读 token**，均需人工。

raw 命令脚本（只读）：main/_nacos_v2_probe.sh、main/_nacos_v2_cfg.sh（会话目录）。

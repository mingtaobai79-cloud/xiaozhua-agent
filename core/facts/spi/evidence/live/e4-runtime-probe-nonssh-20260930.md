# e4 — 非 SSH 运行态通道有界只读探测记录（P4b 步2；3 发硬上限，全 GET，0 凭据）

> 采集会话: implementer / P4b
> 时钟口径: 全部 `date -u`（UTC）。注: 消息 created_at 标 +00:00 实为 UTC+8。
> 探测纪律: no_retry_bombing —— 同批 3 发后即停，未重试、未换分支、未扩 SSH、未开写面。
> 请求形态: 均 `curl -sS -g --max-time 12 <GET url>`，**0 header 凭据、0 body**。

## 探测逐发记录

### P1 — 网关根（C1 business/router）
- 时间: 2026-09-30T20:20:41Z（UTC）
- 端点: `GET https://lowcode-test2.example.com/`
- 结果: **CURL_EXIT=35 — Recv failure: Connection was aborted**（TLS 握手被中断）
- 判级: **明确问题（通道不可达/传输失败）**；非 200、非空结果、非加载链证据。
- 备注: 历史既有事实（TASK-GOAL 环境段）曾记 GET / → 301；本会话内 TLS 中断属**探测面可达性不稳定**，非"网关不存在"或"未加载 SPI"。

### P2 — Nacos naming 服务清单（public 命名空间）（C3）
- 时间: 2026-09-30T20:20:42Z（UTC）
- 端点: `GET http://mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848/nacos/v1/ns/service/list?pageNo=1&pageSize=20`
- 结果: **CURL_EXIT=56 — Recv failure: Connection was reset**
- 判级: **明确问题（通道不可达/连接重置）**；未获得任何服务实例清单。

### P3 — Nacos naming 服务清单（tenant=xiaozhua-test2）（C3）
- 时间: 2026-09-30T20:20:42Z（UTC）
- 端点: `GET http://mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848/nacos/v1/ns/service/list?pageNo=1&pageSize=20&namespaceId=xiaozhua-test2`
- 结果: **CURL_EXIT=56 — Recv failure: Connection was reset**
- 判级: **明确问题（通道不可达/连接重置）**；未获得 xiaozhua-test2 运行态实例信息。

## 探测结论（步2 产出）
- **3 发皆未获得运行态 SPI 加载/注册/调用证据**；且皆未获 HTTP 200 正文（传输层失败）。
- 对照既有: Nacos **config 组** `GET /nacos/v1/cs/configs?...tenant=xiaozhua-test2` 曾于 2026-09-30T19:28Z 达 200（e2，本线既有、**禁再触碰**）；本次 Nacos **naming 组** `/ns/service/list` 连接重置。二者差异属**探测面（端点/会话网络）**，不构成被测系统运行态结论。
- 即便 naming 面可得，亦仅"服务实例存活"粒度，**不证 SPI 加载链**（见 e3 §C3 / 本格 §7）。
- 凭据 0 入件: 本探测未携带、未引用任何 username/password/token；响应体无内容（传输失败）。

## 停手声明（步3 纪律）
- 达 3 发硬上限即停：未重试、未扩到 SSH/kubectl、未绕 host key、未开写面（zzprobe/jar 上传/Nacos 改配）。
- 负结果事实（供 spi-ext-runtime.md §9）: **非 SSH 只读通道不足以观测 test2 运行态 SPI 加载链；G2 运行态子面仍未达成，需 P4a 人工解阻（可信 host key / 可信 kubeconfig 后的 pod logs）。**
- 若 main 判定"必须写面（如部署 zzprobe SPI jar 后触发调用）"方能推进 G2 运行态子面，本线仅提设计方案、不动手（见 RESULT 附报）。

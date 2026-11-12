# SPI-EXT-LIVE-01 — SPI 插件在 test2 运行态的加载/注册表现（LIVE 事实格）

> 事实格 ID: SPI-EXT-LIVE-01
> 建模口径: SPI 扩展点/插件契约/实现边界（不按 UDC 模式套）
> 本格等级面: 配置面 = LIVE READONLY（快照/新鲜复核）；运行态加载 = 见 §9 Verified
> 关联冻结格: `spi-ext-registration.md`（SPI-EXT-REG-01）、`spi-ext-loading.md`（SPI-EXT-LOAD-01）—— 观测点合法性来自 P1 §5 加载链路（VERIFIED_STATIC_BYTECODE）
> 阶段: P2（终格）

## 1. Capability（本事实格主张的能力）
描述 SPI 插件机制在 test2 环境**运行态/配置态**的可观测表现：平台是否启用 SPI 加载开关、是否声明并加载 SPI 插件 jar、SPI 实现类是否被动态注册进 Spring 容器并广播注册事件。
主张边界: 仅登记**实际观测到的**配置/日志事实；配置启用 ≠ 插件已加载 ≠ 实现被调用。

## 2. Version（版本绑定）
- 观测目标环境: `tenant=seeyon-test2`，`group=seeyon`，`dataId=public`（Nacos 配置面）；对照 `tenant=seeyon-uat`。
- 快照采集时间: 2026-09-22（源件记录）；新鲜复核时间: 2026-09-30T19:28Z（date -u 实测，见 e2）。
- 与 P1 契约版本单元关系: P1 字节码为 5.3.x 家族，客户模块声明 `platform.version=3.10.1`（本地无 3.10.1 家族，见 P1 §4.5 缺口）。**本格运行态证据若成立，对应 test2 实际部署版本=以日志/配置面实测为准，对 3.10.1 的适用性 UNVERIFIED。**

## 3. Input（输入/观测面）
- 配置面（只读）: Nacos `dataId=public` (test2/uat)，键路径 `seeyon.spi.enable`、`seeyon.spi.spi-plugins` / `spiPlugins`、`seeyon.dynamic.loader.*`。
- 运行态（只读，若步3 执行）: `kubectl logs` of ctp-user / cip-connector pods in ns=lowcode-test，grep SPI 加载关键串。
- 输入源快照件: `docs/audit/artifacts/u6-nacos-config/raw-02-nacos-configs.md` (sha256 81b2d7a4…)，逐字摘录见 evidence/live/e1。

## 4. Required（启用条件 / 前置）
- 来自 P1 §5 加载链路（VERIFIED_STATIC_BYTECODE）: `SPIProperties.spiPlugins` 默认为空 → `initialize()` 遇空即 return（短路，不加载任何插件 jar）。
- 故"插件被加载"的必要条件 = 配置面存在非空 `seeyon.spi.spi-plugins` 声明；仅 `enable=true` 不足。

## 5. Execution（执行/观测链路）
1. Nacos GET `tenant=seeyon-test2 dataId=public` → 读 `seeyon.spi.enable`、`spi-plugins`。
2. （步2）同通道新鲜复核 enable 现值与 spi-plugins 是否仍缺。
3. （步3）`kubectl get pods -n lowcode-test` 定位 ctp-user/cip-connector → `kubectl logs --tail` grep：`未开启SPI插件加载机制，忽略SPI实现的加载` / `SPIApplicationRunListener` / `SPIJarLoader` / `registerSingleton` / `SPIProviderRegisterEvent` / `获取的spiPlugins数据有错`。
- 命中加载/注册行 或 命中"未开启…忽略加载"短路行 = 运行态 SPI 加载链**被执行**（后者为负向命中，照实标注未加载插件）。

## 6. Side Effects
- 全为只读观测（Nacos GET / kubectl logs），0 写；无 zzprobe 应用创建、无 jar 上传、无 Nacos 改配（写面越界，须先报设计方案获 main 批准）。
- 凭据 0 入件：password/artifactory username 一律 `<REDACTED>` 或仅键名。

## 7. Known Constraints
- **配置启用 ≠ 部署成功 ≠ 运行态被调用**（沿用 P1 冻结格约束）。`enable=true` 只证配置，不证加载。
- 覆盖面缺口: 只读快照捕获 8 个 dataId 块，均未声明 spi-plugins；未捕获服务级/插件级 dataId ⇒ 不能全局断言"test2 无插件清单"，只能断言"已捕获配置面无声明"。该缺口 = UNVERIFIED。
- "插件未加载"若由空 spi-plugins 推断，推断源 = P1 VERIFIED_STATIC_BYTECODE（`spiPlugins` 空即 return），非运行态直接观测。
- HTTP 200 / 空结果不算 PASS；快照 vs 新鲜值若不一致以新鲜为准并登记。

## 8. Evidence
- `core/facts/spi/evidence/live/e1-nacos-spi-config-snapshot-20260922.md` — 配置面逐字摘录（2026-09-22 快照；块头 L841 / L964-965 spi.enable=true / L997-1006 dynamic.loader；spi-plugins 全文件 grep 0 命中；对照 uat L575-576）。源件 sha256 `81b2d7a44dabe3a229f2444870201f707957aba0d0178ed28bd7893749ddd145`。
- `core/facts/spi/evidence/live/e2-nacos-spi-config-fresh-20260930.md` — 配置面**新鲜只读复核**（本地直连 MSE Nacos，不经 SSH）。`date -u` 实测 2026-09-30T19:28Z（UTC）。端点 `GET /nacos/v1/cs/configs?dataId=public&group=seeyon&tenant=seeyon-test2` → HTTP 200，正文 13589B/225行；`seeyon.spi.enable=true`（L123-124）、`spi-plugins`/`spiPlugins` grep **0 命中**、dynamic.loader 同构（batchSize5/lruSize200/type maven）。辅助 `GET /nacos/v1/console/namespaces` → 200（seeyon-test2 configCount=74）。敏感值 0 入件（全 `<REDACTED>`）。
- 步2 新鲜复核: **已达成**（本地直连通道，与 2026-09-22 快照一致，无漂移；现值以 e2 为准）。
- 步3 运行态日志: **未达成**（见 §10；SSH 跳板 host-key 阻塞，main 定性为需人工项，implementer 不绕过、不扩写面）。无运行态加载/注册正/负向命中。

## 9. Verified
- **判级（四类分写）:**
  - 配置面 = **LIVE READONLY（新鲜复核，2026-09-30T19:28Z）**；`enable=true` **只证配置，不证加载**（沿用 §7 约束）。
  - 运行态加载/注册日志 = **未测试**（步3 通道阻塞，非命中性负结果）。
  - 无 HTTP 200/空结果冒充 PASS。
- 已证:
  - test2 配置面 `seeyon.spi.enable=true` — 新鲜复核达成（e2，本地直连 GET 正文 L123-124）；与 2026-09-22 快照一致，无漂移。
- 未证 / UNVERIFIED:
  - test2 新鲜配置正文**未见** `spi-plugins`/`spiPlugins` 声明（e2 grep 0 命中，实测）→ 覆盖面缺口仍 UNVERIFIED：不能全局断言"test2 无插件清单"，仅断言"已捕获 dataId=public/group=seeyon 无声明"。
  - 由 P1 链路推断: spiPlugins 空 ⇒ 加载短路 ⇒ **推断运行态可能未加载任何 SPI 插件**；**推断源 = P1 VERIFIED_STATIC_BYTECODE**（`SPIProperties.spiPlugins` 空 → `initialize()` return），非运行态直接观测，待步3 日志面坐实。
  - 运行态 SPI 加载/注册日志证据: **未获取**（步3 阻塞）⇒ 登记"运行态未见 SPI 加载日志证据（探测通道不可达，非命中性负结果）"。
- 本节反映步1（落盘）+ 步2（新鲜复核达成）；运行态面见 §10。G2（运行态 LIVE 加载证据）仍未达成。

## 10. 通道状态登记 (OBSERVATION — 步2 已达成 / 步3 阻塞)
- **步2 新鲜复核（已达成）**: 走 main 门3 实测的替代通道——本地直连 `mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848`（解析 10.0.0.1），**无需 SSH 跳板、无需 accessToken**。`GET /nacos/v1/cs/configs?dataId=public&group=seeyon&tenant=seeyon-test2` → 200（见 e2）。本轮共 3 发只读 GET（硬上限 4 内），0 写、0 凭据入件。
- **步3 运行态日志面（仍阻塞，需人工）**: `kubectl logs` of ctp-user/cip-connector（ns=lowcode-test）需经 SSH `root@10.0.0.1`。实测 TCP/22 OPEN，但 `ssh` 报 **Host key verification failed**（known_hosts 已有该主机 2 条 key，服务器呈现 key 不匹配）。
- 处置: **未绕过**（不对已知主机强行 `StrictHostKeyChecking=no` 覆盖密钥，防潜在 MITM/密钥漂移）。main 门3 已定性该面为需人工项，implementer 不自行解阻、不扩到 SSH、不开写面。
- 影响: **G2 运行态 LIVE 加载证据仍未达成**（配置面新鲜复核已达成并可审；运行态面 UNVERIFIED/未测试）。
- 报 main（步3 人工解阻方案）: 人工/看门狗确认可信后刷新 10.0.0.1 host key 或提供可信 kubeconfig 直连；解阻后单独重派步3（kubectl logs grep，硬上限 3 发）。若只读日志仍不足判"是否加载插件"，再议写面方案（须先报设计获批准）。

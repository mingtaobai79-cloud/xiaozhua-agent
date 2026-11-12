# e2 — Nacos SPI 配置面·新鲜只读复核 (test2) — LIVE READONLY

> 观测面: Nacos 配置面（本地直连，不经 SSH 跳板）
> 采集时间: 2026-09-30T19:28Z（`date -u` 实测，UTC）
> 通道: 本地直连 `mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848`（解析 10.0.0.1；只读 GET，未提供任何 accessToken 亦未抄任何凭据）
> 端点与请求形态: `GET http://mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848/nacos/v1/cs/configs?dataId=public&group=seeyon&tenant=xiaozhua-test2` → HTTP 200，正文 13589 B / 225 行
> 辅助面: `GET /nacos/v1/console/namespaces` → HTTP 200（namespace 列表，`xiaozhua-test2` configCount=74，坐实 dataId=public/group=seeyon 读取形态有效）
> 凭据纪律: password / username / license-key / license-info / accessToken / artifactory URL 等敏感值一律 `<REDACTED>`，0 值入件（仅保留键名与结构值 true/false/整数/type）。

## 1. 逐字摘录（仅 SPI 相关键，敏感值脱敏）
```
# L123-124（seeyon 块内）
  spi:
    enable: true

# L156-163（seeyon.dynamic.loader 块）
  dynamic:
    loader:
      batchSize: 5
      lruSize: 200
      type: maven
      maven:
        releaseUrl: <REDACTED-URL>
        snapshotUrl: <REDACTED-URL>
        username: <REDACTED>
        password: <REDACTED>
```

## 2. spi-plugins / spiPlugins 命中
- 命令: `grep -inE 'spi-plugins|spiPlugins' <正文>` → **命中 0 行**。
- 结论: 新鲜配置正文中，`seeyon.spi.spi-plugins` / `spiPlugins` **仍未声明**（与 2026-09-22 快照一致）。

## 3. 与 2026-09-22 快照（e1 / raw-02-nacos-configs.md）差异比对
| 键 | 2026-09-22 快照 (e1) | 2026-09-30T19:28Z 新鲜 (e2) | 差异 |
|---|---|---|---|
| `seeyon.spi.enable` | `true`（L964-965） | `true`（L123-124） | 无变化（现值=true） |
| `seeyon.spi.spi-plugins`/`spiPlugins` | 全文件 0 命中 | 0 命中 | 无变化（仍未声明） |
| `seeyon.dynamic.loader` | batchSize5/lruSize200/type maven/releaseUrl+snapshotUrl | 同构 | 无变化 |

- 现值优先原则: 以本件（2026-09-30 新鲜）现值为准；本轮差异=「与快照一致，无漂移」。

## 4. 分级说明（供格引用）
- 本件 = 配置面 **LIVE READONLY 新鲜复核**（非 2026-09-22 快照）。
- `enable=true` 只证配置开关，不证插件被加载，不证 SPI 实现被调用。
- 运行态加载/注册日志面: 本件未覆盖（步3 kubectl 日志面另见格 §9/§10，通道阻塞、未测试）。

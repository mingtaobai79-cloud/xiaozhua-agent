# E1 — test2 SPI 配置面 LIVE 只读快照摘录 (LIVE READONLY SNAPSHOT)

- 观测面标识: `nacos-config-snapshot-20260922` (通道 = Nacos HTTP GET only, 0 写自证见下)
- 采集日期 (源件记录): 2026-09-22
- 源文件 (在盘逐字摘录来源): `docs/audit/artifacts/u6-nacos-config/raw-02-nacos-configs.md`
- 源文件绝对路径: `<XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/u6-nacos-config/raw-02-nacos-configs.md`
- 源文件 sha256 (本会话 sha256sum 实测): `81b2d7a44dabe3a229f2444870201f707957aba0d0178ed28bd7893749ddd145`
- 源文件大小: 56628 B / 1163 行
- 摘录复算方式: `sha256sum <上列路径>` + `sed -n '841p;964p;965p;997,1006p;575,576p' <路径>`
- 证据等级: LIVE READONLY (配置面快照；值全 `<REDACTED>`，凭据 0 入件)
- 落盘 UTC: 见本件 git/文件 mtime（本会话于步1 本地 0 网络写入）

## 逐字摘录 — CONTROL-xiaozhua-test2 / dataId=public / tenant=xiaozhua-test2

块头 (源件 L841，该块为文件最后一个 `##########` 块，起始 L841，至文件末 1163 行无其它块头):
```
########## CONTROL-xiaozhua-test2 dataId=public group=seeyon tenant=xiaozhua-test2 ##########
```
父键 (源件 L842):
```
seeyon:
```
SPI 开关 (源件 L964–965，位于上列块内):
```
  spi:
    enable: true
```
动态加载器 (源件 L997–1006，位于同一 test2 public 块内；username 值按纪律仅登记键名，password 源件已 `<REDACTED>`):
```
  dynamic:
    loader:
      batchSize: 5
      lruSize: 200
      type: maven
      maven:
        releaseUrl: http://10.0.0.1/artifactory/libs-release/
        snapshotUrl: http://10.0.0.1/artifactory/libs-snapshot/
        username: <REDACTED:仅登记键名>
        password: <REDACTED>
```

## 对照面 — TARGET-xiaozhua-uat / dataId=public / tenant=xiaozhua-uat

块头 (源件 L458):
```
########## TARGET-xiaozhua-uat dataId=public group=seeyon tenant=xiaozhua-uat ##########
```
SPI 开关 (源件 L575–576，位于该 uat public 块内):
```
  spi:
    enable: true
```

## spi-plugins / spiPlugins 覆盖面检索 (本会话实测)

命令: `grep -inE 'spi-plugins|spiPlugins' raw-02-nacos-configs.md`
结果: **0 命中**（全文件）。

本会话实测该快照捕获的 `##########` 配置块 = 8 个 dataId（main HANDOFF 记为 6，此处据实测登记，差异作 OBSERVATION）:
1. L67   TARGET-xiaozhua-uat     dataId=app9000000000000000001  tenant=xiaozhua-uat
2. L405  TARGET-xiaozhua-uat     dataId=udc                          tenant=xiaozhua-uat
3. L458  TARGET-xiaozhua-uat     dataId=public                       tenant=xiaozhua-uat
4. L679  TARGET-xiaozhua-uat     dataId=public-common                tenant=xiaozhua-uat
5. L688  TARGET-xiaozhua-uat     dataId=public-system                tenant=xiaozhua-uat
6. L720  CONTROL-xiaozhua-test2  dataId=znxmglptcopy5791640252914287064  tenant=xiaozhua-test2
7. L784  CONTROL-xiaozhua-test2  dataId=udc                          tenant=xiaozhua-test2
8. L841  CONTROL-xiaozhua-test2  dataId=public                       tenant=xiaozhua-test2

以上已捕获 dataId 均未声明 SPI 插件清单 (`spi-plugins`/`spiPlugins`)。
**覆盖面缺口 (UNVERIFIED)**: 该只读通道未捕获服务级/插件级 dataId；不能由本快照断言 test2 全局不存在 SPI 插件清单声明，只能断言"已捕获配置面未见声明"。

## 0 写自证

- 本件全部内容来自在盘只读快照文件的逐字摘录 + 本地 grep/行读取；无任何 Nacos/网关/kubectl 写调用。
- 值全 `<REDACTED>` 或仅键名；无 password、无 artifactory username 值、无 token 入件。

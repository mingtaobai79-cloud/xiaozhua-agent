# core/facts/spi/evidence — 证据索引（SPI-EXT-REG-01 / SPI-EXT-LOAD-01）

本目录是 `core/facts/spi/` 两格事实的**可复算证据**。口径：`VERIFIED_STATIC_BYTECODE`（有 jar 字节码支撑）> `STATIC_CONTRACT`（仅源码/文档）。
**取证时钟**：2026-09-29T10:43:12Z（北京 18:43:12，epoch 1790678592）。**无 LIVE、无网络、凭据 0 入件。**

## 证据来源（artifact）
| artifact | 路径 | sha256 | 字节 |
|---|---|---|---|
| com.seeyon:boot-starter-spi:5.3.358 | `<MAVEN_REPO>/com/seeyon/boot-starter-spi/5.3.358/boot-starter-spi-5.3.358.jar` | `67b830e4da9e805e462dd9eb4ba809888ba6a21f06b3f2dfe8fa3558bfc39dab` | 22906 |
| com.seeyon:cip-connector-api:5.3.286 | `<MAVEN_REPO>/com/seeyon/cip-connector-api/5.3.286/cip-connector-api-5.3.286.jar` | `de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91` | 170420 |
| 客开模块（在盘源码） | `<PATH> HEAD `a954272`） | 逐件见 `hashes/customer-files.sha256.txt` | — |

## 目录
| 路径 | 内容 |
|---|---|
| `hashes/` | `jars.sha256.txt`、`customer-files.sha256.txt`、`platform-classes.sha256.txt`（13 件）、`cip-connector-classes.sha256.txt`、`evidence-inventory.sha256.txt`（**62 件全量清单**） |
| `jar-contents/` | `unzip -l` VERBATIM（两个 jar 的条目清单） |
| `javap-signatures/` | `javap -p`（15 类，方法/字段签名） |
| `javap-verbose/` | `javap -p -v`（常量池、`ConstantValue`、`RuntimeVisibleAnnotations`、class 级 SHA-256） |
| `javap-code/` | `javap -p -c`（8 类字节码，含 `ldc` 字符串常量与调用目标） |
| `class-constant-strings/` | 常量池 UTF-8 真值（修正 javap 在本机的 GBK 乱码）+ 还原工具 `cp_strings.py` |
| `platform-jar-resources/` | 平台 jar 内 `META-INF/spring.factories`、`README.md`、两个 `MANIFEST.MF` 的 VERBATIM 副本 |
| `customer-modules/` | 客开 10 件 VERBATIM 副本（`cmp` 实测与原件逐字节相同） |

## 复算命令（实测可用）
```bash
sha256sum <file>                                   # 任意件哈希
unzip -l <jar>                                     # 条目清单
cmp <copy> <original>                              # VERBATIM 同一性
od -c <file>                                       # 行尾/字节形态（本机 wc -l 会掩盖 CR）
"C:/Program Files/Java/latest/jdk-21/bin/javap.exe" -p -cp <jar> <FQN>   # 签名
python class-constant-strings/cp_strings.py <path/x.class>               # 常量池真值
```

## 清单快照时点与预期 FAILED（P3d 补记）

- `hashes/evidence-inventory.sha256.txt` 是 **P1 取证时点（2026-09-29T10:43:12Z）的快照**：覆盖面 = 该时点的 62 条
  （不含清单自身；含清单自身为 63 件，与 registration §8 口径一致），**不含** P2/P4b 后新增的 `evidence/live/` e1–e4
  （**P3d 时点** `evidence/live/` 共 4 件：`core/facts/spi/evidence/live/e1-nacos-spi-config-snapshot-20260922.md`、`core/facts/spi/evidence/live/e2-nacos-spi-config-fresh-20260930.md`、`core/facts/spi/evidence/live/e3-runtime-channel-inventory-20260930.md`、`core/facts/spi/evidence/live/e4-runtime-probe-nonssh-20260930.md`；现盘 evidence 树共 67 文件 = 63 P1 + e1–e4）。★ **2026-11-07 复核**：`evidence/live/` 现为 **9 件**（e1–e9，新增 e5–e9），`evidence/` 全树现为 **79 文件**；本段其余数字仍是 P3d 时点值，未重生成 inventory。
  即「62 件全量清单」的「全量」限定于 P1 覆盖面，不是本目录当前全树。
- 在本目录内执行 `sha256sum -c hashes/evidence-inventory.sha256.txt` 的**预期结果 = 61 OK / 1 FAILED（`README.md`）**：
  清单 L62 自锚行 `d174efc5…` 记录的是 P1 时点的 README 字节，N2 订正后现 README 必然与之不符——
  属**设计内时点差**，非证据损坏；按门14 NB-2 裁定**不重生成 inventory**（重生成 = 重开已 PASS 的 P1 证据面）。

## 已知工具注意点（实测）
- 本机 `javap` 以 GBK 渲染常量池中文 → VERBATIM 落盘件含乱码字节；**真值以 `class-constant-strings/` 为准**，两件并存。
- 本机无 `python3`（用 `python`）、无 `strings`、`javap` 不在 PATH。
- 本机 `wc -l` 会把 CRLF 计数掩盖为行数；行尾一律用 `tr -dc '\r' | wc -c` 比对。

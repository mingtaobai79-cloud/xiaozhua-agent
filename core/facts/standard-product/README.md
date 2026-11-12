# core/facts/standard-product/ 索引

## 这个目录是什么

**标品域（平台自带能力）的事实格：包用法、扩展点、接口面。环境无关，不绑客户应用。**

| 问题 | 去哪 |
|---|---|
| "我要做 X，该用平台哪个包/接口" | ①⑩⑪ 能力地图 |
| "这个方法签名是什么、入参 DTO 里有什么" | ⑰⑲㉒㉓ |
| "我要扩展平台，该实现哪个接口" | ⑭⑮⑯ |
| "方法背后动了什么（Dao/Service/Event）" | ⑳㉑ |
| "扩展工程怎么建、哪层能改" | ⑬ |
| "某个具体接口的全量清单" | `interface-inventory.md` |

与相邻目录分工：`core/facts/udc/` 是 **UDC 客开域**（绑客户应用、绑实例）；
本目录是 **标品域**（平台 91 构件、1457 接口，任何客户环境都一样）。

## 一、23 格（对应 `core/facts/INDEX.md` L118 的 ①–㉓）

| # | 文件 | 字节 | 行 |
|---|---|---:|---:|
| # | 文件 | 字节 | 行 |
|---|---|---:|---:|
| ① | `platform-package-capability-index.md` | 11,830 | 219 |
| ② | `transport-usage.md` | 9,858 | 223 |
| ③ | `appservice-usage.md` | 9,671 | 200 |
| ④ | `dao-and-mybatis.md` | 11,487 | 205 |
| ⑤ | `standard-product-appservice-surfaces.md` | 16,439 | 341 |
| ⑥ | `dubbo-cross-service.md` | 8,182 | 166 |
| ⑦ | `boot-core-utils-and-annotations.md` | 8,994 | 176 |
| ⑧ | `udc-runtime-and-extend-packages.md` | 8,968 | 189 |
| ⑨ | `frontend-platform-packages.md` | 15,010 | 310 |
| ⑩ | `frontend-package-capability-index.md` | 10,975 | 158 |
| ⑪ | `frontend-component-signatures.md` | 12,171 | 209 |
| ⑫ | `udc-microflow-extend-interfaces.md` | 24,079 | 441 |
| ⑬ | `extension-project-skeleton.md` | 7,711 | 144 |
| ⑭ | `extension-point-decision-table.md` | 19,995 | 181 |
| ⑮ | `extension-registration-mechanisms.md` | 13,729 | 264 |
| ⑯ | `extension-point-consumers.md` | 7,689 | 153 |
| ⑰ | `appservice-dto-fields.md` | 5,395 | 141 |
| ⑱ | `enums-and-constants.md` | 5,706 | 139 |
| ⑲ | `platform-annotations.md` | 6,469 | 136 |
| ⑳ | `service-business-flow.md` | 8,920 | 184 |
| ㉑ | `business-action-index.md` | 7,237 | 160 |
| ㉒ | `appservice-invocation.md` | 6,442 | 163 |
| ㉓ | `api-usage-cards.md` | 7,393 | 181 |
| ㉔ | `code-repo-and-targets.md` | 7,566 | 180 |
| ㉕ | `autocode-project-templates.md` | 4,990 | 136 |

合计 25 格 = 256906 B。
INDEX L118 那一行是这 23 份的**逐格摘要**（7886 字符的单行），本表只给坐标，不重复摘要。

## 二、另外三份（不在这 23 格里）

| 文件 | 字节 | sha256（前 8…后 5） | 性质 |
|---|---:|---|---|
| `interface-inventory.md` | 149,393 | `a925bd02…9977e` | **自动生成**，勿手改。`tools/core/platform/emit_interface_inventory.py` 重跑。1457 接口 = 1348 真接口 + 109 注解，755 个有 abstract 方法 |
| `standard-product-contracts.md` | 34,217 | `9b89172f…16ef8` | **P1 字节码核验契约格 A–E**（cip-connector-api 5.3.286 / bpm-facade 3.12.101 / ctp-user-api 3.8.215），P1/P2/P5 均 auditor PASS |
| `reconciliation.md` | 17,172 | `c29962df…146eb` | **P2 对账**：module_catalog 层级对齐、`UdcOperationRegistry` 64−3别名−2=59 实测复现、标品域↔客开域边界 |

⚠️ `interface-inventory.md` 在 `docs/audit/artifacts/extension-surface-20261029/interface-inventory.md`
有一份**逐字节相同**的副本（均 149,393 B，实测 `cmp` 无差异）。
**不是重复劳动**：生成器写在 artifacts 侧（证据产物），facts 侧是消费入口。
改前先看 `tools/core/platform/emit_interface_inventory.py` 的 `--emit` 默认路径；
测试 `tests/udc/test_extension_usage_assets.py:374` 断言的是 **artifacts 侧**那份存在。

## 三、evidence/ 子树（证据，不是事实）

| 目录 | 内容 |
|---|---|
| `evidence/bytecode/` | cfr/javap 反编译原件（`cip-connector-api-5.3.286-*.java` 等）+ `manifest.json`（31,696 B，sha256 `7da53941…5ffbd`，可复算清单） |
| `evidence/bytecode/ctp-user-api-3.8.215/` | 29 件：`javap` 输出、`file-hashes.txt`、`crosscheck-javap-vs-cfr.json`（双路核验 5/5 等值）、整 jar cfr 产物 |
| `evidence/docs-drift/` | `drift-diff.md` / `drift-diff-f6.md`：P6–P8 registry 状态分布漂移 S1~S11 的逐字新旧对照 |
| `evidence/reconciliation/` | `count_registry_contracts.py` + `.out.json`：59 口径的复现脚本与实测输出 |

**evidence 里的 sha 锚是真锚**：`standard-product-contracts.md` 正文与 `manifest.json` 互相登记对方的 sha256。
两份在 2026-11-07 的脱敏提交（`85f0b211`）里同步改过（本机路径 → Maven 坐标），锚已随之更新。

## 四、外部引用清单（改前必查）

| 被引文件 | 引用方 |
|---|---|
| 23 格全部 | `core/facts/INDEX.md` L118（逐格摘要）、`skills/02-udc/xiaozhua-extension-usage/references/evidence-index.md`（自动生成）、`tools/core/platform/emit_evidence_index.py` |
| 12 份核心格（见测试 `FACTS` 列表） | `tests/udc/test_extension_usage_assets.py`（**逐份断言章节标题**，缺段落即红） |
| `api-usage-cards.md` / `appservice-invocation.md` / `extension-point-decision-table.md` / `extension-point-consumers.md` / `platform-annotations.md` / `udc-microflow-extend-interfaces.md` | `skills/02-udc/xiaozhua-extension-usage/SKILL.md` 与 `references/extension-points.md` |
| `standard-product-contracts.md` / `reconciliation.md` | `docs/ledger/STATUS-2026H2.md` |
| 8 份（`appservice-usage` / `boot-core-*` / `dao-and-mybatis` / `dubbo-cross-service` / `frontend-platform-packages` / `platform-package-capability-index` / `standard-product-appservice-surfaces` / `transport-usage` / `udc-runtime-and-extend-packages`） | `docs/audit/artifacts/extension-surface-20261029/README.md` |
| `interface-inventory.md` | `docs/audit/artifacts/extension-surface-20261029/BASELINE.md`、`tools/core/platform/align_version_baseline.py` |

## 五、锚点现值（2026-11-07 实测，改件后须重算）

```
standard-product-contracts.md        34217 B  9b89172f…16ef8
evidence/bytecode/manifest.json      31696 B  7da53941…5ffbd
reconciliation.md                    17172 B  c29962df…146eb
interface-inventory.md              149393 B  a925bd02…9977e（自动生成，重跑即复现）
```

`core/facts/INDEX.md` L119 的锚已按上表校正（旧锚 `4cd71033…efede` / `d7643f75…34f8`
是 `85f0b211` 脱敏改写本机路径之前的值，已作废）。
`reconciliation.md` 正文里写的 `13a82834…d168` / `4e53e5f0…aa44` 是 **P1 冻结时点值**，
保留不改——那是"P2 当时复核 P1 未被改写"的证据，不是当前值。

## 六、不要做的事

- **不要**手改 `interface-inventory.md`：它是生成物，改动会被下次重跑覆盖。
- **不要**把本目录内容改成绑具体客户应用：标品域的价值就是环境无关。凡是"客户应用里实际长什么样"的，
  归 `core/facts/udc/` 或 `docs/audit/artifacts/service-flow-20261103/`。
- **不要**在改完 23 格里任何一份后不重算锚点：`tests/udc/test_extension_usage_assets.py`
  只守章节标题，**不守字节数与 sha**——那是本文件 §五 的责任。
- **不要**删 `evidence/` 下任何件：正文的 `VERIFIED_STATIC_BYTECODE` 分级全靠它可复算。

---

维护：本文件是入口，不是事实格。新增格先落盘 → 在 §一 加一行 → 在 `core/facts/INDEX.md` L118 加摘要 →
重跑 `tools/core/platform/emit_evidence_index.py` → 更新 §五 锚点。

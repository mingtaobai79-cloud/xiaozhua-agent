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
| ⑨ | `frontend-platform-packages.md` | 15,322 | 310 |
| ⑩ | `frontend-package-capability-index.md` | 11,139 | 158 |
| ⑪ | `frontend-component-signatures.md` | 12,173 | 209 |
| ⑫ | `udc-microflow-extend-interfaces.md` | 24,079 | 441 |
| ⑬ | `extension-project-skeleton.md` | 7,711 | 144 |
| ⑭ | `extension-point-decision-table.md` | 19,995 | 181 |
| ⑮ | `extension-registration-mechanisms.md` | 13,729 | 264 |
| ⑯ | `extension-point-consumers.md` | 7,689 | 153 |
| ⑰ | `appservice-dto-fields.md` | 5,536 | 141 |
| ⑱ | `enums-and-constants.md` | 5,845 | 139 |
| ⑲ | `platform-annotations.md` | 6,605 | 136 |
| ⑳ | `service-business-flow.md` | 8,915 | 184 |
| ㉑ | `business-action-index.md` | 7,232 | 160 |
| ㉒ | `appservice-invocation.md` | 6,605 | 163 |
| ㉓ | `api-usage-cards.md` | 7,574 | 181 |
| ㉔ | `code-repo-and-targets.md` | 7,566 | 180 |
| ㉕ | `autocode-project-templates.md` | 4,990 | 136 |
| ㉖ | `organization-ctpuser-method-index.md` | 10,900 | 230 |
| ㉗ | `udc-biz-microflow-method-index.md` | 15,000 | 340 |

合计 27 格。
INDEX L118 那一行是前 25 份的**逐格摘要**（7886 字符的单行），本表只给坐标，不重复摘要。
㉖㉗ 是 2026-11-18 新增的方法签名索引格，摘要待补。

## 一点五、版本漂移登记（2026-11-18 实测，必读）

`surface-index` 产物的 `packages/*.md` 头部标注的构件版本，**有 17 个与实际 `cplib/` 不符**：

| 构件 | 索引标注 | 实际 jar |
|---|---|---|
| `bpm-facade` | 5.3.374 | **5.3.600** |
| `ctp-affair-facade` | 5.3.315 | **5.3.600** |
| `ctp-user-facade` | 5.3.429 | **5.3.600** |
| `ctp-message-facade` | 5.3.287 | **5.3.600** |
| `organization-facade` | 5.3.601 | 5.3.601 ✅ |
| `app-common-facade` | 5.3.274 | **5.3.600** |
| `portal-facade` | 5.3.392 | **5.3.600** |
| `cdp-data-facade` | 5.3.279 | **5.3.600** |
| `cip-capability-common` | 5.3.276 | **5.3.600** |
| `cip-capability-facade` | 5.3.276 | **5.3.600** |
| `cip-connector-facade` | 5.3.286 | **5.3.600** |
| `cip-manager-facade` | 5.3.273 | **5.3.279** |
| `cip-openapi-common` | 5.3.260 | **5.3.600** |
| `udc-biz` | 5.3.517 | **5.3.605** |
| `udc-cicd` | 5.3.517 | **5.3.605** |
| `udc-extend` | 5.3.517 | **5.3.605** |
| `udc-plugin-api` | 5.3.517 | **5.3.605** |
| `udc-web` | 5.3.517 | **5.3.605** |

**已验证：类数完全一致**（`bpm-facade` 533=533、`organization-facade` 414=414、`ctp-user-facade` 263=263、`udc-biz` 1856=1856），
**方法签名可用** —— 漂移是「同内容换版本号」，不是内容过期。

**★ 但包名必须从 jar 取真值，不能信索引 md 的路径推断：**

| 类 | 索引暗示 | jar 里真实全限定名 |
|---|---|---|
| `BpmActionAppService` | `com.seeyon.bpm.api` | **`com.seeyon.bpm.api.common`** |
| `OrgCommonAppService` | `com.seeyon.organization.api` | **`com.seeyon.organization.api.common`** |
| `CtpUserCoreAppService` | `com.seeyon.ctp.user.api` | **`com.seeyon.ctp.user.api.core`** |
| `AffairMicroflowAppService` | `...affair.api` | **`com.seeyon.ctp.affair.api.microflow`** |
| `OrgWorkFlowAppService` | `...organization.api` | **`...organization.api.app.workflow`** |
| `OrgMetadataCoreAppService` | `...organization.api` | **`...organization.api.core.metadata`** |
| `OrgZhongheService` | `...organization.api` | **`...organization.api.app.third.zhonghe`** |

**⇒ 规则：拿类名去 jar 里搜 `.class`，取 `n[:-6].replace('/','.')`；不要从索引 md 猜包路径。**

### 一点五、更新链事务语义（第 7 格）

`transaction-beforeupdate-semantics.md` —— **事务内改「更新前」数据能不能生效**。

一句话：**能，改 `getInfo()` 返回对象即可，不用再 update**（事件与写库源是同一引用）；
但**默认发的是 `BeforeUpdateBatchEvent`，不是 `BeforeUpdateEvent`**，挂错事件收不到。

### 一点六、索引已重建（2026-11-18，`extension-surface-20261118`）

**旧 `interfaces.json` 已丢失**（原 `extension-surface-20261029/` 目录不存在），本次从 91 个 jar 全量重建：

| 项 | 值 |
|---|---|
| 位置 | `docs/audit/artifacts/extension-surface-20261118/` |
| `interfaces.json` | **60.3 MB** — 91 构件 / **10453 类** / **106451 方法** / 41339 个可反查方法名 |
| `packages/` | 91 个（每构件方法级签名） |
| `dto-fields/` | 12 个域 |
| `domains/` | 11 个域 |
| `interface-inventory.md` | 1144 接口 = 1035 真接口 + 109 注解；**754 个可 implements** |
| `constants.md` | 378 KB（10258 个带字面值常量） |
| `impl-map.json` | 295 接口 / 297 条实现关系 |
| `extension-points.md` | 150 扩展点（有实现 100 / 纯扩展位 27） |
| `action-index.md` | **113 KB** / 2259 方法（有实现 2130 / 有流转 388） |
| `annotations.md` | **109 个 `@interface`**（RUNTIME 108），含元注解 Spring 注册线索 |
| `consumers.json` | 12248 类扫描 / **182 个扩展点的真实引用计数** |
| `registration-scan.json` | 91 JAR（48 个有 spring.factories / 3 条 services 条目） |
| `dto-meta.json` | 1331 扫 / **1305 有中文元数据**（字段 caption） |
| `dto-validations.json` | **0 条约束（真实：平台 DTO 无 JSR-303 注解，旧版同样为 0）** |
| `service-flow-20261118/` | udc-biz 155 KB / udc-dataflow 19 KB（action-index 的前置） |
| `surface-index.tar.gz` | **746 KB** / 127 条目（已覆盖 `docs/audit/reference/`） |

**重建链路（可复现）：**

```
cplib/*.jar (221 个)
  → build_batch2_fast.py   (批量 javap -p -constants，每批 80 类)
  → batch2/<构件>.json
  → index_backend_interfaces.py  (官方脚本)
  → interfaces.json
  → emit_package_surfaces / emit_interface_inventory / emit_constants
    / emit_extension_points / emit_dto_fields / emit_domain_surfaces
    / build_impl_map
  → 各产物
```

**★★★ 关键教训：旧 `packages/*.md` 只渲染「关键类」的**部分**方法，不能当全量方法清单用。**

| 接口 | 旧索引显示 | 真实方法数 |
|---|---|---|
| `BpmAppService` | 4 | **26** |
| `BpmTemplateAppService` | 23 | **55** |
| `BpmCaseAppService` | 21 | **23** |
| `BpmOpinionAppService` | 5 | **7** |
| `BpmProcessLogAppService` | 2 | **7** |
| `OrgCommonAppService` | 10 | **45** |
| `OrgWorkFlowAppService` | 7 | **37** |
| `OrgMetadataCoreAppService` | 4 | **16** |
| `OrgMemberSyncAppService` | 2 | **14** |
| `CtpRoleCoreAppService` | 6 | **14** |
| `CtpUserRoleCoreAppService` | 5 | **13** |

**⇒ 想要某接口的完整方法清单，必须查 `interfaces.json` 的 `classes[<fqcn>].methods`，不要读 `packages/*.md`（那只是节选）。**

**方法数口径：** `interfaces.json` 的 `methods` 含 `lambda$` 合成方法。
真实业务方法数 = 总数 − 以 `lambda$` 开头的项（如 `MicroFlowAppService` 95 = 75 真 + 20 lambda）。

**为什么 BPM / 组织的 action-index 只看得到接口，追不到方法体流转：**

平台服务端只发布了接口 jar（`bpm-facade` / `organization-facade`），
实现类在服务端进程里，jar 里没有 `*AppServiceImpl` 字节码。
能追流转的只有 UDC 域（`udc-biz` 等有实现类在仓库）。
⇒ **BPM/组织的调用链只能靠实测或平台日志，静态索引到此为止。**

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
standard-product-contracts.md         34,226 B  5567670e…52d60
evidence/bytecode/manifest.json       31,731 B  06ae1ad2…563c4
reconciliation.md                     17,333 B  f151945a…2ee4a
interface-inventory.md               149,393 B  a925bd02…9977e（自动生成，重跑即复现）
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

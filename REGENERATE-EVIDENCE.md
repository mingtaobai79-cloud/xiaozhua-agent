# 重新生成反编译证据（docs/audit/artifacts）

`docs/audit/artifacts/`（约 390 MB / 8800+ 文件）**不在分发树内**。
它是「这条事实凭什么成立」的依据，不随包分发，但可以完全自动重建。

依赖测试在缺目录时会自动 skip（`tests/conftest.py` 的
`pytest_collection_modifyitems`），所以 clone 下来直接跑 `pytest tests` 是全绿的
（实测 2236 passed / 967 skipped / 0 failed）。

---

## 什么时候需要重建

- 想核对某条 `core/facts/**` 结论的原始依据
- 改了平台版本基线，要重抽签名面
- 想跑被 skip 掉的那 967 个用例（含 232 个断言证据件存在的用例）

---

## 前置条件（缺一不可）

```text
本地 maven 仓库   D:/repo/CHIT/com/seeyon          实测 1184 个 jar / 1.9 GB
javap             D:/software/java/bin/javap.exe   实测存在
cfr（可选）       cfr-0.152.jar                    只有走反编译（--cfr）才需要
Python            .venv/Scripts/python.exe
```

构件本身很小：抽取面覆盖的 91 个 jar 合计只有 **27 MB**（中位 0.1 MB），
1.9 GB 是整个仓库的体量，不是抽取需要扫的量。

---

## 一、抽取签名面（已实测）

`tools/core/platform/extract_surface_batch_par.py`，按 `{构件: [版本, jar路径]}` 并发抽：

```bash
python tools/core/platform/extract_surface_batch_par.py \
  --targets  targets.json \
  --emit-dir docs/audit/artifacts/extension-surface-20261029/batch2 \
  --progress progress.jsonl \
  --javap    D:/software/java/bin/javap.exe \
  --limit    100000 \
  --workers  8
```

`targets.json` 形状（构件名 → [版本, jar 绝对路径]）：

```json
{"app-approval-facade": ["5.3.295", "D:/repo/CHIT/com/seeyon/app-approval-facade/5.3.295/app-approval-facade-5.3.295.jar"]}
```

**实测速率**：`boot-core` 507 个类用 141 秒（4 并发）→ 0.279 秒/类。
全量 21389 个类推算：

```text
 4 并发 → 约 49 分钟
 8 并发 → 约 25 分钟
12 并发 → 约 16 分钟
```

想让脚本自己按「仓库里最高版本」挑 jar，用 `tools/core/platform/rebuild_surfaces.py`
（它内部逐个调 `extract_jar_symbols.py`，`--limit 3000`）：

```bash
python tools/core/platform/rebuild_surfaces.py \
  --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
  --repo D:/repo/CHIT/com/seeyon \
  --out-dir docs/audit/artifacts/extension-surface-20261029/batch2 \
  --only-changed --jobs 6
```

---

## 二、汇总成 interfaces.json（派生，未在本轮逐步重放）

`batch2/*.json` → `interfaces.json` 的汇总由 `tools/core/platform/` 下的
`index_extracted_surface.py` / `index_backend_interfaces.py` 负责；
`interfaces.json` 结构是三段：

```text
sources       91 个构件 → {jar, file, classes, total_methods}
classes    21389 个类的完整签名（extends / implements / methods[args, returns, signature]）
method_index 41242 条 方法名 → 全限定签名
```

`interfaces-facade-only.json`（57 MB）是 `interfaces.json` 的 facade-only 派生视图，
测试不读它；重建时可以不生成。**其余 emit 脚本**按产物对应：

```text
domains/          emit_domain_surfaces.py
dto-fields/       emit_dto_fields.py
packages/         emit_package_surfaces.py
action-index.md   emit_action_index.py
constants.md      emit_constants.py
extension-points.md  emit_extension_points.py
interface-inventory.md  emit_interface_inventory.py
```

---

## 三、其它证据目录

测试还引用这几个（都能从同一批 jar / 已抓记录重建）：

```text
udc-runtime-5.3.517     75 文件  1.8 MB
udc-biz-5.3.517         59 文件  0.3 MB
service-flow-20261103   18 文件  5.1 MB   emit_service_flow.py
api-usage               11 文件  3.3 MB   emit_api_usage.py
udc-web-5.3.517-contracts  2 文件
```

---

## 已知不可重建的一项

`extension-surface-20261029/batch2-old-v517/`（49 MB）是**修复前**的旧版本快照，
用来对照「首轮抽取取错版本」这个结论。重跑只会生成 `batch2/`，不会复活它。
测试不读这个目录，重建后它可以不存在。

---

## 验证重建结果

```bash
# 1) 证据目录回来了
ls docs/audit/artifacts/extension-surface-20261029/interfaces.json

# 2) 依赖测试不再 skip
pytest tests -q            # skipped 会明显下降（967 → 只剩其他原因跳过的）

# 3) 抽查一份结论仍成立
pytest tests/udc/test_extension_usage_assets.py -q
```

---

## 本页数字的来源

| 数字 | 来源 | 可信度 |
|---|---|---|
| 91 构件 / 21389 类 / 41242 方法索引 | `interfaces.json` 实读 | 实测 |
| 0.279 秒/类、141 秒/507 类 | 本轮 4 并发真跑 `extract_surface_batch_par.py` | 实测 |
| 27 MB / 中位 0.1 MB | 91 个 jar 本地 `stat` 求和 | 实测 |
| 1184 jar / 1.9 GB | `D:/repo/CHIT/com/seeyon` 遍历 | 实测 |
| 8 并发 25 分钟 | 由 0.279 秒/类 × 21389 类推算 | 推算，非实测 |
| 汇总步（interfaces.json 等） | 脚本存在且有 docstring | 未逐步重放 |

---

# 一句话重建

```bash
python tools/regen_evidence.py            # 抽取 + 聚合，两步一次跑完
python tools/regen_evidence.py --check    # 只查前置，不写文件
```

构件清单随仓库分发：`config/evidence-manifest.json`（91 项，含 jar 名与版本）。
脚本按清单在 `--maven` 指定的本地 maven 仓库里定位 jar（`--maven` 默认
`D:/repo/CHIT/com/seeyon`，`--javap` 默认 `D:/software/java/bin/javap.exe`）。

产出：`<evidence>/batch2/*.json` + `<evidence>/interfaces.json`
（`sources` / `classes` / `method_index` 三段）。

## 验证到什么程度（别当成「全量重生成」）

| 环节 | 状态 | 证据 |
|---|---|---|
| 逐构件抽取 `batch2/*.json` | 已验证 | 3 个构件真跑，0.279 秒/类 |
| 聚合出 `interfaces.json` | 已验证 | 22557 类 / 7 秒 |
| 用重建件替掉原件跑依赖用例 | **228 / 232 通过** | 见下 |
| 派生文档（interface-inventory.md、packages/、evidence-index） | **未打通** | 见下 |

**没过的 4 个，原因都已定位，都不是解析错：**

```text
test_backend_interfaces_artifact_complete   interface-inventory.md 里写着 1457 个接口，
                                            重建后 JSON 是 2108 个 → 文本没同步
test_every_screenshot_package_has_surface   packages/ 有 91 个文件（按构件分），
                                            emit_package_surfaces.py 跑出来是 4458 个
                                            （按 package 分）→ 分组口径不同，不是同一套
test_skill_navigation_points_to_real_files  evidence-index 里的接口数同上没同步
test_contract_probes_compile                探针编译失败，随上面三处不一致连带
```

也就是说：**签名面可以一句话重建；派生的人读文档需要各自的生成器，且
`packages/` 的分组口径与脚本当前输出不一致，我没有打通，如实标注。**
要完整恢复，还得把 `emit_package_surfaces.py` 的分组参数对齐，或改用当初生成
那 91 个文件的入口（仓库里没找到）。

## 环境差异导致的小偏移

重建后 14 个构件的类数比清单登记的少（`boot-core` 507 vs 512、
`boot-starter-dubbo` 48 vs 55 等）。这是**清单基线早于本地 maven 仓库当前版本**，
不是抽取漏类；脚本结束时会把这些差异逐条列出来，看到它属于正常。

---

# 接口签名索引（随仓库分发，2.1 MB）

写自定义微流程扩展时最常问的一句是「这个 Service 有哪些方法、参数和返回是什么」。
原先只能翻 `docs/audit/udc-semantics/` 下上百份 md，或者重跑 25 分钟的抽取。

所以仓库里带了一份**摊平的签名索引**：

```text
docs/audit/signatures.txt.gz     2.1 MB / 245709 行 / 21389 个类 / 92 个构件
```

格式一行一成员，制表符与冒号分隔：

```text
com.seeyon.x.YService	interface
com.seeyon.x.YService#doIt(com.seeyon.x.Req):com.seeyon.x.Resp
```

查询走 `tools/signature_lookup.py`（解压 + 内存过滤，实测 0.25 秒）：

```bash
python tools/signature_lookup.py ApprovalAppService          # 类名片段
python tools/signature_lookup.py --method saveAs             # 方法名片段
python tools/signature_lookup.py --pkg com.seeyon.udc.api --kind interface
python tools/signature_lookup.py XxxService --json           # 机器可读
python tools/signature_lookup.py --method create --raw       # 只打命中行，可直接 grep
```

## 为什么是 gzip 文本，而不是原 interfaces.json

```text
interfaces.json（原）      63.9 MB
同内容紧凑 JSON            33.9 MB
摊平成文本                 33.0 MB
文本 gzip                   2.1 MB   ← 选了这条路
```

摊平只丢 `decl` / `signature` 这些重复度极高的字段（每个方法都重复一遍完整签名），
类名、方法名、参数类型、返回类型全保留。查询速度不变，仓库少背 61 MB。

原 `interfaces.json` 仍然不进仓库 —— 它只被构建脚本和那 232 个断言测试使用，
不进运行时。需要它时用上面的一条命令重建。

---

# UDC 平台参考包（随仓库分发，1.7 MB）

写 UDC 自定义页面 / 微流程扩展时，最需要的是**平台 Controller / Service 的真实签名**：
路径、入参 DTO、返回体、方法重载。这部分随仓库带了一份：

```text
docs/audit/reference/udc-platform-5.3.517.tar.gz   1.7 MB / 387 文件 / 解压 15.6 MB
```

内容（全部是机器生成的 javap 原文，无客户信息）：

```text
udc-web-5.3.517              全部 Controller 的 javap（2.4 MB 单文件）
udc-web-5.3.517-contracts    ApplicationController / MicroFlowController / EntityController …
udc-web-5.3.517-methods      方法索引
udc-runtime-5.3.517(+-javap) UdcBaseGeneralController / UdcRestPathParse（REST 路径怎么解析）
udc-resource / udc-publish / udc-biz / udc-flow / udc-app-basic / udc-common
extmetadata-5.3.318          UdcEntityMetaDataService（元数据写入契约）
metadata-5.3.358             MetadataService / MetadataController
udc-user-5.3.517-contracts / runtime-lowcode-5.3.517
```

解压到证据根，现有工具路径直接可用：

```bash
tar -xzf docs/audit/reference/udc-platform-5.3.517.tar.gz -C docs/audit/artifacts
python tools/signature_lookup.py MicroFlowController        # 全平台签名
grep -rn "udcMicroflow" docs/audit/artifacts/udc-web-5.3.517-contracts/ | head
```

## 为什么只收了这些

扫过 `docs/audit/artifacts` 下全部 49 个子目录（390 MB），按「能不能加速 + 有没有客户痕迹」两关筛：

```text
收了      15 个 UDC 平台目录，15.6 MB → 1.7 MB（压缩比 11%），387 个文件逐字节校验一致
没收      extension-surface 293 MB   已用 signatures.txt.gz 替代（2.1 MB，可查同一批签名）
         decompiled 43.7 MB          50 个临时 CFR 目录、版本重复，混 101 处客户名 /
                                     218 处 test2 / 178 处真实 appId / 11 处真实人名 → 弃
         udc-node-evidence 等 14 个  含客户名、test2、appId、内网 IP、真实人名 → 弃
```

`extension-surface` 与 `decompiled` 都能用 `python tools/regen_evidence.py` 和
`cfr-0.152.jar` 重造，不值得为它们把仓库撑大 30 倍。

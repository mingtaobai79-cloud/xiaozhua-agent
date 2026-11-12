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

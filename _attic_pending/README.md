# `_attic_pending/` —— 抽离收容桶

本目录**被 `.gitignore` 排除**（156 MB 级证据不拖进仓库）。它存在的意义：
让每一条「已迁出至 …」的标记都有一个可查的落点，而不是指向虚空。

## 这里放什么

从仓库抽出来、但还不能直接删除的东西：

| 类别 | 说明 | 去向 |
|---|---|---|
| 客户现场报告 | 按 `docs/audit/**` 结构平铺保留 | 仓外 `<EVIDENCE_ROOT>/xiaozhua-customer-evidence/docs-archive-<日期>/` |
| 抓包 / 回包快照 | `artifacts/**` 里的 request/response、日志切片 | 同上（按原相对路径） |
| 一次性脚本产物 | `scripts/random-biz-evidence/` 之类 | 同上，或本桶 `scripts/` |

**不进这里**：平台机制文档、操作契约、能力矩阵 —— 那些要留在仓库，只脱敏示例值。

## 抽离流程（四步，缺一步测试就红）

1. **归档**：`cp --parents` 到仓外证据根，保留原相对路径，并写 `_MANIFEST.txt`（逐行一个仓库相对路径）。
2. **串位**：`git rm` 仓库内原件；同时在 `.gitignore` 保留 `/_attic_pending/`。
3. **标去向**：每一处引用都要写成
   `（**客户场景证据，已迁出至 `xiaozhua-customer-evidence/<相对路径>`**）`
   —— 测试 `test_no_unmarked_dead_asset_refs` 就认这个形态，凭空删标记会红。
4. **验证**：
   ```bash
   pytest tests/udc/test_docs_py_refs_alive.py tests/test_deidentification.py -q
   ```

## 台账

| 日期 | 批次 | 数量 | 归档目录 | 验证 |
|---|---|---|---|---|
| 2026-11-24 | 第 0 批（前置） | 0 | — | 本 README 补齐，`test_attic_bucket_exists_in_gitignore_and_has_readme` 转绿 |
| 2026-11-24 | 第 1 批（零引用现场报告） | 47（含硬标识 25） | `xiaozhua-customer-evidence/docs-archive-20261124/`（`_MANIFEST-batch1.txt`） | 死链 103→100，无新增 |
| 2026-11-24 | 第 3 批（**首个带标记的迁移**） | 8 | `docs-archive-20261124/docs/audit/entity-field-matrix/artifacts/c9-20261020/`（`_MANIFEST-batch3.txt`） | `c9*.js` 是**可执行探测脚本**，里面写死真域名与 appId —— 属「执行字符串」不是「参考资料」，整目录迁出；`C9-CREATE-DATE-20261020.md` 存档行已改写成「已迁出至 …」 |
| 2026-11-24 | 第 2 批（零引用现场报告） | 10 选中 → 8 迁出 | `docs-archive-20261124/`（`_MANIFEST-batch2.txt`） | 契约/规则 2 份（`MIGRATION-SCHEDULER-DISPATCH.contract.md`、`ENTITY-DTO-CONSTRAINTS.md`）回仓；全量 239→240，唯一新增 `test_udc_semantics_index::test_declared_counts_match_disk`，改 README 计数后转绿 |
| 2026-11-24 | 第 1 批修正 | **-20 回仓** | — | `entity-field-matrix` 是更正链知识资产（入口 README 有更正表和计数闸门），不是现场报告，已整体回港；净迁出 27 份，`test_entity_field_matrix_index` 转绿 |

> 原则：**能标去向就不删证据**。删掉的每一条，都要能让下一个人顺着这条记录找回原件。
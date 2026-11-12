# P7-E2E-2 宿主 LLM 生成草稿 → 业务结果闭环（2026-11-03）

## 结论：E2E_BUSINESS_FLOW_VERIFIED（第二次，换实体+换聚合）

宿主 LLM（本会话"小爪"）读自然语言业务需求，产出 IntentDraft（中文字段名），
xiaozhua-agent 编译器归一化→构造→发布→构建→调度运行→数据库结果正确。
execution_id = e2e-349271037da9，buildVersion = 20261103200509。

## 业务需求（自然语言）

「数据迁移任务 MIG-11032005 执行完成后做质量汇总：统计所有批次的失败行数总和，
写成一条汇总批次记录（批次序号=999、源表=SUMMARY）。」

## LLM 草稿 → 归一化 → 业务结果

| 环节 | 结果 |
|---|---|
| 草稿节点链 | 4×CREATE_ENTITY(种子 failedRows=0/3/0/5) → RETRIEVE_ARRAY → SUM(失败行数) → CREATE_ENTITY(写汇总) |
| 归一化 | 任务ID→taskId / 失败行数→failedRows / 批次序号→batchNo / 源表→sourceTable |
| 构建 | BUILD_SUCCESS |
| 运行 | SCHEDULE 触发，写节点 input failedRows=8 |
| 数据库断言 | task_id=MIG-11032005-SUM 的 failed_rows=**8**（=0+3+0+5）✓ |

## 新验证到的能力（相比 P7-E2E-1）

1. **实体「迁移任务批次账本」**（24 实体中业务字段最丰富：readRows/writtenRows/
   failedRows/skippedRows/batchNo/batchStatus 等）可正常 create + 字段写回。
2. **LIST_OPERATION SUM 聚合**（`count_fields=["失败行数"]`）运行时正确：
   0+3+0+5=8 分毫不差，出参 BIGINTEGER 写回汇总记录。
3. **中文草稿归一化**在多字段实体上成立（4 个字段全命中 caption）。

## ★ 坑：conn.py 输出尾部 `ROWS N` 会破坏 json.loads

`scripts/conn.py db "<SQL>"` 的输出是 `[<json>]\r\nROWS N\r\n`（不是纯 JSON）。
探针脚本里 `json.loads(stdout)` 直接解析会失败（`ROWS N` 不是 JSON），
导致读库断言「永远查不到记录」——P7-E2E-1、P7-E2E-2 各空等一次超时。

修法：`if "ROWS" in out: out = out.split("ROWS")[0].strip()` 再 `json.loads`。
任何用 conn.py 读库做断言的脚本都要先剥 `ROWS` 尾。

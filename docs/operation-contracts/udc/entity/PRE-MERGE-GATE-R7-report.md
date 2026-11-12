# UDC 实体域 PRE-MERGE GATE 报告（R7）

用途: UDC-MERGE 照抄入库前最后一道离线 gate（HUMAN 08:16Z 权威指令重开）。
性质: 对当前时刻全量移交集做 6 项复测，非重做 5 轮切片审计；只读 + 本域 1 新报告。
生成: 2026-09-19 R7（哈希/计数全部取自本次落盘实测，非记忆）。

## 6 项复测结果

### 复测 1 — op_id 三源一致（MATCH/MISS）
- 命令: 抽取 D1 `### N udc.*` 行 / D3 `contracts["..." ] = UdcOperationContract` 首参 / R4 第3节编号清单，各自 sort 后两两 diff。
- 实测: D1=16, D3=16, R4=16 条；D1==D3 → MATCH；D1==R4 → MATCH；D3==R4 → MATCH。
- 判定: **MATCH**（三源 16 op_id 集合相等）。

### 复测 2 — MANIFEST 哈希全量复跑
- 命令: 逐条重算 udc-entity-5.3.517/MANIFEST.md(24 哈希行) + udc-entity-customplan-5.3.517/MANIFEST.md(5 哈希行) 共 29 条 sha256 并对照记录值。
- 实测: 29 条全部 MATCH（3 源 jar + 14+2 javap.txt + 7+2 目标 .class[unzip -p 流式]），MISS=0，无缺失文件。
- 判定: **MATCH**（29/29）。

### 复测 3 — 代码块哈希复现
- 命令: 从 registry-entries-code.md 取纯代码块（双 fence 之间、不含 fence 与 1 结尾换行）重算 sha256。
- 实测: 代码块 17871 字节，sha256=e2b82dc3453ac35de3f1d65ef3f83001398566cb5d0ea60954e5977109c618cf
- 期望: e2b82dc3453ac35de3f1d65ef3f83001398566cb5d0ea60954e5977109c618cf
- 判定: **MATCH**（复现值==锚定值）。

### 复测 4 — 冻结 registry.py 零写（精确判据）
- 命令: `git -C xiaozhua-agent diff -- components/platform_operations/registry.py`，取 + 行，grep 本会话 16 个精确 entity op_id，统计命中。
- 实测: + 行共 44 行，命中本会话 16 entity op_id 的 + 行 = **0**。
  （registry.py 现 + 行属并行微流程域 udc.application/flow/metadata/page_log/applog，非本会话 entity；上轮 main 亦独立测得 0。）
- 判定: **MATCH**（本会话 entity op_id 冻结 0 写入）。

### 复测 5 — R4 锚定
- 命令: `wc -c` + `sha256sum registry-merge-handoff.md`。
- 实测: 4426 字节 / sha256=3eb4fd6dbcb544bef19a8c0beaaa29322440b80f0f7c59e732996ad64148b295
- 期望: 4426B / 3eb4fd6dbcb544bef19a8c0beaaa29322440b80f0f7c59e732996ad64148b295
- 判定: **MATCH**。

### 复测 6 — 结论
- 六项（1 op_id 三源 / 2 哈希 29 / 3 代码块 / 4 冻结 0 / 5 R4 锚定 / 6 结论）逐项 全过。
- 判定: **PASS** —— PRE-MERGE gate 通过，UDC-MERGE 可照抄 registry-entries-code.md 的 build_udc_entity_contracts() 块（16 条，类型已对齐，代码块 e2b82dc3… 锚定）。

## 本报告自证
- 16 个 op_id（三源一致）: udc.appinfo.get_deploy_info, udc.applog.list_app_data_by_dataid, udc.applog.search_app_data_log, udc.applog.select_app_data_by_id, udc.database.query_data, udc.entity.ext.attribute, udc.entity.ext.available_datatype, udc.entity.ext.list, udc.entity.ext.tree, udc.entity.history.select_by_condition, udc.entity_data.query_form_data, udc.page.check_exists, udc.page.select_host_only_pages, udc.role.has_system_admin, udc.serial.select_entity_by_serial, udc.serial.select_entity_list
- GATE1 MATCH / GATE2 29/29 MATCH / GATE3 MATCH / GATE4 entity 命中 0 / GATE5 MATCH / GATE6 PASS
- 仅本域新增本 1 报告；未重算已有 5 轮切片；未动 registry.py/layer.py/tests/其他域；未 LIVE；未写测试。

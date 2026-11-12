# UDC 实体域 UDC-MERGE 单一移交索引（registry-merge-handoff）

用途: 本文件是 UDC-MERGE 会话照抄入库的**单一入口**。下游 UDC-MERGE 会话不会读本任务
（session-20260917-215503-1da9ad69）的 ROUTE/CLOSURE/DECISION，故把照抄所需的 6 项事实
收敛于此一处。实体域只读契约发现任务整体已 PASS（过 R1-RESUME/R3/R3FIX/R5FIX/R6 五轮独立审计，
全 PASS，留痕 auditor/），
本索引 = 就绪补强，不重开任务，不改冻结 registry.py。

---

## 1) 落库对象
直接照抄同目录 **registry-entries-code.md** 的 `build_udc_entity_contracts()` 代码块。
该块 = 16 条 UdcOperationContract 真实 Python 位置参数构造调用，已：
- 类型对齐（evidence=list[dict]、required_inputs/verification_rules=tuple、
  status=OperationStatus.VERIFIED_STATIC_BYTECODE 枚举名、write=False）；
- py_compile PASS + 16×10 位置参数 AST 双验（0 条 *args/**kwargs）；
- 代码块 17871 字节，SHA-256 e2b82dc3453ac35de3f1d65ef3f83001398566cb5d0ea60954e5977109c618cf
  （口径=两个 fence 反引号之间、不含 fence 标记与结尾换行；R5 追加 5 条 customplan 后由
  c438d118/12497B 更新为本值，第三方可确定性复现）。

## 2) 目标函数
并入 **components/platform_operations/registry.py** 的契约构建流程。
registry.py:6 已 `from .models import OperationStatus, UdcOperationContract`，
**无需新增 import**；把 `build_udc_entity_contracts()` 返回的 dict 合并进现有 contracts 构建处即可。

## 3) 16 条 operation_id 清单（从 D1 entity-readonly-contracts.md 抄，照抄顺序）
1. udc.serial.select_entity_list
2. udc.serial.select_entity_by_serial
3. udc.entity_data.query_form_data
4. udc.applog.select_app_data_by_id
5. udc.applog.list_app_data_by_dataid
6. udc.applog.search_app_data_log
7. udc.role.has_system_admin
8. udc.appinfo.get_deploy_info
9. udc.page.check_exists
10. udc.page.select_host_only_pages
11. udc.database.query_data
12. udc.entity.history.select_by_condition   （R5 补：udc-starter-customplan）
13. udc.entity.ext.tree
14. udc.entity.ext.list
15. udc.entity.ext.available_datatype
16. udc.entity.ext.attribute

## 4) 类型约定（照抄代码块即满足，勿再手工改类型）
- evidence = list[dict]（每条包一层 list）
- required_inputs / verification_rules = tuple
- status = OperationStatus.VERIFIED_STATIC_BYTECODE（枚举名，非裸串）
- write = False
> R2 登记的 2 条机械备忘（evidence 包 list、inputs/rules 转 tuple）**已由 R3 代码块落实关闭**。
> UDC-MERGE 只需照抄 registry-entries-code.md，不要再手工逐字段改类型；类型已内置正确。

## 5) 网关 service 前缀 = UNVERIFIED（不得拼接）
- 16 条 path 均为**控制器原路径**（javap 逐字），**未拼任何网关/service 前缀**。
- 网关 service 前缀是否真实存在 = UNVERIFIED（离线不可确证），**MERGE 落库时严禁拼接前缀**。
- R6 已做 6 条只读 GET LIVE 回读（LIVE-readback.md，cookie-free，config 键组装），印证网关=/service/{appId}（test2）；16 条 registry 条目仍存控制器原路径（不拼前缀）。
- 特别保留怪值（勿美化）: #3 `udc-runtime/data//query`（双斜杠）、
  #8 `deploy-info`（类级 req-mapping 缺省、无前缀）、#11 GET 携带请求体 RuntimeDataBaseQueryDataReqDto。

## 6) 冻结提示 + 证据引用
- **registry.py 当前被并行微流程会话冻结**（多 agent 并写同一文件会互相覆盖），
  本移交索引**本身不改 registry.py**，仅登记落库动作。实际入库须在冻结解除后、
  由 UDC-MERGE 会话统一执行。
- 人读版逐字段: 同目录 **registry-entries.md**（16 条 × 10 位置参数逐字段 + 排除项 + 待 MERGE 注意）。
- 证据索引（SHA-256 全量）:
  **docs/audit/artifacts/udc-entity-5.3.517/MANIFEST.md**（runtime 构件: 3 源 jar + 14 javap + 7 目标 .class）
  + **docs/audit/artifacts/udc-entity-customplan-5.3.517/MANIFEST.md**（customplan 构件: 1 源 jar + 2 javap + 2 目标 .class；R5 补扫）。
  证据等级 VERIFIED_STATIC_BYTECODE。
- 版本单元锁定: 本地 Maven **5.3.517**（<MAVEN_REPO>/com/seeyon，勿与 test2 镜像 5.3.496 混写）。

---
本文件由 implementer 于 R4（2026-09-18）落盘；仅新增此 1 个文件，冻结 registry.py 零改动，未新增 LIVE。

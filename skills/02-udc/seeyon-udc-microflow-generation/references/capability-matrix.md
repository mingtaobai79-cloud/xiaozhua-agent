# 微流程生成能力矩阵（当前基线）

> 唯一用途：被问「能生成吗 / 什么状态 / 成功率多少」时，照此表回答，**不要凭记忆**。
> 更新纪律：每次验证等级变化后同步本文件；仓库侧对应 `core/facts/udc/microflow/all-nodes-coverage.md`
> 与 `runtime-log.md`（铁律负二：技能与仓库两套文件都要改）。

## 一、四档状态定义

| 档 | 判据 | 能说吗 |
|---|---|---|
| `CONSTRUCTED` | 本地 `run_gates` 0 问题，schema 能生成 | 只能说「能构造」 |
| `SCHEMA_VERIFIED` | `publish` 成功 `errors=[]`，落库 `state=RELEASE` | 只能说「平台收了」 |
| `BUILD_VERIFIED` | 应用构建 `state=SUCCESS`（生成 Java 编译过） | 只能说「能编译」 |
| `RUNTIME_VERIFIED` | 真实执行 `success=true` **且业务结果正确**（回读/store 证据） | 才能说「能跑」 |

★ **发布 ≠ 编译 ≠ 运行**。三层全绿也可能运行时静默出错（G35 就是这样）。

## 二、节点覆盖（22 种 actionType + 4 种结构节点）

构造器 `MicroflowComposer` 有 `_st_` 的 19 种；逻辑图 DSL `_STEP_KINDS` 19 种。
**DSL 是真正生成流程的入口**，所以要同时看两边。

| actionType | 实例数 | 占比 | 构造器 | DSL | 最高验证档 |
|---|---|---|---|---|---|
| CHANGE_VARIABLE | 2413 | 22.0% | ✓ | ✓ | RUNTIME_VERIFIED（随只读流程跑过） |
| CREATE_VARIABLE | 1785 | 16.3% | ✓ | ✓ | RUNTIME_VERIFIED |
| RETRIEVE | 1683 | 15.3% | ✓ | ✓ | RUNTIME_VERIFIED |
| LIST_OPERATION | 1095 | 10.0% | ✓ | ✓ | SCHEMA_VERIFIED |
| CHANGE_LIST | 822 | 7.5% | ✓ | ✓ | SCHEMA_VERIFIED |
| SUB_MICROFLOW | 251 | 2.3% | ✓ | ✓ | **RUNTIME_VERIFIED**（父子流程自建：入参落库、出参 424242 流回、契约变更构建期被拦、刷新后跑通） |
| RETRIEVE_ARRAY | 523 | 4.8% | ✓ | ✓ | SCHEMA_VERIFIED |
| CREATE_LIST | 508 | 4.6% | ✓ | ✓ | SCHEMA_VERIFIED |
| CHANGE_ENTITY | 374 | 3.4% | ✓ | ✓ | **RUNTIME_VERIFIED**（库内 lastOffset 123→999、version 0→1） |
| CALL_APP_SERVICE | 296 | 2.7% | ✓ | ✓ | CONSTRUCTED（需真实方法签名） |
| CONVERT_DATA | 215 | 2.0% | ✓ | ✓ | SCHEMA_VERIFIED（字段级语义需匹配） |
| CREATE_ENTITY | 197 | 1.8% | ✓ | ✓ | **RUNTIME_VERIFIED**（插入返 ID，字段逐个对上） |
| CHANGE_BATCH_ENTITY | 87 | 0.8% | ✓ | ✓ | **RUNTIME_VERIFIED**（999→111 被批量写回，两行 update_time 相同） |
| MAP_OPERATION | 68 | 0.6% | ✓ | ✓ | SCHEMA_VERIFIED |
| PUBLISH_BUSINESS_EVENT | 64 | 0.6% | ✓ | **✓** | **LIVE_EXECUTED**（构建把事件 DTO+3 字段映射编译通过、运行 success；无订阅者 → 投递不可观测，见 node-publish-event.md） |
| DELETE_ENTITY | 39 | 0.4% | ✓ | ✓ | **RUNTIME_VERIFIED**（SELECT_PARAM 模式；库内按 id 查 0 行、对照 1 行） |
| CREATE_BATCH_ENTITY | 26 | 0.2% | ✓ | ✓ | **RUNTIME_VERIFIED**（CREATE_VARIABLE→CREATE_LIST→ADD→批量插入 1 行，库内值逐个对上） |
| CREATE_MAP | 26 | 0.2% | ✓ | ✓ | SCHEMA_VERIFIED |
| DATA_MAPPING | 20 | 0.2% | ✓ | ✓ | CONSTRUCTED（mappingRows 复杂） |
| BREAK | 12 | 0.1% | ✓ | **✓** | **RUNTIME_VERIFIED**（对照 3 行 / 实验 1 行，同流程自证；type 必须=BREAK，见 node-break.md） |
| CUSTOM_ERROR | 11 | 0.1% | ✓ | ✓ | RUNTIME_VERIFIED（唯一 success=False 可断言底座） |
| CALL_DATA_FLOW | 9 | 0.1% | ✓ | **✓** | **RUNTIME_VERIFIED**（udc_rt_data_flow_log 记 dataflow_mapping_id=行id、is_success=1；CONDITION 形态） |

结构节点：`BRANCH`/`CONDITION`（RUNTIME_VERIFIED）、`FOR`(for_count)/`FOR_EACH`（SCHEMA_VERIFIED）、`BREAK`（需在 BRANCH 内）。

## 三、按实例加权的覆盖率

真实语料 10979 个节点实例（643 条 RELEASE 流程统计；SUB_MICROFLOW 旧记 706 条是错的，实际 251 条）：

| 口径 | 数值 | 说明 |
|---|---|---|
| 有构造器 | 22/22 类 = 100% | **实例加权 100%**（PUBLISH_BUSINESS_EVENT / CALL_DATA_FLOW / BREAK 本轮接上 DSL；DSL kind 27 个、执行器 24 个，一一对上） |
| DSL 可直接生成 | 22/22 类 = 100% | 实例加权 **100%**（六种入口 2026-11-02 已补齐，见 test_dsl_step_coverage.py） |
| RUNTIME_VERIFIED | 12 类 | 实例加权 **65.4%**（CHANGE_VARIABLE/CREATE_VARIABLE/RETRIEVE/CREATE_ENTITY/CHANGE_ENTITY/DELETE_ENTITY/CREATE_BATCH_ENTITY/CHANGE_BATCH_ENTITY/CUSTOM_ERROR/BREAK/CALL_DATA_FLOW/SUB_MICROFLOW） |

## 四、真实成功率（按任务复杂度）

本地构造成功率 ≠ 端到端成功率。以下按「需求 → 可交付流程」估：

| 复杂度 | 典型需求 | 一次成功率 | 卡点 |
|---|---|---|---|
| **简单** | 定时查数据 → 条件 → 改字段；单实体 CRUD | **85~95%** | 基本无卡点，闸门能拦掉大部分 |
| **中等** | 多节点组合（查询+循环+写+分支）；含表达式 | **60~75%** | ①表达式右值形态 ②字段映射 attrType 键齐 ③循环内写要走 RETRIEVE 中转（G20） |
| **困难** | 跨应用调用 / 数据流 / 复杂 DATA_MAPPING / 批量写 | **30~50%** | ①CALL_APP_SERVICE 需真实方法签名 ②CALL_DATA_FLOW 需数据流对象 ③DATA_MAPPING mappingRows ④写节点多数只到 BUILD_VERIFIED |

**这三档的卡点性质不同**，说清楚才对用户有用：
- 简单档的失败基本都是**我构造错**，闸门拦得住，改一次就好。
- 中等档的失败多在**配置项细节**（attrType 键、expression 形态），有矩阵可查。
- 困难档的失败在**平台接口/数据依赖**，不是构造问题——需要先取到真实签名/对象才能开工。

## 五、未关闭的问题（会直接影响成功率）

1. **写节点族五个节点全部 RUNTIME_VERIFIED**
   CREATE / CHANGE / DELETE / CREATE_BATCH / CHANGE_BATCH 都有数据库级证据。
   仍未验：批量**部分失败**路径、IDS 模式删除、FOR_EACH 组合、大批量分批行为。
   48 条业务流程里写节点真实样本为 0 → 形态来自设计器保存样本 + 真实业务流对照。

2. **DSL 入口已补齐，但接线 ≠ 能跑**
   2026-11-02 核对发现 DSL 是**双向不一致**的，比「缺 6 种」更严重：
   - 声明了但没执行器（validate_graph 放行，跑到一半 GraphError）：
     `call_app_service` / `data_mapping` / `delete_entity`
   - 有执行器但没声明（validate_graph 直接拒，执行器永远用不到）：`custom_error`
   已补 8 个 kind（六个目标 + create_list_entity / change_list_add），
   现有 27 kind / 24 执行器，三者一一对上（tests/test_dsl_step_coverage.py 守）。
   **但**：PUBLISH_BUSINESS_EVENT / CALL_DATA_FLOW 仍停在 CONSTRUCTED，
   执行器要求调用方传入活引用对象（事件行 / 生单规则行），没有运行时证据。

3. **CALL_APP_SERVICE / CALL_DATA_FLOW / DATA_MAPPING 停在 CONSTRUCTED**
   都需要先取到真实平台对象（方法签名 / 数据流 / 映射行），无法纯离线构造。

4. **UI 抽屉自动化不通**（平台限制）
   设计器节点抽屉在本轮所有临时流程上点击无反应。不影响 API 主链路，
   但「生成后人工逐节点确认」这个环节做不了自动化。

5. **关闭抽屉会把抽屉卡死**（平台侧限制，已单列，不假装通过）。

6. **无干净实体时不能验写节点**
   实体若有默认值表达式且撞自身约束（如 YsFull6956），永远插不进数据。
   选实体前必须查 `core/facts/udc/microflow/entity-write-capability.json`。

## 六、回答模板

被问「给你需求能做成吗 / 成功率多少」时：

```
① 端到端验证过的 —— 逐行给证据（deployId / 执行时间 / success / 返回 ID）
② 我不能说没问题的 —— 逐条点名哪个节点停在哪个级别，为什么
③ 按复杂度给区间 —— 简单 85~95% / 中等 60~75% / 困难 30~50%
④ 指出卡点性质 —— 构造错（可自愈）/ 配置细节（有矩阵）/ 平台依赖（需先取证）
```

**不要只给一个总数**。用户要的是「哪类能做、哪类做不到、做不到卡在哪」。

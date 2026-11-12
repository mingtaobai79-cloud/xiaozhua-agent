# docs/audit/ 索引

> 审计报告的入口。**本目录 29 份顶层 `.md` + 16 个专题目录一直没有索引**，导致"哪份是当前结论、哪份是历史时点"
> 只能靠逐个打开判断。本索引按**职能**分组，不给结论、不改任何原文件。
>
> 约定：`docs/audit/artifacts/` = 权威证据归档（字节级、只增不删）；
> `docs/audit/<专题>/` = 专题审计报告；本目录根下的 `.md` = 跨专题的结论性报告。

## 一、当前基线（会被反复引用）

| 文件 | 内容 | 备注 |
|---|---|---|
| `agent-version-audit.md` | 工程版本边界与文档漂移审计；§2.1 是 19 个 LIVE 构件 tag 全表 | 被 `tests/udc/test_deployed_tags_version_audit_alignment.py` 钉死；Test collection 数需与 README 同步 |
| `code-reality-audit.md` | 代码与文档的实际情况对照（历史计数保留，不当契约） | Test collection 数需与 README 同步 |
| `udc-evidence-consistency-audit.md` | 审计 JSON 之间的口径一致性核对 | 被 `tests/fixtures/udc-audit/manifest.json` 列为 source_documents |
| `module-boundary-contract.md` | 模块边界与联动契约 | — |
| `udc-nine-modules-status.md` | UDC 九大模块状态与证据审计（2026-10-17） | 时点快照，数字勿直接引用 |

## 二、微流程（UDC microflow）

| 文件 | 内容 |
|---|---|
| `microflow-capability-matrix.md` | P0 收口的**审计视角**能力矩阵（状态定义 / 接口契约 / P1–P4 验收标准）。★ 与 `core/facts/udc/microflow/capability-matrix.md` 同主题两份，**判据以 facts 为准**（有代码消费者），见文件头登记 |
| `udc-node-audit-report.md` | 标准微流程 100% 可生成化验收报告 |
| `p1-verification-report.md` | P1 验收（RETRIEVE / CHANGE_VARIABLE / L2） |
| `p5-stage-report.md` | P5 阶段报告（2026-11-01） |
| `p5-write-node-runtime-report.md` | P5 写节点运行时验证（CHANGE_ENTITY / DELETE_ENTITY） |
| `p5-acceptance.md` | P5 总验收（节点级运行时语义） |
| `p6-continuous-learning.md` | P6 证据驱动的能力登记 |
| `udc-semantics/` | **126 个文件**的语义审计主战场，含 34 份 `MICROFLOW-<ACTION>-CONTRACT.md`。归属裁决见该目录自己的 `README.md`；裁决过程见 `docs/ledger/LOG-doc-consolidation-20261107-rounds1-15.md` 第 4、14 轮 |

## 三、实体与字段

| 文件 / 目录 | 内容 |
|---|---|
| `entity-field-matrix/` | 实体字段类型矩阵取证（B 段静态 ×7 / C 段 test2 探针 ×12 / 证据 JSON / assets）。**有索引**：见该目录 `README.md`，含"谁在读、不要移动" |
| `entity/` | `entity-golden-sample-static-chain.md` |
| `entity-backend-static-chain-evidence.md` | 实体构造链后端静态证据 |
| `entity-metadata-*.md`（2 份） | `entity-metadata-storage-evidence.md`（存储）/ `entity-metadata-write-contract-evidence.md`（写契约） |
| `entity-runtime-*-evidence.md`（2 份） | `entity-runtime-deployment-boundary-evidence.md`（运行时与部署边界 5.3.517）/ `entity-runtime-proxy-and-generated-consumer-evidence.md`（运行时代理与消费方 5.3.517） |
| `extmetadata-entity-read-chain-evidence.md` | extmetadata 实体读链 |
| `metadata-artifact-5.3.358-evidence.md` | 元数据构件证据（90 KiB，字节码级） |
| `udc-entity-operation-contract-evidence.md` | 实体操作契约证据 |
| `p0-3a-runtime-crud-boundary-audit.md` / `p0-3b-live-entity-construction-evidence.md` | P0-3 Runtime CRUD 边界 / 活体构造 |
| `construction/` | 构造规则来源索引与清单（`.md` + `.json` 成对） |

## 四、页面 / 菜单 / 列 / 角色 / 设置

| 目录 | 内容 |
|---|---|
| `page/` | PageTree / FunctionNode dispatch 追踪（`.md` + `.json` 成对） |
| `menu/` | 菜单只读追踪（`.md` + `.json` 成对） |
| `column-discovery/` | 列域 S1/S2 抓包与静态写链；`raw/` 是原始抓包。**有索引**：见该目录 `README.md`（15 处更正登记 —— 最贵一条是"对象查错了名字"：真实对象是 `udc_portlet`，不是 `udc_column`；`raw/*.json` 含运行态数据、不可外发） |
| `role/` | 角色域 P0–P3 + P3b + S5 写链收口（9 件）。**有自己的入口 `README.md`**：三处结论推翻的登记（「绑资源=权限闸」被推翻、「relationOrgRoleCode 空串」被推翻、javap 的 SHA-256 不能自证来源）+ 推荐读法。**不要按序号直线读** |
| `settings/` | `SET-PUB-1-publish-chain-live.md` 发布链 LIVE |
| `app-quota/` | 租户配额 LIVE 证据 + `NEEDS-HUMAN.md`（需人工） |

## 五、平台 / 网关 / 运行态

| 文件 / 目录 | 内容 |
|---|---|
| `udc-gateway-and-capability-boundary-evidence.md` | 网关与能力边界 |
| `udc-design-artifact-availability-evidence.md` | 设计态 Artifact 可得性 |
| `udc-design-time-deploy-write-contracts.md` | 设计态构建/部署写契约族（R18） |
| `udc-page-tree-function-node-dispatch-audit-20260906.md` | 早期页面树 dispatch 审计（2026-09-06） |
| `runtime/` | phase5 只读证据 + 低代码基座 CRUD 边界 |
| `modules/` | 模块画像与联动证据（`.json` 为主，`decompiled/` 是反编译产物） |
| `apps/` | 客户扩展边界审计（`.md` + `.json`） |
| `evidence/` | 杂项原样抓包（nacos yaml / 邮件模板 / bpm 信封等）；`feishu-base/` 为飞书多维表导出 |

## 六、流水与检查点（P6 已登记，勿随便移动）

| 文件 | 状态 |
|---|---|
| `next-direction-input.md` | **被代码读取**：`components/audit_summary.py:12` 的 `REPORTS["next_direction"]`；`xiaozhua_cli.py` 的 `summary` 子命令用它 |
| `recovery-checkpoint.md` | **被读取**：`tests/fixtures/udc-audit/manifest.json` 的 `source_documents` |
| `udc-semantics/COMPLETION-METHOD-PROMPT.md` | **保留原地**（2026-11-07 裁决）：udc-semantics 线（cron 已于 2026-10-16 停）的任务级方法提示词。方法论六步 + 完成判据 checklist 仍被 `skills/05-agent/xiaozhua-constraint-extraction/SKILL.md` 当作范式引用；`DEPLOYED-STATE-VERDICT.md` 拿它的 §环境 做运行时版本交叉校验（3/3 一致）。**已脱敏环境节**（客户应用 ID / 目标实体 ID / 集群命名空间 / 凭据路径改为配置键），方法内容未改 |
| `udc-semantics/UNDERSTANDING-CHECKPOINT.md` | **保留原地**（2026-11-07 裁决）：2026-10-11 的理解检查点。§3「已确认的前端真实机制」与 §4「页面保存/构建链」是全仓**唯一**系统性叙述该主题的位置（`core/facts/udc/write-chain/` 有保存协议与 page-schema 形状，但没有 UdcForm/UdcSubPage/UdcReference/UdcPanel 的组件语义与动作枚举）。零代码读取、零正文引用，但内容无替代 |
| `deferred/_deferred/` | 暂缓实现（v0.2 才启用） |

## 未被本索引覆盖的

`artifacts/`（48 个条目 = 36 子目录 + 11 顶层文件 + 本次新增的 `README.md`，权威证据归档，按批次命名，只增不删）不在上表逐条登记——它的组织方式是"按取证批次"，逐条登记会立刻过期。

**有自己的入口文件 `artifacts/README.md`**（2026-11-07 补）：按「谁在读」把 36 个子目录分成 A 代码+测试都在读 / B 只有代码在读（无测试守，风险最高）/ C 只被文档引用 / D 三方零命中，并写明命名规则与「找证据的路径」。

⚠️ **注意 `artifacts/` 不只是文档目录**：25 个子目录被 `components/`/`core/`/`tools/`/`config/` 按精确路径**在运行时读取**（`config/artifact-versions.yaml` 的 `evidence_dirs` 就指到它们）。**搬动或重命名是改运行时行为，不是文档整理。** 动手前先跑 `git grep -n "audit/artifacts/<子目录名>" -- components core tools config tests`。

`udc-semantics/`（99 份 md + 27 份 json）有**自己的入口文件** `udc-semantics/README.md`：
按组分类、34 份 `MICROFLOW-*` 与 `core/facts/udc/microflow/node-*.md` 的对应关系裁决、
13 份被代码读取的清单。此处不重复。
